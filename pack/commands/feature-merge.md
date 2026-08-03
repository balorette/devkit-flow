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
| `in-review`, PR open, **PR tip == `Gated baseline`** | Report review status and open-thread count. Point at `/pr-review`. Run no gates — this exact commit already passed them. |
| `in-review`, PR open, **PR tip != `Gated baseline`** | Re-run gates 1–3 — the PR contains commits that have never been gated — then push and update `Gated baseline`. Do **not** re-create the PR. |
| `in-review`, PR merged | Closeout only (see *After the merge*). **Skip the gates**; the merge already happened. |

**The discriminator is `Gated baseline` versus the PR tip — never local tip versus remote tip.** `/pr-review` commits its fixes and pushes them, so after it runs the local and remote tips agree while carrying commits no gate has ever seen. A rerun keyed on tip equality would take the *nothing changed* path and skip tests, docs reconciliation, and security review on precisely the code that is about to merge. Read the PR tip with `gh pr view --json headRefOid`.

Which flow applies is settled by *Flow detection* below (`CLAUDE.md` convention → infer from the repo → ask). The gates are identical in both flows, so that determination can wait until the proposal — but `Phase: in-review` only ever occurs in PR flow, so the last three rows need no detection.

Merged-state detection is `gh pr view --json state,mergedAt`. If `gh` fails or is unauthenticated, **ask the user whether the PR merged** — do not guess, and do not treat a failed call as "not merged."

The numbered preconditions below apply to the two `building` / `merging` rows. The `in-review` rows have their own precondition: `PR:` is set in state.md, or a PR is discoverable for the current branch.

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

The three gates run in fixed order: tests → docs → security. Each gate's failure surfaces concrete remediation. The gates are independent — a Gate-2 failure doesn't tell you anything about Gate 3 — but they execute sequentially because each is cheap to re-run after a fix and there's no value in showing the user three problems at once.

### Gate 1 — Tests pass

Load the `engineer` skill. Identify the test runner from the plan's "Approach" section or from project config (`pyproject.toml`, `package.json`, `Cargo.toml`). Run the full test suite (not just the feature's tests — regressions matter at merge time).

- **Suite green:** proceed to Gate 2.
- **Suite red:** halt. Surface the failing tests' names and a one-line "fix or amend the plan via `/checkpoint`" prompt. Do not proceed to other gates — a red suite invalidates downstream assumptions.

Also run linter / type-checker if the project has them configured. Their failures are merge-blocking at the same severity as red tests; same halt behavior.

### Gate 2 — Docs reconciliation

Load the `documenter` skill. Run a final-pass version of Pattern D (see the documenter skill's "Pattern D — On-demand reconciliation") **plus** an additional acceptance-criteria-coverage check:

- **Pattern D checks:** `owned_files` coherence (any commits touching files outside scope?); state.md coherence (Spec/Plan paths exist; Phase makes sense for a feature about to merge); spec/plan front-matter coherence.
- **Acceptance-criteria coverage:** read the spec's "Acceptance criteria" section. For each criterion, identify which plan step (or completed work) satisfies it. Any criterion not mapped to completed work is a coverage gap. The plan's "Acceptance mapping" table (per the pm skill's plan-time guidance) is the primary source; the documenter cross-references against the plan's Completed steps in state.md.

If all checks pass: proceed to Gate 3.

If anything is unaddressed:
- **Drift surfaced:** documenter proposes resolution per Pattern A. User confirms; documenter applies; re-run Gate 2 from the top.
- **Coverage gap:** the spec promised behavior the plan/code didn't deliver. Two resolution paths:
  - **Scope-cut amendment:** trim the spec's acceptance criteria via `/checkpoint`. Honest "we shipped less than originally scoped" — explicit in the amendment note. The cut criteria become followups in the summary.
  - **Build the missing work:** continue `/build` for the remaining plan steps; come back to `/feature-merge` when complete.

The user picks. Don't proceed past Gate 2 with a coverage gap silently.

### Gate 3 — Security review

Invoke the `security-reviewer` subagent in fresh context. Pass:
- The diff command (`git diff <mainline>..HEAD`) for the subagent to run itself.
- Path to the active spec.
- Paths to related ADRs from the spec/plan front-matter.
- Path to the active plan (intent context only; not authoritative for security).

The subagent returns a structured findings document with severity-bucketed entries (critical / high / medium / low / informational).

- **Zero critical findings:** Gate 3 passes. Surface the full findings document to the user — they need to know the medium/low/informational items even though they don't block.
- **One or more critical findings:** halt. Surface the findings. User addresses (either by fixing the code, amending the spec/plan via `/checkpoint`, or — rarely — formally accepting the risk with an ADR that downgrades the finding). Re-run Gate 3 (or the full sequence from Gate 1, since fixes touch code) after resolution.

### After all three gates pass — Summary and supersede

Load the `documenter` skill again. Run the "Summary authoring" pattern (see the documenter skill):

1. Write `docs/summaries/<feature>.md` per the documenter's summary checklist. Include the security-reviewer's non-critical findings in the "Security review notes" section.
2. Update `docs/domains/<domain>.md` if the feature shifted domain vocabulary (per the documenter's "Domain doc updates" guidance). If `docs/domains/` doesn't exist and the feature is the project's first in a domain, create it.
3. **Supersede mechanic.** If the feature's spec lists `supersedes:` in its front-matter (or the work-in-progress conversation has identified parked features this merge absorbs), update `.claude/state.md`'s Parked features section: change each superseded entry's note to `superseded by <this-feature> (merged YYYY-MM-DD)`. The parked branch is **not** deleted — it remains for historical reference and possible cherry-pick — but it's clearly marked closed.

Surface all proposed doc writes to the user before applying. The documenter skill's cardinal "propose before writing" discipline holds at merge time too.

### Flow detection

Before proposing anything, determine whether this project merges locally or through a PR. Same three-tier pattern as *Merge strategy* below, same no-silent-default rule:

1. **`CLAUDE.md` convention.** If the project states a PR workflow (or states that it merges directly to mainline), follow it.
2. **Infer from the repo.** A remote exists (`git remote -v`), `gh` is available and authenticated (`gh auth status`), and the mainline has merged PRs in its history (`gh pr list --state merged --limit 1`) → PR flow. A repo with **no remote is local-merge, unambiguously** — don't ask, and don't mention PRs.
3. **Ask.** If neither is conclusive, ask. The wrong guess opens an unwanted PR or merges something that should have been reviewed.

If `gh` is absent or unauthenticated but the project is otherwise PR-shaped, say so and offer the **draft-only path**: the pack prepares the branch, the summary, and a PR body, and the user opens the PR by hand. Same for non-GitHub forges — the pack does not shell out to `glab` or equivalents.

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
- The `gh pr create` invocation, with `--title` from the spec's title and `--body-file` pointing at a temp file assembled per the `documenter` skill's *The summary as PR body* guidance: the summary's *What shipped* section, then links to `docs/specs/<slug>.md`, `docs/plans/<slug>.md`, and any related ADR paths. Reviewers should arrive with the contract in front of them.
- Whether the PR is a draft. Default is not-draft; honor a `CLAUDE.md` convention if one states otherwise.

**Wait for user confirmation.** Opening a PR is outward-facing — it notifies reviewers and is visible to the whole team.

On confirmation: push, create the PR, then set `.claude/state.md` to `Phase: in-review`, `PR: <url>`, and **`Gated baseline: <the SHA that just passed gates 1–3>`**. **Do not clear state** — the feature is still active until the PR merges. Report the PR URL and point at `/pr-review`.

Update `Gated baseline` again after **every** successful gate rerun, to the SHA those gates ran against. A stale baseline is worse than none: it makes ungated commits look gated.

### After the merge

In PR flow this section runs on a **later invocation** — the one that found `Phase: in-review` with a merged PR. The merge may have been performed by someone else, days ago, in a session that no longer exists. Everything below applies unchanged; only the trigger differs.

Once the merge has been executed (by the user locally, by you on their instruction, or on the forge by anyone):

1. **Clear state.md** to the idle pointer shape: Active feature `none`, Active branch `<mainline>`, Phase `idle`, Spec/Plan/PR/Next step `—`. Move the just-merged feature's entry to "Last merge: <feature> (YYYY-MM-DD)".
2. Surface a one-line completion summary (feature merged, summary doc at `<path>`, branch archived/deleted).

The pack expects the user to push the mainline branch themselves; `/feature-merge` does not auto-push (push is also irreversible from a code-review perspective).

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
- `gh pr view` fails while checking merged state. Ask whether the PR merged; never treat a failed call as "not merged."

After any halt, the user resolves; re-running `/feature-merge` picks up from the beginning (Gate 1). Re-running is cheap because gates 1 and 2 are mostly read-only and the security-reviewer's work is fresh-context per invocation — no harm in re-running the full sequence after a fix.

## Notes on the merge being irreversible

`/feature-merge` is the only pack command that proposes git-history-altering operations. Even though all three gates pass before the proposal, the propose-before-acting friction is deliberate. The gates catch *what we knew to check*; user review catches *what the gates didn't think to check*. Both matter.

If a merge goes wrong (e.g., the wrong branch was merged; the merge included an accidental WIP commit), revert is `git revert -m 1 <merge-commit>` for merge-commit-style merges. The pack does not include a `/feature-revert` command; that's a manual git operation by design.
