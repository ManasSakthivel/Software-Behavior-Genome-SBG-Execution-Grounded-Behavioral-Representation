"""Compare stored/rerun Regression+HardNegative V5 results between py3.13.5 and py3.9.6 (exploratory)."""
import json, sys, math, pathlib
O = pathlib.Path(__file__).resolve().parent.parent / "outputs"
def load(v, n): return json.load(open(O/v/f"{n}.json"))
def spearman(a,b):
    def rk(x):
        s=sorted(range(len(x)),key=lambda i:x[i]); r=[0]*len(x); i=0
        while i<len(s):
            j=i
            while j+1<len(s) and x[s[j+1]]==x[s[i]]: j+=1
            for k in range(i,j+1): r[s[k]]=(i+j)/2+1
            i=j+1
        return r
    ra,rb=rk(a),rk(b); n=len(a); ma=sum(ra)/n; mb=sum(rb)/n
    num=sum((x-ma)*(y-mb) for x,y in zip(ra,rb)); da=math.sqrt(sum((x-ma)**2 for x in ra)); db=math.sqrt(sum((y-mb)**2 for y in rb))
    return num/(da*db) if da and db else float('nan')
def auroc(scores, labels):
    pos=[s for s,l in zip(scores,labels) if l==1]; neg=[s for s,l in zip(scores,labels) if l==0]
    if not pos or not neg: return float('nan')
    w=0
    for p in pos:
        for q in neg: w+= 1 if p>q else (0.5 if p==q else 0)
    return w/(len(pos)*len(neg))
rows=[]
reg={v:load(v,"REGRESSION_V5_RESULTS") for v in ("py313","py39")}
for a,b in zip(reg["py313"]["pairs"],reg["py39"]["pairs"]):
    assert a["id"]==b["id"]
    rows.append(("regression",a["id"],a.get("ground_truth_label"),a["n_events_buggy"],b["n_events_buggy"],a["n_events_fixed"],b["n_events_fixed"],a["distances"],b["distances"]))
hn={v:load(v,"HARD_NEGATIVE_V5_RESULTS") for v in ("py313","py39")}
for reg_name in hn["py313"]["regimes"]:
    for a,b in zip(hn["py313"]["regimes"][reg_name]["pairs"],hn["py39"]["regimes"][reg_name]["pairs"]):
        assert a["pair_id"]==b["pair_id"]
        rows.append(("hardneg_"+reg_name,a["pair_id"],a["ground_truth_label"],a.get("n_events_base"),b.get("n_events_base"),a.get("n_events_variant"),b.get("n_events_variant"),a["distances"],b["distances"]))
print("keys hn pair:", list(hn["py313"]["regimes"]["canonical"]["pairs"][0].keys()))
comps=["sbg_v5","sbg_v3","temporal","state","exception_component"]
summary={}
for grp in sorted({r[0] for r in rows}):
    R=[r for r in rows if r[0]==grp]
    g={"n":len(R)}
    for c in comps:
        x=[r[7][c] for r in R]; y=[r[8][c] for r in R]
        d=[abs(p-q) for p,q in zip(x,y)]
        lab=[r[2] for r in R]
        g[c]={"n_changed":sum(1 for t in d if t>0),"max_abs":round(max(d),6),"mean_abs":round(sum(d)/len(d),6),
              "spearman":round(spearman(x,y),4),"auroc_313":round(auroc(x,lab),4),"auroc_39":round(auroc(y,lab),4),
              "n_decision_flip_at_0.08":sum(1 for p,q in zip(x,y) if (p>0.08)!=(q>0.08))}
    summary[grp]=g
json.dump(summary,open(O/"comparison_summary.json","w"),indent=1)
print(json.dumps(summary,indent=1))
print("\nPER-PAIR CHANGES")
for r in rows:
    ch={c:(r[7][c],r[8][c]) for c in comps if r[7][c]!=r[8][c]}
    ev=(r[3],r[4],r[5],r[6]) 
    if ch or r[3]!=r[4] or r[5]!=r[6]: print(r[0],r[1],"events(313b,39b,313f,39f)=",ev,ch)
