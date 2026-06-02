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
- high-risk classification when applicable.

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
