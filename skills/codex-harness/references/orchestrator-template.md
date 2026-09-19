# Orchestrator Generation Guide

Use `references/schemas/agent-orchestrator.template.md` as the generated skill body. Replace its name, description, role table, and completion criteria with the project's actual values.

## Runtime bundle

Copy only the following files alongside that generated SKILL.md, preserving paths relative to its root:

| Source relative to this meta-skill | Destination relative to generated skill |
| --- | --- |
| `references/project-policy.md` | `references/project-policy.md` |
| `references/orchestrator-procedures.md` | `references/orchestrator-procedures.md` |
| `references/schemas/models.md` | `references/schemas/models.md` |

Resolve source paths from the installed meta-skill directory, not from the user's project working directory. Use the active file-editing tools to create the bundle. Verify each generated reference exists.

The publication skills are external dependencies. Report their absence before publishing; do not copy references to the maintainer's home directory into a generated skill.

## Execution

The main Orchestrator reads the selected work record and project artifacts, delegates to native Codex subagents where useful, verifies results, and records meaningful progress. Workers report directly back to it. Hierarchical role names do not grant nested-spawn permissions.

Resume from the issue/spec, comments, actual artifacts, and relevant checks. For issue-free work, use the conversation and optional handoff notes. Do not infer progress from old internal state files.

## Boundaries

Do not generate a State Manager, a local execution database, a state CLI, or mandatory scratch files. Project-specific workflow order may be described in the generated skill or spec without requiring a separate workflow parser.

Do not silently close issues when implementation finishes. Update the current work record rather than mirroring it into a second authority.
