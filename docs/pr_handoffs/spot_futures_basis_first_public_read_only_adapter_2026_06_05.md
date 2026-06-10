# Spot-Futures Basis First Public-Read-Only Adapter Implementation v0

## 1. 작업 목적

이 PR은 `spot_futures_basis_v0`의 first public-read-only adapter class를 추가한다. Adapter는 Binance Spot `BTCUSDT`와 Binance USDⓈ-M Futures `BTCUSDT` public endpoint 후보를 호출할 수 있는 경계를 제공하되, 이번 PR의 tests는 mocked HTTP client만 사용한다.

Purpose:

- Public no-key payloads를 수집하는 first adapter boundary를 구현한다.
- Existing parser, readiness helper, pure OpportunityPacket builder를 연결한다.
- Returned output은 analysis-only OpportunityPacket-compatible dict다.
- Actual live endpoint calls, registry/config integration, active promotion은 수행하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. 변경 파일

Changed files:

- `src/market_data/adapters/spot_futures_basis.py`
- `tests/test_spot_futures_basis_adapter.py`
- `docs/pr_handoffs/spot_futures_basis_first_public_read_only_adapter_2026_06_05.md`

Not changed:

- Existing parser/readiness/packet builder files
- Existing fixture JSON files
- Registry/config files
- `data/market_samples/`
- `data/generated_packets/`

## 3. Adapter implementation summary

Added `BinanceSpotFuturesBasisAdapter` in `src/market_data/adapters/spot_futures_basis.py`.

Adapter identity:

- `DEFAULT_ADAPTER_ID="live_binance_spot_futures_basis_btcusdt"`
- `adapter_type="binance_spot_futures_basis"`
- `strategy_family="spot_futures_basis"`
- `strategy_id="spot_futures_basis_v0"`
- `status="experimental_non_active_no_trade_only"`
- `execution_policy="NO_TRADE_ONLY"`

Constructor behavior:

- Accepts optional `adapter_id`.
- Accepts optional `config` dict.
- Accepts optional injected `http_client`.
- Accepts optional injected `now_fn`.
- Does not require credentials.
- Does not expose private API, account, balance, or order options.

Adapter output:

- `fetch_snapshot()` returns an OpportunityPacket-compatible dict.
- It returns a dict only and writes no files.
- It adds adapter metadata and public fetch diagnostics to packet extensions after the pure packet builder returns.

## 4. Public endpoint call set

Spot base URL default:

- `https://api.binance.com`

Spot public endpoint candidates:

- `GET /api/v3/ticker/bookTicker`
- `GET /api/v3/depth`
- `GET /api/v3/exchangeInfo`

Futures base URL default:

- `https://fapi.binance.com`

Futures public endpoint candidates:

- `GET /fapi/v1/ticker/bookTicker`
- `GET /fapi/v1/depth`
- `GET /fapi/v1/premiumIndex`
- `GET /fapi/v1/exchangeInfo`

Public params:

- Spot symbol: `BTCUSDT`
- Perp symbol: `BTCUSDT`
- Depth limit default: `5`

This PR does not perform real live endpoint calls in tests. Tests use a mocked HTTP client only.

## 5. Parser/readiness/packet builder integration

`fetch_snapshot()` flow:

1. Fetch seven public no-key endpoint candidates through the injected HTTP client.
2. Build safe diagnostics for each endpoint.
3. Pass spot payloads to `parse_binance_spot_observation`.
4. Pass futures payloads to `parse_binance_perp_observation`.
5. Build source bundle via `build_spot_futures_basis_source_bundle`.
6. Evaluate readiness via `evaluate_spot_futures_basis_readiness`.
7. Build packet via `build_spot_futures_basis_opportunity_packet`.
8. Attach adapter metadata and diagnostics to packet extensions.
9. Return the packet dict.

Integration guardrails:

- Adapter does not create a Binance-specific strategy class.
- Binance is the first reference venue only.
- Adapter does not register itself in config/registry.
- `WATCH` remains analysis-only and is not converted to `ENTER`.

## 6. Diagnostics / adapter metadata coverage

Each endpoint diagnostic can include:

- `endpoint`
- `params`
- `parser_stage`
- `http_status`
- `safe_response_preview`
- `elapsed_ms`
- `url`

Parser stages covered:

- `spot_book_ticker`
- `spot_depth`
- `spot_exchange_info`
- `futures_book_ticker`
- `futures_depth`
- `futures_premium_index`
- `futures_exchange_info`

Adapter metadata coverage:

- `adapter_id`
- `adapter_type`
- `venue_id="binance"`
- `spot_venue_name="Binance Spot"`
- `perp_venue_name="Binance USDⓈ-M Futures"`
- `strategy_family="spot_futures_basis"`
- `strategy_id="spot_futures_basis_v0"`
- `status="experimental_non_active_no_trade_only"`
- `experimental_strategy=True`
- `non_active_strategy=True`
- `no_trade_only=True`
- `execution_policy="NO_TRADE_ONLY"`
- `endpoints`
- `fetched_at_utc`

Packet assumptions are preserved/extended with:

- Public no-key endpoints only.
- Analysis-only packet.
- No private API.
- No trading behavior.

## 7. Tests added

Added `tests/test_spot_futures_basis_adapter.py`.

Coverage:

- Builds a no-trade OpportunityPacket-compatible dict from mocked HTTP payloads.
- Verifies exactly seven public endpoint calls.
- Verifies adapter metadata and diagnostics.
- Verifies parser/readiness/packet builder integration via candidate metrics and detector metadata.
- Verifies public fetch error behavior is safe and redacted.
- Verifies adapter source does not reference generated data paths or file-write/read patterns.
- Verifies `WATCH` remains `NO_TRADE_ONLY` through the adapter.
- Recursively checks returned packet keys for forbidden private/account/order/cancel/withdraw/deposit/transfer substrings while allowing schema-required public orderbook context keys.

## 8. Explicitly not implemented

This PR explicitly does not implement:

- Registry/config changes
- Active strategy changes
- Live user-local smoke
- `sample_market_data` integration
- Generated JSON creation
- Private API
- Credentials
- Account/balance/position/order/cancel/withdraw/deposit/transfer handling
- Execution
- Alert
- Council auto-call
- Auto-trading

## 9. No-trade compliance

No-trade compliance for this PR:

- Active strategy promotion: no
- `spot_futures_basis_v0` active promotion: no
- Private API: no
- Credentials/API keys/secrets/tokens: no
- Account/balance/position lookup: no
- Order/cancel: no
- Withdrawal/deposit/transfer: no
- Auto-trading: no
- Council auto-call: no
- Alert: no
- Execution: no
- Config/registry change: no
- Generated JSON file creation: no
- `NO_TRADE_ONLY` preserved: yes

## 10. Generated JSON commit 금지 확인

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

This PR:

- Does not add generated JSON.
- Does not change `data/market_samples`.
- Does not change `data/generated_packets`.
- Adapter `fetch_snapshot()` returns a dict only and writes no files.

## 11. Rollback plan

Rollback path:

1. Revert this adapter PR.
2. Remove `src/market_data/adapters/spot_futures_basis.py`.
3. Remove `tests/test_spot_futures_basis_adapter.py`.
4. Remove `docs/pr_handoffs/spot_futures_basis_first_public_read_only_adapter_2026_06_05.md`.
5. No registry/config/runtime/generated-data rollback is required.

## 12. 다음 PR 후보

Recommended order:

1. Registry/config planning, no activation
2. User-local public-read-only collect smoke
3. Docs-only collect evidence
4. 3-sample sampling support
5. 3-sample sampling evidence
6. 30-sample extended evidence
