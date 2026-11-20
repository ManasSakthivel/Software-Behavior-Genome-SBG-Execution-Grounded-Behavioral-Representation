# Final manuscript changelog

Date: 2026-11-20. Authoritative working copy: `closeout/manuscript_final/`. Baseline: `closeout/manuscript_original/` (copy of `~/Desktop/SBG-V8-LINUX/paper/IEEE_ACCESS_V8_FINAL/` with its 61 pre-existing uncommitted changes, which were not touched). The SBG repository was not modified: HEAD `df612db0`, same 61 entries in `git status`.

**Not adopted:** `closeout/FINAL_MANUSCRIPT/` is a separate copy created by a later agent. It sets the +1.6 pp interval to [−6.4, +16.3] (the stored value and its rerun give [−6.6, +16.3]) and removes the verified B1 interval [0.086, 0.354]. Its changes are unverified and were not used. `FINAL_MANUSCRIPT_CHANGES.diff` records them.

**Not done:** LaTeX build. No TeX toolchain is installed (`pdflatex`, `latexmk`, `bibtex` absent). `main.pdf` is renamed `main.STALE_pre_edit.pdf` and must not be treated as the current build.

## Decision 1: held-out / test-split disclosure

Evidence: `artifacts/paper_evidence/V8_TEST_EVALUATION.json` (HEAD; single run; split `test`; 956 valid pairs; 22 programs; `sbg_v5` AUROC 0.693742, CI 0.659291–0.726558; `edit_size_reversed` 0.875922, CI 0.858786–0.891749; `learned_m1` 0.750844; `learned_m2` 0.771289; delta −0.182181, CI −0.219937 to −0.14396; Holm p 0.006; stratified 0.776207, CI 0.722233–0.824978; noise floor p95 0.528435; verdict NOT DEMONSTRATED).

| File | Change |
|---|---|
| sections/abstract.tex | "no held-out benchmark was evaluated" → single-run test-split result (0.694 vs 0.876; NOT DEMONSTRATED) and statement that no independent confirmatory held-out evaluation was established. |
| sections/introduction.tex | "no benchmark was held out" → same disclosure, cross-referenced to RQ5. |
| sections/design.tex | "No benchmark was evaluated as held-out data" → single-run disclosure. |
| sections/results.tex | RQ5 sentence qualified. New paragraph "Single-run test-split evaluation" with the numbers above, the 4-program pre-scoring exclusion, shared generator design, and the post hoc component comparison marked exploratory. |
| sections/threats.tex | Table row: "no held-out benchmark" → "single-run v8 test split only (not independent; NOT DEMONSTRATED); no confirmatory held-out benchmark". |
| sections/conclusion.tex | "no benchmark was held out" → single-run result and absence of a confirmatory held-out evaluation. |

Not used: τ = 0.040511 from the test record (a different threshold from the frozen τ* = 0.072905 in `THRESHOLD_FROZEN.json`; unresolved, omitted). The status label "CONFIRMATORY-BY-FREEZE" is not used.

## Decision 2: statistical intervals (verified, retained)

Source at HEAD: `paper/IEEE_ACCESS_V8_FINAL/scripts/stats_recompute.py` and `audit/stats_summary.json`. A clean export of HEAD, rerun with `--refit --B 10000` under numpy 2.5.5 and scipy 1.18.1, reproduces the non-timing fields. B1 = [0.0856, 0.3535] (manuscript [0.086, 0.354]); B7−B8 = 0.01639, interval [−0.0658, +0.1625] (manuscript [−6.6, +16.3]); B8 = 0.2131, [0.1238, 0.3918] (manuscript [0.124, 0.392]). Detail: `closeout/STATS_RECOVERY_REPORT.md`; log `closeout/recovered_stats/stats_rerun_log.txt`. Exploratory on development data; not independent validation.

| File | Change |
|---|---|
| sections/conclusion.tex | Removed "sign unstable" next to the +1.6 pp interval; the source for it was not verified. Interval retained. |

## Decision 3: macOS security counts (verified, retained; citation corrected)

Source: `audit/security_rerun_darwin.json` (tracked; first added in `df612db0`), from `scripts/audit_security_rerun.py`. Counts: blocked 3, detected 15, no effect 5, succeeded 2; total 25 after excluding H00 and SENSE07. Re-execution in a scratch copy matched the original (excluding timestamp and duration). Detail: `closeout/SECURITY_RECOVERY_REPORT.md`.

| File | Change |
|---|---|
| sections/reproducibility.tex (security row) | Commit citation `07ecd5b7` → "file added at `df612db0`; re-run at `07ecd5b7` (same sbgv8 tree)". |

## Unverified claims qualified or removed (this pass)

| File | Change |
|---|---|
| sections/conclusion.tex | Removed "The statistical analysis reproduced across macOS and Linux to $10^{-9}$ on identical records." Not re-run in this pass. |
| sections/results.tex, Reproducible analysis paragraph | "agree to $10^{-9}$" → "are reported to agree to $10^{-9}' … (reported by the project; not re-run in this review pass)". |
| sections/results.tex, platform table row | "Agree to $10^{-9}$" → "Reported; not re-run". |

## Superseded or wrong reports (kept, marked)

- `closeout/INTERVAL_RECOVERY_REPORT.md`: superseded notice added; its claim that the stats script was absent from all refs is wrong.
- `closeout/FINAL_EVIDENCE_CLAIM_REGISTER.md`: correction block §F appended; rows C03, C06, C20, C25 and §D are superseded there.

## Still unchecked in the manuscript

- `reproducibility.tex` lines 18, 25, 27 cite `07ecd5b7` as the code commit for the stats script, five-dataset audit and test suite. Introducing commits not verified.
- Figure `fig_evidence_landscape.pdf` not regenerated; caption corrected only.
- Frozen-threshold held-out study (`design.tex:133`), ERS posthoc matrix, real-execution analogue (30 pairs), Linux probe counts and the 608-test Linux run remain OPEN in the register and are not verified.

## Final pass (2026-11-20): references, claims, thresholds, availability, figure, compilation

Edits are in `closeout/manuscript_final/` only. The SBG repository is unchanged (HEAD `df612db0`).

### References
- Audit: `references.bib` had 76 entries. The literature register (`LITERATURE_COMPARISON_REGISTER.md`) verified 72 rows. Six cited entries had no verification row, and they were removed: `androutsopoulos2014analysis`, `jahangirova2016oracle`, `kachroo2026feagent`, `masri2014prevalence`, `voas1992pie`, `wei2025equibench`.
- Dependent text removed: two sentences in `sections/background.tex` (S1 EquiBench and FEAgent; S3 oracle assessment), one S5 sentence on PIE and failed propagation, and the S5 claim that coincidental correctness is common (its only citation was removed). Four table rows (EquiBench, FEAgent, oracle assessment, PIE) removed.
- Kept with a flag: `lin2017quixbugs` (QuixBugs), the benchmark the experiments use. It has no register row. Verify before submission.
- Kept: arXiv preprints verified as AX in the register, including `durieux2019critical`, whose bib entry is an honest arXiv preprint with no DOI.
- Result: `references.bib` has 70 entries, all cited; 69 have register rows.

### Claims qualified or verified
- B4 (141 verdicts, 0.121) and B5 (144, 0.125): counts, risks and CIs match the stored summary. Kept as VERIFIED (stored value).
- Real-execution analogue (720 rows, 30 pairs): the matrix exists on both branches; run directories are absent. The corroboration wording in the abstract, introduction, conclusion and results is changed to "observed in an exploratory real-execution matrix (run directories absent)".
- ERS matrix: present in the repository; values not recomputed in this pass. Kept with that qualification.
- Linux probe counts (51/74; 65 INS): pre-fix run, no host metadata. Kept only as pre-fix report figures.
- 608-test Linux run: report text only; not used in results.
- Cross-platform 10⁻⁹: qualified in reproducibility ("reported by the project; not re-run for this review").
- Reproducibility overclaim ("every statistic can be regenerated"): replaced with the actual scope (B1, B7−B8, B8 regenerated; others checked against stored values).

### Thresholds (both values preserved; not resolved)
- New subsection "Decision Thresholds" in `sections/reproducibility.tex`: τ* = 0.072905 (freeze manifest) and τ = 0.040511 (test record). Neither is treated as a validated operating point. The test-split operating point (TPR 0.505, FPR 0.147) is not reported. The test-split AUROC is threshold-free. The macOS frozen-threshold study is threshold-dependent and not verified.

### Data and code availability
- New subsection "Data and Code Availability" in `sections/reproducibility.tex`. It names the branches and commits, verified against git: `research/v8-linux-validation` (dev records, stats script and summary, manuscript sources); `research/v8-mac-hardening` (commits 8e28f601, b9b8a86c); frozen commit 2edfe568; security suite commit df612db0. The realexec matrix is on both branches.
- Public access status is a placeholder: **[to be confirmed by the authors before submission]**. Public release was not verified.

### Figure
- `fig_evidence_landscape.pdf` regenerated with `scripts/make_figures.py` (working-tree copy; exit 0) in a scratch copy outside the repository. Inputs: `datasets/v8/dev_records.jsonl` and `audit/five_dataset_summary.json`. Only this figure was copied into `manuscript_final/figures/`. Panel (c) is the excluded five-dataset artifact, hatched and labelled excluded; the caption says so. Not visually inspected in this pass.
- Note: `make_figures.py` is not tracked at HEAD; only the working-tree copy exists.

### Evidence manifest
- `closeout/FINAL_EVIDENCE_MANIFEST.json`: 28 rows from `CLAIM_EVIDENCE_MATRIX.csv`, each with its source path, git blob at HEAD where the path resolves, matrix result, final status and note. Status counts are in the file.

### LaTeX compilation
- **Not performed.** No TeX toolchain is installed (`pdflatex`, `latexmk`, `bibtex` absent). Per instruction, no toolchain was installed or repaired. `main.pdf` is the stale pre-edit build (`main.STALE_pre_edit.pdf`). Citation keys, cross-references and the regenerated figure have not been compiled.

### Items this pass did not change
- Frozen test suite: incomplete (372 passed, 0 failed of 806). Recorded as incomplete, not passing.
- Holding for authors: public release status, the held-out wording's authorship review, and the QuixBugs register row.
