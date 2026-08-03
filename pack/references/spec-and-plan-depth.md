# Spec and plan depth

Used by: `pm` skill (spec drafting + plan drafting), `documenter` skill (amendment depth).

Default to **typical** depth, not minimum-viable. Use the checklists below. Hold a section back only with an explicit one-line reason in the artifact itself — *"No persistence, so no schema section"* — rather than omitting it silently. **Visible cuts beat invisible ones:** a reader can evaluate a stated omission and cannot evaluate one they never see.

The failure this prevents is subtle. A thin spec looks finished. Nothing about it announces that the error-handling table or the integration section was skipped, so the gap surfaces at build time as an ambiguity the implementer has to resolve under pressure — or worse, guesses at.

## Spec section checklist (typical)

- **Problem** — what need this addresses; what changes for the user.
- **Scope** — In *and* Out, both explicit.
- **Domains touched** — new vs existing; expected folder layout.
- **Data model** — entities, fields, types, constraints; storage schema if persisted.
- **Tool / API / user-flow contract** — what the caller (LLM, HTTP client, end user) sees, including **both** success and failure shapes.
- **Error handling** — a table per case: where the error surfaces and what happens. Degenerate inputs called out explicitly.
- **Clean Architecture layout** — file by file, with dependency direction stated.
- **Integration / wiring** — how the layers compose at runtime, where config flows in, how the feature plugs into existing entry points.
- **Testing strategy** — per layer: real values vs fakes vs mocks, and what each layer actually exercises.
- **Risks / known trade-offs** — concurrency, performance at scale, temporary couplings, deferred follow-ups.
- **Acceptance criteria** — checkable, and covering the edge cases the spec itself describes.
- **Open questions** — anything not yet decided.

## Plan section checklist (typical)

- **Approach** — TDD throughout; dependency order; test runner, linter, and type-checker identified by name.
- **Conventions and constraints** — the load-bearing section, and the one most often missing:
  - **Repo conventions** — observed from existing files, each with `file:line` evidence.
  - **Project-firsts** — patterns this work introduces for the first time, with the choice justified.
  - **Framework constraints** — researched from framework internals wherever behaviour actually depends on them.
- **Step order** — every step carries: files (new) and (modified); **type signatures for the tester** (authoritative — the tester infers nothing from elsewhere); the test list; **conventions applied** (which specific repo or framework pattern this step follows); why this order; SOLID / Clean Arch notes.
- **Acceptance mapping** — spec criteria → the plan step(s) that satisfy them.
- **Out-of-plan changes that may surface** — anything you anticipate needing that sits outside the spec's strict scope.

## When minimum-viable is correct

- A literal one-line code change — a typo, a single-line bug fix.
- A refactor with no user-visible behaviour change **and** contained to one module.
- Work that is really just doc updates.

Everything else — refactors spanning modules, bug fixes crossing layer boundaries, any new functionality — defaults to typical.

## Exemplars

The best exemplars are **this project's own merged specs and plans**, under `docs/specs/` and `docs/plans/`. Real-shape beats illustrative: they show the depth this codebase actually needs, in its vocabulary.

One caution when copying a merged artifact's shape: check its amendment blockquotes first (`> **Amendment …`). An artifact that looks thinner than the checklist above may have been **scope-cut** during the build rather than authored thin — and copying the outcome of a cut as if it were a template propagates the cut into work that never agreed to it.
