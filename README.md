# SBG V7-B: an evidence contract for differential execution of code changes

**Status: exploratory research prototype. Branch `research/v7b-final-validation`. No confirmatory result exists.**
The previous README (V5/V6-era claims) is kept unchanged at [`docs/README_pre_v7b.md`](docs/README_pre_v7b.md). Its numbers (for example AUROC 0.897) are about a different method (V5/V6 behavioural distance), were measured on developer-authored benchmarks, and are **not** results of V7-B.

---

## 1. Positioning

V7-B is a small Python tool plus an evaluation harness. Given two versions of a Python function and a set of inputs, it runs both in isolated child processes and reports one of three verdicts, each backed by a replayable evidence record:

- `DIVERGENT_OBSERVABLE`: a replay-confirmed input on which the two versions differ in an observed channel (a witness).
- `INSUFFICIENT(reason)`: the tool refuses to conclude.
- `NO_DIVERGENCE_OBSERVED(S1|S2)`: no difference was seen on the inputs tried, plus a sufficiency level describing how much of the changed code those inputs reached.

It is positioned as a **design and feasibility study with a negative-result flavour**, not as a validated detector. An independent red-team review ([`reports/final/INDEPENDENT_RED_TEAM_REVIEW.md`](reports/final/INDEPENDENT_RED_TEAM_REVIEW.md)) rated it "publishable only as a design/feasibility/negative-result report; not ready as a validation paper", and nothing in this repository contradicts that.

## 2. Overview

| | |
|---|---|
| Input | two `.py` files, the name of one top-level function, a JSON list of arguments, an optional JSON config |
| Output | `verdict.json` and a hash-chained `evidence.jsonl` in an output directory |
| Isolation | fresh child process per run under macOS `sandbox-exec` (network and writes denied, rlimits) |
| Scope | top-level Python functions with JSON-representable arguments, CPython 3.13, macOS |
| Evaluation | 321 development pairs from QuixBugs, BugsInPy units and synthetic transformations, all **non-pristine** |
| Code | [`sbgv7/`](sbgv7) (about 1,100 lines); V5/V6 code (`sbg/`, `sbgv6/`) is untouched |

## 3. The problem

A reviewer who sees a code change wants to know whether the behaviour changed. Running both versions on some inputs and comparing outputs (differential testing) can find a difference but cannot show there is none; a quiet run is easily over-read as assurance. V7-B asks a narrower question: can a tool report differences with replayable evidence, refuse when its evidence is weak (nondeterminism, changed code never executed), and never state "equivalent"?

## 4. Contributions

### 4.1 Implemented (software exists and is tested)
- A closed verdict set with no equivalence value; `NO_DIVERGENCE_OBSERVED` cannot be turned into "equal" by the type system (`sbgv7/records.py`, `sbgv7/decide.py`). This is a naming guarantee, not a semantic one (section 7).
- Witnesses confirmed by repeated fresh-process replay, with per-input outcomes (`CONFIRMED_DIFF`, `UNCONFIRMED_DIFF`, `ENV_SENSITIVE_DIFF`, `SAME`, `QUARANTINED`, `LIMIT_ASYMMETRIC`, `NO_RUN`).
- A changed-region activation record and S1/S2 sufficiency levels (line coverage of changed lines; S2 adds a branch-direction floor).
- Content-addressed, hash-chained evidence log and a `trace` function from verdict to runs.
- A process-per-run isolation layer (macOS only).
- Baselines B1 (plain differential), B1+rep (repeat 3 times), B2 (declared-test oracle, QuixBugs only), B3 (mutation loop), B4 (edit-size threshold), B5 (lookup of V6 scores for 237 of 321 pairs).
- Analysis and power scripts with a pre-declared plan ([`research/evaluation/STATISTICAL_ANALYSIS_PLAN.md`](research/evaluation/STATISTICAL_ANALYSIS_PLAN.md)).

### 4.2 Experimentally demonstrated
**None confirmatory.** No held-out or independent benchmark exists, gate K1 is not met and K5 is not approached. What exists are exploratory development observations (section 11): the tool ran 321 invocations without crashing, reruns of 102 pairs in the post-fix run (139 in the pre-fix run) gave identical verdicts, and it emitted no false alarm on the labelled negatives. These show the harness is stable on development data, not that it is correct or useful.

### 4.3 Exploratory (hypotheses, not findings)
- That the sufficiency level reduces false assurance relative to plain differential testing. On current data the evidence does not support this (see sections 11 and 14).
- That replay and control alternation add value over "run it 3 times" (B1+rep). On current data the difference is 2 of 311 pairs, both plain flakiness.
- That an evidence-contract framing is a useful contribution in itself, independent of detection gains.

Prior-art positioning (witnesses, patch coverage, abstention, flaky filtering all pre-exist) is in [`research/literature/RESEARCH_GAP_AND_NOVELTY_ASSESSMENT.md`](research/literature/RESEARCH_GAP_AND_NOVELTY_ASSESSMENT.md). No "first", "novel" or "state of the art" claim is made.

## 5. Architecture

```
compare BASE.py VARIANT.py --entry F --inputs inputs.json
   config.py   strict config/inputs validation
   runner.py   per input: r_det repeats, r_replay fresh replays, k_alt control-alternated runs; activation
     isolation.py + _child.py + sandbox_darwin.sb   one sandboxed child per run (macOS)
     harness.py  child-side executor: runs the entry, captures observations, line/branch hits
     compare.py  boundary comparator (return, exception, stdout, temp files, arg mutation, globals, API break)
   decide.py     pure function: outcomes + activation -> verdict + sufficiency level
   records.py    typed, content-addressed, hash-chained evidence; trace()
```

Diagram sources (Graphviz, **not rendered**; no `dot` is installed here): [`paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/figures/`](paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/figures). Implementation status per module: [`docs/architecture/V7B_IMPLEMENTATION.md`](docs/architecture/V7B_IMPLEMENTATION.md). Frozen design: [`reports/final/V7B_FROZEN_SPEC.md`](reports/final/V7B_FROZEN_SPEC.md).

## 6. Core concepts

- **Witness**: an input whose observable outcome differs between versions and is reproduced on fresh replays (`r_replay=5`, agreement on observations only). Timeouts and resource kills are never witnesses.
- **Observation boundary**: return value, exception type plus normalised message, stdout, sandbox-temp files, argument post-state, module globals written. stderr, resource use and internal state are excluded. Floats compare exactly (NaN equal, -0.0 differs from 0.0) unless a tolerance is configured.
- **Changed region**: lines that differ between versions (imported read-only from `sbgv6.features.changed_lines`).
- **Activation**: a changed unit counts as hit only by deterministic, confirmed `SAME` inputs.
- **Sufficiency**: S1 and S2 are conjunctions of floors on activation and branch-direction coverage. Thresholds (for example 0.80) are **unvalidated defaults**. S0 appears only inside `INSUFFICIENT`. S3 is refused by the config.
- **Quarantine**: nondeterministic inputs block `NO_DIVERGENCE_OBSERVED` rather than being dropped.

## 7. Verdict semantics

| Verdict | Meaning | Does NOT mean |
|---|---|---|
| `DIVERGENT_OBSERVABLE` | a replay-confirmed input differs in an observed channel | that the difference is a bug, or that the diff is the cause of a regression elsewhere |
| `INSUFFICIENT(reason)` | the tool declines; the primary reason is the highest-ranked blocker (B1..B9), e.g. `changed_region_not_activated`, `unsupported_signature`, `nondeterministic`, `resource_limit` | honest abstention in general: most INSUFFICIENT cases here come from unimplemented engine features (renamed entries, generators, classes) |
| `NO_DIVERGENCE_OBSERVED(S1\|S2)` | on the inputs tried, nothing differed and the changed region was exercised to the stated level | **equivalence, safety, correctness, "no bug", or any probability or confidence** |

**`NO_DIVERGENCE_OBSERVED` is not equivalence.** It reports what the harness looked at. Real counter-example, run in this repository (section 13): `examples/v7b/variant_hidden.py` differs from `base.py` for every `x >= 1000`, and with three small inputs the tool returns `NO_DIVERGENCE_OBSERVED` at level S1. On development data, 16 of 46 driven BugsInPy real-fix pairs received this verdict (15 at S2) although a real difference exists by construction (inputs came from a synthetic battery, not tests aimed at the bug). Precedence is `DIVERGENT_OBSERVABLE` > `INSUFFICIENT` > `NO_DIVERGENCE_OBSERVED`. Byte-identical sources are "ineligible" and receive no verdict.

S2 can be reached with as few as two inputs: levels ignore input count and diversity.

## 8. Repository layout (real, top level)

```
sbgv7/                 V7-B engine (this work): runner, harness, decide, records, isolation, baselines/
tests/v7/              V7-B tests (4 files)
tests/*.py, tests/v6/  legacy V5/V6 tests
experiments/v7b/       k1_spike.py: feasibility spike over the 321 pairs
scripts/               analyze_results.py, power_actual.py, build_dev_pairs_csv.py, generate_figures.py, run_evaluation.sh
examples/v7b/          tiny worked example used in this README
external/              vendored QuixBugs and BugsInPy units (4.8 MB)
datasets/README.md     how data is obtained (no data stored)
results/               postfix/ (current), processed/ + statistics/ + figures/ (pre-fix, superseded), raw/ (run outputs, 128+ MB)
research/              benchmarks/, evaluation/, literature/, security/, reproducibility/
reports/final/         frozen spec, P0 reconciliation, red-team review, execution log
docs/                  architecture/V7B_IMPLEMENTATION.md, README_pre_v7b.md, legacy current/, archive/, figures/
paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/   draft manuscript (uncompiled), figure register, Graphviz sources (section 17)
sbg/, sbgv6/, baselines/, benchmark/, phase5-7/, artifacts/, experiments/final/ ...   V1-V6 legacy, not modified
```

## 9. Technology stack

CPython 3.13.15 (`.venv`), standard library only for `sbgv7/`. numpy 2.5.5, scipy 1.18.1, pandas 3.1.1, matplotlib 3.11.2 for analysis and figures; pytest 9.2.0. macOS `sandbox-exec`. The legacy `sbg/` library targets Python 3.9+, and CI (`.github/workflows/ci.yml`) is a legacy workflow that is not V7-B specific.

## 10. Installation

```bash
git clone https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation.git SBG
cd SBG && git checkout research/v7b-final-validation
python3.13 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt numpy scipy pandas matplotlib
```
macOS is required for execution (see section 18). The numpy/scipy/pandas/matplotlib versions above are what was present in the author's `.venv`; `requirements-lock.txt` pins only pytest.

## 11. Quick start (commands actually run; output captured)

Run from the repository root with `.venv/bin/python`. Files are in [`examples/v7b/`](examples/v7b). Each command ran on macOS, CPython 3.13.15, on 2026-11-17.

```bash
for v in changed refactor hidden; do
  .venv/bin/python -m sbgv7 compare examples/v7b/base.py examples/v7b/variant_$v.py \
    --entry f --inputs examples/v7b/inputs.json --config examples/v7b/config.json --out /tmp/out_$v
done
```
`base.py` is `x + 1 if x < 1000 else x`; the inputs are `1, 5, 7`. Output (JSON trimmed to the verdict fields; the full object also carries ids and `cpu_seconds_spent`, about 0.5 s per pair):

| variant | what it is | verdict returned | exit |
|---|---|---|---|
| `variant_changed.py` | `x + 2` | `DIVERGENT_OBSERVABLE`, level null, a `witness_id` | 0 |
| `variant_refactor.py` | `1 + x` (same behaviour) | `NO_DIVERGENCE_OBSERVED`, level `S1` | 0 |
| `variant_hidden.py` | differs only for `x >= 1000` | `NO_DIVERGENCE_OBSERVED`, level `S1` (a real difference, missed) | 0 |

Every record also carried `"policy_below_minimum": true` (the macOS sandbox is below the spec's minimum isolation grade). Other behaviours observed: re-running into an existing output directory prints `error: .../evidence.jsonl exists; refusing to overwrite evidence` and exits 2; comparing a file with itself prints `ineligible:identical (source bytes identical; no verdict is issued)` and exits 3. Output directory contents: `evidence.jsonl`, `verdict.json`.

Tests and the evaluation pipeline: sections 15 and 16.

## 12. Configuration

JSON, strictly validated (unknown keys are errors). Defaults are the frozen-spec values and are **unvalidated**: `repeat.r_det=3`, `r_replay=5`, `k_alt=3`; `suff.s2_branch_floor=0.80`, `suff.s3_enabled=false` (true is refused); `budget.cpu_seconds=60`, `budget.per_run.cpu_s=10`, `wall_s=20`, `rss_mib=2048`; `harness.exc_message=exact_normalised`, `float_tol` 0. The evaluation runs used `{"budget": {"cpu_seconds": 60, "per_run": {"cpu_s": 2, "wall_s": 5}}}`. Schema: [`sbgv7/config.py`](sbgv7/config.py). Inputs are a JSON list of `{"id", "args", "kwargs"?}`; tuples, sets and objects are not representable.

## 13. Output: real versus illustrative

- **Real**: everything under "Quick start" (captured from actual runs) and every number in section 14 (read from `results/` files). No output in this README is illustrative or invented.
- **Not shown**: fields of `verdict.json` and `evidence.jsonl` beyond those shown are not reproduced here; see [`sbgv7/records.py`](sbgv7/records.py). `records.trace(log, verdict_id)` walks the chain; I did not run it separately for this README.

## 14. Benchmark status and results

**All exposed data is non-pristine. K1 is not met. There is no sealed holdout, no independent ground truth and no confirmatory test.**

| Arm | Pairs | Truth used | V7-B verdicts (from `results/postfix/processed/k1_spike_summary.json`) |
|---|---|---|---|
| QuixBugs buggy/fixed | 31 | declared tests (29 of 31) | 27 DIVERGENT, 4 INSUFFICIENT |
| QuixBugs SP negatives | 85 | generator label | 1 DIVERGENT, 47 NO_DIVERGENCE_OBSERVED (S1 3, S2 44), 37 INSUFFICIENT |
| Synthetic (changed + equivalent) | 150 | generator label (not adjudicated; at least 6 suspect) | 50 DIVERGENT, 45 NO_DIVERGENCE_OBSERVED (S1 13, S2 32), 55 INSUFFICIENT |
| BugsInPy units | 55 | none defensible | 6 DIVERGENT, 16 NO_DIVERGENCE_OBSERVED (S1 1, S2 15), 24 INSUFFICIENT, 9 not driven (class units) |

K1 asks for at least 100 runnable real pairs from at least 8 projects with project-level runs; the report finds 74 runnable real pairs and 0 project-level runs ([`research/evaluation/K1_K2_FEASIBILITY_REPORT.md`](research/evaluation/K1_K2_FEASIBILITY_REPORT.md)). K5 (60 projects, 250 independent divergent pairs, kappa >= 0.7) is not approached.

Descriptive comparison on the 258 pairs with usable labels (106 DIV, 152 NO_OBS_DIFF), from `results/postfix/statistics/system_metrics.csv`; intervals are 95% project-cluster bootstrap and are untrustworthy (one cluster holds 113 eligible pairs):

| System | Detection on DIV | False assurance on DIV | Abstention | False alarm on NO_OBS_DIFF |
|---|---|---|---|---|
| V7-B | 0.708 [0.545, 0.816] | 0.123 [0.054, 0.236] | 0.360 [0.306, 0.435] | 0.000 |
| B1 (plain differential) | 0.774 [0.609, 0.881] | 0.226 [0.119, 0.392] | 0 | 0.303 |
| B1+rep | 0.774 [0.610, 0.880] | 0.226 [0.120, 0.390] | 0 | 0.303 |
| B3 (mutation loop) | 0.811 [0.663, 0.904] | 0.189 [0.097, 0.337] | 0 | 0.309 |

How to read this: B1 detected every pair V7-B detected. V7-B's lower false-assurance number comes mostly from moving 18 divergent pairs into `INSUFFICIENT`, not from matched-coverage superiority. Baseline "false alarms" are dominated by 46 renamed-entry pairs (a harness artefact); without them B1's false-alarm rate is 0.000 and B1's detection (0.767) still exceeds V7-B's (0.728). No row meets the +10 percentage-point rule. Matched-coverage false-assurance (the K4 metric) was **not computed**. The observed design cannot support a confirmatory +10pp claim (power at +5pp is at best 0.27; `results/postfix/statistics/power_actual.json`). Full table and caveats: [`research/evaluation/EXPLORATORY_RESULTS.md`](research/evaluation/EXPLORATORY_RESULTS.md); the numbers above are the post-fix rerun after the red-team B-1 fix (3 pairs moved from `NO_DIVERGENCE_OBSERVED` to `INSUFFICIENT`), see [`research/evaluation/POSTFIX_RERUN_NOTE.md`](research/evaluation/POSTFIX_RERUN_NOTE.md). Synthetic-arm determinism was not re-checked post-fix (37/37 identical pre-fix).

Claims this README does **not** make (from the red-team review): that V7-B reduces false assurance, improves detection or beats differential testing or any published tool; that thresholds are calibrated; that K1 or K2 pass; that replay adds value over B1+rep; that these datasets are evidence rather than development material; any cross-platform, cross-language or "safe execution of untrusted code" claim; and any reuse of the V5/V6 AUROC numbers as V7-B results.

## 15. Testing

Run (macOS, `.venv`, nothing else running; see the protocol for the stray-process hazard):

```bash
.venv/bin/python -m pytest tests/v7 -q     # V7-B tests
.venv/bin/python -m pytest tests -q        # everything
```

Real results from this machine on 2026-11-17 (`.venv`, CPython 3.13.15):

| Scope | Result |
|---|---|
| `tests/v7` + `tests/v6` | **85 passed, 1 skipped** (the skip is the `RLIMIT_AS` test, unenforceable on macOS); also 84 passed / 1 failed once, see below |
| `tests/v7` alone | 76 collected; 4 files: `test_core.py`, `test_isolation.py`, `test_baselines.py`, `test_analysis.py` |
| all of `tests/` | 348 collected. The full run was **not completed**: it ran more than 13 minutes, I stopped it at about 85% progress with no failure shown, so the legacy V5/V6 suite is **not verified here** |

Two flakes were observed and are not fixed: `test_no_stray_processes` fails if any other V7-B run is active on the machine (it inspects the process table), and `test_timeout_asymmetric_and_both` failed once with `PermissionError` from `os.killpg` (probable race on a child that had already exited) and passed on rerun. The tests exercise sandboxed subprocesses and take about 30 s.

## 16. Reproducing

```bash
scripts/run_evaluation.sh --dry-run   # preflight and plan only
scripts/run_evaluation.sh --quick     # tests + QuixBugs-only pipeline (not comparable with committed results)
scripts/run_evaluation.sh --full      # all 321 pairs; long
```
Output goes to `results/repro/<mode>_<timestamp>/`; committed results are never overwritten. See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md), [`research/reproducibility/REPRODUCIBILITY_PROTOCOL.md`](research/reproducibility/REPRODUCIBILITY_PROTOCOL.md) and [`datasets/README.md`](datasets/README.md). Only files under `results/postfix/` (current) and `results/processed/` plus `results/statistics/` (pre-fix, superseded) are the source for numbers quoted here.

## 17. Figures and manuscript

- Data figures (PDF and PNG, generated from `results/` by `scripts/generate_figures.py`): [`results/postfix/figures/`](results/postfix/figures) (current); `results/figures/` holds superseded pre-fix versions. Exploratory data only.
- Diagram sources, **not rendered** (no `dot` installed): [`paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/figures/`](paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/figures); register: [`FIGURE_AND_TABLE_REGISTER.md`](paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/FIGURE_AND_TABLE_REGISTER.md).
- Manuscript: [`paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/`](paper/IEEE_ACCESS_INITIAL_MANUSCRIPT) (`main.tex`, see its [`README.md`](paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/README.md)). **Draft: never compiled (no LaTeX toolchain here), not peer reviewed, exploratory.** Do not cite it.

## 18. Limitations

- **macOS only.** Isolation is `sandbox-exec` (deprecated by Apple). Reads are not confined, a `setsid()` child escapes the group kill (untested), `RLIMIT_AS` and `RLIMIT_NPROC` are not enforced (memory cap is parent polling). Every record carries `policy_below_minimum=true`. This is not a mechanism for running untrusted code.
- **No Linux or container verification**: not implemented, not tested (Docker daemon was down).
- **No LaTeX compile**: manuscript unbuilt.
- **Not implemented**: S3, the explorer / input generation, module E (`internal_divergence`), declared renames, generator and class entries, Merkle tree, supersession, calibration, gates K1 to K5. Several spec reason codes are never produced (`ambiguous_entry`, `unmodelled_change`, `unsafe_program`, `blind_spot_dominant`).
- **Exploratory only**: 321 non-pristine pairs; V7-B was shaped by them; no independent labels; synthetic labels are known to be wrong in places; BugsInPy runs are function units on a synthetic battery.
- Sufficiency is line plus branch-direction coverage of the diff with unvalidated thresholds; `s2_all_channels_instrumented` is a constant `True` in `sbgv7/decide.py`. Control alternation virtualises only `random.seed` and `time`.
- Python top-level functions with JSON arguments only. No cross-language claim.
- No published tool (Testora, DiffTestGen, Mokav, shadow symbolic execution, DiffKemp) was run as a baseline.
- V7-B CPU is child-process only (lower bound); memory was not recorded.
- `make readme` and `make verify-artifacts` (legacy targets) splice generated results into the old README between markers that this README no longer has; they will fail until the Makefile is updated.

## 19. Roadmap (realistic, in order of what blocks any claim)

1. Acquire independent real pairs from projects disjoint from QuixBugs, BugsInPy and the synthetic corpus; seal a holdout before running V7-B on it; kappa-checked labels (K5).
2. Compare false assurance of V7-B against B1+rep on that set. This is the decisive experiment for the sufficiency idea; current data predicts no gain.
3. Implement declared renames, generators and class entries so `INSUFFICIENT` means something other than "engine gap".
4. Linux container isolation (I1 to I7 checks) so that K2 can be evaluated.
5. Run at least one external baseline of the Testora/DiffTestGen/Mokav class, or drop competitive claims.
6. Only then consider S3 and calibration of S1/S2.

No dates are promised. The alternative the red-team review suggests is to reframe the work as an evidence contract for differential testing rather than a sufficiency advance.

## 20. Citation

[`CITATION.cff`](CITATION.cff) exists (author Manas Sakthivel, software type, repository URL). It carries **no DOI, no version and no release date**, and its text predates V7-B. No paper describing V7-B has been published. Do not cite V7-B numbers from this README as a peer-reviewed result.

## 21. Licence

MIT, see [`LICENSE`](LICENSE) (Copyright 2025 Manas Sakthivel). Vendored datasets keep their own licences: QuixBugs is MIT (`external/quixbugs/LICENSE`); BugsInPy units stay under each upstream project's licence (`external/bugsinpy/README.md`).

## 22. Further reading

[`reports/final/V7B_FROZEN_SPEC.md`](reports/final/V7B_FROZEN_SPEC.md), [`reports/final/P0_FINAL_RECONCILIATION_REPORT.md`](reports/final/P0_FINAL_RECONCILIATION_REPORT.md), [`research/security/THREAT_MODEL.md`](research/security/THREAT_MODEL.md), [`research/security/EXECUTION_ISOLATION_AUDIT.md`](research/security/EXECUTION_ISOLATION_AUDIT.md), [`research/benchmarks/INDEPENDENCE_AND_LEAKAGE_AUDIT.md`](research/benchmarks/INDEPENDENCE_AND_LEAKAGE_AUDIT.md), [`research/evaluation/BASELINE_IMPLEMENTATION_AND_FAIRNESS.md`](research/evaluation/BASELINE_IMPLEMENTATION_AND_FAIRNESS.md), [`research/literature/RELATED_WORK_COMPARISON.md`](research/literature/RELATED_WORK_COMPARISON.md).

## 23. History

V1 to V6 (static and dynamic behavioural "genome" distances, AUROC evaluations, withdrawn claims) are documented in [`docs/README_pre_v7b.md`](docs/README_pre_v7b.md), [`docs/VERSION_MAP.md`](docs/VERSION_MAP.md) and [`FINAL_STANFORD_READINESS_REPORT.md`](FINAL_STANFORD_READINESS_REPORT.md). Preserved git tags: `v6-holdout-complete`, `v7-design-package-original`.

## 24. Acknowledgements

None are claimed. The development history shows work by the repository owner assisted by AI coding agents; the independent red-team review in `reports/final/` was also produced by an AI reviewer, not by an external human reviewer.
