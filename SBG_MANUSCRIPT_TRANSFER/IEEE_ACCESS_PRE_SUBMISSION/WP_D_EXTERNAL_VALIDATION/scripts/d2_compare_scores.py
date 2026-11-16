#!/usr/bin/env python3
"""WP-D / D2: per-pair comparison of a RE-EXECUTED scores file against the COMMITTED one
(stdlib only; own AUROC / bootstrap code).

    d2_compare_scores.py KIND COMMITTED NEW OUT_PREFIX [--tol 1e-3]

KIND:
  bugsinpy   pairs_bugsinpy_output_free_v7.jsonl format (jsonl, bug_id, scores.*)
  quixbugs   pairs_quixbugs_<regime>_output_free_v7.jsonl format (jsonl, base_id, scores.*)
  v8dump     artifacts/paper_evidence/raw/external_rescore_v8_pairs.json format
             (json {corpus: [rows]}), compared per corpus

Outputs: OUT_PREFIX.json (summary), OUT_PREFIX_mismatches.csv (every pair whose sbg_v5 or
evaluated flag differs, with all predictor diffs).
Classification printed in the summary:
  EXACT              : all pairs evaluated-flag equal and every numeric score equal (==)
  WITHIN_TOLERANCE   : not exact, but every pair's |sbg_v5 diff| <= tol, evaluated flags equal, and |AUROC delta| <= tol (default 1e-3; chosen by D2 after inspecting B1 (max diff 6.5e-4), BEFORE B2/B3/C results were seen)
  NOT_REPRODUCED     : otherwise
"""
import collections
import csv
import json
import math
import pathlib
import random
import sys

B, SEED = 2000, 42


def auroc(s, y):
    n = len(s)
    order = sorted(range(n), key=lambda i: s[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and s[order[j + 1]] == s[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    npos = sum(y)
    nneg = n - npos
    if npos == 0 or nneg == 0:
        return None
    return (sum(ranks[i] for i in range(n) if y[i] == 1) - npos * (npos + 1) / 2.0) / (npos * nneg)


def ci(s, y, c):
    by = collections.defaultdict(list)
    for i, k in enumerate(c):
        by[k].append(i)
    keys = sorted(by)
    rng = random.Random(SEED)
    v = []
    for _ in range(B):
        idx = []
        for _k in keys:
            idx.extend(by[keys[rng.randrange(len(keys))]])
        lab = [y[i] for i in idx]
        if 0 < sum(lab) < len(lab):
            v.append(auroc([s[i] for i in idx], lab))
    v.sort()
    m = len(v)
    return [round(v[max(0, int(math.floor(0.025 * m)))], 6), round(v[min(m - 1, int(math.ceil(0.975 * m)) - 1)], 6)]


def norm(kind, path, corpus=None):
    """-> {pair_id: dict(label, cluster, transformation, evaluated, scores{})}"""
    out = {}
    p = pathlib.Path(path)
    if kind == "v8dump":
        rows = json.loads(p.read_text())[corpus]
        for r in rows:
            sc = dict(r["scores"]) if r.get("scores") else {}
            out[r["pair_id"]] = dict(label=r["label"], cluster=r["cluster"], transformation=r["transformation"],
                                     evaluated=r["evaluated"], scores=sc,
                                     extra={"base_self_distance_v5": r.get("base_self_distance_v5"),
                                            "base_entry_fn": r.get("base_entry_fn"),
                                            "variant_entry_fn": r.get("variant_entry_fn"),
                                            "failure_kind": r.get("failure_kind")})
        return out
    for l in p.read_text().splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if kind == "bugsinpy":
            out[r["pair_id"]] = dict(label=r["label"], cluster=r["bug_id"], transformation=r["transformation"],
                                     evaluated=r["evaluated"], scores=dict(r["scores"] or {}),
                                     extra={"failure_kind": r.get("failure_kind")})
        else:
            tr = "real_bug" if r["pair_kind"] == "real_bug" else r["pair_kind"].split(":")[1]
            out[r["pair_id"]] = dict(label=r["label"], cluster=r["base_id"], transformation=tr,
                                     evaluated=r["evaluated"], scores=dict(r["scores"] or {}),
                                     extra={"failure_kind": r.get("failure_kind")})
    return out


def compare(kind, committed, new, prefix, tol, corpus=None):
    a, b = norm(kind, committed, corpus), norm(kind, new, corpus)
    ids_a, ids_b = set(a), set(b)
    common = sorted(ids_a & ids_b)
    res = {"kind": kind, "corpus": corpus, "committed": str(committed), "new": str(new), "tol": tol,
           "n_committed": len(a), "n_new": len(b), "n_common": len(common),
           "only_in_committed": sorted(ids_a - ids_b)[:20], "only_in_new": sorted(ids_b - ids_a)[:20]}
    eval_diff, pair_rows = [], []
    pred_stats = collections.defaultdict(lambda: {"n": 0, "exact": 0, "max_abs": 0.0, "n_diff_gt_tol": 0})
    n_exact_pairs = n_within = 0
    for pid in common:
        x, y = a[pid], b[pid]
        if x["evaluated"] != y["evaluated"]:
            eval_diff.append({"pair_id": pid, "committed_evaluated": x["evaluated"], "new_evaluated": y["evaluated"],
                              "committed_failure": x["extra"].get("failure_kind"),
                              "new_failure": y["extra"].get("failure_kind")})
            pair_rows.append({"pair_id": pid, "transformation": x["transformation"], "label": x["label"],
                              "evaluated_committed": x["evaluated"], "evaluated_new": y["evaluated"],
                              "sbg_v5_committed": x["scores"].get("sbg_v5"), "sbg_v5_new": y["scores"].get("sbg_v5"),
                              "abs_diff_sbg_v5": "", "other_predictors_differing": ""})
            continue
        if not x["evaluated"]:
            continue
        keys = sorted(set(x["scores"]) | set(y["scores"]))
        diffs = {}
        for k in keys:
            u, v = x["scores"].get(k), y["scores"].get(k)
            st = pred_stats[k]
            st["n"] += 1
            if u is None or v is None:
                if u != v:
                    st["n_diff_gt_tol"] += 1
                    diffs[k] = "missing_on_one_side"
                else:
                    st["exact"] += 1
                continue
            d = abs(u - v)
            st["exact"] += d == 0.0
            st["max_abs"] = max(st["max_abs"], d)
            if d > tol:
                st["n_diff_gt_tol"] += 1
            if d != 0.0:
                diffs[k] = d
        if not diffs:
            n_exact_pairs += 1
        elif not isinstance(diffs.get("sbg_v5", 0.0), str) and diffs.get("sbg_v5", 0.0) <= tol:
            n_within += 1          # tolerance applies to sbg_v5 only; other predictors are reported, not gated
        if diffs:
            pair_rows.append({"pair_id": pid, "transformation": x["transformation"], "label": x["label"],
                              "evaluated_committed": True, "evaluated_new": True,
                              "sbg_v5_committed": x["scores"].get("sbg_v5"), "sbg_v5_new": y["scores"].get("sbg_v5"),
                              "abs_diff_sbg_v5": diffs.get("sbg_v5", 0.0),
                              "other_predictors_differing": ";".join(f"{k}:{v}" for k, v in diffs.items() if k != "sbg_v5")})
    n_both_eval = sum(1 for pid in common if a[pid]["evaluated"] and b[pid]["evaluated"])
    res.update(n_both_evaluated=n_both_eval, evaluated_flag_disagreements=eval_diff,
               n_pairs_all_predictors_exact=n_exact_pairs, n_pairs_differing_but_within_tol=n_within,
               n_pairs_beyond_tol=n_both_eval - n_exact_pairs - n_within,
               sbg_v5=dict(pred_stats.get("sbg_v5", {})),
               per_predictor={k: dict(v) for k, v in sorted(pred_stats.items())})
    # self distance (v8dump only)
    if kind == "v8dump":
        sd = {}
        for pid in common:
            bp = pid  # keyed per pair; self distance is per base - gather by pair (dupes ok)
            u, v = a[pid]["extra"].get("base_self_distance_v5"), b[pid]["extra"].get("base_self_distance_v5")
            sd[pid] = (u, v)
        res["self_distance_pairs_equal"] = sum(1 for u, v in sd.values() if u == v)
        res["self_distance_pairs_total"] = len(sd)
        res["entry_fn_equal"] = sum(1 for pid in common if a[pid]["extra"].get("base_entry_fn") == b[pid]["extra"].get("base_entry_fn")
                                    and a[pid]["extra"].get("variant_entry_fn") == b[pid]["extra"].get("variant_entry_fn"))
    # AUROC on each side's own evaluated rows, all and SP-2-excluded, plus on the pairs both evaluated
    aur = {}
    for name, dd in (("committed", a), ("new", b)):
        for ex in (False, True):
            rows = [r for r in dd.values() if r["evaluated"] and not (ex and r["transformation"] == "SP-2")]
            s = [r["scores"]["sbg_v5"] for r in rows]
            yv = [r["label"] for r in rows]
            c = [r["cluster"] for r in rows]
            if 0 < sum(yv) < len(yv):
                aur[f"{name}{'_exSP2' if ex else ''}"] = {"n": len(rows), "n_pos": sum(yv), "auroc": round(auroc(s, yv), 6),
                                                          "ci95": ci(s, yv, c)}
    res["auroc_own_evaluated_rows"] = aur
    if aur.get("committed") and aur.get("new"):
        res["auroc_delta_new_minus_committed"] = round(aur["new"]["auroc"] - aur["committed"]["auroc"], 6)
    if aur.get("committed_exSP2") and aur.get("new_exSP2"):
        res["auroc_delta_exSP2_new_minus_committed"] = round(aur["new_exSP2"]["auroc"] - aur["committed_exSP2"]["auroc"], 6)
    exact = (not eval_diff and not res["only_in_committed"] and not res["only_in_new"] and res["n_pairs_beyond_tol"] == 0
             and res["n_pairs_differing_but_within_tol"] == 0)
    d_all = abs(res.get("auroc_delta_new_minus_committed", 0.0))
    d_ex = abs(res.get("auroc_delta_exSP2_new_minus_committed", 0.0))
    within = (not eval_diff and not res["only_in_committed"] and not res["only_in_new"] and res["n_pairs_beyond_tol"] == 0
              and d_all <= tol and d_ex <= tol)
    res["classification"] = "REPRODUCED-EXACT" if exact else ("REPRODUCED-WITHIN-TOLERANCE" if within else "NOT-REPRODUCED")
    pathlib.Path(str(prefix) + ".json").write_text(json.dumps(res, indent=1) + "\n")
    with open(str(prefix) + "_mismatches.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["pair_id", "transformation", "label", "evaluated_committed", "evaluated_new",
                                           "sbg_v5_committed", "sbg_v5_new", "abs_diff_sbg_v5", "other_predictors_differing"])
        w.writeheader()
        w.writerows(pair_rows)
    return res


def main():
    kind, committed, new, prefix = sys.argv[1:5]
    tol = float(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[5] == "--tol" else 1e-3
    if kind == "v8dump":
        allres = {}
        for corpus in ("bugsinpy", "quixbugs_canonical"):
            allres[corpus] = compare(kind, committed, new, f"{prefix}_{corpus}", tol, corpus)
        res = allres
    else:
        res = {"": compare(kind, committed, new, prefix, tol)}
    for k, r in res.items():
        print(k or kind, r["classification"], "common", r["n_common"], "both_eval", r["n_both_evaluated"],
              "exact_pairs", r["n_pairs_all_predictors_exact"], "within_tol", r["n_pairs_differing_but_within_tol"],
              "beyond_tol", r["n_pairs_beyond_tol"], "eval_flag_diffs", len(r["evaluated_flag_disagreements"]),
              "sbg_v5 max_abs", r["sbg_v5"].get("max_abs"), "auroc", r["auroc_own_evaluated_rows"].get("committed", {}).get("auroc"),
              "->", r["auroc_own_evaluated_rows"].get("new", {}).get("auroc"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
