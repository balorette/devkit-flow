---
description: Reconcile the project's CLAUDE.md against the canonical devkit-compliant structure. Reads CLAUDE.md, detects missing or semantically-overlapping sections, and proposes section-by-section merges with the documenter skill's "propose before writing" discipline. Idempotent — running on an already-compliant CLAUDE.md reports "nothing to merge." Not gated on an active feature; usable anytime.
---

Drive an interactive merge between the project's existing `CLAUDE.md` and the canonical structure a devkit-compliant `CLAUDE.md` should have. One `/claude-md-merge` invocation walks the user through every chunk that needs adding or reconciling and leaves the file with a clean structure that supports `/feature-start`'s orient phase, the documenter skill's *what lives where* map, and the doc-drift hook's expectations.

`/claude-md-merge` is **housekeeping**, not feature work. It is not gated on an active feature — run it before adopting the pack, after declining `install.sh`'s append prompt, or after a pack update changed the canonical template.

**Clause 1 exception:** this command may run before a project is a git repository — its preconditions require only `CLAUDE.md` and `.claude/devkit-orientation.md`, and neither implies a repo. With no repo there is no carrier commit to propose, so ADR-0008 clause 1 does not apply here and this command names no staging step; the user commits at their own cadence. Stating the exception is required rather than optional: an unstated one is indistinguishable from the oversight the clause exists to catch. `/adopt` writes the same artifact and does **not** qualify, because it gates on being a repo and always has somewhere to commit.

## Arguments

None. Operates on `CLAUDE.md` in the current working directory (the project root).

## Preconditions

1. `CLAUDE.md` exists in the project root. If absent, stop and recommend `./install.sh` instead — fresh-stamp from template is cleaner than reconstructing from scratch.
2. `.claude/devkit-orientation.md` exists. If absent, stop and recommend running `install.sh` first — the orientation reference points at that file, so writing the reference before the file exists creates a dangling pointer.

If either fails, surface it with the recommended remediation and exit. Load the `documenter` skill and proceed when both pass.

## Run

The loop is **read → detect → propose chunk-by-chunk → apply confirmed → summarize**. The documenter skill's *Pattern A — User-described change* is the procedural template; this command supplies the *what to check for* (the canonical structure) and the placement defaults.

### Phase 1 — Read

Read the full `CLAUDE.md`. Note: line count, top-level headings (`#` and `##`), and any blockquote that looks like a previously-installed orientation reference.

### Phase 2 — Detect

Read `.claude/references/claude-md-elements.md`. It defines the six canonical elements, their recognition cues, the four classifications (present-exact / present-equivalent / partial / absent), and the placement defaults. **It is the single definition** — this command does not restate it, because two commands holding two copies is exactly what produced an unresolvable loop with `/adopt`.

Classify each of the six elements against the target's `CLAUDE.md`.

**Before proposing any write, detect machine-owned regions** per that reference's *Machine-owned regions* section. Never write inside another tool's sentinel pair; write adjacent and say why. Name every detected region in your findings, including ones you did not need to touch.

### Phase 3 — Propose chunk-by-chunk

**Placement defaults** are defined in `.claude/references/claude-md-elements.md`. Override one only where the existing file's structure makes a different placement obviously better — and say so in the proposal.

**Proposal shape.** For each element classified as partial or absent (and equivalent elements where you're proposing a non-trivial reconciliation), produce a proposal of this shape:

````markdown
**Element <N>: <name>** — <classification>

<one-sentence finding: what's there, what's missing>

Proposed change:
```diff
+ ## <heading>
+
+ <content>
```

Placement: <where the diff lands — line number or "after section X" / "end of file">.

Accept / modify / skip?
````

Surface proposals **one at a time** (or as a small batch of 2–3 when tightly coupled — e.g., elements 3 and 4 together as the orient block). Wait for the user's call on each before moving on. The documenter cardinal discipline holds: never apply a proposal silently, and never bundle so many proposals at once that the user can't review each.

For an **equivalent** classification where the proposal is "leave as-is," surface as informational only:

```markdown
**Element <N>: <name>** — present (equivalent)

You have `## Setup` (line 23) covering this role. Content is materially equivalent to the canonical "Project conventions" section. Leaving as-is.
```

Informational items don't need confirmation. The user can override (request a rename or restructuring) by saying so.

### Phase 4 — Apply

For each accepted proposal, edit `CLAUDE.md` to apply it. Use `Edit` for precise insertions; do not rewrite the whole file. Preserve user-authored content exactly — only the six canonical structural elements are in scope for this command.

If the user modified a proposal (e.g., "yes but use 'Stack' instead of 'Project conventions' as the heading"), apply the modified version. If the user skipped a proposal, do not apply it; note the skip for the summary.

### Phase 5 — Summarize

End with a short summary in this shape:

```markdown
CLAUDE.md merge complete.

Applied:
- <element> — <one-line description>
- <element> — ...

Skipped (by your choice):
- <element> — <reason if given>

Already present (no change):
- <element>

Equivalent (left as-is):
- <element> — <existing section cited>
```

If anything was skipped, end with a one-line nudge: "Re-run `/claude-md-merge` later to revisit skipped items."

Do not propose a git commit. CLAUDE.md edits are project housekeeping; the user commits at their cadence. This command's preconditions require only `CLAUDE.md` and `.claude/devkit-orientation.md` — no git repo — so it may run somewhere with no commit to propose; it relies on clause 1's outside-a-repo exception rather than omitting the carrier by oversight.

## Idempotency

Running `/claude-md-merge` twice in a row should produce no further changes the second time, assuming the first run's proposals were accepted (or skipped items remain skipped). If the second run surfaces new proposals, either:

- The first run's edits didn't apply cleanly (read the file directly to see what landed).
- The detection rules have a non-deterministic edge case — treat as a bug in this command.

A clean idempotent run on a compliant file produces:

```markdown
CLAUDE.md merge complete.

Already present (no change):
- Title
- Description
- How to read this project
- Orientation reference
- Project conventions
- When in doubt
```

## Halt conditions

Stop and surface, without applying anything, when:

- `CLAUDE.md` does not exist (precondition).
- `.claude/devkit-orientation.md` does not exist (precondition).
- The existing `CLAUDE.md` is in a format the canonical structure doesn't model (e.g., it's a stub redirecting to a different file). Surface the situation; do not force canonical structure on top.
- The user declines every proposed chunk in a row — they may prefer a different approach. Pause and ask whether to abandon the run.
- A proposal would touch user-authored content outside the six canonical elements. That's out of scope; surface and skip.

## What this command does not do

- **Does not touch `.claude/devkit-orientation.md`.** That file is pack-owned; the installer manages it.
- **Does not touch any other doc** (`docs/`, READMEs, etc.). `CLAUDE.md` only.
- **Does not commit.** The user commits at their cadence. Unlike `/adopt`, this command has no git precondition, so it cannot assume a commit is available to propose — the stated exception is clause 1's outside-a-repo case, not an oversight.
- **Does not rewrite user-authored content.** Project conventions, custom sections, prose the user wrote — all left alone. Only the canonical structural elements are in scope.
- **Does not require an active feature.** Unlike `/checkpoint` and `/feature-merge`, this command is project housekeeping and runs whether `.claude/state.md` shows an active feature or `none`.

## How this command plugs into the pack

- **`install.sh`** points at this command in two places: (a) the existing-CLAUDE.md prompt at fresh install ("decline and run `/claude-md-merge` for a structured merge"); (b) the TEMPLATE-CHANGED advisory at update mode ("run `/claude-md-merge` to walk a structured merge after the pack template changed"). The `--claude-md-only` install flag is the script-side equivalent for re-entering just the simple append path.
- **`documenter` skill** is loaded for the propose-before-writing discipline. This command's Phase 3 follows the skill's Pattern A shape.
- **No state.md interaction.** This command does not read or update `.claude/state.md`. It operates only on `CLAUDE.md`.
