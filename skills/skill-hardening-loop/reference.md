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
- **release-gates:** pass | fail
(summary bullets)

### Round result
- **converged this round:** yes | no

### Verification audit
- **status:** clean | issues found
(paste audit-skill audit-only output: Findings + Strengths; this is the authoritative "last audit" for the Final report's Remaining Minor findings)

---

## Round 2
(repeat structure; omit "### Verification audit" entirely for any round where converged this round: no)
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
- Optimizer: front-loaded Restrictions checklist. `optimizer_edits`: yes
- Round result: not converged

**Round 2**
- Audit: no Critical/Major. `audit_edits`: no
- Empirical: 2 iterations; zero new unclear points. `empirical_edits`: no
- Optimizer: release-gates pass; no salience gap. `optimizer_edits`: no
- Round result: **converged**

## Failure modes

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Audit edits every round | Optimizer/empirical reintroduce Major defects | Compare diffs round-over-round; one theme per child skill fix |
| Empirical never converges | Scenario too hard or prompt structure wrong | Apply empirical **Divergence** — stop loop, recommend rewrite |
| Optimizer edits every round | Chasing metrics without audit stability | Run audit-only verification between rounds; tie optimizer to BENCHMARKS gaps only |
| Phase 2 skipped | Task tool unavailable | Partial stop; user reruns in session with dispatch |
| Max rounds without convergence | Complex skill or conflicting child fixes | Final report lists last round deltas; user decides ship or rewrite |

## Phase handoff rules

1. **Audit → Empirical:** Empirical Iteration 0 must re-read target after audit edits. Do not reuse pre-audit text.
2. **Empirical → Optimizer:** Optimizer must read latest `BENCHMARKS.md` entry, not only chat summary.
3. **Optimizer → Next round audit:** Next round Phase 1 must read post-optimizer files fresh.

## Convergence decision tree

```
End of Round N
├─ audit_edits OR empirical_edits OR optimizer_edits = yes
│  └─ N < max_rounds → Round N+1
│  └─ N = max_rounds → Final report (Max rounds reached)
└─ all edits = no
   └─ Verification audit (no Critical/Major) — logged as this round's "### Verification audit" subsection, not a new round
      ├─ clean → Final report (Converged); verification Findings become Remaining Minor findings
      └─ issues found → one more round OR report as Partial
```

## Relationship to child skills

| Child skill | Scope within this loop |
|-------------|------------------------|
| audit-skill | Phase 1 only; owns Critical/Major static fixes |
| empirical-prompt-tuning | Phase 2 only; owns executor-verified behavior fixes |
| skill-optimizer | Phase 3 only; owns activation/salience/context after measured signal |

This loop **does not replace** child skills—it sequences them. Do not duplicate their checklists here; read them each phase.
