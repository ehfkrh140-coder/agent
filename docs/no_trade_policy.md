# No-Trade Policy

This project is currently a read-only analysis system. It may collect and transform public market data, build OpportunityPackets, run deterministic readiness checks, sample spread persistence, write journals/alerts, and optionally send data to the AI Council for manual analysis.

## Allowed
- Read-only public market data access.
- Replay fixtures and deterministic test data.
- OpportunityPacket creation and validation.
- VWAP, slippage, readiness, sampling, persistence, handoff, journal, and alert calculations.
- Manual Council analysis on an OpportunityPacket.

## Forbidden
- Private exchange endpoints.
- API keys, API secrets, OAuth tokens, bot tokens, or webhook secrets for trading/notification execution.
- Account or balance lookup.
- Order placement or cancellation.
- Withdrawal, deposit, or transfer actions.
- Auto-trading, execution engines, or persistent order loops.
- Any code path that turns a Council decision into a trade.

## Council decision meaning
Council output is analysis only. `ENTER`, if it appears, means only an analysis-stage candidate classification. It is not a real order instruction, not permission to submit an order, and not a recommendation to transfer funds.
