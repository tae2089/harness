# Security Policy

## Supported Versions

| Branch / tag       | Security fixes |
| ------------------ | -------------- |
| `main` (latest)    | ✅ Yes          |
| Older tagged releases | ❌ No — upgrade to `main` |

This project ships as a Gemini CLI skill bundle (markdown + JSON schema files), not a compiled binary. There is no version matrix with conflicting patch lines; security fixes land on `main` and are tagged on the regular biweekly cadence (P0 fixes cut an off-schedule patch release).

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security reports.**

Use GitHub's built-in **Private Vulnerability Reporting**:

1. Go to the **Security** tab of this repository.
2. Click **"Report a vulnerability"**.
3. Fill in the advisory form — describe the issue, affected files/logic, and (if known) a proof-of-concept or reproduction steps.

GitHub keeps the report private between you and the maintainer until a fix is published.

### Response SLA

| Milestone                      | Target  |
| ------------------------------ | ------- |
| Initial acknowledgement        | **< 7 days**  |
| Status update (triage/confirm) | **< 14 days** |
| Patch / mitigation             | **< 30 days** |

If you do not receive acknowledgement within 7 days, please follow up on the same advisory thread.

---

## Scope

### In scope

- Logic in `skills/gemini-harness/SKILL.md` or `references/` that could cause unintended **file writes**, **tool invocations**, or **prompt injection** when the skill is executed by Gemini CLI.
- Schema files (`references/schemas/`) that could bypass validation and allow malformed `workflow.md` or `checkpoint.json` to execute unsafe agent instructions.
- Any supply-chain concern with this repository itself (e.g., malicious commits to `main`).

### Out of scope

- Vulnerabilities in Gemini CLI itself — report those to Google.
- Issues that require the attacker to already have write access to the target project's `_workspace/` directory.
- Social-engineering attacks on the skill description triggers.

---

## Disclosure Policy

Once a fix is merged and released, we will publish a GitHub Security Advisory with:

- CVE (if applicable)
- Affected versions / files
- Description of the vulnerability
- Credit to the reporter (unless you prefer to remain anonymous)

---

## Credits

We appreciate responsible disclosure. Reporters who follow this policy will be credited in the Security Advisory unless they request anonymity.
