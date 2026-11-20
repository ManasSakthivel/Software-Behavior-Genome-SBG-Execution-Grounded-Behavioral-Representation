# Failure matrix: what goes wrong, and what the tool reports

Derived by reading `sbgv7/__main__.py`, `runner.py`, `decide.py`, `isolation.py`, `verify.py`, `records.py` at HEAD (code identical to `5efcef74`). "Verdict" is the content of `verdict.json`. Rank is the blocker rank in `decide.RANK`: when several blockers apply, the lowest rank is the `primary` reason and the others are `secondary`. Precedence: a replay-confirmed witness gives `DIVERGENT_OBSERVABLE` regardless of any blocker; otherwise any blocker gives `INSUFFICIENT`; otherwise `NO_DIVERGENCE_OBSERVED`.

## A. `compare` command: no verdict is written
| Failure | Outcome | Exit |
|---|---|---|
| base or variant is not an existing `.py` file; `--entry` is not an identifier; config or inputs fail strict validation (unknown key, S3 enabled, non-constant `normaliser_id`/`stderr`/`capture_tier`, non-JSON inputs) | `error: ...` | 2 |
| `OUT/evidence.jsonl` already exists (no-overwrite policy) | `error: ... refusing to overwrite evidence` | 2 |
| output directory not writable, or a file where a directory is needed | `error: cannot write evidence to ...` | 2 |
| the two source files are byte-identical | `ineligible:identical (...no verdict is issued)`; no directory or log is created | 3 |
| unexpected internal exception | one line `internal error: <Type>: <msg>`, no traceback, no verdict | 1 |
| anything else: a verdict was written (any value) | read `verdict.json` | 0 |

Exit 0 therefore does not mean "no difference"; it means the tool completed.

## B. Static (probe) phase: both versions are imported once with no call; any failure blocks all input runs
| Failure | Verdict and reason | Rank |
|---|---|---|
| probe run not `sandbox_ok` (sandbox unavailable, a required control inactive, cleanup unverified, orphan processes, rlimit could not be applied) | `INSUFFICIENT(sandbox_failure)` | 3 |
| probe run flagged tampered (result-protocol violation or monitoring tamper) | `INSUFFICIENT(unsafe_program)` | 3 |
| import hits a CPU/wall/memory limit | `INSUFFICIENT(resource_limit)` | 6 |
| import raises | `INSUFFICIENT(import_error)` | 1 |
| entry function missing in a version | `INSUFFICIENT(unsupported_signature)` | 2 |
| signatures incompatible and `api_break_probe` false | `INSUFFICIENT(unsupported_signature)` | 2 |
| other probe phase failure (harness error) | `INSUFFICIENT(tool_error)` | 8 |
| changed-region alignment fails (SyntaxError, ValueError, decode error, RecursionError) | `INSUFFICIENT(alignment_failed)` | 2 |
| changed lines that carry no executable code (not docstring-only), for example continuation lines of multi-line statements | `INSUFFICIENT(unmodelled_change)` (inputs still run; it is a conservative rule, UD-2 open) | 2 |

## C. Per-input execution (`runner.classify`)
| Event on an input | Outcome | Reason code it contributes | Rank |
|---|---|---|---|
| any run (primary, repeat, replay, alt) tampered: forged, missing, duplicate, malformed, oversized result frame or trailing bytes after it, premature `os._exit`, monitoring tamper | `NO_RUN` (tamper) | `unsafe_program` | 3 |
| call run raises at import or entry lookup | `NO_RUN` (import) | `import_error` | 1 |
| harness error in a call run | `NO_RUN` (tool) | `tool_error` | 8 |
| a run not `sandbox_ok` | `NO_RUN` (sandbox) | `sandbox_failure` | 3 |
| repeats of one side disagree (`r_det`) | `QUARANTINED` | `nondeterministic` (blocks `NO_DIVERGENCE_OBSERVED`) | 5 |
| both sides hit a limit | `NO_RUN` (both_limit) | `resource_limit` | 6 |
| exactly one side hits a limit | `LIMIT_ASYMMETRIC` | `resource_limit` (never a witness) | 6 |
| input cannot be bound on either side | `NO_RUN` (invalid_input) | none by itself; excluded from evidence | - |
| equal observations | `SAME` | none; contributes to activation unless lossy or degenerate | - |
| observations differ but replays (`r_replay`) do not all reproduce | `UNCONFIRMED_DIFF` | `flaky_witness` | 4 |
| differ, replay confirms, but an alternate control setting (`k_alt`) changes an observation | `ENV_SENSITIVE_DIFF` | `env_sensitive` | 4 |
| differ, replay confirms, controls invariant | `CONFIRMED_DIFF` | witness: `DIVERGENT_OBSERVABLE` | - |
| captured output exceeded the cap | any | `capture_truncated` | 7 |
| signal death (killed by the parent or OS), sandbox ok | recorded as a `crashed` observation, compared like any other | none | - |

## D. Whole-comparison conditions (`decide._blockers`, `runner.finalize`)
| Condition | Verdict and reason | Rank |
|---|---|---|
| no input at all, or no deterministic confirmed `SAME` input | `INSUFFICIENT(no_inputs)` | 8 |
| every `SAME` input is degenerate (nothing observable) or only equal on a lossy canonical form (opaque objects, depth/size limits) | `INSUFFICIENT(unobservable_outcome)` | 8 |
| a changed line was not hit by any deterministic confirmed non-lossy `SAME` input | `INSUFFICIENT(changed_region_not_activated)` | 9 |
| CPU budget exhausted before inputs finished, or cut inside an input | stop `budget` / `budget_mid_input`; unhit lines then give `INSUFFICIENT(budget_exhausted_s0)` (rank 9); a mid-input cut always adds it | 9 |
| missing or incomplete evidence record, unknown reason code, unrecognised outcome | `INSUFFICIENT(tool_error)` (never a crash in `decide`) | 8 |
| none of the above, activation and floors met | `NO_DIVERGENCE_OBSERVED(S2)` if both versions reach the branch floor (default 0.80) and no lossy `SAME`, else `(S1)` | - |

Reason codes never produced by the current engine: `ambiguous_entry`, `blind_spot_dominant`. Every record carries `policy_below_minimum=true` on macOS.

## E. `verify` command
| Failure | Exit |
|---|---|
| recomputed verdict equals the recorded one; chain, ids, sources, regions, outcomes and sufficiency record all re-derive | 0 |
| broken hash chain; unreadable log lines; content id mismatch; unknown reason code; not exactly one package and one trailing verdict; `verdict.json` disagrees with the log; source digest, harness id or pair id mismatch; V6 `changed_lines` digest differs; recomputed regions, per-input outcome, tamper flag, verdict, witness or sufficiency record differ from the recorded | 1 |
| `evidence.jsonl` missing or unreadable as a file; malformed or missing fields (OSError, KeyError, ValueError, TypeError) | 2 |
| source text or an input was omitted by the size cap: the verdict cannot be recomputed | 4 |

Not detected by `verify` (documented, observed in E7): editing unverified recorded facts (run timings, run status or detail, observations) and recomputing the whole chain and `log_head`; deleting `verdict.json`; a false observation recorded by a malicious evaluated program that shares the harness's address space. `verify` never re-executes anything.
