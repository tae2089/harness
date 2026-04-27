# 오케스트레이터 스킬 고도화 템플릿 (Codex CLI 버전)

오케스트레이터는 메인 에이전트가 오케스트레이션 로직을 실행하기 위해 사용하는 상위 스킬이다. Codex CLI 환경은 **서브에이전트 간 직접 통신이 불가능**하므로, 메인 에이전트가 유일한 **Data Broker**로서 `findings.md`·`tasks.md`·`checkpoint.json`을 매개로 팀을 조율한다.


> **주의:** 서브에이전트 호출은 Codex subagent spawn 사용. 병렬: 기본값. 순차: 스킬 지시로 단계 분리. 병렬 실행: `wait_for_previous: false`. 셸 백그라운드(dev server 등): `run_shell_command`. Claude Code와의 API 차이 상세(`TeamCreate`·`SendMessage`·`TaskCreate` 부재 이유): `references/agent-design-patterns.md` § "실행 모드: 오케스트레이션" 참조.

## 오케스트레이터 기본 구조 (Data Broker 강화형)

````markdown
---
name: {domain}-orchestrator
description: "{도메인} 하네스 오케스트레이터. 발견 사항 공유(findings.md), 상태 영속성(checkpoint.json) 및 작업 관리(tasks.md)를 통해 가상 팀을 조율한다. {초기 실행 키워드}. 후속 작업({도메인} 결과 수정/부분 재실행/업데이트/보완/다시 실행/이전 결과 개선) 시에도 반드시 이 스킬을 사용하여 일관성을 유지하라."
---

# {Domain} Orchestrator

## 가상 팀 구성

> **공통 필수 도구 (표 생략):** 사용자 확인 요청, 스킬 로드
> **오케스트레이터 전용:** `subagent spawn` — 워커 서브에이전트에는 부여하지 않는다.

| agent     | 타입                 | 역할   | 스킬    | 출력          |
| --------- | -------------------- | ------ | ------- | ------------- |
| {agent-1} | {커스텀 또는 빌트인} | {역할} | {skill} | {output-file} |
| {agent-2} | {커스텀 또는 빌트인} | {역할} | {skill} | {output-file} |

## 워크플로우

### Step 0: 컨텍스트 확인 (Durable Execution)

`_workspace/checkpoint.json`의 상태에 따라 진입 경로를 결정한다. **표를 위에서 아래로 순서대로 평가**하여 처음 일치하는 행의 액션을 실행한다.

| `_workspace/` | `ckpt.status` | 추가 조건 | 액션 |
|---|---|---|---|
| 없음 | — | — | GOTO Step 1 |
| 있음 | `in_progress` 또는 `partial` | — | workflow.md 읽기 → GOTO Step 2 ¹ |
| 있음 | `blocked` | 응답 = "계속/재개/해결" | 차단 task 파일 삭제 ² → checkpoint `{status:"in_progress"}` 갱신 → GOTO Step 2 |
| 있음 | `blocked` | 응답 = "처음부터/초기화" | `_workspace/` → `_workspace_{NOW()}/` 백업 → GOTO Step 1 |
| 있음 | `blocked` | 기타 (첫 진입 포함) | 차단 사유 보고 ³ → 사용자 확인 요청 → HALT |
| 있음 | `completed` | 요청 = "부분 수정" | RESUME_FROM 결정 ⁴ → checkpoint `{status:"partial", current_stage, current_step}` 갱신 → GOTO Step 2 |
| 있음 | `completed` | 기타 | `_workspace/` → `_workspace_{YYYYMMDD_HHMMSS}/` 백업 → GOTO Step 1 |

¹ max_turns 소진 후 자동 재개 경로. 수동 개입 불필요.

² 삭제 대상: `_workspace/tasks/task_{ckpt.blocked_agent}_*.json` (`ckpt.blocked_agent` 기준 특정). 다른 step의 Blocked 파일은 건드리지 않는다.

³ 차단 사유 보고 형식:
```
이전 실행 Blocked. 사유: {ckpt.blocked_reason} | 에이전트: {ckpt.blocked_agent}
차단 원인을 해결한 뒤 재개해 주세요. ("계속" / "처음부터")
```
> 사용자 확인 요청는 다음 턴에서 이 표를 재평가한다.

⁴ **부분 수정 RESUME_FROM 결정:**

| 요청 유형 | RESUME_FROM |
|---|---|
| "에이전트 X 프롬프트/산출물 수정" | `{stage: ckpt.current_stage, agent: X}` |
| "스킬 Y 수정" | `{skill: Y}` (해당 에이전트들만 재호출) |
| "workflow.md / 종료 조건 수정" | `{stage: ckpt.current_stage, step: ckpt.current_step}` |
| 범위 불명확 | `ask_user("수정 범위 확인: 어떤 에이전트·스킬·파일?")` → RETURN |

---

### Step 1: 초기화

1. `user_input`에서 `{plan_name}` 파싱. 없으면 `ask_user("작업 이름을 지정해주세요.")` → RETURN.
2. 디렉터리 생성: `_workspace/`, `_workspace/{plan_name}/`, `_workspace/tasks/`, `_workspace/_schemas/`.
3. **스키마 템플릿 동기화 (필수):** 본 스킬의 `references/schemas/` 디렉터리에서 5개 파일을 읽어 `_workspace/_schemas/`에 그대로 작성한다. 각 파일에 대해 shell `cat` → `apply_patch` 1쌍씩 실행:

   | 소스 (스킬 reference 경로) | 대상 (워크스페이스 경로) |
   |---------------------------|------------------------|
   | `references/schemas/task.schema.json` | `_workspace/_schemas/task.schema.json` |
   | `references/schemas/checkpoint.schema.json` | `_workspace/_schemas/checkpoint.schema.json` |
   | `references/schemas/workflow.template.md` | `_workspace/_schemas/workflow.template.md` |
   | `references/schemas/findings.template.md` | `_workspace/_schemas/findings.template.md` |
   | `references/schemas/tasks.template.md` | `_workspace/_schemas/tasks.template.md` |
   | `references/schemas/models.md` | `_workspace/_schemas/models.md` |
   | `references/schemas/agent-worker.template.toml` | `_workspace/_schemas/agent-worker.template.toml` |
   | `references/schemas/agent-orchestrator.template.md` | `_workspace/_schemas/agent-orchestrator.template.md` |
   | `references/schemas/agent-state-manager.template.toml` | `_workspace/_schemas/agent-state-manager.template.toml` |

   > `README.md`·`models.md`·에이전트 템플릿은 에이전트 정의 생성 시 참조용 — 워크스페이스 사본은 생성 기준점으로 활용. `models.md`는 모델 ID SoT이므로 반드시 동기화.
   > **`run_shell_command("cp ...")` 금지** — 런타임 워킹 디렉터리(사용자 프로젝트 루트)에서 스킬 reference 경로는 셸로 도달 불가. 반드시 에이전트 도구 shell `cat` + `apply_patch` 사용.

   **운영 규칙:**
   - 워커 에이전트는 자기 산출물 작성 전 `_workspace/_schemas/task.schema.json` 읽기.
   - 메인은 `task_*.json`·`checkpoint.json` 갱신 시 매번 스키마 검증.
   - 스킬 갱신 시 다음 init부터 새 스키마 적용. 진행 중 워크스페이스 스키마 변경 금지(스냅샷 보존).
   - **SoT:** `references/schemas/`. 워크스페이스 사본은 실행 시점 스냅샷.

4. `workflow.md` 작성 — `_workspace/_schemas/workflow.template.md`를 시작점으로 사용. 패턴에 따라 타이밍이 다르다:

   | 패턴 | 작성 방식 |
   |------|-----------|
   | `pipeline` / `fan_out_fan_in` / `producer_reviewer` / `handoff` / `expert_pool` | 사용자 요청 기반 즉시 작성 |
   | `supervisor` / `hierarchical` | Discovery Agent 먼저 호출 → 산출물 기반 작성 |

5. `findings.md` 초기화 — `_workspace/_schemas/findings.template.md` 복사 후, 패턴별 필요 섹션만 남기고 나머지 제거:

   | 패턴 | 섹션 |
   |------|------|
   | 전 패턴 공통 | `[공유 변수/경로]` |
   | fan_out / fan_out_fan_in | + `[핵심 통찰]`, `[핵심 키워드]`, `[데이터 충돌]` |
   | producer_reviewer | + `[변경 요청]` |
   | pipeline / hierarchical | + `[다음 단계 지침]` |
   | supervisor / handoff | + `[데이터 충돌]` |
   | expert_pool | + `[라우팅 근거]` (형식: `"- {에이전트}: {이유} (매칭 키워드: {키워드})"`) |

6. `tasks.md` 초기화 — `_workspace/_schemas/tasks.template.md` 복사 (헤더만 유지, 행은 비움).
7. `checkpoint.json` 생성 — `_workspace/_schemas/checkpoint.schema.json` 필드를 모두 채워 작성:

```json
{
  "execution_id":   "YYYYMMDD_HHMMSS",
  "plan_name":      "{plan_name}",
  "status":         "in_progress",
  "current_stage":  "{workflow.stages[0].name}",
  "current_step":  "{workflow.stages[0].steps[0].name}",
  "active_pattern": "{first_step.pattern}",
  "stage_history":  [],
  "step_history":  [],
  "stage_artifacts": {},
  "handoff_chain":  [],
  "tasks_snapshot": { "done": [], "current": null },
  "shared_variables": {},
  "last_updated":   "NOW()"
}
```

> **`@state-manager` 위임 패턴 (선택적):** 가상 팀에 `@state-manager`를 포함한 경우, 5~7번 단계(findings.md·tasks.md·checkpoint.json 초기화)와 Step 2의 모든 상태 갱신을 `subagent spawn` 로 위임한다. 오케스트레이터는 추론·조율에 집중, 상태 I/O는 `@state-manager`(flash 모델)가 스키마 검증 후 처리. 인터페이스: `OPERATION: state.init|checkpoint.update|task.upsert|findings.append|tasks.update|state.archive` + `PAYLOAD:` 블록. 상세 명세: `references/schemas/agent-state-manager.template.toml`.

> **표기법 브리지:** `workflow.md`는 JSON이 아닌 **마크다운 헤더**(`### Stage 1: {deliverable-name}`, `#### Step 1: {deliverable-name}`)로만 Stage·Step를 선언한다. 위 checkpoint.json의 `"current_stage": "{workflow.stages[0].name}"` 표기는 "첫 번째 `### Stage` 헤더에서 파싱한 이름"을 의미하는 의사코드다 — JSON 배열 접근이 아니다.
> **파싱 예시:** `### Stage 1: sso-integration` → `current_stage = "sso-integration"` / `#### Step 1: requirements-gathering` → `current_step = "requirements-gathering"`. 오케스트레이터는 `workflow.md`를 shell `cat`로 읽어 헤더 순서대로 Stage·Step 목록을 구성한 뒤 이름(텍스트)으로 참조한다.
> **명명 규칙(필수):** `main`·`step1`·`task` 같은 placeholder 금지. kebab-case + deliverable 의미 명사구 (Jira 제목 컨벤션). 위반 시 workflow.md 스키마 검증에서 차단.

8. **workflow.md 스키마 검증 (작성 직후 필수, 사이클 검증보다 먼저 실행):**

   각 Stage·Step 블록에서 **필수 필드 누락**을 모두 검사한다. 한 건이라도 누락 시 즉시 차단.

   | 검사 항목 | 방법 | 실패 시 액션 |
   |-----------|------|-------------|
   | Stage 필드: `종료 조건`, `다음 stage`, `사용자 승인 게이트` | 정규식/파서로 헤더 아래 필드 존재 확인 | `ask_user("workflow.md Stage {name} 필수 필드 누락: {missing_fields}. 보강 후 재시도.")` → HALT |
   | Step 필드: `패턴`, `활성 에이전트`, `종료 조건`, `다음 step`, `최대 반복 횟수` | 동일 | 동일 |
   | `패턴` 값 = 7대 중 1 (`pipeline`·`fan_out_fan_in`·`expert_pool`·`producer_reviewer`·`supervisor`·`hierarchical`·`handoff`) | enum 검사 | `ask_user("패턴 값 위반: {value}. 7대 중 선택.")` → HALT |
   | `활성 에이전트` 형식 = `[@name, ...]` | 정규식 `\[(@\w[\w-]*\s*,?\s*)+\]` | `ask_user("활성 에이전트 형식 위반.")` → HALT |
   | **`종료 조건` 검증 가능 술어** | 키워드 화이트리스트: `task_*.json`·`status=done`·`존재`·`verdict=`·`score ≥`·`iterations ≥`. 화이트리스트 미매칭 + LLM 자의 해석 키워드(`승인`·`충분`·`완료되면`·`만족`·`적절히`) 발견 시 위반 | `ask_user("Step {name}의 종료 조건이 자연어다('{value}'). 검증 가능 술어로 재작성: 파일 존재·JSON 필드값·iteration ≥ N.")` → HALT |
   | 사용자 승인 게이트 누락 | Stage 블록에 명시 안 됨 | 동일 |
   | **Stage·Step 명명 규칙 (Jira 제목 컨벤션)** | 헤더 이름 추출 → 정규식 `^[a-z][a-z0-9-]*$` 일치 + placeholder 블랙리스트(`main`·`step1`·`task`·`work`·`default`·`phase1`·`stage1`·`generic`) 미포함 | `ask_user("Stage/Step 이름 위반: '{name}'. kebab-case + deliverable 명사구로 재작성 (예: sso-integration, requirements-gathering). placeholder 금지.")` → HALT |

9. **workflow.md 사이클 검증 (스키마 검증 통과 후):**

   | 검사 항목 | 방법 | 실패 시 액션 |
   |-----------|------|-------------|
   | Step 내 순환 참조 | 각 Stage 내 Step의 `다음 step` 링크를 순서대로 추적 — 이미 방문한 Step 이름이 재등장 시 → 순환 | `ask_user("workflow.md에 순환 참조 발견: {Stage} → {cycle_path}. 수정 후 재시도하세요.")` → HALT |
   | Stage 내 `done` 미도달 | Step 체인 끝이 `done`이 아닌 경우 | 동일 |
   | 미정의 Step 참조 | `다음 step` 값이 같은 Stage 내에 존재하지 않는 Step 이름인 경우 | 동일 |

   > 두 검사는 Step 2 루프 진입 전 단 1회 실행. resume 경로(Step 0 → Step 2)에서는 생략 가능(workflow.md가 이미 검증된 상태).

10. GOTO Step 2.

---

### Step 2: Step 실행 루프

**매 사이클 시작 시:**

1. `workflow.md`, `checkpoint.json`, `findings.md` 읽기.
2. `workflow[ckpt.current_stage][ckpt.current_step]` → `step_block` 추출. 없으면 findings.md 오류 기록 → 사용자 확인 요청 → HALT.
3. `step_block`에서 `active_agents`, `pattern`, `exit_cond`, `max_iterations` 추출.
4. **심볼릭 플레이스홀더 해결:** `active_agents`에 `@선택된_전문가` 등 심볼릭 이름 포함 시:
   - `checkpoint.shared_variables.selected_expert` 읽기 → 실제 에이전트명으로 치환.
   - 필드 미존재 → `ask_user("expert_pool Step이 아직 실행되지 않았거나 selected_expert 미기록. 어떤 에이전트를 호출할까요?")` → RETURN.
   > 이 치환은 런타임에만 적용. workflow.md 파일 자체는 수정하지 않는다.
5. **Pre-blocked 검사 (에이전트 호출 전 필수):** `_workspace/tasks/task_*.json` 중 `status=="blocked" AND agent IN active_agents` → 발견 시 checkpoint `blocked` 갱신 → 사용자 확인 요청 → RETURN. 에이전트 호출 절대 금지.
6. 출입 통제: `active_agents` 목록 외 에이전트 호출 금지.
7. **findings.md 컨텍스트 주입:** 에이전트 호출 프롬프트에 `findings.md` 전체를 포함한다.
   ```
   subagent spawn(@{name}, prompt="""
   {task_description}

   ## 공유 컨텍스트 (findings.md)
   @{_workspace/findings.md}
   """)
   ```
   > findings.md가 비어 있어도 헤더는 포함할 것 — 에이전트가 섹션 구조를 인식한다.

**패턴별 에이전트 호출:**

| 패턴 | 호출 방식 | 완료 후 기록 |
|------|-----------|-------------|
| `pipeline` / `hierarchical` | 순차 (`wait_for_previous=true`), 에이전트마다 즉시 기록 | findings.md, tasks.md, checkpoint.json |
| `fan_out` / `fan_out_fan_in` | 병렬 (`wait_for_previous=false`) → 전체 완료 후 `COLLECT ALL task_*.json` → apply_patch ⁷ | tasks/task_{agent}_{id}.json, tasks.md, findings.md, checkpoint.json |
| `producer_reviewer` | — | GOTO Step 3 |
| `expert_pool` | CLASSIFY → 단일 에이전트 순차 ⁵ | findings.md[라우팅 근거], task 파일, tasks.md |
| `supervisor` | 배치별 병렬 → 배치마다 apply_patch | tasks.md, checkpoint.json |
| `handoff` | 순차, `[NEXT_AGENT]` 키워드 파싱 ⁶ | task 파일 (수신자 또는 첫 에이전트), findings.md, tasks.md |

⁵ **expert_pool 상세:**
1. CLASSIFY(user_request, active_agents): 키워드 vs description 비교 → 최적 에이전트 또는 AMBIGUOUS 반환.
2. AMBIGUOUS → `ask_user("전문가 목록: {active_agents}")` → RETURN.
3. findings.md[라우팅 근거] 기록 → checkpoint `shared_variables.selected_expert` 갱신 → 에이전트 호출 → task 파일 기록.

⁶ **handoff 상세:**
1. `active_agents[0]` 호출.
2. 응답에 `[NEXT_AGENT: @{name}]` 포함 시: `handle_handoff({name})` 순환 감지 → next_prompt 구성 → `{name}` 호출 → `task_{name}_{id}.json` 기록.
3. `[NEXT_AGENT]` 미포함 시: `task_{active_agents[0]}_{id}.json` 기록 (단독 완료).

⁷ **fan_out / fan_out_fan_in 에이전트 책임:** 병렬 에이전트 각자가 작업 완료 직후 `_workspace/tasks/task_{agent}_{id}.json`을 직접 작성한다(메인 에이전트가 대신 작성하지 않음). 메인 에이전트는 전체 완료 후 GLOB으로 파일을 수집하여 apply_patch로 통합한다.

   **부분 실패 복구 (일부 에이전트 task 파일 미생성 시):**
   1. GLOB 결과 파일 수 < 예상 에이전트 수 → 미생성 에이전트 식별 (active_agents에서 GLOB 결과 차집합).
   2. 미생성 에이전트마다 Zero-Tolerance 재호출 (최대 2회 재시도, 총 3회).
   3. 재시도 후에도 미생성 → `blocked_protocol(agent, task)` 호출 → HALT. 부분 결과로 강제 진행 절대 금지.
   4. 모든 에이전트 task 파일 확인 후에만 apply_patch 수행.

**종료 조건 검사 (`exit_cond` 유형별):**

| Type | 종료 조건 형식 | 검사 방법 |
|------|----------------|-----------|
| A | `task_*.json` 모두 `status=done` | GLOB → status 필드 전수 확인 (`"done"` 소문자 — task.schema.json enum 기준) |
| B | 특정 파일 존재 | `EXISTS(경로)` |
| C | JSON 필드값 (예: `verdict=PASS`) | READ 파일 → 필드 비교 |
| D | `iterations ≥ N` | `step_history` 배열에서 `stage==current_stage AND step==current_step`인 마지막 항목의 `.iterations` 비교 (배열 딕셔너리 접근 아님 — 선형 탐색) |

**종료 조건 충족 시 — Step/Stage 전환:**

1. checkpoint.json `step_history`에 완료 기록.
2. `step_block.다음_step` 누락(필드 없음 또는 null/빈 값) → findings.md 오류 기록 → 사용자 확인 요청 → HALT.
3. `다음_step != "done"` → checkpoint 갱신(`current_step`, `active_pattern`, `handoff_chain: []`) → Step 2 루프 상단 재진입 (다음 Step로 진입).
4. `다음_step == "done"` → GOTO Stage 전환 게이트. (상세: `references/stage-step-guide.md` § "Stage 전환 프로토콜")

**종료 조건 미충족 시:**

1. `iterations < max_iterations` → `step_history` 배열에서 `stage==current_stage AND step==current_step`인 항목 찾아 `.iterations` 증가(없으면 신규 추가) → `active_pattern == "handoff"` 이면 checkpoint.json `handoff_chain: []` 리셋 (새 iteration = 새 체인) → Step 2 루프 상단 재진입 (같은 Step 재실행).
2. 소진 → findings.md에 `"Step {current_step}: max_iterations 소진, 종료 조건 미충족"` 기록 → blocked_protocol. (상세: `references/orchestrator-procedures.md`)

---

### Step 3: Fix Loop (producer_reviewer 전용)

```
retries ← 0

WHILE retries < 3:
    CALL subagent spawn
    WRITE "_workspace/{plan_name}/{output}_v{retries+1}.md" ← producer 결과

    CALL subagent spawn
    READ "_workspace/tasks/task_{reviewer}_{id}.json" → review

    IF review.status == "done":  // PASS
        apply_patch { tasks.md ← PASS evidence, checkpoint.json ← tasks_snapshot 갱신 }
        GOTO Step 4

    ELSE:  // FAIL
        retries += 1
        IF retries >= 3:
            UPDATE tasks.md ← task "blocked"
            CALL ask_user("3회 후에도 검증 실패. 개입 요청.")
            RETURN
        WRITE findings.md["변경 요청"] ← review.evidence  // 피드백 주입 후 재시도
```

---

### Step 4: 통합 및 최종 산출

1. `GLOB "_workspace/tasks/task_*.json"` → `status=="done"` 파일만 필터 → 각 파일의 `artifact_path` 추출 → `artifacts` 리스트 구성.
2. findings.md의 `[데이터 충돌]` 섹션 확인 → 충돌 있으면 reviewer 에이전트 호출하여 해소. 미해소 시 사용자 확인 요청 → RETURN.
3. `_workspace/{plan_name}/final_{output}.md` ← artifacts 병합(MERGE) 후 저장.
   > MERGE: 각 에이전트 산출물을 역할 순서대로 읽어 섹션별로 연결. 포맷은 도메인에 따라 결정 (마크다운: `## {에이전트명}\n{내용}` 연결, JSON: 키 병합, 코드: 파일 경로 목록).

---

### Step 5: 아카이브 및 보고

1. `findings.md`, `tasks.md` → `_workspace/{plan_name}/` 복사 (상세 이력 보존).
2. `findings.md` 요약본으로 교체: `[최종 결과 요약]` + `[아카이브 경로]` 섹션만 유지.
3. `checkpoint.json` 갱신: `status:"completed"`, `current_stage/step:"done"`, `stage_history`에 완료 기록.
4. 사용자 보고:

```
완료: {plan_name}
산출물:    _workspace/{plan_name}/final_{output}.md
상세 이력: _workspace/{plan_name}/findings.md
tasks:     _workspace/{plan_name}/tasks.md
```

## 데이터 영속성 프로토콜 (checkpoint.json 스키마)

> **정본(canonical spec).** `stage-step-guide.md` 등 다른 파일은 이 스키마를 참조한다.

### 필드 설명

| 필드 | 타입 | 설명 | 필수 |
|------|------|------|------|
| `execution_id` | string | `YYYYMMDD_HHMMSS` 형식 실행 ID. | **필수** |
| `plan_name` | string | 실행 계획 식별자. | **필수** |
| `status` | string | `"in_progress"` \| `"completed"` \| `"partial"` \| `"blocked"`. | **필수** |
| `last_updated` | string | ISO 8601 타임스탬프. | **필수** |
| `current_stage` | string | 현재 활성 stage 이름. **deliverable kebab-case 강제** (예: `"sso-integration"`); placeholder(`"main"` 등) 금지. | **필수** |
| `current_step` | string | 현재 활성 step 이름. **deliverable kebab-case 강제** (예: `"requirements-gathering"`); placeholder(`"main"`·`"step1"` 등) 금지. | **필수** |
| `active_pattern` | string | 현 step 실행 패턴 (예: `"pipeline"`). | 권장 |
| `stage_history` | array | 완료 stage 기록. `started_at` + `completed_at` 포함. | 다단계 |
| `step_history` | array | 완료 step 기록. `iterations` 포함. | 다단계 |
| `stage_artifacts` | object | stage별 주요 산출물 경로 매핑. | 선택 |
| `tasks_snapshot` | object | 태스크 완료 현황 스냅샷. | 선택 |
| `shared_variables` | object | 여러 에이전트가 공유하는 런타임 변수. | 선택 |
| `handoff_chain` | array | Handoff 패턴 사용 시 현 step 내 호출된 에이전트 순서. 순환 감지용. Step 전환 시 초기화. | Handoff 패턴 |
| `blocked_agent` | string | Blocked 발생 시 차단된 에이전트명. `status:"blocked"` 전환 시에만 기록. | Blocked 시 |
| `blocked_reason` | string | Blocked 발생 원인. 재개 시 사용자에게 표시. | Blocked 시 |

### 스키마 예시

```json
{
  "execution_id": "20260425_103000",
  "plan_name": "blog-writing-run-001",
  "status": "in_progress",
  "last_updated": "2026-04-25T10:30:00Z",

  "current_stage": "refine",
  "current_step": "draft-review",
  "active_pattern": "producer_reviewer",

  "stage_history": [
    { "stage": "gather", "started_at": "2026-04-25T09:00:00Z", "completed_at": "2026-04-25T10:00:00Z" }
  ],
  "step_history": [
    { "stage": "gather", "step": "research", "completed_at": "2026-04-25T10:00:00Z", "iterations": 1 }
  ],

  "stage_artifacts": { "gather": "_workspace/research/", "refine": "_workspace/draft.md" },
  "tasks_snapshot": { "done": ["T1", "T2"], "current": "T3" },
  "shared_variables": { "main_artifact": "_workspace/plan/02_code.md" },
  "handoff_chain": ["@incident-triage", "@db-fixer"]
}
```
````

## 분할 작업 파일 프로토콜 (Split Task Schema)

서브에이전트가 병렬 실행 중 자신의 상태를 보고할 때 사용하는 `_workspace/tasks/task_{agent}_{id}.json` 스키마.

```json
{
  "agent": "@coder",
  "task_id": "T2",
  "status": "done",
  "retries": 0,
  "evidence": "Reviewer PASS report: _workspace/plan/03_review.md",
  "artifact_path": "_workspace/plan/02_code.md"
}
```

> `status`: `"done"` | `"blocked"`. `retries ≥ 2` 시 blocked 전환 (0·1 허용 = 총 3회).

## 절차 & 원칙

> 에러 핸들링(`handle_error` / `blocked_protocol` / `handle_handoff`), 테스트 시나리오, description 키워드, 작성 원칙, Stage·Step 참조:
> **`references/orchestrator-procedures.md`** 참조.
