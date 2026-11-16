#!/usr/bin/env python3
"""P13: SeqCoBench label-observability/reliability on SBG's frozen battery (from P10_seqco_outcomes.jsonl) + edit-size-matched stratum yield.
Polarity: SBG_label = 1 - label_seqco (SeqCoBench 1 = preserved).  OBSERVED_CHANGED = battery outcome signature of transformed != original.
Reports: eligibility (both programs run & select SAME entry), degenerate originals (all 11 inputs raise), SP-labelled rows that nonetheless differ (label noise),
SA-labelled rows that are unobservable (same outcomes), AST-identical rows, per-transformation breakdown, and e<=2 matched-stratum yield by split/cluster.
No SBG scoring."""
import json, collections
O = {}
for l in open("P10_seqco_outcomes.jsonl"):
    o = json.loads(l); O[o["file"]] = o
rows = [json.loads(l) for l in open("data/seqco_rows.jsonl")]
C = collections.Counter(); per_t = collections.defaultdict(collections.Counter); keep = []
for r in rows:
    a, b = O[r["orig"]], O[r["var"]]; sbg = 1 - r["label_seqco"]; t = r["transformation"]
    r["sbg_label"] = sbg
    if a["status"] != "ok": C["orig_" + a["status"]] += 1; per_t[t]["orig_not_ok"] += 1; r["cls"] = "orig_" + a["status"]; continue
    if b["status"] != "ok": C["var_" + b["status"]] += 1; per_t[t]["var_not_ok"] += 1; r["cls"] = "var_" + b["status"]; continue
    if a["entry"] != b["entry"]: C["entry_differs"] += 1; per_t[t]["entry_differs"] += 1; r["cls"] = "entry_differs"; continue
    ao = a["outcomes"]; degenerate = all(x[0] != "ret" for x in ao)
    differ = ao != b["outcomes"]
    if degenerate: cls = "orig_all_exc"
    elif r["ast_identical"]: cls = "ast_identical"
    elif sbg == 0 and not differ: cls = "SP_ok"
    elif sbg == 0 and differ: cls = "SP_but_differs"           # label noise on EQUIVALENT side
    elif sbg == 1 and differ: cls = "CH_ok"
    else: cls = "CH_unobservable"                              # altered by construction, identical on battery
    r["cls"] = cls; C[cls] += 1; per_t[t][cls] += 1
    if cls in ("SP_ok", "CH_ok"): keep.append(r)
res = {"n_rows": len(rows), "classes": dict(C), "per_transformation": {t: dict(c) for t, c in sorted(per_t.items())}}
# matched-stratum yield: e==2 (repo edit-size bin (0,2) is e<=2; here strict e==2 and e<=2 both reported)
def yields(sel, name):
    k = [r for r in keep if sel(r)]; progs = collections.defaultdict(lambda: [0, 0])
    for r in k: progs[r["orig_hash"]][r["sbg_label"]] += 1
    both = [p for p, (n0, n1) in progs.items() if n0 and n1]
    res[name] = {"pairs_SP": sum(1 for r in k if r["sbg_label"] == 0), "pairs_CH": sum(1 for r in k if r["sbg_label"] == 1), "programs_with_any": len(progs), "programs_with_both_classes": len(both),
                 "by_split_programs_with_both": dict(collections.Counter(next(r["split"] for r in k if r["orig_hash"] == p) for p in both))}
yields(lambda r: r["edit"] == 2, "stratum_e_eq_2"); yields(lambda r: r["edit"] is not None and 0 < r["edit"] <= 2, "stratum_0_lt_e_le_2"); yields(lambda r: True, "all_observable_validated")
# rates
sp_ok = C["SP_ok"]; sp_bad = C["SP_but_differs"]; ch_ok = C["CH_ok"]; ch_un = C["CH_unobservable"]
res["SP_label_noise_rate"] = round(sp_bad / max(1, sp_ok + sp_bad), 4); res["CH_unobservable_rate"] = round(ch_un / max(1, ch_ok + ch_un), 4)
res["eligible_frac_rows"] = round((len(rows) - sum(v for k, v in C.items() if k.startswith(("orig_", "var_", "entry_")))) / len(rows), 4)
json.dump(res, open("P13_seqco_observability.json", "w"), indent=1); print(json.dumps({k: v for k, v in res.items() if k != "per_transformation"}, indent=1))
for t, c in res["per_transformation"].items(): print(t, dict(c))
