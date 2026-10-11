---
name: linear-decompose-project
description: Decomposes requirements and ADRs into a milestone-linked Linear Issue plan, reviews the draft with Devin on an ubuntu24 self-hosted worker (not the cloud VM), reflects feedback, gets user approval, then creates Issues via linear-create-issue. Never creates Issues before user OK. Use in product kickoff or /linear-decompose-project.
disable-model-invocation: true
---

# Decompose project into Linear Issues

Turn **requirements** + **ADRs** (titles or storage links from the user) into a **draft Issue breakdown** mapped to **Linear milestones**, run a **Devin** review on an **ubuntu24** worker, revise, get **user approval**, then create Issues with **`linear-create-issue`** only.

## Prerequisites

- **Linear MCP** — `get_project`, `list_milestones`, `list_issues` (duplicate check context only; do not create here).
- **`linear-create-issue`** — read and follow for **each** Issue after approval (one Issue per invocation path; no bulk `save_issue` bypass).
- **Inputs** — Linear Project URL/id; milestone names; requirements doc title; ADR ids/titles; optional priority/state defaults from user.

## Restrictions

1. **No Issue create before user OK** — no `save_issue` create, no `linear-create-issue` execution, until the user explicitly approves the final breakdown table.
2. **No Devin on cloud VM** — run Devin CLI only on a **self-hosted worker** whose `machineDisplayName` is **`ubuntu24`** (Cursor `Task` / subagent with that worker target, or user-run commands on that machine). If no worker is available, stop and ask the user to run Devin locally on ubuntu24 and paste the review output.
3. **No secrets** in Devin prompts (paste structure and titles, not `COSENSE_SID`).
4. **Do not embed** Linear issue keys in committed repo files.

## Workflow

### 1. Load context

- Resolve **Project** and **`list_milestones`**.
- User supplies requirements + ADR **titles** (and milestone mapping intent). Read storage pages only when credentials exist and user asked; otherwise use summaries the user pasted in chat.

### 2. Draft breakdown

Produce a markdown table (chat or artifact):

| # | Issue title | Milestone | Team (if not default) | Priority | Notes / AC summary |
|---|-------------|-----------|------------------------|----------|-------------------|

Rules:

- One Issue = one deliverable or one vertical slice; split large FRs.
- Every row links to a **milestone name** from step 1 (or `Unassigned` only if user allows).
- Titles are actionable (“Implement …”, “Design …”, “Spike …”).
- Include 1–2 line acceptance hint per row (full description filled in **`linear-create-issue`** step).

### 3. Devin review (ubuntu24)

On **ubuntu24** worker only, non-interactive:

```bash
devin -p "<PROMPT>" --model swe-2-max
```

Follow-up turns:

```bash
devin -c -p "<PROMPT>"
```

**PROMPT** must include: Project goal, milestone list, draft table, requirements/ADR summaries, and ask for gaps (missing work, wrong granularity, dependency order, risk). Ask Devin **not** to create Issues—review only.

Capture Devin output; apply reasonable edits to the draft table. If Devin is unreachable, document the skip and proceed to user review with that caveat.

### 4. User confirmation (required)

Present **revised table** + summary of Devin changes. Ask explicit approval to create **N** Issues on Linear.

### 5. Create Issues

For **each approved row**, run **`linear-create-issue`** workflow:

- Pass title, team, project, milestone association (per Linear MCP descriptor—`save_issue` / project fields as supported), description from [`linear-create-issue/reference/issue-description.md`](../linear-create-issue/reference/issue-description.md).
- Map milestone: use fields the schema supports (e.g. project milestone link); if MCP cannot set milestone, put milestone name in description **Milestone:** line and tell the user to link manually.

After each create, record returned Issue URL in the final report (chat only).

### 6. Report

- Count created vs skipped duplicates.
- List Issue URLs and milestone mapping.
- Note any manual follow-ups (milestone link, Devin skip).

## Usage

```text
/linear-decompose-project
```

Provide Linear Project, milestones, requirements + ADR references.

## Additional resources

- Issue creation: **`linear-create-issue`**
- Parent: **`product-kickoff`**
