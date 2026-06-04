# Tether Cross-Market User Local Live Smoke Success Evidence v0

## 1. Purpose

Record user-local live smoke success evidence for `live_tether_cross_market_premium` after the previous Codex workspace smoke attempts failed with network tunnel `403 Forbidden`.

This handoff explicitly distinguishes user-local success from Codex workspace network failures. Codex did not directly produce the successful live packet in its workspace; this file records the user's normal-network evidence. This PR is evidence-only and does not modify runtime code, config, tests, generated packets, sampling, alerts, Council handoff, active strategy status, or execution behavior.

## 2. Baseline before user-local smoke

- Global reference diagnostics, `ticker_candidates`, inverse normalization, and `min_successful_global_references: 1` are already present from earlier diagnostics work.
- Previous Codex workspace smoke attempts failed because Upbit/Bithumb/Binance/Bybit/OKX public endpoints were blocked by a network tunnel returning `403 Forbidden`.
- Previous Codex tests passed: full unit tests and tether-specific tests.
- `tether_cross_market_premium` remains experimental, non-active, and `NO_TRADE_ONLY`.
- Active strategy remains `cross_exchange_spot_spread_v1`.

## 3. User-local environment summary

User-local environment evidence:

- Browser/direct public API access worked for all required public endpoints.
- `gci env:*proxy*` returned no proxy variables.
- Python proxy environment inspection returned `{}`.
- This indicates the user-local environment had direct public endpoint access and was not affected by the Codex workspace tunnel `403 Forbidden` blocker.

## 4. Direct public endpoint probe result

User-local browser/direct public API evidence:

- Upbit `KRW-USDT` returned JSON.
- Bithumb `USDT_KRW` returned JSON.
- Binance `USDCUSDT` returned JSON.
- Bybit `USDCUSDT` returned JSON.
- OKX `USDC-USDT` returned JSON.

Interpretation: the required public read-only endpoints were reachable from the user-local environment.

## 5. Adapter registry result

User-local adapter registry evidence showed these adapters present:

- `live_upbit_usdt_krw_spot`
- `live_bithumb_usdt_krw_spot`
- `live_binance_usdt_reference`
- `live_bybit_usdt_reference`
- `live_okx_usdt_reference`
- `live_tether_cross_market_premium`
- `replay_tether_cross_market_premium`

## 6. Domestic adapter smoke result

User-local domestic adapter smoke succeeded:

- Upbit `USDT/KRW`:
  - `bid`: `1469`
  - `ask`: `1470`
  - `last_price`: `1470`
  - `api_ok`: `true`
- Bithumb `USDT/KRW`:
  - `bid`: `1469`
  - `ask`: `1470`
  - `last_price`: `1470`
  - `api_ok`: `true`

Interpretation: both required domestic child adapters were available and normalized live public data successfully in the user-local environment.

## 7. Global reference adapter smoke result

User-local global reference smoke succeeded:

- Binance:
  - symbol: `USDCUSDT`
  - response_format: `binance_book_ticker`
  - normalize: `inverse`
  - http_status: `200`
- Bybit:
  - symbol: `USDCUSDT`
  - response_format: `bybit_v5_ticker`
  - normalize: `inverse`
  - http_status: `200`
- OKX:
  - instId: `USDC-USDT`
  - response_format: `okx_ticker`
  - normalize: `inverse`
  - http_status: `200`

Interpretation: the candidate symbol direction and inverse normalization baseline works against live public endpoints in the user-local environment.

## 8. Composite live smoke result

User-local composite smoke succeeded:

- `live_tether_cross_market_packet.json` was generated locally by the user.
- `strategy_family`: `tether_cross_market_premium`
- `strategy_id`: `usdt_krw_global_reference_v0`
- `asset`: `USDT`
- `quote`: `KRW`
- `experimental_strategy`: `true`
- `non_active_strategy`: `true`
- `no_trade_only`: `true`
- `successful_global_reference_count`: `3`
- `failed_global_reference_venues`: `[]`
- `global_reference_pass`: `true`
- `global_usdt_depeg_flag`: `false`
- `net_gap_pass`: `false`
- No execution signal was generated.

Generated packet JSON is user-local smoke output only and is not committed in this PR.

## 9. Packet interpretation

The user-local packet confirms that:

- Domestic Upbit and Bithumb `USDT/KRW` observations can be collected from a normal network.
- All three global reference venues can be collected from a normal network.
- The global reference candidate direction (`USDCUSDT` / `USDC-USDT`) and inverse normalization are compatible with live public endpoints.
- The composite can build a `tether_cross_market_premium` packet with `successful_global_reference_count = 3`.
- The packet remained experimental/non-active/NO_TRADE_ONLY.
- `global_usdt_depeg_flag = false` and `net_gap_pass = false` mean this smoke evidence is not an execution signal or trade instruction.

## 10. Failure root cause conclusion

Conclusion: previous Codex workspace live smoke failures were environment/network/location failures caused by network tunnel `403 Forbidden`, not code/config/parser failures.

Evidence:

- Codex workspace smoke failed at public HTTP access for domestic and global endpoints.
- User-local direct public endpoint probes returned JSON.
- User-local domestic adapters succeeded.
- User-local global reference adapters succeeded with http_status `200`.
- User-local composite generated a live packet with all three global references successful.

## 11. Changed files

- Added: `docs/pr_handoffs/tether_cross_market_user_local_live_smoke_success_v0.md`.
- No runtime code changed.
- No config changed.
- No tests changed.
- No generated packet JSON committed.

## 12. Tests run by Codex

Codex ran these checks in the workspace for this evidence-only PR:

```text
git status
```

Result: clean before changes.

```text
git diff --name-only
```

Result: no output before adding this evidence file.

```text
python -m unittest discover -s tests
```

Result: pass.

```text
Ran 248 tests in 12.114s
OK
```

```text
python -m unittest discover -s tests -p "test_tether_cross_market_live_composite_adapter.py"
```

Result: pass.

```text
Ran 15 tests in 0.125s
OK
```

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed. Matches are existing documentation/tests/no-trade guardrail references; this PR did not add runtime credentials, private endpoints, account/balance lookup, order/cancel, withdrawal/deposit/transfer, or auto-trading code.

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed. Evidence remains consistent with active strategy `cross_exchange_spot_spread_v1`; `tether_cross_market_premium` remains experimental/non-active/NO_TRADE_ONLY.

## 13. Risks

- This file records user-local evidence; Codex did not reproduce the live success in its network-restricted workspace.
- Generated packet JSON is intentionally not included, so reviewers rely on the summarized user-local evidence rather than a committed packet artifact.
- This success should not be interpreted as approval to proceed automatically to sampling, alerts, Council handoff, active promotion, or execution.
- Future readiness/sampling work still requires a separate task card/PR and human review.

## 14. Rollback plan

- Revert this evidence file if the user-local success record needs replacement.
- Re-run `python -m unittest discover -s tests` after rollback.
- Confirm no generated packet JSON files are committed.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.

## 15. Human review required

Human review should inspect:

1. `docs/pr_handoffs/tether_cross_market_user_local_live_smoke_success_v0.md`
2. The user-local smoke evidence summarized in this file.
3. Prior Codex workspace failure handoffs if comparing environment/network root cause.

## 16. No-trade compliance

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

## 17. Next recommended step

Open a separate PR/task for `Tether Cross-Market Readiness/Sampling Baseline v0` if the user wants to proceed. That future task must remain NO_TRADE_ONLY, avoid execution/private API surfaces, keep generated packet JSON out of git unless explicitly scoped, and require its own tests, evidence, and human review.
