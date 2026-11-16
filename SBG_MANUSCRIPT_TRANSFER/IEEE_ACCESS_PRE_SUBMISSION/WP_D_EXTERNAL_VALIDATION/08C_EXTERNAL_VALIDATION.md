# 08C — External validation (WP-D): BugsInPy, QuixBugs, additional datasets, reproduction

Writer W2, 2026-11-14. Compiles the WP-D subagent outputs. No SBG scoring was run for this report, and SBG/, V10 and V9c were not touched. It makes no IEEE Access submission decision.

**Path shorthand.** All paths are relative to PKG (`IEEE_ACCESS_PRE_SUBMISSION/`).

| Tag | Path |
|---|---|
| `D1` | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D1_compat/FINDINGS.md` |
| `D3` | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D3_datasets/FEASIBILITY.md` |
| `D4` | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D4_stats/STATS_REPORT.md` |
| `D2/` | `WP_D_EXTERNAL_VALIDATION/raw/WPD-D2_repro/` (no `REPRO_REPORT.md`, see §4) |
| `A3` | `results/raw/EXP-A3-007/external_auroc_recompute.json` |
| `AUDIT` | `SBG/artifacts/paper_evidence/REAL_BUG_GENERALISATION_AUDIT.md` (repo root: `SBG/…`) |

Evidence tags: **EXECUTED** = a WP-D script produced the number. **READ** = quoted from a file, not recomputed. **NOT-RUN** = planned only.

---

## 1. Verdict (read this first)

**The two external numbers are not evidence of external validity, and they are not evidence that SBG fails to generalise.** They show that this benchmark cannot answer the question. The benchmark is label-incompatible with the SBG task, and the labels are confounded with source. It is also post-hoc and underpowered for moderate effects.

### 1.1 What was reproduced

| Number | Exact pair set | Reproduced? | Status | Source |
|---|---|---|---|---|
| **0.497** BugsInPy | v8 corrected-harness rescore, 147 pairs minus **all 40 SP-2 negatives** = 107 pairs (41 pos / 66 neg, 39 bug clusters). AUROC 0.497044, cluster-bootstrap CI [0.402, 0.596] (A3, D1) or [0.401, 0.593] (D4) | Yes, from stored per-pair scores (D2 Level 1, D4, D1). D2 Level 2 re-execution on py3.13 gives 0.4967 (within tolerance). | **POST-HOC.** It needs the v8 rescore and the SP-2 deletion. Neither is in the pre-registration. | `D2/level1/level1_summary.md`, `D2/level1/level1_vs_A3-007.json`, D4 §0.1, D1 §1.3 |
| **0.444** QuixBugs canonical | v8 rescore, 151 evaluated pairs (`mergesort` positive non-terminating) minus all 40 SP-2 = 111 pairs (39 pos / 72 neg, 40 clusters). AUROC 0.444444, CI [0.355, 0.539] (A3) or [0.356, 0.536] (D4) | Yes. Level 1 matches exactly. Level 2 on py3.13 (v8 rescore) gives **exactly** 0.444444. | **POST-HOC**, same reason | `D2/compare/B3_v8dump_py313_quixbugs_canonical.json`, D4 §1 |
| **0.410** BugsInPy | v7 committed scores, evaluated only (147 pairs, 41/106, 39 clusters). **Pre-registered primary set.** CI [0.326, 0.494] | Yes. | PRE-REG, **below** 0.5 | D4 §0.1–2, `D2/level1/level1_summary.md` |
| **0.388** QuixBugs canonical | v7 committed, all 152 pairs (40/112, 40 clusters). **Pre-registered.** CI [0.285, 0.503] | Yes. | PRE-REG, **below** 0.5 | same |
| unfiltered v8 | BugsInPy 0.416 (147 pairs); QuixBugs 0.384 (151 pairs) | Yes. | post-hoc rescore | D1 §1.3 |

Counts and CIs for every set are in D4 §2–3 and `D2/level1/level1_summary.md`.

### 1.2 What the numbers do and do NOT mean

| Question | Answer | Evidence |
|---|---|---|
| Are 0.497 / 0.444 the pre-registered results? | **No.** The pre-registered values are 0.410 (BugsInPy) and 0.388 (QuixBugs), both below chance. D4 gives BugsInPy-EVAL bug-cluster CI [0.329, 0.489], permutation p(AUROC<0.5) = 0.015, and QuixBugs-canonical CI [0.290, 0.495], p = 0.007. The BugsInPy project-cluster CI [0.354, 0.529] contains 0.5. | D4 §3, F2 |
| Why do the headlines look "near chance"? | Deleting all SP-2 negatives removes the negatives where SBG scores worst (SP-2-only AUROC 0.28 BugsInPy, 0.28 QuixBugs). The SP-2 deletion adds +0.081 (BugsInPy) and +0.060 (QuixBugs). Only about 0.03 of the +0.081 comes from the 7 audited-invalid negatives. | D4 §7 |
| Is the external label compatible with the SBG label? | **Largely not.** SBG's label means "differs on the 11 protocol inputs". Under that definition only **2 of 47** comparable BugsInPy positives and **8 of 40** QuixBugs-canonical positives are CHANGED. 34 of 47 BugsInPy fixed programs raise on all 11 inputs. 27 of 40 QuixBugs base programs raise on at least 10 of 11 inputs. About 95% and 80% of the "positive" labels are EQUIVALENT in the SBG sense. | D1 §2.1 (EXECUTED oracle) |
| Is a near-0.5 AUROC then a failure of generalisation? | **No.** It is the expected outcome of an output-differencing method scored against labels that are mostly unobservable on its inputs. It is also not evidence of success. | D1 §2.1 |
| Is there a format shortcut? | **Yes.** `variant_is_unparse_canonical` separates labels perfectly in BugsInPy and both QuixBugs corpora: 145/145 and 112/112 negatives are `ast.unparse` fixed points, and 0/55 and 0/40 positives are. A static format score gives AUROC 0.915 (BugsInPy) and 1.000 (QuixBugs). Reversed edit size gives about 0.93 (BugsInPy raw line edit) and 0.88 (QuixBugs token). The external AUROC mixes "behaviour change" with "developer edit vs SBG transformer". | D1 §1.2 C1–C2, D4 §5 |
| What do the CIs rule out? | Ex-SP-2 CIs contain 0.5 and rule out a true AUROC ≥ 0.75 and V10-level 0.897. They rule out ≥ 0.6 only narrowly. They do **not** rule out 0.55–0.60. | D4 §6A |
| Power? | 80% power only for a true AUROC of ≈ 0.61–0.68 (simplified model, order of magnitude). 39 bug clusters / 11 projects (BugsInPy), 40 programs (QuixBugs). | D4 §6B |
| Which sentence is supportable? | **"No evidence of AUROC ≥ 0.6 on these two corpora under the output-free protocol, with confounded labels."** Not supportable: "SBG does not generalise" (a mechanism claim), "SBG is at chance" (the pre-registered values are below it and the headlines are post-hoc), "SBG generalises". | D4 §0.4, §9 |
| Is there any positive external signal? | QuixBugs **declared**-input regime: EVALUABLE 0.702 [0.580, 0.825] (24 pos / 75 neg). It is not credible as validity evidence (see §2, §5). | D4 §3 |

---

## 2. Dataset classification

Classes: **VI** Valid independent evaluation · **VA** Valid with documented adaptation · **EX** Exploratory only · **NS** Not methodologically suitable.

| Dataset / regime | Class | Basis (D1 unless noted) | Agreement |
|---|---|---|---|
| BugsInPy (51 bugs / 55 units; 41 positives scored) | **EX** (arguably NS as validation) | 2/47 positives CHANGED. Eligibility 10.2%. 44 lineages for 55 units, 5 role flips. 9 broken SP-2 negatives. Format shortcut 0.915. Seen by developers in Aug 2026. 14/55 positives not scorable. | D3 provisional EX; D4 implies the same via §5. D1/D3/D4 agree. |
| QuixBugs-Python **canonical** | **EX** | 8/40 positives CHANGED. Format shortcut 1.000. Reversed edit size beats SBG. Headline is post-hoc (unfiltered 0.384). | agree |
| QuixBugs-Python **declared** | **EX** (closest to VA, but the VA conditions in D1 §6 are not met) | 28/31 comparable positives CHANGED. Evaluable on only 99/152 pairs (28/40 programs), selected by evaluability. Inputs come from the repo's own tests. Reversed `static_token` 0.818 beats SBG 0.702 (D4 §5). | agree |
| QuixBugs-Java | **NS / not evaluated** | No SBG-schema Java result exists. The only Java numbers are an EEP-formula pilot with a different method. | D1 only; D3 does not assess it |
| SeqCoBench (MBPP-derived) | **VA** (independent-generator synthetic replication only) | D3 §1.2, §6.6. Different authors and implementation. Transformation families overlap SBG's. Static shortcut 0.82 in e ≤ 2. | D3 only |
| HumanEvalFix / HumanEvalPack-Python | EX | Only 52.4% of bugs are battery-observable. Minifier negatives are edit-size confounded (reversed AUROC 0.765). | D3 only |
| Refactory, CPython stdlib history, stdlib + independent mutation tool, PyPIBugs, EvalPlus canonical-vs-canonical, DebugBench, CanItEdit | EX | D3 §5. DebugBench, CanItEdit and PyPIBugs were not inspected and are provisional. | D3 only |
| Defects4J, ManySStuBs4J, GitBug-Java, Codeflaws, BugSwarm, CodeNet, CodeContests, EquiBench OJ, CodeXGLUE, refactoring oracles, CrossCodeEval-style, MBPP standalone, TypeBugs/Defects4Py | NS | D3 §5. Non-Python, stdin scripts, repo-scale builds, or no pair structure. TypeBugs/Defects4Py are UNVERIFIED. | D3 only |
| **Any VI dataset** | **none exists** | D3 §1.1 | — |

**Source disagreements (noted, none changes a classification):**
- D3 flags that the prior quoted "BugsInPy / QuixBugs AUROC 0.4099 / 0.3877" differ from the task-quoted 0.497 / 0.444 (D3 §8). D4 explains this. 0.4099 and 0.3877 are the pre-registered v7 values. 0.497 and 0.444 are post-hoc v8 values with SP-2 deleted (D4 §1, §8).
- D1 counts 47 comparable BugsInPy positives (v8 entry policy) and SBG evaluated 41. D1 states it did not reconcile this per pair (D1 §7.11).
- D1 and D4 both find the SP-2 negatives invalid or confounded. D4 knows only the 7 audited invalid ones (D4 §10). D1's execution finds **9** (2 more in matplotlib). See §9.
- The cluster-bootstrap CIs differ slightly between sources because of seeds and B (D4 §1, `D2/level1/level1_summary.md` uses the repo's CIs). This is not a point-estimate disagreement.
- D1 reports "26 of 41 BugsInPy positives score 0". D4 shows this holds for v8 (63.4%) but not v7 (21/41 = 51%). Quote the version with the number.

---

## 3. Evidence table

| Exp ID | Question | Scripts (`WP_D_EXTERNAL_VALIDATION/scripts/`) | Outputs | Tag |
|---|---|---|---|---|
| **WPD-D1** | Compatibility, label oracle, independence, leakage, confounds | `d1_01_inventory.py`, `d1_02_confounds.py`, `d1_03_label_oracle.py` (+`d1_exec_child.py`), `d1_04_label_audit.py`, `d1_05_independence.py`, `d1_06_leakage_and_edits.py`, `d1_stats.py` | `raw/WPD-D1_compat/FINDINGS.md`, `raw/WPD-D1_compat/data/*`, `oracle/`, `declared_inputs/`, `unit_copies/`, `logs/d1_03_label_oracle.log` | EXECUTED (oracle, AST/token) and READ (git history, docs) |
| **WPD-D2** | Level 1 recompute from stored scores. Level 2 re-execution. Python version, cold-start, nondeterminism. SBG integrity. | `d2_level1_recompute.py`, `d2_level1_vs_a3.py`, `d2_verify_copy.py`, `d2_run.py`, `d2_task_c_*.sh`, `d2_quix_driver.py`, `d2_task_d_*.sh`, `d2_cold_start_probe.py`, `d2_compare_scores.py`, `d2_sbg_integrity.sh`, `d2_make_reproduce_sh.py` (not yet run) | `raw/WPD-D2_repro/{level1,compare,integrity,logs,runs,sbg_copy,command_log.jsonl,copy_verification.json}`. **`REPRO_REPORT.md` and `REPRODUCE.sh` are absent.** | EXECUTED, report INCOMPLETE (§4) |
| **WPD-D3** | Additional dataset feasibility, offline probes | `raw/WPD-D3_datasets/probes/P*.py`, `make_candidates_csv.py` | `FEASIBILITY.md`, `PROBE_LOG.md`, `candidates.csv` (24 rows), `probes/P99_sha256_manifest.txt` | READ + EXECUTED probes, no SBG scoring |
| **WPD-D4** | Statistics: sets, CIs, permutation, zero decomposition, baselines, power, sensitivity, forking paths | `d4_00_selftest.py` … `d4_09_check_report.py`, `d4_lib.py`, `d4_sets.py` | `raw/WPD-D4_stats/STATS_REPORT.md`, `00…07_*.json/csv/log` | EXECUTED on stored scores, post-hoc for non-PRE-REG sets |
| prior claim 1 | A3-007 external recompute | A3 file | `results/raw/EXP-A3-007/external_auroc_recompute.json` | **Verified** by D2 Level 1 (§4.1) |
| prior claim 2 | Real-bug generalisation audit | AUDIT file | `SBG/artifacts/paper_evidence/REAL_BUG_GENERALISATION_AUDIT.md` | Partly **contradicted** (§9) |

---

## 4. Reproduction results (WPD-D2)

**D2 status: INCOMPLETE.** `D2/REPRO_REPORT.md` did not appear. I polled `ls` from 21:44 to 22:05 IST (about 20 min). The last D2 command (`D1_cold_seed0_black23_cwdcopy`, exit 0, 1357 s) finished at about 21:54 and no D2 process was running afterwards. D2 did not produce an aggregated report, `REPRODUCE.sh`, or the full cold-start CSV. `D2/compare/D_cold_start_results.csv` was last written at 21:34 and **does not contain the black23 row**. Everything in this section is read directly from `D2/{level1,compare,integrity,logs,command_log.jsonl}`. The classifications are from `D2/compare/ALL_COMPARISONS_SUMMARY.csv` (D2's own per-pair criteria, not mine). D2's own interpretation is missing.

Classification rule (`scripts/d2_compare_scores.py`): **EXACT** means every score is equal. **WITHIN-TOLERANCE** means evaluated flags are equal, every pair's |sbg_v5 diff| ≤ 1e-3, and |ΔAUROC| ≤ 1e-3. **NOT-REPRODUCED** is anything else. The tolerance was fixed after B1 and before B2, B3 and C were seen. It is strict: a single pair beyond tolerance gives NOT-REPRODUCED even when ΔAUROC is small.

### 4.1 Level 1 — recompute AUROC from stored per-pair scores (own stdlib code)

| Result | Tag |
|---|---|
| 12 of 16 A3-007 rows reproduce to 4 d.p. for both AUROC and CI (BugsInPy v7 all / ex-SP-2 / unevaluated=0; QuixBugs v7 all / ex-SP-2 / unevaluated=0; v8 BugsInPy all and ex-SP-2; v8 QuixBugs all and ex-SP-2; the two "v7 on v8 pair set" rows). The 4 seed-7 rows are `NOT_COMPARED` (D2 used seed 42 only). `all_compared_slices_match: true`. | **REPRODUCED-EXACT** (source: `D2/level1/level1_vs_A3-007.json`) |
| The A3-007 claim is therefore correct as arithmetic on the stored scores. It says nothing about whether the stored scores regenerate. | — |
| Stored v8 rows embed the committed v7 score exactly (max |diff| 0.0). v8 − v7 changed 51 of 147 BugsInPy scores (max |diff| 0.795). | READ (`D2/level1/level1_results.json`) |
| Funnel: BugsInPy 200 pairs → 53 unevaluated (49 `unsupported_signature`, 4 `import_error`; 14 are positives) → 147 evaluated. QuixBugs canonical 152 pairs, 0 unevaluated in v7 and 1 (`mergesort` positive, nonterminating) in v8. Declared 152 → 53 unevaluated. 504 CSV rows, 214 with a drop reason (`D2/level1/dropped_pairs.csv`). | EXECUTED |
| Freeze check on the copy used for Level 2: BugsInPy combined sha256 (256 files), QuixBugs manifest, negatives (112) and corpus (131) all match the frozen digests. 20,966 files in the copy equal the original with 0 differing (`D2/copy_verification.json`). | EXECUTED |

### 4.2 Level 2 — re-execution of the tracer (py3.13 is SBG's pinned version, `SBG/.python-version` = 3.13)

AUROCs are D2's own on the both-evaluated rows. "Pairs beyond tol" counts pairs whose |sbg_v5 diff| > 1e-3.

| Config | Committed AUROC all / ex-SP-2 | Re-run all / ex-SP-2 | Pairs exact / beyond tol | Class |
|---|---|---|---|---|
| **B1** BugsInPy v7, py3.13 (`D2/compare/B1_bugsinpy_v7_py313.json`) | 0.4099 / 0.4715 | 0.4099 / 0.4715 | 130 / 0 (max |diff| 6.5e-4) | **WITHIN-TOLERANCE** |
| **B2** QuixBugs canonical v7, py3.13 | 0.3877 / 0.4507 | 0.3805 / 0.4380 | 145 / 4 | **NOT-REPRODUCED**. 4 pairs: `mergesort` positive evaluated→non-terminating, plus 3 `powerset` pairs. ΔAUROC −0.007. |
| **B2** QuixBugs declared v7, py3.13 | 0.7022 / 0.6684 | 0.7007 / 0.6699 | 96 / 1 (5 flagged) | **NOT-REPRODUCED**. `gcd` positive and `knapsack` SP-3 became unevaluated. 3 `mergesort` negatives became evaluated. `sieve` differs by 0.040. |
| **B3** v8 rescore, BugsInPy (147 pairs) | 0.4159 / 0.4970 | 0.4154 / 0.4967 | 143 / 0 (max 2.9e-4) | **WITHIN-TOLERANCE** |
| **B3** v8 rescore, QuixBugs canonical (151 pairs) | 0.3842 / 0.4444 | 0.3842 / 0.4444 | 151 / 0 | **REPRODUCED-EXACT** |

Reading of Level 2: the headline v8 numbers regenerate on the pinned interpreter (0.497 within 3e-4, 0.444 exact). The v7 BugsInPy value regenerates. The v7 QuixBugs value (0.388) does not regenerate exactly. The re-run gives 0.3805, with a different `mergesort` termination status and `powerset` scores.

### 4.3 Python-version effect (re-scores of the same frozen copy)

BugsInPy v7, evaluated 147 pairs; QuixBugs canonical v7, 151 both-evaluated pairs. Source: `D2/compare/ALL_COMPARISONS_SUMMARY.csv`.

| Interpreter | BugsInPy all / ex-SP-2 | Pairs exact / beyond tol (BP) | Class (BP) | QuixBugs all / ex-SP-2 | Pairs exact / beyond tol (QB) | Class (QB) |
|---|---|---|---|---|---|---|
| committed (reference) | 0.4099 / 0.4715 | — | — | 0.3877 / 0.4507 | — | — |
| **3.13** (pinned) | 0.4099 / 0.4715 | 130 / 0 | WITHIN-TOLERANCE | 0.3805 / 0.4380 | 145 / 4 | NOT-REPRODUCED |
| 3.11 | 0.4067 / 0.4712 | 96 / 41 | NOT-REPRODUCED | 0.3848 / 0.4444 | 141 / 8 | NOT-REPRODUCED |
| 3.14 | 0.4101 / 0.4745 | 108 / 10 | NOT-REPRODUCED | 0.3759 / 0.4373 | 145 / 4 | NOT-REPRODUCED |
| 3.9 | **0.4378 / 0.5155** | 82 / 51 | NOT-REPRODUCED | **0.4663 / 0.5712** | 120 / 29 | NOT-REPRODUCED |

- Pair-level scores move materially off the pinned interpreter. On 3.9, 51 of 147 BugsInPy pairs and 29 of 151 QuixBugs pairs are beyond tolerance.
- The aggregate AUROC is stable on 3.11, 3.13 and 3.14 (within about ±0.01).
- **BLOCKED / not interpretable as a replication:** 3.9 moves the QuixBugs AUROC by +0.079 (ex-SP-2 +0.121). The direction and size of this effect is measured, but D2 wrote no analysis of the cause. Python 3.9 is outside the pinned version.
- The BugsInPy 3.14 maximum pair difference is 0.666, on the `black/23` cold-start unit (§4.4).
- The headline numbers are therefore interpreter-dependent beyond the stated precision.

### 4.4 Cold-start / self-distance and nondeterminism

| Observation | Value | Source | Tag |
|---|---|---|---|
| `black/21` `dump_to_file` base: the first extraction in a process has 5756 events and the 2nd and 3rd have 945. First-vs-second self-distance (sbg_v5) is **0.6897**; second-vs-third is 0.0. Identical under PYTHONHASHSEED 0 and 1. | 0.6897 | `D2/compare/D_cold_start_results.csv` | EXECUTED |
| `youtube-dl/37` `uppercase_escape`: events 2934/2124/2124, self-distance 0.5966, identical under seeds 0 and 1. | 0.5966 | same | EXECUTED |
| `black/23` `assert_equivalent`: events 22351/17440/17440, self-distance 0.7301. Run in a cwd copy. A plain run **timed out at 420 s** (exit 124), and the cwd-copy run took 1357 s. | 0.7301 | `D2/logs/D1_cold_seed0_black23_cwdcopy.log`, `command_log.jsonl` | EXECUTED (CSV row missing) |
| `ansible/11` control: no cold-start effect. | 0.0 | CSV | EXECUTED |
| QuixBugs `powerset` base: events vary run to run (21404/21252/21460, 21304/21397/21274, 21350/21324/21399) while consecutive self-distance is 0.0. | 0.0 | CSV | EXECUTED |
| Self-distance v8: committed vs B3 re-run max 0.67346 vs 0.67376 (BugsInPy). QuixBugs `correct_python_programs` is 0.0262 in both. | within 3e-4 | `D2/compare/D_self_distance_v8_committed_vs_B3rerun.json` | **WITHIN-TOLERANCE** |
| `re.purge` diagnostic (EXPLORATORY): purged BugsInPy AUROC re-run 0.4289 vs committed purged 0.4294 (143/147 pairs exact, max diff 2.9e-4). 41 of 147 pairs change score under purge. | 0.4289 | `D2/compare/D2_diagnose_bugsinpy_cache_vs_committed.json` | WITHIN-TOLERANCE |
| **Nondeterminism, same py3.13, same config.** BugsInPy B1 vs repeat: 147/147 exact. QuixBugs repeat2 and seed2 vs B2: 151/151 exact. QuixBugs **repeat1 and seed1 vs B2: 1 pair differs** (`powerset` SP-3: 0.0146 vs 0.0408, |diff| 0.026). The py3.9 QuixBugs runs (repeat1, seed1) are mutually consistent at 0.4663 / 0.5712. | — | `D2/compare/C_quix_py313_*`, `C_bp_py313_repeat_*` | EXECUTED. The QuixBugs run is **not bit-deterministic**, localised to the `powerset` cold-start unit. |

Effect on the claims: the cold-start effect is localised in 3 BugsInPy base units and 1 QuixBugs base. D4 shows removing them changes the headline numbers by at most 0.01–0.02 (D4 §7: 0.4159→0.4059 and 0.497→0.495; QuixBugs 0.3842→0.3704). So cold-start contamination does not explain the results, contrary to AUDIT §3 / §5.

### 4.5 SBG integrity (D2)

`D2/integrity/summary.txt`: `diff rc=0 lines=0 before=16137 after=16137`. D2 re-hashed exactly the files listed in `logs/sbg_tree_sha256_BEFORE.txt` (16,137 files in the SBG tree) after all D2 work, and there is no difference. Stderr is empty. See §10.

---

## 5. Baselines and shortcut results

All AUROCs are D4 (EXECUTED on stored scores), unless marked. PRE-REG sets used the Holm family of 5 baselines. `sbg_state` is not in the family and is exploratory.

| Set | SBG V5 | Static / trivial baselines (PRE-REG sets unless marked) | Reading |
|---|---|---|---|
| BugsInPy v7 EVAL (41/106) | 0.410 | `static_ast` **0.636** [0.561, 0.710] (Δ vs SBG +0.226, Holm p = 0.002). `static_token` 0.451. `exception_fraction` 0.495. `call_count` 0.476. `sbg_v3` 0.440. `sbg_state` 0.511 (exploratory). | SBG is not better than any trivial baseline. `static_ast` is significantly better. |
| QuixBugs canonical v7 ALL (40/112) | 0.388 | `static_token` **0.209**. `static_ast` 0.490. `call_count` 0.550 and `exception_fraction` 0.516, both better than SBG after Holm. | SBG is beaten by trivial baselines. |
| QuixBugs canonical v8 ex-SP-2 (POST-HOC) | 0.444 | `static_token` 0.119. `static_ast` 0.274. | same |
| QuixBugs **declared** v7 EVAL (24/75) | **0.702** | `static_token` 0.182 (reversed 0.818). `static_ast` 0.462. `call_count` 0.645 (not significantly lower). `sbg_state` 0.738. | The one above-chance result. A reversed static baseline reaches or exceeds it, and 24 of 40 programs survive. |

**Label-source shortcut checks (post-hoc, label-aware direction choice, diagnostics only):**

| Feature | Result | Source |
|---|---|---|
| `variant_is_unparse_canonical` | AUROC 0.000 = 1.000 reversed. Perfect on BugsInPy and both QuixBugs corpora (1 for every negative, 0 for every positive). | D4 §5, D1 C1 |
| Header-independent format score | **0.915** [0.845, 0.974] BugsInPy (41/106); **1.000** QuixBugs (39/112). | D1 §1.2 |
| `edit_lines` (BugsInPy v7 EVAL) | 0.084, reversed 0.916. | D4 §5 |
| Edit size, QuixBugs ex-SP-2 | Reversed `static_token` 0.88, `static_ast` 0.73, normalised line edit 0.81, versus SBG 0.444. | D1 C2 |
| Zero-score decomposition | P(s=0 \| positive) vs P(s=0 \| negative): BugsInPy v7 EVAL 51% vs 29%; QuixBugs v7 ALL 80% vs 49%. The hurdle difference is negative (negatives detected as changed more often than real fixes). Fisher p = 0.020 and 0.0007 (PRE-REG sets). | D4 §4 |
| Tie sensitivity of the 0.444 set | 0.177 (ties→0), 0.444 (ties = ½), 0.712 (ties→1). | D4 §4 |
| Unevaluated-pair imputation, BugsInPy v8 all types | zero 0.431, half 0.440, neutral 0.454, Manski bounds **0.227–0.682** | D4 §7 |
| Forking paths | 21 external AUROC variants on record (11 BugsInPy, 7 QuixBugs canonical, 3 declared). 9 of 11 BugsInPy and 7 of 7 canonical QuixBugs variants are < 0.5. No multiplicity control exists. | D4 §8 |
| Label-consistent subset (EXPLORATORY, partly circular) | BugsInPy 2 pos / 94 neg, AUROC 0.596 [0.15, 1.00]. QuixBugs 7 pos / 110 neg, 0.849 [0.60, 1.00]. **Do not cite as validation.** | D1 §2.4 |

---

## 6. Additional datasets (WPD-D3) and the SeqCoBench replication sketch

### 6.1 Summary (D3, feasibility and probes only, no SBG score computed)

| Finding | Value |
|---|---|
| Valid independent evaluation | none |
| Valid with documented adaptation | SeqCoBench only (`nickil/seqcobench`, MBPP-derived, 14,572 rows, 1,134 originals; licence UNVERIFIED) |
| Real-bug validation beyond BugsInPy / QuixBugs feasible offline in ≤ 2 h | none |
| HumanEvalFix | 164/164 statically eligible. Bug observable on the battery in only **86/164 (52.4%)**. 47/164 canonical solutions raise on all 11 inputs. Minifier negatives give reversed edit-size AUROC 0.765. |
| Refactory | 5 assignments (5 clusters). 26.5% of "correct" programs differ from the reference on the battery. EQUIVALENT label not reproduced. |
| EquiBench OJ | 2/4/2 usable pairs of 400. Not suitable. |
| SeqCoBench observability | 38.3% of "changed" rows are battery-unobservable. 31% of rows have an original that raises on all 11 inputs. Usable e ≤ 2 stratum: 735 SP + 629 CH pairs from 486 programs (260 with both classes). Static label-only shortcut: token-bag reversed 0.824 within e ≤ 2 (0.947 pooled). |
| Prior in-repo numbers | SeqCoBench 332 zero-exception originals (prior) vs 329 (D3). e = 2 programs 188 vs 184. "Plausible but not exactly reproduced"; do not reuse without regeneration (D3 §8). |

### 6.2 SeqCoBench replication sketch (WPD-X1) — **NOT EXECUTED**

**Planned only. Needs an authorised scoring session. Not run in WP-D. No SBG score exists for this dataset.**

| Item | Frozen-before-extraction specification (D3 §9) |
|---|---|
| Population | Pool of train, valid and test CSVs (record sha256). Same selected entry in A and B. Original not raising on all 11 inputs. AST differs. Exact overlap with SBG corpus excluded (2 trivial matches). Programs non-deterministic across two oracle runs excluded and logged. |
| Primary stratum | e ≤ 2, AUROC primary metric. |
| Label | `1 − SeqCoBench label`, validated by battery differential execution. 13 SP-but-differs and 391 CH-unobservable rows go to separate logged strata. |
| Scoring | Frozen SBG V5 (0.5/0.25/0.25), τ* from V9c-train, no tuning, scored once. |
| Statistics | Cluster = original program. Cluster bootstrap B = 2000, seed 42. One-sided within-program permutation. Baselines: token-bag (both directions), edit size, AST bag, `static_token`, `static_ast`, exec-statistics. Paired ΔAUROC with Holm. |
| Failure criteria | F1: lower 95% CI ≤ 0.5. F2: SBG does not beat the best static baseline (paired Δ CI includes 0). Either is reported as a negative result. |
| Claim ceiling | "Independent-generator synthetic replication". Not real-bug external validation. |

---

## 7. Java / cross-language status

| Item | Status | Source |
|---|---|---|
| SBG-schema Java result (`QUIXBUGS_JAVA_SBG_RESULTS.json`, `pairs_quixbugs_java.jsonl`, `JAVA_CLAIM_REMOVAL.json`) | **does not exist** (file-existence check) | D1 §5 |
| Existing Java numbers | Aug-2026 EEP pilot (ENTER/EXIT markers, 5-feature formula, τ = 0.08): 6/18 detected. Not an SBG-schema measurement. | D1 §5 (READ) |
| Java infrastructure | `external/quixbugs_java/` (40 buggy + 40 correct programs), JDI tracer, `external_java.py`. Agent-5 readiness report: 12 tests pass, 30/40 programs canonical-eligible, 3-program smoke run mechanical only. | D1 §5 (READ) |
| Java executed in WP-D | **No** (JDK 21 present, deliberately not run) | D1 §5, §7.1 |
| Cross-language generalisation | **None demonstrated.** Pre-registration §6 says Java counts as SBG only if the full schema is produced, otherwise the claim is removed. | D1 §5 |

---

## 8. What failed / what could not be done / continuation commands

| # | Item | Status |
|---|---|---|
| 1 | **D2 report absent** (INCOMPLETE). No `REPRO_REPORT.md` or `REPRODUCE.sh`. `D_cold_start_results.csv` lacks the `black/23` row. D2's interpretation of the Python 3.9 effect is missing. | Not done |
| 2 | Python 3.9 QuixBugs and BugsInPy aggregate shift (+0.079 / +0.028) not diagnosed | Not done |
| 3 | `black/23` plain cold-start probe timed out (420 s, exit 124). The cwd-copy re-run took 1357 s. | Failed then re-run |
| 4 | Java not executed | Not done (D1) |
| 5 | D1 did not re-trace SBG. Its oracle uses a 1.0 s timeout vs 2.0 s in V10, a single run, py3.13, and v8-style entry policy. 47 vs 41 positives not reconciled. | Limitation |
| 6 | EXP-A3-011 "max 0.17 overlap" not located. D1 finds max identifier-Jaccard 0.147 (BugsInPy) and **0.444** (QuixBugs). | Not confirmed for QuixBugs |
| 7 | V10 test and V9c were not compared for independence | By design |
| 8 | D3: Refactory `fail/` (163 files) not run. Several guessed GitHub URLs returned 404 (UNVERIFIED, not disproven). Large datasets not downloaded. SeqCoBench licence, `groups` meaning, EquiBench authors UNVERIFIED. | Not done |
| 9 | D4: `within_unit_stratified` 0.4018 (BugsInPy) **not reproduced** (D4 gets 0.3922 pooled within-bug and 0.3618 within-unit-family; the weighting is undocumented). The QuixBugs 0.3884 is reproduced. | Not reproduced |
| 10 | D4 power model is a simplified censored-binormal (order of magnitude). Bootstrap with 10–12 project clusters is optimistic. | Limitation |
| 11 | SeqCoBench replication (WPD-X1) | NOT EXECUTED (§6.2) |

**Exact continuation commands** (no SBG scoring is run by these; each is taken from the source reports or `command_log.jsonl`):

```bash
cd /Users/manassakthivel/Desktop/SBG-FINALREVIEW
export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1
PY=venvs/py313/bin/python
W=IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION

# D4 (stats, from stored scores; D4 §11)
for s in 00_selftest 01_sets 02_inference 03_zero_decomposition 04_baselines 05_power 06_sensitivity 07_forking_paths 08_render 09_check_report; do $PY $W/scripts/d4_$s.py; done

# D1 (static ledgers + sandboxed oracle of program copies; D1 §8; run from $W)
(cd $W && for s in 01_inventory 02_confounds "03_label_oracle --workers 4" 04_label_audit 05_independence 06_leakage_and_edits; do $PY scripts/d1_$s.py; done)

# D3 (probes; D3 §11; run from $W/raw/WPD-D3_datasets)
(cd $W/raw/WPD-D3_datasets && for p in P10_seqco_prepare P10_seqco_run P13_analyze_seqco P14_seqco_static_shortcut P16_seqco_prior_crosscheck; do $PY -W ignore probes/$p.py; done; (cd probes && shasum -a 256 -c P99_sha256_manifest.txt))

# D2 Level 1 (arithmetic on stored scores) and A3 cross-check
$PY $W/scripts/d2_level1_recompute.py SBG $W/raw/WPD-D2_repro/level1
(cd $W/raw/WPD-D2_repro && $PY ../../scripts/d2_level1_vs_a3.py level1/level1_results.json ../../../results/raw/EXP-A3-007/external_auroc_recompute.json level1/level1_vs_A3-007.json)

# D2 finish (missing artefacts): generate REPRODUCE.sh from the executed log, re-hash SBG, then write REPRO_REPORT.md
$PY $W/scripts/d2_make_reproduce_sh.py
bash $W/scripts/d2_sbg_integrity.sh
# D2 Level 2 re-execution commands are exactly those recorded in
#   $W/raw/WPD-D2_repro/command_log.jsonl (72 entries; each has command, cwd, env, exit_code, runtime_s).
#   They depend on the copies in raw/WPD-D2_repro/{sbg_copy,runs/*} and on an authorised scoring session.
```

SeqCoBench replication (WPD-X1): see §6.2. Freeze config and script sha256 first, then run it in an authorised scoring session.

---

## 9. Claims: supported / unsupported / contradicted

| Claim | Verdict | Basis |
|---|---|---|
| A3-007 arithmetic (12 comparable slices) | **Supported** | D2 Level 1 matches 4 d.p. (§4.1) |
| 0.497 and 0.444 regenerate from stored scores and on a py3.13 re-run | **Supported** | §4.1–4.2 |
| 0.497 / 0.444 are "the corrected results" (AUDIT §5, §7) | **Unsupported** | Post-hoc: they need the v8 rescore and the SP-2 deletion, which was chosen after the full-set results were seen (D1 §3.2, D4 §0.1, §7) |
| "SBG is at approximately chance" (AUDIT §5) | **Contradicted for the pre-registered sets** | v7 EVAL 0.410 and QuixBugs 0.388 are below 0.5 (p = 0.015 and 0.007). Ex-SP-2 values are indistinguishable from 0.5 in either direction (D4 F2, F3). |
| 7 invalid SP-2 BugsInPy negatives (`fix_kv`) | **Supported but incomplete** | D1 executed 9 broken SP-2 negatives in BugsInPy (7 youtube-dl + 2 matplotlib `_make_getset_interval` 24/26). Frozen variants were not regenerated after the SP-2 fix (D1 §2.2). |
| AUDIT: removing the 7 gives ≈0.445 | **Supported** | D4 §7 gives 0.4453 (v8) |
| AUDIT: artefacts (invalid negatives + self-distance) explain the sub-chance values, "near-chance is correct given the zero-score rate" | **Contradicted** | The 7 invalid negatives explain ≈0.03 of the +0.081. Contamination is immaterial (0.416→0.406; D4 §7). The sub-0.5 values are driven by valid SP-2/SP-3 negatives ranked above real fixes (D4 F7) and by the label-source confound. |
| AUDIT: "63–82% of positives score 0, therefore AUROC cannot exceed chance in expectation" | **Contradicted** | D4 §4 / F9: ties-as-½ AUROC depends on the relative zero rates, with a range 0.334–0.660 on the same data. The empirical driver is that negatives are detected more often than positives. D1 gives a better-grounded cause: positives are unobservable under the SBG label definition. |
| AUDIT: "26/41 BugsInPy, 32/39 QuixBugs zero" | **Supported for v8** | D4 §4 (63.4% = 26/41; 82.1% = 32/39). v7 BugsInPy is 21/41. |
| AUDIT: "canonical inputs are the originally provided test inputs" | **Contradicted** | Canonical inputs are the fixed 11-input batteries. The repo's test inputs are the *declared* regime (D1 §1.1). |
| AUDIT: "Leakage: none; overall validity valid" | **Unsupported** | The external programs were seen by developers in Aug 2026, and the pre-registration was committed after the v6 results (D1 §3.2). The label is incompatible with the SBG task (D1 §2.1). The labels are source-confounded (D4 §5). |
| AUDIT: output-free protocol hides return-value differences (second mechanism) | **Not tested** | Neither D1 nor D4 tests it. D1's oracle does observe return values. |
| "SBG does not generalise to real bugs" (mechanism / negative-result claim) | **Unsupported** | The label is incompatible. The decisive result is only "no evidence of AUROC ≥ 0.6" (D4 §0.4). |
| "SBG generalises / is externally validated" (any external claim) | **Unsupported** | No VI dataset. Both corpora are EX. Java has no SBG result. |
| QuixBugs declared 0.702 as positive evidence | **Unsupported as validity evidence** | 28/40 programs survive. Declared inputs come from the repo's tests. Reversed `static_token` 0.818 ≥ SBG (D4 F8, D1 §6). |
| External programs overlap SBG training or thresholds | **Not found** | τ is derived from dev programs only (D1 §3.2). External-ness is not a priori, though. Text overlap max Jaccard 0.147 / 0.444; algorithm-level overlap in QuixBugs. V10/V9c not compared. |
| v7 results are bit-reproducible | **Contradicted** for QuixBugs and for other interpreters | §4.2–4.4. QuixBugs v7 re-run 0.3805 vs 0.3877. Interpreter changes alter pair scores. |
| Cross-language (Java) generalisation | **Unsupported** | No SBG-schema Java result (§7) |
| SeqCoBench replication result | **Does not exist** | NOT EXECUTED (§6.2) |

---

## 10. Integrity statement

| Check | Result | Source |
|---|---|---|
| SBG tree re-hash after D2 work | `diff rc=0 lines=0`, 16,137 files before and after, empty stderr | `D2/integrity/summary.txt`, `diff.txt`, `sbg_AFTER_D2.stderr` |
| D2 working copy | Verified identical to the frozen digests and to the original (20,966 files, 0 differing). All D2 re-execution ran in `raw/WPD-D2_repro/{sbg_copy,runs/*}` copies. | `D2/copy_verification.json` |
| WP-D check of `SBG/` git state (D1) | `git -C SBG status --short` shows only pre-existing entries (4 untracked `*_v8.json(l)` dev files, `paper/`, `reports/sprint2/`). D1 states the same. I re-ran the status command read-only for this report and it matches. | D1 header; W2 read-only check |
| D3 housekeeping flag (resolved) | `SBG/.pytest_cache/v/cache/{nodeids,lastfailed}` mtime is 2026-11-14 18:34, earlier than `PKG/logs/sbg_tree_sha256_BEFORE.txt` (18:41) and than WP-D start (~20:40); `.pytest_cache` is not in the BEFORE/AFTER hash lists (excluded by the hash scope; git-ignored). Not written by WP-D. | `stat` check by WP-D lead; D3 §11 |
| V10 test / V9c validation | **Not rescored and not read** by WP-D. D1 excluded the V10 / V9c trees from independence checks. D3 and D4 scored nothing. D2 re-scored only BugsInPy and QuixBugs external pair files. | D1 §3.1, D3 header, D4 §10 |
| Tuning on external labels | **None.** D4 states nothing was tuned on external labels. D1's label-consistent subset filter is label-aware, never reads an SBG score, and is marked exploratory. The label-aware shortcut features are diagnostics, not models. | D4 header, D1 §2.4 |
| W2 (this report) | Wrote this file only. No SBG scoring was run. | — |

**Caveat.** D2's report is missing, so D2's own integrity narrative is read from its raw files only. The D2 re-hash result is a sha256 comparison over exactly the files listed in `logs/sbg_tree_sha256_BEFORE.txt` (`scripts/d2_sbg_integrity.sh`). It does not cover files absent from that manifest.
