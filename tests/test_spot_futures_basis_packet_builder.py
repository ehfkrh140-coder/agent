import copy
import inspect
import json
import unittest
from pathlib import Path

from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.parsers.spot_futures_basis import (
    build_spot_futures_basis_source_bundle,
    parse_binance_perp_observation,
    parse_binance_spot_observation,
)
from src.market_data.spot_futures_basis_packet_builder import build_spot_futures_basis_opportunity_packet
from src.strategy.spot_futures_basis_readiness import evaluate_spot_futures_basis_readiness


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "market_data" / "spot_futures_basis"
CREATED_AT_UTC = "2026-06-05T00:00:00Z"
FORBIDDEN_FIELD_SUBSTRINGS = (
    "apiKey",
    "secret",
    "token",
    "account",
    "balance",
    "position",
    "orderId",
    "clientOrderId",
    "order",
    "cancel",
    "withdraw",
    "deposit",
    "transfer",
    "privateKey",
)
ALLOWED_SCHEMA_KEYS_WITH_FORBIDDEN_SUBSTRINGS = {"orderbook_depth_available"}


def _load_fixture(filename):
    with (FIXTURE_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_source_bundle():
    spot = parse_binance_spot_observation(
        _load_fixture("binance_spot_book_ticker_btcusdt.json"),
        _load_fixture("binance_spot_depth_btcusdt.json"),
        _load_fixture("binance_spot_exchange_info_btcusdt.json"),
    )
    perp = parse_binance_perp_observation(
        _load_fixture("binance_futures_book_ticker_btcusdt.json"),
        _load_fixture("binance_futures_depth_btcusdt.json"),
        _load_fixture("binance_futures_premium_index_btcusdt.json"),
        _load_fixture("binance_futures_exchange_info_btcusdt.json"),
    )
    return build_spot_futures_basis_source_bundle(spot, perp)


class SpotFuturesBasisPacketBuilderTest(unittest.TestCase):
    def setUp(self):
        self.bundle = _build_source_bundle()
        self.readiness = evaluate_spot_futures_basis_readiness(self.bundle)
        self.packet = build_spot_futures_basis_opportunity_packet(
            self.bundle,
            self.readiness,
            created_at_utc=CREATED_AT_UTC,
            packet_id="test_packet_id",
        )

    def test_build_packet_from_default_fixture(self):
        self.assertEqual("opportunity_packet_v0", self.packet["schema_version"])
        self.assertEqual("test_packet_id", self.packet["packet_id"])
        self.assertEqual(CREATED_AT_UTC, self.packet["created_at_utc"])
        self.assertEqual("spot_futures_basis", self.packet["signal_type"])
        self.assertEqual("spot_futures_basis", self.packet["strategy_family"])
        self.assertEqual("spot_futures_basis_v0", self.packet["strategy_id"])
        self.assertEqual("BTC", self.packet["asset"])
        self.assertEqual("USDT", self.packet["quote"])
        self.assertEqual(2, len(self.packet["observations"]))
        self.assertEqual(1, len(self.packet["candidates"]))
        self.assertIn("detector_metadata", self.packet)
        self.assertTrue(self.packet["extensions"]["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", self.packet["extensions"]["execution_policy"])

        deterministic = build_spot_futures_basis_opportunity_packet(
            self.bundle,
            self.readiness,
            created_at_utc=CREATED_AT_UTC,
        )
        self.assertEqual(
            "binance_spot_futures_basis_v0_20260605T000000z",
            deterministic["packet_id"],
        )

    def test_observation_mapping(self):
        spot_observation, perp_observation = self.packet["observations"]
        parser_spot = self.bundle["spot_observation"]
        parser_perp = self.bundle["perp_observation"]

        self.assertEqual("binance_spot_btcusdt_spot_futures_basis", spot_observation["observation_id"])
        self.assertEqual("binance_usdm_btcusdt_perp_spot_futures_basis", perp_observation["observation_id"])
        self.assertEqual("Binance Spot", spot_observation["venue_name"])
        self.assertEqual("Binance USDⓈ-M Futures", perp_observation["venue_name"])
        self.assertEqual("spot", spot_observation["instrument_type"])
        self.assertIn(perp_observation["instrument_type"], {"linear_perpetual", "perp"})
        self.assertEqual(parser_spot["best_bid"], spot_observation["bid"])
        self.assertEqual(parser_spot["best_ask"], spot_observation["ask"])
        self.assertEqual(parser_spot["best_bid_qty"], spot_observation["bid_size"])
        self.assertEqual(parser_spot["best_ask_qty"], spot_observation["ask_size"])
        self.assertEqual(parser_perp["best_bid"], perp_observation["bid"])
        self.assertEqual(parser_perp["best_ask"], perp_observation["ask"])
        self.assertEqual(parser_perp["best_bid_qty"], perp_observation["bid_size"])
        self.assertEqual(parser_perp["best_ask_qty"], perp_observation["ask_size"])
        self.assertEqual(parser_perp["mark_price"], perp_observation["mark_price"])
        self.assertEqual(parser_perp["index_price"], perp_observation["index_price"])
        self.assertEqual(parser_perp["funding_rate"], perp_observation["derivatives"]["funding_rate_pct"])
        self.assertEqual(
            parser_spot["parser_normalized_status"],
            spot_observation["extensions"]["parser_normalized_status"],
        )
        self.assertEqual(parser_spot["raw_endpoint_ids"], spot_observation["extensions"]["raw_endpoint_ids"])
        self.assertEqual(
            parser_perp["parser_normalized_status"],
            perp_observation["extensions"]["parser_normalized_status"],
        )
        self.assertEqual(parser_perp["raw_endpoint_ids"], perp_observation["extensions"]["raw_endpoint_ids"])

    def test_candidate_mapping(self):
        candidate = self.packet["candidates"][0]
        self.assertEqual("spot_futures_basis_observation", candidate["candidate_type"])
        self.assertEqual(self.readiness["metrics"]["selected_direction"], candidate["direction"])
        for missing_field in self.readiness["required_missing_fields"]:
            self.assertIn(missing_field, candidate["required_missing_fields"])
        for metric in (
            "readiness_status",
            "recommended_default_decision",
            "readiness_pass",
            "selected_gross_basis_pct",
            "estimated_net_basis_pct",
        ):
            self.assertIn(metric, candidate["metrics"])
        self.assertEqual(self.readiness["readiness_status"], candidate["metrics"]["readiness_status"])
        self.assertEqual(
            self.readiness["recommended_default_decision"],
            candidate["metrics"]["recommended_default_decision"],
        )
        self.assertEqual(self.readiness["warnings"], candidate["extensions"]["warnings"])
        self.assertIn("WATCH is not ENTER", candidate["assumptions"])
        self.assertIn("no trading behavior", candidate["assumptions"])

    def test_watch_still_no_trade_only(self):
        bundle = copy.deepcopy(self.bundle)
        spot = bundle["spot_observation"]
        perp = bundle["perp_observation"]
        spot["best_ask"] = 100.0
        spot["best_bid"] = 99.9
        perp["best_bid"] = 101.0
        perp["best_ask"] = 101.1
        readiness = evaluate_spot_futures_basis_readiness(bundle, fee_slippage_buffer_pct=0.20)
        packet = build_spot_futures_basis_opportunity_packet(bundle, readiness, created_at_utc=CREATED_AT_UTC)
        candidate = packet["candidates"][0]

        self.assertEqual("WATCH", candidate["metrics"]["recommended_default_decision"])
        self.assertTrue(candidate["metrics"]["readiness_pass"])
        self.assertTrue(packet["extensions"]["no_trade_only"])
        self.assertTrue(candidate["extensions"]["no_trade_only"])
        self.assertIn("WATCH is not ENTER", candidate["assumptions"])
        self.assertIn("WATCH does not trigger Council auto-call, alert, or execution", candidate["assumptions"])

    def test_need_data_packet(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["spot_observation"].pop("best_ask")
        readiness = evaluate_spot_futures_basis_readiness(bundle)
        packet = build_spot_futures_basis_opportunity_packet(bundle, readiness, created_at_utc=CREATED_AT_UTC)
        candidate = packet["candidates"][0]

        self.assertEqual("NEED_DATA", candidate["metrics"]["readiness_status"])
        self.assertEqual("NEED_DATA", candidate["metrics"]["recommended_default_decision"])
        self.assertTrue(candidate["required_missing_fields"])
        self._assert_no_forbidden_fields(packet)


    def test_fractional_negative_data_age_ms_validates_as_int_and_preserves_raw(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["spot_observation"]["data_age_ms"] = 12.987
        bundle["perp_observation"]["data_age_ms"] = -558.491943359375
        readiness = evaluate_spot_futures_basis_readiness(bundle)
        packet_dict = build_spot_futures_basis_opportunity_packet(
            bundle,
            readiness,
            created_at_utc=CREATED_AT_UTC,
        )

        validated = OpportunityPacketBuilder().build(packet_dict).model_dump(mode="json", exclude_none=True)
        spot_observation, perp_observation = validated["observations"]

        self.assertIsInstance(spot_observation["data_quality"]["max_data_age_ms"], int)
        self.assertEqual(12, spot_observation["data_quality"]["max_data_age_ms"])
        self.assertEqual(12.987, spot_observation["extensions"]["raw_data_age_ms"])
        self.assertIsInstance(perp_observation["data_quality"]["max_data_age_ms"], int)
        self.assertLess(perp_observation["data_quality"]["max_data_age_ms"], 0)
        self.assertNotEqual(0, perp_observation["data_quality"]["max_data_age_ms"])
        self.assertEqual(-558, perp_observation["data_quality"]["max_data_age_ms"])
        self.assertEqual(-558.491943359375, perp_observation["extensions"]["raw_data_age_ms"])

    def test_fractional_latency_ms_validates_as_int_and_preserves_raw(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["spot_observation"]["latency_ms"] = 123.987
        bundle["perp_observation"]["latency_ms"] = "456.789"
        readiness = evaluate_spot_futures_basis_readiness(bundle)
        packet_dict = build_spot_futures_basis_opportunity_packet(
            bundle,
            readiness,
            created_at_utc=CREATED_AT_UTC,
        )

        validated = OpportunityPacketBuilder().build(packet_dict).model_dump(mode="json", exclude_none=True)
        spot_observation, perp_observation = validated["observations"]

        self.assertIsInstance(spot_observation["data_quality"]["latency_ms"], int)
        self.assertEqual(123, spot_observation["data_quality"]["latency_ms"])
        self.assertEqual(123.987, spot_observation["extensions"]["raw_latency_ms"])
        self.assertIsInstance(perp_observation["data_quality"]["latency_ms"], int)
        self.assertEqual(456, perp_observation["data_quality"]["latency_ms"])
        self.assertEqual(456.789, perp_observation["extensions"]["raw_latency_ms"])

    def test_data_age_not_clamped_to_zero(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["perp_observation"]["data_age_ms"] = -1.75
        readiness = evaluate_spot_futures_basis_readiness(bundle)
        packet_dict = build_spot_futures_basis_opportunity_packet(
            bundle,
            readiness,
            created_at_utc=CREATED_AT_UTC,
        )

        validated = OpportunityPacketBuilder().build(packet_dict).model_dump(mode="json", exclude_none=True)
        perp_observation = validated["observations"][1]

        self.assertEqual(-1, perp_observation["data_quality"]["max_data_age_ms"])
        self.assertNotEqual(0, perp_observation["data_quality"]["max_data_age_ms"])
        self.assertLess(perp_observation["data_quality"]["max_data_age_ms"], 0)
        self.assertEqual(-1.75, perp_observation["extensions"]["raw_data_age_ms"])

    def test_no_private_or_execution_fields(self):
        self._assert_no_forbidden_fields(self.packet)

    def test_builder_is_pure_no_file_or_network_behavior(self):
        import src.market_data.spot_futures_basis_packet_builder as packet_builder

        source = inspect.getsource(packet_builder)
        self.assertNotIn("requests", source)
        self.assertNotIn("data/market_samples", source)
        self.assertNotIn("data/generated_packets", source)
        self.assertNotIn("open(", source)
        self.assertNotIn("Path(", source)

    def _assert_no_forbidden_fields(self, value):
        if isinstance(value, dict):
            for key, nested in value.items():
                if key not in ALLOWED_SCHEMA_KEYS_WITH_FORBIDDEN_SUBSTRINGS:
                    normalized_key = key.lower()
                    for forbidden in FORBIDDEN_FIELD_SUBSTRINGS:
                        self.assertNotIn(forbidden.lower(), normalized_key, key)
                self._assert_no_forbidden_fields(nested)
        elif isinstance(value, list):
            for item in value:
                self._assert_no_forbidden_fields(item)


if __name__ == "__main__":
    unittest.main()
