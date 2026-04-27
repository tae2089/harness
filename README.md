<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Gemini_CLI-Skill-4285F4.svg" alt="Gemini CLI Skill">
  <img src="https://img.shields.io/badge/Patterns-7_Architectures-orange.svg" alt="7 Architecture Patterns">
  <a href="https://github.com/tae2089/harness/stargazers"><img src="https://img.shields.io/github/stars/tae2089/harness?style=social" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/README-EN%20%7C%20KO%20%7C%20JA-lightgrey" alt="i18n"></a>
</p>

# Harness — Subagent Orchestration Meta-Framework for Coding Agents

**English** | [한국어](README_KO.md) | [日本語](README_JA.md)

A meta-framework for designing specialist subagent teams and collaboration skills in Coding Agents (primarily Gemini CLI).

## Overview

Harness is a meta-skill that builds domain-specific agent teams, defines each agent's role and tool permissions, and generates procedure skills and orchestrators. Core outputs are `.gemini/agents/`, `.gemini/skills/`, and `GEMINI.md`. All runtime state is persisted in `_workspace/`.

## Installation

```bash
gemini skills install https://github.com/tae2089/harness.git --path skills
```

After installation, say `"build a harness"` in a Gemini CLI session to confirm `gemini-harness` skill auto-triggers.

> **First time?** Check [`references/usage-examples.md`](skills/gemini-harness/references/usage-examples.md) first. 8 domain scenarios (SSO · migration · content loop · parallel research · incident analysis · full-stack · expansion · partial re-run) with trigger phrase mappings and a non-trigger table for false-positive prevention.

---

## Core Principles

- **7 Architecture Patterns:** Pipeline · Fan-out/Fan-in · Expert Pool · Producer-Reviewer · Supervisor · Hierarchical · Handoff. Composed via Stage (parent issue / Jira Issue) → Step (sub-issue / Jira Sub-issue) hierarchy.
- **Naming Convention Enforcement:** Stage/Step names must be deliverable-noun kebab-case (`^[a-z][a-z0-9-]*$`). Placeholders like `main`, `step1`, `task` are blocked by workflow.md schema validation.
- **Strict Tool Permission Control:** `tools: ["*"]` is forbidden. Every agent requires `ask_user` and `activate_skill`. `invoke_agent` is restricted to orchestrators, Supervisors, and Hierarchical team leads only.
- **Main Agent as Single Broker:** Gemini CLI has no direct inter-subagent communication API (`SendMessage`/`TeamCreate`). All collaboration is brokered by the main agent via `_workspace/findings.md`, `tasks.md`, `checkpoint.json`, and `task_*.json`.
- **3-Component Structure:** `.gemini/agents/` + `.gemini/skills/` + `GEMINI.md`. Slash commands (`.gemini/commands/`) are not created.
- **Plan Mode Required:** `enter_plan_mode` is mandatory for new builds and expansions (except yolo mode).
- **Zero-Tolerance Failure Protocol:** Arbitrary skipping is absolutely forbidden. Max 2 retries (3 total) → unresolved → `Blocked` + `ask_user`.

## Directory Structure

```
harness/
└── skills/
    └── gemini-harness/
        ├── SKILL.md                              # Main skill definition
        └── references/
            ├── usage-examples.md                 # 🚀 8 trigger phrases + mode mapping
            ├── agent-design-patterns.md          # 7 patterns + tool mapping
            ├── orchestrator-template.md          # Orchestrator Step 0~5 pseudocode
            ├── orchestrator-procedures.md        # Error handling · blocked · handoff procedures
            ├── team-examples.md                  # Real-world collaboration case index
            ├── stage-step-guide.md               # Stage-Step workflow specification
            ├── skill-writing-guide.md            # Skill authoring guide
            ├── skill-testing-guide.md            # Skill testing/validation guide
            ├── qa-agent-guide.md                 # QA agent guide
            ├── evolution-protocol.md             # Harness evolution/operations protocol
            ├── expansion-matrix.md               # Phase selection matrix for expansion
            ├── schemas/                          # Runtime schemas + agent templates (SoT)
            │   ├── models.md                     # ⚠️ Model ID source of truth — update here only
            │   ├── agent-worker.template.md      # Worker agent creation standard
            │   ├── agent-orchestrator.template.md # Orchestrator skill creation standard
            │   ├── task.schema.json
            │   ├── checkpoint.schema.json
            │   ├── workflow.template.md
            │   ├── findings.template.md
            │   ├── tasks.template.md
            │   └── README.md
            └── examples/
                ├── full-bundle/sso-style.md      # Full artifact package demo
                ├── team/01~05-*.md               # 5 pattern-based collaboration examples
                └── step/01~05-*.md               # 5 Stage-Step structure examples
                    + test-scenarios.md           # Trigger validation scenarios
```

## Usage

Direct invocation via slash command:

```
/gemini-harness build a harness
/gemini-harness build a harness for an SSO authentication project
```

Or trigger via natural language:

| Phrase Pattern | Mode |
|----------------|------|
| "build/design/set up a harness", "automate {domain}" | New build |
| "add {feature} to existing harness", "add agent" | Expansion |
| "audit/inspect harness", "sync drift" | Operations/maintenance |
| "re-run/fix/improve previous result" | Operations (partial re-run) |

> On receiving a new domain, first match against the 8 scenarios in `references/usage-examples.md` (SSO · migration · content loop · parallel research · incident analysis · full-stack · expansion · partial re-run). The non-trigger table prevents false positives.

## Workflow Phases

| Phase | Description |
|-------|-------------|
| Phase 0 | Audit current state and branch by mode (new / expand / operate) |
| Phase 1 | Domain analysis and pattern matching (usage-examples.md scenario matching) |
| Phase 2 | Virtual team design + tool permission mapping + architecture pattern selection |
| Phase 3 | Subagent definition generation (`.gemini/agents/{name}.md`) |
| Phase 4 | Procedure skill generation (`.gemini/skills/{name}/SKILL.md`) |
| Phase 5 | Integration and orchestration (workflow.md · findings.md · tasks.md · checkpoint.json init) |
| Phase 6 | Validation and testing (trigger verification, Resume, Zero-Tolerance, GEMINI.md registration) |

> Expansion/operations modes use `expansion-matrix.md` / `evolution-protocol.md` to run only the required phases.

## Generated Artifacts

```
{project}/
├── .gemini/
│   ├── agents/{name}.md                # Agent definition (role, tools, temperature)
│   └── skills/{orchestrator}/
│       ├── SKILL.md                    # Orchestrator skill
│       └── references/schemas/         # Schema copies (required bundle)
├── _workspace/
│   ├── _schemas/                       # Runtime schema copies (synced at Step 1.3)
│   ├── workflow.md                     # Stage (parent issue) → Step (sub-issue) declaration
│   ├── findings.md                     # Data broker
│   ├── tasks.md                        # Task board
│   ├── checkpoint.json                 # Resume point (Durable Execution)
│   └── tasks/task_{agent}_{id}.json    # Per-agent artifact metadata
└── GEMINI.md                           # Harness pointer + change history
```

## 7 Pattern Selection Guide

| Pattern | Best for |
|---------|----------|
| Pipeline | Sequential dependent tasks: design → implement → verify |
| Fan-out/Fan-in | Parallel independent tasks with aggregation |
| Expert Pool | Situational expert selection and invocation |
| Producer-Reviewer | Generate → quality-check loop (PASS/FIX/REDO) |
| Supervisor | Dynamic assignment via tasks.md claim |
| Hierarchical | 2-tier delegation: team lead → worker (heterogeneous domains) |
| Handoff | Dynamic routing to next specialist based on analysis result |

## Reference Docs

- `skills/gemini-harness/SKILL.md` — Main skill definition + workflow + reference index
- `references/usage-examples.md` — 🚀 8 trigger phrases + mode mapping + non-trigger table + Phase matrix
- `references/agent-design-patterns.md` — 7 patterns detail, agent definition structure, tool mapping
- `references/orchestrator-template.md` — Orchestrator Step 0~5 pseudocode, checkpoint.json schema
- `references/orchestrator-procedures.md` — Error handling decision tree, blocked_protocol, handle_handoff
- `references/team-examples.md` — Pattern-based real-world case index
- `references/stage-step-guide.md` — workflow.md specification, Stage/Step transition protocol
- `references/skill-writing-guide.md` — Skill authoring patterns, data schema standards, flat-Step → Stage-Step migration
- `references/skill-testing-guide.md` — Trigger validation, Resume testing, Zero-Tolerance verification
- `references/qa-agent-guide.md` — QA agent integration consistency verification
- `references/evolution-protocol.md` — Harness evolution, operations/maintenance workflow
- `references/expansion-matrix.md` — Phase selection matrix for existing expansion
- `references/schemas/models.md` — ⚠️ Model ID source of truth — update here when new models are released
- `references/schemas/agent-worker.template.md` · `agent-orchestrator.template.md` — Agent creation standard templates
- `references/schemas/` — Runtime schema SoT (task · checkpoint · workflow · findings · tasks templates)
- `references/examples/full-bundle/sso-style.md` — Full artifact package canonical example
- `references/examples/team/` · `references/examples/step/` — Pattern-based and structure-based detailed examples
