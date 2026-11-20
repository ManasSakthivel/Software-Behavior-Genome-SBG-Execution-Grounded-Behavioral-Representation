"""Recompute test-split AUROC from the committed scored-pairs file (read-only). Tie-aware Mann-Whitney."""
import json, sys
path = sys.argv[1]
rows = [json.loads(l) for l in open(path, encoding="utf-8")]
ev = [r for r in rows if r.get("evaluated")]
print("rows", len(rows), "evaluated", len(ev), "labels", {l: sum(1 for r in ev if r["label"] == l) for l in (0, 1)})
print("predictor keys:", sorted(ev[0]["scores"].keys()))
def auroc(pos, neg):
    s = sorted([(x, 1) for x in pos] + [(x, 0) for x in neg])
    i, rank_sum, n_pos = 0, 0.0, len(pos)
    while i < len(s):
        j = i
        while j < len(s) and s[j][0] == s[i][0]: j += 1
        avg = (i + 1 + j) / 2.0
        rank_sum += avg * sum(1 for k in range(i, j) if s[k][1] == 1)
        i = j
    n_neg = len(neg)
    return (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
for name in sorted(ev[0]["scores"].keys()):
    pos = [r["scores"][name] for r in ev if r["label"] == 1]
    neg = [r["scores"][name] for r in ev if r["label"] == 0]
    print(name, round(auroc(pos, neg), 6))
