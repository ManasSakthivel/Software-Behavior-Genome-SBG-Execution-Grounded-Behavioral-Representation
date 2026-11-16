"""
FIGURE 5 — Robustness to Refactoring Perturbations
====================================================
STATUS : PLACEHOLDER_PENDING_DATA

Requires:
  - H12 experiment : robustness sweep over perturbation types
                     (variable renaming, dead-code insertion, loop unrolling, etc.)
  - Not yet evaluated (artifacts/v2/PHASE_2_GATE.json)

Intended figure type : Line chart
  x-axis : Perturbation intensity (e.g. % tokens changed)
  y-axis : AUROC on perturbed pairs
  Lines  : V1 Static SBG, V2 Dynamic, V2 Hybrid, AST baseline

Also needed:
  - SAFEGUARD-6 noise floor with n_runs=5 (currently n_runs=1, insufficient).
    See: artifacts/v2/PHASE_2_GATE.json → open_issues[2]

To generate this figure:
  1. Run H12 robustness experiments and write results to:
       artifacts/v2/H12/results_robustness.json
  2. Increase SAFEGUARD-6 n_runs to 5 and record noise floor.
  3. Remove this placeholder and implement the plot below.

Source to check for readiness:
  artifacts/v2/PHASE_2_GATE.json → hypothesis_verdicts.H12
"""

import json
import os
import sys

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
gate_path = os.path.join(REPO_ROOT, "artifacts", "v2", "PHASE_2_GATE.json")

with open(gate_path) as f:
    gate = json.load(f)

h12 = gate["hypothesis_verdicts"]["H12"]

OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT_DIR, exist_ok=True)

placeholder = {
    "status": "PLACEHOLDER_PENDING_DATA",
    "figure": "FIGURE 5",
    "title": "Robustness to Refactoring Perturbations",
    "h12_status": h12,
    "safeguard_6_note": gate["safeguards_verified"]["SAFEGUARD-6"],
    "open_issues": gate["open_issues"],
    "data_needed": [
        "artifacts/v2/H12/results_robustness.json",
        "SAFEGUARD-6 noise floor with n_runs=5",
    ],
    "source_gate": "artifacts/v2/PHASE_2_GATE.json",
}

out = os.path.join(OUT_DIR, "fig5_robustness_PLACEHOLDER.json")
with open(out, "w") as f:
    json.dump(placeholder, f, indent=2)

print("[fig5] PLACEHOLDER_PENDING_DATA")
print(f"       H12 status: {h12}")
print(f"       Written → {out}")
print("       Action required: run H12 experiments and increase SAFEGUARD-6 n_runs to 5.")
sys.exit(0)
