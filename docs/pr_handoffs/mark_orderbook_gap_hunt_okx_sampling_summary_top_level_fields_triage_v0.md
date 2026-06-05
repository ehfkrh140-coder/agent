# Mark-Orderbook Gap Hunt OKX Sampling Summary Top-Level Fields Triage v0

## 1. Purpose

Triage the user-local OKX sampling output where sample-level records were successful but aggregate summary fields appeared as `None` when inspected as top-level fields.

This PR determines whether the fields were missing, nested elsewhere, not populated by `run_market_sampling`, lost during serialization, or only missing from the user inspection command. It keeps live user-local success evidence as a follow-up and does not record the latest user-local run as full OKX sampling smoke success evidence.

## 2. Baseline

- `live_okx_mark_orderbook_gap_btc_usdt_swap` is registered in config/registry.
- OKX direct adapter smoke succeeded.
- OKX official `collect_market_data` smoke succeeded.
- OKX sampling baseline v0 added mocked OKX sampling coverage and watch fields for `index_price=None`, negative `data_age_ms`, and stale assumption wording.
- User-local OKX sampling command produced three sample-level `ok` records with `REJECT`, `okx`, `BTC-USDT-SWAP`, `parser_normalized_status=OK`, positive `data_age_ms`, `index_price=None`, `index_price_null_observed=True`, no stale wording, `NO_TRADE_ONLY`, and no execution/Council/alert fields.

## 3. User-local symptom

User-local command:

```bash
python tools/sample_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_okx_sampling_summary.json
```

Observed symptom:

- Top-level lookups for aggregate fields such as `samples_ok`, `samples_error`, `candidate_seen_count`, `readiness_status_counts`, `persistence_status`, `recommended_default_decision`, `index_price_null_count`, and stale wording fields returned `None`.
- Sample-level fields were populated correctly for all three samples.

## 4. Root cause

The aggregate sampling fields are not top-level `market_sampling_v1` envelope fields. They are nested under `payload["summary"]`.

`run_market_sampling` returns top-level envelope fields such as:

- `schema_version`
- `adapter_id`
- `created_at_utc`
- `samples_requested`
- `interval_seconds`
- `max_errors`
- `samples`
- `summary`
- Council handoff metadata

The aggregate fields named in the symptom are populated inside the nested `summary` object. Therefore `payload.get("samples_ok")` returns `None`, while `payload["summary"]["samples_ok"]` is the correct inspection path.

This indicates an inspection-path mismatch, not an OKX collection, adapter, parser, readiness, serialization, or sampling enrichment failure.

## 5. Fix or inspection-path clarification

No `src/market_data/sampling.py` fix was needed for this symptom because mocked tests confirm the fields are populated under `result["summary"]`.

Changes made:

- Added a mocked 3-sample OKX test that verifies summary fields under `result["summary"]`:
  - `samples_ok=3`
  - `samples_error=0`
  - `candidate_seen_count=3`
  - `readiness_status_counts={"REJECT": 3}`
  - `reject_count=3`
  - `positive_net_gap_count=0`
  - `persistence_status=NO_PERSISTENT_EDGE`
  - `recommended_default_decision=REJECT`
  - `council_recommended=False`
  - `index_price_null_count=3`
  - `index_price_null_observed=True`
  - `timestamp_data_age_watch_count=0` for positive `data_age_ms`
  - `negative_data_age_observed=False` for positive `data_age_ms`
  - `stale_assumption_wording_count=0`
  - `stale_assumption_wording_observed=False`
- The same test preserves sample-level assertions for `status=ok`, `readiness_status=REJECT`, `venue_id=okx`, `market_symbol=BTC-USDT-SWAP`, `parser_normalized_status=OK`, `no_trade_only=True`, and `execution_policy=NO_TRADE_ONLY`.
- Updated the OKX sampling plan with an inspection-path clarification: aggregate summary fields must be read from `payload["summary"]`, not top-level `payload`.

## 6. Tests run

- `git status` completed before edits to confirm branch/worktree state.
- `git diff --name-only` completed before commit to confirm only allowed files changed.
- `python -m unittest discover -s tests` passed (`Ran 339 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_okx_sampling` passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_okx_adapter` passed (`Ran 13 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_sampling` passed (`Ran 6 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` passed (`Ran 5 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` passed and listed `live_okx_mark_orderbook_gap_btc_usdt_swap`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` completed as an audit scan; matches are existing policy/test/doc references and no generated artifacts were introduced.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` completed as a strategy/no-trade audit scan.
- `git status --short` confirmed only allowed files were changed before staging/commit.

## 7. Expected follow-up user-local command

Future user-local evidence command remains:

```bash
python tools/sample_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap --samples 3 --interval 1 --output data/market_samples/mark_orderbook_gap_okx_sampling_summary.json
```

Correct inspection path:

```python
summary = payload["summary"]
summary["samples_ok"]
summary["samples_error"]
summary["candidate_seen_count"]
summary["readiness_status_counts"]
summary["persistence_status"]
summary["recommended_default_decision"]
summary["index_price_null_count"]
summary["index_price_null_observed"]
summary["timestamp_data_age_watch_count"]
summary["negative_data_age_observed"]
summary["stale_assumption_wording_count"]
summary["stale_assumption_wording_observed"]
```

Do not commit generated sampling JSON. User-local live sampling success evidence remains a separate follow-up after this triage.

## 8. What this proves

- The OKX sampling output schema stores aggregate fields under `summary`.
- A mocked 3-sample OKX sampling run populates the expected aggregate fields under `summary`.
- The sample-level OKX fields remain populated.
- `index_price=None` is counted as a watch item without changing OKX index/reference semantics.
- Positive `data_age_ms` does not trip the negative timestamp/data_age watch count.
- Stale assumption wording remains false for future-style mocked packet assumptions.
- `council_recommended` remains false.

## 9. What this does not prove

- It does not record full user-local OKX sampling smoke success evidence.
- It does not prove live OKX endpoint reliability.
- It does not prove profitability or persistent edge.
- It does not justify alert/notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution/private API.
- It does not resolve timestamp freshness / clock-skew policy.
- It does not resolve OKX index/reference semantics.
- It does not implement multi-venue composite or generic/base adapter extraction.

## 10. Changed files

- `tests/test_mark_orderbook_gap_hunt_okx_sampling.py`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_okx_sampling_summary_top_level_fields_triage_v0.md`
- `docs/sampling_plans/mark_orderbook_gap_hunt_okx_sampling_baseline_v0.md`

No `src/`, `configs/`, registry, adapter, parser, readiness, tools, generated packet/sampling data, Council, notification, storage, Gemini runtime/prompt, multi-venue composite, or generic/base adapter files are changed.

## 11. Risks

- A reviewer or user may still inspect top-level envelope fields directly; the corrected path is `payload["summary"]`.
- Future schema changes should preserve or explicitly migrate the `market_sampling_v1` envelope/summary contract.
- User-local live evidence still needs a separate follow-up run after reviewing this triage.

## 12. Rollback plan

- Revert this PR.
- Remove the added 3-sample OKX summary inspection-path test.
- Remove this triage handoff file.
- Revert the inspection-path clarification in `docs/sampling_plans/mark_orderbook_gap_hunt_okx_sampling_baseline_v0.md`.
- No code/config/registry/adapter/parser/readiness/tool/generated-data rollback is required.

## 13. Human review required

Human review should first inspect:

1. `tests/test_mark_orderbook_gap_hunt_okx_sampling.py` to confirm the mocked 3-sample OKX result asserts aggregate fields under `result["summary"]` and preserves sample-level fields.
2. `docs/sampling_plans/mark_orderbook_gap_hunt_okx_sampling_baseline_v0.md` to confirm the corrected inspection path.
3. This handoff file to confirm root cause, no-trade compliance, rollback, and follow-up user-local evidence separation.

## 14. No-trade compliance

- private API: no
- API key/secret/token: no
- env credential lookup: no
- auth/private headers: no
- account/balance lookup: no
- position lookup: no
- order/cancel: no
- withdrawal/deposit/transfer: no
- fiat/bank transfer: no
- auto-trading: no
- Council auto-call: no
- Council decision to trade conversion: no
- active strategy promotion: no
- alert expansion: no
- notification expansion: no
- generated packet JSON commit: no
- generated sampling JSON commit: no
- live network smoke as merge requirement: no
- config/registry changes: no
- adapter/parser/readiness logic changes: no
- timestamp/freshness policy changes: no
- data_age_ms clamp or reinterpretation: no
- OKX index/reference semantics change: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no

## 15. Next recommended step

After human review, rerun the user-local OKX sampling inspection using `payload["summary"]` for aggregate fields. If summary fields are populated there, open a separate user-local OKX sampling smoke evidence PR; if not, capture the exact JSON shape and open a targeted serialization/enrichment bugfix PR.
