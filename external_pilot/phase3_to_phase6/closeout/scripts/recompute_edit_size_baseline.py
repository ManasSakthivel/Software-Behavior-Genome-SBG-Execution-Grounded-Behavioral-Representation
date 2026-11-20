"""Recompute reversed edit-size AUROC on the evaluated test pairs (read-only).
Mirrors experiments/final/edit_size_analysis.py: canonical lines via ast.unparse, unified diff n=0 count of +/- lines,
baseline score = -edit_size. Uses the same tie-aware AUROC as recompute_v8_test_auroc.py."""
import ast, difflib, json, pathlib, sys
REPO = pathlib.Path(sys.argv[1]); scored = sys.argv[2]; meta_file = sys.argv[3]
def canon(p): return ast.unparse(ast.parse((REPO / p).read_text())).splitlines()
def edit(bp, vp):
    n = 0
    for line in difflib.unified_diff(canon(bp), canon(vp), lineterm="", n=0):
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")): n += 1
    return n
meta = {m["pair_id"]: m for m in (json.loads(l) for l in open(meta_file))}
rows = [json.loads(l) for l in open(scored)]
ev = [r for r in rows if r.get("evaluated")]
pos, neg = [], []
for r in ev:
    m = meta[r["pair_id"]]
    s = -float(edit(m["base_path"], m["variant_path"]))
    (pos if r["label"] == 1 else neg).append(s)
def auroc(pos, neg):
    s = sorted([(x, 1) for x in pos] + [(x, 0) for x in neg]); i = 0; rs = 0.0
    while i < len(s):
        j = i
        while j < len(s) and s[j][0] == s[i][0]: j += 1
        avg = (i + 1 + j) / 2.0; rs += avg * sum(1 for k in range(i, j) if s[k][1] == 1); i = j
    return (rs - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg))
print("evaluated", len(ev), "changed", len(pos), "equivalent", len(neg))
print("edit_size_reversed AUROC", round(auroc(pos, neg), 6))
