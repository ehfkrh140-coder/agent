# agent-runtime-core 인수인계 메모

이 문서는 다음 채팅방과 새 Codex 작업에 바로 넘기기 위한 현재 상태 정리입니다. 핵심은 **Gemini CLI 기반 5개 에이전트 실행 기반은 마련되었고, 다음 단계는 역할 분리와 회의 시스템 구축**이라는 점입니다.

---

## 1. 프로젝트의 큰 목표

최종 목표는 매매 실행 봇이 아니라, **AI 에이전트들이 투자/매매 아이디어를 서로 검증하고 토론하는 연구용 회의 시스템**이다.

원칙은 다음과 같다.

- 실제 거래소 주문, 출금, 이체, 자동매매 실행 기능은 넣지 않는다.
- API key 방식은 쓰지 않는다.
- Gemini API가 아니라 **Gemini CLI + Google Pro 계정 로그인** 방식을 사용한다.
- 5개의 Gemini Pro 계정을 각각 독립된 에이전트처럼 실행한다.
- 에이전트들은 분석, 검증, 반박, 요약을 수행한다.
- 최종적으로는 전략 제안 → 다중 관점 검토 → 리스크 검토 → 백테스트 검토 → 최종 요약/보류/기각 같은 회의 구조로 발전시킨다.

---

## 2. 현재까지 완료된 단계

### 0단계: 방향 정리

초기에는 API key 방식과 Gemini CLI 로그인 방식이 혼동되었다. 이후 방향을 다음처럼 확정했다.

- Gemini API key 사용 안 함.
- `GEMINI_API_KEY_*` 사용 안 함.
- Google Pro 계정 5개를 Gemini CLI OAuth 로그인으로 사용.
- Windows + PowerShell + VS Code 환경 기준.

### 1단계: 5개 Gemini CLI 프로필 분리

각 에이전트는 서로 다른 `GEMINI_CLI_HOME`을 사용한다.

| Agent | Gemini CLI Home | Expected Account | Chrome Profile |
|---|---|---|---|
| agent_01 | `C:\gemini-profiles\agent_01` | `qhrb9292@gmail.com` | `Default` |
| agent_02 | `C:\gemini-profiles\agent_02` | `ehfkrh22@gmail.com` | `Profile 1` |
| agent_03 | `C:\gemini-profiles\agent_03` | `ehfkrh33@gmail.com` | `Profile 2` |
| agent_04 | `C:\gemini-profiles\agent_04` | `ehfkrh44@gmail.com` | `Profile 3` |
| agent_05 | `C:\gemini-profiles\agent_05` | `ehfkrh55@gmail.com` | `Profile 4` |

정상 상태의 기준은 각 프로필의 아래 파일에서 `active == expected_account`인 것이다.

```powershell
C:\gemini-profiles\agent_XX\.gemini\google_accounts.json
```

정상 예:

```json
{
  "active": "ehfkrh22@gmail.com",
  "old": []
}
```

`old`에 기대 계정이 있어도 `active`가 다르면 실패다.

---

## 3. 현재 코드 상태

현재 런타임은 **CLI-only** 정책으로 정리되었다.

확정된 정책:

- `provider: gemini_cli`만 지원.
- `src/llm/gemini_client.py`는 삭제됨.
- `google-genai` 제거됨.
- `python-dotenv` 제거됨.
- `.env`는 기본 실행에 필요 없음.
- `requirements.txt`는 최소 의존성만 유지.

현재 의존성:

```txt
pydantic>=2.7.0
PyYAML>=6.0.1
```

중요 파일:

| 파일 | 역할 |
|---|---|
| `main.py` | 사용자 메시지를 한 번 입력받고 5개 agent를 순차 실행한 뒤 세션 저장 |
| `configs/agents.yaml` | 5개 에이전트 설정, 프로필 경로, expected account, working/output dir |
| `src/agent_config.py` | agent 설정 스키마 |
| `src/agents/generic_gemini_agent.py` | CLI-only Generic Gemini Agent |
| `src/agents/agent_runner.py` | 5개 agent 순차 실행, preflight, 성공/실패 기록 |
| `src/llm/gemini_cli_client.py` | Gemini CLI subprocess 호출, JSON 파싱, preflight, timeout 처리 |
| `src/schemas/agent_response.py` | agent 응답 스키마 |
| `src/schemas/session_record.py` | 세션 저장 스키마 |
| `src/storage/session_store.py` | `data/sessions/session_*.json` 저장 |
| `tools/auth_warmup.py` | 계정 check-only / repair-login / optional verify |
| `tools/diagnose_gemini_cli.py` | CLI 진단 도구 |

---

## 4. 현재 실행 방식

### 기본 실행

```powershell
cd C:\Users\qhrb9\Desktop\agent
.\.venv\Scripts\Activate.ps1
python main.py
```

현재 `main.py`는 채팅 루프가 아니다. 한 번 실행하면 다음 흐름으로 끝난다.

```text
사용자 메시지 입력
→ agent_01~05 순차 실행
→ summary 출력
→ data/sessions/session_*.json 저장
→ PowerShell 프롬프트로 복귀
```

따라서 한 번 답하고 종료되는 것은 정상이다.

### 계정 상태 점검

```powershell
python tools/auth_warmup.py --all
```

현재 `auth_warmup.py --all`은 check-only다.

- Gemini CLI 실행 안 함.
- 브라우저 안 엶.
- 모델 호출 안 함.
- `google_accounts.json`만 읽고 `active == expected_account`인지 확인.

### 계정 복구

계정이 꼬였을 때만 사용한다.

```powershell
python tools/auth_warmup.py --agent agent_02 --repair-login
```

강제 재로그인:

```powershell
python tools/auth_warmup.py --agent agent_02 --repair-login --force-login
```

주의: 정상 상태에서 repair-login을 자주 실행하면 오히려 active 계정이 꼬일 수 있다.

### 선택적 verify

```powershell
python tools/auth_warmup.py --all --verify
```

verify는 필수 인증 단계가 아니라 headless healthcheck다.

- timeout은 계정 실패가 아닐 수 있다.
- `429 No capacity available` / `rateLimitExceeded`는 capacity/rate/burst 문제일 수 있다.
- main.py가 정상 실행되면 verify warning은 치명적이지 않다.

---

## 5. 우리가 겪었던 주요 문제와 결론

### API 방식 혼동

처음에는 Gemini API key 방식과 Gemini CLI 로그인 방식이 섞였다. 최종 결론은 CLI-only다.

금지:

- `GEMINI_API_KEY` 추가 금지.
- `google-genai` 재추가 금지.
- `provider: gemini` 또는 `gemini_api` 복구 금지.
- `src/llm/gemini_client.py` 재생성 금지.

### Codex 브랜치와 GitHub main 불일치

Codex가 자기 작업 브랜치 기준으로 “파일 없음”이라고 해도, GitHub main에는 파일이 남아 있을 수 있었다. 중요한 것은 PR diff에 실제 삭제가 들어갔는지다.

앞으로 Codex에게는 항상 이렇게 요구해야 한다.

```text
반드시 최신 origin/main 기준으로 새 브랜치를 만들어 작업하세요.
오래된 PR/브랜치/캐시된 워크스페이스 기준으로 작업하지 마세요.
```

### PowerShell `$home` 변수 문제

PowerShell에서 `$home`은 `$HOME` 자동 변수와 충돌한다. 반드시 `$profileHome`을 사용해야 한다.

잘못된 예:

```powershell
$home = "C:\gemini-profiles\agent_02"
```

올바른 예:

```powershell
$profileHome = "C:\gemini-profiles\agent_02"
```

### Chrome 프로필 / OAuth 문제

방식 B, 즉 Chrome 프로필 창을 먼저 여는 방식은 “그 창이 열린다”까지만 보장한다. Gemini CLI의 로그인 링크가 반드시 그 프로필에서 열리는 것은 아니다.

방식 C, 즉 `BROWSER` 환경변수로 강제하는 방식은 현재 Windows 환경에서 실패했다.

Auth URL Relay는 가능성이 있었지만, 현재 warmup은 기본 check-only로 정리되었고 repair-login에서만 필요할 수 있다.

최종 판정 기준은 항상:

```text
active == expected_account
```

### 인코딩 문제

한때 PowerShell `Tee-Object`가 UTF-16LE 파일을 만들어 summary가 깨졌다. 이후 Python UTF-8 저장 방식으로 회피했다.

증상:

```text
FF-FE BOM
\u0000 다량 포함
깨진 한글
```

현재 이 문제는 정리된 것으로 본다.

### Gemini CLI 불안정성

관찰된 현상:

- `429 No capacity available`
- `rateLimitExceeded`
- `Opening authentication page... [Y/n]`
- 긴 지연 후 정상 응답
- invalid JSON 비슷한 응답: `{summary:ok,...}`

현재 런타임은 fallback과 failed 격리로 대응한다. 특정 agent가 실패해도 전체 세션은 저장된다.

---

## 6. 현재 우리는 몇 단계까지 왔나

전체 로드맵 기준으로 보면 지금은 **기초 런타임 완성 단계**다.

| 단계 | 상태 | 설명 |
|---|---|---|
| 0. 아이디어 정리 | 완료 | AI 회의형 매매 연구 봇 구상 |
| 1. 실행 환경 구성 | 완료 | Windows, Python venv, GitHub, Gemini CLI |
| 2. 5개 계정 분리 | 완료 | agent별 GEMINI_CLI_HOME / expected account |
| 3. CLI-only 런타임 | 완료 | API key 제거, Gemini CLI subprocess 실행 |
| 4. 세션 저장 | 완료 | `data/sessions/session_*.json` 저장 |
| 5. 계정 check/repair 체계 | 완료 | warmup을 check-only/repair-login으로 재정의 |
| 6. 에이전트 역할 분리 | 다음 단계 | 아직 모두 범용 분석 에이전트 |
| 7. 단일 라운드 회의 | 예정 | 5개 관점 독립 응답 |
| 8. 요약자/의장 구조 | 예정 | agent_05 또는 chair가 결과 통합 |
| 9. 다중 라운드 토론 | 예정 | 반박/재검토/최종 의견 |
| 10. 전략 제안/검증 스키마 | 예정 | StrategyProposal, Review, RiskCheck 등 |
| 11. 백테스트/데이터 검증 | 예정 | 연구용 검증, 실거래 없음 |
| 12. 실거래 연동 | 보류/금지 | 현재 범위 밖, 자동매매 금지 |

현재 단계는 5번까지 완료, 6번으로 넘어가기 직전이다.

---

## 7. 다음 단계 권장 순서

다음 단계부터는 로그인/CLI 기반은 건드리지 말고 기능을 위에 얹는다.

### 다음 1단계: 역할 분리

수정 대상:

```text
prompts/agent_01.md
prompts/agent_02.md
prompts/agent_03.md
prompts/agent_04.md
prompts/agent_05.md
```

권장 역할:

| Agent | 역할 |
|---|---|
| agent_01 | 의장 / 문제 정리자 |
| agent_02 | 찬성 관점 / 가능성 탐색자 |
| agent_03 | 반대 관점 / 약점 공격자 |
| agent_04 | 리스크 관리자 / 안전성 검토자 |
| agent_05 | 최종 요약자 / 합의안 작성자 |

이 단계에서는 `main.py`, `auth_warmup.py`, `gemini_cli_client.py`를 건드리지 않는 것이 좋다.

### 다음 2단계: 단일 라운드 회의

현재처럼 5개 agent가 같은 사용자 메시지에 각자 답한다. 다만 역할이 다르므로 답변이 다르게 나와야 한다.

### 다음 3단계: 회의 결과 통합

새 기능 후보:

- `CouncilSession`
- `RoundResult`
- `FinalSummary`
- `council_runner.py`

단, 처음부터 복잡하게 가지 말고 agent_05가 agent_01~04 결과를 받아 최종 요약하는 구조부터 시작한다.

### 다음 4단계: 다중 라운드 토론

예정 구조:

```text
Round 1: 각자 초안 의견
Round 2: 서로 반박/검증
Round 3: 수정 의견
Final: 의장/요약자가 최종 결론
```

---

## 8. 다음 Codex 작업 시작 시 반드시 붙일 문구

앞으로 Codex 새 작업에는 아래 문구를 맨 위에 붙인다.

```text
반드시 최신 origin/main 기준으로 새 브랜치를 만들어 작업하세요.
오래된 PR, 오래된 작업 브랜치, 캐시된 워크스페이스 기준으로 작업하지 마세요.

현재 main의 확정 상태:
- Gemini CLI OAuth only
- API key 방식 사용 금지
- src/llm/gemini_client.py 삭제됨
- google-genai / python-dotenv 제거됨
- requirements.txt에는 pydantic, PyYAML만 있음
- main.py는 기본 실행 시 warmup 없이 바로 메시지 입력
- auth_warmup.py --all은 check-only
- repair-login은 active mismatch/AUTH_REQUIRED 때만 사용
- verify는 optional healthcheck
- active == expected_account가 최종 계정 통과 조건

금지:
- GEMINI_API_KEY 추가 금지
- google-genai 재추가 금지
- python-dotenv 재추가 금지
- provider: gemini/gemini_api 복구 금지
- src/llm/gemini_client.py 재생성 금지
- 거래소 API, 주문, 출금, 이체, 자동매매 기능 추가 금지
```

---

## 9. 다음 Codex 작업: 역할 분리 요청 초안

다음 작업은 이 정도로 시작하는 것이 안전하다.

```text
반드시 최신 origin/main 기준으로 새 브랜치를 만들어 작업하세요.
오래된 PR/브랜치 기준으로 작업하지 마세요.

현재 5개 Gemini CLI agent 런타임은 정상 동작합니다.
이번 작업에서는 로그인, warmup, CLI client, registry, main 실행 흐름을 건드리지 마세요.
오직 prompts/agent_01.md ~ prompts/agent_05.md의 역할 분리만 진행합니다.

목표:
5개 agent가 모두 같은 범용 분석 에이전트처럼 답하는 문제를 개선합니다.
각 agent별 시스템 프롬프트를 회의 역할에 맞게 다르게 설정하세요.

역할:
- agent_01: 의장 / 문제 정리자
- agent_02: 찬성 관점 / 가능성 탐색자
- agent_03: 반대 관점 / 약점 공격자
- agent_04: 리스크 관리자 / 안전성 검토자
- agent_05: 최종 요약자 / 합의안 작성자

공통 규칙:
- 한국어 응답
- AgentResponse JSON schema 준수
- 민감정보 요구 금지
- 거래소 주문/출금/이체/자동매매 실행 제안 금지
- 분석 전용
- 프로젝트 파일을 멋대로 읽거나 분석하지 말 것
- 사용자 메시지에 집중

수정 허용 파일:
- prompts/agent_01.md
- prompts/agent_02.md
- prompts/agent_03.md
- prompts/agent_04.md
- prompts/agent_05.md
- README.md는 필요 시 최소 수정만 허용

금지:
- main.py 수정 금지
- auth_warmup.py 수정 금지
- gemini_cli_client.py 수정 금지
- configs/agents.yaml 수정 금지
- API key 방식 재도입 금지
- 회의 라운드 기능 추가 금지
- DecisionEngine 추가 금지

테스트:
python -m compileall main.py src tests tools
python -m unittest tests/test_gemini_cli_client.py
```

---

## 10. 새 채팅방 / 새 Codex 작업 추천

### ChatGPT 채팅방

새 채팅방에서 진행하는 것을 추천한다.

이 채팅방은 로그인/CLI 이슈 디버깅 기록이 너무 많아서 렉이 심하고, 다음 단계의 판단을 흐릴 수 있다. 새 채팅방에는 이 Markdown 파일을 첨부하거나 내용을 붙여넣으면 된다.

### Codex

Codex도 새 작업으로 시작하는 것을 추천한다.

이유:

- 기존 Codex 작업들은 오래된 브랜치/캐시 상태 때문에 main과 불일치가 자주 발생했다.
- 다음 작업은 역할 분리라는 새 단계다.
- 반드시 최신 origin/main 기준에서 시작해야 한다.

새 Codex 작업 첫 문장은 반드시:

```text
반드시 최신 origin/main 기준으로 새 브랜치를 만들어 작업하세요.
```

로 시작한다.

---

## 11. 현재 운영 체크 명령

다음 채팅방에서 상태 확인이 필요하면 아래만 실행하면 된다.

```powershell
cd C:\Users\qhrb9\Desktop\agent
.\.venv\Scripts\Activate.ps1

git checkout main
git pull origin main

Test-Path src\llm\gemini_client.py
python tools\auth_warmup.py --all
python -m compileall main.py src tests tools
python -m unittest tests/test_gemini_cli_client.py
python main.py
```

기대:

- `Test-Path src\llm\gemini_client.py` → `False`
- `auth_warmup.py --all` → 모든 agent OK
- tests → OK
- `python main.py` → 5개 agent success 후 session 저장

---

## 12. 마지막 요약

우리가 지금 끝낸 것은 “매매 봇”이 아니라 **AI 회의 시스템을 만들기 위한 실행 기반**이다.

완료된 것:

- 5개 Gemini Pro 계정 분리
- Gemini CLI OAuth 기반 실행
- API key 방식 제거
- 계정 preflight/check/repair 구조
- 5개 agent 순차 실행
- session JSON 저장

다음에 할 것:

- agent별 역할 분리
- 단일 라운드 회의
- 최종 요약자 구조
- 다중 라운드 토론
- 전략 제안/리스크 검토/백테스트 검토 스키마

가장 중요한 원칙:

```text
로그인/CLI 기반은 이제 더 이상 건드리지 말고,
그 위에 회의 시스템을 얹는다.
```
