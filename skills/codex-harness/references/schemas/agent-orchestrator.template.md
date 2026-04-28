<!--
ORCHESTRATOR AGENT TEMPLATE — After variable substitution, save as `.agents/skills/{harness-name}/SKILL.md`.
The orchestrator is generated as a skill SKILL.md, not as an agent .md file.
Model ID SoT: references/schemas/models.md (always check models.md first before making changes)

Substitution variables:
  {{SKILL_NAME}}        kebab-case skill name (e.g. sso-dev-flow)
  {{DESCRIPTION}}       pushy description + trigger keywords + follow-up action keywords
  {{PLAN_NAME}}         subdirectory name under _workspace (e.g. sso)
  {{AGENT_TABLE}}       virtual team table rows (repeated)
  {{STAGE_STEP_SUMMARY}} workflow.md Stage/Step structure summary

Only the orchestrator can spawn subagents — worker agents are prohibited from doing so.
Model uses the thinking tier (responsible for complex reasoning and multi-step coordination).
-->

---

name: {{SKILL_NAME}}
description: "{{DESCRIPTION}}. Always use this skill for follow-up work (modifications/enhancements/re-runs)."

---

# Skill: {{SKILL_NAME}} Orchestrator

## Virtual Team

| Agent           | Type                   | Role   | Skill   | Output |
| --------------- | ---------------------- | ------ | ------- | ------ |
| {{AGENT_TABLE}} |

> Orchestrator model: `gpt-5.5` (responsible for design and reasoning). Verify model ID in: `references/schemas/models.md`

## Workflow

### Step 0: Context Check (Durable Execution)

Apply `references/orchestrator-template.md` Step 0 procedure. Branch based on `_workspace/checkpoint.json` status:

- `in_progress` → Resume (continue from current stage/step)
- `completed` → Confirm with user: partial re-run or fresh run
- Not present → Fresh run (proceed to Step 1)

### Step 1: Initialization

1. Create directories: `_workspace/{{PLAN_NAME}}/`, `_workspace/tasks/`, `_workspace/_schemas/`.
2. **Schema synchronization** — Copy 5 schema files + 3 agent templates from `references/schemas/` to `_workspace/_schemas/` via shell `cat` → `apply_patch` (see `references/orchestrator-template.md` Step 1.3).
3. Write `workflow.md` (variable substitution from `_workspace/_schemas/workflow.template.md`):
   {{STAGE_STEP_SUMMARY}}
4. Initialize `findings.md` (based on `_workspace/_schemas/findings.template.md`).
5. Initialize `tasks.md` (based on `_workspace/_schemas/tasks.template.md`).
6. Create `checkpoint.json` (must conform to `_workspace/_schemas/checkpoint.schema.json` schema):
   ```json
   {
     "plan_name": "{{PLAN_NAME}}",
     "status": "in_progress",
     "current_stage": "{first Stage name}",
     "current_step": "{first Step name}",
     "active_pattern": "{first Step pattern}"
   }
   ```
7. **workflow.md schema validation** — 6 required fields + naming convention (no placeholders) + verifiable exit conditions + pattern enum. Violations cause HALT (see `references/orchestrator-template.md` Step 1.8).
8. **workflow.md cycle validation** (after passing schema validation).

### Step 2: Step Execution Loop

Apply `references/orchestrator-template.md` Step 2 standard procedure. Invoke agents per pattern, check exit conditions, handle Stage gates, update checkpoint.json.

## Error Handling

Zero-Tolerance: agent failure → up to 2 retries (3 total) → if unresolved, set `task_*.json` status=blocked and request user confirmation. Arbitrary skipping is strictly prohibited.
