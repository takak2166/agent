---
name: linear-plan-milestones
description: Proposes Linear Project milestone plans (name, completion criteria, target date) for user confirmation, then creates or updates milestones via Linear MCP. Supports create and post-requirements/ADR review modes. Does not create Projects or Issues.
---

# Plan Linear milestones

Add or adjust **milestones** on an **existing** Linear Project. The **Bot proposes** a table (names, completion criteria, target dates, order); the **user confirms or edits** before any **`save_milestone`** create or update.

## Non-negotiables

1. **User OK before write** — no `save_milestone` until the user approves the draft table or review change set.
2. **No Project or Issue create** — use **`linear-create-project`** / **`linear-create-issue`** (or **`linear-decompose-project`**) instead.
3. **Review mode** — after requirements + ADR are settled; propose changes before any update.
4. **Standalone** — if Project or context is missing, ask the user; do not invent a Project.

## Modes

| Mode | When | Outcome |
|------|------|---------|
| **Create** (default) | After Project exists; early kickoff (step 2) | Propose draft → user OK → **`save_milestone` create** |
| **Review** | Requirements + ADR are settled; kickoff step 5 or user asks to revisit schedule | Compare milestones to reqs/ADR → propose **change set** → user OK → **`save_milestone` update** (or create only for new names) |

Activate **Review** when the user says “milestone review”, “review” / Japanese **見直し** (revisit schedule), “after ADR”, or **`product-kickoff`** step 5. If mode is unclear, ask once.

## Standalone invocation

Works without **`product-kickoff`**. Required from user when not passed from a prior step:

- Linear **Project** (URL, name, or id)
- **Create mode:** rough themes or dates (optional — Bot may propose 3–7 milestones)
- **Review mode:** requirements doc title/summary and ADR titles (or paste); existing milestones from **`list_milestones`**

## Prerequisites and tools

- **Linear MCP** — read descriptors for **`get_project`**, **`list_milestones`**, **`save_milestone`** before calling.
- **`save_milestone` create** (no `id`): requires **`project`** and **`name`**; optional **`description`**, **`targetDate`** (ISO date; `null` removes).
- **`save_milestone` update** (`id` set): use in **Review** mode after user approves each change.

## Restrictions

- **No Project create** — resolve the Project first. For new Projects use **`linear-create-project`** (do not modify that skill).
- **No Issue create** — use **`linear-create-issue`** or **`linear-decompose-project`**.
- **No silent dates or order** — Bot proposes; user confirms (question tool when available).
- **No duplicate creates** — **`list_milestones`** before create; in Review, prefer **update** over duplicate names.
- **No changes without user OK** — especially in Review mode: present the full change set before any `save_milestone` call.
- **Do not embed** Linear issue IDs in committed repo files.

## Integrated example (create mode)

**User:** `/linear-plan-milestones` for Project `https://linear.app/example/project/acme-app` — “MVP in Q2, beta Q3.”

1. **`get_project`** → resolve `acme-app`.
2. Propose table: Discovery / MVP / Beta / GA with criteria + proposed dates (labeled as proposals).
3. **Ask user** to confirm order and dates — do **not** call `save_milestone` yet.
4. User OK → **`list_milestones`** → no duplicate names.
5. **`save_milestone`** create each row in order → report table + Project URL.

## Workflow — Create mode

**Checklist (mark before `save_milestone` create):**

```
- [ ] Project resolved
- [ ] Draft table shown; user approved names, order, dates, criteria
- [ ] list_milestones — no unintended duplicates
- [ ] save_milestone create per approved row
```

### 1. Resolve Project

From user input: Project URL, name, slug, or ID. **`get_project`** when needed.

### 2. Bot proposes milestone draft

| Field | Bot fills |
|-------|-----------|
| `name` | Short, unique within the Project |
| Completion criteria | Bullets → future `description` (Markdown) |
| `targetDate` | Proposed ISO date or “none” — label as proposal |

Propose **3–7 milestones** when the user gave little detail (e.g. discovery, MVP, beta, GA). This is **not** created yet.

### 3. User confirmation (required)

User confirms or edits: **names**, **order**, **target dates**, **completion criteria** (per row). No **`save_milestone` create** until approved.

### 4. Check existing milestones

**`list_milestones`**. Same or same-intent name → stop create; ask update vs rename.

### 5. Create milestones

For each approved row in order: **`save_milestone`** create with `project`, `name`, `description`, `targetDate` as agreed.

### 6. Report

Table of created milestones + Project URL.

## Workflow — Review mode

**Checklist (mark before any `save_milestone` update/create):**

```
- [ ] Review mode confirmed (requirements + ADR inputs present)
- [ ] list_milestones current state captured
- [ ] Change-set table shown; user approved full set
- [ ] Updates/creates applied; drops only if user explicitly accepted
```

### 1. Load context

- Resolve **Project**; **`list_milestones`** (current state).
- Inputs: **requirements** (title + summary or pasted sections) and **ADR** list (ids + decision one-liners).

### 2. Bot proposes change set

Diff mentally against milestones. Output a table:

| Action | Milestone | Change (name / date / criteria) | Rationale (req or ADR) |
|--------|-----------|----------------------------------|-------------------------|
| keep / add / update / merge / drop | … | … | … |

**Drop** or **merge** only as proposals — user must explicitly accept (prefer update over delete when unsure).

### 3. User confirmation (required)

User approves the **entire change set** (or edits and re-presents). No **`save_milestone`** until approved.

### 4. Apply changes

- **update** — `save_milestone` with `id`
- **add** — create (check duplicates first)
- **drop** — only if user confirmed; if Linear has no delete in MCP, document manual cleanup and remove from plan

### 5. Report

Before/after summary; note milestones unchanged if change set was empty.

## Usage

```text
/linear-plan-milestones
/linear-plan-milestones review
```

Provide Project reference. For **review**, also provide requirements + ADR pointers or pasted summaries.

## Additional resources

- Project creation: **`linear-create-project`**
- Parent workflow: **`product-kickoff`**
