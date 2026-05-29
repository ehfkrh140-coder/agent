from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ForwardCompatibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class ExtensionModel(ForwardCompatibleModel):
    extensions: dict[str, Any] = Field(default_factory=dict)


class FeeSnapshot(ExtensionModel):
    trading_fee_pct: Optional[float] = None
    maker_fee_pct: Optional[float] = None
    taker_fee_pct: Optional[float] = None
    withdrawal_fee_asset: Optional[float] = None
    network_fee_asset: Optional[float] = None
    fee_tier: Optional[str] = None
    fee_source: Optional[str] = None


class LiquiditySnapshot(ExtensionModel):
    orderbook_depth_available: bool = False
    volume_available: bool = False
    estimated_executable_notional: Optional[float] = None
    estimated_slippage_pct: Optional[float] = None
    depth_levels: list[dict[str, Any]] = Field(default_factory=list)


class TransferSnapshot(ExtensionModel):
    status_known: bool = False
    withdrawal_enabled: Optional[bool] = None
    deposit_enabled: Optional[bool] = None
    estimated_minutes: Optional[float] = None
    network: Optional[str] = None
    status_source: Optional[str] = None


class DerivativesSnapshot(ExtensionModel):
    funding_rate_pct: Optional[float] = None
    next_funding_time_utc: Optional[datetime] = None
    open_interest: Optional[float] = None
    mark_price: Optional[float] = None
    index_price: Optional[float] = None


class DataQualitySnapshot(ExtensionModel):
    timestamps_available: bool = False
    timestamps_aligned: Optional[bool] = None
    max_data_age_ms: Optional[int] = None
    source: Optional[str] = None
    latency_ms: Optional[int] = None
    is_realtime: Optional[bool] = None


class VenueHealthSnapshot(ExtensionModel):
    api_status_known: bool = False
    api_ok: Optional[bool] = None
    maintenance: Optional[bool] = None
    trading_enabled: Optional[bool] = None
    message: Optional[str] = None


class MarketObservation(ExtensionModel):
    observation_id: Optional[str] = None
    venue_id: str
    venue_name: str
    market_symbol: str
    instrument_type: Optional[str] = None
    region: Optional[str] = None
    last_price: Optional[float] = None
    mark_price: Optional[float] = None
    index_price: Optional[float] = None
    leverage: Optional[float] = None
    max_leverage: Optional[float] = None
    unit: Optional[float] = None
    tick: Optional[float] = None
    step: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None
    base_volume_24h: Optional[float] = None
    quote_volume_24h: Optional[float] = None
    timestamp_utc: Optional[datetime] = None
    fees: Optional[FeeSnapshot] = None
    liquidity: Optional[LiquiditySnapshot] = None
    transfer: Optional[TransferSnapshot] = None
    derivatives: Optional[DerivativesSnapshot] = None
    data_quality: Optional[DataQualitySnapshot] = None
    health: Optional[VenueHealthSnapshot] = None


class OpportunityCandidate(ExtensionModel):
    candidate_id: Optional[str] = None
    candidate_type: str
    strategy_family: Optional[str] = None
    strategy_id: Optional[str] = None
    side_candidate: Optional[str] = None
    source_observation_id: Optional[str] = None
    target_observation_id: Optional[str] = None
    source_venue_id: Optional[str] = None
    target_venue_id: Optional[str] = None
    direction: Optional[str] = None
    gross_gap_absolute: Optional[float] = None
    gross_gap_pct: Optional[float] = None
    estimated_net_gap_pct: Optional[float] = None
    target_gap_pct: Optional[float] = None
    long_gap_pct: Optional[float] = None
    short_gap_pct: Optional[float] = None
    long_notional: Optional[float] = None
    short_notional: Optional[float] = None
    liquidity_pass: Optional[bool] = None
    gap_pass: Optional[bool] = None
    freshness_pass: Optional[bool] = None
    guard_pass: Optional[bool] = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    guards: dict[str, Any] = Field(default_factory=dict)
    thresholds: dict[str, Any] = Field(default_factory=dict)
    required_missing_fields: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class HumanAuthority(ForwardCompatibleModel):
    can_block_trade: bool = True
    can_force_trade: bool = False
    can_tighten_risk: bool = True
    can_loosen_risk: bool = False


class HumanContext(ForwardCompatibleModel):
    provided: bool = False
    blocking: bool = False
    thesis: Optional[str] = None
    preference: Optional[str] = None
    constraints: list[str] = Field(default_factory=list)
    veto: bool = False
    questions_for_council: list[str] = Field(default_factory=list)
    authority: HumanAuthority = Field(default_factory=HumanAuthority)


class ExpectedBehavior(ForwardCompatibleModel):
    preferred_final_decision: Optional[str] = None
    acceptable_final_decisions: list[str] = Field(default_factory=list)
    must_not_include: list[str] = Field(default_factory=list)
    max_confidence: Optional[float] = None
    notes: Optional[str] = None


class DetectorMetadata(ExtensionModel):
    detector_name: Optional[str] = None
    detector_version: Optional[str] = None
    generated_from: Optional[str] = None
    source_files: list[str] = Field(default_factory=list)


class OpportunityPacket(ExtensionModel):
    schema_version: str = "opportunity_packet_v0"
    packet_id: str
    created_at_utc: Optional[datetime] = None
    asset: str
    quote: str
    signal_type: str
    strategy_family: Optional[str] = None
    strategy_id: Optional[str] = None
    observations: list[MarketObservation] = Field(default_factory=list)
    candidates: list[OpportunityCandidate] = Field(default_factory=list)
    human_context: Optional[HumanContext] = None
    expected_behavior: Optional[ExpectedBehavior] = None
    detector_metadata: Optional[DetectorMetadata] = None

    def agent_context_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"expected_behavior"})

    def expected_behavior_dict(self) -> Optional[dict[str, Any]]:
        return self.expected_behavior.model_dump(mode="json") if self.expected_behavior else None

    def summary_message(self) -> str:
        return (
            f"OpportunityPacket {self.packet_id}: {self.asset}/{self.quote} "
            f"signal_type={self.signal_type}, observations={len(self.observations)}, "
            f"candidates={len(self.candidates)}"
        )
