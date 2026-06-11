# Funding Rate Venue Parser Wrapper Plan

## Purpose

This document defines the role and boundary for future venue-specific Funding Rate parser wrappers that may sit above the existing pure helper in `src/market_data/funding_rate_parser.py`.

The wrapper layer is a planning-only candidate for safe orchestration between a future public-read-only adapter and the pure parser helper. Its purpose is to preserve venue/source provenance, choose the correct parser labels, call the pure helper deterministically, and return a context-only wrapper envelope without changing readiness, packets, dashboards, or execution behavior.

## Non-Goals

This PR does not implement or modify any of the following:

- Funding Rate wrapper code.
- Funding Rate adapter code.
- HTTP clients, endpoint calls, live payload collection, or live response copy/paste.
- Funding Rate pure parser helper code.
- Funding Rate parser tests.
- Packet builder or candidate builder behavior.
- Readiness policy, readiness thresholds, or readiness interpretation.
- Sampling collectors, generated sampling JSON, or generated packet JSON.
- Dashboard rows, dashboard automation, alerting, or Council auto-call behavior.
- Registry, config, active strategy, or active promotion state.
- Fixture JSON files.

## Current State

### Exists

- Funding Rate public source research.
- Funding Rate mocked fixture files for required, optional, and edge cases.
- Funding Rate pure parser helper.
- Funding Rate parser unit tests.

### Not Yet Present

- Venue wrapper.
- Live/public endpoint adapter.
- Packet or candidate extension.
- Readiness policy for Funding Rate context.
- Sampling collector.
- Dashboard row automation.

## Wrapper Design Principles

- Public-read-only: wrappers must only orchestrate caller-provided public market-data payloads.
- Context-only: wrapper output is diagnostics/regime context, not an entry signal.
- No private API: wrappers must not call private endpoints or depend on private endpoint payloads.
- No credentials: wrappers must not read API keys, secrets, tokens, config credentials, or environment variables.
- No account state: wrappers must not read balances, positions, open orders, transfers, withdrawals, deposits, or account metadata.
- No order/execution: wrappers must not place, cancel, route, or recommend orders.
- Raw payload provenance should be preserved so future reviewers can audit venue, source endpoint, category, symbol, adapter metadata, and caller-provided timestamps without treating them as trade permission.
- Wrappers may call the pure helper, but they must not change readiness.
- Wrapper success is not a trade signal, not `WATCH`, not `ENTER`, and not active promotion evidence.
- Wrappers are candidates for a thin orchestration layer between a future live endpoint caller and the pure parser.

## Proposed Wrapper Boundary

### Candidate Responsibilities

- Select the venue label expected by the pure helper.
- Select the source endpoint label expected by the pure helper.
- Attach or preserve payload provenance metadata, such as adapter source, category hint, request symbol, and payload timestamp supplied by a caller.
- Call the pure helper with caller-provided raw payloads.
- Wrap the parser result in a wrapper result envelope.
- Prevent obvious source endpoint / venue mismatches before parser invocation or mark them as wrapper diagnostics.
- Define the contract by which a future adapter passes raw payloads into the parser helper.
- Add wrapper-level warnings for orchestration concerns that are outside the pure helper, such as category-hint mismatch or empty top-level payload.

### Explicitly Out of Boundary

- HTTP request construction or execution.
- Authentication.
- Account data access.
- Order execution, order cancellation, transfer, withdrawal, deposit, or execution routing.
- Readiness decisions.
- Packet builder mutation.
- Sampling persistence.
- Dashboard updates.
- Council recommendation generation.
- Active promotion.

## Proposed Wrapper API Draft

No code is introduced by this PR. The following names are planning-only API candidates for a future implementation PR.

| Wrapper API candidate | venue | source_endpoint | source_semantics | Input shape | Output envelope | Expected pure helper call | Additional wrapper validation | Context-only guardrail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `parse_binance_usdm_funding_rate_history(payload)` | `binance_usdm` | `binance_usdm_funding_rate_history` | `historical_funding_charge_record` | Caller-provided Binance USD-M funding history payload, expected as a list of records. | Wrapper envelope with parser result, provenance, counts, warnings, `context_only=True`, and `readiness_effect="unchanged"`. | `parse_funding_rate_payload(payload, venue="binance_usdm", source_endpoint="binance_usdm_funding_rate_history")` | Check that payload is not obviously a non-history object; preserve requested symbol/source provenance if supplied by a future adapter. | History parse success is historical funding charge record context only, not short/long permission. |
| `parse_binance_usdm_funding_info(payload)` | `binance_usdm` | `binance_usdm_funding_info` | `interval_cap_floor_context` | Caller-provided Binance funding info payload, expected as a list of funding cap/floor/interval records. | Wrapper envelope with parser result, provenance, counts, warnings, `context_only=True`, and `readiness_effect="unchanged"`. | `parse_funding_rate_payload(payload, venue="binance_usdm", source_endpoint="binance_usdm_funding_info")` | Distinguish funding info from funding history; preserve symbol and source provenance; warn on empty list. | Funding cap/floor/interval context is optional context and cannot trigger readiness. |
| `parse_bybit_v5_funding_history(payload, *, category_hint=None)` | `bybit` | `bybit_v5_funding_history` | `settled_historical_funding_context` | Caller-provided Bybit V5 funding history object with `result.list`; optional `category_hint` from adapter/request context. | Wrapper envelope with category provenance, parser result, counts, warnings, `context_only=True`, and `readiness_effect="unchanged"`. | `parse_funding_rate_payload(payload, venue="bybit", source_endpoint="bybit_v5_funding_history")` | Compare `category_hint` with payload category when present; warn on linear/inverse mismatch; preserve request category even if parser can infer payload category. | Settled historical funding context preserves category provenance; it does not choose execution venue or direction. |
| `parse_bybit_v5_instruments_info(payload, *, category_hint=None)` | `bybit` | `bybit_v5_instruments_info` | `instrument_interval_cap_floor_context` | Caller-provided Bybit instruments-info object with `result.list`; optional `category_hint` from adapter/request context. | Wrapper envelope with category provenance, parser result, counts, warnings, `context_only=True`, and `readiness_effect="unchanged"`. | `parse_funding_rate_payload(payload, venue="bybit", source_endpoint="bybit_v5_instruments_info")` | Preserve category hint; warn if hint and payload category disagree; retain raw instrument interval provenance while helper converts minutes to hours. | Instrument interval/cap/floor data is context only and not readiness permission. |
| `parse_okx_funding_rate_history(payload)` | `okx` | `okx_funding_rate_history` | `historical_funding_context` | Caller-provided OKX funding-rate-history object with `data` records. | Wrapper envelope with parser result, provenance, counts, warnings, `context_only=True`, and `readiness_effect="unchanged"`. | `parse_funding_rate_payload(payload, venue="okx", source_endpoint="okx_funding_rate_history")` | Validate source label is historical; preserve `instId`, `instType`, and source provenance; keep `fundingRate` and `realizedRate` semantics distinct when both are present instead of collapsing them into current predicted fields. | Historical funding context is not standalone `WATCH` or `ENTER`. |
| `parse_okx_current_funding_rate(payload)` | `okx` | `okx_current_funding_rate` | `current_predicted_funding_context` | Caller-provided OKX current funding-rate object with `data` records containing current, predicted, settled, and premium context. | Wrapper envelope with parser result, provenance, counts, warnings, `context_only=True`, and `readiness_effect="unchanged"`. | `parse_funding_rate_payload(payload, venue="okx", source_endpoint="okx_current_funding_rate")` | Preserve `fundingRate`, `realizedRate`, `nextFundingRate`, `settFundingRate`, and premium provenance as distinct fields through the helper result. | Current or predicted funding is context only and is never an `ENTER` trigger. |

## Wrapper Output Envelope Draft

If a future wrapper implementation wraps the pure helper result, the envelope should remain minimal and explicit:

| Field | Draft meaning | Default / guardrail |
| --- | --- | --- |
| `wrapper_status` | Wrapper-level orchestration status, separate from `parser_status`. | Should describe wrapper orchestration only, such as `OK`, `OK_WITH_WARNINGS`, `WRAPPER_INPUT_EMPTY`, `WRAPPER_SOURCE_MISMATCH`, or `WRAPPER_INVALID_INPUT`. |
| `venue` | Venue label passed to or selected for the pure helper. | Must match the wrapper function name and expected source endpoint. |
| `source_endpoint` | Source endpoint label passed to the pure helper. | Must remain provenance, not an endpoint-call instruction. |
| `source_semantics` | Source semantics expected for the selected venue/source pair. | Must preserve history vs current vs predicted vs interval context distinctions. |
| `parser_result` | The unchanged pure helper result. | Must not rewrite parser output into readiness, order, alert, or recommendation fields. |
| `wrapper_warnings` | Wrapper-level warnings that are separate from parser warnings. | Warnings are diagnostics only and never trade signals. |
| `provenance` | Caller-provided metadata such as adapter name, request category, request symbol, source payload timestamp, and collection notes. | Must not include secrets, private account data, or credential-derived information. |
| `input_record_count` | Wrapper estimate of records received before parser invocation. | Diagnostic only; count success is not readiness success. |
| `parsed_record_count` | Count copied from or derived from parser result after parsing. | Diagnostic only; parsed records do not imply execution permission. |
| `context_only` | Boolean guardrail that marks output as non-executable context. | Must be `True`. |
| `readiness_effect` | Declares whether the wrapper changed readiness. | Must default to `"none"` or `"unchanged"`; v0 should use `"unchanged"`. |

## Venue-Specific Wrapper Planning

### Binance

- The USD-M funding history wrapper should select `binance_usdm` and `binance_usdm_funding_rate_history` and preserve symbol/source provenance.
- The `fundingInfo` wrapper should select `binance_usdm` and `binance_usdm_funding_info` and preserve cap/floor/interval provenance.
- `markPrice` data is reference-only if it appears in future source context and must not be treated as executable price or entry permission.
- `fundingInfo` remains optional context for interval/cap/floor diagnostics, not a readiness gate.

### Bybit

- The funding history wrapper should preserve the Bybit V5 category context for `linear` versus `inverse`.
- The instruments-info wrapper should preserve interval/cap/floor context and any caller-provided category hint.
- `category_hint` is a planning candidate for future wrapper arguments when the adapter/request path has category metadata that may not be fully present in payload records.
- A category mismatch warning is a wrapper-level diagnostic candidate when `category_hint` and payload category disagree.
- `fundingInterval` minutes-to-hours conversion remains pure helper responsibility, but the wrapper should preserve original source/category provenance around that conversion.

### OKX

- The funding-rate-history wrapper should preserve `historical_funding_context` semantics.
- The current funding-rate wrapper should preserve current, predicted, settled, and premium context without collapsing fields.
- `fundingRate`, `realizedRate`, `nextFundingRate`, and `settFundingRate` must remain distinct in provenance and parser result interpretation; history wrappers should not collapse `fundingRate` and `realizedRate` when both are present.
- `premium` is formula/context information only.
- Current predicted funding is not an `ENTER` trigger, not standalone `WATCH`, and not active promotion evidence.

## Wrapper Error / Warning Policy

- Unsupported sources may be blocked by a wrapper before pure helper invocation when the wrapper function name and source label cannot match. Alternatively, a generic future wrapper may delegate unsupported source handling to the pure helper. This decision should be explicit in the implementation PR.
- Venue/source mismatch should produce a wrapper-level warning or wrapper-level invalid status before parser invocation.
- Category mismatch should produce a wrapper-level warning when a caller-supplied `category_hint` conflicts with payload category data.
- Empty payload should produce a wrapper-level warning candidate. The implementation PR must decide whether empty payload maps to `OK_WITH_WARNINGS`, `WRAPPER_INPUT_EMPTY`, or pure helper `INVALID_SOURCE_SHAPE` behavior.
- Wrapper warnings are diagnostics/context only and are never trade signals.
- `wrapper_status` describes wrapper orchestration. `parser_status` describes pure helper parsing. Neither status may be interpreted as readiness success or execution permission.

## Relationship to Future Adapter

A future adapter may be responsible for public endpoint calls, but this PR adds no adapter and performs no endpoint calls. The wrapper is a thin layer candidate that may accept raw payloads already fetched by an adapter and pass them to the pure parser helper with fixed venue/source labels and provenance metadata.

Even if an adapter is introduced later, private API usage, credentials, account data, balance/position lookup, order placement, withdrawal, deposit, transfer, alert execution, and Council auto-call remain forbidden unless a separate human-approved policy explicitly changes the project scope. Funding Rate context planning does not grant that permission.

## Relationship to Packet / Candidate Context

A future wrapper result may become a candidate for `packet.extensions` or `candidate.extensions`, but this PR does not modify packet builders, candidate builders, schemas, generated packets, or runtime packet behavior.

Wrapper output should be designed as context that can be attached later without mutating readiness or creating executable intent.

## Relationship to Readiness

Wrapper results do not change readiness. Funding Rate wrapper success is not `WATCH`, not `ENTER`, not readiness success, and not a trading signal.

Any future readiness change involving Funding Rate context requires a separate policy PR with explicit tests, review evidence, and human/GPT designer review. Without that policy PR, Funding Rate wrapper output must keep `readiness_effect="unchanged"` or equivalent.

## Relationship to Sampling / Dashboard

Future work may define a sampling summary or dashboard context row for Funding Rate wrapper output, but this PR does not implement sampling, persistence, generated sampling JSON, dashboard updates, or dashboard automation.

Any future sampling/dashboard work should remain public-read-only, context-only, no-trade-first, and should continue to distinguish diagnostics from execution signals.

## Future Wrapper Test Matrix

A future wrapper implementation PR should include tests for at least the following:

- Binance history wrapper calls pure helper with the correct venue/source.
- Binance `fundingInfo` wrapper calls pure helper with the correct venue/source.
- Bybit funding history wrapper preserves category.
- Bybit instruments-info wrapper handles category hint.
- OKX history wrapper preserves historical semantics.
- OKX current wrapper preserves predicted/current/settled separation.
- Wrapper output has `context_only=True`.
- Wrapper output has `readiness_effect="unchanged"`.
- Wrapper output has no order, alert, execution, private API, balance, position, transfer, withdrawal, deposit, `WATCH`, or `ENTER` permission keys.
- Unsupported wrapper input returns a wrapper-level diagnostic without exception when safe to do so.
- Wrapper does not import network or private API libraries.
- Wrapper does not read files or environment variables.

## Implementation Sequence

Recommended sequence:

1. Funding Venue Parser Wrapper Plan v0.
2. Funding Venue Parser Wrapper Implementation v0.
3. Funding Adapter Public Source Planning v0.
4. Funding Public Adapter Implementation v0.
5. Funding Packet/Candidate Context Extension Planning v0.
6. Funding Sampling Summary Planning v0.
7. Funding Dashboard Context Status Planning v0.

This PR performs only step 1: Funding Venue Parser Wrapper Plan v0.

## Context vs Signal Guardrail

Funding Rate wrapper output is not a trading signal. It is not standalone `WATCH`, standalone `ENTER`, active promotion evidence, execution permission, order direction, venue preference, alert authorization, Council instruction, or readiness success.

Positive funding, negative funding, zero funding, high absolute funding, parser success, parser warnings, wrapper success, wrapper warnings, and parsed record counts are all context/diagnostics only.

## Open Questions

- Should wrappers live in a single module or in venue-specific modules?
- Should `category_hint` be a wrapper argument, provenance metadata, or both?
- Should `wrapper_status` naming be separate from `parser_status` naming, and what exact names should be used?
- When a future adapter exists, where should `source_payload_timestamp_ms` be attached?
- Should empty payload be treated as `OK_WITH_WARNINGS`, `WRAPPER_INPUT_EMPTY`, or `INVALID_SOURCE_SHAPE`?
- How strict should wrappers be about source endpoint / venue mismatch before delegating to the pure helper?
- Should wrappers preserve the full raw payload reference in provenance, or only safe metadata and counts?
- Should future wrapper tests use mocks around the pure helper or call the helper with fixture payloads directly?
