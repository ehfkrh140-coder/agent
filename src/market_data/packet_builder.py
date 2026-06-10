from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.market_data.orderbook_imbalance import compute_orderbook_imbalance
from src.strategy.tether_cross_market_premium import (
    classify_global_usdt_health,
    compute_domestic_mid,
    compute_domestic_spread,
    compute_domestic_spread_pct,
    compute_estimated_net_gap_pct,
)
from src.market_data.vwap import compute_buy_vwap_from_asks, compute_sell_vwap_from_bids
from src.schemas.opportunity_packet import (
    DataQualitySnapshot,
    DerivativesSnapshot,
    DetectorMetadata,
    FeeSnapshot,
    LiquiditySnapshot,
    MarketObservation,
    OpportunityCandidate,
    OpportunityPacket,
    VenueHealthSnapshot,
)


class OpportunityPacketBuilder:
    """Build OpportunityPacket v0 objects from read-only market data snapshots."""

    def build(self, snapshot: dict[str, Any]) -> OpportunityPacket:
        strategy_family = snapshot.get("strategy_family")
        if strategy_family == "mark_orderbook_gap_hunt":
            return self.build_mark_orderbook_gap_hunt(snapshot)
        if strategy_family == "mark_orderbook_gap":
            return self.build_mark_orderbook_gap(snapshot)
        if strategy_family == "spot_futures_basis":
            return self.build_spot_futures_basis(snapshot)
        if strategy_family == "cross_exchange_spot_spread":
            return self.build_cross_exchange_spot_spread(snapshot)
        if strategy_family == "orderbook_imbalance":
            return self.build_orderbook_imbalance(snapshot)
        if strategy_family == "tether_cross_market_premium":
            return self.build_tether_cross_market_premium(snapshot)
        raise ValueError(f"Unsupported strategy_family: {strategy_family!r}")

    def build_spot_futures_basis(self, snapshot: dict[str, Any]) -> OpportunityPacket:
        """Validate a Spot-Futures Basis adapter-produced packet dict.

        The Spot-Futures Basis adapter returns an analysis-only
        OpportunityPacket-compatible dictionary from ``fetch_snapshot``.
        This collect-path support branch intentionally performs validation
        only; it does not fetch live data, parse source bundles, calculate
        readiness, synthesize candidates, trigger Council/alerts, or add any
        trading behavior.
        """

        return OpportunityPacket.model_validate(snapshot)

    def build_mark_orderbook_gap_hunt(self, snapshot: dict[str, Any]) -> OpportunityPacket:
        """Build a Mark-Orderbook Gap Hunt packet from an adapter-produced packet dict.

        The Binance Mark-Orderbook Gap Hunt adapter returns an analysis-only
        OpportunityPacket JSON dictionary from ``fetch_snapshot`` so existing
        collect_market_data flow can serialize a packet after builder
        validation.  This path intentionally does not synthesize execution,
        Council, alert, or sampling fields; it only validates the already
        normalized public-read-only packet shape.
        """

        return OpportunityPacket.model_validate(snapshot)

    def build_mark_orderbook_gap(self, snapshot: dict[str, Any]) -> OpportunityPacket:
        raw_observations = snapshot.get("observations") or []
        observations = [self._observation(raw) for raw in raw_observations]
        candidates = [candidate for obs in observations for candidate in self._mark_candidates(obs, snapshot)]
        return OpportunityPacket(
            packet_id=snapshot.get("packet_id") or self._packet_id("mark_orderbook_gap"),
            created_at_utc=self._created_at(snapshot),
            asset=snapshot["asset"],
            quote=snapshot["quote"],
            signal_type="mark_orderbook_gap",
            strategy_family="mark_orderbook_gap",
            strategy_id=snapshot.get("strategy_id") or "mark_orderbook_gap_hunt_v0",
            observations=observations,
            candidates=candidates,
            detector_metadata=self._metadata(snapshot),
            extensions=snapshot.get("extensions", {}),
        )

    def build_cross_exchange_spot_spread(self, snapshot: dict[str, Any]) -> OpportunityPacket:
        raw_observations = snapshot.get("observations") or []
        observations = [self._observation(raw) for raw in raw_observations]
        candidates = self._spot_candidates(observations, snapshot)
        return OpportunityPacket(
            packet_id=snapshot.get("packet_id") or self._packet_id("cross_exchange_spot_spread"),
            created_at_utc=self._created_at(snapshot),
            asset=snapshot["asset"],
            quote=snapshot["quote"],
            signal_type="cross_exchange_price_gap",
            strategy_family="cross_exchange_spot_spread",
            strategy_id=snapshot.get("strategy_id") or "cross_exchange_spot_spread_v0",
            observations=observations,
            candidates=candidates,
            detector_metadata=self._metadata(snapshot),
            extensions=snapshot.get("extensions", {}),
        )


    def build_orderbook_imbalance(self, snapshot: dict[str, Any]) -> OpportunityPacket:
        raw_observations = snapshot.get("observations") or []
        observations = [self._observation(raw) for raw in raw_observations]
        candidates = self._orderbook_imbalance_candidates(observations, snapshot)
        return OpportunityPacket(
            packet_id=snapshot.get("packet_id") or self._packet_id("orderbook_imbalance"),
            created_at_utc=self._created_at(snapshot),
            asset=snapshot["asset"],
            quote=snapshot["quote"],
            signal_type="orderbook_imbalance",
            strategy_family="orderbook_imbalance",
            strategy_id=snapshot.get("strategy_id") or "orderbook_imbalance_v0",
            observations=observations,
            candidates=candidates,
            detector_metadata=self._metadata(snapshot),
            extensions=snapshot.get("extensions", {}),
        )

    def build_tether_cross_market_premium(self, snapshot: dict[str, Any]) -> OpportunityPacket:
        raw_observations = snapshot.get("observations") or []
        observations = [self._observation(raw) for raw in raw_observations]
        candidates = self._tether_cross_market_candidates(observations, snapshot)
        return OpportunityPacket(
            packet_id=snapshot.get("packet_id") or self._packet_id("tether_cross_market_premium"),
            created_at_utc=self._created_at(snapshot),
            asset=snapshot["asset"],
            quote=snapshot["quote"],
            signal_type="tether_cross_market_premium",
            strategy_family="tether_cross_market_premium",
            strategy_id=snapshot.get("strategy_id") or "usdt_krw_global_reference_v0",
            observations=observations,
            candidates=candidates,
            detector_metadata=self._metadata(snapshot),
            extensions=snapshot.get("extensions", {}),
        )

    def _observation(self, raw: dict[str, Any]) -> MarketObservation:
        data_quality = raw.get("data_quality") or {}
        fees = raw.get("fees")
        liquidity = raw.get("liquidity")
        health = raw.get("health")
        derivatives = raw.get("derivatives")
        return MarketObservation(
            observation_id=raw.get("observation_id"),
            venue_id=raw["venue_id"],
            venue_name=raw.get("venue_name") or raw["venue_id"],
            market_symbol=raw["market_symbol"],
            instrument_type=raw.get("instrument_type"),
            region=raw.get("region"),
            last_price=raw.get("last_price"),
            mark_price=raw.get("mark_price"),
            index_price=raw.get("index_price"),
            leverage=raw.get("leverage"),
            max_leverage=raw.get("max_leverage"),
            unit=raw.get("unit"),
            tick=raw.get("tick"),
            step=raw.get("step"),
            bid=raw.get("bid"),
            ask=raw.get("ask"),
            bid_size=raw.get("bid_size"),
            ask_size=raw.get("ask_size"),
            base_volume_24h=raw.get("base_volume_24h"),
            quote_volume_24h=raw.get("quote_volume_24h"),
            timestamp_utc=raw.get("timestamp_utc"),
            fees=FeeSnapshot.model_validate(fees) if fees else None,
            liquidity=LiquiditySnapshot.model_validate(liquidity) if liquidity else None,
            derivatives=DerivativesSnapshot.model_validate(derivatives) if derivatives else None,
            data_quality=DataQualitySnapshot.model_validate(data_quality) if data_quality else None,
            health=VenueHealthSnapshot.model_validate(health) if health else None,
            extensions=raw.get("extensions", {}),
        )

    def _mark_candidates(self, obs: MarketObservation, snapshot: dict[str, Any]) -> list[OpportunityCandidate]:
        thresholds = snapshot.get("thresholds", {})
        base_percent = float(thresholds.get("base_percent", 2.0))
        min_gap_floor_pct = float(thresholds.get("min_gap_floor_pct", 0.2))
        min_notional = float(thresholds.get("min_notional", 0.0))
        max_data_age_ms = thresholds.get("max_data_age_ms")
        leverage = obs.leverage or obs.max_leverage or 1.0
        target_gap_pct = max(base_percent / leverage, min_gap_floor_pct)
        guards = dict(snapshot.get("guards", {}))
        guard_pass = not any(
            bool(guards.get(key))
            for key in ("manual_blacklisted", "runtime_blocked", "open_position", "pending_duplicate")
        )
        freshness_pass = self._freshness_pass(obs, max_data_age_ms)
        candidates: list[OpportunityCandidate] = []
        if obs.mark_price and obs.ask and obs.ask_size is not None:
            long_gap_pct = ((obs.mark_price - obs.ask) / obs.mark_price) * 100
            long_notional = obs.ask * obs.ask_size * (obs.unit or 1)
            if long_gap_pct > 0:
                candidates.append(
                    OpportunityCandidate(
                        candidate_id=f"{obs.observation_id or obs.venue_id}_long",
                        candidate_type="mark_orderbook_gap_candidate",
                        strategy_family="mark_orderbook_gap",
                        strategy_id="mark_orderbook_gap_hunt_v0",
                        side_candidate="LONG",
                        source_observation_id=obs.observation_id,
                        source_venue_id=obs.venue_id,
                        direction="mark_orderbook_gap_long_candidate",
                        gross_gap_pct=round(long_gap_pct, 8),
                        estimated_net_gap_pct=None,
                        target_gap_pct=round(target_gap_pct, 8),
                        long_gap_pct=round(long_gap_pct, 8),
                        long_notional=round(long_notional, 8),
                        liquidity_pass=long_notional >= min_notional,
                        gap_pass=long_gap_pct >= target_gap_pct,
                        freshness_pass=freshness_pass,
                        guard_pass=guard_pass,
                        metrics={"base_percent": base_percent, "min_gap_floor_pct": min_gap_floor_pct},
                        guards=guards,
                        thresholds=thresholds,
                        required_missing_fields=self._missing_mark_fields(obs),
                    )
                )
        if obs.mark_price and obs.bid and obs.bid_size is not None:
            short_gap_pct = ((obs.bid - obs.mark_price) / obs.mark_price) * 100
            short_notional = obs.bid * obs.bid_size * (obs.unit or 1)
            if short_gap_pct > 0:
                candidates.append(
                    OpportunityCandidate(
                        candidate_id=f"{obs.observation_id or obs.venue_id}_short",
                        candidate_type="mark_orderbook_gap_candidate",
                        strategy_family="mark_orderbook_gap",
                        strategy_id="mark_orderbook_gap_hunt_v0",
                        side_candidate="SHORT",
                        source_observation_id=obs.observation_id,
                        source_venue_id=obs.venue_id,
                        direction="mark_orderbook_gap_short_candidate",
                        gross_gap_pct=round(short_gap_pct, 8),
                        estimated_net_gap_pct=None,
                        target_gap_pct=round(target_gap_pct, 8),
                        short_gap_pct=round(short_gap_pct, 8),
                        short_notional=round(short_notional, 8),
                        liquidity_pass=short_notional >= min_notional,
                        gap_pass=short_gap_pct >= target_gap_pct,
                        freshness_pass=freshness_pass,
                        guard_pass=guard_pass,
                        metrics={"base_percent": base_percent, "min_gap_floor_pct": min_gap_floor_pct},
                        guards=guards,
                        thresholds=thresholds,
                        required_missing_fields=self._missing_mark_fields(obs),
                    )
                )
        return candidates

    def _spot_candidates(self, observations: list[MarketObservation], snapshot: dict[str, Any]) -> list[OpportunityCandidate]:
        thresholds = snapshot.get("thresholds", {})
        min_notional = float(thresholds.get("min_notional") or thresholds.get("min_executable_notional") or 0.0)
        min_net_gap_pct = thresholds.get("min_net_gap_pct")
        safety_buffer_pct = float(thresholds.get("safety_buffer_pct", 0.0))
        target_notionals = self._target_notionals(snapshot, thresholds, min_notional)
        candidates: list[OpportunityCandidate] = []
        for source in observations:
            for target in observations:
                if source.venue_id == target.venue_id or source.ask is None or target.bid is None:
                    continue
                gross_spread = target.bid - source.ask
                if gross_spread <= 0:
                    continue
                gross_spread_pct = gross_spread / source.ask * 100
                source_depth = self._depth_levels_for_side(source, side="buy")
                target_depth = self._depth_levels_for_side(target, side="sell")
                source_fee_pct = self._fee_pct(source)
                target_fee_pct = self._fee_pct(target)
                vwap_results = [
                    self._spot_vwap_result(
                        source_depth=source_depth,
                        target_depth=target_depth,
                        target_notional=target_notional,
                        source_fee_pct=source_fee_pct,
                        target_fee_pct=target_fee_pct,
                        safety_buffer_pct=safety_buffer_pct,
                        min_net_gap_pct=min_net_gap_pct,
                    )
                    for target_notional in target_notionals
                ]
                default_result = vwap_results[0] if vwap_results else {}
                executable_notional = default_result.get("executable_notional")
                estimated_net_gap_pct = default_result.get("estimated_net_gap_pct")
                liquidity_pass = default_result.get("liquidity_pass")
                net_gap_pass = default_result.get("net_gap_pass")
                freshness_pass = self._freshness_pass(source, thresholds.get("max_data_age_ms")) and self._freshness_pass(
                    target, thresholds.get("max_data_age_ms")
                )
                candidates.append(
                    OpportunityCandidate(
                        candidate_id=f"{source.venue_id}_to_{target.venue_id}",
                        candidate_type="spot_executable_spread_candidate",
                        strategy_family="cross_exchange_spot_spread",
                        strategy_id=snapshot.get("strategy_id") or "cross_exchange_spot_spread_v0",
                        side_candidate="BUY_SOURCE_SELL_TARGET",
                        source_observation_id=source.observation_id,
                        target_observation_id=target.observation_id,
                        source_venue_id=source.venue_id,
                        target_venue_id=target.venue_id,
                        direction="buy_source_ask_sell_target_bid_candidate",
                        gross_gap_absolute=round(gross_spread, 8),
                        gross_gap_pct=round(gross_spread_pct, 8),
                        estimated_net_gap_pct=round(estimated_net_gap_pct, 8) if estimated_net_gap_pct is not None else None,
                        liquidity_pass=bool(liquidity_pass) if liquidity_pass is not None else None,
                        freshness_pass=freshness_pass,
                        gap_pass=True if net_gap_pass is None else bool(net_gap_pass),
                        guard_pass=True,
                        metrics={
                            "source_ask": source.ask,
                            "target_bid": target.bid,
                            "source_fee_pct": source_fee_pct,
                            "target_fee_pct": target_fee_pct,
                            "safety_buffer_pct": safety_buffer_pct,
                            "top_of_book_gross_gap_pct": round(gross_spread_pct, 8),
                            "executable_notional": executable_notional,
                            "net_gap_pass": net_gap_pass,
                            "vwap_results": vwap_results,
                        },
                        thresholds=thresholds,
                        required_missing_fields=self._missing_spot_fields(source, target),
                    )
                )
        return candidates


    def _orderbook_imbalance_candidates(self, observations: list[MarketObservation], snapshot: dict[str, Any]) -> list[OpportunityCandidate]:
        thresholds = snapshot.get("thresholds", {})
        threshold = float(thresholds.get("imbalance_ratio_threshold", 1.5))
        target_notional = self._optional_float(thresholds.get("target_notional"))
        max_data_age_ms = thresholds.get("max_data_age_ms")
        candidates: list[OpportunityCandidate] = []
        for obs in observations:
            freshness_pass = self._freshness_pass(obs, max_data_age_ms)
            metrics = compute_orderbook_imbalance(
                obs,
                threshold=threshold,
                target_notional=target_notional,
                max_data_age_ms=max_data_age_ms,
                freshness_pass=freshness_pass,
            )
            direction = metrics["direction"]
            candidates.append(
                OpportunityCandidate(
                    candidate_id=f"{obs.observation_id or obs.venue_id}_orderbook_imbalance",
                    candidate_type="orderbook_imbalance_signal",
                    strategy_family="orderbook_imbalance",
                    strategy_id=snapshot.get("strategy_id") or "orderbook_imbalance_v0",
                    source_observation_id=obs.observation_id,
                    source_venue_id=obs.venue_id,
                    direction=direction,
                    estimated_net_gap_pct=None,
                    liquidity_pass=metrics.get("liquidity_pass"),
                    freshness_pass=freshness_pass,
                    gap_pass=bool(metrics.get("imbalance_pass")),
                    guard_pass=True,
                    metrics=metrics,
                    thresholds={
                        "imbalance_ratio_threshold": threshold,
                        "max_data_age_ms": max_data_age_ms,
                        "target_notional": target_notional,
                    },
                    required_missing_fields=self._missing_orderbook_imbalance_fields(obs),
                    assumptions=[
                        "experimental non-active orderbook imbalance signal",
                        "not an executable spread and not a trade instruction",
                    ],
                )
            )
        return candidates

    def _tether_cross_market_candidates(self, observations: list[MarketObservation], snapshot: dict[str, Any]) -> list[OpportunityCandidate]:
        thresholds = snapshot.get("thresholds", {})
        safety_buffer_pct = float(thresholds.get("safety_buffer_pct", 0.0))
        min_net_gap_pct = self._optional_float(thresholds.get("min_net_gap_pct"))
        min_executable_notional = float(thresholds.get("min_executable_notional") or thresholds.get("min_notional") or 0.0)
        max_data_age_ms = thresholds.get("max_data_age_ms")
        global_mid, global_sources = self._global_usdt_reference(observations)
        health = classify_global_usdt_health(global_mid, thresholds.get("global_depeg_threshold_pct", 0.5))
        global_depeg_flag = health.get("global_usdt_depeg_flag")
        global_reference_pass = bool(global_sources) and global_depeg_flag is False
        domestic = {obs.venue_id.lower(): obs for obs in observations if self._is_tether_domestic_observation(obs)}
        candidates: list[OpportunityCandidate] = []
        for source_id, target_id in (("upbit", "bithumb"), ("bithumb", "upbit")):
            source = domestic.get(source_id)
            target = domestic.get(target_id)
            if source is None or target is None:
                continue
            candidate = self._tether_domestic_candidate(
                source=source,
                target=target,
                snapshot=snapshot,
                thresholds=thresholds,
                safety_buffer_pct=safety_buffer_pct,
                min_net_gap_pct=min_net_gap_pct,
                min_executable_notional=min_executable_notional,
                max_data_age_ms=max_data_age_ms,
                global_mid=global_mid,
                global_sources=global_sources,
                global_health=health,
                global_reference_pass=global_reference_pass,
            )
            candidates.append(candidate)
        return candidates

    def _tether_domestic_candidate(
        self,
        *,
        source: MarketObservation,
        target: MarketObservation,
        snapshot: dict[str, Any],
        thresholds: dict[str, Any],
        safety_buffer_pct: float,
        min_net_gap_pct: float | None,
        min_executable_notional: float,
        max_data_age_ms: Any,
        global_mid: float | None,
        global_sources: list[str],
        global_health: dict[str, Any],
        global_reference_pass: bool,
    ) -> OpportunityCandidate:
        gross_spread = compute_domestic_spread(source.ask, target.bid)
        gross_gap_pct = compute_domestic_spread_pct(source.ask, target.bid)
        source_fee_pct = self._fee_pct(source)
        target_fee_pct = self._fee_pct(target)
        source_slippage_pct = self._slippage_pct(source) or 0.0
        target_slippage_pct = self._slippage_pct(target) or 0.0
        estimated_slippage_pct = source_slippage_pct + target_slippage_pct
        estimated_net_gap_pct = compute_estimated_net_gap_pct(
            gross_gap_pct,
            source_fee_pct,
            target_fee_pct,
            estimated_slippage_pct,
            safety_buffer_pct,
        )
        source_notional = source.ask * source.ask_size if source.ask is not None and source.ask_size is not None else 0.0
        target_notional = target.bid * target.bid_size if target.bid is not None and target.bid_size is not None else 0.0
        executable_notional = min(source_notional, target_notional)
        liquidity_pass = executable_notional >= min_executable_notional if min_executable_notional else executable_notional > 0
        source_fresh = self._freshness_pass(source, max_data_age_ms)
        target_fresh = self._freshness_pass(target, max_data_age_ms)
        freshness_pass = bool(source_fresh and target_fresh)
        net_gap_pass = None
        if estimated_net_gap_pct is not None and min_net_gap_pct is not None:
            net_gap_pass = estimated_net_gap_pct >= min_net_gap_pct
        domestic_best_bid = max(value for value in [source.bid, target.bid] if value is not None) if source.bid is not None or target.bid is not None else None
        domestic_best_ask = min(value for value in [source.ask, target.ask] if value is not None) if source.ask is not None or target.ask is not None else None
        direction = f"buy_{source.venue_id}_sell_{target.venue_id}_usdt_krw_signal"
        metrics = {
            "source_ask": source.ask,
            "target_bid": target.bid,
            "gross_gap_pct": self._round_optional(gross_gap_pct),
            "estimated_net_gap_pct": self._round_optional(estimated_net_gap_pct),
            "source_fee_pct": source_fee_pct,
            "target_fee_pct": target_fee_pct,
            "estimated_slippage_pct": self._round_optional(estimated_slippage_pct),
            "safety_buffer_pct": safety_buffer_pct,
            "executable_notional": self._round_optional(executable_notional),
            "domestic_best_bid": domestic_best_bid,
            "domestic_best_ask": domestic_best_ask,
            "domestic_mid": self._round_optional(compute_domestic_mid(domestic_best_bid, domestic_best_ask)),
            "global_usdt_mid": self._round_optional(global_mid),
            "global_usdt_depeg_pct": self._round_optional(global_health.get("global_usdt_depeg_pct")),
            "global_usdt_depeg_flag": global_health.get("global_usdt_depeg_flag"),
            "global_reference_venue_count": len(global_sources),
            "global_reference_sources": global_sources,
            "global_reference_pass": global_reference_pass,
            "liquidity_pass": liquidity_pass,
            "freshness_pass": freshness_pass,
            "net_gap_pass": net_gap_pass,
        }
        return OpportunityCandidate(
            candidate_id=f"{source.venue_id}_to_{target.venue_id}_tether_cross_market",
            candidate_type="tether_domestic_spread_signal",
            strategy_family="tether_cross_market_premium",
            strategy_id=snapshot.get("strategy_id") or "usdt_krw_global_reference_v0",
            side_candidate="BUY_SOURCE_SELL_TARGET",
            source_observation_id=source.observation_id,
            target_observation_id=target.observation_id,
            source_venue_id=source.venue_id,
            target_venue_id=target.venue_id,
            direction=direction,
            gross_gap_absolute=self._round_optional(gross_spread),
            gross_gap_pct=self._round_optional(gross_gap_pct),
            estimated_net_gap_pct=self._round_optional(estimated_net_gap_pct),
            liquidity_pass=liquidity_pass,
            freshness_pass=freshness_pass,
            gap_pass=bool(net_gap_pass) if net_gap_pass is not None else None,
            guard_pass=True,
            metrics=metrics,
            thresholds=thresholds,
            required_missing_fields=self._missing_tether_fields(source, target),
            assumptions=[
                "experimental non-active tether cross-market replay signal",
                "global references are depeg/reference checks, not execution venues",
                "no private API and no trading behavior",
            ],
        )

    def _global_usdt_reference(self, observations: list[MarketObservation]) -> tuple[float | None, list[str]]:
        mids: list[float] = []
        sources: list[str] = []
        for obs in observations:
            if not self._is_tether_global_reference_observation(obs):
                continue
            if obs.bid is None or obs.ask is None:
                continue
            mids.append((obs.bid + obs.ask) / 2)
            sources.append(obs.venue_id)
        if not mids:
            return None, []
        ordered = sorted(mids)
        midpoint = len(ordered) // 2
        if len(ordered) % 2:
            median = ordered[midpoint]
        else:
            median = (ordered[midpoint - 1] + ordered[midpoint]) / 2
        return median, sources

    def _is_tether_domestic_observation(self, obs: MarketObservation) -> bool:
        symbol = (obs.market_symbol or "").upper().replace("-", "/")
        return (obs.venue_id or "").lower() in {"upbit", "bithumb"} and symbol == "USDT/KRW"

    def _is_tether_global_reference_observation(self, obs: MarketObservation) -> bool:
        if obs.extensions.get("reference_role") == "global_usdt_reference":
            return True
        symbol = (obs.market_symbol or "").upper().replace("-", "/")
        return (obs.venue_id or "").lower() in {"binance", "bybit", "okx"} and symbol in {"USDT/USD", "USDT/USDC", "USDC/USDT"}

    def _missing_tether_fields(self, source: MarketObservation, target: MarketObservation) -> list[str]:
        missing: list[str] = []
        for label, obs in (("source", source), ("target", target)):
            for field_name in ["bid", "ask", "bid_size", "ask_size"]:
                if getattr(obs, field_name) is None:
                    missing.append(f"{label}.{field_name}")
            if obs.fees is None:
                missing.append(f"{label}.fees")
            if obs.liquidity is None or not obs.liquidity.depth_levels:
                missing.append(f"{label}.liquidity.depth_levels")
            if obs.timestamp_utc is None:
                missing.append(f"{label}.timestamp_utc")
            if obs.data_quality is None or obs.data_quality.max_data_age_ms is None:
                missing.append(f"{label}.data_quality.max_data_age_ms")
            if obs.data_quality is None or obs.data_quality.latency_ms is None:
                missing.append(f"{label}.data_quality.latency_ms")
        return missing

    def _missing_orderbook_imbalance_fields(self, obs: MarketObservation) -> list[str]:
        missing: list[str] = []
        for field_name in ["bid", "ask", "bid_size", "ask_size"]:
            if getattr(obs, field_name) is None:
                missing.append(field_name)
        if obs.liquidity is None or not obs.liquidity.depth_levels:
            missing.append("liquidity.depth_levels")
        if obs.timestamp_utc is None and (obs.data_quality is None or not obs.data_quality.timestamps_available):
            missing.append("timestamp")
        if obs.data_quality is None or obs.data_quality.max_data_age_ms is None:
            missing.append("data_quality.max_data_age_ms")
        if obs.data_quality is None or obs.data_quality.latency_ms is None:
            missing.append("data_quality.latency_ms")
        return missing

    def _optional_float(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _target_notionals(self, snapshot: dict[str, Any], thresholds: dict[str, Any], min_notional: float) -> list[float]:
        raw_values = snapshot.get("target_notionals") or thresholds.get("target_notionals") or []
        notionals: list[float] = []
        if isinstance(raw_values, list):
            for value in raw_values:
                try:
                    notional = float(value)
                except (TypeError, ValueError):
                    continue
                if notional > 0:
                    notionals.append(notional)
        if not notionals:
            notionals.append(min_notional if min_notional > 0 else 1_000_000.0)
        return notionals

    def _spot_vwap_result(
        self,
        *,
        source_depth: list[dict[str, Any]],
        target_depth: list[dict[str, Any]],
        target_notional: float,
        source_fee_pct: float | None,
        target_fee_pct: float | None,
        safety_buffer_pct: float,
        min_net_gap_pct: Any,
    ) -> dict[str, Any]:
        buy = compute_buy_vwap_from_asks(source_depth, target_notional)
        sell = compute_sell_vwap_from_bids(target_depth, target_notional)
        executable_notional = min(float(buy.get("filled_notional") or 0.0), float(sell.get("filled_notional") or 0.0))
        source_vwap = buy.get("vwap_price")
        target_vwap = sell.get("vwap_price")
        source_slippage_pct = buy.get("slippage_pct")
        target_slippage_pct = sell.get("slippage_pct")
        combined_slippage_pct = None
        if source_slippage_pct is not None and target_slippage_pct is not None:
            combined_slippage_pct = float(source_slippage_pct) + float(target_slippage_pct)
        vwap_gross_gap_pct = None
        if source_vwap and target_vwap:
            vwap_gross_gap_pct = ((float(target_vwap) - float(source_vwap)) / float(source_vwap)) * 100
        estimated_net_gap_pct = None
        if (
            vwap_gross_gap_pct is not None
            and source_fee_pct is not None
            and target_fee_pct is not None
            and combined_slippage_pct is not None
        ):
            estimated_net_gap_pct = vwap_gross_gap_pct - source_fee_pct - target_fee_pct - combined_slippage_pct - safety_buffer_pct
        net_gap_pass = None
        if estimated_net_gap_pct is not None and min_net_gap_pct is not None:
            net_gap_pass = estimated_net_gap_pct >= float(min_net_gap_pct)
        liquidity_pass = bool(buy.get("fully_filled")) and bool(sell.get("fully_filled"))
        return {
            "target_notional": round(float(target_notional), 8),
            "source_vwap_ask": self._round_optional(source_vwap),
            "target_vwap_bid": self._round_optional(target_vwap),
            "source_slippage_pct": self._round_optional(source_slippage_pct),
            "target_slippage_pct": self._round_optional(target_slippage_pct),
            "combined_slippage_pct": self._round_optional(combined_slippage_pct),
            "vwap_gross_gap_pct": self._round_optional(vwap_gross_gap_pct),
            "estimated_net_gap_pct": self._round_optional(estimated_net_gap_pct),
            "fully_filled_source": bool(buy.get("fully_filled")),
            "fully_filled_target": bool(sell.get("fully_filled")),
            "source_filled_notional": self._round_optional(buy.get("filled_notional")),
            "target_filled_notional": self._round_optional(sell.get("filled_notional")),
            "executable_notional": self._round_optional(executable_notional),
            "source_levels_consumed": buy.get("levels_consumed"),
            "target_levels_consumed": sell.get("levels_consumed"),
            "source_top_ask": self._round_optional(buy.get("top_price")),
            "target_top_bid": self._round_optional(sell.get("top_price")),
            "net_gap_pass": net_gap_pass,
            "liquidity_pass": liquidity_pass,
        }

    def _depth_levels_for_side(self, obs: MarketObservation, *, side: str) -> list[dict[str, Any]]:
        if obs.liquidity and obs.liquidity.depth_levels:
            return obs.liquidity.depth_levels
        if side == "buy" and obs.ask is not None and obs.ask_size is not None:
            return [{"level": 1, "ask_price": obs.ask, "ask_size": obs.ask_size}]
        if side == "sell" and obs.bid is not None and obs.bid_size is not None:
            return [{"level": 1, "bid_price": obs.bid, "bid_size": obs.bid_size}]
        return []

    def _round_optional(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return round(float(value), 8)
        except (TypeError, ValueError):
            return None


    def _fee_pct(self, obs: MarketObservation) -> float | None:
        if obs.fees is None:
            return None
        for value in (obs.fees.trading_fee_pct, obs.fees.taker_fee_pct, obs.fees.maker_fee_pct):
            if value is not None:
                return value
        return None

    def _slippage_pct(self, obs: MarketObservation) -> float | None:
        if obs.liquidity is None:
            return None
        return obs.liquidity.estimated_slippage_pct

    def _missing_mark_fields(self, obs: MarketObservation) -> list[str]:
        missing: list[str] = []
        if obs.fees is None:
            missing.append("fees")
        if obs.liquidity is None or obs.liquidity.estimated_slippage_pct is None:
            missing.append("liquidity.estimated_slippage_pct")
        if obs.data_quality is None or obs.data_quality.max_data_age_ms is None:
            missing.append("data_quality.max_data_age_ms")
        return missing

    def _missing_spot_fields(self, source: MarketObservation, target: MarketObservation) -> list[str]:
        missing: list[str] = []
        for label, obs in (("source", source), ("target", target)):
            if obs.fees is None:
                missing.append(f"{label}.fees")
            if obs.liquidity is None or not obs.liquidity.orderbook_depth_available:
                missing.append(f"{label}.liquidity.depth_levels")
            if obs.liquidity is None or obs.liquidity.estimated_slippage_pct is None:
                missing.append(f"{label}.liquidity.estimated_slippage_pct")
            if obs.data_quality is None or obs.data_quality.max_data_age_ms is None:
                missing.append(f"{label}.data_quality.max_data_age_ms")
        return missing

    def _freshness_pass(self, obs: MarketObservation, max_data_age_ms: Any) -> bool | None:
        if max_data_age_ms is None:
            return None
        if obs.data_quality is None or obs.data_quality.max_data_age_ms is None:
            return False
        return obs.data_quality.max_data_age_ms <= max_data_age_ms

    def _metadata(self, snapshot: dict[str, Any]) -> DetectorMetadata:
        adapter_metadata = snapshot.get("adapter_metadata", {})
        return DetectorMetadata(
            detector_name="read_only_market_data_adapter_v0",
            detector_version="v0",
            generated_from=adapter_metadata.get("adapter_type", "replay"),
            source_files=[adapter_metadata.get("fixture_path", "")],
            extensions={"adapter_id": adapter_metadata.get("adapter_id")},
        )

    def _created_at(self, snapshot: dict[str, Any]) -> datetime:
        value = snapshot.get("created_at_utc")
        if value:
            if isinstance(value, datetime):
                return value
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return datetime.now(timezone.utc)

    def _packet_id(self, prefix: str) -> str:
        return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
