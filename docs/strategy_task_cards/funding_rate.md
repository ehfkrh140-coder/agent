# Strategy Task Card Draft: Funding Rate

## Task name
Prepare funding_rate for derivatives-only experimental documentation review.

## Strategy family
`funding_rate`

## Goal
Define a read-only derivatives signal based on public funding rates and next funding times. It must remain separate from the active spot-only strategy.

## Current status
Future. Public derivatives data requirements must be documented before any code or live adapter work.

## Data required
Public funding rate, next funding time, mark/index price if public, contract symbol, instrument type, timestamp, data age, venue health and optional open interest if public.

## Data forbidden
Private API, API key / secret / token, balance/account lookup, order placement/cancel, withdrawal/deposit/transfer, auto-trading, and Council decision to trade conversion.

## OpportunityPacket shape
Observations would represent derivative venues/contracts. Candidates would include funding_rate_pct, next_funding_time_utc, rate differential if cross-venue, freshness gates, and assumptions in metrics/extensions.

## Readiness rules
NEED_DATA when rate/time/timestamp is missing; REJECT when stale or unsupported; WATCH only for fresh public funding signals that pass deterministic gates. ENTER remains analysis-only and not an instruction to open positions.

## Scenarios
Missing funding time, positive/watch rate, stale-data/reject, unsupported contract/reject, noisy public data/NEED_DATA.

## Allowed files
Future docs/tests first; implementation files only after explicit user approval.

## Forbidden files
No source/config/scenario changes in this draft. No private derivatives endpoints, position checks, leverage actions, order placement, balance lookup, withdrawal, transfer, or auto-trading.

## Tests
Document existence and no-trade compliance now; future work requires schema/readiness/evaluate-only tests.

## Manual smoke
None for this draft.

## Success criteria
A reviewer can decide whether funding_rate should proceed to experimental scenario and readiness design.

## Non-goals
Do not implement derivatives adapters, readiness code, scenarios, alerts, handoff, or Council automation from this draft.
