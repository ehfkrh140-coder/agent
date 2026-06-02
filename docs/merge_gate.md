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

## Human approval required
Human approval is required for:
- strategy changes that can affect active/future/experimental status;
- active promotion;
- risk/no-trade policy changes;
- runtime/auth/Gemini changes;
- any execution/private API area;
- final merge approval.
