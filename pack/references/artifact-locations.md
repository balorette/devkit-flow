# Artifact locations

Where this project's specs, plans, and summaries live, and how to find out rather than assume.

`adr-registry.md` is the same procedure for ADRs, which additionally have allocation semantics — floor-plus-one, re-scan before allocate. This file covers the three artifacts that have locations but no IDs. Cite it; do not restate it.

## Why this exists

A hardcoded `docs/plans/` is wrong in a way that does not error.

On the first brownfield target, `docs/plans/` existed and held the project's *retired* plans, while its live ones sat under a different directory that its `CLAUDE.md` named explicitly. Writing to the default would have passed every precondition, satisfied every later step, and left the project with devkit plans in the tree it had deliberately migrated away from. Nothing errors. The plan lands beside legacy artifacts, `state.md` points at it, `/build` follows the pointer and works fine, and the project now has two vocabularies where it had closed one.

The precondition that missed it asked whether a *file* existed. The question that catches it is whether the *directory* belongs to someone else.

Note the asymmetry that made it findable: specs were fine on that project, because `docs/specs/` did not exist and spec-as-contract was a genuinely new concept there. Plans are not new. **The collision risk scales with how ordinary the artifact's name is**, which is why the common names are the ones that need discovery most.

## Resolve

**Run this, not its parts.** Once per invocation, before the first consumer, and independently **per artifact type** — a project commonly has plans and no specs.

**Per artifact type means every step, not just the first.** A caller resolves the types it is going to write and leaves the rest alone, so a half-filled record is the expected input to this section rather than a broken one. Each type walks all three steps on its own: one type being already recorded says nothing about the others, and an exit taken for one must never be taken on behalf of another.

1. **§ *Discover*.**
2. **Act on what it returned**, per artifact type:
   - `"none found"` → **§ *Default***. Take the default path; no confirmation is needed for an unoccupied namespace.
   - a directory holding files the pack wrote → it is the pack's; use it.
   - a directory holding files the pack did not write → **§ *Confirm***. Ask. Do not resolve it by picking.
3. **§ *Record* the outcome, for every type this invocation resolved** — including when the outcome was a default. Skip a type step 1 found already recorded: that is a recorded resolution already, and rewriting it is how a settled answer gets re-litigated. Skipping the *record* for one type never skips the *chain* for another.

**A caller that runs only § *Discover* has resolved nothing.** It holds a reading, not a decision. An occupied foreign directory has been *identified* and never *asked about* — so the pack writes into it, which is the harm above. A derived default has been *chosen* and never *persisted* — so the next invocation derives it again, and a later move of the directory reads as drift rather than as a decision.

**A caller that runs the chain for one type and lets it exit for all of them has resolved nothing either**, and it is the harder case to see: something ran, a location came back, and the type that came back is genuinely settled. It is the *other* types that hold a reading — or hold nothing at all, while a write site cites them as though they were answered. Report per type; exit per type.

That failure is not hypothetical and not visible in review: every write site here cites *the location this section returned*, and a citation resolves whether or not anything ran. **Cite this section; run this section.** If you are naming § *Discover* at a write site, you are naming the scan and not the answer.

## Discover

Run as step 1 of § *Resolve*, once per invocation, **before the first consumer**. Running it alone is not resolution — see § *Resolve*.

1. **Read `CLAUDE.md` conventions first — and read it per artifact type.** Every type the record names is authoritative: use it, and § *Resolve* is finished for that type. Any of `/adopt`, `/feature-start`, `/plan`, or `/feature-merge` may have written it; which one did is irrelevant, and re-deriving what one of them settled is wasted motion that risks contradicting it.

   **Types the record does not name are not settled. Carry them into step 2.** A record naming specs and not plans is the ordinary state rather than a malformed one: only `/adopt` resolves all three at once, and the feature commands each resolve the types they write, so a project accumulates this record one type at a time. Treating any record as a whole-scan exit is the failure this step is written to avoid — it returns a settled answer for specs, no answer at all for plans, and never reaches § *Confirm* for the occupied `docs/plans/` that is the likeliest collision in this pack.
2. **Otherwise scan** for existing artifact directories: `docs/specs/`, `docs/plans/`, `docs/summaries/`, and any directory under `docs/` or the repo root whose name contains `spec`, `plan`, `summary`, or `design`.
3. **Rank by provenance, not by name.** A directory holding files the pack wrote is the pack's. A directory holding files it did not is the project's, whatever it happens to be called.

Report exactly one of: a path per artifact type, or an explicit `"none found"`. **Silence is not a result** — a consumer cannot distinguish "no directory exists" from "discovery never ran," and those call for opposite behavior.

Discovery is **per artifact type**, not all-or-nothing. A project commonly has plans and no specs; report each independently.

## Default, when nothing is found

`"none found"` is an **answer**, not a dead end. On a greenfield project — the common case, not the edge case — use:

| Artifact | Default |
|---|---|
| Specs | `docs/specs/` |
| Plans | `docs/plans/` |
| Summaries | `docs/summaries/` |

Create the directory on first write. **No confirmation is needed for a default into an unoccupied namespace** — there is nothing to collide with, and asking would put friction on the ordinary path. § *Confirm* exists for the *occupied* case, which is a different question with a different answer.

Record the choice per § *Record* anyway, even when it is the default. A recorded default is what stops the next invocation re-deriving it, and it is what makes a later move read as a decision rather than as drift.

## Confirm

**An occupied namespace is a user decision, not a default.**

When discovery finds a directory that exists and holds files the pack did not write, surface it and ask before writing anything. Offer the three real options:

- write alongside the existing files,
- write to a different path,
- adopt the existing convention as the pack's.

Do not resolve it by picking. The cost of guessing wrong is two vocabularies in one repo, which is expensive to unwind and invisible until someone notices — and the same class of decision at install time (the `state.md` collision) is already resolved by asking rather than by default.

## Record

Record the resolved locations in `CLAUDE.md` conventions so the next invocation reads instead of re-deriving. This is the treatment the ADR registry already gets, for the same reason.

**Every branch of § *Resolve* step 2 lands here** — a confirmed occupied directory, a directory recognized as the pack's own, and a default taken into an empty namespace. The default is the branch most easily skipped and the one that most needs recording: nobody was asked, so nothing feels decided, and an unrecorded default is re-derived by every later invocation until one of them derives differently.

**Record names the types you resolved and claims nothing about the others.** Write the entry so a later reader can tell a type that was settled from a type that was never asked — an entry that reads as a complete answer to a partial question is worse than no entry, because § *Discover* step 1 treats what it names as authoritative. The types you leave out are the ones the next command is expected to resolve and record.

**The location may be recorded. The path may not be reconstructed.** See § *Name*.

## Name

Specs, plans, and summaries are named:

```
<discovered-dir>/YYYY-MM-DD-<slug>.md
```

The date is the artifact's **creation** date and does not change when the artifact is amended — a spec drafted on the 10th and amended on the 20th keeps the 10th. The directory carries the type, so no type suffix is added.

**The date prefix is why every consumer must read the path rather than build it.** A slug alone is no longer sufficient to reconstruct a filename, and that is deliberate: a path that *can* be derived *will* be derived, and derivation is what put artifacts in the wrong directory in the first place. Read the path from `.claude/state.md`'s `Spec:` / `Plan:` / `Summary:` fields, or from this discovery — never assemble it from a slug.

**Write the path into `state.md` the moment the artifact is created.** The date in the filename is the *creation* date, which belongs to the invocation that created it — a later invocation cannot compute it, and `/pr-review` amends the summary in a session that may be days after `/feature-merge` wrote it. All three fields exist for this reason; a discovered *directory* is not enough to find a dated *file*.

Two artifacts are deliberately excluded:

- **Domain docs** (`docs/domains/<domain>.md`) are not dated. A domain doc is per-domain and long-lived, amended at every merge; a creation date on it would assert something false.
- **ADRs** are not dated. They carry a monotonic ID, and `adr-registry.md` owns their discovery — a date would compete with the registry rather than complement it.
