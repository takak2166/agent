---
name: my-grill-me
description: Stress-tests a plan or decision through a classified design-tree interview (look up facts, park empirical forks, ask only preference questions). Use when the user runs `/my-grill-me`, attaches this skill, or a parent skill delegates by Read-and-follow (e.g. product-requirements). Does not implement until the user explicitly asks.
disable-model-invocation: true
---

# My Grill Me

Stress-test a plan, decision, or idea through structured questioning until **shared design understanding** is confirmed. Do not implement the interview subject during this skill.

## Usage

```
/my-grill-me
```

Run when any of these applies:

- The user explicitly attaches this skill or invokes `/my-grill-me`.
- A **parent skill** (for example **`product-requirements`**) explicitly delegates by instructing the agent to **Read** and follow this `SKILL.md` — treat that as invocation; do not wait for `/my-grill-me` or a separate attach.

If the same turn also asks to implement something, grill first and do not implement.

The interview **subject** is the plan, decision, or idea in the user's message. If none is given, ask once via the question tool what to stress-test, then begin the design tree.

## Non-negotiables

1. **No action until asked** — do not implement, edit, or otherwise act on the plan until the frontier is empty, the user confirmed shared understanding, **and** they later asked to implement.
2. **Classify before you ask** — every frontier item is look-up, empirical, or preference (see **Classification**). Only **preference** goes to the question tool.
3. **Design tree** — every decision branches into the decisions that hang off it. A question that depends on another question still open in this logical round belongs to a later round.
4. **Structured questions first** — deliver every preference-frontier question through the runtime question tool when it exists.
5. **Lookups and parks do not stall the rest** — an in-flight fact lookup or a parked empirical item only blocks questions that depend on it. Ask the rest of the preference frontier now.

## Classification

Classify each frontier item **before** adding it to a question-tool payload. Stop at the first matching class.

| Class | Test | Action |
|-------|------|--------|
| **Look-up** | The answer exists in the repo, docs, git history, MCP, or a cheap **read-only** command (how it works today, a type, whether a caller exists, current timing of an existing path) | Look it up (tools / sub-agents). Do not ask. |
| **Empirical** | Running, measuring, or a throwaway sketch could settle it (behavior, timing, layout, output, perf, whether two approaches actually differ) | Do **not** ask as if the user knows. Do **not** prototype or implement during this skill. **Park** it: what to observe later, and which later decision it unlocks. |
| **Preference** | No experiment can settle it (taste, priority, risk appetite, who it is for, what "done" means, which users to serve) | Ask via the question tool. |

A look-up of external state that can change during the interview (PR status, CI runs, issue state, scheduled jobs) goes stale: re-read it right before the preference question that depends on it. If the fresh read makes that decision moot (for example the PR is already merged), record the dropped question and the settling state under **Looked-up facts** this round (Expected output item 2) and omit the question; if only a premise changed (for example CI passed but the release call is still open), rebuild the question and options from the fresh read instead of dropping it. This check updates the question payload only; it is not a mid-round recompute of the design tree (Restrictions).

When class is unclear: try a cheap look-up first. If it is still unsettleable without a product call, class **preference**. Do not default to asking.

Running **existing** code, tests, or traces to learn the current system is look-up. Building a **new** sketch to decide a fork is empirical — park it.

### Integrated example

**Subject:** add virtualization to a slow list.

| Candidate question | Class | What happens |
|--------------------|-------|----------------|
| Does the list already virtualize? | Look-up | Read the list code. Do not ask. |
| Would windowing cut load from ~1s to ~200ms? | Empirical | Park: measure after the grill. Do not ask; do not build a sketch now. |
| Is ~200ms good enough, or must it feel instant? | Preference | Ask via the question tool. |

## Expected output

**Each logical round (in order):**

1. Short **settled decisions** list (bullets).
2. **Looked-up facts** this round (one line each) and **parked empirical** items (what to observe later, what it unlocks). Omit a subsection when empty.
3. One or more structured-question tool calls covering the **preference** frontier only (batched only when the tool caps questions per call).
4. No implementation, edits, prototypes, or other action on the interview subject.

**Session end (preference frontier empty):**

1. Summary of all settled decisions, plus remaining parked empirical items (settle those by observation after the grill, not by asking now).
2. One confirmation question via the question tool (or markdown fallback) with exactly two choices: shared understanding reached, or holes remain. Do **not** offer implement.
3. Stop and wait.

## Design tree

Work in **logical rounds**. The **frontier** is every **preference** decision whose prerequisites are already settled. Look-ups and parks are not frontier questions; they only delay preference items that depend on them.

Each user answer reshapes the tree: settled decisions push the frontier outward. Recompute the frontier only after **every** question from the current logical round has an answer (including all tool-limit batches).

Session is done when the preference frontier is empty and the user confirms shared understanding. Parked empirical items do not keep the session open.

## Question delivery

Deliver preference-frontier questions per [`reference/question-delivery.md`](reference/question-delivery.md). Each round: follow **Expected output** above.

## Session end

When the preference frontier is empty, follow **Expected output** → **Session end** (confirmation question only; do **not** offer implement). If holes remain, recompute the frontier and continue. Implement only on a later explicit request.

## Additional resources

- Question tools: [`reference/question-delivery.md`](reference/question-delivery.md)

## Restrictions

- Do not implement, edit, or prototype the subject of the interview while this skill is running.
- Do not ask the user for look-up-able facts or empirical / observable forks.
- Do not recompute the design tree mid-round.
- Do not add a duplicate Other option.
- Do not start this workflow from ambient chat unless the skill was explicitly attached, `/my-grill-me` was used, or a parent skill delegated by **Read**-and-follow as in **Usage**.
