#!/usr/bin/env python3
"""Guard: every path an installed pack file cites must resolve inside a target.

The first brownfield install shipped four live citations to documents that exist
only in the devkit repo — one of them normative. A model in an installed project
following `pm/SKILL.md:349` to "the source of truth for depth" found no such file.

Nothing checked for this, so nothing caught it. This is that check.

Citations fall into three classes:

  PACK-INSTALLED   `.claude/references/solid-checklist.md`
                   Must be something the installer actually installs. Verified by
                   asking `install_lib.iter_tracked_pack_files` rather than by
                   hardcoding the layout, so the guard survives TRACKED_DIRS changes.

  RUNTIME-TARGET   `docs/specs/<slug>.md`, `.claude/state.md`
                   Created by the workflow in the target project. Legitimately
                   absent from the pack; allowlisted.

  DEVKIT-ONLY      `docs/design/0002-brownfield-adoption.md`
                   Exists in this repo and nowhere else. Forbidden in any file
                   the installer copies. This is the defect class.

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

sys.path.insert(0, str(REPO_ROOT))
import install_lib  # noqa: E402  (path set above)

# Directories whose files get copied into a target and read by a model there.
SCANNED_DIRS = ("skills", "agents", "commands", "references")

# Paths the workflow creates in the target project. Absent from the pack by design.
RUNTIME_TARGET_PREFIXES = (
    "docs/specs/",
    "docs/plans/",
    "docs/adr/",
    "docs/domains/",
    "docs/summaries/",
    "docs/findings.md",
    "docs/reviews/",
    ".claude/state.md",
    ".claude/settings.json",
    ".claude/.devkit-config.json",
    ".claude/.devkit-manifest.json",
    ".claude/.devkit-version",
    ".claude/MIGRATIONS.md",
)

# Backtick-quoted tokens that look like repo-relative paths.
CITATION = re.compile(r"`(\.claude/[A-Za-z0-9._/-]+|docs/[A-Za-z0-9._/-]+)`")

# Directories that exist only in the devkit authoring repo. A reference to one of
# these is dangling whether or not it is backtick-quoted — `adopt.md:92` cited
# "docs/design/0002" in bare prose and slipped past a quoted-only scan.
DEVKIT_ONLY_DIRS = ("docs/design/", "docs/authoring-notes/", "docs/validation/")
BARE_DEVKIT_PATH = re.compile(
    r"(?<![`\w/])((?:" + "|".join(re.escape(d) for d in DEVKIT_ONLY_DIRS) + r")[A-Za-z0-9._/-]*)"
)

PACK_INSTALLED, RUNTIME_TARGET, DEVKIT_ONLY = "pack-installed", "runtime-target", "devkit-only"


def installed_target_paths() -> set[str]:
    """Target-relative paths the installer actually writes. Asked, not assumed."""
    return {target_rel for _, target_rel in install_lib.iter_tracked_pack_files(PACK)}


def classify(token: str, installed: set[str]) -> str:
    token = token.rstrip(".,);:")
    if any(token == p or token.startswith(p) for p in RUNTIME_TARGET_PREFIXES):
        return RUNTIME_TARGET
    if token in installed:
        return PACK_INSTALLED
    return DEVKIT_ONLY


def scan() -> list[tuple[Path, int, str]]:
    """Return (path, line_no, token) for every forbidden citation."""
    installed = installed_target_paths()
    violations: list[tuple[Path, int, str]] = []
    for top in SCANNED_DIRS:
        for path in sorted((PACK / top).rglob("*.md")):
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                seen: set[str] = set()
                for token in CITATION.findall(line):
                    if classify(token, installed) == DEVKIT_ONLY:
                        seen.add(token)
                # Bare (unquoted) references to authoring-repo-only directories.
                seen.update(BARE_DEVKIT_PATH.findall(line))
                for token in sorted(seen):
                    violations.append((path.relative_to(REPO_ROOT), line_no, token))
    return violations


class TestClassifier(unittest.TestCase):
    """The classifier itself, on known inputs — so a green scan means something."""

    def setUp(self) -> None:
        self.installed = installed_target_paths()

    def test_devkit_only_path_is_forbidden(self):
        self.assertEqual(
            classify("docs/design/0002-brownfield-adoption.md", self.installed), DEVKIT_ONLY
        )
        self.assertEqual(
            classify("docs/authoring-notes/spec-and-plan-depth.md", self.installed), DEVKIT_ONLY
        )

    def test_installed_reference_resolves(self):
        self.assertEqual(
            classify(".claude/references/solid-checklist.md", self.installed), PACK_INSTALLED
        )
        self.assertEqual(
            classify(".claude/references/spec-and-plan-depth.md", self.installed), PACK_INSTALLED
        )

    def test_runtime_target_paths_are_allowed(self):
        for token in ("docs/specs/foo.md", "docs/domains/notes.md", ".claude/state.md"):
            with self.subTest(token=token):
                self.assertEqual(classify(token, self.installed), RUNTIME_TARGET)

    def test_trailing_punctuation_is_stripped(self):
        self.assertEqual(classify(".claude/references/solid-checklist.md.", self.installed),
                         PACK_INSTALLED)

    def test_installed_set_is_not_empty(self):
        """A bug that returned {} would make every citation look devkit-only."""
        self.assertGreater(len(self.installed), 10)

    def test_bare_unquoted_devkit_path_is_caught(self):
        """`adopt.md:92` cited "docs/design/0002" in prose and evaded a quoted-only scan."""
        self.assertEqual(
            BARE_DEVKIT_PATH.findall("(see Decision 1 in docs/design/0002). Keep it short."),
            ["docs/design/0002"],
        )

    def test_backticked_paths_are_not_double_reported(self):
        """A quoted devkit path is reported once by CITATION, not again by the bare scan."""
        self.assertEqual(BARE_DEVKIT_PATH.findall("see `docs/design/0002.md` here"), [])


class TestNoDanglingReferences(unittest.TestCase):
    def test_no_installed_file_cites_a_devkit_only_path(self):
        violations = scan()
        if violations:
            detail = "\n".join(f"  {p}:{n} → `{t}`" for p, n, t in violations)
            self.fail(
                f"{len(violations)} citation(s) point at documents that exist only in the "
                f"devkit repo and are never installed:\n{detail}\n\n"
                "Fix by extracting the content into pack/references/ (and citing "
                "`.claude/references/…`), inlining the rule, or removing the citation."
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
