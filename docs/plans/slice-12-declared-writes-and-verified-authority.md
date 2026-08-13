---
slice: 12
status: draft
design: docs/design/0009-declared-writes-and-verified-authority.md
---

# Slice 12 — Declared Writes, Discovered Locations, and Verified Authority: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close all seventeen findings from the pack's first end-to-end execution and the PR #140 static review by applying ADR-0008's clauses as enforced rules rather than as a patch list, and by adding the two clauses that round has shown to be missing.

**Architecture:** Two new reference files (`artifact-locations.md`, `evidence-and-uncertainty.md`), one new test (`tests/test_clause_one.py`), one new `/plan` phase (F3), and edits across nine existing pack files. No new subagent, no new command, no new hook — the slice composes primitives the pack already has. The only executable deliverable is the test; everything else is markdown validated by behavioral prediction.

**Tech Stack:** Markdown pack content (Claude Code `SKILL.md` / command / reference / agent formats); stdlib `unittest` (no pytest — the pack installs into arbitrary projects and cannot assume a runner); `install.sh` + `install_lib.py` for packaging.

---

## Global Constraints

Copied from `docs/design/0009-declared-writes-and-verified-authority.md` and this project's `CLAUDE.md`. Every task's requirements implicitly include this section.

- **Native-first.** No new primitive. If an existing component can host the behavior, that is the answer.
- **Clause 5 applies to this plan's own execution.** Verify every path, symbol, and line number against source before asserting it. Where a choice is arguable, decide and state the reasoning; escalate only when the answer turns on the user's priorities.
- **Never `git add -A` / `git add .`** — stage each task's files explicitly.
- **Propose before writing** for any durable-doc edit, per the `documenter` skill's cardinal discipline.
- **Design docs are the contract.** If implementation diverges from ADR-0009, update ADR-0009 with rationale in the same commit. Do not allow silent divergence.
- **No new durable artifact per feature.** ADR-0009 adds two *reference* files (pack-tracked, shared) and no per-feature artifact.
- **Line numbers in this plan were verified on 2026-08-12** against the working tree at commit `3575048`. They will drift as tasks land. Re-grep before editing; treat the quoted text as authoritative and the line number as a hint.
- **Out of scope, explicitly:** the `debugger` skill and the fan-out `reviewer` gate (both slice 13); artifact dispositions and `/devkit-reconcile` (slice 10); behavioral validation of the `/feature-merge` `in-review` re-entry path (needs a live PR, tracked separately).

### The test cycle for this project

This repo authors markdown. Per `CLAUDE.md` working principle 4, the test analogue for a markdown task is a **behavioral prediction plus a fresh-session run**:

1. Before authoring, write the example task and the predicted behavior into `docs/validation/slice-12.md`.
2. Author the file.
3. Run the example task in a fresh Claude Code session with the pack loaded.
4. Compare actual to predicted. **If behavior diverges from prediction, the pack content needs revision — not the prediction.**

Task 4 is the exception: `tests/test_clause_one.py` is real code and gets real TDD.

Three mechanical checks are cheap enough to run per task:

```bash
# A — the whole suite (must stay green after every task)
python3 -m unittest discover -s tests

# B — installer picks up new/changed pack files (no writes; safe to re-run)
./install.sh "$(mktemp -d)" --dry-run

# C — every pack citation resolves in a target install
python3 -m unittest tests.test_pack_references_resolve -v
```

---

## File Structure

**Created:**

| File | Responsibility |
|---|---|
| `pack/references/artifact-locations.md` | The one copy of the discover→confirm→record→cite procedure for specs, plans, and summaries. Generalizes `adr-registry.md` from one artifact type to four. |
| `pack/references/evidence-and-uncertainty.md` | The one copy of clause 5: facts carry provenance, judgment calls are decided, and the discriminator between them. |
| `tests/test_clause_one.py` | Enforces clause 1 mechanically: write-phases declare, declarations have carriers. |
| `docs/validation/slice-12.md` | Behavioral predictions, recorded before authoring and unrun until the dogfood. |
| `pack/templates/history/0.12.0/` | Seeded-template snapshot for the release guard. |

**Modified:**

| File | Change |
|---|---|
| `pack/commands/plan.md` | Phase F3 (new); Phase F2 third disposition; *Approach* emits the gate list; `Writes:` lines; path citations |
| `pack/skills/engineer/SKILL.md` | Verify substep 3 (gate list); tester dual output; `related_adrs` linking; clause-5 citations; path citations |
| `pack/commands/feature-start.md` | Phase E/H `Writes:` + derived staging; path citations |
| `pack/commands/feature-merge.md` | `in-review` preconditions (3 defects); gate-rerun row `Writes:`; path citations |
| `pack/agents/architect.md` | Silence-is-not-an-input; stale slice-2 note; verify-before-reflect |
| `pack/agents/conformance-reviewer.md`, `tester.md`, `security-reviewer.md` | Path citations |
| `pack/skills/pm/SKILL.md`, `documenter/SKILL.md` | Path citations; clause-5 citations; three-strikes generalization |
| `pack/references/adr-registry.md` | Scan scope includes the recorded location |
| `pack/references/clean-architecture-layers.md` | Verbatim-triplicate line becomes a citation |
| `pack/commands/pr-review.md`, `adopt.md`, `checkpoint.md` | `Writes:` lines; clause-5 citations |
| `pack/state.md.template`, `pack/MIGRATIONS.md`, `VERSION` | Release |
| `pack/devkit-orientation.md`, `README.md` | Path citations; new references listed |
| `install.sh` | Restart guidance narrowed |
| `docs/design/inventory-and-build-order.md`, `CLAUDE.md` | Slice-12 entry; slice-9 → slice-13 renumber |

---

# Phase A — Clause 4 and the gate list

Both findings here are severity-high, both are mechanical, and both would have paid for themselves inside the single feature that found them. Phase A has no dependency on B–E and is independently shippable.

## Task 1: `/plan` Phase F3 — symbol verification

Closes flow-6 (high). The plan declares its type signatures authoritative and nothing verifies them; five wrong symbols shipped in one six-step feature.

**Files:**
- Modify: `pack/commands/plan.md` — insert a new `### Phase F3` between Phase F2 (`:115`) and Phase G (`:132`)
- Modify: `docs/validation/slice-12.md` — the prediction

**Interfaces:**
- Consumes: Phase F2's completed conformance review (F3 runs after, so a plan revised for a blocking finding is the one whose symbols get checked).
- Produces: a halt condition that Phase G's commit step depends on — F3 must pass before the plan is proposed for approval.

- [ ] **Step 1: Write the behavioral prediction**

Append to `docs/validation/slice-12.md`:

```markdown
### Prediction T1 — Phase F3 halts on an unresolvable symbol

**Setup:** A plan whose Step 2 signature block names `CaseLayout` where the
codebase defines `ReconciliationCaseLayout`, and whose conventions table names
`build_manifest_conflict_detail` where the codebase defines `manifest_409_detail`.

**Predicted:** `/plan` reaches Phase F3, reports both names as UNRESOLVED with the
near-miss suggestion for the first, and does **not** proceed to Phase G's commit
proposal until the plan is corrected. The conventions-table name is caught, not
just the signature-block one.

**Why this is the prediction that matters:** the mid-feature partial fix covered
signature blocks only, and instance five was in the conventions table.
```

- [ ] **Step 2: Author Phase F3**

Insert into `pack/commands/plan.md` immediately after Phase F2's closing line (`You wrote this plan. That is exactly why you are not the one checking it…`):

```markdown
### Phase F3 — Symbol verification

Phase F2 asked whether the plan contradicts the spec. This phase asks a different question: **do the things this plan names actually exist?**

The `engineer` skill states the plan's status plainly — *"The signatures are authoritative. If the signatures are wrong, the tester writes the wrong tests."* Nothing downstream can check that. `conformance-reviewer` has no codebase access by design; `tester` is forbidden implementation source; `engineer` finds out at red, after the tester has already spent its context on a contract that cannot compile. This phase is the only place the plan's claims meet the codebase.

**Enumerate every symbol the plan names**, from all three places they appear:

1. **Type signature blocks** — every type, parameter type, and return type.
2. **The conventions table** — every function, method, helper, and constant.
3. **Prose** — any identifier that names real code, including ones mentioned only in a step's narrative.

Scope by *what names code*, not by *what sits in a signature block*. The narrow version of this rule has already failed once: a mid-feature correction restricted to signature blocks let a wrong name through in the conventions table.

**Confirm each against the codebase.** A plain identifier search is enough — a false "resolved" is not possible, and a false "unresolved" costs one look. Report:

```
RESOLVED    ReconciliationCaseLayout        src/layouts.py:41
UNRESOLVED  CaseLayout                      -- nearest: ReconciliationCaseLayout
UNRESOLVED  build_manifest_conflict_detail  -- no match
```

Where a name does not resolve, offer the nearest match if there is a plausible one. Most instances are a shortened or remembered form of a real symbol rather than an invention.

**Halt on any UNRESOLVED.** Do not carry an unresolved name into Phase G. Either correct the plan, or — if the symbol is genuinely new code this plan introduces — mark it explicitly in the plan as *introduced by this plan* so the next reader can tell a deliberate new name from a wrong one. That distinction is the whole output of this phase.

**Symbols the plan introduces are not failures.** A plan for new code names things that do not exist yet, and that is correct. What this phase catches is a name that was *meant* to match existing code and doesn't.
```

- [ ] **Step 3: Verify citations still resolve**

Run: `python3 -m unittest tests.test_pack_references_resolve -v`
Expected: PASS (Phase F3 adds no new citation, but the suite must stay green)

- [ ] **Step 4: Verify the installer picks up the change**

Run: `./install.sh "$(mktemp -d)" --dry-run`
Expected: `plan.md` listed among tracked files; no error

- [ ] **Step 5: Commit**

```bash
git add pack/commands/plan.md docs/validation/slice-12.md
git commit -m "pack: /plan Phase F3 verifies the plan's symbols before approval

Closes flow-6. The plan is declared authoritative for what the tester writes
and had no verification pass; five wrong symbols shipped in one feature.
Enumeration is scoped by what names code, not by what sits in a signature
block -- the narrow rule is the one that already failed at instance five."
```

## Task 2: `engineer` Verify substep 3 reads the recorded gate list

Closes flow-7 (high). Clause 3 already names the blocking-gate list; `/adopt` records it and `/feature-merge` Gate 1 consumes it correctly. The per-step consumer does not.

**Files:**
- Modify: `pack/skills/engineer/SKILL.md:57` (Verify substep 3)
- Modify: `docs/validation/slice-12.md`

**Interfaces:**
- Consumes: the **Blocking gates** list in `CLAUDE.md` conventions, written by `/adopt` Phase A (`adopt.md:43`), in exactly the form `/feature-merge:85` already reads.
- Produces: nothing new for later tasks; Task 3 makes the same list reachable from the plan.

- [ ] **Step 1: Write the behavioral prediction**

Append to `docs/validation/slice-12.md`:

```markdown
### Prediction T2 — the build loop runs the project's fourth gate

**Setup:** A project whose `CLAUDE.md` conventions record four blocking gates
(ruff, mypy ratchet, pytest, `diff-cover --fail-under=85`). Run one `/build` step
whose change lowers diff coverage below 85%.

**Predicted:** the step's Verify substep 3 runs all four recorded commands, the
coverage gate fails inside that step, and the engineer fixes it with that step's
code still in context — rather than the failure surfacing at `/feature-merge`
Gate 1 across six steps of diff.
```

- [ ] **Step 2: Replace substep 3**

In `pack/skills/engineer/SKILL.md`, replace:

```markdown
3. Run the linter and type-checker if the project uses them. Identify them from `CLAUDE.md`, `pyproject.toml`, `package.json`, etc. If unclear, ask.
```

with:

```markdown
3. **Run the project's gates.** If `CLAUDE.md` conventions record a **Blocking gates** list (written by `/adopt`), run exactly that list, in order — it is the whole of this substep. Do not add your own lint or type-check on top: the list already contains whatever the project blocks on, and adding to it risks running a *different* lint profile than CI does, or running the same step twice. Only when no such list exists do you infer the runner and checks from the plan's *Approach* section or from project config (`pyproject.toml`, `package.json`, `Cargo.toml`) — and when you infer, **say that you are inferring**.

   This is the same rule `/feature-merge` Gate 1 follows, for the same reason, and it is the per-step half of it. A gate that only runs at merge is a gate you learn about across the whole feature's diff instead of in the step that broke it. The first brownfield target had four blocking gates where this loop ran two; the missing one was a diff-coverage threshold, which surfaced after step 6 at 80% and cost six new tests written against code from several different steps.
```

- [ ] **Step 3: Verify the suite is green**

Run: `python3 -m unittest discover -s tests`
Expected: `OK` (42 tests as of `3575048`)

- [ ] **Step 4: Commit**

```bash
git add pack/skills/engineer/SKILL.md docs/validation/slice-12.md
git commit -m "pack: engineer's verify step runs the project's recorded gates

Closes flow-7. Clause 3 names the blocking-gate list; /adopt records it and
/feature-merge Gate 1 reads it. The per-step consumer -- the one that runs six
times a feature -- hardcoded two tools. One clause, three consumers, two wired."
```

## Task 3: `/plan` emits the gate list as a per-step verify command

The other half of flow-7: the knowledge was captured at plan time and never reached the loop.

**Files:**
- Modify: `pack/commands/plan.md` — Phase F's plan-writing instruction (`:85-114`), the *Approach* section contents

**Interfaces:**
- Consumes: the same `CLAUDE.md` **Blocking gates** list Task 2 reads.
- Produces: a plan whose *Approach* section carries a literal per-step verify command, which `engineer` Verify substep 3 (Task 2) falls back to when no `CLAUDE.md` list exists.

- [ ] **Step 1: Add the gate-list requirement to Phase F**

In `pack/commands/plan.md` Phase F, in the list of what the plan's *Approach* section must contain, add:

```markdown
- **The per-step verify command.** Copy the project's **Blocking gates** list from `CLAUDE.md` conventions verbatim into the *Approach* section as the command each step's Verify substep runs. If no list is recorded, state the inferred commands and mark them as inferred.

  Recording the gate in a *Framework constraints* table is not enough — that happened on the first full run, complete with the gate's caveat and its exact reproduction command, and the build loop still never ran it. A constraint the loop does not read is a constraint the loop does not have.
```

- [ ] **Step 2: Verify the suite is green**

Run: `python3 -m unittest discover -s tests`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add pack/commands/plan.md
git commit -m "pack: /plan puts the gate list where the build loop reads it

The other half of flow-7. The gate was recorded at plan time in a Framework
constraints table and never reached the loop; the Approach section is what
engineer's Verify substep actually reads."
```

---

# Phase B — Clause 1 by construction

Test first. This is the one phase with a real executable deliverable, and the test is written before the `Writes:` lines exist so that it goes red for the right reason.

## Task 4: `tests/test_clause_one.py`

**Files:**
- Create: `tests/test_clause_one.py`

**Interfaces:**
- Consumes: `pack/commands/*.md` and `pack/skills/*/SKILL.md` as text.
- Produces: two test methods — `test_write_phases_declare_writes` and `test_declared_writes_have_a_carrier` — that Task 5 and Task 6 must make pass. The exemption marker string `**Clause 1 exception:**` is the contract between this test and any command that legitimately writes without a carrier.

- [ ] **Step 1: Write the failing test**

Create `tests/test_clause_one.py`:

```python
"""Clause 1 of ADR-0009: an artifact and its carrier are written in the same step.

A phase that produces a durable artifact declares it with a `**Writes:**` line,
and the command containing that phase has a step that stages what was declared.

The exemption is declared in the file, not here. ADR-0008 requires a command
that falls outside clause 1 to say so in its own text; this test looks for that
statement rather than carrying a hardcoded allowlist, because an allowlist here
would be exactly the cached-discovery failure clause 3 forbids.
"""

import re
import unittest
from pathlib import Path

PACK = Path(__file__).resolve().parent.parent / "pack"

# Data, not structure: revise this list without redesigning the test.
WRITE_MARKERS = (
    "write ",
    "writes ",
    "write the",
    "record ",
    "records ",
    "append ",
    "amend ",
    "draft ",
    "stamp ",
    "allocate and write",
)

PHASE_HEADING = re.compile(r"^#{2,4}\s+(Phase|Gate|Step)\s+\S+.*$", re.MULTILINE)
WRITES_LINE = re.compile(r"^\*\*Writes:\*\*\s+\S", re.MULTILINE)
EXCEPTION = "**Clause 1 exception:**"
STAGING = re.compile(r"git add|Stage (these|the) files|staging list", re.IGNORECASE)


def pack_documents():
    """Every command and skill file, as (path, text) pairs."""
    yield from ((p, p.read_text()) for p in sorted(PACK.glob("commands/*.md")))
    yield from ((p, p.read_text()) for p in sorted(PACK.glob("skills/*/SKILL.md")))


def phase_sections(text):
    """Split a document into (heading, body) pairs, one per phase heading."""
    matches = list(PHASE_HEADING.finditer(text))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield match.group(0).strip(), text[match.end():end]


class TestClauseOne(unittest.TestCase):
    def test_write_phases_declare_writes(self):
        """A phase whose body describes a durable write declares it."""
        offenders = []
        for path, text in pack_documents():
            if EXCEPTION in text:
                continue
            for heading, body in phase_sections(text):
                lowered = body.lower()
                if not any(marker in lowered for marker in WRITE_MARKERS):
                    continue
                if not WRITES_LINE.search(body):
                    offenders.append(f"{path.relative_to(PACK.parent)} :: {heading}")
        self.assertEqual(
            [],
            offenders,
            "Phases describe a durable write with no `**Writes:**` declaration:\n  "
            + "\n  ".join(offenders),
        )

    def test_declared_writes_have_a_carrier(self):
        """A document that declares writes has a step that stages them."""
        offenders = []
        for path, text in pack_documents():
            if EXCEPTION in text:
                continue
            if not WRITES_LINE.search(text):
                continue
            if not STAGING.search(text):
                offenders.append(str(path.relative_to(PACK.parent)))
        self.assertEqual(
            [],
            offenders,
            "Documents declare `**Writes:**` with no staging step:\n  "
            + "\n  ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tests.test_clause_one -v`
Expected: FAIL on `test_write_phases_declare_writes`, listing the phases that describe writes and carry no `**Writes:**` line — including at minimum `feature-start.md :: ### Phase D — Spec draft`, `### Phase E — ADRs (if any)`, and `plan.md :: ### Phase F — Write plan + update state.md`.

If it fails on a phase that does *not* actually write anything, the `WRITE_MARKERS` list is too broad — narrow the marker, not the assertion.

- [ ] **Step 3: Commit the red test**

```bash
git add tests/test_clause_one.py
git commit -m "test: clause 1 -- write-phases declare, declarations have carriers

Red until Task 5 adds the Writes: lines. The exemption is read from the file
rather than allowlisted here: ADR-0008 requires a command outside clause 1 to
state so in its own text, and an allowlist in the test would be the cached-
discovery failure clause 3 forbids."
```

## Task 5: `Writes:` declarations across every artifact-producing phase

Makes Task 4's first assertion pass.

**Files:**
- Modify: `pack/commands/feature-start.md` (Phases D, E, F, G, H)
- Modify: `pack/commands/plan.md` (Phases C, F, F2, G)
- Modify: `pack/commands/adopt.md` (Phases C, D, E, F)
- Modify: `pack/commands/checkpoint.md` (Phases C, D)
- Modify: `pack/commands/pr-review.md` (Phases C, D)
- Modify: `pack/commands/feature-merge.md` (Gate 2, Gate 3, closeout)
- Modify: `pack/commands/claude-md-merge.md` (the clause-1 exception statement)

**Interfaces:**
- Consumes: `tests/test_clause_one.py`'s `WRITES_LINE` pattern — the line must start `**Writes:**` at column 0 and be non-empty.
- Produces: the declarations Task 6's derived staging lists read.

- [ ] **Step 1: Add a `Writes:` line to each artifact-producing phase**

The format is one line, placed at the end of the phase body, naming each artifact and separated by `·`. Examples, using the exact phases they belong to:

`feature-start.md` Phase D — Spec draft:

```markdown
**Writes:** the spec at its discovered path (`.claude/references/artifact-locations.md` § *Specs*)
```

`feature-start.md` Phase E — ADRs (if any):

```markdown
**Writes:** the ADR at its discovered path · the `CLAUDE.md` high-water mark updated by step 4
```

`feature-start.md` Phase G — State update:

```markdown
**Writes:** `.claude/state.md`
```

`plan.md` Phase F — Write plan + update state.md:

```markdown
**Writes:** the plan at its discovered path · `.claude/state.md`
```

`plan.md` Phase F2 — Conformance review:

```markdown
**Writes:** the findings ledger, when an advisory is left outstanding as a `CONF` row (its path is discovered, not assumed)
```

`feature-merge.md` Gate 2 — Docs reconciliation:

```markdown
**Writes:** whatever docs the reconciliation amends — summary, domain docs, spec or plan amendments
```

`feature-merge.md` Gate 3 — Security review:

```markdown
**Writes:** the findings ledger, when the review produces non-critical `SEC` rows
```

Apply the same treatment to every other phase Task 4's red output named. **The Phase E `CLAUDE.md` high-water mark is the specific omission flow-1 found** — do not skip it.

- [ ] **Step 2: State the clause-1 exception in `claude-md-merge.md`**

`/claude-md-merge`'s preconditions require only `CLAUDE.md` and `.claude/devkit-orientation.md` — no git repo — so per ADR-0008 it falls outside clause 1 and must say so. Add near the top of `pack/commands/claude-md-merge.md`:

```markdown
**Clause 1 exception:** this command may run before a project is a git repository — its preconditions require only `CLAUDE.md` and `.claude/devkit-orientation.md`. With no repo there is no carrier commit to propose, so ADR-0008 clause 1 does not apply here and this command names no staging step. The user commits at their own cadence. Stating the exception is required: an unstated one is indistinguishable from the oversight the clause exists to catch.
```

- [ ] **Step 3: Run the test to verify the first assertion passes**

Run: `python3 -m unittest tests.test_clause_one -v`
Expected: `test_write_phases_declare_writes` PASSES. `test_declared_writes_have_a_carrier` may still fail — Task 6 closes it.

- [ ] **Step 4: Commit**

```bash
git add pack/commands/feature-start.md pack/commands/plan.md \
        pack/commands/adopt.md pack/commands/checkpoint.md \
        pack/commands/pr-review.md pack/commands/feature-merge.md \
        pack/commands/claude-md-merge.md
git commit -m "pack: every artifact-producing phase declares what it writes

Clause 1 by construction, taking the alternative ADR-0008 considered and
deferred at 'two staging lists, three lines each.' Execution found two more.
/claude-md-merge states its exception rather than leaving it implicit."
```

## Task 6: Staging lists derive from declarations

Closes flow-1 and pr140-3, and makes Task 4's second assertion pass.

**Files:**
- Modify: `pack/commands/feature-start.md:108` (Phase H staging list)
- Modify: `pack/commands/feature-merge.md:24` (gate-rerun row)
- Modify: `pack/commands/plan.md:134` (Phase G — already correct; restate as derived)

**Interfaces:**
- Consumes: the `**Writes:**` declarations from Task 5.
- Produces: nothing downstream; this is the terminal half of clause 1.

- [ ] **Step 1: Rewrite `feature-start.md` Phase H's staging list**

Replace the opening sentence of Phase H:

```markdown
Before the pause, propose a single commit for the artifacts this invocation produced: the spec, any Phase-E ADRs, and the Phase-G `.claude/state.md` updates.
```

with:

```markdown
Before the pause, propose a single commit for **the union of every `**Writes:**` declaration this invocation produced** — read them off the phases that ran rather than from a list maintained here. On a full run that is the spec (Phase D), any ADRs and the `CLAUDE.md` high-water mark (Phase E), and `.claude/state.md` (Phase G).

The `CLAUDE.md` high-water mark is the one this list used to omit. Phase E step 4 exists specifically to stop the recorded mark decaying into a wrong one; leaving it uncommitted un-does step 4, and the next `/feature-start` re-reads the stale number the update was written to fix.
```

- [ ] **Step 2: Rewrite `feature-merge.md`'s gate-rerun row**

Replace, in the entry-state table:

```markdown
| `in-review`, PR open, **gated content changed** | Re-run gates 1–3 — the PR carries changes no gate has seen — then update `Gated baseline`, commit `.claude/state.md` only, and push (same recipe as *PR creation*'s transition commit, below). Do **not** re-create the PR. |
```

with:

```markdown
| `in-review`, PR open, **gated content changed** | Re-run gates 1–3 — the PR carries changes no gate has seen. **Commit whatever the gates wrote first** (Gate 2's doc reconciliation, Gate 3's `SEC` rows — see each gate's `**Writes:**`), *then* update `Gated baseline` and commit `.claude/state.md` alone, and push. Two commits, in that order: the baseline must name a tip whose content includes the gates' own output, and the transition commit must touch only `state.md` or the next invocation's discriminator is not quiet. Do **not** re-create the PR. |
```

- [ ] **Step 3: Restate `plan.md` Phase G as derived**

Phase G is already correct — it names the ledger. Change it from an enumeration to a derivation so it cannot drift:

```markdown
Before the pause, propose a single commit for **the union of every `**Writes:**` declaration this invocation produced**. On a full run that is the plan and `.claude/state.md` (Phase F), any Phase-C ADRs, and the findings ledger if Phase F2 recorded a `CONF` row (its path is the discovered one, not assumed).
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests`
Expected: `OK` — both clause-1 assertions now pass, and the other 42 tests are unaffected.

- [ ] **Step 5: Commit**

```bash
git add pack/commands/feature-start.md pack/commands/feature-merge.md pack/commands/plan.md
git commit -m "pack: staging lists derive from Writes: declarations

Closes flow-1 (Phase H omitted the CLAUDE.md high-water mark Phase E step 4
mandates) and pr140-3 (the gate-rerun row committed state.md only, stranding
Gate 2's docs and Gate 3's SEC rows -- a clause-1 violation in the clause-1
release). Both are now derived rather than restated."
```

## Task 7: `MIGRATIONS.md` entries become anchored replacements

Closes pr140's unnumbered finding. An entry saying "replace paragraph X" is destructive when the reader's paragraph X grew a sentence the replacement omits.

**Files:**
- Modify: `pack/MIGRATIONS.md` — the *How to apply* section

**Interfaces:**
- Consumes: `tests/test_migrations_snapshot.py`, which already guarantees a template diff is looked at.
- Produces: the entry format Task 18's 0.12.0 entries must follow.

- [ ] **Step 1: Add the entry-format rule**

Append to `pack/MIGRATIONS.md`'s *How to apply* section:

```markdown
## How entries are written

Each entry **names the template hunk it corresponds to** and replaces the **smallest anchored unit** that carries the change — a sentence or a field line, not a whole paragraph.

The asymmetry is the reason. An entry that says too much is merely redundant. An entry that says too little **silently deletes**: "replace paragraph X" is destructive when your paragraph X grew a sentence the replacement omits, and neither you nor the pack will notice. That happened in 0.11.0's `Open questions` entry, which replaced a paragraph and dropped a sentence the template still keeps.

Naming the hunk also makes the snapshot diff and the migration list cross-checkable by reading rather than by recollection — which is what the release step in this project's `CLAUDE.md` asks for, and what the 0.10.0 entry failed at.
```

- [ ] **Step 2: Run the suite**

Run: `python3 -m unittest discover -s tests`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add pack/MIGRATIONS.md
git commit -m "pack: migration entries are anchored, hunk-named replacements

Closes pr140's unnumbered finding. 'Replace paragraph X' deletes silently when
the reader's paragraph X grew a sentence; an over-long entry is merely
redundant. The failure mode is asymmetric, so the format should be too."
```

---

# Phase C — Clauses 3 and 5

The two sweeps are one phase because they rewrite the same files: `architect.md`, `pm/SKILL.md`, and `engineer/SKILL.md` each carry sites from both.

## Task 8: `pack/references/artifact-locations.md`

**Files:**
- Create: `pack/references/artifact-locations.md`

**Interfaces:**
- Consumes: nothing.
- Produces: the sections Task 9's 34 rewritten sites cite — `§ Discover`, `§ Confirm`, `§ Record`, `§ Name`. Task 9 depends on these exact section names.

- [ ] **Step 1: Write the reference**

Create `pack/references/artifact-locations.md`:

```markdown
# Artifact locations

Where this project's specs, plans, and summaries live, and how to find out rather than assume.

`adr-registry.md` is the same procedure for ADRs, which additionally have allocation semantics (floor-plus-one, re-scan before allocate). This file covers the three artifacts that have locations but no IDs. Cite it; do not restate it.

## Why this exists

A hardcoded `docs/plans/` is wrong in a way that does not error. On the first brownfield target, `docs/plans/` existed and held the project's *retired* plans, while its live ones were at `docs/ai/plans/` — recorded in `CLAUDE.md` explicitly. Writing to the default would have passed every precondition, satisfied every later step, and left the project with devkit plans in the tree it had deliberately migrated away from.

The precondition that missed it asked whether a *file* existed. The question that catches it is whether the *directory* belongs to someone else.

## Discover

Run once per invocation, before the first consumer.

1. **Read `CLAUDE.md` conventions first.** If `/adopt` recorded artifact homes, they are authoritative — use them and stop. Re-deriving what adoption settled risks contradicting it.
2. **Otherwise scan** for existing artifact directories: `docs/specs/`, `docs/plans/`, `docs/summaries/`, and any directory whose name contains `spec`, `plan`, `summary`, or `design` under `docs/` or the repo root.
3. **Rank by provenance, not by name.** A directory holding files the pack wrote is the pack's. A directory holding files it did not is the project's, whatever it is called.

Report exactly one of: a path per artifact type, or an explicit `"none found"`. Silence is not a result — a consumer cannot distinguish "no directory" from "did not look."

## Confirm

**An occupied namespace is a user decision, not a default.** When discovery finds a directory that exists and holds files the pack did not write, surface it and ask before writing. Offer the three real options: write alongside, write to a different path, or adopt the existing convention.

Do not resolve it by picking. The cost of guessing wrong is two vocabularies in one repo, which is expensive to unwind and invisible until someone notices.

## Record

Once confirmed, record the chosen locations in `CLAUDE.md` conventions so the next invocation reads instead of re-asking. This is the same treatment the ADR registry gets, for the same reason.

**The location may be recorded. The path may not be reconstructed.** See § *Name*.

## Name

Specs, plans, and summaries are named:

    <discovered-dir>/YYYY-MM-DD-<slug>.md

The date is the artifact's **creation** date and does not change when the artifact is amended — a spec drafted on the 10th and amended on the 20th keeps its 10th. The directory carries the type, so no type suffix is added.

**The date prefix is why every consumer must read the path rather than build it.** A slug alone is no longer enough to reconstruct a filename, which is deliberate: a path that can be derived will be derived, and the derivation is what put artifacts in the wrong directory. Read the path from `.claude/state.md`'s `Spec:` / `Plan:` fields, or from this discovery — never assemble it from a slug.

Domain docs (`docs/domains/<domain>.md`) are **not** dated: a domain doc is per-domain and long-lived, amended at every merge, so a creation date on it would assert something false. ADRs are not dated either — they carry a monotonic ID and `adr-registry.md` owns their discovery.
```

- [ ] **Step 2: Verify every citation in the new file resolves**

Run: `python3 -m unittest tests.test_pack_references_resolve -v`
Expected: PASS

- [ ] **Step 3: Verify the installer tracks it**

Run: `./install.sh "$(mktemp -d)" --dry-run`
Expected: `references/artifact-locations.md` appears in the tracked set. `TRACKED_DIRS` already covers `references/`, so no installer edit is needed — confirm rather than assume.

- [ ] **Step 4: Commit**

```bash
git add pack/references/artifact-locations.md
git commit -m "pack: artifact-locations reference -- discover, confirm, record, name

Clause 3's corollary applied to the three artifacts that have locations but no
IDs. adr-registry.md solved discovery-before-write for one artifact type; flow-4
is the same class hitting plans, which had no equivalent."
```

## Task 9: Date prefixes and the 34 citation sites

**Files:**
- Modify, with exact site counts verified 2026-08-12:
  - `pack/skills/pm/SKILL.md` — 8 sites (`:3`, `:8`, `:87`, `:213`, `:224`, `:320`, `:326`, `:343`)
  - `pack/skills/documenter/SKILL.md` — 7 sites (`:35`, `:36`, `:38`, `:102`, `:128`, `:129`, `:169`)
  - `pack/agents/conformance-reviewer.md` — 5 sites (`:17`, `:18`, `:59`, `:73`, `:74`)
  - `pack/commands/plan.md` — 3 sites (`:87`, `:93`, `:110`)
  - `pack/commands/feature-merge.md` — 3 sites (`:127`, `:137`, `:183`)
  - `pack/devkit-orientation.md` — 3 sites (`:37`, `:39`, `:45`)
  - `pack/commands/feature-start.md` — 2 sites (`:58`, `:100`)
  - `pack/agents/security-reviewer.md` — 2 sites (`:18`, `:20`)
  - `pack/agents/tester.md` — 1 site (`:15`)
- Modify: `pack/state.md.template` — the `Active feature` field-meaning line

**Interfaces:**
- Consumes: `artifact-locations.md` § *Discover*, § *Name* (Task 8).
- Produces: the seeded-file change Task 18's `MIGRATIONS.md` entry documents.

- [ ] **Step 1: Rewrite each site**

Three substitution shapes, by what the site is doing:

**A — a site that tells a component where to write.** Replace the constructed path with a citation:

```diff
-PM skill drafts `docs/specs/<slug>.md` to typical depth, with front-matter:
+PM skill drafts the spec at the path `.claude/references/artifact-locations.md` § *Discover* returned, named per § *Name*, to typical depth, with front-matter:
```

**B — a site that tells a component where to read.** Replace with the state field:

```diff
-- The active spec (`docs/specs/<feature>.md`)
+- The active spec — the caller passes its actual path, read from `.claude/state.md`'s `Spec:` field. Never reconstruct it from a slug; artifact filenames carry a date prefix.
```

**C — an illustrative example in prose or a template.** Keep it an example, make it correctly shaped:

```diff
-**Spec:** `docs/specs/<slug>.md`  ·  **Plan:** `docs/plans/<slug>.md`
+**Spec:** `<the path you were passed>`  ·  **Plan:** `<the path you were passed>`
```

Note the placeholder is currently inconsistent — some sites say `<slug>`, some `<feature>`. Do not preserve that; every rewritten site names the mechanism, not a placeholder.

- [ ] **Step 2: Update the seeded template's field meaning**

In `pack/state.md.template`, replace the single line:

```
  Active feature  short slug matching docs/specs/<slug>.md, or "none"
```

with:

```
  Active feature  short slug identifying the feature, or "none". The slug does
                  NOT determine the spec path -- artifact files carry a date
                  prefix (YYYY-MM-DD-<slug>.md) and live wherever discovery
                  found. Read Spec / Plan below for actual paths.
```

This is the only hunk in a seeded file, and Task 18 carries it to existing installs.

- [ ] **Step 3: Verify no constructed paths remain**

Run: `grep -rn "docs/specs/<\|docs/plans/<\|docs/summaries/<" pack/ --include=*.md`
Expected: no output.

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests`
Expected: `OK`. `test_pack_references_resolve` is the one that matters here — it proves the new citations resolve in a target install.

- [ ] **Step 5: Commit**

```bash
git add pack/skills/pm/SKILL.md pack/skills/documenter/SKILL.md \
        pack/agents/conformance-reviewer.md pack/agents/security-reviewer.md \
        pack/agents/tester.md pack/commands/plan.md \
        pack/commands/feature-merge.md pack/commands/feature-start.md \
        pack/devkit-orientation.md pack/state.md.template
git commit -m "pack: artifact paths are discovered and dated, never derived

Closes flow-4. 34 sites across 9 files constructed docs/specs/<slug>.md rather
than reading a path. The date prefix is the forcing function: a filename that
cannot be rebuilt from a slug makes discovery load-bearing instead of merely
recommended.

Seeded-file hunk: state.md.template's Active feature field meaning."
```

## Task 10: The ADR-registry consumers

Closes pr140-5, pr140-6, and pr140-7 — three defects in one flow.

**Files:**
- Modify: `pack/references/adr-registry.md` — § *Discover* → *Scope*
- Modify: `pack/agents/architect.md:22` — the "still answer" branch
- Modify: `pack/skills/engineer/SKILL.md:81` — build-time ADR linking

**Interfaces:**
- Consumes: `adr-registry.md` § *Allocate* (unchanged).
- Produces: a `related_adrs` front-matter guarantee that `security-reviewer.md:19` already depends on.

- [ ] **Step 1: Widen the registry scan scope (pr140-5)**

In `pack/references/adr-registry.md` § *Discover* → *Scope*, replace:

```markdown
`*.md` under `docs/`, plus root-level `*.md`.
```

with:

```markdown
`*.md` under `docs/`, plus root-level `*.md`, **plus any location `CLAUDE.md` conventions record for decisions** — scanned even when it falls outside those two.

The recorded location has to be in scope or the record is unreadable. § *Never cache the number* says the location may be recorded while the number may not be trusted; a scan that cannot reach `architecture/decisions/` or `.github/decisions/` reports "none found" for a project that told the pack exactly where to look, and the pack then creates a second registry — the duplicate-ID failure step 3 forbids.
```

- [ ] **Step 2: Delete the "still answer" branch (pr140-6)**

In `pack/agents/architect.md`, replace:

```markdown
  **Being passed nothing at all — no paths and no explicit "none found" — is different: that is a caller bug.** Name it in your response (the recommendation you're about to give was formed without reading decisions it may contradict), and still answer the question. Either way, do not go looking for the registry yourself — you cannot tell an empty one from an undiscovered one, and guessing is how a second registry gets created.
```

with:

```markdown
  **Being passed nothing at all — no paths and no explicit "none found" — is different: that is a caller bug, and you stop.** Name it and ask the caller to run discovery, rather than answering. A recommendation formed without reading decisions it may contradict is a guess about precedent, and this same sentence used to end by warning that *guessing is how a second registry gets created* — the warning applies to the recommendation as much as to the scan. One round-trip is cheap; a confidently wrong recommendation is expensive.

  Either way, do not go looking for the registry yourself. You cannot tell an empty registry from an undiscovered one.

  **Silence is not an input.** An explicit "none found" is a complete answer and you proceed on it; nothing at all is a missing answer and you ask for it. See `.claude/references/evidence-and-uncertainty.md`.
```

- [ ] **Step 3: Link build-time ADRs (pr140-7)**

In `pack/skills/engineer/SKILL.md`, after the existing sentence about allocating and writing a build-time ADR, add:

```markdown
Then **add the ADR's number to the applicable `related_adrs` front-matter** — the spec's if the decision changes the contract, the plan's otherwise — via `/checkpoint`, before continuing the build. `pm` does this at brainstorm time and `/feature-start` does it again; `engineer` is the one architect caller that writes an ADR without linking it. `security-reviewer` reads `related_adrs` at merge, so an unlinked build-time ADR is invisible to the review of the very architecture it authorized.
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add pack/references/adr-registry.md pack/agents/architect.md pack/skills/engineer/SKILL.md
git commit -m "pack: the ADR registry reaches all three of its consumers

pr140-5: discovery scans the location CLAUDE.md records, not just docs/.
pr140-6: silence is not an input -- architect asks rather than answering
without precedent, resolving the contradiction inside architect.md:22-25.
pr140-7: engineer links the ADR it writes, as pm and /feature-start already do."
```

## Task 11: `pack/references/evidence-and-uncertainty.md`

**Files:**
- Create: `pack/references/evidence-and-uncertainty.md`

**Interfaces:**
- Consumes: nothing.
- Produces: the sections Task 12's citation sweep points at — `§ Facts`, `§ Judgment`, `§ The discriminator`.

- [ ] **Step 1: Write the reference**

Create `pack/references/evidence-and-uncertainty.md`:

```markdown
# Evidence and uncertainty

Clause 5 of the pack's step invariants: **decide what is arguable; never assert what is unverified.**

The rule was already in the pack fourteen times in fourteen formulations before it had a name, and one sentence appeared verbatim in three files. Cite this; do not restate it. Each citing site keeps its own *specific* obligation — what counts as evidence there, what the round-trip costs there — and defers the shared rationale here.

## Facts

**Any assertion about the project carries its provenance.** A path, a symbol, a convention, a prior decision, what a file says — each is either backed by `file:line` evidence or explicitly marked as inferred.

Silence about provenance reads as verified. That is the whole failure mode: a confidently wrong assertion travels further than a hedged right one, because nothing about it announces that it was never checked. A fresh-context subagent's file:line claim is exactly what its caller cannot check from the reflection alone.

**Verify before reflecting.** When you pass another agent's factual claims onward — to the user, to a spec, to a plan — check the load-bearing ones against source first. Passing them on unchecked launders an inference into a fact.

## Judgment

**A question with two defensible answers gets decided, not escalated.** State the recommendation and the reasoning, then proceed.

Escalate when the answer turns on the user's priorities — what to build, what to trade away, what matters more. Do not escalate merely because a choice exists; a component that returns every fork to its caller is not being careful, it is being unhelpful.

**Name the branch you took, including the ordinary one.** A phase that lists two dispositions and omits the obvious third does not become neutral about the third — it pushes readers toward one of the two it named. Two findings came from exactly this: an advisory that was cheap to fix got framed as either "defer to the ledger" or nothing, and a subagent's most valuable output had no stated handling at all.

## The discriminator

**Can the repo answer it?**

| The question is… | Do this |
|---|---|
| Knowable from the code, the docs, or git | Go and know it. Never guess what you could read. |
| Arguable — two defensible engineering answers | Decide it, state why, proceed. |
| Dependent on what the user wants | Ask. One round-trip is cheap. |

`grill-me` states the first row in its sharpest form: *"If a question can be answered by exploring the codebase, explore the codebase instead."* The other two rows are the same instinct applied where the codebase cannot help.
```

- [ ] **Step 2: Verify citations resolve**

Run: `python3 -m unittest tests.test_pack_references_resolve -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add pack/references/evidence-and-uncertainty.md
git commit -m "pack: evidence-and-uncertainty reference -- clause 5 gets one copy

Owner-sourced rather than finding-sourced: the pack's purpose is to encode how
its owner works, and this is his stated principle. The evidence it belongs is
that the pack reached for it fourteen times without ever naming it."
```

## Task 12: The clause-5 citation sweep

**Files:** the fourteen sites, verified 2026-08-12:
- `pack/references/clean-architecture-layers.md:23`, `pack/skills/engineer/SKILL.md:71`, `pack/skills/pm/SKILL.md:67` — **the verbatim triplicate**
- `pack/agents/architect.md:25`, `pack/agents/tester.md:21`
- `pack/skills/engineer/SKILL.md:95`, `:221-223`
- `pack/skills/pm/SKILL.md:288`, `:357`, `:365`
- `pack/skills/documenter/SKILL.md:14`
- `pack/references/findings-triage.md:12`, `pack/references/spec-and-plan-depth.md:28`
- `pack/commands/plan.md:52`, `pack/commands/adopt.md:55`, `:159`
- `pack/commands/pr-review.md:57`, `pack/commands/feature-merge.md:32`

**Interfaces:**
- Consumes: `evidence-and-uncertainty.md` § *Facts*, § *Judgment*, § *The discriminator* (Task 11).
- Produces: nothing downstream.

- [ ] **Step 1: Collapse the verbatim triplicate**

The sentence *"Do not guess on architectural boundaries; the cost of getting it wrong propagates"* appears identically in three files. Keep it in `clean-architecture-layers.md:23` — the reference that owns the topic — and in the two skills replace it with a citation:

```diff
-Do not guess on architectural boundaries; the cost of getting it wrong propagates.
+Do not guess on architectural boundaries — see `.claude/references/evidence-and-uncertainty.md` § *The discriminator*. An architectural boundary is knowable from the code and the domain docs, which puts it in the first row: go and know it.
```

- [ ] **Step 2: Convert the remaining eleven sites**

**Leave each site's specific obligation in place. Replace only the shared rationale.** This is the risk ADR-0009 names: `tester.md:21`'s "don't read implementation source, return a finding instead" and `plan.md:52`'s "file:line citations, don't generalize from one file" are genuinely different obligations, and flattening them into one vague pointer trades fourteen precise statements for one useless one.

The shape:

```diff
-If any of the above is missing or unclear, **ask the caller a clarifying question instead of guessing**. One round-trip is cheap. A confidently wrong recommendation is expensive.
+If any of the above is missing or unclear, **ask the caller a clarifying question instead of guessing** — the specific obligation here is that a missing input is asked for, never inferred from the question's framing. Rationale: `.claude/references/evidence-and-uncertainty.md` § *Facts*.
```

- [ ] **Step 3: Verify citations resolve**

Run: `python3 -m unittest discover -s tests`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add pack/references/clean-architecture-layers.md pack/references/findings-triage.md \
        pack/references/spec-and-plan-depth.md pack/agents/architect.md \
        pack/agents/tester.md pack/skills/engineer/SKILL.md \
        pack/skills/pm/SKILL.md pack/skills/documenter/SKILL.md \
        pack/commands/plan.md pack/commands/adopt.md \
        pack/commands/pr-review.md pack/commands/feature-merge.md
git commit -m "pack: fourteen restatements of clause 5 become citations

Including the verbatim triplicate (clean-architecture-layers.md:23,
engineer:71, pm:67). Each site keeps its specific obligation and defers only
the shared rationale -- the extraction risk ADR-0009 names is trading fourteen
precise statements for one vague one."
```

## Task 13: The under-stated half

Closes flow-5 and flow-8 — both failures of clause 5's decide-and-recommend obligation.

**Files:**
- Modify: `pack/commands/plan.md` — Phase F2's `CONF`-row paragraph
- Modify: `pack/skills/engineer/SKILL.md:37` — the tester-findings sentence
- Modify: `pack/agents/tester.md` — one line inviting the dual output

**Interfaces:**
- Consumes: `.claude/references/findings-triage.md` (already cited by `engineer:37`).
- Produces: nothing downstream.

- [ ] **Step 1: Name the third advisory disposition (flow-5)**

In `pack/commands/plan.md` Phase F2, after the existing `CONF`-row paragraph, add:

```markdown
**An advisory you fix in the plan needs no row.** The ledger is for what you deliberately leave, not for what was cheaper to fix than to record. Three dispositions, not two: fix it now (preferred when cheap), defer it to a `CONF` row, or resolve it with the user. Prefer the first — a ledger full of postponed two-minute edits stops reading as a record of real decisions.

This matters because the phase's own best case is the un-named one. On the first full run all three advisories were cheap, all three were fixed in the plan, and a literal reader of the previous text would have deferred them instead.
```

- [ ] **Step 2: Reframe tester findings as a dual output (flow-8)**

In `pack/skills/engineer/SKILL.md`, replace:

```markdown
If the tester returns **findings instead of tests**, do not work around them and do not re-invoke with a looser brief. Evaluate them per `.claude/references/findings-triage.md` (internal source). Most tester findings mean the plan's type signatures are wrong or incomplete — which is a `/checkpoint` amendment, not a build-time improvisation.
```

with:

```markdown
**The tester returns two things, and the second one is not a fault.** Expect tests *plus* findings — observations about what the test list omits, fixtures that will break, paths the existing suite cannot distinguish. On the first full run this happened in every one of six steps, and one of them (a gate applied to one endpoint while a sibling method bypassed it) was the most valuable output of the whole feature. Findings arriving alongside green tests are the shape most likely to be skimmed.

Triage them per `.claude/references/findings-triage.md` (internal source):

- **In scope and cheap** → fix now, in this step.
- **A contract gap** — the plan's signatures are wrong or incomplete → `/checkpoint` amendment, not a build-time improvisation.
- **Out of scope for this feature** → the findings ledger, so it outlives the step.

If the tester returns **findings and no tests**, that is a refusal, and it means the brief was unbuildable. Do not work around it and do not re-invoke with a looser brief — fix the contract.
```

- [ ] **Step 3: Invite the dual output in the tester's own definition**

Add to `pack/agents/tester.md`, in its output section:

```markdown
**Report what the test list omits.** Alongside the tests you write, return any observation the list did not cover — a fixture the new code will break, a branch the existing suite cannot distinguish, a sibling method that looks like it shares the behavior under test but may not. This is expected output, not an exception path; you see the contract more closely than anyone downstream will.
```

- [ ] **Step 4: Run the suite and commit**

```bash
python3 -m unittest discover -s tests
git add pack/commands/plan.md pack/skills/engineer/SKILL.md pack/agents/tester.md
git commit -m "pack: name the branch that was missing -- fixed advisories, tester findings

flow-5 and flow-8, both clause 5's under-stated half. Phase F2 named two
dispositions for an advisory and the best one was the third. The tester's most
valuable output was framed as a refusal path and arrived, with green tests,
six times out of six."
```

---

# Phase D — `/feature-merge` `in-review` corrections

Three defects, one section, one file. **These are authored by reading, not running** — the `in-review` re-entry path has never executed, and this phase does not change that. It ships now because pr140-2 blocks closeout on any forge that auto-deletes head branches, which is the path slice 12's own dogfood must traverse.

## Task 14: The three `in-review` precondition defects

**Files:**
- Modify: `pack/commands/feature-merge.md:26-32` (the `in-review` preconditions block)

**Interfaces:**
- Consumes: the entry-state table's `in-review` rows (Task 6 already rewrote the gate-rerun row).
- Produces: nothing downstream.

- [ ] **Step 1: Reorder the merged-state check (pr140-2, high)**

Replace the preconditions preamble:

```markdown
The `in-review` rows have their own preconditions, checked **before** the discriminator runs:
```

with:

```markdown
**Check merged state first.** Before any other precondition, read `gh pr view --json state,mergedAt`. If the PR has merged, go straight to closeout (*After the merge*) — the preconditions below do not apply, and applying them breaks the closeout path outright.

The failure is specific: forges that delete the head branch on merge leave `git ls-remote origin <branch>` returning no OID. `git ls-remote -h` does not error on no-match unless `--exit-code` is passed, so precondition 2 sees an empty result rather than a failure, reads the local checkout as diverged, and **halts before the closeout that would have cleared state**. The halt list does mention a merged-state check; nothing ordered it before precondition 2.

The remaining preconditions apply **only while the PR is still open**, and are checked before the discriminator runs:
```

- [ ] **Step 2: Require tip equality (pr140-1, med — both reviewers)**

Replace precondition 2's opening:

```markdown
2. **Local and remote agree.** No uncommitted changes to tracked files, and the local branch is not ahead of the remote.
```

with:

```markdown
2. **Local and remote agree.** No uncommitted changes to tracked files, and local `HEAD` **equals** the OID `git ls-remote origin <branch>` reports — not merely "is not ahead of" it.

   Equality, because the check is directional otherwise and the missing direction is the common one. When another clone or the web UI pushes to the PR, local is **behind**, and a "not ahead" test passes. `git fetch` then makes the new tip available without moving `HEAD`, so the discriminator reads the PR's new content while gates 1–3 run against stale local content, and the state-only push that follows is a non-fast-forward. The stated rationale for this precondition is exactly that failure in mirror image: the discriminator reasons about the PR's remote content, and that framing is only correct when local and remote already agree. One-directional agreement is not agreement.

   On a mismatch in either direction, halt and report which it is. When local is behind, the fix is to update the checkout before re-running.
```

- [ ] **Step 3: Apply the untracked-file prompt to this path (pr140-4, high)**

Append to precondition 2:

```markdown
   **Untracked files are surfaced here too.** The building-phase path already handles this (*"An untracked file is as likely to be a source file the engineer forgot to `git add` … as it is to be build detritus"*) and the same reasoning applies with more force here: a review fix that adds a new source or test file and forgets to stage it leaves local `HEAD` equal to the remote OID, so this precondition passes, the gates run **green against a working tree containing the untracked implementation**, and the state-only commit pushes a `Gated baseline` the PR did not earn. Surface untracked files and ask before running any gate.
```

- [ ] **Step 4: Write the behavioral predictions**

Append to `docs/validation/slice-12.md`:

```markdown
### Prediction T14 — the in-review re-entry path (UNRUN — needs a live PR)

**T14a (pr140-2):** On a forge that auto-deletes head branches, re-run
`/feature-merge` after the PR merges. Predicted: closeout runs and clears state.
Previously: halts on precondition 2 with an empty `ls-remote` result.

**T14b (pr140-1):** Push a commit to the PR from a second clone, then re-run
`/feature-merge` locally. Predicted: halts, reporting local is *behind*.
Previously: passes, then gates stale content.

**T14c (pr140-4):** Leave an unstaged new test file in the tree and re-run.
Predicted: surfaced and asked about before any gate runs.

**These three are the largest body of never-executed text in the pack.** Slice
12 fixes them textually and does not validate them. The dogfood that settles
them is: reopen the PR, push a review fix from a second clone, re-run.
```

- [ ] **Step 5: Run the suite and commit**

```bash
python3 -m unittest discover -s tests
git add pack/commands/feature-merge.md docs/validation/slice-12.md
git commit -m "pack: three in-review precondition defects (pr140-1, -2, -4)

Merged-state check moves ahead of the sync precondition, which a deleted head
ref fails. Tip comparison becomes equality -- 'not ahead' passes when local is
behind, which is the common case. Untracked-file prompt applies to this path
as it already does to the building path.

Authored by reading. The in-review re-entry path has still never executed;
predictions T14a-c in docs/validation/slice-12.md are unrun."
```

---

# Phase E — Corrections, doc currency, release

## Task 15: The three documentation corrections

Closes flow-2, flow-3, flow-9. Batched into one commit, matching this project's precedent for grouped review findings.

**Files:**
- Modify: `pack/commands/feature-start.md` — the *Invoking the architect* section's slice-2 note
- Modify: `install.sh:576`
- Modify: `pack/skills/documenter/SKILL.md`

- [ ] **Step 1: Delete the stale slice-2 note and add verify-before-reflect (flow-2)**

In `pack/commands/feature-start.md`, delete the *Slice-2 simulation note* paragraph entirely — `subagent_type: architect` resolved correctly on first attempt during the full run, and the note invites a workaround that loses the architect's own system prompt. Replace it with:

```markdown
**Verify the architect's source claims before reflecting them.** The reflection step below is a *user* gate, not a *truth* gate: the user cannot check a fresh-context agent's confident `file:line` assertions from the reflection alone. Check the load-bearing ones against source first. On the first full run the architect surfaced five source-level claims, all of which held — and one of them (a prior ADR's override being unwired dead code) would have been expensive to pass on wrong. See `.claude/references/evidence-and-uncertainty.md` § *Facts*.
```

- [ ] **Step 2: Narrow the restart guidance (flow-3)**

In `install.sh`, replace line 576's text:

```bash
echo "  $step. Restart Claude Code so it picks up the new .claude/ contents."
```

with:

```bash
echo "  $step. Restart Claude Code if this install ADDED commands or skills --"
echo "     the slash-command index is built at startup. Changed bodies of"
echo "     existing commands and skills load fresh at invocation; no restart"
echo "     needed for those."
```

The blanket version over-warns, and an unnecessary instruction is one users learn to skip — then they skip it on the release that adds a command, which is when it was load-bearing. Verified during the 0.11.0 run: `Skill(pm)` and `Skill(grill-me)` both loaded 0.11.0 bodies mid-session with no restart.

- [ ] **Step 3: Generalize three-strikes to process defects (flow-9)**

In `pack/skills/documenter/SKILL.md`, add:

```markdown
**Three strikes on a class, not just on a bug.** The `engineer` skill stops after three failed hypotheses because repeated failures are evidence about the design rather than about the attempts. The same reasoning applies to amendments: when `/checkpoint` corrects the **same class** of defect for the third time in one feature, propose amending the process rule rather than the instance — and say so in the amendment.

On the first full run a symbol slip was corrected at instances 2, 3, and 5. At instance 3 a rule was written narrow enough that instance 5 slipped past it. Three `/checkpoint` commits treated one class as three unrelated cases, which is the failure this line exists to catch.
```

- [ ] **Step 4: Run the suite and the installer check**

```bash
python3 -m unittest discover -s tests
./install.sh "$(mktemp -d)" --dry-run
```
Expected: `OK`; installer runs without error and prints the narrowed restart text.

- [ ] **Step 5: Commit**

```bash
git add pack/commands/feature-start.md install.sh pack/skills/documenter/SKILL.md
git commit -m "pack: three documentation corrections (flow-2, flow-3, flow-9)

Stale slice-2 architect fallback deleted, replaced with verify-before-reflect.
Restart guidance narrowed to newly-added commands -- a blanket warning that is
usually unnecessary gets skipped on the release where it mattered.
Three-strikes generalized from bugs to process defects."
```

## Task 16: Doc currency — inventory, status, and the slice-9 renumber

**Files:**
- Modify: `docs/design/inventory-and-build-order.md` — add `### Slice 12`, add `### Slice 13`
- Modify: `CLAUDE.md` — Status section; the `:72` "Slice 9 — scoped but not authored" heading

- [ ] **Step 1: Add the slice-12 entry to the inventory**

Follow the shape of `### Slice 11 — Step invariants (post-core)` at `:278`. Cover: the five phases, the two new references, the new test, the version bump, and the dogfood that validates it.

- [ ] **Step 2: Renumber the deferred work to slice 13**

In `CLAUDE.md`, change the heading at `:72` from `**Slice 9 — scoped but not authored.**` to `**Slice 13 — scoped but not authored.**`, and add the fan-out decision:

```markdown
Multi-agent fan-out belongs here, not in the build loop: the loop is serialized on purpose (red → green → refactor, one user gate per step), while `reviewer` is defined by the cross-step lens no single component owns. Findings 6 and 7 of the 0.11.0 flow run were both single-lens misses, which is the evidence for placing it here.
```

Add a matching `### Slice 13` stub to `inventory-and-build-order.md`, which currently has no entry for it at all.

- [ ] **Step 3: Update the CLAUDE.md Status section**

Move slice 12 into *Shipped* with its unrun predictions noted, matching how slice 11 is described.

- [ ] **Step 4: Commit**

```bash
git add docs/design/inventory-and-build-order.md CLAUDE.md
git commit -m "docs: slice-12 inventory entry; deferred reviewer work becomes slice 13

CLAUDE.md used 'Slice 9' for two different things -- the built Enterprise API
findings slice and the unauthored debugger + reviewer pair, which the inventory
did not list at all. The latter becomes slice 13, carrying the decision that
multi-agent fan-out belongs to its reviewer gate."
```

## Task 17: Release 0.12.0

> **Corrected during execution (2026-08-12).** Steps 1–3 were **pulled forward into Task 9**, where the seeded-template change actually happens. As written, this task deferred the `MIGRATIONS.md` carrier two phases away from the artifact it carries — a clause-1 violation, in the slice that implements clause 1. The `test_migrations_snapshot` guard caught it by going red the moment T9 edited the template, which is the guard behaving exactly as ADR-0008 designed it.
>
> What remains here is verification: confirm no *later* task introduced a second seeded hunk, and that `VERSION`, the snapshot, and the entry still agree.

Follows the release cycle in this project's `CLAUDE.md`. **Step 1 is the one that matters** — the 0.10.0 failure was a migration entry written from recollection.

**Files:**
- Modify: `VERSION`, `pack/MIGRATIONS.md`
- Create: `pack/templates/history/0.12.0/`

- [ ] **Step 1: Diff the seeded templates against the last snapshot**

```bash
diff -u pack/templates/history/0.11.0/state.md.template pack/state.md.template
diff -u pack/templates/history/0.11.0/CLAUDE.md.template pack/CLAUDE.md.template
```
Expected: exactly one hunk — the `Active feature` field-meaning line from Task 9, Step 2. If any other hunk appears, **account for it before continuing**; an unaccounted hunk is the 0.10.0 failure repeating.

- [ ] **Step 2: Write the 0.12.0 migration entry**

Add to `pack/MIGRATIONS.md`, in the anchored, hunk-naming format Task 7 established:

```markdown
## 0.12.0

### `.claude/state.md`

- **Template hunk:** the `Active feature` line in the trailing HTML comment's field-meanings block.

  Replace this **one line**:

  ```
  Active feature  short slug matching docs/specs/<slug>.md, or "none"
  ```

  with:

  ```
  Active feature  short slug identifying the feature, or "none". The slug does
                  NOT determine the spec path -- artifact files carry a date
                  prefix (YYYY-MM-DD-<slug>.md) and live wherever discovery
                  found. Read Spec / Plan below for actual paths.
  ```

  Leave every other line in the block alone. Without this, your `state.md` tells a model it can rebuild the spec path from the slug — which 0.12.0 made false, deliberately, so that discovery is load-bearing rather than optional.

**Existing artifacts are not renamed.** Files already at `docs/specs/<slug>.md` keep their names and keep working; `state.md`'s `Spec:` / `Plan:` fields already hold real paths. The date prefix applies to artifacts created from 0.12.0 onward.
```

- [ ] **Step 3: Bump and snapshot**

```bash
echo "0.12.0" > VERSION
mkdir -p pack/templates/history/0.12.0
cp pack/*.template pack/templates/history/0.12.0/
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests`
Expected: `OK` — `test_migrations_snapshot` passes only if the snapshot exists for the current `VERSION`, byte-matches the live templates, and `MIGRATIONS.md` carries a `## 0.12.0` section.

- [ ] **Step 5: Commit**

```bash
git add VERSION pack/MIGRATIONS.md pack/templates/history/0.12.0/
git commit -m "release: 0.12.0

New tracked components (references/artifact-locations.md,
references/evidence-and-uncertainty.md), a seeded file's shape change (the
Active feature field meaning), and a new /plan phase.

One template hunk, one anchored migration entry naming it."
```

## Task 18: Close out the validation doc

**Files:**
- Modify: `docs/validation/slice-12.md`

- [ ] **Step 1: Add the carried-over predictions**

Two predictions carry over unresolved from the 0.11.0 round and must be stated here or they are lost:

```markdown
### Prediction T18a — clause 2's discriminator runs no gates (CARRIED FROM SLICE 11, STILL UNRUN)

Reopen the Enterprise API PR, change nothing, re-run `/feature-merge`.
**Predicted:** the content diff is quiet and **no** gates run. This branch has
been unreachable since `Gated baseline` was introduced and slice 11 has not
been dogfooded.

### Prediction T18b — the drift hook's unexplained miss (A LEAD, NOT A FINDING)

During the 0.11.0 run, `/feature-merge` Gate 2 caught two out-of-scope files
(`show_flights.py`, `CLAUDE.md`) that the `PostToolUse` drift hook did not warn
on. Nobody knows whether that is a hook gap or output lost in a long session.
**Predicted:** editing a file outside the active spec's `owned_files` produces a
visible warning at edit time. If it does not, the hook has a real gap and the
cheap layer of drift detection is not working.
```

- [ ] **Step 2: Record the summary table**

Add a table mapping all seventeen findings to the task that closed them and the prediction that validates them, so a future reader can tell "fixed and verified" from "fixed and unrun."

- [ ] **Step 3: Commit**

```bash
git add docs/validation/slice-12.md
git commit -m "docs: slice-12 behavioral predictions, recorded and unrun

Includes two carried over from slice 11 that would otherwise be lost: clause
2's no-gates-on-unchanged-PR branch, and the drift hook's unexplained miss."
```

---

## Self-Review

**Spec coverage.** All seventeen ADR-0009 findings map to a task: flow-6 → T1; flow-7 → T2, T3; flow-1 → T6; pr140-3 → T6; pr140-unnumbered → T7; flow-4 → T8, T9; pr140-5, -6, -7 → T10; pr140-6 also → T11, T12; flow-5, flow-8 → T13; pr140-1, -2, -4 → T14; flow-2, -3, -9 → T15. Clause 4 → T1. Clause 1 by construction → T4, T5, T6. Clause 3 sweep → T8, T9, T10. Clause 5 → T11, T12, T13. Release → T17. Slice-13 renumber → T16.

**Placeholder scan.** No "TBD", no "similar to Task N", no "add appropriate handling." Every edit quotes the exact text it replaces. The one deliberate deferral — behavioral validation of the `in-review` path — is named as such in T14 and in the Global Constraints, not left implicit.

**Type consistency.** The test's contract strings are used identically everywhere they appear: `**Writes:**` (T4 `WRITES_LINE`, T5, T6), `**Clause 1 exception:**` (T4 `EXCEPTION`, T5 Step 2). The reference section names T9 and T12 cite — `§ Discover`, `§ Confirm`, `§ Record`, `§ Name`, `§ Facts`, `§ Judgment`, `§ The discriminator` — are exactly the headings T8 and T11 create.

**Known ordering constraint.** T4 must land before T5 (red before green). T8 before T9, and T11 before T12 (the references must exist before anything cites them, or `test_pack_references_resolve` fails). Everything else is independent.
