# Skill Inventory & Build Order

**Purpose:** Name every component in the pack, describe what it reads/writes, and lay out a build order that makes the pack dogfood-able before it's complete.

---

## Inventory

### Subagents (4)

| Name | Trigger | Reads | Writes | Notes |
|---|---|---|---|---|
| `architect` | Invoked by PM skill during `/feature-start` brainstorm when design questions arise; by Engineer skill during `/build` when Clean Architecture boundary is ambiguous | Active spec, `docs/domains/`, `docs/adr/`, relevant source | Returns a recommendation + ADR draft to the calling context | Fresh context. Sees the question, not the implementation. Outputs are advisory; caller decides whether to accept |
| `tester` | Invoked by Engineer skill at the start of each `/build` step | Active spec, plan's test list for the current step, type signatures of code-under-test, **not** implementation source | Test files only | Fresh context is load-bearing here. Cannot see implementation while writing tests. This is the TDD integrity guarantee |
| `security-reviewer` | Invoked by `/feature-merge` as gate 3 | Diff of the feature branch vs main, active spec, `docs/adr/` | Review notes (structured findings + severity) to the calling context | Fresh context. No prior conversation about the implementation choices |
| `conformance-reviewer` | Invoked by `/plan` (Phase F2) before the plan is approved | Approved spec + draft plan **only** — no source; it has neither `Bash` nor `Glob` | Contradictions by severity (blocking / advisory) to the calling context | Fresh context. The plan's author is anchored on choices just made; a contradiction between contract and proposal is invisible to whoever introduced it. Catching it pre-approval costs a plan revision instead of a build |

### Skills (4)

| Name | Trigger | Reads | Writes | Notes |
|---|---|---|---|---|
| `engineer` | Loaded by `/build`; also by `/plan` for planning-time discipline | Active plan, current step, existing source for context | Source files, test files (after tester returns), commits | Encodes TDD red-green-refactor loop, SOLID checklist, Clean Architecture layering rules, Karpathy-style small reversible steps. The pack's largest skill by content volume |
| `documenter` | Loaded by `/checkpoint`, `/feature-merge`; on-demand when hook surfaces drift | All of `docs/`, `.claude/state.md`, current diff | Spec amendments, plan amendments, ADRs, summaries, domain doc updates, state.md | Always proposes before writing. Never auto-edits docs without user confirmation. Owns the doc-currency invariant in practice |
| `pm` | Loaded by `/feature-start` for brainstorm + decomposition; by `/plan` for plan generation | `docs/domains/`, `docs/specs/` (for shape consistency), user input | Spec drafts, plan drafts, state.md updates | Owns the brainstorm-to-spec dialogue pattern and the domain-decomposition heuristic. Invokes architect when design questions surface |
| `grill-me` | Auto-invoked by `/feature-start` (brainstorm) and `/plan` when user-facing decisions surface; on request ("grill me", "stress-test this") | The plan or design under discussion; the codebase, when a question can be answered by exploring instead of asking | Nothing — it interviews; the caller writes | No isolated context needed, so a skill rather than a subagent. Walks parents before children and reflects each answer back; silent inference is the failure mode it exists to prevent |

### Slash commands (6)

| Name | Purpose | Preconditions | Postconditions |
|---|---|---|---|
| `/feature-start <name>` | Begin a feature: brainstorm → domains → spec → branch | No active feature in state.md; clean working tree | Branch created, spec drafted (status: draft), state.md updated; ADR if architect was invoked |
| `/plan` | Convert approved spec into implementation plan | Active feature; spec status = approved | Plan drafted (status: draft), state.md updated |
| `/build` | Execute the approved plan under TDD | Active feature; plan status = approved | One or more plan steps completed; source/tests committed; state.md updated per step |
| `/checkpoint` | Mid-feature doc-sync and spec/plan amendment | Active feature in any phase | Documenter has reconciled docs against repo state; user-requested amendments applied; state.md updated |
| `/feature-merge` | Close out the feature: tests + docs + security → merge or open a PR → archive. Re-runnable | Active feature; plan complete; tests green. For closeout: `Phase: in-review` with a merged PR | Local flow: summary generated, domain docs updated, branch merged, state.md cleared. PR flow: summary generated, branch pushed, PR opened, `Phase: in-review` and `PR:` set, state.md **not** cleared until a later closeout run |
| `/pr-review [all]` | Intake, triage, and respond to PR review feedback | `Phase: in-review` with `PR:` set (or a PR discoverable for the branch); `gh` authenticated, else paste-in fallback | Accepted in-scope findings fixed with `review:` commits; out-of-scope findings routed to `/checkpoint` or followups; replies posted after user confirmation; summary *Review notes* amended; state.md Open questions updated |

### Hook (1)

| Name | Type | Fires on | Behavior |
|---|---|---|---|
| `doc-drift-detector` | `PostToolUse` | Edit / Write on files under `src/` (configurable) | Reads active feature from `.claude/state.md`. Checks edited file path against active spec's `owned_files` front-matter. If file is not in scope, surfaces a warning: "Edit touched `<path>`, which isn't listed in `<active-spec>.owned_files`. Either expand the spec's scope (`/checkpoint`) or move this change to a different feature." Does not block. Does not auto-edit |

### Memory layout (recap from ADR-0001)

| Path | Purpose | Lifecycle |
|---|---|---|
| `docs/specs/<feature>.md` | Spec — source of truth for *what* | Created at `/feature-start`; amended via `/checkpoint`; final state at merge |
| `docs/plans/<feature>.md` | Plan — source of truth for *how* | Created at `/plan`; amended via `/checkpoint`; final state at merge |
| `docs/adr/NNNN-<name>.md` | Architecture decision records | Created when architect subagent is invoked and produces a decision; immutable once accepted |
| `docs/domains/<domain>.md` | Living domain model | Updated by documenter at `/feature-merge` when feature changes the domain |
| `docs/summaries/<feature>.md` | Feature retrospective + change story | Created at `/feature-merge`; immutable after |
| `.claude/state.md` | Working state pointer | Continuously updated; cleared at `/feature-merge` |
| `CLAUDE.md` | Index pointing at state.md, domains/, active spec | Stable; updated rarely (when memory layout itself changes) |

---

## Component dependency graph

What depends on what (for build ordering):

```
                  ┌─────────────┐
                  │ memory      │  (just the directory structure +
                  │ layout      │   CLAUDE.md index — no code)
                  └──────┬──────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────────┐
   │ engineer │   │ pm skill │   │ documenter   │
   │ skill    │   │          │   │ skill        │
   └────┬─────┘   └────┬─────┘   └──────┬───────┘
        │              │                │
        ▼              ▼                │
   ┌──────────┐  ┌─────────────┐        │
   │ tester   │  │ architect   │        │
   │ subagent │  │ subagent    │        │
   └────┬─────┘  └─────┬───────┘        │
        │              │                │
        │              ▼                │
        │       ┌──────────────┐        │
        │       │ /feature-    │        │
        │       │ start        │        │
        │       └──────┬───────┘        │
        │              │                │
        │              ▼                │
        │       ┌──────────────┐        │
        │       │ /plan        │        │
        │       └──────┬───────┘        │
        │              │                │
        ▼              ▼                ▼
   ┌──────────────────────────────────────────┐
   │ /build           /checkpoint             │
   └────────────┬─────────────────────────────┘
                │
                ▼
        ┌───────────────┐
        │ security-     │
        │ reviewer      │
        └──────┬────────┘
               │
               ▼
        ┌───────────────┐
        │ /feature-     │
        │ merge         │
        └───────────────┘

        (orthogonal, can be added any time after /build exists)
        ┌──────────────────────┐
        │ doc-drift-detector   │
        │ hook                 │
        └──────────────────────┘
```

---

## Build order

Six slices. Each is independently usable on a real feature. Stop and dogfood after every slice — that's the whole point of the slicing.

### Slice 1 — Minimum viable TDD loop

**Build:**
- Memory layout (just the directories + a stub `CLAUDE.md` + an empty `state.md`)
- `engineer` skill (TDD loop, SOLID checklist, Clean Arch rules, Karpathy discipline)
- `tester` subagent definition
- `/build` command

**What you can do after this slice:**
Use a hand-written plan in `docs/plans/<feature>.md` and run `/build` against it. Get the TDD loop working end-to-end on real code. This validates the most novel engineering content (the engineer skill) before anything else is built around it.

**Dogfood task:** Pick a small real feature in an existing project. Hand-write a 5-line plan with a test list. Run `/build`. Verify: tester writes tests in fresh context; engineer skill enforces red-green-refactor; SOLID and Clean Arch rules surface where relevant.

**Why this is slice 1:** It's the smallest useful slice. Everything else is workflow scaffolding around this loop.

---

### Slice 2 — Spec/domain front-end

**Build:**
- `pm` skill (brainstorm pattern, domain decomposition, spec drafting)
- `architect` subagent definition
- `/feature-start` command

**What you can do after this slice:**
Begin features properly. Brainstorm → domains → spec → branch. Then hand off to `/build` using a plan you still write by hand.

**Dogfood task:** Start a new feature with `/feature-start`. Verify: PM dialogue is useful and not bureaucratic; architect gets invoked when warranted; spec produced is actually useful as a contract.

**Why slice 2:** Validates the spec-first front-end before you commit to automating the plan generation. If the PM skill's brainstorm pattern is wrong, you want to know now — before `/plan` is built on top of it.

---

### Slice 3 — Plan generation

**Build:**
- `/plan` command (extends `pm` and `engineer` skills with planning behaviors)

**What you can do after this slice:**
Full spec-to-build flow. `/feature-start` → review spec → `/plan` → review plan → `/build`. No docs maintenance yet; that's slice 4.

**Dogfood task:** Take a feature through `/feature-start` → `/plan` → `/build`. Verify: plan structure matches what you actually want to execute; test lists are useful; step ordering respects Clean Architecture layering.

**Why slice 3:** With slices 1 and 2 validated, this is mostly orchestration. If the plan output is wrong, the fix is in the PM/Engineer skills (already built), not in `/plan` itself.

---

### Slice 4 — Doc-currency workhorse

**Build:**
- `documenter` skill
- `/checkpoint` command

**What you can do after this slice:**
Mid-feature amendments. The pack now actively maintains doc currency at every transition, not just at merge.

**Dogfood task:** Mid-build, deliberately change scope. Run `/checkpoint`. Verify: documenter proposes amendments before writing; spec and plan stay coherent; state.md reflects the change.

**Why slice 4:** Doc currency is the system's hardest invariant. Build the workhorse before the automated guards. If the documenter skill is wrong, the hook in slice 5 amplifies the wrongness.

---

### Slice 5 — Drift detection automation

**Build:**
- `doc-drift-detector` hook
- Add `owned_files` front-matter convention to spec template
- Update `pm` skill to populate `owned_files` when drafting specs

**What you can do after this slice:**
Drift surfaces automatically. Edits outside spec scope produce warnings the user must address.

**Dogfood task:** Deliberately edit a file outside the active spec's scope. Verify: hook fires; warning is useful; resolution path (via `/checkpoint`) is smooth.

**Why slice 5:** Layer on top of slice 4. Hook without documenter is a warning system with no fix path. Documenter without hook works but relies on user remembering to checkpoint. Combined, they make stale docs structurally hard.

---

### Slice 6 — Closeout and gate

**Build:**
- `security-reviewer` subagent definition
- `/feature-merge` command (with three gates: tests, docs, security)

**What you can do after this slice:**
Full feature lifecycle from start to merge. The pack is complete.

**Dogfood task:** Take a feature through the complete lifecycle. Verify: all three gates fire in order; security review surfaces useful findings; summary doc is genuinely retrospective, not boilerplate; domain docs update where appropriate.

**Why slice 6 last:** Merge gating only makes sense once everything it's gating on exists. Building this before slice 4 would be premature — you'd be gating on doc reconciliation that has nowhere to run.

---

### Slice 7 — Brownfield adoption (post-core)

Added after the six-slice core. The lifecycle that consumes the durable memory must exist and be validated before a command that *bootstraps* that memory can be dogfooded — so this is a post-core slice, alongside the other housekeeping command (`/claude-md-merge`), not part of the original six.

**Build:**
- `/adopt` command (`pack/commands/adopt.md`) — surveys conventions, discovers/confirms the domain map, writes baseline `docs/domains/` docs, opt-in ADRs. Orchestrates `documenter` (workhorse), the `pm` domain heuristic run in reverse, and `architect` (ambiguous boundaries only). No new skill or subagent.
- `pm` skill research-phase edit — cite captured `CLAUDE.md` conventions instead of re-deriving.
- `install.sh` closing-message pointer to `/adopt` for existing projects.
- `devkit-orientation.md` Housekeeping-commands entry.

**What you can do after this slice:**
Install the pack into a mature project and reach the same "solid base" a greenfield project grows to — domain map, captured conventions, optional decision records — in one deliberate pass, before the first `/feature-start`.

**Dogfood task:** Run `/adopt` on a real second project (not Enterprise Agent). Verify: Phase A conventions carry `file:line` evidence; the proposed domain map is useful and correctable; domain docs are terse and accurate; no ADRs unless a decision is flagged; a subsequent `/feature-start` orients against the produced docs and `/plan` cites the captured conventions. Re-run and confirm idempotence (deltas, not duplicates). This run doubles as the standing "second-project install" validation.

**Why slice 7 last:** Adoption only pays off if the lifecycle that reads the base exists and is validated. Building it earlier would mean dogfooding a base with nothing to read it. Full rationale and the resolved design forks: `docs/design/0002-brownfield-adoption.md`.

---

### Slice 8 — PR lifecycle and findings triage (post-core)

The lifecycle ended at a local merge performed synchronously by the user. In a pull-request workflow `/feature-merge` ran its three gates and then hit a *designed halt condition* (`gh pr create` was listed as a reason to stop), handing off everything after that point — opening the PR, receiving review, responding, landing the merge, closing out state. This slice closes that gap and, in doing so, adds the consumer-side findings discipline the pack had never written down for *any* source.

**Build:**
- `pack/references/findings-triage.md` — the shared evaluation discipline. Internal (`tester`, `architect`, `security-reviewer`) and external (humans, review agents) sources fail in opposite directions, so the default posture differs. Five classification buckets; five devkit rules.
- `pack/commands/pr-review.md` — fetch across all three GitHub comment surfaces, triage, remediate, respond. Re-runnable; skips already-answered threads.
- `pack/commands/feature-merge.md` — flow detection, a Phase-branch table making the command re-runnable, the `gh pr create` path, phase-aware closeout, four new halt conditions.
- `pack/state.md.template` — `Phase: in-review`, a `PR:` field, Open questions doubling as the accepted-but-unfixed ledger.
- `pack/skills/documenter/SKILL.md` — *Review notes* summary section; *The summary as PR body* derivation.
- `pack/skills/engineer/SKILL.md` — cites `findings-triage.md` for tester findings and architect recommendations.
- `pack/CLAUDE.md.template`, `pack/devkit-orientation.md`, `README.md` — surface the new command and the merge-flow convention.
- **No installer change.** `TRACKED_DIRS` already covers `commands/` and `references/`; both new files install automatically (verified: dry-run 19 → 21).

**What you can do after this slice:**
Run a feature end to end in a PR-based team workflow without leaving the pack — gates run *before* the PR opens so human reviewers spend attention on what machines can't catch, review feedback is triaged against the spec rather than implemented reflexively, and the feature's state survives the days between opening the PR and someone else merging it.

**Dogfood task:** A real feature on a GitHub-remote project: `/feature-start` → `/plan` → `/build` → `/feature-merge` (PR path) → human or agent review → `/pr-review` → merge on GitHub → `/feature-merge` (closeout). Seed the review with one out-of-scope suggestion and one spec-contradicting suggestion so those buckets are exercised. Verify the PR body links the spec; `Phase: in-review` survives a session restart; all three comment surfaces are fetched; no reply posts without confirmation; re-running `/pr-review` skips answered threads; closeout detects the async merge and clears both `Phase` and `PR:`.

**Why slice 8 here:** it precedes the debugging/correctness work (slice 9) because the PR halt sits on the daily path, and because findings triage is required for external review regardless of whether an internal `reviewer` subagent exists. Full rationale and the four resolved forks: `docs/design/0003-pr-lifecycle-and-findings-triage.md`.

**Deferred to slice 9:** a `debugger` skill (the pack has no debugging discipline — `/build`'s halt conditions hand off to a process that doesn't exist) and a `reviewer` subagent as a pre-PR gate 4 covering the cross-step lens no current component owns. Both were scoped during the 0003 discussion; neither is required for the PR lifecycle to work.

---

### Slice 9 — Enterprise API findings (post-core)

The first brownfield install produced twelve findings before a single feature ran. Three phases, sequenced in **lifecycle order** rather than priority order: phase 1 unblocks *starting* a dogfood on a target shaped unlike devkit's own, phase 2 unblocks *finishing* the same run, phase 3 extends the design with what that project's review corpus proved was missing.

**Phase 1 — brownfield portability** ([ADR-0005](0005-brownfield-portability.md)). One principle, five fixes: **read flexibly, write conservatively.** Adaptation buys tolerance on input, never licence on output. `references/spec-and-plan-depth.md` and `references/claude-md-elements.md` extracted (the second makes the `/adopt` ↔ `/claude-md-merge` deadlock impossible by construction rather than patching both sides); ADR-registry discovery by token scan before allocation; machine-owned-region detection so devkit never writes inside another tool's sentinels; host CI-gate discovery. Plus `tests/test_pack_references_resolve.py`, which makes the install-completeness class non-recurring.

**Phase 2 — slice-8 defect fixes** ([ADR-0003 § Corrections](0003-pr-lifecycle-and-findings-triage.md)). Six defects found by slice 8's first external scrutiny, two of which contradicted decisions that ADR recorded as resolved: a gated-baseline SHA so reruns cannot skip the gates; closeout docs committed before integration and post-merge state written on mainline; the merge-base diff (five sites, not one); a reply marker that works on all three PR surfaces; push-verify-then-reply; and Gate 1 running the project's discovered gate set. Plus `pack/MIGRATIONS.md` — without it the new `state.md` field reaches no existing install.

**Phase 3 — findings ledger and plan conformance** ([ADR-0006](0006-findings-ledger-and-plan-conformance.md)). The `conformance-reviewer` subagent, running at `/plan` before approval on documents alone. Gate 2 gains the conformance question it never asked. Findings gain a durable home — as a *discovered* artifact, so devkit never becomes the fifth review system on a project that already has one. `debugger` folds into `engineer` rather than becoming a fifth skill.

**What you can do after this slice:** install into a mature codebase whose ADRs, conventions, plans, and review system are already somewhere devkit didn't choose, and run a feature end to end through a PR reviewed by other people — without the pack overwriting what it found, allocating over an existing registry, or skipping a gate on the commits that actually merge.

**Dogfood task:** see `docs/validation/slice-9.md`. Four behavioural predictions are recorded there **unrun**.

**Why slice 9 here:** it is entirely reactive. Every item traces to a defect a real install exposed — which is the build order working as intended: slices 1–8 were designed, slice 9 was discovered.

---

### Slice 11 — Step invariants (post-core)

A second automated-review round on the Enterprise API 0.10.0 upgrade — the same target as slice 9, now with two reviewers and the first real `/adopt` run behind it — drew eight pack findings (`docs/validation/pr139-pack-findings.md`, [example-corp/enterprise-api#139](https://github.com/example-corp/enterprise-api/pull/139)). Six are instances of three recurring shapes: a step that writes a durable artifact leaves the commit that carries it for something later to notice; a pack decision reads state the pack itself just wrote, so the write invalidates the read before the read ever runs; and discovery that executes after the consumer that needed it. Two of those three shapes had already been fixed once in this pack's history and recurred. [ADR-0008](0008-step-invariants.md) names them as three clauses — artifact and carrier in the same step, never infer "what changed" from your own writes, discovery before every consumer — so the pack is held to a rule instead of eight independent patches.

**Phase A — release guard** (Task 1; finding 1). `pack/templates/history/0.10.0/` snapshots the two seeded templates as 0.10.0 shipped them; `tests/test_migrations_snapshot.py` fails the suite the moment a live template diverges from its snapshot with no `MIGRATIONS.md` section for the shipping version. This is the guard [ADR-0007](0007-artifact-dispositions.md) `:128` proposed as a slice-10 mitigation, landed here instead — see below. A *Releasing the pack* section in this project's `CLAUDE.md` writes down the resulting cycle.

**Phase B — ADR registry** (Tasks 2–6; findings 2, 3). `pack/references/adr-registry.md` absorbs the discover/report/allocate/never-cache-the-number procedure previously restated across five components. `/feature-start` Phase A now discovers the registry before Phase B can invoke the `architect`, Phase E re-scans rather than trusting Phase A's recorded number, and the `:130` architect contract passes discovered paths instead of a `docs/adr/*.md` pattern. Five `pm` sites and `/plan`'s ADR sites cite the reference instead of hardcoding a path; three `architect.md` sites are reworded to receive the ADR paths its caller discovered rather than reading `docs/adr/` themselves; `/adopt`'s restated Phase E scan is deleted in favor of citing it.

**Phase C — transport and self-reference** (Tasks 7–10; findings 4–7). `/plan` Phase G stages the findings-ledger `CONF` row whenever Phase F2 wrote one. `/pr-review` Phase D gains a metadata commit — covering the ledger and doc amendments together — before it pushes. `/feature-merge`'s `Gated baseline` moves from the gate-time SHA (invalidated the moment committing it changes the tip) to the tip immediately before the `state.md`-only transition commit, and the discriminator becomes a content diff against the PR tip excluding that one file, replacing both SHA equality and local-vs-remote-tip comparison. `/pr-review all` now disables only the handled-original check; the devkit-marker exclusion that keeps the pack from re-triaging its own replies applies in every mode.

**Phase D — ownership, doc currency, and release** (Tasks 11–14; finding 8). `devkit-orientation.md`'s `.claude/`-is-pack-owned section, and the same over-claim at `MIGRATIONS.md:5`, are rescoped to the manifest's tracked set plus the two seeded exceptions — everything else under `.claude/` belongs to the host project. The commit-cadence table is corrected to name both `/pr-review` commit moments and the PR-open transition commit it had described as commit-free. This section and the `CLAUDE.md` status update land here; the slice closes with `VERSION` → 0.11.0, two migration entries (the 0.10.0 Open-questions prose that finding 1 caught missing, and the reworded `Gated baseline` field comment), and a re-cut `pack/templates/history/0.11.0/` baseline — Task 14.

**Slice 10 is unbuilt, and slice 11 does not depend on it.** [ADR-0007](0007-artifact-dispositions.md) — owned/seeded/discovered as declared dispositions, a `/devkit-reconcile` command, a disposition-aware manifest — remains designed but unplanned; the numbering is deliberate, not a gap. ADR-0007 `:128` already named a template/migration guard as a slice-10 mitigation for this exact risk; slice 11 lands that guard now because finding 1 is the risk materializing, not something worth waiting on slice 10 for. Entry ordering, per-version uniqueness, and disposition awareness stay slice 10's to build. Full split in ADR-0008's *Relationship to slice 10 / ADR-0007* section.

**What you can do after this slice:** a `/feature-merge` rerun on an open PR with nothing new to gate stops re-running tests, docs reconciliation, and a fresh-context security review; a seeded template can no longer change shape without its diff surfacing to whoever ships the release; the ADR registry has one copy of its discovery procedure instead of five that can drift apart.

**Dogfood task:** Task 13 recorded five behavioural predictions in `docs/validation/slice-11.md`, unrun until the dogfood runs. The one that matters most: open a PR on Enterprise API, change nothing, re-run `/feature-merge`, and confirm it runs no gates — the branch that has been unreachable since `Gated baseline` was introduced.

**Why slice 11 here:** entirely reactive, like slice 9 — every clause traces to a finding a second review round exposed, this time after the pack had already fixed the first round's brownfield defects. Findings 4, 5, and 7 are slice-8 control flow found by reading, not running; slice 11 ships unvalidated, exactly as slices 8 and 9 did.

---

### Slice 12 — Declared writes, discovered locations, verified authority (post-core)

**The first slice with behavioural evidence.** Two validation rounds landed against 0.11.0 within a day: `docs/validation/pr140-pack-findings.md` (seven findings, static review of the pack's *text*) and `docs/validation/flow-execution-0.11.0.md` (nine findings from the pack's **first end-to-end execution** — `/feature-start` → `/plan` → `/build` ×6 → `/checkpoint` ×6 → `/feature-merge`, shipping a real feature to a green PR on a brownfield target). Every prior validation doc in this directory carried the caveat *"no pack command has executed."* For the build lifecycle, that caveat is retired.

Both rounds reached the same diagnosis independently: **0.11.0 stated its clauses correctly and applied them as a patch list.** Eight of seventeen findings are instances of clauses ADR-0008 already names. [ADR-0009](0009-declared-writes-and-verified-authority.md) adds clause 4 (an artifact declared authoritative has a verification pass), adds clause 5 at the owner's direction (decide what is arguable; never assert what is unverified), and takes the by-construction fix ADR-0008 considered and deferred at *"the two staging lists at issue are three lines each"* — an estimate execution falsified by finding two more sites in two commands.

**Phase A — clause 4 and the gate list** (Tasks 1–3; flow-6, flow-7, both high). `/plan` gains **Phase F3**: enumerate every symbol the plan names — signature blocks, conventions table, prose — grep each, halt on unresolved. The plan is declared authoritative for what the tester writes and was the one durable artifact with no verification pass; five wrong symbols shipped in one six-step feature. `engineer`'s Verify substep 3 now runs the project's recorded **Blocking gates** list, the same rule `/feature-merge` Gate 1 already had — clause 3 names the gate list explicitly and had wired two of its three consumers.

**Phase B — clause 1 by construction** (Tasks 4–7; flow-1, pr140-3, pr140-unnumbered). `tests/test_clause_one.py` asserts that a phase describing a durable write declares it with a `**Writes:**` line, and that a document declaring writes has a carrier phase. Twenty declarations land across six commands; staging lists in `/feature-start` Phase H, `/feature-merge`'s gate-rerun row, and `/plan` Phase G become *derived* from those declarations rather than hand-maintained. `/claude-md-merge` states its clause-1 exception rather than leaving it implicit. `MIGRATIONS.md` entries become anchored, hunk-naming replacements — "replace paragraph X" deletes silently when the reader's paragraph grew a sentence.

**Phase C — clauses 3 and 5** (Tasks 8–13; flow-4, flow-5, flow-8, pr140-5/6/7). Two new references: `artifact-locations.md` (discover/confirm/record/name for specs, plans, summaries) and `evidence-and-uncertainty.md` (clause 5's one copy). Specs, plans, and summaries move to `YYYY-MM-DD-<slug>.md`, and **34 sites across 9 files** stop constructing paths — the date prefix is the forcing function, since a filename that cannot be rebuilt from a slug makes discovery load-bearing rather than merely recommended. `adr-registry.md` scans the location `CLAUDE.md` records; `architect.md` stops answering on silence; `engineer` links the ADRs it writes into `related_adrs`. Fifteen clause-5 citations replace fourteen restatements, including one sentence that appeared verbatim in three files.

**Phase D — `/feature-merge` `in-review` corrections** (Task 14; pr140-1, -2, -4). Merged-state detection moves ahead of the sync precondition, which a deleted head ref fails; the tip comparison becomes equality rather than "not ahead"; the untracked-file prompt applies to this path as it already did to the building path. **These three are authored by reading.** The `in-review` re-entry path remains the largest body of never-executed text in the pack.

**Phase E — corrections, doc currency, release** (Tasks 15–18; flow-2, flow-3, flow-9). The stale slice-2 architect fallback is deleted in favour of verify-before-reflect; `install.sh`'s restart guidance narrows to newly-added commands; `documenter` generalizes three-strikes from bugs to process defects. `VERSION` → **0.12.0**, with one seeded hunk and one anchored migration entry naming it.

**What you can do after this slice:** a plan cannot reach approval naming a symbol that does not exist; the build loop runs the gates the project actually blocks on, in the step that breaks them; the pack writes its artifacts where the project keeps them rather than where the pack assumed; and a new command that writes an artifact without naming its carrier fails the suite before it reaches a validation doc.

**Dogfood task:** predictions recorded in `docs/validation/slice-12.md`, unrun. The one that matters most is clause 4's — draft a plan naming a symbol that does not exist and confirm Phase F3 halts before the approval gate. Two carry over unresolved from slice 11: whether the content-diff discriminator runs *no* gates on an unchanged reopened PR, and whether the `PostToolUse` drift hook has a real gap or merely lost its output in a long session.

**Why slice 12 here:** the first slice whose evidence is behavioural rather than textual, and the first to close a clause *as a rule* rather than at the sites a review happened to name. Its own execution proved the point twice — slice 11's release guard caught a clause-1 violation in slice 12's plan, and `test_pack_references_resolve` caught a dangling path in slice 12's new reference file.

---

### Slice 13 — Debugging discipline and the pre-PR reviewer (scoped, not authored)

Two components scoped during the [ADR-0003](0003-pr-lifecycle-and-findings-triage.md) discussion and deliberately deferred. **Renumbered from "slice 9" in slice 12**, resolving a collision: `CLAUDE.md` used that number for both the built Enterprise-API-findings slice and this unbuilt pair, and the inventory listed only the former.

- **A `debugger` skill.** The pack has no debugging discipline at all, and `/build`'s halt conditions hand off to a process that does not exist.
- **A `reviewer` subagent** as a pre-PR gate 4, covering the cross-step lens no current component owns.

**Multi-agent fan-out belongs here, and only here.** The build loop is serialized on purpose — red → green → refactor, one user gate per step — and parallelism there fights both TDD ordering and the every-gate-pauses property the first full run confirmed. `reviewer` is the opposite case: it is *defined* by the lens no single component holds, which is what diverse-lens fan-out is for. The evidence is slice 12's own two high-severity findings — a plan's symbols going unverified and the build loop running the wrong gates were both **single-lens misses**, invisible to every existing reviewer for structural reasons rather than by oversight.

**Sequencing hardened by slice 12's three review rounds.** Every high-severity finding across those rounds landed in the cross-step semantic gap this component is defined by, and the pack's own guards were green through all of them. Rounds 1, 2, and 3 each found the *previous round's correction* carrying a defect of the same family — the last of which was introduced by a change that read as a simplification. See [ADR-0009](0009-declared-writes-and-verified-authority.md) § *What three rounds say about sequencing slice 13*. The by-construction program has a syntactic ceiling and slice 12 found it, so `reviewer` reads as a **precondition** for further by-construction work rather than a component scheduled after it.

#### Candidate: drop the ADR high-water mark from `CLAUDE.md`

Surfaced 2026-08-13 while auditing the pack's `CLAUDE.md` footprint on target projects. Not a defect — a standing cost with no corresponding benefit, which is why it belongs in a slice rather than a fix commit.

`adr-registry.md` § *Never cache the number* states the contract in bold: **"The location may be recorded. The number may not be trusted."** Every allocator must re-scan the registry regardless of what the record says, because two commands reading the same recorded mark allocate the same ID. So the pack writes a value into the one file loaded into every session's context and then forbids every consumer from acting on it.

What that costs, none of which buys anything:

- **Context on every turn**, in a file whose whole design constraint is that it is always loaded.
- **A maintenance step** — `/feature-start` Phase E step 4 exists solely to stop the recorded mark decaying, plus its `**Writes:**` declaration and its place in Phase H's derived staging list.
- **A dirty `CLAUDE.md` during feature work.** It is the only thing that makes the pack touch a target's conventions file mid-feature; everything else written there is settled once.
- **A layering inconsistency.** The pack's memory split is `docs/` human-first and durable, `.claude/state.md` machine-first and current. A mutating integer only a machine reads is `state.md`-shaped. The registry's *location* is genuinely conventions-shaped — a settled decision a human should see — and stays.

**The proposal is removal, not relocation.** If allocation always re-scans, the hint produces nothing the scan does not already produce; moving it to `state.md` would preserve the maintenance burden while merely relocating the storage. Removal deletes step 4, one `**Writes:**` declaration, one staging-list entry, and the pack's only mid-feature `CLAUDE.md` write.

**It is a contract change, so it wants an ADR, not a patch.** ADR-0006 established the registry's shape and `/adopt` records the mark today; `pack/MIGRATIONS.md` would need an entry telling existing installs the line is now inert. Deliberately kept out of PR #4, which was already three review rounds deep on unrelated work.

---

### Slice 14 — Cursor as a second host (scoped, not authored)

Asked 2026-08-13: what would it take to run the pack on Cursor projects. Scoped in [ADR-0010](0010-cursor-as-a-second-host.md), which is **Proposed, not Accepted** — the sequencing argument below is part of why.

**The scoping finding inverts the expected shape of the work.** Cursor loads `.claude/skills/`, `.claude/agents/`, and `.claude/settings.json` hooks for compatibility, and reads `CLAUDE.md` as always-applied context. The pack's references and state file need no host mechanism at all — they are files cited by path. So four of five installed surfaces already work behind one settings toggle, and the port is **one missing surface plus four semantic losses**, not a rewrite.

- **The missing surface** is `.claude/commands/` — eight commands, ~1,320 lines, the entire orchestration layer. Cursor's documented equivalent is a skill with `disable-model-invocation: true`.
- **The losses** come from Cursor having no subagent `tools:` allowlist, only a `readonly` boolean. `architect` is fine and `security-reviewer` probably is; `conformance-reviewer` is degraded; **`tester`'s "runs nothing" is inexpressible** — that guarantee is the absence of `Bash` from its allowlist, and TDD integrity rests on it. Separately, the drift hook warns on **stderr**, which Cursor does not document as a channel to the model, so it would run, exit 0, and warn nobody.

**Three of the four losses are silent** — the class ADR-0008 clause 2 and ADR-0009 clause 4 each name, here reappearing at the host boundary. And one of them lands in `doc-drift-detector.py`, the same component ADR-0004 caught failing silently for an unrelated reason.

**Three shapes, costed in the ADR:** (A) keep `.claude/`, generate eight `.cursor/skills/` shims that delegate to the existing command files — one copy of the prose, smallest possible change; (B) a real second install target, `install.sh --host cursor`, which makes [ADR-0004](0004-configurable-state-path.md)'s prose-indirection sweep a prerequisite rather than a nice-to-have; (C) a Cursor Plugin, which is **[ADR-0007](0007-artifact-dispositions.md)'s disposition split handed a mechanism** — owned files become Cursor's to install and refresh, seeded files stay with a much smaller installer, and `MIGRATIONS.md` shrinks to exactly the set ADR-0007 argued it was always for.

**Also blocking: `/plan` is a Cursor built-in.** So are `/review`, `/review-security`, `/babysit`, and `/loop`, and the last three overlap the pack's gates functionally. Precedence against built-ins is undocumented, and a prefix rename is ~198 citation sites (`/plan` 63, `/checkpoint` 67, `/adopt` 36, `/build` 32) — slice 12's path-sweep shape, again.

**Dogfood task — the spike, and it is not deferred.** Five behavioural predictions are recorded in the ADR, unrun. They cost one Cursor session on an already-installed target and they settle the shape: **P3** (does a shim carry `/feature-start "…"`'s quoted argument, given that Cursor documents no argument mechanism for skills) and **P5** (does `/plan` reach the pack or plan mode). P4 is written to *confirm* the mute drift hook rather than hope against it.

**Why slice 14 here:** the spike happens now; the port waits for slice 13. A second wiring layer is the largest untested surface the pack could add, and it multiplies precisely the cross-step semantic gap that ADR-0009 § *What three rounds say about sequencing slice 13* argues no current component reviews — on top of slices 9, 11, and 12, all shipped and unvalidated.

---

## Build order rationale

A different order was tempting: **start with `/feature-start`** because it's where the user enters the workflow. Rejected for two reasons:

1. **The engineer skill is the most content-dense and least obviously right.** TDD discipline, SOLID, Clean Architecture, Karpathy-style — these are opinionated and need real validation. Get them wrong and everything downstream is built on sand. Putting this in slice 1 means it gets validated against real code earliest.

2. **`/build` is usable with a hand-written plan.** `/feature-start` is *not* usable without something to feed into. So slice 1 = `/build` produces a working tool from day one; slice 1 = `/feature-start` produces a tool that just sits there until slice 3.

The general principle: **build innermost first, then expand outward.** Engineer skill is the core; everything else is scaffolding that brings work to it.

---

## What "done" looks like

After all six slices:

- A feature can be started, scoped, planned, built, amended, reviewed, and merged through five commands
- Three subagents enforce isolation where it matters (TDD integrity, design objectivity, security fresh-eyes)
- Three skills carry the engineering, PM, and doc-currency discipline
- One hook makes drift visible in real time
- Five durable artifact types (spec, plan, ADR, summary, domain doc) carry project memory
- `.claude/state.md` is the working pointer that ties everything together
- The pack uses Claude Code native primitives throughout — no parallel framework

---

## Next concrete step

Pick a real project for the dogfood. Don't start writing skill content yet — start by defining what feature you'll run through slice 1 once it exists. The skill content will be much sharper if it's authored against a concrete validation case rather than in the abstract.

Suggested format for that pick:

```
Dogfood project: <name>
Slice 1 validation feature: <small real feature, ideally one you've been
putting off because it's boring>
Why this feature: <small enough to fit, real enough to surface problems>
```

Once that's locked, slice 1 authoring begins.