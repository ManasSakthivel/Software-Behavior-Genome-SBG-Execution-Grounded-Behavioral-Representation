#!/usr/bin/env python3
"""
Guards the pre-registered invariant that output_free_v7 leaves every v6
selection unchanged (docs/current/PHASE2_PREREGISTRATION.md §1).

Re-extracts every base program of the v6-dataset test split under
output_free_v6 AND output_free_v7 with the current code, and compares each with
artifacts/final/programs_v6test_output_free_v6.json. Two properties must hold:

  1. v6 today == v6 as committed (the code change did not alter v6).
  2. For every program v6 could run, v7 == v6 (the class tier is only a
     fallback).

A program whose v6 record differs between two back-to-back v6 extractions is
reported as NONDETERMINISTIC rather than as a violation: its committed record
is one sample of a varying measurement, and no code change can be judged
against it. sort_heapsort's event count was observed to vary this way
(2026-09-29). Nondeterministic programs are listed so they can be reported.

Exit 0 when both hold for every deterministic program. Executes the programs;
reads no label and no score.
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from experiments.final.extraction import extract_program   # noqa: E402

COMMITTED = REPO_ROOT / "artifacts" / "final" / "programs_v6test_output_free_v6.json"


def _key(record: dict) -> tuple:
    return (record["ok"], record["entry_discovery"], record["failure_kind"],
            json.dumps(record["stats"], sort_keys=True))


def main() -> int:
    committed = json.loads(COMMITTED.read_text())["programs"]
    bases = sorted(p for p in committed if "/base_programs/" in p)
    failures = 0
    nondeterministic = []
    for committed_path in bases:
        local = str(REPO_ROOT / committed_path[committed_path.index("benchmark/"):])
        v6 = extract_program(local, {}, "output_free_v6").summary()
        v6_again = extract_program(local, {}, "output_free_v6").summary()
        v7 = extract_program(local, {}, "output_free_v7").summary()
        if _key(v6) != _key(v6_again):
            nondeterministic.append(pathlib.Path(local).stem)
            print(f"ND  {pathlib.Path(local).stem:28} v6 differs between two runs")
            continue
        same_v6 = _key(v6) == _key(committed[committed_path])
        same_v7 = (not v6["ok"]) or _key(v7) == _key(v6)
        failures += (not same_v6) + (not same_v7)
        print(f"{'ok ' if same_v6 and same_v7 else 'BAD'} {pathlib.Path(local).stem:28} "
              f"v6={v6['entry_discovery'] or v6['failure_kind']} "
              f"v7={v7['entry_discovery'] or v7['failure_kind']}")
    print(f"\n{len(bases)} programs, {failures} violations, "
          f"nondeterministic: {nondeterministic or 'none'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
