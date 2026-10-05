# Reflect — reference

Condensed from pstack Chapter 33 ([Reflect on what the work taught you and apply it](https://zenn.dev/sc30gsw/books/7ff701b9811d04/viewer/7c5f9e)). Structural routing defers to always-on **instruction hygiene** (`.apm/instructions/instruction-hygiene.instructions.md` — **Encode lessons in structure**), not a separate pstack principle skill.

## Reviewer lenses

Run each lens independently before synthesis.

### Judgment

Looks for **durable principles** behind events—not the event itself.

Examples:

- User corrected the same assumption twice → principle about verifying before claiming done
- Agent chose a large refactor when a minimal diff was enough → laziness / scope principle

Reject: restating the ticket title, repeating a skill step verbatim without a new invariant.

### Tooling

Looks for **concrete rediscovery cost**: commands, flags, paths, env vars, MCP tools, `gh`/`jq` patterns the next agent would hunt again.

Examples:

- Found working incantation only after trial → add to the relevant skill **Usage** or Steps
- Wrong default path → fix named path in skill

Reject: pinning volatile facts (`linter at commit bd91aa7 uses chars/4`)—**Durability** failure.

### Divergent

Looks for what the other lenses miss:

- Decision that worked for the **wrong reason** (test passed accidentally)
- Skill was attached but **ignored**—for auto-discovered skills, fix activation (`description` / Usage); for **`disable-model-invocation: true`**, fix **Usage / Steps** only (no discovery WHEN in `description`)
- Verification gap—lesson belongs in **verification** instruction or consumer verification skill, not narrative

## Candidate fields

| Field | Requirement |
|-------|-------------|
| **Principle** | One sentence; must change a future decision |
| **Evidence** | Pointer to moment in transcript or chat |
| **Destination** | Existing skill dir, `.apm/instructions/…`, or Backlog |

## Synthesizer criteria

Apply to each candidate. **Reject** when any critical check fails.

| Criterion | Accept when | Reject example |
|-----------|-------------|----------------|
| **Durability** | Still true in a new session/repo state | Commit SHA, version-specific bug, today's temporary workaround |
| **Actionability** | Changes what the agent does or checks | Vague "be careful" |
| **Generalization** | Pattern, not a single accident | One flaky network blip |
| **Evidence** | Tied to a cited moment | Hypothetical risk |
| **Destination fit** | Skill was used or should have been; rule belongs in always-on only if cross-cutting | Putting app-specific steps in global instructions |
| **Non-duplication** | Not already in always-on rules or linter | Third copy of "use jq for JSON" |
| **Structure first** | If enforceable mechanically → **Backlog**, not Accepted prose | "Never import X from Y" without lint |
| **Proportionality** | Change size matches lesson | Ten-line essay for a one-flag fix |
| **Decision-changing** | A future agent **does** something different | Extra prose that does not change behavior |
| **Skill was used** | Body edit targets a skill/MCP the session **actually invoked** | Skill existed but was not used → **`description` / Usage** fix, not duplicate workflow elsewhere; if neither applies → Reject **`skill-not-used`** |
| **Already covered** | After **Read** of destination skill, guidance is missing or buried | Clear, well-placed duplicate → Reject **`already-covered`** (execution, not text); weak placement → Accepted as wording/placement fix only |
| **Existing-skill-first** | One line in an existing skill suffices | **New skill** only when no home exists, pattern recurs, topic deserves its own skill — else Backlog or Reject |
| **Convergence** | Two or more lenses echo the same lesson | Singleton finding must pass other criteria with a higher bar |

Discard **acknowledge-only** learning ("I'll remember")—convert to **Accepted** only with a concrete edit or **Backlog** with an owner.

**Reject reason tags** (one per row): `durability` | `actionability` | `generalization` | `evidence` | `destination-fit` | `duplicate` | `structure` | `skill-not-used` | `already-covered` | `existing-skill-first` | `convergence` | `decision-changing` | `proportionality`.

## Anti-patterns (do not emit as Accepted)

1. **Acknowledge without recording** — no file change and no Backlog item
2. **Record without routing** — note in chat but no skill/rule/ticket
3. **Fix one instance only** — patch one call site when the lesson is repo-wide (generalize or Backlog lint)
4. **Skill sprawl** — new skill when one line in an existing skill suffices
5. **My-reflect instead of hardening** — execution failures on a known skill → **`skill-hardening-loop`**

## Backlog item template

```markdown
Title: [structure] <short invariant>

Body:
- Lesson from my-reflect (evidence one line)
- Proposed enforcement: lint | script | CI | type | runtime check
- Out of scope for Skill text because: …
```

## Output quality bar

Approve only proposals the user would want **every future agent** to follow—not nitpicks, not stylistic preference unless it repeatedly caused rework.

Step 5 **Accepted** rows must use **`1.` / `2.` / …** numbering so the user can approve with `1`, `1 and 3`, etc. Do not rely on `- [ ]` checklists alone for approval routing.
