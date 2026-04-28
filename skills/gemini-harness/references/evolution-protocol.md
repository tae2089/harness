# Harness Evolution Protocol

Detailed workflow for `SKILL.md` Step 7. A harness is not a static artifact built once and finished — it is a system that continuously evolves in response to user feedback. Load this file first when entering the "operations/maintenance" branch in Step 0, or when the user requests "harness inspection/audit/sync/extension".

---

## Table of Contents

1. [Post-execution Feedback Collection](#1-post-execution-feedback-collection)
2. [Feedback Incorporation Paths](#2-feedback-incorporation-paths)
3. [Change History Management](#3-change-history-management)
4. [Evolution Triggers](#4-evolution-triggers)
5. [Operations/Maintenance Workflow](#5-operationsmaintenance-workflow)

---

## 1. Post-execution Feedback Collection

After each harness execution completes, request feedback from the user.

- "Are there any parts of the results you'd like to improve?"
- "Are there any changes you'd like to make to the agent configuration or workflow?"

If there is no feedback, move on. Do not force it, but always provide the opportunity.

---

## 2. Feedback Incorporation Paths

The target for modification differs depending on the type of feedback.

| Feedback Type       | Modification Target              | Example                                                       |
| ------------------- | -------------------------------- | ------------------------------------------------------------- |
| Output quality      | Skill of the relevant agent      | "Analysis is too shallow" → add depth criteria to skill       |
| Agent role          | Agent definition `.md`           | "Security review is also needed" → add new agent              |
| Workflow order      | Orchestrator skill               | "Validation should come first" → change Step order            |
| Team composition    | Orchestrator + agents            | "These two could be merged" → merge agents                    |
| Missing trigger     | Skill description                | "Doesn't work with this phrasing" → expand description        |

---

## 3. Change History Management

All changes are recorded in the **change history** table in GEMINI.md (same as the history section of the GEMINI.md template in Step 5-4).

```markdown
**Change History:**
| Date | Change | Target | Reason |
|---|---|---|---|
| 2026-04-05 | Initial setup | Entire harness | - |
| 2026-04-07 | Added QA agent | agents/qa-inspector.md | Feedback on insufficient output quality validation |
| 2026-04-10 | Added tone guide | skills/content-creator | Feedback: "too stiff" |
```

---

## 4. Evolution Triggers

Evolution is proposed not only when the user explicitly says "modify the harness", but also in the following situations.

- When the same type of feedback repeats 2 or more times.
- When a repeated failure pattern by an agent is discovered.
- When the user is observed bypassing the orchestrator and working manually.

---

## 5. Operations/Maintenance Workflow

Systematically perform inspection, modification, and synchronization of an existing harness. Follow this workflow when entering the "operations/maintenance" branch in Step 0.

### Step 1: Status Audit

- Compare the file list in `.gemini/agents/` against the agent configuration in the orchestrator skill → generate discrepancy list.
- Compare the directory list in `.gemini/skills/` against the skill configuration in the orchestrator skill → generate discrepancy list.
- Report audit results to the user.

### Step 2: Incremental Addition/Modification

- Perform agent/skill additions, modifications, and deletions per the user's request.
- Classify the type of change and determine which Steps to execute: see `references/expansion-matrix.md` — `classify_change()`.
- Make changes one at a time; immediately run Step 3 after each change.

> **Runtime evolution safety:** If skill/agent files are modified while the harness is currently running (`status: "in_progress"` or `"partial"` in `_workspace/checkpoint.json`), the orchestrator will restore the execution position from `current_stage`·`current_step`·`active_pattern` in checkpoint.json on the next cycle re-entry. Therefore, **already-completed Steps are not re-run** — execution proceeds from the `current_step` restore point in checkpoint.json upon entering the next Step. Modified agent/skill files take effect from the point where the orchestrator next calls that agent via `invoke_agent`. However, if the modification affects the agent or exit condition of the currently running Step, suggest to the user to manually re-run that Step (rolling back `current_step` in `checkpoint.json`) or restart from the beginning.

### Step 3: Update GEMINI.md Change History

- Record date, change content, target, and reason in the change history table.

### Step 4: Change Validation

- Validate the structure of modified agents/skills (per Step 6-1 criteria).
- If the modification scope affects triggers, perform trigger validation (per Step 6-4 criteria).
- For large-scale changes (architecture changes, 3+ agents added/removed), also perform Step 6-3 (execution test) and 6-5 (dry run).
- Final confirmation that GEMINI.md matches the actual files.
