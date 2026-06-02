# Codex Task Template

## Task name
Short, specific name for the task card.

## Goal
What the task should accomplish and why.

## Current state
Relevant merged features, assumptions, and known limitations.

## Allowed files
List exact files or directories Codex may edit.

## Forbidden files
List exact files or directories Codex must not edit.

## Implementation requirements
Concrete implementation details, data contracts, edge cases, and compatibility requirements.

## Tests
Required unit tests and commands, usually including:

```bash
python -m unittest discover -s tests
```

## Manual smoke
Optional read-only manual commands. State if live network access is expected or not.

## Success criteria
Observable outcomes that prove the task is complete.

## Non-goals
Explicitly list what must not be implemented in this task, including trading, private endpoints, account/balance access, orders, withdrawals, transfers, auto-trading, and unrelated strategy expansion unless the task specifically permits them.
