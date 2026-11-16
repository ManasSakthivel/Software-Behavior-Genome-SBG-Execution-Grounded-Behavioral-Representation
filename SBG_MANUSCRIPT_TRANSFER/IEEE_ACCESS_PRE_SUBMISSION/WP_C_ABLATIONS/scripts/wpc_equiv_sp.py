#!/usr/bin/env python3
"""EXP-WPC-005d: false-positive mass on EQUIVALENT pairs, by semantics-preserving (SP) transform, derived from the `group` id
(`<split>__<prog>__sp-N_sK`).  Replaces the degenerate `equiv_by_sp_type` block of EXP-WPC-005 (sp_type column is blank on
label-0 rows; that block is kept un-edited and flagged in the registry).  Permitted data only (v9c_train minus math_gray_code, v9c_dev).
Descriptive / exploratory; uses labels only to split EQUIVALENT vs CHANGED (the pair-label is part of the dev/train data).
"""
from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve()
WPC = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(WPC.parent / "experiments" / "common"))
import eval_lib as E                                                   # noqa: E402
import wpc_ablation as A                                               # noqa: E402

OUT = WPC / "raw" / "EXP-WPC-005" / "equiv_by_sp_from_group.json"


def main():
    if OUT.exists():
        sys.exit("refusing to overwrite " + str(OUT))
    rows = A.read("v9c_train") + A.read("v9c_dev")
    V = A.variant_scores(rows)
    names = ["full", "state_raw", "v3_only", "temporal", "call_topology", "bigrams", "exception", "coverage_resid"]
    sp = [re.search(r"__(sp-\d+)_s\d+$", r["group"]).group(1).upper() for r in rows]
    res = {}
    for t in sorted({s for s in sp}, key=lambda x: int(x.split("-")[1])):
        eq = [i for i, r in enumerate(rows) if r["label"] == 0 and sp[i] == t]
        ch = [i for i, r in enumerate(rows) if r["label"] == 1 and sp[i] == t]
        d = {"n_equiv": len(eq), "n_changed": len(ch), "n_programs": len({rows[i]["base_id"] for i in eq})}
        for n in names:
            s = V[n]
            d[n] = {"equiv_nonzero_rate": sum(1 for i in eq if s[i] > 0) / len(eq), "equiv_mean": sum(s[i] for i in eq) / len(eq),
                    "changed_nonzero_rate": sum(1 for i in ch if s[i] > 0) / len(ch), "changed_mean": sum(s[i] for i in ch) / len(ch)}
        yy = [rows[i]["label"] for i in eq + ch]
        for n in ("full", "state_raw"):
            d[n]["auroc_within_sp_type"] = E.auroc([V[n][i] for i in eq + ch], yy)
        res[t] = d
    # total equivalent mass by component (sum of mean scores over equivalents): where does V5's false-positive mass come from?
    eqs = [i for i, r in enumerate(rows) if r["label"] == 0]
    tot = {n: sum(V[n][i] for i in eqs) / len(eqs) for n in ["call_topology", "bigrams", "exception", "coverage_resid", "temporal", "state", "full"]}
    json.dump({"n_pairs": len(rows), "by_sp_type": res, "mean_equiv_score_by_component": tot}, open(OUT, "w"), indent=1)
    print(f"{'SP':6s} nEq  " + "  ".join(f"{n[:9]:>9s}" for n in names) + "   (equiv nonzero-rate / mean)")
    for t, d in res.items():
        print(f"{t:6s} {d['n_equiv']:4d} " + "  ".join(f"{d[n]['equiv_nonzero_rate']:.2f}/{d[n]['equiv_mean']:.3f}" for n in names),
              f" AUROC within: full {d['full']['auroc_within_sp_type']:.3f} state {d['state_raw']['auroc_within_sp_type']:.3f}")
    print(tot)


if __name__ == "__main__":
    main()
