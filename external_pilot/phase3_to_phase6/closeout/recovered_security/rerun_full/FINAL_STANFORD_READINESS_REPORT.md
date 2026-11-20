# SBG — final readiness report

**Verdict: `BLOCKED — SBG NOT READY` for a publication claim about the
representation. `PASS` as a corrected, reproducible research artifact.**

Two categories of the gate below are BLOCKED and cannot be cleared by further
work inside this repository. Both are stated with what would clear them. The
rest of the gate passes, the numbers are reproducible, and the claims have been
brought back inside the evidence.

---

## Executive conclusion

### What SBG now establishes

**Executing a program tells you something that reading it does not, and the
margin is large.** On the corrected benchmark under the output-free protocol, a
static AST baseline scores AUROC **0.105** and a token baseline **0.169** on
exactly the pairs where the execution-based distance scores **0.601**. The gap
to the AST baseline is **+0.497** [0.361, 0.614], Holm-corrected **p = 0.006**,
and it is significant in all three evaluation arms. Structural similarity here
is not merely uninformative — it is *anti*-correlated with semantic equivalence,
because the semantics-preserving transformations rewrite the source heavily
while the semantics-changing mutations alter one operator or one constant. This
is the inversion the project set out to address, and it is now a measured effect
rather than a motivation.

**The output-free distance carries signal, weakly.** SBG V5 reaches 0.601
[0.490, 0.706] over 259 pairs from 7 programs, above the 0.551 label-shuffle
noise floor, permutation p < 0.001.

### What SBG does not establish

**That this representation is the right one.** SBG V5 is not distinguishable
from any cheap execution statistic: not `exception_fraction` (Δ −0.017,
p_holm = 1.0), not `call_count` (Δ +0.036, p_holm = 1.0), not the V3 distance it
was built to improve on (Δ +0.003, p_holm = 1.0). Two single features —
`exception_component_v3` at 0.659 and the state genome alone at 0.635 — score
*higher* than the full weighted V5 distance.

**That it detects change an output comparison would miss.** On every auxiliary
benchmark the output-reading reference dominates: 12/12 versus 5/12 on the hard
negatives, 13/15 versus 7/15 on the regression corpus, 9/9 versus 3/9 on silent
bugs.

### What the previous release claimed that was wrong

The published evaluation was measuring something other than what it said.

1. **The output-free constraint was violated by the execution protocol.**
   Entry-point discovery falls back to `compute_program_identity`'s call-graph
   root — "the function not called by any other module-level function" — which
   in this corpus is each program's own `test_*` self-test driver. Tracing it
   places the driver's `assert` statements inside the traced region, so
   `exception_rate` and `exception_type_set` encode whether the program's own
   unit tests passed. **47 of 64 programs**, **611 assert statements**, and
   **49 of 64 programs never execute the documented canonical inputs at all**.
   The README's headline reading — that a cheap shortcut beats the full genome —
   does not survive this: under that protocol the "shortcut" is a leaked output
   oracle.

2. **40% of the CHANGED labels were false.** Mutation sites were collected with
   `ast.walk`, which is breadth-first, so site 0 lands on module-level
   scaffolding. **135 of 336** CHANGED test pairs carry a mutation unreachable
   from the entry function. 180 variants across all splits had `__main__ ==`
   mutated to `!=`.

3. **103 variants did not compile.** SP-3 could emit `return None` at module or
   class scope; its `validate()` used `ast.parse`, which accepts a module-level
   `return`. One further file from the same bug sits outside the pair dataset,
   in the V2-era `benchmark/regression/controls/`, and no current experiment
   reads it.

4. **Results were attributed to the wrong method.** 12/12 and 14/15 were output
   comparisons reported under the heading "Behavioral oracle".

5. **Denominators disagreed.** 744 nominal test pairs, 643 evaluated, reported
   as 744.

6. **The confidence interval was not the one described.** The artifact records
   `cluster_by_base_program`; the code took the pair-level branch.

---

## Changes implemented

### Corrections to the measurement

| File | Change |
|---|---|
| `sbg/statistics.py` (new) | Clustered bootstrap, within-cluster permutation with the (b+1)/(m+1) estimator, paired clustered bootstrap for ΔAUROC, Wilson intervals, Holm correction, label-shuffle noise floor. `sbg/v3/metrics.py` left untouched so published artifacts stay reproducible |
| `experiments/final/protocol.py` (new) | `output_free_v6`: entry-point discovery excludes `test_*`, `main`, `demo*` and private names; inputs synthesised from parameter annotations using six fixed batteries; programs whose signatures cannot be supplied are declared out of scope statically |
| `experiments/final/extraction.py` (new) | One shared execution pass per program; every predictor reads the same traces. Failure taxonomy with seven named kinds |
| `sbg/extraction/dynamic/tracer.py` | Host restores `sys.stdout` after every join — an abandoned worker used to leave the process-global stdout hijacked, swallowing all later output. `max_timeouts` added so a non-terminating program stops after N timed-out traces instead of leaking one unkillable thread per input per run. Both default to the previous behaviour |
| `sbg/v2/execution/runner.py` | `timeout_s`, `program_budget_s`, `max_timeouts` passed through; `NONTERMINATING` and `PROGRAM_BUDGET_EXCEEDED` surfaced |

### Corrections to the benchmark

| File | Change |
|---|---|
| `benchmark/transformations/mutations/mutator.py` | `_functional_node_ids` restricts mutation sites to non-scaffolding definitions; `_docstring_node_ids` keeps SC-3 off docstrings |
| `.../preserving/transformations/sp3_dead_code_insert.py` | `return None` template only inside function bodies; `validate()` uses `compile()` |
| `benchmark/scripts/generate_benchmark_v6.py` (new) | Regenerates into `benchmark/datasets/v6/` with three enforced post-conditions: compiles, differs, observable. Same programs, splits and seeds |
| `benchmark/scripts/observability_audit.py` (new) | Static validity audit; never consults a score |
| `benchmark/scripts/build_manifest.py` (new) | `benchmark/benchmark_manifest.json`, the single authoritative count |

### Corrections to the record

| File | Change |
|---|---|
| `experiments/v5/incremental_info_framework.py` | `scores_are_real` is now true only when *every* feature has real per-pair scores; `synthetic_features` and `provenance` added. It used to be true when one of ten did |
| `experiments/external/output_free_audit.py` | Verdict renamed `DISTANCE_FUNCTION_IS_OUTPUT_FREE` with an explicit scope note. Its 9/9 tests the distance function, not the protocol |
| `experiments/final/artifact_provenance.py` (new) | Classifies every result artifact MEASURED / PARTIALLY_SYNTHETIC / SUPERSEDED / NON_REPRODUCING / DERIVED |
| `experiments/final/consistency_check.py` (new) | Eight-check integrity gate |
| `.github/workflows/ci.yml` (new) | Three jobs, no `continue-on-error` |
| `Makefile` | `verify-artifacts` and `reproduce-*` separated; the old `reproduce` only compared hashes |
| `docs/` | 36 superseded documents and four version directories moved to `docs/archive/`; `docs/VERSION_MAP.md`, `docs/current/` and `docs/generated/` added |

---

## Experiments rerun

```bash
make reproduce-v5             # published protocol, 744 test pairs      ~26 min
make reproduce-output-free    # output-free protocol, same pairs        ~20 min
python3 experiments/final/run_main_evaluation.py --split test \
    --protocol output_free_v6 --dataset-dir benchmark/datasets/v6 --tag v6test
make reproduce-fast           # hard negatives + regression corpus      ~1 min
make benchmark-v6             # regenerate the corrected benchmark      ~3 min
make audit                    # static validity + protocol leak audits  ~20 s
```

Every run writes a per-pair JSONL alongside its summary, so a reviewer can
recompute any metric without re-executing anything.

---

## Empirical results

All numbers are from `artifacts/final/`. Tables in `docs/generated/` are
generated from those artifacts and CI fails if they drift.

### Main benchmark, statistically valid pairs

| Predictor | published protocol (n=520, 12 programs) | output-free (n=294, 7) | output-free + corrected benchmark (n=259, 7) |
|---|---|---|---|
| `sbg_v5` | 0.640 [0.577, 0.706] | 0.565 [0.489, 0.639] | **0.601** [0.490, 0.706] |
| `sbg_v3` | 0.648 [0.580, 0.717] | 0.564 [0.500, 0.622] | 0.599 [0.500, 0.675] |
| `exception_component_v3` | 0.689 [0.626, 0.743] | 0.578 [0.510, 0.640] | 0.659 [0.551, 0.742] |
| `exception_fraction` | 0.636 [0.561, 0.704] | 0.551 [0.493, 0.615] | 0.618 [0.520, 0.700] |
| `call_count` | 0.662 [0.598, 0.720] | 0.524 [0.478, 0.584] | 0.565 [0.463, 0.682] |
| `static_ast` | 0.437 [0.397, 0.482] | — | **0.105** [0.066, 0.157] |
| `static_token` | 0.378 [0.335, 0.442] | — | 0.169 [0.130, 0.224] |
| label-shuffle noise floor (p95) | 0.566 | 0.534 | 0.551 |

Removing the leaked test oracle costs 0.075 AUROC (0.640 → 0.565 on the same
pairs). Repairing the benchmark recovers 0.036 (0.565 → 0.601 on comparable
pairs). Both effects are larger than any difference the original paper claimed.

### Paired comparisons, corrected benchmark (Holm-corrected)

| SBG V5 versus | ΔAUROC | 95% CI | p (Holm) | significant |
|---|---:|---|---:|---|
| `static_ast` | +0.497 | [0.361, 0.614] | 0.006 | **yes** |
| `call_count` | +0.036 | [−0.085, 0.168] | 1.000 | no |
| `combined_shortcut` | +0.019 | [−0.022, 0.069] | 1.000 | no |
| `sbg_v3` | +0.003 | [−0.023, 0.045] | 1.000 | no |
| `exception_fraction` | −0.017 | [−0.056, 0.035] | 1.000 | no |
| `exception_component_v3` | −0.057 | [−0.097, 0.004] | 0.360 | no |

### Hard negatives (12 pairs, τ\* = 0.08)

| Method | Reads output | Correct |
|---|---|---|
| SBG V5, output-free (canonical inputs) | no | 5/12 |
| SBG V5, output-free (declared inputs) | no | 5/12 |
| exception component, output-free | no | 5/12 and 6/12 |
| output-reading reference | **yes** | 12/12 |

### Regression corpus (15 bug/fix pairs, τ\* = 0.08)

| Method | Reads output | Detected |
|---|---|---|
| SBG V5, output-free | no | 7/15 |
| SBG V3, output-free | no | 4/15 |
| exception component, output-free | no | 3/15 |
| output-reading reference (full behaviour) | **yes** | 13/15 |
| output-reading reference (return value only) | **yes** | 11/15 |

Silent bugs — invisible to both the exception and the volume shortcut: SBG V5
**3/9**, output-reading reference 9/9.

### Benchmark accounting

| | published | corrected (v6) |
|---|---:|---:|
| programs assigned to splits | 60 | 60 |
| nominal pairs | 3,577 | 2,340 |
| uncompilable variants | 103 | 0 |
| CHANGED but unobservable | 785 | 0 |
| statically valid | 2,571 | 2,302 |
| split intersections empty | yes | yes |

Corpus: 64 files on disk, 60 assigned, 4 unassigned (`err_assert_guard`,
`math_fibonacci`, `sort_insertion_sort`, `str_palindrome`) and named in the
manifest.

---

## Improvements to methodology

1. **Shared execution.** Every predictor is computed from one trace pass, so a
   difference between two predictors is a difference in the feature and not in
   the extraction protocol. Previously the dynamic method used 11 inputs × 5 runs
   at 5000 events while the shortcut controls used a different input set × 3 runs
   at 3000 events.
2. **Three denominators, always reported.** ALL (unevaluable pairs scored at
   distance 0, charging failure to the method), EVALUABLE, VALID.
3. **Static validity filter.** Defined by properties of the source — compiles,
   differs, reachable — never by a score, and applied identically to every
   predictor.
4. **Paired comparisons.** Overlapping marginal intervals are not a test of a
   difference; ΔAUROC now has its own clustered bootstrap and Holm correction.
5. **Clustering respected.** Bootstrap resamples programs; permutation shuffles
   labels within programs.
6. **Structural baselines on the same pairs**, which is what makes the
   execution-beats-structure claim a measurement rather than an assumption.
7. **Declared budgets.** Per-trace timeout, per-program budget and non-termination
   cutoff are fixed constants applied identically to base and variant.

---

## Negative results

- SBG V5 does not beat any execution-derived reference in any arm.
- SBG V5 scores below its own temporal and state components, and below V3. A
  fixed-weight combination that loses to its parts is evidence about the weights,
  which were never fitted.
- The output-reading reference dominates SBG on every auxiliary benchmark.
- Over all 378 evaluable pairs under the output-free protocol, SBG V5 is 0.502 —
  chance.
- `artifacts/v5/REGRESSION_EVALUATION_RESULTS.json` does not reproduce: its own
  generator now gives volume 11/15 where the artifact says 7, and 4 silent bugs
  where it says 8, because one of its features is a wall-clock ratio.

---

## Exclusions

| Exclusion | Count | Rule | Outcome-dependent? |
|---|---:|---|---|
| Corpus programs not assigned to splits | 4 | absent from `split_assignment.json` | no — predates this work |
| Test pairs not executed, published protocol | 101 | 58 base no-entry-function, 22 variant import error, 18 variant syntax error, 3 variant no-entry-function | no |
| Test pairs not executed, output-free protocol | 366 | 337 base signature not synthesisable, 13 import error, 9 syntax error, 4 variant signature, 3 non-terminating | no — static rule on the base program |
| Executed but statically invalid, published | 123 | 135 unobservable CHANGED pairs minus those already unexecutable | no — static |
| v6 generation rejects | 2,340 candidates | 1,992 no-op, 297 unobservable, 51 unanalysable | no — all three are properties of the source |

Every exclusion is listed with its reason in the artifact it affects. The
`ALL` row of every results table scores excluded pairs at distance 0, so a
reader who rejects an exclusion can see the cost of keeping it.

---

## Statistical analysis

| | |
|---|---|
| AUROC | tie-aware Wilcoxon–Mann–Whitney, cross-checked against the independent `sbg.v3.metrics` implementation on 20 random samples |
| Confidence intervals | cluster bootstrap by base program, 2000 resamples, seed 42; degenerate resamples discarded rather than pinned to 0.5 |
| Null test | within-cluster label permutation, 2000 permutations, (b+1)/(m+1) estimator, so the floor is 1/2001 and never 0 |
| Comparisons | paired cluster bootstrap on ΔAUROC, 2000 resamples, two-sided, Holm-corrected across six comparisons |
| Noise floor | 500 within-cluster label shuffles, 95th percentile |
| Detection rates | Wilson score intervals — the normal approximation collapses to zero width at 0/8 |
| Seed | 42 everywhere; all procedures verified deterministic |

Unit of independence is the base program: 12 clusters (published protocol), 7
(output-free). This is what bounds the whole analysis.

---

## Reproducibility

Clean checkout, `python3 -m venv`, `pip install pytest`, then:

| Command | Result |
|---|---|
| `make test` | 602 passed |
| `make quickstart` | runs, prints three distances |
| `make check` | 8/8 consistency checks pass |
| `make reproduce-fast` | re-runs both fast experiments; `git diff` clean |
| `make reproduce-v5` | 643/744 pairs evaluated — the published denominator, reproduced exactly |

The clean-checkout run was done on **Python 3.9.6**, the documented floor, and
it found a real defect that development on 3.13 had hidden: `make_figures.py`
contained a backslash inside an f-string expression, which is a `SyntaxError`
before 3.12. `tests/test_integrity.py::TestSourceCompiles` now compiles every
first-party source file, so the class of bug cannot return silently.

**What does not reproduce bit-for-bit.** The published AUROC of 0.551 comes back
as 0.546 under this harness on CPython 3.13. The tracer reads `frame.f_locals`
on every event, and PEP 667 changed what that returns in 3.13 while 3.12 inlined
comprehensions — both change trace-derived features. CI runs 3.9 and 3.13 for
this reason. The 0.005 difference does not move any conclusion, and it is
reported rather than smoothed over.

**Runtime is honest and uneven.** `make reproduce-v5` takes ~26 minutes, about
half of it on `ds_hash_table` alone: its self-test driver exceeds the 5-second
per-trace budget on every run, so each of its ~58 variants costs ~25 seconds.

---

## Scientific-integrity checks

| Check | Result |
|---|---|
| C1 generated tables match their artifacts | PASS |
| C2 benchmark manifest internally consistent | PASS |
| C3 result denominators agree with the sets | PASS |
| C4 documents cite only MEASURED artifacts | PASS |
| C5 no retired claim in a current document | PASS |
| C6 no output-reading result attributed to SBG | PASS |
| C7 output-free protocol traces no self-test driver | PASS |
| C8 README results block matches the generated tables | PASS |
| Split isolation (6 intersections, variant files, base membership) | PASS |
| Output-free distance function (9 hand-written pairs) | PASS, scope-qualified |
| Tracer isolation regression tests | PASS |
| Full suite | 602 passed |

The gate was verified to fail rather than merely to pass: reintroducing the
retired strings "12/12", "3,777 pairs" and "99 Python programs" into the README
made C5 fail, naming the file, the line and the correct replacement.

---

## Stanford Researcher Gate

| Category | Status | Evidence |
|---|---|---|
| Research question | PASS | "Can an output-free execution representation detect semantic change?" — testable, and the protocol audit shows it had not actually been tested output-free |
| Novelty | PASS | Contribution scoped to: an output-free behavioural distance, and a measured demonstration that structural comparison inverts on semantics-preserving transformations (ΔAUROC +0.50 over a static AST baseline) |
| Methodological rigor | PASS | Shared execution pass; three denominators; static, score-blind validity filter; declared budgets; failure ledger with seven named causes |
| Oracle independence | PASS | Labels come from transformation construction, not from SBG. Output comparison relabelled a reference and reported as a ceiling. The protocol-level leak is removed in the output-free arm and measured in the published one |
| Benchmark quality | **BLOCKED** | Splits are disjoint and the defects are measured and repaired, but the corrected test set is 7 programs and every program is a synthetic single-file exercise written for this benchmark. That does not support a claim about program behaviour in general |
| Statistical rigor | PASS | Clustered bootstrap, within-cluster permutation with a non-zero p-value floor, paired ΔAUROC with Holm correction, Wilson intervals, noise floor, verified determinism |
| Baseline quality | PASS | 13 predictors from the same traces plus two structural baselines on the same pairs; every one reproducible from `make reproduce-*` |
| Empirical validity | PASS | Every headline number traces to a committed artifact with its per-pair record; CI fails on drift |
| Reproducibility | PASS | Clean checkout verified; 643/744 reproduces exactly; the one non-reproducing artifact is labelled NON_REPRODUCING with the cause |
| Claim discipline | PASS | Eight withdrawn claims listed with corrections; claim table marks two Supported, one Supported-with-scope, three Not supported, two Open; no "proves", "solves" or "state of the art" |
| Failure transparency | PASS | Negative results lead the README; every exclusion counted; the `ALL` row charges failures to the method |
| Internal consistency | PASS | 8/8 consistency gate; README results block generated, not written |
| Engineering quality | PASS | 602 tests, three-job CI without `continue-on-error`, archive/current/generated split, one authoritative manifest |
| Scientific integrity | PASS | Provenance registry; `scores_are_real` fixed; the 9/9 output-free verdict scope-qualified rather than deleted |
| Research maturity | PASS | Leakage, circularity, denominator, clustering and reproducibility failures were found, measured and reported against the project's own earlier claims |
| **External validation** | **BLOCKED** | The QuixBugs, BugsInPy and Java cross-language results were not re-run. They use the same entry-discovery code and are therefore subject to the same protocol defect. Their status is unresolved |

### The two blocked categories

**Benchmark quality.** The output-free protocol is defined for programs with a
module-level API function whose parameters can be supplied from a fixed type
battery. 41 of 64 corpus programs qualify; 7 of 13 in the test split. The 23
that do not are mostly class-based — `ds_hash_table`, `api_rate_limiter`,
`fsm_vending_machine` — which is to say the programs *with state*, precisely
where a state-transition genome should have the most to say. The corrected
evaluation therefore runs on the easier half of the corpus.

*To clear it:* a driver-synthesis mechanism that can exercise a class through a
sequence of method calls without hand-writing a driver per program, plus a
corpus of real programs. Neither is a repair; both are new work.

**External validation.** Verifying the external corpora means re-running each
under the output-free protocol, establishing that their labels are independently
sourced, and checking that no tuning touched them. That is a second evaluation
of comparable size to this one. Until it is done, no claim about
generalisation is made, and `results/external/` is excluded from every current
document.

---

## Remaining limitations

Genuine, and not fixable inside this repository:

1. **Seven programs.** With the base program as the unit of independence, the
   intervals are wide and only large differences are detectable. A
   non-significant comparison here is not evidence of equivalence.
2. **Synthetic corpus.** Single-file exercises with self-tests. The uniform
   structure is what produced the protocol defect in the first place.
3. **Class-based programs out of scope**, and they are the stateful ones.
4. **The distance weights were never fitted.** Until a learned combination is
   fitted on dev and evaluated on the frozen test set, "the representation is
   weak" is not separable from "these weights are wrong".
5. **τ\* was derived under the published protocol** and has not been re-derived
   for the output-free one, whose distance distribution differs. Re-deriving it
   on test data would be the leak the fixed threshold exists to prevent.
6. **Trace-derived features shift between Python versions.** Any number here is
   attached to CPython 3.13.15.

---

## Honest summary

The most valuable result in this repository is not about the Software Behavior
Genome. It is that a system can pass nine out of nine output-leakage checks, a
reproducibility audit and an adversarial review while its central measurement is
reading the programs' own unit-test assertions — because every one of those
checks examined the distance function and none examined what was being executed.

The representation itself: execution beats structure by a wide and significant
margin, and beats nothing else.