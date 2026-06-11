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

## Public Source Finalization

This section finalizes official public source candidates for `funding_rate_context_v0` from a research perspective. It does not authorize endpoint calls and does not implement adapters, parsers, packet builders, readiness, or sampling collectors.

| venue | source name | endpoint candidate | source classification | reason | expected fields | missing / uncertain fields | pagination note | rate-limit note | timestamp semantics | funding interval semantics | predicted vs realized semantics | cap/floor semantics | mark/premium reference semantics | public-read-only status | private API required? | implementation status | fixture priority | parser priority | guardrail note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Binance USDⓈ-M Futures | Funding Rate History | `GET /fapi/v1/fundingRate` | `required_primary` | It is the narrowest Binance source for historical funding context and includes the minimum fields needed for a basic funding fixture. | `symbol`, `fundingRate`, `fundingTime`, `markPrice` | Funding interval is not explicit in this endpoint. | `startTime` and `endTime` are inclusive; `limit` defaults to 100 and maxes at 1000; if range exceeds limit, response advances from `startTime` by `limit`; no time params returns recent records. | Shares 500/5min/IP limit with `GET /fapi/v1/fundingInfo`. | `fundingTime` is the funding event timestamp in ms. | Must infer from adjacent records or optional `fundingInfo`; do not hard-code 8h. | Treat historical `fundingRate` as funding-fee charge record context for that `fundingTime`. | None from this endpoint. | `markPrice` is funding-record attached mark reference, not executable price. | Public market data. | No. | Docs-only finalized source candidate; no call/implementation. | Required. | High. | Context only; no `WATCH`, `ENTER`, alert, or execution. |
| Binance USDⓈ-M Futures | Funding Info | `GET /fapi/v1/fundingInfo` | `optional_context` | It provides adjusted cap/floor/interval context only for symbols with funding cap/floor/interval adjustment and should not block minimum history fixtures. | `symbol`, `adjustedFundingRateCap`, `adjustedFundingRateFloor`, `fundingIntervalHours`, `disclaimer` | It may not return every symbol; no funding event timestamp. | No request parameters documented. | Request weight 0; shares 500/5min/IP limit with funding history. | No funding event timestamp; use only as auxiliary metadata. | `fundingIntervalHours` is source-provided context, not a hard-code replacement. | Not a funding event source. | Cap/floor are adjusted context fields. | No mark/premium event reference. | Public market data. | No. | Docs-only optional context; no call/implementation. | Optional. | Medium. | Cap/floor/interval context is not active-promotion evidence. |
| Bybit V5 | Funding Rate History | `GET /v5/market/funding/history` | `required_primary` | It is the minimum Bybit source for historical funding context and covers linear/inverse perpetual products. | `category`, `symbol`, `fundingRate`, `fundingRateTimestamp` | Funding interval not included; category/product semantics must be preserved. | `limit` range 1-200, default 200; passing only `startTime` returns an error; only `endTime` returns up to 200 records up to `endTime`; neither returns 200 up to current time. | Use Bybit market-data public rate-limit policy in future research; no private API required. | `fundingRateTimestamp` is the funding record timestamp in ms. | Each symbol can have a different funding interval; query instruments-info for interval. | Treat `fundingRate` as settled historical funding context unless future docs/source review says otherwise; preserve warning if ambiguity exists. | None from this endpoint. | No mark/premium reference. | Public market data. | No. | Docs-only finalized source candidate; no call/implementation. | Required, linear first; inverse optional context fixture. | High. | Category must not be collapsed; context only. |
| Bybit V5 | Instruments Info | `GET /v5/market/instruments-info` | `optional_context` | It is the best official source candidate for `fundingInterval`, upper/lower funding bounds, and product metadata, but minimum history parsing can proceed without it. | `category`, `symbol`, `contractType`, `fundingInterval`, `upperFundingRate`, `lowerFundingRate`, `settleCoin`, `nextPageCursor` | It is instrument metadata, not a funding event. | Default returns 500 entries; linear symbols can exceed 500, so cursor/limit may be needed; `limit` range 1-1000; use `nextPageCursor`. | Use Bybit public market-data rate-limit policy in future research; no private API required. | Response `time` is payload metadata, not funding event time. | `fundingInterval` is documented in minutes in examples/planning and should convert to hours in normalized context. | Not a funding event source. | `upperFundingRate` / `lowerFundingRate` are optional cap/floor context. | No mark/premium event reference. | Public market data. | No. | Docs-only optional context; no call/implementation. | Optional. | Medium. | Interval/cap/floor context must not change readiness. |
| OKX | Current Funding Rate | `GET /api/v5/public/funding-rate` | `optional_context` | It is valuable for current/predicted funding, next funding time, interval delta, cap/floor, settlement state, and premium context, but v0 minimum history fixture can start from history first. | `instType`, `instId`, `fundingRate`, `nextFundingRate`, `fundingTime`, `nextFundingTime`, `minFundingRate`, `maxFundingRate`, `interestRate`, `impactValue`, `settState`, `settFundingRate`, `premium`, `ts`, `method`, `formulaType` | Field availability can vary by instrument/formula version; source semantics need confirmation before parser implementation. | Current endpoint is point-in-time; no history pagination. | Official docs list public-data rate limit; exact production assumptions should be finalized before implementation. | `fundingTime`, `nextFundingTime`, and `ts` have distinct meanings. | Use `fundingTime` / `nextFundingTime` delta; do not assume 8h. | `fundingRate` is current/predicted context; `settFundingRate` is settlement context and must remain separate. | `minFundingRate` / `maxFundingRate` are optional cap/floor context. | `premium` is formula context, not executable price. | Public market data. | No. | Docs-only optional context; no call/implementation. | Optional. | Medium. | Current/predicted funding is not a standalone trigger. |
| OKX | Funding Rate History | `GET /api/v5/public/funding-rate-history` | `required_primary` | It is the narrowest OKX historical funding source for minimum v0 fixture coverage. | `instType`, `instId`, `formulaType`, `fundingRate`, `realizedRate`, `fundingTime`, `method` | History window and formula semantics must be preserved in source notes. | Uses `before`, `after`, and `limit`; official docs indicate timestamp-style pagination by `fundingTime`; history access window should be captured as docs-derived limit. | Official docs list public-data rate limit; exact production assumptions should be finalized before implementation. | `fundingTime` is the historical funding event timestamp. | Derive from adjacent history timestamps or pair with optional current endpoint; do not hard-code 8h. | `realizedRate` and `fundingRate` must remain separate until parser semantics are finalized. | None from base history endpoint. | No premium/mark reference in minimum history fields. | Public market data. | No. | Docs-only finalized source candidate; no call/implementation. | Required. | High. | Historical funding context is not entry/exit instruction. |

## Source Classification Decision

| classification | sources | final decision |
| --- | --- | --- |
| `required_primary` | Binance `GET /fapi/v1/fundingRate`; Bybit `GET /v5/market/funding/history`; OKX `GET /api/v5/public/funding-rate-history` | These are the minimum venue-level history sources for the next fixture contract. They provide the funding value, instrument identity, timestamp, and source endpoint needed for narrow v0 parser fixtures. |
| `optional_context` | Binance `GET /fapi/v1/fundingInfo`; Bybit `GET /v5/market/instruments-info`; OKX `GET /api/v5/public/funding-rate` | These provide interval, cap/floor, product metadata, current/predicted funding, next funding time, settlement state, or formula context. They should not block minimum fixtures. |
| `deferred_research` | Venue premium-index endpoints, mark-price endpoints, open-interest/long-short/liquidation endpoints, private account funding-fee history | These may be useful later but are outside v0 funding context source finalization. Private/account funding-fee history is especially out of scope. |
| `rejected_for_now` | Any private/account/order/position endpoint, execution/trade endpoints, alert/webhook sources, third-party/vendor aggregated funding APIs | They either require credentials/private scope, mix execution/account semantics, or expand trust and licensing surface beyond official public venue docs. |

## Minimum v0 Source Contract Decision

The v0 contract is intentionally narrow so the next PR can create deterministic fixtures without implementing a broad strategy surface.

| field name | v0 classification | meaning | source venue | source field mapping | parser note | required for minimum fixture? | can be missing? | context-only guardrail | unresolved question |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `venue` | `required_v0` | Exchange identifier. | All. | Derived from selected source. | Stable lowercase enum-like value. | Yes. | No. | Metadata only. | None. |
| `instrument_id` | `required_v0` | Venue-native instrument or symbol. | All. | Binance `symbol`; Bybit `symbol`; OKX `instId`. | Preserve raw venue ID. | Yes. | No. | Not tradability proof. | None. |
| `instrument_type` | `required_v0` | Product family/type. | All. | Binance endpoint family; Bybit `category`; OKX `instType`. | Preserve linear/inverse/swap distinctions. | Yes. | No. | Product type is not signal. | Exact Binance normalized value naming. |
| `symbol_normalized` | `required_v0` | Repository-normalized symbol for fixture comparability. | All. | Derived from venue ID. | In fixtures, provide deterministic normalized value. | Yes. | No for minimum fixtures; future parser may warn if mapping absent. | Normalization does not imply execution. | Future symbol map source. |
| `funding_rate` | `required_v0` | Primary funding value for the selected source record. | All required_primary sources. | Binance `fundingRate`; Bybit `fundingRate`; OKX history `fundingRate`. | String numeric parse candidate; preserve raw fixture string. | Yes. | No. | Funding rate is not entry signal. | Whether OKX history `fundingRate` should also populate predicted field. |
| `funding_rate_timestamp_ms` | `required_v0` | Funding event timestamp. | All required_primary sources. | Binance `fundingTime`; Bybit `fundingRateTimestamp`; OKX `fundingTime`. | Must parse ms timestamp. | Yes. | No. | Timing is diagnostics only. | None. |
| `source_endpoint` | `required_v0` | Endpoint path used by fixture/source. | All. | Endpoint candidate string. | Store path only. | Yes. | No. | Endpoint name is not permission to call live. | None. |
| `source_semantics` | `required_v0` | Declares historical/current/predicted/realized/cap-floor context. | All. | Derived from source classification. | Required to avoid predicted/realized confusion. | Yes. | No. | Semantics label prevents signal misuse. | OKX exact realized/current labels. |
| `parser_status` | `required_v0` | Future parser outcome. | Future parser. | Derived by parser. | Fixture expected outcome can be `ok` or `need_data`. | Yes. | No. | Parser status is not Council recommendation. | Exact enum names. |
| `required_missing_fields` | `required_v0` | Missing required field list. | Future parser. | Derived by parser. | Empty for normal required fixtures. | Yes. | No. | Missing fields do not trigger orders. | Exact field naming. |
| `optional_missing_fields` | `optional_v0` | Missing optional field list. | Future parser. | Derived by parser. | Useful for interval/cap/floor absence. | No. | Yes. | Optional absence is not failure. | None. |
| `warnings` | `optional_v0` | Non-fatal source/parser warnings. | Future parser. | Derived by parser. | Include stale/ambiguous semantics/numeric issues. | No. | Yes. | Warnings are review context only. | Warning taxonomy. |
| `funding_interval_hours` | `optional_v0` | Funding interval in hours when source-supported or derivable. | Binance info; Bybit instruments; OKX current/history deltas. | `fundingIntervalHours`; Bybit minutes converted; OKX time delta. | Do not hard-code 8h. | No. | Yes. | Interval must not change readiness. | Whether to make interval required in later versions. |
| `next_funding_time_ms` | `venue_specific_optional` | Next funding timestamp for current context. | OKX current primarily. | OKX `nextFundingTime`. | Separate from funding timestamp. | No. | Yes. | Countdown is not trade instruction. | Other venue current endpoints. |
| `realized_funding_rate` | `venue_specific_optional` | Realized/settled funding value. | OKX history/current; possibly history semantics for Binance/Bybit after review. | OKX `realizedRate` / `settFundingRate`. | Keep separate from `funding_rate`. | No. | Yes. | Realized rate is context/evidence only. | OKX naming split. |
| `predicted_funding_rate` | `venue_specific_optional` | Current/predicted funding value. | OKX current. | OKX `fundingRate` / `nextFundingRate`. | Do not mix with settled history. | No. | Yes. | Prediction is not executable. | Whether to include in v0 fixtures. |
| `funding_cap` | `venue_specific_optional` | Upper cap/limit. | Binance info; Bybit instruments; OKX current. | `adjustedFundingRateCap`; `upperFundingRate`; `maxFundingRate`. | Optional context. | No. | Yes. | Cap is not promotion evidence. | OKX field availability. |
| `funding_floor` | `venue_specific_optional` | Lower floor/limit. | Binance info; Bybit instruments; OKX current. | `adjustedFundingRateFloor`; `lowerFundingRate`; `minFundingRate`. | Optional context. | No. | Yes. | Floor is not promotion evidence. | OKX field availability. |
| `mark_price_reference` | `venue_specific_optional` | Funding-record mark reference. | Binance history. | Binance `markPrice`. | Reference only. | No. | Yes. | Not executable price. | Whether other venues expose equivalent. |
| `premium_index_reference` | `venue_specific_optional` | Premium/formula context. | OKX current. | OKX `premium`. | Context only. | No. | Yes. | Premium is not order signal. | Whether premium-index endpoints are deferred. |
| `source_payload_timestamp_ms` | `optional_v0` | Source response timestamp if present. | Bybit response `time`; OKX `ts`; others if present. | Source-level timestamp. | Distinguish payload time from funding event time. | No. | Yes. | Freshness diagnostics only. | Exact source priority. |
| `local_observed_at_ms` | `deferred` | Local collection timestamp. | Future adapter. | Local metadata. | Requires adapter implementation, not fixture finalization. | No. | Yes. | Local time is not signal. | Adapter clock policy. |
| `data_age_ms` | `deferred` | Derived freshness age. | Future adapter/parser. | Derived from source/local timestamps. | Needs local observed time. | No. | Yes. | Data age is diagnostics only. | Negative age policy. |
| `clock_skew_warning` | `deferred` | Clock skew warning. | Future adapter/parser. | Derived. | Needs local/source comparison policy. | No. | Yes. | Warning is not signal. | Threshold. |

Minimum v0 fixture contract: `venue`, `instrument_id`, `instrument_type`, `symbol_normalized`, `funding_rate`, `funding_rate_timestamp_ms`, `source_endpoint`, `source_semantics`, `parser_status`, and `required_missing_fields` are required. Interval, cap/floor, premium, mark price, next funding time, predicted funding, realized funding, payload timestamp, optional missing fields, and warnings remain optional or venue-specific optional for v0.

## Predicted vs Realized Funding Policy

- In v0, normalized `funding_rate` means the primary funding value emitted by the selected source record. It must always be paired with `source_semantics`.
- Predicted/current funding and realized/settled funding stay in separate optional fields when the source exposes both.
- If a venue history endpoint's `fundingRate` semantics are not explicit enough to label realized vs predicted, parser fixtures should set `source_semantics=historical_funding_rate` and add a warning rather than silently coercing it.
- OKX current endpoint: `fundingRate` / `nextFundingRate` are predicted/current context candidates, while `settFundingRate` is settlement context; keep them separate.
- OKX history endpoint: `realizedRate` and `fundingRate` must not be collapsed until a parser policy finalizes naming.
- Bybit funding history `fundingRate` is treated as settled historical context for v0 fixture planning because the docs describe returned records as settled historical funding rates; keep a warning hook for venue ambiguity.
- Binance funding history `fundingRate` is treated as funding-fee charge record context at `fundingTime`; `markPrice` remains attached reference context only.

## Funding Interval Finalization Policy

- Do not hard-code 8 hours across all venues/symbols.
- Binance `fundingInfo.fundingIntervalHours` is `optional_context`, not a required source.
- Bybit `instruments-info.fundingInterval` is `optional_context` and should be converted from minutes to hours when used.
- OKX current `fundingTime` / `nextFundingTime` delta can be used as optional interval context.
- Missing interval should not make v0 normal fixture parsing fail. It should appear in `optional_missing_fields` or `warnings`.
- v0 minimum fixtures do not require `funding_interval_hours`.
- A later interval-aware sampling PR may revisit whether interval becomes required for a narrower use case.

## Pagination / Rate-Limit Research Notes

| source | pagination / range note | rate-limit note | implementation decision |
| --- | --- | --- | --- |
| Binance `GET /fapi/v1/fundingRate` | `startTime`/`endTime` inclusive; `limit` default 100, max 1000; no time params returns recent records; responses are ascending; if range exceeds limit, continue from `startTime + limit` behavior. | Shared 500/5min/IP with `GET /fapi/v1/fundingInfo`. | Required fixture source; future collector must page deterministically. |
| Binance `GET /fapi/v1/fundingInfo` | No request parameters documented in official page. | Request weight 0; shared 500/5min/IP with funding history. | Optional interval/cap/floor context. |
| Bybit `GET /v5/market/funding/history` | `limit` 1-200, default 200; only `startTime` returns error; only `endTime` returns 200 records up to `endTime`; neither returns 200 records up to current time. | Use public market-data rate-limit policy in implementation research; no private key required. | Required fixture source. |
| Bybit `GET /v5/market/instruments-info` | Default 500 entries; `limit` 1-1000; linear symbols can exceed 500 and require `cursor`/`nextPageCursor`. | Use public market-data rate-limit policy in implementation research; no private key required. | Optional interval/cap/floor context. |
| OKX `GET /api/v5/public/funding-rate` | Current point-in-time endpoint; no historical pagination. | Official docs list public-data rate limit; verify exact number in implementation research. | Optional current/predicted context. |
| OKX `GET /api/v5/public/funding-rate-history` | Uses `before`, `after`, and `limit`; pagination should be based on `fundingTime`; history window limitations must be preserved from official docs. | Official docs list public-data rate limit; verify exact number in implementation research. | Required fixture source. |

## Fixture Contract Recommendation

| fixture candidate | fixture class | purpose | required source | expected parser outcome | required_missing_fields expectation | optional_missing_fields expectation | warnings expectation | context-only guardrail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `binance_usdm_funding_rate_history_normal.json` | required | Validate Binance required history fields and mark reference preservation. | Binance `GET /fapi/v1/fundingRate`. | `ok`. | Empty. | May include interval/cap/floor as missing optional. | None. | `markPrice` is not executable. |
| `bybit_linear_funding_history_normal.json` | required | Validate Bybit linear category, funding value, and funding timestamp. | Bybit `GET /v5/market/funding/history`. | `ok`. | Empty. | Interval optional missing unless instruments fixture joined. | None or category note. | Linear category is context, not signal. |
| `okx_funding_rate_history_normal.json` | required | Validate OKX history funding fields and realized/funding separation. | OKX `GET /api/v5/public/funding-rate-history`. | `ok`. | Empty. | Current/next funding optional missing. | May warn if realized/funding naming remains ambiguous. | History is context only. |
| `binance_usdm_funding_info_interval_cap_floor.json` | optional | Validate Binance interval/cap/floor context. | Binance `GET /fapi/v1/fundingInfo`. | `ok`. | Empty if used as optional context fixture. | Funding event timestamp optional missing. | Note adjusted-info-only semantics. | Cap/floor not promotion evidence. |
| `bybit_linear_instruments_info_funding_interval.json` | optional | Validate Bybit `fundingInterval` minutes and cap/floor metadata. | Bybit `GET /v5/market/instruments-info`. | `ok`. | Empty if used as optional context fixture. | Funding event timestamp optional missing. | Cursor/pagination note if list includes cursor. | Interval does not change readiness. |
| `bybit_inverse_funding_history_normal.json` | optional | Validate inverse category preservation. | Bybit `GET /v5/market/funding/history`. | `ok`. | Empty. | Interval optional missing. | Category/product semantics note. | Inverse context is not signal. |
| `okx_current_funding_rate_normal.json` | optional | Validate predicted/current funding, next funding time, settlement, premium. | OKX `GET /api/v5/public/funding-rate`. | `ok`. | Empty if current source contract selected. | History fields optional missing. | Predicted/current warning as needed. | Current funding not trigger. |
| `missing_required_funding_rate.json` | edge | Validate required missing funding rate behavior. | Any required_primary source. | `need_data` or `invalid_payload`. | Includes `funding_rate`. | Optional fields may also be missing. | Missing required field warning. | Missing data does not trigger trade. |
| `missing_optional_interval.json` | edge | Validate missing interval remains optional. | Required history source without interval. | `ok`. | Empty. | Includes `funding_interval_hours`. | Optional interval warning allowed. | Interval absence does not change readiness. |
| `string_numeric_parsing.json` | edge | Validate numeric strings parse safely. | Any venue. | `ok` if parseable. | Empty. | None expected. | Numeric parsing warning only on malformed values. | Parsed value not signal. |
| `positive_funding_rate.json` | edge | Validate positive funding context. | Any required_primary source. | `ok`. | Empty. | Venue optional fields as applicable. | None. | Positive funding is not short permission. |
| `negative_funding_rate.json` | edge | Validate negative funding context. | Any required_primary source. | `ok`. | Empty. | Venue optional fields as applicable. | None. | Negative funding is not long permission. |
| `zero_funding_rate.json` | edge | Validate zero funding context. | Any required_primary source. | `ok`. | Empty. | Venue optional fields as applicable. | None. | Zero funding is not no-edge proof. |
| `high_absolute_funding_context.json` | edge | Validate high absolute funding warning context. | Any venue. | `ok`. | Empty. | Venue optional fields as applicable. | High absolute funding warning. | High absolute funding is not `ENTER`. |
| `timestamp_data_age_clock_skew_watch.json` | edge | Validate timestamp/data_age/clock-skew watch planning. | Any venue with source/local timestamp metadata. | `ok` or warning status. | Empty if required fields present. | Local/age fields may be optional. | Clock-skew/data-age warning. | Timestamp warning is diagnostics only. |
| `varying_funding_interval.json` | edge | Validate non-8h interval handling. | Binance info, Bybit instruments, or OKX current delta. | `ok`. | Empty if interval source included. | None expected. | Varying interval warning/context. | Interval variation not signal. |
| `okx_predicted_vs_realized_semantics.json` | edge | Validate OKX current/history semantic separation. | OKX current + history fixture pair or synthetic combined payload. | `ok` if fields separated. | Empty. | Venue-specific missing fields allowed. | Warning if labels ambiguous. | Predicted/realized separation prevents signal misuse. |

## Research Finalization Open Questions

- Exact OKX public-data rate-limit numbers and history window wording should be confirmed during implementation planning without live calls.
- Exact `source_semantics` enum names remain open until the fixture contract PR.
- Whether `symbol_normalized` should be required in parser output or only required in fixtures remains open for implementation.
- Whether Bybit `instruments-info` should be joined during parser tests or kept as separate optional-context parser remains open.
- Whether Binance `fundingInfo` should be sampled periodically or only used in fixture/source-contract tests remains open.
- Whether OKX current funding should be introduced in the first parser PR or delayed until after history parser stability remains open.
