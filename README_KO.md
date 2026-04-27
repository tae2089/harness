<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Gemini_CLI-Skill-4285F4.svg" alt="Gemini CLI Skill">
  <img src="https://img.shields.io/badge/Patterns-7_Architectures-orange.svg" alt="7 Architecture Patterns">
  <a href="https://github.com/tae2089/harness/stargazers"><img src="https://img.shields.io/github/stars/tae2089/harness?style=social" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/README-EN%20%7C%20KO%20%7C%20JA-lightgrey" alt="i18n"></a>
</p>

# Harness — Coding Agent 서브에이전트 오케스트레이션 메타 프레임워크

[English](README.md) | **한국어** | [日本語](README_JA.md)

Coding Agent(특히 Gemini CLI)에서 전문 서브에이전트 팀과 협업 스킬을 설계하는 메타 프레임워크.

## 개요

Harness는 도메인/프로젝트에 맞는 에이전트 팀을 구성하고, 각 에이전트의 역할·도구 권한을 정의하며, 공통 절차 스킬과 오케스트레이터를 생성하는 메타 스킬이다. 핵심 산출물은 `.gemini/agents/`, `.gemini/skills/`, `GEMINI.md`이며, 런타임 상태는 모두 `_workspace/`에 영속된다.

## 설치 방법

```bash
gemini skills install https://github.com/tae2089/harness.git --path skills
```

설치 후 Gemini CLI 세션에서 `"하네스 구성해줘"` 발화 → `gemini-harness` 스킬 자동 트리거 확인.

> **처음이라면 →** [`references/usage-examples.md`](skills/gemini-harness/references/usage-examples.md) 먼저 확인. 8가지 도메인 시나리오(SSO·마이그레이션·콘텐츠 루프·병렬 리서치·장애 분석·풀스택·확장·부분 재실행)와 발화 패턴 매핑, 비트리거 발화 표 제공.

---

## 핵심 원칙

- **7대 아키텍처 패턴:** Pipeline · Fan-out/Fan-in · Expert Pool · Producer-Reviewer · Supervisor · Hierarchical · Handoff. Stage(상위 이슈/Jira Issue) → Step(하위 이슈/Jira Sub-issue) 계층으로 조합.
- **명명 컨벤션 강제:** Stage·Step 이름은 deliverable 명사구 kebab-case (`^[a-z][a-z0-9-]*$`). `main`·`step1`·`task` 같은 placeholder 금지 — workflow.md 스키마 검증에서 차단.
- **엄격한 도구 권한 제어:** `tools: ["*"]` 금지. 모든 에이전트 필수 도구: `ask_user`, `activate_skill`. `invoke_agent`는 오케스트레이터·Supervisor·Hierarchical 팀장만.
- **메인 에이전트 단일 브로커:** Gemini CLI는 서브에이전트 간 직접 통신 API(`SendMessage`/`TeamCreate`) 부재. 모든 협업은 메인이 `_workspace/findings.md`·`tasks.md`·`checkpoint.json`·`task_*.json`으로 중개.
- **3요소 구성:** `.gemini/agents/` + `.gemini/skills/` + `GEMINI.md`. 슬래시 커맨드(`.gemini/commands/`)는 만들지 않음.
- **Plan Mode 필수:** 신규 구축·확장 시 `enter_plan_mode` 강제 (yolo 모드 제외).
- **Zero-Tolerance Failure Protocol:** 임의 Skip 절대 금지. 최대 2회 재시도(총 3회) → 미해결 시 `Blocked` + `ask_user`.

## 디렉토리 구조

```
harness/
└── skills/
    └── gemini-harness/
        ├── SKILL.md                              # 메인 스킬 정의
        └── references/
            ├── usage-examples.md                 # 🚀 트리거 발화 8종 + 모드 매핑
            ├── agent-design-patterns.md          # 7대 패턴 + 도구 매핑
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
            │   ├── models.md                     # ⚠️ 모델 ID 정본 — 여기만 갱신
            │   ├── agent-worker.template.md      # 워커 에이전트 생성 기준
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

슬래시 커맨드로 직접 호출:

```
/gemini-harness 하네스 구축해줘
/gemini-harness SSO 인증 프로젝트를 위한 harness 구축해줘
```

또는 자연어 발화만으로도 자동 트리거:

| 발화 패턴 | 모드 |
|-----------|------|
| "하네스 구성/구축/설계해줘", "{도메인} 자동화 만들어줘" | 신규 구축 |
| "기존 하네스에 {기능} 추가해줘", "에이전트 추가" | 기존 확장 |
| "하네스 점검/감사/현황", "drift 동기화" | 운영/유지보수 |
| "이전 결과 재실행/수정/보완" | 운영 (부분 재실행) |

> 새 도메인을 받으면 가장 먼저 `references/usage-examples.md`의 시나리오 8종(SSO·마이그레이션·콘텐츠루프·병렬리서치·장애분석·풀스택·확장·부분재실행)과 매칭. 비트리거 발화 표도 함께 제공되어 false-positive 방지.

## 워크플로우 Phase

| Phase | 설명 |
|-------|------|
| Phase 0 | 현황 감사 및 모드 분기 (신규/확장/운영) |
| Phase 1 | 도메인 분석 및 패턴 매칭 (usage-examples.md 시나리오 매칭) |
| Phase 2 | 가상 팀 설계 + 도구 권한 매핑 + 아키텍처 패턴 선택 |
| Phase 3 | 서브에이전트 정의 생성 (`.gemini/agents/{name}.md`) |
| Phase 4 | 절차 스킬 생성 (`.gemini/skills/{name}/SKILL.md`) |
| Phase 5 | 통합 및 오케스트레이션 (workflow.md·findings.md·tasks.md·checkpoint.json 초기화) |
| Phase 6 | 검증 및 테스트 (트리거 검증, Resume, Zero-Tolerance, GEMINI.md 등록) |

> 확장·운영 모드는 `expansion-matrix.md` / `evolution-protocol.md`로 Phase 일부만 선택 실행.

## 생성 산출물

```
{프로젝트}/
├── .gemini/
│   ├── agents/{name}.md                # 에이전트 정의 (role, tools, temperature)
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
└── GEMINI.md                           # 하네스 포인터 + 변경 이력
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

- `skills/gemini-harness/SKILL.md` — 메인 스킬 정의 + 워크플로우 + 참고 인덱스
- `references/usage-examples.md` — 🚀 트리거 발화 8종 + 모드 매핑 + 비트리거 발화 + Phase 적용 매트릭스
- `references/agent-design-patterns.md` — 7대 패턴 상세, 에이전트 정의 구조, 도구 매핑
- `references/orchestrator-template.md` — 오케스트레이터 Step 0~5 의사코드, checkpoint.json 스키마
- `references/orchestrator-procedures.md` — 에러 핸들링 결정트리, blocked_protocol, handle_handoff
- `references/team-examples.md` — 패턴별 실전 사례 인덱스
- `references/stage-step-guide.md` — workflow.md 명세, Stage·Step 전환 프로토콜
- `references/skill-writing-guide.md` — 스킬 작성 패턴, 데이터 스키마 표준, 평면 Step → Stage-Step 마이그레이션
- `references/skill-testing-guide.md` — 트리거 검증, Resume 테스트, Zero-Tolerance 검증
- `references/qa-agent-guide.md` — QA 에이전트 통합 정합성 검증
- `references/evolution-protocol.md` — 하네스 진화, 운영/유지보수 워크플로우
- `references/expansion-matrix.md` — 기존 확장 Phase 선택 매트릭스
- `references/schemas/models.md` — ⚠️ 모델 ID 정본 (`gemini models list`로 확인 후 갱신)
- `references/schemas/agent-worker.template.md` · `agent-orchestrator.template.md` — 에이전트 생성 기준 템플릿
- `references/schemas/` — 런타임 스키마 SoT (task·checkpoint·workflow·findings·tasks 템플릿)
- `references/examples/full-bundle/sso-style.md` — 전체 산출물 패키지 정본 예시
- `references/examples/team/` · `references/examples/step/` — 패턴별·구조별 상세 예제
