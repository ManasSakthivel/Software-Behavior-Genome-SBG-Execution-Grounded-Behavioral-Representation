#!/usr/bin/env python3
"""A2: per-FILE extraction-level fallback / truncation census from the recompute outputs (stats written by experiments.final.extraction)."""
import json, glob, collections, pathlib
R = pathlib.Path(__file__).resolve().parents[1] / "results/raw/repro"
out = {}
for n in ["recompute_v10_py313_seed0", "recompute_v9cval_py313_seed0"]:
    c = collections.Counter(); fk = collections.Counter(); tr = bud = nf = 0
    for f in glob.glob(str(R / n / "*.json")):
        j = json.load(open(f))
        if "files" not in j: continue
        for p, i in j["files"].items():
            nf += 1; fk[f"ok={i['ok']} kind={i['failure_kind']}"] += 1
            s = i["stats"]
            if s:
                c[f"temporal={s['temporal_available']} state={s['state_available']}"] += 1
                bud += bool(s["program_budget_exceeded"]); tr += bool(s["n_truncated_traces"])
    out[n] = dict(files=nf, layers_available=dict(c), outcomes=dict(fk), files_with_truncated_traces=tr, program_budget_exceeded=bud)
(R / "fallback_files_recompute.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
