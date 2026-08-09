# Linear 週次サマリ — 出力テンプレート

以下の構造・見出し・表形式に従う。プレースホルダは `<...>`。実データで置換する。

```markdown
## 📊 Linear 週次サマリ（<YYYY/MM/DD> 〜 <MM/DD>）

### ✅ 完了 Issue（<N>件）
| Issue | タイトル | 完了日 | プロジェクト |
|:------|:---------|:-------|:-------------|
| [<KEY>](<issue-url>) | <title> | <MM/DD> | <project-name or —> |

### 🚀 着手 Issue（<N>件）
- [<KEY>](<issue-url>) <title>（<MM/DD> 着手）

### 📝 新規作成 Issue（<N>件）
- **<グループ名> <N>件**（<KEY>〜<KEY>）: <要約>（<MM/DD>）
- **<プロジェクト名> <N>件**: <KEY>, <KEY>, <KEY>

### 🌟 ハイライト
- **<プロジェクト名>** <成果の要約>
- **<プロジェクト名>** <成果の要約>

---

### ⚠️ スケジュール / Update 要対応 Project

（該当 Project が無い場合、この `---` 以降のブロック全体を省略してよい）

#### 📅 スケジュール要確認
| Project | 状況 | 詳細 |
|:--------|:-----|:-----|
| [<name>](<project-url>) | 🔴 期限超過（<N>日） | Target: <MM/DD>、<status> のまま。<今週の関連進捗> |
| [<name>](<project-url>) | 🟡 Target Date 未設定 | <今週の進捗>. スケジュール設定を検討 |
| [<name>](<project-url>) | 🟡 ステータス不一致 | Project は <status> だが <KEY> が In Progress。ステータス更新を検討 |
| [<name>](<project-url>) | 🟡 期限まで<N>日 | Target: <MM/DD>、前回 Update で <health>。進捗確認推奨 |

#### 📢 Update 投稿が必要（7日以上未更新 or 未投稿）
| Project | 最終 Update | 経過日数 | 備考 |
|:--------|:------------|:---------|:-----|
| [<name>](<project-url>) | <MM/DD> | <N>日 | <health>、<反映すべき内容> |
| [<name>](<project-url>) | 未投稿 | — | <反映すべき内容> |

> 先週中の Project Status Update: **<N>件**
```

## 記入ルール

- **完了 Issue 表**: 0 件なら `(0件)` と見出しのみ、表は省略可。
- **着手 / 新規**: 0 件なら見出し + `(0件)` の一行で可。
- **新規 Issue グループ化**: 同一目的の一括起票はレンジ + 要約 1 行にまとめる。
- **ハイライト**: 完了数・再開・プロジェクト完了など、週の narrative を 3–5 行。
- **経過日数**: レポート生成日（JST）基準。`未投稿` は経過日数を `—`。
- **health 表記**: Linear の `onTrack` / `atRisk` / `offTrack` をそのまま lowercase で表示（例: `atRisk`）。

## 参考例（2026/07/26 〜 08/02）

```markdown
## 📊 Linear 週次サマリ（2026/07/26 〜 08/02）

### ✅ 完了 Issue（9件）
| Issue | タイトル | 完了日 | プロジェクト |
|:------|:---------|:-------|:-------------|
| [TAK-123](https://linear.app/me-time/issue/TAK-123) | quoridor-2 に AGENTS.md をスキャフォールドする | 08/01 | Quoridor Webアプリリリース |
| [TAK-120](https://linear.app/me-time/issue/TAK-120) | AGENTS.md / CLAUDE.md 欠如時のスキャフォールド skill | 08/01 | AI活用フロー実装・実験 |
| [TAK-122](https://linear.app/me-time/issue/TAK-122) | Linearでタスクを進めるためのスキルの作成 | 08/01 | AI活用フロー実装・実験 |
| [TAK-121](https://linear.app/me-time/issue/TAK-121) | 会話履歴のスキル化検討 | 08/01 | AI活用フロー実装・実験 |
| [TAK-99](https://linear.app/me-time/issue/TAK-99) | Agent 変更操作ガードレール（汎用 hooks）の実装 🔴High | 07/31 | AI活用フロー実装・実験 |
| [TAK-103](https://linear.app/me-time/issue/TAK-103) | メインPCのストレージを空ける | 07/29 | — |
| [TAK-105](https://linear.app/me-time/issue/TAK-105) | 資料作成 | 07/29 | ぎょーむがいLT資料作成 |
| [TAK-106](https://linear.app/me-time/issue/TAK-106) | 資料のアウトライン作成 | 07/29 | ぎょーむがいLT資料作成 |
| [TAK-107](https://linear.app/me-time/issue/TAK-107) | self hosted agentの用意 | 07/26 | AI活用フロー実装・実験 |

### 🚀 着手 Issue（6件）
- [TAK-24](https://linear.app/me-time/issue/TAK-24) CKAD 取得（07/29 着手）
- [TAK-106](https://linear.app/me-time/issue/TAK-106) 資料のアウトライン作成（07/26）
- [TAK-107](https://linear.app/me-time/issue/TAK-107) self hosted agentの用意（07/26）
- [TAK-120](https://linear.app/me-time/issue/TAK-120) AGENTS.md スキャフォールド skill（08/01）
- [TAK-122](https://linear.app/me-time/issue/TAK-122) Linearタスクスキル（08/01）
- [TAK-123](https://linear.app/me-time/issue/TAK-123) quoridor-2 AGENTS.md（08/01）

### 📝 新規作成 Issue（17件）
- **CKAD学習タスク 12件**（TAK-108〜119）: Day 1〜12 の学習計画を一括起票（07/29）
- **AI活用フロー 3件**: TAK-121, TAK-122, TAK-120
- **Quoridor 1件**: TAK-123
- **その他 1件**: TAK-107（self hosted agent）

### 🌟 ハイライト
- **AI活用フロー実装・実験** が大きく前進: hooks 実装完了（TAK-99）、スキル整備（TAK-120/122）、self-hosted agent 構築（TAK-107）
- **ぎょーむがいLT資料作成** プロジェクト完了（TAK-105/106）
- **CKAD取得** を再開: 学習計画を Day 単位で 12 タスクに分解し、TAK-24 を In Progress に

---

### ⚠️ スケジュール / Update 要対応 Project

#### 📅 スケジュール要確認
| Project | 状況 | 詳細 |
|:--------|:-----|:-----|
| [Quoridor Webアプリリリース](https://linear.app/me-time/project/quoridor-webアプリリリース-6c7e816a6ff6) | 🔴 期限超過（42日） | Target: 06/21、In Progress のまま。今週 TAK-123 完了 |
| [AI活用フロー実装・実験](https://linear.app/me-time/project/ai活用フロー実装実験-e03b30dec53f) | 🟡 Target Date 未設定 | 今週 5 Issue 完了と大きな進捗あり。スケジュール設定を検討 |
| [CKAD取得（〜2026-10-29）](https://linear.app/me-time/project/ckad取得2026-10-29-a3f7986bbe7a) | 🟡 ステータス不一致 | Project は Backlog だが TAK-24 が In Progress。ステータス更新を検討 |
| [効率的なGo（積読）](https://linear.app/me-time/project/効率的なgo積読-9357a4f48f89) | 🟡 期限まで16日 | Target: 08/18、前回 Update で atRisk。進捗確認推奨 |

#### 📢 Update 投稿が必要（7日以上未更新 or 未投稿）
| Project | 最終 Update | 経過日数 | 備考 |
|:--------|:------------|:---------|:-----|
| [Quoridor Webアプリリリース](https://linear.app/me-time/project/quoridor-webアプリリリース-6c7e816a6ff6) | 07/12 | 21日 | atRisk、TAK-123 完了を反映すべき |
| [AI活用フロー実装・実験](https://linear.app/me-time/project/ai活用フロー実装実験-e03b30dec53f) | 07/12 | 21日 | offTrack 表示のまま。今週 5 Issue 完了の報告が必要 |
| [効率的なGo（積読）](https://linear.app/me-time/project/効率的なgo積読-9357a4f48f89) | 07/21 | 12日 | atRisk、Target 08/18 まで進捗確認 |
| [ソフトウェアアーキテクチャの基礎 第2版（積読）](https://linear.app/me-time/project/ソフトウェアアーキテクチャの基礎-第2版積読-979020cd52cb) | 07/21 | 12日 | Planned、Start 08/19 前に状況確認 |
| [CKAD取得（〜2026-10-29）](https://linear.app/me-time/project/ckad取得2026-10-29-a3f7986bbe7a) | 未投稿 | — | 学習再開・12タスク起票を報告すべき |
| [ぎょーむがいLT資料作成](https://linear.app/me-time/project/ぎょーむがいlt資料作成-e1a5f753e295) | 未投稿 | — | Completed だが Update なし。完了報告を推奨 |

> 先週中の Project Status Update: **0件**
```
