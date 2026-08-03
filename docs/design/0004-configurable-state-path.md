# ADR-0004: Configurable State-File Path

**Status:** Proposed
**Date:** 2026-08-03
**Deciders:** [user], Claude (design partner)

---

## Context

The pack hardcodes `.claude/state.md` as the location of its working pointer. That assumption is
load-bearing in one place that is *code* and roughly fifteen places that are *prose*, and it collides
with any project that already keeps a state document.

The collision is not hypothetical. It surfaced on the pack's **second-ever install target**
(Enterprise API, a Python/FastAPI backend) before a single command had run. That project keeps
`docs/ai/STATE.md`, and had merged a PR two weeks earlier whose entire purpose was to eliminate
competing sources of truth — establishing `docs/ai/` as canonical and retiring a rival planning tree.
An installer that drops a second file named "state" into that project reintroduces exactly the
problem that PR closed.

That timing is the evidence worth acting on. **A project mature enough to want this pack's discipline
has probably already grown some form of state document.** Greenfield projects are the case where
owning `.claude/state.md` outright is free; they are also the case least likely to install a pack
built around spec-first rigour and three closeout gates. The pack's install story is weakest exactly
where its value proposition is strongest.

### Two kinds of hardcoding, with different failure modes

**Code — one site, and it fails silently.** `pack/hooks/doc-drift-detector.py:82-84`:

```python
state_md = project_root / ".claude" / "state.md"
if not state_md.exists():
    return 0  # no devkit state — hook is a no-op
```

The soft return is correct for the idle case (no active feature, nothing to check) and dangerous for
the misconfigured one. A missing or relocated state file produces **exactly the same observable
behaviour as a correctly installed pack with no feature in flight**: silence. A user who resolves the
collision by moving or renaming the file loses drift detection and gets no signal that they have.
This is the "silence is not success" failure mode, inside the one component whose whole job is to
make drift visible.

**Prose — roughly fifteen sites, and they fail interpretively.** `pack/skills/pm/SKILL.md:47`,
`pack/skills/engineer/SKILL.md:58`, `pack/skills/documenter/SKILL.md` (six references),
`pack/commands/build.md` (four), `pack/commands/plan.md:9`, `pack/devkit-orientation.md` (eight), and
`pack/CLAUDE.md.template:14,26` all instruct the model to read or write `.claude/state.md` by literal
path. These do not crash; a model told to read a file that is not there will improvise — search for
something similar, proceed without it, or ask. All three are worse than a clear failure.

### What the collision actually is

Worth stating precisely, because it determines whether a *path* knob is even the right fix.

The two documents share a word, not a job:

| | `.claude/state.md` | A typical project state doc |
|---|---|---|
| Audience | machine-first; regex-parsed `**Field:** value` | human-first narrative |
| Cadence | changes per *build step* | changes per *slice* or release |
| Lifetime | cleared at `/feature-merge` | never cleared; accretes history |
| Content | active feature, branch, phase, spec, plan, next step | milestone, shipped work, known gaps, how to run the gates |

So the fix is **not** to merge them. Pointing the pack at a human state doc would put `/feature-merge`'s
clearing step inside a file holding release history and verification baselines — a destructive cadence
and a durable one in one file. Enterprise API resolved its own install by keeping both files with a
cross-reference line in each, which is the right answer for that project and requires no pack change
at all.

What the knob buys is narrower and still worth having: **the pack should not force a naming collision
it does not need.** A project that wants devkit's pointer at `.devkit/state.md`, or
`docs/ai/devkit-state.md`, should be able to say so at install time instead of accepting a file whose
name implies more authority than it has.

## Decision

Make the state-file path configurable, resolved once and consistently by both the code and the prose
surfaces.

Sketch, to be settled in the plan:

- **Single source of truth for the path.** An install-time value written to a location both the hook
  and the pack docs can name — most likely `.claude/.devkit-config.json` alongside the existing
  `.devkit-manifest.json` and `.devkit-version`, since the installer already owns that directory and
  writes both.
- **Hook reads it**, falling back to `.claude/state.md` when no config exists — so existing installs
  keep working untouched.
- **Prose references become indirect.** The pack docs stop naming a literal path and refer to "the
  state file (see `.claude/devkit-orientation.md`)", with the orientation doc naming the configured
  path once. This is the larger part of the work and the part most likely to be done inconsistently.
- **`install.sh` gains a flag** (`--state-path`), defaulting to today's value.

### The hook's soft-fail is fixed regardless of the knob

Independent of configurability, `doc-drift-detector.py` should distinguish *"no active feature"* from
*"state file not found where configured"*. The first is a legitimate silent no-op. The second is a
misconfiguration the user should hear about once. This is a small change and arguably the highest-value
part of the slice, since it converts a silent failure into a loud one.

## Alternatives considered

**Do nothing; the path is part of the pack's contract.** Defensible, and it keeps every reference
pointing at one known location. Rejected because the cost lands entirely on the projects best suited
to the pack, and because the failure mode when a user works around it by hand is silent.

**Symlink at install time.** Zero pack changes; the hook reads through a symlink transparently.
Rejected: it forces the target file to carry the machine fields *and* accept `/feature-merge` clearing
them, which is only safe when the target is a dedicated pointer — in which case the symlink bought
nothing.

**Support a list of candidate paths, first match wins.** Rejected as implicit: two state files in a
repo would make behaviour depend on search order, which is the ambiguity this ADR is trying to remove.

## Scope

**In:** the hook's path resolution and its missing-file diagnostic; the prose sweep across skills,
commands, orientation, and the `CLAUDE.md` template; `state.md.template` placement; the `install.sh`
flag and its `--dry-run` output; update-mode handling for an already-installed project.

**Out:** merging the pointer with a project's human state doc (explicitly rejected above); changing
the state file's *format* or fields; multi-project or per-worktree state; migrating an existing
install's state file automatically — a documented manual move is enough.

## Build order

**After slice 8's dogfood, not before.** Slice 8 is authored but unvalidated
(`docs/validation/slice-8.md`: *"authoring complete; dogfood pending"*), and it touches
`state.md.template` itself by adding the `PR` field and the `in-review` phase. Sequencing this slice
first would mean sweeping prose references that slice 8's dogfood may still change.

There is also a dependency worth naming in the other direction: slice 8 needs *"a GitHub-remote
project with reviewers"* as its dogfood target and has none assigned. Enterprise API is that project — it
has the remote, an automated reviewer already leaving findings on PRs, and a live PR lifecycle. The
install that motivated this ADR is also the validation slice 8 has been waiting for.
