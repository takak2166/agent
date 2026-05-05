---
name: linear-create-issue
description: Creates well-structured Linear Issues from chat requests, notes, URLs, or backlog ideas via the Linear MCP. Resolves teams safely, avoids duplicates, and fills Markdown descriptions from templates; supports parent/sub-issue creation when referenced by id. Use when the user asks to issue-ize work, create Linear Issues, sub-issues under a parent, turn Scrapbox/Cosense notes into tasks, define issue templates, or manage me-time/TAK-style personal planning, or when the user runs /linear-create-issue.
---

# Create Linear Issues

Create **Linear Issues** with consistent fields and a reusable description template.

## Prerequisites and tools

- Use the **Linear MCP** (for example `plugin-linear-linear`). Before calling tools, read each tool’s **descriptor (JSON schema)** and match arguments to it.
- Primary tools: **`list_teams`**, **`list_issues`**, **`get_issue`**, **`save_issue`**, **`get_project`** (when resolving a Project URL or name).
- **`get_issue`**: the accepted `id` format (issue key vs internal id vs URL) is **not** defined in this skill—confirm in the tool **descriptor** before calling; never assume a full Issue URL is valid.
- `save_issue` **`description`** is **Markdown**. Pass **literal newlines and characters**—do not rely on escape sequences when the MCP requires real newlines.
- Issue 本文の Markdown テンプレート（**日本語**）は **`reference/issue-description.md`**。**Workflow §4** で読む。

## Restrictions

- **Honor the user’s workspace and team** (infer team key from URLs like `https://linear.app/<workspace>/team/<key>/...`, including views such as `all` or `active`). Use the **first path segment after `/team/`** as the **candidate team key** to match in `list_teams` (do not treat later path segments as team keys). Use team name, key, or UUID from that resolution when calling `save_issue`. If unclear, confirm with `list_teams` and the user.
- **URLs without a `/team/<segment>/` pattern:** do **not** invent a team key from other path parts—use `list_teams` and ask the user if the team is still ambiguous.
- **Issue URLs** (`.../issue/<id-or-key>/...`): do **not** infer a team key or UUID from the issue identifier prefix (e.g. treating **`DEV`** in **`DEV-42`** or **`FOO`** in **`FOO-401`** as the team key). Use `get_issue` to read the issue when needed; resolve the intended team with `list_teams` and user clarification if needed.
- **Do not create duplicates** of existing Issues when a same-title or same-intent match exists—return the existing Issue URL or ask whether to update (`save_issue` with `id`).
- **Do not set `list_issues` `limit` too high** (large workspaces can hit GraphQL complexity limits). Prefer filters **`team`**, **`project`**, and/or **`query`** with a **moderate `limit`** (e.g. start 10–25). On complexity or truncation errors, **lower `limit`** or narrow filters; use **`cursor`** for the next page when the tool returns `hasNextPage` and duplicate detection still matters.

## Defaults (personal me-time / TAK only)

Apply the table below **only if all** of these hold:

1. The user **does not** specify **which team** this Issue belongs to (no team name, no `/team/...` URL, and no team UUID). If they **do** specify a team, resolve it with **`list_teams`** and **do not use the Defaults table** to explain that choice—the table is only for **inferring `team` when the user left it unstated**.
2. At least one holds: the user or context references **`me-time`**, **`TAK`**, or a Linear URL whose host/path clearly indicates that workspace (e.g. `linear.app/me-time/...`); **or** `list_teams` with the user’s stated intent yields **exactly one** obvious match and the user confirms personal planning.
3. You are **not** in an unknown or multi-org context where assuming a single team would be unsafe—if unsure, **do not apply** these defaults; resolve team with `list_teams` / user.

If **any** of the above fails, resolve **`team`** (and **`project`** if needed) explicitly before **`save_issue` create**. Never use `Takayuki's time` by default outside that gated case.

When the gated case applies and the user gives no stronger instruction:

| Field | Default |
|-------|---------|
| Team | `Takayuki's time` |
| State | `Backlog` for ideas, `Todo` for committed near-term work |
| Priority | `3` / Medium for planned work, `0` / None for raw backlog |
| Assignee | Leave unset unless the user asks, or set `"me"` when they ask to start the issue |

Priority mapping: `urgent` = `1`, `high` = `2`, `mid` / `medium` / `normal` = `3`, `low` = `4`, `none` = `0`.

State mapping: use the workspace state names, commonly `Backlog`, `Todo`, `In Progress`, and `Done`. Treat `To Do` as `Todo`.

## Workflow

### 1. Normalize the request

- Split multiple requested tasks into **one Issue each**.
- Preserve user-provided titles, URLs, projects, due dates, priorities, and states.
- If the request is a raw idea, keep the Issue lightweight. If it is committed work, include acceptance criteria in the description template.

### 2. Resolve Linear context

- Resolve **team** per **Restrictions**; use **`list_teams`** (and **`get_issue`** when starting from an Issue URL **or when the user cites a parent issue id/key like `TEAMKEY-123` for sub-tasking—see bullet below**).
- Resolve **project** by name, ID, slug, or URL; prefer **`get_project`** for a Project URL or ambiguous names.
- **Parent / sub-issue:** If the user wants a **child issue** under a parent identifier (**no Issue URL**, e.g. `TAK-10`): do **not** infer team from the leading letters (**Restrictions** Issue-URL bullet applies to **`TAK` in `TAK-10`** the same way as `FOO`/`DEV`). **`get_issue` the parent first** (`id` shape per descriptor), derive **team** (and **`project`** if needed) from the parent or clarify with the user, then **`list_issues`** for duplicates. **`save_issue` create** may support **`parentId`** (name per descriptor)—confirm in the **`save_issue` descriptor** and pass the parent identifier the schema expects.
- Do not invent team or project when ambiguous—confirm briefly with the user.

### 3. Avoid duplicates

- Call **`list_issues`** before **`save_issue` create**. Prefer **`query`** on title keywords plus filters **`team`** and/or **`project`** when known. Follow **`list_issues` `limit` / paging** guidance in **Restrictions**.
- If **`list_issues` errors** or duplicate detection is **still incomplete** after applying those mitigations (lower `limit`, tighter filters, **`cursor`** pages), **do not `save_issue` create`**—keep narrowing or confirm with the user.
- If a close match exists, ask whether to **update** (`save_issue` with `id`) instead of creating a new Issue.

### 4. Compose the Issue

1. **`Read` [`reference/issue-description.md`](reference/issue-description.md)**（本スキル直下の **`reference/`** 内。リンクが解決できないクライアントは `skills/linear-create-issue/reference/` をたどる）。同ファイル内の表に従い、**フル** / **軽量** / 学習・読書向けの調整など、当てはまるテンプレを選ぶ。
2. Fill placeholders with the normalized request content; omit optional sections when lightweight.
3. Pass the result as `save_issue` **`description`** with **literal newlines** (see **Prerequisites and tools**).

### 5. Create or update

- **Create (`save_issue` without `id`):** `title` and `team` are **required**—always set both. Add other fields (`description`, `state`, `priority`, `project`, `dueDate`, `assignee`, `parentId` / schema equivalents) per schema.
- **Update (`save_issue` with `id`):** pass **`id`**; change only fields the user requested.
- Use **`dueDate`** for Issue-level deadlines per descriptor (ISO format).

### 6. Report completion

- Return created/updated Issue **identifiers and full HTTPS URLs**.
- Mention assumptions, skipped duplicates, or fields left unset.

## Usage

```text
/linear-create-issue
```

Provide a task idea, Scrapbox/Cosense page, URL, or list of items to turn into Linear Issues. Do **not** guess the team when unspecified—resolve per **Restrictions** and **Defaults**.

## Additional resources

- Issue 本文テンプレート（日本語、`reference/`）: [`reference/issue-description.md`](reference/issue-description.md)
- For full argument lists and filters, read the Linear MCP descriptors (e.g. `save_issue`, `list_issues`, `list_teams`, `get_issue`, `get_project`).
