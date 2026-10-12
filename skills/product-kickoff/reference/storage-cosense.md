# Cosense storage (via cosense-cli)

Product kickoff skills read and write requirements and ADRs on **Cosense** (formerly Scrapbox) only through the **`cosense`** skill and **`@helpfeel/cosense-cli`** — not via raw HTTP, curl, jq, import API, or Deno.

Upstream skill (read the installed copy after `apm install`): [helpfeel/cosense-cli `skills/cosense`](https://github.com/helpfeel/cosense-cli/tree/main/skills/cosense). Command details: `cosense <command> --help`.

## Prerequisites

| Requirement | Detail |
|-------------|--------|
| CLI | `npm install -g @helpfeel/cosense-cli` (Node 24+) |
| APM skill | `helpfeel/cosense-cli/skills/cosense` (declared in [`../apm.yml`](../apm.yml) for **`product-kickoff`**) |
| Agent workflow | Read and follow the installed **`cosense`** skill (`edit-page.md`, `read-page.md`, `login.md` as needed) |

## Environment variables

| Variable | Purpose |
|----------|---------|
| `COSENSE_PROJECT` | Project name (`<project>` in `https://scrapbox.io/<project>`) |
| `COSENSE_PAT` | Personal Access Token; the CLI reads it from the environment (overrides saved credentials). Never display, commit, or log the value. |

- **Project URL** for CLI args: `https://scrapbox.io/$COSENSE_PROJECT`
- **Page URL** for a titled page: `https://scrapbox.io/$COSENSE_PROJECT/<url-encoded-title>`
- Auth failures (401/403): see **`cosense`** skill `login.md` (user runs `cosense login` in their terminal; agents do not paste tokens into chat).

## Non-negotiables (kickoff skills)

1. **No overwrite without approval** — if `readPage` reports `persistent: true`, **abort** create and ask the user (different title, explicit update workflow, or cancel).
2. **No secrets in output** — reference env var **names** only; never paste `COSENSE_PAT`.
3. **All reads/writes via CLI** — use the commands below; do not duplicate low-level API steps in kickoff skill bodies.

## Existence check

Before creating a page:

1. `cosense readPage '<pageUrl>'` (quote URLs that contain spaces or non-ASCII).
2. Inspect **`persistent`**: `false` → safe to create; `true` → page exists — **do not** create or replace without explicit user approval for an update.

`GET` returning 200 for missing pages is handled by the CLI; trust **`persistent`**, not HTTP status alone.

## New page (requirements, ADR)

Default for first-time **requirements** and **ADR** pages:

1. Confirm `persistent == false` via `readPage`.
2. Build **plain-text body** for `previewEdit --new`:
   - **Line 1** = full page title (exact string).
   - Following lines = Cosense body (see **Body format**).
3. `cosense previewEdit --new '<projectUrl>'` with stdin = that plain text (or `previewEdit --input-file <path>` on Windows — see **`cosense`** `edit-page.md`).
4. Review preview output; then `cosense submitEdit '<projectUrl>' <previewId>`.
5. Do not reuse the same `previewId` after a successful submit.

For **`previewEdit --new`**, do **not** prepend the title twice: line 1 is the title; do not add a separate title field in JSON.

## Update existing page (append, replace, status)

Only after the user approves changing an existing page:

1. `readPage` → note top-level page `id` and line `id`s.
2. `cosense previewEdit '<projectUrl>' <pageId>` with stdin = **ops JSON** (`insertBefore`, `replace`, `delete` per `cosense previewEdit --help`).
3. Append at end: use anchor `_end` (or `insertBefore` before trailing blank lines if that reads better — see **`cosense`** `edit-page.md`).
4. `cosense submitEdit '<projectUrl>' <previewId>`.

Use this path for **Deprecated** / **Superseded** status blocks on old ADRs after user confirmation — not for silent full-page replacement.

## Delete page

Only when the user explicitly requests deletion:

1. `cosense previewDelete '<projectUrl>' <pageId>`
2. `cosense submitEdit '<projectUrl>' <previewId>`

## Listing ADR numbers

Page titles use **`ADR-<NNN>-<slug>`** (three-digit `NNN`, ASCII slug). To allocate the next number:

- Use `cosense listPages '<projectUrl>'` and/or `cosense searchFullText` (and `cosense readPage` when needed) to find existing titles matching `ADR-` + three digits.
- **Next NNN** = max existing NNN + 1, or `001` if none.

Do not scan a separate `ADR/` path prefix; titles are flat `ADR-001-...` style.

## Body format (Cosense lines)

| Rule | Detail |
|------|--------|
| First line | Page title (same as agreed storage title) |
| Indent | Half-width spaces only (no tabs) |
| Section headings | Cosense `[** …]` / `[*** …]` — not Markdown `#` ( `#word` becomes a tag link) |
| Code | `code:name.ext` then one indent level of body lines |
| Tables | `table:name` then indented tab-separated lines |
| Links | `[text]` is a page link — avoid accidental `[`, `]`, `#` |
| ADR / requirements | Status and ids in title or body (e.g. `ステータス: 承認済み` — Japanese “status: approved”) |

Convert [`product-requirements`](../../product-requirements/reference/requirements-template.md) and [`write-adr`](../../write-adr/reference/adr-template.md) templates to Cosense lines before `previewEdit --new`. Templates stay in Japanese where noted; stored headings may be Japanese per those files.

## Errors

| Symptom | Action |
|---------|--------|
| 401 / 403 | PAT, project membership, origin — **`cosense`** `login.md` |
| 409 `DuplicateTitle` | `readPage` on conflicting title; user chooses append vs new title |
| 409 `NotFastForward` | Page changed since preview — `readPage` and new `previewEdit` |

Report status and error names only (no tokens). On success, hand back **page title** and public URL pattern (no secrets).

## What not to use

- Scrapbox import API, curl, jq pipelines, `/tmp/import.json`
- `@cosense/std`, Deno, `deno run -A`
- Browser cookie `COSENSE_SID` (replaced by **`COSENSE_PAT`** + CLI)
