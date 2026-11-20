# SBG V7: Failure-to-Requirement Matrix

Scope: forensic, read-only. Branch `feature/sbg-v7-architecture` at `197039a1` (tag `v6-holdout-complete`). Every number below was read from the cited file; nothing was re-run. Where a figure was supplied in the task brief and not found verbatim in a file, it is flagged "(not located verbatim)".

Root-cause categories: **label**, **representation**, **instrumentation**, **activation**, **generalisation**, **leakage**, **process**.
Subsystem areas: **A** Exploration, **B** Execution Capture, **C** Static Context, **D** Evidence Fabric, **E** State/Invariant, **F** Multi-view Graph, **G** Alignment, **H** Divergence/Impact, **I** Uncertainty/Decision, **J** Prediction, **K** Validation harness, **L** Reproducibility/Governance.

Evidence path prefixes: `V6R` = `reports/v6_redesign/`, `AUD` = `artifacts/v6/audit/`, `HO` = `artifacts/v6/holdout/`, `PE` = `artifacts/paper_evidence/`.

## 1. Failure / finding to requirement matrix

| ID | Failure / finding (verified figure) | Root cause | Evidence file | Requirement |
|---|---|---|---|---|
| F-01 | SC-6 return-value blindness: trace channel never sees return values; DEV SC-6 AUROC vs equivalents 0.307 (d_v6), 0.305 (V5); d_R 0.866, delta_out 0.874; holdout v8 C0g 0.54, v10 0.32 | instrumentation | `AUD/DIFF_SC6_AUDIT.json`; `V6R/SBG_V6_FAILURE_ANALYSIS.md` item 1; `V6R/SBG_V6_ARCHITECTURE_DECISION_REPORT.md` s2 | R-04, R-12, R-17 |
| F-02 | SP-8 (extract-function) labels not behaviour-preserving: 47 EQUIVALENT pairs where variant returns None/raises (`exception_type_differs`) | label | `AUD/LABEL_ADJUDICATION_SUMMARY.json`; `AUD/DIFF_SC6_AUDIT.json` (`equiv_labelled_with_output_diff_by_type` SP-8 47); generator `benchmark/transformations/preserving/transformations/sp8_extract_function.py` | R-22, R-23 |
| F-03 | SP-11 repr artifact: 42 EQUIVALENT pairs differ only by container repr (deque vs list), values equal; delta_out is the faulty instrument | instrumentation | `AUD/LABEL_ADJUDICATION_SUMMARY.json`; generator `.../sp11_equiv_data_structure.py` | R-05 |
| F-04a | 357 of 1332 CHANGED pairs show no output difference (SC-4 contributes 102) | label / activation | `AUD/DIFF_SC6_AUDIT.json` (`changed_without_observed_diff`) | R-03, R-16, R-22 |
| F-04b | ...of which 61 are changed code never exercised by declared inputs (test inadequacy, not equivalence) | activation | `AUD/LABEL_ADJUDICATION_SUMMARY.json` | R-01, R-16 |
| F-04c | ...of which 116 unresolved: trace and output identical (equivalent mutant or insufficient discrimination; SC-4 33, SC-3 27); 180 are masked (internal trace differs) | label | `AUD/LABEL_ADJUDICATION_SUMMARY.json`; `V6R/SBG_V6_FINAL_ARCHITECTURE.md` s7 | R-03, R-16, R-19 |
| F-05 | Generator fingerprinting: CONV GBM 0.970 program-grouped (0.972 in decision report) falls to 0.742 under leave-mutation-types-out; label is a pure function of mutation type (SC=1, SP=0) | label / leakage | `AUD/LEAKAGE_AUDIT.json` (`label_pure_function_of_type: true`, `gbm_cv_schemes`); `V6R/SBG_V6_ARCHITECTURE_DECISION_REPORT.md` s3 | R-22, R-25, R-21 |
| F-06 | Reversed edit size 0.771 on DEV (construction artifact: SC mean 5.4 diff lines vs SP 11.3); 0.772 on v8 test, 0.847 on BugsInPy, 0.325 on QuixBugs declared (below chance on real bugs) | label / generalisation | `V6R/SBG_V6_ARCHITECTURE_DECISION_REPORT.md` s4; `V6R/SBG_V6_FINAL_HOLDOUT_RESULTS.md`; `docs/current/EDIT_SIZE_REDESIGN.md` | R-09, R-25 |
| F-07 | 596 duplicate variant groups cover 1713 of 2392 pairs; 1275 unique variant files; 816 base x type groups; 9 cross-type duplicate groups; 16-18 straddling groups in leave-type-out folds (0 in program-grouped folds) | leakage | `AUD/DUPLICATE_AUDIT.json`; `AUD/LEAKAGE_AUDIT.json` | R-24 |
| F-08 | BugsInPy coverage 28.5% (57/200 ACTIVATED); UNKNOWN causes: nondeterministic base 60, unsupported signature 49, import error 4; 76% of real fixes abstain | activation / instrumentation | `V6R/SBG_V6_ABSTENTION_AND_COVERAGE_REPORT.md`; `V6R/SBG_V6_FAILURE_ANALYSIS.md` item 3 | R-02, R-06, R-27 |
| F-09 | QuixBugs declared: 36 pairs of 9 programs with no `json_testcases` are ineligible (UNKNOWN, kept in denominator); declared coverage 61.2% | activation | `V6R/SBG_V6_FINAL_HOLDOUT_RESULTS.md` (deviations); `V6R/SBG_V6_ABSTENTION_AND_COVERAGE_REPORT.md` | R-02, R-27 |
| F-10 | V6 loses to conventional features: BugsInPy CONV+C0g vs CONV (LR) -0.103 [-0.148,-0.054] Holm p=0.013; QuixBugs canonical CONV+C0g vs CONV (GBM) -0.123 (Holm 0.007); v8 test CONV GBM 0.981 vs C0g 0.877 | representation / generalisation | `V6R/SBG_V6_EXTERNAL_GENERALISATION_REPORT.md`; `V6R/SBG_V6_FINAL_CLAIM_EVIDENCE_MATRIX.md` ("NOT SUPPORTED") | R-20, R-25 |
| F-11 | E (activation) columns: alpha alone AUROC 0.463 on DEV; C0g vs C1 flips sign across benchmarks (v8 C0g .768 > C1 .758; v10 C1 .878 > C0g .851; BugsInPy C1 .557 > C0g .505; QuixBugs C0g > C1); acts as moderator only | representation | `V6R/SBG_V6_FINAL_ARCHITECTURE.md` s2; `V6R/SBG_V6_FINAL_HOLDOUT_RESULTS.md` | R-20 |
| F-12 | No pristine holdout: v8 test (22-26 programs) and v10 (19) already observed with V5; all five holdouts "NOT pristine" | process / leakage | `V6R/SBG_V6_FINAL_ARCHITECTURE.md` s9.6; `V6R/SBG_V6_FINAL_CLAIM_EVIDENCE_MATRIX.md` header | R-26 |
| F-13 | Harness group-timeout hang: first re-extraction 2341/2392 identical, 51 lost to group timeout (`math_gray_code`); per-pair re-run 2392/2392 identical; earlier v8 test single-process scoring stalled at ~525 pairs three times | instrumentation | `V6R/SBG_V6_FINAL_ARCHITECTURE.md` s8, s9.8; `PE/RESEARCH_STATUS.md` (procedural disclosure) | R-07 |
| F-14 | Thread oversubscription (earlier slowness; 31 s per full re-fit once one thread per worker) | instrumentation / process | `V6R/SBG_V6_FINAL_ARCHITECTURE.md` s8 | R-07, R-29 |
| F-15 | V6 alone does not generalise across mutation types: pooled LOFO ~0.52 for every candidate; V6 GBM falls 0.860 -> 0.582 under type holdout | generalisation | `V6R/SBG_V6_FINAL_ARCHITECTURE.md` s2; `AUD/LEAKAGE_AUDIT.json` (V6 leave-mutation-types-out 0.582) | R-21 |
| F-16 | V5 external below chance ("external corpora already below chance for SBG, per STATUS.md"); V6 BugsInPy 0.505 (chance), AUPRC 0.281 vs prevalence 0.275 | generalisation | `V6R/SBG_V6_ARCHITECTURE_DECISION_REPORT.md` s4 (cites `STATUS.md`); `V6R/SBG_V6_FINAL_HOLDOUT_RESULTS.md`; `PE/REAL_BUG_GENERALISATION_AUDIT.md` | R-27, R-21 |
| F-17 | Stale-program exclusions: v8 base files edited after variants generated; 8/100 programs stale on regeneration (e.g. `math_count_set_bits` 45/48 stale); 4 programs / 163 pairs excluded a priori from v8 test | process | `PE/DIAGNOSTIC_V8_STALE_VARIANTS.json`; `PE/RESEARCH_STATUS.md` | R-30 |
| F-18 | Test set observed before freeze: v6 test results committed in the same commit as the benchmark (`9a9104f`, 2026-09-28); preregistration committed 5 days after; wall-clock ordering unprovable | process / leakage | `docs/current/TEST_SET_CHRONOLOGY.md` | R-28, R-26 |
| F-19 | Selection rule operationalised after ablation observed; C0g vs C1 comparison (PROTOCOL_V2) defined after stage-1 results seen: "not fully preregistered" | process | `V6R/SBG_V6_FINAL_ARCHITECTURE.md` s5; `AUD/SELECTION_RULE_DISCLOSURE.md` | R-31 |
| F-20 | Abstention fill: 76% BugsInPy abstain; ranked ones sit at common value 0.3659 (= DEV median fill, uninformative ties); identical feature vectors give identical scores (0.3299 for many SC-1 pairs) | representation / activation | `V6R/SBG_V6_FAILURE_ANALYSIS.md` items 2-3 | R-18, R-10 |
| F-21 | Structural false positives: SP-5 (loop rewrite) and SP-8 negatives score highest (mean 0.60-0.64 vs ~0.40 others) because they genuinely change traces | representation | `V6R/SBG_V6_FAILURE_ANALYSIS.md` item 5 | R-15, R-14 |
| F-22 | Small point edits unrankable: SC-1/SC-3 with 2 edited lines score 0.55/0.64 (CONV 0.84/0.86) | representation | `V6R/SBG_V6_FAILURE_ANALYSIS.md` item 2 | R-13, R-16 |
| F-23 | Output-free channel blind to return values by design; return-state block d_R (C1+R 0.817 vs C1 0.759 DEV) kept only as separate R2 regime; differential testing alone 0.787 LR / 0.805 GBM | instrumentation / process | `V6R/SBG_V6_FINAL_ARCHITECTURE.md` s4 | R-04, R-11 |
| F-24 | Nondeterminism: 60 BugsInPy bases nondeterministic; source of nondeterminism "not investigated further" | instrumentation | `V6R/SBG_V6_ABSTENTION_AND_COVERAGE_REPORT.md`; `V6R/SBG_V6_FAILURE_ANALYSIS.md` (last line) | R-06 |
| F-25 | No human adjudication of labels; no new-input executions to separate equivalent mutants from weak inputs; protocol's "25% unactivated inputs" ablation not run | label / process | `V6R/SBG_V6_FINAL_ARCHITECTURE.md` s7, s9.5, s9.7 | R-03, R-22 |
| F-26 | Duplicate-aware effective N: dedup-weighted CONV LR moves 0.865 -> 0.903, so duplication inflates sides non-uniformly | leakage | `V6R/SBG_V6_FINAL_ARCHITECTURE.md` s6 | R-24 |
| F-27 | Pairwise-conflict: one CONV feature vector appears with conflicting labels (635 duplicate CONV-vector groups, 1890 rows) | label / representation | `AUD/LEAKAGE_AUDIT.json` | R-24, R-22 |
| F-28 | Not reproduced on a different machine or Python version | process | `V6R/SBG_V6_FINAL_ARCHITECTURE.md` s8 | R-29 |

## 2. Requirements with acceptance tests

Thresholds below are proposed design targets, not observed results. Each is evaluated on a sealed set (R-26) unless stated.

| ID | Area | Requirement | Measurable acceptance test |
|---|---|---|---|
| R-01 | A Exploration | Coverage-directed input exploration must reach the edited lines/branches of the variant before a pair is scored. | Changed-line coverage achieved on >= 95% of CHANGED pairs in the sealed set (V6 DEV baseline: 61 of 1332 CHANGED = 4.6% never exercised; `AUD/LABEL_ADJUDICATION_SUMMARY.json`). Reported per mutation type. |
| R-02 | A Exploration | Signature-aware driver synthesis (arguments from type hints, defaults, call sites, docstrings) and provision of inputs for units lacking declared tests. | On BugsInPy-style units, "unsupported signature" UNKNOWN <= 10% (V6: 49 of 200) and QuixBugs programs without `json_testcases` <= 0 ineligible (V6: 36 pairs / 9 programs). |
| R-03 | A Exploration | Budgeted differential/mutation-guided search for inputs that reveal divergence, used to adjudicate "no output diff" CHANGED pairs. | Each of the 357 no-output-diff DEV pairs ends with a recorded verdict in {divergence-found, equivalent-within-budget(N inputs), unresolved}; unresolved <= 10% (V6: 116 unresolved = 32.5% of 357). Budget N and seed logged. |
| R-04 | B Capture | Capture return values, raised exception type/message, and global/argument mutation per call as first-class observations, tagged by channel. | Unit test: a return-expression-only mutant (SC-6 style) yields a nonzero observation difference in 100% of a 20-case regression set; held-out-type SC-6 AUROC lower 95% CI bound > 0.5 (V6 DEV 0.307 / holdout v8 0.54, v10 0.32). |
| R-05 | B Capture | Type-normalised, semantic value canonicalisation (container type, ordering where specified, float tolerance) before any output comparison. | Of the 42 SP-11 DEV pairs, 0 flagged as output-different unless values differ after canonicalisation; canonicaliser has property tests (equal values, differing reprs). |
| R-06 | B Capture | Controlled determinism: pinned seeds, time/random/hash-order/env control; nondeterminism detected by repeated runs and root-caused into classes (not just flagged). | Repeat-run identical traces for >= 99% of units that are not intrinsically nondeterministic; every one of the 60 BugsInPy-style nondeterministic bases is assigned a cause class or an explicit "intrinsic" code. |
| R-07 | B Capture | Per-unit hard timeout and process isolation (no group-level timeout that can drop other pairs); thread caps enforced. | Three consecutive full extractions on the same machine give 0 pairs lost to timeouts attributable to a different unit (V6 first attempt lost 51) and 100% bitwise-equal feature files; thread count asserted = 1 per worker. |
| R-08 | C Static | Static context: signatures, types, call graph, purity/side-effect summaries and slice of edited statements, available independent of execution. | For >= 95% of units the static context record is produced without execution; consumed by R-02 and R-16; schema-validated. |
| R-09 | C Static | Edit-size-neutral representation: static/dynamic features must not be monotone in raw diff size, and edit size reported as a mandatory covariate. | On the sealed set, reversed edit size AUROC within [0.45, 0.55] overall (V6: 0.771 DEV, 0.847 BugsInPy) AND model AUROC reported inside edit-size strata with non-inferiority margin declared in advance. |
| R-10 | D Evidence | Evidence fabric: every pair has a typed evidence record (channel, status ACTIVATED/NOT_ACTIVATED/UNKNOWN/NONDET, reason code, provenance hashes); no silent drops or imputation. | Reconciliation script: counts in = counts out for every benchmark (pairs in manifest == pairs with record); 0 pairs imputed without a status; reason codes enumerated. |
| R-11 | D Evidence | Channels kept separate and labelled by regime (oracle-free trace, paired-output differential, static); each reported number names its regime. | Results schema rejects a metric without a `regime` field; claim matrix generated from the schema. |
| R-12 | E State | State/invariant layer must include return-state and exception-state invariants (not only intra-function line/variable state). | Ablation on held-out types: invariant block with return-state vs without; pre-declared gain on SC-6 with CI excluding 0. |
| R-13 | E State | Per-input paired state comparison so small point edits are ranked by magnitude of state change, not collapsed to identical vectors. | On SC-1/SC-3 2-line edits, fraction of pairs sharing an identical feature vector <= 20% (V6: many SC-1 pairs score identical 0.3299); within-type rank AUROC reported. |
| R-14 | F Graph | Multi-view graph (CFG, data-flow, call, trace/event) with explicit return and exception nodes. | Unit tests: each mutation family modifies at least one view; per-view ablation reported on held-out types; returns appear as nodes (test fails if no return node). |
| R-15 | G Alignment | Base-to-variant alignment robust to refactors (loop rewrite, extract function, inlining) so behaviour-preserving structure change is not scored as divergence. | On verified-equivalent SP-5/SP-8-style negatives, mean score gap vs other negatives <= 0.05 (V6: 0.60-0.64 vs ~0.40). |
| R-16 | H Divergence | First-divergence localisation and impact propagation to an observable sink; classifies masked vs unexercised vs none. | Every no-output-diff CHANGED pair is auto-classified {unexercised, masked-before-sink, no-divergence}; DEV counts reproduce 61 / 180 / 116 or differences are explained. |
| R-17 | H Divergence | Return/exception sink divergence is a scored component, not an add-on regime. | SC-6 type: score AUROC >= 0.70 with lower CI > 0.5 on sealed set, without using expected outputs. |
| R-18 | I Uncertainty | Abstention is a typed output; abstained pairs are excluded from ranking, not filled with a median constant; coverage-risk curve and selective AUROC reported. | No two abstained pairs share a fill score in output; report coverage, selective AUROC, and ECE (calibration) per benchmark; target coverage declared in advance. |
| R-19 | I Decision | Three-way decision CHANGED / EQUIVALENT-within-budget / UNKNOWN, with evidence-budget recorded. | Decision table contains all three classes; EQUIVALENT never asserted from NOT_ACTIVATED evidence alone (assertion test). |
| R-20 | J Prediction | Prediction claims are incremental over conventional + differential baselines in a pre-declared paired test; feature blocks must keep sign across benchmarks or be demoted to moderators. | Pre-declared criterion: lower CI of (SBG+CONV) - CONV > 0 on each external set (V6: -0.103 BugsInPy LR, -0.123 QuixBugs canonical GBM); sign consistency check for each block across >= 4 sets (V6 E block flips). |
| R-21 | J Prediction | Cross-generator generalisation: evaluate leave-mutation-type/family-out and unseen-generator holdout. | LOFO AUROC lower CI > 0.55 (V6: ~0.52 pooled; V6 GBM 0.582); generator-fingerprint baseline (CONV GBM) also reported under same scheme (V6: 0.742). |
| R-22 | K Validation | Labels derived from a behavioural oracle (tests/differential with budget plus human adjudication sample), never from generator type. | `label_pure_function_of_type` = false in the leakage audit; human adjudication of a stratified sample (>= the 446 flagged rows) with inter-rater agreement reported. |
| R-23 | K Validation | Preserving transformations validated for equivalence on multiple inputs before being labelled EQUIVALENT; invalid generators quarantined. | 0 EQUIVALENT pairs with output diff after R-05 canonicalisation (V6: 47 SP-8 + 42 SP-11 = 89). |
| R-24 | K Validation | Variant-level canonicalisation and dedup; effective-N reported; folds split by variant-group for every scheme. | 0 straddling variant groups in every CV scheme including leave-type-out (V6: 16-18); dedup-weighted and raw AUROC both reported; 1 conflicting-label vector -> 0. |
| R-25 | K Validation | Mandatory confound baselines on every benchmark: reversed edit size, static tokens/AST, CONV GBM, differential output, all under leave-generator-out. | Report generator refuses to emit a headline if any baseline is missing; edit-size-matched strata computed. |
| R-26 | K Validation | Pristine sealed holdout: new programs, new generator family, and real bugs, sealed until freeze; no prior-version scores exist. | Hash of sealed set committed before any extraction; git-history script shows no feature/score file touching those program ids earlier (V6 holdouts all previously seen with V5). |
| R-27 | K Validation | Real-bug corpus with a coverage target and a declared eligibility rule applied before scoring. | Coverage (ACTIVATED share) >= 60% on real-bug set (V6: BugsInPy 28.5%, QuixBugs declared 61.2%); eligibility exclusions logged with counts. |
| R-28 | L Governance | Freeze/manifest practice extended: dataset, code, threshold and analysis-plan hashes committed before scoring; chronology machine-checked. | CI script: freeze-commit timestamp earlier than every result file commit; fails otherwise (V6 `9a9104f` same-commit case). |
| R-29 | L Governance | Environment determinism: pinned Python and lockfile, seeds, `PYTHONHASHSEED=0`, thread caps; cross-machine repro. | Fresh checkout on a second machine/Python reproduces feature matrix with max abs difference 0.0 or declared tolerance (V6: only same machine verified). |
| R-30 | L Governance | Stale-artifact detector: regenerate variants from bases and compare AST dumps; CI fails on mismatch. | 0 stale programs (V6: 8 of 100; 4 programs / 163 pairs excluded). |
| R-31 | L Governance | Selection rules and metrics defined before any ablation or holdout results are seen; deviations logged in a ledger. | Pre-registration commit precedes first ablation output (V6: rule operationalised after single-seed ablation); deviation ledger non-empty only with timestamps. |

## 3. Coverage check, areas A-L

| Area | Requirements |
|---|---|
| A Exploration | R-01, R-02, R-03 |
| B Execution Capture | R-04, R-05, R-06, R-07 |
| C Static Context | R-08, R-09 |
| D Evidence Fabric | R-10, R-11 |
| E State/Invariant | R-12, R-13 |
| F Multi-view Graph | R-14 |
| G Alignment | R-15 |
| H Divergence/Impact | R-16, R-17 |
| I Uncertainty/Decision | R-18, R-19 |
| J Prediction | R-20, R-21 |
| K Validation harness | R-22 to R-27 |
| L Reproducibility/Governance | R-28 to R-31 |

All 12 areas have at least one requirement; every failure F-01 to F-28 maps to at least one requirement.

## 4. Risk register by theme

**Leakage.** (a) Label is a pure function of generator (`AUD/LEAKAGE_AUDIT.json`); conventional GBM learns generator identity (0.970 -> 0.742 under type holdout). (b) 596 duplicate groups / 1713 rows; 16-18 groups straddle leave-type-out folds. (c) Holdouts already seen with V5; test chronology unprovable (`docs/current/TEST_SET_CHRONOLOGY.md`). (d) Selection rule defined after ablations. Mitigation: R-22, R-24, R-26, R-28, R-31. Residual risk: any V7 design choice informed by reading V6 holdout failure lists contaminates those sets further; treat them as development data from now on.

**Label quality.** 47 SP-8 labels probably wrong; 42 SP-11 flagged by a faulty instrument; 116 CHANGED pairs unresolved; 61 unexercised; automated evidence only, no human adjudication. Edit-size confound makes labels partially predictable from diff length. Mitigation: R-03, R-05, R-22, R-23, R-09.

**Instrumentation.** Return-value blindness (SC-6); repr artifacts; harness group timeouts (51 pairs lost once); thread oversubscription; nondeterminism (60 BugsInPy bases) with uninvestigated source. Mitigation: R-04 to R-07. Residual risk: capturing return values moves the system toward differential testing, which already scores 0.805 DEV; V7 must state clearly what is gained beyond it (R-20).

**Activation.** Unexercised changed lines (61), unsupported signatures (49), ineligible QuixBugs programs (36 pairs), coverage 28.5% on BugsInPy; abstention fill creates ties. Mitigation: R-01, R-02, R-18, R-27. Residual risk: exploration may raise coverage only on synthetic code; the real-bug coverage target (R-27) is the real test, and activated-only subsets are executability-selected (QuixBugs evaluable 0.75 vs 0.67).

**Generalisation.** LOFO ~0.52; V6 does not beat conventional features on BugsInPy or QuixBugs canonical GBM; E block sign unstable; V5 external below chance; reversed edit size flips sign between synthetic (0.77-0.85) and QuixBugs (0.325). Mitigation: R-09, R-20, R-21, R-25. Residual risk: with only 40-51 real-bug programs, CIs stay wide (QuixBugs declared 0.666 [0.57, 0.76]); R-27 should extend the real-bug corpus rather than reuse these.

Limitations of this document: figures taken from the V6 reports and audit JSONs, not recomputed; F-06 "0.771 DEV" is stated in the decision report (s4), not in a JSON; the "V5 external below chance" statement is cited second-hand through the decision report (it references `STATUS.md`, whose current head describes the V5 external results as "no transfer"). Acceptance thresholds are design proposals.
