#!/usr/bin/env python3
"""
benchmark/scripts/generate_v10_independent.py  --  independent, size-matched, ORACLE-VALIDATED test set (v10_independent).

Programs: the 19 programs of benchmark/corpus/fresh_programs/ that were never placed in any v8/v9 split and appear in no scored artifact.
validation_report.json shows they were excluded from v8 ONLY by the token-Jaccard novelty rule (0.101-0.146 > 0.10 vs a corpus sibling); every
other validity check passed (compiles, stdlib-only, non-trivial, entry point, 11/11 battery inputs execute, deterministic).  They are therefore
UNSEEN but not unrelated: each is an algorithmic sibling (e.g. gnome sort vs insertion sort) of a program in the development data.
This is disclosed as a limitation of independence; it is not hidden.

Construction (score-free, label-validated independently of the transformation family):
  for every program p, every SP type t in SP-1..SP-12 and seed s in {0,1,2}:
    EQ  = SP_t,s(p)                       accepted iff  check_candidate passes  AND  oracle(EQ) == oracle(p) on every protocol input
    CH  = SP_t,s(SC_k(p))  (k by the v9 score-free rotation; first k accepted) accepted iff check_candidate passes AND
          oracle(SC_k(p)) != oracle(p) on >= 1 protocol input  AND  oracle(CH) == oracle(SC_k(p)) on every input
          (the SP rewrite preserved the mutant -- the label comes from the mutation, not from a broken rewrite)
  A matched set = (EQ, CH) with the same t, s, p; both are required.  Unmatched candidates are logged, not silently dropped.
`oracle` = (return value, exception type, in-place argument mutation, stdout) of the structurally selected entry on the protocol's own
inputs (entry_policy.select_entry_structural).  Outputs are used ONLY to validate labels here; they are never a score input.
No SBG score, edit size, or label statistic is used to choose anything.  Everything is written before any scoring.

    PYTHONHASHSEED=0 python benchmark/scripts/generate_v10_independent.py
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import signal
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments" / "final"))
from benchmark.scripts.generate_v8_dataset import SC_TYPES, SP_TYPES, check_candidate            # noqa: E402
from benchmark.scripts.generate_v9_composed import compose                                         # noqa: E402
from benchmark.transformations.preserving.transformer import apply_transformation                  # noqa: E402
from experiments.final.entry_policy import select_entry_structural                                 # noqa: E402

PROGRAMS = ["ds_min_heap_array", "ds_ranked_set", "ds_union_find", "graph_alien_dict", "graph_cycle_detection_dfs", "graph_network_delay",
            "graph_topological_kahn", "math_coin_change", "math_fib_matrix", "math_knapsack_01", "sort_bitonic_sort", "sort_gnome_sort",
            "sort_gravity_bead", "sort_pancake", "sort_radix_sort_lsd", "sort_stooge_sort", "sort_tree_sort", "str_decode_run_length",
            "str_group_anagrams"]
SEEDS = [0, 1, 2]
OUT = REPO / "benchmark" / "datasets" / "v10_independent"
CORPUS = REPO / "benchmark" / "corpus" / "fresh_programs"


class _Timeout(Exception):
    pass


def _alarm(*_):
    raise _Timeout()


def _load(path):
    re.purge()
    spec = importlib.util.spec_from_file_location("_v10_mod", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def oracle(path: pathlib.Path):
    """Per-input (status, value/exception type, post-call args, stdout) for the structurally selected entry; None if unusable."""
    src = path.read_text()
    try:
        dec = select_entry_structural(src)
        fn = getattr(_load(path), dec.name)
    except BaseException:                                                        # noqa: BLE001
        return None
    out = []
    old = signal.signal(signal.SIGALRM, _alarm)
    try:
        for inp in dec.inputs:
            args = copy.deepcopy(inp)
            buf = io.StringIO()
            signal.setitimer(signal.ITIMER_REAL, 2.0)
            try:
                with contextlib.redirect_stdout(buf):
                    r = fn() if args is None or args == [None] else (fn(*args) if isinstance(args, tuple) else fn(args))
                out.append(("ok", repr(r)[:400], repr(args)[:400], buf.getvalue()[:200]))
            except _Timeout:
                out.append(("timeout", "", "", ""))
            except BaseException as exc:                                         # noqa: BLE001
                out.append(("exc", type(exc).__name__, repr(args)[:400], buf.getvalue()[:200]))
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
    finally:
        signal.signal(signal.SIGALRM, old)
    return out


def usable(o):
    return o is not None and not any(x[0] == "timeout" for x in o)


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def main():
    vdir = OUT / "variants" / "test"
    vdir.mkdir(parents=True, exist_ok=True)
    pairs, log = [], []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        for prog in PROGRAMS:
            bp = CORPUS / f"{prog}.py"
            bsrc = bp.read_text()
            ob = oracle(bp)
            if not usable(ob):
                log.append({"program": prog, "stage": "base_oracle", "reason": "unusable"})
                continue
            j = 0
            for sp in SP_TYPES:
                for s in SEEDS:
                    tag = {"program": prog, "sp": sp, "seed": s}
                    try:
                        kw = {"max_names": 1} if sp in ("SP-1", "SP-2") else {}
                        eq_src, _ = apply_transformation(str(bp), sp, seed=s, **kw)
                    except Exception as exc:                                       # noqa: BLE001
                        log.append({**tag, "stage": "eq_generate", "reason": type(exc).__name__}); continue
                    ok, why = check_candidate(bsrc, eq_src, "EQUIVALENT")
                    if not ok:
                        log.append({**tag, "stage": "eq_check", "reason": why}); continue
                    eqp = tmp / f"{prog}__eq_{sp}_{s}.py"; eqp.write_text(eq_src)
                    oe = oracle(eqp)
                    if not usable(oe) or oe != ob:
                        log.append({**tag, "stage": "eq_oracle", "reason": "output differs from base (label noise) or unusable"}); continue
                    chosen = None
                    for k in range(len(SC_TYPES)):
                        sc = SC_TYPES[(j + k) % len(SC_TYPES)]
                        try:
                            ch_src = compose(bp, sc, sp, s, tmp)
                        except Exception:                                            # noqa: BLE001
                            continue
                        if ch_src is None or not check_candidate(bsrc, ch_src, "CHANGED")[0]:
                            continue
                        # mutant alone (SC only) -- needs the mutation to change behaviour
                        from benchmark.transformations.mutations.mutator import apply_mutation
                        msrc, _ = apply_mutation(str(bp), sc, seed=s, site=0)
                        mp = tmp / f"{prog}__mut_{sc}_{s}.py"; mp.write_text(msrc)
                        om = oracle(mp)
                        cp = tmp / f"{prog}__ch_{sc}_{sp}_{s}.py"; cp.write_text(ch_src)
                        oc = oracle(cp)
                        if not (usable(om) and usable(oc)) or om == ob or oc != om:
                            continue
                        chosen = (sc, ch_src, eq_src)
                        break
                    j += 1
                    if chosen is None:
                        log.append({**tag, "stage": "ch_none", "reason": "no SC type yielded an oracle-validated composed CHANGED"}); continue
                    sc, ch_src, _ = chosen
                    eid = f"{prog}__{sp.lower().replace('-', '')}_s{s}"
                    cid = f"{prog}__{sc.lower().replace('-', '')}+{sp.lower().replace('-', '')}_s{s}"
                    (vdir / f"{eid}.py").write_text(eq_src); (vdir / f"{cid}.py").write_text(ch_src)
                    common = {"base_id": prog, "base_path": f"benchmark/corpus/fresh_programs/{prog}.py", "split": "test", "seed": s,
                              "gt_tier": "GT-T3", "hard_negative": False, "benchmark_version": "v10_independent", "label_validation": "dynamic_oracle"}
                    pairs.append({"pair_id": f"test__{eid}", "variant_id": eid, "variant_path": f"benchmark/datasets/v10_independent/variants/test/{eid}.py",
                                  "transformation_type": sp, "semantic_relation": "EQUIVALENT", "expected_label": "EQUIVALENT", "confidence": 0.99,
                                  "matched_pair_id": f"test__{cid}", **common})
                    pairs.append({"pair_id": f"test__{cid}", "variant_id": cid, "variant_path": f"benchmark/datasets/v10_independent/variants/test/{cid}.py",
                                  "transformation_type": f"{sc}+{sp}", "sc_type": sc, "sp_type": sp, "semantic_relation": "CHANGED",
                                  "expected_label": "CHANGED", "confidence": 0.99, "matched_pair_id": f"test__{eid}", **common})
    (OUT / "pairs_test.jsonl").write_text("".join(json.dumps(p) + "\n" for p in pairs))
    per = {}
    for p in pairs:
        d = per.setdefault(p["base_id"], {"equivalent": 0, "changed": 0})
        d["equivalent" if p["semantic_relation"] == "EQUIVALENT" else "changed"] += 1
    import collections
    man = {"benchmark_version": "v10_independent", "generator": "benchmark/scripts/generate_v10_independent.py",
           "programs_requested": PROGRAMS, "per_program": per, "n_pairs": len(pairs), "n_matched_sets": len(pairs) // 2,
           "n_programs_with_pairs": len(per), "rejections_by_stage": dict(collections.Counter(x["stage"] for x in log)),
           "rejections_by_sp_and_stage": {f"{k[0]}|{k[1]}": v for k, v in sorted(collections.Counter((x.get("sp"), x["stage"]) for x in log).items(), key=str)},
           "rejection_log": log, "pair_file_sha256": sha(OUT / "pairs_test.jsonl"),
           "scored": False, "note": "labels validated by a dynamic oracle on the protocol inputs; no SBG score or edit size was read"}
    (OUT / "manifest.json").write_text(json.dumps(man, indent=2) + "\n")
    print(len(pairs), "pairs;", len(per), "programs;", man["rejections_by_stage"])
    print({k: (v["equivalent"], v["changed"]) for k, v in per.items()})


if __name__ == "__main__":
    main()
