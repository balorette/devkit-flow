# Flow Execution Findings — the review-and-closeout half, at 0.12.1

**Source:** a feature carried end to end on Enterprise API at pack version **0.12.1**, through `/feature-merge` → PR → `/pr-review` → gate rerun → closeout (PR #148). Four fresh-context subagent spawns, four merge gates, a PR review round with an external reviewer (Codex), and a completed closeout on a forge that deletes the head branch.
**Status:** **6 gaps**, all observed during execution rather than read off the page. Five behaviours recorded as working. Two standing predictions exercised and passed.
**Date:** 2026-08-24

---

## What this is

Sibling to [`flow-execution-0.11.0.md`](flow-execution-0.11.0.md), which retired the "no pack command has executed" caveat for the **build** lifecycle. This round retires it for the **review-and-closeout** half.

**Newly executed for the first time:** `/pr-review` (all three comment surfaces, marker skip, batch proposal, push-then-reply), `/feature-merge`'s `in-review` re-entry with a gate rerun, and `/feature-merge`'s **closeout** — the three bodies of text [`pr140-pack-findings.md`](pr140-pack-findings.md) named as the largest never-run region in the pack. Four of that document's seven findings live on this path and were authored by reading; the path has now run.

**The headline: the flow shipped a feature, and one of the things it shipped was wrong.** Gate 3 found a real TOCTOU, recommended a fix, the fix passed all four of the project's gates, and the fix did not work. Nothing in the pack looked at it again. That is gap 1, and it is the round's most valuable output.

**Every gap below was read back against `pack/` source before being recorded here.** The verdicts are ours; the observations are the operator's. Where a gap is an *absence*, the absence was confirmed by grep across `pack/`, not inferred from not having noticed the text.

## Disposition

| # | Gap | Sev | Verdict | Recommended landing |
|---|---|---|---|---|
| G1 | A gate's own recommendation is never re-gated | **high** | Confirmed | [ADR-0010](../design/0010-degradation-is-recorded.md) clause 6a — `/feature-merge` Gate 3 + `security-reviewer` brief |
| G2 | No degraded-mode protocol when a subagent fails | **high** | Confirmed (absence — no such text exists in `pack/`) | ADR-0010 clause 6b |
| G3 | Concurrent writers once the main loop assumes a subagent is dead | med | Confirmed; occurred, handled by the tester's judgment alone | ADR-0010 clause 6c |
| G4 | `/pr-review` stage 4 contradicts `/feature-merge`'s two-commit rule | med | Confirmed — both texts quoted below | Point fix in `pr-review.md` Phase D |
| G5 | An API reply creates an empty-bodied review submission that satisfies neither skip condition | med | Confirmed | Point fix in `pr-review.md` Phase A |
| G6 | Nothing verifies a claim written into a durable doc | **high** | Confirmed — a false claim merged | ADR-0010 — clause 4 swept into `documenter` |

---

## Gap 1 — a gate's own recommendation is never re-gated

**Severity: high.** The pack shipped a fix, written on its own gate's advice, that silently defeated the guarantee it was added to provide.

Gate 3 was right about the defect: it found a TOCTOU, and it recommended `get_with_lock`, citing the repo's own SD-032 precedent rather than inventing a pattern. The fix landed, all four gates went green, and it did not close the race. The reviewer had checked `expire_on_commit=False` and never asked about `populate_existing` — the ORM returns the identity-map-resident object for a `SELECT … FOR UPDATE`, so the lock is taken and the attributes read are the stale ones. **Codex caught it. The pack did not.**

The pack's re-gate rule is scoped to one severity. `feature-merge.md:157`:

> **One or more critical findings:** halt. … Re-run Gate 3 (or the full sequence from Gate 1, since fixes touch code) after resolution.

`feature-merge.md:156` sends non-critical findings to a `SEC` row and passes the gate. `security-reviewer.md:11` names the branch that actually happened and then drops it:

> Lower-severity findings are recorded in the feature's summary doc; they don't block the merge unless the user chooses to address them.

**"Unless the user chooses to address them" is a branch with no procedure behind it.** Choosing to fix a non-critical finding produces new code Gate 3 has never seen, on the most security-relevant hunk in the diff, and the command's own gate accounting still reports a clean pass.

This is the third recorded instance of the shape [`evidence-and-uncertainty.md`](../../pack/references/evidence-and-uncertainty.md) § *Judgment* already names — *"Name the branch you took, including the ordinary one … If the common case is unstated, it does not go unhandled. It gets handled inconsistently, by whoever is reading."* That paragraph records two prior findings of this shape; this is a third, in the gate that stands between the pack and a shipped vulnerability.

**Second half of the gap, and the part a naive fix misses.** The `in-review` row at `feature-merge.md:24` *does* re-run gates 1–3 when gated content changes, so a fix made after the PR opens gets a Gate 3 pass. That pass is not the pass this needs. The reviewer arrives in fresh context, sees `get_with_lock` in the diff, and reads it as the mitigation — because reviewing a diff and **grading your own prior recommendation** are different tasks, and fresh context is precisely what removes the knowledge that this hunk exists *because Gate 3 asked for it*. Fresh context is load-bearing for objectivity (`security-reviewer.md:9`) and is exactly what strips the reviewer of the question it most needs to ask.

**Recommended fix, two parts, both required:**

1. **Re-run Gate 3 after any accepted finding is fixed, regardless of severity.** The severity threshold belongs to *blocking the merge*, not to *deciding what has been reviewed*.
2. **Brief the reviewer that it is grading its own recommendation.** Pass the prior finding and the hunk that answers it, and require an explicit verdict on whether the mitigation achieves the guarantee the finding named — not whether the code looks like the recommendation. `security-reviewer.md:30`'s "recommend a *narrow* fix" earns a companion: **a narrow fix is checked against the property, not against the recommendation.**

## Gap 2 — no degraded-mode protocol when a subagent fails

**Severity: high.** Three of four spawns misbehaved, and the pack has no text for any of it.

- `security-reviewer` went idle without reporting; recovered by pinging it.
- `tester` reported roughly thirty minutes late, after the operator had concluded it was dead and shipped its work.
- A Gate-3 re-review died mid-response.

`grep` across `pack/` returns nothing for a subagent that does not return. The nearest text is `engineer` SKILL.md:47 — *"If the tester returns **findings and no tests**, that is a refusal"* — and `/build`'s halt list, which covers *the tester returns findings instead of tests*. Both handle a subagent that **answered wrongly**. Neither handles one that did not answer.

Two guarantees the pack advertises rest on these spawns completing: the fresh-context TDD integrity guarantee (`engineer` SKILL.md:35 — *"**Do not pass implementation source** — fresh context is the TDD integrity guarantee"*) and Gate 3 itself. With no fallback, the operator improvised, and **both improvisations weakened a guarantee the pack advertises at full strength.** Nothing recorded that they had been weakened.

Two specific corrections from the run, both worth writing into the protocol:

- **`ListAgents` reporting no reachable agents is not evidence that a subagent died.** This is the caller-side mirror of a rule the pack already states callee-side, at `architect.md:24`: *"**Silence is not an input.** An explicit 'none found' is a complete answer and you proceed on it; nothing at all is a *missing* answer and you ask for it."* The pack tells its subagents not to read silence as data and never told their callers the same thing.
- **Check the working tree before concluding a subagent produced nothing.** A subagent that writes files and then fails to report has still done the work. The evidence is on disk; the absence of a message is not evidence of the absence of output.

**Recommended fix:** a named degraded mode — re-ping, then check the tree, then decide — and a hard requirement that **the reduced assurance is recorded rather than silently absorbed.** Recommend the findings ledger as the carrier, not only the summary: `/feature-merge`'s own argument for the ledger (`feature-merge.md:156`) is that *"the summary is a document nobody reopens"*, and "this feature's tests were not written in fresh context" is exactly the kind of fact a later feature needs.

## Gap 3 — concurrent edits between a subagent and the main loop

**Severity: medium.** The direct consequence of gap 2, recorded separately because its fix is separate.

Once the main loop concludes a subagent is dead and does the work itself, two writers exist for one file, and the pack has no ownership or leasing concept to prevent it. In this run the tester handled the collision well — **by its own judgment, with no instruction telling it to.** That is a lucky outcome, not a designed one, and it will not repeat reliably.

**Recommended fix:** as part of the degraded-mode protocol, the main loop does not write into a still-possibly-live subagent's declared output set; if it must, the collision is reconciled and reported, never silently overwritten in either direction.

## Gap 4 — `/pr-review` stage 4 contradicts `/feature-merge`'s two-commit baseline rule

**Severity: medium.** Two commands give incompatible recipes for the same commit, and one of them carries the reasoning.

`pr-review.md:80`:

> **Commit the metadata.** Stage exactly what stages 2 and 3 wrote — the summary doc, the discovered findings-ledger path, and `.claude/state.md` — and propose a commit.

`feature-merge.md:24`, and its rationale at `:65–67`:

> **Commit whatever the gates wrote first** … *then* update `Gated baseline` and commit `.claude/state.md` alone, and push. Two commits, in that order.
>
> … one combined commit would put non-`state.md` content in the transition commit, and the discriminator above excludes only `.claude/state.md`, so the next invocation would read the difference as ungated content and re-run gates that already passed.

**A pass that responds to review *and* records a baseline hits both rules.** The operator followed `/feature-merge`, on the grounds that it carries the reasoning — the right call, and the one this document endorses. Note also that `/pr-review` stage 4 says nothing about `Gated baseline` at all, so an operator on that path has to import the rule from the other command to know a baseline is owed.

**Recommended fix: `/pr-review` always splits.** Artifacts commit, then `.claude/state.md` commits alone — one recipe, stated once, matching `/feature-merge` everywhere rather than only when a baseline happens to be in play. A conditional ("split *if* you are also writing a baseline") is the version that gets read wrong at 11pm, and the cost of the unconditional rule is one extra commit on a metadata-only change.

## Gap 5 — an API reply creates an empty-bodied review submission that satisfies neither skip condition

**Severity: medium.** Near-miss: the operator nearly triaged two of their own replies as new reviewer feedback.

Replying to an inline comment through `POST …/comments/{id}/replies` — the mechanism `pr-review.md:30` prescribes — makes GitHub wrap the reply in a **review submission**. `gh pr view --json reviews`, the fetch at `pr-review.md:31`, then returns an entry authored by the replier with an **empty body**.

Run it against the two skip conditions at `pr-review.md:40–47`:

1. *A marker names its id* — no. The marker in the reply names the **original comment's** id; this submission has its own id that nothing names.
2. *The item itself contains a marker* — no. There is no body to carry one.

So the pack's own reply comes back on the next pass as an unanswered review item. **This is the third occurrence of the same mechanism, one level up each time**: first `in_reply_to_id` (which existed only on inline comments), then the reply-as-comment case that condition 2 was written to close, now the reply-as-*review*. `pr-review.md:45` already names the general law — *"the pack's own actions are among the things that changed the state it is reading"* — and each fix has closed the instance in front of it.

**Recommended fix: a third skip condition — an item with an empty body carries no finding.** An empty review submission is a container for inline comments, not a finding, and the same is true of a bare `APPROVED`. It is content-free by construction, so the filter cannot drop a real item, and it removes the recursion for every surface at once instead of one level at a time. Report the count with the others, per the same paragraph's rule.

## Gap 6 — nothing verifies a claim written into a durable doc

**Severity: high.** A false claim — *"every current caller is safe"* — went into a durable doc, through the proposal, and merged.

The `documenter` skill's cardinal discipline (`SKILL.md:14`) is **propose before writing**. That asks the user whether to write it. **It does not ask whether it is true**, and a proposal is not a verification: a confident row in a table is exactly the artifact a reviewing user is least equipped to falsify, because the person who would have to check it is the one who wrote it.

The rule the pack needs already exists, in the reference `documenter` cites — [`evidence-and-uncertainty.md`](../../pack/references/evidence-and-uncertainty.md) § *Facts*:

> **Any assertion about the project carries its provenance.** … Silence about provenance reads as verified. That is the whole failure mode.

`documenter`'s single citation of that file (`SKILL.md:18`) points at § *Judgment* — decide rather than escalate. **It never cites § *Facts*.** The doc-authoring component of the pack is the one component that does not run the pack's own truth rule.

Structurally this is ADR-0009 clause 4 — *an artifact declared authoritative has a verification pass* — implemented for **exactly one artifact type**. `/plan` Phase F3 verifies a plan's type signatures. Summaries, domain docs, ADRs, and findings-ledger rows all assert things about the codebase and have no equivalent pass. That is the same one-instance shape [`flow-execution-0.11.0.md`](flow-execution-0.11.0.md) finding 4 recorded for clause 3, and the recommendation is the same one four findings have now reached: **sweep the clause, don't patch the site.**

**Recommended fix:** `documenter` gains a verification substep before any proposal ships — every load-bearing factual claim in a proposed doc is either backed by `file:line` or marked as inferred, and a claim quantified over the codebase (*every caller*, *no other path*, *all consumers*) is verified by search or it is not written in that form. The operator has already added this convention downstream in the target project's `CLAUDE.md` (PR #148); it belongs upstream, in the component that writes the docs.

---

## What worked — worth not regressing

A round that logs only failures misreports what was learned. Five behaviours earned their text:

- **The `Gated baseline` content-diff discriminator** correctly reported *quiet, no gates* on a rerun. The written reasoning for why it is neither tip-vs-tip nor SHA-equality (`feature-merge.md:62–63`) is right and paid off in execution.
- **Merged-state-check-first saved the closeout.** The forge deleted the head ref, so `git ls-remote` returned nothing — the exact failure `feature-merge.md:33` predicts — and the ordering fix ahead of precondition 2 is what let the closeout run instead of halting on a PR whose only remaining work was that closeout.
- **Gate 2 asking coverage and conformance separately** (`feature-merge.md:132`) is what surfaced that the design docs asserted a mechanism that did not exist. The coverage check alone was structurally blind to it — which is precisely what that paragraph claims about itself.
- **`/pr-review`'s marker mechanism, condition 2**, genuinely prevented the self-reply recursion its rationale describes. Gap 5 is the *next* level of the same problem, not a failure of this guard.
- **Summary-as-PR-body**, with *Followups* and *Security review notes* withheld (`documenter` SKILL.md:177). Reviewers got the contract without the deferred-scope debate.

## Predictions exercised

| Prediction | Source | Result |
|---|---|---|
| **T18a** — clause 2's discriminator runs no gates on an unchanged PR | [`slice-12.md`](slice-12.md), carried from slice 11 | **Passed.** Reported quiet; no gates ran. Unreachable since `Gated baseline` was introduced; ADR-0008 called it the highest-value thing for a dogfood to exercise. |
| **T14a** — merged-state ordering on a head-deleting forge | [`slice-12.md`](slice-12.md) | **Passed.** Closeout ran and cleared state on a forge that deleted the head ref. |

**Not exercised:** T14b (tip equality from a second clone), T14c (untracked files at the `in-review` precondition), T1 (Phase F3 halting on a genuinely wrong symbol), T18b (the drift hook's unexplained miss). The runbook in [`slice-12.md`](slice-12.md) still stands for those four.

## The round's keeper

Gaps 1, 2 and 6 are one sentence:

> **A guarantee that degrades does not announce it — so the record keeps asserting the undegraded version.**

Gate 3's verdict stopped covering the diff the moment its own recommendation was implemented, and the gate accounting still read *clean*. The fresh-context TDD guarantee was void the moment the main loop wrote the tests, and the summary still read *tests written in fresh context*. A doc's claim carried no verification, and the sentence still read as a fact. In all three, **the assurance kept its full-strength name after the thing that produced it stopped covering the thing it names.**

The remedy shape is the same in all three: an assurance the pack advertises names the condition under which it stops holding, and **a degradation is recorded rather than absorbed.** That is [ADR-0010](../design/0010-degradation-is-recorded.md) **clause 6**, covering G1, G2 and G3, with G6 closed as **clause 4 swept** into `documenter` rather than as new law. G4 and G5 are point defects and need no clause — one is a contradiction between two texts, the other a third skip condition.

## On the operator's bias note

Recorded because it is the most honest thing in the round, and because this document disagrees with half of it:

> Items 1, 2 and 6 are all cases where the pack's assurance was weaker than its confidence, and in each case I was the one who reported the inflated version to you. So they may say as much about how I use the pack as about the pack itself — 1 and 6 in particular would have been caught by a more skeptical operator.

The observation is right and the inference is too generous to the pack. **A discipline that holds only when the operator is skeptical is not a discipline; it is a mood.** The pack's entire premise is that guarantees live in text rather than in the diligence of whoever happens to be driving — the anti-rationalization tables exist because the authors assumed a *tired* reader, not an ideal one. Gaps 1 and 6 are exactly the cases where by-construction guards work: re-running a gate and grepping for a caller are both mechanical, and neither depends on someone being suspicious at the right moment.

What the bias note *does* argue for is a real correction, and it is the reporting side rather than the guard side: **the operator reported the inflated version because nothing required them to report the degradation.** That is gap 2's second half, and it is why the recommended fix records the reduced assurance in the ledger rather than trusting anyone to mention it.

## Not validated by this round

- **T14b, T14c, T1, T18b** — see above.
- **`/checkpoint park`** — still never exercised end to end.
- **The three planned-but-unbuilt slice-14 defects (#6, #8, #9).** #6 (merged-state check querying the current branch rather than `state.md`'s `PR:`) is *on* the closeout path this run traversed; the closeout succeeded because the branch happened to be checked out, which is the condition that hides it.
- **A second-project install.** Everything here is still one target.
