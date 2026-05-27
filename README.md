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
