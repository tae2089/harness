# `_workspace/_schemas/` Source-of-Truth

Real schema definitions (single source of truth). At runtime, orchestrator Step 1.3 reads each file here via `read_file` and emits it via `write_file` to `_workspace/_schemas/` — **shell `cp` cannot be used** because the runtime working directory (user project root) cannot reach the skill's reference path through a shell command. Agent tools (`read_file` / `write_file`) resolve skill reference paths automatically.

## Files

| File | Type | 용도 |
|------|------|------|
| `task.schema.json` | JSON Schema (Draft 7) | `_workspace/tasks/task_{agent}_{id}.json` 워커 보고 검증 |
| `checkpoint.schema.json` | JSON Schema (Draft 7) | `_workspace/checkpoint.json` 상태 검증 |
| `findings.template.md` | Markdown skeleton | `_workspace/findings.md` 데이터 브로커 초기화 |
| `tasks.template.md` | Markdown table skeleton | `_workspace/tasks.md` 태스크 보드 초기화 |
| `workflow.template.md` | Markdown block skeleton | `_workspace/workflow.md` Stage-Step 선언 기준 |
| `models.md` | 모델 ID 레지스트리 (SoT) | 에이전트 생성 시 모델 ID 정본 — 여기만 갱신하면 반영 |
| `agent-worker.template.md` | 에이전트 정의 템플릿 | 워커 에이전트 `.gemini/agents/{name}.md` 생성 기준 |
| `agent-orchestrator.template.md` | 오케스트레이터 템플릿 | 오케스트레이터 스킬 `SKILL.md` 생성 기준 |
| `agent-state-manager.template.md` | 상태 관리 에이전트 템플릿 | CRUD 전담 `@state-manager` 에이전트 생성 기준 (flash 모델) |

> `README.md`만 워크스페이스에 복사하지 않는다. 나머지 파일은 Step 1.3에서 전부 `_workspace/_schemas/`로 동기화.

## Lifecycle

1. **Skill init time:** 메인테이너가 `references/schemas/`에서 파일 편집 (SoT). 모델 ID 변경 시 `models.md` + 에이전트 템플릿 2종의 `model:` 필드 갱신.
2. **Step 1.3 of orchestrator (runtime):** main이 9개 파일 각각 `read_file` → `write_file`으로 `_workspace/_schemas/`에 동기화. `workflow.md`, `findings.md`, `tasks.md`, `checkpoint.json`도 템플릿 기반으로 작성.
3. **Agent creation (Phase 3):** main이 `_workspace/_schemas/agent-worker.template.md`(또는 orchestrator) 읽어 변수 치환 후 `.gemini/agents/{name}.md`로 작성. 모델 ID는 `_workspace/_schemas/models.md`에서 확인.
4. **Worker write time:** worker reads `_workspace/_schemas/task.schema.json` before producing its own `task_*.json` — formats fields per schema.
5. **Main validation time:** main reads `_schemas/*.schema.json` and validates `task_*.json` / `checkpoint.json` on every read (cheap structural check).

## Why duplicate into `_workspace/`?

- **Self-contained workspace:** Resume / handoff / forensic review only needs `_workspace/`, no skill lookup.
- **Drift detection:** if skill schemas evolve mid-run, `_workspace/_schemas/` snapshots the version active at init — prevents validation breaks.
- **Worker isolation:** workers do not have `read_file` access to skill internals; they have `_workspace/` access.

## Update protocol

1. Edit file in `references/schemas/`.
2. Bump skill version (or note in expansion-matrix drift table).
3. New runs auto-pick up via Step 1 copy.
4. Existing runs keep old `_workspace/_schemas/` until manual refresh or new init.
