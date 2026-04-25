# Changelog

## [미정] — 2026-04-25

### 추가

- **Stage-Phase 워크플로우 (3단계 계층)** — Stage(사용자 승인) → Phase(자동 전환) → Agent(실행자) 3단계 계층 모델 도입. 모든 하네스에 적용.
  - `references/stage-phase-guide.md` — workflow.md 명세, Phase·Stage 전환 프로토콜, checkpoint.json 스키마 확장(`current_phase` 필드 추가), 예시 3종.
  - `references/templates/workflow.template.md` — Stage-Phase workflow.md 템플릿 (Stage→Phase→Agent 블록 구조).
- **Phase 자동 전환 + Stage 사용자 승인 게이트** (`references/orchestrator-template.md`) — Phase 종료 시 오케스트레이터가 자동 전환, Stage 완료 시 사용자 승인 요청. checkpoint.json의 `current_stage` + `current_phase` 이중 추적.
- `references/evolution-protocol.md` — SKILL.md Phase 7(하네스 진화)의 상세 워크플로우 분리 이전.
- `references/expansion-matrix.md` — SKILL.md Phase 0(기존 확장 시 Phase 선택 매트릭스) 분리 이전.

### 변경

- **SKILL.md 다이어트** — 496줄 → 374줄 (−122줄).
  - Phase 7 내용 → `references/evolution-protocol.md`로 이전. 본문에 포인터만 유지.
  - Phase 0 확장 매트릭스 → `references/expansion-matrix.md`로 이전.
  - Phase 4 스킬 생성 가이드 → 판단 기준 + 체크리스트 15줄로 축소. 상세는 `references/skill-writing-guide.md` 참조.
- **`A+B` 복합 패턴 노테이션 폐기** — 패턴 조합은 Phase 단위로 선언하여 더 정밀하게 표현. workflow.md의 `## 패턴:` 필드는 참고 레이블로만 사용(선택).
- **`agent-design-patterns.md` "복합 패턴" 섹션** → "다단계 워크플로우 조합"으로 개명. A+B 표기 제거, Phase-단위 조합 표 형식으로 교체.
- **Stage-Phase 워크플로우 테스트 시나리오 6개** `references/skill-testing-guide.md`에 추가 (단순 구조 검증, 다단계 트리거, Phase 자동 전환, Stage 게이트, 출입 통제, 다단계 트리거).

### 하위 호환

- `stages` 필드는 Gemini CLI agent frontmatter에서 지원하지 않음 — 출입 통제는 workflow.md의 phase 블록 `활성 에이전트` 목록으로 수행.
- checkpoint.json의 신규 필드(`current_stage`, `current_phase`, `phase_history`)는 다단계 워크플로우 사용 시만 의미 있음. 단순 워크플로우는 둘 다 `"main"` 고정.
- 기존 하네스는 `workflow.md`에 Stage 1개(`main`) + Phase 1개(`main`) 구조로 마이그레이션 권장. 부재 시 동작하나 Phase 출입 통제 미적용.
