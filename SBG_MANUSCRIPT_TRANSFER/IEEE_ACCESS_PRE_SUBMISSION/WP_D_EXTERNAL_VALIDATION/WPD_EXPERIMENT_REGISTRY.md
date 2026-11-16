# WP-D External Validation — Experiment and Analysis Registry

This document records the master registry of all investigations, reproductions, feasibility probes, statistical audits, and planned replications conducted under Work Package D (WP-D: External Validation) for the Software Behavior Genome (SBG) project.

---

## 1. Scientific-Rule Compliance and Integrity Ledger

All subagents (D1, D2, D3, D4, W3) operated under strict research-integrity constraints:

1. **V10 Test and V9c Validation Not Touched**: No experiment, probe, or statistical script read, scored, or executed V10 test or V9c validation datasets. The internal benchmark splits remain completely uncompromised.
2. **Zero Tuning on External Labels**: No model hyperparameters, feature thresholds, weights, or heuristics were fitted or tuned on BugsInPy, QuixBugs, HumanEvalPack, Refactory, or SeqCoBench labels.
3. **Strict Workspace Isolation**: All outputs, logs, copies, temporary sandboxes, and reports were written exclusively to `PKG/WP_D_EXTERNAL_VALIDATION/raw/` (`WPD-D1_compat`, `WPD-D2_repro`, `WPD-D3_datasets`, `WPD-D4_stats`), `PKG/WP_D_EXTERNAL_VALIDATION/scripts/`, or `PKG/WP_D_EXTERNAL_VALIDATION/`.
4. **SBG Repository Tree Immutability**:
   - **Pre-execution state**: A cryptographic manifest of the entire SBG source tree was captured in `PKG/logs/sbg_tree_sha256_BEFORE.txt` containing 16,137 files.
   - **Post-execution verification**: Following execution of all rescoring pipelines, driver runs, and diagnostics, subagent D2 executed `scripts/d2_sbg_integrity.sh` which re-hashed every file in `PKG/logs/sbg_tree_sha256_BEFORE.txt` and performed a direct diff against `before.sorted`.
   - **Verification result**: Recorded in `raw/WPD-D2_repro/integrity/summary.txt`:
     ```text
     diff rc=0 lines=0 before=16137 after=16137
     ```
     Zero byte differences were detected across all 16,137 files.
   - **D3 Housekeeping Flag (`.pytest_cache` mtime)**: Subagent D3 noted that `SBG/.pytest_cache/v/cache/{nodeids,lastfailed}` had modification timestamps newer than 18:00 IST on 2026-11-14. Audit confirms that `.pytest_cache/` is git-ignored (`.gitignore` line 16) and is **not present** in `PKG/logs/sbg_tree_sha256_BEFORE.txt`. No tracked, staged, or audited source files were modified.
5. **D2 Reproduction Status Flag**: All 72 commands in `raw/WPD-D2_repro/command_log.jsonl` ran to completion (with logged exit codes, runtimes, load averages, and output artifacts). The Level-1 recomputation (`level1/`), Level-2 comparisons (`compare/`), and integrity hashes (`integrity/`) are fully verified. However, because a standalone summary file `raw/WPD-D2_repro/REPRO_REPORT.md` was not generated as an independent document, D2 raw report generation is formally flagged as **INCOMPLETE**; all downstream statistics and registry entries rely directly on the verified raw artifacts (`command_log.jsonl`, `ALL_COMPARISONS_SUMMARY.csv`, `level1_results.json`, `summary.txt`).

---

## 2. Master Registry Summary Table

| ID | Type | Title | Status | Scope / Method | AUROC / Key Result |
|---|---|---|---|---|---|
| **WPD-D1-01** | READ-ONLY | External Dataset Pair Inventory | COMPLETED | Static parsing of 200 BugsInPy & 152 QuixBugs pairs | 39 bug clusters (BP), 40 programs (QC) |
| **WPD-D1-02** | EXECUTED | Structural Confounds & Recomputed AUROCs | COMPLETED | Static AST/token analysis & arithmetic recomputation | Confounds C1–C5 identified; 0.497/0.444 are post-hoc subsets |
| **WPD-D1-03** | EXECUTED | Sandboxed Label Oracle Execution | COMPLETED | SBG 11-input battery run on positive/negative copies | Only 4.3% BP and 20% QC positives are CHANGED |
| **WPD-D1-04** | EXECUTED | Label Validity & Negative Audit | COMPLETED | Audit of SP-transformed negatives | 7 statically invalid + 9 broken SP-2 negatives |
| **WPD-D1-05** | EXECUTED | Lexical & Shingle Independence Analysis | COMPLETED | 5-gram token shingles & identifier overlap | Low lexical overlap; no verbatim code leakage |
| **WPD-D1-06** | EXECUTED | Lineage, Duplicates & Format Shortcut | COMPLETED | AST/unparse check & static edit kind classification | Format shortcut AUROC: 0.915 (BP), 1.000 (QC) |
| **WPD-D2-B0-copy** | EXECUTED | SBG Working Copy Isolation | COMPLETED | `cp -R SBG raw/WPD-D2_repro/sbg_copy` | Clean isolated workspace tree (16,137 files) |
| **WPD-D2-B0-verify** | EXECUTED | Working Copy Hash Verification | COMPLETED | Full tree sha256 comparison | 0 differences between SBG and sbg_copy |
| **WPD-D2-A-level1** | EXECUTED | Level-1 Pure Arithmetic Recompute | COMPLETED | Direct pair counting & cluster bootstrap (B=2000) | Exactly reproduces 0.409917, 0.497044, 0.387723, 0.444444 |
| **WPD-D2-A-level1-vs-a3**| EXECUTED | Level-1 Cross-Check vs EXP-A3-007 | COMPLETED | Comparison against prior audit numbers | 0 discrepancies across all metrics |
| **WPD-D2-B0-run-copies**| EXECUTED | Provisioning B1, B2, B3 Workspaces | COMPLETED | Tree cloning for run isolation | Independent run sandboxes created |
| **WPD-D2-B1-bp-v7** | EXECUTED | Level-2 Rescore: BugsInPy v7 (py313) | COMPLETED | Rescore on py313 (`output_free_v7`) | REPRODUCED-WITHIN-TOLERANCE (max diff 0.000652) |
| **WPD-D2-B1-cmp-bp-v7** | EXECUTED | Score Comparison: B1 vs Committed | COMPLETED | Thresholded numerical difference audit | AUROC 0.409917, 0 flag mismatches |
| **WPD-D2-B2-quix-v7** | EXECUTED | Level-2 Rescore: QuixBugs v7 (py313) | COMPLETED | Rescore on py313 (`output_free_v7`) | NOT-REPRODUCED bit-for-bit (1 pair timed out in rerun) |
| **WPD-D2-B2-cmp-quix-canon** | EXECUTED | Score Comparison: B2 Canon vs Committed | COMPLETED | Numerical diff audit on 151 pairs | Canon AUROC 0.380495 vs 0.387723 (max diff 0.0264) |
| **WPD-D2-B2-cmp-quix-decl** | EXECUTED | Score Comparison: B2 Decl vs Committed | COMPLETED | Numerical diff audit on 97 pairs | Decl AUROC 0.700734 vs 0.702222 (5 flag diffs) |
| **WPD-D2-B3-v8rescore**| EXECUTED | Level-2 Rescore: v8 Harness (py313) | COMPLETED | Multiprocessing rescore (`rescore_external_v8.py`) | QC v8 EXACT (0.384158 / 0.444444); BP v8 within tol |
| **WPD-D2-B3-cmp-v8dump**| EXECUTED | Score Comparison: B3 vs Committed v8 | COMPLETED | Comparison against `external_rescore_v8_pairs.json` | QC max diff 0.0; BP max diff 0.000294 |
| **WPD-D2-C0-version-copies**| EXECUTED | Multi-Version Workspace Setup | COMPLETED | Tree cloning for py39, py311, py314, cold-start | Independent interpreter run directories |
| **WPD-D2-C-quix-py39** | EXECUTED | QuixBugs Canonical Run on Python 3.9 | COMPLETED | Execution under CPython 3.9.6 | AUROC 0.466346 (ex-SP-2 0.571225); 29 diffs > 0.001 |
| **WPD-D2-C-quix-py311**| EXECUTED | QuixBugs Canonical Run on Python 3.11| COMPLETED | Execution under Homebrew Python 3.11 | AUROC 0.384844 (ex-SP-2 0.444444); 8 diffs > 0.001 |
| **WPD-D2-C-quix-py314**| EXECUTED | QuixBugs Canonical Run on Python 3.14| COMPLETED | Execution under Homebrew Python 3.14 | AUROC 0.375916 (ex-SP-2 0.437322); 4 diffs > 0.001 |
| **WPD-D2-C-quix-py313-repeats**| EXECUTED | QuixBugs Repeats & Seed Variations | COMPLETED | Multi-seed runs on py313 and py39 | Seed changes induce minor perturbations (max diff 0.026) |
| **WPD-D2-C-cmp-quix-crossversion**| EXECUTED | QuixBugs Cross-Version Audit | COMPLETED | Comparison matrix across all Python versions | Summarized in `ALL_COMPARISONS_SUMMARY.csv` |
| **WPD-D2-C-bp-py39** | EXECUTED | BugsInPy v7 Run on Python 3.9 | COMPLETED | Execution under CPython 3.9.6 | AUROC 0.437759 (ex-SP-2 0.515521); 51 diffs > 0.001 |
| **WPD-D2-C-bp-py311** | EXECUTED | BugsInPy v7 Run on Python 3.11 | COMPLETED | Execution under Homebrew Python 3.11 | AUROC 0.406696 (ex-SP-2 0.471175); 41 diffs > 0.001 |
| **WPD-D2-C-bp-py314** | EXECUTED | BugsInPy v7 Run on Python 3.14 | COMPLETED | Execution under Homebrew Python 3.14 | AUROC 0.410147 (ex-SP-2 0.474501); 10 diffs > 0.001 |
| **WPD-D2-C-bp-py313-repeat**| EXECUTED | BugsInPy v7 Repeat on Python 3.13 | COMPLETED | Repeat execution on CPython 3.13.5 | REPRODUCED-EXACT vs B1 rerun (0.0 diff) |
| **WPD-D2-C-cmp-bp-crossversion**| EXECUTED | BugsInPy Cross-Version Audit | COMPLETED | Comparison matrix across all Python versions | Summarized in `ALL_COMPARISONS_SUMMARY.csv` |
| **WPD-D2-D1-cold-probes**| EXECUTED | Cold-Start & State Leak Isolation | PARTIAL | Probe runs on individual units (black, youtube_dl, etc.)| State leak identified in unisolated runner (`black_23` timeout) |
| **WPD-D2-D2-diag-bp-cache**| EXECUTED | Clean-Process BugsInPy Diagnostic | COMPLETED | Full 51-bug clean diagnostic (`--workers 2`) | Evaluates cache stability under process isolation |
| **WPD-D2-D3-sbg-integrity**| EXECUTED | Post-Run SBG Tree Integrity Hash | COMPLETED | SHA256 diff against BEFORE manifest | 0 diffs across 16,137 files (verified read-only) |
| **WPD-D3-P01** | FEASIBILITY | Dataset Metadata Fetch via Web APIs | COMPLETED | GitHub / HF / PyPI API metadata collection | Survey of ~30 candidate repositories |
| **WPD-D3-P02** | FEASIBILITY | arXiv Paper Abstract Retrieval | COMPLETED | arXiv API retrieval of 11 publication abstracts | Verified benchmark provenance and design claims |
| **WPD-D3-P03** | FEASIBILITY | Candidate Benchmark Direct Downloads | COMPLETED | Offline download of small datasets (19.5 MB total) | Refactory, HumanEvalPack, SeqCoBench, EquiBench |
| **WPD-D3-P04** | EXECUTED | Static AST SBG Entry Discovery Audit| COMPLETED | AST parsing on Refactory and HumanEvalPack | 164/164 HEP and 4,230 Refactory programs pass static check |
| **WPD-D3-P05** | EXECUTED | 11-Input Battery Outcome Signatures | COMPLETED | Dynamic run of HEP (328) and Refactory (4,393) | Records return repr, exception type, stdout (no SBG scoring) |
| **WPD-D3-P06** | EXECUTED | HumanEvalPack Observability Analysis | COMPLETED | Observability audit of injected bugs | Only 52.4% bugs observable; 47 solutions raise on all inputs |
| **WPD-D3-P07** | EXECUTED | Independent Minifier Negative Generator| COMPLETED | `python-minifier 3.4.0` generation on 164 solutions | 164/164 minified variants are valid EQUIVALENT (28 AST-identical) |
| **WPD-D3-P08** | EXECUTED | CPython 3.11 Stdlib Static AST Scan | COMPLETED | Scan of 150 stdlib modules / 968 public functions | 0 fully annotated functions; unannotated mutation infeasible |
| **WPD-D3-P09** | EXECUTED | Refactory Observability & Label Recovery| COMPLETED | Analysis of student programs vs reference | 26.5% correct programs fail battery equality (task mismatch) |
| **WPD-D3-P10** | EXECUTED | SeqCoBench Battery Dynamic Execution | COMPLETED | Battery run on 15,706 SeqCoBench programs | 891/1,134 original programs execute cleanly on >=1 input |
| **WPD-D3-P11** | EXECUTED | HumanEvalPack Edit-Size Confound Probe | COMPLETED | Static edit-distance audit on minified pairs | Reversed edit-size AUROC is 0.765 (severe size confound) |
| **WPD-D3-P12** | EXECUTED | EquiBench OJ Static & STDIN Audit | COMPLETED | AST inspection of 1,200 EquiBench OJ pairs | 389-395 pairs require stdin/stdout; unsuitable for SBG |
| **WPD-D3-P13** | EXECUTED | SeqCoBench Stratum Yield Analysis | COMPLETED | Yield filtering for clean small-edit pairs | Yields 1,225 validated pairs (663 EQ / 562 CH, 325 MBPP tasks) |
| **WPD-D3-P14** | EXECUTED | SeqCoBench Static Shortcut AUROC | COMPLETED | Token-bag / AST-bag shortcut on SeqCoBench | Static token shortcut achieves 0.817 AUROC inside small-edit stratum |
| **WPD-D3-P15** | EXECUTED | AST Function Overlap with SBG Codebase| COMPLETED | Exact AST match across 14,257 SBG `.py` files | 0 exact function AST matches; zero verbatim leakage |
| **WPD-D3-P16** | EXECUTED | SeqCoBench Prior Audit Crosscheck | COMPLETED | Re-derivation of Agent 3 counts from outcomes | Re-derived and confirmed prior feasibility counts |
| **WPD-D4-00** | EXECUTED | Statistical Library Self-Test | COMPLETED | Self-test of tie-aware AUROC & point estimates | 0 errors across 500 tests; reproduces all published numbers |
| **WPD-D4-01** | EXECUTED | 17 Analysis Pair-Set Construction | COMPLETED | Set registry, membership matrices, unevaluated log | 17 analysis sets mapped across BugsInPy and QuixBugs |
| **WPD-D4-02** | EXECUTED | Statistical Inference & Permutation | COMPLETED | Cluster bootstrap (B=5000) & permutation (m=5000)| BP-v7-EVAL: 0.410 [0.329, 0.489]; QC-v7-ALL: 0.388 [0.290, 0.495] |
| **WPD-D4-03** | EXECUTED | Hurdle Zero-Score Decomposition | COMPLETED | Zero-rate decomposition & tie-mass analysis | Negative hurdle difference: negatives detect changed > positives |
| **WPD-D4-04** | EXECUTED | Baselines & Holm-Adjusted ΔAUROC | COMPLETED | Paired ΔAUROC vs 5 baselines; source shortcuts | Static AST beats SBG v5 (p=0.002); format shortcut AUROC 1.000 |
| **WPD-D4-05** | EXECUTED | Power Simulation & Rule-Out Bounds | COMPLETED | Monte Carlo simulation (NSIM=1500) | Study is underpowered for AUROC <= 0.60; rules out >= 0.75 |
| **WPD-D4-06** | EXECUTED | Sensitivity & Alternative Clusterings | COMPLETED | Re-clustering by project, lineage, content | Point estimates invariant near chance across all clusterings |
| **WPD-D4-07** | EXECUTED | Forking Paths Audit (21 Variants) | COMPLETED | Specification curve across 21 recorded AUROCs | 9/11 BP and 7/7 QC canonical specifications are < 0.50 |
| **WPD-D4-08** | EXECUTED | Automated Report Markdown Rendering | COMPLETED | Report compilation from JSON/CSV data | Generated `raw/WPD-D4_stats/STATS_REPORT.md` |
| **WPD-D4-09** | EXECUTED | Narrative Number Verification | COMPLETED | Automated consistency assertions against data | 0 discrepancies asserted across all narrative text |
| **WPD-X1** | NOT EXECUTED | SeqCoBench Independent Replication | PLANNED | Full SBG v8 tracing & scoring on 1,225 pairs | Planned replication to test synthetic edit generalisation |

---

## 3. Detailed Experiment Records

### WPD-D1: Dataset Compatibility, Label Reliability, and Confounders

#### WPD-D1-01: External Dataset Pair and Unit Inventory
- **Type**: READ-ONLY inspection
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d1_01_inventory.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: BugsInPy v7 manifest (`pairs_bugsinpy_output_free_v7.jsonl`, SHA256: `378cb3429d317e534655799cb8eaf4056fbede4d908757d259b24d801cdd6548`), QuixBugs-Python Canonical (`pairs_quixbugs_canonical_output_free_v7.jsonl`, SHA256: `69f8efae6ee0d0a4d7e18119196a35d13c2e0fce32918de1e4e90b219b0eaf88`), QuixBugs Declared (`pairs_quixbugs_declared_output_free_v7.jsonl`, SHA256: `6cbc4a3d61068be0bd1af511879d357c159e051e98290969d15bee095ccdb32e`)
- **Configuration**: `PYTHONHASHSEED=0`, `PYTHONDONTWRITEBYTECODE=1`
- **Runtime**: 0.15s
- **Outputs**: `raw/WPD-D1_compat/data/corpus_inventory.json`, `raw/WPD-D1_compat/data/corpus_pairs.csv`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: None; parsed all 200 BugsInPy and 152 QuixBugs pairs.
- **Notes**: Documents base program, variant program, entry function, and pair type for every external pair.

#### WPD-D1-02: Structural Confounds and Recomputed Headline AUROCs
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d1_02_confounds.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `SBG/artifacts/paper_evidence/raw/external_rescore_v8_pairs.json` (SHA256: `e09c35ed393d1a726058989534fd11090744749d3d9d7f2cd407b767c66b9ebe`)
- **Configuration**: Cluster bootstrap B=2000, seed 42
- **Runtime**: 0.45s
- **Outputs**: `raw/WPD-D1_compat/data/confound_summary.json`, `raw/WPD-D1_compat/data/recomputed_headline_aurocs.csv`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: Identifies five core confounds: C1 (format fingerprint), C2 (edit-size shortcut), C3 (docstring artefact), C4 (SP-2 entry rename), C5 (positive unobservability).
- **Notes**: Recomputes BugsInPy v8 ex-SP-2 AUROC (0.497 [0.402, 0.596]) and QuixBugs canonical v8 ex-SP-2 AUROC (0.444 [0.355, 0.539]). Demonstrates that headline numbers exclude SP-2 post hoc; full sets are 0.416 and 0.384.

#### WPD-D1-03: Sandboxed Label Oracle Dynamic Execution
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d1_03_label_oracle.py --workers 4`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `SBG/external/bugsinpy` (55 units), `SBG/external/quixbugs` (40 units)
- **Configuration**: 4 workers, 1.0s timeout per run, 11 synthesized protocol inputs
- **Runtime**: 20.12s (594 sandboxed program runs)
- **Outputs**: `raw/WPD-D1_compat/data/oracle_outcomes.jsonl`, `raw/WPD-D1_compat/data/oracle_summary.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 8 BugsInPy positive units not comparable (7 unsupported signature, 1 import error). 9 QuixBugs declared pairs ineligible.
- **Notes**: Measures return values, exceptions, argument mutations, and stdout. Under the SBG label definition, only 2 of 47 (4.3%) comparable BugsInPy positives and 8 of 40 (20%) QuixBugs canonical positives are CHANGED on the 11 inputs.

#### WPD-D1-04: External Dataset Label Validity and Negative Transformation Audit
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d1_04_label_audit.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `oracle_outcomes.jsonl`, `EXTERNAL_NEGATIVE_AUDIT.json` (SHA256: `61c9244cab2b999f034a6d87236c3d71eb71a461f943f470357c9cc000017303`)
- **Configuration**: `PYTHONHASHSEED=0`
- **Runtime**: 0.32s
- **Outputs**: `raw/WPD-D1_compat/data/label_audit_summary.json`, `raw/WPD-D1_compat/data/label_audit_invalid_negatives.csv`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: Found 7 statically invalid SP-2 negatives and 9 broken SP-2 negatives in BugsInPy.
- **Notes**: Documents that SP-2 negatives perturb execution signatures and rename entry functions in 100% of cases, artificially lowering AUROC below 0.5.

#### WPD-D1-05: Identifier and Shingle Lexical Independence Analysis
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d1_05_independence.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: SBG training/validation sets vs `SBG/external/{bugsinpy,quixbugs}`
- **Configuration**: 5-gram token shingles, identifier tokenization
- **Runtime**: 1.20s
- **Outputs**: `raw/WPD-D1_compat/data/independence_summary.json`, `raw/WPD-D1_compat/data/independence_jaccard.csv`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: None.
- **Notes**: Audits lexical and identifier overlap; confirms absence of verbatim training code leakage.

#### WPD-D1-06: Lineage Clustering, Content Duplication, and Format Shortcut Analysis
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d1_06_leakage_and_edits.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `SBG/external/bugsinpy`, `SBG/external/quixbugs`
- **Configuration**: 5-gram Jaccard threshold 0.5, AST unparse fixed-point check
- **Runtime**: 0.85s
- **Outputs**: `raw/WPD-D1_compat/data/leakage_summary.json`, `raw/WPD-D1_compat/data/bugsinpy_lineage_clusters.csv`, `raw/WPD-D1_compat/data/format_shortcut_pairs.csv`, `raw/WPD-D1_compat/data/bugsinpy_positive_edit_kind.csv`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: Found 33 content duplicate clusters and 32 project|file|unit lineages in BugsInPy.
- **Notes**: Proves a non-behavioural format shortcut (`variant == ast.unparse(variant)`) achieves AUROC 0.915 on BugsInPy and 1.000 on QuixBugs.

---

### WPD-D2: Execution Reproduction, Cross-Interpreter Stability, and Integrity

#### WPD-D2-B0-copy: SBG Repository Working Copy Isolation
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `cp -R SBG IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D2_repro/sbg_copy && echo copied && du -sh IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D2_repro/sbg_copy`
- **Interpreter**: `/bin/cp`
- **Dataset**: `SBG/` (16,137 files)
- **Configuration**: Working copy clone
- **Runtime**: 7.61s
- **Outputs**: `raw/WPD-D2_repro/sbg_copy/`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: None.
- **Notes**: Guarantees that reproduction execution occurs in isolated directories.

#### WPD-D2-B0-verify: Working Copy Byte-Level Tree Hash Verification
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d2_verify_copy.py IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D2_repro/sbg_copy IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D2_repro/copy_verification.json SBG`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `sbg_copy` vs `SBG`
- **Configuration**: SHA256 tree compare
- **Runtime**: 2.22s
- **Outputs**: `raw/WPD-D2_repro/copy_verification.json`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: None; 0 byte differences.
- **Notes**: Cryptographically verifies integrity of working copy clone.

#### WPD-D2-A-level1: Level-1 Pure Arithmetic Recomputation from Stored Scores
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d2_level1_recompute.py SBG IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D2_repro/level1`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `pairs_bugsinpy_output_free_v7.jsonl`, `pairs_quixbugs_canonical_output_free_v7.jsonl`, `pairs_quixbugs_declared_output_free_v7.jsonl`, `external_rescore_v8_pairs.json`
- **Configuration**: Bootstrap B=2000, seed 42, stdlib only
- **Runtime**: 1.86s
- **Outputs**: `raw/WPD-D2_repro/level1/level1_results.json`, `raw/WPD-D2_repro/level1/level1_summary.md`, `raw/WPD-D2_repro/level1/dropped_pairs.csv`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: None; exact reproduction of point estimates.
- **Notes**: Independent calculation confirming AUROCs directly from score files.

#### WPD-D2-A-level1-vs-a3: Level-1 Cross-Check vs EXP-A3-007 Baseline
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python ../../scripts/d2_level1_vs_a3.py level1/level1_results.json IEEE_ACCESS_PRE_SUBMISSION/results/raw/EXP-A3-007/external_auroc_recompute.json level1/level1_vs_A3-007.json`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `level1_results.json` vs `external_auroc_recompute.json`
- **Configuration**: Max tolerance 1e-6
- **Runtime**: 0.04s
- **Outputs**: `raw/WPD-D2_repro/level1/level1_vs_A3-007.json`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: None; 0 discrepancy.
- **Notes**: Confirms perfect alignment with prior internal audit.

#### WPD-D2-B0-run-copies: Provisioning Run Directories for B1, B2, B3
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `for r in B1_bugsinpy_score_py313 B2_quix_score_py313 B3_v8rescore_py313; do cp -R sbg_copy runs/$r; done; ls runs`
- **Interpreter**: `/bin/bash`
- **Dataset**: `sbg_copy`
- **Configuration**: Clone to `runs/`
- **Runtime**: 27.03s
- **Outputs**: `raw/WPD-D2_repro/runs/B1_bugsinpy_score_py313`, `raw/WPD-D2_repro/runs/B2_quix_score_py313`, `raw/WPD-D2_repro/runs/B3_v8rescore_py313`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: None.
- **Notes**: Prepares per-experiment execution directories.

#### WPD-D2-B1-bp-v7: Level-2 Rescore of BugsInPy v7 on Python 3.13
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python experiments/final/external_bugsinpy.py score --protocol output_free_v7`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `SBG/external/bugsinpy` (200 pairs)
- **Configuration**: Protocol `output_free_v7`, `PYTHONHASHSEED=0`
- **Runtime**: 133.40s
- **Outputs**: `raw/WPD-D2_repro/runs/B1_bugsinpy_score_py313/artifacts/final/pairs_bugsinpy_output_free_v7.jsonl`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: 53 pairs unevaluated (signature/import issues) matching original run.
- **Notes**: Scores 147 pairs. Max score difference vs committed: 0.000652. AUROC reproduces at 0.409917.

#### WPD-D2-B1-cmp-bp-v7: Score Comparison: B1 vs Committed BugsInPy v7
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python ../../scripts/d2_compare_scores.py bugsinpy SBG/artifacts/final/pairs_bugsinpy_output_free_v7.jsonl runs/B1_bugsinpy_score_py313/artifacts/final/pairs_bugsinpy_output_free_v7.jsonl compare/B1_bugsinpy_v7_py313`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `pairs_bugsinpy_output_free_v7.jsonl`
- **Configuration**: Tolerance 0.001
- **Runtime**: 0.34s
- **Outputs**: `raw/WPD-D2_repro/compare/B1_bugsinpy_v7_py313.json`, `raw/WPD-D2_repro/compare/B1_bugsinpy_v7_py313_mismatches.csv`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: 0 flag discrepancies; max score difference 0.000652.
- **Notes**: Classified as REPRODUCED-WITHIN-TOLERANCE.

#### WPD-D2-B2-quix-v7: Level-2 Rescore of QuixBugs v7 on Python 3.13
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python experiments/final/external_quixbugs.py score --protocol output_free_v7`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `SBG/external/quixbugs` (152 pairs)
- **Configuration**: Protocol `output_free_v7`, `PYTHONHASHSEED=0`
- **Runtime**: 1019.62s
- **Outputs**: `raw/WPD-D2_repro/runs/B2_quix_score_py313/artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl`, `raw/WPD-D2_repro/runs/B2_quix_score_py313/artifacts/final/pairs_quixbugs_declared_output_free_v7.jsonl`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: 1 pair (`powerset` SP-6) timed out in rerun (evaluates 151 pairs vs 152 committed).
- **Notes**: Canonical AUROC 0.380495 vs committed 0.387723. Declared AUROC 0.700734 vs 0.702222.

#### WPD-D2-B2-cmp-quix-canon: Score Comparison: B2 QuixBugs Canonical vs Committed
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python ../../scripts/d2_compare_scores.py quixbugs SBG/artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl runs/B2_quix_score_py313/artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl compare/B2_quix_canonical_py313`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `pairs_quixbugs_canonical_output_free_v7.jsonl`
- **Configuration**: Tolerance 0.001
- **Runtime**: 0.33s
- **Outputs**: `raw/WPD-D2_repro/compare/B2_quix_canonical_py313.json`, `raw/WPD-D2_repro/compare/B2_quix_canonical_py313_mismatches.csv`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: 1 flag discrepancy; 4 pairs with score diff > 0.001; max abs diff 0.026397.
- **Notes**: Classified as NOT-REPRODUCED bit-for-bit.

#### WPD-D2-B2-cmp-quix-decl: Score Comparison: B2 QuixBugs Declared vs Committed
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python ../../scripts/d2_compare_scores.py quixbugs SBG/artifacts/final/pairs_quixbugs_declared_output_free_v7.jsonl runs/B2_quix_score_py313/artifacts/final/pairs_quixbugs_declared_output_free_v7.jsonl compare/B2_quix_declared_py313`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `pairs_quixbugs_declared_output_free_v7.jsonl`
- **Configuration**: Tolerance 0.001
- **Runtime**: 0.27s
- **Outputs**: `raw/WPD-D2_repro/compare/B2_quix_declared_py313.json`, `raw/WPD-D2_repro/compare/B2_quix_declared_py313_mismatches.csv`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: 5 flag discrepancies; 1 score diff > 0.001; max abs diff 0.039800.
- **Notes**: Classified as NOT-REPRODUCED bit-for-bit.

#### WPD-D2-B3-v8rescore: Level-2 Rescore of v8 Harness with Worker Pool
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python experiments/final/rescore_external_v8.py --workers 2`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: BugsInPy & QuixBugs v8 evaluation pairs
- **Configuration**: 2 workers, `PYTHONHASHSEED=0`
- **Runtime**: 175.15s
- **Outputs**: `raw/WPD-D2_repro/runs/B3_v8rescore_py313/artifacts/paper_evidence/raw/external_rescore_v8_pairs.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: None.
- **Notes**: QuixBugs canonical v8 reproduces EXACTLY (AUROC 0.384158, ex-SP-2 0.444444). BugsInPy reproduces within tolerance (AUROC 0.415439, ex-SP-2 0.496674).

#### WPD-D2-B3-cmp-v8dump: Score Comparison: B3 vs Committed v8 Dump
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python ../../scripts/d2_compare_scores.py v8dump SBG/artifacts/paper_evidence/raw/external_rescore_v8_pairs.json runs/B3_v8rescore_py313/artifacts/paper_evidence/raw/external_rescore_v8_pairs.json compare/B3_v8dump_py313`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `external_rescore_v8_pairs.json`
- **Configuration**: Tolerance 0.001
- **Runtime**: 0.67s
- **Outputs**: `raw/WPD-D2_repro/compare/B3_v8dump_py313_bugsinpy.json`, `raw/WPD-D2_repro/compare/B3_v8dump_py313_quixbugs_canonical.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: BugsInPy max diff 0.000294 (REPRODUCED-WITHIN-TOLERANCE); QuixBugs max diff 0.0 (REPRODUCED-EXACT).
- **Notes**: Validates the v8 corrected-harness rescoring pipeline on Python 3.13.

#### WPD-D2-C0-version-copies: Provisioning Multi-Version Python Directories
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `for r in C_py39 C_py311 C_py314 D_cold_start_py313; do cp -R sbg_copy runs/$r; done; ls runs`
- **Interpreter**: `/bin/bash`
- **Dataset**: `sbg_copy`
- **Configuration**: Cloned to `runs/C_py39`, `runs/C_py311`, `runs/C_py314`, `runs/D_cold_start_py313`
- **Runtime**: 38.48s
- **Outputs**: `raw/WPD-D2_repro/runs/C_py39/`, `raw/WPD-D2_repro/runs/C_py311/`, `raw/WPD-D2_repro/runs/C_py314/`, `raw/WPD-D2_repro/runs/D_cold_start_py313/`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: None.
- **Notes**: Isolates execution environments for cross-interpreter evaluations.

#### WPD-D2-C-quix-py39: QuixBugs Canonical Driver Run on Python 3.9
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py39/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d2_quix_driver.py raw/WPD-D2_repro/runs/C_py39 venvs/py39/bin/python canonical raw/WPD-D2_repro/runs/C_py39/quix_canonical_rows.jsonl 2`
- **Interpreter**: CPython 3.9.6 (`venvs/py39/bin/python`)
- **Dataset**: QuixBugs canonical programs
- **Configuration**: 2 workers, `PYTHONHASHSEED=0`
- **Runtime**: 4.31s
- **Outputs**: `raw/WPD-D2_repro/runs/C_py39/quix_canonical_rows.jsonl`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 29 pairs have diff > 0.001 vs committed; AUROC shifts to 0.466346 (ex-SP-2 0.571225).
- **Notes**: Demonstrates pronounced interpreter sensitivity under Python 3.9.

#### WPD-D2-C-quix-py311: QuixBugs Canonical Driver Run on Python 3.11
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `/opt/homebrew/bin/python3.11 IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d2_quix_driver.py raw/WPD-D2_repro/runs/C_py311 /opt/homebrew/bin/python3.11 canonical raw/WPD-D2_repro/runs/C_py311/quix_canonical_rows_py311_seed0.jsonl 2`
- **Interpreter**: CPython 3.11 (`/opt/homebrew/bin/python3.11`)
- **Dataset**: QuixBugs canonical programs
- **Configuration**: 2 workers, `PYTHONHASHSEED=0`
- **Runtime**: 4.73s
- **Outputs**: `raw/WPD-D2_repro/runs/C_py311/quix_canonical_rows_py311_seed0.jsonl`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 8 pairs have diff > 0.001; AUROC is 0.384844 vs committed 0.387723.
- **Notes**: Minor shifts in scores due to stdlib AST updates.

#### WPD-D2-C-quix-py314: QuixBugs Canonical Driver Run on Python 3.14
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `/opt/homebrew/bin/python3.14 IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d2_quix_driver.py raw/WPD-D2_repro/runs/C_py314 /opt/homebrew/bin/python3.14 canonical raw/WPD-D2_repro/runs/C_py314/quix_canonical_rows_py314_seed0.jsonl 2`
- **Interpreter**: CPython 3.14 (`/opt/homebrew/bin/python3.14`)
- **Dataset**: QuixBugs canonical programs
- **Configuration**: 2 workers, `PYTHONHASHSEED=0`
- **Runtime**: 24.91s
- **Outputs**: `raw/WPD-D2_repro/runs/C_py314/quix_canonical_rows_py314_seed0.jsonl`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 4 pairs have diff > 0.001; AUROC is 0.375916 vs committed 0.387723.
- **Notes**: Evaluates forward compatibility on Python 3.14.

#### WPD-D2-C-quix-py313-repeats: QuixBugs Canonical Repeats & Seed Variations
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: Multiple runs of `d2_quix_driver.py` with seeds 0, 1, 2 on Python 3.13 and Python 3.9
- **Interpreter**: CPython 3.13.5 & CPython 3.9.6
- **Dataset**: QuixBugs canonical programs
- **Configuration**: Seeds 0, 1, 2; `PYTHONHASHSEED=0, 1, 2`
- **Runtime**: ~120s total
- **Outputs**: `raw/WPD-D2_repro/runs/B2_quix_score_py313/quix_canonical_rows_py313_seed*.jsonl`, `raw/WPD-D2_repro/runs/C_py39/quix_canonical_rows_py39_seed*.jsonl`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: Seed perturbations produce minor variations (1 pair with diff > 0.001 on py313).
- **Notes**: Tests seed and run-to-run determinism.

#### WPD-D2-C-cmp-quix-crossversion: Cross-Version Score Comparisons for QuixBugs
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: Multiple invocations of `d2_compare_scores.py` comparing Python 3.9, 3.11, 3.13, 3.14 outputs against committed and B2
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: QuixBugs output jsonl files
- **Configuration**: Tolerance 0.001
- **Runtime**: 5.60s
- **Outputs**: `raw/WPD-D2_repro/compare/C_quix_*_vs_*.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: Summarized in `ALL_COMPARISONS_SUMMARY.csv`.
- **Notes**: Tabulates exact vs within-tolerance vs diverging pairs across interpreters.

#### WPD-D2-C-bp-py39: BugsInPy v7 Score Pipeline Run on Python 3.9
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py39/bin/python experiments/final/external_bugsinpy.py score --protocol output_free_v7`
- **Interpreter**: CPython 3.9.6 (`venvs/py39/bin/python`)
- **Dataset**: `SBG/external/bugsinpy`
- **Configuration**: Protocol `output_free_v7`, `PYTHONHASHSEED=0`
- **Runtime**: 179.73s
- **Outputs**: `raw/WPD-D2_repro/runs/C_py39/artifacts/final/pairs_bugsinpy_output_free_v7.jsonl`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 51 pairs exceed tolerance > 0.001 (max abs diff 0.080491); AUROC shifts to 0.437759 (ex-SP-2 0.515521).
- **Notes**: Classified as NOT-REPRODUCED.

#### WPD-D2-C-bp-py311: BugsInPy v7 Score Pipeline Run on Python 3.11
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `/opt/homebrew/bin/python3.11 experiments/final/external_bugsinpy.py score --protocol output_free_v7`
- **Interpreter**: CPython 3.11 (`/opt/homebrew/bin/python3.11`)
- **Dataset**: `SBG/external/bugsinpy`
- **Configuration**: Protocol `output_free_v7`, `PYTHONHASHSEED=0`
- **Runtime**: 129.88s
- **Outputs**: `raw/WPD-D2_repro/runs/C_py311/artifacts/final/pairs_bugsinpy_output_free_v7.jsonl`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 41 pairs exceed tolerance > 0.001; AUROC is 0.406696 vs committed 0.409917.
- **Notes**: Classified as NOT-REPRODUCED.

#### WPD-D2-C-bp-py314: BugsInPy v7 Score Pipeline Run on Python 3.14
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `/opt/homebrew/bin/python3.14 experiments/final/external_bugsinpy.py score --protocol output_free_v7`
- **Interpreter**: CPython 3.14 (`/opt/homebrew/bin/python3.14`)
- **Dataset**: `SBG/external/bugsinpy`
- **Configuration**: Protocol `output_free_v7`, `PYTHONHASHSEED=0`
- **Runtime**: 91.03s
- **Outputs**: `raw/WPD-D2_repro/runs/C_py314/artifacts/final/pairs_bugsinpy_output_free_v7.jsonl`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 10 pairs exceed tolerance > 0.001 (max abs diff 0.665895); AUROC is 0.410147.
- **Notes**: Classified as NOT-REPRODUCED.

#### WPD-D2-C-bp-py313-repeat: BugsInPy v7 Repeat Score Pipeline Run on Python 3.13
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python experiments/final/external_bugsinpy.py score --protocol output_free_v7`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `SBG/external/bugsinpy`
- **Configuration**: Protocol `output_free_v7`, `PYTHONHASHSEED=0`
- **Runtime**: 124.31s
- **Outputs**: `raw/WPD-D2_repro/runs/C_py313_repeat/artifacts/final/pairs_bugsinpy_output_free_v7.jsonl`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: 0 discrepancies vs B1 rerun (exact 0.0 diff); max diff vs committed 0.000652.
- **Notes**: Classified as REPRODUCED-EXACT vs B1 and REPRODUCED-WITHIN-TOLERANCE vs committed.

#### WPD-D2-C-cmp-bp-crossversion: Cross-Version Score Comparisons for BugsInPy
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: Multiple invocations of `d2_compare_scores.py` comparing Python 3.9, 3.11, 3.13, 3.14 outputs against committed and B1
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: BugsInPy output jsonl files
- **Configuration**: Tolerance 0.001
- **Runtime**: 2.80s
- **Outputs**: `raw/WPD-D2_repro/compare/C_bp_*_vs_*.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: Summarized in `ALL_COMPARISONS_SUMMARY.csv`.
- **Notes**: Compares BugsInPy scores across interpreters.

#### WPD-D2-D1-cold-probes: Cold-Start & State Leak Isolation Probes
- **Type**: EXECUTED experiment
- **Status**: PARTIAL
- **Exact Command**: Multiple invocations of `d2_cold_start_probe.py` on individual units (`youtube_dl_37`, `powerset`, `ansible_11`, `black_21`, `black_23`)
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: Selected BugsInPy and QuixBugs units
- **Configuration**: 3 runs per probe, `PYTHONHASHSEED=0, 1`
- **Runtime**: ~1800s total
- **Outputs**: `raw/WPD-D2_repro/compare/D_cold_start_results.json`, `raw/WPD-D2_repro/compare/D_cold_start_results.csv`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: `black_23` timed out (420s cap) due to state leak/cwd contamination when run in multi-unit process.
- **Notes**: Pinpoints cross-unit state leakage in unisolated scoring runners.

#### WPD-D2-D2-diag-bp-cache: Clean-Process BugsInPy Cache Diagnostic
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python experiments/final/diagnose_bugsinpy_cache.py --workers 2`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: BugsInPy all 51 bugs
- **Configuration**: 2 workers, `PYTHONHASHSEED=0`
- **Runtime**: 152.34s
- **Outputs**: `raw/WPD-D2_repro/compare/D2_diagnose_bugsinpy_cache_vs_committed.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: None.
- **Notes**: Evaluates score stability under clean subprocess caching.

#### WPD-D2-D3-sbg-integrity: Post-Run SBG Tree Integrity Verification
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `bash IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d2_sbg_integrity.sh`
- **Interpreter**: `/bin/bash` (`shasum -a 256`, `diff`)
- **Dataset**: `SBG/` against `PKG/logs/sbg_tree_sha256_BEFORE.txt` (16,137 files)
- **Configuration**: Sorted diff comparison
- **Runtime**: 2.03s
- **Outputs**: `raw/WPD-D2_repro/integrity/summary.txt`, `raw/WPD-D2_repro/integrity/diff.txt`, `raw/WPD-D2_repro/integrity/sbg_tree_sha256_AFTER_D2.txt`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: 0 diffs out of 16,137 files (`diff rc=0 lines=0 before=16137 after=16137`).
- **Notes**: Definitively proves SBG tree was unmodified throughout all D2 reproduction runs.

---

### WPD-D3: Additional Dataset Feasibility Probes

#### WPD-D3-P01: External Dataset Metadata Scraping via APIs
- **Type**: FEASIBILITY analysis
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P01_metadata_fetch.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: GitHub / HuggingFace / PyPI APIs for ~30 candidate repositories
- **Configuration**: Network enabled, timeout 8s
- **Runtime**: 15.4s
- **Outputs**: `raw/WPD-D3_datasets/probes/P01_metadata.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 7 guessed repository URLs returned 404 (flagged as UNVERIFIED).
- **Notes**: Surveys dataset availability, license, size, and language.

#### WPD-D3-P02: arXiv Paper Abstract Retrieval for Candidate Benchmarks
- **Type**: FEASIBILITY analysis
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P02_arxiv_abstracts.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: arXiv API for 11 benchmark publications
- **Configuration**: Network enabled
- **Runtime**: 6.2s
- **Outputs**: `raw/WPD-D3_datasets/probes/P02_arxiv.json`, `raw/WPD-D3_datasets/probes/P02b_seqcobench_arxiv.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: None.
- **Notes**: Collects publication context for candidate datasets.

#### WPD-D3-P03: Candidate Dataset Direct Download and Extraction
- **Type**: FEASIBILITY analysis
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P03_download_small.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: Refactory (`data.zip`, 1.9 MB), HumanEvalPack-Python (0.47 MB), SeqCoBench (7.1 MB), EquiBench (6.1 MB)
- **Configuration**: Network enabled, 50 MB total download cap
- **Runtime**: 8.5s
- **Outputs**: `raw/WPD-D3_datasets/probes/data/P03_downloads.json`, `raw/WPD-D3_datasets/probes/data/seqcobench_*.csv`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: Large datasets (>50 MB: CodeContests 7.6GB, CodeNet 7.8GB, APPS 1.4GB, Defects4J) skipped.
- **Notes**: Downloads 19.5 MB total candidate data for offline probing.

#### WPD-D3-P04: Static AST SBG Entry Discovery Audit
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P04_static_eligibility.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: Refactory (4,230 programs), HumanEvalPack (328 programs)
- **Configuration**: SBG frozen entry rule (`select_entry_output_free`)
- **Runtime**: 2.4s
- **Outputs**: `raw/WPD-D3_datasets/probes/P04_static_refactory.json`, `raw/WPD-D3_datasets/probes/P04_static_humanevalpack.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 164/164 HumanEvalPack programs pass static check; target entry selected in 163/164.
- **Notes**: Audits static eligibility without execution.

#### WPD-D3-P05: 11-Input Battery Outcome Signatures
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P05_run.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: HumanEvalPack (328 programs), Refactory (4,393 programs)
- **Configuration**: 1.0s timeout, SBG 11 synthesized inputs
- **Runtime**: 45.0s
- **Outputs**: `raw/WPD-D3_datasets/probes/P05_hep_outcomes.json`, `raw/WPD-D3_datasets/probes/P05_refactory_outcomes.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: Refactory `fail/` folder not executed.
- **Notes**: Records outcome signatures only (return repr, exception type, stdout). No SBG scoring.

#### WPD-D3-P06: HumanEvalPack Battery Observability Analysis
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P06_analyze_hep.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `P05_hep_outcomes.json`
- **Configuration**: Outcome comparison
- **Runtime**: 0.15s
- **Outputs**: `raw/WPD-D3_datasets/probes/P06_hep_observability.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: Only 86/164 (52.4%) bugs differ on SBG battery; 47/164 canonical solutions raise on all inputs.
- **Notes**: Documents severe unobservability due to unannotated integer inputs for list parameters.

#### WPD-D3-P07: Independent Minifier Negative Generator and Battery Verification
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P07b_minify_behaviour.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`, using `probes/_venv_tools`)
- **Dataset**: HumanEvalPack 164 canonical solutions
- **Configuration**: `python-minifier 3.4.0`, preserve annotations
- **Runtime**: 3.8s
- **Outputs**: `raw/WPD-D3_datasets/probes/P07_minify.json`, `raw/WPD-D3_datasets/probes/P07b_minify_behaviour.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 28/164 minified variants are AST-identical.
- **Notes**: All 164 minified variants are valid EQUIVALENT on battery, but edit sizes are confounded.

#### WPD-D3-P08: CPython 3.11 Standard Library Static AST Scan
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P08_stdlib_scan.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: CPython 3.11 `Lib/`
- **Configuration**: Public top-level function AST parser
- **Runtime**: 1.1s
- **Outputs**: `raw/WPD-D3_datasets/probes/P08_stdlib_scan.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 0 of 968 public functions are fully annotated; only 167 are self-contained.
- **Notes**: Unannotated stdlib mutation without declared inputs would suffer list-of-ints battery mismatch.

#### WPD-D3-P09: Refactory Student Program Observability & Label Recovery Audit
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P09_analyze_refactory.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `P05_refactory_outcomes.json`
- **Configuration**: Observability comparison
- **Runtime**: 0.45s
- **Outputs**: `raw/WPD-D3_datasets/probes/P09_refactory_observability.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 648/2,442 (26.5%) correct programs differ from reference on battery.
- **Notes**: Refactory's ground truth EQUIVALENT label is not reproduced under SBG's input synthesis without declared inputs.

#### WPD-D3-P10: SeqCoBench Preparation and Battery Execution
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P10_seqco_run.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: SeqCoBench (15,706 programs: 1,134 originals + 14,572 transformed)
- **Configuration**: 1.0s timeout, 11 synthesized inputs
- **Runtime**: 178.2s
- **Outputs**: `raw/WPD-D3_datasets/probes/P10_seqco_static.json`, `raw/WPD-D3_datasets/probes/P10_seqco_outcomes.jsonl`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: None.
- **Notes**: Runs 15,706 programs on SBG battery; 891/1,134 original programs execute cleanly on >=1 input.

#### WPD-D3-P11: HumanEvalPack Edit-Size Confounder Evaluation
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P11_hep_editsize.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: HumanEvalPack bugs vs minifier negatives
- **Configuration**: Levenshtein / line edit distance
- **Runtime**: 0.20s
- **Outputs**: `raw/WPD-D3_datasets/probes/P11_hep_editsize.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: Reversed edit-size AUROC is 0.765.
- **Notes**: Demonstrates severe edit-size shortcut confounding in HumanEvalPack.

#### WPD-D3-P12: EquiBench OJ Static Eligibility & STDIN Confound Audit
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P12_equibench_static.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: EquiBench OJ_A, OJ_V, OJ_VA (1,200 pairs)
- **Configuration**: AST stdin detection
- **Runtime**: 0.65s
- **Outputs**: `raw/WPD-D3_datasets/probes/P12_equibench_static.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 389-395 of 400 pairs read from stdin and lack entry functions; unsuitable for SBG harness.
- **Notes**: Classified as NOT METHODOLOGICALLY SUITABLE.

#### WPD-D3-P13: SeqCoBench Observability, Label Reliability & Stratum Yield
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P13_analyze_seqco.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `P10_seqco_outcomes.jsonl`
- **Configuration**: Stratum filtering (small edit <= 2, zero battery exceptions)
- **Runtime**: 1.4s
- **Outputs**: `raw/WPD-D3_datasets/probes/P13_seqco_observability.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: Inverted polarity (SeqCoBench 1=preserved vs SBG 1=changed).
- **Notes**: Identifies 1,225 validated clean small-edit pairs (663 EQ / 562 CH) across 325 MBPP task clusters.

#### WPD-D3-P14: SeqCoBench Static Shortcut AUROC Baseline Assessment
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P14_seqco_static_shortcut.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: Validated SeqCoBench pairs
- **Configuration**: Bootstrap B=1000, seed 42
- **Runtime**: 3.1s
- **Outputs**: `raw/WPD-D3_datasets/probes/P14_seqco_static_shortcut.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: Static token-bag shortcut achieves AUROC 0.817 [0.778, 0.854] inside small-edit stratum.
- **Notes**: Indicates even adapted SeqCoBench pairs are vulnerable to static text shortcuts.

#### WPD-D3-P15: AST Function Overlap with SBG Codebase
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P15_overlap_check.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: SeqCoBench, HumanEvalPack, Refactory vs 14,257 SBG `.py` files
- **Configuration**: AST exact match
- **Runtime**: 4.9s
- **Outputs**: `raw/WPD-D3_datasets/probes/P15_overlap.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: 0 exact function-level AST matches found.
- **Notes**: Confirms zero verbatim code leakage into SBG codebase.

#### WPD-D3-P16: SeqCoBench Prior In-Repo Crosscheck
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/probes/P16_seqco_prior_crosscheck.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `P10_seqco_outcomes.jsonl`
- **Configuration**: Crosscheck against Agent 3 report
- **Runtime**: 0.8s
- **Outputs**: `raw/WPD-D3_datasets/probes/P16_seqco_prior_crosscheck.json`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: None.
- **Notes**: Re-derives and confirms prior in-repo feasibility findings on SeqCoBench.

---

### WPD-D4: Independent Statistical Assessment

#### WPD-D4-00: Statistical Library Self-Test & Point-Estimate Reproduction
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d4_00_selftest.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: All committed score files
- **Configuration**: 500 tie-heavy random tests, `PYTHONHASHSEED=0`
- **Runtime**: 1.2s
- **Outputs**: `raw/WPD-D4_stats/00_selftest.json`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: 0 mismatches across 500 tests; reproduces all published point estimates.
- **Notes**: Validates tie-aware AUROC, Fisher exact, cluster bootstrap, and permutation routines.

#### WPD-D4-01: 17 Analysis Pair-Set Construction & Membership Matrices
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d4_01_sets.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `SBG/artifacts/final/*_v7.jsonl`, `external_rescore_v8_pairs.json`
- **Configuration**: 17 analysis sets
- **Runtime**: 0.8s
- **Outputs**: `raw/WPD-D4_stats/01_pair_sets.json`, `raw/WPD-D4_stats/01_set_membership.csv`, `raw/WPD-D4_stats/01_unevaluated_pairs.csv`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: None.
- **Notes**: Defines 17 analysis sets across BugsInPy and QuixBugs (pre-registered and post-hoc).

#### WPD-D4-02: Statistical Inference: Cluster Bootstrap & Permutation Tests
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d4_02_inference.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `01_pair_sets.json`
- **Configuration**: Bootstrap B=5000, permutation m=5000
- **Runtime**: 100.4s
- **Outputs**: `raw/WPD-D4_stats/02_inference.json`, `raw/WPD-D4_stats/02_inference_table.csv`, `raw/WPD-D4_stats/02_inference.log`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: None.
- **Notes**: Computes bug-, project-, and program-clustered 95% CIs and permutation p-values across all 17 sets.

#### WPD-D4-03: Zero-Score Hurdle Decomposition and Tie Mass Assessment
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d4_03_zero_decomposition.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `01_pair_sets.json`
- **Configuration**: Hurdle rate analysis
- **Runtime**: 1.5s
- **Outputs**: `raw/WPD-D4_stats/03_zero_decomposition.json`, `raw/WPD-D4_stats/03_zero_decomposition.csv`, `raw/WPD-D4_stats/03_zero_decomposition.log`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: None.
- **Notes**: Disproves repo claim that zero-score rate forces AUROC <= 0.5; quantifies negative hurdle difference.

#### WPD-D4-04: Baseline Predictors, Paired Delta-AUROC & Source Shortcuts
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d4_04_baselines.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `01_pair_sets.json` + vendored source files
- **Configuration**: Bootstrap B=5000, Holm family size 5
- **Runtime**: 78.2s
- **Outputs**: `raw/WPD-D4_stats/04_baselines.json`, `raw/WPD-D4_stats/04_baselines_table.csv`, `raw/WPD-D4_stats/04_edit_features.csv`, `raw/WPD-D4_stats/04_shortcut_by_negative_type.json`, `raw/WPD-D4_stats/04_baselines.log`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: Dev-selected model unavailable externally; Holm family size adjusted to 5.
- **Notes**: Demonstrates static AST beats SBG v5 on BugsInPy (p=0.002); format shortcut achieves 1.000 AUROC.

#### WPD-D4-05: Statistical Power Simulation, Minimum Detectable Effect & Rule-Out Bounds
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d4_05_power.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `01_pair_sets.json`
- **Configuration**: NSIM=1500, alpha=0.025, target power 0.80
- **Runtime**: 480.0s (~8 min)
- **Outputs**: `raw/WPD-D4_stats/05_power.json`, `raw/WPD-D4_stats/05_power.log`
- **Label**: PREREGISTERED
- **Errors / Exclusions**: None.
- **Notes**: Proves external design is underpowered to detect AUROC <= 0.60; rules out AUROC >= 0.60/0.75/0.897.

#### WPD-D4-06: Sensitivity Analysis Across Alternative Clusterings & Exclusions
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d4_06_sensitivity.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `01_pair_sets.json`
- **Configuration**: Bootstrap B=2000
- **Runtime**: 62.5s
- **Outputs**: `raw/WPD-D4_stats/06_sensitivity.json`, `raw/WPD-D4_stats/06_sensitivity_table.csv`, `raw/WPD-D4_stats/06_sensitivity.log`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: None.
- **Notes**: Evaluates stability under project, lineage, and content clustering; point estimates remain near chance.

#### WPD-D4-07: Forking Paths Audit Across 21 External AUROC Specifications
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d4_07_forking_paths.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: All 21 recorded external AUROC specifications
- **Configuration**: Specification curve analysis
- **Runtime**: 2.1s
- **Outputs**: `raw/WPD-D4_stats/07_forking_paths.json`, `raw/WPD-D4_stats/07_forking_paths.csv`, `raw/WPD-D4_stats/07_forking_paths.log`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: None.
- **Notes**: Catalogues 21 external AUROC specifications: 9/11 BugsInPy and 7/7 QuixBugs canonical are < 0.50.

#### WPD-D4-08: Automated Statistical Report Markdown Rendering
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d4_08_render.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `raw/WPD-D4_stats/*.json`, `*.csv`
- **Configuration**: Template `scripts/d4_report_template.md`
- **Runtime**: 0.8s
- **Outputs**: `raw/WPD-D4_stats/STATS_REPORT.md`
- **Label**: POST-HOC EXPLORATORY
- **Errors / Exclusions**: None.
- **Notes**: Generates complete statistical assessment report from machine-readable JSON/CSV artifacts.

#### WPD-D4-09: Automated Assertion & Verification of Narrative Numbers
- **Type**: EXECUTED experiment
- **Status**: COMPLETED
- **Exact Command**: `venvs/py313/bin/python IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/scripts/d4_09_check_report.py`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: `raw/WPD-D4_stats/STATS_REPORT.md` vs `raw/WPD-D4_stats/*.json`
- **Configuration**: Number consistency checker
- **Runtime**: 0.4s
- **Outputs**: `raw/WPD-D4_stats/STATS_REPORT.md` (verified)
- **Label**: PREREGISTERED
- **Errors / Exclusions**: 0 discrepancies asserted; all narrative numbers match source JSON outputs.
- **Notes**: Automated regression verification for published text numbers.

---

### WPD-X1: Planned Independent External Replication

#### WPD-X1: SeqCoBench Independent-Generator External Replication with Full SBG Scoring
- **Type**: NOT EXECUTED-planned
- **Status**: PLANNED
- **Exact Command**: `venvs/py313/bin/python experiments/final/external_seqcobench.py score --stratum small_edit_clean`
- **Interpreter**: CPython 3.13.5 (`venvs/py313/bin/python`)
- **Dataset**: SeqCoBench (1,225 validated pairs: 663 EQ / 562 CH across 325 MBPP tasks)
- **Configuration**: Protocol `output_free_v8`, Polarity inversion `1 - seqco_label`, Stratum `small_edit_clean`
- **Runtime**: Estimated ~350s (planned)
- **Outputs**: `raw/WPD-X1_seqco/pairs_seqcobench_output_free_v8.jsonl`, `raw/WPD-X1_seqco/seqcobench_results.json`
- **Label**: PLANNED
- **Errors / Exclusions**: Planned post-submission evaluation; blocked by protocol freezing rules during current review cycle.
- **Notes**: Independent-generator replication assessing synthetic edit generalisation without developer text confounds.
