#!/usr/bin/env python3
"""Regression tests for pack/hooks/doc-drift-detector.py.

The hook is the only executable code the pack ships, and its failure mode is
*silent*: when it can't resolve a path it returns 0 with no output, which is
byte-for-byte identical to "no drift detected." That makes it exactly the kind
of component that regresses without anyone noticing, so it gets the repo's
first automated tests.

Tests drive the hook as a subprocess — stdin JSON in, stderr out, exit code
checked — because that is the real contract with the Claude Code harness.
Testing the internals would not have caught the path-anchoring defect these
tests were written for.

Stdlib only (no pytest), matching the hook's own no-dependency posture: the
pack installs into arbitrary projects and cannot assume a test runner.

Run:
    python3 -m unittest discover -s tests -v
    python3 tests/test_doc_drift_detector.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "pack" / "hooks" / "doc-drift-detector.py"

STATE_TEMPLATE = """# Project state

**Active feature:** {feature}
**Active branch:** main
**Phase:** building
**Spec:** {spec}
**Plan:** —
**PR:** —
**Next step:** Step 1
"""

SPEC_TEMPLATE = """---
feature: demo
status: approved
owned_files:
{globs}
---
# Demo spec
"""


def make_project(root: Path, *, feature: str = "demo", spec: str = "docs/specs/demo.md",
                 globs: tuple[str, ...] = ("src/**",), write_spec: bool = True) -> Path:
    """Build a minimal devkit-shaped project tree and return its root."""
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "specs").mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "other").mkdir(parents=True, exist_ok=True)

    (root / ".claude" / "state.md").write_text(
        STATE_TEMPLATE.format(feature=feature, spec=spec), encoding="utf-8"
    )
    if write_spec:
        (root / spec).write_text(
            SPEC_TEMPLATE.format(globs="\n".join(f"  - {g}" for g in globs)),
            encoding="utf-8",
        )
    (root / "src" / "in_scope.py").touch()
    (root / "other" / "out_of_scope.py").touch()
    return root


def run_hook(payload, cwd: Path) -> tuple[int, str]:
    """Invoke the hook the way the harness does. Returns (exit_code, stderr)."""
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=raw,
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    return proc.returncode, proc.stderr


def edit_payload(project: Path, file_path: str, tool: str = "Edit") -> dict:
    return {"tool_name": tool, "cwd": str(project), "tool_input": {"file_path": file_path}}


class DriftHookTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = make_project(Path(self._tmp.name).resolve())

    def assertWarns_(self, cwd: Path, file_path: str, msg: str = "") -> None:
        code, err = run_hook(edit_payload(self.project, file_path), cwd)
        self.assertEqual(code, 0, "hook must always exit 0")
        self.assertIn("devkit drift-detector", err, msg or f"expected a drift warning for {file_path!r}")

    def assertSilent_(self, cwd: Path, file_path: str, msg: str = "") -> None:
        code, err = run_hook(edit_payload(self.project, file_path), cwd)
        self.assertEqual(code, 0, "hook must always exit 0")
        self.assertEqual(err.strip(), "", msg or f"expected silence for {file_path!r}, got: {err!r}")


class TestPathAnchoring(DriftHookTestCase):
    """Regression tests for the payload-cwd anchoring defect (2026-08-03).

    The hook builds `project_root` from the payload's `cwd`, but previously
    resolved the edited path against the *hook process's* cwd. When the two
    differed, an out-of-scope edit either raised ValueError (silently swallowed)
    or resolved under a different subtree and matched the wrong glob.
    """

    def test_absolute_path_out_of_scope_warns(self):
        self.assertWarns_(self.project, str(self.project / "other" / "out_of_scope.py"))

    def test_relative_path_hook_cwd_matches_project_warns(self):
        self.assertWarns_(self.project, "other/out_of_scope.py")

    def test_relative_path_hook_cwd_outside_project_warns(self):
        """Regression: previously silent — resolve() anchored to the wrong root."""
        with tempfile.TemporaryDirectory() as elsewhere:
            self.assertWarns_(
                Path(elsewhere),
                "other/out_of_scope.py",
                "hook cwd outside the project must not suppress the warning",
            )

    def test_relative_path_hook_cwd_is_project_subdir_warns(self):
        """Regression: previously matched `src/**` via src/other/out_of_scope.py."""
        self.assertWarns_(
            self.project / "src",
            "other/out_of_scope.py",
            "hook cwd inside the project must not cause a wrong-glob match",
        )

    def test_relative_in_scope_stays_silent_from_foreign_cwd(self):
        """The fix must not introduce false positives."""
        with tempfile.TemporaryDirectory() as elsewhere:
            self.assertSilent_(Path(elsewhere), "src/in_scope.py")

    def test_absolute_in_scope_stays_silent(self):
        self.assertSilent_(self.project, str(self.project / "src" / "in_scope.py"))


class TestPreExistingBehaviour(DriftHookTestCase):
    """Guards for behaviour that already worked, so the fix can't regress it."""

    def test_excluded_prefix_is_silent(self):
        for path in ("docs/specs/demo.md", "CLAUDE.md", "README.md", ".claude/state.md",
                     "pyproject.toml", "package.json", "Cargo.toml", ".gitignore"):
            with self.subTest(path=path):
                self.assertSilent_(self.project, path)

    def test_non_edit_tool_is_ignored(self):
        code, err = run_hook(
            edit_payload(self.project, "other/out_of_scope.py", tool="Bash"), self.project
        )
        self.assertEqual((code, err.strip()), (0, ""))

    def test_no_active_feature_is_silent(self):
        make_project(self.project, feature="none")
        self.assertSilent_(self.project, "other/out_of_scope.py")

    def test_missing_spec_file_is_silent(self):
        # setUp already wrote the spec; remove it so state.md points at nothing.
        (self.project / "docs" / "specs" / "demo.md").unlink()
        self.assertSilent_(self.project, "other/out_of_scope.py")

    def test_spec_field_with_parenthetical_annotation_is_parsed(self):
        """state.md may read: `**Spec:** docs/specs/demo.md (approved; amended ...)`."""
        (self.project / ".claude" / "state.md").write_text(
            STATE_TEMPLATE.format(feature="demo", spec="docs/specs/demo.md (approved; amended 2026-01-01)"),
            encoding="utf-8",
        )
        self.assertWarns_(self.project, "other/out_of_scope.py")

    def test_path_outside_project_is_silent(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            outside = Path(elsewhere) / "stray.py"
            outside.touch()
            self.assertSilent_(self.project, str(outside))

    def test_malformed_json_exits_zero_silently(self):
        for raw in ("", "   ", "{not json", "[]"):
            with self.subTest(raw=raw):
                code, err = run_hook(raw, self.project)
                self.assertEqual(code, 0, "hook must never crash the harness")
                self.assertEqual(err.strip(), "")

    def test_glob_forms(self):
        """`**`, `*`, and exact paths all behave."""
        make_project(self.project, globs=("src/**", "lib/*.py", "tools/build.sh"))
        (self.project / "lib").mkdir(exist_ok=True)
        (self.project / "tools").mkdir(exist_ok=True)
        self.assertSilent_(self.project, "lib/thing.py")        # single * matches within segment
        self.assertWarns_(self.project, "lib/nested/thing.py")  # single * must not cross /
        self.assertSilent_(self.project, "tools/build.sh")      # exact path
        self.assertWarns_(self.project, "tools/other.sh")


if __name__ == "__main__":
    unittest.main(verbosity=2)
