# 0.12.0 errata — findings from the first upgrade dogfood

**Date:** 2026-08-14
**Target:** Enterprise API — the brownfield target, upgrading 0.11.0 → 0.12.0
**Source:** Codex review of the upgrade PR
**Issues:** [#5](https://github.com/balorette/devkit-flow/issues/5)–[#9](https://github.com/balorette/devkit-flow/issues/9)
**Plan:** [`docs/plans/slice-14-0.12.0-errata.md`](../plans/slice-14-0.12.0-errata.md)

---

## What this round is

**Five findings, all landing on pack files, none on project code.** The target's `CLAUDE.md` and `state.md` came through clean — these are upstream defects in the instruction text, not in how the project adopted it.

Every finding was read back against pack source before being accepted here; the verdicts below are ours, not the reviewer's. Four are confirmed as written. One is confirmed with its severity disputed.

**This is the second set of findings in the pack's history produced by execution rather than reading**, after the nine from the 0.11.0 flow run. It matters what that difference bought: slice 12 went through **four PR review rounds** — eighteen findings, all closed by reading — and none of them surfaced any of these five.

## Disposition

| # | Finding | Sev | Verdict | Status |
|---|---|---|---|---|
| F1 | `/plan` Phase F3 halts on built-in and dependency types | high | Confirmed | **Shipped 0.12.1** |
| F2 | `/feature-merge`'s merged-state check queries the current branch, not `state.md`'s `PR:` | high | Confirmed, **reproduced** | Planned — slice 14 task 1 |
| F3 | Findings-ledger row written in Red, staged in no substep | high | Confirmed | **Shipped 0.12.1** |
| F4 | A gate rerun authors a second dated summary and overwrites the pointer | high | Confirmed | Planned — slice 14 task 2 |
| F5 | § *Discover* cannot report a tie between two pack-foreign directories | med | Confirmed; **severity downgraded from P1** | Planned — slice 14 task 3 |

## The two that shipped immediately

**F1 blocks `/plan` outright on any realistic project.** The phase offered exactly two dispositions for an unresolved name — correct the plan, or mark it introduced by this plan — and a signature naming `UUID`, `AsyncSession`, `datetime`, or `BaseModel` fits neither. A literal reader had to halt on valid work or record a false provenance to escape.

Worth sitting with: **Phase F3 is something slice 12 added.** It was the fix for flow-6 (plan signatures authoritative but unverified), it was refined twice during PR review — X4 gave it definition-site resolution — and it shipped through four review rounds with no bucket for a type the project does not own. 0.12.1 adds `EXTERNAL`, with the same evidence requirement the other two states carry.

**F3 found that the engineer skill had zero `**Writes:**` declarations.** Slice 12 converted `/feature-start`, `/plan`, and `/feature-merge` to derived staging across three review rounds and never touched the component that runs *most often* — once per build step. Its substep 5 was the last hardcoded enumeration in the set, and it failed in exactly the way the other three documented before changing: the findings-ledger row, written at a discovered path outside the directories the step is otherwise touching, invisible in the diff a reader skims before staging.

The consequence chains: the row survives `/build` uncommitted, and `/feature-merge` halts on its own clean-tree precondition. **The build loop hands the closeout a tree it is required to refuse.**

## What the errata saw that four review rounds did not

The reviewer's own synthesis, and it is the most valuable thing in the round:

> F2, F3, and F4 are all the same shape: a step that reads or writes durable state **reconstructs** a value it should have **read** — the PR from the current branch, the staging list from a hardcoded enumeration, the summary filename from today's date. In each case a field holding the correct answer already exists nearby and goes unread.

That is 0.12.0's headline principle — *"a path that can be derived will be derived"* — generalizing past filenames. The pack applied it to artifact paths and stopped. Slice 14 task 4 exists to apply it as a review lens to the commands nobody has re-read under it.

## On the F5 downgrade

Codex raised it P1. We record it as P2, and the argument is worth keeping because it is a case of the pack's layering working:

§ *Discover*'s output contract demands exactly one path per artifact type, and the target genuinely has two pack-foreign plan directories that provenance ranks identically. But § *Resolve* routes any pack-foreign directory to § *Confirm*, and § *Confirm* says outright *"do not resolve it by picking."* **A literal agent is stuck asking, not stuck guessing** — the wrong-directory write named as the consequence is the one outcome the text still prevents.

What is underspecified is the reporting contract, not the decision rule. Real, worth fixing, and without the silent-damage profile that makes a finding urgent.

Sharpest detail: this is the reference's *own* motivating example, one step further than it was written to handle. It opens by describing a brownfield target whose `docs/plans/` held retired plans — and does not resolve the case where the live directory is equally pack-foreign, which is that target's actual state on the day it adopts the pack.

## A prediction that passed

Buried in the PR status and easy to miss among five defects: **CI ran all four of the project's blocking gates green** — ruff, the mypy ratchet, pytest, and `diff-cover`. That is the merge-time sibling of prediction **T2** in [`slice-12.md`](slice-12.md): the recorded gate list reached the runner, including the coverage-delta gate that a plain test run cannot see and that Gate 1 historically missed.

**It is the first slice-12 prediction to be exercised at all.** Recording it because four review rounds produced nothing but defects, and a validation round that logs only failures misreports what was learned.

## What this says about sequencing

Task #7 in the working notes asked whether the Enterprise API dogfood should precede slice 13's `reviewer` gate or follow it. **This round answers it.** Five findings from one execution, after eighteen findings' worth of reading missed all five — and the most severe was in a phase written, reviewed four times, and shipped as a correctness guard.

That does not weaken the case for `reviewer`; F2, F4, and F5 are exactly the cross-step semantic misses it is defined by, and a reviewer applying the reconstruct-vs-read lens would plausibly have caught all three. It does establish the order: **execution first, because it is the only thing that has ever found a defect of F1's kind**, and a reviewer built on unvalidated ground inherits whatever the ground is wrong about.

## Not validated by this round

The upgrade exercised the install path and one PR. It did **not** exercise:

- **T18a** — clause 2's no-gates-on-an-unchanged-PR branch, still unrun.
- **T14a/b/c** — the `in-review` re-entry path. F2 and F4 are both *on* that path and were found by reading the text during an upgrade, not by traversing it.
- **§ *Resolve*'s per-type behaviour** through a full feature — `/feature-start` settling specs and `/plan` then settling plans.
- **T1** — Phase F3 halting on a genuinely wrong symbol. F1 shows the phase halting on the wrong things; nothing yet shows it halting on the right ones.

The runbook in [`slice-12.md`](slice-12.md) still stands, and its step 5 is where the four above get exercised.
