# ADR-0009: Declared Writes, Discovered Locations, and Verified Authority

**Status:** Accepted
**Date:** 2026-08-12
**Deciders:** [user], Claude (design partner)
**Evidence:** [`docs/validation/flow-execution-0.11.0.md`](../validation/flow-execution-0.11.0.md) findings 1–9 (the pack's first end-to-end execution) and [`docs/validation/pr140-pack-findings.md`](../validation/pr140-pack-findings.md) findings 1–7 plus its unnumbered `MIGRATIONS.md` finding. Every quotation re-verified against `pack/` source before this ADR was written.
**Extends:** [ADR-0008](0008-step-invariants.md) — cited throughout, not amended.

---

## Context

Two validation rounds landed against 0.11.0 within a day of each other, and they are different in kind. `pr140-pack-findings.md` is static review of the pack's *text*. `flow-execution-0.11.0.md` is the first time any pack command has **run**: `/feature-start` → `/plan` → `/build` ×6 → `/checkpoint` ×6 → `/feature-merge`, end to end on a real brownfield project, shipping a real feature to a green PR.

That distinction matters for how the findings are weighted. Every prior validation doc in this repo carries the caveat *"still not a dogfood — no pack command has executed."* For the build lifecycle, that caveat is now retired, and the findings below were observed rather than reasoned.

Sixteen findings plus one unnumbered. They sort into four buckets:

| Bucket | Findings |
|---|---|
| Clause 1 stated, not applied | flow-1, pr140-3, pr140-unnumbered |
| Clause 3 stated, not applied | flow-4, flow-7, pr140-5, pr140-6, pr140-7 |
| No existing clause covers it | flow-6 |
| Independent corrections | flow-2, flow-3, flow-5, flow-8, flow-9, pr140-1, pr140-2, pr140-4 |

### The theme both reviews reached independently

Eight of seventeen are instances of clauses ADR-0008 already states. Neither review was looking for that; both concluded it separately, in near-identical words. `pr140` § *The theme worth naming first*:

> Clause 1 was applied to the sites the #139 review named, not swept across the pack. That's the actionable process point: the clause needs a sweep, not a patch list.

and the flow doc's structural theme, from execution rather than reading:

> Four independent findings now recommend the same remedy — sweep the rule across the pack rather than patching the sites a review happened to name.

**0.11.0 did not fail to state its rules. It stated them correctly and applied them as a patch list.**

### Two facts that sharpen the diagnosis

**ADR-0008 already proposed the by-construction fix, and deferred it on a cost estimate execution has now falsified.** From its *Alternatives considered*:

> **Derive `/plan` and `/pr-review` staging lists mechanically** from the artifacts each phase declares it writes, rather than restating paths. Genuinely closes clause 1 by construction instead of by discipline. Deferred: it needs a per-phase artifact declaration the pack does not have, and **the two staging lists at issue are three lines each.**

Two commands' worth of execution found two more sites — `/feature-start` Phase H (flow-1) and `/feature-merge`'s gate-rerun row (pr140-3). "Two staging lists" was the wrong count, and it was wrong in the direction that matters: the deferral assumed the population was known and bounded. It was neither.

**Clause 3 already names the value flow-7 is about, and the mechanism to serve it already exists.** Clause 3's text:

> Where a value must be discovered rather than assumed — the ADR registry, the findings ledger, **the project's blocking-gate list** — discovery runs before the first consumer.

`/adopt:43-47` discovers the gate list and records it verbatim with `file:line` evidence. `/feature-merge:85` consumes it correctly, with an explicit *"when a recorded gate list exists, it is the whole of Gate 1"* rule and an inference fallback that announces itself. `engineer`'s Verify substep 3 — the per-step consumer, the one that runs six times per feature — hardcodes *"the linter and type-checker."* One clause, three consumers, two wired.

The cost of the half-wiring is in the flow doc: the project's fourth gate (`diff-cover --fail-under=85`) was never run during the build loop, surfaced at 80% after step 6, and needed six new tests written against code from several different steps. The plan's *Framework constraints* table **had recorded the gate**, with its caveat and its exact reproduction command. The knowledge was captured correctly and never reached the loop that needed it.

### The shape no clause covers

Finding 6 is new, and it is the pack's most reliable defect generator to date: five wrong symbols across one six-step feature.

`/plan` writes type-signature blocks; the `engineer` skill states their status plainly — *"The signatures are authoritative. If the signatures are wrong, the tester writes the wrong tests."* Trace who could have caught the error:

- **`conformance-reviewer`** deliberately has no codebase access. It verifies plan-against-spec, so it confirms consistency between two documents that are both confidently wrong about the code. That is by design, and the design is right — but it means conformance is not a truth check.
- **`tester`** is explicitly forbidden implementation source. It writes tests against whatever the plan declares.
- **`engineer`** discovers the error at red — the last possible moment, after the tester has spent its context on a contract that cannot compile.

**The artifact with the most downstream authority is the one artifact with no verification pass.** Specs get conformance review; code gets tests and the project's gates; the diff gets security review. Plans get approval from a user who cannot reasonably grep every symbol.

The partial fix that failed is itself evidence for the theme. A rule was recorded mid-feature after the third instance — *"every type named in a signature block must be grep-confirmed"* — and instance five landed in the **conventions table**, which is neither a type nor a signature block. The rule was written for the instances seen rather than the class, which is the same failure at feature scale that 0.11.0 committed at pack scale.

## Decision

One new clause, and the by-construction application of two existing ones.

### Clause 4 — An artifact declared authoritative has a verification pass

Where one pack component instructs another to treat an artifact as authoritative, **some step verifies that artifact's claims against the thing it describes, before the consumer that structurally cannot check them runs.**

| Artifact | Declared authoritative for | Verification pass |
|---|---|---|
| Spec | the contract | `conformance-reviewer` |
| Code | behavior | tests + the project's recorded gates |
| The diff | security posture | `security-reviewer` |
| **Plan type signatures** | **what the tester writes** | **none — this ADR adds it** |

**What it forbids:** an artifact whose correctness is asserted by its author and consumed by an agent structurally unable to check it.

**Corollary — the verifier must hold access the consumer lacks.** This is what makes the clause non-trivial. `conformance-reviewer` cannot host the plan's verification pass without codebase access, and granting it that destroys the isolation that makes its judgment worth having; `tester` cannot host it without implementation source, which destroys the TDD integrity guarantee. Where no existing verifier has the required access, the pass belongs to the component that already holds both sides — for plan signatures, `/plan` itself, which has the plan and the codebase in one context.

**What it does not require.** A verification pass is not necessarily a subagent, a hook, or a test. It is a *step that can fail*. The cheapest form that can fail is the correct one.

### Clause 1, applied by construction — declared writes

Every phase that produces a durable artifact names it in a `**Writes:**` line, in that phase. Every commit step stages **the union of the invocation's `Writes:` lines**, rather than a hand-maintained enumeration held at a distance from the writes it covers.

```markdown
### Phase E — Allocate and write ADRs
...
**Writes:** the ADR at its discovered path · the `CLAUDE.md` high-water mark
```

`tests/test_clause_one.py` enforces both halves: every phase heading containing a write verb has a `Writes:` line, and every command with `Writes:` lines has a staging step covering their union.

**Why the declaration is local rather than centralized.** A carrier table in `pack/references/` was considered and rejected against clause 1's own wording — *"A staging list maintained by hand **at a distance from** the writes it covers is the failure mode."* A reference file is definitionally at a distance; it reproduces the defect one level up, in the same way that recording an ADR high-water mark and then trusting it reproduces the discovery defect one level up. Locality is the mechanism here, not tidiness. This is the one place where clause 3's *"a procedure with more than one consumer lives in `pack/references/`"* corollary does **not** apply, because what is shared here is a discipline, not a procedure.

### Clause 3, swept — discovery reaches every consumer

Five consumers, unwired:

1. **The gate list reaches `engineer`.** Verify substep 3 gets the rule `/feature-merge` Gate 1 already has: run the recorded **Blocking gates** list if one exists; only when none exists, infer from project config — and say that you are inferring. `/plan` emits the recorded gate list as a concrete per-step verify command in the plan's *Approach* section, so the loop reads it rather than re-deriving it.
2. **Spec, plan, and summary locations become discovered.** New `pack/references/artifact-locations.md`, generalizing `adr-registry.md` from one artifact type to four: discover, confirm with the user when the namespace is occupied, record in `CLAUDE.md` conventions, cite. The ~20 sites that today construct `docs/specs/<slug>.md` and `docs/plans/<slug>.md` become citations.
3. **`adr-registry.md`'s scan reaches the location it records.** Scan the recorded location *in addition to* `*.md` under `docs/` plus root — a registry at `architecture/decisions/` is currently invisible to the scan even when `CLAUDE.md` names it exactly.
4. **Build-time ADRs reach `related_adrs`.** `engineer` links the ADR it writes, as `pm` and `/feature-start` already do; otherwise `security-reviewer`, which reads that field, cannot see the decision that authorized the architecture it is reviewing.
5. **`architect` stops answering without discovery.** See below.

### Silence is not an input

`architect.md` currently gives two instructions for the same condition. At `:22`, being passed no ADR paths and no explicit "none found" is *"a caller bug. Name it in your response … **and still answer the question.**"* At `:25`, four lines later, *"If **any of the above** is missing or unclear, **ask the caller a clarifying question instead of guessing**."*

The file argues against itself inside a single sentence: `:22` closes with *"guessing is how a second registry gets created"* — and answering without the registry **is** guessing about precedent. The resolution:

- **An explicit "none found" is a complete input — proceed on it.** This is already correct at `:20` and is unchanged. A project can genuinely have no ADRs; that is a fact about the project.
- **Silence is not an input — ask.** The "still answer" branch is deleted, not scoped. `:25`'s rule stands as the general case, and the contradiction disappears because `:22` no longer carves an exception out of it.

The rejected rationale for "still answer" was that a caller bug should not deadlock the workflow. It does not: a subagent's clarifying question returns to the main thread, which supplies the input or asks the user. One round-trip, which `:25` already prices as cheap. The branch also silently devalues an investment the pack has already made — commits `297cfea` and `2bf6638` exist specifically to make every architect call site pass an explicit none-found registry, and a subagent that proceeds on silence makes that discipline optional at the receiving end.

**This is a clause-3 finding, not a wording nit.** A consumer that answers despite discovery demonstrably not having run is a consumer running before discovery.

### Date-prefixed filenames as the forcing function for clause 3

Specs, plans, and summaries are written to `docs/{specs,plans,summaries}/YYYY-MM-DD-<slug>.md`. The date is the creation date and is stable across amendments; the directory carries the type, so no type suffix is added.

**This is in the ADR rather than filed as a naming preference because it is the mechanism, not the decoration.** The clause-3 sweep for artifact locations is otherwise pure discipline: twenty sites that currently derive a path from a slug would be rewritten to discover it, and nothing would stop the twenty-first from deriving it again. A filename that cannot be reconstructed from a slug makes discovery *load-bearing* — a component that skips it produces a path that does not resolve, which `tests/test_pack_references_resolve.py` already fails on.

Domains are excluded: `docs/domains/<domain>.md` is a per-domain living document amended at every merge, and a creation date on it would assert something false. ADRs are excluded: they carry a monotonic ID and `adr-registry.md` already owns their discovery, so a date would compete with the registry.

## What the clauses decide

| # | Finding | Sev | Clause | Fix |
|---|---|---|---|---|
| flow-6 | Plan signatures authoritative, unverified | high | **4** | `/plan` Phase F3: enumerate every symbol the plan names, grep each, halt on unresolved |
| flow-7 | `/build` verify omits the project's real gates | high | 3 | `engineer` substep 3 reads the recorded gate list; `/plan` emits it per step |
| flow-1 | Phase H staging omits the Phase E `CLAUDE.md` write | med | 1 | `Writes:` declaration; staging derives from it |
| flow-4 | `/plan` precondition vs an occupied namespace | med | 3 | `artifact-locations.md` + date prefixes |
| pr140-3 | Gate-rerun row commits `state.md` only | high | 1 | `Writes:` declaration; staging derives from it |
| pr140-5 | `adr-registry` cannot re-read its recorded location | med | 3 | Scan scope includes the recorded location |
| pr140-6 | `architect` missing-input contradiction | med | 3 | Silence is not an input — ask |
| pr140-7 | Build-time ADRs never linked from spec or plan | med | 3 | `engineer` amends `related_adrs` |
| pr140-un | `MIGRATIONS.md` paragraph replacement silently deletes | — | 1 | Entries become anchored sentence-level replacements naming their template hunk |
| pr140-2 | Merged-state check ordered after a failing precondition | high | none | Reorder: detect `state,mergedAt` first |
| pr140-4 | `in-review` precondition ignores untracked files | high | none | Apply the existing building-phase prompt to `in-review` |
| pr140-1 | `in-review` sync check is one-directional | med | none | Require tip **equality**, not "not ahead" |
| flow-8 | Tester findings framed as an error path | med | none | Rewrite as expected dual output + triage guidance |
| flow-2 | Stale slice-2 simulation note | low | none | Delete; add verify-before-reflect for architect source claims |
| flow-3 | `install.sh` restart guidance over-warns | low | none | Narrow to newly-added commands and skills |
| flow-5 | Phase F2 has no branch for "the advisory was fixed" | low | none | Name the third disposition; prefer cheap fixes to ledger rows |
| flow-9 | Three-strikes not generalized to process defects | low | none | `documenter`: third correction of a class amends the rule, not the instance |

**Eight findings are deliberately not given a clause.** Three — pr140-1, -2, and -4 — are ordinary correctness defects in preconditions: a directional comparison, a mis-ordered check, a scope that says "tracked" where it means "all." Inventing an invariant for each would be the over-correction ADR-0008 warned about when it declined to give its own finding #8 a clause. The other five — flow-2, -3, -5, -8, and -9 — are documentation-accuracy corrections. A rule for every finding is how a rule set stops being read.

## The forks, resolved

**Decision 1 — a new ADR, not an amendment to 0008.** ADR-0008 is `Built` and carries its own dated evidence from PR #139. Folding clause 4 and a reversed deferral into it would make one document assert two decisions made a week apart against different evidence, and would erase the fact that the by-construction fix was *considered, priced, deferred, and then justified by execution*. That sequence is the most useful thing this ADR records.

**Decision 2 — clause 4's verification pass is a `/plan` phase, not a hook.** Finding 6 proposes a hook (*"mechanical enough to be a hook rather than model work"*), and it was rejected on two grounds. First, extraction needs judgment: instance five was in the conventions table, so "what names code" is a semantic question a regex answers wrongly in both directions, and a false-positive warning channel is one users learn to skip — the same dynamic flow-3 identifies in the restart guidance. Second, the pack's one existing hook has an **open, unexplained miss** in this very validation round: Gate 2 caught drift on two files the `PostToolUse` hook did not surface. Adding a second hook to a mechanism with an outstanding reliability question is the wrong order of operations. The split adopted instead gives extraction to the model and confirmation to a shell grep, so the failing step is deterministic even though the enumeration is not.

**Decision 3 — declared writes are local; the carrier is not centralized.** Rejected alternatives: a `pack/references/artifact-carriers.md` table (violates clause 1's own locality rationale, above), and a runtime pending-artifacts list accumulated in `.claude/state.md` (makes the working pointer a transaction log, collides with slice 10's disposition work, and adds a failure mode where an interrupted session leaves a half-drained list).

**Decision 4 — date prefixes ship with the sweep, not separately.** Sequencing them apart would mean rewriting twenty citation sites twice.

**Decision 5 — the `/feature-merge` `in-review` quartet ships textually now.** pr140-1, -2, and -4 sit on a path that has never executed, and both validation docs correctly say the highest-value move for that path is behavioral. They ship anyway because **pr140-2 is severity-high and blocks closeout on any forge that auto-deletes head branches** — which is the very path slice 12's own dogfood must traverse. Leaving it unfixed means the run that validates this slice halts on a known defect. The ADR records plainly that these three are fixes authored by reading, and that the behavioral run still owes an answer on all four.

## Alternatives considered

**Fix findings 6 and 7 only, defer the sweeps.** Both are high severity, both are mechanical, and both would have paid for themselves inside the single feature that found them. Rejected because the sweeps are the diagnosis *both* reviews reached independently, and a second consecutive release that patches named sites would be the third instance of the pattern this ADR exists to close.

**Sweep without the enforcing test.** Cheaper by a file. Rejected on the empirical record: 0.11.0 *was* a sweep without a test, and both reviews concluded it decayed into a patch list. `CLAUDE.md` already describes `test_pack_references_resolve.py` as *"an enforced invariant, not a convention"* — the distinction is the project's own, and this is the second place it applies.

**Give `conformance-reviewer` codebase access and let it check symbols.** One fewer step, and the plan already gets a fresh-context review. Rejected per clause 4's corollary: the flow doc calls its lack of codebase access *"by design and the design is right,"* and a reviewer that reads source begins reviewing the code instead of the contract.

**A fifth subagent dedicated to symbol truth.** Preserves every existing isolation boundary and gets genuinely fresh eyes. Deferred rather than rejected — it is the right shape if Phase F3 proves too noisy in practice, and slice 13's `reviewer` may absorb it.

**Fold the artifact-location work into slice 10 (ADR-0007).** Artifact dispositions and artifact locations are adjacent, and slice 10 is unbuilt. Rejected on the same timing argument ADR-0008 used: slice 10 is a manifest schema change, a new command, and an installer rewrite, while this is a reference file and a citation sweep blocking a dogfood that is now the project's critical path.

## Consequences

**Positive:**

- The two clauses that account for eight of seventeen findings become enforced rather than restated. A new command that writes an artifact and forgets its carrier fails the suite before it reaches a validation doc.
- The pack's most reliable defect generator gets a step that can fail, at the point where fixing it is free rather than at red.
- The build loop runs the gates the project actually blocks on, so a coverage failure surfaces in the step that caused it rather than across six steps of diff at the merge gate.
- Spec, plan, and summary locations stop colliding with brownfield projects' existing artifact trees — the failure flow-4 hit silently, and the class the pack's whole brownfield posture exists to prevent.
- `architect` can no longer form a recommendation while unable to tell whether precedent exists.

**Negative / risks:**

- **Date prefixes are a seeded-shape change shipping alongside a large release.** That is precisely the condition that produced pr140's unnumbered finding. Mitigated by keeping the `MIGRATIONS.md` entry an anchored single-line replacement of `state.md.template`'s `Active feature  short slug matching docs/specs/<slug>.md` line, and by `tests/test_migrations_snapshot.py`, which already blocks a release whose template diff has no entry.
- **`tests/test_clause_one.py` parses prose.** "Every phase heading containing a write verb" is a heuristic, and it will produce both false positives (a phase that describes a write it does not perform) and false negatives (a write described without a listed verb). Accepted deliberately: a test that occasionally demands a `Writes:` line where none is needed costs one line, while the defect it prevents costs a validation round. The verb list is data in the test, revisable without redesign.
- **Phase F3 adds a step to a command that already has eight.** `/plan` is the pack's longest command and this makes it longer. Weighed against five wrong symbols in one feature, and it sits adjacent to Phase F2, which is the other pre-approval check.
- **Three `/feature-merge` fixes remain authored by reading.** The `in-review` re-entry path is still the largest never-executed body of text in the pack, and slice 12 does not change that.
- Seventeen findings are being addressed in one slice. This is larger than the project's *small reversible steps* principle prefers, and the phase ordering exists specifically so A and B are independently committable and independently valuable.

**Open questions:**

- Should `Writes:` declarations extend to the *skills*, or only to slash commands? Leaning: commands only for now — `engineer`'s commit substep is the one skill-side staging list, and it is already correct. Revisit if a second appears.
- Does Phase F3 need a language-aware grep, or is a plain identifier search enough? Leaning: plain search, since a false "resolved" is impossible and a false "unresolved" costs one look. The dogfood should answer this.
- Should `artifact-locations.md` absorb `adr-registry.md` outright rather than sitting beside it? Leaning: no while the ADR registry has allocation semantics (floor-plus-one, re-scan before allocate) the other three artifacts do not. Revisit if a second artifact grows an ID.

## Relationship to slices 10 and 13

**Slice 10 (ADR-0007, artifact dispositions) remains unbuilt, and slice 12 does not depend on it.** The numbering is deliberate, as it was for slice 11. Slice 12 does add to slice 10's eventual surface: `artifact-locations.md` records where a project's specs, plans, and summaries live, which is information a disposition-aware manifest will want. That is a reason to build slice 10 *after*, not to build it first.

**Slice 13 is a renumbering, not new scope.** `CLAUDE.md` currently uses "Slice 9" for two different things: the built Enterprise API findings slice (`:67`, present in `inventory-and-build-order.md`) and the scoped-but-unauthored `debugger` skill plus `reviewer` subagent (`:72`, absent from the inventory). The deferred pair becomes **slice 13**, and the owner's decision from this round is recorded with it: **the `reviewer` gate is where multi-agent fan-out belongs** — diverse lenses over one diff, rather than parallelism in the build loop, which is serialized on purpose. Findings 6 and 7 are both single-lens misses, which is the evidence for putting it there and not elsewhere.

## Build slice

**Slice 12**, in five phases. Task-level breakdown lands in [`inventory-and-build-order.md`](inventory-and-build-order.md).

- **Phase A — clause 4 and the gate list (flow-6, flow-7).** `/plan` Phase F3; `engineer` Verify substep 3; `/plan` *Approach* emits the per-step gate command. Both highs, independently shippable, no dependency on B–E.
- **Phase B — clause 1 by construction (flow-1, pr140-3, pr140-unnumbered).** `Writes:` lines across every artifact-producing phase; `tests/test_clause_one.py`; staging lists derived from declarations; `MIGRATIONS.md` entries become anchored sentence-level replacements naming their template hunk.
- **Phase C — clause 3 sweep (flow-4, pr140-5, pr140-6, pr140-7).** New `pack/references/artifact-locations.md`; date-prefixed spec/plan/summary paths and the ~20 citation sites; `adr-registry.md` scan scope; `engineer` `related_adrs` linking; `architect.md` silence-is-not-an-input.
- **Phase D — `/feature-merge` `in-review` corrections (pr140-1, pr140-2, pr140-4).** Textual fixes to a never-executed path, flagged as such in the command and in `docs/validation/slice-12.md`.
- **Phase E — corrections, doc currency, release (flow-2, flow-3, flow-5, flow-8, flow-9).** The five documentation fixes; the slice-12 section in `inventory-and-build-order.md`; the slice-9 → slice-13 renumbering in `CLAUDE.md`; `VERSION` → 0.12.0; re-snapshot to `pack/templates/history/0.12.0/`; the 0.12.0 migration entries.

**Version 0.12.0, not 0.11.1.** A new tracked component ships (`references/artifact-locations.md`), a seeded file's shape changes (the `Active feature` field meaning), and `/plan` gains a phase.

**Dogfood:** Enterprise API, which now has an open PR (#141) from the run that produced these findings. Behavioral predictions recorded in `docs/validation/slice-12.md` and unrun until then. The prediction that matters most is clause 4's: draft a plan naming a symbol that does not exist, and confirm Phase F3 halts before the approval gate — the check that would have caught five defects in the feature that motivated it. Two carry over unresolved from this round and should be predicted explicitly: whether `/feature-merge`'s content-diff discriminator runs **no** gates on an unchanged reopened PR (ADR-0008's clause-2 prediction, still unrun), and whether the `PostToolUse` drift hook has a genuine gap or merely lost its output in a long session.
