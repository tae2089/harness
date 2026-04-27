# 사용 사례: codex-harness 트리거 발화 → 처리 경로 카탈로그

`codex-harness`를 호출해 하네스를 구축·확장·운영할 때의 **실전 발화 패턴 8종**과 각 발화에 대한 처리 경로(모드 분기 → 패턴 선택 → workflow.md 구조 → 산출물). 새 도메인을 받았을 때 어느 시나리오에 가장 가까운지 매칭하여 참고한다.

> **읽는 순서:** §1 발화 → 모드 매핑 → §2 시나리오 8종 (도메인별) → §3 비트리거 발화 (false-positive 방지) → §4 Phase 적용 가이드.

---

## 1. 발화 → 모드 매핑

`codex-harness`는 트리거 직후 Phase 0에서 모드를 분기한다 (SKILL.md Phase 0 참조). 발화 패턴별 모드:

| 발화 패턴 | 모드 | 진입 Phase | 대표 키워드 |
|-----------|------|-----------|------------|
| "X 도메인 코덱스 하네스 구성/구축/설계해줘, codex 에이전트 팀 만들어줘" | **신규 구축** | Phase 1 → Phase 6 전체 | "구성", "만들어줘", "설계", "구축", "셋업" |
| "기존 하네스에 Y 기능/에이전트 추가해줘" | **기존 확장** | `expansion-matrix.md` 매트릭스 진입 → 일부 Phase 실행 | "추가", "확장", "보완", "신규 에이전트" |
| "하네스 점검/감사/현황 보고해줘" | **운영/유지보수** | `evolution-protocol.md` 워크플로우 | "점검", "감사", "현황", "drift", "동기화" |
| "이전 결과 수정/재실행/보완" | **운영 (부분 재실행)** | Phase 0에서 checkpoint.json status 분기 | "재실행", "수정", "이전 결과", "다시" |

> **명명 규칙(Jira 제목 컨벤션) 강제:** 도메인이 결정되면 Stage·Step 이름은 모두 deliverable 명사구 kebab-case (예: `sso-integration`, `requirements-gathering`). `main`·`step1` 같은 placeholder는 workflow.md 스키마 검증에서 차단(orchestrator-template.md 참조).

---

## 2. 시나리오 8종

### 시나리오 A: SSO 인증 기능 구축 (다단계, pipeline + producer_reviewer)

- **발화:** "Go 백엔드에 SSO 인증 추가해줘. 설계부터 구현·QA까지."
- **모드:** 신규 구축
- **패턴 선택 근거:** 분석→설계→구현이 순차 의존 (pipeline) + 구현 산출물 품질 검수 루프 필요 (producer_reviewer).
- **Stage/Step 구조:**
  ```
  Stage 1: research-plan        (사용자 승인 게이트: 필요)
    Step 1: requirements-gathering   pattern=pipeline
    Step 2: architecture-design      pattern=pipeline
  Stage 2: implementation-review     (마지막 stage)
    Step 1: code-and-review-loop     pattern=producer_reviewer (max 3)
  ```
- **에이전트:** `@sso-researcher`, `@sso-planner`, `@go-developer`, `@qa-reviewer`
- **산출물:** `_workspace/sso-integration/{research.md, plan.md, qa_verdict.json}`, `src/auth/*.go`
- **참고 예제:** `references/examples/full-bundle/sso-style.md`

### 시나리오 B: 대규모 코드 마이그레이션 (단일 stage, supervisor)

- **발화:** "Python 2 → 3 마이그레이션. 80개 파일 일괄 처리해줘."
- **모드:** 신규 구축
- **패턴 선택 근거:** 동종 작업 N개를 런타임 동적 배치 → supervisor (메인이 tasks.md claim).
- **Stage/Step 구조:**
  ```
  Stage 1: python3-migration
    Step 1: batch-migrate    pattern=supervisor    활성 에이전트: [@migrator-1, @migrator-2, @migrator-3]
    Step 2: integration-test pattern=pipeline       활성 에이전트: [메인]
  ```
- **에이전트:** `@migration-supervisor` (작업 등록), `@migrator-{1..N}` (워커 풀)
- **산출물:** `_workspace/python3-migration/tasks.md`, 마이그레이션된 파일들, `final/migration_report.md`
- **참고 예제:** `references/examples/team/03-supervisor.md`

### 시나리오 C: 콘텐츠 생성 + 검수 루프 (단일 stage, producer_reviewer)

- **발화:** "웹툰 에피소드 한 화 그려줘. 작가-편집자 루프로."
- **모드:** 신규 구축
- **패턴 선택 근거:** 단일 deliverable + 품질 게이트 반복 (PASS/FIX/REDO).
- **Stage/Step 구조:**
  ```
  Stage 1: webtoon-episode
    Step 1: produce-and-review   pattern=producer_reviewer (max 3)
  ```
- **에이전트:** `@webtoon-artist`, `@webtoon-reviewer`
- **산출물:** `_workspace/webtoon-episode/panels/*.png`, `review_report.md`, `final/episode.md`
- **참고 예제:** `references/examples/team/02-producer-reviewer.md`

### 시나리오 D: 병렬 리서치 + 통합 보고서 (단일 stage, fan_out_fan_in)

- **발화:** "경쟁사 4곳 동시 조사해서 통합 리포트 만들어줘."
- **모드:** 신규 구축
- **패턴 선택 근거:** 독립 조사 N개 병렬 + 통합 단계.
- **Stage/Step 구조:**
  ```
  Stage 1: competitor-research
    Step 1: parallel-scan   pattern=fan_out_fan_in   활성 에이전트: [@official, @media, @community, @background]
    Step 2: synthesize      pattern=pipeline          활성 에이전트: [@report-writer]
  ```
- **에이전트:** `@official`, `@media`, `@community`, `@background`, `@report-writer`
- **산출물:** `_workspace/competitor-research/{task_*.json, final/research_report.md}`
- **참고 예제:** `references/examples/team/01-fan-out-fan-in.md`

### 시나리오 E: 장애 분석 (handoff + persistence)

- **발화:** "프로덕션 DB 타임아웃 분석해줘. 로그 100GB 있음."
- **모드:** 신규 구축
- **패턴 선택 근거:** 분석 결과에 따라 다음 전문가가 동적 결정 (handoff) + 대용량 로그 중단 재개 가능해야 함 (persistence).
- **Stage/Step 구조:**
  ```
  Stage 1: incident-resolution
    Step 1: triage            pattern=handoff           활성 에이전트: [@incident-triage]
    Step 2: targeted-fix      pattern=producer_reviewer 활성 에이전트: [동적 결정 — handoff_chain]
  ```
- **에이전트:** `@incident-triage`, `@db-fixer`, `@network-fixer`, `@app-fixer`
- **산출물:** `_workspace/incident-resolution/{handoff_chain, final/incident_report.md}`, checkpoint.json `handoff_chain` 추적
- **참고 예제:** `references/examples/team/05-handoff-persistence.md`

### 시나리오 F: 풀스택 기능 개발 (hierarchical)

- **발화:** "결제 모듈 추가. 프론트·백엔드·DB 동시 진행해줘."
- **모드:** 신규 구축
- **패턴 선택 근거:** 도메인 이질 팀 (프론트·백엔드·DB) + 2단계 위임 (팀 리드 → 워커).
- **Stage/Step 구조:**
  ```
  Stage 1: payment-feature       (사용자 승인 게이트: 필요 — 설계 검토)
    Step 1: cross-team-design    pattern=hierarchical   활성 에이전트: [@frontend-team-lead, @backend-team-lead]
    Step 2: parallel-implement   pattern=hierarchical   활성 에이전트: [@ui-designer, @state-engineer, @api-designer, @db-engineer]
  Stage 2: integration-validate
    Step 1: cross-check          pattern=pipeline       활성 에이전트: [@project-architect]
  ```
- **에이전트:** `@project-architect` (전체 설계+검증), 팀 리드 2명, 워커 4명
- **산출물:** `_workspace/payment-feature/{00_architecture.md, frontend/, backend/, final/integration_report.md}`
- **참고 예제:** `references/examples/team/04-hierarchical.md`

### 시나리오 G: 기존 하네스에 보안 검증 단계 추가 (확장 모드)

- **발화:** "기존 SSO 하네스에 보안 검증 Stage 추가해줘. QA 후에."
- **모드:** 기존 확장
- **분류 (expansion-matrix.md):** "Stage/Step 추가" — Stage 수 증가 (2 → 3).
- **실행 Phase:** Phase 2(workflow.md 재설계) + Phase 3(`@security-auditor` 에이전트 추가) + Phase 5(오케스트레이터 수정) + Phase 6-6(resume 흐름 테스트).
- **변경 결과:**
  ```
  Stage 1: research-plan         (기존)
  Stage 2: implementation-review (기존)
  Stage 3: security-audit        (신규, 사용자 승인 게이트: 필요)
    Step 1: vulnerability-scan   pattern=fan_out_fan_in
    Step 2: pen-test             pattern=pipeline
  ```
- **AGENTS.md 변경 이력 기록 필수.**
- **참고:** `references/expansion-matrix.md` 케이스 D.

### 시나리오 H: 이전 분석 결과 부분 재실행 (운영/부분 재실행)

- **발화:** "지난 주 SSO 분석에서 plan.md만 다시 생성해줘. research는 그대로."
- **모드:** 운영 (부분 재실행)
- **Phase 0 분기:** `checkpoint.json status: "completed"` 발견 → 부분 재실행 모드.
- **처리:**
  1. 사용자에게 영향 범위 확인 (사용자 확인 요청).
  2. `_workspace/sso-integration/`의 `research.md` 보존, `plan.md` 삭제.
  3. checkpoint.json `current_stage: "research-plan"`, `current_step: "architecture-design"`, `status: "in_progress"`로 되돌림.
  4. Step 2부터 재실행. 이후 Stage는 영향 분석 후 재실행 여부 결정.
- **참고:** `references/orchestrator-template.md` Step 0 (resume vs partial vs new) + `references/evolution-protocol.md`.

---

## 3. 비트리거 발화 (false-positive 방지)

다음 발화는 **codex-harness를 호출하지 않는다.** 직접 응답 또는 다른 스킬 호출.

| 발화 | 사유 | 처리 |
|------|------|------|
| "이 함수 버그 고쳐줘" | 단일 코드 수정 — 하네스 필요 없음 | 직접 코드 편집 |
| "Go에서 channel 쓰는 법 알려줘" | 단순 질문 | 직접 응답 |
| "테스트 한 번 돌려줘" | 단일 명령 | `run_shell_command` 직접 |
| "tasks.md 항목 하나만 수정해줘" | 기존 산출물 단일 편집 | `apply_patch` 직접 (단, 메인 에이전트가 갱신 책임 있는 경우는 오케스트레이터 호출) |
| "오케스트레이터 코드 한 줄 고쳐줘" | 단일 편집 | 직접 편집. 단, 흐름 변경이면 운영 모드로 진입 (`evolution-protocol.md`) |

> **경계선 발화 (애매):** "에이전트 하나 추가해줘" — 단일 에이전트 추가는 **확장 모드**로 진입 (Phase 3·4·5만 실행). expansion-matrix.md 매트릭스로 Phase 결정.

---

## 4. Phase 적용 가이드

| 모드 | 실행 Phase | 핵심 산출물 |
|------|-----------|-------------|
| 신규 구축 | Phase 1 ~ Phase 6 (전체) | `.codex/agents/*.toml`, `.codex/skills/{orchestrator}/SKILL.md`, `AGENTS.md`, `_workspace/_schemas/`, workflow.md, findings.md, tasks.md, checkpoint.json |
| 기존 확장 | expansion-matrix.md 매트릭스로 결정 (보통 Phase 2·3·5·6-6) | 변경 대상 파일만 + `AGENTS.md` 변경 이력 |
| 운영/유지보수 | Phase 0 → evolution-protocol.md | 감사 보고서 + drift 정정 |
| 부분 재실행 | Phase 0 (checkpoint 되감기) → Phase 2부터 | 영향받는 산출물만 |

> **공통 필수:** 모드 무관하게 (1) Plan Mode 진입(yolo 제외), (2) Phase 0 현황 감사, (3) Zero-Tolerance 실패 프로토콜(최대 2회 재시도(총 3회) → Blocked + ask_user), (4) Stage·Step 명명 컨벤션 검증.

---

## 5. 매칭이 안 될 때

위 8 시나리오와 가까운 도메인이 없으면:

1. **패턴 분해:** 작업의 의존성 그래프를 그리고 (병렬/순차/루프/동적할당/이질적위임/동적라우팅) 7대 패턴 중 매칭.
2. **Stage 경계:** 사용자 승인이 필요한 지점을 Stage 경계로 설정.
3. **유사 시나리오 조합:** 예) "병렬 리서치(D) → SSO 구현(A)"처럼 시나리오를 직렬 결합.
4. **에이전트 설계:** `references/agent-design-patterns.md`의 상호작용 스타일 + 도구 매핑 적용.
5. **불확실 시 ask_user.** 하네스 구조를 추측으로 결정하지 말고 사용자 확인.
