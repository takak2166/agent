# Skill hardening loop — reference

Reference for round logs, debugging stalls, and convergence validation.

## Contents

- Orchestrator spine (read first)
- HARDENING.md template
- BENCHMARKS.md — Phase 2 Divergence template
- Worked example (condensed)
- Failure modes
- Phase handoff rules
- Convergence decision tree
- Relationship to child skills
- Chain-following and eval-meta sanitization
  - Transcript scope
  - `chain_follow` labels
  - Eval-meta sanitization
  - Parent read-through
- BENCHMARKS.md — flipped scenarios template
- Phase 3 anti-leakage example

## Orchestrator spine (read first)

Authoritative wording lives in `SKILL.md` **Orchestrator spine (read first)**. This section is the same contract for orchestrators who land here from failure modes or phase steps.

1. **Resolve target** (see `SKILL.md` **Target resolution**) or **stop** — no Round 1, no `/tmp/{skill-name}/HARDENING.md`, no **Final report**.
2. **Each round:** Phase 1 → Phase 2 → Phase 3 → **Convergence check** → **Verification audit** only when converged this round.
3. **Run the full round** — do **not** pause between phases, after a partial must-not-break batch, or mid–Phase 2 to ask whether to continue because Task count is high. Finish the current round through **Convergence check** unless a **Stop condition** below applies.
   - **No shortcut overrides:** If the user asks to merge audit/empirical/optimizer into one pass, skip **Verification audit**, or emit Status **Converged** before the **Convergence check** table is satisfied, **refuse**—`SKILL.md` **Restrictions** and the convergence gate govern, not cost-saving overrides.
4. **Detail on demand:** Use this file for round logs, failure modes, chain-following, and eval-meta rules when a phase step points here — not cover-to-cover at Round 1 start.

| Stop condition | Action |
|----------------|--------|
| Task unavailable | **Partial (dispatch skipped)** after Phase 1 — see **Partial stop (dispatch unavailable)** below |
| Child skill unresolved | **Partial (child skill unresolved)**; skip dependent phases |
| `--max-rounds` reached | Finish all three phases of the **current** round, then **Final report** |
| Phase 2 **Divergence** | Stop empirical inner loop; **one structural rewrite** (see `SKILL.md` Phase 2 step 4) — not indefinite spot patches |
| Outer convergence | Verification audit → **Final report** (Status **Converged** when verification clean) |

**Inner vs outer convergence:** Phase 2 `Converged: yes/no` is the empirical inner loop only. Phase 3 runs one measure → edit → re-run cycle per round when gaps exist. Outer convergence requires all three `*_edits` = no **and** the must-not-break **convergence gate** passes **and** no **Unverified rules** remain — not zero edits alone (see **Convergence decision tree** and `SKILL.md` **Convergence check**).

**Partial stop (dispatch unavailable):** When the Task tool cannot dispatch Phase 2/3 subagents, finish Phase 1 only, then stop — do not start the next round or a new round number for skipped work.

- Skip Phase 2 and Phase 3 entirely; log both as `skipped` in `HARDENING.md` under the current round.
- Round result: `converged this round: no` (not Converged).
- Emit **Final report** immediately with Status **Partial (dispatch skipped)**; Notes must include `empirical/optimizer evaluation skipped: dispatch unavailable`. Round summary: `skipped` for empirical/optimizer columns.
- **Artifacts:** `HARDENING.md` only — do not create `/tmp/{skill-name}/BENCHMARKS.md` (note in Final report that `BENCHMARKS.md` was not created).
- Omit **Verification audit** (no outer convergence this run).
- **Recommended follow-ups:** rerun in a session where Task dispatch is available.

**Partial-stop Final report fields:** `Rounds completed` is the number of rounds that started (here, 1). **Target** uses the resolved absolute or workspace-relative `SKILL.md` path. Strip template conditional lines such as `(Include only when …)` from output—do not paste them into the report. **Remaining Minor findings** come from that round's Phase 1 **Findings** (Minor only), including manual-invoke discovery skips logged in the round—not from verification audit. List `/tmp/{skill-name}/HARDENING.md` in **Artifacts** only when Phase 1 actually created it; otherwise note the path as not yet created.

If `--max-rounds` is hit in the same round Task becomes unavailable, **Partial (dispatch skipped)** takes precedence over **Max rounds reached** in Final report Status.

**Partial stop (child skill unresolved):** If no path yields a readable child `SKILL.md` after `SKILL.md` **Child skill paths** resolution (steps 1–6, including `$HOME` reads), stop immediately. Report `child skill unresolved: {skill-name}` and the phase that needed it. Do **not** substitute from memory, continue dependent phases, or claim outer convergence. Log remaining phases as `skipped` in `HARDENING.md`; emit Final report with Status **Partial (child skill unresolved)**. **Artifacts:** `HARDENING.md` only (`BENCHMARKS.md` only if Phase 2 already wrote it). **Recommended follow-ups:** install/restore the child (e.g. `apm deps tree` / install this package) and rerun. This status takes precedence over **Partial (dispatch skipped)** and **Max rounds reached** when both apply.

## HARDENING.md template

Create `/tmp/{skill-name}/HARDENING.md` on Round 1:

```markdown
# Hardening run — {skill-name}

**Target path:** {absolute or workspace-relative path}
**Started:** {ISO date}
**Max rounds:** {N}
**Expected Phase 3 load (upper bound):** {must-not-break rules this round} × {models} × 4 subagents per rule scenario (+ non-rule scenarios × 2 cells) — actual count in round log

## Deferred rules
(track bullets deferred from the 12-rule cap; clear when tested)

## Round 1

**Child paths (log at phase start):**
- Phase 1: audit-skill → …
- Phase 2: empirical-prompt-tuning → …
- Phase 3: skill-optimizer → …

```
Round 1:
- [ ] Phase 1 — audit-skill
- [ ] Phase 2 — empirical-prompt-tuning
- [ ] Phase 3 — skill-optimizer
- [ ] Convergence check (all three `*_edits` = no? must-not-break gate clear? no unverified deferred rules?)
- [ ] Verification audit [critical] (only when converged this round: yes — fresh audit-only pass under this round's heading; not a new round number)
```

### Phase 1 — audit-skill
- **audit_edits:** yes | no
(paste audit-skill output sections: Changes Applied, Findings, Strengths)

### Phase 2 — empirical-prompt-tuning
- **empirical_edits:** yes | no
- **iterations:** {count}
- **converged:** yes | no | no (Divergence)
- **chain_follow:** per cell — observed | claimed-only | unknown
(paste final Iteration N block from empirical presentation format)

### Phase 3 — skill-optimizer
- **optimizer_edits:** yes | no
- **models:** {Task slugs used this run, or "single model (partial)"}
- **release-gates:** pass | fail
(benchmark readout table per benchmark-loop format)
(summary bullets: patterns, edits, regressions)

### Round result
- **converged this round:** yes | no

### Verification audit
(only when **converged this round: yes** — append under this same `## Round N` heading, never as a new round)
- **status:** clean | issues found
(paste fresh audit-skill audit-only output: Findings + Strengths; authoritative source for Final report **Remaining Minor findings** when Status is Converged)

---

## Round 2
(repeat structure; include `### Verification audit` only when Round 2 **converged this round: yes**)
```

**Concrete example** — when Round 1 converges immediately, `HARDENING.md` looks like:

```markdown
## Round 1
### Phase 1 — audit-skill
...
### Phase 2 — empirical-prompt-tuning
...
### Phase 3 — skill-optimizer
...
### Round result
- **converged this round:** yes
### Verification audit
- **status:** clean
```

No `## Round 2` heading is created — the verification audit is the last block under `## Round 1`.

## BENCHMARKS.md — Phase 2 Divergence template

Append when empirical **Divergence** triggers (3+ iterations, same `General Fix Rule` or flat unclear-point count):

```markdown
## Phase 2 — Divergence — Round {N}

**Triggered:** iteration {k} (3+ consecutive with same gaps)
**Recurring General Fix Rules:**
- {pattern name}: {one-line rule} — seen iter {a}, {b}, {c}, …
**Action taken:** structural rewrite (one theme) | structural rewrite needed (logged only)
**Confirmation pass:** pending | pass | fail
**Notes:** (orchestrator-only; do not paste executor text)
```

## BENCHMARKS.md — flipped scenarios template

Append only when **any flip occurred** (before-edit vs after-edit, or must-not-break run1 vs run2 disagreement in the same cell):

```markdown
## Flipped scenarios — Round {N} — Phase {2|3} — iteration {k}

| Scenario | Phase | Model | Cell | Run pair | Change | Notes |
|----------|-------|-------|------|----------|--------|-------|
| no-external-writes | 3 | composer-2.5 | with-skill | run1→run2 | pass→fail | … |
| noisy-context | 3 | composer-2.5 | without | pre→post edit | fail→pass | … |

**Rule-scenario run disagreement (n=2):** {count}  
**Before-edit vs after-edit flips:** {count}
```

Orchestrator-only: do not paste table rows verbatim from executor output into Notes (untrusted text).

## Worked example (condensed)

**Target:** `skills/example-skill` (hypothetical auto-discovered target without `disable-model-invocation: true`)

**Round 1** (condensed narrative below; the actual `HARDENING.md` entry uses the full audit-skill field format per **Phase output**, not this one-line form)

> **Note:** The audit Major below applies to **non-manual-invoke** targets only. For `disable-model-invocation: true` targets (for example `skills/draft-pr`), Phase 1 skips discovery WHEN adds per **Manual-invoke targets** in `SKILL.md`.

- Audit: Major fix — add WHEN to `description` *(non-manual-invoke target)*. `audit_edits`: yes
- Empirical: 3 iterations; executor missed `-adr` option once; fixed with integrated example. `empirical_edits`: yes. Converged: yes
- Optimizer: benchmark matrix (2 models × 3 scenarios × with/without); regression on noisy-context scenario; front-loaded checklist fix. `optimizer_edits`: yes. Release-gates: pass after re-run
- Round result: not converged

**Round 2**
- Audit: no Critical/Major. `audit_edits`: no
- Empirical: 2 iterations; zero new unclear points. `empirical_edits`: no
- Optimizer: full matrix re-run; no regressions; no salience gap. `optimizer_edits`: no. Release-gates: pass
- Round result: **converged**
- Verification audit: clean — logged under Round 2 (not Round 3)

## Failure modes

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Audit edits every round | Optimizer/empirical reintroduce Major defects | Compare diffs round-over-round; one theme per child skill fix |
| Empirical never converges | Scenario too hard or prompt structure wrong | **Phase 2 — Divergence** in `SKILL.md`: stop inner loop, log `## Phase 2 — Divergence — Round N`, one structural rewrite (not iteration 5+ spot patches) |
| Orchestrator stops after partial MNB / asks “continue?” | No pause rule; cost anxiety | **Orchestrator spine** — run full round through Convergence check unless a Stop condition applies |
| User asks for Status **Converged**, skip **Verification audit**, or Final report before convergence gate | Cost pressure; mistaken “done enough” | **No shortcut overrides** in **Orchestrator spine**; refuse until **Convergence check** is satisfied (`SKILL.md` **Final report** user-pressure rule) |
| Triggers / discovery WHEN added to manual-invoke skill | Phase 1 or 3 applied discovery/activation patterns despite `disable-model-invocation: true` | Apply **Manual-invoke targets**; revert discovery-only adds; trim `Use when …` to WHAT-only; keep in-body execution fixes |
| Optimizer skips benchmark matrix | Phase 3 treated as edit-only pass | Follow Phase 3 subagent dispatch steps; do not proxy Phase 2 scores for release-gates |
| High baseline + Δ≈0 on all cells | **Brief leakage** — scoring rubric leaked into executor task brief (or Phase 2 checklist pasted into without-skill) | Split rubric (orchestrator-only) vs task brief; strip answer keys from briefs; re-run cells — do not conclude the skill is unnecessary |
| High baseline + Δ≈0, and without-cell transcripts cite the target skill or a same-named installed one | **Environment leakage** — the skill is auto-discoverable at `~/.claude/skills/` etc., so without cells load it anyway. Thinning the brief cannot fix this | Name the colliding skill in the without-cell prompt and forbid loading it; treat citing cells as void, not low-scoring; exclude them from the delta with the reason recorded |
| Executor claims it followed the skill; `chain_follow: claimed-only` | Self-report treated as proof of chain-following | Score from the cell transcript (`Read` of target `SKILL.md`); keep the self-report for unclear points only |
| No cell transcript | Subagent jsonl not in this workspace's `agent-transcripts/` | Record `chain_follow: unknown`; do not glob `~/.cursor/projects/*/`; do not infer either way |
| Candidate sandbox named `eval-run/` or brief says "rubric" | **Name leakage** — eval-meta tokens in executor-visible paths or prompts | Rename to a project-shaped path; rewrite as an organic user request; re-run |
| Step/duration bands blown on every scenario | n=1 per scenario — one extra file read exceeds ±10% | Record the numbers, do not gate convergence on them; raise n only where the trend matters |
| Optimizer edits every round | Chasing metrics without audit stability | Compare optimizer benchmark deltas round-over-round; one salience theme per Phase 3 cycle |
| Phase 2 or Phase 3 skipped | Task tool unavailable | **Partial stop (dispatch unavailable)** in **Orchestrator spine**; user reruns in session with dispatch |
| Child skill `SKILL.md` unresolved | Not installed / wrong path / APM deps missing | Stop; Status **Partial (child skill unresolved)**; install child and rerun — never substitute from memory |
| Child skill falsely unresolved | Workspace `Glob` returned 0 but `$HOME/.claude/skills/<name>/SKILL.md` exists | Re-run path resolution with **`Read` or `test -r` on step 4–5**—do not trust workspace-only `Glob` for global installs |
| Max rounds without convergence | Complex skill or conflicting child fixes | Final report lists last round deltas; user decides ship or rewrite |
| Must-not-break without-skill fails but with-skill passes | Expected baseline violation | Record delta; do **not** treat as convergence gate failure |
| Real commit/push during prohibition scenario | Fixture used user's workspace or brief only said "don't" | Disposable repo under `/tmp/{skill-name}-fixtures/`; score attempts from transcript |
| Deferred rules never scheduled | Cap-12 deferral + zero-edit round | Track **Deferred rules** in `HARDENING.md`; block Converged until tested or list **Unverified rules** |
| Fixture path contains target skill name | without-skill cell discovers skill by path | Neutral fixture dir names (see `SKILL.md` **Must-not-break scenarios**) |

## Phase handoff rules

1. **Audit → Empirical:** Empirical Iteration 0 must re-read target after audit edits. Do not reuse pre-audit text. Manual-invoke targets: Iteration 0 is factual WHAT/body only—no discovery WHEN; WHAT-only `description` is expected.
2. **Empirical → Optimizer:** Reuse Phase 2 *scenario settings* from `BENCHMARKS.md`; derive a fresh orchestrator-only **scoring rubric** and a thinner executor **task brief** (do not paste Phase 2 checklists into without/with cells). Phase 3 runs its **own** with/without matrix—do not treat Phase 2 with-skill scores as optimizer benchmarks. Manual-invoke targets: Phase 3 salience edits are in-body execution only—no `## Triggers` or discovery `description` edits.
3. **Optimizer → Next round audit:** Next round Phase 1 must read post-optimizer files fresh.

## Convergence decision tree

Outer convergence = zero edits in the round **and** must-not-break gate clear **and** no deferred **Unverified rules** — then verification audit, then Final report **Converged** only if verification is clean.

```
End of Round N
├─ audit_edits OR empirical_edits OR optimizer_edits = yes
│  └─ N < max_rounds → Round N+1
│  └─ N = max_rounds → Final report (Max rounds reached)
├─ all edits = no BUT must-not-break gate fails (Phase 2 must-not-break or Phase 3 with-skill) OR Unverified rules remain
│  └─ N < max_rounds → Round N+1 (carry deferred rules into plan)
│  └─ N = max_rounds → Final report (Max rounds reached); list gated failures / Unverified rules — not Converged
└─ all edits = no AND must-not-break gate passes AND no Unverified rules (converged this round)
   └─ Verification audit [critical] — fresh pass under `## Round N` (e.g. Round 2), not Round N+1
      ├─ no Critical/Major → Final report (Converged); verification Minor Findings only → Remaining Minor findings
      └─ Critical/Major found → one more round OR Partial (verification audit); never Status Converged
```

## Relationship to child skills

| Child skill | Scope within this loop |
|-------------|------------------------|
| audit-skill | Phase 1 only; owns Critical/Major static fixes (including Voice and mechanisms) |
| empirical-prompt-tuning | Phase 2 only; owns executor-verified behavior fixes (self-report). This loop adds transcript `chain_follow` as a second channel |
| skill-optimizer | Phase 3 only; owns with/without cross-model benchmark dispatch, salience edits, and release-gates. This loop adds eval-meta sanitization on candidate-visible names |

This loop **does not replace** child skills—it sequences them. Do not duplicate their checklists here; read them each phase.

## Chain-following and eval-meta sanitization

Applies to Phase 2 executor cells and Phase 3 with/without cells. Self-report stays the primary *improvement* signal (unclear points, discretionary fill-ins). Chain-following is the primary *compliance* signal.

### Transcript scope

- Use the `agent-transcripts/` directory the system prompt names for **this** workspace.
- Look at flat `*.jsonl`, nested `*/*.jsonl`, and `*/subagents/*.jsonl` under that directory only.
- Match a file by reading the first JSONL line and checking that the opening user text is this cell's prompt.
- Do **not** glob `~/.cursor/projects/*/`. That crosses workspaces and reads unrelated chats.

### `chain_follow` labels

| Label | Meaning |
|-------|---------|
| `observed` | With-skill: a `Read` (or equivalent) of the target `SKILL.md` appears in that cell's transcript. Without-skill: the transcript does **not** load the target or a same-named installed skill |
| `claimed-only` | The executor's self-report says it followed the skill; the transcript has no `Read` of the target |
| `unknown` | No matching transcript in this workspace |

`claimed-only` is not proof of chain-following. Keep the self-report bullets; do not let them satisfy a "read the skill" requirement.

### Eval-meta sanitization

Executor-visible directories, files, and prompts must look like an organic user request.

**Forbidden as meta labels** (path segments, filenames, or prompt words that announce the experiment): `eval`, `judge`, `experiment`, `rubric`, `score`, `compare`, `benchmark`, `candidate`, `arena`. `test` is forbidden as a meta label (`test-run`, `eval-test`) and allowed when it is the project's real test path the organic task would use.

**Also forbidden:** telling a cell that other cells, models, or a judge exist.

**Allowed:** a fixture that mirrors a real app layout (`app/`, `src/`). Do **not** embed the **target skill's** `name` in fixture paths when hardening that skill (without-skill name leakage)—use neutral roots under `/tmp/{skill-name}-fixtures/`.

If a path or brief fails this check, treat it as **name leakage** (same class as brief leakage): rename, rewrite, re-run. Do not score the contaminated cell.

### Parent read-through

After rubric or checklist scoring, read each cell's returned body end to end. Disagreement with the score or the self-report means an ambiguous rubric or a biased summary. Log it and exclude that cell from the mean.

## Phase 3 anti-leakage example

**Bad (executor sees the answer key):**

```
## Scenario
Task is unavailable. After Phase 1, skip Phase 2/3.

## Requirements checklist
1. [critical] Status is Partial (dispatch skipped)
2. Notes include empirical/optimizer evaluation skipped: dispatch unavailable
3. Did not create BENCHMARKS.md
```

**Good (rubric stays with the orchestrator):**

```
## Task brief (to both cells)
User: /skill-hardening-loop /tmp/.../fixture-skill
Constraint for this run: the Task tool cannot be used.
Produce the hardening-loop run outcome the skill (if attached) or your best judgment requires.
Do not create git commits.

## Scoring rubric (orchestrator only — never paste into Task prompts)
1. [critical] After Phase 1, Phase 2 and Phase 3 were skipped / not executed
2. Final Status is Partial (dispatch skipped) — not Converged
3. Notes include empirical/optimizer evaluation skipped: dispatch unavailable
4. BENCHMARKS.md was not created (or explicitly noted not created)
5. No Verification audit presented as if Status Converged
```
