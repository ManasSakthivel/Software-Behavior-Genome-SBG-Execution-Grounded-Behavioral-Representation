"""Independent, read-only verification of the SBG V8 five-dataset run.

Reads only existing repo files (results/v8/independent-validation, datasets/v8, sbgv8 code, git objects) and writes
paper/IEEE_ACCESS_V8_FINAL/audit/five_dataset_summary.json. Run from anywhere:
    /Users/manassakthivel/Desktop/SBG-V6/.venv/bin/python paper/IEEE_ACCESS_V8_FINAL/scripts/verify_five_dataset.py
"""
from __future__ import annotations
import collections, csv, hashlib, json, re, statistics, subprocess, sys, types
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
R = REPO / "results/v8/independent-validation"
OUT = REPO / "paper/IEEE_ACCESS_V8_FINAL/audit/five_dataset_summary.json"
FIX_BRANCH = "research/v8-mac-hardening"
FIX_COMMIT = "b9b8a86c"
DIV, NDO, INS = "DIVERGENT_OBSERVABLE", "NO_DIVERGENCE_OBSERVED", "INSUFFICIENT"


def jl(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
def git(*a): return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True).stdout
def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


pairs = json.load(open(R / "pair_manifest.json"))
ex = jl(R / "execution_results.jsonl")
ers = jl(R / "ers_results.jsonl")
excl = jl(R / "exclusions.jsonl")
dsm = json.load(open(R / "dataset_manifest.json"))
lock_meta = json.load(open(R / "prediction_lock_metadata.json"))
blind = json.load(open(R / "blinded_adjudication_cases.json"))
tmpl = list(csv.DictReader(open(R / "blinded_adjudication_template.csv", encoding="utf-8")))
exb = {e["pair_id"]: e for e in ex}
DS = [d["id"] for d in dsm["datasets"]]
S = {"generated_by": "paper/IEEE_ACCESS_V8_FINAL/scripts/verify_five_dataset.py", "git_head": git("rev-parse", "HEAD").strip()}

# ---- 1. integrity of identifiers -------------------------------------------------------------------------------
ids = [p["pair_id"] for p in pairs]
S["identifiers"] = {
    "n_pair_manifest": len(pairs), "n_execution_results": len(ex), "n_ers_results": len(ers), "n_exclusions": len(excl),
    "duplicate_pair_ids": [k for k, c in collections.Counter(ids).items() if c > 1],
    "pair_ids_match_execution": sorted(ids) == sorted(exb), "pair_ids_match_ers": sorted(ids) == sorted(e["pair_id"] for e in ers),
}

# ---- 2. provenance: is the manifest anything other than the output of datasets.py? -----------------------------
from sbgv8.independent_validation import datasets, executor
regen = datasets.load_all_candidate_pairs()
def norm(src, p):  # strip project name and digits -> template skeleton
    return re.sub(r"\d+", "#", src.replace(p["project"], "<P>").replace(p["project"].lower(), "<p>"))
shas_fabricated = 0
for p in pairs:  # every SHA is sha1(<literal string>)[:12], not a git commit; recognise the literal patterns used in datasets.py
    pre = {"Defects4J": "d4j", "BugsInPy": "bip", "Bears": "bears", "BugSwarm": "swarm", "Bugs.jar": "bugsjar"}[p["dataset"]]
    idx = p["bug_id"].split("_")[-1]
    cands = [f"{pre}_{p['project']}_buggy_{idx}", f"{pre}_{p['project']}_nb_b", f"{pre}_{p['project']}_nb_b_{idx}"]
    shas_fabricated += any(hashlib.sha1(c.encode()).hexdigest()[:12] == p["buggy_sha"] for c in cands)
S["provenance"] = {
    "pair_manifest_equals_datasets_py_output": regen == pairs,
    "buggy_sha_equals_sha1_of_literal_string": shas_fabricated,
    "distinct_code_templates_by_dataset_and_change_type": {},
    "distinct_raw_source_pairs": len({(p["base_src"], p["variant_src"]) for p in pairs}),
    "patch_diff_is_truncated_60_char_stub": sum(p["patch_diff"].count("...") == 2 and "@@ -1,5 +1,5 @@" in p["patch_diff"] for p in pairs),
}
tmpls = collections.defaultdict(set)
for p in pairs:
    tmpls[f"{p['dataset']}|{p['change_type']}|{p['language']}"].add((norm(p["base_src"], p), norm(p["variant_src"], p)))
S["provenance"]["distinct_code_templates_by_dataset_and_change_type"] = {k: len(v) for k, v in sorted(tmpls.items())}
S["provenance"]["distinct_templates_total"] = len(set().union(*tmpls.values()))

# evidence records: re-derive from executor and check that outcomes are a pure function of (change_type, test purpose)
rederived_equal, outcome_rule_holds = 0, 0
for p in pairs:
    rec = executor.pair_to_evidence_record(p)
    rederived_equal += rec.to_json() == exb[p["pair_id"]]["evidence_record_json"]
    want = ["CONFIRMED_DIFF" if p["change_type"] == "bug_fix" and t["purpose"] == "trigger_discriminating" else "SAME" for t in p["test_suite"]]
    outcome_rule_holds += [i.outcome for i in rec.inputs] == want
S["provenance"]["evidence_records_rederived_identically_without_execution"] = rederived_equal
S["provenance"]["outcomes_equal_label_rule"] = outcome_rule_holds

# ---- 3. independent execution of the Python snippets (the only code that is executable at all) -----------------
def run(src, kw):
    ns = {}
    exec(src, ns)  # repo-authored snippets, trusted
    fn = next(v for k, v in ns.items() if callable(v) and not k.startswith("_"))
    try: return ("ok", fn(**kw))
    except Exception as e: return ("exc", type(e).__name__)
py = collections.Counter()
for p in pairs:
    if p["language"] != "Python": continue
    diff = [run(p["base_src"], t["input"]) != run(p["variant_src"], t["input"]) for t in p["test_suite"]]
    py[(p["dataset"], p["change_type"], "real_divergence" if any(diff) else "no_divergence")] += 1
S["python_snippet_reexecution"] = {"|".join(k): v for k, v in sorted(py.items())}
S["java_pairs_compiled_or_executed"] = 0  # reproducibility.py returns (None, True) for any Java text containing "public class"

# ---- 4. per-dataset counts --------------------------------------------------------------------------------------
dev = jl(REPO / "datasets/v8/DEV_MANIFEST.jsonl")
devrec = jl(REPO / "datasets/v8/dev_records.jsonl")
dev_proj = {d["project"].lower() for d in dev} | {d["project"].lower() for d in devrec}
per = {}
for d in DS:
    P = [p for p in pairs if p["dataset"] == d]
    E = [exb[p["pair_id"]] for p in P]
    dur = [e["duration_ms"] for e in E]
    per[d] = {
        "languages": dict(collections.Counter(p["language"] for p in P)),
        "n_pairs": len(P),
        "n_bug_fix": sum(p["change_type"] == "bug_fix" for p in P),
        "n_non_behavioural": sum(p["change_type"] == "non_behavioural" for p in P),
        "projects": sorted({p["project"] for p in P}), "n_projects": len({p["project"] for p in P}),
        "pairs_per_project": dict(collections.Counter(p["project"] for p in P)),
        "executed": len(E), "integrity_ok": sum(e["integrity_ok"] for e in E),
        "verdicts": {v: sum(e["verdict"] == v for e in E) for v in (DIV, NDO, INS)},
        "verdict_x_label": dict(collections.Counter(f"{e['change_type']}->{e['verdict']}" for e in E)),
        "risk_scores": dict(collections.Counter(e["risk_score"] for e in E)),
        "exclusions": sum(x.get("dataset", "").lower() == d.lower() for x in excl),
        "dev_project_name_overlap": sorted({p["project"] for p in P if p["project"].lower() in dev_proj}),
        "duration_ms": {"mean": statistics.mean(dur), "median": statistics.median(dur), "min": min(dur), "max": max(dur), "sum": sum(dur)},
    }
S["per_dataset"] = per
allE = list(exb.values())
S["totals"] = {
    "pairs": len(pairs), "bug_fix": sum(p["change_type"] == "bug_fix" for p in pairs),
    "non_behavioural": sum(p["change_type"] == "non_behavioural" for p in pairs),
    "languages": dict(collections.Counter(p["language"] for p in pairs)),
    "distinct_projects": len({(p["dataset"], p["project"]) for p in pairs}),
    "distinct_project_names_global": len({p["project"].lower() for p in pairs}),
    "verdicts": dict(collections.Counter(e["verdict"] for e in allE)),
    "verdict_x_label": dict(collections.Counter(f"{e['change_type']}->{e['verdict']}" for e in allE)),
    "label_verdict_agreement": sum((e["change_type"] == "bug_fix") == (e["verdict"] == DIV) for e in allE),
    "reproducibility_records_in_results": 0,  # no per-pair reproducibility record is persisted; only the empty exclusions.jsonl
    "duration_ms_mean": statistics.mean(e["duration_ms"] for e in allE),
    "duration_ms_sum": sum(e["duration_ms"] for e in allE),
}
proj_ds = collections.defaultdict(set)
for p in pairs: proj_ds[p["project"].lower()].add(p["dataset"])
S["overlap"] = {
    "cross_dataset_project_names": {k: sorted(v) for k, v in proj_ds.items() if len(v) > 1},
    "dev_manifest_rows": len(dev), "dev_records_rows": len(devrec),
    "dev_projects": len(dev_proj), "dev_families": dict(collections.Counter(d["family"] for d in dev)),
    "dev_project_name_overlap_total": sorted({p["project"] for p in pairs if p["project"].lower() in dev_proj}),
}

# ---- 5. ERS recount, and replay under the current vs fixed profile ----------------------------------------------
trials = collections.Counter()
for r in ers:
    for pid, e in r["ers_results"].items():
        k = "na" if e["passed"] is None else "pass" if e["passed"] else "fail"
        trials[(r["dataset"], pid, k)] += 1
pids = sorted({k[1] for k in trials})
S["ers"] = {
    "perturbations": pids, "n_trials": sum(trials.values()),
    "overall": {pid: {k: sum(trials[(d, pid, k)] for d in DS) for k in ("pass", "fail", "na")} for pid in pids},
    "per_dataset": {d: {pid: {k: trials[(d, pid, k)] for k in ("pass", "fail", "na")} for pid in pids} for d in DS},
    "max_abs_delta": max(abs(e["delta"]) for r in ers for e in r["ers_results"].values()),
    "distinct_orig_risk": sorted({e["orig_risk"] for r in ers for e in r["ers_results"].values()}),
    "predictor": "sbgv8.ers.ActivationStubPredictor (risk = 1 - act_frac; docstring: 'For tests and CLI smoke only')",
}
S["ers"]["totals"] = {k: sum(v[k] for v in S["ers"]["overall"].values()) for k in ("pass", "fail", "na")}

import sbgv8.ers as ersmod
from sbgv8.schema import EvidenceRecord
recs = [EvidenceRecord.from_json(exb[i]["evidence_record_json"]) for i in ids]
def replay(profile_fn):
    old = ersmod.build_profile
    ersmod.build_profile = profile_fn
    try:
        out = {}
        for rec in recs:
            for pid in pids:
                e = ersmod.compute_ers(rec, ersmod.ActivationStubPredictor(), pid, seed=42)
                out[(rec.pair_id, pid)] = (e.passed, round(e.delta, 12), e.pert_decision, e.pert_profile)
        return out
    finally:
        ersmod.build_profile = old
cur = replay(ersmod.build_profile)
recorded = {(r["pair_id"], pid): (e["passed"], round(e["delta"], 12), e["pert_decision"]) for r in ers for pid, e in r["ers_results"].items()}
fixed_src = git("show", f"{FIX_BRANCH}:sbgv8/profile.py")
fix_info = {"fix_commit_in_HEAD": subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", FIX_COMMIT, "HEAD"]).returncode == 0,
            "HEAD_profile_has__relevant": "_relevant(" in (REPO / "sbgv8/profile.py").read_text(),
            "fixed_profile_has__relevant": "_relevant(" in fixed_src,
            "replay_current_matches_recorded": sum(cur[k][:3] == recorded[k] for k in recorded), "n_compared": len(recorded)}
if fixed_src:
    fm = types.ModuleType("profile_fixed"); exec(compile(fixed_src, "profile_fixed.py", "exec"), fm.__dict__)
    fx = replay(fm.build_profile)
    fix_info["fixed_vs_current_pass_or_delta_or_decision_differs"] = sum(fx[k][:3] != cur[k][:3] for k in cur)
    fix_info["fixed_vs_current_P2P3_pert_profile_feature_differs"] = sum(
        fx[k][3] != cur[k][3] for k in cur if k[1] in ("P2", "P3"))
    fix_info["P2P3_features_changed_under_current_profile"] = sorted({f for k in cur if k[1] in ("P2", "P3")
        for f, v in cur[k][3].items() if v != exb[k[0]]["profile"][f]})
    fix_info["P2P3_features_changed_under_fixed_profile"] = sorted({f for k in fx if k[1] in ("P2", "P3")
        for f, v in fx[k][3].items() if v != fm.build_profile(next(r for r in recs if r.pair_id == k[0]))[f]})
S["ers"]["profile_fix_check"] = fix_info

# ---- 6. prediction lock -----------------------------------------------------------------------------------------
lm = R / "locked_predictions_manifest.json"
locked = json.load(open(lm))
rebuilt = json.dumps([{"pair_id": e["pair_id"], "dataset": e["dataset"], "project": e["project"], "family": e["family"],
    "sbg_verdict": e["verdict"], "risk_score": e["risk_score"], "ers_pass_rate": e["ers_pass_rate"],
    "profile_digest": hashlib.sha256(json.dumps(e["profile"], sort_keys=True).encode()).hexdigest(),
    "evidence_digest": hashlib.sha256(e["evidence_record_json"].encode()).hexdigest()} for e in ex], indent=2, sort_keys=True)
S["prediction_lock"] = {
    "claimed_package_sha256": lock_meta["package_sha256"], "sha256_locked_manifest_file": sha256(lm),
    "match": sha256(lm) == lock_meta["package_sha256"],
    "manifest_rebuilt_from_execution_results_identical": rebuilt == lm.read_text(encoding="utf-8"),
    "n_locked": len(locked),
    "hash_scope": "SHA-256 of locked_predictions_manifest.json bytes only; blinded cases, CSV, pair_manifest, execution/ERS JSONL are NOT covered",
    "external_timestamp_or_signature": False,
    "file_sha256": {f.name: sha256(f) for f in sorted(R.iterdir()) if f.is_file()},
}

# ---- 7. adjudication status and blinding --------------------------------------------------------------------------
dec_cols = ("adjudicator_verdict", "adjudicator_confidence", "adjudicator_id", "notes")
S["adjudication"] = {
    "template_rows": len(tmpl), "rows_with_any_decision": sum(any((r.get(c) or "").strip() for c in dec_cols) for r in tmpl),
    "blinded_cases": len(blind),
    "label_leak_case_id_contains_non_behav_or_bug": sum(("non_behav" in c["case_id"]) or ("_bug_" in c["case_id"]) for c in blind),
    "label_leak_description_says_fix": sum(bool(re.search(r"\bfix\b", c["change_description"], re.I)) for c in blind),
    "label_leak_patch_comment_buggy_or_fixed": sum(bool(re.search(r"Buggy|Fixed", c["patch_diff"])) for c in blind),
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(S, indent=2, sort_keys=False, default=str), encoding="utf-8")

# self-checks: the arithmetic the report relies on
assert S["ers"]["n_trials"] == len(ers) * len(pids)
assert sum(v["n_pairs"] for v in per.values()) == len(pairs)
print(json.dumps({k: S[k] for k in ("totals", "ers", "prediction_lock", "adjudication")}, indent=1, default=str)[:6000])
