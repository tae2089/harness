# Subagent Orchestration Real-world Examples (Gemini CLI)

5 architecture pattern real-world examples. **In the Gemini CLI environment, direct communication between subagents is not possible**, so all team communication is brokered by the main agent via `_workspace/findings.md` and `_workspace/tasks.md`.

> **Note:** Team APIs from Claude Code such as `TeamCreate`, `SendMessage`, and `TaskCreate` do not exist in Gemini CLI. Subagent invocation uses the **`invoke_agent` tool**, and parallel execution is implemented by specifying the **`wait_for_previous: false`** parameter.
> **Stage-Step structure required:** The orchestrator in every example reads `checkpoint.json` (`status`, `current_stage`, `current_step`) in Step 0 to determine the execution mode, and creates `workflow.md` in Step 1 (in Resume mode, reads the existing file). Example 1's orchestrator workflow is the reference implementation; all other examples follow the same pattern.

---

## Example Index

| #   | Pattern               | Domain Example        | Agent Count | Key Characteristics                                                   | File                                                                               |
| --- | --------------------- | --------------------- | ----------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 1   | Fan-out/Fan-in        | Research team         | 4           | Parallel investigation then integration, data conflict mediation      | [examples/team/01-fan-out-fan-in.md](examples/team/01-fan-out-fan-in.md)           |
| 2   | Producer-Reviewer     | Webtoon production    | 2           | PASS/FIX/REDO loop, full agent file example included                  | [examples/team/02-producer-reviewer.md](examples/team/02-producer-reviewer.md)     |
| 3   | Supervisor            | Code migration        | 1+N         | Runtime dynamic task allocation, tasks.md claim mechanism             | [examples/team/03-supervisor.md](examples/team/03-supervisor.md)                   |
| 4   | Hierarchical          | Full-stack app dev    | 5           | 2-level delegation, team lead mid-level coordination, full agent file example included | [examples/team/04-hierarchical.md](examples/team/04-hierarchical.md)               |
| 5   | Handoff + Persistence | System debugging      | 4           | [NEXT_AGENT] parsing, large log resumption                            | [examples/team/05-handoff-persistence.md](examples/team/05-handoff-persistence.md) |

### Pattern Selection Guide

| Situation                                                        | Recommended Pattern            |
| ---------------------------------------------------------------- | ------------------------------ |
| Parallel independent tasks followed by integration               | Fan-out/Fan-in (Example 1)     |
| Output quality needs to be raised through iterative review       | Producer-Reviewer (Example 2)  |
| Large-scale processing of homogeneous tasks, real-time progress tracking | Supervisor (Example 3)  |
| Heterogeneous domain team, 2-level specialization delegation needed | Hierarchical (Example 4)    |
| Unknown root cause, expert selection depends on analysis results | Handoff (Example 5)            |
| Large data processing with interruption/resume needed            | Handoff + Persistence (Example 5) |

---

## Artifact Pattern Summary

### Agent Definition Files

- Path: `.gemini/agents/{agent-name}.md` (project) or `~/.gemini/agents/{agent-name}.md` (user).
- Required YAML: `name`, `description` (pushy, including follow-up keywords), `kind: local`, `model` (orchestrator/Architect → `"gemini-3.1-pro-preview"`, worker → `"gemini-3-flash-preview"`), `tools` (must include `ask_user` and `activate_skill`).
- Recommended YAML: `temperature` (0.2~0.7 by role), `max_turns` (5~20).
- Required sections: core role, task principles, I/O protocol, collaboration protocol (Gemini CLI), error handling.

### findings.md Standard Section Structure

Standard sections initialized by the orchestrator in Phase 1:

| Section Name           | Purpose                                                      | Commonly Used Pattern                    |
| ---------------------- | ------------------------------------------------------------ | ---------------------------------------- |
| `[Key Insights]`       | Core summary of research and analysis results                | Fan-out/Fan-in                           |
| `[Key Keywords]`       | Common keywords for injection into agent prompts             | Fan-out/Fan-in                           |
| `[Shared Variables/Paths]` | Shared paths, API contracts, and persistence resume points between agents | All patterns                |
| `[Data Conflicts]`     | Records of conflicting information between agent outputs     | Fan-out/Fan-in, Supervisor, Handoff      |
| `[Change Requests]`    | Rework instructions                                          | Producer-Reviewer                        |
| `[Next Step Guidelines]` | Guidance on what the next agent should focus on            | Pipeline, Hierarchical                   |

Initialize only the sections needed for the pattern. Omit unused sections.

### tasks.md Basic Schema

Task list format registered by the orchestrator in Phase 1:

```
| ID | Task Name | Assigned Agent | Priority | Complexity | Status |
|----|-----------|---------------|----------|------------|--------|
| 1  | ...       | @migrator-1   | High     | Large      | Todo   |
```

- **Status values**: `Todo` → `In-Progress` → `Done` | `Blocked`
- **Main agent updates only**: Workers record only in `task_{agent}_{id}.json`. Main atomically updates tasks.md after collecting them.
- **Blocked items**: Mark the relevant row status as `Blocked` when calling ask_user.

### Skill File Structure

- Path: `.gemini/skills/{skill-name}/SKILL.md`.
- Large knowledge is split into `references/` (Progressive Disclosure).

### Orchestrator Skill

- Top-level skill that coordinates the entire team. Covers from Phase 0 (re-run detection) to Phase 5 (preservation and reporting).
- Template: see `references/orchestrator-template.md`.
- Direct communication between subagents is not possible — all collaboration is brokered via `findings.md`, `tasks.md`, and `checkpoint.json`.
- Declare Stage-Step in `_workspace/workflow.md` in Phase 1; read every cycle and invoke only the `active_agents` for the current step. On agent failure: maximum 2 retries (3 total) → if unresolved, `Blocked` + `ask_user`. Arbitrary skipping is absolutely prohibited.
