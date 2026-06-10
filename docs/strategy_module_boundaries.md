# Strategy Module Boundaries

## Purpose

This document defines the planning-only module boundaries for adding and comparing strategy families in the AI Council read-only market-candidate validation system. Its goal is to make future experimental strategies additive and reviewable without allowing strategy-specific logic to leak into shared infrastructure, governance policy, Council handoff, or execution-like behavior.

The current project remains a `NO_TRADE_ONLY` research and evidence system. Strategies may transform public market data into `OpportunityPacket` records, candidate metrics, deterministic readiness outputs, sampling summaries, and review evidence. They must not place orders, trigger alerts, call Council automatically, promote themselves to active status, or imply execution permission.

## Non-Goals

This document is not any of the following:

- It is not a code refactor.
- It is not a new strategy implementation.
- It does not implement Funding Rate Context Strategy.
- It does not implement VWAP-adjusted readiness.
- It does not change `cross_exchange_spot_spread_v1` as the active baseline.
- It does not promote any experimental or future strategy to active status.
- It does not add or call live endpoints.
- It does not create generated packet or market-sampling JSON artifacts.
- It does not add private API access, credentials, account/balance/position lookup, orders, transfers, withdrawals, deposits, alerts, auto-trading, or Council auto-call behavior.

## Current Pipeline

The current strategy evidence pipeline is preserved as:

```text
public market data adapter
→ venue-specific parser / normalized observation
→ OpportunityPacket
→ readiness helper
→ packet/candidate metrics
→ sampling summary
→ docs/pr_handoffs evidence
→ strategy_evidence_dashboard
→ Council manual review criteria
```

This document does not replace that pipeline. It names the boundaries that future planning and implementation PRs should respect.

## Module Boundary Map

| Layer | Primary responsibility | Allowed inputs | Allowed outputs | Forbidden behavior |
| --- | --- | --- | --- | --- |
| Venue Data Layer | Fetch or receive read-only public market data and preserve raw venue payloads for downstream parsing. | Public market endpoints explicitly approved for the task; deterministic fixture payloads. | Raw payloads plus minimal collection metadata such as venue, symbol, product type, and observed timestamp. | Strategy edge judgment, readiness judgment, Council judgment, execution judgment, private endpoints, credentials, account/balance/position lookup, orders, transfers, withdrawals, deposits, alerts, auto-trading, or Council auto-call. |
| Venue Parser Layer | Convert venue-specific raw payloads into normalized observations while absorbing Binance / Bybit / OKX response-shape differences. | Raw payloads from the Venue Data Layer or fixtures. | Normalized observations with parsed fields, parser diagnostics, missing-field notes, and venue/product semantics. | Strategy edge judgment, readiness status assignment, Council recommendation, active promotion, execution permission, or silent semantic coercion when product/reference meanings differ. |
| Strategy Source Contract Layer | Define the normalized observation fields a strategy requires or may consume. | Normalized observations and documented field semantics. | A strategy-specific source contract describing required fields, optional fields, context fields, and unsupported fields. | Adding code fields in a docs-only PR, hiding missing data, treating context-only fields as executable signals, or requiring private/account/order data. |
| Strategy Plugin Layer | Define strategy metadata and strategy-specific packet/candidate construction. | Source-contract-compliant normalized observations and diagnostics context. | `OpportunityPacket`, candidate metrics, strategy metadata, default non-execution recommendation metadata, and handoff-ready evidence fields. | Orders, alerts, Council auto-call, active promotion, private API use, shared module pollution, or changing active baseline behavior as a side effect. |
| Readiness Layer | Compute deterministic readiness states such as `NEED_DATA`, `REJECT`, and `WATCH`. | Packet/candidate fields defined by the strategy contract and approved readiness policy. | Readiness status, missing-field lists, deterministic reasons, and default review classification. | Reinterpreting readiness based on sampling outcomes or Council judgment, using context-only diagnostics to change readiness without explicit policy approval, or implying `WATCH` equals `ENTER`. |
| Context / Diagnostics Layer | Attach non-execution context such as Depth/VWAP, funding rate, timestamp/clock-skew, mark/index reference, and data-age diagnostics. | Normalized observations, packet/candidate context inputs, deterministic fixture context, and approved public context sources. | `packet.extensions` or `candidate.extensions` diagnostics, warning counts, context summaries, and watch items. | Automatically changing readiness, `recommended_default_decision`, active status, Council status, alerts, execution permission, or treating reference/context values as executable prices. |
| Sampling / Evidence Layer | Repeat read-only collection or fixture replay, summarize persistence/no-edge evidence, and write reviewable summaries. | Public-read-only observations, packets, candidates, readiness outputs, deterministic fixtures, and diagnostics context. | Summary metrics, persistence/no-edge evidence, test output summaries, and `docs/pr_handoffs` evidence. | Committing raw generated JSON smoke artifacts, mutating strategy policy based on samples without review, calling private endpoints, executing trades, or treating no-edge as a system failure. |
| Dashboard / Council Handoff Layer | Maintain evidence inventory and manual Council review status. | Handoff evidence summaries, strategy metadata, sampling summaries, and policy notes. | `strategy_evidence_dashboard` rows, Council handoff status, watch items, and next-action notes. | Trading signals, execution permission, active promotion, Council auto-call, alerts, or direct use of generated JSON as source-of-truth. |
| Governance Layer | Define and enforce `NO_TRADE_ONLY`, merge gate, rollback, generated artifact guardrails, PR handoff evidence, and human-review boundaries. | Repository policies, task instructions, PR template, handoff docs, and review evidence. | Scope constraints, rollback instructions, no-trade compliance statements, merge criteria, and human-review requirements. | Allowing forbidden trading/private API behavior, accepting unrelated file changes, skipping required evidence without reason, or claiming high-risk changes are safe without human review. |

## Strategy Plugin Contract

A new strategy should be planned as a plugin-like unit with explicit metadata and boundaries. At minimum, each strategy should define:

- `strategy_family`: stable family name, for example `spot_futures_basis`.
- `strategy_id`: stable versioned ID, for example `spot_futures_basis_v0`.
- `lifecycle_status`: active baseline, experimental, proposed, future, deferred, archived, or equivalent documented status.
- `execution_policy`: currently `NO_TRADE_ONLY` for all strategies in this project.
- `source_contract`: required, optional, context-only, and explicitly unsupported normalized observation fields.
- `packet_builder`: strategy-specific construction of `OpportunityPacket` fields from source-contract inputs.
- `candidate_builder`: strategy-specific candidate metrics and diagnostics fields.
- `readiness_policy`: deterministic readiness rules and reasons, including `NEED_DATA`, `REJECT`, and `WATCH` semantics.
- `diagnostics_context`: context-only extensions such as Depth/VWAP, funding rate, timestamp/clock-skew, mark/index references, and watch items.
- `sampling_plan`: read-only collection or fixture-replay plan, target sample counts, persistence/no-edge metrics, and artifact policy.
- `dashboard_row`: manual dashboard fields, Council handoff status, watch items, and next action.
- `handoff_doc`: durable task-specific evidence under `docs/pr_handoffs/` when needed.

The plugin contract is an architectural planning boundary, not a permission to modify shared modules. Implementation PRs should be additive, scoped, and backed by deterministic tests and handoff evidence.

## Context vs Signal Policy

Context-only information must remain separate from executable signals and execution permission.

Depth/VWAP is the current reference precedent. Depth/VWAP context can be attached to packet or candidate extensions and summarized by sampling, but it currently does not change readiness, estimated net gap/basis, persistence status, Council recommendation, active status, alerts, or execution behavior.

Funding Rate Context should follow the same conservative starting policy:

- Funding rate is not an entry signal.
- Funding rate is not a standalone `ENTER` or `WATCH` trigger.
- Funding rate is a context / diagnostics / regime-information candidate.
- Funding rate may later provide context for `spot_futures_basis_v0` or derivatives-oriented strategy families.
- Funding rate must not cause active promotion, alert execution, Council auto-call, order placement, or readiness changes without separate policy planning and explicit approval.
- Public endpoint research for funding data belongs in a future PR and must remain public-read-only.

A strategy may use context fields for reviewer visibility only when the field semantics, limitations, and non-execution meaning are documented.

## Readiness Boundary

Readiness is deterministic strategy-policy evaluation. It should answer whether the packet has enough data and whether the strategy-specific candidate passes the approved readiness thresholds for review classification.

Readiness owns:

- `NEED_DATA`, `REJECT`, `WATCH`, or equivalent deterministic statuses.
- Required missing fields.
- Deterministic reason codes and watch items.
- Preservation of strategy-specific semantics such as mark price not being executable and funding rate not being basis.

Readiness does not own:

- Sampling persistence summaries.
- Council manual judgment.
- Active strategy promotion.
- Alerts, orders, or execution behavior.
- Reinterpreting `WATCH` as `ENTER`.
- Treating `REJECT` or `NO_PERSISTENT_EDGE` as implementation failure when parser/data contracts are otherwise satisfied.
- Letting context-only diagnostics modify readiness without separate policy planning and explicit approval.

If a future PR proposes that a context-only field, such as VWAP-adjusted price or funding regime, should affect readiness, it must first create a policy-planning PR that explains the field semantics, risk, tests, dashboard impact, and no-trade boundary.

## Sampling / Evidence Boundary

Sampling and evidence are review-support layers. They can repeatedly collect public-read-only observations or replay deterministic fixtures, build packets/candidates, run readiness, and summarize persistence/no-edge evidence.

Sampling owns:

- Sample counts and collection windows.
- Positive/negative candidate counts.
- Persistence/no-edge summaries.
- Diagnostics summary counts such as Depth/VWAP context seen, insufficient depth, slippage context, timestamp/data-age warnings, and missing-field counts.
- Handoff evidence summaries under `docs/pr_handoffs/`.

Sampling does not own:

- Active promotion.
- Execution permission.
- Council auto-call.
- Alert execution.
- Readiness semantics changes.
- Generated JSON as source-of-truth.

Generated packet and market-sampling JSON files are smoke artifacts and must not be committed unless a future task explicitly changes that policy with human approval. Handoff docs should record summarized evidence, not raw generated artifacts.

## Dashboard / Council Boundary

The dashboard and Council handoff layer is evidence inventory and manual-review routing only.

The dashboard may record:

- Strategy status and active/non-active status.
- Venue coverage.
- Latest evidence status.
- 30x evidence status when available.
- Persistence status.
- Council handoff status.
- Depth/VWAP or other diagnostics status.
- Watch items.
- Current recommendation and next action.
- Source handoff paths.

The dashboard and Council handoff layer must not imply:

- Trading signal.
- Execution permission.
- Active promotion.
- Council auto-call.
- Alert execution.
- Order placement.
- Private API/account feasibility.
- `MANUAL_REVIEW_CANDIDATE` equals `ENTER`.
- `WATCH` equals `ENTER`.
- `REJECT` equals failure.

Council outputs are analysis only. They must not be converted into trades or treated as instructions for orders, transfers, withdrawals, deposits, alerts, or active promotion.

## Existing Strategy Compatibility Map

| Strategy | Current status | Boundary mapping | Compatibility notes |
| --- | --- | --- | --- |
| `cross_exchange_spot_spread_v1` | Active baseline / `NO_TRADE_ONLY`. | Existing active baseline strategy with governance-protected status. | This boundary map does not change active strategy behavior, execution policy, or config. Future experimental strategies must not modify this baseline unless explicitly approved. |
| `mark_orderbook_gap_hunt_v0` | Experimental / non-active / `NO_TRADE_ONLY`; Binance / Bybit / OKX baseline complete. | Venue data/parser normalize derivatives mark/orderbook context; strategy plugin evaluates mark-vs-orderbook candidate metrics; readiness and sampling remain deterministic no-trade evidence. | Mark price is not executable. Top-of-book is not fill feasibility. Current evidence remains no-edge/archive plus policy review, not active promotion. |
| `spot_futures_basis_v0` | Proposed / experimental / non-active / `NO_TRADE_ONLY`; Binance + Bybit complete; OKX deferred. | Source contract includes spot reference, futures/perp reference, mark/index/funding context, top-of-book, and optional Depth/VWAP diagnostics. | Depth/VWAP context is supported in packet/candidate extensions and sampling summaries, but readiness is unchanged. Positive persistent edge was not established in summarized baseline. |
| `usdt_krw_global_reference_v0` | Experimental / non-active / `NO_TRADE_ONLY`. | Reference/context strategy that depends on domestic USDT/KRW and global reference semantics. | Last-price and global-reference semantics are context-sensitive. It should remain non-active and governed by source-contract clarity and evidence handoffs. |
| `orderbook_imbalance_v0` | Experimental / non-active / planning or insufficient evidence status. | Candidate strategy family that would require venue orderbook source contracts, parser clarity, deterministic fixtures, and careful top-of-book/depth policy. | Top-of-book liquidity can create fill-feasibility illusions. Any future implementation should include mocked fixtures and diagnostics before readiness expansion. |
| `funding_rate_context_v0` | Future / proposed candidate. | Context / diagnostics / regime-information candidate that may attach funding context to derivatives-oriented packets or sampling summaries. | Funding rate is not basis, not an entry signal, not a standalone `WATCH` or `ENTER` trigger, and not implemented in this PR. Public endpoint research belongs in a later PR. |

## New Strategy Addition Checklist

Before adding a new strategy, confirm:

- The strategy can start from public-read-only data.
- It does not require private API, credentials, account, balance, position, order, transfer, withdrawal, deposit, alert execution, or auto-trading.
- It can reuse the existing Venue Data, Parser, Packet, Readiness, Sampling, Handoff, Dashboard, and Council manual-review flow.
- It can be attached as a plugin-like strategy without polluting shared modules or changing active baseline behavior.
- Its source contract clearly separates required fields, optional fields, context-only fields, and unsupported fields.
- Venue parser differences can be covered by deterministic fixtures.
- Mocked fixtures can validate parsing, packet construction, readiness, and diagnostics deterministically.
- Sampling evidence can distinguish no-edge from possible-edge without treating no-edge as adapter failure.
- Context-only information is not confused with executable signal or execution permission.
- Top-of-book liquidity limitations are documented and, where relevant, Depth/VWAP or equivalent diagnostics reduce fill-feasibility illusion.
- Timestamp, clock-skew, and data-age watch items are preserved.
- Dashboard and Council manual-review handoff can represent the strategy without triggering Council auto-call.
- The strategy can remain experimental / non-active unless explicit human approval changes status.
- Generated JSON artifacts are not committed.
- Rollback is clear and limited to additive strategy-specific files or docs.

## Future Refactor Policy

This document does not start a redesign. It documents the boundaries that already exist in the current flow and should guide additive future work.

If future code refactoring becomes necessary, use this order:

1. Write a planning/handoff document that identifies the exact boundary problem and affected files.
2. Confirm no-trade compliance and active strategy preservation.
3. Add or update deterministic fixtures before changing runtime behavior.
4. Refactor one layer at a time, starting with pure helpers or parser contracts rather than runtime orchestration.
5. Keep strategy-specific changes isolated from shared modules unless a shared abstraction is explicitly justified.
6. Run relevant unit tests and full unittest discovery unless explicitly waived with a documented reason.
7. Update handoff evidence and dashboard rows only from summarized evidence, not generated JSON artifacts.
8. Require human review for strategy status changes, risk-policy changes, active promotion, runtime/auth changes, or any execution/private API area.

Future implementation PRs should be additive and scoped to this boundary map. They should not use this document as permission for broad rewrites, live endpoint calls, active promotion, VWAP-adjusted readiness, Funding Rate implementation, or execution-like behavior.
