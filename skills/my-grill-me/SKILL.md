---
name: my-grill-me
description: Relentless design-tree interview of a plan or decision. Asks every unblocked frontier question through the runtime structured-question tool and does not implement until the user explicitly asks.
disable-model-invocation: true
---

# My Grill Me

A skill to stress-test a plan, decision, or idea through structured questioning until you share one design.

Interview the user until you share one design. Do not implement the subject of the interview during this skill.

## Usage

```
/my-grill-me
```

Run only when this skill is explicitly attached or the user invokes `/my-grill-me`. If the same turn also asks to implement something, grill first and do not implement.

The interview **subject** is the plan, decision, or idea in the user's message. If none is given, ask once via the question tool what to stress-test, then begin the design tree.

## Non-negotiables

1. **No action until asked** — do not implement, edit, or otherwise act on the plan until the frontier is empty, the user confirmed shared understanding, **and** they later asked to implement.
2. **Decisions vs facts** — decisions are the user's. Facts are yours: look them up (tools / sub-agents). Never ask the user for something you can find.
3. **Design tree** — every decision branches into the decisions that hang off it. A question that depends on another question still open in this logical round belongs to a later round.
4. **Structured questions first** — deliver every frontier question through the runtime question tool when it exists.
5. **Lookups do not stall the rest** — an in-flight fact lookup only blocks questions that depend on it. Ask the rest of the frontier now.

## Expected output

**Each logical round (in order):**

1. Short **settled decisions** list (bullets).
2. One or more structured-question tool calls covering the full frontier (batched only when the tool caps questions per call).
3. No implementation, edits, or action on the interview subject.

**Session end (frontier empty):**

1. Summary of all settled decisions.
2. One confirmation question via the question tool (or markdown fallback) with exactly two choices: shared understanding reached, or holes remain. Do **not** offer implement.
3. Stop and wait.

## Design tree

Work in **logical rounds**. The **frontier** is every decision whose prerequisites are already settled.

Each user answer reshapes the tree: settled decisions push the frontier outward. Recompute the frontier only after **every** question from the current logical round has an answer (including all tool-limit batches).

Session is done when the frontier is empty and the user confirms shared understanding.

## Question delivery

Preference order:

1. Cursor `AskQuestion` when that tool exists
2. Claude `AskUserQuestion` when that tool exists
3. Markdown fallback below

Ask in the **conversation language**. Default to single-select. Use multi-select only when the decision is a set.

Do **not** add an Other option; the host already provides one.

**Recommended answer:** put it first. Tag the label `(推奨)` when the conversation is Japanese, `(Recommended)` when it is English.

If a decision is not naturally closed, still invent at least two honest options. Freeform goes through host Other.

**After Other / freeform:** accept it in chat. If the boundary is still unclear, resettle that decision in the **next** logical round. Do not immediately fire a replacement form unless the answer was empty.

**Logical round = the full current frontier.** If the tool caps questions per call, split into sequential calls. Do not recompute the tree until that frontier is fully answered.

Each round: follow **Expected output** above.

### Cursor `AskQuestion`

- One call may include the entire frontier (no question cap).
- Option count may exceed 4.
- Set `title` to the grill round (for example `Grill round 2`).
- Each question needs stable `id`, `prompt`, and `options` (`id`, `label`). Set `allow_multiple` only for set decisions.
- Put the recommended tag on the first option's label.

### Claude `AskUserQuestion`

- 1–4 questions per call, 2–4 options each. `header` ≤ 12 characters.
- Each option needs `label` + `description` (rationale / recommendation note goes in `description`).
- Collapse to 4 options; leftover candidates go through Other.
- Not available in subagents — ask from the parent agent only.
- Same logical round: issue another call for leftover frontier questions after the previous call returns.

### Markdown fallback

Use only when neither structured-question tool exists:

```
❓ **Q1** - **<title>**: <body, including choices>

➡️ <recommended answer>
```

## Session end

When the frontier is empty:

1. Summarize settled decisions.
2. Ask via the question tool (or markdown fallback): **Shared understanding reached?** with options **Yes — we agree** and **No — holes remain** (localized to the conversation language). Do **not** offer implement.
3. Stop.

If they report holes, recompute the frontier and continue. Implement only on a later explicit request.

## Restrictions

- Do not implement or edit the subject of the interview while this skill is running.
- Do not ask the user for look-up-able facts.
- Do not recompute the design tree mid-round.
- Do not add a duplicate Other option.
- Do not start this workflow from ambient chat unless the skill was explicitly attached or `/my-grill-me` was used.
