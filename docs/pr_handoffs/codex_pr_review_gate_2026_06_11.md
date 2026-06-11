# Codex PR Review Gate v0 Handoff

## Summary

This is a governance / review-process docs-only PR. It adds a Codex PR Review Gate so reviewers can verify GitHub PR Files changed, branch freshness evidence, validation output, forbidden-path checks, generated-artifact checks, and `NO_TRADE_ONLY` compliance before merge.

This PR does not implement features, funding fixtures, parsers, adapters, packet builders, readiness logic, sampling collectors, endpoint calls, alerts, execution, or strategy promotion.

## Why This Was Needed Now

A recent required funding fixture workflow exposed an operational review gap: Codex-local staged files can match a task's Expected Files Changed while the GitHub PR Files changed view may still show cumulative files if the branch was not freshly based on `origin/main`.

This is treated as a process guardrail issue, not as blame on a specific PR. The new gate makes GitHub PR Files changed, branch parent evidence, and handoff validation output explicit review sources before merge.

## Files Changed

Expected Files Changed:

- `docs/codex_pr_review_gate.md`
- `docs/merge_gate.md`
- `docs/pr_handoffs/codex_pr_review_gate_2026_06_11.md`

## Review Gate Added

The new review gate requires reviewers to prioritize:

1. GitHub PR Files changed.
2. GitHub PR commit parent / branch freshness evidence.
3. Step-specific handoff file.
4. Codex final report.
5. Validation command output.
6. GitHub Checks / CI if available.
7. Generated JSON / fixture artifact clean check.

It also defines required handoff evidence, Expected-vs-GitHub Files Changed rules, branch freshness handling, a risk-tier review matrix, and reviewer checklist.

## Merge-before-review Policy

Codex may create a PR, but it must not merge it. The user should provide the PR number or URL to the GPT designer or human reviewer, and merge must wait for a success decision. A PR with mismatched GitHub Files changed, cumulative prior docs, forbidden files, missing evidence, or unclear branch freshness must remain on hold.

## Test Evidence Standard

Future handoffs must record actual command lines and key output. A sentence such as “tests passed” is not sufficient.

- Docs-only PRs should record diff, forbidden-path, generated-artifact, and optional unittest evidence.
- Fixture PRs should record JSON syntax/load validation plus forbidden-path and generated-artifact evidence.
- Parser/code PRs must include unittest and task-specific tests.
- If GitHub Checks / CI are unavailable, handoff evidence must explicitly say independent CI is unavailable.

## GitHub Files Changed Priority

GitHub PR Files changed is the highest-priority changed-file source. If GitHub PR Files changed differs from Codex-local staged-file claims, reviewers should trust GitHub first and hold merge until the mismatch is resolved or explained.

## Existing System Preservation Gate

- 기존 runtime pipeline을 보존하는가? Yes. This PR only adds governance documentation and does not touch runtime pipeline code.
- active baseline behavior를 바꾸지 않는가? Yes. `cross_exchange_spot_spread_v1` behavior is unchanged.
- existing experimental strategy status / readiness semantics / dashboard interpretation을 바꾸지 않는가? Yes. No strategy status, readiness semantics, or dashboard interpretation is changed.
- `NO_TRADE_ONLY`를 유지하는가? Yes. The new gate reinforces `NO_TRADE_ONLY` review evidence.
- generated JSON을 만들지 않았는가? Yes. No generated JSON was created or committed.
- private API / order / alert / Council auto-call을 추가하지 않았는가? Yes. No private API, order, alert, or Council auto-call surface was added.
- 이번 PR이 docs-only governance update인가? Yes. It is limited to governance/review-process documentation.

## Behavior Unchanged

No `src/`, `tests/`, `config/`, `configs/`, `tools/`, `data/generated_packets/`, `data/market_samples/`, or `tests/fixtures/` files were modified. Runtime behavior is unchanged.

## Generated Artifact Policy

No generated packet JSON, sampling JSON, market sample JSON, fixture JSON, or other generated artifact was created or committed.

## Validation

Validation evidence was recorded after staging so the cached diff reflects the exact intended PR scope.

- `git status --short --branch`

  ```text
  ## docs/codex-pr-review-gate-v0
  A  docs/codex_pr_review_gate.md
  M  docs/merge_gate.md
  A  docs/pr_handoffs/codex_pr_review_gate_2026_06_11.md
  ```

- `git diff --cached --name-only`

  ```text
  docs/codex_pr_review_gate.md
  docs/merge_gate.md
  docs/pr_handoffs/codex_pr_review_gate_2026_06_11.md
  ```

- Expected Files Changed comparison

  ```text
  Expected Files Changed set match: True
  Actual sorted files:
  docs/codex_pr_review_gate.md
  docs/merge_gate.md
  docs/pr_handoffs/codex_pr_review_gate_2026_06_11.md
  ```

- `git diff --cached --name-only -- src tests config configs tools data/generated_packets data/market_samples`

  ```text
  <no output>
  ```

- `find data/generated_packets data/market_samples -type f -name '*.json'`

  ```text
  find: ‘data/generated_packets’: No such file or directory
  find: ‘data/market_samples’: No such file or directory
  ```

  Interpretation: the generated artifact directories are absent in this local checkout, so no generated packet/sampling JSON was found or staged.

- `git diff --check --cached`

  ```text
  <no output>
  ```

- `python -m unittest discover -s tests`

  ```text
  Ran 531 tests in 14.998s

  OK
  ```

## Next Recommended Step

Next recommended step: Funding Optional / Edge Fixture Files v0. That PR should apply this Codex PR Review Gate from the start, keep public-read-only / context-only / no-trade-first boundaries, and ensure GitHub PR Files changed matches the task's Expected Files Changed before merge.
