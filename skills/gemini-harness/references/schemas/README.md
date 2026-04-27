# `_workspace/_schemas/` Source-of-Truth

Real schema definitions (single source of truth). At runtime, orchestrator Step 1.3 reads each file here via `read_file` and emits it via `write_file` to `_workspace/_schemas/` — **shell `cp` cannot be used** because the runtime working directory (user project root) cannot reach the skill's reference path through a shell command. Agent tools (`read_file` / `write_file`) resolve skill reference paths automatically.

## Files

| File | Type | Validates |
|------|------|-----------|
| `task.schema.json` | JSON Schema (Draft 7) | `_workspace/tasks/task_{agent}_{id}.json` worker reports |
| `checkpoint.schema.json` | JSON Schema (Draft 7) | `_workspace/checkpoint.json` durable state |
| `findings.template.md` | Markdown skeleton with section markers | `_workspace/findings.md` data broker file |
| `tasks.template.md` | Markdown table skeleton | `_workspace/tasks.md` task board (main aggregates) |
| `workflow.template.md` | Markdown block skeleton with field rules | `_workspace/workflow.md` Stage-Step structure |

## Lifecycle

1. **Skill init time:** maintainer edits files in `references/schemas/` (SoT). Single point of update — no duplicate to mirror.
2. **Step 1.3 of orchestrator (runtime):** main agent issues 5 `read_file` calls (one per schema file in this dir except `README.md`) and 5 matching `write_file` calls into `_workspace/_schemas/`. Same step also writes `workflow.md`, `findings.md`, `tasks.md`, `checkpoint.json` (all derived from the templates just copied).
3. **Worker write time:** worker reads `_workspace/_schemas/task.schema.json` before producing its own `task_*.json` — formats fields per schema.
4. **Main validation time:** main reads `_schemas/*.schema.json` and validates `task_*.json` / `checkpoint.json` on every read (cheap structural check).

## Why duplicate into `_workspace/`?

- **Self-contained workspace:** Resume / handoff / forensic review only needs `_workspace/`, no skill lookup.
- **Drift detection:** if skill schemas evolve mid-run, `_workspace/_schemas/` snapshots the version active at init — prevents validation breaks.
- **Worker isolation:** workers do not have `read_file` access to skill internals; they have `_workspace/` access.

## Update protocol

1. Edit file in `references/schemas/`.
2. Bump skill version (or note in expansion-matrix drift table).
3. New runs auto-pick up via Step 1 copy.
4. Existing runs keep old `_workspace/_schemas/` until manual refresh or new init.
