# Use Cases: gemini-harness Trigger Utterance → Processing Path Catalog

A catalog of **8 real-world utterance patterns** and their processing paths (mode branching → pattern selection → workflow.md structure → artifacts) when invoking `gemini-harness` to build, extend, or operate a harness. When receiving a new domain, match it to the closest scenario and use it as a reference.

> **Reading order:** §1 Utterance → Mode Mapping → §2 Scenarios (8 types, by domain) → §3 Non-trigger utterances (false-positive prevention) → §4 Phase application guide.

---

## 1. Utterance → Mode Mapping

`gemini-harness` branches into a mode in Phase 0 immediately after triggering (see SKILL.md Phase 0). Mode by utterance pattern:

| Utterance pattern | Mode | Entry Phase | Representative keywords |
|-------------------|------|-------------|------------------------|
| "Set up / build / design a harness for domain X" | **New Build** | Phase 1 → Phase 6 (full) | "set up", "build", "design", "create", "configure" |
| "Add feature/agent Y to an existing harness" | **Existing Extension** | `expansion-matrix.md` matrix → partial Phase execution | "add", "extend", "supplement", "new agent" |
| "Inspect / audit / report status of harness" | **Operations/Maintenance** | `evolution-protocol.md` workflow | "inspect", "audit", "status", "drift", "sync" |
| "Revise / re-run / supplement previous results" | **Operations (partial re-run)** | Phase 0 branches on checkpoint.json status | "re-run", "revise", "previous results", "redo" |

> **Naming convention (Jira title convention) enforced:** Once the domain is decided, all Stage·Step names must be deliverable noun-phrase kebab-case (e.g., `sso-integration`, `requirements-gathering`). Placeholders like `main` or `step1` are blocked by the workflow.md schema validation (see orchestrator-template.md).

---

## 2. Scenarios (8 types)

### Scenario A: SSO Authentication Feature Build (multi-step, pipeline + producer_reviewer)

- **Utterance:** "Add SSO authentication to the Go backend. From design through implementation to QA."
- **Mode:** New Build
- **Pattern selection rationale:** Analysis → design → implementation are sequentially dependent (pipeline) + implementation artifact quality gate loop needed (producer_reviewer).
- **Stage/Step structure:**
  ```
  Stage 1: research-plan        (user approval gate: required)
    Step 1: requirements-gathering   pattern=pipeline
    Step 2: architecture-design      pattern=pipeline
  Stage 2: implementation-review     (last stage)
    Step 1: code-and-review-loop     pattern=producer_reviewer (max 3)
  ```
- **Agents:** `@sso-researcher`, `@sso-planner`, `@go-developer`, `@qa-reviewer`
- **Artifacts:** `_workspace/sso-integration/{research.md, plan.md, qa_verdict.json}`, `src/auth/*.go`
- **Reference example:** `references/examples/full-bundle/sso-style.md`

### Scenario B: Large-scale Code Migration (single stage, supervisor)

- **Utterance:** "Migrate Python 2 → 3. Process 80 files in bulk."
- **Mode:** New Build
- **Pattern selection rationale:** N homogeneous tasks dynamically batched at runtime → supervisor (main claims tasks.md).
- **Stage/Step structure:**
  ```
  Stage 1: python3-migration
    Step 1: batch-migrate    pattern=supervisor    active agents: [@migrator-1, @migrator-2, @migrator-3]
    Step 2: integration-test pattern=pipeline       active agents: [main]
  ```
- **Agents:** `@migration-supervisor` (task registration), `@migrator-{1..N}` (worker pool)
- **Artifacts:** `_workspace/python3-migration/tasks.md`, migrated files, `final/migration_report.md`
- **Reference example:** `references/examples/team/03-supervisor.md`

### Scenario C: Content Creation + Review Loop (single stage, producer_reviewer)

- **Utterance:** "Draw one webtoon episode. With an artist-editor loop."
- **Mode:** New Build
- **Pattern selection rationale:** Single deliverable + quality gate repetition (PASS/FIX/REDO).
- **Stage/Step structure:**
  ```
  Stage 1: webtoon-episode
    Step 1: produce-and-review   pattern=producer_reviewer (max 3)
  ```
- **Agents:** `@webtoon-artist`, `@webtoon-reviewer`
- **Artifacts:** `_workspace/webtoon-episode/panels/*.png`, `review_report.md`, `final/episode.md`
- **Reference example:** `references/examples/team/02-producer-reviewer.md`

### Scenario D: Parallel Research + Integrated Report (single stage, fan_out_fan_in)

- **Utterance:** "Investigate 4 competitors simultaneously and create an integrated report."
- **Mode:** New Build
- **Pattern selection rationale:** N independent investigations in parallel + integration step.
- **Stage/Step structure:**
  ```
  Stage 1: competitor-research
    Step 1: parallel-scan   pattern=fan_out_fan_in   active agents: [@official, @media, @community, @background]
    Step 2: synthesize      pattern=pipeline          active agents: [@report-writer]
  ```
- **Agents:** `@official`, `@media`, `@community`, `@background`, `@report-writer`
- **Artifacts:** `_workspace/competitor-research/{task_*.json, final/research_report.md}`
- **Reference example:** `references/examples/team/01-fan-out-fan-in.md`

### Scenario E: Incident Analysis (handoff + persistence)

- **Utterance:** "Analyze a production DB timeout. 100 GB of logs available."
- **Mode:** New Build
- **Pattern selection rationale:** Next specialist dynamically determined based on analysis results (handoff) + must support interruption and resume for large log volumes (persistence).
- **Stage/Step structure:**
  ```
  Stage 1: incident-resolution
    Step 1: triage            pattern=handoff           active agents: [@incident-triage]
    Step 2: targeted-fix      pattern=producer_reviewer active agents: [dynamically determined — handoff_chain]
  ```
- **Agents:** `@incident-triage`, `@db-fixer`, `@network-fixer`, `@app-fixer`
- **Artifacts:** `_workspace/incident-resolution/{handoff_chain, final/incident_report.md}`, checkpoint.json `handoff_chain` tracking
- **Reference example:** `references/examples/team/05-handoff-persistence.md`

### Scenario F: Full-stack Feature Development (hierarchical)

- **Utterance:** "Add a payment module. Frontend, backend, and DB in parallel."
- **Mode:** New Build
- **Pattern selection rationale:** Heterogeneous teams (frontend, backend, DB) + 2-level delegation (team lead → worker).
- **Stage/Step structure:**
  ```
  Stage 1: payment-feature       (user approval gate: required — design review)
    Step 1: cross-team-design    pattern=hierarchical   active agents: [@frontend-team-lead, @backend-team-lead]
    Step 2: parallel-implement   pattern=hierarchical   active agents: [@ui-designer, @state-engineer, @api-designer, @db-engineer]
  Stage 2: integration-validate
    Step 1: cross-check          pattern=pipeline       active agents: [@project-architect]
  ```
- **Agents:** `@project-architect` (overall design + validation), 2 team leads, 4 workers
- **Artifacts:** `_workspace/payment-feature/{00_architecture.md, frontend/, backend/, final/integration_report.md}`
- **Reference example:** `references/examples/team/04-hierarchical.md`

### Scenario G: Add Security Validation Stage to Existing Harness (extension mode)

- **Utterance:** "Add a security validation Stage to the existing SSO harness. After QA."
- **Mode:** Existing Extension
- **Classification (expansion-matrix.md):** "Stage/Step Addition" — number of Stages increases (2 → 3).
- **Phases executed:** Phase 2 (workflow.md redesign) + Phase 3 (add `@security-auditor` agent) + Phase 5 (orchestrator modification) + Phase 6-6 (resume flow test).
- **Change result:**
  ```
  Stage 1: research-plan         (existing)
  Stage 2: implementation-review (existing)
  Stage 3: security-audit        (new, user approval gate: required)
    Step 1: vulnerability-scan   pattern=fan_out_fan_in
    Step 2: pen-test             pattern=pipeline
  ```
- **GEMINI.md change log entry is required.**
- **Reference:** `references/expansion-matrix.md` Case D.

### Scenario H: Partial Re-run of Previous Analysis Results (operations/partial re-run)

- **Utterance:** "Regenerate only plan.md from last week's SSO analysis. Keep research as-is."
- **Mode:** Operations (partial re-run)
- **Phase 0 branch:** `checkpoint.json status: "completed"` found → partial re-run mode.
- **Processing:**
  1. Confirm scope of impact with the user (`ask_user`).
  2. Preserve `research.md` in `_workspace/sso-integration/`, delete `plan.md`.
  3. Roll back checkpoint.json to `current_stage: "research-plan"`, `current_step: "architecture-design"`, `status: "in_progress"`.
  4. Re-run from Step 2. Decide whether to re-run subsequent Stages after impact analysis.
- **Reference:** `references/orchestrator-template.md` Step 0 (resume vs partial vs new) + `references/evolution-protocol.md`.

---

## 3. Non-trigger Utterances (false-positive prevention)

The following utterances **do not invoke gemini-harness**. Respond directly or call another skill.

| Utterance | Reason | Handling |
|-----------|--------|----------|
| "Fix this function bug" | Single code fix — no harness needed | Direct code edit |
| "How do I use channels in Go?" | Simple question | Direct response |
| "Run the tests once" | Single command | `run_shell_command` directly |
| "Edit just one item in tasks.md" | Single edit of existing artifact | `write_file` directly (unless the main agent is responsible for updates, in which case use the orchestrator) |
| "Fix one line in the orchestrator code" | Single edit | Edit directly. If the flow changes, enter operations mode (`evolution-protocol.md`) |

> **Borderline utterance (ambiguous):** "Add one agent" — adding a single agent enters **extension mode** (only Phases 3·4·5 executed). Determine Phases using the expansion-matrix.md matrix.

---

## 4. Phase Application Guide

| Mode | Phases executed | Key artifacts |
|------|----------------|---------------|
| New Build | Phase 1 ~ Phase 6 (full) | `.gemini/agents/*.md`, `.gemini/skills/{orchestrator}/SKILL.md`, `GEMINI.md`, `_workspace/_schemas/`, workflow.md, findings.md, tasks.md, checkpoint.json |
| Existing Extension | Determined by expansion-matrix.md matrix (typically Phase 2·3·5·6-6) | Changed files only + `GEMINI.md` change log |
| Operations/Maintenance | Phase 0 → evolution-protocol.md | Audit report + drift corrections |
| Partial Re-run | Phase 0 (checkpoint rewind) → from Phase 2 | Affected artifacts only |

> **Common requirements (all modes):** Regardless of mode: (1) Enter Plan Mode (except yolo), (2) Phase 0 status audit, (3) Zero-Tolerance failure protocol (max 2 retries (3 total) → Blocked + ask_user), (4) Stage·Step naming convention validation.

---

## 5. When There Is No Match

If none of the 8 scenarios closely matches the domain:

1. **Pattern decomposition:** Draw the dependency graph of the task and match to one of the 7 core patterns (parallel/sequential/loop/dynamic assignment/heterogeneous delegation/dynamic routing).
2. **Stage boundaries:** Set Stage boundaries at points where user approval is needed.
3. **Combining similar scenarios:** For example, serially combine scenarios: "parallel research (D) → SSO implementation (A)".
4. **Agent design:** Apply the interaction style + tool mapping from `references/agent-design-patterns.md`.
5. **When uncertain, use ask_user.** Do not guess the harness structure — confirm with the user.
