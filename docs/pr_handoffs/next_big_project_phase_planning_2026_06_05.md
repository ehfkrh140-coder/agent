# Next Big Project Phase Planning after Spot-Futures Basis Binance + Bybit Close-out v0

## 1. 작업 목적

이 문서는 `mark_orderbook_gap_hunt_v0`와 `spot_futures_basis_v0`의 baseline close-out 이후 다음 큰 프로젝트 단계를 planning-only로 정리한다.

목적:

- `mark_orderbook_gap_hunt_v0`와 `spot_futures_basis_v0`의 baseline close-out 이후 다음 큰 프로젝트 단계를 정리한다.
- 이번 문서는 implementation이 아니라 planning이다.
- `NO_TRADE_ONLY`를 유지한다.
- Active strategy는 `cross_exchange_spot_spread_v1`로 유지한다.

## 2. Current strategy baseline recap

| Strategy | Status | Venue coverage | Evidence status | Current recommendation | No-trade posture | Next possible action |
| --- | --- | --- | --- | --- | --- | --- |
| `cross_exchange_spot_spread_v1` | active baseline | Existing active cross-exchange spot spread venues | Existing production/baseline strategy; not changed by recent experimental evidence PRs | Keep active strategy unchanged | Active strategy boundary; no new execution behavior in this planning PR | Continue existing governance; do not mix experimental signals into active path without separate approval |
| `tether_cross_market_premium` / `usdt_krw_global_reference_v0` | reference / planning context | Domestic USDT/KRW + global reference candidates | Requirements and source matrix planning exist; FX/global reference gaps remain evidence items | Keep as reference/planning context | Analysis-only evidence posture for planning docs | Use as dashboard/journal context, not as auto-execution signal |
| `orderbook_imbalance_v0` | candidate / planning context | Not promoted; venue coverage remains planning-dependent | No close-out baseline comparable to the two recent experimental tracks in this cycle | Keep as future candidate | Analysis-only | Revisit during next experimental strategy selection |
| `mark_orderbook_gap_hunt_v0` | experimental / non-active / `NO_TRADE_ONLY` | Binance / Bybit / OKX baseline complete | Public-read-only collect/sampling and comparative summary completed | Do not promote; keep as experimental evidence track | `NO_TRADE_ONLY`; no alert / no Council auto-call / no execution | Feed evidence into dashboard/journal and Council review criteria planning |
| `spot_futures_basis_v0` | proposed / experimental / non-active / `NO_TRADE_ONLY` | Binance + Bybit complete for this cycle; OKX deferred | Public-read-only collect, 3-sample, 30-sample, and comparative summary completed | Do not promote; keep as experimental evidence track | `NO_TRADE_ONLY`; no alert / no Council auto-call / no execution | Feed evidence into dashboard/journal and future Depth/VWAP / timestamp policy planning |

## 3. Completed baseline recap

### `mark_orderbook_gap_hunt_v0`

- Binance / Bybit / OKX baseline complete.
- Comparative summary complete.
- Experimental / non-active / `NO_TRADE_ONLY` 유지.
- No active promotion.
- No alerting.
- No Council auto-call.
- No execution.

### `spot_futures_basis_v0`

- Binance + Bybit baseline complete for this cycle.
- OKX deferred as future expansion.
- Comparative summary complete.
- Experimental / non-active / `NO_TRADE_ONLY` 유지.
- No active promotion.
- No alerting.
- No Council auto-call.
- No execution.

## 4. What we learned

Lessons learned:

- Public-read-only collect/sampling workflow works.
- Mocked-first development works.
- User-local smoke/evidence separation works.
- Generated JSON commit ban is necessary.
- Venue-specific response quirks require small follow-up PRs.
- `REJECT` is often normal no-edge, not failure.
- `WATCH` must remain analysis-only.
- Mark/index/funding/last price are context, not executable basis.
- Top-of-book liquidity is not fill feasibility.
- Timestamp/data_age watch items need policy, not ad-hoc fixes.

## 5. Next big phase candidates

| Candidate | Purpose | Why it matters | Explicit non-goals |
| --- | --- | --- | --- |
| A. Strategy Evidence Dashboard / Journal Summary Planning | Design a dashboard/journal view for strategy evidence status, latest sampling result, venue coverage, watch items, and next recommendation in one place. | Recent work produced many handoff files; reviewers need a single evidence index before deciding what deserves deeper review. | No dashboard implementation in this PR; no runtime changes; no active promotion. |
| B. Council Review Handoff Criteria Planning | Define what evidence makes `WATCH` / `NEED_DATA` / `REJECT` worth manual Council review. | Prevents ad-hoc escalation and keeps Council usage evidence-driven. | Not Council auto-call; not alerting; not execution. |
| C. Depth/VWAP Planning | Design depth/VWAP / size simulation candidates to reduce top-of-book basis/gap limitations. | Top-of-book liquidity is not fill feasibility; future evidence should describe size sensitivity. | No execution, no private API, no order feasibility claims. |
| D. Next Experimental Strategy Selection | Compare candidates such as `funding_rate_context_v0`, `derivatives_flow_context_v0`, `trade_flow_momentum_v0`, or strategy evidence dashboard itself as non-trading infra. | Helps choose the next bounded, evidence-first project after two baseline close-outs. | No new strategy implementation in this PR. |
| E. OKX Expansion as Future Only | Keep `spot_futures_basis_v0` OKX expansion as a future expansion option. | Maintains multi-venue roadmap without extending the just-closed Binance + Bybit cycle. | Do not start OKX implementation now. |
| F. Timestamp / Clock-Skew Policy | Define strategy-common handling for negative `data_age_ms` and timestamp alignment watch items. | Timestamp quirks appeared as watch items and should become a shared policy, not ad-hoc fixes. | No readiness behavior change before separate approval. |

## 6. Recommended order

Recommended order:

1. Strategy Evidence Dashboard / Journal Summary Planning.
2. Council Review Handoff Criteria Planning.
3. Timestamp / Clock-Skew Policy Planning.
4. Depth/VWAP Planning.
5. Next Experimental Strategy Selection.
6. OKX expansion as future only.

Each step should start as docs-only planning before implementation.

## 7. Why not active promotion yet

No active promotion rationale:

- `mark_orderbook_gap_hunt_v0` evidence has no persistent positive net edge.
- `spot_futures_basis_v0` evidence has no persistent positive net basis.
- `REJECT` / `NO_PERSISTENT_EDGE` results repeated across baselines.
- `WATCH` / `REJECT` / `NEED_DATA` are analysis-only labels.
- No private API.
- No account state.
- No order feasibility.
- No fill feasibility.
- Therefore no active promotion, no alert, no Council auto-call, and no execution.

## 8. Proposed next PR sequence

Proposed PR sequence:

- PR 1: Strategy Evidence Dashboard / Journal Summary Planning v0.
- PR 2: Dashboard data source / handoff index planning v0.
- PR 3: Council Review Handoff Criteria Planning v0.
- PR 4: Timestamp / Clock-Skew Policy Planning v0.
- PR 5: Depth/VWAP Planning v0.
- PR 6: Next Experimental Strategy Selection v0.

## 9. Explicitly not doing now

Explicitly not doing in this PR:

- Dashboard implementation 없음.
- Council auto-call 없음.
- Alert 구현 없음.
- Execution 구현 없음.
- New strategy implementation 없음.
- OKX `spot_futures_basis` implementation 없음.
- Active strategy 변경 없음.
- Config/registry 변경 없음.
- Source/runtime behavior 변경 없음.
- Live endpoint 호출 없음.
- Generated JSON 생성/commit 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Auto-trading 없음.

## 10. OKX deferred scope note

- `spot_futures_basis_v0` OKX는 future expansion으로 defer한다.
- 이는 scope control이지 permanent rejection이 아니다.
- 이번 PR에서는 OKX research/adapter/config를 만들지 않는다.

## 11. No-trade compliance

No-trade compliance 확인:

- Active strategy promotion 없음.
- Experimental strategy active 승격 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position lookup 없음.
- Order/cancel 없음.
- Withdrawal/deposit/transfer 없음.
- Auto-trading 없음.
- Council auto-call 없음.
- Alert 없음.
- Execution 없음.
- Config/registry 변경 없음.
- Source/runtime behavior 변경 없음.

## 12. Generated JSON commit 금지

Generated JSON policy 확인:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 13. Rollback plan

Rollback plan:

- Docs-only PR이므로 revert하고 이 handoff 문서 1개를 제거하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- Re-run repository tests if the revert PR process requires evidence.
- Confirm no generated JSON files are committed.

## 14. Next PR candidates

다음 PR 후보 순서:

1. Strategy Evidence Dashboard / Journal Summary Planning v0.
2. Council Review Handoff Criteria Planning v0.
3. Timestamp / Clock-Skew Policy Planning v0.
4. Depth/VWAP Planning v0.
5. Next Experimental Strategy Selection v0.
