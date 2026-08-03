# ADR-0006: Findings Ledger and Plan Conformance

**Status:** Proposed
**Date:** 2026-08-03
**Deciders:** [user], Claude (design partner)
**Evidence:** Astraeus's review corpus (`docs/reviews/`, 97 closed / 2 open issues); [`docs/validation/brownfield-install-astraeus.md`](../validation/brownfield-install-astraeus.md) Findings 5 and 9

---

## Context

Astraeus carries a mature, home-grown review practice: a `CQ`/`SD`/`AR`/`TD` × `P0`–`P4` taxonomy, twelve session files, and **97 closed / 2 open** issue files. It worked. Reading it against the pack surfaced two gaps that no existing devkit component covers.

### Coverage is not conformance

The richest artifact in the corpus is `2026-04-15-qr-storage-system-review.md`, a review of a **spec and plan before implementation**. Its *"SPEC–PLAN MISALIGNMENT"* section catches four contradictions:

| # | Spec states | Plan states |
|---|---|---|
| 5 | `HTTP 409` for load blocks | returns 200 in all cases |
| 6 | `GET /scan`, top-level, crosses entity types | `GET /cases/scan`, nested — semantically wrong |
| 7 | `GET /shows/{id}/case-pull-list` | `POST /cases/pull-list` — a materially different endpoint |
| 8 | deactivate hard-blocks on active memberships | `StorageCaseUpdate` exposes `is_active` — **a backdoor around the spec's safety rule** |

Devkit would catch none of them, and the reason is structural. `/feature-merge` Gate 2 performs *acceptance-criteria coverage*: "for each criterion, identify which plan step satisfies it." That asks **is every criterion covered?** It never asks **does any step contradict a criterion?**

Item 8 is the sharp case: the plan *covers* the deactivate criterion and simultaneously opens a schema backdoor that violates it. Coverage-checking is structurally blind to that class — a plan can map every criterion to a step and still specify 200 where the spec says 409.

Every one of these is detectable from two documents, **before a line of code exists**.

### Findings have no durable home, and the pack claims otherwise

`comparison-table.md` scores devkit ✅ on *project-scope memory* against Superpowers' ❌, and names it one of four places the pack earns its keep. Findings are project-scope memory, and devkit's evaporate:

- `security-reviewer`'s non-critical findings go into a summary doc and are never revisited.
- `/pr-review`'s accepted-but-unfixed items go to `state.md` `## Open questions`, which **`/feature-merge` clears**.
- `architect` recommendations that didn't become ADRs leave no trace.

Astraeus needed a ledger badly enough to build one, and closed 97 issues through it.

### The same gap, seen from the other side

Validation Findings 5 and 9 note a shared root cause: *"the pack has no persistent record of what it has already done to a PR."* Finding 5 — no gated-baseline SHA, so a `/feature-merge` rerun can skip every gate. Finding 9 — dedupe works only for inline threads, so a second `/pr-review` pass re-fetches the pack's own replies.

That is this ADR's gap from a different angle: **devkit infers prior work from current state, which fails when its own actions are among the things that changed that state.**

## Decision

### A. `conformance-reviewer` — a plan-time subagent

Rescoped from the `reviewer` subagent ADR-0003 deferred to slice 9. **Receives the approved spec and the draft plan. Never receives code.**

Fresh context is load-bearing for the same reason it is for `tester`: the plan's author is the worst-positioned auditor of their own contradictions, being anchored on the choices they just made. Excluding code is deliberate — a reviewer that reads source drifts into being a second code reviewer, and Astraeus already has `elite-code-reviewer` occupying that slot.

Findings take one shape: *"Plan §X states P; spec §Y states Q; these contradict."* The four misses above are the acceptance test.

Invoked at the end of `/plan`, **before** the user flips `status: approved`. A blocking finding means the plan is revised, not approved-then-amended.

### B. `docs/findings.md` — a thin durable ledger

One append-only table — `id · category · severity · source · status · where` — not 97 files. A per-finding file is created only when a finding needs more context than a row holds.

This is ADR-0002's already-resolved **thin-base-then-grow** fork applied again. Astraeus's per-file shape scaled to 97 and is proven; it is also the shape a small team abandons at 5. Start thin; the escape hatch is one file per finding, at exactly the point the row stops being enough.

Categories borrow Astraeus's axis, mapped to devkit's producers:

| Prefix | Source |
|---|---|
| `CONF` | `conformance-reviewer` |
| `SEC` | `security-reviewer` |
| `ARCH` | `architect` (recommendation that produced no ADR) |
| `REV` | external PR review, via `/pr-review` |

Owned by `documenter`. Written at `/feature-merge` and `/pr-review`. **Survives the merge** — that is the entire point.

### C. Gate 2 gains a conformance question

Three lines: Gate 2 currently asks whether every criterion is covered; it gains *"does any completed work contradict a criterion?"* This closes the same blind spot for drift introduced during the build rather than at plan time.

### D. Slice 9 is rescoped

ADR-0003 deferred two components. Both change:

- **`debugger` is not a fifth skill.** ~20 lines fold into `engineer` instead — root-cause-before-fix, failing test via `tester`, three strikes to `architect` + `/checkpoint`. A standalone skill would collide with `superpowers:systematic-debugging`, which is installed on the author's machine and carries a near-identical trigger.
- **`reviewer` is not a merge-time gate 4.** It becomes A above. This also erases the ~17-site gate-count phrasing ripple across six files that a fourth gate would have required.

## Persistence: three lifetimes, three mechanisms

An earlier framing of this design proposed that one ledger fix Findings 5, 9, *and* the durable-findings gap, on the strength of their shared root cause. **A shared root cause does not imply a shared mechanism** — these have three different lifetimes, and collapsing them would produce a file that is simultaneously machine state and human memory.

| Need | Lifetime | Mechanism | Owner |
|---|---|---|---|
| Gated-baseline SHA (F5) | Per-feature, ephemeral | A `**Gated baseline:** <sha>` field in `state.md`, alongside `PR:` | ADR-0003 amendment |
| Handled PR comments (F9) | Per-PR, lives on the forge | A stable marker in every reply the pack posts — `<!-- devkit:pr-review -->` — searched across all three surfaces | ADR-0003 amendment |
| Findings | Cross-feature, durable | `docs/findings.md` | This ADR |

The marker also **repairs rather than reverses ADR-0003 Decision 2.** "The forge is the ledger" was the right instinct; the defect was that its *detection* — `in_reply_to_id` — exists on only one of three comment surfaces. A marker the pack writes itself works on all three and still requires no local state.

## Alternatives considered

**A conformance checklist in `references/`, run by the main thread — no subagent.** Cheaper, keeps the pack at three agents. Rejected: it asks the plan's author to audit the plan they just wrote, which is precisely the failure the evidence documents.

**Keep `reviewer` as a merge-time code reviewer (gate 4).** Rejected on evidence. Astraeus's AR/SD/CQ/TD taxonomy already covers all four lenses ADR-0003 claimed were unowned, `elite-code-reviewer` occupies the generic-review slot, and `/pr-review` now triages what human reviewers catch. A merge-time finding also costs the entire build; a plan-time one costs a plan revision.

**Per-finding files, matching Astraeus.** Proven at 97 issues. Rejected as the *starting* shape for the reason above — with the growth path preserved.

**Leave findings in summaries.** Status quo. It is what produces the gap.

## Consequences

**Positive:**
- The highest-leverage review moves upstream of the build entirely.
- `project-scope memory` becomes true for findings, closing a claim `comparison-table.md` already makes.
- Slice 9 shrinks: one document-scoped subagent and a ~20-line skill edit, rather than a fifth skill plus a fourth gate plus a six-file phrasing ripple.
- The conformance-reviewer never reads code, so it cannot become a second code reviewer by drift.

**Negative / risks:**
- A subagent round-trip is added to every `/plan`. Mitigated by the input being two documents rather than a repo.
- `docs/findings.md` is a fifth durable artifact type. Justified against principle 6 by the 97-issue evidence and by an existing pack claim it makes true; bounded by starting as one table.
- A ledger that is written but never read is worse than none. `/feature-start`'s orient phase must read it, or it becomes a graveyard.

**Open questions:**
- Should `conformance-reviewer` findings block plan approval outright, or be advisory with the user deciding? Leaning: blocking for direct contradictions, advisory for ambiguity.
- Who closes a `docs/findings.md` row? Leaning: `/checkpoint` and `/feature-merge`, via `documenter`, never automatically.
- Does the ledger need a per-feature view, or is one table with a `where` column enough? Revisit after the first real use.

## Build slice

**Slice 9, Phase 3.** After Phase 1 (ADR-0005 brownfield) and Phase 2 (the ADR-0003 amendment fixing Findings 5–10), because both precede it in the lifecycle of a single Astraeus dogfood.

**Build:**
- `pack/agents/conformance-reviewer.md` — the subagent.
- Edit `pack/commands/plan.md` — invoke it before the approval hand-off.
- Edit `pack/commands/feature-merge.md` — Gate 2 conformance question; ledger writes.
- Edit `pack/commands/pr-review.md` — ledger writes.
- Edit `pack/skills/documenter/SKILL.md` — own `docs/findings.md`; the row format.
- Edit `pack/skills/pm/SKILL.md` — read the ledger during `/feature-start` orient.
- Edit `pack/skills/engineer/SKILL.md` — the ~20-line debugging fold-in.
- Edit `pack/references/findings-triage.md` — the ledger as a disposition.
- Doc currency: ADR-0003's deferred slice-9 section rewritten to point here; `README.md`; `pack/devkit-orientation.md`; `docs/design/inventory-and-build-order.md`.

**Dogfood:** run `/plan` on an Astraeus feature whose spec has a testable behavioral claim (a status code, a route shape, an endpoint signature) and confirm the `conformance-reviewer` catches a deliberately planted contradiction of the Finding-5-through-8 shape. Then confirm a `SEC` or `REV` finding written at merge is still present, and read by `/feature-start`, on the *next* feature.
