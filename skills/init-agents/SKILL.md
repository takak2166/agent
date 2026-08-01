---
name: init-agents
description: Scaffold or refresh project-local AGENTS.md (and optionally CLAUDE.md) from a lean template when the user explicitly asks. Use when setting up agent guidelines, AGENTS.md/CLAUDE.md is missing or a thin stub, or the user runs /init-agents. Do not invent a file unprompted.
disable-model-invocation: true
---

# Init agents context

Create or update **hand-authored** project agent context from the template in this skill. Shared always-on policy stays in APM instructions / rules — this skill fills **project-specific** sections only.

## Non-negotiables

1. **Explicit trigger only** — run when the user invokes `/init-agents`, `--with-claude`, or clearly asks to scaffold / fill `AGENTS.md` or `CLAUDE.md`. Ambiguous "docs?" → confirm first.
2. **No silent scaffolding** — do not create files solely because they are missing; do not add always-on rules that auto-scaffold.
3. **Evidence-based Commands** — install/run/test/lint from manifest, Makefile, or README; omit unevidenced lines (no `[lint]` placeholders).

## Usage

```text
/init-agents
/init-agents --with-claude
```

Also trigger when the user clearly asks to scaffold / create / fill `AGENTS.md` or `CLAUDE.md` for the current repo.

## Steps

1. **Confirm intent** — If the request is ambiguous (e.g. only “docs?”), ask whether to scaffold agent guidelines. Do **not** create files solely because they are missing.
2. **Read skeleton template** — `Read` [`reference/agents-template.md`](reference/agents-template.md). Paths are under **this** skill directory; if the link does not resolve, try `skills/init-agents/reference/` or `.cursor/skills/init-agents/reference/`.
3. **Inspect the repo** — From the project root, `Read` / `Glob` enough to fill Overview / Commands / Architecture:
   - **Overview:** README opening (project type one-liner); primary manifest (`package.json`, `pyproject.toml`, `go.mod`, …) for language + key deps
   - **Commands:** evidenced install/run/test/lint from manifest scripts, Makefile, or README — do not invent. Language-default commands (e.g. `poetry install` when `[tool.poetry]` exists, `go test ./...` / `cargo test` when the matching manifest exists) count as evidenced; omit lint/format lines entirely when no script/Makefile/README/CI names them (e.g. do not add `cargo clippy` unless evidenced).
   - **Architecture:** top-level **source** dirs only (`src/`, `cmd/`, `internal/`, …) with one-line roles
   Prefer facts from the tree over guessing.
4. **Shared-rules check** — Shared rules = non-empty `.cursor/rules/`, `.claude/rules/`, or project `.apm/instructions/` that already carry always-on policy (e.g. language / review). Record detected: yes/no. If **no**, `Read` [`reference/optional-core-sections.md`](reference/optional-core-sections.md) (same path fallbacks as Step 2).
5. **Write `AGENTS.md`** at the repo root from `agents-template.md` only as the skeleton:
   - **Empty/thin (rewrite):** missing; **or** only headings/placeholders/`TODO`/`[To be determined]` with ≤~15 non-blank lines of real project facts.
   - **Substantial:** update in place — keep section order; refresh Overview / Commands / Architecture; preserve existing user bullets (including freeform bullets under Architecture); do not wipe user-specific content without asking.
   - Fill from repo facts; leave `[brackets]` only when unknown and tell the user.
   - **Architecture** lists source/layout paths and roles only — not `package.json`, not `.cursor/rules/`, not other config-as-architecture filler.
   - **Never paste operator notes** into the file (do not copy skill prose, “when shared rules…”, or “if the user asks for self-contained…” into `AGENTS.md`).
   - **If shared rules = yes:** omit Core Principles and Maintenance Notes (they live in rules).
   - **If shared rules = no:** append the short sections from `optional-core-sections.md` (default; do not wait for a “self-contained” ask).
   - Line budget: instruction body ~30–50 non-blank non-HTML-comment lines; whole file ≤~75 lines including blanks.
6. **`CLAUDE.md`** — Only if the user asked for Claude / `--with-claude`, or `CLAUDE.md` already exists and they asked to refresh agent guidelines:
   - Prefer a **short pointer** to `AGENTS.md` (avoid dual maintenance) unless they insist on a full duplicate.
   - Pointer form: one heading + `Follow AGENTS.md.`
7. **Report** — Paths written; inferred vs placeholder; shared-rules yes/no and whether optional core sections were appended.

## Restrictions

- Do **not** run `apm compile` or overwrite APM-generated markers as part of this skill.
- Do **not** add an always-on Cursor/Claude **rule** that auto-scaffolds on missing files.
- Do **not** invent install/test commands that are not evidenced by manifests, Makefile, or README.
- Do **not** expand the template with large essays, emojis, or dashboard-style section sprawl.
