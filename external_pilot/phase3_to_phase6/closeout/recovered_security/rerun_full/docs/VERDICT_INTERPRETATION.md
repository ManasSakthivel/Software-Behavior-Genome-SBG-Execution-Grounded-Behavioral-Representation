# How to read a V7-B verdict

V7-B compares two versions of a Python function on inputs it was given and reports what it saw. The verdict set is closed and contains no equivalence value. All statements below hold for the exploratory Phase 2 engine (macOS, CPython 3.13); none is a calibrated probability.

## `DIVERGENT_OBSERVABLE`
A witness exists: an input on which the two versions differed on an observed channel (return value, exception type and normalised message, stdout including fd-1 bytes, sandbox-temp files, argument post-state, module globals), reproduced by fresh-process replays (`r_replay=5`, all must agree) and invariant under alternate control settings. Timeouts and resource kills are never witnesses.
- It means: on that input, the versions observably differ in this harness. `verify` can recompute that outcome from the recorded runs.
- It does not mean: a bug, a regression, an intended or unintended change, or that the difference is caused by the diff (it could come from environment state not controlled by the harness; `datetime.now` is not virtualised).
- On the 258 labelled development pairs V7-B detected 75 of 106 divergent pairs (0.708); B1 detected those 75 and 7 more (82). A missing detection is not evidence of equivalence.

## `INSUFFICIENT(reason)`
The tool declines to conclude. `primary` is the highest-ranked blocker, `secondary` lists the rest. Reasons actually produced (see [`FAILURE_MATRIX.md`](FAILURE_MATRIX.md)):
| Reason | Plain reading | Typically means |
|---|---|---|
| `import_error` | a version failed to import or the entry could not be loaded in a call run | environment or dependency problem, not a behaviour finding |
| `unsupported_signature` | entry missing, or incompatible signatures with `api_break_probe` off | renamed or removed entry; engine gap (renames are not implemented) |
| `alignment_failed` | changed regions could not be computed | source does not parse or align |
| `unmodelled_change` | changed lines carry no executable code | conservative rule; unrefined for continuation lines of multi-line statements, so part of the abstention is noise (54 pairs in E3) |
| `sandbox_failure` | a run lacked a required isolation property | local isolation problem |
| `unsafe_program` | result-protocol violation or monitoring tamper | the evaluated code interfered with the harness; not an OS-isolation guarantee either way |
| `flaky_witness` | a difference appeared but replays did not reproduce it | intermittent behaviour |
| `env_sensitive` | a confirmed difference changed under alternate control settings | clock/randomness dependence |
| `nondeterministic` | repeated runs of one version disagreed (quarantined input) | nondeterminism; note the child hash seed is fixed, so hash-order effects are not seen |
| `resource_limit` | an input hit a CPU/wall/memory limit on one or both sides | may be a load artefact |
| `capture_truncated` | output exceeded the capture cap | |
| `no_inputs` | no usable equal input | empty or all-invalid inputs |
| `unobservable_outcome` | every equal input was degenerate or only lossily comparable | nothing observable was compared |
| `changed_region_not_activated` | some changed lines were never exercised by a usable equal input | the inputs did not reach the change |
| `budget_exhausted_s0` | CPU budget ran out before the change was covered | |
| `tool_error` | internal inconsistency or harness error | a tool problem, report it |
`ambiguous_entry` and `blind_spot_dominant` exist in the schema but the engine never produces them.
Abstention is the mechanism by which V7-B lowered false assurance in E3: 122 of 258 labelled pairs (0.473) were `INSUFFICIENT`, and the entire false-assurance reduction versus B1 comes from them. It is not a measure of correctness, and many reasons reflect missing engine features rather than genuinely hard programs.

## `NO_DIVERGENCE_OBSERVED(S1|S2)`
No input differed, no blocker applied, and the changed lines were hit by deterministic confirmed equal inputs.
- **S1**: no blockers (activation of all changed lines).
- **S2**: S1 plus branch-direction coverage of the changed lines at least `s2_branch_floor` (default 0.80, unvalidated) on both versions, and no lossy-canonicalised equal input. The floor only separates S1 from S2: across floors 0.6/0.8/0.9 the verdict values were identical and the S2 share was 71, 55 and 43 verdicts.
- Levels ignore the number and diversity of inputs: S2 can be reached with two inputs. S3 is refused by the configuration and never issued.
- **It is never equivalence, safety, correctness, "no bug", or a confidence value.** It is a statement about what this run looked at. Worked counter-example: `examples/v7b/variant_hidden.py` differs from `base.py` for every `x >= 1000`, yet three small inputs give `NO_DIVERGENCE_OBSERVED(S1)`. On the development data 16 of 46 driven BugsInPy real-fix pairs received this verdict (old-engine run) although the versions really differ.
- On the 106 labelled divergent pairs, 13 received it (false assurance 0.123, lower than B1's 0.226 only because V7-B abstained on 11 others). At S2 or higher, the decided-verdict risk was 0.067; this is a descriptive development figure, not a guarantee.

## Not a verdict
`ineligible:identical` (exit 3): byte-identical sources get no verdict and no evidence log.

## Evidence and verification
Every verdict has `evidence.jsonl` and `verdict.json`. `python -m sbgv7 verify DIR` exits 0 only if the verdict re-derives from the recorded facts. That shows internal consistency of the log, not that the observations are true and not that the log is unaltered by someone able to recompute the chain; it is not tamper-proof and no operating-system isolation is claimed.
