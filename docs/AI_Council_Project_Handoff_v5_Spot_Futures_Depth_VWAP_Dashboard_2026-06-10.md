# AI Council Project Handoff v5 — Spot-Futures / Depth-VWAP / Dashboard / Council Status Update

작성일: 2026-06-10  
대상 저장소: `https://github.com/ehfkrh140-coder/agent`  
권장 저장 위치: `docs/AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md`

---

## 0. 이 문서의 목적

이 문서는 긴 GPT + Codex 협업 흐름을 새 GPT 채팅과 새 Codex 작업으로 안전하게 이어가기 위한 **v5 인수인계 문서**다.

기존 v4 문서는 Mark-Orderbook / Tether / Strategy Baseline 상태를 정리했다. v5는 그 이후 우리가 새로 진행한 다음 큰 흐름까지 포함한다.

```text
1. Mark-Orderbook Gap Hunt v0 3-venue baseline close-out
2. Spot-Futures Basis v0 Binance + Bybit baseline 구축
3. Strategy Evidence Dashboard / Journal Summary 구축
4. Council Review Handoff Criteria 수립
5. Timestamp / Clock-Skew 공통 정책 정리
6. Depth/VWAP planning → helper → fixtures → packet context → sampling summary → dashboard status 완료
7. 다음 experimental strategy selection 단계 진입
```

이 문서의 목표는 새 GPT와 새 Codex가 다음을 즉시 이해하는 것이다.

```text
우리는 지금 자동매매를 구현하는 것이 아니다.
public market data 기반 read-only 매매 후보 검증 시스템을 만들고 있다.
각 전략은 OpportunityPacket → readiness → sampling → evidence → dashboard → Council manual review 흐름으로 검증된다.
현재 정책은 계속 NO_TRADE_ONLY이다.
```

---

## 1. 초간단 한 줄 요약

이 프로젝트는 **AI Council 기반 read-only 매매 판단 시스템**을 만드는 중이며, 현재는 자동매매가 아니라 public data 기반으로 매매 후보를 검증하는 연구실을 만드는 단계다.

현재 가장 큰 진전은 다음이다.

```text
Mark-Orderbook Gap Hunt v0:
Binance / Bybit / OKX 3-venue baseline complete.

Spot-Futures Basis v0:
Binance + Bybit baseline complete, OKX deferred.

Depth/VWAP:
계산 helper, mocked fixtures, packet/candidate context, sampling summary, dashboard status까지 완료.

Dashboard / Council:
strategy evidence dashboard, council_handoff_status, depth_vwap_status가 반영됨.

다음 큰 단계:
Next Experimental Strategy Selection v0.
추천 후보는 Funding Rate Context Strategy.
```

---

## 2. 현재와 최종 목표의 차이

최종적으로는 아래처럼 발전할 수 있다.

```text
시장 데이터 괴리 감지
→ OpportunityPacket 표준화
→ deterministic readiness 판단
→ sampling / persistence evidence
→ AI Council manual review
→ 훗날 별도 risk/execution engine 검토
→ 실제 주문 가능성 검토
```

하지만 현재는 절대 아래를 하지 않는다.

```text
private API
API key / secret / token
계정 / 잔고 / 포지션 조회
주문 / 주문취소
출금 / 입금 / 이체
자동매매
alert 실행
Council auto-call
Council 판단을 바로 주문으로 전환
experimental strategy active promotion
```

현재 정책은 다음 한 문장으로 이해한다.

```text
지금은 돈을 버는 버튼을 만드는 단계가 아니라,
돈을 벌 가능성이 있는 후보를 검증하는 판단 시스템을 만드는 단계다.
```

---

## 3. 현재 아키텍처 큰 그림

현재 repo 흐름은 다음과 같다.

```text
public market data adapter
→ venue-specific parser / normalized observation
→ OpportunityPacket
→ readiness helper
→ packet/candidate metrics
→ sampling summary
→ docs/pr_handoffs evidence
→ strategy_evidence_dashboard
→ Council manual review criteria
```

중요한 source-of-truth는 다음이다.

```text
docs/pr_handoffs/*.md
```

Codex PR title/body는 가끔 cumulative하거나 generic하게 보일 수 있다. 따라서 실제 작업 범위는 항상 다음 순서로 판단한다.

```text
1. GitHub Files changed
2. Codex final report의 changed files
3. docs/pr_handoffs/<task>.md
4. test 결과
5. generated JSON path clean 여부
```

---

## 4. 현재 active / experimental 전략 상태

### 4.1 Active baseline

```text
strategy_family: cross_exchange_spot_spread
strategy_id: cross_exchange_spot_spread_v1
status: active baseline
execution_policy: NO_TRADE_ONLY
```

역할:

```text
현재 repo의 active baseline.
다른 전략은 experimental / proposed / non-active.
이번 v5까지 active strategy 변경은 없었다.
```

---

### 4.2 Experimental: mark_orderbook_gap_hunt_v0

```text
strategy_family: mark_orderbook_gap_hunt
strategy_id: mark_orderbook_gap_hunt_v0
status: experimental / non-active / NO_TRADE_ONLY
venue coverage: Binance / Bybit / OKX
current dashboard status: NO_EDGE_ARCHIVE + POLICY_REVIEW
```

정의:

```text
derivatives venue의 mark price와 실제 orderbook bid/ask 사이 괴리를 감지한다.
```

핵심 주의:

```text
mark price는 체결 가능한 가격이 아니다.
REJECT는 실패가 아니라 no-edge일 수 있다.
WATCH도 ENTER가 아니다.
```

현재 완료 상태:

```text
Binance / Bybit / OKX public adapter / parser / readiness / registry / sampling baseline complete.
30-sample evidence complete.
comparative summary complete.
active promotion 없음.
alert 없음.
Council auto-call 없음.
execution 없음.
```

남은 watch item:

```text
timestamp_data_age_watch
negative_data_age_watch
OKX index_price=None / index reference semantics
mark_price_not_executable
top_of_book_liquidity_not_fill_feasibility
```

---

### 4.3 Experimental: spot_futures_basis_v0

```text
strategy_family: spot_futures_basis
strategy_id: spot_futures_basis_v0
status: proposed / experimental / non-active / NO_TRADE_ONLY
venue coverage: Binance + Bybit complete, OKX deferred
current dashboard status: NO_EDGE_ARCHIVE + POLICY_REVIEW
```

정의:

```text
spot market reference와 futures/perpetual market reference 사이의 basis를 관찰한다.
```

현재 완료 상태:

```text
Planning complete.
Common source contract planning complete.
Binance endpoint/source research complete.
Binance mocked fixtures complete.
Binance parser/readiness/packet builder/adapter/registry complete.
Binance collect smoke + 3x + 30x sampling evidence complete.
Bybit source research / fixtures / parser / packet compatibility / adapter / registry complete.
Bybit collect smoke + 3x + 30x sampling evidence complete.
Binance + Bybit comparative summary complete.
OKX deferred.
```

결론:

```text
두 venue 모두 sampling path는 성공.
하지만 positive net basis / persistent edge evidence는 없음.
REJECT / NO_PERSISTENT_EDGE가 정상 no-edge 결과.
```

남은 watch item:

```text
top-of-book liquidity is not fill feasibility
depth_vwap_not_implemented였으나 diagnostics/context path는 이제 지원됨
mark/index/funding are context, not executable
negative_data_age_watch
OKX deferred
```

---

### 4.4 Tether Cross-Market Premium / USDT-KRW Global Reference

```text
strategy_family: tether_cross_market_premium
strategy_id: usdt_krw_global_reference_v0
status: experimental / non-active / NO_TRADE_ONLY
```

현재 상태:

```text
global reference blocker 해결됨.
Binance / Bybit / OKX global reference health evidence 확보.
NO_PERSISTENT_EDGE / REJECT는 no-edge로 해석.
```

---

### 4.5 Orderbook Imbalance

```text
strategy_family: orderbook_imbalance
strategy_id: orderbook_imbalance_v0
status: experimental / non-active / NO_TRADE_ONLY
current council_handoff_status: NOT_REVIEW_READY 또는 future evidence row
```

---

## 5. 우리가 겪은 큰 고난과 해결 과정

### 5.1 Codex를 과소평가했던 문제

초기에는 Codex에게 아주 작은 작업만 시켰다. 그래서 채팅이 길어지고 사용자가 중간 전달을 너무 많이 해야 했다.

나중에 확인한 점:

```text
Codex는 빠르고 똑똑하다.
하지만 행동을 하나하나 잘 설계해줘야 깊게 잘한다.
```

현재 운영 방식:

```text
사용자에게는 쉽게 설명한다.
Codex에게는 긴 지시문으로 정확히 설계한다.
작업 단위는 예전보다 크게 한다.
다만 허용 파일 / 금지 파일 / tests / no-trade guardrail은 강하게 유지한다.
```

---

### 5.2 Codex PR title/body가 cumulative처럼 보이는 문제

문제:

```text
Codex PR 제목이 실제 작업보다 훨씬 커 보이는 경우가 있었다.
GitHub PR 목록이 정리되지 않았을 때 누적 PR처럼 보인 적도 있었다.
```

해결:

```text
GitHub Files changed를 반드시 확인한다.
Open PR이 누적되어 있으면 먼저 정리한다.
step-specific handoff가 source-of-truth다.
```

앞으로 Codex 작업 시작 전 필수 문구:

```text
최신 main 기준 fresh branch인지 확인하세요.
열린 PR이 누적되어 있거나 이번 작업과 무관한 파일이 섞일 가능성이 있으면 작업을 중단하고 보고하세요.
```

---

### 5.3 Codex workspace dependency 문제

Council Review Handoff Criteria Planning 당시 Codex workspace에서 다음 문제가 있었다.

```text
pydantic 없음
yaml 없음
test_auth_warmup_help_runs non-zero
```

사용자 로컬에서는 확인 결과:

```text
pydantic=2.13.4 import 성공
yaml import 성공
python -m unittest discover -s tests
Ran 451 tests, OK
```

해석:

```text
repo code failure가 아니라 Codex workspace dependency/environment issue.
```

이후 user-local verification correction을 docs-only로 반영했다.

---

### 5.4 generated JSON commit 금지

계속 반복된 핵심 규칙:

```text
data/generated_packets/*.json 는 smoke artifact
data/market_samples/*.json 는 smoke artifact
commit 금지
```

사용자 로컬 smoke/sampling 결과는 JSON 원본을 commit하지 않는다.

대신:

```text
summary 값만 docs/pr_handoffs/*.md에 기록한다.
```

---

### 5.5 Binance Spot exchangeInfo min_notional live-shape 문제

Spot-Futures Basis Binance collect smoke에서 처음에는 NEED_DATA가 나왔다.

원인:

```text
Binance Spot live exchangeInfo에서 min_notional filter shape가 mocked fixture와 달랐다.
NOTIONAL.minNotional / NOTIONAL.notional 등을 parser가 충분히 지원하지 못했다.
```

해결:

```text
Spot parser min_notional extraction alias 확장.
readiness missing field 중복 prefix 정리.
retry 결과 parser OK / required_missing_fields empty / REJECT로 정상 no-edge 확인.
```

---

### 5.6 Bybit orderbook category live-shape 문제

Bybit Spot-Futures collect smoke에서 처음에는 NEED_DATA가 나왔다.

원인:

```text
Bybit V5 orderbook response body는 category를 echo하지 않을 수 있는데 parser가 category를 필수로 기대했다.
```

해결:

```text
orderbook category missing은 허용하되, explicit wrong category는 mismatch로 유지.
retry 결과 spot/perp parser OK, required_missing_fields empty, REJECT로 정상 no-edge 확인.
```

---

### 5.7 negative data_age_ms / timestamp clock-skew

여러 venue에서 다음 값이 관찰되었다.

```text
data_age_ms < 0
```

초보자 입장에서는 오류처럼 보이지만, 현재 해석은 다음이다.

```text
거래소 timestamp가 local packet time보다 미래처럼 보이는 상황일 수 있다.
이 자체는 trading edge도 adapter failure도 아니다.
POLICY_REVIEW watch item이다.
```

Strategy-common timestamp / clock-skew policy planning을 완료했다.

핵심 정책:

```text
raw data_age_ms 보존
negative value clamp 금지
readiness behavior 변경 금지
warning-only부터 시작
```

---

### 5.8 top-of-book 착시와 Depth/VWAP

처음에는 top-of-book bid/ask만 사용했다.

문제:

```text
호가창 1단계 가격만 보면 실제 체결 가능성을 과대평가할 수 있다.
```

예시:

```text
ask 100원에 1개뿐인데 5개를 사려면
100원 1개 + 101원 2개 + 102원 2개를 사야 할 수 있다.
이때 평균 예상가는 101.2원이다.
```

해결 흐름:

```text
Depth/VWAP planning
→ pure helper implementation
→ mocked venue fixture contract tests
→ packet/candidate diagnostics context integration
→ sampling summary context aggregation
→ dashboard Depth/VWAP status update
```

중요:

```text
VWAP는 아직 매매 판단에 쓰지 않는다.
VWAP-adjusted readiness는 구현하지 않았다.
VWAP context는 diagnostics-only 참고 정보다.
```

---

## 6. Depth/VWAP 진행 현황 상세

현재 Depth/VWAP는 다음까지 완료됐다.

```text
1. Strategy-Common Depth / VWAP Planning v0
2. Depth / VWAP Pure Helper Implementation v0
3. Depth / VWAP Mocked Fixture Files + Contract Tests v0
4. Depth / VWAP Packet Context Integration v0
5. Depth / VWAP Sampling Summary Context Support v0
6. Dashboard Depth / VWAP Policy Status Update v0
```

### 6.1 Pure helper

파일:

```text
src/market_data/depth_vwap.py
tests/test_depth_vwap.py
```

역할:

```text
orderbook levels와 target_size / target_notional을 넣으면 vwap, filled_size, slippage, insufficient_depth 등을 계산한다.
```

테스트:

```text
22개 unit tests 통과.
```

---

### 6.2 Mocked fixtures

파일 예시:

```text
tests/fixtures/market_data/depth_vwap/binance_spot_depth_btcusdt.json
tests/fixtures/market_data/depth_vwap/binance_usdm_depth_btcusdt.json
tests/fixtures/market_data/depth_vwap/bybit_spot_orderbook_btcusdt.json
tests/fixtures/market_data/depth_vwap/bybit_linear_orderbook_btcusdt.json
tests/fixtures/market_data/depth_vwap/okx_swap_books_btc_usdt_swap.json
```

역할:

```text
VWAP helper가 Binance / Bybit / OKX 스타일 mocked orderbook shape에서 동작하는지 검증.
OKX contract unit conversion은 아직 solved로 주장하지 않음.
```

---

### 6.3 Packet/candidate context

파일:

```text
src/market_data/depth_vwap_context.py
src/market_data/spot_futures_basis_packet_builder.py
```

역할:

```text
명시적 target_size 또는 target_notional이 주어질 때만
packet.extensions.depth_vwap_context
candidate.extensions.depth_vwap_context
에 diagnostics-only context를 추가한다.
```

바꾸지 않은 것:

```text
readiness_status
recommended_default_decision
estimated_net_basis_pct
required_missing_fields
readiness_pass
```

---

### 6.4 Sampling summary context

파일:

```text
src/market_data/sampling.py
tests/test_depth_vwap_sampling_context.py
```

역할:

```text
sampling summary가 depth_vwap_context_seen_count,
depth_vwap_insufficient_depth_count,
slippage max/avg,
warning counts 등을 집계한다.
```

여전히 바꾸지 않은 것:

```text
readiness 판단
persistence_status
council_recommended
positive_net_gap_count
readiness_pass_count
```

---

### 6.5 Dashboard status

파일:

```text
docs/strategy_evidence_dashboard.md
```

현재 spot_futures_basis_v0의 Depth/VWAP status:

```text
PACKET_CONTEXT_SUPPORTED + SAMPLING_SUMMARY_SUPPORTED + READINESS_UNCHANGED
```

mark_orderbook_gap_hunt_v0의 Depth/VWAP status:

```text
WATCH_ITEM_ONLY / future diagnostics candidate
```

---

## 7. Strategy Evidence Dashboard / Council 현황

완료된 흐름:

```text
Strategy Evidence Dashboard / Journal Summary Planning
Handoff Index / Data Source Planning
Manual Dashboard Markdown v0
Council Review Handoff Criteria Planning
Council verification correction
Council Handoff Status column update
Depth/VWAP Status column update
```

현재 dashboard는 다음을 보여준다.

```text
strategy status
venue coverage
evidence status
Council Handoff Status
Depth/VWAP Status
watch items
recommendation
source handoff paths
```

중요한 해석:

```text
Dashboard는 trading signal이 아니다.
Council Handoff Status는 execution permission이 아니다.
NO_EDGE_ARCHIVE는 실패가 아니다.
POLICY_REVIEW는 매매 edge가 아니다.
MANUAL_REVIEW_CANDIDATE도 ENTER가 아니다.
```

---

## 8. Codex 운영 방식 v5

우리가 Codex에 대해 배운 것:

```text
Codex는 빠르고 똑똑하다.
작업이 명확하면 5~10분 안에도 좋은 결과를 낸다.
작업을 넓혀도 산출물이 명확하면 잘 수행한다.
다만 행동을 하나하나 설계해줘야 한다.
```

새 운영 원칙:

```text
사용자에게는 쉽게 설명한다.
Codex에게는 길고 정밀하게 지시한다.
작업은 예전보다 크게 묶되, 허용 파일과 금지 파일은 정확히 제한한다.
반드시 test count / behavior unchanged / no-trade / generated JSON guardrail을 요구한다.
```

좋은 Codex 작업 지시의 구성:

```text
1. 최신 main fresh branch 확인
2. Open PR 누적 여부 확인
3. 관련 docs/source/tests 읽기
4. 작업명
5. 이번 PR 목표
6. 절대 바꾸면 안 되는 것
7. 허용 파일
8. 금지 파일
9. 구현 요구사항
10. tests 요구사항
11. handoff 문서 요구사항
12. 필수 검증 명령
13. GitHub Files changed 예상 목록
14. 최종 응답 섹션
```

---

## 9. 현재 위치를 초보자식으로 다시 말하기

우리는 이제 다음 지점에 있다.

```text
1. 여러 매매 후보를 만들었다.
2. 거래소 public data를 끌어오는 길을 만들었다.
3. 그 데이터를 OpportunityPacket으로 정리했다.
4. readiness로 REJECT / NEED_DATA / WATCH를 판단한다.
5. 여러 번 sampling해서 evidence를 만든다.
6. evidence를 dashboard에 정리한다.
7. Council이 사람이 검토할 수 있도록 status를 붙인다.
8. top-of-book 착시를 줄이기 위해 Depth/VWAP 참고정보까지 연결했다.
```

하지만 아직 다음은 아니다.

```text
실제 주문 아님.
자동매매 아님.
Council 자동 실행 아님.
알림 아님.
active promotion 아님.
```

현재 시스템은 다음이다.

```text
매매 후보 검증 연구실.
```

---

## 10. 바로 다음 단계

현재 가장 자연스러운 다음 단계는 다음이다.

```text
Next Experimental Strategy Selection v0
```

목적:

```text
다음에 어떤 experimental strategy를 개발할지 고른다.
```

추천 방향:

```text
1순위: funding_rate_context_v0
2순위: volatility_breakout_v0
3순위: trade_flow_momentum_v0
4순위: derivatives_flow_context_v0
5순위: mean_reversion_context_v0
```

왜 Funding Rate Context가 1순위인가:

```text
spot_futures_basis_v0와 mark_orderbook_gap_hunt_v0에서 이미 derivatives, mark/index/funding context를 다뤘다.
public-read-only endpoint로 시작 가능성이 높다.
하지만 funding rate 자체는 entry signal이 아니라 context라는 guardrail이 필요하다.
```

---

## 11. 다음 Codex 작업 후보: Next Experimental Strategy Selection v0

다음 Codex에게 바로 시킬 후보 작업은 docs-only planning이다.

목표:

```text
다음 experimental strategy 후보를 비교하고,
Funding Rate Context Strategy를 1순위로 추천할지 결정한다.
```

허용 파일 후보:

```text
docs/pr_handoffs/next_experimental_strategy_selection_2026_06_10.md
```

금지:

```text
src 수정 금지
tests 수정 금지
config/registry 수정 금지
tools 수정 금지
live endpoint 호출 금지
generated JSON 생성/commit 금지
private API 금지
execution / alert / Council auto-call 금지
```

---

## 12. GitHub에 이 MD 파일을 올리는 방법

Codex는 ChatGPT에 첨부한 파일을 직접 읽지 못한다.  
따라서 **이 MD 파일을 GitHub repo 안에 커밋한 뒤, Codex에게 그 경로를 읽으라고 해야 한다.**

권장 경로:

```text
docs/AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md
```

PowerShell 기준:

```powershell
cd C:\Users\qhrb9\Desktop\agent

git switch main
git pull --ff-only origin main

git switch -c docs/handoff-v5-spot-futures-depth-vwap-dashboard

# 다운로드한 MD 파일을 아래 경로로 복사
# docs\AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md

git status --short
git add docs\AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md
git commit -m "Add AI Council project handoff v5"
git push -u origin docs/handoff-v5-spot-futures-depth-vwap-dashboard
```

그 다음:

```text
1. GitHub에서 PR 생성
2. Files changed가 이 MD 파일 1개뿐인지 확인
3. 테스트가 필요 없는 docs-only라도 git status / generated JSON clean 확인
4. merge
5. Codex에게 아래 첫 메시지 전송
```

---

## 13. 새 GPT 첫 대화 시작 문구

새 GPT 채팅에는 이 v5 파일을 첨부하고 아래 문구를 그대로 붙여넣는다.

```text
나는 GitHub repo `https://github.com/ehfkrh140-coder/agent`에서 AI Council 기반 read-only 매매 판단 시스템을 개발 중입니다.

첨부한 `AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md`를 먼저 읽고 현재 프로젝트 상태를 이어받아 주세요.

당신의 역할은 단순 코딩 도우미가 아니라, 세계 최고 수준의 코딩 설계자이자 초보자인 나에게 쉽게 설명해주는 아키텍트입니다.

나에게 설명할 때는 짧고 쉽게 말해주세요.
Codex에게 줄 요청문은 길고 정밀하게 작성해주세요.

앞으로 우리는 이런 루프로 개발합니다.

1. 내가 Codex 결과나 테스트 결과를 붙여넣습니다.
2. 당신은 먼저 성공/실패/보류 여부를 판정합니다.
3. 초보자인 내가 이해할 수 있게 왜 그런지 설명합니다.
4. 다음 단계로 가도 되는지 판단합니다.
5. Codex에게 줄 PR 단위 요청문을 작성합니다.
6. 내가 직접 테스트해야 할 경우 PowerShell 명령어와 성공 기준을 줍니다.
7. no-trade policy, PR handoff evidence, merge gate, rollback, generated JSON commit 금지를 계속 유지합니다.
8. GitHub Files changed가 이상해 보이면 먼저 GitHub 상태를 확인하고 PR 누적 문제를 짚어주세요.

중요한 현재 상태:
- active strategy는 `cross_exchange_spot_spread_v1`입니다.
- `mark_orderbook_gap_hunt_v0`는 Binance / Bybit / OKX baseline complete, experimental / non-active / NO_TRADE_ONLY입니다.
- `spot_futures_basis_v0`는 Binance + Bybit baseline complete, OKX deferred, proposed / experimental / non-active / NO_TRADE_ONLY입니다.
- Strategy Evidence Dashboard가 있고 Council Handoff Status와 Depth/VWAP Status가 반영되어 있습니다.
- Depth/VWAP는 planning, helper, mocked fixtures, packet/candidate context, sampling summary, dashboard status까지 완료되었습니다.
- VWAP-adjusted readiness는 아직 구현하지 않았고, 자동매매/알림/Council auto-call도 없습니다.
- generated packet/sampling JSON은 smoke artifact이며 commit 금지입니다.

현재 바로 다음 단계 후보는 `Next Experimental Strategy Selection v0`입니다.
Funding Rate Context Strategy를 1순위 후보로 보고 있지만, 문서를 읽고 10줄 이내로 현재 상태를 요약한 뒤 다음 단계가 맞는지 판단해주세요.
```

---

## 14. 새 Codex 첫 대화 시작 문구

Codex는 첨부파일을 직접 읽지 못하므로, 반드시 이 v5 MD 파일을 GitHub repo에 커밋/merge한 뒤 아래 문구를 보낸다.

```text
반드시 최신 origin/main 기준으로 새 브랜치를 만들어 작업하세요.
오래된 PR, 오래된 작업 브랜치, 캐시된 워크스페이스 기준으로 작업하지 마세요.
응답 Summary와 설명은 반드시 한국어로 작성하세요.

먼저 아래 인수인계 문서를 반드시 읽고 현재 프로젝트 상태를 10줄 이내로 요약하세요.

`docs/AI_Council_Project_Handoff_v5_Spot_Futures_Depth_VWAP_Dashboard_2026-06-10.md`

그 다음 아래 governance 문서도 읽으세요.

- AGENTS.md
- docs/no_trade_policy.md
- docs/pr_handoffs/README.md
- docs/merge_gate.md
- docs/rollback_policy.md
- docs/task_checklist.md
- docs/agent_workflow.md
- docs/strategy_evidence_dashboard.md

중요한 전제:
이 프로젝트의 최종 목표는 언젠가 execution/risk engine까지 포함하는 AI Council 기반 매매 시스템입니다.
하지만 현재 단계와 이번 PR 범위에서는 NO_TRADE_ONLY를 반드시 유지합니다.

현재 상태:
- active strategy는 cross_exchange_spot_spread_v1입니다.
- mark_orderbook_gap_hunt_v0는 Binance / Bybit / OKX baseline complete, experimental / non-active / NO_TRADE_ONLY입니다.
- spot_futures_basis_v0는 Binance + Bybit baseline complete, OKX deferred, proposed / experimental / non-active / NO_TRADE_ONLY입니다.
- Strategy Evidence Dashboard가 있고 Council Handoff Status와 Depth/VWAP Status가 반영되어 있습니다.
- Depth/VWAP는 planning, pure helper, mocked fixtures, packet/candidate context, sampling summary, dashboard status까지 완료되었습니다.
- VWAP-adjusted readiness는 구현하지 않았습니다.
- generated packet/sampling JSON은 commit 금지입니다.
- Codex PR title/body는 cumulative처럼 보일 수 있으므로 step-specific handoff file과 GitHub Files changed를 source-of-truth로 봅니다.

이번 작업은 아직 시작하지 마세요.
먼저 현재 상태를 요약하고, 다음 단계 후보를 아래 4개 중에서 비교해 제안하세요.

A. Next Experimental Strategy Selection v0
B. Funding Rate Context Strategy Planning v0
C. Dashboard / generated dashboard planning later
D. VWAP-adjusted readiness policy planning later

아직 code/config/test를 수정하지 마세요.
먼저 계획과 추천만 제시하세요.

응답에는 반드시 아래 섹션을 포함하세요.

[프로젝트 상태 10줄 요약]
[다음 단계 후보 비교]
[추천 순서]
[이번에 바로 하면 안 되는 것]
[필요한 user-local 테스트]
[No-trade compliance]
[다음 Codex 작업 제안]
```

---

## 15. 새 채팅 시작 전 체크리스트

```text
1. 이 v5 MD 파일 다운로드
2. 새 GPT 채팅에 v5 MD 첨부
3. v5 MD를 GitHub docs/ 경로에 커밋/merge
4. 새 GPT에게 13번 메시지 전송
5. 새 Codex에게 14번 메시지 전송
6. generated JSON clean 확인
```

PowerShell cleanup:

```powershell
cd C:\Users\qhrb9\Desktop\agent
Remove-Item data\generated_packets\*.json -ErrorAction SilentlyContinue
Remove-Item data\market_samples\*.json -ErrorAction SilentlyContinue
git status --short
```

주의:

```text
의도적으로 tracked된 fixture/sample 파일은 삭제하면 안 된다.
`git status --short` 기준으로 untracked/generated artifact만 확인한다.
```

---

## 16. 다음 큰 로드맵

### Near-term

```text
1. Next Experimental Strategy Selection v0
2. Funding Rate Context Strategy Planning v0
3. Funding public source / endpoint research docs-only
4. Funding common source contract planning
5. Funding mocked fixtures / parser / readiness / packet / adapter sequence
```

### Mid-term

```text
1. Dashboard generated planning
2. Council manual review packet planning
3. Depth/VWAP diagnostics를 다른 전략에도 context로 확장
4. Timestamp policy warning-only implementation
5. VWAP-adjusted readiness는 별도 승인 후 검토
```

### Long-term

```text
1. Paper trading / dry-run engine
2. credential isolation planning
3. risk engine planning
4. execution engine planning
5. kill switch / audit log / rollback
6. 실제 자동매매는 가장 마지막 단계
```

---

## 17. 최종 결론

현재 기준 결론:

```text
Cross-Exchange Spot Spread: active baseline 유지
Mark-Orderbook Gap Hunt: Binance / Bybit / OKX baseline complete
Spot-Futures Basis: Binance + Bybit baseline complete, OKX deferred
Strategy Evidence Dashboard: manual dashboard complete
Council Handoff Criteria: complete
Timestamp / Clock-Skew Policy Planning: complete
Depth/VWAP diagnostics/context/sampling/dashboard cycle: complete
```

다음 단계:

```text
Next Experimental Strategy Selection v0
```

가장 가능성 높은 다음 전략:

```text
Funding Rate Context Strategy v0
```

계속 금지:

```text
private API
credentials
account/balance/position
order/cancel
withdraw/deposit/transfer
auto-trading
alert
Council auto-call
active promotion
VWAP-adjusted readiness without approval
```

