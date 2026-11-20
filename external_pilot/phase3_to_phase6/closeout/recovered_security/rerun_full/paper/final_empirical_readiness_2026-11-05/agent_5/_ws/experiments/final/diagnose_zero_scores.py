"""Zero-score forensic diagnostic (EXPLORATORY; reads outputs ONLY as a diagnostic oracle, never as a score input).

Question: what are the sbg_v5 == 0 pairs?  For every pair in the v9c matched populations (the pairs
`evaluate_v9.py` uses) record

  * the stored scores (from the frozen scored files),
  * an ORACLE comparison of the two programs on the protocol's own inputs: return value, exception, stdout and
    in-place argument mutation (ground truth for "behaviour differs on these inputs"),
  * a RAW trace comparison (event-type sequence; sequence of local-variable VALUES, i.e. name-free; the same
    values mapped through the state genome's abstraction),
  * for zero-scored CHANGED pairs and a seeded sample of non-zero CHANGED controls: genome-level comparison from
    a fresh extraction (unrounded component distances).

Nothing here changes a frozen artifact or any scorer.
Output: artifacts/paper_evidence/raw/zero_score_diagnostic_v1.json  (use --out to redirect)

    PYTHONHASHSEED=0 python experiments/final/diagnose_zero_scores.py --splits train,dev [--workers 4]
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import copy
import json
import os
import pathlib
import random
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments" / "final"))
DEFAULT_OUT = REPO / "artifacts/paper_evidence/raw/zero_score_diagnostic_v1.json"
CONTROL_SEED = 20261029


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def population(split):
    import evaluate_v9 as e
    pop = e.matched_complete(e.load("v9c", split))
    meta = {m["pair_id"]: m for m in jl(REPO / f"benchmark/datasets/v9_composed/pairs_{split}.jsonl")}
    meta.update({m["pair_id"]: m for m in jl(REPO / f"benchmark/datasets/v8/pairs_{split}.jsonl")})
    out = []
    for r in pop:
        m = meta[r["pair_id"]]
        out.append({"pair_id": r["pair_id"], "split": split, "base_id": r["base_id"], "label": r["label"],
                    "transformation_type": r["transformation_type"], "group": r["group"],
                    "base_path": m["base_path"], "variant_path": m["variant_path"], "edit": r["_edit"],
                    "scores": {k: r["scores"][k] for k in ("sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state")},
                    "base_n_events": r["base_n_events"], "variant_n_events": r["variant_n_events"],
                    "base_truncated": r["base_truncated"], "variant_truncated": r["variant_truncated"]})
    return out


# --------------------------------------------------------------------------- worker side
def _run(path):
    """Run one program under the Tracer as the v8 protocol does (1 run). Returns the traces + post-call args."""
    from experiments.final import extraction as ex
    from experiments.final.entry_policy import select_entry_structural
    from sbg.extraction.dynamic.tracer import Tracer
    p = REPO / path
    src = p.read_text()
    re.purge()
    mod, kind, detail = ex._load_module(p)
    if mod is None:
        return {"error": f"load:{kind}"}
    try:
        dec = select_entry_structural(src)
    except Exception as exc:                                            # noqa: BLE001
        return {"error": f"entry:{type(exc).__name__}"}
    fn = getattr(mod, dec.name)
    inputs = copy.deepcopy(dec.inputs)
    if inputs == [None]:
        tf = lambda _i: fn()                                            # noqa: E731
    elif isinstance(inputs[0], tuple):
        tf = lambda a: fn(*a)                                           # noqa: E731
    else:
        tf = fn
    traces = Tracer().trace(tf, inputs, max_events=ex.MAX_EVENTS, timeout_s=1.0, max_timeouts=2)
    return {"inputs": [repr(i) for i in dec.inputs], "after": [repr(i) for i in inputs], "traces": traces}


def _summ(run):
    from sbg.v5.state_transition_genome import _repr_to_abstract
    outs, types, vals, absv = [], [], [], []
    for t in run["traces"]:
        outs.append((repr(t.return_value)[:300], t.exception, t.stdout))
        types.append(tuple(e.event_type for e in t.events))
        vals.append(tuple(tuple(sorted(e.local_vars_snapshot.values())) for e in t.events))
        absv.append(tuple(tuple(sorted(_repr_to_abstract(v) for v in e.local_vars_snapshot.values()))
                          for e in t.events))
    return outs, types, vals, absv


def analyse_pair(row, cache):
    if row["base_path"] not in cache:
        cache[row["base_path"]] = _run(row["base_path"])
    a = cache[row["base_path"]]
    b = _run(row["variant_path"])
    rec = {k: row[k] for k in ("pair_id", "split", "base_id", "label", "transformation_type", "edit", "scores",
                               "base_n_events", "variant_n_events", "base_truncated", "variant_truncated")}
    if "error" in a or "error" in b:
        rec["oracle_error"] = a.get("error") or b.get("error")
        return rec
    oa, ta, va, aa = _summ(a)
    ob, tb, vb, ab = _summ(b)
    n = min(len(oa), len(ob))
    rec["n_inputs"] = [len(oa), len(ob)]
    rec["inputs_identical"] = a["inputs"] == b["inputs"]
    diff_out = [i for i in range(n) if oa[i] != ob[i]]
    diff_ret = [i for i in range(n) if oa[i][0] != ob[i][0] or oa[i][1] != ob[i][1]]
    diff_mut = [i for i in range(n) if a["after"][i] != b["after"][i]]
    rec["n_inputs_output_differs"] = len(set(diff_out) | set(diff_mut))
    rec["n_inputs_return_or_exception_differs"] = len(diff_ret)
    rec["n_inputs_stdout_differs"] = sum(1 for i in range(n) if oa[i][2] != ob[i][2])
    rec["n_inputs_arg_mutation_differs"] = len(diff_mut)
    rec["raw_event_types_equal"] = ta == tb
    rec["raw_values_equal"] = va == vb
    rec["abstract_values_equal"] = aa == ab
    rec["raw_event_count"] = [sum(len(x) for x in ta), sum(len(x) for x in tb)]
    return rec


def genome_level(row):
    """Fresh extraction of both sides; unrounded component distances and genome equality."""
    from experiments.final import extraction as ex
    from sbg.v3.genome import distance_v3
    from sbg.v5.temporal_genome_v5 import distance as tdist
    re.purge()
    A = ex.extract_program(str(REPO / row["base_path"]), {}, "output_free_v8")
    re.purge()
    B = ex.extract_program(str(REPO / row["variant_path"]), {}, "output_free_v8")
    if not (A.ok and B.ok):
        return {"genome_error": f"{A.failure_kind}/{B.failure_kind}"}
    ok_s = A.state is not None and B.state is not None
    return {"d_v3_unrounded": distance_v3(A.genome_v3, B.genome_v3),
            "d_temporal_unrounded": tdist(A.temporal, B.temporal) if A.temporal and B.temporal else None,
            "d_state_unrounded": ex._state_genome.distance(A.state, B.state) if ok_s else None,
            "temporal_available": [A.temporal is not None, B.temporal is not None],
            "state_available": [A.state is not None, B.state is not None],
            "genome_v3_dict_equal": A.genome_v3.to_dict() == B.genome_v3.to_dict(),
            "state_transitions_equal": (A.state.transitions == B.state.transitions) if ok_s else None,
            "state_n_transitions": [len(A.state.transitions), len(B.state.transitions)] if ok_s else None,
            "stats_diff": {k: [A.stats.get(k), B.stats.get(k)]
                           for k in ("call_count", "coverage_size", "n_events", "n_functions", "exception_fraction")
                           if A.stats.get(k) != B.stats.get(k)}}


def worker(base_id, split):
    pop = [r for r in population(split) if r["base_id"] == base_id]
    rng = random.Random(f"{CONTROL_SEED}-{split}-{base_id}")
    cache, out = {}, []
    for r in pop:
        rec = analyse_pair(r, cache)
        if r["label"] == 1 and (r["scores"]["sbg_v5"] == 0 or rng.random() < 0.35):
            try:
                rec["genome"] = genome_level(r)
            except Exception as exc:                                    # noqa: BLE001
                rec["genome"] = {"genome_error": f"{type(exc).__name__}: {exc}"}
        out.append(rec)
    print("@@" + json.dumps(out, default=str))


# --------------------------------------------------------------------------- driver side
def classify(rec):
    """Mutually exclusive cause class for a zero-scored pair (diagnostic only)."""
    if "oracle_error" in rec:
        return "oracle_unavailable"
    if rec["label"] == 0:
        return "EQ_zero_behaviour_identical" if rec["n_inputs_output_differs"] == 0 else "EQ_zero_but_output_differs"
    if rec["n_inputs_output_differs"] == 0:
        return ("CH_zero_no_output_difference__raw_state_identical" if rec["raw_values_equal"]
                else "CH_zero_no_output_difference__raw_state_differs_but_score_zero")
    if rec["raw_event_types_equal"] and rec["raw_values_equal"]:
        return "CH_zero_output_differs__trace_identical_invisible"
    if rec["raw_event_types_equal"] and rec["abstract_values_equal"]:
        return "CH_zero_output_differs__raw_values_differ_lost_in_abstraction"
    if rec["raw_event_types_equal"]:
        return "CH_zero_output_differs__abstract_values_differ_but_score_zero"
    return "CH_zero_output_differs__event_stream_differs_but_score_zero"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--worker")
    ap.add_argument("--split")
    ap.add_argument("--splits", default="train,dev")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    if args.worker:
        worker(args.worker, args.split)
        return
    splits = args.splits.split(",")
    jobs = []
    for s in splits:
        jobs += [(b, s) for b in sorted({r["base_id"] for r in population(s)})]

    def run(job):
        b, s = job
        p = subprocess.run([sys.executable, __file__, "--worker", b, "--split", s], capture_output=True, text=True,
                           cwd=str(REPO), timeout=1800, env={**os.environ, "PYTHONHASHSEED": "0"})
        line = [l for l in p.stdout.splitlines() if l.startswith("@@")]
        if not line:
            return [{"pair_id": None, "base_id": b, "split": s, "worker_error": p.stderr[-300:]}]
        return json.loads(line[0][2:])
    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        recs = [x for chunk in pool.map(run, jobs) for x in chunk]
    bad = [r for r in recs if r.get("worker_error")]
    recs = [r for r in recs if not r.get("worker_error")]
    for r in recs:
        r["zero"] = r["scores"]["sbg_v5"] == 0
        r["cause_class"] = classify(r) if r["zero"] else None
    summ = {}
    for s in splits:
        rs = [r for r in recs if r["split"] == s]
        def cnt(f): return sum(1 for r in rs if f(r))
        noor = lambda r: "oracle_error" not in r
        summ[s] = {
            "n_pairs": len(rs), "n_zero": cnt(lambda r: r["zero"]), "zero_rate": round(cnt(lambda r: r["zero"]) / len(rs), 4),
            "by_label": {lab: {"n": cnt(lambda r: r["label"] == lab), "n_zero": cnt(lambda r: r["label"] == lab and r["zero"])}
                         for lab in (0, 1)},
            "zero_cause_classes": dict(collections.Counter(r["cause_class"] for r in rs if r["zero"])),
            "changed_n": cnt(lambda r: r["label"] == 1),
            "changed_with_no_output_difference_on_protocol_inputs": cnt(lambda r: r["label"] == 1 and noor(r) and r["n_inputs_output_differs"] == 0),
            "changed_nonzero_with_no_output_difference": cnt(lambda r: r["label"] == 1 and not r["zero"] and noor(r) and r["n_inputs_output_differs"] == 0),
            "equivalent_with_output_difference": cnt(lambda r: r["label"] == 0 and noor(r) and r["n_inputs_output_differs"] > 0),
            "zero_with_truncated_trace": cnt(lambda r: r["zero"] and (r["base_truncated"] or r["variant_truncated"])),
            "oracle_unavailable": cnt(lambda r: not noor(r)),
        }
    pathlib.Path(args.out).write_text(json.dumps({
        "artifact": "zero_score_diagnostic_v1",
        "status": "EXPLORATORY diagnostic; the output oracle is used ONLY to explain scores, never as a score input",
        "population": "v9c matched-complete sets as defined by evaluate_v9.matched_complete",
        "splits": splits,
        "control_sampling": {"seed": CONTROL_SEED, "rule": "all zero-scored CHANGED pairs + non-zero CHANGED with p=0.35 get genome-level re-extraction"},
        "worker_errors": bad, "summary": summ, "pairs": recs}, indent=1, default=str) + "\n")
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
