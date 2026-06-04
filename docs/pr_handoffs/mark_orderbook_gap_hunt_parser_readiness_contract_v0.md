# Mark-Orderbook Gap Hunt Parser Readiness Contract v0 Handoff

## 1. Purpose

Define how normalized output from the pure `Mark-Orderbook Gap Hunt v0` production parser should map into readiness decisions.

This PR is a planning/test-contract PR. It does not implement a runtime adapter, config registration, `collect_market_data` integration, `sample_market_data` integration, alert/notification, Council auto-call, active strategy promotion, execution/private API, generated packet JSON, or generated sampling JSON.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Execution policy remains `NO_TRADE_ONLY`.
- The production parser accepts already-fetched public response dictionaries and returns normalized planning output.
- Parser `OK` is not `WATCH`, not Council review, not alert, and not execution.

## 3. Parser-to-readiness boundary

Parser responsibilities remain limited to parsing and normalization:

- parse public mark/ticker/orderbook/metadata payloads;
- verify instrument/category/`instId` comparability;
- expose missing fields and parser warnings;
- return `normalized_status` as `OK`, `NEED_DATA`, or `REJECT` where applicable.

Readiness responsibilities are separate:

- apply fee/slippage/buffer assumptions;
- apply liquidity and size/notional rules;
- apply freshness/latency checks;
- compute mark-vs-orderbook gap metrics;
- classify observations as `NEED_DATA`, `REJECT`, or `WATCH` for analysis only.

Parser `OK` must not be promoted directly to `WATCH` without readiness checks.

## 4. Readiness input/output

Input should be the normalized parser output from `parse_mark_orderbook_gap_snapshot`.

Readiness output should include:

- `readiness_status`: `NEED_DATA`, `REJECT`, or `WATCH`;
- `readiness_pass`: `false` for now unless explicitly justified later;
- `recommended_default_decision`;
- `required_missing_fields`;
- `warnings`;
- `metrics` with `long_gap_pct`, `short_gap_pct`, `max_observed_gap_pct`, `fee_slippage_buffer_pct`, `estimated_net_gap_pct`, `liquidity_pass`, `freshness_pass`, and `comparability_pass`.

Readiness output must not include execution instructions, order payloads, private API requests, Council auto-calls, or alert triggers.

## 5. NEED_DATA mapping

Readiness should return `NEED_DATA` when:

- parser `normalized_status` is `NEED_DATA`;
- `required_missing_fields` is non-empty;
- `comparability_pass` is false;
- `freshness_pass` is false when freshness is required;
- `mark_price`, `bid`, or `ask` is missing;
- size unit / notional formula is unresolved when liquidity readiness is required;
- fee/slippage/buffer assumptions are missing when net gap is required.

## 6. REJECT mapping

Readiness should return `REJECT` when data is sufficient but not a candidate:

- no positive gross mark-vs-orderbook gap exists;
- estimated net gap after fee/slippage/buffer is non-positive;
- liquidity is insufficient;
- gap is below configured threshold;
- severe mark/reference quality warning blocks observation.

## 7. WATCH mapping

Readiness should return `WATCH` only when:

- parser output is `OK`;
- `comparability_pass` is true;
- freshness is true or not required for the controlled test case;
- mark-vs-ask or bid-vs-mark gap is positive;
- fee/slippage/buffer-adjusted estimated net gap is positive when assumptions are available;
- liquidity is sufficient or explicitly out of scope for the controlled test case.

`WATCH` remains analysis-only and must not imply execution, Council auto-call, alert/notification, active promotion, or order placement.

## 8. Formula planning

Planned formulas:

- `long_gap_pct = ((mark_price - ask) / mark_price) * 100`
- `short_gap_pct = ((bid - mark_price) / mark_price) * 100`
- `max_observed_gap_pct = max(long_gap_pct, short_gap_pct)`
- `estimated_net_gap_pct = max_observed_gap_pct - fee_slippage_buffer_pct`

If notional formula or size unit is unresolved, readiness must not claim liquidity readiness.

## 9. Tests run

### Git status

```text
git status
```

Result: passed. The branch was `mark-orderbook-gap-readiness-contract-v0`; only the allowed readiness plan, handoff, and test files were untracked before staging.

### Git diff name check

```text
git diff --name-only
```

Result: passed. No tracked-file diff was shown before staging because the new files were still untracked.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only the three allowed files listed in `Changed files`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed. `Ran 273 tests in 10.643s` and ended with `OK`.

### Production parser test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser
```

Result: passed. `Ran 8 tests in 0.004s` and ended with `OK`.

### Mocked fixture parser test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser_fixtures
```

Result: passed. `Ran 7 tests in 0.004s` and ended with `OK`.

### Readiness contract test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_readiness_contract
```

Result: passed. `Ran 9 tests in 0.002s` and ended with `OK`.

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed. The scan returned existing documentation/test/runtime references plus this PR's explicit no-trade deferrals; this PR added no credential lookup, private API, account/balance, order/cancel, withdrawal/deposit/transfer, execution, adapter, registry, config, sampling, alert, or Council auto-call surface.

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

## 10. What this proves

- The parser-to-readiness boundary is documented and test-pinned without runtime integration.
- A parser `NEED_DATA` output maps to readiness `NEED_DATA`.
- Sufficient parser output with no positive gross gap maps to `REJECT`.
- Positive gross gap that is wiped out by fee/slippage/buffer maps to `REJECT`.
- Positive net gap maps to `WATCH`, but remains analysis-only with `readiness_pass=false`.
- `WATCH` does not imply execution, Council auto-call, alert, or active promotion.

## 11. What this does not prove

- It does not prove runtime adapter behavior.
- It does not prove live endpoint behavior.
- It does not implement a production readiness module.
- It does not implement sampling, alert/notification, Council auto-call, active promotion, or execution.
- It does not register this parser or readiness contract in configs or market-data registry.

## 12. Changed files

- Added: `docs/readiness_plans/mark_orderbook_gap_hunt_readiness_contract_v0.md`.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_parser_readiness_contract_v0.md`.
- Added: `tests/test_mark_orderbook_gap_hunt_readiness_contract.py`.
- No `configs/**` changes.
- No `src/market_data/adapters/**` changes.
- No `src/market_data/registry.py` changes.
- No `tools/**` changes.
- No `src/council/**`, `src/notifications/**`, or `src/storage/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.

## 13. Risks

- The readiness helper is test-local only; future production readiness may need reviewed naming and thresholds.
- Fee/slippage/buffer and liquidity thresholds remain planning assumptions, not live trading rules.
- `WATCH` could be misread as actionable unless reviewers preserve the analysis-only boundary.
- Runtime integration must not be added without a separate PR and review.

## 14. Rollback plan

- Revert `docs/readiness_plans/mark_orderbook_gap_hunt_readiness_contract_v0.md`, `docs/pr_handoffs/mark_orderbook_gap_hunt_parser_readiness_contract_v0.md`, and `tests/test_mark_orderbook_gap_hunt_readiness_contract.py`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling/Council-session JSON is committed.

## 15. Human review required

Reviewers should inspect:

1. `docs/readiness_plans/mark_orderbook_gap_hunt_readiness_contract_v0.md`
2. `tests/test_mark_orderbook_gap_hunt_readiness_contract.py`
3. `docs/pr_handoffs/mark_orderbook_gap_hunt_parser_readiness_contract_v0.md`

## 16. No-trade compliance

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

## 17. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt Runtime Adapter Planning v0` or `Mark-Orderbook Gap Hunt Readiness Helper v0` PR only after this readiness contract is reviewed. Runtime adapter, config registration, sampling, alert/notification, Council auto-call, active promotion, and execution/private API work must remain separate future tasks.
