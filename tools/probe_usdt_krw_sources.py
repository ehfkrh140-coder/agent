#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.market_data.probes.usdt_krw_public_probe import run_probe_report, write_probe_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only public probe for USDT/KRW candidate sources")
    parser.add_argument("--config", default="configs/usdt_krw_probe_sources.yaml", help="Probe source config path")
    parser.add_argument("--output", required=True, help="Output JSON report path")
    parser.add_argument("--include-disabled", action="store_true", help="Include disabled config sources in the report")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout in seconds")
    parser.add_argument("--max-retries", type=int, default=1, help="Maximum retries per endpoint after the first attempt")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_probe_report(
        config_path=args.config,
        include_disabled=args.include_disabled,
        timeout_seconds=args.timeout,
        max_retries=args.max_retries,
    )
    write_probe_report(report, args.output)
    print(json.dumps({"output": args.output, "summary": report["summary"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
