---
name: skill-hardening-loop
description: Runs audit-skill, empirical-prompt-tuning, and skill-optimizer sequentially on a target skill, repeating rounds until no phase edits the target.
disable-model-invocation: true
---

# Skill Hardening Loop

Orchestrate **audit-skill → empirical-prompt-tuning → skill-optimizer** on one target skill. Repeat **rounds** until a full round makes **no edits** to the target skill directory.

**Role:** Pipeline operator. Read and follow each child skill fully at the start of its phase—do not substitute from memory.

## Non-negotiables

1. **Resolve target** before Round 1 (see **Target resolution**). Missing or unresolvable path → ask and **stop**; do not start rounds.
2. **Read child skills** at the start of each phase from their installed paths (see **Child skill paths**).
3. **Scope edits** to the target skill directory only—the same restriction as audit-skill.
4. **Do not** create git commits unless the user explicitly asks.
5. **Task tool required** for Phase 2 and Phase 3 subagent dispatch. If unavailable, stop after Phase 1 and report `empirical/optimizer evaluation skipped: dispatch unavailable`. Outer convergence is unreachable; verification audit is N/A.
6. **Record every round** in `/tmp/{skill-name}/HARDENING.md` (create on Round 1). `{skill-name}` is always the **target skill's** frontmatter `name`—never this loop skill's name. Append Phase 2 detail to `/tmp/{skill-name}/BENCHMARKS.md` per empirical-prompt-tuning; append Phase 3 optimizer benchmark matrices to the same file under `## Optimizer benchmark — Round N` headings.

## Usage

```
/skill-hardening-loop [path to SKILL.md or skill directory] [--max-rounds N]
```

**Quick examples:**
- `/skill-hardening-loop @skills/draft-pr` → Round 1 runs audit on `draft-pr`, logs to `/tmp/draft-pr/HARDENING.md`, then empirical and optimizer; repeats until a round makes zero edits across all three phases.
- `/skill-hardening-loop @skills/skill-hardening-loop` → self-hardening; logs to `/tmp/skill-hardening-loop/HARDENING.md`.

- Default `--max-rounds`: **5**. At cap, finish all three phases of the **current round**, then stop; do not start the next round.
- Optional flags from child skills (for example `--audit-only`) are **not** supported unless the user explicitly passes them—this loop always runs the full edit-capable pipeline.

## Target resolution

Same rules as audit-skill Steps §1–§3:

1. Directory argument → audit `<directory>/SKILL.md`
2. File argument → treat as the skill document
3. Strip a leading `@` from CLI arguments before resolving paths
4. Missing path → ask and stop
5. Unresolvable after search → report and stop

Use the target's frontmatter `name` as `{skill-name}` for `/tmp/{skill-name}/` logs.

## Manual-invoke targets (`disable-model-invocation: true`)

When the target sets `disable-model-invocation: true`, the skill is **explicitly attached or invoked**—auto-discovery and activation tuning do not apply. This section **overrides** child skills on discovery-only edits in all phases.

**Recommended for `description`:**
- **WHAT only** (third person). Slash commands, attach, and invoke examples belong in **Usage**—not discovery WHEN in frontmatter.

**Do not add or expand:**
- Discovery-oriented `Use when …` clauses or trigger-phrase lists in `description`
- New or expanded `## Triggers` (or equivalent trigger-list sections)
- Trigger-phrase lists aimed at skill retrieval / activation

**May remove on manual-invoke targets:**
- Existing discovery-oriented `Use when …` in `description` (trim to WHAT-only)
- Redundant `## Triggers` sections when invocation is already covered in **Usage**

**Keep in `description` when factual (not discovery):**
- Workflow prerequisites that define scope (e.g. "Assumes `check-pr-comment` ran in the same conversation")—not phrases aimed at auto-loading the skill

**Trim vs keep (existing `Use when …` in `description`):**
- **Trim:** clauses whose only job is auto-discovery (synonyms for "invoke this skill", keyword lists, slash-command triggers)
- **Keep:** factual workflow prerequisites tied to *other* artifacts or ordering (e.g. "after `check-pr-comment` triage in the same conversation")
- **Mixed clause:** keep the factual prerequisite portion; remove only the discovery-oriented tail. Do not Major-fix *missing* WHEN; non-missing Major (contradiction with body, wrong third person) still applies when not discovery-only

**Still in scope:**
- `description` fixes that correct **factual WHAT/body mismatches** (Phase 2 Iteration 0)
- In-body **execution clarity**: front-loaded checklists, integrated examples, must/omit wording, regression fixes (Phase 3)
- Phase 3 benchmark matrix (measures executor behavior when the skill is attached)

Log skipped discovery-only findings in the round log (for example `discovery edits skipped: manual-invoke target`).

## Child skill paths

Read the full `SKILL.md` (and linked files that skill requires) at phase start. Resolve each child skill directory using **Path resolution** below, then open paths relative to that directory.

| Phase | Skill | Files to read |
|-------|-------|---------------|
| 1 | audit-skill | `SKILL.md`, `reference.md` |
| 2 | empirical-prompt-tuning | `SKILL.md` |
| 3 | skill-optimizer | `SKILL.md`, `rules/benchmark-loop.md`, `rules/activation-design.md`, `rules/regression-triage.md`, `rules/release-gates.md` |

**Path resolution (all phases):** try in order; use the first directory that contains the skill's `SKILL.md`:

1. `.agents/skills/<skill-name>/` — APM default for Cursor, Copilot, Codex, Gemini, Windsurf, OpenCode
2. `.claude/skills/<skill-name>/` — APM default for Claude Code (project-local)
3. `skills/<skill-name>/` — source layout in `takak2166/agent` or vendored monorepo skills
4. `~/.claude/skills/<skill-name>/` — manual global install (Claude Code)
5. `Glob` search for `<skill-name>/SKILL.md`

**Unresolved child skill:** If no path yields a readable `SKILL.md` after step 5, stop immediately. Report `child skill unresolved: {skill-name}` and the phase that needed it. Do **not** substitute that child from memory. Do **not** continue phases that depend on it. Do **not** claim outer convergence. Log remaining phases as `skipped` in `HARDENING.md`; emit Final report with Status **Partial (child skill unresolved)**; Artifacts: `HARDENING.md` only (`BENCHMARKS.md` only if Phase 2 already wrote it); Recommended follow-ups: install/restore the child (e.g. `apm deps tree` / install this package) and rerun.

Phase 1–3 child skills are declared as transitive APM dependencies in [`apm.yml`](apm.yml). Installing `takak2166/agent/skills/skill-hardening-loop` resolves them automatically; verify with `apm deps tree`.

## Round workflow

Copy this checklist each round and mark progress in the round log:

```
Round N:
- [ ] Phase 1 — audit-skill
- [ ] Phase 2 — empirical-prompt-tuning
- [ ] Phase 3 — skill-optimizer
- [ ] Convergence check (all three `*_edits` = no?)
- [ ] Verification audit [critical] (only when converged this round: yes — fresh audit-only pass under this round's heading, e.g. `## Round 2`; not a new round number)
```

### Phase 1 — audit-skill

1. Read audit-skill `SKILL.md` and its `reference.md`.
2. Run audit on the target with intent **repeat until only Minor findings remain** — this **overrides** audit-skill's default single-pass behavior (audit-skill Steps: re-audit internally when Critical/Major fixes were applied in the same pass). For **manual-invoke targets** (see above), do **not** Major-fix missing discovery WHEN or absent `## Triggers`; **may** trim discovery-oriented `Use when …` in `description` to WHAT-only—log other skipped discovery findings instead.
3. Record `audit_edits`: yes / no.

**Phase output:** embed audit-skill's full output format (**Changes Applied** → **Findings** → **Strengths**, with all fields—not a one-line summary) in the round log. If audit-skill's internal re-audit ran multiple times, **Changes Applied** lists every fix across all internal passes (cumulative, consistent with `audit_edits: yes`); **Findings**/**Strengths** reflect only the final pass's remaining state.

### Phase 2 — empirical-prompt-tuning

Skip entirely if Task tool is unavailable (see **Non-negotiables**).

1. Read empirical-prompt-tuning `SKILL.md` in full.
2. Run **Iteration 0** (description/body consistency) on the target. For **manual-invoke targets**, reconcile only **factual** WHAT/body gaps—do not add discovery WHEN or trigger phrases to `description`. If Phase 1 already fixed factual WHAT/body gaps, Iteration 0 is a confirmation pass only—do not re-edit unless Phase 1 skipped the fix.
3. Run the full empirical loop (baseline → dispatch subagents → two-sided evaluation → apply diff → re-evaluate) until **empirical convergence**:
   - **3** consecutive iterations with **zero new unclear points** for orchestrator/meta skills (including this skill); **2** for ordinary targets
   - Accuracy improvement ≤ +3 points vs previous iteration
   - Step count within ±10%, duration within ±15% of previous — **these two bands only mean something at ≥2 runs per scenario.** At n=1 a single extra file read moves step count past ±10%, so the band measures run-to-run noise rather than the target. With one run per scenario, **record both numbers but do not gate convergence on them**; converge on the unclear-point and accuracy criteria instead, and write `step/duration: n=1, recorded not gating` in the iteration block. Raise n only for scenarios whose trend you actually intend to read—paying for extra runs everywhere is rarely worth it.
   - Hold-out scenario: if accuracy drops ≥15 points from recent average, add edge scenarios and continue (do not declare converged)
4. Append iteration summaries to `/tmp/{skill-name}/BENCHMARKS.md`.
5. Record:
   - `empirical_edits`: yes / no
   - Iteration count
   - Final accuracy / success per scenario (table from empirical presentation format)
   - Converged: yes / no (and why if no)

**Phase output:** one **Iteration N** block (final state) from empirical presentation format in the round log.

### Phase 3 — skill-optimizer

Skip entirely if Task tool is unavailable (same as Phase 2).

1. Read skill-optimizer `SKILL.md` and all rule files listed in **Child skill paths**.
2. Run skill-optimizer's **default optimization loop** (measure → find failure pattern → edit for salience → re-run evals → release gates). Do **not** substitute Phase 2 empirical results for the benchmark matrix—Phase 3 owns with/without cross-model measurement.
3. **Benchmark matrix (subagent dispatch required):**

   **Phase 3 dispatch checklist** (orchestrator-only — do **not** paste this checklist or its items into Task prompts; complete before first subagent call):
   - [ ] Scenarios cover core capability, omission-prone footer/checklist, and noisy-context retrieval
   - [ ] Orchestrator-only **scoring rubric** drafted (5 items, ≥1 `[critical]`) — not pasted into Task prompts
   - [ ] Executor **task brief** written thinner than the rubric (no Status labels, skip-phase wording, or artifact rules as answer keys)
   - [ ] Phase 2 *scenario settings* reused from `BENCHMARKS.md` when present; missing benchmark-loop scenarios added
   - [ ] At least 2 distinct Task models when supported (log `multi-model: partial` if only one)
   - [ ] Target `name` checked against installed skills; if it collides, the without-cell prompt names that skill and forbids loading it
   - [ ] Each scenario × model: two **fresh** subagents (with-skill gets target `SKILL.md`; without-skill gets brief only)
   - [ ] After cells return, score against rubric only; record matrix under `## Optimizer benchmark — Round N` in `BENCHMARKS.md`

   - **Scenarios:** Reuse Phase 2 *scenario settings* from `BENCHMARKS.md` when present; add any missing **benchmark-loop** required scenarios (core capability, omission-prone footer/checklist, noisy-context retrieval). Do **not** paste Phase 2 requirements checklists into executor prompts as-is—Phase 2 lists are with-skill achievement items and leak answers into without-skill cells.
   - **Models:** Use **distinct models available via Task in this environment**—no fixed slug list (panels differ by host). Dispatch at least **2** when supported; if only one is available, run the full with/without matrix on that model and log `multi-model: partial (single model)`. Record chosen slugs in the round log and `BENCHMARKS.md`.
   - **Split scoring from the task brief [critical] (overrides skill-optimizer when they conflict):** Keep two artifacts per scenario (bad/good brief vs rubric contrast: [Phase 3 anti-leakage example](reference.md#phase-3-anti-leakage-example)):
     - **Scoring rubric** (orchestrator-only, **5 items**, ≥1 `[critical]`): used only when *you* score deliverables. May name exact Status strings, Notes phrases, artifact rules, and must/omit criteria.
     - **Task brief** (executor-facing): user request + constraints + what to produce. Must **not** include the scoring rubric, and must **not** spell the rubric's answer keys (exact Status labels, required Notes wording, "skip Phase 2/3", "do not create BENCHMARKS.md", "do not emit Verification audit", etc.).
   - **Cells:** For each scenario × model, dispatch **two fresh subagents** (never reuse). Both cells get the **same task brief**; only with-skill also gets the target skill:
     - **Without skill:** task brief only—do **not** attach the target skill; do **not** attach the scoring rubric.
     - **With skill:** same task brief + target `SKILL.md` (Read path or inline)—do **not** attach the scoring rubric.
   - **Anti-leakage:** A without cell can be handed the answer from two directions—the **brief** or the **environment**. They look identical in the matrix (high baseline, Δ≈0) but need opposite fixes, so diagnose which one before acting.
     - **Brief leakage:** without-skill satisfies the rubric by copying the prompt. Rewrite the task brief thinner and keep specifics only in the rubric. Prefer outcome-shaped briefs ("handle Task unavailable and report the run") over procedure-shaped briefs that restate the skill.
     - **Environment leakage:** the target—or a same-named sibling still installed at `~/.claude/skills/`, `.claude/skills/`, or `.agents/skills/`—is auto-discoverable, so the without-skill executor loads it regardless of what the brief says. Thinning the brief does nothing here. Before dispatching, check whether the target's `name` collides with an installed skill; if it does, name that skill in the without-cell prompt and instruct the executor not to load or consult it. A cell whose transcript cites it is **void, not low-scoring**—re-run it, or drop it from the delta and record why.
     - When most without cells hit ~100% with Δ≈0, treat it as **eval contamination**, not proof the skill is unnecessary. Averaging a contaminated cell into the matrix understates the delta, so exclude it explicitly rather than letting it drag the mean.
   - **Parallelism:** Batch independent cells in one message (multiple Task calls) when practical.
   - **Scoring:** After each cell returns, score against the orchestrator-only rubric: **%** = satisfied items / 5 (○ = 1, partial = 0.5, × = 0). Delta = with − without. Record rubric + brief alongside the matrix in `BENCHMARKS.md`.
   - **Readout:** Use benchmark-loop table format; flag universal failures (0% with skill) and regressions (negative delta) per `regression-triage.md`.
4. **Salience edits:** If the matrix shows universal failures or regressions, apply **minimum salience edits**. For **manual-invoke targets**, limit to in-body execution clarity (front-loaded checklists, integrated examples, must/omit wording)—**not** discovery triggers (`## Triggers`, `description` WHEN expansion, trigger-phrase lists). For other targets, activation-design patterns (including triggers) apply when the matrix shows activation gaps. One theme per optimizer iteration within this phase.
5. **Re-run evals:** After edits, re-dispatch subagents on **affected scenario × model cells** (at minimum: any cell with regression or universal failure; ideally the full matrix if edits were global). Compare deltas to the pre-edit run.
6. **Release gates:** Check required pass conditions in `release-gates.md` against the **latest** benchmark matrix (date, matrix, deltas recorded in `BENCHMARKS.md`). Do not ship-blocking issues silently.
7. **Inner stop (this phase):** Stop Phase 3 when release gates pass with no new salience edits needed, or after **one** edit → re-run cycle this round (outer round may continue if `optimizer_edits: yes`).
8. Append the benchmark matrix and interpretation to `/tmp/{skill-name}/BENCHMARKS.md` under `## Optimizer benchmark — Round N`.
9. Record:
   - `optimizer_edits`: yes / no
   - Models used
   - Patterns addressed (activation, context budget, regression)
   - Release-gate status: pass / fail (with failing items)

**Phase output:** benchmark readout table + optimizer summary (patterns, edits, release-gate status) in the round log.

### Convergence check

After Phase 3:

| Condition | Result |
|-----------|--------|
| `audit_edits` = no **and** `empirical_edits` = no **and** `optimizer_edits` = no | **Converged this round** — run **Verification audit** (below); do **not** emit Status **Converged** until verification passes |
| Any phase edited the target | **Not converged** — start Round N+1 (unless `--max-rounds` reached) |
| Phase 2 or Phase 3 skipped (no Task) | **Partial stop** — report; do not claim full convergence; `BENCHMARKS.md` is not created; do not start the next round |

**Partial stop (dispatch unavailable):** After Phase 1, skip Phase 2 and Phase 3 entirely. Log both phases as `skipped` in `HARDENING.md`; set Round result `converged this round: no`. Emit Final report immediately with Status **Partial (dispatch skipped)** — include message `empirical/optimizer evaluation skipped: dispatch unavailable` in Notes. Round summary: `skipped` for empirical/optimizer columns. **Artifacts:** list `HARDENING.md` only (note `BENCHMARKS.md` not created). Omit **Verification audit**. **Recommended follow-ups:** rerun in a session where Task dispatch is available.

**Inner vs outer convergence:** Phase 2 tracks empirical inner-loop convergence (`Converged: yes/no` in its iteration block). Phase 3 runs one measure → edit → re-run cycle per round when gaps exist. Outer-loop convergence is separate: all three phases must make zero edits in one full round.

When **converged this round** (all three `*_edits` = no), run a **[critical] fresh** audit-only pass (audit-skill, audit-only mindset) as the **verification audit**—re-read the target from disk; do **not** restate or copy that round's Phase 1 output, since Phase 1 ran before Phase 2/3 and cannot see edits they made. Log it in `HARDENING.md` as a `### Verification audit` subsection **under the same `## Round N` heading** (e.g. under `## Round 2` when Round 2 converges)—never as `## Round N+1`.

**Verification audit rules:**
- **Read** audit-skill `SKILL.md` and `reference.md` from disk before the verification pass (same as Phase 1 step 1)—then audit-only mindset on the post–Phase 3 target.
- Apply **Manual-invoke targets** the same as Phase 1: do not treat absent discovery WHEN / `## Triggers` as unresolved Critical/Major; existing discovery WHEN may be trimmed to WHAT-only per **Trim vs keep**; log other skipped discovery findings instead.
- Output **Findings + Strengths** only (audit-only; no **Changes Applied** unless the user explicitly requested edits).
- If verification finds **any Critical or Major** → start **one more round** when `N < max_rounds`; otherwise emit Final report **Partial (verification audit)**. **Never** emit Status **Converged** while Critical/Major remain.
- **Remaining Minor findings** in the Final report come **only** from this verification audit's **Findings** (Minor severity)—not from that round's Phase 1, not from earlier rounds.

## Final report

Use this structure:

```markdown
## Skill Hardening Loop — Final Report

**Target:** {resolved SKILL.md path, not the raw CLI argument}
**Skill name:** {skill-name}
**Rounds completed:** N
**Status:** Converged | Max rounds reached | Partial (dispatch skipped) | Partial (child skill unresolved) | Partial (verification audit)
(if Phase 2 or Phase 3 is skipped because Task is unavailable in the same round the cap is hit, use **Partial (dispatch skipped)**—it takes precedence over Max rounds reached)
(if a required child skill file is missing after Path resolution, use **Partial (child skill unresolved)**—takes precedence over dispatch-skipped and Max rounds reached)
(if verification audit finds Critical/Major when otherwise converged, use **Partial (verification audit)**)

### Round summary
| Round | Audit edits | Empirical edits | Optimizer edits | Notes |
|-------|-------------|-----------------|-----------------|-------|

### Verification audit
(Include only when Status is **Converged**. Report Critical/Major status: "clean — no Critical/Major remain" or list issues found. Omit for Max rounds reached / Partial statuses.)

### Artifacts
- `/tmp/{skill-name}/HARDENING.md`
- `/tmp/{skill-name}/BENCHMARKS.md`

### Remaining Minor findings
(when Status is **Converged**: bullets from verification audit **Findings** only—Minor severity; when Status is **Partial (verification audit)**: list unresolved Critical/Major from verification; otherwise from the last round's Phase 1 **Findings**; or "none")

### Recommended follow-ups
(only if release-gates failed, hold-out failed, unresolved Critical/Major, Status is **Max rounds reached**, Status is **Partial (dispatch skipped)**, Status is **Partial (child skill unresolved)**, or Status is **Partial (verification audit)** — for Partial (dispatch skipped), recommend rerunning with Task dispatch; for Partial (child skill unresolved), recommend installing/restoring the missing child and rerunning)
```

## Restrictions

- **No shortcut phases:** Do not merge audit, empirical, and optimizer into one ad-hoc pass.
- **One target per invocation:** Multi-skill repo audits are out of scope unless the user lists one target path.
- **Preserve intentional design:** Same as audit-skill—verbatim user wording and `disable-model-invocation` choices stay unless a child skill's fix requires changing them. Manual-invoke targets: see **Manual-invoke targets**—WHAT-only `description`; no discovery WHEN / `## Triggers` adds; trimming discovery WHEN is allowed.
- **Divergence escape hatch:** If empirical shows unclear points not decreasing across 3+ iterations (empirical **Divergence** criterion), stop the loop, report structural rewrite needed, and do not patch indefinitely.

## Additional resources

Round log template, worked example, and failure-mode table: [reference.md](reference.md)
