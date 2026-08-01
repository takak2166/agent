---
name: linear-advance-issue
description: Advance an existing Linear Issue through In Progress, work execution, progress comments, and Done via Linear MCP. Use only when the user explicitly names an existing Issue — Issue key (e.g. TAK-N), Issue URL, or a small explicit key list/range to advance in order — combined with progress/advance intent ("進めて", "作業ログを Issue コメントに", "アウトプットは Issue のコメントに"), or when the user runs /linear-advance-issue. Do NOT activate for vague prompts without an Issue reference ("何か進めて", "続きやって" alone), session-start Linear scans, creating new Issues (linear-create-issue), Projects (linear-create-project), weekly summaries, bulk status-only updates, or Cosense bulk issue-ization.
---

# Advance Linear Issue

Orchestrate **existing** Linear Issues: read context → start → comment progress → do the work → finish with Done when acceptance criteria are met.

## Non-negotiables (read first)

1. **Explicit Issue only** — key, URL, or explicit list/range in the **current user message**. No context inference. No Linear scan to discover a target.
2. **Never auto-pick** — if ambiguous which Issue, ask the user (even when only one In Progress exists elsewhere).
3. **Comment trail** — start comment before/at In Progress; completion comment before Done.
4. **Done gate** — mark Done only when acceptance criteria are met (research → after findings comment is posted).
5. **Advance only** — do not create Issues/Projects (`linear-create-issue` / `linear-create-project`).

## Integrated example (median path)

**User:** `TAK-122 を進めて。成果は Issue コメントに。`

1. Parse `TAK-122` from message → activate this skill
2. `GetMcpTools` → `get_issue("TAK-122")` → read AC from description
3. `save_comment` — start: plan + done definition
4. `save_issue` — state `In Progress`, assignee `"me"` (TAK defaults if applicable)
5. Do the work (e.g. edit `skills/linear-advance-issue/SKILL.md`)
6. Self-check AC → `save_comment` — complete: results + checklist (main deliverable here)
7. `save_issue` — `Done` if AC met
8. Chat: brief summary + Issue link; point to completion comment

**User:** `何か進めて` (no key/URL) → **do not activate**; reply: `Issue キーまたは URL を指定してください。`

## Prerequisites and tools

- Use **Linear MCP** (e.g. `plugin-linear-linear`). Before calling tools, read each tool's **descriptor (JSON schema)** and match arguments to it.
- Primary tools: **`get_issue`**, **`save_issue`**, **`save_comment`**, **`list_comments`**
- Optional: **`list_issues`** — only when the user explicitly asked to pick from a filtered set (rare); not for discovering an unnamed target
- `save_comment` / `save_issue` **`body`** / **`description`**: **Markdown** with **literal newlines** — do not rely on escape sequences.
- **`get_issue` `id`**: confirm accepted formats in the descriptor (identifier like `TAK-122`, internal id, or URL — never assume without checking).
- **State names** vary by workspace. Before `save_issue` with `state`, confirm valid names via the descriptor or `list_issue_statuses` if available — do not hardcode beyond common names (`In Progress`, `Done`, `Todo`, `Backlog`).

## When to activate vs skip

**Activate** only when the **current user message explicitly identifies** the target Issue:
- Issue key (`TAK-122`) or Issue URL in the message
- Small explicit list/range in the message: "TAK-37〜40まで進めて" (advance **in order**, one at a time)
- "この Issue" **only if** an Issue key or URL is attached/linked in the same message (not conversation history alone)

**Do not activate** — ask the user for an Issue key or URL instead:
- Vague advance requests with no Issue reference: "何か進めて", "続きやって", "進めて" alone
- Inferring the target from conversation context **without** a key/URL in the current message
- Session start / every-turn Linear scans (`list_projects`, broad `list_issues`)
- Creating new Issues or Projects → `linear-create-issue` / `linear-create-project`
- Weekly summary / "先週のサマリ"
- Bulk status-only changes → `linear-bulk-update` (future)

**Disambiguation — always confirm, never auto-pick:**
- Applies when the user **did** name an Issue but reference is ambiguous (e.g. two keys, unclear range).
- Ask the user which Issue — **even when only one In Progress Issue exists** in the workspace.
- Do **not** run `list_issues` to discover an unnamed target. Prompt: `Issue キーまたは URL を指定してください。`

## Restrictions

- **Advance only** — never create Issues/Projects unless the user explicitly switches to create flow.
- **Do not mark Done** unless acceptance criteria in the Issue (or user-stated done definition) are satisfied. Blockers → comment and stay **In Progress** (or ask).
- **`list_issues` `limit`**: start 5–10; lower on complexity errors. Prefer filters: `assignee`, `state`, `team`, `project`, `query`.
- **Do not set Done** on research-only Issues when the deliverable is "post findings to comment" until the comment is posted.
- **Delegate** specialized work to existing skills when present: `draft-pr`, `create-commit-en`, `ready-pr`, `plan`, etc. This skill orchestrates Linear state + comments, not every implementation detail.

## Defaults (personal me-time / TAK only)

Apply **only if all** hold (same gate as `linear-create-issue`):
1. User did not specify team and context is me-time / TAK / `linear.app/me-time/...`
2. Single obvious team from `list_teams`, or user confirms personal planning
3. Not a multi-org ambiguous context

When advancing and user asked to start work:
- **State**: Todo / Backlog → **In Progress** at start; **Done** only when complete
- **Assignee**: if unset and user asked to advance/start, set **`"me"`** on `save_issue` when schema supports it

## Workflow

### 1. Resolve target Issue(s)

- Parse Issue key, URL, or explicit small list from the **current user message** only.
- If no key/URL in the message, **stop** — ask the user to specify; do not infer from context or scan Linear.
- For a range/list (`TAK-37〜40`), resolve each identifier; advance **sequentially** (finish or pause one before starting the next unless user asked for parallel triage only).

### 2. Load context

1. `get_issue` (optionally `includeRelations: true`)
2. `list_comments` when resuming work on **this same Issue** (already In Progress or prior comments exist) — read recent comments only, not full history unless needed
3. Summarize **done definition** using this priority:
   1. Issue description acceptance criteria
   2. User instructions in the current request (e.g. "output in comment")
   3. Skill defaults (research → comment posted; code → files/PR per Issue AC)
   Git commit / PR are **not** required unless the Issue AC or user explicitly asks.

### 3. Start (visible in Linear)

1. Post **start comment**: short plan (what you will do, how you will verify done)
2. `save_issue` → state **In Progress**; set assignee `"me"` per Defaults if applicable

### 4. Execute work

- Code, docs, research, etc. per Issue content
- **Progress comments** at meaningful boundaries: phase done, blocker found, waiting on user, major finding
- If user said **アウトプットは Issue のコメントに**: put the main deliverable in the **completion comment** (not only in chat)
- If scope expands to "implementation needed" on a research Issue: do **not** create a new Issue silently — note follow-ups in the completion comment; create only if the user explicitly asks (`linear-create-issue`)

### 5. Complete or stop

**Complete:**
1. Self-check acceptance criteria
2. Post **completion comment**: summary, artifacts/links (PR, paths), remaining follow-ups
3. `save_issue` → **Done** only if criteria met

**Stop (blocker / needs user):**
1. Comment: blocker, what was tried, proposed next step
2. Leave **In Progress** unless user says otherwise
3. Do **not** mark Done

### 6. Report to user

- Brief chat summary + link to Issue
- If deliverable lives in Issue comment, say so explicitly

## Comment templates (adapt, do not copy blindly)

**Start:** plan + done definition in one short block

**Progress:** what changed since last comment

**Complete:** results + links + criteria checklist (checked items)

**Blocker:** what blocks + options for user

## Usage

```text
/linear-advance-issue
```

User must provide Issue key/URL in the message. Example: "TAK-122 を進めて。成果は Issue コメントに。"

## Additional resources

- Issue description template (for reading acceptance sections): `skills/linear-create-issue/reference/issue-description.md`
- For tool arguments, read Linear MCP descriptors (`get_issue`, `save_issue`, `save_comment`, `list_issues`).
