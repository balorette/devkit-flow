# CLAUDE.md canonical elements

Used by: `/claude-md-merge` (structural reconciliation), `/adopt` (Phase D, writing conventions).

**One definition, two consumers.** This file exists because they previously held two: `/adopt` required a literal `## Project conventions` heading while `/claude-md-merge` treated `## Conventions` as equivalent and therefore satisfied. Each was individually correct and jointly unresolvable — `/adopt` routed to `/claude-md-merge`, which correctly concluded nothing needed merging, and returned to `/adopt`, which hit the identical condition. The only escape was a rename `/claude-md-merge` had just called unnecessary. Any command reasoning about `CLAUDE.md`'s structure reads this file rather than restating it.

## The six elements

| # | Element | Recognition cue |
|---|---|---|
| 1 | **Title** — h1 with the project name | First non-blank line is `# <something>`. |
| 2 | **One-line description** | Non-blank line(s) after the h1, before the first `##`. |
| 3 | **`## How to read this project`** — the two sources of truth | An `##` heading named "how to read" / "orient" / "navigation" / similar, **and** content mentioning both `docs/` and the state file. |
| 4 | **Orientation reference blockquote** | A blockquote anywhere containing the literal `.claude/devkit-orientation.md`. Wording drifts between pack versions; presence of the path is the test. |
| 5 | **`## Project conventions`** | An `##` heading named "Project conventions" / "Conventions" / "Setup" / "Stack" / similar, holding language, runtime, test-runner, style, or branch-naming content. |
| 6 | **`## When in doubt`** | An `##` heading named "When in doubt" / "Getting started" / "Orientation" / similar, with an ordered list pointing at the state file and the active spec. |

## Classification

- **Present (exact).** At the expected place, satisfying the canonical role. No change.
- **Present (equivalent).** Exists under a different heading or location but covers the role. **Name the existing section and use it.** Default to leaving it as-is — gratuitous heading renames create churn. Propose a rename only where the user genuinely benefits from canonical naming.
- **Partial.** Some canonical content present, some missing. Propose only what's missing; do not rewrite what's there.
- **Absent.** No equivalent. Propose adding it at its placement default.

**An equivalent element is a satisfied element.** A command that needs to *write into* one writes into the equivalent it found. Requiring the canonical heading before writing is what produced the deadlock above.

## Placement defaults

Used when proposing an addition; override only where the file's existing structure makes another spot obviously better.

- **Orientation reference (4)** — between the description and the first `##`. If no description, immediately after the title. **Never at the bottom**; it is orientation content and belongs where it is read first.
- **`## How to read this project` (3)** — directly after the orientation reference. Together they form the orient block.
- **`## Project conventions` (5)** — after the orient block, before user-authored content sections. If a `## Setup` or `## Stack` covers similar ground, that *is* element 5.
- **`## When in doubt` (6)** — last `##` in the file.

## Machine-owned regions

Real `CLAUDE.md` files contain regions written by other tools. Detect them before writing anything:

```
<!--\s*([A-Z][A-Z0-9_]*):([a-z-]+)-(start|end)\s*(.*)-->
```

**Never write inside a matched start/end pair.** If a canonical element lives inside one, write **adjacent** — immediately before the start or after the end — and say why in the proposal. That text belongs to the other tool; it may be regenerated from a source file at any time, silently discarding anything devkit put there.

**Malformed or orphaned sentinels** — an unmatched `-start`, or an `-end` with no start — are treated as suspect. Do **not** infer the region's extent. Surface the orphan and ask. This is not hypothetical: the first brownfield target carried `GSD:conventions-start` with no matching end and a `GSD:architecture-end` with no matching start, left behind when that framework was retired, with its `## Conventions` section inside the orphaned region.

**Always name detected regions in the proposal**, including ones devkit did not need to touch. The user should see what devkit declined to write into, and why.
