# Audit skill — reference

Use this file when auditing a target skill. Requirements in `SKILL.md` **Audit Output** always win if anything conflicts.

## Audit checklist (expanded)

Apply in priority order. For supporting files without YAML frontmatter, skip **Discovery and scope** and bullets that require frontmatter.

### 1. Discovery and scope

- `name` is specific, lowercase, hyphenated, and not vague; **≤ 64 characters**; avoid generic names such as `helper`, `utils`, or `tools`
- `description` explains both WHAT the skill does and WHEN to use it, in **third person** (not "I can help" or "You can use"); for targets with `disable-model-invocation: true`, factual WHAT-only is acceptable—do not Major-fix absent discovery WHEN
- Trigger scenarios are specific enough for discovery
- The skill scope is narrow enough to avoid unrelated tasks
- `disable-model-invocation` matches intent when inferable: side-effect or manually timed workflows should usually set `true`; background reference knowledge may omit it—flag **Major** when the mismatch likely causes unwanted auto-invocation or blocks intended auto-discovery

### 2. Structure and maintainability

- The file uses YAML frontmatter and a Markdown body
- The skill lives in an appropriate directory when path is visible (project `skills/` or personal `~/.cursor/skills/`—not reserved dirs such as `skills-cursor/`); flag **Major** when a user-maintained skill is under a reserved path
- The main structure is readable with Markdown headings
- Markdown is the default structure for human-maintained sections
- XML is used only where strict boundaries help the model parse inputs, outputs, or examples
- The main `SKILL.md` stays concise; move long details to directly linked reference files when needed
- **`SKILL.md` length:** Treat **500 lines** as the recommended upper bound for the main file (Claude Code and Cursor authoring guidance). Count from the `Read` output. This is a soft limit—not a fail-by-default rule:
  - **Major** when the file exceeds ~500 lines and long sections, templates, or examples remain inline instead of linked reference files—or when length likely harms invocation context or maintainability
  - **Minor** when the file is roughly **300–500 lines** with blocks that clearly belong in `reference.md` / `examples.md`, or when slightly over 500 lines but progressive disclosure is already used well
  - Do not flag length alone when the file is well under 300 lines
- Terminology is consistent throughout

### 3. Instruction quality

- Steps are clear, direct, and ordered
- Important constraints appear near the top
- Instruction specificity matches task fragility: high freedom for context-dependent work; medium for preferred patterns; low (scripts, exact steps) for fragile or consistency-critical ops
- Prefer **one default approach with an explicit escape hatch** over many peer options that force discretionary choice
- Fragile rules include brief rationale when it helps correct execution
- Instructions do not contradict each other
- The skill does not mix too many unrelated objectives
- User-specified verbatim wording in the target is preserved, not paraphrased or expanded, unless a defect requires changing it

### 4. Output and examples

- Expected output or response structure is explicit when the task needs it
- Examples are concrete and clearly separated from the main instructions
- Quality-critical workflows include a validation or feedback loop when the task needs it (for example run validator → fix → rerun)
- If XML is used, it improves precision instead of adding noise

### 5. Tooling, safety, and feasibility

- Required tools or commands are named explicitly
- File paths use forward slashes (`scripts/helper.py`), not Windows-style backslashes
- If `scripts/*` is referenced, the skill states whether the agent should **execute** or **read** each script
- Restrictions do not conflict with the steps
- The workflow is executable in the intended environment
- The skill avoids dangerous, impossible, or underspecified instructions

### 6. Context efficiency

- The file avoids redundant explanation the agent likely already knows
- Important rules are near the top
- Background detail is loaded progressively instead of packed into `SKILL.md`
- Frontmatter `description` (and `when_to_use` when present) stays within discovery limits—roughly **1024 characters** for Cursor skills and **1536 characters** combined for Claude Code skill listings; flag **Major** when trigger phrases are buried or likely truncated because the text is padded

### 7. Authoring anti-patterns (Cursor `create-skill` alignment)

- **Minor** for time-sensitive instructions without a dated "old patterns" or deprecated section (for example "before August 2025, use …")
- **Minor** for listing many equivalent tools/libraries with no default
- **Minor** for duplicate examples that teach the same lesson
- Do not flag anti-patterns that are already clearly handled elsewhere in the checklist

## Integrated workflow example

User invokes `/audit-skill @skills/example-skill` (hypothetical target whose `description` lacks WHEN).

1. Resolve path → read `skills/example-skill/SKILL.md`.
2. Read sibling `skills/draft-pr/SKILL.md` frontmatter for convention comparison only.
3. Audit against checklist:
   - **Major:** `description` states WHAT but lacks explicit WHEN triggers (for example add "Use when reviewing or writing kubectl commands").
   - **Minor (optional):** body uses second person while frontmatter should stay third person.
4. Auto-fix Major: update target `description` with third-person WHAT + WHEN.
5. Read this `reference.md` for output templates.
6. Compose reply:

```markdown
## Changes Applied

### Major

- **Affected section:** frontmatter / description
- **Problem:** Description states WHAT but not WHEN with concrete trigger phrases.
- **Why it matters:** Discovery may fail when users describe the task in natural language instead of naming the skill.
- **Fix applied:** Updated `skills/example-skill/SKILL.md` `description` with a "Use when …" clause.

## Findings

**No Minor findings.**

## Strengths

- Clear, executable scope with concrete examples.
- Narrow workflow with no unrelated objectives.
```

---

# Audit output — templates and examples

Use these when composing the final response for **audit-skill**.

## Full template (fixed + suggested)

Copy only the subsections you need. Do not paste empty `### Critical` / `### Major` / `### Minor` headings.

In the actual response, **replace** every `…` placeholder with real text; do not output literal `…` as the item content.

```markdown
## Changes Applied

### Critical
- **Affected section:** …
- **Problem:** …
- **Why it matters:** …
- **Fix applied:** … (file path + brief summary)

### Major
- **Affected section:** …
- **Problem:** …
- **Why it matters:** …
- **Fix applied:** …

## Findings

### Minor
- **Affected section:** …
- **Problem:** …
- **Why it matters:** …
- **Suggested fix:** …

## Strengths
- …
```

## Empty sections

When nothing was fixed at Critical or Major severity:

```markdown
## Changes Applied

**No Critical or Major issues; no edits made.**
```

When the user requested audit-only (or another skip per **When not to auto-fix**) and Critical/Major issues were found but not edited:

```markdown
## Changes Applied

**No edits made.** User requested audit-only; Critical/Major items are reported under **## Findings** with **Suggested fix:**.
```

When there are no Minor suggestions and no unresolved Critical/Major items:

```markdown
## Findings

**No Minor findings.**
```

When the skill is clean end-to-end:

```markdown
## Changes Applied

**No Critical or Major issues; no edits made.**

## Findings

**No Minor findings.**

## Strengths
- …
```

## Multiple items in the same subsection

Within a single `### Critical`, `### Major`, or `### Minor` subsection, repeat the full field block for each item. After the first block, separate the next item from the previous one with a blank line and a bold line **`Finding 2`**; use **`Finding 3`**, **`Finding 4`**, and so on for additional items in that same subsection. The first item in a subsection does not need a **`Finding 1`** line.

Alternatively, use a horizontal rule (`---`) between consecutive field blocks instead of **`Finding N`** lines. Do not mix **`Finding N`** and horizontal rules in the same response.

## Iterative re-audit (multi-pass)

When the user asked to repeat until only Minor findings remain, compose **one** final reply after all passes finish. Each pass runs from the supporting-files step through **Apply fixes** in `SKILL.md` **Steps**. **## Changes Applied** lists every Critical/Major fix from every pass; **## Findings** holds Minor suggestions plus any Critical/Major items skipped per **When not to auto-fix** in `SKILL.md` **Restrictions**.

## Suggested fix — weak vs strong (Minor and unresolved items)

Use **Suggested fix:** to give an actionable, specific change. Avoid vague advice.

<example type="contrast" title="Weak vs strong Suggested fix">

**Weak (too vague):**

- **Suggested fix:** Improve the steps.

**Strong (specific):**

- **Suggested fix:** Pick one spelling (for example "subagent") and use it throughout the body.

</example>

## Fix applied — weak vs strong (Critical/Major auto-fix)

Use **Fix applied:** to name what changed, not to restate the problem.

<example type="contrast" title="Weak vs strong Fix applied">

**Weak (too vague):**

- **Fix applied:** Fixed the description.

**Strong (specific):**

- **Fix applied:** Updated `SKILL.md` frontmatter `description` with concrete trigger phrases and a "Use when …" clause for PR review requests.

</example>

## Few-shot examples (placeholders fully replaced)

<example type="Major" title="Major auto-fixed + Minor suggestion">

Below is a **complete** sample from **## Changes Applied** through **## Strengths**.

```markdown
## Changes Applied

### Major

- **Affected section:** frontmatter / description
- **Problem:** Trigger scenarios were vague
- **Why it matters:** The agent may not load this skill when the user needs it, or may apply it in the wrong context.
- **Fix applied:** Updated `skills/example/SKILL.md` `description` with concrete trigger phrases and a "Use when reviewing pull requests …" clause.

## Findings

### Minor

- **Affected section:** Terminology (body)
- **Problem:** The doc alternates between "sub-agent" and "subagent" for the same concept.
- **Why it matters:** Small inconsistencies make maintenance and search harder.
- **Suggested fix:** Pick one spelling (for example "subagent") and use it throughout.

## Strengths

- Frontmatter includes `name` and `description`, giving a baseline for discovery.
- The main workflow is organized with Markdown headings and numbered steps.
```

</example>

<example type="Critical" title="Critical — contradictory instructions (auto-fixed)">

```markdown
## Changes Applied

### Critical

- **Affected section:** Restrictions vs Steps
- **Problem:** **Restrictions** forbade using the shell, but **Steps** instructed running `npm test` via the terminal.
- **Why it matters:** The agent cannot follow both; execution will fail or violate safety expectations.
- **Fix applied:** Removed shell commands from **Steps** in `skills/example/SKILL.md` and replaced them with read-only verification steps that match **Restrictions**.

## Findings

**No Minor findings.**

## Strengths

- Frontmatter identifies the skill name and a clear primary use case.
```

</example>

<example type="Major" title="Major — length split (auto-fixed)">

```markdown
## Changes Applied

### Major

- **Affected section:** Structure / overall length (~620 lines)
- **Problem:** `SKILL.md` exceeded the ~500-line recommended upper bound and kept long output templates and worked examples inline.
- **Why it matters:** Invoked skill content competes for context on every turn; an oversized main file is harder to maintain.
- **Fix applied:** Moved templates and extended examples to `skills/example/reference.md`, trimmed `skills/example/SKILL.md` to workflow and constraints with one-level-deep links (~180 lines).

## Findings

**No Minor findings.**

## Strengths

- Frontmatter `description` states both WHAT and WHEN.
- Progressive disclosure now separates essentials from reference detail.
```

</example>

<example type="Minor" title="Minor — description voice (third person)">

```markdown
## Findings

### Minor

- **Affected section:** frontmatter / description
- **Problem:** The description uses second person ("You can use this to …") instead of third person.
- **Why it matters:** Descriptions are injected into system prompts; third person reads more clearly to the agent and matches Cursor authoring conventions.
- **Suggested fix:** Rewrite as third person with WHAT and WHEN, for example "Audits SKILL.md files and auto-fixes Critical/Major issues. Use when …".

## Strengths

- Frontmatter includes both `name` and `description`.
```

</example>

<example type="edge" title="Edge — partial read (not auto-fixed)">

```markdown
## Changes Applied

**No Critical or Major issues; no edits made.**

## Findings

### Major

- **Affected section:** Validation coverage
- **Problem:** Only the first portion of `SKILL.md` was visible; the rest was not available to read.
- **Why it matters:** Findings below may miss issues in the unseen portion; auto-fix was skipped to avoid rewriting unseen content.
- **Suggested fix:** Re-run the audit in an environment that returns the full file, or split the skill into a shorter `SKILL.md` plus `reference.md`.

## Strengths

- The visible section uses clear Markdown headings.
```

</example>
