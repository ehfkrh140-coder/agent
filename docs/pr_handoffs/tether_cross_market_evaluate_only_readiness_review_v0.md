# Tether Cross-Market Evaluate-Only Readiness Review v0

## 1. Purpose

Review the current `tether_cross_market_premium / usdt_krw_global_reference_v0` state after user-local live packet generation succeeded, and document evaluate-only readiness interpretation for manual scenarios, replay packet generation, and user-local live smoke evidence.

This PR is evidence/review only. It does not implement sampling, alerts, Council handoff, active strategy promotion, execution, runtime adapter changes, config changes, or packet-builder changes.

## 2. Baseline

- `tether_cross_market_premium / usdt_krw_global_reference_v0` remains experimental, non-active, and `NO_TRADE_ONLY`.
- Active strategy remains `cross_exchange_spot_spread_v1`.
- The previous global reference blocker is resolved: Binance/Bybit use `USDCUSDT`, OKX uses `USDC-USDT`, and global references use `normalize: inverse`.
- The experimental composite baseline includes `min_successful_global_references: 1`.
- User-local normal-network live composite smoke succeeded with `successful_global_reference_count: 3`, `failed_global_reference_venues: []`, `global_reference_pass: true`, `global_usdt_depeg_flag: false`, `net_gap_pass: false`, and no execution signal.

## 3. Reviewed evidence

Reviewed sources:

- Strategy handoff: `docs/AI_Council_Project_Handoff_v3_Strategy_Update_2026-06-02.md`.
- Strategy card: `docs/strategy_task_cards/tether_cross_market_premium.md`.
- Global reference diagnostics evidence: `docs/pr_handoffs/tether_cross_market_global_reference_diagnostics_v0.md`.
- Codex workspace live smoke evidence: `docs/pr_handoffs/tether_cross_market_live_smoke_verification_v0.md`.
- Codex local live smoke confirmation: `docs/pr_handoffs/tether_cross_market_local_live_smoke_confirmation_v0.md`.
- User-local live smoke success evidence: `docs/pr_handoffs/tether_cross_market_user_local_live_smoke_success_v0.md`.
- No-trade / merge / rollback / workflow guardrail docs.

## 4. Scenario readiness review

Command run:

```text
python tools/run_strategy_scenarios.py --strategy tether_cross_market_premium --evaluate-only
```

Result: pass. All listed scenario expectations matched.

Observed scenario readiness classifications:

- `tether_cross_market_missing_bithumb_need_data`: `NEED_DATA`, readiness pass `False`.
- `tether_cross_market_missing_global_reference_need_data`: `NEED_DATA`, readiness pass `False`.
- `tether_cross_market_last_price_only_need_data`: `NEED_DATA`, readiness pass `False`.
- `tether_cross_market_balanced_no_spread_reject`: `REJECT`, readiness pass `False`.
- `tether_cross_market_depeg_risk_reject`: `REJECT`, readiness pass `False`.
- `tether_cross_market_high_fee_reject`: `REJECT`, readiness pass `False`.
- `tether_cross_market_domestic_spread_positive_watch`: `WATCH`, readiness pass `False`.

Evaluate-only interpretation:

- `NEED_DATA` covers missing domestic venue observations, missing global reference observations/metrics, and last-price-only candidates without executable bid/ask/depth.
- `REJECT` covers balanced/no-spread packets, non-positive estimated net gap after fee/buffer/slippage assumptions, and global USDT depeg risk.
- `WATCH` is allowed only as an experimental observation classification when domestic bid/ask/depth and global reference health are sufficient and the experimental signal conditions are positive.
- `WATCH` is not `ENTER`, not a Council handoff, and not an execution instruction.

## 5. Replay packet review

Command run:

```text
python tools/collect_market_data.py --adapter replay_tether_cross_market_premium --output data/generated_packets/replay_tether_cross_market_packet.json
```

Result: pass.

```text
OpportunityPacket saved to: data/generated_packets/replay_tether_cross_market_packet.json
EXIT:0
```

Replay packet interpretation:

- Replay packet generation remains preserved.
- Replay output is a test artifact and was removed after the smoke check.
- The generated replay JSON was not committed.

## 6. User-local live smoke interpretation

User-local live smoke evidence indicates:

- Data collection succeeded for both domestic venues and all three global references.
- Global reference health was normal with `global_reference_pass: true`.
- `global_usdt_depeg_flag: false` indicates no global USDT depeg condition was observed in that packet.
- `net_gap_pass: false` indicates no domestic spread/net-gap candidate passed the evaluate-only threshold.
- `net_gap_pass: false` is not a collection failure. It is normal readiness evidence that the smoke packet is not a trade candidate.
- No execution signal was generated.

## 7. Readiness classification summary

### NEED_DATA 기준

Use `NEED_DATA` when any required evaluate-only data is missing or not comparable, including:

- Upbit or Bithumb domestic `USDT/KRW` observation missing.
- Domestic bid/ask/size/depth unavailable.
- Global reference basket unavailable or below required minimum.
- Global reference metrics such as `global_reference_pass` or `global_usdt_mid` missing.
- Candidate is based only on last price and lacks executable bid/ask/depth.

### REJECT 기준

Use `REJECT` when data is sufficient to rule out an observation candidate, including:

- `estimated_net_gap_pct` is non-positive after fee, slippage, and safety-buffer assumptions.
- The packet is balanced/no-spread and does not present a positive domestic cross-market spread.
- Global USDT depeg risk is active.
- The user-local live smoke case with `net_gap_pass: false` should be treated as no trade candidate, not as a failed data collection.

### WATCH 기준

Use `WATCH` only as an experimental/evaluate-only observation state when:

- Domestic Upbit/Bithumb bid/ask/depth are present.
- Global reference health is sufficient.
- No depeg flag is active.
- Estimated domestic net gap conditions are positive enough for observation.
- Even then, readiness pass remains false and the strategy remains non-active.

### ENTER / execution 해석

`ENTER` is not implemented as an execution instruction in this strategy. `WATCH` is an analysis-stage observation only. Council outputs, if later reviewed manually, remain analysis only and must not be converted into trades in this PR.

## 8. Behavior before / after

Before this PR:

- User-local live smoke success was recorded, but there was no dedicated readiness review tying manual scenarios, replay packet preservation, and the user-local packet interpretation together.

After this PR:

- Evaluate-only readiness interpretation is documented in one handoff file.
- No code behavior changed.
- No config behavior changed.
- No test behavior changed.
- No generated packet artifact is committed.

## 9. Changed files

- Added: `docs/pr_handoffs/tether_cross_market_evaluate_only_readiness_review_v0.md`.
- No runtime adapter/config/packet-builder files changed.
- No Council runtime files changed.
- No notification/sampling/storage files changed.
- No tests changed.
- No generated packet JSON committed.

## 10. Tests run

### Status checks

```text
git status
git diff --name-only
git diff --stat
```

Result before adding this handoff: working tree clean; `git diff --name-only` and `git diff --stat` printed no output.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: pass.

```text
Ran 248 tests in 12.108s
OK
```

### Tether-specific test

```text
python -m unittest discover -s tests -p "test_tether_cross_market_live_composite_adapter.py"
```

Result: pass.

```text
Ran 15 tests in 0.133s
OK
```

### Manual scenario evaluate-only smoke

```text
python tools/run_strategy_scenarios.py --strategy tether_cross_market_premium --evaluate-only
```

Result: pass. Scenario outputs matched expected `NEED_DATA`, `REJECT`, and `WATCH` evaluate-only classifications.

### Replay packet smoke

```text
python tools/collect_market_data.py --adapter replay_tether_cross_market_premium --output data/generated_packets/replay_tether_cross_market_packet.json
```

Result: pass. Generated replay JSON was removed after the check and not committed.

### Optional dry-run context check

```text
python main.py --council --opportunity-file data/generated_packets/replay_tether_cross_market_packet.json --dry-run-context
```

Result: pass.

```text
Dry-run context saved to: data/council_sessions/dry_run_context_20260602_153444.json
EXIT:0
```

This was a dry-run context generation only. The generated context file was removed after the check and not committed. No Council/Gemini live call was added by this PR.

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed. Matches are existing documentation/tests/no-trade guardrail references. This PR did not add runtime credentials, private endpoints, account/balance lookup, order/cancel, withdrawal/deposit/transfer, or auto-trading code.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed. Evidence remains consistent with active strategy `cross_exchange_spot_spread_v1`; `tether_cross_market_premium` remains experimental/non-active/NO_TRADE_ONLY.

### Generated packet not committed check

```text
git status --short
```

Result after cleanup: no generated packet JSON files remained staged, tracked, or untracked.

## 11. Risks

- This is an evaluate-only review, not a live production readiness approval.
- User-local live smoke success confirms packet generation, but it does not imply a profitable or executable trade candidate.
- `net_gap_pass: false` should be interpreted as no trade candidate in the successful packet.
- A future sampling baseline may reveal persistence/freshness issues that are not assessed here.
- Sampling/alerts/Council handoff/active promotion/execution require separate scoped PRs and human review.

## 12. Rollback plan

- Revert this handoff file if the readiness review record needs replacement.
- Re-run `python -m unittest discover -s tests` after rollback.
- Confirm no generated packet JSON files are committed.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.

## 13. Human review required

Human review should inspect:

1. `docs/pr_handoffs/tether_cross_market_evaluate_only_readiness_review_v0.md`
2. Prior user-local success evidence in `docs/pr_handoffs/tether_cross_market_user_local_live_smoke_success_v0.md`
3. Strategy card only if reviewers want to decide whether to add a future next-gate wording update.

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
- generated packet JSON commit: no

## 15. Next recommended step

Open a separate PR/task for `Tether Cross-Market Sampling Baseline v0` if the user wants to proceed. That future PR should remain NO_TRADE_ONLY, avoid Council auto-calls and execution/private API surfaces, keep generated packet JSON out of git unless explicitly scoped, and document sampling thresholds, persistence expectations, tests, risks, rollback, and human review requirements.
