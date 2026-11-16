#!/usr/bin/env python3
"""EXP-A3-004: pair duplication / near-duplication audit of V10-test and V9c (train/dev/val).  Pure stdlib (a3lib only).

Checks: identical pair_id; identical (base_path, variant_path); identical variant source hash (within / across designs & splits);
variant identical to base (raw hash, normalised AST); CHANGED variant identical to an EQUIVALENT variant (same program / any program);
matched-set bijection (EQ partner reuse); near-duplicate variants (token-multiset similarity >= 0.98) incl. across labels;
normalised-AST duplicates among CHANGED vs EQUIVALENT of the primary populations.
  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python exp_a3_004_duplication.py
"""
import ast
import collections
import hashlib
import itertools
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import a3lib as L  # noqa: E402

RAW = L.PKG / "results" / "raw" / "EXP-A3-004"
RAW.mkdir(parents=True, exist_ok=True)
TAB = L.PKG / "results" / "tables"


def h(path):
    return hashlib.sha256((L.REPO / path).read_bytes()).hexdigest()


def ast_norm_hash(path):
    """hash of ast.dump (no attributes) -> identical iff same parse tree incl. identifiers"""
    return hashlib.sha256(ast.dump(ast.parse((L.REPO / path).read_text())).encode()).hexdigest()


_ms_cache = {}


def ms(path):
    if path not in _ms_cache:
        _ms_cache[path] = L.token_multiset((L.REPO / path).read_text())
    return _ms_cache[path]


def sim(a, b):
    return 1.0 - L.ms_distance(ms(a), ms(b))


def design_rows(name):
    if name == "v10_test":
        meta = L.jl(L.V10D / "pairs_test.jsonl")
        prim = {r["pair_id"] for r in L.build_v10(with_static=False)[1]}
    else:
        split = name.split("_")[1]
        m9 = L.jl(L.V9D / f"pairs_{split}.jsonl")
        v8 = {m["pair_id"]: m for m in L.jl(L.V8D / f"pairs_{split}.jsonl")}
        wanted = {m["matched_equivalent_pair_id"] for m in m9}
        meta = m9 + [v8[w] for w in sorted(wanted)]
        prim = {r["pair_id"] for r in L.build_v9c(split)[1]}
    for m in meta:
        m["_primary"] = m["pair_id"] in prim
        m["_label"] = int(m["semantic_relation"] == "CHANGED")
    return meta


def main():
    out = {}
    global_hash = collections.defaultdict(list)   # source hash -> [(design, pair_id, label, variant_path)]
    all_meta = {}
    for name in ("v10_test", "v9c_train", "v9c_dev", "v9c_val"):
        meta = design_rows(name)
        all_meta[name] = meta
        stale = L.stale_programs()
        if name != "v10_test":
            meta = [m for m in meta if m["base_id"] not in stale]
            all_meta[name] = meta
        r = {"n_rows": len(meta), "n_primary": sum(m["_primary"] for m in meta)}
        r["dup_pair_id"] = len(meta) - len({m["pair_id"] for m in meta})
        r["dup_base_variant_path"] = len(meta) - len({(m["base_path"], m["variant_path"]) for m in meta})
        hv = {m["pair_id"]: h(m["variant_path"]) for m in meta}
        hb = {m["pair_id"]: h(m["base_path"]) for m in meta}
        av = {m["pair_id"]: ast_norm_hash(m["variant_path"]) for m in meta}
        ab = {m["pair_id"]: ast_norm_hash(m["base_path"]) for m in meta}
        for m in meta:
            global_hash[hv[m["pair_id"]]].append((name, m["pair_id"], m["_label"], m["variant_path"], m["base_id"]))
        byh = collections.defaultdict(list)
        for m in meta:
            byh[hv[m["pair_id"]]].append(m)
        dups = {k: v for k, v in byh.items() if len(v) > 1}
        r["variant_hash_groups_with_>1_pair"] = len(dups)
        r["variant_rows_in_dup_groups"] = sum(len(v) for v in dups.values())
        r["dup_groups_mixed_label"] = sum(1 for v in dups.values() if len({m["_label"] for m in v}) > 1)
        r["dup_groups_examples"] = [[(m["pair_id"], m["_label"]) for m in v] for v in list(dups.values())[:8]]
        r["variant_file_identical_to_base_bytes"] = [m["pair_id"] for m in meta if hv[m["pair_id"]] == hb[m["pair_id"]]]
        r["variant_ast_identical_to_base"] = [(m["pair_id"], m["_label"]) for m in meta if av[m["pair_id"]] == ab[m["pair_id"]]]
        # same normalised AST among variants of the same program, across labels
        byprog = collections.defaultdict(list)
        for m in meta:
            byprog[m["base_id"]].append(m)
        cross_label_ast_dups = []
        within_label_ast_dups = collections.Counter()
        for prog, ms_ in byprog.items():
            byast = collections.defaultdict(list)
            for m in ms_:
                byast[av[m["pair_id"]]].append(m)
            for v in byast.values():
                if len(v) > 1:
                    labs = {m["_label"] for m in v}
                    if len(labs) > 1:
                        cross_label_ast_dups.append([(m["pair_id"], m["_label"]) for m in v])
                    else:
                        within_label_ast_dups[labs.pop()] += len(v)
        r["same_program_identical_AST_across_labels"] = cross_label_ast_dups
        r["same_program_identical_AST_within_label_rows"] = dict(within_label_ast_dups)
        # matched-set structure
        if name == "v10_test":
            eqs = {m["pair_id"]: m for m in meta if m["_label"] == 0}
            chs = {m["pair_id"]: m for m in meta if m["_label"] == 1}
            cnt = collections.Counter(m["matched_pair_id"] for m in chs.values())
            r["matched_set_structure"] = {"n_eq": len(eqs), "n_ch": len(chs), "ch_per_eq_max": max(cnt.values()), "eq_without_ch": len(set(eqs) - set(cnt)),
                                          "ch_pointing_to_missing_eq": len([c for c in cnt if c not in eqs]),
                                          "reciprocal_ok": all(eqs[c["matched_pair_id"]]["matched_pair_id"] == c["pair_id"] for c in chs.values() if c["matched_pair_id"] in eqs)}
        else:
            eqs = {m["pair_id"]: m for m in meta if m["_label"] == 0}
            chs = [m for m in meta if m["_label"] == 1]
            cnt = collections.Counter(m["matched_equivalent_pair_id"] for m in chs)
            r["matched_set_structure"] = {"n_eq": len(eqs), "n_ch": len(chs), "ch_per_eq_max": max(cnt.values()), "eq_reused_by_multiple_ch": sum(1 for c in cnt.values() if c > 1),
                                          "eq_without_ch": len(set(eqs) - set(cnt)), "ch_pointing_to_missing_eq": len([c for c in cnt if c not in eqs])}
            # the EQUIVALENT variant file of the set vs the CHANGED variant: sc+sp composition => structural closeness
        # per matched set: similarity of EQ vs CH variants (tokens); and CH variant vs base
        sims, sims_ch_base, sims_eq_base = [], [], []
        for m in meta:
            if m["_label"] == 1 and m["_primary"]:
                eqid = m["matched_pair_id"] if name == "v10_test" else m["matched_equivalent_pair_id"]
                e = next((x for x in meta if x["pair_id"] == eqid), None)
                if e is None:
                    continue
                sims.append(sim(m["variant_path"], e["variant_path"]))
                sims_ch_base.append(sim(m["variant_path"], m["base_path"]))
                sims_eq_base.append(sim(e["variant_path"], e["base_path"]))
        r["token_similarity_CH_vs_its_EQ_partner"] = {"mean": sum(sims) / len(sims), "min": min(sims), "max": max(sims), "n": len(sims)}
        r["token_similarity_CH_vs_base"] = {"mean": sum(sims_ch_base) / len(sims_ch_base), "max": max(sims_ch_base)}
        r["token_similarity_EQ_vs_base"] = {"mean": sum(sims_eq_base) / len(sims_eq_base), "max": max(sims_eq_base)}
        # near duplicates (>=0.98) among variants of the same program (primary pairs), by label combination
        near = collections.Counter()
        near_examples = []
        for prog, ms_ in byprog.items():
            pm = [m for m in ms_ if m["_primary"]]
            for a, b in itertools.combinations(pm, 2):
                if sim(a["variant_path"], b["variant_path"]) >= 0.98:
                    near[(a["_label"], b["_label"]) if a["_label"] <= b["_label"] else (b["_label"], a["_label"])] += 1
                    if len(near_examples) < 8:
                        near_examples.append((a["pair_id"], b["pair_id"]))
        r["near_duplicate_variant_pairs_sim>=0.98_same_program_primary"] = {f"{k[0]}-{k[1]}": v for k, v in near.items()}
        r["near_duplicate_examples"] = near_examples
        out[name] = r
    # ---- cross design/split hash reuse
    cross = []
    for k, v in global_hash.items():
        ds = {x[0] for x in v}
        if len(ds) > 1:
            cross.append([x for x in v])
    out["cross_design_variant_hash_reuse_groups"] = len(cross)
    out["cross_design_variant_hash_reuse_examples"] = cross[:10]
    # base-program source hash reuse under different base_id/path across splits
    bh = collections.defaultdict(set)
    for name, meta in all_meta.items():
        for m in meta:
            bh[h(m["base_path"])].add((name, m["base_id"]))
    out["base_source_hash_shared_between_designs_or_ids"] = [sorted(v) for v in bh.values() if len({d for d, _ in v}) > 1 or len({b for _, b in v}) > 1][:20]
    # corpus-wide base program duplicates (all fresh programs)
    fh = collections.defaultdict(list)
    for p in sorted((L.REPO / "benchmark/corpus/fresh_programs").glob("*.py")):
        fh[hashlib.sha256(p.read_bytes()).hexdigest()].append(p.name)
    out["fresh_corpus_byte_identical_program_groups"] = [v for v in fh.values() if len(v) > 1]
    (RAW / "duplication_audit.json").write_text(json.dumps(out, indent=1, default=str))
    import csv
    with open(TAB / "EXP-A3-004_duplication_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["design", "rows", "primary", "dup_pair_id", "dup_(base,variant)_path", "variant_hash_groups>1", "rows_in_dup_groups", "dup_groups_mixed_label",
                    "variant_bytes==base", "variant_AST==base", "same_prog_AST_dup_across_labels", "near_dup>=0.98 (EQ-EQ/CH-CH/EQ-CH)", "sim(CH,EQ partner) mean/max", "ch_per_eq_max"])
        for n in ("v10_test", "v9c_train", "v9c_dev", "v9c_val"):
            r = out[n]
            nd = r["near_duplicate_variant_pairs_sim>=0.98_same_program_primary"]
            w.writerow([n, r["n_rows"], r["n_primary"], r["dup_pair_id"], r["dup_base_variant_path"], r["variant_hash_groups_with_>1_pair"], r["variant_rows_in_dup_groups"],
                        r["dup_groups_mixed_label"], len(r["variant_file_identical_to_base_bytes"]), len(r["variant_ast_identical_to_base"]),
                        len(r["same_program_identical_AST_across_labels"]), f"{nd.get('0-0', 0)}/{nd.get('1-1', 0)}/{nd.get('0-1', 0)}",
                        f"{r['token_similarity_CH_vs_its_EQ_partner']['mean']:.3f}/{r['token_similarity_CH_vs_its_EQ_partner']['max']:.3f}", r["matched_set_structure"]["ch_per_eq_max"]])
    for n in ("v10_test", "v9c_train", "v9c_dev", "v9c_val"):
        r = out[n]
        print(n, {k: (v if not isinstance(v, (list, dict)) or len(str(v)) < 200 else str(v)[:200]) for k, v in r.items() if k not in ("dup_groups_examples", "near_duplicate_examples")})
    print("cross-design reuse groups", out["cross_design_variant_hash_reuse_groups"], "base hash shared", len(out["base_source_hash_shared_between_designs_or_ids"]), "fresh identical groups", out["fresh_corpus_byte_identical_program_groups"])


if __name__ == "__main__":
    main()
