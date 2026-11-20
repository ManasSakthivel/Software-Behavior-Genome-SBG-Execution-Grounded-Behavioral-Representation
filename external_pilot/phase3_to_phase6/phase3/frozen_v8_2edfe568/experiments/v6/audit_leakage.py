"""DEV leakage audit of the CONV/EDIT GBM result (items 3,4). seed 42 only; exploratory. -> artifacts/v6/audit/LEAKAGE_AUDIT.json"""
import json, hashlib, sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from experiments.v6.evaluate import *   # noqa
OUT = REPO / "artifacts/v6/audit"; OUT.mkdir(exist_ok=True)
df = load(["v8train", "v8val"]); y = df.label.values.astype(int); g = df.base_id.values
df["fam"] = df.base_id.str.split("_").str[0]; t = df.transformation_type.values
res = {}
# 1. label is a deterministic function of mutation family -> type-identity oracle
res["label_pure_function_of_type"] = bool((df.groupby("transformation_type").label.nunique() == 1).all())
# 2. duplicates: identical variant source across pairs; identical feature vectors with conflicting labels
h = []
for n, f in (("train", "pairs_train"), ("val", "pairs_val")):
    for l in open(REPO / f"benchmark/datasets/v8/{f}.jsonl"):
        r = json.loads(l); p = REPO / r["variant_path"]
        h.append((r["pair_id"], hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None))
hh = dict(h); df["vh"] = df.pair_id.map(hh)
res["variant_files_missing"] = int(df.vh.isna().sum())
d = df.dropna(subset=["vh"]).groupby("vh").agg(n=("pair_id", "size"), nl=("label", "nunique"), ng=("base_id", "nunique"))
res["duplicate_variant_groups"] = int((d.n > 1).sum()); res["dup_variants_label_conflict"] = int((d.nl > 1).sum())
res["dup_variants_rows"] = int(d[d.n > 1].n.sum()); res["dup_variants_cross_program"] = int((d.ng > 1).sum())
cols = STAT + ["edit_lines"] + EXV
fv = df[cols].round(8).astype(str).apply(lambda r: "|".join(map(str, r)), axis=1)
dd = df.assign(fv=fv).groupby("fv").agg(n=("label", "size"), nl=("label", "nunique"))
res["dup_CONV_vectors_groups"] = int((dd.n > 1).sum()); res["dup_CONV_vectors_label_conflict"] = int((dd.nl > 1).sum())
# fraction of rows whose CONV vector is duplicated in another program (cross-fold leak candidate)
res["rows_with_duplicate_CONV_vector"] = int(dd[dd.n > 1].n.sum())
# 3. CV schemes for GBM
def cv(cols, splits):
    X = df[cols].values; oof = np.full(len(df), np.nan)
    for tr, te in splits:
        oof[te] = fit_predict("GBM", X[tr], y[tr], g[tr], X[te])[0]
    return oof
fam_splits = [(np.where(df.fam != f)[0], np.where(df.fam == f)[0]) for f in sorted(df.fam.unique())]
SC = sorted(set(t[y == 1])); SP = sorted(set(t[y == 0]))
tf = {}   # fold -> held-out types (both classes in every fold; round-robin)
for i, ty in enumerate(SC): tf.setdefault(i % 4, []).append(ty)
for i, ty in enumerate(SP): tf.setdefault(i % 4, []).append(ty)
type_splits = [(np.where(~np.isin(t, v))[0], np.where(np.isin(t, v))[0]) for v in tf.values()]
res["type_holdout_folds"] = {str(k): v for k, v in tf.items()}
sets = {"EDIT": STAT + ["edit_lines"], "edit_lines_only": ["edit_lines"], "static_token_only": ["static_token"], "EXECVOL": EXV,
        "CONV": cols, "V6": V6C, "CONV+V6": cols + V6C, "V5": V5C, "CONV+V5": cols + V5C}
for name, c in sets.items():
    r = {}
    for sch, sp in (("program_grouped", folds(g, 42)), ("family_grouped(leave-program-domain-out)", fam_splits), ("leave-mutation-types-out", type_splits)):
        o = cv(c, sp); r[sch] = auroc(y, o)
    res.setdefault("gbm_cv_schemes", {})[name] = r; print(name, r, flush=True)
# 4. edit-size narrow-bin matched AUROC (rank deciles of edit_lines): raw reversed edit size within bins
q = pd.qcut(df.edit_lines.rank(method="first"), 10, labels=False)
res["edit_lines_within_decile_reversed_auroc"] = [{"decile": int(k), "n": int((q == k).sum()), "pos_frac": float(y[q == k].mean()),
    "edit_range": [float(df.edit_lines[q == k].min()), float(df.edit_lines[q == k].max())],
    "rev_auroc": auroc(y[q == k], -df.edit_lines.values[q == k])} for k in range(10)]
res["edit_lines_by_type"] = df.groupby("transformation_type").edit_lines.describe()[["count", "mean", "50%", "min", "max"]].round(2).to_dict("index")
res["edit_lines_label_means"] = {"changed": float(df.edit_lines[y == 1].mean()), "equiv": float(df.edit_lines[y == 0].mean())}
# edit size restricted to the SP types whose size overlaps the SC range
ov = df.edit_lines.between(df.edit_lines[y == 1].quantile(.05), df.edit_lines[y == 1].quantile(.95)).values
res["rev_edit_auroc_overlap_range"] = auroc(y[ov], -df.edit_lines.values[ov])
# per-type reversed edit AUROC vs ALL equivalents
res["rev_edit_auroc_per_SC_type_vs_all_equiv"] = {s: auroc(y[(t == s) | (y == 0)], -df.edit_lines.values[(t == s) | (y == 0)]) for s in SC}
json.dump(res, open(OUT / "LEAKAGE_AUDIT.json", "w"), indent=1, default=float)
