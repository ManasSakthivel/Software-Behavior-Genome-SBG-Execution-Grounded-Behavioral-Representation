# Claim-evidence notes (closeout)

Matrix: `CLAIM_EVIDENCE_MATRIX.csv` (28 rows). Built by `scripts/build_claim_matrix.py`. Recomputation helpers are in `scripts/`. The SBG repository (`~/Desktop/SBG-V8-LINUX`) was read only. Nothing was committed or changed there.

## What was checked, and how

- Manuscript text was read from the **working-tree** `paper/IEEE_ACCESS_V8_FINAL/sections/*.tex`. That tree has 61 uncommitted changes, so the text read is not the committed HEAD text.
- Raw sources were checked against tracked files at HEAD, and against `research/v8-mac-hardening` where the manuscript names it.
- Recomputations were run on committed files only. Scripts: `recompute_v8_test_auroc.py`, `recompute_edit_size_baseline.py`, `bootstrap_v8_ci.py`, `build_claim_matrix.py`.

## Results of the checks

| Claim | Result |
|---|---|
| 312 dev records, 258 labelled | MATCH |
| Plain testing (B1) risk 31/183 = 0.169 | MATCH (recomputed exactly) |
| V7-B gate 61 verdicts, 13 wrong, 0.213 | MATCH on the stored `v7b_verdict` field |
| Dev records byte-identical on Linux and mac branches (MD5 07e57a80) | MATCH |
| Held-out test split: 956 pairs, 547/409, 22 programs | MATCH (recounted, checksums of the three named inputs match) |
| SBG V5 test AUROC 0.693742 | MATCH (recomputed) |
| Reversed edit-size AUROC 0.875922 | MATCH (recomputed) |
| SBG V5 bootstrap CI | Approximate MATCH: my 0.6587–0.7280 against recorded 0.6593–0.7266 |

## Findings that need an author decision

1. **Manuscript contradicts the repository on held-out evaluation (C13).** The abstract says "no held-out benchmark was evaluated". `artifacts/paper_evidence/V8_TEST_EVALUATION.json` records a single-run, CONFIRMATORY-BY-FREEZE test-split evaluation of 956 pairs. Its verdict is NOT DEMONSTRATED: SBG V5 0.694 against reversed edit size 0.876. The manuscript does not report this. `FINAL_METRICS_V4.json` labels the split `v8_test_burned`. The results section also describes a frozen-threshold study on held-out projects (C14). The sentence must either be narrowed or the evaluation disclosed. I have **not** changed the manuscript text.
2. **Headline abstract CI has no reproducible source (C06).** The +1.6 pp matched-coverage difference and its interval [-6.6, +16.3] depend on `scripts/stats_recompute.py` and `audit/stats_summary.json`. Neither is tracked, neither exists on disk, and neither exists on `research/v8-mac-hardening`. The B1 bootstrap interval [0.086, 0.354] (C03) has the same problem.
3. **Security counts cannot be traced (C20).** The 25-attack macOS result cites `audit/security_rerun_darwin.json`, which is absent everywhere checked. `results/v8_mac_security/` holds 2 tracked files that I did not open.
4. **Real-execution analogue (C19)** has a matrix but no run directories, and the tree was dirty when it was produced. It can be cited only as an unverified analysis.

## Categories used

- AUTHENTIC_COMPLETED: raw output present and at least partly recomputed or checked.
- SYNTHETIC_DEVELOPMENT_FIXTURE: construction labels and template-derived variants.
- INVALID_HISTORICAL: the five-dataset 250-pair artifact (C15). Its executor did not run programs.
- PROPOSED_UNEXECUTED: the adjudication protocol and template, and the external pilot.
- INCOMPLETE_OR_UNVERIFIABLE: cited, but the source is missing or was not checked in this pass.

Rows marked NOT_VERIFIED were not checked in this pass. Those are not confirmed, and they should not be stated as confirmed.

## Limits of this pass

- Baseline rules B4 and B5 were not recomputed (C05).
- The edit-size CI and the Holm p-value (C11, C12) were taken from the recorded JSON.
- Test-split provenance: `benchmark/corpus/fresh_programs` has 122 `.py` files. Whether they are synthetic was not established.
- No platform was recorded for the V8 test evaluation. Its platform column is blank.
- The frozen-snapshot pytest run (PID 94433) is separate. It was still running at 44% when checked, and its exit code is not recorded here.
