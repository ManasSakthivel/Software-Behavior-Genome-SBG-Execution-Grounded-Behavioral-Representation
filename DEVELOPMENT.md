# Development Notes

Notes for working with this codebase.

## Setup

```bash
# Python 3.9+ required (CPython only — sys.settrace isn't available on PyPy)
pip install pytest
```

That's it. The core library (`sbg/`) has no external dependencies — it uses only the Python standard library.

## Running tests

```bash
make test               # full suite (~25s)
make test-fast          # stop at first failure
python3 -m pytest sbg/ -q --tb=short   # with tracebacks
```

All 516 tests should pass. If they don't, something in the Python environment is off.

## Repository layout

```
sbg/
  extraction/
    static/     # CONTROL, DATA, ERROR genome extractors
                # test_extractor.py, test_data_genome.py, test_error_genome.py
    dynamic/    # tracer and dynamic genome extractors
                # test_tracer.py, test_state_genome.py, test_temporal_genome.py, etc.
  v3/           # DynamicGenomeV3 + WMW AUROC + tests
  v5/           # V5 modules (invariant_identity, temporal_genome, state_transition)

baselines/      # comparison methods B01–B08, versioned
benchmark/
  corpus/       # 99 Python base programs
  datasets/     # pairs_train/dev/val/test.jsonl — DO NOT MODIFY pairs_test.jsonl
  transformations/  # SP and SC transform implementations
  v5/           # hard-negative benchmark, regression corpus, Java programs

experiments/    # experiment scripts
artifacts/      # frozen results (JSON) — do not overwrite with new runs
docs/           # research documentation, versioned reports
```

## Adding a new test program

If you want to add a new base program to the corpus:

1. Write it in `benchmark/corpus/base_programs/` following the `category_name.py` convention
2. Make sure the program has a clear entry function (the one that does the main work)
3. The program should work standalone with basic inputs
4. It doesn't need a `__main__` block — the tracer will call the entry function directly

## Working with the benchmark

The test set (`benchmark/datasets/pairs_test.jsonl`) is frozen — don't use it for tuning or development. Use `pairs_dev.jsonl` or `pairs_val.jsonl` for development evaluation.

Each pair in the JSONL files has:
```json
{
  "pair_id": "...",
  "program_a": "...",  // source code string
  "program_b": "...",  // source code string
  "label": "CHANGED" or "EQUIVALENT",
  "base_program": "...",  // which base program it derives from
  "transform": "..."  // which transformation was applied
}
```

## Important design constraints

- **Output-free**: The genome extractors never read program outputs. Distance is computed from execution structure only (call patterns, coverage, state transitions). This is intentional — reading outputs would make the comparison trivial for many cases.
- **Rename-invariant**: Function names are never used as features. All indexing is by call order. This means refactoring (SP-2: function rename) shouldn't change the distance. In practice, this works for V5 with the invariant_identity module; V2/V3 had some leakage here.
- **Deterministic**: SEED=42 is set everywhere. Two runs of the same script produce identical output.

## Adding a new baseline

1. Create a file in `baselines/` following the B01–B08 naming convention
2. Implement the `score_pair(program_a: str, program_b: str) -> float` interface
3. Run it on the dev set first; evaluate with `sbg.v3.metrics.compute_auroc_v3`
4. Don't touch the test set until the method is finalized

## Reproducing results

```bash
make reproduce              # sanity check (instant)
make run-v5                 # V5 AUROC on test set (~30 min)
python3 benchmark/v5/hard_negatives/oracle.py    # hard-negative oracle
python3 experiments/v5/regression_evaluator.py  # regression detection
```

Expected results match `artifacts/v5/` — SHA-256 hashes in `artifacts/v5/FINAL_EVIDENCE_MANIFEST_V5.json`.

## Things that don't work (known limitations)

- PyPy/Jython: `sys.settrace` is not available
- Programs that require network/file I/O beyond `os.path`: the sandbox blocks these
- Very large programs (>500 lines): tracer overhead becomes noticeable
- Programs with heavy use of `threading`: non-deterministic trace ordering
- Java evaluation: infrastructure exists but full AUROC hasn't been run

## Commit hygiene

- Don't commit `.env` files, large outputs, or generated artifacts from new experimental runs
- The `artifacts/` directory contains frozen results — update only when intentionally running a new official evaluation
- Test counts in the README badge should match actual `pytest` output
