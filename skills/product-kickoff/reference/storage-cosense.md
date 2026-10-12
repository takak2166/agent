# Writing to Cosense (formerly Scrapbox)

Summarizes procedures verified on a private project on 2026-10-11. Cosense has **no official write REST API**. The methods here are **unofficial** and may change.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `COSENSE_PROJECT` | Target project name (`<project>` in `https://scrapbox.io/<project>`) |
| `COSENSE_SID` | Browser Cookie `connect.sid` value (session for a project member) |

- Never **display, commit, or log** the SID value. In curl use only `-H "Cookie: connect.sid=$COSENSE_SID"` (value from the environment).
- Login check: `curl -s -H "Cookie: connect.sid=$COSENSE_SID" https://scrapbox.io/api/users/me | jq .isGuest` must be `false`.
- Project membership list: `curl -s -H "Cookie: connect.sid=$COSENSE_SID" https://scrapbox.io/api/projects | jq '.projects[].name'`

## CSRF and Origin (as of 2026-10)

- Legacy `X-CSRF-TOKEN` (`csrfToken` from `/api/users/me`) is **no longer returned**.
- Write REST calls require **`Origin: https://scrapbox.io`**. Without it: `403` `CrossOriginWriteNotAllowedError`.
- CSRF token is **not required** (Origin is sufficient).

## Prevent overwrites (mandatory)

| Fact | Agent action |
|------|----------------|
| `GET /api/pages/<project>/<title>` returns **200** even when the page does not exist | Use **`.persistent`** only (`true` = exists, `false` = not created) |
| **import** with the same title **replaces the full page** (line creation times reset) | Before create, require `persistent == false`. If exists, **abort** and propose another title |
| Title must be URL-encoded | `jq -rn --arg t "$TITLE" '$t|@uri'` |

```sh
ENC=$(jq -rn --arg t "$TITLE" '$t|@uri')
curl -s -H "Cookie: connect.sid=$COSENSE_SID" \
  "https://scrapbox.io/api/pages/$COSENSE_PROJECT/$ENC" \
  | jq -e '.persistent == false' >/dev/null \
  || { echo "Page already exists; aborting"; exit 1; }
```

## Method A — new page (recommended): Import API

`POST https://scrapbox.io/api/page-data/import/<project>.json` (multipart, field name **`import-file`**).

Body JSON shape: `{"pages":[{"title":"<title>","lines":["<title>","line2",...]}]}`.

```sh
jq -n --arg t "$TITLE" --rawfile body body.txt \
  '{pages:[{title:$t, lines:([$t] + ($body | rtrimstr("\n") | split("\n")))}]}' > /tmp/import.json
curl -s -w "\nHTTP %{http_code}\n" -X POST \
  "https://scrapbox.io/api/page-data/import/$COSENSE_PROJECT.json" \
  -H "Cookie: connect.sid=$COSENSE_SID" \
  -H "Origin: https://scrapbox.io" \
  -F "import-file=@/tmp/import.json;type=application/octet-stream"
```

- Success: HTTP 200, body like `{"message":"import succeeded! - 1 pages"}`.
- After create: same GET with `persistent == true` and check `.lines[].text`.
- The UI also calls `POST .../import-finish/<project>.json`; in verification, **pages appeared without that call**.
- Multiple pages per request via the `pages` array.

**Use method A for first-time requirements and ADR pages** (default for the kickoff skill set).

## Method B — append, partial update, delete: @cosense/std (Deno)

Verified version: **`jsr:@cosense/std@0.31.0`** (websocket). No delete REST API.

| Operation | API |
|-----------|-----|
| Append / line-level patch | `patch(project, title, (lines) => ..., { sid })` |
| Delete | `deletePage(project, title, { sid })` |

- Return value is `Result` — check `r.ok`.
- Prefer **method B** for appends to existing pages (preserves history and other lines’ creation times).
- Appending via import is possible but **full overwrite**. Do not use import-append on pages you did not create in this session.
- For create-only via `patch`, still check `persistent == false` beforehand (`undefined` from the callback is a safety net only).

Do not embed long Deno scripts in skill bodies. Run a temporary `.ts` in the working directory with `deno run -A` when needed.

## Page body format

| Rule | Detail |
|------|--------|
| First line | Title (`lines[0]`) |
| Indent | Count of **half-width spaces** (no tabs) |
| Headings | Cosense form `[** …]` / `[*** …]` (e.g. `[** 目的]` for the template section “purpose”) — Markdown `#` is a **tag** (`#foo` becomes a link), not a heading |
| Code | `code:name.ext` then one indent level of lines |
| Table | `table:name` then indented tab-separated lines |
| Links | `[text]` is a page link — avoid accidental `[`, `]`, `#` |
| ADR / requirements | Numbering and status in title or body lines (e.g. `ADR-001 ...`, `ステータス: 承認済み` — Japanese: “status: approved”) |

Do not paste template Markdown `##` headings as-is. Convert `product-requirements` / `write-adr` templates to Cosense lines before import.

## Read helpers (CLI)

When `cosense` CLI (`helpfeel/cosense-cli`) is available, you may use its read flow for existence checks and body fetch. Prefer methods A/B above for writes (if CLI edit conflicts with this reference, **this verified reference wins**).

## Common errors

| Symptom | Fix |
|---------|-----|
| 403 `CrossOriginWriteNotAllowedError` | Add `Origin: https://scrapbox.io` |
| `isGuest: true` / 401 | Refresh SID |
| 403 NotMember | SID user is not a project member — confirm membership |

On failure, report status and error name only (not Cookie values). If the user created the page manually, pass **page title** (and public URL pattern) to later steps.
