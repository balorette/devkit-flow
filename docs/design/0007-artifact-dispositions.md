# ADR-0007: Artifact Dispositions — Owned, Seeded, Discovered

**Status:** Proposed
**Date:** 2026-08-03
**Deciders:** [user], Claude (design partner)
**Evidence:** `install_lib.py:141-151`, `install.sh:232-234`; the Astraeus install (`docs/validation/brownfield-install-astraeus.md`)

---

## Context

### The defect that started it

`.claude/state.md` **is never updated after a fresh install** — customized or not.

It is not a tracked file. `install.sh:232-234` stamps it once from `state.md.template`. On update it goes through a separate loop (`install_lib.py:141-151`) whose own comment is explicit: *"Template plan — never auto-applied, only surfaced as advisory."* The output is `TEMPLATE-CHANGED state.md.template` — a notification that a file the user cannot see has changed. There is no `SKIP`, and `--force` does not reach it: `--force` operates on `FILES_SKIP`, which holds tracked files only.

So every install predating a template change is stale permanently. Slice 8 added `PR:` and `in-review`; slice 9 adds `Gated baseline:`. Neither reaches an existing install by any path except the user hand-editing a file they were told changed but not shown.

This is worse than the customization-skip behaviour it was mistaken for. A `SKIP` at least means "you diverged, so we left you alone." This means "nobody gets this, ever."

### The pack has four reconciliation strategies and no theory

| Artifact | Strategy | Where |
|---|---|---|
| tracked pack files | 3-state hash compare → UPDATE / SKIP / NEW; `--force` + backup | `install_lib.py:118-139` |
| `settings.json` | programmatic idempotent fragment merge | `install.sh:189-210` |
| `CLAUDE.md` | append orientation ref; `/claude-md-merge` for structure | `install.sh:247-327` |
| templates (`state.md`) | **advisory only, never applied** | `install_lib.py:141-151` |

Each was invented when its file needed one. Three work. The fourth is the defect above.

### The same question, one layer out

The Astraeus install surfaced a second cluster that looks unrelated and is not:

| Devkit wants to create | Astraeus already has |
|---|---|
| `docs/adr/` | `docs/ai/decisions.md` — ADR-001…012 |
| `docs/plans/` | `docs/ai/plans/`, `thoughts/shared/plans/` |
| `docs/findings.md` (ADR-0006) | `docs/reviews/` — 97 closed issues, `CQ`/`SD`/`AR`/`TD` taxonomy |
| `.claude/state.md` | `docs/ai/STATE.md` — reconciled by a hand-written note |

Every row above and every row in the previous table is the same question at a different layer: **this artifact already exists, in a shape devkit did not choose — now what?**

[ADR-0005](0005-brownfield-portability.md) answered that for **reads**: *read flexibly, write conservatively*. Nothing answers it for **writes over time**, which is what an update is. The result is four strategies where there should be one taxonomy, and a fourth case nobody noticed was broken.

## Decision

Classify every artifact the pack touches into one of three **dispositions**, each with a defined update contract. Record the disposition in the manifest so the installer acts on it rather than on file type.

### owned — the pack authored it and maintains it

`skills/`, `agents/`, `commands/`, `references/`, `hooks/`.

Contract is today's behaviour, which is correct: overwrite when the local copy matches what we installed; `SKIP` when the user modified it; `--force` overwrites with a backup to `.devkit-bak/`.

One addition: **a `SKIP` currently tells the user nothing about what they are forgoing.** It gains a summary of what changed in the new version, sourced from the same migrations file below. A user who customized `engineer/SKILL.md` should be able to decide whether the update is worth re-applying their edit.

### seeded — the pack stamps it once; the user owns it thereafter

`state.md`, `CLAUDE.md`, `settings.json`.

Contract: **migrations, not advisories.**

The pack ships `pack/MIGRATIONS.md` — sections keyed by pack version, each naming the structural changes to each seeded file:

```markdown
## 0.10.0

### `.claude/state.md`
- Add `**Gated baseline:** —` immediately after `**PR:**`.
  Records the last HEAD that passed gates 1–3 (ADR-0003 § Corrections, F5).
```

A new `/devkit-reconcile [<file>]` reads the installed version, reads `MIGRATIONS.md`, and **proposes** each unapplied change against the live file using `documenter`'s propose-before-write. The user confirms. Applying it is a judgement call the model can make — where does the field go if the user reordered the header? — which is exactly why the migration is prose rather than a patch.

`settings.json` keeps its programmatic merge: it is machine-readable, the merge is provably idempotent, and prose would be a downgrade. Seeded does not mean "must be model-applied"; it means "the user owns the file and we propose, never overwrite."

### discovered — the project may already have one

ADR registry, plans directory, findings/review system, project state doc.

Contract: **discover, record, defer.** `/adopt` finds what exists, records its location and shape, and the pack reads from it. Devkit never silently creates a parallel artifact next to a working one. Where the pack would write and something already exists, it **asks**: adopt the project's format, or keep devkit's alongside with an explicit note on which answers what.

ADR-0005 Fix 2 already implements this for the ADR registry. This ADR names the pattern and extends it.

### Where discovered locations are recorded

`.claude/.devkit-config.json` — the file [ADR-0004](0004-configurable-state-path.md) introduces.

**ADR-0004 is the first instance of this taxonomy, not a competitor to it.** It argued the config belongs beside `.devkit-manifest.json` because the installer already owns that directory; that reasoning holds for every discovered location. Its `--state-path` becomes one entry among several — ADR location and format, plans directory, findings location, state path.

### Manifest change

The manifest's `tracked` / `templates` split becomes a disposition per artifact, so the installer's plan is driven by declared intent rather than by which loop a file happens to fall into. `TEMPLATE-CHANGED` becomes `MIGRATION-PENDING <file> <version>`, which names an action instead of a fact.

## The forks, resolved

**Decision 1 — migrations are prose, not declarative patches.** A structured format would apply mechanically and fail the moment a user reorders a header or renames a section, which is the normal state of a file they own. Prose plus a model that reads the live file handles that. Cost: no mechanical guarantee, so `/devkit-reconcile` must show the proposed edit and get confirmation — which it does anyway.

**Decision 2 — `/devkit-reconcile` is a new command; `/claude-md-merge` is not renamed.** Renaming a shipped command breaks muscle memory and any user doc referencing it. `/claude-md-merge` stays the deep CLAUDE.md-structure tool; `/devkit-reconcile` handles version migrations across all seeded files. After slice 9 Task 3 both cite `references/claude-md-elements.md`, so they cannot drift the way `/adopt` and `/claude-md-merge` did.

**Decision 3 — discovered artifacts: ask, never auto-adopt the project's format.** Writing a finding into someone else's issue schema means inferring their conventions from examples and getting it subtly wrong in a file their team reads. *Write conservatively* applies: surface, ask, and default to not creating anything.

**Decision 4 — `settings.json` stays programmatic.** Classified seeded for ownership purposes, exempt from prose migrations because it is machine-readable and already correct.

## Alternatives considered

**Three-way merge with stored base content.** Keep a copy of every shipped file under `.claude/.devkit-base/` and run a real 3-way merge on update. Mechanical and well-understood. Rejected: it doubles the installed footprint, and conflict markers in a `SKILL.md` or a `state.md` produce a file that is worse than either input — markdown has no merge semantics, and the model reading it afterwards would treat the markers as content.

**Make everything owned and overwrite aggressively.** Simplest possible rule. Rejected: `state.md` holds live feature state and `CLAUDE.md` holds the user's conventions. Overwriting either is data loss.

**Keep advisories, but make them precise** — show the exact diff hunks. Cheapest, and it was the fallback in slice 9's plan. Rejected as the *general* answer because it scales linearly with user effort: every install, every version, forever, by hand. Retained as the interim for slice 9 (see *Build slice*).

**A `devkit doctor` command that reports drift without fixing it.** Useful, and orthogonal — it would report what `/devkit-reconcile` then fixes. Deferred; not needed to close this defect.

## Consequences

**Positive:**
- The template-staleness defect is closed for every seeded file, not just `state.md`.
- Four ad hoc strategies collapse into one taxonomy with three contracts, so the next artifact has a rule to be classified under rather than a strategy to be invented for it.
- `SKIP` on an owned file stops being silent.
- ADR-0006's ledger stops being a fifth review system on projects that already have one.
- ADR-0004 gains a general home rather than remaining a single-purpose knob.

**Negative / risks:**
- `MIGRATIONS.md` is a new maintenance obligation. Every seeded-file change must be written up or it silently doesn't ship — the same failure this ADR fixes, relocated. Mitigated by a test asserting that a changed `state.md.template` has a corresponding migration entry for the current version.
- Prose migrations can be misapplied by a model. Mitigated by propose-before-write; the user sees the edit.
- Two commands in the same neighbourhood (`/devkit-reconcile`, `/claude-md-merge`). Mitigated by the shared element reference and by distinct triggers — version migration vs structural reconciliation.
- A disposition-aware manifest is a schema change; old manifests need a read path. Mitigated by treating a manifest without dispositions as all-`owned` plus the current template list, which reproduces today's behaviour exactly.

**Open questions:**
- Should `/devkit-reconcile` run automatically at the end of `install.sh` when migrations are pending, or stay manual? Leaning: manual, and the installer prints the exact command — the installer should not require a model session to complete.
- Does `discovered` need a "the project's artifact is wrong for this purpose" escape? Leaning: no. If the user wants devkit's shape they say so when asked.
- Should the migration test also assert migrations are *ordered* and non-duplicated per version? Leaning: yes, cheap.

## Build slice

**Slice 10.** A manifest schema change, a new command, and a migrations file is not something to bolt onto slice 9, which is already twenty tasks.

**Build:**
- `pack/MIGRATIONS.md` — the format, seeded with the 0.9.x → 0.10.0 entries.
- `pack/commands/devkit-reconcile.md` — the command.
- `install_lib.py` — disposition-aware manifest; `MIGRATION-PENDING` replacing `TEMPLATE-CHANGED`; back-compat read path for dispositionless manifests.
- `install.sh` — surface pending migrations and the exact command to run; `SKIP` reports what changed.
- `tests/test_migrations.py` — a changed seeded template must have a migration entry for the current version; entries ordered and unique.
- Edit `pack/commands/adopt.md` — record discovered locations into `.devkit-config.json` rather than only into `CLAUDE.md` prose.
- Doc currency: amend [ADR-0006](0006-findings-ledger-and-plan-conformance.md) (findings ledger reclassified **discovered**); note in ADR-0004 that `.devkit-config.json` holds all discovered locations; `README.md`; `devkit-orientation.md`; `inventory-and-build-order.md`.

**Interim, in slice 9.** Slice 9 Phase 2 adds `Gated baseline:` to `state.md`, and without a mechanism no existing install receives it. Slice 9 gains one task that hand-writes `pack/MIGRATIONS.md` for the 0.10.0 entries and points the `TEMPLATE-CHANGED` advisory at it. That is the manual precursor; slice 10 generalizes what it did by hand.

**Dogfood:** on Astraeus — whose `state.md` was stamped fresh at v0.9.0 and so already has `PR:` but will not have `Gated baseline:` — run `/devkit-reconcile` after a slice-9 update and confirm the field is proposed in the right place, that the two-state-files note the user added by hand survives, and that a second run reports nothing pending.
