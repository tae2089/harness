# Stage-Step 워크플로우 가이드

모든 하네스의 워크플로우 구조를 정의하는 가이드. `_workspace/workflow.md`에 Stage-Step 계층을 선언하여 오케스트레이터가 결정론적으로 실행하도록 한다. SKILL.md Step 2 또는 Step 5에서 참조한다.

---

## 목차

1. [개념 정의](#1-개념-정의)
2. [workflow.md 명세](#2-workflowmd-명세)
3. [checkpoint.json 스키마](#3-checkpointjson-스키마)
4. [Step·Stage 전환 프로토콜](#4-stepstage-전환-프로토콜)
5. [검증 가능한 종료 조건 패턴](#5-검증-가능한-종료-조건-패턴)
6. [Step별 에이전트 출입 통제](#6-step별-에이전트-출입-통제)
7. [워크플로우 예시 3종](#7-워크플로우-예시-3종)
8. [테스트 시나리오 6종](#8-테스트-시나리오-6종)

---

## 1. 개념 정의

### 3단계 계층 모델

모든 하네스는 **Stage → Step → Agent** 3단계 계층으로 구성된다.

| 계층 | 전환 주체 | 설명 |
|------|---------|------|
| **Stage** | 사용자 승인 게이트 | 최상위 작업 단위. 사용자 승인 후에만 전환. |
| **Step** | 오케스트레이터 자동 관리 | Stage 내 세부 작업 단위. 자동 전환. 각 step는 7대 기본 패턴 중 하나를 사용. |
| **Agent** | Step 내 실행자 | 실제 작업 수행. step의 `활성 에이전트` 목록으로 제어. |

`_workspace/workflow.md`에 Stage·Step 구조를 선언한다. 오케스트레이터는 항상 이 파일을 읽어 현재 stage와 step를 파악한다.

> **workflow.md는 정적 선언이다.** Step 1에서 한 번 생성되며, 실행 중 Stage·Step 구조가 변경되지 않는다. 에이전트 선택이 동적으로 결정되는 경우(예: `[@선택된_전문가]`) 해당 표기는 **런타임 심볼릭 플레이스홀더**다 — 오케스트레이터가 해당 Step 진입 시 `checkpoint.json`의 `shared_variables.selected_expert` 필드를 읽어 실제 에이전트명으로 치환한다. workflow.md 자체는 수정하지 않는다.
>
> **명명 규칙 구분:** `shared_variables`의 JSON 키는 `selected_expert` (영문 snake_case). workflow.md의 심볼릭 플레이스홀더는 `[@선택된_전문가]` (한글). 두 이름이 일치하지 않아도 무방 — 오케스트레이터가 `selected_expert` 값을 읽어 `@선택된_전문가` 자리에 치환하는 매핑 관계이므로 이름 형식은 구현자 재량이다.

### 단순 vs 다단계

| 유형 | Stage 수 | Step 수 | 사용 조건 |
|------|---------|---------|----------|
| **단순** | 1개(`main`) | 1개(`main`) | 단일 패턴으로 완결되는 작업 |
| **다단계** | 2개 이상 또는 한 Stage에 Step 2개 이상 | 복수 | 2단계 이상 협업 구조 + 종료 조건 명확 검증 가능 + 사용자가 Stage 게이트 개입 가능 |

---

## 2. workflow.md 명세

`_workspace/workflow.md`는 모든 하네스에 필수. Stage·Step 구조를 선언하며, 오케스트레이터가 매 사이클 읽는다.

> 실제 작성 시 `references/templates/workflow.template.md`를 복사해 변수만 치환하면 빠르다.

### 단순 워크플로우 예시 (stage 1 + step 1)

```markdown
<!-- 참고 패턴: fan_out_fan_in (실행에 영향 없음, 문서화 목적) -->

## Stage 정의

### Stage 1: main
- 종료 조건: 모든 step 완료
- 다음 stage: done
- 사용자 승인 게이트: 없음

#### Step 1: main
- 패턴: fan_out_fan_in
- 활성 에이전트: [@researcher-a, @researcher-b, @researcher-c]
- 종료 조건: `_workspace/tasks/task_*.json` 모두 status=done
- 다음 step: done
- 최대 반복 횟수: 1
```

### 다단계 워크플로우 예시 (stage 2 + step 여러 개)

```markdown
<!-- 참고 패턴: fan_out_fan_in → producer_reviewer (실행에 영향 없음, 문서화 목적) -->

## Stage 정의

### Stage 1: gather
- 종료 조건: 모든 step 완료
- 다음 stage: refine
- 사용자 승인 게이트: 필요

#### Step 1: research
- 패턴: fan_out_fan_in
- 활성 에이전트: [@researcher-trend, @researcher-data]
- 종료 조건: `_workspace/research/task_trend.json`, `task_data.json` 모두 status=done
- 다음 step: done
- 최대 반복 횟수: 1

### Stage 2: refine
- 종료 조건: 모든 step 완료
- 다음 stage: done
- 사용자 승인 게이트: 없음 (마지막 stage)

#### Step 1: draft-review
- 패턴: producer_reviewer
- 활성 에이전트: [@writer, @editor]
- 종료 조건: `_workspace/editor_verdict.json`의 verdict=PASS
- 다음 step: done
- 최대 반복 횟수: 3
```

### workflow.md 필드 작성 규칙

| 필드 | 작성 규칙 | 예시 |
|------|----------|------|
| `활성 에이전트` | Step 블록에서만 선언. `@name` 형식, `.gemini/agents/{name}.md`와 일치 | `[@writer, @editor]` |
| `종료 조건` | 검증 가능한 술어만 허용 (파일 존재, JSON 필드값, 수치 임계값) | `task_*.json` 모두 status=done |
| `다음 step` | 다음 step 이름 또는 `done` | `architecture` / `done` |
| `다음 stage` | 다음 stage 이름 또는 `done` | `validate` / `done` |
| `최대 반복 횟수` | 루프 패턴(Producer-Reviewer 등)에서 무한루프 방지 필수 | `3` |
| Stage `종료 조건` | `모든 step 완료` 또는 구체적 검증 가능 조건 | `모든 step 완료` |

---

## 3. checkpoint.json 스키마

> **정본은 `references/orchestrator-template.md` — "데이터 영속성 프로토콜" 섹션.** 전체 필드 설명 및 예시는 해당 파일 참조.

Stage-Step 워크플로우에서 추가로 필요한 필드: `current_stage`, `current_step`, `active_pattern`, `stage_history`, `step_history`, `stage_artifacts`. 모두 정본 스키마에 포함되어 있다.

---

## 4. Step·Stage 전환 프로토콜

### Step 전환 vs Stage 전환 비교

| 구분 | 전환 주체 | 사용자 승인 | checkpoint.json 갱신 |
|------|---------|-----------|---------------------|
| **Step 전환** | 오케스트레이터 자동 | 불필요 | `current_step`, `step_history`, `handoff_chain: []` |
| **Stage 전환** | 사용자 승인 후 오케스트레이터 | **필수** | `current_stage`, `current_step`(다음 Stage 첫 Step), `stage_history`, `handoff_chain: []` |

### Step 전환 프로토콜 (자동)

오케스트레이터가 매 사이클 수행하는 내부 루프. 순서 필수 준수.

1. `checkpoint.json`에서 `current_stage`, `current_step` 읽기.
2. `workflow.md`에서 해당 step 블록의 종료 조건 읽기.
3. 종료 조건 검증 (파일 스캔, JSON 필드 확인).
4. **미충족** → 현재 step 패턴의 활성 에이전트 호출 후 다음 사이클 대기.
5. **충족** → `다음 step` 확인:
   - 다음 step 이름 → checkpoint.json 즉시 갱신 → 같은 턴 내 다음 step 진입 허용.
   - `done` → Stage 전환 프로토콜 진행.

### Stage 전환 프로토콜 (승인 필수)

1. 현재 stage의 마지막 step가 `done`임을 확인.
2. 사용자에게 아래 형식으로 보고.
3. **승인 시:** checkpoint.json 갱신 (current_stage, current_step, stage_history, handoff_chain: []).
4. **거절 시:** checkpoint.json 변경 없음 → "어떤 부분을 수정할까요?" 질문 → 지정 step ATOMIC 롤백:
   - checkpoint.json 갱신: `current_step` ← 지정 step, `active_pattern` ← 해당 step 패턴, `handoff_chain: []`, `last_updated` ← NOW().
   - 해당 step 에이전트의 기존 task 파일 삭제: `_workspace/tasks/task_{해당_step_에이전트}_*.json`.
5. **[금지]** 승인과 같은 응답 턴에 다음 stage 에이전트 호출 금지.
6. **재진입:** 사용자가 "계속해" 등 전송 → 오케스트레이터 Step 0 재실행 → `status: "in_progress"` + 갱신된 `current_stage`·`current_step` 감지 → Step 2 진입해 새 Stage 첫 Step 즉시 시작.

### 사용자 승인 게이트 형식

```
Stage {현재 stage} 완료:
  Step {step-1}: {종료 조건} ✓
  Step {step-2}: {종료 조건} ✓

다음 Stage: {다음 stage}
  Step 목록: [{step-1}, {step-2}]
  첫 Step 활성 에이전트: {에이전트 목록}
  첫 Step 종료 조건: {조건}

진행할까요? [Y/N]
```

---

## 5. 검증 가능한 종료 조건 패턴

| 권장 (검증 가능) | 금지 (LLM 자의 해석) |
|---|---|
| `_workspace/tasks/task_*.json` 모두 status=done | "충분히 모였다" |
| `_workspace/critic_verdict.json`의 verdict=PASS | "검토가 만족스러움" |
| `_workspace/coverage.json`의 score ≥ 임계값 | "품질이 좋음" |
| 특정 파일 존재 (`_workspace/integrated.md`) | "통합이 끝남" |
| step_history의 해당 step iterations ≥ max_iterations | "충분히 반복했다" |

---

## 6. Step별 에이전트 출입 통제

Gemini CLI agent frontmatter는 커스텀 필드를 지원하지 않는다. 출입 통제는 **workflow.md의 step 블록 `활성 에이전트` 목록**으로 수행한다.

```
invoke_agent 호출 전 확인:
1. workflow.md에서 current_stage → current_step 블록 찾기.
2. 해당 step의 `활성 에이전트` 목록 읽기.
3. 호출 대상이 목록에 있으면 → invoke_agent 허용.
4. 목록에 없으면 → 호출 보류, 필요 시 사용자에게 보고:
   "@writer는 현재 step({current_stage}/{current_step})의 활성 에이전트가 아닙니다."
```

---

## 7. 워크플로우 예시 3종

| # | 도메인 | 패턴 조합 | Stage 수 | Step 수 | 파일 |
|---|--------|----------|---------|---------|------|
| 1 | 블로그 포스트 작성 | gather=fan_out_fan_in → write=producer_reviewer | 2 | 2 | [examples/step/01-blog-post.md](examples/step/01-blog-post.md) |
| 2 | 이슈 트리아지 | triage=(expert_pool+pipeline) → review=producer_reviewer | 2 | 3 | [examples/step/02-issue-triage.md](examples/step/02-issue-triage.md) |
| 3 | 아키텍처 설계 | design=pipeline(3 Steps) → validate=fan_out_fan_in | 2 | 4 | [examples/step/03-architecture-design.md](examples/step/03-architecture-design.md) |

---

## 8. 테스트 시나리오 6종

상세 설정·기대 동작·판정 기준: [examples/step/test-scenarios.md](examples/step/test-scenarios.md)

| # | 목적 | 핵심 검증 포인트 | 판정 기준 |
|---|------|----------------|----------|
| 1 | 단순 workflow.md 구조 검증 | Stage 1개 + Step 1개 생성 여부 | Stage 2 블록 없음 + `main/main` 구조 |
| 2 | 다단계 워크플로우 트리거 | 발화에서 다단계 자동 선택 | Stage 블록 2개 이상 존재 |
| 3 | Step 종료 조건 미충족 → 전환 차단 | 미완료 task 있을 때 다음 Step 진입 금지 | Stage 2 에이전트 invoke_agent 미발생 |
| 4 | Step 자동 전환 (승인 불필요) | 종료 조건 충족 시 사용자 개입 없이 전환 | 승인 요청 없이 다음 Step 에이전트 호출 |
| 5 | Stage 전환 게이트 (승인 필수) | Stage 완료 시 승인 게이트 발동 | 승인 요청 발생 + 다음 Stage 에이전트 미호출 |
| 6 | Step별 에이전트 출입 통제 | 현재 Step 목록 외 에이전트 호출 차단 | 비활성 에이전트 invoke_agent 미발생 |
