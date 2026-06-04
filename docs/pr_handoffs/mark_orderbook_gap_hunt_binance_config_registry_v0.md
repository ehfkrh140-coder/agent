# Mark-Orderbook Gap Hunt Binance Adapter Config/Registry v0 Handoff

## 1. Purpose

Register the existing `BinanceMarkOrderbookGapHuntAdapter` as the single experimental/non-active/`NO_TRADE_ONLY` adapter id `live_binance_mark_orderbook_gap_btcusdt`.

This PR is intentionally small: config entry plus registry mapping plus tests/handoff evidence. It does not add sampling, alert/notification, Council auto-call, active strategy promotion, execution/private API, Bybit/OKX registration, multi-venue composite, generated packet JSON, generated sampling JSON, or live network smoke as a merge requirement.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains experimental / non-active / `NO_TRADE_ONLY`.
- `BinanceMarkOrderbookGapHuntAdapter` already existed and had mocked unit coverage.
- User-local direct adapter smoke already succeeded from normal network and preserved `NO_TRADE_ONLY` boundaries.
- Config/registry planning already documented the proposed entry and mapping.
- Before this PR, the adapter id was not present in `configs/market_data.yaml` and adapter type was not mapped in `src/market_data/registry.py`.

## 3. Config changes

Added one adapter entry to `configs/market_data.yaml`:

- adapter id: `live_binance_mark_orderbook_gap_btcusdt`
- type: `binance_mark_orderbook_gap_hunt`
- enabled: `false`
- experimental: `true`
- experimental_strategy: `true`
- non_active_strategy: `true`
- no_trade_only: `true`
- execution_policy: `NO_TRADE_ONLY`
- strategy_family: `mark_orderbook_gap_hunt`
- strategy_id: `mark_orderbook_gap_hunt_v0`
- base_url: `https://fapi.binance.com`
- symbol: `BTCUSDT`
- asset: `BTC`
- quote: `USDT`
- orderbook_limit: `5`
- timeout_seconds: `10`
- max_retries: `2`
- fee_slippage_buffer_pct: `0.20`
- min_net_gap_pct: `0`
- max_data_age_ms: `10000`
- require_freshness: `true`
- liquidity_pass: `true`
- size_or_notional_resolved: `true`

The thresholds are analysis/readiness placeholders only. They are not execution rules.

## 4. Registry changes

Added registry import and mapping:

- adapter type `binance_mark_orderbook_gap_hunt`
- maps to `BinanceMarkOrderbookGapHuntAdapter`

Registry constraints preserved:

- no active strategy change;
- no sampling auto-enable;
- no alert/notification behavior;
- no Council auto-call;
- no execution/private API;
- no Bybit/OKX registration;
- no multi-venue composite.

## 5. Adapter list / instantiation checks

Updated `tests/test_mark_orderbook_gap_hunt_binance_adapter.py` to verify:

- `live_binance_mark_orderbook_gap_btcusdt` appears in `list_adapters(load_market_data_config())`;
- config type is `binance_mark_orderbook_gap_hunt`;
- config keeps `enabled: false`;
- config keeps `NO_TRADE_ONLY`, `experimental_strategy: true`, `non_active_strategy: true`, and `no_trade_only: true`;
- `build_adapter("live_binance_mark_orderbook_gap_btcusdt", config)` returns a `BinanceMarkOrderbookGapHuntAdapter` instance.

`python tools/collect_market_data.py --list-adapters` was run and completed successfully; the adapter id is available through the existing list-adapter path.

## 6. Expected future user-local smoke

Future user-local smoke command after this registration:

```text
python tools/collect_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --output data/generated_packets/live_binance_mark_orderbook_gap_btcusdt.json
```

Expected successful packet characteristics:

- `strategy_family`: `mark_orderbook_gap_hunt`
- `strategy_id`: `mark_orderbook_gap_hunt_v0`
- `asset`: `BTC`
- `quote`: `USDT`
- `observations`: `1`
- `candidates`: `1`
- `execution_policy`: `NO_TRADE_ONLY`
- `no_trade_only`: `true`
- no `execution_allowed`
- no `council_auto_call`
- no `alert_trigger`

Generated output JSON must be deleted after smoke and must not be committed.

Codex did not require live network smoke for merge. If Codex workspace live network fails due to tunnel `403`, treat that as an environment limitation and use user-local smoke evidence in a separate PR.

## 7. Tests run

### Git status

```text
git status
```

Result: passed before staging; branch `mark-orderbook-gap-binance-config-registry-v0` showed only allowed changes to config, registry, adapter test, and handoff.

### Git diff name check

```text
git diff --name-only
```

Result: passed before staging; output contained `configs/market_data.yaml`, `src/market_data/registry.py`, and `tests/test_mark_orderbook_gap_hunt_binance_adapter.py` as tracked changes plus the new handoff file.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only `configs/market_data.yaml`, `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_config_registry_v0.md`, `src/market_data/registry.py`, and `tests/test_mark_orderbook_gap_hunt_binance_adapter.py`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed (`Ran 293 tests in 12.038s`, `OK`).

### Binance adapter test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter
```

Result: passed (`Ran 8 tests in 0.042s`, `OK`).

### Production parser test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_parser
```

Result: passed (`Ran 8 tests in 0.007s`, `OK`).

### Readiness helper test

```text
python -m unittest tests.test_mark_orderbook_gap_hunt_readiness
```

Result: passed (`Ran 12 tests in 0.007s`, `OK`).

### Adapter list check

```text
python tools/collect_market_data.py --list-adapters
```

Result: passed; `live_binance_mark_orderbook_gap_btcusdt` appeared in the adapter list output.

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed (`exit=0`, `2215` matching lines from existing policy/docs/test references plus this PR's explicit no-trade config/handoff entries); no credential/private/account/balance/position/order/transfer/execution/sampling/alert/Council surface was added.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed (`exit=0`, `1562` matching lines from existing strategy/no-trade references plus this PR's `mark_orderbook_gap_hunt` config/registry references); active strategy remains `cross_exchange_spot_spread_v1` and this adapter remains disabled/experimental/non-active/`NO_TRADE_ONLY`.

### Final status check

```text
git status --short
```

Result: passed after commit; working tree was clean on `mark-orderbook-gap-binance-config-registry-v0` and no generated artifacts were present.

## 8. What this proves

- The single Binance adapter id is present in config.
- The adapter type maps to `BinanceMarkOrderbookGapHuntAdapter` in registry.
- Existing list-adapter flow can see the adapter id.
- Unit tests can instantiate the adapter through registry/config without network.
- The registration remains experimental, non-active, disabled, and `NO_TRADE_ONLY`.

## 9. What this does not prove

- It does not prove live Binance endpoint availability in Codex workspace.
- It does not run live network smoke as a merge requirement.
- It does not prove generated packet contents from `tools/collect_market_data.py` in user-local environment.
- It does not implement sampling.
- It does not implement alert/notification.
- It does not implement Council auto-call.
- It does not promote the strategy to active.
- It does not implement execution/private API.
- It does not register Bybit or OKX.
- It does not implement multi-venue composite.

## 10. Changed files

- Updated: `configs/market_data.yaml`.
- Updated: `src/market_data/registry.py`.
- Updated: `tests/test_mark_orderbook_gap_hunt_binance_adapter.py`.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_config_registry_v0.md`.
- No `tools/**` changes.
- No `src/council/**`, `src/notifications/**`, or `src/storage/**` changes.
- No generated packet/sampling/Council-session JSON changes.

## 11. Risks

- The adapter is now visible via list-adapters, so reviewers should ensure the `enabled: false`, experimental, non-active, and `NO_TRADE_ONLY` fields remain clear.
- Future user-local smoke can generate packet JSON; that artifact must be deleted and not committed.
- `WATCH` remains analysis-only and could be misread as actionable if no-trade boundaries are ignored.
- Conservative thresholds may produce `REJECT`; that can be normal no-edge behavior.

## 12. Rollback plan

- Remove `live_binance_mark_orderbook_gap_btcusdt` from `configs/market_data.yaml`.
- Remove the `binance_mark_orderbook_gap_hunt` registry import/mapping from `src/market_data/registry.py`.
- Revert the registration assertions in `tests/test_mark_orderbook_gap_hunt_binance_adapter.py`.
- Revert this handoff file.
- Re-run `python -m unittest discover -s tests`.
- Confirm `python tools/collect_market_data.py --list-adapters` no longer shows the adapter id.
- Confirm no generated packet/sampling/Council-session JSON is committed.

## 13. Human review required

Reviewers should inspect:

1. `configs/market_data.yaml`
2. `src/market_data/registry.py`
3. `tests/test_mark_orderbook_gap_hunt_binance_adapter.py`
4. `docs/pr_handoffs/mark_orderbook_gap_hunt_binance_config_registry_v0.md`

Review focus:

- single-adapter scope only;
- `enabled: false` / experimental / non-active / `NO_TRADE_ONLY` fields;
- registry mapping only, not active strategy change;
- no sampling/alert/Council/execution additions;
- generated artifact non-commit handling;
- user-local smoke as a follow-up, not merge requirement.

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
- sampling implementation: no
- live network smoke as merge requirement: no
- Bybit/OKX adapter registration: no
- multi-venue composite implementation: no

## 15. Next recommended step

After human review, run user-local normal-network smoke in a separate evidence PR using:

```text
python tools/collect_market_data.py --adapter live_binance_mark_orderbook_gap_btcusdt --output data/generated_packets/live_binance_mark_orderbook_gap_btcusdt.json
```

Delete the generated packet JSON after recording safe summary evidence. Keep follow-up work separate from sampling, alert/notification, Council auto-call, active promotion, and execution/private API.
