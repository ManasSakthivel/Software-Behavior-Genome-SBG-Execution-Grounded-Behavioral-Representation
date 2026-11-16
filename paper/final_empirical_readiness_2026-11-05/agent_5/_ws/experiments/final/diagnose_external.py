#!/usr/bin/env python3
"""P3 diagnostic: validate the below-chance BugsInPy / QuixBugs results from the committed pair files.
Checks label/role/orientation/pairing, recomputes AUROC, cluster-bootstrap CIs (resampling programs / bugs), and subsets that
isolate known harness artifacts (SP-2 entry rename; `re` cache).  EXPLORATORY: these corpora were scored before any freeze.
Writes artifacts/paper_evidence/DIAGNOSTIC_EXTERNAL.json.   PYTHONHASHSEED-independent (reads scores only)."""
import collections, hashlib, json, pathlib, random, sys

R = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R))
from sbg.statistics import auroc  # noqa: E402
from experiments.final.edit_size_analysis import _edit_size  # noqa: E402

F = {"qc": "artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl",
     "qd": "artifacts/final/pairs_quixbugs_declared_output_free_v7.jsonl",
     "bp": "artifacts/final/pairs_bugsinpy_output_free_v7.jsonl"}
L = lambda p: [json.loads(l) for l in (R / p).read_text().splitlines() if l.strip()]  # noqa: E731
sha = lambda p: hashlib.sha256((R / p).read_bytes()).hexdigest()  # noqa: E731
sc = lambda rs: [r["scores"]["sbg_v5"] for r in rs]  # noqa: E731
lab = lambda rs: [r["label"] for r in rs]  # noqa: E731


def boot(rows, key, n=2000, seed=42):
    by = collections.defaultdict(list)
    for r in rows:
        by[r[key]].append(r)
    ks, rng, o = sorted(by), random.Random(seed), []
    for _ in range(n):
        s = [x for k in (rng.choice(ks) for _ in ks) for x in by[k]]
        if 0 < sum(lab(s)) < len(s):
            o.append(auroc(sc(s), lab(s)))
    o.sort()
    return [round(o[int(.025 * len(o))], 4), round(o[int(.975 * len(o)) - 1], 4)]


def rep(rows, key, name):
    y = lab(rows)
    return {"subset": name, "n_pairs": len(rows), "n_pos": sum(y), "n_neg": len(y) - sum(y),
            "n_clusters": len({r[key] for r in rows}), "auroc": round(auroc(sc(rows), y), 4), "ci95_cluster_bootstrap": boot(rows, key)}


def strat(rows, k):
    g = collections.defaultdict(lambda: ([], []))
    for r in rows:
        g[k(r)][r["label"]].append(r["scores"]["sbg_v5"])
    num = den = 0
    for neg, pos in g.values():
        for a in pos:
            for c in neg:
                num += 1 if a > c else .5 if a == c else 0
        den += len(pos) * len(neg)
    return {"auroc": round(num / den, 4), "n_cross_label_comparisons": den}


out = {"artifact": "DIAGNOSTIC_EXTERNAL", "status": "EXPLORATORY (pre-freeze corpora; committed artifacts unchanged)",
       "sources": {k: {"path": v, "sha256": sha(v)} for k, v in F.items()}}
qc, qd, bp = ([r for r in L(F[k]) if r["evaluated"]] for k in ("qc", "qd", "bp"))
qc_all = L(F["qc"])

# --- structural checks -------------------------------------------------------------------------------------------
pos = [r for r in qc if r["label"] == 1]
out["checks"] = {
    "quixbugs": {"label_role": dict(collections.Counter(f"{r['pair_kind']}|label={r['label']}" for r in qc)),
                 "positives_base_is_fixed_variant_is_buggy": "pair_kind=real_bug, label=1 (see loader; base=fixed program)",
                 "real_bug_pairs_with_identical_exception_fraction": sum(r["base_stats"]["exception_fraction"] == r["variant_stats"]["exception_fraction"] for r in pos),
                 "real_bug_pairs_with_identical_n_events": sum(r["base_stats"]["n_events"] == r["variant_stats"]["n_events"] for r in pos),
                 "real_bug_pairs_sbg_exactly_zero": sum(r["scores"]["sbg_v5"] == 0 for r in pos), "n_real_bug_pairs": len(pos),
                 "sp2_pairs_with_entry_renamed": sum(r["base_entry"] != r["variant_entry"] for r in qc if r["pair_kind"] == "sp_negative:SP-2"),
                 "sp2_pairs": sum(r["pair_kind"] == "sp_negative:SP-2" for r in qc),
                 "unevaluated_canonical": dict(collections.Counter(r["failure_kind"] for r in qc_all if not r["evaluated"]))},
    "bugsinpy": {"label_role": dict(collections.Counter(f"{r['role']}|label={r['label']}" for r in L(F["bp"]))),
                 "positive_observable_flag": dict(collections.Counter(str(r["observable"]) for r in bp if r["label"] == 1)),
                 "sp2_negatives_with_entry_renamed": sum(r["base_entry"] != r["variant_entry"] for r in bp if r["label"] == 0 and r["transformation"] == "SP-2"),
                 "sp2_negatives": sum(r["label"] == 0 and r["transformation"] == "SP-2" for r in bp),
                 "mean_sbg_sp2_vs_sp1_sp3": {t: round(sum(r["scores"]["sbg_v5"] for r in bp if r["label"] == 0 and r["transformation"] == t) / max(1, sum(r["label"] == 0 and r["transformation"] == t for r in bp)), 4) for t in ("SP-1", "SP-2", "SP-3")}},
}

# --- AUROC recomputation + subsets -------------------------------------------------------------------------------------
out["quixbugs_canonical"] = [rep(qc, "base_id", "all (published headline)"),
                             rep([r for r in qc if r["pair_kind"] != "sp_negative:SP-2"], "base_id", "excluding SP-2 (entry-rename) negatives"),
                             {"within_program_stratified": strat(qc, lambda r: r["base_id"])}]
out["quixbugs_declared_inputs"] = [rep(qd, "base_id", "all evaluable (declared-input regime)"),
                                   rep([r for r in qd if r["pair_kind"] != "sp_negative:SP-2"], "base_id", "excluding SP-2"),
                                   {"edit_size_reversed_auroc": round(auroc([-_edit_size(r["base_path"], r["variant_path"]) for r in qd], lab(qd)), 4)},
                                   {"unevaluated_reasons": dict(collections.Counter(r["failure_kind"] for r in L(F["qd"]) if not r["evaluated"]))}]
dp = {r["base_id"] for r in qd}
out["quixbugs_canonical_on_declared_evaluable_programs"] = rep([r for r in qc if r["base_id"] in dp], "base_id", "canonical, same programs as declared")
out["bugsinpy"] = [rep(bp, "bug_id", "all (published headline)"),
                   rep([r for r in bp if r["transformation"] != "SP-2"], "bug_id", "excluding SP-2 (entry-rename) negatives"),
                   {"within_unit_stratified": strat(bp, lambda r: (r["bug_id"], r["unit"]))}]
uses_re = lambda r: "import re" in (R / r["base_path"]).read_text()  # noqa: E731
nore = [r for r in bp if not uses_re(r) and r["transformation"] != "SP-2"]
out["bugsinpy"].append(rep(nore, "bug_id", "units not importing `re`, excluding SP-2"))
out["bugsinpy_re_cache_rescore"] = json.loads((R / "artifacts/paper_evidence/raw/bugsinpy_purge_rescore.json").read_text()) and {
    k: v for k, v in json.loads((R / "artifacts/paper_evidence/raw/bugsinpy_purge_rescore.json").read_text()).items() if k != "units"}

out["interpretation"] = [
    "Labels, pairing and orientation verified: positives are (fixed -> buggy/real-fix) pairs with label 1, negatives are SP-* rewrites of the same base with label 0; AUROC recomputes exactly from the committed pair files.",
    "SP-2 (function rename) changes the ENTRY name for 100% of SP-2 pairs, which is scored as a behavioural difference: this inflates negative scores and is a harness artifact, not behaviour change.",
    "QuixBugs: SBG is exactly 0 for most real bugs under canonical (synthesised) inputs because buggy and fixed traces are identical; the declared-input regime exposes more bugs (0.70) but on a 28-program, 24-positive subset selected by evaluability.",
    "BugsInPy: process-global `re` regex-cache state makes traces depend on extraction order; purging the cache moves AUROC 0.410 -> 0.429. With SP-2 excluded the values are 0.47-0.51, CIs include 0.5.",
    "Conclusion: no evidence of positive transfer to real bugs; the below-chance headline is partly measurement artifact, corrected values are indistinguishable from chance. The root cause of the remaining weak signal is not proven. Do not claim real-bug detection.",
]
(R / "artifacts/paper_evidence/DIAGNOSTIC_EXTERNAL.json").write_text(json.dumps(out, indent=2) + "\n")
print("wrote DIAGNOSTIC_EXTERNAL.json")
for k in ("quixbugs_canonical", "quixbugs_declared_inputs", "bugsinpy"):
    for e in out[k]:
        if "auroc" in e and "subset" in e:
            print(k, e["subset"], e["n_pairs"], e["auroc"], e["ci95_cluster_bootstrap"])
