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


def migrations_has_section(version: str) -> bool:
    pattern = re.compile(rf"^##\s+{re.escape(version)}\s*$", re.MULTILINE)
    return bool(pattern.search(MIGRATIONS.read_text(encoding="utf-8")))


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
        changed = [
            name
            for name in template_names()
            if (HISTORY / prev / name).read_bytes() != (HISTORY / version / name).read_bytes()
        ]
        if not changed:
            return
        self.assertTrue(
            migrations_has_section(version),
            f"Templates changed between {prev} and {version} ({', '.join(changed)}) "
            f"but pack/MIGRATIONS.md has no `## {version}` section. Seeded files are "
            f"never rewritten by the installer, so a change with no entry ships to "
            f"nobody.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
