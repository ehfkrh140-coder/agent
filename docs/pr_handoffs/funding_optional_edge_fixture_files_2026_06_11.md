# Funding Optional / Edge Fixture Files v0 Handoff

## Summary

This is a fixture-only PR that adds 4 optional context funding-rate fixture JSON files and 10 edge case funding-rate fixture JSON files. It does not implement a parser, adapter, packet builder, readiness policy, sampling collector, endpoint caller, alert, execution flow, or active strategy promotion.

The fixtures are deterministic static test data shaped after public exchange documentation patterns. They are not live exchange responses, not generated packet/sampling artifacts, and not trading signals.

## PR Review Evidence

- PR number: TBD by GitHub after PR creation.
- Branch name: `fixtures/funding-optional-edge-v0`.
- Base branch: intended `origin/main`; local fetch failed, so reviewer must verify GitHub base branch and commit parent.
- Commit hash: pending until commit is created.
- Commit parent hash: `e351dbb` in this local workspace.
- GitHub PR Files changed reviewer checklist included: Yes.

## Branch Freshness Evidence

- `git fetch origin main` success: No.
- Exact failure reason:

  ```text
  fatal: unable to access 'https://github.com/ehfkrh140-coder/agent.git/': CONNECT tunnel failed, response 403
  ```

- Fresh `origin/main` branch: Not proven in this Codex workspace because fetch failed.
- Reviewer action: because freshness is not proven locally, the GPT designer or human reviewer must inspect GitHub PR commit parent, base branch, and Files changed more strictly before merge. If GitHub Files changed differs from Expected Files Changed, merge must remain on hold.

## Expected vs Actual Files Changed

Expected Files Changed should contain exactly 15 files: 14 new funding fixture JSON files plus this handoff.

Pending staged-file validation is recorded in the Validation section after files are staged.

## GitHub PR Files Changed Reviewer Checklist

After PR creation, reviewer must verify:

- GitHub Files changed exactly matches Expected Files Changed.
- Only optional fixture 4 files and edge fixture 10 files were added.
- Required normal fixture 3 files were not modified.
- No tests Python code was modified.
- No `src/`, `config/`, `configs/`, `tools/`, `data/generated_packets/`, or `data/market_samples/` files were modified.
- No generated packet/sampling JSON was created or committed.
- No previous planning docs, previous handoffs, or cumulative unrelated docs are included.

## Inputs Reviewed

Repo documents reviewed or checked in this workspace:

- `docs/AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md`
- `docs/codex_pr_review_gate.md`
- `docs/merge_gate.md`
- `docs/strategy_evidence_dashboard.md`
- `AGENTS.md`
- `docs/no_trade_policy.md`
- `docs/pr_handoffs/README.md`
- `docs/rollback_policy.md`
- `docs/task_checklist.md`
- `docs/agent_workflow.md`

Documents requested by the task but absent in this local checkout because branch freshness could not be proven after fetch failure:

- `docs/strategy_module_boundaries.md`
- `docs/funding_rate_context_strategy.md`
- `docs/funding_rate_mocked_fixture_contract.md`
- `docs/pr_handoffs/funding_public_source_research_finalization_2026_06_11.md`
- `docs/pr_handoffs/funding_mocked_fixture_contract_2026_06_11.md`
- `docs/pr_handoffs/funding_mocked_required_fixture_files_2026_06_11.md`

Reviewer should verify that the GitHub base branch contains the expected prior funding planning and required fixture context before merge.

## Current Baseline Preservation

The active baseline remains `cross_exchange_spot_spread_v1`. Existing experimental strategy status, readiness semantics, dashboard interpretation, and `NO_TRADE_ONLY` policy are unchanged. This PR only adds static fixture JSON files and a handoff evidence document.

## Why Optional / Edge Fixtures Now

Required normal fixtures cover the minimum successful funding-history parse path. Optional context fixtures and edge fixtures come next so a future parser can be tested against interval/cap/floor metadata, category preservation, current/predicted-vs-settled semantics, missing fields, numeric parsing, timestamp watch context, high absolute funding context, and non-8h interval assumptions before runtime code is introduced.

## Optional Fixture Set

| Fixture | Purpose | Source semantics expectation | Guardrail |
|---|---|---|---|
| `binance_usdm_funding_info_interval_cap_floor.json` | Binance optional funding interval / cap / floor context | `interval_cap_floor_context` | Cap/floor and interval are context, not trade permission. |
| `bybit_linear_instruments_info_funding_interval.json` | Bybit linear product metadata and funding interval context | `instrument_interval_cap_floor_context` | Product metadata is not a funding event or signal. |
| `bybit_inverse_funding_history_normal.json` | Bybit inverse funding-history category coverage | `settled_historical_funding_context` | Inverse category is not collapsed into linear and sign is not direction advice. |
| `okx_current_funding_rate_normal.json` | OKX current / predicted funding context | `current_predicted_funding_context` | `fundingRate`, `nextFundingRate`, and `settFundingRate` stay separate and are not ENTER triggers. |

## Edge Case Fixture Set

| Fixture | Purpose | Expected future parser interpretation | Guardrail |
|---|---|---|---|
| `missing_required_funding_rate.json` | Missing required funding rate field | Failure or `NEED_SOURCE_FIELDS` candidate with `funding_rate` missing | No readiness or trade signal. |
| `missing_optional_interval.json` | Optional interval missing | `OK` candidate with `funding_interval_hours` in optional missing fields | Optional missing interval must not fail required parse path. |
| `string_numeric_parsing.json` | String numeric parsing coverage | Deterministic parsing for funding, mark, premium, cap/floor, timestamp strings | Numeric parse success is not a signal. |
| `positive_funding_rate.json` | Positive funding context | `OK` candidate | Positive funding is not short permission. |
| `negative_funding_rate.json` | Negative funding context | `OK` candidate | Negative funding is not long permission. |
| `zero_funding_rate.json` | Zero funding context | `OK` candidate | Zero funding is not a no-risk or no-trade conclusion. |
| `high_absolute_funding_context.json` | High absolute funding context | `OK_WITH_WARNINGS` candidate with `high_abs_funding_context` | Human watch context only; not ENTER or promotion evidence. |
| `timestamp_data_age_clock_skew_watch.json` | Timestamp watch context | `OK_WITH_WARNINGS` candidate with timestamp warning | No clock-skew calculation implemented in this PR. |
| `varying_funding_interval.json` | Non-8h interval coverage | `OK` candidate with do-not-hard-code warning | Interval is context; readiness unchanged. |
| `okx_predicted_vs_realized_semantics.json` | OKX predicted/current vs realized/settled separation | `OK` candidate with do-not-collapse warning | Funding fields must be interpreted with source semantics. |

## Fixture Data Policy

- Deterministic fake data only.
- No live endpoint calls.
- No live response copy/paste.
- No private API, credentials, account, order, alert, execution, or Council auto-call data.
- Fixed millisecond timestamps only; no live current timestamps.
- Funding, premium, cap/floor, and mark reference values use string numeric forms where exchange payloads commonly do so.
- JSON comments and trailing commas are not used.
- These fixtures are static tests/fixtures data, not generated packet/sampling artifacts.

## JSON Validation Evidence

Pending final command output is recorded in the Validation section after staging.

Expected validation coverage:

- `python -m json.tool` for each of 14 new fixture files.
- Python `json.load` for all funding fixture JSON files present in this checkout.
- Top-level shape sanity check for list/dict by fixture file.

## Test Evidence

- GitHub Checks / CI Status: GitHub Checks / CI independent verification unavailable in this Codex environment. Reviewer must inspect GitHub Checks after PR creation if available.
- Codex/local validation commands and output: recorded in the Validation section.
- `python -m unittest discover -s tests`: recorded in the Validation section.

## Context vs Signal Guardrail

Funding fixtures are not standalone WATCH, ENTER, alert, execution, Council recommendation, or active-promotion triggers. Positive funding is not short permission. Negative funding is not long permission. High absolute funding may be future human watch context, but it is not an ENTER trigger. JSON validity and future parser success do not change readiness, `recommended_default_decision`, Council recommendation, active status, alerts, or execution.

## Existing System Preservation Gate

- 기존 public adapter → parser → OpportunityPacket → readiness → sampling → handoff → dashboard → Council manual review 흐름을 보존하는가? Yes. No runtime pipeline files were modified.
- active baseline `cross_exchange_spot_spread_v1` behavior를 바꾸지 않는가? Yes.
- 기존 experimental strategy status / readiness semantics / dashboard interpretation을 바꾸지 않는가? Yes.
- Funding Rate를 기존 공통 모듈에 강제로 섞지 않고 static fixture data로만 추가했는가? Yes.
- Context-only 정보와 executable signal을 분리하는가? Yes.
- generated packet/sampling JSON을 만들거나 commit하지 않는가? Yes.
- private API / credential / order / alert / Council auto-call을 추가하지 않는가? Yes.
- readiness 변경 없이 fixture-files-only로 유지하는가? Yes.
- endpoint 호출 없이 deterministic mocked data만 작성했는가? Yes.

## No-Trade Compliance

`NO_TRADE_ONLY` is preserved. This PR adds no private API, API key, secret, token, account/balance/position lookup, order/cancel/transfer/withdraw/deposit code, auto-trading, alert execution, Council auto-call, active promotion, or execution path.

## Behavior Unchanged

No `src/`, `config/`, `configs/`, `tools/`, `data/generated_packets/`, or `data/market_samples/` files were modified. The only `tests/` changes are static fixture JSON files under `tests/fixtures/market_data/funding_rate/`; no test Python code was modified. Runtime behavior is unchanged.

## Generated Artifact Policy

No generated JSON under `data/generated_packets` or `data/market_samples` was created or committed. The JSON files in this PR are deterministic static test fixtures, not generated packet/sampling artifacts.

## Files Changed

Expected Files Changed:

- `tests/fixtures/market_data/funding_rate/binance_usdm_funding_info_interval_cap_floor.json`
- `tests/fixtures/market_data/funding_rate/bybit_linear_instruments_info_funding_interval.json`
- `tests/fixtures/market_data/funding_rate/bybit_inverse_funding_history_normal.json`
- `tests/fixtures/market_data/funding_rate/okx_current_funding_rate_normal.json`
- `tests/fixtures/market_data/funding_rate/missing_required_funding_rate.json`
- `tests/fixtures/market_data/funding_rate/missing_optional_interval.json`
- `tests/fixtures/market_data/funding_rate/string_numeric_parsing.json`
- `tests/fixtures/market_data/funding_rate/positive_funding_rate.json`
- `tests/fixtures/market_data/funding_rate/negative_funding_rate.json`
- `tests/fixtures/market_data/funding_rate/zero_funding_rate.json`
- `tests/fixtures/market_data/funding_rate/high_absolute_funding_context.json`
- `tests/fixtures/market_data/funding_rate/timestamp_data_age_clock_skew_watch.json`
- `tests/fixtures/market_data/funding_rate/varying_funding_interval.json`
- `tests/fixtures/market_data/funding_rate/okx_predicted_vs_realized_semantics.json`
- `docs/pr_handoffs/funding_optional_edge_fixture_files_2026_06_11.md`

## Validation

Validation evidence was recorded after staging the exact expected file set.

- `git status --short --branch`

  ```text
  ## fixtures/funding-optional-edge-v0
  A  docs/pr_handoffs/funding_optional_edge_fixture_files_2026_06_11.md
  A  tests/fixtures/market_data/funding_rate/binance_usdm_funding_info_interval_cap_floor.json
  A  tests/fixtures/market_data/funding_rate/bybit_inverse_funding_history_normal.json
  A  tests/fixtures/market_data/funding_rate/bybit_linear_instruments_info_funding_interval.json
  A  tests/fixtures/market_data/funding_rate/high_absolute_funding_context.json
  A  tests/fixtures/market_data/funding_rate/missing_optional_interval.json
  A  tests/fixtures/market_data/funding_rate/missing_required_funding_rate.json
  A  tests/fixtures/market_data/funding_rate/negative_funding_rate.json
  A  tests/fixtures/market_data/funding_rate/okx_current_funding_rate_normal.json
  A  tests/fixtures/market_data/funding_rate/okx_predicted_vs_realized_semantics.json
  A  tests/fixtures/market_data/funding_rate/positive_funding_rate.json
  A  tests/fixtures/market_data/funding_rate/string_numeric_parsing.json
  A  tests/fixtures/market_data/funding_rate/timestamp_data_age_clock_skew_watch.json
  A  tests/fixtures/market_data/funding_rate/varying_funding_interval.json
  A  tests/fixtures/market_data/funding_rate/zero_funding_rate.json
  ```

- `git diff --cached --name-only`

  ```text
docs/pr_handoffs/funding_optional_edge_fixture_files_2026_06_11.md
tests/fixtures/market_data/funding_rate/binance_usdm_funding_info_interval_cap_floor.json
tests/fixtures/market_data/funding_rate/bybit_inverse_funding_history_normal.json
tests/fixtures/market_data/funding_rate/bybit_linear_instruments_info_funding_interval.json
tests/fixtures/market_data/funding_rate/high_absolute_funding_context.json
tests/fixtures/market_data/funding_rate/missing_optional_interval.json
tests/fixtures/market_data/funding_rate/missing_required_funding_rate.json
tests/fixtures/market_data/funding_rate/negative_funding_rate.json
tests/fixtures/market_data/funding_rate/okx_current_funding_rate_normal.json
tests/fixtures/market_data/funding_rate/okx_predicted_vs_realized_semantics.json
tests/fixtures/market_data/funding_rate/positive_funding_rate.json
tests/fixtures/market_data/funding_rate/string_numeric_parsing.json
tests/fixtures/market_data/funding_rate/timestamp_data_age_clock_skew_watch.json
tests/fixtures/market_data/funding_rate/varying_funding_interval.json
tests/fixtures/market_data/funding_rate/zero_funding_rate.json
  ```

- Expected Files Changed comparison

  ```text
  Expected Files Changed set match: True
  Actual count: 15
docs/pr_handoffs/funding_optional_edge_fixture_files_2026_06_11.md
tests/fixtures/market_data/funding_rate/binance_usdm_funding_info_interval_cap_floor.json
tests/fixtures/market_data/funding_rate/bybit_inverse_funding_history_normal.json
tests/fixtures/market_data/funding_rate/bybit_linear_instruments_info_funding_interval.json
tests/fixtures/market_data/funding_rate/high_absolute_funding_context.json
tests/fixtures/market_data/funding_rate/missing_optional_interval.json
tests/fixtures/market_data/funding_rate/missing_required_funding_rate.json
tests/fixtures/market_data/funding_rate/negative_funding_rate.json
tests/fixtures/market_data/funding_rate/okx_current_funding_rate_normal.json
tests/fixtures/market_data/funding_rate/okx_predicted_vs_realized_semantics.json
tests/fixtures/market_data/funding_rate/positive_funding_rate.json
tests/fixtures/market_data/funding_rate/string_numeric_parsing.json
tests/fixtures/market_data/funding_rate/timestamp_data_age_clock_skew_watch.json
tests/fixtures/market_data/funding_rate/varying_funding_interval.json
tests/fixtures/market_data/funding_rate/zero_funding_rate.json
  ```

- `python -m json.tool` for each new fixture

  ```text
tests/fixtures/market_data/funding_rate/binance_usdm_funding_info_interval_cap_floor.json: json.tool OK
tests/fixtures/market_data/funding_rate/bybit_linear_instruments_info_funding_interval.json: json.tool OK
tests/fixtures/market_data/funding_rate/bybit_inverse_funding_history_normal.json: json.tool OK
tests/fixtures/market_data/funding_rate/okx_current_funding_rate_normal.json: json.tool OK
tests/fixtures/market_data/funding_rate/missing_required_funding_rate.json: json.tool OK
tests/fixtures/market_data/funding_rate/missing_optional_interval.json: json.tool OK
tests/fixtures/market_data/funding_rate/string_numeric_parsing.json: json.tool OK
tests/fixtures/market_data/funding_rate/positive_funding_rate.json: json.tool OK
tests/fixtures/market_data/funding_rate/negative_funding_rate.json: json.tool OK
tests/fixtures/market_data/funding_rate/zero_funding_rate.json: json.tool OK
tests/fixtures/market_data/funding_rate/high_absolute_funding_context.json: json.tool OK
tests/fixtures/market_data/funding_rate/timestamp_data_age_clock_skew_watch.json: json.tool OK
tests/fixtures/market_data/funding_rate/varying_funding_interval.json: json.tool OK
tests/fixtures/market_data/funding_rate/okx_predicted_vs_realized_semantics.json: json.tool OK
  ```

- Python `json.load` validation and top-level shape check for all funding fixture JSON files present in this checkout

  ```text
tests/fixtures/market_data/funding_rate/binance_usdm_funding_info_interval_cap_floor.json: json.load OK (list)
tests/fixtures/market_data/funding_rate/bybit_inverse_funding_history_normal.json: json.load OK (dict)
tests/fixtures/market_data/funding_rate/bybit_linear_instruments_info_funding_interval.json: json.load OK (dict)
tests/fixtures/market_data/funding_rate/high_absolute_funding_context.json: json.load OK (dict)
tests/fixtures/market_data/funding_rate/missing_optional_interval.json: json.load OK (dict)
tests/fixtures/market_data/funding_rate/missing_required_funding_rate.json: json.load OK (dict)
tests/fixtures/market_data/funding_rate/negative_funding_rate.json: json.load OK (dict)
tests/fixtures/market_data/funding_rate/okx_current_funding_rate_normal.json: json.load OK (dict)
tests/fixtures/market_data/funding_rate/okx_predicted_vs_realized_semantics.json: json.load OK (dict)
tests/fixtures/market_data/funding_rate/positive_funding_rate.json: json.load OK (dict)
tests/fixtures/market_data/funding_rate/string_numeric_parsing.json: json.load OK (dict)
tests/fixtures/market_data/funding_rate/timestamp_data_age_clock_skew_watch.json: json.load OK (dict)
tests/fixtures/market_data/funding_rate/varying_funding_interval.json: json.load OK (dict)
tests/fixtures/market_data/funding_rate/zero_funding_rate.json: json.load OK (dict)
  ```

- `git diff --cached --name-only -- src config configs tools data/generated_packets data/market_samples`

  ```text
  <no output>
  ```

- `git diff --cached --name-only -- tests`

  ```text
tests/fixtures/market_data/funding_rate/binance_usdm_funding_info_interval_cap_floor.json
tests/fixtures/market_data/funding_rate/bybit_inverse_funding_history_normal.json
tests/fixtures/market_data/funding_rate/bybit_linear_instruments_info_funding_interval.json
tests/fixtures/market_data/funding_rate/high_absolute_funding_context.json
tests/fixtures/market_data/funding_rate/missing_optional_interval.json
tests/fixtures/market_data/funding_rate/missing_required_funding_rate.json
tests/fixtures/market_data/funding_rate/negative_funding_rate.json
tests/fixtures/market_data/funding_rate/okx_current_funding_rate_normal.json
tests/fixtures/market_data/funding_rate/okx_predicted_vs_realized_semantics.json
tests/fixtures/market_data/funding_rate/positive_funding_rate.json
tests/fixtures/market_data/funding_rate/string_numeric_parsing.json
tests/fixtures/market_data/funding_rate/timestamp_data_age_clock_skew_watch.json
tests/fixtures/market_data/funding_rate/varying_funding_interval.json
tests/fixtures/market_data/funding_rate/zero_funding_rate.json
  ```

- Existing required normal fixture modified check

  ```text
  <no output>
  ```

  Interpretation: the three required normal fixture paths were not modified in this cached diff.

- `find data/generated_packets data/market_samples -type f -name '*.json'`

  ```text
  find: ‘data/generated_packets’: No such file or directory
  find: ‘data/market_samples’: No such file or directory
  ```

  Interpretation: generated artifact directories are absent in this local checkout, so no generated packet/sampling JSON was found or staged.

- `find tests/fixtures/market_data/funding_rate -type f -name '*.json' | sort`

  ```text
tests/fixtures/market_data/funding_rate/binance_usdm_funding_info_interval_cap_floor.json
tests/fixtures/market_data/funding_rate/bybit_inverse_funding_history_normal.json
tests/fixtures/market_data/funding_rate/bybit_linear_instruments_info_funding_interval.json
tests/fixtures/market_data/funding_rate/high_absolute_funding_context.json
tests/fixtures/market_data/funding_rate/missing_optional_interval.json
tests/fixtures/market_data/funding_rate/missing_required_funding_rate.json
tests/fixtures/market_data/funding_rate/negative_funding_rate.json
tests/fixtures/market_data/funding_rate/okx_current_funding_rate_normal.json
tests/fixtures/market_data/funding_rate/okx_predicted_vs_realized_semantics.json
tests/fixtures/market_data/funding_rate/positive_funding_rate.json
tests/fixtures/market_data/funding_rate/string_numeric_parsing.json
tests/fixtures/market_data/funding_rate/timestamp_data_age_clock_skew_watch.json
tests/fixtures/market_data/funding_rate/varying_funding_interval.json
tests/fixtures/market_data/funding_rate/zero_funding_rate.json
  ```

- `git diff --check --cached`

  ```text
  <no output>
  ```

- `python -m unittest discover -s tests`

  ```text
  Ran 531 tests in 15.334s

  OK
  ```

## Merge Recommendation

Codex does not recommend merging solely from local evidence. GPT designer or human reviewer must inspect GitHub PR Files changed, branch freshness / commit parent, validation evidence, and GitHub Checks if available before deciding whether to merge.

## Next Recommended Step

Recommended next step: Funding Pure Parser Helper Planning v0 before implementation, because the project still needs a parser-status naming plan and source-semantics mapping review before code is introduced. If the reviewer prefers implementation next, Funding Pure Parser Helper Implementation v0 must remain public-read-only, context-only, fixture-driven, and no-trade-first.
