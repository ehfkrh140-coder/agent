# AI Council Project Handoff v4 — Mark-Orderbook / Tether / Strategy Baseline Update

작성일: 2026-06-05  
대상 저장소: `https://github.com/ehfkrh140-coder/agent`  
권장 저장 위치: `docs/AI_Council_Project_Handoff_v4_Mark_Orderbook_Baseline_2026-06-05.md`

---

## 0. 이 문서의 목적

이 문서는 긴 GPT/Codex 협업 흐름을 새 GPT 채팅과 새 Codex 작업으로 안전하게 이어가기 위한 인수인계 문서다.

기존 인수인계 파일들은 Gemini CLI 기반 5-agent runtime, Tether blocker, Strategy Update 등을 다뤘다. 이 v4 문서는 2026-06-05 기준으로 **AI Council 기반 read-only 매매 판단 시스템의 전략 개발 상태**를 최신화한다.

이 문서가 전달해야 하는 핵심은 다음이다.

```text
1. 프로젝트 최종 목표
2. 현재 NO_TRADE_ONLY 개발 원칙
3. 지금까지 완성한 전략/인프라
4. Binance / Bybit / OKX Mark-Orderbook Gap Hunt baseline 현황
5. Tether Cross-Market blocker 해결 및 현재 상태
6. 문제와 해결 방식
7. 바로 다음에 할 일
8. 큰 틀에서 해야 할 일
9. GPT 설계자 역할
10. Codex에게 작업을 시키는 방식
```

---

## 1. 한 줄 요약

이 프로젝트는 지금 당장 자동매매 봇을 만드는 단계가 아니라, **public market data를 수집해 OpportunityPacket으로 표준화하고, deterministic readiness / sampling / evidence / AI Council 검토를 통해 매매 후보를 검증하는 AI Council 기반 매매 판단 시스템**을 만드는 중이다.

현재 기준으로 가장 큰 진전은 다음이다.

```text
Binance / Bybit / OKX 3대 거래소에 대해
Mark-Orderbook Gap Hunt 전략의 public-read-only adapter, parser/readiness, config/registry, collect smoke, sampling baseline, user-local 3-sample evidence까지 1차 연결이 완료되었다.
```

---

## 2. 매우 중요한 정정: 현재와 최종 목표의 차이

이 프로젝트는 최종적으로는 다음까지 갈 수 있다.

```text
시장 데이터 괴리 감지
→ AI Council 토론
→ deterministic risk/execution engine 검토
→ 실제 주문/청산/관리 자동화 가능성
```

하지만 현재 단계에서는 아래를 절대 구현하지 않는다.

```text
private API
API key / secret / token
계정 / 잔고 / 포지션 조회
주문 / 주문취소
출금 / 입금 / 이체
원화/은행 이체
자동매매
Council 판단을 바로 주문으로 전환
active strategy 무단 승격
```

따라서 현재 정책은 다음과 같이 이해해야 한다.

```text
최종 목표에는 execution/risk engine이 포함될 수 있다.
하지만 지금 개발 단계는 NO_TRADE_ONLY이다.
지금은 public data 기반 판단 시스템과 전략 검증 프레임을 쌓는 단계다.
```

---

## 3. 프로젝트 최종 목표

최종 목표는 단순 챗봇도, 단순 알림봇도 아니다.

목표는 다음과 같은 시스템이다.

```text
public market data 수집
→ exchange/venue별 raw response normalize
→ OpportunityPacket 표준화
→ deterministic readiness 판단
→ sampling / persistence / evidence
→ AI Council 검토
→ WATCH / REJECT / NEED_DATA / 분석상 ENTER 후보
→ 훗날 별도 execution/risk engine이 실제 주문 가능성 검토
```

AI Council이 검토해야 할 핵심 질문은 다음이다.

```text
이 가격/호가/mark 괴리가 진짜인가?
last_price 착시인가?
mark price는 체결 가능한 가격이 아닌데 bid/ask와 비교 가능한가?
수수료, 슬리피지, 버퍼 후에도 net gap이 남는가?
orderbook depth와 size unit이 신뢰 가능한가?
데이터 timestamp가 stale이거나 clock skew가 있는가?
특정 venue의 public endpoint 응답이 잘못 해석된 것은 아닌가?
여러 sample에서 반복되는가?
Council이 볼 가치가 있는 WATCH인가, 아니면 그냥 REJECT인가?
```

---

## 4. 현재 아키텍처 개요

현재 repo의 핵심 구조는 다음 흐름으로 이해하면 된다.

```text
market_data adapter
→ parser / normalized snapshot
→ OpportunityPacket
→ readiness helper
→ sampling summary
→ handoff evidence / journal / alert 후보
→ Council dry-run 또는 manual review
```

주요 경로:

```text
src/market_data/
- public read-only adapters
- replay adapters
- composite adapters
- packet_builder
- sampling
- http_client

src/market_data/adapters/
- global_usdt_reference.py
- composite.py
- mark_orderbook_gap_hunt.py

src/market_data/parsers/
- mark_orderbook_gap_hunt.py

src/strategy/
- mark_orderbook_gap_hunt_readiness.py
- tether/cross strategy readiness helpers

tools/
- collect_market_data.py
- sample_market_data.py
- run_strategy_scenarios.py

docs/pr_handoffs/
- 각 PR/작업 단위 evidence source-of-truth
```

---

## 5. 현재 전략 상태

### 5.1 Active strategy

```text
strategy_family: cross_exchange_spot_spread
strategy_id: cross_exchange_spot_spread_v1
status: active
execution_policy: NO_TRADE_ONLY
```

목적:

```text
국내 Upbit/Bithumb public spot orderbook 기반 executable spread 감지
```

핵심 원칙:

```text
last_price 차이만으로 판단 금지
source ask / target bid 또는 VWAP 기준
fee + slippage + safety buffer 반영
readiness_pass=false이면 ENTER 금지
```

현재 역할:

```text
이 프로젝트의 active baseline이다.
다른 전략은 아직 experimental / non-active이다.
```

---

### 5.2 Experimental: tether_cross_market_premium / usdt_krw_global_reference_v0

```text
strategy_family: tether_cross_market_premium
strategy_id: usdt_krw_global_reference_v0
status: experimental / non-active / NO_TRADE_ONLY
```

정의:

```text
국내 Upbit/Bithumb USDT/KRW 가격·호가·뎁스를 비교하고,
해외 Binance/Bybit/OKX global USDT reference health를 확인해,
국내 테더 시장의 스프레드 / 왜곡 / depeg risk를 감지하는 read-only 전략.
```

중요:

```text
FX / USD-KRW / fair_usdt_krw_price 계산은 현재 범위 밖이다.
해외 거래소는 현재 execution venue가 아니라 reference/depeg health 용도다.
```

현재 상태:

```text
global reference blocker 해결됨.
Binance/Bybit: USDCUSDT
OKX: USDC-USDT
normalize: inverse
min_successful_global_references: 1
user-local live packet smoke 성공
3-sample / 30-sample sampling evidence 성공
successful_global_reference_count=3 evidence 존재
NO_PERSISTENT_EDGE / REJECT는 정상 no-edge로 해석됨
```

기존 v3 문서의 blocker였던 `USDTUSDC`, Bybit unsupported symbol, OKX instrument missing 문제는 이후 diagnostics/inverse normalization 작업으로 해결되었다.

---

### 5.3 Experimental: orderbook_imbalance_v0

```text
strategy_family: orderbook_imbalance
strategy_id: orderbook_imbalance_v0
status: experimental / non-active / NO_TRADE_ONLY
```

정의:

```text
bid/ask depth imbalance를 감지해 수급 쏠림을 관찰하는 실험 전략.
```

중요:

```text
executable spread 전략이 아니다.
estimated_net_gap_pct 중심 전략이 아니다.
active가 아니다.
```

---

### 5.4 Experimental: mark_orderbook_gap_hunt_v0

```text
strategy_family: mark_orderbook_gap_hunt
strategy_id: mark_orderbook_gap_hunt_v0
status: experimental / non-active / NO_TRADE_ONLY
```

정의:

```text
derivatives venue의 mark price와 실제 executable orderbook bid/ask 사이 괴리를 감지한다.
```

핵심 공식:

```text
long_gap_pct = ((mark_price - ask) / mark_price) * 100
short_gap_pct = ((bid - mark_price) / mark_price) * 100
max_observed_gap_pct = max(long_gap_pct, short_gap_pct)
estimated_net_gap_pct = max_observed_gap_pct - fee_slippage_buffer_pct
```

중요:

```text
mark price는 체결가가 아니다.
WATCH는 analysis-only이다.
REJECT는 실패가 아니라 no-edge일 수 있다.
수수료/슬리피지/buffer 이후 net gap이 양수가 아니면 REJECT가 정상이다.
```

현재 1차 baseline:

```text
Binance: collect / 3-sample / 30-sample extended evidence 완료
Bybit: collect / 3-sample sampling evidence 완료
OKX: collect / 3-sample sampling evidence 완료
```

---

## 6. Binance / Bybit / OKX Mark-Orderbook Gap Hunt 진행 현황

### 6.1 Binance

완료:

```text
public source probe
metadata evidence
mocked parser fixtures
production parser support: binance_usdm
readiness helper
runtime adapter
user-local direct smoke
config/registry registration
collect_market_data official smoke
sampling baseline planning
sampling baseline implementation
user-local 3-sample sampling smoke
user-local 30-sample extended sampling evidence
```

대표 sampling 결과:

```text
samples_ok=30
samples_error=0
candidate_seen_count=30
REJECT=30
positive_net_gap_count=0
NO_PERSISTENT_EDGE
council_recommended=False
NO_TRADE_ONLY 유지
```

해석:

```text
Binance public data path와 sampling pipeline은 안정적이다.
그러나 profitability나 persistent edge는 증명하지 않는다.
```

---

### 6.2 Bybit

완료:

```text
public source/metadata planning
production parser support: bybit_linear
runtime adapter
user-local direct smoke
config/registry planning
config/registry registration
collect_market_data official smoke
collect evidence
sampling baseline planning
sampling baseline implementation
user-local 3-sample sampling evidence
```

대표 3-sample 결과:

```text
samples_ok=3
samples_error=0
REJECT=3
NO_PERSISTENT_EDGE
council_recommended=False
NO_TRADE_ONLY 유지
```

Watch item:

```text
negative data_age_ms가 반복 관찰된 evidence가 있다.
이는 exchange timestamp와 local collection timestamp alignment / clock skew 가능성으로 분리한다.
현재는 blocker가 아니며 timestamp policy task로 defer한다.
```

---

### 6.3 OKX

완료:

```text
public source probe
metadata evidence
production parser support: okx_swap
runtime adapter
user-local direct smoke
OKX config/registry planning
OKX config/registry registration
official collect_market_data smoke
collect evidence
metadata wording cleanup
sampling baseline planning
sampling baseline mocked implementation
sampling summary path triage
user-local 3-sample sampling smoke evidence
```

대표 3-sample 결과:

```text
samples_ok=3
samples_error=0
candidate_seen_count=3
positive_gross_gap_count=3
positive_net_gap_count=0
REJECT=3
NO_PERSISTENT_EDGE
council_recommended=False
index_price_null_count=3
index_price_null_observed=True
timestamp_data_age_watch_count=0
negative_data_age_observed=False
stale_assumption_wording_count=0
stale_assumption_wording_observed=False
NO_TRADE_ONLY 유지
```

해석:

```text
OKX 1차 baseline 완료.
index_price=None은 OKX index/reference semantics watch item으로 유지.
이번 run에서는 data_age_ms가 양수라 timestamp watch 없음.
metadata wording cleanup도 새 packet에 반영됨.
```

---

## 7. 지금까지 생긴 주요 문제와 해결 방식

### 7.1 Codex PR title/body가 너무 generic하거나 cumulative로 보이는 문제

문제:

```text
Codex PR title/body가 실제 step보다 훨씬 큰 범위처럼 보이는 경우가 많았다.
changed_files도 누적 브랜치처럼 크게 보이는 경우가 있었다.
```

해결:

```text
step-specific handoff file을 source-of-truth로 삼는다.
Codex 최종 보고와 docs/pr_handoffs/<task>.md를 기준으로 실제 작업 범위를 판단한다.
필수 changed files list를 항상 요구한다.
```

계속 유지할 규칙:

```text
PR title/body만 믿지 않는다.
GitHub merged 여부는 확인한다.
하지만 실제 작업 판단은 handoff evidence와 changed files 기준으로 한다.
```

---

### 7.2 Codex workspace live network 403 문제

문제:

```text
Codex workspace에서 Upbit/Bithumb/Binance/Bybit/OKX public endpoint가 tunnel 403으로 실패할 수 있다.
```

해결:

```text
Codex는 mocked tests / unit tests / parser/readiness tests 중심으로 검증한다.
실제 live smoke는 사용자 로컬 정상 네트워크에서 실행한다.
user-local evidence는 docs-only PR로 기록한다.
```

---

### 7.3 Tether global reference symbol 문제

기존 문제:

```text
Binance: USDTUSDC HTTP 400
Bybit: Not supported symbols
OKX: Instrument ID doesn't exist
```

해결:

```text
USDCUSDT / USDC-USDT 방향으로 public symbol 후보를 바꿨다.
USDT reference 관점에서는 inverse normalization을 적용했다.
ticker_candidates와 per-candidate diagnostics를 추가했다.
min_successful_global_references=1 baseline을 도입했다.
```

현재 상태:

```text
user-local live/sampling evidence에서 Binance/Bybit/OKX global references 모두 성공.
```

---

### 7.4 `Unsupported strategy_family: mark_orderbook_gap_hunt`

문제:

```text
adapter는 OpportunityPacket dict를 만들었지만 packet_builder가 mark_orderbook_gap_hunt strategy_family를 몰라 collect_market_data에서 실패했다.
```

해결:

```text
OpportunityPacketBuilder에 mark_orderbook_gap_hunt validation path 추가.
collect_market_data official path 성공.
```

---

### 7.5 `market_sampling_v1` summary field를 잘못 읽은 문제

문제:

```text
OKX sampling result에서 samples_ok 등 aggregate fields를 top-level에서 읽어 None으로 보였다.
```

원인:

```text
market_sampling_v1은 top-level envelope + nested summary object 구조다.
aggregate fields는 payload["summary"] 아래에 있다.
```

해결:

```text
inspection path clarification.
테스트에서 result["summary"] 아래 aggregate fields 검증.
```

올바른 확인 방식:

```python
summary = payload["summary"]
summary["samples_ok"]
summary["candidate_seen_count"]
summary["persistence_status"]
```

---

### 7.6 stale adapter assumption wording 문제

문제:

```text
초기 standalone adapter packet assumptions에
"no config registration in this PR"
"no registry integration in this PR"
같은 과거 PR-stage 문구가 남았다.
```

해결:

```text
runtime-neutral wording으로 cleanup.
향후 generated packet에서는 stale wording false 확인.
```

현재 OKX sampling evidence:

```text
stale_assumption_wording_count=0
stale_assumption_wording_observed=False
```

---

### 7.7 OKX `index_price=None`

문제:

```text
OKX mark/books/instruments 기반 packet에서 index_price가 None이다.
```

현재 판단:

```text
required_missing_fields=[]
parser_normalized_status=OK
readiness_status=REJECT
packet creation success
따라서 현재 blocker 아님.
```

처리:

```text
OKX index/reference semantics watch item으로 유지.
별도 task candidate: Mark-Orderbook Gap OKX Index/Reference Semantics v0
```

---

### 7.8 negative data_age_ms / clock skew

문제:

```text
Bybit와 일부 OKX collect에서 data_age_ms가 음수로 관찰됨.
```

현재 판단:

```text
exchange timestamp가 local packet created_at보다 미래일 수 있다.
clock skew / timestamp alignment issue로 본다.
parser OK, freshness pass, endpoint OK, packet 생성 성공이면 blocker 아님.
```

처리:

```text
watch item으로 유지.
별도 task candidate: Market Data Timestamp Freshness / Clock Skew Policy v0
```

---

## 8. GPT 역할 인수인계

새 GPT는 단순 답변자가 아니라 **세계 최고 수준의 코딩 설계자 / 초보자 친화적 아키텍트 / Codex 작업 지휘자** 역할을 해야 한다.

응답 스타일:

```text
1. 사용자의 테스트 결과를 먼저 성공/실패/보류로 판정한다.
2. 초보자 눈높이로 왜 성공인지, 왜 실패인지 설명한다.
3. REJECT / false / None / WATCH 같은 값을 실패로 오해하지 않게 해석한다.
4. Codex에게 줄 요청문은 작은 PR 단위로 작성한다.
5. Codex에게 너무 넓은 작업을 시키지 않는다.
6. 사용자가 직접 해야 할 테스트가 있으면 PowerShell 명령어를 정확히 준다.
7. generated JSON은 commit 금지라고 반복 확인한다.
8. no-trade / handoff evidence / merge gate / rollback / human review를 유지한다.
9. 다음 단계로 갈 수 있는지 항상 판정한다.
10. 최신 GitHub 상태가 필요하면 확인한다.
```

반복되는 판정 언어:

```text
성공입니다.
실패가 아니라 no-edge REJECT입니다.
지금은 blocker가 아니라 watch item입니다.
바로 evidence PR로 가면 안 되고 triage가 먼저입니다.
다음 단계로 가도 됩니다.
이번 PR은 docs-only입니다.
이번 PR은 mocked-first implementation입니다.
user-local smoke는 별도 evidence입니다.
```

---

## 9. Codex 작업 방식

Codex에게는 반드시 다음 방식으로 시킨다.

```text
1. 최신 main에서 fresh branch 시작.
2. 먼저 관련 docs/handoff/source/test 파일을 읽게 한다.
3. 작업명 명시.
4. 이번 PR 목표와 out-of-scope 명시.
5. 허용 파일 / 금지 파일 명시.
6. private/execution/alert/Council 금지 항목 명시.
7. 테스트 명령어 명시.
8. 필수 handoff file 요구.
9. 최종 응답 형식 요구.
10. git diff --name-only HEAD~1..HEAD 결과 요구.
```

Codex에게 절대 이렇게 말하지 않는다.

```text
전체 다 개발해줘.
자동매매까지 만들어줘.
거래소 API 붙여줘.
알림 붙이고 Council 자동 호출까지 해줘.
공통화까지 한 번에 해줘.
```

---

## 10. 바로 다음에 할 일

현재 OKX 1차 baseline이 끝났으므로 다음 선택지는 두 가지다.

### 추천 1순위: Bybit / OKX 30회 extended sampling evidence

이유:

```text
Binance는 이미 30회 extended evidence가 있다.
Bybit와 OKX는 3-sample smoke까지만 있다.
세 거래소 비교를 하려면 Bybit/OKX도 30회 evidence를 맞추는 것이 좋다.
```

후보 작업:

```text
Mark-Orderbook Gap Hunt Bybit Extended Sampling Evidence v0
Mark-Orderbook Gap Hunt OKX Extended Sampling Evidence v0
```

사용자 로컬 명령 후보:

```powershell
python tools/sample_market_data.py --adapter live_bybit_mark_orderbook_gap_btcusdt --samples 30 --interval 2 --output data/market_samples/mark_orderbook_gap_bybit_sampling_30x_summary.json

python tools/sample_market_data.py --adapter live_okx_mark_orderbook_gap_btc_usdt_swap --samples 30 --interval 2 --output data/market_samples/mark_orderbook_gap_okx_sampling_30x_summary.json
```

주의:

```text
generated sampling JSON commit 금지.
먼저 사용자가 실행하고 결과 요약을 GPT에게 전달.
GPT가 성공 판정 후 Codex evidence-only PR 요청.
```

---

### 추천 2순위: Binance/Bybit/OKX commonization planning

후보 작업:

```text
Mark-Orderbook Gap Hunt Venue Adapter Commonization Planning v0
```

목표:

```text
Binance/Bybit/OKX adapter에서 반복되는 구조를 비교한다.
공통화할 수 있는 부분과 venue-specific으로 남길 부분을 분리한다.
아직 base adapter 구현은 하지 않는다.
```

공통화 후보:

```text
public fetch diagnostics
parser/readiness invocation
OpportunityPacket identity mapping
candidate mapping
NO_TRADE_ONLY metadata
assumptions/warnings
safe diagnostics
sampling interpretation
```

venue-specific으로 남길 것:

```text
endpoint path
symbol/instId/category/instType format
response code format
timestamp semantics
metadata fields
contract/lot/notional interpretation
index/reference semantics
```

---

### 추천 3순위: policy watch items

후보 작업:

```text
Market Data Timestamp Freshness / Clock Skew Policy v0
Mark-Orderbook Gap OKX Index/Reference Semantics v0
```

현재는 바로 구현하지 말고, 30회 extended evidence 또는 commonization planning 이후가 더 좋다.

---

## 11. 큰 틀의 향후 로드맵

### Near-term

```text
1. Bybit 30회 extended sampling evidence
2. OKX 30회 extended sampling evidence
3. Binance/Bybit/OKX commonization planning
4. Timestamp/data_age policy planning
5. OKX index/reference semantics planning
```

### Mid-term

```text
1. Mark-Orderbook Gap multi-venue comparative summary
2. repeated WATCH / persistence policy 강화
3. Council review candidate handoff 기준 정리
4. alert/notification common layer planning
5. 전략별 evidence dashboard/journal 보강
```

### Long-term

```text
1. Spot-Futures Basis strategy
2. Funding Rate strategy
3. Trade Flow Momentum
4. Open Interest / Liquidation data strategy
5. News/Event strategy
6. On-chain strategy
7. Common execution/risk engine planning
8. dry-run / paper trading
9. credential isolation
10. kill switch / audit log / rollback plan
11. 실제 주문 자동화는 가장 마지막 단계
```

---

## 12. 현재 매매법 카탈로그

### Strategy 01. Cross-Exchange Spot Executable Spread

```text
상태: active / NO_TRADE_ONLY
핵심: source ask / target bid / VWAP 기반 실제 체결 가능 spread
```

### Strategy 02. Tether Cross-Market Premium

```text
상태: experimental / non-active / NO_TRADE_ONLY
핵심: 국내 USDT/KRW + global USDT reference health
```

### Strategy 03. Orderbook Imbalance

```text
상태: experimental / non-active / NO_TRADE_ONLY
핵심: bid/ask depth imbalance 관찰
```

### Strategy 04. Mark-Orderbook Gap Hunt

```text
상태: experimental / non-active / NO_TRADE_ONLY
핵심: mark price와 bid/ask 괴리 관찰
현재: Binance/Bybit/OKX 1차 baseline 완료
```

### Strategy 05. Domestic/Global Premium/Discount

```text
상태: future
핵심: 국내 가격과 해외 reference 괴리
```

### Strategy 06. Spot-Futures Basis

```text
상태: future
핵심: spot vs futures/perp basis
```

### Strategy 07. Funding Rate Strategy

```text
상태: future
핵심: funding rate / next funding / basis / OI
```

### Strategy 08. Trade Flow Momentum

```text
상태: future
핵심: recent trades, buy/sell volume imbalance
```

### Strategy 09. Volatility Breakout

```text
상태: future
핵심: OHLCV / ATR / breakout level / volume
```

### Strategy 10. Mean Reversion

```text
상태: future
핵심: spread z-score / historical mean/std
```

### Strategy 11. Grid Strategy

```text
상태: future research
핵심: range-bound / grid spacing / inventory
```

### Strategy 12. Market Making

```text
상태: long-term future
핵심: quote both sides / inventory / cancel latency
주의: private/execution 필요하므로 매우 나중
```

### Strategy 13. Liquidation Data Strategy

```text
상태: future
핵심: liquidation cluster / price reaction / OI
```

### Strategy 14. Open Interest Strategy

```text
상태: future
핵심: OI change + price + funding interpretation
```

### Strategy 15. News / Event Strategy

```text
상태: future
핵심: listing/regulation/hack/ETF/macro event
```

### Strategy 16. On-chain Strategy

```text
상태: future
핵심: exchange inflow/outflow / whale transfers
```

---

## 13. 다음 GPT 채팅 첫 메시지

새 GPT 채팅에는 이 문서 파일을 첨부하고 아래 메시지를 붙여넣는다.

```text
나는 GitHub repo `https://github.com/ehfkrh140-coder/agent`에서 AI Council 기반 read-only 매매 판단 시스템을 개발 중입니다.

첨부한 `AI_Council_Project_Handoff_v4_Mark_Orderbook_Baseline_2026-06-05.md`를 먼저 읽고 현재 프로젝트 상태를 이어받아 주세요.

당신의 역할은 단순 코딩 도우미가 아니라, 세계 최고 수준의 코딩 설계자이자 초보자인 나에게 쉽게 설명해주는 아키텍트입니다.

앞으로 우리는 이런 루프로 개발합니다.

1. 내가 Codex 결과나 테스트 결과를 붙여넣습니다.
2. 당신은 먼저 성공/실패/보류 여부를 판정합니다.
3. 초보자인 내가 이해할 수 있게 왜 그런지 설명합니다.
4. 다음 단계로 가도 되는지 판단합니다.
5. Codex에게 줄 작은 PR 단위 요청문을 작성합니다.
6. 내가 직접 테스트해야 할 경우 PowerShell 명령어와 성공 기준을 줍니다.
7. no-trade policy, PR handoff evidence, merge gate, rollback, generated JSON commit 금지를 계속 유지합니다.

중요한 현재 상태:
- active strategy는 `cross_exchange_spot_spread_v1`입니다.
- `tether_cross_market_premium / usdt_krw_global_reference_v0`는 experimental / non-active / NO_TRADE_ONLY입니다.
- `orderbook_imbalance_v0`도 experimental / non-active / NO_TRADE_ONLY입니다.
- `mark_orderbook_gap_hunt_v0`는 Binance / Bybit / OKX 3개 venue에 대해 1차 baseline이 완료되었습니다.
- Binance는 30-sample extended sampling evidence까지 완료되었습니다.
- Bybit와 OKX는 3-sample sampling smoke evidence까지 완료되었습니다.
- OKX는 index_price=None watch item이 있고, Bybit/일부 OKX collect에는 negative data_age_ms watch item이 있습니다.
- generated packet/sampling JSON은 smoke artifact이며 commit 금지입니다.
- Codex PR title/body는 generic/cumulative로 보일 수 있으므로 step-specific `docs/pr_handoffs/*.md`를 source-of-truth로 봐야 합니다.

현재 바로 다음 후보는 두 가지입니다.
1. Bybit/OKX 30회 extended sampling evidence를 먼저 맞춘다.
2. Binance/Bybit/OKX commonization planning을 시작한다.

먼저 이 문서를 읽고 현재 상태를 10줄 이내로 요약한 뒤, 다음 단계로 무엇이 가장 좋은지 추천해 주세요.
```

---

## 14. 새 Codex 첫 메시지

Codex는 파일 첨부를 직접 읽기 어렵기 때문에, 이 MD 파일을 GitHub repo 안에 업로드/커밋한 뒤 아래처럼 지시한다.

권장 저장 경로:

```text
docs/AI_Council_Project_Handoff_v4_Mark_Orderbook_Baseline_2026-06-05.md
```

Codex 첫 메시지:

```text
반드시 최신 origin/main 기준으로 새 브랜치를 만들어 작업하세요.
오래된 PR, 오래된 작업 브랜치, 캐시된 워크스페이스 기준으로 작업하지 마세요.
응답 Summary와 설명은 반드시 한국어로 작성하세요.

먼저 아래 인수인계 문서를 반드시 읽고 현재 프로젝트 상태를 10줄 이내로 요약하세요.

`docs/AI_Council_Project_Handoff_v4_Mark_Orderbook_Baseline_2026-06-05.md`

그 다음 아래 governance 문서도 읽으세요.

- AGENTS.md
- docs/no_trade_policy.md
- docs/pr_handoffs/README.md
- docs/merge_gate.md
- docs/rollback_policy.md
- docs/task_checklist.md
- docs/agent_workflow.md

중요한 전제:
이 프로젝트의 최종 목표는 언젠가 execution/risk engine까지 포함하는 AI Council 기반 매매 시스템입니다.
하지만 현재 단계와 이번 PR 범위에서는 NO_TRADE_ONLY를 반드시 유지합니다.

현재 상태:
- active strategy는 cross_exchange_spot_spread_v1입니다.
- mark_orderbook_gap_hunt_v0는 experimental / non-active / NO_TRADE_ONLY입니다.
- Binance / Bybit / OKX Mark-Orderbook Gap Hunt 1차 baseline은 완료되었습니다.
- Binance는 30-sample extended evidence까지 완료되었습니다.
- Bybit와 OKX는 3-sample user-local sampling evidence까지 완료되었습니다.
- Codex live network는 403 tunnel 문제가 있을 수 있으므로 live smoke는 user-local evidence로 분리합니다.
- generated packet/sampling JSON은 commit 금지입니다.
- Codex PR title/body는 cumulative처럼 보일 수 있으므로 step-specific handoff file을 source-of-truth로 봅니다.

이번 작업은 아직 시작하지 마세요.
먼저 현재 상태를 요약하고, 다음 단계 후보를 아래 3개 중에서 비교해 제안하세요.

A. Bybit 30-sample extended sampling evidence planning/request
B. OKX 30-sample extended sampling evidence planning/request
C. Mark-Orderbook Gap Hunt Venue Adapter Commonization Planning v0

아직 code/config/test를 수정하지 마세요.
먼저 계획과 추천만 제시하세요.

응답에는 반드시 아래 섹션을 포함하세요.

[프로젝트 상태 10줄 요약]
[다음 단계 후보 비교]
[추천 순서]
[이번에 바로 하면 안 되는 것]
[필요한 user-local 테스트]
[No-trade compliance]
```

---

## 15. GitHub에 이 MD 파일을 업로드하는 방법

PowerShell 기준:

```powershell
cd C:\Users\qhrb9\Desktop\agent

git checkout main
git pull --ff-only

git checkout -b docs/handoff-v4-mark-orderbook-baseline

# 다운로드한 MD 파일을 아래 경로로 복사
# docs\AI_Council_Project_Handoff_v4_Mark_Orderbook_Baseline_2026-06-05.md

git status --short
git add docs\AI_Council_Project_Handoff_v4_Mark_Orderbook_Baseline_2026-06-05.md
git commit -m "Add AI Council project handoff v4"
git push -u origin docs/handoff-v4-mark-orderbook-baseline
```

그 다음 GitHub에서 PR을 만들고 merge한다.

Merge 후 Codex에게는 위 14번 메시지를 보낸다.

---

## 16. 다음 채팅 시작 전 체크리스트

```text
1. generated JSON 삭제 확인
2. git status --short clean 확인
3. handoff v4 MD를 새 GPT에 첨부
4. handoff v4 MD를 GitHub docs/에 커밋
5. 새 GPT에게 이 문서 읽게 하기
6. 새 Codex에게 docs 경로 읽게 하기
```

PowerShell cleanup:

```powershell
Remove-Item data\generated_packets\*.json -ErrorAction SilentlyContinue
Remove-Item data\market_samples\*.json -ErrorAction SilentlyContinue
git status --short
```

단, repo에서 intentionally tracked fixture/sample 파일이 있다면 무작정 삭제하지 말고 `git status --short` 기준으로 untracked/generated artifact만 확인한다.

---

## 17. 최종 인수인계 결론

현재 기준 결론:

```text
Cross-Exchange Spot Spread: active baseline
Tether Cross-Market Premium: experimental, blocker 해결, sampling evidence 확보
Orderbook Imbalance: experimental baseline
Mark-Orderbook Gap Hunt: Binance/Bybit/OKX 1차 baseline 완료
```

다음 큰 목표:

```text
1. Bybit/OKX extended sampling evidence로 Binance와 비교 기준 맞추기
2. Binance/Bybit/OKX commonization planning
3. timestamp/data_age policy planning
4. OKX index/reference semantics planning
5. 그 뒤 다음 전략 또는 common Council/alert layer 검토
```

현재 단계에서 계속 금지:

```text
private API
credentials
account/balance/position
order/cancel
withdraw/deposit/transfer
auto-trading
Council auto-call to execution
active promotion
```

