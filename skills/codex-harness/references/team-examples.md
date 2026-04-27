# Subagent Orchestration 실전 사례 (Codex CLI)

5개 아키텍처 패턴 실전 사례. **Codex CLI 환경에서는 서브에이전트 간 직접 통신이 불가능**하므로, 모든 팀 통신은 메인 에이전트가 `_workspace/findings.md`·`_workspace/tasks.md`를 통해 중개한다.

> **주의:** Claude Code의 `TeamCreate`·`SendMessage`·`TaskCreate` 같은 팀 API는 Codex CLI에 존재하지 않는다. 서브에이전트 호출은 **`spawn_subagent` 도구**를 사용하며, 병렬 실행이 필요한 경우 **`wait_for_previous: false`** 파라미터를 지정하여 구현한다.
> **Stage-Step 구조 필수:** 모든 예시의 오케스트레이터는 Step 0에서 `checkpoint.json`(`status`, `current_stage`, `current_step`)을 읽어 실행 모드를 결정하고, Step 1에서 `workflow.md`를 생성(Resume 모드는 기존 파일 읽기)한다. 예시 1의 오케스트레이터 워크플로우가 기준 구현이며, 나머지 예시도 동일 패턴을 적용한다.

---

## 예시 인덱스

| #   | 패턴                  | 도메인 예시       | 에이전트 수 | 핵심 특징                                                   | 파일                                                                               |
| --- | --------------------- | ----------------- | ----------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 1   | Fan-out/Fan-in        | 리서치 팀         | 4           | 병렬 조사 후 통합, 데이터 충돌 중재                         | [examples/team/01-fan-out-fan-in.md](examples/team/01-fan-out-fan-in.md)           |
| 2   | Producer-Reviewer     | 웹툰 제작         | 2           | PASS/FIX/REDO 루프, 에이전트 파일 전문 예시 포함            | [examples/team/02-producer-reviewer.md](examples/team/02-producer-reviewer.md)     |
| 3   | Supervisor            | 코드 마이그레이션 | 1+N         | 런타임 동적 배치 할당, tasks.md claim 메커니즘              | [examples/team/03-supervisor.md](examples/team/03-supervisor.md)                   |
| 4   | Hierarchical          | 풀스택 앱 개발    | 5           | 2단계 위임, 팀 리드 중간 조율, 에이전트 파일 전문 예시 포함 | [examples/team/04-hierarchical.md](examples/team/04-hierarchical.md)               |
| 5   | Handoff + Persistence | 시스템 디버깅     | 4           | [NEXT_AGENT] 파싱, 대용량 로그 재개                         | [examples/team/05-handoff-persistence.md](examples/team/05-handoff-persistence.md) |

### 패턴 선택 가이드

| 상황                                                | 권장 패턴                      |
| --------------------------------------------------- | ------------------------------ |
| 독립 작업 병렬 수행 후 통합                         | Fan-out/Fan-in (예시 1)        |
| 생성 품질을 반복 검수로 높여야 할 때                | Producer-Reviewer (예시 2)     |
| 동종 작업 대량 처리, 진행 상황 실시간 추적          | Supervisor (예시 3)            |
| 도메인 이질적인 팀, 2단계 전문화 위임 필요          | Hierarchical (예시 4)          |
| 원인 불명, 전문가 선택이 분석 결과에 따라 달라질 때 | Handoff (예시 5)               |
| 대용량 데이터 처리 중 중단 재개 필요                | Handoff + Persistence (예시 5) |

---

## 산출물 패턴 요약

### 에이전트 정의 파일

- 경로: `.codex/agents/{agent-name}.md` (프로젝트) 또는 `~/.codex/agents/{agent-name}.md` (사용자).
- 필수 YAML: `name`, `description`(pushy·후속 키워드 포함), `kind: local`, `model`(오케스트레이터·Architect → `"gpt-5.5"`, 워커 → `"gpt-5.3-codex"` , `tools` (반드시 사용자 확인 요청·스킬 로드 포함).
- 권장 YAML: `temperature`(역할별 0.2~0.7), `max_turns`(5~20).
- 필수 섹션: 핵심 역할, 작업 원칙, 입출력 프로토콜, 협업 프로토콜(Codex CLI), 에러 핸들링.

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
- **메인 에이전트 단독 갱신**: 워커는 `task_{agent}_{id}.json`에만 기록. tasks.md는 메인이 수집 후 원자적 갱신.
- **Blocked 항목**: ask_user 호출 시 해당 행 상태를 `Blocked`로 표시.

### 스킬 파일 구조

- 경로: `.codex/skills/{skill-name}/SKILL.md`.
- 대형 지식은 `references/`로 분리 (Progressive Disclosure).

### 오케스트레이터 스킬

- 팀 전체를 조율하는 상위 스킬. Phase 0(재실행 감지)부터 Phase 5(보존·보고)까지 포함.
- 템플릿: `references/orchestrator-template.md` 참조.
- 서브에이전트 간 직접 통신 불가 — 모든 협업을 `findings.md`·`tasks.md`·`checkpoint.json`으로 중개.
- `_workspace/workflow.md` Phase 1에서 Stage-Step 선언; 매 사이클 읽어 현재 step의 `활성 에이전트`만 호출. 에이전트 실패 시 최대 2회 재시도(총 3회) → 미해결 시 `Blocked` + 사용자 확인 요청. 임의 Skip 절대 금지.
