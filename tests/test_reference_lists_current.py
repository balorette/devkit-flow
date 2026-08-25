#!/usr/bin/env python3
"""Guard: the lists that enumerate `pack/references/` name every file in it, and nothing else.

Two documents promise a reader the complete set of references: README.md's
components table and this repo's CLAUDE.md. Both are hand-maintained, both are
updated by whoever adds a reference, and nothing checked that they kept up.

They had fallen four behind -- `adr-registry.md`, `artifact-locations.md`, and
`evidence-and-uncertainty.md` shipped without ever being added, so a reader
consulting either list saw six of the ten references and had no way to know.

The reverse decays the same way: a reference that is deleted or renamed stays
advertised, and a list naming a file that no longer exists sends a reader looking
for it. Both directions are checked, because the first version of this guard
checked only one -- reading is structurally poor at absence, which is this
round's own finding turned on its own guard.

That is this slice's own subject: a record that keeps asserting something after
it stopped being true. A list nobody verifies decays silently, and the failure is
invisible precisely because the list still looks complete.

Stdlib only, matching the pack's no-dependency posture.

Run:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCES = REPO_ROOT / "pack" / "references"

# Each enumerates the full reference set for a reader. The marker locates the one
# line that promises completeness -- checking the whole document instead lets an
# incidental mention elsewhere mask a stale list, which is how the first version of
# this guard passed CLAUDE.md while three references were missing from its list.
ENUMERATING_LINES = (
    (REPO_ROOT / "README.md", "| **References** ("),
    (REPO_ROOT / "CLAUDE.md", "- **References:**"),
)


def reference_names() -> list[str]:
    return sorted(p.name for p in REFERENCES.glob("*.md"))


# A reference is named in backticks, bare or with its directory. Anything else the
# line mentions -- `pack/references/` itself, a test path -- is not a claim about
# the set, so it must not read as one.
LISTED_NAME = re.compile(r"`(?:pack/references/)?([A-Za-z0-9._-]+\.md)`")


def listed_names(line: str) -> list[str]:
    return sorted(set(LISTED_NAME.findall(line)))


def enumerating_line(path: Path, marker: str) -> str:
    """The single line that claims to list every reference. Absent = failure."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith(marker):
            return line
    return ""


class TestReferenceListsCurrent(unittest.TestCase):
    def test_every_reference_is_listed(self):
        missing = []
        for doc, marker in ENUMERATING_LINES:
            line = enumerating_line(doc, marker)
            if not line:
                missing.append(f"{doc.relative_to(REPO_ROOT)} :: no line starting {marker!r}")
                continue
            for name in reference_names():
                if name not in line:
                    missing.append(f"{doc.relative_to(REPO_ROOT)} :: {name}")
        self.assertEqual(
            [],
            missing,
            "References exist but are absent from a list that enumerates them:\n  "
            + "\n  ".join(missing),
        )

    def test_no_list_names_a_reference_that_is_gone(self):
        """Deleting or renaming a reference must not leave it advertised."""
        actual = set(reference_names())
        stale = []
        for doc, marker in ENUMERATING_LINES:
            line = enumerating_line(doc, marker)
            if not line:
                stale.append(f"{doc.relative_to(REPO_ROOT)} :: no line starting {marker!r}")
                continue
            for name in listed_names(line):
                if name not in actual:
                    stale.append(f"{doc.relative_to(REPO_ROOT)} :: {name}")
        self.assertEqual(
            [],
            stale,
            "A list names a reference that does not exist in pack/references/:\n  "
            + "\n  ".join(stale),
        )

    def test_the_guard_can_read_a_list(self):
        """A regex that matches nothing would make the test above vacuously pass."""
        for doc, marker in ENUMERATING_LINES:
            with self.subTest(doc=doc.name):
                self.assertGreaterEqual(len(listed_names(enumerating_line(doc, marker))), 5)

    def test_the_guard_can_see_the_references(self):
        """A glob that returns nothing would make the test above vacuously pass."""
        self.assertGreaterEqual(len(reference_names()), 5)


if __name__ == "__main__":
    unittest.main()
