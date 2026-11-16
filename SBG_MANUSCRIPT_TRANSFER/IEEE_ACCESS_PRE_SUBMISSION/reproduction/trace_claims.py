#!/usr/bin/env python3
"""A2 task 2: traceability table  claim -> artifact(:line) -> generating script -> command -> verified?
For every claim: (1) the artifact exists in git HEAD and contains the quoted value at a line (searched, not assumed);
(2) the producing script exists in HEAD; (3) whether script / artifact are pinned (sha256) in some freeze file (from hash_verification.json);
(4) whether the artifact is unchanged vs HEAD in the working tree.  It does NOT re-derive statistics (A3)."""
import json, pathlib, re, subprocess, hashlib
REPO = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG"); PKG = pathlib.Path(__file__).resolve().parents[1]
hv = json.loads((PKG / "results/raw/repro/hash_verification.json").read_text())
pinned = {}
for r in hv["rows"]:
    if r.get("path"):
        pinned.setdefault(r["path"], []).append((pathlib.Path(r["source"]).name, r["status"]))
head = set(subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True).stdout.splitlines())
P = "artifacts/paper_evidence/"; F = "artifacts/final/"; X = "experiments/final/"
# (claim, artifact, search-regex (value as written in file), script, command)
C = [
 ("V10 H1: AUROC(sbg_v5)=0.8968, p=0.0005 (n=638)", P+"V10_INDEPENDENT_EVALUATION.json", r'"auroc": 0.896768', X+"evaluate_v10.py", "PYTHONHASHSEED=0 python experiments/final/evaluate_v10.py run  (refuses unless FREEZE_V10 hashes match; single-run)"),
 ("V10 H1 Holm p_adj=0.003", P+"V10_INDEPENDENT_EVALUATION.json", r'"H1_sbg_v5_above_chance"', X+"evaluate_v10.py", "same"),
 ("V10 H2: E+V5 - E = +0.2545 [0.2178,0.2851]", P+"V10_INDEPENDENT_EVALUATION.json", r'"delta": 0.254498', X+"evaluate_v10.py", "same"),
 ("V10 H3: V5 - edit(fwd) = +0.2807", P+"V10_INDEPENDENT_EVALUATION.json", r'"delta": 0.280721', X+"evaluate_v10.py", "same"),
 ("V10 H4: EX+V5 - EX = +0.0063 [-0.069,0.068], p=0.81 (null)", P+"V10_INDEPENDENT_EVALUATION.json", r'"delta": 0.006299', X+"evaluate_v10.py", "same"),
 ("V10 H5: V6 - V5 = +0.0029, Holm p_adj=0.090 (not rejected)", P+"V10_INDEPENDENT_EVALUATION.json", r'"delta": 0.002889', X+"evaluate_v10.py", "same"),
 ("V10 H6: EX+V6 - EX = +0.0085 (null)", P+"V10_INDEPENDENT_EVALUATION.json", r'"delta": 0.008481', X+"evaluate_v10.py", "same"),
 ("V10 state-genome AUROC 0.917 (> SBG-V5 0.897)", P+"V10_INDEPENDENT_EVALUATION.json", r'"auroc": 0.9171', X+"evaluate_v10.py", "same"),
 ("V10 edit forward 0.616 / reversed 0.384", P+"V10_INDEPENDENT_EVALUATION.json", r'"auroc": 0.616046', X+"evaluate_v10.py", "same"),
 ("V10 exact-zero rate 0.3464 (equivalent 0.6364, changed 0.0564)", P+"V10_INDEPENDENT_EVALUATION.json", r'"exact_zero_rate": 0.3464', X+"evaluate_v10.py", "same"),
 ("V10 SC-6 changed zero-rate 0.7391 = 17/23", P+"V10_INDEPENDENT_EVALUATION.json", r'"sbg_v5": 0.7391', X+"evaluate_v10.py", "same"),
 ("V10 scored pairs (input of the above)", F+"pairs_v10_test_v6exp.jsonl", r'.', X+"score_v6_experimental.py", "PYTHONHASHSEED=0 python experiments/final/score_v6_experimental.py --design v10 --split test"),
 ("V9c-val H1: AUROC(sbg_v5)=0.7514, p=0.0005 (n=432)", P+"V9_VAL_EVALUATION.json", r'"auroc": 0.751372', X+"evaluate_v9.py", "PYTHONHASHSEED=0 python experiments/final/evaluate_v9.py run --split val  (refuses unless FREEZE_V9 matches)"),
 ("V9c-val H2: ES-E = +0.1122", P+"V9_VAL_EVALUATION.json", r'"delta": 0.112183', X+"evaluate_v9.py", "same"),
 ("V9c-val H3: V5 - edit(fwd) = +0.1402", P+"V9_VAL_EVALUATION.json", r'"delta": 0.140228', X+"evaluate_v9.py", "same"),
 ("V9c-val H4: ESX-EX = +0.0210 [-0.005,0.048], p=0.117 (null)", P+"V9_VAL_EVALUATION.json", r'"delta": 0.021016', X+"evaluate_v9.py", "same"),
 ("V9c-val zero rate 0.3704", P+"V9_VAL_EVALUATION.json", r'"fraction_sbg_v5_exactly_zero": 0.3704', X+"evaluate_v9.py", "same"),
 ("V9c-val matched-set concordance SBG 0.806 vs edit 0.924", P+"V9_VAL_EVALUATION.json", r'"concordance": 0.923611', X+"evaluate_v9.py", "same"),
 ("V8 test SBG-V5 AUROC 0.6937 (headline 0.694)", P+"V8_TEST_EVALUATION.json", r'"auroc": 0.693742', X+"evaluate_v8.py", "python experiments/final/evaluate_v8.py run --split test  (single run; --allow-overwrite-never-use suppressed flag exists)"),
 ("V8 test reversed edit-size 0.8759 (headline 0.876)", P+"V8_TEST_EVALUATION.json", r'"auroc": 0.875922', X+"evaluate_v8.py", "same"),
 ("V8 test scored pairs (non-stale subset)", F+"v8_test_nonstale/pairs_test.jsonl", r'.', X+"run_chunked.py", "python experiments/final/run_chunked.py --split test --pairs-dir artifacts/final/v8_test_nonstale --tag v8test"),
 ("BugsInPy SBG-V5 AUROC 0.497 (SP-2 excluded rescoring)", P+"EXTERNAL_RESCORE_V8.json", r'"auroc": 0.497', X+"rescore_external_v8.py", "PYTHONHASHSEED=0 python experiments/final/rescore_external_v8.py"),
 ("BugsInPy SBG-V5 AUROC 0.410 (valid pairs, 147)", F+"BUGSINPY_output_free_v7.json", r'"sbg_v5_auroc_valid": 0.409917', X+"external_bugsinpy.py", "python experiments/final/external_bugsinpy.py [fetch|build|score|analyse]"),
 ("QuixBugs SBG-V5 AUROC 0.388 (all 152)", F+"QUIXBUGS_output_free_v7.json", r'"sbg_v5_auroc": 0.387723', X+"external_quixbugs.py", "python experiments/final/external_quixbugs.py [prepare|score|analyse]"),
 ("QuixBugs 0.444 (111 pairs, excl. invalid negatives & SP-2)", P+"EXTERNAL_NEGATIVE_AUDIT.json", r'"sbg_v5_auroc": 0.4444', X+"audit_external_negatives.py", "python experiments/final/audit_external_negatives.py"),
 ("QuixBugs within-program stratified 0.3884", P+"DIAGNOSTIC_EXTERNAL.json", r'"auroc": 0.3884', X+"diagnose_external.py", "python experiments/final/diagnose_external.py"),
 ("Edit-size confound diagnostics (dev/train)", P+"DIAGNOSTIC_EDIT_SIZE.json", r'"purpose"', X+"diagnose_edit_size.py", "PYTHONHASHSEED=0 python experiments/final/diagnose_edit_size.py"),
 ("Ablations (component / weight-model / shortcut controls)", P+"ABLATIONS.json", r'"component_ablation_v5"', X+"build_ablations.py", "python3 experiments/final/build_ablations.py"),
 ("Post-hoc V10 supplement (zero-rate, concordance)", P+"V10_POSTHOC_SUPPLEMENT.json", r'.', X+"posthoc_v10_supplement.py", "PYTHONHASHSEED=0 python experiments/final/posthoc_v10_supplement.py"),
 ("Zero-score population (all scored files)", P+"raw/zero_score_population_v1.json", r'.', X+"zero_score_population.py", "python experiments/final/zero_score_population.py  (needs 4 UNTRACKED v8-dev files)"),
 ("Zero-score root cause (class counts)", P+"ZERO_SCORE_ROOT_CAUSE_V1.md", r'.', X+"diagnose_zero_scores.py", "python experiments/final/diagnose_zero_scores.py"),
 ("Weight fitting (V5 weights 0.50/0.25/0.25 fixed)", P+"WEIGHT_FITTING.json", r'.', X+"fit_weights.py", "python experiments/final/fit_weights.py"),
 ("'35/35 trace verifications'", P+"RESEARCH_STATUS_V4.md", r'.', X+"verify_trace_v4.py", "python experiments/final/verify_trace_v4.py"),
 ("'10/10 consistency checks'", "docs/current/REPRODUCTION.md", r'10/10', X+"consistency_check.py", "python experiments/final/consistency_check.py"),
]
rows = []
for claim, art, rx, script, cmd in C:
    ap = REPO / art
    line = None
    if ap.exists() and rx != ".":
        for i, l in enumerate(ap.read_text(errors="ignore").splitlines(), 1):
            if re.search(rx, l): line = i; break
    art_ok = ap.exists() and (rx == "." or line is not None)
    git_clean = subprocess.run(["git", "-C", str(REPO), "diff", "--quiet", "HEAD", "--", art]).returncode == 0
    sp = pinned.get(script, []); ap_ = pinned.get(art, [])
    rows.append(dict(claim=claim, artifact=art, line=line, artifact_in_HEAD=art in head, value_found=art_ok, artifact_clean_vs_HEAD=git_clean,
                     script=script, script_in_HEAD=script in head, script_pinned_in=sorted({s for s, st in sp}),
                     script_hash_status=sorted({st for s, st in sp}), artifact_pinned_in=sorted({s for s, st in ap_}), command=cmd))
(PKG / "results/raw/repro/traceability.json").write_text(json.dumps(rows, indent=1))
md = ["| # | claim | artifact:line | script (pinned in) | command | value found / in HEAD / clean |", "|---|---|---|---|---|---|"]
for i, r in enumerate(rows, 1):
    md.append(f"| {i} | {r['claim']} | `{r['artifact']}`:{r['line'] or '-'} | `{r['script']}` ({', '.join(r['script_pinned_in']) or '**NOT PINNED**'}{' [' + '/'.join(r['script_hash_status']) + ']' if r['script_pinned_in'] else ''}) | `{r['command']}` | {'Y' if r['value_found'] else '**N**'} / {'Y' if r['artifact_in_HEAD'] else '**N**'} / {'Y' if r['artifact_clean_vs_HEAD'] else '**N**'} |")
(PKG / "results/raw/repro/traceability.md").write_text("\n".join(md) + "\n")
print(len(rows), "claims;", sum(r["value_found"] for r in rows), "values found;", sum(r["artifact_in_HEAD"] for r in rows), "artifacts in HEAD;", sum(r["script_in_HEAD"] for r in rows), "scripts in HEAD;", sum(bool(r["script_pinned_in"]) for r in rows), "scripts pinned")
for r in rows:
    if not (r["value_found"] and r["artifact_in_HEAD"]): print("PROBLEM", r["claim"], r["artifact"])
