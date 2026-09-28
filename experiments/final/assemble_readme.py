#!/usr/bin/env python3
"""
experiments/final/assemble_readme.py
====================================
Splices docs/generated/readme_results.md into README.md between its markers.

The README's results section is generated, not written. Every number in it
comes from an authoritative artifact through make_tables.py, and
consistency_check.py fails the build if the committed block differs from what
the artifacts currently produce. That is the mechanism that stops the README
and the evidence drifting apart, which is how "12/12" outlived the result it
described.

Usage:
    python3 experiments/final/assemble_readme.py
"""
from __future__ import annotations

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
README = REPO_ROOT / "README.md"
GENERATED = REPO_ROOT / "docs" / "generated" / "readme_results.md"
BEGIN = "<!-- BEGIN GENERATED RESULTS -->"
END = "<!-- END GENERATED RESULTS -->"


def splice(readme_text: str, block: str) -> str:
    start = readme_text.find(BEGIN)
    stop = readme_text.find(END)
    if start == -1 or stop == -1:
        raise SystemExit(f"README.md is missing {BEGIN} / {END}")
    return readme_text[:start] + block.rstrip("\n") + readme_text[stop + len(END):]


def main() -> int:
    if not GENERATED.exists():
        print(f"{GENERATED.relative_to(REPO_ROOT)} missing; run `make tables`",
              file=sys.stderr)
        return 1
    README.write_text(splice(README.read_text(), GENERATED.read_text()))
    print(f"spliced {GENERATED.relative_to(REPO_ROOT)} into README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
