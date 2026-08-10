# CLAUDE.md

This file is for Claude Code working *on* this project — the authoring of a compositional skill-pack for Claude Code itself. It is **not** the CLAUDE.md that will ship with the pack to end users; that's a separate deliverable.

## What this project is

A skill-pack for Claude Code that enforces a specific engineering shape: domain-driven feature breakdown, spec-first development, TDD/SOLID/Clean Architecture, branch-per-feature, and living documentation. Composes the best of Obra Superpowers (TDD discipline), SpecKit (spec rigor), and GSD (branch loop) using native Claude Code primitives rather than building a parallel framework.

The design is fully documented in `docs/design/`. Read those before authoring anything:

- `docs/design/0001-skill-pack-architecture.md` — the architecture and rationale
- `docs/design/comparison-table.md` — why this synthesis instead of extending an existing framework
- `docs/design/walkthrough.md` — what the workflow looks like end-to-end
- `docs/design/inventory-and-build-order.md` — every component and the slice-by-slice build plan

If a question can be answered from those four docs, answer it from those four docs. They are the source of truth for design decisions.

## The shape of the pack (summary)

**Subagents (3):** `architect`, `tester`, `security-reviewer` — each gets fresh context because isolation is load-bearing for what they do.

**Skills (4):** `engineer`, `documenter`, `pm`, `grill-me` — instructions the main thread follows; no isolated context needed.

**Slash commands (5):** `/feature-start`, `/plan`, `/build`, `/checkpoint`, `/feature-merge`.

**Hook (1):** `doc-drift-detector` — `PostToolUse` warning system for edits outside active spec scope.

**Memory layout:** `docs/` for durable human-first artifacts (specs, plans, ADRs, domains, summaries, findings) + `.claude/state.md` as the machine-first working pointer.

## Status

History lives in git + `docs/validation/`. This section describes the pack as it stands and what's left to validate.

### Shipped

- **Subagents:** `architect`, `tester`, `security-reviewer`, `conformance-reviewer`
- **Skills:** `engineer`, `documenter`, `pm`, `grill-me`
- **Slash commands:** `/feature-start`, `/plan`, `/build`, `/checkpoint`, `/feature-merge`, `/pr-review` (+ housekeeping: `/adopt`, `/claude-md-merge`)
- **References:** `pack/references/` — `solid-checklist.md`, `clean-architecture-layers.md`, `security-categories.md`, `findings-triage.md`, `spec-and-plan-depth.md`, `claude-md-elements.md`
- **Migrations:** `pack/MIGRATIONS.md` — structural changes to the *seeded* files (`state.md`, `CLAUDE.md`), which the installer never rewrites
- **Hook:** `doc-drift-detector` (`PostToolUse`; warns on edits outside the active spec's `owned_files`)
- **Tests:** `tests/test_doc_drift_detector.py` (drift-hook behaviour) and `tests/test_pack_references_resolve.py` (no installed pack file may cite a path that won't resolve in a target — an enforced invariant, not a convention). Stdlib `unittest`, no pytest (the pack installs into arbitrary projects and can't assume a runner). Run with `python3 -m unittest discover -s tests`. Everything else in this repo is markdown, verified by behavioral prediction + fresh-session run per working principle 4.
- **Templates:** `pack/CLAUDE.md.template` (slim — defers orientation to a separate installed file), `pack/state.md.template`
- **Pack orientation:** `pack/devkit-orientation.md` (memory layout, workflow commands, commit cadence, automated guards)
- **Installer:** `install.sh` + `install_lib.py`. Idempotent. Manifest-based update path with customization detection, default-skip on user-modified files, `--force` overwrite with backup to `.devkit-bak/`, template-change advisories, `--dry-run`. Flags: `--project-name`, `--description`, `--mainline`, `--force`, `--dry-run`.
- **README** (root): install / update path / components map / end-to-end walkthrough / memory layout / disciplines / uninstall.

### Dogfood state (Enterprise Agent)

Target: `enterprise-agent` (Google ADK + LiteLLM personal-assistant agent at `~/Code/enterprise-agent`).

- **`master`:** merged `notes-write-and-delete` feature (commit `e899a28`, 2026-06-05). Pack install present but stale — does not yet include commit-discipline edits, update-path machinery, CLAUDE.md split, or `grill-me`.
- **`feature/notes-write-and-delete-services-and-tools`:** in-flight follow-up. 5 build steps + spec + plan complete (NoteQueryService, NoteWriteService, SqliteNoteRepository, tools.py, agent wiring); 101 tests passing; entire feature in one commit `c81bda0` (the gap that triggered the commit-discipline pass). Ready for `/feature-merge`.
- **`feature/notes-read-and-search`:** superseded by `notes-write-and-delete`; retained per supersede mechanic.
- Summary doc: `docs/summaries/notes-write-and-delete.md`. First-of-domain doc: `docs/domains/notes.md`.

### Validated end-to-end

- Brainstorm → spec → branch → plan → build → checkpoint → security review → summary → merge proposal on a real feature.
- Installer 8-step lifecycle: fresh → customize → bump → default update → bump again → default update → `--force` update → template-change.
- CLAUDE.md split across 5 install paths: fresh+no-CLAUDE.md, fresh+existing-no-ref+accept, fresh+existing-no-ref+decline, fresh+existing-with-ref, update from a simulated old-style install.

### Outstanding

**Not yet dogfood-validated:**

- **Slice 9 — Enterprise API findings (2026-08-03).** All twelve findings from the first brownfield install, in three phases: brownfield portability ([ADR-0005](docs/design/0005-brownfield-portability.md)), the six slice-8 defect fixes ([ADR-0003 § Corrections](docs/design/0003-pr-lifecycle-and-findings-triage.md)), and the findings ledger + `conformance-reviewer` ([ADR-0006](docs/design/0006-findings-ledger-and-plan-conformance.md)), plus a hand-written `MIGRATIONS.md` as the interim for [ADR-0007](docs/design/0007-artifact-dispositions.md). **Four behavioural predictions are recorded and unrun** in `docs/validation/slice-9.md`. Needs the full end-to-end dogfood on the brownfield target — install, `/adopt`, then one feature through to PR closeout. **Finding 1 of the follow-up PR #139 review is [ADR-0007](docs/design/0007-artifact-dispositions.md) `:128`'s risk actually occurring** — a seeded-template change shipped with an incomplete `MIGRATIONS.md` entry — which is why slice 11 lands that guard early instead of waiting on slice 10.
- **Slice 10 — artifact dispositions.** Designed in ADR-0007, unplanned. Generalises what slice 9's task 21 did by hand: owned/seeded/discovered as declared dispositions, a `/devkit-reconcile` command, and a disposition-aware manifest. Until it lands, every seeded-file change must be hand-written into `MIGRATIONS.md` or it silently ships to nobody — the same defect, relocated.
- **Slice 11 — Step invariants (2026-08-10).** Eight pack findings from a second automated-review round on the Enterprise API 0.10.0 upgrade and first `/adopt` run (`docs/validation/pr139-pack-findings.md`, PR #139), closed by three named clauses in [ADR-0008](docs/design/0008-step-invariants.md): an artifact and its carrier commit together, never infer "what changed" from state the pack itself wrote, and discovery precedes every consumer. Net changes: `tests/test_migrations_snapshot.py` + `pack/templates/history/<version>/` (release guard); `pack/references/adr-registry.md` absorbing discovery/allocation restated across `/feature-start`, `pm`, and `architect`; `/plan` Phase G and `/pr-review` Phase D each gain the commit that carries what they write; `/feature-merge`'s `Gated baseline` relocated to the tip before the transition commit with a content-diff discriminator excluding `.claude/state.md`; `/pr-review all` scoped to leave the own-reply filter intact; `.claude/` ownership rescoped to the manifest's tracked set. Ships as **0.11.0** (the `VERSION` bump and 0.11.0 template snapshot are the plan's final task and have not landed yet). **Behavioral predictions are recorded and unrun** in `docs/validation/slice-11.md` (not yet landed). Slice 10 (artifact dispositions, ADR-0007) remains unbuilt; slice 11 does not depend on it — the numbering is deliberate, not a gap. Needs the Enterprise API dogfood: reopen the PR, change nothing, confirm `/feature-merge` runs no gates.

- **PR lifecycle + findings triage (slice 8)** — authored 2026-07-30; design in `docs/design/0003-pr-lifecycle-and-findings-triage.md`, plan in `docs/plans/slice-8-pr-lifecycle.md`, authoring record in `docs/validation/slice-8.md`. Net changes: new `pack/references/findings-triage.md` (the consumer-side discipline for evaluating any finding, internal or external) and `pack/commands/pr-review.md` (intake/triage/response across all three GitHub comment surfaces, re-runnable, nothing posts unseen); `/feature-merge` gains flow detection, a Phase-branch table making it re-runnable, the `gh pr create` path, and phase-aware async closeout; `state.md` gains `Phase: in-review` and a `PR:` field; documenter gains *Review notes* + *The summary as PR body*; engineer cites findings-triage for tester/architect output. No installer change needed (`TRACKED_DIRS` already covers `commands/` and `references/`). **Four behavioral predictions are recorded and unrun** — T6b (nothing posts to a PR before user confirmation) blocks the slice rather than merely revising it. Needs a GitHub-remote project with real reviewers.
- **Slice 9 — scoped but not authored.** The `debugger` skill (the pack has no debugging discipline at all; `/build`'s halt conditions hand off to a process that doesn't exist) and a `reviewer` subagent as a pre-PR gate 4 covering the cross-step lens no current component owns. Both were scoped during the 0003 discussion and deliberately deferred; rationale in that ADR's *Context* and *Consequences*.

- **Brownfield adoption (`/adopt`, slice 7)** — authored 2026-06-22; design in `docs/design/0002-brownfield-adoption.md`. Net changes: new housekeeping command `pack/commands/adopt.md` (surveys conventions into `CLAUDE.md`, discovers + confirms the existing domain map, writes terse `docs/domains/` baselines with an *as-built rationale* subsection, opt-in sparse ADRs; propose-before-write; `state.md` stays idle; incremental/idempotent; optional `<area>` scope); `pm` research-phase edit to cite captured `CLAUDE.md` conventions instead of re-deriving; `install.sh` closing-message pointer; `devkit-orientation.md` housekeeping entry; slice-7 section in `inventory-and-build-order.md`. Resolved design forks: no manufactured retroactive ADRs (as-built rationale lives in domain docs); thin-base-then-grow; plan-time dedup via citation. **The second-project install is its dogfood** — running `/adopt` on a second project validates the command *and* closes the standing "second-project install" item below.
- **Commit-discipline edits** (engineer skill Verify substep 5, `/build` halt condition, `/feature-start` Phase H, `/plan` Phase G, `/checkpoint` propose-then-decline, `CLAUDE.md.template` commit-cadence section). Validates the next time a real `/build` runs against an updated install.
- **`grill-me` skill** and its `/feature-start` Phase B + `/plan` Run-section auto-invocation. Validates on Enterprise Agent's next brainstorm.
- **`pack/CLAUDE.md.template`** on a second target. Second-project install is the only honest test that it stands on its own.
- **addyosmani/agent-skills borrows (Slices A–D)** landed 2026-06-12. Net changes: anti-rationalization tables added to engineer / tester / security-reviewer / documenter; `pack/references/{solid-checklist,clean-architecture-layers,security-categories}.md` extracted and engineer + security-reviewer updated to cite them; `pack/references/` wired into installer (`install.sh`, `install_lib.py`) + memory-layout doc; pm gained a quick-reference architect-invocation table with documenter cross-reference; README and devkit-orientation gained a Define/Plan/Build/Verify/Review/Ship lifecycle mapping. Validates on Enterprise Agent's next `/build` (rationalization defense) and the next `/feature-merge` (security-reviewer citing the categories reference).
- **CLAUDE.md merge UX (2026-06-15)** landed three pieces: (a) `install.sh` now shows a diff-style preview of the proposed append before the Y/n prompt and mentions `/claude-md-merge` as the structured-merge alternative; (b) new `--claude-md-only` install flag with early-exit, useful for re-entering just this step after declining or after a pack template change; (c) new pack-shipped slash command `pack/commands/claude-md-merge.md` — interactive reconciliation of an existing `CLAUDE.md` against the six-element canonical structure (title, description, *How to read this project*, orientation reference, *Project conventions*, *When in doubt*) using documenter's *propose before writing* discipline; idempotent; not gated on an active feature. TEMPLATE-CHANGED advisory updated to suggest `/claude-md-merge`. Validates on Enterprise Agent's next pack update — re-run `install.sh` against Enterprise Agent to pick up the slash command, then exercise it on Enterprise Agent's hand-merged `CLAUDE.md` to test the messy case.

**Polish items.**

Authored 2026-06-30 (polish pass, pending dogfood):

- **documenter skill** — cardinal-discipline section now covers the multi-doc merge-time scenario (propose the whole doc set as one batch before writing any); fixed two stale slice-5-hook "(not yet shipped)" lines to present tense.
- **`/feature-merge`** — precondition now distinguishes uncommitted *tracked* changes (block) from untracked files (surface + ask, since an untracked file may be a forgotten source file); merge-strategy determination elevated to its own `### Merge strategy` subsection (CLAUDE.md convention → infer from history → ask).
- **Package-manifest surfacing in `/feature-merge` summary** — was never actually implemented (only the security-reviewer sampled deps); added a *Dependency / manifest changes* bullet to the documenter summary checklist. Still needs a dogfood with a real manifest change to exercise.
- **`/checkpoint` stale language** — the slice-5-hook "(when shipped)" framing is now present-tense (`doc-drift-detector` is shipped).

Still pending dogfood only (no authoring left):

- **`/checkpoint` Pattern C (park)** — fully authored; never exercised end-to-end.

**Natural next dogfood.** Re-run `install.sh` against Enterprise Agent's `.claude/` (picks up commit-discipline + update path + CLAUDE.md split + `grill-me`), then either:

- (a) `/feature-merge` on `feature/notes-write-and-delete-services-and-tools` to exercise the gate trio + the polish items + `/checkpoint` commit proposal, or
- (b) start a small new feature on Enterprise Agent (e.g., the deferred `add ruff + mypy + pre-commit` follow-up) to exercise commit-discipline + grilling end-to-end.

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

## Working principles for this project

These are non-negotiable for the *authoring work*, not just the eventual pack:

1. **Native-first.** Use Claude Code's actual primitives (subagents, skills, slash commands, hooks, CLAUDE.md) before inventing anything new. If a problem can be solved by a built-in mechanism, that's the answer. The pack exists to compose primitives, not replace them.

2. **Dogfood every meaningful addition.** Each pack component is independently usable. After adding or changing a component, validate it on a real feature in a real project before moving on. Don't author the next thing until the current one has survived contact with reality.

3. **Design docs are the contract.** If implementation diverges from the design docs, one of two things must happen before continuing: (a) update the design doc to reflect the new decision (with rationale), or (b) revert the implementation to match the design. Do not allow silent divergence. This is the same doc-currency discipline the pack itself will eventually enforce — practice it during authoring.

4. **TDD on the skill content where it makes sense.** Skills are markdown, not code, but they can still be tested behaviorally: write a small example task that exercises the skill, predict the expected behavior, then load the skill in a fresh Claude Code session and run the task. If behavior diverges from prediction, the skill needs revision — not the prediction.

5. **Small reversible steps.** The Karpathy discipline applies to authoring too. Author one component at a time. Commit. Validate. Move on. Resist the urge to write the whole skill-pack in one session and review at the end.

6. **No artifact bloat.** The walk-through committed to four durable docs per feature. If, during authoring, an urge to produce a fifth durable artifact appears, that's a signal to either (a) consolidate into an existing artifact or (b) update the design doc with a reasoned argument for why the fifth is necessary. Don't just add it.

## Directory layout (this project)

```
.
├── CLAUDE.md                       (this file)
├── README.md                       (high-level project overview for humans)
├── docs/
│   ├── design/                     (the four design docs — read-mostly)
│   │   ├── 0001-skill-pack-architecture.md
│   │   ├── comparison-table.md
│   │   ├── walkthrough.md
│   │   └── inventory-and-build-order.md
│   ├── authoring-notes/            (decisions made during authoring)
│   └── validation/                 (dogfood reports)
├── pack/                           (the skill-pack itself, the actual deliverable)
│   ├── CLAUDE.md.template          (the CLAUDE.md that ships with the pack)
│   ├── devkit-orientation.md       (installs to .claude/; pack-owned orientation)
│   ├── skills/
│   │   ├── engineer/SKILL.md
│   │   ├── documenter/SKILL.md
│   │   ├── pm/SKILL.md
│   │   └── grill-me/SKILL.md
│   ├── agents/
│   │   ├── architect.md
│   │   ├── tester.md
│   │   └── security-reviewer.md
│   ├── commands/
│   │   ├── feature-start.md
│   │   ├── plan.md
│   │   ├── build.md
│   │   ├── checkpoint.md
│   │   └── feature-merge.md
│   └── hooks/
│       ├── doc-drift-detector.py
│       └── settings.json.fragment
├── tests/                          (stdlib unittest; covers the drift hook — the only executable code)
│   └── test_doc_drift_detector.py
└── examples/                       (fabricated example projects used for dogfood)
```

The split between `docs/` and `pack/` is deliberate: `docs/` is about the project of building the pack; `pack/` is the pack. When dogfooding, the contents of `pack/` get copied into a real target project's `.claude/` directory.

## Conventions for this project's docs

- Design docs in `docs/design/` are versioned by edit, not by filename. Change history goes in git, not in `-v2.md` filenames.
- Authoring notes capture *why a skill was written this way* when the reasoning isn't obvious from the skill itself. They're not required for every skill — only for non-obvious choices.
- Validation reports document what happened during dogfooding: what worked, what didn't, what changed in the pack as a result.

## Conventions for the pack itself (`pack/`)

Skills follow Claude Code's `SKILL.md` format with YAML front-matter:

```yaml
---
name: <skill-name>
description: <triggering conditions in plain language>
---
```

Subagent files use the standard Claude Code agent definition format.

Slash command files use the standard Claude Code command format.

Where Claude Code's primitives are ambiguous or evolving, document the choice in an authoring note. Do not hard-code assumptions that might be wrong; prefer comments like `# When Claude Code's subagent format stabilizes, revisit this.`

## What "done" looks like for this project

- All shipped pack components dogfood-validated on a real feature
- Pack has been used end-to-end on at least one real feature beyond Enterprise Agent (second-project install)
- The pack's own CLAUDE.md template (`pack/CLAUDE.md.template`) is written and tested
- README in this project explains how to install the pack into a target project

This project is finished when someone unfamiliar with the design can install the pack and use it without reading any of the four design docs. The pack must stand on its own.

## When in doubt

1. Re-read the relevant design doc.
2. If the design doc doesn't answer it, the design doc is incomplete — surface that gap explicitly rather than guessing.
3. Never silently extend the design. Either ask, or update the design doc with rationale.