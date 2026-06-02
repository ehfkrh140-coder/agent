# Architecture Status

## Current data flow
```text
public market data
-> OpportunityPacket
-> VWAP/readiness
-> sampling/persistence
-> handoff/journal
-> alert
-> optional manual Council
```

## Current implemented areas
- Public read-only market data adapters and replay fixtures.
- OpportunityPacket v0 schema and scenario loading.
- Cross-exchange spot spread builder using source ask / target bid and VWAP metrics.
- Strategy readiness checks for the active spot strategy.
- Repeated sampling and persistence summaries.
- Council handoff packet generation only for `PERSISTENT_READY_EDGE`.
- Opportunity journal and alert log append-only storage.
- Optional manual Single Round Council v1 analysis.

## Not implemented
- Execution engine.
- Private account data.
- Balance lookup.
- Order placement or cancellation.
- Withdrawal.
- Deposit or transfer.
- Auto trading.
- v2 multi-round debate.

## Active and non-active strategies
- Active: `cross_exchange_spot_spread_v1`.
- Experimental/disabled: `mark_orderbook_gap`.
- Future strategies remain registry/catalog entries until a task explicitly promotes one.
