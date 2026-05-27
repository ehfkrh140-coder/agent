import argparse
import subprocess

from dotenv import load_dotenv

from src.agents.agent_runner import AgentRunner
from src.config_loader import load_agent_configs
from src.storage.session_store import SessionStore


def maybe_warmup(skip_warmup: bool, force_warmup: bool) -> None:
    if force_warmup:
        subprocess.run(["python", "tools/auth_warmup.py", "--all"], shell=False)
        return
    if skip_warmup:
        return
    ans = input("Run auth warmup first? [Y/n] ").strip().lower()
    if ans in {"", "y", "yes"}:
        subprocess.run(["python", "tools/auth_warmup.py", "--all"], shell=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warmup", action="store_true")
    parser.add_argument("--skip-warmup", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    maybe_warmup(skip_warmup=args.skip_warmup, force_warmup=args.warmup)

    agent_configs = load_agent_configs("configs/agents.yaml")
    user_message = input("Enter your message for all agents: ").strip()
    if not user_message:
        print("Input message is empty. Exit.")
        return

    runner = AgentRunner(agent_configs)
    results = runner.run_all(user_message)

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

    print(f"\nSession saved to: {saved_path}")


if __name__ == "__main__":
    main()
