#!/usr/bin/env python3
"""ab03 -- score the 9 A4B wave-2 competitor modules on v9c_train and v9c_dev ONLY (EXP-A4R-004).  Label-free scoring stage.

* Modules and cn_lib are imported READ-ONLY from experiments/competitor_baselines/competitors_new/ (nothing there is modified, no .READY marker is written).
* All declared configurations of every module are scored (score_pair_multi + __default__); no selection is made at this stage.
* Held-out populations are refused.  Labels are NOT read here (population rows are only used for pair ids / paths).
* Checkpointed per (module, pop, program) in WP_A_B_COMPARATIVE_BENCHMARK/raw/EXP-A4R-004/scores/ ; existing checkpoints are never overwritten.
* Failures (exception inside a module for a pair) are logged per pair and the pair's configs are stored as null (= not computable).
usage: ab03_wave2_devtrain_scores.py --pop v9c_dev [--only a,b] [--workers 2]
"""
from __future__ import annotations

import argparse
import collections
import importlib
import json
import math
import multiprocessing
import pathlib
import sys
import time
import traceback

HERE = pathlib.Path(__file__).resolve().parent
WP = HERE.parent
PKG = WP.parent
NEW = PKG / "experiments" / "competitor_baselines" / "competitors_new"
OUT = WP / "raw" / "EXP-A4R-004"
sys.dont_write_bytecode = True
sys.path.insert(0, str(NEW))
import cn_lib  # noqa: E402

MODULES = ["static_tce", "static_ted", "static_srclev", "static_tfidf", "birthmark_kgram", "trace_align", "obs_points_outfree", "obs_points_outreading", "diffexec_same_input"]
ALLOWED = ("v9c_train", "v9c_dev")


def exclusions(pop):
    rows = [r for r in cn_lib.Ctx().population(pop) if r.get("in_primary_population")]
    ex = sorted({r["base_id"] for r in rows if not (PKG / "results" / "raw" / "trace_cache" / pop / r["base_id"] / "DONE").exists()})
    return rows, ex


def job(args):
    name, pop, base, rows = args
    out = OUT / "scores" / pop / name / f"{base}.json"
    if out.exists():
        return name, base, 0.0, 0, True
    t0 = time.time()
    mod = importlib.import_module(name)
    ctx = cn_lib.Ctx()
    res, errs = {}, []
    for r in rows:
        b, v = ctx.records(r, pop)
        try:
            d = dict(mod.score_pair_multi(b, v, ctx))
            d["__default__"] = mod.score_pair(b, v, ctx)
        except Exception as e:  # noqa: BLE001
            d = {}
            errs.append({"pair_id": r["pair_id"], "err": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()[-400:]})
        res[r["pair_id"]] = {k: (None if (x is None or (isinstance(x, float) and math.isnan(x))) else float(x)) for k, x in d.items()}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"scores": res, "errors": errs, "seconds": time.time() - t0}, sort_keys=True))
    return name, base, time.time() - t0, len(errs), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pop", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    if a.pop not in ALLOWED:
        raise SystemExit(f"REFUSED: {a.pop} is not an allowed population for ab03 (dev/train only)")
    mods = [m for m in MODULES if not a.only or m in a.only.split(",")]
    rows, excl = exclusions(a.pop)
    by = collections.defaultdict(list)
    for r in rows:
        if r["base_id"] not in excl:
            by[r["base_id"]].append(r)
    jobs = [(m, a.pop, b, by[b]) for m in mods for b in sorted(by)]
    (OUT / "logs").mkdir(parents=True, exist_ok=True)
    (OUT / "logs" / f"exclusions_{a.pop}.json").write_text(json.dumps({"pop": a.pop, "n_primary_rows": len(rows), "excluded_programs_no_trace_cache": excl,
                                                                       "n_excluded_pairs": sum(1 for r in rows if r["base_id"] in excl), "n_scored_pairs": sum(len(v) for v in by.values())}, indent=1))
    t = time.time()
    nerr = 0
    with multiprocessing.get_context("fork").Pool(a.workers) as pool:
        for name, base, sec, ne, skipped in pool.imap_unordered(job, jobs):
            nerr += ne
            print(f"{name:22s} {a.pop} {base:32s} {'(ckpt)' if skipped else f'{sec:.1f}s'} errors={ne}", flush=True)
    print(f"{a.pop}: {len(jobs)} jobs, {nerr} pair-level errors, {time.time() - t:.0f}s")


if __name__ == "__main__":
    main()
