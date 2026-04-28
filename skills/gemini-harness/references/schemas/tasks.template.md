<!--
tasks.md schema — Main agent sole writer. Aggregates from _workspace/tasks/task_*.json via GLOB + ATOMIC_WRITE.
Workers DO NOT modify this file directly — race condition on parallel writes.

Columns:
- ID:            Unique row id (matches task_*.json `id` field minus prefix, or sequential).
- Agent:         @agent-name (matches task_*.json `agent`).
- Task:          Brief task description (one line).
- Status:        todo | in-progress | done | blocked  (mirrors task_*.json `status`).
- Evidence:      Verifiable predicate from task_*.json `evidence` (only when status=done).
- Artifact Path: From task_*.json `artifact` (deliverable file path).
-->

| ID | Agent | Task | Status | Evidence | Artifact Path |
|----|-------|------|--------|----------|---------------|
| 1  |       |      | todo   | -        |               |
