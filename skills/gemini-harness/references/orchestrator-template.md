# 오케스트레이터 스킬 고도화 템플릿

오케스트레이터는 메인 에이전트가 오케스트레이션 로직을 실행하기 위해 사용하는 상위 스킬이다. Gemini CLI 환경은 **서브에이전트 간 직접 통신이 불가능**하므로, 메인 에이전트가 유일한 **Data Broker**로서 `findings.md`·`tasks.md`를 매개로 팀을 조율한다. 본 템플릿은 Gemini CLI 한 가지 실행 모드(파일 기반 브로커링)만을 다룬다.

> **주의:** Claude Code의 `TeamCreate`, `SendMessage`, `TaskCreate`, 서브에이전트 병렬 실행 플래그(`run_in_background`) 같은 팀/태스크 API는 Gemini CLI에 존재하지 않는다. 절대 사용하지 말고, 아래 파일 기반 프로토콜을 따른다. (단, **셸 명령 수준의 백그라운드 실행**은 Gemini CLI의 `run_shell_command`가 지원하므로, dev server·빌드 워처·장기 테스트 데몬 띄우기 용도로는 별도로 사용 가능하다.)

---

## 오케스트레이터 기본 구조 (Data Broker 강화형)

```markdown
---
name: {domain}-orchestrator
description: "{도메인} 하네스 오케스트레이터. 발견 사항 공유(findings.md)와 작업 관리(tasks.md)를 통해 가상 팀을 조율한다. {초기 실행 키워드}. 후속 작업({도메인} 결과 수정/부분 재실행/업데이트/보완/다시 실행/이전 결과 개선) 시에도 반드시 이 스킬을 사용하여 일관성을 유지하라."
---

# {Domain} Orchestrator

## 가상 팀 구성 및 전문 도구 세트

> **모든 에이전트 공통 필수 도구:** `ask_user`, `activate_skill` (이하 표에서는 생략하여 역할별 차별 도구만 표기).

| agent     | 에이전트 타입        | 역할   | 스킬    | 출력          |
| --------- | -------------------- | ------ | ------- | ------------- |
| {agent-1} | {커스텀 또는 빌트인} | {역할} | {skill} | {output-file} |
| {agent-2} | {커스텀 또는 빌트인} | {역할} | {skill} | {output-file} |
| ...       |                      |        |         |               |

## 워크플로우 및 데이터 브로커링 로직

### Phase 0: 컨텍스트 확인 (재실행 감지)

기존 산출물 존재 여부를 확인하여 실행 모드를 결정한다:

1. `_workspace/` 디렉토리 존재 여부 확인
2. 실행 모드 결정:
   - **`_workspace/` 미존재** → 초기 실행. Phase 1로 진행
   - **`_workspace/` 존재 + 사용자가 부분 수정 요청** → 부분 재실행. 해당 에이전트만 재호출하고, 기존 산출물 중 수정 대상만 덮어쓴다
   - **`_workspace/` 존재 + 새 입력 제공** → 새 실행. 기존 `_workspace/`를 `_workspace_{YYYYMMDD_HHMMSS}/`로 이동한 뒤 Phase 1 진행
3. 부분 재실행 시: 이전 산출물 경로를 에이전트 프롬프트에 포함하여, 에이전트가 기존 결과를 읽고 피드백을 반영하도록 지시

### Phase 1: 준비 및 태스크 보드 초기화

1. 사용자 입력 분석 — {무엇을 파악하는지}
2. 작업 디렉토리에 `_workspace/` 생성
   - **초기 실행**: 새 `_workspace/` 생성
   - **새 실행**: 기존 `_workspace/`를 `_workspace_{YYYYMMDD_HHMMSS}/`로 이동한 직후 새 `_workspace/` 재생성
3. 입력 데이터를 `_workspace/{plan_name}/`에 저장

### Phase 2: 서브에이전트 호출 및 제어 (`invoke_agent` 활용)

메인 에이전트는 각 단계마다 **반드시 시스템 도구인 `invoke_agent`를 사용**하여 다음 브로커링 루프를 수행한다.

1. **사전 브리핑:** 호출 전 `findings.md`를 읽어 현재까지의 발견 사항을 파악한다.
2. **에이전트 호출:** `invoke_agent(agent_name="...", prompt="...")` 도구를 사용한다.
   - **고급 컨텍스트 주입:** 프롬프트 내에 `@{_workspace/findings.md}` 구문을 직접 포함하여 서브에이전트가 작업 중인 최신 통찰을 즉시 참조하게 할 수 있다.
   - 예: `invoke_agent(agent_name="analyst", prompt="@{_workspace/findings.md}의 요구사항을 기반으로 심층분석을 수행하고, 결과를 @{_workspace/{plan_name}/01_analysis.md}에 기록하라.")`
3. **병렬/순차 제어 (`wait_for_previous`):**
   - **병렬 (Fan-out):** 의존성이 없는 에이전트 호출 시 `wait_for_previous: false`로 설정하여 단일 턴 내 동시 실행을 유도한다.
   - **순차 (Pipeline):** 이전 결과가 반드시 필요하면 `wait_for_previous: true`로 설정한다.
4. **결과 요약 브로커링:** 서브에이전트의 전체 로그를 모두 분석하기보다, `invoke_agent`가 반환한 **"요약된 실행 결과"**를 우선적으로 활용하여 `findings.md`를 갱신함으로써 메인 에이전트의 컨텍스트 윈도우를 효율적으로 관리한다.
   - **자문 스타일 처리:** 에이전트가 자문(Consultative) 모드로 쓰인 경우, 결과 파일이 없을 수 있다. 이 때는 반환된 "의견"이나 "체크리스트"를 `findings.md`의 [핵심 통찰]에 즉시 최신화한다.
5. **태스크 보드 갱신:** 매 에이전트 완료 시 `tasks.md`의 상태를 `Todo → In-Progress → Done`으로 전환한다.

### Phase 3: 교차 검증 및 데이터 정합성 해결 (Feedback Loop 강화)

- **상충 중개:** Analyst와 Coder의 산출물이 상충하면, 오케스트레이터가 `findings.md`의 [데이터 충돌] 섹션에 모순점을 명시하고 Reviewer에게 최종 판정을 요청한다.
- **증분 QA & Fix Loop:** 전체 완성 후가 아니라, 각 모듈(생산자+소비자)이 완성되는 즉시 Reviewer를 호출해 피드백 루프를 짧게 유지한다.
  - **피드백 루프 로직:** Reviewer가 산출물을 반려하면, 오케스트레이터는 반려 사유가 담긴 `_workspace/{plan_name}/03_review.md`를 생산자(@coder 등)의 프롬프트에 주입하여 재작성을 지시한다.
  - **산출물 버전 관리:** 기존 산출물을 단순히 덮어쓰는 대신, `_workspace/{plan_name}/02_code_v1.md`처럼 버전을 명시하거나 `_workspace/history/`에 백업하여 변경 이력을 추적 가능하게 관리한다.
  - **재시도 제한:** 이 루프는 최대 3회까지만 수행한다. 3회 초과 시 오케스트레이터는 `ask_user`를 통해 사용자에게 중단 여부나 수동 개입 경로를 확인한다.
- **상태 업데이트:** 매 단계 완료 후 `tasks.md`의 상태와 산출물 경로를 갱신한다.

### Phase 4: 통합 및 최종 산출

1. 모든 에이전트의 산출물을 `read_file`로 수집한다.
2. `findings.md`의 [공유 변수/경로]를 기준으로 충돌을 최종 해소한다.
3. 최종 산출물을 `_workspace/{plan_name}/final_{output}.md`에 생성한다.

### Phase 5: 아카이브 및 정리 (Findings & Tasks 관리 고도화)

1. **상세 기록 보존:** 작업 중 `_workspace/findings.md` 및 `_workspace/tasks.md`에 기록된 모든 상세 내용을 `_workspace/{plan_name}/findings.md` 및 `_workspace/{plan_name}/tasks.md`로 복사하여 플랜별 이력과 태스크 상태를 보존한다.
2. **중앙 findings 요약:** 메인 `_workspace/findings.md`의 내용을 비우고, 해당 플랜의 **[최종 결과 요약]**과 상세 내용이 담긴 **[아카이브 경로]**(`_workspace/{plan_name}/findings.md`)만 남긴다.
3. **보존:** `_workspace/` 전체 구조를 유지하여 사후 검증 및 부분 재실행 시 참조 가능하게 한다.
4. **보고:** 사용자에게 결과 요약과 아카이브된 상세 통찰 및 태스크 경로를 보고한다.

## 데이터 브로커링 프로토콜 (Mandatory Schema)

오케스트레이터는 데이터 일관성과 컨텍스트 효율을 위해 다음 스키마와 경로 규칙을 엄격히 준수해야 한다.

- **작업 경로 규칙:** 모든 실무 에이전트의 산출물은 `_workspace/{plan_name}/` 하위에 저장한다.
- **Findings (중개 데이터):** `_workspace/findings.md`
  - **업데이트 원칙:** 정보를 단순 누적하지 마라. 새로운 통찰이 발견되면 기존 내용을 **요약 및 최신화(Overwrite)**하여 컨텍스트 윈도우 낭비를 방지한다.
  - **작업 중 필드 (상세 기록):**
    - `# [핵심 통찰]`: 현재까지 발견된 도메인/기술적 핵심 사실 (가장 최신 상태로 유지).
    - `# [데이터 충돌]`: 에이전트 간 산출물 불일치 내역 (에이전트명, 충돌 지점, 해결 상태).
    - `# [공유 변수/경로]`: 에이전트들이 공통으로 참조해야 할 파일 경로 및 상수.
    - `# [변경 요청]`: 부분 재실행 시 사용자가 요청한 변경 사항 요약.
    - `# [다음 단계 지침]`: 다음 에이전트가 중점적으로 봐야 할 가이드.
  - **작업 완료 후 (아카이브 & 요약):**
    - **상세 이력 보존:** 위 모든 내용을 `_workspace/{plan_name}/findings.md` 및 `tasks.md`로 이동/복사.
    - **중앙 요약:** `_workspace/findings.md`를 초기화한 후, 해당 플랜의 **[최종 결과 요약]**과 **[상세 이력 경로]**만 남겨 후속 작업 시 컨텍스트 무게를 최소화한다.

- **Tasks (상태 데이터):** `_workspace/tasks.md`
  - `| ID | 에이전트 | 작업 내용 | 상태 | 산출물 경로 |` (Markdown Table 형식 권장)
  - 상태값: `Todo`, `In-Progress`, `Done`, `Blocked`

## 데이터 흐름
```

                     ┌──────────────────────────┐
                     │   메인 에이전트 (Broker)   │
                     │  findings.md / tasks.md  │
                     └────┬────────┬────────┬───┘
                          │        │        │
                 read_file│   호출 │        │read_file (Feedback)
                          ▼        ▼        ▼
                      @analyst  @coder  @reviewer
                          │        │        │
                          ▼        ▼        ▼
                  {plan_name}/  {plan_name}/  {plan_name}/
                  01_analysis.md 02_code.md   03_review.md
                          │        │        │
                          └────────┴───┬────┘
                                       │ (Re-entry Loop)
                                       ▼
                              _workspace/{plan_name}/final_{output}.md

```


핵심: 에이전트는 서로 파일조차 직접 읽지 않고, **오직 메인 에이전트만이 파일을 읽어 다음 에이전트 프롬프트에 요약을 주입**한다. 반려 시 Review 리포트를 생산자에게 다시 주입하는 것이 루프의 핵심이다.

## 에러 핸들링 및 자가 치유

| 상황 | 오케스트레이터 대응 로직 |
| :--- | :--- |
| 에이전트 1명 실패 | `findings.md`에 에러 원인 기록 → 1회 재시도. 재실패 시 `ask_user`로 대체 경로 질문. |
| 에이전트 과반 실패 | `tasks.md`에 중단 지점 저장 → 진행 여부를 `ask_user`로 확인 후 결정. |
| 타임아웃 | `tasks.md`에 중단 지점 저장 → 다음 세션 Phase 0에서 자동 감지·재개. |
| 데이터 모순 발견 | `findings.md` [데이터 충돌] 섹션에 기록 → 관련 에이전트들에게 모순점 피드백과 함께 재호출. 미해소 시 Reviewer 판정. |
| 에이전트 간 데이터 충돌 | 출처를 명시하여 병기. 임의 삭제 금지. Reviewer가 최종 선택. |
| 작업 상태 지연 | `tasks.md`의 `In-Progress` 항목을 점검 → `Blocked`로 전환 후 원인을 `findings.md`에 기록. |
| 루프 한계 도달 (3회) | `findings.md`에 최종 반려 사유 기록 → `ask_user`로 사람의 개입을 요청. |

## 테스트 시나리오

오케스트레이터는 반드시 **정상 흐름 1개 + 에러 흐름 1개** 이상을 스킬 본문에 기술한다.

### 정상 흐름
1. 사용자가 `{입력}`을 제공.
2. Phase 0에서 `_workspace/` 미존재 확인 → 초기 실행 모드 선택.
3. Phase 1에서 `tasks.md`·`findings.md` 초기화.
4. Phase 2에서 @analyst → @coder 순차 실행 (병렬 가능한 구간은 배치 호출).
5. Phase 3에서 @reviewer 호출 → `findings.md` 충돌 없음 확인.
6. Phase 4에서 `_workspace/{plan_name}/final_{output}.md` 생성.
7. Phase 5에서 사용자에게 요약 보고.
8. **예상 결과:** `_workspace/{plan_name}/final_{output}.md` 존재, `tasks.md` 전 항목 `Done`.

### 에러 흐름 (Fix Loop)
1. Phase 3에서 @reviewer가 @coder의 결과물을 반려 (보안 취약점 발견).
2. 오케스트레이터가 `findings.md` [변경 요청]에 반려 사유 기록.
3. 오케스트레이터가 @coder를 재호출하며 `@reviewer`의 리포트를 주입.
4. @coder가 취약점을 수정하여 신규 산출물 생성.
5. @reviewer 재검증 통과 → Phase 4로 진행.
6. 최종 보고에 "에러 복구: @reviewer 반려 후 @coder 수정을 거쳐 최종 통과" 명시.

## description 작성 시 후속 작업 키워드 (필수)

오케스트레이터 description은 **초기 실행 키워드만으로는 부족하다**. 다음 후속 작업 표현을 반드시 포함하지 않으면 첫 실행 후 하네스가 사실상 죽은 코드가 된다.

- 재실행 / 다시 실행 / 업데이트 / 수정 / 보완
- "{도메인}의 {부분}만 다시", "이전 결과 기반으로", "결과 개선"
- 도메인 특화 일상 표현 (예: 런치 전략 하네스라면 "런치", "홍보", "트렌딩" 등)

`description`에 후속 키워드가 누락되면 Gemini CLI의 트리거 라우터가 두 번째 호출부터 이 스킬을 선택하지 않는다.

## [추후 개선 포인트 (Minor Issues)]

본 오케스트레이터 템플릿의 향후 고도화 방향입니다.

1.  **Advanced Task Management:** `tasks.md`에 `priority` 및 `depends_on` 메타데이터 필드를 도입하여 더 복잡한 비순환 방향 그래프(DAG) 형태의 태스크 조율 지원.
2.  **Automated State Recovery:** 태스크가 `Blocked` 상태로 전환될 때, 오케스트레이터가 사전에 정의된 '대체 에이전트(Fallback Agent)'를 자동으로 할당하여 자가 치유 시도.
3.  **Standardized Naming Convention:** 모든 하네스에서 에이전트 명칭을 `@{domain}-{role}` (예: `@web-coder`, `@api-analyst`) 형식으로 엄격히 강제하여 멀티 하네스 환경에서의 충돌 방지.
```

## 작성 및 실행 원칙

1. **중개자 역할 강조:** 메인 에이전트는 단순히 도구를 호출하는 것이 아니라, 결과를 분석하여 **다음 에이전트의 입력(Context)을 고도화**하는 역할을 수행한다.
2. **엄격한 도구 격리:** 에이전트 호출 시 정의된 `tools` 범위를 벗어나는 작업을 시키지 않는다.
3. **가시성 확보:** 모든 중간 과정은 `findings.md`와 `tasks.md`를 통해 파일로 기록되어야 한다.
4. **절대 경로 사용:** 산출물 경로는 `_workspace/` 기준의 명시적 경로만 사용. 상대 경로·추측 경로 금지.
5. **Phase 의존성 명시:** 어떤 Phase가 어떤 Phase의 산출물에 의존하는지를 `tasks.md`의 `depends_on`·설명에 명시.
6. **현실적 에러 가정:** "모든 것이 성공한다"고 가정하지 않는다. 에러 핸들링 표 6행을 모두 커버해야 한다.
7. **테스트 시나리오 필수:** 정상 1 + 에러 1 이상을 스킬 본문에 포함. 없으면 Phase 5 검증 통과 불가.

## 실제 오케스트레이터 참고

팬아웃/팬인 패턴의 기본 흐름:
Phase 0(컨텍스트 확인) → Phase 1(태스크 보드 초기화) → Phase 2(에이전트 배치 호출) → Phase 3(Reviewer 증분 검증) → Phase 4(파일 기반 통합) → Phase 5(보존·보고).
에이전트 분업 예시는 `references/team-examples.md`를 참조.
