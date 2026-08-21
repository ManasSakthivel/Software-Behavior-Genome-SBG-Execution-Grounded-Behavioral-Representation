"""
Agent 1F — Dataset Diversity Audit
====================================
Measures diversity of the SBG benchmark corpus against the criteria in
docs/research/BENCHMARK_DESIGN.md §1.3.

Outputs: benchmark/scripts/diversity_report.json

Metrics computed
----------------
a. Category entropy (Shannon, base-2 bits) over 12 categories.
b. Complexity distribution (LOW / MEDIUM / HIGH counts).
c. Size distribution histogram (line counts, 50-line bins).
d. SP transformation-type coverage — which of the 12 SP types are
   applicable to ≥2 programs (proxy: dimensions_affected per SP type
   mapped to program category affinity).
e. SC mutation-type coverage — which of the 14 SC types apply to ≥2
   programs (proxy: ast_targets mapped to program structural features).
f. Behavioral genome dimension coverage — which of the 8 dimensions
   (CONTROL, DATA, STATE, RESOURCE, TEMPORAL, ERROR, INTERACTION,
   EXECUTION) each program category exercises, based on the SP
   transformation dimension annotations and category semantics.
"""

from __future__ import annotations

import json
import math
import os
import statistics
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "benchmark" / "corpus" / "programs_manifest.json"
SP_MANIFEST_PATH = (
    REPO_ROOT
    / "benchmark"
    / "transformations"
    / "preserving"
    / "manifest.json"
)
SC_MANIFEST_PATH = (
    REPO_ROOT
    / "benchmark"
    / "transformations"
    / "mutations"
    / "manifest.json"
)
OUTPUT_PATH = Path(__file__).resolve().parent / "diversity_report.json"

# ---------------------------------------------------------------------------
# Genome dimensions
# ---------------------------------------------------------------------------
ALL_DIMENSIONS = ["CONTROL", "DATA", "STATE", "RESOURCE", "TEMPORAL",
                  "ERROR", "INTERACTION", "EXECUTION"]

# ---------------------------------------------------------------------------
# Category → genome dimensions exercised
# Derived from FORMAL_MODEL.md Definitions 9-17 and BENCHMARK_DESIGN.md §1.1
# ---------------------------------------------------------------------------
CATEGORY_DIMENSIONS: dict[str, list[str]] = {
    "Sorting/Searching Algorithms": ["CONTROL", "DATA", "EXECUTION"],
    "Graph Algorithms":             ["CONTROL", "DATA", "STATE", "EXECUTION"],
    "Data Structures":              ["STATE", "CONTROL", "DATA", "RESOURCE"],
    "String/Text Processing":       ["DATA", "CONTROL", "EXECUTION"],
    "Mathematical/Numerical":       ["DATA", "CONTROL", "EXECUTION"],
    "State Machines":               ["STATE", "CONTROL", "TEMPORAL"],
    "File/Stream Processing":       ["INTERACTION", "RESOURCE", "DATA"],
    "API/HTTP Simulation":          ["INTERACTION", "CONTROL", "ERROR", "TEMPORAL"],
    "Resource Management":          ["RESOURCE", "STATE", "TEMPORAL", "ERROR"],
    "Error Handling":               ["ERROR", "CONTROL", "EXECUTION"],
    "Concurrency Simulation":       ["TEMPORAL", "STATE", "CONTROL", "EXECUTION"],
    "Parser Implementations":       ["CONTROL", "DATA", "ERROR"],
}

# ---------------------------------------------------------------------------
# SP type → program categories where it is structurally applicable
# Based on SP manifest dimensions_affected + transformation description
# ---------------------------------------------------------------------------
SP_CATEGORY_APPLICABILITY: dict[str, list[str]] = {
    "SP-1":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Data Structures",
              "String/Text Processing", "Mathematical/Numerical", "State Machines",
              "File/Stream Processing", "API/HTTP Simulation", "Resource Management",
              "Error Handling", "Concurrency Simulation", "Parser Implementations"],
    "SP-2":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Data Structures",
              "String/Text Processing", "Mathematical/Numerical", "State Machines",
              "File/Stream Processing", "API/HTTP Simulation", "Resource Management",
              "Error Handling", "Concurrency Simulation", "Parser Implementations"],
    "SP-3":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Data Structures",
              "String/Text Processing", "Mathematical/Numerical", "State Machines",
              "File/Stream Processing", "API/HTTP Simulation", "Resource Management",
              "Error Handling", "Concurrency Simulation", "Parser Implementations"],
    "SP-4":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Mathematical/Numerical",
              "Data Structures", "String/Text Processing"],
    "SP-5":  ["Sorting/Searching Algorithms", "Mathematical/Numerical",
              "String/Text Processing", "Graph Algorithms", "Data Structures",
              "Parser Implementations"],
    "SP-6":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Data Structures",
              "String/Text Processing", "Mathematical/Numerical", "State Machines",
              "API/HTTP Simulation", "Error Handling", "Parser Implementations"],
    "SP-7":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Data Structures",
              "Mathematical/Numerical", "File/Stream Processing", "API/HTTP Simulation",
              "Resource Management", "Parser Implementations"],
    "SP-8":  ["Data Structures", "Graph Algorithms", "Resource Management",
              "Concurrency Simulation", "File/Stream Processing"],
    "SP-9":  ["Data Structures", "Resource Management", "State Machines",
              "API/HTTP Simulation", "File/Stream Processing"],
    "SP-10": ["Sorting/Searching Algorithms", "Graph Algorithms", "Data Structures",
              "String/Text Processing", "Mathematical/Numerical", "State Machines",
              "File/Stream Processing", "API/HTTP Simulation", "Resource Management",
              "Error Handling", "Concurrency Simulation", "Parser Implementations"],
    "SP-11": ["Data Structures", "Graph Algorithms", "Resource Management",
              "Concurrency Simulation", "Parser Implementations"],
    "SP-12": ["Mathematical/Numerical", "Sorting/Searching Algorithms",
              "String/Text Processing", "Graph Algorithms", "Data Structures"],
}

# ---------------------------------------------------------------------------
# SC type → program categories where AST targets are likely to appear
# Based on SC manifest ast_targets
# ---------------------------------------------------------------------------
SC_CATEGORY_APPLICABILITY: dict[str, list[str]] = {
    "SC-1":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Data Structures",
              "Mathematical/Numerical", "String/Text Processing", "Parser Implementations"],
    "SC-2":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Mathematical/Numerical",
              "String/Text Processing", "Data Structures", "Parser Implementations"],
    "SC-3":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Mathematical/Numerical",
              "String/Text Processing", "State Machines", "Resource Management"],
    "SC-4":  ["Graph Algorithms", "Data Structures", "Error Handling", "API/HTTP Simulation",
              "Resource Management", "Parser Implementations"],
    "SC-5":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Data Structures",
              "String/Text Processing", "Mathematical/Numerical", "State Machines",
              "File/Stream Processing", "Error Handling", "Parser Implementations"],
    "SC-6":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Data Structures",
              "Mathematical/Numerical", "String/Text Processing", "Parser Implementations"],
    "SC-7":  ["Error Handling", "API/HTTP Simulation", "Resource Management",
              "File/Stream Processing", "Concurrency Simulation"],
    "SC-8":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Mathematical/Numerical",
              "Data Structures", "String/Text Processing"],
    "SC-9":  ["Sorting/Searching Algorithms", "Graph Algorithms", "Data Structures",
              "Mathematical/Numerical", "File/Stream Processing", "Parser Implementations"],
    "SC-10": ["Sorting/Searching Algorithms", "Graph Algorithms", "Mathematical/Numerical",
              "Data Structures", "String/Text Processing"],
    "SC-11": ["Sorting/Searching Algorithms", "Graph Algorithms", "Data Structures",
              "Mathematical/Numerical", "String/Text Processing", "Parser Implementations"],
    "SC-12": ["Resource Management", "File/Stream Processing", "API/HTTP Simulation",
              "Concurrency Simulation", "Error Handling"],
    "SC-13": ["Sorting/Searching Algorithms", "Graph Algorithms", "Data Structures",
              "Error Handling", "State Machines", "Parser Implementations"],
    "SC-14": ["State Machines", "API/HTTP Simulation", "Resource Management",
              "Error Handling", "Concurrency Simulation"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def shannon_entropy(counts: list[int]) -> float:
    """Shannon entropy in bits for a count vector."""
    total = sum(counts)
    if total == 0:
        return 0.0
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log2(p)
    return entropy


def histogram(values: list[float], bin_size: int = 50) -> dict[str, int]:
    """Build a histogram with fixed-width bins; keys are range strings."""
    if not values:
        return {}
    min_v = int(min(values))
    max_v = int(max(values))
    low = (min_v // bin_size) * bin_size
    buckets: dict[str, int] = {}
    v = low
    while v <= max_v:
        key = f"{v}-{v + bin_size - 1}"
        buckets[key] = 0
        v += bin_size
    for val in values:
        bucket_start = (int(val) // bin_size) * bin_size
        key = f"{bucket_start}-{bucket_start + bin_size - 1}"
        buckets[key] = buckets.get(key, 0) + 1
    return buckets


def count_applicable_programs(
    applicability_map: dict[str, list[str]],
    programs: list[dict[str, Any]],
) -> dict[str, int]:
    """For each transformation type, count how many programs it applies to."""
    result: dict[str, int] = {}
    for t_id, categories in applicability_map.items():
        cat_set = set(categories)
        count = sum(1 for p in programs if p["category"] in cat_set)
        result[t_id] = count
    return result


def dimension_coverage(
    programs: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """
    Return for each genome dimension the list of program_ids that exercise it,
    based on their category's dimension mapping.
    """
    dim_to_programs: dict[str, list[str]] = {d: [] for d in ALL_DIMENSIONS}
    for prog in programs:
        dims = CATEGORY_DIMENSIONS.get(prog["category"], [])
        for dim in dims:
            dim_to_programs[dim].append(prog["program_id"])
    return dim_to_programs


# ---------------------------------------------------------------------------
# Main audit logic
# ---------------------------------------------------------------------------

def run_audit() -> dict[str, Any]:
    with open(MANIFEST_PATH) as f:
        manifest: dict[str, Any] = json.load(f)

    with open(SP_MANIFEST_PATH) as f:
        sp_manifest: dict[str, Any] = json.load(f)

    with open(SC_MANIFEST_PATH) as f:
        sc_manifest: dict[str, Any] = json.load(f)

    programs: list[dict[str, Any]] = manifest["programs"]
    total = len(programs)

    # ------------------------------------------------------------------ a
    # Category distribution and entropy
    cat_dist: dict[str, int] = {}
    for prog in programs:
        cat = prog["category"]
        cat_dist[cat] = cat_dist.get(cat, 0) + 1

    category_entropy = shannon_entropy(list(cat_dist.values()))

    # ------------------------------------------------------------------ b
    # Complexity distribution
    complexity_dist: dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for prog in programs:
        c = prog.get("complexity", "UNKNOWN")
        if c in complexity_dist:
            complexity_dist[c] += 1
        else:
            complexity_dist[c] = complexity_dist.get(c, 0) + 1

    # ------------------------------------------------------------------ c
    # Size distribution
    lines_list = [prog["lines"] for prog in programs]
    size_stats = {
        "min": int(min(lines_list)),
        "max": int(max(lines_list)),
        "mean": round(statistics.mean(lines_list), 2),
        "median": float(statistics.median(lines_list)),
        "histogram_50line_bins": histogram(lines_list, bin_size=50),
    }

    # ------------------------------------------------------------------ d
    # SP transformation coverage
    sp_applicable = count_applicable_programs(SP_CATEGORY_APPLICABILITY, programs)
    sp_coverage_issues: list[str] = []
    sp_coverage_summary: dict[str, Any] = {}
    for sp_id, cnt in sp_applicable.items():
        sp_coverage_summary[sp_id] = cnt
        if cnt < 2:
            sp_coverage_issues.append(
                f"{sp_id}: only {cnt} program(s) applicable (need ≥2)"
            )

    # ------------------------------------------------------------------ e
    # SC mutation coverage
    sc_applicable = count_applicable_programs(SC_CATEGORY_APPLICABILITY, programs)
    sc_coverage_issues: list[str] = []
    sc_coverage_summary: dict[str, Any] = {}
    for sc_id, cnt in sc_applicable.items():
        sc_coverage_summary[sc_id] = cnt
        if cnt < 2:
            sc_coverage_issues.append(
                f"{sc_id}: only {cnt} program(s) applicable (need ≥2)"
            )

    # ------------------------------------------------------------------ f
    # Behavioral genome dimension coverage
    dim_coverage = dimension_coverage(programs)
    dim_coverage_counts = {d: len(ids) for d, ids in dim_coverage.items()}
    uncovered_dims = [d for d, cnt in dim_coverage_counts.items() if cnt == 0]

    # ------------------------------------------------------------------ issues
    issues: list[str] = []

    if category_entropy < 2.5:
        issues.append(
            f"Category entropy {category_entropy:.3f} bits < 2.5 bit threshold"
        )

    # Check minimum corpus size vs BENCHMARK_DESIGN requirement
    if total < 60:
        issues.append(f"Total programs {total} < 60 minimum")

    # Check size diversity: need at least SMALL (<100), MEDIUM (100-500) programs
    small_count = sum(1 for l in lines_list if l < 100)
    medium_count = sum(1 for l in lines_list if 100 <= l < 500)
    large_count = sum(1 for l in lines_list if l >= 500)
    if small_count == 0:
        issues.append("No small programs (< 100 LOC) — scale diversity gap")
    if medium_count == 0:
        issues.append("No medium programs (100–499 LOC) — scale diversity gap")

    # Complexity balance: HIGH-only corpus is a concern
    if complexity_dist.get("LOW", 0) == 0 and complexity_dist.get("MEDIUM", 0) == 0:
        issues.append("All programs are HIGH complexity — no LOW/MEDIUM programs present")
    elif complexity_dist.get("LOW", 0) == 0:
        issues.append(
            "No LOW-complexity programs — BENCHMARK_DESIGN §1.3 requires scale diversity"
        )

    issues.extend(sp_coverage_issues)
    issues.extend(sc_coverage_issues)

    if uncovered_dims:
        issues.append(
            f"Genome dimensions with zero program coverage: {uncovered_dims}"
        )

    # ------------------------------------------------------------------ diversity_score
    # Composite 0–1 score:
    #   20% entropy component (capped at 3.58 bits = log2(12))
    #   20% complexity balance (equal thirds ideal)
    #   20% size diversity (presence of both small and medium)
    #   20% SP all-types covered (≥2 programs each)
    #   20% SC all-types covered (≥2 programs each)

    max_entropy = math.log2(12)  # 12 categories
    entropy_score = min(category_entropy / max_entropy, 1.0)

    # Complexity balance: ideal = [1/3, 1/3, 1/3]; penalise deviation
    fracs = [complexity_dist.get(k, 0) / total for k in ["LOW", "MEDIUM", "HIGH"]]
    ideal = 1.0 / 3.0
    deviation = sum(abs(f - ideal) for f in fracs) / 2.0  # max deviation = 1
    complexity_score = 1.0 - deviation

    size_score = (
        (1.0 if small_count > 0 else 0.0)
        + (1.0 if medium_count > 0 else 0.0)
        + (1.0 if large_count > 0 else 0.0)
    ) / 3.0

    sp_types_ok = sum(1 for cnt in sp_applicable.values() if cnt >= 2)
    sp_score = sp_types_ok / 12.0

    sc_types_ok = sum(1 for cnt in sc_applicable.values() if cnt >= 2)
    sc_score = sc_types_ok / 14.0

    diversity_score = round(
        0.20 * entropy_score
        + 0.20 * complexity_score
        + 0.20 * size_score
        + 0.20 * sp_score
        + 0.20 * sc_score,
        4,
    )

    # ------------------------------------------------------------------ verdict
    critical_issues = [
        iss for iss in issues
        if "entropy" in iss or "Total programs" in iss or "scale diversity" in iss.lower()
    ]
    if diversity_score >= 0.70 and not critical_issues:
        verdict = "PASS"
    elif diversity_score >= 0.50:
        verdict = "CONDITIONAL"
    else:
        verdict = "FAIL"

    return {
        "total_programs": total,
        "category_entropy": round(category_entropy, 4),
        "category_entropy_threshold": 2.5,
        "category_distribution": cat_dist,
        "complexity_distribution": complexity_dist,
        "size_stats": size_stats,
        "sp_transformation_coverage": sp_coverage_summary,
        "sc_mutation_coverage": sc_coverage_summary,
        "genome_dimension_coverage": {
            "counts_by_dimension": dim_coverage_counts,
            "programs_by_dimension": {
                d: ids for d, ids in dim_coverage.items()
            },
        },
        "diversity_score_components": {
            "entropy_score": round(entropy_score, 4),
            "complexity_balance_score": round(complexity_score, 4),
            "size_diversity_score": round(size_score, 4),
            "sp_type_coverage_score": round(sp_score, 4),
            "sc_type_coverage_score": round(sc_score, 4),
        },
        "diversity_score": diversity_score,
        "diversity_verdict": verdict,
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    report = run_audit()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Diversity report written to {OUTPUT_PATH}")
    print(f"  total_programs  : {report['total_programs']}")
    print(f"  category_entropy: {report['category_entropy']} bits "
          f"(threshold: {report['category_entropy_threshold']})")
    print(f"  complexity      : {report['complexity_distribution']}")
    print(f"  diversity_score : {report['diversity_score']}")
    print(f"  verdict         : {report['diversity_verdict']}")
    if report["issues"]:
        print("  issues:")
        for iss in report["issues"]:
            print(f"    - {iss}")
    else:
        print("  issues: none")
