# V7-B core: implementation status

Authority: `reports/final/V7B_FROZEN_SPEC.md`. All thresholds are the UNVALIDATED defaults. Nothing here claims equivalence of any pair.
Run: `python -m sbgv7 compare BASE.py VARIANT.py --entry F --inputs inputs.json --config cfg.json --out DIR`
(exit 0 verdict written, 2 invalid config/inputs/usage, 3 `ineligible:identical`). Tests: `.venv/bin/python -m pytest tests/v7`.

## Modules (sbgv7/)
`records.py` types + content-addressed ids + hash-chained JSONL log + `trace`; `compare.py` boundary comparator; `config.py` strict
validation; `harness.py` child-side executor (monitoring-based line/branch capture); `runner.py` glue, replay protocol, activation;
`decide.py` pure verdict/sufficiency; `__main__.py` CLI. V5/V6 untouched; `sbgv6.features.changed_lines` is imported read-only.

## Implemented
- Verdicts DIVERGENT_OBSERVABLE > INSUFFICIENT(primary; secondary by rank B1..B9) > NO_DIVERGENCE_OBSERVED(S1|S2). `Verdict` asserts a closed
  value/reason-code enum; no equivalence value exists. S0 only appears inside INSUFFICIENT's SufficiencyRecord. Missing records are blockers (`tool_error`).
- Per-input outcomes: CONFIRMED_DIFF, UNCONFIRMED_DIFF (sub-labelled intermittent / failed_reproduction), ENV_SENSITIVE_DIFF, SAME,
  QUARANTINED (nondeterministic), LIMIT_ASYMMETRIC, NO_RUN (both sides limit).
- Protocol: r_det repeats (early stop on first disagreement), r_replay fresh replays per side, k_alt alternate control runs (seeded RNG + shifted clock).
- Comparator: return, exception (exact qualified type, normalised message or `ignore`), stdout, sandbox-temp files, argument post-call state,
  module globals written, API break (argument-binding failure). Type tag is identity, binary64-exact floats (NaN equal, -0.0 != 0.0), optional tolerance, mapping/set order-insensitive, objects to depth 3, `lossy` flag blocks S2.
- Terminals: returned/raised/exited/crashed(signal)/bind_error; timeouts and resource kills are limits, never witnesses.
- Changed-region activation: `changed_lines` intersected with executable lines per side; a unit is hit only by deterministic-confirmed SAME inputs.
- S1/S2 floors as in the spec section 6; S2 branch coverage = observed branch directions / 2 x branch instructions on changed lines, per version.
- Evidence log `DIR/evidence.jsonl` (chain verified by `records.read_log`), `DIR/verdict.json`; `records.trace(log, verdict_id)` walks verdict -> Witness/SufficiencyRecord -> runs -> observations/versions. Run/Witness ids are content-addressed and stable across invocations.
- Stored per run: slot-based id, status, observation id, hit lines (not a hashed event stream).

## Not implemented (honest gaps)
- S3 (refused in config, never emitted), explorer, module E / `internal_divergence`, input generation (inputs are user-supplied JSON values only: no tuples/sets/objects).
- Spec codes never produced: `ambiguous_entry`, `unmodelled_change`, `unsafe_program`(except trace-tamper flag), `blind_spot_dominant`, `alignment_failed` (only on parse failure). Entry-lifting to an outer frame and declared renames are not done; entry must be a top-level function.
- Isolation is the existing `sbgv7.isolation`: macOS `sandbox-exec` only, no Linux container path; every macOS record carries `policy_below_minimum=true` (spec: synthetic/benchmark only). Interpreter/tracer build mismatch handling (replay `inconclusive`) is absent. Dependency/runtime byte-identity check covers the source file only.
- Tamper detection is a post-run check of monitoring state; programs writing via `os.write(1)` or subprocesses bypass stdout capture.
- Quarantine is conservative: any quarantined input blocks (never inspected for "may have hit"). `r_empty` is recorded but not stratified. No minimisation, no Merkle tree (a flat hash of run ids), no Supersession/void, no replay-recipe/event-stream storage, no seeds/budget grid, no calibration, no gates K1-K5.
- Control alternation (`k_alt`) virtualises only `random.seed` and `time.time/time_ns`; other entropy (uuid, os.urandom, env) is not virtualised.
- Branch coverage counts POP_JUMP_IF_*, FOR_ITER and SEND only, and treats all directions as statically reachable (conservative denominator).
- Timing: tests run real sandboxed subprocesses (about 14 s total); `env_sensitive` and replay-failure classes are tested with scripted runs, not real programs.
