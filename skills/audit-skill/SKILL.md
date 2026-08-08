---
name: audit-skill
description: Audits and fixes agent SKILL.md files for discovery, scope, clarity, structure, context efficiency (~500-line cap), and execution safety. Auto-applies edits for Critical and Major issues; reports Minor as suggestions only.
disable-model-invocation: true
---

# Audit Skill

Follow **Non-negotiables**, **Restrictions**, **Steps**, and **Audit Output** below.

**Role:** Act as a strict but constructive skill-design auditor who fixes Critical and Major defects in the target skill.

## Severity → action (do not omit)

| Severity / mode | Action |
|-----------------|--------|
| Critical | Auto-fix in target skill directory |
| Major | Auto-fix in target skill directory |
| Minor | **Findings** only with **Suggested fix:** — **do not edit** |
| `--audit-only` | No edits; Critical/Major → **Findings** with **Suggested fix:** |
| Missing path | Ask for path; **stop** — no full audit output template |
| Unresolvable target | Path given but not found after search; tell user and **stop** — no full audit output template |

## Non-negotiables

Apply items 1–6 below **only when composing the full Audit Output** (after Steps resolve a readable target). For **Missing path** (Steps §1), **not-a-skill** early exit (Steps §2), or **unresolvable target** stop (Steps §3 after search still no readable path), ask or clarify and **stop**—do not emit **## Changes Applied** / **## Findings** / **## Strengths**, do not run the checklist, read `reference.md` for output templates, read `/tmp/{skill-name}/*`, or edit files. Item 2 applies only on the full-output path.

Confirm all of the following before composing the final reply:

1. **Read** the target `SKILL.md` and every linked supporting file (`reference.md`, `examples.md`, `scripts/*`) the main skill references.
2. **Read** [`reference.md`](reference.md) in **this audit-skill directory** (output templates, separators, worked examples—not the target skill's `reference.md`, unless auditing this package).
3. **Fix** Critical and Major issues in the target skill directory only; report Minor as suggestions—**do not edit for Minor**.
4. **Output** sections in this order: **## Changes Applied** → **## Findings** → **## Strengths**.
5. **Ground** every finding and edit in text you actually read; do not infer undocumented behavior.
6. **Do not** create git commits unless the user explicitly asks.

## Success criteria

When the full Audit Output applies, the reply includes **## Changes Applied**, **## Findings**, and **## Strengths** with field labels from **Audit Output**; severities match **Steps**. Default to one audit pass; re-audit only when the user asks to repeat until only Minor findings remain. For targets with `disable-model-invocation: true`, evaluate `description` for factual WHAT accuracy only—do not Major-fix absent discovery WHEN.

## Restrictions

- **Scope edits to the target skill:** You may edit only files in the target skill directory (for example `SKILL.md`, `reference.md`, `examples.md`, and files under `scripts/` when the fix requires it). Use `Read` / `ReadFile`, `Glob`, and `Grep` / ripgrep (`rg`) (or equivalents) to inspect; use file-edit tools only within that directory. Do not modify unrelated workspace files.
- **Fix vs suggest by severity:** Apply fixes for **Critical** and **Major** findings directly in the target skill files. Report **Minor** findings as suggestions only—do not edit for Minor.
- **When not to auto-fix:** Do not edit when evidence is insufficient, the full file was not readable, the fix requires product or scope decisions you cannot infer, or the user explicitly asked for audit-only. Report those Critical/Major items under **## Findings** with **Suggested fix:** instead.
- **Evidence-based work:** Ground every finding and every edit in text you actually read. When something was not read, is missing, or is unclear, state that plainly; do not infer undocumented behavior or rewrite intent you cannot verify.
- **Preserve intentional design:** Keep user-specified verbatim wording, explicit constraints, and `disable-model-invocation` choices unless the finding requires changing them to resolve a defect.
- **No commits:** Do not create git commits unless the user explicitly asks.

## Usage

```
/audit-skill [path to SKILL.md or skill directory]
```

Accept a path relative to the workspace root, a path to `SKILL.md`, or a skill directory. Some clients pass `@`-style references; resolve them to a real path before existence checks.

Example invocations (`disable-model-invocation` is true; attach or run the skill explicitly):

- `/audit-skill @skills/draft-pr` or `/audit-skill path/to/SKILL.md`
- `/audit-skill @skills/draft-pr --audit-only` — report Critical/Major under **## Findings** with **Suggested fix:**; do not edit target files (see **When not to auto-fix** in **Restrictions**)

Resolve the target and follow **Steps** (constraints above apply to the whole workflow). For a full path-to-reply walkthrough, see the integrated example in [`reference.md`](reference.md).

## Steps

Cross-references **Steps §1–§3** mean the **first three items** in this list (missing path; not a skill document; resolve target—including unresolvable stop).

1. If no path is provided, or the path is empty or whitespace-only, ask the user for the target skill directory or `SKILL.md` path and stop.
1. If the user asks you to audit content that is clearly not a skill document (for example application source with no skill intent, or a topic unrelated to agent skills), reply briefly that this workflow audits skill documents, and ask for a path to `SKILL.md` or a skill directory—or stop if they clarify.
1. Resolve the target:
   - If the argument is a directory, audit `<directory>/SKILL.md`
   - If the argument is a file, treat that file as the skill document to audit (the basename does not need to be `SKILL.md`)
   - If the resolved path does not exist, or the file cannot be read as text, or the argument is too vague to map to a single path: use `Glob` / `Grep` (read-only codebase search) to identify candidate paths; choose one clear match or ask the user; if you then have an existing readable target, continue; otherwise tell the user and stop
1. Read the target skill file with `Read` (`ReadFile` in some clients). Note the approximate line count from the read output (for example the highest line number shown). If only a partial view is available (client truncation or huge file), audit what you can see and record a validation-gap item under **## Findings** (typically **Major**); do not auto-fix unseen content.
1. If the target lives under a parent directory that groups multiple skills (for example `.../skills/<skill-name>/SKILL.md`):
   - Use `Glob` on that parent to list sibling `SKILL.md` paths (for example `*/SKILL.md`).
   - When at least one sibling exists besides the target, `Read` at least one sibling far enough to compare frontmatter (`name`, `description`) and top-level heading structure; read more siblings only when needed for the audit.
   - Use this comparison only to flag material divergence from nearby skills (for example inconsistent `description` tone or top-level heading patterns) as a Major or Minor finding when it would affect discovery or maintenance; if the target aligns with sibling conventions, do not add a finding solely because siblings were read. **Do not use sibling alignment to downgrade or skip checklist-driven Critical or Major items** (for example missing WHEN in `description` stays Major for auto-discovered skills even when a sibling shares the same gap; for targets with `disable-model-invocation: true`, WHAT-only `description` is acceptable per checklist row 1).
   - If there is no such parent or no sibling exists, skip this step.
   - Do not load every skill in the repository unless the user asks for a repo-wide audit
1. If the main skill links directly to one-level-deep supporting files such as `reference.md`, `examples.md`, or `scripts/*`, read them with `Read` (use `Glob` or `Grep` / ripgrep (`rg`) to locate paths when needed). Validate claims in the main skill **and** audit those files with the same checklist where applicable (the ~500-line cap applies to `SKILL.md` only). Fix Critical/Major issues in supporting files per **Restrictions**.
1. Audit the target skill package—the primary `SKILL.md` plus any linked supporting files read in the prior step—using the checklist below in priority order. Apply each row to the file under review; for supporting files without YAML frontmatter, skip **Discovery and scope** and any bullet that requires frontmatter.

   | Priority | Category | Key checks |
   |----------|----------|------------|
   | 1 | Discovery and scope | `name` ≤64 chars, lowercase, hyphenated; `description` states WHAT + WHEN in third person (WHAT-only acceptable when `disable-model-invocation: true`); narrow scope; `disable-model-invocation` matches side-effect vs reference intent |
   | 2 | Structure | YAML frontmatter + Markdown body; not under reserved dirs; headings readable; ~500-line `SKILL.md` cap with progressive disclosure to linked files |
   | 3 | Instruction quality | Ordered steps; constraints near top; freedom level matches fragility; one default + escape hatch; no contradictions; preserve verbatim user wording |
   | 4 | Output and examples | Explicit response structure when needed; concrete separated examples; validation loops for quality-critical workflows |
   | 5 | Tooling and safety | Named tools/commands; forward-slash paths; execute vs read for scripts; restrictions align with steps; workflow feasible |
   | 6 | Context efficiency | No redundant agent-common knowledge; rules near top; progressive disclosure; frontmatter within discovery limits (~1024 chars Cursor / ~1536 Claude Code) |
   | 7 | Authoring anti-patterns | **Minor** only: dated deprecations missing, many equivalent tools with no default, duplicate examples |

   When a row is ambiguous, apply the expanded bullet list in [`reference.md`](reference.md) **Audit checklist (expanded)**.

   **Severity definitions:**
   - `Critical`: likely wrong behavior, unsafe behavior, or failed execution
   - `Major`: materially harms discovery, clarity, maintainability, or audit quality
   - `Minor`: consistency, wording, or optional improvements

1. Apply fixes for **Critical** and **Major** findings (Critical first):
   - Edit target skill files with the client's file-edit tools (`StrReplace`, `Write`, or equivalents).
   - Prefer minimal diffs: fix the defect without unrelated refactors.
   - When a Major length issue requires moving content, create or update linked `reference.md` / `examples.md` in the same directory and trim `SKILL.md`; keep links one level deep.
   - After edits, re-read changed files when needed to confirm the fix.
   - Skip auto-fix for any item covered by **When not to auto-fix** in **Restrictions**; leave those for **## Findings**.
1. If the user explicitly asked to repeat until only Minor findings remain (or equivalent): when this pass fixed any Critical or Major issue, re-read the changed target files and repeat from the supporting-files step through **Apply fixes** (checklist, severity assignment, and edits); stop when a full pass finds no new Critical or Major issues to fix.
1. Compose the final reply per **Audit Output** below and [`reference.md`](reference.md).

## Audit Output

Requirements here win over [`reference.md`](reference.md) if anything conflicts.

**Does not apply** on Missing path, not-a-skill, or unresolvable-target early exits (Steps §1–§3)—reply with a brief ask or report, then stop.

- **Section order:** **## Changes Applied** → **## Findings** → **## Strengths** (mandatory on the full-output path).
- **Templates and examples:** Use [`reference.md`](reference.md) for copy-paste Markdown templates, empty-section wording, multi-item separators, and worked examples—**read it before writing the reply**.
- **## Changes Applied:** Critical/Major items you fixed. Subsections `### Critical` / `### Major` only when non-empty. If none fixed: **No Critical or Major issues; no edits made.** If audit-only with unresolved Critical/Major: **No edits made.** (one line). Each item: **Affected section:**, **Problem:**, **Why it matters:**, **Fix applied:** (name file + brief change).
- **## Findings:** Minor suggestions and Critical/Major items not auto-fixed. Each item: **Affected section:**, **Problem:**, **Why it matters:**, **Suggested fix:**. If none: **No Minor findings.**
- **Uncertainty:** Insufficient evidence → do not auto-fix; report under **## Findings** with **cannot determine** / **cannot judge** wording.
- **Separators:** Between items in the same subsection, use **`Finding 2`**, **`Finding 3`**, … or `---`—do not mix both styles.
- **## Strengths:** 2–5 bullets; quote short snippets when grounding claims.
- **Optional prefill:** If the client allows steering the first tokens, prefill with `## Changes Applied` only (no item content)—**full-output path only**; never on early exits (Steps §1–§3).

## Notes

- Full templates, integrated workflow example, and expanded checklist live in [`reference.md`](reference.md).
- Maintainer eval run history is **local only** at `/tmp/{skill-name}/BENCHMARKS.md` (for this skill: `/tmp/audit-skill/BENCHMARKS.md`). Use the target skill's frontmatter `name` as `{skill-name}`. **Do not read during normal audits**; create or append only after `/empirical-prompt-tuning` or maintainer spot-checks.
- Optional eval fixtures for maintainer spot-checks live under `/tmp/{skill-name}/fixtures/` (for this skill: `/tmp/audit-skill/fixtures/`). **Do not read during normal audits**; use only when running empirical evals—not as audit targets unless the user explicitly points there.
- **Restrictions** before **Usage** and **Steps** is intentional—edit-scope and fix-vs-suggest rules must be visible early.
- After auditing, invoke **`/empirical-prompt-tuning`** explicitly when measured iteration or release hardening is needed; append results to `/tmp/{skill-name}/BENCHMARKS.md`.
