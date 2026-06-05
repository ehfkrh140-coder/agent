# Mark-Orderbook Gap Hunt Binance Runtime Adapter v0 Handoff

## 1. Purpose

Implement the first runtime market-data adapter for `Mark-Orderbook Gap Hunt v0`, constrained to Binance USDⓈ-M `BTCUSDT` public market data.

This PR adds a small public-read-only adapter class and mocked unit tests. It does not add config registration, registry integration, `collect_market_data` CLI execution, `sample_market_data` integration, sampling, alert/notification, Council auto-call, active strategy promotion, execution/private API, generated packet JSON, or generated sampling JSON.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- The parser `parse_mark_orderbook_gap_snapshot` already normalizes Binance USDⓈ-M public mark/orderbook/metadata response dictionaries.
- The readiness helper `evaluate_mark_orderbook_gap_readiness` already maps parser output to `NEED_DATA`, `REJECT`, or analysis-only `WATCH`.
- Previous planning documented the first adapter as Binance-only / BTCUSDT-only before any Bybit/OKX runtime expansion.

## 3. Adapter scope

Added `BinanceMarkOrderbookGapHuntAdapter` in `src/market_data/adapters/mark_orderbook_gap_hunt.py`.

Adapter identity:

- `adapter_id`: `live_binance_mark_orderbook_gap_btcusdt`
- `adapter_type`: `binance_mark_orderbook_gap_hunt`
- `venue_id`: `binance`
- `strategy_family`: `mark_orderbook_gap_hunt`
- `strategy_id`: `mark_orderbook_gap_hunt_v0`
- `signal_type`: `mark_orderbook_gap_hunt`
- `execution_policy`: `NO_TRADE_ONLY`
- `experimental_strategy`: `true`
- `non_active_strategy`: `true`
- `no_trade_only`: `true`

Scope exclusions:

- no Bybit runtime adapter;
- no OKX runtime adapter;
- no multi-venue composite;
- no config registration;
- no registry integration;
- no sampling integration;
- no alert/notification;
- no Council auto-call;
- no active strategy promotion;
- no execution/private API.

## 4. Public endpoint behavior

The adapter only requests these public no-key Binance USDⓈ-M paths:

- `/fapi/v1/premiumIndex?symbol=BTCUSDT`
- `/fapi/v1/depth?symbol=BTCUSDT&limit=5`
- `/fapi/v1/exchangeInfo`

Implementation notes:

- The HTTP client is injectable so unit tests can use mocked public responses.
- Metadata is filtered to the selected `BTCUSDT` symbol before parser invocation.
- The adapter records safe diagnostics for each public fetch: endpoint, params, parser stage, HTTP status, safe response preview, elapsed milliseconds, and URL when available.
- Diagnostics do not include credentials, auth headers, account state, balance state, positions, orders, withdrawal/deposit/transfer data, or private payloads.

## 5. Parser/readiness integration

The adapter:

1. fetches the three public response dictionaries;
2. builds the parser input bundle with `venue_id=binance` and `parser_mode=binance_usdm`;
3. calls `parse_mark_orderbook_gap_snapshot`;
4. calls `evaluate_mark_orderbook_gap_readiness` with explicit conservative inputs;
5. stores parser output and readiness output in packet extensions for auditability.

Boundary rules preserved:

- parser `OK` does not mean execution;
- readiness `WATCH` is analysis-only;
- `readiness_pass` remains `false` in this phase;
- the adapter does not emit `execution_allowed=true`, `council_auto_call=true`, or `alert_trigger=true`.

## 6. OpportunityPacket mapping

The adapter builds an `OpportunityPacket` directly, without using config/registry integration.

Packet-level fields:

- `asset`: `BTC`
- `quote`: `USDT`
- `signal_type`: `mark_orderbook_gap_hunt`
- `strategy_family`: `mark_orderbook_gap_hunt`
- `strategy_id`: `mark_orderbook_gap_hunt_v0`

Observation mapping includes:

- venue and market symbol;
- instrument type;
- mark price and index price;
- bid and ask;
- bid/ask size;
- timestamp;
- data quality snapshot;
- venue health snapshot;
- derivatives snapshot;
- parser and metadata fields in extensions where the core schema has no dedicated field.

Candidate mapping includes:

- `candidate_type`: `mark_orderbook_gap_observation`
- `long_gap_pct`
- `short_gap_pct`
- `gross_gap_pct` / max observed gap;
- `estimated_net_gap_pct`;
- `readiness_status` and `recommended_default_decision` in metrics;
- `liquidity_pass`, `freshness_pass`, `comparability_pass`;
- `required_missing_fields`;
- warnings in extensions;
- assumptions that mark price is not executable, `WATCH` is analysis-only, no private API is used, and there is no trading behavior.

## 7. Diagnostics

Safe diagnostics are attached to packet extensions and to raised adapter errors on public fetch failure.

Each fetch diagnostic may include:

- `endpoint`
- `params`
- `parser_stage`
- `http_status`
- `safe_response_preview`
- `elapsed_ms`
- `url`

Failure diagnostics may include:

- `error_type`
- `error_message`
- `http_status`
- `safe_response_preview`
- public exchange error code/message when exposed by the public response

Diagnostics intentionally avoid auth headers, credentials, account data, balance data, positions, orders, cancellation data, withdrawal/deposit/transfer data, fiat/bank data, and private endpoint payloads.

## 8. Tests run

### Git status

```text
git status
```

Result: passed before staging; branch `mark-orderbook-gap-binance-runtime-adapter-v0` had only the three allowed new files untracked.

### Git diff name check

```text
git diff --name-only
```

Result: passed before staging; no tracked-file diff was present because the allowed files were new/untracked before staging.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_runtime_adapter_v0.md`, `src/market_data/adapters/mark_orderbook_gap_hunt.py`, and `tests/test_mark_orderbook_gap_hunt_binance_adapter.py`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed (`Ran 293 tests in 12.688s`, `OK`).

### Production parser test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser
```

Result: passed (`Ran 8 tests in 0.007s`, `OK`).

### Readiness helper test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_readiness
```

Result: passed (`Ran 12 tests in 0.008s`, `OK`).

### Binance adapter test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter
```

Result: passed (`Ran 8 tests in 0.008s`, `OK`).

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed (`exit=0`, `2056` matching lines from existing policy/docs/test references plus this PR's explicit no-trade deferrals); no credential/private/account/balance/position/order/transfer/execution/config/registry/sampling/alert/Council implementation surface was added.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed (`exit=0`, `1414` matching lines from existing strategy/no-trade references plus this PR's `mark_orderbook_gap_hunt` adapter references); active strategy remains `cross_exchange_spot_spread_v1` and this adapter remains experimental/non-active/`NO_TRADE_ONLY`.

### Final status check

```text
git status --short
```

Result: passed after commit; working tree was clean on `mark-orderbook-gap-binance-runtime-adapter-v0` and no generated artifacts were present.

## 9. What this proves

- A Binance USDⓈ-M `BTCUSDT` runtime adapter class can fetch public response dictionaries through an injected/read-only HTTP seam.
- The adapter reuses the production parser and readiness helper instead of duplicating parser/readiness logic.
- The adapter can build an analysis-only `OpportunityPacket` with one observation and one candidate from mocked public responses.
- Safe diagnostics are preserved for successful public fetches and public fetch failures.
- Unit tests cover that `WATCH` does not create execution, Council auto-call, or alert trigger fields.

## 10. What this does not prove

- It does not register the adapter in `configs/market_data.yaml`.
- It does not integrate the adapter into `src/market_data/registry.py`.
- It does not make the adapter runnable from `tools/collect_market_data.py`.
- It does not implement sampling.
- It does not perform live network smoke in Codex.
- It does not prove Binance live endpoint availability in this workspace.
- It does not prove profitability.
- It does not promote the strategy to active.
- It does not implement alert/notification, Council auto-call, or execution/private API.

## 11. Changed files

- Added: `src/market_data/adapters/mark_orderbook_gap_hunt.py`.
- Added: `tests/test_mark_orderbook_gap_hunt_binance_adapter.py`.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_runtime_adapter_v0.md`.
- No `configs/**` changes.
- No `src/market_data/registry.py` changes.
- No `tools/**` changes.
- No `src/council/**`, `src/notifications/**`, or `src/storage/**` changes.
- No generated packet/sampling/Council-session JSON changes.

## 12. Risks

- Future PRs could accidentally register the adapter before thresholds, local smoke, and review are complete.
- Mark price is not executable; packet consumers must not treat mark price as an order price.
- `WATCH` remains analysis-only and could be misread as an actionable signal if no-trade boundaries are ignored.
- Conservative readiness inputs may classify otherwise positive-looking mocked data as `NEED_DATA` or `REJECT`, which is acceptable before full size/notional/liquidity policy review.

## 13. Rollback plan

- Revert `src/market_data/adapters/mark_orderbook_gap_hunt.py`.
- Revert `tests/test_mark_orderbook_gap_hunt_binance_adapter.py`.
- Revert `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_runtime_adapter_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm the adapter remains absent from config/registry.
- Confirm no generated packet/sampling/Council-session JSON is committed.

## 14. Human review required

Reviewers should inspect:

1. `src/market_data/adapters/mark_orderbook_gap_hunt.py`
2. `tests/test_mark_orderbook_gap_hunt_binance_adapter.py`
3. `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_runtime_adapter_v0.md`

Review focus:

- public endpoint restriction;
- parser/readiness boundary;
- OpportunityPacket mapping;
- diagnostics safety;
- absence of config/registry/sampling/alert/Council/execution integration.

## 15. No-trade compliance

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
- config adapter registration: no
- registry integration: no
- sampling implementation: no
- live network smoke as merge requirement: no

## 16. Next recommended step

After human review, open a separate `Mark-Orderbook Gap Hunt Binance Adapter Config/Registry Planning v0` or user-local smoke evidence task before any config/registry registration. Keep that follow-up public-read-only, `NO_TRADE_ONLY`, and separate from sampling, alert/notification, Council auto-call, active promotion, and execution/private API work.
