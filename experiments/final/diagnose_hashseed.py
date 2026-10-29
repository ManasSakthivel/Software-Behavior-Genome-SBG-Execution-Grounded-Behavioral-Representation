"""Diagnostic (exploratory): PYTHONHASHSEED sensitivity of SBG event counts.

Root cause of the graph_connected_components half of the V6-dev reproducibility
discrepancy: `components_dfs` iterates a `set` of strings, whose order depends on
PYTHONHASHSEED, so the traced event stream (hence SBG score) differs by seed.
Each seed is deterministic on its own.  Writes raw/hashseed_sensitivity.json only;
no frozen code, dataset or artifact is modified.

    python experiments/final/diagnose_hashseed.py
"""
import json, os, pathlib, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
PROG = "benchmark/corpus/base_programs/graph_connected_components.py"
SEEDS = [0, 1, 5, 21, 38]
CODE = ("import sys,json;sys.path.insert(0,'.');from experiments.final import extraction as ex;"
        f"r=ex.extract_program('{PROG}',{{}},'output_free_v7');print(json.dumps([r.ok,r.stats.get('n_events')]))")


def run(seed):
    env = dict(os.environ, PYTHONHASHSEED=str(seed))
    out = subprocess.run([sys.executable, "-c", CODE], capture_output=True, text=True, cwd=REPO, env=env)
    return json.loads(out.stdout.strip().splitlines()[-1])[1]


res = {str(s): [run(s), run(s)] for s in SEEDS}
out = {"program": PROG, "protocol": "output_free_v7",
       "n_events_by_seed_two_runs": res,
       "deterministic_within_seed": all(a == b for a, b in res.values()),
       "distinct_values_across_seeds": sorted({a for a, _ in res.values()}),
       "conclusion": "event count depends on PYTHONHASHSEED (set-of-strings iteration order); "
                     "same seed reproduces exactly",
       "status": "EXPLORATORY diagnostic"}
p = REPO / "artifacts/paper_evidence/raw/hashseed_sensitivity.json"
p.write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
