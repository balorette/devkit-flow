---
slice: 9
status: draft
designs:
  - docs/design/0005-brownfield-portability.md
  - docs/design/0003-pr-lifecycle-and-findings-triage.md   # § Corrections (Phase 2)
  - docs/design/0006-findings-ledger-and-plan-conformance.md
evidence: docs/validation/brownfield-install-astraeus.md
---

# Slice 9 — Astraeus Findings: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the twelve findings from the first brownfield install so that one continuous Astraeus dogfood can run end to end — Phase 1 unblocks *starting*, Phase 2 unblocks *finishing*, Phase 3 extends the design with what the review corpus proved was missing.

**Architecture:** Three phases in lifecycle order, not priority order. Phase 1 makes the pack adapt to a target shaped unlike itself (*read flexibly, write conservatively*). Phase 2 repairs six defects in slice 8, two of which contradict decisions ADR-0003 records as resolved. Phase 3 adds a plan-time conformance subagent and a durable findings ledger. Two shared reference files replace duplicated definitions that had already produced a deadlock.

**Tech Stack:** Markdown pack content (Claude Code `SKILL.md` / agent / command / reference formats); stdlib `unittest` for the pack's executable surface; `gh` CLI for the PR lifecycle; `install.sh` + `install_lib.py` for packaging.

---

## Global Constraints

- **Read flexibly, write conservatively** (ADR-0005). Discover where things are; never rename the user's structure, never write inside a region another tool owns, never silently pick when discovery is ambiguous.
- **Propose before writing.** No pack component silently applies a doc edit, a commit, a merge, or a PR reply.
- **Never post unseen.** Nothing reaches a PR without explicit user confirmation.
- **Never `git add -A`.** Stage each task's files explicitly.
- **Design docs are the contract.** Any divergence updates the ADR in the same commit, with a dated note.
- **No new skill and no new hook this slice.** One new subagent (`conformance-reviewer`), two new references, one new durable artifact (`docs/findings.md`).
- **`.claude/` is pack-owned.** Vendored pack files are versioned by the pack, not by the host repo's conventions (validation Finding 12).

### Resolved during design review — do not re-litigate

| Question | Resolution |
|---|---|
| Reference guard in `install.sh` too? | **Tests only.** The installer must not fail on the pack author's mistake at the user's machine. |
| Conformance findings blocking or advisory? | **Blocking for direct contradictions, advisory for ambiguity.** |
| Who closes a findings row? | **`/checkpoint` and `/feature-merge` via `documenter`. Never automatically.** |
| ADR discovery mechanism? | **Token scan**, made precise by scoping + definition-vs-mention ranking + reporting. Not an alternates list. |

### The test cycle

Two mechanical checks, runnable per task:

```bash
# A — installer tracks the expected file set, no packaging change needed
./install.sh "$(mktemp -d)" --dry-run

# B — the full unit suite (grows in Task 2)
python3 -m unittest discover -s tests
```

Markdown behaviour is verified per `CLAUDE.md` principle 4: **write the prediction before authoring**, then run it in a fresh session. Predictions accumulate in `docs/validation/slice-9.md` (Task 20) and are recorded **pending** if unrun — never marked passed without a run.

---

## File Structure

| File | Status | Responsibility | Phase |
|---|---|---|---|
| `pack/references/spec-and-plan-depth.md` | **Create** | Typical-depth section checklists for specs and plans. Ends the dangling normative citation. | 1 |
| `pack/references/claude-md-elements.md` | **Create** | The single canonical-element + equivalence table. Cited by `/adopt` and `/claude-md-merge`. | 1 |
| `tests/test_pack_references_resolve.py` | **Create** | Guard: no installed pack file cites a path that won't resolve in a target. | 1 |
| `pack/commands/feature-start.md` | Modify | ADR registry token-scan discovery before allocation. | 1 |
| `pack/commands/adopt.md` | Modify | Equivalence-aware Phase D; ADR discovery; CI gate discovery; sentinel safety; inline the ADR-0002 rule. | 1 |
| `pack/commands/claude-md-merge.md` | Modify | Cite the shared element table; sentinel safety. | 1 |
| `pack/skills/pm/SKILL.md` | Modify | Repoint depth citations (1); read the findings ledger at orient (3). | 1, 3 |
| `pack/skills/documenter/SKILL.md` | Modify | Repoint depth citation (1); own `docs/findings.md` (3). | 1, 3 |
| `pack/state.md.template` | Modify | `Gated baseline:` field. | 2 |
| `pack/commands/feature-merge.md` | Modify | F5, F6, F7, F8, F11-Gate-1; Gate 2 conformance; ledger writes. | 2, 3 |
| `pack/commands/pr-review.md` | Modify | F9 reply marker, F10 push-then-reply; ledger writes. | 2, 3 |
| `pack/references/findings-triage.md` | Modify | Reply marker; ledger as a disposition. | 2, 3 |
| `pack/agents/conformance-reviewer.md` | **Create** | Plan-time spec-vs-plan contradiction review. Never reads code. | 3 |
| `pack/commands/plan.md` | Modify | Invoke `conformance-reviewer` before the approval hand-off. | 3 |
| `pack/skills/engineer/SKILL.md` | Modify | ~20-line debugging fold-in. | 3 |
| `pack/devkit-orientation.md`, `README.md` | Modify | Surface new behaviour; pack-owned note. | 1, 3 |
| `docs/validation/slice-9.md` | **Create** | Predictions + outcomes. | 3 |

**Deliberately unchanged:** `install.sh`, `install_lib.py`. Both new references land under `pack/references/`, already inside `TRACKED_DIRS` (`install_lib.py:46`). Verify with check A rather than assuming.

---

# PHASE 1 — Brownfield portability (ADR-0005)

## Task 1: Extract `spec-and-plan-depth.md` and repoint the dangling citations

**Files:**
- Create: `pack/references/spec-and-plan-depth.md`
- Modify: `pack/skills/pm/SKILL.md:14`, `:330`, `:349`
- Modify: `pack/skills/documenter/SKILL.md:192`

**Interfaces:**
- Consumes: content from `docs/authoring-notes/spec-and-plan-depth.md` (devkit-repo only).
- Produces: `.claude/references/spec-and-plan-depth.md`, cited by Tasks 2 and 20.

- [ ] **Step 1: Extract the reference**

Read `docs/authoring-notes/spec-and-plan-depth.md` and lift only what the skills cite: the depth rule, the typical-spec section checklist, and the typical-plan section checklist. Leave authoring rationale behind — it belongs to the project, not the pack. Match the house format of `pack/references/solid-checklist.md`: `# Title`, a `Used by:` line, a framing paragraph, terse sections. No YAML front-matter.

- [ ] **Step 2: Repoint `pm/SKILL.md:14`**

Current text names two devkit-repo paths:

> This rule is documented in the devkit project's `docs/authoring-notes/spec-and-plan-depth.md`. Live exemplars are in `docs/design/walkthrough.md` (illustrative) and any merged spec under `docs/specs/` (real-shape).

Replace with:

```markdown
This rule is documented in `.claude/references/spec-and-plan-depth.md`. Live exemplars are any merged spec under `docs/specs/` — real-shape beats illustrative, and this project's own specs are the best guide to its own depth.
```

The `walkthrough.md` citation is **dropped, not installed** (ADR-0005 Fix 1).

- [ ] **Step 3: Repoint `pm/SKILL.md:330`**

> Sections (per the typical-plan checklist in `docs/authoring-notes/spec-and-plan-depth.md`):

becomes:

```markdown
Sections (per the typical-plan checklist in `.claude/references/spec-and-plan-depth.md`):
```

- [ ] **Step 4: Fix the normative claim at `pm/SKILL.md:349`**

Current row arbitrates between two documents, one of which no longer ships:

> - **Producing a thin spec because the walkthrough's example looks thin.** The walkthrough demonstrates *shape*, not *depth*. The spec-and-plan-depth authoring note is the source of truth for depth. When the walkthrough and the authoring note disagree, the authoring note wins.

Replace with:

```markdown
- **Producing a thin spec because an example looks thin.** Examples demonstrate *shape*, not *depth*. `.claude/references/spec-and-plan-depth.md` is the source of truth for depth. A merged spec that looks thinner than the checklist was scope-cut, not depth-cut — check its amendments before copying its shape.
```

With one source there is no disagreement to arbitrate.

- [ ] **Step 5: Repoint `documenter/SKILL.md:192`** to `.claude/references/spec-and-plan-depth.md`, preserving the surrounding sentence.

- [ ] **Step 6: Run check A**

```bash
./install.sh "$(mktemp -d)" --dry-run 2>&1 | grep -E "new |spec-and-plan-depth"
```

Expected: count rises by one; `references/spec-and-plan-depth.md` listed as NEW.

- [ ] **Step 7: Commit**

```bash
git add pack/references/spec-and-plan-depth.md pack/skills/pm/SKILL.md pack/skills/documenter/SKILL.md
git commit -m "pack: extract spec-and-plan-depth reference, end the dangling citations (slice 9, task 1)"
```

---

## Task 2: The reference-resolution guard

**Files:**
- Create: `tests/test_pack_references_resolve.py`

**Interfaces:**
- Consumes: `pack/**` and `install_lib.py`'s `TRACKED_DIRS` / `iter_tracked_pack_files`.
- Produces: an enforced invariant. No later task may reintroduce a devkit-repo-only citation.

- [ ] **Step 1: Write the failing test first**

Add a case asserting a *known-bad* citation is caught, before the scanner exists — e.g. a fixture string `see docs/design/0002-brownfield-adoption.md` fed through the classifier must classify as `FORBIDDEN`.

- [ ] **Step 2: Implement the three-class classifier**

Stdlib `unittest`, matching `tests/test_doc_drift_detector.py`'s posture. Scan every file under `pack/{skills,agents,commands,references}` for backtick-quoted path-shaped tokens, and classify:

```python
PACK_INSTALLED = ".claude/"       # must exist under pack/ at the mapped path
RUNTIME_TARGET = (                # allowlist: created by the workflow, legitimately absent
    "docs/specs/", "docs/plans/", "docs/adr/", "docs/domains/",
    "docs/summaries/", "docs/findings.md", ".claude/state.md",
)
# anything else matching r'docs/[a-z0-9-]+/' is FORBIDDEN (devkit-repo-only)
```

A `.claude/...` citation resolves by stripping the prefix and checking `pack/<rest>` exists. Report every violation with file, line, and the offending token — a bare count is not actionable.

- [ ] **Step 3: Run it**

```bash
python3 -m unittest discover -s tests -v
```

Expected: green. If it flags anything beyond what Task 1 fixed, **stop and report** — an unknown dangling reference is exactly what this guard exists to find, and it should be fixed in its own commit rather than folded in here.

- [ ] **Step 4: Commit**

```bash
git add tests/test_pack_references_resolve.py
git commit -m "test: guard that installed pack references resolve in a target (slice 9, task 2)"
```

---

## Task 3: One shared definition of CLAUDE.md's elements — break the deadlock

**Files:**
- Create: `pack/references/claude-md-elements.md`
- Modify: `pack/commands/claude-md-merge.md` (the `:38` table, `:44` classification rules)
- Modify: `pack/commands/adopt.md` (Phase D, `:99` and `:101`)

**Interfaces:**
- Produces: `.claude/references/claude-md-elements.md` — the single source both commands cite. Task 5 extends it with the sentinel rules.

- [ ] **Step 1: Extract the table**

Move `claude-md-merge.md:38`'s six-element table (title, description, *How to read this project*, orientation reference, *Project conventions*, *When in doubt*) into the new reference, including the equivalence column that already lists *"Project conventions" / "Conventions" / "Setup" / "Stack" / similar*. Carry over the three classifications from `:44` — present-equivalent / partial / absent — and the churn rule: gratuitous heading renames are not proposed.

- [ ] **Step 2: `claude-md-merge.md` cites instead of defines**

Replace the inline table with a pointer to `.claude/references/claude-md-elements.md`, keeping the command's own sequencing and proposal-shape sections intact.

- [ ] **Step 3: Fix `/adopt` Phase D — the actual deadlock**

`adopt.md:101` currently reads:

> If `CLAUDE.md` is not yet devkit-shaped (no `## Project conventions` section, no orientation reference), **stop this phase and route through `/claude-md-merge` first**

Replace with:

```markdown
Resolve the conventions section using `.claude/references/claude-md-elements.md` — element 5, including its equivalence set. A section named `## Conventions`, `## Setup`, `## Stack`, or similar **is** the conventions section; write into it and do not propose a rename.

Route to `/claude-md-merge` only when **no** equivalent exists at all. Requiring the literal heading here while `/claude-md-merge` treats equivalents as satisfied is what produced an unresolvable loop on the first brownfield target.
```

Also update `:99` so it writes into the *resolved* section rather than a literal `## Project conventions`.

- [ ] **Step 4: Inline the ADR-0002 citation at `adopt.md:92`**

`(see Decision 1 in docs/design/0002)` is a devkit-repo path and will now fail Task 2's guard. Replace with the rule itself:

```markdown
(Do not manufacture retroactive ADRs. As-built rationale belongs in the domain doc's *as-built rationale* subsection; an ADR is written only for a decision the user flags as load-bearing *and* plausibly reversible.)
```

- [ ] **Step 5: Run checks A and B.** Guard must stay green — this task removes the last known forbidden citation.

- [ ] **Step 6: Commit**

```bash
git add pack/references/claude-md-elements.md pack/commands/claude-md-merge.md pack/commands/adopt.md
git commit -m "pack: one shared CLAUDE.md element definition; /adopt accepts equivalents (slice 9, task 3)"
```

---

## Task 4: ADR registry discovery by token scan

**Files:**
- Modify: `pack/commands/feature-start.md` (Phase E, the lines beginning *"Find the next free ADR number…"*)
- Modify: `pack/commands/adopt.md` (new discovery step)

**Interfaces:**
- Produces: a recorded ADR location + high-water mark in `CLAUDE.md` conventions, consumed by `/feature-start`.

- [ ] **Step 1: Write the prediction**

```markdown
### Prediction P1 — ADR discovery must not allocate 0001
Task: /feature-start on Astraeus, where docs/adr/ does not exist and
docs/ai/decisions.md holds ADR-001…ADR-012.
Predicted: reports "12 definitions found in docs/ai/decisions.md (single-file
log)", proposes 013, and ASKS whether to continue there or start docs/adr/
above the high-water mark. Never writes docs/adr/0001-*.md.
Catches: silent duplication of a decision registry.
```

- [ ] **Step 2: Replace the allocation step in `feature-start.md` Phase E**

Current:

> 1. Find the next free ADR number by listing `docs/adr/*.md` and incrementing the highest.
> 2. Write the ADR to `docs/adr/NNNN-<short-name>.md`.
> […] If `docs/adr/` doesn't exist, create it.

Replace with:

```markdown
1. **Discover the registry before allocating.** If `CLAUDE.md` conventions already record an ADR location and high-water mark (written by `/adopt`), use it. Otherwise scan:
   - **Scope:** `*.md` under `docs/`, plus root-level `*.md`. Never `.git/`, `node_modules/`, `vendor/`, or anything matched by `.gitignore`.
   - **Match:** `ADR[-_ ]?0*\d+`, case-insensitive.
   - **Rank definitions above mentions.** A definition is a heading (`## ADR-012: …`) or a filename (`0012-*.md`); a mention is inline prose. The high-water mark comes from definitions when any exist; mentions are a lower-confidence fallback and must be reported as such.
2. **Report what was found** — location, format (directory-of-files vs single-file log), highest number, and whether it came from definitions or mentions.
3. **Allocate floor + 1.** If the registry sits outside `docs/adr/`, or definitions appear in more than one location, **ask** — continue numbering in place, or start `docs/adr/` above the high-water mark. Never silently allocate `0001` when any registry exists.
4. Write the ADR to the confirmed location. Create `docs/adr/` only when discovery found nothing anywhere.
5. Update the spec's front-matter `related_adrs`.
```

- [ ] **Step 3: Add ADR discovery to `/adopt`**

A step that runs the same scan and records the result into `CLAUDE.md` conventions (`ADRs live in <path> (<format>); highest is <N>`). **Discovery is not authoring** — ADR-0002 Decision 1 stands; no ADRs are written.

- [ ] **Step 4: Run checks A and B.**

- [ ] **Step 5: Commit**

```bash
git add pack/commands/feature-start.md pack/commands/adopt.md
git commit -m "pack: discover the ADR registry by token scan before allocating (slice 9, task 4)"
```

---

## Task 5: Sentinel-region safety

**Files:**
- Modify: `pack/references/claude-md-elements.md` (add the sentinel rules — one definition, both consumers)
- Modify: `pack/commands/adopt.md`, `pack/commands/claude-md-merge.md` (cite them)

- [ ] **Step 1: Write the prediction**

```markdown
### Prediction P2 — never write inside another tool's region
Task: /adopt on Astraeus, whose CLAUDE.md carries GSD sentinels at lines
137/158/160/189 — with ## Conventions INSIDE the conventions-start region,
and with conventions-start having no matching -end.
Predicted: detects the regions, names them in the proposal, writes ADJACENT
rather than inside, and flags the unmatched sentinel as suspect rather than
guessing the region's extent.
Catches: silently clobbering a region another tool regenerates.
```

- [ ] **Step 2: Add the rules to the shared reference**

```markdown
## Machine-owned regions

Real `CLAUDE.md` files contain regions written by other tools. Detect them:

    <!--\s*([A-Z][A-Z0-9_]*):([a-z-]+)-(start|end)\s*(.*)-->

**Never write inside a matched start/end pair.** If a canonical element lives inside one, write adjacent — immediately before the start or after the end — and say why in the proposal. The other tool owns that text; devkit does not.

**Malformed or orphaned sentinels** — an unmatched `-start`, or an `-end` with no start — are treated as suspect. Do not infer the region's extent. Surface the orphan and ask.

**Always name detected regions in the proposal**, including ones devkit did not need to touch. The user should see what devkit declined to write into and why.
```

- [ ] **Step 3: Cite from both commands** at their write steps.

- [ ] **Step 4: Run checks A and B. Commit**

```bash
git add pack/references/claude-md-elements.md pack/commands/adopt.md pack/commands/claude-md-merge.md
git commit -m "pack: detect machine-owned CLAUDE.md regions and write adjacent (slice 9, task 5)"
```

---

## Task 6: Host CI gate discovery in `/adopt`

**Files:**
- Modify: `pack/commands/adopt.md` (Phase A conventions survey)

**Interfaces:**
- Produces: a `CLAUDE.md`-recorded blocking-gate list, consumed by Task 13.

- [ ] **Step 1: Add the discovery step to Phase A**

```markdown
**Blocking CI gates.** Read `.github/workflows/*.yml` (and `.gitlab-ci.yml`, `Makefile` targets named `ci`/`check`/`verify` if present) and extract the commands that gate a merge. Record them verbatim in `CLAUDE.md` conventions as a **Blocking gates** list, with `file:line` evidence like every other Phase A entry.

This is what `/feature-merge` Gate 1 runs. Without it the pack asserts its own definition of "tests pass" — Astraeus has four blocking gates and devkit checks three, so Gate 1 can pass and open a PR that CI fails immediately. If no CI config exists, say so and record nothing; Gate 1 falls back to the inferred runner.
```

- [ ] **Step 2: Run checks A and B. Commit**

```bash
git add pack/commands/adopt.md
git commit -m "pack: /adopt discovers the project's blocking CI gates (slice 9, task 6)"
```

---

## Task 7: Phase 1 doc currency

**Files:**
- Modify: `docs/design/0002-brownfield-adoption.md` (amendment), `README.md`, `pack/devkit-orientation.md`

- [ ] **Step 1: Amend ADR-0002** with a dated section noting Findings 1–3, that Decision 1 (no retroactive ADRs) is **unchanged**, and that discovery is now distinguished from authoring. Point at ADR-0005.

- [ ] **Step 2: Add the pack-ownership note to `devkit-orientation.md`** (validation Finding 12's generalizable lesson):

```markdown
## `.claude/` is pack-owned

Files under `.claude/` are vendored from the devkit pack and versioned by it, not by this repository's conventions. Your linters, reviewers, and CI will see them and may file findings against them under your project's rules — the drift hook's deliberate `print(..., file=sys.stderr)` is the common one, since that stderr line *is* the hook's channel to the model. Treat `.claude/` findings as pack issues, not project issues, and report them upstream rather than editing in place: local edits are what the installer's customization detection will skip on your next update.
```

- [ ] **Step 3: Update `README.md`** — references row gains both new files; the adoption section notes ADR/CI discovery.

- [ ] **Step 4: Run checks A and B. Commit**

```bash
git add docs/design/0002-brownfield-adoption.md README.md pack/devkit-orientation.md
git commit -m "docs: phase-1 currency — 0002 amendment, pack-ownership note, README (slice 9, task 7)"
```

---

# PHASE 2 — Slice-8 defect fixes (ADR-0003 § Corrections)

## Task 8: F5 — gated-baseline SHA

**Files:**
- Modify: `pack/state.md.template`, `pack/commands/feature-merge.md` (Phase-branch table)

- [ ] **Step 1: Write the prediction**

```markdown
### Prediction P4 — a rerun after a review fix must re-run the gates
Task: /feature-merge with Phase: in-review, after /pr-review pushed a fix, so
local and remote tips agree.
Predicted: compares the PR tip against the recorded Gated baseline (NOT
against the local tip), sees they differ, and re-runs gates 1-3.
Catches: skipping tests/docs/security on the code that actually merges.
```

- [ ] **Step 2: Add the field** to `state.md.template` after `**PR:** —`:

```markdown
**Gated baseline:** —
```

Document it in the HTML comment: *the last `HEAD` that passed gates 1–3; set at PR open and after every successful gate rerun; compared against the PR tip to decide whether a rerun needs the gates.*

- [ ] **Step 3: Rewrite the two `in-review` PR-open rows** in the Phase-branch table so the discriminator is `Gated baseline` vs the PR tip, **not** local vs remote tip. State the failure mode inline so the reason survives future edits.

- [ ] **Step 4: Set it on success** — the PR-creation step and every successful gate rerun write the gated `HEAD`.

- [ ] **Step 5: Run checks A and B. Commit**

```bash
git add pack/state.md.template pack/commands/feature-merge.md
git commit -m "pack: record a gated-baseline SHA so reruns can't skip the gates (slice 9, task 8, F5)"
```

---

## Task 9: F6 + F7 — closeout integrity

Grouped: both are "the closeout writes land somewhere they don't survive," in adjacent sections.

**Files:**
- Modify: `pack/commands/feature-merge.md` (*After all three gates pass*, *PR creation*, *After the merge*)

- [ ] **Step 1: F6 — propose a closeout commit before integration**

The summary and domain/state updates are authored after the clean-tree precondition and never committed, so `git push` and `git merge` both transport nothing. Add, before the *PR creation* and *Merge proposal* steps:

```markdown
**Commit the closeout docs before proposing integration.** The summary, any domain-doc updates, and the state.md transition are authored above but not yet committed — and both `git push` and `git merge` transport only committed changes. Propose a commit (`/feature-merge: summary + state.md`) staging exactly those files. Without it the PR omits the summary the PR body was built from, and a local merge leaves it untracked in the working tree.
```

- [ ] **Step 2: F7 — check out mainline before writing post-merge state**

In *After the merge*, before the numbered list:

```markdown
**Check out mainline first.** PR creation never leaves the feature branch, so a closeout invocation is normally still on `feature/<slug>`. Writing the idle transition there leaves mainline holding the feature's stale `building` state and the idle write stranded on a branch about to be deleted. Order: check out mainline, write the state transition, commit it, *then* propose any push.
```

- [ ] **Step 3: Run checks A and B. Commit**

```bash
git add pack/commands/feature-merge.md
git commit -m "pack: commit closeout docs and write post-merge state on mainline (slice 9, task 9, F6+F7)"
```

---

## Task 10: F8 — merge-base diff in Gate 3

**Files:**
- Modify: `pack/commands/feature-merge.md` (Gate 3 diff command)

- [ ] **Step 1: Replace the two-dot form.** `git diff <mainline>..HEAD` becomes `git diff <mainline>...HEAD` (or `--merge-base`), with the reason inline:

```markdown
Use the three-dot (merge-base) form. With two dots, any commit that landed on mainline after this branch diverged renders as a *removal* in the feature's diff, so the `security-reviewer` can report — or block on — changes this feature never made.
```

- [ ] **Step 2: Run checks A and B. Commit**

```bash
git add pack/commands/feature-merge.md
git commit -m "pack: gate 3 uses the merge-base diff (slice 9, task 10, F8)"
```

---

## Task 11: F9 — a reply marker across all three surfaces

**Files:**
- Modify: `pack/commands/pr-review.md` (Phase A dedupe, Phase D reply steps)
- Modify: `pack/references/findings-triage.md`

- [ ] **Step 1: Define the marker** — every reply the pack posts, on **all three** surfaces, ends with:

```html
<!-- devkit:pr-review handled:<comment-id> -->
```

- [ ] **Step 2: Rewrite the Phase A skip rule.** Replace the `in_reply_to_id` test with a marker search across inline threads, review bodies, and top-level comments. Keep reporting the skipped count.

- [ ] **Step 3: Record why in the command**, so the correction isn't re-reverted:

```markdown
ADR-0003 chose the forge as the triage ledger — no local state — and that choice stands. What failed was the *detection*: `in_reply_to_id` exists only on inline review comments, so replies to review bodies and top-level comments recorded nothing and a second pass re-fetched both the original item and the pack's own reply. A marker the pack writes itself works on every surface and still requires no local bookkeeping.
```

- [ ] **Step 4: Run checks A and B. Commit**

```bash
git add pack/commands/pr-review.md pack/references/findings-triage.md
git commit -m "pack: stable reply marker for dedupe across all three PR surfaces (slice 9, task 11, F9)"
```

---

## Task 12: F10 — push before replying

**Files:**
- Modify: `pack/commands/pr-review.md` (Phase D ordering, halt conditions)

- [ ] **Step 1: Reorder Phase D.** Current order is fixes → docs → state → **replies → push**. New order:

```markdown
1. Code fixes (one at a time, `engineer` Verify discipline, own `review:` commit).
2. Doc amendments via `documenter`.
3. `state.md` — Open questions add/remove.
4. **Push, and verify the remote tip contains the fix commits.**
5. **Replies**, only after the push is confirmed.
```

- [ ] **Step 2: Replace the stale rationale.** The command currently justifies replies-last with *"so a reply saying 'fixed in `<sha>`' is true when it posts."* Replace:

```markdown
Push before replying. A reply citing a SHA is a public, unrecallable claim about the remote — and until the push succeeds, that SHA does not exist there. If the push fails (auth, network, rejected non-fast-forward) after replies have posted, the PR carries citations to code it does not contain. The earlier ordering had this exactly backwards.
```

- [ ] **Step 3: Add the halt condition** — push fails after fixes are committed: report which commits are local-only, post nothing, stop.

- [ ] **Step 4: Run checks A and B. Commit**

```bash
git add pack/commands/pr-review.md
git commit -m "pack: push and verify the remote tip before posting replies (slice 9, task 12, F10)"
```

---

## Task 13: F11 — Gate 1 runs the discovered gate set

**Files:**
- Modify: `pack/commands/feature-merge.md` (Gate 1)

**Interfaces:**
- Consumes: the **Blocking gates** list Task 6 records in `CLAUDE.md`.

- [ ] **Step 1: Rewrite Gate 1's command selection**

```markdown
Run the project's **Blocking gates** list from `CLAUDE.md` conventions if `/adopt` recorded one. Only when it is absent do you infer the runner from project config (`pyproject.toml`, `package.json`, `Cargo.toml`) — and say so, since an inferred gate set is a guess about what the project means by "tests pass."

The distinction matters: a coverage-delta or diff-cover gate is invisible to a plain test run, so Gate 1 can pass and open a PR that CI fails on the first push.
```

- [ ] **Step 2: Run checks A and B. Commit**

```bash
git add pack/commands/feature-merge.md
git commit -m "pack: gate 1 runs the project's discovered blocking gates (slice 9, task 13, F11)"
```

---

# PHASE 3 — Findings ledger and plan conformance (ADR-0006)

## Task 14: The `conformance-reviewer` subagent

**Files:**
- Create: `pack/agents/conformance-reviewer.md`

- [ ] **Step 1: Write the prediction**

```markdown
### Prediction P5 — catch a planted spec/plan contradiction
Task: a spec stating "returns HTTP 409 when blocked" and a plan whose endpoint
returns 200 in all cases.
Predicted: returns one BLOCKING finding naming both locations and quoting both
claims. Does NOT read source. Does NOT propose the fix's implementation.
Catches: the exact class the 2026-04-15 Astraeus review found four times.
```

- [ ] **Step 2: Author the agent**

Match `pack/agents/security-reviewer.md`'s shape: front-matter `name`/`description`, a role paragraph, explicit non-goals, output format, severity criteria, an anti-rationalization table.

Required content:
- **Inputs:** approved spec, draft plan. **Never source code** — a reviewer that reads source drifts into being a second code reviewer, and that slot is usually already occupied.
- **Finding shape:** *"Plan §X states P; spec §Y states Q; these contradict."* Both quoted, both located.
- **Severity:** **blocking** for a direct contradiction (a stated value, status code, path, or signature differs); **advisory** for ambiguity (the spec is silent or admits both readings). Advisory findings do not stop approval.
- **Non-goals:** don't review code quality, don't propose implementations, don't re-litigate the spec's decisions, don't flag *absence* of coverage — Gate 2 owns that.
- **Anti-rationalization rows** including: "the plan's approach is better, so I'll bless it" → *your job is conformance, not adjudication; a better idea that contradicts an approved spec is a `/checkpoint` amendment*.

- [ ] **Step 3: Run checks A and B. Commit**

```bash
git add pack/agents/conformance-reviewer.md
git commit -m "pack: add conformance-reviewer subagent (slice 9, task 14)"
```

---

## Task 15: Invoke it from `/plan`

**Files:**
- Modify: `pack/commands/plan.md`

- [ ] **Step 1: Add the invocation** at the end of the run, before the approval hand-off: pass spec path + plan path only. Blocking findings mean the plan is revised **before** `status: approved`; advisory findings are surfaced and the user decides.

- [ ] **Step 2: Add the halt condition** — blocking findings unresolved.

- [ ] **Step 3: Run checks A and B. Commit**

```bash
git add pack/commands/plan.md
git commit -m "pack: /plan runs conformance review before approval (slice 9, task 15)"
```

---

## Task 16: `docs/findings.md` — the ledger

**Files:**
- Modify: `pack/skills/documenter/SKILL.md`

- [ ] **Step 1: Add the ownership section**

```markdown
### The findings ledger — `docs/findings.md`

One append-only table. A finding earns its own file only when a row can't hold it.

| ID | Category | Severity | Source | Status | Where |
|----|----------|----------|--------|--------|-------|
| SEC-001 | security | medium | security-reviewer, notes-write | open | `src/notes/repo.py:88` |

Categories: `CONF` (conformance-reviewer), `SEC` (security-reviewer), `ARCH` (an architect recommendation that produced no ADR), `REV` (external PR review).

**Rows are never closed automatically.** `/checkpoint` and `/feature-merge` propose closure; the user confirms — same cardinal discipline as every other durable doc.

**A ledger nobody reads is worse than none.** `/feature-start`'s orient phase reads it; if that stops happening, this file is a graveyard and should be deleted rather than maintained.
```

- [ ] **Step 2: Run checks A and B. Commit**

```bash
git add pack/skills/documenter/SKILL.md
git commit -m "pack: documenter owns the findings ledger (slice 9, task 16)"
```

---

## Task 17: Write to the ledger

**Files:**
- Modify: `pack/commands/feature-merge.md` (Gate 2 conformance question; Gate 3 ledger write)
- Modify: `pack/commands/pr-review.md` (ledger write)
- Modify: `pack/references/findings-triage.md` (ledger as a disposition)

- [ ] **Step 1: Gate 2 gains the conformance question**

```markdown
- **Acceptance-criteria conformance:** for each criterion, does any completed work *contradict* it? Coverage and conformance are different questions — a step can satisfy the coverage check while violating the criterion it maps to (a schema field that reopens a path the spec says must be blocked). Coverage-checking is structurally blind to this; ask it explicitly.
```

- [ ] **Step 2: Gate 3 writes `SEC` rows** for every non-critical finding instead of only recording them in the summary. The summary keeps its *Security review notes* section and cross-references the row IDs.

- [ ] **Step 3: `/pr-review` writes `REV` rows** for accepted-but-deferred findings, replacing the `state.md` Open-questions parking for anything that must outlive the merge.

- [ ] **Step 4: `findings-triage.md` gains "record in the ledger"** as an explicit disposition alongside fix / cite / push back / ask.

- [ ] **Step 5: Run checks A and B. Commit**

```bash
git add pack/commands/feature-merge.md pack/commands/pr-review.md pack/references/findings-triage.md
git commit -m "pack: write findings to the ledger; gate 2 asks conformance (slice 9, task 17)"
```

---

## Task 18: `pm` reads the ledger at orient

**Files:**
- Modify: `pack/skills/pm/SKILL.md` (orient phase)

- [ ] **Step 1: Add `docs/findings.md` to the orient reading list**, after `docs/domains/`: open rows touching the area the new feature will change are prior art — either fix-now candidates for this feature's scope or known hazards to design around.

- [ ] **Step 2: Run checks A and B. Commit**

```bash
git add pack/skills/pm/SKILL.md
git commit -m "pack: pm reads the findings ledger at orient (slice 9, task 18)"
```

---

## Task 19: Fold debugging discipline into `engineer`

**Files:**
- Modify: `pack/skills/engineer/SKILL.md`

- [ ] **Step 1: Add the section** (~20 lines), after *Karpathy discipline*:

```markdown
## When something breaks

Root cause before fix. The rule is not "investigate thoroughly" — it is **no fix without a stated cause**.

1. **Read the error completely.** Stack trace, line numbers, exit codes. Most are more specific than they first appear.
2. **Reproduce.** If it isn't reliably reproducible, gather data — don't guess.
3. **Check what changed.** Per-step commits make `git bisect` cheap here; that is a payoff of the commit cadence, not a coincidence.
4. **State one hypothesis** — "I think X because Y" — and test it with the smallest possible change. One variable.
5. **Write the failing test through the `tester` subagent**, fresh context, exactly as in the Red phase. A fix without a test that pins it will regress.
6. **Three strikes.** If three hypotheses have failed, stop fixing. Repeated failures in different places mean the architecture is wrong, not the attempt — invoke the `architect`, then `/checkpoint` if the plan needs amending.

Do not bundle "while I'm here" changes into a fix. The diff that fixes the bug should contain only the fix.
```

- [ ] **Step 2: Run checks A and B. Commit**

```bash
git add pack/skills/engineer/SKILL.md
git commit -m "pack: fold debugging discipline into engineer (slice 9, task 19)"
```

---

## Task 20: Phase 3 doc currency + validation record

**Files:**
- Create: `docs/validation/slice-9.md`
- Modify: `README.md`, `pack/devkit-orientation.md`, `docs/design/inventory-and-build-order.md`, `CLAUDE.md`

- [ ] **Step 1: Create `docs/validation/slice-9.md`** in the slice-8 format. Move predictions P1, P2, P4, P5 in with **pending** status and empty `Actual:` fields. Record any authoring findings, as slice 8 did.

- [ ] **Step 2: `inventory-and-build-order.md`** — slice-9 section (three phases); subagents `(3)` → `(4)`; add `conformance-reviewer` to the agents table.

- [ ] **Step 3: `README.md` + `devkit-orientation.md`** — the ledger, the conformance step in the walkthrough, the fourth subagent, `docs/findings.md` in the memory layout.

- [ ] **Step 4: `CLAUDE.md`** — move slice-9 items to Shipped; record the four dogfood predictions as outstanding.

- [ ] **Step 5: Run checks A and B. Commit**

```bash
git add docs/validation/slice-9.md README.md pack/devkit-orientation.md docs/design/inventory-and-build-order.md CLAUDE.md
git commit -m "docs: slice-9 currency — validation record, inventory, README, status (slice 9, task 20)"
```

---

## Dogfood (after Task 20)

Not a task — the gate that closes the slice, per `CLAUDE.md` working principle 2.

Re-run `install.sh` against Astraeus (picks up all of Phase 1–3), then run **one continuous feature** through the full lifecycle: `/adopt` → `/feature-start` → `/plan` → `/build` → `/feature-merge` (PR path) → automated reviewers comment → `/pr-review` → merge on GitHub → `/feature-merge` (closeout).

Verify P1, P2, P4, P5, plus: `## Conventions` written into without a rename; GSD sentinels named and untouched; the `diff-cover` gate present in Gate 1; a `SEC` or `REV` row surviving the merge and read by the *next* `/feature-start`.

**Known update-path issue to confirm:** Astraeus's `.claude/state.md` is customized (the two-state-files note), so the update will **SKIP** it — meaning `PR:` and `Gated baseline:` won't arrive. Confirm the TEMPLATE-CHANGED advisory names both fields precisely enough to add by hand, since `--force` would discard the customization.

---

## Self-review

**Design coverage** — all twelve findings mapped: F1 → T1, T2 · F2 → T4 · F3 → T3 · F4 → already fixed (`fd5cafd`) · F5 → T8 · F6, F7 → T9 · F8 → T10 · F9 → T11 · F10 → T12 · F11 → T6 (discovery) + T13 (execution) · F12 → T7 Step 2 (the generalizable lesson; the `# noqa: T201` residue is deliberately **not** actioned, since devkit does not currently lint the hook). ADR-0005 Fix 4 (sentinels) → T5. ADR-0006 A → T14, T15 · B → T16, T17, T18 · C → T17 Step 1 · D → T19 + T20.

**Placeholder scan** — clean. Task 1 Step 1 and Task 14 Step 2 specify *what to extract/author* rather than quoting final prose, because both are extractions from sources the implementer must read; every other step carries literal replacement text and an exact anchor.

**Type consistency** — contract strings spelled identically throughout: `**Gated baseline:** —`, `<!-- devkit:pr-review handled:<comment-id> -->`, `.claude/references/spec-and-plan-depth.md`, `.claude/references/claude-md-elements.md`, `docs/findings.md`, and the `CONF`/`SEC`/`ARCH`/`REV` prefixes.

**Ordering** — no task consumes an interface a later task produces. T2's guard runs after T1 removes the two known violations and before T3 removes the third (T3 Step 5 re-runs it). T13 consumes T6's recorded gate list. T17 consumes T16's row format. T18 consumes T16.

**Scope check** — 20 tasks across three phases is large for one plan, and the phases are separable: each ends in a coherent, independently valuable state. If execution stalls, Phase 1 alone unblocks brownfield adoption and is worth landing on its own.
