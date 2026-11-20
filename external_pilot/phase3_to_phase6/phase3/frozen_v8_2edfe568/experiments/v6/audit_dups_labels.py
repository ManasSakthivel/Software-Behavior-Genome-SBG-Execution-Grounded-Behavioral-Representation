"""Duplicate-variant audit (task 5) and label adjudication evidence (task 6). DEV only. Original labels are preserved and never edited.
 -> artifacts/v6/audit/DUPLICATE_AUDIT.json, LABEL_ADJUDICATION.csv, LABEL_ADJUDICATION_SUMMARY.json"""
import json, sys, pathlib, hashlib, collections, csv
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from experiments.v6.evaluate import *   # noqa
OUT = REPO / "artifacts/v6/audit"
sha = lambda p: hashlib.sha256((REPO / p).read_bytes()).hexdigest()
meta = {}
for f in ("train", "val"):
    for l in open(REPO / f"benchmark/datasets/v8/pairs_{f}.jsonl"):
        r = json.loads(l); meta[r["pair_id"]] = r
df = load(["v8train", "v8val"]); y = df.label.values.astype(int); g = df.base_id.values; t = df.transformation_type.values
df["vh"] = df.pair_id.map(lambda p: sha(meta[p]["variant_path"])); df["bh"] = df.pair_id.map(lambda p: sha(meta[p]["base_path"]))
res = {}
# ---- effective independent units
grp = df.groupby("vh")
res["counts"] = {"pairs": len(df), "programs": int(df.base_id.nunique()), "unique_base_sources": int(df.bh.nunique()),
    "unique_variant_files": int(df.vh.nunique()), "unique_base_x_type_groups": int(df.groupby(["base_id", "transformation_type"]).ngroups),
    "unique_variants_changed": int(df[y == 1].vh.nunique()), "unique_variants_equiv": int(df[y == 0].vh.nunique()),
    "dup_groups(size>1)": int((grp.size() > 1).sum()), "rows_in_dup_groups": int(grp.size()[grp.size() > 1].sum()),
    "max_group_size": int(grp.size().max()), "pairs_per_unique_variant_mean": float(len(df) / df.vh.nunique())}
res["dup_group_properties"] = {"cross_program_groups": int((grp.base_id.nunique() > 1).sum()), "cross_type_groups": int((grp.transformation_type.nunique() > 1).sum()),
    "label_conflict_groups": int((grp.label.nunique() > 1).sum()), "cross_split_groups(train/val)": int((grp.split.nunique() > 1).sum())}
ct = grp.filter(lambda x: x.transformation_type.nunique() > 1)
res["cross_type_group_type_sets"] = collections.Counter(tuple(sorted(set(x))) for _, x in ct.groupby("vh").transformation_type).most_common(10) if len(ct) else []
res["base_source_shared_by_multiple_base_ids"] = int((df.groupby("bh").base_id.nunique() > 1).sum())
# ---- partition audit: does any variant-file group straddle train/test in any partition used?
vh = df.vh.values
def straddle(splits): return int(sum(len(set(vh[tr]) & set(vh[te])) for tr, te in splits))
SC = sorted(set(t[y == 1])); SP = sorted(set(t[y == 0])); tf = {}
for i, ty in enumerate(SC): tf.setdefault(i % 4, []).append(ty)
for i, ty in enumerate(SP): tf.setdefault(i % 4, []).append(ty)
part = {f"program_grouped_seed{s}": folds(g, s) for s in SEEDS}
part["leave_one_type_out"] = [(np.where(t != u)[0], np.where(t == u)[0]) for u in sorted(set(t))]
part["leave_type_groups_out(4)"] = [(np.where(~np.isin(t, v))[0], np.where(np.isin(t, v))[0]) for v in tf.values()]
part["leave_domain_out"] = [(np.where(df.base_id.str.split("_").str[0] != f)[0], np.where(df.base_id.str.split("_").str[0] == f)[0]) for f in sorted(set(df.base_id.str.split("_").str[0]))]
res["variant_groups_straddling_train_test"] = {k: straddle(v) for k, v in part.items()}
res["program_overlap_straddling"] = {k: int(sum(len(set(g[tr]) & set(g[te])) for tr, te in v)) for k, v in part.items()}
# ---- holdout metadata overlap (program ids + base-source hashes only; NO results/scores read)
ho = {}
for name, p in (("v8_test", "benchmark/datasets/v8/pairs_test.jsonl"), ("v10", "benchmark/datasets/v10_independent/pairs_test.jsonl")):
    rows = [json.loads(l) for l in open(REPO / p)]
    ids = {r["base_id"] for r in rows}; hs = {sha(r["base_path"]) for r in rows if (REPO / r["base_path"]).exists()}
    ho[name] = {"programs": len(ids), "base_id_overlap_with_DEV": len(ids & set(df.base_id)), "base_source_hash_overlap_with_DEV": len(hs & set(df.bh))}
res["holdout_metadata_overlap"] = ho
json.dump(res, open(OUT / "DUPLICATE_AUDIT.json", "w"), indent=1, default=str); print(json.dumps(res, indent=1, default=str)[:3500])
