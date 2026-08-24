# Slice 15 — Degradation Is Recorded: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close [ADR-0010](../design/0010-degradation-is-recorded.md) — clause 6a/6b/6c plus clause 4 swept into `documenter` — bundled with slice 14's three unbuilt defects (#6, #8, #9), shipping as **0.13.0**.

**Architecture:** Six of the seven text changes are edits to existing commands, skills, and agents. The one new artifact is a reference file (`pack/references/subagent-degraded-mode.md`) holding the degraded-mode protocol, because it has three consumers and ADR-0008's corollary sends a multi-consumer procedure to `pack/references/` rather than restating it. Nothing here adds a primitive; nothing here changes a seeded template.

**Tech Stack:** Markdown (the pack), stdlib `unittest` (the three guards), `bash` (installer). No pytest — the pack installs into arbitrary projects and cannot assume a runner.

**Spec:** [`docs/design/0010-degradation-is-recorded.md`](../design/0010-degradation-is-recorded.md), with [ADR-0008](../design/0008-step-invariants.md) and [ADR-0009](../design/0009-declared-writes-and-verified-authority.md) as the clauses it extends. Evidence: [`docs/validation/flow-execution-0.12.1.md`](../validation/flow-execution-0.12.1.md) (G1–G6) and [`docs/validation/errata-0.12.0.md`](../validation/errata-0.12.0.md) (#6, #8, #9).

---

## Global Constraints

Copied from ADR-0010 and this project's `CLAUDE.md`. Every task's requirements implicitly include this section.

- **Native-first.** No new primitive. If an existing component can host the behavior, that is the answer.
- **Clause 5 applies to this plan's own execution.** Verify every path, symbol, and line number against source before asserting it. Where a choice is arguable, decide and state the reasoning; escalate only when the answer turns on the user's priorities.
- **Clause 4 applies to this plan's own execution.** This plan asserts what pack files currently say. Re-grep the quoted text before editing; a quotation that no longer matches means an earlier task moved it, not that the file is wrong.
- **Never `git add -A` / `git add .`** — stage each task's files explicitly.
- **Propose before writing** for any durable-doc edit, per the `documenter` skill's cardinal discipline.
- **Design docs are the contract.** If implementation diverges from ADR-0010, update ADR-0010 with rationale in the same commit. No silent divergence.
- **No new per-feature artifact.** ADR-0010 adds one *reference* file (pack-tracked, shared) and one ledger **row type**. It does not add a durable artifact per feature.
- **Line numbers were verified on 2026-08-24** against commit `357ddad`. They drift as tasks land. **Re-grep before editing; the quoted text is authoritative and the line number is a hint.**
- **Out of scope, explicitly:** the `debugger` skill and the fan-out `reviewer` gate (slice 13); artifact dispositions and `/devkit-reconcile` (slice 10); slice 14's task 4 sweep is *in* scope (task 15) but its task 5 measurement lands as a recorded answer, not a new guard.

### The test cycle for this project

This repo authors markdown. Per `CLAUDE.md` working principle 4, the test analogue for a markdown task is a **behavioral prediction plus a fresh-session run**:

1. Before authoring, the prediction is already written — that is Task 1, and it runs first for the same reason a failing test does.
2. Author the file.
3. Run the example task in a fresh Claude Code session with the pack loaded.
4. Compare actual to predicted. **If behavior diverges from prediction, the pack content needs revision — not the prediction.**

Task 14 is the exception: it touches real Python and gets real TDD.

Three mechanical checks are cheap enough to run per task:

```bash
# A — the whole suite (must stay green after every task)
python3 -m unittest discover -s tests

# B — installer picks up new/changed pack files (no writes; safe to re-run)
./install.sh "$(mktemp -d)" --dry-run

# C — every pack citation resolves in a target install
python3 -m unittest tests.test_pack_references_resolve -v
```

---

## File Structure

**Created:**

| File | Responsibility |
|---|---|
| `pack/references/subagent-degraded-mode.md` | The one copy of clause 6b/6c: what to do when a subagent does not return, and who owns a file while it might still be alive. |
| `docs/validation/slice-15.md` | Behavioral predictions P1–P7, recorded before authoring and unrun until the dogfood. |
| `pack/templates/history/0.13.0/` | Seeded-template snapshot for the release guard. |

**Modified:**

| File | Change |
|---|---|
| `pack/commands/pr-review.md` | Phase A third skip condition (G5); Phase D stage 4 splits unconditionally (G4) |
| `pack/commands/feature-merge.md` | Merged-state check reads `PR:` (#6); gate rerun reads `Summary:` (#8); Gate 3 re-run rule (6a); Gate 3 spawn cites degraded mode (6b); merge proposal surfaces `DEG` rows |
| `pack/agents/security-reviewer.md` | *Grading your own recommendation* input + verdict; one anti-rationalization row (6a) |
| `pack/skills/engineer/SKILL.md` | Red-phase tester spawn cites degraded mode (6b/6c) |
| `pack/commands/build.md` | Halt conditions gain the non-returning tester (6b) |
| `pack/skills/documenter/SKILL.md` | `DEG` ledger row type; verification substep + § *Facts* citation (clause 4 swept) |
| `pack/devkit-orientation.md`, `README.md`, `CLAUDE.md` | New reference listed |
| `VERSION`, `pack/MIGRATIONS.md` | Release |
| `docs/design/inventory-and-build-order.md`, `CLAUDE.md` | Slice-15 entry moves from *recorded* to *shipped* |

**Deliberately not modified:** `pack/state.md.template`, `pack/CLAUDE.md.template`. Nothing in ADR-0010 changes a seeded file — see Task 17.

---

## Sequencing, and one ordering that is load-bearing

Phase A is four independent point fixes; any order works inside it. Phase B has one constraint that is not cosmetic:

**#8 lands before 6a.** Clause 6a *increases* the frequency of gate reruns, and #8 is a defect in the gate-rerun path — a rerun authors a second dated summary and overwrites `Summary:`. Shipping 6a while #8 is live makes a known defect fire more often than it does today. #8 is a prerequisite, not a co-traveller.

Phase C's reference (Task 9) precedes its three consumers (Tasks 10–12), per ADR-0008 clause 3: discovery precedes every consumer, and a citation to a file that does not exist yet is the *"citation is not a wiring"* failure ADR-0009 recorded twice.

**What this plan does not close.** Authoring these tasks does not validate them. Six defects came out of one execution after four review rounds of reading missed all of them; the closing event for slice 15 is the dogfood in Task 17's handoff, not the last commit here.

---

# Phase 0 — the predictions

## Task 1: Record P1–P7 before authoring anything

**Files:**
- Create: `docs/validation/slice-15.md`

**Interfaces:**
- Produces: the seven prediction IDs `P1`–`P7`, referenced by every later task's verification step.

- [ ] **Step 1: Write the predictions file**

```markdown
# Slice 15 — Behavioral predictions

**Slice:** 15 — degradation is recorded, not absorbed
**Design:** [`docs/design/0010-degradation-is-recorded.md`](../design/0010-degradation-is-recorded.md)
**Plan:** [`docs/plans/slice-15-degradation-is-recorded.md`](../plans/slice-15-degradation-is-recorded.md)
**Status:** predictions recorded, **unrun**
**Date:** 2026-08-24

---

## How to read this

Each prediction is written **before** the corresponding pack content is authored, per `CLAUDE.md` working principle 4. If behavior diverges from a prediction during the dogfood, **the pack content needs revision — not the prediction.**

**P2 blocks the slice.** The others revise it.

### P1 (G1) — a non-critical finding that gets fixed is re-gated

**Task:** `/feature-merge` on a feature where Gate 3 returns one *medium* finding. Accept it and fix it.
**Predicted:** Gate 3 re-runs after the fix, and its brief names the prior finding and the hunk that answers it. The reviewer returns a verdict on whether the mitigation achieves the property the finding named.
**Before this change:** the medium finding becomes a `SEC` row, the gate passes, and the fix is never reviewed.

### P2 (6b) — the pack never silently proceeds past a subagent that did not return  **(blocks the slice)**

**Task:** during `/build`'s red phase, cause the `tester` spawn to return nothing.
**Predicted:** the loop re-pings, then inspects the working tree for files the tester may have written, and reports what it found before doing anything else. It does **not** write the tests itself without saying that it is doing so.
**Before this change:** no text covers this; the behavior is whatever the operator improvises.
**If this fails, clause 6b is decoration and must not ship.**

### P3 (6b) — a degraded run is surfaced at the merge proposal

**Task:** `/feature-merge` on a feature whose findings ledger carries a `DEG` row.
**Predicted:** the merge proposal halts, names which assurance was reduced and why, and proceeds only on explicit acknowledgement.
**Before this change:** the reduction is invisible at merge time.

### P4 (G4) — `/pr-review` produces two commits

**Task:** a `/pr-review` pass that amends the summary and writes a ledger row.
**Predicted:** two commits — artifacts, then `.claude/state.md` alone.
**Before this change:** one combined commit, which `/feature-merge` names as the shape that breaks the discriminator.

### P5 (G5) — a second pass skips the pack's own empty review submission

**Task:** run `/pr-review`, let it post an inline reply, then run `/pr-review` again.
**Predicted:** the empty-bodied review submission the reply created is skipped as content-free, and the skipped count is reported.
**Before this change:** it satisfies neither skip condition and is offered as a new review item.

### P6 (clause 4 swept) — documenter will not assert an unverified quantifier

**Task:** ask `documenter` to record *"every current caller is safe"* in a summary, without having searched.
**Predicted:** it searches and cites `file:line`, or it marks the claim inferred. It does not propose the bare sentence.
**Before this change:** the claim passes through the proposal unchallenged — observed, and merged.

### P7 (#6) — the merged-state check reads the recorded PR

**Task:** `/feature-merge` from a branch whose own PR differs from `state.md`'s `PR:`.
**Predicted:** the recorded PR is queried; the feature's real state decides the path.
**Before this change:** an argument-less `gh pr view` inspects whatever PR belongs to the current branch.
```

- [ ] **Step 2: Verify the file resolves**

Run: `python3 -m unittest discover -s tests`
Expected: OK, 44 tests. (This file is under `docs/`, so no guard reads it; the run confirms nothing regressed.)

- [ ] **Step 3: Commit**

```bash
git add docs/validation/slice-15.md
git commit -m "docs: slice-15 predictions P1-P7, recorded before authoring"
```

---

# Phase A — the point fixes

## Task 2: G4 — `/pr-review` stage 4 splits unconditionally

**Files:**
- Modify: `pack/commands/pr-review.md` — Phase D, stage 4 (≈`:80–84`)

**Interfaces:**
- Consumes: nothing.
- Produces: a two-commit shape that Task 6's `Summary:` reader and `/feature-merge`'s discriminator both rely on.

- [ ] **Step 1: Replace stage 4 with two stages**

Find the paragraph beginning `4. **Commit the metadata.** Stage exactly what stages 2 and 3 wrote` and replace stages 4 through 5 numbering so the list reads:

```markdown
4. **Commit the artifacts.** Stage exactly what stages 2 and 3 wrote *other than* `.claude/state.md` — the summary doc and the discovered findings-ledger path — and propose a commit. Subject: `review: findings ledger + summary`. Stage explicitly; never `git add -A`.

5. **Commit `.claude/state.md` alone.** Subject: `review: state`. Two commits, in that order, always — not only when a baseline is in play.

   **Why unconditionally.** `/feature-merge` requires this split whenever a gate rerun records a `Gated baseline`, and it explains why: the discriminator excludes only `.claude/state.md`, so a combined commit puts gated content in a commit the exclusion does not account for, and the next invocation re-runs gates that already passed. `/feature-merge` owns that rule and this command does not restate it — see its *Why two commits*. What this command owns is not producing a commit shape the other command cannot consume. A conditional split ("only when a baseline is owed") puts the decision in the hands of a reader who has to know what the *other* command is going to do next; an unconditional split costs one extra commit on a metadata-only pass and cannot be got wrong.

   Stages 4 and 5 write durable artifacts and stage 6 pushes; without them, neither reaches the remote. The PR then lacks the `REV` record that is the whole point of a cross-feature deferral, and the tree stays dirty — which `/feature-merge`'s own preconditions treat as blocking, so the next closeout cannot check out mainline.

   **If the user declines either commit, stop here — do not proceed to stage 6.** Like every commit in this pack, it's a proposal the user may decline, but declining leaves the summary, ledger, and `state.md` edits uncommitted, and pushing the fix commits anyway would strand exactly those artifacts locally: the failure these stages exist to close. The user's options are to commit (editing the message or splitting further, if they want) or to stop and resolve the tree by hand; either way, re-run `/pr-review` once the tree is clean rather than continuing past the decline.
```

- [ ] **Step 2: Renumber the two stages that follow**

The old stages 5 and 6 (push-and-verify, replies) become **6** and **7**. Update the in-file cross-references that name them: *"Push before replying"*, the *Halt conditions* bullet naming *"Phase D stage 4"* — which becomes *"Phase D stages 4–5"* — and the *Common rationalizations* row citing *Phase D*.

- [ ] **Step 3: Verify no dangling stage numbers remain**

```bash
grep -n "stage 4\|stage 5\|stage 6\|stages 2 and 3" pack/commands/pr-review.md
```
Expected: every hit reads correctly against the new numbering; no reference to a "metadata commit" survives.

- [ ] **Step 4: Run checks A and C**

Run: `python3 -m unittest discover -s tests`
Expected: OK. `test_clause_one` must still find a carrier for this document's `**Writes:**` line — both new stages match `CARRIER_HEADING` on the word *commit*.

- [ ] **Step 5: Commit**

```bash
git add pack/commands/pr-review.md
git commit -m "fix: /pr-review splits its metadata commit unconditionally (G4)"
```

---

## Task 3: G5 — an item with an empty body carries no finding

**Files:**
- Modify: `pack/commands/pr-review.md` — Phase A, the skip conditions (≈`:40–47`)

**Interfaces:**
- Consumes: the existing two-condition skip list.
- Produces: a third condition, referenced by prediction P5.

- [ ] **Step 1: Add the third condition**

After the existing condition 2 (`**The item itself contains a marker.**`), insert:

```markdown
3. **The item's body is empty.** An empty body carries no finding, so there is nothing to triage. This is not a heuristic: GitHub wraps a reply posted through the replies endpoint in a **review submission**, which `gh pr view --json reviews` then returns as an entry authored by the replier with no body at all. It carries no marker because it has nowhere to put one, and no marker names its id because the marker in the reply names the *original* comment. A bare `APPROVED` with no body is the same shape and is likewise not a finding — the inline comments carry the content, and those are fetched separately.
```

- [ ] **Step 2: Extend the paragraph that explains why all three are needed**

Replace `Both checks must be implemented — an item matching *either* is skipped —` with `All three checks must be implemented — an item matching **any** is skipped —` and append to that paragraph:

```markdown
Condition 3 is the same defect one level up again. `in_reply_to_id` existed only on inline comments, so condition 2 replaced it; condition 2 reads a body, so a reply that becomes a *review* escapes it. Each fix closed the level in front of it. Condition 3 is content-free by construction rather than id-matching, which is why it closes every surface at once: an item with nothing in it cannot be a finding, whatever mechanism produced it.
```

- [ ] **Step 3: Scope the flag**

Find `**`/pr-review all` disables condition 1 only.**` and replace with:

```markdown
**`/pr-review all` disables condition 1 only.** Conditions 2 and 3 always apply, in any mode: an item carrying a devkit marker is the pack's own reply, and an item with an empty body has no content to re-triage. Disabling either would re-fetch the pack's own replies and offer to answer them — the exact recursion this section prevents, reintroduced by the flag meant to re-triage the reviewer's comments.
```

- [ ] **Step 4: Verify**

```bash
grep -n "condition 1\|condition 2\|condition 3\|Both checks" pack/commands/pr-review.md
python3 -m unittest discover -s tests
```
Expected: no surviving "Both checks"; suite OK.

- [ ] **Step 5: Commit**

```bash
git add pack/commands/pr-review.md
git commit -m "fix: an empty-bodied review submission carries no finding (G5)"
```

---

## Task 4: #6 — the merged-state check reads `state.md`'s `PR:`

**Files:**
- Modify: `pack/commands/feature-merge.md` — Preconditions, the merged-state paragraph (≈`:29`)

**Interfaces:**
- Consumes: `.claude/state.md`'s `PR:` field, which `/feature-merge` itself writes at PR creation (≈`:236`).
- Produces: the corrected precondition order that P7 tests.

- [ ] **Step 1: Replace the merged-state paragraph**

Find `**Check merged state first, before any other precondition.** Read `gh pr view --json state,mergedAt`.` and replace the sentence with:

```markdown
**Check merged state first, before any other precondition — and check it against the PR this feature recorded.** Read `.claude/state.md`'s `PR:` field, then `gh pr view <that PR> --json state,mergedAt`. With no argument, `gh pr view` reports *"the pull request that belongs to the current branch"*, which is a different question: on a head-deleting forge the closeout commonly runs from mainline, where no PR belongs to the branch at all, and from an unrelated branch it returns that branch's PR and decides this feature's path from it. The field holding the correct answer already exists — read it before using it, rather than reconstructing it from whatever is checked out. If `PR:` is unset, fall back to branch inference and say so.
```

- [ ] **Step 2: Cross-reference the precondition rather than moving it**

`feature-merge.md:37` numbers `PR:` is set as precondition 1 — but that list opens with *"With the PR confirmed open, the `in-review` rows have their own preconditions"*, so it is **scoped to the open-PR path** and cannot simply be hoisted above the merged-state check without changing what it governs. Do not restructure the block.

Instead, step 1's replacement text already reads the field where it is needed, and precondition 1 gains one line:

```markdown
   The merged-state check above reads this same field earlier and does not depend on this list — that check runs before the PR is known to be open, which is exactly when the current branch is least likely to be the feature's.
```

- [ ] **Step 3: Verify the ordering claim against the file**

```bash
grep -n "merged state\|PR:\` is set\|gh pr view" pack/commands/feature-merge.md | head -20
```
Expected: the `PR:` precondition line number is **lower** than the merged-state paragraph's.

- [ ] **Step 4: Run check A**

Run: `python3 -m unittest discover -s tests`
Expected: OK.

- [ ] **Step 5: Commit**

```bash
git add pack/commands/feature-merge.md
git commit -m "fix: merged-state check queries the recorded PR, not the current branch (#6)"
```

---

## Task 5: #9 — § *Discover* can report a tie

**Files:**
- Modify: `pack/references/artifact-locations.md` — § *Discover*, the output-contract paragraph

**Interfaces:**
- Consumes: § *Resolve*'s routing to § *Confirm*.
- Produces: a reportable third outcome, so a consumer is never forced to pick.

- [ ] **Step 1: Extend the output contract**

Find `Report exactly one of: a path per artifact type, or an explicit `"none found"`.` and replace with:

```markdown
Report exactly one of three, per artifact type: a path, an explicit `"none found"`, or an explicit **tie** — two or more candidate directories that provenance ranks identically. `"none found"` and a tie are both **answers**; silence is not. A consumer cannot distinguish "no directory exists" from "discovery never ran" from "discovery could not choose," and those call for three different behaviors.

**A tie is reported, never broken.** Step 3 ranks by provenance, and provenance genuinely cannot separate two directories that both hold files the pack did not write. That is not a malformed project: it is the ordinary state of a brownfield target that keeps plans in more than one place, which is this reference's own motivating example one step further on. Name every tied candidate and what each holds, and route to § *Confirm* — which says outright *"do not resolve it by picking."* A tie reported as a path is a guess wearing a result's clothes.
```

- [ ] **Step 2: Verify the tie language reaches § *Confirm***

```bash
grep -n "tie\|none found\|Silence is not" pack/references/artifact-locations.md
```
Expected: § *Confirm* already handles the occupied case; confirm no contradiction was introduced.

- [ ] **Step 3: Run checks A and C**

Run: `python3 -m unittest tests.test_pack_references_resolve -v && python3 -m unittest discover -s tests`
Expected: OK — every path this reference cites still resolves.

- [ ] **Step 4: Commit**

```bash
git add pack/references/artifact-locations.md
git commit -m "fix: Discover reports a tie rather than picking (#9)"
```

---

# Phase B — clause 6a, the gate contract

## Task 6: #8 — a gate rerun reads `Summary:` instead of authoring a second one

**Files:**
- Modify: `pack/commands/feature-merge.md` — *After all three gates pass* (≈`:165`) and the gate-rerun paragraph (≈`:242`)

**Interfaces:**
- Consumes: `.claude/state.md`'s `Summary:` field, written at first closeout.
- Produces: the invariant Task 7 depends on — reruns become frequent, so a rerun must be idempotent.

**⚠️ This task precedes Task 7 deliberately.** 6a increases rerun frequency; shipping it while this defect is live makes it fire more often.

- [ ] **Step 1: Make summary authoring conditional on the field**

In *After all three gates pass*, replace step 1's opening with:

```markdown
1. **If `.claude/state.md`'s `Summary:` field is `—`, write the summary** per the documenter's summary checklist, at the summaries directory the Orient step above resolved, named per that reference's § *Name*. Include the security-reviewer's non-critical findings in the "Security review notes" section. **Record the path it was written to in `.claude/state.md`'s `Summary:` field** — the filename carries this invocation's date, and `/pr-review` amends the file in a session that may be days later and cannot recompute it.

   **If `Summary:` already names a file, amend that file — do not author a second one.** A gate rerun on `in-review` reaches this step with a summary already written, at a filename carrying the *first* invocation's date. Authoring again produces a second dated file and overwrites the pointer, which strands the reviewed summary at a path nothing names and leaves `/pr-review` amending a document the PR body was never built from. Read the field, open that file, and propose the delta.
```

- [ ] **Step 2: Verify the field is written before it is read**

```bash
grep -n "Summary:" pack/commands/feature-merge.md pack/state.md.template
```
Expected: `state.md.template` carries a `Summary:` field (0.12.0 backfilled it) and the write at first closeout precedes the rerun read.

- [ ] **Step 3: Run check A**

Run: `python3 -m unittest discover -s tests`
Expected: OK.

- [ ] **Step 4: Commit**

```bash
git add pack/commands/feature-merge.md
git commit -m "fix: a gate rerun amends the recorded summary rather than authoring a second (#8)"
```

---

## Task 7: 6a — Gate 3 re-runs after any accepted finding

**Files:**
- Modify: `pack/commands/feature-merge.md` — Gate 3, both severity bullets (≈`:156–157`)

**Interfaces:**
- Consumes: Task 6's idempotent rerun.
- Produces: the re-gate obligation Task 8's `security-reviewer` brief answers.

- [ ] **Step 1: Rewrite the zero-critical bullet**

```markdown
- **Zero critical findings:** Gate 3 passes *as of the diff it just read*. Surface the full findings document to the user — they need to know the medium/low/informational items even though they don't block. **Record each of them as a `SEC` row in the findings ledger** (see the documenter skill's *The findings ledger* — its location is discovered, not assumed). The summary keeps its *Security review notes* section and cross-references the row IDs rather than restating them. Without the ledger these findings ship and are never seen again; the summary is a document nobody reopens.

  **If the user chooses to fix any of them, the gate is no longer passed.** A fix produces code Gate 3 has never read, on the hunk the review just identified as the most security-relevant in the diff. Re-run from Gate 1 — fixes touch code, so tests and docs are in scope too — and re-run Gate 3 with the *grading* brief below. This holds at every severity: the severity threshold decides whether the merge **blocks**, and it has never been the right input to whether something has been **reviewed**.
```

- [ ] **Step 2: Rewrite the critical bullet so both branches state one rule**

```markdown
- **One or more critical findings:** halt. Surface the findings. User addresses (either by fixing the code, amending the spec/plan via `/checkpoint`, or — rarely — formally accepting the risk with an ADR that downgrades the finding). Then re-run the full sequence from Gate 1, since fixes touch code, with Gate 3 carrying the grading brief. Same rule as the bullet above; the difference between the two branches is whether the merge was blocked in the meantime, not whether the fix gets reviewed.
```

- [ ] **Step 3: Add the grading brief to the Gate 3 spawn list**

In the `Pass:` list at the top of Gate 3, add:

```markdown
- **When this run follows a fix made on Gate 3's own recommendation:** the prior finding, verbatim, and the commit or hunk that answers it. Say plainly that the reviewer is **grading its own prior recommendation**, and that the question is whether the mitigation achieves the property the finding named — not whether the code matches what was recommended. This input is what fresh context cannot supply: the reviewer has no way to know a hunk exists *because* Gate 3 asked for it, and will otherwise read the recommended pattern in the diff as evidence that the risk is handled.
```

- [ ] **Step 4: Verify the `**Writes:**` line still covers this gate**

```bash
grep -n -A2 "Writes:" pack/commands/feature-merge.md | grep -n "findings ledger"
python3 -m unittest discover -s tests
```
Expected: Gate 3's declaration is unchanged (it still writes only `SEC` rows) and `test_clause_one` stays green.

- [ ] **Step 5: Commit**

```bash
git add pack/commands/feature-merge.md
git commit -m "feat: Gate 3 re-runs after any accepted finding, at any severity (ADR-0010 6a)"
```

---

## Task 8: 6a — `security-reviewer` learns to grade its own recommendation

**Files:**
- Modify: `pack/agents/security-reviewer.md` — *What you receive* (≈`:13–24`), *How to review* (≈`:34`), *Common rationalizations* (≈`:105`)

**Interfaces:**
- Consumes: the grading brief Task 7 added to the Gate 3 spawn list — same wording on both sides.
- Produces: a verdict field the command reads.

- [ ] **Step 1: Add the input to *What you receive***

```markdown
- **A prior finding of your own, when this run follows a fix made on your recommendation.** The finding verbatim, plus the hunk that answers it. This is the one input you cannot derive from the diff: fresh context is what keeps you objective about the implementer's choices, and it is also what stops you knowing that a line exists *because you asked for it*. Without this input you will read your own recommended pattern as evidence the risk is handled.
```

- [ ] **Step 2: Add the review step**

In *How to review*, after the diff step:

```markdown
6. **If you were given a prior finding: grade it, and say so explicitly.** The question is not *"does this code look like what was recommended?"* — it is *"does this achieve the property the finding named?"* Name the property in your own words first, then check the code against it. A recommendation names a mechanism; a finding names a guarantee, and a mechanism can be present and the guarantee absent. Return one of **achieved** / **not achieved** / **cannot tell from the diff**, with the evidence. "Cannot tell" is a real answer and is better than a confident wrong one; say what you would need to see.
```

- [ ] **Step 3: Add the anti-rationalization row**

```markdown
| "The fix matches what I recommended, so it's handled." | You recommended a *mechanism*; the finding named a *property*. The mechanism can be present and the property absent — a locking read that returns a cached object takes the lock and reads stale state. Check the property. (See *How to review*, step 6.) |
```

- [ ] **Step 4: Verify both sides of the interface agree**

```bash
grep -n "grading\|grade it\|prior finding\|property the finding named" pack/commands/feature-merge.md pack/agents/security-reviewer.md
```
Expected: the command's spawn list and the agent's input section describe the same object, in the same terms.

- [ ] **Step 5: Run check A and commit**

```bash
python3 -m unittest discover -s tests
git add pack/agents/security-reviewer.md
git commit -m "feat: security-reviewer grades its own prior recommendation (ADR-0010 6a)"
```

---

# Phase C — clauses 6b and 6c

## Task 9: The degraded-mode reference

**Files:**
- Create: `pack/references/subagent-degraded-mode.md`

**Interfaces:**
- Produces: the section names `§ Detect`, `§ Decide`, `§ Ownership`, and `§ Record` — cited verbatim by Tasks 10, 11, and 12. **A citing site names a section; it does not restate its content.**

- [ ] **Step 1: Write the reference**

```markdown
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
```

- [ ] **Step 2: Verify every path it cites resolves in an install**

Run: `python3 -m unittest tests.test_pack_references_resolve -v`
Expected: OK. This test caught a dangling path in slice 12's new reference — it is the guard that matters for this task.

- [ ] **Step 3: Verify the installer picks it up**

Run: `./install.sh "$(mktemp -d)" --dry-run`
Expected: the new file appears in the tracked set — `TRACKED_DIRS` already covers `references/`, so no installer change is needed. **If it does not appear, stop**: the reference is uninstallable and every citation added in Tasks 10–12 would dangle.

- [ ] **Step 4: Commit**

```bash
git add pack/references/subagent-degraded-mode.md
git commit -m "feat: pack/references/subagent-degraded-mode.md (ADR-0010 6b, 6c)"
```

---

## Task 10: Wire `engineer` and `/build`

**Files:**
- Modify: `pack/skills/engineer/SKILL.md` — Red, step 2 (≈`:35`) and the refusal paragraph (≈`:47`)
- Modify: `pack/commands/build.md` — Halt conditions

**Interfaces:**
- Consumes: `§ Detect`, `§ Decide`, `§ Ownership`, `§ Record` from Task 9.

- [ ] **Step 1: Extend the engineer's refusal paragraph**

After `If the tester returns **findings and no tests**, that is a refusal…`, add:

```markdown
**If the tester returns nothing at all, that is not a refusal — it is a missing answer**, and the two call for opposite responses. A refusal means the brief was unbuildable and the contract needs fixing. Silence means you do not yet know what happened. Work `.claude/references/subagent-degraded-mode.md` § *Detect* before concluding anything, and § *Ownership* before writing to any path the tester was asked to produce. If you proceed without the tester, fresh context is spent — § *Decide* is the trade, and § *Record* is the `DEG` row it costs.
```

- [ ] **Step 2: Extend the engineer's `**Writes:**` line**

```markdown
**Writes:** this step's test files · **the findings ledger, at its discovered path, when triage routes an out-of-scope finding to it, or when § *Record* requires a `DEG` row.**
```

- [ ] **Step 3: Add the halt condition to `/build`**

```markdown
- The `tester` returns **nothing**, and `.claude/references/subagent-degraded-mode.md` § *Detect* has been worked without finding its output. Surface the trade named in § *Decide*; do not write the step's tests in the main loop without saying so and recording it.
```

- [ ] **Step 4: Verify the citations resolve and the declaration has a carrier**

```bash
python3 -m unittest tests.test_pack_references_resolve tests.test_clause_one -v
```
Expected: OK — the new citation path resolves and the engineer's carrier still stages what it declares.

- [ ] **Step 5: Commit**

```bash
git add pack/skills/engineer/SKILL.md pack/commands/build.md
git commit -m "feat: engineer and /build handle a tester that does not return (ADR-0010 6b)"
```

---

## Task 11: Wire `/feature-merge`'s Gate 3 spawn

**Files:**
- Modify: `pack/commands/feature-merge.md` — Gate 3 (≈`:146`)

**Interfaces:**
- Consumes: `§ Detect`, `§ Decide`, `§ Record` from Task 9; Task 7's rewritten bullets.

- [ ] **Step 1: Add the non-return case to Gate 3**

After the severity bullets:

```markdown
- **The subagent returns nothing:** Gate 3 has not run, and a gate cannot report a pass it did not compute. Work `.claude/references/subagent-degraded-mode.md` § *Detect*, then re-invoke — a fresh security pass is cheap relative to the assurance it carries. If the user chooses to proceed without it, that is § *Decide*'s trade and it costs a `DEG` row per § *Record*. **Do not record Gate 3 as passed.**
```

- [ ] **Step 2: Extend Gate 3's `**Writes:**`**

```markdown
**Writes:** the findings ledger — `SEC` rows when the review produces non-critical findings, and a `DEG` row if the review did not run.
```

- [ ] **Step 3: Verify**

```bash
python3 -m unittest discover -s tests
```
Expected: OK.

- [ ] **Step 4: Commit**

```bash
git add pack/commands/feature-merge.md
git commit -m "feat: Gate 3 cannot pass a review that did not run (ADR-0010 6b)"
```

---

## Task 12: The `DEG` row, and surfacing it at the merge proposal

**Files:**
- Modify: `pack/skills/documenter/SKILL.md` — *The findings ledger* → *The shape* (≈`:196`)
- Modify: `pack/commands/feature-merge.md` — *Merge proposal* / *PR creation*

**Interfaces:**
- Consumes: the `DEG` row type, written by Tasks 10 and 11.
- Produces: the halt P3 tests.

- [ ] **Step 1: Add `DEG` to the ledger's category list**

Replace the categories sentence with:

```markdown
Categories map to producers: **`CONF`** (conformance-reviewer), **`SEC`** (security-reviewer), **`ARCH`** (an architect recommendation that produced no ADR), **`REV`** (external PR review), **`DEG`** (an assurance the pack advertises that did not hold for this feature — see `.claude/references/subagent-degraded-mode.md` § *Record*).
```

Add a row to the example table:

```markdown
| DEG-001 | degraded | — | engineer · notes-write step 3 | open | tester did not return; tests written in main loop |
```

- [ ] **Step 2: Note why `DEG` has no severity**

```markdown
A `DEG` row's Severity is `—` on purpose. A degradation is not a finding about the code; it is a fact about how much the record can be trusted, and grading it invites the arithmetic where two mediums equal a high. What matters is that it is **open** — an open `DEG` row means an advertised guarantee did not hold and nobody has decided what to do about it.
```

- [ ] **Step 3: Add the surface-and-ask to the merge proposal**

Immediately before the proposal is put to the user, in **both** *Merge proposal* and *PR creation*:

```markdown
**Before proposing: read the findings ledger for open `DEG` rows on this feature.** If any exist, state each one — which assurance was reduced, why, and what was done instead — and ask whether to proceed. Do not fold it into the proposal as a bullet; it is a different question from *"shall I merge this"* and it is the one the user is least likely to have been told about, because the run that produced it was a run where something went wrong.

This is the pack's untracked-files rule applied to assurance: *don't silently proceed, and don't silently treat it as blocking.* The user is the only one who can weigh a harness flake against a release. What is not optional is that they are told at the moment the decision is made, rather than finding the row later.
```

- [ ] **Step 4: Verify both proposal paths carry it**

```bash
grep -n "DEG" pack/commands/feature-merge.md pack/skills/documenter/SKILL.md
```
Expected: hits in *Merge proposal* **and** *PR creation* — the two paths are separate sections and a fix to one is not a fix to the other.

- [ ] **Step 5: Run check A and commit**

```bash
python3 -m unittest discover -s tests
git add pack/skills/documenter/SKILL.md pack/commands/feature-merge.md
git commit -m "feat: DEG rows, surfaced at the merge proposal (ADR-0010 6b)"
```

---

# Phase D — clause 4, swept

## Task 13: `documenter` verifies before it proposes

**Files:**
- Modify: `pack/skills/documenter/SKILL.md` — *The cardinal discipline* (≈`:14–24`)

**Interfaces:**
- Consumes: `.claude/references/evidence-and-uncertainty.md` § *Facts* — which this skill currently never cites.
- Produces: the behavior P6 tests.

- [ ] **Step 1: Insert a verification step into the numbered procedure**

The procedure is currently 1–4 (identify → produce a diff → surface → iterate). Insert a new step 2, renumbering the rest:

```markdown
2. **Verify every load-bearing claim in the proposal before you show it.** A proposal asks whether to write something; it does not ask whether it is true, and the user reviewing it is the person least able to falsify a confident sentence you wrote. `.claude/references/evidence-and-uncertainty.md` § *Facts* is the rule: any assertion about the project carries its provenance — backed by `file:line`, or explicitly marked as inferred. Silence about provenance reads as verified.

   **A claim quantified over the codebase gets searched, or it gets rewritten.** *"Every current caller is safe"*, *"no other path reaches this"*, *"all consumers were updated"* — each is a claim about files you have not read unless you went and read them. Run the search, cite what you found, or narrow the sentence to what you actually checked. A quantifier is the cheapest sentence to write and the most expensive to be wrong about: it merges, and every later feature is built on it.
```

- [ ] **Step 2: Add the anti-rationalization row**

```markdown
| "It's obviously true — I don't need to check it." | Obviousness is not provenance, and the reader cannot tell the two apart in a finished sentence. The false claim that shipped was obvious to the person who wrote it. One search costs a round-trip; a wrong durable claim costs every feature built on it. (See *The cardinal discipline*, step 2.) |
```

- [ ] **Step 3: Verify the citation resolves**

```bash
grep -n "evidence-and-uncertainty" pack/skills/documenter/SKILL.md
python3 -m unittest tests.test_pack_references_resolve -v
```
Expected: two citations now — § *Judgment* (existing) and § *Facts* (new). Before this task there was one.

- [ ] **Step 4: Commit**

```bash
git add pack/skills/documenter/SKILL.md
git commit -m "feat: documenter verifies claims before proposing them (ADR-0009 clause 4, swept)"
```

---

## Task 14: Measure whether skills can come under `test_clause_one`

**Files:**
- Modify (possibly): `tests/test_clause_one.py`
- Modify: `docs/validation/slice-15.md` — record the measurement either way

**Interfaces:**
- Consumes: `pack_documents()`, which already globs `skills/*/SKILL.md`, and `phase_sections()`, which for skills splits only on `Phase|Gate` headings.

This is slice 14's task 5, inherited. It is a **measurement**, and a negative result is a result — record it and move on.

- [ ] **Step 1: Measure before changing anything**

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, "tests")
from test_clause_one import pack_documents, phase_sections, _split, SUB_HEADING, WRITE_VERBS, DURABLE_TARGET, WRITES_LINE, CARRIER_HEADING
flagged = []
for path, text, is_command in pack_documents():
    if is_command: continue
    for heading, body in _split(text, SUB_HEADING):
        if CARRIER_HEADING.search(heading): continue
        if WRITE_VERBS.search(body) and DURABLE_TARGET.search(body) and not WRITES_LINE.search(body):
            flagged.append(f"{path.name} :: {heading}")
print(len(flagged)); print("\n".join(flagged))
PY
```

- [ ] **Step 2: Decide on the number, not on principle**

The existing scoping comment records the standard: widening to every heading flagged 54 sections and 4 were real, so it was rejected — *"a guard that cries wolf is a guard that gets an allowlist, and an allowlist here is the cached-discovery failure clause 3 forbids."* Apply the same test here. **If the true-positive rate is comparable to the commands' (3 of 4), widen `phase_sections()` to split skills on `###` headings. If it is not, do not widen.**

- [ ] **Step 3: If widening — TDD it**

Add a failing test asserting a known skill subsection that writes durably is flagged; run it (expect FAIL); make the change; run it (expect PASS); confirm the whole suite stays green.

- [ ] **Step 4: Record the measurement in `docs/validation/slice-15.md` either way**

Add a short section naming the number flagged, how many were real, and the decision. A measurement taken and not written down gets retaken.

- [ ] **Step 5: Commit**

```bash
git add tests/test_clause_one.py docs/validation/slice-15.md   # drop the test file if not widened
git commit -m "test: settle whether skills can come under clause-1 enforcement"
```

---

## Task 15: The reconstruct-vs-read sweep

**Files:**
- Modify: whichever of `pack/commands/*.md`, `pack/skills/*/SKILL.md`, `pack/agents/*.md` the sweep implicates

Slice 14's task 4, inherited, and now carrying a second lens.

- [ ] **Step 1: Sweep under both lenses**

For every command, skill, and agent **not already touched by Tasks 2–13**, ask two questions:

1. **Reconstruct-vs-read** (0.12.1 errata): does this step rebuild a value that a field nearby already holds? Tasks 4 and 6 fixed two instances; the lens is what finds the rest.
2. **Assurance decay** (ADR-0010): does this step report an assurance whose computation could have stopped covering what it names? That is clause 6's general form, and Tasks 7 and 11 fixed the two known instances.

- [ ] **Step 2: Record findings; fix only what is unambiguous**

An instance that is clearly the same defect gets fixed here. An instance that needs a design call gets a row in `docs/validation/slice-15.md` and a decision later. **Do not expand this task into a redesign** — it is a sweep, and the point is coverage.

- [ ] **Step 3: Run the full suite and commit**

```bash
python3 -m unittest discover -s tests
git add -- pack docs/validation/slice-15.md   # explicit paths only, never -A
git commit -m "fix: reconstruct-vs-read and assurance-decay sweep across untouched components"
```

---

## Task 15b: The six skill declarations (added during execution)

**Added at the owner's direction after Task 14's measurement**, which found the gap and recorded it rather than fixing it. Folded in here rather than deferred to a later slice because every command that derives a staging list from declarations was blind to all six, and that is errata F3's failure shape in the two skills that write the most.

**Files:**
- Modify: `pack/skills/documenter/SKILL.md` — *Pattern A*, *Pattern C*, *Pattern D*, *Domain doc updates*; new `## Who commits what you write`
- Modify: `pack/skills/pm/SKILL.md` — *4. Draft the spec*, *Producing the plan*; new `## Who commits what you write`

**What was verified before declaring** (clause 5, and the rule Task 13 had just added to `documenter` itself): each section was read before its declaration was written. Two results changed what got declared — *Pattern A* does **not** touch `.claude/state.md` in its own loop, and *Pattern D* writes **nothing**, so it declares `none` and names Pattern A as where a confirmed amendment actually lands.

**Why each skill needed a carrier section.** `test_clause_one`'s second assertion requires any document containing a `**Writes:**` line to have a heading matching `commit|hand off`. Skills legitimately have neither — the invoking command carries every commit. Rather than claim the file-wide `**Clause 1 exception:**`, which would have skipped these documents from *both* assertions and undone the declarations' purpose, each skill gained a `## Who commits what you write` table naming the carrying command per artifact. The guard is satisfied by a true statement rather than by an exemption.

# Phase E — release

## Task 16: Wire the new reference into the three places that list references

**Files:**
- Modify: `pack/devkit-orientation.md`, `README.md`, `CLAUDE.md`

- [ ] **Step 1: Add it to the two filename enumerations**

Exactly two places list the references by filename, and both need the new entry with a half-line gloss — *"what to do when a subagent does not return, and who owns a file while it might still be alive"*:

- `CLAUDE.md:39` — the `**References:**` bullet in § *Shipped*.
- `README.md:120` — the **References** row of the components table.

- [ ] **Step 2: Update the orientation's prose gloss**

`pack/devkit-orientation.md:22–23` does **not** list filenames; it carries a parenthetical of topics:

```
  references/              checklists loaded on demand (SOLID, Clean Arch, security
                           categories, findings triage, spec/plan depth, CLAUDE.md elements)
```

Add `subagent degraded mode` to that parenthetical. Do not convert it into a filename list — it is a tree diagram, and the two forms serve different readers.

- [ ] **Step 3: Verify no list was missed**

```bash
grep -rn "spec-and-plan-depth\|spec/plan depth" --include=*.md . | grep -v "^./docs/"
```
Expected: three hits — `CLAUDE.md`, `README.md`, `pack/devkit-orientation.md` — and each now also names the new reference. That grep is the enumeration-finder: `spec-and-plan-depth` is the most recently added reference before this one, so anywhere it appears is a list that grew last time and must grow again.

- [ ] **Step 4: Commit**

```bash
git add pack/devkit-orientation.md README.md CLAUDE.md
git commit -m "docs: list subagent-degraded-mode.md wherever references are enumerated"
```

---

## Task 17: Release 0.13.0

**Files:**
- Modify: `VERSION`, `pack/MIGRATIONS.md`, `CLAUDE.md`, `docs/design/inventory-and-build-order.md`
- Create: `pack/templates/history/0.13.0/`

Follow `CLAUDE.md` § *Releasing the pack* exactly. **Step 1 is the one that matters** — PR #139's finding 1 was a migration entry written from recollection.

- [ ] **Step 1: Diff the seeded templates against the last snapshot**

```bash
diff -u pack/templates/history/0.12.0/state.md.template pack/state.md.template
diff -u pack/templates/history/0.12.0/CLAUDE.md.template pack/CLAUDE.md.template
```
Expected: **no differences.** ADR-0010 changes no seeded file. If either diff is non-empty, an earlier task changed a seeded template without saying so — stop and account for it before continuing.

- [ ] **Step 2: Write the MIGRATIONS section anyway**

```markdown
## 0.13.0

**No seeded-file changes.** `state.md.template` and `CLAUDE.md.template` are byte-identical to 0.12.0; existing installs need no hand edit for this release.

Recorded explicitly rather than omitted. A missing section is indistinguishable from a forgotten one, and a forgotten one is exactly how 0.10.0's entry shipped incomplete. This release's own subject is that a silent absence reads as an assurance.

What *did* change is pack-owned and arrives by re-running `install.sh`: the Gate 3 re-run rule, `security-reviewer`'s grading brief, `pack/references/subagent-degraded-mode.md` (new), the `DEG` ledger row type, `documenter`'s verification step, and four defect fixes in `/pr-review` and `/feature-merge`.
```

- [ ] **Step 3: Bump and snapshot**

```bash
echo "0.13.0" > VERSION
mkdir -p pack/templates/history/0.13.0 && cp pack/*.template pack/templates/history/0.13.0/
```

- [ ] **Step 4: Run the release guard**

```bash
python3 -m unittest discover -s tests
```
Expected: OK — `test_migrations_snapshot` asserts the `0.13.0` snapshot exists and byte-matches, and that a differing snapshot carries a `## 0.13.0` section.

- [ ] **Step 5: Move slice 15 from *recorded* to *shipped***

Update `CLAUDE.md`'s slice-15 bullet and `docs/design/inventory-and-build-order.md` § *Slice 15* to state what shipped, and to say plainly that **the predictions are recorded and unrun**.

- [ ] **Step 6: Commit**

```bash
git add VERSION pack/MIGRATIONS.md pack/templates/history/0.13.0 CLAUDE.md docs/design/inventory-and-build-order.md
git commit -m "release: 0.13.0 -- ADR-0010 and slice-14's remaining three"
```

---

## After this plan

**The slice is authored, not validated.** Seven predictions are recorded and unrun; P2 blocks the slice, and nothing in this plan runs it.

The closing event is the dogfood: upgrade the target to 0.13.0, then run one feature end to end with a deliberately killed `tester` spawn (P2), a non-critical security finding that gets fixed (P1), and a `/pr-review` pass with a real reply (P4, P5). P3 and P6 fall out of the same run. P7 needs a checkout on the wrong branch, which costs one `git checkout`.

That ordering is the round's own finding applied to itself: **execution is what has found every defect of this class, and reading is structurally poor at absence.** Three of slice 15's six inputs were things the pack never said.
