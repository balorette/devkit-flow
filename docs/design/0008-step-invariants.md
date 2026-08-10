# ADR-0008: Step Invariants — Artifact Transport, Self-Reference, and Discovery Order

**Status:** Proposed
**Date:** 2026-08-10
**Deciders:** [user], Claude (design partner)
**Evidence:** [`docs/validation/pr139-pack-findings.md`](../validation/pr139-pack-findings.md) Findings 1–8, each re-verified against `pack/` source before this ADR was written

---

## Context

The Enterprise API install of 0.10.0 drew eight pack findings from two automated reviewers. All eight are real. Verification against `pack/` also moved three of them:

- **Finding 3 is narrower than filed.** `feature-start.md:34` already orients on the ADR location *"per `CLAUDE.md` conventions, not assumed to be `docs/adr/`"*, and `plan.md:148` already passes *"relevant ADR files from the project's registry."* The defect is not that discovery is absent from Phase A — it is that the full **scan procedure** exists only in Phase E, and one contract (`feature-start.md:130`) still hardcodes the path.
- **Findings 2 and 3 both reach into `agents/architect.md`.** Three sites (`:3`, `:18`, `:77`) send the subagent to `docs/adr/` in its own instructions. Fixing only the callers leaves the bug: the architect is told to read a directory that does not exist on the target.
- **Finding 5 under-reports.** `pr-review.md:78` (doc amendments) is uncommitted for the same reason `:79` is. The fix is one commit covering both steps, not one covering step 3.

### The theme

Four findings — #1, #5, #6, and half of #2 — share a shape: **a step produces a durable artifact and the step that transports it does not carry it.**

- `/plan` Phase F2 writes a `CONF` row; Phase G's staging list omits the ledger.
- `/pr-review` step 3 writes a `REV` row; step 4 pushes without committing it.
- A seeded template's shape changed in 0.10.0; the `MIGRATIONS.md` entry that carries it to upgraders documents one of the two changes.

Each was introduced by a *correct* local fix that stopped at the artifact and never reached the plumbing.

### The second shape, which has now recurred three times

Finding #4 is not a transport failure. `Gated baseline` records a SHA, then commits that record — producing a tip that can never equal the baseline, so the "already gated" branch is unreachable from PR-open onward. **The pack's own bookkeeping write is one of the things it later reads to decide what changed.**

That is the third instance of this shape in the pack's history:

| Instance | Where | How it failed |
|---|---|---|
| `in_reply_to_id` triage detection | `/pr-review`, pre-0.10.0 | The pack's own replies were re-fetched as new items to answer |
| local tip vs remote tip | `/feature-merge`, pre-0.10.0 | `/pr-review` pushes its fixes, making the tips agree while carrying ungated commits |
| `Gated baseline` | `/feature-merge`, 0.10.0 | Writing the baseline commits it, so tip ≠ baseline always |

Each fix was written by someone who had just understood the previous one. `pr-review.md:45` even names the generalization — *"the pack's own actions are among the things that changed the state it is reading"* — in a paragraph that sits four lines above finding #7, which is another instance of it. The pattern is understood locally and rediscovered globally. That is what an invariant is for.

### The third shape

Finding #3 is neither. It is **discovery that runs after the consumer that needs it** — the architect forms a recommendation in Phase B against a hardcoded path, while Phase E discovers the real registry two phases later. The report notes this is the same class as a type-gate defect found in the host project's own conventions this round. Being right eventually does not help a consumer that already ran.

### Why a rule instead of eight patches

Six of the eight findings are instances of three shapes, and two of those shapes have already recurred inside this pack after being fixed once. A patch-only pass fixes the eight sites and leaves the next component free to grow a ninth. The pack's own working principle — *never silently extend the design* — cuts the other way too: a rule the pack keeps rediscovering should be written down.

## Decision

Three clauses. Every pack component is held to them; every future component is checked against them at authoring time.

### Clause 1 — An artifact and its carrier are written in the same step

A step that produces a durable artifact names, **in that same step**, the thing that transports it to its consumer.

The carrier depends on the artifact:

| Artifact | Consumer | Carrier |
|---|---|---|
| A file in the repo | another clone, the PR, a later session | a commit, with its staging list named |
| A change to a *seeded* file's shape | an existing install | a `MIGRATIONS.md` entry for the version that ships it |

**What it forbids:** a step whose output is left for "whatever commits next" to notice. A staging list maintained by hand at a distance from the writes it covers is the failure mode — `/plan` Phase G lists four artifact classes and F2's ledger row is simply not among them.

### Clause 2 — Never infer "what changed" from state you wrote yourself

Where a pack decision reads state that the pack also writes, the pack's own writes are **excluded from the comparison explicitly**, and the exclusion is named at the point of comparison rather than assumed.

**What it forbids:** equality checks against a value the comparing step mutates; "has anything changed since X" where the step's own bookkeeping is among the changes; skip-sets built from a surface the pack posts into without filtering its own posts back out.

**Corollary:** when a comparison must tolerate the pack's own writes, prefer a **content** comparison over a **topology** one. `git diff <baseline> <tip> -- <pathspec>` answers "is the gated content the same," which is the actual question; `git rev-list` answers "were there commits," which a revert-and-restore correctly should not trip.

### Clause 3 — Discovery precedes every consumer, once per invocation

Where a value must be discovered rather than assumed — the ADR registry, the findings ledger, the project's blocking-gate list — discovery runs **before the first consumer**, and the result is recorded for the invocation so later phases neither re-derive it nor contradict it.

**What it forbids:** a discovery phase ordered after a phase that uses the discovered value; a contract that passes a default path when a discovered one exists; the same discovery procedure restated in more than one component, which is how two copies drift into disagreeing.

**Corollary:** a procedure with more than one consumer lives in `pack/references/` and is cited, not restated. This is why `findings-triage.md` and `solid-checklist.md` were extracted, and the reasoning is identical.

## What the clauses decide

| Finding | Clause | Fix |
|---|---|---|
| #1 `MIGRATIONS.md` 0.10.0 incomplete | 1 | The missed change ships in the **0.11.0** section; a snapshot test makes the diff unskippable |
| #2 `pm` writes ADRs to `docs/adr/` | 3 | Five `pm` sites cite the extracted procedure; three `architect.md` sites are reworded to receive discovered ADR paths from their caller instead of hardcoding `docs/adr/` |
| #3 architect invoked before discovery | 3 | Discovery runs in Phase A and is recorded; `feature-start.md:130` passes the discovered paths |
| #4 `Gated baseline` self-invalidates | 2 | Baseline becomes the closeout commit; discriminator becomes a content diff excluding `.claude/state.md` |
| #5 `/pr-review` pushes uncommitted | 1 | A metadata commit covering Phase D steps 2 **and** 3, before the push |
| #6 `/plan` Phase G omits the ledger | 1 | Ledger joins the staging list whenever F2 wrote a `CONF` row |
| #7 `/pr-review all` kills the filter | 2 | `all` disables the handled-original check only; devkit-marked items are always excluded |
| #8 `.claude/` ownership over-claimed | **none** | A scoping error, fixed by scoping — see below |

**Finding #8 is deliberately not covered by a clause.** `devkit-orientation.md:83` claims the whole of `.claude/`; the Enterprise API install is 25 pack-tracked files against 45 that are not, including 14 pre-existing subagents and a `settings.json` the installer merges into rather than owns. That is a wrong sentence, not a systemic defect, and `.claude/.devkit-manifest.json` already holds the precise answer. Inventing a rule for it would be the same over-correction that produced it: the section was written in response to the previous round's disputed bare-`print` finding, and the fix for over-applying host rules to pack files over-corrected into claiming host files for the pack.

### Clause 2 applied to `Gated baseline`

The report's account is incomplete: the closeout commit (`feature-merge.md:113` — summary, domain docs, ledger, `state.md`) also lands after the gates, so at PR-open the baseline is **two** commits behind the tip, not one.

```
gates 1-3 pass                      tip = A
closeout commit                     tip = C     baseline := C
push; gh pr create
transition commit (state.md only)   tip = T
```

The baseline becomes **the tip immediately before the `state.md`-only transition commit** — in practice the closeout commit — rather than the gate-time SHA. Stating it that way rather than naming the closeout commit keeps it correct on the rerun path, where no closeout commit is written, and where `feature-merge.md:117` already blocks PR creation if the closeout commit was declined. Exactly one commit is then unaccounted for. The discriminator becomes:

```
git diff --quiet <baseline> <tip> -- . ':(exclude).claude/state.md'
```

Quiet → the gated content is unchanged; run no gates. Differs → re-run gates 1–3.

The rerun path preserves the invariant: gates run against tip *X*, baseline := *X*, and the transition commit touches only `state.md`, so the next invocation is quiet again.

The exclusion list is exactly one file, and that is the point. Setting the baseline to the gate-time SHA would require excluding `.claude/state.md`, `docs/summaries/**`, `docs/domains/**`, and the *discovered* ledger path — four entries, one resolved at runtime, each a place where a genuinely ungated change could pass as gated.

### Clause 3 applied to the ADR registry

The scan procedure moves to **`pack/references/adr-registry.md`**: scan scope, both match patterns, definitions-ranked-above-mentions, floor-plus-one allocation, ask-before-relocating, and the never-trust-a-cached-high-water-mark rule. Four components cite it and none restate it — `pm`, `/feature-start`, `/plan`, `/adopt` — plus `architect`, which receives the discovered ADR paths from its caller rather than citing the reference itself.

`pm` is why the reference is a file rather than a section of `/feature-start`. It is a skill, loadable outside any command, and a skill citing a slash command for its own write path is a backwards dependency. `tests/test_pack_references_resolve.py` already enforces that every citation resolves in a target install, so the new file is covered the day it lands.

## The forks, resolved

**Decision 1 — an ADR plus a corrections slice, not a corrections pass alone.** Two of the three shapes have already recurred after being fixed once, so the cost of leaving the rule as tribal knowledge in a validation report is measurable rather than hypothetical.

**Decision 2 — the ADR-registry procedure becomes a reference file.** Rejected alternatives: leaving `/feature-start` Phase E canonical (backwards dependency, above), and fixing only the nine hardcoded paths (leaves five copies of a procedure free to drift).

**Decision 3 — the `Gated baseline` fix moves the baseline rather than widening the exclusion.** A one-file exclusion is auditable; a four-entry one containing a runtime-discovered path is not. Keeping the baseline out of the committed file was rejected outright: it contradicts the async-resume requirement documented at `feature-merge.md:164`, where a second clone reading `Phase: building` opens a duplicate PR.

**Decision 4 — release mechanics get a snapshot plus a guard test, not a checklist.** No release baseline currently exists — the repo has no tags and `VERSION` was bumped mid-slice at `a11733e` — so "diff between versions" is not computable at all today. Committing a per-version copy of each seeded template under `pack/templates/history/<version>/` makes the baseline in-repo, retroactive, and independent of tagging discipline.

**No test can verify a migration entry is semantically complete.** That is precisely what finding #1 hit: a 0.10.0 section existed and was missing one of two changes. Automation's job here is narrower — guarantee the diff is *looked at*. Editing a template fails the suite until the snapshot is refreshed, and refreshing it is the moment the old→new diff is in front of the author.

## Alternatives considered

**Fold these into slice 10 (ADR-0007).** Findings #1 and #8 are both arguably the seeded/owned/discovered problem that ADR already designs. Rejected on timing: slice 10 is a manifest schema change, a new command, and an installer rewrite, while six of these eight findings are one-line-to-one-paragraph edits blocking a dogfood that is already overdue.

**Patch the eight sites, bump 0.10.1, no ADR.** Fastest to a dogfood-ready pack. Rejected per Decision 1.

**A lint-style authoring checklist instead of an ADR.** A checklist is read when someone remembers to read it. The three clauses need to be citable from a review — `conformance-reviewer` and `security-reviewer` can be pointed at an ADR; they cannot be pointed at a habit.

**Derive `/plan` and `/pr-review` staging lists mechanically** from the artifacts each phase declares it writes, rather than restating paths. Genuinely closes clause 1 by construction instead of by discipline. Deferred: it needs a per-phase artifact declaration the pack does not have, and the two staging lists at issue are three lines each.

## Consequences

**Positive:**

- Three shapes that between them account for six of these eight findings — and for two fixes the pack already shipped and then reproduced — get a name and a citable home.
- The ADR-registry procedure has one copy, so `/adopt`'s brownfield discovery cannot drift from `/feature-start`'s allocation.
- Every `/feature-merge` rerun on an unchanged open PR stops re-running tests, docs reconciliation, and a fresh-context security review.
- A seeded-template edit can no longer ship without its diff being surfaced.
- Slice 8's control flow gets corrected *before* its first dogfood, so the dogfood tests the design rather than rediscovering these.

**Negative / risks:**

- `pack/templates/history/` grows two files per release. Small, and it is the only in-repo release baseline that exists.
- The snapshot test blocks on a stale snapshot, which will occasionally be a nuisance edit during authoring. Accepted: that friction *is* the mechanism.
- Clause 2's `git diff --quiet` discriminator is more machinery than SHA equality, and a wrong pathspec fails **open** — treating ungated content as gated. This wants a behavioral prediction in `docs/validation/slice-11.md` specifically, and it is the highest-value thing for the dogfood to exercise.
- Six of these eight fixes are still authored by reading, not running. Slice 11 ships unvalidated, exactly as slice 8 and slice 9 did.

**Open questions:**

- Should clause 2's exclusion pathspec be centralized (a named "pack bookkeeping paths" list) rather than written at each comparison? Leaning: no while there is exactly one comparison. Revisit at the second.
- Should `conformance-reviewer` be taught to check plans against these three clauses? Leaning: out of scope — it reviews plans against specs, and this is an authoring-time property of the pack itself.
- `pack/commands/claude-md-merge.md` and `pack/commands/adopt.md` both write structural edits to a project's `CLAUDE.md` — the same artifact — but disagree on clause 1: `claude-md-merge.md:100,137` explicitly declines to name a carrier commit ("the user commits at their cadence"), while `adopt.md`'s Phase F proposes and commits the same kind of edit. A plausible rationale exists — `/claude-md-merge` may run before a project is git-bootstrapped, whereas `/adopt` gates on being a repo (`adopt.md:22`) — but neither file states it. Does clause 1 admit an exception for a command that may run outside a git repo, and if so must that exception be stated in the command rather than left implicit? Unresolved; not fixed in slice 11.

## Relationship to slice 10 / ADR-0007

ADR-0007 `:128` mitigates its own risk with *"a test asserting that a changed `state.md.template` has a corresponding migration entry for the current version,"* and `:147` puts `tests/test_migrations.py` in slice 10's build. Slice 11 lands that guard early, because finding #1 is the mitigated risk actually occurring.

The split:

- **Slice 11 builds `tests/test_migrations_snapshot.py`** — a snapshot exists for the current `VERSION` and byte-matches each live template; and where the current version's snapshot differs from the previous version's, `MIGRATIONS.md` carries a section for the current version. The second assertion is ADR-0007's proposed test, made computable by the snapshots.
- **Slice 10 extends it**, rather than authoring a competing file: entry ordering and per-version uniqueness (ADR-0007's third open question, leaning yes), and disposition awareness once the manifest carries dispositions.

Nothing in this ADR changes ADR-0007's taxonomy. `pack/templates/history/` is a **development-tree** artifact — it is not installed, not tracked in the manifest, and has no disposition.

## Build slice

**Slice 11**, in four phases. The task-level breakdown lands in [`inventory-and-build-order.md`](inventory-and-build-order.md) as part of this slice, alongside every other slice's.

- **Phase A — release guard (#1).** Snapshot templates to `pack/templates/history/0.10.0/`; `tests/test_migrations_snapshot.py`; the missed Open-questions entry into the **0.11.0** section, not retroactively into 0.10.0 — applicability is "sections newer than your installed version," so a 0.9.0 upgrader would otherwise apply it twice; release step into this project's `CLAUDE.md`.
- **Phase B — ADR registry (#2, #3).** New `pack/references/adr-registry.md`; `/feature-start` Phase A discovery + Phase E citation + the `:130` contract; five `pm` sites; three `architect.md` sites reworded to receive discovered ADR paths rather than to cite the reference; `/plan` and `/adopt` citations.
- **Phase C — transport and self-reference (#4–#7).** `/plan` Phase G staging; `/pr-review` metadata commit; `/feature-merge` baseline relocation and diff discriminator, including the `state.md.template` field comment it necessarily rewords; `/pr-review` `all`-mode filter and the `either`/`both` contradiction at `:40` vs `:45`.
- **Phase D — ownership (#8), doc currency, and release.** `devkit-orientation.md:81-89` scoped to the manifest's tracked set plus the two seeded exceptions; the slice-11 section in `inventory-and-build-order.md` and the status update in this project's `CLAUDE.md`; `VERSION` → 0.11.0; re-snapshot; the 0.11.0 migration entries.

**Version 0.11.0, not 0.10.1.** A new tracked component ships (`references/adr-registry.md`) and `Gated baseline`'s meaning changes. Two 0.11.0 migration entries: the missed Open-questions prose, and the reworded `Gated baseline` field comment.

**Dogfood:** Enterprise API, which now has two automated reviewers and six exercised PR lifecycles. Behavioral predictions recorded in `docs/validation/slice-11.md` and unrun until then. The prediction that matters most is clause 2's: open a PR, change nothing, re-run `/feature-merge`, and confirm it runs **no** gates — the branch that has been unreachable since `Gated baseline` was introduced.
