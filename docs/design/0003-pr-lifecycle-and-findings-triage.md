# ADR-0003: PR Lifecycle and Findings Triage

**Status:** Proposed
**Date:** 2026-07-30
**Deciders:** [user], Claude (design partner)

---

## Context

The pack's feature lifecycle ends at a **local merge performed synchronously by the user**. That assumption is load-bearing in `/feature-merge` and in `state.md`, and it does not match a pull-request workflow where other people and agents review the branch.

The evidence is unambiguous. `gh` / "pull request" appear exactly twice in the entire pack, and both are *escape hatches*:

- `pack/commands/feature-merge.md:86` — merge-strategy determination mentions "a PR-tool workflow like `gh pr create`" as a convention to follow.
- `pack/commands/feature-merge.md:121` — halt conditions: *"The user rejects the proposed merge mechanics (e.g., the project uses a tool — `gh pr create`, `bors`, `mergify` — instead of direct `git merge`)."*

So in a PR flow the pack runs its three gates and then **stops at a designed halt condition and hands off.** Everything after that point — opening the PR, receiving review, responding, landing the merge, closing out state — happens outside the pack's discipline.

`state.md` confirms the same assumption independently:

- `Phase` enumerates `idle | spec-draft | spec-approved | plan-draft | plan-approved | building | checkpoint | merging`. There is no post-PR phase.
- There is no field for a PR reference.
- `/feature-merge` **clears state.md** in its "After the merge" step, on the assumption that merge is a single act the user just performed.

In a PR flow the feature stays alive after the gates pass. Review runs over hours or days. The merge may be executed on GitHub, by someone else, long after the session that produced the branch has ended.

Three consequences compound:

1. **The lifecycle terminates one step early.** `/feature-merge` is described as "one `/feature-merge` invocation completes a feature lifecycle" — in a PR flow it completes roughly two-thirds of one.
2. **External review findings have no intake path.** They are handled ad hoc, outside the pack, which is exactly where the failure modes the pack exists to prevent reappear: silent scope creep in response to a reviewer's suggestion, un-triaged findings, and code changes that never touch the spec they contradict.
3. **The pack specifies the *producer* side of findings exhaustively and the *consumer* side not at all.** `security-reviewer` has severity criteria and a six-row anti-rationalization table; `tester` has a contract for returning findings instead of tests; `architect` produces recommendations. Nothing anywhere says what the main thread does with a finding it believes is wrong. `security-reviewer.md:109` even instructs *"Re-litigating accepted ADRs as findings is noise. Cite the ADR and move on"* — presuming a triage discipline that is written down nowhere.

### How this surfaced

This design emerged from evaluating whether the pack should depend on **Obra Superpowers** at runtime (compose where available, fall back to inline instructions where not). That evaluation was **rejected** — see *Alternatives considered* — but it identified three genuine gaps: debugging discipline, correctness review, and findings triage. Findings triage turned out to be entangled with the PR-lifecycle gap above, because the dominant source of findings in this workflow is external reviewers. The other two gaps are deferred to slice 9.

Superpowers' `receiving-code-review` skill is the closest prior art for the triage half, particularly its source-specific handling (trusted partner vs. external reviewer) and its thread-reply mechanics. Its structure is borrowed; its content is not, because roughly half of it addresses human-reviewer social dynamics rather than the contract-conformance questions this pack cares about.

## Decision

Extend the lifecycle through PR review with **two new pack files and edits to the state machine**. No new skill and no new subagent: this is orchestration of primitives the pack already has.

| New | Purpose |
|---|---|
| `pack/commands/pr-review.md` | Fetch, triage, remediate, and respond to PR review feedback |
| `pack/references/findings-triage.md` | The shared discipline for evaluating *any* finding, internal or external |

GitHub is first-class (`gh` is the assumed tool). Other forges degrade to a draft-only path where the pack triages and drafts replies for the user to post by hand.

The local-merge flow remains fully supported. `/feature-merge` determines which flow applies using the **same three-tier pattern already in its *Merge strategy* section**: `CLAUDE.md` convention → infer from the repo (remote present, `gh` available, existing PR history) → ask. No silent default.

### The state-machine change

```
Phase:  … building → merging → idle
becomes
Phase:  … building → merging → in-review → idle
                                   ↑           ↑
                        PR open; state    PR merged, possibly
                        must SURVIVE      asynchronously by
                        the session       someone else
```

`state.md.template` changes:

- `Phase` gains `in-review`.
- A new top field: `**PR:** —` (URL or `owner/repo#N` when a PR is open).
- The existing `## Open questions` section becomes the ledger for **accepted-but-not-yet-fixed** review findings. No new state mechanism is introduced; Open questions already exists for "we know about this; it isn't resolved yet."

### `/feature-merge` becomes re-runnable

Rather than adding a sixth command for the closeout transition, `/feature-merge` branches on `Phase` at the top and stays the single owner of feature closeout.

| Entry state | Behavior |
|---|---|
| `building` / `merging`, **local-merge flow** | Unchanged from today: gates 1–3 → summary → merge proposal → user merges → clear state. |
| `building` / `merging`, **PR flow** | Gates 1–3 → summary → push branch → `gh pr create` → set `Phase: in-review` and `PR:`. **Does not clear state.** |
| `in-review`, PR open, no new commits since PR-open | Report review status (`reviewDecision`, open thread count). Point at `/pr-review`. No gates. |
| `in-review`, PR open, new commits since PR-open | Re-run gates 1–3 — review fixes are code changes and need re-validation — then push. Do **not** re-create the PR. |
| `in-review`, PR merged | Closeout only: clear state to idle, record `Last merge:`, propose branch cleanup. **Skip the gates** — the merge already happened; re-running them proves nothing. |

Merged-state detection is `gh pr view --json state,mergedAt`. If `gh` is unavailable or unauthenticated at closeout time, fall back to asking the user whether the PR merged rather than guessing.

**The PR body derives from artifacts that already exist.** The summary doc is authored before the PR opens (this is already the gate order today), so `gh pr create --body-file` can use it directly, with links to the spec and any related ADRs. Reviewers arrive with the contract in front of them — which is what makes the triage rule "an external reviewer hasn't read your spec" a statement about *access*, not a dismissal.

### `/pr-review` — command shape

`/pr-review` takes no arguments in the normal case. It is **re-runnable** as new comments land; that is its primary mode, unlike the once-per-feature commands.

**Preconditions.** `Phase: in-review` with `PR:` set, or a PR discoverable for the current branch via `gh pr view --json number`. If no PR exists, stop and point at `/feature-merge`.

**Phase A — Fetch.** Three comment surfaces, all of which carry findings:

| Surface | Fetch | Reply |
|---|---|---|
| Inline review comments (threaded) | `gh api repos/{owner}/{repo}/pulls/{n}/comments` | `POST …/pulls/{n}/comments/{id}/replies` |
| Review submission bodies (`APPROVED` / `CHANGES_REQUESTED` / `COMMENTED`) | `gh pr view --json reviews` | Not repliable in-thread → `gh pr comment` |
| Top-level PR conversation comments | `gh pr view --json comments` | `gh pr comment` |

Skip inline threads the pack has already replied in (detected via `in_reply_to_id`). Report the skipped count so silent omission is visible.

**Phase B — Triage.** Each item is classified per `references/findings-triage.md` into exactly one of five buckets:

| Classification | Action |
|---|---|
| Accept, in scope | Fix now under the `engineer` skill's Verify discipline. Own commit, subject `review: <summary>`. |
| Accept, **outside the spec's `owned_files`** | Route to `/checkpoint` (amendment) or record as a followup in the summary. Never silent scope expansion inside a PR. |
| Already answered by the spec or an accepted ADR | Reply citing it. No code change. |
| Technically disagree | Draft a reply with technical reasoning. Surface to the user before posting — pushback is legitimate but it is the user's call to make publicly. |
| Unclear | Ask in-thread, and **implement nothing else in that cluster** until answered. Related items with partial understanding produce the wrong implementation. |

**Phase C — Propose.** One batch, as a single table: comment → classification → action → draft reply. This mirrors the `documenter` skill's multi-doc merge-time discipline (propose the whole set before writing any of it). Wait for confirmation. The user may reclassify any row.

**Phase D — Apply.** In order: land code fixes as commits (staged explicitly, never `git add -A`), then post replies, then push. Fixes before replies, so a reply that says "fixed in `<sha>`" is true when it posts.

**Phase E — Hand off.** One short report: items triaged by bucket, commits made, replies posted, items parked in Open questions. If every thread is answered and the working tree is clean, suggest re-running `/feature-merge` to re-validate the gates against the new commits.

**Two hard rules.**

1. **Never post a reply the user has not seen.** Posting to a shared PR is outward-facing and visible to colleagues — the same friction class as the merge proposal, and the same propose-before-acting discipline the whole pack uses.
2. **A review fix is still a step.** It ends in a green suite and is independently revertable. *"It's just a quick review fix"* is an anti-rationalization row, not an exception to the engineer skill.

### `references/findings-triage.md`

One shared evaluation loop, two sources. The source distinction is the substance of the reference:

| | **Internal** (`tester`, `architect`, `security-reviewer`) | **External** (humans, review agents) |
|---|---|---|
| Has read the spec | Yes — it is passed in | **No** |
| Structure | Severity-bucketed, predictable shape | Free-form prose |
| Default posture | Trust the finding; evaluate the severity | Verify against the repo before implementing |
| Blind spot | No conversation context | No spec, no ADR history, no `owned_files` |

**The shared loop:** read the item completely → restate the technical claim in one sentence → verify against the repo **and** the spec → classify → respond → implement one at a time, each ending green.

**Five devkit-specific rules** that generic review-response guidance has no analogue for:

1. **A finding that contradicts an approved spec is a spec question, not a code fix.** Route to `/checkpoint`, do not quietly change the code.
2. **A finding that re-opens an accepted ADR is answered by citing the ADR back.** If the threat model or context has genuinely changed since, that is a *different* finding and must be named as one. (`security-reviewer.md:109` already assumes this rule exists.)
3. **A finding requiring work outside the spec's `owned_files` becomes a `/checkpoint` amendment or a followup** — never silent scope expansion.
4. **Never implement a finding that breaks the current step's revertability.** Split it into its own step.
5. **Clarify every unclear item in a cluster before implementing any of it.** Partial understanding of related items produces the wrong implementation.

**Consumers:** `engineer` (tester findings, architect recommendations), `/build` (halt conditions), `/feature-merge` (security-reviewer findings), `/pr-review` (external findings), and — once slice 9 lands — the `reviewer` subagent's output.

### The four forks, resolved

**Decision 1 — `/feature-merge` becomes re-runnable rather than adding `/feature-close`.** A sixth command for what is fundamentally a state transition is ceremony the pack rejects elsewhere. Closeout logic stays in one place, and the branch is a four-row table at the top of an otherwise unchanged command. Cost: `/feature-merge` grows; accepted, because splitting it would mean two commands that must agree about state.

**Decision 2 — the forge is the triage ledger.** An inline comment is "handled" when the pack has posted a reply in its thread. That survives session boundaries, context compaction, and machine changes with zero pack-side bookkeeping. Only *accepted-but-unfixed* findings need local tracking, and `## Open questions` in `state.md` already exists for that. Known cost: if the user replies to a thread manually, `/pr-review` treats it as handled. Mitigated by reporting the skipped-thread count on every run and supporting a re-triage-everything invocation.

**Decision 3 — the summary doc is authored pre-PR and amended during review.** It feeds the PR body, which is its highest-leverage use. When an accepted finding changes behavior, `/pr-review` proposes the summary amendment as part of its Phase C batch. This is the pack's existing doc-currency discipline applied to the review window rather than suspended for it.

**Decision 4 — the pack drafts and posts, but never posts unseen.** Draft-only would be safe but would leave the most error-prone step (writing a technically correct public reply) entirely manual. Auto-posting would put unreviewed text under the user's name in front of colleagues. Propose-then-post with explicit confirmation is the same trade the merge proposal already makes.

## Alternatives considered

**Runtime dependency on Obra Superpowers (compose where present, fall back where absent).** Rejected. Superpowers installs as a **user-level plugin** (`~/.claude/plugins/`); the devkit pack installs **project-level** (`.claude/`). A soft dependency means the same repository behaves differently on different machines — `/build` enforcing one discipline for the author and another for a teammate. That directly undercuts the pack's central claim, which `comparison-table.md` states as structural enforcement rather than encouraged discipline. Borrowing structure at authoring time carries none of this cost.

**Extend `/checkpoint` to handle review intake.** Rejected. `/checkpoint` means "I learned something mid-feature and the docs need to catch up." Review intake has different preconditions (`Phase: in-review`, a PR must exist), a different cadence (re-runnable N times), and a side effect no other pack command has (writing to an external service). Conflating them would make `/checkpoint`'s preconditions conditional on a mode flag. `/pr-review` *routes to* `/checkpoint` for out-of-scope findings, which is the right relationship.

**Extend `/feature-merge` with a post-PR review phase.** Rejected. It is already the longest command in the pack, and the cadences differ: merge closeout happens once, review intake happens as many times as reviewers comment.

**A `pr-reviewer` subagent that intakes and replies.** Rejected on two grounds. First, fresh context is *actively wrong* for evaluating an external critique — answering "this is a race condition" with "ADR-0007 accepted that trade-off, and here is why" requires exactly the spec and ADR history a fresh-context subagent lacks. Second, posting outward-facing content is a propose-before-acting responsibility that belongs on the main thread, consistent with every other irreversible action in the pack. A narrow subagent invocation to *verify one contested claim* without authorship bias remains available and is a good use; it is not the same thing as owning intake.

**Forge-agnostic, draft-only (user pastes comments in, pastes replies out).** Rejected as the design center. `gh` 2.86 is installed and the remote is GitHub, so the manual path is a fallback for other forges rather than the primary shape. Building for the lowest common denominator would cost the automatic fetch and the reply-as-ledger mechanic in Decision 2.

## Consequences

**Positive:**

- The lifecycle covers the actual workflow end to end. `/feature-merge` stops halting by design on the user's normal path.
- External findings receive the same triage discipline internal findings do — and internal findings finally get a consumer-side discipline at all, closing a gap `security-reviewer` already presumed was closed.
- The PR body is derived from artifacts the pack already produces. The spec/summary discipline pays a dividend it was not designed for.
- Gates run *before* the PR opens, so human reviewer attention is spent on what machines cannot catch.
- Slice 9 (`debugger` skill, `reviewer` subagent as pre-PR gate 4) slots into this structure without rework: gate 4 is another gate, and the reviewer's findings are another `findings-triage.md` consumer.

**Negative / risks:**

- **`/feature-merge` grows.** Mitigated by keeping the Phase branch as a table at the top and leaving the gate sections untouched.
- **Reply-as-ledger breaks on manual replies.** Mitigated per Decision 2 (report skipped count; support re-triage).
- **Async merge detection depends on `gh` auth at closeout time.** Mitigated by falling back to asking the user rather than guessing.
- **Scope creep into "the pack manages your PRs."** Labels, reviewer assignment, CI babysitting, and merge-queue interaction are explicitly out of scope. `/pr-review` handles review *findings*, nothing else.
- **A bad auto-reply is publicly visible.** Mitigated by hard rule 1 — nothing posts unseen.

**Open questions:**

- Should `/pr-review` handle **failing CI checks** reported on the PR, or is that the `debugger`'s job? Leaning: surface the failing check and route to `debugger` once slice 9 exists; until then, halt and report.
- Does a `CHANGES_REQUESTED` review state block a `/feature-merge` re-run? Leaning: no — gates measure code health, review state measures human approval. Report both; let the user decide.
- Should review-fix commits use a distinct `review:` subject prefix or continue the `step N:` numbering? Leaning: `review:` — they are not plan steps and should not be mistaken for them in the log.
- Should `/feature-merge` create **draft** PRs by default? Leaning: no, but honor a `CLAUDE.md` convention if one is stated.
- Whether `/pr-review` should offer to resolve GitHub review threads (GraphQL `resolveReviewThread`) after a reply lands. Leaning: no in slice 8 — resolving is a reviewer's prerogative, not the author's. Revisit in dogfood.

## Build slice

This is **slice 8**. It precedes the debugging/correctness work (slice 9) because the PR halt is on the daily path, and because findings triage is required for external review regardless of whether the internal `reviewer` subagent exists.

**Build:**

- `pack/commands/pr-review.md` — the command (Phases A–E above).
- `pack/references/findings-triage.md` — the shared discipline, both sources.
- Edit `pack/commands/feature-merge.md` — PR-flow detection, the Phase branch table, `gh pr create` path, PR-body-from-summary, re-runnable closeout.
- Edit `pack/state.md.template` — `Phase: in-review`, `PR:` field, Open-questions usage note.
- Edit `pack/skills/documenter/SKILL.md` — summary gains review-notes; PR-body derivation guidance.
- Edit `pack/skills/engineer/SKILL.md` — cite `findings-triage.md` for tester findings and architect recommendations.
- Edit `pack/CLAUDE.md.template` — a PR-workflow convention line alongside merge strategy.
- Edit `install.sh` + `install_lib.py` — manifest entries for the two new files.
- Edit `pack/devkit-orientation.md` — `/pr-review` in the command list; Review/Ship lifecycle mapping.
- Follow-up doc edits (design-currency): slice-8 section in `docs/design/inventory-and-build-order.md`; status update in this project's `CLAUDE.md`.

**Dogfood task:** Run a real feature on a GitHub-remote project through `/feature-start` → `/plan` → `/build` → `/feature-merge` (PR path) → have a human or agent review the PR → `/pr-review` → merge on GitHub → `/feature-merge` (closeout). Verify: the PR body is usable and links the spec; `Phase: in-review` survives a session restart; all three comment surfaces are fetched; each of the five triage buckets is exercised at least once across the run (deliberately leave one out-of-scope suggestion and one spec-contradicting suggestion in the review); no reply posts without confirmation; re-running `/pr-review` skips already-answered threads; closeout detects the async merge and clears state correctly.

**Deferred to slice 9:** the `debugger` skill and the `reviewer` subagent as pre-PR gate 4. Both were scoped during this design discussion; neither is required for the PR lifecycle to work.
