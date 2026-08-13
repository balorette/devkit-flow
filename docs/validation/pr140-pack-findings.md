# Pack Findings — Enterprise API 0.11.0 Upgrade

**Source:** [example-corp/enterprise-api#140](https://github.com/example-corp/enterprise-api/pull/140) — automated review (Codex, Cursor Bugbot) of the 0.10.0 → 0.11.0 upgrade
**Pack version reviewed:** 0.11.0
**Status:** 8 raw findings → **7 unique**, all verified against `pack/` source before filing. 0 host-project findings.
**Date:** 2026-08-10

---

## What this is

The Enterprise API upgrade to 0.11.0 drew eight automated review findings. **All eight are pack-authored files** — unlike #139, which mixed four host-project findings in, this round produced none. The upgrade changed nothing under `src/` or `tests/`, so every reviewer comment landed on `.claude/`.

Two of the eight are the same defect reported by both reviewers (Bugbot's *In-review sync misses remote-ahead case* and Codex's *Require exact tip equality*). Merged as **#1** below. Seven unique findings remain.

Verified against `pack/` rather than the vendored copy. Every quotation below is from `pack/`, checked at filing time.

**Still not a dogfood.** No pack command has executed. Findings 1–4 all concern `/feature-merge`'s `in-review` re-entry path — the path 0.11.0 substantially rewrote — and that path has never run. They are control-flow reasoning against text, which is what the pack keeps producing findings from.

---

## The theme worth naming first

**0.11.0 violates its own ADR-0008 clause 1 in the row that ADR-0008 added.**

Clause 1 is *an artifact and its carrier commit together*. The slice applied it to `/plan` Phase G and `/pr-review` Phase D. But the new gate-rerun row in `/feature-merge`'s entry-state table (finding **#3**) says:

> Re-run gates 1–3 … then update `Gated baseline`, commit `.claude/state.md` **only**, and push.

Gate 2 reconciles docs. Gate 3 writes `SEC` rows to the findings ledger. Both produce artifacts; `commit .claude/state.md only` strands them. The pack already knows this — `feature-merge.md:137` gets it *right* for the closeout commit, staging "the findings ledger if Gate 3 wrote `SEC` rows to it," with a paragraph explaining that an uncommitted ledger row "is the durable-memory failure the ledger was added to fix, reproduced one layer down."

So the rule is stated, correct, and applied one section away from where it's broken. **Clause 1 was applied to the sites the #139 review named, not swept across the pack.** That's the actionable process point: the clause needs a sweep, not a patch list.

A second, smaller theme in **#5** and **#7** — clause 3 (*discovery precedes every consumer*) has the same shape of incompleteness. `pm` routes a drafted ADR back into `related_adrs`; `engineer` doesn't. `adr-registry.md` says the location "may be recorded" but its `Discover` scope can't re-read a recorded location outside `docs/`.

---

## Finding 1 — `in-review` precondition is one-sided: catches local-ahead, misses local-behind

**Severity: medium.** Reported independently by both reviewers. Gates run against content the PR doesn't have.

`feature-merge.md:29-32`:

> **Local and remote agree.** No uncommitted changes to tracked files, and the local branch **is not ahead of** the remote.

and the halt condition at `:227`:

> local `HEAD` **ahead of** what `git ls-remote origin <branch>` reports.

Both are directional. When another clone or the web UI pushes to the PR, local is **behind**, not ahead — the precondition passes. The next step is:

> With that established, fetch the PR tip locally before diffing against it: `git fetch origin <branch>`

`git fetch` makes the object available; it does not move `HEAD`. So the discriminator reads the **new** PR tip while gates 1–3 — including Gate 3's `mainline...HEAD` diff — execute against **stale local content**. The subsequent state-only push is then a non-fast-forward.

The stated rationale for the check is exactly this failure, in mirror image: "the discriminator below reasons about the PR's remote content, and that framing is only correct when local and remote already agree." One-directional agreement isn't agreement.

**Suggested fix (Codex):** require local `HEAD` to *equal* the `ls-remote` OID, or update the checkout before running the discriminator and gates.

---

## Finding 2 — merged-state check ordered after a precondition that a deleted head ref fails

**Severity: high.** Blocks closeout on any forge that auto-deletes head branches.

The preconditions are introduced as applying to the `in-review` **rows** (plural), "checked **before** the discriminator runs" — and the row set includes `in-review, PR merged`. When the forge deletes the head branch on merge, `git ls-remote origin <branch>` returns no OID. `git ls-remote -h` does not error on no-match unless `--exit-code` is passed, so the precondition sees an empty result rather than a failure, and the local checkout reads as diverged/unpushed → **halt**, before the `in-review, PR merged` closeout can clear state.

The halt list does contain "`gh pr view` fails while checking merged state," so a merged-state check exists — but nothing orders it *before* precondition 2.

**Suggested fix (Codex):** detect `state,mergedAt` first; apply the local/remote synchronization requirement only while the PR is still open.

---

## Finding 3 — gate-rerun row commits `state.md` only, stranding Gate 2 and Gate 3 artifacts

**Severity: high.** This is the clause-1 violation described in *The theme worth naming first*.

`feature-merge.md:24` (entry-state table, `in-review` / gated content changed):

> Re-run gates 1–3 … then update `Gated baseline`, commit `.claude/state.md` only, and push.

Gate 2 reconciles documentation; Gate 3 can write non-critical `SEC` rows to the findings ledger. Both leave files other than `state.md` modified. Committing only `state.md`:

1. leaves the tree dirty, which **finding #1's own precondition** ("no uncommitted changes to tracked files") will halt on at the next invocation — the row breaks the path it returns to;
2. pushes a new `Gated baseline` asserting content passed gates, while the gates' own output is absent from the branch.

Contrast `feature-merge.md:137`, which handles the identical concern correctly for closeout.

**Suggested fix (Codex):** route reruns through an explicit artifact commit before the state-only baseline commit.

---

## Finding 4 — `in-review` precondition checks tracked files only; untracked implementation slips past the gates

**Severity: high.** A PR can be marked gated without the code that made its tests pass.

Precondition 2 is scoped to "no uncommitted changes to **tracked** files." A review fix that adds a new source or test file and forgets to `git add` it leaves local `HEAD` equal to the remote OID — precondition passes. Gates then run **green against a working tree containing the untracked implementation**, while the state-only commit and push omit it. The remote PR gets a `Gated baseline` it did not earn.

The pack already has the right handling for this, on the other path — `feature-merge.md:69`:

> Untracked files present → surface them and ask before proceeding. An untracked file is as likely to be a source file the engineer forgot to `git add` … as it is to be build detritus.

It simply isn't applied to the `in-review` path. Same shape as finding #3: correct rule, one section away.

**Suggested fix (Codex):** apply the existing building-phase untracked-file prompt to the `in-review` path before running any gates.

---

## Finding 5 — `adr-registry.md` discovery cannot re-read a location it told you to record

**Severity: medium.** Reintroduces the duplicate-registry failure the file was written to prevent.

`adr-registry.md` § *Discover* → *Scope*:

> `*.md` under `docs/`, plus root-level `*.md`.

But § *Never cache the number* says:

> **The location may be recorded.** The number may not be trusted.

A project keeping decisions at `architecture/decisions/`, `.github/decisions/`, or any non-`docs/` path is outside the scan even when `CLAUDE.md` records the exact location. Discovery reports "none found," callers pass `registry: none found` to the architect, and § *Allocate* step 5's recorded high-water mark is unreachable — so the pack may create a second `docs/adr/` registry. That is precisely the duplicate-ID failure the file's own step 3 forbids.

Note this is *not* hypothetical for the file's motivating example: the Enterprise API registry is a single log under a `docs/` subdirectory, so it happens to be in scope. A registry one directory to the left is not.

**Suggested fix (Codex):** scan the recorded location in addition to the default scope, or broaden discovery to all eligible tracked Markdown files.

---

## Finding 6 — `architect.md` gives two contradictory instructions for missing ADR inputs

**Severity: medium.** Two defensible behaviors, and which one fires is undefined.

`architect.md:22`:

> **Being passed nothing at all — no paths and no explicit "none found" — is different: that is a caller bug.** Name it in your response …, **and still answer the question.**

`architect.md:25`, four lines later, closing the inputs list:

> If **any of the above** is missing or unclear, **ask the caller a clarifying question instead of guessing**.

ADR paths are one of "the above." So the architect is told both to answer anyway and to stop and ask. Depending on which wins, it either produces a recommendation formed without decisions it may contradict, or unexpectedly blocks the calling workflow.

**Suggested fix (Codex):** pick one and state it once. Codex favors asking, on the file's own stated safety rationale; note that the "still answer" branch has a rationale too (a caller bug shouldn't deadlock the workflow), so this is a real decision rather than a typo.

---

## Finding 7 — build-time ADRs are written but never linked from spec or plan

**Severity: medium.** The merge-time security reviewer cannot see the decision that authorized the architecture it's reviewing.

`engineer/SKILL.md:81`:

> If the architect drafts an ADR in response (build-time or plan-time), allocate and write it per `.claude/references/adr-registry.md` § *Allocate* …

Allocate and write — with no step adding the number to the spec's or plan's front-matter `related_adrs`. And `security-reviewer.md:19` reads related ADRs from exactly that field:

> **Related ADRs** named in the spec/plan's `related_adrs` front-matter

The asymmetry is the tell: `pm/SKILL.md:207` *does* close this loop at brainstorm time ("reference it in the spec's front-matter `related_adrs`"), and `feature-start.md:80` does it again. `engineer` is the one architect caller that writes an ADR without linking it. The result is an ADR that is undiscoverable from the feature history and invisible at merge.

**Suggested fix (Codex):** route the decision through `/checkpoint` and amend the applicable `related_adrs` before continuing the build.

---

## Suggested disposition

| # | Area | Sev | Note |
|---|---|---|---|
| 1 | `feature-merge` in-review sync | med | Both reviewers, independently |
| 2 | `feature-merge` merged-state order | high | Blocks closeout on auto-delete forges |
| 3 | `feature-merge` gate-rerun commit | high | **Clause-1 violation in the clause-1 release** |
| 4 | `feature-merge` untracked files | high | Gated baseline without the code |
| 5 | `adr-registry` discovery scope | med | Duplicate-registry risk returns |
| 6 | `architect` missing-input rule | med | Genuine decision, not a typo |
| 7 | `engineer` build-time ADR linking | med | `pm` does this; `engineer` doesn't |

Four of seven are one file (`commands/feature-merge.md`) and one path (`in-review` re-entry). That path is 0.11.0's largest rewrite and has never executed. **The highest-value next move is behavioral, not textual:** run the Enterprise API PR through a real `/feature-merge` re-entry — reopen, push a review fix from a second clone, re-run — which would settle #1, #2, #3, and #4 at once.

The two clause sweeps (clause 1 across every artifact-writing step; clause 3 across every registry consumer) are the textual work worth doing regardless, and would catch #3, #5, and #7 as a class rather than as three patches.

---

## One more, from the upgrade itself — not a reviewer finding

`MIGRATIONS.md`'s 0.11.0 `Open questions` entry, **applied literally, deletes a sentence the template keeps.**

The entry says to replace the `Open questions` paragraph with "the two-paragraph version below." In a 0.10.0-era `state.md`, that paragraph's final sentence is `Already-answered review threads are NOT tracked here…`. The replacement text does not carry it. `state.md.template` still has it — as a third paragraph, reworded: `a thread the pack has replied in is handled` → `a reply carrying the pack's marker means handled`, tracking the `in_reply_to_id` fix in the same ADR.

Applied the template's actual delta rather than the entry's literal text, so the vendored copy is correct.

**This is finding #1's class from #139, not finding #1 itself.** The snapshot test guarantees a template diff is *looked at*; nothing guarantees every hunk in that diff reaches a migration entry. The failure mode is asymmetric and worth designing against: an entry that says **too little silently deletes**, because "replace paragraph X" is destructive when the reader's paragraph X grew a sentence the replacement omits. An entry that says too much is merely redundant.

**Candidate fix:** express entries as anchored replacements of *specific sentences* rather than whole paragraphs, or have each entry name the template hunk it corresponds to — which would let the snapshot diff and the migration list be cross-checked mechanically instead of by recollection.
