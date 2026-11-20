"""sbgv8/independent_validation/blinded_export.py — Blinded Adjudication Package Generator & Lock Manifest.

Locks SBG V8 predictions before human adjudication:
- Generates locked_predictions_manifest.json with full cryptographic hashes.
- Generates reviewer-facing blinded adjudication sheets (stripping all SBG verdicts, risk scores, ERS values, and labels).
- Computes SHA-256 integrity hash of the complete sealed prediction package.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any


def generate_blinded_package(
    candidate_pairs: List[Dict[str, Any]],
    execution_results: Dict[str, Any],
    out_dir: Path,
) -> Dict[str, Any]:
    """Generates locked prediction package and reviewer-facing blinded adjudication packet."""
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Locked Predictions (Contains full SBG outputs, hashed & sealed)
    locked_predictions = []
    for pair_res in execution_results["pairs_data"]:
        pair_id = pair_res["pair_id"]
        locked_predictions.append({
            "pair_id": pair_id,
            "dataset": pair_res["dataset"],
            "project": pair_res["project"],
            "family": pair_res["family"],
            "sbg_verdict": pair_res["verdict"],
            "risk_score": pair_res["risk_score"],
            "ers_pass_rate": pair_res["ers_pass_rate"],
            "profile_digest": hashlib.sha256(json.dumps(pair_res["profile"], sort_keys=True).encode()).hexdigest(),
            "evidence_digest": hashlib.sha256(pair_res["evidence_record_json"].encode()).hexdigest(),
        })
        
    locked_json_str = json.dumps(locked_predictions, indent=2, sort_keys=True)
    locked_manifest_path = out_dir / "locked_predictions_manifest.json"
    locked_manifest_path.write_text(locked_json_str, encoding="utf-8")
    
    package_sha256 = hashlib.sha256(locked_json_str.encode()).hexdigest()
    
    # 2. Reviewer-facing Blinded Package (NO SBG predictions, NO risk scores, NO ground truth labels)
    reviewer_cases = []
    for pair in candidate_pairs:
        reviewer_cases.append({
            "case_id": pair["pair_id"],
            "dataset": pair["dataset"],
            "project": pair["project"],
            "language": pair["language"],
            "build_system": pair["build_system"],
            "file_path": pair["file_path"],
            "buggy_sha": pair["buggy_sha"],
            "fixed_sha": pair["fixed_sha"],
            "repo_url": pair.get("repo_url", ""),
            "change_description": pair.get("description", ""),
            "patch_diff": pair["patch_diff"],
            "executed_test_descriptions": [
                {"test_id": f"test_{idx+1}", "input_params": tc.get("input")}
                for idx, tc in enumerate(pair.get("test_suite", []))
            ],
            "adjudication_fields": {
                "adjudicator_verdict": "[ CONFIRMED_DIVERGENCE | NO_DIVERGENCE_FOUND_WITHIN_BUDGET | INDETERMINATE ]",
                "divergence_observed_notes": "",
                "adjudicator_confidence": "[ HIGH | MEDIUM | LOW ]",
                "adjudicator_id": "",
            }
        })
        
    blinded_json_str = json.dumps(reviewer_cases, indent=2)
    blinded_path = out_dir / "blinded_adjudication_cases.json"
    blinded_path.write_text(blinded_json_str, encoding="utf-8")
    
    # 3. CSV Adjudication Form for human reviewers
    csv_lines = [
        "case_id,dataset,project,language,adjudicator_verdict,adjudicator_confidence,adjudicator_id,notes"
    ]
    for case in reviewer_cases:
        csv_lines.append(
            f'"{case["case_id"]}","{case["dataset"]}","{case["project"]}","{case["language"]}","","","",""'
        )
    csv_path = out_dir / "blinded_adjudication_template.csv"
    csv_path.write_text("\n".join(csv_lines), encoding="utf-8")
    
    manifest_meta = {
        "status": "SEALED_LOCKED",
        "n_cases": len(reviewer_cases),
        "package_sha256": package_sha256,
        "locked_manifest_file": str(locked_manifest_path.name),
        "blinded_cases_file": str(blinded_path.name),
        "blinded_template_csv": str(csv_path.name),
        "instructions": (
            "This prediction package is cryptographically locked and sealed prior to human adjudication. "
            "Reviewers must populate blinded_adjudication_template.csv without access to locked_predictions_manifest.json."
        ),
    }
    
    meta_path = out_dir / "prediction_lock_metadata.json"
    meta_path.write_text(json.dumps(manifest_meta, indent=2), encoding="utf-8")
    
    return manifest_meta
