# tae2089/harness 개선 작업 명세서

> **목적**: 복합 패턴(composite patterns) 기능을 추가하면서 SKILL.md의 비대화를 막고, Progressive Disclosure 원칙을 실제로 강화하기 위한 작업 정의서.
>
> **작성 기준일**: 2026-04-25  
> **현재 SKILL.md 라인 수**: 496줄 (자체 가이드 한계 500줄에 근접)  
> **목표 라인 수**: 350~400줄

---

## 0. 작업 원칙

본 작업은 다음 원칙을 위배하면 안 된다.

1. **본문 우선 다이어트**: 새 기능 추가 전에 기존 본문의 슬리밍을 먼저 완료한다.
2. **description 불변**: 매 세션 컨텍스트에 상주하는 frontmatter description은 변경하지 않는다.
3. **Progressive Disclosure**: 자주 트리거되지 않는 내용은 본문이 아니라 references에 둔다.
4. **하위 호환**: 기존에 생성된 하네스(`.gemini/agents/`, `_workspace/`)가 여전히 동작해야 한다.
5. **자체 규칙 준수**: 본 변경 후에도 `references/skill-writing-guide.md`의 모든 기준을 통과해야 한다.

---

## 1. 작업 범위 요약

| 작업군               | 항목 수  | 우선순위              |
| -------------------- | -------- | --------------------- |
| A. SKILL.md 다이어트 | 3개 작업 | 최우선 — 신규 기능 전 |
| B. 복합 패턴 신설    | 5개 작업 | 다이어트 완료 후      |
| C. 검증·테스트       | 4개 작업 | 신설과 병행           |
| D. 문서·기록         | 2개 작업 | 마무리                |

---

## 2. 작업군 A — SKILL.md 다이어트 (선행 작업)

### A-1. Phase 7을 references로 이전

**대상**: SKILL.md의 394~496행 (Phase 7: 하네스 진화)

**작업**:

- 신규 파일 생성: `skills/gemini-harness/references/evolution-protocol.md`
- Phase 7의 모든 하위 절(7-1 신규 기능 추가, 7-2 기존 에이전트 수정, 7-3 스킬 갱신, 7-4 폐기/통폐합, 7-5 운영/유지보수)을 그대로 이전
- 본문에는 다음 한 단락만 남긴다:

  ```markdown
  ### Phase 7: 하네스 진화

  하네스는 고정물이 아니라 진화하는 시스템이다. 신규 기능 추가, 기존 에이전트
  수정, 스킬 갱신, 폐기·통폐합, 정기 운영/유지보수 워크플로우는
  `references/evolution-protocol.md`에 정의되어 있다. 사용자가 "하네스 점검",
  "하네스 감사", "에이전트 동기화", "기능 추가" 등을 요청하면 해당 파일을
  먼저 로드한다.
  ```

**기대 효과**: SKILL.md −95줄 → 401줄

**검증**:

- [ ] `references/evolution-protocol.md`만 읽어도 Phase 7을 단독으로 수행할 수 있다
- [ ] 본문의 Phase 0~6 흐름에 Phase 7 참조가 깨지지 않는다
- [ ] Phase 7 트리거 키워드(점검·감사·동기화·확장)가 SKILL.md 본문 또는 description에 여전히 식별 가능하게 남아있다

---

### A-2. Phase 0의 "기존 확장 시 Phase 선택 매트릭스" 분리

**대상**: SKILL.md 내부의 7×3 매트릭스 표

**작업**:

- 신규 파일: `skills/gemini-harness/references/expansion-matrix.md`
- 매트릭스 본체와 각 행의 상세 설명을 이전
- 본문에는 다음 한 줄로 대체:

  ```markdown
  3. 기존 확장 모드인 경우, `references/expansion-matrix.md`의 Phase 선택
     매트릭스를 참조하여 실행할 Phase 목록을 결정한다.
  ```

**기대 효과**: SKILL.md −15~20줄

**검증**:

- [ ] 신규 구축 모드 사용자는 expansion-matrix.md를 로드하지 않는다
- [ ] 기존 확장 모드 진입 시 메인 에이전트가 자동으로 매트릭스를 로드한다

---

### A-3. Phase 4 "스킬 생성"의 상세 템플릿 참조 강화

**대상**: SKILL.md 153~224행 중 스킬 작성 템플릿 부분

**작업**:

- 본문에 남길 것: 스킬을 **언제 만들지** 결정하는 기준, **무엇을** 포함해야 하는지 체크리스트 (15줄 이내)
- 본문에서 뺄 것: 스킬 frontmatter 작성 예시, 디렉토리 구조 예시, description 작성 패턴 → 이미 존재하는 `references/skill-writing-guide.md`로 통합
- 중복 제거: 현재 본문과 `skill-writing-guide.md`에 동일 내용이 분산되어 있을 가능성이 있으므로, **단일 진실원은 references**로 정한다

**기대 효과**: SKILL.md −20~30줄

**검증**:

- [ ] Phase 4 본문만 읽고도 "스킬을 만들지 말지" 판단이 가능하다
- [ ] "어떻게" 만드는지는 메인이 skill-writing-guide.md를 자동 로드한다
- [ ] 동일 내용이 두 군데에 중복되지 않는다

---

**작업군 A 완료 시점의 SKILL.md 라인 수 목표: 350~370줄**

이 시점에서 자체 한계 500줄 대비 130~150줄의 여유 확보 → 신규 기능 추가 가능 상태.

---

## 3. 작업군 B — 복합 패턴(Composite Patterns) 신설

### B-1. 복합 패턴 reference 문서 신설

**파일 경로**: `skills/gemini-harness/references/composite-patterns.md`

**필수 포함 섹션**:

#### 3-1-1. 개념 정의

- 복합 패턴이란 무엇이며 단일 패턴 대비 어떤 문제를 해결하는가
- 표기법: `pattern_a+pattern_b` (`+`로 연결)
- 한계: 7개 기본 패턴(Pipeline, Fan-out/Fan-in, Expert Pool, Producer-Reviewer, Supervisor, Hierarchical, Handoff) 중에서만 조합 가능. 복합의 복합(`A+B+C`) 금지.

#### 3-1-2. workflow.md 명세

- 새 파일 위치: `_workspace/workflow.md`
- 필수 필드(머신리더블 마크다운 양식):
  - `## 패턴: <단일 또는 복합>`
  - `## Stage 정의` 섹션 아래 각 stage별로:
    - 패턴 이름 (단일 패턴만 허용)
    - 활성 에이전트 목록 (`@name` 형식)
    - 진입 조건 (검증 가능한 술어)
    - 종료 조건 (검증 가능한 술어)
    - 다음 stage (또는 `done`)
    - 최대 반복 횟수 (Producer-Reviewer 등 루프 패턴인 경우)
- 명세 작성 예시 1개 이상 포함 (`fan_out_fan_in+producer_reviewer`)

#### 3-1-3. checkpoint.json 스키마 확장

- 기존 checkpoint.json에 추가할 필드:
  - `current_stage`: string
  - `active_pattern`: string (현 stage의 단일 패턴)
  - `stage_history`: array of `{stage, started_at, completed_at, iterations}`
  - `stage_artifacts`: object — stage별 산출물 파일 경로 매핑
- 기존 필드와의 충돌 검사 — 단일 패턴 사용 시 위 필드를 모두 생략 가능해야 한다 (하위 호환)

#### 3-1-4. Stage 전환 프로토콜

- 메인 에이전트가 매 사이클 수행할 6단계 알고리즘을 명령형으로 기술:
  1. checkpoint.json 읽기 → current_stage 확인
  2. workflow.md에서 해당 stage의 종료 조건 확인
  3. 종료 조건 검증 (각 활성 에이전트의 task\_\*.json 또는 산출물 파일 스캔)
  4. 미충족 → 현재 stage 패턴에 따라 다음 에이전트 호출
  5. 충족 → checkpoint.json의 current_stage 갱신 + 사용자에게 전환 보고
  6. **금지: stage 전환과 동일 응답 턴에 다음 stage 작업 시작 금지** (사용자 승인 게이트)

#### 3-1-5. 검증 가능한 종료 조건 패턴

다음 표를 포함:

| 권장 (검증 가능)                                | 금지 (LLM 자의 해석) |
| ----------------------------------------------- | -------------------- |
| `_workspace/tasks/task_*.json` 모두 status=done | "충분히 모였다"      |
| `_workspace/critic_verdict.json`의 verdict=PASS | "검토가 만족스러움"  |
| `_workspace/coverage.json`의 score ≥ 임계값     | "품질이 좋음"        |
| 특정 파일 존재 (`_workspace/integrated.md`)     | "통합이 끝남"        |

#### 3-1-6. Stage별 에이전트 출입 통제

- 에이전트 정의(`.gemini/agents/{name}.md`) frontmatter에 신규 필드: `stages: ["gather", "refine"]`
- 메인 에이전트 규칙: current_stage가 에이전트의 stages 목록에 포함된 경우에만 invoke_agent 호출 허용
- 미포함 호출 시 메인이 차단하고 사용자에게 보고

#### 3-1-7. 복합 패턴 예시 3종

최소 3가지 시나리오를 완성된 workflow.md 형태로 제공:

1. `fan_out_fan_in+producer_reviewer` — 병렬 리서치 → 글쓰기·검토 루프 (블로그 작성 등)
2. `expert_pool+producer_reviewer` — 입력 분류 후 전문가 처리 → 통합 검토 (이슈 트리아지 등)
3. `pipeline+fan_out_fan_in` — 순차 설계 → 마지막 단계 병렬 검증 (아키텍처 설계 등)

**파일 크기 목표**: 250~350줄

---

### B-2. SKILL.md 본문에 포인터 추가

**대상**: SKILL.md의 Phase 2 (가상 팀 및 도구 설계) 또는 Phase 5 (통합 및 오케스트레이션) 중 적합한 위치

**추가할 내용** (10줄 이내):

```markdown
#### 복합 패턴 (Composite Patterns)

여러 패턴을 stage로 연결한 복합 워크플로우가 필요한 경우 (예: 병렬 수집 후
검토 루프), `references/composite-patterns.md`를 참조한다. workflow.md 명세,
stage 전환 프로토콜, 종료 조건 술어 패턴, 3종의 완성 예시가 정의되어 있다.

복합 패턴 사용 조건:

- 단일 패턴으로 표현하기 어려운 다단계 협업
- 각 stage의 진입·종료 조건이 명확히 검증 가능한 경우
- 사용자가 stage 전환 게이트에 직접 개입할 수 있는 환경
```

**검증**:

- [ ] 단일 패턴으로 충분한 케이스에서는 메인이 composite-patterns.md를 로드하지 않는다
- [ ] "여러 단계", "병렬 후 검토", "수집 후 정제" 같은 표현이 사용자 발화에 등장 시 메인이 파일을 로드한다

---

### B-3. workflow.md 템플릿 파일 추가

**파일 경로**: `skills/gemini-harness/references/templates/workflow.template.md`

**내용**: B-1의 명세대로 빈 템플릿 (사용자가 채워 넣을 자리에 `{{...}}` 표시), Phase 5의 산출물 생성 단계에서 메인 에이전트가 이 템플릿을 복사·치환하여 `_workspace/workflow.md`를 만든다.

**검증**:

- [ ] 템플릿만으로 메인 에이전트가 유효한 workflow.md를 생성할 수 있다
- [ ] 템플릿에 모든 필수 필드가 포함되어 있다

---

### B-4. 에이전트 출입 통제 — workflow.md 기반으로 구현

**설계 변경**: Gemini CLI agent frontmatter는 커스텀 필드(`stages` 등)를 지원하지 않음. 출입 통제를 frontmatter 대신 **workflow.md의 `활성 에이전트` 목록**으로 대체 구현.

**실제 구현**:

- `workflow.md` 각 stage 블록에 `활성 에이전트: [@name, ...]` 목록 선언.
- 오케스트레이터가 매 사이클 current_stage의 활성 에이전트 목록만 `invoke_agent`로 호출.
- 별도 frontmatter 확장 없음 — agent 파일은 공식 필드만 사용.

**검증**:

- [x] 기존 에이전트 정의 변경 없이 출입 통제 동작
- [x] workflow.md의 활성 에이전트 목록이 단일 진실원

---

### B-5. 오케스트레이터 템플릿에 stage 인지 로직 추가

**대상**: `references/orchestrator-template.md`

**작업**:

- 단일 패턴용 오케스트레이터 템플릿(기존)을 그대로 유지
- 신규 섹션 추가: "복합 패턴 오케스트레이터"
  - 매 사이클 시작 시 checkpoint.json 읽기 절차
  - workflow.md의 현재 stage 종료 조건 확인 절차
  - stage 전환 시 사용자 승인 게이트 호출 패턴
  - stage별 활성 에이전트 출입 통제 검증 로직

**검증**:

- [ ] 단일 패턴 사용자는 신규 섹션을 읽지 않아도 된다
- [ ] 복합 패턴 오케스트레이터가 6단계 프로토콜을 빠짐없이 실행한다

---

## 4. 작업군 C — 검증 및 테스트

### C-1. skill-testing-guide.md에 복합 패턴 테스트 시나리오 추가

**대상**: `references/skill-testing-guide.md`

**추가할 테스트 시나리오** (최소 5개):

1. **트리거 격리 테스트**: 단일 패턴 발화 시 composite-patterns.md가 로드되지 않는가
2. **복합 패턴 트리거 테스트**: "병렬로 모은 후 검토 루프 돌려줘" 같은 발화에서 자동 로드되는가
3. **stage 전환 게이트 테스트**: 종료 조건 미충족 시 다음 stage로 넘어가지 않는가
4. **에이전트 출입 통제 테스트**: 비활성 stage의 에이전트 호출 시 차단되는가
5. **하위 호환 테스트**: stages 필드 없는 기존 에이전트가 정상 동작하는가

---

### C-2. 자체 규칙 위반 검사

**작업**: 본 변경 적용 후 `references/skill-writing-guide.md`의 기준을 자동·수동 검사

체크리스트:

- [ ] SKILL.md 라인 수 ≤ 500
- [ ] description 변경 없음 (305자 유지)
- [ ] description의 트리거 키워드(후속작업, 동기화, 점검 등) 보존
- [ ] 새 references 파일 모두 frontmatter 또는 명확한 헤더 포함
- [ ] 모든 reference 파일이 단독으로 의미 있게 읽힌다 (다른 reference 의존성 없음)

---

### C-3. 컨텍스트 비용 측정

**작업**: 변경 전/후 토큰 사용량 비교

- 단일 패턴 시나리오 (예: 단순 fan_out_fan_in 하네스 구성) → 변경 전 vs 변경 후 토큰 사용량
- 복합 패턴 시나리오 → 추가로 로드되는 토큰량
- 목표: 단일 패턴 시나리오에서 토큰 사용량 **증가 없음** (오히려 감소 기대 — 다이어트 효과)

---

### C-4. 통합 시나리오 E2E 검증

복합 패턴 예시 3종 각각에 대해:

1. 사용자 자연어 발화 → workflow.md 생성
2. workflow.md 기반 stage 전환 시뮬레이션
3. 각 stage 종료 조건 검증
4. 최종 산출물 확인

수행 결과를 `references/composite-patterns.md`의 "검증된 시나리오" 섹션에 기록.

---

## 5. 작업군 D — 문서 및 기록

### D-1. README.md 업데이트

**대상**: `README.md` (4.5K)

**추가 항목**:

- "복합 패턴 지원" 한 줄 추가 (피처 목록)
- 복합 패턴 사용 시작 가이드 링크 (`skills/gemini-harness/references/composite-patterns.md`)
- 7대 패턴 → 7대 기본 패턴 + 복합 패턴 표기 변경

**제약**: README는 마케팅·진입점 문서이므로 상세 명세 추가 금지. 링크와 한 줄 요약만.

---

### D-2. 변경 기록 작성

**파일**: 신규 `CHANGELOG.md` 작성 (없는 경우) 또는 기존 갱신

**기록 항목** (이번 변경분):

- SKILL.md 다이어트: Phase 7과 expansion matrix를 references로 이전
- 신규 기능: 복합 패턴 (composite patterns) 지원
- 신규 reference 파일: composite-patterns.md, evolution-protocol.md, expansion-matrix.md
- 신규 frontmatter 필드: agents의 `stages` (옵션, 하위 호환)
- 신규 워크스페이스 파일: `_workspace/workflow.md` (복합 패턴 사용 시)

---

## 6. 작업 순서 (권장 시퀀스)

```
1주차: 작업군 A (다이어트)
  └─ A-1 → A-2 → A-3 순서로 진행
  └─ 매 작업 후 SKILL.md 라인 수 확인
  └─ 완료 기준: 라인 수 ≤ 400

2주차: 작업군 B (복합 패턴 신설)
  └─ B-1 (composite-patterns.md 작성) — 가장 큰 작업
  └─ B-3 (workflow 템플릿) → B-4 (frontmatter 확장) → B-5 (오케스트레이터)
  └─ B-2 (SKILL.md 포인터 추가)는 마지막에 — 다른 파일이 안정된 후

3주차: 작업군 C (검증) — B와 병행 가능
  └─ C-1 (테스트 시나리오) → C-4 (E2E 검증)
  └─ C-2, C-3는 매 작업 후 점검

마무리: 작업군 D
  └─ D-1 (README) → D-2 (CHANGELOG)
```

---

## 7. 완료 기준 (Done Definition)

본 명세의 모든 작업은 다음을 모두 만족할 때 완료로 간주한다.

### 정량 기준

- [ ] SKILL.md 라인 수: 350~400줄 범위
- [ ] description 글자 수: 변경 없음 (현재 305자 유지)
- [ ] 신규 reference 파일 4개 추가 (composite-patterns, evolution-protocol, expansion-matrix, workflow.template)
- [ ] 작업군 C의 5개 테스트 시나리오 모두 통과

### 정성 기준

- [ ] 단일 패턴 사용자의 토큰 비용이 증가하지 않는다
- [ ] 복합 패턴 사용자가 stage 전환을 결정론적으로 경험한다 (LLM 자의 판단 최소화)
- [ ] 기존 하네스가 변경 없이 동작한다 (하위 호환)
- [ ] 자체 규칙(skill-writing-guide.md)을 모두 통과한다
- [ ] namojo와의 차별점("선언적 명세 + 사용자 승인 게이트") 정체성이 강화된다

---

## 8. 잠재 위험 및 대응

| 위험                                     | 대응                                                           |
| ---------------------------------------- | -------------------------------------------------------------- |
| 복합 패턴 추가 후 SKILL.md가 다시 비대화 | 본문 추가는 10줄 이내로 엄격히 제한                            |
| stage 전환 결정성 부족으로 LLM이 스킵    | 종료 조건을 검증 가능한 술어로 강제 + 사용자 승인 게이트       |
| 기존 하네스 호환성 깨짐                  | stages 필드 옵션 처리 + checkpoint.json 신규 필드 옵션 처리    |
| references 간 중복 발생                  | 단일 진실원 원칙: 동일 내용은 하나의 파일에만                  |
| 매 세션 description 비대화 압력          | description은 본 작업 범위에서 절대 변경 금지 (별도 PR로 다룸) |

---

## 9. 본 명세에 포함되지 않은 것 (Out of Scope)

다음은 의도적으로 본 작업에서 제외했다.

- description 자체의 트리거 키워드 추가/변경
- 새로운 8번째 기본 패턴 추가
- LangGraph 등 외부 런타임 의존성 도입 (tae2089의 정체성 변경)
- namojo와의 상호운용 레이어 (별개의 큰 작업)
- 슬래시 커맨드(`.gemini/commands/`) 도입 (현 설계 원칙에 반함)

위 항목들은 향후 별도 명세로 다룬다.

---

**문서 버전**: v1.0  
**다음 리뷰 시점**: 작업군 A 완료 시점에서 본 명세의 라인 수 목표·테스트 시나리오 재조정
