# Archived documents

Everything under this directory is **superseded**. It is kept because it is the
record of what was claimed at each stage, and deleting it would destroy the
evidence a reviewer needs to check how the conclusions moved.

Nothing here should be cited as a current result. `docs/VERSION_MAP.md` says
which version each document belongs to and what replaced it.

| Directory | Contents |
|---|---|
| `superseded/` | Top-level reports and status documents from V1–V5, including the `FINAL_*` series |
| `v2/` `v3/` `v4/` `v5/` | Per-version experiment reports |

Several of these documents contain numbers the current evidence has withdrawn.
The three that matter most:

- the hard-negative score of 12/12 and the regression score of 14/15 are
  **output-comparison** results. They were reported under headings such as
  "Behavioral oracle", which reads as an SBG result. SBG V5 scores 5/12 and
  7/15 on the same pairs (`artifacts/final/HARD_NEGATIVE_V5_RESULTS.json`,
  `artifacts/final/REGRESSION_V5_RESULTS.json`).
- the benchmark is described as 3,777 pairs over 99 programs. It holds 3,577
  pairs over 60 assigned programs (`benchmark/benchmark_manifest.json`).
- the main-benchmark AUROC is reported against 744 test pairs. It was computed
  over the 643 that executed.

`experiments/final/consistency_check.py` exempts this directory from the
retired-claim scan for exactly that reason.
