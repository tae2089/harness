# 오케스트레이터 절차 & 원칙

오케스트레이터 스킬 작성 시 공통으로 적용되는 에러 처리 절차, 검증 원칙, description 작성 가이드.
`orchestrator-template.md`의 Step 0~5 pseudocode와 함께 사용한다.

## 에러 핸들링 및 자가 치유

> **정본(canonical spec).** 다른 파일(qa-agent-guide, agent-design-patterns 등)의 재시도·Blocked·사용자 확인 요청 언급은 이 결정 트리를 따른다.

### 에러 대응 결정 트리 (pseudocode)

```
PROCEDURE handle_error(agent, task, error_type):

    // ── 즉시 사용자 확인 요청 (재시도 없음) ──────────────────────────────
    IF error_type == "ambiguous_input" OR error_type == "missing_params":
        CALL 사용자 확인 요청("입력 모호 또는 파라미터 누락: {상세}")
        RETURN

    IF error_type == "majority_failure":        // 과반 에이전트 실패
        apply_patch "_workspace/tasks.md" ← 중단 지점 기록
        CALL 사용자 확인 요청("과반 실패. 진행 여부 확인 요청.")
        RETURN

    // ── 자동 복구 (Step 0 재개) ──────────────────────────────────
    IF error_type == "timeout" OR error_type == "session_restart":
        // Step 0 재실행 시 checkpoint.json 감지 → 자동 재개
        // ※ 멱등성 필수: 각 에이전트는 산출물 파일 존재 여부를 먼저 확인하고
        //   이미 완료된 작업은 스킵해야 한다. 재개 횟수와 무관하게 결과가 동일해야 함.
        GOTO Step 0
        RETURN

    // ── 데이터 충돌 ──────────────────────────────────────────────
    IF error_type == "data_conflict":
        RECORD findings.md ← "[데이터 충돌]" 섹션에 출처 병기
        @reviewer 호출 (conflict_resolution_prompt)
        IF reviewer resolves conflict:
            RETURN
        ELSE:
            CALL 사용자 확인 요청("데이터 충돌 미해소: {상세}")
            RETURN

    // ── 재시도 가능한 실패 ───────────────────────────────────────
    // 해당: agent_failure | reviewer_reject | context_limit_exceeded
    // 해당: handoff_no_candidate (핸드오프 대상 없음)
    IF task.retries < 2:                        // 총 3회 미만
        task.retries += 1
        RECORD findings.md ← "재시도 {task.retries}/2: {에러 원인} → 접근법 변경"
        @agent 호출 (modified_prompt_with_feedback)
        RETURN

    // ── 3회 소진 → Blocked 프로토콜 ─────────────────────────────
    GOTO blocked_protocol

// ── Blocked 프로토콜 (공통) ──────────────────────────────────────
PROCEDURE blocked_protocol(agent, task):
    apply_patch "_workspace/tasks/task_{agent}_{id}.json":
        status  ← "blocked"
        result  ← null
        retries ← task.retries   // 최종값 보존
    RECORD findings.md ← "최종 반려: {사유} | 시도 이력: {이력}"
    // Step·Stage 전환 절대 금지
    DO NOT UPDATE checkpoint.json  // 역할 분리: blocked_protocol은 task 파일만 기록.
                                   // Step 2의 pre-blocked 검사가 다음 사이클 진입 시 task 파일을 감지하고
                                   // checkpoint를 blocked로 갱신한다. blocked_protocol이 직접 갱신하면 중복 갱신.
    CALL 사용자 확인 요청("Blocked: @{agent} — {사유}. 개입 요청.")
    HALT    // 임의 Skip·Done 절대 금지

// ── 특수 케이스: Handoff 순환 감지 ──────────────────────────────
// (A→B→A 무한루프 방지. call_history = checkpoint.json의 handoff_chain 필드)
PROCEDURE handle_handoff(next_agent):
    READ "_workspace/checkpoint.json" → ckpt
    call_history ← ckpt.handoff_chain ?? []     // 없으면 빈 배열

    IF next_agent IN call_history:
        RECORD findings.md ← "순환 핸드오프: {call_history} → {next_agent}"
        CALL 사용자 확인 요청("순환 핸드오프 감지: {경로}. 개입 요청.")
        HALT

    IF LENGTH(call_history) >= 3:               // 3단계 초과
        RECORD findings.md ← "핸드오프 3단계 초과: {call_history}"
        CALL 사용자 확인 요청("핸드오프 3단계 초과. 개입 요청.")
        HALT

    // 안전 → 이력 갱신 후 호출
    apply_patch "_workspace/checkpoint.json":
        ckpt.handoff_chain ← APPEND(call_history, next_agent)
        ckpt.last_updated  ← NOW()
    @next_agent 호출 (...)

// Step 전환 시 반드시 handoff_chain 초기화
// (checkpoint.json 갱신 시 handoff_chain: [] 로 리셋)
```

## 테스트 시나리오

> 정상 흐름 / 재개 흐름 / 에러 흐름 시나리오 전문: `references/skill-testing-guide.md` § **오케스트레이터 테스트 시나리오** (정상 흐름 / 재개 흐름 / 에러 흐름 3종).

## description 작성 시 후속 작업 키워드 (필수)

오케스트레이터 description은 **초기 실행 키워드만으로는 부족하다**. 다음 후속 작업 표현을 반드시 포함하지 않으면 첫 실행 후 하네스가 사실상 죽은 코드가 된다.

- 재실행 / 다시 실행 / 업데이트 / 수정 / 보완
- "{도메인}의 {부분}만 다시", "이전 결과 기반으로", "결과 개선"
- 도메인 특화 일상 표현 (예: 런치 전략 하네스라면 "런치", "홍보", "트렌딩" 등)

`description`에 후속 키워드가 누락되면 Codex CLI의 트리거 라우터가 두 번째 호출부터 이 스킬을 선택하지 않는다.

## 작성 및 실행 원칙

1. **중개자 역할 강조:** 메인 에이전트는 단순히 도구를 호출하는 것이 아니라, 결과를 분석하여 **다음 에이전트의 입력(Context)을 고도화**한다.
2. **영속성 우선:** 모든 주요 상태 변경 직후에 파일을 갱신하여 예기치 못한 종료에 대비한다.
3. **원자적 상태 통합:** 병렬 에이전트가 생성한 분할 작업 파일들을 오케스트레이터가 수집하여 통합함으로써 쓰기 충돌을 원천 차단한다.
4. **엄격한 SandBox Mode 격리:** 에이전트 호출 시 정의된 `sandbox_mode` 범위를 벗어나는 작업을 시키지 않는다.
5. **가시성 확보:** 모든 중간 과정은 `findings.md`와 `tasks.md`를 통해 파일로 기록되어야 한다.
6. **Step 의존성 명시:** workflow.md의 Step 순서와 종료 조건으로 의존성을 선언한다. Step N 완료 → Step N+1 진입 구조가 workflow.md에 명확히 표현되어야 한다.
7. **현실적 에러 가정:** "모든 것이 성공한다"고 가정하지 않는다. Step Blocked 시 Stage 전환 금지 규칙 포함.
8. **테스트 시나리오 필수:** 정상 1 + 에러 1 이상을 스킬 본문에 포함. 없으면 Step 5 검증 통과 불가.

## Stage·Step 전환 프로토콜

> Step 2의 Step 실행 루프, Stage 전환 게이트, 출입 통제 로직 전체 상세:
> **`references/stage-step-guide.md`** 참조.
