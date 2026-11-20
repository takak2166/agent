# agent

Personal repository for agent-oriented configuration.

- **`skills/`** — [Agent Skills](https://agentskills.io) (`skills/<name>/SKILL.md`).
- **Rules** — APM [instruction primitives](https://microsoft.github.io/apm/introduction/anatomy-of-an-apm-package/) under **`.apm/instructions/`**. On `apm install takak2166/agent`, they deploy to **`.claude/rules/`**, **`.cursor/rules/`**, etc. (with `.claude/` / `.cursor/` present or an explicit `target`). See [IDE & Tool Integration](https://microsoft.github.io/apm/integrations/ide-tool-integration/).
  - Omit `applyTo` for rules that must be in context from session start: Claude Code loads `.claude/rules/*.md` without `paths:` at launch, while any `applyTo` (even `**/*`) becomes `paths:` and loads only after Claude reads a matching file. In Cursor, an instruction without `applyTo` becomes a description-only rule (the agent decides when to apply it). Keep `applyTo` only for rules scoped to specific files.

## Repository layout

```text
apm.yml
.apm/instructions/*.instructions.md
skills/<skill-name>/SKILL.md
packages/cursor-always-on-rules/   # Cursor-only sessionStart hook package
```

## Install skills (APM)

In a consumer repo with **`apm.yml`** at its root:

```bash
apm install takak2166/agent/skills/draft-pr
```

Or list skills under `dependencies.apm` and run **`apm install`**.

**`apm.yml` example** (one skill):

```yaml
name: my-project
version: 1.0.0
dependencies:
  apm:
    - takak2166/agent/skills/draft-pr
```

All skills: [`apm.yml.example`](./apm.yml.example). For post-session skill/rule updates, use **`/my-reflect`** (`skills/my-reflect/`) — aligned with this package's instruction hygiene; do not duplicate [pstack's upstream reflect](https://github.com/cursor/plugins/blob/main/pstack/skills/reflect/SKILL.md).

## Install rules (APM)

Rules ship as this repo’s **APM package** (root `apm.yml` + `.apm/instructions/`). Install the repo root, **not** a `skills/…` path:

```bash
apm install takak2166/agent
```

**User-wide (e.g. under `~/.claude/`):** `apm install -g takak2166/agent` — installs into APM’s user-level targets instead of the current project. See [Global user-scope installation](https://microsoft.github.io/apm/guides/dependencies/#global-user-scope-installation).

Add to your consumer **`apm.yml`**:

```yaml
dependencies:
  apm:
    - takak2166/agent
```

Ensure the runtimes you use exist (e.g. `mkdir -p .claude .cursor`) or use `apm install --target claude` / `target:` in `apm.yml` so APM creates them—same behavior as other APM packages. See [`apm.yml.example`](./apm.yml.example) (includes `takak2166/agent` alongside skills).

### How always-on rules reach each harness

| Harness | Mechanism |
|---------|-----------|
| Claude Code | `~/.claude/rules/*.md` without `paths:` load at launch (instructions without `applyTo`). |
| Cursor (IDE / CLI) | APM turns instructions without `applyTo` into description-only `.mdc` rules, so they are not guaranteed in context. The **`packages/cursor-always-on-rules`** package adds a **`SessionStart`** hook (APM renames to Cursor’s native `sessionStart` on install; see [APM hooks](https://microsoft.github.io/apm/producer/author-primitives/hooks-and-commands/)) that merges user-scope and project always-on rules from `.claude/rules/*.md` (skipping `paths:`) and returns them as `additional_context`. |
| Copilot | Instructions without `applyTo` are not scope-attached; APM folds them into compiled root context (`AGENTS.md` / `copilot-instructions.md`) at `apm compile` time rather than as a per-glob `.github/instructions/` rule ([APM instructions](https://microsoft.github.io/apm/producer/author-primitives/instructions-and-agents/)). Scoped instructions still deploy as `.github/instructions/*.instructions.md` with `applyTo`. |
| Codex | `apm compile -g` writes the instructions without `applyTo` into `~/.codex/AGENTS.md`. |

Install the hook package next to the root package (**user scope** with `apm install -g`, with `claude` and `cursor` among the targets):

```yaml
dependencies:
  apm:
    - takak2166/agent
    - takak2166/agent/packages/cursor-always-on-rules
```

Notes:

- The hook package declares `target: cursor`. APM refuses to install one package's hooks to both Claude and Cursor (Cursor can import Claude hooks, so they could run twice), which is why the hook is not in the root package.
- Prefer **`apm install -g`** for the root package and hook so rules land under `~/.claude/rules/`. **Project-scoped** `apm install` adds path-scoped rules under `<project>/.claude/rules`; the hook always merges user-scope always-on rules first, then appends project always-on rules (same basename: home wins).
- The `claude` target must be installed. Rule files are assumed **APM-generated** `.md` with standard `paths:` frontmatter; the hook skips files that declare `paths:` in the leading block.
- The hook answers only Cursor input (`cursor_version`), once per `session_id`, and prints nothing otherwise. Set `APM_ALWAYS_ON_RULES_DEBUG=1` to log skip reasons on stderr.
- Session stamps live under `${XDG_RUNTIME_DIR:-$HOME/.cache}/apm-always-on-rules-stamps/`; entries older than seven days are removed best-effort on each run.
- JSON is built with `jq`, falling back to `python3` if `jq` is missing or fails; with neither usable, the hook does nothing. Without `jq`, hook input fields are parsed with a whitespace-tolerant `sed` fallback.
- Cursor runs `sessionStart` only for a new chat. A resumed chat (`--resume`) keeps the context from its first start, but does not pick up rule changes made since.
- Cursor does **not** natively load project `.claude/rules/*.md` (it uses `.cursor/rules/*.mdc` and root `AGENTS.md` / `CLAUDE.md`; see [Cursor Rules](https://cursor.com/docs/context/rules)). This hook is the bridge for APM’s Claude-shaped rule tree, so project always-on rules are not expected to double-inject via a separate Cursor loader.
