# agent-runtime-core

초보자도 Windows + VS Code + PowerShell에서 실행할 수 있는 **Gemini 기반 멀티 에이전트 런타임**입니다.

현재 기본 provider는 **gemini_cli** 입니다. 즉, API 키 없이도(선택) 각 에이전트별 Gemini CLI 로그인 프로필(OAuth/Google 로그인)을 분리해 실행할 수 있습니다.

---

## 이 프로젝트가 하는 일

- `configs/agents.yaml`에서 에이전트 5개 설정을 읽습니다.
- 각 에이전트를 순서대로 실행합니다.
- 응답은 `AgentResponse` Pydantic 스키마(JSON)로 검증합니다.
- 1개 에이전트가 실패해도 나머지는 계속 실행합니다.
- 결과를 `data/sessions/session_<timestamp>.json`으로 저장합니다.

---

## Windows 설치 및 실행 (PowerShell)

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

---

## gemini_cli 기반 실행 방법 (기본)

## 1) agent별 홈 폴더 준비

`configs/agents.yaml` 기본값:

- `C:\gemini-profiles\agent_01`
- `C:\gemini-profiles\agent_02`
- `C:\gemini-profiles\agent_03`
- `C:\gemini-profiles\agent_04`
- `C:\gemini-profiles\agent_05`

필요하면 경로는 자유롭게 바꿀 수 있습니다.

## 2) 각 프로필로 로그인

아래를 **각 agent 폴더별로 1회씩** 실행해 로그인합니다.

```powershell
$env:GEMINI_CLI_HOME="C:\gemini-profiles\agent_01"
gemini
```

로그인 완료 후 종료하고, agent_02~agent_05도 같은 방식으로 각각 로그인합니다.

## 3) active 계정 확인

각 프로필 폴더의 `google_accounts.json`으로 현재 active 계정을 확인할 수 있습니다.

예시 경로:
- `C:\gemini-profiles\agent_01\google_accounts.json`

> 주의: credential 파일 내용/토큰은 절대 공유하거나 출력하지 마세요.

## 4) 런타임 실행

```powershell
python main.py
```

런타임은 agent별 `GEMINI_CLI_HOME`을 주입해서 서로 다른 로그인 프로필을 사용합니다.

---

## gemini_cli 출력 파싱 구조

`--output-format json`의 출력은 보통 아래처럼 **바깥 JSON**입니다:

- 바깥 JSON 객체
  - `response`: 모델 응답 문자열

이 `response` 문자열 안에 실제 `AgentResponse` JSON이 들어옵니다.
런타임은 다음 순서로 파싱합니다:

1. stdout에서 첫 번째 JSON 객체 추출
2. 바깥 JSON 파싱
3. `response` 필드 읽기
4. `response` 안에 ```json ... ``` 코드블록이 있으면 제거
5. 내부 JSON 파싱
6. `AgentResponse`로 검증

또한 stdout/stderr에 ripgrep 경고 같은 일반 텍스트가 섞여도, **정상 JSON 파싱이 되면 실패로 보지 않습니다**.

---

## API key provider도 유지됨 (선택)

`provider: gemini_cli`가 기본이며, 필요 시 `provider: gemini_api` 또는 하위호환 `provider: gemini`로 API key 방식도 사용할 수 있습니다.

- 이 경우 `api_key_env`가 필요합니다.
- 기본 템플릿은 `gemini_cli`로 설정되어 있습니다.

---


## 빠른 상태 점검 (오류 진단)

`python main.py` 실행 시 `GEMINI_API_KEY_01`을 요구하면 설정이 잘못된 상태입니다.
기본값이 `gemini_cli`여야 하며, 아래 명령으로 바로 점검하세요.

```powershell
# 1) provider가 gemini_cli인지 확인
Select-String -Path .\configs\agents.yaml -Pattern "provider:\s*gemini_cli"

# 2) API key 항목이 남아있는지 확인(아무것도 안 나오면 정상)
Select-String -Path .\configs\agents.yaml -Pattern "GEMINI_API_KEY_0[1-5]"

# 3) Gemini CLI 클라이언트 파일 존재 확인
Test-Path .\src\llm\gemini_cli_client.py
```

## 첫 실제 실행 테스트 체크리스트

- [ ] `.env` 작성 확인 (gemini_api 사용할 때만 필요)
- [ ] `py -m venv .venv`
- [ ] `.\.venv\Scripts\Activate.ps1`
- [ ] `pip install -r requirements.txt`
- [ ] `python main.py`
- [ ] `data/sessions` 폴더에 `session_<timestamp>.json` 생성 확인

---

## 폴더/파일 역할

- `main.py`: 실행 진입점
- `configs/agents.yaml`: 에이전트 설정
- `prompts/*.md`: agent 시스템 프롬프트
- `src/llm/gemini_cli_client.py`: Gemini CLI 실행/파싱
- `src/llm/gemini_client.py`: Gemini API key 호출
- `src/agents/generic_gemini_agent.py`: provider별 실행 분기
- `src/agents/agent_runner.py`: 5개 순차 실행 + 실패 격리
- `src/schemas/agent_response.py`: 응답 스키마
- `src/storage/session_store.py`: 세션 JSON 저장

---

## 현재 금지된 기능

- DecisionEngine
- Bull/Bear/Risk 전용 역할 클래스
- 거래소 API
- 주문/출금/이체/자동매매
- function calling
