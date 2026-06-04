# Tether Cross-Market Live Smoke Verification v0

## 1. Purpose

Verify the current `live_tether_cross_market_premium` baseline after the Global Reference Diagnostics v0 change, record actual test and live smoke results, and classify whether any remaining live packet blocker is code/config/parser related or environment/network/location related.

This work is verification/evidence only. It does not extend features and does not move into sampling, alerts, Council handoff, active strategy promotion, or execution.

## 2. Current baseline

- `tether_cross_market_premium` remains experimental, non-active, and `NO_TRADE_ONLY`.
- Active strategy remains `cross_exchange_spot_spread_v1`.
- Binance/Bybit/OKX global references are configured to use `USDCUSDT` or `USDC-USDT` public spot candidates with `normalize: inverse`.
- The experimental live composite has `min_successful_global_references: 1`.
- Previous unit tests recorded in `docs/pr_handoffs/tether_cross_market_global_reference_diagnostics_v0.md` passed, but live packet creation from the Codex workspace was not confirmed because public exchange access was blocked by a 403 network tunnel.

## 3. Changed files

- Added: `docs/pr_handoffs/tether_cross_market_live_smoke_verification_v0.md`.
- No runtime code changed.
- No config changed.
- No tests changed.
- Generated packet JSON files were not committed.

## 4. Tests run

### Baseline status commands

```text
git status
git diff --name-only
git diff --stat
```

Result:

```text
On branch work
nothing to commit, working tree clean
```

`git diff --name-only` and `git diff --stat` printed no output before the evidence file was added.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: pass.

```text
Ran 248 tests in 9.932s
OK
```

Note: the suite emitted existing Gemini/auth warmup log lines and timeout text, but the unittest process exited successfully with `OK`.

### Tether-specific unit test

```text
python -m unittest discover -s tests -p "test_tether_cross_market_live_composite_adapter.py"
```

Result: pass.

```text
Ran 15 tests in 0.066s
OK
```

### Adapter registry check

```text
python tools/collect_market_data.py --list-adapters
```

Result: pass. Required adapters were present:

- `live_tether_cross_market_premium`
- `live_binance_usdt_reference`
- `live_bybit_usdt_reference`
- `live_okx_usdt_reference`
- `replay_tether_cross_market_premium`

## 5. Domestic adapter smoke results

### Upbit USDT/KRW

```text
python tools/collect_market_data.py --adapter live_upbit_usdt_krw_spot --output data/generated_packets/debug_upbit_usdt_krw_spot.json
```

Result: failed with environment/network tunnel blocker.

```text
Market data collection failed: Network error for https://api.upbit.com/v1/ticker?markets=KRW-USDT: Tunnel connection failed: 403 Forbidden
EXIT:1
```

### Bithumb USDT/KRW

```text
python tools/collect_market_data.py --adapter live_bithumb_usdt_krw_spot --output data/generated_packets/debug_bithumb_usdt_krw_spot.json
```

Result: failed with environment/network tunnel blocker.

```text
Market data collection failed: Network error for https://api.bithumb.com/public/ticker/USDT_KRW: Tunnel connection failed: 403 Forbidden
EXIT:1
```

## 6. Global reference smoke results

### Binance USDT reference

```text
python tools/collect_market_data.py --adapter live_binance_usdt_reference --output data/generated_packets/debug_binance_usdt_reference.json
```

Result: failed with environment/network tunnel blocker, but diagnostics showed the corrected candidate endpoint and symbol.

```text
Market data collection failed: Global USDT reference adapter live_binance_usdt_reference failed all candidates: live_binance_usdt_reference[binance] candidate=0 endpoint=/api/v3/ticker/bookTicker symbol=USDCUSDT stage=http_get status=None code=None message=Network error for https://api.binance.com/api/v3/ticker/bookTicker?symbol=USDCUSDT: Tunnel connection failed: 403 Forbidden
EXIT:1
```

### Bybit USDT reference

```text
python tools/collect_market_data.py --adapter live_bybit_usdt_reference --output data/generated_packets/debug_bybit_usdt_reference.json
```

Result: failed with environment/network tunnel blocker, but diagnostics showed the corrected candidate endpoint and symbol.

```text
Market data collection failed: Global USDT reference adapter live_bybit_usdt_reference failed all candidates: live_bybit_usdt_reference[bybit] candidate=0 endpoint=/v5/market/tickers symbol=USDCUSDT stage=http_get status=None code=None message=Network error for https://api.bybit.com/v5/market/tickers?category=spot&symbol=USDCUSDT: Tunnel connection failed: 403 Forbidden
EXIT:1
```

### OKX USDT reference

```text
python tools/collect_market_data.py --adapter live_okx_usdt_reference --output data/generated_packets/debug_okx_usdt_reference.json
```

Result: failed with environment/network tunnel blocker, but diagnostics showed the corrected candidate endpoint and instId.

```text
Market data collection failed: Global USDT reference adapter live_okx_usdt_reference failed all candidates: live_okx_usdt_reference[okx] candidate=0 endpoint=/api/v5/market/ticker symbol=USDC-USDT stage=http_get status=None code=None message=Network error for https://www.okx.com/api/v5/market/ticker?instId=USDC-USDT: Tunnel connection failed: 403 Forbidden
EXIT:1
```

## 7. Composite live smoke result

```text
python tools/collect_market_data.py --adapter live_tether_cross_market_premium --output data/generated_packets/live_tether_cross_market_packet.json
```

Result: failed before global reference collection because the domestic Upbit public endpoint was blocked by the workspace network tunnel.

```text
Market data collection failed: Domestic child adapter live_upbit_usdt_krw_spot failed: Network error for https://api.upbit.com/v1/ticker?markets=KRW-USDT: Tunnel connection failed: 403 Forbidden
EXIT:1
```

Composite live smoke did not create a confirmed live packet in this workspace.

## 8. Packet field summary, if smoke succeeded

Not run because composite live smoke failed. The required packet-summary Python snippet was intentionally not executed because the live composite output JSON was not created.

## 9. Failure classification, if smoke failed

Classification: environment/network/location blocker, not a code/config/parser failure.

Evidence:
- Both domestic public exchange calls failed with `Tunnel connection failed: 403 Forbidden`.
- All global public exchange calls failed at `parser_stage=http_get` with `Tunnel connection failed: 403 Forbidden`.
- Global diagnostics show corrected endpoint/symbol candidates (`USDCUSDT` for Binance/Bybit and `USDC-USDT` for OKX), so the previous symbol-direction blocker is no longer the observed failure in this workspace.
- Unit tests for parser, inverse normalization, diagnostics, partial global success, all-global failure, domestic fail-fast, and replay preservation passed.

## 10. Risks

- Live packet generation remains unverified from this Codex workspace because public exchange network access is blocked.
- A successful live verification still needs to be run from a network/location that can reach Upbit, Bithumb, Binance, Bybit, and OKX public endpoints.
- Since domestic adapters are intentionally fail-fast, any domestic network/access issue blocks the composite before global partial-success behavior can be observed.
- This evidence file should not be interpreted as approval to proceed to sampling, alerts, Council handoff, active promotion, or execution.

## 11. Rollback plan

- Revert this evidence file if the verification record needs to be removed or replaced.
- Re-run `python -m unittest discover -s tests` after rollback.
- Delete any generated files under `data/generated_packets/` that were created only for local smoke testing.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.

## 12. Human review required

Human review is required before treating live smoke as complete. Reviewer should inspect:

1. `docs/pr_handoffs/tether_cross_market_live_smoke_verification_v0.md`
2. The console outputs for live smoke commands, especially the `403 Forbidden` network tunnel failures.
3. Existing diagnostics/config files only if deciding whether a follow-up live verification should be run from another environment.

## 13. No-trade compliance

- private API: no
- API key/secret/token: no
- auth/private headers: no
- account/balance lookup: no
- order/cancel: no
- withdrawal/deposit/transfer: no
- fiat/bank transfer: no
- auto-trading: no
- Council auto-call: no
- Council decision to trade conversion: no
- active strategy promotion: no
- sampling/alert expansion: no
- FX / USD-KRW / fair_usdt_krw_price calculation: no

## 14. Next recommended step

Run the same smoke sequence from a network/location that can reach all required public exchange endpoints. If live composite succeeds there, record the packet field summary and keep the generated JSON out of git. If it fails there with exchange status/code/parser diagnostics rather than tunnel `403`, open a separate small bugfix task scoped to the exact adapter/config/parser issue.
