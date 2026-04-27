# Codex CLI vs Gemini CLI 대응표 + 마이그레이션 가이드

codex-harness와 gemini-harness의 개념·도구·파일 포맷 대응 관계.

## 핵심 대응표

| 개념 | Gemini CLI | Codex CLI |
|------|-----------|-----------|
| **에이전트 정의** | `.gemini/agents/{name}.md` (YAML frontmatter) | `.codex/agents/{name}.toml` (TOML) |
| **스킬 디렉터리** | `.gemini/skills/{name}/SKILL.md` | `.codex/skills/{name}/SKILL.md` |
| **프로젝트 컨텍스트** | `GEMINI.md` | `AGENTS.md` |
| **서브에이전트 호출** | `invoke_agent(@name, prompt=...)` | subagent spawn (Codex 네이티브) |
| **파일 읽기** | `read_file` | shell `cat` / Codex 네이티브 파일 읽기 |
| **파일 쓰기** | `write_file` | `apply_patch` (외과적) / shell `tee` (신규) |
| **사용자 질의** | `ask_user` 도구 | approval prompt / 자연어 질의 |
| **스킬 활성화** | `activate_skill` | `$skill-name` 또는 Codex 자동 선택 |
| **권한 제어** | `tools: [ask_user, activate_skill, ...]` | `sandbox_mode = "read-only \| workspace-write \| danger-full-access"` |
| **병렬 실행** | `invoke_agent(..., wait_for_previous: false)` | subagent 기본 병렬 실행 |
| **순차 실행** | `invoke_agent(..., wait_for_previous: true)` | 스킬 지시로 단계 분리 (이전 task_*.json 확인 후 spawn) |
| **오케스트레이터 전용 도구** | `invoke_agent` | subagent spawn 권한 (max_depth ≥ 1) |
| **서브에이전트 깊이** | 제한 없음 | `max_depth=1` 기본 (`.codex/config.toml`에서 조정) |
| **모델 선택** | `model: "gemini-3.1-pro-preview"` | `model = "codex-1"` |

## 에이전트 정의 포맷 비교

### Gemini (`.gemini/agents/backend-coder.md`)
```yaml
---
name: backend-coder
description: "..."
model: gemini-3-flash-preview
tools:
  - ask_user
  - activate_skill
  - read_file
  - write_file
temperature: 0.3
max_turns: 10
---

# Backend Coder
...
```

### Codex (`.codex/agents/backend-coder.toml`)
```toml
name = "backend-coder"
description = "..."
model = "o4-mini"
sandbox_mode = "workspace-write"

developer_instructions = """
# Backend Coder
...
"""
```

## 오케스트레이터 SKILL.md 구조 비교

| 항목 | Gemini | Codex |
|------|--------|-------|
| 가상 팀 표 | `tools` 컬럼 포함 | `sandbox_mode` 컬럼 포함 |
| Step 0 checkpoint | 동일 | 동일 |
| Step 1 초기화 | `read_file` + `write_file` | shell read/write + `apply_patch` |
| Step 2 에이전트 호출 | `invoke_agent` | subagent spawn |
| 에이전트 생성 출력 | `.gemini/agents/*.md` | `.codex/agents/*.toml` |
| 프로젝트 등록 | `GEMINI.md` | `AGENTS.md` |

## Hierarchical 패턴 차이

Gemini: `invoke_agent` 어디서나 가능 (워커 제외).
Codex: `max_depth=1` 기본 → 팀장이 워커 spawn 불가.

```toml
# .codex/config.toml — Hierarchical 패턴 사용 시 필수
[agents]
max_depth = 2
max_threads = 6
```

## 마이그레이션 체크리스트 (Gemini → Codex)

- [ ] `.gemini/agents/*.md` → `.codex/agents/*.toml` 변환
- [ ] YAML frontmatter → TOML 포맷 변환
- [ ] `tools:` 목록 → `sandbox_mode` 단일 필드로 대체
- [ ] `ask_user` 호출 → approval prompt 또는 자연어 확인으로 대체
- [ ] `invoke_agent` → subagent spawn 방식으로 오케스트레이터 지시 수정
- [ ] `GEMINI.md` → `AGENTS.md` 이름 변경 + 내용 유지
- [ ] `.gemini/skills/` → `.codex/skills/` 경로 변경
- [ ] 모델 ID 교체 (`gemini-*` → `codex-1` / `o4-mini`)
- [ ] `write_file` → `apply_patch` (외과적 수정) + shell (신규 파일)
- [ ] Hierarchical 패턴 사용 시 `.codex/config.toml` `max_depth=2` 설정
