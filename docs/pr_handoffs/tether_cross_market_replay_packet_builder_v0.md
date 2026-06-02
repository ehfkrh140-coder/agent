# PR Handoff Evidence

- PR number: pending / to be filled after PR creation
- Task name: Tether Cross-Market Replay Packet Builder v0
- Risk class: packet-builder/replay, medium risk
- Task type: packet-builder

## 1. Purpose
Add a replay-fixture OpportunityPacket generation path for the experimental, non-active `tether_cross_market_premium` / `usdt_krw_global_reference_v0` strategy before any live adapter work. The replay path should support deterministic review of Upbit/Bithumb domestic `USDT/KRW` observations and Binance/Bybit/OKX global USDT reference health.

## 2. Changed files
- `src/market_data/packet_builder.py` — add tether cross-market replay packet build support and candidates.
- `data/fixtures/market_data/tether_cross_market_snapshot.json` — add deterministic replay snapshot.
- `configs/market_data.yaml` — add `replay_tether_cross_market_premium` replay adapter config.
- `tests/test_tether_cross_market_replay_packet_builder.py` — add replay packet builder, collect CLI, dry-run context, handoff evidence tests.
- `docs/pr_handoffs/tether_cross_market_replay_packet_builder_v0.md` — add this handoff evidence file.
- `docs/strategy_task_cards/tether_cross_market_premium.md` — note replay packet builder support.
- `README.md` — add replay collect/dry-run example.

## 3. Impact scope
- Adds replay-only packet-builder support for an experimental/non-active strategy.
- Does not change the active strategy.
- Does not change live adapters, probes, prompts, Gemini runtime, sampling/alerts, or strategy current config.
- Does not create Council handoff or auto-call behavior.

## 4. Tests run
Executed commands:
- `python -m unittest tests/test_tether_cross_market_replay_packet_builder.py` — passed, 7 tests OK.
- `python -m unittest discover -s tests` — passed, 233 tests OK.
- `git diff --check` — passed.

## 5. Manual smoke
Executed commands:
- `python tools/collect_market_data.py --adapter replay_tether_cross_market_premium --output data/generated_packets/replay_tether_cross_market_packet.json`
- `python main.py --council --opportunity-file data/generated_packets/replay_tether_cross_market_packet.json --dry-run-context`

Observed result:
- output packet JSON was created;
- dry-run context JSON was created;
- generated smoke artifacts were removed after verification so they are not committed.

Expected packet properties are covered by automated tests:
- `strategy_family=tether_cross_market_premium`;
- `asset=USDT`, `quote=KRW`;
- observations include Upbit, Bithumb, Binance, Bybit, OKX;
- candidates include replay domestic spread directions;
- dry-run context is created without Gemini calls;
- no Council handoff or trading behavior.

## 6. Generated artifacts
- Manual smoke may generate `data/generated_packets/replay_tether_cross_market_packet.json` and a dry-run context JSON under `data/council_sessions/`.
- Generated smoke artifacts are not source files for this PR and should not be committed unless explicitly requested.

## 7. Risks
- Medium risk because packet-builder logic is added for an experimental strategy.
- Replay fixture metrics could be mistaken for live readiness if reviewers ignore the replay-only source metadata.
- Candidate direction/metric calculations must be reviewed carefully because they influence evaluate-only readiness checks.

## 8. Rollback plan
- Revert this PR.
- Rerun `python -m unittest discover -s tests`.
- Verify active strategy remains `cross_exchange_spot_spread_v1`.
- Verify `tether_cross_market_premium` remains experimental/non-active if the rollback should only remove replay packet support.

## 9. Human review required
Reviewers should inspect:
- `src/market_data/packet_builder.py` tether-specific candidate generation;
- `data/fixtures/market_data/tether_cross_market_snapshot.json` fixture shape and no-trade metadata;
- `configs/market_data.yaml` replay adapter config;
- `tests/test_tether_cross_market_replay_packet_builder.py` assertions;
- this handoff file.

Human final approval is required before merge because this is packet-builder/replay medium risk.

## 10. No-trade compliance
- private API: no
- API key/secret/token: no
- balance/account: no
- order/cancel: no
- transfer/withdraw/deposit: no
- fiat/bank transfer: no
- auto-trading: no
- active strategy changed: no

## 11. Codex self-check
- Scope is limited to replay fixture, packet builder, replay config, docs, tests, and README example.
- No live adapter, persistent adapter, probe, prompt, Gemini runtime, sampling/alert, Council handoff, or active strategy change is included.
- PR evidence must reference this handoff file so reviewers are not dependent on a generic GitHub PR body.

## 12. Next recommended step
After this replay path is reviewed, the next step should be an evaluate-only review of generated packet quality and readiness outputs before any live adapter or sampling work is considered.
