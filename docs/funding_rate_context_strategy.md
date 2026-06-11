# Funding Rate Context Strategy

## Purpose

`funding_rate_context_v0` is a planning-only context strategy candidate. It is not a trading strategy at this stage.

The purpose is to define how public perpetual-futures funding-rate data could later be normalized and attached as context / diagnostics / regime information for strategy review. Funding rate can help describe perpetual-market regime, crowding, and carry pressure, and may later support manual review around `spot_futures_basis_v0`, `mark_orderbook_gap_hunt_v0`, or other derivatives-oriented candidates.

Funding rate alone must not cause `WATCH`, `ENTER`, active promotion, alert execution, Council auto-call, order placement, or any execution behavior.

## Non-Goals

This document does not implement or authorize:

- Funding Rate endpoint calls.
- Funding Rate adapter code.
- Funding Rate parser code.
- Funding Rate packet builder code.
- Funding Rate readiness logic.
- Funding Rate sampling collectors.
- VWAP-adjusted readiness.
- Live endpoint calls or generated JSON artifacts.
- Active strategy promotion.
- Trading signals, alerts, orders, transfers, withdrawals, deposits, auto-trading, or Council auto-call.
- Private API, credentials, account lookup, balance lookup, or position lookup.

## Strategy Role

Funding Rate starts as context / diagnostics / regime information.

Funding Rate may answer reviewer questions such as:

- Is a perpetual market showing unusual carry pressure?
- Is funding positive, negative, zero, capped/floored, stale, or unusually large in absolute value?
- Is the funding interval standard or venue-adjusted?
- Does funding context help explain basis or derivatives-market observations without changing readiness?

Funding Rate must not answer:

- Should the system enter a trade?
- Should a Council review auto-run?
- Should an alert fire?
- Should a strategy be promoted to active?
- Is an order executable?

## Public Source Candidates

The table below records public-read-only source candidates from official exchange documentation. No endpoint was called for this PR.

| venue | endpoint candidate | source type | expected fields | public-read-only? | private API needed? | rate-limit / pagination note | timestamp semantics | funding interval note | implementation status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Binance USDⓈ-M Futures | `GET /fapi/v1/fundingRate` | Funding history candidate | `symbol`, `fundingRate`, `fundingTime`, `markPrice` | Yes | No | Official docs list default `limit=100`, max `1000`, ascending order, and shared 500/5min/IP limit with funding info. Source: <https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History> | `fundingTime` is a millisecond timestamp associated with the funding record. | Historical records do not themselves prove interval; interval context should come from observed deltas or funding info when available. | Planned only; no implementation. |
| Binance USDⓈ-M Futures | `GET /fapi/v1/fundingInfo` | Funding cap/floor/interval context candidate | `symbol`, `adjustedFundingRateCap`, `adjustedFundingRateFloor`, `fundingIntervalHours` | Yes | No | Official docs list request weight `0` and shared 500/5min/IP limit with funding history. Source: <https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-Info> | No funding event timestamp in the documented example; this should be auxiliary context, not the event source. | `fundingIntervalHours` can provide cap/floor/interval context for adjusted symbols. | Planned only; no implementation. |
| Bybit V5 | `GET /v5/market/funding/history` | Funding history candidate | `category`, `symbol`, `fundingRate`, `fundingRateTimestamp` | Yes | No | Official docs list `category` and `symbol` as required, `limit` range `1` to `200`, default `200`; source notes each symbol has a different funding interval. Source: <https://bybit-exchange.github.io/docs/v5/market/history-fund-rate> | `fundingRateTimestamp` is a millisecond timestamp for the funding record. | Official docs say to query funding interval through instruments info. | Planned only; no implementation. |
| Bybit V5 | `GET /v5/market/instruments-info` | Instrument metadata / funding interval candidate | `category`, `symbol`, `contractType`, `fundingInterval`, `upperFundingRate`, `lowerFundingRate`, `settleCoin` | Yes | No | Official docs include cursor pagination via `nextPageCursor` and `limit`; source: <https://bybit-exchange.github.io/docs/v5/market/instrument> | Instrument metadata has launch/delivery times, not funding event time. | `fundingInterval` is documented in minutes for linear/inverse instruments; category must distinguish `linear` vs `inverse`. | Planned only; no implementation. |
| OKX | `GET /api/v5/public/funding-rate` | Current/predicted funding candidate | `instType`, `instId`, `fundingRate`, `fundingTime`, `nextFundingTime`, `settFundingRate`, `premium`, `ts`, `method`, `formulaType` plus possible cap/floor fields depending on response version | Yes | No | Official public-data docs list this as a public REST endpoint; OKX changelog records funding formula-related response fields. Sources: <https://www.okx.com/docs-v5/en/> and <https://www.okx.com/docs-v5/log_en/> | `fundingTime`, `nextFundingTime`, and `ts` are millisecond timestamps with distinct meanings. | Do not assume fixed 8h; OKX says users should focus on the difference between `fundingTime` and `nextFundingTime` to determine the interval. | Planned only; no implementation. |
| OKX | `GET /api/v5/public/funding-rate-history` | Funding history candidate | `instType`, `instId`, `fundingRate`, `realizedRate`, `fundingTime`, `method`, `formulaType` | Yes | No | Official public-data docs list this endpoint; OKX changelog includes `formulaType` for funding history. Sources: <https://www.okx.com/docs-v5/en/> and <https://www.okx.com/docs-v5/log_en/> | `fundingTime` identifies the historical funding event; response semantics must be separated from current predicted fields. | Derive or validate interval from adjacent funding timestamps or current endpoint fields, not a fixed constant. | Planned only; no implementation. |

## Common Source Contract Draft

This is a draft normalized funding context contract. It is a documentation-only contract and does not add fields to code.

| field name | required / optional | meaning | venue-specific source | parser note | context-only guardrail |
| --- | --- | --- | --- | --- | --- |
| `venue` | required | Exchange identifier such as `binance`, `bybit`, or `okx`. | All sources. | Normalize to stable lowercase internal value. | Venue label is metadata, not a signal. |
| `instrument_id` | required | Venue-native instrument or symbol ID. | Binance `symbol`; Bybit `symbol`; OKX `instId`. | Preserve venue-native ID for auditability. | Instrument ID does not imply tradability or execution permission. |
| `instrument_type` | required | Product type such as USDⓈ-M perpetual, linear perpetual, inverse perpetual, or swap. | Binance endpoint family; Bybit `category`/`contractType`; OKX `instType`. | Must distinguish linear/inverse/swap semantics. | Product type is context only. |
| `symbol_normalized` | optional | Repository-normalized symbol, if mapping is available. | Derived from venue symbol/instId. | Missing mapping should be optional unless a future strategy requires it. | Normalized symbol does not promote a strategy. |
| `funding_rate` | required | Primary funding rate for the selected record. | Binance `fundingRate`; Bybit `fundingRate`; OKX current/history `fundingRate`. | Parse string numerics to decimal in future parser; preserve raw in fixtures. | Funding rate is not an entry signal. |
| `funding_rate_timestamp_ms` | required | Timestamp for the funding-rate record or settlement reference. | Binance `fundingTime`; Bybit `fundingRateTimestamp`; OKX `fundingTime`. | Must be milliseconds; reject or warn on unparseable values. | Timestamp freshness is diagnostic only. |
| `funding_interval_hours` | optional | Funding interval expressed in hours when known. | Binance `fundingIntervalHours`; Bybit `fundingInterval` minutes converted to hours; OKX `nextFundingTime - fundingTime` when applicable. | Do not default all venues to 8h; derive from source fields or observed deltas. | Interval is context only. |
| `next_funding_time_ms` | optional | Next funding timestamp for current/predicted funding context. | OKX `nextFundingTime`; possible future current endpoints if researched. | Separate from historical funding timestamp. | Countdown/timing is not an instruction to trade. |
| `realized_funding_rate` | optional | Settled or realized funding rate after settlement. | OKX `realizedRate`; OKX `settFundingRate` depending on semantics; Binance/Bybit historical `fundingRate` may be interpreted as settled after source review. | Keep venue semantics explicit in `source_semantics`. | Realized value is context/evidence, not a trigger. |
| `predicted_funding_rate` | optional | Current or predicted funding rate before settlement. | OKX current `fundingRate`/possible `nextFundingRate`; venue-specific current endpoints if later approved. | Must not be mixed with realized fields. | Prediction is not guaranteed and not executable. |
| `funding_cap` | optional | Upper funding cap/limit. | Binance `adjustedFundingRateCap`; Bybit `upperFundingRate`; OKX max/cap field if present. | Parse numeric strings; cap source may be endpoint-specific. | Cap context is not active-promotion evidence. |
| `funding_floor` | optional | Lower funding floor/limit. | Binance `adjustedFundingRateFloor`; Bybit `lowerFundingRate`; OKX min/floor field if present. | Parse numeric strings; floor source may be endpoint-specific. | Floor context is not active-promotion evidence. |
| `mark_price_reference` | optional | Mark price attached to a funding record if provided. | Binance `markPrice`; other venue current funding records if later confirmed. | Mark price is a reference, not executable price. | Mark price must not imply fill feasibility. |
| `premium_index_reference` | optional | Premium index or premium field associated with funding calculation. | OKX `premium`; possible venue premium-index endpoints in future. | Keep formula/source version explicit. | Premium context is not an order signal. |
| `source_endpoint` | required | Endpoint candidate that produced the payload. | All planned sources. | Store endpoint path, not full signed/private URL. | Endpoint name does not authorize calls in this PR. |
| `source_payload_timestamp_ms` | optional | Exchange-returned payload time, if distinct from funding time. | OKX `ts`; Bybit response `time`; other source-level timestamps if available. | Distinguish payload time from funding event time. | Payload time supports freshness diagnostics only. |
| `local_observed_at_ms` | optional | Local collection observation time. | Future adapter collection metadata. | Must be local monotonic/wall-clock metadata if implemented. | Local time is not market signal. |
| `data_age_ms` | optional | Derived age between local observation and source timestamp. | Derived from timestamp fields. | Must handle negative age/clock skew warnings. | Data age can reject/flag data only if a future policy approves; this PR is planning only. |
| `clock_skew_warning` | optional | Warning when source/local timestamps appear inconsistent. | Derived. | Preserve timestamp/data_age watch item. | Warning is diagnostics only. |
| `source_semantics` | required | Declares predicted, realized, current, historical, cap/floor, interval, or mixed context semantics. | Derived from endpoint and fields. | Required to prevent predicted/settled confusion. | Semantics label prevents signal misuse. |
| `parser_status` | required | Future parser outcome such as `ok`, `need_data`, or `invalid_payload`. | Future parser. | Planning only; no parser implemented here. | Parser status is not Council recommendation. |
| `required_missing_fields` | required | Required fields missing from normalized observation. | Future parser. | Empty list means source contract satisfied, not that an edge exists. | Missing fields do not trigger orders. |
| `optional_missing_fields` | optional | Optional/context fields absent from payload. | Future parser. | Optional absence should not fail core context unless policy says so. | Optional context absence is not no-trade failure. |
| `warnings` | optional | Non-fatal parser/source warnings. | Future parser. | Include stale data, interval uncertainty, numeric parsing, product mismatch. | Warnings are review context only. |

## Venue-Specific Semantics

### Binance USDⓈ-M Futures

- `GET /fapi/v1/fundingRate` is a funding history candidate with `symbol`, `fundingRate`, `fundingTime`, and `markPrice` in the official response example.
- `markPrice` is attached to a funding-fee record and must remain a mark/reference price, not executable price.
- `GET /fapi/v1/fundingInfo` is an auxiliary funding info candidate for adjusted cap, floor, and interval context.
- `fundingInfo` should not be treated as the primary funding event source. It is cap/floor/interval context only unless a future source-research PR decides otherwise.

### Bybit V5

- `GET /v5/market/funding/history` covers USDT/USDC perpetual and inverse perpetual products and requires `category` and `symbol`.
- `category` must distinguish `linear` and `inverse`; parser planning must not collapse those product semantics.
- The funding history response includes `fundingRate` and `fundingRateTimestamp`.
- Bybit docs direct users to `instruments-info` for the funding interval; instrument fields include `fundingInterval`, `upperFundingRate`, and `lowerFundingRate`.

### OKX

- `GET /api/v5/public/funding-rate` is a current funding candidate with predicted/current and next-funding timing context.
- `GET /api/v5/public/funding-rate-history` is a historical funding candidate.
- `fundingRate`, `realizedRate`, and `settFundingRate` must be separated by source semantics before normalization.
- `premium`, `method`, and `formulaType` are formula/context fields, not trade instructions.
- Do not assume a fixed 8-hour interval; use `fundingTime` / `nextFundingTime` differences or history deltas when available.


## Strategy Module Boundary Placement

`funding_rate_context_v0` maps to the existing Strategy Module Boundary Map as follows:

| layer | funding-rate placement | implementation status |
| --- | --- | --- |
| Venue Data Layer | Candidate future layer for collecting raw payloads from public funding endpoints only. | Not implemented in this PR. |
| Venue Parser Layer | Candidate future layer for converting raw funding payloads into normalized funding observations. | Not implemented in this PR. |
| Strategy Source Contract Layer | Defines normalized funding context fields, required/optional fields, source semantics, parser status, warnings, and timestamp/data-age fields. | Main planning scope of this PR. |
| Strategy Plugin Layer | Defines planning-only metadata, lifecycle, execution policy, and source-contract expectations for `funding_rate_context_v0`. | Metadata draft only; no plugin code. |
| Context / Diagnostics Layer | Funding Rate may later attach to packet/candidate extensions as context-only regime diagnostics. | Planned only; no extension code. |
| Readiness Layer | Funding Rate must not change `NEED_DATA`, `REJECT`, `WATCH`, `recommended_default_decision`, persistence, or active status without separate approved policy planning. | Unchanged. |
| Sampling / Evidence Layer | Future summaries may count context seen/missing, high absolute funding, timestamp warnings, and predicted/realized availability. | Planned only; no collector and no generated JSON. |
| Dashboard / Council Handoff Layer | Funding Rate may appear as dashboard watch/context status but not as trading signal or execution permission. | Planned only; dashboard not modified. |
| Governance Layer | `NO_TRADE_ONLY`, private API ban, generated JSON ban, active-promotion ban, and handoff source-of-truth remain controlling. | Preserved. |

## Plugin Metadata Draft

Planning-only metadata for the future context strategy:

| metadata key | draft value |
| --- | --- |
| `strategy_family` | `funding_rate_context` |
| `strategy_id` | `funding_rate_context_v0` |
| `lifecycle_status` | `planning / proposed / experimental / non-active` |
| `execution_policy` | `NO_TRADE_ONLY` |
| `primary_role` | `context / diagnostics / regime information` |
| `active_promotion_allowed` | `false` |
| `standalone_signal_allowed` | `false` |
| `readiness_changes_allowed` | `false` |
| `council_auto_call_allowed` | `false` |
| `alert_allowed` | `false` |
| `private_api_allowed` | `false` |

This metadata is not a registry change and does not create a runtime plugin. It is a planning contract for future implementation review.

## Predicted vs Realized Funding

Predicted/current funding and realized/settled funding are different source semantics.

- Predicted/current funding is context about a future or current funding cycle and may change before settlement.
- Realized/settled funding is context about a completed or settlement-used funding value.
- Funding timestamp identifies the relevant funding event or settlement reference.
- Next funding timestamp identifies a future settlement boundary.
- Cap/floor fields constrain rates but do not prove a trade opportunity.
- Premium index fields help explain funding calculation context but are not executable prices.
- Mark price attached to a funding record is a mark/reference price, not a fillable orderbook price.

All of these values are context. None are executable prices, direct trade instructions, active-promotion evidence, alert triggers, or Council auto-call triggers.

## Funding Interval Policy

Funding interval must not be hard-coded to 8 hours across venues or symbols.

Future implementations should prefer:

1. Explicit venue fields, such as Binance `fundingIntervalHours` or Bybit `fundingInterval`.
2. Differences between OKX `fundingTime` and `nextFundingTime` when current funding context is used.
3. Differences between adjacent historical funding timestamps when explicit interval fields are absent.
4. A warning when interval cannot be determined confidently.

Unknown interval should remain `optional_missing_fields` or a warning unless a future approved source contract makes it required.

## Context vs Signal Guardrail

Funding Rate is not a standalone signal.

- Funding Rate is not `WATCH`.
- Funding Rate is not `ENTER`.
- High absolute funding is not `ENTER`.
- Positive funding is not permission to short.
- Negative funding is not permission to long.
- Funding cap/floor pressure is not active-promotion evidence.
- Funding context presence is not Council auto-call permission.
- Funding context must not trigger alerts or execution.

## Readiness Boundary

This PR does not change readiness. Future default policy should also keep funding context out of readiness unless a separate policy-planning PR receives explicit approval.

Funding context must not change:

- `NEED_DATA`, `REJECT`, or `WATCH` semantics.
- `recommended_default_decision`.
- Estimated net spread/gap/basis.
- Persistence status.
- Council recommendation.
- Active strategy status.

## Packet / Candidate Context Placement

In a future implementation, normalized funding context may be attached to:

- `packet.extensions.funding_rate_context`
- `candidate.extensions.funding_rate_context`
- future sampling-summary diagnostics fields
- future dashboard watch/context fields

This PR does not implement any extension field, packet builder, candidate builder, parser, adapter, or sampling collector.

## Sampling / Evidence Planning

Future sampling summary fields may include:

- `funding_context_seen_count`
- `funding_context_missing_count`
- `funding_required_missing_count`
- `funding_optional_missing_count`
- `positive_funding_count`
- `negative_funding_count`
- `zero_funding_count`
- `high_abs_funding_count`
- `funding_cap_floor_context_seen_count`
- `funding_interval_known_count`
- `funding_interval_unknown_count`
- `funding_timestamp_warning_count`
- `funding_clock_skew_warning_count`
- `funding_predicted_seen_count`
- `funding_realized_seen_count`

These metrics are diagnostics only. They must not imply no-edge failure, possible-edge proof, `WATCH`, `ENTER`, Council auto-call, alert, execution, or active promotion.

## Dashboard / Council Semantics

Future dashboard row/status candidates may include:

- `FUNDING_CONTEXT_PLANNED`
- `PUBLIC_SOURCE_CANDIDATE_IDENTIFIED`
- `SOURCE_CONTRACT_PLANNED`
- `FIXTURE_PLAN_READY`
- `CONTEXT_ONLY`
- `READINESS_UNCHANGED`
- `NO_TRADE_ONLY`

Dashboard semantics:

- Dashboard is not a trading signal.
- Council Handoff Status is not execution permission.
- Funding context presence is not active-promotion evidence.
- High absolute funding may be watch context, but it is not an `ENTER` trigger.
- Dashboard rows must not trigger alerts, Council auto-call, orders, transfers, or strategy promotion.

## Fixture Plan

Next fixture planning or fixture contract PR should consider mocked payloads for:

- Binance USDⓈ-M funding history normal.
- Binance funding info cap/floor/interval normal.
- Bybit linear funding history normal.
- Bybit inverse funding history normal.
- OKX current funding normal.
- OKX funding history normal.
- Missing optional fields case.
- Missing required fields case.
- String numeric parsing case.
- Negative funding rate case.
- Positive funding rate case.
- Zero funding rate case.
- Abnormal / high absolute funding context case.
- Timestamp / data_age / clock-skew watch case.
- Varying funding interval case.
- Predicted vs realized funding separation case.
- Cap/floor present without funding history case.
- Product mismatch case, such as Bybit `linear` vs `inverse` or OKX non-`SWAP` instrument.

No fixture files are created by this PR.

## Implementation Sequence

Safe future implementation order:

1. Public source research finalization.
2. Mocked fixture contract.
3. Pure parser helper.
4. Venue-specific parser wrappers.
5. Normalized funding observation model.
6. Packet/candidate context extension planning.
7. Sampling summary support planning.
8. Dashboard status planning.
9. Optional read-only source adapter planning after source and parser contracts are reviewed.

Each implementation step should be a separate scoped PR with no-trade compliance, generated artifact policy, and deterministic tests.

## Open Questions

Open questions intentionally left unresolved:

- Should current predicted funding or historical settled funding be prioritized first?
- Which field should be canonical for `funding_interval_hours` when multiple sources exist?
- Should OKX `realizedRate` and `settFundingRate` map to separate normalized fields or one realized/settled field with `source_semantics`?
- Should Binance `fundingInfo` be a required source or optional cap/floor/interval context?
- Should Bybit `instruments-info` be required to normalize funding interval, or optional until interval-aware sampling exists?
- What threshold, if any, should label `high_abs_funding_count` as watch context without changing readiness?
- How should stale funding history be summarized when a venue returns no recent record?
- How should symbol normalization handle venue-specific perpetual naming differences?
