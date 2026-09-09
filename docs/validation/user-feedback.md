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
