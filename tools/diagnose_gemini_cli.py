import argparse
import json
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config_loader import load_agent_configs
from src.llm.gemini_cli_client import GeminiCliClient


def preview(text: str, n: int = 2000) -> str:
    return (text or "")[:n]


def run_once(client: GeminiCliClient, cfg, timeout: int = 60):
    cmd = [cfg.cli_command, "--skip-trust", "-p", '{"summary":"diag"}', "--output-format", "json"]
    start = time.time()
    timed_out = False
    try:
        rc, so, se = client._run_cli_command(cmd=cmd, env=client._build_env(cfg.gemini_cli_home), cwd=Path(cfg.working_dir or "."), timeout_seconds=timeout)
    except TimeoutError as exc:
        rc, so, se, timed_out = -1, str(exc), "", True
    elapsed = round(time.time() - start, 2)
    combined = (so or "") + "\n" + (se or "")
    return {
        "returncode": rc,
        "elapsed_seconds": elapsed,
        "timed_out": timed_out,
        "auth_prompt_detected": client._detect_auth_required(combined),
        "hidden_input_wait_suspected": timed_out or ("do you want to continue" in combined.lower()),
        "status_429_detected": "429" in combined,
        "rateLimitExceeded_detected": "rateLimitExceeded" in combined,
        "has_outer_json": "{\"response\"" in (so or ""),
        "has_response_field": "response" in (so or ""),
        "stdout_preview": preview(so, 3000),
        "stderr_preview": preview(se, 3000),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--agent")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--delay", type=int, default=0)
    args = ap.parse_args()

    cfgs = load_agent_configs("configs/agents.yaml")
    targets = cfgs if args.all else [c for c in cfgs if c.agent_id == args.agent]
    client = GeminiCliClient()
    rows = []

    for cfg in targets:
        gp = Path(cfg.gemini_cli_home) / ".gemini" / "google_accounts.json"
        active = None
        if gp.exists():
            try:
                active = json.loads(gp.read_text(encoding="utf-8")).get("active")
            except Exception:
                active = None

        for i in range(args.repeat):
            record = {
                "agent_id": cfg.agent_id,
                "gemini_cli_home": cfg.gemini_cli_home,
                "working_dir": cfg.working_dir,
                "expected_account_masked": client.mask_email(cfg.expected_account),
                "active_account_masked": client.mask_email(active),
                "active_matches_expected": bool(active and cfg.expected_account and active.lower() == cfg.expected_account.lower()),
                "browser_profile_directory": cfg.browser_profile_directory,
                "google_accounts_exists": gp.exists(),
                "test_index": i + 1,
                "direct_like_test": run_once(client, cfg),
                "python_capture_n": run_once(client, cfg),
                "python_capture_devnull": run_once(client, cfg),
            }
            rows.append(record)
            print(cfg.agent_id, i + 1, record["active_account_masked"], record["active_matches_expected"])
            if i < args.repeat - 1 and args.delay > 0:
                time.sleep(args.delay)

    outdir = Path("data/diagnostics")
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"gemini_cli_diag_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
