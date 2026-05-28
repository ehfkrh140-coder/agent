import argparse
import json
import os
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


def mask_email(email: str | None) -> str | None:
    return GeminiCliClient.mask_email(email)


def read_accounts(home: str) -> dict:
    p = Path(home) / ".gemini" / "google_accounts.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_active(home: str) -> str | None:
    return read_accounts(home).get("active")


def build_env(gemini_cli_home: str) -> dict:
    env = dict(os.environ)
    env.update(
        {
            "GEMINI_CLI_HOME": gemini_cli_home,
            "GEMINI_FORCE_ENCRYPTED_FILE_STORAGE": "true",
            "GEMINI_FORCE_FILE_STORAGE": "true",
            "GEMINI_CLI_TRUST_WORKSPACE": "true",
            "NO_COLOR": "1",
            "TERM": "dumb",
        }
    )
    return env


def maybe_preopen_browser(cfg) -> None:
    if cfg.browser_launcher_mode != "preopen":
        return
    if not cfg.browser_executable or not cfg.browser_profile_directory:
        return
    cmd = [
        cfg.browser_executable,
        f'--profile-directory={cfg.browser_profile_directory}',
        "--new-window",
        cfg.browser_start_url,
    ]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Chrome profile for {cfg.agent_id} has been opened.")
    print(f"Make sure this browser profile is logged in as {mask_email(cfg.expected_account)}.")
    print("If Gemini asks 'Do you want to continue?', type Y.")


def login_only_for_agent(cfg) -> bool:
    wd = Path(cfg.working_dir or ".")
    wd.mkdir(parents=True, exist_ok=True)
    maybe_preopen_browser(cfg)
    print(f"\n[{cfg.agent_id}] LOGIN-ONLY home={cfg.gemini_cli_home} cwd={wd}")
    cmd = [cfg.cli_command]
    try:
        completed = subprocess.run(cmd, cwd=str(wd), env=build_env(cfg.gemini_cli_home), shell=False)
        if completed.returncode != 0:
            print(f"[{cfg.agent_id}] login-only failed (code={completed.returncode})")
            return False
    except Exception as exc:
        print(f"[{cfg.agent_id}] login-only failed: {exc}")
        return False

    active = read_active(cfg.gemini_cli_home)
    expected = cfg.expected_account
    if not active:
        print(f"[{cfg.agent_id}] failed: active account missing after login-only")
        return False
    if expected and active.lower() != expected.lower():
        print(
            f"Wrong active account. Expected {mask_email(expected)} but active is {mask_email(active)}. "
            f"Re-run login-only and choose the correct Chrome/Google account."
        )
        return False
    print(f"[{cfg.agent_id}] login-only success active={mask_email(active)}")
    return True


def verify_for_agent(cfg, strict_verify: bool = False, verify_timeout: int = 60) -> tuple[str, str]:
    wd = Path(cfg.working_dir or ".")
    wd.mkdir(parents=True, exist_ok=True)
    client = GeminiCliClient(cli_command=cfg.cli_command, timeout_seconds=verify_timeout)
    cmd = [cfg.cli_command, "--skip-trust", "-p", '{"summary":"verify"}', "--output-format", "json"]

    start = time.time()
    try:
        code, stdout, stderr = client._run_cli_command(cmd=cmd, env=build_env(cfg.gemini_cli_home), cwd=wd, timeout_seconds=verify_timeout)
    except TimeoutError:
        msg = "verify timeout: account active matches expected, but headless Gemini CLI did not respond within timeout. This may be capacity/headless/capture related."
        print(f"[{cfg.agent_id}] {msg}")
        return (("failed", "timeout") if strict_verify else ("warning", "timeout"))

    combined = (stdout or "") + "\n" + (stderr or "")
    if client._detect_auth_required(combined):
        return ("failed", "auth_required")

    active = read_active(cfg.gemini_cli_home)
    if not active or (cfg.expected_account and active.lower() != cfg.expected_account.lower()):
        return ("failed", "active_mismatch")

    elapsed = round(time.time() - start, 1)
    if code == 0:
        print(f"[{cfg.agent_id}] verify success ({elapsed}s)")
        return ("success", "ok")
    return ("failed", f"code={code}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--agent", type=str)
    ap.add_argument("--login-only", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--strict-verify", action="store_true")
    ap.add_argument("--verify-timeout", type=int, default=60)
    args = ap.parse_args()

    cfgs = load_agent_configs("configs/agents.yaml")
    if args.agent:
        targets = [c for c in cfgs if c.agent_id == args.agent]
    elif args.all:
        targets = cfgs
    else:
        ap.error("Use --all or --agent <id>")

    do_login = args.login_only or (not args.login_only and not args.verify)
    do_verify = args.verify or (not args.login_only and not args.verify)

    login_ok = login_fail = 0
    verify_ok = verify_warn = verify_fail = 0

    if do_login:
        print("\n=== Step 1/2: login-only warmup ===")
        for c in targets:
            if login_only_for_agent(c):
                login_ok += 1
            else:
                login_fail += 1

    if do_verify:
        print("\n=== Step 2/2: verify warmup ===")
        for c in targets:
            st, _ = verify_for_agent(c, strict_verify=args.strict_verify, verify_timeout=args.verify_timeout)
            if st == "success":
                verify_ok += 1
            elif st == "warning":
                verify_warn += 1
            else:
                verify_fail += 1

    if do_login:
        print(f"\nLogin-only warmup: success={login_ok} failed={login_fail}")
    if do_verify:
        print(f"Verify healthcheck: success={verify_ok} warning={verify_warn} failed={verify_fail}")

    if login_fail > 0 or verify_fail > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
