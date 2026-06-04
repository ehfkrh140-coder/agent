# Mark-Orderbook Gap Hunt Bybit Adapter Config/Registry v0

## 1. Purpose

Register the existing `BybitMarkOrderbookGapHuntAdapter` as a disabled, experimental, non-active, `NO_TRADE_ONLY` market-data adapter so the standard `tools/collect_market_data.py` registry/config lookup path can instantiate it by adapter id in a future user-local collect smoke.

This PR is intentionally small: it registers only `live_bybit_mark_orderbook_gap_btcusdt` and does not add sampling integration, alerts, notifications, Council auto-call, active promotion, execution, private API, OKX registration, multi-venue composite behavior, or generic/base adapter extraction.

## 2. Baseline

- `BybitMarkOrderbookGapHuntAdapter` already exists and uses public Bybit V5 linear BTCUSDT ticker, orderbook, and instruments-info data.
- The adapter already calls the shared `parse_mark_orderbook_gap_snapshot` parser with `parser_mode="bybit_linear"` and the shared `evaluate_mark_orderbook_gap_readiness` helper.
- Mocked Bybit adapter unit tests already cover packet creation, parser/readiness integration, safe diagnostics, and no-trade boundaries.
- User-local direct adapter smoke already succeeded and produced one analysis-only observation and one candidate.
- Before this PR, the adapter class was not exposed through `configs/market_data.yaml` or `src/market_data/registry.py`, so the official `collect_market_data` adapter-id path could not build it.

## 3. Config changes

Added one disabled adapter entry under `configs/market_data.yaml`:

```yaml
live_bybit_mark_orderbook_gap_btcusdt:
  type: bybit_mark_orderbook_gap_hunt
  enabled: false
  experimental: true
  strategy_family: mark_orderbook_gap_hunt
  strategy_id: mark_orderbook_gap_hunt_v0
  base_url: https://api.bybit.com
  category: linear
  symbol: BTCUSDT
  asset: BTC
  quote: USDT
  orderbook_limit: 5
  timeout_seconds: 10
  max_retries: 2
  user_agent: agent-council-market-data-v1
  fee_slippage_buffer_pct: "0.20"
  min_net_gap_pct: "0"
  max_data_age_ms: 10000
  require_freshness: true
  liquidity_pass: true
  size_or_notional_resolved: true
  execution_policy: NO_TRADE_ONLY
  experimental_strategy: true
  non_active_strategy: true
  no_trade_only: true
```

The entry is public read-only, disabled by default, experimental, non-active, and explicitly `NO_TRADE_ONLY`.

## 4. Registry changes

- Imported `BybitMarkOrderbookGapHuntAdapter` alongside the existing Binance Mark-Orderbook Gap adapter.
- Mapped adapter type `bybit_mark_orderbook_gap_hunt` to `BybitMarkOrderbookGapHuntAdapter` in `build_adapter`.
- Preserved existing Binance adapter mapping.
- Did not change active strategy, sampling behavior, alerts, notifications, Council behavior, execution behavior, OKX behavior, multi-venue composite behavior, or generic/base adapter structure.

## 5. Adapter list / instantiation checks

Expected registry/config behavior after this PR:

- `live_bybit_mark_orderbook_gap_btcusdt` appears in `list_adapters(load_market_data_config())`.
- The config type is `bybit_mark_orderbook_gap_hunt`.
- The config remains `enabled: false`, `experimental_strategy: true`, `non_active_strategy: true`, `no_trade_only: true`, and `execution_policy: NO_TRADE_ONLY`.
- `build_adapter("live_bybit_mark_orderbook_gap_btcusdt", config)` returns `BybitMarkOrderbookGapHuntAdapter`.
- Existing Binance registration remains `binance_mark_orderbook_gap_hunt` for `live_binance_mark_orderbook_gap_btcusdt`.
- Active strategy references remain `cross_exchange_spot_spread_v1`.

## 6. Expected future user-local smoke

Future user-local normal-network collect smoke command, to be run after this registration PR is reviewed and merged:

```bash
python tools/collect_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --output data/generated_packets/live_bybit_mark_orderbook_gap_btcusdt.json
```

Expected successful packet characteristics:

- `strategy_family: mark_orderbook_gap_hunt`
- `strategy_id: mark_orderbook_gap_hunt_v0`
- `asset: BTC`
- `quote: USDT`
- `observations: 1`
- `candidates: 1`
- `venue_id: bybit`
- `execution_policy: NO_TRADE_ONLY`
- `no_trade_only: true`
- no `execution_allowed`
- no `council_auto_call`
- no `alert_trigger`

The generated packet JSON is a local smoke artifact only. It must be deleted after inspection and must not be committed.

## 7. Tests run

Codex checks completed for this PR before commit:

- `git status` — showed only the scoped working-tree changes plus the new handoff file.
- `git diff --name-only` — showed the scoped modified files before staging.
- `python -m unittest discover -s tests` — passed (`Ran 311 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed (`Ran 5 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` — passed and listed `live_bybit_mark_orderbook_gap_btcusdt`.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed as a no-trade/credential scan across existing repository references.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as an active-strategy/no-trade scan across existing repository references.
- `git status --short` — showed only the scoped modified files plus this new handoff file before staging.
- `git diff --name-only HEAD~1..HEAD` — to be recorded after commit in the final response.

## 8. What this proves

- The existing Bybit Mark-Orderbook Gap Hunt adapter is now discoverable by adapter id in the market-data config list.
- The registry can instantiate `BybitMarkOrderbookGapHuntAdapter` from type `bybit_mark_orderbook_gap_hunt`.
- The Bybit registration is disabled, experimental, non-active, and `NO_TRADE_ONLY`.
- The standard `collect_market_data` adapter lookup path has the config/registry prerequisites needed for a future user-local live collect smoke.
- Existing Binance Mark-Orderbook Gap registration remains present.

## 9. What this does not prove

- It does not prove user-local Bybit `collect_market_data` live smoke success.
- It does not prove Bybit sampling integration.
- It does not prove profitability.
- It does not prove persistent edge.
- It does not justify alert or notification implementation.
- It does not justify Council auto-call.
- It does not justify active strategy promotion.
- It does not justify execution or private API.
- It does not register OKX.
- It does not prove or implement multi-venue composite behavior.
- It does not extract a generic/base adapter.

## 10. Changed files

- `configs/market_data.yaml`
- `src/market_data/registry.py`
- `tests/test_mark_orderbook_gap_hunt_bybit_adapter.py`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_bybit_config_registry_v0.md`

## 11. Risks

- Config/registry registration makes the adapter selectable by id, so reviewers should confirm it remains disabled, experimental, non-active, and `NO_TRADE_ONLY`.
- User-local public endpoint behavior can vary by network, exchange availability, or rate limiting; live smoke evidence is intentionally deferred to a separate evidence PR.
- This PR does not add sampling, so sampling behavior for the Bybit adapter remains unproven.

## 12. Rollback plan

- Revert this PR.
- Confirm `live_bybit_mark_orderbook_gap_btcusdt` is removed from `configs/market_data.yaml`.
- Confirm `bybit_mark_orderbook_gap_hunt` is no longer mapped in `src/market_data/registry.py`.
- Re-run `python -m unittest discover -s tests` and `python tools/collect_market_data.py --list-adapters`.
- Confirm active strategy references remain `cross_exchange_spot_spread_v1`.

## 13. Human review required

Human review should first inspect:

1. `configs/market_data.yaml` — confirm disabled/experimental/non-active/NO_TRADE_ONLY config and no private/auth fields.
2. `src/market_data/registry.py` — confirm only the Bybit adapter type mapping was added and no active behavior changed.
3. `tests/test_mark_orderbook_gap_hunt_bybit_adapter.py` — confirm registration assertions cover config, instantiation, no-trade fields, and active-strategy guard.
4. This handoff file — confirm scope, risks, rollback, and deferred live smoke are accurate.

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
- OKX adapter registration: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no

## 15. Next recommended step

After human review and merge, run a separate user-local evidence task: `Mark-Orderbook Gap Hunt User-Local Bybit Collect Market Data Smoke Evidence v0`, using the documented `tools/collect_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt` command and excluding generated packet JSON from git.
