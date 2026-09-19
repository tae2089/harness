# Role Model Policy

This file is the source of truth for model assignments when generating Codex agent TOML files. These are project defaults, not benchmark guarantees. Set both `model` and `model_reasoning_effort` explicitly; do not inherit an unrelated session model.

| Role | Model | model_reasoning_effort |
| --- | --- | --- |
| Orchestrator | `gpt-6-astra` | `medium` |
| Architect / Planner | `gpt-6-astra` | `medium` |
| Researcher | `gpt-5.6-terra` | `medium` |
| Analyst | `gpt-5.6-sol` | `medium` |
| Coder / Developer | `gpt-5.6-sol` | `medium` |
| Reviewer | `gpt-6-astra` | `medium` |
| QA Inspector | `gpt-5.6-sol` | `medium` |
| Operator / Deployer | `gpt-5.6-sol` | `medium` |

## Generation and updates

- Resolve each agent's responsibility to a row. For a combined role, make the primary responsibility explicit before choosing its model.
- All supported roles use `medium` by default. The Orchestrator handles progress updates; no separate state-management agent is generated.
- Verify model and effort availability in the target Codex environment. API documentation alone does not establish account access. If unavailable, report the role and ask for a replacement; do not silently substitute.
- Do not automatically raise effort to `high`, `xhigh`, or `max` on retries. Apply an explicit user override when supplied.
- The main Orchestrator session must use its configured model and effort. A Markdown skill cannot switch the active session; report a mismatch rather than claiming the model changed.
- Updating this registry does not rewrite generated agents. Update bundled examples and templates together, and update existing project agents only within the requested scope.

## Sources

Assignments agreed on 2026-09-19, informed by official model and subagent guidance:
- [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra)
- [GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
- [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra)
- [Codex subagents](https://developers.openai.com/es-419/docs/agent-configuration/subagents)
