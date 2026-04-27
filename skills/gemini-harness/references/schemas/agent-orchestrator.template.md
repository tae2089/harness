<!--
ORCHESTRATOR AGENT TEMPLATE — 변수 치환 후 `.gemini/skills/{harness-name}/SKILL.md`로 저장.
오케스트레이터는 agent .md가 아닌 skill SKILL.md 형태로 생성된다.
모델 ID SoT: references/schemas/models.md (변경 시 반드시 models.md 먼저 확인)

치환 변수:
  {{SKILL_NAME}}        kebab-case 스킬 이름 (예: sso-dev-flow)
  {{DESCRIPTION}}       pushy 설명 + 트리거 키워드 + 후속 작업 키워드
  {{PLAN_NAME}}         _workspace 하위 디렉터리 이름 (예: sso)
  {{AGENT_TABLE}}       가상 팀 테이블 행 (반복)
  {{STAGE_STEP_SUMMARY}} workflow.md Stage/Step 구조 요약

오케스트레이터는 invoke_agent 권한 보유 — 워커 에이전트는 금지.
모델은 pro 티어 사용 (복잡 추론·다단계 조율 담당).
-->

---

name: {{SKILL_NAME}}
description: "{{DESCRIPTION}}. 후속 작업(수정/보완/재실행) 시에도 반드시 이 스킬 사용."

---

# Skill: {{SKILL_NAME}} Orchestrator

## 가상 팀

| 에이전트        | 역할 | 산출물 |
| --------------- | ---- | ------ |
| {{AGENT_TABLE}} |

> 오케스트레이터 모델: `gemini-3.1-pro-preview` (설계·추론 담당). 모델 ID 확인: `references/schemas/models.md`

## 워크플로우

### Step 0: 컨텍스트 확인 (Durable Execution)

`references/orchestrator-template.md` Step 0 절차 적용. `_workspace/checkpoint.json` status별 분기:

- `in_progress` → Resume (현재 stage/step부터 재개)
- `completed` → 부분 재실행 or 신규 실행 사용자 확인
- 미존재 → 신규 실행 (Step 1로 진행)

### Step 1: 초기화

1. `_workspace/{{PLAN_NAME}}/`, `_workspace/tasks/`, `_workspace/_schemas/` 디렉터리 생성.
2. **스키마 동기화** — `references/schemas/` 파일 5종 + 에이전트 템플릿 3종을 `_workspace/_schemas/`로 `read_file` → `write_file` 복사 (`references/orchestrator-template.md` Step 1.3 참조).
3. `workflow.md` 작성 (`_workspace/_schemas/workflow.template.md` 변수 치환):
   {{STAGE_STEP_SUMMARY}}
4. `findings.md` 초기화 (`_workspace/_schemas/findings.template.md` 기반).
5. `tasks.md` 초기화 (`_workspace/_schemas/tasks.template.md` 기반).
6. `checkpoint.json` 생성 (`_workspace/_schemas/checkpoint.schema.json` 스키마 준수):
   ```json
   {
     "plan_name": "{{PLAN_NAME}}",
     "status": "in_progress",
     "current_stage": "{첫 Stage 이름}",
     "current_step": "{첫 Step 이름}",
     "active_pattern": "{첫 Step 패턴}"
   }
   ```
7. **workflow.md 스키마 검증** — 6 필수 필드 + 명명 컨벤션(placeholder 금지) + 검증 가능 종료 조건 + 패턴 enum. 위반 시 HALT (`references/orchestrator-template.md` Step 1.8 참조).
8. **workflow.md 사이클 검증** (스키마 검증 통과 후).

### Step 2: Step 실행 루프

`references/orchestrator-template.md` Step 2 표준 절차 적용. 패턴별 에이전트 호출, 종료 조건 검사, Stage 게이트 처리, checkpoint.json 갱신.

## 에러 핸들링

Zero-Tolerance: 에이전트 실패 → 최대 2회 재시도(총 3회) → 미해결 시 `task_*.json` status=Blocked + `ask_user`. 임의 Skip 절대 금지.
