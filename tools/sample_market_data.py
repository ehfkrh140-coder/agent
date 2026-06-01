#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.market_data.handoff import build_handoff_packet_from_sampling_result, write_handoff_packet
from src.market_data.registry import build_adapter, load_market_data_config
from src.market_data.sampling import run_market_sampling
from src.storage.opportunity_journal import DEFAULT_JOURNAL_PATH, append_journal_record


def main() -> None:
    parser = argparse.ArgumentParser(description="Repeated read-only market data sampler for spread persistence checks")
    parser.add_argument("--config", default="configs/market_data.yaml")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--samples", type=int, required=True)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--output", required=True)
    parser.add_argument("--also-save-packets", action="store_true")
    parser.add_argument("--max-errors", type=int, default=3)
    parser.add_argument("--handoff-output", help="Optional OpportunityPacket output path for PERSISTENT_READY_EDGE only")
    parser.add_argument("--journal", action="store_true", help="Append a sampling summary record to the opportunity journal")
    parser.add_argument("--journal-path", default=str(DEFAULT_JOURNAL_PATH))
    args = parser.parse_args()

    config = load_market_data_config(args.config)
    adapter = build_adapter(args.adapter, config)
    output_path = Path(args.output)
    packet_dir = output_path.with_suffix("") if args.also_save_packets else None
    result = run_market_sampling(
        adapter,
        adapter_id=args.adapter,
        samples_requested=args.samples,
        interval_seconds=args.interval,
        max_errors=args.max_errors,
        also_save_packets=args.also_save_packets,
        packet_output_dir=packet_dir,
        output_path=output_path,
    )
    if args.handoff_output:
        handoff_packet = build_handoff_packet_from_sampling_result(result)
        if handoff_packet is not None:
            handoff_path = write_handoff_packet(handoff_packet, args.handoff_output)
            result["council_recommended"] = True
            result["council_reason"] = "PERSISTENT_READY_EDGE: handoff OpportunityPacket is available"
            result["council_input_file"] = str(handoff_path)
        else:
            result["council_recommended"] = False
            result["council_input_file"] = None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.journal:
        append_journal_record(result, journal_path=args.journal_path, sampling_output=str(output_path))
    print(f"Market sampling saved to: {output_path}")
    print(
        "summary: "
        f"status={result['summary']['persistence_status']} "
        f"ok={result['summary']['samples_ok']} "
        f"errors={result['summary']['samples_error']} "
        f"council_recommended={result['council_recommended']}"
    )
    if result["summary"].get("persistence_status") == "SAMPLE_ERRORS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
