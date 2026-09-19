<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Codex_CLI-Skill-5C5C5C.svg" alt="Codex CLI Skill">
  <img src="https://img.shields.io/badge/Gemini_CLI-Skill-4285F4.svg" alt="Gemini CLI Skill">
  <img src="https://img.shields.io/badge/Patterns-7_Architectures-orange.svg" alt="7 Architecture Patterns">
  <a href="https://github.com/tae2089/harness/stargazers"><img src="https://img.shields.io/github/stars/tae2089/harness?style=social" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/README-EN%20%7C%20KO%20%7C%20JA-lightgrey" alt="i18n"></a>
</p>

# Harness — Subagent Orchestration Meta-Framework

**English** | [한국어](README_KO.md) | [日本語](README_JA.md)

A meta-framework for designing specialist subagent teams in AI coding agents. Generates agent definitions, orchestrator skills, and all runtime scaffolding from a single natural-language domain description.

## Available Skills

| Skill | CLI | Agent Definition | Skills Path |
|-------|-----|-----------------|-------------|
| `codex-harness` | OpenAI Codex CLI | `.codex/agents/{name}.toml` | `.codex/skills/` |
| `gemini-harness` | Google Gemini CLI | `.gemini/agents/{name}.md` | `.gemini/skills/` |

---

## codex-harness (OpenAI Codex CLI)

### Installation

**Personal (global):**
```bash
git clone https://github.com/tae2089/harness.git
cp -r harness/skills/codex-harness ~/.codex/skills/
```

**Team (per-repo):**
```bash
cp -r harness/skills/codex-harness .codex/skills/
```

After installation, say `"build a codex harness"` in a Codex CLI session to confirm `codex-harness` skill auto-triggers.

> **First time?** Check [`references/usage-examples.md`](skills/codex-harness/references/usage-examples.md) first. 8 domain scenarios with trigger phrase mappings and a non-trigger table.

### Core Principles (Codex CLI)

- The main Orchestrator coordinates native Codex subagents and verifies their outputs; no separate agent-team runtime is required.
- Share `.scratch/.tracker` with `to-spec` and `to-issues`. Choose existing issue, new issue, or no issue unless already specified.
- Record meaningful progress, evidence, blockers, and next actions on the selected work record. Resume by checking that record against actual artifacts and tests.
- Close issues only on user request. No mandatory local task database, checkpoint, state CLI, or State Manager is generated.
- Set role-specific models explicitly, with `medium` effort by default. Generate the user's domain/familiarity explanation profile in AGENTS.md.
- Use the minimum permissions needed; operational roles do not automatically receive full access.

### Usage

```text
Build a Codex harness for an SSO authentication project.
```

### Generated Artifacts

```text
{project}/
├── .codex/
│   ├── agents/{name}.toml
│   └── skills/{orchestrator}/
│       ├── SKILL.md
│       └── references/
│           ├── project-policy.md
│           ├── orchestrator-procedures.md
│           └── schemas/models.md
├── .scratch/.tracker                 # Shared publication configuration, when used
└── AGENTS.md
```

---

## gemini-harness (Google Gemini CLI)

### Installation

```bash
gemini skills install https://github.com/tae2089/harness.git --path skills
```

After installation, say `"build a harness"` in a Gemini CLI session to confirm `gemini-harness` skill auto-triggers.

> **First time?** Check [`references/usage-examples.md`](skills/gemini-harness/references/usage-examples.md) first. 8 domain scenarios with trigger phrase mappings and a non-trigger table.

### Core Principles (Gemini CLI)

- **Strict Tool Permission Control:** `tools: ["*"]` is forbidden. All agents require `ask_user` and `activate_skill`. `invoke_agent` for orchestrators/supervisors only.
- **Plan Mode Required:** Use `enter_plan_mode` before new builds and expansions (except yolo mode).
- **Main Agent as Single Broker:** No `SendMessage`/`TeamCreate` API. All collaboration brokered via `_workspace/`.
- **3-Component Structure:** `.gemini/agents/` + `.gemini/skills/` + `GEMINI.md`.

### Usage

```
/gemini-harness build a harness for an SSO authentication project
```

Or trigger naturally:

| Phrase Pattern | Mode |
|----------------|------|
| "build/design/set up a harness", "automate {domain}" | New build |
| "add {feature} to existing harness", "add agent" | Expansion |
| "audit/inspect harness", "sync drift" | Operations/maintenance |
| "re-run/fix/improve previous result" | Operations (partial re-run) |

### Generated Artifacts

```
{project}/
├── .gemini/
│   ├── agents/{name}.md                # Agent definition (role, tools, temperature)
│   └── skills/{orchestrator}/
│       ├── SKILL.md
│       └── references/schemas/
├── _workspace/
│   ├── workflow.md
│   ├── findings.md
│   ├── tasks.md
│   ├── checkpoint.json
│   └── tasks/task_{agent}_{id}.json
└── GEMINI.md
```

---

## Shared: Core Concepts

### Workflow Phases

| Phase | Description |
|-------|-------------|
| Phase 0 | Audit current state and branch by mode (new / expand / operate) |
| Phase 1 | Domain analysis and pattern matching (usage-examples.md scenario matching) |
| Phase 2 | Virtual team design + permission mapping + architecture pattern selection |
| Phase 3 | Agent definition generation |
| Phase 4 | Orchestrator skill generation |
| Phase 5 | Integration and orchestration (workflow.md · findings.md · tasks.md · checkpoint.json init) |
| Phase 6 | Validation (trigger check, Resume, Zero-Tolerance, project manifest registration) |

### 7 Pattern Selection Guide

| Pattern | Best for |
|---------|----------|
| Pipeline | Sequential dependent tasks: design → implement → verify |
| Fan-out/Fan-in | Parallel independent tasks with aggregation |
| Expert Pool | Situational expert selection and invocation |
| Producer-Reviewer | Generate → quality-check loop (PASS/FIX/REDO) |
| Supervisor | Dynamic assignment via tasks.md claim |
| Hierarchical | 2-tier delegation: team lead → worker (heterogeneous domains) |
| Handoff | Dynamic routing to next specialist based on analysis result |

### Naming Convention

Stage/Step names must be deliverable-noun kebab-case (`^[a-z][a-z0-9-]*$`). Placeholders like `main`, `step1`, `task` are blocked by workflow.md schema validation.

### Zero-Tolerance Failure Protocol

Arbitrary skipping is absolutely forbidden. Max 2 retries (3 total) → unresolved → `Blocked` + user confirmation.

---

## Directory Structure

```
harness/
└── skills/
    ├── codex-harness/
    │   ├── SKILL.md
    │   └── references/
    │       ├── usage-examples.md
    │       ├── agent-design-patterns.md
    │       ├── orchestrator-template.md
    │       ├── project-policy.md
    │       ├── orchestrator-procedures.md
    │       ├── team-examples.md
    │       ├── stage-step-guide.md
    │       ├── skill-writing-guide.md
    │       ├── skill-testing-guide.md
    │       ├── qa-agent-guide.md
    │       ├── evolution-protocol.md
    │       ├── expansion-matrix.md
    │       ├── schemas/
    │       │   ├── models.md                     # ⚠️ Model ID source of truth
    │       │   ├── agent-worker.template.toml
    │       │   ├── agent-orchestrator.template.md
    │       │   └── README.md
    │       └── examples/
    │           ├── full-bundle/sso-style.md
    │           ├── team/01~05-*.md
    │           └── step/01~05-*.md
    └── gemini-harness/
        ├── SKILL.md
        └── references/                           # Same structure as codex-harness
```

## Reference Docs

### codex-harness
- `skills/codex-harness/SKILL.md` — Main skill definition + workflow + reference index
- `references/schemas/models.md` — ⚠️ Model ID source of truth + `model_reasoning_effort` selection guide
- `references/schemas/agent-worker.template.toml` · `agent-orchestrator.template.md` — Agent creation standard templates

### gemini-harness
- `skills/gemini-harness/SKILL.md` — Main skill definition + workflow + reference index
- `references/schemas/models.md` — ⚠️ Model ID source of truth
- `references/schemas/agent-worker.template.md` · `agent-orchestrator.template.md` — Agent creation standard templates

### Shared References
- `references/usage-examples.md` — 🚀 8 trigger phrases + mode mapping + non-trigger table + Phase matrix
- `references/agent-design-patterns.md` — 7 patterns detail, agent definition structure, permission mapping
- `references/orchestrator-template.md` — Orchestrator Step 0~5 pseudocode, checkpoint.json schema
- `references/orchestrator-procedures.md` — Error handling decision tree, blocked_protocol, handle_handoff
- `references/team-examples.md` — Pattern-based real-world case index
- `references/stage-step-guide.md` — workflow.md specification, Stage/Step transition protocol
- `references/skill-writing-guide.md` — Skill authoring patterns, data schema standards
- `references/skill-testing-guide.md` — Trigger validation, Resume testing, Zero-Tolerance verification
- `references/qa-agent-guide.md` — QA agent integration consistency verification
- `references/evolution-protocol.md` — Harness evolution, operations/maintenance workflow
- `references/expansion-matrix.md` — Phase selection matrix for existing expansion
- `references/examples/full-bundle/sso-style.md` — Full artifact package canonical example
- `references/examples/team/` · `references/examples/step/` — Pattern-based and structure-based detailed examples
