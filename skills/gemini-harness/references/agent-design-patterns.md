# Subagent Orchestration Design Patterns (Gemini CLI)

## Table of Contents

1. [Orchestration Mode Overview](#execution-mode-orchestration)
2. [Thread-safe Task Board Protocol](#thread-safe-task-board-protocol-preventing-parallel-write-conflicts)
3. [7 Core Architecture Patterns](#7-core-architecture-patterns)
4. [Multi-stage Workflow Composition](#multi-stage-workflow-composition)
5. [Durability Protocol (Durable Execution)](#durability-and-persistence-protocol-durable-execution)
6. [Tool Permission Control and Type Mapping](#tool-permission-control-and-type-mapping-guide)
7. [Data Brokering Protocol](#data-brokering-protocol)
8. [Subagent Interaction Styles](#subagent-interaction-styles)
9. [Agent Separation Criteria](#agent-separation-criteria)
10. [Agent Definition Structure](#agent-definition-structure-gemini-cli-official-format)
11. [Skill vs Agent Distinction](#skill-vs-agent-distinction)
12. [Skill ↔ Agent Connection Methods](#skill--agent-connection-methods)

---

## Execution Mode: Orchestration

In Gemini CLI, the main agent acts as the **orchestrator** and coordinates subagents. Direct communication between subagents is not possible, but high-level collaboration can be achieved through the main agent's **brokering** and shared files.

```
[Main Agent (Orchestrator)]
  ├── Data Brokering (Data Broker / findings.md)
  ├── State Management (Atomic Task Board / tasks.md)
  ├── Persistence Management (Persistence / checkpoint.json)
  └── Shared Workspace (_workspace/{plan_name}/)
        ├── @subagent-A (specialized toolset + creates dedicated task_A.json)
        ├── @subagent-B (specialized toolset + creates dedicated task_B.json)
        └── @subagent-C (specialized toolset + creates dedicated task_C.json)
```

> **Difference from Claude Code:** Claude Code has an "agent team" mode based on `TeamCreate`/`SendMessage`/`TaskCreate` that allows team members to communicate and broadcast directly, but **Gemini CLI does not have this team API**. When communication between team members is needed, the main agent reads artifacts via `read_file` and injects them into the next agent's prompt — a **file brokering** approach. Also, subagent invocation uses the **`invoke_agent` tool**, and when parallel execution is required, the **`wait_for_previous: false`** parameter must be specified to achieve concurrent execution within a single turn. (Background execution of shell commands themselves is separately supported via `run_shell_command`.)

### Orchestration Model Selection Decision Tree

```
Are there 2 or more agents?
├── Yes → Is information exchange between agents needed?
│         ├── Yes → Fan-out/fan-in design with main brokering via findings.md
│         │         (cross-validation, discovery sharing, real-time feedback quality improvement)
│         │
│         └── No → Simple fan-out where main only collects results
│                  (one-pass patterns like produce-validate or expert pool)
│
└── No (1 agent) → Single subagent invocation
              (single agent does not need orchestration)
```

> **Core Principle:** In Gemini CLI, the premise that "the main agent is the sole broker" underlies all patterns. When selecting a pattern, first design "what information must the main agent broker and at what point?"

---

## Thread-safe Task Board Protocol (Preventing Parallel Write Conflicts)

When multiple agents run in parallel (`wait_for_previous: false`), data can be lost if they simultaneously attempt to write to the shared file `tasks.md`. To prevent this, follow these **Atomic Task Management** principles.

### 1. Split Task Artifacts

- **Principle:** Subagents must never directly modify the shared `tasks.md`.
- **Implementation:** Each agent records its task results in a **dedicated individual file** such as `_workspace/tasks/task_{agent_name}_{task_id}.json`.
- **Contents:** Includes task status (`status`), evidence (`evidence`), and artifact path (`path`).

### 2. Sole Aggregator

- **Principle:** The exclusive write authority over `tasks.md` and `checkpoint.json` belongs to the **main agent (orchestrator)**.
- **Workflow:**
  1. Main invokes parallel agents.
  2. Agents each create their own individual task file and exit.
  3. Main scans `_workspace/tasks/` with `list_directory` and reads all individual files.
  4. Main performs an atomic update of `tasks.md` in one operation based on the data read.

---

## 7 Core Architecture Patterns

### 1. Pipeline — Sequentially Dependent Tasks

A flow where the output of the previous stage is used as input to the next stage.

```
[Analyze] → [Design] → [Implement] → [Validate]
```

- **Coordination:** Sequential invocation. After the Nth agent completes, the main summarizes results in `findings.md` → injects into the (N+1)th agent's prompt.
- **Usage Example (orchestrator invocation style):**
  > **Main:** `[Tool: invoke_agent(agent_name="analyst", wait_for_previous=true)]` `@{analyst}`, analyze the requirements and save them to `_workspace/{plan_name}/01_reqs.md`. Use `activate_skill('context7-docs')` if needed to check the latest specs.
  > (After completion)
  > **Main:** `[Tool: invoke_agent(agent_name="coder", wait_for_previous=true)]` `@{coder}`, read `_workspace/{plan_name}/01_reqs.md` and implement while adhering to the [Key Constraints] in `findings.md`. Save results to `_workspace/{plan_name}/02_code.md`.
- **Suitable for:** Novel writing (worldbuilding→characters→plot→writing→editing), design→implementation→validation flows.
- **Note:** Bottlenecks delay the entire pipeline. Design each stage as independently as possible and verify whether each consecutive stage is a "true dependency" required at every point. Choosing pipeline merely for sequential preference misses parallelization opportunities.

### 2. Fan-out/Fan-in — Parallel Investigation and Integration

Independently perform tasks simultaneously and merge results into one.

```
         ┌→ [ExpertA] ─┐
[Distribute] → ├→ [ExpertB] ─┼→ [Integrate]
         └→ [ExpertC] ─┘
```

- **Coordination:** Invoke `@A`, `@B`, `@C` consecutively in a single response turn → each saves artifacts under `_workspace/{plan_name}/` → when main invokes the integration agent, inject all artifact paths into the prompt.
- **Usage Example (orchestrator invocation style):**
  > **Main:** (batch invocation within a single turn)
  >
  > 1. `[Tool: invoke_agent(agent_name="researcher-market", wait_for_previous=false)]` `@{researcher-market}`, research market trends and record them in `_workspace/{plan_name}/mkt.md`.
  > 2. `[Tool: invoke_agent(agent_name="researcher-tech", wait_for_previous=false)]` `@{researcher-tech}`, research technical feasibility and record it in `_workspace/{plan_name}/tech.md`.
  >    (After all complete)
  >    **Main:** `[Tool: invoke_agent(agent_name="strategist", wait_for_previous=true)]` `@{strategist}`, read both `_workspace/{plan_name}/mkt.md` and `_workspace/{plan_name}/tech.md`, resolve any conflicting data noted in the [Data Conflicts] section of `findings.md`, and establish the final strategy.
- **Suitable for:** Comprehensive research (simultaneous investigation of official docs/media/community/background → integration), multi-module development.
- **Note:** The quality of the integration stage determines overall quality. Since discoveries across experts may **conflict**, the main should maintain a [Data Conflicts] section in `findings.md` and instruct the integration agent to resolve it.

### 3. Expert Pool — Situation-based Expert Selection

Select and invoke the most suitable subagent based on the nature of the user's request.

```
[Router] → { ExpertA | ExpertB | ExpertC }
```

- **Coordination:** The main agent classifies input and then invokes only the agent for that domain.
- **Invocation style:** Always `wait_for_previous=true` (sequential). Do not invoke multiple experts simultaneously.
- **Usage Example (orchestrator invocation style):**
  > **Main:** (user request: "React performance improvement")
  > **Main:** `[Tool: invoke_agent(agent_name="perf-expert", wait_for_previous=true)]` `@{perf-expert}`, analyze the current code and identify bottlenecks. `@{security-expert}` is excluded from this task.
- **Suitable for:** Multilingual support (native agents per language), code review (selecting security/performance/architecture experts), technology stack-specific review.
- **Note:** The classification accuracy of the router (main) is critical. If classification is ambiguous, use `ask_user` for clarification, or invoke two experts simultaneously for cross-validation.

### 4. Producer-Reviewer — Quality Assurance Loop

Producer and reviewer loop to refine the output.

```
[Produce] → [Review] → (if issues) → [Produce] re-run
```

- **Coordination:** Main invokes producer → reads artifact and summarizes in `findings.md` → invokes reviewer (inject artifact path) → reads review report and re-invokes producer if there are issues (inject report).
- **Usage Example (orchestrator invocation style):**
  > **Main:** `[Tool: invoke_agent(agent_name="writer", wait_for_previous=true)]` `@{writer}`, write a draft.
  > **Main:** `[Tool: invoke_agent(agent_name="editor", wait_for_previous=true)]` `@{editor}`, review the draft and leave revision suggestions in `_workspace/{plan_name}/edit_notes.md` according to `activate_skill('qa-standard')`.
  > (If review result is 'Fail')
  > **Main:** `[Tool: invoke_agent(agent_name="writer", wait_for_previous=true)]` `@{writer}`, revise the draft incorporating feedback from `_workspace/{plan_name}/edit_notes.md`. (Maximum 2 retries, 3 total)
- **Suitable for:** Webtoons (artist→reviewer→regenerate), high-quality code writing, technical document proofreading.
- **Note:** **A maximum of 2 retries (3 total) is mandatory to prevent infinite loops.** After 3 attempts, if still failing, the main uses `ask_user` to hand the decision to a human.

### 5. Supervisor — Dynamic Task Assignment

The main agent analyzes workload and dependencies at runtime to distribute tasks.

```
         ┌→ [WorkerA]
[Supervisor] ─┼→ [WorkerB]    ← Supervisor dynamically distributes based on status
         └→ [WorkerC]
```

- **Coordination:** State management via `tasks.md`. Main splits the `Todo` list into batches and assigns them to each worker. After worker completion, **verify success via `Evidence` or `qa_report.md`**, then update to `Done` and assign the next batch.
- **Usage Example (orchestrator invocation style):**
  > **Main:** There are 50 migration tasks in `tasks.md`.
  >
  > 1. `[Tool: invoke_agent(agent_name="worker-1", wait_for_previous=false)]` `@{worker-1}`, perform task IDs 1–10.
  > 2. `[Tool: invoke_agent(agent_name="worker-2", wait_for_previous=false)]` `@{worker-2}`, perform task IDs 11–20.
  >    (When completion report arrives)
  >    **Main:** `@{worker-1}`, I have reviewed the artifacts and test logs (`Evidence`). Since they passed, mark them as `Done` and now perform tasks 21–30. **If any task fails, do not skip it — stop immediately and report the solution.**
- **Suitable for:** Large-scale file migration, bulk data processing.
- **Difference from Fan-out:** Fan-out pre-assigns fixed tasks; Supervisor dynamically adjusts while monitoring progress.
- **Note:** Set the delegation unit large enough so the Supervisor (main) does not become a bottleneck (1 file × 100 calls < 10 files × 10 calls).

### 6. Hierarchical Delegation — Recursive Problem Decomposition

Upper-level agent recursively delegates to lower-level agents. Progressively decomposes complex problems.

```
[Overall] → [Team Lead A] → [Worker A1]
                          → [Worker A2]
           → [Team Lead B] → [Worker B1]
```

- **Coordination:** Nested agent invocations with context summary passing. The team lead agent breaks down the instructions it received and re-invokes worker agents.
- **Usage Example (orchestrator invocation style):**
  > **Main:** `[Tool: invoke_agent(agent_name="frontend-lead", wait_for_previous=true)]` `@{frontend-lead}`, oversee the UI system construction.
  > **@{frontend-lead}:** (within its prompt) `[Tool: invoke_agent(agent_name="component-coder", wait_for_previous=false)]` I will instruct `@{component-coder}` to implement the button component and `[Tool: invoke_agent(agent_name="style-coder", wait_for_previous=false)]` `@{style-coder}` to implement the theme system.
- **Suitable for:** Full-stack application development (overall→frontend lead→UI/logic/tests + backend lead→API/DB/tests), complex system architecture design.
- **Note:** **Depth beyond 3 levels increases delay and context loss significantly — keep to 2 levels or fewer.** Team lead agents should summarize worker artifacts for the overall lead, while preserving originals in `_workspace/{plan_name}/{team}/`.

### 7. Handoff — Agent-driven Delegation

Instead of the main deciding all paths in advance, the working agent, after completing its task, recommends **"the most suitable expert for the next step"** to the orchestrator, passing over control.

- **Coordination:** The agent leaves a `[NEXT_AGENT: @expert-name]` keyword and reason for recommendation at the end of its artifact, and the orchestrator parses this to dynamically summon the next agent.
- **Routing Principle:** The agent makes its recommendation by referencing the list of other agents in the project (based on their descriptions).
- **Usage Example (orchestrator invocation style):**
  > **Main:** `[Tool: invoke_agent(agent_name="log-analyzer", wait_for_previous=true)]` `@{log-analyzer}`, analyze the error logs and identify the root cause. If specialized processing is needed, you must leave `[NEXT_AGENT: @{agent-name}] Reason: {specific reason}` at the end of the artifact.
  > (log-analyzer completes, end of artifact: `[NEXT_AGENT: @security-patcher] Reason: Authentication vulnerability found due to missing JWT validation`)
  > **Main:** (after parsing keyword) `[Tool: invoke_agent(agent_name="security-patcher", wait_for_previous=true)]` `@{security-patcher}`, read `_workspace/{plan_name}/log_analysis.md` and patch the identified authentication vulnerability.
- **Suitable for:** Exploratory debugging (log analysis → reproduction attempt → handoff to fix expert), complex support processes.
- **Note:** Circular handoff (A→B→A) infinite loop prevention is mandatory — the orchestrator tracks the call history and does not re-summon an agent that has already executed. If handoff chains reach 3 or more stages, or if the recommended target agent does not exist, hand the decision to the user via `ask_user`. Detection pseudocode: see `references/orchestrator-procedures.md` — "handle_handoff".

---

## Multi-stage Workflow Composition

The 7 basic patterns are **combined at the Step level**. Declaring a Stage-Step structure allows each Step to have an independent pattern, enabling precise multi-stage workflow composition. Details: `references/stage-step-guide.md`.

| Workflow Type                       | Step Composition                                                                                   | Example                                                                    |
| ----------------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **Parallel Collection → Review Loop**   | Stage 1 / Step 1: fan_out_fan_in → Stage 2 / Step 1: producer_reviewer                            | Multilingual translation — parallel translation in 4 languages → native reviewer loop |
| **Sequential Design → Parallel Validation** | Stage 1 / Step 1-N: pipeline → Stage 2 / Step 1: fan_out_fan_in                               | Requirements·design·API design (sequential) → security·performance·compatibility validation (parallel) |
| **Classify → Expert Analysis → Review** | Stage 1 / Step 1: expert_pool, Step 2: pipeline → Stage 2 / Step 1: producer_reviewer          | Issue classification → expert analysis → report review                     |

### Multi-stage Workflow Coordination Points (Gemini CLI)

| Scenario                   | Brokering Strategy                                                                                       | Note                                                                                        |
| -------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **Research + Analysis**    | Merge researcher artifacts into `findings.md` in real time; record conflicting discoveries in [Data Conflicts] section | If the integration agent cannot resolve conflicts, call `ask_user`                   |
| **Design + Implementation + Validation** | Design artifact → inject into implementation agent prompt → implementation result → inject into validation agent prompt | Between each stage, do not **just pass file paths** — extract **key constraints** into `findings.md` and inject them |
| **Supervisor + Worker**    | Synchronize state via `tasks.md`; each worker reads only its assigned tasks                              | Supervisor must partition files so multiple simultaneously assigned workers do not modify the same file |
| **Produce + Validate**     | Produce → validation report (`qa_report.md`) → inject report into prompt for regeneration               | Maximum 2 retries (3 total); exceed → ask_user                                              |

---

## Durability and Persistence Protocol (Durable Execution)

All orchestration workflows must have **persistence** to handle network failures, timeouts, and model errors.

### 1. Checkpoint Protocol (`checkpoint.json`)

The orchestrator creates or updates `_workspace/checkpoint.json` upon completion of each agent task.

- **Required data:**
  - `last_successful_step`: The step number or agent name of the last successfully completed step.
  - `tasks_snapshot`: A summary of the current state data from `tasks.md`.
  - `shared_variables`: Key constants or variable values shared between agents.
- **Benefit:** Even if execution is interrupted, the checkpoint can be detected at Step 0 to **resume immediately from the point of failure**.

### 2. Idempotency Guarantee Principles

- **Duplicate prevention:** Each agent checks at the start of execution whether its target artifact file already exists.
- **Status-based skip:** If the content is current and no modifications are needed, the agent does not perform the task and immediately sends a completion signal to prevent token waste.
- **Atomic write:** `tasks.md` is not updated to `Done` until the file write is complete.

---

## Tool Permission Control and Type Mapping Guide

When defining agents, strictly restrict the `tools` array to improve stability and efficiency. **Using `tools: ["*"]` is strictly prohibited** — assign only tools optimized for the role.

> **Common rules (required for all agents):**
>
> - `ask_user`: When instructions are ambiguous, parameters are missing, or data conflicts arise — do not guess; query the user for confirmation.
> - `activate_skill`: Required to load and execute procedural skills (methodologies, checklists, protocols) under `.gemini/skills/` at runtime. In principle, no agent exists that does not call a skill.

### Standard Tool Sets by Agent Type

| Agent Type    | Core Role                         | Recommended Tool Set                                                                                                                                                    | Related MCP/Built-in         |
| :------------ | :-------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------- |
| **Analyst**   | Information gathering, analysis, research | `ask_user`, `activate_skill`, `read_file`, `read_many_files`, `list_directory`, `grep_search`, `google_web_search`, `web_fetch`                                | Search, Browser, Context7    |
| **Architect** | Structure design, planning        | `ask_user`, `activate_skill`, `read_file`, `list_directory`, `glob`, `grep_search`, `enter_plan_mode`, `exit_plan_mode`                                                 | Planning, CCG                |
| **Coder**     | Code writing, modification, refactoring | `ask_user`, `activate_skill`, `read_file`, `write_file`, `replace`, `run_shell_command` (format/lint)                                                             | Filesystem, Lang-specific    |
| **Reviewer**  | Quality review, testing, QA       | `ask_user`, `activate_skill`, `read_file`, `read_many_files`, `grep_search`, `run_shell_command` (test execution; use background option for long-running processes)     | Testing, Linter              |
| **Operator**  | Infrastructure management, deployment, CICD | `ask_user`, `activate_skill`, `run_shell_command`, `k8s_*`, `terraform_*`                                                                                    | K8s, Terraform, CLI          |

### Special Purpose Tools

Special tools confirmed in Gemini CLI. Do not grant to general worker agents — allow selectively only for roles that need them.

| Tool                | Purpose                                         | Recommended Agents                                                                           |
| ------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `invoke_agent`      | Invoke subagents                                | Orchestrator, Supervisor, Hierarchical team lead (mid-level) only — prohibited for general workers |
| `save_memory`       | Persist key information across sessions         | Orchestrator (as checkpoint supplement)                                                      |
| `write_todos`       | Built-in to-do list management (lightweight alternative to `tasks.md`) | Orchestrator for single-agent tasks                              |
| `get_internal_docs` | Query Gemini CLI internal documentation         | Analyst, Architect                                                                           |

> **Note:** `save_memory` does **not replace** file-based persistence via `checkpoint.json`. Files are more reliable when resuming a session. Use `save_memory` only for small amounts of data that are burdensome to manage as files, such as agent personas and shared constants.

### MCP Tool Mapping Examples

- **GitHub specialist agent:** Assign only `mcp_github_*` tools for dedicated issue management and PR handling.
- **Infrastructure specialist:** Restrict permissions to `mcp_kubernetes_*` or `mcp_terraform_*` tools.
- **Documentation specialist:** Assign primarily `web_fetch` and `read_file` for knowledge base construction.

### temperature / max_turns Recommendations

| Role                    | temperature | max_turns | Reason                                       |
| ----------------------- | ----------- | --------- | -------------------------------------------- |
| Analyst, Architect      | 0.3 ~ 0.5   | 10 ~ 15   | Moderate explorability, needs iterative evidence gathering |
| Coder                   | 0.2         | 15 ~ 20   | Deterministic output, allows repeated revisions |
| Reviewer (QA Inspector) | 0.2         | 8 ~ 10    | Reproducibility and consistency are top priority |
| Operator                | 0.1 ~ 0.2   | 6 ~ 8     | Low variability, safety first                |

### Model Selection Guide

| Agent Role | Model Tier | Where to Check the Actual ID |
|------------|------------|------------------------------|
| Orchestrator, Architect | **pro tier** | `references/schemas/models.md` (SoT) |
| Coder, Analyst, Reviewer, Operator | **flash tier** | `references/schemas/models.md` (SoT) |

> **Important:** Do not hardcode model IDs directly in code. Always confirm by reading `_workspace/_schemas/models.md` with `read_file` before using. Gemini model IDs change periodically, and incorrect IDs cause runtime errors.
> **Reason:** Workers have a narrow scope and are called frequently. Flash has a speed and cost advantage over Pro. Only the orchestrator and Architect use Pro.

---

## Data Brokering Protocol

The main agent brokers **discoveries** between subagents in real time.

1. **Real-time recording:** Each time the main agent reads intermediate results, it summarizes key insights in `_workspace/findings.md`.
2. **Context injection:** When invoking the next subagent, inject "Key findings so far: [contents of findings.md]" into the prompt.
3. **State synchronization:** Instruct all agents to read `_workspace/tasks.md` on every invocation to understand the full context.
4. **Conflict brokering:** If artifacts from agents conflict, note them explicitly in the [Data Conflicts] section of `_workspace/findings.md` → request adjudication from a mediator expert (typically the Reviewer).

## Subagent Interaction Styles

In addition to structural patterns, the orchestrator can choose the **style** of interaction with agents to maximize efficiency.

| Style                            | Invocation Method  | Characteristics                                                              | Suitable When                                                          |
| :------------------------------- | :----------------- | :--------------------------------------------------------------------------- | :--------------------------------------------------------------------- |
| **Full Delegation**              | `invoke_agent`     | The subagent completes the task end-to-end (including file creation).        | Independent hands-on work such as coding, research, test execution.    |
| **Expert Consultation**          | `invoke_agent`     | Returns only **"analysis opinions"** or **"checklists"** instead of artifacts. | Architecture review, security checks, implementation strategy planning. |
| **Manual Intervention**          | `@agent_name`      | The user directly summons a specific agent from the terminal.                | When you want to manually re-verify only a specific stage during harness execution. |

### Advanced Tips by Style

- **Using the consultative style:** Before the main agent writes code directly, summon `@architect` and ask it to "just give an opinion on which structure would be best." The main then records that opinion in `findings.md` and handles coding itself, minimizing context loss.
- **Guiding manual intervention:** If the orchestrator cannot resolve an error, guide it to suggest to the user: "Would you like to call `@agent-name` directly to check detailed logs?"
- **The power of tool isolation:** Consultative-style agents can be designed with `write_file` permission removed and only `read_file` granted, so they provide only "knowledge" without accidentally touching code.

---

## Agent Separation Criteria

Four criteria for deciding whether to consolidate into a single agent or separate into distinct agents.

| Criterion        | Separate                                                        | Consolidate                          |
| ---------------- | --------------------------------------------------------------- | ------------------------------------ |
| **Specialization** | Separate if domains (domain/language/stack) differ              | Consolidate if domains overlap       |
| **Parallelism**  | Separate if independently executable (reduces delay via parallel invocation) | Consider consolidation if sequentially dependent |
| **Context**      | Separate if context burden is large (each reads only a small scope) | Consolidate if lightweight and fast  |
| **Reusability**  | Separate if used by other teams/scenarios                       | Consider consolidation if only used by this team |

**Additional Gemini CLI considerations:** Each separation increases the main agent's brokering burden (requires updating `findings.md` before and after each agent invocation). Check whether the benefit of separation outweighs the brokering overhead. When in doubt, start with a consolidated agent and separate when a reuse need arises.

---

## Agent Definition Structure (Gemini CLI Official Format)

> **When creating an agent file:** Do not use the inline example below — instead, read **`_workspace/_schemas/agent-worker.template.md`** (for workers) or **`agent-orchestrator.template.md`** (for orchestrators) with `read_file`, substitute variables, and create. Model IDs must be confirmed in **`_workspace/_schemas/models.md`** before use — no arbitrary guessing.

```markdown
---
name: agent-name
description: "1-2 sentence role description. List trigger keywords. Also specify that follow-up tasks (revision/supplementation/re-execution) should use this agent."
kind: local
model: "{role tier ID confirmed from models.md}"  # ← must reference _workspace/_schemas/models.md
tools:
  - ask_user
  - activate_skill
  - read_file
  # … add only the minimum tools for the role
temperature: 0.3
max_turns: 10
---

# Agent Name — One-line Role Summary

You are a [role] expert in [domain].

## Core Role

1. Role 1
2. Role 2

## Operating Principles

- Principle 1
- Principle 2

## Input/Output Protocol (Data Broker-based)

- **Input briefing:** Read the `findings.md` summary and assigned task from `tasks.md` injected into the prompt at invocation.
- **Artifact path:** `_workspace/{plan_name}/{step}/{agent}-result.md` (or the path specified by the orchestrator).
- **Format:** [File format, section structure, required fields]
- **Completion signal:** After recording the artifact, output the "completion keyword" specified in the prompt.

## Error Handling

- Missing required input → request supplementation via `ask_user`.
- Data conflict discovered → add to [Data Conflicts] in `findings.md` and indicate that progress cannot continue.
- Timeout/retry limit reached → report failure to the orchestrator with detailed logs.

## Relationships with Other Agents

- Upstream: [Which agent's artifacts does this depend on?]
- Downstream: [Which agent consumes this artifact?]
- Note: Direct communication between subagents is not possible. All collaboration goes through `findings.md`.
```

> **Note:** The "Team Communication Protocol (SendMessage)" section of Claude Code agent definitions does not exist in Gemini CLI. Instead, specifying file paths, completion signals, and briefing methods in the "Input/Output Protocol" serves the same purpose.

---

## Skill vs Agent Distinction

| Aspect          | Skill                                                              | Agent                                          |
| --------------- | ------------------------------------------------------------------ | ---------------------------------------------- |
| **Definition**  | Procedural knowledge + tool bundle                                 | Expert persona + behavioral principles         |
| **Location**    | `.gemini/skills/{name}/SKILL.md`                                   | `.gemini/agents/{name}.md`                     |
| **Trigger**     | User request keyword matching, or agent invokes via `activate_skill` | Orchestrator explicitly invokes via `@{name}` |
| **Size**        | Small to large (workflow)                                          | Small (role definition)                        |
| **Purpose**     | "**How** to do it"                                                 | "**Who** does it"                              |
| **State**       | Stateless (procedure re-executed on each call)                     | Persona and principles fixed; context maintained within session |

**Summary:** A skill is a **procedural guide** that an agent references when performing a task, and an agent is a **specialist role definition** that utilizes skills.

---

## Skill ↔ Agent Connection Methods

Three ways for an agent to utilize a skill.

| Method                   | Implementation                                                                                              | Suitable When                                                       |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| **activate_skill call**  | Specify in the agent prompt: "For this procedure, invoke and execute `activate_skill('{skill-name}')`"      | The skill is an independent workflow and the user can call it directly |
| **Inline in prompt**     | Directly include the skill content in the agent definition body                                             | The skill is short (50 lines or fewer) and **exclusive** to this agent |
| **Reference load**       | Load `.gemini/skills/{skill}/references/*.md` with `read_file` as needed                                   | The skill content is large and only needed **conditionally**         |

**Recommendations:**

- High reusability → `activate_skill`
- Exclusive → inline
- Large + conditional → `read_file` reference load

**Principle:** All agent definitions include `activate_skill` in the `tools` array. A purely persona-based agent that never calls a skill does not exist in principle (because behavioral principles, protocols, and checklists should almost always be separated into skills to improve reusability and maintainability).
