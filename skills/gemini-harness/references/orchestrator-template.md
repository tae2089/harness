# Orchestrator Skill Advanced Template

The orchestrator is the top-level skill used by the main agent to execute orchestration logic. Because the Gemini CLI environment **does not allow direct communication between sub-agents**, the main agent acts as the sole **Data Broker**, coordinating the team via `findings.md`, `tasks.md`, and `checkpoint.json`. This template covers the single Gemini CLI execution mode: file-based brokering.

> **Note:** Sub-agent invocation uses `invoke_agent`. Parallel execution: `wait_for_previous: false`. Shell background processes (dev server, etc.): `run_shell_command`. For API differences from Claude Code (`TeamCreate`, `SendMessage`, `TaskCreate` absence explained): see `references/agent-design-patterns.md` § "Execution Mode: Orchestration".

## Orchestrator Base Structure (Data Broker Enhanced)

````markdown
---
name: {domain}-orchestrator
description: "{Domain} harness orchestrator. Coordinates a virtual team via shared findings (findings.md), state persistence (checkpoint.json), and task management (tasks.md). {Initial trigger keywords}. Also use this skill for follow-up work ({domain} result modification / partial re-run / update / supplement / re-execute / improve previous results) to maintain consistency."
---

# {Domain} Orchestrator

## Virtual Team Composition

> **Common required tools (table omitted):** `ask_user`, `activate_skill`
> **Orchestrator only:** `invoke_agent` — do not grant this to worker sub-agents.

| agent     | type                    | role   | skill   | output        |
| --------- | ----------------------- | ------ | ------- | ------------- |
| {agent-1} | {custom or built-in}    | {role} | {skill} | {output-file} |
| {agent-2} | {custom or built-in}    | {role} | {skill} | {output-file} |

## Workflow

### Step 0: Context Check (Durable Execution)

Determine the entry path based on the state of `_workspace/checkpoint.json`. **Evaluate the table top-to-bottom in order** and execute the action of the first matching row.

| `_workspace/` | `ckpt.status` | Additional condition | Action |
|---|---|---|---|
| absent | — | — | GOTO Step 1 |
| present | `in_progress` or `partial` | — | Read workflow.md → GOTO Step 2 ¹ |
| present | `blocked` | response = "continue/resume/resolved" | Delete blocked task file ² → update checkpoint `{status:"in_progress"}` → GOTO Step 2 |
| present | `blocked` | response = "from scratch/reset" | Backup `_workspace/` → `_workspace_{NOW()}/` → GOTO Step 1 |
| present | `blocked` | other (including first entry) | Report blocked reason ³ → `ask_user` → HALT |
| present | `completed` | request = "partial modification" | Determine RESUME_FROM ⁴ → update checkpoint `{status:"partial", current_stage, current_step}` → GOTO Step 2 |
| present | `completed` | other | Backup `_workspace/` → `_workspace_{YYYYMMDD_HHMMSS}/` → GOTO Step 1 |

¹ Auto-resume path after max_turns exhausted. No manual intervention required.

² Files to delete: `_workspace/tasks/task_{ckpt.blocked_agent}_*.json` (identified by `ckpt.blocked_agent`). Do not touch Blocked files from other steps.

³ Blocked reason report format:
```
Previous execution Blocked. Reason: {ckpt.blocked_reason} | Agent: {ckpt.blocked_agent}
Please resolve the blocking cause and resume. ("continue" / "from scratch")
```
> `ask_user` re-evaluates this table on the next turn.

⁴ **Partial modification RESUME_FROM determination:**

| Request type | RESUME_FROM |
|---|---|
| "Modify agent X prompt/output" | `{stage: ckpt.current_stage, agent: X}` |
| "Modify skill Y" | `{skill: Y}` (re-invoke only those agents) |
| "Modify workflow.md / exit condition" | `{stage: ckpt.current_stage, step: ckpt.current_step}` |
| Scope unclear | `ask_user("Confirm modification scope: which agent, skill, or file?")` → RETURN |

---

### Step 1: Initialization

1. Parse `{plan_name}` from `user_input`. If absent, `ask_user("Please specify a task name.")` → RETURN.
2. Create directories: `_workspace/`, `_workspace/{plan_name}/`, `_workspace/tasks/`, `_workspace/_schemas/`.
3. **Schema template sync (required):** Read the 5 files from this skill's `references/schemas/` directory and write them to `_workspace/_schemas/`. Execute one `read_file` → `write_file` pair per file:

   | Source (skill reference path) | Destination (workspace path) |
   |-------------------------------|------------------------------|
   | `references/schemas/task.schema.json` | `_workspace/_schemas/task.schema.json` |
   | `references/schemas/checkpoint.schema.json` | `_workspace/_schemas/checkpoint.schema.json` |
   | `references/schemas/workflow.template.md` | `_workspace/_schemas/workflow.template.md` |
   | `references/schemas/findings.template.md` | `_workspace/_schemas/findings.template.md` |
   | `references/schemas/tasks.template.md` | `_workspace/_schemas/tasks.template.md` |
   | `references/schemas/models.md` | `_workspace/_schemas/models.md` |
   | `references/schemas/agent-worker.template.md` | `_workspace/_schemas/agent-worker.template.md` |
   | `references/schemas/agent-orchestrator.template.md` | `_workspace/_schemas/agent-orchestrator.template.md` |
   | `references/schemas/agent-state-manager.template.md` | `_workspace/_schemas/agent-state-manager.template.md` |

   > `README.md`, `models.md`, and agent templates are reference material for agent definition creation — the workspace copies serve as the baseline for generation. `models.md` is the SoT for model IDs and must always be synced.
   > **`run_shell_command("cp ...")` is prohibited** — the skill reference path is unreachable from the shell in the runtime working directory (user project root). Always use agent tools `read_file` + `write_file`.

   **Operating rules:**
   - Worker agents must read `_workspace/_schemas/task.schema.json` before writing their own output.
   - The main agent must validate against the schema every time it updates `task_*.json` or `checkpoint.json`.
   - Schema updates take effect from the next init. Do not change workspace schemas mid-run (preserve the snapshot).
   - **SoT:** `references/schemas/`. Workspace copies are point-in-time snapshots.

4. Write `workflow.md` — use `_workspace/_schemas/workflow.template.md` as the starting point. Timing varies by pattern:

   | Pattern | Writing approach |
   |---------|-----------------|
   | `pipeline` / `fan_out_fan_in` / `producer_reviewer` / `handoff` / `expert_pool` | Write immediately based on user request |
   | `supervisor` / `hierarchical` | Invoke Discovery Agent first → write based on its output |

5. Initialize `findings.md` — copy `_workspace/_schemas/findings.template.md`, then remove all sections not needed for the current pattern:

   | Pattern | Sections |
   |---------|----------|
   | All patterns (common) | `[Shared Variables/Paths]` |
   | fan_out / fan_out_fan_in | + `[Key Insights]`, `[Key Keywords]`, `[Data Conflicts]` |
   | producer_reviewer | + `[Change Requests]` |
   | pipeline / hierarchical | + `[Next Stage Instructions]` |
   | supervisor / handoff | + `[Data Conflicts]` |
   | expert_pool | + `[Routing Rationale]` (format: `"- {agent}: {reason} (matched keywords: {keywords})"`) |

6. Initialize `tasks.md` — copy `_workspace/_schemas/tasks.template.md` (keep header only, clear rows).
7. Create `checkpoint.json` — fill in all fields from `_workspace/_schemas/checkpoint.schema.json`:

```json
{
  "execution_id":   "YYYYMMDD_HHMMSS",
  "plan_name":      "{plan_name}",
  "status":         "in_progress",
  "current_stage":  "{workflow.stages[0].name}",
  "current_step":  "{workflow.stages[0].steps[0].name}",
  "active_pattern": "{first_step.pattern}",
  "stage_history":  [],
  "step_history":  [],
  "stage_artifacts": {},
  "handoff_chain":  [],
  "tasks_snapshot": { "done": [], "current": null },
  "shared_variables": {},
  "last_updated":   "NOW()"
}
```

> **`@state-manager` delegation pattern (optional):** If the virtual team includes `@state-manager`, delegate steps 5–7 (findings.md, tasks.md, checkpoint.json initialization) and all state updates in Step 2 to `invoke_agent(@state-manager, ...)`. The orchestrator focuses on reasoning and coordination; state I/O is handled by `@state-manager` (flash model) after schema validation. Interface: `OPERATION: state.init|checkpoint.update|task.upsert|findings.append|tasks.update|state.archive` + `PAYLOAD:` block. Full spec: `references/schemas/agent-state-manager.template.md`.

> **Notation bridge:** `workflow.md` declares Stages and Steps using **markdown headers only** (`### Stage 1: {deliverable-name}`, `#### Step 1: {deliverable-name}`), not JSON. The `"current_stage": "{workflow.stages[0].name}"` notation in the checkpoint.json above is pseudocode meaning "the name parsed from the first `### Stage` header" — it is not a JSON array access.
> **Parsing example:** `### Stage 1: sso-integration` → `current_stage = "sso-integration"` / `#### Step 1: requirements-gathering` → `current_step = "requirements-gathering"`. The orchestrator reads `workflow.md` via `read_file`, builds the Stage/Step list in header order, and references them by name (text).
> **Naming convention (required):** Placeholders such as `main`, `step1`, `task` are forbidden. Use kebab-case + deliverable-meaning noun phrase (Jira title convention). Violations are blocked at workflow.md schema validation.

8. **workflow.md schema validation (required immediately after writing, before cycle validation):**

   Check **all required field absences** in each Stage/Step block. Block immediately if even one is missing.

   | Check | Method | On failure |
   |-------|--------|------------|
   | Stage fields: `exit condition`, `next stage`, `user approval gate` | Verify field presence below header using regex/parser | `ask_user("workflow.md Stage {name} missing required fields: {missing_fields}. Please add them and retry.")` → HALT |
   | Step fields: `pattern`, `active agents`, `exit condition`, `next step`, `max iterations` | Same | Same |
   | `pattern` value = one of 7 (`pipeline`, `fan_out_fan_in`, `expert_pool`, `producer_reviewer`, `supervisor`, `hierarchical`, `handoff`) | Enum check | `ask_user("Pattern value violation: {value}. Choose from the 7 patterns.")` → HALT |
   | `active agents` format = `[@name, ...]` | Regex `\[(@\w[\w-]*\s*,?\s*)+\]` | `ask_user("Active agents format violation.")` → HALT |
   | **`exit condition` verifiable predicate** | Keyword whitelist: `task_*.json`, `status=done`, `exists`, `verdict=`, `score ≥`, `iterations ≥`. If not matching whitelist AND contains natural-language interpretation keywords (`approved`, `sufficient`, `when complete`, `satisfied`, `appropriately`) → violation | `ask_user("Step {name} exit condition is natural language ('{value}'). Rewrite as a verifiable predicate: file existence, JSON field value, iteration ≥ N.")` → HALT |
   | User approval gate missing | Not specified in Stage block | Same |
   | **Stage/Step naming convention (Jira title convention)** | Extract header name → regex `^[a-z][a-z0-9-]*$` match + not in placeholder blacklist (`main`, `step1`, `task`, `work`, `default`, `phase1`, `stage1`, `generic`) | `ask_user("Stage/Step name violation: '{name}'. Rewrite as kebab-case + deliverable noun phrase (e.g. sso-integration, requirements-gathering). Placeholders are forbidden.")` → HALT |

9. **workflow.md cycle validation (after schema validation passes):**

   | Check | Method | On failure |
   |-------|--------|------------|
   | Circular reference within Step | Trace each Stage's Step `next step` links in order — if an already-visited Step name reappears → cycle | `ask_user("Circular reference found in workflow.md: {Stage} → {cycle_path}. Please fix and retry.")` → HALT |
   | No `done` reachable within Stage | Step chain end is not `done` | Same |
   | Undefined Step reference | `next step` value is a Step name that does not exist in the same Stage | Same |

   > Both checks run exactly once before entering the Step 2 loop. May be skipped on resume paths (Step 0 → Step 2) since workflow.md is already validated.

10. GOTO Step 2.

---

### Step 2: Step Execution Loop

**At the start of each cycle:**

1. Read `workflow.md`, `checkpoint.json`, `findings.md`.
2. Extract `workflow[ckpt.current_stage][ckpt.current_step]` → `step_block`. If not found, record error in findings.md → `ask_user` → HALT.
3. Extract `active_agents`, `pattern`, `exit_cond`, `max_iterations` from `step_block`.
4. **Resolve symbolic placeholders:** If `active_agents` contains symbolic names such as `@selected_expert`:
   - Read `checkpoint.shared_variables.selected_expert` → substitute with actual agent name.
   - If field does not exist → `ask_user("The expert_pool Step has not yet run, or selected_expert was not recorded. Which agent should be called?")` → RETURN.
   > This substitution is runtime-only. Do not modify the workflow.md file itself.
5. **Pre-blocked check (required before invoking agents):** If any `_workspace/tasks/task_*.json` has `status=="blocked" AND agent IN active_agents` → update checkpoint to `blocked` → `ask_user` → RETURN. Absolutely no agent invocation.
6. Access control: only agents in the `active_agents` list may be invoked.
7. **Inject findings.md context:** Include the full `findings.md` in the agent invocation prompt.
   ```
   invoke_agent(@{name}, prompt="""
   {task_description}

   ## Shared Context (findings.md)
   @{_workspace/findings.md}
   """)
   ```
   > Include the header even if findings.md is empty — agents use it to recognize the section structure.

**Agent invocation by pattern:**

| Pattern | Invocation method | Record after completion |
|---------|-------------------|------------------------|
| `pipeline` / `hierarchical` | Sequential (`wait_for_previous=true`), record immediately per agent | findings.md, tasks.md, checkpoint.json |
| `fan_out` / `fan_out_fan_in` | Parallel (`wait_for_previous=false`) → after all complete, `COLLECT ALL task_*.json` → ATOMIC_WRITE ⁷ | tasks/task_{agent}_{id}.json, tasks.md, findings.md, checkpoint.json |
| `producer_reviewer` | — | GOTO Step 3 |
| `expert_pool` | CLASSIFY → single agent sequential ⁵ | findings.md[Routing Rationale], task file, tasks.md |
| `supervisor` | Parallel per batch → ATOMIC_WRITE per batch | tasks.md, checkpoint.json |
| `handoff` | Sequential, parse `[NEXT_AGENT]` keyword ⁶ | task file (recipient or first agent), findings.md, tasks.md |

⁵ **expert_pool details:**
1. CLASSIFY(user_request, active_agents): compare keywords vs. descriptions → return best agent or AMBIGUOUS.
2. AMBIGUOUS → `ask_user("Expert list: {active_agents}")` → RETURN.
3. Record findings.md[Routing Rationale] → update checkpoint `shared_variables.selected_expert` → invoke agent → record task file.

⁶ **handoff details:**
1. Invoke `active_agents[0]`.
2. If response contains `[NEXT_AGENT: @{name}]`: `handle_handoff({name})` cycle detection → compose next_prompt → invoke `{name}` → record `task_{name}_{id}.json`.
3. If `[NEXT_AGENT]` is absent: record `task_{active_agents[0]}_{id}.json` (completed alone).

⁷ **fan_out / fan_out_fan_in agent responsibility:** Each parallel agent writes its own `_workspace/tasks/task_{agent}_{id}.json` immediately after completing its work (the main agent does not write on their behalf). The main agent collects files via GLOB after all complete and consolidates via ATOMIC_WRITE.

   **Partial failure recovery (if some agent task files are missing):**
   1. GLOB result count < expected agent count → identify missing agents (set difference of active_agents minus GLOB results).
   2. Zero-Tolerance re-invoke each missing agent (max 2 retries, 3 total attempts).
   3. Still missing after retries → call `blocked_protocol(agent, task)` → HALT. Absolutely no forced progress with partial results.
   4. Perform ATOMIC_WRITE only after all agent task files are confirmed.

**Exit condition check (by `exit_cond` type):**

| Type | Exit condition format | Check method |
|------|-----------------------|-------------|
| A | All `task_*.json` have `status=done` | GLOB → exhaustively check status field (`"done"` lowercase — per task.schema.json enum) |
| B | Specific file exists | `EXISTS(path)` |
| C | JSON field value (e.g. `verdict=PASS`) | READ file → compare field |
| D | `iterations ≥ N` | Find the last entry in `step_history` array where `stage==current_stage AND step==current_step`, compare `.iterations` (linear search, not dict access by index) |

**On exit condition met — Step/Stage transition:**

1. Record completion in checkpoint.json `step_history`.
2. If `step_block.next_step` is absent (field missing, null, or empty) → record error in findings.md → `ask_user` → HALT.
3. `next_step != "done"` → update checkpoint (`current_step`, `active_pattern`, `handoff_chain: []`) → re-enter top of Step 2 loop (proceed to next Step).
4. `next_step == "done"` → GOTO Stage Transition Gate. (Details: `references/stage-step-guide.md` § "Stage Transition Protocol")

**On exit condition not met:**

1. `iterations < max_iterations` → find the entry in `step_history` array where `stage==current_stage AND step==current_step` and increment `.iterations` (add new entry if not found) → if `active_pattern == "handoff"`, reset checkpoint.json `handoff_chain: []` (new iteration = new chain) → re-enter top of Step 2 loop (re-execute same Step).
2. Exhausted → record `"Step {current_step}: max_iterations exhausted, exit condition not met"` in findings.md → blocked_protocol. (Details: `references/orchestrator-procedures.md`)

---

### Step 3: Fix Loop (producer_reviewer only)

```
retries ← 0

WHILE retries < 3:
    CALL invoke_agent(@producer, prompt="Refer to @{_workspace/findings.md}. {generation instructions}.")
    WRITE "_workspace/{plan_name}/{output}_v{retries+1}.md" ← producer result

    CALL invoke_agent(@reviewer, prompt="Validate @{above file}. Record result in task_{reviewer}_{id}.json.")
    READ "_workspace/tasks/task_{reviewer}_{id}.json" → review

    IF review.status == "done":  // PASS
        ATOMIC_WRITE { tasks.md ← PASS evidence, checkpoint.json ← tasks_snapshot update }
        GOTO Step 4

    ELSE:  // FAIL
        retries += 1
        IF retries >= 3:
            UPDATE tasks.md ← task "blocked"
            CALL ask_user("Validation failed after 3 attempts. Requesting intervention.")
            RETURN
        WRITE findings.md["Change Requests"] ← review.evidence  // inject feedback and retry
```

---

### Step 4: Integration and Final Output

1. `GLOB "_workspace/tasks/task_*.json"` → filter only `status=="done"` files → extract `artifact_path` from each file → build `artifacts` list.
2. Check `[Data Conflicts]` section in findings.md → if conflicts exist, invoke reviewer agent to resolve. If unresolved → `ask_user` → RETURN.
3. `_workspace/{plan_name}/final_{output}.md` ← save after merging (MERGE) artifacts.
   > MERGE: Read each agent's output in role order and concatenate section by section. Format determined by domain (markdown: concatenate as `## {agent name}\n{content}`, JSON: merge keys, code: list of file paths).

---

### Step 5: Archive and Report

1. Copy `findings.md`, `tasks.md` → `_workspace/{plan_name}/` (preserve detailed history).
2. Replace `findings.md` with summary: keep only `[Final Result Summary]` + `[Archive Path]` sections.
3. Update `checkpoint.json`: `status:"completed"`, `current_stage/step:"done"`, record completion in `stage_history`.
4. Report to user:

```
Completed: {plan_name}
Output:         _workspace/{plan_name}/final_{output}.md
Detailed log:   _workspace/{plan_name}/findings.md
tasks:          _workspace/{plan_name}/tasks.md
```

## Data Persistence Protocol (checkpoint.json Schema)

> **Canonical spec.** Other files such as `stage-step-guide.md` reference this schema.

### Field Descriptions

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `execution_id` | string | Execution ID in `YYYYMMDD_HHMMSS` format. | **Required** |
| `plan_name` | string | Execution plan identifier. | **Required** |
| `status` | string | `"in_progress"` \| `"completed"` \| `"partial"` \| `"blocked"`. | **Required** |
| `last_updated` | string | ISO 8601 timestamp. | **Required** |
| `current_stage` | string | Name of the currently active stage. **Enforced deliverable kebab-case** (e.g. `"sso-integration"`); placeholders (e.g. `"main"`) are forbidden. | **Required** |
| `current_step` | string | Name of the currently active step. **Enforced deliverable kebab-case** (e.g. `"requirements-gathering"`); placeholders (`"main"`, `"step1"`, etc.) are forbidden. | **Required** |
| `active_pattern` | string | Execution pattern for the current step (e.g. `"pipeline"`). | Recommended |
| `stage_history` | array | Record of completed stages. Includes `started_at` + `completed_at`. | Multi-stage |
| `step_history` | array | Record of completed steps. Includes `iterations`. | Multi-stage |
| `stage_artifacts` | object | Mapping of key output paths per stage. | Optional |
| `tasks_snapshot` | object | Snapshot of current task completion status. | Optional |
| `shared_variables` | object | Runtime variables shared across multiple agents. | Optional |
| `handoff_chain` | array | Order of agents invoked within the current step when using the Handoff pattern. Used for cycle detection. Reset on step transition. | Handoff pattern |
| `blocked_agent` | string | Name of the agent that caused the block. Recorded only when transitioning to `status:"blocked"`. | When blocked |
| `blocked_reason` | string | Cause of the block. Displayed to the user on resume. | When blocked |

### Schema Example

```json
{
  "execution_id": "20260425_103000",
  "plan_name": "blog-writing-run-001",
  "status": "in_progress",
  "last_updated": "2026-04-25T10:30:00Z",

  "current_stage": "refine",
  "current_step": "draft-review",
  "active_pattern": "producer_reviewer",

  "stage_history": [
    { "stage": "gather", "started_at": "2026-04-25T09:00:00Z", "completed_at": "2026-04-25T10:00:00Z" }
  ],
  "step_history": [
    { "stage": "gather", "step": "research", "completed_at": "2026-04-25T10:00:00Z", "iterations": 1 }
  ],

  "stage_artifacts": { "gather": "_workspace/research/", "refine": "_workspace/draft.md" },
  "tasks_snapshot": { "done": ["T1", "T2"], "current": "T3" },
  "shared_variables": { "main_artifact": "_workspace/plan/02_code.md" },
  "handoff_chain": ["@incident-triage", "@db-fixer"]
}
```
````

## Split Task File Protocol (Split Task Schema)

The `_workspace/tasks/task_{agent}_{id}.json` schema used by sub-agents to report their status during parallel execution.

```json
{
  "agent": "@coder",
  "task_id": "T2",
  "status": "done",
  "retries": 0,
  "evidence": "Reviewer PASS report: _workspace/plan/03_review.md",
  "artifact_path": "_workspace/plan/02_code.md"
}
```

> `status`: `"done"` | `"blocked"`. Transition to blocked when `retries ≥ 2` (0 and 1 are allowed = 3 total attempts).

## Procedures & Principles

> For error handling (`handle_error` / `blocked_protocol` / `handle_handoff`), test scenarios, description keywords, writing principles, and Stage/Step reference:
> See **`references/orchestrator-procedures.md`**.
