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


## 인증 워밍업
- 전체: `python tools/auth_warmup.py --all`
- 단일: `python tools/auth_warmup.py --agent agent_02`
- warmup 중 `yy`를 입력하면 `Authentication cancelled`가 날 수 있습니다. 이 경우 해당 agent만 다시 실행하세요.
- `AUTH_REQUIRED`가 뜨면 해당 agent warmup이 필요합니다.
- timeout이 잦으면 `timeout_seconds`를 60~90으로 늘려보세요. 디버깅 중에는 30으로 줄일 수 있습니다.
- 계정 확인 예: `Get-Content C:\gemini-profiles\agent_02\.gemini\google_accounts.json`
- PowerShell에서는 `$home` 대신 `$profileHome` 사용하세요.

- `ModuleNotFoundError: No module named 'src'`가 warmup에서 발생하면 import path 문제일 수 있습니다.
- 최신 코드의 `tools/auth_warmup.py`는 프로젝트 루트를 `sys.path`에 추가해 이 문제를 해결합니다.
- `main.py`는 warmup 실패 시 계속 진행 여부를 물어봅니다.


## Warmup 모드 분리 (중요)
- `Path not in workspace` 에러는 보안 제한 장치가 정상 작동한 것입니다.
- 하지만 warmup에서 도구 호출이 발생하는 것은 바람직하지 않으므로 warmup을 분리했습니다.
- **login-only**: `gemini.cmd`만 interactive 실행 (사용자가 직접 로그인 후 `/quit`).
- **verify**: 짧은 headless 호출로 profile 사용 가능 여부만 점검.

권장 순서:
```powershell
python tools/auth_warmup.py --all --login-only
python tools/auth_warmup.py --all --verify
python main.py --skip-warmup
```

기본 `python tools/auth_warmup.py --all` 은 login-only → verify를 순서대로 실행합니다.

주의:
- `$home` 사용 금지, `$profileHome` 사용
- OAuth credential/token 파일은 절대 열거나 공유하지 말 것
- active 계정이 expected_account와 일치해야 정상
- old 목록에 계정이 있어도 active가 다르면 잘못된 상태
- `429 No capacity available`은 계정 매핑 문제가 아니라 capacity/rate 문제일 수 있음


## Run 모드
- `headless_capture`: 완전 자동 실행용. 인증 프롬프트가 뜨면 AUTH_REQUIRED 실패 가능.
- `interactive_file`(기본): 터미널과 연결되어 실행 중 Y/n 입력 가능.
  결과는 `output_dir`(예: `C:\gemini-agent-outputs\agent_01`)에 저장된 파일을 다시 읽어 파싱합니다.

Google Pro CLI 방식에서는 `interactive_file`이 기본 운영에 더 안정적입니다.
완전 무인 자동화가 필요하면 API key/Vertex AI가 일반적으로 더 적합하지만, 이 프로젝트는 API key를 사용하지 않습니다.

권장 실행:
```powershell
python tools/auth_warmup.py --all --login-only
python main.py --skip-warmup
```

또는 `python main.py` 실행 중 Y/n 프롬프트가 나오면 Y를 입력하세요.


## 브라우저 인증 운영 정책 (방식 B/C)
- 기본 운영은 **방식 B(preopen)** 입니다. agent별 Chrome 프로필 창을 먼저 열고 로그인 상태를 확인한 뒤 Gemini CLI login-only를 진행합니다.
- 방식 C(BROWSER 환경변수)는 이 환경에서 실패했으며 **experimental** 입니다.
- wrapper log가 생성되지 않고 기본 Chrome 프로필이 열리면 BROWSER 방식 실패로 판단합니다.
- Chrome profile-directory 확인: `chrome://version` -> `Profile Path`의 마지막 폴더명
- 현재 매핑: agent_01=Default, agent_02=Profile 1, agent_03=Profile 2, agent_04=Profile 3, agent_05=Profile 4
- 최종 판정은 `active == expected_account` 입니다. old 목록에 expected가 있어도 active가 다르면 실패입니다.
- 하나의 Chrome 프로필에서 여러 계정을 고르면 active 계정이 꼬일 수 있습니다.
- `$home` 사용 금지, `$profileHome` 사용.
- verify는 선택적 headless healthcheck이며 필수 인증 단계가 아닙니다. verify timeout은 기본 warning, `--strict-verify`에서만 failed 처리합니다.
- `429 No capacity available` / `rateLimitExceeded`는 계정 매핑 오류가 아니라 capacity/rate/burst/IP 문제일 수 있습니다.
- 과거 FF-FE BOM(UTF-16LE) 문제는 Tee-Object 저장 방식에서 발생했으며, 현재는 Python UTF-8 저장 방식으로 회피합니다.


## Auth URL Relay (기본)
- 방식 B(preopen) 단독은 Chrome 프로필 창을 먼저 여는 것만 보장하며, Gemini CLI 로그인 링크가 반드시 그 창에서 열리는 것은 보장하지 않습니다.
- 방식 C(BROWSER env)는 현재 Windows 환경에서 실패했으며 experimental 입니다.
- 기본 운영 방식은 **Auth URL Relay** 입니다.
- Auth URL Relay는 Gemini CLI 출력의 인증 URL을 감지해, 지정된 Chrome `profile-directory`로 다시 엽니다.
- 사용자는 여전히 Y 입력과 브라우저 로그인은 직접 수행해야 합니다(자동 Y 입력 없음).
- 최종 판정은 `active == expected_account`입니다. old에 expected가 있어도 active가 다르면 실패입니다.
- 하나의 Chrome 프로필에서 여러 Google 계정을 선택하면 active가 꼬일 수 있습니다.
- OAuth token/credential 내용은 절대 공유하지 마세요.
- verify는 선택적 headless healthcheck입니다. timeout은 기본 warning이며 strict 모드에서만 failed 처리합니다.
- `429 No capacity available` / `rateLimitExceeded`는 계정 매핑 오류가 아니라 capacity/rate/burst/IP 문제일 수 있습니다.


## Warmup (Account Check/Repair)
- `python tools/auth_warmup.py --all` is **check-only** by default (no Gemini CLI call, no browser open).
- If an agent mismatches, run: `python tools/auth_warmup.py --agent agent_02 --repair-login`.
- Use `--force-login` only when you intentionally want re-login even when active==expected.
- `--verify` is optional headless healthcheck (not required for normal authenticated runs).
