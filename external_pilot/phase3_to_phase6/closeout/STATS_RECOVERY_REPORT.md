# Statistics recovery report (Decision 2)

Date: 2026-11-20. Scope: the +1.6 pp matched-coverage interval [-6.6, +16.3] and the B1 interval [0.086, 0.354] cited in the SBG V8 manuscript.

## Search scope

- `~/Desktop/SBG-V8-LINUX` (read only): tracked files at HEAD, all 25 branches, reflog, stash, `git fsck --lost-found`, working tree.
- Search strings: `stats_recompute`, `stats_summary`, `matched-coverage`, `0.354`, `0.086`, `+1.6`, `16.3`.
- Not searched: `~/Desktop/SBG-V6` and `~/.Trash` (the forked search that was meant to cover them did not report).

## Findings

Earlier notes stated that no source existed. That was wrong. Both sources are tracked in the repository.

| Item | Location | Commit / state |
|---|---|---|
| Generator script | `paper/IEEE_ACCESS_V8_FINAL/scripts/stats_recompute.py` | tracked; unmodified in working tree |
| Summary output | `paper/IEEE_ACCESS_V8_FINAL/audit/stats_summary.json` | tracked, last changed in `df612db0`; generated 2026-11-19 22:34 |
| Input records | `datasets/v8/dev_records.jsonl` | tracked; md5 `07e57a80a2d9060d42748626e0819436` (matches the script's recorded checksum) |
| Input runs | `results/v8_dev_eval_20261119_055209_linux_soft/`, `..._060213_linux_strict/` | tracked |

The dangling commit `dfc01268` and the stash are unrelated (experiment and sprint files), so no other copy was needed.

## Reproduction

- Clean export of HEAD (`git archive`) to `~/SBG_EXTERNAL_PILOT/closeout_scratch_stats`. The source repository was not modified.
- Environment: CPython 3.13, numpy 2.5.5, scipy 1.18.1 (the versions in `SBG_V8_DEPENDENCY_LOCK.installed.txt`), in `~/SBG_EXTERNAL_PILOT/closeout_scratch_venv`.
- Command: `PYTHONPATH=. python -I paper/IEEE_ACCESS_V8_FINAL/scripts/stats_recompute.py --refit --B 10000`. Exit 0, 72 s. Log: `recovered_stats/stats_rerun_log.txt`.
- Comparison with the tracked `stats_summary.json`: every non-timing field is identical. The only differences are `fit_seconds` and the generation timestamp.

## Values

| Quantity | Stored / reproduced value | Manuscript | Match |
|---|---|---|---|
| B1 observed risk (soft, seed 0) | 0.1694 (31 / 183) | 0.169 | yes |
| B1 cluster-bootstrap 95% CI | [0.08560, 0.35354] | [0.086, 0.354] | yes (rounded) |
| B7 − B8 matched-coverage difference (soft) | +0.01639 (+1.6 pp) | +1.6 | yes |
| B7 − B8 cluster-bootstrap 95% CI | [-0.06577, +0.16254] | [−6.6, +16.3] pp | yes (rounded) |
| B8 matched-coverage risk and CI (soft) | 0.2131, [0.1238, 0.3918] | 0.213 [0.124, 0.392] | yes (rounded) |

Method, as stated in the script: project-cluster bootstrap, B = 10,000, seed 20261119, with an independent RNG stream. The matched-coverage contrast is computed at c* = 0.2364 under the soft policy.

## Manuscript sentences that depend on these intervals

- `sections/results.tex:56`: "an observed risk of 0.169 [0.086, 0.354]" (B1). Supported.
- `sections/results.tex:76`: "B8 has risk 0.213 [0.124, 0.392] ... B7 minus B8 ..." (B8 interval and contrast). Supported.
- `sections/results.tex:104`: table row "B7 − B8 | H2 (primary) | +1.6 | [−6.6, +16.3]". Supported.
- `sections/introduction.tex:45`: "differed ... by 1.6 percentage points, with an interval from −6.6 to +16.3". Supported.
- `sections/conclusion.tex:9`: "+1.6 points, interval −6.6 to +16.3, sign unstable". Supported. The phrase "sign unstable" is not re-derived in this report and must be checked separately.
- `sections/discussion.tex:25`: "No (up to +16.3 admitted)" and "B8 worse by >6.6 or better by >16.3". Derived from the same interval. Supported.

## Verdict

Both intervals are **VERIFIED** by reproduction from raw repository data. No interval is regenerated, estimated or removed. The manuscript values are rounding of the reproduced values and may stay as they are.

## Limitations to disclose

- The contrast is on the development data (312 records, 258 labelled). The script labels it exploratory, not independent validation.
- The seed-0 out-of-fold predictions were regenerated (no saved per-pair predictions), and checked against the saved `results.json` for log loss, Brier and slope. Seeds 1–4 are read from saved outputs, not re-run.
- The "sign unstable" wording in the conclusion is not covered by this recovery.
