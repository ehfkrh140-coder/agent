# agent-runtime-core

초보자도 Windows + VS Code + PowerShell에서 바로 실행할 수 있는 **Gemini API 기반 범용 AI 에이전트 실행 프로젝트**입니다.

이 단계에서는 역할별 클래스(Bull/Bear/Risk)를 만들지 않고, **GenericGeminiAgent 1개 구현 + 설정 파일로 5개 에이전트 실행** 구조만 제공합니다.

---

## 1) 이 프로젝트가 하는 일

- `configs/agents.yaml`에서 에이전트 5개 설정을 읽습니다.
- 각 에이전트는 `.env`의 Gemini API Key를 사용해 실제 Gemini API를 호출합니다.
- 각 에이전트는 `prompts/*.md`의 시스템 프롬프트를 읽습니다.
- 응답은 Pydantic 스키마(`AgentResponse`) 형식의 JSON 구조화 응답으로 받습니다.
- 한 에이전트가 실패해도 전체는 계속 실행됩니다.
- 실행 결과를 `data/sessions/session_<timestamp>.json`에 저장합니다.

---

## 2) Windows에서 설치 방법

PowerShell에서 아래 순서대로 실행하세요.

### 2-1. Python 설치 확인
```powershell
py --version
```

### 2-2. 가상환경 만들기
```powershell
py -m venv .venv
```

### 2-3. 가상환경 활성화
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2-4. 패키지 설치
```powershell
pip install -r requirements.txt
```

---

## 3) VS Code에서 여는 방법

1. VS Code 실행
2. **File > Open Folder...**
3. `agent-runtime-core` 폴더 선택
4. 터미널 열기: **Terminal > New Terminal** (PowerShell 권장)
5. 인터프리터 선택: `Ctrl+Shift+P` → `Python: Select Interpreter` → `.venv` 선택

---

## 4) PowerShell에서 실행 방법

### 4-1. `.env` 파일 만들기
```powershell
Copy-Item .env.example .env
```

### 4-2. `.env`에 Gemini API Key 5개 입력
`.env` 파일을 열고 아래 값을 채우세요.

```env
GEMINI_API_KEY_01=your_real_key_1
GEMINI_API_KEY_02=your_real_key_2
GEMINI_API_KEY_03=your_real_key_3
GEMINI_API_KEY_04=your_real_key_4
GEMINI_API_KEY_05=your_real_key_5
```

### 4-3. 실행
```powershell
python main.py
```

메시지를 입력하면 5개 에이전트가 순서대로 실행됩니다.

---

## 5) `.env` 설정 방법 (중요)

- `.env`는 절대 Git에 올리지 마세요.
- 키 이름은 `configs/agents.yaml`의 `api_key_env`와 정확히 일치해야 합니다.
- 키가 비어있거나 오타가 있으면 해당 에이전트는 `failed` 상태로 저장됩니다.

---

## 6) 폴더/파일 역할

- `main.py`: 실행 진입점. 사용자 입력 받고 5개 에이전트 실행.
- `configs/agents.yaml`: 에이전트 5개 설정.
- `prompts/*.md`: 에이전트별 시스템 프롬프트.
- `src/config_loader.py`: YAML 설정 로딩.
- `src/agent_config.py`: 에이전트 설정 Pydantic 모델.
- `src/llm/gemini_client.py`: Gemini API 호출 및 JSON 구조화 응답 처리.
- `src/agents/generic_gemini_agent.py`: 단일 범용 Gemini 에이전트 구현.
- `src/agents/agent_registry.py`: 설정 기반 에이전트 생성(API key 주입).
- `src/agents/agent_runner.py`: 여러 에이전트 순차 실행 + 실패 격리.
- `src/schemas/agent_response.py`: 에이전트 응답 스키마.
- `src/schemas/session_record.py`: 세션 저장 스키마.
- `src/storage/session_store.py`: 실행 결과 JSON 파일 저장.
- `data/sessions/`: 실행 결과 파일이 저장되는 폴더.

---

## 7) 에이전트 역할을 나중에 바꾸는 방법

지금은 GenericGeminiAgent 하나만 사용합니다.

나중에 역할을 바꾸려면:
1. `prompts/agent_01.md`~`agent_05.md` 내용을 역할별로 수정
2. `configs/agents.yaml`에서 `name`, `model`, `temperature`, `system_prompt_path` 변경

즉, **코드 수정 없이 설정/프롬프트 중심으로 역할을 바꿀 수 있는 구조**입니다.

---

## 8) 현재 금지된 기능

이 프로젝트는 아래 기능을 구현하지 않습니다.

- 거래소 API 연동
- 주문/취소/출금/이체 함수
- 자동매매/라이브 트레이딩
- 백테스트
- function calling
- Bull/Bear/Risk 전용 클래스
- DecisionEngine
- Docker/WSL/Linux 전용 실행 방식

---


## 첫 실제 실행 테스트 체크리스트

아래 순서를 그대로 점검하세요.

- [ ] `.env` 작성 확인 (Gemini API Key 5개 입력)
- [ ] `py -m venv .venv`
- [ ] `.\.venv\Scripts\Activate.ps1`
- [ ] `pip install -r requirements.txt`
- [ ] `python main.py`
- [ ] `data/sessions` 폴더에 `session_<timestamp>.json` 파일 생성 확인

---

## 9) 자주 나는 오류와 해결 방법

### 오류 A: `ModuleNotFoundError`
원인: 가상환경 미활성화 또는 패키지 미설치
해결:
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 오류 B: API 키 관련 실패
원인: `.env` 누락, 변수명 오타, 빈 값
해결:
- `.env` 파일이 프로젝트 루트에 있는지 확인
- 변수명이 `GEMINI_API_KEY_01` 형식과 일치하는지 확인
- 실제 키가 들어갔는지 확인

### 오류 C: 프롬프트 파일 없음
원인: `configs/agents.yaml`의 `system_prompt_path` 경로 오타
해결:
- 예: `prompts/agent_01.md` 파일이 실제 존재하는지 확인

### 오류 D: Gemini 응답 파싱 실패
원인: 모델 응답이 스키마와 맞지 않거나 일시적인 API 문제
해결:
- 다시 실행
- 프롬프트를 더 명확하게 수정
- 모델명을 점검 (`configs/agents.yaml`)

---

## 빠른 실행 요약

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# .env에 키 5개 입력
python main.py
```
