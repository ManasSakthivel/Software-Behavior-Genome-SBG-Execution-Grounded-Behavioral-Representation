# LABEL-RELIABILITY check only: run HumanEvalPack's own unit tests on canonical and buggy (no SBG).
import json,sys,multiprocessing as mp,collections,signal,warnings
warnings.filterwarnings('ignore'); sys.dont_write_bytecode=True
rows=[]
for o in (0,100): rows+=[r['row'] for r in json.load(open(f'hep_{o}.json'))['rows']]
def run(code,q):
    def h(*a): raise TimeoutError
    signal.signal(signal.SIGALRM,h); signal.setitimer(signal.ITIMER_REAL,5)
    try:
        exec(compile(code,'<t>','exec'),{'__name__':'t'}); q.put('pass')
    except AssertionError: q.put('fail')
    except BaseException as e: q.put('err:'+type(e).__name__)
def go(code):
    q=mp.Queue(); p=mp.Process(target=run,args=(code,q)); p.start()
    try: r=q.get(timeout=20)
    except Exception: r='timeout'
    p.join(1)
    if p.is_alive(): p.kill()
    return r
if __name__=='__main__':
    c=collections.Counter()
    for r in rows:
        can=r['declaration']+r['canonical_solution']+'\n'+r['test']; bug=r['declaration']+r['buggy_solution']+'\n'+r['test']
        a=go(can); b=go(bug); c[('canonical',a)]+=1; c[('buggy','pass' if b=='pass' else 'notpass')]+=1
    print(dict(c))
