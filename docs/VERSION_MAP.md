# Version map

Which result belongs to which version, what changed between them, and which one
is authoritative. A reviewer should not have to guess which "FINAL" document is
final: none of them are. The authoritative results are the V6 artifacts under
`artifacts/final/`, and every number in the README is generated from them.

| Version | What it introduced | Where its results live | Status |
|---|---|---|---|
| V1 | Static genome (control, data, error dimensions); first pair benchmark | `artifacts/phase3/`, `artifacts/research/` | superseded |
| V2 | Dynamic genome: call frequencies, exception rate, call depth | `artifacts/v2/` | superseded |
| V3 | Order-sensitive features: call-transition bigrams, input sensitivity, exception causality. `distance_v3` | `artifacts/v3/` | superseded |
| V4 | Shortcut controls, feature ablation, strong baselines, semantic oracle | `artifacts/v4/` | partly authoritative — see below |
| V5 | Temporal genome, state-transition genome, rename-invariant identity. `distance_v5 = 0.50·d_v3 + 0.25·d_temporal + 0.25·d_state` | `artifacts/v5/` | superseded |
| EEP | External evaluation on QuixBugs, BugsInPy, QuixBugs-Java | `results/external/` | **not verified in this release** — see below |
| **V6** | Corrected accounting, corrected statistics, output-free protocol, repaired benchmark | `artifacts/final/`, `benchmark/datasets/v6/` | **authoritative** |

## What V6 changed and why

V6 is not a new representation. The representation is still V5. V6 is a
correction of how it was measured.

**1. The execution protocol violated the output-free constraint.**
Entry-function discovery falls back to `compute_program_identity`'s call-graph
root — "the function not called by any other module-level function". In this
corpus that is each program's own `test_*` self-test driver. Tracing it puts
the driver's `assert` statements inside the traced region, so `exception_rate`
and `exception_type_set` record whether the program's own tests passed. 47 of
64 programs are affected, covering 611 `assert` statements; 49 of 64 never
execute the documented canonical inputs at all
(`artifacts/final/OUTPUT_ORACLE_LEAK_AUDIT.json`).

This is why the published reading of the headline comparison does not hold.
`exception_fraction` was described as a cheap shortcut that beats the full
genome. Under a protocol that traces self-tests it is not a shortcut, it is a
leaked output oracle.

`experiments/final/protocol.py` adds `output_free_v6`, which excludes
scaffolding from entry discovery and synthesises inputs from parameter
annotations. 41 of 64 programs support it; the rest are declared out of scope
by a static rule applied identically to every method.

**2. 40% of the CHANGED labels were false.**
Mutation sites were chosen by walking the module breadth-first, so site 0 lands
on module-level scaffolding. 135 of 336 CHANGED test pairs carry a mutation
unreachable from the entry function, and 180 variants across all splits had
their `__main__` guard flipped from `==` to `!=`, which makes the file run its
own test driver on import; 22 of those crash while loading
(`artifacts/final/BENCHMARK_VALIDITY_AUDIT.json`).

**3. 103 variants did not compile.**
SP-3 could emit `return None` at module or class scope. `validate()` used
`ast.parse`, which accepts a module-level `return` — only the compiler rejects
it — so the corrupt variants passed validation.

**4. The published confidence interval was not the one described.**
`artifacts/v5/B07/results_test.json` records `"bootstrap":
"cluster_by_base_program"`, but `baselines/v5/b07_dynamic_v5.py` calls
`bootstrap_auroc_ci` without `pair_ids`, which takes the pair-level branch.
Permutation p-values could also be exactly 0. `sbg/statistics.py` provides
clustered bootstrap, within-cluster permutation with the (b+1)/(m+1)
estimator, and a paired clustered bootstrap for differences between predictors.

**5. The denominators disagreed.**
744 nominal test pairs, 643 evaluated, reported as 744. All 101 are now
categorised in the failure ledger of every result artifact.

## Numbers that were never in conflict

`exception_fraction` appears as 0.567 and as 0.593. These are two different
predictors that were given one name:

- **0.567** (`artifacts/v4/SHORTCUT_CONTROLS.json`) is the pure
  exception-fraction shortcut, |Δ exception rate|, over 643 pairs.
- **0.593** (`artifacts/v4/FEATURE_ABLATION.json`, `only_exception`) is the V3
  exception *component*, `0.5·Jaccard(exception types) + 0.5·|Δ rate|`, with
  the other seven weights zeroed — two features, not one.

The README quoted 0.593 while describing 0.567 ("a single feature counting how
often the program throws an exception"). Both measurements are sound.

## What is not verified in this release

The external-evaluation (EEP) results — QuixBugs, BugsInPy, QuixBugs-Java, the
macro AUROC of 0.829 over 73 bugs, and the Java cross-language transfer figures
— were **not** re-run or verified here. They are subject to the same protocol
defect as the main benchmark, since they use the same entry-discovery code, so
their status is unresolved rather than confirmed. They are excluded from the
README's claims. See `FINAL_STANFORD_READINESS_REPORT.md` for what verifying
them would require.
