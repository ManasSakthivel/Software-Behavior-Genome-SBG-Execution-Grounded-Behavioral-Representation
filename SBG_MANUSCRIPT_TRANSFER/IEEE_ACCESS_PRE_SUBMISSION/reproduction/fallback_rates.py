#!/usr/bin/env python3
"""A2: how often do the silent fallbacks (temporal/state -> d_V3; V5 -> d_V3; unevaluated) fire in the FROZEN scored files?
Reads REPO read-only. Output: PKG/results/raw/repro/fallback_rates_frozen.json"""
import json, pathlib, collections
PKG = pathlib.Path(__file__).resolve().parents[1]; REPO = PKG.parent / "SBG"; OUT = PKG / "results/raw/repro"
def jl(p): return [json.loads(l) for l in open(p) if l.strip()]
pops = json.load(open(PKG / "configs/populations/v9c_val.json")); 
def load_pop(n): return {r["pair_id"]: r for r in json.load(open(PKG / f"configs/populations/{n}.json"))["rows"]}
src = {
 "v10_test": [REPO / "artifacts/final/pairs_v10_test_v6exp.jsonl"],
 "v9c_val": [REPO / "artifacts/final/pairs_v9c_val_output_free_v8.jsonl", REPO / "artifacts/final/pairs_v8val_output_free_v8.jsonl"],
 "v9c_dev": [REPO / "artifacts/final/pairs_v9c_dev_output_free_v8.jsonl", REPO / "artifacts/final/pairs_v8dev_output_free_v8.jsonl", REPO / "artifacts/final/pairs_v8devrescore_output_free_v8.jsonl"],
 "v9c_train": [REPO / "artifacts/final/pairs_v9c_train_output_free_v8.jsonl", REPO / "artifacts/final/pairs_v8train_output_free_v8.jsonl"],
}
out = {}
for name, files in src.items():
    pop = load_pop(name)
    rows = {}
    for f in files:
        if not f.exists(): continue
        for r in jl(f):
            rows.setdefault(r["pair_id"], r)
    res = collections.Counter(); per_prog = collections.defaultdict(collections.Counter)
    missing = 0
    for pid, p in pop.items():
        r = rows.get(pid)
        if r is None: missing += 1; continue
        prim = p["in_primary_population"]
        tag = "primary" if prim else "nonprimary"
        res[f"{tag}:rows"] += 1
        if not r.get("evaluated"): res[f"{tag}:unevaluated"] += 1; continue
        sc = r["scores"]
        v5f = sc.get("v5_full")
        if v5f != 1.0:
            res[f"{tag}:v5_full!=1 (fallback to d_V3)"] += 1; per_prog[p["base_id"]][f"{tag}:fallback"] += 1
        if sc["sbg_temporal"] == sc["sbg_v3"] and sc["sbg_state"] == sc["sbg_v3"] and sc["sbg_v3"] != 0.0:
            res[f"{tag}:temporal==state==v3 nonzero (fallback signature)"] += 1
        if sc["sbg_v5"] == 0.0: res[f"{tag}:sbg_v5 exactly 0"] += 1
    out[name] = dict(sources=[str(f.relative_to(REPO)) for f in files if f.exists()], population_rows=len(pop), rows_not_found_in_scored_files=missing,
                     counts=dict(res), fallback_by_program={k: dict(v) for k, v in per_prog.items()})
(OUT / "fallback_rates_frozen.json").write_text(json.dumps(out, indent=1))
print(json.dumps({k: v["counts"] | {"missing": v["rows_not_found_in_scored_files"]} for k, v in out.items()}, indent=1))
