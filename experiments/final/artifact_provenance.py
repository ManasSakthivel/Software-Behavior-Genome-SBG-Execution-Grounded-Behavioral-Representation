#!/usr/bin/env python3
"""
experiments/final/artifact_provenance.py
========================================
Classifies every result artifact by how its numbers were obtained, and writes
``artifacts/final/ARTIFACT_PROVENANCE.json``.

Why
---
The repository carries 190 JSON result files across six research versions, and
nothing on disk distinguished a measured result from a reconstructed one. Two
concrete cases made that dangerous:

  artifacts/v5/INCREMENTAL_INFO_RESULTS.json carried ``"scores_are_real": true``
  next to its own note that "All other features use AUROC-consistent synthetic
  reconstruction". Only one of its ten features had real per-pair scores.
  results/phase2/REPRESENTATION_ABLATION.json then cited nine of its numbers as
  measured standalone AUROCs, and the README quoted one of those.

  artifacts/v5/REGRESSION_EVALUATION_RESULTS.json does not reproduce. Re-running
  its own generator gives volume_ratio 11/15 where the artifact says 7, and 4
  silent bugs where the artifact says 8, because one of its three features is a
  wall-clock time ratio.

Statuses
--------
MEASURED            every number came from executing the pipeline in this repo
PARTIALLY_SYNTHETIC some numbers are reconstructed from aggregates
SUPERSEDED          a later artifact corrects it; kept for the record
NON_REPRODUCING     re-running its own generator does not reproduce it
DERIVED             contains no primary measurement, only copies

``consistency_check.py`` fails if a document cites a non-MEASURED artifact as
the source of a headline number.

Usage:
    python3 experiments/final/artifact_provenance.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# Hand-classified because provenance is a claim about how a file was produced,
# which cannot be read off the file. Each entry states the evidence.
REGISTRY = {
    "artifacts/final/MAIN_EVALUATION_test_published.json": {
        "status": "MEASURED",
        "evidence": "produced by experiments/final/run_main_evaluation.py + "
                    "analyse_results.py in this repo; per-pair records committed "
                    "alongside it as pairs_test_published.jsonl",
        "authoritative_for": ["main benchmark AUROC under the published protocol"],
    },
    "artifacts/final/MAIN_EVALUATION_test_output_free_v6.json": {
        "status": "MEASURED",
        "evidence": "same pipeline under PROTOCOL output_free_v6",
        "authoritative_for": ["main benchmark AUROC under the output-free protocol"],
    },
    "artifacts/final/HARD_NEGATIVE_V5_RESULTS.json": {
        "status": "MEASURED",
        "evidence": "experiments/final/hard_negative_evaluation.py",
        "authoritative_for": ["hard-negative detection"],
    },
    "artifacts/final/REGRESSION_V5_RESULTS.json": {
        "status": "MEASURED",
        "evidence": "experiments/final/regression_evaluation.py",
        "authoritative_for": ["regression-corpus detection"],
    },
    "artifacts/final/BENCHMARK_VALIDITY_AUDIT.json": {
        "status": "MEASURED",
        "evidence": "benchmark/scripts/observability_audit.py; static, deterministic",
        "authoritative_for": ["benchmark validity counts"],
    },
    "artifacts/final/OUTPUT_ORACLE_LEAK_AUDIT.json": {
        "status": "MEASURED",
        "evidence": "experiments/final/output_oracle_leak_audit.py; static, deterministic",
        "authoritative_for": ["output-free constraint audit"],
    },
    "benchmark/benchmark_manifest.json": {
        "status": "MEASURED",
        "evidence": "benchmark/scripts/build_manifest.py, generated from the files",
        "authoritative_for": ["every program and pair count"],
    },
    "artifacts/v5/INCREMENTAL_INFO_RESULTS.json": {
        "status": "PARTIALLY_SYNTHETIC",
        "evidence": "its own reconstruction_note: only sbg_static has real per-pair "
                    "scores; the other nine features are reconstructed from aggregate "
                    "AUROCs by _reconstruct_scores_from_auroc(). The committed copy "
                    "carries scores_are_real=true, which the generator no longer emits.",
        "must_not_be_cited_as": "a measured standalone AUROC for any feature "
                                "other than sbg_static",
        "superseded_by": "artifacts/final/MAIN_EVALUATION_test_published.json",
    },
    "results/phase2/REPRESENTATION_ABLATION.json": {
        "status": "DERIVED",
        "evidence": "every row names artifacts/v5/INCREMENTAL_INFO_RESULTS.json as "
                    "its source, so it inherits that file's synthetic reconstruction",
        "superseded_by": "artifacts/final/MAIN_EVALUATION_test_published.json",
    },
    "artifacts/v5/REGRESSION_EVALUATION_RESULTS.json": {
        "status": "NON_REPRODUCING",
        "evidence": "re-running experiments/v5/regression_evaluator.py on this machine "
                    "gives volume_ratio_only 11/15 (artifact: 7) and 4 silent bugs "
                    "(artifact: 8). Its volume feature is a wall-clock ratio, so the "
                    "silent-bug partition it derives is timing dependent. Its SBG "
                    "column is a three-statistic proxy, not the V5 representation.",
        "superseded_by": "artifacts/final/REGRESSION_V5_RESULTS.json",
    },
    "artifacts/v4/FEATURE_ABLATION.json": {
        "status": "MEASURED",
        "evidence": "643 evaluated pairs with bootstrap CIs; its only_exception row "
                    "(0.592947) is the V3 exception COMPONENT (0.5*Jaccard of "
                    "exception types + 0.5*|delta rate|) with the other seven weights "
                    "zeroed -- not the single exception_fraction feature",
        "authoritative_for": ["V4 feature ablation"],
        "caveat": "the README quoted 0.593 as '`exception_fraction` alone -- a single "
                  "feature counting how often the program throws an exception'. That "
                  "describes artifacts/v4/SHORTCUT_CONTROLS.json's 0.567, a different "
                  "predictor. The two values were never in conflict; the label was.",
    },
    "artifacts/v4/SHORTCUT_CONTROLS.json": {
        "status": "MEASURED",
        "evidence": "643 evaluated pairs, 101 recorded missing; exc_frac = 0.567 "
                    "[0.522, 0.616] is the pure exception-fraction shortcut",
        "authoritative_for": ["exception_fraction shortcut AUROC (published protocol)"],
    },
    "artifacts/v5/B07/results_test.json": {
        "status": "SUPERSEDED",
        "evidence": "AUROC 0.551246 over 643 pairs is reproduced here, but its "
                    "methodology block claims 'bootstrap: cluster_by_base_program' "
                    "while baselines/v5/b07_dynamic_v5.py calls bootstrap_auroc_ci "
                    "without pair_ids, which takes the pair-level branch. The "
                    "published interval is therefore narrower than a clustered one.",
        "superseded_by": "artifacts/final/MAIN_EVALUATION_test_published.json",
    },
}


def main() -> int:
    rows = {}
    for relative, entry in sorted(REGISTRY.items()):
        path = REPO_ROOT / relative
        record = dict(entry)
        record["exists"] = path.exists()
        if path.exists():
            record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            record["bytes"] = path.stat().st_size
        rows[relative] = record

    counts: dict = {}
    for record in rows.values():
        counts[record["status"]] = counts.get(record["status"], 0) + 1

    payload = {
        "registry": "ARTIFACT_PROVENANCE",
        "statuses": {
            "MEASURED": "every number came from executing this repository's pipeline",
            "PARTIALLY_SYNTHETIC": "some numbers are reconstructed from aggregates",
            "SUPERSEDED": "a later artifact corrects it; kept for the record",
            "NON_REPRODUCING": "re-running its own generator does not reproduce it",
            "DERIVED": "contains no primary measurement, only copies",
        },
        "rule": ("A headline number may only cite an artifact whose status is "
                 "MEASURED. experiments/final/consistency_check.py enforces this."),
        "counts": counts,
        "artifacts": rows,
    }
    out = REPO_ROOT / "artifacts" / "final" / "ARTIFACT_PROVENANCE.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")

    for relative, record in rows.items():
        flag = "" if record["exists"] else "  (MISSING)"
        print(f"  {record['status']:20s} {relative}{flag}")
    print(f"\ncounts: {counts}")
    print(f"wrote {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
