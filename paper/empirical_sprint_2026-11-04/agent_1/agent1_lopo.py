#!/usr/bin/env python3
"""Agent 1 supplement (post-hoc, exploratory): leave-one-program-out (LOPO) sensitivity of pooled paired deltas AUROC(full V5) - AUROC(ablation).
Reuses populations/loaders from agent1_ablation.py (read-only on repo). Writes lopo_sensitivity.csv in this directory.

  PYTHONDONTWRITEBYTECODE=1 /Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python \
      /Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/paper/empirical_sprint_2026-11-04/agent_1/agent1_lopo.py
"""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import agent1_ablation as A                                    # noqa: E402
from sbg.statistics import auroc                               # noqa: E402

CONTRASTS = ("V5_minus_V3", "V5_minus_temporal", "V5_minus_state", "V3_only", "temporal_only", "state_only")
rows_out = []
for tag, loader in (("V10_test", A.load_v10), ("V9c_val", A.load_v9c_val)):
    pop = loader()[0]
    progs = sorted({r["base_id"] for r in pop})
    for n in CONTRASTS:
        full = A.arr(pop, "full_V5")
        abl = A.arr(pop, n)
        y = [r["label"] for r in pop]
        pooled = auroc(full, y) - auroc(abl, y)
        ds = []
        for p in progs:
            keep = [i for i, r in enumerate(pop) if r["base_id"] != p]
            yy = [y[i] for i in keep]
            d = auroc([full[i] for i in keep], yy) - auroc([abl[i] for i in keep], yy)
            ds.append((p, d))
        vals = [d for _, d in ds]
        worst = max(ds, key=lambda t: abs(t[1] - pooled))
        rows_out.append([tag, n, f"{pooled:.6f}", f"{min(vals):.6f}", f"{max(vals):.6f}", "same" if (min(vals) > 0) == (max(vals) > 0) and (min(vals) > 0 or max(vals) < 0) else "SIGN CHANGES",
                         worst[0], f"{worst[1]:.6f}"])
with open(HERE / "lopo_sensitivity.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["population", "contrast_full_minus", "pooled_delta", "lopo_min", "lopo_max", "sign_stability_across_LOPO", "most_influential_program_dropped", "delta_without_it"])
    w.writerows(rows_out)
for r in rows_out:
    print(*r)
