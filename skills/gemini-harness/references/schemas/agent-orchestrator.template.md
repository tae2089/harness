<!--
ORCHESTRATOR AGENT TEMPLATE — After variable substitution, save as `.gemini/skills/{harness-name}/SKILL.md`.
The orchestrator is generated as a skill SKILL.md, not as an agent .md.
Model ID SoT: references/schemas/models.md (always check models.md first before making changes)

Substitution variables:
  {{SKILL_NAME}}        kebab-case skill name (e.g. sso-dev-flow)
  {{DESCRIPTION}}       Pushy description + trigger keywords + follow-up action keywords
  {{PLAN_NAME}}         Subdirectory name under _workspace (e.g. sso)
  {{AGENT_TABLE}}       Virtual team table rows (repeated)
  {{STAGE_STEP_SUMMARY}} Summary of workflow.md Stage/Step structure

The orchestrator holds invoke_agent permission — worker agents are prohibited from using it.
Uses the pro tier model (responsible for complex reasoning and multi-step coordination).
-->

---

name: {{SKILL_NAME}}
description: "{{DESCRIPTION}}. This skill must also be used for all follow-up actions (modifications, refinements, re-runs)."

---

# Skill: {{SKILL_NAME}} Orchestrator

## Virtual Team

| Agent           | Role | Output |
| --------------- | ---- | ------ |
| {{AGENT_TABLE}} |

> Orchestrator model: `gemini-3.1-pro-preview` (responsible for design and reasoning). Verify model ID at: `references/schemas/models.md`

## Workflow

### Step 0: Context Check (Durable Execution)

Apply the Step 0 procedure from `references/orchestrator-template.md`. Branch based on `_workspace/checkpoint.json` status:

- `in_progress` → Resume (resume from current stage/step)
- `completed` → Ask user whether to partially re-run or start a new execution
- Not found → New execution (proceed to Step 1)

### Step 1: Initialization

1. Create directories: `_workspace/{{PLAN_NAME}}/`, `_workspace/tasks/`, `_workspace/_schemas/`.
2. **Schema sync** — Copy 5 schema files + 3 agent templates from `references/schemas/` to `_workspace/_schemas/` via `read_file` → `write_file` (see `references/orchestrator-template.md` Step 1.3).
3. Write `workflow.md` (substitute variables from `_workspace/_schemas/workflow.template.md`):
   {{STAGE_STEP_SUMMARY}}
4. Initialize `findings.md` (based on `_workspace/_schemas/findings.template.md`).
5. Initialize `tasks.md` (based on `_workspace/_schemas/tasks.template.md`).
6. Create `checkpoint.json` (conforming to `_workspace/_schemas/checkpoint.schema.json` schema):
   ```json
   {
     "plan_name": "{{PLAN_NAME}}",
     "status": "in_progress",
     "current_stage": "{first Stage name}",
     "current_step": "{first Step name}",
     "active_pattern": "{first Step pattern}"
   }
   ```
7. **workflow.md schema validation** — 6 required fields + naming convention (no placeholders) + verifiable exit conditions + pattern enum. Violation triggers HALT (see `references/orchestrator-template.md` Step 1.8).
8. **workflow.md cycle validation** (after schema validation passes).

### Step 2: Step Execution Loop

Apply the standard Step 2 procedure from `references/orchestrator-template.md`. Invoke agents by pattern, check exit conditions, handle Stage gates, update checkpoint.json.

## Error Handling

Zero-Tolerance: Agent failure → up to 2 retries (3 total) → if unresolved, set `task_*.json` status=blocked + `ask_user`. Arbitrary skipping is strictly prohibited.
