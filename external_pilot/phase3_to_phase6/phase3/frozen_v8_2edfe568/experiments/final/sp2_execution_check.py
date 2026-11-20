"""
Execute the self-tests of base and variant for every SP-2 pair flagged by
``data_integrity.py`` (dangling method reference) and record whether the
variant fails with AttributeError while the base passes. Read-only; labels are
not changed. Runs each program as a subprocess with a 20 s timeout.

Usage: python experiments/final/sp2_execution_check.py [--out FILE]
"""
import json,subprocess,sys,collections,pathlib
REPO=pathlib.Path(__file__).resolve().parents[2]
import os; os.chdir(REPO)
sys.path.insert(0,str(REPO/'experiments'/'final'))
import data_integrity as di
rep=di.check_dataset(REPO/'benchmark/datasets/v6')['defects']['sp2_dangling_method_reference']
rows={}
for s in ('train','dev','val','test'):
    for l in open(f'benchmark/datasets/v6/pairs_{s}.jsonl'):
        r=json.loads(l); rows[r['pair_id']]=r
res=collections.Counter(); detail=[]
for d in rep:
    r=rows[d['pair_id']]
    def run(p):
        try:
            c=subprocess.run([sys.executable,p],capture_output=True,text=True,timeout=20)
            return c.returncode,c.stderr.strip().splitlines()[-1] if c.stderr.strip() else ''
        except subprocess.TimeoutExpired: return 'timeout',''
    b=run(r['base_path']); v=run(r['variant_path'])
    attr = isinstance(v[0],int) and v[0]!=0 and 'AttributeError' in v[1]
    res[('base_ok' if b[0]==0 else 'base_fail', 'var_ok' if v[0]==0 else ('var_attr' if attr else 'var_other_fail'))]+=1
    detail.append({'pair_id':d['pair_id'],'split':d['split'],'base':b,'variant':v,'names':d['names']})
print(res)
out=pathlib.Path(sys.argv[sys.argv.index('--out')+1]) if '--out' in sys.argv else REPO/'reports/remediation/results/sp2_dangling_execution_check.json'
out.parent.mkdir(parents=True,exist_ok=True)
json.dump({'summary':{' / '.join(k):v for k,v in res.items()},'pairs':detail},open(out,'w'),indent=1)
