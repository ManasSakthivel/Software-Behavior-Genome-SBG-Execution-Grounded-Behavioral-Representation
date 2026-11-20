# Evaluation protocol

SBG compares two versions of a program by executing both and measuring the
distance between their execution genomes. What gets executed is therefore part
of the method, not an implementation detail — and it is where the published
evaluation went wrong.

## The published protocol

`baselines/v5/b07_dynamic_v5.py` picks an entry function in three steps:

1. the first name in a fixed priority list (`sort`, `search`, `run`, `main`, …)
   that the module defines;
2. otherwise the call-graph root returned by
   `sbg.v5.invariant_identity.compute_program_identity`;
3. otherwise the alphabetically first public function.

It then calls that function with 11 canonical list inputs, 5 times, under
`sys.settrace`, capping each trace at 5000 events and 5 seconds.

### Why step 2 breaks the output-free constraint

`compute_program_identity` documents its root as "the function not called by
any other module-level function". In this corpus that is the program's own
`test_*` self-test driver: a driver calls everything, and nothing calls it.

Tracing a self-test driver puts its `assert` statements inside the traced
region. When a mutant breaks an assertion, `AssertionError` is raised there and
lands in `exception_type_set` and `exception_rate`. Those features then encode
*whether the program's own unit tests passed* — an output comparison reached
indirectly.

Measured statically over the corpus
(`artifacts/final/OUTPUT_ORACLE_LEAK_AUDIT.json`):

| | |
|---|---:|
| Corpus programs | 64 |
| Entry function is a self-test driver | 47 |
| `assert` statements inside traced regions | 611 |
| Programs where the 11 canonical inputs are never executed | 49 |

The third row follows from the second: a `test_*` driver takes no arguments, so
the protocol calls it once with `None` and the documented input battery never
runs. 9 of the 13 test-split programs are affected.

This matters for the headline claim. The published README reports that
`exception_fraction` alone beats the full genome and reads that as evidence
that the representation fails to beat a cheap shortcut. Under a protocol that
traces self-tests, `exception_fraction` is not a shortcut — it is a leaked
output oracle, and the comparison does not support that reading.

The V5 safeguard audit reported 9/9 checks passing, and its checks were sound:
no SBG code path reads a return value. The leak is in the choice of what to
execute, which the audit did not examine.

## PROTOCOL `output_free_v6`

`experiments/final/protocol.py` defines the corrected protocol.

**Entry selection.** Candidates exclude scaffolding: any name matching `test_*`,
`main`, `demo*`, or a leading underscore. Among the remainder: a priority-list
name if one exists, otherwise the alphabetically first *annotated* candidate,
otherwise the alphabetically first candidate. Annotated candidates are
preferred because their inputs are synthesised from declared types; the
preference is on the presence of annotations alone and never consults an
outcome.

**Input synthesis.** One fixed battery per type family — list, str, int, float,
bool, dict — each of 11 elements, all defined as constants in
`experiments/final/protocol.py`. For a function of several parameters the
batteries are *zipped*, not multiplied, so the number of traced executions
stays at 11 regardless of arity.

**Scope.** A program is in scope only if some candidate's every parameter can
be supplied from the battery. `Callable`, IO types and unknown custom classes
are not synthesisable, so their functions are ineligible. 41 of 64 corpus
programs are in scope; 7 of the 13 test-split programs are. This is a real
reduction in sample size and it is reported as such rather than worked around.

**Budgets.** Because the protocol traces a real function over 11 inputs rather
than a zero-argument driver over one, it performs 55 traced executions per
program instead of 5, and a mutant that fails to terminate becomes expensive.
Three fixed constants bound it:

| Constant | Value | Reason |
|---|---|---|
| per-trace timeout | 1 s | base programs finish in milliseconds |
| per-program budget | 60 s | checked between runs, so one full run always completes |
| max timed-out traces | 2 | then the program is recorded `nonterminating` |

All three were fixed before any result was computed and apply identically to
the base and the variant of every pair, so they cannot favour one predictor
over another. A program that hits them appears in the failure ledger of the
result artifact; none is dropped.

## Shared execution

`experiments/final/extraction.py` executes each program **once** and hands the
same traces to every predictor. Previously each predictor ran its own
extraction with its own entry discovery, input set and run count —
`b07_dynamic_v5.py` used 11 inputs × 5 runs at 5000 events, while
`experiments/v4/phase1_volume_control.py` used the V3 input set × 3 runs at
3000 events. An AUROC difference measured that way confounds the representation
with the execution protocol. Under the shared pass, two predictors differ only
in the feature they read.

## Two tracer defects fixed along the way

Both surfaced while running the corrected protocol and both are covered by
`tests/test_tracer_isolation.py`.

**`sys.stdout` was left hijacked after a timeout.** The worker thread replaces
the process-global `sys.stdout` to capture the traced program's output and
restores it in a `finally`. A worker abandoned on timeout never reaches that
`finally`, so every later write by the host disappeared into a dead thread's
buffer. This silently swallowed the evaluation harness's own progress logging
and made a running job look hung. The host now restores `sys.stdout` itself
after every join.

**Timed-out workers accumulated.** A trace that exceeds its budget leaves a
thread that cannot be killed. Without an early abort, a mutant that loops
forever leaves one per input per run, and they compete for the GIL with every
program traced afterwards. `Tracer.trace` now accepts `max_timeouts` and stops
after that many.

Neither change alters the published protocol: the new parameters default to the
previous behaviour, and `PROTOCOL published` passes `None` for all of them.
