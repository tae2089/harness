# Subagent Orchestration 실전 사례 (Gemini CLI)

5개 아키텍처 패턴 실전 사례. **Gemini CLI 환경에서는 서브에이전트 간 직접 통신이 불가능**하므로, 모든 팀 통신은 메인 에이전트가 `_workspace/findings.md`·`_workspace/tasks.md`를 통해 중개한다.

## 목차

1. [예시 1: 리서치 팀 (Fan-out/Fan-in)](#예시-1-리서치-팀-fan-outfan-in-패턴)
2. [예시 2: 웹툰 제작 팀 (Producer-Reviewer)](#예시-2-웹툰-제작-팀-producer-reviewer-패턴)
3. [예시 3: 코드 마이그레이션 팀 (Supervisor)](#예시-3-코드-마이그레이션-팀-supervisor-패턴)
4. [예시 4: 풀스택 앱 개발 (Hierarchical Delegation)](#예시-4-풀스택-앱-개발-hierarchical-delegation-패턴)
5. [예시 5: 시스템 디버깅 및 장애 대응 팀 (Handoff + Persistence)](#예시-5-시스템-디버깅-및-장애-대응-팀-handoff--persistence-패턴)
6. [산출물 패턴 요약](#산출물-패턴-요약)

---

> **주의:** Claude Code의 `TeamCreate`·`SendMessage`·`TaskCreate` 같은 팀 API는 Gemini CLI에 존재하지 않는다. 서브에이전트 호출은 **`invoke_agent` 도구**를 사용하며, 병렬 실행이 필요한 경우 **`wait_for_previous: false`** 파라미터를 지정하여 구현한다. 본 사례들은 Claude Code의 팀 기능을 Gemini CLI의 **파일 기반 브로커링** 프로토콜로 치환해 재구성한 것이다.

> **Stage-Phase 구조 필수:** 모든 예시의 오케스트레이터는 Phase 0에서 `checkpoint.json`(`status`, `current_stage`, `current_phase`)을 읽어 실행 모드를 결정하고, Phase 1에서 `workflow.md`를 생성(Resume 모드는 기존 파일 읽기)한다. 단, 예시 3·4처럼 Phase 1에서 설계 에이전트를 먼저 호출해 결과를 확정한 뒤 workflow.md를 작성하는 것이 올바른 순서다. 예시 1의 오케스트레이터 워크플로우가 기준 구현이며, 나머지 예시도 동일 패턴을 적용한다.

---

## 예시 1: 리서치 팀 (Fan-out/Fan-in 패턴)

### 팀 아키텍처

주제 하나를 4개 전문 영역으로 팬아웃해 병렬 조사한 뒤, 메인 에이전트가 팬인 통합한다.

### 에이전트 구성

| 에이전트               | 유형    | 핵심 도구                                                                   | 산출물                                    |
| ---------------------- | ------- | --------------------------------------------------------------------------- | ----------------------------------------- |
| @official-researcher   | Analyst | `ask_user`, `activate_skill`, `read_file`, `google_web_search`, `web_fetch` | `_workspace/{plan_name}/01_official.md`   |
| @media-researcher      | Analyst | `ask_user`, `activate_skill`, `read_file`, `google_web_search`, `web_fetch` | `_workspace/{plan_name}/01_media.md`      |
| @community-researcher  | Analyst | `ask_user`, `activate_skill`, `read_file`, `google_web_search`, `web_fetch` | `_workspace/{plan_name}/01_community.md`  |
| @background-researcher | Analyst | `ask_user`, `activate_skill`, `read_file`, `google_web_search`, `web_fetch` | `_workspace/{plan_name}/01_background.md` |

### 오케스트레이터 워크플로우

```
Phase 0: _workspace/ + checkpoint.json 존재 여부 확인 → 실행 모드 결정:
         - checkpoint.json 존재 + status: "in_progress" → 중단 지점 재개(Resume)
           workflow.md 읽기 → current_stage, current_phase 복원
         - checkpoint.json 존재 + status: "completed" → 완료 상태.
           사용자 요청이 부분 수정이면 부분재실행, 새 입력이면 새 실행으로 분기. Resume 금지.
         - _workspace/ 미존재 또는 checkpoint.json 미존재 → 신규 실행 (Phase 1로 진행)
Phase 1: 사용자 입력 분석
         workflow.md 생성:
           Stage 1: main / 사용자 승인 게이트: 없음
           Phase 1: research / 패턴: fan_out_fan_in / 활성 에이전트: [4명] / 다음 phase: done
         checkpoint.json 생성 (current_stage: "main", current_phase: "research",
                            active_pattern: "fan_out_fan_in", status: "in_progress")
         tasks.md 4개 조사 작업 등록
         findings.md 초기화: [핵심 통찰], [핵심 키워드], [공유 변수/경로], [데이터 충돌] 섹션 생성
Phase 2: [Phase 실행 루프 — Stage main / Phase research]
         단일 응답 턴에서 @official/@media/@community/@background를
         invoke_agent(wait_for_previous: false)로 배치 호출
         - 각 에이전트 프롬프트에 findings.md의 [핵심 키워드]·[공유 변수/경로] 주입
Phase 3: 각 산출물을 read_file로 수집
         - 산출물 파일 미존재(에이전트 실패) → 최대 2회 재시도(총 3회).
           3회 후에도 미생성 → Blocked, ask_user로 수동 개입 요청. 임의 Skip 금지.
         - 수집 성공 → findings.md [데이터 충돌]에 상충 기록
         - 상충 정보는 교차 영역(예: media 발견 투자 뉴스 ↔ background 경쟁사)을
           메인 에이전트가 findings.md에 병기하고, 필요 시 해당 에이전트를 재호출
           (재호출 최대 2회·총 3회. 그래도 상충 미해결 → 출처 병기 후 진행, findings.md [데이터 충돌]에 미해결 표시)
         Phase research 종료 조건 충족 → checkpoint.json 갱신:
           - phase_history에 "research" completed_at 기록
           - stage_history에 "main" completed_at 기록
           - current_stage·current_phase: "done", status: "completed", last_updated: 현재 타임스탬프
         사용자 승인 게이트: 없음 → 워크플로우 자동 완료
Phase 4: 통합 보고서 _workspace/{plan_name}/final/research_report.md 생성 (상충 정보는 출처 병기)
Phase 5: 사용자 보고, _workspace/ 보존
```

### 브로커 중개 패턴 (SendMessage 대체)

Claude Code에서 `official → media → background`로 SendMessage가 오갔던 부분은 Gemini CLI에서 다음처럼 변환된다:

```
@official 산출물(_workspace/{plan_name}/01_official.md) 완료
  → 메인 에이전트가 read_file로 확인
  → findings.md [공유 변수/경로]에 "official의 공식 발표 X는 media 맥락에서 재검증 필요" 추가
  → @media 호출 시 프롬프트에 findings.md의 해당 섹션을 요약 주입
```

---

## 예시 2: 웹툰 제작 팀 (Producer-Reviewer 패턴)

### 팀 아키텍처

생성자(artist)와 검증자(reviewer)가 짧은 루프로 산출물을 정제한다. 메인 에이전트가 리뷰 리포트를 해석해 재생성 루프를 제어한다.

### 에이전트 구성

| 에이전트          | 유형     | 역할             | 핵심 도구                                                                      | 스킬                                  |
| ----------------- | -------- | ---------------- | ------------------------------------------------------------------------------ | ------------------------------------- |
| @webtoon-artist   | Coder    | 패널 이미지 생성 | `ask_user`, `activate_skill`, `read_file`, `write_file`                        | `generate-webtoon`                    |
| @webtoon-reviewer | Reviewer | 품질 검수        | `ask_user`, `activate_skill`, `read_file`, `write_file`, `glob`, `grep_search` | `review-webtoon`, `fix-webtoon-panel` |

### 에이전트 파일 전문 예시: `.gemini/agents/webtoon-reviewer.md`

````markdown
---
name: webtoon-reviewer
description: "웹툰 패널의 품질을 검수하는 전문가. 구도·캐릭터 일관성·텍스트 가독성·연출을 평가. 웹툰 QA·검수·재작업 요청 시 반드시 이 에이전트를 선택."
kind: local
model: "gemini-3.1-pro-preview"
temperature: 0.2
max_turns: 10
tools:
  - ask_user
  - activate_skill
  - read_file
  - write_file
  - glob
  - grep_search
---

# Webtoon Reviewer — 웹툰 품질 검수 전문가

웹툰 패널의 품질을 검수하는 전문가. 시각적 완성도·스토리 전달력·캐릭터 일관성을 기준으로 평가한다.

## 핵심 역할

1. 각 패널의 구도와 시각적 완성도 평가
2. 캐릭터 외형의 패널 간 일관성 검증
3. 말풍선 텍스트의 가독성과 배치 평가
4. 전체 에피소드의 연출 흐름과 페이싱 검토

## 작업 원칙

- PASS / FIX / REDO 3단계로 명확히 판정
- FIX는 부분 수정 가능, REDO는 전면 재생성 필요
- 주관적 취향이 아닌 객관적 기준(일관성·가독성·구도)으로 판단

## 입력/출력 프로토콜

- 입력: `_workspace/{plan_name}/panels/` 디렉토리의 패널 이미지들
- 출력: `_workspace/{plan_name}/review_report.md`
- 형식:

```

## Panel {N}

- 판정: PASS | FIX | REDO
- 사유: [구체적 이유]
- 수정 지시: [FIX/REDO인 경우 구체적 수정 방향]

```

## 협업 프로토콜 (Gemini CLI)

- @webtoon-artist에게 직접 지시할 수 없다. 모든 수정 요청은
  `_workspace/{plan_name}/review_report.md`에 기록하며, 메인 에이전트가
  해당 리포트를 findings.md [변경 요청]으로 요약한 뒤 artist를 재호출한다.

## 에러 핸들링

- 이미지 로드 실패 시 해당 패널을 REDO로 판정
- 3회 재생성 후에도 REDO인 패널은 **Blocked 처리 후 ask_user로 사용자 개입 요청. 임의 PASS 처리 절대 금지.**
- 판정 기준이 모호하면 `ask_user`로 레퍼런스 이미지를 요청
````

### 오케스트레이터 워크플로우

```
Phase 0: (예시 1과 동일 — 상태 확인·Resume·신규 실행 분기)
Phase 1: 사용자 입력(에피소드 명세) 분석
         workflow.md 생성:
           Stage 1: main / 사용자 승인 게이트: 없음
           Phase 1: produce / 패턴: producer_reviewer / 활성 에이전트: [@webtoon-artist, @webtoon-reviewer] / 다음 phase: done
         checkpoint.json 생성 (current_stage: "main", current_phase: "produce",
                            active_pattern: "producer_reviewer", status: "in_progress")
         tasks.md 패널 작업 등록, findings.md [공유 변수/경로]·[변경 요청] 초기화
Phase 2: [Phase 실행 루프 — Stage main / Phase produce]
         @webtoon-artist 호출 → _workspace/{plan_name}/panels/*.png 생성
         @webtoon-reviewer 호출 → _workspace/{plan_name}/review_report.md 생성
         메인 에이전트가 review_report.md 파싱:
         - FIX/REDO 패널 → 수정 지시를 findings.md [변경 요청]에 기록 → @webtoon-artist 재호출
           (FIX: 부분 수정, REDO: 전면 재생성)
         - 1회차 검수 후 REDO 패널이 전체의 50% 이상이면 재호출 전 ask_user로 프롬프트 재조정 제안
         - FIX+REDO 합산 재호출 최대 2회 재시도(총 3회). 초과 시 Blocked → ask_user
         루프 탈출 조건: 모든 패널 PASS → Phase 3으로 전환
Phase 3: 최종 PASS 집계 → phase "produce" 종료 조건 충족
         checkpoint.json 갱신:
           - phase_history에 "produce" completed_at 기록
           - stage_history에 "main" completed_at 기록
           - current_stage·current_phase: "done", status: "completed", last_updated: 현재 타임스탬프
         사용자 승인 게이트: 없음 → 워크플로우 자동 완료
Phase 4: 최종 에피소드 _workspace/{plan_name}/final/episode.md 생성
         (Blocked 패널은 ask_user 승인 후 사용자 결정에 따라 포함·제외 처리)
Phase 5: 사용자 보고, _workspace/ 보존
```

---

## 예시 3: 코드 마이그레이션 팀 (Supervisor 패턴)

### 팀 아키텍처

감독자가 대상 파일 목록을 배치로 나누어 워커들에게 동적으로 할당한다. Gemini CLI에서는 `tasks.md`가 공유 작업 목록 역할을 하며, 메인 에이전트가 배치 할당·재할당을 담당한다.

### 에이전트 구성

| 에이전트              | 유형      | 핵심 도구                                                                               | 역할                     |
| --------------------- | --------- | --------------------------------------------------------------------------------------- | ------------------------ |
| @migration-supervisor | Architect | `ask_user`, `activate_skill`, `list_directory`, `glob`, `read_file`                     | 파일 분석·배치 분해      |
| @migrator-1~N         | Coder     | `ask_user`, `activate_skill`, `read_file`, `write_file`, `replace`, `run_shell_command` | 할당된 배치 마이그레이션 |

### 오케스트레이터 워크플로우

```
Phase 0: (예시 1과 동일 — 상태 확인·Resume·신규 실행 분기)
Phase 1: ① @migration-supervisor 호출
           → 대상 파일 목록 수집 + 복잡도 추정 (파일 크기·import 수·의존성)
           → tasks.md에 N개 배치로 등록 (우선순위·복잡도 필드 포함; 순서는 오케스트레이터가 tasks.md 상태를 읽어 수동 제어)
         ② supervisor 완료 후 배치 수(N) 확정 → workflow.md 생성:
           Stage 1: main / 사용자 승인 게이트: 없음
           Phase 1: migrate / 패턴: supervisor / 활성 에이전트: [@migrator-1~N] / 다음 phase: test
           Phase 2: test / 패턴: pipeline / 활성 에이전트: [메인] / 다음 phase: done
         ③ checkpoint.json 생성 (current_stage: "main", current_phase: "migrate",
                            active_pattern: "supervisor", status: "in_progress")
         findings.md [공유 변수/경로]·[데이터 충돌] 초기화
Phase 2: [Phase 실행 루프 — Stage main / Phase migrate]
         메인 에이전트가 tasks.md를 읽어 가용 워커 수만큼 배치 할당
         - 단일 응답 턴에서 @migrator-1 / @migrator-2 / @migrator-3를
           invoke_agent(wait_for_previous: false)로 배치 호출
         - 각 프롬프트에 할당 배치의 파일 목록·성공 기준 명시
         - 워커 완료 → 산출물 read_file로 확인
           - 성공 → tasks.md 상태 Todo→Done, 남은 배치 중 우선순위 최상을 즉시 재할당
           - 실패 → findings.md [데이터 충돌]에 원인 기록, 최대 2회 재시도 (총 3회)
           - 3회 후에도 실패 → Blocked 처리, ask_user로 대체 경로 질의. 임의 Skip 절대 금지.
         모든 배치 Done → phase "migrate" 종료 조건 충족
         checkpoint.json 갱신: current_phase → "test", active_pattern → "pipeline"
                            phase_history에 "migrate" completed_at 기록, last_updated: 현재 타임스탬프
Phase 3: [Phase 실행 루프 — Stage main / Phase test]
         통합 테스트 실행 (run_shell_command)
         → 실패 시 영향 범위 분석 후 해당 배치만 재실행 (최대 2회 재시도, 총 3회)
         → 3회 후에도 실패 → Blocked 처리, ask_user로 수동 대응 요청. 임의 완료 처리 금지.
         phase "test" 종료 조건 충족 → stage "main" 완료
         checkpoint.json 갱신:
           - phase_history에 "test" completed_at 기록
           - stage_history에 "main" completed_at 기록
           - current_stage·current_phase: "done", status: "completed", last_updated: 현재 타임스탬프
Phase 4: 마이그레이션 완료 보고서 _workspace/{plan_name}/final/migration_report.md 생성
Phase 5: 사용자 보고, _workspace/ 보존
```

**팬아웃과의 차이:** 작업이 사전 고정이 아니라 **런타임에 동적 할당**된다. `tasks.md`의 `[상태]` 필드가 claim 메커니즘을 대신한다.

---

## 예시 4: 풀스택 앱 개발 (Hierarchical Delegation 패턴)

### 팀 아키텍처

최상위 아키텍트가 프로젝트를 프론트엔드·백엔드 서브 프로젝트로 분해하고, 각 팀 리드가 다시 자신의 서브에이전트를 조율한다.

### 계층 구조

```
@project-architect (Top)
  ├── @frontend-team-lead (Mid) — UI/UX, 컴포넌트, 상태 관리
  │     ├── @ui-designer
  │     └── @state-engineer
  └── @backend-team-lead (Mid) — API, DB, 인프라
        ├── @api-designer
        └── @db-engineer
```

### 에이전트 파일 전문 예시: `.gemini/agents/frontend-team-lead.md`

```markdown
---
name: frontend-team-lead
description: "프론트엔드 아키텍처 및 구현 전문가. UI 컴포넌트 설계와 상태 관리를 전담. 프론트엔드 구조 설계·구현·리팩토링 요청 시 반드시 이 에이전트를 선택."
kind: local
model: "gemini-3.1-pro-preview"
temperature: 0.3
max_turns: 15
tools:
  - ask_user
  - activate_skill
  - read_file
  - write_file
  - replace
  - glob
  - list_directory
  - grep_search
---

# Frontend Team Lead

## 핵심 역할

1. 아키텍트의 설계를 기반으로 UI 명세서 작성
2. React/Next.js 컴포넌트 구조 설계 및 구현
3. 프론트엔드 테스트 코드 작성
4. @ui-designer·@state-engineer의 산출물을 통합하는 중간 조율

## 협업 프로토콜 (Gemini CLI)

- 상위: @project-architect가 findings.md에 기록한 요구사항을 입력으로 받는다.
- 하위: @ui-designer·@state-engineer에게 **직접 지시할 수 없다**.
  필요한 하위 작업은 `task_frontend-team-lead_{id}.json`에 기록하고, 메인 에이전트가 수집·통합 후 해당 에이전트들을 호출하도록 한다.
- 산출물은 `_workspace/frontend/` 하위에 정리하며,
  @backend-team-lead와의 API 계약은 findings.md [공유 변수/경로]에 기록한다.

## 에러 핸들링

- 아키텍트 명세 불명확 시 `ask_user`로 요구사항 재확인. 임의 해석 금지.
- 하위 에이전트(@ui-designer·@state-engineer) 산출물 검수 실패 시 task*{agent}*{id}.json에 재작업 지시 기록 후 메인 에이전트에 위임.
- 3회 재작업 후에도 기준 미달 → findings.md [데이터 충돌]에 미달 내용 기록, Blocked 판정. 메인 에이전트가 ask_user 호출.
```

### 오케스트레이터 워크플로우

```
Phase 0: (예시 1과 동일 — 상태 확인·Resume·신규 실행 분기)
Phase 1: findings.md 초기화: [공유 변수/경로]·[변경 요청]·[데이터 충돌] 섹션 생성
         ① @project-architect 호출 → 전체 설계 _workspace/{plan_name}/00_architecture.md
           → findings.md [공유 변수/경로]에 프론트/백엔드 API 계약 요약
         ② architect 완료 후 설계 결과 기반으로 workflow.md 생성:
           Stage 1: main / 사용자 승인 게이트: 없음
           Phase 1: design / 패턴: hierarchical / 활성 에이전트: [@frontend-team-lead, @backend-team-lead] / 다음 phase: implement
           Phase 2: implement / 패턴: hierarchical / 활성 에이전트: [@ui-designer, @state-engineer, @api-designer, @db-engineer] / 다음 phase: done
         ③ checkpoint.json 생성 (current_stage: "main", current_phase: "design",
                            active_pattern: "hierarchical", status: "in_progress")
         tasks.md 초기화
Phase 2: [Phase 실행 루프 — Stage main / Phase design]
         @frontend-team-lead / @backend-team-lead를
         invoke_agent(wait_for_previous: false)로 배치 호출
         - 각 호출 프롬프트에 findings.md [공유 변수/경로]의 프론트/백엔드 API 계약 요약 주입
         → 각자 자기 영역 설계 완료 + 필요한 하위 작업을 task_{agent}_{id}.json에 기록
         → 메인 에이전트가 두 파일 수집 후 tasks.md에 원자적 통합 (동시 쓰기 충돌 방지)
         phase "design" 종료 조건 충족
         checkpoint.json 갱신: current_phase → "implement", active_pattern → "hierarchical" (유지)
                            phase_history에 "design" completed_at 기록, last_updated: 현재 타임스탬프
Phase 3: [Phase 실행 루프 — Stage main / Phase implement]
         메인 에이전트가 tasks.md를 읽어 @ui-designer·@state-engineer·
         @api-designer·@db-engineer를 invoke_agent로 순차/병렬 호출
         (의존관계 없는 작업은 wait_for_previous: false로 병렬, 의존관계 있으면 순차)
         → 산출물은 각 팀 리드가 통합 검수
         → 검수 실패 시 해당 에이전트 재호출 (최대 2회 재시도, 총 3회)
         → 3회 후에도 실패 → Blocked, ask_user로 수동 개입 요청
         종료 조건: tasks.md의 모든 항목 상태 = Done + 각 팀 리드 검수 통과 → phase "implement" 충족
         → stage "main" 완료 (Phase 4 교차 검증 후 최종 확정)
Phase 4: @project-architect가 최종 산출물을 교차 검증
         - 검증 통과 → checkpoint.json 갱신:
           phase_history에 "implement" completed_at, stage_history에 "main" completed_at
           current_stage·current_phase: "done", status: "completed", last_updated: 현재 타임스탬프
         - 검증 실패 → 실패 영역(프론트/백엔드)을 findings.md [변경 요청]에 기록 후 해당 팀 리드 재호출 (최대 1회)
         - 재검증 후에도 실패 → Blocked, ask_user로 수동 판단 요청
Phase 5: 사용자 보고, _workspace/ 보존
```

계층적 위임에서는 **중간 리드가 직접 하위 호출을 하지 않는다**. 모든 호출은 메인 에이전트가 tasks.md를 통해 트리거한다.

**Supervisor와의 차이:** 단일 계층(감독자→동종 워커)이 아닌 2단계 계층(아키텍트→팀 리드→전문 워커)으로, 도메인이 이질적인 팀에 적합.

---

## 예시 5: 시스템 디버깅 및 장애 대응 팀 (Handoff + Persistence 패턴)

### 팀 아키텍처

문제를 분류하는 트리아지 에이전트가 로그를 분석하고, 분석 결과에 따라 가장 적합한 수정 전문가에게 직접 제어권을 넘긴다(Handoff). 대규모 로그 분석 중 중단될 경우에 대비해 체크포인트를 관리한다(Persistence).

### 에이전트 구성

| 에이전트          | 유형    | 핵심 역할                       | 도구                                     |
| ----------------- | ------- | ------------------------------- | ---------------------------------------- |
| @incident-triage  | Analyst | 원인 분석 및 전문가 추천        | `grep_search`, `read_file`, `web_fetch`  |
| @db-fixer         | Coder   | DB 쿼리 및 스키마 수정          | `mcp_sql_*`, `read_file`, `write_file`   |
| @logic-fixer      | Coder   | 애플리케이션 비즈니스 로직 수정 | `read_file`, `write_file`, `replace`     |
| @security-patcher | Coder   | 취약점 패치 및 보안 설정        | `grep_search`, `read_file`, `write_file` |

### 오케스트레이터 워크플로우

```
Phase 0: _workspace/ + checkpoint.json 존재 여부 확인 → 실행 모드 결정:
         - checkpoint.json 존재 + status: "in_progress" → findings.md의 [공유 변수/경로]에서
           "마지막 분석 로그 라인" 확인 후 그 지점부터 재개 (Persistence)
           workflow.md 읽기 → current_stage, current_phase 복원
         - checkpoint.json 존재 + status: "completed" → 이전 분석 완료 상태.
           사용자 요청이 부분 수정이면 부분 재실행, 새 장애면 새 실행으로 분기. Resume 금지.
         - _workspace/ 미존재 또는 checkpoint.json 미존재 → 신규 분석 시작 (Phase 1로 진행)
Phase 1: workflow.md 생성:
           Stage 1: main / 사용자 승인 게이트: 없음
           Phase 1: triage / 패턴: handoff / 활성 에이전트: [@incident-triage] / 다음 phase: fix
           Phase 2: fix / 패턴: producer_reviewer / 활성 에이전트: [동적 결정] / 다음 phase: done
         checkpoint.json 생성 (current_stage: "main", current_phase: "triage",
                            active_pattern: "handoff", status: "in_progress")
         tasks.md 초기화 (fix 작업 등록용)
         findings.md [공유 변수/경로]·[데이터 충돌] 초기화
Phase 2: [Phase 실행 루프 — Stage main / Phase triage]
         @incident-triage 호출 → 수 기가바이트의 로그 및 스택 트레이스 스캔
         - 분석 결과: "DB 연결 타임아웃 발견"
         - 응답 끝에 핸드오프 신호 삽입:
           `[NEXT_AGENT: @db-fixer] 사유: Connection Pool 고갈 및 Slow Query 확인됨.`
         오케스트레이터가 [NEXT_AGENT] 파싱:
         - 파싱 성공 → checkpoint.json 갱신: current_phase → "fix", active_pattern → "producer_reviewer"
                      phase_history에 "triage" completed_at 기록, last_updated: 현재 타임스탬프. 지정 에이전트 즉시 호출.
                      호출 프롬프트에 트리아지의 분석 요약과 로그 위치 자동 주입
         - 파싱 실패 ([NEXT_AGENT] 미포함) → ask_user로 전문가 선택 요청
Phase 3: [Phase 실행 루프 — Stage main / Phase fix]
         지정 에이전트(@db-fixer 등)가 수정 수행 후 @incident-triage에게 재검증 요청 (Fix Loop, 최대 2회 재시도·총 3회)
         - 종료 조건(성공): @incident-triage 응답에 [NEXT_AGENT] 없음 + "이상 없음" 또는 "수정 확인" 명시
         - 종료 조건(실패): 3회 후에도 [NEXT_AGENT] 재반환 또는 에러 지속
           → Blocked, ask_user로 수동 개입 요청. 임의 PASS 절대 금지.
         phase "fix" 종료 조건 충족 → stage "main" 완료
         checkpoint.json 갱신:
           - phase_history에 "fix" completed_at 기록
           - stage_history에 "main" completed_at 기록
           - current_stage·current_phase: "done", status: "completed", last_updated: 현재 타임스탬프
Phase 4: 장애 대응 보고서 _workspace/{plan_name}/final/incident_report.md 생성
Phase 5: 사용자 보고, _workspace/ 보존
```

### 협업 프로토콜 예시: `@incident-triage.md`

```markdown
## 핸드오프 가이드 (Gemini CLI)

작업 완료 시 다음 규칙에 따라 전문가를 추천하라.

- SQL/DB 에러·커넥션 타임아웃·슬로우 쿼리 발견 시: `[NEXT_AGENT: @db-fixer]`
- 403/401/인증·권한 에러 발견 시: `[NEXT_AGENT: @security-patcher]`
- 성능 이슈(DB 외 애플리케이션 레벨 병목): `[NEXT_AGENT: @logic-fixer]`
- 그 외 비즈니스 로직 오류: `[NEXT_AGENT: @logic-fixer]`
- 복수 원인 동시 발견 시: 가장 심각한 원인 기준으로 1개 선택 후 사유에 나머지 원인 병기

## 영속성 가이드

로그 분석 중 `max_turns`에 도달할 경우, 현재까지 읽은 마지막 파일 경로와 라인 번호를
`_workspace/findings.md`의 [공유 변수/경로] 섹션에 기록하여 다음 턴에서 이어서 읽을 수 있게 하라.

## 에러 핸들링

- 로그 파일 접근 불가(권한·경로 오류) → `ask_user`로 올바른 경로 요청. 임의 경로 추측 금지.
- 원인 특정 불가(에러 패턴 없음) → 분석 불가 사유를 findings.md [데이터 충돌]에 기록 후 `ask_user`로 추가 컨텍스트 요청.
- 재검증 시 동일 에러 반복(Fix Loop 3회 초과) → 재반환 없이 Blocked 판정. 메인 에이전트가 ask_user 호출.
```

---

## 산출물 패턴 요약

### 에이전트 정의 파일

- 경로: `.gemini/agents/{agent-name}.md` (프로젝트) 또는 `~/.gemini/agents/{agent-name}.md` (사용자).
- 필수 YAML: `name`, `description`(pushy·후속 키워드 포함), `kind: local`, `model`(오케스트레이터·Architect → `"gemini-3.1-pro-preview"`, 워커 → `"gemini-3-flash-preview"` 또는 `"inherit"`), `tools` (반드시 `ask_user`·`activate_skill` 포함).
- 권장 YAML: `temperature`(역할별 0.2~0.7), `max_turns`(5~20).
- 필수 섹션: 핵심 역할, 작업 원칙, 입출력 프로토콜, 협업 프로토콜(Gemini CLI), 에러 핸들링.

### findings.md 표준 섹션 구조

오케스트레이터가 Phase 1에서 초기화하는 표준 섹션:

| 섹션명             | 용도                                                 | 주로 쓰는 패턴                      |
| ------------------ | ---------------------------------------------------- | ----------------------------------- |
| `[핵심 통찰]`      | 리서치·분석 결과 핵심 요약                           | Fan-out/Fan-in                      |
| `[핵심 키워드]`    | 에이전트 프롬프트 주입용 공통 키워드                 | Fan-out/Fan-in                      |
| `[공유 변수/경로]` | 에이전트 간 공유 경로·API 계약·Persistence 재개 지점 | 전 패턴                             |
| `[데이터 충돌]`    | 에이전트 산출물 간 상충 정보 기록                    | Fan-out/Fan-in, Supervisor, Handoff |
| `[변경 요청]`      | 재작업 지시 내용                                     | Producer-Reviewer                   |
| `[다음 단계 지침]` | 다음 에이전트가 중점적으로 봐야 할 가이드            | Pipeline, Hierarchical              |

패턴별로 필요한 섹션만 초기화한다. 사용하지 않는 섹션은 생략.

### tasks.md 기본 스키마

오케스트레이터가 Phase 1에서 등록하는 작업 목록 형식:

```
| ID | 작업명 | 담당 에이전트 | 우선순위 | 복잡도 | 상태 |
|----|--------|--------------|----------|--------|------|
| 1  | ...    | @migrator-1  | High     | Large  | Todo |
```

- **상태 값**: `Todo` → `In-Progress` → `Done` | `Blocked`
- **메인 에이전트 단독 갱신**: 워커는 task*{agent}*{id}.json에만 기록. tasks.md는 메인이 수집 후 원자적 갱신.
- **Blocked 항목**: ask_user 호출 시 해당 행 상태를 `Blocked`로 표시.

### 스킬 파일 구조

- 경로: `.gemini/skills/{skill-name}/SKILL.md`.
- 대형 지식은 `references/`로 분리 (Progressive Disclosure).

### 오케스트레이터 스킬

- 팀 전체를 조율하는 상위 스킬. Phase 0(재실행 감지)부터 Phase 5(보존·보고)까지 포함.
- 템플릿: `references/orchestrator-template.md` 참조.
- **서브에이전트 간 직접 통신이 불가능함**을 전제로 모든 협업을 `findings.md`·`tasks.md`·`checkpoint.json`으로 중개.
- **`_workspace/workflow.md` 필수 생성**: Phase 1에서 Stage-Phase 구조를 선언. 단순 작업은 Stage·Phase 각 1개(`main`), 다단계 작업은 2개 이상. 오케스트레이터는 매 사이클 이 파일을 읽어 현재 phase의 `활성 에이전트` 목록만 호출한다.
- **Zero-Tolerance 실패 프로토콜**: 에이전트 실패 시 최대 2회 재시도(총 3회). 3회 후에도 실패 시 `Blocked` 상태로 전환하고 `ask_user` 호출. 임의 Skip·PASS·완료 처리 절대 금지.
