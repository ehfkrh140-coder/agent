# Mark-Orderbook Gap Hunt Binance Adapter Config/Registry Planning v0

## Purpose

Plan the future config/registry registration scope for `BinanceMarkOrderbookGapHuntAdapter` before making it runnable through `tools/collect_market_data.py`.

This is planning-only. It does not implement config registration, registry integration, tool/CLI wiring, sampling, alert/notification, Council auto-call, active promotion, execution/private API, or generated artifact commits.

## Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- `BinanceMarkOrderbookGapHuntAdapter` already exists as a standalone Binance USDⓈ-M `BTCUSDT` adapter class.
- User-local direct adapter smoke succeeded from normal network and produced an analysis-only packet.
- The adapter is not yet registered in `configs/market_data.yaml`.
- The adapter is not yet mapped in `src/market_data/registry.py`.
- The adapter is not yet runnable through `tools/collect_market_data.py`.

## Proposed config entry

Future registration PR may add an adapter entry like the following. This PR documents the plan only and does not modify `configs/market_data.yaml`.

```yaml
adapters:
  live_binance_mark_orderbook_gap_btcusdt:
    type: binance_mark_orderbook_gap_hunt
    enabled: false
    strategy_family: mark_orderbook_gap_hunt
    strategy_id: mark_orderbook_gap_hunt_v0
    base_url: https://fapi.binance.com
    symbol: BTCUSDT
    asset: BTC
    quote: USDT
    orderbook_limit: 5
    timeout_seconds: 10
    max_retries: 2
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
```

Planning notes:

- `enabled` should remain `false` or experimental-only until review.
- Thresholds are analysis/readiness inputs, not execution rules.
- Future threshold changes require human review.
- No credentials, auth headers, account state, position state, balances, orders, transfers, fiat/bank data, or private payloads belong in config.

## Registry mapping plan

Future registration PR may map adapter type `binance_mark_orderbook_gap_hunt` to `BinanceMarkOrderbookGapHuntAdapter` in `src/market_data/registry.py`.

Registry mapping constraints:

- Registration must not change the active strategy.
- Registration must not make sampling automatic.
- Registration must not trigger alerts or notifications.
- Registration must not trigger Council auto-call.
- Registration must not create execution or private API behavior.
- Registration must keep `mark_orderbook_gap_hunt_v0` experimental / non-active / `NO_TRADE_ONLY`.

## Future collect_market_data behavior

After a separate reviewed registration PR, expected manual command:

```text
python tools/collect_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --output data/generated_packets/live_binance_mark_orderbook_gap_btcusdt.json
```

Expected successful packet shape:

- `strategy_family`: `mark_orderbook_gap_hunt`
- `strategy_id`: `mark_orderbook_gap_hunt_v0`
- `asset`: `BTC`
- `quote`: `USDT`
- `observations`: `1`
- `candidates`: `1`
- `execution_policy`: `NO_TRADE_ONLY`
- `no_trade_only`: `true`
- no `execution_allowed`
- no `council_auto_call`
- no `alert_trigger`

Generated packet JSON from this command is a smoke artifact and must not be committed.

## User-local smoke plan

- Codex workspace live network may fail due to network tunnel `403`; that should be treated as an environment limitation.
- User-local normal-network smoke is required after future config/registry registration.
- Generated packet JSON must be deleted after smoke and must not be committed.
- `readiness_status` may be `NEED_DATA`, `REJECT`, or `WATCH`.
- `REJECT` is not a failure; it can be a healthy no-edge classification.
- `WATCH` is analysis-only and does not imply execution, Council auto-call, or alert trigger.

## Future registration merge gate

A future config/registry registration PR should include:

- unit tests for registry construction;
- `list_adapters` or equivalent adapter listing check;
- direct adapter smoke or mocked/replay collection check as applicable;
- user-local live smoke evidence after registration;
- no-trade safety scan;
- active strategy scan;
- generated artifact cleanup evidence;
- handoff evidence under `docs/pr_handoffs/`;
- explicit human review.

## Future deferrals

Defer these areas to separate PRs:

- sampling integration;
- alert/notification;
- Council auto-call;
- Bybit adapter;
- OKX adapter;
- multi-venue composite;
- active strategy promotion;
- execution/private API through a future common execution/risk engine with credential isolation, dry-run/paper trading, kill switch, risk limits, order-state machine, audit logs, rollback plan, and explicit human review.

## No-trade boundary

This plan does not add private API, credentials, account/balance/position lookup, order/cancel, withdrawal/deposit/transfer, fiat/bank transfer, auto-trading, Council auto-call, active promotion, alert expansion, notification expansion, generated packet commit, generated sampling commit, config registration implementation, registry integration implementation, sampling implementation, or live-network smoke as a merge requirement.

## Next recommended step

Open `Mark-Orderbook Gap Hunt Binance Adapter Config/Registry v0` only after human review of this planning PR. Keep that follow-up small: config entry, registry mapping, unit/list-adapter checks, generated artifact cleanup evidence, and `NO_TRADE_ONLY` boundaries only.
