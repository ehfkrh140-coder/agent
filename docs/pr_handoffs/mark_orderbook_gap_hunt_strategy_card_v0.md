# Mark-Orderbook Gap Hunt Strategy Card v0 Handoff

## 1. Purpose

Add a planning-only strategy card for `Mark-Orderbook Gap Hunt v0`, the next proposed strategy candidate after the cross-strategy decision criteria framework.

This PR does not implement runtime adapters, parsers, config registration, tests, sampling, Council handoff, alert/notification, active promotion, execution, private API, credentials, account/balance lookup, orders, transfers, or live network smoke.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- Current project phase remains `NO_TRADE_ONLY`.
- `orderbook_imbalance_v0` and `tether_cross_market_premium` remain experimental/non-active.
- Cross-strategy decision criteria now define `NEED_DATA`, `REJECT`, `WATCH`, `COUNCIL_REVIEW_CANDIDATE`, and forbidden/currently unimplemented `EXECUTION_CANDIDATE` semantics.
- Alert/notification is intentionally deferred until strategy criteria are more stable across multiple strategies.

## 3. Strategy concept

`Mark-Orderbook Gap Hunt v0` is a proposed / experimental-planning strategy that compares mark price with executable bid/ask prices.

Planning identity:

- Candidate `strategy_family`: `mark_orderbook_gap_hunt`
- Candidate `strategy_id`: `mark_orderbook_gap_hunt_v0`
- Status: proposed / experimental-planning
- Active: false
- Execution policy: `NO_TRADE_ONLY`

Candidate concepts:

- Long-side observation: mark price is sufficiently above executable ask.
  - `long_gap_pct = ((mark_price - ask) / mark_price) * 100`
- Short-side observation: executable bid is sufficiently above mark price.
  - `short_gap_pct = ((bid - mark_price) / mark_price) * 100`

Core warning: mark price is not executable. Bid/ask, size, unit/contract size, notional, fee, slippage, latency, freshness, and venue health must be validated before any candidate can move beyond `NEED_DATA` or `WATCH`.

## 4. Decision criteria mapping

- `NEED_DATA`: mark price missing, bid/ask missing, size missing, orderbook depth missing, unit/notional unknown, timestamp stale, latency too high, mark/reference quality unknown, or venue health unknown.
- `REJECT`: gap is non-positive after fee/slippage/buffer assumptions, liquidity insufficient, stale data, mark/reference unreliable, bid/ask and mark not comparable, or orderbook depth too thin/inconsistent.
- `WATCH`: mark-vs-bid/ask gap is positive and data quality is sufficient for observation, but persistence and human review are still required.
- `COUNCIL_REVIEW_CANDIDATE`: repeated `WATCH` with stable public data, enough liquidity, acceptable freshness/latency, and no obvious data-quality issue. Still not an order instruction.
- `EXECUTION_CANDIDATE`: currently forbidden; future execution/risk engine only, with explicit human review, credential isolation, dry-run/paper-trading, kill switch, rollback plan, and policy updates.

## 5. Source/probe plan

Do not implement the probe in this PR.

Next PR candidate: `Mark-Orderbook Gap Hunt Public Source Probe v0`.

Probe candidates may include public no-key derivatives endpoints from:

- Binance Futures;
- Bybit Derivatives;
- OKX derivatives;
- other public derivatives venues if endpoints are no-key and comparable.

The probe should confirm:

- endpoint is public and no key is required;
- symbol format;
- mark price field;
- bid/ask fields;
- size unit;
- timestamp;
- rate limit / latency;
- whether bid/ask and mark are comparable;
- whether derivative unit/contract size and notional can be calculated consistently.

## 6. Changed files

- Added: `docs/strategy_task_cards/mark_orderbook_gap_hunt.md`.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_strategy_card_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `tests/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.
- No Council runtime, notification/alert runtime, Gemini runtime, or prompt changes.

## 7. Tests run

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
Ran 249 tests in 12.331s
OK
```

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed (`exit=0`, 1193 matches). Matches are existing documentation/tests/no-trade guardrail references. This PR added no runtime credentials, private endpoints, account/balance lookup, order/cancel, withdrawal/deposit/transfer, fiat/bank transfer, auto-trading, parser, adapter, config registration, live network smoke, or execution surface.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed (`exit=0`, 989 matches). Evidence remains consistent with active strategy `cross_exchange_spot_spread_v1`; `tether_cross_market_premium` and `orderbook_imbalance` remain experimental/non-active; `mark_orderbook_gap_hunt` appears only in this proposed planning card/handoff.

### Final status check

```text
git status --short
```

Result after checks: only the two allowed documentation files were untracked before staging; no generated packet/sampling/Council session artifacts were present.

```text
?? docs/pr_handoffs/mark_orderbook_gap_hunt_strategy_card_v0.md
?? docs/strategy_task_cards/mark_orderbook_gap_hunt.md
```

## 8. Risks

- Mark price is not executable.
- Derivatives unit/contract-size and notional rules can create false positives.
- Leverage can magnify apparent opportunities.
- Last price, mark price, and orderbook can be stale or misaligned.
- Fees, slippage, funding, and buffers are not modeled in this card.
- The strategy must not become active automatically.
- The next source/probe task must remain public-read-only and no-key.

## 9. Rollback plan

- Revert `docs/strategy_task_cards/mark_orderbook_gap_hunt.md` and `docs/pr_handoffs/mark_orderbook_gap_hunt_strategy_card_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling JSON is committed.

## 10. Human review required

Reviewers should inspect:

1. `docs/strategy_task_cards/mark_orderbook_gap_hunt.md`
2. `docs/pr_handoffs/mark_orderbook_gap_hunt_strategy_card_v0.md`

## 11. No-trade compliance

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
- live network smoke: no

## 12. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt Public Source Probe v0` task. The probe should only verify public no-key endpoint availability and response shape for mark price/orderbook comparability. Do not implement runtime adapters, config registration, parsers, alert/notification, Council auto-call, active promotion, or execution in this strategy-card PR.
