# Migrations

Structural changes to **seeded** files — the ones the pack stamps once at install and you own thereafter: `.claude/state.md` and your `CLAUDE.md`. The installer never rewrites them, so changes to their shape arrive here instead of being applied over your edits.

Files the manifest tracks (`.claude/.devkit-manifest.json`) are pack-tracked, not seeded — you do not need this file for those. A tracked file updates on a normal `install.sh` run unless you've edited it yourself, in which case the installer reports `SKIP` and leaves your edit alone (`--force` overwrites it, backing up your version first). Anything under `.claude/` that the manifest does not list is **yours**, and the pack neither updates it nor expects you to migrate it.

## How to apply

1. Check your installed version: `cat .claude/.devkit-version`.
2. Apply the sections **newer** than that version, oldest first.
3. Each entry is a proposal, not a patch. Read your live file and place the change where it belongs *in your copy* — the pack does not assume your header is in the shipped order, and your own additions stay.

A Claude Code session can do this for you: ask it to apply the pending entries. It will propose the edits before writing, like every other durable-doc change in the pack.

## How entries are written

Each entry **names the template hunk it corresponds to** and replaces the **smallest anchored unit** that carries the change — a sentence or a field line, not a whole paragraph.

The asymmetry is the reason. An entry that says too much is merely redundant. An entry that says too little **silently deletes**: "replace paragraph X" is destructive when your paragraph X grew a sentence the replacement omits, and neither you nor the pack will notice, because the result is a well-formed paragraph that simply says less than it did. That is not hypothetical — 0.11.0's `Open questions` entry replaced a paragraph and dropped a sentence the template still keeps.

Naming the hunk closes the other half. `tests/test_migrations_snapshot.py` guarantees a changed template is *looked at*; nothing guarantees every hunk in that diff reaches an entry, and the 0.10.0 section is what that gap produces — two things changed and the entry documented one. An entry that names its hunk lets the snapshot diff and the migration list be cross-checked by reading rather than by recollection.

---

## 0.12.0

### `.claude/state.md`

- **Template hunk:** the `Active feature` line in the trailing HTML comment's field-meanings block. One line, replaced.

  Replace this **single line**:

  ```
  Active feature  short slug matching docs/specs/<slug>.md, or "none"
  ```

  with:

  ```
  Active feature  short slug identifying the feature, or "none". The slug does
                  NOT determine the spec path -- artifact files carry a date
                  prefix (YYYY-MM-DD-<slug>.md) and live wherever discovery
                  found. Read Spec / Plan below for actual paths.
  ```

  Leave every other line in that block alone.

  Without this, your `state.md` tells a model it can rebuild the spec path from the slug. 0.12.0 made that false **deliberately**: specs, plans, and summaries now carry a date prefix and live wherever `.claude/references/artifact-locations.md` discovers, so that discovery is load-bearing rather than merely recommended. A model that reconstructs `docs/specs/<slug>.md` from the field meaning will look in the wrong place, or write to a directory that belongs to another system.

- **Template hunk:** the `Summary:` field in the header block, and its entry in the field-meanings block. Both new; nothing is replaced.

  Add a `**Summary:** —` line to the header, directly after `**Plan:** —`:

  ```
  **Summary:** —
  ```

  **Then backfill it, if a summary already exists on disk.** `—` is the right value only when no summary has been written yet. If your active feature has already been through `/feature-merge` — the `in-review` case, which is exactly the state an upgrade is most likely to interrupt — find the file in your summaries directory and record its real path instead. A pre-0.12.0 summary is at `<summaries-dir>/<slug>.md` with no date prefix; keep that name, per *Existing artifacts are not renamed* below.

  Seeding the field blank and walking away is a hard stop, not a cosmetic gap: `/pr-review` stage 2 halts when the field is `—`, because a summary it cannot locate is one it must not silently duplicate. That halt is correct for a feature whose summary was never written and wrong for a feature whose summary is sitting in the tree — and the second is the path a dogfood traverses.

  And add its meaning to the field-meanings block, directly after the `Spec / Plan` entry:

  ```
  Summary         path to the feature summary once /feature-merge writes
                  it, or "—". Recorded because the filename carries a
                  creation date a later invocation cannot compute --
                  /pr-review amends this file days later. Cleared at
                  closeout with the rest.
  ```

  Without it, `/pr-review` cannot locate the summary it is required to amend: discovery returns the summary *directory*, and the dated filename belongs to the invocation that created it.

**Existing artifacts are not renamed.** Files already at `docs/specs/<slug>.md` keep their names and keep working — `state.md`'s `Spec:` and `Plan:` fields already hold real paths, and every consumer now reads them. The date prefix applies to artifacts created from 0.12.0 onward.

---

## 0.11.0

### `.claude/state.md`

- **In the trailing HTML comment**, replace the `Open questions` paragraph with the two-paragraph version below. *(This change shipped in 0.10.0 and was omitted from that entry — apply it now regardless of whether you already applied 0.10.0.)*

  ```
  The Open questions section captures things deferred mid-feature that need
  the user's input. /checkpoint reads and helps resolve these.

  During Phase: in-review it holds review findings accepted for THIS
  feature and not yet fixed. It is cleared at /feature-merge, so anything
  deferred PAST this feature must go to the findings ledger instead --
  /pr-review routes cross-feature deferrals there as REV rows. Parking a
  durable finding here discards it at merge.
  ```

  Without it your `state.md` tells a model that accepted-but-unfixed review findings live in `## Open questions` — a section `/feature-merge` clears — directly contradicting `/pr-review`, which routes cross-feature deferrals to the findings ledger as `REV` rows.

- **In the trailing HTML comment**, replace the `Gated baseline` field meaning with:

  ```
  Gated baseline  the last commit whose CONTENT passed gates 1-3 -- the tip
                  before the state.md-only transition commit, set when the PR
                  opens and after every successful gate rerun. /feature-merge
                  diffs it against the PR tip, excluding this file, to decide
                  whether a rerun needs the gates. Excluding it is required:
                  writing this field commits it, so a plain SHA comparison
                  would never match. Comparing local vs remote tips cannot
                  work either -- /pr-review pushes its fixes and makes them
                  agree.
  ```

  The field's shape is unchanged; its **meaning** is. In 0.10.0 it held the SHA the gates ran against, and `/feature-merge` compared it to the PR tip for equality — which could never match, because writing the field commits it. 0.11.0 stores the tip before that commit and compares by content diff excluding `state.md`. No edit to your header is needed; this keeps the file's own documentation true.

---

## 0.10.0

### `.claude/state.md`

- **Add `**Gated baseline:** —`** immediately after the `**PR:**` line.

  Records the last commit SHA that passed gates 1–3. `/feature-merge` compares it against the PR tip to decide whether a rerun needs to re-run the gates.

  Without it the command compares your local tip against the remote tip — and `/pr-review` pushes its fixes, which makes those agree while carrying commits no gate has seen. A rerun then takes the "nothing changed" path and skips tests, docs reconciliation, and security review on exactly the code that is about to merge.

- **In the trailing HTML comment**, add `Gated baseline` to the field-meanings list, so the file keeps explaining itself:

  ```
  Gated baseline  the last commit SHA that passed gates 1-3. Set when the PR
                  opens and after every successful gate rerun.
  ```

---

## 0.9.0

### `.claude/state.md`

Installs stamped at 0.9.0 or later already have both of these — skip this section unless you are coming from an earlier version.

- **Add `**PR:** —`** after the `**Plan:**` line. Holds the PR URL (or `owner/repo#N`) while a feature is in review.
- **Add `in-review`** to the `Phase` enum in the field-meanings comment. The feature lifecycle no longer ends at a local merge: in a PR flow the feature stays active while review happens, possibly across days and sessions.
