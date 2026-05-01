# agent

Personal repository for agent-oriented configuration.

- **`skills/`** — [Agent Skills](https://agentskills.io) (`skills/<name>/SKILL.md`).
- **Rules** — APM [instruction primitives](https://microsoft.github.io/apm/introduction/anatomy-of-an-apm-package/) under **`.apm/instructions/`**. On `apm install takak2166/agent`, they deploy to **`.claude/rules/`**, **`.cursor/rules/`**, etc. (with `.claude/` / `.cursor/` present or an explicit `target`). See [IDE & Tool Integration](https://microsoft.github.io/apm/integrations/ide-tool-integration/).

## Repository layout

```text
apm.yml
.apm/instructions/*.instructions.md
skills/<skill-name>/SKILL.md
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

All skills: [`apm.yml.example`](./apm.yml.example).

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
