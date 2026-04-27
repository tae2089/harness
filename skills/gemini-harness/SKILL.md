---
name: gemini-harness
description: "하네스를 구성합니다. 전문 서브에이전트 팀과 협업 스킬을 설계하는 Gemini CLI 메타 프레임워크. (1) '하네스 구성해줘', '하네스 구축/설계/엔지니어링' 요청 시, (2) 새로운 도메인/프로젝트에 대한 자동화 체계를 구축할 때, (3) 하네스를 재구성·확장할 때, (4) '하네스 점검', '하네스 감사', '하네스 현황', '에이전트/스킬 동기화' 등 기존 하네스 운영/유지보수 요청 시, (5) 이전 결과 수정/보완/재실행 요청 시 **반드시 이 스킬을 먼저 호출하라.** 7대 아키텍처 패턴과 엄격한 도구 제어 기반으로 설계한다."
---

# Harness — Subagent Orchestration & Skill Architect

도메인/프로젝트에 맞는 하네스를 구성하고, 각 서브에이전트의 역할·도구 권한을 정의하며, 에이전트가 공통으로 사용할 절차 스킬과 오케스트레이터를 생성하는 메타 스킬.

**핵심 원칙:**

1. **7대 핵심 아키텍처 패턴 적용:** 문제 특성에 맞는 최적의 협업 구조(Pipeline, Fan-out/Fan-in, Expert Pool, Producer-Reviewer, Supervisor, Hierarchical, Handoff)를 선택한다. 상세: `references/agent-design-patterns.md`.
2. **엄격한 도구 권한 제어:** 에이전트 역할에 최적화된 도구만 할당하며, `tools: ["*"]`는 금지한다. 단, **모든 에이전트는 다음 도구들을 반드시 포함**한다.
   - `ask_user`: 모호한 지시·데이터 충돌 시 추측 대신 사용자에게 확인 질의.
   - `activate_skill`: `.gemini/skills/` 아래 절차 스킬(방법론·체크리스트·프로토콜)을 에이전트가 런타임에 로드하여 실행하기 위해 필수.
   - `invoke_agent`는 오케스트레이터·Supervisor·Hierarchical 팀장(Mid-level)에서만 허용 — 일반 워커 금지. 순차(`wait_for_previous: true`) 및 병렬(`wait_for_previous: false`) 모두 사용 가능.
3. **메인 에이전트 오케스트레이션 및 영속성:** Gemini CLI에는 서브에이전트 간 직접 통신(`SendMessage`) API가 없으므로, 메인 에이전트가 유일한 데이터 브로커(`_workspace/findings.md`)이자 상태 관리자(`_workspace/checkpoint.json`) 및 태스크 보드(`_workspace/tasks.md`) 관리자가 된다.
4. **`.gemini/agents/` + `.gemini/skills/` + `GEMINI.md` 3요소 생성.** 슬래시 커맨드(`.gemini/commands/`)는 만들지 않는다.
5. **하네스는 고정물이 아니라 진화하는 시스템이다.** 매 실행 후 피드백을 반영하고, 에이전트·스킬·GEMINI.md를 지속 갱신한다.
6. **Plan Mode 필수 적용 (Critical):** 모든 하네스 설계, 생성 및 확장 작업 시작 전 반드시 `enter_plan_mode`를 호출한다. 리서치와 설계 단계를 격리하여 복잡한 오케스트레이션 로직의 안정성을 확보하고, 사용자에게 최종 승인받은 계획만을 코드로 구현한다. 단, yolo mode일 경우에는 바로 실행한다.
7. **무관용 실패 대응 프로토콜 (Zero-Tolerance Failure Protocol):** 테스트 실패나 에이전트의 산출물 반려를 임의로 스킵하는 행위는 절대 금지한다. 메인 에이전트 및 감독자는 반드시 해결책을 강구(최대 2회 재시도(총 3회))해야 하며, 해결되지 않을 경우 독단적으로 다음 단계로 넘어가지 말고 즉시 작업을 중단하여 사용자에게 개입을 요청한다.

---

## 워크플로우

### Phase 0: 현황 감사 및 모드 분기

하네스 스킬이 트리거되면 가장 먼저 기존 하네스 현황을 확인한다.

1. `{프로젝트}/.gemini/agents/`, `{프로젝트}/.gemini/skills/`, `{프로젝트}/GEMINI.md`를 읽는다.
2. 현황에 따라 실행 모드를 분기한다:
   - **신규 구축:** 에이전트/스킬 디렉토리가 없거나 비어있음 → Phase 1부터 전체 실행.
   - **기존 확장:** 기존 하네스가 있고 새 에이전트/스킬 추가 요청 → `references/expansion-matrix.md`의 Phase 선택 매트릭스에 따라 필요한 Phase만 실행.
   - **운영/유지보수:** 기존 하네스의 감사·수정·동기화 요청 → `references/evolution-protocol.md`의 운영/유지보수 워크플로우로 이동.
3. 기존 에이전트/스킬 목록과 GEMINI.md 기록을 대조하여 불일치(drift)를 감지한다.
4. 감사 결과를 사용자에게 요약 보고하고, 실행 계획을 확인받는다.

---

### Phase 1: 도메인 분석 및 패턴 매칭

1. 사용자 요청에서 도메인/프로젝트 파악.
2. 핵심 작업 유형 식별(생성, 분석, 검증, 편집, 배포 등).
3. Phase 0 감사 결과를 기반으로 기존 에이전트/스킬과의 충돌·중복 분석.
4. 프로젝트 코드베이스 탐색 — 기술 스택, 데이터 모델, 주요 모듈 파악.
5. **사용자 숙련도 감지:** 대화의 맥락 단서(사용 용어, 질문 수준)로 기술 수준을 파악하고, 이후 커뮤니케이션 톤을 조절한다. 코딩 경험이 적은 사용자에게는 "assertion", "JSON schema", "브로커링" 같은 용어를 설명 없이 쓰지 않는다.
6. **아키텍처 패턴 매칭:** 7대 패턴 중 최적 구조를 선택한다.

---

### Phase 2: 가상 팀 및 도구 설계

#### 2-0. agents vs skills 분리 원칙

- **`.gemini/agents/{name}.md` (페르소나 — "누가"):** 역할 기반 서브에이전트. 도구 권한과 시스템 프롬프트로 행동 경계를 정의한다. (예: `@backend-coder`, `@qa-inspector`)
- **`.gemini/skills/{name}/SKILL.md` (절차 — "어떻게"):** 에이전트들이 공통으로 따르는 방법론·체크리스트·프로토콜. 여러 에이전트가 재사용한다. (예: `tdd-workflow`, `integration-coherence-check`)
- **판정 기준:** 고정된 책임·도구 집합이 있으면 agent, 절차·원칙이면 skill. 헷갈리면 skill을 먼저 만들고 agent가 `activate_skill`로 호출하게 한다.

#### 2-1. 아키텍처 패턴 선택

작업을 전문 영역으로 분해한 뒤, 조율 구조를 결정한다.

- **파이프라인 (Pipeline):** 순차 의존 작업 (설계→구현→검증).
- **팬아웃/팬인 (Fan-out/Fan-in):** 병렬 독립 작업 후 통합.
- **전문가 풀 (Expert Pool):** 상황별 선택 호출.
- **생성-검증 (Producer-Reviewer):** 생성 후 품질 검수 루프.
- **감독자 (Supervisor):** 메인이 상태를 보며 동적 분배.
- **계층적 위임 (Hierarchical):** 팀장 에이전트가 하위 에이전트에 재귀 위임(2단계 이내 권장).
- **핸드오프 (Handoff):** 에이전트가 작업 완료 후 다음 전문가를 직접 추천하여 위임.

**workflow.md (모든 하네스 필수):** 모든 하네스는 `_workspace/workflow.md`에 Stage-Step 구조를 선언한다. **Stage = 상위 이슈(Jira Issue/Story, deliverable)**, **Step = 하위 이슈(Jira Sub-issue) = Stage 안의 단일 작업 항목**(1 Step = 1 패턴). 사용자 승인 게이트는 상위 이슈(Stage) 단위. 상세: `references/stage-step-guide.md`.

> **[MANDATORY] 명명 규칙 — Jira 제목 컨벤션 강제.** Stage·Step 이름은 **deliverable 의미를 담은 명사구**여야 한다. Jira 이슈 제목과 동일한 기준 — 제목만 보고 무엇을 만드는지 식별 가능해야 한다.
>
> | 금지 (placeholder·일반어)              | 허용 (deliverable 식별)                                |
> | -------------------------------------- | ------------------------------------------------------ |
> | `main`·`step1`·`task`·`work`·`default` | `sso-integration`·`payment-flow`·`onboarding-redesign` |
> | `phase1`·`stage1`·`generic`            | `requirements-gathering`·`api-design`·`load-test`      |
>
> **단일 Stage·단일 Step 케이스도 동일 규칙 적용** — `main` 같은 placeholder 금지. 도메인 deliverable 이름 사용. 예: 단일 블로그 작성 → `Stage 1: blog-post` / `Step 1: draft-and-review` (≠ `main/main`).
> 형식: `^[a-z][a-z0-9-]*$` (소문자 케밥 케이스, 숫자·하이픈 허용, 시작은 영문 소문자).

> **[MANDATORY] workflow.md 스키마 강제 — 누락 시 Zero-Tolerance Failure.** 오케스트레이터 스킬을 작성할 때 절대 평면 "Step 1~N" 나열로 도피하지 말 것. 모든 Step 블록은 아래 6개 필드를 **빠짐없이** 포함해야 한다.
>
> | 필수 필드                  | 형식                                                                               | 자연어 금지                                                             |
> | -------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
> | `패턴`                     | 7대 패턴 중 1개 (`pipeline`·`fan_out_fan_in` 등)                                   | "순차 진행" 같은 임의 표기 금지                                         |
> | `활성 에이전트`            | `[@name1, @name2]` 형식                                                            | 에이전트명 누락·자유 텍스트 금지                                        |
> | `종료 조건`                | **검증 가능 술어** (파일 존재·`task_*.json` status=done·JSON 필드값·iteration ≥ N) | "QA 승인", "충분히 모였다", "완료되면" 같은 LLM 자의 해석 표현 **차단** |
> | `다음 step`                | 같은 Stage 내 step 이름 또는 `done`                                                | 누락 금지                                                               |
> | `최대 반복 횟수`           | 정수 (비루프=1, 루프 ≤3)                                                           | 누락 금지                                                               |
> | Stage `사용자 승인 게이트` | `필요` 또는 `없음 (마지막 stage)`                                                  | 명시 누락 금지                                                          |
>
> 자연어 종료 조건이 작성되면 **즉시 거부**하고 검증 가능 술어로 재작성. drift 처리: `references/expansion-matrix.md`의 "drift 처리 가이드" 참조.

**상호작용 스타일 선택 (Interaction Styles - 필수):** 구조적 패턴 외에도, 에이전트와 대화하는 스타일을 정의한다.

- **위임 (Delegation):** 에이전트가 직접 산출물 파일을 생성/수정하도록 지시 (`invoke_agent`).
- **자문 (Consultative):** 메인이 결정하기 전, 전문가의 분석 의견이나 체크리스트만 반환받음 (`invoke_agent`).
- **수동 (Manual):** 사용자가 직접 터미널에서 개입하여 검수 (`@agent_name`).

> **핵심 가이드:** 패턴 선택 및 오케스트레이터의 에이전트 호출 프롬프트 작성 시, `references/agent-design-patterns.md`의 **"상호작용 스타일"** 및 **"사용 예시"** 섹션을 반드시 참조하여 구체적인 지시문을 구성하라. 스타일을 먼저 정하면 에이전트에게 `write_file` 권한을 줄지(위임) 말지(자문)가 명확해진다.

---

#### 2-2. 에이전트 분리 기준

전문성·병렬성·컨텍스트·재사용성 4축으로 판단한다.

| 기준     | 분리                          | 통합             |
| -------- | ----------------------------- | ---------------- |
| 전문성   | 영역이 다르면                 | 영역이 겹치면    |
| 병렬성   | 독립 실행 가능하면            | 순차 종속이면    |
| 컨텍스트 | 부담이 크면(각자 작은 범위만) | 가볍고 빠르면    |
| 재사용성 | 다른 팀에서도 쓰면            | 이 팀에서만 쓰면 |

**Gemini CLI 고유 고려사항:** 분리할 때마다 메인 에이전트의 중개 부담(`findings.md` 갱신·프롬프트 주입)이 늘어난다. 분리 이득이 중개 오버헤드를 상회할 때만 분리한다.

#### 2-3. 도구 세트 매핑

각 에이전트 유형(Analyst / Architect / Coder / Reviewer / Operator)에 맞는 표준 도구 + 관련 MCP 도구를 할당한다. 표 전문은 `references/agent-design-patterns.md`의 "에이전트 유형별 표준 도구 세트" 참조.

#### 2-4. 오케스트레이션 및 영속성 프로토콜 설계

- **데이터 흐름:** `_workspace/` 내의 파일 기반 데이터 교환 경로를 설계한다.
- **영속성 프로토콜:** 실행 중단 시 재개를 위한 `checkpoint.json` 스키마 및 갱신 시점을 정의한다.
- **데이터 브로커링:** 메인 에이전트가 `findings.md`·`tasks.md`를 통해 에이전트 간 통찰을 중개하는 경로를 정의한다.
- **충돌 중개:** 에이전트 간 산출물이 상충할 때 메인이 어떤 에이전트에게 최종 판정을 맡길지 사전 지정.

---

### Phase 3: 서브에이전트 정의 생성 (.md)

**공식 Gemini CLI 서브에이전트 포맷을 준수하여 `{프로젝트}/.gemini/agents/{name}.md` 파일로 생성한다.** Agent 도구 프롬프트에 역할을 인라인으로 넣는 것은 금지한다(재사용성·협업 프로토콜 보장을 위해).

1. **YAML Frontmatter 필수 필드:**
   - `name`: slug 형태의 고유 이름.
   - `description`: pushy하게 작성. 트리거 상황·후속 작업 키워드 포함.
   - `kind: local`
   - `model`: 역할에 따라 선택. 오케스트레이터·Architect → `"gemini-3.1-pro-preview"`, 워커(Coder·Analyst·Reviewer·Operator) → `"gemini-3-flash-preview"`을 사용한다.
   - `tools`: **제한된 목록** (`ask_user`·`activate_skill`은 모든 에이전트 필수 포함; `invoke_agent`는 오케스트레이터·Supervisor·Hierarchical 팀장(Mid-level) 허용 — 일반 워커 에이전트에 부여 금지).

2. **선택 필드(역할에 따라 권장):**

   | 역할                          | temperature | max_turns |
   | ----------------------------- | ----------- | --------- |
   | Reviewer·QA (결정론적 산출)   | 0.2         | 5 ~ 10    |
   | Analyst·Architect (탐색·설계) | 0.3 ~ 0.5   | 10 ~ 15   |
   | Coder                         | 0.2         | 15 ~ 20   |
   | Operator (인프라·배포)        | 0.1 ~ 0.2   | 6 ~ 8     |
   | 창작·브레인스토밍             | 0.7 이상    | 10 ~ 15   |

3. **시스템 프롬프트 필수 섹션:** 핵심 역할, 작업 원칙, 입출력 프로토콜(Data Broker 기반), 에러 핸들링, 다른 에이전트와의 관계.

4. **재호출 지침:** 각 에이전트 정의에 "이전 산출물이 있을 때의 행동"을 명시한다(이전 결과 파일 읽고 개선점 반영, 사용자 피드백이 주어지면 해당 부분만 수정).

5. **시스템 등록 (필수, 사용자 수동 실행):** 에이전트 파일(`.md`) 생성 및 수정 완료 후, 사용자에게 `/agents reload`와 `/skills reload`를 진행시킨다. reload는 Gemini CLI 내부에서만 가능하다. — 반드시 사용자가 Gemini CLI 프롬프트에서 직접 입력해야 시스템 레지스트리에 반영된다. 메인 에이전트는 다음 형식으로 알린다:
   ```
   에이전트 파일 작성 완료: {agent-1}, {agent-2}, ...
   skill 파일 작성 완료: {skill-1}, {skill-2}, ...
   다음 작업을 위해 Gemini CLI 프롬프트에 `/agents reload`와 `/skills reload`를 직접 입력해 주세요.
   완료되면 "리로드 완료" 등으로 알려주시면 이어서 진행하겠습니다.
   ```
   리로드 확인 응답을 받기 전까지는 새 에이전트를 호출(`invoke_agent`)과 스킬을 호출(`activate_skill`)하지 않는다 — 호출 시 등록 누락으로 실패한다.

> 템플릿과 실제 파일 전문은 `references/agent-design-patterns.md`의 "에이전트 정의 구조" + `references/examples/team/` 참조.

**QA 에이전트 포함 시 필수 사항:**

- QA의 `tools`에는 반드시 `run_shell_command`를 포함한다(테스트·린트 실행). 장기 프로세스(dev server·빌드 워처)는 **셸 백그라운드 옵션**으로 띄우고 동일 턴에서 후속 검증 수행.
- QA의 핵심은 "존재 확인"이 아니라 **"경계면 교차 비교"** — 생산자 출력과 소비자 입력 기대를 동시에 읽고 비교.
- QA는 전체 완성 후 1회가 아니라 **각 모듈 완성 직후 점진적으로 실행**(Incremental QA).
- 상세: `references/qa-agent-guide.md` 참조.

---

### Phase 4: 스킬 생성

각 에이전트가 사용할 절차 스킬을 `{프로젝트}/.gemini/skills/{name}/SKILL.md`에 생성한다.

**스킬 생성 판단 기준:**

- 고정된 역할·도구 집합이 있으면 → **agent**. 절차·원칙이면 → **skill**.
- 2개 이상의 에이전트가 같은 방법론을 반복한다 → 스킬로 추출.
- 체크리스트·프로토콜·반복 검증 절차가 있다 → 스킬로 번들링.

**스킬이 포함해야 할 것:**

1. `name` + `description` frontmatter — 트리거 키워드·후속 작업 키워드 포함, pushy하게 작성. (pushy 기준·예시: `references/skill-writing-guide.md` § 1-2·1-3)
2. 명령형 본문 — Step 순서, 입출력 프로토콜, 에러 핸들링(`ask_user` 경로).
3. `references/` 포인터 — 자주 트리거되지 않는 세부 내용은 여기로 분리(500줄 이내 유지).

**스킬-에이전트 연결:** `activate_skill` 호출 / 프롬프트 인라인 / `read_file`로 `references/` 로드 — 3가지 방식. 상세 기준은 `references/agent-design-patterns.md` § "스킬 ↔ 에이전트 연결 방식" 참조.

상세 작성 패턴·description 예시·Progressive Disclosure·데이터 스키마: `references/skill-writing-guide.md`.

---

### Phase 5: 통합 및 오케스트레이션

오케스트레이터는 스킬의 특수한 형태로, 개별 에이전트와 스킬을 하나의 워크플로우로 엮어 팀 전체를 조율한다. Phase 4의 개별 스킬이 "각 에이전트가 무엇을 어떻게 하는가"를 정의한다면, 오케스트레이터는 "누가 언제 어떤 순서로 협업하는가"를 정의한다. 구체적 템플릿: `references/orchestrator-template.md`.

**기존 확장 시 오케스트레이터 수정:** 신규 구축이 아니면 오케스트레이터를 새로 만들지 않고 기존 것을 수정한다. 에이전트 추가 시 팀 구성·작업 할당·데이터 흐름에 새 에이전트를 반영하고, description에 새 에이전트 관련 트리거 키워드를 추가한다.

#### 5-0. 오케스트레이터 패턴 (Gemini CLI 단일 모드)

메인 에이전트가 데이터 브로커 역할을 하면서 서브에이전트를 순차·배치로 호출한다. Claude Code의 `TeamCreate`/`SendMessage`/`TaskCreate` API는 Gemini CLI에 **존재하지 않으므로** 절대 사용하지 않는다. 대신:

```
[메인 에이전트 (오케스트레이터)]
    ├── workflow.md 읽기 (current_stage + current_step + 활성 에이전트 + 종료 조건 확인)
    ├── checkpoint.json 관리 (상태 영속화 및 재개 로직)
    ├── findings.md 갱신 (작업 중 상세 기록)
    ├── tasks.md 갱신 (태스크 보드)
    ├── @agent-1 호출 (workflow.md step 출입 통제 확인 후 invoke_agent)
    ├── 결과 분석 및 동적 위임 (Handoff 파싱)
    ├── 산출물 읽고 findings.md 업데이트
    ├── step 종료 → 자동 전환, stage 완료 → 사용자 승인 게이트 → checkpoint.json 갱신
    ├── 모든 작업 완료 후 findings.md를 _workspace/{plan_name}/findings.md로 아카이브
    └── 중앙 findings.md에는 요약과 아카이브 경로만 유지
```

**병렬성:** Claude Code의 `run_in_background` 플래그는 존재하지 않지만, Gemini CLI에서는 **`invoke_agent` 호출 시 `wait_for_previous: false`**를 사용하여 병렬 실행을 구현한다. 의존성이 없는 에이전트들을 단일 응답 턴 내에서 배치 호출하여 시간을 단축한다. (단, 셸 명령은 `run_shell_command`의 백그라운드 옵션으로 별개 병렬 구동 가능.)

#### 5-1. 데이터 전달 프로토콜

오케스트레이터 내에 에이전트 간 데이터 전달 방식을 명시한다. **Gemini CLI는 서브에이전트 간 직접 통신 API가 없으므로**, 모든 에이전트 간 정보 흐름은 아래 5종 파일 매개로 메인 에이전트가 중개한다.

| 전략                          | 방식                                                                                                             | 적합한 경우                                                            |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **파일 기반 산출물 (기본)**   | `_workspace/{plan_name}/`에 워커가 직접 산출물 기록                                                              | 대용량 데이터, 구조화된 산출물, 감사 추적                              |
| **findings.md 브로커링**      | 메인이 산출물을 읽어 요약을 `findings.md`에 기록, 다음 에이전트 프롬프트에 주입                                  | 에이전트 간 통찰 공유, 상충 중재                                       |
| **task\_\*.json (워커 보고)** | 워커가 `_workspace/tasks/task_{agent}_{id}.json`을 **자기 것만 작성** → 메인이 GLOB 수집 후 tasks.md 원자적 통합 | **병렬 에이전트 race condition 회피** (워커는 tasks.md 직접 쓰기 금지) |
| **tasks.md 태스크 보드**      | 메인 단독 갱신. Todo / In-Progress / Done / Blocked 상태                                                         | 진행 추적, 감독자 패턴의 동적 할당                                     |
| **checkpoint.json**           | 메인 단독 갱신. 마지막 성공 지점·공유 변수·current_stage·current_step                                            | Durable Execution (중단 시 재개)                                       |
| **반환 메시지**               | 서브에이전트가 최종 답을 반환                                                                                    | 짧은 결과, 단발성 조회                                                 |

**권장 조합:** 파일 기반 산출물 + findings.md(통찰 중개) + task\_\*.json(워커 보고) + tasks.md(진행 보드) + checkpoint.json(영속성) 5종 모두 활용.

##### 산출물 관리 계층 (읽기/쓰기 권한 매트릭스)

```
_workspace/
├── _schemas/                    [WRITE: 메인(Step 1만)]  [READ: 모든 에이전트(자기 산출물 검증)]
│   ├── task.schema.json         (JSON Schema — task_*.json 검증)
│   ├── checkpoint.schema.json   (JSON Schema — checkpoint.json 검증)
│   ├── findings.template.md     (섹션 골격 — 패턴별 필요 섹션 가이드)
│   ├── tasks.template.md        (표 골격 — 메인 통합용)
│   └── workflow.template.md     (Stage-Step 블록 골격 + 필드 룰)
├── workflow.md             [WRITE: 메인(Step 1만)] [READ: 메인(매 사이클)]
├── findings.md             [WRITE: 메인 단독]      [READ: 모든 에이전트(프롬프트 주입)]
├── tasks.md                [WRITE: 메인 단독]      [READ: 메인]
├── checkpoint.json         [WRITE: 메인 단독]      [READ: 메인]
├── tasks/
│   └── task_{agent}_{id}.json   [WRITE: 워커 자기 것만] [READ: 메인(GLOB 수집)]
└── {plan_name}/
    └── {step}_{agent}_*.md      [WRITE: 워커]           [READ: 메인 → findings 요약]
```

**`_schemas/` 자기 검증 워크스페이스:** Step 1.3에서 스킬 `references/schemas/` 5종(`task.schema.json`·`checkpoint.schema.json`·`workflow.template.md`·`findings.template.md`·`tasks.template.md`)을 `read_file` → `write_file` 쌍으로 `_workspace/_schemas/`에 작성(**셸 `cp` 금지** — 런타임 워킹 디렉터리에서 스킬 reference 경로는 셸 도달 불가, 반드시 에이전트 도구 사용). 워커는 자기 `task_*.json` 작성 전 `_workspace/_schemas/task.schema.json` 읽고 형식 맞춤. 메인은 `task_*.json`·`checkpoint.json` 갱신 시 매번 스키마 검증. 스킬 갱신 시 다음 init부터 적용 — 진행 중 워크스페이스 스냅샷은 보존. SoT: `references/schemas/`.

**핵심 규칙:**

- **워커는 `tasks.md`·`findings.md`·`checkpoint.json` 절대 직접 수정 금지** — 병렬 호출 시 race condition으로 데이터 손실.
- **메인은 `task_*.json` 직접 작성 금지** — 워커가 자기 작업 완료 후 자기 파일만 작성.
- **메인의 통합 흐름:** `GLOB("_workspace/tasks/task_*.json")` → 모두 읽기 → tasks.md ATOMIC_WRITE 갱신 + findings.md 요약 갱신 + checkpoint.json 갱신.

##### task\_\*.json 스키마 (워커 → 메인 보고 표준)

```json
{
  "id": "task_{agent}_{seq}",
  "agent": "@agent-name",
  "stage": "{current_stage}",
  "step": "{current_step}",
  "status": "Todo | In-Progress | Done | Blocked",
  "evidence": "검증 가능 술어 (예: '_workspace/sso/research.md 존재', 'go test ./... PASS')",
  "artifact": "_workspace/{plan_name}/{filename}",
  "blocked_reason": "(status=Blocked일 때만) 차단 사유",
  "timestamp": "YYYYMMDD_HHMMSS"
}
```

**파일명 컨벤션 (산출물용):** `{step}_{agent}_{artifact}_v{version}.{ext}` (예: `01_analyst_requirements_v1.md`). 최종 산출물만 사용자 지정 경로에 출력, 중간 파일들은 `_workspace/{plan_name}/`에 보존.

#### 5-2. 에러 핸들링 및 자가 치유

오케스트레이터 내에 에러 처리 방침을 포함한다. 핵심 원칙: **체크포인트 기반 자동 재개**, 최대 2회 재시도(총 3회) 후 미해결 시 태스크를 `Blocked`로 전환하고 `ask_user`로 사용자 개입 요청(임의 Skip 절대 금지), 상충 데이터는 삭제하지 않고 출처 병기.

> 에러 유형별 전략표와 구현 상세는 `references/orchestrator-procedures.md`의 "에러 핸들링 및 자가 치유" 참조.

#### 5-3. 팀 크기 가이드라인

| 작업 규모             | 권장 에이전트 수 | 에이전트당 작업 수 |
| --------------------- | ---------------- | ------------------ |
| 소규모 (5~10개 작업)  | 2~3명            | 3~5개              |
| 중규모 (10~20개 작업) | 3~5명            | 4~6개              |
| 대규모 (20개 이상)    | 5~7명            | 4~5개              |

> 에이전트가 많을수록 메인의 중개 오버헤드가 커진다. 3명의 집중된 에이전트가 5명의 산만한 팀보다 낫다.

#### 5-4. GEMINI.md 하네스 포인터 등록

하네스 구성 완료 후, 프로젝트의 `GEMINI.md`에 최소한의 포인터를 등록한다. GEMINI.md는 새 세션마다 로딩되므로, 하네스 존재와 트리거 규칙만 기록하면 오케스트레이터 스킬이 나머지를 처리한다.

> **AGENTS.md 병행 사용:** Claude Code·Codex·Aider 등과 함께 쓰는 프로젝트라면 Agent Rules 이니셔티브 표준인 `AGENTS.md`를 추가로 작성하고, `settings.json`에 `{ "context": { "fileName": ["AGENTS.md", "GEMINI.md"] } }`를 등록하면 두 파일 모두 로딩된다.

**GEMINI.md 템플릿:**

```markdown
## 하네스: {도메인명}

**목표:** {하네스의 핵심 목표 한 줄}

**트리거:** {도메인} 관련 작업 요청 시 `{orchestrator-skill-name}` 스킬을 사용하라. 단순 질문은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|---|---|---|---|
| {YYYY-MM-DD} | 초기 구성 | 전체 | - |
```

**GEMINI.md에 넣지 않는 것:** 에이전트 목록, 스킬 목록, 디렉토리 구조, 실행 규칙 상세. 이유: 이는 `.gemini/agents/`·`.gemini/skills/` 및 오케스트레이터 스킬에서 관리되므로 중복이다. GEMINI.md는 **포인터(트리거 규칙) + 변경 이력**만 담는다.

#### 5-5. 후속 작업 지원

오케스트레이터는 초기 실행뿐 아니라 후속 작업도 처리해야 한다. 다음 세 가지를 보장하라.

**1. 오케스트레이터 description에 후속 키워드 포함:**
초기 생성 키워드만으로는 후속 요청이 트리거되지 않는다. 반드시 포함할 표현:

- "다시 실행", "재실행", "업데이트", "수정", "보완"
- "{도메인}의 {부분작업}만 다시"
- "이전 결과 기반으로", "결과 개선"

**2. 오케스트레이터 Step 0에 컨텍스트 확인 단계 추가:**
워크플로우 시작 시 기존 산출물 및 체크포인트 존재 여부를 확인하여 실행 모드를 결정한다.

- **`checkpoint.json` 존재 + `status: "in_progress"`** → **중단 지점 재개** (실패 지점부터 실행).
- **`checkpoint.json` 존재 + `status: "completed"`** → 이전 완료 상태. 부분 수정이면 부분 재실행, 새 입력이면 새 실행으로 분기. Resume 금지.
- `_workspace/` 존재 + 사용자가 부분 수정 요청 → **부분 재실행** (해당 에이전트만 재호출).
- `_workspace/` 존재 + 사용자가 새 입력 제공 → **새 실행** (기존을 `_workspace_{timestamp}/`로 이동 후 보존).
- `_workspace/` 미존재 → **초기 실행**.

**3. 에이전트 정의에 재호출 지침 포함:** Phase 3-4 참조.

> 오케스트레이터 템플릿의 "Step 0: 재실행 감지" 섹션 참조: `references/orchestrator-template.md`.

---

### Phase 6: 검증 및 테스트

생성된 하네스를 검증한다. 상세 테스트 방법론: `references/skill-testing-guide.md`.

#### 6-1. 구조 검증

- 모든 에이전트 파일이 `.gemini/agents/` 아래 올바른 위치에 있는지 확인.
- 스킬 frontmatter(`name`, `description`) 검증.
- 에이전트 frontmatter(`name`, `description`, `kind: local`, `model`, `tools`) 검증.
- `tools` 배열이 `["*"]`이 아니고 `ask_user`·`activate_skill`이 포함되어 있는지 확인.
- 에이전트 간 참조 일관성 확인.
- 슬래시 커맨드(`.gemini/commands/`)가 **생성되지 않았는지** 확인.

#### 6-2. 실행 모드 검증

- 각 에이전트의 입출력 경로(`_workspace/`)가 다음 에이전트의 입력과 매칭되는지 확인.
- 오케스트레이터가 `findings.md`·`tasks.md`·`checkpoint.json`을 실제로 갱신하는 로직을 포함하는지 확인.
- Claude Code 전용 API(`TeamCreate`/`SendMessage`/`TaskCreate`/서브에이전트 `run_in_background`)가 오케스트레이터에 남아있지 않은지 확인.
- **expert_pool 패턴 사용 시:** `CLASSIFY()` 결과가 `findings.md`의 `[라우팅 근거]` 섹션에 기록되는지, 분류 모호 시 `ask_user`로 위임하는지 확인.
- **handoff 패턴 사용 시:** `[NEXT_AGENT]` 포함·미포함 두 경로(ELSE 브랜치) 모두 task 파일·findings를 기록하는지 확인. 순환 감지(`handle_handoff`) 호출 포함 여부 확인.

#### 6-3. 스킬 실행 테스트

생성된 각 스킬에 대해 실제 실행 테스트를 수행한다.

1. **테스트 프롬프트 작성** — 각 스킬에 대해 2~3개의 현실적인 테스트 프롬프트 작성. 실제 사용자가 입력할 법한 구체적이고 자연스러운 문장.
2. **With-skill vs Without-skill 비교** — 가능하면 스킬 있는 실행과 없는 실행을 병렬로 수행하여 스킬의 부가가치를 확인한다.
   - **With-skill:** 스킬을 활성화해 작업 수행.
   - **Without-skill (baseline):** 같은 프롬프트를 스킬 없이 수행.
3. **결과 평가** — 산출물 품질을 정성적(사용자 리뷰) + 정량적(assertion 기반)으로 평가. 객관적으로 검증 가능한 경우(파일 생성, 데이터 추출) assertion 정의, 주관적인 경우(문체·디자인) 사용자 피드백.
4. **반복 개선 루프** — 문제 발견 시 피드백을 **일반화**하여 스킬 수정(특정 예시 전용 수정 금지) → 재테스트 → 만족할 때까지 반복.
5. **반복 패턴 번들링** — 에이전트들이 공통으로 작성하는 코드가 발견되면 `scripts/`에 미리 번들링.

평가 결과는 `references/skill-writing-guide.md`의 `grading.json` 스키마에 맞춰 `_workspace/evals/{timestamp}/grading.json`에 기록한다.

> **경로 구분:** `_workspace/evals/{timestamp}/grading.json`은 **하네스 구축 시 생성 스킬의 일회성 검증** 경로다. 스킬을 장기적으로 반복 개선할 때는 `references/skill-testing-guide.md`의 `_workspace/{skill-name}/iteration-N/eval-{id}/{variant}/grading.json` 구조를 사용한다.

#### 6-4. 트리거 검증

각 스킬의 description이 올바르게 트리거되는지 검증한다.

1. **Should-trigger 쿼리 (10개)** — 스킬을 트리거해야 하는 다양한 표현(공식적/캐주얼, 명시적/암시적, 후속 작업 키워드 포함).
2. **Should-NOT-trigger 쿼리 (10개)** — 키워드가 유사하지만 다른 도구/스킬이 적합한 "near-miss" 쿼리.

**near-miss 작성 핵심:** "피보나치 함수 작성" 같이 명백히 무관한 쿼리는 테스트 가치가 없다. "이 엑셀 파일의 차트를 PNG로 추출해줘"(xlsx 스킬 vs 이미지 변환)처럼 **경계가 모호한 쿼리**가 좋은 테스트 케이스다.

기존 스킬과의 트리거 충돌도 이 단계에서 확인한다(`.gemini/skills/*/SKILL.md` 전수 스캔).

#### 6-5. 드라이런 테스트

- 오케스트레이터 스킬의 Step 순서가 논리적인지 검토.
- 데이터 전달 경로에 빈 구간(dead link)이 없는지 확인.
- 모든 에이전트의 입력이 이전 Step의 출력과 매칭되는지 확인.
- 에러 시나리오별 폴백 경로가 실행 가능한지 확인.

#### 6-6. 테스트 시나리오 작성

- 오케스트레이터 스킬에 `## 테스트 시나리오` 섹션 추가.
- 정상 흐름 1개 + 에러 흐름 1개 + **재개(Resume) 흐름 1개** 이상 기술.

---

### Phase 7: 하네스 진화

하네스는 고정물이 아니라 진화하는 시스템이다. 신규 기능 추가, 기존 에이전트 수정, 스킬 갱신, 폐기·통폐합, 정기 운영/유지보수 워크플로우는 `references/evolution-protocol.md`에 정의되어 있다. 사용자가 "하네스 점검", "하네스 감사", "에이전트 동기화", "기능 추가" 등을 요청하면 해당 파일을 먼저 로드한다.

---

## 산출물 체크리스트

생성 완료 후 확인:

- [ ] `{프로젝트}/.gemini/agents/{name}.md` — **에이전트 정의 파일 필수 생성**. 각 파일에 `kind: local`, `model`(오케스트레이터·Architect → gemini-3.1-pro-preview, 워커 → gemini-3-flash-preview), 제한된 `tools`, `temperature`/`max_turns`, `ask_user`+`activate_skill` 포함.
- [ ] `{프로젝트}/.gemini/skills/{name}/SKILL.md` — 스킬 파일들 (SKILL.md + 필요 시 `references/`·`scripts/`·`assets/`).
- [ ] **신규 오케스트레이터 스킬 `references/schemas/` 5종 번들 필수** — `task.schema.json`·`checkpoint.schema.json`·`workflow.template.md`·`findings.template.md`·`tasks.template.md`. SoT(`gemini-harness/references/schemas/`)에서 그대로 복사. 런타임 Step 1.3가 `references/schemas/{file}`을 `read_file`로 읽음 — 누락 시 즉시 실패. (gemini-harness는 메타 스킬·런타임 활성화 안 됨.)
- [ ] 오케스트레이터 스킬 1개 (Step 0 재실행 감지 + 데이터 흐름 + 에러 핸들링 + 테스트 시나리오 포함).
- [ ] `_workspace/` 표준 경로 정의 — `_schemas/`(Step 1.3에서 `references/schemas/` 5종 `read_file`+`write_file` 쌍으로 동기화), `workflow.md`(Stage-Step 구조 선언), `findings.md`, `tasks.md`, `checkpoint.json`, `{plan_name}/`(실행 산출물), `tasks/task_{agent}_{id}.json`(에이전트별 상태 파일), `evals/{timestamp}/grading.json`.
- [ ] `{프로젝트}/GEMINI.md` — 하네스 포인터(트리거 규칙 + 변경 이력) 등록.
- [ ] `.gemini/commands/` — **아무것도 생성하지 않음**.
- [ ] 기존 에이전트/스킬과 충돌 없음 (트리거 충돌 포함).
- [ ] 스킬 description이 적극적("pushy")으로 작성됨 — **후속 작업 키워드 포함**.
- [ ] SKILL.md 본문이 500줄 이내, 초과 시 `references/`로 분리.
- [ ] 테스트 프롬프트 2~3개로 실행 검증 완료.
- [ ] 트리거 검증(Should-trigger + Should-NOT-trigger 각 10개, 총 20개) 완료.
- [ ] **grading.json 경로 구분** — 하네스 구축 일회성 검증: `_workspace/evals/{timestamp}/grading.json` / 장기 반복 개선: `_workspace/{skill-name}/iteration-N/eval-{id}/{variant}/grading.json` (두 경로 혼용 금지).
- [ ] **오케스트레이터 Step 0에 컨텍스트 및 체크포인트 확인 단계**(초기/후속/부분/재개 판별) 존재.
- [ ] **GEMINI.md 변경 이력**에 에이전트/스킬 추가·삭제·수정 기록.
- [ ] Claude Code 전용 API(`TeamCreate`/`SendMessage`/`TaskCreate`/서브에이전트 `run_in_background`) 미사용 확인 — Gemini CLI에는 이런 팀 API가 없으므로 에이전트 간 통신은 `_workspace/tasks/task_{agent}_{id}.json` 파일 기반 브로커링으로 대체한다.

---

## 참고

- **7대 아키텍처 패턴 + 에이전트 정의 구조 + 도구 매핑:** `references/agent-design-patterns.md`
- **오케스트레이터 고도화 템플릿** (Step 0~5 pseudocode, checkpoint.json 스키마, Split Task Schema): `references/orchestrator-template.md`
- **오케스트레이터 절차 & 원칙** (에러 핸들링 결정트리, blocked_protocol, handle_handoff, description 키워드, 작성 원칙): `references/orchestrator-procedures.md`
- **실전 협업 사례** (패턴 인덱스 + 패턴 선택 가이드 + 산출물 패턴 요약): `references/team-examples.md` / 각 예시 상세: `references/examples/team/01~05-*.md`
- **스킬 작성 가이드** (작성 패턴, 예시, 데이터 스키마 표준, 오케스트레이터 작성 규칙 §7-5, **평면 Step → Stage-Step 마이그레이션 §7-6**): `references/skill-writing-guide.md`
- **스킬 테스트 가이드** (테스트/평가/트리거 검증/반복 개선): `references/skill-testing-guide.md`
- **QA 에이전트 가이드** (통합 정합성 검증, 경계면 버그 패턴, 셸 백그라운드 활용, 실제 버그 7건 사례): `references/qa-agent-guide.md`
- **하네스 진화 프로토콜** (피드백 반영, 변경 이력, 운영/유지보수 워크플로우): `references/evolution-protocol.md`
- **기존 확장 Phase 선택 매트릭스** (변경 유형별 실행 Phase 결정): `references/expansion-matrix.md`
- **Stage-Step 워크플로우 가이드** (workflow.md 명세, checkpoint.json 스키마, Step·Stage 전환 프로토콜): `references/stage-step-guide.md` / 예시 5종: `references/examples/step/01~05-*.md` / 테스트 시나리오 6종: `references/examples/step/test-scenarios.md`
- **workflow.md 작성 템플릿** (변수 치환 후 `_workspace/workflow.md`로 작성): `references/schemas/workflow.template.md`
