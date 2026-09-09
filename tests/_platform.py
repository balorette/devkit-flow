#!/usr/bin/env python3
r"""Platform helpers shared by the installer test suites.

Not named `test_*`, so `unittest discover` does not collect it.

The one thing here exists because `subprocess.run(["bash", ...])` does not
mean what it looks like on Windows. `C:\Windows\System32\bash.exe` ships with
Windows and is the **WSL launcher**, not a shell -- on a machine with no
distro installed it prints

    Windows Subsystem for Linux has no installed distributions.

in UTF-16 and exits 1. `shutil.which("bash")` finds it first, so every test
that shells out to install.sh failed on the first Windows CI run, including
four in `test_install_plan.py` that long predate that run.

Git Bash is the shell install.sh is actually documented to run under, so
resolve to it explicitly rather than trusting PATH order.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def find_bash() -> str | None:
    """Absolute path to a real bash, or None. Never the WSL launcher."""
    if os.name != "nt":
        return shutil.which("bash")

    candidates: list[Path] = []

    # Derive from git, which is the most reliable marker of where Git for
    # Windows landed: <root>\cmd\git.exe -> <root>\bin\bash.exe.
    git = shutil.which("git")
    if git:
        candidates.append(Path(git).parent.parent / "bin" / "bash.exe")

    candidates += [
        Path(r"C:\Program Files\Git\bin\bash.exe"),
        Path(r"C:\Program Files (x86)\Git\bin\bash.exe"),
    ]

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)

    # Last resort: PATH, but only if it is not the System32 WSL shim.
    found = shutil.which("bash")
    if found and "system32" not in found.lower():
        return found
    return None
