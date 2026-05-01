---
name: linear-create-project
description: Creates Linear Projects from goals or backlog notes via the Linear MCP. Resolves teams, avoids duplicate Projects, and fills summary and Markdown description from the source. Use when opening Linear Projects, syncing Scrapbox/Cosense wiki goals to Linear, bulk-creating backlog Projects, me-time/TAK-style personal PM, or when the user runs /linear-create-project.
disable-model-invocation: true
---

# Create Linear Projects

When the user shares goals from Scrapbox, another wiki, or plain chat, create **Linear Projects** (not mandatory issue breakdown unless the user asks).

## Prerequisites and tools

- Use the **Linear MCP** (e.g. `plugin-linear-linear`). Before calling tools, read each tool’s **descriptor (JSON schema)** and match `save_project` arguments to it.
- `save_project` **`description`** is **Markdown**. Pass **literal newlines and characters** in the string—do not rely on escape sequences when the MCP requires real newlines.

## Restrictions

- **Honor the user’s workspace and team** (infer team key from URLs like `https://linear.app/<workspace>/team/<key>/projects/...`, including views such as `all` or `active`). Use the **first path segment after `/team/`** as the **candidate team key** to match in `list_teams` (do not treat later path segments as team keys). For `addTeams`, use team name, key, or UUID from that resolution. If unclear, confirm with `list_teams`.
- **URLs without a `/team/<segment>/` pattern:** do not invent a team key from other path parts—use `list_teams` and ask the user if the team is still ambiguous.
- **Issue URLs** (`/issue/...`): do **not** infer a team key or UUID from the issue identifier (e.g. treating `DEV` in `DEV-42` as the team key). Resolve the team with `list_teams` and user clarification if needed.
- **Do not create duplicates** of existing Projects (list matches and stop, or ask whether to merge).
- **Do not set `list_projects` `limit` too high** (large workspaces can hit GraphQL complexity limits). Prefer **filtering by team UUID** with a **small limit**, or use **`query`** to search by name.

## Workflow

### 1. Normalize input

Group source items into Projects by **whether they belong in one ongoing theme**:

- **One Project ≈ a multi-month / ongoing theme**. Put detailed components (service names, hardware) in a list inside `description`.
- If the source mentions **workflow setup** (e.g. Linear usage, prioritization) and it overlaps, **merge into one Project** when sensible.

For each Project, decide (ask briefly if missing, or infer reasonably so the user can edit later):

| Field | Content |
|-------|---------|
| `name` | Short, unique, easy to search |
| `summary` | One line, max 255 characters |
| `description` | Context, goals, first steps (Markdown headings recommended) |
| `priority` | Per Linear convention (e.g. `0` None, `1` Urgent, `2` High, `3` Medium, `4` Low) |

### 2. Resolve the team

1. List teams with `list_teams`; use `query` if provided.
2. If the user supplied a **Team URL**, use the **candidate key** from Restrictions (the first path segment after `/team/`) to shortlist matches in `list_teams`—**do not** match on later URL segments.
3. If the user had a Team page open, pick the team whose **key or name** matches that candidate (or ask for clarification if multiple teams match).

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
- **`addTeams`** or **`setTeams`**: at least **one team is required** on create. Prefer **`addTeams`** over replacing all teams.
- **`lead`**: default to `"me"` if unset (when the schema allows).
- **`priority`**: if the user gave none, set a sensible value from emphasis in the source.

### 5. Report completion

List **each created Project’s Linear URL**. If an API call failed (e.g. complexity), note the retry conditions (`limit` / `team` / `query`).

## Usage

```
/linear-create-project
```

Include Scrapbox/Cosense page content, a Linear Team URL, or a list of themes to file. Do not guess the team when unspecified—resolve with `list_teams`.

## Additional resources

- For full argument lists, read the connected Linear MCP server’s tool descriptors (e.g. `save_project`, `list_projects`, `list_teams`).
