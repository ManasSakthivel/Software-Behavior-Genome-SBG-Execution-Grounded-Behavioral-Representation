#!/usr/bin/env python3
"""
Quantifies how much trace-derived results move between two CPython versions.

Runs the two fast experiments under each interpreter in a throwaway clone and
compares every numeric field. Distances are expected to move -- the tracer sees
a different event stream (3.12 inlined comprehensions; PEP 667 changed
frame.f_locals in 3.13) -- so the question is whether any *reported* value
moves. The canonical research environment is recorded here, and every headline
number is produced under it.

    python3 experiments/final/python_version_sensitivity.py \\
        --python /path/to/python3.9 --python /path/to/python3.13
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from typing import Any, List, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CANONICAL = "3.13"
EXPERIMENTS = ("hard_negative_evaluation.py", "regression_evaluation.py")
ARTIFACTS = ("HARD_NEGATIVE_V5_RESULTS.json", "REGRESSION_V5_RESULTS.json")


def _walk(a: Any, b: Any, path: List[str], out: List[Tuple[float, str]]) -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        for key in a:
            if key in b:
                _walk(a[key], b[key], path + [key], out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for index, (x, y) in enumerate(zip(a, b)):
            _walk(x, y, path + [str(index)], out)
    elif (isinstance(a, (int, float)) and isinstance(b, (int, float))
          and not isinstance(a, bool)):
        out.append((abs(a - b), ".".join(path)))
    elif a != b:
        out.append((float("inf"), ".".join(path)))


def _run(python: str) -> Tuple[str, dict]:
    version = subprocess.run([python, "-c", "import sys;print('%d.%d.%d'%sys.version_info[:3])"],
                             capture_output=True, text=True, check=True).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        clone = pathlib.Path(tmp) / "repo"
        subprocess.run(["git", "clone", "-q", str(REPO_ROOT), str(clone)], check=True)
        for experiment in EXPERIMENTS:
            subprocess.run([python, "-W", "ignore", f"experiments/final/{experiment}"],
                           cwd=clone, capture_output=True, check=True)
        return version, {name: json.loads((clone / "artifacts" / "final" / name).read_text())
                         for name in ARTIFACTS}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", action="append", required=True)
    args = parser.parse_args()
    if len(args.python) != 2:
        parser.error("give exactly two interpreters")
    (va, ra), (vb, rb) = _run(args.python[0]), _run(args.python[1])
    report = {"artifact": "PYTHON_VERSION_SENSITIVITY", "canonical_version": CANONICAL,
              "compared": [va, vb], "experiments": {}}
    for name in ARTIFACTS:
        diffs: List[Tuple[float, str]] = []
        _walk(ra[name], rb[name], [], diffs)
        distances = [d for d in diffs if ".distances." in f".{d[1]}." or "distances" in d[1]]
        moved = [d for d in distances if d[0] > 0]
        reported = [path for delta, path in diffs
                    if delta > 0 and "distances" not in path and "n_events" not in path]
        report["experiments"][name] = {
            "distance_values": len(distances),
            "distance_values_changed": len(moved),
            "max_abs_distance_change": round(max((d[0] for d in distances), default=0.0), 6),
            "reported_values_changed": reported,
        }
    out = REPO_ROOT / "artifacts" / "final" / "PYTHON_VERSION_SENSITIVITY.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if all(not e["reported_values_changed"] for e in report["experiments"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
