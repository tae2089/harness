# Findings: {plan_name}

<!--
findings.md schema — Main agent sole writer. All workers read via prompt injection.
Init: include only sections required by the active patterns (see table below).
Do NOT invent custom section names. Pattern → section mapping is fixed.

| Pattern                  | Required sections (in addition to [공유 변수/경로])                       |
|--------------------------|---------------------------------------------------------------------------|
| pipeline / hierarchical  | [다음 단계 지침]                                                          |
| fan_out / fan_out_fan_in | [핵심 통찰], [핵심 키워드], [데이터 충돌]                                 |
| producer_reviewer        | [변경 요청]                                                               |
| supervisor / handoff     | [데이터 충돌]                                                             |
| expert_pool              | [라우팅 근거]  (format: "- {agent}: {reason} (matching: {keyword})")     |

All patterns share: [공유 변수/경로].
-->

## [공유 변수/경로]
<!-- Required for all patterns. Workspace paths, API contracts, persistence resume points. -->
- 작업 디렉터리:
- 산출물 경로:

## [핵심 통찰]
<!-- fan_out / fan_out_fan_in only. Worker outputs synthesized by main. -->

## [핵심 키워드]
<!-- fan_out / fan_out_fan_in only. Common keywords injected into worker prompts. -->

## [데이터 충돌]
<!-- fan_out / supervisor / handoff. Conflicting outputs with sources cited. Never delete a side. -->

## [변경 요청]
<!-- producer_reviewer only. Reviewer's REJECT feedback for next producer iteration. -->

## [다음 단계 지침]
<!-- pipeline / hierarchical only. Hand-off guidance to next agent. -->

## [라우팅 근거]
<!-- expert_pool only. Format: "- @agent-name: {reason} (matching: {keyword})" -->
