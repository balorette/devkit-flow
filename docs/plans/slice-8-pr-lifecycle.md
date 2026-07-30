---
slice: 8
status: draft
design: docs/design/0003-pr-lifecycle-and-findings-triage.md
---

# Slice 8 — PR Lifecycle and Findings Triage: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the devkit pack's feature lifecycle through pull-request review — a `Phase: in-review` state that survives the session, a re-runnable `/feature-merge` that opens the PR and later closes out an asynchronous merge, a new `/pr-review` command for intake and response, and a shared findings-triage discipline that serves internal subagents as well as external reviewers.

**Architecture:** Two new pack files plus edits to the state template, two commands, two skills, and the user-facing docs. No new skill and no new subagent — this is orchestration of primitives the pack already has. `/pr-review` routes out-of-scope findings to `/checkpoint`, code fixes through the `engineer` skill's Verify discipline, and doc amendments through `documenter`. GitHub is first-class via `gh`; other forges degrade to a draft-only path.

**Tech Stack:** Markdown pack content (Claude Code `SKILL.md` / command / reference formats); `install.sh` (bash) + `install_lib.py` (python3) for packaging; `gh` CLI 2.86+ as the runtime dependency of the authored command.

---

## Global Constraints

Copied from `docs/design/0003-pr-lifecycle-and-findings-triage.md` and this project's `CLAUDE.md`. Every task's requirements implicitly include this section.

- **Native-first.** Slice 8 adds no new skill and no new subagent. If a problem can be solved by an existing primitive, that is the answer.
- **Propose before writing.** No pack component silently applies a doc edit, a commit, or a merge.
- **Never post unseen.** `/pr-review` must never post a reply to a PR that the user has not seen and confirmed.
- **A review fix is still a step.** It ends in a green suite and is independently revertable.
- **Never `git add -A` / `git add .`** — stage the task's files explicitly, every time.
- **Design docs are the contract.** If implementation diverges from `0003`, update `0003` with rationale in the same commit. Two known divergences are already scheduled in Task 8.
- **GitHub first-class.** `gh` is the assumed tool; other forges get a documented draft-only fallback. No `glab` support in this slice.
- **Out of scope, explicitly:** labels, reviewer assignment, CI babysitting, merge-queue interaction, GraphQL thread resolution.

### The test cycle for this project

This repo authors markdown, not code, and has **no automated test suite**. Per `CLAUDE.md` working principle 4, the test analogue is a **behavioral prediction plus a fresh-session run**:

1. Before authoring, write down the example task and the predicted behavior.
2. Author the file.
3. Run the example task in a fresh Claude Code session with the pack loaded.
4. Compare actual to predicted. **If behavior diverges from prediction, the pack content needs revision — not the prediction.**

Two mechanical checks are available and are cheap enough to run per task:

```bash
# A — installer picks up new/changed pack files (no writes; safe to re-run)
./install.sh "$(mktemp -d)" --dry-run

# B — cross-reference integrity: every cited pack path actually exists
grep -rhoE '\.claude/(references|commands|skills|agents)/[A-Za-z0-9._/-]+' pack/ \
  | sort -u \
  | sed 's|^\.claude/||' \
  | while read -r p; do [ -f "pack/$p" ] || echo "DANGLING: $p"; done
```

Behavioral predictions and their outcomes are recorded in `docs/validation/slice-8.md` (created in Task 8), matching `docs/validation/slice-1.md` … `slice-6.md`.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `pack/references/findings-triage.md` | **Create** | The shared discipline for evaluating any finding, internal or external. Cited, never loaded wholesale. |
| `pack/commands/pr-review.md` | **Create** | Fetch → triage → remediate → respond, across the three GitHub comment surfaces. Re-runnable. |
| `pack/state.md.template` | Modify | Adds `in-review` to the Phase enum, a `PR:` field, and the Open-questions-as-review-ledger note. |
| `pack/commands/feature-merge.md` | Modify | Flow detection, the Phase-branch table, the `gh pr create` path, re-runnable async closeout. |
| `pack/skills/documenter/SKILL.md` | Modify | Summary gains a review-notes section; PR-body-from-summary derivation guidance. |
| `pack/skills/engineer/SKILL.md` | Modify | Cites `findings-triage.md` for tester findings and architect recommendations. |
| `pack/CLAUDE.md.template` | Modify | A PR-workflow convention line so projects can state their flow. |
| `pack/devkit-orientation.md` | Modify | `/pr-review` in the command list; lifecycle mapping; two commit-cadence rows. |
| `README.md` | Modify | Components map, walkthrough step 8, lifecycle table. **Not in `0003`'s build list** — see Task 8. |
| `docs/design/inventory-and-build-order.md` | Modify | Slice-8 section, matching the slice-7 format. |
| `docs/design/0003-…md` | Modify | Two corrections (Task 8). |
| `docs/validation/slice-8.md` | **Create** | Behavioral predictions and dogfood outcomes. |
| `CLAUDE.md` (this project) | Modify | Status section. |

**Deliberately unchanged:** `install.sh` and `install_lib.py`. `install_lib.py:46` declares `TRACKED_DIRS = ("skills", "agents", "commands", "hooks", "references")` and `iter_tracked_pack_files` (`install_lib.py:55-71`) `rglob`s each one, so both new files are tracked, hashed, and installed with no code change. `install.sh:443` already `mkdir -p`s `commands` and `references`. Verify with mechanical check A rather than assuming.

**Task order rationale:** innermost-first, the same Clean Architecture dependency ordering the `engineer` skill imposes on plan steps. The reference has no dependencies; the state template must land before the commands that read it; `/pr-review` lands last among the behavior files because it consumes all three.

---

## Task 1: `references/findings-triage.md`

**Files:**
- Create: `pack/references/findings-triage.md`

**Interfaces:**
- Consumes: nothing. This is the innermost file in the slice.
- Produces: the path `.claude/references/findings-triage.md` and these five stable anchor headings, cited by Tasks 2, 4, and 6: `## The shared loop`, `## Source matters`, `## The five devkit rules`, `## Classification buckets`, `## Common rationalizations`.

- [ ] **Step 1: Write the behavioral prediction**

Append to a scratch file (it moves into `docs/validation/slice-8.md` in Task 8):

```markdown
### Prediction T1 — spec-contradicting finding
Task: "A reviewer commented: 'this should page results, returning all rows won't
scale.' The spec's Out-of-scope section says 'pagination — deferred.'"
Predicted: cites the spec, does NOT edit code, classifies as
"already answered by the spec," drafts a reply naming the spec section.
Failure mode this catches: silently implementing pagination.
```

- [ ] **Step 2: Author the reference**

Follow the format of the three existing references (`pack/references/solid-checklist.md`, `clean-architecture-layers.md`, `security-categories.md`): no YAML front-matter, an H1, and terse cite-able sections. Required structure:

```markdown
# Findings triage

<one paragraph: any finding — from a subagent or a human — is a claim to be
evaluated, not an instruction to be executed. This file is the evaluation.>

## The shared loop

Read completely → restate the technical claim in one sentence → verify against
the repo **and** the spec → classify → respond → implement one at a time, each
ending green.

## Source matters

| | Internal (`tester`, `architect`, `security-reviewer`) | External (humans, review agents) |
|---|---|---|
| Has read the spec | Yes — it is passed in | **No** |
| Structure | Severity-bucketed, predictable | Free-form prose |
| Default posture | Trust the finding; evaluate the severity | Verify against the repo first |
| Blind spot | No conversation context | No spec, no ADR history, no `owned_files` |

## Classification buckets

| Classification | Action |
|---|---|
| Accept, in scope | Fix under the `engineer` skill's Verify discipline. Own commit. |
| Accept, outside `owned_files` | `/checkpoint` amendment, or a followup in the summary. Never silent scope expansion. |
| Already answered by spec or accepted ADR | Reply citing it. No code change. |
| Technically disagree | Reply with technical reasoning. Surface to the user before it goes anywhere public. |
| Unclear | Ask. Implement nothing else in that cluster until answered. |

## The five devkit rules

1. A finding that contradicts an approved spec is a **spec question**, not a code fix. Route to `/checkpoint`.
2. A finding that re-opens an accepted ADR is answered by **citing the ADR back**. If the context has genuinely changed since, that is a different finding and must be named as one.
3. A finding requiring work outside the spec's `owned_files` becomes a `/checkpoint` amendment or a followup — never silent scope expansion.
4. Never implement a finding that breaks the current step's **revertability**. Split it into its own step.
5. **Clarify every unclear item in a cluster before implementing any of it.** Partial understanding of related items produces the wrong implementation.

## Common rationalizations

<table, pack house style — at minimum these four rows:>
| "The reviewer is senior, just implement it." | … |
| "It's a one-line change, it doesn't need a `/checkpoint`." | … |
| "I'll implement the clear items now and ask about the unclear ones after." | … |
| "Pushing back will look defensive." | … |
```

- [ ] **Step 3: Run mechanical check A — installer picks up the new file**

```bash
./install.sh "$(mktemp -d)" --dry-run 2>&1 | grep -E "findings-triage"
```

Expected: one line showing `references/findings-triage.md` as a NEW file. If absent, `TRACKED_DIRS` is not behaving as read — stop and investigate before continuing.

- [ ] **Step 4: Run the behavioral prediction from Step 1**

Fresh Claude Code session, pack loaded, run the Prediction T1 task. Compare to the prediction. Record actual behavior verbatim in the scratch file. If it diverges, revise the reference — not the prediction.

- [ ] **Step 5: Commit**

```bash
git add pack/references/findings-triage.md
git commit -m "pack: add references/findings-triage.md (slice 8, task 1)"
```

---

## Task 2: Wire `findings-triage` into the `engineer` skill

Makes Task 1 live for internal findings before any PR machinery exists. This task is independently useful and independently revertable.

**Files:**
- Modify: `pack/skills/engineer/SKILL.md` — two insertion points

**Interfaces:**
- Consumes: `.claude/references/findings-triage.md` from Task 1.
- Produces: nothing other tasks depend on.

- [ ] **Step 1: Add the citation to the Red phase**

In `pack/skills/engineer/SKILL.md`, the Red section step 4 currently ends:

> Run the tests. They must fail. If any pass on first run, something is wrong — either the test isn't testing what it claims, or the production code already exists. Stop and investigate before continuing.

Append to that paragraph:

```markdown
If the tester returns **findings instead of tests**, do not work around them and do not re-invoke with a looser brief. Evaluate them per `.claude/references/findings-triage.md` (internal source) — most tester findings mean the plan's type signatures are wrong, which is a `/checkpoint` amendment, not a build-time improvisation.
```

- [ ] **Step 2: Add the citation to "When to stop and ask the user"**

That section currently lists four bullets ending with "Any time you would otherwise guess at intent." Insert as a new bullet before that last one:

```markdown
- The `architect` returns a recommendation you believe is wrong. Disagreement is legitimate; silent deviation is not. Evaluate it per `.claude/references/findings-triage.md` and surface the disagreement with technical reasoning.
```

- [ ] **Step 3: Run mechanical check B — no dangling cross-references**

```bash
grep -rhoE '\.claude/(references|commands|skills|agents)/[A-Za-z0-9._/-]+' pack/ \
  | sort -u | sed 's|^\.claude/||' \
  | while read -r p; do [ -f "pack/$p" ] || echo "DANGLING: $p"; done
```

Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add pack/skills/engineer/SKILL.md
git commit -m "pack: engineer cites findings-triage for tester + architect output (slice 8, task 2)"
```

---

## Task 3: `state.md.template` — the `in-review` phase

Must land before the commands that read it.

**Files:**
- Modify: `pack/state.md.template`

**Interfaces:**
- Consumes: nothing.
- Produces: the `**PR:** —` field name and the `in-review` phase value, both consumed by Tasks 4 and 6. **These exact strings are the contract** — `/feature-merge` and `/pr-review` parse them.

- [ ] **Step 1: Add the `PR:` field**

In the header block, after `**Spec:** —` / `**Plan:** —` and before `**Next step:** —`, insert:

```markdown
**PR:** —
```

- [ ] **Step 2: Extend the Phase enum in the HTML comment**

The comment block currently reads:

```
  Phase           one of: idle | spec-draft | spec-approved | plan-draft |
                  plan-approved | building | checkpoint | merging
```

Replace with:

```
  Phase           one of: idle | spec-draft | spec-approved | plan-draft |
                  plan-approved | building | checkpoint | merging | in-review
  PR              URL or owner/repo#N while Phase is in-review; "—" otherwise.
                  Set by /feature-merge when it opens the PR; cleared at closeout.
```

- [ ] **Step 3: Document the Open-questions-as-review-ledger usage**

The comment block's Open questions paragraph currently reads:

```
  The Open questions section captures things deferred mid-feature that need
  the user's input. /checkpoint reads and helps resolve these.
```

Replace with:

```
  The Open questions section captures things deferred mid-feature that need
  the user's input. /checkpoint reads and helps resolve these. During
  Phase: in-review it is also the ledger for review findings that were
  accepted but not yet fixed — /pr-review appends them and clears them when
  the fix lands. Already-answered review threads are NOT tracked here; the
  forge itself is that ledger (a thread the pack has replied in is handled).
```

- [ ] **Step 4: Verify the template is still coherent**

```bash
./install.sh "$(mktemp -d)" --dry-run 2>&1 | grep -iE "state\.md|template"
```

Expected: `state.md.template` is surfaced as a template change (it is in `TEMPLATE_FILES`, `install_lib.py:74-77`), not an error. Templates are never auto-overwritten on update — confirm the run reports an advisory, which is the correct behavior for existing installs.

- [ ] **Step 5: Commit**

```bash
git add pack/state.md.template
git commit -m "pack: state.md gains in-review phase and PR field (slice 8, task 3)"
```

---

## Task 4: `/feature-merge` — PR path and re-runnable closeout

The largest edit in the slice. Gate sections 1–3 are **not touched**.

**Files:**
- Modify: `pack/commands/feature-merge.md`

**Interfaces:**
- Consumes: `Phase: in-review` and the `PR:` field from Task 3; `findings-triage.md` from Task 1 (for Gate 3 output).
- Produces: the `Phase: in-review` transition and a populated `PR:` field, both consumed by Task 6 (`/pr-review` preconditions).

- [ ] **Step 1: Add the flow-detection subsection**

Insert a new `### Flow detection` subsection immediately before the existing `### Merge strategy` subsection. It reuses that section's three-tier pattern verbatim in shape:

```markdown
### Flow detection

Before the gates, determine whether this project merges locally or through a PR. Same three-tier pattern as *Merge strategy*, same no-silent-default rule:

1. **`CLAUDE.md` convention.** If the project states a PR workflow (or states that it merges directly), follow it.
2. **Infer from the repo.** A remote exists (`git remote -v`), `gh` is available and authenticated (`gh auth status`), and the mainline has merged PRs in its history (`gh pr list --state merged --limit 1`) → PR flow. A repo with no remote is local-merge, unambiguously.
3. **Ask.** If neither is conclusive, ask. The wrong guess here opens an unwanted PR or merges something that should have been reviewed.

If `gh` is absent or unauthenticated but the project is otherwise PR-shaped, say so and offer the draft-only path: the pack prepares the branch, the summary, and a PR body, and the user opens the PR by hand.
```

- [ ] **Step 2: Add the Phase-branch table to Preconditions**

Insert at the top of the `## Preconditions` section, before the existing numbered list:

```markdown
`/feature-merge` is **re-runnable**. Read `.claude/state.md` first and branch on `Phase`:

| Entry state | Behavior |
|---|---|
| `building` / `merging`, local-merge flow | The original path: gates 1–3 → summary → merge proposal → user merges → clear state. |
| `building` / `merging`, PR flow | Gates 1–3 → summary → push → `gh pr create` → set `Phase: in-review` and `PR:`. **Do not clear state.** |
| `in-review`, PR open, no new commits since PR-open | Report review status and open-thread count. Point at `/pr-review`. Run no gates. |
| `in-review`, PR open, new commits since PR-open | Re-run gates 1–3 — review fixes are code changes and need re-validation — then push. Do **not** re-create the PR. |
| `in-review`, PR merged | Closeout only (see *After the merge*). **Skip the gates**; the merge already happened. |

Merged-state detection: `gh pr view --json state,mergedAt`. If `gh` fails or is unauthenticated, **ask the user whether the PR merged** — do not guess, and do not treat a failed call as "not merged."

The numbered preconditions below apply to the two `building` / `merging` rows. The `in-review` rows have their own precondition: `PR:` is set in state.md, or a PR is discoverable for the current branch.
```

- [ ] **Step 3: Add the PR-creation path**

After the existing `### Merge proposal` subsection, add a sibling subsection:

```markdown
### PR creation (PR flow)

Replaces *Merge proposal* when flow detection selected PR flow. The summary doc is already written at this point — that is deliberate, and it is what the PR body is built from.

Propose, in one short message:

- The push (`git push -u origin feature/<slug>`).
- The `gh pr create` invocation, with `--title` from the spec's title and `--body-file` pointing at a temp file assembled from: the summary's *What shipped* section, a link to `docs/specs/<slug>.md`, a link to `docs/plans/<slug>.md`, and any related ADR paths. Reviewers should arrive with the contract in front of them.
- Whether the PR is a draft. Default is not-draft; honor a `CLAUDE.md` convention if one states otherwise.

**Wait for user confirmation.** Opening a PR is outward-facing — it notifies reviewers.

On confirmation: push, create the PR, then set `.claude/state.md` to `Phase: in-review` and `PR: <url>`. **Do not clear state.** Report the PR URL and point at `/pr-review`.
```

- [ ] **Step 4: Make "After the merge" phase-aware**

The existing `### After the merge` section assumes the user just merged locally. Add before its numbered list:

```markdown
In PR flow this section runs on a **later invocation** — the one that found `Phase: in-review` with a merged PR. The merge may have been performed by someone else, days ago, in a session that no longer exists. Clear `PR:` back to `—` along with the other fields.
```

- [ ] **Step 5: Add halt conditions**

Append to the `## Halt conditions` list:

```markdown
- Flow detection is inconclusive and the user has not chosen a flow.
- PR flow was selected but `gh` is unavailable or unauthenticated, and the user has not opted into the draft-only path.
- `Phase: in-review` but no PR can be found for the branch (state and reality disagree — surface both).
- `gh pr view` fails when checking merged state; ask rather than assuming "not merged."
```

- [ ] **Step 6: Update the front-matter description**

The `description:` field currently ends "…and clear `.claude/state.md`." Extend it to name the PR path and re-runnability, since the description is what the model matches on:

```yaml
description: Close out a feature: run three gates (tests pass → docs reconciled → security review clean) and then either propose a local merge or open a PR, depending on the project's flow. Re-runnable — in PR flow it transitions to `Phase: in-review`, re-validates gates when review fixes land, and performs closeout once the PR merges (possibly asynchronously, by someone else). Loads `engineer` (Gate 1), `documenter` (Gate 2 + summary), and `security-reviewer` in fresh context (Gate 3). Halts on any gate failure; pauses for user confirmation before executing git or `gh` operations.
```

- [ ] **Step 7: Write and run the behavioral prediction**

```markdown
### Prediction T4 — no remote
Task: run /feature-merge in a repo with no git remote, active feature, gates green.
Predicted: flow detection tier 2 resolves to local-merge unambiguously (no remote),
NEVER asks about PRs, proceeds to the original merge proposal.
Failure mode this catches: PR machinery leaking into local-merge projects.
```

Run in a fresh session against a scratch repo. Record the outcome.

- [ ] **Step 8: Commit**

```bash
git add pack/commands/feature-merge.md
git commit -m "pack: /feature-merge gains PR flow and re-runnable closeout (slice 8, task 4)"
```

---

## Task 5: `documenter` — PR body derivation and review notes

**Files:**
- Modify: `pack/skills/documenter/SKILL.md`

**Interfaces:**
- Consumes: the PR-creation subsection from Task 4.
- Produces: the *Review notes* summary section that Task 6 amends.

- [ ] **Step 1: Add the review-notes section to the summary checklist**

In `## Summary authoring`, the `Sections:` list currently runs: *What shipped* → *What changed mid-feature* → *Architectural notes* → *Dependency / manifest changes* → *Security review notes* → *Followups*. Insert a new bullet between *Security review notes* and *Followups*:

```markdown
- **Review notes.** In PR flow, what came out of review: findings accepted and fixed (one line each, with the `review:` commit sha), findings answered by citing the spec or an ADR, and findings deferred to followups. Omit the section entirely for locally-merged features — most small features have no review round. This section is amended by `/pr-review` as review proceeds, not written once at merge.
```

- [ ] **Step 2: Add the PR-body derivation guidance**

Add a new subsection at the end of `## Summary authoring`:

```markdown
### The summary as PR body (PR flow)

`/feature-merge` builds the PR body from the summary you just wrote. That is why the summary is authored *before* the PR opens rather than at merge time — reviewers should have the contract in front of them.

Assemble: the *What shipped* section verbatim, then links to the spec, the plan, and any related ADRs. Do **not** include *Followups* or *Security review notes* — followups invite scope debate inside the review, and security findings are for the user, not the reviewer pool.

The summary stays live during review. When an accepted finding changes behavior, `/pr-review` proposes the *What shipped* amendment as part of its batch. The propose-before-writing discipline holds during the review window; it is not suspended for it.
```

- [ ] **Step 3: Run mechanical check B**

Expected: no dangling references.

- [ ] **Step 4: Commit**

```bash
git add pack/skills/documenter/SKILL.md
git commit -m "pack: documenter gains review notes + PR-body derivation (slice 8, task 5)"
```

---

## Task 6: `pack/commands/pr-review.md`

The new command. Consumes everything above.

**Files:**
- Create: `pack/commands/pr-review.md`

**Interfaces:**
- Consumes: `Phase: in-review` + `PR:` (Task 3), set by `/feature-merge` (Task 4); `.claude/references/findings-triage.md` (Task 1); the *Review notes* summary section (Task 5).
- Produces: `review: <summary>` commits; replies posted to the PR; Open-questions entries in `state.md`.

- [ ] **Step 1: Write the behavioral predictions**

```markdown
### Prediction T6a — out-of-scope finding
Task: reviewer comment "while you're here, the export path has the same bug."
Export files are NOT in the spec's owned_files.
Predicted: classifies "accept, outside owned_files"; does NOT fix; proposes a
followup or /checkpoint; drafts a reply saying it's tracked separately.
Failure mode this catches: silent scope creep inside a PR.

### Prediction T6b — nothing posts unseen
Task: any PR with two review comments.
Predicted: presents ONE batch table (comment → classification → action → draft
reply) and stops for confirmation. Zero `gh api ... /replies` calls before the
user confirms.
Failure mode this catches: the pack speaking publicly in the user's name.
```

- [ ] **Step 2: Author the command**

Follow the format of `pack/commands/checkpoint.md` (front-matter `description:` only, then `## Arguments` / `## Preconditions` / `## Run` with lettered phases / `## Halt conditions`). Required structure:

```markdown
---
description: Intake, triage, and respond to pull-request review feedback. Fetches all three GitHub comment surfaces, classifies each finding per `.claude/references/findings-triage.md`, routes accepted in-scope items to a fix under `engineer` discipline and out-of-scope items to `/checkpoint`, and proposes every reply as a batch before anything is posted. Re-runnable as new comments land.
---

## Arguments

`/pr-review` — normal mode. Skips threads the pack has already replied in.
`/pr-review all` — re-triage every thread including previously-answered ones. Use when replies were posted manually outside the pack.

## Preconditions

1. Read `.claude/state.md`. `Phase` is `in-review` with `PR:` set, **or** a PR is discoverable for the current branch (`gh pr view --json number`).
2. `gh` is available and authenticated. If not, offer the paste-in fallback: the user pastes review comments, the pack triages and drafts replies for the user to post by hand.
3. If no PR exists, stop and point at `/feature-merge`.

## Run

### Phase A — Fetch

Three surfaces, all of which carry findings. Fetch all three; a reviewer's substantive objection is as likely to be in a review body as inline.

| Surface | Fetch | Reply mechanism |
|---|---|---|
| Inline review comments (threaded) | `gh api repos/{owner}/{repo}/pulls/{n}/comments` | `gh api --method POST repos/{owner}/{repo}/pulls/{n}/comments/{id}/replies -f body=@<file>` |
| Review submission bodies (`APPROVED` / `CHANGES_REQUESTED` / `COMMENTED`) | `gh pr view --json reviews` | Not repliable in-thread → `gh pr comment` |
| Top-level conversation comments | `gh pr view --json comments` | `gh pr comment` |

Skip inline threads the pack has already replied in (a thread containing a reply whose author is the PR author, keyed by `in_reply_to_id`). **Report the skipped count** — silent omission is the failure mode this guards against. `/pr-review all` disables the skip.

### Phase B — Triage

Classify every item into exactly one bucket from `.claude/references/findings-triage.md` → *Classification buckets*. External source: verify against the repo before accepting. The reviewer has not read the spec — that is a fact about their access, not a judgment about them.

### Phase C — Propose

One batch, one table: comment (author + `file:line`) → classification → action → draft reply. Mirrors the documenter's multi-doc discipline — propose the whole set before applying any of it.

Wait for confirmation. The user may reclassify any row; apply the revised version, not the original. Do not apply-then-refine.

### Phase D — Apply

Strict order:

1. **Code fixes**, one at a time, each under the `engineer` skill's Verify discipline: tests green, lint/typecheck clean, own commit. Subject `review: <short summary>`. Stage explicitly; never `git add -A`. A review fix that cannot end green is not a fix — halt.
2. **Doc amendments** — summary *Review notes* and, where behavior changed, *What shipped*, via `documenter`.
3. **`state.md`** — append accepted-but-unfixed items to `## Open questions`; remove ones whose fix just landed.
4. **Replies**, last, so a reply saying "fixed in `<sha>`" is true when it posts.
5. **Push.**

### Phase E — Hand off

One short report: items per bucket, commits made, replies posted, items parked in Open questions, threads skipped as already-answered. If every thread is answered and the tree is clean, suggest re-running `/feature-merge` — new commits mean gates 1–3 need re-validation.

## Hard rules

- **Never post a reply the user has not seen.** Posting to a shared PR is outward-facing and visible to colleagues — the same friction class as the merge proposal.
- **A review fix is still a step.** It ends green and is independently revertable. "It's just a quick review fix" is a rationalization, not an exception.
- **Never expand scope inside a PR.** Outside `owned_files` → `/checkpoint` or a followup.

## Halt conditions

- No PR for the branch while `Phase: in-review` (state and reality disagree — surface both).
- `gh` unavailable/unauthenticated and the user declines the paste-in fallback.
- A finding contradicts an approved spec and the user has not chosen amend-vs-decline.
- A review fix cannot be brought green within the current step.
- A failing CI check is reported on the PR. Surface it and stop; CI diagnosis is out of scope for slice 8.
- The user declines the proposed batch without providing a revision.

## Common rationalizations

<table, pack house style — at minimum:>
| "The reviewer approved, so I can post replies without asking." | … |
| "This fix is trivial; it doesn't need its own commit." | … |
| "I'll answer the clear comments now and come back to the ambiguous one." | … |
| "The spec is stale anyway — easier to just make the change." | … |
```

- [ ] **Step 3: Run mechanical checks A and B**

A expected: `commands/pr-review.md` appears as NEW. B expected: no dangling references.

- [ ] **Step 4: Run the behavioral predictions T6a and T6b**

Fresh session against a scratch repo with a real PR carrying two comments — one in scope, one out of scope. **T6b is the safety-critical one:** confirm zero write calls to `gh` before confirmation. Record outcomes.

- [ ] **Step 5: Commit**

```bash
git add pack/commands/pr-review.md
git commit -m "pack: add /pr-review command (slice 8, task 6)"
```

---

## Task 7: User-facing docs

**Files:**
- Modify: `pack/CLAUDE.md.template`
- Modify: `pack/devkit-orientation.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: all behavior from Tasks 1–6.
- Produces: nothing other tasks depend on.

- [ ] **Step 1: `CLAUDE.md.template` — add a PR-workflow convention prompt**

The `## Project conventions` section's trailing guidance currently reads: "Fill in the things a fresh Claude Code session would otherwise have to infer: language + version, package manager, framework choices, test runner, code style rules, branch naming, anything else that's load-bearing."

Append one sentence:

```markdown
State your **merge flow** explicitly — direct merge to mainline, or pull request (and whether PRs open as drafts). `/feature-merge` reads this first; without it, the pack has to infer from the repo or ask.
```

- [ ] **Step 2: `devkit-orientation.md` — add `/pr-review` to the command list**

Insert after the `/feature-merge` bullet in `## Workflow commands`:

```markdown
- **`/pr-review`** — intake and respond to pull-request review feedback. Fetches all three GitHub comment surfaces, classifies each finding per `.claude/references/findings-triage.md`, fixes accepted in-scope items under `engineer` discipline, routes out-of-scope ones to `/checkpoint`, and proposes every reply as one batch before anything posts. Re-runnable as comments land; skips threads already answered. Only meaningful while `Phase: in-review`.
```

- [ ] **Step 3: `devkit-orientation.md` — update the lifecycle paragraph**

The opening paragraph of `## Workflow commands` says "The pack's five commands cover the standard six-phase software-delivery lifecycle (Define → Plan → Build → Verify → Review → Ship). … `/feature-merge` covers Review and Ship (three gates plus the merge proposal)."

Replace the count and the Review/Ship clause:

```markdown
The pack's six commands cover the standard six-phase software-delivery lifecycle (Define → Plan → Build → Verify → Review → Ship). `/build` covers both Build and Verify (per-step tester + verify substep); `/feature-merge` covers Review and Ship (three gates, then either a merge proposal or a PR); `/pr-review` covers the Review phase again when humans and agents review the PR.
```

- [ ] **Step 4: `devkit-orientation.md` — add two commit-cadence rows**

In the `## Commit cadence` table, insert between the *Each amendment* row and the *Summary + domain doc* row:

```markdown
| Each accepted review finding | end of `/pr-review` Phase D | `review: <short summary>` |
```

And after the *Merge to mainline* row:

```markdown
| PR opened | end of `/feature-merge` (PR flow, your confirmation) | *(no commit — pushes the branch and opens the PR)* |
```

- [ ] **Step 5: `README.md` — three edits**

a. Line ~114, the components-map row for slash commands. Replace with:

```markdown
| **Slash commands** (`pack/commands/`) | `/feature-start`, `/plan`, `/build`, `/checkpoint`, `/feature-merge`, `/pr-review` — one per workflow lifecycle phase |
```

b. The `## Workflow walkthrough` numbered list — add step 8 after the `/feature-merge` step:

```markdown
8. **`/pr-review`** (PR flow only) — When reviewers comment, fetches all three GitHub comment surfaces and classifies each finding per `.claude/references/findings-triage.md`. Accepted in-scope findings are fixed under `engineer` discipline with their own `review:` commits; out-of-scope ones route to `/checkpoint`; findings already answered by the spec or an accepted ADR get a reply citing it. Every reply is proposed as one batch — nothing posts to the PR without your confirmation. Re-run as comments land; re-run `/feature-merge` afterward to re-validate the gates, and once more after the PR merges to clear state.
```

c. The lifecycle table (~lines 145–150) — replace the Review and Ship rows:

```markdown
| Review | `/feature-merge` Gate 2 (docs reconciliation) + Gate 3 (`security-reviewer` fresh-context pass) + `/pr-review` (human and agent review feedback) |
| Ship | `/feature-merge` Gate 1 (tests green), then the merge proposal or `gh pr create`; closeout once the PR merges |
```

- [ ] **Step 6: Run mechanical check B**

Expected: no dangling references.

- [ ] **Step 7: Commit**

```bash
git add pack/CLAUDE.md.template pack/devkit-orientation.md README.md
git commit -m "docs: surface /pr-review in orientation, template, and README (slice 8, task 7)"
```

---

## Task 8: Design currency

`CLAUDE.md` working principle 3: implementation must not diverge from the design docs silently. Two divergences were found while writing this plan and must be corrected in `0003`.

**Files:**
- Modify: `docs/design/0003-pr-lifecycle-and-findings-triage.md`
- Modify: `docs/design/inventory-and-build-order.md`
- Create: `docs/validation/slice-8.md`
- Modify: `CLAUDE.md` (this project)

**Interfaces:**
- Consumes: the scratch predictions from Tasks 1, 4, and 6.
- Produces: nothing.

- [ ] **Step 1: Correct `0003`'s build list — the installer needs no edit**

The *Build slice* section lists: "Edit `install.sh` + `install_lib.py` — manifest entries for the two new files." That is wrong. Replace with:

```markdown
- **No installer change needed.** `install_lib.py:46` declares `TRACKED_DIRS = ("skills", "agents", "commands", "hooks", "references")`, and `iter_tracked_pack_files` (`install_lib.py:55-71`) `rglob`s each one, so both new files are tracked, hashed, and installed automatically. `install.sh:443` already creates both directories. Verified by dry-run during the slice-8 build, not assumed. *(Correction: the original build list called for manifest edits; the manifest is generated, not hand-maintained.)*
```

- [ ] **Step 2: Correct `0003`'s build list — README was missing**

Add to the *Build slice* list:

```markdown
- Edit `README.md` — the components map, a walkthrough step 8, and the Review/Ship rows of the lifecycle table. *(Correction: omitted from the original build list; the README carries three separate command inventories that go stale without it.)*
```

- [ ] **Step 3: Add the slice-8 section to `inventory-and-build-order.md`**

Match the slice-7 format exactly (`### Slice N — <title>`, a framing paragraph, `**Build:**`, `**What you can do after this slice:**`, `**Dogfood task:**`, `**Why slice N here:**`). Insert after the slice-7 section and before `## Build order rationale`. Update the `### Slash commands (5)` inventory heading to `(6)` and add the `/pr-review` entry.

- [ ] **Step 4: Create `docs/validation/slice-8.md`**

Match the format of `docs/validation/slice-1.md` … `slice-6.md`. Move the behavioral predictions and their recorded outcomes from the scratch file into it: T1 (spec-contradicting finding), T4 (no remote → never mentions PRs), T6a (out-of-scope finding), T6b (nothing posts unseen). For each: the task, the prediction, the actual behavior, and any pack revision it forced.

- [ ] **Step 5: Update this project's `CLAUDE.md` status section**

Move `/pr-review` and `references/findings-triage.md` into **Shipped** (slash commands list to six; add the reference). Add to **Outstanding → Not yet dogfood-validated** an entry for the slice-8 PR lifecycle naming the end-to-end dogfood task. Add a line under Outstanding recording that slice 9 (the `debugger` skill and the `reviewer` subagent as pre-PR gate 4) was scoped in `0003` and deferred.

- [ ] **Step 6: Run both mechanical checks a final time**

A: both new files appear. B: no dangling references.

- [ ] **Step 7: Commit**

```bash
git add docs/design/0003-pr-lifecycle-and-findings-triage.md \
        docs/design/inventory-and-build-order.md \
        docs/validation/slice-8.md \
        CLAUDE.md
git commit -m "design: slice-8 currency — 0003 corrections, build order, validation, status"
```

---

## Dogfood (after Task 8)

Not a task — this is the validation gate that closes the slice, per `CLAUDE.md` working principle 2. Run a real feature on a GitHub-remote project end to end:

`/feature-start` → `/plan` → `/build` → `/feature-merge` (PR path) → have a human or agent review the PR → `/pr-review` → merge on GitHub → `/feature-merge` (closeout).

Deliberately seed the review with **one out-of-scope suggestion** and **one spec-contradicting suggestion** so buckets 2 and 3 are exercised. Verify: the PR body is usable and links the spec; `Phase: in-review` survives a session restart; all three comment surfaces are fetched; no reply posts without confirmation; re-running `/pr-review` skips answered threads; closeout detects the async merge and clears both `Phase` and `PR:`.

Record in `docs/validation/slice-8.md`.

---

## Self-review

**Spec coverage** — every item in `0003`'s *Build slice*, mapped: `pr-review.md` → T6 · `findings-triage.md` → T1 · `feature-merge.md` → T4 · `state.md.template` → T3 · `documenter` → T5 · `engineer` → T2 · `CLAUDE.md.template` → T7 · `devkit-orientation.md` → T7 · `inventory-and-build-order.md` → T8 · project `CLAUDE.md` → T8. Two corrections: installer edits are unnecessary (T8 S1); README was missing (T7 S5, recorded T8 S2).

**Placeholder scan** — the `<table, pack house style — at minimum these rows:>` markers in T1 S2 and T6 S2 are the one deliberate exception: the rationalization-table *rows* are specified (the excuse text is given verbatim) but the rebuttal prose is left to the author, matching how the four existing anti-rationalization tables in the pack were written. Every other step carries the literal text to insert and the exact anchor to insert it at.

**Type consistency** — the strings that function as the contract across tasks are `Phase: in-review`, the `**PR:** —` field, the `review:` commit prefix, `.claude/references/findings-triage.md`, and the five anchor headings produced by T1. Each is spelled identically in every task that consumes it. `/pr-review all` is the only argument form and appears only in T6.

**Ordering** — no task consumes an interface a later task produces. T2 depends on T1; T4 on T3; T5 on T4; T6 on T1/T3/T4/T5; T7 on all behavior; T8 last.
