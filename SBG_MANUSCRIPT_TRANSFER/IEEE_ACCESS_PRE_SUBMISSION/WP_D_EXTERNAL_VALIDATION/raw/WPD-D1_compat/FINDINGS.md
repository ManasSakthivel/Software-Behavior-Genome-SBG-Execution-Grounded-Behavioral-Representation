# WPD-D1 — Dataset compatibility, label reliability, independence and leakage

Subagent D1 of WP-D (external validation) for Software Behavior Genome (SBG). Python 3.13 (`venvs/py313`), stdlib only, `PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1`.
`SBG/` was treated as read-only: `git -C SBG status --short` after all work shows only the pre-existing entries (4 untracked `*_v8.json(l)` dev files, `paper/`, `reports/sprint2/`). V10 test and V9c validation were not read, scored or executed.

**Evidence tags used on every claim**

| Tag | Meaning |
|---|---|
| **EXECUTED** | I ran code that produced the number, either on stored per-pair scores (arithmetic only), on program text (AST/tokens), or by running program copies under a sandboxed harness. |
| **READ** | I read a file or git history and am quoting it. I did not recompute it. |
| **NOT-DONE** | Not performed (reason stated). |

D1 did **not** re-trace SBG scores. All SBG AUROCs below are recomputed from SBG's stored per-pair scores (`artifacts/paper_evidence/raw/external_rescore_v8_pairs.json`, `artifacts/final/pairs_*_output_free_v7.jsonl`). Whether those scores can be regenerated is D2's question.

---

## 0. Verdict summary

| Corpus | Recommended classification | One-line reason |
|---|---|---|
| BugsInPy (51 bugs / 55 units; 41 positives scored) | **Exploratory only** (arguably Not methodologically suitable as validation evidence) | Task mismatch: 34 of 47 comparable fixed programs raise on all 11 SBG inputs, so only 2 of 47 real-bug positives are CHANGED under the SBG label definition. Eligibility is 10.2%. Lineage duplicates, 9 broken SP-2 negatives, and the format and edit-size shortcut. Seen by developers before the "frozen" evaluation. |
| QuixBugs-Python, **canonical** inputs | **Exploratory only** (the SBG label is invalid for 80% of positives under this regime) | Type-mismatched canonical inputs: 8 of 40 positives are CHANGED, 27 of 40 base programs raise on at least 10 of 11 inputs. The AUROC reflects the format and edit-size shortcut plus input type mismatch, not behavioural-change detection. Seen by developers in Aug 2026. |
| QuixBugs-Python, **declared** inputs | **Exploratory only** (closest to "Valid with documented adaptation", but the conditions are not met) | 28 of 31 comparable positives are oracle-CHANGED, so the task is compatible. But it is evaluable on only 99 of 152 pairs (28 of 40 programs), selected by evaluability. Inputs come from the repo's own test cases. Not a-priori independent, and a reversed static edit-size baseline (AUROC ≈ 0.82–0.90) beats SBG (0.70). |
| QuixBugs-**Java** | **Not evaluated; not methodologically suitable as evidence** | No SBG-schema Java result exists anywhere. The only Java numbers are an Aug-2026 pilot of a different method (EEP formula). No cross-language evidence. |

These are D1's compatibility and reliability classifications. They are not the IEEE Access submission decision.

---

## 1. Task definitions and structural confounds

### 1.1 SBG task vs external task (READ)

* **SBG label** (`PKG/configs/PROTOCOL.md` §2): CHANGED means the return value, exception, stdout or argument mutation differs on the protocol's 11 synthesised inputs. EQUIVALENT means a semantics-preserving transformation. It is explicitly not general semantic (non-)equivalence.
* **External label** (`SBG/docs/current/PHASE2_PREREGISTRATION.md` §6; `SBG/experiments/final/external_common.py::generate_sp_negatives`):
  * Positive = real bug pair, base = fixed program, variant = buggy program.
  * Negative = fixed program vs a variant produced by SBG's own SP transformers. Seed 0, up to 3 per program, order SP-1, SP-2, SP-4, SP-6, SP-10, SP-3, SP-5, SP-9, accepted if it compiles and the AST differs.
* **Canonical inputs** (`SBG/experiments/final/protocol.py`): fixed batteries by annotation. An unannotated parameter gets the LIST battery of 11 lists. Nearly all QuixBugs and BugsInPy parameters are unannotated.
* **Declared regime** (`SBG/experiments/final/external_quixbugs.py`): `load_declared_inputs` takes only the input half of `json_testcases`. Expected outputs are not used for the SBG score. The `output_reference` field compares fixed and buggy return values, not expected outputs.

### 1.2 Confound table (EXECUTED; `scripts/d1_02_confounds.py`, `d1_06_leakage_and_edits.py`)

| # | Confound | Evidence | Consequence |
|---|---|---|---|
| C1 | **Format fingerprint**. Every negative is an `ast.unparse` product. Positives are developer-formatted. | 145/145 BugsInPy and 112/112 QuixBugs negatives are `ast.unparse` fixed points. 0/55 and 0/40 positives are. | A header-independent format score (share of code lines that are not verbatim lines of `ast.unparse(variant)`, docstrings and comments excluded) gives AUROC **0.915** [0.845, 0.974] on BugsInPy (41 pos / 106 neg) and **1.000** on QuixBugs (39 / 112). Within-cluster: 0.90 and 1.00. Excluding SP-2 changes nothing. A static learner can separate the labels without seeing behaviour. SBG's score is execution-based and does not use this, but the benchmark cannot discriminate "detects behavioural change" from "detects a text shape". |
| C2 | **Edit-size shortcut**. Real bugs are 1–2-line edits. SP negatives are large mechanical rewrites. | QuixBugs excl. SP-2: `static_token` AUROC 0.119, `static_ast` 0.274, normalised line edit 0.187. Reversed (1 − x), edit smallness gives 0.88 / 0.73 / 0.81, vs SBG 0.444. BugsInPy excl. SP-2: raw line edit 0.074 (reversed ≈ 0.93); `static_token` 0.421 and `static_ast` 0.443 are near chance. Declared (v7 excl. SP-2): `static_token` 0.105 (reversed ≈ 0.90), vs SBG 0.668. | A "smaller edit means real bug" rule beats SBG in QuixBugs canonical and declared, and on raw line edit in BugsInPy. The task is dominated by edit type. SBG's own `STATUS.md` says the same for V10. |
| C3 | **Docstring artefact in QuixBugs**. Buggy files carry ≈19 explanatory lines that fixed files lack. | Raw line edit AUROC 0.70, but docstring-stripped normalised edit 0.22. Normalised positives differ from the fix by 1–2 lines (36 with 2 lines, 4 with 1 line). | A naive size feature is misleading in both directions. Features must be docstring-normalised. |
| C4 | **SP-2 entry rename**. SP-2 renames the entry function in 100% of SP-2 pairs and in 0 positives. | 40/40 SP-2 pairs in each corpus change the entry name. SBG V5 is non-zero on 36/40 (BugsInPy) and 29/40 (QuixBugs) SP-2 negatives. Positives vs SP-2 negatives AUROC 0.282 (BugsInPy), 0.276 (QuixBugs). | SP-2 negatives look more "changed" than the real bugs, so they drive the AUROC below 0.5. The headline numbers (0.497, 0.444) exclude SP-2. That exclusion was chosen after the full-set results were seen (§3.2). |
| C5 | **Positive observability**. Real-bug labels are not observable on SBG's 11 inputs (§2.1). | 32 of 39–40 QuixBugs and 26 of 41 BugsInPy real-bug pairs have SBG V5 exactly 0 (stored pair data). | A zero score is the correct answer under the SBG definition, yet the pair is labelled positive. |

Within-cluster label balance (EXECUTED): BugsInPy clusters are mostly (3 neg, 1 pos) or (2 neg, 1 pos). QuixBugs, all 152 pairs, is (3,1) ×32 and (2,1) ×8; in the v8-evaluated set one cluster has 3 negatives and 0 positives, because its positive was dropped as nonterminating. Within-cluster AUROCs are close to the pooled ones (BugsInPy 0.43 on all v8 pairs and 0.53 excl. SP-2; QuixBugs ≈ 0.38 and 0.45), so cluster structure is not what produces the near-chance numbers.

### 1.3 Recomputed headline numbers (EXECUTED arithmetic on stored scores; `confound_summary.json`, `leakage_summary.json`)

| Corpus / set | AUROC | Cluster-bootstrap 95% CI (B=2000, seed 42) | Pairs (pos) | Note |
|---|---|---|---|---|
| BugsInPy v8 excl. SP-2 (**the "0.497"**) | 0.497 | [0.402, 0.596] | 107 (41) | post-hoc exclusion |
| BugsInPy v8 all | 0.416 | [0.322, 0.514] | 147 (41) | |
| BugsInPy v7 committed, all | 0.410 | [0.326, 0.494] | 147 (41) | |
| QuixBugs canonical v8 excl. SP-2 (**the "0.444"**) | 0.444 | [0.355, 0.539] | 111 (39) | post-hoc exclusion |
| QuixBugs canonical v8 all | 0.384 | [0.285, 0.490] | 151 (39) | 1 pair dropped as nonterminating |
| QuixBugs canonical v7 committed, all | 0.388 | [0.285, 0.503] | 152 (40) | |
| QuixBugs declared v7 | 0.702 | [0.584, 0.817] | 99 (24) | 28-program subset selected by evaluability |

**Both headline numbers are post-hoc SP-2-excluded subsets.** The unfiltered numbers are lower (0.416, 0.384).

BugsInPy CI under alternative cluster definitions (EXECUTED; `d1_06`; v8 excl. SP-2, AUROC 0.497 in all rows):

| Cluster unit | #clusters | 95% CI |
|---|---|---|
| bug id (reported) | 39 | [0.402, 0.596] |
| fixed-unit content cluster (5-gram Jaccard ≥ 0.5) | 33 | [0.397, 0.607] |
| project\|file\|unit lineage | 32 | [0.413, 0.607] |
| project | 11 | [0.432, 0.597] |

The CI changes only modestly. The point estimate is indistinguishable from 0.5 under every clustering, and the full-set (v8 all) CI also stays near chance.

---

## 2. Label reliability

### 2.1 Positives: are real-bug labels CHANGED under the SBG definition? (EXECUTED; `d1_03_label_oracle.py`, `d1_04_label_audit.py`)

I ran the V10-style oracle (per input: status, `repr(ret)[:400]`, `repr(args after call)[:400]`, `stdout[:200]`) for base and variant on SBG's 11 protocol inputs. Entry selection uses SBG's own `entry_policy.select_entry_structural` and `class_driver.select_class_entry`, imported read-only.

| Corpus / regime | Positives in manifest | Comparable | Oracle-CHANGED | Fraction CHANGED | Base raises on all 11 inputs |
|---|---|---|---|---|---|
| BugsInPy canonical | 55 | 47 (7 class-tier `unsupported_signature` and 1 `import_error` not comparable) | **2** | **4.3%** | **34 of 47** |
| QuixBugs canonical | 40 | 40 | **8** | **20%** | 20 of 40 (27 of 40 raise on ≥ 10/11) |
| QuixBugs declared | 40 | 31 (9 ineligible, not run) | **28** | **90%** | 0 of 31 |

* BugsInPy: both CHANGED positives are function-tier. Restricted to the 41 SBG-evaluated positives it is still 2 of 41.
* QuixBugs canonical base exceptions: TypeError ×22, IndexError ×4, AttributeError ×3, no exception ×13 (counted over the inputs that raise). Example: `bitcount(n)` is given list inputs, so 10 of 11 inputs raise TypeError and the bug `n ^= n-1` is unobservable on the remaining `[]`.
* **Caveat on UNCHANGED**: functions that return a generator are compared by normalised `repr` and not consumed, so UNCHANGED is not conclusive for them. This affects 2 BugsInPy and 2 QuixBugs positives. The unaffected lower bounds are BugsInPy 43 of 47 and QuixBugs 30 of 40 (canonical) UNCHANGED.
* Static edit kind of the 55 BugsInPy positives (EXECUTED; `bugsinpy_positive_edit_kind.csv`): 42 structural or name change, 12 constant-only changes (identical AST structure and names), 1 alpha-equivalent name change (`pandas/167`; this may still be behavioural if an attribute name changed). None is docstring-only or comment-only, so the positives are not non-behavioural edits.

**Interpretation.** Under the SBG task definition, about 80% (QuixBugs canonical) and about 95% (BugsInPy) of the "positive" real bugs are EQUIVALENT in the SBG sense. An SBG AUROC near 0.5 on these labels is the expected outcome of a behaviour-differencing method run on unobservable bugs. It is not evidence of failed external generalisation, and it is not evidence of success. The external label is incompatible with the SBG label definition under canonical inputs.

### 2.2 Negatives: are SP-transformed variants actually EQUIVALENT? (EXECUTED; `label_audit_invalid_negatives.csv`, `label_audit_summary.json`)

| Corpus / regime | Negatives | Comparable | Oracle-CHANGED | By cause |
|---|---|---|---|---|
| BugsInPy canonical | 145 | 121 (21 `unsupported_signature`, 3 `import_error` not comparable) | 14 | **9 genuine broken (NameError)**: 7 youtube-dl `js_to_json` SP-2 (undefined `fix_kv`, matches SBG's `EXTERNAL_NEGATIVE_AUDIT.json`) and **2 matplotlib `_make_getset_interval` SP-2 (matplotlib/24, /26): SP-2 renamed the nested `getter` def but left `getter.__name__ = …` and `return (getter, setter)`, which raises NameError**. **5 harness or repr artefacts**: black `dump_to_file` ×3 (a random temp-file name is returned), spacy/1 `add_codes` (returned class repr contains the renamed qualname), spacy/4 `read_conllx` (generator repr contains the renamed name). |
| QuixBugs canonical | 112 | 112 | 2 | 0 broken. Both are generator-repr artefacts of the SP-2 rename (`flatten`, `kheapsort`). |
| QuixBugs declared | 112 | 85 (27 ineligible, not run) | 3 | 2 generator-repr artefacts (`flatten`, `kheapsort`) and 1 `levenshtein` SP-6 where one input timed out in the variant (the oracle counts timeout = timeout). |

* **New finding vs SBG's audit:** SBG's `EXTERNAL_NEGATIVE_AUDIT.json` reports 7 broken BugsInPy SP-2 negatives, all youtube-dl. My execution finds 2 more (matplotlib), so 9 of the 40 BugsInPy SP-2 negatives are broken. The external variants were frozen on 2026-10-03 and were not regenerated after the SP-2 fix in commit `5cf5211` (2026-10-25); I did not check whether that fix would change the matplotlib variants.
* Per-transformation oracle-CHANGED counts, BugsInPy: SP-2 12/46, SP-3 1/32, SP-4 1/17, SP-1 0/17, SP-6 0/9. QuixBugs canonical: SP-2 2/40, others 0. Excluding repr artefacts, only SP-2 produces genuinely invalid negatives (9 of 40 in BugsInPy, 0 of 40 in QuixBugs).
* The harness differs from SBG's: 1.0 s per input vs V10's 2.0 s, a single run, and Python 3.13.

### 2.3 Eligibility and selection (EXECUTED; `bugsinpy_*_ledger.csv`; taxonomy recomputed and equal to the manifest's)

* BugsInPy: 501 bugs → **51 eligible (10.2%)**. Bug-level exclusions: 408 `no_eligible_unit`, 31 `commit_not_resolvable_upstream`, 10 `change_outside_function_or_method`, 1 `no_non_test_python_file_changed`. 704 candidate units → 55 eligible. Unit-level exclusions: 428 `project_internal_import`, 110 `third_party_import`, 61 `non_literal_or_unresolved_global`, 30 `unit_added_or_removed_by_fix`, 7 `unit_identical_after_normalisation`, 6 `unsafe_module`, 6 `ambiguous_binding`, 1 `local_project_internal_import`. All reasons are preserved per bug and per unit in the ledgers.
* Eligible by project: youtube-dl 17/26, thefuck 7/25, ansible 4/14, scrapy 4/36, black 3/20, keras 3/42, luigi 3/30, pandas 3/166, spacy 3/7, matplotlib 2/28, httpie 1/4, tqdm 1/8. Zero for PySnooper, cookiecutter, fastapi, sanic and tornado. The sample is dominated by self-contained stdlib-only helper functions. It is not representative of BugsInPy.
* Scoring failures (EXECUTED from ledgers): 55 positive units → 41 evaluated (14 failed: 13 `unsupported_signature` — 6 class-tier and 7 function-tier — and 1 `import_error`); 145 negatives → 106 evaluated (36 `unsupported_signature`, 3 `import_error`). The 5 `import_error` files also fail in my harness with `ImportError: cannot import name 'Mapping' from 'collections'` (old upstream code on Python 3.13). That is an environment incompatibility, not a bug-related failure. The failures are reported separately and are not dropped from the tables above.
* QuixBugs: 50 files in the repo, of which 10 are scaffolding (`node` and the `*_test` helpers), leaving 40 subject programs. 40 are canonical-eligible. 31 are declared-eligible, with 9 positives and 27 negatives ineligible. Declared scored pairs: 99 of 152 (5 positive and 5 negative `nonterminating`, 2 positive and 5 negative `harness_error`).

### 2.4 Label-consistent subset (EXPLORATORY; `label_consistent_subset_summary.json`)

Definition: keep a positive iff oracle-CHANGED and a negative iff oracle-UNCHANGED, on v8-evaluated canonical pairs. The filter never reads an SBG score and nothing is tuned.

| Corpus | Kept (pos / neg) | Dropped pos (unobservable) | Dropped neg (invalid) | SBG V5 AUROC | Static-token AUROC |
|---|---|---|---|---|---|
| BugsInPy | 96 (**2** / 94) | 39 | 12 | 0.596 [0.15, 1.00] | 0.245 |
| QuixBugs canonical | 117 (**7** / 110) | 32 | 2 | 0.849 [0.60, 1.00] | 0.214 |

**Do not read these as validation.** BugsInPy has 2 positives, so the number is uninformative. QuixBugs has 7 positives. The filter keeps exactly the positives whose bug is visible on the 11 inputs, and an output-differencing score fires on such pairs by construction, so the selection is partly circular. 31 of 32 dropped QuixBugs positives have SBG V5 exactly 0, and 1 of the 7 retained does. With N = 7 positives, the result is a descriptive observation and not a confidence statement.

---

## 3. Program-level independence

### 3.1 Textual independence (EXECUTED; `scripts/d1_05_independence.py`; `independence_*.csv/json`)

Reference set: 210 SBG base programs (`benchmark/corpus/base_programs`, `benchmark/corpus/fresh_programs`, `benchmark/v5/corpus/base_programs`). **Deliberately not compared:** `benchmark/datasets/v10_independent/**` (V10 test), V9c validation and any val/test variant tree (WP-D rules). SBG variants are derived from these base programs, so base-level overlap is the quantity of interest, but this is a limitation.

| Corpus (fixed programs) | n | max identifier-set Jaccard | max raw 5-gram shingle Jaccard | max structural 5-gram shingle Jaccard |
|---|---|---|---|---|
| BugsInPy units | 55 | **0.147** (mean 0.092) | 0.022 | 0.126 |
| QuixBugs subjects | 40 | **0.444** (`get_factors` vs `fresh_programs/math_catalan_number.py`; mean 0.187; 20 programs ≥ 0.17) | 0.201 | 0.298 (`mergesort` vs `math_median_two_sorted`) |

* The "max 0.17" attributed to EXP-A3-011 could not be located in the repo (NOT-DONE). It is consistent with BugsInPy (my max 0.147). It is **not** reproduced for QuixBugs: my max identifier-set Jaccard is 0.444. The value 0.17 is close to the QuixBugs mean (0.187). I did not establish which statistic EXP-A3-011 used.
* **Algorithm-level overlap in QuixBugs**: `gcd`, `mergesort`, `quicksort`, `sieve` (and `merge`, `get`) are also defined in SBG corpus programs (`math_number_theory`, `sort_mergesort`, `sort_quicksort`, `math_prime_sieve`, …). The text is not near-identical (shingle Jaccard ≤ 0.30), so this is not text leakage, but these are textbook algorithms of the kind the SBG corpus was written around.
* BugsInPy def-name overlaps with SBG are mostly generic dunder or method names (`__init__`, `__repr__`, `__len__`, …), plus `Task`, `update` and similar. No BugsInPy program is a near-duplicate of an SBG program.

### 3.2 Training, threshold fitting and chronology (READ: `THRESHOLD_PROVENANCE.md`, `PHASE2_PREREGISTRATION.md`, `TEST_SET_CHRONOLOGY.md`, `THRESHOLD_FROZEN.json`, `git -C SBG log`)

| Claim | Evidence | Verdict |
|---|---|---|
| External programs were not in SBG training or threshold fitting | `THRESHOLD_FROZEN.json` (τ = 0.072905) is derived from dev programs only (no external ids). | Supported (READ). |
| The external sets were seen by developers before the "frozen" protocol | QuixBugs and BugsInPy were already used in 2026-08-30 sprints: commit `255499f` ("QuixBugs 60.7% detection"), `03ffc18`, `5aa3372`, `4128bf8`. These used τ = 0.08, whose derivation has no record (`THRESHOLD_PROVENANCE.md`). | External-ness is **not a priori**. |
| The preregistration preceded the evidence | `PHASE2_PREREGISTRATION.md` was committed 2026-10-03 (`ad7b655`), **after** the v6 test results (2026-09-28). Its own chronology note says all v6 results are exploratory. External manifests, freezes and the threshold were committed in the same commit. | Not a clean pre-registration. |
| Post-hoc adaptation after results were seen | v7 → v8 external rescore (`rescore_external_v8.py`, commit `1b41e20`, 2026-10-29) with `re.purge` and a structural entry policy; the SP-2 exclusion; the SP-2 attribute-reference fix (`5cf5211`, 2026-10-25) which post-dates the frozen external variants (2026-10-03). | Post-hoc exploratory. |
| SBG's own docs | `README.md` (~line 500) and `LIMITATIONS.md` §External state the external results were not re-run or verified and are excluded from claims. | Consistent with this classification. |

**Declaration:** BugsInPy, QuixBugs-canonical and QuixBugs-declared are **post-hoc exploratory**, not a-priori independent. Java is not evaluated.

---

## 4. Split leakage

There is no train/test split in the external corpora (SBG is not trained on them), so "split leakage" means (a) dependence between evaluation units and (b) overlap with the SBG development set.

| Check | Result | Tag |
|---|---|---|
| BugsInPy bug-level independence | 51 eligible bugs, but only 44 distinct project\|file\|unit lineages over 55 units. **6 lineages span several bugs**: youtube-dl `js_to_json` (bugs 7, 10, 15, 23, 25, 26, 34), `unified_strdate` (35, 41), `parse_dfxp_time_expr` (6, 27); matplotlib `_make_getset_interval` (24, 26); pandas `validate_baseindexer_support` (18, 22); scrapy `ItemMeta` (8, 34). | EXECUTED |
| Near-duplicate units | 5-gram Jaccard ≥ 0.5 groups the 55 positive units into **44 content clusters** (9 multi-member groups). Pairwise 1.00 (matplotlib 24/26, ansible/2 `_Alpha`/`_Numeric`), 0.92 (spacy/7 `filter_spans` ×2), 0.91 (youtube-dl 23/25). | EXECUTED |
| Role flips across bugs | In 5 cases the fixed unit of one bug is AST-identical to the buggy unit of another (consecutive-commit lineage, e.g. youtube-dl 23/25/26, pandas 18/22, scrapy 8/34, youtube-dl 6/27). The same code appears as the "correct" base in one cluster and the "buggy" variant in another. 16 AST hashes are shared by more than one unit. | EXECUTED |
| Effect on inference | CI changes modestly (§1.3). Bug-level clustering gives 39 clusters vs 32 (lineage) or 33 (content) in the v8-evaluated set. The conclusion (indistinguishable from 0.5) is unchanged. | EXECUTED |
| QuixBugs within-cluster structure | One unit per program: 1 positive plus up to 3 negatives that share the same fixed base. (3 neg, 1 pos) ×32 and (2 neg, 1 pos) ×8 over all 152 pairs. Base-specific properties are shared across labels in a cluster, so within-cluster AUROC is the cleaner statistic (≈ 0.38 all, 0.45 excl. SP-2). | EXECUTED |
| External vs SBG overlap | No near-duplicate text (§3.1). QuixBugs shares textbook algorithms and some function names with SBG base programs. V10 and V9c were not compared. | EXECUTED / NOT-DONE for V10, V9c |
| Coupling through transformers | Negatives are produced by the same SP transformers used to create SBG's training and dev populations. Combined with C1 and C2, this is the "edit-type shortcut". It is a design coupling, not text overlap. | EXECUTED (static) |

---

## 5. QuixBugs-Java

* **READ and EXECUTED inventory (`java_inventory.json`):** `external/quixbugs_java/` has 40 buggy and 40 correct programs and `declared_inputs.json`. A JDI tracer exists (`tracer/SbgJdiTracer.java`, 509 lines), and so does `experiments/final/external_java.py` (1051 lines).
* **No SBG-schema Java result exists:** no `artifacts/final/QUIXBUGS_JAVA_SBG_RESULTS.json`, `pairs_quixbugs_java.jsonl` or `JAVA_CLAIM_REMOVAL.json` (EXECUTED file-existence check).
* The only Java numbers are `results/external/QUIXBUGS_JAVA_EVALUATION_RESULTS.json` (2026-08-30). It is an EEP pilot with ENTER/EXIT markers, a 5-feature formula and τ = 0.08, with 6 of 18 detected (33.3%) vs Python 17 of 28. It is not an SBG-schema measurement (READ).
* `paper/final_empirical_readiness_2026-11-05/agent_5/agent_5_java_readiness.md` (READ): 12 tests pass, 30 of 40 programs are canonical-input eligible, a 3-program smoke run was mechanical only (no AUROC), and no cross-language claim is supported.
* `PHASE2_PREREGISTRATION.md` §6 (READ): Java counts as SBG only if the full schema is produced. Otherwise the Python-to-Java generalisation claim is removed. The Python SBG tracer does not run Java.
* **NOT-DONE:** I did not execute Java (a JDK 21 exists at `/usr/bin/java`). Running the pilot was outside D1's remit and would be a new experiment.
* Classification: **Not evaluated. Not methodologically suitable as evidence of cross-language generality.** If a pilot is ever run, **Exploratory only**.

---

## 6. Per-corpus recommended classification and justification

| Corpus | Classification | Justification |
|---|---|---|
| **BugsInPy** | **Exploratory only.** There is no supported reading as "Valid independent evaluation". | (1) Label incompatibility: 2 of 47 comparable positives are CHANGED under the SBG definition (34 of 47 bases raise on all inputs). (2) Selection: 10.2% eligibility, with heavy bias toward stdlib-only helper functions. (3) Lineage non-independence: 44 lineages for 55 units, and 5 role flips between bugs. (4) 9 broken SP-2 negatives (7 reported by SBG, 2 new) plus 5 repr or harness artefacts. (5) Format shortcut AUROC 0.915. (6) Post-hoc; seen by developers in Aug 2026. (7) 14 of 55 positives not scorable. |
| **QuixBugs-Python canonical** | **Exploratory only.** | SBG label invalid for 80% of positives (8 of 40 CHANGED); canonical LIST battery mismatches the argument types of most programs; format shortcut AUROC 1.000; reversed edit-size beats SBG; headline 0.444 is a post-hoc SP-2-excluded subset (unfiltered 0.384); seen by developers in Aug 2026. |
| **QuixBugs-Python declared** | **Exploratory only.** It would be "Valid with documented adaptation" if (a) the evaluable 28-program subset were pre-specified, (b) the declared inputs were shown independent of SBG development, and (c) the static baselines were reported next to it. None of these holds here. | Task compatibility is good (28 of 31 comparable positives CHANGED), so this is the only regime where positives are observable. But evaluable pairs are 99 of 152 (selected by termination and eligibility), the inputs are the repo's own tests, the AUROC 0.70 [0.58, 0.82] has 24 positives, and reversed static edit-size baselines reach ≈ 0.82–0.90. |
| **QuixBugs-Java** | **Not evaluated; not methodologically suitable as evidence.** | No SBG-schema result; the pilot used a different method. No cross-language evidence exists in the repository. |

These classifications cover dataset compatibility and label reliability only. The overall external-validation verdict and the submission decision are outside D1.

---

## 7. Failures and things I could not or did not do

1. **Java not executed** (§5). Only the inventory and documents were inspected.
2. **D1 did not re-trace SBG.** All SBG AUROCs are arithmetic on stored scores. Reproducing them from raw traces is D2's job.
3. **EXP-A3-011 could not be located** in `SBG/` or `PKG/`, so its 0.17 figure was neither confirmed nor refuted as a stated claim. My own computation gives max identifier-set Jaccard 0.147 (BugsInPy) and 0.444 (QuixBugs).
4. **V10 test and V9c val were intentionally not compared** for independence.
5. **Oracle fidelity**: 1.0 s per-input timeout (V10 used 2.0 s), a single run (no nondeterminism check), Python 3.13 with old upstream code (5 `import_error` files), class-tier observability limited to exception and stdout, and generator returns compared by normalised repr (not consumed). The oracle uses the structural-entry policy (v8-style), not necessarily the exact v7 policy that produced the committed v7 pair sets.
6. **Not-comparable pairs are listed, not dropped:** BugsInPy positives 8 (7 class-tier `unsupported_signature`, 1 `import_error`), negatives 24 (21 + 3); QuixBugs declared positives 9 and negatives 27 (ineligible, not run). Each is a row in `label_oracle_pairs.csv` with its status.
7. **Label-consistent subset** (§2.4) is exploratory and partly circular. It must not be cited as validation.
8. **Format-shortcut score** is my own construct (non-unparse line share). It is label-blind and was computed after seeing the data. It is a diagnostic of benchmark construction, not a model.
9. **Rename-only edit** classification also renames attributes, so `pandas/167` may be a behavioural attribute swap. Not adjudicated by hand.
10. **Statistical caveats:** the cluster bootstrap is percentile, B = 2000, seed 42. No multiplicity correction was applied.
11. **Oracle vs SBG counts**: my comparable BugsInPy positive count (47) differs from SBG's evaluated count (41), because the harness follows the v8 entry policy and handles class-tier units differently. I did not reconcile this per pair.

---

## 8. Reproduction

```bash
cd /Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION
export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1
PY=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python
$PY scripts/d1_01_inventory.py           # static ledgers (no execution)
$PY scripts/d1_02_confounds.py           # AUROCs from stored scores, static confounds (no execution)
$PY scripts/d1_03_label_oracle.py --workers 4   # sandboxed execution of copies (594 child jobs, about 20 s)
$PY scripts/d1_04_label_audit.py         # aggregate oracle: positives / negatives / consistent subset
$PY scripts/d1_05_independence.py        # identifier / shingle Jaccard, name collisions (no execution)
$PY scripts/d1_06_leakage_and_edits.py   # lineage, content clusters, edit kind, format shortcut (no execution)
git -C ../SBG status --short             # must show only the pre-existing untracked entries
```

Order matters: `d1_02` needs `d1_01` outputs, `d1_04` needs `d1_02` and `d1_03`, and `d1_05` and `d1_06` need `d1_01` and `d1_02`. `d1_03` makes sha256-verified copies of SBG units under `raw/WPD-D1_compat/unit_copies/`. It writes nothing under `SBG/`, and the child (`d1_exec_child.py`) runs each program with a temp cwd, rlimits, socket and subprocess stubs, a 1.0 s per-input alarm and a 120 s wall limit. Log: `logs/d1_03_label_oracle.log`.

## 9. Files

`scripts/`: `d1_stats.py` (tie-aware AUROC, cluster bootstrap, within-cluster AUROC), `d1_01_inventory.py`, `d1_02_confounds.py`, `d1_03_label_oracle.py`, `d1_exec_child.py`, `d1_04_label_audit.py`, `d1_05_independence.py`, `d1_06_leakage_and_edits.py`.

`raw/WPD-D1_compat/data/`:
`bugsinpy_bug_ledger.csv`, `bugsinpy_unit_ledger.csv`, `bugsinpy_exclusion_taxonomy.json`, `bugsinpy_pair_ledger.csv`, `quixbugs_program_ledger.csv`, `quixbugs_pair_ledger.csv`, `java_inventory.json`, `inventory_summary.json`, `confound_pairs.csv`, `confound_summary.json`, `label_oracle_pairs.csv`, `label_oracle_file_records.json`, `label_audit_summary.json`, `label_audit_positives.csv`, `label_audit_invalid_negatives.csv`, `label_consistent_subset_summary.json`, `independence_per_program.csv`, `independence_name_collisions.csv`, `independence_summary.json`, `leakage_summary.json`, `bugsinpy_lineage_clusters.csv`, `bugsinpy_positive_edit_kind.csv`, `format_shortcut_pairs.csv`.

Also under `raw/WPD-D1_compat/`: `oracle/` (per-file observation records), `unit_copies/` (sha256-verified program copies), `declared_inputs/` (inputs extracted from `json_testcases`).
