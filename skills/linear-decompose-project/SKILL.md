---
name: linear-decompose-project
description: Decomposes requirements and ADRs into milestone-linked Linear Issues at one-PR-per-Issue granularity; Devin review on ubuntu24 worker; user approval before linear-create-issue. Standalone or product-kickoff step 6. Never creates Issues before user OK.
disable-model-invocation: true
---

# Decompose project into Linear Issues

Turn **requirements** + **ADRs** into a **draft Issue breakdown** mapped to **Linear milestones**, run **Devin** review on **ubuntu24**, revise, get **user approval**, then create Issues with **`linear-create-issue`** only.

## Standalone invocation

Works without **`product-kickoff`**. If inputs are missing, **ask in one batch**:

- Linear **Project** (URL or id)
- **Milestone** names (from user or `list_milestones`)
- **Requirements** doc title or pasted 7-section summary
- **ADR** ids/titles (and one-line decision each)
- Optional: team, default priority/state

Do not create Issues until the user approves the final table (step 4 below).

## Prerequisites

- **Linear MCP** — `get_project`, `list_milestones`, `list_issues` (duplicate context only).
- **`linear-create-issue`** — read and follow for **each** Issue after approval (no bulk `save_issue` bypass).
- **Inputs** — as above.

## Restrictions

1. **No Issue create before user OK** — no `save_issue` create, no **`linear-create-issue`**, until explicit approval of the final breakdown table.
2. **Granularity** — **one Issue = one PR’s worth of work** (mergeable in a single draft PR; completable in one review cycle). Split epics; do not bundle unrelated FRs. Spikes get their own Issue when they are separate PRs.
3. **Milestone link** — every row maps to a **milestone name** from the Project (or user-approved `Unassigned` exception).
4. **No Devin on cloud VM** — Devin CLI only on a self-hosted worker with **`machineDisplayName` `ubuntu24`**. If unavailable, ask the user to run Devin on ubuntu24 and paste output.
5. **No secrets** in Devin prompts.
6. **Do not embed** Linear issue keys in committed repo files.

## Integrated example

**User:** `/linear-decompose-project` — Project URL, 3 milestones, pasted requirements summary, ADR-001/002 titles.

1. Draft table: each row = **one PR** (e.g. “Add auth API routes”, not “Build auth”).
2. Devin on **ubuntu24** reviews granularity → revise table.
3. User OK → **`linear-create-issue`** per row with milestone name.

## Workflow

**Checklist:**

```
- [ ] Project + milestones + requirements + ADRs loaded
- [ ] Draft table: one Issue = one PR; every row has milestone
- [ ] Devin review on ubuntu24 (or documented skip)
- [ ] User approved final table
- [ ] linear-create-issue per row only after OK
```

### 1. Load context

Resolve **Project** and **`list_milestones`**. Load requirements + ADR content from user paste or storage (when credentialed and asked).

### 2. Draft breakdown

| # | Issue title | Milestone | Team (if not default) | Priority | Notes / AC summary |
|---|-------------|-----------|------------------------|----------|-------------------|

Rules:

- **One row = one PR** — title must name a single shippable increment mergeable as **one draft PR** (e.g. “Add login API endpoint”, not “Build entire auth”). Split until each row is one review cycle. **Epic-sized titles** in the user input must be **split in the draft table** before Devin/user review — do not leave a single “build everything” row unless the user explicitly limits scope to one PR.
- Every row has a **milestone** (name from step 1).
- Actionable titles; 1–2 line acceptance hint (full body via **`linear-create-issue`**).

### 3. Devin review (ubuntu24)

Non-interactive on **ubuntu24** only. **Never** embed user-provided requirements or ADR text inside a double-quoted shell string (injection risk). Write the full prompt to a private temp file, then pass it to Devin without shell interpolation of the file contents.

```bash
PROMPT_FILE=$(mktemp)
trap 'rm -f "$PROMPT_FILE"' EXIT
# Write PROMPT body with the agent/editor (not: echo "$VAR" or devin -p "$VAR").
# Devin CLI: --prompt-file loads the initial prompt; combine with -p for print mode.
devin -p --prompt-file "$PROMPT_FILE" --model swe-2-max
```

Follow-up (new prompt file or reuse after rewriting the same path):

```bash
devin -c -p --prompt-file "$PROMPT_FILE"
```

If `devin --help` on the worker shows a different file flag, use that instead of `--prompt-file` — still use `mktemp`, no inline quoted prompt, and `trap` cleanup.

**PROMPT** includes: goal, milestones, draft table, requirements/ADR summaries; ask to check **PR-sized granularity**, missing work, dependencies, milestone fit. Review only — no Issue creation.

Apply reasonable edits to the table. If Devin skipped, note caveat before user review.

### 4. User confirmation (required)

Present revised table + Devin summary. Explicit approval to create **N** Issues.

### 5. Create Issues

For each approved row, run **`linear-create-issue`** (title, team, project, milestone per MCP schema, description from [`linear-create-issue/reference/issue-description.md`](../linear-create-issue/reference/issue-description.md)). If milestone cannot be set via MCP, **Milestone:** line in description + tell user to link in UI.

### 6. Report

Created count, Issue URLs, milestone mapping, manual follow-ups.

## Usage

```text
/linear-decompose-project
```

Provide Project, milestones, requirements + ADR references.

## Additional resources

- Issue creation: **`linear-create-issue`**
- Parent: **`product-kickoff`**
