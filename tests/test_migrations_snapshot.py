#!/usr/bin/env python3
"""Guard: a seeded template cannot change without its diff being surfaced.

Finding 1 of the PR #139 review: `state.md.template`'s Open-questions prose
changed in 0.10.0, and the 0.10.0 MIGRATIONS entry documented only the
`Gated baseline` field. The installer never rewrites seeded files, so every
upgrader who followed MIGRATIONS.md exactly ended up with a `state.md` whose
own documentation contradicts `/pr-review`.

No test can verify an entry is semantically *complete* — that is precisely
what failed, since a 0.10.0 section existed and was missing one of two
changes. What this guarantees is narrower and sufficient: editing a template
turns the suite red until the author re-snapshots, and re-snapshotting is the
moment the old->new diff is in front of them.

  SNAPSHOT-CURRENT   pack/templates/history/<VERSION>/ exists and byte-matches
                     every live template.

  MIGRATION-PRESENT  If <VERSION>'s snapshot differs from the previous
                     version's, MIGRATIONS.md carries a `## <VERSION>` section.
                     This is the test ADR-0007:128 proposed, made computable by
                     the snapshots -- this repo has no tags and VERSION was
                     bumped mid-slice at a11733e, so "diff between releases"
                     was not otherwise derivable.

`pack/templates/history/` is a development-tree artifact: TRACKED_DIRS does not
include it, so it is never installed and has no manifest disposition.

Stdlib only, matching the pack's own no-dependency posture.

Run:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK = REPO_ROOT / "pack"
HISTORY = PACK / "templates" / "history"
MIGRATIONS = PACK / "MIGRATIONS.md"

sys.path.insert(0, str(REPO_ROOT))
import install_lib  # noqa: E402  (path set above)


def current_version() -> str:
    return (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()


def version_key(name: str) -> tuple[int, ...]:
    """Numeric ordering. A string sort puts 0.9.0 above 0.10.0, which would
    silently pick the wrong baseline for the diff."""
    return tuple(int(part) for part in name.split("."))


def snapshot_versions() -> list[str]:
    if not HISTORY.is_dir():
        return []
    return sorted((d.name for d in HISTORY.iterdir() if d.is_dir()), key=version_key)


def previous_version(version: str) -> str | None:
    earlier = [v for v in snapshot_versions() if version_key(v) < version_key(version)]
    return earlier[-1] if earlier else None


def template_names() -> list[str]:
    """Asked of install_lib rather than hardcoded, so adding a seeded template
    extends this guard automatically."""
    return [pack_rel for pack_rel, _ in install_lib.TEMPLATE_FILES]


def migrations_has_section_in(migrations_path: Path, version: str) -> bool:
    pattern = re.compile(rf"^##\s+{re.escape(version)}\s*$", re.MULTILINE)
    return bool(pattern.search(migrations_path.read_text(encoding="utf-8")))


def migrations_has_section(version: str) -> bool:
    return migrations_has_section_in(MIGRATIONS, version)


def snapshot_file_names(history_dir: Path, version: str) -> set[str]:
    snap_dir = history_dir / version
    if not snap_dir.is_dir():
        return set()
    return {p.name for p in snap_dir.iterdir() if p.is_file()}


def changed_template_names(history_dir: Path, prev: str, version: str) -> list[str]:
    """Names whose bytes differ between two snapshots.

    Iterates the UNION of both snapshots' filenames, not `template_names()`
    (the *current* TEMPLATE_FILES). A template dropped from TEMPLATE_FILES
    between `prev` and `version` still has a file in the `prev` snapshot and
    none in the `version` one -- that disappearance must register as a change
    even though the name is no longer in the live list, or a same-version
    removal-only release would take the "nothing changed" early return while
    existing installs still carry the formerly-seeded file.
    """
    names = snapshot_file_names(history_dir, prev) | snapshot_file_names(history_dir, version)
    changed = []
    for name in sorted(names):
        prev_path = history_dir / prev / name
        cur_path = history_dir / version / name
        prev_bytes = prev_path.read_bytes() if prev_path.is_file() else None
        cur_bytes = cur_path.read_bytes() if cur_path.is_file() else None
        if prev_bytes != cur_bytes:
            changed.append(name)
    return changed


class TestVersionHelpers(unittest.TestCase):
    """The helpers, on known inputs — so a green run means something."""

    def test_version_key_orders_numerically_not_lexically(self):
        self.assertLess(version_key("0.9.0"), version_key("0.10.0"))
        self.assertLess(version_key("0.10.0"), version_key("0.11.0"))

    def test_template_names_is_not_empty(self):
        """A bug returning [] would make SNAPSHOT-CURRENT vacuously pass."""
        self.assertGreaterEqual(len(template_names()), 2)

    def test_migrations_has_section_matches_a_real_heading(self):
        self.assertTrue(migrations_has_section("0.10.0"))

    def test_migrations_has_section_rejects_a_missing_one(self):
        self.assertFalse(migrations_has_section("99.0.0"))

    def test_migrations_has_section_does_not_match_a_substring(self):
        """`## 0.10.0` must not satisfy a query for `0.1`."""
        self.assertFalse(migrations_has_section("0.1"))


class TestSnapshotCurrent(unittest.TestCase):
    def test_snapshot_dir_exists_for_current_version(self):
        version = current_version()
        self.assertTrue(
            (HISTORY / version).is_dir(),
            f"No snapshot for VERSION {version}. Create "
            f"pack/templates/history/{version}/ by copying every file in "
            f"{template_names()} from pack/.",
        )

    def test_every_template_matches_its_snapshot(self):
        version = current_version()
        for name in template_names():
            with self.subTest(template=name):
                live = (PACK / name).read_bytes()
                snap_path = HISTORY / version / name
                self.assertTrue(snap_path.is_file(), f"Missing snapshot: {snap_path}")
                self.assertEqual(
                    live,
                    snap_path.read_bytes(),
                    f"\n\npack/{name} differs from its {version} snapshot.\n"
                    f"This is the guard working. Do this, in order:\n"
                    f"  1. diff pack/templates/history/{version}/{name} pack/{name}\n"
                    f"  2. Account for EVERY hunk in pack/MIGRATIONS.md under the\n"
                    f"     version that will ship it.\n"
                    f"  3. Re-snapshot: cp pack/{name} "
                    f"pack/templates/history/<shipping-version>/{name}\n",
                )

    def test_snapshot_has_no_files_that_are_not_templates(self):
        """A renamed template would otherwise leave a stale snapshot behind,
        and a stale baseline produces a wrong diff — worse than no baseline."""
        version = current_version()
        snap_dir = HISTORY / version
        if not snap_dir.is_dir():
            self.skipTest("covered by test_snapshot_dir_exists_for_current_version")
        extra = {p.name for p in snap_dir.iterdir() if p.is_file()} - set(template_names())
        self.assertEqual(extra, set(), f"Stale files in {snap_dir}: {sorted(extra)}")


class TestMigrationPresent(unittest.TestCase):
    def test_changed_template_has_a_migration_section(self):
        version = current_version()
        prev = previous_version(version)
        if prev is None:
            self.skipTest(f"{version} is the earliest snapshot; no baseline to diff")
        changed = changed_template_names(HISTORY, prev, version)
        if not changed:
            return
        self.assertTrue(
            migrations_has_section(version),
            f"Templates changed between {prev} and {version} ({', '.join(changed)}) "
            f"but pack/MIGRATIONS.md has no `## {version}` section. Seeded files are "
            f"never rewritten by the installer, so a change with no entry ships to "
            f"nobody.",
        )


class TestChangedTemplateNamesCoversRemovals(unittest.TestCase):
    """Regression for the finding that `changed_template_names` (formerly
    inlined against `template_names()`, i.e. the *current* TEMPLATE_FILES)
    missed a template removed between two versions: the name is gone from the
    current list, so a removal-only diff was invisible to the old
    iteration. Exercised against temporary snapshot dirs -- never the real
    pack/templates/history/ -- per this file's own no-mutation posture.
    """

    def test_template_removed_since_prev_version_counts_as_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            history = Path(tmp) / "history"
            (history / "0.1.0").mkdir(parents=True)
            (history / "0.2.0").mkdir(parents=True)
            (history / "0.1.0" / "kept.template").write_bytes(b"same in both")
            (history / "0.2.0" / "kept.template").write_bytes(b"same in both")
            (history / "0.1.0" / "removed.template").write_bytes(b"present only in 0.1.0")
            # 0.2.0 has no removed.template: simulates a template dropped from
            # TEMPLATE_FILES between releases.

            changed = changed_template_names(history, "0.1.0", "0.2.0")

            self.assertIn("removed.template", changed)
            self.assertNotIn("kept.template", changed)

    def test_template_added_since_prev_version_counts_as_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            history = Path(tmp) / "history"
            (history / "0.1.0").mkdir(parents=True)
            (history / "0.2.0").mkdir(parents=True)
            (history / "0.2.0" / "added.template").write_bytes(b"present only in 0.2.0")

            changed = changed_template_names(history, "0.1.0", "0.2.0")

            self.assertIn("added.template", changed)

    def test_a_removal_with_no_migration_section_fails_the_real_assertion(self):
        """End-to-end shape of the guard: a removal is detected AND, when
        MIGRATIONS.md lacks the corresponding section, the assertion this
        test file makes in `test_changed_template_has_a_migration_section`
        would fail. Checked directly against isolated files so this test
        does not depend on the repo's real version history lining up."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            history = tmp_path / "history"
            (history / "0.1.0").mkdir(parents=True)
            (history / "0.2.0").mkdir(parents=True)
            (history / "0.1.0" / "removed.template").write_bytes(b"gone in 0.2.0")

            migrations = tmp_path / "MIGRATIONS.md"
            migrations.write_text("# Migrations\n\n## 0.1.0\n\nInitial.\n", encoding="utf-8")

            changed = changed_template_names(history, "0.1.0", "0.2.0")
            self.assertTrue(changed, "removal should register as a change")
            self.assertFalse(
                migrations_has_section_in(migrations, "0.2.0"),
                "fixture MIGRATIONS.md deliberately has no 0.2.0 section",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
