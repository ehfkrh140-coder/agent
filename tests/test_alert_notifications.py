from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from src.notifications.alert_rules import evaluate_alert
from src.notifications.formatters import format_console_alert
from src.storage.alert_log import append_alert_log


class AlertNotificationTests(unittest.TestCase):
    def test_no_candidate_is_suppressed_by_default(self):
        alert = evaluate_alert(sampling_payload("NO_CANDIDATE"))

        self.assertFalse(alert["should_alert"])
        self.assertEqual(alert["alert_type"], "no_candidate")
        self.assertEqual(alert["recommended_action"], "NO_ACTION")

    def test_no_persistent_edge_is_suppressed_by_default(self):
        alert = evaluate_alert(sampling_payload("NO_PERSISTENT_EDGE"))

        self.assertFalse(alert["should_alert"])
        self.assertEqual(alert["alert_type"], "no_persistent_edge")

    def test_persistent_net_gap_is_watch_alert(self):
        alert = evaluate_alert(sampling_payload("PERSISTENT_NET_GAP", positive_net_gap_count=3, council_recommended=False))

        self.assertTrue(alert["should_alert"])
        self.assertEqual(alert["alert_level"], "WATCH")
        self.assertEqual(alert["recommended_action"], "REVIEW_JOURNAL")

    def test_persistent_ready_edge_with_council_handoff_is_critical(self):
        alert = evaluate_alert(
            sampling_payload(
                "PERSISTENT_READY_EDGE",
                council_recommended=True,
                council_input_file="data/generated_packets/handoff.json",
                readiness_pass_count=2,
            )
        )

        self.assertTrue(alert["should_alert"])
        self.assertEqual(alert["alert_level"], "CRITICAL")
        self.assertEqual(alert["recommended_action"], "REVIEW_COUNCIL_HANDOFF")

    def test_sample_errors_is_error_alert(self):
        alert = evaluate_alert(sampling_payload("SAMPLE_ERRORS", samples_error=4))

        self.assertTrue(alert["should_alert"])
        self.assertEqual(alert["alert_level"], "ERROR")
        self.assertEqual(alert["alert_type"], "sample_errors")

    def test_opportunity_journal_record_can_be_evaluated(self):
        payload = {
            "adapter_id": "live_upbit_bithumb_spot_spread",
            "sampling_output": "data/market_samples/sample.json",
            "persistence_status": "PERSISTENT_NET_GAP",
            "samples_requested": 3,
            "samples_ok": 3,
            "samples_error": 0,
            "candidate_seen_count": 3,
            "positive_net_gap_count": 3,
            "readiness_pass_count": 0,
            "max_estimated_net_gap_pct": 0.55,
            "council_recommended": False,
        }

        alert = evaluate_alert(payload)
        message = format_console_alert(payload, alert)

        self.assertTrue(alert["should_alert"])
        self.assertIn("[WATCH]", message)
        self.assertIn("sampling_output=data/market_samples/sample.json", message)

    def test_formatter_includes_core_sampling_fields(self):
        payload = sampling_payload("PERSISTENT_NET_GAP", positive_net_gap_count=3, council_recommended=False)
        alert = evaluate_alert(payload)
        message = format_console_alert(payload, alert)

        self.assertIn("[WATCH]", message)
        self.assertIn("status=PERSISTENT_NET_GAP", message)
        self.assertIn("samples_ok=3/3", message)
        self.assertIn("candidate_seen=3", message)
        self.assertIn("positive_net_gap_count=3", message)
        self.assertIn("readiness_pass_count=0", message)
        self.assertIn("max_net_gap=0.5500%", message)
        self.assertIn("council_recommended=false", message)
        self.assertIn("reason=Persistent positive net gap", message)

    def test_alert_log_appends_jsonl(self):
        payload = sampling_payload("PERSISTENT_NET_GAP")
        alert = evaluate_alert(payload)
        message = format_console_alert(payload, alert)
        with tempfile.TemporaryDirectory() as td:
            log_path = Path(td) / "alert_log.jsonl"
            append_alert_log(payload, alert, message, log_path=log_path, sampling_output="/tmp/sample.json")
            append_alert_log(payload, alert, message, log_path=log_path, sampling_output="/tmp/sample.json")
            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["persistence_status"], "PERSISTENT_NET_GAP")
        self.assertTrue(records[0]["should_alert"])
        self.assertEqual(records[0]["sampling_output"], "/tmp/sample.json")

    def test_notify_sampling_result_cli_prints_console_message_and_logs(self):
        with tempfile.TemporaryDirectory() as td:
            sample_path = Path(td) / "sample.json"
            log_path = Path(td) / "alerts.jsonl"
            sample_path.write_text(json.dumps(sampling_payload("PERSISTENT_NET_GAP")), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    "tools/notify_sampling_result.py",
                    "--sampling-output",
                    str(sample_path),
                    "--log",
                    "--log-path",
                    str(log_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("[WATCH]", completed.stdout)
            self.assertIn("status=PERSISTENT_NET_GAP", completed.stdout)
            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["sampling_output"], str(sample_path))

    def test_alert_config_has_no_external_token_or_webhook_fields(self):
        config = yaml.safe_load(Path("configs/alerts.yaml").read_text(encoding="utf-8"))
        channels = config["channels"]

        self.assertFalse(channels["telegram"]["enabled"])
        self.assertFalse(channels["discord"]["enabled"])
        self.assertNotIn("token", channels["telegram"])
        self.assertNotIn("webhook", channels["discord"])
        self.assertNotIn("webhook_url", channels["discord"])


def sampling_payload(
    status: str,
    *,
    samples_error: int = 0,
    positive_net_gap_count: int = 0,
    readiness_pass_count: int = 0,
    council_recommended: bool = False,
    council_input_file: str | None = None,
) -> dict:
    return {
        "schema_version": "market_sampling_v1",
        "adapter_id": "live_upbit_bithumb_spot_spread",
        "samples_requested": 3,
        "samples": [
            {
                "opportunity_packet": {
                    "asset": "BTC",
                    "quote": "KRW",
                    "strategy_family": "cross_exchange_spot_spread",
                }
            }
        ],
        "summary": {
            "adapter_id": "live_upbit_bithumb_spot_spread",
            "samples_requested": 3,
            "samples_ok": 3 - samples_error,
            "samples_error": samples_error,
            "candidate_seen_count": 3 if status in {"PERSISTENT_NET_GAP", "PERSISTENT_READY_EDGE"} else 0,
            "positive_net_gap_count": positive_net_gap_count,
            "readiness_pass_count": readiness_pass_count,
            "max_estimated_net_gap_pct": 0.55 if status in {"PERSISTENT_NET_GAP", "PERSISTENT_READY_EDGE"} else None,
            "avg_estimated_net_gap_pct": 0.25 if status in {"PERSISTENT_NET_GAP", "PERSISTENT_READY_EDGE"} else None,
            "direction_counts": {"upbit_to_bithumb": 3} if status in {"PERSISTENT_NET_GAP", "PERSISTENT_READY_EDGE"} else {},
            "persistence_status": status,
            "recommended_default_decision": "WATCH" if status in {"PERSISTENT_NET_GAP", "PERSISTENT_READY_EDGE"} else "REJECT",
        },
        "council_recommended": council_recommended,
        "council_input_file": council_input_file,
        "sampling_output_file": "data/market_samples/sample.json",
    }


if __name__ == "__main__":
    unittest.main()
