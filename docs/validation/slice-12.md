# Slice 12 — Behavioral predictions

**Slice:** 12 — declared writes, discovered locations, verified authority
**Design:** [`docs/design/0009-declared-writes-and-verified-authority.md`](../design/0009-declared-writes-and-verified-authority.md)
**Plan:** [`docs/plans/slice-12-declared-writes-and-verified-authority.md`](../plans/slice-12-declared-writes-and-verified-authority.md)
**Status:** predictions recorded, **unrun**
**Date:** 2026-08-12

---

## How to read this

Each prediction is written **before** the corresponding pack content is authored, per `CLAUDE.md` working principle 4. If behavior diverges from a prediction during the dogfood, **the pack content needs revision — not the prediction.**

The dogfood target is Enterprise API, which has an open PR (#141) from the run that produced slice 12's findings.

---

### Prediction T1 — Phase F3 halts on an unresolvable symbol

**Setup:** A plan whose Step 2 signature block names `CaseLayout` where the codebase defines `ReconciliationCaseLayout`, and whose conventions table names `build_manifest_conflict_detail` where the codebase defines `manifest_409_detail`.

**Predicted:** `/plan` reaches Phase F3, reports both names as UNRESOLVED with the near-miss suggestion for the first, and does **not** proceed to Phase G's commit proposal until the plan is corrected. The conventions-table name is caught, not just the signature-block one.

**Why this is the prediction that matters:** the mid-feature partial fix during the 0.11.0 run covered signature blocks only, and instance five was in the conventions table. A Phase F3 that catches four of five is the same defect relocated.

**Secondary check:** a plan that names a symbol it *introduces* must not halt. The phase's whole output is the distinction between a deliberate new name and a wrong one.

---

### Prediction T2 — the build loop runs the project's fourth gate

**Setup:** A project whose `CLAUDE.md` conventions record four blocking gates (ruff, a mypy total-count ratchet, pytest, `diff-cover --fail-under=85`). Run one `/build` step whose change lowers diff coverage below 85%.

**Predicted:** the step's Verify substep 3 runs all four recorded commands, the coverage gate fails **inside that step**, and the engineer fixes it with that step's code still in context — rather than the failure surfacing at `/feature-merge` Gate 1 across six steps of diff.

**Secondary check:** on a project with **no** recorded gate list, the loop infers and **says that it is inferring**. A silent inference is the failure this substep's rewrite exists to prevent, and it is indistinguishable from a recorded list to anyone reading the transcript.

---

### Prediction T3 — the plan carries the gate list to the loop

**Setup:** Run `/plan` on a project whose `CLAUDE.md` records a **Blocking gates** list.

**Predicted:** the written plan's *Approach* section contains those commands verbatim as the per-step verify command — not merely in a *Framework constraints* evidence table.

**Why:** on the 0.11.0 run the gate *was* captured at plan time, in the constraints table, with its caveat and its exact reproduction command. It never reached the loop. A constraint the loop does not read is a constraint the loop does not have.

---

### Prediction T14 — the `in-review` re-entry path

> **UNRUN, and slice 12 does not change that.** These three are authored by reading. The `in-review` re-entry path remains the largest body of never-executed text in the pack, and the dogfood that settles it is: reopen the PR, push a review fix from a second clone, re-run.

**T14a (pr140-2) — merged-state ordering.** On a forge that auto-deletes head branches, re-run `/feature-merge` after the PR merges.
**Predicted:** closeout runs and clears state.
**Before this change:** halts on precondition 2, because `git ls-remote` returns an empty result for the deleted ref and that reads as diverged.

**T14b (pr140-1) — tip equality.** Push a commit to the PR from a second clone, then re-run `/feature-merge` locally.
**Predicted:** halts, reporting that local is *behind* — naming the direction, not just the mismatch.
**Before this change:** passes, then gates stale local content while the discriminator reads the new remote tip.

**T14c (pr140-4) — untracked files.** Leave an unstaged new test file in the tree and re-run.
**Predicted:** surfaced and asked about before any gate runs.
**Before this change:** precondition passes, gates run green against a tree containing the untracked implementation, and the PR gets a `Gated baseline` it did not earn.
