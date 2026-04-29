<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Codex_CLI-Skill-5C5C5C.svg" alt="Codex CLI Skill">
  <img src="https://img.shields.io/badge/Gemini_CLI-Skill-4285F4.svg" alt="Gemini CLI Skill">
  <img src="https://img.shields.io/badge/Patterns-7_Architectures-orange.svg" alt="7 Architecture Patterns">
  <a href="https://github.com/tae2089/harness/stargazers"><img src="https://img.shields.io/github/stars/tae2089/harness?style=social" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/README-EN%20%7C%20KO%20%7C%20JA-lightgrey" alt="i18n"></a>
</p>

# Harness — サブエージェントオーケストレーション・メタフレームワーク

[English](README.md) | [한국어](README_KO.md) | **日本語**

AI コーディングエージェントで専門サブエージェントチームを設計するメタフレームワーク。ドメインの自然言語説明一つから、エージェント定義・オーケストレータースキル・ランタイムスキャフォールディング全体を生成します。

## 提供スキル

| スキル | CLI | エージェント定義 | スキルパス |
|--------|-----|----------------|----------|
| `codex-harness` | OpenAI Codex CLI | `.codex/agents/{name}.toml` | `.codex/skills/` |
| `gemini-harness` | Google Gemini CLI | `.gemini/agents/{name}.md` | `.gemini/skills/` |

---

## codex-harness (OpenAI Codex CLI)

### インストール

**個人用（グローバル）:**
```bash
git clone https://github.com/tae2089/harness.git
cp -r harness/skills/codex-harness ~/.codex/skills/
```

**チーム用（リポジトリ内）:**
```bash
cp -r harness/skills/codex-harness .codex/skills/
```

インストール後、Codex CLI セッションで `"build a codex harness"` と発話し、`codex-harness` スキルが自動トリガーされることを確認してください。

> **初めての方へ →** まず [`references/usage-examples.md`](skills/codex-harness/references/usage-examples.md) を確認してください。8 つのドメインシナリオと発話パターンのマッピング、非トリガー発話表を提供しています。

### コア原則（Codex CLI）

- **sandbox_mode 権限制御:** すべてのエージェントに明示的な `sandbox_mode` が必須: `read-only`（Analyst/Architect）· `workspace-write`（Coder/Reviewer/QA）· `danger-full-access`（Operator/Deployer）。ワイルドカード権限は禁止。
- **Plan Mode 必須:** 新規構築・拡張時は `/plan` または `Shift+Tab` で有効化。
- **メインエージェントを単一ブローカーとして:** サブエージェント間の直接通信 API なし。すべての協調は `_workspace/` 経由で仲介。
- **3 要素構成:** `.codex/agents/*.toml` + `.codex/skills/*/SKILL.md` + `AGENTS.md`。

### 使い方

```
/plan
SSO認証プロジェクト用の codex ハーネスを構築して
```

### 生成される成果物

```
{プロジェクト}/
├── .codex/
│   ├── agents/{name}.toml              # エージェント定義（TOML: 役割、sandbox_mode、モデル）
│   └── skills/{orchestrator}/
│       ├── SKILL.md
│       └── references/schemas/
├── _workspace/
│   ├── workflow.md
│   ├── findings.md
│   ├── tasks.md
│   ├── checkpoint.json
│   └── tasks/task_{agent}_{id}.json
└── AGENTS.md
```

---

## gemini-harness (Google Gemini CLI)

### インストール

```bash
gemini skills install https://github.com/tae2089/harness.git --path skills
```

インストール後、Gemini CLI セッションで `"ハーネスを構成して"` と発話し、`gemini-harness` スキルが自動トリガーされることを確認してください。

> **初めての方へ →** まず [`references/usage-examples.md`](skills/gemini-harness/references/usage-examples.md) を確認してください。8 つのドメインシナリオと発話パターンのマッピング、非トリガー発話表を提供しています。

### コア原則（Gemini CLI）

- **厳格なツール権限制御:** `tools: ["*"]` は禁止。すべてのエージェントに `ask_user`・`activate_skill` が必須。`invoke_agent` はオーケストレーター/Supervisor 専用。
- **Plan Mode 必須:** 新規構築・拡張時は `enter_plan_mode` を強制（yolo モードを除く）。
- **メインエージェントを単一ブローカーとして:** `SendMessage`/`TeamCreate` API なし。すべての協調は `_workspace/` 経由で仲介。
- **3 要素構成:** `.gemini/agents/` + `.gemini/skills/` + `GEMINI.md`。

### 使い方

```
/gemini-harness SSO認証プロジェクト用のハーネスを構築して
```

または自然言語発話:

| 発話パターン | モード |
|-------------|--------|
| "ハーネスを構成/構築/設計して"、"{ドメイン}を自動化して" | 新規構築 |
| "既存のハーネスに{機能}を追加して"、"エージェントを追加" | 既存拡張 |
| "ハーネスを点検/監査/現状確認"、"drift 同期" | 運用/メンテナンス |
| "前の結果を再実行/修正/改善" | 運用（部分再実行） |

### 生成される成果物

```
{プロジェクト}/
├── .gemini/
│   ├── agents/{name}.md                # エージェント定義（役割、tools、temperature）
│   └── skills/{orchestrator}/
│       ├── SKILL.md
│       └── references/schemas/
├── _workspace/
│   ├── workflow.md
│   ├── findings.md
│   ├── tasks.md
│   ├── checkpoint.json
│   └── tasks/task_{agent}_{id}.json
└── GEMINI.md
```

---

## 共通: コア概念

### ワークフロー Phase

| Phase | 説明 |
|-------|------|
| Phase 0 | 現状監査とモード分岐（新規/拡張/運用） |
| Phase 1 | ドメイン分析とパターンマッチング（usage-examples.md シナリオ照合） |
| Phase 2 | 仮想チーム設計 + 権限マッピング + アーキテクチャパターン選択 |
| Phase 3 | エージェント定義生成 |
| Phase 4 | オーケストレータースキル生成 |
| Phase 5 | 統合とオーケストレーション（workflow.md・findings.md・tasks.md・checkpoint.json 初期化） |
| Phase 6 | 検証（トリガー検証、Resume、Zero-Tolerance、プロジェクトマニフェスト登録） |

### 7 パターン選択ガイド

| パターン | 適した場合 |
|---------|-----------|
| Pipeline | 設計 → 実装 → 検証など、順次依存するタスク |
| Fan-out/Fan-in | 並列独立タスクの実行後に統合 |
| Expert Pool | 状況に応じた専門家の選択と呼び出し |
| Producer-Reviewer | 生成後の品質レビューループ（PASS/FIX/REDO） |
| Supervisor | tasks.md claim によるメインの動的配置 |
| Hierarchical | チームリーダー → ワーカー 2 段階委任（異質ドメイン） |
| Handoff | 分析結果に基づく次の専門家への動的ルーティング |

### 命名規則

Stage・Step 名は deliverable 名詞句の kebab-case（`^[a-z][a-z0-9-]*$`）。`main`・`step1`・`task` などのプレースホルダーは workflow.md スキーマ検証でブロックされます。

### Zero-Tolerance Failure Protocol

任意のスキップは絶対禁止。最大 2 回リトライ（合計 3 回）→ 未解決時は `Blocked` + ユーザー確認要求。

---

## ディレクトリ構造

```
harness/
└── skills/
    ├── codex-harness/
    │   ├── SKILL.md
    │   └── references/
    │       ├── usage-examples.md
    │       ├── agent-design-patterns.md
    │       ├── orchestrator-template.md
    │       ├── orchestrator-procedures.md
    │       ├── team-examples.md
    │       ├── stage-step-guide.md
    │       ├── skill-writing-guide.md
    │       ├── skill-testing-guide.md
    │       ├── qa-agent-guide.md
    │       ├── evolution-protocol.md
    │       ├── expansion-matrix.md
    │       ├── schemas/
    │       │   ├── models.md                     # ⚠️ モデル ID 正本
    │       │   ├── agent-worker.template.toml
    │       │   ├── agent-state-manager.template.toml
    │       │   ├── agent-orchestrator.template.md
    │       │   ├── task.schema.json
    │       │   ├── checkpoint.schema.json
    │       │   ├── workflow.template.md
    │       │   ├── findings.template.md
    │       │   ├── tasks.template.md
    │       │   └── README.md
    │       └── examples/
    │           ├── full-bundle/sso-style.md
    │           ├── team/01~05-*.md
    │           └── step/01~05-*.md
    └── gemini-harness/
        ├── SKILL.md
        └── references/                           # codex-harness と同一構造
```

## 参考ドキュメント

### codex-harness
- `skills/codex-harness/SKILL.md` — メインスキル定義 + ワークフロー + 参考インデックス
- `references/schemas/models.md` — ⚠️ モデル ID 正本 + `model_reasoning_effort` 選択ガイド
- `references/schemas/agent-worker.template.toml` · `agent-orchestrator.template.md` — エージェント生成基準テンプレート

### gemini-harness
- `skills/gemini-harness/SKILL.md` — メインスキル定義 + ワークフロー + 参考インデックス
- `references/schemas/models.md` — ⚠️ モデル ID 正本
- `references/schemas/agent-worker.template.md` · `agent-orchestrator.template.md` — エージェント生成基準テンプレート

### 共通参考
- `references/usage-examples.md` — 🚀 トリガー発話 8 種 + モードマッピング + 非トリガー発話 + Phase 適用マトリクス
- `references/agent-design-patterns.md` — 7 パターン詳細、エージェント定義構造、権限マッピング
- `references/orchestrator-template.md` — オーケストレーター Step 0~5 疑似コード、checkpoint.json スキーマ
- `references/orchestrator-procedures.md` — エラーハンドリング決定木、blocked_protocol、handle_handoff
- `references/team-examples.md` — パターン別実践事例インデックス
- `references/stage-step-guide.md` — workflow.md 仕様、Stage・Step 遷移プロトコル
- `references/skill-writing-guide.md` — スキル作成パターン、データスキーマ標準
- `references/skill-testing-guide.md` — トリガー検証、Resume テスト、Zero-Tolerance 検証
- `references/qa-agent-guide.md` — QA エージェント統合整合性検証
- `references/evolution-protocol.md` — ハーネス進化、運用/メンテナンスワークフロー
- `references/expansion-matrix.md` — 既存拡張 Phase 選択マトリクス
- `references/examples/full-bundle/sso-style.md` — 全成果物パッケージの正本例
- `references/examples/team/` · `references/examples/step/` — パターン別・構造別の詳細例
