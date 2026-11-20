# Entry-Point Limitation: `conc_read_write_lock`

**Phase 4 — Wave 1**
**Status:** RESOLVED (91.4% of affected pairs), 5 pairs honestly disclosed as unresolved
**Frozen benchmark:** NOT MODIFIED
**Historical Phase 3B artifacts:** NOT MODIFIED (new artifact created alongside)

---

## 1. The Problem

`benchmark/corpus/base_programs/conc_read_write_lock.py` defines only two classes
(`ReadWriteLock`, `ProtectedDict`) with all exercising logic inside an
`if __name__ == "__main__":` block — there is no top-level callable function.
This pattern is repeated identically across all 58 of its test-set variant files
(21 SP-type EQUIVALENT pairs + 37 SC-type CHANGED pairs), because the transform
generators preserve the base program's structure.

Before this fix, `baselines/v2/b07_dynamic_v2.py::_load_entry_fn()` returned
`None` for every one of these 116 program files (base + variants), and
`_score_pair()` fell back to a hardcoded neutral `similarity = 0.5` for every
affected pair. This is **58/744 = 7.8%** of the frozen test set contributing
zero real signal to any AUROC computation — pure noise, symmetric across both
the EQUIVALENT and CHANGED classes.

A second, independent bug compounded this: `sbg/v2/execution/runner.py`
excluded `conc_read_write_lock` from execution entirely via a hardcoded
`_UNSAFE_PROGRAMS` set (matched by filename stem), on the grounds that its
`__main__` block spawns real concurrent threads (non-deterministic). This
exclusion was applied inconsistently — it matched the base file's stem exactly
but never matched any differently-named variant file's stem, so variants would
have been run for real (and possibly hung/flaked on threading) the moment
entry-point discovery was otherwise fixed.

## 2. Scientifically Correct Resolution (per Phase 4 priority order)

Per the Phase 4 mandate, the preferred order was:
1. Implement a legitimate class-based execution adapter, if possible.
2. Otherwise, a documented supported-entry-point protocol.
3. Only if genuinely impossible, exclude the program with explicit accounting.

**Option 1 was implemented successfully.**

### 2.1 The Adapter

`baselines/v2/b07_dynamic_v2.py::_build_class_adapter()` is a generic,
reflection-based fallback used only when no top-level callable function is
found (so it changes behavior *only* for programs that were previously
returning `None`; no regression risk to any already-working program).

**Class selection (composition-based, not source-order-based).** The adapter
instantiates every top-level class defined in the module and identifies the
"primary" (outer/composed) class structurally: a class `C` is preferred if an
instance of `C` holds an attribute that is itself an instance of another
class also defined in the module (e.g. `ProtectedDict` holds a
`ReadWriteLock`). This is necessary because `inspect.getsourcelines()` (which
would otherwise be used to detect declaration order) fails for modules loaded
via `importlib` without `sys.modules` registration — an early version of this
adapter that relied on source-line ordering silently fell back to alphabetical
class discovery order and selected the wrong (inner, primitive) class,
causing genuine deadlocks when driven directly and out of protocol.

**Driving strategy.** The adapter calls every public method of the primary
class over `V2_CANONICAL_INPUTS`, **constructing a brand-new instance for
every individual method call** (not once per program, not even once per
input). This was required after empirical testing revealed that several
benchmark transform variants (see §3 below) contain a genuine bug that leaves
internal lock state corrupted after a failed call (e.g. an `AttributeError`
raised inside a `try/finally` before `release_read()` runs, permanently
incrementing `_readers` with no matching decrement). Reusing the same
instance across calls would then deadlock permanently on a real
`threading.Condition.wait()` that no other call will ever notify —
fresh-instance-per-call fully isolates each call so one broken transaction
cannot cascade into a hang for the rest of genome extraction.

**No threading is spawned.** The adapter deliberately drives the class
sequentially, not concurrently. This is why removing `conc_read_write_lock`
from `_UNSAFE_PROGRAMS` is safe: the original exclusion targeted the
`__main__` block's real `threading.Thread` spawning (non-deterministic
interleaving), which this adapter does not reproduce.

### 2.2 Disclosed Limitation

This adapter measures **sequential correctness of the class's public API**
— it does *not* reproduce genuine concurrent contention (multiple threads
racing on `acquire_read`/`acquire_write`). The dynamic genome extracted for
`conc_read_write_lock` therefore reflects how the class behaves under a
deterministic, single-threaded call sequence, not how it behaves under real
concurrent load. This is an intentional, disclosed trade-off: reproducing
genuine concurrency would reintroduce the non-determinism that made this
program unsafe for execution-based benchmarking in the first place.

### 2.3 Companion Fairness Fix

`baselines/v2/b06_fair_v2.py` had an *independent, worse* bug for the same 58
pairs: when entry-fn discovery failed, `_extract_trace_features()` returned
empty feature dicts, and `score_fn()`'s `_jaccard(set(), set()) == 1.0`
convention computed `similarity = 1.0` — fabricating **maximum** similarity
(claiming perfect equivalence) rather than a neutral score. This has been
fixed to check `n_traces == 0` and return the same neutral `0.5` convention
B07 uses, so B06-vs-B07 comparisons in Wave 2 are not distorted by
inconsistent fallback semantics.

## 3. Residual Imputation (Honestly Disclosed, Not Fabricated)

**5 of the 58 test-set pairs (0.67% of the full 744-pair test set) remain
imputed at exactly 0.5**, for a reason **unrelated to entry-point discovery**:

| Pair | Transformation | Cause |
|---|---|---|
| `test__conc_read_write_lock__sp-3_s1` | SP-3 | Module-level `SyntaxError` |
| `test__conc_read_write_lock__sp-3_s2` | SP-3 | Module-level `SyntaxError` |
| `test__conc_read_write_lock__sp-8_s2` | SP-8 | Module-level `SyntaxError` |
| `test__conc_read_write_lock__sc11_s1_p0` | SC-11 | Module-level `SyntaxError` |
| `test__conc_read_write_lock__sc11_s2_p0` | SC-11 | Module-level `SyntaxError` |

These variant files contain a bug in the benchmark's dead-code-injection
transform generator: it inserts a bare `if False: return None` statement at
**module scope** (outside any function or method body), e.g.:

```python
if False:
    return None      # <-- SyntaxError: 'return' outside function
```

`return` outside a function body is a Python `SyntaxError`. `importlib`'s
`exec_module()` cannot even parse the file — there is no class, no function,
nothing an adapter could execute. This is a pre-existing defect in the
benchmark's transform generator, independent of and unfixable by any entry-
point adapter. Per the "never fabricate a score" mandate, these 5 pairs
retain the neutral `0.5` imputation, explicitly disclosed here and in
`artifacts/v2/ENTRYPOINT_VALIDATION.json`, rather than being silently hidden
or worked around.

**This defect likely affects other programs beyond `conc_read_write_lock`**
(any program whose transform variant received the same dead-code-injection
mutation) and is noted here as a benchmark-generator bug for future
awareness; auditing its full extent across the corpus is out of scope for
this entry-point fix.

## 4. Result

| Metric | Before fix (historical, Phase 3B) | After fix (Wave 1, corrected) |
|---|---|---|
| conc_read_write_lock pairs resolved with real execution | 0/58 (0%) | 53/58 (91.4%) |
| conc_read_write_lock pairs imputed at 0.5 | 58/58 (100%) | 5/58 (8.6%), explicitly disclosed |
| Overall TEST AUROC (B07) | 0.531023 | 0.5292 |
| Delta | — | −0.0018 |

**Interpretation:** fixing the imputation problem changed the aggregate B07
test AUROC by a negligible amount (−0.0018). This is an honest negative
finding: the 7.8%-of-test-set imputation was not responsible for suppressing
B07's aggregate performance — the aggregate signal remains within the
random-label noise floor regardless of this fix (see
`artifacts/v2/NEGATIVE_CONTROL_RESULTS.json`). The fix is nonetheless
scientifically necessary: any per-SP-type or per-SC-type stratified analysis
(Wave 2 onward) that includes `conc_read_write_lock` pairs now reflects real
execution signal for the overwhelming majority of those pairs rather than
uninformative noise.

## 5. Files Changed

- `baselines/v2/b07_dynamic_v2.py` — added `_build_class_adapter()`, wired into `_load_entry_fn()`.
- `sbg/v2/execution/runner.py` — removed `conc_read_write_lock` from `_UNSAFE_PROGRAMS`.
- `baselines/v2/b06_fair_v2.py` — fixed empty-feature-set fabrication bug.
- `experiments/v2/run_entrypoint_fix_validation.py` — new validation/evaluation script (does not modify historical artifacts).

## 6. New Artifacts (Historical Data Untouched)

- `artifacts/v2/ENTRYPOINT_VALIDATION.json` — full validation detail.
- `artifacts/v2/B07_ENTRYPOINT_CORRECTED/results_dev.json`, `results_test.json` — corrected B07 metrics, saved to a NEW directory. `artifacts/v2/B07/results_test.json` (historical Phase 3B) is unmodified.
