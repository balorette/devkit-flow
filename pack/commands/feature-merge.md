---
description: Close out a feature: run three gates (tests pass → docs reconciled → security review clean) and then either propose a local merge or open a pull request, depending on the project's flow. Re-runnable — in PR flow it transitions to `Phase: in-review`, re-validates the gates when review fixes land, and performs closeout once the PR merges (possibly asynchronously, by someone else). Loads the `engineer` skill (Gate 1), the `documenter` skill (Gate 2 + summary authoring), and the `security-reviewer` subagent in fresh context (Gate 3). Halts on any gate failure; pauses for user confirmation before executing any git or `gh` operation.
---

Drive the three closeout gates and the integration sequence for the active feature.

In **local-merge flow**, one invocation completes the feature lifecycle (or halts at a gate and surfaces what blocked). In **PR flow** it takes at least two: the first runs the gates and opens the PR, moving the feature to `Phase: in-review`; a later one performs closeout once the PR has merged. `/pr-review` handles everything in between.

`/feature-merge` is the **gating** command, not the merge-script command. Even on the happy path, it proposes the git and `gh` operations and waits for user confirmation before executing — merging and opening a PR are both consequential enough that explicit confirmation is the right friction.

## Arguments

`/feature-merge` takes no arguments. It operates on the active feature in `.claude/state.md`. To merge a parked feature, the user resumes it first (`/checkpoint` to update state, then `/feature-merge`).

## Preconditions

`/feature-merge` is **re-runnable**. Read `.claude/state.md` first and branch on `Phase`:

| Entry state | Behavior |
|---|---|
| `building` / `merging`, local-merge flow | The original path: gates 1–3 → summary → merge proposal → user merges → clear state. |
| `building` / `merging`, PR flow | Gates 1–3 → summary → push → `gh pr create` → set `Phase: in-review` and `PR:`. **Do not clear state.** |
| `in-review`, PR open, **gated content unchanged** | Report review status and open-thread count. Point at `/pr-review`. Run no gates — this content already passed them. |
| `in-review`, PR open, **gated content changed** | Re-run gates 1–3 — the PR carries changes no gate has seen. **Commit whatever the gates wrote first** (Gate 2's reconciliation, Gate 3's `SEC` rows — see each gate's `**Writes:**`), *then* update `Gated baseline` and commit `.claude/state.md` alone, and push. Two commits, in that order — see *Why two commits* below. Do **not** re-create the PR. |
| `in-review`, PR merged | Closeout only (see *After the merge*). **Skip the gates**; the merge already happened. |

**Check merged state first, before any other precondition — and check it against the PR this feature recorded.** Read `.claude/state.md`'s `PR:` field, then `gh pr view <that PR> --json state,mergedAt`. With no argument, `gh pr view` reports *"the pull request that belongs to the current branch"*, which is a different question: on a head-deleting forge the closeout commonly runs from mainline, where no PR belongs to the branch at all, and from an unrelated branch it returns that branch's PR and decides this feature's path from it. The field holding the correct answer already exists — read it before using it, rather than reconstructing it from whatever is checked out. If `PR:` is unset, fall back to branch inference and say so. If the PR has merged, skip to closeout (*After the merge*) — the *remote-agreement* preconditions below apply only while the PR is still **open**, and applying them to a merged PR breaks the closeout path outright.

**One precondition still applies on the merged path: the tracked worktree must be clean.** Closeout runs `git checkout <mainline>` as its first act, and a dirty tracked tree either aborts that checkout on an overlap or carries unrelated modifications onto mainline. Neither is a state transition anyone can complete safely. Check `git diff --quiet && git diff --cached --quiet` before the checkout; if it fails, halt and report what is uncommitted rather than proceeding. Untracked files are surfaced and asked about, as everywhere else.

What does **not** apply on this path is the remote comparison — the head ref may be gone, which is exactly why the merged check has to come first.

The failure is specific enough to be worth naming. Forges that delete the head branch on merge leave `git ls-remote origin <branch>` returning no OID, and `git ls-remote -h` does not error on no-match unless `--exit-code` is passed. So precondition 2 sees an empty result rather than a failure, reads the local checkout as diverged or unpushed, and **halts before the closeout that would have cleared state** — on a PR whose only remaining work is that closeout. The halt list further down does mention a merged-state check; nothing ordered it ahead of precondition 2.

With the PR confirmed open, the `in-review` rows have their own preconditions, checked **before** the discriminator runs:

1. `PR:` is set in state.md, or a PR is discoverable for the current branch.
   The merged-state check above reads this same field earlier and does not depend on this list — that check runs before the PR is known to be open, which is exactly when the current branch is least likely to be the feature's.
2. **Local and remote agree.** No uncommitted changes to tracked files, and local `HEAD` **equals** the OID `git ls-remote origin <branch>` reports — not merely "is not ahead of" it. Use `git ls-remote`, **not** `gh pr view --json headRefOid`: the API can serve a stale `headRefOid` for a moment after a push (see `/pr-review`'s push-verification step for the same distinction), which risks a false negative on a genuinely diverged branch, and `git ls-remote` reads the ref directly.

   **Equality, because a directional check misses the common direction.** When another clone or the web UI pushes to the PR, local is *behind*, and a "not ahead" test passes. `git fetch` then makes the new tip available without moving `HEAD`, so the discriminator reads the PR's new content while gates 1–3 run against stale local content — and the state-only push that follows is a non-fast-forward. The stated rationale for this precondition is exactly that failure in mirror image: the discriminator reasons about the PR's remote content, and that framing is only correct when local and remote already agree. One-directional agreement is not agreement. On a mismatch, halt and report **which direction**; when local is behind, the fix is to update the checkout before re-running.

3. **Untracked files are surfaced here too.** The building-phase path already handles this — *"An untracked file is as likely to be a source file the engineer forgot to `git add` … as it is to be build detritus"* — and the reasoning applies with more force here. A review fix that adds a new source or test file and forgets to stage it leaves local `HEAD` equal to the remote OID, so precondition 2 passes; the gates then run **green against a working tree containing the untracked implementation**, and the state-only commit pushes a `Gated baseline` the PR did not earn. Surface untracked files and ask before running any gate.

If any check fails — uncommitted tracked changes, or local and remote disagreeing in either direction — **halt**. Report what's uncommitted (`git status`) or unpushed (`git log <remote-tracking>..HEAD --oneline`); don't guess which it is, and don't run the discriminator anyway — git can answer which, so ask git (`.claude/references/evidence-and-uncertainty.md` § *The discriminator*, first row). The reason this has to come first: the discriminator below reasons about the PR's **remote** content, and that framing is only correct when local and remote already agree. A review-fix commit made locally and never pushed leaves the remote diff quiet while the code actually about to merge has never passed a gate — gates 1–3 get silently skipped on exactly the commits that most need them.

With that established, fetch the PR tip locally before diffing against it. `gh pr view --json headRefOid` returns an OID from GitHub's record; if the PR was updated from another clone or the web UI since this checkout, that commit may not exist in the local object database, and the diff below fails on an unknown object instead of deciding anything:

```
git fetch origin <branch>
```

**The discriminator is a content diff against `Gated baseline` — never local tip versus remote tip, and never SHA equality.** Read the PR tip with `gh pr view --json headRefOid`, then:

```
git diff --quiet <Gated baseline> <PR tip> -- . ':(exclude).claude/state.md'
```

Quiet (exit 0) → the gated content is unchanged; run no gates. Differs → re-run gates 1–3.

Two things this gets right that the obvious versions do not:

- **Not tip versus tip.** `/pr-review` commits its fixes and pushes them, so after it runs the local and remote tips agree while carrying commits no gate has ever seen. A rerun keyed on that would skip tests, docs reconciliation, and security review on precisely the code about to merge.
- **Not SHA equality against the baseline.** Writing `Gated baseline` requires committing `state.md`, which changes the tip — so tip *never* equals baseline, and an equality check makes the no-gates branch unreachable from the moment the PR opens. The exclusion of `.claude/state.md` is what makes the comparison survive the command's own bookkeeping write. It is a **content** diff rather than a commit walk so that a change reverted within the PR correctly reads as unchanged.

**Why two commits on a gate rerun.** Gate 2 reconciles documentation and Gate 3 can write `SEC` rows to the findings ledger — both leave files modified other than `state.md`, as each gate's `**Writes:**` declares. A single `state.md`-only commit strands them, and does so in two directions at once: the tree stays dirty, so the *next* invocation's own precondition ("no uncommitted changes to tracked files") halts on it — the row breaks the path it returns to — and the pushed `Gated baseline` asserts that content passed the gates while the gates' own output is absent from the branch.

So: commit the gates' artifacts first, then set `Gated baseline` to *that* commit and commit `state.md` alone. The order matters in both directions. Baseline-then-artifacts would name a tip whose content the artifacts postdate; one combined commit would put non-`state.md` content in the transition commit, and the discriminator above excludes only `.claude/state.md`, so the next invocation would read the difference as ungated content and re-run gates that already passed.

This is the same reasoning the closeout commit already applies one section down, where the ledger is staged "if Gate 3 wrote `SEC` rows to it" — an uncommitted ledger row is the durable-memory failure the ledger was added to fix, reproduced one layer down.

Which flow applies is settled by *Flow detection* below (`CLAUDE.md` convention → infer from the repo → ask). The gates are identical in both flows, so that determination can wait until the proposal — but `Phase: in-review` only ever occurs in PR flow, so the last three rows need no detection.

Merged-state detection is `gh pr view --json state,mergedAt`. If `gh` fails or is unauthenticated, **ask the user whether the PR merged** — do not guess, and do not treat a failed call as "not merged."

The numbered preconditions below apply to the two `building` / `merging` rows; the `in-review` rows' preconditions are above.

Read `.claude/state.md`. Verify:

1. `Active feature` is not `none`.
2. `Spec` points to an existing file; spec `status` is `approved` or `approved (amended ...)`.
3. `Plan` points to an existing file; plan `status` is `approved` or `approved (amended ...)`.
4. No uncommitted changes to **tracked** files (`git diff --quiet && git diff --cached --quiet`). Untracked files do not block on their own, but they are not ignored — see the handling below.
5. Current branch matches `Active branch` in state.md.

If any precondition fails, **stop and report**. Common cases:
- Uncommitted changes to tracked files → user commits or stashes; re-run.
- Untracked files present → surface them and ask before proceeding. An untracked file is as likely to be a source file the engineer forgot to `git add` (which won't be in the merge — a real problem) as it is to be build detritus (harmless). Don't silently proceed past untracked files, and don't silently treat them as blocking; let the user commit the forgotten ones and confirm the rest are intended omissions, then re-run.
- Plan still `draft` → user approves the plan (or runs `/plan` if no plan exists).
- Spec still `draft` → user approves the spec; if plan doesn't exist, run `/plan` first.

## Run

### Orient — resolve the summary's home

Run `.claude/references/artifact-locations.md` § *Resolve* in full and record the **summaries** directory for the rest of this invocation. The summary write below is a consumer of that result, and clause 3 puts the producer before every consumer.

This command is the pack's **only** producer of a summary, so outside `/adopt` it is the only place the summaries directory is ever resolved. `/feature-start` and `/plan` resolve the types *they* write and leave this one alone — § *Resolve* runs and exits per artifact type, so the `CLAUDE.md` record they left almost certainly names specs and plans and says nothing about summaries.

**Do not read that record as an answer to this question.** A record naming two types out of three is the ordinary state here, not a sign something went wrong, and summaries is the type most likely to be the missing one. Expect § *Resolve* to reach the scan for it on a project that has never merged a feature through the pack — and on a brownfield target, expect the scan to find something: `docs/summaries/` is an ordinary name, and § *Confirm* is why this step runs ahead of the gates rather than during closeout.

Resolving here rather than beside the write is deliberate: it keeps every location question in front of the gates, so the user is never asked to settle a directory during closeout for a feature that Gate 1 is about to send back.

**Writes:** the `CLAUDE.md` conventions entry recording the artifact locations, for any type § *Resolve* settled here that the record did not already name. Otherwise none.

### The gates

The three gates run in fixed order: tests → docs → security. Each gate's failure surfaces concrete remediation. The gates are independent — a Gate-2 failure doesn't tell you anything about Gate 3 — but they execute sequentially because each is cheap to re-run after a fix and there's no value in showing the user three problems at once.

### Gate 1 — Tests pass

Load the `engineer` skill.

**Run the project's own gate set if it has one.** If `CLAUDE.md` conventions record a **Blocking gates** list (written by `/adopt`), run exactly that, in order. Only when no such list exists do you infer the runner from the plan's "Approach" section or from project config (`pyproject.toml`, `package.json`, `Cargo.toml`) — and when you infer, **say that you are inferring**.

The distinction is not cosmetic. Any project with a CI config has already defined what "tests pass" means, and that definition routinely includes gates a plain test run cannot see — coverage deltas, diff-coverage thresholds, migration checks, lint profiles that differ from the local one. The first brownfield target had four blocking gates where the pack checked three; the fourth was a coverage-delta check. Gate 1 would have passed and opened a PR that CI failed on the first push, which is worse than no gate: it spends a reviewer's attention to discover something the pack could have.

**When a recorded gate list exists, it is the whole of Gate 1.** Run exactly those commands and nothing extra — the list already contains whatever lint and type-checking the project blocks on, and adding your own risks running a *different* lint profile than CI does, or running the same step twice.

**When inferring** (no recorded list), run the full suite — not just the feature's tests, since regressions matter at merge time — plus the linter and type-checker if the project has them configured.

- **Green:** proceed to Gate 2.
- **Red:** halt. Surface what failed and a one-line "fix or amend the plan via `/checkpoint`" prompt. Do not proceed to other gates — a red result invalidates downstream assumptions. Lint and type-check failures block at the same severity as failing tests.

**Writes:** none — runs the project's recorded gates and reports.

### Gate 2 — Docs reconciliation

Load the `documenter` skill. Run a final-pass version of Pattern D (see the documenter skill's "Pattern D — On-demand reconciliation") **plus** an additional acceptance-criteria-coverage check:

- **Pattern D checks:** `owned_files` coherence (any commits touching files outside scope?); state.md coherence (Spec/Plan paths exist; Phase makes sense for a feature about to merge); spec/plan front-matter coherence.
- **Acceptance-criteria coverage:** read the spec's "Acceptance criteria" section. For each criterion, identify which plan step (or completed work) satisfies it. Any criterion not mapped to completed work is a coverage gap. The plan's "Acceptance mapping" table (per the pm skill's plan-time guidance) is the primary source; the documenter cross-references against the plan's Completed steps in state.md.
- **Acceptance-criteria conformance:** for each criterion, does any completed work *contradict* it? Ask this separately and explicitly — coverage and conformance are different questions, and the coverage check is structurally blind to the difference. A step can satisfy the mapping while violating the criterion it maps to: a schema field that reopens a path the spec says must be blocked is *covered* and *wrong*. `/plan`'s `conformance-reviewer` catches this class before the build; this is the same question asked of the code that actually got written, which may have drifted from the plan.

If all checks pass: proceed to Gate 3.

If anything is unaddressed:
- **Drift surfaced:** documenter proposes resolution per Pattern A. User confirms; documenter applies; re-run Gate 2 from the top.
- **Coverage gap:** the spec promised behavior the plan/code didn't deliver. Two resolution paths:
  - **Scope-cut amendment:** trim the spec's acceptance criteria via `/checkpoint`. Honest "we shipped less than originally scoped" — explicit in the amendment note. The cut criteria become followups in the summary.
  - **Build the missing work:** continue `/build` for the remaining plan steps; come back to `/feature-merge` when complete.

The user picks. Don't proceed past Gate 2 with a coverage gap silently.

**Writes:** whatever the reconciliation amends — the summary, domain docs, and any spec or plan amendment.

### Gate 3 — Security review

Invoke the `security-reviewer` subagent in fresh context. Pass:
- The diff command (`git diff <mainline>...HEAD` — **three dots**) for the subagent to run itself. The three-dot form diffs against the merge base, which is what "what this feature changed" means. With two dots, every commit that landed on mainline after this branch diverged renders as a *removal* in the feature's diff — so the `security-reviewer` can report, or block on, changes this feature never made. The longer the branch lives, the worse it gets.
- Path to the active spec.
- Paths to related ADRs from the spec/plan front-matter.
- Path to the active plan (intent context only; not authoritative for security).
- **When this run follows a fix made on Gate 3's own recommendation:** the prior finding, verbatim, and the commit or hunk that answers it. Say plainly that the reviewer is **grading its own prior recommendation**, and that the question is whether the mitigation achieves the property the finding named — not whether the code matches what was recommended. This input is what fresh context cannot supply: the reviewer has no way to know a hunk exists *because* Gate 3 asked for it, and will otherwise read the recommended pattern in the diff as evidence that the risk is handled.

The subagent returns a structured findings document with severity-bucketed entries (critical / high / medium / low / informational).

- **Zero critical findings:** Gate 3 passes *as of the diff it just read*. Surface the full findings document to the user — they need to know the medium/low/informational items even though they don't block. **Record each of them as a `SEC` row in the findings ledger** (see the documenter skill's *The findings ledger* — its location is discovered, not assumed). The summary keeps its *Security review notes* section and cross-references the row IDs rather than restating them. Without the ledger these findings ship and are never seen again; the summary is a document nobody reopens.

  **If the user chooses to fix any of them, the gate is no longer passed.** A fix produces code Gate 3 has never read, on the hunk the review just identified as the most security-relevant in the diff. Re-run from Gate 1 — fixes touch code, so tests and docs are in scope too — and re-run Gate 3 with the *grading* brief above. This holds at every severity: the severity threshold decides whether the merge **blocks**, and it has never been the right input to whether something has been **reviewed**. The gate that recommended the change is the one component guaranteed to have an opinion about whether the change did what it asked for, and it is the one nobody was asking.
- **One or more critical findings:** halt. Surface the findings. User addresses (either by fixing the code, amending the spec/plan via `/checkpoint`, or — rarely — formally accepting the risk with an ADR that downgrades the finding). Then re-run the full sequence from Gate 1, since fixes touch code, with Gate 3 carrying the grading brief. Same rule as the bullet above; the difference between the two branches is whether the merge was blocked in the meantime, not whether the fix gets reviewed.

- **The subagent returns nothing:** Gate 3 has not run, and a gate cannot report a pass it did not compute. Work `.claude/references/subagent-degraded-mode.md` § *Detect*, then re-invoke — a fresh security pass is cheap relative to the assurance it carries. If the user chooses to proceed without it, that is § *Decide*'s trade and it costs a `DEG` row per § *Record*. **Do not record Gate 3 as passed.**

**Writes:** the findings ledger — `SEC` rows when the review produces non-critical findings, and a `DEG` row if the review did not run.

### After all three gates pass — Summary and supersede

Load the `documenter` skill again. Run the "Summary authoring" pattern (see the documenter skill):

1. **If `.claude/state.md`'s `Summary:` field is `—`, write the summary** per the documenter's summary checklist, at the summaries directory the Orient step above resolved, named per that reference's § *Name*. Include the security-reviewer's non-critical findings in the "Security review notes" section. **Record the path it was written to in `.claude/state.md`'s `Summary:` field** — the filename carries this invocation's date, and `/pr-review` amends the file in a session that may be days later and cannot recompute it.

   **If `Summary:` already names a file, amend that file — do not author a second one.** A gate rerun on `in-review` reaches this step with a summary already written, at a filename carrying the *first* invocation's date. Authoring again produces a second dated file and overwrites the pointer, which strands the reviewed summary at a path nothing names and leaves `/pr-review` amending a document the PR body was never built from. Read the field, open that file, and propose the delta.
2. Update `docs/domains/<domain>.md` if the feature shifted domain vocabulary (per the documenter's "Domain doc updates" guidance). If `docs/domains/` doesn't exist and the feature is the project's first in a domain, create it.
3. **Supersede mechanic.** If the feature's spec lists `supersedes:` in its front-matter (or the work-in-progress conversation has identified parked features this merge absorbs), update `.claude/state.md`'s Parked features section: change each superseded entry's note to `superseded by <this-feature> (merged YYYY-MM-DD)`. The parked branch is **not** deleted — it remains for historical reference and possible cherry-pick — but it's clearly marked closed.

Surface all proposed doc writes to the user before applying. The documenter skill's cardinal "propose before writing" discipline holds at merge time too.

**Writes:** the summary at the resolved summaries directory · `.claude/state.md` (the `Summary:` field, and the Parked features section when step 3 supersedes anything) · `docs/domains/<domain>.md` for each domain the feature shifted.

This is the command's largest producer, and it is the one the closeout below is most likely to under-stage — the summary and the domain docs are new or newly-amended files that no other step names, and the `Summary:` field is what `/pr-review` reads days later to find the summary at all.

### Commit the closeout docs — before proposing any integration

Everything authored above is **uncommitted**. The preconditions demanded a clean tree, then this command dirtied it — and both `git push` and `git merge` transport only committed changes.

Propose a commit for **the union of every `**Writes:**` declaration the steps that ran produced** — read them off those steps. On a full run the sections carrying declarations are **Orient, Gate 2, Gate 3, and *After all three gates pass***; go read those four and stage what they name.

**That is a list of sections to read, deliberately, and not a list of files to stage** — the same rule `/feature-start` Phase H and `/plan` Phase G follow, and for the same reason. This paragraph previously enumerated the artifacts and named this closeout itself as one of the declaring sections. It is not: a carrier stages what producers declare, and the actual producer of the summary, the domain docs, and the `Summary:` field had no declaration at all. A reader following the derivation rule to the letter would have staged the `CLAUDE.md` entry, Gate 2's amendments, and the ledger — and dropped the summary.

Two of the four are quiet in opposite ways. Gate 3's ledger row is **remote**: written at the ledger's resolved path, not somewhere obvious in the diff. A row written and not committed is absent from the pushed branch in PR flow and left untracked after integration in local flow, which is the durable-memory failure the ledger was added to fix, reproduced one layer down. Orient's `CLAUDE.md` entry is **conditional**: written only for an artifact type nothing had recorded before, and dropping it sends the next feature back to re-deriving a location this one settled. Subject: `/feature-merge: summary + state.md`. Stage them explicitly; never `git add -A`.

**Record this commit's SHA.** It becomes `Gated baseline` at PR creation — it is the tip as it stands before the `state.md`-only transition commit, which is the one commit the discriminator's exclusion accounts for.

Skip this and the failure is quiet in both flows. In PR flow the body assembles correctly from a summary that **is not in the branch**, so reviewers get a description of a file the PR does not contain. In local-merge flow the merge succeeds and leaves the summary sitting untracked in the working directory, belonging to a feature that no longer has an active state.

Only after this commit lands do you proceed to *Merge proposal* or *PR creation*.

### Flow detection

Before proposing anything, determine whether this project merges locally or through a PR. Same three-tier pattern as *Merge strategy* below, same no-silent-default rule:

1. **`CLAUDE.md` convention.** If the project states a PR workflow (or states that it merges directly to mainline), follow it.
2. **Infer from the repo.** A remote exists (`git remote -v`), `gh` is available and authenticated (`gh auth status`), and the mainline has merged PRs in its history (`gh pr list --state merged --limit 1`) → PR flow. A repo with **no remote is local-merge, unambiguously** — don't ask, and don't mention PRs.
3. **Ask.** If neither is conclusive, ask. The wrong guess opens an unwanted PR or merges something that should have been reviewed.

If `gh` is absent or unauthenticated but the project is otherwise PR-shaped, say so and offer the **draft-only path**: the pack prepares the branch, the summary, and a PR body, and the user opens the PR by hand. Same for non-GitHub forges — the pack does not shell out to `glab` or equivalents.

**Writes:** none — reads the project's convention and the repo's shape, and reports which flow applies.

### Merge strategy

The pack does not assume a merge strategy — squash, merge commit, and rebase are all legitimate, and the choice is a project convention, not a pack decision. Determine it in this fixed order:

1. **`CLAUDE.md` convention.** If the project states a merge strategy (or a PR-tool workflow like `gh pr create`), follow it.
2. **Existing history.** If `CLAUDE.md` is silent, infer from the mainline's recent shape (`git log --merges <mainline>` for merge commits vs a flat, squashed history) and propose what matches — name the evidence.
3. **Ask.** If neither is conclusive, ask the user. Don't default silently to one strategy; the wrong one is annoying to undo after the fact.

Carry the determined strategy into the proposal below.

### Merge proposal

Once all docs are written and the strategy is determined (above), propose the merge mechanics.

Propose, in one short message:
- The merge command (e.g., `git checkout <mainline> && git merge --no-ff feature/<slug>` for a merge commit; or `git checkout <mainline> && git merge --squash feature/<slug> && git commit` for squash).
- The post-merge cleanup (`git branch -d feature/<slug>` to delete the local branch after merge; or `git branch -m feature/<slug> archive/<slug>` to rename if the project archives rather than deletes).
- The expectation that the user reviews `git log mainline..HEAD` (or equivalent) one last time before running.

**Wait for user confirmation.** Do not execute git merge ops without explicit go-ahead. Merge is the most irreversible action in this command; the friction is intentional.

### PR creation (PR flow)

Replaces *Merge proposal* when flow detection selected PR flow. The summary doc is already written at this point — that is deliberate, and it is what the PR body is built from.

Propose, in one short message:

- The push (`git push -u origin feature/<slug>`).
- The `gh pr create` invocation, with `--title` from the spec's title and `--body-file` pointing at a temp file assembled per the `documenter` skill's *The summary as PR body* guidance: the summary's *What shipped* section, then links to the spec and plan at their actual paths (from `state.md`'s `Spec:` / `Plan:` fields) and any related ADR paths. Reviewers should arrive with the contract in front of them.
- Whether the PR is a draft. Default is not-draft; honor a `CLAUDE.md` convention if one states otherwise.

**Wait for user confirmation.** Opening a PR is outward-facing — it notifies reviewers and is visible to the whole team.

On confirmation: push, create the PR, then set `.claude/state.md` to `Phase: in-review`, `PR: <url>`, and **`Gated baseline: <the closeout commit's SHA>`** — the tip as it stands *before* the transition commit below, not the SHA the gates ran against. The closeout commit lands after the gates too, so the gate-time SHA is already two commits behind by the time the PR opens. **Do not clear state** — the feature is still active until the PR merges.

**Then commit and push that transition.** Subject: `/feature-merge: in-review (PR #<n>)`, staging `.claude/state.md` only. It is written *after* the closeout commit and after the push, so without this step the tracked file is left dirty and the remote branch still says `Phase: building` with no PR and no baseline. Review is explicitly asynchronous — another session, clone, or worktree resuming the feature would read `building`, take the PR-creation path a second time, and open a duplicate PR. A later closeout in the original worktree can also fail outright, because checking out mainline over a dirty tracked `state.md` is exactly what its own preconditions forbid.

Report the PR URL and point at `/pr-review`.

Update `Gated baseline` after **every** successful gate rerun — to the tip as it stands once any fix commits are in and before the `state.md`-only transition commit. Same rule as at PR creation: the baseline is the last commit whose content was gated, never the SHA that happened to be checked out when the gates started.

**Commit and push that update using the same recipe as the transition commit above:** stage `.claude/state.md` only, commit (subject e.g. `/feature-merge: gate rerun (PR #<n>)`), then push. Skipping it leaves the tree dirty against this command's own clean-tree preconditions and the new baseline unrecorded on the remote — a later invocation, possibly a different session, still reads the stale baseline and misjudges the discriminator.

A stale baseline is worse than none: it makes ungated commits look gated.

**Writes:** `.claude/state.md` — `Phase: in-review`, `PR: <url>`, and `Gated baseline: <SHA>` at PR creation, and `Gated baseline` again after every gate rerun. This section carries its own writes rather than deferring them to the closeout above: both the transition commit and the rerun commit stage `.claude/state.md` alone, and both land *after* the closeout commit has already been made and pushed.

### After the merge

In PR flow this section runs on a **later invocation** — the one that found `Phase: in-review` with a merged PR. The merge may have been performed by someone else, days ago, in a session that no longer exists. Everything below applies unchanged; only the trigger differs.

**Check out mainline before writing anything.** PR creation never leaves the feature branch, so a closeout invocation is normally still on `feature/<slug>`. Writing the idle transition there strands it on a branch that is about to be deleted, while mainline keeps the feature's stale `building` state — and the next `/feature-start` orients against that. Order: `git checkout <mainline>`, `git pull` (the merge happened remotely), write the state transition, **commit it**, then propose any push.

Once the merge has been executed (by the user locally, by you on their instruction, or on the forge by anyone):

1. **Clear state.md** to the idle pointer shape: Active feature `none`, Active branch `<mainline>`, Phase `idle`, Spec/Plan/**Summary**/PR/**Gated baseline**/Next step `—`. Leaving a merged PR's SHA in `Gated baseline` makes the idle pointer assert that some commit passed gates for a feature that no longer exists. Move the just-merged feature's entry to "Last merge: <feature> (YYYY-MM-DD)".
2. Surface a one-line completion summary (feature merged, summary doc at `<path>`, branch archived/deleted).

The pack expects the user to push the mainline branch themselves; `/feature-merge` does not auto-push (push is also irreversible from a code-review perspective).

**Writes:** `.claude/state.md`, cleared to the idle pointer shape. Propose a commit staging it alone — subject `/feature-merge: closeout (<feature> merged)`. This runs after the integration the closeout commit above was written for, so it has no carrier but its own; an uncleared `state.md` leaves the next `/feature-start` blocked on its `Active feature is none` precondition, holding a feature that no longer exists.

## Halt conditions

Stop and surface, without auto-recovering:

- Any precondition fails (no active feature, dirty tree, unapproved spec/plan, wrong branch).
- Gate 1 fails (tests red or lint/typecheck fail).
- Gate 2 surfaces drift or coverage gap; user has not yet chosen a resolution path.
- Gate 3 returns one or more critical findings.
- The security-reviewer returns a finding it couldn't complete (e.g., couldn't read the diff — see the subagent's "When to return findings without completing the full review").
- The user rejects the proposed merge mechanics (e.g., the project routes merges through `bors` or `mergify` rather than either direct `git merge` or `gh pr create`, both of which this command supports).
- The user declines to confirm the merge proposal, or the PR-creation proposal.
- Flow detection is inconclusive and the user has not chosen a flow.
- PR flow was selected but `gh` is unavailable or unauthenticated, and the user has not opted into the draft-only path.
- `Phase: in-review` but no PR can be found for the branch — state and reality disagree. Surface both; do not silently re-open a PR or silently reset the phase.
- `in-review` and local doesn't agree with remote: uncommitted changes to tracked files, untracked files not yet resolved, or local `HEAD` **not equal** to what `git ls-remote origin <branch>` reports — **in either direction**. Halt and report which it is; do not run the discriminator against content the PR doesn't actually have yet. Local *behind* the remote is the case a directional check misses, and it is the common one: it happens whenever another clone or the web UI pushes to the PR. This list and precondition 2 state the same rule, and they must keep stating the same rule.
- `gh pr view` fails while checking merged state. Ask whether the PR merged; never treat a failed call as "not merged."

After any halt, the user resolves; re-running `/feature-merge` picks up from the beginning (Gate 1). Re-running is cheap because gates 1 and 2 are mostly read-only and the security-reviewer's work is fresh-context per invocation — no harm in re-running the full sequence after a fix.

## Notes on the merge being irreversible

`/feature-merge` is the only pack command that proposes git-history-altering operations. Even though all three gates pass before the proposal, the propose-before-acting friction is deliberate. The gates catch *what we knew to check*; user review catches *what the gates didn't think to check*. Both matter.

If a merge goes wrong (e.g., the wrong branch was merged; the merge included an accidental WIP commit), revert is `git revert -m 1 <merge-commit>` for merge-commit-style merges. The pack does not include a `/feature-revert` command; that's a manual git operation by design.
