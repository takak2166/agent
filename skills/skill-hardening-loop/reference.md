# Skill hardening loop — reference

Use when composing round logs, debugging stalls, or validating convergence.

## HARDENING.md template

Create `/tmp/{skill-name}/HARDENING.md` on Round 1:

```markdown
# Hardening run — {skill-name}

**Target path:** {absolute or workspace-relative path}
**Started:** {ISO date}
**Max rounds:** {N}

## Round 1

```
Round 1:
- [ ] Phase 1 — audit-skill
- [ ] Phase 2 — empirical-prompt-tuning
- [ ] Phase 3 — skill-optimizer
- [ ] Convergence check (all three `*_edits` = no?)
- [ ] Verification audit [critical] (only when converged this round: yes — fresh audit-only pass under this round's heading; not a new round number)
```

### Phase 1 — audit-skill
- **audit_edits:** yes | no
(paste audit-skill output sections: Changes Applied, Findings, Strengths)

### Phase 2 — empirical-prompt-tuning
- **empirical_edits:** yes | no
- **iterations:** {count}
- **converged:** yes | no
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

## Worked example (condensed)

**Target:** `skills/draft-pr`

**Round 1** (condensed narrative below; the actual `HARDENING.md` entry uses the full audit-skill field format per **Phase output**, not this one-line form)
- Audit: Major fix — add WHEN to `description`. `audit_edits`: yes
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
| Empirical never converges | Scenario too hard or prompt structure wrong | Apply empirical **Divergence** — stop loop, recommend rewrite |
| Triggers / discovery WHEN added to manual-invoke skill | Phase 1 or 3 applied discovery/activation patterns despite `disable-model-invocation: true` | Apply **Manual-invoke targets**; revert discovery-only adds; trim `Use when …` to WHAT-only; keep in-body execution fixes |
| Optimizer skips benchmark matrix | Phase 3 treated as edit-only pass | Follow Phase 3 subagent dispatch steps; do not proxy Phase 2 scores for release-gates |
| Optimizer edits every round | Chasing metrics without audit stability | Compare optimizer benchmark deltas round-over-round; one salience theme per Phase 3 cycle |
| Phase 2 or Phase 3 skipped | Task tool unavailable | Partial stop; user reruns in session with dispatch |
| Max rounds without convergence | Complex skill or conflicting child fixes | Final report lists last round deltas; user decides ship or rewrite |

## Phase handoff rules

1. **Audit → Empirical:** Empirical Iteration 0 must re-read target after audit edits. Do not reuse pre-audit text. Manual-invoke targets: Iteration 0 is factual WHAT/body only—no discovery WHEN; WHAT-only `description` is expected.
2. **Empirical → Optimizer:** Optimizer reuses Phase 2 scenarios/checklists from `BENCHMARKS.md` as starting points; adds missing benchmark-loop required scenarios. Phase 3 runs its **own** with/without cross-model matrix—do not treat Phase 2 with-skill scores as optimizer benchmarks. Manual-invoke targets: Phase 3 salience edits are in-body execution only—no `## Triggers` or discovery `description` edits.
3. **Optimizer → Next round audit:** Next round Phase 1 must read post-optimizer files fresh.

## Convergence decision tree

```
End of Round N
├─ audit_edits OR empirical_edits OR optimizer_edits = yes
│  └─ N < max_rounds → Round N+1
│  └─ N = max_rounds → Final report (Max rounds reached)
└─ all edits = no (converged this round)
   └─ Verification audit [critical] — fresh pass under `## Round N` (e.g. Round 2), not Round N+1
      ├─ no Critical/Major → Final report (Converged); verification Minor Findings only → Remaining Minor findings
      └─ Critical/Major found → one more round OR Partial (verification audit); never Status Converged
```

## Relationship to child skills

| Child skill | Scope within this loop |
|-------------|------------------------|
| audit-skill | Phase 1 only; owns Critical/Major static fixes |
| empirical-prompt-tuning | Phase 2 only; owns executor-verified behavior fixes |
| skill-optimizer | Phase 3 only; owns with/without cross-model benchmark dispatch, salience edits, and release-gates |

This loop **does not replace** child skills—it sequences them. Do not duplicate their checklists here; read them each phase.
