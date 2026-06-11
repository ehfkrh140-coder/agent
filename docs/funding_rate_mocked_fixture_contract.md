# Funding Rate Mocked Fixture Contract

## Purpose

This document is the docs-only contract for future `funding_rate_context_v0` mocked fixture JSON files. It defines fixture names, pseudo raw payload shapes, required/optional normalized field expectations, parser outcome expectations, warning expectations, and context-only guardrails before any fixture JSON exists.

This contract exists so the next PR can create deterministic mocked fixture files safely. Mocked fixtures should reflect official public exchange documentation shapes, but they must not copy live endpoint responses or be produced by live endpoint calls. They are fake deterministic data for future parser tests.

Funding fixtures are not trading signals, active-promotion evidence, Council execution permission, or proof of order feasibility. Fixture existence must not change readiness, `recommended_default_decision`, Council recommendation, dashboard interpretation, active status, alerts, or execution behavior.

## Non-Goals

This document does not create or authorize:

- Funding Rate fixture JSON files.
- Funding Rate endpoint calls or live endpoint calls.
- Funding Rate parser implementation.
- Funding Rate adapter implementation.
- Funding Rate packet builder implementation.
- Funding Rate readiness implementation.
- Funding Rate sampling collector implementation.
- VWAP-adjusted readiness.
- Generated JSON artifacts.
- Private API, credentials, account/balance/position lookup, orders, transfers, withdrawals, deposits, alerts, Council auto-call, auto-trading, or execution.

## Fixture Contract Principles

| principle | contract |
| --- | --- |
| Deterministic | Every future fixture should use stable mocked values and fixed timestamps so parser tests are repeatable. |
| Public-docs-shaped | Payload shape should follow official public exchange docs at the field-name/type level. |
| No live payload copy | Fixture values must be synthetic and must not be copied from live exchange calls. |
| No endpoint calls | Fixture creation must not require live calls. |
| Context-only | Funding values are diagnostics / regime context only. |
| No-trade | Fixtures must not imply orders, alerts, Council auto-call, active promotion, or execution permission. |
| Narrow v0 | Required fixtures should cover only the finalized minimum v0 source contract before optional context expands. |
| Parser contract only | Parser status, missing fields, and warnings are expectations for future tests, not implemented here. |

## Fixture Naming Policy

Recommended future fixture directory:

```text
tests/fixtures/market_data/funding_rate/
```

Naming rules:

- Use a clear venue prefix: `binance`, `bybit`, `okx`.
- Include market type when relevant: `usdm`, `linear`, `inverse`, `current`.
- Include source endpoint type: `funding_rate_history`, `funding_info`, `instruments_info`, `current_funding_rate`.
- Include scenario type: `normal`, `optional_context`, or explicit `edge_case` wording.
- Keep filenames lowercase snake_case.
- Use `.json` only in the future fixture-files PR. This PR creates no JSON files.

Recommended future filenames:

- `binance_usdm_funding_rate_history_normal.json`
- `binance_usdm_funding_info_interval_cap_floor.json`
- `bybit_linear_funding_history_normal.json`
- `bybit_inverse_funding_history_normal.json`
- `bybit_linear_instruments_info_funding_interval.json`
- `okx_funding_rate_history_normal.json`
- `okx_current_funding_rate_normal.json`
- `missing_required_funding_rate.json`
- `missing_optional_interval.json`
- `string_numeric_parsing.json`
- `positive_funding_rate.json`
- `negative_funding_rate.json`
- `zero_funding_rate.json`
- `high_absolute_funding_context.json`
- `timestamp_data_age_clock_skew_watch.json`
- `varying_funding_interval.json`
- `okx_predicted_vs_realized_semantics.json`

## Required Fixture Contract

| fixture filename | fixture category | source classification | source endpoint represented | venue | market type | purpose | expected raw payload shape summary | required raw fields | optional raw fields | normalized required_v0 fields expected | normalized optional_v0 fields expected | source_semantics expectation | parser_status expectation | required_missing_fields expectation | optional_missing_fields expectation | warnings expectation | context-only guardrail | future parser test expectation | future readiness effect |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `binance_usdm_funding_rate_history_normal.json` | required | `required_primary` | `GET /fapi/v1/fundingRate` | Binance | USDⓈ-M perpetual futures | Validate Binance historical funding charge record shape and mark reference preservation. | List/array of funding records. | `symbol`, `fundingRate`, `fundingTime` | `markPrice` | `venue`, `instrument_id`, `instrument_type`, `symbol_normalized`, `funding_rate`, `funding_rate_timestamp_ms`, `source_endpoint`, `source_semantics`, `parser_status`, `required_missing_fields` | `mark_price_reference`, `optional_missing_fields`, `warnings` | `historical_funding_charge_record` or equivalent. | `ok` in future parser. | Empty. | May include `funding_interval_hours` as optional missing. | None expected for normal case. | `markPrice` is not executable price. | Required Binance history normal fixture parses deterministically. | None; readiness unchanged. |
| `bybit_linear_funding_history_normal.json` | required | `required_primary` | `GET /v5/market/funding/history` | Bybit | Linear perpetual | Validate Bybit linear funding history and category preservation. | Response object with `result.list` records. | `category`, `symbol`, `fundingRate`, `fundingRateTimestamp` | Response `time` if included. | Same required_v0 set. | `source_payload_timestamp_ms`, `optional_missing_fields`, `warnings` | `settled_historical_funding_context` or equivalent. | `ok` in future parser. | Empty. | `funding_interval_hours` optional missing unless instruments-info is joined. | None or non-fatal category/product note. | `linear` category is context, not trade direction. | Required Bybit linear history fixture parses deterministically. | None; readiness unchanged. |
| `okx_funding_rate_history_normal.json` | required | `required_primary` | `GET /api/v5/public/funding-rate-history` | OKX | Swap/perpetual | Validate OKX historical funding context while preserving `fundingRate` and `realizedRate` separation. | Response object with `data` list records. | `instType`, `instId`, `fundingRate`, `fundingTime` | `realizedRate`, `method`, `formulaType` | Same required_v0 set. | `realized_funding_rate`, `optional_missing_fields`, `warnings` | `historical_funding_context` or equivalent. | `ok` in future parser. | Empty. | Current/next funding optional missing. | Optional warning if realized/funding naming remains ambiguous. | History context is not entry/exit instruction. | Required OKX history fixture parses deterministically and keeps fields separate. | None; readiness unchanged. |

## Optional Context Fixture Contract

| fixture filename | why optional_context | why it does not block required fixtures | interval / cap / floor / current predicted / product metadata meaning | source_semantics expectation | normalized field mapping candidate | missing field handling expectation | context-only guardrail | future parser test expectation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `binance_usdm_funding_info_interval_cap_floor.json` | Binance funding info is adjusted cap/floor/interval metadata, not a funding event record. | Minimum Binance history fixture can parse without cap/floor/interval metadata. | `fundingIntervalHours`, `adjustedFundingRateCap`, `adjustedFundingRateFloor` provide source-provided interval and cap/floor context. | `interval_cap_floor_context`. | `funding_interval_hours`, `funding_cap`, `funding_floor`, `source_endpoint`, `source_semantics`. | Missing funding event timestamp is expected and should not fail an optional context parser. | Cap/floor/interval context is not active-promotion evidence. | Optional context parser can normalize interval/cap/floor without changing readiness. |
| `bybit_linear_instruments_info_funding_interval.json` | Bybit instruments info is product metadata and interval/cap/floor context, not funding history. | Bybit funding history normal fixture can parse without instruments-info. | `fundingInterval` is interval metadata in minutes; `upperFundingRate` / `lowerFundingRate` are cap/floor context. | `instrument_interval_cap_floor_context`. | `funding_interval_hours`, `funding_cap`, `funding_floor`, `instrument_type`, `source_endpoint`, `source_semantics`. | Missing funding event timestamp is expected; preserve optional missing fields. | Product metadata and interval do not change readiness. | Optional context parser preserves `linear` category and interval conversion expectations. |
| `bybit_inverse_funding_history_normal.json` | Inverse category coverage is useful but not needed for first minimum linear fixture. | Required Bybit v0 can start with linear history. | Validates inverse product semantics and category preservation. | `settled_historical_funding_context`. | Required_v0 fields plus `instrument_type=inverse`. | Interval remains optional missing unless instruments-info is joined. | Inverse category is not signal direction. | Future parser should not collapse `linear` and `inverse`. |
| `okx_current_funding_rate_normal.json` | OKX current funding adds predicted/current context, next funding time, settlement state, premium, and cap/floor context. | OKX history fixture can cover minimum historical funding context first. | `fundingRate` / `nextFundingRate` are current/predicted context; `settFundingRate` is settlement context; `premium`, `minFundingRate`, `maxFundingRate` are formula/cap/floor context. | `current_predicted_funding_context`. | `predicted_funding_rate`, `next_funding_time_ms`, `realized_funding_rate` or settlement field candidate, `premium_index_reference`, `funding_cap`, `funding_floor`. | Missing optional current fields should become optional missing/warnings, not parser failure if required current fields exist. | Current/predicted funding is not a standalone trigger. | Future parser keeps predicted/current and settled fields separate. |

## Edge Case Fixture Contract

| fixture filename | edge category | purpose | simulated condition | expected parser_status | expected required_missing_fields | expected optional_missing_fields | expected warnings | expected normalized output behavior | expected context-only interpretation | expected future readiness effect | why this edge case matters |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `missing_required_funding_rate.json` | missing required | Validate required missing field behavior. | Funding record lacks `fundingRate` or equivalent required field. | Failure or `NEED_SOURCE_FIELDS`-style status; exact enum deferred. | Includes `funding_rate`. | Optional fields may also be missing. | Missing required funding warning. | No valid normalized funding rate. | Missing data does not imply edge. | None; readiness unchanged. | Prevents silent parsing of incomplete source records. |
| `missing_optional_interval.json` | missing optional | Validate interval optionality. | History payload lacks interval source. | `ok`. | Empty. | Includes `funding_interval_hours`. | Optional interval warning allowed. | Required_v0 output still produced. | Missing interval is diagnostics only. | None. | Ensures v0 does not hard-require interval. |
| `string_numeric_parsing.json` | numeric parsing | Validate string numeric parsing. | Funding, mark, premium, cap, or floor values are numeric strings. | `ok` if parseable. | Empty. | As applicable. | Warning only for malformed optional values. | Numeric values normalize deterministically. | Numeric parse success is not a signal. | None. | Venue APIs commonly encode decimals as strings. |
| `positive_funding_rate.json` | sign coverage | Validate positive funding context. | Funding rate is positive string numeric. | `ok`. | Empty. | As applicable. | None. | Positive normalized funding value. | Positive funding is not short permission. | None. | Prevents direction inference from sign. |
| `negative_funding_rate.json` | sign coverage | Validate negative funding context. | Funding rate is negative string numeric. | `ok`. | Empty. | As applicable. | None. | Negative normalized funding value. | Negative funding is not long permission. | None. | Prevents direction inference from sign. |
| `zero_funding_rate.json` | sign coverage | Validate zero funding context. | Funding rate is `0` or `0.00000000`. | `ok`. | Empty. | As applicable. | None. | Zero normalized funding value. | Zero funding is not no-edge proof. | None. | Handles neutral funding deterministically. |
| `high_absolute_funding_context.json` | context warning | Validate high absolute funding warning. | Funding absolute value exceeds future warning threshold. | `ok` with warning candidate. | Empty. | As applicable. | `high_abs_funding_context` or equivalent. | Funding output plus warning/context. | High absolute funding may be human watch context but not `ENTER`. | None. | Preserves risk context without signal semantics. |
| `timestamp_data_age_clock_skew_watch.json` | timestamp watch | Preserve timestamp/data-age/clock-skew expectations. | Funding timestamp and future local/source timestamps imply stale or negative age. | `ok` or warning status; exact enum deferred. | Empty if required fields present. | Local/age fields may be optional/deferred. | Timestamp/data_age/clock-skew warning expectation. | Funding output plus warning expectation. | Negative data age is not trading edge. | None. | Aligns with existing timestamp watch policy. |
| `varying_funding_interval.json` | interval edge | Validate non-8h interval handling. | Source-provided interval differs from 8h or OKX delta differs. | `ok`. | Empty. | None if interval source present. | Varying interval context warning allowed. | `funding_interval_hours` normalized when available. | Interval variation is not signal. | None. | Prevents hard-coded 8h assumptions. |
| `okx_predicted_vs_realized_semantics.json` | semantic separation | Validate OKX predicted/current vs realized/settled separation. | Payload includes `fundingRate`, `nextFundingRate`, `settFundingRate`, and/or `realizedRate`. | `ok` if fields separated. | Empty. | Venue-specific optional fields allowed. | Warning if labels are ambiguous. | `funding_rate`, `predicted_funding_rate`, and `realized_funding_rate` candidates remain separate. | Semantics separation prevents signal misuse. | None. | OKX exposes multiple funding-related meanings. |

## Venue Raw Shape Expectations

These are pseudo-shapes only. They are not full real payloads and must not be copied from live endpoints.

### Binance `GET /fapi/v1/fundingRate`

```text
[
  {
    symbol: string,
    fundingRate: string numeric,
    fundingTime: integer ms,
    markPrice: string numeric optional
  }
]
```

- Source semantics: `historical_funding_charge_record` or equivalent.
- `markPrice` is an attached funding-record mark reference, not executable price.

### Binance `GET /fapi/v1/fundingInfo`

```text
[
  {
    symbol: string,
    adjustedFundingRateCap: string numeric,
    adjustedFundingRateFloor: string numeric,
    fundingIntervalHours: integer or numeric,
    disclaimer: boolean optional
  }
]
```

- Source semantics: `interval_cap_floor_context`.
- This is optional context, not a funding event source.

### Bybit `GET /v5/market/funding/history`

```text
{
  result: {
    category: linear | inverse optional/source-level,
    list: [
      {
        symbol: string,
        fundingRate: string numeric,
        fundingRateTimestamp: string or integer ms
      }
    ]
  }
}
```

- Source semantics: `settled_historical_funding_context`.
- Category must preserve `linear` vs `inverse`; do not collapse product semantics.

### Bybit `GET /v5/market/instruments-info`

```text
{
  result: {
    category: linear | inverse,
    nextPageCursor: string optional,
    list: [
      {
        symbol: string,
        fundingInterval: numeric minutes,
        upperFundingRate: string numeric optional,
        lowerFundingRate: string numeric optional
      }
    ]
  }
}
```

- Source semantics: `instrument_interval_cap_floor_context`.
- This is optional context, not a funding event source.

### OKX `GET /api/v5/public/funding-rate-history`

```text
{
  data: [
    {
      instType: string,
      instId: string,
      fundingRate: string numeric,
      realizedRate: string numeric optional,
      fundingTime: string or integer ms,
      method: string optional,
      formulaType: string optional
    }
  ]
}
```

- Source semantics: `historical_funding_context`.
- Do not collapse `fundingRate` and `realizedRate`.

### OKX `GET /api/v5/public/funding-rate`

```text
{
  data: [
    {
      instType: string,
      instId: string,
      fundingRate: string numeric,
      nextFundingRate: string numeric optional,
      fundingTime: string or integer ms,
      nextFundingTime: string or integer ms optional,
      settFundingRate: string numeric optional,
      premium: string numeric optional,
      minFundingRate: string numeric optional,
      maxFundingRate: string numeric optional,
      ts: string or integer ms optional
    }
  ]
}
```

- Source semantics: `current_predicted_funding_context`.
- Current/predicted and settled context must remain separate.

## Normalized Output Expectations

Required v0 expected fields:

- `venue`
- `instrument_id`
- `instrument_type`
- `symbol_normalized`
- `funding_rate`
- `funding_rate_timestamp_ms`
- `source_endpoint`
- `source_semantics`
- `parser_status`
- `required_missing_fields`

Optional v0 / venue-specific optional fields:

- `funding_interval_hours`
- `next_funding_time_ms`
- `realized_funding_rate`
- `predicted_funding_rate`
- `funding_cap`
- `funding_floor`
- `mark_price_reference`
- `premium_index_reference`
- `optional_missing_fields`
- `warnings`

Deferred fields for this fixture contract:

- `local_observed_at_ms`
- `data_age_ms`
- `clock_skew_warning`
- `source_payload_timestamp_ms`

Contract expectations:

- Deferred fields must not be required in v0 fixture JSON.
- If a required_v0 field is missing, future parser output should use a failure or `NEED_SOURCE_FIELDS`-style `parser_status`; exact enum is deferred.
- Missing optional fields should not fail the parser; they should appear in `optional_missing_fields` or `warnings` as appropriate.
- This PR does not define parser_status enum values in code.
- Future parser PR must finalize enum/value naming.

## Numeric Parsing Policy

Funding public payloads commonly use string numeric fields. Future fixtures should cover:

- Positive funding string.
- Negative funding string.
- Zero funding string.
- High absolute funding string.
- `markPrice`, `premium`, cap, and floor string numeric values.
- Integer timestamps.
- String timestamps.
- Invalid numeric string as a future optional edge fixture if parser policy needs it.

Guardrails:

- Positive funding is not short permission.
- Negative funding is not long permission.
- High absolute funding is not `ENTER`.
- Numeric parsing success is not readiness success and not a trade signal.

## Timestamp Policy

- `funding_rate_timestamp_ms` is a required_v0 candidate.
- `next_funding_time_ms` is optional_v0 or venue-specific optional.
- `local_observed_at_ms`, `data_age_ms`, and `clock_skew_warning` are deferred in this fixture contract.
- `timestamp_data_age_clock_skew_watch.json` is an edge fixture candidate for future adapter/parser timestamp policy only.
- This PR does not implement clock-skew or data-age calculation.
- Negative `data_age_ms` is not a trading edge; it may be warning/watch context only under future policy.

## Predicted vs Realized Fixture Policy

- Normalized `funding_rate` must be interpreted with `source_semantics`.
- OKX history fixtures should plan a semantics edge case where both `fundingRate` and `realizedRate` are present.
- OKX current fixtures must not collapse `fundingRate`, `nextFundingRate`, and `settFundingRate`.
- Bybit funding history `fundingRate` is treated as settled historical context for v0 fixture planning.
- Binance funding history `fundingRate` is treated as a funding charge record context at `fundingTime`.
- Future parsers must not interpret `funding_rate` without `source_semantics`.

## Future Parser Test Matrix

| future test | fixture input | expected parser behavior | no-trade expectation |
| --- | --- | --- | --- |
| Required Binance history normal parses OK | `binance_usdm_funding_rate_history_normal.json` | `parser_status=ok`, required fields populated. | No readiness or signal change. |
| Required Bybit linear history normal parses OK | `bybit_linear_funding_history_normal.json` | `parser_status=ok`, category preserved. | No readiness or signal change. |
| Required OKX history normal parses OK | `okx_funding_rate_history_normal.json` | `parser_status=ok`, funding/realized fields separated. | No readiness or signal change. |
| Missing required funding rate reports missing field | `missing_required_funding_rate.json` | `required_missing_fields` includes `funding_rate`; failure/need-source status. | Missing data is not edge. |
| Missing optional interval does not fail parser | `missing_optional_interval.json` | `parser_status=ok`; optional interval recorded missing/warning. | No readiness change. |
| String numeric values parse deterministically | `string_numeric_parsing.json` | Parse numeric strings or warn on invalid optional strings. | Numeric parse is not signal. |
| Positive/negative/zero funding parse without direction recommendation | sign fixtures | Preserve sign and value. | No long/short permission. |
| High absolute funding creates warning/context but no ENTER | `high_absolute_funding_context.json` | Warning/context field populated. | No `ENTER`, alert, or execution. |
| OKX predicted vs realized fields remain separate | `okx_predicted_vs_realized_semantics.json` | Do not collapse current/predicted/settled/realized fields. | No signal from semantic split. |
| Timestamp edge preserves warning expectations | `timestamp_data_age_clock_skew_watch.json` | Timestamp warnings retained when future policy exists. | Timestamp warning is not edge. |
| Varying interval does not assume 8h | `varying_funding_interval.json` | Uses source interval/delta or warning. | Interval variation is not signal. |

## Context vs Signal Guardrail

Funding fixtures are context-only test inputs.

- Fixture existence is not a trading signal.
- Fixture existence is not active promotion evidence.
- Fixture existence is not Council execution permission.
- Funding Rate is not standalone `WATCH`.
- Funding Rate is not standalone `ENTER`.
- Positive funding is not short permission.
- Negative funding is not long permission.
- High absolute funding may be human watch context, but it is not `ENTER`.
- Fixture parser success must not change readiness, `recommended_default_decision`, Council recommendation, active status, alert behavior, or execution behavior.

## Implementation Sequence

Safe future sequence:

1. Funding Mocked Fixture Contract v0. This PR only.
2. Funding Mocked Fixture Files v0.
3. Funding Pure Parser Helper Planning or Implementation v0.
4. Venue-Specific Funding Parser Wrappers v0.
5. Normalized Funding Observation Model v0.
6. Packet/Candidate Context Extension Planning v0.
7. Sampling Summary Planning v0.
8. Dashboard Funding Context Status Planning v0.

Each step should stay scoped, additive, public-read-only, context-only, and no-trade-first.

## Open Questions

- Exact future `parser_status` enum names remain open.
- Exact `source_semantics` enum names remain open.
- Whether invalid numeric strings belong in the first fixture-files PR or a later edge-case PR remains open.
- Whether future parser tests should join optional interval/cap/floor fixtures with required history fixtures remains open.
- Whether `source_payload_timestamp_ms` should move from deferred to optional_v0 in the first parser implementation remains open.
- Exact high absolute funding warning threshold remains open and must not affect readiness without separate policy approval.
