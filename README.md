# Software Behavior Genome (SBG)

[![CI](https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation/actions/workflows/ci.yml/badge.svg)](https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

Can you tell whether a code change altered what a program *does*, without
looking at what it outputs?

SBG builds a behavioural representation from execution traces — call-graph
topology, call-order bigrams, exception structure, temporal patterns, abstract
value-state transitions — and scores the distance between two versions of a
program. The representation never reads return values, printed output, expected
outputs or labels. The point of that constraint is to rule out a trivial
solution: a method that "detects behavioural change" by comparing outputs has
not learned anything about behaviour.

**This release is a correction.** An earlier version of this README reported
results that the evidence does not support. What follows replaces them, and the
withdrawn claims are listed below rather than quietly removed.

---

## The short version

- **One claim is strongly supported: execution beats structure.** On the
  strongest arm, a structural AST baseline scores AUROC **0.105** on the same
  pairs where the execution-based distance scores **0.601** — a gap of +0.50,
  Holm-corrected p = 0.006. Structural similarity is not merely uninformative
  here, it is *anti*-correlated with semantic equivalence: the
  semantics-preserving transformations rewrite the source heavily while the
  semantics-changing mutations alter one operator. That inversion is exactly what
  the project set out to address, and it holds in all three evaluation arms.
- **The rest is weak.** SBG V5's 0.601 [0.490, 0.706] comes from 259 pairs over 7
  programs and sits above the 0.551 label-shuffle noise floor, but it is not
  distinguishable from any cheap execution statistic — not `exception_fraction`,
  not `call_count`, not the V3 distance it was meant to improve on. On the
  *published* benchmark under the same protocol it falls to 0.565, and to 0.502 —
  chance — over every pair it can evaluate.
- **The published evaluation was measuring something else.** Its entry-point
  discovery traced each program's own `test_*` self-test driver, so the
  "output-free" exception features were recording whether the program's unit
  tests passed. Removing that leak costs about 0.08 AUROC (0.640 → 0.565 on the
  same pairs), which is larger than every effect the paper claimed.
- **40% of the benchmark's positive labels were false.** Mutations were being
  placed in code the evaluation never executes. Repairing the benchmark moves
  every method by ~0.09 AUROC, in the same direction, which is why the
  aggregate number was never about the representation.
- A **corrected protocol**, a **repaired benchmark**, corrected statistics and a
  CI gate that keeps the numbers and the prose in agreement are all included.

If you are here to check whether the claims are real, start with
[`docs/current/EVALUATION_PROTOCOL.md`](docs/current/EVALUATION_PROTOCOL.md) and
[`FINAL_STANFORD_READINESS_REPORT.md`](FINAL_STANFORD_READINESS_REPORT.md).

---

## Claims withdrawn in this release

| Previously reported | Actually |
|---|---|
| Hard negatives: **12/12**, labelled "Behavioral oracle" | That is an output comparison. SBG V5 scores 5/12 at the pre-fixed threshold |
| Regression detection: **14/15**, labelled "Behavioral oracle" | Also an output comparison. SBG V5 scores 7/15 |
| Silent bugs: **9/9 detected** | SBG V5 detects 3/9; the output-reading reference detects 9/9 |
| Benchmark of **3,777 pairs** over **99 programs** | 3,577 pairs over 60 assigned programs (64 files on disk) |
| Main AUROC over **744 test pairs** | Computed over the 643 that executed. All 101 failures are now categorised |
| `exception_fraction` alone (0.593) beats SBG | 0.593 is the V3 exception *component* (two features), not `exception_fraction` (0.567). And under the published protocol neither is a shortcut — both read a leaked output oracle |
| **516 tests** | The suite has grown; `make test` prints the count |
| `make reproduce` "verifies reproducibility" | It compared hashes of committed files. Verification and reproduction are now separate targets |

`experiments/final/consistency_check.py` fails the build if any of these
reappears in a current document.

---

## What went wrong, and how it was found

### The output-free constraint was violated by the protocol, not the code

Entry-point discovery falls back to the call-graph root — documented as "the
function not called by any other module-level function". In this corpus that is
each program's own `test_*` self-test driver: a driver calls everything, and
nothing calls it.

Tracing a self-test driver puts its `assert` statements inside the traced
region. A mutant that breaks an assertion raises `AssertionError` there, and
that lands in `exception_type_set` and `exception_rate`. Those features then
encode *whether the program's own unit tests passed*.

The earlier safeguard audit reported 9/9 checks passing, and its checks were
correct as far as they went: no SBG code path reads a return value. It did not
examine what was being executed.

The audit is static, deterministic, and executes nothing:
`experiments/final/output_oracle_leak_audit.py`.

### 40% of the positive labels were false

Mutation sites were collected with `ast.walk`, which is breadth-first. Module-
level statements are visited before anything nested, so site 0 — the site every
generated variant used — lands on scaffolding: the module docstring, the
`if __name__ == '__main__'` guard, or a `test_*` driver. The result is a pair
labelled CHANGED whose two programs behave identically when the entry function
runs.

180 variants had `__main__ ==` mutated to `!=`, which makes the file execute its
own test driver on import; 22 of those crash while loading, which is part of why
101 test pairs never reached the evaluation.

### 103 variants did not compile

SP-3 could emit `return None` at module or class scope. Its `validate()` used
`ast.parse`, which *accepts* a module-level `return` — only the compiler rejects
it — so the corrupt variants passed validation and were silently dropped later.

### The confidence interval was not the one described

`artifacts/v5/B07/results_test.json` records
`"bootstrap": "cluster_by_base_program"`, but `baselines/v5/b07_dynamic_v5.py`
calls `bootstrap_auroc_ci` without `pair_ids`, which takes the pair-level
branch. 744 pairs come from 13 programs; resampling pairs understates the
uncertainty. Permutation p-values could also be exactly 0, which a Monte Carlo
test cannot support.

`sbg/statistics.py` replaces all of it: clustered bootstrap, within-cluster
permutation with the (b+1)/(m+1) estimator, a paired clustered bootstrap for
differences between predictors, Wilson intervals for the small detection-rate
denominators, and Holm correction. The old module is left untouched so the
published artifacts stay reproducible.

### Two tracer defects

A timed-out worker thread left the process-global `sys.stdout` hijacked, so
every later write by the host vanished into a dead thread's buffer — which
silently swallowed the harness's own progress output and made a running job look
hung. And timed-out workers accumulated: a mutant that loops forever left one
unkillable thread per input per run, competing for the GIL with everything
traced afterwards. Both are fixed and covered by
`tests/test_tracer_isolation.py`.

---

## Results

Every number below is generated from an authoritative artifact by
`experiments/final/make_tables.py`. None is typed by hand, and CI fails if the
block drifts from the artifacts.

<!-- BEGIN GENERATED RESULTS -->
<!-- Generated by experiments/final/make_tables.py. Do not edit by hand; run `make tables`. -->

### Main benchmark

Test split: **744** nominal pairs over 13 programs. **643** executed under the published protocol; **520** of those also pass the static benchmark-validity audit. All three denominators are reported because the published result quoted the first and computed the second.

AUROC, tie-aware; interval is a cluster bootstrap resampling base programs (the unit of independence), not pairs.

| Predictor | evaluated (n=643) | statically valid (n=520) |
|---|---|---|
| `sbg_v5` | 0.546 [0.494, 0.617] | 0.640 [0.577, 0.706] |
| `sbg_v3` | 0.553 [0.498, 0.627] | 0.648 [0.580, 0.717] |
| `exception_component_v3` | 0.602 [0.557, 0.648] | 0.689 [0.626, 0.743] |
| `exception_fraction` | 0.577 [0.532, 0.624] | 0.636 [0.561, 0.704] |
| `call_count` | 0.576 [0.529, 0.630] | 0.662 [0.598, 0.720] |
| `combined_shortcut` | 0.556 [0.503, 0.622] | 0.650 [0.587, 0.709] |
| `static_ast` | 0.432 [0.389, 0.477] | 0.437 [0.397, 0.482] |
| `static_token` | 0.376 [0.335, 0.429] | 0.378 [0.335, 0.442] |

Label-shuffle noise floor on the valid set: **0.566** (95th percentile over 500 within-cluster shuffles). An AUROC below that is not evidence of signal.

Paired comparisons on the valid set (paired cluster bootstrap, Holm-corrected). Overlapping marginal intervals are not a test of a difference.

| SBG V5 versus | ΔAUROC | 95% CI | p (Holm) | significant |
|---|---:|---|---:|---|
| `exception_fraction` | +0.004 | [-0.053, 0.084] | 0.9335 | no |
| `exception_component_v3` | -0.049 | [-0.073, -0.016] | 0.0300 | yes |
| `call_count` | -0.022 | [-0.039, 0.000] | 0.1639 | no |
| `combined_shortcut` | -0.010 | [-0.020, 0.005] | 0.2739 | no |
| `sbg_v3` | -0.008 | [-0.016, -0.000] | 0.1639 | no |
| `static_ast` | +0.204 | [0.113, 0.299] | 0.0060 | yes |

Pairs that could not be executed, by cause — none is discarded:

| Cause | Pairs |
|---|---:|
| `base:no_entry_function` | 58 |
| `variant:import_error` | 22 |
| `variant:no_entry_function` | 3 |
| `variant:syntax_error` | 18 |

### Same benchmark, output-free protocol

Entry-point discovery excludes self-test drivers and inputs are synthesised from parameter annotations, so no assertion is traced. Programs whose signatures cannot be supplied from the fixed input battery are out of scope by a static rule applied identically to every predictor, which is why the denominator falls.

**378** of 744 pairs executed; **294** are statistically valid.

| Predictor | evaluated | statically valid |
|---|---|---|
| `sbg_v5` | 0.502 [0.466, 0.547] | 0.565 [0.489, 0.639] |
| `sbg_v3` | 0.515 [0.485, 0.544] | 0.564 [0.500, 0.622] |
| `exception_component_v3` | 0.529 [0.490, 0.574] | 0.578 [0.510, 0.640] |
| `exception_fraction` | 0.516 [0.484, 0.559] | 0.551 [0.493, 0.615] |
| `call_count` | 0.493 [0.471, 0.514] | 0.524 [0.478, 0.584] |
| `combined_shortcut` | 0.498 [0.478, 0.517] | 0.562 [0.513, 0.612] |
| `static_ast` | 0.395 [0.352, 0.439] | 0.408 [0.367, 0.461] |
| `static_token` | 0.351 [0.315, 0.416] | 0.363 [0.331, 0.434] |

### Corrected benchmark, output-free protocol

The strongest arm: no leaked test oracle and no mislabelled pairs. Same programs and same splits as the published benchmark, regenerated with the transformation operators fixed.

**259** of 488 pairs executed. Every executed pair is statistically valid, because the corrected generator rejects uncompilable and unobservable candidates at generation time.

| Predictor | AUROC | 95% CI | p (within-cluster permutation) |
|---|---:|---|---:|
| `sbg_v5` | 0.601 | [0.490, 0.706] | 0.0005 |
| `sbg_v3` | 0.599 | [0.500, 0.675] | 0.0010 |
| `exception_component_v3` | 0.659 | [0.551, 0.742] | 0.0005 |
| `exception_fraction` | 0.618 | [0.520, 0.700] | 0.0005 |
| `call_count` | 0.565 | [0.463, 0.682] | 0.0020 |
| `combined_shortcut` | 0.583 | [0.491, 0.671] | 0.0045 |
| `static_ast` | 0.105 | [0.066, 0.157] | 1.0000 |
| `static_token` | 0.169 | [0.130, 0.224] | 1.0000 |

Label-shuffle noise floor: **0.551**; SBG V5 sits above it. With 7 programs, the paired comparisons (Holm-corrected) split cleanly:

| SBG V5 versus | ΔAUROC | 95% CI | p (Holm) | significant |
|---|---:|---|---:|---|
| `exception_fraction` | -0.017 | [-0.056, 0.035] | 1.0000 | no |
| `exception_component_v3` | -0.057 | [-0.097, 0.004] | 0.3598 | no |
| `call_count` | +0.036 | [-0.085, 0.168] | 1.0000 | no |
| `combined_shortcut` | +0.019 | [-0.022, 0.069] | 1.0000 | no |
| `sbg_v3` | +0.003 | [-0.023, 0.045] | 1.0000 | no |
| `static_ast` | +0.497 | [0.361, 0.614] | 0.0060 | yes |

SBG beats `static_ast` and is not distinguishable from `call_count`, `combined_shortcut`, `exception_component_v3`, `exception_fraction`, `sbg_v3`.

### Where the representation was claimed to win

Both rows below were reported in an earlier README as SBG results. They are output comparisons. The SBG figures are the corrected ones.

| Task | SBG V5, output-free | Output-reading reference |
|---|---|---|
| Hard negatives, 12 pairs (canonical inputs) | **5/12** | 12/12 |
| Hard negatives, 12 pairs (declared inputs) | **5/12** | 12/12 |
| Regression corpus, 15 bug/fix pairs | **7/15** | 13/15 |
| Silent bugs (invisible to exception and volume shortcuts) | **3/9** | 9/9 |

Decision threshold τ* = 0.08, fixed in advance and not re-tuned.

### Why the published comparison does not mean what it said

The published protocol's entry-point discovery returns the call-graph root, which in this corpus is each program's own `test_*` self-test driver. Tracing it puts the driver's `assert` statements inside the traced region, so the exception features record whether the program's own tests passed.

| | |
|---|---:|
| Corpus programs | 64 |
| Entry function is a self-test driver | 47 |
| `assert` statements inside traced regions | 611 |
| Programs where the canonical inputs never execute | 49 |

### Benchmark

**3577** pairs over **60** programs (64 files on disk; 4 take part in no experiment). All six split intersections empty.

The published benchmark carries three defects, all measured statically:

| Defect | Test split | All splits |
|---|---:|---:|
| Variants that do not compile | 20 | 103 |
| CHANGED pairs whose mutation the entry function cannot reach | 135 of 366 | 785 |
| Pairs with no discoverable entry function | 56 | 118 |

`benchmark/datasets/v6/` regenerates the benchmark with the operators fixed: **2340** pairs, 0 uncompilable, 0 unobservable, same programs and same splits (test: 488 pairs, 13 programs).

<!-- END GENERATED RESULTS -->

### Reading these numbers

**The two protocols answer different questions.** The published protocol traces
self-test drivers, so its exception features carry the programs' own assertions.
Its 0.640 on the valid set is therefore an upper bound contaminated by an output
oracle, not an output-free result. The output-free protocol removes the
contamination and the same predictor on the same pairs falls to 0.565. That
0.075 gap is the size of the leak.

**On the output-free protocol the result is weak and equivocal.** Over the 378
evaluable pairs of the published benchmark SBG V5 sits at 0.502 — chance. Over
the 294 statistically valid pairs it reaches 0.565; the within-cluster
permutation test rejects the null (p = 0.004) but the clustered bootstrap
interval still includes 0.5, and the two disagreeing is what a genuinely
marginal effect looks like with 7 programs.

**Repairing the benchmark is what recovers the signal.** On the corrected
benchmark under the same output-free protocol, SBG V5 reaches 0.601 with
permutation p < 0.001, above the noise floor. That arm is the one to judge the
method on: it has neither the leaked test oracle nor the mislabelled positives.

**Against structure, the margin is decisive; against execution statistics, there
is none.** The structural AST baseline scores 0.105 and the token baseline 0.169
on those same 259 pairs. SBG beats both by a margin no sample this small could
produce by chance (ΔAUROC +0.50, Holm p = 0.006). But `exception_component_v3`
(0.659) and the state genome alone (0.635) both score *higher* than the full V5
distance, and no comparison against any execution-derived reference is
significant. The supportable statement is that executing a program tells you
something reading it does not — not that this particular representation of the
execution is the right one.

**The benchmark defect moved every method equally.** The jump from ~0.55 on the
evaluable set to ~0.64 on the valid set under the published protocol is not
about SBG: a mislabelled positive and a trivially-equal negative both produce
distance exactly 0, so the invalid pairs pile both classes onto the same tie and
drag every predictor toward 0.5.

**The distance formula loses to its own parts.** SBG V5 scores below `sbg_v3`
and below its temporal and state components on the published protocol. A
fixed-weight combination that underperforms its components is a statement about
the weights, and nobody has fitted them — so "the representation is weak" is not
yet separable from "these weights are wrong". See
[`docs/current/LIMITATIONS.md`](docs/current/LIMITATIONS.md).

---

## Claim strength

| Claim | Status |
|---|---|
| Execution-grounded comparison beats structural comparison | **Supported** — ΔAUROC +0.50 over a static AST baseline on the corrected benchmark, Holm p = 0.006; significant in all three evaluation arms |
| Structural similarity is anti-correlated with semantic equivalence on this benchmark | **Supported** — static AST AUROC 0.105, static token 0.169, both far below 0.5 |
| An output-free execution distance separates CHANGED from EQUIVALENT above chance | **Supported on the corrected benchmark** — AUROC 0.601, permutation p < 0.001, above the 0.551 noise floor. On the published benchmark it is 0.565 with a bootstrap interval that includes 0.5, and 0.502 over all evaluable pairs |
| The published protocol violates the output-free constraint | **Supported** — static audit, 47/64 programs, 611 traced assertions |
| 40% of the benchmark's CHANGED labels are unobservable | **Supported** — static audit, 135/336 in the test split |
| SBG V5 beats the cheapest execution statistic | **Not supported** — under the output-free protocol no paired comparison against any reference is significant after Holm correction |
| The multi-dimensional representation adds value over V3 | **Not supported** — ΔAUROC −0.008 under the published protocol, +0.001 under the output-free one; V5 scores below its own temporal and state components |
| SBG detects behavioural change that output comparison misses | **Not supported** — the output-reading reference dominates on every auxiliary benchmark |
| The published 0.593-beats-0.551 comparison shows a shortcut defeating the representation | **Withdrawn** — under a protocol that traces self-test drivers, the exception features are a leaked output oracle, not a shortcut |
| The representation generalises beyond this corpus | **Open** — external corpora not verified in this release |
| The distance formula's weights are the limit rather than the representation | **Open** — a learned combination has not been run |

Nothing here uses "proves", "solves" or "state of the art", because nothing here
would support them.

---

## How it works

```
two versions of a program
        |
        +-- static extraction ----> control, data, error dimensions
        |
        +-- dynamic extraction ---> sys.settrace sandbox, seed 42
                  entry function + fixed input battery
                  |
                  +-- V3: call-transition bigrams, coverage, exception causality,
                  |       input sensitivity, call-depth variance
                  +-- V5: temporal trigrams, phase diversity, loop profiles
                  +-- V5: abstract value-state transitions
                             |
                             +-- distance_v5 = 0.50*d_v3 + 0.25*d_temporal + 0.25*d_state
```

Which function gets executed is part of the method, and getting it wrong is what
this release corrects. Two protocols are implemented and both are runnable:
`published` reproduces the original exactly, `output_free_v6` excludes
self-test drivers and synthesises inputs from parameter annotations. See
[`docs/current/EVALUATION_PROTOCOL.md`](docs/current/EVALUATION_PROTOCOL.md).

---

## Quick start

```bash
git clone https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation.git
cd Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation

python3 -m venv .venv && . .venv/bin/activate
pip install pytest            # the only dependency

make test                     # full test suite
make quickstart               # smoke test, instant
make check                    # verify every committed artifact against its generator
make help                     # all targets, with runtimes
```

`make check` executes no experiment: it re-runs the static audits, rebuilds the
manifest, regenerates every table from the artifacts and diffs them against the
committed copies. To actually re-measure, use a `reproduce-*` target; each one
overwrites its artifact, so a clean `git diff` afterwards means the result
reproduced.

| Target | What it re-measures | Time |
|---|---|---|
| `make reproduce-fast` | hard negatives, regression corpus | ~1 min |
| `make reproduce-v5` | main benchmark, published protocol | ~26 min |
| `make reproduce-output-free` | main benchmark, output-free protocol | ~10 min |
| `make benchmark-v6` | regenerates the corrected benchmark | ~3 min |

Full details, including which results reproduce bit-for-bit and which do not, in
[`docs/current/REPRODUCTION.md`](docs/current/REPRODUCTION.md).

---

## Repository layout

```
sbg/
  extraction/       static and dynamic genome extractors, sys.settrace tracer
  v3/               DynamicGenomeV3 and distance_v3
  v5/               temporal genome, state-transition genome, invariant identity
  statistics.py     corrected AUROC, clustered bootstrap, paired comparison

benchmark/
  corpus/           64 base programs (60 assigned to splits)
  datasets/         the published benchmark: 3,577 pairs, frozen
  datasets/v6/      the corrected benchmark: 2,340 pairs, same programs and splits
  transformations/  12 semantics-preserving + 14 semantics-changing operators
  scripts/          benchmark generation, validity audit, manifest
  benchmark_manifest.json    authoritative counts for everything

experiments/final/  the V6 evaluation pipeline
  protocol.py            entry selection and input synthesis
  extraction.py          one shared execution pass per program
  run_main_evaluation.py raw per-pair records
  analyse_results.py     metrics over ALL / EVALUABLE / VALID
  make_tables.py         every table and headline number
  consistency_check.py   the integrity gate CI runs

artifacts/final/    authoritative results, with per-pair records
docs/current/       protocol, benchmark, limitations, reproduction
docs/generated/     tables, generated — do not edit
docs/archive/       superseded documents, kept as the record
tests/              statistics, tracer isolation, scientific integrity
```

### Finding your way through the versions

There are six research versions and the earlier ones left behind a `FINAL_*`
document each. None of them is final.
[`docs/VERSION_MAP.md`](docs/VERSION_MAP.md) says which result belongs to which
version and which artifact is authoritative; everything superseded is under
`docs/archive/` and is exempt from the consistency gate precisely because
rewriting it would destroy the record.

---

## Evidence chain

```
source code -> experiment script -> raw per-pair record -> authoritative artifact
            -> docs/generated/*.md -> README / manuscript
```

One source per number. `artifacts/final/ARTIFACT_PROVENANCE.json` classifies
every result file as MEASURED, PARTIALLY_SYNTHETIC, SUPERSEDED, NON_REPRODUCING
or DERIVED, and the gate refuses to let a document cite a non-MEASURED artifact
without saying so. Two files earned those labels the hard way: one carried
`"scores_are_real": true` beside its own note that nine of its ten features were
synthesised from aggregate AUROCs, and one does not reproduce when its own
generator is re-run.

---

## Limitations

The full list is in
[`docs/current/LIMITATIONS.md`](docs/current/LIMITATIONS.md). The ones that bound
every number above:

- **13 programs** in the test split, 7 under the output-free protocol. The unit
  of independence is the program, not the pair, so the intervals are wide and
  nothing generalises beyond programs like these.
- **Synthetic corpus.** Single-file exercises written for this benchmark, each
  with its own self-test. No real-world code.
- **The output-free protocol covers the easier half.** The 23 programs it cannot
  handle are mostly class-based — the ones with state, where a state-transition
  genome should have the most to say.
- **External validation is unverified.** The QuixBugs, BugsInPy and Java results
  in `results/external/` use the same entry-discovery code and are subject to the
  same defect. They were not re-run here and are excluded from every claim above.
- **CPython only.** `sys.settrace` is required. Trace-derived features can shift
  between Python versions; CI runs 3.9 and 3.13.

---

## Citation

```bibtex
@misc{sbg2026,
  title  = {Software Behavior Genome: An Empirical Study of Execution-Grounded
            Behavioral Representations for Semantic Change Detection},
  author = {Manas Sakthivel},
  year   = {2026},
  note   = {Includes a correction of the evaluation protocol and benchmark used
            in earlier versions},
  url    = {https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation},
}
```

## License

MIT — see [LICENSE](LICENSE).
