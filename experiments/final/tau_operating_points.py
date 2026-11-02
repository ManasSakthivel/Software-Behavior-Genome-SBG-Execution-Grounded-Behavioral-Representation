"""Operating point of the frozen tau* on dev/train/v8-dev VALID pairs (no test split read)."""
import json,sys
sys.path.insert(0,'.')
from experiments.final.build_paper_evidence import RUNS, valid_rows
tau=json.load(open('artifacts/final/THRESHOLD_FROZEN.json'))['tau_star']
out={'tau_star':tau,'rule':'detected iff sbg_v5 > tau_star','source':'artifacts/final/THRESHOLD_FROZEN.json'}
for run in ('v6dev_v7','v6train_v7','v8dev_v8_rescore'):
    rows=valid_rows(run)
    p=[r for r in rows if r['label']==1]; n=[r for r in rows if r['label']==0]
    tp=sum(r['scores']['sbg_v5']>tau for r in p); fp=sum(r['scores']['sbg_v5']>tau for r in n)
    out[run]={'n_changed':len(p),'n_equivalent':len(n),'tpr':round(tp/len(p),6),'fpr':round(fp/len(n),6),'youden_j':round(tp/len(p)-fp/len(n),6)}
json.dump(out,open('artifacts/paper_evidence/raw/tau_operating_points.json','w'),indent=2)
print(json.dumps(out,indent=1))
