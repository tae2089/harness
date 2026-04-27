# 스킬 작성 가이드

하네스에서 생성하는 스킬의 품질을 높이기 위한 상세 작성 가이드. `SKILL.md` Phase 4(전문 스킬 및 오케스트레이터 생성)의 보충 레퍼런스. Codex CLI 서브에이전트 오케스트레이션 환경에 특화된 작성 스타일을 제공한다.

---

## 목차

0. [스킬 디렉토리 구조](#0-스킬-디렉토리-구조)
1. [Description 작성 패턴](#1-description-작성-패턴)
2. [본문 작성 스타일](#2-본문-작성-스타일)
3. [출력 형식 정의 패턴](#3-출력-형식-정의-패턴)
4. [예시 작성 패턴](#4-예시-작성-패턴)
5. [Progressive Disclosure 패턴](#5-progressive-disclosure-패턴)
6. [스크립트 번들링 판단 기준](#6-스크립트-번들링-판단-기준)
7. [데이터 브로커링 & 조율 패턴 (Codex CLI 고유)](#7-데이터-브로커링--조율-패턴-codex-cli-고유)
8. [데이터 스키마 표준](#8-데이터-스키마-표준)
9. [스킬에 포함하지 않을 것](#9-스킬에-포함하지-않을-것)

---

## 0. 스킬 디렉토리 구조

```
skill-name/
├── SKILL.md (필수)
│   ├── YAML frontmatter (name, description 필수)
│   └── Markdown 본문
└── Bundled Resources (선택)
    ├── scripts/    - 반복/결정적 작업용 실행 코드
    ├── references/ - 조건부 로딩하는 참조 문서
    └── assets/     - 출력에 사용되는 파일 (템플릿·이미지)
```

- `scripts/` — 에이전트들이 공통으로 작성하는 스크립트를 미리 번들링. `run_shell_command`로 직접 실행.
- `references/` — 자주 트리거되지 않는 상세 내용을 분리. 에이전트가 shell `cat`로 조건부 로드.
- `assets/` — 출력에 사용되는 템플릿·이미지 등 정적 파일.

---

## 1. Description 작성 패턴

Description은 스킬의 **유일한 트리거 메커니즘**이다. Codex CLI 트리거 라우터는 `.codex/skills/*/SKILL.md`의 `name` + `description`만 보고 스킬 사용 여부를 결정한다.

### 1-1. 트리거 메커니즘 이해

Codex는 기본 도구로 쉽게 처리할 수 있는 단순 작업에는 스킬을 호출하지 않는 경향이 있다. "이 PDF 읽어줘" 같은 단순 요청은 description이 완벽해도 트리거되지 않을 수 있다. **복잡하고 다단계이며 전문적인 작업일수록** 스킬 트리거 확률이 높다.

### 1-2. 작성 원칙

1. **스킬이 하는 일 + 구체적 트리거 상황**을 모두 기술한다.
2. 유사하지만 트리거하면 안 되는 경우를 구분하는 **경계 조건**을 명시한다.
3. 약간 **"pushy"하게** — 트리거 라우터가 보수적으로 판단하는 경향을 보상.
4. **후속 작업 키워드**(재실행·수정·보완·업데이트·부분 재실행)를 반드시 포함. 없으면 첫 실행 후 스킬이 사실상 죽은 코드가 된다.

### 1-3. 좋은 예시

```yaml
description: "PDF 파일 읽기, 텍스트·테이블 추출, 병합·분할·회전·워터마크,
  암호화·복호화, OCR 등 모든 PDF 작업을 수행. .pdf 파일을 언급하거나
  PDF 산출물을 요청하면 반드시 이 스킬을 사용할 것. 단순 '읽어달라'
  요청이 아닌 변환·편집·분석이 필요할 때 특히 유용. 이미 처리한 PDF를
  수정·재추출·재생성할 때에도 반드시 이 스킬을 사용."
```

```yaml
description: "엑셀·CSV·TSV 파일의 열 추가, 수식 계산, 서식, 차트,
  데이터 정제를 포함한 모든 스프레드시트 작업. 사용자가 스프레드시트를
  언급하면 — 심지어 캐주얼하게('다운로드 폴더의 xlsx')라고만 해도
  — 이 스킬을 사용할 것. 기존 결과 업데이트·열 재계산·정렬 변경도 포함."
```

### 1-4. 나쁜 예시

- `"데이터를 처리하는 스킬"` — 너무 모호, 파일·작업 불분명.
- `"PDF 관련 작업"` — 구체적 동작 나열 없음, 트리거 상황 미기술.
- `"X를 수행합니다"` — 후속 작업 키워드 누락으로 두 번째 호출부터 라우터가 무시.

---

## 2. 본문 작성 스타일

### 2-1. Why-First 원칙

LLM은 이유를 이해하면 엣지 케이스에서도 올바르게 판단한다. 강압적 규칙보다 맥락 전달이 효과적이다.

**나쁜 예:**
```markdown
ALWAYS use pdfplumber for table extraction. NEVER use PyPDF2 for tables.
```

**좋은 예:**
```markdown
테이블 추출에는 pdfplumber를 사용한다. PyPDF2는 텍스트 추출에 특화되어
있어 테이블의 행·열 구조를 보존하지 못하기 때문이다. pdfplumber는
셀 경계를 인식하여 구조화된 데이터를 반환한다.
```

### 2-2. 일반화 원칙

피드백이나 테스트 결과에서 문제가 발견되면, 특정 예시에만 맞는 좁은 수정 대신 **원리 수준에서 일반화**한다.

**오버피팅 수정:**
```markdown
"Q4 매출" 열이 있으면 해당 열을 숫자로 변환하라.
```

**일반화된 수정:**
```markdown
열 이름에 "매출", "금액", "수량" 등 수치를 암시하는 키워드가 있으면
해당 열을 숫자 타입으로 변환한다. 변환 실패 시 원본 값을 유지한다.
```

### 2-3. 명령형 어조

"~합니다", "~할 수 있습니다" 대신 "~한다", "~하라" 형태를 사용한다. 스킬은 지시서이다.

### 2-4. 컨텍스트 절약

컨텍스트 윈도우는 공공재다. 모든 문장이 토큰 비용을 정당화하는지 자문한다:
- "에이전트가 이미 알고 있는 내용인가?" → 삭제
- "이 설명이 없으면 에이전트가 실수하는가?" → 유지
- "구체적 예시 하나가 긴 설명보다 효과적인가?" → 예시로 대체

---

## 3. 출력 형식 정의 패턴

산출물의 형식이 중요한 스킬에서 사용한다:

```markdown
## 보고서 구조
다음 템플릿을 정확히 따른다:

# [제목]
## 요약
## 핵심 발견
## 권장 사항
```

형식 정의는 간결하게 하되, **실제 예시**를 포함하면 더 효과적이다. 서브에이전트가 생성하는 산출물을 오케스트레이터(메인 에이전트)가 자동 파싱해야 한다면, 형식 규격을 JSON 스키마나 YAML로 엄격히 고정한다.

---

## 4. 예시 작성 패턴

예시는 긴 설명보다 효과적이다:

```markdown
## 커밋 메시지 형식

**예시 1:**
입력: JWT 토큰 기반 사용자 인증 추가
출력: feat(auth): JWT 기반 인증 구현

**예시 2:**
입력: 로그인 페이지에서 비밀번호 표시 버튼이 동작하지 않는 버그 수정
출력: fix(login): 비밀번호 표시 토글 버튼 동작 수정
```

**좋은 예시의 조건:**
- 입력과 출력이 **쌍으로** 제시
- 경계 케이스·오류 사례도 최소 1개 포함
- 도메인 용어가 실제로 등장

---

## 5. Progressive Disclosure 패턴

`SKILL.md` 본문은 **500줄 이내**로 유지하고, 상세 레퍼런스·큰 데이터 스키마·도메인별 지식은 `references/` 하위 파일로 분리한다. 에이전트가 필요할 때만 해당 파일을 shell `cat`로 로드하도록 유도한다.

### 5-1. 패턴 1: 도메인별 분리

```
bigquery-skill/
├── SKILL.md (개요 + 도메인 선택 가이드)
└── references/
    ├── finance.md   (매출, 빌링 메트릭)
    ├── sales.md     (기회, 파이프라인)
    └── product.md   (API 사용량, 기능)
```

사용자가 매출에 대해 물으면 `finance.md`만 로드한다.

### 5-2. 패턴 2: 조건부 상세

```markdown
# DOCX 처리

## 문서 생성
docx-js로 새 문서를 생성한다. → [DOCX-JS.md](references/docx-js.md) 참조.

## 문서 편집
단순 편집은 XML을 직접 수정.
**추적 변경이 필요하면**: [REDLINING.md](references/redlining.md) 참조.
```

### 5-3. 패턴 3: 대형 레퍼런스 파일 구조

300줄 이상의 reference 파일은 상단에 목차를 포함한다:

```markdown
# API 레퍼런스

## 목차
1. [인증](#인증)
2. [엔드포인트 목록](#엔드포인트-목록)
3. [에러 코드](#에러-코드)
4. [레이트 리밋](#레이트-리밋)

---

## 인증
...
```

---

## 6. 스크립트 번들링 판단 기준

테스트 실행에서 에이전트들의 트랜스크립트를 관찰한다. 다음 패턴이 보이면 번들링 대상이다.

| 신호 | 조치 |
|---|---|
| 3개 테스트 중 3개에서 동일한 헬퍼 스크립트 생성 | `scripts/`에 번들링 |
| 매번 같은 `pip install` / `npm install` 실행 | 스킬에 의존성 설치 단계 명시 |
| 동일한 다단계 접근법 반복 | 스킬 본문에 표준 절차로 기술 |
| 매번 비슷한 에러 후 같은 회피책 적용 | 스킬에 알려진 문제와 해결법 기술 |

번들링된 스크립트는 반드시 **실행 테스트**를 거친다. `run_shell_command`로 실제 실행 결과를 확인한 뒤 스킬에 포함한다.

---

## 7. 데이터 브로커링 & 조율 패턴 (Codex CLI 고유)

Codex CLI 환경에서는 메인 에이전트가 **Data Broker** 역할을 수행함을 전제로 스킬을 작성한다. 서브에이전트 간 직접 통신이 불가능하므로, 스킬은 다음 원칙을 따른다.

### 7-1. 산출물 규격화

서브에이전트가 생성하는 파일이 **다른 에이전트나 메인 에이전트가 읽기 쉬운 구조**(MD·JSON)가 되도록 엄격히 정의한다. 자유 형식 출력은 오케스트레이션을 어렵게 만든다.

### 7-2. 완료 및 상태 보고 (Completion Signals)

스킬 수행 결과를 오케스트레이터에게 보고하는 방식이다.

1.  **원자적 상태 보고 (Thread-safe):** 병렬 실행 중인 에이전트는 `tasks.md`를 직접 수정하지 않고, `_workspace/tasks/task_{agent}_{id}.json` 파일을 생성하여 보고한다.
2.  **동적 핸드오프 (Handoff):** 자신의 전문 범위를 벗어나거나 특정 분야의 전문가가 추가로 필요한 경우 사용한다.
    - **형식:** `[NEXT_AGENT: @expert-name] 사유: {구체적 이유}`
    - **예시:** `[NEXT_AGENT: @security-patcher] 사유: 로직 분석 중 인증 취약점이 발견되어 전문 패치가 필요함.`
3.  **가시성 확보:** 모든 중간 과정은 `findings.md`의 [핵심 통찰] 섹션에 실시간으로 업데이트한다.

### 7-3. 외부 입력은 사용자 확인 요청으로

모호한 지시·데이터 충돌 시 추측하지 않는다. 스킬 본문에 "X가 불확실하면 사용자 확인 요청으로 확인하라"를 명시해 사용자 개입 지점을 고정한다.

### 7-4. 절차형 스킬은 스킬 로드로 호출되는 것을 전제

모든 서브에이전트는 공통 도구로 스킬 로드를 갖는다. 스킬 작성 시 **다른 스킬을 참조·재사용**한다면 해당 스킬 이름과 호출 시점을 명시한다.

### 7-5. 오케스트레이터 스킬 작성 규칙 (필수, drift 차단)

오케스트레이터 스킬을 작성할 때 **평면 "Step 1~N" 나열로 도피하지 말 것**. 반드시 Stage(상위 이슈/Jira Issue) → Step(하위 이슈/Jira Sub-issue) 블록 형식 사용. 이 규칙은 `examples/sso-dev-flow` 같은 비표준 산출물 재발 방지를 위한 강제 사항이다.

| 금지 | 허용 |
|------|------|
| `### Step 0: ...` `### Step 1: ...` 평면 헤더 | `### Stage 1: {name}` 후 `#### Step 1: {name}` 중첩 |
| 종료 조건에 "QA 승인 시", "완료되면", "충분히" | "qa_verdict.json의 verdict=PASS", "task_*.json status=done" |
| 패턴 미명시 또는 자유 표기 ("순차적으로") | 7대 패턴 enum (`pipeline`·`fan_out_fan_in`·`expert_pool`·`producer_reviewer`·`supervisor`·`hierarchical`·`handoff`) |
| 활성 에이전트 본문에 산문 서술 | Step 블록 필드 `활성 에이전트: [@name1, @name2]` |
| 사용자 승인 게이트 누락 | Stage 블록 `사용자 승인 게이트: 필요 / 없음` 명시 |
| 최대 반복 횟수 누락 (특히 producer_reviewer) | Step 블록 `최대 반복 횟수: 3` |
| findings.md `[Review: 단계]` 같은 임의 섹션 | `[핵심 통찰]`·`[변경 요청]`·`[공유 변수/경로]` 등 표준 섹션 |
| tasks.md 항목 단순 체크 | `_workspace/tasks/task_{agent}_{id}.json` 영속 + tasks.md 표 갱신 |

**오케스트레이터 SKILL.md 본문 필수 섹션 (체크리스트):**

- [ ] 가상 팀 (agent · 타입 · 역할 · 출력 표)
- [ ] Step 0 (컨텍스트 확인 — checkpoint.json status별 분기)
- [ ] Step 1 (초기화 — workflow.md·findings.md·tasks.md·checkpoint.json 5종 동시 작성 + 스키마 검증 1단계)
- [ ] Step 2 (Step 실행 루프 — 패턴별 호출 + 종료 조건 검사 + 자동/승인 전환)
- [ ] Step 3+ (패턴별 특수 처리 — 예: producer_reviewer 루프, supervisor 동적 배치)
- [ ] 에러 핸들링 (Zero-Tolerance: 재시도 ≤2 → Blocked + ask_user)

**오케스트레이터 스킬 디렉터리 필수 번들 (작성 시점):**

신규 오케스트레이터 스킬은 런타임에 자기 `references/schemas/`를 읽으므로 (`codex-harness`는 메타 스킬·런타임 활성화 안 됨) 다음 **9종**을 반드시 번들링한다. SoT는 `codex-harness/references/schemas/` — 신규 스킬 생성 시 그대로 복사.

```
{프로젝트}/.codex/skills/{name}-orchestrator/
├── SKILL.md
└── references/
    └── schemas/
        ├── task.schema.json                    ← codex-harness/references/schemas/ 사본
        ├── checkpoint.schema.json              ← 동일
        ├── workflow.template.md                ← 동일
        ├── findings.template.md                ← 동일
        ├── tasks.template.md                   ← 동일
        ├── models.md                           ← 모델 ID SoT (에이전트 생성 시 참조 필수)
        ├── agent-worker.template.toml            ← 워커 에이전트 생성 기준 (TOML)
        ├── agent-orchestrator.template.md      ← 오케스트레이터 스킬 생성 기준
        └── agent-state-manager.template.toml   ← 상태관리 에이전트 생성 기준 (선택적)
```

> **번들 검증:** Step 1.3 가 `references/schemas/` 9종을 shell `cat`로 읽으므로 누락 시 즉시 런타임 실패. 스킬 생성 직후 `ls .codex/skills/{name}/references/schemas/`로 9개 파일 존재 확인.
> **갱신 정책:** codex-harness `references/schemas/` 변경 시 모든 파생 오케스트레이터 스킬에 동일 변경 전파(드리프트 방지). 진행 중인 워크스페이스의 `_workspace/_schemas/`는 스냅샷이므로 보존.

> **풀 번들 예시 (한 도메인의 모든 산출물 통합 케이스):** `references/examples/full-bundle/sso-style.md` 참조. 오케스트레이터 SKILL.md + workflow.md + findings.md + tasks.md + checkpoint.json 5종을 동시 작성한 정본 패키지.

### 7-6. 평면 Step → Stage-Step 마이그레이션 가이드

기존에 평면 `Step 0~N` 헤더만으로 작성된 비표준 오케스트레이터 스킬(예: `examples/sso-dev-flow` 류)을 현행 Stage-Step 모델로 전환할 때 따르는 절차. **`expansion-matrix.md` drift 항목 #1·#2와 직접 대응한다.**

**전환 대상 식별 (체크리스트):**

- [ ] SKILL.md 본문에 `### Stage` 헤더가 0개 — 평면 Step만 존재
- [ ] workflow.md 미사용 (또는 단순 체크리스트로 대체)
- [ ] 종료 조건이 자연어 ("QA 승인", "완료되면", "충분히")
- [ ] `_workspace/tasks/task_*.json` 영속 없음 (tasks.md 직접 수정)
- [ ] `references/schemas/` 디렉터리 부재

**마이그레이션 6단계:**

| 단계 | 작업 | 검증 | 산출물 |
|------|------|------|--------|
| **M1. 인벤토리** | 기존 SKILL.md의 평면 Step 0~N을 도메인 작업 단위(Work)로 그룹핑. 각 그룹 = 잠재 Stage 후보. | 그룹 수 = Stage 후보 수, 각 그룹 내 Step 수 ≥ 1 | `migration_plan.md` 초안 |
| **M2. Stage 매핑** | 각 그룹에 Stage 이름 부여(작업 의미 기반: `gather`·`design`·`validate`). 각 그룹 내 sub-step을 Step(≡Task)으로 분해. | Stage·Step 이름이 `[a-z][a-z0-9-]*` 패턴 | Stage-Step 매핑표 |
| **M3. 패턴 할당** | 각 Step에 7대 패턴 중 1개 부여(`pipeline`·`fan_out_fan_in`·`expert_pool`·`producer_reviewer`·`supervisor`·`hierarchical`·`handoff`). 자유 표기("순차적으로") 금지. | enum 검사 통과 | 패턴 컬럼 추가된 매핑표 |
| **M4. 종료 조건 변환** | 자연어 → 검증 가능 술어. `"QA 승인"` → `qa_verdict.json의 verdict=PASS`, `"완료되면"` → `task_*.json status=done`, `"충분히"` → `iterations ≥ N`. | `orchestrator-template.md` Step 1.8 화이트리스트 통과 | 검증 술어 컬럼 추가 |
| **M5. 산출물 5종 작성** | 매핑표 기반으로 `workflow.md` + `findings.md` + `tasks.md` + `checkpoint.json` 작성. 신규 SKILL.md 본문은 `references/orchestrator-template.md` 골격 채택. | `workflow.md` 6 필드 누락 0개, 사이클 검증 통과 | 신규 5종 파일 |
| **M6. schemas/ 번들** | `codex-harness/references/schemas/` 9종을 신규 스킬 `references/schemas/`로 복사 (task/checkpoint/workflow/findings/tasks 스키마 + models.md + agent-worker.template.toml + agent-orchestrator.template.md + agent-state-manager.template.toml). | `ls .codex/skills/{new}/references/schemas/` 9개 파일 존재 | 번들 완료 |

**예시 변환표 (sso-dev-flow → 5단계 Stage-Step):**

| 기존 (평면) | 신규 (Stage-Step + 패턴) | 종료 조건 변환 |
|------------|--------------------------|---------------|
| `Step 0: 요구사항 수집` | Stage `discover` / Step `gather` (`fan_out_fan_in`) | `task_*.json status=done` 4건 |
| `Step 1: 설계 검토` | Stage `discover` / Step `design-review` (`producer_reviewer`) | `review_verdict.json verdict=PASS` |
| `Step 2: 구현` | Stage `build` / Step `implement` (`pipeline`) | `_workspace/{plan}/code/*.go` 파일 존재 |
| `Step 3: QA 승인 시 통과` | Stage `validate` / Step `qa-loop` (`producer_reviewer`) | `qa_verdict.json verdict=PASS AND iterations ≤ 3` |
| `Step 4: 배포` | Stage `validate` / Step `deploy` (`pipeline`) | `deployment.log status=success` |

**역호환성 정책:**

- 기존 진행 중 `_workspace/`는 보존 — 마이그레이션 후 신규 실행부터 적용.
- 기존 `_workspace/`에 `_schemas/` 디렉터리가 없을 경우 자동 추가 금지 (스냅샷 무결성 보장). 신규 실행 전 사용자 승인.
- AGENTS.md 변경 이력에 마이그레이션 기록 필수: `[YYYY-MM-DD] {스킬명}: 평면 Step → Stage-Step 전환 (M1~M6)`.

**마이그레이션 후 검증:**

- [ ] `expansion-matrix.md` drift 항목 #1·#2·#3 (평면 Step·자연어 종료조건·필수 필드) 모두 통과
- [ ] `orchestrator-template.md` Step 1.8 (스키마 검증) + Step 1.9 (사이클 검증) 통과
- [ ] 테스트 시나리오 1개 실행 성공 (full-bundle/sso-style.md 패턴 참조)

---

## 8. 데이터 스키마 표준

스킬 간 데이터 교환과 평가의 일관성을 위해 아래 표준 스키마를 준수한다.

### 8-1. eval_metadata.json

각 테스트 케이스의 메타데이터:

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "사용자의 작업 프롬프트",
  "assertions": [
    "산출물에 X가 포함되어 있다",
    "Y 형식으로 파일이 생성되었다"
  ]
}
```

### 8-2. grading.json

Assertion 기반 채점 결과:

```json
{
  "expectations": [
    {
      "text": "산출물에 '서울'이 포함됨",
      "passed": true,
      "evidence": "3번째 단계에서 '서울 지역 데이터 추출' 확인"
    }
  ],
  "summary": {
    "passed": 2,
    "failed": 1,
    "total": 3,
    "pass_rate": 0.67
  }
}
```

**필드명 주의:** 최상위 배열은 `expectations`, 내부 필드는 `text`·`passed`·`evidence`를 정확히 사용한다(`items`·`name`·`met`·`details` 등 변형 금지). 하네스의 Phase 6 검증과 `skill-testing-guide.md` 4절이 이 스키마를 전제로 한다.

### 8-3. timing.json

실행 시간·토큰 측정:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

서브에이전트 완료 알림에서 `total_tokens`와 `duration_ms`를 **즉시 저장**한다. 이 데이터는 알림 시점에만 접근 가능하고 이후 복구 불가.

### 8-4. findings.md / tasks.md

Codex CLI 하네스의 공용 상태 파일. 스킬이 이 두 파일을 업데이트할 때는 `orchestrator-template.md`의 섹션 규격을 준수한다.

- `findings.md`: `[핵심 통찰]`, `[핵심 키워드]`, `[공유 변수/경로]`, `[데이터 충돌]`, `[변경 요청]`, `[다음 단계 지침]` (패턴별 필요 섹션만 사용)
- `tasks.md`: `[ID]`, `[에이전트]`, `[작업 내용]`, `[상태]`, `[Evidence (증거)]`, `[연결 산출물]`

---

## 9. 스킬에 포함하지 않을 것

- `README.md`, `CHANGELOG.md`, `INSTALLATION_GUIDE.md` 등 부가 문서
- 스킬 생성 과정의 메타 정보(테스트 결과, 반복 이력, 커밋 메시지 등)
- 사용자 대상 설명서 — 스킬은 **AI 에이전트를 위한 지시서**다.
- 이미 에이전트가 알고 있는 일반적 지식(언어 문법, 일반 CS 개념 등)
- 특정 테스트 케이스에만 맞는 하드코딩된 값(일반화 원칙 위반)
