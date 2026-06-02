# AI Council Project Handoff v3 — 전략/목적/현재 개발상태 업데이트

작성일: 2026-06-02  
대상 저장소: https://github.com/ehfkrh140-coder/agent  
권장 저장 위치: `C:\Users\qhrb9\Desktop\agent\docs\AI_Council_Project_Handoff_v3_Strategy_Update_2026-06-02.md`

---

## 0. 이 문서의 목적

이 문서는 이전 대화가 길어져 새 GPT 채팅과 새 Codex 작업으로 이어가기 위한 **업데이트형 인수인계 문서**다.

중요한 정정:

- 이 프로젝트는 단순 챗봇이 아니다.
- 이 프로젝트는 단순 알림봇도 아니다.
- 이 프로젝트는 지금 당장 주문을 넣는 자동매매 봇도 아니다.
- 최종 목표는 **변화하는 시장 데이터를 자동 수집하고, 여러 AI 에이전트가 서로 다른 관점으로 회의·토론·검증하여 수익 기회를 판단하는 AI Council 기반 매매 판단 시스템**이다.

현재는 실거래 단계가 아니라, 다음 구조를 안전하게 쌓는 중이다.

```text
public market data 수집
→ OpportunityPacket 표준화
→ deterministic readiness / sampling / alert / journal
→ AI Council 검토
→ WATCH / REJECT / NEED_DATA / 분석상 ENTER 후보 판단
→ 나중에 별도 deterministic execution/risk 엔진이 실제 주문 여부를 판단
```

현재 프로젝트는 **NO_TRADE_ONLY** 원칙을 유지한다.

금지:

```text
private API
API key / secret / token
잔고 조회
주문 / 주문취소
출금 / 입금 / 이체
원화 입출금 / bank transfer
자동매매
LLM 판단을 바로 주문으로 전환
active strategy 무단 변경
```

---

## 1. 프로젝트 최종 목표

최종적으로 만들려는 것은 **AI Council 매매 판단 시스템**이다.

시장 데이터에서 다음과 같은 신호가 발생하면:

```text
거래소 간 가격 차이
호가 차이
체결 가능 스프레드
오더북 불균형
펀딩비 차이
현물-선물 베이시스
청산/OI/체결 흐름 이상
테더/USDT 국내-해외 시장 차이
뉴스/이벤트 기반 시장 왜곡
```

데이터 엔진이 이를 `OpportunityPacket`으로 만들고, AI Council이 다음 질문을 검토한다.

```text
이 차이가 진짜인가?
데이터 지연/착시/last_price 착시인가?
bid/ask와 VWAP 기준으로 실제 체결 가능한가?
수수료, 슬리피지, 안전 버퍼 후에도 순수익이 남는가?
유동성은 충분한가?
글로벌 reference나 depeg 위험은 없는가?
수동 사용자 의견이 bias를 만들고 있지 않은가?
리스크 게이트를 통과하는가?
```

최종적으로 agent들은 다음 중 하나를 낸다.

```text
WATCH
REJECT
NEED_DATA
ENTER 후보
```

단, 현재 단계에서 `ENTER`는 **실제 주문 지시가 아니다.**  
항상 분석상 후보일 뿐이며 execution layer는 아직 구현하지 않는다.

---

## 2. AI Council 구조

현재 Council은 Single Round v1 구조다.

```text
agent_01: Chair / 문제 정리자
agent_02: Pro / 수익 가능성 탐색자
agent_03: Skeptic / 약점 공격자
agent_04: Risk Manager / 안전성 검토자
agent_05: Final Summarizer / 최종 판단 정리자
```

현재 역할:

```text
agent_01
- OpportunityPacket을 회의 가능한 브리프로 정리
- 관측 데이터, 사용자 의견, 쟁점, 부족 데이터를 분리

agent_02
- 수익 thesis와 조건부 가능성을 탐색
- 단, 주문 실행 제안 금지

agent_03
- 데이터 오류, 지연, 호가 착시, 수수료, 슬리피지, 유동성 부족을 공격

agent_04
- 리스크 게이트 우선
- readiness_pass=false이면 ENTER 금지

agent_05
- 제공된 agent 의견과 readiness를 바탕으로 최종 분석 판단 정리
```

초기 단계에서는 Gemini CLI가 코딩/도구 사용 본능으로 파일 탐색, workspace 분석, non-json output을 내는 문제가 있었다. 이후 JSON-only hardening, stdin mode, targeted policy, response safety validator, tool-call warning을 추가했다.

---

## 3. 핵심 아키텍처

현재 저장소의 큰 구조는 다음이다.

```text
market data adapter
→ normalized snapshot
→ OpportunityPacketBuilder
→ OpportunityPacket
→ strategy readiness
→ sampling / persistence
→ journal / alert
→ optional Council dry-run / manual Council
```

주요 구성:

```text
src/market_data/
- public read-only adapters
- replay adapters
- composite adapters
- packet_builder
- vwap/slippage
- sampling/persistence
- handoff

src/strategy/
- readiness
- strategy formula helpers

src/council/
- scenario loader
- SingleRoundCouncilRunner
- dry-run context generation

src/notifications/
- alert rules
- formatters

src/storage/
- council sessions
- opportunity journal
- alert logs

tools/
- collect_market_data.py
- sample_market_data.py
- run_strategy_scenarios.py
- probe_usdt_krw_sources.py
- notify_sampling_result.py
```

---

## 4. 현재 active / experimental / future 전략 상태

### 4.1 Active strategy

현재 active strategy는 하나다.

```text
strategy_family: cross_exchange_spot_spread
strategy_id: cross_exchange_spot_spread_v1
status: active
execution_policy: NO_TRADE_ONLY
```

목적:

```text
국내 Upbit/Bithumb BTC/KRW public spot orderbook 기반 executable spread 감지
```

핵심 원칙:

```text
last_price 차이만으로 판단 금지
source ask / target bid 또는 VWAP 기준
수수료 + 슬리피지 + safety buffer 반영
readiness_pass=false이면 ENTER 금지
private endpoint / 잔고 / 주문 / 출금 / 이체는 범위 밖
```

현재 구현 상태:

```text
Upbit/Bithumb public adapter
composite spot spread adapter
VWAP/slippage
OpportunityPacket
readiness
sampling/persistence
handoff/journal
alert
Council dry-run / manual Council 가능
```

---

### 4.2 Experimental strategy 1: orderbook_imbalance

```text
strategy_family: orderbook_imbalance
strategy_id: orderbook_imbalance_v0
status: experimental
execution_policy: NO_TRADE_ONLY
active: false
```

목적:

```text
bid/ask depth imbalance를 통해 매수/매도 호가 쏠림을 감지하는 실험 전략
```

현재 구현 상태:

```text
manual scenarios
readiness
replay packet builder
replay_orderbook_imbalance adapter
live_upbit_bithumb_orderbook_imbalance composite adapter
sampling/persistence
experimental alert/journal
```

중요:

```text
executable spread 전략이 아님
estimated_net_gap_pct 없음
Council handoff 없음
active 아님
```

---

### 4.3 Experimental strategy 2: tether_cross_market_premium

현재 집중 중인 전략이다.

```text
strategy_family: tether_cross_market_premium
strategy_id: usdt_krw_global_reference_v0
status: experimental
execution_policy: NO_TRADE_ONLY
active: false
```

정확한 전략 정의:

```text
국내 Upbit/Bithumb USDT/KRW 가격·호가·뎁스를 비교하고,
해외 Binance/Bybit/OKX의 global USDT reference health를 확인해,
국내 테더 시장의 스프레드 / 왜곡 / depeg risk를 감지하는 read-only 전략.
```

중요한 정정:

```text
이 전략은 USD/KRW FX 기반 김치프리미엄 전략이 아니다.
FX / fair_usdt_krw_price / Frankfurter는 현재 범위 밖이다.
```

Domestic v0:

```text
Upbit USDT/KRW
Bithumb USDT/KRW
```

Global reference v0:

```text
Binance
Bybit
OKX
```

현재까지 완료:

```text
strategy direction reframe
Bithumb USDT/KRW public recheck
experimental scaffolding
manual scenarios
formula helper
readiness rule
replay packet builder
replay collect_market_data output
dry-run context
handoff evidence file
live composite adapter 등록
```

현재 blocker:

```text
live_tether_cross_market_premium packet 생성 실패
원인: global USDT reference adapters 3개가 모두 실패
```

실제 로컬 실패 로그:

```text
live_binance_usdt_reference:
HTTP status 400 for https://api.binance.com/api/v3/ticker/bookTicker?symbol=USDTUSDC

live_bybit_usdt_reference:
Bybit reference status 10001: Not supported symbols

live_okx_usdt_reference:
OKX reference status 51001: Instrument ID, Instrument ID code, or Spread ID doesn't exist.
```

현재 판단:

```text
등록 문제는 아니다.
adapter 목록에는 live_binance_usdt_reference, live_bybit_usdt_reference, live_okx_usdt_reference, live_tether_cross_market_premium이 존재한다.

문제는 global reference symbol / endpoint / parser 후보가 잘못되었거나,
USDT reference로 사용하려는 pair 선택이 각 거래소 public endpoint에서 지원되지 않는 것이다.
```

---

### 4.4 Deferred / not current: stablecoin_krw_premium / FX Kimchi Premium

이전에는 다음 전략을 고려했다.

```text
strategy_family: stablecoin_krw_premium
strategy_id: usdt_krw_kimchi_premium_v0
```

초기 개념:

```text
domestic USDT/KRW
vs
USD/KRW FX reference × global USDT/USD reference
```

하지만 사용자가 정정했다.

현재 사용자가 원하는 것은:

```text
국내 Upbit/Bithumb 테더 가격
vs
해외 Binance/Bybit/OKX global USDT reference health
```

즉, USD/KRW FX는 현재 매매법 범위를 넓히기만 하고 실제 구현 대상이 아니다.

따라서:

```text
stablecoin_krw_premium / FX-based kimchi premium
→ near-term deferred / superseded
```

---

## 5. 우리가 만들기로 했던 매매방식 전체 카탈로그

이 목록은 이전 전략 인수인계 문서의 카탈로그를 현재 상태에 맞게 업데이트한 것이다.

### Strategy 01. Cross-Exchange Spot Executable Spread

현재 active v1.

```text
동일 자산이 국내 거래소 A/B에서 다르게 거래될 때,
source ask와 target bid 기준으로 실제 체결 가능한 스프레드를 감지한다.
```

필요 데이터:

```text
source ask
target bid
bid_size / ask_size
orderbook depth
VWAP
fee
slippage
safety_buffer
timestamp
latency
data_age
```

Council 검증:

```text
last price 착시인가?
source ask / target bid 기준으로 순수익이 남는가?
호가 깊이가 충분한가?
수수료/슬리피지/버퍼 후에도 net gap이 양수인가?
데이터가 stale이 아닌가?
```

---

### Strategy 02. Tether Cross-Market Premium

현재 experimental, 집중 개발 중.

```text
국내 Upbit/Bithumb USDT/KRW 가격과,
해외 Binance/Bybit/OKX global USDT reference health를 함께 보고
국내 테더 시장의 가격 차이/왜곡/depeg risk를 감지한다.
```

필요 데이터:

```text
Upbit USDT/KRW bid/ask/depth
Bithumb USDT/KRW bid/ask/depth
Binance global USDT reference bid/ask
Bybit global USDT reference bid/ask
OKX global USDT reference bid/ask
global_usdt_mid
global_usdt_depeg_flag
fees
timestamp
latency
```

중요:

```text
FX 사용 안 함
fair_usdt_krw_price 계산 안 함
해외 거래소는 처음엔 실행 대상이 아니라 reference/depeg health 용도
```

---

### Strategy 03. Orderbook Imbalance

현재 experimental.

```text
호가창 bid depth와 ask depth의 불균형을 감지해 수급 쏠림을 확인한다.
```

필요 데이터:

```text
depth_bid_levels
depth_ask_levels
bid_depth_notional
ask_depth_notional
imbalance_ratio
spread_pct
timestamp
latency
```

검증:

```text
bid-heavy/ask-heavy가 지속되는가?
일시적인 허수 주문인가?
실제 체결 가능한 depth인가?
```

---

### Strategy 04. Mark-Orderbook Gap Hunt

현재 near-term active 아님. 이전 알람봇에서 나온 핵심 아이디어.

```text
mark 가격과 실제 bid/ask 체결 가격 사이의 괴리를 감지한다.
```

핵심 공식:

```text
target_gap_pct = BASE_PERCENT / leverage
long_gap_pct = ((mark - ask) / mark) * 100
short_gap_pct = ((bid - mark) / mark) * 100
long_notional = ask * ask_size * unit
short_notional = bid * bid_size * unit
```

주의:

```text
mark price는 실제 체결 가격이 아니다.
수수료/슬리피지/데이터 지연/허수 호가 확인 전에는 실행 후보로 보면 안 된다.
```

---

### Strategy 05. Domestic/Global Price Premium and Discount

현재 Tether Cross-Market과 일부 겹치지만 일반 자산으로 확장 가능.

```text
국내 가격과 해외 reference 가격의 괴리를 해석한다.
```

현재는 FX 기반 정통 김프가 아니라, reference health 중심으로 축소한다.

---

### Strategy 06. Spot-Futures Basis

```text
현물 가격과 선물/무기한 선물 가격 차이를 이용하는 전략.
```

필요 데이터:

```text
spot_price
futures_price
basis_pct
funding_rate
expiry/perpetual
fees
margin risk
```

---

### Strategy 07. Funding Rate Strategy

```text
무기한 선물 funding rate를 수익원 또는 과열 신호로 해석한다.
```

필요 데이터:

```text
funding_rate
next_funding_time
open_interest
basis
price_change
```

---

### Strategy 08. Trade Flow Momentum

```text
실제 체결 강도와 매수/매도 체결 흐름을 감지한다.
```

필요 데이터:

```text
recent_trades
buy_volume
sell_volume
trade_imbalance
large_trade_count
```

---

### Strategy 09. Volatility Breakout

```text
일정 범위 또는 고점/저점 돌파를 감지한다.
```

필요 데이터:

```text
OHLCV
ATR
range
breakout_level
volume
```

---

### Strategy 10. Mean Reversion

```text
가격, 스프레드, 베이시스, 프리미엄이 과도하게 벌어진 뒤 평균으로 돌아올 가능성을 본다.
```

필요 데이터:

```text
spread_zscore
historical_mean
historical_std
current_deviation
```

---

### Strategy 11. Grid Strategy

```text
횡보장에서 일정 간격으로 매수/매도 반복을 시도하는 전략.
```

현재는 future research.

필요 데이터:

```text
range_bound
volatility
grid_spacing
fee
inventory
```

---

### Strategy 12. Market Making

```text
양쪽 호가를 제공해 스프레드를 수익화하는 전략.
```

현재는 execution/private API가 필요하므로 장기 future.

필요 데이터:

```text
spread
depth
fee_tier
fill_probability
inventory
cancel_latency
```

---

### Strategy 13. Liquidation Data Strategy

```text
롱/숏 청산 클러스터와 강제청산 후 가격 반응을 이용한다.
```

필요 데이터:

```text
liquidation_long
liquidation_short
liquidation_cluster_price
OI_change
price_reaction
```

---

### Strategy 14. Open Interest Strategy

```text
가격 변화와 OI 변화를 함께 해석한다.
```

필요 데이터:

```text
open_interest
oi_change
price_change
funding_rate
long_short_ratio
```

---

### Strategy 15. News / Event Strategy

```text
상장, 규제, 해킹, ETF, 거래소 공지, 거시경제 발표 등 이벤트를 해석한다.
```

필요 데이터:

```text
news_source
event_type
timestamp
affected_assets
price_reaction
```

---

### Strategy 16. On-chain Strategy

```text
온체인 이동, 고래 지갑, 거래소 유입/유출 등을 해석한다.
```

필요 데이터:

```text
exchange_inflow
exchange_outflow
whale_transfer
wallet_cluster
stablecoin_supply
```

---

## 6. 현재까지의 개발 과정 요약

### Phase 1. Gemini CLI 5-agent runtime

완료:

```text
Gemini CLI OAuth 기반
5개 Gemini Pro 계정 분리
GEMINI_CLI_HOME 분리
agent preflight
session 저장
parallel 실행
JSON-only hardening
stdin mode
targeted policy
response safety warning
```

이전 문제:

```text
non_json_output
workspace empty message
Gemini CLI tool calls
tool_type 400 error
429 model capacity
```

현재는 상당 부분 완화됨.

---

### Phase 2. Single Round Council v1

완료:

```text
agent_01 chair
agent_02/03/04 review
agent_05 final
chair_context / review_contexts / final_context
CouncilSessionStore
dry-run context
session JSON 저장
```

---

### Phase 3. OpportunityPacket / scenario mode

완료:

```text
OpportunityPacket v0 schema
scenario loader
--scenario
--opportunity-file
--dry-run-context
expected_behavior는 agent context에서 제외
scenario evaluation metadata
```

---

### Phase 4. Active cross_exchange_spot_spread

완료:

```text
strategy registry
readiness
Upbit/Bithumb public adapters
VWAP
fee/slippage/safety buffer
replay + live packet
sampling/persistence
handoff/journal
alert
Council dry-run
```

---

### Phase 5. Orderbook imbalance

완료:

```text
experimental registry
manual scenarios
readiness
replay packet builder
live composite adapter
sampling/persistence
experimental alert
journal
```

---

### Phase 6. Tether cross-market premium

진행 중.

완료:

```text
전략 방향 정정: no FX
strategy card
source matrix
Bithumb recheck
experimental scaffolding
manual scenarios
readiness
formula helper
replay packet builder
live composite adapter 등록
handoff evidence
```

현재 blocker:

```text
live_tether_cross_market_premium fails because all global references fail.
```

---

### Phase 7. PR trust / handoff evidence

완료:

```text
.github/pull_request_template.md
docs/pr_handoffs/README.md
docs/pr_handoffs/TEMPLATE.md
docs/pr_review_policy.md
docs/merge_gate.md
docs/rollback_policy.md
docs/task_checklist.md
docs/agent_workflow.md
```

문제:

```text
Codex PR title/body가 여전히 generic한 경우가 많음.
하지만 docs/pr_handoffs/<task>.md evidence file을 요구하도록 개선됨.
```

---

## 7. 현재 blocker 상세 분석

명령:

```powershell
python tools\collect_market_data.py --adapter live_tether_cross_market_premium --output data\generated_packets\live_tether_cross_market_packet.json
```

실패:

```text
Market data collection failed:
All global USDT reference adapters failed for live_tether_cross_market_premium:
live_binance_usdt_reference, live_bybit_usdt_reference, live_okx_usdt_reference
```

개별 실패:

```text
python tools\collect_market_data.py --adapter live_binance_usdt_reference --output data\generated_packets\debug_binance_usdt_reference.json

Market data collection failed:
HTTP status 400 for https://api.binance.com/api/v3/ticker/bookTicker?symbol=USDTUSDC
```

```text
python tools\collect_market_data.py --adapter live_bybit_usdt_reference --output data\generated_packets\debug_bybit_usdt_reference.json

Market data collection failed:
Bybit reference status 10001: Not supported symbols
```

```text
python tools\collect_market_data.py --adapter live_okx_usdt_reference --output data\generated_packets\debug_okx_usdt_reference.json

Market data collection failed:
OKX reference status 51001: Instrument ID, Instrument ID code, or Spread ID doesn't exist.
```

원인 추정:

```text
USDTUSDC / USDT-USD / USDT-USDC 같은 pair 후보가 각 거래소에서 실제 지원되지 않거나,
endpoint별 symbol format이 틀렸거나,
parser가 실제 응답 shape를 잘못 가정하고 있다.
```

핵심:

```text
이건 adapter 등록 문제가 아니다.
domestic Upbit/Bithumb 문제도 아니다.
global reference symbol/endpoint/parser 문제다.
```

---

## 8. 다음 GPT가 가장 먼저 해야 할 일

새 GPT는 다음을 해야 한다.

1. 이 문서를 읽는다.
2. GitHub repo `https://github.com/ehfkrh140-coder/agent` 최신 상태를 확인한다.
3. 현재 latest PR 이후에도 blocker가 같은지 확인한다.
4. Codex에게 줄 다음 작업 요청문을 만든다.
5. 작업은 **Tether Cross-Market Global Reference Diagnostics v0**로 작게 쪼갠다.

---

## 9. 다음 Codex 작업명

```text
Tether Cross-Market Global Reference Diagnostics v0
```

목표:

```text
global USDT reference adapter 실패 원인을 진단 가능하게 만들고,
Binance/Bybit/OKX의 public reference symbol/endpoint/parser 문제를 보수적으로 수정한다.
```

중요:

```text
live_tether_cross_market_premium이 최소 1개 이상의 global reference 성공 시 packet을 생성할 수 있게 하되,
0개 성공 시 명확한 per-adapter diagnostic error를 내야 한다.
```

금지:

```text
private API
API key
auth headers
잔고 조회
주문
출금/이체
sampling/alert
Council handoff
active 승격
Gemini runtime/prompt 변경
```

필수 handoff file:

```text
docs/pr_handoffs/tether_cross_market_global_reference_diagnostics_v0.md
```

---

## 10. 새 GPT 첫 메시지

새 GPT에게는 아래를 보내면 된다.

```text
나는 GitHub repo `https://github.com/ehfkrh140-coder/agent`에서 AI Council 기반 read-only 매매 판단 시스템을 개발 중입니다.

첨부한 `AI_Council_Project_Handoff_v3_Strategy_Update_2026-06-02.md`를 먼저 읽고 현재 상태를 이어받아 주세요.

이 프로젝트의 목적은 AI 에이전트들이 변화하는 시장 데이터를 수집한 뒤 서로 회의/토론/검증하여 수익 기회를 판단하는 시스템을 만드는 것입니다. 현재 실거래/주문/잔고/출금/이체/자동매매는 금지되어 있고, public market data 기반 판단 시스템과 Council 구조를 개발 중입니다.

현재 핵심 blocker는 `live_tether_cross_market_premium`이 live packet을 생성하지 못하는 문제입니다. 원인은 global USDT reference adapters가 모두 실패하는 것입니다.

실패 로그:
- Binance: HTTP 400 for `https://api.binance.com/api/v3/ticker/bookTicker?symbol=USDTUSDC`
- Bybit: `Bybit reference status 10001: Not supported symbols`
- OKX: `OKX reference status 51001: Instrument ID, Instrument ID code, or Spread ID doesn't exist`

먼저 프로젝트 목적/전략 상태/현재 blocker를 요약하고, Codex에게 줄 작은 PR 단위 수정 요청문과 테스트 계획을 작성해 주세요.
```

---

## 11. 새 Codex 첫 메시지

Codex에게는 repo 안의 문서를 읽게 해야 한다.

권장 저장 경로:

```text
docs/AI_Council_Project_Handoff_v3_Strategy_Update_2026-06-02.md
```

Codex 첫 메시지:

```text
이전 대화가 길어져 새 작업으로 이어갑니다.

먼저 아래 파일을 반드시 읽고 현재 프로젝트 상태를 요약하세요.

`docs/AI_Council_Project_Handoff_v3_Strategy_Update_2026-06-02.md`

그 다음 아래 문서도 읽으세요.

- AGENTS.md
- docs/no_trade_policy.md
- docs/pr_handoffs/README.md
- docs/merge_gate.md
- docs/rollback_policy.md
- docs/task_checklist.md
- docs/agent_workflow.md
- docs/strategy_task_cards/tether_cross_market_premium.md

현재 작업은 기능 확장이 아니라 blocker 진단/수정입니다.

현재 blocker:
`live_tether_cross_market_premium` adapter가 등록되어 있지만 live packet 생성이 실패합니다.

실패 명령:
`python tools/collect_market_data.py --adapter live_tether_cross_market_premium --output data/generated_packets/live_tether_cross_market_packet.json`

실패 메시지:
`All global USDT reference adapters failed for live_tether_cross_market_premium: live_binance_usdt_reference, live_bybit_usdt_reference, live_okx_usdt_reference`

개별 adapter 실패:
- Binance: `HTTP status 400 for https://api.binance.com/api/v3/ticker/bookTicker?symbol=USDTUSDC`
- Bybit: `Bybit reference status 10001: Not supported symbols`
- OKX: `OKX reference status 51001: Instrument ID, Instrument ID code, or Spread ID doesn't exist`

요구사항:
1. 먼저 프로젝트 상태와 blocker 원인을 짧게 요약하세요.
2. 그 다음 “Tether Cross-Market Global Reference Diagnostics v0” 작업을 작은 PR로 수행하세요.
3. PR에는 반드시 `docs/pr_handoffs/tether_cross_market_global_reference_diagnostics_v0.md` 파일을 추가하세요.
4. private API, API key/secret/token, account/balance lookup, order/cancel, withdrawal/deposit/transfer, fiat/bank transfer, auto-trading, Council auto-call, active strategy promotion은 절대 추가하지 마세요.
5. global reference symbol/endpoint/parser 오류를 진단 가능하게 만들고, 최소 하나 이상의 global reference가 성공하면 composite packet을 생성할 수 있게 보수적으로 수정하세요.
6. 모든 변경은 PR template과 handoff evidence 기준을 만족해야 합니다.
```

---

## 12. 새 Codex에게 줄 실제 작업 압축 요청

```text
작업명: Tether Cross-Market Global Reference Diagnostics v0

목표:
`live_tether_cross_market_premium`의 global reference adapter 실패 원인을 진단 가능하게 만들고, Binance/Bybit/OKX public reference symbol/endpoint/parser 문제를 보수적으로 수정하세요. 국내 Upbit/Bithumb 쪽은 현재 실패 지점이 아닙니다.

허용 파일:
- src/market_data/adapters/global_usdt_reference.py
- src/market_data/adapters/composite.py
- src/market_data/registry.py
- configs/market_data.yaml
- tests/test_tether_cross_market_live_composite_adapter.py
- docs/pr_handoffs/tether_cross_market_global_reference_diagnostics_v0.md
- README 최소 수정

금지:
- private API
- API key/secret/token
- auth/private headers
- balance/account
- order/cancel
- transfer/withdraw/deposit
- fiat/bank transfer
- auto-trading
- Council handoff/auto-call
- active strategy 변경
- Gemini runtime/prompt 변경

필수:
- global reference 실패 시 adapter_id, venue_id, endpoint, symbol, HTTP status, exchange error code/message, parser stage, safe response preview를 남기세요.
- Binance/Bybit/OKX 각각 mocked success/failure test를 추가하세요.
- composite는 domestic Upbit/Bithumb이 모두 있어야 하고, global reference는 최소 설정 개수 이상 성공해야 packet을 만들 수 있게 하세요.
- 모든 global reference가 실패하면 지금처럼 실패하되, 세 adapter별 구체적 진단을 포함하세요.
- `python -m unittest discover -s tests` 통과.
- 가능하면 수동 smoke:
  `python tools/collect_market_data.py --adapter live_tether_cross_market_premium --output data/generated_packets/live_tether_cross_market_packet.json`
```

---

## 13. 새 채팅에서 혼동하면 안 되는 것

- 현재 목적은 실거래 봇 완성이 아니라 **AI Council 기반 매매 판단 시스템**이다.
- 현재는 public data 기반 read-only 시스템이다.
- Tether 전략은 FX 기반 김프가 아니다.
- 현재 집중 전략은 `tether_cross_market_premium`.
- active 전략은 아직 `cross_exchange_spot_spread_v1`.
- `tether_cross_market_premium`은 experimental / non-active.
- 다음 작업은 global reference diagnostics.
- sampling/alert로 넘어가면 안 된다. live packet 생성이 먼저 성공해야 한다.

