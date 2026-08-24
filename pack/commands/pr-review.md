---
description: Intake, triage, and respond to pull-request review feedback. Fetches all three GitHub comment surfaces, classifies each finding per `.claude/references/findings-triage.md`, routes accepted in-scope items to a fix under `engineer` discipline and out-of-scope items to `/checkpoint`, and proposes every reply as one batch before anything is posted. Re-runnable as new comments land; skips threads already answered. Only meaningful while `Phase: in-review`.
---

Drive the review-response loop for a feature whose PR is open. One `/pr-review` invocation handles one pass over the outstanding comments; run it again as more land.

`/pr-review` is the **triage** command, not the auto-responder. Its output is a proposal — fixes, replies, and doc amendments — that you confirm before anything reaches the PR. Posting to a shared PR is outward-facing and visible to the whole team; that is the same friction class as the merge proposal, and it gets the same treatment.

## Arguments

- **`/pr-review`** — normal mode. Skips threads the pack has already replied in.
- **`/pr-review all`** — re-triage every thread, including previously-answered ones. Use when replies were posted manually outside the pack, or when a spec amendment changes how earlier findings should have been classified. The pack's own replies stay excluded; `all` re-opens the reviewer's items, not the answers to them.

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

Skip an item if **any** is true:

1. **A marker names its id.** Some reply on the PR carries `handled:<this item's id>` — the item has been answered.
2. **The item itself contains a marker.** It is one of the pack's own replies.
3. **The item's body is empty.** An empty body carries no finding, so there is nothing to triage. This is not a heuristic: GitHub wraps a reply posted through the replies endpoint in a **review submission**, which `gh pr view --json reviews` then returns as an entry authored by the replier with no body at all. It carries no marker because it has nowhere to put one, and no marker names its id because the marker in the reply names the *original* comment. A bare `APPROVED` with no body is the same shape and is likewise not a finding — the inline comments carry the content, and those are fetched separately.

All three checks must be implemented — an item matching **any** is skipped — and the second check is the one that is easy to miss. A reply's marker names the *original* comment's id, while the reply is itself a comment with a *different* id that no marker names. Condition 1 alone would therefore skip the original and treat the pack's own answer as a new item to respond to — proposing replies to its own replies, growing by one every pass. This is the same defect as the `in_reply_to_id` bug it replaced, recurring one level up: the pack's own actions are among the things that changed the state it is reading.

Condition 3 is that same defect one level up again. `in_reply_to_id` existed only on inline comments, so condition 2 replaced it; condition 2 reads a body, so a reply that becomes a *review* escapes it. Each fix closed the level in front of it. Condition 3 is content-free by construction rather than id-matching, which is why it closes every surface at once: an item with nothing in it cannot be a finding, whatever mechanism produced it.

Search all three surfaces for markers, build the handled set, then skip. **Report the skipped count** — silent omission is precisely the failure this guard prevents, and a number the user can sanity-check is the whole point. **`/pr-review all` disables condition 1 only.** Conditions 2 and 3 always apply, in any mode: an item carrying a devkit marker is the pack's own reply, and an item with an empty body has no content to re-triage. Disabling either would re-fetch the pack's own replies and offer to answer them — the exact recursion the paragraph above prevents, reintroduced by the flag meant to re-triage the reviewer's comments.

ADR-0003 chose the forge as the triage ledger — no local state — and that choice stands. What failed was the *detection*: `in_reply_to_id` exists only on inline review comments, so replies to review bodies and top-level comments recorded nothing, and a second pass re-fetched both the original item **and** the pack's own reply, then offered to answer it again. A marker the pack writes itself works on every surface and still requires no local bookkeeping.

If a thread has a reply from the PR author but **no** marker, the user answered it by hand. Treat it as unhandled but say so — the user may want it skipped, and that is their call rather than an inference.

Also read the active spec, the plan, and any ADRs named in their front-matter. You cannot classify a finding as "already answered by the spec" without having read the spec.

### Phase B — Triage

Classify every item into exactly one bucket from `.claude/references/findings-triage.md` → *Classification buckets*. This is an **external** source: verify the claim against the repo before accepting it. An external reviewer's confident claim is exactly the case `.claude/references/evidence-and-uncertainty.md` § *Facts* names — provenance you did not establish reads as verified unless you check.

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
2. **Doc amendments** — the summary's *Review notes*, and where shipped behavior changed, *What shipped*. The summary's path is `.claude/state.md`'s `Summary:` field; read it there rather than reconstructing it, since the filename carries the creation date of the invocation that wrote it. If the field is `—`, surface that and stop — a summary that cannot be located cannot be amended, and writing a second one is worse than not writing. Through the `documenter` skill, propose-before-write as always.
3. **The findings ledger and `.claude/state.md`.** Anything accepted but deferred past this feature goes in the ledger as a `REV` row (see the documenter skill's *The findings ledger*; its location is discovered, not assumed). `state.md`'s `## Open questions` holds only what must be resolved *within this feature* — `/feature-merge` clears that section, so a finding parked there and not fixed before merge is a finding silently discarded. Remove entries whose fix just landed.
4. **Commit the artifacts.** Stage exactly what stages 2 and 3 wrote *other than* `.claude/state.md` — the summary doc and the discovered findings-ledger path — and propose a commit. Subject: `review: findings ledger + summary`. Stage explicitly; never `git add -A`.
5. **Commit `.claude/state.md` alone.** Subject: `review: state`. Two commits, in that order, always — not only when a baseline is in play.

   **Why unconditionally.** `/feature-merge` requires this split whenever a gate rerun records a `Gated baseline`, and it explains why: the discriminator excludes only `.claude/state.md`, so a combined commit puts gated content in a commit the exclusion does not account for, and the next invocation re-runs gates that already passed. `/feature-merge` owns that rule and this command does not restate it — see its *Why two commits*. What this command owns is not producing a commit shape the other command cannot consume. A conditional split ("only when a baseline is owed") puts the decision in the hands of a reader who has to know what the *other* command is going to do next; an unconditional split costs one extra commit on a metadata-only pass and cannot be got wrong.

   Stages 4 and 5 write durable artifacts and stage 6 pushes; without them, neither reaches the remote. The PR then lacks the `REV` record that is the whole point of a cross-feature deferral, and the tree stays dirty — which `/feature-merge`'s own preconditions treat as blocking, so the next closeout cannot check out mainline.

   **If the user declines either commit, stop here — do not proceed to stage 6.** Like every commit in this pack, it's a proposal the user may decline, but declining leaves the summary, ledger, and `state.md` edits uncommitted, and pushing the fix commits anyway would strand exactly those artifacts locally: the failure these stages exist to close. The user's options are to commit (editing the message or splitting further, if they want) or to stop and resolve the tree by hand; either way, re-run `/pr-review` once the tree is clean rather than continuing past the decline.
6. **Push — and verify the remote tip actually contains the fix commits.** Check with `git ls-remote origin <branch>`, compared against your local `HEAD`.

   Use `git ls-remote`, **not** `gh pr view --json headRefOid`. The former reads the ref directly and is authoritative the moment the push lands; the latter reads GitHub's PR view, which can serve a stale `headRefOid` for seconds after a successful push. Verifying with the API produces a false *negative* — a correct push reported as unverified — and the correct response to an unverified push is to post nothing, so the failure mode is a stalled run rather than a bad one. Still worth avoiding: a check that cries wolf gets skipped.
7. **Replies**, only after that verification passes.

**Push before replying.** A reply citing a SHA is a public, unrecallable claim about the remote — and until the push succeeds that SHA does not exist there. If the push then fails (auth, network, a rejected non-fast-forward because someone else pushed), the PR is left carrying citations to code it does not contain, in comments addressed to the reviewers who will go looking.

An earlier version of this command had replies last, reasoning that *"a reply saying 'fixed in `<sha>`' is true when it posts."* That reads as correct and is exactly backwards: the SHA is true **locally**, and the reply is a statement about the remote. Verifying the tip — rather than assuming a successful `git push` implies it — closes the remaining gap where the push reports success against a stale remote ref.

**Writes:** the confirmed code fixes and doc amendments · `REV` rows in the findings ledger · `.claude/state.md`.

### Phase E — Hand off

One short report: items per bucket, commits made (the fixes **and** both metadata commits), replies posted, **findings recorded in the ledger** (cross-feature deferrals), items left in `state.md` Open questions (in-feature only), and threads skipped as already-answered. Keep those last two distinct — reporting a cross-feature deferral as "parked in Open questions" invites it back into a section `/feature-merge` clears.

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
- **Either metadata commit (Phase D stages 4–5) is declined.** Report what's still uncommitted (summary doc, findings-ledger entry, `.claude/state.md`) and stop — do not push the fix commits from stage 1 while those remain uncommitted. The user commits the metadata (as proposed or edited) or resolves the tree themselves; re-run `/pr-review` once it's clean.

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
