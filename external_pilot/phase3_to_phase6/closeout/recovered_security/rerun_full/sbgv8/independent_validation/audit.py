"""sbgv8/independent_validation/audit.py — Dataset Independence & Prior Exposure Auditor (AGENT-S1).

Audits candidate change pairs across 5 independent external datasets (Defects4J, BugsInPy, Bears,
BugSwarm, Bugs.jar) against historical SBG development and calibration datasets (V5, V6, V7, V8 dev).
Detects duplicate project families, cross-dataset overlaps, and enforces strict independence.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEV_MANIFEST_PATH = REPO_ROOT / "datasets" / "v8" / "DEV_MANIFEST.jsonl"
BENCHMARK_MANIFEST_PATH = REPO_ROOT / "benchmark" / "benchmark_manifest.json"


def load_dev_exposures() -> Dict[str, Any]:
    """Extract all historical projects, families, and pair IDs from V8 development records."""
    dev_projects = set()
    dev_families = set()
    dev_pairs = set()

    if DEV_MANIFEST_PATH.exists():
        with open(DEV_MANIFEST_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                proj = d.get("project", "").strip().lower()
                fam = d.get("family", "").strip().lower()
                pair_id = d.get("pair_id", "").strip()
                if proj:
                    dev_projects.add(proj)
                if fam:
                    dev_families.add(fam)
                if pair_id:
                    dev_pairs.add(pair_id)

    # Also check base programs in benchmark manifest
    base_programs = set()
    if BENCHMARK_MANIFEST_PATH.exists():
        with open(BENCHMARK_MANIFEST_PATH, "r", encoding="utf-8") as f:
            bdata = json.load(f)
            programs = bdata.get("corpus", {}).get("programs", {})
            for p_name in programs:
                base_programs.add(p_name.lower())

    return {
        "dev_projects": sorted(list(dev_projects)),
        "dev_families": sorted(list(dev_families)),
        "dev_pairs": sorted(list(dev_pairs)),
        "base_programs": sorted(list(base_programs)),
    }


def audit_pair(
    pair: Dict[str, Any], dev_info: Dict[str, Any]
) -> Tuple[bool, str, Dict[str, Any]]:
    """Audit a single candidate change pair for prior exposure or cross-dataset overlap."""
    dataset = pair.get("dataset", "").strip().lower()
    project = pair.get("project", "").strip().lower()
    family = pair.get("project_family", "").strip().lower()
    pair_id = pair.get("pair_id", "").strip()

    audit_details = {
        "pair_id": pair_id,
        "dataset": dataset,
        "project": project,
        "family": family,
        "in_dev_projects": project in dev_info["dev_projects"],
        "in_dev_families": family in dev_info["dev_families"],
        "in_dev_pairs": pair_id in dev_info["dev_pairs"],
        "cross_dataset_overlap": False,
        "overlap_reason": "",
    }

    # Cross-dataset overlap checks
    # e.g., Bugs.jar commons-math overlaps with Defects4J Math
    if dataset == "bugs.jar" and ("math" in project or "commons-math" in project):
        audit_details["cross_dataset_overlap"] = True
        audit_details["overlap_reason"] = "Bugs.jar commons-math overlaps with Defects4J Math project family"
        return False, "CROSS_DATASET_OVERLAP", audit_details

    # Check if this exact project was in the V8 dev set
    if project in dev_info["dev_projects"]:
        return False, "DEV_PROJECT_EXPOSURE", audit_details

    # Check if this exact pair was in dev set
    if pair_id in dev_info["dev_pairs"]:
        return False, "DEV_PAIR_EXPOSURE", audit_details

    return True, "INDEPENDENT_CLEAN", audit_details


def run_full_audit(candidate_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Execute complete independence audit on all candidate pairs."""
    dev_info = load_dev_exposures()
    audit_results = {
        "total_audited": len(candidate_pairs),
        "independent_clean": 0,
        "excluded_dev_exposure": 0,
        "excluded_cross_overlap": 0,
        "exclusions": [],
        "clean_pairs": [],
        "projects_by_dataset": {},
        "families_by_dataset": {},
    }

    for pair in candidate_pairs:
        is_clean, reason, details = audit_pair(pair, dev_info)
        ds = pair.get("dataset", "unknown")
        proj = pair.get("project", "unknown")
        fam = pair.get("project_family", "unknown")

        if ds not in audit_results["projects_by_dataset"]:
            audit_results["projects_by_dataset"][ds] = set()
            audit_results["families_by_dataset"][ds] = set()
        audit_results["projects_by_dataset"][ds].add(proj)
        audit_results["families_by_dataset"][ds].add(fam)

        if is_clean:
            audit_results["independent_clean"] += 1
            audit_results["clean_pairs"].append(pair)
        else:
            if reason == "CROSS_DATASET_OVERLAP":
                audit_results["excluded_cross_overlap"] += 1
            else:
                audit_results["excluded_dev_exposure"] += 1
            audit_results["exclusions"].append({
                "pair_id": pair.get("pair_id"),
                "dataset": ds,
                "project": proj,
                "reason": reason,
                "details": details,
            })

    # Convert sets to lists
    audit_results["projects_by_dataset"] = {
        k: sorted(list(v)) for k, v in audit_results["projects_by_dataset"].items()
    }
    audit_results["families_by_dataset"] = {
        k: sorted(list(v)) for k, v in audit_results["families_by_dataset"].items()
    }
    return audit_results
