# URL から候補チームキーを取る（Project）

**`linear-create-project`** 向け。**Restrictions** に従うこと。フィールド名は **`save_project`** の MCP ディスクリプタで確認する。

## ルールの要約

**`/team/` の直後の 1 セグメントだけ**が候補チームキー。`projects`・`active`・`all`・**後ろに続く別の `/team/`** はチームキーにしない。

## パターン別の例

| 状況 | URL の断片の例 | 候補キー | チームキーにしてはいけないもの |
|------|----------------|----------|-------------------------------|
| チームのプロジェクトビュー | `…/team/ENG/projects/active` | `ENG` | `projects`、`active` |
| チームの一覧系ビュー | `…/team/RND/all` | `RND` | `all` |
| パスが `…/team/.../team/...` のように続く typo 想定 | `…/team/RND/team/active` | `RND`（**最初の** `/team/` の直後だけ） | 2 つ目の `team`、`active` |
| チーム配下の Issue | `…/team/PLAT/issue/WWW-77` | `PLAT` | `WWW`（**`WWW-77` の接頭辞**は Issue のキーでありチームではない） |
| チャットに Issue 番号のみ（URL なし） | `FOO-401` | — | **`FOO`**（プレフィックスをチーム key にしない） |

**`/team/<segment>/` が無い URL**では、ほかのパス片からキーを捏造しない。**`list_teams`** とユーザ確認へ（**Restrictions**）。
