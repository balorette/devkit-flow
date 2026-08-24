# Subagent degraded mode

Clause 6b and 6c of the pack's step invariants: **an assurance that can stop holding says when, and a degradation is recorded rather than absorbed.**

Used by: the `engineer` skill (tester spawns), `/build` (halt conditions), `/feature-merge` (Gate 3). Cite this; do not restate it.

The pack spawns subagents for work whose value depends on isolation — the `tester`'s fresh context is the TDD integrity guarantee, and `security-reviewer`'s is what keeps Gate 3 honest. Every one of those guarantees is void if the subagent does not actually do the work. The pack had text for a subagent that answers *wrongly* and none for one that does not answer.

## Detect

**Silence is not evidence of death.** `architect.md` states the callee's half of this rule — *"an explicit 'none found' is a complete answer; nothing at all is a missing answer"* — and it holds identically for the caller. A subagent that has not reported may be working, may have died, or may have finished and failed to deliver, and those are three different situations.

Before concluding a subagent produced nothing:

1. **Re-ping it.** The cheapest possible check, and it recovered a stalled `security-reviewer` on the run that produced this clause.
2. **Read the working tree.** A subagent that wrote files and then failed to report has still done the work; the evidence is on disk. Check the paths it was asked to write before assuming there is nothing to find.
3. **Do not treat an agent-listing tool's "no reachable agents" as proof.** It reports what is reachable now, which is not the same claim.

A subagent that returned late is not a failure. On the run that produced this clause one reported thirty minutes after it was written off — after its work had already been redone.

## Decide

If the subagent genuinely produced nothing and you proceed without it, **you are trading an assurance for progress, and that is the user's trade to make.** Say which assurance, say what replaces it, and get an answer. Concretely:

- **`tester` did not return** → writing the tests in the main loop voids fresh context: the tests are now written by something that has seen the implementation intent. That is not TDD with a caveat; it is a different practice.
- **`security-reviewer` did not return** → Gate 3 did not run. The gate cannot report a pass it did not compute.

Re-running the spawn is almost always cheaper than the trade. Prefer it.

## Ownership

**One writer per file.** While a subagent may still be live, the main loop does not write into the paths that subagent was asked to produce. If it must, the collision is **reconciled and reported** — read both versions, decide deliberately, and say what was overwritten. Never silently take one side, in either direction.

This is the concurrency that the *Detect* steps make likely rather than rare: the moment a caller decides a subagent is dead and does its work, one file has two writers.

## Record

**A degradation that is not recorded is indistinguishable from a clean run**, and the record is what a later feature reads. Write a `DEG` row to the findings ledger at its discovered path (see the `documenter` skill's *The findings ledger*), naming the assurance, the reason, and what was done instead.

The ledger, not the summary alone: the pack's own argument for the ledger is that *"the summary is a document nobody reopens"*, and *"this feature's tests were not written in fresh context"* is exactly the kind of fact the next feature in that area needs.

`/feature-merge` surfaces open `DEG` rows at the merge proposal and asks before proceeding.
