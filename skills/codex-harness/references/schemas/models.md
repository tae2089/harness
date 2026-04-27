# OpenAI 모델 ID 레지스트리 (SoT)

Codex 에이전트 템플릿에서 참조하는 **단일 모델 ID 정본**. 여기만 갱신하면 모든 템플릿에 반영된다.

## 역할별 모델 배정

| 역할 티어                                  | 사용 모델 ID   | 비고                                                  |
| ------------------------------------------ | -------------- | ----------------------------------------------------- |
| 오케스트레이터, Architect (복잡 추론·설계) | `gpt-5.5`      | 256K ctx, 심층 추론·연구·다단계 계획                  |
| 워커 (Coder·Analyst·Reviewer·Operator)     | `gpt-5.5`      | 1M ctx, 대형 코드베이스·리팩토링·80% SWE-Bench        |
| State Manager (CRUD 전담)                  | `gpt-5.4-mini` | 400K ctx, 고속·저비용 ($0.30/1M) — 단순 파일 읽쓰기만 |

> ⚠️ 잘못된 모델 ID를 agent TOML에 하드코딩하면 런타임 에러 발생.

## model_reasoning_effort 선택 기준

| 값       | 적합 에이전트           | 특징                                  |
| -------- | ----------------------- | ------------------------------------- |
| `low`    | State Manager           | 단순 CRUD, 속도·비용 우선             |
| `medium` | Analyst, Researcher     | 조사·정리, 충분한 추론                |
| `high`   | Coder, Reviewer, QA     | 복잡 구현·디버깅                      |
| `xhigh`  | Orchestrator, Architect | 다단계 에이전트 추론·계획 (최고 비용) |

## 갱신 프로토콜

신규 모델 출시 시 이 파일만 업데이트:

1. 위 테이블 모델 ID 수정 (신규 모델 행 추가 또는 기존 ID 교체).
2. `references/schemas/agent-worker.template.toml`의 `model` 필드도 동일하게 수정.
3. 이후 harness로 생성되는 모든 에이전트는 새 ID 적용.
4. **기존 생성 에이전트는 수동 갱신 필요** (`.codex/agents/*.toml` 직접 편집).
