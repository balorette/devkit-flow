# User Feedback

I had a friend try it out. They are not a software engineer but use Claude a lot to build below are the feedback docs drafted: 

## pt 1

devkit-flow feedback

Went through the repo and actually ran it end-to-end rather than just reading the code — overall take is that this is a genuinely well-engineered piece of tooling, not a quick hack. The design docs/ADRs explaining why each decision was made, the manifest-based update system that distinguishes "you customized this file" from "we can't tell," and the fresh-context adversarial subagents (tester/architect/security-reviewer) are all more careful than most Claude Code workflow packs I've seen. Found two real, concrete bugs along the way — both Windows-specific, both verified fixed with small patches.

Bug 1: missing python3 fallback.
install.sh hardcodes python3 in 4 places (lines 155, 202, 348, 538) with no fallback. A standard python.org Windows install only provides python.exe/py.exe, never python3.exe — so the installer dies immediately on a typical Windows machine with a confusing "install from Microsoft Store" message. Not a PATH issue; the binary genuinely doesn't exist under that name on that setup. Confirmed this is specifically about the distribution channel: installing Python via the Microsoft Store instead (which does register python3.exe) fixed it on my end.

Fix: resolve the interpreter once —
PY="$(command -v python3 || command -v python || command -v "py -3" || true)"
— and use $PY everywhere instead of the literal python3. Same fix needed for the test suite's python3 -m unittest discover.

Bug 2: CRLF corrupts every installed filename.
Once python3 was working, I ran the installer for real and it silently wrecked the install. Python's stdout on Windows translates \n → \r\n in text mode, so install_lib.py's plan subcommand emits CRLF line endings. install.sh's parsing loop (while IFS= read -r line; do ... done <<< "$PLAN") doesn't strip the trailing \r, so every file path it extracts carries one — every installed file lands with a literal carriage return in its name (e.g. build.md actually gets written as build.md\r, a different file). Confirmed with cat -A on the resulting .claude/ tree: every single file had a trailing ^M.

The script then dies with exit code 1 and zero error output, from an adjacent issue: mark_hook_exec runs
[[ -f "$hook" ]] && chmod +x "$hook"
as a bare statement. Under set -e, a false A, the whole statement'sfailing exit status kills the script — silently, since it's not inside an if. The hook "isn't found" because its real (corrupted) filename has the trailing \r.                             
Verified fix: one line at the bottom of install_lib.py:
if __name__ == "__main__":                                                                      sys.stdout.reconfigure(newline
    sys.exit(main(sys.argv))
Re-ran the full (non-dry-run) install after patching: clean exit 0, correct filenames, exec bi the hook, well-formed manifest,etected update mode (0.13.0 (update mode), all 29 files unchanged). One line fully resolves it.                                   
Bonus hardening note: the [[ -f x ]] && chmod +x x bare-statement pattern is a general set -e trap — any future missing-file case (not just this CRLF bug) will kill the script silently with no ssage. Worth wrapping as if [[ -$hook"; fi so a failure is at leastreadable.
                                                                                              her notes:
- No CI (.github/workflows absent). A real test suite exists but nothing runs it automatically — likely why both bugs above shipped unnoticed. Even a minimal GitHub Actions job running the existing tests on windows-lateste a real user hit them.
- The README already candidly flags "unverified on Windows" — this turns that from an open unknown into two specific, small, verified fixes.
- Design/workflow quality of the teview gates, "propose before write"discipline, doc-drift hook) is solid and clearly thought through for its target audience: disciplined feature-branch TDD work.

Bottom line: devkit-flow is two small, now-verified patches away from working cleanly on Windows.


## pt 2

devkit-flow feedback — dogfood run addendum

Beyond the installer bugs, I actually ran a tiny feature (unitconv c2f <value>, a Celsius→Fahrenheit CLI) through the entire workflow by hand — spec, plan, two TDD steps, and a three-gate merge — spawning real fresh-context agents for the tester, conformance-reviewer, and security-reviewer roles exactly as the commands describe. A few genuine findings from actually using it, not just reading it:

What worked impressively well:
- The plan's "Framework constraints" research step caught a real, non-obvious defect risk before any code was written: naively using argparse's type=float would have silently produced argparse's own error message instead of the spec's exact contracted string (error: 'abc' is not a number). The plan flagged this and chose manual parsing instead — this is exactly the kind of thing a fast implementer skips and nobody notices until later.
- All three fresh-context subagents genuinely added value in a real run, not just in theory: the conformance-reviewer correctly found zero contradictions and correctly recognized the argparse workaround as spec-serving rather than flagging it as a deviation; the security-reviewer was well-calibrated — it noted inf/nan parsing and unbounded input length as informational only, correctly declining to inflate severity given the spec's stated "local, single-user" threat model instead of reflexively flagging everything (a common failure mode in security-review prompts).

Two real process gaps found:
1. Fresh install leaves a dirty working tree, and /feature-start's own first precondition requires a clean one. install.sh doesn't commit its own output. A brand-new user who installs the pack and immediately runs /feature-start hits their own pack-install files as "uncommitted changes" on their very first command. Not documented anywhere — worth either having the installer offer to commit, or the README/orientation doc telling the user to commit .claude/ first.
2. A tester subagent's fresh-context finding can silently evaporate between steps. During Step 1, the tester correctly flagged (unprompted) that python -m unitconv had no confirmed entry point (unitconv/__main__.py). Nothing forced that finding to be tracked, and it fell through — Step 2's unit tests all called main() directly and never exercised the real python -m unitconv invocation, so they stayed green even though the feature's own literal acceptance-criteria example was broken. It only surfaced because Gate 2 happened to involve running the spec's literal example commands by hand rather than just trusting green tests. The mechanism worked, but only because the merge gate is thorough — there's no place between steps where a tester's inline finding gets carried forward the way cross-feature findings go to the findings ledger. Worth considering: should /build require re-checking prior steps' tester findings before closing out, or route them into state.md's Open Questions the same way /checkpoint does?

One design-taste observation, not a bug: for a genuinely tiny feature (2 source files, ~30 lines of real code), the full-depth workflow produced a ~100-line spec, ~90-line plan, 3 subagent calls, and 7 commits. The "minimum-viable" carve-out only covers literal one-liners and pure refactors, so anything with any new functionality — however small — gets the full typical-depth treatment. That's presumably the right default for real features, but worth asking your brother whether there's an intentionally smaller tier for trivial ones, or whether the assumption is that devkit users are always operating at a scale where that overhead pays for itself.

Bottom line: once the two Windows bugs are patched, the workflow doesn't just install — it actually works as designed, including the parts that are hardest to get right (fresh-context adversarial review). The one real gap found in a live run is small and specific enough to hand him directly.

---

## Disposition (2026-09-09)

Recorded after the review pass. Every claim above was checked against the code
before anything was changed; all four installer claims reproduced.

**A note on the source text.** Parts 1 and 2 above are transcribed as received
and are corrupted in several places — the bug-2 fix snippet breaks mid-line
(`sys.stdout.reconfigure(newline` with no argument), and there are chewed
fragments (`"a false A, the whole statement'sfailing exit status"`,
`"windows-lateste a real user hit them"`). Looks like a terminal-capture
artifact. The findings were reconstructable; a clean copy is still worth
requesting before this is cited as the record.

### Shipped in 0.13.1

| # | Finding | Fix |
|---|---|---|
| 1 | `python3` hard-coded at `install.sh:155, 202, 348, 538` | Interpreter resolved once, up front: `python3` → `python` → `py -3`, each probed for **>= 3.7** so an old Linux `python` (Python 2) is rejected with a clear message instead of an obscure `SyntaxError` later |
| 2 | CRLF from `install_lib.py` corrupts every installed filename | LF forced on the producer (`sys.stdout.reconfigure(newline="\n")`) **and** stripped on the consumer (`line="${line%$'\r'}"` in the plan loop, plus `INSTALLED_VERSION`, which drives mode selection) |
| 3 | `mark_hook_exec`'s bare `&&` kills the script silently | Wrapped in `if`. `set -e` exempts a failure *inside* an AND-list but not the *call* to a function that returns non-zero — verified both halves empirically |
| 4 | **New, found while building the CI:** no `.gitattributes` | `* text=auto eol=lf`. Git for Windows defaults to `core.autocrlf=true`, so a Windows clone rewrote `install.sh` itself and bash died at line 1 — upstream of all three fixes above |
| Gap 1 | Fresh install leaves a dirty tree; `/feature-start:21` requires a clean one | Closing message now names the commit, in update mode too. README says it as well |
| — | No CI | `.github/workflows/tests.yml` — Linux + Windows, py3.9 / py3.11 |

**Corrections to the proposed fixes**, both of which matter if applied verbatim:

- `command -v "py -3"` cannot work — `command -v` resolves a command *name*,
  not a name plus arguments, so that branch never fires.
- `sys.stdout.reconfigure(...)` alone is one-sided. It is the right primary
  fix and does cover all four call sites at once, but the bash loop is the
  consumer and a CR reaching it becomes a filename. Both sides are now fixed.

### The keeper

**A guard can be structurally blind to the defect it appears to cover.**

The obvious lesson — "no CI, so bugs shipped" — is true but not the sharp one.
The suite that existed *could not have caught any of these even if it had been
run on Windows*:

- `tests/test_install_plan.py` reads `install_lib.py` through
  `subprocess.run(..., text=True)`, and universal-newlines mode rewrites
  `\r\n` to `\n` before any assertion sees it. **A CRLF producer is invisible
  to a text-mode consumer.** Verified directly rather than assumed.
- Its only `install.sh` invocation is `--dry-run`, which returns roughly sixty
  lines before `mark_hook_exec` is ever reached.

So `tests/test_installer_portability.py` reads raw **bytes**, builds its own
CRLF producer via a stub `install_lib.py` so the bash-side strip is tested on
every platform rather than only on Windows, and runs the **first non-dry-run
install this suite has ever had**. All four guards were confirmed red against
the unfixed code first, and the static one was mutation-tested afterward.

This is a sibling of slice 15's *a guarantee that degrades does not announce
it*: the assurance a green suite advertises was never the assurance it
provided, and nothing said so.

### Deferred — the substantive half, not authored

Both are the round's real content, and both are clause-shaped rather than
point fixes:

1. **Triage has three routes and no receipt.** `engineer` Red routes a tester
   finding to fix-now / `/checkpoint` amendment / findings ledger, and nothing
   confirms it landed in any of them. The reported case — `python -m unitconv`
   having no entry point — was flagged unprompted, routed nowhere, and
   surfaced only because Gate 2 happened to run the spec's literal examples by
   hand rather than trusting green tests.
2. **Acceptance mapping maps a criterion to a *step*, not to a test that
   exercises it as written.** `pm/SKILL.md:303-320` was fully green while the
   feature's own literal acceptance example was broken, because the step's
   tests called `main()` directly. Strictly sharper than the slice-1 Finding 4
   it descends from: that was *no test*; this is *a test that does not
   exercise the criterion*.

Structurally these are ADR-0009 clause 4 and ADR-0010 clause 6 — an
observation with no forced landing spot, and a claim declared satisfied with
no verification pass.

### Noted, no change

The depth-tier observation is a legitimate design question, not a defect. The
minimum-viable carve-out (`pack/references/spec-and-plan-depth.md:35-41`) is
defined by *change shape* — one-liners, contained refactors, doc-only — so a
~30-line CLI drew the full typical-depth treatment. Whether a third tier
defined by *risk* belongs there is open. The current default is deliberate:
the pack's whole evidence base is that the cheap-looking step is where defects
hide. Unchanged pending a second opinion from real use.

### Recorded as working

Worth keeping, since a findings list is not the whole result — and this is the
first assessment by someone with no stake in the design:

- The plan's *Framework constraints* research step caught `argparse`'s
  `type=float` silently substituting its own error text for the spec's
  contracted string, **before any code was written**.
- `conformance-reviewer` read the resulting manual-parsing workaround as
  spec-serving rather than flagging it as a deviation.
- `security-reviewer` held `inf`/`nan` parsing and unbounded input length at
  informational, correctly declining to inflate severity against the spec's
  stated local-single-user threat model.
