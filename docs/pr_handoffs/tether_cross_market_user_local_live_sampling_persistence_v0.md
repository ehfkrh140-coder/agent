# Tether Cross-Market User-Local Live Sampling Persistence Evidence v0

## 1. Purpose

Record user-local normal-network evidence that `live_tether_cross_market_premium` live sampling persistence succeeded after `Tether Cross-Market Sampling Baseline v0` was merged.

This PR is evidence-only. Codex did not modify runtime code, configs, adapters, sampling logic, tests, generated packet JSON, generated sampling JSON, Council runtime, notification/alert runtime, or Gemini runtime/prompt files.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `tether_cross_market_premium / usdt_krw_global_reference_v0` remains experimental, non-active, and `NO_TRADE_ONLY`.
- Global reference blocker is resolved: Binance/Bybit use `USDCUSDT`, OKX uses `USDC-USDT`, and global references use `normalize: inverse`.
- Composite baseline includes `min_successful_global_references: 1`.
- User-local live packet smoke already succeeded.
- Evaluate-only readiness review already documented `NEED_DATA`, `REJECT`, and `WATCH` semantics.
- Sampling baseline already added replay sampling checks and tether-specific sampling summary fields.
- Codex workspace live sampling may still be blocked by network tunnel `403 Forbidden`; this file records user-local normal-network evidence and does not claim Codex produced the live success.

## 3. User-local live sampling command

User-local command provided by the user:

```text
python tools/sample_market_data.py --adapter live_tether_cross_market_premium --samples 3 --interval 1 --output data/market_samples/tether_cross_market_live_sampling_summary.json
```

The generated sampling JSON is a local artifact and is not committed.

## 4. User-local live sampling result

User-local normal-network result:

```text
schema_version: market_sampling_v1
adapter_id: live_tether_cross_market_premium
samples_requested: 3
samples_ok: 3
samples_error: 0
candidate_seen_count: 3
positive_net_gap_count: 0
readiness_pass_count: 0
persistence_status: NO_PERSISTENT_EDGE
recommended_default_decision: REJECT
council_recommended: false
council_reason: NO_PERSISTENT_EDGE: persistent ready edge handoff packet not available
successful_global_reference_count per sample: 3
failed_global_reference_venues per sample: []
sample statuses: ok, ok, ok
readiness_status per sample: REJECT, REJECT, REJECT
recommended_default_decision per sample: REJECT, REJECT, REJECT
net_gap_pass per sample: false
global_reference_pass per sample: true
global_reference_venue_count per sample: 3
global_usdt_depeg_flag per sample: false
estimated_net_gap_pct per sample: -0.21743088
gross_gap_pct per sample: -0.06743088
domestic_best_bid: 1482.0
domestic_best_ask: 1483.0
domestic_mid: 1482.5
global_usdt_mid: 0.9989511
global_usdt_depeg_pct: -0.10488962
max_latency_ms: 124.0
avg_latency_ms: 113.66666666666667
```

## 5. Sampling interpretation

- Live sampling succeeded in the user-local normal-network environment.
- All three samples collected live public data successfully.
- Upbit/Bithumb domestic `USDT/KRW` public data was available.
- Binance/Bybit/OKX global USDT reference data was available.
- The sampling result correctly classified the run as `NO_PERSISTENT_EDGE` because no positive net gap persisted.
- `recommended_default_decision: REJECT` is consistent with the absence of a positive net gap and readiness pass.
- `council_recommended: false` is expected because no persistent ready edge handoff packet is available.
- No execution signal was generated.

## 6. False-value interpretation

- `readiness_pass=false` means no readiness pass / no trade candidate, not data collection failure.
- `net_gap_pass=false` means no profitable net spread after fee/buffer assumptions, not API failure.
- `council_recommended=false` means no persistent ready edge handoff, not Council malfunction.
- `global_usdt_depeg_flag=false` is a healthy state: no depeg condition observed.

## 7. Generated artifact handling

- The user-local output path was `data/market_samples/tether_cross_market_live_sampling_summary.json`.
- The generated sampling JSON is evidence for local review only and is not committed.
- No generated packet JSON is committed.
- No generated Council session JSON is committed.
- This PR adds only the handoff evidence file.

## 8. Changed files

- Added: `docs/pr_handoffs/tether_cross_market_user_local_live_sampling_persistence_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `tests/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.
- No Council runtime, notification/alert runtime, Gemini runtime, or prompt changes.

## 9. Tests run by Codex

### Git status

```text
git status
```

Result before adding this handoff: working tree clean.

### Git diff name check

```text
git diff --name-only
```

Result before adding this handoff: no output.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: pass.

```text
Ran 249 tests in 11.805s
OK
```

### Sampling unit tests

```text
python -m unittest discover -s tests -p "*sampling*.py"
```

Result: pass.

```text
Ran 19 tests in 0.934s
OK
```

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed. Matches are existing documentation/tests/no-trade guardrail references. This PR added no runtime credentials, private endpoints, account/balance lookup, order/cancel, withdrawal/deposit/transfer, fiat/bank transfer, auto-trading, or execution surface.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed. Evidence remains consistent with active strategy `cross_exchange_spot_spread_v1`; `tether_cross_market_premium` remains experimental, non-active, and `NO_TRADE_ONLY`.

## 10. Risks

- This is user-local evidence, not Codex workspace live success. Codex workspace network access may still be blocked by tunnel `403 Forbidden`.
- The result proves live sampling can collect public data in a normal-network environment, but it does not prove a profitable opportunity.
- `NO_PERSISTENT_EDGE`, `REJECT`, `readiness_pass=false`, and `net_gap_pass=false` should not be treated as failures; they are expected no-trade/no-handoff outcomes for this sample.
- Future alert/notification, Council handoff, active promotion, or execution work must be separate and explicitly reviewed.

## 11. Rollback plan

- Revert `docs/pr_handoffs/tether_cross_market_user_local_live_sampling_persistence_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated sampling JSON or packet JSON is committed.

## 12. Human review required

Reviewers should inspect:

1. `docs/pr_handoffs/tether_cross_market_user_local_live_sampling_persistence_v0.md`
2. Prior sampling baseline evidence in `docs/pr_handoffs/tether_cross_market_sampling_baseline_v0.md`
3. Prior user-local live packet smoke evidence in `docs/pr_handoffs/tether_cross_market_user_local_live_smoke_success_v0.md`

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
- alert expansion: no
- notification expansion: no
- FX / USD-KRW / fair_usdt_krw_price calculation: no
- generated packet JSON commit: no
- generated sampling JSON commit: no

## 14. Next recommended step

Do not move directly to alert/notification, Council handoff automation, active promotion, or execution. If the user wants to proceed, open a separate reviewed task for continued evaluate-only sampling/persistence review or a clearly scoped readiness evidence update while preserving `NO_TRADE_ONLY`.
