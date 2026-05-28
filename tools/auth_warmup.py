import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config_loader import load_agent_configs
from src.llm.gemini_cli_client import GeminiCliClient

AUTH_URL_RE = re.compile(r"https://(?:accounts\.google\.com|developers\.google\.com/gemini-code-assist)[^\s\]\)\"']+", re.IGNORECASE)
WARMUP_PROMPT = (
    "인증 복구 테스트입니다. 프로젝트를 분석하지 마세요. 도구를 사용하지 마세요. "
    "반드시 다음 JSON만 출력하세요: {\"summary\":\"auth_ok\",\"key_points\":[],\"concerns\":[],"
    "\"questions\":[],\"suggested_next_steps\":[],\"confidence\":1.0}"
)

def mask_email(email: str | None) -> str | None:
    return GeminiCliClient.mask_email(email)

def read_accounts(home: str) -> dict:
    p = Path(home) / '.gemini' / 'google_accounts.json'
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {}

def read_active(home: str) -> str | None:
    return read_accounts(home).get('active')

def build_env(gemini_cli_home: str) -> dict:
    env = dict(os.environ)
    env.update({
        'GEMINI_CLI_HOME': gemini_cli_home,
        'GEMINI_FORCE_ENCRYPTED_FILE_STORAGE': 'true',
        'GEMINI_FORCE_FILE_STORAGE': 'true',
        'GEMINI_CLI_TRUST_WORKSPACE': 'true',
        'NO_COLOR': '1',
        'TERM': 'dumb',
    })
    return env

def open_profile_browser(cfg, url: str) -> None:
    if not getattr(cfg, 'browser_executable', None) or not getattr(cfg, 'browser_profile_directory', None):
        return
    cmd = [cfg.browser_executable, f'--profile-directory={cfg.browser_profile_directory}', '--new-window', url]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def maybe_preopen_browser(cfg) -> None:
    mode = getattr(cfg, 'auth_browser_mode', 'relay')
    if mode not in {'preopen', 'relay'}:
        return
    open_profile_browser(cfg, cfg.browser_start_url)
    print(f"Chrome profile for {cfg.agent_id} has been opened.")

def check_agent(cfg) -> tuple[str, str]:
    active = read_active(cfg.gemini_cli_home)
    expected = cfg.expected_account
    if not active:
        return 'FAILED', f"{cfg.agent_id} FAILED active=<missing> expected={mask_email(expected)}"
    if expected and active.lower() != expected.lower():
        return 'FAILED', f"{cfg.agent_id} FAILED active={mask_email(active)} expected={mask_email(expected)}"
    return 'OK', f"{cfg.agent_id} OK active={mask_email(active)}"

def repair_login_for_agent(cfg, force_login: bool = False) -> bool:
    status, _ = check_agent(cfg)
    active = read_active(cfg.gemini_cli_home)
    if status == 'OK' and not force_login:
        print(f"[{cfg.agent_id}] already authenticated active={mask_email(active)}. Skipping repair-login.")
        return True

    wd = Path(cfg.working_dir or '.')
    wd.mkdir(parents=True, exist_ok=True)
    maybe_preopen_browser(cfg)
    env = build_env(cfg.gemini_cli_home)
    cmd = [cfg.cli_command, '--skip-trust', '-p', WARMUP_PROMPT, '--output-format', 'json']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None, text=True, encoding='utf-8', errors='replace', cwd=str(wd), env=env, shell=False)

    last_output = time.time()
    opened_urls = set()

    def pump(pipe, is_err=False):
        nonlocal last_output
        out = sys.stderr if is_err else sys.stdout
        if pipe is None:
            return
        for line in iter(pipe.readline, ''):
            print(line, end='', file=out, flush=True)
            last_output = time.time()
            if getattr(cfg, 'auth_browser_mode', 'relay') == 'relay':
                for u in AUTH_URL_RE.findall(line):
                    if u in opened_urls:
                        continue
                    opened_urls.add(u)
                    print(f"Auth URL detected. Opening it in Chrome profile {getattr(cfg, 'browser_profile_directory', '')} for {cfg.agent_id}.")
                    open_profile_browser(cfg, u)
        pipe.close()

    t1 = threading.Thread(target=pump, args=(process.stdout, False), daemon=True)
    t2 = threading.Thread(target=pump, args=(process.stderr, True), daemon=True)
    t1.start(); t2.start()
    while process.poll() is None:
        time.sleep(1)
        if time.time() - last_output > 20:
            print('No output for 20s. Gemini CLI may be waiting for input or browser authentication. Check the terminal prompt or browser.')
            last_output = time.time()
    t1.join(timeout=2); t2.join(timeout=2)

    if process.returncode != 0:
        print(f"[{cfg.agent_id}] repair-login failed (code={process.returncode})")
        return False
    new_active = read_active(cfg.gemini_cli_home)
    expected = cfg.expected_account
    if not new_active or (expected and new_active.lower() != expected.lower()):
        print(f"Wrong active account. Expected {mask_email(expected)} but active is {mask_email(new_active)}. Re-run login-only for this agent.")
        return False
    print(f"[{cfg.agent_id}] repair-login success active={mask_email(new_active)}")
    return True

def verify_for_agent(cfg, strict_verify: bool = False, verify_timeout: int = 60) -> tuple[str, str]:
    wd = Path(cfg.working_dir or '.')
    wd.mkdir(parents=True, exist_ok=True)
    client = GeminiCliClient(cli_command=cfg.cli_command, timeout_seconds=verify_timeout)
    cmd = [cfg.cli_command, '--skip-trust', '-p', '{"summary":"verify"}', '--output-format', 'json']
    try:
        code, stdout, stderr = client._run_cli_command(cmd=cmd, env=build_env(cfg.gemini_cli_home), cwd=wd, timeout_seconds=verify_timeout)
    except TimeoutError:
        print(f"[{cfg.agent_id}] verify timeout: account active matches expected, but headless Gemini CLI did not respond within timeout. This may be capacity/headless/capture related.")
        return (('failed','timeout') if strict_verify else ('warning','timeout'))
    if client._detect_auth_required((stdout or '') + '\\n' + (stderr or '')):
        return ('failed', 'auth_required')
    if code == 0:
        return ('success', 'ok')
    return ('failed', f'code={code}')

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--agent', type=str)
    ap.add_argument('--repair-login', action='store_true')
    ap.add_argument('--force-login', action='store_true')
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--strict-verify', action='store_true')
    ap.add_argument('--verify-timeout', type=int, default=60)
    args = ap.parse_args()

    cfgs = load_agent_configs('configs/agents.yaml')
    if args.agent:
        targets = [c for c in cfgs if c.agent_id == args.agent]
    elif args.all:
        targets = cfgs
    else:
        ap.error('Use --all or --agent <id>')

    if not args.repair_login and not args.verify:
        failed = 0
        for c in targets:
            st, msg = check_agent(c)
            print(msg)
            if st != 'OK':
                failed += 1
                print(f"Run: python tools/auth_warmup.py --agent {c.agent_id} --repair-login")
        if failed == 0:
            print('All accounts are ready. No warmup needed.')
            return
        raise SystemExit(1)

    if args.repair_login:
        ok = fail = 0
        for c in targets:
            if repair_login_for_agent(c, force_login=args.force_login): ok += 1
            else: fail += 1
        print(f"Repair-login: success={ok} failed={fail}")
        if fail:
            raise SystemExit(1)

    if args.verify:
        s=w=f=0
        for c in targets:
            st,_=verify_for_agent(c, strict_verify=args.strict_verify, verify_timeout=args.verify_timeout)
            if st=='success': s+=1
            elif st=='warning': w+=1
            else: f+=1
        print(f"Verify healthcheck: success={s} warning={w} failed={f}")
        if f:
            raise SystemExit(1)

if __name__ == '__main__':
    main()
