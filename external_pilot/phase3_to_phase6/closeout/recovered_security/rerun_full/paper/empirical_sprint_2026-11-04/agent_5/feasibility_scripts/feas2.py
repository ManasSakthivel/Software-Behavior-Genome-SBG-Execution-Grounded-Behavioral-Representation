# FEASIBILITY ONLY (oracle outputs on fixed battery; no SBG): MBPP+ canonical-code eligibility
import json, sys, copy, collections, multiprocessing as mp, warnings
warnings.filterwarnings('ignore'); sys.dont_write_bytecode=True
sys.path.insert(0,'/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')
from experiments.final.entry_policy import select_entry_structural, EntryPointError
from feas import go
rows=[]
for o in (0,100,200,300): rows+=[r['row'] for r in json.load(open(f'mp_{o}.json'))['rows']]
if __name__=='__main__':
    st=collections.Counter()
    for r in rows:
        try: d=select_entry_structural(r['code'])
        except EntryPointError: st['no_entry']+=1; continue
        a=go(r['code'],d.name,d.inputs)
        if a[0]!='ok': st['harness_fail']+=1; continue
        ne=sum(1 for x in a[1] if x[0]=='exc')
        st['zero_exc' if ne==0 else ('all_exc' if ne==len(a[1]) else 'some_exc')]+=1
    print(dict(st))
