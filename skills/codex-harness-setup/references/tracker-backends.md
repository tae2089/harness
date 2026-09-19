# Shared Tracker Backends

Use the installed `to-issues/references/tracker-config.md`, shared by `to-spec`, as the publication contract. Do not maintain a second set of shell/API sequences here.

- GitHub: connected tool, otherwise an already-authenticated `gh`.
- GitLab: connected tool, otherwise an already-authenticated `glab`.
- Jira: connected Jira tool; optional Confluence destination via `spec-target`.
- Local: shared `.scratch/<feature-slug>/` documents and tickets.

Do not install or authenticate a CLI implicitly, request secret values, or infer a target from Git remotes. Report missing dependencies and apply the shared publication skill's fallback/partial-success rules.

A work unit has one issue with completion criteria. Worker results describe internal execution and return directly to the main Orchestrator; they are not individually published. Reuse explicit issue references, preserve human-authored content, and record meaningful results rather than mirroring every state operation. Use native relationships when supported, otherwise explicit references as the shared contract prescribes.

No automatic issue closure on implementation completion. Close only on user request after checking the applicable completion criteria. No Epic-per-plan bootstrap, implicit label creation, automatic replay queue, or per-tool-call comment stream.

Full policy: `../../codex-harness/references/project-policy.md`.
