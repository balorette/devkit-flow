# Slice 11 — Validation Report

**Slice:** 11 (step invariants — `adr-registry.md` extraction, `/feature-start` discovery ordering, `Gated baseline` self-invalidation fix, `/plan` findings-ledger commit, `/pr-review` push-before-reply and own-reply filtering under `all`)
**Design:** [`0008-step-invariants.md`](../design/0008-step-invariants.md) (clause references below map to that ADR's three numbered clauses)
**Plan:** [`slice-11-step-invariants.md`](../plans/slice-11-step-invariants.md)
**Evidence:** [`pr139-pack-findings.md`](pr139-pack-findings.md) — 8 findings
**Status:** **authoring complete; dogfood pending.** Mechanical checks pass. No pack command has been executed.
**Date:** 2026-08-10 (authoring)

## Executive summary

Slice 11 is authored and mechanically green (see below) but has not survived contact with reality. The five behavioral predictions below were written **before** running any pack command against them, which is the load-bearing half of the discipline: a prediction written after seeing the result bends to fit it. Per `CLAUDE.md` working principle 4, on divergence the pack content is what gets revised — never the prediction.

**No pack command has been executed.** Findings 4, 5, and 7 (the defects this slice fixes) were found by reading the shipped files and fixed by reading them again — not by running `/feature-merge`, `/feature-start`, `/plan`, or `/pr-review` against a real target. That remains true after this document is written; nothing below changes it.

## What was mechanically verified

| Check | Result |
|---|---|
| Full unit suite | 39 tests, all passing, no failures, no skips |
| `test_every_template_matches_its_snapshot` | Passes — `VERSION` is `0.11.0`, `pack/templates/history/0.11.0/` exists, and the release task re-snapshotted it against the live templates, including `state.md.template`. Mid-slice this test failed by design (an earlier task had edited the template ahead of the re-snapshot); the release task landed the snapshot and closed that gap. |
| `test_changed_template_has_a_migration_section` | Now runs for real, rather than skipping — 0.11.0 gives it a genuine 0.10.0 baseline to diff against and confirm `pack/MIGRATIONS.md` covers the change. It was skipped for the whole slice before the release task landed, because 0.10.0 was the newest snapshot and had no prior baseline to diff. |

Verbatim tail of the run (`python3 -m unittest discover -s tests -v`):

```
test_migrations_has_section_matches_a_real_heading (test_migrations_snapshot.TestVersionHelpers.test_migrations_has_section_matches_a_real_heading) ... ok
test_migrations_has_section_rejects_a_missing_one (test_migrations_snapshot.TestVersionHelpers.test_migrations_has_section_rejects_a_missing_one) ... ok
test_template_names_is_not_empty (test_migrations_snapshot.TestVersionHelpers.test_template_names_is_not_empty)
A bug returning [] would make SNAPSHOT-CURRENT vacuously pass. ... ok
test_version_key_orders_numerically_not_lexically (test_migrations_snapshot.TestVersionHelpers.test_version_key_orders_numerically_not_lexically) ... ok
test_backticked_paths_are_not_double_reported (test_pack_references_resolve.TestClassifier.test_backticked_paths_are_not_double_reported)
A quoted devkit path is reported once by CITATION, not again by the bare scan. ... ok
test_bare_unquoted_devkit_path_is_caught (test_pack_references_resolve.TestClassifier.test_bare_unquoted_devkit_path_is_caught)
`adopt.md:92` cited "docs/design/0002" in prose and evaded a quoted-only scan. ... ok
test_devkit_only_path_is_forbidden (test_pack_references_resolve.TestClassifier.test_devkit_only_path_is_forbidden) ... ok
test_installed_reference_resolves (test_pack_references_resolve.TestClassifier.test_installed_reference_resolves) ... ok
test_installed_set_is_not_empty (test_pack_references_resolve.TestClassifier.test_installed_set_is_not_empty)
A bug that returned {} would make every citation look devkit-only. ... ok
test_runtime_target_paths_are_allowed (test_pack_references_resolve.TestClassifier.test_runtime_target_paths_are_allowed) ... ok
test_trailing_punctuation_is_stripped (test_pack_references_resolve.TestClassifier.test_trailing_punctuation_is_stripped) ... ok
test_no_installed_file_cites_a_devkit_only_path (test_pack_references_resolve.TestNoDanglingReferences.test_no_installed_file_cites_a_devkit_only_path) ... ok

----------------------------------------------------------------------
Ran 39 tests in 0.788s

OK
```

Mid-slice, `test_every_template_matches_its_snapshot` was red by design: an earlier task in this slice had edited `pack/state.md.template` ahead of the release task's re-snapshot, and re-snapshotting early would have hidden the drift the guard exists to catch. The release task has since landed (`VERSION` `0.11.0`, `pack/templates/history/0.11.0/` created), closing that gap.

Mechanical checks confirm the files install, cross-reference correctly, and that the suite is fully green. They say nothing about whether the pack *behaves* as intended in a real session — that is what the predictions below are for.

## Behavioral predictions (pending)

Each was written **before** any pack command in this slice was run. On divergence, revise the pack — not the prediction.

### P1 — a stable, unchanged PR must trigger no gates (clause 2, the one that matters)

**Task:** On Enterprise API, with a PR open and `.claude/state.md` reading `Phase: in-review`, run `/feature-merge` again with nothing changed since the PR opened — no new commits, no force-push, no manual edits.

**Grounded in** `pack/commands/feature-merge.md`'s Preconditions table:

> `in-review`, PR open, **gated content unchanged** | Report review status and open-thread count. Point at `/pr-review`. Run no gates — this content already passed them.

and the discriminator immediately below it:

> **The discriminator is a content diff against `Gated baseline` — never local tip versus remote tip, and never SHA equality.**

**Predicted:** the command reads `Gated baseline` from state.md, reads the PR's `headRefOid` via `gh pr view --json headRefOid`, runs `git diff --quiet <Gated baseline> <PR tip> -- . ':(exclude).claude/state.md'`, finds it quiet, and takes the unchanged-content branch: it reports review status and open-thread count, points at `/pr-review`, and runs **zero** of the three gates. In particular it does **not** invoke the `security-reviewer` subagent — no `Agent`/Task call with `subagent_type: security-reviewer` occurs anywhere in the run. It does not push, does not call `gh pr create`, and does not touch `Gated baseline`.

**Catches:** this branch has been unreachable since `Gated baseline` was introduced (per the design doc's clause-2 framing) — every prior invocation of `/feature-merge` at `Phase: in-review` had *something* differ from the baseline (even if only the transition commit itself, which is exactly what the exclusion of `.claude/state.md` is meant to make safe). If the exclusion doesn't hold in practice, this is the run that would show a full gate re-run — including a live security-reviewer invocation — on a PR that hasn't changed, which is the specific defect the clause exists to close.

**Status:** pending · **Actual:** —

### P2 — a landed code commit re-runs all three gates and updates the baseline (clause 2, negative case)

**Task:** Same starting state as P1 (`Phase: in-review`, PR open, `Gated baseline` set), but before running `/feature-merge`, land one code-touching commit via `/pr-review` (a reviewer finding accepted in-scope, fixed, committed, and pushed per `/pr-review` Phase D).

**Grounded in** the same Preconditions table, the row directly below the one P1 exercises:

> `in-review`, PR open, **gated content changed** | Re-run gates 1–3 — the PR carries changes no gate has seen — then push and update `Gated baseline`. Do **not** re-create the PR.

and the closing instruction under *PR creation (PR flow)*:

> Update `Gated baseline` after **every** successful gate rerun — to the tip as it stands once any fix commits are in and before the `state.md`-only transition commit.

**Predicted:** the content diff against `Gated baseline` is non-quiet (the fix commit's content is real, not excluded), so the command takes the changed-content branch: Gate 1 (tests), Gate 2 (docs reconciliation), and Gate 3 (security-reviewer, fresh context) all run in full — the same sequence as a first-time `/feature-merge` call. It does **not** call `gh pr create` again (the PR already exists). After the gates pass, it pushes and writes a new `Gated baseline` equal to the tip *before* the `state.md`-only transition commit that records it — not the SHA that was checked out when the gates started, and not the transition commit's own SHA.

**Catches:** the negative case of P1 — confirms the discriminator doesn't over-fire toward "unchanged" and silently skip gates on code that actually reached the PR. Also confirms `Gated baseline` moves forward rather than staying pinned to the original PR-creation commit, which would make every subsequent run see "changed" forever and re-run gates on content already gated once.

**Status:** pending · **Actual:** —

### P3 — ADR discovery precedes the brainstorm, allocation re-scans, no `docs/adr/` is invented (clause 3)

**Task:** Run `/feature-start` on Enterprise API, where twelve ADRs live as headings in a single decisions log (not a `docs/adr/` directory of files).

**Grounded in** `pack/commands/feature-start.md` Phase A:

> 1. **Run ADR-registry discovery now.** Follow `.claude/references/adr-registry.md` § *Discover* in full, and record for the rest of this invocation: the registry's location, its format, and its current high-water number. Report what was found per that reference's *Report what was found* step.
> Discovery runs here rather than at Phase E because **Phase B may invoke the `architect`**.

and Phase E:

> 1. **Re-scan before allocating.** Phase A recorded the registry's location, format, and high-water mark. Re-run `.claude/references/adr-registry.md` § *Discover* against that location now, and allocate from what it returns — **never from the number Phase A recorded**.
> ...
> 4. **Write in that registry's format**, not the pack's. ... Create `docs/adr/` only when discovery found nothing anywhere.

and `pack/references/adr-registry.md` § *Report what was found*:

> Location, format (directory-of-files vs single-file log), highest number, and whether it came from definitions or mentions. **A bare number is not something the user can check.**

and § *Allocate* step 2 (floor + 1) plus "Invoking the architect" in `feature-start.md`:

> relevant ADR files from the registry Phase A discovered — actual paths, never a pattern

**Predicted:** before any brainstorm dialogue begins, the command reports the registry as the single decisions log (its path), the format (single-file log, not directory-of-files), and the current high-water mark (`012`), sourced from heading definitions rather than mentions. If Phase B invokes the `architect` subagent, the invocation's paths include the actual decisions-log path (not a `docs/adr/NNNN-*.md` glob). At Phase E, discovery is re-run against that same location before allocating; the number written is `013` (floor 12 + 1), taken from the re-scan's result rather than the number reported at Phase A (even if nothing changed between the two, the source of the number is the re-scan, not the cached value — this matters for the negative case where a second feature's `/feature-start` runs concurrently or a second brainstorm allocates first). No `docs/adr/` directory is created; the new entry is written as a new heading in the existing decisions log, in that log's own format.

**Catches:** the brownfield failure mode the slice-9 dogfood surfaced — an architect handed a default `docs/adr/` path or pattern on a project whose registry lives elsewhere forms a recommendation having read none of the twelve existing decisions, and correct allocation at Phase E afterward doesn't un-form it. Also catches silent duplicate-ID allocation if Phase E ever allocates from a Phase-A-cached number instead of re-scanning.

**Status:** pending · **Actual:** —

### P4 — `/plan`'s Phase G commit stages the discovered findings-ledger path (clause 1)

**Task:** Run `/plan` on a feature whose Phase F2 conformance review (via the `conformance-reviewer` subagent) leaves at least one **advisory** finding outstanding — the spec is silent, the plan chose, and the user leaves it as-is rather than resolving it before approval.

**Grounded in** `pack/commands/plan.md` Phase F2:

> **Record every advisory the user leaves outstanding as a `CONF` row in the findings ledger** (see the documenter skill's *The findings ledger*; its location is discovered, not assumed).

and Phase G:

> Before the pause, propose a single commit for the artifacts this invocation produced: the plan, any Phase-C ADRs, the Phase-F `.claude/state.md` updates, **and the findings ledger if Phase F2 recorded a `CONF` row** (its path is the discovered one, not assumed).
> A `CONF` row that is written and not committed reaches no other clone and no PR — defeating the stated purpose of surfacing to the next `/feature-start`'s orient phase, which reads the ledger from the repo rather than from this conversation.

**Predicted:** the Phase G commit proposal lists the findings-ledger file among the staged paths (alongside `docs/plans/<slug>.md` and `.claude/state.md`), using whatever path the ledger was actually discovered/created at for this project — not a hardcoded `docs/findings.md` or similar assumed path. After the user confirms and the commit lands, `git show --stat <sha>` on the resulting commit lists that ledger path in its changed-files output, confirming the `CONF` row is not left uncommitted the way slice-9's Finding 4 pattern (a durable artifact written but not staged) would produce one layer down.

**Catches:** the class of defect this slice's clause 1 exists to close — a ledger row written to disk during the command but never staged, so it's invisible to the next clone, the next `/feature-start`, and (in PR flow) the PR itself. The prediction is deliberately checking the *commit contents*, not just that a file exists on disk afterward, because an uncommitted file passes a weaker check.

**Status:** pending · **Actual:** —

### P5 — `/pr-review all` re-triages the reviewer's items but not the pack's own replies (finding 7)

**Task:** With at least one pack-authored reply already posted to the PR (carrying a `<!-- devkit:pr-review handled:<id> -->` marker), run `/pr-review all`.

**Grounded in** `pack/commands/pr-review.md` Arguments:

> **`/pr-review all`** — re-triage every thread, including previously-answered ones. ... The pack's own replies stay excluded; `all` re-opens the reviewer's items, not the answers to them.

and Phase A:

> Skip an item if **either** is true:
> 1. **A marker names its id.** ...
> 2. **The item itself contains a marker.** It is one of the pack's own replies.
> ... **`/pr-review all` disables condition 1 only.** Condition 2 always applies: an item carrying a devkit marker is the pack's own reply and is never a review item, in any mode. Disabling the whole skip would re-fetch those replies and offer to answer them — the exact recursion the paragraph above prevents, reintroduced by the flag meant to re-triage the reviewer's comments.
> Search all three surfaces for markers, build the handled set, then skip. **Report the skipped count**

**Predicted:** in the Phase C proposal table, the reviewer's original comment(s) that were previously answered **reappear** as rows to be (re-)triaged — condition 1 is disabled under `all`, so a marker naming that comment's id no longer causes a skip. The pack's own prior reply (the comment carrying the marker itself) does **not** appear as a row — condition 2 still applies regardless of the `all` flag. The hand-off report's skipped count names the excluded pack replies specifically (not a bare number with no referent), and that count is strictly less than it would be under plain `/pr-review` (which would also skip the marker-matched originals).

**Catches:** the self-recursion defect finding 7 fixes — `all` disabling both conditions would re-offer the pack's own replies as new review items to respond to, growing the thread by one pack-authored comment every pass. The prediction is specifically checking that `all` is asymmetric (reopens originals, never reopens the pack's own answers), not merely that *some* skipping still happens.

**Status:** pending · **Actual:** —

## Deferred findings

Four findings surfaced during this slice's task-level reviews. Each was evaluated, judged real, and deliberately left unresolved rather than fixed in-slice — the final whole-branch review triaged all four as ship-as-is. These are recorded decisions, not oversights or open bugs; losing them at cleanup would be the exact failure `pack/references/findings-triage.md` exists to prevent, one layer down.

1. **`pack/skills/pm/SKILL.md:344`** — duplicated prose. The sentence "Plan-time allocation re-scans exactly as brainstorm-time does — `/feature-start` may already have consumed the number you last saw" restates the `/feature-start`-then-`/plan` ADR-number collision hazard that `pack/references/adr-registry.md` § *Never cache the number* already owns (that section names the identical collision in its own words: "`/plan` allocating from a mark `/feature-start` already consumed is the same collision one command over"). Mild tension with clause 3's corollary — cite, don't restate. **Deferred because** it's defensible as a one-sentence hazard pointer at the call site; the defect is that it's restated prose rather than a citation, so it can drift out of sync with the reference it duplicates. **Resolution:** replace the sentence with a citation to the reference's *Never cache the number* section.

2. **`pack/agents/architect.md`** — an enforcement asymmetry between two of its rules. *"Never write an ADR file yourself"* (line 79) is backstopped by the absence of `Write`/`Edit` from the front-matter `tools:` line (line 4: `tools: Read, Glob, Grep`) — structurally impossible to violate. *"Do not go looking for the registry yourself"* (line 20) has no such backstop: `Read`, `Glob`, and `Grep` are exactly the tools needed to disobey it. Coherent as guidance, not enforced as constraint. **Deferred because** the question it raises — when must a pack rule be tool-enforced rather than instructed? — is bigger than this slice; answering it for one rule without a general policy would be ad hoc. **Resolution:** a follow-up ADR on tool-enforcement policy for subagent instructions, or an explicit acceptance that this rule stays instruction-only.

3. **`pack/devkit-orientation.md`'s commit-cadence table** — missing row. The table (§ *Commit cadence*) has no row for `/feature-merge`'s post-merge "clear `state.md` to idle" commit (`pack/commands/feature-merge.md` § *After the merge*, step 1: "Clear state.md ... commit it"). `feature-merge.md` does specify that this transition is written and committed, but — unlike the closeout-docs commit (`/feature-merge: summary + state.md`) or the PR-opened transition (`/feature-merge: in-review (PR #<n>)`) — never gives it a subject line. Writing a table row here would have meant inventing a subject line `feature-merge.md` itself doesn't state. **Deferred because** the real fix is upstream: name the subject in `feature-merge.md` first, and the table row follows directly. **Resolution:** add a named subject (e.g., `/feature-merge: idle (merged)`) to `feature-merge.md` § *After the merge*, then add the corresponding commit-cadence row.

4. **`.claude/.devkit-manifest.json` and `.claude/.devkit-version`** — ownership gap. Neither file is manifest-tracked content (the manifest itself lists skills/agents/commands/hooks/references plus `devkit-orientation.md` and `MIGRATIONS.md` — see `devkit-orientation.md` § *Which `.claude/` files the pack owns*) nor genuinely user-owned (both are rewritten by the installer on every run — see `install.sh` lines 151–152 and its manifest-write logic). That section's "Anything else under `.claude/` is yours" sweeps these two into the user-owned bucket by implication, which is wrong for them specifically. Pre-existing gap, relocated rather than worsened by this slice's rewrite of that section. **Resolution:** carve out an explicit third category in that section — installer-owned bookkeeping, rewritten every run, not yours to edit — covering the manifest and version-stamp files.

## Outstanding

- Every behavioral prediction (P1, P2, P3, P4, P5).
- The full end-to-end dogfood on Enterprise API: a PR sitting at `Phase: in-review` with an established `Gated baseline`, at least one reviewer comment already answered by the pack, and a second `/feature-start` run against its twelve-ADR decisions log — none of which currently exist as live state on that target.
- Whether the `Gated baseline` exclusion of `.claude/state.md` (P1/P2) survives a real diff where the transition commit also happens to touch an unrelated tracked file in the same commit (outside this slice's scope to construct, but worth a note if the dogfood surfaces it).
- Re-snapshotting `pack/templates/history/` for `state.md.template` is explicitly **not** this task's job — that is Task 14 (release). The current red `test_every_template_matches_its_snapshot` result is expected and should stay red until Task 14 runs.
