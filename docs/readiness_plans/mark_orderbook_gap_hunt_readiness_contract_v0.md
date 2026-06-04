# Mark-Orderbook Gap Hunt Readiness Contract v0

## Purpose

Define how normalized parser output from `parse_mark_orderbook_gap_snapshot` should be interpreted by a future `Mark-Orderbook Gap Hunt v0` readiness layer.

This document is planning/test-contract only. It does not implement a runtime adapter, config registration, `collect_market_data` integration, `sample_market_data` integration, alert/notification, Council auto-call, active strategy promotion, execution/private API, generated packet JSON, or generated sampling JSON.

## Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Execution policy remains `NO_TRADE_ONLY`.
- The production parser is a pure function over already-fetched public response dictionaries.
- Parser `OK` means a normalized parser snapshot is available; it does not mean `WATCH`, Council review, alert, or execution.

## Parser-to-readiness boundary

Parser responsibilities end at parsing and normalization:

- parse public mark/ticker/orderbook/metadata payloads;
- verify instrument/category/`instId` comparability;
- surface missing fields and parser warnings;
- expose `normalized_status` as `OK`, `NEED_DATA`, or `REJECT` where applicable.

Readiness responsibilities start after parser output:

- apply fee/slippage/buffer assumptions;
- apply liquidity and size/notional rules;
- apply freshness/latency thresholds;
- compute mark-vs-orderbook gap metrics;
- apply persistence rules in a future sampling/runtime layer;
- decide `NEED_DATA`, `REJECT`, or `WATCH` for analysis only.

Parser `OK` must not be promoted directly to `WATCH`; readiness must still check gap, buffer, liquidity, freshness, and comparability.

## Readiness input

Readiness input should be the normalized parser output returned by `parse_mark_orderbook_gap_snapshot`.

Optional readiness parameters may include:

- `fee_slippage_buffer_pct`
- `liquidity_pass`
- `require_freshness`
- `size_or_notional_resolved`
- future persistence context, when sampling/runtime work is separately approved

## Readiness output

Readiness output should include:

- `readiness_status`: `NEED_DATA`, `REJECT`, or `WATCH`
- `readiness_pass`: `false` for now unless explicitly justified in a future reviewed PR
- `recommended_default_decision`
- `required_missing_fields`
- `warnings`
- `metrics`
  - `long_gap_pct`
  - `short_gap_pct`
  - `max_observed_gap_pct`
  - `fee_slippage_buffer_pct`
  - `estimated_net_gap_pct`, if computable
  - `liquidity_pass`
  - `freshness_pass`
  - `comparability_pass`

The readiness output must not include an execution instruction, order payload, private API request, Council auto-call, or alert trigger.

## NEED_DATA mapping

Return `NEED_DATA` when any of the following are true:

- parser `normalized_status` is `NEED_DATA`;
- `required_missing_fields` is non-empty;
- `comparability_pass` is false;
- `freshness_pass` is false;
- `mark_price`, `bid`, or `ask` is missing;
- size unit / notional formula is unresolved when liquidity readiness is required;
- fee/slippage/buffer assumptions are missing when net gap is required.

`NEED_DATA` means the observation is not ready for opportunity classification. It is not an API failure by itself and not an execution signal.

## REJECT mapping

Return `REJECT` when data is sufficient but the observation is not a candidate:

- no positive gross mark-vs-orderbook gap exists;
- fee/slippage/buffer-adjusted estimated net gap is non-positive;
- liquidity is insufficient;
- mark/orderbook gap is below the configured threshold;
- severe mark/reference quality warning exists.

`REJECT` means the data can be interpreted and the result is not a useful observation. It is not an execution signal.

## WATCH mapping

Return `WATCH` only when all of the following are true:

- parser output is `OK`;
- `comparability_pass` is true;
- `freshness_pass` is true, or freshness is not required for the controlled test case;
- mark-vs-ask or bid-vs-mark gap is positive;
- fee/slippage/buffer-adjusted estimated net gap is positive when assumptions are available;
- liquidity is sufficient, or liquidity is explicitly out of scope for the controlled test case;
- no severe quality warning blocks observation.

`WATCH` remains analysis-only. It must not imply `execution_allowed=true`, Council auto-call, alert/notification, active strategy promotion, or order placement.

## Formula planning

Readiness should use these planning formulas:

- `long_gap_pct = ((mark_price - ask) / mark_price) * 100`
- `short_gap_pct = ((bid - mark_price) / mark_price) * 100`
- `max_observed_gap_pct = max(long_gap_pct, short_gap_pct)`
- `estimated_net_gap_pct = max_observed_gap_pct - fee_slippage_buffer_pct`

If notional formula or size unit is unresolved, readiness must not claim liquidity readiness. It should return `NEED_DATA` if liquidity readiness is required.

## Test contract

The test-local readiness helper in `tests/test_mark_orderbook_gap_hunt_readiness_contract.py` pins this contract without adding production readiness/runtime code.

Required test cases:

- parser `NEED_DATA` -> readiness `NEED_DATA`;
- missing required fields -> `NEED_DATA`;
- valid parser output but zero/negative gross gap -> `REJECT`;
- positive gross gap wiped out by fee/slippage/buffer -> `REJECT`;
- positive net gap -> `WATCH`, with `readiness_pass=false` and no execution/Council/alert signal;
- `WATCH` does not imply `execution_allowed` or `council_auto_call`;
- no private/auth/order fields in readiness outputs.

## Future execution/API note

The user intends a future execution/risk engine only after multiple strategies have well-defined decision structures. That future engine must be common/shared, not strategy-specific ad hoc order code.

Future execution work requires a separate task card, credential isolation, dry-run/paper trading, kill switch, risk limits, order-state machine, audit logs, rollback plan, and explicit human review. This PR does not implement any part of that future execution/API layer.

## Next recommended step

After this readiness contract is reviewed, open a separate `Mark-Orderbook Gap Hunt Runtime Adapter Planning v0` or `Mark-Orderbook Gap Hunt Readiness Helper v0` PR only if needed. Runtime adapter, config registration, sampling, alert/notification, Council auto-call, active promotion, and execution/private API work must remain separate future tasks.
