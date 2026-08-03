---
description: Begin a feature — brainstorm with the user, propose a domain decomposition, draft a typical-depth spec, create the feature branch, and update `.claude/state.md`. Loads the `pm` skill; invokes the `architect` subagent in fresh context when a brainstorm surfaces an architectural question. Pauses at the end for user review and approval.
---

Drive the `pm` skill from a feature idea to an approvable spec. One `/feature-start` invocation produces one draft spec and one feature branch; the user reviews and approves before `/plan` runs.

## Arguments

The user types `/feature-start "<short description>"`. The description is a starting point — the brainstorm will sharpen it. Derive a slug from the description (lowercase, hyphenated, ~3 words) for the spec filename, branch name, and `state.md` `Active feature` field. Confirm the slug with the user once you have it; renaming after the spec is written is cheap, after the branch is created is mildly annoying.

If the user invokes `/feature-start` with no argument, ask them for one before proceeding.

## Preconditions

Before doing anything visible to the user:

1. Read `.claude/state.md`.
2. Verify all of the following — if any is false, **stop and report what is missing** (do not work around it):
   - `Active feature` is `none`.
   - `Phase` is `idle`.
   - Working tree is clean (`git status` reports no uncommitted changes).
   - Current branch is `main` (or the project's mainline equivalent — check `CLAUDE.md` for project conventions if `main` isn't it).

If any precondition fails, surface what's blocking and stop. The most common case is an unfinished prior feature: the user resolves it (merge, abandon, or explicitly branch out) before starting the next one.

## Run

Load the `pm` skill. The skill governs the brainstorm-to-spec discipline; this command scopes its work to one feature and orchestrates the side-effects (branch creation, state.md update, ADR writes).

The phases below mirror the `pm` skill's loop. The skill is the source of truth for *how*; this command is the source of truth for *what side-effects fire when*.

### Phase A — Orient and confirm

PM skill orients (reads `CLAUDE.md`, `docs/domains/`, prior `docs/specs/`, the findings ledger, and the project's ADR titles — location per `CLAUDE.md` conventions, not assumed to be `docs/adr/`). Then:

1. Propose the slug derived from the user's argument. Confirm with the user.
2. Confirm the feature framing back to the user in one or two sentences before brainstorming. ("My read: you want X so that Y. Right?")

If the framing confirmation surfaces a misunderstanding, restate and reconfirm. Do not proceed to brainstorm against a wrong frame.

### Phase B — Brainstorm

PM skill runs the brainstorm-to-spec dialogue with the user (see the skill for the dialogue pattern). The brainstorm is visible and interactive; this command does not interfere with it.

Load the `grill-me` skill at the start of this phase. Its discipline (walk the decision tree parents-before-children, explore the codebase before asking, recommend an answer per question, reflect each answer back) applies to every brainstorm question — the spec-as-contract demands it.

If a question arises that warrants the `architect` subagent, invoke it in fresh context (see "Invoking the architect" below). When the architect returns, reflect the recommendation back to the user before accepting it.

### Phase C — Decomposition

PM skill proposes the domain decomposition. The user confirms or corrects. Do not proceed to draft until the decomposition is accepted; correcting domain shape mid-spec is wasteful.

### Phase D — Spec draft

PM skill drafts `docs/specs/<slug>.md` to typical depth, with front-matter:

```yaml
---
feature: <slug>
status: draft
branch: feature/<slug>
owned_files:
  - <glob>
  - <glob>
related_adrs: [<numbers>]
---
```

Write the spec to the path. If `docs/specs/` doesn't exist, create it. If a spec with that slug already exists, **stop and surface** — the user resolves (rename, replace, or abandon) explicitly.

### Phase E — ADRs (if any)

If the architect was invoked during brainstorm and drafted an ADR:

1. **Discover the registry before allocating.** `CLAUDE.md` conventions may record the ADR *location* (written by `/adopt`) — use that to know **where** to look. **Never trust a recorded high-water number.** Re-scan the registry for the current highest every time, because `/adopt` records it once and features allocate continuously: with adoption at `12`, feature one takes `13`, and feature two reading the same cached `12` takes `13` again. Duplicate decision IDs in the normal documented flow, which is worse than the brownfield case this discovery was built for. Scan:
   - **Scope:** `*.md` under `docs/`, plus root-level `*.md`. Never `.git/`, `node_modules/`, `vendor/`, or anything matched by `.gitignore`.
   - **Match, two patterns.** In file *contents*: `ADR[-_ ]?0*\d+`, case-insensitive. In *filenames*: `^0*\d+[-_]` under any directory whose name suggests decision records (`adr`, `adrs`, `decisions`, `rfc`, `rfcs`). The second is not optional — a project using the pack's own `docs/adr/0012-name.md` convention need never write the string "ADR" inside the file, so a contents-only scan finds nothing and allocates `0001` over an existing registry.
   - **Rank definitions above mentions.** A *definition* is a heading (`## ADR-012: …`) or a filename (`0012-*.md`). A *mention* is inline prose — a summary citing `ADR-007`, a changelog line. Take the high-water mark from definitions when any exist; mentions are a lower-confidence fallback and must be reported as such.
2. **Report what was found** — location, format (directory-of-files vs single-file log), highest number, and whether it came from definitions or mentions. A bare number is not something the user can check.
3. **Allocate floor + 1.** If the registry sits outside `docs/adr/`, or definitions appear in more than one location, **ask**: continue numbering in place, or start `docs/adr/` above the high-water mark. **Never silently allocate `0001` when any registry exists** — a duplicate ADR number means two documents claim the same decision ID, and the `architect` starts blind to every prior decision it might contradict.
4. Write the ADR to the confirmed location, in that registry's format. Create `docs/adr/` only when discovery found nothing anywhere.
5. Update the spec's front-matter `related_adrs` to include the new number.
6. **Update the recorded high-water mark** in `CLAUDE.md` conventions to the number just written, so the record stays a useful hint rather than decaying into a wrong one. The re-scan in step 1 is the authority regardless; this keeps the two from disagreeing.

A fixed list of known locations would only ever find the layouts its author thought of. The first brownfield target kept twelve ADRs as headings inside a **single decisions log** rather than a directory of files, under a docs subdirectory no such list would have contained.

### Phase F — Branch

Create the feature branch:

```
git checkout -b feature/<slug>
```

If the branch already exists (because a prior `/feature-start` attempt for the same slug failed mid-flight), surface that and stop — the user decides whether to delete the old branch and retry, or whether to resume.

### Phase G — State update

Update `.claude/state.md`:

- `Active feature: <slug>`
- `Active branch: feature/<slug>`
- `Phase: spec-draft`
- `Spec: docs/specs/<slug>.md`
- `Plan: —`
- `Next step: —`

Leave `## Open questions` alone unless the brainstorm surfaced something deferred.

### Phase H — Commit and hand off

Before the pause, propose a single commit for the artifacts this invocation produced: the spec, any Phase-E ADRs, and the Phase-G `.claude/state.md` updates. Subject: `spec: <slug> (draft)`. Body: one short paragraph — the feature framing in one sentence, plus ADR numbers if any. Stage these files explicitly; never `git add -A` (same reasoning as the engineer skill's commit substep). Wait for confirmation; on decline, leave the proposal visible and proceed to the pause without committing. The user may legitimately want to split (separate commits for spec vs ADR) — let them.

Then pause for the user. Surface, in one short message:

- The spec path.
- Any ADRs written.
- The branch name.
- The commit status (committed / proposal-declined / nothing-to-commit-yet).
- A one-line prompt: "Review the spec; when ready, change its front-matter `status` from `draft` to `approved`, commit that change, and run `/plan`."

Do not auto-approve the spec. The approval-status flip is the user's separate commit between `/feature-start` and `/plan` — the precedent message is `approve spec: <slug>`.

## Invoking the architect

When the PM skill identifies an architectural question during brainstorm (see the PM skill for the criteria — bounded context, layer introduction, cross-cutting pattern, reversal), invoke the `architect` subagent via the `Agent` tool with `subagent_type: architect`. Pass:

- The question framed in one sentence.
- The trade-offs the brainstorm has already considered.
- Paths to: the active spec draft (write-as-you-go if necessary), relevant `docs/domains/<domain>.md` files, relevant `docs/adr/NNNN-*.md` files, and source-code pointers.

The architect returns a recommendation in its response. Reflect it back to the user before accepting; the user's confirmation is the gate before applying it to the spec or writing an ADR.

> **Slice-2 simulation note:** while the pack's subagent format is being stabilized in the host project, `subagent_type: architect` may not yet resolve. The validated fallback is `subagent_type: general-purpose` with the *contents* of `pack/agents/architect.md` (or `.claude/agents/architect.md` in the installed pack) passed as the prompt body. Either way preserves fresh context; the user experience is identical.

## Halt conditions

Stop and surface to the user (do not auto-recover) if:

- Preconditions fail (active feature, dirty tree, wrong branch).
- A spec with the chosen slug already exists.
- The feature branch already exists.
- The architect returns a recommendation that conflicts with what the user said they wanted.
- The brainstorm reveals the feature framing is wrong (the work is bigger or different than the framing implied). Stop and re-frame with the user; do not silently re-scope and continue.
- Git is not available or the repo is not in a state where branching is meaningful.
- The proposed commit cannot be staged (e.g., a file Phase D/E/G expected isn't on disk, or `git add` errors out). Surface; do not work around it.
