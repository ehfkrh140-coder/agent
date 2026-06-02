# PR Review Policy

## Purpose
This policy helps determine whether a PR can be trusted without reading every line. The reviewer should be able to inspect the PR template, changed-file list, tests, risk class, and rollback plan to decide where deep review is needed.

## General rules
- PRs must be small and scoped to one task-card style change.
- Every PR must include purpose, affected files, tests, risks, and rollback.
- Every PR must state whether it touched `src`, `tools`, `prompts`, `configs`, `configs/strategy_current.yaml`, private API, or no-trade boundaries.
- Any PR touching runtime/auth/prompts/strategy_current/private API is high-risk.
- No PR may claim safety solely because Codex generated it; it must provide evidence.

## Review classification
Reviewers should classify each PR as one or more of:

| Class | Examples | Expected review depth |
|---|---|---|
| docs-only | docs, README, templates, policies | Check scope, links, consistency, and no accidental code/config changes. |
| config-only | YAML/TOML settings, registry metadata | Verify no active strategy change, no credentials, and config tests/smoke. |
| test-only | unit tests, fixtures used only by tests | Verify tests are meaningful and do not hide failures or add network/private behavior. |
| probe | read-only public probe tooling/config | Verify no adapter/persistence/execution path, no private headers, mocked tests. |
| adapter | public market-data adapters | Verify public endpoints only, no keys/private endpoints, mocked tests, failure handling. |
| readiness | strategy readiness logic | Verify expected decisions, no active handoff change unless approved, regression tests. |
| strategy/scenario | registry, scenario JSON, strategy docs | Verify status, active strategy unchanged, expected_behavior kept out of agent context. |
| runtime/LLM | Gemini CLI, auth, prompts, agent runtime | High-risk: require manual smoke, JSON contract checks, and explicit human review. |
| execution/private API | order, balance, account, transfer, private endpoint | Forbidden in current project phase; do not merge. |

## High-risk signals
Treat a PR as high-risk if it touches any of:
- `configs/strategy_current.yaml`
- `src/llm/*`, auth/runtime code, or Gemini CLI invocation
- `prompts/*`
- strategy promotion or active strategy status
- private API, API key, account/balance, order, transfer, withdrawal, deposit, bank/fiat flow
- Council automatic call or Council decision-to-trade conversion

High-risk PRs require explicit human approval and must not be described as safe-to-merge by Codex alone.
