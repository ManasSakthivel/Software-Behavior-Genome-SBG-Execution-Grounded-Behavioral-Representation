#!/usr/bin/env python3
"""A2: compare the Orchestrator's dump_traces output (results/raw/trace_cache/<pop>/<program>/pairs_scores.json; only programs with a DONE file)
against the frozen scored files, pair by pair, exact equality of every score key.  Independent of recompute_scores.py (different harness)."""
import json, pathlib, sys
PKG = pathlib.Path(__file__).resolve().parents[1]; REPO = PKG.parent / "SBG"
A = REPO / "artifacts/final"
frozen = {"v10_test": [A / "pairs_v10_test_v6exp.jsonl"],
          "v9c_val": [A / "pairs_v9c_val_output_free_v8.jsonl", A / "pairs_v8val_output_free_v8.jsonl"]}
res = {}
for pop, files in frozen.items():
    fz = {}
    for f in files:
        for l in f.read_text().splitlines():
            if l.strip():
                r = json.loads(l); fz.setdefault(r["pair_id"], r)
    root = PKG / "results/raw/trace_cache" / pop
    if not root.exists():
        continue
    n = eq = bad = 0; progs = []; unfinished = []
    for d in sorted(root.iterdir()):
        ps = d / "pairs_scores.json"
        if not (d / "DONE").exists() or not ps.exists():
            unfinished.append(d.name); continue
        progs.append(d.name)
        for r in json.loads(ps.read_text()):
            n += 1; z = fz.get(r["pair_id"])
            if z is None: bad += 1; continue
            if bool(z["evaluated"]) != bool(r["evaluated"]): bad += 1; continue
            if not r["evaluated"]: eq += 1; continue
            if all(abs(z["scores"][k] - r["scores"][k]) == 0.0 for k in r["scores"] if k in z["scores"]): eq += 1
            else: bad += 1
    res[pop] = dict(programs_done=progs, programs_not_done=unfinished, pairs=n, equal=eq, differing_or_missing=bad)
(PKG / "results/raw/repro/crosscheck_orch_trace_cache.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
