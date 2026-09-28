---
name: init-agents
description: Scaffolds or refreshes lean AGENTS.md (and optionally CLAUDE.md) with project-specific gotchas and non-default commands only—not language, deps, or standard install/test/lint the tree already shows. Runs only when the user explicitly asks.
disable-model-invocation: true
---

# Init agents context

Create or update **hand-authored** project agent context from the template in this skill. Shared always-on policy stays in APM instructions / rules — this skill fills **project-specific** sections only.

## Non-negotiables

1. **Explicit trigger only** — run when the user invokes `/init-agents`, `--with-claude`, or clearly asks to scaffold / fill `AGENTS.md` or `CLAUDE.md`. Ambiguous "docs?" → confirm first.
2. **No silent scaffolding** — do not create files solely because they are missing; do not add always-on rules that auto-scaffold.
3. **Non-derivable content only** — do not paste primary language, dependency lists, standard install/run/test/lint, or a full directory map. Include custom commands and layout notes only when evidenced and non-obvious; omit empty sections (no `[lint]` placeholders).

## Usage

```text
/init-agents
/init-agents --with-claude
```

Also trigger when the user clearly asks to scaffold / create / fill `AGENTS.md` or `CLAUDE.md` for the current repo.

## Steps

1. **Confirm intent** — If the request is ambiguous (e.g. only “docs?”), ask whether to scaffold agent guidelines. Do **not** create files solely because they are missing.
2. **Read skeleton template** — `Read` [`reference/agents-template.md`](reference/agents-template.md). Paths are under **this** skill directory; if the link does not resolve, try `skills/init-agents/reference/` or `.cursor/skills/init-agents/reference/`.
3. **Inspect the repo** — From the project root, `Read` / `Glob` for **non-derivable** facts only (shared rules and manifests already cover the rest):
   - **Project-specific context:** README / CONTRIBUTING quirks only when purpose or scope is not obvious from the repo name and tree; skip language and dependency inventory
   - **Commands (non-default only):** Makefile targets, `package.json` scripts, or docs that name **wrappers or custom workflows** (e.g. `./scripts/…`, monorepo root commands, non-standard test entrypoints)—not plain `npm install`, `go test ./...`, or `cargo test` when the manifest is visible
   - **Conventions & gotchas:** non-default conventions, pitfalls, safety ordering, or tooling choices that differ from ecosystem defaults (evidence in README, CONTRIBUTING, or existing `AGENTS.md` bullets)
   - **Layout notes:** top-level dirs **only** when the role is not obvious from the name (legacy boundaries, generated trees, unusual monorepo splits)—omit a standard `src/` / `cmd/` map
   Prefer omitting a section over guessing. When refreshing a substantial file, migrate old Overview / Commands / Architecture content: drop derivable lines; keep or move non-obvious bullets into the matching new section.
4. **Shared-rules check** — Shared rules = non-empty `.cursor/rules/`, `.claude/rules/`, or project `.apm/instructions/` that already carry always-on policy (e.g. language / review). Record detected: yes/no. If **no**, `Read` [`reference/optional-core-sections.md`](reference/optional-core-sections.md) (same path fallbacks as Step 2).
5. **Write `AGENTS.md`** at the repo root from `agents-template.md` only as the skeleton:
   - **Empty/thin (rewrite):** missing; **or** only headings/placeholders/`TODO`/`[To be determined]` with ≤~15 non-blank lines of real project facts.
   - **Substantial:** update in place — use the template section order; migrate legacy **Project Overview** / **Commands** / **Architecture** into the lean sections (drop derivable lines; preserve user-specific gotchas and custom commands); do not wipe non-derivable bullets without asking.
   - Fill from repo facts; leave `[brackets]` only when unknown and tell the user.
   - **Layout notes** lists non-obvious path boundaries only — not manifests, not `.cursor/rules/`, not config-as-architecture filler.
   - **Omit empty sections** when a section has nothing non-derivable to say.
   - **Do not copy template HTML comments** into `AGENTS.md`; they guide the operator only.
   - **Never paste operator notes** into the file (do not copy skill prose, “when shared rules…”, or “if the user asks for self-contained…” into `AGENTS.md`).
   - **If shared rules = yes:** omit Core Principles and Maintenance Notes (they live in rules).
   - **If shared rules = no:** append the short sections from `optional-core-sections.md` (default; do not wait for a “self-contained” ask).
   - Line budget: instruction body ~30–50 non-blank non-HTML-comment lines; whole file ≤~75 lines including blanks.
6. **`CLAUDE.md`** — Only if the user asked for Claude / `--with-claude`, or `CLAUDE.md` already exists and they asked to refresh agent guidelines:
   - Prefer a **short pointer** to `AGENTS.md` (avoid dual maintenance) unless they insist on a full duplicate.
   - Pointer form: one heading + `Follow AGENTS.md.`
7. **Report** — Tell the user:
   - Paths written (or none)
   - Placeholders left (`[bracket]` items, if any)
   - Shared rules detected: yes/no; optional core sections appended: yes/no

## Restrictions

- Do **not** run `apm compile` or overwrite APM-generated markers as part of this skill.
- Do **not** add an always-on Cursor/Claude **rule** that auto-scaffolds on missing files.
- Do **not** invent commands, or paste standard stack defaults, when manifests/Makefile/README already expose them.
- Do **not** expand the template with large essays, emojis, or dashboard-style section sprawl.
