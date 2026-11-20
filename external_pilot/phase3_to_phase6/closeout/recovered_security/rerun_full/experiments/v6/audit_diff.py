"""Item 5: observed output equivalence vs semantic equivalence; item 2 SC-6 decomposition. DEV only -> artifacts/v6/audit/DIFF_SC6_AUDIT.json"""
import json, sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from experiments.v6.evaluate import *   # noqa
df = load(["v8train", "v8val"]); y = df.label.values.astype(int); g = df.base_id.values; t = df.transformation_type
res = {}
res["delta_out_auroc"] = {"all": auroc(y, neutral(df, "delta_out").values), "ci95": list(cluster_boot(y, neutral(df, "delta_out").values, g, B=2000))}
res["per_type_output_diff_rate"] = {k: float((v > 0).mean()) for k, v in df.groupby("transformation_type").delta_out}
# Output-diff among pairs labelled EQUIVALENT: label noise or genuine behaviour change in 'semantics-preserving' generators
res["equiv_labelled_with_output_diff_by_type"] = {k: int(((df.delta_out > 0) & (t == k)).sum()) for k in sorted(set(t[y == 0]))}
# Upper bound on how much of the 0.805 depends on finite inputs: pairs labelled CHANGED with delta_out==0 are indistinguishable by observation
nd = ((df.delta_out == 0) & (y == 1)); res["changed_without_observed_diff"] = {"n": int(nd.sum()), "of": int((y == 1).sum()),
    "by_type": {k: int(((df.delta_out == 0) & (t == k)).sum()) for k in sorted(set(t[y == 1]))}}
# Sensitivity: how AUROC of delta_out moves if the unobserved-diff mutants were (a) all genuinely changed (as labelled) vs (b) dropped as possibly equivalent
s = neutral(df, "delta_out").values
res["delta_out_auroc_if_unobserved_changed_dropped"] = auroc(y[~nd.values], s[~nd.values])
res["delta_out_auroc_if_output_differing_equiv_dropped"] = auroc(y[~((df.delta_out > 0) & (y == 0)).values], s[~((df.delta_out > 0) & (y == 0)).values])
res["delta_out_auroc_both_dropped"] = (lambda m: auroc(y[m], s[m]))(~(nd.values | ((df.delta_out > 0) & (y == 0)).values))
# SC-6 decomposition
sc6 = (t == "SC-6").values; eq = y == 0
tr_neutral = t.isin(["SP-1", "SP-2", "SP-4", "SP-6", "SP-9"]).values
r = {"n": int(sc6.sum()), "d_v6_zero_frac": float((df.d_v6[sc6] == 0).mean()), "v5_zero_frac": float((df.sbg_v5[sc6] == 0).mean()),
     "status": df.status.value_counts().to_dict() if False else None}
for c in ("d_v6", "sbg_v5", "d_R", "delta_out"):
    v = neutral(df, c).values
    r[f"auroc_vs_all_equiv|{c}"] = auroc(y[sc6 | eq], v[sc6 | eq]); r[f"auroc_vs_trace_neutral_equiv|{c}"] = auroc(y[sc6 | tr_neutral], v[sc6 | tr_neutral])
# Tie-mass decomposition: AUROC = P(s1>s0)+.5P(tie). Contribution of each equivalent type
v = neutral(df, "d_v6").values; a = v[sc6]
r["pairwise_vs_equiv_type"] = {k: {"P(sc6>eq)": float((a[:, None] > v[(t == k).values][None]).mean()), "P(tie)": float((a[:, None] == v[(t == k).values][None]).mean())} for k in sorted(set(t[eq]))}
# SC-6 coverage of return-value change: does the return actually differ whenever d_R>0? is d_R informative on SC-6 only (not on equivalents)?
r["d_R_equiv_nonzero_frac"] = float((df.d_R[eq] > 0).mean())
res["SC6"] = r
json.dump(res, open(REPO / "artifacts/v6/audit/DIFF_SC6_AUDIT.json", "w"), indent=1, default=float)
print(json.dumps({k: v for k, v in res.items() if k != "SC6"}, indent=1)[:2500]); print(json.dumps(res["SC6"], indent=1)[:3000])
