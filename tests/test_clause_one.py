"""Clause 1 of ADR-0009: an artifact and its carrier are written in the same step.

A phase that produces a durable artifact declares it with a `**Writes:**` line,
and the command containing that phase has a step that stages what was declared.

The exemption is declared in the file, not here. ADR-0008 requires a command
that falls outside clause 1 to say so in its own text; this test looks for that
statement rather than carrying a hardcoded allowlist, because an allowlist here
would be exactly the cached-discovery failure clause 3 forbids.
"""

import re
import unittest
from pathlib import Path

PACK = Path(__file__).resolve().parent.parent / "pack"

# A phase writes when it names a durable target AND acts on it. Either signal
# alone is noise: carrier phases quote artifact paths in order to stage them,
# and orient phases use write verbs about writes that happen later.
#
# Both lists are data. Revise them without redesigning the test.
# Stems, so writing/written/records/drafted all match one entry.
WRITE_VERBS = re.compile(
    r"\b(writ|record|append|amend|updat|appl|allocat|stamp|draft)",
    re.IGNORECASE,
)
DURABLE_TARGET = re.compile(
    r"`[^`]*\.md`|`\.claude/state\.md`|state\.md|CLAUDE\.md|findings ledger",
    re.IGNORECASE,
)

# `Step` is deliberately absent: no command uses `### Step` headings, and the
# skills use them for illustrative content that is not a phase at all.
PHASE_HEADING = re.compile(r"^#{2,4}\s+(Phase|Gate)\s+\S+.*$", re.MULTILINE)

# Clause 1 has two sides. A phase named for committing is the *carrier*, not the
# producer, so it quotes the artifacts it stages without producing them.
CARRIER_HEADING = re.compile(r"commit|hand off", re.IGNORECASE)

WRITES_LINE = re.compile(r"^\*\*Writes:\*\*\s+\S", re.MULTILINE)
EXCEPTION = "**Clause 1 exception:**"

# The carrier is looked for as a *heading*, not as prose containing "git add".
# Every command mentions `git add` — in a sentence forbidding `git add -A` —
# so a prose match passes for a document that has no carrier at all.
ANY_HEADING = re.compile(r"^#{2,4}\s+.*$", re.MULTILINE)


def pack_documents():
    """Every command and skill file, as (path, text) pairs."""
    yield from ((p, p.read_text()) for p in sorted(PACK.glob("commands/*.md")))
    yield from ((p, p.read_text()) for p in sorted(PACK.glob("skills/*/SKILL.md")))


def phase_sections(text):
    """Split a document into (heading, body) pairs, one per phase heading."""
    matches = list(PHASE_HEADING.finditer(text))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield match.group(0).strip(), text[match.end():end]


class TestClauseOne(unittest.TestCase):
    def test_write_phases_declare_writes(self):
        """A phase whose body describes a durable write declares it."""
        offenders = []
        for path, text in pack_documents():
            if EXCEPTION in text:
                continue
            for heading, body in phase_sections(text):
                if CARRIER_HEADING.search(heading):
                    continue
                if not (WRITE_VERBS.search(body) and DURABLE_TARGET.search(body)):
                    continue
                if not WRITES_LINE.search(body):
                    offenders.append(f"{path.relative_to(PACK.parent)} :: {heading}")
        self.assertEqual(
            [],
            offenders,
            "Phases describe a durable write with no `**Writes:**` declaration:\n  "
            + "\n  ".join(offenders),
        )

    def test_declared_writes_have_a_carrier(self):
        """A document that declares writes has a step that stages them."""
        offenders = []
        for path, text in pack_documents():
            if EXCEPTION in text:
                continue
            if not WRITES_LINE.search(text):
                continue
            headings = (m.group(0) for m in ANY_HEADING.finditer(text))
            if not any(CARRIER_HEADING.search(h) for h in headings):
                offenders.append(str(path.relative_to(PACK.parent)))
        self.assertEqual(
            [],
            offenders,
            "Documents declare `**Writes:**` with no staging step:\n  "
            + "\n  ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
