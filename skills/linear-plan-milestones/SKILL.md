---
name: linear-plan-milestones
description: Plans and creates Linear Project milestones (name, completion criteria, target date) via Linear MCP after user confirms order and dates. Use when kicking off a product, scheduling a Linear Project, or when the user runs /linear-plan-milestones. Does not create Projects (linear-create-project) or Issues (linear-create-issue).
---

# Plan Linear milestones

Add **milestones** to an **existing** Linear Project. Names, **completion criteria** (in `description`), **target dates**, and **order** are agreed with the user **before** any `save_milestone` create.

## Prerequisites and tools

- **Linear MCP** — read descriptors for **`get_project`**, **`list_milestones`**, **`save_milestone`** before calling.
- **`save_milestone` create** (no `id`): requires **`project`** and **`name`**; optional **`description`**, **`targetDate`** (ISO date; `null` removes).
- **`save_milestone` update** (`id` set): use when the user explicitly asks to change an existing milestone.

## Restrictions

- **No Project create** — resolve the Project first (`get_project`, URL, name, or slug). For new Projects use **`linear-create-project`**.
- **No Issue create** — use **`linear-create-issue`** or **`linear-decompose-project`**.
- **No silent dates** — do not invent `targetDate` or milestone order; confirm with the user (question tool when available).
- **No duplicates** — `list_milestones` for the Project; skip or update only when the user asks.
- **Do not embed** Linear issue IDs or internal-only tracker URLs in skill edits or committed repo files (chat/report URLs to the user is fine).

## Workflow

### 1. Resolve Project

- From user input: Project URL, name, slug, or ID.
- **`get_project`** when needed. Record **Project HTTPS URL** and identifier used in `save_milestone` **`project`** field (per descriptor).

### 2. Gather milestone candidates

From user notes, Cosense links, or chat:

| Field | Source |
|-------|--------|
| `name` | Short, unique within the Project |
| Completion criteria | Bullet list → `description` (Markdown) |
| `targetDate` | User-confirmed ISO date or “none” |

Propose **3–7 milestones** typical for a new product (e.g. discovery, MVP, beta, GA) only as a **draft list** — not as created milestones.

### 3. User confirmation (required)

Confirm in one round (or sequential questions if the tool limits batch size):

1. Milestone **names** and **order** (first → last).
2. **Target date** per milestone (or explicitly “no date”).
3. **Completion criteria** per milestone (one-liner each is enough for confirmation; expand in `description` on create).

Do not call **`save_milestone` create** until the user approves the table.

### 4. Check existing milestones

- **`list_milestones`** with the resolved **`project`**.
- If a **same or same-intent name** exists: stop create; return existing milestone info and ask whether to **update** (`save_milestone` with `id`) or rename.

### 5. Create milestones

For each approved row **in order**:

- **`save_milestone`**: `project`, `name`, `description` (criteria + optional links to storage docs), `targetDate` when set.
- Use **literal newlines** in Markdown `description`.

### 6. Report

Return a table: milestone name, target date, and how criteria were recorded. Include Project URL. List any skipped duplicates.

## Usage

```text
/linear-plan-milestones
```

Provide a Linear **Project** reference and rough schedule themes. Run after **`linear-create-project`** when the Project already exists.

## Additional resources

- Project creation: **`linear-create-project`** (this skill does not create Projects).
- Parent workflow: **`product-kickoff`**.
