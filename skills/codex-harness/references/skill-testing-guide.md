# Codex Harness Verification

Separate static generation checks, simulated workflow evaluation, and live integration. Passing a text check is not proof that models, permissions, or remote publication work.

## Static generation checks

- Render the worker template with representative role inputs and parse TOML.
- Check every role against schemas/models.md; default effort is medium.
- Render the orchestrator skill in an isolated directory with the exact three-file bundle from orchestrator-template.md.
- Resolve every local reference from the generated skill root.
- Check frontmatter and unresolved placeholders.
- Ensure generation requires no state CLI, local task database, or State Manager.
- Verify AGENTS.md preserves unrelated instructions and contains the selected domain/familiarity profile.

## Behavioral scenarios

| Scenario | Expected behavior |
| --- | --- |
| Normal work | Read the selected record, implement, verify, publish a concise outcome; leave issue open without closure instruction |
| Resume after interruption | Read issue/spec/comments and actual files, reuse still-valid work, identify remaining action |
| Stale completion comment | Inspect current artifacts/checks rather than trusting the comment |
| Reviewer rejection | Return evidence to producer, make a bounded correction, reverify |
| New natural-language task | Ask existing/new/no issue once if not already specified |
| Explicit no issue | No tracker prerequisite, ticket creation, or required local progress files |
| Explicit issue reference | Read that issue; no duplicate creation or repeated selection question |
| Local provider | Update the existing local ticket's progress, not a separate task database |
| Jira with spec-target | Use shared Confluence plus normal parent-issue contract, not an Epic per run |
| Publication failure | Disclose failed update and preserve results; do not claim sync or silently duplicate |
| Retry publication | Read existing remote content before retrying to avoid duplicate comments |
| Closure requested earlier | Verify completion, honor that instruction and applicable safety rules without redundant preference questions |
| Mixed audience expertise | Explain unfamiliar terms; preserve technical rigor and user overrides |
| Parallel workers | Isolate ownership; workers report to main without independent issue mutations |
| Legacy generated project | Preserve old user artifacts; stop requiring retired machinery without automatic cleanup |

Use mock publication tools or isolated fixtures for evaluation unless live writes were explicitly authorized. Record observed outputs and exact failed expectations, not only expected behavior.

For prompt comparisons, run the same representative work with the candidate and baseline instructions, compare correctness, scope, verification quality, time, and tool use. Use only metrics actually available. Temporary evaluation reports are optional artifacts, not a production state store.

Live validation additionally checks model availability, agent discovery, publication dependency/tool access, and safe execution in the target environment. If unavailable or not run, report that limitation.
