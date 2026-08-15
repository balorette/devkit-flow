---
description: Convert an approved spec into a typical-depth implementation plan with research-grounded conventions, per-step type signatures, and acceptance-criteria mapping. Loads the `pm` skill (plan-time behaviors — research, acceptance mapping) and the `engineer` skill (plan-time behaviors — step ordering, step shape, tester contract). Invokes the `architect` subagent when research surfaces a first-of-kind cross-cutting decision. Pauses for user review and approval; does not flip status itself.
---

Drive the `pm` and `engineer` skills from an approved spec to an approvable draft plan. One `/plan` invocation produces one draft plan; the user reviews and approves before `/build` runs.

## Arguments

`/plan` takes no arguments. It operates on the active feature named in `.claude/state.md`. If the user wants to plan a different feature, they switch state first (or use `/feature-start` for a new one).

## Preconditions

Before doing anything visible to the user:

1. Read `.claude/state.md`.
2. Verify all of the following — if any is false, **stop and report what is missing** (do not work around it):
   - `Active feature` is not `none`.
   - `Spec` points to an existing file.
   - The spec's front-matter contains `status: approved`. If the spec is `draft`, surface that and stop — the user reviews and approves the spec first.
   - `Plan` is `—` (no plan exists yet) **or** the plan file does not exist on disk. If a plan file exists already, surface that and stop — the user either deletes the existing draft (to re-plan from scratch) or uses `/checkpoint` to amend it (slice 4; for now, manual edits).
3. Working tree may have uncommitted changes; `/plan` writes a new file and does not change branches.

If preconditions pass, continue. State.md's `Phase` may be `spec-approved` (clean handoff from `/feature-start`) or something else (e.g., user manually transitioned); don't gate on Phase, gate on the spec's own `status` and the plan-not-yet-existing condition.

## Run

Load the `pm` skill (for plan-time behaviors: research, acceptance mapping, cross-cutting pattern check) and the `engineer` skill (for plan-time behaviors: step ordering, step shape, tester contract). Both skills' "Plan-time behaviors" sections are the source of truth for the discipline; this command sequences the phases and handles side-effects (file writes, state.md updates, ADR persistence).

Also load the `grill-me` skill. `/plan` is mostly automatic — research and decomposition don't require user dialogue when the spec is decisive. But when research surfaces a user-facing decision the spec didn't pin (library choice, framework idiom, a project-first the architect won't catch), apply the grilling discipline: codebase-explore before asking, walk parents before children, recommend an answer per question, reflect each answer back.

### Phase A — Orient

**Both discoveries run before the first read that consumes them**, and their results are recorded for the rest of this invocation. Phase C's architect invocation and the engineer skill's plan-time architect calls read the ADR record rather than re-discovering; Phase F writes the plan at the location the artifact record names; and the exemplar scans below read the artifact homes rather than the defaults.

1. **Read `CLAUDE.md`** (project conventions). Both discoveries below open it first regardless — a recorded artifact home or ADR-registry note is authoritative for its own question — so reading it here is not a duplicate pass.
2. **Resolve the artifact locations.** Run `.claude/references/artifact-locations.md` § *Resolve* in full — the whole chain, not § *Discover* alone — and record the spec, plan, and summary directories it settles on. This is what the exemplar scans below and Phase F's write both read. Running it after either of them would be the producer arriving behind its consumer, which is the shape clause 3 exists to forbid.

   **Expect the plans question here specifically, and do not skip it as automation friction.** § *Resolve* asks only when a directory exists and holds files the pack did not write, and `docs/plans/` is the likeliest place in this pack for that to be true: plans are not a new idea, so the name is commonly already taken, while `docs/specs/` on the same project is often free. That asymmetry is the reference's own motivating case. A user-facing decision the spec didn't pin is exactly what the `grill-me` discipline above is loaded for — recommend an answer, then let the user settle it.
3. **Discover the ADR registry.** Run `.claude/references/adr-registry.md` § *Discover* in full. Record the registry's location, its format, and its current high-water number — the number is a reported hint only, never an allocation source (see that reference's § *Never cache the number*; allocation always re-scans). Report what was found per that reference's § *Report what was found*.
4. **Record the ADR paths.** The actual file paths discovery found, or the explicit `"registry: none found"` when discovery finds nothing. This is the piece the architect contract in "Invoking the architect" below needs verbatim — a directory pattern is not a substitute for either.

Then read, in this order:

- The active spec (path from state.md).
- The **discovered specs directory** for one or two recent merged specs — gives shape context.
- The **discovered plans directory** for any merged plans on adjacent features — these are the best evidence of what a typical plan in *this* project looks like. Scan the homes step 2 returned, not `docs/specs/` and `docs/plans/` literally: on a project that keeps them elsewhere the defaults return nothing, and the precedent is lost silently.
- `docs/domains/<domain>.md` for each domain the spec touches.
- **Any relevant ADR, in full**, read from the paths step 4 recorded — one named in the spec's `related_adrs` front-matter, or one whose title is keyword-relevant to the spec.

If the spec's `owned_files` glob excludes a directory you'd expect the feature to touch, surface that as a likely spec gap — flag, don't silently widen scope.

**Writes:** the `CLAUDE.md` conventions entry recording the artifact locations, for any type § *Resolve* settled here that the record did not already name. Otherwise none — both results are held for this invocation and consumed by later phases.

`/plan` is usually the second command to run, so it usually finds the record `/feature-start` left — **and that record usually names specs and not plans.** § *Resolve* runs per artifact type and exits per artifact type: a settled `Specs:` entry does not settle plans, and does not stop the scan that reaches the plans question. Expect this phase to write on the run that first pins the plans directory, whether or not specs were pinned before it. Phase G derives its staging list from this declaration and carries the write on the runs that produce one.

### Phase B — Research (REQUIRED)

Per the pm skill's "Research phase (required, not optional)" section, produce three buckets of grounded evidence:

- **Repo conventions** — observed precedents with file:line citations. Read multiple existing modules in the affected directories; do not generalize from one file. Provenance rationale: `.claude/references/evidence-and-uncertainty.md` § *Facts*.
- **Project-firsts** — patterns this feature introduces for the first time, each justified with explicit reasoning. *These are the cross-cutting-pattern candidates.*
- **Framework constraints** — researched from framework internals (or current docs) where behavior matters. Cite the source.

This phase is the difference between a plan that drives correct code and one that drives stylistically detached code that has to be re-styled later. Do not shortcut it. If a relevant repo file doesn't exist yet (the feature is establishing a new directory), say so — that's evidence the area is a project-first, not a reason to skip research.

### Phase C — Cross-cutting pattern check

After research, audit the project-firsts you identified in Phase B against the pm skill's "When to invoke the architect" criteria (specifically the cross-cutting-pattern subsection — framework-exception translation, retry policy, transaction boundary, logging shape, validation cascade, authorization placement, pagination convention, and similar).

For each first-of-kind cross-cutting decision found, **invoke the `architect` subagent in fresh context** before drafting it into the plan. See "Invoking the architect" below for the invocation mechanic. Surface the architect's recommendation to the user; do not silently apply.

If the architect drafts an ADR, allocate and write it per `.claude/references/adr-registry.md` — § *Discover* to locate the registry, § *Allocate* to take the next number, § *Never cache the number* for why a recorded high-water mark is not it. `/plan` allocating from a mark `/feature-start` already consumed is exactly how two ADRs end up claiming one ID. Reference it in the plan's front-matter `related_adrs`.

This is the slice-2 forward-reference: the pm skill almost missed a cross-cutting pattern at spec time; the same risk applies even more sharply at plan time when decisions get baked into multiple steps.

**Writes:** any ADR the architect drafts, at its discovered path.

### Phase D — Step decomposition

Per the engineer skill's "Step ordering" and "Each step's required entries" sections, decompose the feature into steps. Each step must:

- End in a green test suite.
- Be independently revertable.
- Have Files (new/modified), authoritative type signatures for the tester, a test list, conventions-applied bullets, a one-line why-this-order, and SOLID/Clean Arch notes where relevant.
- Be flagged with a smoke-import note if the engineer skill's "Smoke-import prediction" criteria apply.

If the analysis predicts a Step 1 that can't reach red because of a prerequisite (broken legacy import in a chained `__init__.py`, missing package initializer, etc.), include a **Step 0 prerequisite** in the plan that fixes it before Step 1 runs. Don't ship a plan whose Step 1 fails the smoke-import check.

### Phase E — Acceptance mapping

Per the pm skill's "Acceptance mapping" section, enumerate every acceptance criterion from the spec into a checklist table. Map each criterion to the step(s) that satisfy it, or mark it as a deliberate omission with a one-line reason. No criterion may map to "—" without a reason.

If the mapping reveals a criterion that has no plausible step (because the spec is internally inconsistent, or the criterion implies a behavior the plan doesn't account for), surface it — the spec may need amendment.

### Phase F — Write plan + update state.md

Write the plan at the location `.claude/references/artifact-locations.md` § *Resolve* returned, named per its § *Name* (`YYYY-MM-DD-<slug>.md`), with:

```yaml
---
feature: <slug>
status: draft
spec: <the actual spec path, copied from state.md's Spec: field>
related_adrs: [<numbers including any drafted in Phase C>]
---
```

Sections in order:

1. **Approach** — TDD throughout; dependency order rationale; and **the per-step verify command**. Copy the project's **Blocking gates** list from `CLAUDE.md` conventions verbatim — concrete commands like `uv run pytest`, never abstract "we use pytest." If no list is recorded, state the commands you inferred and mark them as inferred.

   This is what the `engineer` skill's Verify substep 3 reads at every step. Recording the gate in the *Framework constraints* table below is **not** enough: on the first full run a diff-coverage gate was captured there, with its caveat and its exact reproduction command, and the build loop still never ran it. A constraint the loop does not read is a constraint the loop does not have.
2. **Conventions and constraints** — three subsections from Phase B (Repo conventions, Project-firsts, Framework constraints), each with its evidence table.
3. **Step order** — each step entry per the engineer skill's "Each step's required entries" list.
4. **Acceptance mapping** — the table from Phase E.
5. **Out-of-plan changes that may surface** — lint-rule additions, one-time migrations, anything you anticipate needing that's outside the spec's strict scope. Surface here; don't surprise the user during `/build`.

If the discovered directory doesn't exist, create it.

Update `.claude/state.md`:
- `Phase: plan-draft`
- `Plan: <the path just written>`
- `Next step: Step 1 — <step name>` (the heading of the first step, so `/build` has something to point at the moment the user approves the plan)

Leave `## Open questions` alone unless the research or architect invocation surfaced something to defer.

**Writes:** the plan at its discovered path · `.claude/state.md`.

### Phase F2 — Conformance review

Invoke the `conformance-reviewer` subagent in fresh context. Pass **only** two paths: the approved spec and the plan you just wrote. It has no tools to reach the codebase, deliberately.

It answers one question — does the plan contradict the spec? — which is not the question Phase E asked. Acceptance mapping checks that every criterion is *covered*; it cannot see a step that covers a criterion while violating it. A plan can map every criterion to a step and still return `200` where the spec says `409`, or expose through an update schema a state change the spec says must hard-block.

The reviewer returns findings at two severities:

- **Blocking** — a direct contradiction: a stated value, path, name, signature, or prohibition differs. **Resolve before the plan is approved.** Either revise the plan, or amend the spec via `/checkpoint` if the plan's version is the one that's right. Do not approve and fix later: the spec is the contract every later gate reads.
- **Advisory** — the spec is silent and the plan chose. Surface to the user; the plan can be approved with these outstanding.

Surface the full findings document either way, including a clean result. A conformance review that found nothing is information about the plan, not an empty formality.

**Record every advisory the user leaves outstanding as a `CONF` row in the findings ledger** (see the documenter skill's *The findings ledger*; its location is discovered, not assumed). Advisories do not block approval, which is exactly why they evaporate — the `/plan` conversation ends and the finding goes with it. The ledger defines `CONF` for this producer specifically so a deliberate deferral is still readable by the next `/feature-start`.

**An advisory you fix in the plan needs no row.** There are three dispositions, not two: fix it now, defer it to a `CONF` row, or resolve it with the user. **Prefer the first when the fix is cheap** — the ledger is for what you deliberately leave, and a ledger full of postponed two-minute edits stops reading as a record of real decisions.

The phase's own best case is the one that used to go unnamed. On the first full run all three advisories were cheap, all three were fixed in the plan, and no rows were written — which is the right outcome, and a literal reader of the previous text would have deferred them instead. A branch left unstated does not go unhandled; it gets handled inconsistently, by whoever is reading.

You wrote this plan. That is exactly why you are not the one checking it — the fresh-context reviewer has not spent the last hour making these choices sound reasonable.

**Writes:** the findings ledger, when an advisory is left outstanding as a `CONF` row.

### Phase F3 — Symbol verification

Phase F2 asked whether the plan contradicts the spec. This phase asks a different question: **do the things this plan names actually exist?**

The `engineer` skill states the plan's status plainly — *"The signatures are authoritative. If the signatures are wrong, the tester writes the wrong tests."* Nothing downstream can check that. `conformance-reviewer` has no codebase access by design; `tester` is forbidden implementation source; `engineer` finds out at red, after the tester has already spent its context on a contract that cannot compile. This phase is the only place the plan's claims meet the codebase.

**Enumerate every symbol the plan names**, from all three places they appear:

1. **Type signature blocks** — every type, parameter type, and return type.
2. **The conventions table** — every function, method, helper, and constant.
3. **Prose** — any identifier that names real code, including ones mentioned only in a step's narrative.

Scope by *what names code*, not by *what sits in a signature block*. The narrow version of this rule has already failed once: a mid-feature correction restricted to signature blocks let a wrong name through in the conventions table two steps later.

**Confirm each against the codebase — at its definition, not at any occurrence.** A bare text search is not sufficient and will pass names that do not exist. `Config`, `Result`, `get`, `Client`, and `Handler` all match something in almost any repository; a plan that meant `ReconciliationConfig` and wrote `Config` resolves cleanly against an unrelated class, an import line, a test fixture, or a comment, and the wrong signature reaches the tester anyway — which is the exact failure this phase exists to prevent.

For each symbol, establish **that this name is defined, and where**:

- Search for the *definition* form the language uses — `class X`/`def X`/`X =` in Python, `function X`/`const X`/`class X`/`export` in JS/TS, `func X`/`type X` in Go, and so on — not a bare occurrence of the identifier.
- Check it against **the module the plan says it lives in**. A symbol that exists somewhere else in the repo is not the symbol the plan named; that is a different defect wearing the same name, and it is the one most likely to survive review.
- Where the plan names a method, confirm it on the type it was attributed to. A method that exists on a sibling class is a `RESOLVED` that will fail at red.

**Symbols the project does not own are `EXTERNAL`, not failures.** A signature naming `str`, `UUID`, `datetime`, `AsyncSession`, or `BaseModel` is naming the standard library or a declared dependency, and there is no project definition to find. This phase asks whether the plan's names match *the code this project owns*; a name that resolves outside the project has been answered, not left open.

**`EXTERNAL` requires evidence, exactly like the other two states.** Cite where the name comes from — the import in the module the plan attributes it to, or the dependency in the project's manifest (`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`). *"It looks like a library type"* is not evidence and is reported `UNRESOLVED`. This matters more than it appears: `EXTERNAL` is the state a hurried reader will reach for to clear a halt, and an `EXTERNAL` that nobody had to justify turns this phase back into the bare text search it was written to replace.

An external name attributed to a *project* module stays `UNRESOLVED` — the module-mismatch rule above is unchanged, and "imported into that module" is not "defined by it" when the plan claims the latter.

Report:

```
RESOLVED    ReconciliationCaseLayout        src/layouts.py:41
EXTERNAL    UUID                            stdlib -- uuid, imported at src/recon/case.py:3
EXTERNAL    AsyncSession                    dep -- sqlalchemy, pyproject.toml:24
UNRESOLVED  CaseLayout                      -- nearest: ReconciliationCaseLayout
UNRESOLVED  build_manifest_conflict_detail  -- no match
UNRESOLVED  Config                          -- defined at src/app/config.py:8,
                                               not src/recon/ as the plan says
```

Where a name does not resolve, offer the nearest match if there is a plausible one. Most instances are a shortened or half-remembered form of a real symbol rather than an invention.

**Halt on any UNRESOLVED.** `RESOLVED` and `EXTERNAL` both pass. Do not carry an unresolved name into Phase G. Either correct the plan, or — if the symbol is genuinely new code this plan introduces — mark it explicitly in the plan as *introduced by this plan*, so the next reader can tell a deliberate new name from a wrong one. That distinction is the entire output of this phase.

**Three states, because two could not describe a real plan.** The first version of this phase offered only *correct the plan* or *mark it introduced*, and a Python signature naming `UUID` fits neither — so a literal reader had to halt on valid work or record a false provenance to escape. That version would have halted on the first step of essentially any plan written against a project with dependencies, which is every project. Found in execution on the first target that ran it, having survived five rounds of review of this file.

**Symbols the plan introduces are not failures.** A plan for new code names things that do not exist yet, and that is correct. What this phase catches is a name that was *meant* to match existing code and doesn't.

### Phase G — Commit and hand off

Before the pause, propose a single commit for **the union of every `**Writes:**` declaration the phases that ran produced** — read them off those phases. On a full run the phases carrying declarations are **A, C, F, and F2**; go read those four and stage what they name.

**That is a list of phases to read, deliberately, and not a list of files to stage.** This paragraph used to enumerate the artifacts, and it used to cite itself as the version that got it right while `/feature-start`'s equivalent got it wrong. Both were wrong within one slice: Phase A gained a conditional `CLAUDE.md` artifact-homes write and neither enumeration grew it. Being correct at the moment of writing is not a property a hand-maintained list keeps — which is the whole argument for deriving it, and the reason this one no longer names files.

Two of the four are easy to drop for opposite reasons. Phase A's write is **conditional per artifact type** — § *Resolve* records the types this run settled that the record did not already name — and the case most likely to be dropped is the one that looks least like it should produce a write: specs already recorded by `/feature-start`, plans settled here for the first time. Reading "a record already exists" as "nothing to write" is wrong on exactly the run that writes, and `/plan` is where that run normally happens. Phase F2's `CONF` row is **remote** — written to the findings ledger at its resolved path, not somewhere obvious in the diff. A `CONF` row written and not committed reaches no other clone and no PR, defeating its stated purpose of surfacing to the next `/feature-start`'s orient, which reads the ledger from the repo rather than from this conversation.

Subject: `plan: <slug> (draft, <N> steps)`. Body: one short paragraph — the plan's approach in one sentence, ADR numbers if any. Stage these files explicitly; never `git add -A` (same reasoning as the engineer skill's commit substep). Wait for confirmation; on decline, leave the proposal visible and proceed to the pause without committing. If Phase C produced architect-driven ADRs, the user may prefer per-ADR commits — surface that option in the decline branch.

Then pause for the user. Surface, in one short message:

- The plan path.
- Any ADRs written in Phase C.
- The commit status (committed / proposal-declined / nothing-to-commit-yet).
- A one-line prompt: "Review the plan; when ready, change its front-matter `status` from `draft` to `approved`, commit that change, and run `/build`."

Do not auto-approve the plan. The approval-status flip is the user's separate commit between `/plan` and `/build` — the precedent message is `approve plan: <slug>`. `/build` reads the plan's front-matter `status` directly, so the user only needs to edit the plan file — state.md's `Phase` is descriptive.

## Invoking the architect

When Phase C identifies a first-of-kind cross-cutting decision, invoke the `architect` subagent via the `Agent` tool. Use `subagent_type: architect` if the host project's pack install resolves it; otherwise fall back to `subagent_type: general-purpose` with the contents of `.claude/agents/architect.md` (or `pack/agents/architect.md` in the dev tree) pasted at the top of the prompt body. Either way the architect runs in fresh context, which is the integrity guarantee.

Pass the architect:

- The question framed in one sentence.
- The trade-offs you've already considered.
- Paths to: the active spec, the in-progress plan draft (if any sections are written), relevant `docs/domains/<domain>.md` files, relevant ADR files from the discovered registry (actual paths, never a directory pattern — or the explicit `"registry: none found"` signal if discovery found nothing).
- Pointers to source files the architect should sample.

The architect returns a recommendation, rationale, trade-offs, precedent, and (if warranted) an ADR draft. Reflect the recommendation back to the user before accepting; the user's confirmation is the gate before applying it to the plan or writing an ADR.

## Halt conditions

Stop and surface to the user (do not auto-recover) if:

- Preconditions fail (no active feature, spec not approved, plan already exists).
- Research surfaces evidence that the spec is internally inconsistent or names files/conventions that don't exist (suggests the spec needs amendment before `/plan` can proceed).
- The architect returns a recommendation that conflicts with what the spec commits to (the spec may need amendment via `/checkpoint`).
- Acceptance mapping leaves a spec criterion unable to map to any step or deliberate-omission (suggests the spec criterion is unimplementable as stated).
- The user rejects an architect recommendation but has no alternative direction — surface the disagreement, don't proceed with either option.
- The `conformance-reviewer` returns **blocking** findings that are not yet resolved. Hand off with the plan still `status: draft` and the contradictions named. A plan approved over a known contradiction makes the spec stop describing the system, silently, from that moment on.
- The proposed commit cannot be staged (e.g., a file Phase C/F expected isn't on disk, or `git add` errors out). Surface; do not work around it.

Plan generation is not a one-shot script; if any of these conditions surface, halting and asking is cheaper than producing a plan that has to be redone.
