# Slice 14 — 0.12.0 errata

**Source:** [`docs/validation/errata-0.12.0.md`](../validation/errata-0.12.0.md) — five findings raised by Codex against the 0.12.0 upgrade PR on the Enterprise API target, 2026-08-14.
**Issues:** [#5](https://github.com/balorette/devkit-flow/issues/5)–[#9](https://github.com/balorette/devkit-flow/issues/9)
**Status:** F1 and F3 shipped in 0.12.1; F2, F4, F5 planned here, unbuilt.
**Date:** 2026-08-15

---

## Why this is a slice and not a patch round

The first four PR-review rounds on slice 12 were *readings* of the pack. This is the first set of findings produced by **running** it, and the difference shows in what got caught: F1 is a defect in a phase slice 12 added, reviewed five times, and shipped — one that would have halted `/plan` on the first step of essentially any Python plan. No amount of further reading was going to surface it.

Two findings were urgent enough to ship ahead of this plan, because they block real use:

- **F1** (#5) — Phase F3 halting on `UUID`, `AsyncSession`, `datetime`, `BaseModel`. Shipped in 0.12.1.
- **F3** (#7) — the findings-ledger row written in Red and staged nowhere, halting `/feature-merge` on its own precondition. Shipped in 0.12.1.

The remaining three are real and confirmed, but none of them stops a project working today.

## The pattern behind F2, F4, and F5

Named by the errata and worth carrying into the work rather than rediscovering per task:

> A step that reads or writes durable state **reconstructs** a value it should have **read** — the PR from the current branch, the summary filename from today's date, a single directory from a scan that found two. In each case a field holding the correct answer already exists nearby and goes unread.

This is 0.12.0's headline principle (*"a path that can be derived will be derived"*) generalizing past filenames. **The lens is the deliverable as much as the three fixes are** — Task 4 exists to apply it to the commands nobody has re-read under it.

---

## Task 1 — F2: the merged-state check queries the current branch (#6)

**Severity: high. Reproduced in execution**, which no other finding here was.

`/feature-merge`'s first precondition reads `gh pr view --json state,mergedAt` with **no argument**, so it inspects whatever PR belongs to the current branch. Precondition 1 — *"`PR:` is set in state.md"* — is ordered *after* it, so the one field identifying the right PR is read too late to inform the query.

Observed on the target: `state.md` recorded a merged PR while `HEAD` sat on the upgrade branch whose own PR was open. The argument-less query returned the wrong PR as open, routing the command into "gated content changed" and re-running all three gates for a feature that had already merged. From mainline it fails outright, no PR belonging to that branch at all.

**Do:**
- Read `PR:` from `state.md` **before** the merged-state check, and pass it to the query.
- Handle the field's full form: it may hold `owner/repo#N`, not just `#N`, so the repository travels with it.
- Reorder the preconditions so nothing consumes `PR:` before it is read — this is clause 3 in the small, and the fix is an ordering change plus an argument.
- Decide and state what happens when `PR:` is absent but `Phase` is `in-review`. That is a real state (a hand-edited `state.md`, or an upgrade that dropped the field) and the current text has no answer.

**Verification:** behavioural, and cheap — set `state.md` to a merged PR, check out an unrelated branch with an open PR, run `/feature-merge`. Predicted: it reads the recorded PR, finds it merged, and takes the closeout path. Record as **T19** in the validation doc.

## Task 2 — F4: a gate rerun authors a second summary (#8)

**Severity: high.**

The `in-review` row for changed gated content routes to *"re-run gates 1–3"* and says nothing about the summary. The section that follows is headed unconditionally — *"After all three gates pass — Summary and supersede"* — and its first step writes a summary named per § *Name*, which stamps the **creation** date. A rerun on a later day therefore cannot land on the original filename: it authors a second retrospective, overwrites `state.md`'s `Summary:` pointer, and strands whatever `/pr-review` had already written into the first.

**Note the self-inflicted edge:** 0.12.0 added `Summary:` precisely so a later session could find a file whose dated name it cannot recompute. This path recomputes the name anyway.

**Do:**
- Gate summary *authoring* on the entry rows that mean "this feature is closing out" — `building` / `merging` — rather than on the unconditional heading.
- On the `in-review` rerun path, **amend** the summary at `state.md`'s `Summary:` path through Gate 2's reconciliation, and do not touch the pointer.
- Say explicitly what a rerun does when `Summary:` is `—` and the phase is `in-review`. Authoring the first summary there may be right; guessing is not.
- Check the supersede mechanic in the same section for the same bug — it writes `state.md`'s Parked features on a path that can now run twice.

**Verification:** **T20** — merge-gate a PR, push a change, re-run `/feature-merge` on a later date. Predicted: one summary, amended; `Summary:` unchanged.

## Task 3 — F5: § *Discover* cannot report a tie (#9)

**Severity: medium.** Codex raised it P1; the errata argues P2 and this plan accepts that reading — § *Resolve* routes any pack-foreign directory to § *Confirm*, and § *Confirm* says *"do not resolve it by picking."* A literal agent is stuck **asking**, not stuck guessing, so the silent-damage profile the reference exists to prevent is absent. What is underspecified is the **reporting contract**, not the decision rule.

The target is the demonstration: `docs/plans/` (retired plans plus `completed/`) and `docs/ai/plans/` (live) are both pack-foreign, provenance ranks them identically, and the return shape — *"exactly one of: a path per artifact type, or an explicit `none found`"* — cannot carry both.

**This is the reference's own motivating example**, one step further than it was written to handle: it opens on a brownfield target whose `docs/plans/` held retired plans, and does not resolve the case where the live directory is equally pack-foreign.

**Do:**
- Let § *Discover* return a **candidate list** per artifact type — one path, several, or `none found`.
- Have § *Confirm* present the tie, with what distinguishes the candidates (file counts, recency, whether one holds a `completed/` subtree), and let the user pick.
- Keep *"silence is not a result"* intact: several candidates is an answer, and it must be distinguishable from a scan that never ran.
- Re-check every § *Resolve* consumer for an assumption that discovery returns at most one path.

**Verification:** **T21** — run `/adopt` on a repo with two pack-foreign plan directories. Predicted: both surfaced, user asked, choice recorded per type.

## Task 4 — apply the reconstruct-vs-read lens across the remaining commands

The three findings above were found one at a time by a reviewer who noticed the shape. **Look for the siblings deliberately**, rather than waiting for the next dogfood to surface them singly.

Sweep `/build`, `/checkpoint`, `/pr-review`, `/adopt`, and the `documenter` and `pm` skills for: a value reconstructed from context (current branch, today's date, a slug, an inferred path) where a recorded field holds the answer. `state.md`'s fields are the obvious candidates — `Spec`, `Plan`, `Summary`, `PR`, `Gated baseline`, `Active branch`.

Record what the sweep finds even when the answer is "nothing" — a sweep whose scope is unrecorded reads as complete when it was partial, which is the failure the pack keeps naming.

## Task 5 — the guard question

`test_clause_one` scans commands' `## Run` subsections and, for skills, only `Phase`/`Gate` headings. **The engineer skill's missing declarations sat in that excluded region**, and F3 is what found them. Skills have no `## Run` to scope by, and an all-headings scan of skills flagged 29 sections when measured during slice 12 — mostly prose that mentions writes performed elsewhere.

**Decide, with a measurement rather than a guess:** is there a scoping for skills with a signal-to-noise ratio worth enforcing? If yes, land it. If no, **record the negative result and the number**, so the next person does not re-derive it — and accept explicitly that skill-level clause-1 coverage rests on review rather than on the suite.

---

## Sequencing

Tasks 1 and 2 are independent and both touch `/feature-merge`; do them in one pass to avoid two rounds of edits to the same preconditions table. Task 3 touches `artifact-locations.md` and its consumers, and is independent of both. Task 4 depends on nothing and informs everything — run it early enough that anything it finds can join this slice rather than starting slice 15. Task 5 is independent and small.

## Release

Pack text only — commands, skills, and one reference, all manifest-tracked rather than seeded. Unless a task changes `state.md.template` or `CLAUDE.md.template`, no `MIGRATIONS.md` section is required, and the release is a `VERSION` bump plus a byte-identical template snapshot. **Verify that rather than assuming it**: `tests/test_migrations_snapshot.py` is the check, and the 0.12.1 release confirmed the shape.

Task 2's `Summary:` handling is the one to watch — it is the field 0.12.0's migration added, and a change to what writes it may need an entry even when the template does not move.
