#!/usr/bin/env python3
"""A2: independent recomputation + sensitivity harness for the frozen SBG scores.

Re-extracts every program with the FROZEN code (experiments.final.extraction, protocol output_free_v8) and rescoring
pairs exactly as experiments/final/score_v6_experimental.py / run_chunked.py do (score_pair on ProgramRecords, per-program
subprocess).  SBG is imported by sys.path insertion only; nothing is written under SBG/ (PYTHONDONTWRITEBYTECODE=1).

  run      : recompute scores into <out>/<program>.json  (one subprocess per program, bounded workers)
  compare  : compare a recompute directory with the frozen scored files (exact equality, max |diff|, rank flips)

Knobs for sensitivity experiments
  --python PATH        interpreter used for the worker subprocesses (3.13 canonical vs 3.9 ...)
  --hashseed S         PYTHONHASHSEED for workers ("0" frozen setting; "random" = a fresh random value per program, recorded)
  --purge MODE         pair (default; = frozen score_v6_experimental.py: re.purge() at the start of every pair) | always (= dump_traces.py:
                       re.purge() before every NEW file) | never (no re.purge at all)
  --cwd MODE           repo (default) | tmp (different working directory)
  --load N             spawn N busy-loop processes (CPU-contention => 1 s trace timeout sensitivity)
  --workers K          concurrent program subprocesses

Examples
  PYTHONHASHSEED=0 python recompute_scores.py run --design v10 --split test --out ../results/raw/repro/recompute_v10_full
  python recompute_scores.py compare --design v10 --split test --dir ../results/raw/repro/recompute_v10_full
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import pathlib
import random
import re
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve()
PKG = HERE.parents[1]
REPO = pathlib.Path(os.environ.get("SBG_REPO") or (PKG.parent / "SBG")).resolve()   # override with SBG_REPO=<clean checkout>
KEYS = ["sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state", "exception_fraction", "exception_component_v3",
        "exception_type_jaccard", "call_count", "n_functions", "coverage_size", "combined_shortcut", "v5_full"]


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


def frozen_rows(design, split):
    A = REPO / "artifacts/final"
    files = ([A / "pairs_v10_test_v6exp.jsonl"] if design == "v10" else
             [A / f"pairs_v9c_{split}_output_free_v8.jsonl", A / f"pairs_v8{split}_output_free_v8.jsonl"])
    rows = {}
    for f in files:
        for r in jl(f):
            rows.setdefault(r["pair_id"], r)
    return rows


# ------------------------------------------------------------------------------------------------------------
# worker (runs in a subprocess under the interpreter / hash seed / cwd under test)
# ------------------------------------------------------------------------------------------------------------
def worker(design, split, prog, outfile, purge, cwd):
    sys.path.insert(0, str(REPO))
    os.chdir(REPO if cwd == "repo" else cwd)
    from experiments.final import extraction as ex
    captured = {}
    orig = ex._runner.run

    def wrapped(program_id, *a, **k):
        res = orig(program_id, *a, **k)
        captured[program_id] = res
        return res
    ex._runner.run = wrapped

    def digests(sb):
        if sb is None or not sb.traces:
            return None
        out = {"events_only": [], "with_snapshots": [], "n_traces": [len(r) for r in sb.traces]}
        for run in sb.traces:
            h1, h2 = hashlib.sha256(), hashlib.sha256()
            for t in run:
                h1.update(repr((t.input_repr, t.exception, t.stdout, [(e.event_type, e.function_name, e.lineno) for e in t.events])).encode())
                h2.update(repr((t.input_repr, t.exception, t.stdout, [(e.event_type, e.function_name, e.lineno, sorted(e.local_vars_snapshot.items())) for e in t.events])).encode())
            out["events_only"].append(h1.hexdigest()[:12])
            out["with_snapshots"].append(h2.hexdigest()[:12])
        out["truncated"] = sum(1 for run in sb.traces for t in run if t.truncated)
        out["timeouts"] = sum(1 for run in sb.traces for t in run if t.exception and t.exception.startswith("TimeoutError"))
        return out

    pairs = [p for p in pair_list(design, split) if p["base_id"] == prog]
    cache, info, rows = {}, {}, []
    t0 = time.time()

    def rec(path):
        if path in info:
            return info[path][0]
        if purge == "always":
            re.purge()
        r = ex.extract_program(str(REPO / path), cache, "output_free_v8")
        sb = captured.pop(pathlib.Path(path).stem, None)
        info[path] = (r, {"ok": r.ok, "failure_kind": r.failure_kind, "entry": r.entry_function,
                          "stats": {k: r.stats.get(k) for k in ("n_traces", "n_events", "n_truncated_traces", "temporal_available",
                                                                "state_available", "runs_completed", "program_budget_exceeded")} if r.stats else None,
                          "digests": digests(sb), "timeout_fraction": sb.timeout_fraction if sb else None})
        return r

    for p in pairs:
        if purge == "pair":
            re.purge()                      # exactly what score_v6_experimental.py:71 (the frozen V10 scorer) does
        A = rec(p["base_path"])
        B = rec(p["variant_path"])
        sc = ex.score_pair(A, B)
        rows.append({"pair_id": p["pair_id"], "evaluated": sc is not None, "scores": sc})
    pathlib.Path(outfile).write_text(json.dumps({"program": prog, "python": sys.version.split()[0], "hashseed": os.environ.get("PYTHONHASHSEED"),
                                                 "purge": purge, "cwd": os.getcwd(), "seconds": round(time.time() - t0, 2),
                                                 "files": {k: v[1] for k, v in info.items()}, "rows": rows}))
    print("@@ok", prog, len(rows))


# ------------------------------------------------------------------------------------------------------------
def cmd_run(a):
    out = pathlib.Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    progs = sorted({p["base_id"] for p in pair_list(a.design, a.split)})
    if a.programs:
        progs = [p for p in a.programs.split(",") if p in progs]
    load = []
    for _ in range(a.load):
        load.append(subprocess.Popen([sys.executable, "-c", "while True: pass"]))
    log = []
    rng = random.Random(a.seed_for_seeds)

    def one(pr):
        fn = out / f"{pr}.json"
        if fn.exists():
            return pr, "skipped(exists)", 0.0, None
        hs = a.hashseed if a.hashseed != "random" else str(rng.randrange(1, 2 ** 31))
        env = dict(os.environ, PYTHONHASHSEED=hs, PYTHONDONTWRITEBYTECODE="1")
        cwd = "repo" if a.cwd == "repo" else a.cwd_path
        t0 = time.time()
        try:
            r = subprocess.run([a.python, str(HERE), "worker", "--design", a.design, "--split", a.split, "--program", pr,
                                "--outfile", str(fn), "--purge", a.purge, "--cwdmode", cwd], env=env, capture_output=True, text=True,
                               timeout=a.timeout)
            st = "ok" if fn.exists() else f"FAILED rc={r.returncode} {r.stderr[-300:]}"
        except subprocess.TimeoutExpired:
            st = f"TIMEOUT>{a.timeout}s"
        return pr, st, time.time() - t0, hs

    try:
        with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
            for pr, st, dt, hs in pool.map(one, progs):
                print(f"{pr:36s} {st} {dt:6.1f}s seed={hs}", flush=True)
                log.append(dict(program=pr, status=st, seconds=round(dt, 1), hashseed=hs))
    finally:
        for p in load:
            p.kill()
    (out / "RUN_LOG.json").write_text(json.dumps(dict(args=vars(a), python=a.python, log=log), indent=1))


def auc_flips(frozen, new, labels):
    """tie-aware ordering comparison of the cross-label pairs: returns (n_cross, n_changed_order, auroc_frozen, auroc_new)"""
    pos = [k for k in frozen if labels.get(k) == 1 and k in new]
    neg = [k for k in frozen if labels.get(k) == 0 and k in new]
    ch = 0
    cf = cn = 0.0
    for p in pos:
        for n in neg:
            sf = (frozen[p] > frozen[n]) - (frozen[p] < frozen[n])
            sn = (new[p] > new[n]) - (new[p] < new[n])
            ch += sf != sn
            cf += 1.0 if sf > 0 else 0.5 if sf == 0 else 0.0
            cn += 1.0 if sn > 0 else 0.5 if sn == 0 else 0.0
    nc = len(pos) * len(neg)
    return nc, ch, (cf / nc if nc else None), (cn / nc if nc else None)


def cmd_compare(a):
    fr = frozen_rows(a.design, a.split)
    pairs = {p["pair_id"]: p for p in pair_list(a.design, a.split)}
    d = pathlib.Path(a.dir)
    labels = {pid: (1 if (p.get("semantic_relation") or p.get("expected_label")) == "CHANGED" else 0) for pid, p in pairs.items()}
    tot = dict(rows=0, evaluated_equal=0, evaluated_flag_diff=0, exact=0, differing=0, missing=0)
    maxdiff = {k: 0.0 for k in KEYS}
    nd = {k: 0 for k in KEYS}
    per_prog = {}
    new_v5, fro_v5, lab = {}, {}, {}
    for f in sorted(d.glob("*.json")):
        if f.name in ("RUN_LOG.json", "COMPARE.json"):
            continue
        j = json.loads(f.read_text())
        pp = dict(rows=0, exact=0, differing=0, python=j["python"], hashseed=j["hashseed"], seconds=j["seconds"], max_abs_diff_v5=0.0,
                  det_runs_identical=None, timeouts=0, truncated=0)
        ident = []
        for path, inf in j["files"].items():
            dg = inf.get("digests")
            if dg:
                ident.append(len(set(dg["with_snapshots"])) == 1)
                pp["timeouts"] += dg.get("timeouts", 0)
                pp["truncated"] += dg.get("truncated", 0)
        pp["det_runs_identical"] = (all(ident) if ident else None)
        for r in j["rows"]:
            tot["rows"] += 1
            pp["rows"] += 1
            fz = fr.get(r["pair_id"])
            if fz is None:
                tot["missing"] += 1
                continue
            if bool(fz["evaluated"]) != bool(r["evaluated"]):
                tot["evaluated_flag_diff"] += 1
                pp["differing"] += 1
                continue
            if not r["evaluated"]:
                tot["evaluated_equal"] += 1
                pp["exact"] += 1
                continue
            same = True
            for k in KEYS:
                if k not in fz["scores"]:
                    continue
                dv = abs(fz["scores"][k] - r["scores"][k])
                if dv != 0.0:
                    same = False
                    nd[k] += 1
                    maxdiff[k] = max(maxdiff[k], dv)
                    if k == "sbg_v5":
                        pp["max_abs_diff_v5"] = max(pp["max_abs_diff_v5"], dv)
            tot["exact" if same else "differing"] += 1
            pp["exact" if same else "differing"] += 1
            new_v5[r["pair_id"]] = r["scores"]["sbg_v5"]
            fro_v5[r["pair_id"]] = fz["scores"]["sbg_v5"]
        per_prog[j["program"]] = pp
    nc, ch, af, an = auc_flips(fro_v5, new_v5, labels)
    summary = dict(design=a.design, split=a.split, dir=str(d), totals=tot, n_keys_differing=nd, max_abs_diff_by_key=maxdiff,
                   cross_label_pairs=nc, cross_pairs_order_changed=ch, pooled_auroc_frozen_subset=af, pooled_auroc_new_subset=an,
                   n_programs=len(per_prog), per_program=per_prog)
    (d / "COMPARE.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k != "per_program"}, indent=1))
    bad = {k: v for k, v in per_prog.items() if v["differing"]}
    print("programs with differing rows:", {k: (v["differing"], v["rows"], round(v["max_abs_diff_v5"], 6)) for k, v in bad.items()})


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--design", required=True)
    r.add_argument("--split", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--programs", default="")
    r.add_argument("--python", default=sys.executable)
    r.add_argument("--hashseed", default="0")
    r.add_argument("--purge", default="pair", choices=["pair", "always", "never"])
    r.add_argument("--cwd", default="repo", choices=["repo", "tmp"])
    r.add_argument("--cwd-path", dest="cwd_path", default="/tmp")
    r.add_argument("--load", type=int, default=0)
    r.add_argument("--workers", type=int, default=3)
    r.add_argument("--timeout", type=int, default=3600)
    r.add_argument("--seed-for-seeds", dest="seed_for_seeds", type=int, default=12345)
    c = sub.add_parser("compare")
    c.add_argument("--design", required=True)
    c.add_argument("--split", required=True)
    c.add_argument("--dir", required=True)
    w = sub.add_parser("worker")
    w.add_argument("--design")
    w.add_argument("--split")
    w.add_argument("--program")
    w.add_argument("--outfile")
    w.add_argument("--purge")
    w.add_argument("--cwdmode")
    a = ap.parse_args()
    if a.cmd == "worker":
        worker(a.design, a.split, a.program, a.outfile, a.purge, a.cwdmode)
    elif a.cmd == "run":
        cmd_run(a)
    else:
        cmd_compare(a)


if __name__ == "__main__":
    main()
