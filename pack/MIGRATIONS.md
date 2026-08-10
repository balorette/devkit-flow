# Migrations

Structural changes to **seeded** files — the ones the pack stamps once at install and you own thereafter: `.claude/state.md` and your `CLAUDE.md`. The installer never rewrites them, so changes to their shape arrive here instead of being applied over your edits.

Every file the manifest tracks (`.claude/.devkit-manifest.json`) updates automatically — you do not need this file for those. Anything under `.claude/` that the manifest does not list is **yours**, and the pack neither updates it nor expects you to migrate it.

## How to apply

1. Check your installed version: `cat .claude/.devkit-version`.
2. Apply the sections **newer** than that version, oldest first.
3. Each entry is a proposal, not a patch. Read your live file and place the change where it belongs *in your copy* — the pack does not assume your header is in the shipped order, and your own additions stay.

A Claude Code session can do this for you: ask it to apply the pending entries. It will propose the edits before writing, like every other durable-doc change in the pack.

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
