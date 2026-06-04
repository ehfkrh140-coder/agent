# Mark-Orderbook Gap Hunt collect_market_data Packet Builder Fix v0

## 1. Purpose

Fix the user-local `tools/collect_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt` failure where `OpportunityPacketBuilder` rejected the adapter-produced packet dictionary with:

```text
ValueError: Unsupported strategy_family: 'mark_orderbook_gap_hunt'
```

This PR keeps the Binance Mark-Orderbook Gap Hunt adapter public-read-only and `NO_TRADE_ONLY`; it only teaches the packet builder to validate the adapter-produced Mark-Orderbook Gap Hunt packet shape instead of rejecting it.

## 2. Baseline

- `BinanceMarkOrderbookGapHuntAdapter.fetch_snapshot()` returns an `OpportunityPacket` JSON dictionary whose `strategy_family` is `mark_orderbook_gap_hunt`.
- `tools/collect_market_data.py` always passes the adapter result into `OpportunityPacketBuilder().build(snapshot)` before serialization.
- `OpportunityPacketBuilder.build()` previously supported `mark_orderbook_gap`, `cross_exchange_spot_spread`, `orderbook_imbalance`, and `tether_cross_market_premium`, but not `mark_orderbook_gap_hunt`.
- That mismatch caused the user-local traceback even though the adapter could build the analysis-only packet directly.

## 3. Root cause

The new Binance adapter returns an already-normalized `OpportunityPacket` JSON dict for the `mark_orderbook_gap_hunt` strategy family, while the packet builder dispatch table did not include that strategy family. The CLI therefore failed before writing the generated packet output.

## 4. Fix summary

- Add `mark_orderbook_gap_hunt` to `OpportunityPacketBuilder.build()` dispatch.
- Add `build_mark_orderbook_gap_hunt()` that validates the adapter-produced packet dict with `OpportunityPacket.model_validate(snapshot)`.
- Keep the existing legacy `mark_orderbook_gap` replay builder unchanged.
- Add a mocked unit test proving the adapter `fetch_snapshot()` output can pass through `OpportunityPacketBuilder`, matching the existing `collect_market_data` build path without live network access.

## 5. collect_market_data behavior

After this fix, the existing CLI flow can accept the registered Binance adapter output:

```bash
python tools/collect_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --output data/generated_packets/live_binance_mark_orderbook_gap_btcusdt.json
```

Expected user-local behavior remains:

- public no-key Binance endpoints only;
- generated packet JSON is a smoke artifact and must not be committed;
- packet remains `strategy_family=mark_orderbook_gap_hunt`;
- packet remains `strategy_id=mark_orderbook_gap_hunt_v0`;
- packet remains `execution_policy=NO_TRADE_ONLY` via adapter metadata;
- no `execution_allowed`, no `council_auto_call`, and no `alert_trigger` should be introduced.

## 6. Tests run

- `git status` — checked before changes.
- `git diff --name-only` — checked changed files before commit.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed; 9 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed; 8 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed; 12 tests OK.
- `python -m unittest discover -s tests` — run as final full-suite gate.
- `python tools/collect_market_data.py --list-adapters` — run as adapter-list check.
- `python tools/collect_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --output /tmp/live_binance_mark_orderbook_gap_btcusdt_fix_check.json` — attempted as a workspace live check; blocked by the environment with `Tunnel connection failed: 403 Forbidden` before writing an artifact. User-local normal-network smoke remains the appropriate live verification.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — run as no-trade/sensitive-term scan; expected policy/test/documentation matches only.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — run as strategy/no-trade scan.
- `git status --short` — run after commit.

## 7. What this proves

- The packet builder now recognizes `mark_orderbook_gap_hunt` adapter packet dictionaries.
- The existing `collect_market_data` build path no longer fails solely because of the `mark_orderbook_gap_hunt` strategy-family dispatch.
- The fix is covered by mocked unit tests and does not require live network access.
- The legacy replay `mark_orderbook_gap` builder path remains separate.

## 8. What this does not prove

- It does not prove user-local Binance endpoint availability at review time.
- It does not prove profitability.
- It does not add sampling integration.
- It does not add alert/notification behavior.
- It does not add Council auto-call.
- It does not add execution/private API behavior.

## 9. Changed files

- `src/market_data/packet_builder.py` — add `mark_orderbook_gap_hunt` dispatch and validation path.
- `tests/test_mark_orderbook_gap_hunt_binance_adapter.py` — add mocked packet-builder/collect-CLI-flow coverage for adapter `fetch_snapshot()` output.
- `docs/pr_handoffs/mark_orderbook_gap_hunt_collect_market_data_packet_builder_fix_v0.md` — this handoff evidence file.

## 10. Risks

- The fix validates adapter-produced packet dictionaries rather than rebuilding candidates from raw snapshots. This is intentional for the current adapter shape, but future adapters should explicitly decide whether they return raw snapshots or packet dictionaries.
- User-local live collection may still fail due to public network restrictions or exchange availability; that would be a separate connectivity issue, not this dispatch bug.

## 11. Rollback plan

Revert this commit to remove the `mark_orderbook_gap_hunt` packet-builder dispatch/test/handoff. The Binance adapter direct `fetch_packet()` path would remain available from prior work, but `collect_market_data` would again reject `mark_orderbook_gap_hunt` snapshots until a replacement builder path is added.

## 12. Human review required

Reviewers should verify:

- `OpportunityPacketBuilder.build()` only adds the `mark_orderbook_gap_hunt` dispatch and does not alter active strategy behavior;
- the new builder method only validates `OpportunityPacket` shape and does not synthesize execution/Council/alert fields;
- the adapter test uses mocked public data only;
- generated packet JSON remains uncommitted.

## 13. No-trade compliance

- private API: no
- API key/secret/token: no
- env credential lookup: no
- auth/private headers: no
- account/balance lookup: no
- position lookup: no
- order/cancel: no
- withdrawal/deposit/transfer: no
- fiat/bank transfer: no
- auto-trading: no
- Council auto-call: no
- Council decision to trade conversion: no
- active strategy promotion: no
- alert expansion: no
- notification expansion: no
- generated packet JSON commit: no
- generated sampling JSON commit: no
- sampling implementation: no
- live network smoke as merge requirement: no
- Bybit/OKX adapter registration: no
- multi-venue composite implementation: no

## 14. Next recommended step

Ask the user to rerun the same user-local command and record a follow-up evidence-only handoff if it succeeds. If it fails again, separate packet-builder dispatch issues from public-network or exchange-response issues before expanding scope.
