#!/usr/bin/env python3
"""EXP-A4-007 runtime / peak-memory measurement.

Driver mode: for every method spawn a CLEAN subprocess (sequential, no parallel load) that scores the same 50 deterministic v10_test pairs
(first 50 primary pairs ordered by sha1(pair_id)) and reports wall seconds (time.perf_counter) and peak RSS (ru_maxrss, bytes on macOS).
Trace-cache loading (gzip JSON) is timed separately from scoring.  SBG = frozen extraction of base and variant (uncached, as in a first-time pair) + score_pair.
"""
from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import importlib.util
import json
import os
import pathlib
import resource
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PKG = HERE.parents[1]
REPO = PKG.parent / "SBG"
OUT = PKG / "results" / "raw" / "EXP-A4-007"
METHODS = ["edit", "static_repo", "static_own", "execstats", "traceseq", "pathspectra", "valuespectra", "output_oracle", "output_indep", "sbg_extract_and_score"]


def sample_pairs(n=50):
    sys.path.insert(0, str(PKG / "experiments" / "common"))
    import eval_lib
    rows = eval_lib.load_population("v10_test")
    rows = sorted(rows, key=lambda r: hashlib.sha1(r["pair_id"].encode()).hexdigest())[:n]
    return rows


def edit_size(a, b):
    la = ast.unparse(ast.parse((REPO / a).read_text())).splitlines()
    lb = ast.unparse(ast.parse((REPO / b).read_text())).splitlines()
    return sum(1 for l in difflib.unified_diff(la, lb, lineterm="", n=0) if l.startswith(("+", "-")) and not l.startswith(("+++", "---")))


def worker(method):
    rows = sample_pairs()
    res = {"method": method, "n_pairs": len(rows)}
    t_all = time.perf_counter()
    if method == "edit":
        t = time.perf_counter()
        ok = sum(1 for r in rows if edit_size(r["base_path"], r["variant_path"]) == int(r["edit"]))
        res.update(score_s=time.perf_counter() - t, check_equals_frozen_edit=ok)
    elif method == "static_repo":
        spec = importlib.util.spec_from_file_location("sb", REPO / "experiments/final/static_baselines.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        t = time.perf_counter()
        for r in rows:
            a, b = (REPO / r["base_path"]).read_text(), (REPO / r["variant_path"]).read_text()
            m.multiset_distance(m.token_multiset(a), m.token_multiset(b))
            m.multiset_distance(m.ast_multiset(a), m.ast_multiset(b))
        res.update(score_s=time.perf_counter() - t)
    elif method == "static_own":
        import pickle
        import b02_static
        with open(PKG / "results/raw/EXP-A4-002/idf.pkl", "rb") as f:
            idf = pickle.load(f)["static"]
        feat = b02_static.StaticFeaturizer(idf)
        t = time.perf_counter()
        for r in rows:
            feat.pair(r["base_path"], r["variant_path"])
        res.update(score_s=time.perf_counter() - t)
    else:
        import pickle
        import b03_execstats
        import b04_valuespectra
        import b05_pathspectra
        import b05_traceseq
        from bl_common import FileTrace
        if method == "output_indep":
            return worker_indep(rows, res)
        if method == "sbg_extract_and_score":
            return worker_sbg(rows, res)
        t = time.perf_counter()
        pairs = [(FileTrace("v10_test", r["base_id"], r["base_path"]), FileTrace("v10_test", r["base_id"], r["variant_path"])) for r in rows]
        res["trace_load_s"] = time.perf_counter() - t
        with open(PKG / "results/raw/EXP-A4-002/idf.pkl", "rb") as f:
            idf = pickle.load(f)["trace"]
        t = time.perf_counter()
        for a, b in pairs:
            if method == "execstats":
                b03_execstats.exec_features(a, b)
            elif method == "traceseq":
                b05_traceseq.pair_features(a, b, idf)
            elif method == "pathspectra":
                b05_pathspectra.pair_features(a, b)
            elif method == "valuespectra":
                b04_valuespectra.pair_features(a, b)
            elif method == "output_oracle":
                b03_execstats.oracle_features(a, b)
        res["score_s"] = time.perf_counter() - t
    res["wall_total_s"] = time.perf_counter() - t_all
    res["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print("@@" + json.dumps(res))


def worker_indep(rows, res):
    import b06_indep_inputs as B6
    import gzip
    from bl_common import cache_file
    bat_dir = PKG / "results/raw/EXP-A4-003/batteries"
    tmp = pathlib.Path("/tmp/a4_rt")
    tmp.mkdir(exist_ok=True)
    t = time.perf_counter()
    per_file = []
    for r in rows:
        bat = bat_dir / f"v10_test__{r['base_id']}.json"
        for p in (r["base_path"], r["variant_path"]):
            ent = json.load(gzip.open(cache_file("v10_test", r["base_id"], p), "rt"))["entry_function"]
            t1 = time.perf_counter()
            B6.run_file(p, ent, str(bat), str(tmp / "o.json"))
            per_file.append(time.perf_counter() - t1)
    res.update(score_s=time.perf_counter() - t, n_files_executed=len(per_file), per_pair_includes="base+variant execution of <=40 inputs each (in-process, excl. interpreter start ~30-40 ms/file)")
    res["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print("@@" + json.dumps(res))


def worker_sbg(rows, res):
    sys.path.insert(0, str(REPO))
    os.chdir(REPO)
    t_imp = time.perf_counter()
    from experiments.final import extraction as ex
    res["import_s"] = time.perf_counter() - t_imp
    ext, sc = 0.0, 0.0
    for r in rows:
        cache = {}
        t = time.perf_counter()
        A = ex.extract_program(str(REPO / r["base_path"]), cache, "output_free_v8")
        B = ex.extract_program(str(REPO / r["variant_path"]), cache, "output_free_v8")
        ext += time.perf_counter() - t
        t = time.perf_counter()
        ex.score_pair(A, B)
        sc += time.perf_counter() - t
    res.update(extract_s=ext, score_s=sc)
    res["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print("@@" + json.dumps(res))


def driver():
    OUT.mkdir(parents=True, exist_ok=True)
    allres = []
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
    for m in METHODS:
        t = time.perf_counter()
        o = subprocess.run([sys.executable, str(HERE / "runtime.py"), "--worker", m], capture_output=True, text=True, env=env, timeout=1500)
        line = [l for l in o.stdout.splitlines() if l.startswith("@@")]
        if not line:
            print("FAILED", m, o.stderr[-400:])
            allres.append({"method": m, "error": o.stderr[-400:]})
            continue
        r = json.loads(line[0][2:])
        r["subprocess_wall_s"] = time.perf_counter() - t
        n = r["n_pairs"]
        r["score_ms_per_pair"] = 1000 * r["score_s"] / n
        r["peak_rss_MB"] = r["peak_rss_bytes"] / 1e6
        allres.append(r)
        print(m, {k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()})
    (OUT / "runtime.json").write_text(json.dumps(allres, indent=1))
    # cost of the shared trace dump (frozen SBG extraction) per file from cache records
    import gzip
    import glob
    ex = []
    for f in glob.glob(str(PKG / "results/raw/trace_cache/v10_test/*/*.json.gz")):
        ex.append(json.load(gzip.open(f, "rt")).get("extract_seconds") or 0.0)
    ex.sort()
    (OUT / "extract_seconds_v10.json").write_text(json.dumps({"n_files": len(ex), "sum_s": sum(ex), "mean_s": sum(ex) / len(ex), "median_s": ex[len(ex) // 2], "max_s": ex[-1]}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker")
    a = ap.parse_args()
    worker(a.worker) if a.worker else driver()
