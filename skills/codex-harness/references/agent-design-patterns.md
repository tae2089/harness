# Codex Coordination Patterns

The main Orchestrator owns subagent spawning, integration, and work-record updates. A separate agent-team runtime is not required. Workers return results directly; no file-based message bus is required.

| Pattern | Use when | Coordination |
| --- | --- | --- |
| Pipeline | Outputs depend on earlier work | Run the next role after verifying its input |
| Fan-out / fan-in | Independent investigations or changes can proceed together | Spawn bounded workers, collect results, resolve contradictions |
| Expert pool | One specialist best matches a focused request | Select by responsibility; ask only if ambiguity changes scope |
| Producer / reviewer | A deliverable benefits from independent inspection | Producer returns artifacts; reviewer reports evidence; bounded corrections follow |
| Supervisor | Several work units need prioritization within authorized scope | Main selects ready work from the agreed issue/spec, not an invented backlog |
| Hierarchical | A broad objective needs decomposition | Team lead returns a plan; main spawns workers and integrates |
| Handoff | Findings determine the next useful role | Worker suggests next action; main decides and passes context |

Choose direct execution for work that does not benefit from delegation. Role count is not a quality target.

## Ownership and evidence

Give each worker an objective, acceptance criteria, relevant context, allowed files, dependencies, and verification. Avoid concurrent writes to the same files unless worktrees and integration ownership are explicit. Workers do not update shared issues; the main Orchestrator consolidates meaningful progress.

Check artifacts and tests before accepting completion. Progress belongs on the selected issue/local ticket or in the conversation for issue-free work. Refer to project-policy.md and orchestrator-procedures.md for resumption and publication failure behavior.

## Models and permissions

Use schemas/models.md for explicit role models and efforts. Models are assigned by responsibility, not pattern. Read-only analysis uses read-only access; writing and tests need the appropriate workspace permissions. Operational roles do not automatically receive unrestricted access.
