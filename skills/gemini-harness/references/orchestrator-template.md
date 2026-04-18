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

| 에이전트 | 유형 | 핵심 도구 세트 | 주요 산출물 |
| :--- | :--- | :--- | :--- |
| @{analyst} | Analyst | read_file, grep_search, google_web_search | `_workspace/01_analysis.md` |
| @{coder} | Coder | write_file, replace, run_shell_command | `_workspace/02_code.md` |
| @{reviewer} | Reviewer | read_file, grep_search, testing_tools | `_workspace/03_review.md` |

## 워크플로우 및 데이터 브로커링 로직

### Phase 0: 컨텍스트 확인 (재실행 감지)

오케스트레이터는 가장 먼저 기존 산출물을 점검하여 실행 모드를 결정한다.

1. `_workspace/` 디렉토리 존재 여부 확인.
2. 실행 모드 분기:
   - **미존재** → 초기 실행. Phase 1로 진행.
   - **존재 + 부분 수정 요청** → 부분 재실행. 해당 에이전트만 재호출하고 대상 산출물만 덮어쓴다. 기존 `findings.md`는 유지하며 [변경 요청] 섹션을 추가한다.
   - **존재 + 새 입력 제공** → 새 실행. 기존 `_workspace/`를 `_workspace_{YYYYMMDD_HHMMSS}/`로 이동한 뒤 Phase 1 진행.
3. 부분 재실행 시, 이전 산출물 경로를 에이전트 프롬프트에 명시하여 재작성이 아닌 **수정·보완**이 되도록 지시한다.

### Phase 1: 준비 및 태스크 보드 초기화

1. 사용자 입력을 분석하여 목표·제약·성공 기준을 추출한다.
2. `_workspace/00_input/`에 원본 입력을 보존한다.
3. `_workspace/tasks.md`에 전체 단계(Phase 1~N)와 담당 에이전트를 등록한다.
4. `_workspace/findings.md`를 생성하고 초기 요구사항 요약을 [핵심 통찰] 섹션에 기록한다.

### Phase 2: 서브에이전트 병렬/순차 실행

메인 에이전트는 각 단계마다 다음 **데이터 브로커링 루프**를 수행한다.

1. **사전 브리핑:** 호출 전 `findings.md`를 읽어 현재까지의 발견 사항을 파악한다.
2. **에이전트 호출:** `@{agent}` 직접 호출. 프롬프트에 `findings.md`의 핵심 요약을 포함하고, 예상 산출물 경로를 명시한다.
   - 예: `@{analyst}` 에게 "findings.md의 [핵심키워드]를 중심으로 심층 조사하고, 결과를 `_workspace/01_analysis.md`에 기록하라."
3. **병렬 실행 지침:** 의존성이 없는 에이전트는 메인 에이전트가 단일 응답 턴에서 여러 번 호출하여 동시 실행을 유도한다(Gemini CLI는 **서브에이전트 병렬 실행 플래그**가 없으므로, 에이전트 간 병렬성은 호출 배치로만 확보된다. 반면 셸 명령 자체는 `run_shell_command`의 백그라운드 옵션으로 병렬 구동 가능).
4. **사후 분석:** 에이전트의 산출물을 `read_file`로 읽고, 새로운 통찰·데이터 충돌을 `findings.md`에 실시간 업데이트한다.
5. **태스크 보드 갱신:** 매 에이전트 완료 시 `tasks.md`의 상태를 `Todo → In-Progress → Done`으로 전환한다.

### Phase 3: 교차 검증 및 데이터 정합성 해결

- **상충 중개:** Analyst와 Coder의 산출물이 상충하면, 오케스트레이터가 `findings.md`의 [데이터 충돌] 섹션에 모순점을 명시하고 Reviewer에게 최종 판정을 요청한다.
- **증분 QA:** 전체 완성 후가 아니라, 각 모듈(생산자+소비자)이 완성되는 즉시 Reviewer를 호출해 피드백 루프를 짧게 유지한다.
- **상태 업데이트:** 매 단계 완료 후 `tasks.md`의 상태와 산출물 경로를 갱신한다.

### Phase 4: 통합 및 최종 산출

1. 모든 에이전트의 산출물을 `read_file`로 수집한다.
2. `findings.md`의 [공유 변수/경로]를 기준으로 충돌을 최종 해소한다.
3. 최종 산출물을 `_workspace/final/{output}.md`에 생성한다.

### Phase 5: 정리

1. `_workspace/`는 **삭제하지 않고 보존**한다 — 사후 검증·감사 추적·부분 재실행에 사용한다.
2. 사용자에게 결과 요약과 주요 산출물 경로, `findings.md`의 [다음 단계 지침]을 보고한다.

## 데이터 브로커링 프로토콜

- **Findings (중개 데이터):** `_workspace/findings.md`
  - 섹션: [핵심 통찰], [데이터 충돌], [공유 변수/경로], [변경 요청], [다음 단계 지침]
- **Tasks (상태 데이터):** `_workspace/tasks.md`
  - 항목: [ID], [에이전트], [작업 내용], [상태: Todo/In-Progress/Done/Blocked], [연결 산출물]

## 데이터 흐름

```
                     ┌──────────────────────────┐
                     │   메인 에이전트 (Broker)   │
                     │  findings.md / tasks.md  │
                     └────┬────────┬────────┬───┘
                          │        │        │
                 read_file│   호출 │        │read_file
                          ▼        ▼        ▼
                      @analyst  @coder  @reviewer
                          │        │        │
                          ▼        ▼        ▼
                 01_analysis.md 02_code.md 03_review.md
                          │        │        │
                          └────────┼────────┘
                                   ▼
                              _workspace/final/{output}.md
```

핵심: 에이전트는 서로 파일조차 직접 읽지 않고, **오직 메인 에이전트만이 파일을 읽어 다음 에이전트 프롬프트에 요약을 주입**한다.

## 에러 핸들링 및 자가 치유

| 상황 | 오케스트레이터 대응 로직 |
| :--- | :--- |
| 에이전트 1명 실패 | `findings.md`에 에러 원인 기록 → 1회 재시도. 재실패 시 `ask_user`로 대체 경로 질문. |
| 에이전트 과반 실패 | `tasks.md`에 중단 지점 저장 → 진행 여부를 `ask_user`로 확인 후 결정. |
| 타임아웃 | `tasks.md`에 중단 지점 저장 → 다음 세션 Phase 0에서 자동 감지·재개. |
| 데이터 모순 발견 | `findings.md` [데이터 충돌] 섹션에 기록 → 관련 에이전트들에게 모순점 피드백과 함께 재호출. 미해소 시 Reviewer 판정. |
| 에이전트 간 데이터 충돌 | 출처를 명시하여 병기. 임의 삭제 금지. Reviewer가 최종 선택. |
| 작업 상태 지연 | `tasks.md`의 `In-Progress` 항목을 점검 → `Blocked`로 전환 후 원인을 `findings.md`에 기록. |

## 테스트 시나리오

오케스트레이터는 반드시 **정상 흐름 1개 + 에러 흐름 1개** 이상을 스킬 본문에 기술한다.

### 정상 흐름
1. 사용자가 `{입력}`을 제공.
2. Phase 0에서 `_workspace/` 미존재 확인 → 초기 실행 모드 선택.
3. Phase 1에서 `tasks.md`·`findings.md` 초기화.
4. Phase 2에서 @analyst → @coder 순차 실행 (병렬 가능한 구간은 배치 호출).
5. Phase 3에서 @reviewer 호출 → `findings.md` 충돌 없음 확인.
6. Phase 4에서 `_workspace/final/{output}.md` 생성.
7. Phase 5에서 사용자에게 요약 보고.
8. **예상 결과:** `_workspace/final/{output}.md` 존재, `tasks.md` 전 항목 `Done`.

### 에러 흐름
1. Phase 2에서 @coder가 `run_shell_command` 실패로 중단.
2. 오케스트레이터가 `findings.md`에 에러 로그 기록 → 1회 재시도.
3. 재시도 실패 → `ask_user`로 대체 경로 질의.
4. 사용자 답변 반영 후 @coder 재호출 성공.
5. Phase 3~5 정상 진행.
6. 최종 보고에 "에러 복구: @coder 1회 재시도 후 사용자 확정 경로로 성공" 명시.

## description 작성 시 후속 작업 키워드 (필수)

오케스트레이터 description은 **초기 실행 키워드만으로는 부족하다**. 다음 후속 작업 표현을 반드시 포함하지 않으면 첫 실행 후 하네스가 사실상 죽은 코드가 된다.

- 재실행 / 다시 실행 / 업데이트 / 수정 / 보완
- "{도메인}의 {부분}만 다시", "이전 결과 기반으로", "결과 개선"
- 도메인 특화 일상 표현 (예: 런치 전략 하네스라면 "런치", "홍보", "트렌딩" 등)

`description`에 후속 키워드가 누락되면 Gemini CLI의 트리거 라우터가 두 번째 호출부터 이 스킬을 선택하지 않는다.
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
