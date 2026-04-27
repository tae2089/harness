<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Codex_CLI-Skill-5C5C5C.svg" alt="Codex CLI Skill">
  <img src="https://img.shields.io/badge/Patterns-7_Architectures-orange.svg" alt="7 Architecture Patterns">
  <a href="https://github.com/tae2089/harness/stargazers"><img src="https://img.shields.io/github/stars/tae2089/harness?style=social" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/README-EN%20%7C%20KO%20%7C%20JA-lightgrey" alt="i18n"></a>
</p>

# Harness — OpenAI Codex CLI サブエージェントオーケストレーション・メタフレームワーク

[English](README.md) | [한국어](README_KO.md) | **日本語**

OpenAI Codex CLI で専門サブエージェントチームを設計するメタフレームワーク。ドメインの自然言語説明一つから、エージェント TOML 定義・オーケストレータースキル・ランタイムスキャフォールディング全体を生成します。

## 概要

Harness はドメイン/プロジェクトに最適なエージェントチームを構成し、各エージェントの役割・サンドボックス権限を定義し、オーケストレータースキルとランタイム状態管理を完全生成するメタスキルです。主要な成果物は `.codex/agents/{name}.toml`、`.agents/skills/{orchestrator}/SKILL.md`、`AGENTS.md` であり、ランタイム状態はすべて `_workspace/` に永続化されます。

## インストール

**個人用（グローバル）:**
```bash
git clone https://github.com/tae2089/harness.git
cp -r harness/skills/codex-harness ~/.agents/skills/
```

**チーム用（リポジトリ内）:**
```bash
cp -r harness/skills/codex-harness .agents/skills/
```

インストール後、Codex CLI セッションで `"build a codex harness"` と発話し、`codex-harness` スキルが自動トリガーされることを確認してください。

> **初めての方へ →** まず [`references/usage-examples.md`](skills/codex-harness/references/usage-examples.md) を確認してください。8 つのドメインシナリオ（SSO・マイグレーション・コンテンツループ・並列リサーチ・障害分析・フルスタック・拡張・部分再実行）と発話パターンのマッピング、非トリガー発話表を提供しています。

---

## コア原則

- **7 つのアーキテクチャパターン:** Pipeline · Fan-out/Fan-in · Expert Pool · Producer-Reviewer · Supervisor · Hierarchical · Handoff。Stage（親課題 / Jira Issue）→ Step（子課題 / Jira Sub-issue）の階層で組み合わせます。
- **命名規則の強制:** Stage・Step 名は deliverable 名詞句の kebab-case（`^[a-z][a-z0-9-]*$`）。`main`・`step1`・`task` などのプレースホルダーは workflow.md スキーマ検証でブロックされます。
- **sandbox_mode 権限制御:** すべてのエージェントに明示的な `sandbox_mode` が必須: `read-only`（Analyst/Architect）· `workspace-write`（Coder/Reviewer/QA）· `danger-full-access`（Operator/Deployer）。ワイルドカード権限は禁止。
- **メインエージェントを単一ブローカーとして:** Codex CLI にはサブエージェント間の直接通信 API がありません。すべての協調はメインが `_workspace/findings.md`・`tasks.md`・`checkpoint.json`・`task_*.json` 経由で仲介します。
- **3 要素構成:** `.codex/agents/*.toml` + `.agents/skills/*/SKILL.md` + `AGENTS.md`。
- **Plan Mode 必須:** 新規構築・拡張時は `/plan` または `Shift+Tab` で有効化。
- **Zero-Tolerance Failure Protocol:** 任意のスキップは絶対禁止。最大 2 回リトライ（合計 3 回）→ 未解決時は `Blocked` + ユーザー確認要求。

## ディレクトリ構造

```
harness/
└── skills/
    └── codex-harness/
        ├── SKILL.md                              # メインスキル定義
        └── references/
            ├── usage-examples.md                 # 🚀 トリガー発話 8 種 + モードマッピング
            ├── agent-design-patterns.md          # 7 パターン + sandbox_mode マッピング
            ├── orchestrator-template.md          # オーケストレーター Step 0~5 疑似コード
            ├── orchestrator-procedures.md        # エラーハンドリング・blocked・handoff 手順
            ├── team-examples.md                  # 実践コラボレーション事例インデックス
            ├── stage-step-guide.md               # Stage-Step ワークフロー仕様
            ├── skill-writing-guide.md            # スキル作成ガイド
            ├── skill-testing-guide.md            # スキルテスト/検証ガイド
            ├── qa-agent-guide.md                 # QA エージェントガイド
            ├── evolution-protocol.md             # ハーネス進化/運用プロトコル
            ├── expansion-matrix.md               # 拡張時 Phase 選択マトリクス
            ├── schemas/                          # ランタイムスキーマ + エージェントテンプレート（SoT）
            │   ├── models.md                     # ⚠️ モデル ID 正本 + reasoning_effort ガイド
            │   ├── agent-worker.template.toml    # ワーカーエージェント TOML 基準
            │   ├── agent-state-manager.template.toml # 状態管理者 TOML 基準
            │   ├── agent-orchestrator.template.md # オーケストレータースキル生成基準
            │   ├── task.schema.json
            │   ├── checkpoint.schema.json
            │   ├── workflow.template.md
            │   ├── findings.template.md
            │   ├── tasks.template.md
            │   └── README.md
            └── examples/
                ├── full-bundle/sso-style.md      # 全成果物パッケージのデモ
                ├── team/01~05-*.md               # パターン別コラボレーション例 5 種
                └── step/01~05-*.md               # Stage-Step 構成例 5 種
                    + test-scenarios.md           # トリガー検証シナリオ
```

## 使い方

まず Plan Mode を有効化してから自然言語で発話:

```
/plan
SSO認証プロジェクト用の codex ハーネスを構築して
```

| 発話パターン | モード |
|-------------|--------|
| "codex ハーネスを構成/構築/設計して"、"{ドメイン} codex 自動化を作って" | 新規構築 |
| "既存のハーネスに{機能}を追加して"、"エージェントを追加" | 既存拡張 |
| "ハーネスを点検/監査/現状確認"、"drift 同期" | 運用/メンテナンス |
| "前の結果を再実行/修正/改善" | 運用（部分再実行） |

> 新しいドメインを受け取ったら、まず `references/usage-examples.md` の 8 シナリオと照合してください。非トリガー発話表で誤検知を防止します。

## ワークフロー Phase

| Phase | 説明 |
|-------|------|
| Phase 0 | 現状監査とモード分岐（新規/拡張/運用） |
| Phase 1 | ドメイン分析とパターンマッチング（usage-examples.md シナリオ照合） |
| Phase 2 | 仮想チーム設計 + sandbox_mode マッピング + アーキテクチャパターン選択 |
| Phase 3 | エージェント TOML 生成（`.codex/agents/{name}.toml`） |
| Phase 4 | オーケストレータースキル生成（`.agents/skills/{name}/SKILL.md`） |
| Phase 5 | 統合とオーケストレーション（workflow.md・findings.md・tasks.md・checkpoint.json 初期化） |
| Phase 6 | 検証（トリガー検証、Resume、Zero-Tolerance、AGENTS.md 登録） |

> 拡張・運用モードは `expansion-matrix.md` / `evolution-protocol.md` で必要な Phase のみ選択実行。

## 生成される成果物

```
{プロジェクト}/
├── .codex/
│   └── agents/{name}.toml              # エージェント定義（TOML: 役割、sandbox_mode、モデル）
├── .agents/
│   └── skills/{orchestrator}/
│       ├── SKILL.md                    # オーケストレータースキル
│       └── references/schemas/         # スキーマコピー（必須同梱）
├── _workspace/
│   ├── _schemas/                       # ランタイムスキーマコピー（Step 1.3 で同期）
│   ├── workflow.md                     # Stage（親課題）→ Step（子課題）構造宣言
│   ├── findings.md                     # データブローカー
│   ├── tasks.md                        # タスクボード
│   ├── checkpoint.json                 # 再開地点（Durable Execution）
│   └── tasks/task_{agent}_{id}.json    # エージェント別成果物メタ
└── AGENTS.md                           # ハーネスポインター + 変更履歴
```

## 7 パターン選択ガイド

| パターン | 適した場合 |
|---------|-----------|
| Pipeline | 設計 → 実装 → 検証など、順次依存するタスク |
| Fan-out/Fan-in | 並列独立タスクの実行後に統合 |
| Expert Pool | 状況に応じた専門家の選択と呼び出し |
| Producer-Reviewer | 生成後の品質レビューループ（PASS/FIX/REDO） |
| Supervisor | tasks.md claim によるメインの動的配置 |
| Hierarchical | チームリーダー → ワーカー 2 段階委任（異質ドメイン） |
| Handoff | 分析結果に基づく次の専門家への動的ルーティング |

## 参考ドキュメント

- `skills/codex-harness/SKILL.md` — メインスキル定義 + ワークフロー + 参考インデックス
- `references/usage-examples.md` — 🚀 トリガー発話 8 種 + モードマッピング + 非トリガー発話 + Phase 適用マトリクス
- `references/agent-design-patterns.md` — 7 パターン詳細、エージェント定義構造、sandbox_mode マッピング
- `references/orchestrator-template.md` — オーケストレーター Step 0~5 疑似コード、checkpoint.json スキーマ
- `references/orchestrator-procedures.md` — エラーハンドリング決定木、blocked_protocol、handle_handoff
- `references/team-examples.md` — パターン別実践事例インデックス
- `references/stage-step-guide.md` — workflow.md 仕様、Stage・Step 遷移プロトコル
- `references/skill-writing-guide.md` — スキル作成パターン、データスキーマ標準、フラット Step → Stage-Step マイグレーション
- `references/skill-testing-guide.md` — トリガー検証、Resume テスト、Zero-Tolerance 検証
- `references/qa-agent-guide.md` — QA エージェント統合整合性検証
- `references/evolution-protocol.md` — ハーネス進化、運用/メンテナンスワークフロー
- `references/expansion-matrix.md` — 既存拡張 Phase 選択マトリクス
- `references/schemas/models.md` — ⚠️ モデル ID 正本 + `model_reasoning_effort` 選択ガイド
- `references/schemas/agent-worker.template.toml` · `agent-orchestrator.template.md` — エージェント生成基準テンプレート
- `references/schemas/` — ランタイムスキーマ SoT（task・checkpoint・workflow・findings・tasks テンプレート）
- `references/examples/full-bundle/sso-style.md` — 全成果物パッケージの正本例
- `references/examples/team/` · `references/examples/step/` — パターン別・構造別の詳細例
