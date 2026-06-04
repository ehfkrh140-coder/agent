# Mark-Orderbook Gap Hunt Strategy Card v0

## 1. Strategy identity

- Candidate `strategy_family`: `mark_orderbook_gap_hunt`
- Candidate `strategy_id`: `mark_orderbook_gap_hunt_v0`
- Status: proposed / experimental-planning
- Active: false
- Execution policy: `NO_TRADE_ONLY`

This card is a planning document only. It does not implement a runtime adapter, parser, config registration, sampling flow, alert, notification, Council auto-call, execution, private API access, API key usage, account/balance lookup, order/cancel, withdrawal/deposit/transfer, or generated data artifact.

## 2. Strategy concept

`Mark-Orderbook Gap Hunt v0` looks for a difference between a venue's mark price and the actually executable top-of-book/orderbook prices.

The core hypothesis is simple:

- A mark price can imply where the derivatives instrument is being referenced or risk-managed.
- Actual execution still depends on bid/ask and available size.
- A mark-vs-orderbook gap can be an observation candidate only when the executable side is also available, fresh, sufficiently liquid, and comparable to the mark reference.

### Long-side observation candidate

A long-side observation candidate may exist when mark price is sufficiently above the executable ask.

Example planning metric:

```text
long_gap_pct = ((mark_price - ask) / mark_price) * 100
```

Interpretation: the mark reference is higher than the current ask, but this is not enough by itself. The ask must have real size, the unit/notional must be understood, and fees/slippage/buffer/freshness must be checked before treating this as an opportunity candidate.

### Short-side observation candidate

A short-side observation candidate may exist when executable bid is sufficiently above mark price.

Example planning metric:

```text
short_gap_pct = ((bid - mark_price) / mark_price) * 100
```

Interpretation: the current bid is higher than the mark reference, but this is not enough by itself. The bid must have real size, the unit/notional must be understood, and fees/slippage/buffer/freshness must be checked before treating this as an opportunity candidate.

### Non-negotiable caveat

Mark price is not an executable fill price. Do not classify a mark/orderbook divergence as an opportunity until bid/ask, size, unit/contract size, notional calculation, fee placeholder, slippage placeholder, latency, freshness, and venue health are validated with public read-only data.

## 3. Required public data

A future source/probe PR should confirm the following fields from public, no-key endpoints:

- `mark_price`
- `bid`
- `ask`
- `bid_size`
- `ask_size`
- orderbook depth
- unit / contract size, if derivatives
- notional calculation rule
- timestamp
- latency
- data age
- fee placeholder
- slippage placeholder
- venue health

If any of these fields are missing or not comparable, the correct state is usually `NEED_DATA`, not `WATCH`.

## 4. Candidate metrics

Potential candidate metrics for future implementation:

- `mark_price`
- `ask`
- `bid`
- `long_gap_pct`
- `short_gap_pct`
- `long_notional`
- `short_notional`
- `estimated_net_gap_pct` — future only after fee/slippage/buffer rules are specified
- `liquidity_pass`
- `freshness_pass`
- `mark_reference_quality`

Metric names are planning placeholders. A future implementation PR must validate schema, units, and exact calculation rules before adding runtime code.

## 5. Decision criteria mapping

This card follows `docs/strategy_decision_criteria.md`.

### NEED_DATA

Use `NEED_DATA` when the strategy cannot safely compare mark and executable prices.

Examples:

- `mark_price` missing;
- bid/ask missing;
- bid/ask size missing;
- orderbook depth missing;
- derivative unit or contract size unknown;
- notional calculation rule unknown;
- timestamp stale;
- latency too high;
- mark/reference quality unknown;
- venue health unknown.

### REJECT

Use `REJECT` when data is sufficient and the observation is not a valid opportunity.

Examples:

- long/short gap is non-positive after fee/slippage/buffer assumptions;
- liquidity is insufficient;
- timestamp/data age is stale;
- mark/reference appears unreliable;
- bid/ask and mark are not comparable;
- orderbook depth is too thin or inconsistent.

### WATCH

Use `WATCH` when mark-vs-bid/ask gap is positive, data quality is sufficient for observation, and the signal is worth monitoring, but persistence and human review are still required.

`WATCH` is not an order, not an `ENTER`, not a Council auto-call, and not execution permission.

### COUNCIL_REVIEW_CANDIDATE

Use `COUNCIL_REVIEW_CANDIDATE` only after repeated `WATCH` observations with stable public data, enough liquidity, acceptable freshness/latency, and no obvious data-quality issue.

This remains an analysis state only. It is not an order instruction and must not be converted directly into execution.

### EXECUTION_CANDIDATE

`EXECUTION_CANDIDATE` is currently forbidden. It may only be discussed in a future execution/risk-engine task with explicit human review, credential isolation, dry-run/paper-trading, kill switch, rollback plan, and policy updates.

## 6. Source/probe plan

Do not implement any probe in this PR.

The next PR should be a public source probe that checks candidate public endpoints for mark price and orderbook data. Candidate venues may include:

- Binance Futures public endpoints;
- Bybit Derivatives public endpoints;
- OKX derivatives public endpoints;
- other public derivatives endpoints if they require no credentials and expose comparable fields.

The probe must confirm:

- endpoint is public and no key is required;
- symbol format;
- mark price field;
- bid/ask fields;
- size unit;
- timestamp;
- rate limit / latency;
- whether bid/ask and mark are comparable;
- whether derivative unit/contract size and notional can be calculated consistently.

The probe must not add private APIs, credentials, auth headers, account/balance lookup, orders, transfers, config adapter registration, runtime parser implementation, alerts, Council auto-calls, or live smoke that requires network access as part of this strategy-card PR.

## 7. Risks

- Mark price is not executable.
- Derivatives units and contract sizes can be confusing.
- Leverage can magnify false positives.
- Last price and mark price can be stale or misaligned.
- Orderbook depth can be thin, spoofed, or not comparable to mark price.
- Fees, slippage, funding, and safety buffers are not yet modeled for this proposed strategy.
- The strategy must not become active automatically.

## 8. Explicit deferrals

This strategy card explicitly defers:

- runtime adapter implementation;
- config registration;
- parser implementation;
- sampling;
- alert/notification;
- Council auto-call;
- Council decision to trade conversion;
- active strategy promotion;
- execution/private API;
- API key/secret/token;
- account/balance lookup;
- order/cancel;
- withdrawal/deposit/transfer;
- live network smoke.

## 9. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt Public Source Probe v0` task. That task should only inspect public no-key source availability and response shapes, keep `NO_TRADE_ONLY`, and avoid runtime adapter/config/parser implementation unless explicitly scoped in a later PR.
