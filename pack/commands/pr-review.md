---
description: Intake, triage, and respond to pull-request review feedback. Fetches all three GitHub comment surfaces, classifies each finding per `.claude/references/findings-triage.md`, routes accepted in-scope items to a fix under `engineer` discipline and out-of-scope items to `/checkpoint`, and proposes every reply as one batch before anything is posted. Re-runnable as new comments land; skips threads already answered. Only meaningful while `Phase: in-review`.
---

Drive the review-response loop for a feature whose PR is open. One `/pr-review` invocation handles one pass over the outstanding comments; run it again as more land.

`/pr-review` is the **triage** command, not the auto-responder. Its output is a proposal — fixes, replies, and doc amendments — that you confirm before anything reaches the PR. Posting to a shared PR is outward-facing and visible to the whole team; that is the same friction class as the merge proposal, and it gets the same treatment.

## Arguments

- **`/pr-review`** — normal mode. Skips threads the pack has already replied in.
- **`/pr-review all`** — re-triage every thread, including previously-answered ones. Use when replies were posted manually outside the pack, or when a spec amendment changes how earlier findings should have been classified.

## Preconditions

1. Read `.claude/state.md`. `Phase` is `in-review` with `PR:` set, **or** a PR is discoverable for the current branch (`gh pr view --json number`).
2. `gh` is available and authenticated (`gh auth status`). If not, offer the **paste-in fallback**: the user pastes the review comments, the pack triages them and drafts replies for the user to post by hand. Everything below applies except Phase A's fetch and Phase D's posting.
3. If no PR exists at all, stop and point at `/feature-merge` — the PR has to be opened before it can be reviewed.

If `Phase: in-review` but no PR can be found, state and reality disagree. Surface both and stop; do not silently re-open a PR and do not silently reset the phase.

## Run

### Phase A — Fetch

Three surfaces carry findings. Fetch all three — a reviewer's most substantive objection is as likely to be in a review body as attached to a line of code.

| Surface | Fetch | Reply mechanism |
|---|---|---|
| Inline review comments (threaded) | `gh api repos/{owner}/{repo}/pulls/{n}/comments` | `gh api --method POST repos/{owner}/{repo}/pulls/{n}/comments/{id}/replies -F body=@<file>` |
| Review submission bodies (`APPROVED` / `CHANGES_REQUESTED` / `COMMENTED`) | `gh pr view --json reviews` | Not repliable in-thread → `gh pr comment` |
| Top-level conversation comments | `gh pr view --json comments` | `gh pr comment` |

**Skip what the pack has already answered — on all three surfaces.** Every reply the pack posts ends with a marker:

```html
<!-- devkit:pr-review handled:<comment-id> -->
```

An item is handled when a marker naming its id exists anywhere on the PR. Search all three surfaces for markers, build the handled set, then skip those items. **Report the skipped count** — silent omission is precisely the failure this guard prevents, and a number the user can sanity-check is the whole point. `/pr-review all` disables the skip.

ADR-0003 chose the forge as the triage ledger — no local state — and that choice stands. What failed was the *detection*: `in_reply_to_id` exists only on inline review comments, so replies to review bodies and top-level comments recorded nothing, and a second pass re-fetched both the original item **and** the pack's own reply, then offered to answer it again. A marker the pack writes itself works on every surface and still requires no local bookkeeping.

If a thread has a reply from the PR author but **no** marker, the user answered it by hand. Treat it as unhandled but say so — the user may want it skipped, and that is their call rather than an inference.

Also read the active spec, the plan, and any ADRs named in their front-matter. You cannot classify a finding as "already answered by the spec" without having read the spec.

### Phase B — Triage

Classify every item into exactly one bucket from `.claude/references/findings-triage.md` → *Classification buckets*. This is an **external** source: verify the claim against the repo before accepting it.

The reviewer has not read the spec. That is a fact about their access, not a judgment about them — cite the spec, don't condescend to it. If the PR body doesn't link the spec, that is a `/feature-merge` problem worth fixing rather than a reviewer failing.

### Phase C — Propose

One batch, one table:

| Comment | Classification | Action | Draft reply |
|---|---|---|---|
| `@reviewer` on `src/x.py:42` | Accept, in scope | Fix + `review:` commit | *(draft text)* |

Propose the whole set before applying any of it — the same discipline the `documenter` skill uses for multi-doc merge-time proposals. A batch lets the user see the shape of the response as a whole, which is where inconsistencies show up.

**Wait for confirmation.** The user may reclassify any row; apply the revised version, not the original. Do not apply a first pass and then refine — re-propose, then apply once.

### Phase D — Apply

Strict order. Each stage completes before the next begins.

1. **Code fixes**, one at a time, each under the `engineer` skill's Verify discipline: tests green, lint and type-check clean, its own commit. Subject `review: <short summary>`. Stage explicitly; never `git add -A`. A review fix that cannot be brought green is not a fix — halt and surface it.
2. **Doc amendments** — the summary's *Review notes*, and where shipped behavior changed, *What shipped*. Through the `documenter` skill, propose-before-write as always.
3. **The findings ledger and `.claude/state.md`.** Anything accepted but deferred past this feature goes in the ledger as a `REV` row (see the documenter skill's *The findings ledger*; its location is discovered, not assumed). `state.md`'s `## Open questions` holds only what must be resolved *within this feature* — `/feature-merge` clears that section, so a finding parked there and not fixed before merge is a finding silently discarded. Remove entries whose fix just landed.
4. **Push — and verify the remote tip actually contains the fix commits** (`gh pr view --json headRefOid`, compared against your local `HEAD`).
5. **Replies**, only after that verification passes.

**Push before replying.** A reply citing a SHA is a public, unrecallable claim about the remote — and until the push succeeds that SHA does not exist there. If the push then fails (auth, network, a rejected non-fast-forward because someone else pushed), the PR is left carrying citations to code it does not contain, in comments addressed to the reviewers who will go looking.

An earlier version of this command had replies last, reasoning that *"a reply saying 'fixed in `<sha>`' is true when it posts."* That reads as correct and is exactly backwards: the SHA is true **locally**, and the reply is a statement about the remote. Verifying the tip — rather than assuming a successful `git push` implies it — closes the remaining gap where the push reports success against a stale remote ref.

### Phase E — Hand off

One short report: items per bucket, commits made, replies posted, items parked in Open questions, threads skipped as already-answered.

If every thread is answered and the working tree is clean, suggest re-running `/feature-merge`. New commits mean gates 1–3 need re-validation against the code that will actually merge.

## Hard rules

- **Never post a reply the user has not seen.** No exceptions, no "obviously fine" replies, no batching a small acknowledgement in with a confirmed one. The user's name is on it.
- **A review fix is still a step.** It ends in a green suite and is independently revertable. "It's just a quick review fix" is a rationalization, not an exception to the engineer skill.
- **Never expand scope inside a PR.** Outside the spec's `owned_files` → `/checkpoint` amendment or a followup. A PR is the worst possible place to discover that a feature grew.

## Halt conditions

Stop and surface to the user (do not auto-recover) if:

- `Phase: in-review` but no PR can be found for the branch.
- `gh` is unavailable or unauthenticated and the user declines the paste-in fallback.
- A finding contradicts an approved spec and the user has not chosen between amending and declining.
- A review fix cannot be brought green within the current step.
- A failing CI check is reported on the PR. Surface it and stop — CI diagnosis is out of scope for this command.
- The user declines the proposed batch without providing a revision.
- A reply fails to post (`gh` error, thread locked, PR closed mid-run). Report which replies landed and which did not; never retry blindly into a PR whose state you no longer know.
- **The push fails, or the remote tip does not contain the fix commits after it.** Report which commits are local-only, **post nothing**, and stop. Fixes that exist only on your machine plus replies announcing them is the worst state this command can leave a PR in — the reviewer sees claims they cannot verify and code that has not changed.

## Common rationalizations

Review triage fails for social reasons rather than technical ones, which is exactly why the excuses work. If you find yourself reasoning one of these, stop.

| Excuse | Rebuttal |
|---|---|
| "The reviewer approved, so I can post replies without asking." | Approval is about the code, not about who speaks for the user. Every reply is proposed. (See *Hard rules*.) |
| "This fix is trivial; it doesn't need its own commit." | Trivial fixes are the ones most likely to be reverted independently later, which is what per-step commits are for. Size is not the criterion — revertability is. (See *Phase D*, step 1.) |
| "I'll answer the clear comments now and come back to the ambiguous one." | Review items in a cluster are usually related. Answering four of five and then learning the fifth reframes all of them means redoing the four — publicly. (See `findings-triage.md` rule 5.) |
| "The spec is stale anyway — easier to just make the change." | Then amend the spec. "The document is out of date" argues for updating the document, never for ignoring it. (See `findings-triage.md` rule 1.) |
| "It's a one-line change outside `owned_files`, not really scope creep." | Scope is measured by which files change, not by how many lines. The drift hook will flag it regardless; decide deliberately instead of being told afterward. (See *Hard rules*.) |
| "I'll fix the code and mention it in the reply I'm about to draft." | Order matters: fixes land, then replies post. A reply claiming a sha that doesn't exist yet is a lie with a timestamp on it. (See *Phase D*.) |

## How this command plugs into the pack

- **`/feature-merge`** opens the PR and sets `Phase: in-review`; it is also what you run *after* this command to re-validate the gates, and once more after the PR merges to close out.
- **`.claude/references/findings-triage.md`** owns the classification discipline. This command sequences it against a PR; it does not restate it.
- **`engineer` skill** governs every code fix, exactly as it does during `/build`.
- **`documenter` skill** proposes the summary amendments.
- **`/checkpoint`** is where out-of-scope findings go. If a finding is really a new feature, that is `/feature-start` with the current feature parked — say so rather than growing this one.
