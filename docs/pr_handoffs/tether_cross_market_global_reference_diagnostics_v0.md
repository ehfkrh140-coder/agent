# Tether Cross-Market Global Reference Diagnostics v0

## 1. Purpose

Diagnose and conservatively fix the live packet blocker for `live_tether_cross_market_premium`, where all Binance/Bybit/OKX global USDT reference adapters failed because the configured public spot reference symbols were pointed at the likely unsupported `USDT/USDC` direction instead of the available `USDC/USDT` direction.

This is an experimental adapter/blocker fix only. It keeps the project in the current `NO_TRADE_ONLY` phase.

## 2. Changed files

- `src/market_data/adapters/global_usdt_reference.py` — adds candidate-based public ticker attempts, inverse bid/ask normalization, and per-candidate diagnostics.
- `src/market_data/adapters/composite.py` — keeps domestic adapters fail-fast while allowing the global reference basket to pass when at least the configured minimum succeeds.
- `src/market_data/http_client.py` — preserves public GET behavior while adding HTTP status and safe response preview fields for diagnostics.
- `configs/market_data.yaml` — points Binance/Bybit/OKX candidates at public `USDC/USDT` spot references with `normalize: inverse`, and sets `min_successful_global_references: 1` for the experimental composite.
- `tests/test_tether_cross_market_live_composite_adapter.py` — covers inverse normalization, diagnostics, partial success, all-failure, domestic fail-fast, replay preservation, and no-trade guardrails.
- `docs/pr_handoffs/tether_cross_market_global_reference_diagnostics_v0.md` — this review evidence file.

## 3. Impact scope

Impacted:
- Experimental `tether_cross_market_premium` live global reference adapters.
- Experimental `live_tether_cross_market_premium` composite packet creation.
- Public read-only HTTP diagnostics for market-data GET failures.

Not impacted:
- Active strategy remains `cross_exchange_spot_spread_v1`.
- Replay tether packet behavior should remain valid.
- Existing active cross-exchange spot spread behavior is not changed.
- Orderbook imbalance behavior is not changed.
- No sampling, alert, Council runtime, prompt, FX, USD/KRW, or execution surface is added.

## 4. Behavior before / after

Before:
- Binance requested `USDTUSDC` and could return HTTP 400.
- Bybit requested `USDTUSDC` spot and could return `10001: Not supported symbols`.
- OKX requested `USDT-USDC` and could return `51001` instrument-not-found.
- If all global references failed, the composite error only listed adapter ids and did not preserve endpoint/symbol/stage diagnostics.

After:
- Binance candidate requests public `USDCUSDT` and normalizes to `USDT/USDC` with inverse bid/ask.
- Bybit candidate requests public spot `USDCUSDT` and normalizes to `USDT/USDC` with inverse bid/ask.
- OKX candidate requests public `USDC-USDT` and normalizes to `USDT/USDC` with inverse bid/ask.
- Inverse normalization uses `inverse_bid = 1 / raw_ask` and `inverse_ask = 1 / raw_bid`.
- Non-positive raw bid/ask fails normalization and records diagnostics.
- Domestic Upbit/Bithumb child failure remains fail-fast.
- Global references pass when at least `min_successful_global_references` succeeds; default/configured value is `1` for this experimental composite.
- If all global references fail, the error includes adapter, venue, endpoint, symbol/instId, parser stage, HTTP status, exchange code/message where available, and reason.

## 5. Diagnostics added

Per-candidate global reference diagnostics include:
- `adapter_id`
- `venue_id`
- `candidate_index`
- `base_url`
- `endpoint` / `ticker_path`
- `request_params` with symbol or instId
- `response_format`
- `parser_stage` (`http_get`, `parse`, or `normalize`)
- `http_status` when available
- `exchange_error_code` when available
- `exchange_error_message` when available
- `error_message`
- `safe_response_preview` when available, capped and with no credentials or headers

Successful snapshots also record selected candidate metadata and diagnostics summary in observation extensions and adapter metadata. Composite snapshots record successful global count, failed global references, global diagnostics, and minimum required global references.

## 6. Tests run

Completed:
- `python -m unittest tests/test_tether_cross_market_live_composite_adapter.py` — pass, 15 tests.
- `python -m unittest discover -s tests` — pass, 248 tests.

Targeted coverage in this PR:
- Binance mocked success with `USDCUSDT` inverse normalization.
- Bybit mocked success with `category=spot`, `symbol=USDCUSDT`, and inverse normalization.
- OKX mocked success with `instId=USDC-USDT` and inverse normalization.
- Per-adapter HTTP/exchange diagnostics.
- Partial global success with only Binance succeeding.
- All global failure with adapter-specific diagnostics in the error.
- Domestic child failure fail-fast behavior.
- No-trade guard over config/code.

## 7. Manual smoke

Command run:

```text
python tools/collect_market_data.py --adapter live_tether_cross_market_premium --output data/generated_packets/live_tether_cross_market_packet.json
```

Result: failed due to this workspace's live network tunnel rejecting public exchange access before global references were reached:

```text
Market data collection failed: Domestic child adapter live_upbit_usdt_krw_spot failed: Network error for https://api.upbit.com/v1/ticker?markets=KRW-USDT: Tunnel connection failed: 403 Forbidden
```

Additional read-only global adapter probe run:

```text
python - <<'PY'
from src.market_data.registry import load_market_data_config, build_adapter
config=load_market_data_config('configs/market_data.yaml')
for adapter_id in ['live_binance_usdt_reference','live_bybit_usdt_reference','live_okx_usdt_reference']:
    try:
        snapshot=build_adapter(adapter_id, config).fetch_snapshot()
        obs=snapshot['observations'][0]
        print(adapter_id, 'OK', obs['extensions']['api_market'], obs['bid'], obs['ask'], obs['extensions']['selected_candidate'])
    except Exception as exc:
        print(adapter_id, 'FAIL', exc)
        print(getattr(exc,'diagnostics',None))
PY
```

Result: all three public global endpoints were also blocked by the workspace network tunnel with `Tunnel connection failed: 403 Forbidden`; diagnostics still showed the corrected endpoint/symbol candidates: Binance `USDCUSDT`, Bybit `category=spot&symbol=USDCUSDT`, and OKX `USDC-USDT`.

Why unit tests still pass: mocked tests are network-free and verify the parser, inverse normalization, per-adapter diagnostics, partial global success, all-global failure, domestic fail-fast, replay preservation, and no-trade guard behavior deterministically.

Next confirmation point: run the same smoke from a network/location that can reach Upbit, Bithumb, Binance, Bybit, and OKX public endpoints.

## 8. Risks

- Risk class: adapter / packet-builder-adjacent diagnostics for an experimental strategy.
- Public exchange symbol availability can change; diagnostics are designed to make future endpoint/symbol/parser failures auditable.
- Partial global success is conservative but means the packet can be built with only one global reference; downstream readiness remains evaluate-only and no-trade.
- Human review should verify that inverse normalization is mathematically correct and that `min_successful_global_references: 1` is acceptable for experimental data collection.

## 9. Rollback plan

- Revert this PR.
- Re-run `python -m unittest discover -s tests`.
- Re-run the read-only smoke command if network access is available.
- Confirm active strategy is still `cross_exchange_spot_spread_v1`.
- Delete any generated local smoke packet if it is not intentionally committed.

## 10. Human review required

Human review is required before merge because this touches adapter behavior and experimental strategy live packet generation. Review these files first:

1. `src/market_data/adapters/global_usdt_reference.py`
2. `src/market_data/adapters/composite.py`
3. `configs/market_data.yaml`
4. `tests/test_tether_cross_market_live_composite_adapter.py`
5. `docs/pr_handoffs/tether_cross_market_global_reference_diagnostics_v0.md`

## 11. No-trade compliance

- private API: no
- API key/secret/token: no
- auth/private headers: no
- account/balance lookup: no
- order/cancel: no
- withdrawal/deposit/transfer: no
- fiat/bank transfer: no
- auto-trading: no
- Council auto-call: no
- active strategy promotion: no
- Council decision to trade conversion: no
- FX / USD-KRW / fair_usdt_krw_price calculation: no
- no_trade_policy weakened or deleted: no

## 12. Future execution note

This PR does not implement execution.

Future execution/risk engine work must be introduced by a separate task card, separate policy update, explicit human review, credential isolation, dry-run/paper-trading phase, and rollback/kill-switch plan.

Do not weaken the current NO_TRADE_ONLY policy in this PR.
