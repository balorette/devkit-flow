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

---

## Carried over from slice 11 — still unrun

Recorded here because slice 11's predictions were never run and would otherwise be lost behind slice 12's. Neither is a slice-12 finding; both are open questions slice 12 inherits.

### Prediction T18a — clause 2's discriminator runs no gates on an unchanged PR

Reopen the Enterprise API PR, change nothing, re-run `/feature-merge`.

**Predicted:** the content diff against `Gated baseline` is quiet and **no gates run** — no tests, no docs reconciliation, no fresh-context security review.

**Why it still matters:** this branch has been unreachable since `Gated baseline` was introduced, because writing the baseline commits it and a SHA comparison could therefore never match. ADR-0008 called this the highest-value thing for a dogfood to exercise, and it remains unexercised. Slice 12 changed the rerun path around it (the two-commit ordering), so the prediction now covers both.

### Prediction T18b — the drift hook's unexplained miss

**This is a lead, not a finding.** During the 0.11.0 run, `/feature-merge` Gate 2's `owned_files` check caught two files edited outside the active spec's declared scope (`show_flights.py` and `CLAUDE.md`) that the `PostToolUse` drift hook did not warn about.

**Predicted:** editing a file outside the active spec's `owned_files` produces a visible warning at edit time.

**If it does not:** the hook has a real gap, and the cheap layer of drift detection is not working — leaving the expensive layer (the merge gate) as the only one. Nobody yet knows whether this was a hook defect or output lost in a long session, and that distinction is the whole point of running it.

---

## Findings → task → prediction

Every finding from both rounds, what closed it, and what would confirm it. **"—" in the prediction column means the fix is authored by reading and has no behavioural check in this slice.**

| # | Finding | Sev | Clause | Closed by | Prediction |
|---|---|---|---|---|---|
| flow-6 | Plan signatures authoritative, unverified | high | 4 | T1 — `/plan` Phase F3 | **T1** |
| flow-7 | `/build` verify omits the project's real gates | high | 3 | T2, T3 | **T2, T3** |
| flow-1 | Phase H staging omits the Phase E `CLAUDE.md` write | med | 1 | T5, T6 | `test_clause_one` |
| pr140-3 | Gate-rerun row commits `state.md` only | high | 1 | T5, T6 | `test_clause_one` |
| pr140-un | `MIGRATIONS.md` paragraph replacement deletes silently | — | 1 | T7, T9 | `test_migrations_snapshot` |
| flow-4 | `/plan` precondition vs an occupied namespace | med | 3 | T8, T9 | — |
| pr140-5 | `adr-registry` cannot re-read its recorded location | med | 3 | T10 | — |
| pr140-6 | `architect` missing-input contradiction | med | 3, 5 | T10 | — |
| pr140-7 | Build-time ADRs never linked from spec or plan | med | 3 | T10 | — |
| flow-5 | Phase F2 has no branch for "the advisory was fixed" | low | 5 | T13 | — |
| flow-8 | Tester findings framed as an error path | med | 5 | T13 | — |
| pr140-2 | Merged-state check ordered after a failing precondition | high | — | T14 | **T14a** |
| pr140-1 | `in-review` sync check is one-directional | med | — | T14 | **T14b** |
| pr140-4 | `in-review` precondition ignores untracked files | high | — | T14 | **T14c** |
| flow-2 | Stale slice-2 simulation note | low | — | T15 | — |
| flow-3 | `install.sh` restart guidance over-warns | low | — | T15 | verified during the 0.11.0 run |
| flow-9 | Three-strikes not generalized to process defects | low | — | T15 | — |

**Seventeen findings, seven behavioural predictions, three mechanical guards.** The gap between those numbers is the honest state of this slice: most of it is authored by reading, exactly as slices 8, 9, and 11 were, and the dogfood is what converts it.

## Two things that caught defects during authoring

Worth recording because both were machinery the pack already had, working on the slice that was extending it.

- **`test_migrations_snapshot.py` (slice 11) caught a clause-1 violation in slice 12's own plan.** The plan sequenced the `MIGRATIONS.md` entry into Task 17 while the seeded-template change was in Task 9 — deferring a carrier two phases from its artifact, in the slice implementing clause 1. The guard went red the instant the template changed and would not go green until the entry existed. ADR-0008 was explicit that no test can verify an entry is semantically *complete*; what this one enforces is *timing*, and timing was enough.
- **`test_pack_references_resolve.py` caught a dangling path in `artifact-locations.md`.** The new reference used the brownfield target's real plans directory as a narrative example; in an installed file a backticked path reads as a pointer, and that directory does not exist in a target project.
