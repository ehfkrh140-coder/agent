# Mark-Orderbook Gap Hunt Bybit Runtime Adapter v0

## 1. Purpose

Add a single Bybit Derivatives V5 linear `BTCUSDT` Mark-Orderbook Gap Hunt runtime adapter class for analysis-only public market-data collection.

This PR implements only the standalone adapter class and mocked unit coverage. It does not register the adapter in config/registry, does not wire it into `collect_market_data`, does not add sampling integration, does not require live network smoke, and does not add alert, Council auto-call, active promotion, execution, private API, credentials, account/balance/position lookup, orders, cancellations, withdrawals, deposits, or transfers.

## 2. Baseline

- Binance single-venue baseline is already implemented and has collect, 3-sample sampling, and 30-sample extended sampling evidence.
- Bybit runtime adapter planning documented the future `live_bybit_mark_orderbook_gap_btcusdt` scope, public endpoints, parser bundle, readiness flow, OpportunityPacket mapping, and commonization candidates.
- Existing parser supports `parser_mode="bybit_linear"`.
- Existing readiness helper can evaluate parser output without network, credentials, alerts, Council, or execution behavior.
- Mark-Orderbook Gap Hunt remains experimental / non-active / `NO_TRADE_ONLY`.
- Current active strategy remains `cross_exchange_spot_spread_v1`.

## 3. Adapter scope

Implemented class:

- Class: `BybitMarkOrderbookGapHuntAdapter`
- Default adapter id: `live_bybit_mark_orderbook_gap_btcusdt`
- Adapter type: `bybit_mark_orderbook_gap_hunt`
- Venue id: `bybit`
- Venue name: `Bybit Derivatives V5`
- Category: `linear`
- Symbol: `BTCUSDT`
- Asset: `BTC`
- Quote: `USDT`
- Strategy family: `mark_orderbook_gap_hunt`
- Strategy id: `mark_orderbook_gap_hunt_v0`
- Signal type: `mark_orderbook_gap_hunt`
- Execution policy: `NO_TRADE_ONLY`
- Experimental strategy: `true`
- Non-active strategy: `true`
- No-trade-only: `true`

Out of scope in this PR:

- Bybit config adapter registration.
- Bybit registry integration.
- `collect_market_data` CLI wiring.
- Sampling implementation changes.
- OKX adapter implementation.
- Multi-venue composite implementation.
- Generic/base adapter extraction.

## 4. Public endpoint behavior

The adapter uses only public Bybit V5 market-data endpoint paths:

- `/v5/market/tickers` with params `category=linear&symbol=BTCUSDT`
- `/v5/market/orderbook` with params `category=linear&symbol=BTCUSDT&limit=5`
- `/v5/market/instruments-info` with params `category=linear&symbol=BTCUSDT`

The adapter accepts an injected HTTP client so tests can use mocked public responses and avoid live network calls.

The adapter does not send credentials, auth headers, account context, balance requests, position requests, order requests, cancellation requests, withdrawal/deposit requests, or transfer requests.

## 5. Parser/readiness integration

The adapter fetches mocked/future public Bybit ticker, orderbook, and metadata responses, then calls:

- `parse_mark_orderbook_gap_snapshot` with `parser_mode="bybit_linear"`
- `evaluate_mark_orderbook_gap_readiness` with explicit conservative config parameters

Parser/readiness semantics preserved:

- Parser `OK` does not mean `WATCH`.
- `NEED_DATA` remains valid for missing data, unresolved metadata, freshness, comparability, liquidity, or size/notional requirements.
- `REJECT` can be normal no-edge behavior.
- `WATCH` remains analysis-only.
- `readiness_pass` remains false under the current readiness helper policy.
- The adapter does not add `execution_allowed`, `council_auto_call`, or `alert_trigger` fields.

## 6. OpportunityPacket mapping

The adapter builds an analysis-only `OpportunityPacket` with:

- `strategy_family=mark_orderbook_gap_hunt`
- `strategy_id=mark_orderbook_gap_hunt_v0`
- `asset=BTC`
- `quote=USDT`
- `signal_type=mark_orderbook_gap_hunt`

Observation mapping includes:

- `venue_id=bybit`
- `venue_name=Bybit Derivatives V5`
- `market_symbol=BTCUSDT`
- `instrument_type=linear_perpetual`
- `mark_price`
- `index_price`
- `bid`
- `ask`
- `bid_size`
- `ask_size`
- timestamp/data-quality/venue-health fields
- derivative fields such as funding rate, next funding time, mark price, and index price
- Bybit-specific metadata such as category, settlement currency, min order size, min notional, parser mode, and parser normalized status under extensions

Candidate mapping includes:

- `candidate_type=mark_orderbook_gap_observation`
- `long_gap_pct`
- `short_gap_pct`
- `gross_gap_pct` / `max_observed_gap_pct`
- `estimated_net_gap_pct`
- `readiness_status`
- `recommended_default_decision`
- `liquidity_pass`
- `freshness_pass`
- `comparability_pass`
- `required_missing_fields`
- warnings under extensions
- assumptions that mark price is not executable, WATCH is analysis-only, no private API, and no trading behavior

## 7. Diagnostics

Diagnostics include safe public-fetch details:

- endpoint
- params
- parser stage
- HTTP status if available
- safe response preview if available
- elapsed milliseconds if available
- URL if available
- Bybit `retCode` if available
- Bybit `retMsg` if available

Bybit `retCode != 0` raises `MarketDataAdapterError` with attached diagnostics. Unit tests verify these diagnostics remain safe and do not include credential/auth strings.

## 8. Commonization notes

This PR intentionally does not extract a generic/base adapter.

Some implementation structure duplicates the Binance Mark-Orderbook Gap adapter:

- injected HTTP client seam
- public fetch diagnostics
- parser/readiness invocation
- OpportunityPacket identity/candidate mapping
- `NO_TRADE_ONLY` adapter metadata
- assumptions and warnings
- no config/registry/sampling integration assumptions

This duplication is acceptable for a small first Bybit implementation. After Binance + Bybit + possibly OKX are reviewed, a future `Mark-Orderbook Gap Hunt Venue Adapter Base Planning v0` can compare real duplication and decide whether shared helpers should be extracted.

## 9. Tests run

- `git status` — completed before/after changes.
- `git diff --name-only` — completed before commit and showed only allowed changed-file scope.
- `python -m unittest discover -s tests` — passed; ran 309 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — passed; ran 10 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed; ran 9 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed; ran 8 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed; ran 12 tests.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed; ran 5 tests.
- `python tools/collect_market_data.py --list-adapters` — passed; existing adapter list command completed.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed; matches were expected docs/tests/policy references and no private/runtime credential surface was added.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed; matches were expected strategy/no-trade references.
- `git status --short` — completed before commit.

## 10. What this proves

- A standalone Bybit Derivatives V5 linear `BTCUSDT` Mark-Orderbook Gap Hunt adapter class exists.
- The adapter can consume mocked public Bybit ticker/orderbook/metadata responses.
- The adapter reuses the existing `bybit_linear` parser path and shared readiness helper.
- The adapter can build one analysis-only OpportunityPacket observation and one candidate from mocked public data.
- Bybit public fetch diagnostics are captured safely, including `retCode` / `retMsg`.
- `NO_TRADE_ONLY` metadata is preserved.
- The adapter is not registered in config/registry in this PR.

## 11. What this does not prove

- It does not prove live Bybit endpoint reachability.
- It does not prove Bybit config/registry registration.
- It does not prove `collect_market_data` execution for the Bybit adapter.
- It does not prove Bybit sampling integration.
- It does not prove profitability.
- It does not prove persistent edge.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not prove OKX or multi-venue composite behavior.
- It does not prove a generic/base adapter should be extracted now.

## 12. Changed files

- `src/market_data/adapters/mark_orderbook_gap_hunt.py`
- `tests/test_mark_orderbook_gap_hunt_bybit_adapter.py`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_bybit_runtime_adapter_v0.md`

No `configs/**`, `src/market_data/registry.py`, `tools/**`, generated data, Council, notifications, storage, or Gemini runtime/prompt files are changed.

## 13. Risks

- Bybit live public response edge cases may differ from mocked fixtures and require user-local smoke after future registration.
- Bybit size/notional/liquidity semantics require continued review of `lotSizeFilter`, `priceFilter`, and instrument units.
- The adapter duplicates some Binance packet-building structure; future base extraction should wait for more venue evidence.
- Since config/registry are intentionally unchanged, the adapter cannot be run via `collect_market_data` until a separate registration PR.

## 14. Rollback plan

Revert this PR or remove the Bybit adapter class, Bybit adapter unit test file, and this handoff document. No config/registry/tool/generated-data rollback is required because those files are not changed.

## 15. Human review required

Human review should first inspect:

- `src/market_data/adapters/mark_orderbook_gap_hunt.py`
- `tests/test_mark_orderbook_gap_hunt_bybit_adapter.py`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_bybit_runtime_adapter_v0.md`

Review focus:

- Confirm only public Bybit V5 market endpoint paths are used.
- Confirm the adapter calls the shared parser/readiness helpers instead of duplicating strategy logic.
- Confirm OpportunityPacket mapping and metadata remain analysis-only / `NO_TRADE_ONLY`.
- Confirm no config registration, registry integration, CLI wiring, sampling implementation, generated artifacts, alert, Council, active promotion, execution, or private API behavior was added.

## 16. No-trade compliance

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
- Bybit config adapter registration: no
- Bybit registry integration: no
- sampling implementation: no
- live network smoke as merge requirement: no
- OKX adapter implementation: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no

## 17. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt Bybit Adapter Config/Registry Planning v0` or direct config/registry planning PR after human review of the standalone Bybit adapter implementation and mocked tests.
