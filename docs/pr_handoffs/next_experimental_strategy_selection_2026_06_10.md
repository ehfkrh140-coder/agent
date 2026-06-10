# Next Experimental Strategy Selection Finalization v0

## Summary

This is a docs-only decision PR. It applies the previously documented Strategy Module Boundary Map and Strategy Selection Rubric to the next experimental strategy candidates, then selects one candidate for the next planning step.

This PR does not implement any strategy. It does not implement Funding Rate endpoints, parsers, adapters, packet builders, readiness logic, VWAP-adjusted readiness, dashboard generation, alerts, Council auto-call, execution behavior, registry changes, config changes, or active promotion.

Decision: recommend `funding_rate_context_v0` as the next experimental strategy planning candidate, with strict context-only and `NO_TRADE_ONLY` guardrails.

## Inputs Reviewed

The following inputs were reviewed before writing this decision handoff:

- `docs/AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md`
- `docs/strategy_module_boundaries.md`
- `docs/pr_handoffs/strategy_module_boundary_map_2026_06_10.md`
- `docs/strategy_evidence_dashboard.md`
- `AGENTS.md`
- `docs/no_trade_policy.md`
- `docs/pr_handoffs/README.md`
- `docs/merge_gate.md`
- `docs/rollback_policy.md`
- `docs/task_checklist.md`
- `docs/agent_workflow.md`

Operational note: a fresh `origin/main` branch was attempted first, but this environment could not fetch GitHub because the network request failed with `CONNECT tunnel failed, response 403`. Work proceeded on a scoped branch from the available repository state, and this limitation is recorded here for reviewer awareness.

## Current Baseline Preservation

This decision does not change the current baseline or any existing strategy behavior.

- Active baseline remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY` with Binance / Bybit / OKX baseline complete.
- `spot_futures_basis_v0` remains proposed / experimental / non-active / `NO_TRADE_ONLY` with Binance + Bybit baseline complete and OKX deferred.
- `usdt_krw_global_reference_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- `orderbook_imbalance_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- Depth/VWAP remains diagnostics-only context. It does not change readiness, recommended default decision, persistence, dashboard interpretation, or active status.
- `funding_rate_context_v0` remains unimplemented. This document only selects it as the next planning candidate.

No active strategy behavior, execution policy, config, registry, source code, tests, tools, generated data, or runtime behavior is changed by this PR.

## Existing System Preservation Gate

| Gate question | Answer | Evidence / decision |
| --- | --- | --- |
| Does this preserve the existing public adapter → parser → OpportunityPacket → readiness → sampling → handoff → dashboard → Council manual review flow? | Yes. | The selected next step is planning-first and must reuse the existing evidence pipeline. No new runtime path is introduced here. |
| Does this avoid changing active baseline `cross_exchange_spot_spread_v1` behavior? | Yes. | This PR is docs-only and does not touch config, registry, or active strategy files. |
| Does this avoid changing existing experimental strategy status, readiness semantics, or dashboard interpretation? | Yes. | Existing experimental strategies remain non-active and `NO_TRADE_ONLY`; this document only selects the next planning candidate. |
| Does this avoid polluting common modules for a new strategy? | Yes. | The recommended candidate must start with source-contract and context planning before any implementation, and must attach plugin-like if later implemented. |
| Does this separate context-only information from executable signal? | Yes. | Funding rate is explicitly classified as context / diagnostics / regime information, not an entry signal or standalone readiness trigger. |
| Does this avoid generated JSON creation or commit? | Yes. | This PR creates no generated packet or sampling JSON and records no raw smoke artifacts. |
| Does this avoid private API, credentials, orders, alerts, or Council auto-call? | Yes. | The decision requires public-read-only planning and does not add private endpoints, secrets, account lookup, orders, alerts, execution, or Council auto-call. |

## Strategy Selection Rubric Applied

The rubric from `docs/strategy_module_boundaries.md` was applied to each candidate. The highest priority candidate should:

- Start from public-read-only data.
- Avoid private API, credentials, account/balance/position lookup, orders, transfers, withdrawals, deposits, alerts, execution engines, and auto-trading.
- Reuse the current Venue Data / Parser / Packet / Readiness / Sampling / Handoff / Dashboard flow.
- Attach as a plugin-like strategy or context module without contaminating shared modules.
- Have a clear source contract and deterministic mocked fixture path.
- Support sampling evidence that can separate no-edge from possible-edge.
- Preserve context-vs-signal boundaries.
- Reduce or explicitly label top-of-book / liquidity illusion risk.
- Preserve timestamp, data_age, and clock-skew watch items.
- Feed manual dashboard / Council handoff without triggering Council auto-call.
- Remain experimental / non-active / `NO_TRADE_ONLY` until explicit human approval changes status.

## Candidate Comparison Table

| candidate strategy id | primary purpose | required public data | private API needed? | existing module reuse possible? | new source contract needed? | parser/adapter expected complexity | deterministic mocked fixture possible? | sampling evidence possible? | can start context-only? | executable-signal misunderstanding risk | top-of-book / liquidity illusion risk | timestamp / data_age / clock-skew watch needed? | dashboard / Council handoff possible? | active promotion ban maintainable? | recommended rank | select / defer / exclude reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `funding_rate_context_v0` | Add derivatives funding-rate regime context for future strategy review and for possible context support around `spot_futures_basis_v0` or derivatives strategy families. | Public funding-rate, predicted/current funding, funding interval/time, symbol/product metadata, and timestamp/data_age fields after a later source-research PR. | No. Must remain public-read-only. | High. Can reuse source-contract planning, diagnostics context, packet/candidate extension pattern, sampling summary pattern, handoff evidence, and dashboard watch-item pattern. | Yes, but initially as context-only fields, not executable or readiness fields. | Low to medium. Public endpoint semantics vary by venue, but this is simpler than trade-flow reconstruction and can be researched before implementation. | Yes. Funding payloads and edge cases can be mocked deterministically, including missing funding time, stale timestamps, product mismatch, and venue-specific field names. | Yes. Sampling can summarize funding availability, sign/range/regime persistence, missing fields, and stale data without claiming trade edge. | Yes. This is the strongest context-only fit. | Medium. Funding is often confused with carry/entry signal, so the guardrail must state it is not a standalone `WATCH` / `ENTER` trigger. | Low direct top-of-book risk because it is not orderbook liquidity, but it can be misread as executable basis/carry; must preserve `funding_rate_not_basis`. | Yes. Funding intervals and next funding times require timestamp, data_age, and clock-skew checks. | Yes. Dashboard can show future/proposed context status and Council manual review watch items without auto-call. | Yes, if documented as context-only and non-active. | 1 | Select for next planning PR because it reuses the current derivatives/context evidence direction while minimizing execution-like surface area. |
| `volatility_breakout_v0` | Detect possible breakout regimes from public price/time-series or candle data. | Public klines/candles/trades or ticker history with timestamps. | No for basic public data, but richer quality may tempt private or premium data. | Medium. Can reuse packet/readiness/sampling, but likely needs new time-series source contract and windowing helpers. | Yes. Needs candle/window/volatility field contract. | Medium. Venue candle semantics and interval alignment must be normalized. | Yes. Mocked candles and deterministic volatility windows are feasible. | Yes. Sampling can summarize breakout frequency and false-positive/no-edge outcomes. | Partly. Volatility regime can be context-only, but breakout language strongly suggests signal. | High. Breakout can easily be interpreted as entry signal. | Medium. Breakout without depth/VWAP can overstate executable opportunity. | Yes. Candle close time, interval alignment, and stale data are core risks. | Yes, but Council wording must avoid signal language. | Yes, but riskier than funding context. | 2 | Defer. Feasible, but signal-risk and time-window semantics should wait until context-only funding planning is complete. |
| `trade_flow_momentum_v0` | Evaluate public trade-flow or taker-flow momentum context. | Public recent trades, aggregate trades, taker buy/sell volume if available, timestamps, venue/product metadata. | No for public trades, but accurate participant/order-flow interpretation can tempt private data. | Medium. Can reuse sampling and packet concepts but may require heavier data volume handling. | Yes. Needs trade aggregation, windowing, and flow-field contract. | High. Venue trade feeds, aggregation rules, rate limits, and inferred taker direction differ materially. | Yes, but robust fixtures need many ordered events and edge cases. | Yes, though evidence quality depends on sampling windows and flow semantics. | Partly. Momentum can be context-only, but it is commonly treated as executable signal. | High. Momentum is easily misread as `ENTER` / `WATCH`. | Medium to high. Trade prints do not prove available liquidity or fill feasibility. | Yes. Event ordering and stale/late trades are major risks. | Yes, but review language must be conservative. | Possible, but guardrails must be strong. | 3 | Defer. More complex parser/windowing and higher signal-confusion risk than funding context. |
| `derivatives_flow_context_v0` | Add derivatives market-flow context such as open interest, liquidations, long/short ratio, or related public derivatives regime data. | Public derivatives flow/context endpoints, possibly open interest, liquidation, long/short account ratio, product metadata, timestamps. | No only if limited to public endpoints; some useful versions may require restricted or vendor data. | Medium to high for diagnostics pattern, but source semantics vary widely. | Yes. Needs careful contract separating each context type. | Medium to high. Venue endpoint availability and meaning vary, and fields can be semantically weak or delayed. | Yes, if each context source is mocked separately. | Yes. Can summarize availability, regime persistence, and stale/missing fields. | Yes, if framed strictly as diagnostics. | Medium. Flow context may be interpreted as directional signal. | Low to medium direct orderbook risk, but can create false confidence about executable flow. | Yes. Many derivatives context sources have delayed or interval-based timestamps. | Yes. Good dashboard watch-item candidate. | Yes, with strict non-active status. | 4 | Defer. Useful later, but broader and less tightly scoped than funding context. |
| `mean_reversion_context_v0` | Evaluate whether deviations from reference bands may provide mean-reversion context. | Public price/reference series, spread/basis history, rolling bands, timestamps, venue/product metadata. | No for public prices, but robust reference construction may tempt broader data dependencies. | Medium. Can reuse packet/sampling, but needs historical windows and reference-band policy. | Yes. Needs reference window, band, z-score/deviation, and stale-history contract. | Medium to high. Historical window alignment and reference-quality policy are non-trivial. | Yes. Deterministic time-series fixtures are possible. | Yes. Sampling can separate persistent/no-edge from candidate deviations. | Partly. It can be context-only, but mean-reversion naturally suggests trade direction. | High. Mean-reversion is easily mistaken for entry signal. | Medium. Price deviation alone does not prove fill feasibility. | Yes. Window freshness and reference staleness are central. | Yes, but wording must avoid trade recommendation. | Possible, but risky. | 5 | Defer. Valuable later, but higher strategy-signal semantics risk and more historical-policy complexity. |

## Recommended Candidate

Recommended next experimental strategy planning candidate: `funding_rate_context_v0`.

This recommendation is only a planning decision. It does not implement funding endpoints, parser logic, adapter logic, packet builder logic, readiness logic, sampling collectors, dashboard automation, Council packets, alerts, execution, or active promotion.

## Why This Candidate Is First

`funding_rate_context_v0` is ranked first because it best fits the current project constraints:

- It can plausibly begin with public-read-only source research.
- It builds on the existing derivatives-context work around `mark_orderbook_gap_hunt_v0` and `spot_futures_basis_v0`.
- It can start as context / diagnostics / regime information without claiming a trade edge.
- It can reuse the Depth/VWAP precedent: attach context to packet/candidate extensions or sampling summaries without changing readiness.
- It has a clear no-trade guardrail: funding rate is not basis, not executable price, not an entry signal, and not active-promotion evidence.
- It can be tested with deterministic mocked fixture payloads before any live public endpoint collection is considered.
- It can produce useful dashboard/Council manual-review watch items without Council auto-call or alerts.

The decisive reason is not that funding rate is a stronger trading signal. The decisive reason is that it is the safest next context-planning candidate under the module-boundary rubric.

## Why Other Candidates Are Deferred

- `volatility_breakout_v0` is deferred because breakout terminology and thresholding are easily misread as directional trade signals. It also requires careful candle/window alignment before it can be safely treated as context-only.
- `trade_flow_momentum_v0` is deferred because public trade-flow parsing and windowing are more complex, event ordering matters, and momentum framing carries high executable-signal confusion risk.
- `derivatives_flow_context_v0` is deferred because it is broader than funding context and would likely include multiple semantically different data sources such as open interest, liquidation, and long/short ratio. It should be split only after simpler funding context rules are established.
- `mean_reversion_context_v0` is deferred because reference-band construction, historical window quality, and deviation semantics can quickly become strategy-signal policy rather than diagnostics.

None of these candidates are excluded permanently. They are deferred until the project has stronger context-vs-signal conventions, fixture patterns, and dashboard semantics for new strategy families.

## Context vs Signal Guardrail

This decision preserves the separation between context-only information and executable signal.

Context-only information may support reviewer understanding, diagnostics, regime labeling, watch items, or manual Council review. It must not automatically change:

- Readiness status.
- `recommended_default_decision`.
- Estimated net gap or basis.
- Persistence status.
- Council recommendation.
- Active strategy status.
- Alert behavior.
- Execution behavior.

Any future proposal to let a context field affect readiness must first go through a separate policy-planning PR with explicit human approval, risk analysis, deterministic tests, dashboard semantics, and no-trade compliance.

## Funding Rate Context Guardrail

Because `funding_rate_context_v0` is the recommended next candidate, these guardrails are mandatory for the next PR:

- Funding Rate is not an entry signal.
- Funding Rate is not a standalone `WATCH` trigger.
- Funding Rate is not a standalone `ENTER` trigger.
- Funding Rate is not active promotion evidence.
- Funding Rate starts only as context / diagnostics / regime information.
- Funding Rate may be reviewed only as auxiliary context for `spot_futures_basis_v0` or other derivatives-oriented strategy families.
- Funding Rate must preserve `NO_TRADE_ONLY`.
- Funding Rate must not change readiness, `recommended_default_decision`, persistence, Council handoff status, active status, alert behavior, or execution behavior without a separate explicitly approved policy PR.
- Public endpoint/source research belongs in the next PR and must remain public-read-only.
- Endpoint implementation, parser implementation, adapter implementation, packet builder implementation, readiness implementation, and sampling collector implementation are not part of this PR.

## No-Trade Compliance

`NO_TRADE_ONLY` is preserved.

This PR adds no:

- Private API.
- API key, secret, token, OAuth token, bot token, or webhook secret.
- Account, balance, or position lookup.
- Order placement or cancellation.
- Withdrawal, deposit, or transfer behavior.
- Auto-trading or execution engine.
- Alert execution.
- Council auto-call.
- Council decision to trade conversion.
- Active strategy promotion.
- Funding Rate endpoint, parser, adapter, or packet-builder implementation.
- VWAP-adjusted readiness implementation.

## Behavior Unchanged

Runtime behavior is unchanged. This PR only adds one decision handoff document.

No files under `src/`, `tests/`, `config/`, `configs/`, `tools/`, `data/generated_packets/`, or `data/market_samples/` were modified. No registry/config/active strategy file was modified. The active strategy remains `cross_exchange_spot_spread_v1`; all experimental and future strategies remain non-active unless a separate approved PR changes status.

## Generated Artifact Policy

No generated packet JSON or market-sampling JSON was created or committed. Generated JSON remains a smoke artifact and is not source-of-truth for dashboard or handoff evidence.

## Validation

Validation commands required for this docs-only PR:

- `git status --short --branch`
- `git diff --name-only`
- `git diff --name-only -- src tests config configs tools data/generated_packets data/market_samples`
- `find data/generated_packets data/market_samples -type f -name '*.json'`
- `git diff --check`
- `python -m unittest discover -s tests`

Validation result summary:

- Fresh `origin/main` branch creation was attempted but could not complete because GitHub fetch failed in this environment with `CONNECT tunnel failed, response 403`.
- Work was performed on `docs/next-experimental-strategy-selection-finalization-v0` from the available repository state.
- Only the allowed handoff file was changed.
- Forbidden source/test/config/tool/generated-data paths were not modified.
- No generated JSON artifact was created or committed.
- `git diff --check` passed.
- Full unittest discovery passed: `Ran 531 tests in 15.588s`, `OK`.

## Next Recommended Step

Next recommended PR: `Funding Rate Context Strategy Planning v0`.

That next PR should still be planning-first, public-read-only, and context-only. It should research public funding-rate source options and define source-contract/fixture/dashboard semantics before any endpoint, parser, adapter, packet builder, readiness, sampling collector, alert, Council auto-call, execution, or active-promotion work is considered.
