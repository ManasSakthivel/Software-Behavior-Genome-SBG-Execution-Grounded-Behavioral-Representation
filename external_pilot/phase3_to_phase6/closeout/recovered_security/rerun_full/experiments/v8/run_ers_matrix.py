"""ERS control matrix on the DEVELOPMENT records with the actual fitted model (full_profile, no ERS features).
DEVELOPMENT / EXPLORATORY. Usage: python experiments/v8/run_ers_matrix.py OUT_DIR"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sbgv8 import calibrate, ers, schema
from sbgv8.schema import EvidenceRecord
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
recs = [EvidenceRecord.from_json(l) for l in open("datasets/v8/dev_records.jsonl")]
model = calibrate.fit(recs, schema.FEATURE_SETS["full_profile"])
rep = ers.run_matrix(recs, model)
json.dump(rep if isinstance(rep, (dict, list)) else str(rep), open(os.path.join(out, "ers_matrix.json"), "w"), indent=1, default=str)
print(json.dumps(rep, default=str)[:3000])
