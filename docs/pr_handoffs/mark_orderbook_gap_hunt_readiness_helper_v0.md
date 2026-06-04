# Mark-Orderbook Gap Hunt Readiness Helper v0 Handoff

## 1. Purpose

Add a small pure production readiness helper for `Mark-Orderbook Gap Hunt v0` that consumes normalized parser output and returns `NEED_DATA`, `REJECT`, or `WATCH` readiness output.

This PR does not implement a runtime adapter, config registration, `collect_market_data` integration, `sample_market_data` integration, alert/notification, Council auto-call, active strategy promotion, execution/private API, generated packet JSON, or generated sampling JSON.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Execution policy remains `NO_TRADE_ONLY`.
- The production parser remains a pure function over already-fetched public response dictionaries.
- The parser readiness contract established that parser `OK` is not `WATCH`, Council review, alert, or execution.

## 3. Helper implementation scope

Implemented `src/strategy/mark_orderbook_gap_hunt_readiness.py` as a pure helper module.

Allowed implementation scope:

- accepts normalized parser output dictionaries;
- computes readiness metrics with Decimal conversion;
- returns analysis-only readiness dictionaries;
- maps expected missing-data cases to `NEED_DATA`;
- maps sufficient-but-not-candidate observations to `REJECT`;
- maps positive net gap observations to `WATCH` only.

Explicitly not implemented:

- runtime adapter;
- config registration;
- registry integration;
- live HTTP/network calls;
- env var credential lookup;
- sampling integration;
- alert/notification;
- Council auto-call;
- execution/private API.

## 4. Input/output

Public helper function:

```text
evaluate_mark_orderbook_gap_readiness(
    parser_output,
    *,
    fee_slippage_buffer_pct,
    liquidity_pass=None,
    require_freshness=True,
    size_or_notional_resolved=False,
    min_net_gap_pct=0,
)
```

Readiness output includes:

- `readiness_status`: `NEED_DATA`, `REJECT`, or `WATCH`;
- `readiness_pass`: always `false` in this phase;
- `recommended_default_decision`;
- `required_missing_fields`;
- `warnings`;
- `metrics.long_gap_pct`;
- `metrics.short_gap_pct`;
- `metrics.max_observed_gap_pct`;
- `metrics.fee_slippage_buffer_pct`;
- `metrics.estimated_net_gap_pct`;
- `metrics.liquidity_pass`;
- `metrics.freshness_pass`;
- `metrics.comparability_pass`.

The output intentionally excludes `execution_allowed`, `council_auto_call`, and `alert_trigger`.

## 5. NEED_DATA behavior

The helper returns `NEED_DATA` when:

- parser output is not a dict;
- parser `normalized_status` is `NEED_DATA` or unsupported;
- parser `required_missing_fields` is non-empty;
- `comparability_pass` is not true;
- `freshness_pass` is not true when freshness is required;
- `mark_price`, `bid`, or `ask` is missing or not safely numeric;
- `size_or_notional_resolved` is false;
- `fee_slippage_buffer_pct` is missing;
- `liquidity_pass` is missing.

## 6. REJECT behavior

The helper returns `REJECT` when data is sufficient but:

- `liquidity_pass` is false;
- `max_observed_gap_pct <= 0`;
- `estimated_net_gap_pct <= min_net_gap_pct`.

## 7. WATCH behavior

The helper returns `WATCH` only when:

- parser output is `OK`;
- `comparability_pass` is true;
- freshness is true or not required;
- `size_or_notional_resolved` is true;
- `fee_slippage_buffer_pct` is provided;
- `liquidity_pass` is true;
- `estimated_net_gap_pct > min_net_gap_pct`.

`WATCH` remains analysis-only. `readiness_pass` remains `false`, and no execution, Council auto-call, or alert trigger field is emitted.

## 8. Formula implementation

The helper uses Decimal conversion and computes:

- `long_gap_pct = ((mark_price - ask) / mark_price) * 100`
- `short_gap_pct = ((bid - mark_price) / mark_price) * 100`
- `max_observed_gap_pct = max(long_gap_pct, short_gap_pct)`
- `estimated_net_gap_pct = max_observed_gap_pct - fee_slippage_buffer_pct`

## 9. Tests run

### Git status

```text
git status
```

Result: passed. The branch was `mark-orderbook-gap-readiness-helper-v0`; changes were limited to allowed readiness helper, tests, and handoff files before staging.

### Git diff name check

```text
git diff --name-only
```

Result: passed. The tracked diff showed `tests/test_mark_orderbook_gap_hunt_readiness_contract.py`; new readiness helper, helper test, and handoff files were untracked before staging.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only the four allowed files listed in `Changed files`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed. `Ran 285 tests in 16.751s` and ended with `OK`.

### Production parser test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser
```

Result: passed. `Ran 8 tests in 0.010s` and ended with `OK`.

### Mocked fixture parser test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser_fixtures
```

Result: passed. `Ran 7 tests in 0.006s` and ended with `OK`.

### Readiness contract test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_readiness_contract
```

Result: passed. `Ran 9 tests in 0.008s` and ended with `OK`.

### Readiness helper test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_readiness
```

Result: passed. `Ran 12 tests in 0.016s` and ended with `OK`.

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

- The parser-to-readiness mapping now has a small production pure helper.
- Parser `NEED_DATA` maps to readiness `NEED_DATA`.
- Missing mark/bid/ask, unresolved notional, missing fee buffer, missing freshness, or missing liquidity gates map to `NEED_DATA`.
- No positive gross gap, fee-buffer-wiped gap, and failed liquidity map to `REJECT`.
- Positive net gap maps to `WATCH`, but remains analysis-only with `readiness_pass=false`.
- Helper tests verify no socket call, no `os.getenv` call, and no execution/Council/alert trigger fields.

## 11. What this does not prove

- It does not prove runtime adapter behavior.
- It does not prove live endpoint behavior.
- It does not implement sampling, alert/notification, Council auto-call, active promotion, or execution.
- It does not register this helper in configs or market-data registry.
- It does not finalize live trading thresholds or notional/liquidity rules.

## 12. Changed files

- Added: `src/strategy/mark_orderbook_gap_hunt_readiness.py`.
- Added: `tests/test_mark_orderbook_gap_hunt_readiness.py`.
- Updated: `tests/test_mark_orderbook_gap_hunt_readiness_contract.py` to delegate the contract helper to the production helper.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_readiness_helper_v0.md`.
- No `configs/**` changes.
- No `src/market_data/adapters/**` changes.
- No `src/market_data/registry.py` changes.
- No `tools/**` changes.
- No `src/council/**`, `src/notifications/**`, or `src/storage/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.

## 13. Risks

- Thresholds are still planning assumptions and may need review before runtime use.
- Size/notional readiness is explicit but final venue formulas remain future work.
- `WATCH` could be misread as actionable unless reviewers preserve the analysis-only boundary.
- Runtime integration must not be added without a separate PR and review.

## 14. Rollback plan

- Revert `src/strategy/mark_orderbook_gap_hunt_readiness.py`, `tests/test_mark_orderbook_gap_hunt_readiness.py`, the contract-test update, and this handoff file.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling/Council-session JSON is committed.

## 15. Human review required

Reviewers should inspect:

1. `src/strategy/mark_orderbook_gap_hunt_readiness.py`
2. `tests/test_mark_orderbook_gap_hunt_readiness.py`
3. `tests/test_mark_orderbook_gap_hunt_readiness_contract.py`
4. `docs/pr_handoffs/mark_orderbook_gap_hunt_readiness_helper_v0.md`

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

Open a separate `Mark-Orderbook Gap Hunt Runtime Adapter Planning v0` only after this readiness helper is reviewed. Runtime adapter, config registration, sampling, alert/notification, Council auto-call, active promotion, and execution/private API work must remain separate future tasks.
