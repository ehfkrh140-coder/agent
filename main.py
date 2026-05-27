from dotenv import load_dotenv

from src.agents.agent_runner import AgentRunner
from src.config_loader import load_agent_configs
from src.storage.session_store import SessionStore


def main() -> None:
    load_dotenv()

    agent_configs = load_agent_configs("configs/agents.yaml")
    if len(agent_configs) != 5:
        print(f"[WARN] Expected 5 agents, found {len(agent_configs)}")

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
            print(f"- [{result.status}] {result.name}: {result.response.summary}")
        else:
            print(f"- [{result.status}] {result.name}: {result.error}")

    print(f"\nSession saved to: {saved_path}")


if __name__ == "__main__":
    main()
