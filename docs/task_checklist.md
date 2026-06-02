# Codex Task Checklist

## Before starting
- Task type:
- Allowed files:
- Forbidden files:
- Expected tests:
- Manual smoke needed?
- Rollback path:
- Human approval needed?
- Handoff file required?
- High-risk category? If yes, why:
- No-trade boundaries for this task:

## During work
- Keep changes scoped to allowed files.
- Do not modify active strategy unless explicitly allowed and approved.
- Do not add private API, credentials, account/balance lookup, orders, transfers, withdrawal/deposit, bank/fiat flow, auto-trading, or Council auto-call.
- Preserve existing behavior outside the task scope.

## After completing
- Files changed:
- Tests run with exact commands:
- Manual smoke run with exact commands or reason not needed:
- Risks:
- Rollback method:
- No-trade confirmation:
- Reviewer should inspect first:
- Create `docs/pr_handoffs/<task_slug>.md` when required:
- Handoff file path or reason PR template alone is enough:
- Human approval required before merge?
