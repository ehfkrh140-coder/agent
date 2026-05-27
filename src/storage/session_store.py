from datetime import datetime, timezone
from pathlib import Path

from src.schemas.session_record import SessionRecord


class SessionStore:
    def __init__(self, base_dir: str = "data/sessions"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, user_message: str, results) -> Path:
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{ts}"

        record = SessionRecord(
            session_id=session_id,
            created_at_utc=now,
            user_message=user_message,
            results=results,
        )

        out_path = self.base_dir / f"{session_id}.json"
        out_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return out_path
