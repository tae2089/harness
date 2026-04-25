# Stage-Phase 워크플로우 가이드

모든 하네스의 워크플로우 구조를 정의하는 가이드. `_workspace/workflow.md`에 Stage-Phase 계층을 선언하여 오케스트레이터가 결정론적으로 실행하도록 한다. SKILL.md Phase 2 또는 Phase 5에서 참조한다.

---

## 목차

1. [개념 정의](#1-개념-정의)
2. [workflow.md 명세](#2-workflowmd-명세)
3. [checkpoint.json 스키마 확장](#3-checkpointjson-스키마-확장)
4. [Phase·Stage 전환 프로토콜](#4-phasestage-전환-프로토콜)
5. [검증 가능한 종료 조건 패턴](#5-검증-가능한-종료-조건-패턴)
6. [Phase별 에이전트 출입 통제](#6-phase별-에이전트-출입-통제)
7. [워크플로우 예시 3종](#7-워크플로우-예시-3종)

---

## 1. 개념 정의

### 3단계 계층 모델

모든 하네스는 **Stage → Phase → Agent** 3단계 계층으로 구성된다.

| 계층 | 전환 주체 | 설명 |
|------|---------|------|
| **Stage** | 사용자 승인 게이트 | 최상위 작업 단위. 사용자 승인 후에만 전환. |
| **Phase** | 오케스트레이터 자동 관리 | Stage 내 세부 작업 단위. 자동 전환. 각 phase는 7대 기본 패턴 중 하나를 사용. |
| **Agent** | Phase 내 실행자 | 실제 작업 수행. phase의 `활성 에이전트` 목록으로 제어. |

`_workspace/workflow.md`에 Stage·Phase 구조를 선언한다. 오케스트레이터는 항상 이 파일을 읽어 현재 stage와 phase를 파악한다.

### 단순 vs 다단계

- **단순 워크플로우:** stage 1개(`main`) + phase 1개(`main`). 단일 7대 패턴 적용.
- **다단계 워크플로우:** stage 2개 이상, 또는 한 stage에 phase 2개 이상. 각 phase가 독립 패턴을 사용.

**다단계 워크플로우 사용 조건 (모두 충족 시):**

- 단일 phase로 표현하기 어려운 2단계 이상의 협업 구조
- 각 stage·phase의 종료 조건이 파일 존재·JSON 필드값 등으로 명확히 검증 가능
- 사용자가 stage 전환 게이트에 직접 개입할 수 있는 환경

---

## 2. workflow.md 명세

`_workspace/workflow.md`는 모든 하네스에 필수. Stage·Phase 구조를 선언하며, 오케스트레이터가 매 사이클 읽는다.

### 단순 워크플로우 예시 (stage 1 + phase 1)

```markdown
<!-- 참고 패턴: fan_out_fan_in (실행에 영향 없음, 문서화 목적) -->

## Stage 정의

### Stage 1: main
- 종료 조건: 모든 phase 완료
- 다음 stage: done
- 사용자 승인 게이트: 없음

#### Phase 1: main
- 패턴: fan_out_fan_in
- 활성 에이전트: [@researcher-a, @researcher-b, @researcher-c]
- 종료 조건: `_workspace/tasks/task_*.json` 모두 status=done
- 다음 phase: done
- 최대 반복 횟수: 1
```

### 다단계 워크플로우 예시 (stage 2 + phase 여러 개)

```markdown
<!-- 참고 패턴: fan_out_fan_in → producer_reviewer (실행에 영향 없음, 문서화 목적) -->

## Stage 정의

### Stage 1: gather
- 종료 조건: 모든 phase 완료
- 다음 stage: refine
- 사용자 승인 게이트: 필요

#### Phase 1: research
- 패턴: fan_out_fan_in
- 활성 에이전트: [@researcher-trend, @researcher-data]
- 종료 조건: `_workspace/research/task_trend.json`, `task_data.json` 모두 status=done
- 다음 phase: done
- 최대 반복 횟수: 1

### Stage 2: refine
- 종료 조건: 모든 phase 완료
- 다음 stage: done
- 사용자 승인 게이트: 없음 (마지막 stage)

#### Phase 1: draft-review
- 패턴: producer_reviewer
- 활성 에이전트: [@writer, @editor]
- 종료 조건: `_workspace/editor_verdict.json`의 verdict=PASS
- 다음 phase: done
- 최대 반복 횟수: 3
```

### 작성 규칙

- `활성 에이전트`는 **phase 블록에서만 선언**. `@name` 형식, `.gemini/agents/{name}.md`와 일치해야 함.
- `종료 조건`은 반드시 검증 가능한 술어(파일 존재, JSON 필드값, 수치 임계값)로 작성.
- `다음 phase`는 다음 phase 이름 또는 `done`.
- `다음 stage`는 다음 stage 이름 또는 `done`.
- `최대 반복 횟수`는 Producer-Reviewer 등 루프 패턴에서 무한루프 방지용으로 필수.
- Stage의 `종료 조건`은 `모든 phase 완료`로 선언하거나 구체적인 검증 가능 조건으로 작성.

---

## 3. checkpoint.json 스키마 확장

### 필드 설명

| 필드 | 타입 | 설명 | 필수 |
|------|------|------|------|
| `current_stage` | string | 현재 활성 stage 이름. 단순 워크플로우는 `"main"`. | **필수** |
| `current_phase` | string | 현재 활성 phase 이름. 단순 워크플로우는 `"main"`. | **필수** |
| `active_pattern` | string | 현 phase에서 사용 중인 단일 패턴. | 권장 |
| `stage_history` | array | 완료된 stage 기록 (재개 및 감사 추적용). | 다단계 |
| `phase_history` | array | 완료된 phase 기록 (stage 내 전환 추적). | 다단계 |
| `stage_artifacts` | object | stage별 주요 산출물 경로 매핑. | 선택 |

### 스키마 예시 (다단계 워크플로우)

```json
{
  "plan_name": "blog-writing-run-001",
  "status": "in_progress",
  "last_updated": "2026-04-25T10:30:00Z",

  "current_stage": "refine",
  "current_phase": "draft-review",
  "active_pattern": "producer_reviewer",

  "stage_history": [
    {
      "stage": "gather",
      "started_at": "2026-04-25T09:00:00Z",
      "completed_at": "2026-04-25T10:00:00Z"
    }
  ],
  "phase_history": [
    {
      "stage": "gather",
      "phase": "research",
      "completed_at": "2026-04-25T10:00:00Z",
      "iterations": 1
    }
  ],
  "stage_artifacts": {
    "gather": "_workspace/research/",
    "refine": "_workspace/draft.md"
  }
}
```

---

## 4. Phase·Stage 전환 프로토콜

### Phase 전환 프로토콜 (자동, 사용자 승인 불필요)

오케스트레이터가 매 사이클 수행하는 내부 루프. 순서를 반드시 지킨다.

1. `checkpoint.json`에서 `current_stage`, `current_phase` 읽기.
2. `workflow.md`에서 해당 phase 블록의 종료 조건 읽기.
3. 종료 조건 검증 (파일 스캔, JSON 필드 확인).
4. **미충족** → 현재 phase 패턴의 활성 에이전트 호출 후 다음 사이클 대기.
5. **충족** → `다음 phase` 확인:
   - 다음 phase 이름 → `checkpoint.json`의 `current_phase` 즉시 갱신 + `phase_history`에 기록 → 같은 턴 내 다음 phase 진입 허용.
   - `done` → Stage 종료 조건 검증 진행 (아래 Stage 전환 프로토콜).

### Stage 전환 프로토콜 (사용자 승인 필수)

1. 현재 stage의 마지막 phase가 `done`임을 확인.
2. 사용자에게 아래 형식으로 보고.
3. 사용자 승인 후: `checkpoint.json`의 `current_stage` 갱신 + `current_phase` → 다음 stage 첫 번째 phase명으로 초기화 + `stage_history`에 기록.
4. **[금지]** 승인과 같은 응답 턴에 다음 stage 에이전트 호출 금지.

### 사용자 승인 게이트 형식

```
Stage {현재 stage} 완료:
  Phase {phase-1}: {종료 조건} ✓
  Phase {phase-2}: {종료 조건} ✓

다음 Stage: {다음 stage}
  Phase 목록: [{phase-1}, {phase-2}]
  첫 Phase 활성 에이전트: {에이전트 목록}
  첫 Phase 종료 조건: {조건}

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
| phase_history의 해당 phase iterations ≥ max_iterations | "충분히 반복했다" |

---

## 6. Phase별 에이전트 출입 통제

Gemini CLI agent frontmatter는 커스텀 필드를 지원하지 않는다. 출입 통제는 **workflow.md의 phase 블록 `활성 에이전트` 목록**으로 수행한다.

```
invoke_agent 호출 전 확인:
1. workflow.md에서 current_stage → current_phase 블록 찾기.
2. 해당 phase의 `활성 에이전트` 목록 읽기.
3. 호출 대상이 목록에 있으면 → invoke_agent 허용.
4. 목록에 없으면 → 호출 보류, 필요 시 사용자에게 보고:
   "@writer는 현재 phase({current_stage}/{current_phase})의 활성 에이전트가 아닙니다."
```

---

## 7. 워크플로우 예시 3종

### 예시 1: 병렬 수집 후 검토 루프 (블로그 포스트 작성)

```markdown
<!-- 참고 패턴: gather=fan_out_fan_in, write=producer_reviewer -->

## Stage 정의

### Stage 1: gather
- 종료 조건: 모든 phase 완료
- 다음 stage: write
- 사용자 승인 게이트: 필요

#### Phase 1: research
- 패턴: fan_out_fan_in
- 활성 에이전트: [@researcher-trend, @researcher-data, @researcher-case]
- 종료 조건: `_workspace/research/task_trend.json`, `task_data.json`, `task_case.json` 모두 status=done
- 다음 phase: done
- 최대 반복 횟수: 1

### Stage 2: write
- 종료 조건: 모든 phase 완료
- 다음 stage: done
- 사용자 승인 게이트: 없음 (마지막 stage)

#### Phase 1: draft-review
- 패턴: producer_reviewer
- 활성 에이전트: [@writer, @editor]
- 종료 조건: `_workspace/editor_verdict.json`의 verdict=PASS 또는 iterations ≥ 3
- 다음 phase: done
- 최대 반복 횟수: 3
```

**데이터 흐름:**
```
gather/research:     @researcher-* → _workspace/research/{topic}.md (병렬)
write/draft-review:  메인이 research/*.md 요약 → @writer에 주입
                     @writer → _workspace/draft.md
                     @editor → _workspace/editor_verdict.json
                     verdict=REJECT → @writer 재호출 (findings 업데이트 포함)
```

---

### 예시 2: 분류 → 전문가 분석 → 검토 (이슈 트리아지)

```markdown
<!-- 참고 패턴: triage=expert_pool+pipeline, review=producer_reviewer -->

## Stage 정의

### Stage 1: triage
- 종료 조건: 모든 phase 완료
- 다음 stage: review
- 사용자 승인 게이트: 필요

#### Phase 1: classification
- 패턴: expert_pool
- 활성 에이전트: [@bug-analyst, @perf-analyst, @security-analyst]
- 종료 조건: `_workspace/triage/selected_expert.json` 존재
- 다음 phase: analysis
- 최대 반복 횟수: 1

#### Phase 2: analysis
- 패턴: pipeline
- 활성 에이전트: [@선택된_전문가]  <!-- checkpoint의 selected_expert 값 기반 동적 결정 -->
- 종료 조건: `_workspace/triage/analysis.md` 존재
- 다음 phase: done
- 최대 반복 횟수: 1

### Stage 2: review
- 종료 조건: 모든 phase 완료
- 다음 stage: done
- 사용자 승인 게이트: 없음 (마지막 stage)

#### Phase 1: report
- 패턴: producer_reviewer
- 활성 에이전트: [@report-writer, @tech-lead]
- 종료 조건: `_workspace/review/final_report.md` 존재 + `_workspace/review/approval.json`의 approved=true
- 다음 phase: done
- 최대 반복 횟수: 2
```

**데이터 흐름:**
```
triage/classification: 메인이 이슈 유형 분류 → selected_expert.json 생성
triage/analysis:       selected_expert.json 기반 적합한 @*-analyst 1개 호출
                       → _workspace/triage/analysis.md
review/report:         @report-writer가 analysis.md 읽고 보고서 초안 작성
                       @tech-lead → 승인 또는 수정 요청
```

---

### 예시 3: 순차 설계 후 병렬 검증 (아키텍처 설계)

```markdown
<!-- 참고 패턴: design=pipeline(다단계), validate=fan_out_fan_in -->

## Stage 정의

### Stage 1: design
- 종료 조건: 모든 phase 완료
- 다음 stage: validate
- 사용자 승인 게이트: 필요

#### Phase 1: requirements
- 패턴: pipeline
- 활성 에이전트: [@requirements-analyst]
- 종료 조건: `_workspace/design/requirements.md` 존재
- 다음 phase: architecture
- 최대 반복 횟수: 1

#### Phase 2: architecture
- 패턴: pipeline
- 활성 에이전트: [@architect]
- 종료 조건: `_workspace/design/architecture.md` 존재
- 다음 phase: api-design
- 최대 반복 횟수: 1

#### Phase 3: api-design
- 패턴: pipeline
- 활성 에이전트: [@api-designer]
- 종료 조건: `_workspace/design/api_spec.md` 존재
- 다음 phase: done
- 최대 반복 횟수: 1

### Stage 2: validate
- 종료 조건: 모든 phase 완료
- 다음 stage: done
- 사용자 승인 게이트: 없음 (마지막 stage)

#### Phase 1: parallel-review
- 패턴: fan_out_fan_in
- 활성 에이전트: [@security-reviewer, @perf-reviewer, @compat-reviewer]
- 종료 조건: `_workspace/validation/task_security.json`, `task_perf.json`, `task_compat.json` 모두 status=done
- 다음 phase: done
- 최대 반복 횟수: 1
```

**데이터 흐름:**
```
design/requirements:      @requirements-analyst → requirements.md
design/architecture:      @architect: requirements.md 읽고 → architecture.md
design/api-design:        @api-designer: architecture.md 읽고 → api_spec.md
validate/parallel-review: 세 reviewer가 api_spec.md + architecture.md 병렬 검토
                          메인이 세 리뷰 결과 통합 → 최종 보고
```
