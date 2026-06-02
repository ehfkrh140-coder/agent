from datetime import datetime, timezone
from pathlib import Path

from src.schemas.council_session import CouncilFlowMetadata, CouncilSessionRecord, ScenarioEvaluationMetadata


class CouncilSessionStore:
    def __init__(self, base_dir: str = "data/council_sessions"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, *, user_message: str, results, council_flow: CouncilFlowMetadata, chair_context=None, review_contexts=None, final_context=None, opportunity_packet=None, scenario_name=None, opportunity_file_path=None, expected_behavior=None, scenario_evaluation: ScenarioEvaluationMetadata | None = None) -> Path:
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        session_id = f"council_session_{ts}"

        record = CouncilSessionRecord(
            session_id=session_id,
            created_at_utc=now,
            user_message=user_message,
            council_flow=council_flow,
            results=results,
            chair_context=chair_context,
            review_contexts=review_contexts or {},
            final_context=final_context,
            opportunity_packet=opportunity_packet,
            scenario_name=scenario_name,
            opportunity_file_path=opportunity_file_path,
            expected_behavior=expected_behavior,
            scenario_evaluation=scenario_evaluation,
        )

        out_path = self.base_dir / f"{session_id}.json"
        out_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return out_path

    def save_dry_run_context(self, *, chair_context, review_contexts, final_context, opportunity_packet=None, expected_behavior=None, scenario_name=None, opportunity_file_path=None, scenario_evaluation: ScenarioEvaluationMetadata | None = None) -> Path:
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        out_path = self.base_dir / f"dry_run_context_{ts}.json"
        payload = {
            "created_at_utc": now.isoformat(),
            "dry_run": True,
            "scenario_name": scenario_name,
            "opportunity_file_path": opportunity_file_path,
            "opportunity_packet": opportunity_packet,
            "expected_behavior": expected_behavior,
            "scenario_evaluation": scenario_evaluation.model_dump(mode="json") if scenario_evaluation else None,
            "chair_context": chair_context,
            "review_contexts": review_contexts,
            "final_context": final_context,
        }
        import json
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return out_path
