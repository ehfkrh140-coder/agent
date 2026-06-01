# Project Roadmap

## Completed
1. Gemini CLI 5-agent runtime.
2. JSON hardening.
3. Single Round Council v1.
4. OpportunityPacket v0.
5. Strategy registry/readiness.
6. Upbit/Bithumb public adapter.
7. VWAP/slippage evaluator.
8. Repeated sampling/persistence.
9. Council handoff/journal.
10. Alert/notification v1.

## Next TODO
1. Market Watch Runner v1.
2. Scheduler / Watch Loop v1.
3. Paper Decision Journal / Backtest-lite v1.
4. Multi-venue expansion.
5. WebSocket data freshness upgrade.
6. Council auto-review option, default off.
7. Strategy expansion one-by-one.

## Guardrails for all TODOs
- Every TODO starts as read-only by default.
- Execution/private API support is a future gated phase and is currently forbidden.
- New strategies should be introduced one at a time with schema, fixtures, readiness rules, tests, and documentation before any live workflow.
- Council auto-review must be default off if it is ever added.
