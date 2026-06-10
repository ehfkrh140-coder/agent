# Spot-Futures Basis Bybit Public-Read-Only Adapter Implementation with Mocked Unit Tests v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 Bybit Spot BTCUSDT + Bybit USDT linear perpetual BTCUSDT public-read-only adapter 구현 결과를 기록한다.

목적:

- Bybit public source research, mocked fixtures, parser/source mapping, packet builder compatibility 이후 first Bybit adapter boundary를 추가한다.
- Adapter는 injectable HTTP client를 통해 mocked Bybit V5 public payloads를 받아 기존 parser/readiness/packet builder pipeline에 연결한다.
- Binance-only strategy가 되지 않도록 Bybit도 common source contract와 `spot_futures_basis_v0` family를 재사용한다.
- Bybit 전용 strategy class/family를 만들지 않는다.
- 이번 PR은 mocked/unit-test only adapter implementation이며 live endpoint 호출, registry/config 변경, collect/sampling evidence 작업이 아니다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. 변경 파일

| File | Change |
| --- | --- |
| `src/market_data/adapters/spot_futures_basis.py` | Added `BybitSpotFuturesBasisAdapter`, Bybit endpoint specs, Bybit public fetch flow, diagnostics preservation, and Bybit adapter metadata while preserving Binance adapter behavior. |
| `tests/test_spot_futures_basis_bybit_adapter.py` | Added mocked/unit tests for Bybit adapter packet creation, expected public endpoint calls, metadata/diagnostics, parser/readiness/packet-builder integration, safe error handling, no-generated/no-private guardrails, WATCH no-trade behavior, and Binance import regression. |
| `docs/pr_handoffs/spot_futures_basis_bybit_public_read_only_adapter_2026_06_05.md` | Added this handoff evidence document. |

## 3. Bybit adapter implementation summary

Added `BybitSpotFuturesBasisAdapter` with the following identity:

- `adapter_id=live_bybit_spot_futures_basis_btcusdt` by default.
- `adapter_type=bybit_spot_futures_basis`.
- `strategy_family=spot_futures_basis`.
- `strategy_id=spot_futures_basis_v0`.
- `status=experimental_non_active_no_trade_only`.
- `execution_policy=NO_TRADE_ONLY`.
- `source_venue_id=bybit` through the normalized parser/source bundle and packet extensions.

Constructor supports:

- Optional `adapter_id`.
- Optional config dict.
- Optional injectable `http_client`.
- Optional injectable `now_fn`.
- No credentials.
- No private API config.
- No account/balance/order options.

Default Bybit config values:

- `base_url=https://api.bybit.com`.
- `spot_symbol=BTCUSDT`.
- `perp_symbol=BTCUSDT`.
- `spot_category=spot`.
- `perp_category=linear`.
- `depth_limit=5`.

## 4. Public endpoint call set

The Bybit adapter public call set is:

| Parser stage | Path | Params |
| --- | --- | --- |
| `spot_ticker` | `/v5/market/tickers` | `category=spot`, `symbol=BTCUSDT` |
| `spot_orderbook` | `/v5/market/orderbook` | `category=spot`, `symbol=BTCUSDT`, `limit=5` |
| `spot_instruments_info` | `/v5/market/instruments-info` | `category=spot`, `symbol=BTCUSDT` |
| `linear_ticker` | `/v5/market/tickers` | `category=linear`, `symbol=BTCUSDT` |
| `linear_orderbook` | `/v5/market/orderbook` | `category=linear`, `symbol=BTCUSDT`, `limit=5` |
| `linear_instruments_info` | `/v5/market/instruments-info` | `category=linear`, `symbol=BTCUSDT` |

All tests use a mocked HTTP client. No real Bybit endpoint was called.

## 5. Parser/readiness/packet builder integration

`fetch_snapshot()` runs the public-read-only mocked pipeline:

1. Fetch six mocked Bybit V5 public payloads through the injected HTTP client.
2. Collect safe endpoint diagnostics.
3. Call `parse_bybit_spot_observation(...)`.
4. Call `parse_bybit_perp_observation(...)`.
5. Call `build_spot_futures_basis_source_bundle(...)`.
6. Call `evaluate_spot_futures_basis_readiness(...)`.
7. Call `build_spot_futures_basis_opportunity_packet(...)`.
8. Attach adapter metadata and diagnostics to packet extensions.
9. Return an OpportunityPacket-compatible dict only.

The adapter does not synthesize any strategy family, readiness policy, packet schema, Council, alert, or execution behavior.

## 6. Diagnostics / adapter metadata coverage

Each endpoint diagnostic preserves safe public metadata:

- `endpoint`
- `params`
- `parser_stage`
- `retCode` when present
- `retMsg` when present
- `http_status` when present
- `safe_response_preview` when present
- `elapsed_ms` when present
- `url` when present

Bybit `retCode` / `retMsg` are diagnostics/source metadata only. They are not trading signals.

Packet extensions include `adapter_metadata` with:

- `adapter_id`
- `adapter_type`
- `venue_id=bybit`
- `spot_venue_name=Bybit Spot`
- `perp_venue_name=Bybit Derivatives V5`
- `spot_category=spot`
- `perp_category=linear`
- `strategy_family=spot_futures_basis`
- `strategy_id=spot_futures_basis_v0`
- `status=experimental_non_active_no_trade_only`
- `experimental_strategy=True`
- `non_active_strategy=True`
- `no_trade_only=True`
- `execution_policy=NO_TRADE_ONLY`
- `endpoints`
- `fetched_at_utc`

Packet assumptions preserve:

- `public no-key endpoints only`
- `analysis-only packet`
- `no private API`
- `no trading behavior`
- `WATCH is not ENTER`
- `mark price is not executable`

## 7. Tests added

Added `tests/test_spot_futures_basis_bybit_adapter.py` with mocked/unit coverage for:

- Bybit adapter `fetch_snapshot()` builds a `NO_TRADE_ONLY` packet.
- Exactly six expected public Bybit V5 endpoint calls are made with spot/linear category separation.
- No private/account/balance/position/order/cancel endpoint semantics are used; public `orderbook` wording is treated as harmless public market-data wording.
- Adapter metadata and six diagnostics preserve parser stages plus `retCode=0` / `retMsg=OK` from fixtures.
- Existing Bybit parser/readiness/packet builder integration is used.
- Bybit observation/candidate ids are venue-correct and not Binance ids.
- Public fetch errors raise `MarketDataAdapterError` with safe redacted messages.
- Structural guardrails verify no generated artifact path references, no file writing, and no private credential module references.
- Mutated WATCH case stays `NO_TRADE_ONLY` and does not add alert/Council/execution fields.
- Binance adapter remains importable with its default adapter id and adapter type.

## 8. Bybit-specific watch items preserved

Preserved watch items:

- `category=spot` vs `category=linear`.
- `retCode` / `retMsg` diagnostics.
- Nested `result.list` remains parser-owned source shape.
- `funding_interval=480` remains context/warning candidate, not a trading signal.
- Negative `data_age_ms` / timestamp clock-skew watch remains parser/readiness concern.
- Same `BTCUSDT` symbol string does not imply identical spot/perp product semantics.
- Mark/index/funding context is not executable basis.
- Top-of-book liquidity is not fill feasibility.

## 9. Explicitly not implemented

Not implemented in this PR:

- Registry/config 변경 없음.
- Active strategy 변경 없음.
- Live endpoint 호출 없음.
- `collect_market_data` 실행 없음.
- `sample_market_data` 실행 없음.
- Generated JSON 생성 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Execution 없음.
- Alert 없음.
- Council auto-call 없음.
- Auto-trading 없음.
- OKX implementation/research 없음.

## 10. OKX deferred scope note

- 이번 `spot_futures_basis_v0` cycle은 Binance + Bybit까지만 진행한다.
- OKX는 future expansion으로 defer한다.
- This is scope control, not permanent rejection.
- 이번 PR에서는 OKX 관련 파일을 만들지 않았다.

## 11. No-trade compliance

No-trade compliance 확인:

- Active strategy promotion 없음.
- `spot_futures_basis_v0` active 승격 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position lookup 없음.
- Order/cancel 없음.
- Withdrawal/deposit/transfer 없음.
- Auto-trading 없음.
- Council auto-call 없음.
- Alert 없음.
- Execution 없음.
- Config/registry 변경 없음.
- Generated JSON 파일 생성 없음.
- `NO_TRADE_ONLY` 유지.

## 12. Generated JSON commit 금지 확인

Generated JSON policy:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- 이번 PR은 mocked fixture pipeline only이며 generated JSON을 추가하지 않음.
- Future Bybit smoke/sampling output은 evidence 요약 후 삭제해야 함.

## 13. Rollback plan

Scoped rollback:

1. Revert this PR.
2. Remove `BybitSpotFuturesBasisAdapter` and Bybit endpoint specs from `src/market_data/adapters/spot_futures_basis.py`.
3. Remove `tests/test_spot_futures_basis_bybit_adapter.py`.
4. Remove this handoff document.
5. No registry/config/tools/generated-data rollback is required because those areas were not changed.

## 14. 다음 PR 후보

Recommended next PR sequence:

1. Bybit registry/config no activation.
2. Bybit user-local collect smoke.
3. Docs-only Bybit collect evidence.
4. Bybit user-local 3-sample sampling evidence.
5. Bybit user-local 30-sample extended sampling evidence.
6. OKX public source research against common contract as future expansion.
