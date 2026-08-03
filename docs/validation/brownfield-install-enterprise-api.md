# Brownfield Install — Validation Report (Enterprise API)

**Target:** Enterprise API — Python 3.11 / FastAPI / SQLAlchemy backend, ~200 source files, compliance-relevant
**Pack version:** 0.9.0
**Install:** `chore/install-devkit`, [example-corp/enterprise-api#137](https://github.com/example-corp/enterprise-api/pull/137)
**Status:** **install succeeded; 11 defects found by automated review before any pack command ran**
**Date:** 2026-08-03

---

## What this is

The README names the pack's untested case precisely:

> it has not yet been installed by a stranger on a fresh second project, which is the real
> "stands on its own" test.

This is that test — with two differences from the imagined version. The project is **mature**, not
fresh: it carries 13 ADRs, an established `docs/ai/` tree, its own `.claude/` agents and commands, and
a four-gate CI pipeline. And the findings came from **two automated reviewers on the install PR**
(Codex and Cursor Bugbot) reading the vendored pack files as ordinary source, rather than from running
`/feature-start`.

That last point is the report's main caveat. **No pack command has been executed.** Every finding
below is a static-review defect. The behavioral-prediction run that `CLAUDE.md` working principle 4
requires has not happened, so nothing here validates that the pack *works* — only that eleven things
in it are wrong, most of which a dogfood would have hit later and more expensively.

The install itself was clean: 21 files, no filename collisions, `settings.json` created, hook wired,
`.gitignore` correctly left alone (entries already present).

---

## Finding 1 — the installer ships dangling references (install completeness)

**Severity: high.** Blocks the first `/feature-start` or `/plan` on any target.

`pack/skills/pm/SKILL.md` and `pack/skills/documenter/SKILL.md` point at two authoring documents that
**the installer never copies**:

| Referenced path | In devkit repo | In install target |
|---|---|---|
| `docs/authoring-notes/spec-and-plan-depth.md` | ✅ | ❌ |
| `docs/design/walkthrough.md` | ✅ | ❌ |

Four live references (`pm/SKILL.md:14`, `:330`, `:349`; `documenter/SKILL.md:192`), and
`pm/SKILL.md:349` makes one of them normative — *"the authoring note is the source of truth for depth.
When the walkthrough and the authoring note disagree, the authoring note wins."* A model asked to
resolve that disagreement in an installed project finds neither file.

`pm/SKILL.md:14` hedges with *"the devkit project's `docs/authoring-notes/…`"*, which is accurate but
does not help: the reader has no copy of the devkit project. `:330` and `:349` carry no such
qualifier and read as target-relative paths.

**Options:** install both into `.claude/references/` (where four reference docs already live and where
the pack's own precedent points); or inline the depth checklist into the skill and cite the walkthrough
by description rather than path.

The general defect is worth naming beyond these two files: **nothing checks that the installed pack's
internal references resolve inside the target.** A `grep` for backtick-quoted `docs/…` paths across
`pack/` at build or install time would have caught this and will catch the next one.

---

## Finding 2 — the ADR allocator ignores an existing registry (brownfield)

**Severity: high.** Silent corruption of an existing decision registry.

`pack/commands/feature-start.md:79`:

> Find the next free ADR number by listing `docs/adr/*.md` and incrementing the highest.
> […] If `docs/adr/` doesn't exist, create it.

Enterprise API stores **ADR-001 … ADR-012** in `docs/ai/decisions.md` — a single file, not a directory, and
not at that path. `docs/adr/` does not exist. So the first architectural feature creates
`docs/adr/0001-*.md` while `ADR-001` already denotes something else, and the `architect` subagent
starts with no knowledge of twelve prior decisions it may contradict.

`/adopt` does not rescue this: Phase E defaults to **writing no ADRs**, deliberately, to avoid
manufacturing retroactive ones. That decision is right for *authoring* and leaves *discovery*
unaddressed — the pack never learns the registry exists.

**This is the sharpest brownfield gap found.** A duplicate ADR number in a compliance-relevant project
is not cosmetic; two documents claiming `ADR-001` is exactly the "competing sources of truth" problem
that pack discipline exists to prevent.

**Options:** teach `/adopt` to *discover and record* the registry's location and highest number
(without authoring ADRs); make the ADR path and format configurable, since single-file registries are
common; or refuse to allocate when a plausible existing registry is detected and ask.

---

## Finding 3 — `/adopt` and `/claude-md-merge` deadlock on an equivalent heading (brownfield)

**Severity: high.** Unresolvable without a manual edit each command advises against.

- `pack/commands/adopt.md` Phase D requires a literal `## Project conventions` section. If absent:
  *"stop this phase and route through `/claude-md-merge` first."*
- `pack/commands/claude-md-merge.md:38` treats *"Project conventions" / "Conventions" / "Setup" /
  "Stack" / similar* as **equivalent** and therefore satisfied.

Enterprise API's `CLAUDE.md:161` is `## Conventions`.

So `/adopt` routes to `/claude-md-merge`, which correctly concludes nothing needs merging, and
returns to `/adopt`, which hits the identical condition. The loop has no exit. The user's only escape
is renaming the heading — which `/claude-md-merge` has just told them is unnecessary.

**Fix:** `/adopt` Phase D should accept the same equivalence set `/claude-md-merge` recognises. One
shared definition of "the conventions section," referenced by both, rather than two.

---

## Finding 4 — the hook anchors relative paths to the wrong directory

**Severity: medium.** Another silent no-op. Reported by Cursor Bugbot.

`pack/hooks/doc-drift-detector.py:70-74`:

```python
cwd_str = payload.get("cwd") or "."
project_root = Path(cwd_str).resolve()

try:
    rel_path = Path(edited_path).resolve().relative_to(project_root)
except (ValueError, OSError):
    return 0
```

The payload's `cwd` is read for `project_root` but **not used to anchor `edited_path`**. When the
tool supplies a relative path, `Path(edited_path).resolve()` anchors to the *hook process's* working
directory. If that differs from the payload's `cwd`, resolution either lands outside `project_root`
(→ `ValueError` → `return 0`) or, worse, resolves to a real file that is the wrong one.

**Fix:** anchor explicitly — `Path(edited_path)` when absolute, `project_root / edited_path` when not.

This compounds the concern in [ADR-0004](../design/0004-configurable-state-path.md): it is the second
distinct route by which the drift detector silently stops detecting drift. **Both fail closed and
silent, and silence is the hook's normal idle output.** There is no observable difference between
"working, nothing to flag" and "broken." That pattern — not either individual bug — is the thing to
fix.

---

## Findings 5-10 — slice 8's PR lifecycle, reviewed but not yet run

Six findings land on slice 8 (`docs/plans/slice-8-pr-lifecycle.md`), which `docs/validation/slice-8.md`
records as *"authoring complete; dogfood pending. No behavioral prediction has been run."*

**This is that slice's first external scrutiny.** It is not the dogfood — no `/feature-merge` or
`/pr-review` was executed — but it is six defects found before the dogfood, which is a cheaper place
to find them.

| # | Where | Severity | Defect |
|---|---|---|---|
| 5 | `feature-merge.md:24` | P1 | **No gated-baseline SHA recorded at PR open.** The two `in-review` branches must distinguish commits present when the gates passed from commits pushed later. Only `Phase` and the PR URL are stored. After `/pr-review` pushes a fix, local and remote tips agree, so a rerun can take the "no new commits" path and skip tests, docs reconciliation, and security review entirely. Store the last successfully gated `HEAD`; compare against the PR tip every rerun. |
| 6 | `feature-merge.md:96` | P1 | **Closeout docs are written but never committed before integration.** `docs/summaries/<feature>.md` and any domain/state updates are authored after the clean-tree precondition, and no commit is proposed before the subsequent `git push` / `git merge`. Both transport only committed changes: the PR omits the summary; a local merge leaves it untracked. |
| 7 | `feature-merge.md:151` | P1 | **Post-merge state is written on the wrong branch.** PR creation never checks out mainline, so the closeout invocation is normally still on `feature/<slug>`. The idle-state transition is written there, uncommitted, and mainline retains the feature's prior active/building state. Check out mainline, write, commit, *then* propose the push. |
| 8 | `feature-merge.md:80` | P2 | **Security gate uses a two-dot diff.** When mainline advances after the branch diverges, `git diff <mainline> HEAD` renders upstream-only commits as removals in the feature's diff, so the `security-reviewer` can report or block on changes the feature never made. Use the merge-base form (`A...B`, or `--merge-base`). |
| 9 | `pr-review.md:34` | P2 | **Dedupe covers only one of three surfaces.** Inline threads have an already-answered test via `in_reply_to_id`; review bodies and top-level comments are answered with fresh `gh pr comment` calls recording nothing. A second pass re-fetches the original item *and* the pack's own prior reply, and can propose duplicates. Persist handled IDs, or emit a stable marker, across all three surfaces. |
| 10 | `pr-review.md:64` | P2 | **Replies are posted before the fix is pushed.** If the push then fails (auth, network, rejected non-fast-forward), public replies already cite SHAs the remote cannot resolve, against code the PR still doesn't contain. The command's reply-failure halt handles the inverse case only. Push, verify the remote tip, then reply. |

Findings 5 and 9 share a root cause worth stating once: **the pack has no persistent record of what it
has already done to a PR.** Both are instances of inferring prior work from current Git or GitHub
state, which is not sufficient when the pack's own actions are among the things that changed that
state.

---

## Finding 11 — Gate 1 doesn't discover the project's actual CI gates

**Severity: medium.** Generalizes beyond this target.

`feature-merge.md:58` runs tests, lint, and type-checking. Enterprise API's CI has **four** blocking gates —
the fourth is `diff-cover coverage.xml --compare-branch=origin/main --fail-under=85`, documented as the
pre-push baseline in the project's own `docs/ai/STATE.md`.

So Gate 1 can pass and open a PR that CI fails immediately. The gate is *a* test gate, not *the*
project's gate.

The general shape: the pack assumes it knows what "tests pass" means. In any project with a CI config,
that project already defines it. Reading `.github/workflows/*.yml` (or an explicit
`CLAUDE.md`-declared gate list) during `/adopt`, and running the discovered set in Gate 1, would make
the gate mean what the project means by it.

---

## Finding 12 — disputed: "bare print" in the hook

**Filed P1 by Codex. Does not survive checking, with one residue.**

The claim: `doc-drift-detector.py:122` executes *"a bare `print`"* violating the repository's logging
invariant, citing Enterprise API's `AGENTS.md:L21`.

The code:

```python
# Out of scope — surface a warning. Stderr is what the harness shows
# to the model as additional context after the tool runs.
print(
    f"devkit drift-detector: edit touched `{rel_path_str}` …",
    file=sys.stderr,
)
```

It is not bare — it is explicitly directed to stderr, with a comment stating why. Stderr **is** the
hook's output channel to the model; routing it through a logging framework would not reach the model
and would contradict the pack's stdlib-only requirement for this file.

The finding is also scoped wrongly: it applies the *host repository's* conventions to a vendored,
pack-owned file. Enterprise API lints `src/` and `tests/` only; `.claude/` is not in its ruff path.

**Residue worth keeping:** ruff's `T201` does flag `print()` regardless of `file=`, so a
`--select ALL` run over the hook — which devkit might reasonably adopt for its one Python file —
would flag line 122. If devkit ever lints the hook, that line wants `# noqa: T201` with the stderr
rationale, not a rewrite.

**The generalizable lesson is about the install, not the hook.** Vendored pack files land inside a
host repository and are read by that repository's reviewers under that repository's rules. Expect
findings of this shape on every install. A short note in `devkit-orientation.md` explaining that
`.claude/` is pack-owned — versioned by the pack, not by the host's conventions — would give reviewers
and users the right frame.

---

## What this changes

**Ranked by what I'd fix first:**

1. **Findings 1, 2, 3 — brownfield adoption is the pack's weakest surface.** All three are hit before
   any feature work begins, on a target that is otherwise an ideal fit. ADR-0002 covers brownfield
   adoption; these are amendments to it, and arguably justify a slice.
2. **Findings 5-10 — slice 8, before its dogfood.** Six defects in an unvalidated slice. Fixing them
   first makes the eventual dogfood a test of the design rather than a rediscovery of these.
3. **Finding 4 + [ADR-0004](../design/0004-configurable-state-path.md) — the hook's silent-failure
   class.** Two independent routes to a silent no-op, in the component whose entire job is making
   drift visible.
4. **Finding 11 — host CI discovery.** Real, general, and larger than it looks.

**Sequencing note.** ADR-0004 sequences the configurable-state-path work after slice 8's dogfood.
Findings 5-10 change that calculus: slice 8 now has six known defects to fix, and fixing them is a
prerequisite to a dogfood that means anything.

**On the dogfood itself.** Enterprise API remains the right target — `docs/validation/slice-8.md` asks for
*"a GitHub-remote project with reviewers"* and this project has two automated reviewers actively
leaving findings on PRs, plus a live PR lifecycle. What this report demonstrates is that the target
works. It does not demonstrate that the pack does.
