# Example Role Combinations

Use only the roles needed for the requested work. The main Orchestrator coordinates native Codex subagents, publishes consolidated progress, and honors the selected issue mode.

| Work | Suggested roles | Pattern |
| --- | --- | --- |
| Independent competitor research | Researchers, Analyst | Fan-out / fan-in |
| Backend feature | Architect, Developer, Reviewer, QA | Pipeline plus producer/reviewer |
| Full-stack feature | Architect, frontend/backend Developers, Reviewer | Hierarchical decomposition with main-owned spawning |
| Many similar migrations | Developer workers, QA | Supervisor within the authorized work list |
| Incident investigation | Analyst, relevant specialist, Operator | Handoff |

Role names do not imply unrestricted permissions. Explicit model/effort assignments are defined in schemas/models.md.

Examples:
- [Parallel research](examples/team/01-fan-out-fan-in.md)
- [Producer/reviewer](examples/team/02-producer-reviewer.md)
- [Supervisor](examples/team/03-supervisor.md)
- [Hierarchical](examples/team/04-hierarchical.md)
- [Handoff and resume](examples/team/05-handoff-persistence.md)
- [SSO harness](examples/full-bundle/sso-style.md)
