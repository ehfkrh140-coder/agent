# Mark-Orderbook Gap Hunt User-Local Bybit collect_market_data Smoke Evidence v0

## 1. Purpose

Record user-local normal-network evidence that the registered `live_bybit_mark_orderbook_gap_btcusdt` adapter id can run through the official `tools/collect_market_data.py` path and generate an analysis-only Mark-Orderbook Gap Hunt `OpportunityPacket` from live public Bybit data.

This is an evidence-only PR. It does not change runtime code, config, registry, tools, tests, sampling logic, parser/readiness/timestamp/freshness logic, alerts, Council behavior, active promotion, execution/private API, generated packet JSON, generated sampling JSON, OKX registration, multi-venue composite behavior, or generic/base adapter extraction.

## 2. Baseline

- `BybitMarkOrderbookGapHuntAdapter` exists and is implemented for Bybit V5 linear BTCUSDT public market data.
- The adapter uses public no-key Bybit ticker, orderbook, and instruments-info endpoints.
- The adapter reuses the common Mark-Orderbook Gap parser with `parser_mode="bybit_linear"` and the shared readiness helper.
- The adapter had already succeeded in user-local direct class invocation evidence.
- The adapter was subsequently registered in config/registry as `live_bybit_mark_orderbook_gap_btcusdt` with `enabled: false`, experimental/non-active status, and `execution_policy: NO_TRADE_ONLY`.
- This evidence records the first user-local live collect smoke through the official `tools/collect_market_data.py` adapter-id path, not a Codex workspace live-network success.

## 3. User-local collect command

The user ran the following command from a normal local network environment:

```bash
python tools/collect_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --output data/generated_packets/live_bybit_mark_orderbook_gap_btcusdt.json
```

The generated JSON output path was `data/generated_packets/live_bybit_mark_orderbook_gap_btcusdt.json`. It is a smoke artifact only and is excluded from this PR.

## 4. User-local collect result

Observed summary from the user-local generated packet:

- `schema_version: opportunity_packet_v0`
- `adapter_id: live_bybit_mark_orderbook_gap_btcusdt`
- `adapter_type: bybit_mark_orderbook_gap_hunt`
- `venue_id: bybit`
- `venue_name: Bybit Derivatives V5`
- `category: linear`
- `strategy_family: mark_orderbook_gap_hunt`
- `strategy_id: mark_orderbook_gap_hunt_v0`
- `asset: BTC`
- `quote: USDT`
- `signal_type: mark_orderbook_gap_hunt`
- `observations: 1`
- `candidates: 1`
- `market_symbol: BTCUSDT`
- `instrument_type: linear_perpetual`
- `mark_price: 63991.52`
- `index_price: 64014.24`
- `bid: 63995.50`
- `ask: 63995.60`
- `gross_gap_pct: 0.006219574093567398`
- `estimated_net_gap_pct: -0.1937804259064326`
- `readiness_status: REJECT`
- `recommended_default_decision: REJECT`
- `readiness_pass: false`
- `required_missing_fields: []`
- `parser_mode: bybit_linear`
- `parser_normalized_status: OK`
- `comparability_pass: true`
- `freshness_pass: true`
- `diagnostics_count: 3`
- `ticker http_status: 200, retCode: 0, retMsg: OK`
- `orderbook http_status: 200, retCode: 0, retMsg: OK`
- `metadata http_status: 200, retCode: 0, retMsg: OK`
- `no_trade_only: true`
- `execution_policy: NO_TRADE_ONLY`
- `has_execution_allowed: false`
- `has_council_auto_call: false`
- `has_alert_trigger: false`
- `observed data_age_ms: approximately -6647 ms`
- `observation timestamp_utc was later than packet created_at_utc by about 6.6 seconds`

## 5. Result interpretation

- User-local `collect_market_data` Bybit smoke succeeded.
- The registered adapter id `live_bybit_mark_orderbook_gap_btcusdt` can be executed through the official `tools/collect_market_data.py` path.
- The adapter fetched live Bybit public no-key ticker, orderbook, and instruments-info data.
- The official collect path generated one analysis-only `OpportunityPacket` with one observation and one candidate.
- `readiness_status=REJECT` is expected no-edge behavior because a small gross gap existed but `estimated_net_gap_pct` was negative after fee/slippage buffer.
- This was not a data collection failure.
- This was not a trade signal.
- No `execution_allowed`, `council_auto_call`, or `alert_trigger` fields were present.
- `no_trade_only=true` and `execution_policy=NO_TRADE_ONLY` were preserved.

## 6. Timestamp / data_age watch item

The user-local output showed `data_age_ms` around `-6647 ms`, with `observation.timestamp_utc` later than packet `created_at_utc` by about 6.6 seconds.

This likely reflects exchange timestamp vs local collection timestamp alignment or clock skew. It is recorded as a watch item only.

This is not treated as a blocker in this evidence PR because:

- `parser_normalized_status` was `OK`.
- `freshness_pass` was `true`.
- `required_missing_fields` was empty.
- Bybit ticker, orderbook, and metadata diagnostics were all `http_status=200`, `retCode=0`, and `retMsg=OK`.
- Packet creation succeeded.
- The readiness result was `REJECT` due to negative net gap, not `NEED_DATA` due to timestamp/freshness failure.

Explicit non-actions for this PR:

- Do not change code in this PR.
- Do not clamp negative `data_age_ms` in this PR.
- Do not reinterpret negative `data_age_ms` in this PR.
- Do not change parser/readiness/timestamp/freshness logic in this PR.
- Do not change freshness policy in this PR.

## 7. Future timestamp policy follow-up candidate

Potential future task candidates:

- `Market Data Timestamp Freshness / Clock Skew Policy v0`
- `Mark-Orderbook Gap Hunt Timestamp Alignment Policy v0`

Future work should compare Binance, Bybit, and OKX timestamp semantics before changing shared parser/readiness/freshness behavior. A future policy should decide whether negative `data_age_ms` should be tolerated, clamped, warned, normalized with clock-skew allowance, or converted into `NEED_DATA` under specific conditions.

No timestamp policy change is made in this evidence PR.

## 8. What this proves

- Registered Bybit adapter id can run through `tools/collect_market_data.py` in a user-local normal-network environment.
- Bybit public ticker/orderbook/instruments-info fetch path works from the user-local environment.
- Parser/readiness integration works through the official collect path.
- The adapter can produce an analysis-only `OpportunityPacket` through the official collect path.
- `REJECT` no-edge classification is represented correctly.
- The `NO_TRADE_ONLY` boundary is preserved.

## 9. What this does not prove

- It does not prove profitability.
- It does not prove sampling or persistence behavior.
- It does not justify alert or notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution or private API.
- It does not prove OKX adapter or multi-venue composite behavior.
- It does not resolve timestamp freshness or clock-skew policy.
- It does not prove that negative `data_age_ms` is always safe.
- It does not justify changing timestamp policy without Binance/Bybit/OKX comparison.

## 10. Generated artifact handling

- Generated output path was `data/generated_packets/live_bybit_mark_orderbook_gap_btcusdt.json`.
- It is a user-local smoke artifact only.
- It must not be committed.
- Generated packet JSON is excluded from this PR.
- No generated sampling JSON is included.

## 11. Changed files

- `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_bybit_collect_market_data_smoke_v0.md`

No `src/**`, `configs/**`, `tests/**`, `tools/**`, or generated `data/**` files are changed.

## 12. Tests run by Codex

Codex checks completed for this docs-only evidence PR before commit:

- `git status` — clean before the docs-only change, then showed only the new handoff file.
- `git diff --name-only` — showed no tracked file diff before staging because the only change was a new untracked handoff file.
- `python -m unittest discover -s tests` — passed (`Ran 311 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed (`Ran 5 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` — passed and listed `live_bybit_mark_orderbook_gap_btcusdt`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed as a no-trade/credential scan across existing repository references.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as an active-strategy/no-trade scan across existing repository references.
- `git status --short` — to be checked again after staging/commit; before commit it showed only this new handoff file.
- `git diff --name-only HEAD~1..HEAD` — to be recorded after commit in the final response.

## 13. Risks

- User-local live evidence depends on the user's local network, Bybit public endpoint availability, exchange timestamps, and local clock alignment.
- Negative `data_age_ms` was observed and is intentionally not fixed here; reviewers should treat it as a timestamp policy watch item, not as resolved behavior.
- This PR does not add automated timestamp policy coverage.
- This PR does not prove sampling/persistence behavior for the Bybit adapter.

## 14. Rollback plan

- Revert this docs-only PR.
- Confirm `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_bybit_collect_market_data_smoke_v0.md` is removed.
- No code/config/test/tool rollback is required because none were changed.
- Re-run documentation or unit checks as needed.

## 15. Human review required

Human review should first inspect:

1. This handoff file's user-local result and interpretation.
2. The `Timestamp / data_age watch item` section to confirm negative `data_age_ms` is recorded without silently changing policy.
3. The generated artifact handling section to confirm generated packet JSON is excluded.
4. The no-trade compliance section to confirm no execution/private/API/Council/alert expansion is claimed.

## 16. No-trade compliance

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
- OKX adapter registration: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no

## 17. Next recommended step

Open a separate planning task for timestamp alignment policy only after enough Binance, Bybit, and OKX evidence exists to compare exchange timestamp semantics. Suggested title: `Market Data Timestamp Freshness / Clock Skew Policy v0`.

Do not implement timestamp policy changes, sampling integration, alerts, Council auto-call, active promotion, or execution/private API as part of this evidence PR.
