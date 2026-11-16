#!/usr/bin/env python3
"""P16: cross-check of the prior in-repo SeqCoBench counts (agent_3: 332 zero-exception originals of 1,135; e=2 stratum 188 programs / 860 pairs (400 SP,460 SA); test: 60 programs, 259 pairs)
using D3's independent oracle outcomes (P10) under the 'zero-exception original' rule. Not a re-run of their code. Output P16_seqco_prior_crosscheck.json"""
import json, collections
O = {}
for l in open("P10_seqco_outcomes.jsonl"):
    o = json.loads(l); O[o["file"]] = o
rows = [json.loads(l) for l in open("data/seqco_rows.jsonl")]
orig_ok = {}
for f, o in O.items():
    if "/orig_" in f: orig_ok[f] = o["status"] == "ok" and all(x[0] == "ret" for x in o["outcomes"])
by_split = collections.defaultdict(set)
for r in rows: by_split[r["split"]].add(r["orig"])
res = {"zero_exception_originals_total": sum(orig_ok.values()), "unique_originals": len(orig_ok), "zero_exc_by_split": {s: [sum(orig_ok[f] for f in fs), len(fs)] for s, fs in by_split.items()}}
def stratum(split=None, strict_e=2):
    pairs = collections.defaultdict(lambda: [0, 0]); n = [0, 0]
    for r in rows:
        if split and r["split"] != split: continue
        if r["edit"] != strict_e or not orig_ok.get(r["orig"]) or r["ast_identical"]: continue
        a, b = O[r["orig"]], O[r["var"]]
        if b["status"] != "ok" or a["entry"] != b["entry"]: continue
        differ = a["outcomes"] != b["outcomes"]; sbg = 1 - r["label_seqco"]
        if sbg == 0 and not differ: pairs[r["orig_hash"]][0] += 1; n[0] += 1
        elif sbg == 1 and differ: pairs[r["orig_hash"]][1] += 1; n[1] += 1
    both = [p for p, (a, b) in pairs.items() if a and b]
    return {"SP_pairs": n[0], "CH_pairs": n[1], "programs_with_both": len(both)}
res["e_eq_2_all"] = stratum(); res["e_eq_2_test"] = stratum("test"); res["e_eq_2_train"] = stratum("train"); res["e_eq_2_valid"] = stratum("valid")
json.dump(res, open("P16_seqco_prior_crosscheck.json", "w"), indent=1); print(json.dumps(res, indent=1))
