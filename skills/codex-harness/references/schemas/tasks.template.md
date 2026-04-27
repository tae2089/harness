<!--
tasks.md schema — Main agent sole writer. Aggregates from _workspace/tasks/task_*.json via GLOB + apply_patch.
Workers DO NOT modify this file directly — race condition on parallel writes.

Columns:
- ID:            Unique row id (matches task_*.json `id` field minus prefix, or sequential).
- 에이전트:       @agent-name (matches task_*.json `agent`).
- 작업 내용:      Brief task description (one line).
- 상태:           todo | in-progress | done | blocked  (mirrors task_*.json `status`).
- Evidence:      Verifiable predicate from task_*.json `evidence` (only when status=done).
- 산출물 경로:    From task_*.json `artifact` (deliverable file path).
-->

| ID | 에이전트 | 작업 내용 | 상태 | Evidence | 산출물 경로 |
|----|---------|----------|------|----------|------------|
| 1  |         |          | todo | -        |            |
