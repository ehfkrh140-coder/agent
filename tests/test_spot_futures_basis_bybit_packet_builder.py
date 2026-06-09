import copy
import json
import unittest
from pathlib import Path

from src.market_data.packet_builder import OpportunityPacketBuilder
from src.market_data.parsers.spot_futures_basis import (
    build_spot_futures_basis_source_bundle,
    parse_binance_perp_observation,
    parse_binance_spot_observation,
    parse_bybit_perp_observation,
    parse_bybit_spot_observation,
)
from src.market_data.spot_futures_basis_packet_builder import build_spot_futures_basis_opportunity_packet
from src.strategy.spot_futures_basis_readiness import evaluate_spot_futures_basis_readiness


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "market_data" / "spot_futures_basis"
CREATED_AT_UTC = "2026-06-05T00:00:00Z"
BYBIT_SPOT_OBSERVATION_ID = "bybit_spot_btcusdt_spot_futures_basis"
BYBIT_PERP_OBSERVATION_ID = "bybit_linear_btcusdt_perp_spot_futures_basis"
BYBIT_CANDIDATE_ID = "bybit_btcusdt_spot_futures_basis_candidate"
BINANCE_SPOT_OBSERVATION_ID = "binance_spot_btcusdt_spot_futures_basis"
BINANCE_PERP_OBSERVATION_ID = "binance_usdm_btcusdt_perp_spot_futures_basis"
BINANCE_CANDIDATE_ID = "binance_btcusdt_spot_futures_basis_candidate"

FORBIDDEN_FIELD_SUBSTRINGS = (
    "apiKey",
    "secret",
    "token",
    "credential",
    "account",
    "balance",
    "position",
    "orderId",
    "clientOrderId",
    "cancel",
    "withdraw",
    "deposit",
    "transfer",
    "privateKey",
    "execution_enabled",
    "auto_trade",
    "alert_enabled",
    "council_auto_call",
)


def _load_fixture(filename):
    with (FIXTURE_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_bybit_pipeline(
    *,
    spot_ticker=None,
    spot_orderbook=None,
    spot_instruments=None,
    linear_ticker=None,
    linear_orderbook=None,
    linear_instruments=None,
):
    spot = parse_bybit_spot_observation(
        spot_ticker or _load_fixture("bybit_spot_ticker_btcusdt.json"),
        spot_orderbook or _load_fixture("bybit_spot_orderbook_btcusdt.json"),
        spot_instruments or _load_fixture("bybit_spot_instruments_info_btcusdt.json"),
    )
    perp = parse_bybit_perp_observation(
        linear_ticker or _load_fixture("bybit_linear_ticker_btcusdt.json"),
        linear_orderbook or _load_fixture("bybit_linear_orderbook_btcusdt.json"),
        linear_instruments or _load_fixture("bybit_linear_instruments_info_btcusdt.json"),
    )
    bundle = build_spot_futures_basis_source_bundle(spot, perp)
    readiness = evaluate_spot_futures_basis_readiness(bundle)
    packet = build_spot_futures_basis_opportunity_packet(
        bundle,
        readiness,
        created_at_utc=CREATED_AT_UTC,
    )
    return spot, perp, bundle, readiness, packet


def _build_binance_pipeline():
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
    bundle = build_spot_futures_basis_source_bundle(spot, perp)
    readiness = evaluate_spot_futures_basis_readiness(bundle)
    packet = build_spot_futures_basis_opportunity_packet(
        bundle,
        readiness,
        created_at_utc=CREATED_AT_UTC,
    )
    return bundle, readiness, packet


class SpotFuturesBasisBybitPacketBuilderTest(unittest.TestCase):
    def setUp(self):
        self.spot, self.perp, self.bundle, self.readiness, self.packet = _build_bybit_pipeline()

    def test_bybit_packet_builder_outputs_bybit_identity(self):
        self.assertEqual("opportunity_packet_v0", self.packet["schema_version"])
        self.assertEqual("spot_futures_basis", self.packet["signal_type"])
        self.assertEqual("spot_futures_basis", self.packet["strategy_family"])
        self.assertEqual("spot_futures_basis_v0", self.packet["strategy_id"])
        self.assertEqual("bybit", self.packet["extensions"]["source_venue_id"])
        self.assertEqual("same_exchange_spot_perp_basis", self.packet["extensions"]["comparison_type"])
        self.assertEqual(2, len(self.packet["observations"]))
        self.assertEqual(1, len(self.packet["candidates"]))

        observation_ids = {observation["observation_id"] for observation in self.packet["observations"]}
        self.assertEqual({BYBIT_SPOT_OBSERVATION_ID, BYBIT_PERP_OBSERVATION_ID}, observation_ids)
        self.assertNotIn(BINANCE_SPOT_OBSERVATION_ID, observation_ids)
        self.assertNotIn(BINANCE_PERP_OBSERVATION_ID, observation_ids)

        candidate = self.packet["candidates"][0]
        self.assertEqual(BYBIT_CANDIDATE_ID, candidate["candidate_id"])
        self.assertNotEqual(BINANCE_CANDIDATE_ID, candidate["candidate_id"])
        self.assertEqual("bybit", candidate["source_venue_id"])
        self.assertEqual("bybit", candidate["target_venue_id"])
        self.assertEqual(BYBIT_SPOT_OBSERVATION_ID, candidate["source_observation_id"])
        self.assertEqual(BYBIT_PERP_OBSERVATION_ID, candidate["target_observation_id"])
        self.assertIn("bybit", self.packet["detector_metadata"]["generated_from"])
        self.assertIn("linear", self.packet["detector_metadata"]["generated_from"])

    def test_bybit_packet_observation_mapping(self):
        observations = {observation["observation_id"]: observation for observation in self.packet["observations"]}
        spot_observation = observations[BYBIT_SPOT_OBSERVATION_ID]
        perp_observation = observations[BYBIT_PERP_OBSERVATION_ID]

        self.assertEqual("bybit", spot_observation["venue_id"])
        self.assertEqual("Bybit Spot", spot_observation["venue_name"])
        self.assertEqual("spot", spot_observation["instrument_type"])
        self.assertEqual("BTCUSDT", spot_observation["market_symbol"])
        self.assertEqual("spot", spot_observation["extensions"]["category"])
        self.assertEqual("OK", spot_observation["extensions"]["parser_normalized_status"])
        self.assertEqual([], spot_observation["extensions"]["required_missing_fields"])

        self.assertEqual("bybit", perp_observation["venue_id"])
        self.assertEqual("Bybit Derivatives V5", perp_observation["venue_name"])
        self.assertIn(perp_observation["instrument_type"], {"perp", "linear_perpetual"})
        self.assertEqual("linear", perp_observation["extensions"]["category"])
        self.assertEqual("BTCUSDT", perp_observation["market_symbol"])
        self.assertEqual(self.perp["mark_price"], perp_observation["mark_price"])
        self.assertEqual(self.perp["index_price"], perp_observation["index_price"])
        self.assertEqual(self.perp["funding_rate"], perp_observation["derivatives"]["funding_rate_pct"])
        self.assertEqual(self.perp["next_funding_time"], perp_observation["derivatives"]["next_funding_time_utc"])
        self.assertEqual("OK", perp_observation["extensions"]["parser_normalized_status"])
        self.assertEqual([], perp_observation["extensions"]["required_missing_fields"])

    def test_bybit_packet_candidate_mapping_and_metrics(self):
        candidate = self.packet["candidates"][0]
        self.assertEqual("spot_futures_basis_observation", candidate["candidate_type"])
        self.assertEqual(self.readiness["metrics"]["selected_direction"], candidate["direction"])
        for metric in (
            "readiness_status",
            "recommended_default_decision",
            "readiness_pass",
            "selected_gross_basis_pct",
            "estimated_net_basis_pct",
        ):
            self.assertIn(metric, candidate["metrics"])
        self.assertEqual(
            candidate["metrics"]["estimated_net_basis_pct"],
            candidate["estimated_net_gap_pct"],
        )
        self.assertEqual([], candidate["required_missing_fields"])
        self.assertIn("WATCH is not ENTER", candidate["assumptions"])
        self.assertIn("no trading behavior", candidate["assumptions"])
        self.assertIn("funding rate is context, not basis decision alone", candidate["assumptions"])

    def test_bybit_packet_builder_validates_through_opportunity_packet_builder(self):
        validated = OpportunityPacketBuilder().build(self.packet).model_dump(mode="json", exclude_none=True)
        self.assertEqual("spot_futures_basis", validated["strategy_family"])
        self.assertTrue(validated["extensions"]["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", validated["extensions"]["execution_policy"])
        self.assertEqual("bybit", validated["extensions"]["source_venue_id"])

    def test_bybit_watch_case_still_no_trade_only(self):
        linear_ticker = copy.deepcopy(_load_fixture("bybit_linear_ticker_btcusdt.json"))
        linear_orderbook = copy.deepcopy(_load_fixture("bybit_linear_orderbook_btcusdt.json"))
        ticker = linear_ticker["result"]["list"][0]
        ticker["bid1Price"] = "66000.00"
        ticker["ask1Price"] = "66010.00"
        ticker["lastPrice"] = "66005.00"
        linear_orderbook["result"]["b"][0] = ["66000.00", "2.500"]
        linear_orderbook["result"]["a"][0] = ["66010.00", "2.250"]

        _, _, bundle, readiness, packet = _build_bybit_pipeline(
            linear_ticker=linear_ticker,
            linear_orderbook=linear_orderbook,
        )
        validated = OpportunityPacketBuilder().build(packet).model_dump(mode="json", exclude_none=True)
        candidate = validated["candidates"][0]

        self.assertEqual("WATCH", candidate["metrics"]["recommended_default_decision"])
        self.assertTrue(candidate["metrics"]["readiness_pass"])
        self.assertTrue(packet["extensions"]["no_trade_only"])
        self.assertTrue(candidate["extensions"]["no_trade_only"])
        self.assertEqual("NO_TRADE_ONLY", candidate["extensions"]["execution_policy"])
        self.assertEqual("bybit", bundle["source_venue_id"])
        self.assertEqual("bybit", validated["extensions"]["source_venue_id"])
        self.assertIn("WATCH is not ENTER", candidate["assumptions"])
        self.assertIn("no trading behavior", candidate["assumptions"])
        self._assert_no_forbidden_private_or_execution_fields(packet)
        self._assert_no_forbidden_private_or_execution_fields(validated)

    def test_bybit_packet_has_no_private_or_execution_fields(self):
        validated = OpportunityPacketBuilder().build(self.packet).model_dump(mode="json", exclude_none=True)
        self._assert_no_forbidden_private_or_execution_fields(self.packet)
        self._assert_no_forbidden_private_or_execution_fields(validated)

    def test_binance_packet_builder_regression_still_uses_binance_identity(self):
        bundle, readiness, packet = _build_binance_pipeline()
        self.assertEqual("binance", bundle["source_venue_id"])
        self.assertEqual("binance", packet["extensions"]["source_venue_id"])
        observation_ids = {observation["observation_id"] for observation in packet["observations"]}
        self.assertEqual({BINANCE_SPOT_OBSERVATION_ID, BINANCE_PERP_OBSERVATION_ID}, observation_ids)
        candidate = packet["candidates"][0]
        self.assertEqual(BINANCE_CANDIDATE_ID, candidate["candidate_id"])
        self.assertEqual(BINANCE_SPOT_OBSERVATION_ID, candidate["source_observation_id"])
        self.assertEqual(BINANCE_PERP_OBSERVATION_ID, candidate["target_observation_id"])
        self.assertEqual("binance", candidate["source_venue_id"])
        self.assertEqual("binance", candidate["target_venue_id"])
        self.assertNotEqual("bybit", packet["extensions"]["source_venue_id"])
        self.assertIn("binance", packet["detector_metadata"]["generated_from"])
        self.assertEqual(readiness["metrics"]["selected_direction"], candidate["direction"])

    def _assert_no_forbidden_private_or_execution_fields(self, value):
        if isinstance(value, dict):
            for key, nested in value.items():
                normalized_key = key.lower()
                for forbidden in FORBIDDEN_FIELD_SUBSTRINGS:
                    self.assertNotIn(forbidden.lower(), normalized_key, key)
                self._assert_no_forbidden_private_or_execution_fields(nested)
        elif isinstance(value, list):
            for item in value:
                self._assert_no_forbidden_private_or_execution_fields(item)
        elif isinstance(value, str):
            normalized_value = value.lower()
            for forbidden in FORBIDDEN_FIELD_SUBSTRINGS:
                self.assertNotIn(forbidden.lower(), normalized_value, value)


if __name__ == "__main__":
    unittest.main()
