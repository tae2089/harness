# Generation Templates

This directory retains its existing path for template consumers; it no longer contains runtime state schemas or a state CLI.

| File | Purpose |
| --- | --- |
| `models.md` | Explicit role model and effort policy |
| `agent-worker.template.toml` | Worker definition rendered to .codex/agents/{name}.toml |
| `agent-orchestrator.template.md` | Orchestrator skill body |

Render every placeholder with project-specific content and validate TOML/frontmatter. Updating templates does not automatically update existing project agents.

The generated runtime bundle consists of the model policy plus project-policy.md and orchestrator-procedures.md from the parent references directory. See the main skill's Phase 4 for exact source and destination paths.

Existing project state artifacts are user work. Stop referencing them after an explicit migration, but do not delete or rewrite them automatically.
