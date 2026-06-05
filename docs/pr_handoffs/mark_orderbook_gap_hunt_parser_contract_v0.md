# Mark-Orderbook Gap Hunt Parser Contract v0 Handoff

## 1. Purpose

Document the future `Mark-Orderbook Gap Hunt v0` production parser interface / contract before implementing parser code.

This PR is planning-only. It does not add production parser implementation, runtime adapter implementation, config registration, sampling, alert/notification, Council auto-call, active strategy promotion, execution, private API, credentials, account/balance lookup, order/cancel, withdrawal/deposit/transfer, generated packet JSON, or generated sampling JSON.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Execution policy remains `NO_TRADE_ONLY`.
- Prior public endpoint and metadata evidence confirmed user-local reachability and response field availability.
- Prior mocked parser fixture tests pinned valid Binance / Bybit / OKX planning outputs and failure / `NEED_DATA` / `REJECT` / `WATCH` cases.
- Parser correctness, final notional formulas, fee/slippage/funding treatment, readiness thresholds, runtime adapter behavior, config registration, and sampling behavior remain future work.

## 3. Parser input contract

The parser contract document defines one input bundle per venue/instrument observation.

Required input fields:

- `venue_id`
- `parser_mode`
- `raw_mark_or_ticker_response`
- `raw_orderbook_or_top_of_book_response`
- `raw_instrument_metadata_response`
- `collected_at_utc`
- `latency_ms`
- `max_data_age_ms`

Initial planned parser modes:

- `binance_usdm`
- `bybit_linear`
- `okx_swap`

The input contract is public-read-only and must not include credentials, auth headers, private endpoint payloads, account state, balances, orders, withdrawals, deposits, transfers, or fiat/bank data.

## 4. Parser output contract

The parser contract defines normalized output fields for future implementation:

- identity/price: `venue_id`, `instrument_id`, `instrument_type`, `mark_price`, `index_price`, `bid`, `ask`, `bid_size_raw`, `ask_size_raw`, `bid_size_unit`, `ask_size_unit`;
- metadata/sizing: `tick_size`, `quantity_step`, `lot_size`, `min_order_size`, `min_notional`, `contract_value`, `contract_multiplier`, `contract_value_currency`, `settle_currency`, `margin_asset`;
- funding/timing: `funding_rate`, `next_funding_time`, `timestamp`, `data_age_ms`;
- quality/status: `comparability_pass`, `freshness_pass`, `required_missing_fields`, `parser_warnings`, `normalized_status` with `OK`, `NEED_DATA`, or `REJECT`.

Planning gap fields may be included only when enough data exists. `estimated_net_gap_pct` should remain `null` or readiness-owned until fee/slippage/buffer assumptions are defined.

## 5. Parser responsibilities

Parser should:

- parse fields from raw public mark/ticker, orderbook/top-of-book, and metadata responses;
- verify same instrument / same category / same `instId`;
- normalize decimal numeric fields safely;
- identify missing fields through `required_missing_fields`;
- identify unknown size unit or notional formula;
- compute planning gaps only when enough comparable data exists;
- return `NEED_DATA` contract output for expected missing-data cases instead of raising.

Parser should not:

- call live network;
- read API keys, secrets, tokens, or auth headers;
- access private endpoints;
- decide execution;
- trigger Council;
- trigger alerts/notifications;
- write generated artifacts;
- place or cancel orders;
- check account/balance state;
- create withdrawal/deposit/transfer/fiat flows.

## 6. Readiness responsibilities

Readiness should consume parser output and apply strategy-level decision logic:

- map insufficient parser data to `NEED_DATA`;
- apply persistence rules;
- apply fee/slippage/buffer assumptions;
- apply liquidity thresholds;
- apply freshness and latency thresholds;
- classify sufficient-but-not-profitable observations as `REJECT`;
- classify positive-but-not-automated observations as `WATCH`;
- classify repeated high-quality `WATCH` evidence as `COUNCIL_REVIEW_CANDIDATE` only when future criteria are defined;
- keep `WATCH` and `COUNCIL_REVIEW_CANDIDATE` analysis-only and non-execution.

## 7. Error handling contract

Documented future behavior:

- malformed JSON or malformed raw payload -> parser error in future tests;
- missing mark/ticker -> `NEED_DATA`;
- missing orderbook/top-of-book or bid/ask -> `NEED_DATA`;
- missing metadata -> `NEED_DATA`;
- instrument/category/`instId` mismatch -> `NEED_DATA`;
- unknown size unit or notional-critical metadata -> `NEED_DATA`;
- stale timestamp / excessive latency -> `NEED_DATA` or `REJECT`; final rule TBD;
- non-positive net gap after fee/slippage/buffer -> likely readiness `REJECT`;
- positive mark-orderbook gap with complete metadata -> parser `OK`, readiness `WATCH` only;
- unexpected code bug -> exception.

## 8. Test mapping

Current mocked fixture tests should map to future parser contract tests as follows:

- valid Binance fixture -> parser `OK` same-instrument case;
- valid Bybit fixture -> parser `OK` same-category and same-symbol case;
- valid OKX fixture -> parser `OK` same-`instId` case;
- missing mark/orderbook/metadata -> `NEED_DATA` tests;
- instrument/category/`instId` mismatch -> `NEED_DATA` tests;
- unknown size unit / missing `ctVal` or lot size -> `NEED_DATA` test;
- stale timestamp / excessive latency -> `NEED_DATA` or `REJECT` after readiness threshold rule is finalized;
- non-positive gap -> readiness `REJECT` test;
- positive complete-data observation -> readiness `WATCH` test, not execution;
- no fixture should imply `execution_allowed=true`;
- no fixture should require live network or credentials.

## 9. Future execution/API note

The user's longer-term direction includes a future common/shared execution/risk engine only after multiple strategies have well-defined decision structures.

That future execution/API layer must not be strategy-specific ad hoc order code. It requires a separate task card, credential isolation, dry-run/paper trading, kill switch, risk limits, order-state machine, audit logs, rollback plan, and explicit human review.

This PR does not implement any execution/API layer.

## 10. Changed files

- Added: `docs/parser_plans/mark_orderbook_gap_hunt_parser_contract_v0.md`.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_parser_contract_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `tests/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.
- No Council runtime, notification/alert runtime, Gemini runtime, or prompt changes.

## 11. Tests run

### Git status

```text
git status
```

Result: passed. The branch was `mark-orderbook-gap-parser-contract-v0`; only the two allowed docs files were untracked before staging.

### Git diff name check

```text
git diff --name-only
```

Result: passed. No tracked-file diff was shown before staging because the new files were still untracked.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only `docs/parser_plans/mark_orderbook_gap_hunt_parser_contract_v0.md` and `docs/pr_handoffs/mark_orderbook_gap_hunt_parser_contract_v0.md`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed. `Ran 255 tests in 12.101s` and ended with `OK`.

### Targeted mocked parser fixture test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser_fixtures
```

Result: passed. `Ran 6 tests in 0.004s` and ended with `OK`.

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

Result: passed after commit; working tree was clean and no generated packet, sampling, or Council-session artifacts were present.

## 12. Risks

- Contract wording may need refinement before production parser implementation.
- Final notional formulas remain unresolved and must not be guessed by the parser.
- Parser/readiness boundary must be preserved so parser output does not become an execution decision.
- Mark price is not executable and must not be treated as an order price.

## 13. Rollback plan

- Revert `docs/parser_plans/mark_orderbook_gap_hunt_parser_contract_v0.md` and `docs/pr_handoffs/mark_orderbook_gap_hunt_parser_contract_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling/Council-session JSON is committed.

## 14. Human review required

Reviewers should inspect:

1. `docs/parser_plans/mark_orderbook_gap_hunt_parser_contract_v0.md`
2. `docs/pr_handoffs/mark_orderbook_gap_hunt_parser_contract_v0.md`
3. Existing mocked fixture tests only as reference: `tests/test_mark_orderbook_gap_hunt_parser_fixtures.py`

## 15. No-trade compliance

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

## 16. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt Parser Contract Tests v0` or `Mark-Orderbook Gap Hunt Production Parser v0` PR only after this parser contract is reviewed. Runtime adapter, config registration, sampling, alert/notification, Council auto-call, active promotion, and execution/private API work should remain separate future tasks.
