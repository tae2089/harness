# Scoped Harness Changes and Migration

| Request | Change | Validate |
| --- | --- | --- |
| Add or refine a role | Agent TOML, role roster, relevant scope instructions | TOML, model/effort, ownership |
| Change execution order | Generated skill/spec procedure | Dependencies, outputs, acceptance criteria |
| Change tracker | Shared publication contract and explicitly selected target | No duplicate configuration or implicit migration of issues |
| Change explanation profile | Relevant AGENTS.md section | Preserve other instructions and quality requirements |
| Resume work | Read selected record and actual artifacts | Remaining work and evidence, not a stored step pointer |
| Remove old state machinery | Generated references, role roster, and execution instructions | No runtime dependency on retired machinery |

## Existing projects

Inspect before migrating. Existing local reports and state artifacts may contain user work; leave them untouched unless cleanup is explicitly requested and satisfies project safety rules.

Remove the old state-management role from newly generated rosters and stop invoking it. Do not silently overwrite or delete an existing agent file, reset work, replay all steps, or publish old internal tasks as new issues.

If useful information exists only in legacy artifacts, read it as historical evidence, compare it with current code/tests, and summarize verified progress on the selected record within the user's publication choice. Do not present old status as current proof.

Preserve issue/document references and the user's no-issue choice. Changing publication targets does not authorize duplicating or moving existing work records.
