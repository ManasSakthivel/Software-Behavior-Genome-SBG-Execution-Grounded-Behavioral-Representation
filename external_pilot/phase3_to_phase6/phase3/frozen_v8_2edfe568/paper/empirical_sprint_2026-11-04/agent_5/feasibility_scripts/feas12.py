# FEASIBILITY ONLY: SeqCoBench matched-size stratum yield. Oracle outputs on fixed battery + canonical edit size. NO SBG, NO tracer.
import csv,sys,json,ast,difflib,copy,signal,collections,warnings,multiprocessing as mp
warnings.filterwarnings('ignore'); sys.dont_write_bytecode=True; csv.field_size_limit(10**8)
sys.path.insert(0,'/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')
from experiments.final.entry_policy import select_entry_structural, EntryPointError, interfaces_correspond
def canon(s):
    try: return ast.unparse(ast.parse(s)).splitlines()
    except SyntaxError: return None
def esize(a,b):
    A,B=canon(a),canon(b)
    if A is None or B is None: return None
    return sum(1 for l in difflib.unified_diff(A,B,lineterm='',n=0) if l[:1] in '+-' and l[:3] not in('+++','---'))
class TO(Exception): pass
def _h(*a): raise TO()
def oracle(src,name,inputs):
    ns={}
    signal.signal(signal.SIGALRM,_h)
    signal.setitimer(signal.ITIMER_REAL,2.0)
    try: exec(compile(src,'<m>','exec'),ns)
    except BaseException as e: return ('load_error',)
    finally: signal.setitimer(signal.ITIMER_REAL,0)
    fn=ns.get(name)
    if fn is None: return ('no_fn',)
    outs=[]
    for x in copy.deepcopy(inputs):
        signal.setitimer(signal.ITIMER_REAL,1.0)
        try:
            a=x if isinstance(x,tuple) else (x,)
            outs.append(('ok',repr(fn(*a))[:300]))
        except BaseException as e: outs.append(('exc',type(e).__name__))
        finally: signal.setitimer(signal.ITIMER_REAL,0)
    return ('ok',outs)
def work(args):
    split,orig,rows=args
    res={'orig':None,'rows':[]}
    try: do=select_entry_structural(orig)
    except EntryPointError as e: return (split,orig[:0],'no_entry',[])
    ro=oracle(orig,do.name,do.inputs)
    if ro[0]!='ok': return (split,'', 'orig_fail',[])
    if any(x[0]=='exc' for x in ro[1]): return (split,'','orig_exc',[])
    out=[]
    for r in rows:
        t=r['transformed_code']; lab=r['label']; tr=r['transformation']
        e=esize(orig,t)
        try: dt=select_entry_structural(t)
        except EntryPointError: out.append((lab,tr,e,'variant_no_entry')); continue
        ok_iface=interfaces_correspond(do,dt) and dt.name==do.name
        rt=oracle(t,do.name,do.inputs) if dt.name==do.name else ('name_changed',)
        if rt[0]!='ok': out.append((lab,tr,e,'variant_'+rt[0], ok_iface)); continue
        out.append((lab,tr,e,'same' if rt[1]==ro[1] else 'diff', ok_iface))
    return (split,'','eligible',out)
if __name__=='__main__':
    jobs=[]
    for sp in ('test','valid','train'):
        R=list(csv.DictReader(open(f'sq_{sp}.csv')))
        P=collections.OrderedDict()
        for r in R:
            if 'dissimilar' in r['transformation']: continue
            P.setdefault(r['original_code'],[]).append(r)
        for o,rows in P.items(): jobs.append((sp,o,rows))
    PER=[]; nprog=collections.Counter()
    with mp.Pool(8,maxtasksperchild=25) as pool:
        for sp,_,status,out in pool.imap_unordered(work,jobs,chunksize=2):
            nprog[(sp,status)]+=1
            if status!='eligible': continue
            c=collections.Counter()
            for t in out:
                lab,tr,e,res=t[0],t[1],t[2],t[3]; iface=t[4] if len(t)>4 else None
                cls='SP' if lab=='1' else 'SA'
                if res in ('same','diff') and iface is False: c['iface_excluded']+=1; continue
                if e==2 and ((cls=='SP' and res=='same') or (cls=='SA' and res=='diff')): c[cls+'_in_stratum']+=1
                if res in ('same','diff'): c[cls+'_'+res+'_all']+=1
            c['_split']=sp; PER.append(dict(c))
    out={}
    for sp in ('train','valid','test'):
        P=[c for c in PER if c['_split']==sp]
        out[sp]={'programs_eligible_zero_exc':len(P),
                 'with_both_classes_at_e2':sum(1 for c in P if c.get('SP_in_stratum',0)>0 and c.get('SA_in_stratum',0)>0),
                 'pairs_SP_e2':sum(c.get('SP_in_stratum',0) for c in P),'pairs_SA_e2':sum(c.get('SA_in_stratum',0) for c in P)}
    print(json.dumps(out))
