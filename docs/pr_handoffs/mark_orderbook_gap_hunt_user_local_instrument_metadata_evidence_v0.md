# Mark-Orderbook Gap Hunt User-Local Instrument Metadata Evidence v0

## 1. Purpose

Record user-local normal-network evidence that Binance USDⓈ-M Futures, Bybit Derivatives V5, and OKX derivatives instrument metadata endpoints are reachable through public no-key requests and return the core metadata fields needed for future `Mark-Orderbook Gap Hunt v0` mocked parser planning.

This evidence is from user-run public endpoint probes. Codex did not perform these successful live probes in the workspace, and this PR is documentation-only. It does not implement runtime adapters, parser code, config registration, sampling, alerts, notification, Council auto-call, active promotion, execution, private API access, or generated artifacts.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Execution policy remains `NO_TRADE_ONLY`.
- Previous user-local endpoint evidence confirmed mark price, orderbook, and top-of-book field availability.
- Previous metadata planning documented the need for instrument metadata before notional/parser correctness can be claimed.
- This evidence confirms metadata endpoint reachability and core field availability, but it still does not prove parser correctness, final notional formula correctness, profitability, alert readiness, Council auto-call readiness, active promotion readiness, or execution readiness.

## 3. User-local metadata probe method

The user directly probed public no-key metadata endpoints from a normal local network environment.

No API key, secret, token, auth/private header, private endpoint, account lookup, balance lookup, order placement, cancellation, withdrawal, deposit, transfer, fiat/bank flow, auto-trading, Council auto-call, or execution path was used.

## 4. Endpoint results

| Venue | Endpoint role | URL | User-local result | Evidence status |
| --- | --- | --- | --- | --- |
| Binance USDⓈ-M Futures | Symbol metadata / exchange info | `https://fapi.binance.com/fapi/v1/exchangeInfo` | `STATUS: 200` | BTCUSDT symbol-level metadata extracted |
| Bybit Derivatives V5 | Linear instruments info | `https://api.bybit.com/v5/market/instruments-info?category=linear&symbol=BTCUSDT` | `STATUS: 200` | BTCUSDT linear instrument metadata returned |
| OKX derivatives | Swap instruments info | `https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId=BTC-USDT-SWAP` | `STATUS: 200` | BTC-USDT-SWAP metadata returned |

All three user-local instrument metadata probes returned `STATUS: 200`.

## 5. Venue metadata observations

### Binance USDⓈ-M Futures `exchangeInfo`

URL:

```text
https://fapi.binance.com/fapi/v1/exchangeInfo
```

User-local result: `STATUS: 200`.

BTCUSDT symbol-level extracted fields:

- `symbol`: `BTCUSDT`
- `pair`: `BTCUSDT`
- `contractType`: `PERPETUAL`
- `status`: `TRADING`
- `baseAsset`: `BTC`
- `quoteAsset`: `USDT`
- `marginAsset`: `USDT`
- `pricePrecision`: `2`
- `quantityPrecision`: `3`
- `PRICE_FILTER.minPrice`: `556.80`
- `PRICE_FILTER.maxPrice`: `4529764`
- `PRICE_FILTER.tickSize`: `0.10`
- `LOT_SIZE.minQty`: `0.001`
- `LOT_SIZE.maxQty`: `1000`
- `LOT_SIZE.stepSize`: `0.001`
- `MARKET_LOT_SIZE.minQty`: `0.001`
- `MARKET_LOT_SIZE.maxQty`: `120`
- `MARKET_LOT_SIZE.stepSize`: `0.001`
- `MIN_NOTIONAL.notional`: `50`
- `PERCENT_PRICE.multiplierDown`: `0.9500`
- `PERCENT_PRICE.multiplierUp`: `1.0500`
- `PERCENT_PRICE.multiplierDecimal`: `4`
- `POSITION_RISK_CONTROL.positionControlSide`: `NONE`

Interpretation:

Binance BTCUSDT USDⓈ-M perpetual symbol-level metadata is available from a public no-key endpoint. It provides trading status, asset/margin identity, price tick, quantity step, minimum quantity, market quantity limits, and minimum-notional candidate fields for future mocked parser planning.

### Bybit Derivatives V5 `instruments-info`

URL:

```text
https://api.bybit.com/v5/market/instruments-info?category=linear&symbol=BTCUSDT
```

User-local result: `STATUS: 200`.

Observed fields:

- `retCode`: `0`
- `category`: `linear`
- `symbol`: `BTCUSDT`
- `contractType`: `LinearPerpetual`
- `status`: `Trading`
- `baseCoin`: `BTC`
- `quoteCoin`: `USDT`
- `settleCoin`: `USDT`
- `priceScale`: `2`
- `priceFilter.tickSize`: `0.10`
- `lotSizeFilter.maxOrderQty`: `1500.000`
- `lotSizeFilter.minOrderQty`: `0.001`
- `lotSizeFilter.qtyStep`: `0.001`
- `lotSizeFilter.maxMktOrderQty`: `150.000`
- `lotSizeFilter.minNotionalValue`: `5`
- `fundingInterval`: `480`
- `upperFundingRate`: `0.005`
- `lowerFundingRate`: `-0.005`

Interpretation:

Bybit linear BTCUSDT instrument metadata is available from a public no-key endpoint and provides useful tick size, quantity step, minimum order quantity, maximum order quantity, market-order maximum quantity, minimum notional value, funding interval, funding limits, and settlement currency fields for future mocked parser planning.

### OKX derivatives public `instruments`

URL:

```text
https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId=BTC-USDT-SWAP
```

User-local result: `STATUS: 200`.

Observed fields:

- `code`: `0`
- `instId`: `BTC-USDT-SWAP`
- `instType`: `SWAP`
- `ctType`: `linear`
- `ctVal`: `0.01`
- `ctMult`: `1`
- `ctValCcy`: `BTC`
- `settleCcy`: `USDT`
- `tickSz`: `0.1`
- `lotSz`: `0.01`
- `minSz`: `0.01`
- `state`: `live`
- `uly`: `BTC-USDT`
- `instFamily`: `BTC-USDT`
- `lever`: `100`

Interpretation:

OKX BTC-USDT-SWAP metadata is available from a public no-key endpoint and provides contract value, multiplier, contract value currency, settlement currency, tick size, lot size, minimum size, state, underlying, instrument family, and leverage fields useful for future mocked parser planning.

## 6. Cross-venue interpretation

- All three venues returned `STATUS: 200` from the user-local normal-network environment.
- Metadata field availability is sufficient to proceed to mocked parser fixture planning.
- This confirms endpoint reachability and metadata field availability.
- This does not prove profitability.
- This does not prove parser correctness.
- This does not finalize notional formulas.
- This does not finalize fee/slippage/funding treatment.
- This does not justify runtime adapter, config registration, or parser implementation yet.
- This does not justify alert/notification, Council auto-call, active strategy promotion, or execution/private API work.

## 7. Remaining NEED_DATA

The following remain unresolved and must be addressed before parser/readiness logic can classify any mark/orderbook case above `NEED_DATA`:

- Final notional formula per venue.
- Whether Binance quantity unit can be treated as BTC amount for the selected USDⓈ-M BTCUSDT parser planning.
- Whether Bybit quantity is base coin amount for linear BTCUSDT or requires additional confirmation.
- Whether OKX size in books/ticker maps to contracts/lots and how `ctVal`, `ctMult`, and `ctValCcy` determine BTC/USDT notional.
- Bid/ask size unit per venue.
- Whether ticker and orderbook are perfectly comparable for the same symbol/instrument.
- Funding fee treatment.
- Fee/slippage/buffer placeholders.
- Freshness/latency thresholds.
- Exact parser behavior for missing metadata, instrument mismatch, and stale timestamp cases.

## 8. Generated artifact handling

No generated packet JSON, generated sampling JSON, generated Council-session JSON, or other runtime artifact is included in this PR.

The user-local metadata probes were direct public endpoint checks. The extracted fields are copied into this evidence document only. No raw generated artifact file is committed.

## 9. Changed files

- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_instrument_metadata_evidence_v0.md`.
- No `src/**` changes.
- No `configs/**` changes.
- No `tests/**` changes.
- No `data/generated_packets/**`, `data/market_samples/**`, or `data/council_sessions/**` changes.
- No Council runtime, notification/alert runtime, Gemini runtime, or prompt changes.

## 10. Tests run by Codex

### Git status

```text
git status
```

Result: passed. The branch was `mark-orderbook-gap-user-local-instrument-metadata-evidence-v0`; only this allowed handoff evidence file was untracked before staging.

### Git diff name check

```text
git diff --name-only
```

Result: passed. No tracked-file diff was shown before staging because the new handoff file was still untracked.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: to be run after commit; expected to contain only `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_instrument_metadata_evidence_v0.md`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed. `Ran 249 tests in 12.894s` and ended with `OK`.

### No-trade safety check

```text
rg -n -i -e "api_key|api_secret|secret|token|Authorization|Bearer|balance|account|order|cancel|withdraw|deposit|transfer|private" src configs tests docs README.md
```

Result: completed. The scan returned existing documentation/test/runtime references plus this PR's explicit no-trade deferrals; this PR added no runtime, config, credential, private API, account/balance, order/cancel, withdrawal/deposit/transfer, or execution surface.

### Active strategy check

```text
rg -n -i -e "cross_exchange_spot_spread_v1|tether_cross_market_premium|orderbook_imbalance|mark_orderbook_gap|active|NO_TRADE_ONLY" configs docs src tests README.md
```

Result: completed. Existing references still identify `cross_exchange_spot_spread_v1` as active and keep `mark_orderbook_gap_hunt_v0` proposed/inactive/NO_TRADE_ONLY.

### Final status check

```text
git status --short
```

Result: passed before staging with only this allowed handoff file untracked and no generated packet, sampling, or Council-session artifacts present.

## 11. Risks

- User-local endpoint reachability does not guarantee Codex workspace or deployment-network reachability.
- Metadata field availability does not prove parser correctness.
- Metadata field availability does not finalize notional formulas or funding/fee/slippage treatment.
- Incorrect unit, contract, lot, or notional assumptions can create false positives.
- Mark price is not executable and must not be treated as an order price.
- Future work must not promote this strategy to active automatically.

## 12. Rollback plan

- Revert `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_instrument_metadata_evidence_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling/Council-session JSON is committed.

## 13. Human review required

Reviewers should inspect:

1. `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_instrument_metadata_evidence_v0.md`
2. Prior metadata planning doc: `docs/source_probes/mark_orderbook_gap_hunt_instrument_metadata_v0.md`
3. Prior metadata planning handoff: `docs/pr_handoffs/mark_orderbook_gap_hunt_instrument_metadata_mocked_parser_planning_v0.md`
4. Prior public endpoint evidence: `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_public_endpoint_probe_v0.md`
5. Strategy card: `docs/strategy_task_cards/mark_orderbook_gap_hunt.md`

## 14. No-trade compliance

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

## 15. Next recommended step

Open a separate `Mark-Orderbook Gap Hunt Mocked Parser Fixture Planning v0` PR. It should use these metadata observations plus the previous market-data endpoint observations to define safe mocked fixtures and expected normalized parser outputs before runtime adapter/config/parser implementation is considered.
