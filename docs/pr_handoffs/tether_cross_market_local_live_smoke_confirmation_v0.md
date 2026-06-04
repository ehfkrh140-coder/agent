# Tether Cross-Market Local Live Smoke Confirmation v0

## 1. Purpose

Confirm whether `live_tether_cross_market_premium` can create a real live packet after PR #63/#64, using the current local/Codex environment, and preserve the exact evidence for tests, adapter registry, domestic/global live smoke, composite live smoke, replay preservation, no-trade safety, and active strategy status.

This task is verification/evidence only. It does not modify runtime code, config, tests, sampling, alerts, Council handoff, active strategy status, or execution behavior.

## 2. Baseline

- Global reference diagnostics, `ticker_candidates`, inverse normalization, and `min_successful_global_references: 1` are already present from the previous diagnostics work.
- Previous evidence records full unit tests passing and identifies the prior Codex workspace live smoke blocker as public-exchange network tunnel `403 Forbidden`.
- Current strategy status remains `tether_cross_market_premium` / `usdt_krw_global_reference_v0` as experimental/non-active/NO_TRADE_ONLY.
- Active strategy remains `cross_exchange_spot_spread_v1`.

## 3. Environment

- Repository path: `/workspace/agent`.
- Branch: `work`.
- Starting HEAD: `da526dd`.
- `git pull --ff-only` could not run because the local `work` branch has no upstream tracking branch configured. This is a repository tracking configuration issue, not a test/code failure.
- Live public exchange requests from this environment still route through a tunnel that returns `403 Forbidden` before exchange payloads can be fetched.

## 4. Changed files

- Added: `docs/pr_handoffs/tether_cross_market_local_live_smoke_confirmation_v0.md`.
- No runtime code changed.
- No config changed.
- No tests changed.
- Generated packet JSON files were removed after smoke and were not committed.

## 5. Tests run

### Repo status / pull

```text
git status
git pull --ff-only
git status
```

Result:

```text
On branch work
nothing to commit, working tree clean
There is no tracking information for the current branch.
Please specify which branch you want to merge with.
...
PULL_EXIT:1
On branch work
nothing to commit, working tree clean
```

### Full unit test

```text
python -m unittest discover -s tests
```

Result: pass.

```text
Ran 248 tests in 13.254s
OK
```

The test suite printed existing Gemini/auth warmup logs, but unittest completed successfully with `OK`.

### Tether-specific unit test

```text
python -m unittest discover -s tests -p "test_tether_cross_market_live_composite_adapter.py"
```

Result: pass.

```text
Ran 15 tests in 0.099s
OK
```

### Adapter registry check

```text
python tools/collect_market_data.py --list-adapters
```

Result: pass. Required adapters were present:

- `live_tether_cross_market_premium`
- `live_upbit_usdt_krw_spot`
- `live_bithumb_usdt_krw_spot`
- `live_binance_usdt_reference`
- `live_bybit_usdt_reference`
- `live_okx_usdt_reference`
- `replay_tether_cross_market_premium`

## 6. Domestic adapter smoke results

### Upbit USDT/KRW

```text
python tools/collect_market_data.py --adapter live_upbit_usdt_krw_spot --output data/generated_packets/debug_upbit_usdt_krw_spot.json
```

Result: failed due to environment/network tunnel.

```text
Market data collection failed: Network error for https://api.upbit.com/v1/ticker?markets=KRW-USDT: Tunnel connection failed: 403 Forbidden
EXIT:1
```

### Bithumb USDT/KRW

```text
python tools/collect_market_data.py --adapter live_bithumb_usdt_krw_spot --output data/generated_packets/debug_bithumb_usdt_krw_spot.json
```

Result: failed due to environment/network tunnel.

```text
Market data collection failed: Network error for https://api.bithumb.com/public/ticker/USDT_KRW: Tunnel connection failed: 403 Forbidden
EXIT:1
```

## 7. Global reference smoke results

### Binance global USDT reference

```text
python tools/collect_market_data.py --adapter live_binance_usdt_reference --output data/generated_packets/debug_binance_usdt_reference.json
```

Result: failed at `http_get` due to environment/network tunnel, with corrected candidate diagnostics visible.

```text
Market data collection failed: Global USDT reference adapter live_binance_usdt_reference failed all candidates: live_binance_usdt_reference[binance] candidate=0 endpoint=/api/v3/ticker/bookTicker symbol=USDCUSDT stage=http_get status=None code=None message=Network error for https://api.binance.com/api/v3/ticker/bookTicker?symbol=USDCUSDT: Tunnel connection failed: 403 Forbidden
EXIT:1
```

### Bybit global USDT reference

```text
python tools/collect_market_data.py --adapter live_bybit_usdt_reference --output data/generated_packets/debug_bybit_usdt_reference.json
```

Result: failed at `http_get` due to environment/network tunnel, with corrected candidate diagnostics visible.

```text
Market data collection failed: Global USDT reference adapter live_bybit_usdt_reference failed all candidates: live_bybit_usdt_reference[bybit] candidate=0 endpoint=/v5/market/tickers symbol=USDCUSDT stage=http_get status=None code=None message=Network error for https://api.bybit.com/v5/market/tickers?category=spot&symbol=USDCUSDT: Tunnel connection failed: 403 Forbidden
EXIT:1
```

### OKX global USDT reference

```text
python tools/collect_market_data.py --adapter live_okx_usdt_reference --output data/generated_packets/debug_okx_usdt_reference.json
```

Result: failed at `http_get` due to environment/network tunnel, with corrected candidate diagnostics visible.

```text
Market data collection failed: Global USDT reference adapter live_okx_usdt_reference failed all candidates: live_okx_usdt_reference[okx] candidate=0 endpoint=/api/v5/market/ticker symbol=USDC-USDT stage=http_get status=None code=None message=Network error for https://www.okx.com/api/v5/market/ticker?instId=USDC-USDT: Tunnel connection failed: 403 Forbidden
EXIT:1
```

## 8. Composite live smoke result

```text
python tools/collect_market_data.py --adapter live_tether_cross_market_premium --output data/generated_packets/live_tether_cross_market_packet.json
```

Result: failed before global reference collection because the domestic Upbit public endpoint was blocked by the workspace network tunnel.

```text
Market data collection failed: Domestic child adapter live_upbit_usdt_krw_spot failed: Network error for https://api.upbit.com/v1/ticker?markets=KRW-USDT: Tunnel connection failed: 403 Forbidden
EXIT:1
```

No confirmed live composite packet was created in this environment.

## 9. Packet field summary, if succeeded

Not applicable. The composite live smoke did not create `data/generated_packets/live_tether_cross_market_packet.json`, so the packet-field summary command was intentionally not run.

## 10. Failure classification, if failed

Classification: environment/network/location failure.

Detailed classification:
- Domestic endpoint failure: yes. Upbit and Bithumb both failed with tunnel `403 Forbidden` before JSON payloads were fetched.
- Global endpoint failure: yes. Binance, Bybit, and OKX all failed at `parser_stage=http_get` with tunnel `403 Forbidden`.
- Parser/config failure: not observed. Global diagnostics show the corrected public candidates (`USDCUSDT` for Binance/Bybit, `USDC-USDT` for OKX) and failures happen before parser stages can inspect exchange JSON payloads.
- Composite failure cause: domestic fail-fast on Upbit network tunnel `403`, not global partial-success logic.

## 11. Risks

- Live packet creation remains unconfirmed from this environment because public exchange endpoint access is blocked by the network tunnel.
- A true normal-network smoke must still be run from an environment with direct/public access to Upbit, Bithumb, Binance, Bybit, and OKX.
- Because no live packet was created, this verification must not be used as a trigger to proceed to sampling, alerts, Council handoff, active strategy promotion, or execution.

## 12. Rollback plan

- Revert this evidence file if the confirmation record needs replacement.
- Re-run `python -m unittest discover -s tests` after rollback.
- Confirm generated files under `data/generated_packets/` are not committed.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.

## 13. Human review required

Human review should inspect:

1. `docs/pr_handoffs/tether_cross_market_local_live_smoke_confirmation_v0.md`
2. The command output showing `git pull --ff-only` had no upstream tracking branch.
3. The live smoke outputs showing `Tunnel connection failed: 403 Forbidden`.
4. Existing config/adapter code only if deciding where to run the next normal-network verification.

## 14. No-trade compliance

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

## 15. Next recommended step

Run the same live smoke sequence from an environment with normal public internet access to the required exchange endpoints. If the composite succeeds, record the packet field summary and keep generated JSON out of git. If it fails in that environment with exchange status/code/parser diagnostics instead of tunnel `403`, stop verification and open a separate small bugfix task scoped to the exact domestic/global/parser/config issue.
