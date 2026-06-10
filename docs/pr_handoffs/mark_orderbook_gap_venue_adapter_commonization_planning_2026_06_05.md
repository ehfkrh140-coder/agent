# Mark-Orderbook Gap Hunt Venue Adapter Commonization Planning v0

## 1. Purpose

Plan a future, small-slice commonization path for the Binance / Bybit / OKX `mark_orderbook_gap_hunt_v0` venue adapters without changing runtime behavior in this PR.

This is a planning-only, docs-only handoff document. It records the current evidence baseline, commonization candidates, venue-specific boundaries, proposed future implementation PR slices, risks, rollback, and no-trade compliance.

## 2. Current evidence baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental, non-active, analysis-only, and `NO_TRADE_ONLY`.
- Binance 30-sample extended sampling evidence is complete.
- Bybit 30-sample extended sampling evidence is complete.
- OKX 30-sample extended sampling evidence is complete.
- Binance / Bybit / OKX all have `mark_orderbook_gap_hunt_v0` baseline coverage.
- The extended evidence proves user-local sampling pipeline success across venues.
- The extended evidence does not prove profitable edge.
- The extended evidence does not prove persistent edge.
- `NO_PERSISTENT_EDGE`, `REJECT`, and `council_recommended=false` remain normal no-edge outcomes where observed.
- Mark price is not an executable price; it must not be treated as directly tradable bid/ask liquidity.
- Generated packet/sampling JSON remains smoke artifact data and must not be committed.

## 3. Read-only review scope for this plan

The following files/areas were reviewed only to compare structure and identify planning candidates. This PR does not modify them:

- `src/market_data/adapters/mark_orderbook_gap_hunt.py`
- `src/market_data/parsers/mark_orderbook_gap_hunt.py`
- `src/strategy/mark_orderbook_gap_hunt_readiness.py`
- `tools/collect_market_data.py`
- `tools/sample_market_data.py`
- Related `tests/test_mark_orderbook_gap_hunt_*` files

## 4. Commonization candidates

These items appear suitable for future shared helpers or constants, provided each change is implemented in a small, behavior-preserving PR with venue regression tests.

### 4.1 Public fetch diagnostics shape

Candidate commonization:

- Build a shared diagnostics envelope for public GET calls.
- Preserve fields such as endpoint, params, parser stage, HTTP status, elapsed time, exchange error code/message where available, and safe response preview.
- Keep diagnostics public-read-only and scrubbed of credential-like fields.

Why this is a candidate:

- All three adapters fetch multiple public endpoints and attach diagnostics for success and failure paths.
- A shared builder could reduce drift in field naming and error-shape handling.

Guardrail:

- Do not hide venue-specific error codes or venue-specific response semantics behind overly generic labels.

### 4.2 `safe_response_preview` handling

Candidate commonization:

- Use one helper for bounded safe response previews.
- Keep preview length deterministic.
- Ensure preview generation never introduces private headers, auth values, secrets, or generated artifact blobs.

Why this is a candidate:

- Failure diagnostics across venues should expose enough public response context for review without leaking sensitive data.

Guardrail:

- The helper must remain safe-by-default and should not stringify local environment, headers, credentials, or request auth metadata.

### 4.3 Adapter metadata `NO_TRADE_ONLY` fields

Candidate commonization:

- Centralize stable adapter metadata wording and fields for:
  - experimental / non-active status
  - `NO_TRADE_ONLY`
  - analysis-only packet language
  - no private API / no trading behavior language

Why this is a candidate:

- The same no-trade assertions should remain consistent across Binance, Bybit, and OKX.

Guardrail:

- A shared helper must not imply active strategy promotion or execution readiness.

### 4.4 Parser output to `OpportunityPacket` mapping pattern

Candidate commonization:

- Extract shared packet-building mapping for parser output fields that are already normalized across venues:
  - observation IDs and candidate IDs
  - venue and instrument identifiers
  - mark/bid/ask/gross gap/net gap fields
  - normalized parser status
  - missing fields / warnings / diagnostics linkage

Why this is a candidate:

- Adapter packet assembly follows the same high-level structure after parser normalization.

Guardrail:

- Parser behavior itself should remain venue-aware; this candidate is about mapping normalized output into the packet shape, not changing parsing semantics.

### 4.5 Readiness invocation pattern

Candidate commonization:

- Centralize the adapter-side call pattern into readiness evaluation, including config-driven parameters such as fee/slippage buffer, freshness requirement, liquidity pass, size/notional resolved flag, and minimum net gap.

Why this is a candidate:

- Each adapter ultimately passes normalized parser output into the same readiness helper.

Guardrail:

- Do not change readiness thresholds, readiness statuses, `WATCH`/`REJECT` semantics, or analysis-only behavior in a commonization PR.

### 4.6 Candidate metrics mapping

Candidate commonization:

- Use a shared metrics builder for stable candidate metrics:
  - gross gap percentage
  - estimated net gap percentage
  - mark price
  - best bid / best ask
  - parser normalized status
  - readiness status and pass flag
  - data age / freshness indicators

Why this is a candidate:

- Sampling and review evidence depend on stable metric names across venues.

Guardrail:

- Do not collapse venue-specific units, contract fields, or warning labels into a misleading common value.

### 4.7 Assumptions / warnings wording

Candidate commonization:

- Standardize recurring assumptions:
  - public no-key endpoints only
  - analysis-only packet
  - mark price is not executable liquidity
  - no private API
  - no trading behavior
  - sampling integration is separate from packet generation
  - timestamp/data-age policy unchanged unless explicitly changed in a separate policy PR

Why this is a candidate:

- Consistent wording makes generated packet reviews easier and avoids stale phrasing.

Guardrail:

- Venue-specific warnings must remain venue-specific where semantics differ.

### 4.8 Latency and `data_quality` envelope

Candidate commonization:

- Build a shared `data_quality` / latency envelope from diagnostics and parser output.
- Preserve per-endpoint latency and total latency visibility where available.
- Keep freshness and data-age fields explicit.

Why this is a candidate:

- Sampling summaries and watch-item triage rely on consistent latency and freshness labels.

Guardrail:

- Do not normalize away negative `data_age_ms`; timestamp and clock-skew interpretation requires a separate policy task.

### 4.9 `generated_from` / `source_files` metadata

Candidate commonization:

- Centralize generated provenance fields that tell reviewers which public venue sources contributed to a packet.
- Use explicit venue-specific source names while maintaining a shared metadata shape.

Why this is a candidate:

- Provenance should be consistent enough for review while retaining venue detail.

Guardrail:

- Provenance must not imply private data, execution readiness, or active strategy status.

### 4.10 Sampling interpretation labels

Candidate commonization:

- Standardize documentation and, in later implementation PRs if needed, stable labels around:
  - `NO_PERSISTENT_EDGE`
  - `REJECT`
  - `WATCH`
  - `NEED_DATA`
  - `council_recommended=false`
  - sampling pipeline success vs profitability evidence

Why this is a candidate:

- Evidence PRs should consistently distinguish no-edge results from pipeline failures.

Guardrail:

- Interpretation labels remain analysis-only and must not trigger alerts, Council auto-call, execution, or active promotion.

## 5. Venue-specific boundaries

These items should not be commonized, or should remain explicitly venue-specific with tests and review notes.

### 5.1 Endpoint paths and params

- Binance, Bybit, and OKX use different public endpoint paths and parameter names.
- Commonization should not hide endpoint differences that reviewers need for public API verification.

### 5.2 Binance USDM response shape

- Binance USDⓈ-M responses have Binance-specific mark price, orderbook depth, and exchange info shapes.
- Binance symbols use `BTCUSDT` style naming for this baseline.

### 5.3 Bybit V5 response shape

- Bybit V5 uses `retCode` / `retMsg` style responses.
- Bybit linear endpoints use `category=linear` semantics.
- Bybit symbols use `BTCUSDT` style naming for this baseline.

### 5.4 OKX response shape

- OKX uses `code` / `msg` response fields.
- OKX instrument fields include `instId` / `instType` semantics.
- OKX symbols use `BTC-USDT-SWAP` style naming for this baseline.

### 5.5 Symbol naming

- `BTCUSDT` and `BTC-USDT-SWAP` are not interchangeable strings.
- Shared helpers should accept venue-specific normalized identifiers rather than constructing symbol names generically.

### 5.6 Timestamp semantics and possible clock skew

- Bybit negative `data_age_ms` remains a timestamp/clock-skew policy watch item.
- OKX negative `data_age_ms` is also observed and remains a timestamp/clock-skew policy watch item.
- A common helper must not clamp, reinterpret, or silently ignore negative `data_age_ms`.
- Any timestamp/data-age semantics change requires a separate policy PR.

### 5.7 Contract / lot / notional interpretation

- Venue contract, lot, min size, min notional, and multiplier fields differ.
- Commonization must not assume one venue's lot-size or notional model applies to another venue.

### 5.8 Funding fields availability

- Funding-related fields are not guaranteed to be present with the same name, precision, or timing semantics across venues.
- Missing funding data should remain venue-aware and should not be treated as equivalent across venues without explicit policy.

### 5.9 OKX index/reference semantics

- OKX `index_price=None` remains an OKX index/reference semantics watch item.
- A common adapter helper must not synthesize, assume, or backfill OKX index price.
- Any OKX index/reference endpoint implementation must be a separate PR with explicit tests and user-local smoke evidence.

### 5.10 Size units: base asset vs contracts

- Binance and Bybit baseline top-of-book sizes are represented as base-asset style quantities.
- OKX swap top-of-book sizes are represented as contracts.
- Shared candidate metrics must keep size unit labels explicit.

### 5.11 Venue-specific warnings

- Venue-specific warnings should remain visible for reviewer triage.
- Common assumptions wording can be shared, but warnings tied to response shape, contract semantics, timestamp behavior, or index/reference semantics must stay venue-specific.

## 6. Proposed implementation PR slices

This PR implements none of the following. These are proposed future, small, reviewable PRs.

### PR 1: Shared constants / metadata wording helper

- Add shared constants for `NO_TRADE_ONLY`, experimental/non-active metadata, and analysis-only assumptions.
- Scope: metadata wording only.
- Required checks: existing adapter tests plus assertions that no active strategy, execution, alert, Council auto-call, or private API fields appear.

### PR 2: Shared diagnostics builder helper

- Add a helper for public fetch diagnostics and safe response previews.
- Scope: diagnostic shape and safe preview only.
- Required checks: venue adapter error-path regression tests for Binance, Bybit, and OKX.

### PR 3: Shared readiness/candidate mapping helper

- Add a helper that maps normalized parser output and readiness output into stable candidate metrics and packet fields.
- Scope: mapping only; no parser/readiness behavior change.
- Required checks: golden or regression tests proving packet fields and sampling summary inputs remain unchanged.

### PR 4: Venue-specific adapter regression tests

- Strengthen tests around venue-specific response shape, symbol naming, timestamp watch fields, size units, funding field availability, and OKX `index_price=None` semantics.
- Scope: tests only.
- Required checks: per-venue adapter tests and parser/readiness tests.

### PR 5: User-local smoke evidence update

- After any behavior-preserving helper refactor, request user-local public read-only smoke/sampling evidence for Binance, Bybit, and OKX.
- Scope: evidence docs only; generated JSON remains uncommitted.
- Required checks: changed files limited to `docs/pr_handoffs/` evidence and no generated JSON staged/committed.

## 7. Risk assessment

- Over-commonization risk: shared helpers may hide important venue differences or make reviewers assume uniform semantics where none exist.
- OKX `index_price=None` handling risk: common code could incorrectly synthesize or require an index price, changing OKX evidence interpretation.
- Negative `data_age_ms` interpretation risk: common code could clamp, reinterpret, or downgrade timestamp/clock-skew watch items without policy approval.
- Contract size / notional misinterpretation risk: a generic quantity helper could confuse base-asset quantities with contract counts or venue-specific notional rules.
- Mark price executable-price risk: reviewers or code could mistakenly treat mark price as executable bid/ask liquidity; all commonization must preserve the warning that mark price is not directly executable.
- Sampling-evidence interpretation risk: future evidence could be read as profitability or persistent edge rather than pipeline success unless labels remain explicit.

## 8. Out of scope confirmation

This planning PR does not implement or modify:

- `src/` code
- config or strategy registry files
- active strategy state
- `mark_orderbook_gap_hunt_v0` active promotion
- timestamp policy
- OKX index endpoint
- common base adapter
- parser behavior
- readiness behavior
- alert behavior
- Council auto-call
- execution behavior
- private API usage
- credentials, API keys, secrets, tokens, or auth headers
- account, balance, position, order, cancel, withdraw, deposit, or transfer behavior
- generated packet JSON
- generated sampling JSON
- `data/market_samples/*.json`
- `data/generated_packets/*.json`

## 9. No-trade compliance

- Active strategy promotion: no
- Council auto-call: no
- Alert: no
- Execution: no
- Private API: no
- Credentials/API keys/secrets/tokens: no
- Account/balance/position lookup: no
- Order/cancel: no
- Withdrawal/deposit/transfer: no
- Auto-trading: no
- Generated JSON commit: no
- `NO_TRADE_ONLY` preserved: yes
- Analysis-only planning document: yes

## 10. Generated artifact handling

Generated files under paths such as the following remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR intentionally adds only `docs/pr_handoffs/mark_orderbook_gap_venue_adapter_commonization_planning_2026_06_05.md`.

## 11. Verification plan

Expected verification for this PR:

- `git status --short`
- `git diff --name-only origin/main...HEAD` when `origin/main` exists in the workspace
- `git show --name-only --format='' HEAD`
- generated JSON is not staged or committed
- changed files are limited to this planning document
- `python -m unittest discover -s tests` per repository guardrails, unless explicitly waived

If `origin/main` is unavailable in the workspace, report that explicitly and require final confirmation in GitHub PR Files changed.

## 12. Rollback plan

- Revert this docs-only PR.
- Remove `docs/pr_handoffs/mark_orderbook_gap_venue_adapter_commonization_planning_2026_06_05.md`.
- No code, config, registry, generated JSON, runtime, adapter, parser, readiness, timestamp policy, OKX index semantics, Council, alert, or execution rollback is required.
