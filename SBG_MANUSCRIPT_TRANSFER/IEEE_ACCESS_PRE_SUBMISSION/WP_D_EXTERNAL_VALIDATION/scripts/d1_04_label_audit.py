#!/usr/bin/env python3
"""WP-D / D1 step 4 -- aggregate the executed label oracle (d1_03) into the label-reliability / compatibility tables.

Reads  raw/WPD-D1_compat/data/label_oracle_pairs.csv, label_oracle_file_records.json, confound_pairs.csv
Writes raw/WPD-D1_compat/data/label_audit_summary.json, label_audit_invalid_negatives.csv,
       label_audit_positives.csv, label_consistent_subset_summary.json

EXPLORATORY by construction: the 'label-consistent subset' filters PAIRS by the SBG task definition (oracle on the 11
protocol inputs).  It never looks at an SBG score, never fits anything and is reported alongside the unfiltered numbers.
"""
import collections
import csv
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve()
WP = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
from d1_stats import auroc, summarize  # noqa: E402

DATA = WP / "raw" / "WPD-D1_compat" / "data"


def rd(name):
    return list(csv.DictReader(open(DATA / name)))


def num(x):
    return None if x in ("", None) else float(x)


ora = rd("label_oracle_pairs.csv")
conf = {r["pair_id"]: r for r in rd("confound_pairs.csv") if r["regime"] == "canonical"}
files = json.loads((DATA / "label_oracle_file_records.json").read_text())

out = {"method": "d1_03_label_oracle.py: V10-style oracle (value|exception type|args-after-call|stdout per input) of the "
                 "structurally selected entry on SBG's 11 protocol inputs, 1.0 s/input, single run, on sha256-verified copies",
       "tables": {}}


def cmp_rows(corpus, regime, label=None):
    R = [r for r in ora if r["corpus"] == corpus and r["regime"] == regime]
    if label is not None:
        R = [r for r in R if r["label"] == str(label)]
    return R


def status_counts(R):
    return dict(collections.Counter(("comparable" if r["oracle_changed"] != "" else
                                     f"not_comparable:{r['base_status'] or 'NA'}/{r['variant_status'] or 'NA'}") for r in R))


# ---------------------------------------------------------------- positives (real bugs)
pos_rows = []
for corpus, regime in (("bugsinpy", "canonical"), ("quixbugs", "canonical"), ("quixbugs", "declared")):
    P = cmp_rows(corpus, regime, 1)
    comp = [r for r in P if r["oracle_changed"] != ""]
    ch = [r for r in comp if r["oracle_changed"] == "1"]
    block = {"n_positive_pairs_in_manifest": len(P), "status_counts": status_counts(P),
             "n_comparable": len(comp), "n_oracle_CHANGED": len(ch), "n_oracle_UNCHANGED": len(comp) - len(ch),
             "fraction_CHANGED_of_comparable": round(len(ch) / len(comp), 4) if comp else None,
             "n_differ_distribution_(inputs_differing_of_n)": dict(sorted(collections.Counter(int(r["n_differ"]) for r in comp).items()))}
    if corpus == "bugsinpy":
        ev = [r for r in comp if conf.get(r["pair_id"], {}).get("evaluated_v8") == "True"]
        block["restricted_to_v8_evaluated_pairs"] = {
            "n": len(ev), "n_CHANGED": sum(1 for r in ev if r["oracle_changed"] == "1")}
        block["unit_kind_of_comparable"] = dict(collections.Counter(r["unit_kind"] for r in comp))
        block["CHANGED_by_unit_kind"] = dict(collections.Counter(r["unit_kind"] for r in ch))
    if corpus == "quixbugs" and regime == "canonical":
        block["base_programs_with_>=10_of_11_inputs_raising"] = sum(
            1 for r in comp if r["base_n_exc_inputs"] not in ("", None) and int(r["base_n_exc_inputs"]) >= 10)
        block["base_exception_inputs_distribution"] = dict(sorted(collections.Counter(
            int(r["base_n_exc_inputs"]) for r in comp).items()))
        block["base_exception_types"] = dict(collections.Counter(
            t for r in comp for t in (r.get("base_n_exc_types") or "").split(";") if t))
    out["tables"][f"positives/{corpus}/{regime}"] = block
    for r in P:
        pos_rows.append({k: r.get(k) for k in ("corpus", "regime", "pair_id", "cluster", "unit_kind", "base_status",
                                               "variant_status", "base_entry", "variant_entry", "n_inputs", "n_differ",
                                               "oracle_changed", "n_differ_value_or_exc", "n_differ_args",
                                               "n_differ_stdout", "base_n_exc_inputs", "oracle_note")})
with open(DATA / "label_audit_positives.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(pos_rows[0].keys()))
    w.writeheader()
    w.writerows(pos_rows)

# ---------------------------------------------------------------- negatives (SP variants of the FIXED program)
inv_rows = []
for corpus, regime in (("bugsinpy", "canonical"), ("quixbugs", "canonical"), ("quixbugs", "declared")):
    N = cmp_rows(corpus, regime, 0)
    comp = [r for r in N if r["oracle_changed"] != ""]
    ch = [r for r in comp if r["oracle_changed"] == "1"]
    by_t = collections.defaultdict(lambda: [0, 0])
    for r in comp:
        by_t[r["transformation"]][0] += 1
        by_t[r["transformation"]][1] += int(r["oracle_changed"])
    out["tables"][f"negatives/{corpus}/{regime}"] = {
        "n_negative_pairs_in_manifest": len(N), "status_counts": status_counts(N),
        "n_comparable": len(comp), "n_oracle_CHANGED_(invalid_negative)": len(ch),
        "by_transformation_[n_comparable,n_oracle_CHANGED]": {k: v for k, v in sorted(by_t.items())}}
    for r in ch:
        # first differing input details
        inv_rows.append({"corpus": corpus, "regime": regime, "pair_id": r["pair_id"], "transformation": r["transformation"],
                         "n_differ_of_inputs": f"{r['n_differ']}/{r['n_inputs']}",
                         "differ_value_or_exc": r["n_differ_value_or_exc"], "differ_args": r["n_differ_args"],
                         "differ_stdout": r["n_differ_stdout"], "base_entry": r["base_entry"],
                         "variant_entry": r["variant_entry"], "oracle_note": r["oracle_note"]})
with open(DATA / "label_audit_invalid_negatives.csv", "w", newline="") as f:
    if inv_rows:
        w = csv.DictWriter(f, fieldnames=list(inv_rows[0].keys()))
        w.writeheader()
        w.writerows(inv_rows)

# detail: which exceptions do invalid negatives raise (NameError after rename?)
canon_files = {}
for k, v in files.items():
    if k.startswith("canon__") and v.get("file"):
        canon_files[v["file"].split("/unit_copies/")[-1]] = v
detail = []
for r in inv_rows:
    if r["regime"] != "canonical":
        continue
    crow = next(x for x in ora if x["pair_id"] == r["pair_id"] and x["regime"] == "canonical")
    pc = conf[r["pair_id"]]
    vrec = canon_files.get(pc["variant_path"])
    brec = canon_files.get(pc["base_path"])
    first = None
    for i, (a, b) in enumerate(zip(brec["obs"], vrec["obs"])):
        if a != b:
            first = {"input_index": i, "base_obs": a[:2], "variant_obs": b[:2]}
            break
    detail.append({"pair_id": r["pair_id"], "transformation": r["transformation"], "first_differing_input": first})
out["invalid_negative_first_difference"] = detail
exc_types = collections.Counter()
for d in detail:
    if d["first_differing_input"]:
        exc_types[(d["transformation"], d["first_differing_input"]["variant_obs"][0],
                   d["first_differing_input"]["variant_obs"][1][:40])] += 1
out["invalid_negative_first_difference_summary"] = {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in exc_types.items()}

# ---------------------------------------------------------------- the label oracle vs committed 'observable' static flag
bp = [r for r in ora if r["corpus"] == "bugsinpy" and r["label"] == "1"]
import csv as _c  # noqa
flag = {}
for r in _c.DictReader(open(DATA / "bugsinpy_pair_ledger.csv")):
    if r["role"] == "positive":
        flag[r["pair_id"]] = r["observable_static_flag"]
out["bugsinpy_static_observable_flag_vs_oracle"] = {f"{k[0]}|{k[1]}": v for k, v in collections.Counter(
    (flag.get(r["pair_id"]), "oracle_CHANGED" if r["oracle_changed"] == "1" else
     ("oracle_UNCHANGED" if r["oracle_changed"] == "0" else "not_comparable")) for r in bp).items()}

(DATA / "label_audit_summary.json").write_text(json.dumps(out, indent=1) + "\n")

# ---------------------------------------------------------------- label-consistent subset (EXPLORATORY)
sub_out = {"status": "EXPLORATORY post-hoc label audit view; pairs filtered by the SBG label definition via the oracle, never by SBG score; "
                     "no tuning; unfiltered numbers are in confound_summary.json",
           "definition": "keep positive iff oracle_CHANGED; keep negative iff oracle_UNCHANGED; both must be comparable; "
                         "pairs must be in the v8 evaluated set (BugsInPy 147 / QuixBugs 151)"}
for corpus_key, corpus in (("bugsinpy", "bugsinpy"), ("quixbugs", "quixbugs_canonical")):
    rows = []
    for r in ora:
        if r["corpus"] != corpus_key or r["regime"] != "canonical" or r["oracle_changed"] == "":
            continue
        c = conf[r["pair_id"]]
        if c["evaluated_v8"] != "True":
            continue
        want = (r["label"] == "1" and r["oracle_changed"] == "1") or (r["label"] == "0" and r["oracle_changed"] == "0")
        rows.append({"pair_id": r["pair_id"], "cluster": r["cluster"], "label": int(r["label"]),
                     "transformation": r["transformation"], "consistent": want,
                     "sbg_v5_v8": num(c["sbg_v5_v8"]), "static_token": num(c["static_token"]),
                     "static_ast": num(c["static_ast"]), "norm_line_edit": num(c["norm_line_edit"])})
    keep = [r for r in rows if r["consistent"]]
    block = {"n_v8_evaluated_comparable": len(rows), "n_kept": len(keep),
             "kept_pos": sum(r["label"] for r in keep), "kept_neg": sum(1 - r["label"] for r in keep),
             "dropped_pos_unobservable": sum(1 for r in rows if r["label"] == 1 and not r["consistent"]),
             "dropped_neg_invalid": sum(1 for r in rows if r["label"] == 0 and not r["consistent"])}
    if keep and 0 < block["kept_pos"] < len(keep):
        for f in ("sbg_v5_v8", "static_token", "static_ast", "norm_line_edit"):
            block[f] = summarize(keep, f)
        # also excluding SP-2
        k2 = [r for r in keep if r["transformation"] != "SP-2"]
        if k2 and 0 < sum(r["label"] for r in k2) < len(k2):
            block["excl_SP2"] = {f: summarize(k2, f) for f in ("sbg_v5_v8", "static_token", "static_ast", "norm_line_edit")}
            block["excl_SP2"]["n"] = len(k2)
    sub_out[corpus] = block
    # SBG v5 on the full v8 evaluated pairs restricted to *positives that are oracle CHANGED* only: detection profile
    pos_ch = [r for r in rows if r["label"] == 1 and r["consistent"]]
    sub_out[corpus]["oracle_CHANGED_positives_sbg_v5_exact_zero"] = sum(1 for r in pos_ch if r["sbg_v5_v8"] == 0)
    sub_out[corpus]["oracle_CHANGED_positives_n"] = len(pos_ch)
    pos_un = [r for r in rows if r["label"] == 1 and not r["consistent"]]
    sub_out[corpus]["oracle_UNCHANGED_positives_sbg_v5_exact_zero"] = sum(1 for r in pos_un if r["sbg_v5_v8"] == 0)
    sub_out[corpus]["oracle_UNCHANGED_positives_n"] = len(pos_un)
(DATA / "label_consistent_subset_summary.json").write_text(json.dumps(sub_out, indent=1) + "\n")

print(json.dumps({k: v for k, v in out["tables"].items()}, indent=1))
print(json.dumps(out["invalid_negative_first_difference_summary"], indent=1))
print(json.dumps(out["bugsinpy_static_observable_flag_vs_oracle"], indent=1, default=str))
print(json.dumps(sub_out, indent=1)[:6000])
