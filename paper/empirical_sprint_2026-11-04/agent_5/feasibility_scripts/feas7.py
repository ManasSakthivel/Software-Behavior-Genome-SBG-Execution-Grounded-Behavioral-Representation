import json,sys,collections,warnings
warnings.filterwarnings('ignore'); sys.dont_write_bytecode=True
sys.path.insert(0,'/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')
from experiments.final.entry_policy import select_entry_structural, EntryPointError
from feas import go
rows=[]
for o in (0,100): rows+=[r['row'] for r in json.load(open(f'hep_{o}.json'))['rows']]
if __name__=='__main__':
    c=collections.Counter()
    for r in rows:
        can=r['declaration']+r['canonical_solution']; bug=r['declaration']+r['buggy_solution']
        try: d=select_entry_structural(can)
        except EntryPointError: continue
        a=go(can,d.name,d.inputs); b=go(bug,d.name,d.inputs)
        if a[0]!='ok' or b[0]!='ok': continue
        ok=sum(1 for x in a[1] if x[0]=='ok')
        for thr in (11,8,6,4,1):
            if ok>=thr:
                c[f'ge{thr}']+=1
                if a[1]!=b[1]: c[f'ge{thr}_witnessed']+=1
    print(dict(sorted(c.items())))
