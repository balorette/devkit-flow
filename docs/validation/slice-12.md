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

---

## PR #4 review round 3 (2026-08-13)

Cursor Bugbot on commit `be31756` — the round-2 fix commits — relayed by the owner. **4 findings, all verified against source, all real. Every one is a regression introduced by `9f21d8f`**, the round-2 fix commit.

### Disposition

| # | Finding | Sev | Fix |
|---|---|---|---|
| C8 | § *Discover* step 1 exits the whole scan on any `CLAUDE.md` record, against a chain § *Resolve* declares per-artifact-type | high | Step 1 and step 3 are per type; § *Record* states an entry claims nothing about the types it omits; three `**Writes:**` declarations rescoped | `65b647d` |
| C9 | `/feature-merge`'s largest producer carries no `**Writes:**` line, so the new derived closeout drops the summary | high | The producing section declares; the crutch enumeration is deleted; `test_clause_one` widened and three sibling declarations added | `df271d4` |
| C10 | `### Orient` sits outside `test_clause_one`'s scan, so deleting its declaration leaves the suite green | med | Closed by C9's widening, *before the finding was read*. Verified against C10's own stated test: stripping Orient's `**Writes:**` line now goes red naming exactly that section | `df271d4` |
| C11 | `/adopt` Phase A runs § *Resolve* in full — whose step 3 writes `CLAUDE.md` — while declaring `**Writes:** none` and deferring conventions to Phase D's propose-before-write | med | § *Resolve* step 3 gains a deferral branch (on *when*, never *whether*); Phase A holds the resolution, Phase D records it inside the proposal | `<this commit>` |

**C11 is the one worth not glossing.** `9f21d8f` changed `/adopt`'s bullet from "run § *Discover*, confirm per § *Confirm*, record per § *Record*" to "run § *Resolve* in full" — reading as a tidy-up, since the chain is what the old text spelled out. But § *Resolve* ends in a write, and `/adopt` is built so that every `CLAUDE.md` write lands in Phase D behind a proposal. Consolidating three named steps into one entry point moved a write across a confirmation boundary the entry point knew nothing about.

### What each one was

**C8 — an exit outliving its producer's granularity.** The § *Resolve* fix generalized § *Discover* step 1 from *"if `/adopt` recorded artifact homes"* to *"if artifact homes are recorded,"* because four commands now record. The exit was sound only by accident of the old producer: `/adopt` resolves all three types at once, so its records were always complete. The feature commands produce partial records **by design**, and against a partial record the unchanged exit skips § *Default* and § *Confirm* for every unnamed type — writing into an occupied `docs/plans/` without asking, which is the harm the reference was written to prevent, on the type its own anecdote names.

Both `/plan` and `/feature-merge` stated the contradiction in their own text and neither was reconciled against the exit they depend on.

**C9 — a derivation over an incomplete set of declarations.** The closeout was converted to derive from `**Writes:**` declarations and named four sections, one being the closeout itself — a carrier, not a producer — while the real producer of the summary, domain docs, and `Summary:` field declared nothing. Following the rule exactly drops the summary: the untracked-summary failure that section warns about, caused by the rule written to prevent it.

This is the C6 fix re-creating C6 in the third command. `/feature-start` and `/plan` had their enumerations **deleted**; `/feature-merge` kept one alongside the derivation as a crutch, and the crutch is what hid the missing declaration.

### The first guard that moved

`test_clause_one` matched `Phase N` / `Gate N` headings only. `/feature-merge` names its steps for what they do, so three producers sat outside the scan entirely — the suite's 44 passing tests were never evidence about them. A command's `## Run` now contributes all its `###` subsections.

The scoping was **measured, not guessed**: every-heading-everywhere flags 54 sections, nearly all `## Arguments` / `## Preconditions` prose that mentions writes performed elsewhere; `## Run`-scoped flags 4, of which 3 were real writes and the 4th now declares `**Writes:** none`. Verified red against `65b647d` naming all four, green after.

**This is the only guard that has moved in slice 12**, and the reason is worth keeping: C9 was *syntactic* — a heading that writes without a declaration. C2, C5, and C8 were semantic, and no regex expresses them.

### What three rounds say

Three consecutive rounds, each finding the previous round's correction carrying a defect of the same family:

| Round | Defect | Producer state |
|---|---|---|
| 1 | C2 — discovery never runs | never ran |
| 2 | C5 — § *Confirm* / § *Record* never invoked | ran partially |
| 3 | C8 — exit taken on behalf of unresolved types | ran correctly, exited early |
| 3 | C9 — derivation over a missing declaration | ran, declared nothing |

Each is harder to see than the last, and for the same reason each time: **more of the mechanism visibly works.** By C8, something runs, a location comes back, and the type that comes back is genuinely settled — it is the other types that hold nothing while a write site cites them as answered.

Recorded in ADR-0009 as *Widening a producer invalidates its consumers' exits*, *A derivation is only as strong as its declarations*, and *What three rounds say about sequencing slice 13*. The last of those is the substantive change: **every high-severity finding across three rounds landed in the cross-step semantic gap no component owns**, and the pack's own guards were green through all of them.

**A correction to how this was first written up.** The initial version of this section called round 3 owner-reported and said neither automated reviewer had surfaced it. Both claims were false: Bugbot posted all four findings against `be31756` at 12:28:39Z, and the owner relayed two of them. The error is worth leaving visible because it cuts against the argument it was attached to — the automated reviewers **did** catch every round, including this one, and what has consistently failed is the pack's own mechanical guards plus the authors' review of their own corrections. The case for the `reviewer` gate does not need external review to have failed; it rests on three consecutive rounds where an in-repo guard could not see the defect and the author could not either.

**Still true, and worth not losing:** the behavioural predictions above remain unrun, and everything in rounds 2 and 3 was closed by reading. `/feature-merge`'s Orient step, its four new declarations, and the whole `in-review` path are text that has never executed.

---

## PR #4 review round 4 (2026-08-13)

Cursor Bugbot on `b7ecfb6`. **1 finding, medium, verified real** — plus one unreported sibling found while fixing it. The check itself passed; the finding came as a comment.

| # | Finding | Fix |
|---|---|---|
| C12 | `/plan` Phase G describes Phase A's write as firing "only when nothing was recorded before" — the whole-record gloss C8 removed from Phase A, left behind in the carrier that reads it | Both carriers now say *conditional per artifact type* and warn against reading "a record exists" as "nothing to write" |

`/feature-start` Phase H carried the identical stale sentence and was not flagged; `/feature-merge`'s closeout was already per-type correct, having been written after the C8 fix rather than before it.

**The defect is a fix's blast radius, not a new rule.** C8 made § *Resolve* per-type and updated Phase A. Two carriers describing Phase A's behaviour in prose were not updated, and prose describing a declaration is not itself a declaration — so `test_clause_one` had nothing to say. The consequence is specific and plausible: on a `/plan` run where `/feature-start` already recorded specs, a carrier following the stale gloss treats a real plans-directory write as an anomaly and drops it from the staged commit.

### The trend across four rounds

**9 → 4 → 4 → 1**, with severity falling alongside: two high in round 2, two high in round 3, none in round 4. Four rounds is enough to say the rate is converging rather than stationary, which is the first evidence in this slice that the corrections are net-reducing defects rather than trading them.

It does not change what remains unvalidated. Every round so far has been closed by reading, and the behavioural predictions above are still unrun.

