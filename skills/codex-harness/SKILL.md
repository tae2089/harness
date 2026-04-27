---
name: codex-harness
description: "Codex CLI 환경에서 전문 서브에이전트 팀을 설계하는 메타 스킬. 도메인 분석 → 에이전트 TOML 정의(.codex/agents/) → 스킬 생성(.codex/skills/) → AGENTS.md 초기화. 트리거: '코덱스 하네스 구성해줘', 'codex 에이전트 팀 만들어줘', 'codex harness 구축', '{도메인} codex 자동화'. 후속 작업(수정/보완/재실행/확장) 시에도 반드시 이 스킬 사용."
---

# Skill: Codex Harness Orchestrator

> **시작 전 필수:** `references/usage-examples.md` 시나리오와 발화 매칭 확인.

## 핵심 원칙

1. **7대 아키텍처 패턴:** Pipeline · Fan-out/Fan-in · Expert Pool · Producer-Reviewer · Supervisor · Hierarchical · Handoff
2. **에이전트 정의:** TOML 포맷 — `.codex/agents/{name}.toml` (Gemini의 `.gemini/agents/*.md` 대응)
3. **스킬 포맷:** SKILL.md — `.codex/skills/{name}/SKILL.md` (동일)
4. **프로젝트 컨텍스트:** `AGENTS.md` (Gemini의 `GEMINI.md` 대응)
5. **상태 영속성:** `_workspace/` 파일 기반 브로커링 (Gemini harness와 동일)
6. **권한 제어:** TOML `sandbox_mode` 필드 — `read-only | workspace-write | danger-full-access`
7. **서브에이전트 제약:** 오케스트레이터만 서브에이전트 스폰. `max_depth=1`(기본값) 강제.
8. **파일 I/O:** `apply_patch` 우선 (외과적 수정). 신규 파일은 shell write.
9. **Zero-Tolerance Failure Protocol:** 임의 Skip 절대 금지. 최대 2회 재시도(총 3회) → `Blocked`.

## 워크플로우

### Phase 0: 현황 감사 (모드 분기)

`.codex/agents/`, `.codex/skills/`, `AGENTS.md`, `_workspace/checkpoint.json` 존재 여부 확인:

| 상태 | 모드 | 진입 Phase |
|------|------|-----------|
| 전부 미존재 | 신규 구축 | Phase 1 |
| 일부 존재 | 기존 확장 | Phase 1 (expansion-matrix.md 참조) |
| checkpoint.json `in_progress` | Resume | Phase 5 재개 |
| checkpoint.json `blocked` | 운영/수정 | 차단 해소 후 Phase 5 재개 |

### Phase 1: 도메인 분석 + 패턴 매칭

1. 사용자 요청 분석 → 도메인·목표·제약 추출.
2. `references/usage-examples.md` 시나리오 매칭 → 패턴·Stage/Step 구조 도출.
3. 비트리거 발화 확인 — false-positive 방지.

### Phase 2: 가상 팀 설계

1. 에이전트 역할 분리 (단일 책임 원칙).
2. 패턴 선택 (`references/agent-design-patterns.md` 참조).
3. 각 에이전트 `sandbox_mode` 결정:

   | 역할 | sandbox_mode |
   |------|-------------|
   | Researcher / Analyst (읽기 전용) | `read-only` |
   | Developer / Writer (코드·파일 작성) | `workspace-write` |
   | Operator / Deployer (외부 실행 포함) | `danger-full-access` |

4. **서브에이전트 제약 확인:** 오케스트레이터 아닌 에이전트는 subagent spawn 금지.

### Phase 3: 에이전트 TOML 생성

`.codex/agents/{name}.toml` 생성. 기준: `references/schemas/agent-worker.template.toml`.

필수 필드: `name`, `description`, `developer_instructions`, `model`, `sandbox_mode`.

> **모델 ID SoT:** `references/schemas/models.md` — 임의 추측 금지.

### Phase 4: 절차 스킬 생성

`.codex/skills/{orchestrator-name}/SKILL.md` 작성. 기준: `references/schemas/agent-orchestrator.template.md`.

Schema 번들 동봉: `references/schemas/` 8종 → `.codex/skills/{name}/references/schemas/` 복사.

### Phase 5: 통합 및 오케스트레이션

1. `_workspace/`, `_workspace/{plan_name}/`, `_workspace/tasks/`, `_workspace/_schemas/` 생성.
2. Schema 동기화: `references/schemas/` 8종 → `_workspace/_schemas/`.
3. `workflow.md` 작성 — Stage-Step 구조, 6 필수 필드, 검증 가능 종료 조건.
4. `findings.md` 초기화 (패턴별 섹션).
5. `tasks.md` 초기화.
6. `checkpoint.json` 생성 (status: `in_progress`).
7. **AGENTS.md 갱신** — 하네스 포인터 추가:

   ```markdown
   ## Harness: {plan_name}
   - 에이전트: {에이전트 목록 + .codex/agents/ 경로}
   - 스킬: {스킬 목록 + .codex/skills/ 경로}
   - 워크플로우: _workspace/workflow.md
   - 체크포인트: _workspace/checkpoint.json
   ```

### Phase 6: 검증

- [ ] `.codex/agents/*.toml` 필수 필드 완전 (name, description, developer_instructions, model, sandbox_mode)
- [ ] `.codex/skills/*/SKILL.md` frontmatter name·description 검증
- [ ] workflow.md 스키마 검증 (6 필수 필드 + 검증 가능 종료 조건, 자연어 금지)
- [ ] workflow.md 사이클 검증
- [ ] `_workspace/_schemas/` 8종 파일 존재
- [ ] `AGENTS.md` 하네스 섹션 추가 확인
- [ ] `checkpoint.json` status `in_progress`

## 패턴별 Codex 조율 방식

Gemini `invoke_agent` 대신 Codex subagent spawn. 기본 병렬 실행 — 순차는 스킬 지시로 단계 분리:

| 패턴 | Codex 조율 방식 |
|------|---------------|
| `pipeline` | 단계별 sequential spawn — 이전 단계 `task_*.json` status=done 확인 후 다음 |
| `fan_out_fan_in` | 병렬 spawn → 전체 완료 후 ATOMIC aggregation |
| `producer_reviewer` | producer spawn → task 확인 → reviewer spawn → verdict 확인 |
| `expert_pool` | Codex description 기반 자동 라우팅 |
| `supervisor` | tasks.md claim 기반 동적 spawn |
| `hierarchical` | 팀장 spawn → 팀장이 워커 spawn (`max_depth=2` 필요: `.codex/config.toml`) |
| `handoff` | `[NEXT_AGENT:name]` 파싱 → 순차 spawn |

## 생성 산출물

```
{프로젝트}/
├── .codex/
│   ├── agents/{name}.toml              # 에이전트 정의 (TOML)
│   └── skills/{orchestrator}/
│       ├── SKILL.md
│       └── references/schemas/         # 스키마 사본 (8종)
├── _workspace/
│   ├── _schemas/
│   ├── workflow.md
│   ├── findings.md
│   ├── tasks.md
│   ├── checkpoint.json
│   └── tasks/task_{agent}_{id}.json
└── AGENTS.md                           # 하네스 포인터 + 프로젝트 컨텍스트
```

## 에러 핸들링

Zero-Tolerance: 에이전트 실패 → 최대 2회 재시도 → 미해결 시 task_*.json status=blocked + HALT.

## 참고 문서

- `references/usage-examples.md` — 🚀 트리거 발화 시나리오 + 모드 매핑
- `references/agent-design-patterns.md` — 7대 패턴 + Codex sandbox 권한 매핑
- `references/orchestrator-template.md` — Step 0~5 의사코드 (Codex 버전)
- `references/codex-vs-gemini.md` — Gemini↔Codex 대응표 + 마이그레이션 가이드
- `references/schemas/models.md` — ⚠️ 모델 ID 정본 (OpenAI)
- `references/schemas/agent-worker.template.toml` — 워커 에이전트 TOML 기준
- `references/schemas/` — 런타임 스키마 SoT (8종)
