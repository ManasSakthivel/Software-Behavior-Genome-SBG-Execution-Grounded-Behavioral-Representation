import json, math, collections
pop=json.load(open('configs/populations/v10_test.json'))
prim=[r for r in pop['rows'] if r['in_primary_population']]
def auroc(s,y):
    P=[a for a,b in zip(s,y) if b]; N=[a for a,b in zip(s,y) if not b]
    # rank-based O(n log n)
    idx=sorted(range(len(s)),key=lambda i:s[i]); ranks=[0]*len(s); i=0
    while i<len(idx):
        j=i
        while j+1<len(idx) and s[idx[j+1]]==s[idx[i]]: j+=1
        for k in range(i,j+1): ranks[idx[k]]=(i+j)/2+1
        i=j+1
    rp=sum(ranks[i] for i in range(len(s)) if y[i])
    return (rp-len(P)*(len(P)+1)/2)/(len(P)*len(N))
progs=sorted({r['base_id'] for r in prim})
def stat(rs,f):
    y=[r['label'] for r in rs]; return f(rs,y)
def mk(name_a,name_b=None):
    def f(rs,y):
        a=auroc([r['scores'][name_a] for r in rs],y)
        return a if name_b is None else a-auroc([r['scores'][name_b] for r in rs],y)
    return f
# t-quantile 18 df two-sided 95%
t18=2.1009
for label,f in [('V5',mk('sbg_v5')),('state',mk('sbg_state')),('state-V5',mk('sbg_state','sbg_v5')),('V5-edit',mk('sbg_v5','edit')),('V6-V5',mk('sbg_v6','sbg_v5'))]:
    full=stat(prim,f)
    loo=[stat([r for r in prim if r['base_id']!=p],f) for p in progs]
    n=len(progs); m=sum(loo)/n
    se=math.sqrt((n-1)/n*sum((v-m)**2 for v in loo))
    # pseudo-values
    pv=[n*full-(n-1)*v for v in loo]; pm=sum(pv)/n; psd=math.sqrt(sum((v-pm)**2 for v in pv)/(n-1)); pse=psd/math.sqrt(n)
    print(f"{label}: est={full:.4f} jackknife SE={se:.4f} t18 CI=[{full-t18*se:.4f},{full+t18*se:.4f}]  min/max LOPO {min(loo):.4f}/{max(loo):.4f}")
