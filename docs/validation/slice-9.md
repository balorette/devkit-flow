# Slice 9 — Validation Report

**Slice:** 9 (Astraeus findings — brownfield portability, slice-8 defect fixes, findings ledger + plan conformance)
**Designs:** [`0005-brownfield-portability.md`](../design/0005-brownfield-portability.md) · [`0003` § Corrections](../design/0003-pr-lifecycle-and-findings-triage.md) · [`0006-findings-ledger-and-plan-conformance.md`](../design/0006-findings-ledger-and-plan-conformance.md) · interim from [`0007`](../design/0007-artifact-dispositions.md)
**Plan:** [`slice-9-astraeus-findings.md`](../plans/slice-9-astraeus-findings.md)
**Evidence:** [`brownfield-install-astraeus.md`](brownfield-install-astraeus.md) — 12 findings
**Status:** **authoring complete; dogfood pending.** Mechanical checks pass. No behavioural prediction has been run.
**Date:** 2026-08-03 (authoring)

## Executive summary

All twelve findings from the first brownfield install are addressed, across 20 commits. Finding 4 was already fixed before the slice began; the remaining eleven map to tasks in the plan.

The slice is **not validated**. Its four behavioural predictions are recorded below unrun, deliberately, so the dogfood cannot quietly skip them. Per `CLAUDE.md` working principle 2, the slice is not done until this document reports outcomes instead of predictions.

What *is* verified is mechanical: the pack installs, the reference guard is green, and the seeded-file migration path was exercised end to end against a temporary target.

## What was mechanically verified

| Check | Result |
|---|---|
| Tracked file count | 19 → **25** (`spec-and-plan-depth.md`, `claude-md-elements.md`, `conformance-reviewer.md`, `MIGRATIONS.md`, and slice-8's two) |
| Reference guard | Green — no installed file cites a devkit-repo-only path |
| Full unit suite | **22 tests green** across two files |
| Fresh install | Stamps `Gated baseline:` into `.claude/state.md`; installs `MIGRATIONS.md` |
| Update path | Update-mode dry run reports all tracked files unchanged (idempotent) |
| Migration advisory | With a deliberately invalidated template hash, renders with the installed version interpolated and points at `MIGRATIONS.md` |

Mechanical checks confirm the files install and cross-reference correctly. They say nothing about whether the pack *behaves* as intended — that is what the predictions are for.

## Behavioural predictions (pending)

Each was written **before** the corresponding pack content. On divergence, revise the pack — not the prediction.

### P1 — ADR discovery must never allocate over an existing registry

**Task:** `/feature-start` where `docs/adr/` does not exist and twelve ADRs live as headings in a single decisions log elsewhere.
**Predicted:** reports the count, location, and format; proposes the next free number; **asks** whether to continue there or start `docs/adr/` above the high-water mark. Never writes `0001`.
**Catches:** silent duplication of a decision registry — two documents claiming the same ID.
**Status:** pending · **Actual:** —

### P2 — never write inside another tool's region

**Task:** `/adopt` on a `CLAUDE.md` whose conventions section sits inside a foreign tool's sentinel region, where that region's `-start` has no matching `-end`.
**Predicted:** resolves the equivalent heading as element 5 without proposing a rename; detects and names the regions; writes **adjacent**; flags the orphaned sentinel as suspect rather than inferring the region's extent.
**Catches:** clobbering text another tool regenerates — silent until regeneration.
**Status:** pending · **Actual:** —

### P4 — a rerun after a review fix must re-run the gates

**Task:** `/feature-merge` at `Phase: in-review` after `/pr-review` pushed a fix, so local and remote tips agree.
**Predicted:** compares the PR tip against `Gated baseline`, sees they differ, re-runs gates 1–3.
**Catches:** skipping tests, docs reconciliation, and security review on the code that actually merges.
**Status:** pending · **Actual:** —

### P5 — catch a planted spec/plan contradiction

**Task:** a spec stating *"returns 409 when blocked"* against a plan whose handler returns 200 in all cases.
**Predicted:** one **blocking** finding quoting both sides. Does not read source. Does not propose the implementation.
**Catches:** the class a real spec-and-plan review found four times, none of which devkit would have caught.
**Status:** pending · **Actual:** —

## Findings from authoring

**Finding 1 — the reference guard immediately found more than the plan had catalogued.** The validation report named four dangling citations; the guard found a fifth (`adopt.md:9`) on its first run, and a sixth (`adopt.md:92`) once widened to unquoted paths. A count derived by reading is a lower bound.

**Finding 2 — the guard caught a class nobody specified.** It flagged `docs/ai/decisions.md` in prose written minutes earlier, where it was an *illustration* of another project's layout rather than a citation. On reflection the guard was right and the distinction is not one a reader can make either: a backticked path in pack prose reads as real, and a model following it finds nothing. Both were rewritten to describe the shape (*"a single decisions log rather than a directory of files"*) instead of naming a path. A tool built for one defect class caught a second.

**Finding 3 — a finding names where a defect was *noticed*, not where it *lives*.** F8 cited one two-dot diff in `/feature-merge`. Grepping the pattern found **five**, and `security-reviewer.md:17` documented the two-dot form while instructing the agent to *"run it yourself"* — so fixing gate 3 alone would have changed what was passed to an agent whose own instructions overrode it. The inverse discipline mattered equally: `git log mainline..HEAD` appears twice and is **correct**, so a blanket replace would have fixed one bug and introduced another. When a finding describes a *form* rather than a behaviour, grep the form.

**Finding 4 — the plan violated the discipline the pack exists to enforce.** Task 2 was designed to land a red suite that Task 3 would turn green, to demonstrate the guard catching something real. But the `engineer` skill's cardinal step-shape rule requires every step to end green and be independently revertable; a bisect landing between them would have hit a failure caused by neither. The demonstration was worth having — it is how Findings 1 and 2 surfaced — but **committing** the red state was the error. Fixed by pulling the two-line citation fix into Task 2.

*This suggests a gap:* `/plan` reviews step *content* against the spec (now via `conformance-reviewer`) but nothing reviews the plan against the pack's own step-shape rules. The engineer skill states them at plan time; nothing checks them.

**Finding 5 — one task disappeared into another.** Task 5's sentinel rules belonged in the same reference Task 3 created, and its command wiring in the same edits. Verified both commands cite the section rather than committing an empty task. Plans that decompose by *topic* will sometimes produce tasks that decompose by *file* into their neighbours.

**Finding 6 — two tooling errors on the author's side, both caught within one command.** A verify-then-commit written as `tests | tail -3 && git commit` let a red suite through, because `tail` exits 0 regardless; fixed by an `if`-guarded run, and the bad commit was amended rather than followed up, to keep history bisectable. Separately, backticks inside a double-quoted `git commit -m` string executed `git log` and pasted its output into the message; fixed by using quoted heredocs throughout. Both are worth recording because neither was caught by any check the pack defines — only by reading the output.

## Outstanding

- Every behavioural prediction (P1, P2, P4, P5).
- The full end-to-end dogfood: re-install on the brownfield target, `/adopt`, then one feature through `/feature-start` → `/plan` → `/build` → `/feature-merge` (PR path) → `/pr-review` → merge → closeout.
- **Seeded-file migration, hand-applied.** The target's `state.md` predates `Gated baseline:`. Confirm the `MIGRATIONS.md` 0.10.0 entry is precise enough to apply against a file whose header the user has already added to, and that the 0.9.0 entry is correctly identified as already-present.
- The `conformance-reviewer`'s severity calibration — whether *blocking vs advisory* holds up against a real plan, or whether everything drifts to one end.
- Whether the findings ledger is actually read at `/feature-start` on the second feature. If not, per the documenter skill's own instruction, delete it rather than maintain it.
