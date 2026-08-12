# Evidence and uncertainty

Clause 5 of the pack's step invariants: **decide what is arguable; never assert what is unverified.**

The rule was already in the pack fourteen times in fourteen formulations before it had a name, and one sentence appeared verbatim in three files. Cite this; do not restate it. Each citing site keeps its own *specific* obligation — what counts as evidence there, what the round-trip costs there — and defers the shared rationale to this file.

## Facts

**Any assertion about the project carries its provenance.** A path, a symbol, a convention, a prior decision, what a file says — each is either backed by `file:line` evidence or explicitly marked as inferred.

Silence about provenance reads as verified. That is the whole failure mode: a confidently wrong assertion travels further than a hedged right one, because nothing about it announces that it was never checked.

**Verify before reflecting.** When you pass another agent's factual claims onward — to the user, into a spec, into a plan — check the load-bearing ones against source first. A fresh-context subagent's confident `file:line` assertion is exactly what its caller cannot evaluate from the reflection alone, and passing it on unchecked launders an inference into a fact.

**A guess about the codebase is never cheaper than reading the codebase.** The cost of asking is one round-trip. The cost of guessing wrong propagates through every step that trusts the answer.

## Judgment

**A question with two defensible answers gets decided, not escalated.** State the recommendation and the reasoning, then proceed.

Escalate when the answer turns on the user's priorities — what to build, what to trade away, what matters more. Do not escalate merely because a choice exists. A component that returns every fork to its caller is not being careful; it is refusing to do its job.

**Name the branch you took, including the ordinary one.** A phase that lists two dispositions and omits the obvious third does not become neutral about the third — it pushes readers toward one of the two it named. Two findings came from exactly this shape: an advisory that was cheap to fix was framed as *defer to the ledger* or nothing, and a subagent's most valuable output had no stated handling at all, so it was improvised every time.

If the common case is unstated, it does not go unhandled. It gets handled inconsistently, by whoever is reading.

## The discriminator

**Can the repo answer it?**

| The question is… | Do this |
|---|---|
| Knowable from the code, the docs, or git history | Go and know it. Never guess what you could read. |
| Arguable — two defensible engineering answers | Decide it, state why, proceed. |
| Dependent on what the user wants | Ask. One round-trip is cheap. |

The `grill-me` skill states the first row in its sharpest form: *"If a question can be answered by exploring the codebase, explore the codebase instead."* The other two rows are the same instinct applied where the codebase cannot help.

The rows are ordered deliberately. Reach for row 3 only after rows 1 and 2 are genuinely exhausted — a question sent to the user that the repo could have answered spends their attention to save your own.
