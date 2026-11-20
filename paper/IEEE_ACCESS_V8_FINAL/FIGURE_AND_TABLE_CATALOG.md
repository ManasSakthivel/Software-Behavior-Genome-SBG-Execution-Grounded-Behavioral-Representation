# Figure and table catalog (second-round revision)

This catalog maps every figure, table and algorithm in `main.pdf` (27 pages) to four things: its data source, the script or method that builds it, and its evidence class. It also maps the twelve figures and sixteen tables required by the revision brief to their manuscript numbers. It is linked from `README.md` and `SECOND_ROUND_SCIENTIFIC_REVISION.md`.

**Evidence classes:**
- **R** — raw machine-readable output.
- **D** — derived from R by a script.
- **M** — manuscript calculation or comparison of D.
- **C** — conceptual diagram with no data.
- **L** — literature-reported.

**What changed in this revision.** No figure or table was produced by running an experiment. The data figures re-plot existing JSON. `make_stat_figures.py` was re-run, and it only reads `audit/stats_summary.json`; the regenerated `tables/tab_ablation.tex` is byte-identical to the round-1 file.

**Shared style.** All figures use `scripts/figstyle.py`:
- one serif family (Times), 7–8 pt text;
- a restrained Okabe–Ito palette with fixed semantic roles: blue for SBG/trusted, vermillion for risk/attack, green for pass/verified, orange for baselines, grey for untrusted/excluded;
- vector PDF output with embedded TrueType fonts.

**Build commands.**
```
PY=/path/to/python   # NumPy, Matplotlib
cd paper/IEEE_ACCESS_V8_FINAL/scripts
$PY make_figures.py          # Figs 1-9, 14, 15 (all, or name functions as arguments)
$PY make_stat_figures.py     # Figs 10-13 and tables/tab_ablation.tex
# optional PNG previews: SBG_FIG_PREVIEW=/some/dir $PY make_figures.py
```

## Required figures → manuscript

| Brief # | Required figure | Manuscript | File | Script (function) | Data source | Class |
|---|---|---|---|---|---|---|
| 1 | Problem / motivation | Fig. 1 | `fig_motivation.pdf` | `make_figures.py` (`motivation`) | none (five schematic cases) | C |
| 2 | System architecture | Fig. 2 | `fig_architecture.pdf` | `architecture` | Module names checked against `sbgv8/` | C |
| 3 | Evidence lifecycle | Fig. 3 | `fig_evidence_lifecycle.pdf` | `lifecycle` | Module names checked against `sbgv8/` | C |
| 4 | CEC methodology | Fig. 4 | `fig_cec_method.pdf` | `cec` | Inset is labelled "schematic" (no data) | C |
| 5 | ERS framework | Fig. 5 | `fig_ers_framework.pdf` | `ers_framework` | Property↔perturbation map and criteria from `sbgv8/ers.py` (`TOL`, `_MONO`, `_eval`) | C |
| 6 | Perturbation taxonomy | Fig. 6 | `fig_perturbation_taxonomy.pdf` | `taxonomy` | Post-hoc: `sbgv8/perturb.py`. Execution-level counts (7 / 30 / 1 applicable): `results/v8_mac_perturb/realexec_matrix.json` | C + D |
| 7 | Five-dataset benchmark landscape | Fig. 8 | `fig_evidence_landscape.pdf` | `landscape` | (a) `datasets/v8/dev_records.jsonl` (the script asserts arm totals 150/31/85/46). (c) `audit/five_dataset_summary.json`, drawn hatched grey and marked "excluded" | D |
| 8 | Cross-platform validation | Fig. 14 | `fig_cross_platform.pdf` | `cross_platform` | Status curated from saved outputs on both branches (Table 18) | M |
| 9 | Risk–coverage | Fig. 10 | `fig_risk_coverage.pdf` | `make_stat_figures.py` | `audit/stats_summary.json` | D |
| 10 | Statistical uncertainty | Figs. 11, 12, 13 | `fig_ablation_forest.pdf`, `fig_calibration.pdf`, `fig_power_mde.pdf` | `make_stat_figures.py` | `audit/stats_summary.json` | D |
| 11 | Security / threat model | Fig. 7 (threat model); Fig. 9 (outcomes) | `fig_threat_model.pdf`, `fig_security_outcomes.pdf` | `threat_model`, `security` | `audit/security_outcomes.json` (suite `audit_rerun_head_darwin` and others) | C + D |
| 12 | Evidence-to-claim traceability | Fig. 15 | `fig_traceability.pdf` | `traceability` | Three real chains (B1 risk; P2 109/227; SENSE04b) | C |

## Required tables → manuscript

| Brief # | Required table | Manuscript | Source | Class |
|---|---|---|---|---|
| 1 | Contributions and RQs | Table 1 (`tab:contrib`) | Manuscript synthesis; status per RQ result | M |
| 2 | Notation | Table 4 (`tab:notation`) | Definitions in §III | C |
| 3 | Component responsibilities | Table 5 (`tab:components`) | `sbgv8/{collect,procsep,evidence_schema,adapter,profile,policy,calibrate,stats,ers,perturb,trust}.py` | C |
| 4 | ERS properties | Table 7 (`tab:ersprops`) | `sbgv8/ers.py`. Counts from `results/v8/linux/perturb/posthoc_matrix.md`, mac `b9b8a86c:results/v8_mac_perturb_profilefix2/` and `results/v8_mac_perturb/realexec_matrix.json` | R + D |
| 5 | Perturbations (P1–P9, plus P1b) | Table 8 (`tab:perturb`) | `sbgv8/perturb.py`; applicability from `posthoc_matrix.md` | R |
| 6 | Five-dataset benchmark characteristics | Table 11 (`tab:benchmarks`) | Literature sizes (L). Artifact counts from `audit/five_dataset_summary.json` and `audit/DATASET_VERIFICATION_REPORT.md`. **No per-dataset metric.** | D + L |
| 7 | Cross-platform summary | Table 18 (`tab:xplat`) | Saved outputs on both branches. Supporting checks: md5 of `dev_records.jsonl`; 1e-9 agreement of Linux and mac pre-fix (`210512`) point values, seeds 0–2, both policies (`audit/STATISTICAL_AUDIT_REPORT.md`, finding 5); identical pre-fix ERS matrices (empty `diff` of the two `posthoc_matrix.md` files) | M |
| 8 | Positioning against closest prior work (15 works, 11 columns) | Table 2 (`tab:positioning`) | `LITERATURE_COMPARISON_REGISTER.md` (Supports / Must NOT be cited for) | L |
| 9 | Literature synthesis matrix | Table 3 (`tab:synthesis`) | Same register | L |
| 10 | Experimental design | Table 10 (`tab:design`) | §VII | C |
| 11 | Baseline comparison | Table 13 (`tab:baselines`, definitions); Table 16 (`tab:ablation`, results) | `sbgv8/baselines.py`; `audit/stats_summary.json` | D |
| 12 | Statistical results | Table 17 (`tab:stats`) | `stats_summary.json` → `seed0_recomputed.*.contrasts_own_bootstrap`. The B6 contrast comes from the saved run `results/v8_dev_eval_20261119_055209_linux_soft` (B = 2,000) | D + R |
| 13 | Ablation | Table 16 (`tab:ablation`) | `make_stat_figures.py` ← `stats_summary.json` (byte-identical to round 1) | D |
| 14 | Security threat summary | Table 9 (`tab:threats`); Table 14 (`tab:security`, counts) | `audit/security_outcomes.json`, `audit/security_rerun_darwin.json` | R + D |
| 15 | Artifact mapping | Table 20 (`tab:artifacts`) | Repository paths, checked to exist | M |
| 16 | Threats to validity | Table 19 (`tab:threatsval`) | §X | C |

**Additional tables:**
- Table 6: evidence profile (`sbgv8/profile.py`).
- Table 12: development corpus (`dev_records.jsonl`).
- Table 15: ERS property matrix (raw matrix files).

## Algorithms

| # | Algorithm | Implements (checked against the code in this revision) |
|---|---|---|
| 1 | Evidence acquisition and sealing | `sbgv8/collect.py:run_capture` |
| 2 | Integrity validation | `sbgv8/evidence_schema.py:validate_dir`; `procsep.validate_isolated`; `adapter.load_record` |
| 3 | CEC fit and threshold | `sbgv8/calibrate.py:fit_select`; `sbgv8/stats.py:select_threshold` |
| 4 | Verdict generation | `sbgv8/calibrate.py:Model.decide` |
| 5 | ERS evaluation of one trial | `sbgv8/ers.py:compute_ers`, `_eval` |
| 6 | Matched-coverage risk | `sbgv8/stats.py:matched_risk` |

## Superseded items

- `fig_pipeline.pdf` and `scripts/make_diagrams.py` were superseded by Figs. 2, 3 and 6 (`make_figures.py`). Both remain in commit `df612db0`.
- The round-1 capability table and method-comparison table were replaced by Tables 2 and 3.
- The round-1 benchmark table was replaced by Table 11.
