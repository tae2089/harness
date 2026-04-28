# Stage-Step Workflow Guide

A guide that defines the workflow structure for all harnesses. Declaring the Stage-Step hierarchy in `_workspace/workflow.md` ensures the orchestrator executes deterministically. Referenced in SKILL.md Step 2 or Step 5.

---

## Table of Contents

1. [Concept Definitions](#1-concept-definitions)
2. [workflow.md Specification](#2-workflowmd-specification)
3. [checkpoint.json Schema](#3-checkpointjson-schema)
4. [Step·Stage Transition Protocol](#4-stepstage-transition-protocol)
5. [Verifiable Exit Condition Patterns](#5-verifiable-exit-condition-patterns)
6. [Per-Step Agent Access Control](#6-per-step-agent-access-control)
7. [Workflow Examples (5 types)](#7-workflow-examples-5-types)
8. [Test Scenarios (6 types)](#8-test-scenarios-6-types)

---

## 1. Concept Definitions

### 3-tier hierarchy model (Stage = parent issue, Step = child issue)

Every harness is structured as a **Stage → Step → Agent** 3-tier hierarchy. **This directly borrows from Jira's issue hierarchy (Issue → Sub-issue).**

| Tier | Jira equivalent | Meaning | Transition owner | Responsibility |
|------|-----------------|---------|-----------------|----------------|
| **Stage** | **Parent issue (Issue / Story)** | A grouping of deliverable-unit work | User approval gate | Groups multiple child issues (Steps) to complete one deliverable. Transitions to the next Stage only after approval. |
| **Step** | **Child issue (Sub-issue)** | A single work item within a Stage | Orchestrator (automatic) | **1 Step = 1 pattern**. Holds one of the 7 core patterns + active agents + exit condition. Transitions automatically. |
| **Agent** | Task assignee | Step executor | Called within Step | Performs the actual work. Access controlled by the Step's `active agents` list. |

> **Core semantics (borrowed from Jira):** A Stage is a **parent issue**, and a Step is a **sub-issue**. A Stage is not a direct execution unit itself; all its child issues (Steps) must be completed before the parent issue (Stage) closes. The user approval gate is at the Stage level — the same flow as requiring PM approval before marking a Story as Done in Jira.

> **Workflow ↔ Jira mapping example:**
> - Jira Story "Payment Module SSO Integration" = one Stage in workflow.md (`Stage 1: integrate-sso`)
> - Jira Sub-issue "Implement OAuth Callback Handler" = one Step in that Stage (`Step 2: implement-callback`)
> - Sub-issue assignee = Step's `active agents`

The Stage·Step structure is declared in `_workspace/workflow.md`. The orchestrator always reads this file to determine the current stage and step.

> **workflow.md is a static declaration.** It is created once in Step 1 and the Stage·Step structure does not change during execution. When agent selection is determined dynamically (e.g., `[@selected_expert]`), that notation is a **runtime symbolic placeholder** — the orchestrator reads the `shared_variables.selected_expert` field in `checkpoint.json` when entering that Step and substitutes the actual agent name. workflow.md itself is not modified.
>
> **Naming convention distinction:** JSON keys in `shared_variables` use `selected_expert` (English snake_case). The symbolic placeholder in workflow.md uses `[@selected_expert]` (English). The two names do not need to match — the mapping relationship is that the orchestrator reads the `selected_expert` value and substitutes it in place of `@selected_expert`, so the name format is at the implementer's discretion.

### Simple vs. Multi-step

| Type | Number of Stages (parent issues) | Number of Steps (child issues) | When to use |
|------|----------------------------------|-------------------------------|-------------|
| **Simple** | 1 (`main`) | 1 (`main`) | Completes with a single child issue and a single pattern |
| **Multi-step** | 2 or more, or a Stage with 2 or more Steps | Multiple | Parent issue decomposes into multiple child issues + exit conditions are verifiable + user can intervene at the Stage (parent issue) gate |

---

## 2. workflow.md Specification

`_workspace/workflow.md` is mandatory for all harnesses. It declares the Stage·Step structure and is read by the orchestrator every cycle.

> When writing in practice, substitute variables in `_workspace/_schemas/workflow.template.md` (the copy synchronized in Step 1.3) and `write_file` to `_workspace/workflow.md`.

### Simple workflow example (stage 1 + step 1)

> **Naming note:** Placeholders like `main` or `step1` are prohibited. Stage·Step names must be deliverable-meaningful kebab-case (Jira title convention). No exceptions even for single-Stage, single-Step cases.

```markdown
<!-- Reference pattern: fan_out_fan_in (no effect on execution, for documentation only) -->

## Stage Definitions

### Stage 1: blog-post
- Exit condition: all steps completed
- Next stage: done
- User approval gate: none

#### Step 1: parallel-research
- Pattern: fan_out_fan_in
- Active agents: [@researcher-a, @researcher-b, @researcher-c]
- Exit condition: all `_workspace/tasks/task_*.json` have status=done
- Next step: done
- Max iterations: 1
```

### Multi-step workflow example (stage 2 + multiple steps)

```markdown
<!-- Reference patterns: fan_out_fan_in → producer_reviewer (no effect on execution, for documentation only) -->

## Stage Definitions

### Stage 1: gather
- Exit condition: all steps completed
- Next stage: refine
- User approval gate: required

#### Step 1: research
- Pattern: fan_out_fan_in
- Active agents: [@researcher-trend, @researcher-data]
- Exit condition: `_workspace/research/task_trend.json`, `task_data.json` all have status=done
- Next step: done
- Max iterations: 1

### Stage 2: refine
- Exit condition: all steps completed
- Next stage: done
- User approval gate: none (last stage)

#### Step 1: draft-review
- Pattern: producer_reviewer
- Active agents: [@writer, @editor]
- Exit condition: verdict=PASS in `_workspace/editor_verdict.json`
- Next step: done
- Max iterations: 3
```

### workflow.md field writing rules

| Field | Writing rule | Example |
|------|-------------|---------|
| `Active agents` | Declared in Step blocks only. `@name` format, must match `.gemini/agents/{name}.md` | `[@writer, @editor]` |
| `Exit condition` | Only verifiable predicates allowed (file existence, JSON field value, numeric threshold) | all `task_*.json` have status=done |
| `Next step` | Next step name or `done` | `architecture` / `done` |
| `Next stage` | Next stage name or `done` | `validate` / `done` |
| `Max iterations` | Required for loop patterns (Producer-Reviewer, etc.) to prevent infinite loops | `3` |
| Stage `Exit condition` | `all steps completed` or a specific verifiable condition | `all steps completed` |

---

## 3. checkpoint.json Schema

> **The authoritative source is `references/orchestrator-template.md` — "Data Persistence Protocol" section.** Refer to that file for full field descriptions and examples.

Additional fields required for Stage-Step workflows: `current_stage`, `current_step`, `active_pattern`, `stage_history`, `step_history`, `stage_artifacts`. All are included in the authoritative schema.

---

## 4. Step·Stage Transition Protocol

### Step transition vs. Stage transition comparison

| Type | Transition owner | User approval | checkpoint.json update |
|------|-----------------|--------------|------------------------|
| **Step transition** | Orchestrator (automatic) | Not required | `current_step`, `step_history`, `handoff_chain: []` |
| **Stage transition** | Orchestrator after user approval | **Required** | `current_stage`, `current_step` (first Step of next Stage), `stage_history`, `handoff_chain: []` |

### Step Transition Protocol (automatic)

The internal loop performed by the orchestrator every cycle. Order must be strictly followed.

1. Read `current_stage`, `current_step` from `checkpoint.json`.
2. Read the exit condition of the corresponding step block from `workflow.md`.
3. Verify the exit condition (file scan, JSON field check).
4. **Not met** → call active agents for the current step pattern, then wait for the next cycle.
5. **Met** → check `Next step`:
   - Next step name → immediately update checkpoint.json → allow entering the next step within the same turn.
   - `done` → proceed with Stage Transition Protocol.

### Stage Transition Protocol (approval required)

1. Confirm the last step of the current stage is `done`.
2. Report to the user in the format below.
3. **On approval:** Update checkpoint.json (current_stage, current_step, stage_history, handoff_chain: []).
4. **On rejection:** No change to checkpoint.json → ask "What part would you like to revise?" → ATOMIC rollback to the specified step:
   - Update checkpoint.json: `current_step` ← specified step, `active_pattern` ← that step's pattern, `handoff_chain: []`, `last_updated` ← NOW().
   - Delete existing task files for agents of that step: `_workspace/tasks/task_{step_agent}_*.json`.
5. **[Prohibited]** Do not call the next stage's agents in the same response turn as the approval.
6. **Re-entry:** User sends "continue" or equivalent → orchestrator re-executes Step 0 → detects `status: "in_progress"` + updated `current_stage`·`current_step` → enters Step 2 and immediately starts the first Step of the new Stage.

### User approval gate format

```
Stage {current stage} completed:
  Step {step-1}: {exit condition} ✓
  Step {step-2}: {exit condition} ✓

Next Stage: {next stage}
  Step list: [{step-1}, {step-2}]
  First Step active agents: {agent list}
  First Step exit condition: {condition}

Proceed? [Y/N]
```

---

## 5. Verifiable Exit Condition Patterns

| Recommended (verifiable) | Prohibited (LLM arbitrary interpretation) |
|---|---|
| all `_workspace/tasks/task_*.json` have status=done | "Enough has been gathered" |
| verdict=PASS in `_workspace/critic_verdict.json` | "The review is satisfactory" |
| score ≥ threshold in `_workspace/coverage.json` | "Quality is good" |
| Specific file exists (`_workspace/integrated.md`) | "Integration is complete" |
| iterations of the relevant step in step_history ≥ max_iterations | "Iterated enough" |

---

## 6. Per-Step Agent Access Control

Gemini CLI agent frontmatter does not support custom fields. Access control is performed via the **`active agents` list in the step block of workflow.md**.

```
Before calling invoke_agent:
1. Find the current_stage → current_step block in workflow.md.
2. Read the `active agents` list for that step.
3. If the target is in the list → allow invoke_agent.
4. If not in the list → hold the call, and report to the user if needed:
   "@writer is not an active agent for the current step ({current_stage}/{current_step})."
```

---

## 7. Workflow Examples (5 types)

| # | Domain | Pattern combination | Number of Stages (parent issues) | Number of Steps (child issues) | File |
|---|--------|--------------------|---------------------------------|-------------------------------|------|
| 1 | Blog post writing | gather=fan_out_fan_in → write=producer_reviewer | 2 | 2 | [examples/step/01-blog-post.md](examples/step/01-blog-post.md) |
| 2 | Issue triage | triage=(expert_pool+pipeline) → review=producer_reviewer | 2 | 3 | [examples/step/02-issue-triage.md](examples/step/02-issue-triage.md) |
| 3 | Architecture design | design=pipeline(3 Steps) → validate=fan_out_fan_in | 2 | 4 | [examples/step/03-architecture-design.md](examples/step/03-architecture-design.md) |
| 4 | Feature implementation (single Stage, multiple Tasks) | feature-build = research(fan_out) → implement(pipeline) → review(producer_reviewer) | 1 | 3 | [examples/step/04-single-stage-multi-task.md](examples/step/04-single-stage-multi-task.md) |
| 5 | Product lifecycle (multiple Stages, multiple Tasks) | discovery(fan_out+pipeline) → build(pipeline+supervisor+producer_reviewer) → validate(fan_out+pipeline) | 3 | 7 | [examples/step/05-multi-stage-multi-task.md](examples/step/05-multi-stage-multi-task.md) |

---

## 8. Test Scenarios (6 types)

Detailed setup, expected behavior, and pass criteria: [examples/step/test-scenarios.md](examples/step/test-scenarios.md)

| # | Purpose | Key verification point | Pass criteria |
|---|---------|----------------------|---------------|
| 1 | Simple workflow.md structure validation | Whether Stage 1 + Step 1 are created | No Stage 2 block + `main/main` structure |
| 2 | Multi-step workflow trigger | Multi-step automatically selected from utterance | 2 or more Stage blocks exist |
| 3 | Step exit condition not met → transition blocked | Next Step entry prohibited when there are incomplete tasks | No invoke_agent for Stage 2 agents |
| 4 | Automatic Step transition (no approval needed) | Transition without user intervention when exit condition is met | Next Step agent called without approval request |
| 5 | Stage transition gate (approval required) | Approval gate triggered when Stage is complete | Approval request issued + next Stage agents not called |
| 6 | Per-step agent access control | Calls to agents not in the current Step list are blocked | No invoke_agent for inactive agents |
