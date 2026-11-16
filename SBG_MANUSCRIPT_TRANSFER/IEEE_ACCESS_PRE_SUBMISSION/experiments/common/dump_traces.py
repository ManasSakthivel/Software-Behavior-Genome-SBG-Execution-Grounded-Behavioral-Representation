#!/usr/bin/env python3
"""EXP-ORCH-001: shared trace dump (single execution pass reused by every competitor / ablation).

Executes the FROZEN SBG extraction (experiments.final.extraction, protocol output_free_v8, same entry policy,
same synthesised inputs, same budgets) on every base and variant of a split and persists
  (a) a compact raw trace record per program file (events, return values, exceptions, stdout), and
  (b) the SBG scores recomputed by the frozen code (replication check against the frozen scored pairs files).

READ-ONLY with respect to the SBG repository: nothing is written under SBG/. Output goes to
IEEE_ACCESS_PRE_SUBMISSION/results/raw/trace_cache/<design>_<split>/.

  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python dump_traces.py --design v10 --split test --workers 6
  ... --design v9c --split val|dev|train

Resumable: a per-program output directory that already contains DONE is skipped.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve()
PKG = HERE.parents[2]                                   # IEEE_ACCESS_PRE_SUBMISSION
REPO = PKG.parent / "SBG"
OUT_ROOT = PKG / "results" / "raw" / "trace_cache"
MAXREPR = 1500


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def pair_list(design, split):
    if design == "v10":
        return jl(REPO / "benchmark/datasets/v10_independent/pairs_test.jsonl")
    meta = {m["pair_id"]: m for m in jl(REPO / f"benchmark/datasets/v9_composed/pairs_{split}.jsonl")}
    v8 = {m["pair_id"]: m for m in jl(REPO / f"benchmark/datasets/v8/pairs_{split}.jsonl")}
    for m in list(meta.values()):
        meta[m["matched_equivalent_pair_id"]] = v8[m["matched_equivalent_pair_id"]]
    return list(meta.values())


def _r(x):
    try:
        s = repr(x)
    except Exception as e:                                 # noqa: BLE001
        s = f"<repr-error {type(e).__name__}>"
    return s if len(s) <= MAXREPR else s[:MAXREPR] + f"...<+{len(s) - MAXREPR}>"


def compact(sandbox):
    """First run in full, later runs summarised by a determinism digest."""
    if sandbox is None or not sandbox.traces:
        return None
    runs = sandbox.traces
    def dig(run):
        h = hashlib.sha256()
        for t in run:
            h.update(repr((t.input_repr, t.exception, _r(t.return_value), t.stdout,
                           [(e.event_type, e.function_name, e.lineno) for e in t.events])).encode())
        return h.hexdigest()[:16]
    out = {"n_runs": len(runs), "run_digests": [dig(r) for r in runs], "wall_time_ms": sandbox.wall_time_ms,
           "error": sandbox.error, "timeout_fraction": sandbox.timeout_fraction, "traces": []}
    for t in runs[0]:
        ev = []
        for e in t.events:
            snap = e.local_vars_snapshot if e.event_type in ("call", "return", "exception") else None
            ev.append([e.event_type[0], e.function_name, e.lineno, snap])
        out["traces"].append({"input": t.input_repr, "ret": _r(t.return_value), "ret_type": type(t.return_value).__name__,
                              "exc": t.exception, "stdout": t.stdout[:MAXREPR], "ms": t.execution_time_ms,
                              "cov": sorted(t.coverage), "trunc": t.truncated, "events": ev})
    return out


def worker(design, split, prog, outdir):
    sys.path.insert(0, str(REPO))
    os.chdir(REPO)
    from experiments.final import extraction as ex
    captured = {}
    orig = ex._runner.run

    def wrapped(program_id, *a, **k):
        res = orig(program_id, *a, **k)
        captured[program_id] = res
        return res
    ex._runner.run = wrapped
    pairs = [p for p in pair_list(design, split) if p["base_id"] == prog]
    od = pathlib.Path(outdir)
    od.mkdir(parents=True, exist_ok=True)
    cache, recs, rows = {}, {}, []

    def rec_for(path):
        if path in recs:
            return recs[path]
        re.purge()
        t0 = time.time()
        r = ex.extract_program(str(REPO / path), cache, "output_free_v8")
        # extract_program caches by the absolute path string
        sb = captured.pop(pathlib.Path(path).stem, None)
        info = {"path": path, "ok": r.ok, "failure_kind": r.failure_kind, "failure_detail": r.failure_detail,
                "entry_function": r.entry_function, "entry_discovery": r.entry_discovery, "stats": r.stats,
                "extract_seconds": round(time.time() - t0, 3), "sandbox": compact(sb)}
        recs[path] = (r, info)
        return recs[path]

    for p in pairs:
        A, ia = rec_for(p["base_path"])
        B, ib = rec_for(p["variant_path"])
        sc = ex.score_pair(A, B)
        rows.append({"pair_id": p["pair_id"], "base_id": prog, "evaluated": sc is not None,
                     "scores": sc, "failure": None if sc is not None else (A.failure_kind or B.failure_kind)})
    for path, (_, info) in recs.items():
        fn = od / (hashlib.sha1(path.encode()).hexdigest()[:12] + "__" + pathlib.Path(path).stem + ".json.gz")
        with gzip.open(fn, "wt") as f:
            json.dump(info, f)
    (od / "pairs_scores.json").write_text(json.dumps(rows))
    (od / "DONE").write_text(str(time.time()))
    print("@@ok", prog, len(recs), "files", len(rows), "pairs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True)
    ap.add_argument("--split", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--worker")
    ap.add_argument("--outdir")
    ap.add_argument("--timeout", type=int, default=1800)
    a = ap.parse_args()
    if a.worker:
        worker(a.design, a.split, a.worker, a.outdir)
        return
    root = OUT_ROOT / f"{a.design}_{a.split}"
    root.mkdir(parents=True, exist_ok=True)
    progs = sorted({p["base_id"] for p in pair_list(a.design, a.split)})
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
    log = []

    def run(pr):
        od = root / pr
        if (od / "DONE").exists():
            return pr, "skipped(done)", 0.0
        t0 = time.time()
        try:
            o = subprocess.run([sys.executable, str(HERE), "--design", a.design, "--split", a.split, "--worker", pr,
                                "--outdir", str(od)], env=env, capture_output=True, text=True, timeout=a.timeout)
            st = "ok" if (od / "DONE").exists() else f"FAILED rc={o.returncode} {o.stderr[-400:]}"
        except subprocess.TimeoutExpired:
            st = f"TIMEOUT>{a.timeout}s"
        return pr, st, time.time() - t0

    with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
        for pr, st, dt in pool.map(run, progs):
            print(f"{pr:40s} {st} {dt:.1f}s", flush=True)
            log.append({"program": pr, "status": st, "seconds": round(dt, 1)})
    (root / "DUMP_LOG.json").write_text(json.dumps(log, indent=1))


if __name__ == "__main__":
    main()
