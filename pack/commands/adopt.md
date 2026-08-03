---
description: Bootstrap the durable memory of an existing codebase newly adopting the pack. Surveys conventions into CLAUDE.md, discovers and confirms the existing domain map, writes terse baseline `docs/domains/<domain>.md` docs, and (only for decisions you flag as load-bearing-and-reversible) writes ADRs. Propose-before-write throughout; `state.md` stays idle. Incremental, idempotent, and optionally scoped to one area. Not gated on an active feature.
---

Bring an existing project to "a solid base" — the durable memory the devkit lifecycle reads — before the feature loop runs. One `/adopt` invocation surveys the repo, proposes the things `/feature-start` and `/plan` expect to already exist (`CLAUDE.md` conventions, `docs/domains/`), and writes the ones you confirm.

`/adopt` is **housekeeping**, not feature work. It is not gated on an active feature. Run it once after `install.sh` on a mature codebase, before your first `/feature-start`. Re-run it later to deepen coverage or document a new area.

Why it exists: every orient phase in the pack assumes durable memory already exists — the `pm` skill reads `docs/domains/` to ground decomposition, `/plan` cites `CLAUDE.md` conventions, the `architect` checks the project's ADRs for contradictions. On a project that grew the pack organically, that memory accretes feature by feature. On a project adopting the pack mid-life, it's empty. `/adopt` fills the spine so the first feature is as well-grounded as the tenth.

## Arguments

`/adopt [<area>]`

- **No argument** — document the *spine*: the project's core domains plus the conventions block. Not every domain; the few that carry the project (see Decision 2 in the design note). Deepen later with re-runs.
- **`<area>`** — a directory or subsystem (e.g., `src/billing`, `chungar/notes`). Scopes the entire pass to that area. The natural move when you're about to start a feature: `/adopt` the area it touches, then `/feature-start`.

## Preconditions

1. `.claude/devkit-orientation.md` exists (the pack is installed). If absent, stop and recommend `./install.sh` first.
2. `CLAUDE.md` exists in the project root. If absent, stop and recommend `./install.sh` (fresh-stamp from template is cleaner than reconstructing).
3. The working tree is a git repo. `/adopt` proposes a commit at the end; without git there's nowhere to land it (surface and continue read-only if the user insists, but default to stopping).

`/adopt` does **not** require `state.md` to be idle, but it's best run when it is — adoption is a baseline activity, not mid-feature work. If `state.md` shows an active feature, note it and ask whether to proceed anyway (the user may legitimately want to backfill a domain doc mid-feature); don't refuse.

Load the `documenter` skill — it is the workhorse for every write this command proposes, and its *propose before writing* discipline governs the whole run.

## Run

The loop is **survey → discover → confirm → propose-and-write → commit**. The `documenter` skill supplies the write discipline; the `pm` skill's domain heuristic supplies the decomposition lens (run in reverse: discover existing contexts rather than propose new ones); the `architect` subagent is invoked only for a genuinely ambiguous boundary call, on the same criteria as everywhere else in the pack.

### Phase A — Survey conventions

Survey the repo and assemble a proposed `## Project conventions` block for `CLAUDE.md`. Cover what a fresh Claude Code session would otherwise have to infer:

- Language + version; package manager.
- Test runner; lint / format / typecheck config.
- DI / wiring pattern; composition-root location.
- Import style (relative vs absolute, suffixes, barrels).
- Error / result shape (exceptions vs `Result`-style; project-local helpers).
- Logging / config access (singletons vs injection; env vs file; the project-wide config object).
- Branch naming, commit conventions, anything else load-bearing.
- **Blocking CI gates** — see below. Record them as their own list; `/feature-merge` Gate 1 runs it.

**Blocking gates.** Read `.github/workflows/*.yml` **and `*.yaml`** (GitHub Actions accepts both, and a project using `.yaml` would otherwise look like it has no CI at all), plus `.gitlab-ci.yml` / `.gitlab-ci.yaml` and `Makefile` targets named `ci` / `check` / `verify` if present and extract the commands that actually gate a merge. Record them **verbatim**, with `file:line` evidence like every other entry.

This is what `/feature-merge` Gate 1 runs. Without it the pack asserts its own definition of "tests pass" — and a project with a CI config has already defined it. The first brownfield target had four blocking gates where devkit checks three; the fourth was a coverage-delta check, which is invisible to a plain test run. Gate 1 would have passed and opened a PR that CI failed on the first push.

If no CI config exists, say so and record nothing — Gate 1 falls back to the runner it infers, and should say that it is inferring.

**Existing review / findings system.** Look for somewhere the project already tracks findings that outlive a single change: a `docs/reviews/` tree, an `issues/` directory, a `docs/**/*review*` corpus, or a stated tracker convention in `CLAUDE.md` or `CONTRIBUTING.md`. Record the location and its shape (per-finding files vs a single table vs an external tracker), and whether it uses its own ID scheme.

`documenter` writes findings to whatever this records. If it finds nothing, the pack creates `docs/findings.md`; if it finds something, `/feature-merge` and `/pr-review` **ask** whether to adopt that format or sit alongside it. Skipping this step is how devkit becomes the fifth review system on a project that already had a working one — the duplication the pack's whole brownfield posture exists to prevent.

**Every entry carries `file:line` evidence.** This is the same rule the `/plan` research phase enforces — no folk knowledge. The format is the evidence table the `pm` skill already uses:

```markdown
| Convention | Evidence | Note |
|---|---|---|
| Relative imports within a package | `src/agent.py:3` `from .config import Config` | New files follow `from .module import X` |
| Pytest, mirrored test layout | `pyproject.toml:21`; `tests/notes/test_*.py` | Tests under `tests/<area>/`, `test_*.py` |
```

If a convention isn't observable (no file demonstrates it yet), it isn't a convention — leave it out. `/adopt` records what *is*, not what *should be*.

When scoped to an `<area>`, survey conventions within that area; don't claim project-wide conventions from one subsystem.

### Phase B — Discover and confirm the domain map

Run the `pm` skill's extend-vs-introduce heuristic in reverse: cluster the existing code (within `<area>` if scoped) into bounded contexts. For each, note the slug, a one-line responsibility, and the files/directories it owns.

Propose the map to the user as a list — one line per domain — and **wait for confirmation**. The user merges, splits, renames, or drops entries. This is the cheap correction point, exactly as domain decomposition is in `/feature-start`; correcting the map here is far cheaper than after docs are written.

Invoke the `architect` subagent (fresh context, `subagent_type: architect`) **only** when a boundary is genuinely ambiguous — "is this one context or two?" where the answer constrains future work. Reflect its recommendation back before adopting it. Do not invoke it to rubber-stamp an obvious clustering.

Default to the spine: if the repo has many candidate contexts, propose the few that carry the project and say so ("Proposing the 4 core domains; re-run `/adopt` to document the rest"). Silent truncation reads as "covered everything" — name what you're deferring.

### Phase C — Write the domain docs

For each **confirmed** domain, draft a terse `docs/domains/<slug>.md` and propose it before writing (documenter discipline). Keep it lean — a starting point the documenter will keep current at future merges, not an exhaustive manual:

```markdown
# <Domain name>

<One-sentence purpose.>

## Responsibilities

- <what this context owns>

## Key types & entry points

- `<Type/function>` — `<file:line>` — <one line>

## Dependencies

<What it depends on and the direction. Note any inward/outward rule the code follows.>

## As-built rationale

<Why it's shaped this way — the decision context that would otherwise be lost.
This subsection is where "why" lives at adoption time, NOT a retroactive ADR.
Do not manufacture ADRs for decisions already made — an ADR is written only for
a decision you flag as load-bearing AND plausibly reversible. Keep this to what's
genuinely load-bearing.>
```

Create `docs/domains/` if it doesn't exist. If a domain doc already exists (re-run), propose a **delta** against it — don't overwrite; add what's missing or deepen a thin section.

### Phase D — Conventions into CLAUDE.md

**Resolve the conventions section using `.claude/references/claude-md-elements.md` — element 5, including its equivalence set.** A section named `## Conventions`, `## Setup`, `## Stack`, or similar **is** the conventions section. Write into it. Do not propose a rename: an equivalent element is a satisfied element.

Propose writing the Phase A block into that resolved section (replacing the `{{LIST_PROJECT_CONVENTIONS_HERE}}` placeholder if present), via the documenter's propose-before-write.

**Before writing, check for machine-owned regions** per that reference's *Machine-owned regions* section. If the resolved section sits inside another tool's sentinel pair, write **adjacent** to the region rather than inside it, and say why — that text may be regenerated from a source file at any time, silently discarding whatever devkit put there.

Route to `/claude-md-merge` **only when no equivalent exists at all**. Requiring a literal `## Project conventions` here while `/claude-md-merge` treats equivalents as satisfied is what produced an unresolvable loop on the first brownfield target: `/adopt` routed out, `/claude-md-merge` correctly found nothing to merge, and `/adopt` hit the same condition again. `/adopt` fills the conventions slot; `/claude-md-merge` builds one only when there is none.

### Phase E — Discover the ADR registry, then contested decisions (opt-in, sparse)

**Discovery first, and it is not authoring.** Before anything else in this phase, find out whether the project already keeps decision records, and where:

- **Scope:** `*.md` under `docs/`, plus root-level `*.md`. Never `.git/`, `node_modules/`, `vendor/`, or anything matched by `.gitignore`.
- **Match, two patterns.** In file *contents*: `ADR[-_ ]?0*\d+`, case-insensitive. In *filenames*: `^0*\d{1,4}[-_]` under any directory whose name suggests decision records (`adr`, `adrs`, `decisions`, `rfc`, `rfcs`), **excluding date-prefixed names** matching `^\d{4}-\d{2}-\d{2}` — dated notes are not ADR numbers, and treating `2026-04-15-review.md` as one sets the high-water mark in the thousands. A numbered-filename registry may never spell "ADR" in its contents at all.
- **Rank definitions above mentions** — a heading (`## ADR-012: …`) or a filename (`0012-*.md`) is a definition; inline prose citing `ADR-007` is a mention. Report which kind the high-water mark came from.

Record the result in `CLAUDE.md` conventions: *"ADRs live in `<path>` (`<format>`); highest is `<N>`."*

The **location** is the durable part. The recorded number is a snapshot, not an authority: `/feature-start` and `/plan` both re-scan for the current highest before every allocation, because features allocate continuously while this record is written once. Recording it is still worth doing — it makes the registry's shape visible to a human reading `CLAUDE.md` — but nothing allocates from it.

Registries turn up in shapes a fixed list would miss — the first brownfield target kept `ADR-001 … ADR-012` as headings inside a **single decisions log**, not a directory of files. Without this step `/feature-start` would have found no `docs/adr/`, started at `0001`, and created a second document claiming `ADR-001`.

**Discovery records; it does not write ADRs.** The default below is unchanged.

Default: **write no ADRs.** As-built rationale lives in the domain docs (Phase C), not in reconstructed ADRs — manufacturing retroactive ADRs wholesale is the bloat this command avoids.

Write an ADR **only** when, during the run, the user flags an existing decision as both *load-bearing* and *plausibly reversible* (a future feature might want to revisit it). For each such case:

1. Invoke the `architect` to frame the decision, its alternatives, and the trade-offs as they stand today.
2. Write the ADR **to the registry discovered above**, in that registry's format and at its next free number — `docs/adr/NNNN-<short-name>.md` only when discovery found nothing. Use `status: accepted` and an explicit opening line: *"Documents a pre-existing decision; adoption date is not the original decision date."*
3. Reference it from the relevant domain doc.

If nothing is flagged, skip this phase entirely and say so.

### Phase F — Commit and hand off

`state.md` stays `idle` — adoption is not a feature and creates no active state. Do not touch the top fields.

Propose a single commit of what this invocation produced: the new/updated `docs/domains/*.md`, the `CLAUDE.md` conventions edit, and any Phase-E ADRs. Stage these paths explicitly; never `git add -A` (same reasoning as the engineer skill's commit substep — adoption often runs on a repo with untracked detritus the `.gitignore` doesn't cover yet). Subject: `adopt: baseline domain docs + conventions` (append ` (<area>)` when scoped). Body: one short paragraph naming the domains documented and any ADRs.

Wait for confirmation; on decline, leave the proposal visible and stop without committing. The user may want to split (domains vs CLAUDE.md vs ADRs) — let them.

Then surface, in one short message: the domain docs written, the CLAUDE.md change, any ADRs, the commit status, and a one-line next step — "Review the domain docs and conventions; when ready, run `/feature-start \"<idea>\"` (or re-run `/adopt <area>` to document more)."

## Idempotency

A second `/adopt` run after an accepted first run proposes **deltas, not duplicates**: it detects existing domain docs and the filled conventions block, and only offers what's new or thin. A clean re-run on a fully-documented area reports "nothing to add." If a re-run re-proposes content that already landed, the first run's edits didn't apply cleanly (read the files to see what's there) — treat as a bug in this command.

## Halt conditions

Stop and surface, without writing anything, when:

- A precondition fails (pack not installed; no `CLAUDE.md`; not a git repo and the user wants the commit).
- `CLAUDE.md` isn't devkit-shaped and the user declines to run `/claude-md-merge` first (Phase D can't place the conventions cleanly).
- The architect returns a domain-boundary recommendation that conflicts with what the user said they wanted — reflect and re-confirm; don't silently pick one.
- The repo is large enough that the domain map is unclear even after the architect — surface the ambiguity and propose scoping to an `<area>` instead of guessing a whole-repo map.

## What this command does not do

- **Does not generate user-facing docs** (READMEs, guides, API docs). It produces only the three base artifacts — conventions, domain docs, opt-in ADRs. Scope creep into "document the whole project" is out.
- **Does not manufacture ADRs.** See Phase E / Decision 1.
- **Does not create an active feature or touch `state.md`'s top fields.** Adoption is idle-state housekeeping.
- **Does not rewrite existing domain docs.** Re-runs propose deltas only.
- **Does not require an active feature**, unlike `/checkpoint` and `/feature-merge`.

## How this command plugs into the pack

- **`documenter` skill** — the workhorse; every write follows its propose-before-write discipline.
- **`pm` skill** — its domain-decomposition heuristic, run in reverse, drives Phase B. After `/adopt` populates `CLAUDE.md`, the pm skill's plan-time research phase **cites** the captured conventions instead of re-deriving them (see the pm skill's research section).
- **`architect` subagent** — invoked only for ambiguous boundaries (Phase B) and to frame opt-in ADRs (Phase E).
- **`/claude-md-merge`** — the prerequisite when `CLAUDE.md` isn't yet devkit-shaped (Phase D).
- **`install.sh`** — its closing message points existing-project users here.
