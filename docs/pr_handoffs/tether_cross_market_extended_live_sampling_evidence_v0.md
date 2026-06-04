# Tether Cross-Market Extended Live Sampling Evidence v0

## 1. Purpose

Record user-local normal-network evidence that `live_tether_cross_market_premium` completed an extended 30-sample live sampling run successfully after the prior 3-sample user-local live sampling persistence evidence.

This PR is evidence-only. It does not modify runtime code, configs, adapters, sampling logic, tests, generated packet JSON, generated sampling JSON, Council runtime, notification/alert runtime, or Gemini runtime/prompt files.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `tether_cross_market_premium / usdt_krw_global_reference_v0` remains experimental, non-active, and `NO_TRADE_ONLY`.
- Global reference blocker is resolved: Binance/Bybit use `USDCUSDT`, OKX uses `USDC-USDT`, and references use `normalize: inverse`.
- Composite baseline includes `min_successful_global_references: 1`.
- User-local live packet smoke succeeded.
- User-local 3-sample live sampling persistence evidence succeeded.
- Sampling baseline exposes tether-specific metrics in summaries.
- Codex workspace live sampling may still be blocked by network tunnel `403 Forbidden`; this document records user-local normal-network evidence and does not claim Codex produced the live sampling success.

## 3. User-local extended live sampling command

User-local command provided by the user:

```text
python tools/sample_market_data.py --adapter live_tether_cross_market_premium --samples 30 --interval 2 --output data/market_samples/tether_cross_market_live_sampling_30x_summary.json
```

The generated sampling JSON is a local artifact and is not committed.

## 4. User-local 30-sample result

User-local normal-network result:

```text
adapter_id: live_tether_cross_market_premium
strategy_family: tether_cross_market_premium
samples_requested: 30
samples_ok: 30
samples_error: 0
candidate_seen_count: 30
positive_net_gap_count: 0
readiness_pass_count: 0
direction_counts:
  bithumb_to_upbit: 14
  upbit_to_bithumb: 16
max_estimated_net_gap_pct: -0.15
avg_estimated_net_gap_pct: -0.18598740266666666
max_gross_gap_pct: 0.0
avg_latency_ms: 100.06666666666666
max_latency_ms: 144.0
persistence_status: NO_PERSISTENT_EDGE
recommended_default_decision: REJECT
min_consecutive_ready: 2
council_recommended: false
all sample statuses: ok
all sample decisions: REJECT
all net_gap_pass values: false
successful_global_reference_count: 3 for all 30 samples
```

## 5. Sampling interpretation

- Live sampling succeeded from the user-local normal-network environment.
- All 30 samples collected live public data successfully.
- No sample had an API/data collection failure.
- All 30 samples had all three global references available.
- No positive net gap persisted.
- The correct classification is `NO_PERSISTENT_EDGE / REJECT`.
- `council_recommended=false` is expected because there was no persistent ready edge.
- `net_gap_pass=false` is expected because no profitable spread remained after fee/buffer assumptions.
- This is not an API failure and not a strategy failure.
- No execution signal was generated.

## 6. False-value interpretation

- `samples_error=0` means data collection succeeded.
- `net_gap_pass=false` means no profitable spread after fees/buffer, not API failure.
- `readiness_pass_count=0` means no ready trade candidate, not a broken system.
- `council_recommended=false` means no persistent ready edge handoff, not Council malfunction.
- `successful_global_reference_count=3` means all global references succeeded for each sample.

## 7. What this proves

- User-local live sampling can run 30 consecutive samples successfully.
- Domestic Upbit/Bithumb public data collection is stable for this run.
- Binance/Bybit/OKX global reference collection is stable for this run.
- The sampling pipeline can summarize no-edge conditions correctly.

## 8. What this does not prove

- It does not prove profitability.
- It does not justify alert/notification implementation yet.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API work.

## 9. Generated artifact handling

- The user-local output path was `data/market_samples/tether_cross_market_live_sampling_30x_summary.json`.
- The generated sampling JSON is evidence for local review only and is not committed.
- No generated packet JSON is committed.
- No generated Council session JSON is committed.
- This PR adds only the handoff evidence file.

## 10. Changed files

- Added: `docs/pr_handoffs/tether_cross_market_extended_live_sampling_evidence_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `tests/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.
- No Council runtime, notification/alert runtime, Gemini runtime, or prompt changes.

## 11. Tests run by Codex

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
Ran 249 tests in 11.923s
OK
```

### Sampling unit tests

```text
python -m unittest discover -s tests -p "*sampling*.py"
```

Result: pass.

```text
Ran 19 tests in 0.916s
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

## 12. Risks

- This is user-local evidence, not Codex workspace live success. Codex workspace network access may still be blocked by tunnel `403 Forbidden`.
- The result proves live sampling can collect 30 consecutive public-data samples in a normal-network environment, but it does not prove profitability or execution readiness.
- `NO_PERSISTENT_EDGE`, `REJECT`, `readiness_pass_count=0`, and `net_gap_pass=false` are expected no-trade/no-handoff outcomes for this sample window.
- Future alert/notification, Council handoff, active promotion, or execution work must be separate and explicitly reviewed.

## 13. Rollback plan

- Revert `docs/pr_handoffs/tether_cross_market_extended_live_sampling_evidence_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated sampling JSON or packet JSON is committed.

## 14. Human review required

Reviewers should inspect:

1. `docs/pr_handoffs/tether_cross_market_extended_live_sampling_evidence_v0.md`
2. Prior 3-sample user-local live sampling evidence in `docs/pr_handoffs/tether_cross_market_user_local_live_sampling_persistence_v0.md`
3. Sampling baseline evidence in `docs/pr_handoffs/tether_cross_market_sampling_baseline_v0.md`

## 15. No-trade compliance

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

## 16. Next recommended step

Do not move directly to alert/notification, Council handoff automation, active promotion, or execution. If the user wants to proceed, open a separate reviewed task for continued evaluate-only sampling/persistence review, threshold calibration, or a clearly scoped readiness evidence update while preserving `NO_TRADE_ONLY`.
