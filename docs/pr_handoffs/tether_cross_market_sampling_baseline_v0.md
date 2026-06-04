# Tether Cross-Market Sampling Baseline v0

## 1. Purpose

Add and verify a conservative sampling baseline for `tether_cross_market_premium / usdt_krw_global_reference_v0` after global reference diagnostics, user-local live smoke success, evaluate-only readiness review, and PR hygiene reconciliation were completed.

This PR keeps the strategy experimental, non-active, and `NO_TRADE_ONLY`. It does not add alerts, notifications, Council handoff auto-calls, active strategy promotion, execution, private APIs, credentials, account/balance lookup, orders, transfers, FX conversion, or generated JSON artifacts.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `tether_cross_market_premium / usdt_krw_global_reference_v0` remains experimental, non-active, and `NO_TRADE_ONLY`.
- Global reference blocker is resolved: Binance/Bybit use `USDCUSDT`, OKX uses `USDC-USDT`, and candidates use `normalize: inverse`.
- Composite baseline has `min_successful_global_references: 1`.
- User-local normal-network live smoke succeeded with `successful_global_reference_count: 3`, `failed_global_reference_venues: []`, `global_reference_pass: true`, `global_usdt_depeg_flag: false`, `net_gap_pass: false`, and no execution signal.
- Evaluate-only readiness review already documents `NEED_DATA`, `REJECT`, and `WATCH` interpretation.
- Scope reconciliation confirmed that future sampling work should proceed only as a separate reviewed PR.

## 3. Scope

In scope:

- Use deterministic replay sampling as the official baseline smoke.
- Keep live sampling as a user-local/normal-network command, with Codex workspace `403 Forbidden` network tunnel failures classified as environment issues.
- Expose tether-specific candidate metrics in sampling `best_candidate` summaries so reviewers can inspect core tether signals without digging into the full packet.
- Add a focused replay sampling unit test.
- Add this handoff evidence file.

Out of scope:

- Alert/notification rules or transports.
- Council handoff auto-call or default `--handoff-output` behavior.
- Journal writes as default behavior.
- Active strategy promotion.
- Execution/risk engine, private APIs, credentials, account/balance lookup, orders/cancels, withdrawals/deposits/transfers, fiat/bank transfer, FX conversion, or fair USDT/KRW calculation.

## 4. Changed files

- `src/market_data/sampling.py`
  - Adds tether candidate metrics to the sampling `best_candidate` summary:
    - `global_reference_pass`
    - `global_reference_venue_count`
    - `global_usdt_depeg_flag`
    - `global_usdt_depeg_pct`
    - `global_usdt_mid`
    - `domestic_best_bid`
    - `domestic_best_ask`
    - `domestic_mid`
  - Adds sample-level `successful_global_reference_count` and `failed_global_reference_venues` from packet extensions when present. Replay packets do not currently expose these extension values, so replay samples record them as `null`; live composite packets can expose them when present.
- `tests/test_tether_cross_market_sampling.py`
  - Adds deterministic replay sampling coverage for tether-specific summary fields.
- `docs/pr_handoffs/tether_cross_market_sampling_baseline_v0.md`
  - Adds this evidence record.

No adapter, HTTP client, registry, config, Council runtime, notification, storage, Gemini runtime/prompt, generated packet, or generated sampling artifact files were changed.

## 5. Sampling behavior

Official replay smoke command:

```text
python tools/sample_market_data.py --adapter replay_tether_cross_market_premium --samples 3 --interval 0 --output data/market_samples/tether_cross_market_replay_sampling_summary.json
```

User-local/normal-network live smoke command:

```text
python tools/sample_market_data.py --adapter live_tether_cross_market_premium --samples 3 --interval 1 --output data/market_samples/tether_cross_market_live_sampling_summary.json
```

Sampling remains read-only. `--handoff-output` and `--journal` remain opt-in behaviors only; this PR does not make Council handoff or journal writes default behavior. Alerts and notifications are not added.

## 6. Replay sampling smoke result

Command run:

```text
python tools/sample_market_data.py --adapter replay_tether_cross_market_premium --samples 3 --interval 0 --output data/market_samples/tether_cross_market_replay_sampling_summary.json
```

Result: pass.

```text
Market sampling saved to: data/market_samples/tether_cross_market_replay_sampling_summary.json
summary: status=PERSISTENT_NET_GAP ok=3 errors=0 council_recommended=False
```

Replay summary inspection:

```text
schema_version: market_sampling_v1
adapter_id: replay_tether_cross_market_premium
samples_requested: 3
samples_ok: 3
samples_error: 0
persistence_status: PERSISTENT_NET_GAP
council_recommended: False
```

Each sample recorded:

```text
status: ok
strategy_family: tether_cross_market_premium
readiness_status: WATCH
recommended_default_decision: WATCH
candidate_count: 2
successful_global_reference_count: None
```

Best candidate core metrics for each sample:

```text
candidate_id: upbit_to_bithumb_tether_cross_market
estimated_net_gap_pct: 0.43942446
net_gap_pass: True
global_reference_pass: True
global_reference_venue_count: 3
global_usdt_depeg_flag: False
global_usdt_depeg_pct: 0.0
global_usdt_mid: 1.0
domestic_best_bid: 1400.0
domestic_best_ask: 1390.0
domestic_mid: 1395.0
```

Interpretation: deterministic replay sampling is now usable as a baseline smoke for tether sampling. It records the core tether candidate metrics in `best_candidate` while keeping Council handoff disabled by default.

## 7. Live sampling smoke result

Command run:

```text
python tools/sample_market_data.py --adapter live_tether_cross_market_premium --samples 3 --interval 1 --output data/market_samples/tether_cross_market_live_sampling_summary.json
```

Result: command exited `0`, but all three samples were errors in this Codex workspace due to the known network tunnel `403 Forbidden` environment blocker.

```text
Market sampling saved to: data/market_samples/tether_cross_market_live_sampling_summary.json
summary: status=INSUFFICIENT_DATA ok=0 errors=3 council_recommended=False
```

Live summary inspection:

```text
schema_version: market_sampling_v1
adapter_id: live_tether_cross_market_premium
samples_requested: 3
samples_ok: 0
samples_error: 3
persistence_status: INSUFFICIENT_DATA
recommended_default_decision: NEED_DATA
```

Representative sample error:

```text
Domestic child adapter live_upbit_usdt_krw_spot failed: Network error for https://api.upbit.com/v1/ticker?markets=KRW-USDT: Tunnel connection failed: 403 Forbidden
```

Classification: environment/network/location issue in the Codex workspace, not a code/config/parser failure. Previous user-local normal-network evidence remains the live success evidence. Human/user-local recheck command is the live sampling command listed in section 5.

## 8. Sampling summary fields

Replay sampling result satisfies:

- `schema_version == market_sampling_v1`
- `adapter_id == replay_tether_cross_market_premium`
- `samples_requested == 3`
- sample statuses are explicit `ok`
- each ok sample includes `opportunity_packet`
- each ok sample has `strategy_family == tether_cross_market_premium`
- `readiness_status == WATCH`
- `recommended_default_decision == WATCH`, consistent with the evaluate-only readiness result
- `candidate_count == 2`
- `best_candidate` includes `estimated_net_gap_pct`, `net_gap_pass`, `global_reference_pass`, `global_reference_venue_count`, `global_usdt_depeg_flag`, `global_usdt_depeg_pct`, `global_usdt_mid`, `domestic_best_bid`, `domestic_best_ask`, and `domestic_mid`
- `council_recommended == False`
- generated packet/sampling JSON was not committed

## 9. Generated artifact cleanup

Generated artifacts from this task were removed after inspection:

- `data/market_samples/tether_cross_market_replay_sampling_summary.json`
- `data/market_samples/tether_cross_market_live_sampling_summary.json`
- `data/market_samples/tether_cross_market_replay_sampling_summary/`
- `data/market_samples/tether_cross_market_live_sampling_summary/`

No generated packet JSON, generated sampling JSON, or generated Council session JSON is intended to be committed.

## 10. Tests run

### Status checks

```text
git status
git diff --name-only
git diff --stat
```

Result before changes: working tree clean; `git diff --name-only` and `git diff --stat` printed no output.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: pass.

```text
Ran 249 tests in 12.099s
OK
```

### Tether-specific unit test

```text
python -m unittest discover -s tests -p "test_tether_cross_market_live_composite_adapter.py"
```

Result: pass.

```text
Ran 15 tests in 0.101s
OK
```

### Sampling unit tests

```text
python -m unittest discover -s tests -p "*sampling*.py"
```

Result: pass.

```text
Ran 19 tests in 0.872s
OK
```

### Evaluate-only scenario smoke

```text
python tools/run_strategy_scenarios.py --strategy tether_cross_market_premium --evaluate-only
```

Result: pass. Scenario outputs matched expected `NEED_DATA`, `REJECT`, and `WATCH` classifications.

### Replay tether sampling smoke

```text
python tools/sample_market_data.py --adapter replay_tether_cross_market_premium --samples 3 --interval 0 --output data/market_samples/tether_cross_market_replay_sampling_summary.json
```

Result: pass. See section 6.

### Live tether sampling smoke

```text
python tools/sample_market_data.py --adapter live_tether_cross_market_premium --samples 3 --interval 1 --output data/market_samples/tether_cross_market_live_sampling_summary.json
```

Result: command completed with `EXIT:0`, but all samples were errors due to Codex workspace network tunnel `403 Forbidden`. See section 7.

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

## 11. Risks

- Replay sampling is deterministic and useful for baseline schema/summary checks, but it does not prove live-market persistence.
- Codex workspace live sampling remains blocked by network tunnel `403 Forbidden`; user-local normal-network live sampling should be re-run if live persistence evidence is needed.
- `PERSISTENT_NET_GAP` and `WATCH` are evaluate-only sampling signals, not execution signals.
- Exposing additional metrics in sampling summaries may require reviewer confirmation that field names are sufficient before any future alert/journal/Council work.

## 12. Rollback plan

- Revert `src/market_data/sampling.py`, `tests/test_tether_cross_market_sampling.py`, and this handoff file.
- Re-run `python -m unittest discover -s tests`.
- Delete any local generated sampling/packet artifacts.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no no-trade violation was introduced.

## 13. Human review required

Reviewers should inspect:

1. `docs/pr_handoffs/tether_cross_market_sampling_baseline_v0.md`
2. `src/market_data/sampling.py`
3. `tests/test_tether_cross_market_sampling.py`

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
- alert expansion: no
- notification expansion: no
- FX / USD-KRW / fair_usdt_krw_price calculation: no
- generated packet JSON commit: no
- generated sampling JSON commit: no

## 15. Next recommended step

After human review, run the documented live sampling command in a user-local normal-network environment and record the resulting persistence evidence in a separate PR. Do not add alert/notification rules, Council handoff automation, active promotion, or execution/private API surfaces without a separate task card, explicit human review, and rollback/kill-switch planning.
