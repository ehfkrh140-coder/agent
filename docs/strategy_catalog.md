# Strategy Catalog for AI Council v1

이 문서는 AI Council이 검토할 전략 신호를 active / experimental / future 상태로 정리한다. 현재 런타임은 분석/판단 보조 전용이며 주문, 출금, 이체, 잔고 조회, 자동매매 실행을 포함하지 않는다. `ENTER`도 실제 주문 지시가 아니라 분석상 후보 판단이다.

## Active Strategy: P0 Cross-Exchange Spot Executable Spread

- strategy_id: `cross_exchange_spot_spread_v1`
- strategy_family: `cross_exchange_spot_spread`
- status: `active`
- priority: `P0`
- description: 여러 spot 거래소의 source ask와 target bid 또는 VWAP를 비교해 실제 체결 가능한 spread 후보를 탐지한다. last_price 차이만으로 기회로 보지 않는다.
- required_observation_fields:
  - `venue_id`, `market_symbol`, `instrument_type=spot`
  - `bid`, `ask`, `bid_size`, `ask_size`
  - `fees.trading_fee_pct` 또는 maker/taker fee
  - `liquidity.orderbook_depth_available`, `liquidity.depth_levels`, `liquidity.estimated_executable_notional`
  - `timestamp_utc`, `data_quality.max_data_age_ms`, `data_quality.latency_ms`
- required_candidate_metrics:
  - `gross_spread = target_bid - source_ask`
  - `gross_spread_pct = gross_spread / source_ask * 100`
  - `estimated_net_gap_pct = gross_spread_pct - buy_fee_pct - sell_fee_pct - estimated_slippage_pct - safety_buffer_pct`
  - `liquidity_pass`, `freshness_pass`, `gap_pass`
- required_data_quality_fields:
  - `timestamps_available`, `max_data_age_ms`, `latency_ms`, `is_realtime`
- council_validation_points:
  - source ask와 target bid를 사용했는지 확인한다.
  - last_price premium만 보고 기회로 오판하지 않는다.
  - 수수료, 슬리피지, depth, timestamp, liquidity가 빠지면 `NEED_DATA`를 우선한다.
  - `estimated_net_gap_pct <= 0`이면 `REJECT`를 우선한다.
- allowed_decisions: `ENTER`, `WATCH`, `REJECT`, `NEED_DATA`
- execution_policy: `NO_TRADE_ONLY`
- notes: 현재 active v1 전략이며 Upbit/Bithumb live adapter는 아직 구현하지 않았다.

## Experimental Strategy: Mark-Orderbook Gap Hunt

- strategy_id: `mark_orderbook_gap_hunt_v0`
- strategy_family: `mark_orderbook_gap`
- status: `experimental`
- priority: `experimental`
- description: mark 가격과 bid/ask 실제 체결 가능 가격 사이 괴리를 후보로 탐지하는 실험 전략이다. Bybit public adapter가 있어도 현재 active v1 판단 흐름에는 사용하지 않는다.
- required_observation_fields:
  - `venue_id`, `market_symbol`, `instrument_type`
  - `mark_price`, `index_price` optional
  - `bid`, `ask`, `bid_size`, `ask_size`
  - `leverage` 또는 `max_leverage`
  - `unit`, `tick`, `step`
  - `timestamp_utc`, `data_quality.max_data_age_ms`
- required_candidate_metrics:
  - `target_gap_pct = max(base_percent / leverage, min_gap_floor_pct)`
  - `long_gap_pct = ((mark_price - ask) / mark_price) * 100`
  - `short_gap_pct = ((bid - mark_price) / mark_price) * 100`
  - `long_notional = ask * ask_size * unit`
  - `short_notional = bid * bid_size * unit`
  - `gap_pass`, `liquidity_pass`, `freshness_pass`, `guard_pass`
- required_data_quality_fields:
  - `timestamps_available`, `max_data_age_ms`, `latency_ms`
- council_validation_points:
  - current active v1 strategy does not use mark/index/leverage.
  - active config에서 disabled strategy family이면 experimental warning을 유지한다.
  - 후보가 있어도 active v1 흐름에서는 WATCH/NEED_DATA 이상으로 과장하지 않는다.
- allowed_decisions: `WATCH`, `REJECT`, `NEED_DATA`
- execution_policy: `NO_TRADE_ONLY`
- notes: 삭제하지 않고 experimental/archived 후보로 유지한다.

## Future Strategies

아래 전략은 registry에 future로 남기며 현재 active v1 판단 입력으로 사용하지 않는다.

### P1 Future
- `kimchi_premium`
- `reverse_premium`
- `spot_futures_basis`
- `funding_rate`

### P2 Future
- `orderbook_imbalance`
- `trade_flow_momentum`
- `volatility_breakout`
- `mean_reversion`
- `liquidation_open_interest`

### P3 Future
- `news_event`
- `onchain`
- `grid`
- `market_making`

## 공통 원칙

- active strategy가 아닌 strategy_family는 experimental 또는 future로 취급한다.
- `readiness_report.readiness_pass=false`이면 `ENTER`를 금지한다.
- `last_price_only_candidate` warning이 있으면 수익 기회로 과장하지 않는다.
- 모든 전략의 execution_policy는 현재 `NO_TRADE_ONLY`이다.
