# Phase 2 execution handoff

This document is for the person running the remaining Phase 2 experiments. It
contains no scientific decisions and no expected numbers. The protocol is
fixed in [`PHASE2_PREREGISTRATION.md`](PHASE2_PREREGISTRATION.md) (SHA-256
`905e3d3a…9067`). If a step here seems to need a decision, **stop and report**.
Do not choose.

Current progress is tracked in [`/STATUS.md`](../../STATUS.md).

---

## 0. Rules that cannot be broken

1. **Do not edit** any of the following:
   - `docs/current/PHASE2_PREREGISTRATION.md`;
   - anything under `benchmark/datasets/`;
   - anything under `external/`;
   - `artifacts/final/THRESHOLD_FROZEN.json`;
   - any `artifacts/final/freeze_*.json`;
   - `artifacts/final/PHASE2_FREEZE.json`.
2. **τ\* = 0.072905** (reported to four places as 0.0729). It was derived
   from dev only. It must not be re-derived, rounded, or changed using TEST
   or external data. `derive_threshold.py` must not be run again.
3. **Do not run the dev split again.** Dev is complete and τ\* depends on
   its exact output file (SHA-256 `64deffbc…3e0ee6`).
4. **TEST is scored once.** Run `make v7-test` only after `make v7-fit` has
   written `WEIGHT_FITTING.json`.
   - Once `artifacts/final/MAIN_EVALUATION_v6test_output_free_v7.json`
     exists, never run `v7-test` again.
   - If `v7-test` crashes before that file is written, it may be re-run,
     because no test score has been produced.
5. **Do not change code, constants, timeouts, seeds or budgets** to make a
   run succeed. Record failures as the scripts emit them.
   - A program that times out, fails to import or is non-terminating is a
     result, not a bug.
6. **Do not open, summarise or compare results between stages.** The order
   below exists so that nothing downstream is chosen after seeing TEST.
7. **Commit nothing** except what §7 says.

---

## 1. Environment

| Item | Requirement |
|---|---|
| Python | **CPython 3.13** (the artifacts so far were produced on 3.13.15). Every run uses `.venv/bin/python`. |
| Test runner | `requirements-lock.txt` (pytest 9.1.1 and pins). The pipeline itself is standard-library only. |
| Java (Java stage only) | A JDK with `javac` and `java` on `PATH`. The Java stage was built against OpenJDK 21.0.12.1. |
| OS | macOS or Linux. |
| Network | Not needed. Every corpus is vendored under `external/`. |
| Environment variables | **None required.** Do not set `PYTHONHASHSEED` or any other variable the dev run did not have. |
| Seeds | In-code constants; set nothing. Do not change them: `SEED = 42` (execution, bootstraps), `N_RUNS = 5`, `SP_SEED = 0` (negatives, already generated), bootstrap resamples `2000`. |

Setup, from the repository root:

```bash
git checkout phase2-handoff      # the branch this document was committed on
make setup                       # python3.13 -m venv .venv && pip install -r requirements-lock.txt
export PYTHON=.venv/bin/python   # every make target below uses $(PYTHON)
```

Preflight checks. All three must pass before anything runs:

```bash
$PYTHON -m pytest sbg/ tests/ -q              # full suite
make verify-v7-invariance                     # expect: "0 violations"; sort_heapsort is listed as nondeterministic (known, see §8)
$PYTHON experiments/final/consistency_check.py 2>&1 | grep C9   # expect: [PASS] C9
```

---

## 2. Stage order and commands

Run the stages in this order. Stages 2c, 2d and 2e are independent of 2a/2b
and of each other, so they may run in parallel on separate machines.

| # | Stage | Command | Status at handoff |
|---|---|---|---|
| — | class-driver **DEV** | *(no command — frozen)* | **DONE** |
| 2a | class-driver **TRAIN** | `make v7-train` | pending (a run was stopped part-way; nothing kept) |
| 2b | **weight fitting** | `make v7-fit` | pending (needs 2a) |
| 2c | class-driver **TEST**, final frozen evaluation | `make v7-test` | pending (needs 2b) |
| 2d | **QuixBugs** (Python) | `make quixbugs` | pending (corpus frozen) |
| 2e | **BugsInPy** | `make bugsinpy` | pending (corpus frozen) |
| 2f | **Java** (QuixBugs Java) | `make java` | pending (corpus frozen) |
| 3 | **final gate** | see §6 | pending (needs all above) |

What each target runs, verbatim:

```bash
# 2a  v7-train
$PYTHON experiments/final/run_main_evaluation.py --split train --protocol output_free_v7 --dataset-dir benchmark/datasets/v6 --tag v6train
$PYTHON experiments/final/static_baselines.py --pairs artifacts/final/pairs_v6train_output_free_v7.jsonl --dataset benchmark/datasets/v6

# 2b  v7-fit   (fits on train, selects on dev; refuses to run if any test file already holds learned scores)
$PYTHON experiments/final/fit_weights.py fit

# 2c  v7-test  (the single test scoring)
$PYTHON experiments/final/run_main_evaluation.py --split test --protocol output_free_v7 --dataset-dir benchmark/datasets/v6 --tag v6test
$PYTHON experiments/final/static_baselines.py --pairs artifacts/final/pairs_v6test_output_free_v7.jsonl --dataset benchmark/datasets/v6
$PYTHON experiments/final/fit_weights.py score
$PYTHON experiments/final/analyse_results.py --split test --protocol output_free_v7 --tag v6test --audit artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json --family prereg_v7
$PYTHON experiments/final/fit_weights.py test

# 2d  quixbugs   (the "prepare" stage is frozen -- never run it)
$PYTHON experiments/final/external_quixbugs.py score   --protocol output_free_v7
$PYTHON experiments/final/external_quixbugs.py analyse --protocol output_free_v7

# 2e  bugsinpy   (the "fetch" and "build" stages are frozen -- never run them)
$PYTHON experiments/final/external_bugsinpy.py score --protocol output_free_v7

# 2f  java       (the "vendor" stage is frozen -- never run it)
$PYTHON experiments/final/external_java.py run
$PYTHON experiments/final/external_java.py finalize
```

Runtimes have not been measured on the final code, so none are given. Log
each stage with `2>&1 | tee logs/<stage>.log` (`logs/` is git-ignored via
`*.log`). Record the wall-clock time in `STATUS.md`.

---

## 3. Inputs and outputs of every stage

Every path is relative to the repository root.

| Stage | Reads | Writes (expected artifact filenames) |
|---|---|---|
| 2a | `benchmark/datasets/v6/pairs_train.jsonl`, `benchmark/corpus/base_programs/`, `benchmark/datasets/v6/variants/train/` | `artifacts/final/pairs_v6train_output_free_v7.jsonl`, `artifacts/final/programs_v6train_output_free_v7.json` |
| 2b | `pairs_v6train_output_free_v7.jsonl`, `pairs_v6dev_output_free_v7.jsonl`, `BENCHMARK_VALIDITY_AUDIT_V7.json` | `artifacts/final/WEIGHT_FITTING.json` (train fit + dev choice) |
| 2c | `benchmark/datasets/v6/pairs_test.jsonl`, test variants, `WEIGHT_FITTING.json`, `BENCHMARK_VALIDITY_AUDIT_V7.json`, `THRESHOLD_FROZEN.json` | `artifacts/final/pairs_v6test_output_free_v7.jsonl`, `artifacts/final/programs_v6test_output_free_v7.json`, `artifacts/final/MAIN_EVALUATION_v6test_output_free_v7.json`; `WEIGHT_FITTING.json` completed with test results |
| 2d | `external/quixbugs/` (manifest, programs, variants, json_testcases inputs), `THRESHOLD_FROZEN.json` | `artifacts/final/pairs_quixbugs_canonical_output_free_v7.jsonl`, `artifacts/final/pairs_quixbugs_declared_output_free_v7.jsonl`, `artifacts/final/QUIXBUGS_output_free_v7.json` |
| 2e | `external/bugsinpy/` (manifest, units), `THRESHOLD_FROZEN.json` | `artifacts/final/pairs_bugsinpy_output_free_v7.jsonl`, `artifacts/final/BUGSINPY_output_free_v7.json` |
| 2f | `external/quixbugs_java/` (MANIFEST, buggy, correct, declared_inputs), `THRESHOLD_FROZEN.json` | `artifacts/final/QUIXBUGS_JAVA_SBG_RESULTS.json` |
| 3 | all of the above | `artifacts/final/STANFORD_GATE.json` |

**Files that already exist locally from the stopped runs.** The following are
unreviewed and **not committed**. The stages above overwrite them. Do not use
them:

- `pairs_quixbugs_*_output_free_v7.jsonl`;
- `pairs_bugsinpy_output_free_v{6,7}.jsonl`;
- `BUGSINPY_output_free_v{6,7}.json`.

---

## 4. Frozen inputs and their SHA-256

These values are also recorded in `artifacts/final/freeze_handoff.json`, and
consistency check **C9** verifies them. If C9 fails at any point, **stop**.

| File | SHA-256 |
|---|---|
| `docs/current/PHASE2_PREREGISTRATION.md` | `905e3d3a9929379486bb2fe1b83938ff5d67df94047662b6548bfdbdd9c67067` |
| `artifacts/final/THRESHOLD_FROZEN.json` (τ\* = 0.072905) | `9dcd74eb97088bdc8fc31df9a33f082893a88afdd6bc8c50a65b95812102173b` |
| `artifacts/final/pairs_v6dev_output_free_v7.jsonl` (dev scored file) | `64deffbc0c0839a4bd0d825e9e59154b33d7ae98944f2b7f5bec3b91903e0ee6` |
| `artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json` | `4360b99f942a7f30b3165c4a7197717dbb11c234dc68e7a9a4ad366df49fb347` |
| `benchmark/datasets/v6/pairs_train.jsonl` | `e5259734572414ea78410662190b0d17b9d67ba3e5c31c75c135187c39c0dff9` |
| `benchmark/datasets/v6/pairs_dev.jsonl` | `f58b92256d648e6e5e6fe23547b32084cfe89808133d00528d79a9eb538fdbdd` |
| `benchmark/datasets/v6/pairs_test.jsonl` | `ada35810bd783fe194e86ebda29f1bd729ad3a396c772d4a0406b1d532c2b396` |
| `external/quixbugs/manifest.json` (upstream commit `4257f44b`) | `49491ccbe1296907a69c4ce93c8b6990d32a025518f72c1ec2eba267c732c056` |
| `external/bugsinpy/manifest.json` (BugsInPy commit `11c5f1ee`) | `5953c43b82f6f46a90d489a3d99fe8976a26827ada71bd5e759b418f3fdbf558` |
| `external/quixbugs_java/MANIFEST.json` (upstream commit `4257f44b`) | `46773144b124678d958f4ca24cd2b56090809df40621c4dd9433790dbf5ec1ba` |

Hashes of the individual QuixBugs negatives and BugsInPy units are in
`artifacts/final/freeze_quixbugs.json` and `artifacts/final/freeze_bugsinpy.json`.
C9 checks them too.

---

## 5. Validating each stage, and resuming after an interruption

No stage checkpoints internally. **A stage is either complete, meaning its
artifact exists and validates, or it is re-run from its first command.**
Completed stages are never re-run, with the exception of 2c described in §0.4.

Run the stage's validation directly after it finishes:

| Stage | Complete when | Validation command |
|---|---|---|
| 2a | the train pairs file has one row per train pair (1129 rows) | `wc -l < artifacts/final/pairs_v6train_output_free_v7.jsonl` → `1129`; `grep -c '"static_ast"' artifacts/final/pairs_v6train_output_free_v7.jsonl` → the number of evaluated rows |
| 2b | `WEIGHT_FITTING.json` exists with a `chosen_on_dev` field, and **no** test pairs file exists yet | `$PYTHON -c "import json;print(json.load(open('artifacts/final/WEIGHT_FITTING.json'))['chosen_on_dev'])"`; `ls artifacts/final/pairs_v6test_output_free_v7.jsonl` → must fail |
| 2c | `MAIN_EVALUATION_v6test_output_free_v7.json` exists | `wc -l < artifacts/final/pairs_v6test_output_free_v7.jsonl` → `488`; `$PYTHON experiments/final/consistency_check.py 2>&1 \| grep -E "C3\|C7\|C9"` → all PASS |
| 2d | `QUIXBUGS_output_free_v7.json` exists | `$PYTHON -m pytest tests/test_external_quixbugs.py -q`; consistency C9 PASS |
| 2e | `BUGSINPY_output_free_v7.json` exists | `$PYTHON -m pytest tests/test_external_bugsinpy.py -q`; consistency C9 PASS |
| 2f | `QUIXBUGS_JAVA_SBG_RESULTS.json` exists | `$PYTHON -m pytest tests/test_external_java.py -q` |

How to resume:

| If this is interrupted | Do this |
|---|---|
| 2a | Delete any partial `pairs_v6train_*`/`programs_v6train_*` and re-run `make v7-train`. |
| 2b | Re-run `make v7-fit`. |
| 2c, before `MAIN_EVALUATION_v6test_output_free_v7.json` exists | Delete the partial `pairs_v6test_*`/`programs_v6test_*` and re-run `make v7-test`. `fit_weights.py fit` is not re-run. |
| 2c, after it exists | Do nothing. Report it. |
| 2d, 2e, 2f | Re-run the stage's make target. Each overwrites its own outputs, and none reads another's. |

Update `STATUS.md` after every stage: status, date, wall-clock time, machine,
the exact Python version (`$PYTHON -V`), and the commit hash of the code that
ran.

---

## 6. Final statistics and the evidence-driven gate

The statistics are computed by the stages themselves:

- 2c: `analyse_results.py` and `fit_weights.py test`;
- 2d: `external_quixbugs.py analyse`;
- 2e: `external_bugsinpy.py score`;
- 2f: `external_java.py finalize`.

To regenerate them **from the committed per-pair files, without executing any
program**:

```bash
$PYTHON experiments/final/analyse_results.py --split test --protocol output_free_v7 --tag v6test --audit artifacts/final/BENCHMARK_VALIDITY_AUDIT_V7.json --family prereg_v7
$PYTHON experiments/final/fit_weights.py test
$PYTHON experiments/final/external_quixbugs.py analyse --protocol output_free_v7
```

Then the gate, and the checks that audit it:

```bash
make gate                                              # writes artifacts/final/STANFORD_GATE.json, prints PASS/BLOCKED per category
$PYTHON experiments/final/consistency_check.py         # C9 = frozen inputs unchanged; C10 = gate recomputed from artifacts and quoted exactly
```

- **C9** must PASS at every stage.
- **C10** passes once `STANFORD_GATE.json` exists and matches a fresh
  recomputation.

The gate will still report some categories BLOCKED after every run
completes:

- novelty;
- research maturity;
- generalisation validity;
- claim discipline;
- reproducibility, for the `README`/report citations.

These categories need the README and the readiness report rewritten from the
new artifacts. That is authoring work for the integrator, not part of this
handoff. Report the gate output exactly as printed.

---

## 7. What to commit

After each completed stage, commit **only** that stage's output files from §3,
plus `STATUS.md`. Use one commit per stage, with the message
`phase2: <stage> results`. Do not commit logs, `.venv`, caches, or the
unreviewed files listed in §3. Do not push to `main`; push the
`phase2-handoff` branch.

---

## 8. Known conditions (record them; do not fix them)

- **`sort_heapsort` is nondeterministic.** Its traced event count differs
  between back-to-back runs in the same process (8855 vs 8771 observed).
  `make verify-v7-invariance` lists it as nondeterministic; this is expected.
  Its committed v6 record is one sample. This is pre-existing, and the Phase 2
  code did not introduce it.
- **Cross-version sensitivity.** Traced distances change between Python 3.9
  and 3.13 (`artifacts/final/PYTHON_VERSION_SENSITIVITY.json`), which is why
  3.13 is mandatory.
- **QuixBugs harness timeouts.** In the stopped QuixBugs run, `mergesort` and
  `possible_change` hit the harness timeout in the declared-input regime. If
  they recur, the script records them as failures. Leave them.
- **Driver threads.** `conc_read_write_lock` constructs a lock driven by one
  thread. A non-terminating driver sequence is classified as
  `nonterminating` by the budget rules. Leave it.
