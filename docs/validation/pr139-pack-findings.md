# Pack Findings — Enterprise API 0.10.0 Upgrade + `/adopt` Run

**Source:** [example-corp/enterprise-api#139](https://github.com/example-corp/enterprise-api/pull/139) — automated review (Codex, Cursor Bugbot) of the 0.10.0 upgrade and the first real `/adopt` run
**Pack version reviewed:** 0.10.0
**Status:** 8 pack findings, all verified against `pack/` source before filing. 1 already fixed upstream.
**Date:** 2026-08-10

---

## What this is

The Enterprise API install of 0.10.0 drew ten review findings. **Four were the host project's own content** and are fixed there. The remaining **eight are pack-authored files**, verified here against `pack/` rather than the vendored copy.

Two notes on provenance:

- **This round is stronger evidence than the first.** The 0.9.0 report was static review of freshly-vendored files. This round reviews 0.10.0 *after* it fixed the first round's brownfield findings, and the reviewers had `/adopt`'s real output to check the pack's instructions against.
- **Still not a dogfood.** No pack command has executed. Findings 4, 5, and 7 in particular are reasoning about control flow that has never run; they look sound on the page, but a behavioral run is what would settle them.

One correction to the summary given on the PR: it listed **six** pack findings. There are **eight** — the ownership over-claim (#6) and the `all`-mode filter (#7) were omitted from that list.

---

## The theme worth naming first

Four of the eight — #2, #3, #4, #5 — are the same shape: **a step's outputs are not carried into the step that transports them.**

- `/plan` Phase F2 writes a `CONF` row; Phase G's staging list omits the ledger.
- `/pr-review` step 3 writes a `REV` row; step 4 pushes without committing it.
- `/feature-merge` writes `Gated baseline`, then commits it — invalidating the thing it just wrote.
- `pm` reads the ADR registry from `CLAUDE.md` but writes back to a hardcoded `docs/adr/`.

Each was introduced by a *correct* local fix. The findings ledger was added so findings outlive their feature; `Gated baseline` was added so ungated commits cannot skip gates; the commit-the-transition step was added so async resume works. Every one of them creates an artifact and stops short of the plumbing that moves it.

**A candidate rule for the pack: any step that writes a durable artifact must name the commit that carries it, in the same step.** Three of these four disappear under that rule.

---

## Finding 1 — `MIGRATIONS.md` 0.10.0 is incomplete (root cause of the reported `state.md` contradiction)

**Severity: high.** Silently ships a contradicting seeded file to every upgrader.

Cursor reported that the installed `.claude/state.md`'s HTML comment says `/pr-review` parks accepted-but-unfixed findings in `## Open questions`, contradicting `pr-review.md:79`, which routes cross-feature deferrals to the findings ledger as `REV` rows.

**The pack template is already correct.** `pack/state.md.template:49-54` reads:

> During Phase: in-review it holds review findings accepted for THIS feature and not yet fixed. It is cleared at /feature-merge, so anything deferred PAST this feature must go to the findings ledger instead — /pr-review routes cross-feature deferrals there as REV rows.

So the finding is against the *installed* file, not the pack. But that is exactly the problem: **`state.md` is a seeded file the installer never rewrites**, and `MIGRATIONS.md`'s 0.10.0 section lists only the `Gated baseline` field addition. It says nothing about the Open-questions prose change.

Verified: `sed -n '/## 0.10.0/,/## 0.9.0/p' pack/MIGRATIONS.md | grep -c "Open questions"` → `0`.

An upgrader who follows `MIGRATIONS.md` exactly — as Enterprise API did — ends up with a `state.md` whose own documentation contradicts the command that writes to it.

**Fix:** add the Open-questions prose change to the 0.10.0 migration entry. **And the process fix that matters more:** whatever produces a `MIGRATIONS.md` entry should be driven by a diff of `state.md.template` between versions, not by recollection of what changed. A template diff would have caught this mechanically.

---

## Finding 2 — `pm` skill writes ADRs to a hardcoded path

**Severity: high.** Reintroduces the duplicate-ADR hazard 0.10.0 just fixed elsewhere.

0.10.0 correctly fixed the **read** path — `pack/skills/pm/SKILL.md:46`: *"Their location is recorded in `CLAUDE.md` conventions by `/adopt`; `docs/adr/` is the default, not the assumption."*

The **write** path was not updated:

| Line | Text |
|---|---|
| `:207` | *"write it to `docs/adr/NNNN-<short-name>.md` with the next free number"* |
| `:214` | *"Any ADRs drafted during brainstorm are written under `docs/adr/`."* |
| `:344` | *"Any ADRs drafted during plan-time architect calls are written under `docs/adr/`."* |

On Enterprise API this means the skill reads twelve ADRs from `docs/ai/decisions.md`, then writes ADR-013 into a `docs/adr/` directory that does not exist — producing precisely the split registry `/feature-start`'s discovery was added to prevent. `/feature-start:80` handles this correctly; `pm` bypasses it.

**Fix:** route all three write sites through the same discovery `/feature-start` uses, or have `pm` delegate ADR writing to it rather than duplicating the path.

---

## Finding 3 — `/feature-start` invokes the architect before registry discovery

**Severity: high.** The architect starts blind on exactly the projects discovery was built for.

Ordering in `pack/commands/feature-start.md`:

- **Phase B** (`:41-47`) — brainstorm; invokes the `architect` when an architectural question surfaces.
- **Phase E** (`:71-86`) — discovers the ADR registry and allocates.

The invocation contract at `:130` passes *"relevant `docs/adr/NNNN-*.md` files"* — a hardcoded path, resolved two phases before discovery runs.

On Enterprise API, `docs/adr/` does not exist. The architect therefore receives **no ADRs at all**, having twelve in `docs/ai/decisions.md`, and may recommend or draft something that contradicts one. Phase E's allocation is correct by then, but the *recommendation* was already formed blind.

This is the same class as the type-gate defect found in the host project's own conventions: **discovery that runs after the consumer that needs it.** Being right eventually does not help a consumer that already ran.

**Fix:** hoist registry discovery to Phase A (orient), record it once, and pass the discovered paths in the architect contract at `:130`.

---

## Finding 4 — `Gated baseline` invalidates itself on write

**Severity: high.** Defeats the optimization it was added for; every open-PR invocation re-runs everything.

`pack/commands/feature-merge.md` establishes the discriminator at `:23-24`:

| Condition | Behavior |
|---|---|
| PR tip **==** `Gated baseline` | Run no gates — this commit already passed |
| PR tip **!=** `Gated baseline` | Re-run gates 1–3 |

Then `:162-164`:

> On confirmation: push, create the PR, then set `.claude/state.md` to … **`Gated baseline: <the SHA that just passed gates 1–3>`** … **Then commit and push that transition.** Subject: `/feature-merge: in-review (PR #<n>)`, staging `.claude/state.md` only.

Setting the baseline to SHA *X*, then committing that value, produces tip *Y ≠ X*. **The equality branch is unreachable from the moment the PR opens**, and the same self-reference recurs at `:168` on every rerun ("Update `Gated baseline` again after every successful gate rerun") — updating it commits it, producing a new tip.

Consequence: every `/feature-merge` invocation on an open PR re-runs tests, docs reconciliation, and a fresh-context security review, including when nothing changed.

The step that causes it is well-justified — `:164` explains that leaving `state.md` dirty breaks async resume and can open a duplicate PR. Both concerns are real; the interaction is what was missed.

**Fix options:** compare against the tip *excluding* commits that touch only `.claude/state.md`; or record the baseline as "tip at gate time" and compare `git rev-list <baseline>..<tip> -- . ':!.claude/state.md'` being empty; or keep the baseline out of the committed file. The third is cleanest but conflicts with the async-resume requirement that put it there.

---

## Finding 5 — `/pr-review` pushes before committing the findings ledger

**Severity: medium.**

`pack/commands/pr-review.md` Phase D:

- **Step 1** — code fixes, *"each … its own commit."*
- **Step 3** — writes the findings ledger (`REV` rows) and `.claude/state.md`. **No commit named.**
- **Step 4** — *"Push — and verify the remote tip actually contains the fix commits."*

Only step 1 commits. The ledger and state edits from step 3 are uncommitted when step 4 pushes, so the remote PR lacks the durable `REV` record, and the tree stays dirty for the next `/feature-merge` — whose own preconditions forbid checking out mainline over a dirty tracked `state.md` (`feature-merge.md:164`).

Worth noting for its own sake: this command reasons carefully and at length about push-before-reply ordering and about verifying the remote tip with `git ls-remote` rather than the API. It gets the hard part right and omits the commit.

**Fix:** add an explicit metadata commit between steps 3 and 4, staging the discovered ledger path and `.claude/state.md`.

---

## Finding 6 — `/plan` Phase G staging list omits the findings ledger

**Severity: medium.** Reported independently by both reviewers.

Phase F2 records outstanding conformance advisories as `CONF` rows. Phase G (`pack/commands/plan.md:129`) proposes a commit staging *"the plan, any Phase-C ADRs, the Phase-F `.claude/state.md` updates, and any spec front-matter `related_adrs` amendment"* — not the ledger.

The row therefore never reaches other clones or the PR, defeating its stated purpose of surfacing to the next `/feature-start`'s orient phase.

**Fix:** add the discovered ledger path to Phase G's staging list whenever F2 wrote to it.

---

## Finding 7 — `/pr-review all` disables the pack's own-reply filter

**Severity: medium.** Reintroduces a recursion the same section explains at length.

`pack/commands/pr-review.md:44-49` builds the skip set from **two** conditions: the original was already handled, **and** the item is not itself a pack-authored reply. The prose is explicit about why the second matters:

> Condition 1 alone would therefore skip the original and treat the pack's own answer as a new item to respond to — proposing replies to its own replies, growing by one every pass.

Then `:49`: **"`/pr-review all` disables the skip."**

Disabling the whole skip disables condition 2 as well. In `all` mode the pack fetches its own marker-bearing replies and offers to answer them — the exact growth the paragraph above prevents.

**Fix:** in `all` mode disable only the handled-original check; always exclude items carrying a devkit marker.

---

## Finding 8 — `.claude/` ownership is over-claimed

**Severity: medium.** Misclassifies host-owned files, and this section was added by the previous round's fix.

`pack/devkit-orientation.md:80-83`:

> ## `.claude/` is pack-owned
> Everything under `.claude/` is vendored from the devkit pack and versioned by it, not by this repository's conventions.

Measured against the Enterprise API install:

```
pack-tracked (in .devkit-manifest.json): 25
NOT pack-tracked:                        45
```

The 45 include the project's own `agents/` (14 pre-existing subagents such as `fastapi-engineer`, `qa-test-director`, `safety-compliance-officer`) and roughly 20 pre-existing commands, plus `settings.json`, which the installer *merges into* rather than owns.

Telling users not to edit `.claude/` misclassifies all of it, and on a project that had `.claude/` before devkit — the brownfield case — the majority of the directory is not the pack's.

There is a wrinkle worth flagging: **this section was written in response to the previous round's disputed bare-`print` finding**, and it cites that exact example. The fix for over-applying host rules to pack files over-corrected into claiming host files for the pack.

**Fix:** scope the claim to the manifest's tracked set plus the seeded exceptions (`state.md`, `CLAUDE.md`), and say plainly that anything else under `.claude/` belongs to the project. The manifest already exists to answer this precisely.

---

## Suggested order

1. **#1 (MIGRATIONS completeness)** — every upgrade ships the defect until fixed, and the template-diff process fix prevents recurrence.
2. **#2 and #3 (ADR write path, architect ordering)** — together they undo 0.10.0's brownfield work in the two places it did not reach.
3. **#4 (Gated baseline)** — the slice-8 feature most likely to be noticed first in real use, since it makes every merge invocation expensive.
4. **#5, #6, #7** — mechanical, and #5/#6 fall out of the "name the commit that carries it" rule.
5. **#8** — documentation-only, but it is what tells a user which files they may touch.

## Still not validated

`docs/validation/slice-8.md` remains *"authoring complete; dogfood pending."* Findings 4, 5, and 7 are all slice-8 control flow, found by reading rather than running. Fixing them first makes the eventual dogfood a test of the design instead of a rediscovery of these — Enterprise API remains the right target, with two automated reviewers and a PR lifecycle now exercised six times.
