# Question delivery (my-grill-me)

Preference order:

1. Cursor `AskQuestion` when that tool exists
2. Claude `AskUserQuestion` when that tool exists
3. Grok Bot question widget when that tool exists
4. Markdown fallback in **this file** (see **Markdown fallback** below)

Ask in the **conversation language**. Default to single-select. Use multi-select only when the decision is a set.

## Free-text / Other

| Channel | Built-in free text? | What to do |
|---------|---------------------|------------|
| Cursor `AskQuestion` | Yes (host "Other") | Do **not** add a duplicate free-text option |
| Claude `AskUserQuestion` | Yes (host "Other") | Do **not** add a duplicate free-text option |
| Grok Bot question widget | Only when `allowCustom: true` | Always set `allowCustom: true`; do **not** add a duplicate free-text option in the option list |
| Markdown fallback | No | Always include an explicit **Other / free text** option |

If a decision is not naturally closed, still invent at least two honest structured options. Freeform answers go through the host's built-in free-text field, or through the markdown **Other / free text** option.

**After Other / freeform:** accept it in chat. If the boundary is still unclear, resettle that decision in the **next** logical round. Do not immediately fire a replacement form unless the answer was empty.

**Logical round = the full current preference frontier.** If the tool caps questions per call, split into sequential calls. Do not recompute the tree until that frontier is fully answered.

## Option descriptions (all channels)

Every structured option needs a one-line description: what happens if the user chooses it, plus brief pros and cons.

**Recommended answer:** put it first. Tag the label `(推奨)` when the conversation is Japanese, `(Recommended)` when it is English.

| Channel | Where the description goes |
|---------|------------------------------|
| Claude `AskUserQuestion` | `description` on each option |
| Cursor `AskQuestion` | Append to `label`: `label — <description>` |
| Grok Bot question widget | Append to label text: `label — <description>` |
| Markdown fallback | Append after the choice line: `label — <description>` |

## Cursor `AskQuestion`

- One call may include the entire preference frontier (no question cap).
- Option count may exceed 4.
- Set `title` to the grill round (for example `Grill round 2`).
- Each question needs stable `id`, `prompt`, and `options` (`id`, `label` with embedded description). Set `allow_multiple` only for set decisions.
- Put the recommended tag on the first option's label (before the ` — ` description suffix).
- Do not add a duplicate free-text option; the host provides one.

## Claude `AskUserQuestion`

- 1–4 questions per call, 2–4 options each. `header` ≤ 12 characters.
- Each option needs `label` + `description` (one line: outcome if chosen + pros/cons; put the recommendation note in `description` when useful).
- Collapse to 4 options; leftover candidates go through host Other / free text.
- Not available in subagents — ask from the parent agent only.
- Same logical round: issue another call for leftover frontier questions after the previous call returns.
- Do not add a duplicate free-text option; the host provides one.

## Grok Bot question widget

- Set `allowCustom: true` on every question.
- Append descriptions to each option label: `label — <description>`.
- Put the recommended tag on the first option's label (before the ` — ` description suffix).
- Do not list a separate free-text option; `allowCustom` covers it.

## Markdown fallback

Use only when none of the structured-question tools above exist:

```
❓ **Q1** - **<title>**: <body>

- **A** — <what happens if chosen; pros/cons>
- **B** — <what happens if chosen; pros/cons>
- **Other / free text** — State your own answer in chat instead of picking A or B.

➡️ <recommended answer>
```

Every listed option (including **Other / free text**) must carry its one-line description.