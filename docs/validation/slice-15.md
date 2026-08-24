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
