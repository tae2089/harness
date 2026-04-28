# QA Agent Design Guide

A reference guide for including a QA agent in a build harness. Based on bug patterns and root cause analyses discovered in real projects, this guide provides a verification methodology for systematically catching defects that QA tends to miss. This guide assumes the **Gemini CLI orchestration environment** (no direct communication between sub-agents; the main agent acts as Data Broker).

---

## Table of Contents

1. Patterns of defects that QA agents miss
2. Integration Coherence Verification
3. QA Agent Design Principles (Orchestration Mode)
4. Verification Result Reporting Protocol (JSON Protocol)
5. Verification Checklist Template
6. QA Agent Definition Template
7. Appendix: Lessons Learned from Real Cases

---

## 1. Patterns of defects that QA agents miss

### 1-1. Boundary Mismatch

The most frequent type of defect. Two components are each implemented "correctly," but the contract breaks at the connection point.

| Boundary | Mismatch example | Why it is missed |
|---|---|---|
| API response → frontend hook | API returns `{ projects: [...] }`, hook expects `SlideProject[]` | Passes individual validation; no cross-comparison performed |
| API response field name → type definition | API uses `thumbnailUrl` (camelCase), type uses `thumbnail_url` (snake_case) | TypeScript generic casting causes the compiler to miss it |
| File path → link href | Page is at `/dashboard/create` but link points to `/create` | File structure and href are not cross-compared |
| State transition map → actual status update | Map defines `generating_template → template_approved`, transition missing in code | Only the map's existence is checked; update code is not traced |
| API endpoint → frontend hook | API exists but no corresponding hook (never called) | API list and hook list are not mapped 1:1 |
| Immediate response → async result | API immediately returns `{ status }`, frontend accesses `data.failedIndices` | Only the type is checked without distinguishing sync/async responses |

### 1-2. Why static code review cannot catch these

- **Limits of TypeScript generics:** `fetchJson<SlideProject[]>()` — compiles even if the runtime response is `{ projects: [...] }`.
- **`npm run build` passing ≠ correct behavior:** If type casting, `any`, or generics are present, the build succeeds but fails at runtime.
- **Existence verification vs. connection verification:** "Does the API exist?" and "Does the API response match the caller's expectation?" are completely different checks.
- **One-sided code review:** If a reviewer reads only the producer or only the consumer, a contract mismatch will never be visible.

---

## 2. Integration Coherence Verification

The **cross-comparison verification** areas that must be included in every QA agent.

### 2-1. API Response ↔ Frontend Hook Type Cross-Verification

**Method:** Compare the object shape passed to `NextResponse.json()` in each API route with the type parameter `T` in `fetchJson<T>` of the corresponding hook.

```
Verification steps:
1. Extract the shape of the object passed to NextResponse.json() in the API route
2. Check the T type in fetchJson<T> in the corresponding hook
3. Compare whether the shape and T match
4. Check wrapping: if the API returns { data: [...] }, verify the hook unwraps via .data
```

**Patterns to watch especially:**
- Pagination API `{ items: [], total, page }` vs. frontend expecting an array
- Mismatches between snake_case DB fields → camelCase API responses → frontend type definitions
- Shape differences between an immediate response (202 Accepted) and the final result

### 2-2. File Path ↔ Link/Router Path Mapping

**Method:** Extract URL paths from page files under `src/app/`, then compare against all `href`, `router.push()`, and `redirect()` values in the code.

```
Verification steps:
1. Extract URL patterns from page.tsx file paths under src/app/
   - (group) → removed from URL
   - [param] → dynamic segment
2. Collect all href=, router.push(, redirect( values in the code
3. Verify that each link matches an actually existing page path
4. Watch for URL prefix of pages inside route groups (e.g., under dashboard/)
```

### 2-3. State Transition Completeness Tracking

**Method:** Extract all `status:` updates from the code and compare against the state transition map.

```
Verification steps:
1. Extract the list of allowed transitions from the state transition map (STATE_TRANSITIONS)
2. Search all API routes for the .update({ status: "..." }) pattern
3. Verify that each transition is defined in the map
4. Identify transitions defined in the map but never executed in code (dead transitions)
5. Check for missing transitions from intermediate states (e.g., generating_template) to final states (template_approved)
```

### 2-4. API Endpoint ↔ Frontend Hook 1:1 Mapping

**Method:** List all API routes and frontend hooks to verify that every endpoint has a matching hook.

```
Verification steps:
1. Extract HTTP-method-level endpoint list from route.ts files under src/app/api/
2. Extract fetch call URL list from use*.ts files under src/hooks/
3. Identify API endpoints not called by any hook → flag as "unused"
4. Determine whether "unused" is intentional (e.g., admin API) or accidental (missing hook call)
```

---

## 3. QA Agent Design Principles (Orchestration Mode)

In the Gemini CLI environment, sub-agents cannot communicate directly, so the orchestrator (main agent) is responsible for coordination.

### 3-1. "Provide both sides simultaneously" principle

For a QA agent to catch boundary bugs, the main agent must provide **context from both sides** when invoking it.

- **Method:** Use `read_file` to read both the API route and the frontend hook, and specify both paths explicitly in the QA agent prompt.
- **Agent instruction:** State "You must open both specified files and cross-compare them" in the system prompt.

### 3-2. Grant execution permissions, not just read access

Effective QA goes beyond simply reading files — it must use `grep_search` to search for patterns and `run_shell_command` to actually run test, lint, and type-check scripts. Therefore, the QA agent's `tools` must include not only `read_file`, `grep_search`, and `glob` but also **execution tools (`run_shell_command`)**.

**Run long-running processes in the background.** Gemini CLI's `run_shell_command` supports background execution (e.g., `npm run dev &`, `is_background: true`). Non-terminating processes such as dev servers, build watchers, and test daemons should be run in the background, while follow-up verification such as `curl`, Playwright, and API tests are performed within the same turn. This avoids foreground blocking while keeping the E2E/integration QA flow uninterrupted.

| Purpose | Execution mode | Example |
|---|---|---|
| Lint, type check, unit tests | **Foreground** (result needed immediately) | `npm run lint`, `tsc --noEmit`, `pytest` |
| Dev server, API server | **Background** | `npm run dev &`, `python -m uvicorn app:app &` |
| Build watcher, file watcher | **Background** | `vite build --watch &`, `jest --watch &` |
| E2E verification after starting the server | Background + Foreground combination | Background dev server, foreground `curl`/Playwright |

Note: If the QA agent starts a background process, it must be terminated upon completion (`kill $PID` or `pkill`) and recorded in the "Cleanup" section of `qa_report.md` to avoid affecting subsequent QA calls.

### 3-3. Prioritize "cross-comparison" over "existence checks" in checklists

| Weak checklist | Strong checklist |
|---|---|
| Does the API endpoint exist? | Does the API endpoint's response shape match the corresponding hook's type? |
| Is the state transition map defined? | Do all status update code entries match the transitions in the map? |
| Does the page file exist? | Do all links in the code point to actually existing pages? |
| Is TypeScript strict mode enabled? | Is there no type safety bypassed via generic casting? |

### 3-4. Incremental QA

Do not validate everything at once after full completion. Invoke the QA agent immediately after each module (producer + consumer) is completed to keep the feedback loop short.

- If the orchestrator places QA only at Step 4 (after full completion), bugs accumulate and early boundary mismatches propagate to subsequent modules.
- **Recommended pattern:** Run cross-verification of each backend API and its corresponding hook immediately after completion.

### 3-5. Report first; fixes are handled by re-invoking the orchestrator

In Gemini CLI, the QA agent cannot send instructions directly to other agents. Discovered bugs should be recorded in `_workspace/qa_report.md`, and **verification results (PASS/FAIL) should be recorded in the split task file (`_workspace/tasks/task_{agent}_{id}.json`) for coherence with the orchestrator**. The main agent reads this report and the split files, summarizes the findings in `findings.md`, and re-invokes implementation agents as needed.

---

## 4. Verification Result Reporting Protocol (JSON Protocol)

The QA agent must create a split task file in the following format to ensure data coherence in a parallel execution environment.

- **File path:** `_workspace/tasks/task_{agent_name}_{task_id}.json`
- **Reporting schema:**
    ```json
    {
      "agent": "@qa-inspector",
      "task_id": "T101",
      "status": "done",        // "done" | "blocked" — base schema field
      "retries": 0,            // cumulative retry count. blocked when retries ≥ 2 (0·1 allowed = 3 total)
      "evidence": "E2E test passed. Logs saved at _workspace/qa/log.txt",
      "artifact_path": "_workspace/qa_report.md",  // base schema field name must be followed
      "result": "PASS"         // QA-specific extension field. "PASS" | "FAIL" | null (when Blocked)
    }
    ```

> **Schema reference:** For the normative definitions of `agent`, `task_id`, `status`, `retries`, `evidence`, and `artifact_path` fields, see `references/orchestrator-template.md` § "Split Task File Protocol". The schema above is an application example from the QA agent's perspective; `result` is the only QA-specific extension field.

### Zero-Tolerance Retry Protocol

> **The authoritative source is `references/orchestrator-procedures.md` — "Error Response Decision Tree".** The following is a summary of its application from the QA agent's perspective.

The QA agent must not skip or ignore verification failures arbitrarily. The following procedure must be strictly followed:

1. **Up to 2 retries (3 attempts total):** Identify the cause of failure, change the approach, and retry. Increment the `retries` value on each retry.
2. **Still failing after 3 attempts → `blocked`:** Record `status: "blocked"`, `result: null`. Record the failure cause, attempt history, and required information in detail in the "Blocked Items" section of `qa_report.md`.
3. **Orchestrator escalation:** When the main agent detects `Blocked` → record `status: "blocked"` in `checkpoint.json`, then call `ask_user`. **Arbitrary skip is strictly prohibited.** On restart, Step 0 detects the blocked status → displays the reason and waits for instructions.

---

## 5. Verification Checklist Template

A general-purpose integration coherence checklist to be included in QA agent definitions. The core principle is to **read both components that share a boundary simultaneously** and cross-compare for contract conformance. Select only the relevant sections based on the domain.

```markdown
### Integration Coherence Verification

#### Boundary Contracts (common to all domains)
- [ ] Producer output types/formats match Consumer input expectations
- [ ] Shared constants and enum values are defined identically on both sides
- [ ] null/undefined handling for optional fields is consistent on both sides
- [ ] Async and immediate response formats are clearly distinguished on the consumer side

#### Referential Integrity (common to all domains)
- [ ] All paths, identifiers, and links in the code point to actually existing targets
- [ ] Dynamic parameters and slots are filled with correct values

#### State Transition Completeness (when a state machine is present)
- [ ] All defined state transitions are executed in code (no dead transitions)
- [ ] All state-change code entries match the transition definitions (no unauthorized transitions)
- [ ] No missing transitions from intermediate states to final states

#### Data Flow Coherence (common to all domains)
- [ ] Field names and types from the source (DB, file, API) are consistent throughout the entire pipeline
- [ ] Data transformations (type, case, unit) are handled explicitly

---

#### [Web App] API ↔ Frontend Connection
- [ ] All API route response shapes match the generic types of the corresponding hooks
- [ ] Wrapped responses ({ items: [...] }) are unwrapped in the hook
- [ ] snake_case ↔ camelCase conversion is applied consistently
- [ ] Immediate responses (202) and final result shapes are distinguished on the frontend
- [ ] A corresponding frontend hook exists for every API endpoint and is actually called

#### [Web App] Routing Coherence
- [ ] All href/router.push values in the code match actual page file paths
- [ ] Route groups ((group)) are accounted for (they are removed from the URL) in path validation
- [ ] Dynamic segments ([id]) are filled with the correct parameters
```

---

## 6. QA Agent Definition Template

Conforms to the official Gemini CLI sub-agent format.

```markdown
---
name: qa-inspector
description: "QA verification specialist. Validates spec compliance, boundary integration coherence, and artifact quality. Always select this agent for quality inspection, bug review, and coherence verification requests."
kind: local
model: "gemini-3-flash-preview"
temperature: 0.2
max_turns: 10
tools:
  - ask_user
  - activate_skill
  - read_file
  - read_many_files
  - grep_search
  - glob
  - run_shell_command
---

# QA Inspector

## Core Role
Verify artifact quality against the spec and **inter-module integration coherence**. Regardless of domain, the core principle is to read both components that share a boundary simultaneously and cross-compare for contract conformance.

## Verification Priorities

1. **Integration coherence** (highest) — boundary mismatches are the leading cause of runtime errors
2. **Functional spec compliance** — contracts, state machines, data models
3. **Artifact quality** — format, completeness, readability (domain-specific criteria apply)
4. **Internal consistency** — unused references, naming conventions, duplication

## Verification Method: "Read Both Sides Simultaneously"

Boundary verification must always be done by **opening both the producer and the consumer** and comparing them.

| Verification target | Producer (left) | Consumer (right) |
|---|---|---|
| Data contract | Output format/type definitions | Input expectations/parsing logic |
| Paths/references | Defined paths, identifiers, links | Paths and identifiers used by the caller |
| State transitions | Transition map/definitions | Actual state-change code |
| Data flow | Field names/types from source (DB, file, API) | Field names/types in downstream consumers |

> **Web App example:** `route.ts` NextResponse → `fetchJson<T>` hook / `src/app/` page path → `href` value / `STATE_TRANSITIONS` map → `.update({ status })` code

## Collaboration Protocol (Orchestration)

1. Verification results are recorded in `_workspace/qa_report.md`.
2. Discovered bugs are detailed in the **"Fix Instructions"** section with `file:line + fix method`.
3. For boundary issues, both producer and consumer paths are listed in the report so both agents can rework as needed.
4. The main agent (orchestrator) reads this report, summarizes it in `findings.md`, and re-invokes implementation agents as needed.
5. Ambiguous contracts (e.g., "is this field optional?") are not guessed — confirm with `ask_user`.
```

---

## 7. Appendix: Lessons Learned from Real Cases

All content in this guide is derived from the lessons learned from the actual bugs below.

| Bug | Boundary | Cause |
|---|---|---|
| `projects?.filter is not a function` | API → hook | API returns `{ projects: [] }`, hook expects an array |
| All dashboard links 404 | File path → href | Missing `/dashboard/` prefix |
| Theme image not displayed | API → component | `thumbnailUrl` vs `thumbnail_url` |
| Theme selection not saved | API → hook | select-theme API exists, no corresponding hook |
| Creation page stuck forever | State transition → code | Missing `template_approved` transition code |
| `data.failedIndices` crash | Immediate response → frontend | Background result accessed from immediate response |
| View slides after completion 404 | File path → href | `/projects/` → `/dashboard/projects/` |

The common thread in all these bugs is that **each side looks correct on its own, and the problem only becomes visible when both sides are examined together**. Therefore, the first principle of QA agent design is "read both sides simultaneously."
