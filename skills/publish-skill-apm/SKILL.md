---
name: publish-skill-apm
description: Publishes an APM skill dependency to dotfiles apm.yml, then commit, push main, chezmoi update, apm install -g, and apm compile -g in one fail-fast pipeline.
disable-model-invocation: true
---

# Publish Skill via APM

Register a new APM skill dependency in chezmoi-managed dotfiles, commit, push to **main**, apply with chezmoi, materialize globally with APM, and regenerate user-scope root context files.

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
4. **`yq` on PATH:** required for steps 2 and 2b (`dependencies.apm` membership and transitive resolution).
5. **Manual global APM (outside this pipeline):** follow `.apm/instructions/apm-global-root-context.instructions.md`.

## Non-negotiables

1. **Explicit path only** — require a full APM dependency path (e.g. `takak2166/agent/skills/foo`). Do not infer from skill name alone.
2. **Fail-fast** — stop at the first failing step; report using **Fail-fast report** below.
3. **Duplicate = no-op** — if the path already exists under **`dependencies.apm`** in `dot_apm/apm.yml` (step 2 semantics; other keys such as `dependencies.discussed` do not count), exit without commit, push, chezmoi, or apm.
4. **Stage `dot_apm/apm.yml` only** — never stage other files.
5. **Do not modify** `/create-commit-en` or `apm.yml.example` in the `takak2166/agent` repository.

## Fail-fast report

When any step fails, stop immediately and report:

- **Step:** step number and name (e.g. `Step 7 — Push to main`)
- **Command:** exact command attempted (if applicable)
- **Error:** stderr, non-zero exit summary, or the compile/output lines that triggered failure
- **Affected paths:** (step 10 only) each target path named in a failing `skipped` / `retained` / `error` line

Do not continue to later steps.

## Integrated example

**Input:** `/publish-skill-apm takak2166/agent/skills/new-skill`

**Duplicate (step 2):** `dot_apm/apm.yml` already lists the path under `dependencies.apm` → report **already registered — no changes made** and exit. No git commit, push, chezmoi, or apm.

**Full run (per-skill manifest, path not present):** append line in agent skill block → `git add dot_apm/apm.yml` → commit (`chore: Add new-skill to apm dependencies`) → warn if other dirty files → `git push origin main` → `chezmoi update` → `apm install -g` → `apm compile -g` (capture, classify, list `wrote` paths) → success report with commit hash.

**Root-only manifest (only `takak2166/agent`, no `takak2166/agent/skills/*` lines):** for `takak2166/agent/skills/hybrid-skill`, append only missing **transitive** deps from that skill's `apm.yml`; if none, skip 3–7 → `chezmoi update` → `apm install -g` → `apm compile -g` → success report with **no commit/push** (see **Success report**).

## Steps

All git commands run with working directory `~/.local/share/chezmoi`.

**Pipeline checklist** (mark as you go):

```
- [ ] 0. Validate input
- [ ] 1. Verify chezmoi source
- [ ] 2. Check duplicate
- [ ] 2b. Root-package layout (if applicable)
- [ ] 3. Append dependency
- [ ] 4. Stage
- [ ] 5. Commit
- [ ] 6. Warn on other dirty files
- [ ] 7. Push to main
- [ ] 8. chezmoi update
- [ ] 9. apm install -g
- [ ] 10. apm compile -g
```

### 0. Validate input

- Reject if the argument is missing, empty, or not a full APM path.
- Accept format: `owner/repo` or `owner/repo/sub/path` — segments of `[A-Za-z0-9_.-]+`, separated by `/`, no leading or trailing `/`.
- Example valid: `takak2166/agent/skills/publish-skill-apm`
- Example invalid: `foo`, `/takak2166/agent/skills/foo`, `takak2166/agent/skills/foo/`
- On rejection, stop and report using **Fail-fast report** (**Step 0 — Validate input**, command: the invocation, error: why the path was rejected) and include a valid path example (e.g. `takak2166/agent/skills/<name>`).

### 1. Verify chezmoi source

- Confirm `~/.local/share/chezmoi` exists and is a git repository (`git -C ~/.local/share/chezmoi rev-parse --is-inside-work-tree`).
- Confirm `dot_apm/apm.yml` exists.
- If either check fails, stop and report using **Fail-fast report** (**Step 1 — Verify chezmoi source**, command: the failing check — e.g. `git -C ~/.local/share/chezmoi rev-parse --is-inside-work-tree` or existence of `dot_apm/apm.yml`, error: summary of the failure).

### 2. Check duplicate

- Read `dot_apm/apm.yml`.
- Treat the dependency as present only when it appears in **`dependencies.apm`** (not other keys or comments). Prefer:

```bash
yq -e '.dependencies.apm[] | select(. == "<path>")' dot_apm/apm.yml
```

- Exit code **0** → duplicate; **1** with no match → not registered. **`yq` is required** for steps 2 and 2b; if it is missing, stop and report using **Fail-fast report** (**Step 2 — Check duplicate**, command: `yq`, error: `yq` not on PATH). Do not grep the whole file — other keys such as `dependencies.discussed` can contain the same string.
- If present, report **already registered — no changes made** and **exit** — do not run steps 3–10.

### 2b. Root-package consumer layout

Some manifests declare only `takak2166/agent` and omit per-skill `takak2166/agent/skills/*` lines. APM ≥0.36 rejects adding a repository together with its own subdirectory packages.

Detect **root-only** layout in `dot_apm/apm.yml` with `yq` (from the chezmoi source directory):

1. `yq -e '.dependencies.apm[] | select(. == "takak2166/agent")' dot_apm/apm.yml` → exit **0** (root package listed).
2. `yq -e '.dependencies.apm[] | select(tag == "!!str" and (. | test("^takak2166/agent/skills/")))' dot_apm/apm.yml` → exit **1** with no match (no per-skill `takak2166/agent/skills/*` lines).

**Root-only** when check 1 exits **0** and check 2 exits **1** with no match (both predicates met — not “both commands exit 0”).

When layout is root-only **and** the input matches `takak2166/agent/skills/<name>`:

1. Do **not** append that skill path.
2. Resolve `skills/<name>/apm.yml` from the first readable file:
   - `$HOME/apm_modules/takak2166/agent/skills/<name>/apm.yml`
   - `$HOME/ghq/github.com/takak2166/agent/skills/<name>/apm.yml`
3. If neither exists, stop and report using **Fail-fast report** (**Step 2b — Root-package consumer layout**, command: read `skills/<name>/apm.yml` at the documented paths, error: manifest not found — cannot resolve transitive dependencies).
4. Collect string entries from `dependencies.apm` in that file (`yq '.dependencies.apm[] | select(tag == "!!str")'`). Treat any still missing in `dot_apm/apm.yml` (step 2 semantics) as **paths to append**.
5. If **paths to append** is empty, report **root package covers skill — no dot_apm changes** and run steps **8–10 only** (skip 3–7).
6. If non-empty, pass the list to step 3 (one commit for all lines), then continue 4–10.

Otherwise continue to step 3 with the single input path.

### 3. Append dependency

- Edit `dot_apm/apm.yml` only.
- For each path in **paths to append** (normally the validated input; after step 2b, only transitive paths — never the skill path under root-only layout), insert one line `    - <path>` in the **agent skill block**: after existing `takak2166/agent/skills/*` entries and **before** the first external repo dependency (list lines whose value does not start with `takak2166/agent`).
- If there is **no** external repo line, append after the **last** `takak2166/agent/` dependency in the list (still before any non-agent entries if they appear later).
- Keep YAML list indentation (4 spaces before `-`).
- Preserve a blank line before the external-repo block if one already exists.

### 4. Stage

```bash
git add dot_apm/apm.yml
```

- Non-zero exit → stop and report using **Fail-fast report** (**Step 4 — Stage**, command: `git add dot_apm/apm.yml`, error: non-zero exit; include captured stderr in **Error**).

### 5. Commit (create-commit-en equivalent)

Inline the commit logic; do **not** invoke `/create-commit-en` (different repo; full pipeline ownership).

1. Run `git diff --staged`.
   - If no diff, stop and report using **Fail-fast report** (**Step 5 — Commit**, command: `git diff --staged`, error: no staged changes after step 3) and **exit** — do not push or run apm.
2. Summarize the staged diff in one concise English sentence; pick prefix from `feat` / `fix` / `chore` / `test` / `refactor` / `docs` (typically `chore` for new apm dependency).
3. Commit:

```bash
git commit -m "prefix: <Message starting with capital letter>"
```

- Non-zero exit → stop and report using **Fail-fast report** (**Step 5 — Commit**, command: `git commit -m "…"`, error: non-zero exit; include captured stderr in **Error**) — do not push or run apm.

### 6. Warn on other dirty files

- Run `git status --porcelain`.
- If files other than `dot_apm/apm.yml` are modified or untracked, **warn** the user but **continue**.

### 7. Push to main

1. Confirm current branch is `main` (`git branch --show-current`). If not, stop and report using **Fail-fast report** (**Step 7 — Push to main**, command: `git branch --show-current`, error: current branch is not `main`).
2. Push without extra confirmation:

```bash
git push origin main
```

- Non-zero exit → stop and report using **Fail-fast report** (**Step 7 — Push to main**, command: `git push origin main`, error: non-zero exit; include captured stderr in **Error**) — do not run chezmoi or apm.

### 8. chezmoi update

```bash
chezmoi update
```

- Non-zero exit → stop and report using **Fail-fast report** (**Step 8 — chezmoi update**, command: `chezmoi update`, error: non-zero exit; include captured stdout/stderr in **Error**).

### 9. Materialize globally

```bash
apm install -g
```

- Non-zero exit → stop and report using **Fail-fast report** (**Step 9 — Materialize globally**, command: `apm install -g`, error: non-zero exit; include captured stdout/stderr in **Error**).
- `apm install` has no `--yes` flag; run as shown. If a future APM version adds a non-interactive flag for install, prefer it.

### 10. Regenerate user-scope root context

```bash
apm compile -g
```

1. **Capture** combined stdout and stderr from the command.
2. **Exit code:** non-zero → stop and report using **Fail-fast report** (**Step 10 — Regenerate user-scope root context**, command: `apm compile -g`, error: non-zero exit; include captured output in **Error** and list **Affected paths** when output names targets).
3. **Classify lines** using **Compile output contract** below (match meaning, not a bare `retained` prefix).
4. **Success:** every global compile target either shows a benign line or a `wrote` / `unchanged` line for its root file; list each `wrote` path in the **Success report**. If classification is ambiguous, rerun once with `apm compile -g -v` and reclassify; still ambiguous → stop and report using **Fail-fast report** (same step; command: `apm compile -g -v`; error: ambiguous compile output after verbose rerun).

#### Compile output contract

Read `targets:` from `~/.apm/apm.yml` (after step 9). Global user-scope root files are the compile outputs this step must account for (for example `~/.codex/AGENTS.md`, `~/.cursor/AGENTS.md`).

**Failure — stop and report using Fail-fast report** (**Step 10 — Regenerate user-scope root context**, command: `apm compile -g` or `apm compile -g -v` if rerun, error: the full triggering line(s), **Affected paths:** each path named in those lines):

- `skipped (hand-authored)` for any expected root target
- `retained` with `(edited or unverifiable generated file)`
- `retained` with `(symlink)` or any other `retained` variant that means APM did not write the file
- `skipped (no global instructions)` when that target should receive compiled instructions
- `error` / compile failure text from APM

**Benign — continue** (note in success report when relevant):

- `skipped (instructions already in native rules)` (Claude when rules already exist)
- `retained redundant` (optional cleanup via `apm compile -g --clean`; not a pipeline failure)
- `unchanged` for a target (idempotent success)
- `[+] <target>: wrote <path>` (success)

**Idempotent / empty `wrote` output:**

- Non-verbose compile may omit `unchanged`. If **no** `wrote` lines appear for targets that normally write, rerun with `apm compile -g -v`.
- After `-v`, if every non-benign-skipped target shows `wrote` or `unchanged`, success.
- If expected targets still lack `wrote` / `unchanged` / a documented benign skip, stop and report using **Fail-fast report** (step 10; command as above; error: missing expected output for one or more targets; **Affected paths:** targets still unaccounted for).

## Troubleshooting (outside this pipeline)

Allowed only with **owner approval** and **outside** steps 0–10. These commands are **not** in **Restrictions** for the pipeline itself.

### First-time switch to generated `~/.codex/AGENTS.md`

When step 10 fails with `skipped (hand-authored)` on `~/.codex/AGENTS.md`:

1. Copy the hand-written file to a dated backup (for example `~/.codex/AGENTS.md.bak-YYYYMMDD`).
2. Move the original out of the way.
3. Rerun `apm compile -g` (then `apm compile -g -v` if output is still unclear).

Do not edit generated root context files by hand afterwards; edits make APM retain/skip them on later compiles.

## Success report

After step 10, report using the branch that matches the run (steps 3–7 ran vs step 2b skipped 3–7).

**When steps 3–7 ran** (`dot_apm/apm.yml` changed):

- Requested input path
- Each dependency path appended in step 3 (under root-only layout these may be **transitive only**, not the skill path)
- Commit hash (from step 5)
- Push target (`origin/main`)
- `chezmoi update`, `apm install -g`, and `apm compile -g` completed
- **Compile outputs:** each path from a `wrote` line; note `unchanged` or benign skips (for example Claude native-rules skip) per target

**When step 2b skipped 3–7** (no `dot_apm` changes; **root package covers skill — no dot_apm changes**):

- Requested input path and that root package covers the skill (no new `dot_apm` lines)
- Do **not** list commit hash or push (steps 5–7 did not run)
- `chezmoi update`, `apm install -g`, and `apm compile -g` completed
- **Compile outputs:** same classification as above

## Restrictions

- **Allowed commands:** file read/edit for `dot_apm/apm.yml`; read-only access to `~/.apm/apm.yml` in step 10 only; read-only access to `skills/<name>/apm.yml` under `apm_modules/takak2166/agent` or `ghq/github.com/takak2166/agent` in step 2b only; `yq` read queries on those files in steps 2 and 2b only; `git -C ~/.local/share/chezmoi rev-parse` (including `--is-inside-work-tree`); `git diff --staged`, `git add dot_apm/apm.yml`, `git commit -m`, `git status --porcelain`, `git branch --show-current`, `git push origin main`; `chezmoi update`; `apm install -g`; `apm compile -g`; `apm compile -g -v` (only when step 10 requires clearer output).
- **Allowed file writes outside chezmoi:** user-scope root context files that `apm compile -g` generates or updates (under `~/.codex/`, `~/.cursor/`, `~/.config/opencode/`, and equivalent global compile targets).
- Do not push branches other than **main**.
- Do not run **project-scope** `apm update` or `apm compile` (without `-g`). Global `apm update -g` is **not** part of this pipeline; when run manually, follow `.apm/instructions/apm-global-root-context.instructions.md`.
- Do not pass `apm compile -g --clean`, `--force`, or other destructive/extra flags in this pipeline unless the owner explicitly approves outside this skill.
- Do not create git commits in repos other than the chezmoi source.