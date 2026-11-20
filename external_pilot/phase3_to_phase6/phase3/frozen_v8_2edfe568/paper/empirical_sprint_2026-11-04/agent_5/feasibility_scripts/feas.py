# FEASIBILITY ONLY: oracle outputs on the fixed battery. No SBG, no tracer.
import json, sys, copy, collections, multiprocessing as mp
sys.dont_write_bytecode=True
sys.path.insert(0,'/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')
from experiments.final.entry_policy import select_entry_structural, EntryPointError
rows=[]
for o in (0,100): rows+=[r['row'] for r in json.load(open(f'hep_{o}.json'))['rows']]

def run(src, name, inputs, q):
    import signal
    ns={}
    try:
        exec(compile(src,'<m>','exec'),ns)
    except BaseException as e:
        q.put(('load_error',repr(e)[:80])); return
    fn=ns[name]; outs=[]
    def h(*a): raise TimeoutError
    signal.signal(signal.SIGALRM,h)
    for x in copy.deepcopy(inputs):
        signal.setitimer(signal.ITIMER_REAL,1.0)
        try:
            a = x if isinstance(x,tuple) else (x,)
            outs.append(('ok',repr(fn(*a))[:300]))
        except BaseException as e:
            outs.append(('exc',type(e).__name__))
        finally:
            signal.setitimer(signal.ITIMER_REAL,0)
    q.put(('ok',outs))

def go(src,name,inputs):
    q=mp.Queue(); p=mp.Process(target=run,args=(src,name,inputs,q)); p.start()
    try: r=q.get(timeout=30)
    except Exception: r=('timeout',None)
    p.join(1)
    if p.is_alive(): p.kill()
    return r

if __name__=='__main__':
    stat=collections.Counter(); per=[]
    for r in rows:
        can=r['declaration']+r['canonical_solution']; bug=r['declaration']+r['buggy_solution']
        try: d=select_entry_structural(can)
        except EntryPointError as e: stat['no_entry:'+e.kind]+=1; continue
        stat['entry_ok']+=1
        a=go(can,d.name,d.inputs); b=go(bug,d.name,d.inputs)
        if a[0]!='ok' or b[0]!='ok': stat['harness_fail']+=1; continue
        co,bo=a[1],b[1]
        n_exc_can=sum(1 for x in co if x[0]=='exc')
        if n_exc_can==len(co): stat['canonical_all_exceptions']+=1
        if n_exc_can>0: stat['canonical_any_exception']+=1
        differs=any(x!=y for x,y in zip(co,bo))
        if n_exc_can>0: continue   # would be excluded per FRESH_PROGRAM_PROTOCOL §4
        stat['eligible_no_exception']+=1
        stat['eligible_bug_witnessed']+=differs
        per.append((r['task_id'],d.name,differs,r['bug_type']))
    print(dict(stat))
    c=collections.Counter((bt,dif) for _,_,dif,bt in per); print(sorted(c.items()))
