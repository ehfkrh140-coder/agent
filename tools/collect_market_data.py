from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.registry import build_adapter, list_adapters, load_market_data_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only market data replay collector for OpportunityPacket v0")
    parser.add_argument("--config", default="configs/market_data.yaml")
    parser.add_argument("--adapter", default="replay_mark_orderbook_gap")
    parser.add_argument("--list-adapters", action="store_true")
    parser.add_argument("--output", help="Optional path to write the generated OpportunityPacket JSON")
    args = parser.parse_args()

    config = load_market_data_config(args.config)
    if args.list_adapters:
        for adapter_id in list_adapters(config):
            print(adapter_id)
        return

    adapter = build_adapter(args.adapter, config)
    snapshot = adapter.fetch_snapshot()
    packet = OpportunityPacketBuilder().build(snapshot)
    payload = packet.model_dump(mode="json")
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
        print(f"OpportunityPacket saved to: {output_path}")
    else:
        print(text)


if __name__ == "__main__":
    main()
