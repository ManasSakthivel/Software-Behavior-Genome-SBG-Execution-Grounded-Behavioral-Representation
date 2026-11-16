# Claim-to-evidence matrix (FINAL SPRINT, Part 2D / 6B)

Every headline claim the manuscript may or may not make. "Frozen" = produced by a pre-registered, frozen evaluation;
"Exploratory" = post-hoc, labelled; "Qualitative" = case study. V10 = 19 held-out programs, same author and generation
procedure as development (**not independently authored**). Source paths are under `artifacts/paper_evidence/` unless stated.

## A. Claims the manuscript may make

| # | Claim | Evidence level | Dataset / version | Metric [95 % CI] | Test | Baseline | Limitations | Source artifact | Manuscript section |
|---|---|---|---|---|---|---|---|---|---|
| A1 | SBG V5 separates behaviour-changing from behaviour-preserving transformations above chance | Frozen | V10 (638 pairs, 19 programs) | AUROC 0.897 [0.863, 0.922] | H1, Holm p = 0.003 | chance | Synthetic; same author/procedure; labels = equivalence on protocol inputs | `V10_INDEPENDENT_EVALUATION.json` | Results |
| A2 | Same, on the validation split | Frozen | V9c-val (432 pairs, 11 programs) | 0.751 [0.706, 0.794] | Holm-supported | chance | as A1 | `V9_VAL_EVALUATION.json` | Results |
| A3 | Adding SBG V5 to edit size improves AUROC | Frozen | V10 | H2: +0.254 [+0.218, +0.285] | Holm p = 0.005 | edit size | as A1 | `V10_INDEPENDENT_EVALUATION.json` | Results |
| A4 | SBG V5 outperforms edit size alone | Frozen | V10 | H3: +0.281 [+0.244, +0.308] (V5 0.897 vs edit 0.616) | Holm p = 0.005 | edit size | as A1 | same | Results |
| A5 | Discrimination persists with edit size exactly matched | Frozen | V10 | stratified AUROC 0.875 (edit 0.500), 8605 comparisons | descriptive (frozen) | edit size | no CI in frozen output; exploratory window sweep 0.87–0.90 | `V10_INDEPENDENT_EVALUATION.json`; `INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json` | Results |
| A6 | An edit-size/label confound existed in the V8 benchmark | Frozen | V8 test | reversed-edit AUROC 0.876 vs SBG 0.694 | pre-declared verdict "not demonstrated" | edit | design artefact, not a code defect | `V8_TEST_EVALUATION.json`, `LABEL_GENERATION_AUDIT.json`, `DIAGNOSTIC_EDIT_SIZE.json` | Motivation / Methods |
| A7 | The composed design removes most of the confound | Frozen | V10 | forward edit AUROC 0.616 [0.606, 0.628] | – | – | not fully removed (CHANGED variant has the larger edit in 92 % of V10 sets, mean +1.9 tokens) | `V10_INDEPENDENT_EVALUATION.json`; `INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json` | Methods |
| A8 | **No statistically established gain from adding SBG to edit size + execution statistics** | Frozen (null) | V10; V9c-val | H4: +0.006 [−0.069, +0.068], Holm p = 1.0; +0.021 [−0.005, +0.048], p = 0.117 | Holm | edit + exec. stats (`M_EX`) | does **not** show equivalence; CI leaves ≲ 0.05–0.07 open | same two JSONs; `INCREMENTAL_CONTRIBUTION_ANALYSIS.md` | Results (prominent) |
| A9 | Execution statistics from the same traces are a strong baseline (0.79 frozen; 0.885 with in-distribution refit on V10) | Frozen / Exploratory | V10 | 0.791 [0.718, 0.851]; LOPO 0.885 [0.850, 0.917] | – | – | LOPO uses same-set programs (never the scored one) | `V10_INDEPENDENT_EVALUATION.json`; `INCREMENTAL_CONTRIBUTION_ANALYSIS_lopo.json` | Results / Discussion |
| A10 | SBG alone vs frozen `M_EX`: nominally better in V10, narrower after refit | Exploratory | V10; V9c-val | +0.106 [0.033, 0.186] (frozen `M_EX`); +0.012 [−0.013, 0.033] (LOPO `M_EX`); V9c-val LOPO +0.094 [0.051, 0.131] | uncorrected | `M_EX` | post hoc | `INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json`, `_lopo.json`; `V10_POSTHOC_SUPPLEMENT.json` | Discussion |
| A11 | V6 is not shown to improve on V5 | Frozen | V10 | H5: +0.0029 [+0.0003, +0.0060], raw p = 0.030, Holm p = 0.090 | Holm (not rejected) | V5 | effect ≈ 0.003 AUROC | `V10_INDEPENDENT_EVALUATION.json` | Results / Limitations |
| A12 | Value-only mutations (SC-6) are invisible to the output-free representation | Frozen + Qualitative | V10 | SBG V5 = 0 on 73.9 % of SC-6 CHANGED pairs (17/23) | descriptive | – | single mutation family; mechanism verified for one case (Case 3) | `V10_INDEPENDENT_EVALUATION.json` (`changed_zero_rate_by_sc_family`); `REPRESENTATION_CASE_STUDIES.md` | Discussion / Limitations |
| A13 | SBG does not transfer to real-bug corpora | Frozen | BugsInPy; QuixBugs | 0.416 / 0.497 (all / excl. SP-2); 0.384 / 0.444 | CIs include 0.5 | – | fixed inputs rarely exercise real bugs (26/41 BugsInPy real-bug pairs score exactly 0) | `EXTERNAL_RESCORE_V8.json`, `REAL_BUG_GENERALISATION_AUDIT.md` | Limitations |
| A14 | Review ordered by SBG reaches a recall target with less of the list than edit order | Exploratory | V10; V9c-val | review fraction for 80 % recall 0.447 vs 0.725 (V10); 0.606 vs 0.717 (V9c-val); paired Δ −0.278 [−0.309, −0.244] (V10) | none | edit; `M_EX` | 50 % prevalence by construction; precision not interpretable | `PRACTICAL_SIGNIFICANCE_ANALYSIS.json`; `PRACTICAL_SIGNIFICANCE_ASSESSMENT.md` | Discussion (as exploratory) |
| A15 | The state-transition component is the strongest single component | Frozen | V9c-val; V10 | 0.762 vs V5 0.751; V10 0.917 [0.893, 0.938] vs 0.897 | descriptive | V3, temporal | no leave-one-component-out ablation; V5 weights unchanged | `V9_VAL_EVALUATION.json`, `V10_INDEPENDENT_EVALUATION.json` | Discussion |
| A16 | The COBOL corpus provided no evaluation | Qualitative / negative | `COBOLSRC` (95 files) | – | – | – | see report | `COBOL_EVALUATION_REPORT.md`, `COBOL_CORPUS_INVENTORY.json` | Future work (one sentence) |

## B. Claims that must not be made

| # | Claim | Why not | Evidence |
|---|---|---|---|
| B1 | SBG is the first / a novel / a unique dynamic approach to behaviour comparison or equivalence | Behaviour sampling (1992), differential testing, DCI (2020), Kessel & Atkinson (2019) exist | `RELATED_WORK_COMPARISON.md` |
| B2 | SBG adds predictive value beyond edit size + execution statistics | H4 null in both datasets; CI includes 0 | A8 |
| B3 | The H4 null proves SBG and execution statistics are redundant/equivalent | CI does not exclude +0.05–0.07 | `INCREMENTAL_CONTRIBUTION_ANALYSIS.md` |
| B4 | SBG alone is better than execution statistics (unqualified) | Reverses to n.s. under in-distribution refit on V10 | A10 |
| B5 | V6 is better than V5 | Holm p = 0.090 | A11 |
| B6 | SBG detects real bugs / regressions | BugsInPy 0.497, QuixBugs 0.444 (excl. SP-2) | A13 |
| B7 | V10 demonstrates generalisation to independently authored software | V10 = same author and generator | `INDEPENDENT_EVALUATION_LIMITATIONS.md` |
| B8 | Equivalence labels are semantic equivalence | They are equivalence on protocol inputs only | `generate_v10_independent.py` (oracle) |
| B9 | SBG improves developer productivity, saves cost, or has realistic precision | not measured; prevalence 50 % by construction | `PRACTICAL_SIGNIFICANCE_ASSESSMENT.md` |
| B10 | SBG works on COBOL / any other language | tracer is Python-only; corpus unusable | `COBOL_EVALUATION_REPORT.md` |
| B11 | SBG is better than output-based differential testing | not tested; SBG is blind to SC-6 by design | A12 |
| B12 | Any "COBOL AUROC", or comparing COBOL with V10 | none exists | – |

## C. Claim audit of existing documents (this sprint)

| Document | Finding | Action |
|---|---|---|
| `FINAL_PREMANUSCRIPT_RELEASE_CHECK.md` (l. 90), `NOVELTY_CLAIM_TO_EVIDENCE.md` (l. 44), `RELATED_WORK_NOVELTY_AUDIT.md` (l. 42) | Kessel & Atkinson DOI **wrong** (…00019 = Harrand et al.; correct …00030) | Dated correction notes added (originals preserved). |
| `NOVELTY_CLAIM_TO_EVIDENCE.md` | EquiBench cited as "NeurIPS 2025 Workshop"; title differs from arXiv record | Correction note added; cite as arXiv:2502.12466. |
| `README.md` | Describes the V6-era state (13-program test split; no V9c/V10 results); not wrong but materially outdated, and silent on the size-aware design | Dated "Update" block added above the generated block; the generated results block (checked by C8) is unchanged. |
| `docs/current/REPRODUCTION.md` | "Expected output" already shows C1–C10 / 10/10 after commit `9bed2f0` | Verified; sprint reproduction commands appended. |
| `FINAL_CLAIMS_AUDIT.md`, `FINAL_IEEE_ACCESS_READINESS.md`, `MANUSCRIPT_CLAIMS_CHECKLIST.md`, `INCREMENTAL_VALUE_AUDIT.md` | Claim boundaries consistent with frozen results (no "first", no real-bug, no V6, no H4 claim) | Historical files kept; sprint addenda added where they are indexed. |
| Searched `*.md/*.yaml` for `first … dynamic`, `novel framework`, `unique approach`, `detects real bugs`, `V6 … better`, `beyond … execution` | Matches in current documents are all *prohibitions*; archive documents are exempt (historical) | none needed |
