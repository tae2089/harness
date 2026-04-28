# `_workspace/_schemas/` Source-of-Truth

Real schema definitions (single source of truth). At runtime, orchestrator Step 1.3 reads each file here via `read_file` and emits it via `write_file` to `_workspace/_schemas/` — **shell `cp` cannot be used** because the runtime working directory (user project root) cannot reach the skill's reference path through a shell command. Agent tools (`read_file` / `write_file`) resolve skill reference paths automatically.

## Files

| File | Type | Purpose |
|------|------|---------|
| `task.schema.json` | JSON Schema (Draft 7) | Validates worker reports at `_workspace/tasks/task_{agent}_{id}.json` |
| `checkpoint.schema.json` | JSON Schema (Draft 7) | Validates state at `_workspace/checkpoint.json` |
| `findings.template.md` | Markdown skeleton | Initializes data broker at `_workspace/findings.md` |
| `tasks.template.md` | Markdown table skeleton | Initializes task board at `_workspace/tasks.md` |
| `workflow.template.md` | Markdown block skeleton | Stage-Step declaration reference for `_workspace/workflow.md` |
| `models.md` | Model ID registry (SoT) | Authoritative model IDs for agent creation — update only here to propagate |
| `agent-worker.template.md` | Agent definition template | Reference for generating worker agent `.gemini/agents/{name}.md` |
| `agent-orchestrator.template.md` | Orchestrator template | Reference for generating orchestrator skill `SKILL.md` |
| `agent-state-manager.template.md` | State manager agent template | Reference for generating CRUD-dedicated `@state-manager` agent (flash model) |

> `README.md` is the only file not copied to the workspace. All other files are synchronized to `_workspace/_schemas/` in Step 1.3.

## Lifecycle

1. **Skill init time:** Maintainer edits files in `references/schemas/` (SoT). When model IDs change, update the `model:` fields in `models.md` and both agent templates.
2. **Step 1.3 of orchestrator (runtime):** main synchronizes all 9 files to `_workspace/_schemas/` via `read_file` → `write_file`. Also writes `workflow.md`, `findings.md`, `tasks.md`, and `checkpoint.json` from templates.
3. **Agent creation (Phase 3):** main reads `_workspace/_schemas/agent-worker.template.md` (or orchestrator), substitutes variables, and writes to `.gemini/agents/{name}.md`. Model IDs are verified from `_workspace/_schemas/models.md`.
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
