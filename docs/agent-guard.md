# Agent Guard（TAK-99）

Cursor / Claude Code / Codex 向けの **変更操作ガードレール** です。ポリシー本体は `scripts/agent-guard/` に集約し、各ツールは薄い hooks アダプタだけ持ちます。

## ブロック

- **sudo**（および `doas` / `pkexec`）
- **変更系 / DDL SQL**（`INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, `CREATE`, `GRANT` など）
- **kubectl 変更系**（`apply`, `delete`, `exec`, `patch`, `scale`, `rollout` など）
- **変更系 HTTP**（`curl -X POST/PUT/PATCH/DELETE` など）
- **破壊的 git**（`reset --hard`, `push --force` 等）、`git commit --no-verify` / `--no-gpg-sign`

## 許可

- ファイルの作成・編集・削除（tracked / untracked を問わない）
- `git commit` / `git push`
- MCP 書き込み（Linear / Notion 等）
- 読み取り専用操作（`SELECT`、参照系 API、`git status` / `kubectl get` など）

> git 管理外ファイルの編集は hooks ではブロックしません。秘密情報は別 Issue（pre-commit / TAK-100）で扱います。

## 構成

| パス | 役割 |
|------|------|
| `scripts/agent-guard/rules.yaml` | 共通ポリシー |
| `scripts/agent-guard/run.py` | stdin JSON → 判定 JSON |
| `.apm/hooks/agent-guard-*-hooks.json` | ツール別 hooks 定義 |
| `.apm/hooks/scripts/*.sh` | 薄いラッパ（`PLUGIN_ROOT` 空ならリポジトリの `scripts/agent-guard` にフォールバック） |

## 前提条件

- Python 3.10+ と PyYAML（`python3 -c 'import yaml'` で確認）
- APM でこのパッケージをインストールするか、hooks を各ツールの設定に接続する
- Cursor: `beforeShellExecution` のみ
- Claude Code / Codex: `PreToolUse` matcher `"Bash"` のみ

## インストール（APM）

消費者リポジトリで:

```bash
apm install takak2166/agent
```

hooks が各ターゲットにマージされます。ローカル検証時は:

```bash
apm install /path/to/agent --target cursor
```

## 手動動作確認

```bash
# 許可: git status
echo '{"command":"git status"}' | python3 scripts/agent-guard/run.py --target cursor

# 拒否: sudo
echo '{"command":"sudo apt update"}' | python3 scripts/agent-guard/run.py --target cursor

# 拒否: kubectl apply
echo '{"command":"kubectl apply -f x.yaml"}' | python3 scripts/agent-guard/run.py --target cursor
```

## テスト

```bash
python3 -m unittest discover -s scripts/agent-guard/tests -v
```

## トラブルシューティング

- **hooks が動かない / GUARD パスエラー**: `PLUGIN_ROOT` が空のときラッパはリポジトリ直下の `scripts/agent-guard` にフォールバックします。それでも失敗する場合は `AGENT_GUARD_ROOT` を絶対パスで指定してください。
- **全部 deny される**: デフォルトは fail-closed です。許可したい操作が `rules.yaml` の allow ルールに載っているか確認してください。
- **PyYAML がない**: `python3 -m pip install pyyaml`
- **監査ログ**: `AGENT_GUARD_AUDIT_LOG=/tmp/agent-guard.jsonl` をセットすると判定が追記されます。

## 設計メモ

- ファイル編集は hooks 対象外（matcher を shell / Bash に限定）のため、tracked / untracked の区別は行いません。
- ポリシー変更は `rules.yaml` のみ。アダプタは `--target` / `--source` を渡すだけです。
