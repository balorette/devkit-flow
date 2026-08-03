#!/usr/bin/env python3
"""Tests for the installer's update-plan classification and mainline detection.

Both defects these cover were found by asking "how do I update an existing
install?" against a real target, not by reading the code — and both failed
*silently*, which is the property that makes them worth a test rather than a
fix. A plan reading `skip 15` looks exactly like a routine update of a
customized install; a mainline recorded as a feature branch looks like nothing
at all until a merge targets the wrong place.

Stdlib only, matching the rest of the suite.

Run:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK = REPO_ROOT / "pack"
LIB = REPO_ROOT / "install_lib.py"
INSTALL = REPO_ROOT / "install.sh"


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                          text=True, check=False).stdout.strip()


def plan(target: Path, manifest: Path) -> dict[str, list[str]]:
    """Run `install_lib.py plan` and bucket its verbs."""
    out = subprocess.run(
        [sys.executable, str(LIB), "plan", str(PACK), str(target), str(manifest), "9.9.9"],
        capture_output=True, text=True, check=True).stdout
    buckets: dict[str, list[str]] = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        verb, _, payload = line.partition(" ")
        buckets.setdefault(verb, []).append(payload)
    return buckets


def seed_installed_files(target: Path, n: int = 3) -> list[str]:
    """Copy a few real pack files in, then modify them so they differ from the pack."""
    rels = []
    for src in sorted((PACK / "commands").glob("*.md"))[:n]:
        rel = f".claude/commands/{src.name}"
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text() + "\n<!-- older pack version -->\n")
        rels.append(rel)
    return rels


class TestNoManifestIsUnmanaged(unittest.TestCase):
    """A target with pack files but no manifest must not be reported as customized."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.target = Path(self._tmp.name).resolve()
        self.manifest = self.target / ".claude" / ".devkit-manifest.json"
        self.rels = seed_installed_files(self.target)

    def test_no_manifest_yields_unmanaged_not_skip(self):
        b = plan(self.target, self.manifest)
        self.assertEqual(sorted(b.get("UNMANAGED", [])), sorted(self.rels),
                         "differing files must be UNMANAGED when no manifest exists")
        for rel in self.rels:
            self.assertNotIn(rel, b.get("SKIP", []),
                             "SKIP asserts the user customized it — unprovable without a manifest")

    def test_new_files_still_install_without_a_manifest(self):
        """The unclassifiable ones must not block files that plainly don't exist yet."""
        b = plan(self.target, self.manifest)
        self.assertTrue(b.get("NEW"), "files absent from the target are still NEW")
        self.assertFalse(set(b.get("NEW", [])) & set(self.rels))

    def test_manifest_present_and_matching_yields_update(self):
        """The control: with a manifest recording what we installed, it's a clean UPDATE."""
        import hashlib
        tracked = {}
        for rel in self.rels:
            h = hashlib.sha256((self.target / rel).read_bytes()).hexdigest()
            tracked[rel] = h
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        self.manifest.write_text(json.dumps({"version": "0.0.1", "tracked": tracked, "templates": {}}))
        b = plan(self.target, self.manifest)
        self.assertEqual(sorted(b.get("UPDATE", [])), sorted(self.rels))
        self.assertNotIn("UNMANAGED", b)

    def test_manifest_present_but_file_modified_yields_skip(self):
        """The other control: a manifest that disagrees with the file IS evidence of customization."""
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        self.manifest.write_text(json.dumps(
            {"version": "0.0.1", "tracked": {rel: "0" * 64 for rel in self.rels}, "templates": {}}))
        b = plan(self.target, self.manifest)
        self.assertEqual(sorted(b.get("SKIP", [])), sorted(self.rels))
        self.assertNotIn("UNMANAGED", b)


class TestMainlineDetection(unittest.TestCase):
    """`--mainline` must not default to whatever branch happens to be checked out."""

    def _repo(self) -> Path:
        d = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(d)], check=False))
        git("init", "-q", cwd=d)
        git("config", "user.email", "t@t", cwd=d)
        git("config", "user.name", "t", cwd=d)
        (d / "f.txt").write_text("x")
        git("add", "-A", cwd=d)
        git("commit", "-qm", "init", cwd=d)
        git("branch", "-M", "main", cwd=d)
        return d

    def _detected_mainline(self, repo: Path) -> str:
        out = subprocess.run(
            ["bash", str(INSTALL), str(repo), "--dry-run",
             "--project-name", "p", "--description", "d"],
            capture_output=True, text=True, check=False, stdin=subprocess.DEVNULL).stdout
        for line in out.splitlines():
            if "Mainline" in line:
                return line.split(":", 1)[1].strip()
        return ""

    def test_prefers_main_over_checked_out_feature_branch(self):
        repo = self._repo()
        git("checkout", "-qb", "feature/some-work", cwd=repo)
        self.assertEqual(self._detected_mainline(repo), "main",
                         "installing from a feature branch must not record it as mainline")

    def test_uses_main_when_on_main(self):
        self.assertEqual(self._detected_mainline(self._repo()), "main")

    def test_master_is_found_when_there_is_no_main(self):
        repo = self._repo()
        git("branch", "-M", "master", cwd=repo)
        git("checkout", "-qb", "wip", cwd=repo)
        self.assertEqual(self._detected_mainline(repo), "master")

    def test_explicit_flag_wins(self):
        repo = self._repo()
        git("checkout", "-qb", "feature/x", cwd=repo)
        out = subprocess.run(
            ["bash", str(INSTALL), str(repo), "--dry-run", "--mainline", "trunk",
             "--project-name", "p", "--description", "d"],
            capture_output=True, text=True, check=False, stdin=subprocess.DEVNULL).stdout
        self.assertIn("trunk", [l.split(":", 1)[1].strip() for l in out.splitlines() if "Mainline" in l])


if __name__ == "__main__":
    unittest.main(verbosity=2)
