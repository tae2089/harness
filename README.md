# Harness — Coding Agent의 서브에이전트 오케스트레이션 메타 프레임워크

Coding Agent에서 전문 서브에이전트 팀과 협업 스킬을 설계하는 메타 프레임워크입니다.

## 개요

Harness는 도메인/프로젝트에 맞는 에이전트 팀을 구성하고, 각 에이전트의 역할·도구 권한을 정의하며, 공통 절차 스킬과 오케스트레이터를 생성하는 메타 스킬입니다.

## 핵심 원칙

- **6대 아키텍처 패턴:** Pipeline, Fan-out/Fan-in, Expert Pool, Producer-Reviewer, Supervisor, Hierarchical
- **엄격한 도구 권한 제어:** `tools: ["*"]` 금지, 역할에 맞는 도구만 할당
- **모든 에이전트 필수 도구:** `ask_user`, `activate_skill`
- **메인 에이전트 단일 브로커:** `_workspace/findings.md`, `_workspace/tasks.md`로 중개
- **3요소 구성:** `.gemini/agents/` + `.gemini/skills/` + `GEMINI.md`

## 디렉토리 구조

```
harness/
└── skills/
    └── gemini-harness/
        ├── SKILL.md                        # 메인 스킬 정의
        └── references/
            ├── agent-design-patterns.md    # 6대 패턴 + 도구 매핑
            ├── orchestrator-template.md    # 오케스트레이터 고도화 템플릿
            ├── team-examples.md            # 실전 협업 사례 7개
            ├── skill-writing-guide.md      # 스킬 작성 가이드
            ├── skill-testing-guide.md      # 스킬 테스트/검증 가이드
            └── qa-agent-guide.md           # QA 에이전트 전문 가이드
```

## 사용 방법

Coding Agent에서 다음과 같은 요청 시 `gemini-harness` 스킬이 자동으로 트리거됩니다.

- "하네스 구성해줘"
- "하네스 구축/설계/엔지니어링"
- "하네스 점검", "하네스 감사", "에이전트/스킬 동기화"
- 새로운 도메인/프로젝트에 대한 자동화 체계 구축

## 워크플로우

| Phase   | 설명                                        |
| ------- | ------------------------------------------- |
| Phase 0 | 현황 감사 및 모드 분기 (신규/확장/유지보수) |
| Phase 1 | 도메인 분석 및 패턴 매칭                    |
| Phase 2 | 가상 팀 및 도구 설계                        |
| Phase 3 | 서브에이전트 정의 생성 (`.md`)              |
| Phase 4 | 스킬 생성                                   |
| Phase 5 | 통합 및 오케스트레이션                      |
| Phase 6 | 검증 및 테스트                              |
| Phase 7 | 하네스 진화                                 |

## 생성 산출물

하네스 구성 완료 시 생성되는 파일들:

```
{프로젝트}/
├── .gemini/
│   ├── agents/
│   │   └── {name}.md          # 에이전트 정의 (role, tools, temperature)
│   └── skills/
│       └── {name}/
│           ├── SKILL.md        # 절차 스킬
│           └── references/     # 참조 문서
├── _workspace/
│   ├── findings.md             # 데이터 브로커 (에이전트 간 통찰 공유)
│   └── tasks.md                # 태스크 보드
└── GEMINI.md                   # 하네스 포인터 + 변경 이력
```

## 아키텍처 패턴

| 패턴              | 적합한 경우                            |
| ----------------- | -------------------------------------- |
| Pipeline          | 설계 → 구현 → 검증 등 순차 의존 작업   |
| Fan-out/Fan-in    | 병렬 독립 작업 후 통합                 |
| Expert Pool       | 상황별 선택 호출                       |
| Producer-Reviewer | 생성 후 품질 검수 루프                 |
| Supervisor        | 메인이 상태를 보며 동적 분배           |
| Hierarchical      | 팀장 에이전트의 재귀 위임 (2단계 이내) |

## 참고 문서

- `references/agent-design-patterns.md` — 6대 패턴, 에이전트 정의 구조, 도구 매핑
- `references/orchestrator-template.md` — 오케스트레이터 Phase 0~5, 에러 핸들링
- `references/team-examples.md` — 완성형 에이전트 파일 포함 7개 사례
- `references/skill-writing-guide.md` — 작성 패턴, 데이터 스키마 표준
- `references/skill-testing-guide.md` — 테스트/평가/트리거 검증
- `references/qa-agent-guide.md` — 통합 정합성 검증, 경계면 버그 패턴
