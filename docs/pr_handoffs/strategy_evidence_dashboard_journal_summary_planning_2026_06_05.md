# Strategy Evidence Dashboard / Journal Summary Planning v0

## 1. 작업 목적

이 문서는 지금까지 쌓인 strategy evidence를 한 곳에서 추적하기 위한 Strategy Evidence Dashboard / Journal Summary를 planning-only로 설계한다.

목적:

- 전략별 evidence status, venue coverage, latest sampling status, watch items, next recommendation을 한 곳에서 추적하기 위한 dashboard / journal summary를 설계한다.
- 이번 문서는 implementation이 아니라 planning이다.
- `NO_TRADE_ONLY`를 유지한다.
- Active strategy는 `cross_exchange_spot_spread_v1`로 유지한다.

## 2. Problem statement

최근 baseline/evidence 작업의 문제 정의:

- 최근 작업으로 `docs/pr_handoffs` 문서가 많아졌다.
- PR title/body는 generic/cumulative처럼 보일 수 있어 step-specific handoff가 source-of-truth다.
- 전략별 evidence 상태를 매번 사람이 수동으로 추적하기 어렵다.
- Council 검토 전에 어떤 전략이 ready / no-edge / needs-data / watch-item 상태인지 한눈에 볼 필요가 있다.
- Generated JSON은 commit 금지이므로 dashboard는 raw JSON이 아니라 handoff evidence summary 기반이어야 한다.

## 3. Dashboard / journal goals

Dashboard / journal summary의 목표:

- Strategy별 status 확인.
- Active / experimental / proposed / future 구분.
- Venue coverage 확인.
- Latest collect smoke 확인.
- Latest 3-sample / 30-sample evidence 확인.
- Readiness status counts 확인.
- Persistence status 확인.
- `council_recommended` 확인.
- Watch items 확인.
- No-trade posture 확인.
- Next recommended action 확인.
- Source handoff document link/path 확인.
- Rollback/source-of-truth 확인.

## 4. Initial strategy rows

초기 dashboard row 후보:

| Strategy row | Initial role | Candidate row reason |
| --- | --- | --- |
| `cross_exchange_spot_spread_v1` | Active baseline | Current active strategy; dashboard must show it is unchanged by experimental evidence docs. |
| `tether_cross_market_premium` / `usdt_krw_global_reference_v0` | Experimental / reference context | Domestic/global reference context and unresolved source requirements should remain visible. |
| `orderbook_imbalance_v0` | Experimental / future evidence row | Candidate strategy row for future evidence tracking, not active. |
| `mark_orderbook_gap_hunt_v0` | Experimental / non-active / `NO_TRADE_ONLY` | Binance / Bybit / OKX baseline complete and needs summarized evidence status. |
| `spot_futures_basis_v0` | Proposed / experimental / non-active / `NO_TRADE_ONLY` | Binance + Bybit baseline complete for this cycle and OKX deferred. |
| `funding_rate_context_v0` | Proposed / future | Future candidate only. |
| `derivatives_flow_context_v0` | Proposed / future | Future candidate only. |
| `trade_flow_momentum_v0` | Proposed / future | Future candidate only. |

Candidate row fields:

- `strategy_family`
- `strategy_id`
- `status`
- `active_flag`
- `no_trade_only`
- `execution_policy`
- `venue_coverage`
- `latest_collect_smoke`
- `latest_3_sample_evidence`
- `latest_30_sample_evidence`
- `latest_comparative_summary`
- `readiness_status_counts`
- `persistence_status`
- `council_recommended`
- `positive_net_gap_count`
- `readiness_pass_count`
- `watch_items`
- `current_recommendation`
- `next_action`
- `source_handoff_paths`

## 5. Initial dashboard status proposal

### `cross_exchange_spot_spread_v1`

- Active baseline.
- Active strategy remains unchanged.
- Dashboard should not imply new execution behavior.

### `mark_orderbook_gap_hunt_v0`

- Experimental / non-active / `NO_TRADE_ONLY`.
- Binance / Bybit / OKX baseline complete.
- Comparative summary complete.
- No active promotion.
- Watch items:
  - timestamp/data_age.
  - OKX index/reference semantics.
  - mark price not executable.
  - no persistent positive net edge.

### `spot_futures_basis_v0`

- Proposed / experimental / non-active / `NO_TRADE_ONLY`.
- Binance + Bybit baseline complete for this cycle.
- OKX deferred.
- Comparative summary complete.
- No active promotion.
- Watch items:
  - top-of-book liquidity not fill feasibility.
  - mark/index/funding context.
  - timestamp/data_age.
  - depth/VWAP not implemented.
  - non-positive estimated net basis.

### `tether_cross_market_premium` / `usdt_krw_global_reference_v0`

- Experimental / reference context / non-active / `NO_TRADE_ONLY`.
- Global reference and domestic/global context should be tracked.
- No active promotion.

### `orderbook_imbalance_v0`

- Experimental / non-active / `NO_TRADE_ONLY`.
- Future evidence dashboard row, not active.

### Future strategies

- `funding_rate_context_v0`, `derivatives_flow_context_v0`, and `trade_flow_momentum_v0` are proposed/future rows only.
- They are not active strategies.
- They require separate planning before any implementation.

## 6. Source-of-truth policy

Source-of-truth policy:

- `docs/pr_handoffs/*.md`가 strategy evidence source-of-truth다.
- Generated `data/market_samples/*.json`와 `data/generated_packets/*.json`는 smoke artifact이며 commit 금지다.
- Dashboard는 generated JSON 원본을 참조하지 않고, handoff summary를 참조해야 한다.
- PR title/body가 generic해 보여도 step-specific handoff를 우선한다.
- Dashboard/journal row는 handoff path를 반드시 포함해야 한다.

## 7. Dashboard data model candidate

아래는 planning-only data model 후보이며, 이번 PR에서는 구현하지 않는다.

```yaml
dashboard_schema_version: strategy_evidence_dashboard_v0
generated_at_utc: "<manual-or-generated-timestamp>"
strategies:
  - strategy_family: "<family>"
    strategy_id: "<strategy_id>"
    status: "active|experimental|proposed|future|reference"
    active_flag: false
    no_trade_only: true
    execution_policy: "NO_TRADE_ONLY|existing_active_policy"
    venue_coverage:
      - "<venue_or_context>"
    evidence_status: "baseline_complete|planning_only|needs_data|future"
    latest_collect_smoke:
      status: "complete|not_applicable|not_started"
      source_handoff_path: "docs/pr_handoffs/<file>.md"
    latest_sampling_3x:
      status: "complete|not_applicable|not_started"
      source_handoff_path: "docs/pr_handoffs/<file>.md"
    latest_sampling_30x:
      status: "complete|not_applicable|not_started"
      source_handoff_path: "docs/pr_handoffs/<file>.md"
    latest_comparative_summary:
      status: "complete|not_applicable|not_started"
      source_handoff_path: "docs/pr_handoffs/<file>.md"
    readiness_status_counts: {}
    persistence_status: "NO_PERSISTENT_EDGE|not_applicable|unknown"
    council_recommended: false
    watch_items: []
    recommendation: "keep_active|do_not_promote|future_planning"
    source_handoff_paths: []
```

Candidate fields are intentionally evidence-oriented and should not encode execution instructions.

## 8. Manual vs generated dashboard options

| Option | Description | 장점 | 단점 | Recommendation |
| --- | --- | --- | --- | --- |
| Option A | Docs-only manual dashboard markdown | 안전, 빠름, generated JSON 없음 | 사람이 갱신해야 함 | First step recommendation. |
| Option B | Generated markdown from handoff index | 자동화 가능 | Parser 구현 필요, drift 위험 | Consider only after handoff index / data source planning. |
| Option C | JSON/YAML dashboard index committed | Machine-readable | Schema governance 필요 | Consider only after schema governance and review criteria exist. |

Recommendation:

- 첫 단계는 Option A docs-only manual dashboard planning이다.
- Implementation 전에는 data source / handoff index planning을 별도 PR로 둔다.
- Any future generated dashboard must not commit raw market sample JSON or generated packet JSON.

## 9. What dashboard must not imply

Dashboard가 암시하면 안 되는 것:

- Dashboard는 trading signal이 아니다.
- `WATCH`는 `ENTER`가 아니다.
- `REJECT`는 failure가 아니다.
- `NO_PERSISTENT_EDGE`는 adapter failure가 아니다.
- `council_recommended=false`는 정상 no-edge일 수 있다.
- Dashboard는 alert, Council auto-call, execution, active promotion을 트리거하지 않는다.
- Dashboard는 private API / account / order feasibility를 암시하지 않는다.

## 10. Proposed implementation sequence

제안 sequence:

- PR 1: Strategy Evidence Dashboard / Journal Summary Planning v0.
- PR 2: Handoff index / data source planning v0.
- PR 3: Manual dashboard markdown v0.
- PR 4: Dashboard row schema tests, docs-only or mocked/unit only.
- PR 5: Optional generated dashboard script planning.
- PR 6: Optional generated dashboard implementation, no generated market JSON.

## 11. Relationship to Council Review Handoff Criteria

Relationship:

- Dashboard는 Council criteria의 입력 자료다.
- Dashboard는 Council auto-call이 아니다.
- Dashboard가 `WATCH` / `NEED_DATA` / `REJECT` evidence를 정리하면, 다음 PR에서 Council review criteria가 어떤 evidence를 manual review할지 정의한다.
- Council review criteria should remain manual/review-oriented until explicitly approved otherwise.

## 12. Explicitly not doing now

이번 PR에서 명시적으로 하지 않는 것:

- Dashboard implementation 없음.
- Generated dashboard script 없음.
- JSON/YAML dashboard file 없음.
- Source/runtime behavior 변경 없음.
- Config/registry 변경 없음.
- Active strategy 변경 없음.
- Live endpoint 호출 없음.
- `sample_market_data` 실행 없음.
- `collect_market_data` 실행 없음.
- Generated market JSON 생성/commit 없음.
- Alert 없음.
- Council auto-call 없음.
- Execution 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Auto-trading 없음.
- OKX `spot_futures_basis` implementation 없음.

## 13. OKX deferred scope note

- `spot_futures_basis_v0` OKX는 future expansion으로 defer한다.
- 이는 scope control이지 permanent rejection이 아니다.
- 이번 PR에서는 OKX research/adapter/config를 만들지 않는다.

## 14. No-trade compliance

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

## 15. Generated JSON commit 금지

Generated JSON policy 확인:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- Dashboard는 generated JSON 원본이 아니라 handoff evidence summary를 기반으로 해야 한다.
- 이번 PR에는 generated JSON을 추가하지 않음.

## 16. Rollback plan

Rollback plan:

- Docs-only PR이므로 revert하고 이 handoff 문서 1개를 제거하면 된다.
- Code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback은 필요 없다.
- Confirm GitHub Files changed contains only this handoff file after rollback.
- Re-run required validation commands if rollback evidence is requested.

## 17. Next PR candidates

다음 PR 후보 순서:

1. Handoff index / data source planning v0.
2. Council Review Handoff Criteria Planning v0.
3. Timestamp / Clock-Skew Policy Planning v0.
4. Depth/VWAP Planning v0.
5. Next Experimental Strategy Selection v0.
