# FEASIBILITY ONLY: HumanEval canonical (OpenAI, via HumanEvalPack python split) vs EvalPlus canonical, oracle outputs on fixed battery. No SBG.
import json,sys,collections,difflib,statistics,warnings
warnings.filterwarnings('ignore'); sys.dont_write_bytecode=True
sys.path.insert(0,'/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')
from experiments.final.entry_policy import select_entry_structural, EntryPointError
from feas import go
A=[];B=[]
for o in (0,100):
    A+=[r['row'] for r in json.load(open(f'hep_{o}.json'))['rows']]
    B+=[r['row'] for r in json.load(open(f'hp_{o}.json'))['rows']]
def esize(a,b):
    return sum(1 for l in difflib.unified_diff(a.splitlines(),b.splitlines(),lineterm='',n=0) if l[:1] in '+-' and l[:3] not in ('+++','---'))
if __name__=='__main__':
    c=collections.Counter(); sizes_eq=[]; sizes_ch=[]
    for x,y in zip(A,B):
        assert x['entry_point']==y['entry_point']
        src_a=x['declaration']+x['canonical_solution']
        src_b=y['prompt']+y['canonical_solution']
        try: d=select_entry_structural(src_a)
        except EntryPointError: c['no_entry']+=1; continue
        ra=go(src_a,d.name,d.inputs); rb=go(src_b,d.name,d.inputs)
        if ra[0]!='ok' or rb[0]!='ok': c['harness_fail']+=1; continue
        if any(t[0]=='exc' for t in ra[1]): c['excluded_exceptions']+=1; continue
        same=ra[1]==rb[1]
        s=esize(src_a,src_b)
        c['eligible']+=1
        if s==0: c['identical_source']+=1; continue
        (c.__setitem__('eq_diff_source',c['eq_diff_source']+1), sizes_eq.append(s)) if same else (c.__setitem__('ch_diff_source',c['ch_diff_source']+1), sizes_ch.append(s))
    print(dict(c)); print('edit size EQ median',statistics.median(sizes_eq) if sizes_eq else None,'CH',statistics.median(sizes_ch) if sizes_ch else None)
