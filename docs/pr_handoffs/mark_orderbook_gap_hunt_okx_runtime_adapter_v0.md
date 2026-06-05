# Mark-Orderbook Gap Hunt OKX Runtime Adapter v0

## 1. Purpose

Add a standalone, public-read-only OKX BTC-USDT-SWAP Mark-Orderbook Gap Hunt runtime adapter class for `mark_orderbook_gap_hunt_v0` while preserving the experimental, non-active, analysis-only, `NO_TRADE_ONLY` boundary.

This PR is scoped to the OKX runtime adapter class, mocked OKX adapter tests, and this handoff evidence file. It does not register OKX in config/registry, does not wire `collect_market_data`, does not add sampling integration, does not add alerts/notifications, does not call Council, does not promote an active strategy, and does not add execution/private API behavior.

## 2. Baseline

- Binance Mark-Orderbook Gap Hunt has runtime/config/registry/collect/sampling evidence.
- Bybit Mark-Orderbook Gap Hunt has runtime/config/registry/collect/sampling evidence.
- Bybit user-local sampling smoke completed `samples_ok=3`, `samples_error=0`, `REJECT=3`, `NO_PERSISTENT_EDGE`, `council_recommended=false`, and `NO_TRADE_ONLY` preserved.
- Bybit negative `data_age_ms` remains a timestamp/data_age watch item only.
- The production parser already supports `parser_mode="okx_swap"`.
- OKX public source and instrument metadata planning/evidence already exist.
- OKX runtime adapter did not exist before this PR.
- OKX config/registry registration remains deferred.

## 3. Adapter scope

Implemented class:

- class: `OkxMarkOrderbookGapHuntAdapter`
- default adapter id: `live_okx_mark_orderbook_gap_btc_usdt_swap`
- adapter type: `okx_mark_orderbook_gap_hunt`
- venue id: `okx`
- venue name: `OKX`
- instrument: `BTC-USDT-SWAP`
- instType: `SWAP`
- asset: `BTC`
- quote: `USDT`
- strategy family: `mark_orderbook_gap_hunt`
- strategy id: `mark_orderbook_gap_hunt_v0`
- signal type: `mark_orderbook_gap_hunt`
- execution policy: `NO_TRADE_ONLY`
- experimental strategy: `true`
- non-active strategy: `true`
- no-trade-only: `true`

Out of scope in this PR:

- OKX config adapter registration;
- OKX registry integration;
- `collect_market_data` CLI wiring;
- sampling integration;
- alert/notification expansion;
- Council auto-call;
- active promotion;
- execution/private API;
- multi-venue composite;
- generic/base adapter extraction.

## 4. Public endpoint behavior

The adapter uses only public no-key OKX endpoints:

- `/api/v5/public/mark-price` with `instType=SWAP` and `instId=BTC-USDT-SWAP`;
- `/api/v5/market/books` with `instId=BTC-USDT-SWAP` and `sz=5`;
- `/api/v5/public/instruments` with `instType=SWAP` and `instId=BTC-USDT-SWAP`.

The adapter does not use the optional ticker endpoint in this PR because the existing `okx_swap` parser can normalize mark price, top-of-book, and instrument metadata from mark/books/instruments responses.

Non-zero OKX `code` responses raise `MarketDataAdapterError` with safe diagnostics. Missing/empty public payload data is passed to the existing parser as missing data so readiness can produce a `NEED_DATA` candidate according to existing parser/readiness style.

## 5. Parser/readiness integration

- Calls `parse_mark_orderbook_gap_snapshot` with `parser_mode="okx_swap"`.
- Passes public `mark_response`, `orderbook_response`, and `metadata_response`.
- Does not pass ticker response because the parser contract does not require it for OKX books-based top-of-book parsing.
- Calls `evaluate_mark_orderbook_gap_readiness` with explicit conservative adapter config parameters:
  - `fee_slippage_buffer_pct`;
  - `liquidity_pass`;
  - `require_freshness`;
  - `size_or_notional_resolved`;
  - `min_net_gap_pct`.
- Parser `OK` does not imply `WATCH`.
- `WATCH` remains analysis-only and `readiness_pass` remains `false`.
- `REJECT` remains normal no-edge behavior.

## 6. OpportunityPacket mapping

The adapter builds an analysis-only `OpportunityPacket` with:

- `strategy_family=mark_orderbook_gap_hunt`;
- `strategy_id=mark_orderbook_gap_hunt_v0`;
- `asset=BTC`;
- `quote=USDT`;
- `signal_type=mark_orderbook_gap_hunt`;
- one OKX observation for `BTC-USDT-SWAP`;
- one candidate of type `mark_orderbook_gap_observation`.

Observation mapping includes:

- `venue_id=okx`;
- `venue_name=OKX`;
- `market_symbol=BTC-USDT-SWAP`;
- `instrument_type=linear_swap` when parser metadata indicates linear `ctType`;
- `mark_price`;
- `bid` / `ask`;
- `bid_size` / `ask_size`;
- timestamp from OKX mark/books response;
- tick/lot size mapping through `tick` and `step`;
- OKX derivative metadata in observation extensions;
- data quality and venue health snapshots.

Candidate mapping includes:

- long/short/max observed gap metrics;
- estimated net gap;
- readiness status;
- recommended default decision;
- liquidity/freshness/comparability pass flags;
- required missing fields;
- warnings in extensions;
- assumptions that mark price is not executable, `WATCH` is analysis-only, no private API is used, and no trading behavior exists.

## 7. Diagnostics

Each public fetch records safe diagnostics with:

- endpoint;
- params;
- parser stage;
- HTTP status when available;
- OKX `code` / `msg` when available;
- safe response preview;
- elapsed milliseconds when available;
- URL when available.

Diagnostics deliberately exclude credentials, auth/private headers, account identifiers, balance data, order data, position data, withdrawal/deposit/transfer data, and execution instructions.

## 8. Timestamp/data_age note

This PR does not change timestamp/freshness policy.

- It does not clamp negative `data_age_ms`.
- It does not reinterpret `data_age_ms`.
- It does not change parser/readiness/freshness logic.
- OKX mocked tests use existing parser timestamp behavior only.
- Any OKX/Binance/Bybit timestamp differences remain future input for `Market Data Timestamp Freshness / Clock Skew Policy v0` or `Mark-Orderbook Gap Hunt Timestamp Alignment Policy v0`.

## 9. Commonization notes

This PR intentionally does not extract a base adapter.

The OKX adapter duplicates some safe structure already present in Binance/Bybit adapters:

- injected HTTP client seam;
- public GET diagnostic capture;
- parser/readiness delegation;
- analysis-only `OpportunityPacket` mapping;
- no-trade adapter metadata;
- no config/registry/sampling assumptions.

Future base adapter extraction should be considered only after OKX runtime behavior is reviewed alongside Binance and Bybit, and after config/registry/live evidence clarifies which venue-specific differences should remain isolated.

## 10. Tests run

Codex checks for this PR:

- `git status` — checked repository state before changes.
- `git diff --name-only` — checked changed-file scope before staging.
- `python -m unittest discover -s tests` — passed (`Ran 328 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_okx_adapter` — passed (`Ran 11 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_sampling` — passed (`Ran 6 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_bybit_adapter` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_binance_adapter` — passed (`Ran 9 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_parser` — passed (`Ran 8 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_readiness` — passed (`Ran 12 tests`, `OK`).
- `python -m unittest tests.test_mark_orderbook_gap_hunt_sampling` — passed (`Ran 5 tests`, `OK`).
- `python tools/collect_market_data.py --list-adapters` — passed and did not list an OKX Mark-Orderbook Gap adapter id.
- `rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md` — completed as a no-trade/credential scan across existing repository references.
- `rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md` — completed as an active-strategy/no-trade scan across existing repository references.
- `git status --short` — checked final working tree state.
- `git diff --name-only HEAD~1..HEAD` — to be recorded after commit in the final response.

## 11. What this proves

- Standalone OKX public-read-only Mark-Orderbook Gap Hunt adapter class exists.
- Adapter can consume mocked OKX public mark/books/instruments responses.
- Adapter reuses existing parser/readiness logic.
- Adapter can build an analysis-only `OpportunityPacket`.
- Diagnostics are safe and public-only.
- `NO_TRADE_ONLY` boundary is preserved.
- OKX is not registered in config/registry in this PR.

## 12. What this does not prove

- It does not prove live OKX endpoint reachability.
- It does not prove OKX config/registry registration.
- It does not prove `collect_market_data` execution.
- It does not prove sampling integration.
- It does not prove profitability or persistent edge.
- It does not justify alert/Council auto-call/active promotion/execution/private API.
- It does not implement multi-venue composite.
- It does not implement generic/base adapter extraction.
- It does not resolve timestamp freshness / clock-skew policy.

## 13. Changed files

- `src/market_data/adapters/mark_orderbook_gap_hunt.py`
- `tests/test_mark_orderbook_gap_hunt_okx_adapter.py`
- `docs/pr_handoffs/mark_orderbook_gap_hunt_okx_runtime_adapter_v0.md`

No config, registry, tools, sampling, parser, readiness, Council, notification, storage, generated packet, generated sampling, OKX registration, multi-venue composite, or generic/base adapter files are changed.

## 14. Risks

- OKX live endpoint behavior is not proven by this mocked-first PR.
- OKX config/registry and official collect path are intentionally deferred.
- Some packet-building structure duplicates Binance/Bybit adapter code until future base extraction is reviewed.
- Timestamp/clock-skew policy remains unresolved and must not be inferred from this adapter implementation alone.

## 15. Rollback plan

- Revert this PR.
- Remove `OkxMarkOrderbookGapHuntAdapter` from `src/market_data/adapters/mark_orderbook_gap_hunt.py`.
- Remove `tests/test_mark_orderbook_gap_hunt_okx_adapter.py`.
- Remove this handoff file.
- Re-run `python -m unittest discover -s tests` and targeted Mark-Orderbook Gap adapter/parser/readiness tests.
- No generated artifacts require cleanup because none are committed.

## 16. Human review required

Human review should first inspect:

1. `src/market_data/adapters/mark_orderbook_gap_hunt.py` to confirm OKX fetch paths are public-only, diagnostics are safe, parser/readiness are reused, and no Binance/Bybit behavior changed.
2. `tests/test_mark_orderbook_gap_hunt_okx_adapter.py` to confirm mocked-only coverage, no env/network access with injected client, safe diagnostics, and no config/registry registration.
3. This handoff file for scope, no-trade compliance, risks, rollback, timestamp/data_age guard, and commonization deferral.

## 17. No-trade compliance

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
- OKX config adapter registration: no
- OKX registry integration: no
- sampling implementation: no
- live network smoke as merge requirement: no
- multi-venue composite implementation: no
- generic/base adapter extraction: no
- parser/readiness/timestamp/freshness logic changes: no
- data_age_ms clamp or reinterpretation: no

## 18. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt OKX Config/Registry Planning v0` PR before registering the OKX adapter. After any future registration PR, record user-local OKX `collect_market_data` evidence separately and keep generated packet JSON out of git.
