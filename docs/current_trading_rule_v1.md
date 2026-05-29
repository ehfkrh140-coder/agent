# Cross-Exchange Spot Executable Spread v1

현재 active strategy는 `cross_exchange_spot_spread`이며, spot 거래소 간 실제 체결 가능한 bid/ask spread 후보만 검토한다.

## Active Rule

- last_price 차이만으로 기회 판단을 하지 않는다.
- gross spread는 반드시 source ask와 target bid 또는 VWAP 기준으로 계산한다.
- buy_price = source ask 또는 source ask VWAP
- sell_price = target bid 또는 target bid VWAP
- gross_spread = sell_price - buy_price
- gross_spread_pct = gross_spread / buy_price * 100
- estimated_net_gap_pct = gross_spread_pct - buy_fee_pct - sell_fee_pct - estimated_slippage_pct - safety_buffer_pct

## 사용하지 않는 데이터

- mark_price is not required for active v1.
- index_price is not required for active v1.
- leverage is not required for active v1.
- funding_rate와 open_interest는 현재 active strategy 판단에 사용하지 않는다.

## Decision Rules

- 수수료, 슬리피지, orderbook depth, timestamp, data_age_ms, liquidity가 없으면 `NEED_DATA`를 기본값으로 둔다.
- `estimated_net_gap_pct <= 0`이면 `REJECT`를 기본값으로 둔다.
- data stale이면 `REJECT` 또는 `NEED_DATA`를 기본값으로 둔다.
- net gap이 기준 이상이고 데이터 품질이 충분하면 `WATCH`를 기본값으로 둔다.
- `ENTER`는 현재 실행부가 없으므로 실제 주문 지시가 아니라 분석상 후보 판단으로만 허용된다.
- 실제 주문, 출금, 이체, 잔고 조회, private endpoint 사용은 현재 금지한다.
