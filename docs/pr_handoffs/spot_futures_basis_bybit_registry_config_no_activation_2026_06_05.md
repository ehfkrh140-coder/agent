# Spot-Futures Basis Bybit Registry / Config No Activation v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 Bybit public-read-only adapter를 registry/config에 disabled / experimental / non-active / `NO_TRADE_ONLY` 상태로 추가한 결과를 기록한다.

목적:

- `live_bybit_spot_futures_basis_btcusdt` adapter entry를 `configs/market_data.yaml`에 추가한다.
- `bybit_spot_futures_basis` adapter type을 registry `build_adapter(...)`에서 생성 가능하게 한다.
- Binance + Bybit multi-venue cycle을 유지하되 Bybit adapter를 활성화하지 않는다.
- Active strategy 또는 collect/sampling behavior를 변경하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. 변경 파일

| File | Change |
| --- | --- |
| `src/market_data/registry.py` | Imported `BybitSpotFuturesBasisAdapter` and added a `bybit_spot_futures_basis` build branch. |
| `configs/market_data.yaml` | Added disabled experimental/non-active Bybit Spot-Futures Basis adapter config. |
| `tests/test_spot_futures_basis_bybit_registry_config.py` | Added registry/config no-activation tests for the Bybit adapter entry and OKX deferred scope. |
| `docs/pr_handoffs/spot_futures_basis_bybit_registry_config_no_activation_2026_06_05.md` | Added this handoff evidence document. |

## 3. Registry/config implementation summary

Implementation summary:

- Added `BybitSpotFuturesBasisAdapter` import to the market-data registry.
- Added `adapter_type == "bybit_spot_futures_basis"` branch to `build_adapter(...)`.
- Added `live_bybit_spot_futures_basis_btcusdt` config entry.
- The Bybit entry is `enabled: false`, `experimental: true`, `experimental_strategy: true`, `non_active_strategy: true`, `no_trade_only: true`, and `execution_policy: NO_TRADE_ONLY`.
- The existing Binance `binance_spot_futures_basis` registry branch remains unchanged.
- No auto-enable logic was added.

## 4. Adapter config metadata

Bybit adapter config metadata:

- `type: bybit_spot_futures_basis`
- `enabled: false`
- `experimental: true`
- `experimental_strategy: true`
- `non_active_strategy: true`
- `no_trade_only: true`
- `execution_policy: NO_TRADE_ONLY`
- `strategy_family: spot_futures_basis`
- `strategy_id: spot_futures_basis_v0`
- `source_venue_id: bybit`
- `signal_type: spot_futures_basis`
- `asset: BTC`
- `quote: USDT`
- `comparison_type: same_exchange_spot_perp_basis`
- `base_url: https://api.bybit.com`
- `spot_symbol: BTCUSDT`
- `perp_symbol: BTCUSDT`
- `spot_category: spot`
- `perp_category: linear`
- `depth_limit: 5`
- `timeout_seconds: 10`
- `max_retries: 2`
- `user_agent: agent-council-market-data-v1`
- `fee_slippage_buffer_pct: 0.20`
- `note: Public read-only, experimental/non-active, NO_TRADE_ONLY, not active, no execution, no Council auto-call, OKX deferred.`

Forbidden private/execution metadata was not added:

- No credentials.
- No API keys/secrets/tokens.
- No account/balance/position fields.
- No order/cancel/withdraw/deposit/transfer fields.
- No `execution_enabled`, `auto_trade`, `alert_enabled`, or `council_auto_call` keys.

## 5. No activation / active strategy unchanged

No activation evidence:

- `live_bybit_spot_futures_basis_btcusdt` is `enabled=false`.
- Existing `live_binance_spot_futures_basis_btcusdt` remains `enabled=false`.
- Existing active baseline adapter `live_upbit_bithumb_spot_spread` remains enabled and uses `cross_exchange_spot_spread_v1`.
- `spot_futures_basis_v0` is not promoted to active.
- No active strategy config was changed.

## 6. Tests added

Added `tests/test_spot_futures_basis_bybit_registry_config.py` with coverage for:

- Bybit config entry exists and is disabled / experimental / non-active / `NO_TRADE_ONLY`.
- Registry `build_adapter(...)` returns `BybitSpotFuturesBasisAdapter` without calling `fetch_snapshot()`.
- `list_adapters(...)` includes `live_bybit_spot_futures_basis_btcusdt`.
- Config has no forbidden private/account/execution keys.
- Existing active baseline remains unchanged and Binance/Bybit Spot-Futures Basis entries remain disabled.
- Collect smoke not executed and user-local collect smoke next step is documented.
- No OKX Spot-Futures Basis config entry was added.

## 7. Collect path follow-up

- Bybit adapter is now buildable through registry/config, but user-local collect smoke was not executed in this PR.
- collect smoke not executed.
- Next step is user-local public-read-only collect smoke.
- user-local collect smoke next.
- Generated packet JSON must not be committed.
- Future collect output under `data/generated_packets/*.json` must be treated as a local smoke artifact and summarized in docs only.

## 8. Explicitly not implemented

Not implemented in this PR:

- `collect_market_data` 실행 없음.
- `sample_market_data` 실행 없음.
- User-local live smoke 없음.
- Sampling support/evidence 없음.
- `OpportunityPacketBuilder` change 없음.
- Active strategy 변경 없음.
- Live endpoint 호출 없음.
- Generated JSON 생성 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Execution 없음.
- Alert 없음.
- Council auto-call 없음.
- Auto-trading 없음.
- OKX implementation/research 없음.

## 9. OKX deferred scope note

- 이번 `spot_futures_basis_v0` cycle은 Binance + Bybit까지만 진행한다.
- OKX는 future expansion으로 defer한다.
- This is scope control, not permanent rejection.
- 이번 PR에서는 OKX adapter/config/research를 만들지 않았다.

## 10. No-trade compliance

No-trade compliance 확인:

- Active strategy promotion 없음.
- `spot_futures_basis_v0` active 승격 없음.
- `enabled=false`.
- Private API 없음.
- Credentials 없음.
- Account/balance/position lookup 없음.
- Order/cancel 없음.
- Withdrawal/deposit/transfer 없음.
- Auto-trading 없음.
- Council auto-call 없음.
- Alert 없음.
- Execution 없음.
- Generated JSON 파일 생성 없음.
- `NO_TRADE_ONLY` 유지.

## 11. Generated JSON commit 금지 확인

Generated JSON policy:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- 이번 PR에는 `data/market_samples` 또는 `data/generated_packets` 변경 없음.
- Future Bybit collect/sampling output은 evidence 요약 후 삭제해야 함.

## 12. Rollback plan

Scoped rollback:

1. Revert this PR.
2. Remove the `bybit_spot_futures_basis` registry branch and import from `src/market_data/registry.py`.
3. Remove `live_bybit_spot_futures_basis_btcusdt` from `configs/market_data.yaml`.
4. Remove `tests/test_spot_futures_basis_bybit_registry_config.py`.
5. Remove this handoff document.
6. No adapter/parser/readiness/packet-builder/tools/generated-data rollback is required because those areas were not changed.

## 13. 다음 PR 후보

Recommended next PR sequence:

1. Bybit user-local collect smoke.
2. Docs-only Bybit collect evidence.
3. Bybit user-local 3-sample sampling evidence.
4. Bybit user-local 30-sample extended sampling evidence.
5. OKX public source research against common contract as future expansion.
