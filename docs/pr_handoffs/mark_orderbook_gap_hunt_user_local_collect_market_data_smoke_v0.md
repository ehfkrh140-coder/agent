# Mark-Orderbook Gap Hunt User-Local collect_market_data Smoke Evidence v0

## 1. Purpose

Record evidence that the user ran the registered `live_binance_mark_orderbook_gap_btcusdt` adapter through the official `tools/collect_market_data.py` path on a normal user-local network and successfully generated an analysis-only `OpportunityPacket` from live Binance public market data.

This is an evidence-only PR. It does not modify runtime code, config, registry, tools, tests, sampling, alerts, Council behavior, execution, private API behavior, or generated packet artifacts.

## 2. Baseline

- `BinanceMarkOrderbookGapHuntAdapter` exists and is registered as `live_binance_mark_orderbook_gap_btcusdt`.
- The adapter is experimental, disabled/non-active in config, public-read-only, and `NO_TRADE_ONLY`.
- The packet-builder dispatch issue for `strategy_family=mark_orderbook_gap_hunt` was fixed in the preceding packet-builder support PR.
- Codex workspace live network checks may be blocked by tunnel/network restrictions; this evidence is explicitly user-local and must not be presented as a Codex workspace live success.
- Generated packet JSON is a local smoke artifact and must not be committed.

## 3. User-local smoke command

The user ran:

```bash
python tools/collect_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --output data/generated_packets/live_binance_mark_orderbook_gap_btcusdt.json
```

Output artifact path:

```text
data/generated_packets/live_binance_mark_orderbook_gap_btcusdt.json
```

The generated JSON file is not part of this PR.

## 4. User-local smoke result

User-local verification summary:

```text
strategy_family: mark_orderbook_gap_hunt
strategy_id: mark_orderbook_gap_hunt_v0
asset: BTC
quote: USDT
observations: 1
candidates: 1
venue_id: binance
market_symbol: BTCUSDT
mark_price: 62413.6
index_price: 62444.55652174
bid: 62416.3
ask: 62416.4
candidate_type: mark_orderbook_gap_observation
gross_gap_pct: 0.00432598023507697
estimated_net_gap_pct: -0.19567401976492302
readiness_status: REJECT
recommended_default_decision: REJECT
readiness_pass: False
required_missing_fields: []
no_trade_only: True
execution_policy: NO_TRADE_ONLY
has_execution_allowed: False
has_council_auto_call: False
has_alert_trigger: False
```

## 5. Result interpretation

- User-local `collect_market_data` smoke succeeded.
- The registered adapter id `live_binance_mark_orderbook_gap_btcusdt` can be executed through the official `tools/collect_market_data.py` path.
- The adapter fetched live Binance public no-key mark/orderbook/metadata data from the user-local normal network.
- The official collect path generated one analysis-only `OpportunityPacket` with one observation and one candidate.
- `readiness_status=REJECT` is expected for this run because the gross observed gap was positive but the estimated net gap was negative after the configured fee/slippage buffer.
- `REJECT` is not a data-collection failure and is not a trade signal.
- No `execution_allowed`, `council_auto_call`, or `alert_trigger` fields were present.
- `no_trade_only=True` and `execution_policy=NO_TRADE_ONLY` were preserved.
- The prior packet-builder dispatch failure for `strategy_family=mark_orderbook_gap_hunt` is resolved in this user-local normal-network smoke.

## 6. What this proves

- The registered adapter id can run through `tools/collect_market_data.py` in a user-local normal network.
- The Binance public mark/orderbook/metadata fetch path works from the user-local environment.
- The packet-builder fix resolved the previous unsupported `strategy_family=mark_orderbook_gap_hunt` error in the official collect path.
- The adapter can produce an analysis-only `OpportunityPacket` through the official collect path.
- The `NO_TRADE_ONLY` boundary is preserved.

## 7. What this does not prove

- It does not prove profitability.
- It does not prove sampling or persistence behavior.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API work.
- It does not prove Bybit/OKX adapters.
- It does not prove a multi-venue composite implementation.
- It does not make `mark_orderbook_gap_hunt_v0` the active strategy.

## 8. Generated artifact handling

- Generated output path was `data/generated_packets/live_binance_mark_orderbook_gap_btcusdt.json`.
- The generated packet is a user-local smoke artifact only.
- Generated packet JSON must not be committed.
- This PR commits only this evidence document and excludes the generated packet JSON.

## 9. Changed files

- `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_collect_market_data_smoke_v0.md` — user-local official collect-path smoke evidence.

No runtime code, config, registry, tool, test, sampling, generated-data, Council, notification, storage, or Gemini runtime files were changed.

## 10. Tests run by Codex

- `git status` — checked repository state before changes.
- `git diff --name-only` — checked changed files before commit.
- `python -m unittest discover -s tests` — passed; 294 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed; 9 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed; 8 tests OK.
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed; 12 tests OK.
- `python tools/collect_market_data.py --list-adapters` — passed; output included `live_binance_mark_orderbook_gap_btcusdt`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed; expected policy/test/documentation matches only.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as a strategy/no-trade scan.
- `git status --short` — run after commit.

Codex did not run live Binance collection as a merge requirement for this docs-only PR. The live result recorded here is user-local evidence supplied by the user.

## 11. Risks

- The evidence is based on a single user-local live observation; future public endpoint availability and values may differ.
- `readiness_status=REJECT` is expected for this observation, but future observations may be `NEED_DATA`, `REJECT`, or analysis-only `WATCH` depending on live data and thresholds.
- This evidence does not validate persistence, sampling, alerting, Council review, or execution behavior.

## 12. Rollback plan

Revert this docs-only commit to remove the user-local collect-path smoke evidence file. No runtime rollback is required because this PR does not change code, config, registry, tools, tests, generated data, sampling, alerts, Council, or execution behavior.

## 13. Human review required

Human reviewers should verify:

- the evidence is correctly described as user-local, not Codex workspace live success;
- generated packet JSON is not committed;
- `readiness_status=REJECT` is interpreted as analysis/readiness output, not a data-collection failure and not a trade signal;
- `NO_TRADE_ONLY` is preserved;
- no alert, Council auto-call, active promotion, execution, private API, or generated-artifact scope is introduced.

## 14. No-trade compliance

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
- config adapter registration changes: no
- registry changes: no
- sampling implementation: no
- live network smoke as merge requirement: no
- Bybit/OKX adapter registration: no
- multi-venue composite implementation: no

## 15. Next recommended step

Keep this evidence as the first official collect-path user-local live smoke record. The next recommended implementation step, if the user approves, is a narrowly scoped planning PR for sampling/persistence boundaries or a separate evidence-only PR if the user performs additional user-local repeated smoke runs. Do not add alerts, Council auto-call, active promotion, execution, or private API work at this stage.
