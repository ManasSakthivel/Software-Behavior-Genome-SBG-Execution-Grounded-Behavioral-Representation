#!/usr/bin/env python3
"""EXP-A4C-006 runtime / peak-memory measurement.

Driver: for every method spawn a CLEAN subprocess (sequential; no parallel load) which scores the same N=50 deterministic pairs of a population
(first 50 primary pairs ordered by sha1(pair_id), default v10_test) and reports wall seconds (time.perf_counter, first = cold-cache repeat of 3; all repeats stored) and peak RSS
(resource.getrusage(RUSAGE_SELF).ru_maxrss; bytes on macOS) together with the RSS of the freshly-imported interpreter (baseline).
Trace-cache loading (gzip JSON -> FileTrace) is timed separately from scoring.  Every trace-based module computes ALL its declared configurations jointly,
so its per-pair cost is an upper bound for any single configuration.
SBG: frozen extraction of base AND variant (uncached, as for a first-time pair) + score_pair; the cached shared-trace extraction cost is summarised from the
`extract_seconds` fields of the trace-cache records and per-program DUMP_LOG.json.
Run: PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 <py313> runtime_a4c.py [--pop v10_test]            (driver)
     runtime_a4c.py --worker <method> --pop P                                                      (internal)
"""
from __future__ import annotations

import argparse
import ast
import difflib
import glob
import gzip
import hashlib
import importlib.util
import json
import os
import pathlib
import pickle
import resource
import statistics
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a4c_common as C  # noqa: E402
from a4c_common import PKG, REPO, RAW, EXP_RT, EXP_FEAT, eval_lib  # noqa: E402

METHODS = ["edit", "static_repo", "static_own_and_tce", "execstats", "traceseq", "pathspectra", "valuespectra", "oracle_output_reading", "output_indep_run", "output_indep_battery_gen",
           "combiners_LR_RF", "sbg_extract_and_score"]
N = 50


def sample_pairs(pop, n=N):
    rows = eval_lib.load_population(pop)
    return sorted(rows, key=lambda r: hashlib.sha1(r["pair_id"].encode()).hexdigest())[:n]


def edit_size(a, b):
    la = ast.unparse(ast.parse((REPO / a).read_text())).splitlines()
    lb = ast.unparse(ast.parse((REPO / b).read_text())).splitlines()
    return sum(1 for l in difflib.unified_diff(la, lb, lineterm="", n=0) if l.startswith(("+", "-")) and not l.startswith(("+++", "---")))


def timed3(fn):
    ts = []
    for _ in range(3):
        t = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t)
    return ts[0], ts                      # first (cold-cache) repeat is the reported figure; all 3 repeats are stored


def worker(method, pop):
    v = C.verified_state()
    C.setup_modules(bool(v.get("use_fixed_modules", True)) if isinstance(v, dict) else False)
    rows = sample_pairs(pop)
    res = {"method": method, "population": pop, "n_pairs": len(rows)}
    rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    res["rss_interpreter_start_bytes"] = rss0
    if method == "edit":
        s, ts = timed3(lambda: [edit_size(r["base_path"], r["variant_path"]) for r in rows])
        res.update(score_s=s, repeats_s=ts, check_equals_frozen_edit=sum(1 for r in rows if edit_size(r["base_path"], r["variant_path"]) == int(r["edit"])))
    elif method == "static_repo":
        spec = importlib.util.spec_from_file_location("sb", REPO / "experiments/final/static_baselines.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)

        def f():
            for r in rows:
                a, b = (REPO / r["base_path"]).read_text(), (REPO / r["variant_path"]).read_text()
                m.multiset_distance(m.token_multiset(a), m.token_multiset(b))
                m.multiset_distance(m.ast_multiset(a), m.ast_multiset(b))
        s, ts = timed3(f)
        res.update(score_s=s, repeats_s=ts)
    elif method == "static_own_and_tce":
        import b02_static
        with open(RAW / EXP_FEAT / "idf.pkl", "rb") as fh:
            idf = pickle.load(fh)["static"]

        def f():
            feat = b02_static.StaticFeaturizer(idf)             # cold per-file cache: includes tokenisation, AST, bytecode compile
            for r in rows:
                feat.pair(r["base_path"], r["variant_path"])
        s, ts = timed3(f)
        res.update(score_s=s, repeats_s=ts, note="cold file cache per repeat (parses both files of each pair)")
    elif method in ("execstats", "traceseq", "pathspectra", "valuespectra", "oracle_output_reading"):
        import b03_execstats
        import b04_valuespectra
        import b05_pathspectra
        import b05_traceseq
        from bl_common import FileTrace
        t = time.perf_counter()
        pairs = [(FileTrace(pop, r["base_id"], r["base_path"]), FileTrace(pop, r["base_id"], r["variant_path"])) for r in rows]
        res["trace_load_s"] = time.perf_counter() - t
        res["trace_load_ms_per_pair"] = 1000 * res["trace_load_s"] / len(rows)
        with open(RAW / EXP_FEAT / "idf.pkl", "rb") as fh:
            idf = pickle.load(fh)["trace"]
        fn = {"execstats": lambda a, b: b03_execstats.exec_features(a, b), "traceseq": lambda a, b: b05_traceseq.pair_features(a, b, idf),
              "pathspectra": lambda a, b: b05_pathspectra.pair_features(a, b), "valuespectra": lambda a, b: b04_valuespectra.pair_features(a, b),
              "oracle_output_reading": lambda a, b: b03_execstats.oracle_features(a, b)}[method]
        s, ts = timed3(lambda: [fn(a, b) for a, b in pairs])
        res.update(score_s=s, repeats_s=ts)
    elif method == "output_indep_run":
        import b06_indep_inputs as B6
        from bl_common import cache_file
        bat_dir = RAW / EXP_FEAT / "indep" / "batteries"
        tmp = pathlib.Path("/tmp/a4c_rt")
        tmp.mkdir(exist_ok=True)
        t = time.perf_counter()
        n_files = 0
        for r in rows:
            bat = bat_dir / f"{pop}__{r['base_id']}.json"
            if not bat.exists() or json.loads(bat.read_text()).get("status") != "ok":
                continue
            for p in (r["base_path"], r["variant_path"]):
                ent = json.load(gzip.open(cache_file(pop, r["base_id"], p), "rt"))["entry_function"]
                B6.run_file(p, ent, str(bat), str(tmp / "o.json"))
                n_files += 1
        res.update(score_s=time.perf_counter() - t, n_files_executed=n_files, note="in-process execution of <=40 inputs on base+variant; excludes ~30-40 ms interpreter start per file; battery generation measured separately")
    elif method == "output_indep_battery_gen":
        import b06_indep_inputs as B6
        bat_dir = RAW / EXP_FEAT / "indep" / "batteries"
        tmp = pathlib.Path("/tmp/a4c_rt")
        tmp.mkdir(exist_ok=True)
        from bl_common import cache_file
        progs = {}
        for r in rows:
            progs[r["base_id"]] = r["base_path"]
        t = time.perf_counter()
        for b, p in progs.items():
            ent = json.load(gzip.open(cache_file(pop, b, p), "rt"))["entry_function"]
            B6.make_battery(p, ent, b, str(tmp / "bat.json"))
        el = time.perf_counter() - t
        res.update(score_s=el, n_programs=len(progs), note="battery generation is per PROGRAM (amortised over its pairs); score_s/n_pairs is the amortised cost over the 50-pair sample")
    elif method == "combiners_LR_RF":
        fc = RAW / C.EXP_FIT
        with open(fc / "models.pkl", "rb") as fh:
            Mdl = pickle.load(fh)
        X = [[float(r["edit"]), r["scores"]["exception_fraction"], r["scores"]["call_count"], r["scores"]["coverage_size"], r["scores"]["n_functions"], 0.0, 0.0] for r in rows]
        lr = Mdl[("lr", ("edit", "exception_fraction", "call_count", "coverage_size"))]
        rf = Mdl[("tree", "forest|RF_d4|EXx")]
        s, ts = timed3(lambda: [(eval_lib.logit_score(lr, x[:4]), rf["model"].predict(x[:len(rf["feats"])])) for x in X])
        res.update(score_s=s, repeats_s=ts, note="scoring only (given feature values); fit cost is a one-off on v9c_train")
    elif method == "sbg_extract_and_score":
        sys.path.insert(0, str(REPO))
        os.chdir(REPO)
        t_imp = time.perf_counter()
        from experiments.final import extraction as ex
        res["import_s"] = time.perf_counter() - t_imp
        ext = sc = 0.0
        for r in rows:
            cache = {}
            t = time.perf_counter()
            A = ex.extract_program(str(REPO / r["base_path"]), cache, "output_free_v8")
            B = ex.extract_program(str(REPO / r["variant_path"]), cache, "output_free_v8")
            ext += time.perf_counter() - t
            t = time.perf_counter()
            ex.score_pair(A, B)
            sc += time.perf_counter() - t
        res.update(extract_s=ext, score_s=sc, extract_ms_per_pair=1000 * ext / len(rows), note="score_s = distance only (frozen score_pair); extract_s = uncached frozen extraction of base+variant")
        res["total_s"] = ext + sc
    res["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    res["python"] = sys.version.split()[0]
    print("@@" + json.dumps(res))


def cache_extraction_summary(pop):
    ex = []
    for f in glob.glob(str(RAW / "trace_cache" / pop / "*" / "*.json.gz")):
        ex.append(json.load(gzip.open(f, "rt")).get("extract_seconds") or 0.0)
    ex.sort()
    dl = RAW / "trace_cache" / pop / "DUMP_LOG.json"
    dump = json.loads(dl.read_text()) if dl.exists() else []
    return {"pop": pop, "n_files": len(ex), "sum_s": sum(ex), "mean_s": sum(ex) / len(ex), "median_s": ex[len(ex) // 2], "p95_s": ex[int(0.95 * len(ex))], "max_s": ex[-1],
            "dump_log_programs": len(dump), "dump_log_sum_s_of_nonskipped": sum(d.get("seconds", 0) for d in dump if d.get("status") == "ok")}


def driver(pop, extra_methods):
    out = RAW / EXP_RT
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
    allres = []
    for m in METHODS + extra_methods:
        t = time.perf_counter()
        o = subprocess.run([sys.executable, str(HERE / "runtime_a4c.py"), "--worker", m, "--pop", pop], capture_output=True, text=True, env=env, timeout=1500)
        line = [l for l in o.stdout.splitlines() if l.startswith("@@")]
        if not line:
            print("FAILED", m, o.stderr[-500:])
            allres.append({"method": m, "error": o.stderr[-500:]})
            continue
        r = json.loads(line[0][2:])
        r["subprocess_wall_s"] = time.perf_counter() - t
        n = r["n_pairs"]
        r["score_ms_per_pair"] = 1000 * r["score_s"] / n
        r["peak_rss_MB"] = r["peak_rss_bytes"] / 1e6
        r["rss_over_interpreter_MB"] = (r["peak_rss_bytes"] - r["rss_interpreter_start_bytes"]) / 1e6
        allres.append(r)
        print(m, {k: round(v, 3) if isinstance(v, float) else v for k, v in r.items() if k not in ("repeats_s", "note")})
    (out / f"runtime_{pop}.json").write_text(json.dumps({"population": pop, "n": N, "results": allres, "cache_extraction": cache_extraction_summary(pop)}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker")
    ap.add_argument("--pop", default="v10_test")
    ap.add_argument("--extra", default="")
    a = ap.parse_args()
    if a.worker:
        worker(a.worker, a.pop)
    else:
        driver(a.pop, [m for m in a.extra.split(",") if m])
