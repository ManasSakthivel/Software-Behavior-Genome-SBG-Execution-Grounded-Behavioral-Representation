# Dataset provenance (V7-B development pairs)

All 321 pairs are **non-pristine**: they were seen by the developers and shaped V5, V6 and V7-B. None is a held-out or independent benchmark; no sealed holdout exists. See [`research/benchmarks/INDEPENDENCE_AND_LEAKAGE_AUDIT.md`](../research/benchmarks/INDEPENDENCE_AND_LEAKAGE_AUDIT.md), [`research/benchmarks/DATASET_INVENTORY.md`](../research/benchmarks/DATASET_INVENTORY.md) and [`datasets/README.md`](../datasets/README.md). Pair construction is `tasks_quixbugs`, `tasks_synthetic` and `tasks_bugsinpy` in [`experiments/v7b/k1_spike.py`](../experiments/v7b/k1_spike.py); the label rules are in [`scripts/build_dev_pairs_csv.py`](../scripts/build_dev_pairs_csv.py).

## Arms (321 pairs)
| Arm | Pairs | Source and path (as read by `k1_spike.py`) | Base / variant | Label used |
|---|---|---|---|---|
| `quixbugs` | 31 | `external/quixbugs/manifest.json` (programs with `eligible.declared`); QuixBugs upstream commit `4257f44b0ff1181dedaedee6a447e133219fcebf`, MIT | buggy / fixed; inputs from the declared JSON test cases (first 12) | declared tests: DIV for 29, UNLABELLED for 2 (no test separates buggy from fixed) |
| `quixbugs_neg` | 85 | the `negatives` listed in the same manifest (`external/quixbugs/variants/`), semantics-preserving transformations of the fixed programs | fixed / transformed; same inputs | generator label (equivalent) |
| `synthetic` | 150 (78 CHANGED, 72 EQUIVALENT) | `benchmark/datasets/v8/pairs_*.jsonl` and `benchmark/datasets/v10_independent/pairs_*.jsonl`; stratified draw of at most one EQUIVALENT and one CHANGED pair per base program (`random.Random(20261117)`), trimmed to 150 | `base_path` / `variant_path` of each record; inputs from `experiments.final.entry_policy.select_entry_structural` (first 12) | generator label (`expected_label`), not adjudicated |
| `bugsinpy_units` | 55 (9 not driven) | `external/bugsinpy/manifest.json`; BugsInPy commit `11c5f1eea954a42132cfd06bf257766a7963e0fd` plus upstream code at the recorded buggy/fixed commits; per-project licences in `external/bugsinpy/README.md` | buggy / fixed function units; inputs from the same structural entry policy (a synthetic battery, not tests aimed at the bug) | none: UNLABELLED |

The synthetic arm is built from the repository's own SC/SP transformation generators over the authored corpus in `benchmark/` (`datasets/README.md`), so it is not independent of V5/V6 development; the directory name `v10_independent` must not be read as independence from V7-B.

## Counts and denominators
- 31 + 85 + 150 + 55 = 321 pairs. 9 BugsInPy class units are not driven (the engine supports top-level functions only), leaving 312 driven pairs.
- Primary analyses use 258 pairs: 321 minus 57 UNLABELLED (55 BugsInPy plus the 2 QuixBugs pairs without a distinguishing test) and 6 SUSPECT_LABEL (generator labels known to be doubtful: SP-8, SP-11 and levenshtein SP-6 per the script). Of the 258, 106 are divergent (DIV) and 152 are not (NO_OBS_DIFF).
- Pair-level clustering: all QuixBugs pairs are one project; synthetic pairs cluster by base program; BugsInPy pairs by project. The analysis report states 78 and 69 projects for the two bootstrap strata (divergent, other).

## Limits of use
Truth is test-based or generator-based and unadjudicated; some synthetic labels are known wrong; BugsInPy units have no defensible truth. Results on these data are exploratory and say nothing about independent code. Raw vendored data (about 4.8 MB under `external/`) is in git; if it is lost, `datasets/README.md` gives acquisition steps. Independent data (K5) has not been acquired; candidates are assessed in `research/benchmarks/DATASET_INVENTORY.md` and nothing was run on them.
