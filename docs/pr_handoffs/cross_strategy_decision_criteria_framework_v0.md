# Cross-Strategy Decision Criteria Framework v0

## 1. Purpose

Document a shared cross-strategy decision criteria framework before adding any alert/notification layer or implementing another strategy. This PR is documentation/evidence only.

## 2. Why alert is deferred

Alert/notification is deferred because the strategy decision vocabulary should be consistent before alerts are attached. The project should first align strategies around `NEED_DATA`, `REJECT`, `WATCH`, and `COUNCIL_REVIEW_CANDIDATE`; only later should a common alert layer be added.

Future alerts should focus on `WATCH` and `COUNCIL_REVIEW_CANDIDATE`, avoid noisy routine `NEED_DATA`/`REJECT` alerts, and must never be execution.

## 3. Current strategy status

- `cross_exchange_spot_spread_v1`: active / `NO_TRADE_ONLY`.
- `orderbook_imbalance_v0`: experimental / non-active / `NO_TRADE_ONLY`.
- `tether_cross_market_premium / usdt_krw_global_reference_v0`: experimental / non-active / `NO_TRADE_ONLY`.
- Tether user-local 30-sample live sampling evidence succeeded and showed data collection stability with `NO_PERSISTENT_EDGE / REJECT`, not profitability.

## 4. Decision criteria summary

- `NEED_DATA`: required data is missing or not comparable; examples include missing bid/ask, missing orderbook depth, missing global reference, stale timestamp, or poor latency.
- `REJECT`: data is sufficient, but the candidate is not an opportunity; examples include negative fee/slippage/buffer-adjusted net gap, depeg risk, stale data, or insufficient liquidity.
- `WATCH`: interesting observation, but not ready for execution or automatic Council handoff; persistence or human review may still be required.
- `COUNCIL_REVIEW_CANDIDATE`: persistent high-quality evidence suitable for Council analysis only; still not an order instruction.
- `EXECUTION_CANDIDATE`: not implemented and forbidden in the current phase; future execution/risk work requires a separate task, explicit human review, credential isolation, dry-run/paper-trading, rollback/kill-switch planning, and policy updates.

## 5. Strategy-by-strategy mapping

### `cross_exchange_spot_spread_v1`

- Current status: active / `NO_TRADE_ONLY`.
- Main criteria: executable bid/ask, VWAP, fee/slippage/buffer, liquidity, freshness, and latency.
- `NEED_DATA`: missing venue, missing bid/ask/depth, stale timestamps, or missing liquidity context.
- `REJECT`: no executable net gap after fees/slippage/buffer, stale data, insufficient liquidity, or last-price-only illusion.
- `WATCH`: positive observation requiring persistence or human review under `NO_TRADE_ONLY`.
- `COUNCIL_REVIEW_CANDIDATE`: only after persistent, high-quality read-only evidence; still not execution.

### `orderbook_imbalance_v0`

- Current status: experimental / non-active / `NO_TRADE_ONLY`.
- Main criteria: orderbook depth imbalance, notional, spread, freshness, and liquidity.
- Imbalance is not an executable spread, so it should be WATCH-centered.
- Do not automatically convert imbalance into Council handoff or execution.

### `tether_cross_market_premium`

- Current status: experimental / non-active / `NO_TRADE_ONLY`.
- Current evidence: user-local 30-sample live sampling succeeded; all samples collected live public data, all three global references succeeded, and the run summarized `NO_PERSISTENT_EDGE / REJECT`.
- This proves data collection stability for that run, not profitability.
- `net_gap_pass=false`, `NO_PERSISTENT_EDGE`, and `REJECT` are normal no-edge outcomes, not API or strategy failures.

## 6. Next strategy candidate

Future next candidate: `Mark-Orderbook Gap Hunt v0`.

Purpose: detect divergence between mark price and executable bid/ask prices.

Caveats:

- mark price is not an executable fill price;
- bid/ask, size, unit, notional, fee, slippage, latency, and freshness must be validated;
- any future implementation must be a separate public-read-only `NO_TRADE_ONLY` task unless policy changes through explicit human review;
- this PR does not implement the strategy.

## 7. Changed files

- Added: `docs/strategy_decision_criteria.md`.
- Added: `docs/pr_handoffs/cross_strategy_decision_criteria_framework_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `tests/**` changes.
- No generated packet/sampling/Council session artifacts committed.
- No Council runtime, notification/alert runtime, Gemini runtime, or prompt changes.

## 8. Tests run

### Git status

```text
git status
```

Result before changes: working tree clean.

### Git diff name check

```text
git diff --name-only
```

Result before changes: no output.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: pass.

```text
Ran 249 tests in 12.297s
OK
```

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed (`exit=0`, 1145 matches). Matches are existing documentation/tests/no-trade guardrail references. This PR added no runtime credentials, private endpoints, account/balance lookup, order/cancel, withdrawal/deposit/transfer, fiat/bank transfer, auto-trading, or execution surface.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed (`exit=0`, 886 matches). Evidence remains consistent with active strategy `cross_exchange_spot_spread_v1`; `orderbook_imbalance_v0` and `tether_cross_market_premium` remain experimental/non-active/`NO_TRADE_ONLY`.

### Final generated artifact/status check

```text
git status --short
```

Result after changes: only the two documentation files were changed before commit; no generated packet/sampling/Council session artifacts were present.

## 9. Risks

- A shared vocabulary can still be misused if future alert/Council/runtime work treats `WATCH` or `COUNCIL_REVIEW_CANDIDATE` as execution instructions.
- Strategy-specific thresholds are not finalized by this document; this PR defines decision language, not numeric tuning.
- `Mark-Orderbook Gap Hunt v0` is only a future candidate and must not be treated as implemented.

## 10. Rollback plan

- Revert `docs/strategy_decision_criteria.md` and `docs/pr_handoffs/cross_strategy_decision_criteria_framework_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling JSON is committed.

## 11. Human review required

Reviewers should inspect:

1. `docs/strategy_decision_criteria.md`
2. `docs/pr_handoffs/cross_strategy_decision_criteria_framework_v0.md`

## 12. No-trade compliance

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
- FX / USD-KRW / fair_usdt_krw_price calculation: no
- generated packet JSON commit: no
- generated sampling JSON commit: no
- new strategy runtime implementation: no

## 13. Next recommended step

Use this framework when defining the next strategy candidate, likely `Mark-Orderbook Gap Hunt v0`, in a separate task. Do not add alert/notification, Council auto-call, active promotion, execution, private API, or new runtime behavior in this PR.
