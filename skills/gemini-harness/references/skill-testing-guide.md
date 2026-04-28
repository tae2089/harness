# Skill Testing & Iterative Improvement Guide

A methodology for verifying the quality of skills created in the harness and improving them iteratively. A supplementary reference for `SKILL.md` Phase 6 (Validation and Testing). This guide is written with the premise of the **Gemini CLI orchestration environment** (no direct communication between sub-agents; the main agent acts as Grader and Analyzer).

---

## Table of Contents

1. [Test Framework Overview](#1-test-framework-overview)
2. [Writing Test Prompts](#2-writing-test-prompts)
3. [Execution Testing: With-skill vs Baseline](#3-execution-testing-with-skill-vs-baseline)
4. [Quantitative Evaluation: Assertion-Based Grading](#4-quantitative-evaluation-assertion-based-grading)
5. [Using Specialized Agents (Grader / Comparator / Analyzer)](#5-using-specialized-agents-grader--comparator--analyzer)
6. [Iterative Improvement Loop](#6-iterative-improvement-loop)
7. [Description Trigger Verification](#7-description-trigger-verification)
8. [Workspace Structure](#8-workspace-structure)

---

## 1. Test Framework Overview

Skill quality verification is a combination of **qualitative evaluation** and **quantitative evaluation**.

| Evaluation Type | Method | Suitable Skills |
|---|---|---|
| **Qualitative** | User directly reviews the output | Subjective quality such as writing style, design, creative work |
| **Quantitative** | Automated assertion-based grading | Objectively verifiable outputs such as file generation, data extraction, code generation |

Core loop: **Write → Run tests in parallel → Evaluate → Improve → Retest**

In Gemini CLI, since there is no communication between sub-agents, **the main agent doubles as the Grader and Analyzer, or calls a dedicated QA agent (`@grader`)** to perform grading.

---

## 2. Writing Test Prompts

### 2-1. Principles

Test prompts should be **specific and natural sentences that an actual user would type**. Abstract or artificial prompts have low test value.

### 2-2. Bad Examples

```
"Process the PDF"
"Extract the data"
"Generate a chart"
```

### 2-3. Good Examples

```
"Add a profit margin (%) column to 'Q4_Sales_Final_v2.xlsx' in the Downloads folder
using column C (Sales) and column D (Cost). Then sort by profit margin in descending order."
```

```
"Extract the table on page 3 from this PDF and convert it to CSV. The table header
spans 2 rows — the first row is the category and the second row is the actual column name."
```

### 2-4. Prompt Diversity

- Mix **formal / casual** tone
- Mix **explicit / implicit** intent (cases where the file format is stated directly vs. must be inferred from context)
- Mix **simple / complex** tasks
- Some include abbreviations, typos, and casual expressions

### 2-5. Coverage

Start with 2–3 prompts but design to cover:
- 1 core use case
- 1 edge case
- (Optional) 1 compound task

---

## 3. Execution Testing: With-skill vs Baseline

### 3-1. Comparison Run Structure (Gemini CLI Parallel Call)

For each test prompt, call two sub-agents **in parallel within a single response turn**.

**With-skill execution:**
```
Call @tester-with-skill
  Prompt: "{test prompt}"
  Specify skill path: .gemini/skills/{skill-name}/
  Output path: _workspace/{skill-name}/iteration-N/eval-{id}/with_skill/outputs/
```

**Baseline execution:**
```
Call @tester-baseline
  Prompt: "{test prompt}"  (same)
  Skill activation prohibited (cannot call activate_skill)
  Output path: _workspace/{skill-name}/iteration-N/eval-{id}/without_skill/outputs/
```

In Gemini CLI, agent-level parallelism is achieved by specifying the **`wait_for_previous: false`** parameter when calling the `invoke_agent` tool. (Shell commands can also be run simultaneously in the background with `run_shell_command`'s background option, but this is distinct from evaluation agent calls.)

### 3-2. Baseline Selection

| Situation | Baseline |
|---|---|
| Creating a new skill | Run the same prompt without the skill |
| Improving an existing skill | Previous skill version (snapshot) — reuse results preserved in the iteration-N-1 directory |

### 3-3. Timing/Cost Data Capture

Save elapsed time and tokens **immediately** from the agent completion notification. This is only accessible at the moment of notification and cannot be recovered afterward.

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

Since Gemini CLI includes token/time metadata in execution results, the main agent records this with `write_file` to `_workspace/{skill-name}/iteration-N/eval-{id}/{variant}/timing.json`.

---

## 4. Quantitative Evaluation: Assertion-Based Grading

### 4-1. Assertion Writing Principles

When the output can be objectively verified, define assertions for automated grading.

**Good assertion:**
- Objectively determinable as true/false
- A descriptive name that makes it clear what is being checked just from the result
- Verifies the **core value** of the skill

**Bad assertion:**
- One that always passes regardless of whether the skill is present (e.g., "output exists")
- One requiring subjective judgment (e.g., "is well written")

### 4-2. Programmatic Verification

If an assertion can be verified with code, write it as a script. It is faster and more reliable than manual inspection, and can be reused across iterations.

In Gemini CLI, the main agent executes verification scripts (Python, shell, etc.) with `run_shell_command` and records the results in `grading.json`.

### 4-3. Beware of Non-Discriminating Assertions

Assertions that "pass 100% in both configurations (With-skill / Baseline)" do not measure the differential value of the skill. Remove such assertions or replace them with more challenging ones.

### 4-4. Grading Result Schema

```json
{
  "expectations": [
    {
      "text": "Profit margin column is added",
      "passed": true,
      "evidence": "Confirmed 'profit_margin_pct' column in column E"
    },
    {
      "text": "Sorted by profit margin in descending order",
      "passed": false,
      "evidence": "Original order retained without sorting"
    }
  ],
  "summary": {
    "passed": 1,
    "failed": 1,
    "total": 2,
    "pass_rate": 0.50
  }
}
```

This schema is saved to the path `_workspace/{skill-name}/iteration-N/eval-{id}/{variant}/grading.json`.

> **Path distinction:**
> - **Long-term iterative improvement (this file):** `_workspace/{skill-name}/iteration-N/eval-{id}/{variant}/grading.json`
> - **One-time verification during harness construction (`SKILL.md` Phase 6):** `_workspace/evals/{timestamp}/grading.json`
>
> The two paths serve different purposes and can coexist. When aggregating in Phase 6, scan both paths or specify the target path explicitly.

---

## 5. Using Specialized Agents (Grader / Comparator / Analyzer)

In the Gemini CLI environment, since direct communication between sub-agents is not possible, the main agent **sequentially calls** dedicated evaluation agents and brokers results via `findings.md` and `grading.json`.

### 5-1. Grader

Performs assertion-based grading and cross-validates by extracting verifiable claims from the output.

**Role:**
- Pass/fail judgment per assertion + supporting evidence
- Extract and verify factual claims from the output
- Feedback on the quality of the eval itself (suggestions when assertions are too easy or ambiguous)

**Recommended tools:** `ask_user`, `activate_skill`, `read_file`, `grep_search`, `run_shell_command` (`temperature: 0.2`).

### 5-2. Comparator (Blind Comparator)

Anonymizes two outputs as A/B and judges quality without knowing which result used the skill.

**When to use:** When you want to rigorously confirm "is the new version really better?". Can be omitted in normal iterative improvement.

**Judgment criteria:**
- Content: accuracy, completeness
- Structure: organization, formatting, usability
- Overall score

**Gemini CLI note:** The main agent must anonymize copy the two outputs to `_workspace/.../variant_A.md` and `variant_B.md`, then pass only the paths to the Comparator. If "with_skill"/"without_skill" labels are exposed in the prompt, the blind nature is compromised.

### 5-3. Analyzer

Analyzes statistical patterns from benchmark data:
- Non-discriminating assertions (both configurations pass → no discriminating power)
- High-variance evals (results vary significantly across runs → unstable)
- Time/token tradeoff (skill improves quality but also increases cost)

Results are recorded in `_workspace/{skill-name}/iteration-N/benchmark.json` and in the [Key Insights] section of `findings.md`.

**`benchmark.json` schema:**
```json
{
  "iteration": 1,
  "timestamp": "2026-04-25T12:00:00Z",
  "eval_count": 3,
  "with_skill": {
    "pass_rate": 0.83,
    "avg_tokens": 45230,
    "avg_duration_ms": 18500
  },
  "without_skill": {
    "pass_rate": 0.50,
    "avg_tokens": 38100,
    "avg_duration_ms": 12300
  },
  "skill_delta": {
    "pass_rate_improvement": 0.33,
    "token_overhead": 7130,
    "duration_overhead_ms": 6200
  },
  "non_discriminating": ["eval-simple-csv-export"],
  "high_variance": [],
  "notes": "Simple CSV extraction assertion passes in both configurations — candidate for removal"
}
```

---

## 6. Iterative Improvement Loop

### 6-1. Collecting Feedback

Show the output to the user and collect feedback. Empty feedback is interpreted as "no issues".

### 6-2. Improvement Principles

1. **Generalize feedback** — Narrow fixes that only fit the test example are overfitting. Fix at the principle level.
2. **Remove what doesn't earn its weight** — Read the transcripts; if the skill is making the agent do unproductive work, remove it.
3. **Explain the why** — Even if the user's feedback is brief, understand why it matters and reflect that understanding in the skill.
4. **Bundle repetitive tasks** — If the same helper script is generated in every test, pre-include it in `scripts/`.

### 6-3. Iteration Procedure

```
1. Modify the skill
2. Re-run all test cases in a new iteration-N+1/ directory
3. Present results to the user (compared to previous iteration)
4. Collect feedback (use ask_user if ambiguous)
5. Modify again → repeat
```

**Termination conditions:**
- The user is satisfied
- All feedback is empty (all outputs have no issues)
- No more meaningful improvement is possible

### 6-4. Draft → Review Pattern

When modifying a skill, write a draft, then **re-read it with fresh eyes** and improve it. Do not try to write it perfectly in one pass; go through a draft-review cycle.

---

## 7. Description Trigger Verification

The Gemini CLI trigger router selects a skill based only on the description. Therefore, the description is the **only practical API** of the skill.

### 7-1. Writing Trigger Eval Queries

Write 20 eval queries — 10 should-trigger + 10 should-NOT-trigger.

**Query quality criteria:**
- Specific and natural sentences that an actual user would type
- Include specific details such as file paths, personal context, column names, company names
- Mix varied length, tone, and format
- Focus on **edge cases** rather than cases with clear answers

**Should-trigger queries (10):**
- Same intent expressed in various ways (formal/casual)
- Cases where the skill or file type is not explicitly stated but is clearly needed
- Non-mainstream use cases
- Cases that compete with other skills but this skill should win

**Should-NOT-trigger queries (10):**
- **Near-miss is the key** — Queries where keywords are similar but a different tool or skill is appropriate
- Obviously unrelated queries ("write a Fibonacci function") have no test value
- Adjacent domains, ambiguous expressions, keyword overlap but different context

### 7-2. Existing Skill Conflict Verification

Verify that the new skill's description does not overlap with the trigger area of existing skills.

1. Collect descriptions from the existing skill list (full scan of `.gemini/skills/*/SKILL.md` with `glob`·`read_file`).
2. Verify that the new skill's should-trigger queries do not incorrectly trigger existing skills.
3. When a conflict is found, describe the **boundary conditions** in the description more clearly (specify the differentiator from similar skills).

### 7-3. Automated Optimization (Optional Advanced Feature)

When description optimization is needed:

1. Split the 20 eval queries into Train (60%) / Test (40%).
2. Measure trigger accuracy with the current description.
3. Analyze failure cases to generate an improved description.
4. Select the best description based on the Test set (not the Train set — to prevent overfitting).
5. Repeat up to 5 times.

> Gemini CLI automation is performed with a script that calls `gemini -p "..."` via `run_shell_command`. Token costs are high, so run this in the final stage after the skill has stabilized sufficiently.

---

## 8. Workspace Structure

A directory structure for systematically managing test and evaluation results.

> **Name distinction:** Here `{skill-name}` is the **name of the skill under test**. It is a separate level from the `{plan_name}` in `_workspace/{plan_name}/` used during orchestration runs. Skill test results are stored under `_workspace/{skill-name}/`, and orchestration run outputs are stored separately under `_workspace/{plan_name}/`.

```
_workspace/{skill-name}/
├── iteration-1/
│   ├── eval-descriptive-name-1/
│   │   ├── eval_metadata.json
│   │   ├── with_skill/
│   │   │   ├── outputs/
│   │   │   ├── timing.json
│   │   │   └── grading.json
│   │   └── without_skill/
│   │       ├── outputs/
│   │       ├── timing.json
│   │       └── grading.json
│   ├── eval-descriptive-name-2/
│   │   └── ...
│   └── benchmark.json
├── iteration-2/
│   └── ...
└── evals/
    └── evals.json
```

**Rules:**
- Eval directories use **descriptive names**, not numbers (e.g., `eval-multi-page-table-extraction`).
- Each iteration is preserved in an independent directory (do not overwrite previous iterations).
- `_workspace/` is not deleted — used for post-hoc verification, audit trails, and blind comparisons.
- **Evaluation metadata for the entire session** (skill version, total number of iterations, final pass rate, etc.) is cumulatively recorded in `evals.json` to track the long-term quality trend of the harness.

**`evals.json` schema:**
```json
{
  "skill_name": "pdf-extractor",
  "skill_version": "1.0.0",
  "created_at": "2026-04-25T10:00:00Z",
  "total_iterations": 3,
  "final_pass_rate": 0.85,
  "iterations": [
    {
      "iteration": 1,
      "eval_count": 3,
      "pass_rate": 0.67,
      "timestamp": "2026-04-25T10:00:00Z",
      "notes": "Initial version — 2 out of 3 assertions passed"
    },
    {
      "iteration": 2,
      "eval_count": 3,
      "pass_rate": 0.83,
      "timestamp": "2026-04-25T11:00:00Z",
      "notes": "Retest after improving multi-step table processing"
    }
  ]
}
```

---

## Orchestrator Test Scenarios

An orchestrator must describe at least **1 normal flow + 1 error flow + 1 resume flow** in the skill body.

> **Name distinction:** "Orchestrator Steps 0~5" refers to the **internal execution stages of the orchestrator skill itself** (context verification · initialization · agent calls · QA · integration · reporting). This is a separate concept from the Stage·Step hierarchy in `workflow.md`.

### Normal Flow

1. The user provides `{input}`.
2. Orchestrator Step 0 confirms `_workspace/` does not exist → selects initial execution mode.
3. Orchestrator Step 1 initializes `workflow.md`·`tasks.md`·`findings.md`.
   - `workflow.md`: Stage 1 (`{plan_name}` deliverable kebab-case) / Step 1 (deliverable kebab-case) / record list of active agents. **Placeholder (`main`) is prohibited** — follows Jira title convention.
   - `checkpoint.json`: initialize `current_stage: "{deliverable-kebab}"`, `current_step: "{deliverable-kebab}"`, `active_pattern: {first step pattern}`, `status: "in_progress"`.
4. Orchestrator Step 2 enters [Step execution loop] — calls the agent for the current Step in workflow.md.
   - @analyst → @coder sequential execution (batch-call parallelizable segments).
5. Orchestrator Step 3 calls @reviewer → confirms no conflicts in `findings.md`.
6. Orchestrator Step 4 generates `_workspace/{plan_name}/final_{output}.md`.
7. Orchestrator Step 5 reports summary to the user.
8. **Expected result:** `_workspace/{plan_name}/final_{output}.md` exists, all items in `tasks.md` are `Done`.

### Resume Flow (Persistence Test)

1. @analyst call completes; session ends due to network failure during @coder call.
2. User re-invokes → orchestrator Step 0 finds `checkpoint.json`.
3. Restore `current_stage`·`current_step` from `checkpoint.json` → confirm entry point for that step.
4. Confirm @analyst output exists → immediately resume from the @coder step.
5. **Expected result:** @analyst work is skipped; only work from @coder onward is completed.

### Error Flow (Fix Loop)

1. Orchestrator Step 3: @reviewer rejects @coder's output (security vulnerability found).
2. Orchestrator records rejection reason in `findings.md` [Change Requests].
3. Orchestrator re-invokes @coder, injecting @reviewer's report.
4. @coder fixes the vulnerability and generates a new output.
5. @reviewer re-validation passes → proceed to orchestrator Step 4.
6. Final report explicitly states "error recovery: passed after @reviewer rejection and @coder fix".

### expert_pool Scenario — Ambiguous Classification Path

1. User inputs "review both performance and security" (multiple domains mixed).
2. Orchestrator Step 2 expert_pool: CLASSIFY result is AMBIGUOUS.
3. Calls `ask_user("Expert list: which of [@perf-analyst, @security-analyst] should handle this?")`.
4. User responds "@security-analyst".
5. Records `"- @security-analyst: directly specified by user"` in findings.md [Routing Rationale].
6. Calls @security-analyst → records task file → termination condition satisfied.
7. **Expected result:** AMBIGUOUS path → ask_user triggered, user-specified agent is selected.

### handoff Scenario — Standalone Completion Without [NEXT_AGENT]

1. @log-analyzer is called → analysis complete, no `[NEXT_AGENT]` keyword in response.
2. Orchestrator enters the ELSE branch: records `task_{log-analyzer}_{id}.json` (standalone completion).
3. Checks termination condition → satisfied → transitions to next Step.
4. **Expected result:** handle_handoff not called, task file is recorded based on active_agents[0].

---

## Reference Links

- The simplified form of the grading schema (`grading.json`) is included in `references/skill-writing-guide.md`.
- The Phase 6 validation procedure follows the workflow Phase 6 item in `SKILL.md`.
- Stage-Step workflow details: `references/stage-step-guide.md`.
- **Stage-Step workflow test scenarios** (scenarios 1~6): See `references/stage-step-guide.md`.
