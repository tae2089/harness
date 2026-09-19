# Supervisor: Code Migration

1. The user authorizes a defined migration scope. The main Orchestrator selects ready work from that scope and assigns non-overlapping files to Developers.

2. Workers return changed files and checks. The main integrates results and records completed areas, blockers, and next action on the selected work record.

3. On resume, inspect the diff and tests before treating previously reported files as migrated. Do not automatically select unrelated backlog items.

Use the shared project policy and runtime procedure. Native Codex subagents return results to the main Orchestrator. Scratch notes are optional; actual artifacts and verification evidence determine completion.
