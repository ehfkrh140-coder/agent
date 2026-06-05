# Mark-Orderbook Gap Hunt OKX Config/Registry v0

## 1. Purpose

Register the standalone `OkxMarkOrderbookGapHuntAdapter` in the existing market-data config/registry path as one disabled, experimental, non-active, `NO_TRADE_ONLY` adapter id: `live_okx_mark_orderbook_gap_btc_usdt_swap`.

This PR is limited to OKX config/registry registration and mocked/list-adapter/build-adapter verification. It does not add sampling integration, alert/notification behavior, Council auto-call, active promotion, execution/private API, multi-venue composite behavior, generic/base adapter extraction, parser/readiness/timestamp/freshness changes, `data_age_ms` clamp/reinterpretation, or OKX index/reference semantics changes.

## 2. Baseline

- `OkxMarkOrderbookGapHuntAdapter` class already exists.
- Mocked OKX adapter unit tests passed before this registration PR.
- User-local direct OKX smoke succeeded before this PR and produced one analysis-only `OpportunityPacket`.
- The direct smoke preserved `NO_TRADE_ONLY`, `no_trade_only=true`, and no `execution_allowed`, `council_auto_call`, or `alert_trigger` fields.
- OKX config/registry planning was completed before this PR.
- Before this PR, the OKX adapter was not connected to `configs/market_data.yaml` or `src/market_data/registry.py`.
- The direct smoke observed `index_price=None`; this remains a watch item, not a blocker for config/registry registration.

## 3. Config changes

Added one adapter entry to `configs/market_data.yaml`:

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
  note: Public read-only OKX BTC-USDT-SWAP Mark-Orderbook Gap Hunt adapter. Experimental/non-active/NO_TRADE_ONLY.
```

The entry is disabled by default, experimental, non-active, analysis-only, and `NO_TRADE_ONLY`.

## 4. Registry changes

Updated `src/market_data/registry.py` to import `OkxMarkOrderbookGapHuntAdapter` and map adapter type `okx_mark_orderbook_gap_hunt` to that class in `build_adapter`.

This registration does not change active strategy, does not auto-enable sampling, does not add alert/notification, does not add Council auto-call, does not add execution/private API, does not create multi-venue composite behavior, and does not trigger generic/base adapter extraction.

## 5. Adapter list / instantiation checks

The OKX adapter registration test verifies:

- `live_okx_mark_orderbook_gap_btc_usdt_swap` appears in `list_adapters(load_market_data_config())`.
- The config type is `okx_mark_orderbook_gap_hunt`.
- The config remains `enabled: false`, `execution_policy: NO_TRADE_ONLY`, `experimental_strategy=true`, `non_active_strategy=true`, and `no_trade_only=true`.
- `build_adapter(adapter_id, config)` returns `OkxMarkOrderbookGapHuntAdapter`.
- Active strategy remains `cross_exchange_spot_spread_v1`.
- No private/auth/order/account/balance/position/transfer fields are introduced in the OKX adapter config.
- Binance and Bybit Mark-Orderbook Gap adapter registrations remain disabled and `NO_TRADE_ONLY`.
- OKX `index_price=None` watch item is not silently fixed by adding config-level index/reference semantics.

`python tools/collect_market_data.py --list-adapters` was run and the registered adapter id appears in the listing.

## 6. Expected future user-local smoke

Future user-local live smoke should be recorded in a separate evidence PR, not as a Codex workspace merge requirement.

Manual follow-up command:

```bash
python tools/collect_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap --output data/generated_packets/live_okx_mark_orderbook_gap_btc_usdt_swap.json
```

Expected user-local smoke packet:

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
- `index_price` may remain `None` and should be documented as a watch item unless future policy changes.

Generated output JSON must be deleted after inspection and must not be committed.

## 7. OKX index_price / reference watch item

The user-local direct OKX smoke observed `index_price=None`.

Carry-forward interpretation:

- It was not a blocker because `required_missing_fields=[]`, readiness completed, and packet creation succeeded.
- This PR does not change OKX index/reference interpretation.
- This PR does not add config-level index/reference semantics.
- This PR does not change parser/readiness logic.
- This PR does not change timestamp/freshness policy.
- Future OKX index/reference interpretation should compare Binance, Bybit, and OKX before changing shared packet semantics.

## 8. Tests run

Codex checks for this registration PR:

- `git status` — checked repository state before changes.
- `git diff --name-only` — checked changed-file scope.
- `python -m unittest discover -s tests` — passed (`Ran 330 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_okx_adapter` — passed (`Ran 13 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_sampling` — passed (`Ran 6 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed (`Ran 5 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` — passed; adapter listing includes `live_okx_mark_orderbook_gap_btc_usdt_swap`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed as a no-trade/credential scan across existing repository references.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as an active-strategy/no-trade scan across existing repository references.
- `git status --short` — checked final working tree state.
- `git diff --name-only HEAD~1..HEAD` — recorded after commit in the final response.

## 9. What this proves

- `live_okx_mark_orderbook_gap_btc_usdt_swap` is present in market-data config.
- The OKX config entry is disabled, experimental, non-active, and `NO_TRADE_ONLY`.
- Adapter type `okx_mark_orderbook_gap_hunt` maps to `OkxMarkOrderbookGapHuntAdapter`.
- Existing registry/config lookup can instantiate the OKX adapter id without modifying `tools/collect_market_data.py`.
- Adapter listing exposes the new OKX adapter id.
- Registration does not add private/auth/order/account/balance/position/transfer fields.
- Registration does not change active strategy.
- OKX `index_price=None` remains a watch item without policy changes.

## 10. What this does not prove

- It does not prove live OKX endpoint reachability through `collect_market_data`.
- It does not prove user-local OKX collect smoke success.
- It does not prove sampling integration.
- It does not prove profitability or persistent edge.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not implement multi-venue composite.
- It does not implement generic/base adapter extraction.
- It does not resolve timestamp freshness / clock-skew policy.
- It does not resolve OKX index/reference semantics.

## 11. Changed files

- `configs/market_data.yaml`
- `src/market_data/registry.py`
- `tests/test_mark_orderbook_gap_hunt_okx_adapter.py`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_okx_config_registry_v0.md`

No `tools/`, sampling implementation, parser/readiness/timestamp/freshness logic, Council, notification, storage, generated data, multi-venue composite, generic/base adapter extraction, or Gemini runtime/prompt files are changed.

## 12. Risks

- Future live OKX `collect_market_data` smoke may fail due to network, exchange, environment, or response-shape issues.
- OKX `index_price=None` remains unresolved and should not be silently fixed in config/registry registration.
- Future PRs could accidentally widen scope into sampling, alert, Council, active promotion, execution, composite, or base extraction if not constrained.
- Human review is required before merge because this PR touches config/registry for an experimental strategy adapter.

## 13. Rollback plan

- Revert this PR.
- Remove `live_okx_mark_orderbook_gap_btc_usdt_swap` from `configs/market_data.yaml`.
- Remove `OkxMarkOrderbookGapHuntAdapter` import and `okx_mark_orderbook_gap_hunt` mapping from `src/market_data/registry.py`.
- Revert the OKX adapter registration assertions in `tests/test_mark_orderbook_gap_hunt_okx_adapter.py`.
- Remove this handoff file.
- Re-run `python -m unittest discover -s tests` and `python tools/collect_market_data.py --list-adapters` after rollback if verification is needed.

## 14. Human review required

Human review should first inspect:

1. `configs/market_data.yaml` to confirm the OKX adapter entry is disabled, experimental, non-active, public-read-only, and `NO_TRADE_ONLY`.
2. `src/market_data/registry.py` to confirm the mapping is limited to `okx_mark_orderbook_gap_hunt` -> `OkxMarkOrderbookGapHuntAdapter`.
3. `tests/test_mark_orderbook_gap_hunt_okx_adapter.py` to confirm registration assertions, no-trade field checks, active strategy check, and Binance/Bybit unchanged checks.
4. This handoff file to confirm scope, risks, rollback, generated artifact handling, and OKX `index_price=None` watch carry-forward.

## 15. No-trade compliance

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
- multi-venue composite implementation: no
- generic/base adapter extraction: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no
- OKX index/reference semantics change: no

## 16. Next recommended step

Record `Mark-Orderbook Gap Hunt User-Local OKX collect_market_data Smoke Evidence v0` in a separate docs-only PR after a human runs the OKX collect command on a normal local network. Keep generated packet JSON out of git and continue carrying the OKX `index_price=None` watch item unless a future policy task explicitly changes interpretation.
