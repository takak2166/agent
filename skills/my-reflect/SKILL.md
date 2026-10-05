---
name: my-reflect
description: Extracts durable lessons from a finished agent session (transcript or current chat), triages them through Judgment / Tooling / Divergent lenses and a synthesizer, and applies only user-approved updates to Skills or always-on instructions. Routes enforceable fixes to backlog instead of prose.
disable-model-invocation: true
---

# My Reflect

Turn **what this session taught** into **durable agent environment changes**—without bloating Skills with one-off notes or duplicating what lint and scripts should enforce.

**Upstream:** Cursor pstack ships a heavier [`reflect`](https://github.com/cursor/plugins/blob/main/pstack/skills/reflect/SKILL.md) (parallel Task subagents, bundled reviewer prompts, per-role models via `pstack-models.mdc` from `/setup-pstack`). **This skill** is the package-local variant inspired by pstack [Chapter 33](https://zenn.dev/sc30gsw/books/7ff701b9811d04/viewer/7c5f9e): same Judgment / Tooling / Divergent → synthesize → approve → apply shape, but **structure-first routing** follows always-on **instruction hygiene** (`.apm/instructions/instruction-hygiene.instructions.md`), not pstack's separate `principle-encode-lessons-in-structure`. Large skill fixes route to **`audit-skill`** / **`skill-hardening-loop`**. Do **not** also install `cursor/plugins/pstack/skills/reflect`—pick `takak2166/agent/skills/my-reflect` when you depend on this package.

## Usage

```
/my-reflect
```

Run only when the user explicitly invokes `/my-reflect` or asks to reflect on the session's lessons.

Infer **destinations** (skills, `.apm/instructions/`, or Backlog) from evidence in the session—do not require the user to name a target skill up front.

## When to run (and when to stop)

**Run** after work that **taught something**—corrections, surprises, repeated friction, or unclear skill behavior.

**Stop immediately** (brief reply, no reviewers) when any of these hold:

| Condition | Why |
|-----------|-----|
| Conversation was trivial or mostly off-topic | No durable lesson |
| Agent followed an existing skill correctly end-to-end | Skill is already sufficient evidence |
| User only wants a human summary with no repo changes | Not this skill's job |
| Single skill is clearly at fault and user already named it | Prefer **`/skill-hardening-loop`** or **`/audit-skill`** on that target |

Do **not** treat a one-time coincidence as a rule. Prefer **Backlog** or **Rejected** over weak Accepted items.

## Non-negotiables

1. **User approval before edits** — show the full synthesizer result; apply file changes only to items the user explicitly approves.
2. **Encode in structure first** — if a lesson can be a lint rule, script, metadata flag, or runtime check, put it in **Backlog** (Linear issue or equivalent), not Skill prose. Align with always-on **instruction hygiene** in this package.
3. **Scope edits** — Skills: only under the approved skill directory. Rules: only under `.apm/instructions/` (or the consumer's deployed rules path when reflecting in another repo). Do not drive unrelated application code changes during reflect.
4. **Evidence required** — every Accepted candidate cites a concrete moment (user correction, failed command, wrong assumption).
5. **No git commits** unless the user explicitly asks.
6. **Do not auto-invoke** — this skill never runs from ambient chat; the user must attach or name it.

## Relationship to other skills

| Situation | Use instead |
|-----------|-------------|
| One skill misfired; target path known | **`skill-hardening-loop`** or **`audit-skill`** |
| Need checklist audit, not session narrative | **`audit-skill`** |
| Lesson is "run verify X before saying done" | Consumer repo rule or verification skill—not a paragraph in reflect output |

Reflect fills the gap when **lessons span multiple skills/rules** or the **right destination is unclear** until after review.

## Steps

Copy and mark progress:

```
Reflect:
- [ ] Step 0 — eligibility (or stop)
- [ ] Step 1 — transcript / session source
- [ ] Step 2 — three reviewer passes
- [ ] Step 3 — synthesize
- [ ] Step 4 — structural → Backlog
- [ ] Step 5 — present for approval
- [ ] Step 6 — apply approved edits only
- [ ] Step 7 — brief report
```

### Step 0 — Eligibility

Apply **When to run (and when to stop)**. If stopping, say why in one short paragraph.

### Step 1 — Transcript / session source

Resolve the **active session transcript** before reviewers. The system prompt names this workspace's `agent-transcripts/` directory—use **that path only**. Do not glob `~/.cursor/projects/*/` across workspaces (unrelated private chats).

```bash
ls -t <agent-transcripts>/*.jsonl <agent-transcripts>/*/*.jsonl <agent-transcripts>/*/subagents/*.jsonl 2>/dev/null | head -10
```

Three layouts: legacy flat (`<id>.jsonl`), nested (`<id>/<id>.jsonl`), subagent (`<parent>/subagents/<child>.jsonl`).

1. For each candidate (newest first), read the **first JSONL line** and check that `message.content[0].text` contains this conversation's **opening user prompt**. Use the matching file.
2. If the user named a specific session file, prefer that over recency.
3. If no file resolves, use the **current conversation** as the source and state that limitation in the final report (Step 7).

### Step 2 — Three reviewer passes

Produce candidate lessons from **three lenses** (parallel subagents when **Task** is available; otherwise three sequential passes in one run). Full lens definitions and output fields: [`reference.md`](reference.md).

Each candidate must include:

- **Principle** — one sentence that should still guide the **next** session
- **Evidence** — quote or paraphrase the triggering moment
- **Destination** — skill path, `.apm/instructions/*.instructions.md`, or **Backlog (structure)**

**Destination rule:** prefer a skill the conversation **actually used**. If a skill should have been used but was not, propose a fix in that skill—not a duplicate workflow elsewhere. For **auto-discovered** skills, tune `description` / Usage for activation. For **`disable-model-invocation: true`** destinations, change **Usage / Steps / execution clarity** only—do not add discovery WHEN or trigger lists to `description`.

### Step 3 — Synthesize

Merge candidates with the **synthesizer criteria** in [`reference.md`](reference.md). Bucket each item:

| Bucket | Meaning |
|--------|---------|
| **Accepted** | Durable, actionable, correct destination |
| **Rejected** | With one-line reason |
| **Backlog** | Enforceable by lint/script/CI or needs a human ticket |

### Step 4 — Structural → Backlog

From **Accepted**, move any item that **instruction hygiene** would encode as structure (lint, script, type, runtime check) to **Backlog**. Leave **Accepted** only with text changes that truly need judgment in prose.

For Backlog entries, draft a **one-line Linear-style title** and body bullet the user can paste into an issue tracker.

### Step 5 — Present for approval

Output **before any edits**. Keep all three subsections below; when a bucket is empty, write `- none` under that heading (do not omit the heading).

**Number every Accepted item** with `1.`, `2.`, `3.`, … (sequential integers starting at 1). The closing line tells the user to reply with those numbers—checkboxes alone are not enough.

```markdown
## Reflect — synthesizer result

### Accepted (needs your approval to apply)

1. **Principle:** …
   - **Evidence:** …
   - **Destination:** …
   - **Proposed change:** …

2. **Principle:** …
   - **Evidence:** …
   - **Destination:** …
   - **Proposed change:** …

### Backlog (structure / tickets)
- …

### Rejected
- … — reason

Reply with which Accepted items to apply (numbers, e.g. `1`, `1 and 3`, or quotes), or "none".
```

Wait for the user. Do not edit files until they approve specific items (by **number** or quoted Principle text).

### Step 6 — Apply approved edits

| Change size | Action |
|-------------|--------|
| Small (roughly ≤10 lines in one file) | Edit directly in the approved destination |
| Large (new section, heavy rewrite) | Propose outline first; if user already approved, edit or suggest **`audit-skill`** / **`skill-hardening-loop`** on that skill after reflect |
| New skill needed | Do not create silently—list as Backlog or ask user to open a dedicated task |
| Always-on rule | Add or patch one `.apm/instructions/*.instructions.md`; keep cross-cutting invariants only |

After editing any `SKILL.md`, run **`skills-ref validate <skill-dir>`** when that CLI exists; otherwise manually check frontmatter (`name`, `description`) and linked paths.

### Step 7 — Brief report

One block:

- Applied (file + one line each)
- Backlog (titles only)
- Rejected (count + top reason if any)
- Source (transcript path or "current chat")

## Integrated example

**User:** `/my-reflect` after a long session fixing `draft-pr` public-repo visibility and almost pasting a Linear URL into a public PR body.

1. **Step 0** — nontrivial corrections → continue.
2. **Step 2 — Judgment:** "Public repo PR text must not leak internal tracker URLs" → destination `skills/draft-pr/SKILL.md` (already partially covered—propose tightening Non-negotiables).
3. **Step 2 — Tooling:** "`gh repo view --json visibility` before compose" → same destination, evidence from failed assumption.
4. **Step 2 — Divergent:** Agent nearly skipped visibility check because template was read first → propose checklist order in Steps.
5. **Step 3** — both Accepted; nothing to Backlog.
6. **Step 5** — user approves item 1 only.
7. **Step 6** — edit `draft-pr` Non-negotiables only; report.

## Additional resources

- Reviewer lenses, synthesizer criteria, anti-patterns: [`reference.md`](reference.md)
