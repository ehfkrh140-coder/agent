# PR Handoff Evidence Files

`docs/pr_handoffs/` stores task-specific evidence files that reviewers can inspect when a GitHub PR title/body is too generic or cannot carry the full review record. These files are operational evidence, not implementation code.

## When a handoff file is required
Every non-trivial Codex PR must include either a correctly filled GitHub PR template body or a task-specific handoff evidence file under this directory. Because Codex-generated GitHub PR bodies may be generic, a handoff evidence file is required for PRs that touch any of the following areas:

- probe
- adapter
- packet-builder
- readiness
- scenario
- sampling-alert
- runtime/LLM
- strategy registry changes

Docs-only PRs that only update governance docs may use the PR template alone, but a handoff evidence file is still recommended when the reviewer would benefit from a durable evidence record.

## File naming
Use a stable task slug:

```text
docs/pr_handoffs/<task_slug>.md
```

Examples:

```text
docs/pr_handoffs/tether_cross_market_experimental_scaffolding_v0.md
docs/pr_handoffs/bithumb_usdt_krw_recheck_v0.md
```

## Review usage
Reviewers should compare the handoff file against:

- the changed-file list;
- the PR template/body;
- test output;
- no-trade compliance statements;
- rollback instructions;
- human-review-required items.

A handoff file does not replace code review for high-risk changes, but it gives the reviewer a reliable starting point when the GitHub PR body is generic.
