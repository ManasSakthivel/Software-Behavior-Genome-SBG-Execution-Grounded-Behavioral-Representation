#!/usr/bin/env python3
"""A4 head-to-head benchmark driver.  Stages (see README.md / PKG/06_COMPARATIVE_BENCHMARK_REPRODUCTION.md):

  idf        fit unsupervised IDF tables on v9c_train sources/traces            -> results/raw/EXP-A4-002/idf.pkl
  features   label-free baseline scores for every primary pair of a population  -> results/raw/EXP-A4-002/features_<pop>.json
  indep      independent-input batteries + execution + pair scores             -> results/raw/EXP-A4-003/
  fit        fit on v9c_train, select on v9c_dev (frozen config)               -> results/raw/EXP-A4-004/
  heldout    score v9c_val and v10_test ONCE with the frozen config            -> results/raw/EXP-A4-005/
  incremental  incremental-value matrix                                        -> results/raw/EXP-A4-006/
  (runtime.py: EXP-A4-007; make_report.py: tables)
Run with: PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 <py313> run_benchmark.py --stage <stage> [--pop P]
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import gzip
import hashlib
import json
import multiprocessing
import pathlib
import pickle
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bl_common import FileTrace, POPS, PKG, cache_file, eval_lib  # noqa: E402
import features as F  # noqa: E402
import b06_indep_inputs as B6  # noqa: E402

RAW = PKG / "results" / "raw"
PY = sys.executable
WORKERS = 4


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def stage_idf():
    rows = eval_lib.load_population("v9c_train")
    t = time.time()
    idf = F.fit_idfs(rows)
    out = RAW / "EXP-A4-002" / "idf.pkl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump(idf, f)
    print("idf fitted on", len(rows), "train rows in", round(time.time() - t, 1), "s ->", out)


def stage_features(pop):
    rows = eval_lib.load_population(pop)
    by = collections.defaultdict(list)
    for r in rows:
        by[r["base_id"]].append(r)
    jobs = [(pop, by[b]) for b in sorted(by)]
    t = time.time()
    res, ext = {}, {}
    with multiprocessing.Pool(WORKERS, initializer=F.init_worker, initargs=(str(RAW / "EXP-A4-002" / "idf.pkl"),)) as pool:
        for o in pool.imap_unordered(F.compute_program, jobs):
            res.update(o["features"])
            ext.update(o["extract_seconds"])
            print(f"  {o['base_id']:34s} {len(o['features']):4d} pairs {o['seconds']:.1f}s", flush=True)
    out = RAW / "EXP-A4-002" / f"features_{pop}.json"
    out.write_text(json.dumps(res))
    (RAW / "EXP-A4-002" / f"extract_seconds_{pop}.json").write_text(json.dumps(ext))
    n_bad = sum(1 for v in res.values() if not v.get("_trace_ok"))
    print(f"{pop}: {len(res)} pairs, trace-missing {n_bad}, {time.time() - t:.0f}s -> {out}")


# ------------------------------------------------------------------ independent inputs
def _entry_of(pop, base_id, path):
    with gzip.open(cache_file(pop, base_id, path), "rt") as f:
        return json.load(f).get("entry_function")


def _sub(cmd, timeout):
    t = time.time()
    try:
        o = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env={"PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"},
                           cwd=str(HERE))
        return o.returncode, o.stderr[-300:], time.time() - t
    except subprocess.TimeoutExpired:
        return -9, "TIMEOUT", time.time() - t


def _runfile(root, pop, base_id, path):
    return root / "runs" / pop / base_id / (hashlib.sha1(path.encode()).hexdigest()[:12] + "__" + pathlib.Path(path).stem + ".json")


def stage_indep(pops):
    root = RAW / "EXP-A4-003"
    (root / "batteries").mkdir(parents=True, exist_ok=True)
    log = []
    for pop in pops:
        rows = eval_lib.load_population(pop)
        bases = {}
        for r in rows:
            if cache_file(pop, r["base_id"], r["base_path"]).exists():  # programs without a trace-cache entry (train: math_gray_code) are excluded everywhere
                bases.setdefault(r["base_id"], r["base_path"])
        jobs = []
        for b, p in sorted(bases.items()):
            out = root / "batteries" / f"{pop}__{b}.json"
            if not out.exists():
                jobs.append((b, [PY, str(HERE / "b06_indep_inputs.py"), "battery", p, _entry_of(pop, b, p), b, str(out)]))
        with concurrent.futures.ThreadPoolExecutor(WORKERS) as ex:
            for (b, _), (rc, err, dt) in zip(jobs, ex.map(lambda j: _sub(j[1], 300), jobs)):
                log.append({"pop": pop, "base": b, "stage": "battery", "rc": rc, "err": err, "s": round(dt, 2)})
                if rc:
                    print("battery FAIL", pop, b, err)
        files = {}
        for r in rows:
            if r["base_id"] not in bases:
                continue
            for k in ("base_path", "variant_path"):
                files[(r["base_id"], r[k])] = None
        rjobs = []
        for (b, p) in sorted(files):
            bat = root / "batteries" / f"{pop}__{b}.json"
            if not bat.exists() or json.loads(bat.read_text())["status"] != "ok":
                continue
            out = _runfile(root, pop, b, p)
            out.parent.mkdir(parents=True, exist_ok=True)
            if not out.exists():
                rjobs.append((out, [PY, str(HERE / "b06_indep_inputs.py"), "run", p, _entry_of(pop, b, p) or "", str(bat), str(out)]))
        t0 = time.time()
        with concurrent.futures.ThreadPoolExecutor(WORKERS) as ex:
            for (out, _), (rc, err, dt) in zip(rjobs, ex.map(lambda j: _sub(j[1], 120), rjobs)):
                if rc or not out.exists():
                    out.write_text(json.dumps({"status": f"worker_fail:{rc}:{err}", "per_input": [], "n": 0, "wall_parent_s": dt}))
                    log.append({"pop": pop, "file": str(out.name), "rc": rc, "err": err})
                else:
                    d = json.loads(out.read_text())
                    d["wall_parent_s"] = dt
                    out.write_text(json.dumps(d))
        print(f"{pop}: ran {len(rjobs)} files in {time.time() - t0:.0f}s")
        scores, n_cov = {}, 0
        for r in rows:
            bat = root / "batteries" / f"{pop}__{r['base_id']}.json"
            if r["base_id"] not in bases or not bat.exists() or json.loads(bat.read_text())["status"] != "ok":
                continue
            ra = json.loads(_runfile(root, pop, r["base_id"], r["base_path"]).read_text())
            rb = json.loads(_runfile(root, pop, r["base_id"], r["variant_path"]).read_text())
            s = B6.pair_scores(ra, rb)
            if s:
                scores[r["pair_id"]] = s
                n_cov += 1
        (root / f"indep_{pop}.json").write_text(json.dumps(scores))
        print(f"{pop}: indep-covered pairs {n_cov}/{len(rows)}")
    (root / f"indep_log_{'_'.join(pops)}.json").write_text(json.dumps(log, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--pop", default=None)
    a = ap.parse_args()
    pops = [a.pop] if a.pop else list(POPS)
    if a.stage == "idf":
        stage_idf()
    elif a.stage == "features":
        for p in pops:
            stage_features(p)
    elif a.stage == "indep":
        stage_indep(pops)
    else:
        import stages_eval
        stages_eval.run(a.stage, pops)
