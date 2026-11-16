"""d4_00_selftest.py -- unit checks of the D4 statistics code + point-estimate reproduction of
the numbers published in the SBG repo (own recomputation from raw pair files).
Output: raw/WPD-D4_stats/00_selftest.json   (status: ANALYSIS-INDEPENDENT, no external-label tuning)
"""
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from d4_lib import *  # noqa

res = {"script": "scripts/d4_00_selftest.py", "checks": {}}

# 1. auroc == brute force on random tie-heavy data
rng = random.Random(1)
bad = 0
for _ in range(500):
    n = rng.randint(4, 40)
    sc = [rng.choice([0.0, 0.0, 0.0, 0.1, 0.2, 0.5, rng.random()]) for _ in range(n)]
    lab = [rng.randint(0, 1) for _ in range(n)]
    a, b = auroc(sc, lab), auroc_bruteforce(sc, lab)
    if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-12):
        bad += 1
res["checks"]["auroc_vs_bruteforce_500_random_tieheavy"] = {"mismatches": bad}

# 2. exact stratified vs. brute-force enumeration (tiny)
sc = [0, 0.2, 0.2, 0.5, 0.0, 0.0, 0.7, 0.1, 0.3]
lab = [1, 0, 0, 1, 0, 0, 0, 1, 0]
cl = ["a", "a", "a", "b", "b", "b", "c", "c", "c"]
g = groups_of(cl)
ex = exact_stratified(sc, lab, g)
# brute-force
import math as _m
tot = le = 0
T_OBS = None
_pos = lambda gg: [i for i in gg if lab[i] == 1]
_num = _den = 0
for gg in g:
    for i in gg:
        for j in gg:
            if lab[i] == 1 and lab[j] == 0:
                _num += 1 if sc[i] > sc[j] else 0.5 if sc[i] == sc[j] else 0
                _den += 1
T_OBS = _num / _den
for combo in itertools.product(*[list(itertools.combinations(gg, sum(lab[i] for i in gg))) for gg in g]):
    pos = set(i for c in combo for i in c)
    l2 = [1 if i in pos else 0 for i in range(len(sc))]
    num = den = 0
    for gg in g:
        for i in gg:
            for j in gg:
                if l2[i] == 1 and l2[j] == 0:
                    num += 1 if sc[i] > sc[j] else 0.5 if sc[i] == sc[j] else 0
                    den += 1
    tot += 1
    t = num / den
    if t <= T_OBS + 1e-9:
        le += 1
res["checks"]["exact_stratified_vs_enumeration"] = {"exact_p_lower": ex["p_lower_tail_T<=obs"],
                                                      "enumeration_p_lower": le / tot,
                                                      "match": abs(ex["p_lower_tail_T<=obs"] - le / tot) < 1e-12}

# 3. fisher: known value (Agresti tea tasting 3,1,1,3 -> two-sided 0.4857)
f = fisher_exact(3, 1, 1, 3)
res["checks"]["fisher_tea_tasting"] = {"p_two_sided": round(f["p_two_sided"], 4), "expected": 0.4857}

# 4. point-estimate reproduction of published numbers
C = load_corpora()


def a(recs, src, pred="sbg_v5", use_unev=False):
    sel = [r for r in recs if (r["ev7"] if src == "s7" else r["ev8"])] if not use_unev else recs
    return auroc(vecs(sel, pred, src), [r["label"] for r in sel]), len(sel)


rep = {}
bp, qc, qd = C["bugsinpy"], C["quixbugs_canonical"], C["quixbugs_declared"]
rep["bugsinpy v7 evaluated (committed headline 0.409917)"] = a(bp, "s7")
rep["bugsinpy v7 ALL, unevaluated->0 (committed ALL 0.433981)"] = a(bp, "s7", use_unev=True)
rep["bugsinpy v8 evaluated (EXTERNAL_RESCORE_V8 0.4159)"] = a(bp, "s8")
nosp2 = lambda recs: [r for r in recs if r["kind"] != "SP-2"]
rep["bugsinpy v8 ex-SP-2 (0.497)"] = a(nosp2(bp), "s8")
rep["bugsinpy v7 ex-SP-2 (A3: 0.4715)"] = a(nosp2(bp), "s7")
rep["quixbugs canonical v7 evaluated (committed 0.387723)"] = a(qc, "s7")
rep["quixbugs canonical v8 evaluated (0.3842)"] = a(qc, "s8")
rep["quixbugs canonical v8 ex-SP-2 (0.4444)"] = a(nosp2(qc), "s8")
rep["quixbugs canonical v7 ex-SP-2 (0.4507)"] = a(nosp2(qc), "s7")
rep["quixbugs declared v7 evaluated (DIAGNOSTIC_EXTERNAL 0.7022)"] = a(qd, "s7")
rep["quixbugs declared v7 ex-SP-2 (0.6684)"] = a(nosp2(qd), "s7")
res["checks"]["point_estimate_reproduction"] = {k: {"auroc": round(v[0], 6), "n": v[1]} for k, v in rep.items()}
res["input_manifest"] = input_manifest()
p = write_json("00_selftest.json", res)
print("wrote", p)
for k, v in res["checks"].items():
    print(k, v if not isinstance(v, dict) or len(str(v)) < 300 else "...")
for k, v in rep.items():
    print("  %-70s %.6f n=%d" % (k, v[0], v[1]))
