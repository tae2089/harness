# Skill Writing Guide

A detailed writing guide for improving the quality of skills created in the harness. Supplementary reference for `SKILL.md` Phase 4 (specialized skill and orchestrator creation). Provides a writing style tailored to the Codex CLI sub-agent orchestration environment.

---

## Table of Contents

0. [Skill Directory Structure](#0-skill-directory-structure)
1. [Description Writing Patterns](#1-description-writing-patterns)
2. [Body Writing Style](#2-body-writing-style)
3. [Output Format Definition Patterns](#3-output-format-definition-patterns)
4. [Example Writing Patterns](#4-example-writing-patterns)
5. [Progressive Disclosure Pattern](#5-progressive-disclosure-pattern)
6. [Script Bundling Decision Criteria](#6-script-bundling-decision-criteria)
7. [Coordination and Generated Skills](#7-coordination-and-generated-skills)
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
    ├── scripts/    - executable code for repetitive/deterministic tasks
    ├── references/ - reference documents loaded conditionally
    └── assets/     - files used in output (templates, images)
```

- `scripts/` — pre-bundle scripts that agents commonly write. Executed directly from the shell.
- `references/` — separates detailed content that is not frequently triggered. Agents load conditionally via shell `cat`.
- `assets/` — static files such as templates and images used in output.

---

## 1. Description Writing Patterns

The description is the **only trigger mechanism** for a skill. The Codex CLI trigger router looks only at the `name` + `description` from `.codex/skills/*/SKILL.md` to decide whether to use a skill.

### 1-1. Understanding the Trigger Mechanism

Codex tends not to invoke a skill for simple tasks that can be handled easily with basic tools. A simple request like "read this PDF" may not trigger even with a perfect description. The **more complex, multi-step, and specialized a task**, the higher the probability of triggering a skill.

### 1-2. Writing Principles

1. Describe **both what the skill does and the specific trigger situations**.
2. Specify **boundary conditions** that distinguish similar cases that should not trigger the skill.
3. Be slightly **"pushy"** — to compensate for the trigger router's tendency toward conservative judgment.
4. Always include **follow-up action keywords** (re-run, modify, revise, update, partial re-run). Without them, the skill effectively becomes dead code after the first execution.

### 1-3. Good Examples

```yaml
description: "Performs all PDF operations including reading PDF files, extracting text
  and tables, merging, splitting, rotating, watermarking, encrypting, decrypting,
  and OCR. When a .pdf file is mentioned or a PDF output is requested, this skill
  MUST be used. Especially useful when conversion, editing, or analysis is needed
  rather than a simple 'read' request. Also MUST be used when modifying, re-extracting,
  or regenerating a previously processed PDF."
```

```yaml
description: "All spreadsheet operations including adding columns, formula calculations,
  formatting, charts, and data cleaning for Excel, CSV, and TSV files. Use this skill
  whenever a user mentions a spreadsheet — even casually ('the xlsx in the downloads
  folder'). Also covers updating existing results, recalculating columns, and changing
  sort order."
```

### 1-4. Bad Examples

- `"A skill that processes data"` — too vague, file type and task are unclear.
- `"PDF-related tasks"` — no enumeration of specific actions, trigger situations not described.
- `"Performs X"` — missing follow-up action keywords, so the router ignores it from the second call onward.

---

## 2. Body Writing Style

### 2-1. Why-First Principle

When an LLM understands the reason, it makes correct judgments even in edge cases. Conveying context is more effective than imposing rigid rules.

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

When a problem is found in feedback or test results, generalize at the **principle level** rather than making a narrow fix that only fits the specific example.

**Overfitting fix:**
```markdown
If there is a column named "Q4 Sales", convert that column to numeric.
```

**Generalized fix:**
```markdown
If a column name contains keywords suggesting numeric values such as "sales",
"amount", or "quantity", convert that column to a numeric type. If conversion
fails, preserve the original value.
```

### 2-3. Imperative Tone

Use the imperative form ("do this", "use this") rather than descriptive forms ("this can be done", "it is possible to"). A skill is a set of instructions.

### 2-4. Context Economy

The context window is a shared resource. Ask whether every sentence justifies its token cost:
- "Is this something the agent already knows?" → Remove
- "Will the agent make a mistake without this explanation?" → Keep
- "Is one concrete example more effective than a long explanation?" → Replace with an example

---

## 3. Output Format Definition Patterns

Use this in skills where the format of the output matters:

```markdown
## Report Structure
Follow this template exactly:

# [Title]
## Summary
## Key Findings
## Recommendations
```

Keep format definitions concise, but including **real examples** makes them more effective. If an orchestrator (main agent) needs to automatically parse the output produced by a sub-agent, strictly fix the format specification using JSON schema or YAML.

---

## 4. Example Writing Patterns

Examples are more effective than long explanations:

```markdown
## Commit Message Format

**Example 1:**
Input: Add JWT token-based user authentication
Output: feat(auth): implement JWT-based authentication

**Example 2:**
Input: Fix bug where password visibility toggle button doesn't work on login page
Output: fix(login): fix password visibility toggle button behavior
```

**Conditions for good examples:**
- Input and output are presented as **pairs**
- Include at least 1 edge case or error case
- Domain-specific terms appear in the examples

---

## 5. Progressive Disclosure Pattern

Keep the `SKILL.md` body to **under 500 lines**, and separate detailed references, large data schemas, and domain-specific knowledge into files under `references/`. Guide the agent to load those files via shell `cat` only when needed.

### 5-1. Pattern 1: Domain-Based Separation

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
Create a new document using docx-js. → See [DOCX-JS.md](references/docx-js.md).

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

Observe agent transcripts during test runs. Bundle when you see the following patterns.

| Signal | Action |
|---|---|
| Same helper script created in 3 out of 3 tests | Bundle in `scripts/` |
| Same `pip install` / `npm install` run every time | Specify dependency installation step in the skill |
| Same multi-step approach repeated every time | Document as standard procedure in the skill body |
| Same workaround applied after similar error every time | Document known issues and solutions in the skill |

Bundled scripts must go through an **execution test**. Confirm actual execution results in the shell before including them in the skill.

---

## 7. Coordination and Generated Skills

Workers return outcome, artifact paths, verification, blockers, and next action directly to the main Orchestrator. Only the main Orchestrator coordinates workers and updates the chosen work record.

Use the exact runtime bundle from `orchestrator-template.md`. Generated skills load project-policy.md and orchestrator-procedures.md, and use schemas/models.md for role assignments. Validate those references from an isolated generated directory.

Define acceptance criteria in observable terms: behavior, artifact contents, or relevant test results. Do not make an agent-written completion marker the sole proof.

Resume by reading the selected issue/spec and checking actual artifacts. Issue-free work uses the conversation and optional notes. Do not require a local state machine or file-based message bus.

## 8. Data Schema Standards

Follow the standard schemas below for consistency in data exchange between skills and evaluation.

### 8-1. eval_metadata.json

Metadata for each test case:

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "User's task prompt",
  "assertions": [
    "Output contains X",
    "File was created in Y format"
  ]
}
```

### 8-2. grading.json

Assertion-based scoring results:

```json
{
  "expectations": [
    {
      "text": "Output contains 'Seoul'",
      "passed": true,
      "evidence": "Confirmed 'Seoul region data extraction' in step 3"
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

**Field name caution:** The top-level array is `expectations`, and internal fields must use exactly `text`·`passed`·`evidence` (variants like `items`·`name`·`met`·`details` are prohibited). The harness Phase 6 validation and section 4 of `skill-testing-guide.md` assume this schema.

### 8-3. timing.json

Execution time and token measurement:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

Save `total_tokens` and `duration_ms` **immediately** from the agent completion notification. This data is only accessible at the time of notification and cannot be recovered afterward.

### 8-4. Work records

Use the selected issue or local ticket for meaningful progress, evidence, blockers, and next action. Temporary scratch notes are optional and are not authoritative task state. Evaluation JSON described above is optional test evidence, not required runtime machinery.

---

## 9. What Not to Include in a Skill

- Supplementary documents such as `README.md`, `CHANGELOG.md`, `INSTALLATION_GUIDE.md`
- Meta information from the skill creation process (test results, iteration history, commit messages, etc.)
- User-facing documentation — a skill is **a set of instructions for an AI agent**.
- General knowledge that agents already know (language syntax, general CS concepts, etc.)
- Hardcoded values that only fit a specific test case (violation of the generalization principle)
