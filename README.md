# SBG V7-B: an evidence contract for differential execution of code changes

**Status: exploratory research prototype. Branch `research/v7b-final-validation`. No confirmatory result exists. Phase 2 (local, macOS, existing data only) is complete; Phase 3 (Linux isolation, independent data) has not been started.**
The previous README (V5/V6-era claims) is kept unchanged at [`docs/README_pre_v7b.md`](docs/README_pre_v7b.md). Its numbers (for example AUROC 0.897) are about a different method (V5/V6 behavioural distance), were measured on developer-authored benchmarks, and are **not** results of V7-B.

---

## 1. Positioning

V7-B is a small Python tool plus an evaluation harness. Given two versions of a Python function and a set of inputs, it runs both in isolated child processes and reports one of three verdicts, each backed by a replayable evidence record:

- `DIVERGENT_OBSERVABLE`: a replay-confirmed input on which the two versions differ in an observed channel (a witness).
- `INSUFFICIENT(reason)`: the tool refuses to conclude.
- `NO_DIVERGENCE_OBSERVED(S1|S2)`: no difference was seen on the inputs tried, plus a sufficiency level describing how much of the changed code those inputs reached.

It is positioned as a **design and feasibility study with a negative-result flavour**, not as a validated detector. An independent red-team review ([`reports/final/INDEPENDENT_RED_TEAM_REVIEW.md`](reports/final/INDEPENDENT_RED_TEAM_REVIEW.md)) rated it "publishable only as a design/feasibility/negative-result report; not ready as a validation paper", and nothing in this repository contradicts that.

## 1a. What V7-B claims and does not claim (Phase 2 state)

**Claims (all local, exploratory, on 321 non-pristine development pairs, macOS only):**
- The tool issues a closed set of verdicts, none of which means equivalence, and each verdict can be recomputed offline from its evidence log (`python -m sbgv7 verify DIR`).
- On the 258 labelled pairs, V7-B had a lower false-assurance rate than plain differential testing (B1) (the 0/152 false-alarm figure is a harness artefact, not a result: B1 treats renamed entry points as differences and V7-B abstains on them). The whole reduction is explained by abstention (`INSUFFICIENT`), not by detecting more.
- The harness ran every driven pair without an engine failure, and its verdicts were reproduced across two independent runs (321/321 strict identity, E1 versus E3).

**Does NOT claim:** independent generalisation; that `NO_DIVERGENCE_OBSERVED` means equivalence, safety or "no bug"; operating-system isolation or a secure sandbox for untrusted code; tamper-proof evidence (the plaintext hash chain is forgeable by anyone who can recompute it); complete or hash-order-robust determinism; superiority over, or comparison with, any published tool (none was run); that thresholds are calibrated; any Linux, Docker or cross-language result; novelty ("first", "state of the art").

### Verdict meanings (short; the guide is [`docs/VERDICT_INTERPRETATION.md`](docs/VERDICT_INTERPRETATION.md))
`DIVERGENT_OBSERVABLE` = a replay-confirmed input differs on an observed channel (not "a bug"). `INSUFFICIENT(reason)` = the tool declines; the reason names the highest-ranked blocker. `NO_DIVERGENCE_OBSERVED(S1|S2)` = nothing differed on the inputs tried and the changed lines were exercised to that level; it never means equivalence.

### Phase 2 results in brief (exploratory, non-pristine, 2026-11-18)
Full tables: [`reports/phase2/PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md`](reports/phase2/PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md). Compact outputs: [`results/v7b_phase2_summary/`](results/v7b_phase2_summary). Engine commit `a6afa639` (implementation `5efcef74`), CPython 3.13.15, macOS arm64.

| Exp | Headline (exact) | Status |
|---|---|---|
| E1 K2 determinism | pairs with a QUARANTINED input 1 versus 2 of 312 (inputs 1 versus 3 of 3,044); verdict "supported (weak)": no rise observed | confounded by other engine changes; tiny counts; hash-order not tested |
| E3 detection / false assurance / abstention (106 divergent, 152 other, 258 labelled) | V7-B false assurance 13/106 = 0.123 versus B1 24/106 = 0.226 (-10.4pp, 95% CI [-20.5, -4.3], Holm p = 0.0059; the +10pp rule is **not** met); detection 0.708 versus 0.774 (Holm p = 0.156, not significant); abstention 122/258 = 0.473; false alarm 0/152 versus 0.303 | exploratory; **the false-assurance reduction is entirely abstention** (11 of 11 recovered pairs are `INSUFFICIENT`; V7-B detects nothing B1 misses) |
| E4 ablations | no verdict value or level changes under any of 5 component ablations (one reason code moved) | the data hold almost no nondeterminism, so this cannot show component value |
| E5 S2 floor 0.6/0.8/0.9 | verdict values identical; S2 share 71/55/43 | the floor only relabels S1/S2 |
| E6 runtime (40 pairs x 5 reps) | V7-B about 1.6x B1 (wall), about 1.02x B1+rep | machine on battery, load rule tripped, run twice |
| E7 verification | 828/828 evidence directories verified; 42/42 corruption cases as pre-registered | `verify` recomputes recorded facts and executes nothing; forged-and-rechained logs pass by design |

Abstention rose from 0.360 (pre-Phase-2 engine) to 0.473 because 54 pairs now return `INSUFFICIENT(unmodelled_change)`: changed lines with no executable code (for example continuation lines of multi-line statements) are treated conservatively. Part of this may be noise of an unrefined rule. Witness ids near a resource limit can depend on timing (one pair differed between runs; its verdict did not).

**Deferred to Phase 3 (not done, no claim):** Linux/Docker isolation, K1 (>= 100 runnable real pairs, >= 8 projects), K5 (>= 60 projects, >= 250 adjudicated divergent pairs, kappa >= 0.7), an independent sealed holdout, comparison with published tools, hash-order sensitivity (E2), a trust anchor for the evidence log, refinement of `unmodelled_change`.

## 2. Overview

| | |
|---|---|
| Input | two `.py` files, the name of one top-level function, a JSON list of arguments, an optional JSON config |
| Output | `verdict.json` and a hash-chained `evidence.jsonl` in an output directory |
| Isolation | fresh child process per run under macOS `sandbox-exec` (network and writes denied, rlimits) |
| Scope | top-level Python functions with JSON-representable arguments, CPython 3.13, macOS |
| Evaluation | 321 development pairs from QuixBugs, BugsInPy units and synthetic transformations, all **non-pristine** |
| Code | [`sbgv7/`](sbgv7) (about 1,560 lines); V5/V6 code (`sbg/`, `sbgv6/`) is untouched |

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
tests/v7/              V7-B tests (see section 15 for counts)
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

**The table and figures below are the pre-Phase-2 (post-red-team-fix) run of the OLD engine, kept as history.** The current engine's numbers are in section 1a and in `results/v7b_phase2_summary/` (for example abstention 0.473, not 0.360). Do not mix the two.

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

Run (macOS, `.venv`, nothing else running: `test_no_stray_processes` inspects the process table):

```bash
.venv/bin/python -m pytest tests/v7 -q              # V7-B tests only
.venv/bin/python -m pytest tests/v7 tests/v6 -q     # the set used for the Phase 2 E3 run
.venv/bin/python -m pytest tests/v7/test_second_stage.py -q -k tamper_proof   # wording guard for docs/architecture
```

Recorded results (each number names its suite; none was re-run for this README):

| Suite | Result | Where recorded |
|---|---|---|
| `tests/v7` alone | 276 passed, 1 skipped (277 tests; the skip is the `RLIMIT_AS` test, unenforceable on macOS) | `reports/phase2/MB_SECOND_STAGE_REVIEW.md`, at `5efcef74`; `git diff 5efcef74 HEAD -- sbgv7 tests` is empty, so this is the count for HEAD sources |
| `tests/v7` + `tests/v6` | 286 passed, 1 skipped (`tests/v6` contributes 10) | tests stage of the E3 run, `results/v7b_phase2_summary/p2_e3_20261118_092700/E3_COMMANDS.sh` and `run.log` |
| all of `tests/` (`pytest tests -q`, legacy V5/V6 included) | **not completed**: killed after more than 77 CPU-minutes without finishing in the Phase 2 campaign (an earlier attempt was stopped after 13 minutes) | `reports/phase2/PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md` section 9 |

Older counts in other documents (74, 75, 85, 91, 168, 261) describe earlier states and are superseded; see [`docs/DOCUMENTATION_RECONCILIATION_INDEX.md`](docs/DOCUMENTATION_RECONCILIATION_INDEX.md). The tests exercise sandboxed subprocesses; `test_no_stray_processes` fails if another V7-B run is active. A pass count is not evidence that the engine is correct on real code.

## 16. Reproducing

**Phase 2 workflow (one sequence; full commands in [`docs/PHASE2_REPRODUCTION_GUIDE.md`](docs/PHASE2_REPRODUCTION_GUIDE.md), pre-registration in [`docs/EXPERIMENT_PROTOCOL.md`](docs/EXPERIMENT_PROTOCOL.md)).** Always write to NEW directories under `results/repro/` (gitignored); never overwrite `results/raw`, `results/postfix` or `artifacts/`. Run one experiment at a time with nothing else CPU-heavy running. macOS required.

1. E1 (about 16 min): `K1_RAW=results/repro/p2_e1_NEW/raw K1_PROC=results/repro/p2_e1_NEW/proc .venv/bin/python experiments/v7b/k1_spike.py run`, then `summarize` with the same variables, then `.venv/bin/python scripts/e1_analyze.py ...` and `python -m sbgv7 verify` on every evidence directory.
2. E3 (long): do **not** use `scripts/run_evaluation.sh --full` as is. Its first stage is the legacy `pytest tests -q`, which took more than 77 CPU-minutes in the Phase 2 campaign without finishing (unrelated V5/V6 tests). Use the manual stage sequence recorded in `results/v7b_phase2_summary/p2_e3_20261118_092700/E3_COMMANDS.sh`: `pytest tests/v7 tests/v6`, `k1_spike.py run/summarize`, `sbgv7.baselines.run run/summarize`, `build_dev_pairs_csv.py`, `analyze_results.py ... --reference B1 --seed 42 --boot 10000`, `power_actual.py`, `generate_figures.py`.
3. E4 and E5: `experiments/v7b/p2_variants.py run --variant V0..V5 / S2F06,S2F08,S2F09`, then `p2_variants.py csv` and `analyze_results.py` (commands in the protocol).
4. E6: `scripts/p2_e6_runtime.py records|select|timing`. E7: `scripts/p2_e7_verify.py run`. Consolidation: `scripts/p2_consolidate.py build`.

Smaller entry points (not comparable with committed results):

```bash
scripts/run_evaluation.sh --dry-run   # preflight and plan only
scripts/run_evaluation.sh --quick     # tests/v7 + tests/v6 + QuixBugs-only pipeline
scripts/run_evaluation.sh --full      # all 321 pairs; the first stage is the very slow legacy pytest (see above)
```
Output goes to `results/repro/<mode>_<timestamp>/`; committed results are never overwritten. See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md), [`research/reproducibility/REPRODUCIBILITY_PROTOCOL.md`](research/reproducibility/REPRODUCIBILITY_PROTOCOL.md) and [`datasets/README.md`](datasets/README.md).

**Verifying evidence.** `python -m sbgv7 verify DIR` re-reads `DIR/evidence.jsonl`, checks the hash chain and content ids, recomputes per-input outcomes, changed regions, sufficiency and the verdict from the stored runs and sources, and compares them with the recorded verdict. Exit 0: verified; 1: mismatch or inconsistency detected; 2: unreadable, missing or malformed; 4: evidence omitted by a size cap (not recomputable). It does **not** re-execute anything, so it cannot detect a false recorded observation; it does **not** detect a writer who recomputes the whole chain and `log_head` (the plaintext chain is not tamper-proof); a deleted `verdict.json` is not detected. A trust anchor (pinned `log_head` or an external signature) is Phase 3. `compare` exits 0 (verdict written; read `verdict.json`), 1 internal error, 2 usage/config/output error, 3 `ineligible:identical`.

**Where results are.** Compact tracked summaries: [`results/v7b_phase2_summary/`](results/v7b_phase2_summary) (index in its `README.md`). Raw per-run evidence (about 470 MB, about 27,000 files) is not in git: it is in tar.gz archives at `~/Desktop/SBG-V6-phase2-raw-archive/` on the author's machine, with sha256 sums in `results/v7b_phase2_summary/RAW_ARCHIVE_SHA256SUMS.txt`, and in gitignored `results/repro/p2_*`. Historical `results/postfix/` (old engine) is superseded by these for every number about the current engine.

## 17. Figures and manuscript

- Data figures (PDF and PNG, generated from `results/` by `scripts/generate_figures.py`): [`results/postfix/figures/`](results/postfix/figures) (current); `results/figures/` holds superseded pre-fix versions. Exploratory data only.
- Diagram sources, **not rendered** (no `dot` installed): [`paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/figures/`](paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/figures); register: [`FIGURE_AND_TABLE_REGISTER.md`](paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/FIGURE_AND_TABLE_REGISTER.md).
- Manuscript: [`paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/`](paper/IEEE_ACCESS_INITIAL_MANUSCRIPT) (`main.tex`, see its [`README.md`](paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/README.md)). **Draft: never compiled (no LaTeX toolchain here), not peer reviewed, exploratory.** Do not cite it.

## 18. Limitations

- **macOS only.** Isolation is `sandbox-exec` (deprecated by Apple). Reads are not confined, a `setsid()` child escapes the group kill (untested), `RLIMIT_AS` and `RLIMIT_NPROC` are not enforced (memory cap is parent polling). Every record carries `policy_below_minimum=true`. This is not a mechanism for running untrusted code.
- **No Linux or container verification**: not implemented, not tested (Docker daemon was down).
- **No LaTeX compile**: manuscript unbuilt.
- **Not implemented**: S3, the explorer / input generation, module E (`internal_divergence`), declared renames, generator and class entries, supersession, calibration, gates K1 to K5. Spec reason codes never produced: `ambiguous_entry`, `blind_spot_dominant` (`unmodelled_change` and `unsafe_program` are produced since Phase 2). A flat Merkle-style `run_set_root` exists in the sufficiency record; there is no Merkle domain separation.
- **Exploratory only**: 321 non-pristine pairs; V7-B was shaped by them; no independent labels; synthetic labels are known to be wrong in places; BugsInPy runs are function units on a synthetic battery.
- **Determinism is partial.** Children run with `PYTHONHASHSEED=0` (fixed: hash-order sensitivity is untested), `TZ=UTC`, one thread. `datetime.now()` and `secrets` are not virtualised (wall-clock programs can produce false witnesses); control alternation virtualises `time`, monotonic clocks and `random`/`os.urandom` seeding, and relies on the private `random._urandom` attribute. Not claimed: complete determinism.
- **Evidence is not tamper-proof.** A plaintext SHA-256 chain detects accidental corruption and inconsistent edits only. `verify` re-derives, never re-executes.
- **Pair id depends on the policy record** (`pair_id` includes the isolation policy id), so the same pair gets different ids on different hosts or policies.
- **Result-channel protocol correctness is not isolation.** The harness runs in the same process as the evaluated code; no operating-system isolation is claimed or validated. Isolation is macOS-only and every record carries `policy_below_minimum=true`.
- **`unmodelled_change` abstention noise.** 54 pairs abstain under a conservative rule that is unrefined for continuation lines of multi-line statements (UD-2 open).
- **Witness id near resource limits is timing-dependent** (one E4 pair); verdicts were unchanged.
- **Phase 2 results are exploratory:** same 321 pairs that shaped the tool; project clusters (one project holds most QuixBugs pairs); synthetic labels not adjudicated; B3/B4 tuned on development rows.
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

[`docs/PHASE2_REPRODUCTION_GUIDE.md`](docs/PHASE2_REPRODUCTION_GUIDE.md), [`docs/EXPERIMENT_PROTOCOL.md`](docs/EXPERIMENT_PROTOCOL.md), [`docs/DATASET_PROVENANCE.md`](docs/DATASET_PROVENANCE.md), [`docs/FAILURE_MATRIX.md`](docs/FAILURE_MATRIX.md), [`docs/VERDICT_INTERPRETATION.md`](docs/VERDICT_INTERPRETATION.md), [`docs/CHANGELOG_V7B.md`](docs/CHANGELOG_V7B.md), [`docs/DOCUMENTATION_RECONCILIATION_INDEX.md`](docs/DOCUMENTATION_RECONCILIATION_INDEX.md), [`reports/final/V7B_FROZEN_SPEC.md`](reports/final/V7B_FROZEN_SPEC.md), [`reports/final/P0_FINAL_RECONCILIATION_REPORT.md`](reports/final/P0_FINAL_RECONCILIATION_REPORT.md), [`research/security/THREAT_MODEL.md`](research/security/THREAT_MODEL.md), [`research/security/EXECUTION_ISOLATION_AUDIT.md`](research/security/EXECUTION_ISOLATION_AUDIT.md), [`research/benchmarks/INDEPENDENCE_AND_LEAKAGE_AUDIT.md`](research/benchmarks/INDEPENDENCE_AND_LEAKAGE_AUDIT.md), [`research/evaluation/BASELINE_IMPLEMENTATION_AND_FAIRNESS.md`](research/evaluation/BASELINE_IMPLEMENTATION_AND_FAIRNESS.md), [`research/literature/RELATED_WORK_COMPARISON.md`](research/literature/RELATED_WORK_COMPARISON.md).

## 23. History

V1 to V6 (static and dynamic behavioural "genome" distances, AUROC evaluations, withdrawn claims) are documented in [`docs/README_pre_v7b.md`](docs/README_pre_v7b.md), [`docs/VERSION_MAP.md`](docs/VERSION_MAP.md) and [`FINAL_STANFORD_READINESS_REPORT.md`](FINAL_STANFORD_READINESS_REPORT.md). Preserved git tags: `v6-holdout-complete`, `v7-design-package-original`.

## 24. Acknowledgements

None are claimed. The development history shows work by the repository owner assisted by AI coding agents; the independent red-team review in `reports/final/` was also produced by an AI reviewer, not by an external human reviewer.
