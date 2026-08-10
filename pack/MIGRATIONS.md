# Migrations

Structural changes to **seeded** files — the ones the pack stamps once at install and you own thereafter: `.claude/state.md` and your `CLAUDE.md`. The installer never rewrites them, so changes to their shape arrive here instead of being applied over your edits.

Every file the manifest tracks (`.claude/.devkit-manifest.json`) updates automatically — you do not need this file for those. Anything under `.claude/` that the manifest does not list is **yours**, and the pack neither updates it nor expects you to migrate it.

## How to apply

1. Check your installed version: `cat .claude/.devkit-version`.
2. Apply the sections **newer** than that version, oldest first.
3. Each entry is a proposal, not a patch. Read your live file and place the change where it belongs *in your copy* — the pack does not assume your header is in the shipped order, and your own additions stay.

A Claude Code session can do this for you: ask it to apply the pending entries. It will propose the edits before writing, like every other durable-doc change in the pack.

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
