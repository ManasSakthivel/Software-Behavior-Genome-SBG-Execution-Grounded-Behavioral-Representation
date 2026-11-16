#!/usr/bin/env python3
"""P10: SeqCoBench (nickil/seqcobench; Maveli, Vergari, Cohen 2024; arXiv 2408.11081) -- STATIC preparation + leakage/edit-size audit. No execution here, no SBG.
NB polarity: SeqCoBench label 1 = semantics PRESERVED (equivalent); label 0 = semantics ALTERED / dissimilar. SBG label is the opposite (1 = CHANGED).
Outputs: data/seqco_src/*.py, P10_seqco_static.json, data/seqco_rows.jsonl"""
import csv, ast, json, hashlib, difflib, os, collections, sys, importlib.util
sys.dont_write_bytecode = True; csv.field_size_limit(10**8)
spec = importlib.util.spec_from_file_location("p", "/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG/experiments/final/protocol.py"); P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
os.makedirs("data/seqco_src", exist_ok=True)
def canon(s):
    try: return ast.unparse(ast.parse(s)).splitlines()
    except SyntaxError: return None
def edit(a, b):
    return sum(1 for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[0] in "+-" and not l.startswith(("+++", "---")))
rows = []; orig_files = {}; st = collections.Counter(); per_split_orig = collections.defaultdict(set)
for split in ("train", "valid", "test"):
    for i, r in enumerate(csv.DictReader(open(f"data/seqcobench_{split}.csv", newline=""))):
        oh = hashlib.sha1(r["original_code"].encode()).hexdigest()[:12]; per_split_orig[split].add(oh)
        of = f"data/seqco_src/orig_{oh}.py"
        if oh not in orig_files: open(of, "w").write(r["original_code"] + "\n"); orig_files[oh] = of
        tf = f"data/seqco_src/{split}_{i}.py"; open(tf, "w").write(r["transformed_code"] + "\n")
        a, b = canon(r["original_code"]), canon(r["transformed_code"])
        e = edit(a, b) if a is not None and b is not None else None
        try: elig = bool(P.eligible_candidates(ast.parse(r["original_code"]))) and bool(P.eligible_candidates(ast.parse(r["transformed_code"])))
        except SyntaxError: elig = None
        rows.append({"split": split, "i": i, "orig": of, "var": tf, "orig_hash": oh, "transformation": r["transformation"], "label_seqco": int(r["label"]), "groups": r["groups"], "edit": e, "static_eligible_both": elig,
                     "ast_identical": (a == b) if a is not None and b is not None else None})
with open("data/seqco_rows.jsonl", "w") as f:
    for r in rows: f.write(json.dumps(r) + "\n")
S = {"n_rows": len(rows), "n_unique_originals": len(orig_files), "rows_by_split": collections.Counter(r["split"] for r in rows), "unique_orig_by_split": {k: len(v) for k, v in per_split_orig.items()},
     "orig_overlap_train_valid": len(per_split_orig["train"] & per_split_orig["valid"]), "orig_overlap_train_test": len(per_split_orig["train"] & per_split_orig["test"]), "orig_overlap_valid_test": len(per_split_orig["valid"] & per_split_orig["test"]),
     "label_counts": collections.Counter(r["label_seqco"] for r in rows), "static_eligible_both": collections.Counter(str(r["static_eligible_both"]) for r in rows),
     "ast_identical_rows": sum(1 for r in rows if r["ast_identical"]), "ast_identical_by_label": collections.Counter(r["label_seqco"] for r in rows if r["ast_identical"]),
     "groups_unique": len({r["groups"] for r in rows})}
# groups vs originals: is a 'group' one base program?
g2o = collections.defaultdict(set)
for r in rows: g2o[r["groups"]].add(r["orig_hash"])
S["groups_with_multiple_originals"] = sum(len(v) > 1 for v in g2o.values()); S["groups_per_split_overlap"] = {}
gs = {s: {r["groups"] for r in rows if r["split"] == s} for s in ("train", "valid", "test")}
S["groups_per_split_overlap"] = {"train&valid": len(gs["train"] & gs["valid"]), "train&test": len(gs["train"] & gs["test"]), "valid&test": len(gs["valid"] & gs["test"])}
# edit-size distribution by transformation & label
def q(v, p): v = sorted(v); return v[int(p * (len(v) - 1))] if v else None
by_t = collections.defaultdict(list)
for r in rows:
    if r["edit"] is not None: by_t[r["transformation"]].append(r["edit"])
S["edit_by_transformation"] = {t: {"n": len(v), "median": q(v, .5), "q25": q(v, .25), "q75": q(v, .75), "frac_le2": round(sum(x <= 2 for x in v) / len(v), 3)} for t, v in sorted(by_t.items())}
json.dump(S, open("P10_seqco_static.json", "w"), indent=1, default=lambda o: dict(o)); print(json.dumps(S, indent=0, default=lambda o: dict(o))[:3500])
