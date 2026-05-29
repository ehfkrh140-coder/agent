from datetime import datetime, timezone
from pathlib import Path

from src.schemas.council_session import CouncilFlowMetadata, CouncilSessionRecord


class CouncilSessionStore:
    def __init__(self, base_dir: str = "data/council_sessions"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, *, user_message: str, results, council_flow: CouncilFlowMetadata, chair_context=None, review_contexts=None, final_context=None) -> Path:
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
        )

        out_path = self.base_dir / f"{session_id}.json"
        out_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return out_path
