# PR 검증 템플릿

## 작업 목적
- 이 PR이 해결하려는 문제:
- 작업 카드 / 사용자 요청:
- 이 PR이 아닌 것:

## 변경 내용 요약
- 주요 변경:
- 동작 변경 여부:
- 문서/운영 정책 변경 여부:

## 변경 파일 목록
- 리뷰어가 먼저 볼 파일:
- 전체 변경 파일:
- 생성/수정/삭제 구분:
- Handoff evidence file (`docs/pr_handoffs/<task_slug>.md`) 또는 필요 없는 이유:

> If this PR body is generated generically or cannot include full evidence, add a task-specific handoff file under `docs/pr_handoffs/` and link it here.

## 영향 범위
- 영향 받는 기능:
- 영향 받지 않아야 하는 기능:
- 기존 동작 보존 근거:

## 테스트 결과
- 정확히 실행한 테스트 명령:
- 결과:
- 실행하지 못한 테스트와 이유:

## 수동 smoke 결과
- 정확히 실행한 smoke 명령:
- 결과:
- smoke가 필요 없는 이유:

## 예상 리스크
- 리스크 등급: docs-only / config-only / test-only / probe / adapter / readiness / strategy/scenario / runtime/LLM / execution-private-api
- 주요 실패 가능성:
- 모니터링/확인 포인트:

## 롤백 방법
- How to rollback?
- 되돌릴 파일/PR:
- 롤백 후 실행할 테스트:

## 사람이 반드시 확인해야 하는 항목
- What files should the reviewer inspect first?
- 사람 승인 필요 여부:
- 승인자가 확인해야 하는 결정:

## 금지 범위 준수 확인
- Did this PR modify src? yes/no + 이유:
- Did this PR modify tools? yes/no + 이유:
- Did this PR modify prompts? yes/no + 이유:
- Did this PR modify configs? yes/no + 이유:
- Did this PR change active strategy? yes/no:
- Did this PR add private API / API key / balance / order / transfer / auto-trading? yes/no:

## No-trade compliance
- Private API 추가 없음:
- API key / secret / token 추가 없음:
- account/balance lookup 추가 없음:
- order/cancel 추가 없음:
- withdrawal/deposit/transfer 추가 없음:
- auto-trading 추가 없음:
- Council decision to trade conversion 추가 없음:

## Codex self-check
- 목적/파일/영향/테스트/리스크/롤백/no-trade compliance를 모두 설명했는가:
- 허용 파일만 수정했는가:
- 관련 문서와 테스트를 업데이트했는가:
- high-risk 작업이면 safe-to-merge라고 주장하지 않고 명시적 human review를 요구했는가:
