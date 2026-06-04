# Mark-Orderbook Gap Hunt Mocked Parser Tests v0 Handoff

## 1. Purpose

Add mocked/synthetic fixture tests for the future `Mark-Orderbook Gap Hunt v0` parser before any production parser, runtime adapter, config registration, sampling, alert, Council auto-call, active promotion, or execution work is implemented.

The tests freeze expected fixture shapes and expected normalized planning outputs for Binance, Bybit, and OKX valid same-instrument cases, plus failure / `NEED_DATA` decision cases.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Execution policy remains `NO_TRADE_ONLY`.
- Prior user-local endpoint evidence confirmed public mark/orderbook/top-of-book field availability.
- Prior user-local metadata evidence confirmed public instrument metadata field availability.
- Parser correctness, final notional formulas, fee/slippage/funding treatment, and readiness thresholds are still not implemented in production code.

## 3. Fixture files

Added fixture files:

1. `tests/fixtures/mark_orderbook_gap_hunt/binance_valid_btcusdt.json`
2. `tests/fixtures/mark_orderbook_gap_hunt/bybit_valid_btcusdt_linear.json`
3. `tests/fixtures/mark_orderbook_gap_hunt/okx_valid_btc_usdt_swap.json`
4. `tests/fixtures/mark_orderbook_gap_hunt/failure_cases.json`

The fixtures are mocked/synthetic public examples. They do not contain private API data, credentials, account data, balances, live orders, withdrawals, deposits, transfers, generated packets, generated sampling summaries, or Council sessions.

## 4. Valid fixture tests

Added `tests/test_mark_orderbook_gap_hunt_parser_fixtures.py` with small in-test helper functions only. No production parser module was added.

Valid fixture coverage:

- Binance valid BTCUSDT fixture includes mark response, depth response, and `exchangeInfo` metadata; expected normalized planning output pins `venue_id=binance`, `instrument_id=BTCUSDT`, `instrument_type=linear_perpetual`, mark/index/bid/ask, raw sizes, `tick_size=0.10`, `quantity_step=0.001`, `min_order_size=0.001`, `min_notional=50`, `margin_asset=USDT`, `comparability_pass=true`, and `required_missing_fields=[]`.
- Bybit valid BTCUSDT linear fixture includes ticker response, orderbook response, and `instruments-info` metadata; expected normalized planning output pins `venue_id=bybit`, `instrument_id=BTCUSDT`, `instrument_type=linear_perpetual`, mark/index/bid/ask, raw sizes, `tick_size=0.10`, `quantity_step=0.001`, `min_order_size=0.001`, `min_notional=5`, `settle_coin=USDT`, `funding_interval=480`, `comparability_pass=true`, and `required_missing_fields=[]`.
- OKX valid BTC-USDT-SWAP fixture includes mark-price response, books response, and instruments metadata; expected normalized planning output pins `venue_id=okx`, `instrument_id=BTC-USDT-SWAP`, `instrument_type=linear_swap`, mark/bid/ask, raw sizes, `contract_value=0.01`, `contract_multiplier=1`, `contract_value_currency=BTC`, `settle_currency=USDT`, `tick_size=0.1`, `lot_size=0.01`, `min_order_size=0.01`, `comparability_pass=true`, and `required_missing_fields=[]`.

## 5. Failure / NEED_DATA tests

The failure fixture test pins these expected outcomes:

- missing mark response -> `NEED_DATA`.
- missing orderbook or bid/ask -> `NEED_DATA`.
- missing metadata -> `NEED_DATA`.
- instrument mismatch, e.g. mark `BTCUSDT` but orderbook `ETHUSDT` -> `NEED_DATA`.
- Bybit category/type mismatch, e.g. ticker `linear` but orderbook `inverse` -> `NEED_DATA`.
- OKX `instId` mismatch -> `NEED_DATA`.
- unknown size unit / missing `ctVal` or lot size -> `NEED_DATA`.
- stale timestamp / excessive latency -> `NEED_DATA` for this fixture baseline; future readiness may choose `REJECT` after thresholds are defined.
- non-positive gap after fee/slippage/buffer -> `REJECT`.
- positive mark-orderbook gap with metadata/comparability confirmed -> `WATCH` only, not execution.

## 6. Decision criteria assertions

The tests assert that:

- valid same-instrument fixtures normalize to the expected planning output;
- valid fixtures keep `required_missing_fields=[]`;
- failure fixtures expose `required_missing_fields` or equivalent diagnostics;
- `WATCH` never implies execution;
- `WATCH` never implies Council auto-call;
- fixtures contain no private/auth/account/balance/transfer material.

## 7. What this proves

- The future parser has a stable mocked fixture baseline for Binance, Bybit, and OKX valid same-instrument planning cases.
- Failure / `NEED_DATA` cases are explicitly pinned before production parser implementation.
- The repository can run these tests without live network access, API keys, environment variables, or generated JSON artifacts.
- `WATCH` is explicitly treated as analysis-only, not execution or Council auto-call.

## 8. What this does not prove

- It does not prove runtime parser correctness because no production parser was implemented.
- It does not prove live endpoint behavior.
- It does not prove final notional formula correctness.
- It does not finalize fee/slippage/funding treatment.
- It does not justify runtime adapter implementation.
- It does not justify config registration.
- It does not justify sampling, alert/notification, Council auto-call, active strategy promotion, or execution/private API work.

## 9. Changed files

- Added: `tests/fixtures/mark_orderbook_gap_hunt/binance_valid_btcusdt.json`.
- Added: `tests/fixtures/mark_orderbook_gap_hunt/bybit_valid_btcusdt_linear.json`.
- Added: `tests/fixtures/mark_orderbook_gap_hunt/okx_valid_btc_usdt_swap.json`.
- Added: `tests/fixtures/mark_orderbook_gap_hunt/failure_cases.json`.
- Added: `tests/test_mark_orderbook_gap_hunt_parser_fixtures.py`.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_mocked_parser_tests_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.
- No Council runtime, notification/alert runtime, Gemini runtime, or prompt changes.

## 10. Tests run

### Git status

```text
git status
```

Result: passed. The branch was `mark-orderbook-gap-mocked-parser-tests-v0`; only the allowed test fixture, test, and handoff files were untracked before staging.

### Git diff name check

```text
git diff --name-only
```

Result: passed. No tracked-file diff was shown before staging because the new files were still untracked.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only the six allowed files listed in `Changed files`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed. `Ran 255 tests in 12.115s` and ended with `OK`.

### Targeted mocked parser fixture test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser_fixtures
```

Result: passed. `Ran 6 tests in 0.003s` and ended with `OK`.

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed. The scan returned existing documentation/test/runtime references plus this PR's explicit no-trade deferrals; this PR added no runtime, config, credential, private API, account/balance, order/cancel, withdrawal/deposit/transfer, or execution surface.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed. Existing references still identify `cross_exchange_spot_spread_v1` as active and keep `mark_orderbook_gap_hunt_v0` proposed/inactive/NO_TRADE_ONLY.

### Final status check

```text
git status --short
```

Result: passed before staging with only allowed files untracked and no generated packet, sampling, or Council-session artifacts present.

## 11. Risks

- The test helper functions are intentionally in-test planning helpers, not production parser code.
- Future parser implementation may need refined field names or notional formulas after human review.
- Incorrect fixture assumptions could create false confidence if not checked against user-local evidence.
- Mark price is not executable and must not be treated as an order price.
- Future work must not promote this strategy to active automatically.

## 12. Rollback plan

- Revert the new fixture files, `tests/test_mark_orderbook_gap_hunt_parser_fixtures.py`, and `docs/pr_handoffs/mark_orderbook_gap_hunt_mocked_parser_tests_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling/Council-session JSON is committed.

## 13. Human review required

Reviewers should inspect:

1. `tests/test_mark_orderbook_gap_hunt_parser_fixtures.py`
2. `tests/fixtures/mark_orderbook_gap_hunt/binance_valid_btcusdt.json`
3. `tests/fixtures/mark_orderbook_gap_hunt/bybit_valid_btcusdt_linear.json`
4. `tests/fixtures/mark_orderbook_gap_hunt/okx_valid_btc_usdt_swap.json`
5. `tests/fixtures/mark_orderbook_gap_hunt/failure_cases.json`
6. `docs/pr_handoffs/mark_orderbook_gap_hunt_mocked_parser_tests_v0.md`

## 14. No-trade compliance

- private API: no
- API key/secret/token: no
- auth/private headers: no
- account/balance lookup: no
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
- runtime adapter implementation: no
- config adapter registration: no
- production parser implementation: no
- sampling implementation: no
- live network smoke as merge requirement: no

## 15. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt Parser Contract v0` or `Mark-Orderbook Gap Hunt Production Parser v0` planning PR only after this mocked fixture baseline is reviewed. Runtime adapter/config registration should remain out of scope unless explicitly approved later.
