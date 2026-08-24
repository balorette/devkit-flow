#!/usr/bin/env python3
"""Guard: every file in `pack/references/` is named in the lists that enumerate them.

Two documents promise a reader the complete set of references: README.md's
components table and this repo's CLAUDE.md. Both are hand-maintained, both are
updated by whoever adds a reference, and nothing checked that they kept up.

They had fallen four behind -- `adr-registry.md`, `artifact-locations.md`, and
`evidence-and-uncertainty.md` shipped without ever being added, so a reader
consulting either list saw six of the nine references and had no way to know.

That is this slice's own subject: a record that keeps asserting something after
it stopped being true. A list nobody verifies decays silently, and the failure is
invisible precisely because the list still looks complete.

Stdlib only, matching the pack's no-dependency posture.

Run:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

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

    def test_the_guard_can_see_the_references(self):
        """A glob that returns nothing would make the test above vacuously pass."""
        self.assertGreaterEqual(len(reference_names()), 5)


if __name__ == "__main__":
    unittest.main()
