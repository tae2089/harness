# 기존 확장 시 Phase 선택 매트릭스

`SKILL.md` Phase 0에서 **기존 확장** 모드로 분기되었을 때 참조한다. 변경 유형에 따라 실행할 Phase 목록을 결정한다.

---

## 1단계: 변경 유형 분류 결정 트리

```
PROCEDURE classify_change(request):

    // ── Step A: workflow.md / Step 구조만 변경? ─────────────────
    IF request affects ONLY ["workflow.md", "checkpoint.json 로직"]:
        IF adds new Stage OR adds new Step:
            RETURN "Stage/Step 추가"
        ELSE:                               // 종료 조건·패턴명·에이전트 목록 조정
            RETURN "workflow.md 수정"

    // ── Step B: 에이전트·스킬 파일만 변경? ──────────────────────
    IF request affects ONLY [".codex/agents/*.md", "references/skills/"]:
        IF adds new agent OR renames agent role:
            RETURN "에이전트 추가"
        ELSE:                               // 프롬프트·체크리스트·도구 목록만 수정
            RETURN "스킬 추가/수정"

    // ── Step C: 아키텍처 변경 임계값 판정 ───────────────────────
    // 아래 조건 중 하나라도 해당 시 "아키텍처 변경"
    // 패턴 목록 전체는 references/agent-design-patterns.md § "7대 핵심 아키텍처 패턴" 참조
    아키텍처 변경 조건:
      - 패턴 변경 (예: pipeline → fan_out_fan_in)
      - 에이전트 3개 이상 동시 재편 (추가·삭제·역할 재정의 합산)
      - 오케스트레이터 Step 2 핵심 분기 로직 수정
      - Stage 수 증가 또는 감소

    IF ANY of 아키텍처 변경 조건:
        RETURN "아키텍처 변경"

    // ── Step D: 여러 유형 동시 발생 ─────────────────────────────
    // 우선순위 (높을수록 넓은 범위):
    // 아키텍처 변경 > Stage/Step 추가 > 에이전트 추가 > 스킬 추가/수정 > workflow.md 수정
    RETURN highest_priority_type(matched_types)
```

---

## Phase 선택 매트릭스

| 변경 유형           | Phase 1                    | Phase 2           | Phase 3             | Phase 4           | Phase 5                    | Phase 6  |
| ------------------- | -------------------------- | ----------------- | ------------------- | ----------------- | -------------------------- | -------- |
| 에이전트 추가       | 건너뜀 (Phase 0 결과 활용) | 배치 결정만       | **필수**            | 전용 스킬 필요 시 | 오케스트레이터 수정        | **필수** |
| 스킬 추가/수정      | 건너뜀                     | 건너뜀            | 건너뜀              | **필수**          | 연결 변경 시               | **필수** |
| 아키텍처 변경       | 건너뜀                     | **필수**          | 영향받는 에이전트만 | 영향받는 스킬만   | **필수**                   | **필수** |
| Stage/Step 추가    | 건너뜀                     | **필수** (재설계) | 새 에이전트 필요 시 | 새 스킬 필요 시   | **필수** (workflow.md 수정) | **필수** |
| workflow.md 수정    | 건너뜀                     | 건너뜀            | 건너뜀              | 건너뜀            | **필수** (workflow.md 수정 + `orchestrator-template.md` Step 0·Step 2 읽기 로직 정합성 검증) | **필수** |

---

## 판단 가이드

**에이전트 추가** — 새 역할이 생기거나 기존 에이전트의 부담이 과도할 때. Phase 1(도메인 분석)은 이미 Phase 0 감사 결과가 있으므로 건너뜀.

**스킬 추가/수정** — 방법론·체크리스트·프로토콜만 변경. 에이전트 페르소나와 아키텍처는 그대로이므로 Phase 1~3 건너뜀.

**아키텍처 변경** — 패턴 변경(예: Pipeline → Fan-out/Fan-in) 또는 에이전트 3개 이상 동시 재편. 가장 넓은 범위이므로 Phase 2부터 전체 재검토.

**Stage/Step 추가** — 기존 워크플로우에 Stage나 Step를 삽입. `workflow.md`의 Stage-Step 구조 재설계(Phase 2)가 필수. 새 에이전트·스킬이 필요하면 Phase 3·4도 실행.

**workflow.md 수정** — Stage·Step 구조나 종료 조건만 변경. 에이전트·스킬 변경 없음. Phase 5에서 `workflow.md` 수정 후, 오케스트레이터 Step 0(체크포인트 stage/step 이름 일치 여부)·Step 2(step_block 추출 경로·exit_cond 유형) 읽기 로직이 변경된 구조와 정합한지 반드시 검증.

**아키텍처 변경 임계값** — 다음 중 하나라도 해당하면 아키텍처 변경으로 분류:

| 조건 | 예시 |
|------|------|
| 패턴 변경 | pipeline → fan_out_fan_in |
| 에이전트 3개 이상 동시 재편 | 추가·삭제·역할 재정의 합산 3개 이상 |
| 오케스트레이터 Step 2 핵심 분기 수정 | Step 실행 루프 구조 변경 |
| Stage 수 증감 | Stage 1 → Stage 2 추가, 또는 Stage 삭제 |

---

## Phase 실행 순서 규칙

Phase는 **번호 오름차순** 실행이 원칙이다. 역방향 실행 금지.

| 규칙 | 내용 |
|------|------|
| **Phase 4 → Phase 3 이후** | 스킬은 에이전트가 정의된 뒤 연결 가능. Phase 3 없이 Phase 4만 실행하는 것은 스킬 추가/수정 변경 유형일 때만 허용. |
| **Phase 5 → Phase 3·4 이후** | 오케스트레이터가 에이전트·스킬을 호출하므로, 호출 대상이 먼저 정의되어야 함. |
| **Phase 6 → 항상 마지막** | 변경 유형에 무관하게 마지막에 실행. |
| **"건너뜀" Phase** | Phase 0 감사에서 drift(불일치) 감지 시 해당 Phase 부분 실행. |
| **겹침 시 우선순위** | 여러 변경 유형이 겹치면 가장 넓은 범위(아키텍처 변경) 기준으로 실행. |

```
// Phase 실행 순서 의존성
Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
          (에이전트)  (스킬)    (오케스트)  (검증)

// 독립 실행 허용 (다른 Phase 불필요)
스킬 추가/수정:   Phase 4 → Phase 6
workflow.md 수정: Phase 5 → Phase 6
```

---

## 검증 규칙

- **"건너뜀"** 표기 Phase라도, Phase 0 감사에서 불일치(drift)가 감지되면 해당 Phase를 부분적으로 실행한다.
- Phase 6(검증)은 변경 유형에 관계없이 **항상 필수**다.
- 여러 변경 유형이 겹치면 가장 넓은 범위(아키텍처 변경)를 기준으로 삼는다.

---

## 실전 케이스 예시

### 케이스 A: 에이전트 1개 추가 + 전용 스킬 1개 추가

**상황:** 기존 Pipeline 하네스에 보안 검토 에이전트(`@security-reviewer`)와 전용 스킬(`security-checklist`)이 필요해짐.

```
classify_change → "에이전트 추가" (에이전트 추가 + 스킬 추가 복합 → 우선순위: 에이전트 추가 > 스킬 추가)

Phase 실행:
  Phase 3: @security-reviewer.md 신규 생성
  Phase 4: security-checklist/SKILL.md 신규 생성
  Phase 5: 오케스트레이터 스킬 수정
    - 팀 구성에 @security-reviewer 추가
    - Step N (security-review) 삽입
    - workflow.md Stage·Step 갱신
    - description에 "보안 검토", "취약점 점검" 키워드 추가
  Phase 6: 구조 검증 + 트리거 검증 (신규 에이전트 포함)

AGENTS.md 변경 이력: "@security-reviewer 추가 | 보안 검토 부재 피드백"
```

### 케이스 B: 기존 스킬 체크리스트만 강화

**상황:** `code-review` 스킬의 리뷰 기준이 부족하다는 피드백 → 체크리스트 항목 추가.

```
classify_change → "스킬 추가/수정" (에이전트 파일·아키텍처 무변경)

Phase 실행:
  Phase 4: code-review/SKILL.md 수정 (체크리스트 항목 추가)
  Phase 6: 스킬 실행 테스트(Phase 6-3) + 트리거 검증(Phase 6-4)
            구조 검증(Phase 6-1)은 frontmatter 변경이 없으면 생략 가능

AGENTS.md 변경 이력: "code-review 스킬 체크리스트 강화 | 리뷰 품질 피드백"
```

### 케이스 C: 아키텍처 패턴 변경 (Pipeline → Fan-out/Fan-in)

**상황:** 순차 분석 3단계를 병렬화하여 속도를 높이려 함. 기존 에이전트 3개 역할 재정의 포함.

```
classify_change → "아키텍처 변경"
  조건 매칭: 패턴 변경(pipeline → fan_out_fan_in) + 에이전트 3개 동시 재편

Phase 실행:
  Phase 2: 병렬 팬아웃 구조 재설계 (workflow.md Stage-Step 재정의)
           findings.md·tasks.md·checkpoint.json 흐름 재설계
  Phase 3: 영향받는 에이전트 3개 수정
           - wait_for_previous: false 병렬 호출 패턴 반영
           - 입출력 경로 재정의 (_workspace/{plan_name}/ 하위 분기)
  Phase 4: 병렬 실행 관련 스킬 수정 (있는 경우)
  Phase 5: 오케스트레이터 전면 수정
           - Step 실행 루프 배치 호출로 교체
           - checkpoint.json active_pattern 갱신 로직 추가
  Phase 6: 드라이런 테스트(Phase 6-5) 필수 포함

AGENTS.md 변경 이력: "아키텍처 Pipeline→Fan-out/Fan-in 변경 | 분석 속도 개선 목적"
```

### 케이스 D: 기존 Stage 1에 Stage 2(검증 스테이지) 추가

**상황:** 현재 단일 Stage(예: `sso-integration`)로 실행 중인 하네스에 최종 사용자 검증 Stage를 추가해야 함.

```
classify_change → "Stage/Step 추가"
  조건 매칭: Stage 수 증가 (1 → 2)

Phase 실행:
  Phase 2: workflow.md 재설계
           - Stage 1: sso-integration (기존, deliverable 명사구)
           - Stage 2: user-validation (신규, 사용자 승인 게이트: "검증 결과 확인 후 완료 처리")
           Stage 2 종료 조건·전환 프로토콜 정의 (이름은 kebab-case + deliverable 의미; `main`·`validate` 같은 generic placeholder 금지)
  Phase 3: @qa-validator 에이전트 추가 (신규 Stage 담당)
  Phase 4: validation-checklist 스킬 생성 (필요 시)
  Phase 5: 오케스트레이터 수정
           - Stage 2 실행 블록 추가
           - checkpoint.json Stage 전환(sso-integration → user-validation) 로직 추가
           - AGENTS.md 사용자 승인 게이트 명시
  Phase 6: Resume 흐름 테스트(Phase 6-6) 필수 — Stage 중간 중단 재개 시나리오

AGENTS.md 변경 이력: "Stage 2(user-validation) 추가 | 사용자 검증 게이트 부재 피드백"
```

---

## drift 처리 가이드

Phase 0 감사에서 불일치(drift)가 발견되면, 변경 유형 분류 전에 drift를 먼저 해소한다.

| drift 유형 | 발생 원인 | 처리 방법 |
|------------|-----------|-----------|
| **에이전트 파일 존재 / AGENTS.md 미등록** | 에이전트 추가 후 AGENTS.md 변경 이력 미기록 | AGENTS.md 변경 이력 보정 후 Phase 6-1 재검증 |
| **AGENTS.md 등록 / 에이전트 파일 없음** | 파일 삭제 누락 또는 이름 변경 미반영 | `ask_user`로 의도 확인 후 파일 복구 또는 AGENTS.md 항목 삭제 |
| **오케스트레이터 참조 에이전트 ≠ 실제 파일** | 리팩토링 중 파일명 변경 미반영 | Phase 5 부분 실행 — 오케스트레이터 에이전트명 수정 |
| **스킬 description 트리거 충돌** | 신규 스킬 추가 후 기존 스킬과 키워드 겹침 | Phase 6-4(트리거 검증) 부분 실행 — description 조정 |
| **checkpoint.json current_step ≠ workflow.md step명** | workflow.md 수정 후 checkpoint.json 미갱신 | `ask_user`로 현재 진행 위치 확인 후 checkpoint.json 수동 보정 |
| **오케스트레이터 SKILL.md 평면 Step 나열 (Stage 계층 부재)** | 초기 생성 시 Stage-Step 모델 미적용 (예: `examples/sso-dev-flow`처럼 `Step 0~4` 평면 헤더) | **`skill-writing-guide.md` §7-6 마이그레이션 가이드 6단계(M1~M6) 적용** — 인벤토리 → Stage 매핑 → 패턴 할당 → 종료 조건 변환 → 산출물 5종 작성 → schemas/ 번들. 정본 패키지: `references/examples/full-bundle/sso-style.md`. |
| **종료 조건이 자연어 ("QA 승인", "충분히", "완료되면")** | LLM 자의 해석 표현이 workflow.md 또는 오케스트레이터 SKILL.md에 잔존 | `orchestrator-template.md` Step 1.7 스키마 검증 루틴 적용 → 화이트리스트 위반 검출 시 검증 가능 술어로 재작성 (`task_*.json status=done`·`{file}.json의 verdict=PASS`·`iterations ≥ N` 등) |
| **workflow.md 필수 필드 누락** | `패턴`·`활성 에이전트`·`종료 조건`·`다음 step`·`최대 반복 횟수`·Stage `사용자 승인 게이트` 중 하나 이상 누락 | 즉시 보강. `SKILL.md` Phase 2-1의 [MANDATORY] 6 필드 표 참조. 누락 시 Zero-Tolerance Failure → ask_user → HALT |
| **findings.md 임의 섹션 사용** (`[Review: 단계]` 등) | 표준 섹션 미준수 | 표준 섹션으로 변환 (`[핵심 통찰]`·`[변경 요청]`·`[공유 변수/경로]` 등). `references/team-examples.md` "findings.md 표준 섹션 구조" 표 참조 |
| **task_*.json 영속 미사용** (tasks.md 단순 체크만) | 병렬 에이전트 보고가 tasks.md 직접 수정으로 대체됨 — race condition 위험 | 각 에이전트에게 `_workspace/tasks/task_{agent}_{id}.json` 작성 의무 부여. 메인이 GLOB 수집 후 ATOMIC_WRITE로 tasks.md 갱신 |

**drift 해소 원칙:** drift 항목이 1개라도 있으면 변경 유형 Phase 실행 전에 반드시 해소한다. drift 해소 자체도 Phase 6-1(구조 검증)로 확인 후 AGENTS.md 변경 이력에 기록한다.
