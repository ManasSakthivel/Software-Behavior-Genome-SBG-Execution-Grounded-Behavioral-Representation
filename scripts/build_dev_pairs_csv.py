#!/usr/bin/env python
"""Build results/processed/dev_pairs_per_system.csv from the K1-spike and baseline per-pair JSONL (read-only).
Truth is never relabelled: QuixBugs DIV = the benchmark's own declared tests distinguish buggy from fixed (B2 oracle,
independent of V7-B/B1/B3); synthetic = generator label; suspect generator labels are marked SUSPECT_LABEL (excluded from
primary denominators, still counted); BugsInPy units and QuixBugs pairs without a test witness are UNLABELLED."""
import csv, json, re
P = "results/processed/"
rd = lambda f: [json.loads(l) for l in open(P + f)]
k1 = {(r["arm"], r["pair"]): r for r in rd("k1_spike_per_pair.jsonl") if r["tag"] == "run1"}
bl = {(r["arm"], r["pair"]): r for r in rd("baselines_per_pair.jsonl")}
b4 = {(r["arm"], r["pair"]): r["B4"] for r in rd("baselines_per_pair_final.jsonl")}
MAP = {"DIVERGE": "DIVERGENT_OBSERVABLE", "NO_DIFF": "NO_DIVERGENCE_OBSERVED"}

def truth(arm, pair, r):
    label, sp = r["label"], r.get("sp") or ""
    if arm == "quixbugs":
        b2 = bl[(arm, pair)]["B2"]
        ok = b2["verdict"] == "DIVERGE" and all(t[1] is False and t[2] is True for t in b2["tests_changed"] if True) 
        return ("DIV", "") if ok else ("UNLABELLED", "no declared test distinguishes buggy from fixed (or fixed also fails)")
    if arm == "bugsinpy_units":
        return "UNLABELLED", "real bugfix on synthetic-battery inputs; regression not reproduced"
    toks = set(re.split(r"[+]", sp))
    if toks & {"SP-8", "SP-11"} or ("levenshtein" in pair and "SP-6" in toks):
        return "SUSPECT_LABEL", "known suspect generator label (SP-8/SP-11/levenshtein SP-6)"
    flag = "renamed_entry_SP-2" if "SP-2" in toks else ""
    return ("DIV" if label == "CHANGED" else "NO_OBS_DIFF"), flag

DS = {"quixbugs": "quixbugs_buggy_fixed", "quixbugs_neg": "quixbugs_sp_negatives", "bugsinpy_units": "bugsinpy_units"}
rows = []
for (arm, pair), r in k1.items():
    ds = DS.get(arm) or ("synthetic_changed" if r["label"] == "CHANGED" else "synthetic_equivalent")
    t, flag = truth(arm, pair, r)
    pid, proj = f"{arm}:{pair}", r["project"]
    base = dict(project=proj, pair_id=pid, truth=t, dataset=ds, flag=flag)
    rows.append(dict(base, system="V7-B", verdict=r["verdict"], sufficiency=r.get("level") or "", cpu_s=r.get("cpu_s", ""), mem_mb=""))
    b = bl.get((arm, pair))
    for name, key in [("B1", "B1"), ("B1+rep", "B1rep"), ("B3", "B3")]:
        x = b.get(key) if b else None
        rows.append(dict(base, system=name, verdict=MAP.get(x["verdict"], "") if x else "", sufficiency="", cpu_s=x["cpu_s"] if x else "", mem_mb=""))
    x = b4.get((arm, pair))
    rows.append(dict(base, system="B4", verdict=MAP.get(x["verdict"], "") if x else "", sufficiency="", cpu_s=x["cpu_s"] if x else "", mem_mb=""))
rows.sort(key=lambda r: (r["system"], r["pair_id"]))
with open(P + "dev_pairs_per_system.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["project","pair_id","system","verdict","sufficiency","truth","cpu_s","mem_mb","dataset","flag"])
    w.writeheader(); w.writerows(rows)
print(len(rows), "rows;", len(k1), "pairs")
