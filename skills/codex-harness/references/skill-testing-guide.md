# 스킬 테스트 & 반복 개선 가이드

하네스에서 생성한 스킬의 품질을 검증하고 반복적으로 개선하는 방법론. `SKILL.md` Phase 6(검증 및 테스트)의 보충 레퍼런스. 본 가이드는 **Codex CLI 오케스트레이션 환경**(서브에이전트 간 직접 통신 불가, 메인 에이전트가 Grader·Analyzer)을 전제로 작성되었다.

---

## 목차

1. [테스트 프레임워크 개요](#1-테스트-프레임워크-개요)
2. [테스트 프롬프트 작성법](#2-테스트-프롬프트-작성법)
3. [실행 테스트: With-skill vs Baseline](#3-실행-테스트-with-skill-vs-baseline)
4. [정량적 평가: Assertion 기반 채점](#4-정량적-평가-assertion-기반-채점)
5. [전문 에이전트 활용 (Grader / Comparator / Analyzer)](#5-전문-에이전트-활용-grader--comparator--analyzer)
6. [반복 개선 루프](#6-반복-개선-루프)
7. [Description 트리거 검증](#7-description-트리거-검증)
8. [워크스페이스 구조](#8-워크스페이스-구조)

---

## 1. 테스트 프레임워크 개요

스킬 품질 검증은 **정성적 평가**와 **정량적 평가**의 조합이다.

| 평가 유형 | 방법 | 적합한 스킬 |
|---|---|---|
| **정성적** | 사용자가 산출물을 직접 리뷰 | 문체, 디자인, 창작물 등 주관적 품질 |
| **정량적** | assertion 기반 자동 채점 | 파일 생성, 데이터 추출, 코드 생성 등 객관적 검증 가능 |

핵심 루프: **작성 → 병렬 테스트 실행 → 평가 → 개선 → 재테스트**

Codex CLI에서는 서브에이전트 간 통신이 없으므로, **메인 에이전트가 Grader·Analyzer 역할을 겸하거나 전용 QA 에이전트(`@grader`)를 호출**해 채점을 수행한다.

---

## 2. 테스트 프롬프트 작성법

### 2-1. 원칙

테스트 프롬프트는 **실제 사용자가 입력할 법한 구체적이고 자연스러운 문장**이어야 한다. 추상적이거나 인공적인 프롬프트는 테스트 가치가 낮다.

### 2-2. 나쁜 예

```
"PDF를 처리하라"
"데이터를 추출하라"
"차트를 생성하라"
```

### 2-3. 좋은 예

```
"다운로드 폴더에 있는 'Q4_매출_최종_v2.xlsx'에서 C열(매출)과 D열(비용)을
사용해서 이익률(%) 열을 추가해줘. 그리고 이익률 기준으로 내림차순 정렬."
```

```
"이 PDF에서 3페이지 표를 추출해서 CSV로 변환해줘. 표 헤더가 2줄로
되어 있어서 첫 번째 줄은 카테고리, 두 번째 줄이 실제 열 이름이야."
```

### 2-4. 프롬프트 다양성

- **공식적 / 캐주얼** 톤 혼합
- **명시적 / 암시적** 의도 혼합 (파일 형식을 직접 말하는 경우 vs 맥락으로 추론해야 하는 경우)
- **단순 / 복잡** 작업 혼합
- 일부는 약어, 오타, 캐주얼한 표현 포함

### 2-5. 커버리지

2~3개 프롬프트로 시작하되 다음을 커버하도록 설계:
- 핵심 사용 사례 1개
- 엣지 케이스 1개
- (선택) 복합 작업 1개

---

## 3. 실행 테스트: With-skill vs Baseline

### 3-1. 비교 실행 구조 (Codex CLI 병렬 호출)

각 테스트 프롬프트에 대해 두 개의 서브에이전트를 **단일 응답 턴에서 병렬 호출**한다.

**With-skill 실행:**
```
@tester-with-skill 호출
  프롬프트: "{테스트 프롬프트}"
  스킬 경로 명시: .gemini/skills/{skill-name}/
  출력 경로: _workspace/{skill-name}/iteration-N/eval-{id}/with_skill/outputs/
```

**Baseline 실행:**
```
@tester-baseline 호출
  프롬프트: "{테스트 프롬프트}"  (동일)
  스킬 활성화 금지 (activate_skill 호출 불가)
  출력 경로: _workspace/{skill-name}/iteration-N/eval-{id}/without_skill/outputs/
```

Codex CLI에서 에이전트 차원의 병렬성은 **`spawn_subagent` 도구 호출 시 `wait_for_previous: false`** 파라미터를 지정하여 확보한다. (셸 명령은 `run_shell_command`의 백그라운드 옵션으로 별개로 동시 실행 가능하지만, 평가용 에이전트 호출과는 구분된다.)

### 3-2. Baseline 선택

| 상황 | Baseline |
|---|---|
| 새 스킬 생성 | 스킬 없이 같은 프롬프트 실행 |
| 기존 스킬 개선 | 수정 전 스킬 버전(스냅샷) — iteration-N-1 디렉토리에 보존된 결과 재사용 |

### 3-3. 타이밍/비용 데이터 캡처

에이전트 완료 알림에서 소요 시간과 토큰을 **즉시** 저장한다. 알림 시점에만 접근 가능하고 이후 복구할 수 없다.

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

Codex CLI는 실행 결과에 토큰/시간 메타데이터가 포함되므로, 메인 에이전트는 이를 `_workspace/{skill-name}/iteration-N/eval-{id}/{variant}/timing.json`에 `write_file`로 기록한다.

---

## 4. 정량적 평가: Assertion 기반 채점

### 4-1. Assertion 작성 원칙

산출물이 객관적으로 검증 가능한 경우, 자동 채점을 위한 assertion을 정의한다.

**좋은 assertion:**
- 객관적으로 참/거짓 판별 가능
- 서술적인 이름으로 결과만 봐도 무엇을 검사하는지 명확
- 스킬의 **핵심 가치**를 검증

**나쁜 assertion:**
- 스킬 유무와 무관하게 항상 통과하는 것 (예: "출력이 존재한다")
- 주관적 판단이 필요한 것 (예: "잘 작성되었다")

### 4-2. 프로그래밍 가능한 검증

assertion이 코드로 검증 가능하면 스크립트로 작성한다. 눈으로 확인하는 것보다 빠르고 신뢰성 있으며, iteration마다 재사용 가능.

Codex CLI에서는 메인 에이전트가 `run_shell_command`로 검증 스크립트(파이썬·쉘 등)를 실행해 결과를 `grading.json`에 기록한다.

### 4-3. Non-discriminating Assertion 주의

"두 구성(With-skill / Baseline) 모두에서 100% 통과"하는 assertion은 스킬의 차별적 가치를 측정하지 못한다. 이런 assertion은 제거하거나, 더 도전적인 것으로 교체한다.

### 4-4. 채점 결과 스키마

```json
{
  "expectations": [
    {
      "text": "이익률 열이 추가됨",
      "passed": true,
      "evidence": "E열에 'profit_margin_pct' 열 확인"
    },
    {
      "text": "이익률 기준 내림차순 정렬",
      "passed": false,
      "evidence": "정렬 없이 원본 순서 유지됨"
    }
  ],
  "summary": {
    "passed": 1,
    "failed": 1,
    "total": 2,
    "pass_rate": 0.50
  }
}
```

이 스키마는 `_workspace/{skill-name}/iteration-N/eval-{id}/{variant}/grading.json` 경로에 저장한다.

> **경로 구분:**
> - **장기 반복 개선 (이 파일):** `_workspace/{skill-name}/iteration-N/eval-{id}/{variant}/grading.json`
> - **하네스 구축 시 일회성 검증 (`SKILL.md` Phase 6):** `_workspace/evals/{timestamp}/grading.json`
>
> 두 경로는 용도가 다르므로 공존 가능. Phase 6 집계 시 두 경로 모두 스캔하거나 대상 경로를 명시해야 한다.

---

## 5. 전문 에이전트 활용 (Grader / Comparator / Analyzer)

Codex CLI 환경에서는 서브에이전트 간 직접 통신이 불가능하므로, 평가 전용 에이전트들을 **메인 에이전트가 순차 호출**하여 결과를 `findings.md`·`grading.json`으로 중개한다.

### 5-1. Grader (채점자)

Assertion 기반 채점을 수행하고, 산출물에서 검증 가능한 주장을 추출해 교차 검증한다.

**역할:**
- Assertion별 통과/실패 판정 + 근거 제시
- 산출물에서 사실적 주장을 추출하고 검증
- Eval 자체의 품질에 대한 피드백 (assertion이 너무 쉽거나 모호한 경우 제안)

**권장 도구:** `ask_user`, `activate_skill`, `read_file`, `grep_search`, `run_shell_command` (`temperature: 0.2`).

### 5-2. Comparator (블라인드 비교자)

두 산출물을 A/B로 익명화해, 어느 쪽이 스킬을 사용한 결과인지 모르는 상태에서 품질을 판정한다.

**활용 시점:** "새 버전이 정말 더 나은가?"를 엄밀히 확인하고 싶을 때. 일반 반복 개선에서는 생략 가능.

**판정 기준:**
- 내용: 정확성, 완성도
- 구조: 조직화, 포맷팅, 사용성
- 종합 점수

**Codex CLI 주의:** 메인 에이전트는 두 산출물을 `_workspace/.../variant_A.md`·`variant_B.md`로 익명화 복사한 뒤 Comparator에 경로만 전달해야 한다. 프롬프트에 "with_skill"/"without_skill" 라벨이 노출되면 블라인드성이 깨진다.

### 5-3. Analyzer (분석자)

벤치마크 데이터에서 통계적 패턴을 분석한다:
- Non-discriminating assertion (두 구성 모두 통과 → 차별력 없음)
- 고분산 eval (결과가 실행마다 크게 달라짐 → 불안정)
- 시간/토큰 트레이드오프 (스킬이 품질은 높이지만 비용도 높이는 경우)

결과는 `_workspace/{skill-name}/iteration-N/benchmark.json`과 `findings.md` [핵심 통찰]에 기록한다.

**`benchmark.json` 스키마:**
```json
{
  "iteration": 1,
  "timestamp": "2026-04-25T12:00:00Z",
  "eval_count": 3,
  "with_skill": {
    "pass_rate": 0.83,
    "avg_tokens": 45230,
    "avg_duration_ms": 18500
  },
  "without_skill": {
    "pass_rate": 0.50,
    "avg_tokens": 38100,
    "avg_duration_ms": 12300
  },
  "skill_delta": {
    "pass_rate_improvement": 0.33,
    "token_overhead": 7130,
    "duration_overhead_ms": 6200
  },
  "non_discriminating": ["eval-simple-csv-export"],
  "high_variance": [],
  "notes": "단순 CSV 추출 assertion은 두 구성 모두 통과 — 제거 대상"
}
```

---

## 6. 반복 개선 루프

### 6-1. 피드백 수집

사용자에게 산출물을 보여주고 피드백을 받는다. 빈 피드백은 "이상 없음"으로 해석한다.

### 6-2. 개선 원칙

1. **피드백을 일반화하라** — 테스트 예시에만 맞는 좁은 수정은 오버피팅이다. 원리 수준에서 수정한다.
2. **무게를 벌지 않는 것은 제거하라** — 트랜스크립트를 읽고, 스킬이 에이전트에게 비생산적인 작업을 시키고 있다면 삭제한다.
3. **Why를 설명하라** — 사용자의 피드백이 간결하더라도, 왜 그것이 중요한지 이해하고 그 이해를 스킬에 반영한다.
4. **반복 작업은 번들링하라** — 모든 테스트에서 같은 헬퍼 스크립트가 생성되면, `scripts/`에 미리 포함한다.

### 6-3. 반복 절차

```
1. 스킬 수정
2. 새 iteration-N+1/ 디렉토리에 모든 테스트 케이스 재실행
3. 사용자에게 결과 제시 (이전 iteration과 비교)
4. 피드백 수집 (모호하면 ask_user)
5. 다시 수정 → 반복
```

**종료 조건:**
- 사용자가 만족
- 피드백이 모두 비어 있음 (모든 산출물 이상 없음)
- 의미 있는 개선이 더 이상 없음

### 6-4. 초안 → 재검토 패턴

스킬 수정 시, 초안을 작성한 후 **새로운 시각으로 다시 읽고** 개선한다. 한 번에 완벽하게 쓰려 하지 말고, 초안-검토 사이클을 거친다.

---

## 7. Description 트리거 검증

Codex CLI의 트리거 라우터는 description만 보고 스킬을 선택한다. 따라서 description이 스킬의 **유일한 실질적 API**다.

### 7-1. 트리거 Eval 쿼리 작성

20개의 eval 쿼리를 작성한다 — should-trigger 10개 + should-NOT-trigger 10개.

**쿼리 품질 기준:**
- 실제 사용자가 입력할 법한 구체적이고 자연스러운 문장
- 파일 경로, 개인적 맥락, 열 이름, 회사명 등 구체적 디테일 포함
- 길이·톤·형식 다양하게 혼합
- 명확한 정답보다 **경계 케이스(edge case)**에 집중

**Should-trigger 쿼리 (10개):**
- 다양한 표현의 같은 의도 (공식적/캐주얼)
- 스킬·파일 유형을 명시적으로 말하지 않지만 분명히 필요한 경우
- 비주류 사용 사례
- 다른 스킬과 경쟁하지만 이 스킬이 이겨야 하는 경우

**Should-NOT-trigger 쿼리 (10개):**
- **Near-miss가 핵심** — 키워드가 유사하지만 다른 도구·스킬이 적합한 쿼리
- 명백히 무관한 쿼리("피보나치 함수 작성")는 테스트 가치 없음
- 인접 도메인, 모호한 표현, 키워드 겹침 but 맥락이 다른 경우

### 7-2. 기존 스킬 충돌 검증

새 스킬의 description이 기존 스킬의 트리거 영역과 겹치지 않는지 확인한다.

1. 기존 스킬 목록의 description을 수집 (`.gemini/skills/*/SKILL.md`를 `glob`·`read_file`로 전수 스캔).
2. 새 스킬의 should-trigger 쿼리가 기존 스킬을 잘못 트리거하지 않는지 확인.
3. 충돌 발견 시 description의 **경계 조건**을 더 명확히 기술(유사 스킬과의 차별점 명시).

### 7-3. 자동 최적화 (선택적 고급 기능)

description 최적화가 필요한 경우:

1. 20개 eval 쿼리를 Train(60%) / Test(40%) split.
2. 현재 description으로 트리거 정확도 측정.
3. 실패 케이스를 분석하여 개선된 description 생성.
4. Test set 기준으로 best description 선택 (Train set 기준 ❌ — 과적합 방지).
5. 최대 5회 반복.

> Codex CLI 자동화는 `gemini -p "..."`를 `run_shell_command`로 호출하는 스크립트로 수행한다. 토큰 비용이 높으므로 스킬이 충분히 안정화된 후 최종 단계에서 실행한다.

---

## 8. 워크스페이스 구조

테스트·평가 결과를 체계적으로 관리하는 디렉토리 구조.

> **명칭 구분:** 여기서 `{skill-name}`은 **테스트 중인 스킬의 이름**이다. 오케스트레이션 실행 중 사용하는 `_workspace/{plan_name}/`의 `{plan_name}`과 별개의 레벨이다. 스킬 테스트 결과는 `_workspace/{skill-name}/` 하위에, 오케스트레이션 실행 산출물은 `_workspace/{plan_name}/` 하위에 분리 저장된다.

```
_workspace/{skill-name}/
├── iteration-1/
│   ├── eval-descriptive-name-1/
│   │   ├── eval_metadata.json
│   │   ├── with_skill/
│   │   │   ├── outputs/
│   │   │   ├── timing.json
│   │   │   └── grading.json
│   │   └── without_skill/
│   │       ├── outputs/
│   │       ├── timing.json
│   │       └── grading.json
│   ├── eval-descriptive-name-2/
│   │   └── ...
│   └── benchmark.json
├── iteration-2/
│   └── ...
└── evals/
    └── evals.json
```

**규칙:**
- eval 디렉토리는 숫자가 아닌 **서술적 이름** 사용 (예: `eval-multi-page-table-extraction`).
- 각 iteration은 독립 디렉토리에 보존 (이전 iteration 덮어쓰기 금지).
- `_workspace/`는 삭제하지 않음 — 사후 검증·감사 추적·블라인드 비교용.
- `evals.json`에 **전체 세션의 평가 메타데이터**(스킬 버전, 총 iteration 수, 최종 pass rate 등)를 누적 기록해 하네스의 장기 품질 추이를 추적한다.

**`evals.json` 스키마:**
```json
{
  "skill_name": "pdf-extractor",
  "skill_version": "1.0.0",
  "created_at": "2026-04-25T10:00:00Z",
  "total_iterations": 3,
  "final_pass_rate": 0.85,
  "iterations": [
    {
      "iteration": 1,
      "eval_count": 3,
      "pass_rate": 0.67,
      "timestamp": "2026-04-25T10:00:00Z",
      "notes": "초기 버전 — assertion 3개 중 2개 통과"
    },
    {
      "iteration": 2,
      "eval_count": 3,
      "pass_rate": 0.83,
      "timestamp": "2026-04-25T11:00:00Z",
      "notes": "다단계 표 처리 개선 후 재테스트"
    }
  ]
}
```

---

## 오케스트레이터 테스트 시나리오

오케스트레이터는 반드시 **정상 흐름 1개 + 에러 흐름 1개 + 재개(Resume) 흐름 1개** 이상을 스킬 본문에 기술한다.

> **명칭 구분:** "오케스트레이터 Step 0~5"는 **오케스트레이터 스킬 자체의 내부 실행 단계**다(컨텍스트 확인·초기화·에이전트 호출·QA·통합·보고). `workflow.md`의 Stage·Step 계층과 별개 개념이다.

### 정상 흐름

1. 사용자가 `{입력}`을 제공.
2. 오케스트레이터 Step 0에서 `_workspace/` 미존재 확인 → 초기 실행 모드 선택.
3. 오케스트레이터 Step 1에서 `workflow.md`·`tasks.md`·`findings.md` 초기화.
   - `workflow.md`: Stage 1(`{plan_name}` deliverable kebab-case) / Step 1(deliverable kebab-case) / 활성 에이전트 목록 기록. **placeholder(`main`) 금지** — Jira 제목 컨벤션.
   - `checkpoint.json`: `current_stage: "{deliverable-kebab}"`, `current_step: "{deliverable-kebab}"`, `active_pattern: {첫 step 패턴}`, `status: "in_progress"` 초기화.
4. 오케스트레이터 Step 2에서 [Step 실행 루프] — workflow.md의 현재 Step 에이전트 호출.
   - @analyst → @coder 순차 실행 (병렬 가능한 구간은 배치 호출).
5. 오케스트레이터 Step 3에서 @reviewer 호출 → `findings.md` 충돌 없음 확인.
6. 오케스트레이터 Step 4에서 `_workspace/{plan_name}/final_{output}.md` 생성.
7. 오케스트레이터 Step 5에서 사용자에게 요약 보고.
8. **예상 결과:** `_workspace/{plan_name}/final_{output}.md` 존재, `tasks.md` 전 항목 `Done`.

### 재개 흐름 (Persistence Test)

1. @analyst 호출 완료, @coder 호출 중 네트워크 장애로 세션 종료.
2. 사용자 재호출 → 오케스트레이터 Step 0에서 `checkpoint.json` 발견.
3. `checkpoint.json`의 `current_stage`·`current_step` 복원 → 해당 step 진입 지점 확인.
4. @analyst 산출물 존재 확인 → @coder 단계부터 즉시 재개.
5. **예상 결과:** @analyst 작업 스킵, @coder 이후 작업만 완료됨.

### 에러 흐름 (Fix Loop)

1. 오케스트레이터 Step 3에서 @reviewer가 @coder의 결과물을 반려 (보안 취약점 발견).
2. 오케스트레이터가 `findings.md` [변경 요청]에 반려 사유 기록.
3. 오케스트레이터가 @coder를 재호출하며 @reviewer의 리포트를 주입.
4. @coder가 취약점을 수정하여 신규 산출물 생성.
5. @reviewer 재검증 통과 → 오케스트레이터 Step 4로 진행.
6. 최종 보고에 "에러 복구: @reviewer 반려 후 @coder 수정을 거쳐 최종 통과" 명시.

### expert_pool 시나리오 — 분류 모호 경로

1. 사용자가 "성능과 보안 모두 검토해줘" 입력 (복수 도메인 혼재).
2. 오케스트레이터 Step 2 expert_pool: CLASSIFY 결과 AMBIGUOUS.
3. `ask_user("전문가 목록: [@perf-analyst, @security-analyst] 중 어느 분께 맡길까요?")` 호출.
4. 사용자가 "@security-analyst"로 응답.
5. findings.md [라우팅 근거]에 `"- @security-analyst: 사용자 직접 지정"` 기록.
6. @security-analyst 호출 → task 파일 기록 → 종료 조건 충족.
7. **예상 결과:** AMBIGUOUS 경로 → ask_user 발동, 사용자 지정 에이전트가 선택됨.

### handoff 시나리오 — [NEXT_AGENT] 없는 단독 완료

1. @log-analyzer 호출 → 분석 완료, 응답에 `[NEXT_AGENT]` 키워드 없음.
2. 오케스트레이터가 ELSE 분기 진입: `task_{log-analyzer}_{id}.json` 기록 (단독 완료).
3. 종료 조건 검사 → 충족 → Step 전환.
4. **예상 결과:** handle_handoff 미호출, task 파일은 active_agents[0] 기준 기록.

---

## 참고 링크

- 채점 스키마(`grading.json`)의 간소형은 `references/skill-writing-guide.md`에 수록되어 있다.
- Phase 6 검증 절차는 `SKILL.md`의 워크플로우 Phase 6 항목을 따른다.
- Stage-Step 워크플로우 상세: `references/stage-step-guide.md`.
- **Stage-Step 워크플로우 테스트 시나리오** (시나리오 1~6): `references/stage-step-guide.md` 참조.
