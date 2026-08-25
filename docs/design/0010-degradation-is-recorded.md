# ADR-0010: Degradation Is Recorded, Not Absorbed

**Status:** Accepted — plan not yet authored
**Date:** 2026-08-24
**Deciders:** [user], Claude (design partner)
**Evidence:** [`docs/validation/flow-execution-0.12.1.md`](../validation/flow-execution-0.12.1.md) gaps G1–G6 — the first execution of `/pr-review`, `/feature-merge`'s `in-review` re-entry, and closeout. Every quotation re-verified against `pack/` source before this ADR was written.
**Extends:** [ADR-0008](0008-step-invariants.md) and [ADR-0009](0009-declared-writes-and-verified-authority.md) — cited throughout, not amended.

---

## Context

The 0.11.0 run retired the "no pack command has executed" caveat for the **build** lifecycle. This round retires it for the **review-and-closeout** half: `/pr-review` across all three comment surfaces, an `in-review` gate rerun, and a closeout on a forge that deletes the head ref. Those three bodies of text were the largest never-run region in the pack, and four of `pr140-pack-findings.md`'s seven findings live on them.

Six gaps. Two standing predictions passed (T18a, T14a) and five behaviours are recorded as working, so this is not a round where the flow failed — it is a round where the flow **shipped something wrong while reporting that it had not.**

### The gap that names the ADR

Gate 3 found a real TOCTOU. It recommended a locking read and cited the repository's own precedent for it — a good finding, well-grounded. The fix was implemented, passed all four of the project's gates, and **did not close the race**: the reviewer had checked `expire_on_commit=False` and never asked about `populate_existing`, so the ORM returned the identity-map-resident object for the `SELECT … FOR UPDATE`. Lock taken; stale attributes read.

Nothing in the pack looked at it again, because `feature-merge.md:157` mandates a Gate 3 re-run only for **critical** findings, and this one was not critical. An external reviewer caught it.

### The shape no existing clause covers

Three of the six gaps are one sentence:

> **A guarantee that degrades does not announce it — so the record keeps asserting the undegraded version.**

- **G1.** Gate 3's verdict stopped covering the diff the moment its own recommendation was implemented. The gate accounting still read *clean*.
- **G2.** The fresh-context TDD guarantee was void the moment the main loop wrote the tests, because the `tester` had not returned. The summary still read *tests written in fresh context*.
- **G6.** A claim in a durable doc carried no verification. The sentence still read as a fact, and merged.

In each case the assurance kept its full-strength **name** after the thing that produced it stopped covering the thing it names. ADR-0008's clauses are about *what a step does*; ADR-0009's are about *what a step declares and verifies*. Neither covers *what happens to an assurance after the conditions it was computed under change* — which is a property of the record, not of the step.

### Two facts that sharpen the diagnosis

**Fresh context is what hides G1.** `security-reviewer.md:9` makes fresh context load-bearing for objectivity: the reviewer must not have absorbed the implementer's justifications. That same isolation means a reviewer re-invoked on the `in-review` path sees the recommended pattern in the diff and reads it as the mitigation — it cannot know the hunk exists *because Gate 3 asked for it*. So the existing rerun branch at `feature-merge.md:24` does not close G1 even where it fires. **Reviewing a diff and grading your own prior recommendation are different tasks**, and the pack has text for only the first.

**The pack states G2's rule already — on the wrong side of the call.** `architect.md:24`: *"**Silence is not an input.** An explicit 'none found' is a complete answer and you proceed on it; nothing at all is a *missing* answer and you ask for it."* That is the callee's obligation. The caller-side mirror — *silence from a subagent is not evidence that it died* — is nowhere, and the run cost was a thirty-minute-late `tester` whose work had already been superseded, plus a fresh-context guarantee quietly spent.

---

## Decision

### Clause 6 — An assurance that can stop holding says when, and a degradation is recorded rather than absorbed

Three obligations, all falling out of the one sentence:

**6a — Re-gate what the gate caused.** Re-run Gate 3 after **any** accepted finding is fixed, regardless of severity. The severity threshold belongs to *blocking the merge*; it has no business deciding *what has been reviewed*. And when the re-run is grading the pack's own prior recommendation, say so in the brief: pass the finding and the hunk that answers it, and require an explicit verdict on **whether the mitigation achieves the property the finding named** — not whether the code resembles the recommendation. `security-reviewer.md:30`'s *"recommend a narrow fix"* earns its companion: a narrow fix is checked against the property, not against the recommendation.

**6b — A subagent that does not answer has a named protocol.** Re-ping; then check the working tree, because a subagent that wrote files and failed to report has still done the work; then decide. `ListAgents` reporting nothing reachable is not evidence of death. If the main loop proceeds without the subagent, the assurance that subagent provides is **reduced**, and the reduction is written to the findings ledger — not the summary alone. `/feature-merge`'s own argument for the ledger (`feature-merge.md:156`) is that *"the summary is a document nobody reopens"*, and *"this feature's tests were not written in fresh context"* is exactly what a later feature needs to know.

**6c — One writer per file, including during degraded mode.** While a subagent may still be live, the main loop does not write into that subagent's declared output set. If it must, the collision is reconciled and reported — never silently overwritten in either direction. In the observed run the `tester` handled the collision on its own judgment, with nothing instructing it to; that is a lucky outcome, not a designed one.

### Clause 4, swept — the verification pass reaches the component that writes docs

**G6 needs no new clause.** It is ADR-0009 clause 4 (*an artifact declared authoritative has a verification pass*) implemented for exactly one artifact type — plan type signatures, `/plan` Phase F3 — and clause 5's § *Facts* never wired into the component that writes every other durable artifact.

`documenter`'s cardinal discipline is *propose before writing* (`SKILL.md:14`). That asks whether to write it, **not whether it is true.** Its single citation of `evidence-and-uncertainty.md` (`SKILL.md:18`) points at § *Judgment*; it never cites § *Facts*.

So: `documenter` gains a verification substep before any proposal ships. Every load-bearing factual claim is backed by `file:line` or explicitly marked inferred, and a claim quantified over the codebase — *every caller*, *no other path*, *all consumers* — is verified by search or is not written in that form.

This is the fourth independent finding to reach the same recommendation (`flow-execution-0.11.0.md` finding 4 reached it for clause 3): **sweep the clause across the places it holds, rather than patching the site a review happened to name.**

### Two point fixes, no clause

- **G4** — `/pr-review` Phase D stage 4's single metadata commit contradicts `/feature-merge`'s two-commit rule, which exists precisely because the discriminator excludes only `.claude/state.md`. `/pr-review` splits **unconditionally**: artifacts commit, then `.claude/state.md` alone. A conditional is the version that gets read wrong under pressure, and the cost of the unconditional rule is one extra commit on a metadata-only change.
- **G5** — a third skip condition in `/pr-review` Phase A: **an item with an empty body carries no finding.** An empty review submission is a container for inline comments, not a finding; a bare `APPROVED` likewise. Content-free by construction, so the filter cannot drop a real item, and it closes the recursion on every surface at once — where the two prior fixes each closed only the level in front of them.

---

## What the clauses decide

| Gap | Clause | Net change |
|---|---|---|
| G1 | 6a | `/feature-merge` Gate 3 re-run rule; `security-reviewer` gains a *grading your own recommendation* brief |
| G2 | 6b | A degraded-mode section; the reduced assurance recorded as a ledger row |
| G3 | 6c | Single-writer rule inside the degraded-mode protocol |
| G6 | 4 (swept) | `documenter` verification substep; § *Facts* cited where docs are written |
| G4 | — | `pr-review.md` Phase D stage 4 splits unconditionally |
| G5 | — | `pr-review.md` Phase A third skip condition |

---

## The operator's bias note, and why it does not change the decision

The round was reported with a caveat worth preserving:

> Items 1, 2 and 6 are all cases where the pack's assurance was weaker than its confidence, and in each case I was the one who reported the inflated version to you. So they may say as much about how I use the pack as about the pack itself — 1 and 6 in particular would have been caught by a more skeptical operator.

The observation is right; the inference is too generous to the pack. **A discipline that holds only when the operator is skeptical is not a discipline; it is a mood.** The anti-rationalization tables throughout `pack/` exist because the authors assumed a tired reader rather than an ideal one, and G1 and G6 are exactly the cases where by-construction guards work: re-running a gate and grepping for a caller are both mechanical, and neither depends on anyone being suspicious at the right moment.

What the note does establish is a real correction, on the reporting side rather than the guard side: **the operator reported the inflated version because nothing required them to report the degradation.** That is clause 6b's second half, and it is why the reduction goes to the ledger rather than being left to whoever remembers to mention it.

---

## Consequences

**Gate 3 gets more expensive.** Every accepted finding now costs a fresh-context security pass. Accepted: the alternative is what this round produced — a mitigation that did not mitigate, shipped with a clean gate record. The cost is bounded by the number of findings the user chooses to fix, which is small in practice and is precisely the set most worth re-reviewing.

**Degraded mode makes a failure visible that used to be invisible.** A run where a subagent died will now carry a ledger row saying so. That is the point; it will also make the pack look less reliable in exactly the runs where it was less reliable, which is honest.

**`documenter` gains a round-trip on claims.** Its cardinal discipline already costs one round-trip per amendment; this adds verification work before the proposal, not another confirmation. The failure it prevents merged a false claim into a durable doc on the first run that could have produced one.

**Clause 6 is a property of the record, not of a step**, which makes it harder to enforce by construction than clauses 1–5. `tests/test_clause_one.py` can check that a declared write is staged; no test can check that an assurance still holds. This clause is enforced by text and by the ledger row, and that limitation should be stated plainly rather than designed around.

## Relationship to slice 13

Neutral, and worth saying because the previous two rounds both moved it. G1 is not a cross-step semantic miss — it is a scope defect inside one gate's own rule, which a pre-PR `reviewer` covering cross-step lenses would have no special claim to catch. G2 and G3 are not review-findable at all; they required a subagent to actually fail.

What this round does reinforce is the ordering the errata settled: **execution first.** Four review rounds and eighteen findings against slice 12 missed all five errata findings; this round found six more, three of them by absence — and reading is structurally poor at absence, because nothing on the page draws the eye to a sentence that was never written.

## Relationship to slice 14

Slice 14's three unbuilt defects stand. *(As built: slice 15 shipped all three in 0.13.0. The sentence records the position at decision time; the disposition is here so the claim does not outlive it.)* Note that **#6** — the merged-state check querying the current branch rather than `state.md`'s `PR:` — lives on the closeout path this run traversed successfully. It succeeded because the branch happened to be checked out, which is exactly the condition that hides it.
