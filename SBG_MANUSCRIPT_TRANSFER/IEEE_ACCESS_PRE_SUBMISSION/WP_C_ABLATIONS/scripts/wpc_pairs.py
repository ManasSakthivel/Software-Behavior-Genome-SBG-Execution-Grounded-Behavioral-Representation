#!/usr/bin/env python3
"""EXP-WPC-002: per-pair component distances from the EXP-WPC-001 genome bundles (dev / train only).

Recomputes, for every primary pair, the FROZEN distance components by importing SBG read-only
(sbg.v3.genome.distance_v3, sbg.v5.temporal_genome_v5.distance, StateTransitionGenome.distance) and checks them against the
frozen scores stored in configs/populations (rounded to 9 d.p., exactly as experiments/final/extraction.score_pair rounds).
The 8 terms of distance_v3 are re-evaluated term by term (formula copied verbatim from sbg/v3/genome.py) and their weighted sum is asserted
bit-equal to distance_v3 (same summation order).

Output: raw/EXP-WPC-002/<split>_pairs.csv  (+ VERIFY.json).  Original-SBG columns:  d_* , r_v5, r_v3, r_temporal, r_state.
EXPLORATORY (modified-representation) columns:  sv_* (state variants), rv_* (return-value multisets), sk_* (state by event kind).
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve()
WPC = HERE.parents[1]
PKG = WPC.parent
REPO = PKG.parent / "SBG"
sys.path.insert(0, str(REPO))
os.chdir(REPO)

from sbg.v3.genome import DynamicGenomeV3, distance_v3                      # noqa: E402
from sbg.v5.temporal_genome_v5 import TemporalGenomeV5, distance as temporal_distance   # noqa: E402
from sbg.v5.state_transition_genome import StateTransitionGenome, StateTransitionGraph  # noqa: E402

SG = StateTransitionGenome()
BUNDLES = WPC / "raw" / "EXP-WPC-001"
OUT = WPC / "raw" / "EXP-WPC-002"
W = dict(cov=0.20, seq=0.25, freq=0.20, exc=0.10, dep=0.10, con=0.05, inp=0.05, exc2=0.05)
STATE_VARIANTS = ["s0", "s_noret", "s_args", "s_args_noret", "s_boundary", "s_boundary_noret", "s_structure", "s_shuffle"]
RV_VARIANTS = ["rv_abs100", "rv_abs_full", "rv_type_abs", "rv_hash", "rv_entry_hash"]
EKINDS = ["state_creation", "state_mutation", "state_deletion", "resource_acquire", "resource_release", "error_transition",
          "error_recovery", "data_flow"]


def bundle_path(split, base_id, rel):
    fn = hashlib.sha1(rel.encode()).hexdigest()[:12] + "__" + pathlib.Path(rel).stem + ".json.gz"
    return BUNDLES / split / base_id / fn


_cache = {}


def load(split, base_id, rel):
    k = (split, base_id, rel)
    if k in _cache:
        return _cache[k]
    p = bundle_path(split, base_id, rel)
    if not p.exists():
        _cache[k] = None
        return None
    d = json.load(gzip.open(p, "rt"))
    if d.get("ok") and "v3" in d:
        v3 = dict(d["v3"])
        v3["anon_call_freq"] = {int(a): b for a, b in v3["anon_call_freq"].items()}
        d["g_v3"] = DynamicGenomeV3(**v3)
        d["g_t"] = TemporalGenomeV5(**d["temporal"]) if d.get("temporal") is not None else None
        d["g_s"] = ({n: StateTransitionGraph(transitions={tuple(x[:4]): x[4] for x in v}) for n, v in d["state_variants"].items()}
                    if d.get("state_frozen") is not None else None)
        d["g_s_frozen"] = StateTransitionGraph(transitions={tuple(x[:4]): x[4] for x in d["state_frozen"]}) \
            if d.get("state_frozen") is not None else None
    _cache[k] = d
    return d


def v3_terms(g1, g2):
    """verbatim term-by-term copy of sbg.v3.genome.distance_v3 (returns the 8 unweighted components)."""
    max_cov = max(g1.coverage_size, g2.coverage_size, 1)
    d_cov = abs(g1.coverage_size - g2.coverage_size) / max_cov
    all_b = set(g1.call_transition_bigrams) | set(g2.call_transition_bigrams)
    if not all_b:
        d_seq = 0.0
    else:
        l1 = sum(abs(g1.call_transition_bigrams.get(b, 0.0) - g2.call_transition_bigrams.get(b, 0.0)) for b in all_b)
        d_seq = min(1.0, l1 / 2.0)
    all_f = set(g1.anon_call_freq) | set(g2.anon_call_freq)
    if not all_f:
        d_freq = 0.0
    else:
        l1 = sum(abs(g1.anon_call_freq.get(f, 0.0) - g2.anon_call_freq.get(f, 0.0)) for f in all_f)
        d_freq = min(1.0, l1 / 2.0)
    s1, s2 = set(g1.exception_type_set), set(g2.exception_type_set)
    un = len(s1 | s2)
    jac = 0.0 if un == 0 else (1.0 - len(s1 & s2) / un)
    d_exc = 0.5 * jac + 0.5 * abs(g1.exception_rate - g2.exception_rate)
    md = max(g1.call_depth_mean, g2.call_depth_mean, 1.0)
    d_dep = abs(g1.call_depth_mean - g2.call_depth_mean) / md
    d_con = abs(g1.coverage_consistency - g2.coverage_consistency)
    d_inp = abs(g1.input_sensitivity_score - g2.input_sensitivity_score)
    d_exc2 = 0.0 if g1.exception_causality_hash == g2.exception_causality_hash else 1.0
    t = dict(cov=d_cov, seq=d_seq, freq=d_freq, exc=d_exc, dep=d_dep, con=d_con, inp=d_inp, exc2=d_exc2)
    total = (W["cov"] * d_cov + W["seq"] * d_seq + W["freq"] * d_freq + W["exc"] * d_exc + W["dep"] * d_dep
             + W["con"] * d_con + W["inp"] * d_inp + W["exc2"] * d_exc2)
    return t, max(0.0, min(1.0, total))


def wjaccard(a, b):
    """frequency-weighted Jaccard distance on {key: count} (identical formula to StateTransitionGenome.distance)."""
    keys = set(a) | set(b)
    if not keys:
        return 0.0
    num = den = 0.0
    for k in keys:
        f1, f2 = a.get(k, 0), b.get(k, 0)
        num += min(f1, f2)
        den += max(f1, f2)
    if den == 0.0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - num / den))


def process(split):
    rows = [r for r in json.loads((PKG / "configs" / "populations" / f"{split}.json").read_text())["rows"]
            if r.get("in_primary_population")]
    out, excl = [], []
    ver = dict(n_primary=len(rows), n_scored=0, n_excluded=0, v3_term_sum_bit_equal=0, v3_term_sum_not_equal=0, match_v5=0, match_v3=0,
               match_temporal=0, match_state=0, s0_equals_frozen_state_graph=0, n_v5_not_full=0)
    for r in rows:
        A = load(split, r["base_id"], r["base_path"])
        B = load(split, r["base_id"], r["variant_path"])
        if A is None or B is None or not A.get("ok") or not B.get("ok") or "g_v3" not in A or "g_v3" not in B:
            excl.append({"pair_id": r["pair_id"], "base_id": r["base_id"],
                         "reason": "no bundle (program missing from EXP-WPC-001)" if (A is None or B is None) else "extraction not ok"})
            continue
        g1, g2 = A["g_v3"], B["g_v3"]
        terms, tot = v3_terms(g1, g2)
        d_v3 = distance_v3(g1, g2)
        ver["v3_term_sum_bit_equal" if tot == d_v3 else "v3_term_sum_not_equal"] += 1
        # temporal
        if A["g_t"] is not None and B["g_t"] is not None:
            try:
                d_t, t_ok = temporal_distance(A["g_t"], B["g_t"]), True
            except Exception:                                    # noqa: BLE001
                d_t, t_ok = d_v3, False
        else:
            d_t, t_ok = d_v3, False
        # state (frozen) + variants
        if A["g_s_frozen"] is not None and B["g_s_frozen"] is not None:
            try:
                d_s, s_ok = SG.distance(A["g_s_frozen"], B["g_s_frozen"]), True
            except Exception:                                    # noqa: BLE001
                d_s, s_ok = d_v3, False
        else:
            d_s, s_ok = d_v3, False
        v5_full = t_ok and s_ok
        d_v5 = (0.50 * d_v3 + 0.25 * d_t + 0.25 * d_s) if v5_full else d_v3
        d_v5 = round(min(1.0, max(0.0, d_v5)), 9)
        sc = r["scores"]
        ver["match_v5"] += d_v5 == sc["sbg_v5"]
        ver["match_v3"] += round(d_v3, 9) == sc["sbg_v3"]
        ver["match_temporal"] += round(d_t, 9) == sc["sbg_temporal"]
        ver["match_state"] += round(d_s, 9) == sc["sbg_state"]
        ver["n_v5_not_full"] += (not v5_full)
        ver["s0_equals_frozen_state_graph"] += bool(A.get("s0_equals_frozen")) and bool(B.get("s0_equals_frozen"))
        row = {"pair_id": r["pair_id"], "base_id": r["base_id"], "label": r["label"], "group": r["group"], "edit": r["edit"],
               "sc_type": r.get("sc_type") or "", "sp_type": r.get("sp_type") or "", "v5_full": int(v5_full),
               "f_v5": sc["sbg_v5"], "f_v3": sc["sbg_v3"], "f_temporal": sc["sbg_temporal"], "f_state": sc["sbg_state"],
               "r_v5": d_v5, "r_v3": round(d_v3, 9), "r_temporal": round(d_t, 9), "r_state": round(d_s, 9),
               "raw_v3": d_v3, "raw_t": d_t, "raw_s": d_s}
        for k, v in terms.items():
            row[f"d_{k}"] = v
        for n in STATE_VARIANTS:
            try:
                row[f"sv_{n}"] = SG.distance(A["g_s"][n], B["g_s"][n])
            except Exception:                                    # noqa: BLE001
                row[f"sv_{n}"] = d_v3
        for kind in EKINDS:
            ta = {k: v for k, v in A["g_s_frozen"].transitions.items() if k[2] == kind}
            tb = {k: v for k, v in B["g_s_frozen"].transitions.items() if k[2] == kind}
            row[f"sk_{kind}"] = wjaccard(ta, tb)
        for n in RV_VARIANTS:
            row[f"rv_{n[3:]}"] = wjaccard(A["rv"][n], B["rv"][n])
        out.append(row)
        ver["n_scored"] += 1
    ver["n_excluded"] = len(excl)
    return out, excl, ver


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", default="v9c_dev,v9c_train")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    allv = {}
    for split in a.splits.split(","):
        if split not in ("v9c_dev", "v9c_train"):
            sys.exit("refused: WP-C pair stage only for v9c_dev / v9c_train")
        target = OUT / f"{split}_pairs.csv"
        if target.exists():
            sys.exit(f"refusing to overwrite {target}")
        rows, excl, ver = process(split)
        with open(target, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        (OUT / f"{split}_exclusions.json").write_text(json.dumps(excl, indent=1))
        allv[split] = ver
        print(split, ver, "excluded", len(excl))
    (OUT / "VERIFY.json").write_text(json.dumps(allv, indent=1))


if __name__ == "__main__":
    main()
