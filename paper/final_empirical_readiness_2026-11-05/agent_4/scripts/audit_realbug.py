#!/usr/bin/env python3
"""Agent 4 auditor: recompute BugsInPy / QuixBugs headline AUROCs, zero counts, taxonomy counts from raw v7 pair files (read-only)."""
import sys; sys.dont_write_bytecode = True
import json, pathlib, collections, random, math, csv
HERE = pathlib.Path(__file__).resolve().parent; REPO = HERE.parents[3]; OUT = HERE.parent / "tables"
def jl(p): return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]
def auc(pos, neg):
    vals = sorted([(v,1) for v in pos]+[(v,0) for v in neg], key=lambda t:t[0]); n=len(vals); rk=[0.0]*n; i=0
    while i<n:
        j=i
        while j+1<n and vals[j+1][0]==vals[i][0]: j+=1
        for k in range(i,j+1): rk[k]=(i+j)/2+1
        i=j+1
    rs=sum(rk[k] for k in range(n) if vals[k][1]); return (rs-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg))
res = {}
def boot(rows, cl, key="sbg_v5", B=2000, seed=42):
    by = collections.defaultdict(list)
    for r in rows: by[r[cl]].append(r)
    ks = sorted(by); rng = random.Random(seed); v=[]
    for _ in range(B):
        rs=[x for _ in ks for x in by[ks[rng.randrange(len(ks))]]]
        p=[r["scores"][key] for r in rs if r["label"]==1]; n=[r["scores"][key] for r in rs if r["label"]==0]
        if p and n: v.append(auc(p,n))
    v.sort(); return [round(v[int(.025*len(v))],6), round(v[int(math.ceil(.975*len(v)))-1],6)], len(ks)
for name, f, cl in (("bugsinpy","pairs_bugsinpy_output_free_v7.jsonl","bug_id"),("quixbugs_canonical","pairs_quixbugs_canonical_output_free_v7.jsonl","base_id"),("quixbugs_declared","pairs_quixbugs_declared_output_free_v7.jsonl","base_id")):
    rows = jl(REPO/"artifacts/final"/f); ev=[r for r in rows if r.get("evaluated", True) and r.get("scores")]
    pos=[r for r in ev if r["label"]==1]; neg=[r for r in ev if r["label"]==0]
    d = {"n_rows":len(rows),"n_eval":len(ev),"n_pos":len(pos),"n_neg":len(neg),"n_clusters":len({r[cl] for r in ev}),
         "n_pos_clusters":len({r[cl] for r in pos}),
         "auroc":auc([r["scores"]["sbg_v5"] for r in pos],[r["scores"]["sbg_v5"] for r in neg])}
    d["ci"], d["ci_nclusters"] = boot(ev, cl)
    for c in ("sbg_v5","sbg_temporal","sbg_v3","sbg_state"):
        d[f"pos_zero_{c}"] = sum(r["scores"][c]==0 for r in pos)
    d["neg_zero_v5"]=sum(r["scores"]["sbg_v5"]==0 for r in neg)
    d["pos_mean_v5"]=sum(r["scores"]["sbg_v5"] for r in pos)/len(pos); d["neg_mean_v5"]=sum(r["scores"]["sbg_v5"] for r in neg)/len(neg)
    # transformation breakdown of negatives
    key = "transformation" if name=="bugsinpy" else "pair_kind"
    tb = collections.defaultdict(list)
    for r in neg: tb[r.get(key)].append(r["scores"]["sbg_v5"])
    d["neg_by_transf"] = {k:{"n":len(v),"mean":round(sum(v)/len(v),4),"zero":sum(x==0 for x in v)} for k,v in tb.items()}
    # excluding SP-2 negatives
    ex = [r for r in ev if not (r["label"]==0 and "SP-2" in str(r.get(key)))]
    d["auroc_excl_SP2_neg"]=auc([r["scores"]["sbg_v5"] for r in ex if r["label"]==1],[r["scores"]["sbg_v5"] for r in ex if r["label"]==0])
    d["auroc_excl_SP2_neg_ci"]=boot(ex, cl)[0]
    d["pos_zero_ids"] = [r["pair_id"] for r in pos if r["scores"]["sbg_v5"]==0]
    d["label_nonbinary"]=sorted({r["label"] for r in rows})
    res[name]=d
(OUT/"realbug_audit.json").write_text(json.dumps(res,indent=1))
for k,v in res.items():
    print(k, {a:b for a,b in v.items() if a not in("pos_zero_ids",)})
