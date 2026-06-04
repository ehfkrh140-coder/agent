# Mark-Orderbook Gap Hunt Bybit Runtime Adapter Planning v0

## 1. Purpose

Document the planned scope for a future Bybit linear BTCUSDT Mark-Orderbook Gap Hunt runtime adapter before implementation.

This PR is planning-only. It does not implement a Bybit adapter, does not register a Bybit adapter in config/registry, does not change sampling logic, and does not add alerts, Council auto-call, active promotion, execution, private API, credentials, or generated artifacts.

## 2. Baseline

- Binance single-venue Mark-Orderbook Gap Hunt is already the first baseline for this strategy family.
- User-local Binance collect smoke proved the official collect path can generate an analysis-only OpportunityPacket.
- User-local Binance 3-sample sampling smoke proved short live sampling can run through `tools/sample_market_data.py`.
- User-local Binance 30-sample extended sampling evidence reported `samples_ok=30`, `samples_error=0`, `candidate_seen_count=30`, `positive_gross_gap_count=26`, `positive_net_gap_count=0`, `REJECT=30`, `NO_PERSISTENT_EDGE`, and `council_recommended=False`.
- The Binance evidence is stability evidence only; it does not prove profitability or persistent edge.
- Existing parser/readiness logic should remain shared across venues where possible.
- Current active strategy remains `cross_exchange_spot_spread_v1`; Mark-Orderbook Gap Hunt remains experimental, non-active, and `NO_TRADE_ONLY`.

## 3. Bybit adapter v0 scope

Future proposed adapter identity:

- Proposed adapter id: `live_bybit_mark_orderbook_gap_btcusdt`
- Venue: Bybit Derivatives V5
- Category: `linear`
- Instrument: `BTCUSDT`
- Strategy: `mark_orderbook_gap_hunt_v0`
- Strategy family: `mark_orderbook_gap_hunt`
- Signal type: `mark_orderbook_gap_hunt`
- Status: experimental / non-active / `NO_TRADE_ONLY`
- Purpose: collect public Bybit linear ticker, orderbook, and instruments-info data and use the existing parser/readiness helper to produce an analysis-only OpportunityPacket.

This planning PR intentionally does not add implementation, config registration, registry mapping, sampling integration, live-network smoke requirements, multi-venue composite behavior, alerting, Council auto-call, or execution/private API behavior.

## 4. Public endpoints

Future Bybit adapter should use only public no-key Bybit V5 market endpoints:

- Ticker / mark / top-of-book:
  - `GET https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT`
- Orderbook:
  - `GET https://api.bybit.com/v5/market/orderbook?category=linear&symbol=BTCUSDT&limit=5`
- Metadata:
  - `GET https://api.bybit.com/v5/market/instruments-info?category=linear&symbol=BTCUSDT`

Endpoint constraints:

- All endpoints are public no-key market-data endpoints.
- Do not call private/auth endpoints.
- Do not send API keys, secret tokens, auth headers, account identifiers, balance requests, position requests, order requests, cancellation requests, withdrawal/deposit requests, or transfer requests.
- Diagnostics may include public endpoint, safe params, parser/fetch stage, HTTP status if available, safe response preview if available, and Bybit public error fields such as `retCode` / `retMsg`.

## 5. Parser input bundle

Future adapter should build a parser-compatible input bundle:

- `venue_id`: `bybit`
- `parser_mode`: `bybit_linear`
- `ticker_response`: raw public ticker response
- `orderbook_response`: raw public orderbook response
- `metadata_response`: raw public instruments-info response for `BTCUSDT`
- `mark_response`: `ticker_response` or `None`, depending on the final parser contract usage
- `collected_at_utc`: adapter collection timestamp
- `latency_ms`: total/per-stage public fetch latency summary
- `max_data_age_ms`: future config-driven analysis threshold

The future adapter should preserve the pure parser/readiness boundary and should not perform network calls inside parser/readiness helpers.

## 6. Parser/readiness flow

Future flow:

1. Adapter fetches public ticker, orderbook, and metadata responses.
2. Adapter records safe diagnostics for public fetch stages.
3. Adapter calls `parse_mark_orderbook_gap_snapshot` with `parser_mode="bybit_linear"`.
4. Adapter calls `evaluate_mark_orderbook_gap_readiness` with explicit conservative, config-driven parameters.
5. Adapter maps parser/readiness output into an analysis-only OpportunityPacket.

Required semantics:

- Parser `OK` does not mean `WATCH`.
- `WATCH` remains analysis-only.
- `REJECT` can be normal no-edge behavior.
- `NEED_DATA` can represent missing metadata, unresolved size/notional, freshness, comparability, or liquidity requirements.
- Do not include `execution_allowed=true`.
- Do not include `council_auto_call=true`.
- Do not include `alert_trigger=true`.
- Keep `NO_TRADE_ONLY` metadata explicit.

## 7. OpportunityPacket mapping

Future packet identity should include:

- `strategy_family`: `mark_orderbook_gap_hunt`
- `strategy_id`: `mark_orderbook_gap_hunt_v0`
- `signal_type`: `mark_orderbook_gap_hunt`
- `asset`: `BTC`
- `quote`: `USDT`
- `execution_policy`: `NO_TRADE_ONLY`
- `experimental_strategy`: `true`
- `non_active_strategy`: `true`
- `no_trade_only`: `true`

Future observation should include or expose in extensions:

- `venue_id`: `bybit`
- `market_symbol` / `instrument_id`: `BTCUSDT`
- `instrument_type`: `linear_perpetual`
- `mark_price`
- `index_price`
- `bid`
- `ask`
- `bid_size`
- `ask_size`
- `timestamp`
- `data_quality`
- `health`
- derivatives metadata when the schema supports it or under `extensions`

Future candidate should include:

- `candidate_type`: `mark_orderbook_gap_observation`
- `long_gap_pct`
- `short_gap_pct`
- `max_observed_gap_pct`
- `estimated_net_gap_pct`
- `readiness_status`
- `recommended_default_decision`
- `liquidity_pass`
- `freshness_pass`
- `comparability_pass`
- `required_missing_fields`
- `warnings`
- `assumptions`:
  - mark price is not executable
  - WATCH is analysis-only
  - no private API
  - no trading behavior

## 8. Binance vs Bybit commonization analysis

Common/reusable candidates:

- Public fetch diagnostics shape.
- Parser/readiness invocation pattern.
- OpportunityPacket identity and candidate mapping.
- `NO_TRADE_ONLY`, `experimental_strategy`, `non_active_strategy`, and `no_trade_only` metadata.
- Assumptions/warnings for mark price non-executability and analysis-only WATCH.
- Sampling interpretation for `NEED_DATA`, `REJECT`, `WATCH`, positive gross gap, positive net gap, and `NO_PERSISTENT_EDGE`.
- Generated artifact handling for collect/sampling smoke outputs.

Bybit-specific pieces:

- `base_url`: `https://api.bybit.com`
- Endpoint paths: `/v5/market/tickers`, `/v5/market/orderbook`, `/v5/market/instruments-info`
- Required query parameter `category=linear`
- Bybit V5 response shape under `retCode`, `retMsg`, `result`, and `time`
- Timestamp fields such as public response `time`, orderbook `ts`, and `cts`
- Symbol matching for `BTCUSDT`
- Metadata mapping for `priceFilter` and `lotSizeFilter`
- Funding fields such as `fundingRate` and `nextFundingTime`
- Bybit-specific safe diagnostics for non-zero `retCode` or missing result rows

## 9. Future base adapter extraction candidates

Do not extract a generic/base adapter in this PR.

After Binance and Bybit implementations both exist, compare real duplication before commonizing. A possible follow-up planning task is:

`Mark-Orderbook Gap Hunt Venue Adapter Base Planning v0`

Candidate shared helper responsibilities:

- Safe public fetch with diagnostics.
- Parser/readiness dispatch.
- OpportunityPacket construction.
- Adapter metadata generation.
- No-trade assertions.
- Diagnostics sanitization.
- Shared assumptions and warnings.

## 10. User-local smoke plan

Future collect smoke after implementation and registration:

```bash
python tools/collect_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --output data/generated_packets/live_bybit_mark_orderbook_gap_btcusdt.json
```

Later sampling smoke:

```bash
python tools/sample_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_bybit_sampling_summary.json
```

Smoke handling rules:

- Codex workspace may fail live public network checks due to tunnel/public endpoint restrictions.
- Live smoke should be user-local follow-up evidence, not a Codex merge requirement.
- Generated packet JSON and generated sampling JSON must not be committed.
- `NEED_DATA`, `REJECT`, or `WATCH` may all be valid depending on public data and analysis thresholds.
- `REJECT` is not automatically an API failure.
- `WATCH` is analysis-only and must not trigger alert, Council, or execution behavior.

## 11. Future deferrals

Deferred work:

- Bybit runtime adapter implementation is a separate next PR.
- Bybit config/registry registration should happen after implementation tests pass.
- Bybit user-local collect smoke evidence should be separate.
- Bybit sampling baseline/evidence should be separate.
- OKX expansion is later.
- Multi-venue composite is later.
- Alert/notification common layer is later.
- Council auto-call is later and requires explicit review.
- Execution/private API is much later through a common execution/risk engine, not this strategy adapter planning path.

## 12. Tests run

- `git status` — completed before/after changes; final status only included the two allowed docs files before commit.
- `git diff --name-only` — completed before commit and showed only the two allowed docs files.
- `python -m unittest discover -s tests` — passed; ran 299 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed; ran 5 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed; ran 9 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed; ran 8 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed; ran 12 tests.
- `python tools/collect_market_data.py --list-adapters` — passed; adapter list command completed.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed; matches were expected docs/tests/policy references and no new runtime/private surface was added by this docs-only PR.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed; matches were expected strategy/no-trade references.
- `git status --short` — completed before commit and showed only the two allowed docs files.

## 13. What this proves

- The Bybit adapter scope is documented before implementation.
- Public Bybit endpoint candidates are identified as public no-key market-data sources.
- The future adapter should reuse the existing `bybit_linear` parser mode and shared readiness helper.
- OpportunityPacket mapping is planned consistently with the Binance baseline.
- Commonization candidates are documented without prematurely extracting a base adapter.
- No-trade boundaries and future deferrals are explicit.

## 14. What this does not prove

- It does not prove a Bybit runtime adapter exists.
- It does not prove Bybit config/registry registration.
- It does not prove Bybit collect or sampling smoke success.
- It does not prove live Bybit public endpoints are reachable from Codex workspace.
- It does not prove profitability.
- It does not prove persistent edge.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not prove OKX or multi-venue composite behavior.

## 15. Changed files

- `docs/adapter_plans/mark_orderbook_gap_hunt_bybit_runtime_adapter_v0.md`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_bybit_runtime_adapter_planning_v0.md`

No `src/**`, `configs/**`, `tests/**`, `tools/**`, generated data, Council, notifications, storage, or Gemini runtime/prompt files are changed.

## 16. Risks

- Bybit V5 response fields and edge cases may differ from the planning assumptions and must be validated with mocked fixtures before implementation.
- Size/notional and liquidity interpretation may still require careful review of `lotSizeFilter`, contract units, tick size, and quantity semantics.
- Public endpoint availability in Codex workspace may differ from user-local normal network behavior.
- Premature commonization could obscure venue-specific failure handling; base extraction should wait until Binance and Bybit implementations can be compared.

## 17. Rollback plan

Revert this docs-only PR or delete the two added planning/handoff documents. No runtime/config/test rollback is required because no runtime/config/test files are changed.

## 18. Human review required

Human review should first inspect:

- `docs/adapter_plans/mark_orderbook_gap_hunt_bybit_runtime_adapter_v0.md`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_bybit_runtime_adapter_planning_v0.md`

Review focus:

- Confirm the Bybit endpoint plan is correct and public no-key only.
- Confirm Bybit-specific fields are sufficiently separated from shared Mark-Orderbook Gap Hunt logic.
- Confirm no implementation, config registration, registry integration, sampling change, generated artifact, alert, Council, active promotion, execution, or private API scope was added.
- Confirm the next PR should be `Mark-Orderbook Gap Hunt Bybit Runtime Adapter v0`.

## 19. No-trade compliance

- private API: no
- API key/secret/token: no
- env credential lookup: no
- auth/private headers: no
- account/balance lookup: no
- position lookup: no
- order/cancel: no
- withdrawal/deposit/transfer: no
- fiat/bank transfer: no
- auto-trading: no
- Council auto-call: no
- Council decision to trade conversion: no
- active strategy promotion: no
- alert expansion: no
- notification expansion: no
- generated packet JSON commit: no
- generated sampling JSON commit: no
- Bybit runtime adapter implementation: no
- Bybit config adapter registration: no
- Bybit registry integration: no
- sampling implementation changes: no
- live network smoke as merge requirement: no
- multi-venue composite implementation: no

## 20. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt Bybit Runtime Adapter v0` implementation PR using mocked public Bybit responses first, reusing the existing parser/readiness helper, and preserving `NO_TRADE_ONLY` without config/registry promotion until a later registration PR.
