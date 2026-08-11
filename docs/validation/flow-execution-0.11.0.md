# Flow Execution Findings — first behavioral run of a pack command

**Source:** `/feature-start` → `/plan` → `/build` ×6 → `/checkpoint` ×6 → `/feature-merge`, executed end to end on Enterprise API at pack version **0.11.0**, immediately after the 0.10.0 → 0.11.0 upgrade merged (example-corp/enterprise-api#140).
**Feature produced:** a reconciliation-gate slice, shipped to an open PR (#141). Spec drafted and approved, architect invoked, ADR-013 allocated and written, plan drafted with 6 steps, conformance review run, all six steps built under TDD with a `tester` subagent per step, six mid-feature amendments, three merge gates passed, summary authored, findings ledger created, branch pushed, PR opened, `state.md` transitioned to `in-review`.
**Status:** 9 findings. All observed during execution, not read off the page.
**Date:** 2026-08-10 / 2026-08-11

---

## What this is, and why it is different from the other validation docs

Sibling to `pr140-pack-findings.md`, which holds **static-review** findings on 0.11.0's *text*. This doc holds findings from **running** the flow.

Every prior validation doc in this directory carries some version of the same caveat:

> **Still not a dogfood.** No pack command has executed. Findings 4, 5, and 7 in particular are reasoning about control flow that has never run.

**That caveat is now retired for the whole build lifecycle.** `/feature-start`, `/plan`, `/build`, `/checkpoint`, and `/feature-merge` have all executed against a real brownfield project with a real feature, along with all four fresh-context subagents — `architect`, `conformance-reviewer`, `tester` (six times), and `security-reviewer`.

**Still unrun:** `/pr-review`, `/checkpoint park`, and `/feature-merge`'s **closeout** path (the second invocation, after the PR merges). `/feature-merge`'s `in-review` re-entry path — which carries four of the seven findings in `pr140-pack-findings.md` — remains the largest body of never-executed text in the pack, and this run stopped one step short of exercising it.

**The headline: the flow worked, and shipped.** Every phase of every command ran in order, every gate paused where it said it would, and the feature reached an open PR with all four CI gates green. The findings below are nine seams, not a verdict.

**The structural theme, stated once — now four instances, not two.** Findings 1, 4, 6, and 7 are the same shape: *a rule the pack states in one place and does not apply across the places it holds.*

- **Clause 1** (an artifact and its carrier commit together) was applied to the sites the previous review named; **finding 1** found another the patch list missed.
- **Clause 3** (discovery precedes every consumer) got `references/adr-registry.md` — **for exactly one artifact type**; **finding 4** hit the identical problem with plans, which have no equivalent.
- **Finding 6**: the pack declares a plan's type signatures authoritative and has no pass that verifies them.
- **Finding 7**: `/build`'s verify step enumerates two of a project's four gates.

Each is cheap to fix at the instance and cheap to fix as a rule; the recurring cost is fixing them one instance at a time. **Four independent findings now recommend the same remedy — sweep the rule across the pack rather than patching the sites a review happened to name.**

---

## Human Notes

We should format the names of the core created files like plans, designs, etc to include the date. I.E. 2026-08-10-super-cool-feature-design.md 

Should we be pulling in some things around fan out multi agent like SuperPowers? 

---

## Finding 1 — Phase H's staging list omits the artifact Phase E step 4 mandates

**Severity: medium.** Another ADR-0008 clause-1 instance, in the command that was not part of the 0.11.0 sweep.

`feature-start.md` Phase E step 4 requires:

> **Update the recorded high-water mark** in `CLAUDE.md` conventions to the number just written, so the record stays a useful hint rather than decaying into a wrong one.

I did this — `CLAUDE.md` went from `Highest at adoption: ADR-012` to `Highest known: ADR-013`.

Phase H then says to propose a commit for:

> the artifacts this invocation produced: the spec, any Phase-E ADRs, and the Phase-G `.claude/state.md` updates.

**The `CLAUDE.md` edit is named nowhere.** It is a Phase-E artifact but not "a Phase-E ADR." Following Phase H literally — and it says *"Stage these files explicitly; never `git add -A`"*, so the literal list is the operative instruction — leaves a modified `CLAUDE.md` uncommitted in the working tree.

The downstream consequence is the same one `/feature-merge`'s gate-rerun row has: the next command's precondition trips on a dirty tree, and the high-water mark that Phase E just corrected sits unshipped, so the next `/feature-start` re-reads the stale number it was written to fix. The failure is self-cancelling in the worst way — step 4 exists specifically to stop the record decaying, and the omission un-does step 4.

**This is exactly the shape ADR-0008 clause 1 names**, in a command the 0.11.0 sweep did not cover. `/plan` Phase G and `/pr-review` Phase D each gained the commit that carries what they write; `/feature-start` Phase H was not revisited. That strengthens the recommendation already in `pr140-pack-findings.md`: **clause 1 needs a sweep across every artifact-writing step, not a patch list.** This finding was found by running one command that the patch list happened to miss — there is no reason to think it is the last one.

**Suggested fix:** add the `CLAUDE.md` high-water update to Phase H's staging list explicitly. Cheap, and it makes the Phase E → Phase H handoff complete.

---

## Finding 2 — the slice-2 simulation note on `architect` is stale

**Severity: low (documentation accuracy).** It advises a fallback for a condition that no longer occurs.

`feature-start.md` closes its *Invoking the architect* section with:

> **Slice-2 simulation note:** while the pack's subagent format is being stabilized in the host project, `subagent_type: architect` may not yet resolve. The validated fallback is `subagent_type: general-purpose` with the *contents* of `pack/agents/architect.md` passed as the prompt body.

**`subagent_type: architect` resolved correctly on first attempt** and produced exactly the expected shape — recommendation, rationale, trade-offs, precedent, and a draft ADR. The fallback was not needed.

The note is not harmful, but it invites an unnecessary workaround, and a reader who takes it at face value may reach for `general-purpose` and lose the architect's own system prompt. Worth either deleting or narrowing to "if your harness does not register custom subagent types."

**Evidence of the architect earning its round-trip**, since a validation doc should record what worked as well as what didn't: it *reversed the justification* for the feature while leaving the user's settled policy intact. The brainstorm had grounded a force-bypass on operational urgency; the architect rejected that as unfalsifiable ("would license a bypass on any gate anyone finds inconvenient") and re-grounded it on record truthfulness — the strict override would require asserting a cause the operator does not know. That reframing is what let the resulting ADR state a rule that *excludes* the adjacent edge, rather than merely describing the feature being built. It also caught three verified source-level defects the brainstorm had missed, including a shared freeze method whose hard-coded constants would have written a record asserting the opposite of what happened.

**One caveat worth carrying:** the architect also surfaced a claim about a prior ADR's override being unwired dead code. It was correct — verified — but I verified all five of its load-bearing source claims before reflecting any of them back, and that verification step is not in `feature-start.md`'s *Invoking the architect* section. The command says to "reflect the recommendation back to the user before accepting it," which is a **user** gate, not a **truth** gate. Consider adding: verify the subagent's source-level factual claims before reflecting them, since a fresh-context agent's confident file:line assertions are exactly what a user cannot check from the reflection alone.

---

## Finding 3 — "restart Claude Code" is imprecise about what is stale

**Severity: low (documentation accuracy).** It over-warns, and the over-warning is the kind that gets ignored.

`install.sh`'s closing output says:

> 2. Restart Claude Code so it picks up the new `.claude/` contents.

Acting on that, I told the user a restart was required before dogfooding 0.11.0, on the reasoning that the session had indexed 0.10.0's skills at startup. **That was wrong, and I hedged the run unnecessarily.**

Observed: `Skill(pm)` and `Skill(grill-me)` both loaded the **0.11.0** files from disk mid-session, with no restart. Confirmed by content — the loaded `pm` skill referenced `.claude/references/adr-registry.md` throughout, a file that does not exist in 0.10.0. Skill bodies are read at invocation time.

What is genuinely startup-indexed is the **command/skill discovery listing** (names and descriptions), not the bodies. So the accurate statement is narrower: a restart is needed for *newly added* commands or skills to appear in the slash-command index; *changed* bodies of already-listed items load fresh.

This matters more than a wording nit, because the pack's whole update story is "install, then keep working." A blanket restart instruction that turns out to be unnecessary is one users learn to skip — and then they skip it on the release that adds a new command, which is the case where it was actually load-bearing.

**Belt-and-braces note for the pack:** I sidestepped the ambiguity by reading `.claude/commands/feature-start.md` from disk and following that file directly rather than relying on session-cached command text. That guarantees a true version-N run and is worth recommending explicitly for the first invocation after any upgrade.

---

## Finding 4 — `/plan`'s preconditions check for a file, not for an occupied namespace

**Severity: medium.** On a brownfield project it silently interleaves the pack's artifacts with another system's.

`plan.md` Preconditions step 2 requires:

> `Plan` is `—` (no plan exists yet) **or** the plan file does not exist on disk.

Both were true here. `.claude/state.md` said `Plan: —`, and `docs/plans/cancel-reconciliation-gate.md` did not exist. **The precondition passed cleanly — and writing there would still have been wrong.**

`docs/plans/` already existed on this project, holding its own legacy plans (`2025-11-28-airspace.md`, `2026-06-03-docs-alignment-plan.md`, and a `completed/` subdirectory). Meanwhile the project's *current* plans live in `docs/ai/plans/`, and its `CLAUDE.md` says so explicitly: "Write new artifacts to `docs/ai/{brainstorms,designs,plans,actions}/`."

So the pack's default target was a directory that (a) exists, (b) belongs to a different system, and (c) the project has already migrated away from. The precondition cannot see any of that, because it asks about one filename rather than about the directory's provenance. I caught it only by listing the directory before writing — which the command does not ask for.

**The failure is quiet and compounding.** Nothing errors. The plan lands beside legacy artifacts, `state.md` points at it, `/build` follows the pointer and works fine. The cost is that the project now has devkit plans in the retired tree and project plans in the live one, which is precisely the two-vocabularies problem the host project closed deliberately in an earlier PR — and the same problem the `state.md` collision raised at install, where the resolution was an explicit user decision rather than a default.

**There is already a model for the fix in the pack.** `references/adr-registry.md` exists because exactly this happened with ADRs: a hardcoded `docs/adr/` would have allocated `0001` over a twelve-entry registry living somewhere else. That reference solved discovery-before-write for **one** artifact type. Specs and plans have the same exposure and no equivalent.

**Suggested fix**, in increasing order of ambition:

1. Add to `/plan`'s preconditions: if `docs/plans/` exists and contains files not written by the pack, surface it and ask rather than writing.
2. Have `/adopt` record the project's artifact homes in `CLAUDE.md` conventions — it already records the ADR registry location — and have `/feature-start` and `/plan` read that record.
3. Generalise `adr-registry.md` into an artifact-location reference covering specs, plans, and ADRs, since clause 3 ("discovery precedes every consumer") is not ADR-specific and the pack now has two demonstrated instances.

Worth noting the asymmetry that made this findable: **specs were fine.** `docs/specs/` did not exist and `CLAUDE.md`'s artifact list has no "specs" entry, because spec-as-contract is a genuinely new concept for this project. Plans are not new. The collision risk scales with how ordinary the artifact name is.

## Finding 5 — Phase F2's `CONF`-row instruction has no branch for "the advisory was fixed"

**Severity: low.** Under-specifies the most likely action, and the gap pushes toward the worse outcome.

`plan.md` Phase F2 says:

> **Record every advisory the user leaves outstanding as a `CONF` row in the findings ledger** … Advisories do not block approval, which is exactly why they evaporate.

The reasoning is right, and the ledger row is the right destination for a genuine deferral. But the phase describes only two dispositions for an advisory — leave it outstanding (→ ledger) or, implicitly, do nothing — and says nothing about the third, which is what actually happened on this run: **all three advisories were cheap to fix, so I fixed them in the plan and recorded no rows.**

That is the better outcome, and the text does not name it. A literal reader has to either defer a fixable finding to the ledger — where it becomes durable memory of a problem that could have been gone in two minutes — or improvise past the instruction. Neither is what the phase intends.

The advisory that made this concrete is worth recording, because it is also the best evidence for why Phase F2 exists at all. The reviewer flagged that a shared freeze method's `close_succeeded` parameter defaulted to `True` — the *passing* value on the field that a governing ADR's distinguishability obligation rests on. Acceptance mapping had already passed: the criterion said "forced → `False`," and the step that satisfied it did exactly that. **Coverage checking asks whether a criterion is addressed; contradiction checking asks whether anything present undercuts what the spec promises.** A fail-open default on a safety field is invisible to the first question and obvious to the second. Fixing it cost one edit; deferring it to a ledger row would have been absurd.

**Suggested fix:** one sentence naming the third disposition — "an advisory you fix in the plan needs no row; the ledger is for what you deliberately leave" — plus a note that cheap fixes are preferred to deferrals, so the ledger stays a record of real decisions rather than of postponed edits.

## Finding 6 — a plan's type signatures are declared authoritative and nothing verifies them

**Severity: high.** Five occurrences in one feature. It is the pack's most reliable defect generator.

`/plan` writes type-signature blocks and the `engineer` skill states their status plainly:

> The signatures are authoritative. If the signatures are wrong, the tester writes the wrong tests.

Across six steps, the plan named **five symbols that do not exist**:

| Named in the plan | Actual | Where |
|---|---|---|
| `CaseLayout` | `ReconciliationCaseLayout` | Step 2 signature block |
| `ShowResponse` (return type) | `Show \| None` | Step 5 signature block |
| `build_manifest_conflict_detail` | `manifest_409_detail` | Conventions table + 3 prose sites |

**The reason it recurred is structural, not careless.** Trace who could have caught it:

- The **`conformance-reviewer`** deliberately has no codebase access. It verifies plan-against-spec, so it will happily confirm consistency between two documents that are both confidently wrong about the code. That is by design and the design is right — but it means conformance is not a truth check.
- The **`tester`** is explicitly forbidden from reading implementation source. It writes tests against whatever the plan declares.
- The **`engineer`** discovers the error at red — the last possible moment, after the tester has already spent its context on a contract that cannot compile.

So the artifact with the **most downstream authority** is the one artifact with **no verification pass**. Every other durable artifact has one: specs get conformance review, code gets tests and three CI gates, the diff gets security review. Plans get approval by a user who cannot reasonably be expected to grep every symbol.

**Suggested fix.** A `/plan` pre-approval step: extract every symbol the plan names — types in signature blocks, functions in the conventions table, methods in prose — and grep each one. Report unresolvable names before the user is asked to approve. This is mechanical enough to be a hook rather than model work, and it closes the gap at the point where fixing it is free.

**Note on the partial fix that failed.** A rule was recorded mid-feature after the third instance: *"every type named in a signature block must be grep-confirmed."* Instance five landed in the **conventions table** — neither a type nor a signature block — so the narrow rule did not cover it. Which is itself the theme above: the rule was written for the instances seen rather than the class.

---

## Finding 7 — `/build`'s verify step enumerates lint and typecheck, not the project's actual gates

**Severity: high.** The gate most likely to fail is the one the loop never runs, and it fails at the most expensive moment.

The `engineer` skill's Verify substep 3 reads:

> Run the linter and type-checker if the project uses them. Identify them from `CLAUDE.md`, `pyproject.toml`, `package.json`, etc.

Two named tools. This project has **four** blocking CI gates: ruff, a mypy total-count ratchet, pytest, and `diff-cover --fail-under=85` on changed lines. All six steps verified green on the first three. Coverage was never run, because nothing told the loop to run it.

When it was finally run — after step 6, unprompted — it was at **80%**. The endpoint handler bodies sat at 34.8%, because in this project ASGI-client integration tests produce no coverage for handler code; only direct calls do. Fixing it required six new unit tests written against code from several different steps.

**The cost is entirely in the timing.** Had the loop run coverage per step, step 6 would have failed its own verify with its own code fresh in context, and the fix would have been three tests in the step that caused it. Instead it surfaced at merge, where the diff spans six steps and the person fixing it has to reconstruct which step each uncovered line came from. `/feature-merge` Gate 1 *would* have caught it — but Gate 1 is where you learn it, not where it is cheap.

Note that the plan's *Framework constraints* table **did** record the gate, with the ASGI-coverage caveat and the exact reproduction command. The knowledge was captured correctly at plan time and simply never reached the loop that needed it.

**Suggested fix.** Reword substep 3 to "run the project's gates" and have `/plan` emit the gate list as a concrete per-step verify command in the *Approach* section. On a project whose gates are already recorded in `CLAUDE.md` (as `/adopt` does), the loop can read them directly.

---

## Finding 8 — the tester's findings channel is written as an error path and behaves as a primary output

**Severity: medium.** The framing invites treating the most valuable output as a fault.

The `engineer` skill mentions tester findings once, conditionally:

> If the tester returns **findings instead of tests**, do not work around them and do not re-invoke with a looser brief.

That describes a refusal. What happened across six steps is different: the tester returned findings **alongside** working tests, every single time, and several were the most valuable thing produced in that step:

- Step 2 — three existing frozen-row fixtures lacked a column the new code reads (correctly predicted, before it broke).
- Step 3 — the `unresolved`-beats-`reconciled` path shipped **untested**; the existing test could not distinguish it.
- Step 4 — **the AC-4 gap.** The tester noticed that `update_show_status` is a different method and asked whether it delegates. It does not. Without that observation the feature would have shipped a gate on one cancel endpoint and a silent bypass on the other — the exact hole the feature exists to close.
- Step 6 — that ASGI-client tests would not produce handler coverage, and that it could not write the unit tests that would, because it lacked the handler signatures and was forbidden from reading the module.

None of these were refusals. All arrived with green-on-arrival test files. The skill has no guidance for this case, so what to do with them is improvised each time — and "findings that arrive with passing tests" is precisely the shape most likely to be skimmed.

**Suggested fix.** Rewrite the section as an expected **dual output**: tests plus findings. Add explicit triage guidance for findings-with-tests (in-scope-and-cheap → fix now; contract gap → `/checkpoint`; out-of-scope → ledger). One line in the tester's own definition inviting it to report what the test list omits would formalise what it already does well.

---

## Finding 9 — three-strikes exists for debugging, not for recurring process defects

**Severity: low.** A cheap escalation rule that already exists in one form and not the other.

The `engineer` skill escalates after three failed hypotheses on a bug:

> **Three strikes.** If three hypotheses have failed, stop fixing. Repeated failures in different places are evidence about the *design*, not about your attempts.

That reasoning generalises exactly, and the pack does not generalise it. The symbol slip in finding 6 was corrected at instances 2, 3, and 5 — each time by amending the specific instance and, at instance 3, by writing a rule narrow enough that instance 5 slipped past it. Three separate `/checkpoint` commits treated a class as three unrelated cases.

The debugging version of this rule would have fired at instance 3 and said: *stop correcting instances; the rule is wrong.*

**Suggested fix.** One sentence in the `documenter` skill: when a `/checkpoint` corrects the same class of defect for the third time in one feature, propose amending the process rule rather than the instance — and say so in the amendment.

## Suggested disposition

| # | Area | Sev | Note |
|---|---|---|---|
| 6 | Plan signatures authoritative, unverified | **high** | 5 occurrences in one feature; the pack's most reliable defect generator |
| 7 | `/build` verify omits the project's real gates | **high** | Coverage gate failed at merge instead of at the step that caused it |
| 1 | `feature-start` Phase H staging list | med | Clause-1 violation in a command the 0.11.0 sweep didn't cover |
| 4 | `/plan` precondition vs occupied namespace | med | Passes cleanly while writing into another system's directory |
| 8 | Tester findings framed as an error path | med | Caught the AC-4 gap; the framing invites skimming it |
| 2 | `feature-start` slice-2 simulation note | low | Stale; also consider adding a verify-before-reflect step |
| 3 | `install.sh` restart guidance | low | Over-warns; narrow it to newly-added commands |
| 5 | `/plan` Phase F2 advisory dispositions | low | No branch for "fixed it"; pushes fixable findings into the ledger |
| 9 | Three-strikes not generalised to process defects | low | Same class corrected three times as three unrelated cases |

**Findings 6 and 7 are the ones to fix first** — both are high, both are mechanical, and both would have paid for themselves inside this single feature. Finding 6 cost five round-trips; finding 7 cost a coverage rescue across six steps' worth of diff at the merge gate. Neither needs judgment to fix: one is a grep, the other is reading a gate list the plan already recorded.

**Findings 1 and 4 matter as evidence for claims already made.**

Finding 1 supports the clause-1 sweep recommended in `pr140-pack-findings.md`: two commands executed, one previously-unknown instance found, in a file the static review had already read twice. A patch list will keep missing these.

Finding 4 is the stronger result, because it says the same thing about **clause 3**. `references/adr-registry.md` was built to satisfy "discovery precedes every consumer," and it works — finding 4's own writeup notes the ADR registry discovery ran flawlessly on this project's unusual single-log layout. But it was built for one artifact type, and the very next artifact the pack wrote hit the same class of problem with no reference to protect it. **Clause 3 needs the same sweep clause 1 does.**

Both sweeps share a diagnosis worth stating plainly: 0.11.0 fixed the *instances* the previous review reported, and the instances were correct, but neither clause was applied as a rule across the pack. Two commands' worth of execution surfaced one new instance of each.

## What ran clean, and is now behaviorally confirmed

Recording these so a future reader can tell "verified working" from "never exercised". **The strongest single result is at the top — a validation doc that only lists defects misrepresents a pack that shipped a feature to a green PR on its first end-to-end run.**

- **All four fresh-context subagents found something their caller could not, and two found something the caller was actively wrong about.** This is the pack's central bet, and it is the clearest evidence in the doc:
  - **`architect`** reversed the feature's *justification* while leaving the user's settled policy intact. The brainstorm had grounded a safety-gate bypass on operational urgency; the architect rejected that as unfalsifiable ("would license a bypass on any gate anyone finds inconvenient") and re-grounded it on record truthfulness. That reframing is what let the resulting ADR state a rule that **excludes** the adjacent edge rather than merely describing the feature being built.
  - **`conformance-reviewer`** caught a fail-open default (`close_succeeded: bool = True`) on the exact field the governing ADR's distinguishability obligation rests on. Acceptance-mapping had already passed — the criterion was covered and the mechanism protecting it was broken. That is precisely the gap Phase F2 claims to close, now demonstrated rather than argued.
  - **`tester`** surfaced the AC-4 gap (see finding 8), without which the feature would have shipped a gate on one endpoint and a silent bypass on the other.
  - **`security-reviewer`** found a self-authorized-flight path in a diff that never mentions flight authorization. The spec asserted a permission gated four routes; it gates 23 across five routers. The reviewer re-derived the surface from source instead of trusting the summary it was handed — and the summary was mine.
- **The doc-currency loop demonstrably works.** Six steps produced six `/checkpoint` commits; the spec and plan are measurably *more* accurate at merge than at approval, with every correction dated and reasoned in place. Stated neutrally: this is either the loop working as designed, or evidence that plans are authored deeper than they can sustain — and the data does not distinguish them. Worth watching over the next few features rather than concluding now.
- **`/feature-merge`'s three gates each caught something distinct.** Gate 1 caught nothing (the steps had verified as they went). Gate 2's `owned_files` check caught two files touched outside declared scope. Gate 3 caught the permission blast radius. Three gates, three different failure classes, no redundancy between them.
- **Gate 2 caught drift the `PostToolUse` hook did not.** Both out-of-scope files (`show_flights.py`, `CLAUDE.md`) were edited without a drift warning surfacing. Either the hook has a gap or its output was lost in a long session — worth checking, since at-edit warnings are the cheap layer and the merge gate is the expensive one. **This is the one item here that is a lead rather than a confirmation.**
- **`Gated baseline` was set correctly on the transition.** Recorded as the tip *before* the `state.md`-only commit, exactly as the 0.11.0 semantics require. Whether the content-diff comparison behaves on re-entry is still unrun — that is the gap named at the top of this doc.

- **ADR registry discovery on the single-log format.** `Discover` correctly identified `docs/ai/decisions.md`, a single log with `## ADR-NNN:` headings, high-water 012, and correctly ranked heading **definitions** over the 42 prose **mentions** of ADR-012 scattered through the docs. This is the exact layout the reference was written for, and it worked without a hint from `CLAUDE.md`.
- **Actual paths, never a pattern.** The architect received `docs/ai/decisions.md` as a literal path. `docs/adr/NNNN-*.md` would have matched nothing here, and the architect would have formed its recommendation having read no prior decisions — it instead cited ADR-008, ADR-011, and ADR-012's amendment, and the ADR-011 citation reframed the whole finding from "first-of-kind precedent" to "scoping an existing unbounded allowance."
- **Re-scan before allocation.** Phase E step 1's full re-scan ran and returned 012, matching Phase A. It would have caught a concurrent allocation; on this run it confirmed rather than corrected. The mechanism is exercised, not merely present.
- **Every user gate paused.** Phase A slug/framing, Phase B brainstorm batches, the architect reflection, Phase C decomposition, and Phase H's commit proposal all stopped for confirmation. No phase auto-advanced past a gate.
- **The brainstorm caught a decision whose consequence was invisible in its own framing.** A permission-reuse option was offered without first checking which roles hold that permission; a scan showed it was ADMIN-only, which would have defeated the feature's stated rationale. `grill-me`'s "if a question can be answered by exploring the codebase, explore the codebase instead" is the rule that was violated in offering it and the rule that caught it. Worth noting the discipline works even when the model applies it late.
- **`conformance-reviewer` resolved and did the job Phase F2 claims for it.** Returned 0 blocking / 3 advisory in fresh context with only two paths and no codebase access. Critically, it caught something acceptance-mapping structurally could not: a shared method's `close_succeeded` parameter defaulting to the *passing* value, on the exact field a governing ADR's distinguishability obligation depends on. The acceptance table was complete and correct; the default undercut it anyway. **Phase F2's stated rationale — "acceptance mapping checks that every criterion is covered; it cannot see a step that covers a criterion while violating it" — is now demonstrated rather than argued.**
- **Plan-time allocation re-scan.** `/plan` Phase A's discovery correctly returned high-water **013** — the ADR `/feature-start` had allocated one command earlier in the same session. This is the precise scenario `§ Never cache the number` warns about ("`/plan` allocating from a mark `/feature-start` already consumed is exactly how two ADRs end up claiming one ID"), and the re-scan behaved as designed. It happened not to matter here because Phase C invoked no architect, but the mechanism was exercised against a genuinely-moved registry rather than a static one.
- **Phase C's architect-exception reasoning held under a real case.** Dual-permission authorization was a verified project-first *and* sits on the cross-cutting list (authorization placement), which reads as a mandatory architect call. The `pm` skill's stated exception — "a prior ADR already decides the pattern (cite it, no new invocation needed)" — correctly suppressed a redundant invocation, because the ADR written one command earlier had already decided it. Without that exception the flow would have re-litigated its own freshly-ratified decision at the user's expense.
- **The two-state-file arrangement survived a full command sequence.** `.claude/state.md` transitioned `idle → spec-draft → spec-approved → plan-draft` while `docs/ai/STATE.md` was untouched, which is the intended division. The scope blockquote added at install is still the only divergence from the template.
