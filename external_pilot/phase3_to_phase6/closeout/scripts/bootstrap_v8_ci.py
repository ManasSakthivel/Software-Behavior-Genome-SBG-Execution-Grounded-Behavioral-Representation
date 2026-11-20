"""Cluster bootstrap (resample base_id clusters with replacement, 2000 draws, seed 0, percentile CI)
for sbg_v5 on the 956 evaluated test pairs. Approximate: the recorded JSON method may differ in RNG and
resampling details, so this is a plausibility check, not an exact reproduction."""
import json, random, sys
from collections import defaultdict
rows = [json.loads(l) for l in open(sys.argv[1]) if json.loads(l).get("evaluated")]
clusters = defaultdict(list)
for r in rows: clusters[r["base_id"]].append(r)
keys = list(clusters)
def auroc(rs):
    pos = [r["scores"]["sbg_v5"] for r in rs if r["label"] == 1]; neg = [r["scores"]["sbg_v5"] for r in rs if r["label"] == 0]
    if not pos or not neg: return None
    s = sorted([(x, 1) for x in pos] + [(x, 0) for x in neg]); i = 0; rs_ = 0.0
    while i < len(s):
        j = i
        while j < len(s) and s[j][0] == s[i][0]: j += 1
        avg = (i + 1 + j) / 2.0; rs_ += avg * sum(1 for k in range(i, j) if s[k][1] == 1); i = j
    return (rs_ - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg))
rng = random.Random(0); draws = []
for _ in range(2000):
    samp = [rr for _ in range(len(keys)) for rr in clusters[rng.choice(keys)]]
    a = auroc(samp)
    if a is not None: draws.append(a)
draws.sort()
print("clusters", len(keys), "valid draws", len(draws), "percentile 95% CI", round(draws[int(0.025*len(draws))],6), round(draws[int(0.975*len(draws))],6))
