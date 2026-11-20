"""
FIGURE 4 — Hard-Negative Evaluation: SC-3 / SC-11 Semantic Clones
==================================================================
STATUS : PLACEHOLDER_PENDING_DATA

Requires:
  - SC-3 test suite  : algorithm-equivalent rewrites (e.g. bubble sort ↔ merge sort)
  - SC-11 test suite : cross-language semantic clones
  - H10 experiment   : not yet evaluated (artifacts/v2/PHASE_2_GATE.json)
  - H11 experiment   : not yet evaluated (artifacts/v2/PHASE_2_GATE.json)

Intended figure type : Grouped bar chart
  x-axis : System (V1 Static, V2 Dynamic, AST)
  y-axis : AUROC on SC-3 / SC-11 hard-negative subsets
  Groups : SC-3 (algorithm variants), SC-11 (cross-language)

To generate this figure:
  1. Run H10 and H11 experiments and write results to:
       artifacts/v2/H10/results_test.json
       artifacts/v2/H11/results_test.json
  2. Remove this placeholder and implement the plot below.

Source to check for readiness:
  artifacts/v2/PHASE_2_GATE.json → hypothesis_verdicts.H10 / H11
"""

import json
import os
import sys

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
gate_path = os.path.join(REPO_ROOT, "artifacts", "v2", "PHASE_2_GATE.json")

with open(gate_path) as f:
    gate = json.load(f)

h10 = gate["hypothesis_verdicts"]["H10"]
h11 = gate["hypothesis_verdicts"]["H11"]

OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT_DIR, exist_ok=True)

placeholder = {
    "status": "PLACEHOLDER_PENDING_DATA",
    "figure": "FIGURE 4",
    "title": "Hard-Negative Evaluation: SC-3 / SC-11 Semantic Clones",
    "h10_status": h10,
    "h11_status": h11,
    "data_needed": [
        "artifacts/v2/H10/results_test.json",
        "artifacts/v2/H11/results_test.json",
    ],
    "source_gate": "artifacts/v2/PHASE_2_GATE.json",
}

out = os.path.join(OUT_DIR, "fig4_hard_negative_PLACEHOLDER.json")
with open(out, "w") as f:
    json.dump(placeholder, f, indent=2)

print("[fig4] PLACEHOLDER_PENDING_DATA")
print(f"       H10 status: {h10}")
print(f"       H11 status: {h11}")
print(f"       Written → {out}")
print("       Action required: run H10 and H11 experiments, then implement this figure.")
sys.exit(0)
