# ADR-0005: Brownfield Portability — Read Flexibly, Write Conservatively

**Status:** Proposed
**Date:** 2026-08-03
**Deciders:** [user], Claude (design partner)
**Evidence:** [`docs/validation/brownfield-install-enterprise-api.md`](../validation/brownfield-install-enterprise-api.md) Findings 1, 2, 3, 11

---

## Context

The pack's first real brownfield install — Enterprise API, a mature FastAPI backend with an existing decision registry, an existing conventions section, and a retired predecessor framework still present in its `CLAUDE.md` — hit **three high-severity defects before any feature work began**, on a target the validation report calls "otherwise an ideal fit."

ADR-0002 designed `/adopt` for exactly this case. It correctly identified that a mature project's durable memory starts empty and needs bootstrapping. What it did not anticipate is that a mature project's memory is not empty — **it is full, and shaped differently.**

The four defects share one root cause: **devkit assumes its own shape is the target's shape.**

| Finding | The assumption | The reality at Enterprise API |
|---|---|---|
| 1 | Docs the skills cite are readable from the target | `docs/authoring-notes/spec-and-plan-depth.md` and `docs/design/walkthrough.md` exist only in the devkit repo; the installer copies neither |
| 2 | ADRs are files under `docs/adr/` | `ADR-001…012` live in `docs/ai/decisions.md` — a single file, at a different path |
| 3 | The conventions section is literally `## Project conventions` | `CLAUDE.md:161` is `## Conventions` |
| 11 | "Tests pass" means the runner devkit identifies | CI has **four** blocking gates; the fourth is `diff-cover … --fail-under=85` |

A fifth, found while designing this ADR: **`CLAUDE.md` in the wild contains regions owned by other tools.** Enterprise API's carries GSD sentinels at lines 137, 158, 160, and 189 — and they are *malformed*, with a `conventions-start` that has no matching `-end` and an `architecture-end` with no matching start, presumably from the *"retire GSD"* commit. `## Conventions` sits inside one of them. The pack has **no awareness of sentinel regions anywhere** in `/adopt` or `/claude-md-merge`.

Finding 2 is the sharpest: it doesn't error. `/feature-start` lists `docs/adr/*.md`, finds nothing, and creates `docs/adr/0001-*.md` while `ADR-001` already denotes something else — **silent duplication of a decision registry in a compliance-relevant project**, which is precisely the competing-sources-of-truth failure the pack exists to prevent.

## Decision

Adopt one principle and derive the fixes from it.

> **Read flexibly, write conservatively.** Devkit discovers where things actually are and adapts its *reads* to them. It never renames the user's structure, never writes inside a region another tool owns, and never silently picks when discovery is ambiguous. Adaptation buys tolerance on input, never license on output.

This bounds the "adapt up to a point" requirement precisely: the point is the write boundary.

### Fix 1 — install completeness (Finding 1)

Extract the depth material the skills actually need into `pack/references/spec-and-plan-depth.md`, which installs. This is the established pattern — `solid-checklist.md`, `clean-architecture-layers.md`, and `security-categories.md` were extracted the same way in Slices A–D.

Repoint `pm/SKILL.md:14`, `:330`, `:349` and `documenter/SKILL.md:192` at `.claude/references/spec-and-plan-depth.md`.

The `docs/design/walkthrough.md` citation is **dropped rather than installed**. It was cited as an illustrative exemplar; a target's own merged specs under `docs/specs/` are better exemplars because they are real-shape rather than illustrative. That also dissolves `:349`'s "when the walkthrough and the authoring note disagree" clause — with one source there is no disagreement to arbitrate. `adopt.md:92`'s citation of `docs/design/0002` becomes an inline statement of the rule.

**And a guard, so this cannot regress:** a test asserting that **no installed pack file cites a path that will not resolve inside a target**. Citations fall into three classes and the guard must distinguish them:

| Class | Example | Rule |
|---|---|---|
| Pack-installed | `.claude/references/solid-checklist.md` | Must exist under `pack/` at a `TRACKED_DIRS` path |
| Runtime-created target artifact | `docs/specs/<slug>.md`, `docs/domains/` | Allowlisted — created by the workflow |
| Devkit-repo-only | `docs/design/0002-*.md` | **Forbidden** in any installed file |

This promotes the ad-hoc cross-reference check used during slice 8 into an enforced invariant.

### Fix 2 — ADR registry discovery (Finding 2)

`/feature-start` Phase E must **discover before allocating**:

1. `docs/adr/*.md` — the canonical location.
2. Common alternates — `docs/decisions/`, `docs/adr.md`, `docs/decisions.md`, `docs/ai/decisions.md`.
3. A token scan across `docs/**/*.md` for `ADR-0*\d+`.

The highest number found **anywhere** is the floor; the next allocation is floor + 1. If a registry is detected outside the canonical location, **surface it and ask** — continue numbering in place, or start `docs/adr/` above the existing high-water mark. Never silently allocate `0001` when any registry exists.

`/adopt` gains a **discovery** step that records where ADRs live and the highest number, into `CLAUDE.md`'s conventions section. Discovery is not authoring: **ADR-0002 Decision 1 stands unchanged** — no retroactive ADRs are manufactured. The pack learns the registry exists without pretending to have written it.

*Integration note:* if ADR-0004's `.claude/.devkit-config.json` lands, the discovered ADR location belongs there rather than being re-discovered per feature.

### Fix 3 — one shared definition of CLAUDE.md's elements (Finding 3)

The deadlock exists because **two commands hold two different notions of "devkit-shaped."** `/adopt` requires the literal heading; `/claude-md-merge:38` treats `Conventions` / `Setup` / `Stack` as equivalent and `:44` defaults to leaving equivalents alone. Each is individually correct and jointly unresolvable.

Extract the canonical-element table into `pack/references/claude-md-elements.md` and have both commands cite it. `/adopt` Phase D then accepts an equivalent section and writes into it; it routes to `/claude-md-merge` only when **no** equivalent exists at all.

This makes the deadlock impossible *by construction* rather than by patching both sides to agree — the class of defect, not the instance.

### Fix 4 — sentinel-region safety (new)

Both commands detect machine-owned regions matching `<!--\s*([A-Z][A-Z0-9_]*):([a-z-]+)-(start|end)\s*(.*)-->`.

- **Never write inside a matched start/end pair.** If a section devkit wants lives inside one, write adjacent — before the start or after the end — and state why in the proposal.
- **Malformed or orphaned sentinels** (an unmatched start or end, as Enterprise API has) are treated as suspect: surface them and ask rather than guessing the region's extent.
- Detected foreign-tool regions are named in the proposal so the user can see what devkit declined to touch.

### Fix 5 — host CI gate discovery (Finding 11, `/adopt` half)

`/adopt` reads `.github/workflows/*.yml` and records the project's **blocking gate set** into `CLAUDE.md` conventions. `/feature-merge` Gate 1 then runs the discovered set rather than the set devkit inferred.

The general shape: *the pack assumes it knows what "tests pass" means; in any project with a CI config, that project already defines it.* Gate 1 currently runs tests, lint, and type-check, so it can pass and open a PR that CI fails immediately.

The Gate 1 half of this fix is sequenced with the slice-8 defect work, since it edits `/feature-merge`.

## The forks, resolved

**Decision 1 — extract-and-install, not inline (Fix 1).** Inlining the depth checklist into `pm/SKILL.md` would work and add no file, but the skill is already the pack's second-largest and the checklist is cited from two skills. Extraction matches the established precedent and keeps one copy.

**Decision 2 — discovery-and-ask, not a configurable ADR path (Fix 2).** ADR-0004 makes the *state* path configurable, and consistency argues for the same treatment here. Rejected for now on YAGNI: discovery plus a question solves the defect without adding a second config knob, and discovery is required regardless — a configured path that disagrees with reality reintroduces the bug. Configurability can follow if single-file registries prove common.

**Decision 3 — adapt to the user's heading, never rename it (Fix 3).** `/claude-md-merge:44` already says gratuitous renames create churn. Making `/adopt` agree is the smaller change and the one consistent with the principle.

**Decision 4 — write adjacent, don't refuse (Fix 4).** Refusing to proceed when a sentinel region is in the way would be safe and useless. Writing adjacent with a stated reason preserves both the other tool's ownership and devkit's usefulness.

## Alternatives considered

**Install the whole `docs/` tree into targets.** Fixes Finding 1 trivially and ships the authoring project's design docs, validation reports, and build order to every user. The pack is the deliverable; `docs/` is the project of building it. Rejected.

**Require targets to conform — document the expected shape and let users adapt.** That is the current behavior, and it is the defect. A pack that only works on projects shaped like its own examples is not portable.

**Make every path configurable.** Config-surface explosion, and each knob is another thing that can disagree with reality. Discovery is cheaper for the user and self-correcting.

## Consequences

**Positive:**
- The four defects that block a brownfield start are closed, and Fix 1's guard makes the install-completeness class non-recurring.
- Two shared references (`spec-and-plan-depth.md`, `claude-md-elements.md`) remove two sources of drift, one of which had already produced a deadlock.
- The write-boundary principle gives future commands a rule to derive from rather than a list of patches.

**Negative / risks:**
- Discovery adds a step to `/feature-start` and occasionally a question. Mitigated by caching the answer in `CLAUDE.md` conventions at `/adopt` time.
- Sentinel handling adds real complexity to two commands, for a case only some projects have. Justified by the silence of the failure — writing into another tool's region is destructive and invisible until regeneration.
- The pack grows two reference files. Both are extractions of existing content, not new material.

**Open questions:**
- Should the guard in Fix 1 run in `install.sh` as well as in tests? Leaning: tests only — the installer should not fail on the pack author's mistake at the user's machine.
- Is the alternates list in Fix 2 sufficient, or should discovery be a repo-wide token scan from the start? Leaning: alternates first, token scan as the fallback that already covers the tail.
- Does `/adopt` need to re-run discovery when a project's structure changes later? Leaning: yes, and it is already idempotent by design.

## Build slice

**Slice 9, Phase 1.** Sequenced first because these defects block *starting* on a brownfield target; the slice-8 defect fixes (Phase 2) block *finishing* the same dogfood run.

**Build:**
- `pack/references/spec-and-plan-depth.md` (extract), `pack/references/claude-md-elements.md` (extract).
- Edit `pack/skills/pm/SKILL.md` (:14, :330, :349), `pack/skills/documenter/SKILL.md` (:192), `pack/commands/adopt.md` (:92 inline; Phase D equivalence; ADR discovery; CI discovery; sentinels), `pack/commands/claude-md-merge.md` (cite the shared table; sentinels), `pack/commands/feature-start.md` (Phase E discovery).
- `tests/test_pack_references_resolve.py` — the Fix 1 guard.
- Doc currency: `docs/design/0002-brownfield-adoption.md` gains an amendment noting Findings 1–3 and that Decision 1 is unchanged; `README.md`; `pack/devkit-orientation.md` gains the "`.claude/` is pack-owned" note from Finding 12's generalizable lesson.

**Dogfood:** re-run `install.sh` against Enterprise API, then `/adopt`. Verify: no dangling references; ADR discovery finds `ADR-001…012` in `docs/ai/decisions.md` and asks rather than allocating `0001`; Phase D writes into `## Conventions` without a rename; the GSD sentinel regions are detected, named, and not written into; the CI gate set including `diff-cover` is recorded.
