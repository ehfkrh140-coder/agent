# Strategy Task Card Draft: Orderbook Imbalance

## Task name
Add minimal experimental scaffolding for orderbook_imbalance without changing the active strategy.

## Strategy family
`orderbook_imbalance`

## Goal
Define a read-only experimental signal that compares bid-side and ask-side public orderbook depth to identify imbalance pressure or thin-book illusion. This remains non-active and is not an executable spread.

## Current status
Experimental scaffolding. It is not active; `cross_exchange_spot_spread_v1` remains the only active strategy.

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
No live adapter changes, no active strategy changes, no exchange API additions, no private endpoint, order, balance, withdrawal, transfer, or auto-trading implementation.

## Tests
Schema-valid manual scenarios, experimental readiness checks, evaluate-only smoke, and no-trade guardrail tests.

## Manual smoke
None for this draft.

## Success criteria
orderbook_imbalance is represented as experimental scaffolding in docs, registry, scenarios and readiness while remaining non-active.

## Non-goals
Do not implement live adapters, active promotion, alerts, handoff, Council automation, private APIs, or execution features from this scaffolding.
