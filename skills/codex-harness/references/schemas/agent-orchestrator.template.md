---
name: {{SKILL_NAME}}
description: "{{DESCRIPTION}}"
---

# {{SKILL_NAME}}

## Roles

| Agent | Responsibility | Definition |
| --- | --- | --- |
{{AGENT_TABLE}}

Use the explicit model and effort policy in `references/schemas/models.md`. The main Orchestrator uses `gpt-6-astra` with `medium` effort unless the user overrides it; this skill cannot switch the active session model.

## Work policy

Load `references/project-policy.md` before actionable work. Accept natural-language requests. Reuse the user's existing/new/no-issue choice and the project's AGENTS.md explanation profile.

Share `.scratch/.tracker` with the installed `to-spec` and `to-issues` skills. Do not create issues per agent or retry. Missing publication dependencies must be reported; issue-free work remains possible.

## Execution

Follow `references/orchestrator-procedures.md`:
1. Read the selected work record and inspect current artifacts.
2. Establish remaining work and completion criteria.
3. Execute directly or delegate bounded tasks to selected native Codex subagents.
4. Verify returned artifacts and record meaningful progress, evidence, blockers, and next action.
5. Report completion; close the selected issue only on user request.

Only the main Orchestrator spawns subagents. Workers report directly back; no separate agent-team runtime or local execution-state engine is required.

## Completion criteria

{{COMPLETION_CRITERIA}}

## Resume and failure

Read the issue/spec and relevant comments, then verify them against actual artifacts and tests. Reuse completed work that is still valid. For issue-free work, use the conversation and an optional handoff note. Ask for missing context rather than guessing.

On failure, report the evidence and next action. Do not restart completed work or repeat the same failed action without new evidence. Report publication failures separately from implementation results.

## Verification scenarios

- Normal: finish the requested work, verify the result, update the selected work record, leave closure to the user.
- Resume: read the record and current artifacts; continue remaining work without replaying already valid work.
- Error: use reviewer evidence to make a bounded correction, reverify, and report the outcome.
- No issue: execute without creating a ticket or requiring tracker configuration.
