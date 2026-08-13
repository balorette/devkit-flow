# ADR-0010: Cursor as a Second Host

**Status:** Proposed
**Date:** 2026-08-13
**Deciders:** [user], Claude (design partner)
**Evidence:** Cursor's own documentation, read 2026-08-13 — [Agent Skills](https://cursor.com/docs/skills), [Subagents](https://cursor.com/docs/subagents), [Hooks](https://cursor.com/docs/hooks), [Third Party Hooks](https://cursor.com/docs/reference/third-party-hooks), [Rules](https://cursor.com/docs/rules), [Plugins reference](https://cursor.com/docs/reference/plugins), [Help: Rules](https://cursor.com/help/customization/rules). Claims the docs do not make are quarantined in *What the docs do not say*; nothing in the Decision rests on them. Per `pack/references/evidence-and-uncertainty.md` § *Facts*, every capability claim below is a quotation or a citation, not a recollection.

---

## Context

The question this ADR answers: **what would it take to run this pack on Cursor projects.**

The pack is built on working principle 1 — native-first, compose the host's primitives rather than building a parallel framework. That principle is what makes the question tractable at all, and it is also what makes the answer counter-intuitive.

### The finding that reframes the question

**Cursor already loads four of the pack's five installed surfaces, unmodified.** It is not a port of 3,699 lines. It is a port of *one surface*, plus four semantic losses, three of which are silent.

| Pack surface | Cursor behaviour | Source |
|---|---|---|
| `.claude/skills/*/SKILL.md` (4 skills) | **Loaded.** "For compatibility, Cursor also loads skills from Claude and Codex directories: `.claude/skills/`…" | Skills |
| `.claude/agents/*.md` (4 subagents) | **Loaded.** Project subagents are read from `.cursor/agents/`, `.claude/agents/`, `.codex/agents/`; "`.cursor/` takes precedence over `.claude/`" on name conflict | Subagents |
| `.claude/settings.json` hooks | **Loaded.** `PostToolUse` → `postToolUse`; `Edit` → `Write`; both flat and `hookSpecificOutput` response shapes accepted | Third Party Hooks |
| `CLAUDE.md` | **Loaded, and always.** "Cursor reads `CLAUDE.md` files the same way it reads `AGENTS.md`… `CLAUDE.md` files are always applied to every conversation, regardless of any `alwaysApply` frontmatter setting." | Help: Rules |
| `.claude/references/*.md` (9 files) | **Needs no mechanism.** The pack cites them by path and the model reads them on demand; a file that exists at the cited path works on any host | — |
| `.claude/state.md` | **Needs no mechanism**, same reason — prose reads and writes it | — |
| `.claude/commands/*.md` (8 commands) | **Not loaded.** No Cursor doc names `.claude/commands/` as a discovery root | — |

Two preconditions attach to the first three rows: Settings → Rules, Skills, Subagents → **Include third-party Plugins, Skills, and other configs**, and "the feature must be enabled for your account."

The pack's front-matter survives this by luck that isn't entirely luck. Skills declare `name` and `description` — both required by Cursor's `SKILL.md` schema, no unsupported fields. Subagents declare `name`, `description`, and `tools`; the first two are Cursor fields, and the third is the loss discussed below. Commands declare only `description` — no `name` — which is the one place the pack would need an added field rather than a removed one.

### The one surface that does not load

Eight commands, ~1,320 lines: `/feature-start`, `/plan`, `/build`, `/checkpoint`, `/feature-merge`, `/pr-review`, `/adopt`, `/claude-md-merge`. This is the orchestration layer — the phase machines, the preconditions, the halt conditions, the `**Writes:**` declarations clause 1 is enforced against. Without it the pack is four skills and four subagents with no loop to run them in.

Cursor's documented shape for this is a skill with explicit invocation:

> Set `disable-model-invocation: true` to make a skill behave like a traditional slash command, where it is only included in context when you explicitly type `/skill-name` in chat.

`.cursor/commands/` still loads — a community-confirmed path, and command deeplinks in the docs still reference the directory — but the commands documentation page has been removed, and the built-in `/migrate-to-skills` skill treats commands as a *migration source*, converting them "to skills with `disable-model-invocation: true`, preserving their explicit invocation behavior." Authoring new work against the legacy shape would be building on the one primitive in scope that Cursor is visibly moving off.

### Four semantic losses

Cursor's subagent front-matter has no `tools:` allowlist. The only documented restriction is a boolean: `readonly`, which "runs with restricted write permissions (no file edits, no state-changing shell commands)." Otherwise "subagents inherit all tools from the parent." All four of the pack's subagents encode their contract in an allowlist, and the allowlist is doing different work in each.

| Subagent | Claude Code | Cursor | Assessment |
|---|---|---|---|
| `architect` | `Read, Glob, Grep` | `readonly: true` | **Equivalent or stronger.** Nothing lost. |
| `security-reviewer` | `Read, Glob, Grep, Bash` | `readonly: true` | **Probably fine, unverified.** It needs `git diff`; whether `readonly` classifies that as state-changing is undocumented. |
| `conformance-reviewer` | `Read` | `readonly: true` | **Degraded.** Its own text: "Your only tool is `Read`… no `Bash`, no `Glob`, and no `Grep`." Under `readonly` it gains all three. |
| `tester` | `Read, Write, Glob, Grep` | `readonly: false` — no restriction available | **Inexpressible.** |

The `tester` case is the sharpest thing in this ADR. Its description ends "**returns test files and findings, runs nothing**," and in Claude Code that guarantee is not prose — it is the *absence of `Bash` from the allowlist*. The tester cannot run tests because it has no tool that runs anything. Cursor cannot express "may write files, may not execute," because `readonly` is one boolean and the tester needs the write half. So it inherits `Shell`.

A tester that can run tests can iterate toward green, and iterating toward green is precisely the failure the fresh-context red-phase split exists to prevent. ADR-0001 called that isolation load-bearing for TDD integrity. On Cursor, the mechanism that bears the load is gone and only the sentence remains.

**The drift hook goes mute** — the third loss, and the one that fails in this project's most familiar shape. `doc-drift-detector.py` prints its warning to **stderr** and always exits `0`; its own docstring names the mechanism it relies on: "a warning to stderr (which the Claude Code harness surfaces back to the model)." Cursor's `postToolUse` contract is explicit about what reaches the model, and it is a JSON field:

> `additional_context` | string (optional) | Extra context injected into the conversation after the tool result

Exit `0` means "Hook succeeded, use the JSON output." No documented stderr channel exists. So on Cursor the hook fires, matches, parses `state.md`, evaluates the globs correctly, exits 0 — and warns nobody. It does not error. It does not degrade visibly. It reports success while doing nothing, which is verbatim the failure mode ADR-0004 named *in this same component*: "A missing or relocated state file produces exactly the same observable behaviour as a correctly installed pack with no feature in flight: silence." Two independent host-level defects, one component, same signature.

Two smaller notes on the same hook. Its matcher `Edit|Write|NotebookEdit|MultiEdit` still matches, because Cursor maps `Edit` → `Write` and the regex alternation catches `Write` — but `NotebookEdit` and `MultiEdit` map to nothing, so three-quarters of that matcher is dead text on this host. And `EXCLUDED_PREFIXES` hardcodes `.claude/`, so on a `.cursor/`-shaped install the pack's own files stop being excluded from drift warnings.

**Three of these four losses are silent.** The pack has now been bitten by that class enough times to have named it twice — ADR-0008 clause 2 and ADR-0009 clause 4 — and the lesson both encode is that a second host needs a *guard*, not just an install path.

### A name collision the pack cannot ignore

Cursor ships built-in skills invoked the same way the pack's commands would be. `/plan` is taken — plan mode is a first-class Cursor feature with its own `/plan` invocation. So are `/review`, `/review-security`, `/review-bugbot`, `/babysit`, `/loop`, `/split-to-prs`, `/automate`, `/create-skill`. Two of those overlap the pack functionally rather than only nominally: `/review-security` against Gate 3, and `/babysit` ("monitors a pull request and addresses feedback, conflicts, failing checks") against `/pr-review` and `/feature-merge`'s closeout.

Cursor documents skill precedence neither across its eight skill roots nor against built-ins. And renaming is not a rename: `/plan` appears 63 times across `pack/`, `/checkpoint` 67, `/adopt` 36, `/build` 32. A prefix sweep is ~198 citation sites — the same shape as slice 12's "34 path-construction sites across 9 files," which the pack has already paid for once and which produced a dangling-path defect its own guard caught.

## Decision

Three shapes, in increasing cost. **Recommend the spike now, Shape B as the target, Shape C as the distribution layer once B exists.** Shape A is the honest floor if the spike says arguments carry.

### Shape A — compatibility install

Change nothing about the `.claude/` layout. Add to the installer: the setting-toggle instruction, and eight generated `.cursor/skills/<name>/SKILL.md` **shims** that delegate to the command file that already exists:

```markdown
---
name: feature-start
description: Begin a feature — brainstorm, spec, branch. Devkit workflow entry point.
disable-model-invocation: true
---

Read `.claude/commands/feature-start.md` in full and follow it exactly, treating
anything the user typed after `/feature-start` as its `## Arguments` section describes.
```

One copy of the orchestration prose, which matters: eight 165-line phase machines maintained twice is the divergence this project's principle 3 exists to forbid. Cost is a target flag and eight generated files. Buys a running pack with the three silent losses **documented rather than fixed**.

### Shape B — a second install target

`install.sh --host cursor` emits a `.cursor/`-shaped install: the four skills and eight command-skills under `.cursor/skills/`, `.cursor/agents/*.md` with `readonly:` replacing `tools:`, `.cursor/hooks.json` registering `postToolUse`, the hook rewritten to emit `{"additional_context": …}` on stdout, references under `.cursor/references/`, the state file relocated, `CLAUDE.md` retained (see the forks).

`install_lib.py` is where this is cheap: `TRACKED_DIRS`, `TRACKED_TOP_FILES`, and the single `f".claude/{pack_rel}"` mapping are the whole coupling surface, and the manifest/hash/plan logic is already host-agnostic. The expensive half is prose — 151 `.claude/` occurrences and 66 `.claude/state.md` sites.

**This makes ADR-0004 a prerequisite rather than a nice-to-have.** Its prose-indirection decision — "the pack docs stop naming a literal path and refer to *the state file (see …)*" — is the same sweep this shape needs, and doing them separately means sweeping 66 sites twice.

### Shape C — a Cursor Plugin

`.cursor-plugin/plugin.json` with folder-discovered `skills/`, `agents/`, `commands/`, `hooks/hooks.json`. Marketplace-distributable; Cursor owns installation and refresh.

**This is ADR-0007's disposition split handed a mechanism, and it is worth recording even if C is never built.** *owned* becomes the plugin — Cursor installs and refreshes it, so the manifest, SHA-256 customization detection, `--force`, `.devkit-bak/`, and the update-path advisories all become someone else's problem. *seeded* stays with a much smaller installer: the memory file and the state file, which a plugin has no mechanism to stamp. *discovered* is untouched. `MIGRATIONS.md` shrinks to exactly the seeded set — which is what ADR-0007 argued it was always actually for.

C is a distribution answer layered on B, not an alternative to it: it removes none of the four semantic losses, and it cannot seed.

## The spike, and why it comes first

Five behavioural predictions, per working principle 4. **Recorded here unrun.** All five are cheap — one Cursor session on an already-installed target — and they convert the load-bearing unknowns into facts before any authoring commits to a shape.

| # | Prediction |
|---|---|
| **P1** | With third-party configs enabled, a fresh Cursor session in a devkit-installed project lists `engineer`, `pm`, `documenter`, `grill-me` under Customize → Skills, and the four subagents as delegation targets. |
| **P2** | Typing `/feature-start` offers no such command — confirming the commands surface is the only missing one. |
| **P3** | A Shape-A shim invoked as `/feature-start "add a health endpoint"` carries the quoted argument through to the command's `## Arguments` handling. |
| **P4** | An edit outside the active spec's `owned_files` produces **no** visible drift warning. |
| **P5** | `/plan` resolves to Cursor's plan mode, not the pack's. |

**P3 and P5 decide the shape.** Cursor documents no argument mechanism for skills or commands — `$ARGUMENTS` appears in the docs only for prompt-based hooks — so P3 is a genuine unknown, and the pack's commands take arguments in prose from a user-typed string, which is the shape most likely to survive. If P3 fails, Shape A collapses and B becomes the floor. P4 is expected to *fail as stated* — it is written to confirm loss 3 rather than to hope against it, and if a warning does appear, the stderr channel is undocumented rather than absent and loss 3 is downgraded.

## The forks, open

Owner's call; none of these should be resolved by an authoring session.

**Rename or collide?** `/devkit-plan` and friends cost a ~198-site sweep and make every command name uglier at the exact moment the user is typing it. Colliding costs an undocumented resolution order on the pack's most-cited command. P5 informs this but does not settle it.

**`CLAUDE.md` or `AGENTS.md`?** Cursor documents `CLAUDE.md` as *always* applied to every conversation; root `AGENTS.md` only as "picked up automatically." The better-documented option is to keep the file the pack already stamps, change nothing, and ship a target project a file named for a tool it isn't using. `AGENTS.md` is the neutral name and the weaker guarantee. Note that `claude-md-elements.md`, `/claude-md-merge`, and 145 `CLAUDE.md` citations all ride on this fork.

**One pack, two hosts, or two packs?** Every future slice either authors host-neutrally or authors twice. Given that slices 9, 11, and 12 are all shipped-and-unvalidated, doubling the authoring surface is a real risk and the reason the build slice below is sequenced where it is.

## Alternatives considered

**Rewrite host-neutral from the start** — `AGENTS.md` plus `.agents/skills/`, which Cursor documents as a first-class root and which is the [Agent Skills](https://agentskills.io) open standard. Attractive, and rejected for now: nothing establishes that Claude Code reads `.agents/skills/`, so neutrality would have to be *validated on both hosts*, doubling validation debt on a pack whose largest single body of text has never executed.

**Cursor Automations for the branch loop.** Rejected as a different product. Automations are scheduled or event-triggered cloud runs; the pack's loop is interactive with a user gate per step, and the gates are the point.

**Defer Gate 3 to Cursor's `/review-security`.** Worth a fork later, not now. `security-reviewer`'s value is its fresh-context contract and its `security-categories.md` sweep; Cursor's built-in has its own contract, unread. Deciding this from the docs alone would be asserting the unverified — clause 5.

**Do nothing; the pack is a Claude Code pack.** The strongest alternative, and the reason this is Proposed rather than Accepted. The pack has three unvalidated slices and a `reviewer` component that ADR-0009 argues is a precondition for further by-construction work. A second host is scope growth against that backlog.

## Consequences

- **The pack acquires a host axis it has never had.** Every subsequent component authored must decide whether it is host-neutral or host-specific, and `install.sh`'s eight-step lifecycle validation becomes sixteen.
- **`tests/test_pack_references_resolve.py` becomes host-parameterized.** Its `CITATION` regex, `RUNTIME_TARGET_PREFIXES`, and classifier tests all encode `.claude/`; the invariant it enforces is host-agnostic but its implementation is not. `test_doc_drift_detector.py` needs the same treatment, and would need a new case asserting the warning reaches the model *through the host's documented channel* — the assertion that would have caught loss 3 by construction.
- **`test_clause_one.py` and `test_migrations_snapshot.py` survive nearly untouched**, which is a useful signal: the guards that test the pack's *own discipline* are portable, and the guards that test its *wiring* are not.
- **Slice 13 is unaffected and slightly better served.** Cursor's Task fan-out and `readonly: true` fit the `reviewer` subagent's multi-lens shape directly, and the docs list "you want an independent verification of work" as a subagent use case.
- **ADR-0004 moves from Proposed-and-deferred to a prerequisite** for Shape B.
- **The three silent losses become the port's acceptance criteria.** A Cursor install that cannot make the drift hook speak, cannot stop the tester executing, and cannot hold the conformance-reviewer to one tool is a *degraded* install, and it should say so out loud in its closing message rather than presenting as complete. That is the same "silence is not success" rule the pack applies to itself.

## Build slice

**Slice 14, sequenced after slice 13 — with the spike pulled forward to now.**

The spike is read-only, costs one session, and answers five questions that otherwise get guessed at during authoring; there is no reason to hold it. The port itself waits, for the reason ADR-0009 § *What three rounds say about sequencing slice 13* already establishes: the by-construction program has a syntactic ceiling, `reviewer` is the component that raises it, and a second host multiplies exactly the cross-step semantic surface that no current component reviews. Authoring a second wiring layer before that gate exists would add the pack's largest untested surface to date on top of three slices that are already shipped-and-unvalidated.

Full breakdown in `docs/design/inventory-and-build-order.md` § *Slice 14*.
