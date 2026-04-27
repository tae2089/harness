# `_workspace/_schemas/` Source-of-Truth (Codex CLI 버전)

Runtime schema definitions (single source of truth). At runtime, orchestrator Step 1 reads each file and writes to `_workspace/_schemas/` via shell commands or `apply_patch`.

## Files

| File                             | Type                           | 용도                                                     |
| -------------------------------- | ------------------------------ | -------------------------------------------------------- |
| `task.schema.json`               | JSON Schema (Draft 7)          | `_workspace/tasks/task_{agent}_{id}.json` 워커 보고 검증 |
| `checkpoint.schema.json`         | JSON Schema (Draft 7)          | `_workspace/checkpoint.json` 상태 검증                   |
| `findings.template.md`           | Markdown skeleton              | `_workspace/findings.md` 데이터 브로커 초기화            |
| `tasks.template.md`              | Markdown table skeleton        | `_workspace/tasks.md` 태스크 보드 초기화                 |
| `workflow.template.md`           | Markdown block skeleton        | `_workspace/workflow.md` Stage-Step 선언 기준            |
| `models.md`                      | 모델 ID 레지스트리 (SoT)       | 에이전트 생성 시 OpenAI 모델 ID 정본                     |
| `agent-worker.template.toml`         | 에이전트 TOML 템플릿           | 워커 에이전트 `.codex/agents/{name}.toml` 생성 기준      |
| `agent-orchestrator.template.md`     | 오케스트레이터 SKILL.md 템플릿 | 오케스트레이터 스킬 생성 기준                            |
| `agent-state-manager.template.toml`  | 상태관리 에이전트 TOML 템플릿  | State Manager `.codex/agents/state-manager.toml` 생성 기준 (선택적) |

> `README.md`만 워크스페이스에 복사하지 않는다. 나머지 9개 파일은 Step 1 init에서 `_workspace/_schemas/`로 동기화.

## Lifecycle

1. **Skill init time:** 메인테이너가 `references/schemas/`에서 파일 편집 (SoT). 모델 ID 변경 시 `models.md` + `agent-worker.template.toml`의 `model` 필드 갱신.
2. **Step 1 of orchestrator (runtime):** shell 또는 `apply_patch`로 9개 파일을 `_workspace/_schemas/`에 동기화.
3. **Agent creation (Phase 3):** main이 `_workspace/_schemas/agent-worker.template.toml` 읽어 변수 치환 후 `.codex/agents/{name}.toml`로 작성.
4. **Worker write time:** worker reads `_workspace/_schemas/task.schema.json` before producing `task_*.json`.
5. **Main validation time:** main reads `_schemas/*.schema.json` and validates `task_*.json` / `checkpoint.json`.

## Why duplicate into `_workspace/`?

- **Self-contained workspace:** Resume / handoff / forensic review only needs `_workspace/`.
- **Drift detection:** snapshots the schema version active at init.
- **Worker isolation:** workers access `_workspace/` only.
