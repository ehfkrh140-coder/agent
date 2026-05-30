from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config_loader import load_agent_configs
from src.council.evaluation import build_scenario_evaluation
from src.council.scenarios import list_scenarios, load_scenario
from src.council.single_round_runner import SingleRoundCouncilRunner
from src.storage.council_session_store import CouncilSessionStore
from src.strategy.readiness import build_readiness_report


def scenario_names(args: argparse.Namespace) -> list[str]:
    names = list_scenarios()
    if args.scenario:
        return [args.scenario]
    if args.strategy:
        return [name for name in names if (load_scenario(name).strategy_family or load_scenario(name).signal_type) == args.strategy]
    if args.all:
        return names
    return []


def print_report(name: str, report: dict, expected_present: bool) -> None:
    missing = ",".join(report.get("missing_required_fields") or []) or "-"
    warnings = ",".join(report.get("warnings") or []) or "-"
    print(
        f"{name}\t{report.get('strategy_family')}\t{report.get('status')}\t"
        f"pass={report.get('readiness_pass')}\texpected={expected_present}\tmissing={missing}\twarnings={warnings}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch evaluate OpportunityPacket scenarios without Gemini calls")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--strategy")
    parser.add_argument("--scenario")
    parser.add_argument("--evaluate-only", action="store_true")
    parser.add_argument("--dry-run-context", action="store_true")
    args = parser.parse_args()

    if args.list:
        for name in list_scenarios():
            print(name)
        return

    names = scenario_names(args)
    if not names:
        print("Select --all, --strategy, --scenario, or --list.")
        raise SystemExit(2)

    if not args.evaluate_only and not args.dry_run_context:
        print("Batch Council execution is intentionally disabled; use --evaluate-only or --dry-run-context.")
        raise SystemExit(2)

    store = CouncilSessionStore("data/council_sessions") if args.dry_run_context else None
    runner = SingleRoundCouncilRunner(load_agent_configs("configs/agents.yaml")) if args.dry_run_context else None
    print("scenario\tstrategy\tstatus\treadiness\texpected\tmissing\twarnings")
    for name in names:
        packet = load_scenario(name)
        report = build_readiness_report(packet)
        print_report(name, report, packet.expected_behavior is not None)
        if args.dry_run_context:
            assert runner is not None and store is not None
            chair_context, review_contexts, final_context = runner.build_dry_run_contexts(
                packet.summary_message(),
                opportunity_packet=packet,
            )
            path = store.save_dry_run_context(
                chair_context=chair_context,
                review_contexts=review_contexts,
                final_context=final_context,
                opportunity_packet=packet.model_dump(mode="json"),
                expected_behavior=packet.expected_behavior_dict(),
                scenario_name=name,
                opportunity_file_path=str(REPO_ROOT / "data" / "test_scenarios" / f"{name}.json"),
                scenario_evaluation=build_scenario_evaluation(packet),
            )
            print(json.dumps({"scenario": name, "dry_run_context": str(path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
