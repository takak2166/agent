---
name: publish-skill-apm
description: Publishes an APM skill dependency to dotfiles apm.yml, then commit, push main, chezmoi update, and apm install -g in one fail-fast pipeline.
disable-model-invocation: true
---

# Publish Skill via APM

Register a new APM skill dependency in chezmoi-managed dotfiles, commit, push to **main**, apply with chezmoi, and materialize globally with APM.

## Usage

```text
/publish-skill-apm <full-apm-dependency-path>
```

Example:

```text
/publish-skill-apm takak2166/agent/skills/foo
```

## Prerequisites

1. **Agent side:** The target skill is already merged and pushed to `takak2166/agent` (this skill does not verify; `apm install -g` fails fast if the dependency is unavailable).
2. **Bootstrap (first time only):** This skill itself must be registered in `dot_apm/apm.yml` manually before it can be invoked via APM. After that, use this skill for subsequent skill publishes.
3. **Chezmoi source:** Git operations run in `~/.local/share/chezmoi` on branch **main** tracking `origin/main`.

## Non-negotiables

1. **Explicit path only** — require a full APM dependency path (e.g. `takak2166/agent/skills/foo`). Do not infer from skill name alone.
2. **Fail-fast** — stop at the first failing step; report using **Fail-fast report** below.
3. **Duplicate = no-op** — if the path already exists in `dot_apm/apm.yml`, exit without commit, push, chezmoi, or apm.
4. **Stage `dot_apm/apm.yml` only** — never stage other files.
5. **Do not modify** `/create-commit-en` or `agent/apm.yml.example`.

## Fail-fast report

When any step fails, stop immediately and report:

- **Step:** step number and name (e.g. `Step 7 — Push to main`)
- **Command:** exact command attempted (if applicable)
- **Error:** stderr or exit message

Do not continue to later steps.

## Steps

All git commands run with working directory `~/.local/share/chezmoi`.

**Pipeline checklist** (mark as you go):

```
- [ ] 0. Validate input
- [ ] 1. Verify chezmoi source
- [ ] 2. Check duplicate
- [ ] 3. Append dependency
- [ ] 4. Stage
- [ ] 5. Commit
- [ ] 6. Warn on other dirty files
- [ ] 7. Push to main
- [ ] 8. chezmoi update
- [ ] 9. apm install -g
```

### 0. Validate input

- Reject if the argument is missing, empty, or not a full APM path.
- Accept format: `owner/repo` or `owner/repo/sub/path` — segments of `[A-Za-z0-9_.-]+`, separated by `/`, no leading or trailing `/`.
- Example valid: `takak2166/agent/skills/publish-skill-apm`
- Example invalid: `foo`, `/takak2166/agent/skills/foo`, `takak2166/agent/skills/foo/`
- On rejection, fail-fast with a valid path example (e.g. `takak2166/agent/skills/<name>`).

### 1. Verify chezmoi source

- Confirm `~/.local/share/chezmoi` exists and is a git repository (`git -C ~/.local/share/chezmoi rev-parse --is-inside-work-tree`).
- Confirm `dot_apm/apm.yml` exists.
- If either check fails, **stop** with fail-fast report.

### 2. Check duplicate

- Read `dot_apm/apm.yml`.
- If a line `- <path>` (exact match) already exists under `dependencies.apm`, report **already registered — no changes made** and **exit** — do not run steps 3–9.

### 3. Append dependency

- Edit `dot_apm/apm.yml` only.
- Insert one line `- <path>` in the **agent skill block**: after existing `takak2166/agent/skills/*` entries and **before** the first external repo dependency (lines that do not start with `takak2166/agent`).
- Keep YAML list indentation (4 spaces before `-`).
- Preserve a blank line before the external-repo block if one already exists.

### 4. Stage

```bash
git add dot_apm/apm.yml
```

### 5. Commit (create-commit-en equivalent)

Inline the commit logic; do **not** invoke `/create-commit-en` (different repo; full pipeline ownership).

1. Run `git diff --staged`.
   - If no diff, report and **exit**.
2. Summarize the staged diff in one concise English sentence; pick prefix from `feat` / `fix` / `chore` / `test` / `refactor` / `docs` (typically `chore` for new apm dependency).
3. Commit:

```bash
git commit -m "prefix: <Message starting with capital letter>"
```

### 6. Warn on other dirty files

- Run `git status --porcelain`.
- If files other than `dot_apm/apm.yml` are modified or untracked, **warn** the user but **continue**.

### 7. Push to main

1. Confirm current branch is `main` (`git branch --show-current`). If not, **stop** and report.
2. Push without extra confirmation:

```bash
git push origin main
```

### 8. Apply dotfiles

```bash
chezmoi update
```

### 9. Materialize globally

```bash
apm install -g
```

- `apm install` has no `--yes` flag; run as shown. If a future APM version adds a non-interactive flag for install, prefer it.

## Integrated example

**Input:** `/publish-skill-apm takak2166/agent/skills/new-skill`

**Duplicate (step 2):** `dot_apm/apm.yml` already contains `- takak2166/agent/skills/new-skill` → report **already registered — no changes made** and exit. No git commit, push, chezmoi, or apm.

**Full run (path not present):** append line in agent skill block → `git add dot_apm/apm.yml` → commit (`chore: Add new-skill to apm dependencies`) → warn if other dirty files → `git push origin main` → `chezmoi update` → `apm install -g` → success report with commit hash.

## Success report

After step 9, report:

- Added dependency path
- Commit hash (from step 5)
- Push target (`origin/main`)
- `chezmoi update` and `apm install -g` completed

## Restrictions

- Allowed commands: file read/edit for `dot_apm/apm.yml`; `git -C ~/.local/share/chezmoi rev-parse`; `git diff --staged`, `git add dot_apm/apm.yml`, `git commit -m`, `git status --porcelain`, `git branch --show-current`, `git push origin main`; `chezmoi update`; `apm install -g`.
- Do not push branches other than **main**.
- Do not run `apm update`, `apm compile`, or modify files outside the pipeline scope.
- Do not create git commits in repos other than the chezmoi source.
