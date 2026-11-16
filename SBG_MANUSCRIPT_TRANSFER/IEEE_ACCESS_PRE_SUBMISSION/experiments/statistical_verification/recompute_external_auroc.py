#!/usr/bin/env python3
"""EXP-A3-007: recompute external-corpus AUROC (BugsInPy, QuixBugs-canonical) from RAW scored pair files, pure stdlib, own code.
General usage:
  recompute_external_auroc.py                      # default: the 4 committed external files/slices listed below
  recompute_external_auroc.py FILE.jsonl[:SCOREKEY[:CLUSTERKEY]] ...   # any jsonl with keys label, evaluated, scores[SCOREKEY]
Reports AUROC, cluster bootstrap CI (B=2000, seed 42; resampling scheme = diagnose_external.boot: rng.choice over sorted clusters,
percentile indices int(.025 n), int(.975 n)-1), n pairs / pos / neg / clusters, with and without SP-2 (entry-rename) negatives.
Slices:
 BugsInPy  v7 committed  (evaluated rows only)        -> reported 0.4099 (task text 0.410)
 BugsInPy  v8 rescore, SP-2 excluded                  -> reported 0.497
 QuixBugs  v7 canonical committed (152 pairs)         -> reported 0.3877 (task text 0.388)
 QuixBugs  v8 rescore, SP-2 excluded                  -> reported 0.4444 (task text 0.444)
Unevaluated pairs are DROPPED (never scored 0 or 0.5); a sensitivity row 'unevaluated=0.0' is given to show the effect of silent zeros.
"""
import collections, csv, json, pathlib, random, sys
PKG = pathlib.Path(__file__).resolve().parents[2]; REPO = PKG.parent / "SBG"; ART = REPO / "artifacts"

def jl(p): return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]

def auroc(s, y):
    P = sum(y); N = len(y) - P
    if P == 0 or N == 0: return 0.5
    num = 0.0
    pos = [a for a, b in zip(s, y) if b]; neg = [a for a, b in zip(s, y) if not b]
    for a in pos:
        for c in neg: num += 1.0 if a > c else 0.5 if a == c else 0.0
    return num / (P * N)

def boot(rows, key, n=2000, seed=42):
    by = collections.defaultdict(list)
    for r in rows: by[r[key]].append(r)
    ks, rng, o = sorted(by), random.Random(seed), []
    for _ in range(n):
        smp = [x for k in (rng.choice(ks) for _ in ks) for x in by[k]]
        y = [x["label"] for x in smp]
        if 0 < sum(y) < len(y): o.append(auroc([x["score"] for x in smp], y))
    o.sort()
    return [round(o[int(.025 * len(o))], 4), round(o[int(.975 * len(o)) - 1], 4)]

def summarise(name, rows, key, seed=42):
    y = [r["label"] for r in rows]
    return {"slice": name, "n_pairs": len(rows), "n_pos": sum(y), "n_neg": len(y) - sum(y), "n_clusters": len({r[key] for r in rows}),
            "auroc": round(auroc([r["score"] for r in rows], y), 4), "ci95_cluster_bootstrap": boot(rows, key, seed=seed) if rows else None, "seed": seed}

def main():
    out, rows_out = [], []
    # --- committed v7 files
    for corp, fn, ck, sp2key in [("bugsinpy", "final/pairs_bugsinpy_output_free_v7.jsonl", "bug_id", "transformation"),
                                  ("quixbugs_canonical", "final/pairs_quixbugs_canonical_output_free_v7.jsonl", "base_id", "pair_kind")]:
        raw = jl(ART / fn)
        def sp2(r):
            if corp == "bugsinpy": return r.get("transformation") == "SP-2"
            return r.get("pair_kind") == "sp_negative:SP-2"
        ev = [{"label": r["label"], "score": r["scores"]["sbg_v5"], key_: r[ck], "pair_id": r["pair_id"], "sp2": sp2(r)} for r in raw if r["evaluated"] for key_ in ["cl"]]
        zero = [{"label": r["label"], "score": (r["scores"]["sbg_v5"] if r["evaluated"] else 0.0), "cl": r[ck]} for r in raw]
        rows_out.append(summarise(f"{corp} v7 committed, evaluated only (all)", ev, "cl"))
        rows_out.append(summarise(f"{corp} v7 committed, evaluated only, SP-2 excluded", [r for r in ev if not r["sp2"]], "cl"))
        rows_out.append(summarise(f"{corp} v7 committed, SENSITIVITY unevaluated scored 0.0 (NOT the reported analysis)", zero, "cl"))
        rows_out[-1]["note"] = f"{sum(1 for r in raw if not r['evaluated'])} unevaluated rows of {len(raw)}"
        rows_out.append(summarise(f"{corp} v7 committed, evaluated only (all), seed 7", ev, "cl", seed=7))
    # --- v8 rescore
    resc = json.loads((ART / "paper_evidence/raw/external_rescore_v8_pairs.json").read_text())
    for corp in ("bugsinpy", "quixbugs_canonical"):
        ev = [{"label": r["label"], "score": r["sbg_v5"], "cl": r["cluster"], "sp2": r["transformation"] == "SP-2"} for r in resc[corp] if r["evaluated"]]
        rows_out.append(summarise(f"{corp} v8 rescore (all)", ev, "cl"))
        rows_out.append(summarise(f"{corp} v8 rescore, SP-2 excluded", [r for r in ev if not r["sp2"]], "cl"))
        rows_out.append(summarise(f"{corp} v8 rescore, SP-2 excluded, seed 7", [r for r in ev if not r["sp2"]], "cl", seed=7))
        # committed v7 on same pairs as rescore
        ev7 = [{"label": r["label"], "score": r["committed_sbg_v5"], "cl": r["cluster"]} for r in resc[corp] if r["evaluated"] and r.get("committed_sbg_v5") is not None]
        rows_out.append(summarise(f"{corp} committed_v7 scores on the rescored pair set", ev7, "cl"))
    # --- user supplied
    for a in sys.argv[1:]:
        parts = a.split(":"); fn = parts[0]; sk = parts[1] if len(parts) > 1 else "sbg_v5"; ck = parts[2] if len(parts) > 2 else "base_id"
        rr = [{"label": r["label"], "score": r["scores"][sk], "cl": r[ck]} for r in jl(fn) if r.get("evaluated")]
        rows_out.append(summarise(f"USER {fn} [{sk}]", rr, "cl"))
    return rows_out

if __name__ == "__main__":
    res = main()
    (PKG / "results/raw/EXP-A3-007").mkdir(parents=True, exist_ok=True)
    (PKG / "results/raw/EXP-A3-007/external_auroc_recompute.json").write_text(json.dumps(res, indent=1))
    with open(PKG / "results/tables/EXP-A3-007_external_auroc.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["slice", "n_pairs", "n_pos", "n_neg", "n_clusters", "auroc", "ci_lo", "ci_hi", "seed", "note"])
        for r in res: w.writerow([r["slice"], r["n_pairs"], r["n_pos"], r["n_neg"], r["n_clusters"], r["auroc"], *(r["ci95_cluster_bootstrap"] or ["", ""]), r["seed"], r.get("note", "")])
    for r in res: print(r["slice"], "|", r["n_pairs"], r["n_pos"], r["n_neg"], r["n_clusters"], r["auroc"], r["ci95_cluster_bootstrap"], r["seed"], r.get("note", ""))
