# Strategy Task Card Draft: Orderbook Imbalance

## Task name
Prepare orderbook_imbalance for experimental documentation review.

## Strategy family
`orderbook_imbalance`

## Goal
Define a read-only signal that compares bid-side and ask-side public orderbook depth to identify imbalance pressure. This is a future/experimental preparation card, not an implementation request.

## Current status
Future. It is a recommended next candidate because Upbit/Bithumb public orderbook depth is already collected for the active spot strategy.

## Data required
Public bid/ask levels, level sizes, spread, depth notional by side, timestamp, latency, data age, venue health and fee context if used in candidate scoring.

## Data forbidden
Private API, API key / secret / token, balance/account lookup, order placement/cancel, withdrawal/deposit/transfer, auto-trading, and Council decision to trade conversion.

## OpportunityPacket shape
Observations would reuse public depth levels. Candidates would describe imbalance direction and metrics such as bid_depth_notional, ask_depth_notional, imbalance_ratio, spread_pct, freshness and liquidity gates.

## Readiness rules
NEED_DATA when depth/timestamp/latency is missing; REJECT when stale or too shallow; WATCH only when public depth is fresh and imbalance persists. ENTER remains forbidden as execution and may only mean analysis-stage candidate if retained.

## Scenarios
Missing depth, balanced book, positive/watch imbalance, stale-data reject, low-liquidity reject.

## Allowed files
Future documentation, tests, and later explicitly approved scenario/readiness files.

## Forbidden files
No source/config/scenario changes in this draft. No exchange API, private endpoint, order, balance, withdrawal, transfer, or auto-trading implementation.

## Tests
Document existence and key no-trade phrases now; future implementation must add schema/readiness/evaluate-only tests.

## Manual smoke
None for this draft.

## Success criteria
A reviewer can decide whether to promote orderbook_imbalance from future to experimental documentation work.

## Non-goals
Do not implement strategy code, readiness code, adapters, configs, scenarios, alerts, handoff, or Council automation from this draft.
