# Spot-Futures Basis Registry / Config Implementation, No Activation v0

## 1. 작업 목적

이 문서는 `live_binance_spot_futures_basis_btcusdt` adapter를 registry/config에 experimental / disabled / non-active / `NO_TRADE_ONLY` 상태로 추가한 작은 implementation PR의 handoff이다.

목적:

- `spot_futures_basis_v0` first public-read-only adapter를 `src/market_data/registry.py`와 `configs/market_data.yaml`에서 생성 가능하게 한다.
- Active strategy promotion 없이 config entry를 disabled 상태로 유지한다.
- Live endpoint 호출, collect smoke, sampling support, `OpportunityPacketBuilder` 변경 없이 registry/config 생성 경계만 검증한다.
- `NO_TRADE_ONLY` / analysis-only posture를 유지한다.

## 2. 변경 파일

| File | Change |
| --- | --- |
| `src/market_data/registry.py` | `BinanceSpotFuturesBasisAdapter` import 및 `adapter_type == "binance_spot_futures_basis"` build branch 추가. |
| `configs/market_data.yaml` | `live_binance_spot_futures_basis_btcusdt` adapter entry를 `enabled=false`, experimental, non-active, `NO_TRADE_ONLY` metadata로 추가. |
| `tests/test_spot_futures_basis_registry_config.py` | Config metadata, registry build, adapter listing, forbidden private/execution keys, active baseline unchanged, collect path follow-up wording을 검증하는 unit tests 추가. |
| `docs/pr_handoffs/spot_futures_basis_registry_config_no_activation_2026_06_05.md` | 이 handoff 문서 추가. |

## 3. Registry/config implementation summary

- `src/market_data/registry.py` now imports `BinanceSpotFuturesBasisAdapter`.
- `build_adapter(...)` now returns `BinanceSpotFuturesBasisAdapter(adapter_id, config=adapter_config)` when `adapter_type == "binance_spot_futures_basis"`.
- No active strategy logic was changed.
- No auto-enable logic was added.
- No `fetch_snapshot()` call is introduced by registry build tests.
- `configs/market_data.yaml` now contains a disabled, experimental, non-active, `NO_TRADE_ONLY` config entry for `live_binance_spot_futures_basis_btcusdt`.

## 4. Adapter config metadata

Adapter id:

- `live_binance_spot_futures_basis_btcusdt`

Required metadata added:

- `type: binance_spot_futures_basis`
- `enabled: false`
- `experimental: true`
- `experimental_strategy: true`
- `non_active_strategy: true`
- `no_trade_only: true`
- `execution_policy: NO_TRADE_ONLY`
- `strategy_family: spot_futures_basis`
- `strategy_id: spot_futures_basis_v0`
- `source_venue_id: binance`
- `signal_type: spot_futures_basis`
- `asset: BTC`
- `quote: USDT`
- `comparison_type: same_exchange_spot_perp_basis`
- `spot_base_url: https://api.binance.com`
- `futures_base_url: https://fapi.binance.com`
- `spot_symbol: BTCUSDT`
- `perp_symbol: BTCUSDT`
- `depth_limit: 5`
- `timeout_seconds: 10`
- `max_retries: 2`
- `user_agent: agent-council-market-data-v1`
- `fee_slippage_buffer_pct: 0.20`
- `private_api_required: false`
- `note`: public read-only, experimental/non-active/`NO_TRADE_ONLY`, not active, no execution, no Council auto-call.

Forbidden metadata was not added:

- `credentials`
- `api_key`
- `secret`
- `account`
- `balance`
- `position`
- `order`
- `execution_enabled`
- `auto_trade`
- `alert_enabled`
- `council_auto_call`

## 5. No activation / active strategy unchanged

- Active strategy promotion 없음.
- `spot_futures_basis_v0` active 승격 없음.
- `live_binance_spot_futures_basis_btcusdt.enabled=false`.
- Existing active baseline adapter `live_upbit_bithumb_spot_spread` remains present and enabled.
- Active strategy remains `cross_exchange_spot_spread_v1`.
- This PR does not modify `configs/strategy_current.yaml` or `configs/strategy_registry.yaml`.

## 6. Tests added

Added `tests/test_spot_futures_basis_registry_config.py` with coverage for:

1. `test_config_contains_spot_futures_basis_adapter_disabled_no_trade`
2. `test_registry_builds_spot_futures_basis_adapter_without_live_fetch`
3. `test_list_adapters_includes_spot_futures_basis_adapter`
4. `test_spot_futures_basis_config_has_no_private_or_execution_keys`
5. `test_existing_active_strategy_unchanged`
6. `test_collect_path_not_claimed_yet`

## 7. Explicitly not implemented

- `collect_market_data` integration 없음.
- `sample_market_data` integration 없음.
- User-local live smoke 없음.
- Sampling support 없음.
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

## 8. Collect path follow-up

- `tools/collect_market_data.py` still calls `OpportunityPacketBuilder().build(snapshot)`.
- `spot_futures_basis` packet-compatible adapter output may require `OpportunityPacketBuilder` spot_futures_basis validation/pass-through support.
- user-local collect smoke is not executed in this PR.
- Next PR candidate should verify/implement collect path support with mocked/unit tests before user-local smoke.
- This PR does not claim collect smoke evidence.
- This PR does not add generated `data/generated_packets/*.json` output.

## 9. No-trade compliance

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

## 10. Generated JSON commit 금지 확인

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- 이번 PR에는 `data/market_samples` 또는 `data/generated_packets` 변경 없음.
- Registry/config tests do not write generated JSON.

## 11. Rollback plan

Rollback steps:

1. Remove the `binance_spot_futures_basis` import and build branch from `src/market_data/registry.py`.
2. Remove the `live_binance_spot_futures_basis_btcusdt` entry from `configs/market_data.yaml`.
3. Remove `tests/test_spot_futures_basis_registry_config.py`.
4. Remove this handoff document.
5. Rerun the required unit tests and generated JSON path checks.

No generated-data rollback is required because this PR does not create generated JSON files.

## 12. 다음 PR 후보

Recommended next PR sequence:

1. Collect path support with mocked/unit tests, including `OpportunityPacketBuilder` validation/pass-through if required.
2. User-local public-read-only collect smoke request.
3. Docs-only collect evidence handoff.
4. `sample_market_data` support with mocked/unit tests.
5. User-local 3-sample sampling evidence.
6. User-local 30-sample extended evidence.
