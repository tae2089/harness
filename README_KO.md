<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Codex_CLI-Skill-5C5C5C.svg" alt="Codex CLI Skill">
  <img src="https://img.shields.io/badge/Gemini_CLI-Skill-4285F4.svg" alt="Gemini CLI Skill">
  <img src="https://img.shields.io/badge/Patterns-7_Architectures-orange.svg" alt="7 Architecture Patterns">
  <a href="https://github.com/tae2089/harness/stargazers"><img src="https://img.shields.io/github/stars/tae2089/harness?style=social" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/README-EN%20%7C%20KO%20%7C%20JA-lightgrey" alt="i18n"></a>
</p>

# Harness — 서브에이전트 오케스트레이션 메타 프레임워크

[English](README.md) | **한국어** | [日本語](README_JA.md)

AI 코딩 에이전트에서 전문 서브에이전트 팀을 설계하는 메타 프레임워크. 도메인 설명 하나로 에이전트 정의, 오케스트레이터 스킬, 런타임 스캐폴딩 전체를 생성한다.

## 제공 스킬

| 스킬 | CLI | 에이전트 정의 | 스킬 경로 |
|------|-----|-------------|---------|
| `codex-harness` | OpenAI Codex CLI | `.codex/agents/{name}.toml` | `.codex/skills/` |
| `gemini-harness` | Google Gemini CLI | `.gemini/agents/{name}.md` | `.gemini/skills/` |

---

## codex-harness (OpenAI Codex CLI)

### 설치 방법

**개인용 (글로벌):**
```bash
git clone https://github.com/tae2089/harness.git
cp -r harness/skills/codex-harness ~/.codex/skills/
```

**팀용 (레포 내):**
```bash
cp -r harness/skills/codex-harness .codex/skills/
```

설치 후 Codex CLI 세션에서 `"codex 하네스 구성해줘"` 발화 → `codex-harness` 스킬 자동 트리거 확인.

> **처음이라면 →** [`references/usage-examples.md`](skills/codex-harness/references/usage-examples.md) 먼저 확인. 8가지 도메인 시나리오와 발화 패턴 매핑, 비트리거 발화 표 제공.

### 핵심 원칙 (Codex CLI)

- **sandbox_mode 권한 제어:** 모든 에이전트에 명시적 `sandbox_mode` 필수: `read-only`(Analyst/Architect) · `workspace-write`(Coder/Reviewer/QA) · `danger-full-access`(Operator/Deployer). 와일드카드 권한 금지.
- **Plan Mode 필수:** 신규 구축·확장 시 `/plan` 또는 `Shift+Tab` 활성화.
- **메인 에이전트 단일 브로커:** 서브에이전트 간 직접 통신 API 부재. 모든 협업은 `_workspace/`로 중개.
- **3요소 구성:** `.codex/agents/*.toml` + `.codex/skills/*/SKILL.md` + `AGENTS.md`.

### 사용 방법

```
/plan
SSO 인증 프로젝트를 위한 codex 하네스 구성해줘
```

### 생성 산출물

```
{프로젝트}/
├── .codex/
│   ├── agents/{name}.toml              # 에이전트 정의 (TOML: 역할, sandbox_mode, 모델)
│   └── skills/{orchestrator}/
│       ├── SKILL.md
│       └── references/schemas/
├── _workspace/
│   ├── workflow.md
│   ├── findings.md
│   ├── tasks.md
│   ├── checkpoint.json
│   └── tasks/task_{agent}_{id}.json
└── AGENTS.md
```

---

## gemini-harness (Google Gemini CLI)

### 설치 방법

```bash
gemini skills install https://github.com/tae2089/harness.git --path skills
```

설치 후 Gemini CLI 세션에서 `"하네스 구성해줘"` 발화 → `gemini-harness` 스킬 자동 트리거 확인.

> **처음이라면 →** [`references/usage-examples.md`](skills/gemini-harness/references/usage-examples.md) 먼저 확인. 8가지 도메인 시나리오와 발화 패턴 매핑, 비트리거 발화 표 제공.

### 핵심 원칙 (Gemini CLI)

- **엄격한 툴 권한 제어:** `tools: ["*"]` 금지. 모든 에이전트에 `ask_user`·`activate_skill` 필수. `invoke_agent`는 오케스트레이터/Supervisor 전용.
- **Plan Mode 필수:** 신규 구축·확장 시 `enter_plan_mode` 강제 (yolo 모드 제외).
- **메인 에이전트 단일 브로커:** `SendMessage`/`TeamCreate` API 부재. 모든 협업은 `_workspace/`로 중개.
- **3요소 구성:** `.gemini/agents/` + `.gemini/skills/` + `GEMINI.md`.

### 사용 방법

```
/gemini-harness SSO 인증 프로젝트를 위한 하네스 구성해줘
```

또는 자연어 발화:

| 발화 패턴 | 모드 |
|-----------|------|
| "하네스 구성/구축/설계해줘", "{도메인} 자동화 만들어줘" | 신규 구축 |
| "기존 하네스에 {기능} 추가해줘", "에이전트 추가" | 기존 확장 |
| "하네스 점검/감사/현황", "drift 동기화" | 운영/유지보수 |
| "이전 결과 재실행/수정/보완" | 운영 (부분 재실행) |

### 생성 산출물

```
{프로젝트}/
├── .gemini/
│   ├── agents/{name}.md                # 에이전트 정의 (역할, tools, temperature)
│   └── skills/{orchestrator}/
│       ├── SKILL.md
│       └── references/schemas/
├── _workspace/
│   ├── workflow.md
│   ├── findings.md
│   ├── tasks.md
│   ├── checkpoint.json
│   └── tasks/task_{agent}_{id}.json
└── GEMINI.md
```

---

## 공통: 핵심 개념

### 워크플로우 Phase

| Phase | 설명 |
|-------|------|
| Phase 0 | 현황 감사 및 모드 분기 (신규/확장/운영) |
| Phase 1 | 도메인 분석 및 패턴 매칭 (usage-examples.md 시나리오 매칭) |
| Phase 2 | 가상 팀 설계 + 권한 매핑 + 아키텍처 패턴 선택 |
| Phase 3 | 에이전트 정의 생성 |
| Phase 4 | 오케스트레이터 스킬 생성 |
| Phase 5 | 통합 및 오케스트레이션 (workflow.md·findings.md·tasks.md·checkpoint.json 초기화) |
| Phase 6 | 검증 (트리거 검증, Resume, Zero-Tolerance, 프로젝트 매니페스트 등록) |

### 7대 패턴 선택 가이드

| 패턴 | 적합한 경우 |
|------|------------|
| Pipeline | 설계 → 구현 → 검증 등 순차 의존 작업 |
| Fan-out/Fan-in | 병렬 독립 작업 후 통합 |
| Expert Pool | 상황별 전문가 선택 호출 |
| Producer-Reviewer | 생성 후 품질 검수 루프 (PASS/FIX/REDO) |
| Supervisor | tasks.md claim 기반 동적 배치 |
| Hierarchical | 팀장 → 워커 2단계 위임 (이질적 도메인) |
| Handoff | 분석 결과에 따라 다음 전문가 동적 라우팅 |

### 명명 컨벤션

Stage·Step 이름은 deliverable 명사구 kebab-case (`^[a-z][a-z0-9-]*$`). `main`·`step1`·`task` 같은 placeholder는 workflow.md 스키마 검증에서 차단.

### Zero-Tolerance Failure Protocol

임의 Skip 절대 금지. 최대 2회 재시도(총 3회) → 미해결 시 `Blocked` + 사용자 확인 요청.

---

## 디렉토리 구조

```
harness/
└── skills/
    ├── codex-harness/
    │   ├── SKILL.md
    │   └── references/
    │       ├── usage-examples.md
    │       ├── agent-design-patterns.md
    │       ├── orchestrator-template.md
    │       ├── orchestrator-procedures.md
    │       ├── team-examples.md
    │       ├── stage-step-guide.md
    │       ├── skill-writing-guide.md
    │       ├── skill-testing-guide.md
    │       ├── qa-agent-guide.md
    │       ├── evolution-protocol.md
    │       ├── expansion-matrix.md
    │       ├── schemas/
    │       │   ├── models.md                     # ⚠️ 모델 ID 정본
    │       │   ├── agent-worker.template.toml
    │       │   ├── agent-state-manager.template.toml
    │       │   ├── agent-orchestrator.template.md
    │       │   ├── task.schema.json
    │       │   ├── checkpoint.schema.json
    │       │   ├── workflow.template.md
    │       │   ├── findings.template.md
    │       │   ├── tasks.template.md
    │       │   └── README.md
    │       └── examples/
    │           ├── full-bundle/sso-style.md
    │           ├── team/01~05-*.md
    │           └── step/01~05-*.md
    └── gemini-harness/
        ├── SKILL.md
        └── references/                           # codex-harness와 동일 구조
```

## 참고 문서

### codex-harness
- `skills/codex-harness/SKILL.md` — 메인 스킬 정의 + 워크플로우 + 참고 인덱스
- `references/schemas/models.md` — ⚠️ 모델 ID 정본 + `model_reasoning_effort` 선택 가이드
- `references/schemas/agent-worker.template.toml` · `agent-orchestrator.template.md` — 에이전트 생성 기준 템플릿

### gemini-harness
- `skills/gemini-harness/SKILL.md` — 메인 스킬 정의 + 워크플로우 + 참고 인덱스
- `references/schemas/models.md` — ⚠️ 모델 ID 정본
- `references/schemas/agent-worker.template.md` · `agent-orchestrator.template.md` — 에이전트 생성 기준 템플릿

### 공통 참고
- `references/usage-examples.md` — 🚀 트리거 발화 8종 + 모드 매핑 + 비트리거 발화 + Phase 적용 매트릭스
- `references/agent-design-patterns.md` — 7대 패턴 상세, 에이전트 정의 구조, 권한 매핑
- `references/orchestrator-template.md` — 오케스트레이터 Step 0~5 의사코드, checkpoint.json 스키마
- `references/orchestrator-procedures.md` — 에러 핸들링 결정트리, blocked_protocol, handle_handoff
- `references/team-examples.md` — 패턴별 실전 사례 인덱스
- `references/stage-step-guide.md` — workflow.md 명세, Stage·Step 전환 프로토콜
- `references/skill-writing-guide.md` — 스킬 작성 패턴, 데이터 스키마 표준
- `references/skill-testing-guide.md` — 트리거 검증, Resume 테스트, Zero-Tolerance 검증
- `references/qa-agent-guide.md` — QA 에이전트 통합 정합성 검증
- `references/evolution-protocol.md` — 하네스 진화, 운영/유지보수 워크플로우
- `references/expansion-matrix.md` — 기존 확장 Phase 선택 매트릭스
- `references/examples/full-bundle/sso-style.md` — 전체 산출물 패키지 정본 예시
- `references/examples/team/` · `references/examples/step/` — 패턴별·구조별 상세 예제
