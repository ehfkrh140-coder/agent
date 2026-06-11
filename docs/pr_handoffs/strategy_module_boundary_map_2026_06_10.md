# Strategy Module Boundary Map v0 Handoff

## Summary

This PR is a docs-only planning update for `Strategy Module Boundary Map v0 + Next Experimental Strategy Selection Criteria v0`. It adds a strategy module boundary map and strategy-selection rubric before choosing or implementing the next experimental strategy.

This PR does not implement a new strategy. It does not implement Funding Rate Context Strategy, VWAP-adjusted readiness, endpoint research, adapters, parsers, packet builders, readiness code, sampling code, dashboard generation, alerts, Council auto-call, execution, or active promotion.

## Why This Is Not a Restart

This is not a restart or a rejection of the existing project direction. The current project already has a working read-only evidence flow:

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

The new boundary document preserves that flow and labels its layers so future strategy work can be additive, scoped, and reviewable. Existing adapter, parser, packet, readiness, sampling, dashboard, and handoff patterns remain the intended path.

## Files Changed

- Added `docs/strategy_module_boundaries.md`.
- Added `docs/pr_handoffs/strategy_module_boundary_map_2026_06_10.md`.

No `src/`, `tests/`, `configs/`, `tools/`, `data/generated_packets/`, `data/market_samples/`, generated JSON, credential, private API, execution, alert, or order-related files were modified.

## Design Decisions

- Treat strategy families as plugin-like units with explicit metadata, source contracts, packet/candidate builders, readiness policy, diagnostics context, sampling plan, dashboard row, and handoff evidence.
- Keep Venue Data Layer limited to read-only public market data collection and raw payload handling.
- Keep Venue Parser Layer limited to venue-specific normalization and diagnostics, not strategy edge judgment.
- Keep Strategy Source Contract Layer responsible for required/optional/context-only field semantics.
- Keep Readiness Layer deterministic and independent from sampling summaries or Council judgment.
- Keep Context / Diagnostics Layer diagnostics-only by default, following the existing Depth/VWAP precedent.
- Keep Sampling / Evidence Layer focused on summarized persistence/no-edge evidence, with raw generated JSON treated as non-committed smoke artifacts.
- Keep Dashboard / Council Handoff Layer as evidence inventory and manual-review status only, not trading signal or execution permission.
- Keep Governance Layer responsible for `NO_TRADE_ONLY`, merge gate, rollback, generated artifact policy, handoff source-of-truth, and human-review boundaries.

## Strategy Selection Rubric

Next experimental strategy selection should prefer a candidate that satisfies the following rubric:

- Can start from public-read-only data.
- Does not require private API, credentials, account lookup, balance lookup, position lookup, order placement, cancellation, transfers, withdrawals, deposits, alert execution, or auto-trading.
- Reuses the existing Venue Data / Parser / Packet / Readiness / Sampling / Handoff / Dashboard flow.
- Attaches as a plugin-like strategy without polluting shared modules or changing active baseline behavior.
- Has a clear source contract with required, optional, context-only, and unsupported fields.
- Can be tested with deterministic mocked fixtures.
- Can produce sampling evidence that distinguishes no-edge from possible-edge.
- Does not confuse context-only information with executable signal.
- Addresses top-of-book liquidity and fill-feasibility illusion through explicit diagnostics or policy notes.
- Preserves timestamp, clock-skew, and data-age watch items.
- Can be represented in the dashboard and Council manual review process without Council auto-call.
- Can remain experimental / non-active / `NO_TRADE_ONLY` until explicit human approval changes status.
- Avoids generated JSON commits and records only summarized evidence in handoff docs.

## Funding Rate Context Placement

`funding_rate_context_v0` remains a plausible next experimental candidate, but this PR does not implement it.

The planned placement is:

- Strategy identity: future / proposed `funding_rate_context_v0`.
- Primary layer: Context / Diagnostics Layer.
- Possible integration points: Strategy Source Contract Layer for derivatives-oriented strategies, packet/candidate extensions, Sampling / Evidence summaries, and Dashboard / Council watch items.
- Initial semantics: funding rate is context / diagnostics / regime information.
- Explicit non-goal: funding rate is not an entry signal, not basis by itself, not a standalone `WATCH` / `ENTER` trigger, and not active-promotion evidence by itself.
- Future work: public endpoint research and any fixture/parser planning should happen in a separate PR.

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

## Behavior Unchanged

Runtime behavior is unchanged. This PR only adds planning documentation.

No files under `src/`, `tests/`, `configs/`, `tools/`, `data/generated_packets/`, or `data/market_samples/` were modified. The active strategy remains `cross_exchange_spot_spread_v1`, and all experimental/future strategies remain non-active unless a separate approved PR changes that status.

## Generated Artifact Policy

No generated packet JSON or market-sampling JSON was created or committed. Generated JSON remains a smoke artifact and is not source-of-truth for dashboard or handoff evidence.

## Validation

Validation commands run:

- `git status --short --branch` before work to check the starting branch and cleanliness.
- `git rev-parse --short HEAD` before work to record the starting HEAD.
- `git remote -v` before work to inspect remote configuration.
- `git remote add origin https://github.com/ehfkrh140-coder/agent.git && git fetch origin main && git switch -c docs/strategy-module-boundaries-v0 origin/main` attempted to satisfy the fresh `origin/main` requirement, but fetch failed in this environment with `CONNECT tunnel failed, response 403`.
- `git switch -c docs/strategy-module-boundary-map-v0` to create a scoped work branch from the available workspace state after the network fetch failed.
- `git status --short` after edits to confirm only allowed docs files changed.
- `git diff --name-only -- src tests config configs tools data/generated_packets data/market_samples` to confirm forbidden source/test/config/tool/generated-data paths were not modified.
- `find data/generated_packets data/market_samples -type f -name '*.json'` to inspect generated JSON artifact paths.
- `python -m unittest discover -s tests` to run the repository test suite even though this is docs-only.

Validation result summary:

- Only allowed files were changed.
- No forbidden source/test/config/tool/generated-data paths were modified.
- No generated JSON was created or committed by this PR.
- Full unittest discovery passed in this environment: `Ran 531 tests in 15.421s`, `OK`.
- Fresh `origin/main` verification could not be completed because the network fetch to GitHub was blocked by the environment.

## Next Recommended Step

Recommended next step: `Next Experimental Strategy Selection finalization v0` as a short docs-only decision PR that applies the rubric from `docs/strategy_module_boundaries.md` to the candidate list and confirms whether `funding_rate_context_v0` should proceed to a separate planning PR.

If that finalization confirms Funding Rate Context as the next candidate, then the following PR should be `Funding Rate Context Strategy Planning v0`. That later PR should remain planning-first, public-read-only, context-only, and should not implement endpoints until its source contract, fixture plan, no-trade guardrails, and dashboard semantics are approved.
