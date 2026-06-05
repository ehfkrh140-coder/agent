from __future__ import annotations

import copy
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from src.market_data.adapters.base import MarketDataAdapterError
from src.market_data.adapters.mark_orderbook_gap_hunt import BinanceMarkOrderbookGapHuntAdapter
from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.http_client import HttpJsonResponse
from src.market_data.registry import build_adapter, list_adapters, load_market_data_config
from src.schemas.opportunity_packet import OpportunityPacket

FIXTURE_DIR = Path("tests/fixtures/mark_orderbook_gap_hunt")
NOW = datetime.fromtimestamp(1780536387000 / 1000, tz=timezone.utc)


class FakeHttpClient:
    def __init__(self, responses: dict[str, dict] | None = None, *, fail_path: str | None = None) -> None:
        self.responses = responses or {}
        self.fail_path = fail_path
        self.calls: list[tuple[str, str, dict]] = []

    def get_json(self, base_url: str, path: str, params: dict | None = None) -> HttpJsonResponse:
        params = dict(params or {})
        self.calls.append((base_url, path, params))
        if path == self.fail_path:
            error = MarketDataAdapterError(f"mocked failure for {path}")
            setattr(error, "http_status", 503)
            setattr(error, "safe_response_preview", '{"code":-1,"msg":"temporary public failure"}')
            raise error
        if path not in self.responses:
            raise AssertionError(f"unexpected path: {path}")
        return HttpJsonResponse(
            data=copy.deepcopy(self.responses[path]),
            elapsed_ms=7,
            url=f"{base_url}{path}",
            http_status=200,
            safe_response_preview=json.dumps(self.responses[path])[:500],
        )


def _binance_responses(*, watch_gap: bool = False) -> dict[str, dict]:
    fixture = json.loads((FIXTURE_DIR / "binance_valid_btcusdt.json").read_text(encoding="utf-8"))
    if watch_gap:
        fixture["mark_response"]["markPrice"] = "100.00"
        fixture["mark_response"]["indexPrice"] = "100.00"
        fixture["depth_response"]["bids"] = [["98.80", "10.000"]]
        fixture["depth_response"]["asks"] = [["99.00", "5.000"]]
    return {
        BinanceMarkOrderbookGapHuntAdapter.MARK_PRICE_PATH: fixture["mark_response"],
        BinanceMarkOrderbookGapHuntAdapter.ORDERBOOK_PATH: fixture["depth_response"],
        BinanceMarkOrderbookGapHuntAdapter.METADATA_PATH: fixture["metadata_response"],
    }


def _adapter(fake: FakeHttpClient, **config: object) -> BinanceMarkOrderbookGapHuntAdapter:
    merged_config = {
        "max_data_age_ms": 10_000,
        "fee_slippage_buffer_pct": "0.05",
        "min_net_gap_pct": "0",
        "liquidity_pass": True,
        "require_freshness": True,
        "size_or_notional_resolved": True,
    }
    merged_config.update(config)
    return BinanceMarkOrderbookGapHuntAdapter(
        http_client=fake,
        now_fn=lambda: NOW,
        config=merged_config,
    )


class BinanceMarkOrderbookGapHuntAdapterTests(unittest.TestCase):
    def test_successful_public_bundle_creates_analysis_only_packet(self) -> None:
        fake = FakeHttpClient(_binance_responses())
        packet = _adapter(fake).fetch_packet()

        self.assertIsInstance(packet, OpportunityPacket)
        self.assertEqual(packet.strategy_family, "mark_orderbook_gap_hunt")
        self.assertEqual(packet.strategy_id, "mark_orderbook_gap_hunt_v0")
        self.assertEqual(packet.signal_type, "mark_orderbook_gap_hunt")
        self.assertEqual(packet.asset, "BTC")
        self.assertEqual(packet.quote, "USDT")
        self.assertEqual(len(packet.observations), 1)
        self.assertEqual(len(packet.candidates), 1)
        self.assertEqual(packet.observations[0].venue_id, "binance")
        self.assertEqual(packet.observations[0].market_symbol, "BTCUSDT")
        self.assertEqual(packet.candidates[0].candidate_type, "mark_orderbook_gap_observation")
        self.assertEqual(packet.candidates[0].strategy_family, "mark_orderbook_gap_hunt")
        self.assertEqual(packet.candidates[0].strategy_id, "mark_orderbook_gap_hunt_v0")
        self.assertIn(packet.candidates[0].metrics["readiness_status"], {"NEED_DATA", "REJECT", "WATCH"})

        metadata = packet.extensions["adapter_metadata"]
        self.assertEqual(metadata["adapter_id"], "live_binance_mark_orderbook_gap_btcusdt")
        self.assertTrue(metadata["experimental_strategy"])
        self.assertTrue(metadata["non_active_strategy"])
        self.assertTrue(metadata["no_trade_only"])
        self.assertEqual(metadata["execution_policy"], "NO_TRADE_ONLY")

    def test_fetch_snapshot_returns_packet_json_dict(self) -> None:
        snapshot = _adapter(FakeHttpClient(_binance_responses())).fetch_snapshot()

        self.assertEqual(snapshot["strategy_family"], "mark_orderbook_gap_hunt")
        self.assertEqual(snapshot["strategy_id"], "mark_orderbook_gap_hunt_v0")
        self.assertEqual(len(snapshot["observations"]), 1)
        self.assertEqual(len(snapshot["candidates"]), 1)
        self.assertEqual(snapshot["extensions"]["adapter_metadata"]["no_trade_only"], True)

    def test_packet_builder_accepts_adapter_snapshot_for_collect_cli_flow(self) -> None:
        snapshot = _adapter(FakeHttpClient(_binance_responses())).fetch_snapshot()
        packet = OpportunityPacketBuilder().build(snapshot)

        self.assertEqual(packet.strategy_family, "mark_orderbook_gap_hunt")
        self.assertEqual(packet.strategy_id, "mark_orderbook_gap_hunt_v0")
        self.assertEqual(packet.signal_type, "mark_orderbook_gap_hunt")
        self.assertEqual(len(packet.observations), 1)
        self.assertEqual(len(packet.candidates), 1)
        self.assertEqual(packet.candidates[0].candidate_type, "mark_orderbook_gap_observation")
        self.assertEqual(packet.extensions["adapter_metadata"]["execution_policy"], "NO_TRADE_ONLY")

    def test_parser_output_ok_feeds_readiness_helper(self) -> None:
        packet = _adapter(FakeHttpClient(_binance_responses())).fetch_packet()

        parser_output = packet.extensions["parser_output"]
        readiness = packet.extensions["readiness"]
        self.assertEqual(parser_output["normalized_status"], "OK")
        self.assertIn(readiness["readiness_status"], {"REJECT", "WATCH"})
        self.assertEqual(packet.candidates[0].metrics["parser_normalized_status"], "OK")
        self.assertEqual(packet.candidates[0].metrics["readiness_status"], readiness["readiness_status"])

    def test_watch_remains_analysis_only_without_execution_council_or_alert(self) -> None:
        packet = _adapter(FakeHttpClient(_binance_responses(watch_gap=True))).fetch_packet()
        candidate = packet.candidates[0]
        packet_text = json.dumps(packet.model_dump(mode="json"), sort_keys=True)

        self.assertEqual(candidate.metrics["readiness_status"], "WATCH")
        self.assertEqual(candidate.metrics["readiness_pass"], False)
        self.assertNotIn("execution_allowed", packet_text)
        self.assertNotIn("council_auto_call", packet_text)
        self.assertNotIn("alert_trigger", packet_text)

    def test_public_http_failure_raises_adapter_error_with_safe_diagnostics(self) -> None:
        fake = FakeHttpClient(_binance_responses(), fail_path=BinanceMarkOrderbookGapHuntAdapter.MARK_PRICE_PATH)
        with self.assertRaises(MarketDataAdapterError) as ctx:
            _adapter(fake).fetch_packet()

        diagnostics = getattr(ctx.exception, "diagnostics")
        self.assertEqual(diagnostics[0]["endpoint"], BinanceMarkOrderbookGapHuntAdapter.MARK_PRICE_PATH)
        self.assertEqual(diagnostics[0]["params"], {"symbol": "BTCUSDT"})
        self.assertEqual(diagnostics[0]["http_status"], 503)
        self.assertIn("temporary public failure", diagnostics[0]["safe_response_preview"])
        diagnostics_text = json.dumps(diagnostics)
        for forbidden in ("api_key", "api_secret", "Authorization", "Bearer"):
            self.assertNotIn(forbidden, diagnostics_text)

    def test_adapter_uses_only_allowed_public_binance_paths(self) -> None:
        fake = FakeHttpClient(_binance_responses())
        _adapter(fake).fetch_packet()

        paths = [path for _, path, _ in fake.calls]
        self.assertEqual(
            paths,
            [
                BinanceMarkOrderbookGapHuntAdapter.MARK_PRICE_PATH,
                BinanceMarkOrderbookGapHuntAdapter.ORDERBOOK_PATH,
                BinanceMarkOrderbookGapHuntAdapter.METADATA_PATH,
            ],
        )
        for _, path, params in fake.calls:
            self.assertTrue(path.startswith("/fapi/v1/"))
            self.assertNotIn("private", path.lower())
            self.assertNotIn("account", path.lower())
            self.assertNotIn("order", path.lower())
            self.assertNotIn("balance", path.lower())
            self.assertNotIn("withdraw", path.lower())
            self.assertNotIn("deposit", path.lower())
            self.assertNotIn("transfer", path.lower())
            self.assertNotIn("api_key", json.dumps(params).lower())

    def test_adapter_does_not_read_env_vars_or_open_network_when_http_client_is_injected(self) -> None:
        with patch("socket.socket") as socket_factory, patch("os.getenv") as getenv:
            packet = _adapter(FakeHttpClient(_binance_responses())).fetch_packet()

        socket_factory.assert_not_called()
        getenv.assert_not_called()
        self.assertEqual(packet.strategy_family, "mark_orderbook_gap_hunt")

    def test_adapter_is_registered_as_experimental_no_trade_only(self) -> None:
        config = load_market_data_config()
        adapter_id = "live_binance_mark_orderbook_gap_btcusdt"

        self.assertIn(adapter_id, list_adapters(config))
        adapter_config = config["adapters"][adapter_id]
        self.assertEqual(adapter_config["type"], "binance_mark_orderbook_gap_hunt")
        self.assertFalse(adapter_config["enabled"])
        self.assertEqual(adapter_config["strategy_family"], "mark_orderbook_gap_hunt")
        self.assertEqual(adapter_config["strategy_id"], "mark_orderbook_gap_hunt_v0")
        self.assertEqual(adapter_config["execution_policy"], "NO_TRADE_ONLY")
        self.assertTrue(adapter_config["experimental_strategy"])
        self.assertTrue(adapter_config["non_active_strategy"])
        self.assertTrue(adapter_config["no_trade_only"])

        adapter = build_adapter(adapter_id, config)
        self.assertIsInstance(adapter, BinanceMarkOrderbookGapHuntAdapter)
        self.assertEqual(adapter.adapter_id, adapter_id)


if __name__ == "__main__":
    unittest.main()
