# Shared Project Policy

Apply this policy in the meta-skill and bundle it into each generated orchestrator skill. The selected work record, actual deliverables, and verification evidence guide execution and resumption.

## Request and issue selection

1. Accept the user's natural-language request. Do not require an issue number or URL, or autonomously choose backlog work unless the user requests it.
2. For actionable work, reuse an explicit choice already supplied. Otherwise ask one question offering: connect an existing issue, create a new issue, or proceed without an issue. Pure questions and lookups need no ticket prompt.
3. Existing issue: obtain an unambiguous reference, read its requirements and completion criteria, and use it without creating a duplicate. If the request conflicts with the issue, clarify the intended scope before changing that scope.
4. New issue: define one work unit with verifiable completion criteria per issue. Agent research, implementation, review, and retries are internal steps, not individual issues. Use the `to-issues` skill if available for ticket publication; use `to-spec` if available when a spec is needed. Selecting a new issue authorizes preparing it; follow the publication skill's preview and applicable approval requirements.
5. No issue: perform the requested work without creating a remote issue or local ticket. Do not make a tracker file a prerequisite for this path.
6. Preserve the choice and issue/document references in the conversation and selected work record across follow-ups and resume. For issue-free work, create an optional handoff note only when useful; no local ticket or execution database is required.
7. At meaningful milestones, update the selected issue's comments and applicable nonterminal status with progress, verification evidence, blockers, and next action. For a local tracker, update the same ticket's progress section. Preserve human-authored content and follow applicable publication rules. Workers return results to the main Orchestrator; they do not publish independently.
8. Close a GitHub issue or transition a Jira issue to a completed state only when the user requests it. A prior explicit instruction to close after successful verification counts; never infer closure permission from an agent report or implementation completion.

## Shared tracker and documents

Reuse `.scratch/.tracker` exactly as `to-spec` and `to-issues` do. Do not create `.source/.tracker`, `docs/agents/harness-tracker.md`, or a second tracker configuration. Do not put model or explanation settings in this file.

The shared format is one `key: value` per line:
- `provider`: required; `local`, `github`, `gitlab`, or `jira`.
- `target`: required for remote providers; forbidden for local.
- `ready-label`: optional; apply only if configured. Do not create labels implicitly.
- `spec-target`: optional, Jira only; selects Confluence for specs.
- Reject unknown or duplicate keys, empty values, and malformed lines. Never store or display secrets.

Read the installed `to-issues/references/tracker-config.md` before publishing, including when using `to-spec`. These skills are external dependencies, not bundled in this repository. If the required skill or contract is unavailable, report the missing dependency and keep any draft local without claiming publication or silently inventing another contract. No-issue execution remains available.

| Configuration | Spec destination | Work tickets |
| --- | --- | --- |
| GitHub | Issue | GitHub issues |
| Jira without `spec-target` | Normal issue | Jira issues |
| Jira with `spec-target` | Confluence page linked from a normal parent issue | Jira issues |
| GitLab | Issue | GitLab issues |
| Local | `.scratch/<feature-slug>/spec.md` | `.scratch/<feature-slug>/issues/` |

Use the same publication destination for durable design/spec documents; do not leave their sole copy in `_workspace/` or replace them with a stream of findings comments. Do not create an Epic per harness run.

Missing configuration follows the shared skills' explicit local fallback, including their preview before creating `provider: local`. Do not infer a destination from the Git remote. Preserve malformed or unavailable remote configuration; apply the publication skill's failure policy. After partial remote success, report created references and stop publication instead of duplicating them locally. Do not claim successful publication on a network/authentication failure.

Keep shared tracker configuration and local published documents/tickets in version control. Optional `_workspace/<task>/` scratch notes stay out of version control. No mandatory task JSON, checkpoint, progress list, state CLI, or State Manager is generated.

On resume, read the selected work record and relevant comments, then inspect actual code, deliverables, and verification results before choosing the remaining work. Do not treat comments as proof of completion. This is evidence-based continuation, not exact internal-step replay. With no issue, use the conversation and actual files; ask for missing context when needed.

## Explanation profile for AGENTS.md

Before generating the project instructions:
1. Reuse an existing audience profile or an explicit preference from the conversation.
2. If missing, ask for domains and familiarity. Offer suggested descriptions (beginner / ELI5, practitioner, specialist) and allow free text such as "senior backend engineer, frontend beginner." Allow different levels by domain.
3. Write the chosen profile into AGENTS.md, preserving unrelated instructions. Do not retain template placeholders or invent expertise.
4. In familiar domains, prioritize evidence and tradeoffs; in unfamiliar domains, define necessary terms and use concrete examples.
5. A user's explicit explanation-level request overrides the profile for that task. Explanation level never reduces code quality, verification, or disclosure of material constraints and risks.

## Acceptance scenarios

- Natural-language implementation request with no issue choice: ask existing/new/no issue once.
- Explicit issue URL or "without an issue": proceed on that path without asking again.
- Question or file lookup: answer without creating a ticket or prompting for one.
- New issue with several agents and retries: retain one issue for the work unit.
- Resume the same work unit: reuse its recorded issue choice and references.
- Existing issue unavailable: report the access problem; do not fabricate its requirements or create a replacement.
- Implementation finishes: selected issue remains open unless closure was requested.
- Jira with `spec-target`: use the shared Confluence-plus-normal-issue contract, not an Epic.
- Missing publication dependency or partial publication failure: disclose the gap and existing references; do not claim success.
- Existing explanation profile: preserve it; a new profile supports mixed domain expertise and explicit ELI5 overrides.
