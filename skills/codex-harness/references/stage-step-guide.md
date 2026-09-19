# Planning Work Without a Local Execution Engine

Describe the order of work in the selected spec, issue, or generated skill. A separate workflow file and stage parser are not required.

For each meaningful work unit, identify its deliverable, dependencies, responsible role, and observable acceptance criteria. Agent invocations and retries remain internal to that work unit.

Example: design authentication boundaries → implement the approved behavior → independent review → run relevant tests → publish the outcome. Parallelize only independent work.

Stage names are descriptive labels, not machine state. On resume, read the work record and inspect the artifacts to establish what remains. A stage label or prior completion comment does not replace verification.

Keep user review gates when the user or project requires them. Do not add approval gates for routine, already authorized steps. Never interpret implementation completion as permission to close an issue.
