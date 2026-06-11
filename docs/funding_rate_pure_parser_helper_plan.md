# Funding Rate Pure Parser Helper Plan

## Purpose

This document freezes the planning contract for a future Funding Rate pure parser helper before any parser implementation exists. The goal is to define the input/output boundary, `parser_status` naming, `source_semantics` mapping, missing-field handling, warning policy, and draft normalized output shape using the existing required, optional, and edge Funding Rate fixtures.

This is a docs-only planning step for `funding_rate_context_v0`. Funding Rate remains context, diagnostics, and regime information only. Parser success is not readiness success, not Council execution permission, and not a trading signal.

## Non-Goals

This PR does not implement or modify any of the following:

- Funding Rate parser code.
- Funding Rate venue adapter code.
- Packet builder or candidate mutation.
- Readiness logic or readiness thresholds.
- Sampling collector logic.
- Endpoint calls, live response collection, or copied live payloads.
- Fixture JSON files.
- Tests or executable runtime behavior.
- Active strategy, registry, config, dashboard, alert, or Council automation behavior.

## Parser Design Principles

- Pure function first: future helpers should accept already-provided raw payload objects and return deterministic normalized observations plus parse metadata.
- No network calls: helpers must not call Funding Rate endpoints or any other endpoint.
- No private API: helpers must not require credentials, account state, positions, balances, transfers, or order data.
- Deterministic fixture-driven parsing: behavior should be specified and tested with mocked fixture payloads before live adapters are considered.
- Venue-specific wrappers are later-stage work: this document describes helper contracts; wrapper orchestration belongs in a future PR.
- Normalized output is context-only: it may inform future diagnostics but must not create executable intent.
- Parser success is not a trading signal: `OK` only means the helper understood the payload contract.
- Warnings are not trade permission: warning names are audit/context labels, not `WATCH`, `ENTER`, or alert instructions.
- No readiness change: parser status and warnings must not alter active readiness decisions in this planning step.

## Proposed Helper Boundary

### In Scope for the Pure Helper

- Raw payload shape validation.
- Venue/source-specific field extraction planning.
- String numeric parsing policy planning.
- Timestamp parsing policy planning.
- Population of `required_missing_fields`, `optional_missing_fields`, and `warnings`.
- `source_semantics` tagging so downstream consumers know whether a value is historical, realized, predicted, or context-only.
- Draft normalized funding observation creation for future parser tests.

### Out of Scope for the Pure Helper

- HTTP requests.
- Credential handling.
- Account data, balances, positions, transfers, deposits, or withdrawals.
- Order placement, cancellation, execution, routing, or execution eligibility.
- Readiness decisions or readiness threshold changes.
- Council recommendation generation or Council auto-call behavior.
- Packet builder mutation.
- Sampling collection.
- Dashboard generation.

## Proposed Normalized Funding Observation Shape

The following table is a planning-only shape. It is not a code schema and should not be treated as implementation. Field presence labels are `required_v0`, `optional_v0`, `venue_specific_optional`, or `deferred`.

| Field | Presence | Expected type | Parse source | Missing behavior | Warning behavior | Context-only note |
| --- | --- | --- | --- | --- | --- | --- |
| `venue` | required_v0 | string enum-like label | Explicit parser input or source wrapper metadata such as `binance_usdm`, `bybit`, `okx` | Missing venue should produce `UNSUPPORTED_VENUE` or `NEED_SOURCE_FIELDS` depending on call boundary. | Add warning only if caller supplied ambiguous venue metadata. | Venue identifies source only; it is not venue preference or execution venue selection. |
| `source_endpoint` | required_v0 | string enum-like label | Explicit parser input such as `binance_usdm_funding_rate_history`, `bybit_v5_funding_history`, `okx_funding_rate_history` | Missing/unknown source should produce `UNSUPPORTED_SOURCE`. | Unsupported source may include a diagnostic warning. | Endpoint label is provenance, not an instruction to call the endpoint. |
| `source_semantics` | required_v0 | string enum-like label | Derived from venue and source endpoint; examples appear in the Source Semantics Mapping section. | Missing derivation should produce `UNSUPPORTED_SOURCE` or `INVALID_SOURCE_SHAPE`. | Warn when semantics are intentionally mixed, such as OKX predicted versus realized examples. | Semantics determine interpretation; they never promote a signal. |
| `instrument_id` | required_v0 | string | Binance `symbol`, Bybit `result.list[].symbol`, OKX `data[].instId` | Missing should populate `required_missing_fields` and produce `NEED_SOURCE_FIELDS`. | No warning unless partial batch behavior is later approved. | Instrument identifier is observation identity, not an order instrument. |
| `instrument_type` | optional_v0 | string | Bybit `result.category`, OKX `instType`, inferred only where safe for Binance USD-M futures context | Missing should populate `optional_missing_fields` only. | Warn if venue source implies multiple categories and no category is present. | Used for diagnostics and to avoid collapsing linear/inverse contexts. |
| `symbol_normalized` | deferred | string | Future symbol normalization helper, not this parser plan | Missing should not fail v0 parser. | Warn only if a future normalization step fails. | Normalization is display/routing context only, not execution permission. |
| `funding_rate` | required_v0 for history/current rate records; optional_v0 for interval-only sources | decimal-compatible numeric value or decimal string after parse decision | Binance `fundingRate`, Bybit `fundingRate`, OKX `fundingRate` when source semantics match | Missing from required records should populate `required_missing_fields` and produce `NEED_SOURCE_FIELDS`; missing from interval-only sources should be allowed. | Invalid strings should produce `INVALID_NUMERIC_FIELD`; high absolute value may add context warning only. | Positive, negative, zero, or high absolute funding is not long/short/ENTER permission. |
| `funding_rate_timestamp_ms` | required_v0 for funding observations; optional_v0 for interval/cap/floor-only context | integer milliseconds | Binance `fundingTime`, Bybit `fundingRateTimestamp`, OKX `fundingTime` | Missing from funding observations should populate `required_missing_fields`; interval-only context can omit. | Invalid timestamp strings should produce `INVALID_TIMESTAMP_FIELD`; age/skew warnings are deferred. | Timestamp freshness is context only and does not change readiness. |
| `parser_status` | required_v0 | string enum-like label | Derived by helper from validation outcome | Must always be set. | `OK_WITH_WARNINGS` requires non-empty `warnings`; failure statuses may or may not include warnings. | Parser status is parser health only, not trade status. |
| `required_missing_fields` | required_v0 | list of strings | Helper-populated diagnostics | Empty list when no required field is missing. | Missing required fields generally do not require warnings because the list is explicit. | Missing data is not a trading signal. |
| `optional_missing_fields` | required_v0 | list of strings | Helper-populated diagnostics | Empty list when no optional field is missing. | Optional missing fields may add context warnings but should not fail the parser. | Optional absence cannot grant or deny trade permission. |
| `warnings` | required_v0 | list of strings | Helper-populated diagnostics | Empty list when no warning exists. | Warnings are stable string labels such as `optional_interval_missing` or `high_abs_funding_context`. | Warnings are review context, never alerts or Council instructions. |
| `funding_interval_hours` | optional_v0 | decimal-compatible numeric value | Binance funding info `fundingIntervalHours`, Bybit instruments info `fundingInterval` minutes divided by 60, OKX derived from `fundingTime` to `nextFundingTime` only if future policy approves | Missing should populate `optional_missing_fields`. | Warn on missing optional interval or varying interval assumptions. | Do not hard-code 8h; interval variation is context only. |
| `next_funding_time_ms` | optional_v0 | integer milliseconds | OKX current funding `nextFundingTime`; future sources where present | Missing is optional unless source-specific policy later requires it. | Invalid timestamp should produce timestamp warning or `INVALID_TIMESTAMP_FIELD` if parsed field is present but malformed. | Next time is schedule context, not a trigger. |
| `realized_funding_rate` | venue_specific_optional | decimal-compatible numeric value | OKX history `realizedRate`; OKX current `settFundingRate` remains separate unless future policy maps it here | Missing should not fail non-OKX or predicted-only records. | Warn if source contains realized and predicted values that risk being collapsed. | Realized funding is historical context, not promotion evidence. |
| `predicted_funding_rate` | venue_specific_optional | decimal-compatible numeric value | OKX current `nextFundingRate`; current `fundingRate` remains source-semantics-dependent | Missing should not fail historical records. | Warn that predicted/current values are not ENTER triggers. | Predicted/current funding is diagnostics only. |
| `funding_cap` | venue_specific_optional | decimal-compatible numeric value | Binance `adjustedFundingRateCap`, Bybit `upperFundingRate`, OKX `maxFundingRate` | Missing should populate optional fields only when that source is interval/cap/floor context. | Invalid cap string should use numeric error policy. | Cap is risk/regime context, not trade permission. |
| `funding_floor` | venue_specific_optional | decimal-compatible numeric value | Binance `adjustedFundingRateFloor`, Bybit `lowerFundingRate`, OKX `minFundingRate` | Missing should populate optional fields only when that source is interval/cap/floor context. | Invalid floor string should use numeric error policy. | Floor is risk/regime context, not trade permission. |
| `mark_price_reference` | venue_specific_optional | decimal-compatible numeric value | Binance history `markPrice` | Missing should not fail if source treats it as optional reference. | Invalid mark price string should follow numeric error policy if present. | Mark price is a reference only, not executable price. |
| `premium_index_reference` | venue_specific_optional | decimal-compatible numeric value or string policy TBD | OKX `premium` | Missing should not fail. | Invalid premium should follow numeric error policy if present. | Premium is formula context, not a signal. |

## Parser Status Naming Plan

| `parser_status` | Meaning | When it occurs | Relationship to `required_missing_fields` | Relationship to `warnings` | Future parser test fixture | Readiness effect |
| --- | --- | --- | --- | --- | --- | --- |
| `OK` | Payload shape and required fields are parseable without warnings. | Normal required fixtures and benign optional context records. | Must be empty for records where required fields apply. | Usually empty; optional missing fields may remain warning-free only if policy chooses no warning. | `binance_usdm_funding_rate_history_normal.json`, `bybit_linear_funding_history_normal.json`, `okx_funding_rate_history_normal.json` | none / readiness unchanged |
| `OK_WITH_WARNINGS` | Required fields are parseable but context diagnostics are present. | High absolute funding context, timestamp watch context, semantic non-collapse warnings. | Must be empty for the parsed record unless partial-batch policy later allows mixed records. | Must be non-empty. | `high_absolute_funding_context.json`, `timestamp_data_age_clock_skew_watch.json`, `okx_predicted_vs_realized_semantics.json` | none / readiness unchanged |
| `NEED_SOURCE_FIELDS` | Required fields needed to produce a funding observation are missing. | Required `funding_rate`, timestamp, instrument, venue, or source metadata is absent. | Must be non-empty and list the normalized field names. | May be empty because missing required fields are explicit. | `missing_required_funding_rate.json` | none / readiness unchanged |
| `INVALID_SOURCE_SHAPE` | The top-level payload shape does not match the expected source wrapper. | Binance history is not a list, Bybit lacks `result.list`, or OKX lacks `data` array/object shape. | May be empty if failure is structural before field extraction. | May include a diagnostic shape warning. | Future malformed wrapper fixture. | none / readiness unchanged |
| `INVALID_NUMERIC_FIELD` | A present numeric field cannot be parsed under the numeric policy. | Non-numeric string in `fundingRate`, `realizedRate`, `nextFundingRate`, cap/floor, mark price, or premium. | Usually empty unless the field is treated as unavailable after parse failure. | May include field-specific invalid numeric warning. | Future invalid numeric fixture derived from `string_numeric_parsing.json` policy. | none / readiness unchanged |
| `INVALID_TIMESTAMP_FIELD` | A present timestamp field cannot be parsed as integer milliseconds. | Non-integer, malformed, or unsupported timestamp format in `fundingTime`, `fundingRateTimestamp`, or `nextFundingTime`. | Usually empty unless the timestamp is required and effectively unavailable. | May include field-specific invalid timestamp warning. | Future invalid timestamp fixture derived from timestamp watch policy. | none / readiness unchanged |
| `UNSUPPORTED_SOURCE` | The source endpoint label is unknown or intentionally not supported by v0. | Caller passes a source outside the approved Funding Rate mocked fixture set. | May be empty because no record extraction is attempted. | May include unsupported source diagnostic. | Future unsupported source fixture. | none / readiness unchanged |
| `UNSUPPORTED_VENUE` | The venue label is unknown or intentionally not supported by v0. | Caller passes a venue outside Binance USD-M, Bybit, or OKX planning scope. | May be empty because no source extraction is attempted. | May include unsupported venue diagnostic. | Future unsupported venue fixture. | none / readiness unchanged |

## Source Semantics Mapping

| `source_semantics` | Represented source | Venue | Fixture examples | Predicted vs realized handling | Context-only guardrail |
| --- | --- | --- | --- | --- | --- |
| `historical_funding_charge_record` | Funding history record representing a charged historical funding event. | Binance USD-M | `binance_usdm_funding_rate_history_normal.json`, `positive_funding_rate.json`, `negative_funding_rate.json` | Treat Binance `fundingRate` as historical charge context with `fundingTime`; do not treat sign as directional advice. | Historical charge context is not entry, exit, WATCH, or ENTER. |
| `settled_historical_funding_context` | Settled historical funding context from a history endpoint. | Bybit linear/inverse | `bybit_linear_funding_history_normal.json`, `bybit_inverse_funding_history_normal.json`, `zero_funding_rate.json` | Preserve `result.category` so linear and inverse records do not collapse. | Settled context does not select long/short side or venue. |
| `historical_funding_context` | Historical funding-rate context that may contain separate nominal and realized values. | OKX | `okx_funding_rate_history_normal.json` | Keep OKX `fundingRate` and `realizedRate` separate; normalized `funding_rate` requires semantics. | Historical context does not alter readiness. |
| `interval_cap_floor_context` | Funding interval, cap, and floor context independent from history records. | Binance USD-M | `binance_usdm_funding_info_interval_cap_floor.json`, `missing_optional_interval.json` | No predicted/realized funding rate is implied. | Cap/floor/interval context is diagnostics only. |
| `instrument_interval_cap_floor_context` | Instrument metadata containing interval and cap/floor context. | Bybit | `bybit_linear_instruments_info_funding_interval.json`, `varying_funding_interval.json` | Convert minutes to candidate hours only after policy approval; no funding direction implied. | Instrument metadata cannot become a readiness gate in this PR. |
| `current_predicted_funding_context` | Current/predicted funding context from a current funding endpoint. | OKX | `okx_current_funding_rate_normal.json` | Keep `fundingRate`, `nextFundingRate`, and `settFundingRate` distinct. | Current predicted funding is not an ENTER trigger. |
| `predicted_vs_realized_semantics_context` | Explicit mixed fixture used to test non-collapse of current, next, settled, and realized rates. | OKX | `okx_predicted_vs_realized_semantics.json` | Must warn or document `do_not_collapse_predicted_and_realized`; no single field should erase provenance. | Semantics warning is context only and does not change readiness. |
| `timestamp_watch_context` | Timestamp freshness/skew observation context. | Bybit or future cross-venue context | `timestamp_data_age_clock_skew_watch.json` | No predicted/realized distinction; focus is timestamp parsing and future watch diagnostics. | Timestamp watch wording is human review context, not standalone WATCH. |
| `high_abs_funding_context` | High absolute funding magnitude context. | OKX or future cross-venue context | `high_absolute_funding_context.json` | Preserve source fields and add context warning rather than converting magnitude into a side signal. | High absolute funding may be human watch context but is not ENTER. |

## Venue Parser Planning

### Binance

- Funding history parser plan: accept the USD-M funding history array/list shape and iterate each record deterministically.
- Required funding observation fields: `symbol`, `fundingRate`, and `fundingTime`.
- Optional reference fields: `markPrice` and future symbol normalization context.
- Funding info optional context plan: accept the funding info array/list shape for `adjustedFundingRateCap`, `adjustedFundingRateFloor`, and `fundingIntervalHours`.
- `markPrice` is a reference only. It is not an executable price, fill price, fair value, or order-routing input.
- `fundingRate` is string numeric and should be parsed under the common numeric policy.
- `fundingTime` is a millisecond timestamp and should populate `funding_rate_timestamp_ms` when the record is a funding observation.

### Bybit

- V5 response object parser plan: validate `retCode`, `retMsg`, `result`, and `result.list` shape before extracting records.
- Preserve `result.category` in `instrument_type` or venue-specific metadata so `linear` and `inverse` records are not collapsed.
- Iterate `result.list` records deterministically.
- Do not collapse linear and inverse symbols or categories into one semantic bucket.
- Parse `fundingRateTimestamp` as a millisecond timestamp string.
- Instruments-info parser plan: use `fundingInterval` in minutes as a candidate for `funding_interval_hours = fundingInterval / 60`, while preserving cap/floor metadata (`upperFundingRate`, `lowerFundingRate`).

### OKX

- Response parser plan: validate the `code`, `msg`, and `data` object/array wrapper before extracting records.
- Funding-rate-history parser plan: parse `instId`, `instType`, `fundingRate`, `realizedRate`, and `fundingTime` without collapsing nominal and realized fields.
- Current funding-rate parser plan: parse `fundingRate`, `nextFundingRate`, `settFundingRate`, `nextFundingTime`, `premium`, `minFundingRate`, and `maxFundingRate` as separate context fields.
- Do not collapse OKX `fundingRate`, `realizedRate`, `nextFundingRate`, or `settFundingRate` into one unqualified signal value.
- Parse `fundingTime` and `nextFundingTime` as millisecond timestamp strings.
- `premium` is formula context only; it is not a premium-index trading signal or execution instruction.

## Missing Field Policy

- Required and optional fields must be tracked separately.
- If a `required_v0` field is missing, the preferred status candidate is `NEED_SOURCE_FIELDS`.
- Missing required fields should be listed in `required_missing_fields` using normalized field names such as `funding_rate` or `funding_rate_timestamp_ms`.
- If an `optional_v0` field is missing, the parser should not fail solely for that reason.
- Missing optional fields should be listed in `optional_missing_fields`.
- Warnings are context-only and should explain review-relevant conditions such as `optional_interval_missing`, `timestamp_watch_context`, or `high_abs_funding_context`.
- Missing fields are not trading signals, risk approvals, or readiness decisions.

## Numeric Parsing Policy

- Funding numeric fields are expected to arrive mostly as strings and should be parsed by a deterministic numeric policy.
- Candidate numeric fields include `fundingRate`, `realizedRate`, `nextFundingRate`, `settFundingRate`, cap/floor fields, `markPrice`, and `premium`.
- Decimal-compatible parsing should be considered before float-based parsing because fixtures preserve small rates and exact string values.
- Invalid numeric strings should produce `INVALID_NUMERIC_FIELD` when the field is required for the record; optional numeric fields may be candidates for field-level warnings if future partial parsing is approved.
- Numeric parse success is only parser health. It does not imply that a funding value is useful, safe, risky, directional, or actionable.
- Positive funding is not short permission.
- Negative funding is not long permission.
- Zero funding is not a no-risk or trade conclusion.
- High absolute funding may populate `warnings` such as `high_abs_funding_context`, but it is not a standalone WATCH or ENTER trigger.

## Timestamp Parsing Policy

- Primary timestamp format is integer milliseconds.
- String milliseconds should be accepted when the source uses string timestamps, as in Bybit and OKX fixtures.
- `funding_rate_timestamp_ms` is required for funding observation records.
- `next_funding_time_ms` is optional and applies to sources such as OKX current funding context.
- `local_observed_at_ms`, `data_age_ms`, and `clock_skew_warning` are deferred fields and should not be implemented by this helper planning PR.
- Negative `data_age` handling is outside this parser helper boundary.
- Clock-skew calculation is not implemented in this plan and must not be inferred from parser success.

## Predicted vs Realized Funding Policy

- Normalized `funding_rate` must be interpreted together with `source_semantics` and source endpoint provenance.
- OKX `fundingRate`, `realizedRate`, `nextFundingRate`, and `settFundingRate` must not be collapsed into a single executable meaning.
- Binance history `fundingRate` is historical funding charge record context.
- Bybit history `fundingRate` is settled historical context and must preserve category such as `linear` or `inverse`.
- Current predicted funding is not an ENTER trigger and must not become active promotion evidence.

## Fixture-to-Parser Test Matrix

This matrix plans future parser tests only. This PR does not add or modify tests.

| Fixture filename | Represented source | Expected `parser_status` | Expected `required_missing_fields` | Expected `optional_missing_fields` | Expected `warnings` | Expected normalized fields | Readiness effect |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `binance_usdm_funding_rate_history_normal.json` | Binance USD-M funding history | `OK` | `[]` | `[]` or mark price optional policy if absent in future records | `[]` | `venue`, `source_endpoint`, `historical_funding_charge_record`, `instrument_id`, `funding_rate`, `funding_rate_timestamp_ms`, `mark_price_reference` | none / readiness unchanged |
| `bybit_linear_funding_history_normal.json` | Bybit V5 linear funding history | `OK` | `[]` | `[]` | `[]` | `venue`, `source_endpoint`, `settled_historical_funding_context`, `instrument_id`, `instrument_type=linear`, `funding_rate`, `funding_rate_timestamp_ms` | none / readiness unchanged |
| `okx_funding_rate_history_normal.json` | OKX funding-rate-history | `OK` | `[]` | `[]` | `[]` | `venue`, `source_endpoint`, `historical_funding_context`, `instrument_id`, `instrument_type`, `funding_rate`, `realized_funding_rate`, `funding_rate_timestamp_ms` | none / readiness unchanged |
| `binance_usdm_funding_info_interval_cap_floor.json` | Binance funding info optional context | `OK` | `[]` | `[]` | `[]` | `venue`, `source_endpoint`, `interval_cap_floor_context`, `instrument_id`, `funding_interval_hours`, `funding_cap`, `funding_floor` | none / readiness unchanged |
| `bybit_linear_instruments_info_funding_interval.json` | Bybit instruments-info interval/cap/floor context | `OK` | `[]` | `[]` | `[]` | `venue`, `source_endpoint`, `instrument_interval_cap_floor_context`, `instrument_id`, `instrument_type=linear`, `funding_interval_hours`, `funding_cap`, `funding_floor` | none / readiness unchanged |
| `bybit_inverse_funding_history_normal.json` | Bybit V5 inverse funding history | `OK` | `[]` | `[]` | `[]` | Preserve `instrument_type=inverse`; do not collapse with linear. | none / readiness unchanged |
| `okx_current_funding_rate_normal.json` | OKX current funding-rate context | `OK` | `[]` | `[]` | `[]` | `current_predicted_funding_context`, `funding_rate`, `predicted_funding_rate`, `next_funding_time_ms`, `funding_cap`, `funding_floor`, `premium_index_reference` | none / readiness unchanged |
| `missing_required_funding_rate.json` | Binance history missing required rate | `NEED_SOURCE_FIELDS` | `["funding_rate"]` | `[]` | `[]` | No complete normalized observation unless partial-error record policy is approved. | none / readiness unchanged |
| `missing_optional_interval.json` | Binance funding info missing interval | `OK` or `OK_WITH_WARNINGS` depending warning policy | `[]` | `["funding_interval_hours"]` | `["optional_interval_missing"]` if warning policy keeps fixture label | Cap/floor context without interval. | none / readiness unchanged |
| `string_numeric_parsing.json` | Cross-source numeric-string parsing | `OK` | `[]` | Source-dependent | `["numeric_parse_success_is_not_signal"]` | Numeric fields parse as Decimal-compatible values while provenance is preserved. | none / readiness unchanged |
| `positive_funding_rate.json` | Positive Binance funding-rate context | `OK` | `[]` | `[]` | `[]` or `numeric_parse_success_is_not_signal` if policy adds sign context | Positive `funding_rate` preserved with historical charge semantics. | none / readiness unchanged |
| `negative_funding_rate.json` | Negative Binance funding-rate context | `OK` | `[]` | `[]` | `[]` or `numeric_parse_success_is_not_signal` if policy adds sign context | Negative `funding_rate` preserved with historical charge semantics. | none / readiness unchanged |
| `zero_funding_rate.json` | Zero Bybit funding-rate context | `OK` | `[]` | `[]` | `[]` or `numeric_parse_success_is_not_signal` if policy adds zero context | Zero `funding_rate` preserved with settled historical semantics. | none / readiness unchanged |
| `high_absolute_funding_context.json` | High absolute OKX funding context | `OK_WITH_WARNINGS` | `[]` | `[]` | `["high_abs_funding_context"]` | Preserve `funding_rate`, `realized_funding_rate`, timestamp, and high-abs warning. | none / readiness unchanged |
| `timestamp_data_age_clock_skew_watch.json` | Bybit timestamp watch context | `OK_WITH_WARNINGS` | `[]` | `[]` | `["timestamp_watch_context"]` | Parse timestamps; defer age/skew calculations. | none / readiness unchanged |
| `varying_funding_interval.json` | Cross-source varying interval context | `OK` or `OK_WITH_WARNINGS` depending warning policy | `[]` | Source-dependent | `["do_not_hard_code_8h_interval"]` | Preserve 8h/4h differences; Bybit minutes-to-hours candidate; OKX interval derived only if later approved. | none / readiness unchanged |
| `okx_predicted_vs_realized_semantics.json` | OKX predicted vs realized semantics | `OK_WITH_WARNINGS` or `OK` with semantic warning retained | `[]` | Source-dependent | `["do_not_collapse_predicted_and_realized"]` | Separate current, next, settled, and realized fields with semantics preserved. | none / readiness unchanged |

## Future Implementation Sequence

1. Funding Pure Parser Helper Plan v0. This PR only.
2. Funding Pure Parser Helper Implementation v0.
3. Funding Venue Parser Wrapper v0.
4. Funding Normalized Observation Model v0.
5. Funding Packet/Candidate Context Extension Planning v0.
6. Funding Sampling Summary Planning v0.
7. Funding Dashboard Context Status Planning v0.

Each future step must stay public-read-only, fixture-driven, context-only, and no-trade-first unless a separate human-approved task explicitly changes scope.

## Context vs Signal Guardrail

Funding parser output is not a trading signal. It is not standalone `WATCH`, standalone `ENTER`, active promotion evidence, short permission, long permission, venue selection, execution permission, alert authorization, or Council instruction. The normalized funding observation is only a candidate context extension for future research and must not mutate readiness, packet decisions, strategy status, or dashboard interpretation in this planning PR.

## Open Questions

- Should future parser implementation use `Decimal` values, preserve numeric strings, or expose both Decimal and source string values?
- Should `parser_status` remain a string for fixture readability, or become a dataclass/Enum in implementation?
- Should symbol normalization connect to an existing common helper, and if so at what layer?
- For OKX, how should `fundingRate`, `realizedRate`, `nextFundingRate`, and `settFundingRate` be exposed without implying priority or collapsing semantics?
- When a numeric field is invalid, should the whole record be rejected or should optional field-level warnings allow partial records?
- In batch payloads, should one failed record make the whole parse fail, or should partial OK records plus per-record error diagnostics be allowed?
- Should optional missing fields always create warnings, or only when a fixture explicitly expects a warning?
- What high absolute funding threshold, if any, should be used for warnings, and who approves that threshold?
