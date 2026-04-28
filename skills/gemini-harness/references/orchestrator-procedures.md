# Orchestrator Procedures & Principles

Common error handling procedures, validation principles, and description writing guidelines applied when writing orchestrator skills.
Used alongside the Step 0~5 pseudocode in `orchestrator-template.md`.

## Error Handling and Self-Healing

> **Canonical spec.** Retry, Blocked, and ask_user references in other files (qa-agent-guide, agent-design-patterns, etc.) follow this decision tree.

### Error Response Decision Tree (pseudocode)

```
PROCEDURE handle_error(agent, task, error_type):

    // ── Immediate ask_user (no retry) ────────────────────────────
    IF error_type == "ambiguous_input" OR error_type == "missing_params":
        CALL ask_user("Ambiguous input or missing parameters: {details}")
        RETURN

    IF error_type == "majority_failure":        // majority of agents failed
        ATOMIC_WRITE "_workspace/tasks.md" ← record interruption point
        CALL ask_user("Majority failure. Requesting confirmation to proceed.")
        RETURN

    // ── Auto recovery (Step 0 resume) ────────────────────────────
    IF error_type == "timeout" OR error_type == "session_restart":
        // Step 0 re-run detects checkpoint.json → auto resume
        // ※ Idempotency required: each agent must first check whether output files
        //   already exist and skip already-completed tasks. Results must be identical
        //   regardless of how many times resumed.
        GOTO Step 0
        RETURN

    // ── Data conflict ─────────────────────────────────────────────
    IF error_type == "data_conflict":
        RECORD findings.md ← "[Data Conflict]" section with source attribution
        CALL invoke_agent(reviewer, conflict_resolution_prompt)
        IF reviewer resolves conflict:
            RETURN
        ELSE:
            CALL ask_user("Data conflict unresolved: {details}")
            RETURN

    // ── Retryable failure ─────────────────────────────────────────
    // Applies to: agent_failure | reviewer_reject | max_turns_exceeded
    // Applies to: handoff_no_candidate (no handoff target found)
    IF task.retries < 2:                        // fewer than 3 total attempts
        task.retries += 1
        RECORD findings.md ← "Retry {task.retries}/2: {error cause} → approach changed"
        CALL invoke_agent(agent, modified_prompt_with_feedback)
        RETURN

    // ── 3 attempts exhausted → Blocked protocol ───────────────────
    GOTO blocked_protocol

// ── Blocked protocol (common) ─────────────────────────────────────
PROCEDURE blocked_protocol(agent, task):
    ATOMIC_WRITE "_workspace/tasks/task_{agent}_{id}.json":
        status  ← "blocked"
        result  ← null
        retries ← task.retries   // preserve final value
    RECORD findings.md ← "Final rejection: {reason} | Attempt history: {history}"
    // Step/Stage transition is absolutely prohibited
    DO NOT UPDATE checkpoint.json  // Role separation: blocked_protocol only records the task file.
                                   // Step 2's pre-blocked check detects the task file on the next
                                   // cycle entry and updates checkpoint to blocked.
                                   // Direct update by blocked_protocol would cause duplicate updates.
    CALL ask_user("Blocked: @{agent} — {reason}. Requesting intervention.")
    HALT    // Arbitrary Skip or Done is absolutely prohibited

// ── Special case: Handoff cycle detection ─────────────────────────
// (Prevents A→B→A infinite loops. call_history = handoff_chain field of checkpoint.json)
PROCEDURE handle_handoff(next_agent):
    READ "_workspace/checkpoint.json" → ckpt
    call_history ← ckpt.handoff_chain ?? []     // empty array if not present

    IF next_agent IN call_history:
        RECORD findings.md ← "Circular handoff: {call_history} → {next_agent}"
        CALL ask_user("Circular handoff detected: {path}. Requesting intervention.")
        HALT

    IF LENGTH(call_history) >= 3:               // exceeds 3 levels
        RECORD findings.md ← "Handoff exceeded 3 levels: {call_history}"
        CALL ask_user("Handoff exceeded 3 levels. Requesting intervention.")
        HALT

    // Safe → update history then invoke
    ATOMIC_WRITE "_workspace/checkpoint.json":
        ckpt.handoff_chain ← APPEND(call_history, next_agent)
        ckpt.last_updated  ← NOW()
    CALL invoke_agent(next_agent, ...)

// Reset handoff_chain on Step transition
// (reset handoff_chain: [] when updating checkpoint.json)
```

## Test Scenarios

> Full normal flow / resume flow / error flow scenarios: `references/skill-testing-guide.md` § **Orchestrator Test Scenarios** (3 types: normal flow / resume flow / error flow).

## Follow-up Task Keywords for description (Required)

An orchestrator description with **only initial execution keywords is insufficient**. If the following follow-up expressions are not included, the harness effectively becomes dead code after the first run.

- re-run / run again / update / modify / supplement
- "redo only {partial} of {domain}", "based on previous results", "improve results"
- Domain-specific everyday expressions (e.g., for a launch strategy harness: "launch", "promotion", "trending", etc.)

If follow-up keywords are missing from the `description`, the Gemini CLI trigger router will not select this skill from the second invocation onward.

## Writing and Execution Principles

1. **Emphasize the broker role:** The main agent does not merely call tools — it analyzes results and **elevates the context (input) for the next agent**.
2. **Persistence first:** Update files immediately after every major state change to prepare for unexpected termination.
3. **Atomic state integration:** The orchestrator collects and integrates the split task files generated by parallel agents to prevent write conflicts at the source.
4. **Strict tool isolation:** When invoking agents, do not assign tasks that exceed the defined `tools` scope.
5. **Ensure visibility:** All intermediate processes must be recorded as files via `findings.md` and `tasks.md`.
6. **Declare Step dependencies:** Declare dependencies through the Step order and exit conditions in workflow.md. The structure of Step N completion → Step N+1 entry must be clearly expressed in workflow.md.
7. **Realistic error assumptions:** Do not assume "everything will succeed". Include the rule that Stage transitions are prohibited when a Step is Blocked.
8. **Test scenarios required:** Include at least 1 normal + 1 error scenario in the skill body. Without them, Step 5 validation cannot be passed.

## Stage/Step Transition Protocol

> Full details of the Step execution loop in Step 2, Stage transition gate, and access control logic:
> See **`references/stage-step-guide.md`**.
