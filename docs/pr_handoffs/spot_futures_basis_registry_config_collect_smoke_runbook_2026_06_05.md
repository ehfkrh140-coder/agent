# Spot-Futures Basis Registry / Config / Collect Smoke Integration Runbook v0

## 1. 작업 목적

이 문서는 `spot_futures_basis_v0` first public-read-only adapter 구현 이후 registry/config, `collect_market_data`, `sample_market_data`, user-local smoke, 3-sample evidence, 30-sample evidence로 연결하기 위한 docs-only integration runbook이다.

Purpose:

- `spot_futures_basis_v0` adapter 구현 이후 다음 연결 단계를 안전하게 계획한다.
- Registry/config/collect/sampling을 한 PR에 몰아넣지 않기 위한 runbook이다.
- 현재 behavior는 유지한다.
- `NO_TRADE_ONLY`를 유지한다.
- 이번 PR은 implementation이 아니라 integration runbook이다.
- 이번 PR에서는 code, tests, fixtures, config, registry, tools, runtime behavior를 변경하지 않는다.

## 2. Current implementation inventory

| Area | Current status | Evidence / notes |
| --- | --- | --- |
| Mocked fixture files | 존재 | `tests/fixtures/market_data/spot_futures_basis/*.json` seven deterministic Binance Spot / USDⓈ-M Futures fixtures exist. |
| Fixture contract tests | 존재 | `tests/test_spot_futures_basis_mocked_fixtures.py` validates shape, placement, and no-private/no-generated guardrails. |
| Parser helper | 존재 | `src/market_data/parsers/spot_futures_basis.py` parses Binance spot/perp payload dicts into normalized observations and source bundle. |
| Readiness helper | 존재 | `src/strategy/spot_futures_basis_readiness.py` evaluates `REJECT` / `NEED_DATA` / `WATCH` as analysis-only readiness. |
| Pure packet builder | 존재 | `src/market_data/spot_futures_basis_packet_builder.py` returns an `opportunity_packet_v0` compatible dict from source bundle + readiness result. |
| Public-read-only adapter | 존재 | `src/market_data/adapters/spot_futures_basis.py` provides `BinanceSpotFuturesBasisAdapter` with injected HTTP client support and mocked/unit tests only. |
| Registry/config entry | 없음 | `configs/market_data.yaml` has no `live_binance_spot_futures_basis_btcusdt` entry in this PR. |
| `collect_market_data` official adapter path | 없음 / needs_follow_up_verification | `tools/collect_market_data.py` calls `src.market_data.registry.build_adapter(...)` and then `OpportunityPacketBuilder().build(snapshot)`. `src/market_data/registry.py` does not yet import/register `BinanceSpotFuturesBasisAdapter`; collect may also need packet-pass-through or builder support for already-packet-shaped dicts. |
| `sample_market_data` support | 없음 / needs_follow_up_verification | `tools/sample_market_data.py` uses `build_adapter(...)` and `run_market_sampling(...)`; sampling also calls `OpportunityPacketBuilder().build(snapshot)`. Support for `spot_futures_basis` packet-shaped adapter output needs follow-up verification. |
| User-local live smoke evidence | 없음 | No docs-only user-local smoke evidence exists yet for `spot_futures_basis_v0`. |
| 3-sample evidence | 없음 | No 3-sample sampling evidence exists yet for `spot_futures_basis_v0`. |
| 30-sample evidence | 없음 | No 30-sample extended evidence exists yet for `spot_futures_basis_v0`. |
| Active promotion | 없음 | Active strategy remains `cross_exchange_spot_spread_v1`; `spot_futures_basis_v0` remains proposed / experimental / non-active / `NO_TRADE_ONLY`. |

## 3. Existing pattern inventory

This PR only investigates and documents patterns. It does not modify any source, tests, fixtures, config, registry, generated data, or tools.

| Pattern | Existing file / name | Observed behavior | Follow-up status |
| --- | --- | --- | --- |
| Adapter registry lookup | `src/market_data/registry.py::build_adapter` | Loads `configs/market_data.yaml`, reads `adapters.<adapter_id>.type`, and switches on `adapter_type` to instantiate adapters. Mark-orderbook-gap adapters are registered through explicit imports and `if adapter_type == ...` branches. | `spot_futures_basis` needs a future explicit import and `adapter_type == "binance_spot_futures_basis"` branch. |
| Adapter listing | `src/market_data/registry.py::list_adapters` | Returns sorted keys under `config["adapters"]`. | Future config entry will make adapter visible to `tools/collect_market_data.py --list-adapters`. |
| Config entry pattern | `configs/market_data.yaml` | Existing live experimental adapters use `enabled: false`, `experimental: true`, `experimental_strategy: true`, `non_active_strategy: true`, `no_trade_only: true`, and `execution_policy: NO_TRADE_ONLY` for Mark-Orderbook Gap. | Future spot-futures entry should copy no-trade/disabled pattern and remain non-active. |
| Collect adapter lookup | `tools/collect_market_data.py` | CLI loads config via `load_market_data_config`, builds adapter via `build_adapter`, calls `adapter.fetch_snapshot()`, then calls `OpportunityPacketBuilder().build(snapshot)` before optional JSON output. | needs_follow_up_verification: `spot_futures_basis` adapter returns packet-compatible dict, so collect may require pass-through or `OpportunityPacketBuilder` support for `signal_type=spot_futures_basis`. |
| Sampling adapter lookup | `tools/sample_market_data.py` | CLI builds adapter via registry and passes it to `run_market_sampling`. | needs_follow_up_verification: sampling path likely needs the same packet-pass-through / builder support as collect. |
| Sampling packet conversion | `src/market_data/sampling.py::run_market_sampling` | For each sample, calls `adapter.fetch_snapshot()`, then `OpportunityPacketBuilder().build(snapshot)`, then readiness reporting and summary enrichment. | needs_follow_up_verification: verify whether `OpportunityPacketBuilder` accepts already-packet-compatible spot-futures snapshots; if not, add mocked/unit support in a later code PR. |
| Sampling summary fields | `src/market_data/sampling.py::_sample_record` and `_enrich_sampling_summary` | Extracts readiness/default decision from packet extensions and candidate metrics; counts `WATCH` / `REJECT` / `NEED_DATA`; records diagnostics count and adapter metadata no-trade fields. | Likely reusable for `spot_futures_basis` once packet conversion path works; still needs mocked/unit coverage. |
| Evidence handoff pattern | `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_binance_sampling_smoke_v0.md` and related Mark-Orderbook Gap handoffs | User-local command, generated output path, summarized fields, no-trade interpretation, generated JSON cleanup, rollback, and test evidence are documented without committing raw generated JSON. | Reuse this evidence structure for spot-futures collect and sampling evidence. |
| Generated JSON cleanup / commit ban | `docs/no_trade_policy.md`, `docs/pr_handoffs/README.md`, Mark-Orderbook Gap evidence docs | Generated `data/market_samples/*.json` and `data/generated_packets/*.json` are smoke artifacts and must not be committed. | Continue mandatory generated path checks in every PR. |
| No-trade metadata pattern | Mark-Orderbook Gap config entries and adapter metadata | Existing experimental entries include `NO_TRADE_ONLY`, non-active flags, and notes forbidding sampling/Council/alert/execution. | Future spot-futures config/registry must keep the same explicit no-trade language. |
| Rollback pattern | `docs/rollback_policy.md` and handoff docs | Docs-only rollback is revert/remove handoff; config/registry rollback is removing entries and rerunning tests. | Future code/config PRs should name exact files and rollback commands. |

## 4. Proposed adapter identity and config boundary

Future registry/config candidate, planning-only:

- `adapter_id`: `live_binance_spot_futures_basis_btcusdt`
- `type`: `binance_spot_futures_basis`
- `strategy_family`: `spot_futures_basis`
- `strategy_id`: `spot_futures_basis_v0`
- `source_venue_id`: `binance`
- `status`: experimental / non-active / `NO_TRADE_ONLY`
- `enabled_by_default`: `false`
- `enabled`: `false`
- `active_strategy`: `false`
- `experimental`: `true`
- `experimental_strategy`: `true`
- `non_active_strategy`: `true`
- `no_trade_only`: `true`
- `execution_policy`: `NO_TRADE_ONLY`
- `private_api_required`: `false`
- `spot_base_url`: `https://api.binance.com`
- `futures_base_url`: `https://fapi.binance.com`
- `spot_symbol`: `BTCUSDT`
- `perp_symbol`: `BTCUSDT`
- `depth_limit`: `5`

Config boundary:

- This PR does not add registry/config entries.
- Future registry/config entry must not be interpreted as active strategy activation.
- Active strategy remains `cross_exchange_spot_spread_v1`.
- Future registry/config entry must not enable auto execution, Council auto-call, alerting, private API, credentials, account lookup, or orders.
- Rollback for a future config/registry PR is removing the registry branch/import and removing the config entry, then rerunning tests.

## 5. Proposed `collect_market_data` path

Current tool interface candidate based on `tools/collect_market_data.py`:

```bash
python tools/collect_market_data.py --adapter live_binance_spot_futures_basis_btcusdt --output data/generated_packets/spot_futures_basis_binance_collect_smoke_packet.json
```

Status:

- Planning-only; this PR does not run the command.
- `needs_follow_up_verification`: `src/market_data/registry.py` does not yet register `binance_spot_futures_basis`.
- `needs_follow_up_verification`: `tools/collect_market_data.py` currently wraps adapter output with `OpportunityPacketBuilder().build(snapshot)`. Because the spot-futures adapter already returns an `opportunity_packet_v0` compatible dict, the future collect integration may need either:
  - `OpportunityPacketBuilder` support for `signal_type=spot_futures_basis`, or
  - a safe pass-through path for already packet-shaped adapter output, or
  - a small adapter snapshot shape that the existing builder can convert.

Collect smoke success criteria candidate:

- Command exits `0`.
- Output packet `schema_version=opportunity_packet_v0`.
- `signal_type=spot_futures_basis`.
- `strategy_id=spot_futures_basis_v0`.
- `observations` length is `2`.
- `candidates` length is `1`.
- `extensions.no_trade_only=true`.
- `execution_policy=NO_TRADE_ONLY` either at packet extensions or adapter metadata.
- `adapter_metadata.adapter_id=live_binance_spot_futures_basis_btcusdt`.
- Diagnostics count is `7`.
- No private/account/order fields are present.
- Generated packet JSON is a smoke artifact and must not be committed.

## 6. Proposed `sample_market_data` path

Current tool interface candidate based on `tools/sample_market_data.py`:

```bash
python tools/sample_market_data.py --adapter live_binance_spot_futures_basis_btcusdt --samples 3 --interval 2 --output data/market_samples/spot_futures_basis_binance_sampling_3x_summary.json
```

Status:

- Planning-only; this PR does not run the command.
- `needs_follow_up_verification`: registry/config support must exist first.
- `needs_follow_up_verification`: `src/market_data/sampling.py::run_market_sampling` uses `OpportunityPacketBuilder().build(snapshot)` and must be verified with spot-futures adapter output.
- `needs_follow_up_verification`: summary persistence labels may need acceptance tests for `spot_futures_basis` readiness labels and `signal_type`.

Sampling success criteria candidate:

- `samples_requested=3`.
- `samples_ok=3`.
- `samples_error=0`.
- `candidate_seen_count=3` or equivalent candidate count summary.
- Summary status may be `NO_PERSISTENT_EDGE`, `NO_EDGE`, or equivalent depending sampler support.
- `council_recommended=false` is acceptable and expected unless future policy explicitly changes.
- `REJECT` / `NEED_DATA` / `WATCH` must be interpreted as analysis-only.
- Generated sampling JSON is a smoke artifact and must not be committed.

## 7. Recommended next PR sequence

Recommended small PR sequence:

1. PR 1: Registry/config implementation, no activation.
2. PR 2: `collect_market_data` integration, mocked/unit tests only if not covered by registry.
3. PR 3: User-local collect smoke request + docs-only evidence.
4. PR 4: `sample_market_data` support, mocked/unit tests.
5. PR 5: User-local 3-sample sampling evidence.
6. PR 6: User-local 30-sample extended evidence.
7. PR 7: Comparative summary / next venue planning.

If the actual repo structure requires registry/config and collect integration in the same file/PR, the future PR must explain why, keep `enabled=false`, keep `NO_TRADE_ONLY`, add mocked/unit tests, and preserve no activation / no execution.

## 8. User-local runbook

Future user-local PowerShell runbook candidate, planning-only:

```powershell
git pull --ff-only origin main
python -m unittest discover -s tests
python tools/collect_market_data.py --adapter live_binance_spot_futures_basis_btcusdt --output data/generated_packets/spot_futures_basis_binance_collect_smoke_packet.json
Get-Content data/generated_packets/spot_futures_basis_binance_collect_smoke_packet.json | Select-Object -First 80
Remove-Item data/generated_packets/spot_futures_basis_binance_collect_smoke_packet.json
git status --short data\market_samples data\generated_packets
```

Success criteria:

- Tests pass.
- Collect command exits `0`.
- Generated packet has `schema_version=opportunity_packet_v0`.
- Generated packet has `signal_type=spot_futures_basis`.
- Generated packet has `strategy_id=spot_futures_basis_v0`.
- Generated packet has `extensions.no_trade_only=true` and `NO_TRADE_ONLY` metadata.
- Generated packet has 2 observations and 1 candidate.
- Diagnostics count is 7.
- No private/account/order fields appear.
- Generated JSON is removed before commit.
- `git status --short data\market_samples data\generated_packets` returns clean output.

Failure criteria:

- Any private API / credentials / account / order / transfer field appears.
- Any generated JSON remains staged or in worktree.
- `WATCH` is interpreted as execution / alert / Council auto-call.
- Collect command writes outside `data/generated_packets` or another explicitly documented smoke path.
- Output is missing no-trade metadata.
- Live endpoint response shape differs from mocked fixtures enough to produce parser `NEED_DATA` without documented watch items.

## 9. Evidence handoff plan

Future docs-only collect evidence PR should record:

- `adapter_id`
- command
- output path
- `schema_version`
- `signal_type`
- `strategy_id`
- `readiness_status`
- `recommended_default_decision`
- `observations_count`
- `candidates_count`
- `diagnostics_count`
- `no_trade_only`
- `execution_policy`
- generated JSON not committed
- interpretation of `REJECT` / `NEED_DATA` / `WATCH` as analysis-only
- watch items, including parser missing fields, live-shape mismatch, stale timestamp, negative data age, or diagnostics preview concerns
- rollback path
- exact tests/checks run
- generated JSON cleanup command and final generated path status

## 10. Risk assessment

Key risks:

- Registry/config entry can look active if disabled/non-active/no-trade metadata is not explicit.
- Collect smoke and sampling support in one PR increases review and rollback risk.
- Generated packet JSON can be accidentally committed.
- `WATCH` can be misunderstood as a trade signal.
- Live endpoint shape can differ from mocked fixtures.
- Diagnostics safe preview can expose too much raw data if not bounded and reviewed.
- Sample summary parser may not understand the new `signal_type=spot_futures_basis` and fail or under-report fields.
- Codex live network can encounter 403 / regional / rate-limit issues; user-local evidence should be separated from Codex mocked tests.
- User-local evidence and Codex mocked tests must stay separate because generated live outputs are smoke artifacts and should be summarized in docs instead of committed.
- Top-of-book liquidity can be mistaken for fill feasibility unless candidate/readiness wording stays analysis-only.

## 11. No-trade compliance

This docs-only runbook PR preserves no-trade posture:

- Active strategy promotion: no
- `spot_futures_basis_v0` active promotion: no
- Private API: no
- Credentials/API keys/secrets/tokens: no
- Account/balance/position lookup: no
- Order/cancel: no
- Withdrawal/deposit/transfer: no
- Auto-trading: no
- Council auto-call: no
- Alert: no
- Execution: no
- Config/registry change: no
- Source/runtime behavior change: no
- Live endpoint call: no
- Generated JSON creation: no
- `NO_TRADE_ONLY` preserved: yes

## 12. Generated JSON commit 금지

Generated packet/sampling files remain smoke artifacts only and must not be committed:

- `data/market_samples/*.json`
- `data/generated_packets/*.json`

Policy:

- Future collect/sampling outputs are summarized as user-local evidence.
- Raw generated JSON outputs are not committed.
- Generated JSON must be removed before final status checks.
- This PR does not add generated JSON.

## 13. Rollback plan

Rollback path:

1. Revert this docs-only runbook PR.
2. Remove `docs/pr_handoffs/spot_futures_basis_registry_config_collect_smoke_runbook_2026_06_05.md`.
3. No code/config/registry/runtime/parser/readiness/test/fixture/generated-data rollback is required.

## 14. Next PR candidates

Recommended order:

1. Registry/config implementation, no activation
2. Collect integration mocked/unit tests if needed
3. User-local public-read-only collect smoke
4. Docs-only collect evidence
5. 3-sample sampling support
6. 3-sample sampling evidence
7. 30-sample extended evidence
