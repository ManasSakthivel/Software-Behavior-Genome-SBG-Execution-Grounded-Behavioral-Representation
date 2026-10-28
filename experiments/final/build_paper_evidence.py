"""Builds artifacts/paper_evidence/*.json|csv from the committed source artifacts.

Every number written is read from (or recomputed from) a file whose path and
SHA-256 are recorded next to it. Nothing here scores the v6/v8 TEST splits and
the script refuses to read any pair file whose rows carry split == "test" for
the freshly computed comparisons.

    python3 experiments/final/build_paper_evidence.py
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import pathlib
import platform
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from experiments.final.edit_size_analysis import _edit_size                      # noqa: E402
from experiments.final.fit_weights import MODELS, score as lin_score            # noqa: E402
from sbg.statistics import (                                                     # noqa: E402
    auroc, cluster_bootstrap_ci, paired_cluster_bootstrap_delta)

ART = REPO / "artifacts" / "final"
OUT = REPO / "artifacts" / "paper_evidence"
OUT.mkdir(parents=True, exist_ok=True)


def sha(path) -> str:
    return hashlib.sha256((REPO / path).read_bytes()).hexdigest()


def rel(path) -> str:
    return str(pathlib.Path(path).relative_to(REPO)) if pathlib.Path(path).is_absolute() else str(path)


def jl(path):
    return [json.loads(l) for l in (REPO / path).read_text().splitlines() if l.strip()]


def js(path):
    return json.loads((REPO / path).read_text())


def src(path) -> dict:
    return {"path": str(path), "sha256": sha(path)}


def write(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2) + "\n")


def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True).stdout.strip()


# ---------------------------------------------------------------- datasets
DATASETS = {"v6": "benchmark/datasets/v6", "v8": "benchmark/datasets/v8"}
SPLITS = ("train", "dev", "val", "test")


def dataset_summary():
    out = {}
    for name, d in DATASETS.items():
        splits, all_bases, all_ids, missing = {}, {}, set(), 0
        for sp in SPLITS:
            rows = jl(f"{d}/pairs_{sp}.jsonl")
            ids = [r["pair_id"] for r in rows]
            bases = {r["base_id"] for r in rows}
            for r in rows:
                for k in ("base_path", "variant_path"):
                    if not (REPO / r[k]).exists():
                        missing += 1
            rel_counts = {}
            for r in rows:
                rel_counts[r["semantic_relation"]] = rel_counts.get(r["semantic_relation"], 0) + 1
            splits[sp] = {
                "n_pairs": len(rows), "n_unique_pair_ids": len(set(ids)),
                "n_programs": len(bases), "n_changed": sum(1 for r in rows if r["semantic_relation"] != "EQUIVALENT"),
                "n_equivalent": sum(1 for r in rows if r["semantic_relation"] == "EQUIVALENT"),
                "semantic_relation_counts": rel_counts,
                "transformation_types": sorted({r["transformation_type"] for r in rows}),
                "pair_file": src(f"{d}/pairs_{sp}.jsonl"),
            }
            all_bases[sp] = bases
            all_ids |= set(ids)
        overlaps = {f"{a}&{b}": sorted(all_bases[a] & all_bases[b])
                    for a, b in itertools.combinations(SPLITS, 2) if all_bases[a] & all_bases[b]}
        out[name] = {
            "dataset_dir": d, "splits": splits,
            "total_pairs": sum(s["n_pairs"] for s in splits.values()),
            "total_programs": len(set().union(*all_bases.values())),
            "program_overlap_between_splits": overlaps,
            "program_disjointness_check": "PASS" if not overlaps else "FAIL",
            "pair_id_global_uniqueness_check": "PASS" if len(all_ids) == sum(
                s["n_pairs"] for s in splits.values()) else "FAIL",
            "missing_referenced_files": missing,
            "_bases": {k: sorted(v) for k, v in all_bases.items()},
        }
    v6b = set().union(*[set(x) for x in out["v6"]["_bases"].values()])
    v8b = set().union(*[set(x) for x in out["v8"]["_bases"].values()])
    cross = sorted(v6b & v8b)
    for v in out.values():
        del v["_bases"]
    return out, cross


# ------------------------------------------------------------- scored runs
RUNS = {
    "v6train_v7": dict(pairs="artifacts/final/pairs_v6train_output_free_v7.jsonl",
                       programs="artifacts/final/programs_v6train_output_free_v7.json",
                       main="artifacts/final/MAIN_EVALUATION_v6train_output_free_v7.json",
                       audit="artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json",
                       dataset="v6", split="train", protocol="output_free_v7",
                       role="weight-fitting TRAIN split (in-sample for learned weights)",
                       status="complete"),
    "v6dev_v7": dict(pairs="artifacts/final/pairs_v6dev_output_free_v7.jsonl",
                     programs="artifacts/final/programs_v6dev_output_free_v7.json",
                     main="artifacts/final/MAIN_EVALUATION_v6dev_output_free_v7.json",
                     audit="artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json",
                     dataset="v6", split="dev", protocol="output_free_v7",
                     role="DEV split: tau* derived here, weight model selected here",
                     status="complete (frozen 2026-09-28; not byte-reproducible under current code, see DATA_VALIDATION.md)"),
    "v8dev_v8_rescore": dict(pairs="artifacts/final/pairs_v8devrescore_output_free_v8.jsonl",
                             programs="artifacts/final/programs_v8devrescore_output_free_v8.json",
                             main="artifacts/final/MAIN_EVALUATION_v8devrescore_output_free_v8.json",
                             audit="artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7ENTRY_ON_V8.json",
                             dataset="v8", split="dev", protocol="output_free_v8",
                             role="fresh-program DEV split of the CURRENT v8 dataset, re-scored 2026-10-28 (not used for tau*/weights)",
                             status="complete; exploratory (v8 TEST not evaluated)"),
    "v6test_v6": dict(pairs="artifacts/final/pairs_v6test_output_free_v6.jsonl",
                      programs="artifacts/final/programs_v6test_output_free_v6.json",
                      main="artifacts/final/MAIN_EVALUATION_v6test_output_free_v6.json",
                      audit="artifacts/final/BENCHMARK_VALIDITY_AUDIT_V6.json",
                      dataset="v6", split="test", protocol="output_free_v6",
                      role="OBSERVED (not held-out) v6 test, historical protocol v6, committed before this session",
                      status="historical; exploratory; NOT rerun"),
}


def run_table(label, r):
    rows = jl(r["pairs"])
    prog = js(r["programs"])
    ev = [x for x in rows if x["evaluated"]]
    return {
        "dataset": r["dataset"], "split": r["split"], "protocol": r["protocol"],
        "role": r["role"], "status": r["status"],
        "n_pairs_scored_rows": len(rows), "n_evaluated": len(ev),
        "n_changed_evaluated": sum(x["label"] for x in ev),
        "n_equivalent_evaluated": sum(1 - x["label"] for x in ev),
        "n_programs_in_pairs": len({x["base_id"] for x in rows}),
        "n_programs_evaluated": len({x["base_id"] for x in ev}),
        "failure_ledger": {k: v for k, v in sorted(
            __import__("collections").Counter(
                f"{x.get('failure_side')}:{x.get('failure_kind')}" for x in rows if not x["evaluated"]).items())},
        "programs_file_n_programs_incl_variants": prog["n_programs"],
        "programs_file_n_ok": prog["n_ok"], "wall_time_s_recorded": prog.get("wall_time_s"),
        "sources": {"pairs": src(r["pairs"]), "programs": src(r["programs"]),
                    "main_evaluation": src(r["main"]), "validity_audit": src(r["audit"])},
    }


# --------------------------------------------------- recomputed comparisons
W = js("artifacts/final/WEIGHT_FITTING.json")


def valid_rows(run):
    r = RUNS[run]
    audit = {x["pair_id"]: x for x in js(r["audit"])["pairs"]}
    out = []
    for x in jl(r["pairs"]):
        v = audit.get(x["pair_id"])
        if not x["evaluated"] or v is None or v.get("status") != "ok":
            continue
        if x["label"] == 1 and v.get("observable") is not True:
            continue
        out.append(x)
    return out


def recompute(run):
    r = RUNS[run]
    assert r["split"] != "test"
    meta = {}
    for sp in ("train", "dev", "val"):
        for m in jl(f"{DATASETS[r['dataset']]}/pairs_{sp}.jsonl"):
            meta[m["pair_id"]] = m
    rows = valid_rows(run)
    y = [x["label"] for x in rows]
    cl = [x["base_id"] for x in rows]
    pred = {
        "sbg_v5": [x["scores"]["sbg_v5"] for x in rows],
        "edit_size_reversed": [-float(_edit_size(meta[x["pair_id"]]["base_path"],
                                                 meta[x["pair_id"]]["variant_path"])) for x in rows],
        "exception_fraction": [x["scores"]["exception_fraction"] for x in rows],
        "call_count": [x["scores"]["call_count"] for x in rows],
        "static_ast": [x["scores"]["static_ast"] for x in rows],
    }
    for name, feats in MODELS.items():
        pred[f"learned_{name.lower()}"] = [lin_score(W["models"][name], feats, x["scores"]) for x in rows]
    table = {}
    for p, s in pred.items():
        lo, hi, n = cluster_bootstrap_ci(s, y, cl, n_bootstrap=2000, seed=42)
        table[p] = {"auroc": round(auroc(s, y), 6), "ci95_lo": lo, "ci95_hi": hi, "n_boot": n}
    deltas = {}
    for other in ("edit_size_reversed", "exception_fraction", "call_count", "learned_m1", "learned_m2"):
        d = paired_cluster_bootstrap_delta(pred["sbg_v5"], pred[other], y, cl, n_bootstrap=2000, seed=42)
        deltas[f"sbg_v5_minus_{other}"] = d
    for other in ("edit_size_reversed", "exception_fraction", "call_count"):
        d = paired_cluster_bootstrap_delta(pred["learned_m2"], pred[other], y, cl, n_bootstrap=2000, seed=42)
        deltas[f"learned_m2_minus_{other}"] = d
    return {"set": "VALID", "n": len(rows), "n_programs": len(set(cl)),
            "n_changed": sum(y), "n_equivalent": len(y) - sum(y),
            "predictors": table, "paired_deltas": deltas,
            "learned_weights_note": ("learned_m1/m2 use weights fitted on v6 TRAIN (WEIGHT_FITTING.json); "
                                     "in-sample on v6train, selection set on v6dev, out-of-distribution on v8dev"),
            "method": "sbg.statistics cluster bootstrap (2000, seed 42) by base program; paired deltas via paired_cluster_bootstrap_delta",
            "code": "experiments/final/build_paper_evidence.py"}


def main():
    ds, cross = dataset_summary()
    runs = {k: run_table(k, v) for k, v in RUNS.items()}
    external = {
        "quixbugs_output_free_v7": {**{k: js("artifacts/final/QUIXBUGS_output_free_v7.json")["headline"][k]
                                      for k in ("pairs_total", "pairs_evaluated", "n_changed", "n_equivalent", "sbg_v5_auroc")},
                                    "ci95": None, "note": "CI not computed in source artifact; produced pre-freeze; BELOW CHANCE",
                                    "source": src("artifacts/final/QUIXBUGS_output_free_v7.json")},
        "bugsinpy_output_free_v7": {**js("artifacts/final/BUGSINPY_output_free_v7.json")["headline"],
                                    "source": src("artifacts/final/BUGSINPY_output_free_v7.json")},
    }
    # zero-test-touch checks
    forbidden = [p for p in ("artifacts/final/pairs_v6test_output_free_v7.jsonl",
                             "artifacts/final/MAIN_EVALUATION_v6test_output_free_v7.json",
                             "artifacts/final/programs_v6test_output_free_v7.json",
                             "artifacts/final/pairs_v8test_output_free_v8.jsonl",
                             "artifacts/final/THRESHOLD_V8_FROZEN.json", "artifacts/final/FREEZE_V8.json")
                 if (REPO / p).exists()]
    leak = {r: sum(1 for x in jl(RUNS[r]["pairs"]) if any(k.startswith("learned_") for k in x.get("scores", {})))
            for r in RUNS}
    recomputed = {k: recompute(k) for k in ("v6train_v7", "v6dev_v7", "v8dev_v8_rescore")}
    write("raw/recomputed_comparisons.json", recomputed)

    # ---------------------------------------------------------- CSV
    rows_csv = []

    def add(run, set_name, pred, au, lo, hi, n, ncl, src_path, note=""):
        r = RUNS.get(run, {})
        rows_csv.append([run, r.get("dataset", ""), r.get("split", ""), r.get("protocol", ""), set_name,
                         pred, au, lo, hi, n, ncl, r.get("status", ""), src_path, note])

    for run in ("v6train_v7", "v6dev_v7", "v8dev_v8_rescore", "v6test_v6"):
        m = js(RUNS[run]["main"])
        for pred, st in m["results"]["VALID"]["predictors"].items():
            if st.get("auroc") is None:
                continue
            ci = st["ci95_cluster_bootstrap"]
            add(run, "VALID", pred, st["auroc"], ci[0], ci[1], st["n"], "", RUNS[run]["main"], "precomputed by analyse_results.py")
    for run, rc in recomputed.items():
        for pred in ("edit_size_reversed", "learned_m1", "learned_m2"):
            st = rc["predictors"][pred]
            add(run, "VALID", pred, st["auroc"], st["ci95_lo"], st["ci95_hi"], rc["n"], rc["n_programs"],
                "artifacts/paper_evidence/raw/recomputed_comparisons.json",
                "recomputed by build_paper_evidence.py" + ("; weights from v6 TRAIN" if pred.startswith("learned") else ""))
    b = js("artifacts/final/BUGSINPY_output_free_v7.json")["sets"]["VALID"]
    for pred, st in b["predictors"].items():
        add("bugsinpy_v7", "VALID", pred, st["auroc"], st["ci_lower"], st["ci_upper"], st["n_pairs"], st["n_clusters"],
            "artifacts/final/BUGSINPY_output_free_v7.json", "external; pre-freeze; dataset=BugsInPy@11c5f1e")
    q = external["quixbugs_output_free_v7"]
    add("quixbugs_v7", "ALL", "sbg_v5", q["sbg_v5_auroc"], "", "", q["pairs_evaluated"], "",
        "artifacts/final/QUIXBUGS_output_free_v7.json", "external; pre-freeze; no CI in source")
    with open(OUT / "BASELINE_COMPARISON.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "dataset", "split", "protocol", "eval_set", "predictor", "auroc", "ci95_lo", "ci95_hi",
                    "n_pairs", "n_programs", "run_status", "source_artifact", "note"])
        w.writerows(rows_csv)

    # --------------------------------------------------------- JSONs
    write("DATASET_SUMMARY.json", {
        "generated_by": "experiments/final/build_paper_evidence.py",
        "datasets": ds,
        "v6_v8_program_overlap": cross, "v6_v8_program_disjointness_check": "PASS" if not cross else "FAIL",
        "scored_runs": runs,
        "external_corpora": external,
        "integrity_checks": {
            "forbidden_test_artifacts_present": forbidden,
            "learned_scores_present_in_scored_files": leak,
            "v6train_scored_ids_equal_dataset_ids": {
                r: sorted(x["pair_id"] for x in jl(RUNS[r]["pairs"])) == sorted(
                    x["pair_id"] for x in jl(f"{DATASETS[RUNS[r]['dataset']]}/pairs_{RUNS[r]['split']}.jsonl"))
                for r in ("v6train_v7", "v6dev_v7", "v8dev_v8_rescore", "v6test_v6")},
        },
    })
    write("raw/_fit_inputs_check.json", {k: W["inputs"][k] for k in W["inputs"]})
    print("ok", len(rows_csv), "csv rows; forbidden:", forbidden, "leak:", leak)


if __name__ == "__main__":
    main()
