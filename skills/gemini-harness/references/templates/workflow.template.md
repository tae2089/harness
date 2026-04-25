<!-- 참고 패턴 (선택): fan_out_fan_in, pipeline 등 사용된 패턴 나열. 실행에 영향 없음. -->
<!-- 예: gather=fan_out_fan_in, refine=producer_reviewer                              -->

## Stage 정의

<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
<!-- 계층 구조: Stage(사용자 승인) → Phase(자동 전환) → Agent(실행자)              -->
<!-- 단순: Stage 1개("main") + Phase 1개("main")                                   -->
<!-- 다단계: Stage 2개 이상. 각 Stage는 Phase 1개 이상 포함. Phase는 패턴 1개.     -->
<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->

### Stage 1: {{STAGE_1_NAME}}
<!-- 단순이면 "main", 다단계이면 의미 있는 이름 (예: "gather", "design") -->

- 종료 조건: 모든 phase 완료
- 다음 stage: {{STAGE_2_NAME_OR_done}}
  <!-- 단순이면 "done". 다단계이면 다음 stage 이름. -->
- 사용자 승인 게이트: {{필요/없음}}
  <!-- 마지막 stage이거나 단순 워크플로우면 "없음". 중간 stage면 "필요". -->

#### Phase 1: {{PHASE_1_NAME}}
<!-- 단순이면 "main". 다단계이면 의미 있는 이름 (예: "research", "requirements") -->

- 패턴: {{PHASE_1_PATTERN}}
  <!-- 7대 기본 패턴 중 하나: pipeline | fan_out_fan_in | expert_pool |
       producer_reviewer | supervisor | hierarchical | handoff -->
- 활성 에이전트: [{{@AGENT_1}}, {{@AGENT_2}}]
  <!-- .gemini/agents/{name}.md 파일명과 일치해야 함 -->
- 종료 조건: {{VERIFIABLE_EXIT_CONDITION}}
  <!-- 예: `_workspace/tasks/task_*.json` 모두 status=done -->
  <!-- 예: `_workspace/output.md` 파일 존재 -->
  <!-- 예: `_workspace/verdict.json`의 verdict=PASS -->
- 다음 phase: {{PHASE_2_NAME_OR_done}}
  <!-- 같은 stage 내 다음 phase 이름 또는 "done" -->
- 최대 반복 횟수: {{MAX_ITERATIONS}}
  <!-- 비루프 패턴(pipeline, fan_out_fan_in, expert_pool)은 1 -->
  <!-- 루프 패턴(producer_reviewer, supervisor)은 3 이하 권장 -->

<!-- 같은 Stage 내 Phase 추가 필요 시 아래 블록 복사 -->
<!-- #### Phase 2: {{PHASE_2_NAME}}
- 패턴: {{PHASE_2_PATTERN}}
- 활성 에이전트: [{{@AGENT_3}}]
- 종료 조건: {{VERIFIABLE_EXIT_CONDITION_2}}
- 다음 phase: {{PHASE_3_NAME_OR_done}}
- 최대 반복 횟수: {{MAX_ITERATIONS_2}}
-->

<!-- 다단계: Stage 2 이상 필요 시 아래 블록 복사. 단순 워크플로우는 삭제. -->
<!-- ### Stage 2: {{STAGE_2_NAME}}

- 종료 조건: 모든 phase 완료
- 다음 stage: done
- 사용자 승인 게이트: 없음 (마지막 stage)

#### Phase 1: {{PHASE_1_NAME}}
- 패턴: {{STAGE_2_PHASE_1_PATTERN}}
- 활성 에이전트: [{{@AGENT_3}}, {{@AGENT_4}}]
- 종료 조건: {{VERIFIABLE_EXIT_CONDITION}}
- 다음 phase: done
- 최대 반복 횟수: {{MAX_ITERATIONS}}
-->
