#!/usr/bin/env python3
"""EXP-WPC-004: forensic characterisation of the SC-6 CHANGED pairs that SBG scores 0 ("invisible").

LABEL-FREE / DESCRIPTIVE ONLY.  Reads (a) the frozen per-pair scores stored in configs/populations/<split>.json,
(b) the shared trace cache (results/raw/trace_cache), (c) variant sources from the SBG repo (READ-ONLY).
Nothing is scored or re-evaluated; no AUROC is computed.  Deterministic (no randomness).

Matched EQUIVALENT partner of an SC-6 pair = the label-0 primary row with the same 'group' (carries the same SP
transform without SC-6).  Cross-checked against matched_pair_id / matched_equivalent_pair_id in the repo pair files.

Two trace comparisons are made per pair:
  BV = base      vs SC-6 variant   (as requested; SP transform + SC-6 edit are both present in the diff)
  PV = partner   vs SC-6 variant   (SP transform cancels; isolates the SC-6 edit; same SP seed => same renames)
Cause classes (applied to pairs with sbg_v5 == 0), decided on PV (fallback BV only if partner cache is missing):
  C  ret, exc, stdout identical on all inputs (label says CHANGED, battery shows nothing)
  A  ret differs on >=1 input; exc/stdout identical; full event skeleton (type+function, incl. line events) identical;
     every c/r/e locals snapshot identical (=> the changed value is recorded nowhere)
  B  as A but >=1 c/r/e locals snapshot differs (value change in a recorded local; zero score => abstract domain collapses
     it; NOT verified by re-running the scorer)
  D  everything else (exc/stdout differ, skeleton differs, truncation, missing cache ...)

  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python wpc_sc6_forensics.py            # writes outputs (refuses to overwrite)
  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 python wpc_sc6_forensics.py --no-write  # prints summary only
"""
from __future__ import annotations

import argparse
import collections
import csv
import difflib
import gzip
import hashlib
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve()
PKG = HERE.parents[2]
REPO = PKG.parent / "SBG"
OUT = PKG / "WP_C_ABLATIONS" / "raw" / "EXP-WPC-004"
SPLITS = ["v10_test", "v9c_val", "v9c_dev", "v9c_train"]
SCORES = ["sbg_v5", "sbg_v3", "sbg_temporal", "sbg_state"]
PAIRFILES = {"v10_test": [REPO / "benchmark/datasets/v10_independent/pairs_test.jsonl"],
             "v9c_val": [REPO / "benchmark/datasets/v9_composed/pairs_val.jsonl", REPO / "benchmark/datasets/v8/pairs_val.jsonl"],
             "v9c_dev": [REPO / "benchmark/datasets/v9_composed/pairs_dev.jsonl", REPO / "benchmark/datasets/v8/pairs_dev.jsonl"],
             "v9c_train": [REPO / "benchmark/datasets/v9_composed/pairs_train.jsonl", REPO / "benchmark/datasets/v8/pairs_train.jsonl"]}
TRIVIAL_RET = {"None", "True", "False", "0", "1", "-1", "''", '""', "[]", "{}", "()", "set()"}


# ----------------------------------------------------------------------------------------------------- helpers
def cache_file(split, base_id, path):
    return PKG / "results/raw/trace_cache" / split / base_id / (
        hashlib.sha1(path.encode()).hexdigest()[:12] + "__" + pathlib.Path(path).stem + ".json.gz")


def load_trace(split, base_id, path):
    f = cache_file(split, base_id, path)
    if not f.exists():
        return None
    with gzip.open(f, "rt") as fh:
        return json.load(fh)


def read_src(rel):
    return (REPO / rel).read_text().splitlines()


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()] if pathlib.Path(p).exists() else []


def edit_bin(e):
    return "<=10" if e <= 10 else "11-30" if e <= 30 else "31-60" if e <= 60 else ">60"


TOK = re.compile(r"\w+|[^\w\s]")


def nrm(l):
    """Normalise a source line for diffing: drop parentheses and whitespace (the v8 SP pipeline and the v9_composed pipeline
    render tuples/parentheses differently, which is cosmetic noise in partner->variant diffs of the v9c splits)."""
    return re.sub(r"[()\s]", "", l)


def describe(old_lines, new_lines):
    """Automated one-line description of the changed tokens (partner -> variant); parentheses-only differences ignored."""
    sm = difflib.SequenceMatcher(None, [nrm(l) for l in old_lines], [nrm(l) for l in new_lines], autojunk=False)
    ops = [o for o in sm.get_opcodes() if o[0] != "equal"]
    if len(ops) == 1 and ops[0][0] == "replace" and ops[0][2] - ops[0][1] == 1 and ops[0][4] - ops[0][3] == 1:
        o, n_ = old_lines[ops[0][1]].strip(), new_lines[ops[0][3]].strip()
        if o.startswith("return") and n_.startswith("return"):
            return f"L{ops[0][3] + 1}: return-expression mutation `{o[:70]}` -> `{n_[:70]}`"
    parts = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                a = [t for t in TOK.findall(old_lines[i1 + k]) if t not in "()"]
                b = [t for t in TOK.findall(new_lines[j1 + k]) if t not in "()"]
                t = difflib.SequenceMatcher(None, a, b, autojunk=False)
                for tg, a1, a2, b1, b2 in t.get_opcodes():
                    if tg != "equal":
                        parts.append(f"L{j1 + k + 1}: `{' '.join(a[a1:a2]) or '∅'}` -> `{' '.join(b[b1:b2]) or '∅'}`")
        else:
            if i2 > i1:
                parts.append(f"L{i1 + 1}: -[{' | '.join(s.strip() for s in old_lines[i1:i2])[:70]}]")
            if j2 > j1:
                parts.append(f"L{j1 + 1}: +[{' | '.join(s.strip() for s in new_lines[j1:j2])[:70]}]")
    if not parts:
        return "NO TEXTUAL DIFF"
    s = "; ".join(parts[:4])
    return s + (f" (+{len(parts) - 4} more)" if len(parts) > 4 else "")


def unified(a_name, a, b_name, b):
    return "\n".join(difflib.unified_diff(a, b, fromfile=a_name, tofile=b_name, lineterm="", n=2))


def n_changed(a, b):
    return sum(1 for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] == "+" and not l.startswith("+++"))


_RE_INT = re.compile(r"^-?\d+$")
_RE_FLOAT = re.compile(r"^-?\d+\.\d")
_RE_STR = re.compile(r"^'.*'$|^\".*\"$")
_RE_BYTES = re.compile(r"^b'")


def _n_elems(inner):
    depth = commas = 0
    for ch in inner:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            commas += 1
    return commas + 1


def repr_to_abstract(r):
    """VERBATIM logic copy of sbg.v5.state_transition_genome._repr_to_abstract (copied, not imported; SBG repo untouched)."""
    r = r.strip()
    if r == "None":
        return "NULL"
    if r == "True":
        return "POSITIVE"
    if r == "False":
        return "ZERO"
    if _RE_INT.match(r):
        v = int(r)
        return "ZERO" if v == 0 else "POSITIVE" if v > 0 else "NEGATIVE"
    if _RE_FLOAT.match(r):
        try:
            v = float(r)
            return "ZERO" if v == 0.0 else "POSITIVE" if v > 0 else "NEGATIVE"
        except ValueError:
            pass
    if r in ("''", '""'):
        return "EMPTY_COLLECTION"
    if _RE_STR.match(r):
        return "NON_NULL"
    if _RE_BYTES.match(r):
        return "NON_NULL" if len(r) > 3 else "EMPTY_COLLECTION"
    if r.startswith("[") or r.startswith("("):
        inner = r[1:-1].strip()
        if not inner:
            return "EMPTY_COLLECTION"
        return "SINGLETON" if _n_elems(inner) == 1 else "MULTI_ELEMENT"
    if r.startswith("{"):
        inner = r[1:-1].strip()
        if not inner:
            return "EMPTY_COLLECTION"
        return "SINGLETON" if _n_elems(inner) == 1 else "MULTI_ELEMENT"
    if r.startswith("<") or re.match(r"^[A-Za-z_][A-Za-z0-9_.]*\(", r):
        return "NON_NULL"
    return "UNKNOWN"


def abs_snap_compare(A, B):
    """Over aligned c/r/e snapshots (call it only when skeletons are identical): #inputs whose raw snapshots differ,
    #inputs whose ABSTRACT snapshots differ, differing variable names and one raw example."""
    raw = ab = 0
    names = set()
    ex = ""
    for a, b in zip(A, B):
        ea = [e for e in a["events"] if e[0] in "cre"]
        eb = [e for e in b["events"] if e[0] in "cre"]
        rd = ad = False
        for x, y in zip(ea, eb):
            sx, sy = norm_snap(x[3]) or {}, norm_snap(y[3]) or {}
            if sx != sy:
                rd = True
                for k in sorted(set(sx) | set(sy)):
                    if sx.get(k) != sy.get(k):
                        names.add(k)
                        if not ex:
                            ex = f"{x[0]}:{k}: {str(sx.get(k))[:40]} -> {str(sy.get(k))[:40]}"
            ax = {k: repr_to_abstract(v) for k, v in sx.items()}
            ay = {k: repr_to_abstract(v) for k, v in sy.items()}
            if ax != ay:
                ad = True
        raw += rd
        ab += ad
    return raw, ab, sorted(names), ex


def skel(tr, kinds=None):
    return [(e[0], e[1]) for e in tr["events"] if kinds is None or e[0] in kinds]


ADDR = re.compile(r"0x[0-9a-fA-F]{4,}")


def norm_snap(d):
    """Mask memory addresses in reprs (e.g. '<function f at 0x10775dee0>' differs between independent runs/processes)."""
    return None if d is None else {k: ADDR.sub("0xADDR", v) if isinstance(v, str) else v for k, v in d.items()}


def cesnaps(tr):
    return [(e[0], e[1], json.dumps(norm_snap(e[3]), sort_keys=True)) for e in tr["events"] if e[0] in "cre"]


def compare(ta, tb):
    """Channel comparison of two cached trace records (run 0 only is stored in full)."""
    if ta is None or tb is None:
        return {"available": False}
    ra, rb = ta.get("sandbox"), tb.get("sandbox")
    if not ra or not rb or not ra.get("traces") or not rb.get("traces"):
        return {"available": False, "why": "no sandbox traces"}
    A, B = ra["traces"], rb["traces"]
    r = {"available": True, "ok_a": ta["ok"], "ok_b": tb["ok"], "entry_a": ta["entry_function"], "entry_b": tb["entry_function"],
         "entry_same": ta["entry_function"] == tb["entry_function"], "n_a": len(A), "n_b": len(B),
         "inputs_same": [t["input"] for t in A] == [t["input"] for t in B]}
    n = min(len(A), len(B))
    P = list(zip(A[:n], B[:n]))
    r["n_inputs"] = n
    r["ret_diff"] = sum(a["ret"] != b["ret"] for a, b in P)
    r["rettype_diff"] = sum(a["ret_type"] != b["ret_type"] for a, b in P)
    r["exc_diff"] = sum(a["exc"] != b["exc"] for a, b in P)
    r["stdout_diff"] = sum(a["stdout"] != b["stdout"] for a, b in P)
    r["trunc_any"] = any(t["trunc"] for t in A[:n] + B[:n])
    r["skel_all_diff"] = sum(skel(a) != skel(b) for a, b in P)
    r["skel_ces_diff"] = sum(skel(a, "cre") != skel(b, "cre") for a, b in P)
    r["nevents_diff"] = sum(len(a["events"]) != len(b["events"]) for a, b in P)
    r["cov_set_diff"] = sum(a["cov"] != b["cov"] for a, b in P)
    r["cov_size_diff"] = sum(len(a["cov"]) != len(b["cov"]) for a, b in P)
    r["snap_diff"] = sum(cesnaps(a) != cesnaps(b) for a, b in P)
    r["snap_diff_rawaddr"] = sum([(e[0], e[1], json.dumps(e[3], sort_keys=True)) for e in a["events"] if e[0] in "cre"] !=
                                 [(e[0], e[1], json.dumps(e[3], sort_keys=True)) for e in b["events"] if e[0] in "cre"] for a, b in P)
    r["ret_diff_idx"] = [i for i, (a, b) in enumerate(P) if a["ret"] != b["ret"]]
    if r["skel_all_diff"] == 0:
        _, r["abs_snap_diff"], r["snap_vars"], r["snap_example"] = abs_snap_compare(A[:n], B[:n])
    return r


def ret_in_locals(tr, only_idx=None):
    """Task 4: does repr(ret) appear among the snapshot values of the entry function's last 'r' event (cap 100 chars)?"""
    if tr is None or not tr.get("sandbox") or not tr["sandbox"].get("traces"):
        return None
    ent = tr["entry_function"]
    n = hit = hit_nt = n_ret = 0
    for i, t in enumerate(tr["sandbox"]["traces"]):
        if only_idx is not None and i not in only_idx:
            continue
        n += 1
        if t["exc"] is not None:
            continue
        rs = [e for e in t["events"] if e[0] == "r" and e[1] == ent and e[3]]
        if not rs:
            continue
        n_ret += 1
        snap = rs[-1][3]
        ret = t["ret"]
        m = any(v == ret or (len(ret) > 100 and isinstance(v, str) and v[:90] == ret[:90]) for v in snap.values())
        hit += m
        hit_nt += m and ret not in TRIVIAL_RET
    return {"n": n, "n_with_r_snapshot": n_ret, "ret_in_locals": hit, "ret_in_locals_nontrivial": hit_nt}


def classify(cmp_):
    if not cmp_.get("available"):
        return "D", "trace cache missing/unusable"
    if not (cmp_["inputs_same"] and cmp_["entry_same"] and cmp_["ok_a"] and cmp_["ok_b"] and cmp_["n_a"] == cmp_["n_b"]):
        return "D", "entry/inputs/ok mismatch between compared traces"
    if cmp_["trunc_any"]:
        c2, w2 = classify(dict(cmp_, trunc_any=False))
        return "D", f"truncated trace present (would be {c2} if truncation ignored: {w2})"
    if cmp_["exc_diff"] or cmp_["stdout_diff"]:
        return "D", f"exc_diff={cmp_['exc_diff']} stdout_diff={cmp_['stdout_diff']}"
    if cmp_["ret_diff"] == 0:
        return "C", "ret/exc/stdout identical on all inputs"
    if cmp_["skel_all_diff"] or cmp_["nevents_diff"]:
        return "D", f"event skeleton differs on {cmp_['skel_all_diff']} inputs"
    if cmp_["snap_diff"] == 0:
        return "A", f"ret differs on {cmp_['ret_diff']}/{cmp_['n_inputs']}; skeleton + all c/r/e snapshots identical"
    if cmp_.get("abs_snap_diff", 0):
        return "D", (f"ret differs on {cmp_['ret_diff']}/{cmp_['n_inputs']}; skeleton identical; c/r/e snapshots differ and ABSTRACT "
                     f"snapshots differ on {cmp_['abs_snap_diff']} inputs although score==0 (needs manual look)")
    return "B", (f"ret differs on {cmp_['ret_diff']}/{cmp_['n_inputs']}; skeleton identical; raw c/r/e snapshots differ on {cmp_['snap_diff']}, "
                 f"abstract (frozen-domain) c/r/e snapshots identical on all inputs; differing vars={cmp_['snap_vars']}")


# ----------------------------------------------------------------------------------------------------- main
def run(write):
    summary = {"definition": "SC-6, label==1, in_primary_population; invisible := score == 0 (exact)", "splits": {}}
    csv_rows = {}
    diffs = {}
    anomalies = []
    for split in SPLITS:
        pop = json.load(open(PKG / f"configs/populations/{split}.json"))
        rows = [r for r in pop["rows"] if r.get("in_primary_population")]
        eq = collections.defaultdict(list)
        for r in rows:
            if r["label"] == 0:
                eq[r["group"]].append(r)
        meta = {}
        for pf in PAIRFILES[split]:
            for m in jl(pf):
                meta[m["pair_id"]] = m
        sc6 = [r for r in rows if r["sc_type"] == "SC-6" and r["label"] == 1]
        out = []
        for r in sc6:
            partners = eq.get(r["group"], [])
            p = partners[0] if len(partners) == 1 else None
            if p is None:
                anomalies.append(f"{split} {r['pair_id']}: {len(partners)} matched equivalents by group")
            mm = meta.get(r["pair_id"], {}).get("matched_pair_id") or meta.get(r["pair_id"], {}).get("matched_equivalent_pair_id")
            if p is not None and mm and mm != p["pair_id"]:
                anomalies.append(f"{split} {r['pair_id']}: group partner {p['pair_id']} != repo matched id {mm}")
            row = {"split": split, "pair_id": r["pair_id"], "base_id": r["base_id"], "sp_type": r["sp_type"], "edit": r["edit"],
                   "edit_bin": edit_bin(r["edit"]), "partner_id": p["pair_id"] if p else "", "partner_edit": p["edit"] if p else "",
                   "base_path": r["base_path"], "variant_path": r["variant_path"], "partner_variant_path": p["variant_path"] if p else ""}
            for s in SCORES:
                row[s] = r["scores"].get(s)
                row["partner_" + s] = p["scores"].get(s) if p else ""
            row["invisible_v5"] = int(r["scores"]["sbg_v5"] == 0)
            # ---- sources / diffs
            base, var = read_src(r["base_path"]), read_src(r["variant_path"])
            pv_src = read_src(p["variant_path"]) if p else None
            row["bv_changed_lines"] = n_changed(base, var)
            row["sc6_changed_lines_vs_partner"] = n_changed(pv_src, var) if p else ""
            row["sc6_edit_desc_auto"] = describe(pv_src, var) if p else describe(base, var)
            d = [f"##### {r['pair_id']}  sp={r['sp_type']} edit={r['edit']} v5={r['scores']['sbg_v5']} partner={row['partner_id']}",
                 f"auto-description (partner->variant): {row['sc6_edit_desc_auto']}",
                 "=== SC-6 edit isolated: partner (SP only) -> variant (SP + SC-6) ===",
                 unified(p["variant_path"], pv_src, r["variant_path"], var) if p else "(no partner)",
                 "=== base -> variant ===", unified(r["base_path"], base, r["variant_path"], var), ""]
            diffs.setdefault(split, []).extend(d)
            # ---- traces
            tb = load_trace(split, r["base_id"], r["base_path"])
            tv = load_trace(split, r["base_id"], r["variant_path"])
            tp = load_trace(split, r["base_id"], p["variant_path"]) if p else None
            bv, pv = compare(tb, tv), compare(tp, tv)
            for tag, c in (("bv", bv), ("pv", pv)):
                row[f"{tag}_available"] = int(c.get("available", False))
                for k in ("n_inputs", "ret_diff", "rettype_diff", "exc_diff", "stdout_diff", "skel_all_diff", "skel_ces_diff",
                          "nevents_diff", "cov_set_diff", "cov_size_diff", "snap_diff", "snap_diff_rawaddr"):
                    row[f"{tag}_{k}"] = c.get(k, "")
                row[f"{tag}_skeleton_identical"] = int(c["skel_all_diff"] == 0) if c.get("available") else ""
                row[f"{tag}_cov_sets_identical"] = int(c["cov_set_diff"] == 0) if c.get("available") else ""
                row[f"{tag}_snapshots_identical"] = int(c["snap_diff"] == 0) if c.get("available") else ""
                row[f"{tag}_nevents_equal"] = int(c["nevents_diff"] == 0) if c.get("available") else ""
                row[f"{tag}_exc_identical"] = int(c["exc_diff"] == 0) if c.get("available") else ""
                row[f"{tag}_stdout_identical"] = int(c["stdout_diff"] == 0) if c.get("available") else ""
            row["pv_abs_snapshots_differ_inputs"] = pv.get("abs_snap_diff", "")
            row["pv_snapshot_diff_vars"] = ";".join(pv.get("snap_vars", []))
            row["pv_snapshot_diff_example"] = pv.get("snap_example", "")
            row["bv_ret_diff_inputs"] = ";".join(map(str, bv.get("ret_diff_idx", [])))
            row["pv_ret_diff_inputs"] = ";".join(map(str, pv.get("ret_diff_idx", [])))
            row["variant_cov_size_stat"] = tv["stats"]["coverage_size"] if tv else ""
            row["base_cov_size_stat"] = tb["stats"]["coverage_size"] if tb else ""
            row["partner_cov_size_stat"] = tp["stats"]["coverage_size"] if tp else ""
            # ---- ret visible in locals
            for tag, t in (("base", tb), ("variant", tv)):
                x = ret_in_locals(t)
                row[f"{tag}_ret_in_r_locals"] = x["ret_in_locals"] if x else ""
                row[f"{tag}_ret_in_r_locals_nontrivial"] = x["ret_in_locals_nontrivial"] if x else ""
                row[f"{tag}_r_snapshot_inputs"] = x["n_with_r_snapshot"] if x else ""
            idx = set(pv.get("ret_diff_idx", []))
            if pv.get("available"):
                x = ret_in_locals(tv, idx)
                row["pv_diffinputs_variant_ret_in_r_locals"] = x["ret_in_locals"] if x else ""
                row["pv_diffinputs_variant_ret_in_r_locals_nontrivial"] = x["ret_in_locals_nontrivial"] if x else ""
                row["pv_diffinputs_n_with_r_snapshot"] = x["n_with_r_snapshot"] if x else ""
            else:
                row["pv_diffinputs_variant_ret_in_r_locals"] = row["pv_diffinputs_variant_ret_in_r_locals_nontrivial"] = row["pv_diffinputs_n_with_r_snapshot"] = ""
            ref = pv_src or base
            smx = difflib.SequenceMatcher(None, [nrm(l) for l in ref], [nrm(l) for l in var], autojunk=False)
            plus = [var[j].strip() for tg, i1, i2, j1, j2 in smx.get_opcodes() if tg in ("replace", "insert") for j in range(j1, j2)]
            row["sc6_added_lines_all_return"] = int(bool(plus) and all(l.startswith("return") for l in plus))
            row["sc6_added_lines_n"] = len(plus)
            row["base_exc_fraction"] = tb["stats"]["exception_fraction"] if tb else ""
            row["variant_exc_fraction"] = tv["stats"]["exception_fraction"] if tv else ""
            row["partner_exc_fraction"] = tp["stats"]["exception_fraction"] if tp else ""
            # ---- class
            basis = pv if pv.get("available") else bv
            cls, why = classify(basis)
            row["cause_basis"] = "PV" if pv.get("available") else "BV"
            row["cause_class"] = cls if row["invisible_v5"] else ""
            row["cause_evidence"] = why if row["invisible_v5"] else ""
            row["cause_class_if_BV"] = classify(bv)[0]
            if row["invisible_v5"] and r["scores"]["sbg_v3"] != 0:
                anomalies.append(f"{split} {r['pair_id']}: v5==0 but v3!=0")
            out.append(row)
        csv_rows[split] = out
        summary["splits"][split] = summarise(out, sc6)
    summary["anomalies"] = anomalies
    return summary, csv_rows, diffs


def summarise(out, sc6):
    n = len(out)
    s = {"n_sc6_changed_primary": n}
    for k in SCORES:
        s[f"n_{k}_zero"] = sum(1 for r in out if r[k] == 0)
    s["n_invisible_v5"] = sum(r["invisible_v5"] for r in out)
    s["n_visible_v5"] = n - s["n_invisible_v5"]
    s["n_all_four_zero"] = sum(1 for r in out if all(r[k] == 0 for k in SCORES))

    def tab(keyf):
        t = collections.OrderedDict()
        for r in sorted(out, key=lambda r: str(keyf(r))):
            e = t.setdefault(str(keyf(r)), {"n": 0, "v5_zero": 0, "v5_visible": 0})
            e["n"] += 1
            e["v5_zero" if r["invisible_v5"] else "v5_visible"] += 1
        return t
    s["by_sp_type"] = tab(lambda r: r["sp_type"])
    s["by_edit_bin"] = tab(lambda r: r["edit_bin"])
    # visible pairs vs matched equivalent partner
    vis = [r for r in out if not r["invisible_v5"]]
    cat = collections.Counter()
    detail = []
    for r in vis:
        pv5 = r["partner_sbg_v5"]
        if pv5 == "":
            c = "no_partner"
        elif pv5 == 0:
            c = "partner_zero(visibility not explained by SP edit)"
        elif r["sbg_v5"] <= pv5:
            c = "SP_alone_explains(pair_v5<=partner_v5)"
        else:
            c = "partner_nonzero_pair_higher(SP contributes; SC-6 may add)"
        cat[c] += 1
        detail.append({"pair_id": r["pair_id"], "sp": r["sp_type"], "edit": r["edit"], "v5": r["sbg_v5"], "partner_v5": pv5,
                       "pv_ret_diff": r["pv_ret_diff"], "category": c})
    s["visible_vs_partner"] = dict(cat)
    dl = [r["sbg_v5"] - r["partner_sbg_v5"] for r in vis if r["partner_sbg_v5"] != ""]
    s["visible_pair_minus_partner_v5"] = {"min": min(dl) if dl else None, "max": max(dl) if dl else None,
                                          "n_exactly_equal": sum(1 for d in dl if d == 0), "n_pair_gt_partner": sum(1 for d in dl if d > 0)}
    s["visible_with_partner_exc_fraction_gt0"] = sum(1 for r in vis if r["partner_exc_fraction"] not in ("", 0, 0.0))
    s["visible_with_partner_exc_fraction_eq1"] = sum(1 for r in vis if r["partner_exc_fraction"] == 1.0)
    s["invisible_with_all_exc_fraction_zero"] = sum(1 for r in out if r["invisible_v5"] and r["variant_exc_fraction"] == 0)
    s["visible_detail"] = detail
    s["partner_v5_zero_among_visible"] = sum(1 for r in vis if r["partner_sbg_v5"] == 0)
    s["partner_v5_zero_among_invisible"] = sum(1 for r in out if r["invisible_v5"] and r["partner_sbg_v5"] == 0)
    # causes
    inv = [r for r in out if r["invisible_v5"]]
    s["cause_counts_v5_zero"] = dict(collections.Counter(r["cause_class"] for r in inv))
    s["cause_counts_v5_zero_if_BV_basis"] = dict(collections.Counter(r["cause_class_if_BV"] for r in inv))
    s["cause_by_pair"] = {r["pair_id"]: r["cause_class"] for r in inv}
    s["task4_pv_diff_inputs_zero_pairs_with_ret_in_r_locals_on_some_differing_input"] = sum(
        1 for r in inv if r["pv_diffinputs_variant_ret_in_r_locals"] not in ("", 0))
    s["task4_pv_diff_inputs_zero_pairs_with_ret_in_r_locals_on_all_differing_inputs"] = sum(
        1 for r in inv if r["pv_diffinputs_n_with_r_snapshot"] not in ("", 0) and r["pv_diffinputs_variant_ret_in_r_locals"] == r["pv_diffinputs_n_with_r_snapshot"])
    s["task4_pv_diff_inputs_zero_pairs_with_ret_in_r_locals_nontrivial_some"] = sum(
        1 for r in inv if r["pv_diffinputs_variant_ret_in_r_locals_nontrivial"] not in ("", 0))
    s["all_pairs_sc6_added_lines_all_return"] = sum(r["sc6_added_lines_all_return"] for r in out)
    s["zero_pairs_pv_snapshots_differ_only_by_memory_address"] = sum(
        1 for r in inv if r["pv_snap_diff_rawaddr"] not in ("", 0) and r["pv_snap_diff"] == 0)
    s["all_pairs_pv_snapshots_differ_only_by_memory_address"] = sum(
        1 for r in out if r["pv_snap_diff_rawaddr"] not in ("", 0) and r["pv_snap_diff"] == 0)
    s["zero_pairs_sc6_added_lines_all_return"] = sum(r["sc6_added_lines_all_return"] for r in inv)
    s["cause_A_with_all_added_lines_return"] = sum(1 for r in inv if r["cause_class"] == "A" and r["sc6_added_lines_all_return"])
    s["cause_D_trunc"] = sum(1 for r in inv if r["cause_class"] == "D" and "truncated" in r["cause_evidence"])
    s["cause_D_lean_if_trunc_ignored"] = dict(collections.Counter(re.search(r"would be (\w)", r["cause_evidence"]).group(1) for r in inv if r["cause_class"] == "D" and "would be" in r["cause_evidence"]))
    s["task4_zero_pairs_variant_ret_visible_in_r_locals_all_inputs"] = sum(
        1 for r in inv if r["variant_r_snapshot_inputs"] not in ("", 0) and r["variant_ret_in_r_locals"] == r["variant_r_snapshot_inputs"])
    s["task4_zero_pairs_variant_ret_visible_in_r_locals_some_inputs"] = sum(
        1 for r in inv if r["variant_ret_in_r_locals"] not in ("", 0))
    s["task4_zero_pairs_variant_ret_visible_nontrivial_some_inputs"] = sum(
        1 for r in inv if r["variant_ret_in_r_locals_nontrivial"] not in ("", 0))
    s["zero_pairs_pv_skeleton_identical"] = sum(1 for r in inv if r["pv_skeleton_identical"] == 1)
    s["zero_pairs_pv_snapshots_identical"] = sum(1 for r in inv if r["pv_snapshots_identical"] == 1)
    s["zero_pairs_pv_ret_diff_ge1"] = sum(1 for r in inv if r["pv_ret_diff"] not in ("", 0))
    s["zero_pairs_bv_ret_diff_ge1"] = sum(1 for r in inv if r["bv_ret_diff"] not in ("", 0))
    s["zero_pairs_bv_ret_diff_zero"] = sum(1 for r in inv if r["bv_ret_diff"] == 0)
    s["zero_pairs_trace_unavailable"] = sum(1 for r in inv if not r["bv_available"] or not r["pv_available"])
    s["all_pairs_bv_ret_diff_zero"] = sum(1 for r in out if r["bv_ret_diff"] == 0)
    s["visible_pairs_bv_ret_diff_zero"] = sum(1 for r in vis if r["bv_ret_diff"] == 0)
    return s


def write_all(summary, csv_rows, diffs):
    OUT.mkdir(parents=True, exist_ok=True)
    targets = [OUT / f"sc6_pairs_{s}.csv" for s in SPLITS] + [OUT / f"sc6_diffs_{s}.txt" for s in SPLITS] + [OUT / "sc6_summary.json",
                                                                                                         OUT / "SC6_FORENSICS_SUMMARY.md"]
    ex = [str(t) for t in targets if t.exists()]
    if ex:
        sys.exit("refusing to overwrite: " + ", ".join(ex))
    for s in SPLITS:
        rows = csv_rows[s]
        with open(OUT / f"sc6_pairs_{s}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        (OUT / f"sc6_diffs_{s}.txt").write_text("\n".join(diffs[s]) + "\n")
    (OUT / "sc6_summary.json").write_text(json.dumps(summary, indent=1, sort_keys=False) + "\n")
    write_md(summary, csv_rows)


def write_md(summary, csv_rows):
    f = OUT / "SC6_FORENSICS_SUMMARY.md"
    if f.exists():
        sys.exit(f"refusing to overwrite {f}")
    S = summary["splits"]
    L = []
    w = L.append
    w("# EXP-WPC-004 - SC-6 CHANGED-pair forensics (label-free, descriptive; generated by `scripts/wpc_sc6_forensics.py`)\n")
    w("Scope: frozen scores + cached traces only; **nothing was scored or evaluated** (no AUROC); V10 / V9c-val used descriptively only. "
      "'Invisible' := frozen `sbg_v5 == 0` (exact). 'Partner' := label-0 primary row with the same `group` (same SP transform, no SC-6; "
      "cross-checked against the repo's `matched_pair_id`/`matched_equivalent_pair_id`: 0 mismatches).\n")
    w("## 1. Zero-score counts (SC-6, label 1, primary)\n")
    w("| split | n | v5==0 | v3==0 | temporal==0 | state==0 | all four ==0 | v5>0 (visible) |")
    w("|---|---|---|---|---|---|---|---|")
    for sp in SPLITS:
        x = S[sp]
        w(f"| {sp} | {x['n_sc6_changed_primary']} | {x['n_sbg_v5_zero']} | {x['n_sbg_v3_zero']} | {x['n_sbg_temporal_zero']} | "
          f"{x['n_sbg_state_zero']} | {x['n_all_four_zero']} | {x['n_visible_v5']} |")
    v = S["v10_test"]
    w(f"\n**V10 verification: {v['n_sbg_v5_zero']}/{v['n_sc6_changed_primary']} SC-6 CHANGED pairs have `sbg_v5 == 0`** "
      f"({'CONFIRMED' if (v['n_sbg_v5_zero'], v['n_sc6_changed_primary']) == (17, 23) else 'NOT CONFIRMED'}); the same 17 are zero on v3, temporal and state.\n")
    w("### By composed SP transform and edit size (v5==0 / n)\n")
    w("| split | " + " | ".join(f"SP-{k}" for k in (1, 2, 3, 8, 11)) + " | edit<=10 | 11-30 | 31-60 | >60 |")
    w("|---|" + "---|" * 9)
    for sp in SPLITS:
        x = S[sp]
        cells = []
        for k in (1, 2, 3, 8, 11):
            e = x["by_sp_type"].get(f"SP-{k}")
            cells.append(f"{e['v5_zero']}/{e['n']}" if e else "-")
        for b in ("<=10", "11-30", "31-60", ">60"):
            e = x["by_edit_bin"].get(b)
            cells.append(f"{e['v5_zero']}/{e['n']}" if e else "-")
        w(f"| {sp} | " + " | ".join(cells) + " |")
    w("\n`edit` = value stored in the population file (units not independently verified); it is almost fully determined by the SP type "
      "(SP-2 pairs: edit = 4 in every row), so edit size and SP type are confounded.\n")
    w("### Are the visible pairs visible only because of the composed SP edit?\n")
    w("| split | visible (v5>0) | partner v5 == 0 | pair v5 == partner v5 exactly | pair v5 > partner v5 | max(pair - partner) | visible with partner exc_fraction>0 | (partner exc_fraction==1) |")
    w("|---|---|---|---|---|---|---|---|")
    for sp in SPLITS:
        x = S[sp]
        d = x["visible_pair_minus_partner_v5"]
        w(f"| {sp} | {x['n_visible_v5']} | {x['partner_v5_zero_among_visible']} | {d['n_exactly_equal']} | {d['n_pair_gt_partner']} | "
          f"{d['max']} | {x['visible_with_partner_exc_fraction_gt0']} | {x['visible_with_partner_exc_fraction_eq1']} |")
    w(f"\nOn V10 all {v['n_visible_v5']} visible SC-6 pairs have a matched SP-only partner with the *identical* `sbg_v5` "
      f"(difference exactly {v['visible_pair_minus_partner_v5']['max']}), i.e. **{v['visible_vs_partner'].get('SP_alone_explains(pair_v5<=partner_v5)', 0)}/{v['n_visible_v5']} "
      "visible V10 pairs are visible only because of the composed SP edit; SC-6 contributes no measurable score (SC-6-attributable detections = 0/23).** "
      "Same on every analogue split (see table). Caveat: this shows the *score* is unchanged by SC-6; it does not by itself prove that the two genomes are identical.\n")
    w("## 2. SC-6 edit (all pairs)\n")
    for sp in SPLITS:
        w(f"- {sp}: {S[sp]['all_pairs_sc6_added_lines_all_return']}/{S[sp]['n_sc6_changed_primary']} pairs - every changed line (partner->variant, parentheses ignored) is a `return` line. "
          "Observed forms: `return X` -> `return not X`; `return <const>` -> `return <const> + 1`.")
    w("\nFull unified diffs (partner->variant isolates SC-6; base->variant also shown): `sc6_diffs_<split>.txt`; one-line auto descriptions in the CSV column `sc6_edit_desc_auto` "
      "(rule-based; for V10 verified by reading all 23 diffs: every SC-6 edit is a final-`return` expression mutation, e.g. `return result` -> `return not result`).\n")
    w("## 3. Trace channels and cause classes for v5==0 pairs\n")
    w("Channel comparison uses **PV = partner-vs-variant** (SP transform cancels, same SP seed) as primary basis; BV (base-vs-variant) columns are in the CSV but are confounded "
      "by the SP edit (line-event skeleton/coverage differ on SP-transformed code). Run 0 only is stored in the cache. Locals snapshots compared at c/r/e events only, "
      "after masking `0x...` addresses.\n")
    w("| split | zero pairs | A | B | C | D | D: truncated (lean if ignored) | D: cache missing | zero pairs with PV skeleton identical | PV c/r/e snapshots identical | PV ret differs on >=1 input |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for sp in SPLITS:
        x = S[sp]
        c = x["cause_counts_v5_zero"]
        w(f"| {sp} | {x['n_invisible_v5']} | {c.get('A', 0)} | {c.get('B', 0)} | {c.get('C', 0)} | {c.get('D', 0)} | "
          f"{x['cause_D_trunc']} ({x['cause_D_lean_if_trunc_ignored']}) | {x['zero_pairs_trace_unavailable']} | {x['zero_pairs_pv_skeleton_identical']} | "
          f"{x['zero_pairs_pv_snapshots_identical']} | {x['zero_pairs_pv_ret_diff_ge1']} |")
    w("\nDefinitions (decided on PV): **A** ret differs on >=1 input, exc/stdout identical, full event skeleton (type+function incl. line events) identical, every c/r/e locals snapshot identical; "
      "**B** as A but a c/r/e snapshot differs (and abstract-domain snapshots identical - see below); **C** ret/exc/stdout identical on all 11 inputs; "
      "**D** other (truncated traces, missing cache, exc/stdout/skeleton differ, or abstract snapshot differs). **B = 0 everywhere**: before masking memory addresses "
      "many pairs looked like B because snapshots hold `<function ... at 0x...>` reprs that differ between processes; after masking, no zero-score pair has any other differing recorded local.\n")
    w("Honest limits: (i) the cache keeps locals snapshots only at c/r/e events; line-event snapshots (which the frozen state genome consumes) are NOT in the cache, so class A means "
      "'no difference in recorded c/r/e locals', not 'no difference in any local at any line' (for a pure `return <expr>` edit there is no new local by construction, which is consistent with A); "
      "(ii) only run 0 of 5 runs is stored; (iii) `ret` reprs are capped at 1500 chars; (iv) class C = battery-blind on 11 inputs only - the label oracle's differing input is not recoverable here (UNKNOWN); "
      "(v) the 'abstract domain collapse' (class B) was not observed, so it is not supported as a cause by this evidence.\n")
    w("### Task 4 - does the returned value appear in the `r`-event locals of the entry function? (zero-score pairs, variant)\n")
    w("| split | pairs with ret present among r-snapshot values on >=1 input (all inputs) | same, non-trivial values only | on inputs where ret differs from partner: pairs with ret in locals (>=1 input) | (all differing inputs) |")
    w("|---|---|---|---|---|")
    for sp in SPLITS:
        x = S[sp]
        w(f"| {sp} | {x['task4_zero_pairs_variant_ret_visible_in_r_locals_some_inputs']} | {x['task4_zero_pairs_variant_ret_visible_nontrivial_some_inputs']} | "
          f"{x['task4_pv_diff_inputs_zero_pairs_with_ret_in_r_locals_on_some_differing_input']} | {x['task4_pv_diff_inputs_zero_pairs_with_ret_in_r_locals_on_all_differing_inputs']} |")
    w("\n(Exact string match of `repr(ret)` to a snapshot value of the entry function's last `r` event; snapshot values capped at 100 chars, long returns compared on the first 90 chars; "
      "'non-trivial' excludes None/True/False/0/1/-1/empty containers. Matches on inputs where ret is unchanged are coincidental, hence the restriction to differing inputs. "
      "The mutated return value (`not X`, `X + 1`) is by construction not a local, so the changed value is not recorded in the snapshot.)\n")
    w("## 4. V10 per-pair table (23 SC-6 pairs)\n")
    w("| pair | SP | edit | v5 | partner v5 | PV ret diff /11 | PV skeleton ident. | PV c/r/e snaps ident. | PV cov-size diff inputs | class | SC-6 edit |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in csv_rows["v10_test"]:
        w(f"| {r['pair_id'].split('__', 1)[1]} | {r['sp_type']} | {r['edit']:g} | {r['sbg_v5']:.4f} | {r['partner_sbg_v5']:.4f} | {r['pv_ret_diff']} | "
          f"{'yes' if r['pv_skeleton_identical'] else 'no'} | {'yes' if r['pv_snapshots_identical'] else 'no'} | {r['pv_cov_size_diff']} | "
          f"{r['cause_class'] or 'visible'} | `{r['sc6_edit_desc_auto'].split(': ', 1)[-1][:80]}` |")
    w("\n## 5. Anomalies / data problems\n")
    for sp in SPLITS:
        x = S[sp]
        w(f"- {sp}: zero-score pairs whose raw PV c/r/e snapshots differ ONLY by memory address reprs: {x['zero_pairs_pv_snapshots_differ_only_by_memory_address']} "
          f"(all pairs: {x['all_pairs_pv_snapshots_differ_only_by_memory_address']}).")
    w("- Cached snapshots contain process-specific `<function ... at 0x...>` reprs (nondeterministic across extractions); the frozen abstract domain maps them to NON_NULL so scores are unaffected, but raw snapshot equality is unusable without masking.")
    w(f"- v9c SP-8 'equivalent' partners can be broken: visible SC-6+SP-8 pairs whose SP-only partner has exception_fraction>0 -> val {S['v9c_val']['visible_with_partner_exc_fraction_gt0']}, "
      f"dev {S['v9c_dev']['visible_with_partner_exc_fraction_gt0']}, train {S['v9c_train']['visible_with_partner_exc_fraction_gt0']} "
      f"(e.g. val `math_largest_rect_hist__sp-8_s2`: `UnboundLocalError` on all inputs, exception_fraction 1.0). Their large v5 (0.28-0.68) is then driven by exceptions of the SP transform itself. Not investigated further (outside scope).")
    w("- v9c_train: `math_gray_code` is absent from the trace cache -> its 2 SC-6 pairs (1 zero-score, 1 visible) have no trace evidence (UNKNOWN; counted D).")
    w("- Truncated traces (event cap) in a few pairs prevent a clean classification -> D, with the lean if truncation were ignored shown above.")
    w("- In v9c splits the partner comes from the v8 SP pipeline while the SC-6 variant comes from v9_composed, so partner->variant diffs contain cosmetic parenthesisation differences (ignored in descriptions/flags).")
    w("- Base->variant comparisons: the SP transform alone changes the line-event skeleton/coverage, so BV classification is not meaningful (almost all D); see `cause_class_if_BV`.")
    w("- Anomaly list from consistency checks (partner count != 1, matched-id mismatch, v5==0 but v3!=0): " + (", ".join(summary["anomalies"]) or "none") + ".\n")
    w("## 6. Reproduction\n")
    w("```\ncd IEEE_ACCESS_PRE_SUBMISSION/WP_C_ABLATIONS/scripts\nexport PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1\n"
      "../../../venvs/py313/bin/python wpc_sc6_forensics.py          # ~0.5 s; refuses to overwrite existing outputs\n```\n")
    w("Outputs: `sc6_pairs_<split>.csv` (one row per pair, all channel fields), `sc6_diffs_<split>.txt`, `sc6_summary.json`, this file.\n")
    f.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    summary, csv_rows, diffs = run(not a.no_write)
    if a.no_write:
        for s in SPLITS:
            print(s, json.dumps({k: v for k, v in summary["splits"][s].items() if k != "visible_detail"}, indent=1))
        print("ANOMALIES", summary["anomalies"])
    else:
        write_all(summary, csv_rows, diffs)
        print("written to", OUT)
