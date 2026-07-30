# Findings triage

Used by: `engineer` skill (tester findings, architect recommendations), `/build` (halt conditions), `/feature-merge` (Gate 3 security findings), `/pr-review` (external review feedback).

A finding is a **claim to be evaluated, not an instruction to be executed**. That holds whether it came from a fresh-context subagent or from a senior engineer on the pull request. The pack specifies at length how findings should be *produced* — severity criteria, threat-model matching, structured output. This file is the other half: what the receiving side does with one.

The failure mode this prevents is not "ignoring good feedback." It is the quieter one: implementing a finding correctly, promptly, and outside the scope the spec approved — so the feature ships something nobody agreed to and no document records.

## The shared loop

1. **Read completely.** All of it, before reacting to any of it. Items in a review often depend on each other.
2. **Restate the technical claim** in one sentence. If you can't, you don't understand it yet — that's the *Unclear* bucket, not a reason to guess.
3. **Verify against the repo and the spec.** Both. Code alone tells you whether the claim is true; the spec tells you whether it's in scope.
4. **Classify** into exactly one bucket (below).
5. **Respond** — a fix, a citation, or reasoned pushback. Never performative agreement; the code is the acknowledgment.
6. **Implement one at a time**, each ending green.

## Source matters

The two sources fail in opposite directions, so the default posture differs.

| | Internal (`tester`, `architect`, `security-reviewer`) | External (humans, review agents) |
|---|---|---|
| Has read the spec | Yes — it is passed in | **No** |
| Structure | Severity-bucketed, predictable shape | Free-form prose |
| Default posture | Trust the finding; evaluate the severity | Verify against the repo first |
| Blind spot | No conversation context — it can't know what you already ruled out | No spec, no ADR history, no `owned_files` |

An external reviewer not having read the spec is a fact about their **access**, not a judgment about them. Cite the spec; don't condescend to it. (If your PR body doesn't link the spec, fix that before blaming the review.)

## Classification buckets

Every item lands in exactly one.

| Classification | Action |
|---|---|
| **Accept, in scope** | Fix under the `engineer` skill's Verify discipline — green suite, lint clean, own commit. |
| **Accept, outside `owned_files`** | `/checkpoint` amendment, or a followup recorded in the summary. Never silent scope expansion. |
| **Already answered** by the spec or an accepted ADR | Reply citing it. No code change. |
| **Technically disagree** | Reply with technical reasoning. Surface to the user before it goes anywhere public. |
| **Unclear** | Ask. Implement nothing else in that cluster until answered. |

## The five devkit rules

1. **A finding that contradicts an approved spec is a spec question, not a code fix.** The spec was approved; a reviewer's preference does not override it in passing. Route to `/checkpoint` and let the amendment be explicit and dated.
2. **A finding that re-opens an accepted ADR is answered by citing the ADR back.** ADRs are immutable once accepted. If the context that justified the decision has genuinely changed, that is a *different* finding — name it that way ("the assumption in ADR-N no longer holds because…"), don't re-litigate the original.
3. **A finding requiring work outside the spec's `owned_files` becomes a `/checkpoint` amendment or a followup.** The `doc-drift-detector` hook will flag the edit anyway; better to decide deliberately than to be told after the fact.
4. **Never implement a finding that breaks the current step's revertability.** If the fix entangles two steps, it is its own step. Reversibility is the property the whole commit cadence exists to protect.
5. **Clarify every unclear item in a cluster before implementing any of it.** Partial understanding of related items produces a coherent-looking implementation of the wrong thing — the most expensive failure in this list, because it passes review.

## Common rationalizations

Triage is easy to talk yourself out of, and the excuses are social rather than technical — which is exactly why they work. If you find yourself reasoning one of these, stop; the rebuttal applies.

| Excuse | Rebuttal |
|---|---|
| "The reviewer is senior — just implement it." | Seniority is evidence about the *claim*, not authority over the *scope*. A senior reviewer who hasn't read the spec is still a reviewer who hasn't read the spec. Verify, classify, then implement. (See *Source matters*.) |
| "It's a one-line change; it doesn't need a `/checkpoint`." | Scope is measured by which files the change touches, not by diff size. A one-line edit outside `owned_files` is exactly the drift the hook exists to catch. (See rule 3.) |
| "I'll implement the clear items now and ask about the unclear one after." | Review items in a cluster are usually related. Implementing four of five, then learning the fifth reframes all of them, means redoing the four. Clarify first. (See rule 5.) |
| "Pushing back will look defensive." | Reasoned technical disagreement is the job. Silent compliance with a wrong finding ships a bug and teaches the reviewer nothing. State the reasoning, cite the code, let the user decide what goes public. (See *Classification buckets* → *Technically disagree*.) |
| "The spec is stale anyway — easier to just make the change." | Then amend the spec. "The document is out of date" is an argument for updating the document, never for ignoring it. An approved spec that quietly stops describing the code is how the project loses its memory. (See rule 1.) |
| "The security-reviewer flagged it, so it must be real." | Severity assignment is the reviewer's job; deciding what to do is yours. The `security-reviewer` has its own rationalization table precisely because reviewers inflate and deflate. Evaluate the finding against the spec's stated threat model. (See *Source matters*.) |
