# Mark-Orderbook Gap Hunt Bybit Adapter Config/Registry Planning v0

## 1. Purpose

Plan the future config/registry registration for the standalone `BybitMarkOrderbookGapHuntAdapter` before making it executable through official `collect_market_data` paths.

This is planning-only. It does not edit `configs/market_data.yaml`, does not edit `src/market_data/registry.py`, does not wire `tools/collect_market_data.py`, does not implement sampling, and does not add alert, Council, active promotion, execution, private API, generated artifacts, OKX, multi-venue composite, or generic/base adapter extraction.

## 2. Current baseline

- `BybitMarkOrderbookGapHuntAdapter` exists as a standalone class.
- Mocked Bybit adapter unit tests pass.
- User-local direct Bybit adapter smoke succeeded with one observation and one candidate.
- Direct smoke preserved `adapter_type=bybit_mark_orderbook_gap_hunt`, `no_trade_only=True`, `execution_policy=NO_TRADE_ONLY`, and no `execution_allowed`, `council_auto_call`, or `alert_trigger` fields.
- Bybit adapter is not registered in `configs/market_data.yaml` or `src/market_data/registry.py` yet.
- Bybit official `collect_market_data` and sampling paths are not proven yet.

## 3. Proposed config entry

Document only; do not implement in this planning PR.

Proposed adapter id:

```yaml
live_bybit_mark_orderbook_gap_btcusdt:
  type: bybit_mark_orderbook_gap_hunt
  enabled: false
  experimental: true
  strategy_family: mark_orderbook_gap_hunt
  strategy_id: mark_orderbook_gap_hunt_v0
  base_url: https://api.bybit.com
  category: linear
  symbol: BTCUSDT
  asset: BTC
  quote: USDT
  orderbook_limit: 5
  timeout_seconds: 10
  max_retries: 2
  user_agent: agent-council-market-data-v1
  fee_slippage_buffer_pct: 0.20
  min_net_gap_pct: 0
  max_data_age_ms: 10000
  require_freshness: true
  liquidity_pass: true
  size_or_notional_resolved: true
  execution_policy: NO_TRADE_ONLY
  experimental_strategy: true
  non_active_strategy: true
  no_trade_only: true
  note: "Public read-only Bybit V5 linear BTCUSDT Mark-Orderbook Gap Hunt adapter. Experimental/non-active/NO_TRADE_ONLY."
```

Planning notes:

- Keep `enabled: false` for initial registration unless a later explicit review chooses another disabled/experimental-only convention.
- Thresholds are analysis-only placeholders and must not be interpreted as execution rules.
- Do not include credentials, auth headers, account identifiers, balance/position fields, order/cancel fields, transfer fields, alert fields, Council fields, or execution fields.

## 4. Registry mapping plan

Document only; do not implement in this planning PR.

Future mapping:

- Adapter type `bybit_mark_orderbook_gap_hunt` should map to `BybitMarkOrderbookGapHuntAdapter`.
- The registry import should be minimal and should not alter existing Binance behavior.
- Registration must not change the active strategy.
- Registration must not make sampling automatic.
- Registration must not enable alert/notification behavior.
- Registration must not enable Council auto-call.
- Registration must not enable execution or private API behavior.
- Registration must not register OKX behavior.
- Registration must not create multi-venue composite behavior.
- Registration must not extract a generic/base adapter.

## 5. Future collect_market_data behavior

Document only; do not implement in this planning PR.

Expected future command after config/registry registration:

```bash
python tools/collect_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --output data/generated_packets/live_bybit_mark_orderbook_gap_btcusdt.json
```

Expected successful packet shape:

- `strategy_family: mark_orderbook_gap_hunt`
- `strategy_id: mark_orderbook_gap_hunt_v0`
- `asset: BTC`
- `quote: USDT`
- `observations: 1`
- `candidates: 1`
- `venue_id: bybit`
- `execution_policy: NO_TRADE_ONLY`
- `no_trade_only: true`
- no `execution_allowed`
- no `council_auto_call`
- no `alert_trigger`

Generated packet JSON must be deleted after inspection and must not be committed.

## 6. User-local smoke plan

Future registration PR should not require Codex workspace live network success because this environment may fail public endpoint access through tunnel or 403 restrictions.

After registration, user-local normal-network smoke should be recorded in a separate evidence PR. The smoke should verify:

- `python tools/collect_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --output data/generated_packets/live_bybit_mark_orderbook_gap_btcusdt.json` completes.
- Generated output contains one Bybit observation and one Mark-Orderbook Gap candidate when public data is complete.
- `readiness_status` may be `NEED_DATA`, `REJECT`, or `WATCH`.
- `REJECT` is not a failure; it can be normal no-edge behavior.
- `WATCH` is analysis-only.
- `NO_TRADE_ONLY` is preserved.
- Generated packet JSON is not committed.

## 7. Future registration merge gate

A future `Mark-Orderbook Gap Hunt Bybit Adapter Config/Registry v0` implementation PR should include:

- Unit tests for config entry and registry mapping.
- `list-adapters` check showing `live_bybit_mark_orderbook_gap_btcusdt` after registration.
- `build_adapter` instantiation check that maps `bybit_mark_orderbook_gap_hunt` to `BybitMarkOrderbookGapHuntAdapter`.
- Mocked/no-network `collect_market_data` path check if an existing test seam supports it.
- No-trade safety scan.
- Active strategy check confirming `cross_exchange_spot_spread_v1` remains active.
- Generated artifact cleanup confirmation.
- Handoff evidence.
- Human review.

## 8. Future deferrals

- Bybit registration implementation is the next separate PR.
- Bybit user-local collect smoke is separate evidence after registration.
- Bybit sampling baseline and sampling evidence are later.
- OKX adapter is later.
- Multi-venue composite is later.
- Generic/base adapter extraction is later after Binance/Bybit/OKX comparison.
- Alert/notification common layer is later.
- Council auto-call is later and requires explicit review.
- Active promotion is later and requires explicit review.
- Execution/private API is much later via a common execution/risk engine.

## 9. No-trade boundary

This plan keeps Bybit Mark-Orderbook Gap Hunt experimental, non-active, analysis-only, and `NO_TRADE_ONLY`. It does not authorize execution, private endpoints, credentials, account/balance/position lookup, orders, cancellations, transfers, alerts, Council auto-call, strategy promotion, generated artifact commits, sampling implementation, OKX implementation, composite implementation, or base adapter extraction.
