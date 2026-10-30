"""Score-only zero-rate population report (reads frozen scored files; executes nothing, uses no outputs).

Writes artifacts/paper_evidence/raw/zero_score_population_v1.json:
  * for every scored file: n rows, n evaluated, n unevaluated by failure_kind, n exact-zero sbg_v5 (and components),
    smallest non-zero value (rules out rounding to zero), v5_full flag counts;
  * for the v9c matched populations (evaluate_v9.matched_complete): zero rate by label, program, transformation
    family (SC part / SP part), edit-size bucket, truncation status.
No forensic oracle is run here; this is descriptive and uses scores only.

    python experiments/final/zero_score_population.py
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments" / "final"))
ART = REPO / "artifacts/final"
OUT = REPO / "artifacts/paper_evidence/raw/zero_score_population_v1.json"
FILES = ["pairs_v9c_train_output_free_v8", "pairs_v9c_dev_output_free_v8", "pairs_v9c_val_output_free_v8",
         "pairs_v8train_output_free_v8", "pairs_v8dev_output_free_v8", "pairs_v8val_output_free_v8",
         "pairs_v8test_output_free_v8"]


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def edit_bucket(e):
    return "<=2" if e <= 2 else "3-5" if e <= 5 else "6-10" if e <= 10 else "11-20" if e <= 20 else ">20"


def rate(rows):
    z = sum(1 for r in rows if r["scores"]["sbg_v5"] == 0)
    return {"n": len(rows), "n_zero": z, "zero_rate": round(z / len(rows), 4) if rows else None}


def main():
    out = {"artifact": "zero_score_population_v1", "status": "descriptive; score-only; no outputs or oracle used",
           "files": {}, "v9c_matched": {}}
    for f in FILES:
        rows = jl(ART / f"{f}.jsonl")
        ev = [r for r in rows if r["evaluated"]]
        nz = [r["scores"]["sbg_v5"] for r in ev if r["scores"]["sbg_v5"] > 0]
        zr = [r for r in ev if r["scores"]["sbg_v5"] == 0]
        out["files"][f] = {
            "n_rows": len(rows), "n_evaluated": len(ev),
            "unevaluated_by_failure_kind": dict(collections.Counter(r.get("failure_kind") for r in rows if not r["evaluated"])),
            "sbg_v5_exact_zero": len(zr), "sbg_v5_zero_rate_of_evaluated": round(len(zr) / len(ev), 4),
            "components_all_exact_zero_given_v5_zero": all(r["scores"][k] == 0 for r in zr for k in ("sbg_v3", "sbg_temporal", "sbg_state")),
            "smallest_nonzero_sbg_v5": min(nz), "v5_full_counts": dict(collections.Counter(r["scores"]["v5_full"] for r in ev)),
            "unevaluated_rows_have_scores": any(r.get("scores") for r in rows if not r["evaluated"]),
            "evaluated_with_truncated_trace": sum(1 for r in ev if r["base_truncated"] or r["variant_truncated"])}
    import evaluate_v9 as e
    for split in ("train", "dev", "val"):
        pop = e.matched_complete(e.load("v9c", split))
        d = {"population": rate(pop), "by_label": {("CHANGED" if l else "EQUIVALENT"): rate([r for r in pop if r["label"] == l]) for l in (1, 0)}}

        def grp(key, lab=None):
            g = collections.defaultdict(list)
            for r in pop:
                if lab is None or r["label"] == lab:
                    g[key(r)].append(r)
            return {str(k): rate(v) for k, v in sorted(g.items(), key=lambda kv: str(kv[0]))}
        d["by_program"] = grp(lambda r: r["base_id"])
        d["changed_by_sc_type"] = grp(lambda r: r["transformation_type"].split("+")[0], 1)
        d["equivalent_by_sp_type"] = grp(lambda r: r["transformation_type"], 0)
        d["by_label_and_edit_bucket"] = grp(lambda r: (r["label"], edit_bucket(r["_edit"])))
        d["by_truncation"] = grp(lambda r: bool(r["base_truncated"] or r["variant_truncated"]))
        out["v9c_matched"][split] = d
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n")
    for s, d in out["v9c_matched"].items():
        print(s, d["population"], {k: v["n_zero"] for k, v in d["by_label"].items()})


if __name__ == "__main__":
    main()
