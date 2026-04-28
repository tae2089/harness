# Phase Selection Matrix for Existing Harness Extension

Referenced when branching into **existing extension** mode in `SKILL.md` Phase 0. Determines the list of Phases to execute based on the type of change.

---

## Step 1: Change Type Classification Decision Tree

```
PROCEDURE classify_change(request):

    // ── Step A: Only workflow.md / Step structure changes? ─────────────────
    IF request affects ONLY ["workflow.md", "checkpoint.json logic"]:
        IF adds new Stage OR adds new Step:
            RETURN "Stage/Step Addition"
        ELSE:                               // exit condition, pattern name, or agent list adjustment only
            RETURN "workflow.md Modification"

    // ── Step B: Only agent / skill file changes? ──────────────────────────
    IF request affects ONLY [".gemini/agents/*.md", "references/skills/"]:
        IF adds new agent OR renames agent role:
            RETURN "Agent Addition"
        ELSE:                               // prompt, checklist, or tool list modification only
            RETURN "Skill Addition/Modification"

    // ── Step C: Architecture change threshold evaluation ──────────────────
    // "Architecture Change" if ANY of the following conditions apply
    // For the full pattern list, see references/agent-design-patterns.md § "7 Core Architecture Patterns"
    Architecture change conditions:
      - Pattern change (e.g., pipeline → fan_out_fan_in)
      - 3 or more agents restructured simultaneously (additions + deletions + role redefinitions combined)
      - Modification of orchestrator Step 2 core branching logic
      - Increase or decrease in the number of Stages

    IF ANY of architecture change conditions:
        RETURN "Architecture Change"

    // ── Step D: Multiple types occur simultaneously ───────────────────────
    // Priority (higher = broader scope):
    // Architecture Change > Stage/Step Addition > Agent Addition > Skill Addition/Modification > workflow.md Modification
    RETURN highest_priority_type(matched_types)
```

---

## Phase Selection Matrix

| Change Type           | Phase 1                        | Phase 2              | Phase 3                     | Phase 4                  | Phase 5                        | Phase 6  |
| --------------------- | ------------------------------ | -------------------- | --------------------------- | ------------------------ | ------------------------------ | -------- |
| Agent Addition        | Skip (use Phase 0 result)      | Placement only       | **Required**                | If dedicated skill needed | Orchestrator modification      | **Required** |
| Skill Addition/Modification | Skip                    | Skip                 | Skip                        | **Required**             | If connection changes           | **Required** |
| Architecture Change   | Skip                           | **Required**         | Affected agents only        | Affected skills only     | **Required**                   | **Required** |
| Stage/Step Addition   | Skip                           | **Required** (redesign) | If new agents needed     | If new skills needed     | **Required** (workflow.md modification) | **Required** |
| workflow.md Modification | Skip                        | Skip                 | Skip                        | Skip                     | **Required** (workflow.md modification + verify consistency with `orchestrator-template.md` Step 0·Step 2 read logic) | **Required** |

---

## Decision Guide

**Agent Addition** — When a new role is needed or an existing agent is overloaded. Phase 1 (domain analysis) is skipped because Phase 0 audit results are already available.

**Skill Addition/Modification** — Only methodology, checklists, or protocols change. Agent persona and architecture remain unchanged, so Phases 1–3 are skipped.

**Architecture Change** — Pattern change (e.g., Pipeline → Fan-out/Fan-in) or 3 or more agents restructured simultaneously. Broadest scope, so full review starting from Phase 2.

**Stage/Step Addition** — Inserting a Stage or Step into an existing workflow. `workflow.md` Stage-Step structure redesign (Phase 2) is required. Execute Phase 3·4 as well if new agents or skills are needed.

**workflow.md Modification** — Only Stage·Step structure or exit conditions change; no agent or skill changes. After modifying `workflow.md` in Phase 5, verify that the orchestrator's Step 0 (checkpoint stage/step name match) and Step 2 (step_block extraction path, exit_cond type) read logic are consistent with the modified structure.

**Architecture change threshold** — Classified as an architecture change if any of the following apply:

| Condition | Example |
|-----------|---------|
| Pattern change | pipeline → fan_out_fan_in |
| 3 or more agents restructured simultaneously | 3 or more additions + deletions + role redefinitions combined |
| Orchestrator Step 2 core branching modification | Change to the Step execution loop structure |
| Increase or decrease in number of Stages | Stage 1 → Stage 2 added, or Stage deleted |

---

## Phase Execution Order Rules

Phases are executed in **ascending numeric order**. Reverse execution is prohibited.

| Rule | Content |
|------|---------|
| **Phase 4 → after Phase 3** | Skills can be connected only after agents are defined. Executing Phase 4 without Phase 3 is allowed only for the Skill Addition/Modification change type. |
| **Phase 5 → after Phase 3·4** | The orchestrator calls agents and skills, so the targets must be defined first. |
| **Phase 6 → always last** | Always executed last regardless of change type. |
| **"Skip" Phases** | If drift (mismatch) is detected in Phase 0 audit, execute the relevant portion of that Phase. |
| **Priority on overlap** | If multiple change types overlap, use the broadest scope (Architecture Change) as the basis. |

```
// Phase execution order dependencies
Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
          (agents)   (skills)  (orchestr) (verify)

// Independent execution allowed (other Phases not needed)
Skill Addition/Modification:  Phase 4 → Phase 6
workflow.md Modification:     Phase 5 → Phase 6
```

---

## Validation Rules

- Even a Phase marked **"Skip"** must be partially executed if a mismatch (drift) is detected in the Phase 0 audit.
- Phase 6 (validation) is **always required** regardless of change type.
- When multiple change types overlap, use the broadest scope (Architecture Change) as the basis.

---

## Practical Case Examples

### Case A: Add 1 agent + 1 dedicated skill

**Situation:** A security review agent (`@security-reviewer`) and a dedicated skill (`security-checklist`) become necessary for an existing Pipeline harness.

```
classify_change → "Agent Addition" (agent addition + skill addition combined → priority: Agent Addition > Skill Addition)

Phase execution:
  Phase 3: Create @security-reviewer.md (new)
  Phase 4: Create security-checklist/SKILL.md (new)
  Phase 5: Orchestrator skill modification
    - Add @security-reviewer to team composition
    - Insert Step N (security-review)
    - Update workflow.md Stage·Step
    - Add "security review", "vulnerability check" keywords to description
  Phase 6: Structure validation + trigger validation (including new agent)

GEMINI.md change log: "@security-reviewer added | security review absence feedback"
```

### Case B: Strengthen an existing skill checklist only

**Situation:** Feedback that the review criteria in the `code-review` skill are insufficient → add checklist items.

```
classify_change → "Skill Addition/Modification" (no agent file or architecture changes)

Phase execution:
  Phase 4: Modify code-review/SKILL.md (add checklist items)
  Phase 6: Skill execution test (Phase 6-3) + trigger validation (Phase 6-4)
            Structure validation (Phase 6-1) can be omitted if no frontmatter changes

GEMINI.md change log: "code-review skill checklist enhanced | review quality feedback"
```

### Case C: Architecture pattern change (Pipeline → Fan-out/Fan-in)

**Situation:** Parallelizing 3 sequential analysis steps to improve speed. Includes role redefinition for 3 existing agents.

```
classify_change → "Architecture Change"
  Conditions matched: pattern change (pipeline → fan_out_fan_in) + 3 agents restructured simultaneously

Phase execution:
  Phase 2: Parallel fan-out structure redesign (workflow.md Stage-Step redefinition)
           Redesign findings.md·tasks.md·checkpoint.json flow
  Phase 3: Modify 3 affected agents
           - Reflect wait_for_previous: false parallel call pattern
           - Redefine I/O paths (branching under _workspace/{plan_name}/)
  Phase 4: Modify parallel execution related skills (if any)
  Phase 5: Full orchestrator overhaul
           - Replace Step execution loop with batch calls
           - Add checkpoint.json active_pattern update logic
  Phase 6: Dry-run test (Phase 6-5) required

GEMINI.md change log: "Architecture Pipeline→Fan-out/Fan-in change | analysis speed improvement purpose"
```

### Case D: Add Stage 2 (validation stage) to existing Stage 1

**Situation:** A harness currently running as a single Stage (e.g., `sso-integration`) needs a final user validation Stage added.

```
classify_change → "Stage/Step Addition"
  Condition matched: increase in number of Stages (1 → 2)

Phase execution:
  Phase 2: workflow.md redesign
           - Stage 1: sso-integration (existing, deliverable noun phrase)
           - Stage 2: user-validation (new, user approval gate: "complete after confirming validation results")
           Define Stage 2 exit condition and transition protocol (names in kebab-case + deliverable meaning; generic placeholders like `main` or `validate` are prohibited)
  Phase 3: Add @qa-validator agent (responsible for new Stage)
  Phase 4: Create validation-checklist skill (if needed)
  Phase 5: Orchestrator modification
           - Add Stage 2 execution block
           - Add checkpoint.json Stage transition (sso-integration → user-validation) logic
           - Specify user approval gate in GEMINI.md
  Phase 6: Resume flow test (Phase 6-6) required — mid-Stage interruption and resume scenario

GEMINI.md change log: "Stage 2 (user-validation) added | absence of user validation gate feedback"
```

---

## Drift Resolution Guide

When a mismatch (drift) is found in a Phase 0 audit, resolve the drift before classifying the change type.

| Drift type | Root cause | Resolution |
|------------|-----------|------------|
| **Agent file exists / not registered in GEMINI.md** | GEMINI.md change log not recorded after adding agent | Correct GEMINI.md change log, then re-validate with Phase 6-1 |
| **Registered in GEMINI.md / agent file missing** | File deletion omitted or name change not reflected | Confirm intent with `ask_user`, then restore file or delete GEMINI.md entry |
| **Orchestrator references agent ≠ actual file** | File name changed during refactoring without updating reference | Partial Phase 5 execution — correct agent name in orchestrator |
| **Skill description trigger conflict** | Keyword overlap with existing skill after adding new skill | Partial Phase 6-4 (trigger validation) execution — adjust description |
| **checkpoint.json current_step ≠ workflow.md step name** | checkpoint.json not updated after modifying workflow.md | Confirm current position with `ask_user`, then manually correct checkpoint.json |
| **Orchestrator SKILL.md flat Step listing (no Stage hierarchy)** | Stage-Step model not applied at initial creation (e.g., flat `Step 0~4` headers as in `examples/sso-dev-flow`) | **Apply `skill-writing-guide.md` §7-6 migration guide 6 steps (M1~M6)** — inventory → Stage mapping → pattern assignment → exit condition conversion → write 5 artifact types → bundle schemas/. Reference package: `references/examples/full-bundle/sso-style.md`. |
| **Exit conditions in natural language ("QA approved", "enough", "when complete")** | LLM arbitrary interpretation expressions remaining in workflow.md or orchestrator SKILL.md | Apply `orchestrator-template.md` Step 1.7 schema validation routine → if whitelist violation detected, rewrite as verifiable predicates (`task_*.json status=done`, `{file}.json verdict=PASS`, `iterations ≥ N`, etc.) |
| **workflow.md required fields missing** | One or more of `pattern`, `active agents`, `exit condition`, `next step`, `max iterations`, Stage `user approval gate` missing | Supplement immediately. See [MANDATORY] 6-field table in `SKILL.md` Phase 2-1. If missing: Zero-Tolerance Failure → ask_user → HALT |
| **findings.md using arbitrary sections** (e.g., `[Review: stage]`) | Standard sections not followed | Convert to standard sections (`[Key Insights]`, `[Change Requests]`, `[Shared Variables/Paths]`, etc.). See "findings.md Standard Section Structure" table in `references/team-examples.md` |
| **task_*.json persistence unused** (only simple tasks.md checkbox) | Parallel agent reports replaced by direct tasks.md modification — race condition risk | Assign each agent the obligation to write `_workspace/tasks/task_{agent}_{id}.json`. Main agent collects via GLOB and updates tasks.md via ATOMIC_WRITE |

**Drift resolution principle:** If even one drift item exists, it must be resolved before executing the change type Phases. Drift resolution itself is confirmed via Phase 6-1 (structure validation) and recorded in the GEMINI.md change log.
