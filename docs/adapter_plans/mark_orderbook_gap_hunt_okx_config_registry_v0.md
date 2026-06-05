# Mark-Orderbook Gap Hunt OKX Config/Registry Planning v0

## 1. Purpose

Plan the future config/registry registration for the standalone `OkxMarkOrderbookGapHuntAdapter` before connecting it to the official `tools/collect_market_data.py` path.

This document is planning-only. It does not implement OKX config registration, registry integration, collect-market-data wiring, sampling, alert/notification expansion, Council auto-call, active promotion, execution/private API, parser/readiness/timestamp/freshness changes, OKX index/reference semantics changes, multi-venue composite behavior, or generic/base adapter extraction.

## 2. Current baseline

- `OkxMarkOrderbookGapHuntAdapter` exists as a standalone public-read-only runtime adapter class.
- Mocked OKX adapter unit tests passed in the runtime adapter PR.
- User-local direct OKX adapter smoke succeeded and produced one analysis-only `OpportunityPacket`.
- User-local direct smoke preserved `NO_TRADE_ONLY`, `no_trade_only=true`, and no execution/Council/alert fields.
- OKX adapter is not registered in `configs/market_data.yaml`.
- OKX adapter type is not mapped in `src/market_data/registry.py`.
- OKX `collect_market_data` and sampling paths are not proven.
- `index_price=None` was observed in direct smoke and remains a future OKX index/reference interpretation watch item.

## 3. Proposed config entry

Document only; do not implement in this planning PR.

Proposed adapter id:

```yaml
live_okx_mark_orderbook_gap_btc_usdt_swap:
  type: okx_mark_orderbook_gap_hunt
  enabled: false
  experimental: true
  strategy_family: mark_orderbook_gap_hunt
  strategy_id: mark_orderbook_gap_hunt_v0
  base_url: https://www.okx.com
  inst_type: SWAP
  inst_id: BTC-USDT-SWAP
  asset: BTC
  quote: USDT
  orderbook_size: 5
  timeout_seconds: 10
  max_retries: 2
  user_agent: agent-council-market-data-v1
  fee_slippage_buffer_pct: "0.20"
  min_net_gap_pct: "0"
  max_data_age_ms: 10000
  require_freshness: true
  liquidity_pass: true
  size_or_notional_resolved: true
  execution_policy: NO_TRADE_ONLY
  experimental_strategy: true
  non_active_strategy: true
  no_trade_only: true
  note: "Public read-only OKX BTC-USDT-SWAP Mark-Orderbook Gap Hunt adapter. Experimental/non-active/NO_TRADE_ONLY."
```

Config invariants:

- `enabled` must remain `false`.
- `experimental_strategy`, `non_active_strategy`, and `no_trade_only` must remain `true`.
- `execution_policy` must remain `NO_TRADE_ONLY`.
- No credentials, private endpoint settings, account identifiers, balance fields, order fields, position fields, transfer fields, alert fields, or Council fields should be added.

## 4. Registry mapping plan

Document only; do not implement in this planning PR.

Future registry mapping should map:

- adapter type: `okx_mark_orderbook_gap_hunt`
- adapter class: `OkxMarkOrderbookGapHuntAdapter`

Registration constraints:

- Must not change active strategy.
- Must not make sampling automatic.
- Must not add alert or notification behavior.
- Must not add Council auto-call behavior.
- Must not add execution/private API behavior.
- Must not create multi-venue composite behavior.
- Must not trigger generic/base adapter extraction.

## 5. Future collect_market_data behavior

Expected future command after config/registry registration:

```bash
python tools/collect_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap --output data/generated_packets/live_okx_mark_orderbook_gap_btc_usdt_swap.json
```

Expected successful packet shape:

- `strategy_family: mark_orderbook_gap_hunt`
- `strategy_id: mark_orderbook_gap_hunt_v0`
- `asset: BTC`
- `quote: USDT`
- `observations: 1`
- `candidates: 1`
- `venue_id: okx`
- `market_symbol: BTC-USDT-SWAP`
- `execution_policy: NO_TRADE_ONLY`
- `no_trade_only: true`
- no `execution_allowed`
- no `council_auto_call`
- no `alert_trigger`

Generated packet JSON from future smoke is a local smoke artifact and must not be committed.

## 6. User-local smoke plan

Future registration PR should not require Codex workspace live endpoint success; workspace live network may fail due to tunnel or 403 restrictions.

After registration, user-local normal-network smoke should verify:

- the future `collect_market_data` command completes;
- generated packet JSON is inspected and then deleted;
- generated packet JSON is not committed;
- `readiness_status` is one of `NEED_DATA`, `REJECT`, or `WATCH`;
- `REJECT` is not failure;
- `WATCH` remains analysis-only;
- no `execution_allowed`, `council_auto_call`, or `alert_trigger` fields appear;
- `index_price=None`, if repeated, is documented as a watch item and not a blocker unless `required_missing_fields` or future readiness policy changes.

## 7. OKX index_price / reference watch item

The user-local direct OKX smoke observed `index_price=None`.

Carry-forward interpretation:

- It was not a blocker because `required_missing_fields=[]`, readiness completed, and packet creation succeeded.
- It does not prove full OKX index/reference semantics.
- Do not change OKX index/reference interpretation in this planning PR.
- Do not add or reinterpret OKX index/ticker endpoint behavior in this planning PR.
- Future policy or adapter work may evaluate whether OKX index/reference fields should be added or normalized consistently across Binance, Bybit, and OKX.

## 8. Future registration merge gate

A future `Mark-Orderbook Gap Hunt OKX Config/Registry v0` implementation PR should include:

- unit tests;
- `list-adapters` check;
- `build_adapter` instantiation check mapping to `OkxMarkOrderbookGapHuntAdapter`;
- mocked/no-network `collect_market_data` path check if possible;
- no-trade safety scan;
- active strategy check confirming `cross_exchange_spot_spread_v1` remains active;
- generated artifact cleanup confirmation;
- handoff evidence;
- human review.

## 9. Future deferrals

- OKX registration implementation is the next separate PR.
- OKX user-local collect smoke is separate evidence.
- OKX sampling is later.
- Multi-venue composite is later.
- Generic/base adapter extraction is later after Binance/Bybit/OKX comparison.
- Timestamp/data_age policy is later after venue comparison.
- OKX index/reference interpretation is later.
- Alert/notification is later.
- Council auto-call is later.
- Active promotion is later.
- Execution/private API is much later via common execution/risk engine.

## 10. No-trade constraints

This plan does not add:

- private API;
- API key/secret/token;
- env credential lookup;
- auth/private headers;
- account/balance lookup;
- position lookup;
- order/cancel;
- withdrawal/deposit/transfer;
- fiat/bank transfer;
- auto-trading;
- Council auto-call;
- Council decision to trade conversion;
- active strategy promotion;
- alert expansion;
- notification expansion;
- generated packet JSON commit;
- generated sampling JSON commit;
- OKX config adapter registration implementation;
- OKX registry integration implementation;
- sampling implementation;
- live network smoke as merge requirement;
- multi-venue composite implementation;
- generic/base adapter extraction;
- parser/readiness/timestamp/freshness logic changes;
- `data_age_ms` clamp or reinterpretation;
- OKX index/reference semantics change.

## 11. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt OKX Config/Registry v0` implementation PR limited to config entry, registry mapping, and mocked/list-adapter/build-adapter checks. Keep generated packet JSON out of git and carry the OKX `index_price=None` watch item forward.
