# Cosense（旧 Scrapbox）への書き込み

2026-10-11 に private プロジェクトで実地検証した手順を要約している。Cosense に**公式の書き込み REST API はない**。ここの方法は**非公式**で、仕様が変わることがある。

## 環境変数

| 変数 | 内容 |
|------|------|
| `COSENSE_PROJECT` | 書き込み先プロジェクト名（`https://scrapbox.io/<project>` の `<project>`） |
| `COSENSE_SID` | ブラウザ Cookie `connect.sid` の値（プロジェクトメンバーのセッション） |

- SID の値は**表示・コミット・ログ出力しない**。curl では `-H "Cookie: connect.sid=$COSENSE_SID"` のみ（値は環境変数から）。
- ログイン確認: `curl -s -H "Cookie: connect.sid=$COSENSE_SID" https://scrapbox.io/api/users/me | jq .isGuest` が `false`。
- 所属プロジェクト一覧: `curl -s -H "Cookie: connect.sid=$COSENSE_SID" https://scrapbox.io/api/projects | jq '.projects[].name'`

## CSRF と Origin（2026-10 時点）

- 旧手順の `X-CSRF-TOKEN`（`/api/users/me` の `csrfToken`）は**現在取得できない**。
- 書き込み系 REST には **`Origin: https://scrapbox.io`** が必須。無いと `403` `CrossOriginWriteNotAllowedError`。
- CSRF トークンは**不要**（Origin で足りる）。

## 上書き防止（必須）

| 事実 | エージェントの行動 |
|------|-------------------|
| `GET /api/pages/<project>/<title>` は未存在でも **200** | 存在判定は **`.persistent`** のみ（`true` = 存在、`false` = 未作成） |
| 同名への **import** は**全文上書き**（行の作成時刻もリセット） | 新規作成前に必ず `persistent == false` を確認。既存なら**中止**し別タイトルを提案 |
| タイトルは URL エンコード | `jq -rn --arg t "$TITLE" '$t|@uri'` |

```sh
ENC=$(jq -rn --arg t "$TITLE" '$t|@uri')
curl -s -H "Cookie: connect.sid=$COSENSE_SID" \
  "https://scrapbox.io/api/pages/$COSENSE_PROJECT/$ENC" \
  | jq -e '.persistent == false' >/dev/null \
  || { echo "既に存在するので中止"; exit 1; }
```

## 方法 A — 新規作成（推奨）: Import API

`POST https://scrapbox.io/api/page-data/import/<project>.json`（multipart、フィールド名 **`import-file`**）。

ボディ JSON 形: `{"pages":[{"title":"<title>","lines":["<title>","行2",...]}]}`。

```sh
jq -n --arg t "$TITLE" --rawfile body body.txt \
  '{pages:[{title:$t, lines:([$t] + ($body | rtrimstr("\n") | split("\n")))}]}' > /tmp/import.json
curl -s -w "\nHTTP %{http_code}\n" -X POST \
  "https://scrapbox.io/api/page-data/import/$COSENSE_PROJECT.json" \
  -H "Cookie: connect.sid=$COSENSE_SID" \
  -H "Origin: https://scrapbox.io" \
  -F "import-file=@/tmp/import.json;type=application/octet-stream"
```

- 成功例: HTTP 200、`{"message":"import succeeded! - 1 pages"}` 相当。
- 作成後: 同じ GET で `persistent == true` と `.lines[].text` を確認。
- UI は `POST .../import-finish/<project>.json` も呼ぶが、検証では**未呼び出しでも反映**された。
- 1 リクエストで `pages` 配列により複数ページ可。

**要件定義・ADR の初回作成は方法 A を使う**（キックオフスキル群のデフォルト）。

## 方法 B — 追記・部分更新・削除: @cosense/std（Deno）

検証バージョン: **`jsr:@cosense/std@0.31.0`**（websocket）。REST に削除 API はない。

| 操作 | API |
|------|-----|
| 追記・行の差分更新 | `patch(project, title, (lines) => ..., { sid })` |
| 削除 | `deletePage(project, title, { sid })` |

- 戻り値は `Result` — `r.ok` を確認する。
- 既存ページへの追記は **方法 B**（履歴・他行の作成時刻を残す）。
- import で既存ページに追記することも可能だが**全文上書き**になる。自分が今回作ったページ以外では import 追記を使わない。
- `patch` で新規だけ作る場合も、事前に `persistent == false` を確認する（コールバック内の `undefined` 返却は保険）。

スキル本文に長い Deno スクリプトは載せない。必要なら作業ディレクトリの一時 `.ts` を `deno run -A` で実行する。

## ページ本文の書式

| ルール | 内容 |
|--------|------|
| 1 行目 | タイトル（`lines[0]`） |
| インデント | **半角スペース**の数（タブ不可） |
| 見出し | `[** 見出し]`、`[*** 大見出し]` — Markdown の `#` は**タグ**（`#foo` はリンク）なので見出しに使わない |
| コード | `code:名前.拡張子` の次行から 1 段インデント |
| 表 | `table:名前` の次行からインデント＋タブ区切り |
| リンク | `[文字列]` がページリンク — 意図しない `[` `]` `#` に注意 |
| ADR / 要件 | 連番・ステータスはタイトルまたは本文行（例: `ADR-001 ...`、`ステータス: 承認済み`） |

テンプレの Markdown 見出し（`##`）をそのまま貼らない。`product-requirements` / `write-adr` のテンプレを Cosense 行に変換してから import する。

## 読み取り補助（CLI）

`cosense` CLI（`helpfeel/cosense-cli`）が使える環境では、存在確認や本文取得に read 手順を併用してよい。書き込みは上記 A/B を優先する（CLI edit 手順と矛盾する場合は**この reference の検証結果**を優先）。

## よくあるエラー

| 症状 | 対処 |
|------|------|
| 403 `CrossOriginWriteNotAllowedError` | `Origin: https://scrapbox.io` を付ける |
| `isGuest: true` / 401 | SID 再取得 |
| 403 NotMember 系 | メンバーでない SID — プロジェクト参加を確認 |

失敗時はステータスとエラー名のみ報告（Cookie 本体は出さない）。ユーザーが手動作成した場合は**ページタイトル**（と公開 URL パターン）を後続ステップへ渡す。
