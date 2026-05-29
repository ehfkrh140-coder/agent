# agent-runtime-core

Windows + VS Code + PowerShell에서 실행하는 Gemini CLI 기반 멀티 에이전트 런타임입니다.

## 핵심
- 기본 실행 방식은 `gemini_cli`입니다.
- 5개 Pro 계정을 분리하려면 **agent별로 서로 다른 `GEMINI_CLI_HOME`**을 써야 합니다.
- `active` 계정이 `expected_account`와 일치해야 올바른 계정 매핑입니다.
- old 목록에 계정이 있어도 active가 다르면 잘못된 상태입니다.

## 실행 전 주의
- OAuth credential/token 파일 내용은 절대 열거나 공유하지 마세요.
- `google_accounts.json`은 active 계정 확인용으로만 사용하세요.
- `Opening authentication page`가 보이면 해당 agent는 수동 재로그인이 필요합니다.
- timeout 발생 시 해당 `gemini_cli_home`을 백업/초기화 후 재로그인하세요.
- `429 No capacity available`은 계정 매핑 오류가 아니라 capacity/rate 이슈일 수 있습니다.
- Windows에서는 `cli_command: gemini.cmd` 권장.
- `working_dir`은 프로젝트 폴더가 아니라 `C:\gemini-agent-workspaces\agent_XX` 권장.

## 설치
```powershell
py --version
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 프로필 수동 점검 스크립트 (PowerShell)
`$home` 변수명 사용 금지. `$HOME` 읽기 전용 자동 변수와 충돌합니다.
반드시 `$profileHome`을 사용하세요.

```powershell
foreach ($n in 1..5) {
    $id = "{0:D2}" -f $n
    $profileHome = "C:\gemini-profiles\agent_$id"

    Write-Host "`n==============================="
    Write-Host "Testing agent_$id"
    Write-Host "GEMINI_CLI_HOME = $profileHome"
    Write-Host "==============================="

    $env:GEMINI_CLI_HOME = $profileHome
    $env:GEMINI_FORCE_ENCRYPTED_FILE_STORAGE = "true"
    $env:GEMINI_FORCE_FILE_STORAGE = "true"
    $env:GEMINI_CLI_TRUST_WORKSPACE = "true"
    $env:NO_COLOR = "1"
    $env:TERM = "dumb"

    Get-Content "$profileHome\.gemini\google_accounts.json" -ErrorAction SilentlyContinue

    $prompt = '반드시 다음 JSON만 출력하세요: {"summary":"ok","key_points":[],"concerns":[],"questions":[],"suggested_next_steps":[],"confidence":1.0}'
    gemini.cmd --skip-trust -p $prompt --output-format json
}
```

## 실행
```powershell
python main.py
```

실행 중 preflight에서 각 agent의 active/expected 계정을 마스킹해서 확인합니다.
일치하지 않으면 해당 agent는 실패 처리되고 실제 호출을 건너뜁니다.

## 테스트
```powershell
python -m compileall main.py src tests
python -m unittest tests/test_gemini_cli_client.py
```


## Preflight와 Healthcheck 차이
- 기본 실행(`python main.py`)의 preflight는 **모델 호출 없이** `google_accounts.json` 파일만 검사합니다.
- 그래서 agent_02처럼 preflight 단계에서 20초 timeout으로 멈추는 문제를 방지합니다.
- 실제 모델 호출 점검은 별도 `healthcheck_profile` 또는 수동 PowerShell 점검 스크립트에서만 수행하세요.


## Troubleshooting
- preflight OK 후 멈추면, 이는 preflight가 아니라 실제 `agent.run` 단계의 Gemini CLI timeout 문제일 수 있습니다.
- `timeout_seconds`를 30으로 낮춰 디버깅하세요(기본값 반영됨).
- agent별 `working_dir`이 빈 폴더인지 확인하세요.
- Gemini CLI는 코딩 CLI 특성상 workspace context를 붙일 수 있습니다.
- timeout 발생 시 해당 프로필로 수동 테스트:

```powershell
$env:GEMINI_CLI_HOME="C:\gemini-profilesgent_01"
gemini.cmd --skip-trust -p '반드시 JSON만 출력' --output-format json
```


- preflight OK 후 멈추는 경우는 계정 문제가 아니라 run 단계에서 gemini.cmd/node.exe 프로세스 정리 문제일 수 있습니다.
- Windows에서 gemini.cmd는 node.exe 자식 프로세스를 띄울 수 있습니다.
- timeout 시 `taskkill /T /F /PID`로 프로세스 트리를 종료해야 합니다.
- timeout이 나도 해당 agent만 failed 처리되고 다음 agent로 넘어가야 정상입니다.
- 직접 수동 실행은 되는데 main.py에서 멈추면 subprocess 프로세스 정리 이슈를 의심하세요.


## Warmup (Account Check/Repair)
- `python tools/auth_warmup.py --all` is **check-only** by default (no Gemini CLI call, no browser open).
- If an agent mismatches, run: `python tools/auth_warmup.py --agent agent_02 --repair-login`.
- Use `--force-login` only when you intentionally want re-login even when active==expected.
- `--verify` is optional headless healthcheck (not required for normal authenticated runs).


## Final CLI-only policy
- This runtime supports **Gemini CLI OAuth only**.
- API key mode is not supported, and `.env` is not required for the default workflow.

### 기본 실행
```powershell
python main.py
```

### 계정 상태 점검 (check-only)
```powershell
python tools/auth_warmup.py --all
```

### 계정 복구
```powershell
python tools/auth_warmup.py --agent agent_02 --repair-login
```

### 강제 재로그인
```powershell
python tools/auth_warmup.py --agent agent_02 --repair-login --force-login
```

### 선택적 healthcheck
```powershell
python tools/auth_warmup.py --all --verify
```

### 핵심 정책
- `active == expected_account` 가 최종 통과 조건입니다.
- `old`에 expected가 있어도 `active`가 다르면 실패입니다.
- verify timeout은 계정 실패가 아닐 수 있습니다(용량/지연 이슈 가능).
- PowerShell에서는 `$home` 대신 `$profileHome`을 사용하세요.
- OAuth token/credential 내용은 출력/공유하지 마세요.

## Council-ready runtime speed/session groundwork
- 현재 runtime은 AI Council 회의 시스템을 위한 **기초 런타임 단계**이며, 아직 실제 회의 라운드 구현은 아닙니다.
- 기본 실행은 기존과 동일하게 sequential입니다.
- 속도 개선 테스트는 아래처럼 실행할 수 있습니다.

```powershell
python main.py --parallel --max-workers 2
```

- `max_workers=2`를 권장합니다.
- `max_workers=5`는 개별 agent latency가 늘거나 `429` / capacity 문제가 생길 수 있어 권장하지 않습니다.
- 현재 `-p` / `--prompt` headless 실행은 자동화와 JSON 파싱에는 안정적이지만, 매번 새 Gemini CLI 프로세스를 시작하므로 느릴 수 있습니다.
- `--prompt-interactive`는 빠를 수 있지만 persistent process/TUI 관리가 복잡하므로 이번 단계에서는 구현하지 않습니다.
- `--resume latest`는 일부 환경에서 속도 개선 가능성이 있었지만, 맥락 오염 위험이 있어 이번 단계에서는 자동 적용하지 않습니다.
- 이번 단계에서는 Gemini CLI outer JSON의 `session_id`를 `cli_session_id`로 저장만 합니다. 나중에 회의 라운드 구현 시 resume 실험에 사용할 수 있습니다.
- `configs/agents.yaml`의 `model` 필드는 실험용 CLI model 직접 지정 옵션입니다. 비워두면 기본 Gemini CLI 설정을 사용합니다.
- 이 시스템은 매매 실행부가 아니라 AI Council 판단부 기반입니다.
- 거래소 API, 주문, 출금, 이체, 자동매매 기능은 아직 구현하지 않습니다.
