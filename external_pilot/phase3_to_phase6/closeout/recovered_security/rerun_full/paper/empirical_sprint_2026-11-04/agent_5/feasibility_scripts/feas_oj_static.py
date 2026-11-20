# STATIC ONLY (no execution of OJ code, no SBG): how many EquiBench OJ_A / OJ_V programs fit the function-entry protocol.
import json,ast,sys,warnings
warnings.filterwarnings('ignore'); sys.dont_write_bytecode=True
sys.path.insert(0,'/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG')
from experiments.final.entry_policy import select_entry_structural, EntryPointError
def import_safe(src):
    t=ast.parse(src)
    for n in t.body:
        if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef)): continue
        if isinstance(n,ast.Assign) and isinstance(n.value,(ast.Constant,ast.List,ast.Dict,ast.Tuple,ast.Set)): continue
        if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='__name__': continue
        if isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant): continue
        return False
    return True
for f in ('oja.jsonl','ojv.jsonl'):
    R=[json.loads(l) for l in open(f)]; ok={}
    for r in R:
        for k in ('program_1','program_2'):
            p=r[k+'_path']; src=r[k+'_code']
            try: select_entry_structural(src); e=True
            except EntryPointError: e=False
            ok[p]=e and import_safe(src)
    print(f,'programs (unique paths):',len(ok),'entry+import-safe:',sum(ok.values()),'pairs with both members usable:',sum(1 for r in R if ok[r['program_1_path']] and ok[r['program_2_path']]))
