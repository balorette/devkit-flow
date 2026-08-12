# ADR registry — discovery and allocation

Used by: `pm` skill (brainstorm and plan-time architect invocations), `architect` subagent (via the paths its caller passes), `/feature-start` (Phase A discovery, Phase E allocation), `/plan` (architect-drafted ADRs), `/adopt` (adoption ADRs).

A project's architecture decisions live wherever that project put them. `docs/adr/` is the pack's default **for a project that has none** — it is never the assumption. This file is the single copy of how to find the registry and how to take the next number in it.

A fixed list of known locations would only ever find the layouts its author thought of. The first brownfield target kept twelve ADRs as headings inside a **single decisions log** under a docs subdirectory no such list would have contained.

## Discover

### Scope

`*.md` under `docs/`, plus root-level `*.md`, **plus any location `CLAUDE.md` conventions record for decisions** — scanned even when it falls outside those two. Never `.git/`, `node_modules/`, `vendor/`, or anything matched by `.gitignore`.

The recorded location has to be in scope, or the record is unreadable. § *Never cache the number* says the location may be recorded while the number may not be trusted — but a scan that cannot reach `architecture/decisions/`, `.github/decisions/`, or wherever else a project keeps them reports "none found" for a project that told the pack exactly where to look. Callers then pass `registry: none found` to the architect, § *Allocate*'s recorded high-water mark is unreachable, and the pack creates a second registry: the duplicate-ID failure step 3 forbids, reintroduced by the scan that exists to prevent it.

### Match, two patterns

- **In file contents:** `ADR[-_ ]?0*\d+`, case-insensitive.
- **In filenames:** `^0*\d{1,4}[-_]` under any directory whose name suggests decision records (`adr`, `adrs`, `decisions`, `rfc`, `rfcs`) — **excluding date-prefixed names** matching `^\d{4}-\d{2}-\d{2}`, which are dated notes rather than ADR numbers and would otherwise set a high-water mark in the thousands.

The filename pattern is not optional. A project using the pack's own `docs/adr/0012-name.md` convention need never write the string "ADR" inside the file, so a contents-only scan finds nothing and allocates `0001` over an existing registry.

### Rank definitions above mentions

A **definition** is a heading (`## ADR-012: …`) or a filename (`0012-*.md`). A **mention** is inline prose — a summary citing `ADR-007`, a changelog line. Take the high-water mark from definitions when any exist; mentions are a lower-confidence fallback and must be reported as such.

### Report what was found

Location, format (directory-of-files vs single-file log), highest number, and whether it came from definitions or mentions. **A bare number is not something the user can check.**

## Allocate

1. **Re-scan first.** See *Never cache the number* below.
2. **Take floor + 1.**
3. **Ask before relocating.** If the registry sits outside `docs/adr/`, or definitions appear in more than one location, ask: continue numbering in place, or start `docs/adr/` above the high-water mark. **Never silently allocate `0001` when any registry exists** — a duplicate ADR number means two documents claim the same decision ID, and the `architect` starts blind to every prior decision it might contradict.
4. **Write in that registry's format**, not the pack's. A project keeping a single decisions log gets a new heading in that log, not a new directory beside it. Create `docs/adr/` only when discovery found nothing anywhere.
5. **Update the recorded high-water mark** in `CLAUDE.md` conventions to the number just written, so the record stays a useful hint rather than decaying into a wrong one.

## Never cache the number

**The location may be recorded. The number may not be trusted.**

`/adopt` records the high-water mark once; features allocate continuously. With adoption at `12`, feature one takes `13`, and feature two reading the same recorded `12` takes `13` again — duplicate decision IDs in the normal documented flow, not just the brownfield case discovery was built for. `/plan` allocating from a mark `/feature-start` already consumed is the same collision one command over.

Re-scan the registry for the current highest number **every time you allocate**. Step 5 above keeps the record from decaying, but the re-scan is the authority regardless.

## Where the location is recorded

`CLAUDE.md` conventions, written by `/adopt`. A project that has never run `/adopt` has no record — run *Discover* in full rather than falling back to `docs/adr/`.
