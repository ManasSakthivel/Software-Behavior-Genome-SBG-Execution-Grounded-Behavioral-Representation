import json,ast,sys,collections,statistics,warnings
warnings.filterwarnings('ignore'); sys.dont_write_bytecode=True
sys.path.insert(0,'/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')
from experiments.final.entry_policy import select_entry_structural, EntryPointError
from feas import go
rows=[]
for o in (0,100): rows+=[r['row'] for r in json.load(open(f'hep_{o}.json'))['rows']]
def shape(src, name):
    t=ast.parse(src); f=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name][0]
    br=any(isinstance(n,(ast.If,ast.IfExp)) for n in ast.walk(f))
    loop=any(isinstance(n,(ast.For,ast.While)) for n in ast.walk(f))
    comp=any(isinstance(n,(ast.ListComp,ast.SetComp,ast.DictComp,ast.GeneratorExp)) for n in ast.walk(f))
    rec=any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==name for n in ast.walk(f))
    return br, loop or rec, loop or rec or comp
if __name__=='__main__':
    loc=[]; c=collections.Counter()
    for r in rows:
        can=r['declaration']+r['canonical_solution']; bug=r['declaration']+r['buggy_solution']
        loc.append(len([l for l in r['canonical_solution'].splitlines() if l.strip()]))
        try: d=select_entry_structural(can)
        except EntryPointError: continue
        a=go(can,d.name,d.inputs)
        if a[0]!='ok' or any(x[0]=='exc' for x in a[1]): continue
        b=go(bug,d.name,d.inputs)
        if b[0]!='ok': continue
        wit=any(x!=y for x,y in zip(a[1],b[1]))
        br,strict,loose=shape(can,d.name)
        c['zero_exc']+=1
        c['zero_exc_branch_and_strictloop']+= (br and strict)
        c['zero_exc_branch_and_loop_or_comp']+= (br and loose)
        if wit:
            c['witnessed']+=1; c['witnessed_branch_and_strictloop']+=(br and strict); c['witnessed_branch_and_loop_or_comp']+=(br and loose)
    print(dict(c)); print('LOC median',statistics.median(loc),'mean',round(statistics.mean(loc),1),'max',max(loc))
