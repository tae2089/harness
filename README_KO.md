<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Codex_CLI-Skill-5C5C5C.svg" alt="Codex CLI Skill">
  <img src="https://img.shields.io/badge/Patterns-7_Architectures-orange.svg" alt="7 Architecture Patterns">
  <a href="https://github.com/tae2089/harness/stargazers"><img src="https://img.shields.io/github/stars/tae2089/harness?style=social" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/README-EN%20%7C%20KO%20%7C%20JA-lightgrey" alt="i18n"></a>
</p>

# Harness — OpenAI Codex CLI 서브에이전트 오케스트레이션 메타 프레임워크

[English](README.md) | **한국어** | [日本語](README_JA.md)

OpenAI Codex CLI에서 전문 서브에이전트 팀을 설계하는 메타 프레임워크. 도메인 설명 하나로 에이전트 TOML 정의, 오케스트레이터 스킬, 런타임 스캐폴딩 전체를 생성한다.

## 개요

Harness는 도메인/프로젝트에 맞는 에이전트 팀을 구성하고, 각 에이전트의 역할·샌드박스 권한을 정의하며, 오케스트레이터 스킬과 런타임 상태 관리를 완전 생성하는 메타 스킬이다. 핵심 산출물은 `.codex/agents/{name}.toml`, `.agents/skills/{orchestrator}/SKILL.md`, `AGENTS.md`이며, 런타임 상태는 모두 `_workspace/`에 영속된다.

## 설치 방법

**개인용 (글로벌):**
```bash
git clone https://github.com/tae2089/harness.git
cp -r harness/skills/codex-harness ~/.agents/skills/
```

**팀용 (레포 내):**
```bash
cp -r harness/skills/codex-harness .agents/skills/
```

설치 후 Codex CLI 세션에서 `"코덱스 하네스 구성해줘"` 발화 → `codex-harness` 스킬 자동 트리거 확인.

> **처음이라면 →** [`references/usage-examples.md`](skills/codex-harness/references/usage-examples.md) 먼저 확인. 8가지 도메인 시나리오(SSO·마이그레이션·콘텐츠 루프·병렬 리서치·장애 분석·풀스택·확장·부분 재실행)와 발화 패턴 매핑, 비트리거 발화 표 제공.

---

## 핵심 원칙

- **7대 아키텍처 패턴:** Pipeline · Fan-out/Fan-in · Expert Pool · Producer-Reviewer · Supervisor · Hierarchical · Handoff. Stage(상위 이슈/Jira Issue) → Step(하위 이슈/Jira Sub-issue) 계층으로 조합.
- **명명 컨벤션 강제:** Stage·Step 이름은 deliverable 명사구 kebab-case (`^[a-z][a-z0-9-]*$`). `main`·`step1`·`task` 같은 placeholder 금지 — workflow.md 스키마 검증에서 차단.
- **sandbox_mode 권한 제어:** 모든 에이전트에 명시적 `sandbox_mode` 필수: `read-only`(Analyst/Architect) · `workspace-write`(Coder/Reviewer/QA) · `danger-full-access`(Operator/Deployer). 와일드카드 권한 금지.
- **메인 에이전트 단일 브로커:** Codex CLI는 서브에이전트 간 직접 통신 API 부재. 모든 협업은 메인이 `_workspace/findings.md`·`tasks.md`·`checkpoint.json`·`task_*.json`으로 중개.
- **3요소 구성:** `.codex/agents/*.toml` + `.agents/skills/*/SKILL.md` + `AGENTS.md`.
- **Plan Mode 필수:** 신규 구축·확장 시 `/plan` 또는 `Shift+Tab`으로 활성화.
- **Zero-Tolerance Failure Protocol:** 임의 Skip 절대 금지. 최대 2회 재시도(총 3회) → 미해결 시 `Blocked` + 사용자 확인 요청.

## 디렉토리 구조

```
harness/
└── skills/
    └── codex-harness/
        ├── SKILL.md                              # 메인 스킬 정의
        └── references/
            ├── usage-examples.md                 # 🚀 트리거 발화 8종 + 모드 매핑
            ├── agent-design-patterns.md          # 7대 패턴 + sandbox_mode 매핑
            ├── orchestrator-template.md          # 오케스트레이터 Step 0~5 의사코드
            ├── orchestrator-procedures.md        # 에러 핸들링·blocked·handoff 절차
            ├── team-examples.md                  # 실전 협업 사례 인덱스
            ├── stage-step-guide.md               # Stage-Step 워크플로우 명세
            ├── skill-writing-guide.md            # 스킬 작성 가이드
            ├── skill-testing-guide.md            # 스킬 테스트/검증 가이드
            ├── qa-agent-guide.md                 # QA 에이전트 가이드
            ├── evolution-protocol.md             # 하네스 진화/운영 프로토콜
            ├── expansion-matrix.md               # 기존 확장 Phase 선택 매트릭스
            ├── schemas/                          # 런타임 스키마 + 에이전트 템플릿 (SoT)
            │   ├── models.md                     # ⚠️ 모델 ID 정본 + reasoning_effort 가이드
            │   ├── agent-worker.template.toml    # 워커 에이전트 TOML 기준
            │   ├── agent-state-manager.template.toml # 상태 관리자 TOML 기준
            │   ├── agent-orchestrator.template.md # 오케스트레이터 스킬 생성 기준
            │   ├── task.schema.json
            │   ├── checkpoint.schema.json
            │   ├── workflow.template.md
            │   ├── findings.template.md
            │   ├── tasks.template.md
            │   └── README.md
            └── examples/
                ├── full-bundle/sso-style.md      # 전체 산출물 패키지 시연
                ├── team/01~05-*.md               # 패턴별 협업 예시 5종
                └── step/01~05-*.md               # Stage-Step 구성 예시 5종
                    + test-scenarios.md           # 트리거 검증 시나리오
```

## 사용 방법

Plan Mode 먼저 활성화 후 자연어 발화:

```
/plan
SSO 인증 프로젝트를 위한 codex 하네스 구성해줘
```

| 발화 패턴 | 모드 |
|-----------|------|
| "코덱스 하네스 구성/구축/설계해줘", "{도메인} codex 자동화 만들어줘" | 신규 구축 |
| "기존 하네스에 {기능} 추가해줘", "에이전트 추가" | 기존 확장 |
| "하네스 점검/감사/현황", "drift 동기화" | 운영/유지보수 |
| "이전 결과 재실행/수정/보완" | 운영 (부분 재실행) |

> 새 도메인을 받으면 가장 먼저 `references/usage-examples.md`의 시나리오 8종과 매칭. 비트리거 발화 표로 false-positive 방지.

## 워크플로우 Phase

| Phase | 설명 |
|-------|------|
| Phase 0 | 현황 감사 및 모드 분기 (신규/확장/운영) |
| Phase 1 | 도메인 분석 및 패턴 매칭 (usage-examples.md 시나리오 매칭) |
| Phase 2 | 가상 팀 설계 + sandbox_mode 매핑 + 아키텍처 패턴 선택 |
| Phase 3 | 에이전트 TOML 생성 (`.codex/agents/{name}.toml`) |
| Phase 4 | 오케스트레이터 스킬 생성 (`.agents/skills/{name}/SKILL.md`) |
| Phase 5 | 통합 및 오케스트레이션 (workflow.md·findings.md·tasks.md·checkpoint.json 초기화) |
| Phase 6 | 검증 (트리거 검증, Resume, Zero-Tolerance, AGENTS.md 등록) |

> 확장·운영 모드는 `expansion-matrix.md` / `evolution-protocol.md`로 Phase 일부만 선택 실행.

## 생성 산출물

```
{프로젝트}/
├── .codex/
│   └── agents/{name}.toml              # 에이전트 정의 (TOML: 역할, sandbox_mode, 모델)
├── .agents/
│   └── skills/{orchestrator}/
│       ├── SKILL.md                    # 오케스트레이터 스킬
│       └── references/schemas/         # 스키마 사본 (필수 동봉)
├── _workspace/
│   ├── _schemas/                       # 런타임 스키마 사본 (Step 1.3에서 동기화)
│   ├── workflow.md                     # Stage(상위 이슈) → Step(하위 이슈) 구조 선언
│   ├── findings.md                     # 데이터 브로커
│   ├── tasks.md                        # 태스크 보드
│   ├── checkpoint.json                 # 재개 지점 (Durable Execution)
│   └── tasks/task_{agent}_{id}.json    # 에이전트별 산출물 메타
└── AGENTS.md                           # 하네스 포인터 + 변경 이력
```

## 7대 패턴 선택 가이드

| 패턴 | 적합한 경우 |
|------|------------|
| Pipeline | 설계 → 구현 → 검증 등 순차 의존 작업 |
| Fan-out/Fan-in | 병렬 독립 작업 후 통합 |
| Expert Pool | 상황별 전문가 선택 호출 |
| Producer-Reviewer | 생성 후 품질 검수 루프 (PASS/FIX/REDO) |
| Supervisor | 메인이 tasks.md claim으로 동적 배치 |
| Hierarchical | 팀장 → 워커 2단계 위임 (이질적 도메인) |
| Handoff | 분석 결과에 따라 다음 전문가 동적 라우팅 |

## 참고 문서

- `skills/codex-harness/SKILL.md` — 메인 스킬 정의 + 워크플로우 + 참고 인덱스
- `references/usage-examples.md` — 🚀 트리거 발화 8종 + 모드 매핑 + 비트리거 발화 + Phase 적용 매트릭스
- `references/agent-design-patterns.md` — 7대 패턴 상세, 에이전트 정의 구조, sandbox_mode 매핑
- `references/orchestrator-template.md` — 오케스트레이터 Step 0~5 의사코드, checkpoint.json 스키마
- `references/orchestrator-procedures.md` — 에러 핸들링 결정트리, blocked_protocol, handle_handoff
- `references/team-examples.md` — 패턴별 실전 사례 인덱스
- `references/stage-step-guide.md` — workflow.md 명세, Stage·Step 전환 프로토콜
- `references/skill-writing-guide.md` — 스킬 작성 패턴, 데이터 스키마 표준, 평면 Step → Stage-Step 마이그레이션
- `references/skill-testing-guide.md` — 트리거 검증, Resume 테스트, Zero-Tolerance 검증
- `references/qa-agent-guide.md` — QA 에이전트 통합 정합성 검증
- `references/evolution-protocol.md` — 하네스 진화, 운영/유지보수 워크플로우
- `references/expansion-matrix.md` — 기존 확장 Phase 선택 매트릭스
- `references/schemas/models.md` — ⚠️ 모델 ID 정본 + `model_reasoning_effort` 선택 가이드
- `references/schemas/agent-worker.template.toml` · `agent-orchestrator.template.md` — 에이전트 생성 기준 템플릿
- `references/schemas/` — 런타임 스키마 SoT (task·checkpoint·workflow·findings·tasks 템플릿)
- `references/examples/full-bundle/sso-style.md` — 전체 산출물 패키지 정본 예시
- `references/examples/team/` · `references/examples/step/` — 패턴별·구조별 상세 예제
