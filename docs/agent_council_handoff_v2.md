# Agent Council Runtime Handoff v2  
_Gemini CLI OAuth 5-Agent 기반 / 다음 단계 인수인계 문서_

작성 목적:  
이 문서는 이전 대화에서 길게 구축한 **Gemini CLI 기반 5-agent 런타임**의 현재 상태, 시행착오, 금지사항, 다음 개발 순서를 다음 GPT 채팅방과 새 Codex 작업이 바로 이해하도록 전달하기 위한 인수인계 문서입니다.

---

## 0. 한 줄 요약

우리는 아직 “매매 봇 완성”이 아니라, **5개의 실제 Gemini Pro 계정을 API key 없이 Gemini CLI OAuth로 분리 실행하는 기초 런타임**을 완성했다.  
이제 다음 단계는 **agent_01~05 역할 분리**이며, 아직 회의 라운드/매매 실행/거래소 API는 구현하지 않는다.

---

## 1. 최종 목표: 무엇을 만들려는가

최종적으로 만들고 싶은 것은 단순 챗봇이 아니라, **거래소별 매매 데이터 차이를 감지했을 때 여러 AI 에이전트가 검증·토론하는 AI Council 기반 매매 판단 시스템**이다.

큰 흐름은 다음과 같다.

```text
거래소별 데이터 차이 발생
예: 가격 차이, 호가 차이, 체결 지연, 펀딩비 차이, 유동성 차이
        ↓
데이터 감지 엔진이 기회 후보(opportunity packet)를 만든다
        ↓
AI Council이 이 차이가 유효한지 논의한다
        ↓
진입 가능성 / 반대 논리 / 리스크 / 데이터 오류 가능성 검토
        ↓
최종 판단: ENTER / WATCH / REJECT / NEED_DATA
        ↓
나중에 별도 실행부가 deterministic rule과 리스크 룰로 주문 여부 처리
```

중요:  
현재 단계에서는 **주문, 출금, 이체, 자동매매, 거래소 API 실행 기능을 절대 구현하지 않는다.**  
AI는 당분간 “판단 보조/분석/검증”까지만 담당한다.

---

## 2. 우리가 오래 고생한 핵심 이유

처음에는 Gemini API key 방식으로 5개 agent를 만들려고 했으나, 사용자는 **Gemini Pro 계정 5개를 이미 결제했으므로 API key가 아니라 브라우저 로그인 기반 Gemini CLI OAuth 방식**을 쓰고 싶어 했다.

그래서 일반적인 API 호출 방식이 아니라:

```text
각 agent마다 별도 GEMINI_CLI_HOME
각 agent마다 별도 Google/Gemini Pro 계정
Python에서 gemini.cmd 호출
결과를 JSON으로 파싱
```

하는 구조를 만들었다.

이 과정에서 겪은 주요 문제는 다음과 같다.

### 2.1 API key 방식과 Gemini CLI OAuth 방식 혼동

초기 프로젝트는 `GEMINI_API_KEY_01~05`를 요구했다.  
하지만 최종 방향은 **Gemini CLI OAuth only**이다.

현재 정책:

```text
API key 방식 사용 금지
GEMINI_API_KEY 사용 금지
google-genai 사용 금지
python-dotenv 사용 금지
src/llm/gemini_client.py 삭제됨
```

### 2.2 `GEMINI_CLI_HOME` 분리

각 agent는 다음처럼 분리되어야 한다.

```text
agent_01 → C:\gemini-profiles\agent_01
agent_02 → C:\gemini-profiles\agent_02
agent_03 → C:\gemini-profiles\agent_03
agent_04 → C:\gemini-profiles\agent_04
agent_05 → C:\gemini-profiles\agent_05
```

최종 통과 조건은 각 profile의:

```text
C:\gemini-profiles\agent_XX\.gemini\google_accounts.json
```

에서:

```json
{
  "active": "expected_account@gmail.com"
}
```

이어야 한다.

`old` 목록에 원래 계정이 있어도 `active`가 다르면 실패다.

### 2.3 Chrome 프로필 혼선

처음에는 하나의 Chrome 프로필에서 여러 Google 계정을 바꿔가며 로그인했기 때문에 active 계정이 꼬였다.

확인된 Chrome profile-directory 매핑:

```text
agent_01 → Default
agent_02 → Profile 1
agent_03 → Profile 2
agent_04 → Profile 3
agent_05 → Profile 4
```

하지만 Gemini CLI가 로그인 링크를 특정 Chrome profile로 강제해서 열어주지는 않았다.  
`BROWSER` 환경변수 방식도 실패했다.  
Auth URL Relay 실험은 가능성이 있었지만, 기본 운영에서는 아직 사용하지 않는다.

### 2.4 warmup의 목적 재정의

초기에 warmup은 매번 로그인/verify를 하려 했다.  
하지만 이는 오히려 계정을 꼬이게 하거나, 로그인창 대기/timeout을 유발했다.

현재 정책:

```text
python tools/auth_warmup.py --all
→ check-only. Gemini CLI 실행 안 함. 브라우저 열지 않음. 모델 호출 안 함.

python tools/auth_warmup.py --agent agent_02 --repair-login
→ active mismatch 또는 AUTH_REQUIRED 때만 복구용.

python tools/auth_warmup.py --all --verify
→ 선택적 healthcheck. 필수 인증 단계 아님.
```

일상 실행에서는 warmup을 하지 않는다.

---

## 3. 현재 확정된 런타임 상태

### 3.1 기본 실행

```powershell
python main.py
```

동작:

```text
사용자 메시지 입력
→ agent_01~05 실행
→ 각 agent preflight에서 active==expected 확인
→ Gemini CLI 호출
→ 결과 요약 출력
→ data/sessions/session_*.json 저장
→ 종료
```

현재 `main.py`는 채팅 루프가 아니다.  
한 번 질문하고, 5개 agent가 답하고, 세션 저장 후 종료한다.

### 3.2 병렬 실행 옵션

최근 속도 기반 업데이트로 다음 옵션이 생겼다.

```powershell
python main.py --parallel --max-workers 2
```

기본 실행은 여전히 순차 실행이다.  
속도 개선 테스트용으로 `--parallel --max-workers 2`를 사용할 수 있다.

테스트 결과상:

```text
max_workers=2 또는 3 → 전체 wall-clock 약 31~33초
max_workers=5 → 각 agent가 느려져 큰 이득 없음
```

따라서 `max_workers=2` 권장.

### 3.3 저장되는 메타데이터

`AgentRunResult`에 다음 필드가 추가됐다.

```text
elapsed_seconds
rate_429_detected
auth_prompt_detected
timed_out
cli_session_id
```

용도:

```text
속도 측정
429/capacity 문제 감지
AUTH_REQUIRED 감지
timeout 감지
나중에 회의 라운드 resume 실험 준비
```

### 3.4 model 직접 지정 옵션

`configs/agents.yaml`에 `model: null`이 있다.

기본은 null이므로 기존 Gemini CLI 기본/Auto 흐름을 유지한다.  
실험적으로 다음과 같은 모델 직접 지정이 가능하도록 기반만 열어두었다.

```text
model: gemini-3-flash-preview
```

수동 테스트에서는 `gemini-3-flash-preview` 직접 지정이 약 8초대로 나와 실험 가치는 있다.  
하지만 기본값으로 강제하지 않는다.

---

## 4. 성능과 세션에 대한 중요한 이해

현재 `gemini.cmd -p` 방식은 다음 구조다.

```text
질문 1개마다 새 gemini.cmd 실행
→ CLI context 구성
→ utility_router 호출
→ main model 호출
→ JSON wrapper 출력
→ 프로세스 종료
```

이 방식은 안정적이고 파싱이 쉽지만, 매번 새 headless 실행이라 느리다.

측정 결과:

```text
headless -p baseline: agent당 약 10~20초
5개 순차 실행: 60초 이상 가능
병렬 max_workers=2/3: 약 31~33초
--resume latest: 15초 → 8~11초 개선 가능성
--prompt-interactive: 5~8초 체감 가능, 하지만 TUI/persistent process 관리가 복잡하여 아직 제외
```

중요 판단:

```text
지금 구현은 “회의 가능성 테스트용 런타임”으로는 OK.
진짜 회의 시스템으로는 아직 부족.
```

이유:

```text
진짜 회의는 agent들이 여러 라운드로 서로의 발언을 보고 반박/수정해야 함.
매 발언마다 완전히 새로 켜지면 속도와 맥락 면에서 불리함.
```

그러나 persistent `--prompt-interactive` 프로세스는 아직 너무 복잡하므로 다음 단계에서는 구현하지 않는다.  
일단 `cli_session_id`를 저장해두고, 나중에 회의 라운드에서 `--resume` 실험을 한다.

---

## 5. 현재 단계: 로드맵 기준 위치

완료됨:

```text
1. Gemini CLI OAuth 기반 방향 확정
2. 5개 agent별 GEMINI_CLI_HOME 분리
3. active == expected_account preflight 검증
4. API key 방식 제거
5. main.py에서 5개 agent 실행 및 session 저장
6. warmup을 check-only / repair-login / optional verify로 재정의
7. 속도/세션 메타데이터 추가
8. 병렬 실행 옵션 추가
9. model 직접 지정 실험 옵션 추가
```

아직 미구현:

```text
1. agent_01~05 역할 분리
2. 진짜 회의 라운드 구조
3. agent_01 → agent_02~04 병렬 검토 → agent_05 최종 요약 흐름
4. 회의 라운드별 resume 실험
5. 거래소 데이터 입력 스키마
6. 기회 후보(opportunity packet) 구조
7. 매매 실행부
```

현재 정확한 위치:

```text
기초 런타임 완성 + 회의형 구조를 위한 속도/세션 기반 준비 완료
```

다음 단계:

```text
agent_01~05 역할 프롬프트 분리
```

---

## 6. 다음 단계에서 해야 할 일

### 목표

5개 agent가 모두 같은 범용 분석 에이전트처럼 답하는 문제를 해결한다.

현재 문제:

```text
agent들이 아직 “범용 분석 에이전트”처럼 답한다.
non_json_output warning이 나올 수 있다.
workspace가 비어 있다는 식의 쓸모없는 답변을 한다.
가끔 도구 사용/파일 탐색을 시도한다.
```

다음 단계는 프롬프트만 바꿔서 역할을 분리한다.

### 역할

```text
agent_01: 의장 / 문제 정리자
agent_02: 찬성 관점 / 수익 가능성 탐색자
agent_03: 반대 관점 / 약점 공격자
agent_04: 리스크 관리자 / 안전성 검토자
agent_05: 최종 요약자 / 합의안 작성자
```

### 매우 중요

다음 Codex 작업에서는 아래 파일만 수정하는 것이 좋다.

```text
prompts/agent_01.md
prompts/agent_02.md
prompts/agent_03.md
prompts/agent_04.md
prompts/agent_05.md
README.md는 필요 시 아주 짧게만
```

건드리면 안 되는 것:

```text
main.py
src/
tools/auth_warmup.py
configs/agents.yaml
requirements.txt
.env.example
```

아직 회의 라운드 구현도 하지 않는다.

---

## 7. 다음 단계 이후 예상 구조

역할 분리 후, 다음 구조로 발전시킨다.

### v1: 단일 라운드 Council

```text
사용자 또는 데이터 감지 엔진이 opportunity packet 제공
        ↓
agent_01 의장: 문제 정리 / 회의 브리프 생성
        ↓
agent_02, agent_03, agent_04 병렬 검토
        ↓
agent_05 최종 요약 / 판단안 작성
```

### v2: 2라운드 Council

```text
Round 1: agent_02~04 1차 의견
Round 2: 서로의 의견을 보고 반박/수정
Final: agent_05 최종 판단
```

### v3: session-aware Council

```text
Round 1에서 cli_session_id 저장
Round 2에서 resume 실험
```

### v4: persistent process Council

```text
--prompt-interactive 기반 agent process pool
```

v4는 나중에 연구한다. 지금 구현하지 않는다.

---

## 8. 다음 GPT 채팅에 전달할 첫 메시지

```text
첨부한 agent_council_handoff_v2.md는 이전 채팅에서 구축한 Gemini CLI 기반 5-agent 런타임 인수인계 문서입니다.

이 프로젝트의 최종 목표는 거래소별 매매 데이터 차이를 감지했을 때, 여러 AI 에이전트가 그 차이가 유효한지/수익성이 있는지/리스크가 감당 가능한지 논의하는 AI Council 기반 매매 판단 시스템을 만드는 것입니다.

현재 완료된 것은 매매 봇이 아니라 기초 런타임입니다.
- Gemini CLI OAuth only
- 5개 Gemini Pro 계정 분리
- agent별 GEMINI_CLI_HOME 분리
- active == expected_account 검증
- main.py에서 5개 agent 실행 및 session 저장
- warmup은 check-only/repair-login/optional verify 구조
- API key 방식 제거
- 속도/세션 메타데이터 추가
- --parallel --max-workers 2 옵션 추가
- model 직접 지정 실험 옵션 추가

아직 미구현:
- agent 역할 분리
- 회의 라운드
- 거래소 데이터 입력 스키마
- opportunity packet
- 매매 실행부

먼저 이 문서를 읽고 현재 프로젝트가 어느 단계인지 요약해 주세요.
그 다음, 다음 단계인 agent_01~05 역할 프롬프트 분리를 어떻게 진행할지 제안해 주세요.

중요:
로그인/warmup/Gemini CLI client/main.py/AgentRunner는 당분간 건드리지 않는 방향으로 진행하고 싶습니다.
이번 다음 단계는 prompts/agent_01.md~agent_05.md 역할 분리와 JSON-only 안정성 강화가 목표입니다.
```

---

## 9. 다음 Codex 작업에 전달할 첫 메시지

```text
반드시 최신 origin/main 기준으로 새 브랜치를 만들어 작업하세요.
오래된 PR, 오래된 작업 브랜치, 캐시된 워크스페이스 기준으로 작업하지 마세요.
응답 Summary와 설명은 반드시 한국어로 작성하세요.

현재 main의 확정 상태:
- Gemini CLI OAuth only
- API key 방식 사용 금지
- src/llm/gemini_client.py 삭제됨
- google-genai / python-dotenv 사용 금지
- main.py는 기본 실행 시 warmup 없이 바로 메시지 입력
- auth_warmup.py --all은 check-only
- repair-login은 active mismatch/AUTH_REQUIRED 때만 사용
- verify는 optional healthcheck
- active == expected_account가 최종 계정 통과 조건
- --parallel --max-workers 2 옵션 있음
- AgentRunResult에 elapsed_seconds / rate_429_detected / auth_prompt_detected / timed_out / cli_session_id 저장됨
- model 직접 지정 옵션은 있으나 configs는 model: null

이번 작업 목표:
5개 agent가 모두 같은 범용 분석 에이전트처럼 답하는 문제를 개선하기 위해, prompts/agent_01.md ~ prompts/agent_05.md만 역할별로 수정하세요.
회의 라운드 구현은 아직 하지 마세요.

역할:
- agent_01: 의장 / 문제 정리자
- agent_02: 찬성 관점 / 수익 가능성 탐색자
- agent_03: 반대 관점 / 약점 공격자
- agent_04: 리스크 관리자 / 안전성 검토자
- agent_05: 최종 요약자 / 합의안 작성자

공통 규칙:
- 반드시 한국어로 응답
- 반드시 AgentResponse JSON schema 형식의 순수 JSON 객체만 출력
- 마크다운 금지
- 코드블록 금지
- workspace가 비어 있다는 말 금지
- 프로젝트 파일 분석 금지
- 도구 사용 시도 금지
- 사용자 메시지와 제공된 데이터만 분석
- 민감정보 요구 금지
- 거래소 주문/출금/이체/자동매매 실행 제안 금지
- 분석/판단 보조만 수행

수정 허용 파일:
- prompts/agent_01.md
- prompts/agent_02.md
- prompts/agent_03.md
- prompts/agent_04.md
- prompts/agent_05.md
- README.md는 필요한 경우 아주 짧게만 수정

수정 금지:
- main.py
- src/
- tools/auth_warmup.py
- configs/agents.yaml
- requirements.txt
- .env.example
- Gemini CLI client
- AgentRunner
- 회의 라운드 구현
- DecisionEngine
- 거래소 API/주문/출금/이체/자동매매 기능

테스트:
python -m compileall main.py src tests tools
python -m unittest tests/test_gemini_cli_client.py

완료 후 요약에는 반드시 다음을 포함하세요:
- 수정한 파일 목록
- 각 agent 역할 요약
- runtime/auth/API 관련 파일을 건드리지 않았는지
- 테스트 결과
```

---

## 10. 앞으로의 금지사항

이 프로젝트는 아직 실행 매매 봇이 아니다.

절대 금지:

```text
거래소 API 연결
주문 실행
출금/이체
자동매매
실계좌 매매
API key 방식 부활
GEMINI_API_KEY 추가
google-genai 재추가
src/llm/gemini_client.py 재생성
```

---

## 11. 사용자가 기억해야 할 운영 명령

기본 실행:

```powershell
python main.py
```

병렬 속도 테스트:

```powershell
python main.py --parallel --max-workers 2
```

계정 점검:

```powershell
python tools/auth_warmup.py --all
```

계정 복구:

```powershell
python tools/auth_warmup.py --agent agent_02 --repair-login
```

선택적 healthcheck:

```powershell
python tools/auth_warmup.py --all --verify
```

PowerShell 주의:

```text
$home 변수명 사용 금지.
반드시 $profileHome 사용.
```

---

## 12. 현재 가장 중요한 다음 액션

다음 채팅과 새 Codex에서 할 일:

```text
1. 이 인수인계 문서를 전달
2. Codex는 최신 origin/main 기준으로 시작
3. 이번 작업은 prompts/agent_01.md~agent_05.md 역할 분리만
4. main.py/src/tools/configs는 건드리지 않음
5. 역할 분리 후 main.py로 같은 질문을 던져 5개 agent가 서로 다른 관점으로 답하는지 확인
```
