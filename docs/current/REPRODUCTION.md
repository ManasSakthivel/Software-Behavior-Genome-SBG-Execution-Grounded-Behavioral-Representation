# Reproduction

## Environment

| | |
|---|---|
| OS | macOS 15 (Darwin 25.6) and Ubuntu 22.04 are both exercised in CI |
| Python | 3.9 minimum. CPython only — `sys.settrace` is required |
| Dependencies | `pytest` for the tests. Nothing else; no numpy, no scipy, no sklearn |
| Hardware | single core is enough; no GPU; peak RSS under 500 MB |
| Seed | 42 everywhere |

The statistics are implemented from scratch in `sbg/statistics.py` rather than
taken from a library, so a reproducer needs no scientific stack. The AUROC is
cross-checked against the independent implementation in `sbg.v3.metrics` by
`tests/test_statistics.py::TestAuroc::test_agrees_with_v3_implementation`.

### A note on Python version

The tracer reads `frame.f_locals` on every trace event. PEP 667 changed what
that returns in Python 3.13, and comprehension inlining in 3.12 changed which
call events a comprehension produces. Trace-derived features can therefore
differ slightly between versions. CI runs the test suite on 3.9 and 3.13 for
this reason, and any headline number should be read as attached to the version
that produced it. The committed artifacts were produced on CPython 3.13.15.

## From a clean checkout

```bash
git clone https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation.git
cd Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation

python3 -m venv .venv && . .venv/bin/activate
pip install pytest

make test          # full suite
make quickstart    # smoke test, instant
make check         # verify every committed artifact against its generator
```

`make check` re-runs the static audits, rebuilds the manifest, regenerates
every table from the artifacts, diffs them against the committed copies, and
runs the integrity tests. It executes no experiment, so it is fast and it
cannot change a result.

## Verification is not reproduction

The previous `make reproduce` target compared hashes of committed artifacts.
That verifies that files have not been edited; it does not re-measure anything.
The two are now separate targets and the distinction is in `make help`.

| Target | What it does | Time |
|---|---|---|
| `make verify-artifacts` | audits, manifest, tables, consistency gate. No experiment runs | ~30 s |
| `make check` | the above plus the integrity tests | ~40 s |
| `make reproduce-fast` | re-executes the hard-negative and regression experiments | ~1 min |
| `make check-reproduction` | re-executes them and compares against the committed artifacts | ~1 min |
| `make reproduce-v5` | re-executes the main benchmark under the published protocol | ~26 min |
| `make reproduce-output-free` | re-executes it under the output-free protocol | ~10 min |
| `make benchmark-v6` | regenerates the corrected benchmark from the corpus | ~3 min |
| `make reproduce-all` | all of the above | ~45 min |

A `reproduce-*` target **overwrites** the artifact it produces. Run
`git diff` afterwards: a clean diff means the result reproduced bit for bit.
CI does exactly this for the two fast experiments, and fails if the diff is
non-empty.

## What reproduces, and what does not

| Result | Status |
|---|---|
| 643 of 744 test pairs evaluable under the published protocol | reproduces exactly |
| Main-benchmark AUROC under the published protocol | reproduces to ±0.006 of the published 0.551; the residual is attributable to Python version (see above) |
| Hard-negative and regression experiments | reproduce bit for bit **on CPython 3.13**, the interpreter that produced the artifacts. On 3.9 every reported count comes back identical but individual pair distances move, because the tracer sees a different event stream. `make check-reproduction` checks the counts on any interpreter; CI adds `--strict` on 3.13 |
| Static audits and the manifest | deterministic; byte-identical |
| `artifacts/v5/REGRESSION_EVALUATION_RESULTS.json` | **does not reproduce.** Re-running its own generator gives volume 11/15 where the artifact says 7, and 4 silent bugs where it says 8. Its volume feature is a wall-clock ratio, so the partition it derives is timing dependent. Superseded by `artifacts/final/REGRESSION_V5_RESULTS.json` |

## Runtime, honestly

`make reproduce-v5` takes about 26 minutes, and it is not evenly distributed:
`ds_hash_table` alone accounts for roughly half. Its self-test driver exceeds
the 5-second per-trace budget on every run, so each of its ~58 variants costs
about 25 seconds. The tracer records a `repr` of every local variable on every
trace event, which is why tracing a program that manipulates large collections
is three orders of magnitude slower than running it.

The output-free protocol is faster (~10 min) because the programs it cannot
handle are declared out of scope before execution rather than traced and
discarded.

## Expected output

After `make check` on an unmodified checkout:

```
[PASS] C1 generated tables match their artifacts
[PASS] C2 benchmark manifest is internally consistent
[PASS] C3 result denominators agree with the sets
[PASS] C4 documents cite only MEASURED artifacts
[PASS] C5 no retired claim appears in a current document
[PASS] C6 no output-reading result is attributed to SBG
[PASS] C7 output-free protocol traces no self-test driver

7/7 checks passed
```

If any check fails, the message names the file, the line and the correct value.
