---
name: skill-hardening-loop
description: Runs audit-skill, empirical-prompt-tuning, and skill-optimizer sequentially on a target skill, repeating rounds until no phase edits the target. Use when hardening a skill, converging skill quality, running the full audit→empirical→optimizer pipeline, or when the user invokes /skill-hardening-loop.
disable-model-invocation: true
---

# Skill Hardening Loop

Orchestrate **audit-skill → empirical-prompt-tuning → skill-optimizer** on one target skill. Repeat **rounds** until a full round makes **no edits** to the target skill directory.

**Role:** Pipeline operator. Read and follow each child skill fully at the start of its phase—do not substitute from memory.

## Triggers

- `/skill-hardening-loop`, skill hardening, skill convergence loop
- full audit + empirical + optimizer pipeline
- harden skill until no more changes

## Non-negotiables

1. **Resolve target** before Round 1 (see **Target resolution**). Missing or unresolvable path → ask and **stop**; do not start rounds.
2. **Read child skills** at the start of each phase from their installed paths (see **Child skill paths**).
3. **Scope edits** to the target skill directory only—the same restriction as audit-skill.
4. **Do not** create git commits unless the user explicitly asks.
5. **Task tool required** for empirical-prompt-tuning subagent dispatch. If unavailable, stop after Phase 1 and report `empirical evaluation skipped: dispatch unavailable`. Outer convergence is unreachable; verification audit is N/A.
6. **Record every round** in `/tmp/{skill-name}/HARDENING.md` (create on Round 1). Append empirical detail to `/tmp/{skill-name}/BENCHMARKS.md` per empirical-prompt-tuning.

## Usage

```
/skill-hardening-loop [path to SKILL.md or skill directory] [--max-rounds N]
```

**Quick example:** `/skill-hardening-loop @skills/draft-pr` → Round 1 runs audit on `draft-pr`, logs to `/tmp/draft-pr/HARDENING.md`, then empirical and optimizer; repeats until a round makes zero edits across all three phases.

- Default `--max-rounds`: **5**. At cap, finish all three phases of the **current round**, then stop; do not start the next round.
- Optional flags from child skills (for example `--audit-only`) are **not** supported unless the user explicitly passes them—this loop always runs the full edit-capable pipeline.

## Target resolution

Same rules as audit-skill Steps §1–§3:

1. Directory argument → audit `<directory>/SKILL.md`
2. File argument → treat as the skill document
3. Missing path → ask and stop
4. Unresolvable after search → report and stop

Use the target's frontmatter `name` as `{skill-name}` for `/tmp/{skill-name}/` logs.

## Child skill paths

Read the full `SKILL.md` (and linked files that skill requires) at phase start. Resolve each child skill directory using **Path resolution** below, then open paths relative to that directory.

| Phase | Skill | Files to read |
|-------|-------|---------------|
| 1 | audit-skill | `SKILL.md`, `reference.md` |
| 2 | empirical-prompt-tuning | `SKILL.md` |
| 3 | skill-optimizer | `SKILL.md`, `rules/benchmark-loop.md`, `rules/activation-design.md`, `rules/release-gates.md` |

**Path resolution (all phases):** try in order; stop at the first directory that contains the skill's `SKILL.md`:

1. `.agents/skills/<skill-name>/` — APM default for Cursor, Copilot, Codex, Gemini, Windsurf, OpenCode
2. `.claude/skills/<skill-name>/` — APM default for Claude Code (project-local)
3. `skills/<skill-name>/` — source layout in `takak2166/agent` or vendored monorepo skills
4. `~/.claude/skills/<skill-name>/` — manual global install (Claude Code)
5. `Glob` search for `<skill-name>/SKILL.md`; stop only if still not found

Phase 1–3 child skills are declared as transitive APM dependencies in [`apm.yml`](apm.yml). Installing `takak2166/agent/skills/skill-hardening-loop` resolves them automatically; verify with `apm deps tree`.

## Round workflow

Copy this checklist each round and mark progress in the round log:

```
Round N:
- [ ] Phase 1 — audit-skill
- [ ] Phase 2 — empirical-prompt-tuning
- [ ] Phase 3 — skill-optimizer
- [ ] Convergence check
```

### Phase 1 — audit-skill

1. Read audit-skill `SKILL.md` and its `reference.md`.
2. Run audit on the target with intent **repeat until only Minor findings remain** — this **overrides** audit-skill's default single-pass behavior (audit-skill Steps: re-audit internally when Critical/Major fixes were applied in the same pass).
3. Record `audit_edits`: yes / no.

**Phase output:** embed audit-skill's full output format (**Changes Applied** → **Findings** → **Strengths**, with all fields—not a one-line summary) in the round log. If audit-skill's internal re-audit ran multiple times, **Changes Applied** lists every fix across all internal passes (cumulative, consistent with `audit_edits: yes`); **Findings**/**Strengths** reflect only the final pass's remaining state.

### Phase 2 — empirical-prompt-tuning

Skip entirely if Task tool is unavailable (see **Non-negotiables**).

1. Read empirical-prompt-tuning `SKILL.md` in full.
2. Run **Iteration 0** (description/body consistency) on the target.
3. Run the full empirical loop (baseline → dispatch subagents → two-sided evaluation → apply diff → re-evaluate) until **empirical convergence**:
   - **3** consecutive iterations with **zero new unclear points** for orchestrator/meta skills (including this skill); **2** for ordinary targets
   - Accuracy improvement ≤ +3 points vs previous iteration
   - Step count within ±10%, duration within ±15% of previous
   - Hold-out scenario: if accuracy drops ≥15 points from recent average, add edge scenarios and continue (do not declare converged)
4. Append iteration summaries to `/tmp/{skill-name}/BENCHMARKS.md`.
5. Record:
   - `empirical_edits`: yes / no
   - Iteration count
   - Final accuracy / success per scenario (table from empirical presentation format)
   - Converged: yes / no (and why if no)

**Phase output:** one **Iteration N** block (final state) from empirical presentation format in the round log.

### Phase 3 — skill-optimizer

1. Read skill-optimizer `SKILL.md` and the three rule files listed in **Child skill paths**.
2. Using empirical results from Phase 2 (and prior `BENCHMARKS.md` if present), run **one optimizer pass** this round:
   - Identify activation gaps, universal failures, or negative deltas
   - Apply **minimum salience edits** (triggers, front-loaded checklists, integrated examples, context trim) in the target skill directory
   - Check **release-gates** required pass conditions; do not ship-blocking issues silently
   - **Do not** re-dispatch empirical subagents; re-evaluation belongs to the next round's Phase 2
3. Record:
   - `optimizer_edits`: yes / no
   - Patterns addressed (activation, context budget, regression)
   - Release-gate status: pass / fail (with failing items)

**Phase output:** short optimizer summary in the round log.

### Convergence check

After Phase 3:

| Condition | Result |
|-----------|--------|
| `audit_edits` = no **and** `empirical_edits` = no **and** `optimizer_edits` = no | **Converged** — stop loop |
| Any phase edited the target | **Not converged** — start Round N+1 (unless `--max-rounds` reached) |
| Phase 2 skipped (no Task) | **Partial stop** — report; do not claim full convergence; `BENCHMARKS.md` is not created |

**Inner vs outer convergence:** Phase 2 tracks empirical inner-loop convergence (`Converged: yes/no` in its iteration block). Outer-loop convergence is separate: all three phases must make zero edits in one full round.

When converged, run a **fresh** audit-only pass (audit-skill, audit-only mindset) as the **verification audit**—not a restatement of that round's Phase 1 result—since Phase 1 ran before Phase 2/3 and cannot see edits they made; confirm no Critical/Major remain before the final report. Log it in `HARDENING.md` as a `### Verification audit` subsection appended after that same round's Phase 3 (not a new round number). If verification finds Critical/Major → one more round or report **Partial**. Otherwise, the verification audit's **Findings** are the authoritative source for the Final report's **Remaining Minor findings** (supersedes that round's Phase 1 Findings).

## Final report

Use this structure:

```markdown
## Skill Hardening Loop — Final Report

**Target:** {resolved SKILL.md path, not the raw CLI argument}
**Skill name:** {skill-name}
**Rounds completed:** N
**Status:** Converged | Max rounds reached | Partial (empirical skipped)
(if Phase 2 is skipped in the same round the cap is hit, use **Partial (empirical skipped)**—it takes precedence over Max rounds reached)

### Round summary
| Round | Audit edits | Empirical edits | Optimizer edits | Notes |
|-------|-------------|-----------------|-----------------|-------|

### Verification audit
(Critical/Major status when converged: "clean — no Critical/Major remain" or the issue found; omit this section entirely for Max rounds reached / Partial statuses)

### Artifacts
- `/tmp/{skill-name}/HARDENING.md`
- `/tmp/{skill-name}/BENCHMARKS.md`

### Remaining Minor findings
(bullets from the verification audit's **Findings** when converged; otherwise from the last round's Phase 1 **Findings**; or "none")

### Recommended follow-ups
(only if release-gates failed, hold-out failed, unresolved Critical/Major, or Status is **Max rounds reached** — recommend rerunning with a higher `--max-rounds`)
```

## Restrictions

- **No shortcut phases:** Do not merge audit, empirical, and optimizer into one ad-hoc pass.
- **One target per invocation:** Multi-skill repo audits are out of scope unless the user lists one target path.
- **Preserve intentional design:** Same as audit-skill—verbatim user wording and `disable-model-invocation` choices stay unless a child skill's fix requires changing them.
- **Divergence escape hatch:** If empirical shows unclear points not decreasing across 3+ iterations (empirical **Divergence** criterion), stop the loop, report structural rewrite needed, and do not patch indefinitely.

## Additional resources

Round log template, worked example, and failure-mode table: [reference.md](reference.md)
