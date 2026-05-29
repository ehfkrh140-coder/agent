import argparse
import subprocess
import sys
from pathlib import Path

from src.agents.agent_runner import AgentRunner
from src.config_loader import load_agent_configs
from src.council.single_round_runner import SingleRoundCouncilRunner
from src.storage.council_session_store import CouncilSessionStore
from src.storage.session_store import SessionStore


def maybe_warmup(skip_warmup: bool, force_warmup: bool) -> bool:
    root_dir = Path(__file__).resolve().parent
    if skip_warmup:
        return True
    if not force_warmup:
        return True
    completed = subprocess.run([sys.executable, "tools/auth_warmup.py", "--all"], cwd=str(root_dir), shell=False)
    return completed.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warmup", action="store_true", help="Run account check/repair tool before execution")
    parser.add_argument("--skip-warmup", action="store_true")
    parser.add_argument("--parallel", action="store_true", help="Run agents concurrently for speed tests")
    parser.add_argument("--council", action="store_true", help="Run Single Round Council v1 flow")
    parser.add_argument("--max-workers", type=int, default=2, help="Parallel worker count (2 recommended)")
    args = parser.parse_args()

    if not maybe_warmup(skip_warmup=args.skip_warmup, force_warmup=args.warmup):
        return

    agent_configs = load_agent_configs("configs/agents.yaml")
    user_message = input("Enter your message for all agents: ").strip()
    if not user_message:
        print("Input message is empty. Exit.")
        return

    if args.council:
        council_runner = SingleRoundCouncilRunner(agent_configs)
        results, council_flow, chair_context, review_contexts, final_context = council_runner.run(
            user_message,
            parallel=args.parallel,
            max_workers=args.max_workers,
        )
        store = CouncilSessionStore("data/council_sessions")
        saved_path = store.save(
            user_message=user_message,
            results=results,
            council_flow=council_flow,
            chair_context=chair_context,
            review_contexts=review_contexts,
            final_context=final_context,
        )
    else:
        runner = AgentRunner(agent_configs)
        results = runner.run_all(user_message, parallel=args.parallel, max_workers=args.max_workers)

        store = SessionStore("data/sessions")
        saved_path = store.save(user_message=user_message, results=results)

    print("\n=== Agent run summary ===")
    for result in results:
        if result.status == "success" and result.response is not None:
            msg = result.response.summary
            if len(msg) > 120:
                msg = msg[:120] + "..."
            print(f"- [success] {result.name}: {msg}")
        else:
            err = (result.error or "")[:140]
            print(f"- [failed] {result.name}: {err}")

    label = "Council session" if args.council else "Session"
    print(f"\n{label} saved to: {saved_path}")


if __name__ == "__main__":
    main()
