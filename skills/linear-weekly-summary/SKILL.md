---
name: linear-weekly-summary
description: Generates a weekly Linear summary (completed, started, and newly created Issues, highlights, and Projects needing schedule or Status Update attention) and posts it to a configured webhook.
disable-model-invocation: true
---

# Linear Weekly Summary

Aggregate last week's Linear activity, build a Markdown report in the **Japanese output template**, and notify a **webhook**.

## Non-negotiables

1. **Read-only on Linear** — Do **not** create or update Issues, Projects, or Status Updates (report only).
2. **Format fidelity** — **`Read`** [`reference/output-template.md`](reference/output-template.md) before composing the report. Follow its headings, tables, emoji, and section breaks. The rendered report body is **Japanese**. Exception only when the user explicitly requests a different format.
3. **Webhook required** — After generating the report, **POST to the webhook** (see §Webhook). If the URL is unset, **do not run** `post-webhook.sh` (it exits 1); skip POST, return the Markdown in chat, and tell the user how to configure `LINEAR_WEEKLY_SUMMARY_WEBHOOK_URL`. Skip POST when the user asks for preview only (see Workflow §5).
4. **State the period** — Put the aggregation window (JST) in the title line. User-provided dates take precedence.

## Prerequisites and tools

- **Linear MCP** (`plugin-linear-linear`). Call **`GetMcpTools`** first; if status is `needsAuth`, call **`mcp_auth`** then retry. Read each tool descriptor before calling.
- Primary tools:
  - **`list_teams`** — resolve team
  - **`list_issues`** — collect Issues (`fields` for required columns, `cursor` for paging)
  - **`list_projects`** — list Projects (`fields`: `targetDate`, `status`, `url`, etc.)
  - **`get_project`** — per-Project detail when needed
  - **`get_status_updates`** — Project Status Updates (`type: "project"` required)
  - **`get_workspace`** — optional workspace URL prefix
- **`list_issues` / `list_projects` `limit`**: start at 25–50. On complexity errors, **lower `limit`** or narrow with **`team` / `query`**. If `hasNextPage`, fetch more with **`cursor`**.
- Date filters: MCP `createdAt` / `updatedAt` accept **ISO-8601 durations** (e.g. `-P14D`) or dates. If there is **no server-side filter for `completedAt` / `startedAt`**, fetch a wider set and **filter client-side** by period.

## Webhook

| Setting | Description |
|---------|-------------|
| `LINEAR_WEEKLY_SUMMARY_WEBHOOK_URL` | POST target (required). Slack Incoming Webhook, Discord Webhook, etc. |
| `LINEAR_WEEKLY_SUMMARY_WEBHOOK_FORMAT` | Optional. `slack` (default) / `discord` / `raw` |

**POST steps** (run from repo/workspace root; adjust path if skill is vendored elsewhere):

```bash
bash skills/linear-weekly-summary/scripts/post-webhook.sh /tmp/linear-weekly-summary.md
```

- The script **executes** the POST (do not merely read it as reference).
- If the user provides a webhook URL in the message, pass it as the **second argument** (overrides the env var for that run).
- After a successful POST, reply in chat with a **short confirmation** (period, counts, webhook sent). Omit the full report unless the user asks.

## Defaults (personal me-time / TAK only)

Apply the table below **only if all** of these hold:

1. The user **does not** specify which **team** belongs to this run (no team name, no `/team/...` URL, no team UUID).
2. At least one holds: context references **`me-time`**, **`TAK`**, or `linear.app/me-time/...`; **or** `list_teams` yields **exactly one** obvious match for personal planning and the user confirms.
3. You are **not** in an unknown or multi-org context where assuming a single team would be unsafe.

When the gate applies and the user gives no stronger instruction:

| Item | Default |
|------|---------|
| Team | `Takayuki's time` (confirm via `list_teams`) |
| Week boundary | **Sun 00:00 JST – Sat 23:59 JST** (title end date shows the following Sunday, e.g. `07/26 〜 08/02`) |
| Stale Update threshold | **7+ days** since last Status Update |
| Schedule alerts | overdue target, missing target date, Project/Issue status mismatch, target within 21 days with atRisk/offTrack |

Outside the gate (other org / explicit team) → resolve team with **`list_teams`** and user input. If the user gives no week rule, **ISO Mon–Sun** is acceptable—**do not mention which rule was used in the report** (title dates only).

## Workflow

### 1. Determine the aggregation period

1. User gives `YYYY-MM-DD` range or 「先週」 → interpret **start and end (JST, inclusive)**.
2. No explicit range → **previous Sun 00:00 – Sat 23:59 JST** when Defaults gate applies; otherwise **previous Mon 00:00 – Sun 23:59 JST**.
3. Keep ISO timestamps internally. Display dates as **`MM/DD`** (include year in the title when crossing years).

### 2. Collect Linear data

**Resolve team** → `list_teams` (Defaults or user-specified).

**Issues (in period)** — combine `list_issues` calls; page with `cursor` as needed:

| Section | Rule | Fetch strategy |
|---------|------|----------------|
| Completed | `completedAt` in period | `state: Done`, `updatedAt: -P21D` (approx.) + `fields`: `id`, `title`, `url`, `completedAt`, `project`, `priority`, `labels` → filter by period |
| Started | `startedAt` in period | `updatedAt: -P21D` + `fields` including `startedAt` → filter by period. Issues may appear in both Completed and Started |
| New | `createdAt` in period | `createdAt` from period start (duration) or broad fetch → filter by period |

**Projects** — `list_projects` (`team` filter, `fields`: `name`, `url`, `status`, `targetDate`, `startDate`, `completedAt`, `updatedAt`).

**Status Updates** — per Project: `get_status_updates` (`type: "project"`, `project: <name|id>`, `limit: 1`, `orderBy: "createdAt"`) for the latest update. Count updates **in the aggregation period** via `get_status_updates` with `createdAt` set to a duration from period start (or `-P7D` when period is one week).

**Status mismatch** — Projects in Backlog/Planned with In Progress Issues active in the period (`list_issues` + `project` filter).

### 3. Build the report

1. **`Read`** [`reference/output-template.md`](reference/output-template.md).
2. Fill sections per that file (Japanese output):
   - **Title** — `## 📊 Linear 週次サマリ（<start> 〜 <end>）`
   - **Completed Issues** — count + table; sort by `completedAt` ascending when practical
   - **Started Issues** — bullet list
   - **New Issues** — count + **group by project/theme** (bulk creation may use ranges, e.g. `TAK-108〜119`)
   - **Highlights** — 3–5 bullets (synthesis allowed; do not invent facts)
   - **Schedule / Update attention** — **only matching Projects**; omit entire subsections when none apply
   - Footnote when applicable: `> 先週中の Project Status Update: **N件**`
3. Use MCP `url` fields as-is for links. Emoji: overdue 🔴, needs review 🟡.

### 4. Send webhook

Skip this section when the webhook URL is unset (env and user message) or the user requested preview only.

1. Save Markdown to `/tmp/linear-weekly-summary.md` or similar.
2. Run `bash skills/linear-weekly-summary/scripts/post-webhook.sh /tmp/linear-weekly-summary.md` (pass URL as 2nd arg if user provided one).
3. On failure: report the error in chat and return the full Markdown.

### 5. Chat response

- Webhook success: 2–4 lines with period, section counts, and destination host (mask tokens).
- **Preview only** or explicit “do not send webhook” → skip §4; return or show the Markdown in chat.

## Integrated example (median path)

**User:** `/linear-weekly-summary` (me-time context; `LINEAR_WEEKLY_SUMMARY_WEBHOOK_URL` set)

1. Defaults gate applies → team `Takayuki's time` via `list_teams`
2. Period → previous Sun–Sat JST; title e.g. `2026/07/26 〜 08/02`
3. `GetMcpTools` → Linear MCP ready (auth if needed)
4. `list_issues` / `list_projects` / per-Project `get_status_updates` → filter by period
5. `Read` `reference/output-template.md` → compose Japanese report
6. Save `/tmp/linear-weekly-summary.md` → `post-webhook.sh` → short chat confirmation

**User:** `先週のサマリ、プレビューのみ` → same steps 1–5; **skip** step 6 POST; return Markdown in chat.

## Usage

```text
/linear-weekly-summary
```

Trigger phrases (attach or invoke this skill explicitly):

- `先週の Linear サマリを Webhook に送って`
- `2026-07-26 から 2026-08-02 の週次サマリ`
- `今週の Update が必要な Project も含めてサマリ`

## Additional resources

- Output template (Japanese, verbatim): [`reference/output-template.md`](reference/output-template.md)
- Webhook POST script: [`scripts/post-webhook.sh`](scripts/post-webhook.sh)
- Linear MCP descriptors: `list_issues`, `list_projects`, `get_status_updates`, `get_project`, `list_teams`
