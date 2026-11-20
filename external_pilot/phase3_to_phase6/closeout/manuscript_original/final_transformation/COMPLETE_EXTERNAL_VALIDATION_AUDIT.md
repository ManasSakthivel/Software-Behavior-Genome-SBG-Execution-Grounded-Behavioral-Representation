# Complete external-validation audit (earlier `reports/external_validation/` workstream)
New file; linked from `../README.md`. Static inspection only; nothing re-run; no original artifact modified. Case-level detail: `EXTERNAL_CASE_EVIDENCE_REGISTRY.json`. Upstream existence was checked against the public GitHub API on 2026-11-20 (read-only metadata queries).

## What this workstream is
A 2026-11-16 effort (baseline branch `remediation/sbg-v4`, commit `3425693b`) that evaluated **SBG V5-era features** (`sbg_v5` column), not the V8 estimator, on QuixBugs, BugsInPy, Bugs.jar, Codeflaws and SeqCoBench, with AUROC as the metric. It is a different method and question from the V8 manuscript (false-assurance risk of NDO verdicts).

## Per-benchmark findings (the ten questions)
| Benchmark | 1 Real project | 2 Commit authentic | 3 Buggy+fixed checked out | 4-5 Built / original tests | 6-7 SBG run, raw logs | 8 Reproducible | 9 Dev overlap | 10 Used to tune |
|---|---|---|---|---|---|---|---|---|
| QuixBugs (40) | Yes (`jkoppel/QuixBugs`) | `4257f44b…` resolves (2022-08-29) | Real upstream files are in `external/quixbugs` | Programs executed on `json_testcases` inputs by the harness; QuixBugs' own test drivers not used | Per-pair feature CSVs exist; raw traces not in worktree | Scripts present; they point to a path (`IEEE_ACCESS_PRE_SUBMISSION/...`) absent here | **31 of 40 programs are in the V8 development corpus** | **Yes.** Harness was repaired (FIX-QB-01..03) after a below-chance AUROC; the repaired result (+0.2188) is post hoc |
| BugsInPy (51 eligible) | Yes | Manifest commit `11c5f1ee…` resolves; sampled buggy/fixed commits (PySnooper 1-3) resolve. The earlier tag `d27c62c` does **not** resolve (HTTP 422) | Function-level units fetched verbatim at recorded commits (`external/bugsinpy`) | Standard-library-only function units; project tests not run | Per-case results not in the worktree (earlier pairs file referenced outside it) | No | **43 of 51 eligible bugs are in V8 dev** | Unknown; the failure analysis re-diagnosed and re-scored after a below-chance result |
| Bugs.jar (24 "cases") | Project names real | Claimed `e09214b` returns 404 | **No checkout.** 8 hand-written snippets in `evaluate_bugsjar.py`, each used as 1 positive + 2 synthetic negatives | Snippets compiled with `javac` and traced; no project build or tests | Result CSV present; scores 1.000 flagged by the project's own perfect-score audit | Script self-contained | None by name | Unknown |
| Codeflaws (36) | Codeforces problems | Release tag `release-2017` not checked | **No checkout.** 12 hand-written C programs in `evaluate_codeflaws.py`; ids look like real Codeflaws ids but were not verified | Compiled with `clang`, traced on chosen inputs; no Codeflaws test harness | Same | Script self-contained | None by name | Unknown |
| SeqCoBench (1,134 problems) | MBPP problems | Not fetched | LLM-generated transformations, not bug fixes | n/a | n/a | n/a | None | Static shortcut reached AUROC 0.824; reported as such |
| Defects4J / Bears / ManyBugs | Yes | Defects4J tag resolves (`v2.0.0`); Bears tag does not | Not attempted | Not attempted | 0 pairs | n/a | n/a | n/a |

## Findings
1. **No case qualifies as external evaluation.** The only benchmark with real upstream code, authentic commits and partial execution (QuixBugs, BugsInPy units) is also development data in V8 (74 of the 91 real-code cases) or was tuned on (QuixBugs repair). Bugs.jar and Codeflaws are hand-written stand-ins.
2. **Negatives are synthetic.** QuixBugs `negative_sp-*` and Bugs.jar/Codeflaws identity/refactor negatives are constructed from the positive; labels come from construction.
3. **Wrong method.** The results concern V5 features and AUROC, not the V8 NDO risk estimand.
4. **Own audits agree.** The workstream's `SBG_BUGSJAR_PERFECT_SCORE_AUDIT.md` and `SBG_CODEFLAWS_PERFECT_SCORE_AUDIT.md` show lexical diffs already reach AUROC 1.0; its claim matrix marks CLM-04/05 contradicted.
5. **Overstated headings.** "Valid Cross-Language Unit Benchmark" and "Evaluated & Recomputed (100% Passing)" in the manifest are not supported by the checkouts present.

## Legitimate contributions
Forensic diagnosis of why earlier below-chance results arose (input-serialisation crashes in 27/40 QuixBugs programs; dummy inputs in 34/47 BugsInPy functions); real QuixBugs and BugsInPy upstream material with verified commits; a worked demonstration that lexical baselines saturate unit-level benchmarks.

## Overall
It does **not** supply a held-out external validation of V8. Details of the decision: `EXTERNAL_VALIDATION_CLAIM_DECISION.md`.
