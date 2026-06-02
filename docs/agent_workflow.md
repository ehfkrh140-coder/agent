# Agent Workflow

## Roles
- User: product owner and final approver.
- Codex: implementation worker that makes scoped changes and provides evidence.
- GPT/reviewer: design and risk reviewer that checks intent, evidence, and risk class.

## Evidence over code volume
Codex must provide evidence, not just code. Evidence includes:
- purpose;
- files changed;
- impact scope;
- exact tests and smoke commands;
- risks;
- rollback method;
- no-trade compliance;
- high-risk classification when applicable;
- a `docs/pr_handoffs/<task_slug>.md` file when the task type requires durable handoff evidence.

User should not need to read every line of code to decide whether a PR deserves deeper review. The reviewer checks PR evidence, risk class, and merge gate status, then chooses which files require line-by-line inspection.

## Human final approval required
Human final approval is required for:
- strategy changes;
- active promotion;
- risk policy changes;
- runtime/auth changes;
- any execution/private API area;
- merge approval.

Codex must not claim a high-risk PR is safe-to-merge without explicit human review.


## Handoff evidence files
When a task touches probe, adapter, packet-builder, readiness, scenario, sampling-alert, runtime/LLM, or strategy registry areas, Codex should create a task-specific handoff evidence file under `docs/pr_handoffs/`. This file helps the user and reviewer trust the change even if the GitHub PR body is generic.
