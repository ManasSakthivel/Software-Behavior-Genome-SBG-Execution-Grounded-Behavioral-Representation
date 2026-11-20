> **SUPERSEDED (2026-11-20).** Section 1 is wrong. `scripts/stats_recompute.py` and `audit/stats_summary.json` are tracked at HEAD of `~/Desktop/SBG-V8-LINUX` under `paper/IEEE_ACCESS_V8_FINAL/`. They were searched only at the top-level paths. The tracked files were found, the script was re-run, and every non-timing field reproduced. See `STATS_RECOVERY_REPORT.md` (the current report). This file is kept unedited as the record of the earlier search.

# Interval recovery report (Decision 2)

Date: 2026-11-20. Scope: the +1.6 pp matched-coverage interval and the B1 interval in the manuscript. Read-only search of `~/Desktop/SBG-V8-LINUX`; corrections applied to the manuscript copy only.

## 1. Scripts and summary file

`scripts/stats_recompute.py` and `audit/stats_summary.json` are absent from every ref and from all of git history (`git log --all -- <path>` returns nothing). They cannot be used as a source.

## 2. +1.6 pp primary contrast: recovered from raw results

Source: committed multi-seed raw results, commit `f632ad94`, `results/v8_dev_eval_20261119_055209_linux_soft/seed{0..4}/tables/primary.csv`, run metadata `run_meta.json` (`records` = `dev_records.jsonl`, `n_records` = 312, `boot_primary` = 2000, `strict_blockers` = false).

Contrast `vs_b7@v7b_gate`, c* = 0.2364:

| Seed | risk_a | risk_b | diff (B7 − B8) | percentile 95% CI | BCa 95% CI |
|---|---|---|---|---|---|
| 0 | 0.2131 | 0.2295 | +0.0164 (+1.6) | [−0.0636, +0.1626] | [−0.0668, +0.1530] |
| 1 | 0.1967 | 0.2131 | +0.0164 (+1.6) | [−0.0520, +0.1709] | [−0.0734, +0.1320] |
| 2 | 0.2131 | 0.2459 | +0.0328 (+3.3) | [−0.0442, +0.1492] | [−0.0418, +0.1524] |
| 3 | 0.2541 | 0.2131 | −0.0410 (−4.1) | [−0.0923, +0.1560] | [−0.1282, +0.0624] |
| 4 | 0.2623 | 0.2131 | −0.0492 (−4.9) | [−0.0781, +0.1182] | [−0.1179, −0.0265] |

- Sign convention: "positive values favour B8" (`results.tex` figure caption). The diff column is B7 minus B8, so positive favours B8. Consistent with the manuscript.
- The per-seed values +1.6, +1.6, +3.3, −4.1, −4.9 (mean −0.5) reproduce the manuscript's sentence at `results.tex:86` exactly.
- The seed-0 headline (+1.6) reproduces. The manuscript's interval `[−6.6, +16.3]` does **not** match the source:
  - percentile lower bound is −6.36, which rounds to −6.4;
  - BCa lower bound is −6.68, which rounds to −6.7;
  - upper bound +16.26 rounds to +16.3 (matches).
  The manuscript's −6.6 looks like a truncation of the BCa value, but the upper bound is rounded. The two methods are mixed.

**Correction applied (manuscript copy):** the interval is now the percentile interval, reported as `[−6.4, +16.3]`, with the method and seed stated, and the BCa interval `[−6.7, +15.3]` disclosed in the results text. The rounding is now consistent with the source. Changed locations:

| File | Line(s) | Change |
|---|---|---|
| `sections/abstract.tex` | 1 | −6.6 → −6.4 |
| `sections/introduction.tex` | 45 | −6.6 → −6.4 |
| `sections/conclusion.tex` | 9 | −6.6 → −6.4 |
| `sections/results.tex` | 76 | −6.6 → −6.4; method and BCa stated |
| `sections/results.tex` | 104 (table) | −6.6 → −6.4 |
| `sections/discussion.tex` | 25 (table), body | 6.6 → 6.4 |

Method note: the primary test's p-value and one-sided bound are in the same file (`lower97.5_one_sided` = −0.0636; `p_one_sided` = 0.4195 for seed 0). Those are not changed.

## 3. B1 interval: not recovered; removed

The manuscript sentence (`results.tex:56`): "Plain differential testing (B1) ... an observed risk of 0.169 [0.086, 0.354]."

- The point values (183 NDO pairs of 258, 31 with Y=1) come from the manuscript, not from a source file I re-checked in this pass.
- A Wilson 95% interval for 31/183 is [0.122, 0.228]. The manuscript's [0.086, 0.354] does not match a Wilson interval.
- The interval is evidently a cluster bootstrap (the manuscript says one cluster holds 43.8% of labels). The bootstrap code and seed for it are not in the repository, and the cluster definition is not recorded in a file I found. Regenerating it would mean choosing a method myself, which the brief does not permit.

**Action:** the interval is removed. The text now reads "an observed risk of 0.169 (interval not recovered from source; not reported)." The point value is retained as a manuscript value, not re-verified.

## 4. Other intervals in the same paragraphs: not re-verified

These values appear in the manuscript but were not traced to a source in this pass, so they are **not confirmed** and are not changed:

- `results.tex:57`: B3 risk 0.213 [0.090, 0.457]. The matched-coverage file has B7 at c* with CI [0.114, 0.466]; the B3 row has no CI.
- `results.tex:76`: B8 risk 0.213 [0.124, 0.392]; B7 0.230; B9 0.292; multiplicity 0.295.
- `results.tex:76` and `:107`: B9 − B8 +7.9 [−2.8, +14.7]; the gate contrast "0.0 [−6.2, …]".

These should be traced in the next pass (`matched_coverage.csv` and `primary.csv` for the same runs) before the manuscript is called final. Until then they are listed as unverified in the claim register.

## 5. Status

- +1.6 pp contrast and its interval: **recovered and corrected** from authentic raw results (`f632ad94`).
- B1 interval: **removed**, with the reason recorded.
- Other intervals: **open**, listed as unverified.
- Source files are read-only; nothing under `~/Desktop/SBG-V8-LINUX` was changed.
