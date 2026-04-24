# Subagent Orchestration 실전 사례 (Gemini CLI)

6대 아키텍처 패턴의 실제 구현 예시. **Gemini CLI 환경에서는 서브에이전트 간 직접 통신이 불가능**하므로, 모든 팀 통신은 메인 에이전트가 `_workspace/findings.md`·`_workspace/tasks.md`를 통해 중개한다.

> **주의:** Claude Code의 `TeamCreate`·`SendMessage`·`TaskCreate` 같은 팀 API는 Gemini CLI에 존재하지 않는다. 서브에이전트 호출은 **`invoke_agent` 도구**를 사용하며, 병렬 실행이 필요한 경우 **`wait_for_previous: false`** 파라미터를 지정하여 구현한다. 본 사례들은 Claude Code의 팀 기능을 Gemini CLI의 **파일 기반 브로커링** 프로토콜로 치환해 재구성한 것이다.

---

## 예시 1: 리서치 팀 (Fan-out/Fan-in 패턴)

### 팀 아키텍처
주제 하나를 4개 전문 영역으로 팬아웃해 병렬 조사한 뒤, 메인 에이전트가 팬인 통합한다.

### 에이전트 구성

| 에이전트 | 유형 | 핵심 도구 | 산출물 |
|---|---|---|---|
| @official-researcher | Analyst | `ask_user`, `activate_skill`, `read_file`, `google_web_search`, `web_fetch` | `_workspace/01_official.md` |
| @media-researcher | Analyst | `ask_user`, `activate_skill`, `read_file`, `google_web_search`, `web_fetch` | `_workspace/01_media.md` |
| @community-researcher | Analyst | `ask_user`, `activate_skill`, `read_file`, `google_web_search`, `web_fetch` | `_workspace/01_community.md` |
| @background-researcher | Analyst | `ask_user`, `activate_skill`, `read_file`, `google_web_search`, `web_fetch` | `_workspace/01_background.md` |

### 오케스트레이터 워크플로우

```
Phase 0: _workspace/ 존재 여부 확인 → 신규/재실행 모드 결정
Phase 1: 사용자 입력 분석 → tasks.md에 4개 조사 작업 등록, findings.md [핵심 통찰] 초기화
Phase 2: 단일 응답 턴에서 @official/@media/@community/@background를
         invoke_agent(wait_for_previous: false)로 배치 호출
         - 각 에이전트 프롬프트에 findings.md의 [핵심 키워드]·[공유 변수/경로] 주입
Phase 3: 각 산출물을 read_file로 수집 → findings.md [데이터 충돌]에 상충 기록
         - 상충 정보는 교차 영역(예: media 발견 투자 뉴스 ↔ background 경쟁사)을
           메인 에이전트가 findings.md에 병기하고, 필요 시 해당 에이전트를 재호출
Phase 4: 통합 보고서 _workspace/final/research_report.md 생성 (상충 정보는 출처 병기)
Phase 5: 사용자 보고, _workspace/ 보존
```

### 브로커 중개 패턴 (SendMessage 대체)

Claude Code에서 `official → media → background`로 SendMessage가 오갔던 부분은 Gemini CLI에서 다음처럼 변환된다:

```
@official 산출물(_workspace/01_official.md) 완료
  → 메인 에이전트가 read_file로 확인
  → findings.md [공유 변수/경로]에 "official의 공식 발표 X는 media 맥락에서 재검증 필요" 추가
  → @media 호출 시 프롬프트에 findings.md의 해당 섹션을 요약 주입
```

---

## 예시 2: SF 소설 집필 팀 (Pipeline + Fan-out 패턴)

### 팀 아키텍처
세계관·캐릭터·플롯을 병렬 설계(Phase 1) → 본문 집필(Phase 2) → 과학·연속성 병렬 리뷰(Phase 3) → 수정(Phase 4).

### 에이전트 구성

| 에이전트 | 유형 | 역할 | 스킬 |
|---|---|---|---|
| @worldbuilder | Architect | 세계관 구축 | `world-setting` |
| @character-designer | Architect | 캐릭터 설계 | `character-profile` |
| @plot-architect | Architect | 플롯 구조 | `outline` |
| @prose-stylist | Coder | 집필 + 수정 | `write-scene`, `review-chapter` |
| @science-consultant | Reviewer | 과학 검증 | `science-check` |
| @continuity-manager | Reviewer | 일관성 검증 | `consistency-check` |

### 에이전트 파일 전문 예시: `.gemini/agents/worldbuilder.md`

```markdown
---
name: worldbuilder
description: "SF 소설의 세계관을 구축하는 전문가. 물리 법칙·사회 구조·기술 수준·역사를 설계. 세계관 신규 설계·확장·수정 요청 시 반드시 이 에이전트를 선택하라."
kind: local
model: "gemini-3.1-pro-preview"
temperature: 0.7
max_turns: 15
tools:
  - ask_user
  - activate_skill
  - read_file
  - write_file
  - grep_search
  - google_web_search
---

# Worldbuilder — SF 세계관 설계 전문가

SF 소설의 세계관 설계 전문가. 과학적 사실에 기반하되 상상력을 확장하여, 이야기가 펼쳐질 세계의 물리적·사회적·기술적 토대를 구축한다.

## 핵심 역할
1. 세계의 물리 법칙과 기술 수준 정의
2. 사회 구조·정치 체계·경제 시스템 설계
3. 역사적 맥락과 현재 갈등 구조 수립
4. 장소별 환경과 분위기 묘사

## 작업 원칙
- 내적 일관성 최우선 — 설정 간 모순이 없어야 한다
- "만약 이 기술이 있다면?" 연쇄 질문으로 세계의 파급 효과를 추론
- 이야기에 봉사하는 세계관 — 플롯을 방해하는 과도한 설정은 지양

## 입력/출력 프로토콜
- 입력: 사용자의 세계관 컨셉, `_workspace/00_input/brief.md`의 장르 요구사항
- 출력: `_workspace/01_worldbuilder_setting.md`
- 형식: 마크다운. 섹션별 (물리 / 사회 / 기술 / 역사 / 장소)

## 협업 프로토콜 (Gemini CLI)
- 타 에이전트와 직접 통신하지 않는다. 공유가 필요한 정보는
  `_workspace/findings.md`의 [공유 변수/경로] 섹션에 기록하고,
  메인 에이전트가 character-designer·plot-architect 프롬프트에 주입한다.
- science-consultant의 피드백은 `_workspace/03_science_review.md`에 기록되며,
  메인 에이전트가 재호출할 때 해당 경로를 프롬프트에 포함한다.
- 컨셉이 모호하면 `ask_user`로 3가지 방향을 제시하고 선택을 요청.

## 에러 핸들링
- 과학적 오류 발견 시 대안을 함께 제시
- 설정 간 모순 발견 시 findings.md [데이터 충돌]에 기록 후 결정을 요청
```

### 팀 워크플로우 상세

```
Phase 1: 메인 에이전트가 @worldbuilder / @character-designer / @plot-architect를
         invoke_agent(wait_for_previous: false)를 통해 배치 호출
         → 완료 산출물(_workspace/01_*)을 read_file로 수집
         → findings.md [공유 변수/경로]에 "주인공 계급은 X, 주요 갈등은 Y" 요약 주입

Phase 2: @prose-stylist 단독 호출. 프롬프트에 Phase 1의 3개 산출물 경로와
         findings.md 요약 제공 → _workspace/02_prose_draft.md 생성

Phase 3: @science-consultant와 @continuity-manager를 invoke_agent(wait_for_previous: false)로 배치 호출
         → 각 리뷰는 _workspace/03_science_review.md / 03_continuity_review.md
         → 메인 에이전트가 두 리뷰를 findings.md [데이터 충돌]에 교차 정리

Phase 4: @prose-stylist 재호출. 프롬프트에 리뷰 리포트 경로 포함
         → _workspace/04_prose_final.md
```

---

## 예시 3: 웹툰 제작 팀 (Producer-Reviewer 패턴)

### 팀 아키텍처
생성자(artist)와 검증자(reviewer)가 짧은 루프로 산출물을 정제한다. 메인 에이전트가 리뷰 리포트를 해석해 재생성 루프를 제어한다.

### 에이전트 구성

| 에이전트 | 유형 | 역할 | 스킬 |
|---|---|---|---|
| @webtoon-artist | Coder | 패널 이미지 생성 | `generate-webtoon` |
| @webtoon-reviewer | Reviewer | 품질 검수 | `review-webtoon`, `fix-webtoon-panel` |

### 에이전트 파일 전문 예시: `.gemini/agents/webtoon-reviewer.md`

```markdown
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
- 입력: `_workspace/panels/` 디렉토리의 패널 이미지들
- 출력: `_workspace/review_report.md`
- 형식:
  ```
  ## Panel {N}
  - 판정: PASS | FIX | REDO
  - 사유: [구체적 이유]
  - 수정 지시: [FIX/REDO인 경우 구체적 수정 방향]
  ```

## 협업 프로토콜 (Gemini CLI)
- @webtoon-artist에게 직접 지시할 수 없다. 모든 수정 요청은
  `_workspace/review_report.md`에 기록하며, 메인 에이전트가
  해당 리포트를 findings.md [변경 요청]으로 요약한 뒤 artist를 재호출한다.

## 에러 핸들링
- 이미지 로드 실패 시 해당 패널을 REDO로 판정
- 2회 재생성 후에도 REDO인 패널은 경고와 함께 PASS 처리
- 판정 기준이 모호하면 `ask_user`로 레퍼런스 이미지를 요청
```

### 루프 제어 로직

```
Phase 1: @webtoon-artist 호출 → _workspace/panels/*.png 생성
Phase 2: @webtoon-reviewer 호출 → _workspace/review_report.md 생성
Phase 3: 메인 에이전트가 review_report.md 파싱
         - REDO 패널 목록을 findings.md [변경 요청]에 기록
         - REDO 패널 전체의 50% 이상이면 ask_user로 프롬프트 재조정 제안
         - 그렇지 않으면 @webtoon-artist 재호출 (최대 2회 루프)
Phase 4: 최종 PASS/강제 PASS 집계 → _workspace/final/episode.md 생성
```

---

## 예시 4: 코드 리뷰 팀 (Fan-out + 브로커 중개 토론)

### 팀 아키텍처
서로 다른 관점(보안·성능·테스트)을 가진 리뷰어들이 병렬로 코드를 검토한다. 리뷰어 간 직접 토론은 불가능하므로, 메인 에이전트가 각자의 발견을 다른 리뷰어에게 전달해 교차 검증을 유도한다.

### 에이전트 구성

| 에이전트 | 유형 | 핵심 도구 | 산출물 |
|---|---|---|---|
| @security-reviewer | Reviewer | `ask_user`, `activate_skill`, `read_file`, `grep_search`, `run_shell_command` | `_workspace/review_security.md` |
| @performance-reviewer | Reviewer | `ask_user`, `activate_skill`, `read_file`, `grep_search`, `run_shell_command` | `_workspace/review_performance.md` |
| @test-reviewer | Reviewer | `ask_user`, `activate_skill`, `read_file`, `grep_search`, `run_shell_command` | `_workspace/review_tests.md` |

### 브로커 중개 토론 흐름

Claude Code 원본에서는 리뷰어들이 `SendMessage`로 직접 의견을 교환했다. Gemini CLI에서는 다음과 같이 변환한다:

```
1차 라운드 (병렬):
  @security-reviewer / @performance-reviewer / @test-reviewer를
  invoke_agent(wait_for_previous: false)로 배치 호출
  → 각자 review_*.md 생성

중개 라운드:
  메인 에이전트가 3개 리뷰를 read_file로 수집
  → findings.md [데이터 충돌]에 교차 영역 이슈 기록. 예:
    - security가 SQL 주입 지적 → performance·test에게 "이 SQL이 성능/테스트 대상인지 재검토" 요청
    - performance가 N+1 지적 → test에게 "관련 테스트 유무 확인" 요청
    - test가 인증 모듈 테스트 누락 지적 → security에게 "보안 관점 우선순위 의견" 요청

2차 라운드 (병렬):
  3명의 리뷰어를 invoke_agent(wait_for_previous: false)로 재호출하면서
  findings.md [데이터 충돌]의 해당 항목을 프롬프트에 주입
  → 각자 review_*_v2.md 생성

통합:
  메인 에이전트가 최종 리포트 _workspace/final/code_review.md 생성
```

핵심: Gemini CLI에서는 리뷰어들이 **리더를 반드시 거쳐** 정보를 교환한다. 교차 영역 이슈는 메인 에이전트의 `findings.md` 해석 품질에 의해 발견된다.

---

## 예시 5: 코드 마이그레이션 팀 (Supervisor 패턴)

### 팀 아키텍처
감독자가 대상 파일 목록을 배치로 나누어 워커들에게 동적으로 할당한다. Gemini CLI에서는 `tasks.md`가 공유 작업 목록 역할을 하며, 메인 에이전트가 배치 할당·재할당을 담당한다.

### 에이전트 구성

| 에이전트 | 유형 | 핵심 도구 | 역할 |
|---|---|---|---|
| @migration-supervisor | Architect | `ask_user`, `activate_skill`, `list_directory`, `glob`, `read_file` | 파일 분석·배치 분해 |
| @migrator-1~N | Coder | `ask_user`, `activate_skill`, `read_file`, `write_file`, `replace`, `run_shell_command` | 할당된 배치 마이그레이션 |

### 동적 분배 로직

```
Phase 1: @migration-supervisor 호출
         → 대상 파일 목록 수집 + 복잡도 추정 (파일 크기·import 수·의존성)
         → tasks.md에 N개 배치로 등록 (각 배치에 depends_on·우선순위·복잡도 필드)

Phase 2: 메인 에이전트가 tasks.md를 읽어 가용 워커 수만큼 배치 할당
         - 단일 응답 턴에서 @migrator-1 / @migrator-2 / @migrator-3를
           invoke_agent(wait_for_previous: false)로 배치 호출
         - 각 프롬프트에 할당 배치의 파일 목록·성공 기준 명시

Phase 3: 각 워커 완료 → 산출물 read_file로 확인
         - 성공 → tasks.md 상태 Todo→Done, 남은 배치 중 우선순위 최상을 즉시 재할당
         - 실패 → findings.md [데이터 충돌]에 원인 기록, 1회 재시도
         - 재시도 실패 → ask_user로 대체 경로 질의 또는 다른 워커에게 재할당

Phase 4: 모든 배치 Done → 통합 테스트 실행 (run_shell_command)
         → 실패 시 영향 범위 분석 후 해당 배치만 재실행
```

**팬아웃과의 차이:** 작업이 사전 고정이 아니라 **런타임에 동적 할당**된다. `tasks.md`의 `[상태]` 필드가 claim 매커니즘을 대신한다.

---

## 예시 6: 다국어 서비스 리서치 (Expert Pool 패턴)

### 팀 아키텍처
사용자 요청 언어·시장에 따라 동적으로 전문가를 선택 호출한다.

### 에이전트 구성

```yaml
@market-analyst-us:
  kind: local
  model: "gemini-3.1-pro-preview"
  tools: [ask_user, activate_skill, google_web_search, web_fetch, read_file]
  전문: 북미 시장

@market-analyst-kr:
  kind: local
  model: "gemini-3.1-pro-preview"
  tools: [ask_user, activate_skill, google_web_search, web_fetch, read_file]
  전문: 국내 시장

@market-analyst-jp:
  kind: local
  model: "gemini-3.1-pro-preview"
  tools: [ask_user, activate_skill, google_web_search, web_fetch, read_file]
  전문: 일본 시장
```

### 라우팅 로직

```
Phase 1: 메인 에이전트가 사용자 입력을 분석
         → findings.md [핵심 통찰]에 타겟 국가(들)를 식별 기록
Phase 2: 식별된 국가에 해당하는 @market-analyst-* 만 invoke_agent로 선택 호출
         (미식별 시 ask_user로 대상 국가 확정)
Phase 3: 각 산출물을 _workspace/market_{country}.md에 저장
Phase 4: 메인 에이전트가 통합 보고서 _workspace/final/market_report.md 생성
```

전문가 풀에서는 **모든 전문가를 호출하지 않는다**. 필요한 전문가만 선택하는 라우팅 판단 자체가 오케스트레이터의 핵심 로직이다.

---

## 예시 7: 풀스택 앱 개발 (Hierarchical Delegation 패턴)

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
  필요한 작업은 tasks.md에 추가하고, 메인 에이전트가 해당 에이전트들을 호출하도록 한다.
- 산출물은 `_workspace/frontend/` 하위에 정리하며,
  @backend-team-lead와의 API 계약은 findings.md [공유 변수/경로]에 기록한다.
```

### 계층 실행 흐름

```
Phase 1: @project-architect 호출 → 전체 설계 _workspace/00_architecture.md
         → findings.md [공유 변수/경로]에 프론트/백엔드 계약 요약

Phase 2: @frontend-team-lead / @backend-team-lead를
         invoke_agent(wait_for_previous: false)로 배치 호출
         → 각자 자기 영역 설계 + 필요한 하위 작업을 tasks.md에 추가

Phase 3: 메인 에이전트가 tasks.md를 읽어 @ui-designer·@state-engineer·
         @api-designer·@db-engineer를 invoke_agent로 순차/병렬 호출
         → 산출물은 각 팀 리드가 통합 검수

Phase 4: @project-architect가 최종 산출물을 교차 검증
```

계층적 위임에서는 **중간 리드가 직접 하위 호출을 하지 않는다**. 모든 호출은 메인 에이전트가 tasks.md를 통해 트리거한다.

---

## 산출물 패턴 요약

### 에이전트 정의 파일
- 경로: `.gemini/agents/{agent-name}.md` (프로젝트) 또는 `~/.gemini/agents/{agent-name}.md` (사용자).
- 필수 YAML: `name`, `description`(pushy·후속 키워드 포함), `kind: local`, `model: "gemini-3.1-pro-preview"`, `tools` (반드시 `ask_user`·`activate_skill` 포함).
- 권장 YAML: `temperature`(역할별 0.2~0.7), `max_turns`(5~20).
- 필수 섹션: 핵심 역할, 작업 원칙, 입출력 프로토콜, 협업 프로토콜(Gemini CLI), 에러 핸들링.

### 스킬 파일 구조
- 경로: `.gemini/skills/{skill-name}/SKILL.md`.
- 대형 지식은 `references/`로 분리 (Progressive Disclosure).

### 오케스트레이터 스킬
- 팀 전체를 조율하는 상위 스킬. Phase 0(재실행 감지)부터 Phase 5(보존·보고)까지 포함.
- 템플릿: `references/orchestrator-template.md` 참조.
- **서브에이전트 간 직접 통신이 불가능함**을 전제로 모든 협업을 `findings.md`·`tasks.md`로 중개.
