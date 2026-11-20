# DESIGN-LEVEL ONLY (static; canonical ast.unparse edit size, docstrings stripped). No SBG, no execution.
import json,ast,difflib,collections,statistics,sys,warnings
warnings.filterwarnings('ignore'); sys.dont_write_bytecode=True
def canon_nodoc(s):
    t=ast.parse(s)
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.Module)) and n.body and isinstance(n.body[0],ast.Expr) and isinstance(getattr(n.body[0],'value',None),ast.Constant) and isinstance(n.body[0].value.value,str):
            n.body=n.body[1:] or [ast.Pass()]
    return ast.unparse(t).splitlines()
def es(a,b):
    A,B=canon_nodoc(a),canon_nodoc(b)
    return sum(1 for l in difflib.unified_diff(A,B,lineterm='',n=0) if l[:1] in '+-' and l[:3] not in('+++','---'))
A=[];B=[]
for o in (0,100):
    A+=[r['row'] for r in json.load(open(f'hep_{o}.json'))['rows']]
    B+=[r['row'] for r in json.load(open(f'hp_{o}.json'))['rows']]
ch=[es(x['declaration']+x['canonical_solution'],x['declaration']+x['buggy_solution']) for x in A]
eq=[es(x['declaration']+x['canonical_solution'],y['prompt']+y['canonical_solution']) for x,y in zip(A,B)]
print('CH (buggy vs canonical) edit:',sorted(collections.Counter(ch).items()))
q=lambda v:(sorted(v)[len(v)//4],sorted(v)[len(v)//2],sorted(v)[3*len(v)//4])
print('EQ-candidate (EvalPlus canonical vs OpenAI canonical) edit quartiles:',q(eq),'min',min(eq),'identical-after-canon:',sum(1 for e in eq if e==0))
print('fraction of EQ-candidates with edit<=2:',round(sum(1 for e in eq if e<=2)/len(eq),3),' <=4:',round(sum(1 for e in eq if e<=4)/len(eq),3),' <=8:',round(sum(1 for e in eq if e<=8)/len(eq),3))
