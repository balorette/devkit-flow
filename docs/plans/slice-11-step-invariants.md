---
slice: 11
status: draft
design: docs/design/0008-step-invariants.md
findings: docs/validation/pr139-pack-findings.md
---

# Slice 11 — Step Invariants: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the eight pack findings from the Enterprise API 0.10.0 upgrade by landing ADR-0008's three step invariants — artifact transport, no self-referential state, discovery before consumers — and ship the result as 0.11.0.

**Architecture:** One new reference file (`pack/references/adr-registry.md`) absorbs a procedure currently restated in five components; one new test (`tests/test_migrations_snapshot.py`) plus an in-repo template snapshot makes seeded-file changes impossible to ship silently. Everything else is targeted edits to four commands, two skills, one subagent, and the orientation doc. No new command, no new subagent, no installer change — `TRACKED_DIRS` already covers `references/`, and `pack/templates/history/` is deliberately outside it.

**Tech Stack:** Markdown pack content (Claude Code `SKILL.md` / command / agent / reference formats); Python 3 stdlib `unittest` for the two guards; `install_lib.py` as the authority on what is tracked and what is a template.

---

## Global Constraints

Copied from `docs/design/0008-step-invariants.md` and this project's `CLAUDE.md`. Every task's requirements implicitly include this section.

- **The three clauses are the contract.** Clause 1: an artifact and its carrier are written in the same step. Clause 2: never infer "what changed" from state you wrote yourself. Clause 3: discovery precedes every consumer, once per invocation.
- **Native-first.** Slice 11 adds no new command and no new subagent.
- **Propose before writing.** No pack component silently applies a doc edit, a commit, or a merge. Edits in this slice must not weaken that.
- **Never `git add -A` / `git add .`** — stage each task's files explicitly.
- **Design docs are the contract.** Any divergence from ADR-0008 updates ADR-0008 with rationale in the same commit.
- **`docs/adr/` is a default, never an assumption.** After Task 2, no pack file states an ADR path except as the fallback when discovery found nothing.
- **Stdlib only** in `tests/`. The pack installs into arbitrary projects and cannot assume a runner; `python3 -m unittest discover -s tests` is the whole harness.
- **Out of scope, explicitly:** the disposition-aware manifest, `/devkit-reconcile`, and migration ordering/uniqueness checks — all ADR-0007 / slice 10. The `debugger` skill and `reviewer` subagent remain deferred.

### The test cycle for this project

Two mechanical guards now run per task:

```bash
python3 -m unittest discover -s tests -v          # both guards
./install.sh "$(mktemp -d)" --dry-run             # installer picks up new pack files
```

Markdown content has no automated test. Per `CLAUDE.md` working principle 4, the analogue is a **behavioral prediction plus a fresh-session run**: write the example task and predicted behavior *before* authoring, then run it in a fresh session. **If behavior diverges from prediction, the pack content needs revision — not the prediction.** Predictions are recorded in Task 13 and remain unrun until the Enterprise API dogfood.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `pack/references/adr-registry.md` | **Create** | The single copy of ADR-registry discovery and allocation. Cited by five components. |
| `tests/test_migrations_snapshot.py` | **Create** | Guard: a seeded template cannot change without its diff being surfaced. |
| `pack/templates/history/0.10.0/*.template` | **Create** | The 0.10.0 release baseline. Dev-tree only — not installed, not in the manifest. |
| `pack/templates/history/0.11.0/*.template` | **Create** (Task 14) | The 0.11.0 baseline, cut after all template edits land. |
| `pack/commands/feature-start.md` | Modify | Phase A discovery; Phase E cites the reference; architect contract passes discovered paths. |
| `pack/commands/plan.md` | Modify | Ledger joins Phase G staging; ADR citations. |
| `pack/commands/pr-review.md` | Modify | Metadata commit before push; `all`-mode filter; either/both contradiction. |
| `pack/commands/feature-merge.md` | Modify | Baseline relocation; content-diff discriminator. |
| `pack/commands/adopt.md` | Modify | Cites the reference instead of restating discovery. |
| `pack/skills/pm/SKILL.md` | Modify | Five ADR-path sites. |
| `pack/agents/architect.md` | Modify | Three ADR-path sites. |
| `pack/state.md.template` | Modify | `Gated baseline` field comment follows the new semantics. |
| `pack/MIGRATIONS.md` | Modify | Task 11: the `:5` ownership over-claim (a second instance, found while planning). Task 14: the 0.11.0 section — missed Open-questions entry + reworded field comment. |
| `pack/devkit-orientation.md` | Modify | Ownership scoped to the manifest's tracked set. |
| `VERSION` | Modify | `0.10.0` → `0.11.0`. |
| `CLAUDE.md` | Modify | Release step; slice-11 status. |
| `docs/design/inventory-and-build-order.md` | Modify | Slice 11 section. |
| `docs/validation/slice-11.md` | **Create** | Behavioral predictions, unrun. |

---

## Phase A — Release guard (Finding 1)

### Task 1: Template snapshot guard

**Files:**
- Create: `tests/test_migrations_snapshot.py`
- Create: `pack/templates/history/0.10.0/state.md.template`
- Create: `pack/templates/history/0.10.0/CLAUDE.md.template`
- Modify: `CLAUDE.md` (add a *Releasing* subsection)

**Interfaces:**
- Consumes: `install_lib.TEMPLATE_FILES` — a tuple of `(pack_rel, target_rel)` pairs; `pack_rel` is the filename under `pack/`.
- Produces: `current_version() -> str`, `version_key(str) -> tuple[int, ...]`, `snapshot_versions() -> list[str]`, `previous_version(str) -> str | None`, `migrations_has_section(str) -> bool`. Task 14 relies on nothing but the test passing.

- [ ] **Step 1: Write the failing test**

Create `tests/test_migrations_snapshot.py`:

```python
#!/usr/bin/env python3
"""Guard: a seeded template cannot change without its diff being surfaced.

Finding 1 of the PR #139 review: `state.md.template`'s Open-questions prose
changed in 0.10.0, and the 0.10.0 MIGRATIONS entry documented only the
`Gated baseline` field. The installer never rewrites seeded files, so every
upgrader who followed MIGRATIONS.md exactly ended up with a `state.md` whose
own documentation contradicts `/pr-review`.

No test can verify an entry is semantically *complete* — that is precisely
what failed, since a 0.10.0 section existed and was missing one of two
changes. What this guarantees is narrower and sufficient: editing a template
turns the suite red until the author re-snapshots, and re-snapshotting is the
moment the old->new diff is in front of them.

  SNAPSHOT-CURRENT   pack/templates/history/<VERSION>/ exists and byte-matches
                     every live template.

  MIGRATION-PRESENT  If <VERSION>'s snapshot differs from the previous
                     version's, MIGRATIONS.md carries a `## <VERSION>` section.
                     This is the test ADR-0007:128 proposed, made computable by
                     the snapshots -- this repo has no tags and VERSION was
                     bumped mid-slice at a11733e, so "diff between releases"
                     was not otherwise derivable.

`pack/templates/history/` is a development-tree artifact: TRACKED_DIRS does not
include it, so it is never installed and has no manifest disposition.

Stdlib only, matching the pack's own no-dependency posture.

Run:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK = REPO_ROOT / "pack"
HISTORY = PACK / "templates" / "history"
MIGRATIONS = PACK / "MIGRATIONS.md"

sys.path.insert(0, str(REPO_ROOT))
import install_lib  # noqa: E402  (path set above)


def current_version() -> str:
    return (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()


def version_key(name: str) -> tuple[int, ...]:
    """Numeric ordering. A string sort puts 0.9.0 above 0.10.0, which would
    silently pick the wrong baseline for the diff."""
    return tuple(int(part) for part in name.split("."))


def snapshot_versions() -> list[str]:
    if not HISTORY.is_dir():
        return []
    return sorted((d.name for d in HISTORY.iterdir() if d.is_dir()), key=version_key)


def previous_version(version: str) -> str | None:
    earlier = [v for v in snapshot_versions() if version_key(v) < version_key(version)]
    return earlier[-1] if earlier else None


def template_names() -> list[str]:
    """Asked of install_lib rather than hardcoded, so adding a seeded template
    extends this guard automatically."""
    return [pack_rel for pack_rel, _ in install_lib.TEMPLATE_FILES]


def migrations_has_section(version: str) -> bool:
    pattern = re.compile(rf"^##\s+{re.escape(version)}\s*$", re.MULTILINE)
    return bool(pattern.search(MIGRATIONS.read_text(encoding="utf-8")))


class TestVersionHelpers(unittest.TestCase):
    """The helpers, on known inputs — so a green run means something."""

    def test_version_key_orders_numerically_not_lexically(self):
        self.assertLess(version_key("0.9.0"), version_key("0.10.0"))
        self.assertLess(version_key("0.10.0"), version_key("0.11.0"))

    def test_template_names_is_not_empty(self):
        """A bug returning [] would make SNAPSHOT-CURRENT vacuously pass."""
        self.assertGreaterEqual(len(template_names()), 2)

    def test_migrations_has_section_matches_a_real_heading(self):
        self.assertTrue(migrations_has_section("0.10.0"))

    def test_migrations_has_section_rejects_a_missing_one(self):
        self.assertFalse(migrations_has_section("99.0.0"))

    def test_migrations_has_section_does_not_match_a_substring(self):
        """`## 0.10.0` must not satisfy a query for `0.1`."""
        self.assertFalse(migrations_has_section("0.1"))


class TestSnapshotCurrent(unittest.TestCase):
    def test_snapshot_dir_exists_for_current_version(self):
        version = current_version()
        self.assertTrue(
            (HISTORY / version).is_dir(),
            f"No snapshot for VERSION {version}. Create "
            f"pack/templates/history/{version}/ by copying every file in "
            f"{template_names()} from pack/.",
        )

    def test_every_template_matches_its_snapshot(self):
        version = current_version()
        for name in template_names():
            with self.subTest(template=name):
                live = (PACK / name).read_bytes()
                snap_path = HISTORY / version / name
                self.assertTrue(snap_path.is_file(), f"Missing snapshot: {snap_path}")
                self.assertEqual(
                    live,
                    snap_path.read_bytes(),
                    f"\n\npack/{name} differs from its {version} snapshot.\n"
                    f"This is the guard working. Do this, in order:\n"
                    f"  1. diff pack/templates/history/{version}/{name} pack/{name}\n"
                    f"  2. Account for EVERY hunk in pack/MIGRATIONS.md under the\n"
                    f"     version that will ship it.\n"
                    f"  3. Re-snapshot: cp pack/{name} "
                    f"pack/templates/history/<shipping-version>/{name}\n",
                )

    def test_snapshot_has_no_files_that_are_not_templates(self):
        """A renamed template would otherwise leave a stale snapshot behind,
        and a stale baseline produces a wrong diff — worse than no baseline."""
        version = current_version()
        snap_dir = HISTORY / version
        if not snap_dir.is_dir():
            self.skipTest("covered by test_snapshot_dir_exists_for_current_version")
        extra = {p.name for p in snap_dir.iterdir() if p.is_file()} - set(template_names())
        self.assertEqual(extra, set(), f"Stale files in {snap_dir}: {sorted(extra)}")


class TestMigrationPresent(unittest.TestCase):
    def test_changed_template_has_a_migration_section(self):
        version = current_version()
        prev = previous_version(version)
        if prev is None:
            self.skipTest(f"{version} is the earliest snapshot; no baseline to diff")
        changed = [
            name
            for name in template_names()
            if (HISTORY / prev / name).read_bytes() != (HISTORY / version / name).read_bytes()
        ]
        if not changed:
            return
        self.assertTrue(
            migrations_has_section(version),
            f"Templates changed between {prev} and {version} ({', '.join(changed)}) "
            f"but pack/MIGRATIONS.md has no `## {version}` section. Seeded files are "
            f"never rewritten by the installer, so a change with no entry ships to "
            f"nobody.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run it to confirm it fails for the right reason**

```bash
python3 -m unittest tests.test_migrations_snapshot -v
```

Expected, verified while this plan was written: `Ran 9 tests … FAILED (failures=3, skipped=2)`. The five `TestVersionHelpers` PASS. Three failures: `test_snapshot_dir_exists_for_current_version` with `No snapshot for VERSION 0.10.0`, plus one `test_every_template_matches_its_snapshot` subtest per template. Two skips: `test_snapshot_has_no_files_that_are_not_templates` and `test_changed_template_has_a_migration_section`.

If `test_migrations_has_section_matches_a_real_heading` fails, `pack/MIGRATIONS.md` does not have a literal `## 0.10.0` line — stop and check, do not adjust the regex to match.

- [ ] **Step 3: Create the 0.10.0 baseline**

The live templates *are* 0.10.0's shipped shape, so the baseline is a copy — no git archaeology.

```bash
mkdir -p pack/templates/history/0.10.0
cp pack/state.md.template pack/CLAUDE.md.template pack/templates/history/0.10.0/
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m unittest discover -s tests -v
```

Expected, verified while this plan was written: `Ran 39 tests … OK (skipped=1)` across both guard files. The skip is `test_changed_template_has_a_migration_section` — 0.10.0 is the earliest snapshot, so there is no baseline to diff until Task 14 cuts 0.11.0.

- [ ] **Step 5: Document the release step**

In this project's `CLAUDE.md`, immediately before `## Working principles for this project`, add:

```markdown
## Releasing the pack

Seeded files (`state.md`, `CLAUDE.md`) are stamped once and never rewritten by
the installer, so a change to their *shape* reaches existing installs only via
`pack/MIGRATIONS.md`. `tests/test_migrations_snapshot.py` blocks a release that
forgets one. The cycle:

1. `diff -u pack/templates/history/<prev>/state.md.template pack/state.md.template`
   (and the same for `CLAUDE.md.template`).
2. Account for **every hunk** in a `## <new-version>` section of `pack/MIGRATIONS.md`.
   Not every hunk needs its own bullet — but every hunk needs a decision.
3. Bump `VERSION`.
4. `mkdir -p pack/templates/history/<new-version> && cp pack/*.template pack/templates/history/<new-version>/`
5. `python3 -m unittest discover -s tests`

Step 1 is the one that matters. Finding 1 of the PR #139 review was a migration
entry written from recollection: two things changed in 0.10.0 and the entry
documented one.
```

- [ ] **Step 6: Commit**

```bash
git add tests/test_migrations_snapshot.py pack/templates/history/0.10.0/ CLAUDE.md
git commit -m "test: seeded templates cannot change without surfacing the diff (ADR-0008 clause 1)"
```

---

## Phase B — ADR registry (Findings 2, 3)

### Task 2: Extract the discovery procedure

**Files:**
- Create: `pack/references/adr-registry.md`

**Interfaces:**
- Produces: the citable path `.claude/references/adr-registry.md`, and four named sections that Tasks 3–6 cite by name: *Discover*, *Report what was found*, *Allocate*, *Never cache the number*.

- [ ] **Step 1: Write the reference**

Content is lifted from `feature-start.md:75-85` — which stops being the canonical copy in Task 3 — with the plan-time and adoption-time rules folded in.

```markdown
# ADR registry — discovery and allocation

Used by: `pm` skill (brainstorm and plan-time architect invocations), `architect` subagent (via the paths its caller passes), `/feature-start` (Phase A discovery, Phase E allocation), `/plan` (architect-drafted ADRs), `/adopt` (adoption ADRs).

A project's architecture decisions live wherever that project put them. `docs/adr/` is the pack's default **for a project that has none** — it is never the assumption. This file is the single copy of how to find the registry and how to take the next number in it.

A fixed list of known locations would only ever find the layouts its author thought of. The first brownfield target kept twelve ADRs as headings inside a **single decisions log** under a docs subdirectory no such list would have contained.

## Discover

### Scope

`*.md` under `docs/`, plus root-level `*.md`. Never `.git/`, `node_modules/`, `vendor/`, or anything matched by `.gitignore`.

### Match, two patterns

- **In file contents:** `ADR[-_ ]?0*\d+`, case-insensitive.
- **In filenames:** `^0*\d{1,4}[-_]` under any directory whose name suggests decision records (`adr`, `adrs`, `decisions`, `rfc`, `rfcs`) — **excluding date-prefixed names** matching `^\d{4}-\d{2}-\d{2}`, which are dated notes rather than ADR numbers and would otherwise set a high-water mark in the thousands.

The filename pattern is not optional. A project using the pack's own `docs/adr/0012-name.md` convention need never write the string "ADR" inside the file, so a contents-only scan finds nothing and allocates `0001` over an existing registry.

### Rank definitions above mentions

A **definition** is a heading (`## ADR-012: …`) or a filename (`0012-*.md`). A **mention** is inline prose — a summary citing `ADR-007`, a changelog line. Take the high-water mark from definitions when any exist; mentions are a lower-confidence fallback and must be reported as such.

### Report what was found

Location, format (directory-of-files vs single-file log), highest number, and whether it came from definitions or mentions. **A bare number is not something the user can check.**

## Allocate

1. **Re-scan first.** See *Never cache the number* below.
2. **Take floor + 1.**
3. **Ask before relocating.** If the registry sits outside `docs/adr/`, or definitions appear in more than one location, ask: continue numbering in place, or start `docs/adr/` above the high-water mark. **Never silently allocate `0001` when any registry exists** — a duplicate ADR number means two documents claim the same decision ID, and the `architect` starts blind to every prior decision it might contradict.
4. **Write in that registry's format**, not the pack's. A project keeping a single decisions log gets a new heading in that log, not a new directory beside it. Create `docs/adr/` only when discovery found nothing anywhere.
5. **Update the recorded high-water mark** in `CLAUDE.md` conventions to the number just written, so the record stays a useful hint rather than decaying into a wrong one.

## Never cache the number

**The location may be recorded. The number may not be trusted.**

`/adopt` records the high-water mark once; features allocate continuously. With adoption at `12`, feature one takes `13`, and feature two reading the same recorded `12` takes `13` again — duplicate decision IDs in the normal documented flow, not just the brownfield case discovery was built for. `/plan` allocating from a mark `/feature-start` already consumed is the same collision one command over.

Re-scan the registry for the current highest number **every time you allocate**. Step 5 above keeps the record from decaying, but the re-scan is the authority regardless.

## Where the location is recorded

`CLAUDE.md` conventions, written by `/adopt`. A project that has never run `/adopt` has no record — run *Discover* in full rather than falling back to `docs/adr/`.
```

- [ ] **Step 2: Verify the citation guard accepts it**

```bash
python3 -m unittest discover -s tests -v
./install.sh "$(mktemp -d)" --dry-run | grep adr-registry
```

Expected: tests PASS; dry-run shows `NEW .claude/references/adr-registry.md`. `TRACKED_DIRS` already contains `references`, so no installer change is needed — if the grep is empty, stop; something is wrong with the file's location.

- [ ] **Step 3: Commit**

```bash
git add pack/references/adr-registry.md
git commit -m "pack: extract ADR-registry discovery into one citable reference (ADR-0008 clause 3)"
```

---

### Task 3: `/feature-start` — discover in Phase A, cite in Phase E

**Files:**
- Modify: `pack/commands/feature-start.md:32-39` (Phase A), `:71-86` (Phase E), `:130` (architect contract)

**Interfaces:**
- Consumes: `.claude/references/adr-registry.md` sections *Discover*, *Report what was found*, *Allocate*, *Never cache the number* (Task 2).

- [ ] **Step 1: Replace Phase A**

Replace the heading and the paragraph + list at `:32-37` with:

```markdown
### Phase A — Orient, discover, and confirm

PM skill orients (reads `CLAUDE.md`, `docs/domains/`, prior `docs/specs/`, and the findings ledger). Then:

1. **Run ADR-registry discovery now.** Follow `.claude/references/adr-registry.md` § *Discover* in full, and record for the rest of this invocation: the registry's location, its format, and its current high-water number. Report what was found per that reference's *Report what was found* step.

   Discovery runs here rather than at Phase E because **Phase B may invoke the `architect`**. An architect handed a default path on a project whose registry lives elsewhere forms its recommendation having read none of the existing decisions — and allocating correctly at Phase E does not un-form a recommendation already made. On the first brownfield target that meant twelve ADRs kept as headings in a single decisions log, invisible to the subagent asked to avoid contradicting them.
2. Propose the slug derived from the user's argument. Confirm with the user.
3. Confirm the feature framing back to the user in one or two sentences before brainstorming. ("My read: you want X so that Y. Right?")
```

Leave the trailing "If the framing confirmation surfaces a misunderstanding…" paragraph unchanged.

- [ ] **Step 2: Replace Phase E steps 1–4**

Replace `:75-81` (numbered items 1 through 4, including the nested bullets) with:

```markdown
1. **Re-scan before allocating.** Phase A recorded the registry's location, format, and high-water mark. Re-run `.claude/references/adr-registry.md` § *Discover* against that location now, and allocate from what it returns — **never from the number Phase A recorded**. That reference's *Never cache the number* explains why: `/plan` allocates from the same registry, and a mark read once is reused by the next allocator.
2. **Allocate and write** per that reference's *Allocate* section — floor + 1, ask before relocating, write in the registry's own format.
```

Then renumber the surviving items `:82-83` from `5.`/`6.` to `3.`/`4.`, and delete the closing paragraph at `:85` ("A fixed list of known locations would only ever find the layouts its author thought of…") — it now lives in the reference.

- [ ] **Step 3: Fix the architect contract**

At `:130`, replace:

```
- Paths to: the active spec draft (write-as-you-go if necessary), relevant `docs/domains/<domain>.md` files, relevant `docs/adr/NNNN-*.md` files, and source-code pointers.
```

with:

```
- Paths to: the active spec draft (write-as-you-go if necessary), relevant `docs/domains/<domain>.md` files, **relevant ADR files from the registry Phase A discovered** — actual paths, never a pattern — and source-code pointers.

  Passing a path pattern instead of paths is how the architect ends up reading nothing: `docs/adr/NNNN-*.md` matches no file on a project whose decisions live in a single log, and the subagent has no way to know that is not simply an empty registry.
```

- [ ] **Step 4: Verify**

```bash
python3 -m unittest discover -s tests -v
grep -n "docs/adr" pack/commands/feature-start.md
```

Expected: tests PASS. The grep should return **only** lines where `docs/adr/` is named as the create-when-nothing-found default — no contract, no scan procedure.

- [ ] **Step 5: Commit**

```bash
git add pack/commands/feature-start.md
git commit -m "pack: /feature-start discovers the ADR registry before the architect runs (ADR-0008 clause 3)"
```

---

### Task 4: `pm` skill — five ADR-path sites

**Files:**
- Modify: `pack/skills/pm/SKILL.md:204`, `:207`, `:214`, `:344`, `:353`

- [ ] **Step 1: Fix the architect-invocation contract (`:204`)**

Replace:

```
- Paths to the active spec draft, relevant `docs/domains/` files, and relevant `docs/adr/` files.
```

with:

```
- Paths to the active spec draft, relevant `docs/domains/` files, and relevant ADR files **from the discovered registry** (`.claude/references/adr-registry.md`) — actual paths, never a directory pattern.
```

- [ ] **Step 2: Fix the ADR write path (`:207`)**

Replace the final sentence of that paragraph:

```
If the architect drafted an ADR, write it to `docs/adr/NNNN-<short-name>.md` with the next free number, and reference it in the spec's front-matter `related_adrs`.
```

with:

```
If the architect drafted an ADR, allocate and write it per `.claude/references/adr-registry.md` § *Allocate* — re-scanning the registry for the current highest number rather than reusing one read earlier — and reference it in the spec's front-matter `related_adrs`.
```

- [ ] **Step 3: Fix the two hand-off checklists (`:214`, `:344`)**

At `:214` replace `- Any ADRs drafted during brainstorm are written under `docs/adr/`.` with:

```
- Any ADRs drafted during brainstorm are written **into the discovered registry**, in its format (`.claude/references/adr-registry.md`).
```

At `:344` replace `- Any ADRs drafted during plan-time architect calls are written under `docs/adr/`.` with:

```
- Any ADRs drafted during plan-time architect calls are written **into the discovered registry**, in its format (`.claude/references/adr-registry.md`). Plan-time allocation re-scans exactly as brainstorm-time does — `/feature-start` may already have consumed the number you last saw.
```

- [ ] **Step 4: Fix the orientation rationalization (`:353`)**

Replace `reading `CLAUDE.md`, `docs/domains/`, and `docs/adr/` means` with:

```
reading `CLAUDE.md`, `docs/domains/`, and the project's ADR registry means
```

- [ ] **Step 5: Verify**

```bash
python3 -m unittest discover -s tests -v
grep -n "docs/adr" pack/skills/pm/SKILL.md
```

Expected: tests PASS; the grep returns only `:46` (the read path, already correct, which names `docs/adr/` explicitly as "the default, not the assumption").

- [ ] **Step 6: Commit**

```bash
git add pack/skills/pm/SKILL.md
git commit -m "pack: pm writes ADRs to the discovered registry, not a hardcoded path (ADR-0008 clause 3)"
```

---

### Task 5: `architect` subagent — three ADR-path sites

**Files:**
- Modify: `pack/agents/architect.md:3` (front-matter description), `:18`, `:77`

- [ ] **Step 1: Fix the front-matter description (`:3`)**

Within the `description:` value, replace:

```
(active spec or draft, `docs/domains/`, `docs/adr/`, and pointers to the source it should sample)
```

with:

```
(active spec or draft, `docs/domains/`, the ADR paths its caller discovered, and pointers to the source it should sample)
```

- [ ] **Step 2: Fix the received-context bullet (`:18`)**

Replace:

```
- **`docs/adr/`** — prior architecture decisions. Read these *before* answering; many questions have already been decided and your job is to surface the precedent.
```

with:

```
- **ADR paths** — prior architecture decisions, passed as explicit paths because a project's registry is wherever that project put it: a `docs/adr/` directory, a single decisions log, or something else entirely. Read these *before* answering; many questions have already been decided and your job is to surface the precedent.

  **If you were passed no ADR paths at all, say so in your response.** On a project with an existing registry that is a caller bug, and the recommendation you are about to give was formed without reading decisions it may contradict. Do not go looking for the registry yourself — you cannot tell an empty one from an undiscovered one, and guessing is how a second registry gets created.
```

- [ ] **Step 3: Fix the ADR-draft placement note (`:77`)**

Replace:

```
Leave the ADR number as `NNNN` — the caller assigns the next free number when accepting. Place the draft in your response body, not directly into `docs/adr/`. The caller writes the file.
```

with:

```
Leave the ADR number as `NNNN` — the caller assigns the next free number when accepting, from the registry it discovered. Place the draft in your response body; **never write an ADR file yourself.** The caller knows where the registry is and what format it uses; you do not.
```

- [ ] **Step 4: Verify**

```bash
python3 -m unittest discover -s tests -v
grep -n "docs/adr" pack/agents/architect.md
```

Expected: tests PASS; the grep returns **exactly one** hit — the illustrative enumeration inside Step 2's own replacement text (*"a `docs/adr/` directory, a single decisions log, or something else entirely"*). That is a list of shapes a registry can take, not a directive to choose one, and it is what teaches the subagent that registries vary. No hit may be a location the architect is told to read or write.

- [ ] **Step 5: Commit**

```bash
git add pack/agents/architect.md
git commit -m "pack: architect reads the ADR paths its caller discovered (ADR-0008 clause 3)"
```

---

### Task 6: `/plan` and `/adopt` — cite instead of restate

**Files:**
- Modify: `pack/commands/plan.md:39`, `:59`, `:148`
- Modify: `pack/commands/adopt.md:132`, `:141`

- [ ] **Step 1: `/plan` research bullet (`:39`)**

Replace:

```
- The project's ADR titles (location per `CLAUDE.md` conventions; `docs/adr/` is the default, not the assumption); read in full any named in the spec's `related_adrs` front-matter or whose title is keyword-relevant.
```

with:

```
- The project's ADR titles — locate the registry per `.claude/references/adr-registry.md` § *Discover*. Read in full any named in the spec's `related_adrs` front-matter or whose title is keyword-relevant.
```

- [ ] **Step 2: `/plan` ADR write path (`:59`)**

Replace the whole paragraph with:

```
If the architect drafts an ADR, allocate and write it per `.claude/references/adr-registry.md` — § *Discover* to locate the registry, § *Allocate* to take the next number, § *Never cache the number* for why a recorded high-water mark is not it. `/plan` allocating from a mark `/feature-start` already consumed is exactly how two ADRs end up claiming one ID. Reference it in the plan's front-matter `related_adrs`.
```

- [ ] **Step 3: `/plan` architect contract (`:148`)**

Replace `relevant ADR files from the project's registry` with:

```
relevant ADR files from the discovered registry (actual paths, never a directory pattern)
```

- [ ] **Step 4: `/adopt` discovery paragraph (`:132`)**

Replace:

```
Registries turn up in shapes a fixed list would miss — the first brownfield target kept `ADR-001 … ADR-012` as headings inside a **single decisions log**, not a directory of files. Without this step `/feature-start` would have found no `docs/adr/`, started at `0001`, and created a second document claiming `ADR-001`.
```

with:

```
Run the scan in `.claude/references/adr-registry.md` § *Discover*, and record what it reports into `CLAUDE.md` conventions — location, format, and high-water number. That reference is what `/feature-start` and `/plan` read too, so adoption and allocation cannot drift into disagreeing about where the registry is.
```

- [ ] **Step 5: `/adopt` adoption-ADR write (`:141`)**

Replace `— `docs/adr/NNNN-<short-name>.md` only when discovery found nothing` with:

```
per `.claude/references/adr-registry.md` § *Allocate* (which creates `docs/adr/` only when discovery found nothing)
```

- [ ] **Step 6: Verify**

```bash
python3 -m unittest discover -s tests -v
grep -rn "docs/adr" pack/ | grep -v "references/adr-registry.md" | grep -v "templates/history"
```

Expected: tests PASS, and **exactly five** surviving hits, each of which must be one of these and nothing else. Confirm each individually; do not accept the count alone.

| Hit | Why it survives |
|---|---|
| `agents/architect.md:18` | Illustrative enumeration of registry shapes ("a `docs/adr/` directory, a single decisions log, or something else entirely") |
| `skills/pm/SKILL.md:46` | Read path, already correct — states `docs/adr/` is "the default, not the assumption" |
| `skills/documenter/SKILL.md:37` | Doc-ownership table row about ADR immutability; outside this slice's scope |
| `commands/feature-start.md:128` | Cautionary prose explaining why a *pattern* fails where paths work |
| `commands/adopt.md:141` | The create-when-discovery-found-nothing default |

None may be a discovery procedure or a subagent contract. A sixth hit means an edit was missed.

- [ ] **Step 7: Commit**

```bash
git add pack/commands/plan.md pack/commands/adopt.md
git commit -m "pack: /plan and /adopt cite the ADR-registry reference (ADR-0008 clause 3)"
```

---

## Phase C — Transport and self-reference (Findings 4–7)

### Task 7: `/plan` Phase G stages the findings ledger

**Files:**
- Modify: `pack/commands/plan.md:129`

- [ ] **Step 1: Extend the staging list**

Replace:

```
Before the pause, propose a single commit for the artifacts this invocation produced: the plan, any Phase-C ADRs, the Phase-F `.claude/state.md` updates, and any spec front-matter `related_adrs` amendment Phase C made.
```

with:

```
Before the pause, propose a single commit for the artifacts this invocation produced: the plan, any Phase-C ADRs, the Phase-F `.claude/state.md` updates, any spec front-matter `related_adrs` amendment Phase C made, **and the findings ledger if Phase F2 recorded a `CONF` row** (its path is the discovered one, not assumed).

A `CONF` row that is written and not committed reaches no other clone and no PR — defeating the stated purpose of surfacing to the next `/feature-start`'s orient phase, which reads the ledger from the repo rather than from this conversation. Every artifact this invocation writes is named in this list; that is the rule, not a checklist that happens to be four items long.
```

- [ ] **Step 2: Verify**

```bash
python3 -m unittest discover -s tests -v
```

- [ ] **Step 3: Commit**

```bash
git add pack/commands/plan.md
git commit -m "pack: /plan commits the CONF row it writes (ADR-0008 clause 1)"
```

---

### Task 8: `/pr-review` commits before pushing

**Files:**
- Modify: `pack/commands/pr-review.md:73-83` (Phase D)

- [ ] **Step 1: Insert the metadata commit**

Phase D currently numbers five stages, of which only stage 1 commits. Renumber to six, inserting a new stage 4 between the current 3 and 4:

```markdown
4. **Commit the metadata.** Stage exactly what stages 2 and 3 wrote — the summary doc, the discovered findings-ledger path, and `.claude/state.md` — and propose a commit. Subject: `review: findings ledger + state`. Stage explicitly; never `git add -A`.

   Stages 2 and 3 write durable artifacts and stage 5 pushes; without this, neither reaches the remote. The PR then lacks the `REV` record that is the whole point of a cross-feature deferral, and the tree stays dirty — which `/feature-merge`'s own preconditions treat as blocking, so the next closeout cannot check out mainline.
```

Renumber the existing stage 4 (push/verify) to 5 and stage 5 (replies) to 6.

- [ ] **Step 2: Update the two back-references**

In *Halt conditions*, `(See *Phase D*, step 1.)` is unaffected. In *Common rationalizations*, the row "I'll fix the code and mention it in the reply I'm about to draft." cites `(See *Phase D*.)` — unaffected. Confirm with:

```bash
grep -n "Phase D., step\|Phase D. step" pack/commands/pr-review.md
```

Expected: only `step 1` references, which still point at code fixes.

- [ ] **Step 3: Extend the Phase E report**

At `:91`, the hand-off report lists what happened. Add the commit to it — replace `commits made,` with:

```
commits made (fixes **and** the metadata commit),
```

- [ ] **Step 4: Verify**

```bash
python3 -m unittest discover -s tests -v
```

- [ ] **Step 5: Commit**

```bash
git add pack/commands/pr-review.md
git commit -m "pack: /pr-review commits the ledger and docs it writes before pushing (ADR-0008 clause 1)"
```

---

### Task 9: `/pr-review all` keeps the own-reply filter

**Files:**
- Modify: `pack/commands/pr-review.md:40`, `:45`, `:47`

- [ ] **Step 1: Resolve the either/both contradiction**

`:40` says "Skip an item if **either** is true"; `:45` says "**Both** conditions are required." Both readings are defensible and they conflict. `:40` is the correct semantics (an item matching either condition is skipped); `:45` means "both *checks* must be implemented."

Replace `:45`'s opening sentence:

```
Both conditions are required, and the second is easy to miss.
```

with:

```
Both checks must be implemented — an item matching *either* is skipped — and the second check is the one that is easy to miss.
```

- [ ] **Step 2: Scope `all` mode to condition 1**

Replace `:47`'s final sentence:

```
`/pr-review all` disables the skip.
```

with:

```
**`/pr-review all` disables condition 1 only.** Condition 2 always applies: an item carrying a devkit marker is the pack's own reply and is never a review item, in any mode. Disabling the whole skip would re-fetch those replies and offer to answer them — the exact recursion the paragraph above prevents, reintroduced by the flag meant to re-triage the reviewer's comments.
```

- [ ] **Step 3: Update the argument description**

At `:12`, replace:

```
- **`/pr-review all`** — re-triage every thread, including previously-answered ones. Use when replies were posted manually outside the pack, or when a spec amendment changes how earlier findings should have been classified.
```

with:

```
- **`/pr-review all`** — re-triage every thread, including previously-answered ones. Use when replies were posted manually outside the pack, or when a spec amendment changes how earlier findings should have been classified. The pack's own replies stay excluded; `all` re-opens the reviewer's items, not the answers to them.
```

- [ ] **Step 4: Verify**

```bash
python3 -m unittest discover -s tests -v
```

- [ ] **Step 5: Commit**

```bash
git add pack/commands/pr-review.md
git commit -m "pack: /pr-review all re-triages reviewer items, not the pack's own replies (ADR-0008 clause 2)"
```

---

### Task 10: `Gated baseline` stops invalidating itself

**Files:**
- Modify: `pack/commands/feature-merge.md:23-24`, `:27`, `:113`, `:162`, `:168`, `:178`
- Modify: `pack/state.md.template:39-44` (the `Gated baseline` field comment)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: a `state.md.template` edit that Task 14's MIGRATIONS entry must carry, and which turns `tests/test_migrations_snapshot.py` red until Task 14 re-snapshots. **That failure is expected from this task until Task 14** — do not "fix" it by re-snapshotting here, or the 0.10.0 baseline is destroyed and the diff is lost.

- [ ] **Step 1: Rewrite the two `in-review` rerun rows (`:23-24`)**

Replace both rows with:

```
| `in-review`, PR open, **gated content unchanged** | Report review status and open-thread count. Point at `/pr-review`. Run no gates — this content already passed them. |
| `in-review`, PR open, **gated content changed** | Re-run gates 1–3 — the PR carries changes no gate has seen — then push and update `Gated baseline`. Do **not** re-create the PR. |
```

- [ ] **Step 2: Replace the discriminator paragraph (`:27`)**

Replace the whole paragraph with:

```
**The discriminator is a content diff against `Gated baseline` — never local tip versus remote tip, and never SHA equality.** Read the PR tip with `gh pr view --json headRefOid`, then:

```
git diff --quiet <Gated baseline> <PR tip> -- . ':(exclude).claude/state.md'
```

Quiet (exit 0) → the gated content is unchanged; run no gates. Differs → re-run gates 1–3.

Two things this gets right that the obvious versions do not:

- **Not tip versus tip.** `/pr-review` commits its fixes and pushes them, so after it runs the local and remote tips agree while carrying commits no gate has ever seen. A rerun keyed on that would skip tests, docs reconciliation, and security review on precisely the code about to merge.
- **Not SHA equality against the baseline.** Writing `Gated baseline` requires committing `state.md`, which changes the tip — so tip *never* equals baseline, and an equality check makes the no-gates branch unreachable from the moment the PR opens. The exclusion of `.claude/state.md` is what makes the comparison survive the command's own bookkeeping write. It is a **content** diff rather than a commit walk so that a change reverted within the PR correctly reads as unchanged.
```

- [ ] **Step 3: Name the baseline at the closeout commit (`:113`)**

Append to the end of that paragraph:

```
**Record this commit's SHA.** It becomes `Gated baseline` at PR creation — it is the tip as it stands before the `state.md`-only transition commit, which is the one commit the discriminator's exclusion accounts for.
```

- [ ] **Step 4: Fix what the baseline is set to (`:162`)**

Replace `**`Gated baseline: <the SHA that just passed gates 1–3>`**` with:

```
**`Gated baseline: <the closeout commit's SHA>`** — the tip as it stands *before* the transition commit below, not the SHA the gates ran against. The closeout commit lands after the gates too, so the gate-time SHA is already two commits behind by the time the PR opens.
```

- [ ] **Step 5: Fix the rerun update rule (`:168`)**

Replace:

```
Update `Gated baseline` again after **every** successful gate rerun, to the SHA those gates ran against. A stale baseline is worse than none: it makes ungated commits look gated.
```

with:

```
Update `Gated baseline` after **every** successful gate rerun — to the tip as it stands once any fix commits are in and before the `state.md`-only transition commit. Same rule as at PR creation: the baseline is the last commit whose content was gated, never the SHA that happened to be checked out when the gates started.

A stale baseline is worse than none: it makes ungated commits look gated.
```

- [ ] **Step 6: Check the closeout clear (`:178`)**

`:178` already clears `Gated baseline` to `—` at closeout. Confirm it still reads correctly against the new semantics — it does; no edit expected. Verify with `grep -n "Gated baseline" pack/commands/feature-merge.md` and read every hit.

- [ ] **Step 7: Update the seeded template's field comment**

In `pack/state.md.template`, replace the `Gated baseline` block at `:39-44` with:

```
  Gated baseline  the last commit whose CONTENT passed gates 1-3 -- the tip
                  before the state.md-only transition commit, set when the PR
                  opens and after every successful gate rerun. /feature-merge
                  diffs it against the PR tip, excluding this file, to decide
                  whether a rerun needs the gates. Excluding it is required:
                  writing this field commits it, so a plain SHA comparison
                  would never match. Comparing local vs remote tips cannot
                  work either -- /pr-review pushes its fixes and makes them
                  agree.
```

- [ ] **Step 8: Verify — and expect one failure**

```bash
python3 -m unittest discover -s tests -v
```

Expected: `test_every_template_matches_its_snapshot` **FAILS** on `state.md.template` with the guard's three-step remediation message. Every other test PASSES. This is Task 1's guard doing its job; Task 14 resolves it.

- [ ] **Step 9: Commit**

```bash
git add pack/commands/feature-merge.md pack/state.md.template
git commit -m "pack: Gated baseline compares content, excluding its own write (ADR-0008 clause 2)"
```

---

## Phase D — Ownership, doc currency, release (Finding 8)

### Task 11: Scope the `.claude/` ownership claim

**Files:**
- Modify: `pack/devkit-orientation.md:81-89`
- Modify: `pack/MIGRATIONS.md:5`

Finding 8 named one site. A grep for the claim while this plan was written found a **second**, in an installed file: `pack/MIGRATIONS.md:5` reads *"Everything else under `.claude/` is **pack-owned** and updates automatically."* Same over-claim, same consequence. `README.md` was checked and is clean — it says "pack-owned" only of `devkit-orientation.md` specifically, which is true.

- [ ] **Step 1: Rewrite the section**

Replace the whole `## `.claude/` is pack-owned` section (`:81-89`) with:

```markdown
## Which `.claude/` files the pack owns

**Not all of them.** `.claude/.devkit-manifest.json` lists exactly what the installer tracks — skills, agents, commands, hooks, references, plus `devkit-orientation.md` and `MIGRATIONS.md`. Those files are vendored from the pack and versioned by it rather than by this repository's conventions.

Anything else under `.claude/` is **yours**: subagents and commands you wrote, and anything a previous setup left there. The pack does not manage them, will not update them, and has no opinion about them. On a project that had `.claude/` before devkit, that is usually most of the directory.

Two files are **seeded** — stamped once and yours to edit freely thereafter: `.claude/state.md` and your `CLAUDE.md`. The installer never rewrites them; changes to their shape arrive as entries in `.claude/MIGRATIONS.md`. `settings.json` is a third case: the installer merges its hook fragment in and leaves the rest of the file alone.

### Findings filed against pack-tracked files

Your linters, reviewers, and CI will see the tracked files and may file findings against them under your project's rules. The drift hook's `print(..., file=sys.stderr)` is the common one — that stderr line **is** the hook's channel back to the model, so routing it through a logging framework would break it, and the hook is deliberately stdlib-only.

For a file in the manifest, treat findings of that shape as pack issues and report them upstream rather than editing in place: a local edit is what the installer's customization detection will `SKIP` on your next update, so you keep your change and silently stop receiving improvements to that file. For a file *not* in the manifest, none of that applies — it is your file, and your project's rules are the right rules for it.
```

- [ ] **Step 2: Fix the same claim in `MIGRATIONS.md`**

Replace `pack/MIGRATIONS.md:5`:

```
Everything else under `.claude/` is **pack-owned** and updates automatically. You do not need this file for those.
```

with:

```
Every file the manifest tracks (`.claude/.devkit-manifest.json`) updates automatically — you do not need this file for those. Anything under `.claude/` that the manifest does not list is **yours**, and the pack neither updates it nor expects you to migrate it.
```

- [ ] **Step 3: Verify**

```bash
python3 -m unittest discover -s tests -v
grep -rn "pack-owned" pack/ README.md
```

Expected: `test_every_template_matches_its_snapshot` still failing from Task 10; everything else PASSES. Every surviving `pack-owned` hit must name a **specific file** (`devkit-orientation.md`), never the directory. Read each one.

- [ ] **Step 4: Commit**

```bash
git add pack/devkit-orientation.md pack/MIGRATIONS.md
git commit -m "pack: scope .claude/ ownership to the manifest's tracked set (finding 8)"
```

---

### Task 12: Doc currency

**Files:**
- Modify: `docs/design/inventory-and-build-order.md` (new `### Slice 11` section after Slice 9)
- Modify: `CLAUDE.md` (Status section)

- [ ] **Step 1: Add the slice-11 section**

After the Slice 9 section, matching the shape of Slices 7–9, add a `### Slice 11 — Step invariants (post-core)` section covering: the design pointer (`docs/design/0008-step-invariants.md`), the eight findings it closes, the four phases and their tasks, and the note that **slice 10 (artifact dispositions) is unbuilt and slice 11 does not depend on it** — the numbering is deliberate, not a gap.

- [ ] **Step 2: Update the Status section**

In `CLAUDE.md` → `## Status` → `### Outstanding`, add a slice-11 entry stating: authored on 2026-08-10, closes the eight PR #139 findings, ships as 0.11.0, **behavioral predictions recorded and unrun**, and that the Enterprise API dogfood is what validates it. Also amend the existing slice-9 bullet to note that finding 1 of the PR #139 review is the ADR-0007 risk at `:128` actually occurring, and that slice 11 lands the guard early.

- [ ] **Step 3: Commit**

```bash
git add docs/design/inventory-and-build-order.md CLAUDE.md
git commit -m "docs: record slice 11 in the build order and project status"
```

---

### Task 13: Behavioral predictions

**Files:**
- Create: `docs/validation/slice-11.md`

- [ ] **Step 1: Write the predictions**

Match the structure of `docs/validation/slice-9.md`. Record these five, each with setup, the exact action, and the predicted behavior — **written before any run, and not revised to match a result**:

- **P1 (clause 2, the one that matters).** On Enterprise API with a PR open and `Phase: in-review`, run `/feature-merge` with nothing changed since the PR opened. **Predict:** it reports review status and open-thread count, runs **no** gates, and does not invoke the `security-reviewer`. This branch has been unreachable since `Gated baseline` was introduced; it is the single highest-value observation in the slice.
- **P2 (clause 2, negative case).** Same setup, but land one code commit via `/pr-review` first. **Predict:** gates 1–3 all re-run, and `Gated baseline` is updated afterward to the tip before the transition commit.
- **P3 (clause 3).** Run `/feature-start` on Enterprise API, where twelve ADRs live in `docs/ai/decisions.md`. **Predict:** Phase A reports the registry location, format, and high-water number **before** the brainstorm; if Phase B invokes the architect, the invocation carries actual paths into `docs/ai/decisions.md`; Phase E allocates `013` after a re-scan; no `docs/adr/` directory is created.
- **P4 (clause 1).** Run `/plan` on a feature whose conformance review leaves an advisory outstanding. **Predict:** the Phase G commit proposal stages the discovered ledger path alongside the plan, and `git show --stat` on the resulting commit lists it.
- **P5 (finding 7).** With at least one pack reply already posted, run `/pr-review all`. **Predict:** the pack's own marker-bearing replies are absent from the proposal table, the skipped count names them, and previously-answered reviewer items **are** re-triaged.

- [ ] **Step 2: Record the standing caveat**

State plainly, as `slice-8.md` and `slice-9.md` do: **no pack command has been executed.** Findings 4, 5, and 7 were found by reading and are fixed by reading. Slice 11 ships unvalidated.

- [ ] **Step 3: Commit**

```bash
git add docs/validation/slice-11.md
git commit -m "docs: slice-11 behavioral predictions (recorded, unrun)"
```

---

### Task 14: Release 0.11.0

**Files:**
- Modify: `VERSION`, `pack/MIGRATIONS.md`
- Create: `pack/templates/history/0.11.0/state.md.template`, `pack/templates/history/0.11.0/CLAUDE.md.template`

**Interfaces:**
- Consumes: the failing `test_every_template_matches_its_snapshot` from Task 10 — this task is what turns the suite green.

- [ ] **Step 1: Walk the diff — do not skip this**

```bash
diff -u pack/templates/history/0.10.0/state.md.template pack/state.md.template
diff -u pack/templates/history/0.10.0/CLAUDE.md.template pack/CLAUDE.md.template
```

Expected: one hunk, the `Gated baseline` field comment from Task 10. `CLAUDE.md.template` is unchanged. **Every hunk gets a decision in step 3** — that is the step whose absence is finding 1.

- [ ] **Step 2: Bump the version**

```bash
echo "0.11.0" > VERSION
```

- [ ] **Step 3: Write the 0.11.0 migration section**

Insert immediately after the `# Migrations` preamble and before `## 0.10.0`:

```markdown
## 0.11.0

### `.claude/state.md`

- **In the trailing HTML comment**, replace the `Open questions` paragraph with the two-paragraph version below. *(This change shipped in 0.10.0 and was omitted from that entry — apply it now regardless of whether you already applied 0.10.0.)*

  ```
  The Open questions section captures things deferred mid-feature that need
  the user's input. /checkpoint reads and helps resolve these.

  During Phase: in-review it holds review findings accepted for THIS
  feature and not yet fixed. It is cleared at /feature-merge, so anything
  deferred PAST this feature must go to the findings ledger instead --
  /pr-review routes cross-feature deferrals there as REV rows. Parking a
  durable finding here discards it at merge.
  ```

  Without it your `state.md` tells a model that accepted-but-unfixed review findings live in `## Open questions` — a section `/feature-merge` clears — directly contradicting `/pr-review`, which routes cross-feature deferrals to the findings ledger as `REV` rows.

- **In the trailing HTML comment**, replace the `Gated baseline` field meaning with:

  ```
  Gated baseline  the last commit whose CONTENT passed gates 1-3 -- the tip
                  before the state.md-only transition commit, set when the PR
                  opens and after every successful gate rerun. /feature-merge
                  diffs it against the PR tip, excluding this file, to decide
                  whether a rerun needs the gates.
  ```

  The field's shape is unchanged; its **meaning** is. In 0.10.0 it held the SHA the gates ran against, and `/feature-merge` compared it to the PR tip for equality — which could never match, because writing the field commits it. 0.11.0 stores the tip before that commit and compares by content diff excluding `state.md`. No edit to your header is needed; this keeps the file's own documentation true.
```

- [ ] **Step 4: Re-snapshot**

```bash
mkdir -p pack/templates/history/0.11.0
cp pack/state.md.template pack/CLAUDE.md.template pack/templates/history/0.11.0/
```

- [ ] **Step 5: Run the full suite**

```bash
python3 -m unittest discover -s tests -v
./install.sh "$(mktemp -d)" --dry-run
```

Expected: **all tests PASS**, including `test_changed_template_has_a_migration_section`, which now has a real baseline (0.10.0), a real diff, and a real `## 0.11.0` section. The dry-run lists `references/adr-registry.md` as `NEW`.

Sanity-check the guard is not passing vacuously:

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "tests")
from test_migrations_snapshot import previous_version, current_version, snapshot_versions
print(snapshot_versions(), current_version(), previous_version(current_version()))
EOF
```

Expected: `['0.10.0', '0.11.0'] 0.11.0 0.10.0`.

- [ ] **Step 6: Commit**

```bash
git add VERSION pack/MIGRATIONS.md pack/templates/history/0.11.0/
git commit -m "release: 0.11.0 — step invariants; carries the 0.10.0 migration entry that was missed"
```

---

## Self-review

**Spec coverage.** All eight findings map to a task: #1 → Tasks 1, 14; #2 → Tasks 4, 5; #3 → Tasks 3, 5; #4 → Task 10; #5 → Task 8; #6 → Task 7; #7 → Task 9; #8 → Task 11. ADR-0008's three clauses each have at least two tasks citing them in a commit subject. The ADR's own build-slice list adds Tasks 12 (doc currency) and 13 (predictions).

**Known deviation from the ADR.** ADR-0008 § *Build slice* puts the missed Open-questions entry "into the **0.11.0** section, not retroactively into 0.10.0." Task 14 does exactly that and adds the parenthetical *"apply it now regardless of whether you already applied 0.10.0"* — necessary because a 0.9.0 upgrader applying both sections would otherwise apply the same prose twice. No ADR update needed; this is the ADR's rule, stated operationally.

**Cross-task consistency.** Task 10 deliberately leaves the suite red; Task 14 is the only task that writes `pack/templates/history/0.11.0/`. `.claude/references/adr-registry.md` is the citation form used in Tasks 3–6 (target-relative, which `test_pack_references_resolve.py` classifies `PACK-INSTALLED`); `pack/references/adr-registry.md` is used only in file paths and `git add`. Section names cited across tasks — *Discover*, *Report what was found*, *Allocate*, *Never cache the number* — match Task 2's headings exactly.

**Ordering constraint.** Task 2 must precede Tasks 3–6 (they cite the file, and `test_pack_references_resolve.py` fails on a citation to a file that does not exist). Task 10 must precede Task 14. Everything else is independent.
