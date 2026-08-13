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

### Phase A — Orient, discover, and confirm

PM skill orients (reads `CLAUDE.md`, `docs/domains/`, prior specs, the findings ledger, and — per the `pm` skill's Orient step — runs **both** `.claude/references/adr-registry.md` § *Discover* and `.claude/references/artifact-locations.md` § *Resolve* in full). Then:

1. **Record what pm's Orient just resolved.** Note for the rest of this invocation: the registry's location, its format, and its current high-water number, **and the spec / plan / summary directories** § *Resolve* settled on.

   **Artifact locations are *resolved*, not merely discovered, and the difference is a user question.** § *Resolve* takes the scan to an answer: a default where the namespace is empty, the user's decision where the directory exists and belongs to the project, and a `CLAUDE.md` record either way. That middle branch is the one that cannot be skipped — writing this feature's spec into a directory the project already uses for its own is the brownfield harm the reference was written to prevent, and it passes every precondition on the way in. If § *Resolve* surfaced that question, it was answered here, before Phase D writes anything.

   **Both run here for the same reason.** Phase D writes the spec at a location this phase resolved; a write site that says "the location § *Resolve* returned" is a consumer, and clause 3 puts the producer before every consumer. A producer that never runs is that clause failing in its most complete form — the citation reads as though a value exists when nothing produced one. Report what was found per each reference's *Report what was found* step. Both run once, inside Orient — this step records and reports their results rather than re-running the scans.

   Orient must run discovery before Phase B because **Phase B may invoke the `architect`**. An architect handed a default path on a project whose registry lives elsewhere forms its recommendation having read none of the existing decisions — and allocating correctly at Phase E does not un-form a recommendation already made. On the first brownfield target that meant twelve ADRs kept as headings in a single decisions log, invisible to the subagent asked to avoid contradicting them.
2. Propose the slug derived from the user's argument. Confirm with the user.
3. Confirm the feature framing back to the user in one or two sentences before brainstorming. ("My read: you want X so that Y. Right?")

If the framing confirmation surfaces a misunderstanding, restate and reconfirm. Do not proceed to brainstorm against a wrong frame.

**Writes:** the `CLAUDE.md` conventions entry recording the artifact locations, for any type § *Resolve* settled here that the record did not already name. Otherwise none — every type this invocation needs was already recorded, and the resolution is held for this invocation and consumed by later phases.

### Phase B — Brainstorm

PM skill runs the brainstorm-to-spec dialogue with the user (see the skill for the dialogue pattern). The brainstorm is visible and interactive; this command does not interfere with it.

Load the `grill-me` skill at the start of this phase. Its discipline (walk the decision tree parents-before-children, explore the codebase before asking, recommend an answer per question, reflect each answer back) applies to every brainstorm question — the spec-as-contract demands it.

If a question arises that warrants the `architect` subagent, invoke it in fresh context (see "Invoking the architect" below). When the architect returns, reflect the recommendation back to the user before accepting it.

### Phase C — Decomposition

PM skill proposes the domain decomposition. The user confirms or corrects. Do not proceed to draft until the decomposition is accepted; correcting domain shape mid-spec is wasteful.

### Phase D — Spec draft

PM skill drafts the spec to typical depth, at the location `.claude/references/artifact-locations.md` § *Resolve* returned and named per its § *Name* (`YYYY-MM-DD-<slug>.md`), with front-matter:

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

Write the spec to the path. If the discovered directory doesn't exist, create it. If a spec with that slug already exists, **stop and surface** — the user resolves (rename, replace, or abandon) explicitly.

**Writes:** the spec at its discovered path.

### Phase E — ADRs (if any)

If the architect was invoked during brainstorm and drafted an ADR:

1. **Re-scan before allocating.** Phase A recorded the registry's location, format, and high-water mark from Orient's discovery. Re-run `.claude/references/adr-registry.md` § *Discover* **in full** now — the same full scan Orient ran, not narrowed to the location it found — and allocate from what it returns — **never from the number Phase A recorded**. That reference's *Never cache the number* explains why: `/plan` allocates from the same registry, and a mark read once is reused by the next allocator; a location-scoped re-scan would just as easily reuse a mark that no longer reflects a registry that changed since Orient ran.
2. **Allocate and write** per that reference's *Allocate* section — floor + 1, ask before relocating, write in the registry's own format.
3. Update the spec's front-matter `related_adrs` to include the new number.
4. **Update the recorded high-water mark** in `CLAUDE.md` conventions to the number just written, so the record stays a useful hint rather than decaying into a wrong one. The re-scan in step 1 is the authority regardless; this keeps the two from disagreeing.

**Writes:** the ADR at its discovered path · the `CLAUDE.md` high-water mark updated by step 4.

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
- `Spec: <the path just written>`
- `Plan: —`
- `Next step: —`

Leave `## Open questions` alone unless the brainstorm surfaced something deferred.

**Writes:** `.claude/state.md`.

### Phase H — Commit and hand off

Before the pause, propose a single commit for **the union of every `**Writes:**` declaration the phases that ran produced** — read them off those phases. On a full run the phases carrying declarations are **A, D, E, and G**; go read those four and stage what they name.

**That is a list of phases to read, deliberately, and not a list of files to stage.** This paragraph used to enumerate the artifacts, and the enumeration was wrong twice. It first omitted Phase E's `CLAUDE.md` high-water mark, self-cancellingly: Phase E step 4 exists to stop the recorded mark decaying into a wrong one, so leaving it uncommitted un-does step 4 and the next `/feature-start` re-reads the stale number the update was written to fix. It was then wrong again the moment Phase A gained its artifact-homes write — the same omission, in the paragraph that had just finished naming the failure. A file list maintained at a distance from the writes it covers is what clause 1 forbids, and it does not stop decaying because you have described the decay.

Phase A's write is conditional **per artifact type** and is the one most easily missed: § *Resolve* records the types this run settled that the record did not already name, so a partly-filled record still produces a write, and the run that produces one can look indistinguishable from a run that should not. Do not read "a record already exists" as "nothing to write" — check which types it names. Dropping the write means the next invocation re-derives locations this feature already settled, and re-derivation is what puts artifacts in a directory that belongs to someone else.

Subject: `spec: <slug> (draft)`. Body: one short paragraph — the feature framing in one sentence, plus ADR numbers if any. Stage these files explicitly; never `git add -A` (same reasoning as the engineer skill's commit substep). Wait for confirmation; on decline, leave the proposal visible and proceed to the pause without committing. The user may legitimately want to split (separate commits for spec vs ADR) — let them.

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
- Paths to: the active spec draft (write-as-you-go if necessary), relevant `docs/domains/<domain>.md` files, **relevant ADR files from the registry Phase A discovered** — actual paths, never a pattern, or its explicit `"registry: none found"` — and source-code pointers.

  Passing a path pattern instead of paths is how the architect ends up reading nothing: `docs/adr/NNNN-*.md` matches no file on a project whose decisions live in a single log, and a pattern is neither an actual path nor the explicit `"registry: none found"` signal — so the architect still can't tell that apart from a genuinely empty registry.

The architect returns a recommendation in its response. Reflect it back to the user before accepting; the user's confirmation is the gate before applying it to the spec or writing an ADR.

**Verify the architect's source-level claims before reflecting them.** That confirmation is a *user* gate, not a *truth* gate — the user cannot evaluate a fresh-context agent's confident `file:line` assertions from the reflection alone, and reflecting them unchecked launders an inference into a fact the spec may then be built on. Check the load-bearing ones against source first. On the first full run the architect made five source-level claims and all five held, including one that a prior ADR's override was unwired dead code — correct, load-bearing, and expensive to have passed on wrong. See `.claude/references/evidence-and-uncertainty.md` § *Facts*.

## Halt conditions

Stop and surface to the user (do not auto-recover) if:

- Preconditions fail (active feature, dirty tree, wrong branch).
- A spec with the chosen slug already exists.
- The feature branch already exists.
- The architect returns a recommendation that conflicts with what the user said they wanted.
- The brainstorm reveals the feature framing is wrong (the work is bigger or different than the framing implied). Stop and re-frame with the user; do not silently re-scope and continue.
- Git is not available or the repo is not in a state where branching is meaningful.
- The proposed commit cannot be staged (e.g., a file Phase D/E/G expected isn't on disk, or `git add` errors out). Surface; do not work around it.
