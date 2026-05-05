---
name: linear-create-project
description: Creates Linear Projects for personal workspace me-time / team Takayuki's time (key TAK) via the Linear MCP from goals or backlog notes. Uses gated defaults for that team only; otherwise resolves teams explicitly with list_teams. Use when syncing Scrapbox/Cosense wiki goals into personal Linear Projects, me-time/TAK backlog themes, bulk-creating personal PM Projects, or when the user runs /linear-create-project.
---

# Create Linear Projects

Personal PM for **`me-time`** / team **`Takayuki's time` (key **`TAK`**) unless the user **explicitly** targets another workspace or team.

When the user shares goals from Scrapbox, another wiki, or plain chat, create **Linear Projects** on the **resolved attach team** from **Workflow §2**—**Defaults** → `Takayuki's time` only when gated; otherwise the user’s explicit team only. Issue breakdown is optional unless the user asks.

## Prerequisites and tools

- Use the **Linear MCP** (e.g. `plugin-linear-linear`). Before calling tools, read each tool’s **descriptor (JSON schema)** and match `save_project` arguments to it.
- `save_project` **`description`** is **Markdown**. Pass **literal newlines and characters** in the string—do not rely on escape sequences when the MCP requires real newlines.
- 補助ドキュメント（**日本語**、`reference/` 配下）: URL 例 [`reference/url-examples.md`](reference/url-examples.md) · 任意の `description` 骨子 [`reference/description-template.md`](reference/description-template.md)（このスキルと同じディレクトリ）。

## Restrictions

- **Personal scope (`me-time` / `TAK`):** attach new Projects to **`Takayuki's time`** **only** when **`Defaults (personal me-time / TAK only)`** below applies. **Never** use that team name as a silent default in other org or unknown contexts.
- **Honor the user’s workspace and team** (infer team key from URLs like `https://linear.app/<workspace>/team/<key>/projects/...`, including views such as `all` or `active`). Use the **first path segment after `/team/`** as the **candidate team key** to match in `list_teams` (do not treat later path segments as team keys). For `addTeams`, use team name, key, or UUID from that resolution. If unclear, confirm with `list_teams`.
- **URLs without a `/team/<segment>/` pattern:** do not invent a team key from other path parts—use `list_teams` and ask the user if the team is still ambiguous.
- **Issue URLs** (`/issue/...`): do **not** infer a team key or UUID from the issue identifier prefix (e.g. treating **`DEV`** in **`DEV-42`** or **`FOO`** in **`FOO-401`** as the team key). Resolve the team with `list_teams` and user clarification if needed. **If the path includes `/team/<segment>/issue/...`, that `<segment>` is still the candidate team key** (first segment after `/team/`, same as other Linear URLs above)—only the **issue id prefix** is forbidden as a team key stand-in.
- **Do not create duplicates** of existing Projects (list matches and stop, or ask whether to merge).
- **Do not set `list_projects` `limit` too high** (large workspaces can hit GraphQL complexity limits). Prefer **filtering by team UUID** with a **small limit**, or use **`query`** to search by name.

## Defaults (personal me-time / TAK only)

Use **`Takayuki's time`** as the **only** team to attach on **`save_project` create** (via **`addTeams`** / **`setTeams`**) **only if all** of these hold:

1. The user **does not** specify **which team(s)** the Project should belong to (no team name, no `/team/...` URL, and no team UUID for attach). If they **do** specify team(s), resolve with **`list_teams`** and **do not use this Defaults section** to justify that choice—this block is only for **inferring the attach team when the user left it unstated**.
2. At least one holds: the user or context references **`me-time`**, **`TAK`**, or a Linear URL whose host/path clearly indicates that workspace (e.g. `linear.app/me-time/...`); **or** a **`list_teams`** call (see **Ordering** below and **Workflow §2** step 1) yields **exactly one** obvious match for the user’s personal-planning intent **and** the user confirms that team.
3. You are **not** in an unknown or multi-org context where assuming a single personal team would be unsafe—if unsure, **do not apply** these defaults; resolve with **`list_teams`** / the user.

**Ordering with Workflow §2:** Treat (1)–(3) as **preconditions**, not as permission to skip **`list_teams`**. When the **Defaults path** in **Workflow §2** step 1 applies, **always** run **`list_teams`** there before `addTeams`. If that call returns **multiple** plausible matches, **do not** apply Defaults to pick a team silently—disambiguate per step 1’s closing sentence. The “exactly one obvious match” clause in **2** is evaluated **after** a real **`list_teams`** round that supports it, not beforehand.

If **any** of the above fails, resolve the attach team(s) **explicitly** before **`save_project` create**. **Never** use `Takayuki's time` **outside** this gated case.

When the gated case applies and the user gives no stronger instruction:

| Field | Default |
|-------|---------|
| Attach team | `Takayuki's time` (confirm with `list_teams` before `addTeams`) |
| `lead` | `"me"` (only in this gated table; see **Workflow §4** when Defaults do not apply) |
| `priority` | `3` / Medium when the source does not emphasize urgency; otherwise map from user emphasis per Linear convention (`0`–`4`) |

## Workflow

In this skill, **`Workflow §N`** refers to subsection **`### N.`** immediately below.

### 1. Normalize input

Group source items into Projects by **whether they belong in one ongoing theme**:

- **One Project ≈ a multi-month / ongoing theme**. Put detailed components (service names, hardware) in a list inside `description`.
- If the source mentions **workflow setup** (e.g. Linear usage, prioritization) and it overlaps, **merge into one Project** when sensible.

For each Project, decide (ask briefly if missing, or infer reasonably so the user can edit later):

| Field | Content |
|-------|---------|
| `name` | Short, unique, easy to search |
| `summary` | One line, max 255 characters |
| `description` | Context, goals, first steps (Markdown headings recommended); optional skeleton in [`reference/description-template.md`](reference/description-template.md) |
| `priority` | Per Linear convention (e.g. `0` None, `1` Urgent, `2` High, `3` Medium, `4` Low); when **Defaults** apply and urgency is unstated, use the **Defaults** table |

### 2. Resolve the team

1. **Defaults path:** If **all** conditions in **Defaults (personal me-time / TAK only)** hold, the attach team is **`Takayuki's time`**. Call **`list_teams`** with a short `query` for that name/key to **confirm it exists** and to obtain the identifier used in **`list_projects`** filters and **`addTeams`** / **`setTeams`**. If **`list_teams`** returns **multiple** plausible matches, **do not** attach silently—disambiguate with the user or with an explicit team **key/UUID**.
2. **Explicit team / URL path:** If the user named a team, gave a **Team URL**, or **Defaults** do **not** apply—list teams with **`list_teams`** and resolve per **Restrictions**:
   - If the user supplied a **Team URL**, use the **candidate key** from Restrictions (the first path segment after `/team/`) to shortlist matches in `list_teams`—**do not** match on later URL segments.
   - Pick the team whose **key or name** matches that candidate (or ask for clarification if multiple teams match).
3. Never proceed to **`save_project`** create **without** at least one resolved attach team satisfying **Restrictions** and (when applicable) **Defaults**.

### 3. Check existing Projects

Before creating, use `list_projects` to avoid duplicates.

- Pass **team UUID** in the **`team`** filter when possible.
- Start with **`limit` 10–25**. On failure, switch to a **name `query`** search.
- If complexity errors persist, **lower `limit` further** (e.g. 5–10). When results come from **`query` without a reliable `team` filter**, **confirm each candidate’s team** matches the intended team before treating the list as sufficient for duplicate detection.
- If a same-name or same-intent Project exists, **do not call `save_project`**; return the existing URL.

### 4. Create the Project

Call `save_project` in **create mode** (no `id`):

- **`name`** / **`summary`**: as above.
- **`description`**: Markdown; include source URLs when available.
- **`addTeams`** or **`setTeams`**: at least **one team is required** on create. Prefer **`addTeams`** over replacing all teams. When **Defaults** apply, **`addTeams` must include `Takayuki's time`** after **`list_teams`** confirmation (Workflow §2). When the user specified other team(s), attach only those resolved teams—do not silently add `Takayuki's time` as an extra team unless they asked for multiple teams explicitly.
- **`lead`**: When **Defaults** apply and the user named no lead, prefer **`"me"`** (if the schema allows). When **Defaults** do **not** apply, **do not** default `lead` to `"me"` silently—**omit** `lead` if the descriptor allows unset, or match the field to what the user asked; if unclear and required, confirm briefly with the user.
- **`priority`**: when **Defaults** apply and the user gave none, use the **Defaults** table (Medium / `3` unless the source emphasizes urgency); otherwise derive from the emphasis in the source (Workflow §1 Linear convention `0`–`4`).

### 5. Report completion

Return **every** Linear **Project HTTPS URL**: newly created Projects, **or existing Project URLs** when you skipped create (**Workflow §3** duplicate). If you could **not** create (e.g. no resolved team yet), summarize what still blocks (`list_teams` / user input / **`limit`** / **`query`**). If an API call failed (e.g. complexity), note the retry conditions (`limit` / `team` / `query`).

## Usage

```
/linear-create-project
```

Include Scrapbox/Cosense goals, a **Linear Team URL**, or themes to file. **`Takayuki's time` is inferred only** when **Defaults (personal me-time / TAK only)** passes; otherwise resolve the attach team with **`list_teams`** (or explicit user team)—see **Restrictions** and **Defaults**.

## Additional resources

- URL 例（日本語）: [`reference/url-examples.md`](reference/url-examples.md)
- 任意の **`description`** スケルトン（日本語）: [`reference/description-template.md`](reference/description-template.md)
- For full argument lists, read the connected Linear MCP server’s tool descriptors (e.g. `save_project`, `list_projects`, `list_teams`).
