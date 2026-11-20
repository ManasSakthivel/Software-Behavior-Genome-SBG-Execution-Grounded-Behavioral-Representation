# DESIGN-LEVEL ONLY (static, canonical ast.unparse edit size as in experiments/final/edit_size_analysis.py). No SBG, no tracer.
import json,ast,csv,difflib,collections,sys,warnings
warnings.filterwarnings('ignore'); sys.dont_write_bytecode=True; csv.field_size_limit(10**8)
def canon(s):
    try: return ast.unparse(ast.parse(s)).splitlines()
    except SyntaxError: return None
def es(a,b):
    A,B=canon(a),canon(b)
    if A is None or B is None: return None
    return sum(1 for l in difflib.unified_diff(A,B,lineterm='',n=0) if l[:1] in '+-' and l[:3] not in('+++','---'))
rows=[]
for o in (0,100): rows+=[r['row'] for r in json.load(open(f'hep_{o}.json'))['rows']]
hp=[]
for o in (0,100): hp+=[r['row'] for r in json.load(open(f'hp_{o}.json'))['rows']]
# HumanEval: buggy vs canonical (CH) ; EvalPlus canonical vs OpenAI canonical (EQ-candidate)
ch=[es(r['declaration']+r['canonical_solution'],r['declaration']+r['buggy_solution']) for r in rows]
eq=[es(r['declaration']+r['canonical_solution'],h['prompt']+h['canonical_solution']) for r,h in zip(rows,hp)]
print('HE CH edit (canonical-unparse lines):',collections.Counter(ch).most_common(6))
print('HE EQ-candidate (OpenAI vs EvalPlus canonical) edit: quartiles',sorted(x for x in eq if x is not None)[len(eq)//4],sorted(x for x in eq if x is not None)[len(eq)//2],sorted(x for x in eq if x is not None)[3*len(eq)//4])
print('HE: fraction of EQ-candidate pairs with edit<=max CH edit(8):',round(sum(1 for x in eq if x is not None and x<=8)/len(eq),3))
# SeqCoBench test, DCS excluded: per transformation canonical edit
R=[r for r in csv.DictReader(open('sq_test.csv')) if 'dissimilar' not in r['transformation']]
by=collections.defaultdict(list)
for r in R:
    e=es(r['original_code'],r['transformed_code'])
    if e is not None: by[('SA' if r['label']=='0' else 'SP')].append(e)
import statistics
for k,v in by.items(): print('SeqCoBench',k,len(v),'median',statistics.median(v),'p10/p90',sorted(v)[len(v)//10],sorted(v)[9*len(v)//10])
sa=by['SA']; sp=by['SP']
frac=sum(1 for x in sp if min(sa)<=x<=max(sa))/len(sp); print('SP pairs within SA edit range [',min(sa),',',max(sa),']:',round(frac,3))
