# Shared Tracker Examples

Write the selected plain key/value content to `.scratch/.tracker`, not this Markdown wrapper and not `docs/agents/harness-tracker.md`. Validate against the installed `to-issues/references/tracker-config.md` before use.

## GitHub

```text
provider: github
target: owner/repository
```

## Jira with Confluence

```text
provider: jira
target: your-company.atlassian.net/PROJ
spec-target: your-company.atlassian.net/wiki/spaces/ENG
```

Replace illustrative targets with user-selected identifiers accepted by the connected tool.

## Local

```text
provider: local
```

Only include `ready-label` when configured by the user and supported by the shared contract. Never store secrets, model settings, explanation preferences, or execution state here.
