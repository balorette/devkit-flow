# Slice 15 — Behavioral predictions

**Slice:** 15 — degradation is recorded, not absorbed
**Design:** [`docs/design/0010-degradation-is-recorded.md`](../design/0010-degradation-is-recorded.md)
**Plan:** [`docs/plans/slice-15-degradation-is-recorded.md`](../plans/slice-15-degradation-is-recorded.md)
**Status:** predictions recorded, **unrun**
**Date:** 2026-08-24

---

## How to read this

Each prediction is written **before** the corresponding pack content is authored, per `CLAUDE.md` working principle 4. If behavior diverges from a prediction during the dogfood, **the pack content needs revision — not the prediction.**

**P2 blocks the slice.** The others revise it.

### P1 (G1) — a non-critical finding that gets fixed is re-gated

**Task:** `/feature-merge` on a feature where Gate 3 returns one *medium* finding. Accept it and fix it.
**Predicted:** Gate 3 re-runs after the fix, and its brief names the prior finding and the hunk that answers it. The reviewer returns a verdict on whether the mitigation achieves the property the finding named.
**Before this change:** the medium finding becomes a `SEC` row, the gate passes, and the fix is never reviewed.

### P2 (6b) — the pack never silently proceeds past a subagent that did not return  **(blocks the slice)**

**Task:** during `/build`'s red phase, cause the `tester` spawn to return nothing.
**Predicted:** the loop re-pings, then inspects the working tree for files the tester may have written, and reports what it found before doing anything else. It does **not** write the tests itself without saying that it is doing so.
**Before this change:** no text covers this; the behavior is whatever the operator improvises.
**If this fails, clause 6b is decoration and must not ship.**

### P3 (6b) — a degraded run is surfaced at the merge proposal

**Task:** `/feature-merge` on a feature whose findings ledger carries a `DEG` row.
**Predicted:** the merge proposal halts, names which assurance was reduced and why, and proceeds only on explicit acknowledgement.
**Before this change:** the reduction is invisible at merge time.

### P4 (G4) — `/pr-review` produces two commits

**Task:** a `/pr-review` pass that amends the summary and writes a ledger row.
**Predicted:** two commits — artifacts, then `.claude/state.md` alone.
**Before this change:** one combined commit, which `/feature-merge` names as the shape that breaks the discriminator.

### P5 (G5) — a second pass skips the pack's own empty review submission

**Task:** run `/pr-review`, let it post an inline reply, then run `/pr-review` again.
**Predicted:** the empty-bodied review submission the reply created is skipped as content-free, and the skipped count is reported.
**Before this change:** it satisfies neither skip condition and is offered as a new review item.

### P6 (clause 4 swept) — documenter will not assert an unverified quantifier

**Task:** ask `documenter` to record *"every current caller is safe"* in a summary, without having searched.
**Predicted:** it searches and cites `file:line`, or it marks the claim inferred. It does not propose the bare sentence.
**Before this change:** the claim passes through the proposal unchallenged — observed, and merged.

### P7 (#6) — the merged-state check reads the recorded PR

**Task:** `/feature-merge` from a branch whose own PR differs from `state.md`'s `PR:`.
**Predicted:** the recorded PR is queried; the feature's real state decides the path.
**Before this change:** an argument-less `gh pr view` inspects whatever PR belongs to the current branch.

---

## Task 14 measurement — can skills come under `test_clause_one`?

**Answer: no, not by widening the section split.** Recorded here so it is not re-measured.

`pack_documents()` already globs `skills/*/SKILL.md`; what is scoped to commands is `phase_sections()`, which for a skill splits only on `Phase|Gate` headings. Widening it to split skills on `###` — the same treatment commands' `## Run` subsections get — flags **16 sections, of which 6 are real**: a 38% true-positive rate against the commands' 3-of-4.

The file's own standard rejects that: *"a guard that cries wolf is a guard that gets an allowlist, and an allowlist here is the cached-discovery failure clause 3 forbids."*

**Why the rate is structurally different, and not a tuning problem.** A command's `## Run` subsections are *steps* — they execute in order and each one does something. A skill's `###` subsections are a mix of procedure and reference material: `documenter`'s *The shape* describes a table's columns, *Two rules* states a policy, `pm`'s *The research phase* describes an activity with no durable output. Those are not under-declared steps; they are prose about artifacts, and a write-verb-plus-durable-target heuristic cannot tell them from steps because the prose legitimately names both.

### The six true positives are a real finding, and they are not fixed here

| File | Section | Writes, undeclared |
|---|---|---|
| `documenter` | *Pattern A — User-described change* | the amended spec / plan / ADR |
| `documenter` | *Pattern C — Park transition* | `.claude/state.md`, the parked entry |
| `documenter` | *Pattern D — On-demand reconciliation* | whatever the reconciliation applies |
| `documenter` | *Domain doc updates* | `docs/domains/<domain>.md` |
| `pm` | *4. Draft the spec* | the spec |
| `pm` | *Producing the plan* | the plan |

**This is errata F3's shape, in the two skills that write the most.** F3 was the `engineer` skill writing a findings-ledger row that no substep staged, which halted `/feature-merge` on its own clean-tree precondition. Every command that derives a staging list from `**Writes:**` declarations — `/feature-start` Phase H, `/plan` Phase G, `/feature-merge`'s closeout — is blind to these six.

It is **clause-1 work, not ADR-0010 work**, and it is recorded rather than done because a measurement task that quietly grows six sections of new text is the scope creep the pack forbids elsewhere. Recommended as the next slice item, or as a task appended to this one deliberately.
