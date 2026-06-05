# Mark-Orderbook Gap Hunt User-Local Public Endpoint Probe Evidence v0

## 1. Purpose

Record user-local normal-network evidence that the candidate public/no-key derivatives endpoints for `Mark-Orderbook Gap Hunt v0` are reachable and return mark price, orderbook, and top-of-book fields.

This is an evidence-only documentation PR. It does not implement runtime adapters, parsers, config registration, sampling, alerts, notification, Council auto-call, active promotion, execution, private API access, or live network smoke as a merge requirement.

## 2. Baseline

- Active strategy remains `cross_exchange_spot_spread_v1`.
- `mark_orderbook_gap_hunt_v0` remains proposed / experimental-planning / inactive.
- Project scope remains `NO_TRADE_ONLY`.
- The prior source-probe PR documented candidate public endpoints for Binance USDⓈ-M Futures, Bybit Derivatives V5, and OKX derivatives.
- Mark price is not executable; any future strategy must compare it only with validated executable bid/ask, orderbook size, unit, notional, freshness, latency, fee/slippage/buffer, and venue health.
- Unit, contract size, lot size, notional, funding, fee, and slippage rules remain `NEED_DATA` until instrument metadata and parser planning are completed.

## 3. User-local probe command / method

The evidence below comes from user-local PowerShell/direct HTTP endpoint probes in a normal network environment. Codex did not perform these successful live probes in the workspace.

The probes were public read-only HTTP requests to exchange market-data endpoints. No API key, secret, token, auth header, account lookup, balance lookup, order placement, cancellation, withdrawal, deposit, transfer, or private endpoint was used.

## 4. Endpoint results

| Venue | Endpoint role | URL | User-local result | Evidence status |
| --- | --- | --- | --- | --- |
| Binance USDⓈ-M Futures | Mark price | `https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT` | `STATUS: 200` | reachable; mark/index/funding/time fields returned |
| Binance USDⓈ-M Futures | Orderbook | `https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT&limit=5` | `STATUS: 200` | reachable; bid/ask price-size levels and timestamps returned |
| Bybit Derivatives V5 | Ticker / mark price | `https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT` | `STATUS: 200` | reachable; mark/index/funding and market fields returned |
| Bybit Derivatives V5 | Orderbook | `https://api.bybit.com/v5/market/orderbook?category=linear&symbol=BTCUSDT&limit=5` | `STATUS: 200` | reachable; bid/ask price-size levels, sequence, and timestamps returned |
| OKX derivatives | Mark price | `https://www.okx.com/api/v5/public/mark-price?instType=SWAP&instId=BTC-USDT-SWAP` | `STATUS: 200` | reachable; `markPx` and timestamp returned |
| OKX derivatives | Books | `https://www.okx.com/api/v5/market/books?instId=BTC-USDT-SWAP&sz=5` | `STATUS: 200` | reachable; bid/ask book levels, timestamp, and sequence returned |
| OKX derivatives | Ticker / top-of-book | `https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT-SWAP` | `STATUS: 200` | reachable; top-of-book bid/ask and size fields returned |

All seven user-local probes returned `STATUS: 200`.

## 5. Field observations

### Binance USDⓈ-M Futures mark price

Safe preview:

```json
{"symbol":"BTCUSDT","markPrice":"62830.60000000","indexPrice":"62830.58760870","estimatedSettlePrice":"63137.66772234","lastFundingRate":"0.00000655","interestRate":"0.00010000","nextFundingTime":1780560000000,"time":1780536386000}
```

Fields observed:

- `symbol`
- `markPrice`
- `indexPrice`
- `estimatedSettlePrice`
- `lastFundingRate`
- `interestRate`
- `nextFundingTime`
- `time`

### Binance USDⓈ-M Futures orderbook

Safe preview:

```json
{"lastUpdateId":10704876096728,"E":1780536386900,"T":1780536386892,"bids":[["62844.50","10.948"],["62844.40","0.002"],["62843.90","0.002"],["62843.80","0.001"],["62843.20","0.003"]],"asks":[["62844.60","5.875"],["62844.70","0.042"],["62844.80","0.001"],["62844.90","0.001"],["62845.00","0.002"]]}
```

Fields observed:

- `lastUpdateId`
- `E`
- `T`
- `bids`
- `asks`
- bid price / size arrays
- ask price / size arrays

### Bybit Derivatives V5 ticker

Safe preview:

```json
{"retCode":0,"retMsg":"OK","result":{"category":"linear","list":[{"symbol":"BTCUSDT","lastPrice":"62839.90","indexPrice":"62868.33","markPrice":"62830.36","prevPrice24h":"66924.90","price24hPcnt":"-0.061038","highPrice24h":"67497.50","lowPrice24h":"62540.30","prevPrice1h":"63979.70","openInterest":"58829.781","openInterestValue":"3696296318.95","turnover24h":"9105518887.6503","volume24h":"138489.0520","fundingRate":"-0.00000239","nextFundingTime":"1780560000000", ...}}
```

Fields observed:

- `retCode`
- `retMsg`
- `category`
- `symbol`
- `lastPrice`
- `indexPrice`
- `markPrice`
- `openInterest`
- `openInterestValue`
- `fundingRate`
- `nextFundingTime`
- price / volume fields

Note: the user-local preview was truncated, but it confirms mark/index/funding and related market fields.

### Bybit Derivatives V5 orderbook

Safe preview:

```json
{"retCode":0,"retMsg":"OK","result":{"s":"BTCUSDT","a":[["62841.00","0.946"],["62841.60","0.001"],["62841.70","0.024"],["62842.00","0.026"],["62842.20","0.001"]],"b":[["62840.90","6.030"],["62840.80","0.001"],["62840.70","0.001"],["62840.60","0.410"],["62839.90","0.024"]],"ts":1780536387136,"u":3797999,"seq":584271322300,"cts":1780536387135},"retExtInfo":{},"time":1780536387150}
```

Fields observed:

- `s`
- `a`
- `b`
- `ts`
- `u`
- `seq`
- `cts`
- `time`
- ask price / size arrays
- bid price / size arrays

### OKX derivatives mark price

Safe preview:

```json
{"code":"0","data":[{"instId":"BTC-USDT-SWAP","instType":"SWAP","markPx":"62838.1","ts":"1780536387323"}],"msg":""}
```

Fields observed:

- `code`
- `msg`
- `instId`
- `instType`
- `markPx`
- `ts`

### OKX derivatives books

Safe preview:

```json
{"code":"0","msg":"","data":[{"asks":[["62844","1.78","0","6"],["62844.3","0.02","0","1"],["62844.4","1","0","1"],["62844.5","0.04","0","2"],["62844.9","0.07","0","1"]],"bids":[["62843.9","2104.66","0","53"],["62843.8","225.34","0","4"],["62843.7","4.74","0","5"],["62843.6","0.01","0","1"],["62843.5","0.02","0","1"]],"ts":"1780536387405","seqId":320237917986}]}
```

Fields observed:

- `code`
- `msg`
- `asks`
- `bids`
- `ts`
- `seqId`
- book levels with price / size / extra fields

### OKX derivatives ticker

Safe preview:

```json
{"code":"0","msg":"","data":[{"instType":"SWAP","instId":"BTC-USDT-SWAP","last":"62843.8","lastSz":"0.06","askPx":"62843.8","askSz":"158.5","bidPx":"62843.7","bidSz":"1300.09","open24h":"66956.9","high24h":"67477.5","low24h":"62519","volCcy24h":"185877.5356","vol24h":"18587753.56","ts":"1780536387209","sodUtc0":"64117.2","sodUtc8":"66057.6"}]}
```

Fields observed:

- `instType`
- `instId`
- `last`
- `lastSz`
- `askPx`
- `askSz`
- `bidPx`
- `bidSz`
- `open24h`
- `high24h`
- `low24h`
- `volCcy24h`
- `vol24h`
- `ts`

## 6. Interpretation

- User-local normal-network public endpoint probes succeeded for all seven endpoint candidates.
- Binance, Bybit, and OKX can provide candidate mark price fields and executable orderbook/top-of-book fields from public no-key endpoints in the user's environment.
- This confirms endpoint reachability and response-shape availability for planning.
- This does not prove profitability.
- This does not prove parser correctness.
- This does not prove unit/notional correctness.
- This does not justify runtime adapter implementation yet.
- This does not justify config registration, sampling implementation, alert/notification, Council auto-call, active strategy promotion, or execution.
- No execution signal was generated.

## 7. Remaining NEED_DATA items

The next planning step must still resolve:

- derivative unit / contract size;
- lot size;
- notional calculation rule;
- bid/ask size unit;
- whether ticker and orderbook are perfectly comparable for the same symbol/instrument;
- fee/slippage/buffer placeholder;
- freshness/latency thresholds;
- instrument metadata source;
- funding fee treatment, if relevant.

Until these are resolved, future Mark-Orderbook Gap Hunt parser/readiness logic must classify affected cases as `NEED_DATA`, not `WATCH` or `COUNCIL_REVIEW_CANDIDATE`.

## 8. Generated artifact handling

No generated packet JSON, generated sampling JSON, generated Council-session JSON, or other runtime artifact is included in this PR.

The user-local endpoint probes were direct public endpoint checks and safe previews are copied into this evidence document only. No raw generated artifact file is committed.

## 9. Changed files

- Added: `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_public_endpoint_probe_v0.md`.
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

Result: passed. The branch was `mark-orderbook-gap-user-local-public-endpoint-probe-v0`; only this allowed handoff evidence file was untracked before staging.

### Git diff name check

```text
git diff --name-only
```

Result: passed. No tracked-file diff was shown before staging because the new handoff file was still untracked.

### Commit diff name check

```text
git diff --name-only HEAD~1..HEAD
```

Result: passed after commit; output contained only `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_public_endpoint_probe_v0.md`.

### Full unit test

```text
python -m unittest discover -s tests
```

Result: passed. `Ran 249 tests in 22.705s` and ended with `OK`.

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
- Exchange response shapes can change before implementation.
- Safe previews confirm field presence, not parser correctness.
- Derivative size units, lot sizes, contract multipliers, funding, and notional rules can produce false positives if not resolved.
- Mark price is not executable and must not be treated as an order price.
- Future work must not promote this strategy to active automatically.

## 12. Rollback plan

- Revert `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_public_endpoint_probe_v0.md`.
- Re-run `python -m unittest discover -s tests` if a rollback PR is opened.
- Confirm active strategy remains `cross_exchange_spot_spread_v1`.
- Confirm no generated packet/sampling/Council-session JSON is committed.

## 13. Human review required

Reviewers should inspect:

1. `docs/pr_handoffs/mark_orderbook_gap_hunt_user_local_public_endpoint_probe_v0.md`
2. Prior source-probe doc: `docs/source_probes/mark_orderbook_gap_hunt_public_sources_v0.md`
3. Prior strategy card: `docs/strategy_task_cards/mark_orderbook_gap_hunt.md`

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

Open a separate `Mark-Orderbook Gap Hunt Instrument Metadata and Mocked Parser Planning v0` PR. It should identify public instrument metadata sources and define mocked parser fixtures for unit, contract size, lot size, notional calculation, freshness/latency, and funding/fee/slippage assumptions before any runtime adapter or config registration work is considered.
