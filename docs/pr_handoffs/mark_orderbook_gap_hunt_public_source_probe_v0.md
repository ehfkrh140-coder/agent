# Mark-Orderbook Gap Hunt Public Source Probe v0 Handoff

## 1. Purpose

Document public, no-key source candidates and response-shape expectations for `Mark-Orderbook Gap Hunt v0` without implementing runtime adapters, parsers, config registration, sampling, alerts, Council auto-calls, active promotion, execution, or live network smoke.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `Mark-Orderbook Gap Hunt v0` remains proposed / experimental-planning / inactive.
- Current project scope remains `NO_TRADE_ONLY`.
- The strategy card warns that mark price is not executable and must be compared against validated bid/ask, size, unit, notional, fee/slippage, latency, freshness, and venue health.
- Cross-strategy criteria require `NEED_DATA` when required fields, units, comparability, or freshness are unknown.

## 3. Probe scope

In scope:

- Document candidate public no-key endpoints for Binance USDⓈ-M Futures, Bybit Derivatives V5, and OKX derivatives.
- Record mark price, orderbook/top-of-book, symbol format, response fields, timestamp, size unit, and notional questions.
- Identify `NEED_DATA` items before runtime implementation.

Out of scope:

- runtime adapter implementation;
- parser implementation;
- config adapter registration;
- sampling implementation;
- alert/notification expansion;
- Council auto-call;
- active strategy promotion;
- execution/private API;
- live network smoke as a merge requirement.

## 4. Venue source matrix

| Venue | Mark endpoint candidate | Orderbook / bid-ask endpoint candidate | Public/no-key expectation | Symbol format | Fields to inspect | Remaining unit/notional question |
| --- | --- | --- | --- | --- | --- | --- |
| Binance USDⓈ-M Futures | `GET /fapi/v1/premiumIndex` | `GET /fapi/v1/depth` | Public market data, no key expected | uppercase futures symbol such as `BTCUSDT` | `markPrice`, `indexPrice`, `lastFundingRate`, `time`, `bids`, `asks`, timestamp fields | confirm quantity unit and notional rule for selected USDⓈ-M instrument |
| Bybit Derivatives V5 | `GET /v5/market/tickers` | `GET /v5/market/orderbook` | Public market data, no key expected | `category=linear` or `inverse`, uppercase symbol such as `BTCUSDT` | `markPrice`, `indexPrice`, `bid1Price`, `ask1Price`, `bid1Size`, `ask1Size`, `b`, `a`, `ts`, `cts`, `seq` | confirm size unit and contract/notional convention by product type |
| OKX derivatives | `GET /api/v5/public/mark-price` | `GET /api/v5/market/books`; optional `GET /api/v5/market/ticker` | Public market data, no key expected | `instType=SWAP` or `FUTURES`, `instId` such as `BTC-USDT-SWAP` | `markPx`, `bidPx`, `bidSz`, `askPx`, `askSz`, `bids`, `asks`, `ts`, `instType`, `instId` | confirm contract size, lot size, settlement convention, and notional rule |

## 5. Endpoint/field findings

### Binance USDⓈ-M Futures

- Mark candidate: `GET /fapi/v1/premiumIndex`.
- Orderbook candidate: `GET /fapi/v1/depth`.
- Planned mark fields: `symbol`, `markPrice`, `indexPrice`, funding-rate-related field, `time`.
- Planned orderbook fields: `lastUpdateId`, timestamp fields if present, `bids`, `asks`, each level as price/quantity arrays.
- Implementation must verify that mark and depth share the exact same futures contract symbol and that quantity unit/notional can be calculated.

### Bybit Derivatives V5

- Ticker candidate: `GET /v5/market/tickers`.
- Orderbook candidate: `GET /v5/market/orderbook`.
- Planned params: `category=linear` or `category=inverse`, `symbol=BTCUSDT` style uppercase symbol.
- Planned ticker fields: `markPrice`, `indexPrice`, `bid1Price`, `ask1Price`, `bid1Size`, `ask1Size`, `fundingRate`, `nextFundingTime`, response timestamp.
- Planned orderbook fields: `s`, `b`, `a`, `ts`, `cts`, `u`, `seq`.
- Implementation must verify size unit, product type, contract multiplier if applicable, and ticker/orderbook comparability.

### OKX derivatives

- Mark candidate: `GET /api/v5/public/mark-price`.
- Orderbook candidate: `GET /api/v5/market/books`.
- Optional top-of-book/ticker candidate: `GET /api/v5/market/ticker`.
- Planned params: `instType=SWAP` or `FUTURES`; `instId` such as `BTC-USDT-SWAP`.
- Planned mark fields: `instType`, `instId`, `markPx`, `ts`.
- Planned book/ticker fields: `bids`, `asks`, `bidPx`, `bidSz`, `askPx`, `askSz`, `ts`, sequence/checksum fields if present.
- Implementation must verify contract size, lot size, settlement convention, timestamp consistency, and mark-vs-book comparability.

## 6. Unknowns / NEED_DATA items

Treat the future parser/adapter state as `NEED_DATA` until all of the following are verified:

- exact symbol / instrument universe for v0;
- public/no-key status for each endpoint in the target deployment environment;
- mark price and orderbook are for the same instrument;
- derivative unit / contract size / lot size is known;
- notional calculation is deterministic;
- bid/ask size unit is understood;
- timestamp and latency are fresh enough;
- orderbook depth is sufficient for any target notional;
- fee/slippage/buffer placeholders are defined before net-gap interpretation;
- response fields are confirmed by official docs or safe user-local public endpoint evidence.

If a response field is not confirmed, keep it `unknown` and do not implement parser logic.

## 7. Live-network limitation

No live network smoke was required or performed as a merge requirement for this PR. Codex workspace access to exchange sites/endpoints can fail with tunnel `403 Forbidden`; this should be classified as an environment limitation, not a strategy failure.

The next evidence step should be user-local public endpoint probe evidence or mocked parser planning based on official response examples.

## 8. Changed files

- Added: `docs/source_probes/mark_orderbook_gap_hunt_public_sources_v0.md`.
- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_public_source_probe_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `tests/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.
- No Council runtime, notification/alert runtime, Gemini runtime, or prompt changes.

## 9. Tests run

### Git status

```text
git status
```

Result: passed. The branch was `mark-orderbook-gap-public-source-probe-v0`; only the two allowed documentation files were untracked before staging.

### Git diff name check

```text
git diff --name-only
```

Result: passed. No tracked-file diff was shown before staging because the two new files were still untracked. The final staged/HEAD diff contains only the allowed files listed in the changed-files section.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed. `Ran 249 tests in 12.372s` and ended with `OK`.

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed. Matches are existing documentation/test/runtime references and this PR's explicit no-trade deferrals; no new runtime, config, credential, private API, account/balance, order/cancel, withdrawal/deposit/transfer, or execution surface was added.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed. Existing references still identify `cross_exchange_spot_spread_v1` as active and keep `mark_orderbook_gap_hunt_v0` proposed/inactive/NO_TRADE_ONLY.

### Final status check

```text
git status --short
```

Result: passed before staging with only the two allowed documentation files untracked and no generated packet, sampling, or Council-session artifacts present.

## 10. Risks

- Endpoint documentation can change; user-local public endpoint probe evidence should verify current response shapes before implementation.
- Mark price is not executable.
- Derivative unit, contract size, lot size, and notional conventions can create false positives.
- Ticker best bid/ask and orderbook best bid/ask must be checked for comparability and freshness.
- Future implementation could accidentally overfit one venue's units unless the source matrix is reviewed.
- The strategy must not become active automatically.

## 11. Rollback plan

- Revert `docs/source_probes/mark_orderbook_gap_hunt_public_sources_v0.md` and `docs/pr_handoffs/mark_orderbook_gap_hunt_public_source_probe_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling JSON is committed.

## 12. Human review required

Reviewers should inspect:

1. `docs/source_probes/mark_orderbook_gap_hunt_public_sources_v0.md`
2. `docs/pr_handoffs/mark_orderbook_gap_hunt_public_source_probe_v0.md`
3. Prior strategy card: `docs/strategy_task_cards/mark_orderbook_gap_hunt.md`

## 13. No-trade compliance

- private API: no
- API key/secret/token: no
- auth/private headers: no
- account/balance lookup: no
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
- runtime adapter implementation: no
- config adapter registration: no
- parser implementation: no
- sampling implementation: no
- live network smoke as merge requirement: no

## 14. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt User-Local Public Endpoint Probe Evidence v0` or `Mark-Orderbook Gap Hunt Mocked Parser Planning v0` PR. It should keep the work public-read-only and no-key, record safe response previews or official response examples, and still avoid runtime adapter/config/parser implementation unless explicitly scoped later.
