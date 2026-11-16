#!/usr/bin/env python3
"""WP-D / D1 step 1 -- STATIC inventory of the external corpora (nothing is executed).

Reads (read-only) SBG/external/*/manifest, SBG/artifacts/final/pairs_{bugsinpy,quixbugs_*}_output_free_v7.jsonl and
SBG/artifacts/paper_evidence/raw/external_rescore_v8_pairs.json.  Writes ONLY under
WP_D_EXTERNAL_VALIDATION/raw/WPD-D1_compat/data/.

Outputs
  bugsinpy_bug_ledger.csv         one row per BugsInPy bug (501) with eligibility and the exclusion reason(s)
  bugsinpy_unit_ledger.csv        one row per candidate unit (704) with eligibility and exclusion reason
  bugsinpy_exclusion_taxonomy.json  recomputed counts (checked against the manifest's own taxonomy)
  bugsinpy_pair_ledger.csv        200 scored-pair rows (55 positives + 145 negatives): evaluated? failure kind
  quixbugs_program_ledger.csv     50 files (40 subject programs + 10 scaffolding) with eligibility reasons
  quixbugs_pair_ledger.csv        canonical + declared pair rows with failure kinds
  java_inventory.json             what exists for QuixBugs-Java (files, results, SBG-schema artifact?)

PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 venvs/py313/bin/python scripts/d1_01_inventory.py
"""
import collections
import csv
import json
import pathlib

HERE = pathlib.Path(__file__).resolve()
WP = HERE.parents[1]
PKG = WP.parent
REPO = PKG.parent / "SBG"
OUT = WP / "raw" / "WPD-D1_compat" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def write_csv(name, rows, cols):
    with open(OUT / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def family(reason):
    parts = (reason or "").split(":")
    if parts[0] in ("buggy", "fixed") and len(parts) > 1:
        return parts[1]
    return parts[0]


# ----------------------------------------------------------------------------- BugsInPy
man = json.loads((REPO / "external/bugsinpy/manifest.json").read_text())
bugs = man["bugs"]
bug_rows, unit_rows = [], []
for b in bugs:
    n_units = len(b["units"])
    n_elig = sum(1 for u in b["units"] if u["eligible"])
    bug_rows.append({
        "bug_id": b["id"], "project": b["project"], "eligible": b["eligible"],
        "exclusion_reason": b["exclusion_reason"] or "",
        "n_candidate_units": n_units, "n_eligible_units": n_elig,
        "unit_exclusion_reasons": " | ".join(b.get("unit_exclusion_reasons", [])),
        "file_notes": " | ".join(f"{n.get('file')}:{n['note']}" for n in b.get("file_notes", [])),
        "license": b["license"],
    })
    for u in b["units"]:
        unit_rows.append({
            "bug_id": b["id"], "project": b["project"], "file": u["file"], "unit": u["unit"],
            "kind": u.get("kind") or "", "changed_members": ";".join(u["changed_members"]),
            "eligible": u["eligible"], "exclusion_reason": u["exclusion_reason"] or "",
            "exclusion_family": family(u["exclusion_reason"]) if not u["eligible"] else "",
            "n_negatives": len(u.get("negatives", [])),
        })
write_csv("bugsinpy_bug_ledger.csv", bug_rows,
          ["bug_id", "project", "eligible", "exclusion_reason", "n_candidate_units", "n_eligible_units",
           "unit_exclusion_reasons", "file_notes", "license"])
write_csv("bugsinpy_unit_ledger.csv", unit_rows,
          ["bug_id", "project", "file", "unit", "kind", "changed_members", "eligible", "exclusion_reason",
           "exclusion_family", "n_negatives"])

bug_tax = collections.Counter(b["exclusion_reason"] for b in bugs if not b["eligible"])
unit_tax = collections.Counter(family(u["exclusion_reason"]) for b in bugs for u in b["units"] if not u["eligible"])
per_project = collections.defaultdict(lambda: {"bugs": 0, "bugs_eligible": 0, "units_eligible": 0})
for b in bugs:
    p = per_project[b["project"]]
    p["bugs"] += 1
    p["bugs_eligible"] += int(b["eligible"])
    p["units_eligible"] += sum(1 for u in b["units"] if u["eligible"])
# specific-name granularity (e.g. which project-internal module blocked the unit)
detail = collections.Counter()
for b in bugs:
    for u in b["units"]:
        if not u["eligible"]:
            detail[u["exclusion_reason"]] += 1
tax = {
    "recomputed": {
        "bugs_total": len(bugs), "bugs_eligible": sum(b["eligible"] for b in bugs),
        "units_total": len(unit_rows), "units_eligible": sum(1 for u in unit_rows if u["eligible"]),
        "bug_exclusion_taxonomy": dict(bug_tax.most_common()),
        "unit_exclusion_family_taxonomy": dict(unit_tax.most_common()),
        "units_by_kind_eligible": dict(collections.Counter(u["kind"] for u in unit_rows if u["eligible"])),
        "per_project": dict(sorted(per_project.items())),
    },
    "manifest_declared": {"counts": man["counts"], "bug_exclusion_taxonomy": man["bug_exclusion_taxonomy"],
                          "unit_exclusion_taxonomy": man["unit_exclusion_taxonomy"]},
    "matches_manifest": (dict(bug_tax) == man["bug_exclusion_taxonomy"]
                         and dict(unit_tax) == man["unit_exclusion_taxonomy"]
                         and len(bugs) == man["counts"]["bugs_total"]),
    "unit_exclusion_reason_detail_top40": detail.most_common(40),
    "n_unit_exclusion_distinct_reason_strings": len(detail),
}
(OUT / "bugsinpy_exclusion_taxonomy.json").write_text(json.dumps(tax, indent=1) + "\n")

# scored pair ledger
bp = jl(REPO / "artifacts/final/pairs_bugsinpy_output_free_v7.jsonl")
write_csv("bugsinpy_pair_ledger.csv",
          [{"pair_id": r["pair_id"], "bug_id": r["bug_id"], "project": r["project"], "unit": r["unit"],
            "unit_kind": r["unit_kind"], "role": r["role"], "label": r["label"],
            "transformation": r["transformation"], "evaluated": r["evaluated"],
            "failure_side": r["failure_side"], "failure_kind": r["failure_kind"],
            "failure_detail": r["failure_detail"], "observable_static_flag": r["observable"],
            "sbg_v5_committed_v7": (r["scores"] or {}).get("sbg_v5"),
            "base_path": r["base_path"], "variant_path": r["variant_path"]} for r in bp],
          ["pair_id", "bug_id", "project", "unit", "unit_kind", "role", "label", "transformation", "evaluated",
           "failure_side", "failure_kind", "failure_detail", "observable_static_flag", "sbg_v5_committed_v7",
           "base_path", "variant_path"])
bp_fail = collections.Counter((r["role"], r["unit_kind"], r["failure_kind"]) for r in bp if not r["evaluated"])

# ----------------------------------------------------------------------------- QuixBugs
qm = json.loads((REPO / "external/quixbugs/manifest.json").read_text())
qrows = []
for p in qm["programs"]:
    qrows.append({"program": p["id"], "kind": "subject", "eligible_canonical": p["eligible"]["canonical"],
                  "eligible_declared": p["eligible"]["declared"],
                  "reason_canonical": (p["exclusion_reason"] or {}).get("canonical") if isinstance(p["exclusion_reason"], dict) else p["exclusion_reason"],
                  "reason_declared": (p["exclusion_reason"] or {}).get("declared") if isinstance(p["exclusion_reason"], dict) else p["exclusion_reason"],
                  "n_declared_cases": p.get("declared_inputs", {}).get("n_cases"),
                  "n_negatives": len(p.get("negatives", [])),
                  "negatives": ";".join(n["transformation_type"] for n in p.get("negatives", [])),
                  "rejected_negatives": ";".join(f"{r['transformation_type']}:{r['reason']}" for r in p.get("negatives_rejected", []))})
for s in qm.get("scaffolding", []):
    qrows.append({"program": s["file"], "kind": "scaffolding_excluded", "eligible_canonical": False,
                  "eligible_declared": False, "reason_canonical": s["reason"], "reason_declared": s["reason"]})
write_csv("quixbugs_program_ledger.csv", qrows,
          ["program", "kind", "eligible_canonical", "eligible_declared", "reason_canonical", "reason_declared",
           "n_declared_cases", "n_negatives", "negatives", "rejected_negatives"])

qpair = []
q_fail = {}
for regime in ("canonical", "declared"):
    rows = jl(REPO / f"artifacts/final/pairs_quixbugs_{regime}_output_free_v7.jsonl")
    for r in rows:
        qpair.append({"regime": regime, "pair_id": r["pair_id"], "base_id": r["base_id"], "label": r["label"],
                      "pair_kind": r["pair_kind"], "evaluated": r["evaluated"], "failure_side": r["failure_side"],
                      "failure_kind": r["failure_kind"], "failure_detail": (r["failure_detail"] or "")[:200],
                      "sbg_v5_committed_v7": (r["scores"] or {}).get("sbg_v5") if r["evaluated"] else None,
                      "declared_output_reference_differs": (r.get("output_reference") or {}).get("differs"),
                      "declared_n_mismatches": (r.get("output_reference") or {}).get("n_mismatches"),
                      "declared_n_inputs": (r.get("output_reference") or {}).get("n_inputs")})
    q_fail[regime] = dict(collections.Counter((r["label"], r["failure_kind"]) .__repr__() for r in rows if not r["evaluated"]))
write_csv("quixbugs_pair_ledger.csv", qpair,
          ["regime", "pair_id", "base_id", "label", "pair_kind", "evaluated", "failure_side", "failure_kind",
           "failure_detail", "sbg_v5_committed_v7", "declared_output_reference_differs", "declared_n_mismatches",
           "declared_n_inputs"])

# ----------------------------------------------------------------------------- Java
jroot = REPO / "external/quixbugs_java"
jm = json.loads((jroot / "MANIFEST.json").read_text())
art = sorted(p.name for p in (REPO / "artifacts/final").glob("*java*")) + \
    sorted(p.name for p in (REPO / "artifacts/final").glob("*JAVA*"))
res_files = sorted(str(p.relative_to(REPO)) for p in (REPO / "results").rglob("*") if "java" in p.name.lower())
java = {
    "programs_in_manifest": len(jm["programs"]),
    "buggy_files": len(list((jroot / "buggy").glob("*.java"))),
    "correct_files": len(list((jroot / "correct").glob("*.java"))),
    "tracer": "external/quixbugs_java/tracer/SbgJdiTracer.java",
    "artifacts_final_matching_java": art,
    "results_dir_matching_java": res_files,
    "QUIXBUGS_JAVA_SBG_RESULTS_json_exists": (REPO / "artifacts/final/QUIXBUGS_JAVA_SBG_RESULTS.json").exists(),
    "pairs_quixbugs_java_jsonl_exists": (REPO / "artifacts/final/pairs_quixbugs_java.jsonl").exists(),
    "JAVA_CLAIM_REMOVAL_json_exists": any(REPO.rglob("JAVA_CLAIM_REMOVAL.json")),
    "note": "see FINDINGS.md section 5; results/external/QUIXBUGS_JAVA_EVALUATION_RESULTS.json is the Aug-2026 EEP pilot "
            "(method ENTER/EXIT markers, 5-feature 'EEP' formula, tau=0.08): not an SBG-schema measurement.",
}
(OUT / "java_inventory.json").write_text(json.dumps(java, indent=1) + "\n")

summary = {
    "bugsinpy": {"taxonomy_matches_manifest": tax["matches_manifest"],
                 "bugs_total": len(bugs), "bugs_eligible": tax["recomputed"]["bugs_eligible"],
                 "units_total": len(unit_rows), "units_eligible": tax["recomputed"]["units_eligible"],
                 "pair_rows": len(bp), "pair_failures": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in bp_fail.items()}},
    "quixbugs": {"manifest_counts": qm["counts"], "pair_failures": q_fail},
    "java": java,
}
(OUT / "inventory_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
print(json.dumps(summary, indent=1))
