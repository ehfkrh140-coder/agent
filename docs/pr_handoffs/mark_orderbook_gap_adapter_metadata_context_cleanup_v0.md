# Mark-Orderbook Gap Adapter Metadata Context Cleanup v0

## 1. Purpose

Clean up stale PR-stage wording in Mark-Orderbook Gap Hunt adapter packet assumptions after Binance, Bybit, and OKX config/registry registration completed.

This PR is wording cleanup only. It does not change endpoint fetch behavior, parser logic, readiness logic, timestamp/freshness policy, `data_age_ms` handling, OKX `index_price` behavior, sampling, alert/notification behavior, Council behavior, active promotion, execution/private API behavior, config, registry, multi-venue composite behavior, or generic/base adapter extraction.

## 2. Baseline

- Binance, Bybit, and OKX Mark-Orderbook Gap Hunt runtime adapters exist.
- Binance, Bybit, and OKX adapter ids are registered in `configs/market_data.yaml` and `src/market_data/registry.py` as disabled, experimental, non-active, and `NO_TRADE_ONLY`.
- Binance has collect, sampling, and extended sampling evidence.
- Bybit has collect and 3-sample sampling evidence.
- OKX has direct adapter smoke and official `collect_market_data` smoke evidence.
- OKX official collect smoke succeeded with one observation, one candidate, `REJECT`, and `NO_TRADE_ONLY`.
- OKX watch items remain: `index_price=None`, negative `data_age_ms`, and stale adapter assumption wording from earlier standalone PR-stage context.

## 3. Cleanup scope

Updated only packet assumption / adapter-context wording in `src/market_data/adapters/mark_orderbook_gap_hunt.py` and related adapter tests.

Cleanup targets:

- Remove stale PR-stage assumptions from generated packet extensions:
  - `no config registration in this PR`
  - `no registry integration in this PR`
  - `no sampling integration in this PR`
- Preserve runtime-neutral no-trade assumptions:
  - public no-key endpoints only
  - analysis-only packet
  - no private API
  - no trading behavior
  - sampling integration is separate from packet generation
  - timestamp/data_age policy unchanged
  - adapter may be registered but remains disabled/experimental/non-active unless explicitly enabled in config

The adapter class docstrings were also made runtime-neutral so they no longer imply the adapters are intentionally unregistered in the current PR stage.

## 4. Wording before / after

Before:

```text
public no-key endpoints only
analysis-only packet
no config registration in this PR
no registry integration in this PR
no sampling integration in this PR
timestamp/data_age policy unchanged
```

After:

```text
public no-key endpoints only
analysis-only packet
adapter may be registered but remains disabled/experimental/non-active unless explicitly enabled in config
sampling integration is separate from packet generation
timestamp/data_age policy unchanged
no private API
no trading behavior
```

The cleanup applies to Binance, Bybit, and OKX Mark-Orderbook Gap Hunt packet extension assumptions.

## 5. Tests run

Codex checks for this cleanup PR:

- `git status` — checked repository state before changes.
- `git diff --name-only` — checked changed-file scope.
- `python -m unittest discover -s tests` — passed (`Ran 330 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_okx_adapter` — passed (`Ran 13 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed (`Ran 5 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` — passed; adapter listing still works.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed as a no-trade/credential scan across existing repository references.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as an active-strategy/no-trade scan across existing repository references.
- `git status --short` — checked final working tree state.
- `git diff --name-only HEAD~1..HEAD` — recorded after commit in the final response.

## 6. What this proves

- Mark-Orderbook Gap adapter packet assumptions no longer contain stale PR-stage registration wording.
- No-trade assumptions remain present in generated packet assumptions.
- Generated packet semantics are clearer after config/registry registration.
- No endpoint, parser, readiness, timestamp, index, or sampling behavior was changed.

## 7. What this does not prove

- It does not prove profitability.
- It does not prove sampling/persistence behavior.
- It does not resolve OKX `index_price` / reference semantics.
- It does not resolve timestamp freshness / clock-skew policy.
- It does not implement multi-venue composite.
- It does not implement generic/base adapter extraction.
- It does not add alert/Council/execution/private API behavior.

## 8. Changed files

- `src/market_data/adapters/mark_orderbook_gap_hunt.py`
- `tests/test_mark_orderbook_gap_hunt_okx_adapter.py`
- `tests/test_mark_orderbook_gap_hunt_bybit_adapter.py`
- `tests/test_mark_orderbook_gap_hunt_binance_adapter.py`
- `docs/pr_handoffs/mark_orderbook_gap_adapter_metadata_context_cleanup_v0.md`

No `configs/`, registry, parser, readiness, sampling, tools, generated data, Council, notification, storage, Gemini runtime/prompt, multi-venue composite, or generic/base adapter files are changed.

## 9. Risks

- Reviewers may still see historical stale wording in older handoff evidence files; this PR only changes future generated packet assumptions and current adapter docstrings/tests.
- OKX `index_price=None` remains unresolved and should not be silently reinterpreted.
- Negative `data_age_ms` remains unresolved and should not be silently clamped or reinterpreted.
- Future wording cleanup should remain separate from behavior changes.

## 10. Rollback plan

- Revert this PR.
- Restore the previous assumptions/docstring wording in `src/market_data/adapters/mark_orderbook_gap_hunt.py`.
- Revert the new adapter assumption assertions in Binance, Bybit, and OKX adapter tests.
- Remove this handoff file.
- Re-run `python -m unittest discover -s tests` if rollback verification is desired.

## 11. Human review required

Human review should first inspect:

1. `src/market_data/adapters/mark_orderbook_gap_hunt.py` to confirm only runtime-neutral assumption/docstring wording changed.
2. `tests/test_mark_orderbook_gap_hunt_okx_adapter.py` to confirm stale wording is rejected and no-trade wording remains.
3. `tests/test_mark_orderbook_gap_hunt_bybit_adapter.py` to confirm stale wording is rejected and no-trade wording remains.
4. `tests/test_mark_orderbook_gap_hunt_binance_adapter.py` to confirm stale wording is rejected and no-trade wording remains.
5. This handoff file to confirm behavior and policy watch items are explicitly out of scope.

## 12. No-trade compliance

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
- config adapter registration changes: no
- registry changes: no
- sampling implementation: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no
- OKX index/reference semantics change: no
- live network smoke as merge requirement: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no

## 13. Next recommended step

Keep OKX `index_price=None` and negative `data_age_ms` as separate watch items. Open a separate policy/planning task only if human review wants to address OKX index/reference semantics or shared timestamp/data_age behavior. Do not proceed from this wording cleanup into sampling, alerts, Council auto-call, active promotion, execution/private API, multi-venue composite, or generic/base adapter extraction.
