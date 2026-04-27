# Gemini 모델 ID 레지스트리 (SoT)

에이전트 템플릿에서 참조하는 **단일 모델 ID 정본**. 여기만 갱신하면 모든 템플릿에 반영된다.

> **갱신 방법:** Gemini CLI에서 `gemini models list` 실행 → 최신 ID 확인 후 아래 테이블 업데이트.

## 역할별 모델 배정

| 역할 티어                                  | 사용 모델 ID             | 비고                                    |
| ------------------------------------------ | ------------------------ | --------------------------------------- |
| 오케스트레이터, Architect (복잡 추론·설계) | `gemini-3.1-pro-preview` | 고비용·고성능 — 오케스트레이터·설계자만 |
| 워커 (Coder·Analyst·Reviewer·Operator)     | `gemini-3-flash-preview` | 저비용·고속 — 반복 작업 워커 기본값     |

> ⚠️ **위 모델 ID는 예시 기준값.** 실제 사용 전 `gemini models list`로 현재 활성 ID 확인 후 교체.
> 잘못된 모델 ID를 agent .md에 하드코딩하면 런타임 에러 발생.

## 갱신 프로토콜

1. `gemini models list` 실행 → 현재 사용 가능한 모델 ID 목록 확인.
2. 위 테이블 모델 ID 수정.
3. `references/schemas/agent-worker.template.md`, `references/schemas/agent-orchestrator.template.md`의 `model:` 필드도 동일하게 수정.
4. 이후 harness로 생성되는 모든 에이전트는 새 ID 적용.
5. **기존 생성 에이전트는 수동 갱신 필요** (harness 재생성 또는 직접 편집).
