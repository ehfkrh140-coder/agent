# Strategy Task Card Draft: Kimchi Premium

## Task name
Prepare kimchi_premium data requirements for experimental review.

## Strategy family
`kimchi_premium`

## Goal
Define a read-only framework for comparing domestic KRW spot prices with global USD/USDT-referenced prices after public FX or USDT-KRW conversion. This is planning only.

## Current status
Future. It needs currency conversion policy and multi-market normalization before any implementation.

## Data required
Domestic spot bid/ask/depth, global spot bid/ask/depth, public FX or USDT-KRW reference, fees, timestamps, latency, data age, source provenance and liquidity metadata.

## Data forbidden
Private API, API key / secret / token, balance/account lookup, order placement/cancel, withdrawal/deposit/transfer, auto-trading, and Council decision to trade conversion.

## OpportunityPacket shape
Observations would separate domestic and global venues and include conversion reference observations. Candidates would include premium_pct, conversion_source, source/target bid/ask basis, freshness and liquidity gates.

## Readiness rules
NEED_DATA when conversion, bid/ask/depth or timestamps are missing; REJECT when stale or net premium is cost-negative; WATCH only for fresh, public, conversion-verified premium observations. ENTER remains analysis-only and not an order instruction.

## Scenarios
Missing FX reference, positive/watch premium, high-fee/reject, stale conversion/reject, low-liquidity/reject.

## Allowed files
Future docs/tests first; implementation files only after explicit user approval.

## Forbidden files
No source/config/scenario changes in this draft. No private data, transfer assumptions, balance checks, order placement, withdrawal, transfer, or auto-trading.

## Tests
Document existence and no-trade compliance now; future work requires schema, readiness and evaluate-only tests.

## Manual smoke
None for this draft.

## Success criteria
Data requirements are clear enough to decide whether to begin experimental scenario design.

## Non-goals
Do not implement adapters, currency conversion code, strategy logic, scenarios, alerts, handoff, or Council automation from this draft.
