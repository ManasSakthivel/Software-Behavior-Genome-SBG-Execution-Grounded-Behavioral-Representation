#!/usr/bin/env python3
"""Score SBG V5 and the EXPERIMENTAL V6-graded variant on the SAME traces (EXPLORATORY / DEVELOPMENT).

The frozen extraction is used unchanged; only the state-transition genome is computed twice from the same trace list
(V5 abstraction = the frozen one, V6 = sbg/v6/state_transition_genome_v6.py).  V5 values are verified equal to the frozen scored files.

    PYTHONHASHSEED=0 python experiments/final/score_v6_experimental.py --design v9c --split dev [--workers 6]
    -> artifacts/final/pairs_{design}_{split}_v6exp.jsonl   (one row per pair in the matched population's source files)

Never run on a split whose use would break a freeze (v8 test is never touched; v9c val is not scored here).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import concurrent.futures

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments" / "final"))
ART = REPO / "artifacts" / "final"
W_V3, W_T, W_S = 0.50, 0.25, 0.25
DESIGN = "v9c"


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def pair_list(design, split):
    """All pairs (CHANGED partners + their matched EQUIVALENT pairs) of the v9c design for `split`."""
    if design == "v10":
        return jl(REPO / "benchmark/datasets/v10_independent/pairs_test.jsonl")
    meta = {m["pair_id"]: m for m in jl(REPO / f"benchmark/datasets/v9_composed/pairs_{split}.jsonl")}
    v8 = {m["pair_id"]: m for m in jl(REPO / f"benchmark/datasets/v8/pairs_{split}.jsonl")}
    for m in list(meta.values()):
        meta[m["matched_equivalent_pair_id"]] = v8[m["matched_equivalent_pair_id"]]
    return list(meta.values())


class Dual:
    """Wraps the two state graphs; `.transitions` is the V5 graph so any frozen consumer behaves as before."""
    def __init__(self, g5, g6):
        self.g5, self.g6, self.transitions = g5, g6, g5.transitions


class DualGenome:
    def __init__(self):
        from sbg.v5.state_transition_genome import StateTransitionGenome as G5
        from sbg.v6.state_transition_genome_v6 import StateTransitionGenome as G6
        self.a, self.b = G5(), G6()

    def extract(self, traces):
        return Dual(self.a.extract(traces), self.b.extract(traces))

    def distance(self, x, y):                       # frozen score_pair calls this -> must return the V5 value
        return self.a.distance(x.g5, y.g5)


def worker(prog, split, only=None):
    from experiments.final import extraction as ex
    ex._state_genome = DualGenome()
    pairs = [p for p in pair_list(DESIGN, split) if p["base_id"] == prog and (only is None or p["pair_id"] == only)]
    cache, rows = {}, []
    for p in pairs:
        re.purge()
        A = ex.extract_program(str(REPO / p["base_path"]), cache, "output_free_v8")
        B = ex.extract_program(str(REPO / p["variant_path"]), cache, "output_free_v8")
        row = {"pair_id": p["pair_id"], "base_id": p["base_id"], "split": split, "evaluated": False}
        sc = ex.score_pair(A, B)
        if sc is not None:
            d6 = ex._state_genome.b.distance(A.state.g6, B.state.g6)
            d3, dt = sc["sbg_v3"], sc["sbg_temporal"]
            row.update(evaluated=True, scores=sc, sbg_state_v6=round(d6, 9),
                       sbg_v6=round(min(1.0, max(0.0, W_V3 * d3 + W_T * dt + W_S * d6)), 9))
        else:
            row["failure"] = (A.failure_kind or B.failure_kind)
        rows.append(row)
    print("@@" + json.dumps(rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="v9c")
    ap.add_argument("--split")
    ap.add_argument("--worker")
    ap.add_argument("--only")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    global DESIGN
    DESIGN = a.design
    if a.worker:
        worker(a.worker, a.split, a.only)
        return
    progs = sorted({p["base_id"] for p in pair_list(a.design, a.split)})
    env = dict(os.environ, PYTHONHASHSEED="0")

    def attempt(pr, only, timeout):
        cmd = [sys.executable, __file__, "--worker", pr, "--split", a.split, "--design", a.design] + (["--only", only] if only else [])
        try:
            o = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None
        line = [l for l in o.stdout.splitlines() if l.startswith("@@")]
        return json.loads(line[-1][2:]) if line else None

    def run(pr):
        got = attempt(pr, None, 900)
        if got is not None:
            return pr, got, None
        # Mechanical fallback (score-independent), as run_chunked.py: one subprocess per pair; a pair that fails/times out is
        # recorded UNEVALUATED with failure=harness_timeout (never a zero score).
        got = []
        for p in [q for q in pair_list(a.design, a.split) if q["base_id"] == pr]:
            r = attempt(pr, p["pair_id"], 120)
            got += r if r else [{"pair_id": p["pair_id"], "base_id": pr, "split": a.split, "evaluated": False, "failure": "harness_timeout"}]
        return pr, got, "per-pair fallback"

    rows = {}
    with concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
        for pr, got, err in ex.map(run, progs):
            print(pr, len(got), err or "", flush=True)
            for r in got or []:
                rows[r["pair_id"]] = r
    order = [p["pair_id"] for p in pair_list(a.design, a.split)]
    out = ART / f"pairs_{a.design}_{a.split}_v6exp.jsonl"
    out.write_text("".join(json.dumps(rows[i]) + "\n" for i in order if i in rows))
    print("wrote", out.relative_to(REPO), len(rows), "rows;", sum(r["evaluated"] for r in rows.values()), "evaluated")


if __name__ == "__main__":
    main()
