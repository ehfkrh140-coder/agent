# AI Council Project Handoff v6 — Funding Rate Parser / Wrapper / App Codex Transition

작성일: 2026-06-11  
대상 저장소: `https://github.com/ehfkrh140-coder/agent`  
권장 저장 위치: `docs/AI_Council_Project_Handoff_v6_Funding_Rate_Parser_Wrapper_App_Codex_2026-06-11.md`

---

## 0. 이 문서의 목적

이 문서는 기존 v5 인수인계 이후 진행된 Funding Rate Context 작업과 Codex 운영 이슈를 정리하고,  
앞으로 **앱 Codex + 로컬 폴더 기반 개발**로 안전하게 이어가기 위한 최신 인수인계 문서다.

v5 문서는 다음 상태까지를 중심으로 정리했다.

```text
Depth/VWAP 완료
→ Next Experimental Strategy Selection 진입
→ Funding Rate Context Strategy가 다음 후보
```

하지만 현재는 Funding Rate 흐름이 훨씬 더 진행되었다.

```text
Strategy Module Boundary Map 완료
Next Experimental Strategy Selection 완료
Funding Rate Context Strategy Planning 완료
Funding public source research 완료
Funding mocked fixture contract 완료
Required fixture files 완료
Optional / edge fixture files 완료
Pure parser helper planning 완료
Pure parser helper implementation 완료
Venue parser wrapper planning 완료
Wrapper implementation clean replacement PR 준비 중
```

따라서 새 GPT / 앱 Codex / 로컬 개발 환경에는 v5만 주면 안 된다.  
반드시 이 v6 문서를 함께 제공해야 한다.

---

## 1. 초간단 현재 상태 요약

```text
1. 이 프로젝트는 AI Council 기반 read-only 매매 후보 검증 시스템이다.
2. 현재 정책은 계속 NO_TRADE_ONLY다.
3. active baseline은 cross_exchange_spot_spread_v1이다.
4. Funding Rate는 trading strategy가 아니라 context / diagnostics / regime information이다.
5. Funding Rate public source research와 source classification은 완료됐다.
6. Funding Rate required / optional / edge mocked fixtures가 추가됐다.
7. Funding Rate pure parser helper와 unit tests가 추가됐다.
8. Funding Rate venue wrapper planning docs는 완료됐다.
9. Funding Rate venue wrapper implementation은 아직 깨끗하게 merge되지 않았다.
10. 다음 작업은 #194 clean replacement PR로 wrapper implementation 3개 파일만 추가하는 것이다.
```

---

## 2. 절대 유지해야 하는 대원칙

현재 프로젝트는 자동매매 시스템이 아니다.

```text
지금은 돈을 버는 버튼을 만드는 단계가 아니라,
돈을 벌 가능성이 있는 후보를 검증하는 판단 연구실을 만드는 단계다.
```

계속 금지:

```text
private API
API key / secret / token
account / balance / position 조회
order / cancel
withdraw / deposit / transfer
auto-trading
alert execution
Council auto-call
active promotion
Funding Rate를 entry signal로 사용
Funding Rate를 standalone WATCH / ENTER trigger로 사용
readiness 변경
generated packet/sampling JSON commit
```

Funding Rate 관련 핵심 guardrail:

```text
positive funding ≠ short permission
negative funding ≠ long permission
high absolute funding ≠ ENTER
parser success ≠ readiness success
wrapper success ≠ trade signal
dashboard / Council status ≠ execution permission
```

---

## 3. 현재 아키텍처 큰 그림

현재 시스템의 intended pipeline:

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

Funding Rate는 아직 이 pipeline의 execution 쪽에 연결되지 않았다.  
현재 Funding Rate는 다음 위치까지만 진행됐다.

```text
mocked fixtures
→ pure parser helper
→ wrapper planning
```

아직 없음:

```text
live/public endpoint adapter
venue wrapper implementation merge
packet/candidate extension
readiness policy
sampling collector
dashboard automation
Council packet
alert
execution
```

---

## 4. v5 이후 완료된 주요 PR / 작업 상태

### 4.1 Strategy Module Boundary Map v0

완료된 목적:

```text
새 전략을 플러그인처럼 추가하기 위한 module boundary 문서화.
Venue Data / Parser / Source Contract / Strategy Plugin / Readiness / Context / Evidence / Dashboard / Governance 계층 정의.
```

핵심 원칙:

```text
전략은 공통 시스템을 오염시키면 안 된다.
context-only 정보는 executable signal과 분리한다.
readiness 변경은 별도 policy PR 없이는 금지한다.
```

---

### 4.2 Next Experimental Strategy Selection Finalization v0

완료된 목적:

```text
후보 전략 비교 후 funding_rate_context_v0를 다음 planning 후보로 선정.
```

선정 이유:

```text
public-read-only로 시작 가능
기존 derivatives / spot-futures / mark/index context와 연결 쉬움
context-only로 시작하기 적합
```

중요:

```text
Funding Rate는 더 강한 trading signal이어서 선택된 것이 아니다.
가장 안전한 context-planning candidate이기 때문에 선택됐다.
```

---

### 4.3 Funding Rate Context Strategy Planning v0

완료된 목적:

```text
Funding Rate를 context / diagnostics / regime information으로 정의.
Funding Rate가 어느 module boundary에 붙는지 설계.
```

plugin metadata planning:

```text
strategy_family: funding_rate_context
strategy_id: funding_rate_context_v0
execution_policy: NO_TRADE_ONLY
active_promotion_allowed: false
standalone_signal_allowed: false
readiness_changes_allowed: false
council_auto_call_allowed: false
alert_allowed: false
private_api_allowed: false
```

---

### 4.4 Funding Public Source Research Finalization v0

완료된 source classification:

```text
required_primary:
- Binance GET /fapi/v1/fundingRate
- Bybit GET /v5/market/funding/history
- OKX GET /api/v5/public/funding-rate-history

optional_context:
- Binance GET /fapi/v1/fundingInfo
- Bybit GET /v5/market/instruments-info
- OKX GET /api/v5/public/funding-rate
```

Minimum v0 source contract:

```text
required_v0:
- venue
- instrument_id
- instrument_type
- symbol_normalized
- funding_rate
- funding_rate_timestamp_ms
- source_endpoint
- source_semantics
- parser_status
- required_missing_fields
```

중요한 policy:

```text
8시간 funding interval hard-code 금지
predicted/current funding과 realized/settled funding collapse 금지
markPrice / premium은 executable price가 아님
```

---

### 4.5 Funding Mocked Fixture Contract v0

완료된 목적:

```text
실제 fixture JSON을 만들기 전 fixture naming / shape / expected parser outcome 계약화.
```

fixture path 후보:

```text
tests/fixtures/market_data/funding_rate/
```

---

### 4.6 Funding Mocked Required Fixture Files v0

추가된 required fixture 3개:

```text
tests/fixtures/market_data/funding_rate/binance_usdm_funding_rate_history_normal.json
tests/fixtures/market_data/funding_rate/bybit_linear_funding_history_normal.json
tests/fixtures/market_data/funding_rate/okx_funding_rate_history_normal.json
```

검증:

```text
json.tool OK
json.load OK
unittest OK
```

---

### 4.7 Funding Optional / Edge Fixture Files v0

추가된 optional context fixture 4개:

```text
binance_usdm_funding_info_interval_cap_floor.json
bybit_linear_instruments_info_funding_interval.json
bybit_inverse_funding_history_normal.json
okx_current_funding_rate_normal.json
```

추가된 edge fixture 10개:

```text
missing_required_funding_rate.json
missing_optional_interval.json
string_numeric_parsing.json
positive_funding_rate.json
negative_funding_rate.json
zero_funding_rate.json
high_absolute_funding_context.json
timestamp_data_age_clock_skew_watch.json
varying_funding_interval.json
okx_predicted_vs_realized_semantics.json
```

---

### 4.8 Funding Pure Parser Helper Planning v0

완료된 목적:

```text
parser 구현 전 parser_status / source_semantics / missing field / warnings / normalized output shape를 문서화.
```

중요 parser_status 계획:

```text
OK
OK_WITH_WARNINGS
NEED_SOURCE_FIELDS
INVALID_SOURCE_SHAPE
INVALID_NUMERIC_FIELD
INVALID_TIMESTAMP_FIELD
UNSUPPORTED_SOURCE
UNSUPPORTED_VENUE
```

모든 status의 readiness effect:

```text
none / readiness unchanged
```

---

### 4.9 Funding Pure Parser Helper Implementation v0

merge 완료.

추가된 파일:

```text
src/market_data/funding_rate_parser.py
tests/test_funding_rate_parser.py
docs/pr_handoffs/funding_pure_parser_helper_implementation_2026_06_11.md
```

public API:

```python
parse_funding_rate_payload(payload, *, venue: str, source_endpoint: str) -> dict[str, Any]
```

역할:

```text
caller-provided Funding Rate raw payload를 normalized context observation으로 변환.
network 없음.
private API 없음.
file I/O 없음.
config/registry lookup 없음.
readiness 변경 없음.
```

테스트:

```text
python -m unittest tests.test_funding_rate_parser
Ran 24 tests, OK

python -m unittest discover -s tests
Ran 555 tests, OK
```

---

### 4.10 Funding Venue Parser Wrapper Planning v0

merge 완료.

추가된 파일:

```text
docs/funding_rate_venue_parser_wrapper_plan.md
docs/pr_handoffs/funding_venue_parser_wrapper_plan_2026_06_11.md
```

핵심 설계:

```text
wrapper는 pure helper 위의 thin orchestration layer 후보.
wrapper는 venue/source label을 고르고 provenance를 보존한다.
wrapper는 parser result를 context-only envelope로 감싼다.
wrapper는 readiness, adapter, packet, sampling, dashboard를 변경하지 않는다.
```

중요 source_semantics mapping:

```text
binance_usdm_funding_rate_history → historical_funding_charge_record
binance_usdm_funding_info → interval_cap_floor_context
bybit_v5_funding_history → settled_historical_funding_context
bybit_v5_instruments_info → instrument_interval_cap_floor_context
okx_funding_rate_history → historical_funding_context
okx_current_funding_rate → current_predicted_funding_context
```

---

## 5. 폐기 / merge hold 된 PR

### 5.1 PR #188

상태:

```text
closed / not merged
```

문제:

```text
Expected Files Changed보다 GitHub Files changed가 컸음.
planning docs가 implementation PR에 다시 섞임.
```

---

### 5.2 PR #192

상태:

```text
closed / not merged
```

문제:

```text
Expected Files Changed: 3
GitHub Files changed: 5
PR #191 planning docs가 implementation PR에 다시 포함됨.
```

---

### 5.3 PR #193

상태:

```text
closed / not merged
```

문제:

```text
Expected Files Changed: 3
GitHub Files changed: 5
PR #191 planning docs가 또 다시 implementation PR에 포함됨.
```

---

## 6. 현재 다음 작업: #194 clean replacement

현재 다음 PR은:

```text
Funding Venue Parser Wrapper Implementation v0 — Clean Replacement
```

목표:

```text
#192 / #193 구현 의도는 유지하되,
GitHub PR Files changed가 정확히 3개만 나오도록 clean replacement PR을 만든다.
```

Expected Files Changed:

```text
src/market_data/funding_rate_wrappers.py
tests/test_funding_rate_wrappers.py
docs/pr_handoffs/funding_venue_parser_wrapper_implementation_2026_06_11.md
```

절대 PR diff에 포함되면 안 되는 파일:

```text
docs/funding_rate_venue_parser_wrapper_plan.md
docs/pr_handoffs/funding_venue_parser_wrapper_plan_2026_06_11.md
src/market_data/funding_rate_parser.py
tests/test_funding_rate_parser.py
tests/fixtures/**
config/**
configs/**
tools/**
data/generated_packets/**
data/market_samples/**
```

#194 성공 기준:

```text
GitHub Files changed = 정확히 3개
wrapper module added
wrapper tests added
implementation handoff added
existing parser helper not modified
existing parser tests not modified
fixtures not modified
config/tools/data not modified
generated JSON 없음
python -m unittest tests.test_funding_rate_wrappers OK
python -m unittest discover -s tests OK
NO_TRADE_ONLY 유지
```

---

## 7. Codex Cloud / workspace 문제 정리

우리는 Codex Cloud에서 다음 문제를 반복적으로 겪었다.

```text
Codex가 PR은 만들 수 있지만,
Codex shell workspace는 origin/main을 검증하지 못할 수 있다.
```

관찰된 문제:

```text
origin remote 없음
origin/main 없음
git fetch origin main 실패
CONNECT tunnel failed 403
main branch 없음
이전 PR branch snapshot에서 시작
Codex local staged files와 GitHub PR Files changed 불일치
```

중요 결론:

```text
Codex가 PR을 만들 수 있다
≠
Codex terminal workspace가 GitHub origin/main과 정상 연결되어 있다
```

따라서 앞으로 최종 판단 기준:

```text
1. GitHub PR Files changed
2. step-specific handoff
3. test results
4. generated JSON clean check
5. no-trade compliance
```

Codex local report는 참고자료일 뿐이다.

---

## 8. 앱 Codex / 로컬 폴더 운영 방침

앞으로 웹 Codex Cloud 방식은 사용하지 않는다.

추천 방식:

```text
앱 Codex + 사용자 로컬 clean clone 폴더 기반 개발
```

사용자가 만든 clean local folder:

```text
C:\Users\qhrb9\Desktop\agent-clean
```

생성 과정:

```powershell
cd C:\Users\qhrb9\Desktop
git clone https://github.com/ehfkrh140-coder/agent.git agent-clean
cd agent-clean
git switch main
git pull --ff-only origin main
git status --short --branch
```

정상 상태:

```text
## main...origin/main
```

필수 확인 파일:

```powershell
Test-Path docs\funding_rate_pure_parser_helper_plan.md
Test-Path docs\pr_handoffs\funding_pure_parser_helper_plan_2026_06_11.md
Test-Path src\market_data\funding_rate_parser.py
Test-Path tests\test_funding_rate_parser.py
Test-Path docs\pr_handoffs\funding_pure_parser_helper_implementation_2026_06_11.md
Test-Path docs\funding_rate_venue_parser_wrapper_plan.md
Test-Path docs\pr_handoffs\funding_venue_parser_wrapper_plan_2026_06_11.md
```

기대 결과:

```text
True
True
True
True
True
True
True
```

앱 Codex에는 이 로컬 폴더를 기준으로 열게 한다.

```text
C:\Users\qhrb9\Desktop\agent-clean
```

---

## 9. 로컬 기반 개발 루프

앞으로의 표준 루프:

```text
1. 사용자 로컬 agent-clean에서 main 최신화
2. 앱 Codex가 agent-clean 폴더를 기준으로 작업
3. Codex가 새 branch 생성
4. Codex가 허용 파일만 수정
5. Codex가 local tests 실행
6. Codex가 commit / PR 생성
7. 사용자는 PR 번호만 GPT에게 전달
8. GPT가 GitHub Files changed / tests / guardrail 확인
9. GPT가 merge 가능 판정
10. 사용자 merge
11. 사용자 로컬 agent-clean에서 main pull
12. 다음 작업 반복
```

로컬 업데이트 명령:

```powershell
cd C:\Users\qhrb9\Desktop\agent-clean
git switch main
git pull --ff-only origin main
git status --short --branch
```

새 작업 브랜치 예시:

```powershell
git switch -c codex/funding-venue-wrapper-implementation-v0
```

---

## 10. 충돌 해결 정책

사용자는 코드 충돌을 직접 해결하지 않는다.

금지:

```text
Accept Current
Accept Incoming
Accept Both
```

충돌 발생 시:

```powershell
git status
```

결과를 GPT에게 전달한다.

GPT는 Codex에게 conflict-resolution 전용 요청문을 작성한다.

Codex conflict policy:

```text
1. conflict files 확인
2. 허용 파일 외 충돌이면 중단
3. 가능한 경우 fresh main branch에서 Expected Files Changed만 재적용
4. 임의로 Accept Both 금지
5. 해결 후 tests 실행
6. GitHub Files changed 확인 전 merge 금지
```

---

## 11. 앱 Codex 첫 메시지

앱 Codex에 로컬 폴더 `agent-clean`을 열고 아래 메시지로 시작한다.

```text
이 작업은 로컬 폴더 `C:\Users\qhrb9\Desktop\agent-clean` 기준으로 진행합니다.
웹 Codex Cloud가 아니라 앱 Codex 로컬 폴더 기반 작업입니다.

먼저 아래 preflight를 수행하세요.

1. 현재 경로 확인:
pwd

2. git 상태 확인:
git status --short --branch

3. remote 확인:
git remote -v

4. main 최신화 가능 여부 확인:
git switch main
git pull --ff-only origin main

5. 필수 파일 존재 확인:
- docs/AI_Council_Project_Handoff_v6_Funding_Rate_Parser_Wrapper_App_Codex_2026-06-11.md
- docs/funding_rate_pure_parser_helper_plan.md
- docs/pr_handoffs/funding_pure_parser_helper_plan_2026_06_11.md
- src/market_data/funding_rate_parser.py
- tests/test_funding_rate_parser.py
- docs/pr_handoffs/funding_pure_parser_helper_implementation_2026_06_11.md
- docs/funding_rate_venue_parser_wrapper_plan.md
- docs/pr_handoffs/funding_venue_parser_wrapper_plan_2026_06_11.md

위 preflight가 실패하면 작업하지 말고 중단 보고하세요.

preflight가 통과하면 아래 작업을 진행하세요.

작업명:
Funding Venue Parser Wrapper Implementation v0 — Clean Replacement

목표:
GitHub PR Files changed가 정확히 아래 3개만 나오게 합니다.

- src/market_data/funding_rate_wrappers.py
- tests/test_funding_rate_wrappers.py
- docs/pr_handoffs/funding_venue_parser_wrapper_implementation_2026_06_11.md

절대 수정 금지:
- docs/funding_rate_venue_parser_wrapper_plan.md
- docs/pr_handoffs/funding_venue_parser_wrapper_plan_2026_06_11.md
- src/market_data/funding_rate_parser.py
- tests/test_funding_rate_parser.py
- tests/fixtures/**
- config/**
- configs/**
- tools/**
- data/generated_packets/**
- data/market_samples/**

NO_TRADE_ONLY 유지.
endpoint 호출 금지.
private API 금지.
readiness 변경 금지.
packet/sampling/dashboard 변경 금지.
generated JSON 생성/commit 금지.
```

---

## 12. #194 작업 상세 요구사항

앱 Codex가 구현해야 할 wrapper module:

```text
src/market_data/funding_rate_wrappers.py
```

public APIs:

```python
parse_binance_usdm_funding_rate_history(payload, *, provenance=None)
parse_binance_usdm_funding_info(payload, *, provenance=None)
parse_bybit_v5_funding_history(payload, *, category_hint=None, provenance=None)
parse_bybit_v5_instruments_info(payload, *, category_hint=None, provenance=None)
parse_okx_funding_rate_history(payload, *, provenance=None)
parse_okx_current_funding_rate(payload, *, provenance=None)
```

각 wrapper는 기존 helper를 호출한다.

```python
parse_funding_rate_payload(payload, venue=..., source_endpoint=...)
```

wrapper envelope:

```python
{
    "wrapper_status": "...",
    "venue": "...",
    "source_endpoint": "...",
    "source_semantics": "...",
    "parser_result": {...},
    "wrapper_warnings": [...],
    "provenance": {...},
    "input_record_count": int | None,
    "parsed_record_count": int,
    "context_only": True,
    "readiness_effect": "unchanged",
}
```

status 후보:

```text
OK
OK_WITH_WARNINGS
WRAPPER_INPUT_EMPTY
WRAPPER_SOURCE_MISMATCH
WRAPPER_INVALID_INPUT
```

source_semantics mapping:

```text
binance_usdm_funding_rate_history → historical_funding_charge_record
binance_usdm_funding_info → interval_cap_floor_context
bybit_v5_funding_history → settled_historical_funding_context
bybit_v5_instruments_info → instrument_interval_cap_floor_context
okx_funding_rate_history → historical_funding_context
okx_current_funding_rate → current_predicted_funding_context
```

Bybit category_hint policy:

```text
None → no warning
match → no warning
mismatch → wrapper_warnings includes category_hint_mismatch
mismatch does not block parsing
mismatch is not a signal
```

empty payload policy:

```text
empty_payload warning
wrapper_status WRAPPER_INPUT_EMPTY or OK_WITH_WARNINGS
must document choice in handoff
no readiness effect
```

---

## 13. #194 test requirements

새 테스트 파일:

```text
tests/test_funding_rate_wrappers.py
```

테스트 범위:

```text
normal wrappers
envelope shape
context_only True
readiness_effect unchanged
provenance shallow copy
Bybit category_hint mismatch
empty payload warning
source_semantics correctness
no forbidden output keys
no network/private imports
no file/env/config lookup
no generated artifact references
```

필수 test commands:

```powershell
python -m unittest tests.test_funding_rate_wrappers
python -m unittest discover -s tests
```

예상:

```text
wrapper tests OK
full test suite OK
```

---

## 14. 다음 로드맵

#194가 성공적으로 merge되면 다음 단계:

```text
Funding Adapter Public Source Planning v0
```

그 다음:

```text
Funding Public Adapter Implementation v0
Funding Packet/Candidate Context Extension Planning v0
Funding Sampling Summary Planning v0
Funding Dashboard Context Status Planning v0
```

아직도 금지:

```text
live endpoint call implementation without planning
private API
credentials
order/execution
readiness 변경
alert
Council auto-call
active promotion
```

---

## 15. 최종 결론

현재 최신 상태:

```text
#191 wrapper planning merge 완료
#192 폐기
#193 폐기
#194 clean wrapper implementation replacement 필요
```

가장 중요한 원칙:

```text
GitHub PR Files changed가 최종 source-of-truth.
Codex local staged files는 참고자료일 뿐.
Expected Files Changed와 다르면 merge hold.
```

현재 바로 다음 작업:

```text
Funding Venue Parser Wrapper Implementation v0 — Clean Replacement
```

Expected Files Changed:

```text
src/market_data/funding_rate_wrappers.py
tests/test_funding_rate_wrappers.py
docs/pr_handoffs/funding_venue_parser_wrapper_implementation_2026_06_11.md
```

성공하면 다음으로 이동:

```text
Funding Adapter Public Source Planning v0
```
