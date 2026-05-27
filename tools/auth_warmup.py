import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config_loader import load_agent_configs
from src.llm.gemini_cli_client import GeminiCliClient


def mask_email(email: str | None) -> str | None:
    return GeminiCliClient.mask_email(email)


def read_active_masked(home: str) -> str | None:
    p = Path(home) / ".gemini" / "google_accounts.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return mask_email(data.get("active"))
    except Exception:
        return None


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


def login_only_for_agent(cfg) -> bool:
    wd = Path(cfg.working_dir or ".")
    wd.mkdir(parents=True, exist_ok=True)
    print(f"\n[{cfg.agent_id}] LOGIN-ONLY")
    print(f"home={cfg.gemini_cli_home}")
    print(f"cwd={wd}")
    print(f"expected={mask_email(cfg.expected_account)} active={read_active_masked(cfg.gemini_cli_home)}")
    print("Sign in with Google if prompted, then type /quit in Gemini CLI.")
    cmd = [cfg.cli_command]
    try:
        completed = subprocess.run(cmd, cwd=str(wd), env=build_env(cfg.gemini_cli_home), shell=False)
        if completed.returncode == 0:
            print(f"[{cfg.agent_id}] login-only done")
            return True
        print(f"[{cfg.agent_id}] login-only failed (code={completed.returncode})")
    except Exception as exc:
        print(f"[{cfg.agent_id}] login-only failed: {exc}")
    print(f"{cfg.agent_id} warmup failed. Run python tools/auth_warmup.py --agent {cfg.agent_id} --login-only again.")
    return False


def verify_for_agent(cfg) -> bool:
    wd = Path(cfg.working_dir or ".")
    wd.mkdir(parents=True, exist_ok=True)
    print(f"\n[{cfg.agent_id}] VERIFY")
    client = GeminiCliClient(cli_command=cfg.cli_command, timeout_seconds=min(cfg.timeout_seconds, 30))
    cmd = [cfg.cli_command, "--skip-trust", "-p", '{"summary":"verify"}', "--output-format", "json"]
    try:
        code, stdout, stderr = client._run_cli_command(
            cmd=cmd,
            env=build_env(cfg.gemini_cli_home),
            cwd=wd,
            timeout_seconds=min(cfg.timeout_seconds, 30),
        )
        combined = (stdout or "") + "\n" + (stderr or "")
        if client._detect_auth_required(combined):
            print(f"[{cfg.agent_id}] AUTH_REQUIRED - run login-only first")
            return False
        if code == 0:
            print(f"[{cfg.agent_id}] verify success (CLI callable)")
            return True
        print(f"[{cfg.agent_id}] verify failed code={code}")
        return False
    except TimeoutError as exc:
        print(f"[{cfg.agent_id}] verify timeout: {str(exc)[:180]}")
        return False
    except Exception as exc:
        print(f"[{cfg.agent_id}] verify failed: {exc}")
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--agent", type=str)
    ap.add_argument("--login-only", action="store_true")
    ap.add_argument("--verify", action="store_true")
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

    ok = fail = 0
    if do_login:
        print("\n=== Step 1/2: login-only warmup ===")
        for c in targets:
            if login_only_for_agent(c):
                ok += 1
            else:
                fail += 1
    if do_verify:
        print("\n=== Step 2/2: verify warmup ===")
        for c in targets:
            if verify_for_agent(c):
                ok += 1
            else:
                fail += 1

    print(f"\nWarmup done. success={ok} failed={fail}")


if __name__ == "__main__":
    main()
