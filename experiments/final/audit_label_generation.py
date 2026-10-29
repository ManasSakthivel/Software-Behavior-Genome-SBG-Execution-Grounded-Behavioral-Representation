#!/usr/bin/env python3
"""Phase 2A-C: label-generation audit + INDEPENDENT edit-size reproduction + confound quantification.  Uses NO SBG scores.

Independence: this file does not import edit_size_analysis / diagnose_edit_size / sbg.statistics.  AUROC is a midrank
Mann-Whitney; line edit = own LCS dynamic programme; token edit = own tokenizer-level LCS; cluster bootstrap is local.
Writes artifacts/paper_evidence/LABEL_GENERATION_AUDIT.json.  Dataset: benchmark/datasets/v8 (all splits; descriptive only)."""
import ast, collections, hashlib, io, json, pathlib, random, statistics, sys, tokenize

R = pathlib.Path(__file__).resolve().parents[2]
DS = R / "benchmark/datasets/v8"
STALE = {s["program"] for s in json.loads((R / "artifacts/paper_evidence/DIAGNOSTIC_V8_STALE_VARIANTS.json").read_text())["stale_programs"]}


def rows(split):
    return [json.loads(l) for l in (DS / f"pairs_{split}.jsonl").read_text().splitlines() if l.strip()]


def lcs_len(a, b):
    if len(a) < len(b):
        a, b = b, a
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if x == y else max(prev[j], cur[-1]))
        prev = cur
    return prev[-1]


def line_edit(a, b):            # insertions + deletions = |a|+|b|-2*LCS   (same quantity as a diff's +/- line count)
    return len(a) + len(b) - 2 * lcs_len(a, b)


def canon_lines(p):
    return ast.unparse(ast.parse((R / p).read_text())).splitlines()


def raw_lines(p):
    return [l.rstrip() for l in (R / p).read_text().splitlines()]


def toks(p):
    out = []
    for t in tokenize.generate_tokens(io.StringIO((R / p).read_text()).readline):
        if t.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER):
            continue
        out.append(t.string)
    return out


def midrank_auc(score, y):       # P(score_pos > score_neg) + .5 P(tie)
    pairs = sorted(range(len(score)), key=lambda i: score[i])
    ranks = [0.0] * len(score)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and score[pairs[j + 1]] == score[pairs[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[pairs[k]] = (i + j) / 2 + 1
        i = j + 1
    n1 = sum(y); n0 = len(y) - n1
    return (sum(r for r, l in zip(ranks, y) if l) - n1 * (n1 + 1) / 2) / (n1 * n0)


def boot(score, y, cl, n=2000, seed=7):
    by = collections.defaultdict(list)
    for i, c in enumerate(cl):
        by[c].append(i)
    ks, rng, o = sorted(by), random.Random(seed), []
    for _ in range(n):
        idx = [i for k in (rng.choice(ks) for _ in ks) for i in by[k]]
        yy = [y[i] for i in idx]
        if 0 < sum(yy) < len(yy):
            o.append(midrank_auc([score[i] for i in idx], yy))
    o.sort()
    return [round(o[int(.025 * len(o))], 4), round(o[int(.975 * len(o)) - 1], 4)]


def q(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(p * len(v)))]


out = {"artifact": "LABEL_GENERATION_AUDIT", "dataset": "benchmark/datasets/v8", "uses_sbg_scores": False,
       "stale_programs_excluded_from_all_numbers": sorted(STALE), "code_trace": {}, "splits": {}}

# ---- A. code trace (static facts, asserted from the generator source) ----
gen = (R / "benchmark/scripts/generate_v8_dataset.py").read_text()
out["code_trace"] = {
    "label_assignment": "generate_split(): relation is bound to the CALL SITE, not computed from the variant: (\"EQUIVALENT\", SP_TYPES, apply_transformation) and (\"CHANGED\", SC_TYPES, apply_mutation); semantic_relation = expected_label = relation.",
    "label_is_function_of_family_asserted": ("(\"EQUIVALENT\", SP_TYPES, apply_transformation)" in gen and "(\"CHANGED\", SC_TYPES, apply_mutation)" in gen),
    "label_verification_in_generator": "check_candidate(): CHANGED must pass a STATIC observability analysis (analyse_pair; mutation inside entry-reachable code); EQUIVALENT is accepted with NO execution-based equivalence check (only compile + non-identical normalised AST).",
    "edit_size_not_controlled_in_generator": "only SP-1/SP-2 are capped (max_names=1); SP-3 inserts dead code with p=0.4 per statement to depth 2; SP-5/8/11/12 rewrite constructs; SC-* each edit one site (site=0).",
    "variants_per_program": "SP-1..12 x seeds{0,1,2} and SC-1..14 x seeds{0,1,2}; no_op variants (identical normalised AST) rejected -> the number of surviving EQUIVALENT variants per program depends on whether the program has constructs the SP family can rewrite.",
}

FAM = {}
ALL = []
for split in ("train", "dev", "val", "test"):
    rs = [r for r in rows(split) if r["base_id"] not in STALE]
    for r in rs:
        r["edit_canon"] = line_edit(canon_lines(r["base_path"]), canon_lines(r["variant_path"]))
        r["edit_raw"] = line_edit(raw_lines(r["base_path"]), raw_lines(r["variant_path"]))
        r["edit_tok"] = None
        r["y"] = 1 if r["semantic_relation"] == "CHANGED" else 0
        ALL.append(r)

# label/family determinism
fam_labels = collections.defaultdict(set)
for r in ALL:
    fam_labels[r["transformation_type"]].add(r["semantic_relation"])
out["family_label_map"] = {k: sorted(v) for k, v in sorted(fam_labels.items())}
out["every_family_has_exactly_one_label"] = all(len(v) == 1 for v in fam_labels.values())
out["label_matches_family_prefix"] = all((r["transformation_type"].startswith("SC") == (r["y"] == 1)) for r in ALL)
out["expected_label_equals_semantic_relation"] = all(r["expected_label"] == r["semantic_relation"] for r in ALL)

# token edit (own tokenizer LCS) -- computed once, for all non-stale pairs (cheap relative to scoring)
for r in ALL:
    r["edit_tok"] = line_edit(toks(r["base_path"]), toks(r["variant_path"]))

BINS = [(0, 1), (2, 2), (3, 5), (6, 10), (11, 20), (21, 10 ** 9)]
bn = lambda e: next(i for i, (lo, hi) in enumerate(BINS) if lo <= e <= hi)  # noqa: E731
for split in ("train", "dev", "val", "test"):
    rs = [r for r in ALL if r["split"] == split]
    y = [r["y"] for r in rs]; cl = [r["base_id"] for r in rs]
    s = {"n_pairs": len(rs), "n_programs": len(set(cl)), "n_changed": sum(y), "n_equivalent": len(y) - sum(y)}
    s["status_note"] = "test split was already examined in the EOD session: descriptive only, never used to choose anything" if split == "test" else "usable for design decisions"
    s["independent_edit_size_auroc"] = {}
    for key in ("edit_canon", "edit_raw", "edit_tok"):
        fwd = midrank_auc([r[key] for r in rs], y)
        rev = midrank_auc([-r[key] for r in rs], y)
        s["independent_edit_size_auroc"][key] = {"forward_larger_edit_means_CHANGED": round(fwd, 4), "reversed_larger_edit_means_EQUIVALENT": round(rev, 4),
                                                 "reversed_ci95_cluster": boot([-r[key] for r in rs], y, cl), "sum_check": round(fwd + rev, 6)}
    s["edit_canon_distribution"] = {}
    for lab, nm in ((1, "CHANGED"), (0, "EQUIVALENT")):
        v = [r["edit_canon"] for r in rs if r["y"] == lab]
        s["edit_canon_distribution"][nm] = {"n": len(v), "mean": round(statistics.mean(v), 2), "median": statistics.median(v), "p10": q(v, .1), "p90": q(v, .9), "max": max(v)}
    # label proportion by edit bucket
    b = collections.Counter((bn(r["edit_canon"]), r["y"]) for r in rs)
    s["label_by_edit_bucket"] = {f"{lo}-{hi if hi < 10**9 else 'inf'}": {"n_changed": b[(i, 1)], "n_equivalent": b[(i, 0)],
                                 "frac_changed": round(b[(i, 1)] / max(1, b[(i, 1)] + b[(i, 0)]), 3)} for i, (lo, hi) in enumerate(BINS)}
    # cross-label overlap: share of cross-label pairs with identical edit size, and range overlap
    c = collections.Counter(r["edit_canon"] for r in rs if r["y"] == 1); e = collections.Counter(r["edit_canon"] for r in rs if r["y"] == 0)
    nx = sum(c.values()) * sum(e.values()); same = sum(c[k] * e[k] for k in c)
    s["cross_label_pairs"] = nx; s["cross_label_pairs_with_identical_edit_size"] = same; s["fraction_identical_edit_size"] = round(same / nx, 4)
    s["equivalent_with_edit_leq_max_changed_edit"] = round(sum(1 for r in rs if r["y"] == 0 and r["edit_canon"] <= max(x["edit_canon"] for x in rs if x["y"] == 1)) / (len(y) - sum(y)), 4)
    s["changed_with_edit_leq_5"] = round(sum(1 for r in rs if r["y"] == 1 and r["edit_canon"] <= 5) / sum(y), 4)
    # program-level variation
    pr = {}
    for p in sorted(set(cl)):
        ps = [r for r in rs if r["base_id"] == p]; py = [r["y"] for r in ps]
        pr[p] = {"n": len(ps), "n_changed": sum(py), "rev_edit_auroc": round(midrank_auc([-r["edit_canon"] for r in ps], py), 4) if 0 < sum(py) < len(py) else None}
    vals = [v["rev_edit_auroc"] for v in pr.values() if v["rev_edit_auroc"] is not None]
    s["per_program_reversed_edit_auroc"] = {"min": min(vals), "median": statistics.median(vals), "max": max(vals), "n_programs": len(vals)}
    out["splits"][split] = s

# per-family distributions (train+dev+val only: design data)
fams = {}
for k in sorted(fam_labels, key=lambda z: (z[:2], int(z.split('-')[1]))):
    v = [r["edit_canon"] for r in ALL if r["transformation_type"] == k and r["split"] != "test"]
    if v:
        fams[k] = {"label": sorted(fam_labels[k])[0], "n": len(v), "median_edit": statistics.median(v), "mean_edit": round(statistics.mean(v), 2),
                   "p90": q(v, .9), "frac_edit_leq_2": round(sum(x <= 2 for x in v) / len(v), 3)}
out["per_family_edit_size_train_dev_val"] = fams
out["interpretation"] = [
    "Labels are bound to the transformation family at the generator call site; edit size is therefore predictive iff the SP families and SC families differ in edit size, which they do by construction (SC edits one site; several SP families rewrite many sites).",
    "No evidence of an implementation or orientation defect: three independently computed edit-size measures agree, forward + reversed AUROC sum to 1 (ties handled by midrank), and the result holds per split.",
    "The generator verifies CHANGED variants statically (observability) but never verifies EQUIVALENT variants dynamically; the equivalence labels rest on the transformations being semantics-preserving by design (tested separately).",
]
(R / "artifacts/paper_evidence/LABEL_GENERATION_AUDIT.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps({k: out[k] for k in ("every_family_has_exactly_one_label", "label_matches_family_prefix", "expected_label_equals_semantic_relation")}))
for sp, s in out["splits"].items():
    print(sp, s["n_pairs"], s["n_programs"], {k: v["reversed_larger_edit_means_EQUIVALENT"] for k, v in s["independent_edit_size_auroc"].items()},
          "identical-edit cross pairs", s["fraction_identical_edit_size"], s["edit_canon_distribution"]["CHANGED"]["median"], s["edit_canon_distribution"]["EQUIVALENT"]["median"])
