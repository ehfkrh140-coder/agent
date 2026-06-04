# Tether Cross-Market PR Hygiene and Scope Reconciliation v0

## 1. Purpose

Reconcile the current repository source of truth, PR metadata, and tether cross-market handoff evidence after the recent `tether_cross_market_premium` work. This PR is documentation/evidence only and does not change runtime code, configs, tests, generated data, sampling, alerts, Council runtime, or execution behavior.

## 2. Why this reconciliation was needed

A recent Codex final report described the evaluate-only readiness review step as adding only `docs/pr_handoffs/tether_cross_market_evaluate_only_readiness_review_v0.md` with no runtime/config/test changes. GitHub PR metadata, however, showed a larger changed-file/addition/deletion footprint that also included the earlier global reference diagnostics code/config/test changes.

This reconciliation treats the current `main`/HEAD content as the source of truth and separates two concepts:

- The cumulative GitHub PR/commit metadata can include the full global-reference implementation plus multiple evidence files.
- The evaluate-only readiness review evidence file is accurate for that specific review step: it did not itself introduce runtime adapter/config/packet-builder/test changes.

## 3. Current main source-of-truth summary

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `tether_cross_market_premium / usdt_krw_global_reference_v0` remains experimental, non-active, and `NO_TRADE_ONLY`.
- Global reference configuration is corrected to use Binance/Bybit `USDCUSDT`, OKX `USDC-USDT`, and `normalize: inverse`.
- The experimental composite uses `min_successful_global_references: 1`.
- User-local normal-network live smoke success evidence exists and records `successful_global_reference_count: 3`, `failed_global_reference_venues: []`, `global_reference_pass: true`, `global_usdt_depeg_flag: false`, `net_gap_pass: false`, and no execution signal.
- Evaluate-only readiness review evidence exists and documents `NEED_DATA`, `REJECT`, and `WATCH` interpretation.
- Generated packet JSON files are test/smoke artifacts and are not committed.

## 4. PR / handoff timeline

1. `tether_cross_market_global_reference_diagnostics_v0.md`
   - Documents the blocker fix for global USDT references: candidate public endpoints, inverse normalization, diagnostics, and partial global-reference success support.
2. `tether_cross_market_live_smoke_verification_v0.md`
   - Documents Codex workspace verification where unit tests passed but live endpoint access was blocked by network tunnel `403 Forbidden`.
3. `tether_cross_market_local_live_smoke_confirmation_v0.md`
   - Confirms the Codex/local environment classification remained network/location blocked rather than a parser/config failure.
4. `tether_cross_market_user_local_live_smoke_success_v0.md`
   - Records user-local normal-network live smoke success for direct public APIs, domestic adapters, global references, and the composite packet.
5. `tether_cross_market_evaluate_only_readiness_review_v0.md`
   - Reviews the successful live packet and scenario/replay evidence as evaluate-only readiness evidence. It is not a sampling, alert, Council handoff, active-promotion, or execution step.
6. `tether_cross_market_pr_hygiene_scope_reconciliation_v0.md`
   - This file reconciles the apparent PR metadata/final-report scope mismatch before any future sampling baseline work.

## 5. Scope mismatch findings

### Codex final report vs GitHub PR metadata

They are partially different views of the same accumulated work:

- The Codex final report for the evaluate-only readiness review correctly stated that the evaluate-only step added only the readiness review handoff and did not modify runtime code/config/tests.
- GitHub PR metadata for the broader accumulated branch/commit can correctly show larger changes because it includes earlier global reference diagnostics implementation, config updates, tests, and multiple handoff files.

### Exact mismatch

The mismatch is not that the repository currently contains undocumented code behavior. The mismatch is that the final report described the scope of the last evidence/review step, while the GitHub PR metadata represented a broader cumulative diff that also contained earlier implementation work.

### Documentation correction decision

No existing handoff file was changed in this reconciliation. The evaluate-only handoff is kept as-is because its statement is scoped to that evaluate-only review step. This new reconciliation file is the corrective evidence layer that explains how to read the cumulative PR metadata and the step-specific handoffs together.

## 6. Files changed in this reconciliation PR

- Added: `docs/pr_handoffs/tether_cross_market_pr_hygiene_scope_reconciliation_v0.md`.
- No changes to `src/**`.
- No changes to `configs/**`.
- No changes to `tests/**`.
- No changes to `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**`.
- No Gemini runtime/prompt, Council runtime, notification, sampling, or storage runtime changes.

## 7. Tests run

### Git status

```text
git status
```

Result: pass. Initial working tree was clean before this handoff was added.

### Git log

```text
git log --oneline -10
```

Result: completed. Recent history showed the current HEAD as the cumulative global reference diagnostics / partial-success handling commit, followed by earlier tether live composite and replay packet work.

### Git diff against origin/main

```text
git diff --name-only origin/main...HEAD
```

Result: not available in this workspace because `origin/main` is not present. Per repository instructions, this is not treated as a task failure.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: pass.

```text
Ran 248 tests in 12.249s
OK
```

### Tether-specific unit test

```text
python -m unittest discover -s tests -p "test_tether_cross_market_live_composite_adapter.py"
```

Result: pass.

```text
Ran 15 tests in 0.097s
OK
```

### Scenario evaluate-only smoke

```text
python tools/run_strategy_scenarios.py --strategy tether_cross_market_premium --evaluate-only
```

Result: pass. Scenario outputs matched expected `NEED_DATA`, `REJECT`, and `WATCH` evaluate-only classifications.

### Replay packet smoke

```text
python tools/collect_market_data.py --adapter replay_tether_cross_market_premium --output data/generated_packets/replay_tether_cross_market_packet.json
```

Result: pass.

```text
OpportunityPacket saved to: data/generated_packets/replay_tether_cross_market_packet.json
EXIT:0
```

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed. Matches are existing documentation, tests, and no-trade guardrail references. This reconciliation PR added no runtime credential, private endpoint, account/balance lookup, order/cancel, withdrawal/deposit/transfer, fiat/bank transfer, or auto-trading surface.

## 8. Generated artifact cleanup

Replay smoke generated `data/generated_packets/replay_tether_cross_market_packet.json`; it was deleted immediately after the smoke check.

```text
git status --short
```

Result after cleanup before adding this handoff: no generated packet JSON files were staged, tracked, or untracked.

## 9. No-trade compliance

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

## 10. Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed. Evidence remains consistent with active strategy `cross_exchange_spot_spread_v1`; `tether_cross_market_premium` remains experimental, non-active, and `NO_TRADE_ONLY`.

## 11. Risks

- This reconciliation is documentation-only; it does not independently validate live-market persistence, freshness, or profitability.
- The larger GitHub PR metadata can still look surprising unless reviewers read the timeline and distinguish cumulative branch scope from step-specific final reports.
- Future sampling/readiness work must not proceed until this scope reconciliation is reviewed.

## 12. Rollback plan

- Revert `docs/pr_handoffs/tether_cross_market_pr_hygiene_scope_reconciliation_v0.md`.
- Re-run `python -m unittest discover -s tests`.
- Confirm no generated packet JSON files are committed.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.

## 13. Human review required

Reviewers should inspect:

1. `docs/pr_handoffs/tether_cross_market_pr_hygiene_scope_reconciliation_v0.md`
2. `docs/pr_handoffs/tether_cross_market_evaluate_only_readiness_review_v0.md`
3. Prior tether handoff files if they need to audit the full timeline.

## 14. Next recommended step

Proceed to `Tether Cross-Market Sampling Baseline v0` only after this reconciliation is reviewed. That future task must remain scoped separately, preserve `NO_TRADE_ONLY`, avoid Council auto-calls and execution/private API surfaces, and document generated artifact handling, tests, risks, rollback, and human review evidence.
