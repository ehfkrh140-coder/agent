# Next Experimental Strategy Planning v0

## 1. 작업 목적

이 문서는 `mark_orderbook_gap_hunt_v0` 3-venue hardening phase 이후 다음 experimental strategy 후보를 비교하고, 다음에 어떤 매매법을 planning-first로 개발할지 정리하는 docs-only planning handoff다.

Scope:

- `mark_orderbook_gap_hunt_v0` hardening phase 이후 다음 experimental strategy 후보를 비교한다.
- 이 문서는 implementation이 아니라 planning이다.
- 현재 active strategy는 `cross_exchange_spot_spread_v1`로 유지한다.
- 모든 후보는 `NO_TRADE_ONLY` / public-read-only / analysis-only 기준으로만 검토한다.
- generated packet/sampling JSON은 smoke artifact이며 commit하지 않는다.

This PR does not implement new adapters, parsers, readiness helpers, registry entries, runtime behavior, timestamp policy, OKX index/reference endpoint access, alerting, Council auto-call, execution, or active strategy promotion.

## 2. Current baseline recap

Current project baseline:

- Active strategy: `cross_exchange_spot_spread_v1`.
- Experimental complete/hardened: `mark_orderbook_gap_hunt_v0`.
- Existing experimental strategy: `tether_cross_market_premium / usdt_krw_global_reference_v0`.
- Existing experimental strategy: `orderbook_imbalance_v0`.
- `mark_orderbook_gap_hunt_v0` has completed Binance / Bybit / OKX 3-venue baseline, 30-sample evidence, helper refactor, regression tests, post-refactor smoke, timestamp planning, OKX index/reference planning, and multi-venue comparative summary.
- `mark_orderbook_gap_hunt_v0` is not active and must not be promoted in this PR.
- Generated JSON under `data/market_samples/*.json` and `data/generated_packets/*.json` remains smoke artifact only and must not be committed.
- Private APIs, credentials, account/balance/position lookup, order/cancel, withdrawal/deposit/transfer, execution, alerting, and auto-trading are forbidden.

## 3. Candidate strategy list

### A. Spot-Futures Basis Strategy

- Candidate `strategy_family`: `spot_futures_basis`
- Candidate `strategy_id`: `spot_futures_basis_v0`
- Concept: compare spot price/orderbook versus futures/perp mark/orderbook basis.
- Public endpoints only: likely possible for market-data-only evidence.
- Infrastructure reuse: can reuse parts of the `mark_orderbook_gap_hunt_v0` derivatives / public endpoint / orderbook / evidence workflow.
- Advantages:
  - Intuitive derivatives-vs-spot dislocation structure.
  - Fits sampling and persistence evidence patterns.
  - Natural next step after mark/orderbook derivatives venue hardening.
- Risks:
  - Spot/futures symbol mapping errors.
  - Contract unit, lot size, and notional interpretation risk.
  - Funding and basis semantics can be confused.
  - Apparent basis can be mistaken for executable edge.
  - Mark price and orderbook price roles must remain distinct.

### B. Funding Rate Strategy

- Candidate `strategy_family`: `funding_rate_context`
- Candidate `strategy_id`: `funding_rate_context_v0`
- Concept: analyze funding rate, next funding time, mark/index/perp context, and funding regime.
- Public endpoints only: likely possible for derivatives metadata/context.
- Advantages:
  - Fits Binance / Bybit / OKX derivatives metadata work.
  - Useful context for Council analysis and future strategy research.
  - Can reuse sampling and evidence handoff patterns.
- Risks:
  - High funding does not by itself imply entry edge.
  - Without positions/execution, this must remain analysis-only context.
  - Funding time, interval, and rate semantics differ across venues.

### C. Open Interest / Liquidation Strategy

- Candidate `strategy_family`: `derivatives_flow_context`
- Candidate `strategy_id`: `derivatives_flow_context_v0`
- Concept: analyze open interest, liquidation cluster availability, and price reaction context.
- Public endpoints only: possible in some venues, but availability and quality need research.
- Advantages:
  - Potentially valuable Council context.
  - Can complement derivatives basis and funding context.
- Risks:
  - Venue public data quality differs.
  - Liquidation data availability may be incomplete or delayed.
  - Endpoint semantics and aggregation windows can be inconsistent.
  - False positives may be high without robust sampling and context.

### D. Trade Flow Momentum

- Candidate `strategy_family`: `trade_flow_momentum`
- Candidate `strategy_id`: `trade_flow_momentum_v0`
- Concept: use recent trades, taker buy/sell volume imbalance, and short-term orderflow context.
- Public endpoints only: possible through public trades endpoints where available.
- Advantages:
  - Can provide short-term momentum context.
  - Useful as Council context if carefully sampled.
- Risks:
  - Public trades volume semantics differ by venue.
  - Rate limits and high noise can make evidence unstable.
  - Short horizon signals can produce false positives.
  - More sensitive to latency and sampling cadence than slower context strategies.

### E. Strategy Evidence Dashboard / Journal Summary

- Not a new trading strategy.
- Concept: collect strategy evidence status, sampling status, watch items, no-trade status, and next-step recommendations in one reviewer-friendly place.
- Advantages:
  - Becomes more useful as the number of experimental strategies grows.
  - Improves review, handoff, and rollback visibility.
- Risks:
  - Does not add a new strategy signal.
  - Can become documentation overhead if not tied to clear review workflows.

### F. Council Review Handoff Criteria

- Not a new trading strategy.
- Concept: define what evidence Council reviewers need before discussing `WATCH` / `NEED_DATA` / `REJECT` at analysis-only level.
- Advantages:
  - Improves AI Council review quality.
  - Helps avoid over-interpreting incomplete evidence.
  - Can standardize no-trade analysis labels.
- Risks:
  - Could become policy documentation without implementation or measurable review improvements.
  - Must not turn Council outputs into execution instructions.

## 4. Comparison criteria

| Candidate | Public-read-only possible | Private API needed | Existing infrastructure reuse | OpportunityPacket schema fit | Readiness helper difficulty | Sampling evidence difficulty | False positive risk | No-trade safety | Beginner ops difficulty | Easy to split into small PRs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Spot-Futures Basis | High | No | High | High, but needs spot/futures fields | Medium | Medium | Medium-high | High if analysis-only | Medium | High |
| B. Funding Rate Context | High | No | Medium-high | Medium-high | Medium | Medium | Medium | High if context-only | Low-medium | High |
| C. Open Interest / Liquidation | Medium | No for public subset | Medium | Medium | Medium-high | High | High | High if context-only | Medium-high | Medium |
| D. Trade Flow Momentum | Medium-high | No for public subset | Medium | Medium | Medium-high | High | High | High if analysis-only | High | Medium |
| E. Evidence Dashboard / Journal Summary | High | No | High | Not a signal packet; summary-oriented | Low | Low | Low | High | Low | High |
| F. Council Review Handoff Criteria | High | No | Medium | Not a signal packet; review-policy-oriented | Low | Low | Medium if misused | High if no execution | Low | High |

Criteria notes:

- Public-read-only possibility is mandatory for any next experimental work.
- No candidate may require private API, credentials, account/balance/position lookup, order/cancel, withdrawal/deposit/transfer, or execution.
- Existing infrastructure reuse favors candidates that can reuse public adapter, packet, readiness, sampling, and handoff patterns.
- OpportunityPacket fit is strongest when candidate evidence can be represented as analysis-only metrics and assumptions without execution semantics.
- Sampling difficulty increases when high-frequency data, venue-specific aggregation, or unstable public endpoint availability is central.
- False positive risk is especially high where gross dislocation, high funding, liquidation clusters, or trade flow can be mistaken for executable edge.

## 5. Recommendation

Recommended ranking:

1. Spot-Futures Basis Strategy Planning v0
2. Funding Rate Context Strategy Planning v0
3. Strategy Evidence Dashboard / Journal Summary Planning

Recommended direction:

- Start with Spot-Futures Basis Strategy Planning v0 as the next strategy-planning PR.
- Keep Funding Rate Context Strategy Planning v0 as the second strategy candidate.
- Keep Strategy Evidence Dashboard / Journal Summary Planning as a parallel or follow-up governance/evidence candidate.
- Do not implement timestamp policy now.
- Do not implement OKX optional index/reference enrichment now.
- Do not promote `mark_orderbook_gap_hunt_v0` to active.

Rationale:

- Spot-Futures Basis most naturally reuses the derivatives / public endpoint / orderbook / evidence structure hardened during `mark_orderbook_gap_hunt_v0` work.
- Basis is intuitive, but spot/futures mapping, contract units, notional interpretation, and basis semantics are easy to misread; therefore the first step must be planning-only.
- Funding Rate Context is a strong next candidate, but funding itself must not be presented as trade edge without broader context and evidence.
- Dashboard / Journal planning is useful as the project grows, but it can follow after the next strategy candidate is selected.

## 6. Proposed next PR sequence

Recommended next PR sequence:

1. PR 1: Spot-Futures Basis Strategy Planning v0
2. PR 2: public source / endpoint research docs-only
3. PR 3: mocked parser fixture planning
4. PR 4: readiness policy planning
5. PR 5: first mocked implementation, `NO_TRADE_ONLY`
6. PR 6: user-local public-read-only smoke evidence
7. PR 7: sampling baseline evidence

Implementation guardrail for the sequence:

- PR 1 through PR 4 should remain planning/research/test-design-first.
- PR 5 must be mocked/unit-test-first and preserve `NO_TRADE_ONLY`.
- PR 6 and PR 7 must keep generated JSON artifacts out of git unless explicitly approved.

## 7. Explicitly not doing now

This PR explicitly does not do any of the following:

- Spot-Futures Basis implementation.
- Funding Rate implementation.
- Open Interest / Liquidation implementation.
- Trade Flow Momentum implementation.
- Strategy Evidence Dashboard implementation.
- Council Review Handoff Criteria implementation.
- Timestamp policy implementation.
- OKX index/reference endpoint implementation.
- Optional enrichment implementation.
- Active strategy change.
- Strategy registry change.
- New adapter implementation.
- New parser implementation.
- Readiness helper implementation.
- Execution implementation.
- Alert implementation.
- Council auto-call implementation.
- Private API or credential work.
- Account/balance/position/order/cancel/withdrawal/deposit/transfer work.
- Generated JSON commit.

## 8. No-trade compliance

This planning PR preserves no-trade posture:

- Active strategy promotion: no
- `mark_orderbook_gap_hunt_v0` active promotion: no
- New experimental strategy activation: no
- Private API: no
- Credentials/API keys/secrets/tokens: no
- Account/balance/position lookup: no
- Order/cancel: no
- Withdrawal/deposit/transfer: no
- Auto-trading: no
- Council auto-call: no
- Alert: no
- Execution: no
- Config/registry change: no
- Source/runtime behavior change: no
- Parser behavior change: no
- Readiness threshold change: no
- Generated JSON commit: no
- `NO_TRADE_ONLY` preserved: yes

## 9. Generated JSON commit 금지

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR intentionally adds only this planning handoff document and does not add generated JSON.

## 10. Rollback plan

Rollback path:

1. Revert this docs-only planning PR.
2. Remove `docs/pr_handoffs/next_experimental_strategy_planning_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/generated-data rollback is required.

## 11. Next PR candidates

Recommended order after this planning PR:

1. Spot-Futures Basis Strategy Planning v0
2. Funding Rate Context Strategy Planning v0
3. Strategy Evidence Dashboard / Journal Summary Planning
4. Council Review Handoff Criteria Planning
