import json, math, collections
from math import comb, sqrt
pop=json.load(open('configs/populations/v10_test.json'))
rows=pop['rows'] if isinstance(pop,dict) else pop
print(type(pop), list(pop.keys())[:10] if isinstance(pop,dict) else '')
r0=rows[0]; print({k:(v if k!='scores' else '...') for k,v in r0.items()})
prim=[r for r in rows if r.get('in_primary_population')]
print(len(rows),len(prim))
ch=[r for r in prim if r['label']==1]
sc6=[r for r in ch if r.get('sc_type')=='SC-6']
print('SC-6 CH',len(sc6), 'zero V5', sum(1 for r in sc6 if r['scores']['sbg_v5']==0), 'programs', len({r['base_id'] for r in sc6}))
c=collections.Counter((r['base_id']) for r in sc6); print(c)
z=collections.Counter(r['base_id'] for r in sc6 if r['scores']['sbg_v5']==0); print(z)
print('all CH zero', sum(1 for r in ch if r['scores']['sbg_v5']==0), 'of', len(ch))
# per-program n
pc=collections.Counter(r['base_id'] for r in prim); print(sorted(pc.values()))
# Wilson & Clopper-Pearson 17/23
def wilson(k,n,z=1.959964):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return c-h,c+h
print('wilson',wilson(17,23))
def cp(k,n,a=0.05):
    def cdf(x,p): return sum(comb(n,i)*p**i*(1-p)**(n-i) for i in range(0,x+1))
    lo=0;hi=1
    # lower: P(X>=k)=a/2
    L,H=0.0,1.0
    for _ in range(100):
        m=(L+H)/2
        if 1-cdf(k-1,m)<a/2: L=m
        else: H=m
    lo=(L+H)/2
    L,H=0.0,1.0
    for _ in range(100):
        m=(L+H)/2
        if cdf(k,m)>a/2: L=m
        else: H=m
    return lo,(L+H)/2
print('CP',cp(17,23))
# SC-6 CH zero if cluster: leave-one-program-out zero rate
progs=sorted(c)
for p in progs:
    rest=[r for r in sc6 if r['base_id']!=p]
    print('drop',p, sum(1 for r in rest if r['scores']['sbg_v5']==0),len(rest))
# edit sign test
def binom_two(k,n,p=.5):
    t=sum(comb(n,i) for i in range(0,min(k,n-k)+1))/2**n; return min(1,2*t)
print('292 of 294 non-tie sign p', binom_two(2,294))
# design effects from A3 SDs
for name,(a,b,c_) in {'V5 AUROC':(0.015072633,0.013118008,0.011860131),'H4 delta':(0.03572445,0.01603124,0.01392313),'M_EX':(0.0333185,0.0178389,0.0155343),'state-V5':(0.0080288,0.0053054,0.0048933)}.items():
    print(name,'DE vs pair-iid',round((a/b)**2,2),'ESS pairs',round(638/(a/b)**2),'DE vs set',round((a/c_)**2,2))
# external AUROC approx z
def zp(est,lo,hi):
    se=(hi-lo)/(2*1.959964); z=(est-0.5)/se
    p=2*(1-0.5*(1+math.erf(abs(z)/sqrt(2)))); return round(se,4),round(z,2),round(p,3)
for n,(e,l,h) in {'BIP v7 all':(0.4099,0.3262,0.4939),'BIP v8 all':(0.4159,0.3223,0.5144),'BIP v8 exSP2':(0.497,0.4023,0.5956),'QB v7 all':(0.3877,0.2847,0.5034),'QB v8 all':(0.3842,0.2847,0.4899),'QB v8 exSP2':(0.4444,0.3553,0.5385)}.items():
    print(n,zp(e,l,h))
