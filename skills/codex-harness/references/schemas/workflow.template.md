<!--
workflow.md schema — Stage(상위 이슈/Jira Issue) → Step(하위 이슈/Jira Sub-issue) hierarchy. Static declaration.
MANDATORY fields per block (Zero-Tolerance: missing field → HALT).

NAMING CONVENTION (Jira issue title style — MANDATORY):
- Stage·Step name MUST be a deliverable-meaningful noun phrase in kebab-case.
- Format: ^[a-z][a-z0-9-]*$  (lowercase letter start, digits/hyphens allowed)
- BANNED placeholders: main, step1, task, work, default, phase1, stage1, generic
- ALLOWED examples: sso-integration, payment-flow, requirements-gathering, api-design, load-test
- Single-Stage / single-Step cases STILL follow this rule — no `main` shortcut.

Stage block required fields:
- 종료 조건:           "모든 step 완료" or verifiable predicate
- 다음 stage:          {next_stage_name} | done
- 사용자 승인 게이트:   필요 | 없음 (마지막 stage)

Step (Task) block required fields:
- 패턴:               pipeline | fan_out_fan_in | expert_pool | producer_reviewer | supervisor | hierarchical | handoff
- 활성 에이전트:       [@name1, @name2, ...]   (must match .gemini/agents/{name}.md)
- 종료 조건:           VERIFIABLE PREDICATE (file exists / JSON field value / iterations ≥ N)
                      BANNED: "QA 승인", "충분히", "완료되면", "만족" (LLM 자의 해석)
- 다음 step:          {next_step_name} | done
- 최대 반복 횟수:      integer (non-loop=1, loop ≤3)

Symbolic placeholders allowed in 활성 에이전트 (e.g. [@선택된_전문가]) — main resolves
at runtime via checkpoint.json shared_variables. workflow.md itself is NOT modified.
-->

<!-- 참고 패턴 (선택, 실행에 영향 없음): {STAGE_1}={pattern}, {STAGE_2}={pattern} -->

## Stage 정의

### Stage 1: {{STAGE_1_NAME}}
- 종료 조건: 모든 step 완료
- 다음 stage: {{STAGE_2_NAME_OR_done}}
- 사용자 승인 게이트: {{필요/없음}}

#### Step 1: {{STEP_1_NAME}}
- 패턴: {{PATTERN}}
- 활성 에이전트: [{{@AGENT_1}}]
- 종료 조건: {{VERIFIABLE_PREDICATE}}
- 다음 step: {{STEP_2_NAME_OR_done}}
- 최대 반복 횟수: {{N}}

<!-- Add more Step blocks within Stage 1 by copying the above. -->

<!-- Add Stage 2+ by copying the Stage block. Single-stage workflow: omit. -->
<!--
### Stage 2: {{STAGE_2_NAME}}
- 종료 조건: 모든 step 완료
- 다음 stage: done
- 사용자 승인 게이트: 없음 (마지막 stage)

#### Step 1: {{STEP_1_NAME}}
- 패턴: {{PATTERN}}
- 활성 에이전트: [{{@AGENT_2}}, {{@AGENT_3}}]
- 종료 조건: {{VERIFIABLE_PREDICATE}}
- 다음 step: done
- 최대 반복 횟수: {{N}}
-->
