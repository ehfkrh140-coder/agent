# Mark-Orderbook Gap Hunt Production Parser v0 Handoff

## 1. Purpose

Add a small pure production parser module for `Mark-Orderbook Gap Hunt v0` that accepts already-fetched mocked/public response dictionaries and returns normalized planning output.

This PR does not implement a runtime adapter, live HTTP calls, config registration, registry integration, `collect_market_data` integration, `sample_market_data` integration, alert/notification, Council auto-call, active strategy promotion, execution/private API, generated packet JSON, or generated sampling JSON.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Execution policy remains `NO_TRADE_ONLY`.
- The previous parser contract documented public-read-only input bundles, normalized output fields, parser/readiness boundaries, and expected `NEED_DATA` behavior.
- Existing mocked fixture tests pinned Binance / Bybit / OKX valid same-instrument examples plus failure / `NEED_DATA` / `REJECT` / `WATCH` planning cases.

## 3. Parser implementation scope

Implemented `src/market_data/parsers/mark_orderbook_gap_hunt.py` as a pure parser module.

Allowed implementation scope:

- accepts already-fetched public response dictionaries;
- supports parser modes `binance_usdm`, `bybit_linear`, and `okx_swap`;
- returns normalized planning dictionaries with `normalized_status` as `OK` or `NEED_DATA` for implemented parser cases;
- raises a parser error only for malformed top-level structure or unsupported parser mode;
- keeps expected missing-data cases as `NEED_DATA` instead of raising.

Explicitly not implemented:

- runtime adapter;
- config registration;
- registry integration;
- live HTTP/network calls;
- env var credential lookup;
- sampling integration;
- readiness decision layer;
- alert/notification;
- Council auto-call;
- execution/private API.

## 4. Parser input/output

Public parser function:

```text
parse_mark_orderbook_gap_snapshot(
    *,
    venue_id,
    parser_mode,
    mark_response,
    orderbook_response,
    metadata_response,
    ticker_response=None,
    collected_at_utc=None,
    latency_ms=None,
    max_data_age_ms=None,
)
```

Normalized output includes:

- `venue_id`
- `parser_mode`
- `instrument_id`
- `instrument_type`
- `mark_price`
- `index_price`
- `bid`
- `ask`
- `bid_size_raw`
- `ask_size_raw`
- `bid_size_unit`
- `ask_size_unit`
- `tick_size`
- `quantity_step`
- `lot_size`
- `min_order_size`
- `min_notional`
- `contract_value`
- `contract_multiplier`
- `contract_value_currency`
- `settle_currency`
- `margin_asset`
- `funding_rate`
- `next_funding_time`
- `timestamp`
- `data_age_ms`
- `comparability_pass`
- `freshness_pass`
- `required_missing_fields`
- `parser_warnings`
- `normalized_status`

The parser intentionally does not return `WATCH`, does not return `execution_allowed=true`, and does not trigger Council/alert/execution.

## 5. Venue parser behavior

### Binance USDⓈ-M: `binance_usdm`

- Parses premiumIndex-like mark responses.
- Parses depth-like orderbook responses.
- Parses exchangeInfo-like metadata responses.
- Requires mark `symbol`, metadata `symbol`, and metadata `pair` to match.
- Extracts tick size, quantity step, minimum order size, minimum notional, margin asset, funding rate, and next funding time.

### Bybit linear: `bybit_linear`

- Parses V5 ticker responses.
- Parses V5 orderbook responses.
- Parses V5 instruments-info metadata responses.
- Requires ticker category and metadata category to be `linear`, and ticker/orderbook/metadata symbols to match.
- Extracts tick size, quantity step, minimum order size, minimum notional, settle currency, funding rate, next funding time, and records funding interval as a parser warning.

### OKX swap: `okx_swap`

- Parses public mark-price responses.
- Parses books responses or ticker top-of-book responses.
- Parses public instruments metadata responses.
- Requires mark, books/ticker when available, and metadata `instId` to be comparable.
- Extracts contract value, contract multiplier, contract value currency, settle currency, tick size, lot size, and minimum order size.

## 6. NEED_DATA behavior

The parser returns `normalized_status=NEED_DATA` and populates `required_missing_fields` for expected missing-data cases, including:

- missing mark/ticker response;
- missing orderbook response;
- missing metadata response;
- missing mark price, bid, or ask;
- instrument mismatch;
- Bybit category mismatch;
- OKX `instId` mismatch;
- missing OKX `ctVal`, `ctMult`, `ctValCcy`, `settleCcy`, `lotSz`, or `minSz`;
- stale timestamp when `collected_at_utc` and `max_data_age_ms` allow freshness evaluation.

Malformed non-dict payloads and unsupported parser modes raise `MarkOrderbookGapParserError` as programmer/malformed-input errors.

## 7. Tests run

### Git status

```text
git status
```

Result: passed. The branch was `mark-orderbook-gap-production-parser-v0`; changes were limited to allowed parser, test, and handoff files before staging.

### Git diff name check

```text
git diff --name-only
```

Result: passed. The tracked diff showed `tests/test_mark_orderbook_gap_hunt_parser_fixtures.py`; new parser, test, and handoff files were untracked before staging.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only the five allowed files listed in `Changed files`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed. `Ran 264 tests in 12.400s` and ended with `OK`.

### Production parser test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser
```

Result: passed. `Ran 8 tests in 0.006s` and ended with `OK`.

### Mocked fixture parser test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser_fixtures
```

Result: passed. `Ran 7 tests in 0.003s` and ended with `OK`.

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed. The scan returned existing documentation/test/runtime references plus this PR's explicit no-trade deferrals; this PR added no credential lookup, private API, account/balance, order/cancel, withdrawal/deposit/transfer, execution, adapter, registry, config, or sampling surface.

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

## 8. What this proves

- The parser can normalize Binance / Bybit / OKX mocked public fixture dictionaries into stable planning output.
- The parser can return `NEED_DATA` for expected missing-data and mismatch cases without raising.
- The parser can evaluate freshness when timestamp inputs and thresholds are supplied.
- The parser remains pure: tests verify no socket call and no `os.getenv` call during parsing.

## 9. What this does not prove

- It does not prove runtime adapter behavior.
- It does not prove live endpoint behavior.
- It does not prove final profitability or final notional formulas.
- It does not implement readiness, sampling, alert/notification, Council auto-call, active promotion, or execution.
- It does not register this parser in configs or market-data registry.

## 10. Changed files

- Added: `src/market_data/parsers/__init__.py`.
- Added: `src/market_data/parsers/mark_orderbook_gap_hunt.py`.
- Added: `tests/test_mark_orderbook_gap_hunt_parser.py`.
- Updated: `tests/test_mark_orderbook_gap_hunt_parser_fixtures.py`.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_production_parser_v0.md`.
- No `configs/**` changes.
- No `src/market_data/adapters/**` changes.
- No `src/market_data/registry.py` changes.
- No `tools/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.

## 11. Risks

- Future parser refinement may change field naming or notional treatment after human review.
- Current size-unit labels remain conservative planning labels and must not be treated as executable sizing rules.
- Readiness remains separate; parser `OK` is not `WATCH`, Council recommendation, or execution permission.
- Runtime integration must not be added without a separate PR and review.

## 12. Rollback plan

- Revert `src/market_data/parsers/__init__.py`, `src/market_data/parsers/mark_orderbook_gap_hunt.py`, `tests/test_mark_orderbook_gap_hunt_parser.py`, the fixture-test update, and this handoff file.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling/Council-session JSON is committed.

## 13. Human review required

Reviewers should inspect:

1. `src/market_data/parsers/mark_orderbook_gap_hunt.py`
2. `tests/test_mark_orderbook_gap_hunt_parser.py`
3. `tests/test_mark_orderbook_gap_hunt_parser_fixtures.py`
4. `docs/pr_handoffs/mark_orderbook_gap_hunt_production_parser_v0.md`

## 14. No-trade compliance

- private API: no
- API key/secret/token: no
- env credential lookup: no
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
- sampling implementation: no
- live network smoke as merge requirement: no

## 15. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt Parser Readiness Contract v0` or `Mark-Orderbook Gap Hunt Runtime Adapter Planning v0` only after this pure parser implementation is reviewed. Runtime adapter, config registration, sampling, alert/notification, Council auto-call, active promotion, and execution/private API work must remain separate future tasks.
