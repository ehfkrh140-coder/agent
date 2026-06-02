# Rollback Policy

## General policy
Prefer a revert PR over force push. Rollback must preserve auditability and make it easy to understand what changed and why it was reversed.

## Docs-only PR rollback
This is the docs-only PR rollback path.
- Revert affected docs/templates.
- Re-run documentation tests if present.
- Confirm links still point to valid docs.

## Config PR rollback
- Restore previous config values.
- Re-run unit tests and any config-specific smoke.
- Verify no credentials or private endpoints were introduced.

## Code PR rollback
- Revert the PR.
- Re-run `python -m unittest discover -s tests`.
- Re-run relevant read-only smoke commands.
- Confirm failure mode is resolved.

## Strategy registry/readiness rollback
- Restore previous registry/readiness files.
- Verify `active_strategy` remains `cross_exchange_spot_spread_v1` (review note: verify `active_strategy` remains `cross_exchange_spot_spread_v1`).
- Re-run strategy/readiness tests.
- Confirm experimental/future strategies were not promoted accidentally.

## Runtime/Gemini rollback
- Revert runtime/auth/Gemini changes.
- Run JSON contract smoke.
- Run Council dry-run after rollback.
- Require explicit human review before reattempting runtime/auth changes.

## Generated data files
Generated data files should not be treated as source rollback unless committed intentionally. Local probe/sampling outputs may be deleted if they are not part of the source PR.
