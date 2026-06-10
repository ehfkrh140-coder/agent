# Spot-Futures Basis Bybit Packet Builder Compatibility v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0`의 Bybit Spot BTCUSDT + Bybit USDT linear perpetual BTCUSDT parser/source bundle output이 pure `opportunity_packet_v0` packet builder를 통과할 수 있도록 packet identity compatibility를 보완한 결과를 기록한다.

목적:

- Bybit parser/source bundle + readiness result를 `build_spot_futures_basis_opportunity_packet(...)`에 입력했을 때 Bybit venue-correct observation/candidate identity를 생성한다.
- `OpportunityPacketBuilder().build(packet_dict)` validation을 mocked/unit-test only로 검증한다.
- 기존 Binance packet builder identity와 behavior를 유지한다.
- Bybit adapter, registry/config, live collect, sampling evidence는 구현하지 않는다.
- `NO_TRADE_ONLY`를 유지한다.

## 2. 변경 파일

| File | Change |
| --- | --- |
| `src/market_data/spot_futures_basis_packet_builder.py` | Added venue-neutral packet identity derivation while preserving Binance hardcoded regression identity; propagated source venue, observation ids, candidate ids, generated_from, and Bybit category/funding metadata into packet output. |
| `tests/test_spot_futures_basis_bybit_packet_builder.py` | Added mocked/unit tests covering Bybit packet identity, observation mapping, candidate metrics, OpportunityPacket validation, WATCH/no-trade behavior, no-private guardrails, and Binance identity regression. |
| `docs/pr_handoffs/spot_futures_basis_bybit_packet_builder_compatibility_2026_06_05.md` | Added this handoff evidence document. |

## 3. Bybit packet builder compatibility summary

The packet builder now derives packet identity from the normalized source bundle instead of always using Binance candidate/observation ids.

Bybit-compatible behavior:

- `source_bundle.source_venue_id=bybit` is preserved in packet extensions and candidate venue fields.
- Bybit Spot observation id becomes `bybit_spot_btcusdt_spot_futures_basis`.
- Bybit linear perpetual observation id becomes `bybit_linear_btcusdt_perp_spot_futures_basis`.
- Bybit candidate id becomes `bybit_btcusdt_spot_futures_basis_candidate`.
- `detector_metadata.generated_from` includes Bybit and linear source-bundle context.
- Bybit observation venue names come from parser output: `Bybit Spot` and `Bybit Derivatives V5`.
- `OpportunityPacketBuilder().build(packet_dict)` validates the Bybit packet dict without adapter/config/registry changes.

## 4. Venue-neutral identity mapping

Venue-neutral identity derivation:

| Packet field | Binance regression | Bybit compatibility |
| --- | --- | --- |
| `extensions.source_venue_id` | `binance` | `bybit` |
| Spot observation id | `binance_spot_btcusdt_spot_futures_basis` | `bybit_spot_btcusdt_spot_futures_basis` |
| Perp observation id | `binance_usdm_btcusdt_perp_spot_futures_basis` | `bybit_linear_btcusdt_perp_spot_futures_basis` |
| Candidate id | `binance_btcusdt_spot_futures_basis_candidate` | `bybit_btcusdt_spot_futures_basis_candidate` |
| Candidate `source_venue_id` | `binance` | `bybit` |
| Candidate `target_venue_id` | `binance` | `bybit` |
| Detector `generated_from` | Existing Binance mocked source bundle | Bybit mocked spot/linear source bundle |

No venue-specific strategy class was added. Both venues still use:

- `strategy_family=spot_futures_basis`
- `strategy_id=spot_futures_basis_v0`
- `comparison_type=same_exchange_spot_perp_basis`

## 5. Bybit observation/candidate mapping coverage

Bybit observation packet mapping now preserves:

- Spot `venue_id=bybit`
- Spot `venue_name=Bybit Spot`
- Spot `instrument_type=spot`
- Spot `market_symbol=BTCUSDT`
- Spot parser status and required missing fields in extensions
- Perp `venue_id=bybit`
- Perp `venue_name=Bybit Derivatives V5`
- Perp `instrument_type=linear_perpetual`
- Perp `extensions.category=linear`
- Perp mark/index/funding context in observation/derivatives fields
- Perp parser status and required missing fields in extensions

Bybit candidate packet mapping now preserves:

- `candidate_type=spot_futures_basis_observation`
- selected direction from readiness metrics
- `readiness_status`
- `recommended_default_decision`
- `readiness_pass`
- `selected_gross_basis_pct`
- `estimated_net_basis_pct`
- compatibility alias `estimated_net_gap_pct`
- `required_missing_fields=[]` for the deterministic fixture path
- no-trade assumptions, including `WATCH is not ENTER` and `no trading behavior`

## 6. Binance regression coverage

Binance behavior remains covered by existing packet builder tests and the new Bybit packet builder regression test.

Regression expectations preserved:

- Binance spot observation id remains `binance_spot_btcusdt_spot_futures_basis`.
- Binance USDⓈ-M perp observation id remains `binance_usdm_btcusdt_perp_spot_futures_basis`.
- Binance candidate id remains `binance_btcusdt_spot_futures_basis_candidate`.
- Binance packet/candidate `source_venue_id` remains `binance`.
- Existing Binance mocked parser, readiness, packet builder, collect path, and sampling tests continue to pass.

## 7. Tests added

Added `tests/test_spot_futures_basis_bybit_packet_builder.py` with coverage for:

- Bybit packet identity and non-Binance ids.
- Bybit observation mapping and category preservation.
- Bybit candidate mapping and readiness metrics propagation.
- Validation through `OpportunityPacketBuilder().build(packet_dict)`.
- Mutated Bybit WATCH case that remains `NO_TRADE_ONLY`.
- No private/account/execution forbidden substrings in packet dict and validated model dump.
- Binance identity regression.

## 8. Bybit-specific watch items preserved

Preserved as parser/source metadata or packet assumptions/watch context:

- `category=spot` vs `category=linear`.
- Bybit `retCode` / `retMsg` envelope remains parser/source metadata, not a trading signal.
- `funding_interval=480` remains context/warning candidate, not a trading signal.
- Negative `data_age_ms` / timestamp clock-skew watch remains unclamped when present.
- Same `BTCUSDT` symbol string does not imply identical spot/perp product semantics.
- Mark/index/funding context is not executable basis.
- Top-of-book liquidity is not fill feasibility.

## 9. Explicitly not implemented

Not implemented in this PR:

- Bybit adapter 구현 없음.
- Config/registry 변경 없음.
- Live endpoint 호출 없음.
- `collect_market_data` 실행 없음.
- `sample_market_data` 실행 없음.
- Generated JSON 생성 없음.
- Readiness threshold 변경 없음.
- Parser behavior 변경 없음.
- Private API 없음.
- Credentials 없음.
- Account/balance/position/order/cancel/withdraw/deposit/transfer 없음.
- Execution 없음.
- Alert 없음.
- Council auto-call 없음.
- Auto-trading 없음.
- OKX implementation/research 없음.

## 10. OKX deferred scope note

- 이번 `spot_futures_basis_v0` multi-venue cycle은 Binance + Bybit까지만 진행한다.
- OKX는 future expansion으로 defer한다.
- This is scope control, not permanent rejection.
- 이번 PR에서는 OKX fixture/research/implementation 파일을 만들지 않았다.

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
- Source/runtime behavior 변경은 packet builder pure dict mapping compatibility에 한정됨.
- `NO_TRADE_ONLY` 유지.

## 12. Generated JSON commit 금지 확인

Generated JSON policy:

- `data/market_samples/*.json`는 smoke artifact이며 commit 금지.
- `data/generated_packets/*.json`는 smoke artifact이며 commit 금지.
- 이번 PR은 mocked fixture pipeline only이며 generated JSON을 추가하지 않음.
- Future Bybit smoke/sampling output은 evidence 요약 후 삭제해야 함.

## 13. Rollback plan

Docs/test/packet-builder scoped rollback:

1. Revert this PR.
2. Remove `tests/test_spot_futures_basis_bybit_packet_builder.py`.
3. Remove this handoff document.
4. Restore `src/market_data/spot_futures_basis_packet_builder.py` to prior Binance-first identity behavior.
5. No adapter/config/registry/runtime/parser/readiness/fixture/generated-data rollback is required because those areas were not changed.

## 14. 다음 PR 후보

Recommended next PR sequence:

1. Bybit public-read-only adapter implementation, mocked/unit tests.
2. Bybit registry/config no activation.
3. Bybit user-local collect smoke.
4. Docs-only Bybit collect evidence.
5. Bybit user-local 3-sample sampling evidence.
6. Bybit user-local 30-sample extended sampling evidence.
7. OKX public source research against common contract as future expansion.
