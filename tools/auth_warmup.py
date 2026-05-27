import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config_loader import load_agent_configs


def mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    local, domain = email.split("@", 1)
    return f"{local[:4]}****@{domain}"


def read_active_masked(home: str) -> str | None:
    p = Path(home) / ".gemini" / "google_accounts.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return mask_email(data.get("active"))
    except Exception:
        return None


def run_warmup_for_agent(cfg) -> bool:
    wd = Path(cfg.working_dir or ".")
    wd.mkdir(parents=True, exist_ok=True)
    active = read_active_masked(cfg.gemini_cli_home)
    print(f"\n[{cfg.agent_id}] home={cfg.gemini_cli_home}")
    print(f"[{cfg.agent_id}] cwd={wd}")
    print(f"[{cfg.agent_id}] expected={mask_email(cfg.expected_account)} active={active}")

    prompt = '{"summary":"warmup","key_points":[],"concerns":[],"questions":[],"suggested_next_steps":[],"confidence":1.0}'
    cmd = [cfg.cli_command, "--skip-trust", "-p", prompt, "--output-format", "json"]
    env = dict(**__import__("os").environ)
    env.update(
        {
            "GEMINI_CLI_HOME": cfg.gemini_cli_home,
            "GEMINI_FORCE_ENCRYPTED_FILE_STORAGE": "true",
            "GEMINI_FORCE_FILE_STORAGE": "true",
            "GEMINI_CLI_TRUST_WORKSPACE": "true",
            "NO_COLOR": "1",
            "TERM": "dumb",
        }
    )
    print(f"[{cfg.agent_id}] running interactive warmup...")
    try:
        completed = subprocess.run(cmd, cwd=str(wd), env=env, shell=False)
        if completed.returncode == 0:
            print(f"[{cfg.agent_id}] warmup success")
            return True
        print(f"[{cfg.agent_id}] warmup failed (code={completed.returncode})")
    except Exception as exc:
        print(f"[{cfg.agent_id}] warmup failed: {exc}")

    print(f"{cfg.agent_id} warmup failed. Run python tools/auth_warmup.py --agent {cfg.agent_id} again.")
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--agent", type=str)
    args = ap.parse_args()

    cfgs = load_agent_configs("configs/agents.yaml")
    targets = cfgs
    if args.agent:
        targets = [c for c in cfgs if c.agent_id == args.agent]
    elif not args.all:
        ap.error("Use --all or --agent <id>")

    ok, fail = 0, 0
    for c in targets:
        if run_warmup_for_agent(c):
            ok += 1
        else:
            fail += 1
    print(f"\nWarmup done. success={ok} failed={fail}")


if __name__ == "__main__":
    main()
