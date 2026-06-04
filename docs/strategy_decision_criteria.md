# Cross-Strategy Decision Criteria Framework v0

## Purpose

This document defines a shared decision vocabulary for market-data strategies before adding a common alert/notification layer. It is documentation-only and does not implement alerts, notifications, Council auto-calls, active strategy promotion, execution, private APIs, credentials, account/balance lookup, orders, transfers, FX conversion, or new strategy runtime.

The project can eventually include an execution/risk engine, but the current phase remains `NO_TRADE_ONLY`. Council and strategy outputs are analysis states only.

## Why alerts are deferred

Alerts should not be attached strategy-by-strategy before the decision criteria are stable. If each strategy invents its own alert semantics, reviewers may confuse data failures, no-edge conditions, watch-only signals, Council-review candidates, and execution candidates.

Near-term policy:

- Do not add alert/notification behavior in this step.
- First align strategies on shared `NEED_DATA`, `REJECT`, `WATCH`, and `COUNCIL_REVIEW_CANDIDATE` semantics.
- Add a common alert layer only after more strategies follow the same criteria.
- Alerts should focus on `WATCH` or `COUNCIL_REVIEW_CANDIDATE` states.
- Alerts should not spam routine `REJECT` or `NEED_DATA` outcomes.
- Alerts are not execution and must not submit orders, transfer funds, query balances, or call private APIs.

## Common decision states

### NEED_DATA

Use `NEED_DATA` when required evidence is missing or not comparable, so the strategy cannot make a reliable judgment.

Examples:

- bid/ask is missing;
- orderbook depth is missing;
- global reference basket is missing or below the configured minimum;
- timestamp, latency, freshness, or source health is poor;
- last-price-only data is present but executable bid/ask/depth is absent;
- required venue observation is missing.

Meaning for reviewers: collect or repair data first. Do not interpret `NEED_DATA` as a trade candidate.

### REJECT

Use `REJECT` when data is sufficient and the strategy can rule out the opportunity.

Examples:

- estimated net gap is negative after fee, slippage, and safety-buffer assumptions;
- data is stale even if prices look favorable;
- liquidity is insufficient;
- global reference/depeg risk is active;
- spread exists at last price but not at executable bid/ask/VWAP;
- no persistent edge appears in sampling.

Meaning for reviewers: the system worked and rejected a non-opportunity. `REJECT` is often a healthy no-action outcome.

### WATCH

Use `WATCH` when the observation is interesting enough to keep monitoring but is not ready for automated handoff or execution.

Examples:

- signal direction is positive, but more persistence samples are needed;
- strategy is experimental/non-active;
- liquidity/freshness is adequate for observation but not for promotion;
- human review is needed before escalation.

Meaning for reviewers: watch-only analysis. `WATCH` is not `ENTER`, not an order, not a Council auto-call, and not execution permission.

### COUNCIL_REVIEW_CANDIDATE

Use `COUNCIL_REVIEW_CANDIDATE` only when a signal persists across samples, data quality is sufficient, and the packet is appropriate for manual Council review.

Requirements should include:

- enough consecutive or persistent samples;
- required bid/ask/depth/global reference data present;
- freshness and latency acceptable;
- liquidity checks acceptable;
- no active blocking risk flag;
- readiness evidence documented.

Meaning for reviewers: Council may review the packet as analysis. It is still not an order instruction and must not be converted directly into a trade.

### EXECUTION_CANDIDATE

`EXECUTION_CANDIDATE` is not implemented in the current project phase.

It may only be discussed in a future, separate task after explicit human review and after the project has a deterministic execution/risk engine plan, credential isolation, dry-run/paper-trading phase, rollback/kill-switch plan, and updated no-trade/execution policy. It must not be introduced by a documentation shortcut, alert rule, Council prompt, or strategy readiness change.

## Strategy-by-strategy mapping

### `cross_exchange_spot_spread_v1`

Status:

- active strategy;
- `NO_TRADE_ONLY`;
- public Upbit/Bithumb spot market data only.

Core criteria:

- executable bid/ask, not last-price-only spread;
- orderbook depth and VWAP where configured;
- fee, slippage, and safety-buffer adjusted net gap;
- liquidity and notional checks;
- freshness and latency checks.

Typical mapping:

- `NEED_DATA`: missing bid/ask/orderbook depth, stale timestamps, missing venue, or insufficient liquidity data.
- `REJECT`: net gap fails after fee/slippage/buffer, stale data, insufficient liquidity, or non-executable spread.
- `WATCH`: positive observation that still requires persistence or human review under `NO_TRADE_ONLY`.
- `COUNCIL_REVIEW_CANDIDATE`: only after persistent, high-quality, read-only evidence; still not execution.

### `orderbook_imbalance_v0`

Status:

- experimental;
- non-active;
- `NO_TRADE_ONLY`.

Core criteria:

- orderbook imbalance is a pressure/structure signal, not an executable spread;
- depth levels, notional, spread, freshness, and liquidity must be interpretable;
- imbalance direction can be useful for observation but should not imply a trade.

Typical mapping:

- `NEED_DATA`: missing orderbook depth, insufficient levels, stale timestamps, or missing liquidity context.
- `REJECT`: balanced/no imbalance, inconsistent depth, stale data, or insufficient liquidity.
- `WATCH`: persistent bid-heavy or ask-heavy imbalance worth monitoring.
- `COUNCIL_REVIEW_CANDIDATE`: only with persistent, clean, well-documented imbalance evidence; no automatic Council handoff or execution.

### `tether_cross_market_premium / usdt_krw_global_reference_v0`

Status:

- experimental;
- non-active;
- `NO_TRADE_ONLY`.

Current evidence:

- global reference blocker was resolved with Binance/Bybit `USDCUSDT`, OKX `USDC-USDT`, and `normalize: inverse`;
- user-local live packet smoke succeeded;
- user-local 3-sample live sampling succeeded;
- user-local 30-sample live sampling succeeded;
- 30-sample evidence shows `samples_ok=30`, `samples_error=0`, `successful_global_reference_count=3` for all samples, `NO_PERSISTENT_EDGE`, and `REJECT`;
- this proves data collection stability for that run, not profitability.

Typical mapping:

- `NEED_DATA`: missing Upbit/Bithumb domestic `USDT/KRW`, missing global reference, stale latency/timestamps, last-price-only candidate, or global reference count below threshold.
- `REJECT`: `net_gap_pass=false`, no persistent edge, depeg risk, negative net gap after fee/buffer, or enough data to conclude no opportunity.
- `WATCH`: positive evaluate-only candidate with healthy global references and no depeg flag, but still experimental/non-active.
- `COUNCIL_REVIEW_CANDIDATE`: only after persistent, high-quality samples and explicit human review; still not execution.

Important interpretation:

- `net_gap_pass=false` is a normal no-edge finding, not an API failure.
- `NO_PERSISTENT_EDGE` is a valid no-action sampling result.
- `successful_global_reference_count=3` means all three global references succeeded for the sample.
- `REJECT` can be a healthy system outcome.

## Future alert/notification policy

Do not add alerts now. A future common alert layer should be considered only after more strategies use the same decision criteria.

Future alert rules should:

- be strategy-agnostic where possible;
- focus on `WATCH` and `COUNCIL_REVIEW_CANDIDATE`;
- avoid noisy routine `REJECT` and `NEED_DATA` alerts;
- clearly label experimental/non-active strategies;
- never imply execution;
- never call Council automatically unless a separate task explicitly permits it;
- never place orders, query balances, transfer funds, or use private APIs.

## Future next strategy candidate: Mark-Orderbook Gap Hunt v0

Suggested next strategy candidate: `Mark-Orderbook Gap Hunt v0`.

Purpose:

- detect divergence between mark price and actually executable bid/ask prices.

Important caveats:

- mark price is not an executable fill price;
- bid/ask, size, unit, notional, fee, slippage, latency, and freshness must be validated;
- any apparent gap must be tested against executable prices, not mark price alone;
- this PR does not implement the strategy;
- any future implementation must remain public-read-only and `NO_TRADE_ONLY` unless a separate human-approved execution/risk task changes the policy.
