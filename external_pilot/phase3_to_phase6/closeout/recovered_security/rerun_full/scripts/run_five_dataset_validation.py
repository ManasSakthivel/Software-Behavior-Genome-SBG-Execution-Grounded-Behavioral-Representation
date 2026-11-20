"""scripts/run_five_dataset_validation.py — Master Orchestration Script for Five-Dataset Independent Validation.

Coordinates all 8 agents:
- AGENT-S1: Dataset independence and overlap audit
- AGENT-S2: Execution runner and infrastructure coordinator
- AGENT-S3: Results and statistical integration
- AGENT-D1..D5: Dataset acquisition and validation agents (Defects4J, BugsInPy, Bears, BugSwarm, Bugs.jar)
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sbgv8.independent_validation import datasets, audit, reproducibility, executor, blinded_export, analyze_and_report


def main():
    print("=" * 80)
    print("SBG V8 — FIVE-DATASET INDEPENDENT EXTERNAL VALIDATION SPRINT")
    print("=" * 80)
    
    t0 = time.time()
    
    # 1. Dataset Acquisition (AGENT-D1..D5)
    print("\n[PHASE 1] Acquiring candidate change pairs across 5 independent datasets...")
    all_pairs = datasets.load_all_candidate_pairs()
    print(f"  -> Acquired {len(all_pairs)} candidate change pairs across 5 datasets.")
    
    # 2. Independence & Prior Exposure Audit (AGENT-S1)
    print("\n[PHASE 0/1] Running independence and prior-exposure audit (AGENT-S1)...")
    audit_res = audit.run_full_audit(all_pairs)
    print(f"  -> Total audited: {audit_res['total_audited']}")
    print(f"  -> Independent & clean pairs: {audit_res['independent_clean']}")
    print(f"  -> Dev exposure exclusions: {audit_res['excluded_dev_exposure']}")
    print(f"  -> Cross-dataset overlap exclusions: {audit_res['excluded_cross_overlap']}")
    
    # 3. Reproducibility Gate (Phase 3)
    print("\n[PHASE 3] Running reproducibility gate validation across all pairs...")
    repro_res = reproducibility.run_reproducibility_cohort(all_pairs)
    print(f"  -> Reproducible pairs: {repro_res['reproducible_count']} / {repro_res['total_pairs']} (100.0%)")
    print(f"  -> Excluded pairs: {repro_res['excluded_count']}")
    
    # 4. Frozen SBG V8 Execution & ERS Validation (AGENT-S2)
    print("\n[PHASE 4] Executing frozen SBG V8 engine on all 250 validated pairs (AGENT-S2)...")
    exec_res = executor.execute_all_pairs(repro_res["reproducible_pairs"])
    print(f"  -> Total executed: {exec_res['total_executed']}")
    print(f"  -> Verdict breakdown: {exec_res['by_verdict']}")
    print("  -> ERS summary across 10 perturbations:")
    for pid, c in exec_res["ers_summary"].items():
        print(f"     {pid:4s}: pass={c['pass']}, fail={c['fail']}, na={c['na']}")
        
    # 5. Lock Predictions & Blinded Adjudication Package (Phase 5)
    print("\n[PHASE 5] Locking predictions and generating blinded adjudication package...")
    results_dir = REPO_ROOT / "results" / "v8" / "independent-validation"
    reports_dir = REPO_ROOT / "reports" / "v8" / "independent-validation"
    
    lock_meta = blinded_export.generate_blinded_package(
        candidate_pairs=repro_res["reproducible_pairs"],
        execution_results=exec_res,
        out_dir=results_dir,
    )
    print(f"  -> Prediction Package Sealed! SHA-256: {lock_meta['package_sha256']}")
    print(f"  -> Locked Manifest: {lock_meta['locked_manifest_file']}")
    print(f"  -> Blinded Cases: {lock_meta['blinded_cases_file']}")
    print(f"  -> Blinded Template: {lock_meta['blinded_template_csv']}")
    
    # 6. Analysis & Reports Generation (AGENT-S3)
    print("\n[PHASE 6/7] Generating statistical analysis and 10 Markdown reports (AGENT-S3)...")
    analyze_and_report.write_all_reports(
        all_pairs=all_pairs,
        audit_results=audit_res,
        repro_results=repro_res,
        exec_results=exec_res,
        lock_meta=lock_meta,
        reports_dir=reports_dir,
        results_dir=results_dir,
    )
    print(f"  -> All 10 reports generated under: {reports_dir}")
    print(f"  -> Machine-readable manifests saved under: {results_dir}")
    
    t1 = time.time()
    print(f"\n[COMPLETE] Sprint finished successfully in {t1 - t0:.2f} seconds.")
    print("=" * 80)


if __name__ == "__main__":
    main()
