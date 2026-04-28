# Skill Writing Guide

A detailed writing guide for improving the quality of skills created in the harness. A supplementary reference for `SKILL.md` Phase 4 (Creating Specialized Skills and Orchestrators). Provides a writing style tailored to the Gemini CLI sub-agent orchestration environment.

---

## Table of Contents

0. [Skill Directory Structure](#0-skill-directory-structure)
1. [Description Writing Patterns](#1-description-writing-patterns)
2. [Body Writing Style](#2-body-writing-style)
3. [Output Format Definition Patterns](#3-output-format-definition-patterns)
4. [Example Writing Patterns](#4-example-writing-patterns)
5. [Progressive Disclosure Pattern](#5-progressive-disclosure-pattern)
6. [Script Bundling Decision Criteria](#6-script-bundling-decision-criteria)
7. [Data Brokering & Coordination Patterns (Gemini CLI Specific)](#7-data-brokering--coordination-patterns-gemini-cli-specific)
8. [Data Schema Standards](#8-data-schema-standards)
9. [What Not to Include in a Skill](#9-what-not-to-include-in-a-skill)

---

## 0. Skill Directory Structure

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown body
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for repetitive/deterministic tasks
    ├── references/ - Reference documents loaded conditionally
    └── assets/     - Files used in output (templates, images)
```

- `scripts/` — Pre-bundle scripts that agents commonly write. Execute directly with `run_shell_command`.
- `references/` — Separate out detailed content that is not frequently triggered. Agents conditionally load with `read_file`.
- `assets/` — Static files such as templates and images used in output.

---

## 1. Description Writing Patterns

The description is the **only trigger mechanism** for a skill. The Gemini CLI trigger router decides whether to use a skill based solely on the `name` + `description` in `.gemini/skills/*/SKILL.md`.

### 1-1. Understanding the Trigger Mechanism

Gemini tends not to invoke a skill for simple tasks that can be easily handled with basic tools. A simple request like "read this PDF" may not trigger even with a perfect description. **The more complex, multi-step, and specialized the task**, the higher the probability of triggering a skill.

### 1-2. Writing Principles

1. Describe both **what the skill does + the specific trigger situation**.
2. Specify **boundary conditions** that distinguish similar but should-not-trigger cases.
3. Be slightly **"pushy"** — compensates for the trigger router's tendency to be conservative.
4. **Follow-up action keywords** (re-run, modify, supplement, update, partial re-run) must be included. Without them, the skill effectively becomes dead code after the first execution.

### 1-3. Good Examples

```yaml
description: "Performs all PDF operations including reading PDF files, extracting text
  and tables, merging, splitting, rotating, watermarking, encrypting, decrypting, OCR,
  and more. Use this skill whenever a .pdf file is mentioned or a PDF output is
  requested. Especially useful when conversion, editing, or analysis is needed rather
  than a simple 'read' request. Also use this skill when modifying, re-extracting, or
  regenerating a previously processed PDF."
```

```yaml
description: "All spreadsheet operations including adding columns, formula calculations,
  formatting, charts, and data cleaning for Excel, CSV, and TSV files. Use this skill
  whenever the user mentions a spreadsheet — even casually ('the xlsx in my downloads
  folder'). Includes updating existing results, recalculating columns, and changing
  sort order."
```

### 1-4. Bad Examples

- `"A skill that processes data"` — Too vague; file type and operation are unclear.
- `"PDF-related tasks"` — No list of specific operations; trigger situation not described.
- `"Performs X"` — Missing follow-up action keywords; the router ignores this skill from the second call onward.

---

## 2. Body Writing Style

### 2-1. Why-First Principle

When an LLM understands the reasoning, it makes correct decisions even in edge cases. Conveying context is more effective than imposing rules.

**Bad example:**
```markdown
ALWAYS use pdfplumber for table extraction. NEVER use PyPDF2 for tables.
```

**Good example:**
```markdown
Use pdfplumber for table extraction. PyPDF2 is specialized for text extraction
and cannot preserve the row/column structure of tables. pdfplumber recognizes
cell boundaries and returns structured data.
```

### 2-2. Generalization Principle

When a problem is found in feedback or test results, generalize at the **principle level** rather than making a narrow fix that only fits a specific example.

**Overfitting fix:**
```markdown
If there is a column named "Q4 Sales", convert that column to a number.
```

**Generalized fix:**
```markdown
If a column name contains keywords that imply numeric values such as "sales",
"amount", or "quantity", convert that column to a numeric type. If conversion
fails, retain the original value.
```

### 2-3. Imperative Tone

Use the imperative form ("do X", "perform X") rather than descriptive forms ("X is done", "X can be done"). A skill is a set of instructions.

### 2-4. Context Economy

The context window is a shared resource. Ask whether every sentence justifies its token cost:
- "Does the agent already know this?" → Remove
- "Will the agent make a mistake without this explanation?" → Keep
- "Is one concrete example more effective than a long explanation?" → Replace with an example

---

## 3. Output Format Definition Patterns

Use in skills where the format of the output matters:

```markdown
## Report Structure
Follow this template exactly:

# [Title]
## Summary
## Key Findings
## Recommendations
```

Keep format definitions concise, but including **actual examples** is more effective. If a sub-agent's output must be automatically parsed by the orchestrator (main agent), fix the format specification strictly as a JSON schema or YAML.

---

## 4. Example Writing Patterns

Examples are more effective than long explanations:

```markdown
## Commit Message Format

**Example 1:**
Input: Add JWT token-based user authentication
Output: feat(auth): implement JWT-based authentication

**Example 2:**
Input: Fix bug where password visibility button on login page doesn't work
Output: fix(login): fix password visibility toggle button
```

**Conditions for a good example:**
- Input and output are presented as a **pair**
- At least 1 boundary case or error case is included
- Domain-specific terms actually appear

---

## 5. Progressive Disclosure Pattern

Keep the `SKILL.md` body to **500 lines or fewer**, and separate detailed references, large data schemas, and domain-specific knowledge into files under `references/`. Guide the agent to load those files with `read_file` only when needed.

### 5-1. Pattern 1: Domain Separation

```
bigquery-skill/
├── SKILL.md (overview + domain selection guide)
└── references/
    ├── finance.md   (revenue, billing metrics)
    ├── sales.md     (opportunities, pipeline)
    └── product.md   (API usage, features)
```

If the user asks about revenue, only `finance.md` is loaded.

### 5-2. Pattern 2: Conditional Detail

```markdown
# DOCX Processing

## Document Creation
Create a new document with docx-js. → See [DOCX-JS.md](references/docx-js.md).

## Document Editing
For simple edits, modify the XML directly.
**If tracked changes are needed**: See [REDLINING.md](references/redlining.md).
```

### 5-3. Pattern 3: Large Reference File Structure

Reference files over 300 lines should include a table of contents at the top:

```markdown
# API Reference

## Table of Contents
1. [Authentication](#authentication)
2. [Endpoint List](#endpoint-list)
3. [Error Codes](#error-codes)
4. [Rate Limits](#rate-limits)

---

## Authentication
...
```

---

## 6. Script Bundling Decision Criteria

Observe agent transcripts during test runs. If the following patterns appear, they are candidates for bundling.

| Signal | Action |
|---|---|
| Same helper script created in 3 out of 3 tests | Bundle in `scripts/` |
| Same `pip install` / `npm install` run every time | Explicitly state dependency installation step in the skill |
| Same multi-step approach repeated every time | Describe as a standard procedure in the skill body |
| Same workaround applied after similar errors every time | Describe the known issue and fix in the skill |

Bundled scripts must undergo **execution testing**. Confirm the actual execution result with `run_shell_command` before including in the skill.

---

## 7. Data Brokering & Coordination Patterns (Gemini CLI Specific)

Skills are written with the premise that the main agent acts as a **Data Broker** in the Gemini CLI environment. Since direct communication between sub-agents is not possible, skills follow these principles.

### 7-1. Standardize Outputs

Strictly define the files generated by sub-agents to have a **structure that is easy for other agents or the main agent to read** (MD, JSON). Free-form output makes orchestration difficult.

### 7-2. Completion and Status Reporting (Completion Signals)

The method by which a skill reports its execution result to the orchestrator.

1.  **Atomic status reporting (Thread-safe):** Agents running in parallel do not directly modify `tasks.md`; instead, they report by creating a `_workspace/tasks/task_{agent}_{id}.json` file.
2.  **Dynamic handoff:** Used when a case falls outside one's area of expertise or when an additional specialist is needed.
    - **Format:** `[NEXT_AGENT: @expert-name] Reason: {specific reason}`
    - **Example:** `[NEXT_AGENT: @security-patcher] Reason: An authentication vulnerability was discovered during logic analysis and requires specialized patching.`
3.  **Visibility:** All intermediate steps are updated in real time in the [Key Insights] section of `findings.md`.

### 7-3. External Input via `ask_user`

Do not guess on ambiguous instructions or data conflicts. Explicitly state in the skill body "if X is uncertain, confirm with `ask_user`" to fix the user intervention point.

### 7-4. Procedural Skills Are Assumed to Be Invoked via `activate_skill`

All sub-agents have `activate_skill` as a common tool. When writing a skill, if it **references or reuses another skill**, specify that skill's name and the point at which it should be called.

### 7-5. Orchestrator Skill Writing Rules (Required, drift prevention)

When writing an orchestrator skill, **do not fall back on a flat "Step 1~N" list**. Always use the Stage (parent issue / Jira Issue) → Step (child issue / Jira Sub-issue) block format. This rule is a mandatory requirement to prevent recurrence of non-standard outputs like `examples/sso-dev-flow`.

| Prohibited | Allowed |
|------|------|
| Flat headers `### Step 0: ...` `### Step 1: ...` | Nested `### Stage 1: {name}` followed by `#### Step 1: {name}` |
| Termination condition as "when QA approves", "when done", "sufficiently" | `verdict=PASS` in `qa_verdict.json`, `status=done` in `task_*.json` |
| No pattern specified or free-form expression ("sequentially") | 7 pattern enum (`pipeline`·`fan_out_fan_in`·`expert_pool`·`producer_reviewer`·`supervisor`·`hierarchical`·`handoff`) |
| Prose narrative in active agent body | Step block field `Active Agents: [@name1, @name2]` |
| Missing user approval gate | Stage block `User Approval Gate: Required / None` explicitly stated |
| Missing maximum iteration count (especially for producer_reviewer) | Step block `Max Iterations: 3` |
| Arbitrary sections like `findings.md` `[Review: Step]` | Standard sections such as `[Key Insights]`·`[Change Requests]`·`[Shared Variables/Paths]` |
| Simply checking off tasks.md items | `_workspace/tasks/task_{agent}_{id}.json` persistence + tasks.md table update |

**Orchestrator SKILL.md Body Required Sections (Checklist):**

- [ ] Virtual team (agent · type · role · output table)
- [ ] Step 0 (Context verification — branching by checkpoint.json status)
- [ ] Step 1 (Initialization — simultaneous creation of workflow.md·findings.md·tasks.md·checkpoint.json 5 files + schema validation step 1)
- [ ] Step 2 (Step execution loop — pattern-based invocation + termination condition check + auto/approval transition)
- [ ] Step 3+ (Pattern-specific special handling — e.g., producer_reviewer loop, supervisor dynamic placement)
- [ ] Error handling (Zero-Tolerance: retry ≤2 → Blocked + ask_user)

**Orchestrator Skill Directory Required Bundle (at creation time):**

Since new orchestrator skills read their own `references/schemas/` at runtime (`gemini-harness` is a meta skill and is not activated at runtime), the following **9 files** must be bundled. The SoT is `gemini-harness/references/schemas/` — copy as-is when creating a new skill.

```
{project}/.gemini/skills/{name}-orchestrator/
├── SKILL.md
└── references/
    └── schemas/
        ├── task.schema.json                    ← copy from gemini-harness/references/schemas/
        ├── checkpoint.schema.json              ← same
        ├── workflow.template.md                ← same
        ├── findings.template.md                ← same
        ├── tasks.template.md                   ← same
        ├── models.md                           ← Model ID SoT (required reference when creating agents)
        ├── agent-worker.template.md            ← Worker agent creation standard
        ├── agent-orchestrator.template.md      ← Orchestrator skill creation standard
        └── agent-state-manager.template.md     ← State management agent creation standard (optional use)
```

> **Bundle Verification:** Step 1.3 reads all 9 files in `references/schemas/` with `read_file`, so a missing file causes an immediate runtime failure. Immediately after skill creation, confirm 9 files exist with `ls .gemini/skills/{name}/references/schemas/`.
> **Update Policy:** When `references/schemas/` in gemini-harness changes, propagate the same change to all derived orchestrator skills (drift prevention). The `_workspace/_schemas/` in an ongoing workspace is a snapshot and should be preserved.

> **Full bundle example (case integrating all outputs for one domain):** See `references/examples/full-bundle/sso-style.md`. A canonical package simultaneously writing all 5 files: orchestrator SKILL.md + workflow.md + findings.md + tasks.md + checkpoint.json.

### 7-6. Flat Step → Stage-Step Migration Guide

Procedure for converting non-standard orchestrator skills written with only flat `Step 0~N` headers (e.g., `examples/sso-dev-flow` style) to the current Stage-Step model. **Directly corresponds to drift items #1 and #2 in `expansion-matrix.md`.**

**Conversion Target Identification (Checklist):**

- [ ] SKILL.md body has 0 `### Stage` headers — only flat Steps exist
- [ ] workflow.md is not used (or replaced by a simple checklist)
- [ ] Termination conditions are in natural language ("QA approval", "when done", "sufficiently")
- [ ] No `_workspace/tasks/task_*.json` persistence (tasks.md directly modified)
- [ ] `references/schemas/` directory is absent

**Migration 6 Steps:**

| Step | Task | Verification | Output |
|------|------|------|--------|
| **M1. Inventory** | Group the flat Steps 0~N in the existing SKILL.md into domain work units. Each group = potential Stage candidate. | Number of groups = number of Stage candidates, each group has ≥ 1 Steps | Draft `migration_plan.md` |
| **M2. Stage Mapping** | Assign Stage names to each group (meaning-based: `gather`·`design`·`validate`). Decompose sub-steps within each group into Steps (≡Tasks). | Stage and Step names match `[a-z][a-z0-9-]*` pattern | Stage-Step mapping table |
| **M3. Pattern Assignment** | Assign 1 of the 7 patterns to each Step (`pipeline`·`fan_out_fan_in`·`expert_pool`·`producer_reviewer`·`supervisor`·`hierarchical`·`handoff`). Free-form expressions ("sequentially") are prohibited. | Passes enum check | Mapping table with pattern column added |
| **M4. Termination Condition Conversion** | Natural language → verifiable predicate. `"QA approval"` → `verdict=PASS in qa_verdict.json`, `"when done"` → `status=done in task_*.json`, `"sufficiently"` → `iterations ≥ N`. | Passes `orchestrator-template.md` Step 1.8 whitelist | Mapping table with verification predicate column added |
| **M5. Write 5 Output Files** | Based on the mapping table, write `workflow.md` + `findings.md` + `tasks.md` + `checkpoint.json`. The new SKILL.md body adopts the `references/orchestrator-template.md` skeleton. | `workflow.md` has 0 missing fields out of 6, passes cycle validation | 5 new files |
| **M6. Bundle schemas/** | Copy the 9 files from `gemini-harness/references/schemas/` to the new skill's `references/schemas/` (task/checkpoint/workflow/findings/tasks schemas + models.md + agent-worker/orchestrator/state-manager templates). | 9 files exist confirmed by `ls .gemini/skills/{new}/references/schemas/` | Bundle complete |

**Example Conversion Table (sso-dev-flow → 5-stage Stage-Step):**

| Existing (Flat) | New (Stage-Step + Pattern) | Termination Condition Conversion |
|------------|--------------------------|---------------|
| `Step 0: Requirements Gathering` | Stage `discover` / Step `gather` (`fan_out_fan_in`) | `task_*.json status=done` 4 items |
| `Step 1: Design Review` | Stage `discover` / Step `design-review` (`producer_reviewer`) | `review_verdict.json verdict=PASS` |
| `Step 2: Implementation` | Stage `build` / Step `implement` (`pipeline`) | `_workspace/{plan}/code/*.go` files exist |
| `Step 3: Pass on QA Approval` | Stage `validate` / Step `qa-loop` (`producer_reviewer`) | `qa_verdict.json verdict=PASS AND iterations ≤ 3` |
| `Step 4: Deployment` | Stage `validate` / Step `deploy` (`pipeline`) | `deployment.log status=success` |

**Backward Compatibility Policy:**

- The existing in-progress `_workspace/` is preserved — applies from new runs after migration.
- If a `_schemas/` directory does not exist in the existing `_workspace/`, do not auto-add (preserving snapshot integrity). Requires user approval before a new run.
- Migration history must be recorded in GEMINI.md change log: `[YYYY-MM-DD] {skill-name}: Flat Step → Stage-Step conversion (M1~M6)`.

**Post-Migration Verification:**

- [ ] All of drift items #1·#2·#3 (flat Step·natural language termination conditions·required fields) in `expansion-matrix.md` pass
- [ ] `orchestrator-template.md` Step 1.8 (schema validation) + Step 1.9 (cycle validation) pass
- [ ] 1 test scenario executes successfully (refer to full-bundle/sso-style.md pattern)

---

## 8. Data Schema Standards

Adhere to the following standard schemas for consistency in data exchange and evaluation between skills.

### 8-1. eval_metadata.json

Metadata for each test case:

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": [
    "The output contains X",
    "A file was created in Y format"
  ]
}
```

### 8-2. grading.json

Assertion-based grading results:

```json
{
  "expectations": [
    {
      "text": "The output contains 'Seoul'",
      "passed": true,
      "evidence": "Confirmed 'Seoul regional data extraction' in step 3"
    }
  ],
  "summary": {
    "passed": 2,
    "failed": 1,
    "total": 3,
    "pass_rate": 0.67
  }
}
```

**Field name note:** The top-level array is `expectations`, and the internal fields must use exactly `text`·`passed`·`evidence` (variations like `items`·`name`·`met`·`details` are prohibited). The harness's Phase 6 validation and section 4 of `skill-testing-guide.md` assume this schema.

### 8-3. timing.json

Execution time and token measurement:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

Save `total_tokens` and `duration_ms` **immediately** from the agent completion notification. This data is only accessible at the moment of notification and cannot be recovered afterward.

### 8-4. findings.md / tasks.md

Shared state files for the Gemini CLI harness. When a skill updates these two files, it must comply with the section specifications in `orchestrator-template.md`.

- `findings.md`: `[Key Insights]`, `[Key Keywords]`, `[Shared Variables/Paths]`, `[Data Conflicts]`, `[Change Requests]`, `[Next Step Guidance]` (use only the sections required by the pattern)
- `tasks.md`: `[ID]`, `[Agent]`, `[Task Description]`, `[Status]`, `[Evidence]`, `[Linked Outputs]`

---

## 9. What Not to Include in a Skill

- Supplementary documents such as `README.md`, `CHANGELOG.md`, `INSTALLATION_GUIDE.md`
- Meta information from the skill creation process (test results, iteration history, commit messages, etc.)
- User-facing documentation — a skill is **a set of instructions for AI agents**.
- General knowledge the agent already knows (language syntax, general CS concepts, etc.)
- Hard-coded values that only fit specific test cases (violates the generalization principle)
