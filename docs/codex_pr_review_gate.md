# Codex PR Review Gate

## Purpose

This document defines the review evidence gate that every Codex-authored PR should satisfy before merge review. Its purpose is to make the real GitHub change scope, validation evidence, forbidden-path compliance, generated-artifact status, and `NO_TRADE_ONLY` compliance easy for a reviewer to verify without relying only on a Codex final report.

The gate is process governance only. It does not implement trading behavior, change strategy status, alter readiness semantics, add fixtures, call endpoints, or modify runtime code.

## Why This Gate Exists

This gate exists because Codex-local evidence can diverge from GitHub PR evidence:

- A Codex workspace `git fetch origin main` can fail, including with network or proxy errors such as `CONNECT tunnel failed, response 403`.
- Codex-local staged files can match the task's Expected Files Changed while the GitHub PR Files changed view still contains cumulative files from an unfresh branch.
- PR titles or descriptions can appear cumulative when prior unmerged work is present in the branch history.
- Therefore, reviewers must not rely on the Codex final report alone.
- The review source of truth is the GitHub PR Files changed view, step-specific handoff evidence, validation command results, and generated artifact clean checks.

## Review Source-of-Truth Order

Reviewers should use this order when evidence conflicts:

1. GitHub PR Files changed.
2. GitHub PR commit parent / branch freshness evidence.
3. Step-specific handoff file.
4. Codex final report.
5. Validation command output.
6. GitHub Checks / CI if available.
7. Generated JSON / fixture artifact clean check.

If GitHub PR Files changed and Codex-local claims disagree, GitHub is treated as the stronger source of truth until the discrepancy is explained and corrected.

## Required PR Review Evidence

Every Codex PR handoff should include the following evidence, or explicitly state why an item is unavailable:

- PR number.
- Branch name.
- Base branch.
- Commit hash.
- Commit parent hash, when available.
- Whether `git fetch origin main` succeeded.
- If fetch failed, the exact failure reason.
- Whether the branch was created from fresh `origin/main`.
- Expected Files Changed.
- Actual staged files from `git diff --cached --name-only`.
- A reviewer reminder to verify the GitHub PR Files changed count.
- Forbidden path diff result.
- Generated JSON check result.
- Test / validation commands run.
- GitHub Checks / CI availability.
- Behavior unchanged statement.
- `NO_TRADE_ONLY` compliance statement.
- Next recommended step.

For already-created PRs, Codex may not know the PR number during local validation. In that case the handoff must mark it as `TBD by GitHub after PR creation`, and the reviewer must fill or verify the GitHub-side value during review.

## Expected vs GitHub Files Changed Rule

Expected Files Changed and Codex staged files matching is necessary but not sufficient.

- The reviewer must also inspect GitHub PR Files changed.
- If GitHub PR Files changed is larger than Expected Files Changed, merge is on hold.
- If cumulative docs, previous handoffs, previous planning docs, or prior task files reappear unexpectedly, merge is on hold.
- If any file outside the task's allowed file list appears, merge is on hold.
- If forbidden paths appear, merge is on hold unless the task explicitly allowed them and the handoff explains why.
- If a previously merged docs-only or fixture-only PR caused no runtime risk, the follow-up action is to strengthen the gate and correct future branch hygiene rather than retroactively treating the old Codex-local report as authoritative.

The reviewer should resolve the mismatch by asking for a fresh branch, a narrowed cherry-pick, or a replacement PR whose GitHub Files changed exactly matches the task scope.

## Branch Freshness Rule

- When possible, Codex should work from a branch created from fresh `origin/main`.
- If `git fetch origin main` succeeds, Codex should record the fetch result and the base commit used.
- If fetch fails, Codex must record the exact failure in the handoff.
- A PR created after fetch failure requires stricter reviewer inspection of the GitHub commit parent, branch history, and cumulative diff.
- If fetch failure repeats, the user should prefer a user-local fresh branch, GitHub web review, or a reviewer-created clean branch as the merge basis.
- Missing local freshness evidence is not a reason to skip review; it is a reason to make GitHub PR Files changed and commit-parent evidence decisive.

## Merge-before-review Rule

- Codex may create a PR, but it must not merge it before reviewer confirmation.
- The user should provide the PR number or PR URL to the GPT designer or human reviewer for review.
- The reviewer must classify the PR as success, hold, or needs changes.
- The PR must not be merged before a success decision.
- Codex must not state that a PR is safe to merge when GPT designer review is still required.

## Test Evidence Standard

A statement such as “tests were run” is not sufficient.

- The handoff must record actual commands and the key output.
- Docs-only PRs should record git diff checks, forbidden path checks, generated JSON clean checks, and optional unittest results or a reason for not running them.
- Fixture PRs should record `python -m json.tool`, `json.load`, forbidden path checks, generated artifact clean checks, and unittest results when runnable.
- Parser or code PRs must record `python -m unittest discover -s tests` plus parser-specific or task-specific tests.
- If GitHub Checks / CI are unavailable, the handoff must state `independent CI unavailable` or equivalent.
- If any command fails due to environment limitations, the exact command, failure output, and impact must be recorded.

## Risk Tier Review Matrix

| PR type | Allowed risk | Required validation | Merge allowed before GPT review? | No-trade sensitivity | Extra reviewer checks |
|---|---:|---|---|---|---|
| docs-only planning | Low | Expected-vs-actual files, forbidden path check, generated JSON check, `git diff --check`; unittest optional if documented | No | Must preserve `NO_TRADE_ONLY`; no executable wording | Confirm docs do not imply active promotion, execution permission, or readiness change |
| docs governance / review gate | Low | Expected-vs-actual files, forbidden path check, generated JSON check, `git diff --check`; unittest optional but preferred | No | Must not weaken no-trade policy | Confirm merge/review policy is stricter, not looser |
| static fixture JSON only | Low to medium | `json.tool`, `json.load`, expected fixture list, forbidden path check, generated artifact clean check, unittest when runnable | No | Fixtures must not be described as signals | Confirm fixture values are deterministic fake data and not live payload copies |
| test code only | Medium | Unittest plus task-specific tests; forbidden path and generated artifact checks | No | Tests must not introduce live/private calls | Confirm tests are deterministic and read-only |
| parser/helper code | Medium | Unittest plus parser-specific tests and fixture tests | No | Parser output must remain context/readiness scoped as approved | Confirm missing fields and warnings do not become trade instructions |
| packet/candidate context | Medium | Unittest, packet schema checks, fixture coverage, handoff evidence | No | Context extensions must not auto-change readiness or execution | Confirm `recommended_default_decision` and active status are unchanged unless explicitly approved |
| readiness policy | High | Unittest, scenario coverage, policy handoff, explicit human review | No | Very sensitive; can change WATCH/REJECT/NEED_DATA meaning | Confirm no context-only signal changes readiness without approved policy |
| sampling collector | Medium to high | Unittest, dry-run/read-only smoke, generated artifact policy check | No | Sampling must remain evidence-only | Confirm generated JSON is not committed unless explicitly allowed |
| dashboard docs | Low | Docs diff, link/table review, forbidden path check | No | Dashboard must not be trading signal | Confirm Council handoff status is not execution permission |
| config/registry | High | Unittest, config diff review, rollback plan, explicit human review | No | Can affect active strategy or strategy exposure | Confirm no active promotion or policy change without approval |
| private API / execution / alert / Council auto-call | Forbidden in current project phase | N/A because currently out of scope | No | Prohibited | Reject unless the project policy is explicitly changed by human approval in a separate high-risk process |

## Required Handoff Template Addendum

Every future Codex handoff should include these sections or clear equivalents:

- PR Review Evidence.
- Branch Freshness Evidence.
- Expected vs Actual Files Changed.
- GitHub PR Files Changed Reviewer Checklist.
- Test Evidence.
- GitHub Checks / CI Status.
- Forbidden Path Check.
- Generated Artifact Check.
- Behavior Unchanged.
- No-Trade Compliance.
- Merge Recommendation.

## Reviewer Checklist

Before merge, the GPT designer or human reviewer should verify:

- PR open/merged status.
- PR Files changed count.
- Full files changed list.
- Whether unexpected cumulative docs or prior handoff/planning files are included.
- Whether `src/`, `tests/`, `config/`, `configs/`, `tools/`, or `data/` changed contrary to task scope.
- Whether generated JSON or sampling artifacts were created.
- Whether fixture JSON is valid when fixture files are included.
- Whether test commands and key outputs are recorded.
- Whether GitHub Checks / CI are available and green, or explicitly unavailable.
- Whether `NO_TRADE_ONLY` guardrails are preserved.
- Whether readiness, active promotion, execution, alerts, or private API surfaces changed.
- Whether the next recommended step matches the roadmap and remains scoped.

## Current Known Limitation

Codex environments may be unable to fetch GitHub due to network/proxy restrictions, including failures such as `CONNECT tunnel failed, response 403`. When that happens, Codex-local staged file checks can still be correct for the local branch, while the GitHub PR diff can appear cumulative because the branch was not created from fresh `origin/main`.

This limitation does not authorize merging from Codex-local evidence alone. It means reviewers must inspect GitHub commit parent and Files changed more strictly.

## Policy

- If GitHub Files changed differs from the Codex report, trust GitHub first.
- If a handoff claims Expected Files Changed matches but the GitHub PR diff differs, reviewer verification takes priority.
- GPT designer or human review before merge is the default for Codex PRs.
- `NO_TRADE_ONLY` and generated JSON guardrails remain mandatory for every PR.
- Private API, credentials, account access, orders, alerts, Council auto-call, and active promotion remain forbidden unless a future explicit human-approved policy changes the project phase.
