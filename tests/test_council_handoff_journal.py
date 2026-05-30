from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.market_data.handoff import build_handoff_packet_from_sampling_result, write_handoff_packet
from src.schemas.opportunity_packet import OpportunityPacket
from src.storage.opportunity_journal import append_journal_record, build_journal_record
from tests.test_market_data_sampling import FakeAdapter, snapshot_with_candidate
from src.market_data.sampling import run_market_sampling


class CouncilHandoffJournalTests(unittest.TestCase):
    def test_persistent_ready_sampling_result_builds_handoff_packet(self):
        result = ready_sampling_result()

        packet = build_handoff_packet_from_sampling_result(result)

        self.assertIsNotNone(packet)
        assert packet is not None
        parsed = OpportunityPacket.model_validate(packet.model_dump(mode="json"))
        self.assertTrue(parsed.packet_id.startswith("handoff_fake_spot_"))
        self.assertEqual(parsed.detector_metadata.generated_from, "sampling_persistence")
        self.assertEqual(parsed.detector_metadata.source_files, ["/tmp/sample.json"])
        self.assertEqual(parsed.extensions["persistence_status"], "PERSISTENT_READY_EDGE")
        self.assertIn("sampling_summary", parsed.extensions)
        self.assertEqual(len(parsed.candidates), 1)
        self.assertIsNone(parsed.human_context)

    def test_no_candidate_sampling_result_does_not_build_handoff(self):
        result = {
            "adapter_id": "fake_spot",
            "summary": {"persistence_status": "NO_CANDIDATE", "samples_ok": 2},
            "samples": [],
        }

        self.assertIsNone(build_handoff_packet_from_sampling_result(result))

    def test_persistent_net_gap_without_readiness_does_not_build_handoff(self):
        result = run_market_sampling(
            FakeAdapter([snapshot_with_candidate(net_gap=0.3, net_pass=True, ready=False)]),
            adapter_id="fake_spot",
            samples_requested=1,
            interval_seconds=0,
        )
        result["summary"]["persistence_status"] = "PERSISTENT_NET_GAP"
        result["summary"]["readiness_pass_count"] = 0

        self.assertIsNone(build_handoff_packet_from_sampling_result(result))

    def test_write_handoff_packet_outputs_parseable_opportunity_packet(self):
        packet = build_handoff_packet_from_sampling_result(ready_sampling_result())
        assert packet is not None
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "handoff.json"
            write_handoff_packet(packet, path)
            parsed = OpportunityPacket.model_validate_json(path.read_text(encoding="utf-8"))
        self.assertEqual(parsed.schema_version, "opportunity_packet_v0")

    def test_sample_tool_handoff_output_only_for_non_persistent_replay_creates_no_file_and_journals(self):
        with tempfile.TemporaryDirectory() as td:
            output_path = Path(td) / "sample.json"
            handoff_path = Path(td) / "handoff.json"
            journal_path = Path(td) / "journal.jsonl"
            completed = subprocess.run(
                [
                    sys.executable,
                    "tools/sample_market_data.py",
                    "--adapter",
                    "replay_cross_exchange_spot_spread",
                    "--samples",
                    "1",
                    "--interval",
                    "0",
                    "--output",
                    str(output_path),
                    "--handoff-output",
                    str(handoff_path),
                    "--journal",
                    "--journal-path",
                    str(journal_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Market sampling saved", completed.stdout)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["council_recommended"])
            self.assertIsNone(payload["council_input_file"])
            self.assertFalse(handoff_path.exists())
            records = [json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["sampling_output"], str(output_path))
            self.assertIn("candidate_seen_count", records[0])


    def test_sample_tool_handoff_output_created_for_persistent_ready_edge(self):
        with tempfile.TemporaryDirectory() as td:
            fixture_path = Path(td) / "ready_snapshot.json"
            fixture_path.write_text(
                json.dumps(snapshot_with_candidate(net_gap=0.4, net_pass=True, ready=True)),
                encoding="utf-8",
            )
            config_path = Path(td) / "market_data.yaml"
            config_path.write_text(
                "adapters:\n"
                "  replay_ready_spot:\n"
                "    type: replay\n"
                f"    fixture_path: {json.dumps(str(fixture_path))}\n",
                encoding="utf-8",
            )
            output_path = Path(td) / "sample.json"
            handoff_path = Path(td) / "handoff.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    "tools/sample_market_data.py",
                    "--config",
                    str(config_path),
                    "--adapter",
                    "replay_ready_spot",
                    "--samples",
                    "2",
                    "--interval",
                    "0",
                    "--output",
                    str(output_path),
                    "--handoff-output",
                    str(handoff_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("council_recommended=True", completed.stdout)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["council_recommended"])
            self.assertEqual(payload["council_input_file"], str(handoff_path))
            parsed = OpportunityPacket.model_validate_json(handoff_path.read_text(encoding="utf-8"))
            self.assertEqual(parsed.schema_version, "opportunity_packet_v0")
            self.assertEqual(parsed.extensions["persistence_status"], "PERSISTENT_READY_EDGE")

    def test_journal_record_has_expected_fields_and_appends(self):
        result = ready_sampling_result()
        result["council_recommended"] = True
        result["council_input_file"] = "/tmp/handoff.json"
        record = build_journal_record(result, sampling_output="/tmp/sample.json")
        self.assertEqual(record["adapter_id"], "fake_spot")
        self.assertEqual(record["sampling_output"], "/tmp/sample.json")
        self.assertEqual(record["persistence_status"], "PERSISTENT_READY_EDGE")
        self.assertTrue(record["council_recommended"])
        with tempfile.TemporaryDirectory() as td:
            journal_path = Path(td) / "journal.jsonl"
            append_journal_record(result, journal_path=journal_path, sampling_output="/tmp/a.json")
            append_journal_record(result, journal_path=journal_path, sampling_output="/tmp/b.json")
            self.assertEqual(len(journal_path.read_text(encoding="utf-8").splitlines()), 2)


def ready_sampling_result() -> dict:
    result = run_market_sampling(
        FakeAdapter([snapshot_with_candidate(net_gap=0.3, net_pass=True, ready=True), snapshot_with_candidate(net_gap=0.4, net_pass=True, ready=True)]),
        adapter_id="fake_spot",
        samples_requested=2,
        interval_seconds=0,
        output_path="/tmp/sample.json",
    )
    self_summary = result["summary"]
    self_summary["persistence_status"] = "PERSISTENT_READY_EDGE"
    self_summary["readiness_pass_count"] = 2
    return result


if __name__ == "__main__":
    unittest.main()
