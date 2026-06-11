# Merge Gate

## Required merge conditions
A PR may be considered for merge only when all applicable conditions are met:
- Tests pass, including `python -m unittest discover -s tests` unless explicitly waived with a reason.
- Existing behavior is preserved or intentional behavior changes are clearly documented.
- Docs are updated when behavior, workflow, strategy policy, or operational process changes.
- Impact scope is declared in the PR template.
- Failure handling exists for new code paths or the PR is docs-only.
- No unrelated files changed.
- No no-trade violation.
- Rollback method is documented.
- User approval is present for high-risk categories.

## Forbidden merge conditions
Do not merge if any of the following are true:
- Unexplained refactor.
- Unrelated file changes.
- Private API/key/order/balance/transfer additions.
- Active strategy change without explicit user approval.
- Runtime/auth change without explicit manual smoke.
- Missing tests without an explicit reason.
- Missing rollback plan.
- PR template not filled with purpose, files, impact, tests, risks, rollback, and no-trade compliance.
- PR title/body is generic and no `docs/pr_handoffs/` evidence file exists.
- Changed files include strategy/config/code but no impact scope or rollback plan exists.
- No-trade compliance is not explicitly stated.

## Codex PR Review Evidence Gate
Before merging a Codex-authored PR, reviewers must apply `docs/codex_pr_review_gate.md` as a merge gate checklist.

- Compare the task's Expected Files Changed against GitHub PR Files changed, not only Codex-local staged files.
- If GitHub PR Files changed is larger than Expected Files Changed, includes cumulative prior docs/handoffs, or includes files outside the allowed scope, hold the merge.
- If GitHub Checks / CI are unavailable, inspect the task handoff validation evidence and exact command output before considering merge.
- If the handoff records a Codex `git fetch origin main` failure or missing branch freshness evidence, verify the GitHub commit parent and cumulative diff more strictly.
- Keep `NO_TRADE_ONLY`, private API/order/alert prohibitions, and generated JSON clean checks as mandatory merge conditions for every PR.
- Codex may create PRs, but GPT designer or human reviewer approval is required before merge.

## Human approval required
Human approval is required for:
- strategy changes that can affect active/future/experimental status;
- active promotion;
- risk/no-trade policy changes;
- runtime/auth/Gemini changes;
- any execution/private API area;
- final merge approval.
