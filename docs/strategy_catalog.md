# Strategy Catalog for AI Council v1

이 문서는 마켓데이터 adapter 구현 전에 AI Council이 검토할 전략 신호를 표준화한다. 모든 전략은 현재 단계에서 **분석/판단 보조 전용**이며, 주문·출금·이체·자동매매 실행을 포함하지 않는다. `ENTER`도 실제 주문 지시가 아니라 분석상 후보 판단이다.

## 공통 원칙

- `OpportunityPacket`은 여러 venue, 여러 market, 여러 candidate를 담을 수 있어야 한다.
- last price 차이만으로 실행 가능 기회로 판단하지 않는다.
- 수수료, 슬리피지, 유동성, 데이터 신선도, venue health, guard 상태가 불충분하면 `NEED_DATA` 또는 `WATCH`가 기본이다.
- `execution_policy=NO_TRADE_ONLY`는 현 런타임에서 실제 실행 제안이 금지됨을 뜻한다.
- `execution_policy=FUTURE_EXECUTION_ENGINE`은 미래 deterministic 실행부가 별도 risk gate로만 검토할 수 있음을 뜻한다.

## Strategy 01. Mark-Orderbook Gap Hunt

- strategy_id: `mark_orderbook_gap_hunt_v0`
- strategy_family: `mark_orderbook_gap`
- status: `P0-A`
- description: mark 가격과 bid/ask 실제 체결 가능 가격 사이에 괴리가 발생했을 때, 그 차이가 수수료·슬리피지·유동성·데이터 지연을 감안해도 의미 있는지 AI Council이 판단하는 후보 탐지 전략이다. mark가 best ask보다 충분히 높으면 LONG 후보, best bid가 mark보다 충분히 높으면 SHORT 후보로 분류할 수 있다.
- required_observation_fields:
  - `venue_id`, `market_symbol`, `instrument_type`
  - `mark_price`, `index_price` optional
  - `bid`, `ask`, `bid_size`, `ask_size`
  - `liquidity.depth_levels` optional, `liquidity.estimated_executable_notional`
  - `leverage` 또는 `max_leverage`
  - `unit`, `tick`, `step`
  - `timestamp_utc`, `data_quality.max_data_age_ms`
  - `fees.trading_fee_pct`, `fees.maker_fee_pct`, `fees.taker_fee_pct`
  - guard fields in `candidate.guards`: `manual_blacklisted`, `runtime_blocked`, `open_position`, `pending_duplicate`
- required_candidate_metrics:
  - `target_gap_pct = max(base_percent / leverage, min_gap_floor_pct)`
  - `long_gap_pct = ((mark_price - ask) / mark_price) * 100`
  - `short_gap_pct = ((bid - mark_price) / mark_price) * 100`
  - `long_notional = ask * ask_size * unit`
  - `short_notional = bid * bid_size * unit`
  - `gap_pass`, `liquidity_pass`, `freshness_pass`, `guard_pass`
  - `metrics`, `guards`, `thresholds`
- required_data_quality_fields:
  - `data_quality.timestamps_available`
  - `data_quality.timestamps_aligned`
  - `data_quality.max_data_age_ms`
  - `data_quality.latency_ms`
  - `data_quality.is_realtime`
  - `health.api_ok`, `health.trading_enabled`, `health.maintenance`
- council_validation_points:
  - mark/index/last/bid/ask의 기준 가격이 혼동되지 않았는지 확인한다.
  - gap이 `target_gap_pct` 이상이어도 수수료와 슬리피지 차감 후 의미 있는지 확인한다.
  - bid/ask size와 unit 기준 notional이 최소 유동성 조건을 넘는지 확인한다.
  - `freshness_pass=false` 또는 timestamp 누락이면 `REJECT` 또는 `NEED_DATA`를 우선한다.
  - `manual_blacklisted`, `runtime_blocked`, `open_position`, `pending_duplicate` 중 하나라도 true면 보수적으로 `REJECT`한다.
  - 이 전략은 즉시 주문 전략이 아니라 후보 탐지 전략이다.
- allowed_decisions: `ENTER`, `WATCH`, `REJECT`, `NEED_DATA`
- execution_policy: `NO_TRADE_ONLY`
- notes:
  - 현재 Council은 분석 보조만 수행한다.
  - 수수료/슬리피지/데이터 신선도/유동성 검증 전에는 `NEED_DATA` 또는 `WATCH`가 기본이다.

## Strategy 02. Cross-Exchange Spot Executable Spread

- strategy_id: `cross_exchange_spot_spread_v0`
- strategy_family: `cross_exchange_spot_spread`
- status: `P0-B`
- description: 여러 spot 거래소의 best ask와 best bid를 비교해 실제 체결 가능한 spread 후보를 탐지한다. last_price 차이만으로 기회로 보지 않고 source ask와 target bid를 기준으로 gross spread를 계산한다.
- required_observation_fields:
  - `venue_id`, `market_symbol`, `instrument_type=spot`
  - `last_price`, `bid`, `ask`, `bid_size`, `ask_size`
  - `liquidity.orderbook_depth_available`, `liquidity.depth_levels`
  - `timestamp_utc`, `data_quality.max_data_age_ms`
  - `fees.trading_fee_pct`, `fees.maker_fee_pct`, `fees.taker_fee_pct`
  - `transfer.withdrawal_enabled`, `transfer.deposit_enabled` when cross-venue transfer is relevant
- required_candidate_metrics:
  - `gross_spread = target_bid - source_ask`
  - `gross_spread_pct = gross_spread / source_ask * 100`
  - `estimated_net_gap_pct` only when fee/slippage data is sufficient
  - `required_missing_fields`, `assumptions`
- required_data_quality_fields:
  - `timestamps_available`, `timestamps_aligned`, `max_data_age_ms`, `latency_ms`, `is_realtime`
- council_validation_points:
  - source ask와 target bid를 사용했는지 확인한다.
  - last_price premium만 보고 기회로 오판하지 않는다.
  - 수수료, 슬리피지, depth, transfer 상태가 빠지면 `NEED_DATA` 또는 `WATCH`를 우선한다.
- allowed_decisions: `ENTER`, `WATCH`, `REJECT`, `NEED_DATA`
- execution_policy: `NO_TRADE_ONLY`
- notes: 실제 주문/출금/이체는 구현하지 않는다.

## P1 Strategies

### Kimchi Premium / Reverse Premium
- strategy_id: `kimchi_premium_v0`
- strategy_family: `premium_gap`
- status: `P1`
- description: KRW 거래소와 글로벌 거래소 간 premium 또는 reverse premium을 관측한다.
- required_observation_fields: `venue_id`, `market_symbol`, `region`, `last_price`, `bid`, `ask`, FX 기준, timestamp
- required_candidate_metrics: premium_pct, fx_source, net_premium_after_fee
- required_data_quality_fields: timestamp alignment, FX freshness, venue health
- council_validation_points: FX 기준, 입출금/전송 상태, local liquidity, price source 혼동 검토
- allowed_decisions: `WATCH`, `REJECT`, `NEED_DATA`, `ENTER`
- execution_policy: `NO_TRADE_ONLY`
- notes: 현 단계에서는 premium 관측/검증만 수행한다.

### Spot-Futures Basis
- strategy_id: `spot_futures_basis_v0`
- strategy_family: `basis_gap`
- status: `P1`
- description: spot 가격과 futures/perpetual mark/index 가격의 basis를 검토한다.
- required_observation_fields: spot bid/ask, derivatives mark/index, funding/open_interest optional
- required_candidate_metrics: basis_pct, annualized_basis optional, net_basis_after_fee
- required_data_quality_fields: timestamp alignment, derivative venue health
- council_validation_points: 만기/펀딩/레버리지/강제청산 리스크 검토
- allowed_decisions: `WATCH`, `REJECT`, `NEED_DATA`, `ENTER`
- execution_policy: `NO_TRADE_ONLY`
- notes: futures 실행은 구현하지 않는다.

### Funding Rate
- strategy_id: `funding_rate_v0`
- strategy_family: `funding_rate_gap`
- status: `P1`
- description: perpetual funding rate 차이를 관측하고 유지 가능성 및 데이터 신선도를 검토한다.
- required_observation_fields: funding_rate_pct, next_funding_time_utc, mark_price, index_price, open_interest
- required_candidate_metrics: funding_gap_pct, time_to_funding, estimated_costs
- required_data_quality_fields: funding timestamp source, rate update latency
- council_validation_points: rate 변경 가능성, 포지션 리스크, 거래소별 산식 차이 검토
- allowed_decisions: `WATCH`, `REJECT`, `NEED_DATA`, `ENTER`
- execution_policy: `NO_TRADE_ONLY`
- notes: 포지션 진입 제안은 금지한다.

## P2 Strategies

### Orderbook Imbalance
- strategy_id: `orderbook_imbalance_v0`
- strategy_family: `orderbook_imbalance`
- status: `P2`
- description: bid/ask depth 불균형과 단기 price pressure를 관측한다.
- required_observation_fields: depth_levels, bid/ask size, spread, timestamp
- required_candidate_metrics: imbalance_ratio, spread_pct, depth_notional
- required_data_quality_fields: depth freshness, websocket snapshot sequence optional
- council_validation_points: spoofing, stale book, thin liquidity 검토
- allowed_decisions: `WATCH`, `REJECT`, `NEED_DATA`
- execution_policy: `NO_TRADE_ONLY`
- notes: 단독 ENTER 근거로 사용하지 않는다.

### Trade Flow Momentum
- strategy_id: `trade_flow_momentum_v0`
- strategy_family: `trade_flow_momentum`
- status: `P2`
- description: 최근 체결 방향성과 volume burst를 검토한다.
- required_observation_fields: recent trades, taker buy/sell volume, timestamp
- required_candidate_metrics: momentum_score, volume_zscore
- required_data_quality_fields: trade feed latency, missing trade detection
- council_validation_points: wash trading, venue-specific reporting delay 검토
- allowed_decisions: `WATCH`, `REJECT`, `NEED_DATA`
- execution_policy: `NO_TRADE_ONLY`
- notes: 보조 신호로만 사용한다.

### Liquidation / OI
- strategy_id: `liquidation_oi_v0`
- strategy_family: `liquidation_open_interest`
- status: `P2`
- description: liquidation cluster와 open interest 변화를 검토한다.
- required_observation_fields: open_interest, liquidation feed, mark/index
- required_candidate_metrics: oi_change_pct, liquidation_notional
- required_data_quality_fields: feed source and latency
- council_validation_points: 후행성, exchange coverage, leverage crowding 검토
- allowed_decisions: `WATCH`, `REJECT`, `NEED_DATA`
- execution_policy: `NO_TRADE_ONLY`
- notes: 리스크 경고 신호로 우선 사용한다.

## P3 Strategies

### News/Event
- strategy_id: `news_event_v0`
- strategy_family: `news_event`
- status: `P3`
- description: 이벤트성 뉴스와 공지 영향을 관측한다.
- required_observation_fields: event source, timestamp, affected assets
- required_candidate_metrics: event_severity, source_reliability
- required_data_quality_fields: publication timestamp, duplicate source detection
- council_validation_points: 루머/오보/지연 전파 검토
- allowed_decisions: `WATCH`, `REJECT`, `NEED_DATA`
- execution_policy: `NO_TRADE_ONLY`
- notes: 현재 웹 검색/뉴스 adapter는 구현하지 않는다.

### On-chain
- strategy_id: `onchain_flow_v0`
- strategy_family: `onchain`
- status: `P3`
- description: exchange inflow/outflow, whale movement 등 on-chain 신호를 검토한다.
- required_observation_fields: chain, tx volume, exchange labels, timestamp
- required_candidate_metrics: inflow_outflow_delta, whale_flow_score
- required_data_quality_fields: label source, confirmation count
- council_validation_points: 주소 라벨 오류, 체인 지연, false attribution 검토
- allowed_decisions: `WATCH`, `REJECT`, `NEED_DATA`
- execution_policy: `NO_TRADE_ONLY`
- notes: on-chain adapter는 구현하지 않는다.

### Grid
- strategy_id: `grid_context_v0`
- strategy_family: `grid`
- status: `P3`
- description: range-bound market에서 grid suitability를 관찰한다.
- required_observation_fields: volatility, range, spread, fees
- required_candidate_metrics: grid_viability_score, fee_drag
- required_data_quality_fields: historical data window quality
- council_validation_points: trend breakout, fee drag, inventory risk 검토
- allowed_decisions: `WATCH`, `REJECT`, `NEED_DATA`
- execution_policy: `NO_TRADE_ONLY`
- notes: grid bot 구현은 금지한다.

### Market Making
- strategy_id: `market_making_context_v0`
- strategy_family: `market_making`
- status: `P3`
- description: spread, inventory, volatility 기반 market making suitability를 관찰한다.
- required_observation_fields: spread, depth, volatility, fee tier
- required_candidate_metrics: spread_capture_potential, inventory_risk_score
- required_data_quality_fields: orderbook freshness, trade feed latency
- council_validation_points: adverse selection, inventory drift, venue outage 검토
- allowed_decisions: `WATCH`, `REJECT`, `NEED_DATA`
- execution_policy: `NO_TRADE_ONLY`
- notes: market making 실행부는 구현하지 않는다.
