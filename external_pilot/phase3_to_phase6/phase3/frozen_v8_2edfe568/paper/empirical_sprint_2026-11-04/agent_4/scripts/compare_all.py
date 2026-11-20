"""Pairwise comparison of all rerun outputs: counts of changed distance values, max |delta| (per component), Spearman, 0.08 decision flips.
Exploratory. Reads only outputs/<tag>/*.json."""
import json, pathlib, math, itertools, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); 
O = pathlib.Path(__file__).resolve().parent.parent / "outputs"
tags = ["py313","py313_rep2","py313_seed1","py313_seed7","py39","py39_seed1","py311_seed0","py312_seed0","py314_seed0"]
comps = ["sbg_v5","sbg_v3","temporal","state","exception_component"]
def vec(tag):
    R = json.load(open(O/tag/"REGRESSION_V5_RESULTS.json")); H = json.load(open(O/tag/"HARD_NEGATIVE_V5_RESULTS.json"))
    d = {}
    for p in R["pairs"]:
        for c in comps: d[("REG",p["id"],c)] = p["distances"][c]
    for rg, b in H["regimes"].items():
        for p in b["pairs"]:
            for c in comps: d[("HN_"+rg,p["pair_id"],c)] = p["distances"][c]
    return d
def rank(x):
    s = sorted(range(len(x)), key=lambda i: x[i]); r=[0]*len(x); i=0
    while i<len(s):
        j=i
        while j+1<len(s) and x[s[j+1]]==x[s[i]]: j+=1
        for k in range(i,j+1): r[s[k]]=(i+j)/2+1
        i=j+1
    return r
def sp(a,b):
    ra,rb=rank(a),rank(b); n=len(a); ma=sum(ra)/n; mb=sum(rb)/n
    num=sum((x-ma)*(y-mb) for x,y in zip(ra,rb)); da=math.sqrt(sum((x-ma)**2 for x in ra)); db=math.sqrt(sum((y-mb)**2 for y in rb))
    return num/(da*db) if da and db else float("nan")
V = {t: vec(t) for t in tags}
keys = list(V["py313"])
print("pair-of-runs | n_values | n_changed | max|d| | Spearman(sbg_v5, pooled 3 sets=39 pairs) | v5 decision flips@0.08")
out = {}
for a,b in [("py313","py313_rep2"),("py313","py313_seed1"),("py313","py313_seed7"),("py39","py39_seed1"),("py313","py39"),("py313","py311_seed0"),("py313","py314_seed0"),("py313","py312_seed0"),("py311_seed0","py312_seed0"),("py39","py312_seed0"),("py313","py312_seed0"),("py311_seed0","py312_seed0"),("py39","py312_seed0"),("py39","py311_seed0"),("py311_seed0","py314_seed0"),("py39","py314_seed0")]:
    ch = [k for k in keys if V[a][k]!=V[b][k]]
    mx = max(abs(V[a][k]-V[b][k]) for k in keys)
    v5k = [k for k in keys if k[2]=="sbg_v5"]
    s = sp([V[a][k] for k in v5k],[V[b][k] for k in v5k])
    flips = sum(1 for k in v5k if (V[a][k]>0.08)!=(V[b][k]>0.08))
    comp_ch = {c: sum(1 for k in ch if k[2]==c) for c in comps}
    comp_mx = {c: round(max(abs(V[a][k]-V[b][k]) for k in keys if k[2]==c),4) for c in comps}
    print(f"{a} vs {b} | {len(keys)} | {len(ch)} | {mx:.4f} | {s:.4f} | {flips}")
    print("    changed by component:", comp_ch, " max by component:", comp_mx)
    out[f"{a}__{b}"] = dict(n=len(keys), n_changed=len(ch), max_abs=mx, spearman_v5=s, flips=flips, changed_by_comp=comp_ch, max_by_comp=comp_mx)
json.dump(out, open(O/"compare_all.json","w"), indent=1)
