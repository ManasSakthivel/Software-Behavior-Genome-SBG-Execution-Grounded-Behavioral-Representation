# Final sprint report — Software Behavior Genome (SBG), IEEE Access preparation

Date: 2026-10-30 · Branch: `remediation/sbg-v4` · Base commit: `9bed2f0` · This sprint is the last planned one.

## Executive verdict

**READY FOR MANUSCRIPT DRAFTING WITH SPECIFIC PRE-SUBMISSION BLOCKERS.**

The strongest defensible paper is an **evaluation-methodology plus empirical-finding paper**: a size-aware,
oracle-validated evaluation of behaviour-change detection that shows a trace-derived representation (SBG) far exceeds
edit size, but is **not shown to add anything to execution statistics computed from the same traces**, and has a
characterised failure profile. It is not an algorithmic-novelty paper and not a bug-detection paper. The blockers are
listed under "Essential before submission" and do not prevent drafting.

## Findings by research weakness

### 1. Incremental contribution beyond baselines

* **Original concern.** Gain beyond edit size + execution statistics not established.
* **Work performed.** Re-derived 42 frozen numbers independently (seed 42, 2000 bootstraps): **42/42 match, 0 discrepancies**
  with the brief. Verified labels, splits (0 program overlap between model-fit and V10), absence of label-derived
  features, fairness of the baseline (same traces). Exploratory analyses A–D plus a two-model leave-one-program-out
  (LOPO) refit.
* **Evidence.** V10 H4 +0.006 [−0.069, +0.068], Holm p = 1.0; V9c-val +0.021 [−0.005, +0.048]. Frozen `M_EX` 0.791 vs
  SBG 0.897, but with an in-distribution refit `M_EX` reaches 0.885 (SBG − LOPO `M_EX` = +0.012 [−0.013, +0.033]); on
  V9c-val SBG keeps +0.094 [0.051, 0.131] over a refit `M_EX`. The v9c-fitted combiner does not transfer (12 programs
  gain, 2 lose > 0.02; gains and losses cancel in matched sets: 11 up, 11 down). SBG is non-zero wherever execution statistics
  are, plus 8 extra CHANGED pairs.
* **Established.** SBG ≫ edit size (H2 +0.254, H3 +0.281; stratified 0.875 vs 0.500).
* **Not established.** Any increment over edit + execution statistics; also not established that none exists
  (CI leaves ≲ 0.05–0.07 open). Status: **not established / unresolved at small effect sizes**.
* **Manuscript can proceed:** Yes, framed around the null.
* **Artifacts.** `INCREMENTAL_CONTRIBUTION_ANALYSIS.md`, `…_main.json`, `…_lopo.json`.

### 2. Novelty

* **Original concern.** Novelty unverified against Kessel & Atkinson (2019) and the dynamic-comparison literature.
* **Work performed.** Verified bibliographic metadata of 13 sources by DOI/arXiv; read DCI abstract + intro and K's
  abstract; built the 10-dimension matrix with explicit depth-of-reading tags; three-level contribution analysis;
  claim audit across current documents.
* **Evidence.** Dynamic behaviour comparison is established (1992 onwards). **Kessel & Atkinson's DOI in three repo
  documents was wrong** (`…00019` is Harrand et al.); correct DOI `10.1109/SCAM.2019.00030`, now annotated (originals
  kept). Full text is closed access: **not read**. EquiBench's title/venue in the earlier audit did not match arXiv.
* **Established.** SBG is not the first dynamic approach; the defensible contributions are Level 2 (evaluation
  design) and Level 3 (empirical finding), Level 1 only modest. Specific novelty paragraph and 5 bullets written.
* **Not established.** Differences from K's full method; novelty relative to the unsurveyed differential-testing,
  regression-selection and change-impact literature (only metadata read for those).
* **Manuscript can proceed:** Yes, with a Level-2/3 framing. **Reading K's full text is essential before submission.**
* **Artifacts.** `RELATED_WORK_COMPARISON.md`, `FINAL_NOVELTY_POSITION.md`, `CLAIM_TO_EVIDENCE_MATRIX.md`.

### 3. Why the representation matters

* **Original concern.** High AUROC without interpretation.
* **Work performed.** Deterministic median-of-pool selection (rules fixed in code before inspection); 10 pairs re-traced
  with the frozen extractor, **10/10 re-scores equal the frozen scores**; source diffs, state-transition diffs, scores, baseline
  comparison for five cases.
* **Evidence.** Case 1 (detection under 26–28-token decoration; `M_EX` wrong because of a negatively weighted
  `call_count`); Case 2 (14-token rename → trace-identical; representativeness caveat: 10 of 72 pool); **Case 3 failure**
  (SC-6 `return not work[target]`: byte-identical trace summaries, SBG = 0; 17/23 SC-6 CHANGED pairs score 0 — output-free
  design blind spot); Cases 4a/4b (adding SBG hurt in 11 sets and helped in 11). State component is the strongest
  single component (V9c-val 0.762; V10 0.917 > V5 0.897).
* **Established.** What the representation captures (control-flow and abstract-state differences) and one verified
  structural blind spot, with the mechanism traced.
* **Not established.** Isolated component contributions (no leave-one-out ablation; deliberately not run); why SP-2
  CHANGED pairs score 0 in 32 % (not investigated).
* **Manuscript can proceed:** Yes. **Artifacts.** `REPRESENTATION_CASE_STUDIES.md`, `REPRESENTATION_CASES_*.json`.

### 4. Practical significance

* **Original concern.** No demonstrated usefulness.
* **Work performed.** Compared five candidate use cases; chose triage of source-transformation impact; exploratory
  review-budget analysis on frozen scores (interpretation limits fixed beforehand: prevalence 50 % by construction;
  ties by expected value).
* **Evidence.** V10: 80 % recall of CHANGED pairs needs 44.7 % of the list under SBG vs 72.5 % under edit size (Δ −0.278
  [−0.309, −0.244]); vs `M_EX` −0.108 [−0.147, −0.054] (recall@25 % difference n.s.); V9c-val 60.6 % vs 71.7 % vs 70.7 %.
  The frozen threshold flags 65.4 % of pairs (sensitivity 0.944, FPR 0.364). A hard ceiling: 18 CHANGED pairs invisible.
* **Established.** On the synthetic benchmarks, SBG-ordered review is more efficient than edit-ordered review.
* **Not established.** Real-world utility, developer benefit, advantage over `M_EX` robustly, advantage over output-based
  differential testing (not run), real-bug detection (contradicted, ≈ 0.4–0.5).
* **Manuscript can proceed:** Yes, with the use case labelled **proposed**. **Artifacts.**
  `PRACTICAL_SIGNIFICANCE_ASSESSMENT.md`, `PRACTICAL_SIGNIFICANCE_ANALYSIS.json`.

## COBOL conclusion

**No defensible evaluation at present; a negative feasibility result.** The path given (`…/COBOLSRC/cobol`) holds **1 file**
(`cosql31.cbl`), not ≈ 70; the sibling directories hold 84 more `.cbl` (84 unique digests overall with the duplicate)
and 10 `.cpy`. All 85 `.cbl` files are IBM Db2 embedded-SQL precompiler snippets: 0/85 compile as-is with GnuCOBOL
3.2.0 (72/85 parse after a behaviour-free `EXEC SQL → CONTINUE` stub, used only to count logic), only 20 have any
non-SQL statement, none has file I/O, tests, fixtures, oracles, variants, licence or provenance, there is no Db2
runtime, and SBG's tracer is Python-only. No labels, pairs, scores or AUROC were produced, and COBOL did not influence
SBG. Place: one sentence in Limitations/Future work.
Artifacts: `COBOL_CORPUS_INVENTORY.md/.json`, `COBOL_EVALUATION_REPORT.md`.

## Remaining blockers

### Essential before submission

1. **Read the full text of Kessel & Atkinson (SCAM 2019, DOI 10.1109/SCAM.2019.00030)** (closed access; use institutional
   access or contact the authors) and fill the "not verified" cells of the comparison matrix. It could reduce the Level-2
   novelty argument.
2. **Read (not just locate) the differential-testing/behavioural-regression papers** (Evans & Savoia; Jin–Orso–Xie; Person
   et al.) before writing the related-work text; method-level claims about them are currently unsupported.
3. **Wording discipline**: H4 null in abstract/results; "held-out, same author/procedure" for V10; no claim of an
   increment over execution statistics, V6 superiority, or real-bug detection (checklist in the blueprint §10).

### Important but not necessarily blocking

* V10 is not independent software; 19 programs; all Python; algorithmic corpus.
* Combiner trained on v9c does not transfer; LOPO shows an in-distribution `M_EX` of 0.885 vs SBG 0.897. State this honestly.
* SP-2/SP-8/SC-6 failure families; no leave-one-component-out ablation; exploratory analyses uncorrected for multiplicity.
* No output-based differential-testing baseline; practical-use case is proposed only.
* EquiBench venue unverified (cite arXiv:2502.12466).

### Optional future research

Independent programs; real refactoring histories with oracle labels; component ablation; output-differential baseline;
a second language with an executable corpus and regression suite (GnuCOBOL's own test suite or NIST COBOL85 tests are
candidate sources, **not inspected**).

## Final claim boundaries

**Strongest supported claims:** see `CLAIM_TO_EVIDENCE_MATRIX.md` A1–A16, in particular: SBG V5 0.897 [0.863, 0.922] vs edit
0.616 on 19 held-out programs; H2 +0.254; 0.875 with matched edit size; **H4 null +0.006 [−0.069, +0.068]**; V6 ≈ V5; SC-6
blind spot; BugsInPy 0.497 / QuixBugs 0.444 (SP-2 excluded).

**Must not appear:** first/novel/unique; gain beyond execution statistics (or null = equivalence); real-bug detection;
independent-software generalisation; V6 superiority; universal semantic equivalence; developer productivity;
COBOL/other-language results; output-differential superiority (matrix B1–B12).

## Reproducibility

| Item | Value |
|---|---|
| Branch | `remediation/sbg-v4` |
| Base commit (start of sprint) | `9bed2f0` |
| Commits made in this sprint | see git log after push (analysis code + JSON: `7039568`; documentation: next commit) |
| Interpreter | CPython 3.13.5 (`../venvs/py313`), `PYTHONHASHSEED=0` |
| Full test suite (**run by me, twice**: before and after the new scripts were added) | `PYTHONHASHSEED=0 python -m pytest sbg/ tests/ -q` → **807 passed, 3 warnings** (340.9 s before; 353.9 s after). The 3 warnings are SyntaxWarnings from benchmark variant files, pre-existing |
| Consistency checks | `experiments/final/consistency_check.py` → **10/10 passed** (run after all documentation edits) |
| Trace verifier | `experiments/final/verify_trace_v4.py` → **35/35 passed** |
| Frozen-hash check | all 18 hashes in `EXPERIMENT_MANIFEST_V4.json` recomputed with SHA-256 → **18 match, 0 mismatch**; `git diff` over `artifacts/final`, frozen evaluation JSON, `sbg/`, `benchmark/`, `extraction.py`, `evaluate_v9/10.py`, `fit_weights.py` empty |
| Sprint commands | in `docs/current/REPRODUCTION.md` (last section) |
| Re-derivation | `sprint_incremental.py main` → 42/42 frozen numbers; `sprint_case_studies.py trace` → 10/10 re-scores = frozen |
| Result artifacts | `artifacts/paper_evidence/*_main.json`, `*_lopo.json`, `REPRESENTATION_CASES_*.json`, `PRACTICAL_SIGNIFICANCE_ANALYSIS.json`, `COBOL_CORPUS_INVENTORY.json` |
| Checked only by earlier agents, **not re-run** | BugsInPy/QuixBugs AUROCs (read from `EXTERNAL_RESCORE_V8.json`, not recomputed); the `make reproduce-*` targets |
| Citation metadata | DOI content negotiation returned HTTP 200 for 12 DOIs; arXiv API for 2502.12466 and 2505.04311; Crossref returned HTTP 429 (rate limit) for part of the checks, so DOI resolution was used instead |
| Untracked, deliberately untouched | four stale `artifacts/final/*_dev_output_free_v8.*` files (pre-existing, not committed) |
| Remote sync (before push) | `HEAD == origin/remediation/sbg-v4 == 9bed2f0` (0 ahead, 0 behind) |
| Deviations from the brief | (i) the COBOL directory held 1 file, not ≈ 70; (ii) BugsInPy/QuixBugs not recomputed; (iii) no leave-one-component-out ablation; (iv) no systematic literature search; (v) the practical-use triage was computed on frozen scores only |

Push outcome is recorded at the end of this file after the push.
