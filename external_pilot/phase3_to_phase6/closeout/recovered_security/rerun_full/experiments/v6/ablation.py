"""DEV ablations / architecture-family comparison (seed 42 only, to bound runtime). Same folds & model families as evaluate.py.
  python experiments/v6/ablation.py  -> artifacts/v6/ABLATION_dev.json
"""
import json, sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from experiments.v6.evaluate import *   # noqa

CONVC = STAT + ["edit_lines"] + EXV
CFG = ["cfg0", "cfg1", "cfg2"]
EVID = ["alpha", "conf", "st_act", "st_nact", "st_unk"]
SETS = {  # name -> columns
    "FAM-A invariants": ["d_A"], "FAM-B transitions": ["d_B", "g"], "FAM-C graph": ["d_C"] + CFG,
    "FAM-E activation/evidence": EVID + ["g"], "FAM-D hybrid (V6 full)": V6C,
    "V6 -A": [c for c in V6C if c != "d_A"], "V6 -B": [c for c in V6C if c not in ("d_B", "g")],
    "V6 -C": [c for c in V6C if c not in ["d_C"] + CFG], "V6 -evidence(E)": [c for c in V6C if c not in EVID + ["g"]],
    "V6 +temporal(V5)": V6C + ["sbg_temporal"], "V6 +V5 state": V6C + ["sbg_state"], "V6 +R(return)": V6C + ["d_R"],
    "V6 -cfg_size (normalisation-free)": [c for c in V6C if c not in CFG],
}
def main():
    df = load(["v8train", "v8val"]); y, g = df.label.values.astype(int), df.base_id.values
    out = {}
    for ctx, base in (("alone", []), ("CONV+", CONVC)):
        for name, cols in SETS.items():
            if ctx == "CONV+" and name.startswith("FAM-") and name != "FAM-D hybrid (V6 full)" and False: continue
            X = df[base + cols].values
            for kind in ("LR", "GBM"):
                oof = np.zeros(len(df))
                for tr, te in folds(g, 42):
                    oof[te] = fit_predict(kind, X[tr], y[tr], g[tr], X[te])[0]
                out[f"{ctx}{name}|{kind}"] = {"auroc": auroc(y, oof), "ci95": list(cluster_boot(y, oof, g, B=500))}
                print(f"{ctx:6s}{name:36s}{kind:4s} {out[f'{ctx}{name}|{kind}']['auroc']:.3f}", flush=True)
    for kind in ("LR", "GBM"):
        oof = np.zeros(len(df))
        for tr, te in folds(g, 42):
            oof[te] = fit_predict(kind, df[CONVC].values[tr], y[tr], g[tr], df[CONVC].values[te])[0]
        out[f"CONV (ref)|{kind}"] = {"auroc": auroc(y, oof)}
    json.dump(out, open(pathlib.Path(__file__).resolve().parents[2] / "artifacts/v6/ABLATION_dev.json", "w"), indent=1)
main()
