# Question delivery (my-grill-me)

Preference order:

1. Cursor `AskQuestion` when that tool exists
2. Claude `AskUserQuestion` when that tool exists
3. Markdown fallback in **SKILL.md**

Ask in the **conversation language**. Default to single-select. Use multi-select only when the decision is a set.

Do **not** add an Other option; the host already provides one.

**Recommended answer:** put it first. Tag the label `(推奨)` when the conversation is Japanese, `(Recommended)` when it is English.

If a decision is not naturally closed, still invent at least two honest options. Freeform goes through host Other.

**After Other / freeform:** accept it in chat. If the boundary is still unclear, resettle that decision in the **next** logical round. Do not immediately fire a replacement form unless the answer was empty.

**Logical round = the full current preference frontier.** If the tool caps questions per call, split into sequential calls. Do not recompute the tree until that frontier is fully answered.

## Cursor `AskQuestion`

- One call may include the entire preference frontier (no question cap).
- Option count may exceed 4.
- Set `title` to the grill round (for example `Grill round 2`).
- Each question needs stable `id`, `prompt`, and `options` (`id`, `label`). Set `allow_multiple` only for set decisions.
- Put the recommended tag on the first option's label.

## Claude `AskUserQuestion`

- 1–4 questions per call, 2–4 options each. `header` ≤ 12 characters.
- Each option needs `label` + `description` (rationale / recommendation note goes in `description`).
- Collapse to 4 options; leftover candidates go through Other.
- Not available in subagents — ask from the parent agent only.
- Same logical round: issue another call for leftover frontier questions after the previous call returns.

## Markdown fallback

Use only when neither structured-question tool exists:

```
❓ **Q1** - **<title>**: <body, including choices>

➡️ <recommended answer>
```
