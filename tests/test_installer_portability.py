#!/usr/bin/env python3
r"""Guard: the installer runs on a machine that is not the author's.

Three defects shipped in 0.13.0 and were found by a first-time user on
Windows, not by this suite:

  1. `python3` was invoked as a literal in four places. A python.org Windows
     install provides `python.exe` and `py.exe` and never `python3.exe`, so
     the installer died immediately on a standard Windows setup with a
     misleading "install from the Microsoft Store" message. Not a PATH
     problem -- the binary does not exist under that name on that
     distribution channel.

  2. Python's text-mode stdout translates "\n" -> "\r\n" on Windows, so
     `install_lib.py plan` emitted CRLF. install.sh's classification loop
     (`while IFS= read -r line`) does not strip the trailing "\r", so every
     parsed path carried one and every installed file landed with a literal
     carriage return in its name -- `build.md` written as `build.md\r`, a
     different file.

  3. A third defect hid the second. `mark_hook_exec` ran

         [[ -f "$hook" ]] && chmod +x "$hook"

     as a bare statement, and that AND-list is the function's last command,
     so its status becomes the function's return status. `set -e` exempts a
     failing command inside an AND-list, but it does not exempt the *call*
     to a function that returns non-zero -- so the missing (because
     CR-corrupted) hook killed the script with exit 1 and no output at all.
     The same trap fires for any future missing-file case, not just this one.

Why the existing suite could not have caught any of the three, even if it had
been run on Windows -- which is the property that makes this a separate file
rather than three more cases in `test_install_plan.py`:

  - `test_install_plan.py` reads `install_lib.py` output through
    `subprocess.run(..., text=True)`, and universal-newlines mode rewrites
    "\r\n" to "\n" before any assertion sees it. **A CRLF producer is
    invisible to a text-mode consumer.** `TestLineEndings` therefore reads
    raw bytes, and builds its own CRLF producer so the bash-side strip is
    tested on every platform rather than only on Windows.
  - Its only install.sh invocation is `--dry-run`, which returns at line 463,
    long before `mark_hook_exec` is reached at line 520. `TestSetETraps` and
    `TestEndToEndInstall` run the installer for real.

Stdlib only, matching the rest of the suite.

Run:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _platform import find_bash  # noqa: E402  (path set above)

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK = REPO_ROOT / "pack"
LIB = REPO_ROOT / "install_lib.py"
INSTALL = REPO_ROOT / "install.sh"
VERSION_FILE = REPO_ROOT / "VERSION"

BASH = find_bash()
HAVE_BASH = BASH is not None
needs_bash = unittest.skipUnless(HAVE_BASH, "install.sh requires bash (Git Bash on Windows)")


def git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, check=False)


def make_target(tmp: Path) -> Path:
    """A realistic install target: an initialized repo with a mainline commit."""
    target = tmp / "target"
    target.mkdir(parents=True, exist_ok=True)
    git("init", "-q", cwd=target)
    git("config", "user.email", "t@t", cwd=target)
    git("config", "user.name", "t", cwd=target)
    (target / "f.txt").write_text("x")
    git("add", "-A", cwd=target)
    git("commit", "-qm", "init", cwd=target)
    git("branch", "-M", "main", cwd=target)
    return target


def run_install(root: Path, target: Path, *flags: str) -> subprocess.CompletedProcess:
    """Run an installer tree's install.sh against a target. Returns BYTES output.

    Bytes, not text: the CRLF defect is erased by universal-newlines decoding.
    """
    return subprocess.run(
        [BASH, str(root / "install.sh"), str(target),
         "--project-name", "p", "--description", "d", *flags],
        capture_output=True, check=False, stdin=subprocess.DEVNULL,
    )


def sandbox_installer(tmp: Path) -> Path:
    """A standalone copy of the installer tree, so its pieces can be swapped."""
    root = tmp / "root"
    root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(INSTALL, root / "install.sh")
    shutil.copy2(LIB, root / "install_lib.py")
    shutil.copy2(VERSION_FILE, root / "VERSION")
    shutil.copytree(PACK, root / "pack")
    return root


class TestInterpreterResolution(unittest.TestCase):
    """The interpreter is resolved once, not assumed to be named `python3`."""

    def test_no_bare_python3_invocation(self):
        offenders = []
        for n, line in enumerate(INSTALL.read_text().splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            # `echo` lines are diagnostics that *name* the interpreters tried;
            # they never invoke one. Everything else that mentions python3
            # outside quotes is running it. (The lookbehind lets the quoted
            # candidate list `for _cand in "python3" ...` through for the same
            # reason: a command name is never quoted in this script.)
            if stripped.startswith("echo "):
                continue
            if re.search(r'(?<![\w"$/-])python3\b', line):
                offenders.append(f"{n}: {line.strip()}")
        self.assertEqual(
            offenders, [],
            "install.sh must invoke the resolved interpreter, not a literal "
            "`python3` -- a python.org Windows install has no python3.exe:\n"
            + "\n".join(offenders),
        )

    @needs_bash
    def test_reports_a_clear_error_when_no_interpreter_exists(self):
        """The failure mode must name the real problem, not die obscurely."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            root = sandbox_installer(tmp)
            target = make_target(tmp)
            # A PATH carrying every ordinary tool but no Python under any
            # name -- the python.org-Windows condition, portably.
            bindir = tmp / "no-python-bin"
            bindir.mkdir()
            # Unprivileged Windows cannot symlink. Without it the shim PATH
            # would be empty, install.sh would die on a missing `tr`, and this
            # would read as an interpreter-resolution failure that it is not.
            try:
                os.symlink(VERSION_FILE, bindir / ".symlink-probe")
                (bindir / ".symlink-probe").unlink()
            except OSError:
                self.skipTest("symlinks unavailable; cannot build a shim PATH")
            seen: set[str] = set()
            for d in os.environ.get("PATH", "").split(os.pathsep):
                if not d or not Path(d).is_dir():
                    continue
                for entry in Path(d).iterdir():
                    name = entry.name
                    if name in seen or name.startswith(("python", "py")):
                        continue
                    seen.add(name)
                    try:
                        os.symlink(entry, bindir / name)
                    except OSError:
                        pass
            env = dict(os.environ, PATH=str(bindir))
            proc = subprocess.run(
                # Absolute path: the stripped PATH must not hide bash from
                # the harness, only Python from the installer.
                [BASH, str(root / "install.sh"), str(target),
                 "--project-name", "p", "--description", "d", "--dry-run"],
                capture_output=True, check=False, stdin=subprocess.DEVNULL, env=env,
            )
            combined = (proc.stdout + proc.stderr).decode("utf-8", "replace").lower()
            self.assertNotEqual(proc.returncode, 0, "should not claim success")
            # Not merely "the word python appears" -- bash's own
            # `python3: command not found` satisfies that while telling a
            # Windows user to install something they already have.
            self.assertNotIn(
                "command not found", combined,
                "the installer died on an unresolved command rather than "
                f"diagnosing the missing interpreter: {combined[:400]!r}")
            self.assertIn(
                "no python interpreter found", combined,
                "the error must name the real dependency and what was tried, "
                f"got: {combined[:400]!r}")


class TestLineEndings(unittest.TestCase):
    r"""CRLF must not reach a filename. Tested from both sides."""

    def test_interpreted_sources_are_lf_in_the_working_tree(self):
        r"""A CRLF checkout breaks the script before it can defend itself.

        Git for Windows defaults to core.autocrlf=true, so without the
        `.gitattributes` `eol=lf` rules a Windows clone rewrites install.sh
        in the working tree and bash dies on `$'\r': command not found` at
        line 1 — upstream of every fix in this file. Fails on a mis-checked-out
        clone, which is the only place it can fail.
        """
        for path in (INSTALL, LIB, PACK / "hooks" / "doc-drift-detector.py"):
            with self.subTest(path=path.name):
                self.assertNotIn(
                    b"\r\n", path.read_bytes(),
                    f"{path.name} has CRLF in the working tree; bash and the "
                    "hook runner treat the CR as content",
                )

    def test_lib_plan_stdout_is_lf_only(self):
        """Producer side: install_lib.py must not emit CR on any platform.

        Tautological on POSIX and load-bearing on Windows, which is exactly
        why CI runs the suite on both.
        """
        with tempfile.TemporaryDirectory() as td:
            target = Path(td).resolve()
            manifest = target / ".claude" / ".devkit-manifest.json"
            proc = subprocess.run(
                [sys.executable, str(LIB), "plan", str(PACK), str(target),
                 str(manifest), "9.9.9"],
                capture_output=True, check=True,
            )
        self.assertNotIn(b"\r", proc.stdout,
                         "install_lib.py plan emitted CR; install.sh parses this "
                         "output into filenames")

    @needs_bash
    def test_installer_strips_cr_from_plan_payloads(self):
        r"""Consumer side: install.sh must tolerate a CRLF plan.

        Reproduces the Windows condition on any platform by swapping in a
        stub `install_lib.py` that emits CRLF deliberately. Without the strip
        in the classification loop, the echoed paths carry the CR through to
        stdout -- and, in a real run, into the filenames themselves.
        """
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            root = sandbox_installer(tmp)
            (root / "install_lib.py").write_text(
                "import sys\n"
                "cmd = sys.argv[1] if len(sys.argv) > 1 else ''\n"
                "if cmd == 'plan':\n"
                "    sys.stdout.buffer.write(\n"
                "        b'NEW .claude/commands/build.md\\r\\n'\n"
                "        b'NEW .claude/commands/plan.md\\r\\n')\n"
                "sys.exit(0 if cmd == 'plan' else 1)\n"
            )
            target = make_target(tmp)
            proc = run_install(root, target, "--dry-run")
        self.assertNotIn(
            b"\r", proc.stdout,
            "install.sh carried a CR out of the plan loop; on Windows this "
            "becomes a literal carriage return in every installed filename",
        )
        self.assertIn(b"build.md", proc.stdout, "the stub plan should still classify")


class TestSetETraps(unittest.TestCase):
    """A missing optional file must not kill the script silently."""

    @needs_bash
    def test_install_completes_when_hook_file_absent(self):
        """`mark_hook_exec` must not return non-zero when there is no hook.

        The hook is deleted from the pack, so nothing installs it and the
        chmod target is legitimately absent -- the same state the CRLF bug
        produced. Pre-fix this exits 1 with no diagnostic.
        """
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()
            root = sandbox_installer(tmp)
            (root / "pack" / "hooks" / "doc-drift-detector.py").unlink()
            target = make_target(tmp)
            proc = run_install(root, target)
        self.assertEqual(
            proc.returncode, 0,
            "installer aborted when the hook was absent.\n"
            f"stdout: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
            f"stderr: {proc.stderr.decode('utf-8', 'replace')[-800:]}",
        )


class TestEndToEndInstall(unittest.TestCase):
    """A real, non-dry-run install. Nothing in the suite covered this before."""

    def setUp(self) -> None:
        if not HAVE_BASH:
            self.skipTest("install.sh requires bash")
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(self._tmp.name).resolve()
        self.target = make_target(tmp)
        self.proc = run_install(REPO_ROOT, self.target)

    def test_exits_clean(self):
        self.assertEqual(
            self.proc.returncode, 0,
            f"stdout: {self.proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
            f"stderr: {self.proc.stderr.decode('utf-8', 'replace')[-800:]}",
        )

    def test_no_installed_path_contains_a_control_character(self):
        """The assertion the Windows run needed and nothing was making."""
        installed = list((self.target / ".claude").rglob("*"))
        # Without this, a failed install leaves nothing to scan and the guard
        # passes vacuously — which is exactly what happened on the first
        # Windows CI run, where it was the only green test in its class.
        self.assertTrue(
            installed, "nothing was installed, so this guard proved nothing")
        bad = [str(p) for p in installed if any(ord(ch) < 32 for ch in p.name)]
        self.assertEqual(bad, [], f"installed paths carry control characters: {bad}")

    def test_manifest_is_well_formed(self):
        manifest = self.target / ".claude" / ".devkit-manifest.json"
        self.assertTrue(manifest.is_file(), "no manifest written")
        data = json.loads(manifest.read_text())
        self.assertIn("tracked", data)
        self.assertTrue(data["tracked"], "manifest records no files")

    def test_hook_is_installed_and_executable(self):
        hook = self.target / ".claude" / "hooks" / "doc-drift-detector.py"
        self.assertTrue(hook.is_file(), "hook not installed")
        if os.name != "nt":  # Windows has no POSIX exec bit
            self.assertTrue(hook.stat().st_mode & stat.S_IXUSR,
                            "hook is not executable")


if __name__ == "__main__":
    unittest.main(verbosity=2)
