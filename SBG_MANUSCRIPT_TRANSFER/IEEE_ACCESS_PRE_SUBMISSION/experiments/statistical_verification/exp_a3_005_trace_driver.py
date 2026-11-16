#!/usr/bin/env python3
"""EXP-A3-005 driver: run the (read-only-on-REPO) trace dump worker for missing programs into an A3-owned dir.
Reuses PKG/results/raw/trace_cache/<design>_<split>/<prog> if it already has DONE, else runs
experiments/common/dump_traces.py --worker into results/raw/EXP-A3-005/trace_cache/<design>_<split>/<prog>.
usage: exp_a3_005_trace_driver.py design split [workers]"""
import concurrent.futures, json, os, pathlib, subprocess, sys, time
PKG = pathlib.Path(__file__).resolve().parents[2]
REPO = PKG.parent / "SBG"
design, split = sys.argv[1], sys.argv[2]
workers = int(sys.argv[3]) if len(sys.argv) > 3 else 2
DUMP = PKG / "experiments/common/dump_traces.py"
sys.path.insert(0, str(PKG / "experiments/common"))
def jl(p): return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]
if design == "v10":
    pairs = jl(REPO / "benchmark/datasets/v10_independent/pairs_test.jsonl")
else:
    meta = {m["pair_id"]: m for m in jl(REPO / f"benchmark/datasets/v9_composed/pairs_{split}.jsonl")}
    v8 = {m["pair_id"]: m for m in jl(REPO / f"benchmark/datasets/v8/pairs_{split}.jsonl")}
    for m in list(meta.values()): meta[m["matched_equivalent_pair_id"]] = v8[m["matched_equivalent_pair_id"]]
    pairs = list(meta.values())
progs = sorted({p["base_id"] for p in pairs})
orch = PKG / "results/raw/trace_cache" / f"{design}_{split}"
mine = PKG / "results/raw/EXP-A3-005/trace_cache" / f"{design}_{split}"
mine.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
def run(pr):
    if (orch / pr / "DONE").exists(): return pr, "orch-done", 0
    od = mine / pr
    if (od / "DONE").exists(): return pr, "mine-done", 0
    t0 = time.time()
    o = subprocess.run([sys.executable, str(DUMP), "--design", design, "--split", split, "--worker", pr, "--outdir", str(od)],
                       env=env, capture_output=True, text=True, timeout=3600)
    return pr, ("ok" if (od / "DONE").exists() else f"FAILED {o.stderr[-300:]}"), time.time() - t0
with concurrent.futures.ThreadPoolExecutor(workers) as pool:
    for pr, st, dt in pool.map(run, progs):
        print(f"{pr:40s} {st} {dt:.1f}s", flush=True)
print("ALLDONE", flush=True)
