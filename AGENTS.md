# AGENTS.md

## Cursor Cloud specific instructions

This repository is **not** a runnable app, backend, or web service. It is an
[APM (Agent Package Manager)](https://microsoft.github.io/apm/) package that
distributes **Agent Skills** (`skills/<name>/SKILL.md`) and **instruction rules**
(`.apm/instructions/*.instructions.md`). There are no servers, ports, build
steps, or automated test suites. "Running" this product means using the `apm`
CLI to install/deploy its skills and rules into a consumer repo.

### Tooling

- The only tool needed is the **APM CLI** (installed by the startup update
  script to `/usr/local/bin/apm`). Verify with `apm --version`.
- `apm doctor` runs environment diagnostics (git, network, auth). A GitHub token
  is auto-detected from the environment; the `takak2166/.github-private` policy
  warning is harmless (no org policy repo exists).

### Validate / "lint" this package

There is no linter. Validation happens through APM itself:

- `apm install <local-path> --target cursor` validates and deploys a package;
  APM validates package structure during install.
- `apm audit` (run inside a consumer repo after install) scans deployed
  primitives for hidden Unicode / drift and reports issues. This is the closest
  thing to a lint/integrity check.

### Run end-to-end (deploy skills + rules into a consumer)

Install commands must specify a target harness when multiple (or none) are
detected, otherwise `apm install` exits asking you to pin one. Use
`--target cursor` (or `claude`, etc.):

```bash
# Deploy the whole package (rules -> .cursor/rules/, skills -> .agents/skills/)
mkdir -p /tmp/consumer && cd /tmp/consumer && git init -q
apm install /workspace --target cursor

# Or a single skill by local path
apm install /workspace/skills/draft-pr --target cursor
```

Expected result of the root install: 5 rules integrated into `.cursor/rules/`
and 13 skills integrated into `.agents/skills/`.

### Gotchas

- Prefer installing from the **local path** (`/workspace`) to test the current
  working tree. `apm install takak2166/agent` pulls the published GitHub version
  instead, not your local edits.
- The root `apm.yml` has empty `dependencies.apm`, so running `apm install`
  *inside* `/workspace` does nothing useful (and needs a target). This repo is a
  package to be *consumed*, not one that installs its own deps.
- APM deploys skills to `.agents/skills/` (shared) and rules to per-harness dirs
  like `.cursor/rules/*.mdc` / `.claude/rules/`.
