# Repository Guardrails for Codex

## Workflow
- Keep every change small and scoped to a single task-card style PR.
- Before changing files, check `git status --short --branch` and the current HEAD short SHA.
- Do not run `git fetch origin main`; this workspace may not have an `origin` remote.
- Do not report a missing `origin` remote as a failure in Summary or Testing.
- Respect the user-provided allowed/forbidden file list for the current task. Do not edit files outside the permitted scope.
- If a task is documentation-only, do not modify `src/`, `tools/`, `prompts/`, or `configs/` unless explicitly allowed.

## Strategy and safety scope
- The active strategy is `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap` is experimental/disabled and must not be treated as the active strategy.
- Follow the no-trade policy in `docs/no_trade_policy.md` for every task.
- Public read-only market data is allowed when the task explicitly permits market-data work.
- API keys, secrets, auth tokens, private endpoints, account/balance lookup, order placement, withdrawal, transfer, and auto-trading are forbidden.
- Council outputs are analysis only. They must not be treated as execution instructions.

## Testing and PR notes
- After changes, run `python -m unittest discover -s tests` unless the task explicitly says otherwise.
- If a test or check cannot run, record the exact command and the reason.
- PR summaries should clearly list changed files/areas and test results.
- Keep manual smoke tests read-only and avoid live network calls unless the task explicitly requests them.

## PR trust evidence
- Every Codex PR must fill `.github/pull_request_template.md` and include purpose, files changed, impact, tests, risks, rollback, and no-trade compliance.
- PR summaries must provide rollback/no-trade evidence, not only a code summary.
- If a task is high-risk, Codex must mark it high-risk in the summary and must not claim it is safe-to-merge without explicit human review.
- High-risk areas include runtime/auth/Gemini changes, prompts, `configs/strategy_current.yaml`, active strategy changes, strategy promotion, risk policy changes, and any execution/private API surface.
