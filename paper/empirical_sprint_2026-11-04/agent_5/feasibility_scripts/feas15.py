# DESIGN-LEVEL ONLY: HumanEval(Pack) CH=(canonical,buggy) vs EQ-candidate=(OpenAI canonical, EvalPlus canonical); oracle on fixed battery; repo edit-size definition. NO SBG.
import json,sys,ast,difflib,collections,warnings,bisect
warnings.filterwarnings('ignore'); sys.dont_write_bytecode=True
sys.path.insert(0,'/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')
from experiments.final.entry_policy import select_entry_structural, EntryPointError
from feas import go
A=[];B=[]
for o in (0,100):
    A+=[r['row'] for r in json.load(open(f'hep_{o}.json'))['rows']]
    B+=[r['row'] for r in json.load(open(f'hp_{o}.json'))['rows']]
def canon(s): return ast.unparse(ast.parse(s)).splitlines()
def es(a,b): return sum(1 for l in difflib.unified_diff(canon(a),canon(b),lineterm='',n=0) if l[:1] in '+-' and l[:3] not in('+++','---'))
def shape(src,name):
    f=[n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name==name][0]
    br=any(isinstance(n,(ast.If,ast.IfExp)) for n in ast.walk(f))
    lp=any(isinstance(n,(ast.For,ast.While)) for n in ast.walk(f)) or any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==name for n in ast.walk(f))
    return br and lp
def auroc(s,y):
    pos=[x for x,l in zip(s,y) if l]; neg=sorted(x for x,l in zip(s,y) if not l); g=0
    for p in pos: g+=bisect.bisect_left(neg,p)+0.5*(bisect.bisect_right(neg,p)-bisect.bisect_left(neg,p))
    return g/(len(pos)*len(neg))
if __name__=='__main__':
    c=collections.Counter(); S=[];Y=[]; both_ids=[]
    for x,y in zip(A,B):
        can=x['declaration']+x['canonical_solution']; bug=x['declaration']+x['buggy_solution']; ep=y['prompt']+y['canonical_solution']
        try: d=select_entry_structural(can)
        except EntryPointError: continue
        r0=go(can,d.name,d.inputs)
        if r0[0]!='ok' or any(t[0]=='exc' for t in r0[1]): continue
        rb=go(bug,d.name,d.inputs); re_=go(ep,d.name,d.inputs)
        if rb[0]!='ok' or re_[0]!='ok': continue
        c['zero_exc']+=1; nt=shape(can,d.name)
        ch = r0[1]!=rb[1]; eqp = (r0[1]==re_[1]) and es(can,ep)>0
        if ch: c['CH_witnessed']+=1; S.append(es(can,bug)); Y.append(1)
        if eqp: c['EQ_oracle_same_nonidentical']+=1; S.append(es(can,ep)); Y.append(0)
        if ch and eqp: c['programs_with_both']+=1; c['programs_with_both_branchloop']+= nt; both_ids.append(x['task_id'])
        if r0[1]!=re_[1]: c['EQ_candidate_oracle_differs']+=1
    print(dict(c)); print('forward edit AUROC (CH+, EQ-) =',round(auroc(S,Y),3),'reversed =',round(1-auroc(S,Y),3))
