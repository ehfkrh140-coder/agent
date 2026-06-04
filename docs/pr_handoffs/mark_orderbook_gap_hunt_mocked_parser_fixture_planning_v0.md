# Mark-Orderbook Gap Hunt Mocked Parser Fixture Planning v0 Handoff

## 1. Purpose

Document mocked parser fixture groups, expected normalized outputs, failure/`NEED_DATA` cases, notional planning, and decision criteria for future `Mark-Orderbook Gap Hunt v0` parser tests.

This is a documentation/test-planning PR only. It does not implement runtime adapters, parser code, config registration, tests, sampling, alerts, notification, Council auto-call, active promotion, execution, private APIs, generated packet JSON, or generated sampling JSON.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Execution policy remains `NO_TRADE_ONLY`.
- User-local public endpoint evidence confirmed mark/orderbook/top-of-book field availability.
- User-local instrument metadata evidence confirmed core metadata field availability.
- Parser correctness, final notional formulas, fee/slippage/funding treatment, and readiness thresholds are still not implemented or proven.

## 3. Fixture group summary

### Binance

Fixture group:

- Binance mark response fixture.
- Binance depth response fixture.
- Binance `exchangeInfo` BTCUSDT metadata fixture.

Expected valid-case identifiers:

- `venue_id`: `binance`
- `instrument_id`: `BTCUSDT`
- `instrument_type`: `linear_perpetual` or equivalent planning label

### Bybit

Fixture group:

- Bybit ticker response fixture.
- Bybit orderbook response fixture.
- Bybit `instruments-info` BTCUSDT metadata fixture.

Expected valid-case identifiers:

- `venue_id`: `bybit`
- `instrument_id`: `BTCUSDT`
- `instrument_type`: `linear_perpetual`

### OKX

Fixture group:

- OKX mark-price response fixture.
- OKX books or ticker response fixture.
- OKX instruments BTC-USDT-SWAP metadata fixture.

Expected valid-case identifiers:

- `venue_id`: `okx`
- `instrument_id`: `BTC-USDT-SWAP`
- `instrument_type`: `linear_swap`

## 4. Expected normalized outputs

Future normalized parser outputs should include these planning fields when data is valid and comparable:

| Venue | Required normalized fields |
| --- | --- |
| Binance | `venue_id`, `instrument_id`, `instrument_type`, `mark_price`, `index_price`, `bid`, `ask`, `bid_size_raw`, `ask_size_raw`, `tick_size=0.10`, `quantity_step=0.001`, `min_order_size=0.001`, `min_notional=50`, `margin_asset=USDT`, `comparability_pass=true`, `required_missing_fields=[]` |
| Bybit | `venue_id`, `instrument_id`, `instrument_type`, `mark_price`, `index_price`, `bid`, `ask`, `bid_size_raw`, `ask_size_raw`, `tick_size=0.10`, `quantity_step=0.001`, `min_order_size=0.001`, `min_notional=5`, `settle_coin=USDT`, `funding_interval=480`, `comparability_pass=true`, `required_missing_fields=[]` |
| OKX | `venue_id`, `instrument_id`, `instrument_type`, `mark_price`, `bid`, `ask`, `bid_size_raw`, `ask_size_raw`, `contract_value=0.01`, `contract_multiplier=1`, `contract_value_currency=BTC`, `settle_currency=USDT`, `tick_size=0.1`, `lot_size=0.01`, `min_order_size=0.01`, `comparability_pass=true`, `required_missing_fields=[]` |

These fields are planning targets only. This PR does not add parser/schema/test/runtime code.

## 5. Failure / NEED_DATA fixture cases

Future parser tests should include at least these fixture cases:

- Missing mark response -> `NEED_DATA`.
- Missing orderbook or missing bid/ask -> `NEED_DATA`.
- Missing metadata -> `NEED_DATA`.
- Instrument mismatch, e.g. mark `BTCUSDT` but orderbook `ETHUSDT` -> `NEED_DATA`.
- Bybit category/type mismatch, e.g. ticker `linear` but orderbook `inverse` -> `NEED_DATA`.
- OKX `instId` mismatch -> `NEED_DATA`.
- Unknown size unit or missing `ctVal` / lot size -> `NEED_DATA`.
- Stale timestamp / excessive latency -> `NEED_DATA` or `REJECT` according to future readiness rules.
- Non-positive gap after fee/slippage/buffer -> `REJECT`.
- Positive mark-orderbook gap with metadata/comparability confirmed -> `WATCH` only, not execution.

Each failure fixture should expose `required_missing_fields` or equivalent diagnostics.

## 6. Notional formula planning

No notional formula is implemented here.

Planning notes:

- Binance / Bybit linear candidate: approximate planning notional may be `price * quantity` if quantity unit is confirmed as base asset amount.
- Binance / Bybit stay `NEED_DATA` until future parser fixtures explicitly confirm and document that assumption.
- OKX requires an explicit formula using `price`, `size`, `ctVal`, `ctMult`, `ctValCcy`, and `settleCcy`.
- OKX stays `NEED_DATA` until fixture rules for contract-value conversion are agreed.

## 7. Decision criteria impact

- Missing metadata -> `NEED_DATA`.
- Instrument mismatch -> `NEED_DATA`.
- Size unit unknown -> `NEED_DATA`.
- Notional formula unknown -> `NEED_DATA`.
- Data is sufficient but no positive net gap after fee/slippage/buffer -> `REJECT`.
- Positive observation with complete metadata and comparability -> `WATCH`.
- Repeated `WATCH` may become `COUNCIL_REVIEW_CANDIDATE` in a future phase, but it is still not an order instruction.
- `EXECUTION_CANDIDATE` remains forbidden.

## 8. Future execution/API note

The user direction is to defer alert/notification and execution/API work until multiple strategy decision structures are better defined. Future execution/risk work must be common/shared, not strategy-specific ad hoc order code.

Any future execution/API track requires separate task cards, credential isolation, dry-run/paper trading, a kill switch, risk limits, an order-state machine, audit logs, rollback planning, and explicit human review.

This PR does not implement that future execution track.

## 9. Changed files

- Added: `docs/parser_plans/mark_orderbook_gap_hunt_mocked_parser_fixtures_v0.md`.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_mocked_parser_fixture_planning_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `tests/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.
- No Council runtime, notification/alert runtime, Gemini runtime, or prompt changes.

## 10. Tests run

### Git status

```text
git status
```

Result: passed. The branch was `mark-orderbook-gap-mocked-parser-fixture-planning-v0`; only the two allowed documentation files were untracked before staging.

### Git diff name check

```text
git diff --name-only
```

Result: passed. No tracked-file diff was shown before staging because the two new documentation files were still untracked.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only `docs/parser_plans/mark_orderbook_gap_hunt_mocked_parser_fixtures_v0.md` and `docs/pr_handoffs/mark_orderbook_gap_hunt_mocked_parser_fixture_planning_v0.md`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed. `Ran 249 tests in 12.049s` and ended with `OK`.

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

Result: passed before staging with only the two allowed documentation files untracked and no generated packet, sampling, or Council-session artifacts present.

## 11. Risks

- Fixture planning can still encode incorrect assumptions if not reviewed against public metadata evidence.
- Notional formulas remain unimplemented and unresolved.
- Future parser tests could accidentally over-promote `WATCH` if failure cases are incomplete.
- Mark price is not executable and must not be treated as an order price.
- Future work must not promote this strategy to active automatically.

## 12. Rollback plan

- Revert `docs/parser_plans/mark_orderbook_gap_hunt_mocked_parser_fixtures_v0.md` and `docs/pr_handoffs/mark_orderbook_gap_hunt_mocked_parser_fixture_planning_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling/Council-session JSON is committed.

## 13. Human review required

Reviewers should inspect:

1. `docs/parser_plans/mark_orderbook_gap_hunt_mocked_parser_fixtures_v0.md`
2. `docs/pr_handoffs/mark_orderbook_gap_hunt_mocked_parser_fixture_planning_v0.md`
3. Prior metadata evidence: `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_instrument_metadata_evidence_v0.md`
4. Prior metadata plan: `docs/source_probes/mark_orderbook_gap_hunt_instrument_metadata_v0.md`
5. Strategy card: `docs/strategy_task_cards/mark_orderbook_gap_hunt.md`

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
- parser implementation: no
- sampling implementation: no
- live network smoke as merge requirement: no

## 15. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt Mocked Parser Tests v0` PR after this fixture plan is reviewed. That future PR may add tests/fixtures for normalized output behavior while still avoiding runtime adapter/config implementation unless explicitly approved.
