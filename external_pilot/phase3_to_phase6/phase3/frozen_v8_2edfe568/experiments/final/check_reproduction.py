#!/usr/bin/env python3
"""
experiments/final/check_reproduction.py
=======================================
Checks that a re-run of the fast experiments reproduces the committed result.

Why this is not just `git diff --exit-code`
-------------------------------------------
Byte-exact reproduction holds only on the interpreter that produced the
artifact. The tracer reads `frame.f_locals` on every event; PEP 667 changed what
that returns in 3.13, and 3.12 inlined comprehensions so they no longer create a
call event. Re-running the regression corpus on 3.9 gives 125 trace events where
3.13 gives 95, which moves individual pair distances -- REG_09 goes from 0.097
to 0.399 -- without moving a single headline count.

So there are two questions, and they deserve two answers:

  strict     does the artifact come back byte for byte? Only meaningful on the
             interpreter that produced it, and CI runs it there.
  headline   do the reported counts come back? This must hold on every
             supported interpreter, and it is what any claim in the README
             depends on.

A headline mismatch is a reproduction failure. A strict mismatch on a different
interpreter is a version difference, and the tool says which it found.

Usage:
    python3 experiments/final/check_reproduction.py            # headline
    python3 experiments/final/check_reproduction.py --strict   # byte-exact too
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any, Dict, List, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ARTIFACTS = REPO_ROOT / "artifacts" / "final"

# Free-text provenance strings that are allowed to differ under --strict. The
# committed HARD_NEGATIVE artifact predates commit d9d6380, which reworded this
# string in the generator (the old wording claimed a derivation that no artifact
# supports; see docs/current/THRESHOLD_PROVENANCE.md). The artifact was frozen
# and is deliberately not regenerated. Only lines containing one of these JSON
# keys may differ; every other byte must match, so any numeric or structural
# change still fails.
STRICT_IGNORED_KEYS = {
    "HARD_NEGATIVE_V5_RESULTS.json": ('"threshold_provenance"',),
}


def strict_differences(artifact: str, old: bytes, new: bytes) -> Tuple[List[int], List[int]]:
    """Return (disallowed differing line numbers, allowed differing line numbers)."""
    if old == new:
        return [], []
    old_lines, new_lines = old.split(b"\n"), new.split(b"\n")
    if len(old_lines) != len(new_lines):
        return [-1], []
    keys = tuple(k.encode() for k in STRICT_IGNORED_KEYS.get(artifact, ()))
    bad: List[int] = []
    ok: List[int] = []
    for i, (a, b) in enumerate(zip(old_lines, new_lines), start=1):
        if a == b:
            continue
        (ok if keys and any(k in a for k in keys) and any(k in b for k in keys) else bad).append(i)
    return bad, ok


# (artifact, generator, [(label, dotted path into the JSON)])
EXPERIMENTS: List[Tuple[str, str, List[Tuple[str, str]]]] = [
    (
        "HARD_NEGATIVE_V5_RESULTS.json",
        "experiments/final/hard_negative_evaluation.py",
        [
            ("hard negatives, canonical, SBG V5 TP",
             "regimes.canonical.metrics.sbg_v5_output_free.tp"),
            ("hard negatives, canonical, SBG V5 TN",
             "regimes.canonical.metrics.sbg_v5_output_free.tn"),
            ("hard negatives, declared, SBG V5 TP",
             "regimes.declared.metrics.sbg_v5_output_free.tp"),
            ("hard negatives, declared, SBG V5 TN",
             "regimes.declared.metrics.sbg_v5_output_free.tn"),
            ("hard negatives, output reference accuracy",
             "regimes.canonical.metrics.output_reading_reference.accuracy"),
        ],
    ),
    (
        "REGRESSION_V5_RESULTS.json",
        "experiments/final/regression_evaluation.py",
        [
            ("regression, SBG V5 detected",
             "all_pairs.sbg_v5_output_free.n_detected"),
            ("regression, SBG V3 detected",
             "all_pairs.sbg_v3_output_free.n_detected"),
            ("regression, exception component detected",
             "all_pairs.exception_component_output_free.n_detected"),
            ("regression, output reference detected",
             "all_pairs.output_reading_reference_full_behaviour.n_detected"),
            ("silent bugs, SBG V5 detected",
             "silent_bugs_only.sbg_v5_output_free.n_detected"),
            ("silent bugs, output reference detected",
             "silent_bugs_only.output_reading_reference.n_detected"),
        ],
    ),
]


def dig(payload: Any, path: str) -> Any:
    for key in path.split("."):
        payload = payload[key]
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true",
                        help="also require the artifact to come back byte for byte")
    args = parser.parse_args()

    failures: List[str] = []
    for artifact, generator, headline in EXPERIMENTS:
        path = ARTIFACTS / artifact
        if not path.exists():
            failures.append(f"{artifact}: not committed")
            continue
        before_bytes = path.read_bytes()
        before: Dict = json.loads(before_bytes)

        result = subprocess.run([sys.executable, str(REPO_ROOT / generator)],
                                capture_output=True, text=True, cwd=REPO_ROOT)
        if result.returncode != 0:
            failures.append(f"{generator} exited {result.returncode}: "
                            f"{result.stderr.strip()[:300]}")
            continue

        after = json.loads(path.read_text())
        for label, dotted in headline:
            expected, actual = dig(before, dotted), dig(after, dotted)
            if expected != actual:
                failures.append(f"{artifact}: {label} was {expected}, re-ran as {actual}")

        if args.strict:
            bad, ok = strict_differences(artifact, before_bytes, path.read_bytes())
            if bad:
                failures.append(f"{artifact}: not byte-identical after re-running "
                                f"(differing lines: {bad[:10]}; expected under --strict "
                                f"on the interpreter that produced it; this is "
                                f"{sys.version_info.major}.{sys.version_info.minor})")
            elif ok:
                print(f"[note] {artifact}: {len(ok)} line(s) differ only in the "
                      f"allowed provenance string (lines {ok}); all other bytes identical")

        print(f"[{'ok' if not failures else '..'}] {artifact}: "
              f"{len(headline)} headline values checked"
              f"{', byte-exact' if args.strict else ''}")

    if failures:
        print("\nREPRODUCTION FAILED", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print(f"\nreproduction check passed on Python "
          f"{sys.version_info.major}.{sys.version_info.minor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
