# FEASIBILITY ONLY (static entry + oracle outputs on fixed battery). No SBG, no tracer.
import csv,sys,collections,warnings,difflib,statistics
warnings.filterwarnings('ignore'); sys.dont_write_bytecode=True; csv.field_size_limit(10**8)
sys.path.insert(0,'/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')
from experiments.final.entry_policy import select_entry_structural, EntryPointError, interfaces_correspond
from feas import go
def esize(a,b): return sum(1 for l in difflib.unified_diff(a.splitlines(),b.splitlines(),lineterm='',n=0) if l[:1] in '+-' and l[:3] not in('+++','---'))
if __name__=='__main__':
    R=list(csv.DictReader(open('sq_test.csv')))
    print('rows',len(R),'labels',collections.Counter(r['label'] for r in R),'datasets',collections.Counter(r['dataset'] for r in R))
    print('transformations',collections.Counter(r['transformation'] for r in R).most_common(30))
    print('unique original programs',len({r['original_code'] for r in R}),'groups',len({r['groups'] for r in R}))
    c=collections.Counter(); per=collections.defaultdict(lambda: collections.Counter()); cache={}
    import random
    random.seed(0)
    sample=random.sample(R,400)
    for r in sample:
        o,t=r['original_code'],r['transformed_code']
        try: do=select_entry_structural(o); dt=select_entry_structural(t)
        except EntryPointError: c['no_entry']+=1; continue
        if not interfaces_correspond(do,dt) or do.name!=dt.name and False: c['iface_mismatch']+=1
        if o not in cache: cache[o]=go(o,do.name,do.inputs)
        ro=cache[o]
        if ro[0]!='ok' or any(x[0]=='exc' for x in ro[1]): c['orig_exc_or_fail']+=1; continue
        rt=go(t,dt.name,dt.inputs)
        if rt[0]!='ok': c['variant_fail']+=1; continue
        same=ro[1]==rt[1]
        c['eligible']+=1
        key=('SP' if r['label']=='1' else 'SA', 'oracle_same' if same else 'oracle_diff')
        c[key]+=1
    print(dict(c))
