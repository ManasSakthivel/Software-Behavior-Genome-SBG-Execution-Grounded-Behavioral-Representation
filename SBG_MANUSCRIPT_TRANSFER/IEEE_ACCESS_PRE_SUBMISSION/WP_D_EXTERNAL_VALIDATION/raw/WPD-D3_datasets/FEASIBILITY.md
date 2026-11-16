# WPD-D3 — Additional independent-source program-change dataset investigation (FEASIBILITY ONLY)

Subagent: D3 (WP-D external validation). Date of probes: 2026-11-14.
Scope: feasibility analysis plus lightweight offline probes. **No SBG model, trace feature, distance, threshold or score was computed. V10-test and V9c-val were not touched. The SBG repository was read only.**
Companion files: `candidates.csv` (24 rows, 17 columns), `PROBE_LOG.md` (every executed probe, environment, limitations), `probes/` (scripts + raw outputs + `P99_sha256_manifest.txt`).

Terminology used throughout
* **FEASIBILITY ANALYSIS** = something I read (README, paper abstract, repo metadata, prior in-repo report).
* **EXECUTED PROBE** = something I ran (static `ast` counts, or running dataset programs under SBG's frozen entry-selection rule and 11-input battery to record *outcome signatures only*). All logged in `PROBE_LOG.md`.
* **UNVERIFIED** = I could not confirm the property from a primary source.

---

## 1. Verdict

1. **No candidate qualifies as "Valid independent evaluation"** of SBG's task (single-file stdlib Python pair → CHANGED/EQUIVALENT on 11 synthesised inputs, with EQUIVALENT negatives that are independent of SBG's own transformers).
2. **One candidate is "Valid with documented adaptation": SeqCoBench** (MBPP-derived; different authors/implementation of semantics-preserving and semantics-changing transforms). Its claim ceiling is **independent-generator replication on synthetic edits**, not real-bug validity. Reasons it is not "valid independent": transformation families overlap SBG's SP/SC families, and a trivial static shortcut (token-bag, label only) already reaches AUROC ≈ 0.82 inside the small-edit stratum.
3. **Real-bug external validation beyond BugsInPy/QuixBugs: none feasible offline within ≤ 2 h.** Every real-bug Python source I assessed fails on at least one of: no SBG-compatible EQUIVALENT negatives, project-internal/third-party imports, I/O or class APIs, non-Python language, or label non-observability on SBG's battery.
4. Negative / cautionary findings are recorded as results, not hidden: HumanEvalFix has only 52.4 % battery-observable bugs and a minifier-negative design is edit-size confounded (reversed edit-size AUROC 0.765); Refactory's "correct" label is not reproduced by the battery (26.5 % of "correct" programs differ from the reference); EquiBench OJ is not executable under SBG's harness.

---

## 2. Method

| Layer | What | Where |
|---|---|---|
| Read (feasibility analysis) | Dataset READMEs, licence/size metadata (GitHub/HF/PyPI APIs), arXiv abstracts, prior in-repo assessments | `probes/P01_*`, `P02*`, `PROBE_LOG.md` |
| Static probes | `ast`-level eligibility under SBG's frozen entry rule; edit-size; stdin-use; stdlib scans; SBG-corpus exact-function overlap | P04, P08, P11, P12, P15 |
| Dynamic probes (dataset code only) | Each program run in a sandboxed subprocess on SBG's own `select_entry_output_free` + `synthesise_inputs` battery; **outcome signature only** (return repr[:300], exception type, stdout[:200], post-call argument repr[:300]) | P05, P07b, P10, P16 |
| Analysis | Observability, label reliability, stratum yields, label-only static shortcut AUROCs | P06, P09, P13, P14, P16 |

I deliberately did **not** import or call SBG's trace extractor, feature builder, V5/V10 scorer, or any model/threshold files.

---

## 3. SBG task requirements that drive compatibility (read from `SBG/experiments/final/protocol.py`, `extraction.py`, PROTOCOL.md §2)

* Unit = a pair (A, B) of single-file pure-stdlib Python programs; label **1 = CHANGED** (behaviour differs on the battery), **0 = EQUIVALENT**.
* Inputs = fixed per-family battery (list, str, int, float, bool, dict; 11 values each). **Unannotated parameters default to the list-of-ints battery**; multiple parameters are zipped into tuples and the entry is called `fn(*tuple)`. Unsupported annotations ⇒ ineligible.
* Entry auto-selected: priority names → annotated function → alphabetically first.
* The label is therefore *"differs on these 11 inputs"*, not general semantic equivalence. A bug only counts as CHANGED if the battery can observe it; an SP-style negative is only a valid EQUIVALENT if outcomes are equal on the same battery.
* SBG's own SP transformers (sp1–sp12: variable/function rename, dead code, comment strip, loop/condition rewrite, inline/extract function, constant fold, format normalise, equivalent data structure, algebraic rewrite) make the in-repo negatives. **Any dataset whose negatives come from these is not independent on the negative side.**
* **Polarity**: SeqCoBench's label 1 = *preserved*; SBG's 1 = *changed*. Must be inverted (`1 − label`).

---

## 4. Offline / network inventory (executed checks)

* Network: github.com, pypi.org, huggingface.co all HTTP 200 (`curl --max-time 8`).
* Offline datasets on this machine: only `SBG/external/{bugsinpy,quixbugs,quixbugs_java}`. No HumanEval/MBPP/CodeNet/Defects4J copies, no mutation tools (`mutmut`, `cosmic-ray`, `MutPy` absent from `venvs/py313`, `venvs/py39`, system 3.9, Homebrew 3.11/3.14).
* pip cache, HF cache (`microsoft/codebert-base` only): irrelevant.
* Local Homebrew CPython 3.11/3.14 ship stdlib `Lib/test` (static material only; no git history).
* New downloads: ≈ 19.5 MB data + pip wheels for the D3-private venv (`probes/_venv_tools`: python-minifier 3.4.0, libcst 1.9.0). Not downloaded (size, no feasibility value beyond proxies): CodeContests 7.6 GB, CodeNet 7.8 GB, APPS 1.4 GB, CPython repo 0.9 GB, Defects4J ≈ 150 MB.
* Consequence: "offline ≤ 2 h" for anything beyond the already-downloaded SeqCoBench / HumanEvalPack / Refactory / EquiBench files is **not met** unless a download is accepted.

---

## 5. Classification summary (full 17-column rows in `candidates.csv`)

| Classification | Datasets |
|---|---|
| Valid independent evaluation | **none** |
| Valid with documented adaptation | **SeqCoBench** (as independent-generator replication) |
| Exploratory only | BugsInPy and QuixBugs (provisional; D1/D2 own the final call); PyPIBugs; HumanEvalFix / HumanEvalPack-Python; EvalPlus canonical-vs-canonical EQ candidates; Refactory student programs; CPython stdlib git history; stdlib + independent mutation tool (cosmic-ray / mutmut / mutatest / MutPy); DebugBench and CanItEdit (provisional, not inspected) |
| Not methodologically suitable | Defects4J, ManySStuBs4J, GitBug-Java, Codeflaws, BugSwarm, Project CodeNet, CodeContests/Codeforces, EquiBench OJ, CodeXGLUE (Devign/BigCloneBench/POJ-104), refactoring oracles, CrossCodeEval-style benchmarks, MBPP standalone, TypeBugs/Defects4Py (UNVERIFIED → treat as unavailable) |

Dominant blockers per group: non-Python language (Defects4J, ManySStuBs4J, GitBug-Java, Codeflaws, CodeXGLUE, refactoring oracles); stdin/stdout scripts without entry functions (CodeNet, CodeContests, EquiBench OJ); repo-scale builds / project imports (BugSwarm, BugsInPy, PyPIBugs, CPython history); class-based / unannotated API vs fixed battery (DebugBench, Refactory, MBPP-derived); no pair structure (MBPP, CrossCodeEval).

Note on provenance: some GitHub names I guessed returned 404 (ManySStuBs4J/ManySStuBs4J, TypeBugs/TypeBugs, ExpertiseModel/Defects4Py, Jungfrau-ai/debugbench, Spirals-Team/defects4j-dissection, cqse/refactoring-oracle, tdurieux/RefactoringMiner). This means *my guessed URL failed*, **not** that the datasets do not exist — those properties are UNVERIFIED. Rows whose classification rests on type-of-dataset judgement rather than a probe are labelled so in `candidates.csv` (`evidence` column).

---

## 6. Key quantitative findings (all EXECUTED probes unless stated)

### 6.1 HumanEvalPack-Python / HumanEvalFix (164 tasks, MIT; human-written bugs) — P04, P05, P06
* 164/164 pass SBG's static eligibility; selected entry equals the target function in 163/164 (Python/10 is the exception).
* Battery observability of the injected bug: **86/164 (52.4 %)** differ on the 11 inputs.
* **47/164 canonical solutions raise on all 11 inputs** (the battery supplies ints for `List[...]`-style parameters in several tasks), so those pairs carry no behavioural signal for an output-free tracer.
* Only positives (bugs) are natural; no independent EQUIVALENT negatives exist in the dataset.

### 6.2 HumanEvalPack + python-minifier negatives (independent tool, annotations preserved) — P07, P07b, P11
* 164/164 minified variants are battery-outcome-equal to canonical (valid EQUIVALENT by SBG's own label definition).
* 136/164 have a changed AST; **28/164 are AST-identical** (trivial negatives).
* **Edit-size confound**: CHANGED median edit = 2, EQUIVALENT (minifier) median = 8; label-from-edit-size reversed AUROC = **0.765**. Only 46/164 EQ pairs have e ≤ 2, and these include the 28 AST-identical ones. Any score correlated with edit size would look like signal.
* Verdict: exploratory only; cannot support an independent-evaluation claim without edit-size matching, and matching leaves ~18 non-trivial negatives.

### 6.3 Refactory (2,442 correct + 1,783 buggy student programs, 5 assignments, LGPL-3.0) — P04, P05, P09
* Under SBG's battery only Q3 (`remove_extras`, list of ints) is natural. For Q3: wrong programs differ from reference 308/308; correct programs differ 37/546.
* Reference programs for Q1, Q2, Q4, Q5 raise TypeError on 10, 10, 8, 11 of 11 inputs (unannotated multi-parameter functions get the list battery for every parameter).
* "Correct" programs differ from the reference in 648/2,442 (**26.5 %**) ⇒ dataset's EQUIVALENT label is **not reproduced** by SBG's label definition without per-assignment declared inputs (a protocol adaptation that would have to be frozen first).
* Only **5 independence clusters** (assignments) ⇒ statistics underpowered at the cluster level.
* `fail/` folder (163 files, all parse) is undocumented in what I read; semantics UNVERIFIED; **not run** (see §11).

### 6.4 EquiBench OJ_A / OJ_V / OJ_VA (400 pairs each, Apache-2.0; arXiv 2502.12466) — P12
* 389–395 of 400 pairs involve a stdin-reading program. Pairs with both programs eligible and no stdin: 2, 4, 2. None free of module-level executable statements. **Not suitable** under SBG's harness.

### 6.5 CPython 3.11 stdlib static scan — P08
* 150 public modules, 968 public top-level functions; only 167 self-contained; **0 fully annotated**; 50 are `operator` wrappers. Supports "exploratory only" for stdlib mutation: population is tiny, unannotated (list-of-ints battery mostly mismatched), and mutation tools are not installed.

### 6.6 SeqCoBench (`nickil/seqcobench`; Maveli, Vergari, Cohen, arXiv 2408.11081; 7.1 MB CSVs) — P02b, P10, P13, P14, P15, P16
Structure (from the CSVs): 14,572 rows; 1,134 unique originals (565 / 229 / 341 by train/valid/test; 1 original shared between valid and test); 972 `groups` of which 84 are shared between valid and test (meaning of `groups` UNVERIFIED). **Licence not stated in what I read ⇒ UNVERIFIED.**

Battery classes over all rows (SBG polarity applied; label = SeqCoBench's label inverted):

| Class | Rows |
|---|---|
| SP_ok (preserved and battery-equal) | 2,449 |
| SP_but_differs (preserved by label, differs on battery) | 13 (0.53 % noise) |
| CH_ok (changed, differs on battery) | 629 |
| CH_unobservable (changed by label, battery-equal) | 391 (**38.3 %** of CH rows) |
| orig_all_exc (original raises on all 11 inputs) | 4,512 (31 % of rows) |
| entry_differs (all 5 dissimilar-injection variants, 1,130 each) | 5,650 |
| ast_identical | 588 |
| var_import_fail | 290 |
| orig_no_entry | 50 |

Yields: usable rows 3,078 (2,449 SP + 629 CH). **e ≤ 2 stratum: 735 SP + 629 CH from 486 programs; 260 programs have both classes (test 85, valid 54, train 121).** e ≤ 2 composition: SP = operand_swap 257, dead_code 243, rename×3 ≈ 77 each, for_while 3; CH = single-token operator / constant flips.

**Static shortcut (label-only, no SBG)**: pooled reversed token-bag AUROC = **0.947**; within e ≤ 2, token-bag AUROC 0.176 ⇒ reversed **0.824** (CI ≈ 0.80–0.85); pooled edit-size AUROC 0.150 (reversed 0.85); AST-bag ≈ 0.65 pooled, ≈ 0.56 within e ≤ 2. A score has to beat these to be evidence of behavioural signal.

Independence: different authors and implementation, but the transformation families (rename, dead code, operand swap, for↔while; operator/constant flips) overlap SBG's SP/SC families ⇒ "independent-generator replication", **not** independent real-bug validation.

Leakage/overlap: 1 original shared valid↔test, 84 `groups` shared valid↔test (so splits are not program-disjoint at the `groups` level, whatever `groups` means); P15 exact-function AST match against 14,257 SBG `.py` files found 2 trivial matches among SeqCoBench originals (an `Average`/mean function and a gcd), 1 for HumanEvalPack (gcd), 0 for Refactory references.

---

## 7. Cross-cutting issues

1. **Polarity**: SeqCoBench 1 = preserved ⇒ invert for SBG; sign errors would flip AUROC to 1 − AUROC.
2. **Label ≠ semantics**: SBG's label is battery observability. 38.3 % of SeqCoBench "changed" rows and 47.6 % (78/164 = 164 − 86; P06) of HumanEvalFix bugs are not observable on the battery. Unobservable rows must be reported as a logged stratum, not silently dropped and not silently kept as CHANGED.
3. **Degenerate originals**: 31 % of SeqCoBench rows have an original that raises on all 11 inputs (list-of-ints battery vs unannotated MBPP functions); 47/164 HEP canonicals likewise. This is a harness-vs-dataset mismatch that biases the usable population toward list-friendly functions.
4. **Static shortcut / edit-size confound**: both SeqCoBench (0.82 in e ≤ 2) and HEP + minifier (0.765) have label-predictive static signals. A non-baseline-controlled AUROC is not evidence.
5. **Cluster counts**: Refactory 5; SeqCoBench 1,134 originals (486 in e ≤ 2, 260 with both classes); HEP 164 tasks; BugsInPy 51 bugs/55 units; QuixBugs 40. Cluster = original program, not row.
6. **Independence taxonomy** (three separate axes): *source independence* (who wrote the programs), *implementation independence* (who wrote the transformer), *transformation-class independence* (same family of edits?). SeqCoBench: source and implementation independent, transformation class **not**. HEP + minifier: source independent, transformer independent, but different edit-size regime. BugsInPy/QuixBugs positives: source independent; negatives are SBG-made ⇒ implementation **not** independent on the negative side (owned by D1/D2).
7. **Determinism**: probes ran each program once; a frozen experiment must re-run and drop non-deterministic programs (logged).

---

## 8. Re-verification of prior in-repo claims (D3 oracle vs prior reports)

Sources: `SBG/reports/sprint2/08_EXTERNAL_POPULATION_FEASIBILITY_CANDIDATE_ASSESSMENT.md`, `SBG/paper/final_empirical_readiness_2026-11-05/agent_3/agent_3_external_validation_decision.md`.

| Item | Prior claim | D3 probe (P16) | Status |
|---|---|---|---|
| SeqCoBench zero-exception originals | 332 | **329** (train 163 / valid 70 / test 96) | close, not identical |
| e = 2, all splits | 188 programs, 400 SP + 460 SA pairs | 184 programs with both classes, 393 SP + 451 CH pairs | close, not identical |
| e = 2, test split | 60 programs, 259 pairs | 59 programs, 114 SP + 138 CH pairs | close; pair count definitions differ |
| SeqCoBench identified as only viable candidate | yes | consistent (only candidate that survives) | consistent |
| HumanEvalPack rejected for edit-size confound | yes (EQ = EvalPlus-vs-OpenAI canonical) | direction reproduced with minifier negatives (reversed edit-size AUROC 0.765) | consistent (different EQ source) |
| EquiBench OJ rejected for harness incompatibility | yes | reproduced: 2/4/2 usable pairs of 400 | consistent |
| EquiBench provenance "Brakel et al." | stated | README shows `Anjiang-Wei/EquiBench`, arXiv 2502.12466; authors UNVERIFIED | prior attribution looks wrong; do not repeat |
| BugsInPy / QuixBugs AUROC 0.4099 / 0.3877 (v8 rescore) | quoted | not tested by D3 (D1/D2 own); differ from task-quoted 0.497 / 0.444 | flagged for orchestrator |

Probable causes of small P16 differences: single-run oracle, exception-type-only comparison, exact exclusion rules. The prior numbers are therefore **plausible but not exactly reproduced**; they must not be reused in a manuscript without being regenerated by a frozen script.

---

## 9. Ranked recommendation

Rank 1 — **WPD-X1: SeqCoBench independent-generator replication** (Valid with documented adaptation). Executable offline ≤ 2 h: data already downloaded (7.1 MB), battery oracle already run, extraction estimate ≈ 1,700 programs at ≈ 0.1 s each ⇒ ≈ 10–30 min on 4 cores (grounded in `PKG/logs/EXP-ORCH-001_v10.log` per-program times) plus ≈ 30–60 min for pre-registration freeze, bootstrap and write-up.
Rank 2 — HumanEvalFix: exploratory, positives or edit-size-confounded negatives only.
Rank 3 — Refactory with declared per-assignment inputs: exploratory, 5 clusters.
Rank 4 — stdlib + cosmic-ray mutation: exploratory; requires install and extraction work, population tiny/unannotated.
Real-bug external validation beyond BugsInPy/QuixBugs: **none feasible offline in ≤ 2 h.**

### Pre-registration sketch — WPD-X1

*Not executed. To be frozen (config + script sha256) before any SBG extraction.*

| Item | Specification |
|---|---|
| Hypothesis | Frozen SBG V5 score discriminates CHANGED from EQUIVALENT pairs in an independently generated MBPP-derived benchmark above chance **and above static baselines**. |
| Population | Pool `seqcobench_{train,valid,test}.csv` (record sha256). Frozen rules: same selected entry in A and B; original non-degenerate (not raising on all 11 inputs); AST differs; dissimilar-injection rows excluded by the same-entry rule; SBG-corpus exact-function overlap excluded (the 2 trivial matches); programs that are non-deterministic across two oracle runs excluded and logged. **Primary stratum: e ≤ 2** (feasibility yield 735 SP + 629 CH from 486 programs, 260 with both classes). **Secondary:** all validated pairs, edit-size stratified. |
| Label source | SBG label = 1 − SeqCoBench label, **validated by battery differential execution**. SP rows that differ (13) and CH rows that are unobservable (391) go to separate **logged strata**, reported, not silently dropped. |
| Independence from SBG transformers | SeqCoBench's own generator (different authors). Overlap in transformation families **declared** as a limitation, not hidden. |
| EQUIVALENT negatives | SeqCoBench SP rows, validated by battery equality (observed noise 0.53 %). |
| Scoring | Frozen SBG V5 (0.5/0.25/0.25) with τ* from V9c-train; no tuning; scored once; config and script sha256 frozen before extraction. **Scoring is a later step by the authorised session, not part of D3.** |
| Primary metric | AUROC on the e ≤ 2 stratum. |
| Clustering unit | Original MBPP program (`orig_hash`); cluster bootstrap B = 2000, seed 42; one-sided within-program permutation (PROTOCOL §4 `eval_lib`). `groups` = sensitivity only (84 groups shared valid↔test). |
| Baselines | Token-bag (forward and reversed), edit size, AST bag, `static_token`, `static_ast`, exec-statistics; paired ΔAUROC with Holm correction. Static label-only shortcut reaches ≈ 0.82 in e ≤ 2, so SBG must exceed it. |
| Exclusions | Every exclusion logged with reason and count (degenerate original, no entry, entry differs, AST identical, import fail, non-deterministic, overlap). |
| **Failure criteria** | **F1**: lower 95 % cluster-bootstrap CI of AUROC ≤ 0.5 ⇒ no external replication. **F2**: SBG does not exceed the best static baseline (paired ΔAUROC CI includes 0) ⇒ no incremental evidence even if AUROC is high. Either failure is reported as a negative result. |
| Required caveats | Synthetic edits; generator-family overlap with SBG's SP/SC; no real bugs; licence unstated (UNVERIFIED); 38 % CH unobservable; harness mismatch drops ≈ 31 % of originals; selection by observability restricts to list-friendly functions. |
| Claim ceiling | "Independent-generator synthetic replication." Not "external validation on real bugs". |

---

## 10. What this report does **not** establish

* Nothing about SBG's performance on any dataset. All AUROCs above are label-only static baselines or observability counts.
* No claim that BugsInPy 0.497 / QuixBugs 0.444 are reproduced or not (D1/D2).
* No final IEEE Access submission decision.

---

## 11. Failed / not done / UNVERIFIED / continuation

**Not done or failed (preserved):**
* Refactory `fail/` folder (163 files, all parse): purpose undocumented in what I read, semantics UNVERIFIED, **not executed**; the first P05 launch was killed after HEP finished (the HEP output was kept) and relaunched for Refactory only; `fail/` was not included.
* Guessed GitHub URLs returning 404 (list in §5) — UNVERIFIED rather than disproven.
* DebugBench, CanItEdit, CrossCodeEval-style: classified by type / abstract; not downloaded or inspected.
* PyPIBugs: not downloaded; "10 % eligible" is an analogy to BugsInPy, not measured.
* Class-based tier of `output_free_v7` (class fallback) not exercised.
* Large datasets (CodeContests, CodeNet, APPS, CPython repo, Defects4J) not downloaded — justified in §4.

**UNVERIFIED:** SeqCoBench licence; meaning of `groups`; EquiBench authors; TypeBugs/Defects4Py existence/URL; Refactory `fail/` semantics; MutPy licence (GitHub metadata says NOASSERTION).

**Housekeeping flag:** `SBG/.pytest_cache/v/cache/{nodeids,lastfailed}` have a modification time later than 18:00 today. D3 never ran pytest in SBG; probably another session. Recorded in `PROBE_LOG.md` for the orchestrator.

**Continuation (all from the `raw/WPD-D3_datasets/` directory; Python 3.13.5):**
```bash
export PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1
PY=/Users/manassakthivel/Desktop/SBG-FINALREVIEW/venvs/py313/bin/python
$PY -W ignore probes/P10_seqco_prepare.py      # static split/leakage audit
$PY -W ignore probes/P10_seqco_run.py          # battery outcomes (≈3 min)
$PY -W ignore probes/P13_analyze_seqco.py      # observability / strata
$PY -W ignore probes/P14_seqco_static_shortcut.py
$PY -W ignore probes/P16_seqco_prior_crosscheck.py
(cd probes && shasum -a 256 -c P99_sha256_manifest.txt)
```
Probe scripts read downloaded data from `data/` (re-fetch commands: P03 and the `curl` lines in `PROBE_LOG.md`). P05/P07 require the `probes/_venv_tools` venv only for the minifier step.
