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

**Third check (added after the PR #4 review).** Give the plan a signature block naming `Config`, in a project where `Config` is defined somewhere unrelated. **Predicted:** UNRESOLVED, naming the module mismatch — not RESOLVED against the unrelated definition. The first version of this phase claimed a plain identifier search was enough and that *"a false 'resolved' is not possible"*; that claim was wrong, and a common identifier is exactly where it fails.

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

---

## PR #4 review round (2026-08-12)

Two automated reviewers — Cursor Bugbot and Codex — on commit `51d2510`. **10 raw findings → 9 unique** (C1 and X3 are the same defect reported by both). **All nine verified against source and all nine real; none pushed back on.**

### The theme

**Five of nine are one root cause: the clause-3 sweep shipped consumers without a producer.** `artifact-locations.md` was written, 34 sites were rewritten to cite it, and nothing ran it. See ADR-0009 § *A citation is not a wiring*.

That matters more than the individual fixes, because it says something the slice's own thesis missed: a rule can be swept *and still not wired*. The citations resolved, `test_pack_references_resolve` was green, `test_clause_one` was green, and flow-4 was not closed.

### Disposition

| # | Reviewer | Finding | Fix |
|---|---|---|---|
| C2 | Cursor high | Artifact discovery never runs | `pm` Orient + `/feature-start` Phase A + `/plan` Phase A run § *Discover*; `/adopt` records homes |
| X1 | Codex P1 | No default when discovery finds nothing | § *Default* — `docs/{specs,plans,summaries}/`, no confirmation for an unoccupied namespace |
| X5 | Codex P2 | Exemplar scans read hardcoded dirs | Both scans read the discovered homes |
| X2 | Codex P2 | § *Record*'s `CLAUDE.md` write not carried | Declared in Phase A, so the derived carrier commits it |
| X6 | Codex P2 | Summary path not persisted | New `state.md` `Summary:` field + migration entry |
| C3 | Cursor med | Halt list still one-directional | Matches precondition 2 in both directions |
| X7 | Codex P2 | Merged-state jump skips clean-tree check | Remote comparison skipped; clean tracked tree still required before `git checkout <mainline>` |
| C1/X3 | Both | `Writes:` declaration inside a fenced template | Declaration moved out **and `test_clause_one` made fence-aware** |
| X4 | Codex P2 | Phase F3 false-RESOLVEs on common identifiers | Definition-site resolution at the attributed module |

### What this round says about the guards

- **`test_clause_one` passed for the wrong reason** and now cannot: fenced blocks are templates the command emits into someone else's file, so their content is not a declaration and their headings are not phase boundaries. The fence-aware version went red naming exactly `adopt.md` Phase C.
- **No existing guard could have caught C2.** The citation resolves, so `test_pack_references_resolve` is satisfied; nothing goes unwritten, so `test_clause_one` is satisfied. The gap between *a reference that exists* and *a reference that is reached* has no mechanical check. **This is now the strongest argument for slice 13's `reviewer` gate.**
- **X4 was a false claim I wrote**, not an omission: *"a plain identifier search is enough — a false 'resolved' is not possible."* Clause 5 applies to the pack's authors as much as to the pack.

---

## PR #4 review round 2 (2026-08-13)

Cursor Bugbot on commit `cd1d46d` — the round-1 fix commits themselves, reviewed two minutes after the round-1 replies were posted. **4 findings, all verified against source, all real.** Codex did not re-review.

### The theme

**Round 1's fix was partial in the shape round 1 was fixing.** C2 said artifact discovery never runs; the fix wired § *Discover* into three call sites and closed it. Round 2 found that § *Confirm* still had no invoker anywhere on the feature path, § *Record* had none outside `/adopt`, and `/feature-start` Phase A still declared a `CLAUDE.md` write no step performed. See ADR-0009 § *A partial wiring reads as a complete one*.

That is the second consecutive round where the defect recurred inside the correction written to close it. Worth stating plainly: **naming a rule is not implementing it, and this pack has now produced that evidence twice in two rounds against itself.**

### Disposition

| # | Reviewer | Finding | Fix |
|---|---|---|---|
| C5 | Cursor high | § *Confirm* / § *Record* never invoked on the feature path | `artifact-locations.md` gains § *Resolve* — one chain, one entry point; four call sites invoke it as a unit |
| C4 | Cursor high | `/plan` Phase A ran discovery after its exemplar-scan consumers | Phase A reordered: `CLAUDE.md`, then both discoveries, then the reads that consume them |
| C6 | Cursor med | Phase H staging enumeration omits Phase A's new write | `/feature-start` Phase H and `/plan` Phase G name **the phases to read**, not the files to stage |
| C7 | Cursor med | 0.12.0 seeds `Summary:` blank against `/pr-review`'s hard stop | Migration entry gains a backfill step naming the pre-0.12.0 undated filename |

### Found while fixing, not reported

**`/feature-merge` never ran artifact discovery at all.** It writes the summary at "the location § *Discover* returned" (`:151`) and had no discovery step in its own invocation — C2 exactly, in a fifth site neither reviewer flagged in either round. It matters more than the count suggests: `/feature-merge` is the pack's **only** summary producer, so no earlier command settles that directory on its behalf, and the path it writes is the one `/pr-review` later hard-stops on. C7 and this are the same defect seen from the two ends.

It now resolves in an Orient step ahead of the gates — placed there rather than beside the write so the user is never asked to settle a directory during closeout for a feature Gate 1 is about to send back.

### What this round says about the guards

- **Both round-2 high findings are clause 3 again**, and neither `test_clause_one` nor `test_pack_references_resolve` moved. The suite was green at 44 before the round and is green at 44 after. A test count is not a coverage claim.
- **The structural fix is new and is the part worth keeping.** A reference whose sections form a chain now names the chain. `adr-registry.md` was checked and does *not* need this — its sections are separate operations at separate times, so subset-picking there is correct. That distinction is recorded in ADR-0009 so the next reference is written on the right side of it.
- **`/plan` Phase G's enumeration had cited itself as the one that got it right** — "this list was correct and the equivalent list in `/feature-start` was not" — and had decayed within the same slice. Both now derive. An enumeration that documents the danger of enumerations is still an enumeration.
- **Two consecutive rounds, both closed by reasoning, neither by execution.** Everything in slice 12 that has run is `test_clause_one`, `test_migrations_snapshot`, and `test_pack_references_resolve`. The behavioural predictions above remain unrun, and the `/feature-merge` Orient step added here is new unexecuted text on the `in-review` path that has still never executed.
