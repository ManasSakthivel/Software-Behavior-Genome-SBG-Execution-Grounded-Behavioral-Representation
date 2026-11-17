# Final V7-B Requirements Traceability Matrix

Branch `research/v7b-final-validation`, HEAD `cc56e029` (working tree clean). Phase 2 boundary: documentation and read-only analysis; no engine, test or result file was changed. Nothing here claims equivalence of any pair, a detection rate, or that any threshold is correct.

## 1. Method

- Rows are the 135 rules of `PHASE_2_SPEC_CONFORMANCE_AUDIT.md` (IDs unchanged). Every row was re-checked against the **current** code (`sbgv7/*.py`) and the **current** suite (`pytest tests/v7 --collect-only`: 169 tests in 8 files; full run in this review: **168 passed, 1 skipped** (`test_memory_rlimit_as_hard`, RLIMIT_AS unavailable on macOS), about 40 s). Line numbers are current. `Fixed since audit` means the audit's finding no longer holds at this HEAD (commits `8f11d3aa` D-01/D-02, `cc56e029` D-05/D-06/D-09/lossy SAME).
- Rule for `Conforms`: a code line AND a test, or the result of a probe that I ran. Probes ran only `python -m sbgv7 compare|verify` and `load_config` on synthetic files in a scratchpad directory outside the repo; no Docker, Linux or third-party code. Probe names (`bigint`, `subproc`, `filepath`, ...) refer to those runs.
- Test paths are under `tests/v7/`. `MB-nn` = item in `MANDATORY_IMPLEMENTATION_BACKLOG.md`; `SD-nn`/`UD-n` = decision in `FINAL_SPECIFICATION_DECISIONS.md`.

## 2. Counts

| Final disposition (primary) | Rows |
|---|---|
| Mandatory implementation | 23 |
| Specification correction | 17 |
| Optional functionality | 5 |
| Intentionally deferred | 15 |
| Phase 3 dependency | 7 |
| Invalid or obsolete finding | 0 |
| Conforms | 68 |
| **Total** | **135** |

Audit statuses (unchanged denominators): 63 Conforms, 45 Deviates, 23 Not implemented, 4 Unverifiable. After re-check: rows that moved to Conforms because they were fixed or because a probe now supplies evidence are marked in the Status column. A row with two actions shows the primary disposition and names the other in `Required correction`. Obsolete audit findings are counted as `Conforms` in the matrix and as `Invalid or obsolete finding` in the D-xx register (section 5).

## 3. New findings of this review (not in the audit; each reproduced by a probe)

| ID | Finding | Evidence | Severity | Backlog |
|---|---|---|---|---|
| NF-01 | A return value that cannot be canonicalised (integers above 4300 decimal digits: `str(v)` raises) is reported as a program `raised ValueError`; if both versions do this the input is a clean `SAME` | probe `bigint`: `return 10**5000` vs `return 10**5001` gave NO_DIVERGENCE_OBSERVED S2; `harness.py:76,214` | Blocking (false assurance on the central channel) | MB-01 |
| NF-02 | The source path leaks into exception messages, so two versions in different files differ spuriously | probe `filepath`: `raise ValueError(__file__)` in both, DIVERGENT_OBSERVABLE; `harness.py:17-18` normalises only the cwd | Major (false witness) | MB-03 |
| NF-03 | D-16 is now demonstrated with differing output: `os.write(1, b'A')` vs `b'B'` gives NDO S2 (fd-level writes bypass the `sys.stdout` capture; the parent sees them in `Result.stdout` but the runner ignores it) | probe `subproc` | Blocking (false assurance) | MB-02 |
| NF-04 | (code reading, not probed) a protocol violation or unverified sandbox on a replay/alt run does not stop a witness: `classify` checks tamper/sandbox only on primary and repeat runs (`runner.py:166-173`), and `decide` returns the witness before any blocker (`decide.py:79-81`) | A-14 | Moderate | MB-05 |
| NF-05 | `python -O` strips the invariants: `Verdict('EQUIVALENT',...)` and an unknown reason code are accepted | probe | Minor (D-18) | MB-04 |

## 4. Matrix (135 rows)

Status values: Conforms; Fixed since audit; Deviates; Not implemented; Unverifiable; Partial; Vacuous.

### 4.1 Verdicts and precedence

| ID | Audit | Requirement | Implementation (current file:line) | Supporting test | Status now | Evidence | Required correction | Final disposition |
|---|---|---|---|---|---|---|---|---|
| V1 | C | Exactly three verdict values | records.py:7,85; decide.py:77-87 | test_core.py::test_verdict_record_rejects_prohibited_values | Conforms | decide() can return only the three strings; closed tuple | - | Conforms |
| V2 | C | Prohibited outcomes unrepresentable | records.py:85-88 (assert) | test_core.py::test_verdict_record_rejects_prohibited_values | Deviates | probe: `python -O` accepted Verdict('EQUIVALENT') | MB-04 explicit raise instead of assert | Mandatory implementation |
| V3 | D | Row 0: identical src/deps/runtime = ineligible, excluded | runner.py:297-300 (log created before check); CLI __main__.py:30,35 | test_core.py::test_identical_is_ineligible (exception only) | Deviates | probe: identical pair exits 3 but leaves evidence.jsonl; second run exits 2; check is source bytes only | MB-08 check before creating files; SD-20 single-file scope (deps/runtime hashing is project-level) | Mandatory implementation |
| V4 | C | Row 1: non-voided CONFIRMED_DIFF => DIVERGENT_OBSERVABLE first | decide.py:79-81 | test_core.py::test_divergent_return_with_trace; test_precedence_divergent_over_insufficient | Conforms | probe o_div: DIVERGENT, verify 0 | - | Conforms |
| V5 | C | Row 2: any B1..B9 => INSUFFICIENT(primary=min rank; secondary) | decide.py:82-86; records.py:89 | test_core.py::test_decide_baseline_and_missing_evidence; test_property_incomplete_evidence_never_positive | Conforms | rank order tested; secondary listed alphabetically (spec silent) | SD-12 state secondary ordering | Conforms |
| V6 | C | Row 3: else NDO(highest level whose floors hold) | decide.py:65-74,87 | test_core.py::test_s1_and_s2 | Conforms | S1/S2 reachable; S3 refused | - | Conforms |
| V7 | C | Missing record counts as true | decide.py:41-42 | test_core.py::test_decide_baseline_and_missing_evidence | Conforms | each missing field => tool_error | - | Conforms |
| V8 | N | DIVERGENT absorbing; voided only by Supersession (failed audit replay, drift) | none | - | Not implemented | no Supersession record, no audit replay; verify.py recomputes but does not void | Needs audit sampling/Module L | Intentionally deferred |
| V9 | C | Early stop at first witness allowed; sufficiency not scored for DIVERGENT | runner.py:310; decide.py:79 | test_core.py::test_divergent_return_with_trace | Conforms | stop reason 'witness' recorded in package | - | Conforms |
| V10 | D | NDO means every changed unit ran in each version containing it | runner.py:114-126 (_regions), 261-267 | test_phase2_fixes.py::test_docstring_only_is_vacuous_not_a_difference; test_mixed_executable_and_docstring; test_non_executable_non_doc_change_is_unmodelled | Fixed since audit (needs ratification) | probes doc/nolines: NDO S2 with r_empty=True (vacuous); non-executable non-doc line => unmodelled_change | Ratify A-U1/A-16 (UD-2); define 'changed unit' (SD-08) | Specification correction |
| V11 | C | internal_divergence absent when module E off | runner.py:322-325 (no such key) | - | Conforms | probe o_div verdict.json has no internal_divergence | - | Conforms |
| V12 | C | S0 only inside INSUFFICIENT | records.py:86; decide.py:73-74 | test_core.py::test_s0_never_with_no_divergence | Conforms | - | - | Conforms |
| V13 | D | Unknown reason code downgrades to INSUFFICIENT | records.py:87-88 (assert); decide.py:85 (RANK[c] KeyError) | test_core.py::test_verdict_record_rejects_prohibited_values (asserts the raise) | Deviates | probe: `-O` accepted primary='bogus_code' | MB-04: explicit ValueError on write; verify/readers map unknown code to INSUFFICIENT | Mandatory implementation |

### 4.2 Blocking conditions and reason codes

| ID | Audit | Requirement | Implementation (current file:line) | Supporting test | Status now | Evidence | Required correction | Final disposition |
|---|---|---|---|---|---|---|---|---|
| B0 | C | 18-code closed enum, retired codes absent | records.py:8-11 | test_core.py::test_verdict_record_rejects_prohibited_values | Conforms | list equals FS s7 (18) | - | Conforms |
| B0r | C | Ranks B1..B9; tie-break inside a rank | decide.py:7-11,85 | test_core.py::test_decide_baseline_and_missing_evidence | Conforms (A-07) | alphabetical tie-break is code-only | SD-12 add tie-break to FS | Specification correction |
| B1 | C | import_error | runner.py:170,239 | test_core.py::test_import_error_and_entry_missing_and_no_inputs | Conforms | - | - | Conforms |
| B2a | D | alignment_failed | runner.py:250-251 (only if _regions raises) | - | Deviates (defensive only) | after a successful import the source parses, so the branch is effectively unreachable; no test | MB-16 unit test via monkeypatched _regions; SD-16 document as defensive | Mandatory implementation |
| B2b | C | unsupported_signature (entry missing; incompatible sig with probe off) | runner.py:240,243-244 | test_core.py::test_import_error_and_entry_missing_and_no_inputs; test_signature_change | Conforms | - | lifting/rename => G1s/G4s | Conforms |
| B2c | N | ambiguous_entry | none (CLI takes exactly one --entry, __main__.py:13) | - | Not implemented | vacuous with a mandatory single entry | Only arises when entries are inferred (explorer / project scope) | Intentionally deferred |
| B2d | N | unmodelled_change | runner.py:125,249 | test_phase2_fixes.py::test_non_executable_non_doc_change_is_unmodelled | Fixed since audit (single-file scope) | non-executable non-doc changed line => INSUFFICIENT(unmodelled_change) | dependency/config changes are project-level (Phase 3) | Conforms |
| B3a | D | sandbox_failure when a property is violated OR unverified | runner.py:61,236; decide.py:48; isolation.py:109,111-114 | test_isolation.py::test_sandbox_unavailable_is_explicit (isolation layer only) | Deviates | rlimit_as/nproc UNAVAILABLE are silently skipped; only network_denial gates; no verdict-level test | MB-06 under SD-07 (required vs advisory properties) | Mandatory implementation |
| B3b | N | unsafe_program (policy violation, tamper) | runner.py:168,237; decide.py:43-44; harness.py:161 | test_result_protocol.py::test_forged_or_broken_result_is_unsafe_program[*]; test_protocol_violations[*] | Fixed since audit (8f11d3aa) | probe sysexit: os._exit => unsafe_program | same-address-space adversary => I4/I10 (Phase 3) | Conforms |
| B4a | C | flaky_witness (replay disagreed) | runner.py:195-197; decide.py:50 | test_core.py::test_replay_classes (scripted runs) | Conforms | real-program flaky case untested | - | Conforms |
| B4b | D | env_sensitive (control-sensitive, fails k_alt) | runner.py:198-202; harness.py:175-179 | test_core.py::test_replay_classes (scripted) | Deviates | alt runs for every candidate; only random.seed and time.time/_ns shifted; no real-program test | MB-07 extend virtualisation; SD-09 trigger rule | Mandatory implementation |
| B5 | D | nondeterministic: quarantined input that hit/may have hit a changed unit | runner.py:175-176; decide.py:50 | test_core.py::test_nondeterministic_quarantined | Deviates (conservative) | every quarantined input blocks; probes rand/hashseed/uuid: INSUFFICIENT(nondeterministic) | UD-4: adopt conservative reading, define 'may have hit' (A-04) | Specification correction |
| B6 | D | resource_limit: exactly one side ended in a harness limit | runner.py:177-179; decide.py:51 | test_core.py::test_timeout_asymmetric_and_both; test_no_run_input_blocks_no_divergence | Deviates | every NO_RUN except invalid_input adds resource_limit (probe sysexit: unsafe_program + secondary resource_limit) | MB-10 record NO_RUN cause; map only limit causes; UD-4 for both-limit | Mandatory implementation |
| B7a | C | capture_truncated | runner.py:62,74,164-165; decide.py:49 | - | Conforms (probe) | probe trunc: print 40000 chars => INSUFFICIENT(capture_truncated) | MB-16 add test | Conforms |
| B7b | N | blind_spot_dominant / blind spot in a changed unit | none | - | Not implemented | probe subproc: os.write(1,'A') vs 'B' => NDO S2 (observable difference missed) | MB-02 fd-level capture closes the stdout blind spot; residual detector deferred | Mandatory implementation |
| B8a | C | no_inputs | decide.py:53-55 | test_core.py::test_import_error_and_entry_missing_and_no_inputs | Conforms | - | - | Conforms |
| B8b | D | unobservable_outcome (no non-degenerate channel) | decide.py:56-58; runner.py:180-188 | test_core.py::test_degenerate_unobservable; test_phase2_fixes.py::test_lossy_s1_is_insufficient; test_symmetric_binding_failure_is_not_a_same | Fixed since audit (cc56e029) | both-bind-error => NO_RUN(invalid_input); lossy/degenerate SAME => unobservable_outcome; probes lossy, gen | ratify A-L1 (UD-1) | Conforms |
| B8c | C | tool_error (internal failure, never blamed on program) | decide.py:41-42; runner.py:170,241 | test_core.py::test_decide_baseline_and_missing_evidence | Conforms | - | MB-01: canon failures must reach tool_error, not 'raised' | Conforms |
| B9 | C | changed_region_not_activated / budget_exhausted_s0 | decide.py:59-61; runner.py:306-307 | test_core.py::test_budget_exhausted; test_s1_and_s2 | Conforms (partial) | budget flag set only if loop breaks before an input (last input exhausting budget => not_activated) | SD-19 define stop granularity and code selection (A-17) | Specification correction |

### 4.3 Per-input outcomes

| ID | Audit | Requirement | Implementation (current file:line) | Supporting test | Status now | Evidence | Required correction | Final disposition |
|---|---|---|---|---|---|---|---|---|
| O1 | C | Seven per-input outcomes | decide.py:6; runner.py:156-204 | test_core.py::test_replay_classes; test_no_run_input_blocks_no_divergence | Conforms | - | - | Conforms |
| O2 | C | returned/raised/exited/crashed/limit | harness.py:213-218; runner.py:70-80 | test_core.py::test_crash_reproduced_is_witness; test_timeout_asymmetric_and_both | Conforms | - | - | Conforms |
| O3 | D | SystemExit is raised(type,msg); exited(code)=os._exit | harness.py:215-216 | - | Deviates (spec choice) | SystemExit recorded as exited(code); os._exit is now a protocol violation (unsafe_program) | SD-11 adopt as-built; MB-16 test | Specification correction |
| O4 | C | Limits never a witness; both-limit => NO_RUN | runner.py:177-179 | test_core.py::test_timeout_asymmetric_and_both | Conforms | probe bothlimit: INSUFFICIENT | - | Conforms |
| O5 | D | Harness-limit MemoryError => limit(oom), not raised | harness.py:217; isolation.py:192 | - | Deviates | RLIMIT_AS unavailable on macOS (RSS watchdog kills instead); enforceable only on Linux | exact oom class needs RLIMIT_AS (Linux) | Phase 3 dependency |
| O6 | D | Unserialisable value => NO_RUN(unobservable_outcome) | harness.py:214 (canon inside program try) | test_harness_canon.py::test_unobservable_is_lossy_never_s2 | Deviates (residual) | cyclic fixed (probe cyc: DIVERGENT); NEW probe bigint: 10**5000 vs 10**5001 both 'raised ValueError' => NDO S2 (false assurance) | MB-01 canon outside program try; int via hex() | Mandatory implementation |
| O7 | C | Introduced non-termination => INSUFFICIENT(resource_limit) | runner.py:177-179; decide.py:51 | test_core.py::test_timeout_asymmetric_and_both | Conforms | - | - | Conforms |

### 4.4 Observation boundary

| ID | Audit | Requirement | Implementation (current file:line) | Supporting test | Status now | Evidence | Required correction | Final disposition |
|---|---|---|---|---|---|---|---|---|
| C1 | C | C_obs default 6 channels | config.py:4,42; compare.py:51-73 | test_core.py::test_divergent_exception_stdout_and_global; test_comparator_options | Conforms | probe load_config({}) prints the six channels | - | Conforms |
| C2 | C | stderr/perf/lines/tracebacks/run ids excluded | isolation.py (stderr drained, never compared) | - | Conforms (probe) | probe stderr A vs B => NDO S2 | MB-16 add test | Conforms |
| C3 | N | Uninstrumentable channels drop to intersection; empty => unobservable_outcome | none; decide.py:72 constant | - | Not implemented | all six channels are always instrumented in-process; nothing can be configured out | needed only for non-Python/E module | Intentionally deferred |
| C4 | D | Equality on canonical form; user __eq__/__repr__ never called | harness.py:35-64,92-124 | test_harness_canon.py::test_canonicalisation_runs_no_user_code | Fixed since audit (8f11d3aa) | type-level reads only | - | Conforms |
| C5 | C | Type tag is identity | compare.py:14-15; harness.py:75-80 | test_core.py::test_comparator_types | Conforms | - | - | Conforms |
| C6 | C | Floats exact binary64, NaN equal | compare.py:17-23 | test_core.py::test_comparator_types | Conforms | - | - | Conforms |
| C7 | D | Declared tolerance: exact record + tolerance_masked, never pooled | compare.py:21-22 | test_core.py::test_comparator_options (equality only) | Deviates | default tol=0 so no effect; probe tol: 1e-12 diff => DIVERGENT | only if a tolerance is ever declared | Optional functionality |
| C8 | C | Mappings key-order-insensitive; ordered_mapping option | compare.py:33-38 | test_core.py::test_comparator_options | Conforms | - | - | Conforms |
| C9 | C | Sets unordered; sequences ordered | harness.py:106; compare.py:24-25 | test_core.py::test_comparator_types | Conforms | - | - | Conforms |
| C10 | D | Objects: class + __dict__/__slots__ digest to depth 3 | harness.py:92-124 | test_harness_canon.py::test_contents_difference_is_divergent[*] (17 types); test_equal_contents_of_all_supported_types_reach_s2 | Fixed since audit (8f11d3aa) | OrderedDict/namedtuple/slots/defaultdict/deque/Counter now DIVERGENT | SD-15 write the rule into FS (A-15) | Conforms |
| C11 | C | Exceptions: qualified type, normalised message, ignore option | compare.py:61; harness.py:217-218 | test_core.py::test_comparator_options | Conforms | - | - | Conforms |
| C12 | D | Normaliser N: addresses, ids, abs paths, default reprs; declared and versioned | harness.py:17-18 | - | Deviates | N strips 0x addresses and cwd only; no normaliser_id; probe filepath: raise ValueError(__file__) differs by source path => false DIVERGENT | MB-03 normalise source path/dir; MB-13 normaliser_id constant; SD-23 | Mandatory implementation |
| C13 | D | Message-only difference is kind=exception_message | compare.py:61 | test_core.py::test_comparator_options | Deviates (minor) | single kind 'exception' | SD-23 kinds enum is outcome/exception/side_effect/api; message-only is a detail | Specification correction |
| C14 | C | equal_lossy blocks S2 | harness.py:12-13; compare.py:73; decide.py:56-58,71 | test_phase2_fixes.py::test_decide_lossy_same_is_not_evidence; test_lossy_s1_is_insufficient | Conforms (stricter: A-L1 also blocks S1) | - | ratify A-L1 (UD-1) | Conforms |
| C15 | D | stdout is bytes written by the call | harness.py:181-185,204 | - | Deviates (minor) | probe importprint: import-time print difference => DIVERGENT | UD-3: boundary decision | Specification correction |

### 4.5 Witness, replay, signatures

| ID | Audit | Requirement | Implementation (current file:line) | Supporting test | Status now | Evidence | Required correction | Final disposition |
|---|---|---|---|---|---|---|---|---|
| W1 | C | Witness fields | records.py:74-77; runner.py:222-227 | test_core.py::test_divergent_return_with_trace | Conforms | - | - | Conforms |
| W2 | C | kinds priority outcome>exception>side_effect>api | compare.py:6,73 | test_core.py::test_divergent_exception_stdout_and_global | Conforms | - | - | Conforms |
| W3 | N | Witness immutable, voidable only by Supersession | none | - | Not implemented | append-only log; no Supersession | with V8 | Intentionally deferred |
| W4 | D | Witness chain resolves to H, programs, input, environment, policy | runner.py:312-321; records.py:57 | test_phase2_fixes.py::test_package_holds_evidence_not_just_hashes; test_verify_recomputes_every_pair[divergent] | Fixed since audit (cc56e029) | Verdict -> Witness + EvidencePackage (config/H, env, policy, inputs, rows, regions) | separate record kinds => SD-17 | Conforms |
| W5 | C | Locus 'unlocalised' valid | records.py:77 | - | Conforms (probe) | probe: Witness.locus == 'unlocalised' | MB-16 add test | Conforms |
| P1 | C | Step 1: r_det self-consistency, early stop, else QUARANTINED | runner.py:212-217,175-176 | test_core.py::test_nondeterministic_quarantined | Conforms | - | - | Conforms |
| P2 | C | Step 2: r_replay=5 fresh replays, 5/5 reproduce | runner.py:190-197,218-219 | test_core.py::test_replay_classes; test_divergent_return_with_trace | Conforms (cost: all 5 replays run before counting) | - | early stop is a cost optimisation | Optional functionality |
| P3 | C | Agreement on C_obs not trace | runner.py:96-100 | test_core.py::test_replay_classes | Conforms | - | - | Conforms |
| P4 | N | Step 3: build mismatch => inconclusive | none | - | Not implemented | single interpreter per invocation | arises only with multi-host/audit replay | Intentionally deferred |
| P5 | D | Step 4: k_alt alternate control settings | runner.py:198-202; harness.py:175-179 | test_core.py::test_replay_classes (scripted) | Deviates | see B4b | MB-07 | Mandatory implementation |
| P6 | N | Step 5: optional minimisation | none | - | Not implemented | spec: optional | - | Optional functionality |
| P7 | D | All replay processes charged to CPU budget | runner.py:59,306 | - | Deviates | child rusage only; parent time and per-input granularity | MB-11 | Mandatory implementation |
| P8 | C | crashed is a witness only if reproduced in every replay | runner.py:78-80,190-197 | test_core.py::test_crash_reproduced_is_witness | Conforms | - | - | Conforms |
| G1s | D | Compatible signatures proceed (arity/names, defaults added, declared rename) | runner.py:142-144,243 | test_core.py::test_signature_change | Deviates (partial) | declared rename absent (K1 spike: 49 INSUFFICIENT pairs from renamed entries) | additive --variant-entry declaration | Optional functionality |
| G2s | C | api_break_probe: bind failure => kind=api witness | harness.py:206-211; compare.py:57 | test_phase2_fixes.py::test_asymmetric_binding_failure_is_api_witness; test_core.py::test_signature_change | Conforms | - | - | Conforms |
| G3s | D | Inputs valid for one side bound against the other | runner.py:180-182; decide.py:51 | test_phase2_fixes.py::test_symmetric_binding_failure_is_not_a_same; test_decide_invalid_input_never_positive | Fixed since audit (cc56e029, A-B1) | both-bind-error => NO_RUN(invalid_input) | SD-06 ratify A-B1 | Conforms |
| G4s | N | Entry missing in one version: lift to outermost common frame | none (fail-safe branch exists: runner.py:240) | - | Not implemented | fails safe as unsupported_signature(entry_missing) | additive capability | Optional functionality |
| G5s | C | Ungenerable inputs => unsupported_signature, never invented default | config.py:77-92 | test_core.py::test_bad_inputs | Vacuous | no generator exists, inputs are user JSON | moves with explorer/input generation | Intentionally deferred |

### 4.6 Sufficiency

| ID | Audit | Requirement | Implementation (current file:line) | Supporting test | Status now | Evidence | Required correction | Final disposition |
|---|---|---|---|---|---|---|---|---|
| S1a | D | SufficiencyRecord stores factor vector, stop reason, r_det, Merkle root, X_eff, quarantined, unhit, r_empty | runner.py:278-283 | test_phase2_fixes.py::test_verify_recomputes_every_pair | Deviates | floors dict not F1-F4; flat sha256 not Merkle; stop_reason 'inputs_exhausted' outside enum | MB-12; SD-12 add inputs_exhausted | Mandatory implementation |
| S1b | C | Hit = deterministic-confirmed input executed unit; one-sided units | runner.py:261-267 | test_core.py::test_s1_and_s2; test_phase2_fixes.py::test_lossy_input_does_not_activate_changed_units | Conforms | - | - | Conforms |
| S1c | D | Uninstrumentable units unhit; R never shrunk | runner.py:114-126 | test_phase2_fixes.py::test_docstring_only_is_vacuous_not_a_difference; test_non_executable_non_doc_change_is_unmodelled | Fixed since audit (needs ratification) | see V10 | UD-2 | Specification correction |
| S1d | D | r_empty flagged, own stratum | runner.py:281,324 | test_phase2_fixes.py::test_docstring_only_is_vacuous_not_a_difference (asserts r_empty True) | Conforms (field exposed) | stratified reporting is analysis-side | SD-08 definition = no changed unit and nothing unmodelled | Conforms |
| S1e | D | S1: >=1 SAME input valid on both, non-degenerate | decide.py:53-58; runner.py:180-188 | test_core.py::test_degenerate_unobservable; test_phase2_fixes.py::test_symmetric_binding_failure_is_not_a_same | Fixed since audit | - | - | Conforms |
| S1f | C | S1: 100% changed units hit | decide.py:59-61 | test_core.py::test_s1_and_s2 | Conforms | - | - | Conforms |
| S1g | D | S1: r_det per input; no quarantined input that may hit | decide.py:50; runner.py:175-176 | test_core.py::test_nondeterministic_quarantined | Deviates (conservative) | see B5 | UD-4 | Specification correction |
| S1h | D | S1: tier >= L0 (FS) / L1 (SPEC) with changed-region bitmap | runner.py:89-90,261 | - | Deviates | hit lines and branch directions per run in Run.meta; no tier field | SD-08: tier L0 + hit-line set is the bitmap (A-05) | Specification correction |
| S1i | D | S1: no truncation, no blind spot, tamper flag clear | decide.py:43-44,49; runner.py:83,321 | test_result_protocol.py::test_forged_or_broken_result_is_unsafe_program; (truncation untested) | Partial | tamper and truncation wired; blind spot absent | MB-02 | Mandatory implementation |
| S2a | C | Direction coverage >= 0.80 of statically reachable directions per version | runner.py:129-139,268-272 | test_core.py::test_s1_and_s2 (single branch) | Conforms (approximation) | all directions treated reachable; vacuous => 1.0 | SD-22 document; MB-16 multi-branch/loop/one-sided tests | Specification correction |
| S2b | C | Every contributing input deterministic-confirmed | decide.py:50-52 | test_core.py::test_nondeterministic_quarantined | Conforms | - | - | Conforms |
| S2c | N | All declared channels instrumented | decide.py:72 (constant True) | - | Not implemented | probe subproc shows an uninstrumented fd-level path | MB-02 closes the known gap; flag then truthful | Mandatory implementation |
| S2d | C | No equal_lossy on ret/side | decide.py:71 | test_core.py::test_s1_not_s2_when_lossy | Conforms (any channel) | - | - | Conforms |
| S3 | C | s3_enabled=false default; plateau/L2/corroboration | config.py:35-37; records.py:86 | test_core.py::test_bad_config[s3 true] | Conforms (disabled) | probe: s3_enabled=true refused | SD-16 state refusal in FS | Intentionally deferred |
| S0 | C | S0 label only inside INSUFFICIENT | decide.py:73-74 | test_core.py::test_s0_never_with_no_divergence | Conforms | - | - | Conforms |

### 4.7 Evidence model and modules

| ID | Audit | Requirement | Implementation (current file:line) | Supporting test | Status now | Evidence | Required correction | Final disposition |
|---|---|---|---|---|---|---|---|---|
| E1 | C | evidence_class on every record; status qualifier | records.py:31-32,38 | test_phase2_fixes.py::test_package_holds_evidence_not_just_hashes | Conforms (probe) | probe: every kind has a class; status only on SufficiencyRecord | - | Conforms |
| E2 | D | Class per record kind; ChangedRegions, SourceMapping, ReplayCheck, Reproducibility, HarnessDeclaration, Input, ExplorationLog, Completeness records | records.py:57; runner.py:312-315 | test_phase2_fixes.py::test_package_holds_evidence_not_just_hashes | Deviates (folded) | equivalents live inside EvidencePackage body | SD-17 mapping table | Specification correction |
| E3 | D | DIVERGENT chain: Verdict, Witness, runs, replays, H, programs, input, env, policy | runner.py:316-321 | test_phase2_fixes.py::test_verify_recomputes_every_pair[divergent] | Fixed since audit | - | - | Conforms |
| E4 | D | NDO chain: SufficiencyRecord -> root + rows, completeness, regions, log, H | runner.py:318-321 | test_phase2_fixes.py::test_verify_recomputes_every_pair[s2,s1] | Fixed since audit | per-input rows in package | - | Conforms |
| E5 | D | INSUFFICIENT chain: records that triggered each blocker | runner.py:278-283 (blockers [code, detail]) | test_phase2_fixes.py::test_verify_recomputes_every_pair[no_inputs,unhit] | Partial | blocker detail names input id; refs include all runs | SD-17 | Specification correction |
| E6 | N | T4: recompute verdict from the chain | verify.py:32-92 | test_phase2_fixes.py::test_verify_recomputes_every_pair; test_verify_detects_rehashed_forgeries; test_verify_divergent_forged_to_same | Fixed since audit (cc56e029) | probe: verify o_div => verified true | - | Conforms |
| E7 | U | T6: no label-namespace record reachable | none (grep: no label records in sbgv7) | - | Unverifiable | vacuously true today; enforcement belongs to Module L/K | Phase 3 audit tooling | Phase 3 dependency |
| E8 | N | Store replay recipe + hashed event stream (~300 B/run) | runner.py:88-90 (summary + hit lines) | - | Not implemented | inputs+config+sources are stored (recipe implicit); no event stream | needed for 5% audit replay | Intentionally deferred |
| E9 | D | Hash chain tamper detection | records.py:97-119; verify.py:32-58 | test_phase2_fixes.py::test_verify_detects_plain_edit_and_truncation; test_verify_detects_rehashed_forgeries | Fixed since audit | ids re-derived; log_head in verdict.json; unkeyed (writer who recomputes the chain can forge: documented) | pin log_head out of band | Conforms |
| E10 | N | Chain hash excludes run id/repeat index (EV-13) | none | - | Not implemented | refers to a per-run event-stream chain_root that does not exist | SD-14 define the two chains; retire EV-13 until streams exist | Specification correction |
| E11 | D | verify_chain, replay(recipe) | verify.py:32-92 | test_phase2_fixes.py::test_verify_cli_exit_codes | Partial | verify done; replay(recipe) absent | replay with audit (Phase 3) | Intentionally deferred |
| M1 | N | Core modules A,B,C,D,G,H,I,K,L | sbgv7/*.py | - | Partial | B=harness+isolation, C=changed_lines import, D=records+verify, H=runner.classify, I=decide; A,G absent; K,L evaluation-side | A and G deferred; K, L Phase 3 | Intentionally deferred |
| M2 | C | Module I sole Verdict writer | runner.py:321 (only R.Verdict call) | test_core.py::test_verdict_record_rejects_prohibited_values | Conforms | grep: single call site | - | Conforms |
| M3 | C | Dependencies acyclic | imports | - | Conforms (probe) | all modules import; verify imports runner, not vice versa | - | Conforms |

### 4.8 Isolation

| ID | Audit | Requirement | Implementation (current file:line) | Supporting test | Status now | Evidence | Required correction | Final disposition |
|---|---|---|---|---|---|---|---|---|
| I1 | D | Fresh child, CPython 3.13, -I, scrubbed env, private cwd, pinned control env | isolation.py:117-118,127 | test_isolation.py::test_ok_and_callable | Deviates (partial) | no 3.13 check; no PYTHONHASHSEED/TZ/LC_ALL/thread pin | MB-07 | Mandatory implementation |
| I2 | D | setrlimit CPU/FSIZE/NPROC/NOFILE/CORE + RSS watchdog | isolation.py:111-115,163-168,294 | test_isolation.py::test_cpu_rlimit; test_memory_limit_200mb_or_less; test_memory_rlimit_as_hard (skipped) | Deviates | RLIMIT_AS/NPROC unavailable on macOS | enforcement on Linux; required-vs-advisory mapping = MB-06/SD-07 | Phase 3 dependency |
| I3 | C | Process-group kill | isolation.py:87-100,127 | test_isolation.py::test_child_process_survival; test_spin_wall_timeout | Conforms (setsid escape untested) | - | setsid fixture Phase 3 (I10) | Conforms |
| I4 | D | Tracing outside user-code reach with tamper detection | harness.py:143-167; runner.py:168,237 | test_result_protocol.py::test_forged_or_broken_result_is_unsafe_program; test_settrace_evasion_behaviour_unchanged | Partial (protocol fixed; same address space) | docs/architecture/V7B_RESULT_PROTOCOL.md states the limit | out-of-process tracing + Linux hostile fixtures | Phase 3 dependency |
| I5 | C | Network denial (macOS sandbox-exec; Linux --network none) | sandbox_darwin.sb:2; isolation.py:296-309 | test_isolation.py::test_network_denied | Conforms (macOS only) | no Linux path (fails closed) | Linux path Phase 3 | Conforms |
| I6 | C | Write confinement to private tmp | sandbox_darwin.sb:3-7 | test_isolation.py::test_write_outside_denied | Conforms (writes) | reads unconfined | - | Conforms |
| I7 | D | Exact failure classification | isolation.py:183-200 | test_isolation.py::test_cpu_rlimit; test_memory_limit_200mb_or_less | Deviates | stderr substring and CPU-time heuristics; no policy_violation/oom/base_exception | exact classes need Linux enforcement | Phase 3 dependency |
| I8 | C | macOS runs flagged policy_below_minimum | runner.py:282,324 | test_core.py::test_s1_and_s2 (accepts True or False) | Conforms (weak test) | probe: flag true in verdict.json | MB-16 assert True on darwin | Mandatory implementation |
| I9 | U | Legacy runner/tracer is v6_compat, invalid evidence | none (sbgv7 imports only sbgv6.features.changed_lines) | - | Unverifiable | no legacy runner reachable from sbgv7 | tag if a legacy path is ever re-admitted | Intentionally deferred |
| I10 | U | Hostile fixtures: zero escapes, no stray processes | tests/v7/test_result_protocol.py; test_isolation.py::test_no_stray_processes | test_result_protocol.py::test_forged_or_broken_result_is_unsafe_program[*] | Unverifiable | no fixture for setsid, subprocess escape, sys.monitoring tamper, fork bomb | hard G1 gate on Linux | Phase 3 dependency |

### 4.9 Config

| ID | Audit | Requirement | Implementation (current file:line) | Supporting test | Status now | Evidence | Required correction | Final disposition |
|---|---|---|---|---|---|---|---|---|
| F1 | C | harness.c_obs 6 channels | config.py:42 | - | Conforms (probe) | probe load_config({}) equals FS defaults | MB-16 defaults test | Conforms |
| F2 | N | harness.normaliser_id | none | - | Not implemented | identity via harness_sha only | MB-13 accept constant | Mandatory implementation |
| F3 | C | float_tol rel=0,abs=0 | config.py:42 | test_core.py::test_comparator_options | Conforms (probe) | - | - | Conforms |
| F4 | C | ordered_mapping=false | config.py:43 | test_core.py::test_comparator_options | Conforms (probe) | - | - | Conforms |
| F5 | C | exc_message=exact_normalised | config.py:43 | test_core.py::test_comparator_options | Conforms (probe) | - | - | Conforms |
| F6 | N | stderr=excluded | none | - | Not implemented | behaviour is implicit | MB-13 accept constant | Mandatory implementation |
| F7 | N | capture_tier=L0(+bitmap) | none | - | Not implemented | implicit | MB-13 accept constant; SD-08 | Mandatory implementation |
| F8 | C | api_break_probe=true | config.py:44 | test_phase2_fixes.py::test_asymmetric_binding_failure_is_api_witness | Conforms (probe) | - | - | Conforms |
| F9 | C | r_det=3, r_replay=5, k_alt=3 | config.py:45 | - | Conforms (probe) | probe defaults | MB-16 defaults test | Conforms |
| F10 | C | s2_branch_floor=0.80 | config.py:46 | test_core.py::test_s1_and_s2 | Conforms (probe) | - | - | Conforms |
| F11 | N | s3_plateau_window, static_match_f1_trigger, witness_outside_R_diag | none | - | Not implemented | S3 and static-match diagnostics are not built | SD-18 mark reserved | Intentionally deferred |
| F12 | C | s3_enabled=false | config.py:35-37,46 | test_core.py::test_bad_config[s3 true] | Conforms | - | - | Conforms |
| F13 | D | budget unit/grid=[10,60,300]/headline=60 | config.py:47 | - | Deviates | single cpu_seconds=60; grid is an evaluation-protocol parameter | SD-18 | Specification correction |
| F14 | D | per_run claims_cpu_s=10, fast_cpu_s=2 | config.py:48 | - | Deviates | single cpu_s=10; K1 spike passed 2 explicitly | SD-18 map claims/fast to cpu_s overrides | Specification correction |
| F15 | C | per_run wall_s=20, rss_mib=2048 | config.py:48-49 | - | Conforms (probe) | - | - | Conforms |
| F16 | N | per_run max_events_L1=200000 | none | - | Not implemented | tier L1 absent | with L1/S3 | Intentionally deferred |
| F17 | N | seeds, stats, platform blocks | none | - | Not implemented | explorer and evaluation-side | - | Intentionally deferred |
| F18 | D | Verdict identity includes all of H (repeat counts, floors, policy, control profile, tier) | runner.py:47,52; verify.py:59-60 | test_core.py::test_repeated_runs_reproduce_ids_and_chain | Deviates | h_id hashes harness section + harness.py only; r_det=1 and r_det=3 share a pair_id | MB-09 | Mandatory implementation |

### 4.10 Gates, CLI, determinism

| ID | Audit | Requirement | Implementation (current file:line) | Supporting test | Status now | Evidence | Required correction | Final disposition |
|---|---|---|---|---|---|---|---|---|
| X1 | U | Gates G0-G8, K1-K5 | experiments/v7b/k1_spike.py, scripts/analyze_results.py (evaluation-side) | - | Unverifiable | K1 NOT MET on existing data; formal evaluation needs Phase 3 inputs | see K1_K5_READINESS_AND_DECISION.md | Phase 3 dependency |
| X2 | D | CLI exit codes | __main__.py:16-38 | test_core.py::test_cli; test_phase2_fixes.py::test_verify_cli_exit_codes | Deviates | probe: --out is a file => FileExistsError traceback (exit 1); INSUFFICIENT and DIVERGENT exit 0 | MB-14; SD-13 | Mandatory implementation |
| X3 | C | Determinism: same inputs/config => same ids | records.py:62-67 | test_core.py::test_repeated_runs_reproduce_ids_and_chain | Conforms (probe) | probe: ids equal across two invocations | - | Conforms |
| X4 | D | Artefact determinism | records.py:35; runner.py:89-90,325 | - | Deviates (by design) | probe: log_head differs (timings in hashed meta); ids equal | SD-14 define reproducibility as ids/verdict, not chain bytes | Specification correction |
| X5 | N | Seeds: exploration_seed pre-declared | none | - | Not implemented | no explorer | - | Intentionally deferred |
| X6 | N | Determinism controls for primary runs | isolation.py:118 | - | Not implemented | probe hashseed: set-of-str order => nondeterministic | MB-07 | Mandatory implementation |

## 5. Disposition of the audit's deviation groups

### 45 deviations (audit status D)

Counts: Mandatory implementation 15; Specification correction 13; Conforms 10; Phase 3 dependency 4; Optional functionality 2; Intentionally deferred 1.

| ID | Now | Disposition |
|---|---|---|
| V3 | Deviates | Mandatory implementation |
| V10 | Fixed since audit (needs ratification) | Specification correction |
| V13 | Deviates | Mandatory implementation |
| B2a | Deviates (defensive only) | Mandatory implementation |
| B3a | Deviates | Mandatory implementation |
| B4b | Deviates | Mandatory implementation |
| B5 | Deviates (conservative) | Specification correction |
| B6 | Deviates | Mandatory implementation |
| B8b | Fixed since audit (cc56e029) | Conforms |
| O3 | Deviates (spec choice) | Specification correction |
| O5 | Deviates | Phase 3 dependency |
| O6 | Deviates (residual) | Mandatory implementation |
| C4 | Fixed since audit (8f11d3aa) | Conforms |
| C7 | Deviates | Optional functionality |
| C10 | Fixed since audit (8f11d3aa) | Conforms |
| C12 | Deviates | Mandatory implementation |
| C13 | Deviates (minor) | Specification correction |
| C15 | Deviates (minor) | Specification correction |
| W4 | Fixed since audit (cc56e029) | Conforms |
| P5 | Deviates | Mandatory implementation |
| P7 | Deviates | Mandatory implementation |
| G1s | Deviates (partial) | Optional functionality |
| G3s | Fixed since audit (cc56e029, A-B1) | Conforms |
| S1a | Deviates | Mandatory implementation |
| S1c | Fixed since audit (needs ratification) | Specification correction |
| S1d | Conforms (field exposed) | Conforms |
| S1e | Fixed since audit | Conforms |
| S1g | Deviates (conservative) | Specification correction |
| S1h | Deviates | Specification correction |
| S1i | Partial | Mandatory implementation |
| E2 | Deviates (folded) | Specification correction |
| E3 | Fixed since audit | Conforms |
| E4 | Fixed since audit | Conforms |
| E5 | Partial | Specification correction |
| E9 | Fixed since audit | Conforms |
| E11 | Partial | Intentionally deferred |
| I1 | Deviates (partial) | Mandatory implementation |
| I2 | Deviates | Phase 3 dependency |
| I4 | Partial (protocol fixed; same address space) | Phase 3 dependency |
| I7 | Deviates | Phase 3 dependency |
| F13 | Deviates | Specification correction |
| F14 | Deviates | Specification correction |
| F18 | Deviates | Mandatory implementation |
| X2 | Deviates | Mandatory implementation |
| X4 | Deviates (by design) | Specification correction |

### 23 not implemented (status N)

Counts: Intentionally deferred 11; Mandatory implementation 6; Conforms 3; Optional functionality 2; Specification correction 1.

| ID | Now | Disposition |
|---|---|---|
| V8 | Not implemented | Intentionally deferred |
| B2c | Not implemented | Intentionally deferred |
| B2d | Fixed since audit (single-file scope) | Conforms |
| B3b | Fixed since audit (8f11d3aa) | Conforms |
| B7b | Not implemented | Mandatory implementation |
| C3 | Not implemented | Intentionally deferred |
| W3 | Not implemented | Intentionally deferred |
| P4 | Not implemented | Intentionally deferred |
| P6 | Not implemented | Optional functionality |
| G4s | Not implemented | Optional functionality |
| S2c | Not implemented | Mandatory implementation |
| E6 | Fixed since audit (cc56e029) | Conforms |
| E8 | Not implemented | Intentionally deferred |
| E10 | Not implemented | Specification correction |
| M1 | Partial | Intentionally deferred |
| F2 | Not implemented | Mandatory implementation |
| F6 | Not implemented | Mandatory implementation |
| F7 | Not implemented | Mandatory implementation |
| F11 | Not implemented | Intentionally deferred |
| F16 | Not implemented | Intentionally deferred |
| F17 | Not implemented | Intentionally deferred |
| X5 | Not implemented | Intentionally deferred |
| X6 | Not implemented | Mandatory implementation |

### 4 unverifiable (status U)

Counts: Phase 3 dependency 3; Intentionally deferred 1.

| ID | Now | Disposition |
|---|---|---|
| E7 | Unverifiable | Phase 3 dependency |
| I9 | Unverifiable | Intentionally deferred |
| I10 | Unverifiable | Phase 3 dependency |
| X1 | Unverifiable | Phase 3 dependency |

## 6. Code deviation register D-01..D-23

| ID | Audit severity | Deviation | Status at HEAD cc56e029 | Final disposition | Action |
|---|---|---|---|---|---|
| D-01 | Blocking | Canonicalisation dropped dict/list subclass and __slots__ contents | FIXED 8f11d3aa: 24 tests in test_harness_canon.py (17 types differ => DIVERGENT; probe cyc DIVERGENT). Residual found by this review: NF-01 (big ints), tracked as MB-01. | Invalid or obsolete finding | obsolete; residual => MB-01 |
| D-02 | Blocking (G1 gate) | Forgeable result channel; tamper flag discarded | FIXED 8f11d3aa for forged/broken frames (HMAC frame on a private fd; 25 tests in test_result_protocol.py; tamper wired at runner.py:274, decide.py:43). A same-address-space adversary remains (documented in V7B_RESULT_PROTOCOL.md). | Invalid or obsolete finding | obsolete for protocol forgery; adversarial residual => I4/I10 (Phase 3) |
| D-03 | Major | Unverified isolation properties do not give sandbox_failure | OPEN: isolation.py:111-114 skips unavailable limits; runner.py:61 gates only network denial. The audit's 3 GiB probe now ends INSUFFICIENT(resource_limit) via the RSS watchdog, but the structural gap stands. | Mandatory implementation | MB-06 under SD-07 |
| D-04 | Moderate | NO_RUN of any cause mapped to resource_limit; any quarantine blocks | OPEN: decide.py:50-51; probe sysexit shows secondary resource_limit for a protocol violation. | Mandatory implementation | MB-10 (cause reporting); conservative policy => UD-4 |
| D-05 | Major | R shrunk to executable lines | FIXED cc56e029 (A-U1): docstring lines vacuous, other non-executable lines => unmodelled_change; 5 tests in test_phase2_fixes.py. | Invalid or obsolete finding | obsolete; ratify A-U1 (UD-2) |
| D-06 | Major | Both-side bind_error counted as SAME | FIXED cc56e029 (A-B1): NO_RUN(invalid_input); test_symmetric_binding_failure_is_not_a_same, test_decide_invalid_input_never_positive. | Invalid or obsolete finding | obsolete; ratify A-B1 (SD-06) |
| D-07 | Moderate | Canonicalisation errors reported as 'raised' | PARTLY FIXED: cycles are structural. NEW probe bigint (10**5000 vs 10**5001) still NDO S2 because str(int) raises ValueError inside the program try (harness.py:76,214). | Mandatory implementation | MB-01 |
| D-08 | Moderate | Harness MemoryError / sandbox denial become program outcomes | OPEN. RLIMIT_AS is unavailable on macOS, so the harness-limit MemoryError case is Linux-only; sandbox denial surfaces as PermissionError (a program outcome). | Phase 3 dependency | Linux enforcement; denial detection with container/seccomp |
| D-09 | Major | Evidence log cannot reproduce or re-verify a verdict | FIXED cc56e029: EvidencePackage + `sbgv7 verify` (6 forgery tests). Residual: no event stream, no separate record kinds, unkeyed chain. | Invalid or obsolete finding | obsolete; residual => SD-17, E8 deferred |
| D-10 | Moderate | Verdict identity omits repeat counts, floors, policy | OPEN: runner.py:47,52. | Mandatory implementation | MB-09 |
| D-11 | Moderate | Config schema differs from FS s11; spec-shaped config rejected | OPEN; probe: unknown key(s) ['capture_tier','normaliser_id','stderr']. | Mandatory implementation | MB-13 (+SD-18 reserved list) |
| D-12 | Moderate | Output created before identity check; overwrite policy differs CLI vs library | OPEN; probe: rc1=3 leaves evidence.jsonl, rc2=2. | Mandatory implementation | MB-08 |
| D-13 | Moderate | Budget: parent time uncharged; per-input granularity | OPEN: runner.py:59,306. | Mandatory implementation | MB-11 (+SD-19) |
| D-14 | Moderate | No control profile; alt runs cover random/time only | OPEN; probe hashseed: INSUFFICIENT(nondeterministic). | Mandatory implementation | MB-07 (+SD-09) |
| D-15 | Minor | SystemExit recorded as exited | OPEN: harness.py:215-216. | Specification correction | SD-11 adopt as-built |
| D-16 | Moderate | S2 'all channels instrumented' constant True | OPEN; probe subproc: differing os.write(1) output => NDO S2. | Mandatory implementation | MB-02 |
| D-17 | Minor | Tolerance semantics missing | OPEN; default 0, no effect. | Optional functionality | only if a tolerance is ever declared |
| D-18 | Minor | Invariants are assert; unknown code raises | OPEN; probe: python -O accepts EQUIVALENT and 'bogus_code'. | Mandatory implementation | MB-04 |
| D-19 | Minor (raised to Moderate) | Normaliser narrower than spec; source path leaks into messages | OPEN; probe filepath: false DIVERGENT from __file__ in a message. Severity raised because it can mint a false witness. | Mandatory implementation | MB-03 |
| D-20 | Minor | Replays run to completion; secondary order alphabetical | OPEN; cost only. | Optional functionality | early stop optional; ordering => SD-12 |
| D-21 | Moderate | Weak chain verification | FIXED cc56e029: id re-derivation, must-end-with-Verdict, log_head check, tail-truncation test. | Invalid or obsolete finding | obsolete; unkeyed chain documented |
| D-22 | Minor | stop_reason 'inputs_exhausted' outside enum; r_empty not in verdict.json | r_empty now exposed (runner.py:324); enum value still outside the SPEC list. | Specification correction | SD-12 add value |
| D-23 | Minor | Static layer is V6 code | OPEN: runner.py:7; verify recomputes with the live sbgv6 code, so a change there silently breaks verification. | Mandatory implementation | MB-15 record a digest of sbgv6/features.py in the package |

Counts: Invalid or obsolete finding 6; Mandatory implementation 12; Phase 3 dependency 1; Specification correction 2; Optional functionality 2.

## 7. Specification ambiguities A-01..A-18

All 18 are specification-side. None is silently chosen: those that change what a verdict asserts are user decisions (UD-n); the rest carry a recommendation in `FINAL_SPECIFICATION_DECISIONS.md`.

| ID | Severity | Problem | Final disposition | Where decided |
|---|---|---|---|---|
| A-01 | Major | macOS rlimit_as/nproc cannot be verified; 'unverified => sandbox_failure' vs 'macOS allowed' | Specification correction | SD-07 required vs advisory set (+MB-06) |
| A-02 | Moderate | NO_RUN semantics vs B table | Specification correction | SD-21 / UD-4 |
| A-03 | Major | 'Changed unit' granularity | Specification correction | SD-08 |
| A-04 | Minor | 'may have hit' undefined | Specification correction | UD-4 |
| A-05 | Moderate | Tier L0 (FS) vs L1 (SPEC) | Specification correction | SD-08: L0 + hit-line set |
| A-06 | Minor | Entry missing: import_error vs unsupported_signature | Specification correction | SD-12: s5 wins |
| A-07 | Minor | B8 omits import_error; no tie-break | Specification correction | SD-12 |
| A-08 | Minor | exited vs raised(SystemExit) | Specification correction | SD-11 |
| A-09 | Moderate | Control profile absent from FS s11; k_alt trigger | Specification correction | SD-09 (+MB-07) |
| A-10 | Moderate | 'Hash chain' names two objects | Specification correction | SD-14 |
| A-11 | Moderate | No CLI contract | Specification correction | SD-13 (+MB-14) |
| A-12 | Minor | S3 listed in row 3 while disabled; refusal unspecified | Specification correction | SD-16 |
| A-13 | Minor | Does r_det=3 count the primary run | Specification correction | SD-12: 3 runs per side in total (as built) |
| A-14 | Moderate | Sandbox violation on a replay/alt run vs a witness | Specification correction | SD-10 (+MB-05) |
| A-15 | Major | Container subclass/opaque canonical rule | Specification correction | SD-15 (code already fixed) |
| A-16 | Moderate | Vacuous branch coverage satisfies the 0.80 floor | Specification correction | UD-2 |
| A-17 | Minor | Budget stop granularity / budget_exhausted_s0 choice | Specification correction | SD-19 |
| A-18 | Minor | Intermittent crash vs QUARANTINED order | Specification correction | SD-12: QUARANTINED first (as built) |

## 8. Open items OI-01..OI-22

| ID | Item | Final disposition | Note |
|---|---|---|---|
| OI-01 | S2 needs all declared channels instrumented; constant True | Mandatory implementation | MB-02 |
| OI-02 | F4 diversity/budget has no floor; S2 reachable from 2 inputs | Specification correction | SD-16: F4 reported-only until development calibration (floors change only via the development split) |
| OI-03 | No hashed event stream | Intentionally deferred | E8 |
| OI-04 | Flat hash instead of Merkle root | Mandatory implementation | MB-12 |
| OI-05 | No Supersession | Intentionally deferred | V8/W3 |
| OI-06 | Reason codes never produced; no ChangedRegions record | Mandatory implementation | unsafe_program and unmodelled_change are now produced (obsolete part); blind_spot_dominant => MB-02 (+DEF detector); ambiguous_entry DEF; ChangedRegions folded into the package (SD-17) |
| OI-07 | Config fields of FS s11 not exposed | Specification correction | SD-18 reserved list + MB-13 |
| OI-08 | ineligible:identical covers the source file only | Specification correction | SD-20 (+MB-08) |
| OI-09 | NO_RUN and LIMIT_ASYMMETRIC both map to resource_limit | Mandatory implementation | MB-10; policy UD-4 |
| OI-10 | B5: any quarantined input blocks | Specification correction | UD-4 |
| OI-11 | r_empty recorded, not stratified | Intentionally deferred | engine exposes it (runner.py:324); stratified reporting is evaluation-side |
| OI-12 | Control alternation virtualises random/time only | Mandatory implementation | MB-07 |
| OI-13 | Build mismatch => inconclusive absent | Intentionally deferred | P4 |
| OI-14 | Isolation completion (Linux, RLIMIT, reads, setsid) | Phase 3 dependency | I2,I4,I5,I7,I10; macOS required/advisory => SD-07/MB-06 |
| OI-15 | Entry lifting, declared rename, ambiguous_entry, ungenerable types | Optional functionality | G1s,G4s,B2c,G5s |
| OI-16 | Budget exhaustion gating | Specification correction | SD-19 |
| OI-17 | S2 direction coverage approximation | Specification correction | SD-22 |
| OI-18 | Tier/bitmap structure | Specification correction | SD-08 |
| OI-19 | Test-count and CPU drift across reports | Specification correction | Current suite: 169 collected, 168 passed + 1 skipped (rlimit_as) in about 40 s (this review). Reports outside this task's ownership still quote 74/75/85/91; their owners must update |
| OI-20 | Tracer tamper; os.write(1)/subprocess bypass stdout capture | Mandatory implementation | MB-02 for the bypass (probe-confirmed); protocol tamper obsolete (fixed); adversarial residual P3 |
| OI-21 | K1 NOT MET on dev data vs STOP | Phase 3 dependency | UD-5; see K1_K5_READINESS_AND_DECISION.md |
| OI-22 | evidence_class on every record | Conforms | probe: Verdict/Witness/EvidencePackage/ProgramVersion/SufficiencyRecord derived; Run/Observation observation (records.py:31,38); status only on SufficiencyRecord |

Counts: Mandatory implementation 6; Specification correction 8; Intentionally deferred 4; Phase 3 dependency 2; Optional functionality 1; Conforms 1.

## 9. Explicit reconciliation by topic

### 9.1 Sufficiency S0, S1, S2, S3
- **S0** is a label for "an S1 floor fails", present only inside `INSUFFICIENT` (`decide.py:73-74`, `records.py:86`; `test_s0_never_with_no_divergence`). In the log it is `SufficiencyRecord.body.level`; the `Verdict.level` is null. Conforms.
- **S1** as built (`decide.py:39-62`): at least one clean `SAME` input (valid on both versions, deterministic-confirmed, not degenerate and, by amendment A-L1, not lossy-canonicalised), 100 % of changed units hit by such inputs, no quarantined or `NO_RUN` input, no truncation, tamper flag clear. Not built: tier/bitmap record (SD-08), blind-spot floor (MB-02).
- **S2** as built: S1 and per-version direction coverage of changed lines >= `s2_branch_floor` (0.80; conservative approximation, all directions counted reachable; vacuous coverage = 1.0), no lossy input, and a channels-instrumented flag that is a constant `True` (`decide.py:72`; MB-02 makes it truthful for the known gap). F4 (input diversity/budget) has no floor, so S2 is reachable from two inputs (SD-16: reported-only until development calibration).
- **S3**: disabled, `s3_enabled=true` is refused (`config.py:35-37`; probe `o_s3`). Maximum emitted level is S2. Intentionally deferred; the corroboration clause is flagged invented/unvalidated in the SPEC.
- Calibration claims (miss-rate caps S1 0.35, S2 0.20, S3 0.10, ECE 0.05) are untested and are not claimed (Phase 3 evaluation).

### 9.2 Explorer, input generation, optional state module
- **Explorer (module A)**: absent. Inputs are a user-supplied JSON list (`config.py:77-92`). X5/F17/G5s are deferred; K3 and K4 cannot be evaluated without it. Dev-data inputs came from a label-free battery in `experiments/` outside `sbgv7/`.
- **Input generation**: absent; the rule "ungenerable types give `unsupported_signature`, never an invented default" is vacuous today. Tuples, sets and objects cannot be supplied. Intentionally deferred (Phase 3 with the explorer).
- **Optional state module (E)**: absent; `internal_divergence` is never emitted (probe `o_div`; V11). Intentionally deferred: the FS places V7-A outside the freeze.

### 9.3 Reason codes: produced versus never produced (18 codes)
| Code | Produced? | Where | Evidence |
|---|---|---|---|
| import_error | yes | `runner.py:170,239` | `test_import_error_and_entry_missing_and_no_inputs` |
| unsupported_signature | yes | `runner.py:240,244` | same; `test_signature_change` |
| ambiguous_entry | **never** | CLI takes one `--entry` | deferred (B2c) |
| alignment_failed | defensive only | `runner.py:250-251` | no test; effectively unreachable (MB-16) |
| unmodelled_change | yes (since cc56e029) | `runner.py:125,249` | `test_non_executable_non_doc_change_is_unmodelled` |
| sandbox_failure | yes | `runner.py:61,236`, `decide.py:48` | isolation-layer test only; no verdict-level test; unverified rlimits do not trigger it (MB-06) |
| unsafe_program | yes (since 8f11d3aa) | `runner.py:168,237`, `decide.py:43-44` | `test_result_protocol.py` (25 tests) |
| flaky_witness | yes | `decide.py:50` | scripted `classify` test only |
| env_sensitive | yes | `runner.py:198-202` | scripted test only; every candidate gets alt runs |
| nondeterministic | yes | `runner.py:175-176` | `test_nondeterministic_quarantined`; probes rand/hashseed/uuid |
| resource_limit | yes | `runner.py:177-179`, `decide.py:51` | also added for non-limit `NO_RUN` causes (MB-10) |
| capture_truncated | yes | `runner.py:62,74` | probe `trunc`; no test (MB-16) |
| blind_spot_dominant | **never** | - | probe `subproc` shows the gap (MB-02) |
| no_inputs | yes | `decide.py:53-55` | tests |
| unobservable_outcome | yes | `decide.py:56-58` | tests; probes lossy, gen |
| changed_region_not_activated | yes | `decide.py:59-61` | tests |
| budget_exhausted_s0 | yes (partial) | `decide.py:60`, `runner.py:306-307` | `test_budget_exhausted` |
| tool_error | yes | `decide.py:41-42`, `runner.py:170,241` | tests; canon failures do not reach it (MB-01) |
Never produced: 2 (`ambiguous_entry`, `blind_spot_dominant`). Produced but not exercised end to end by a verdict-level test: `alignment_failed`, `capture_truncated`, `sandbox_failure`, `flaky_witness`, `env_sensitive`.

### 9.4 Witness generation
`runner.process_input` runs r_det repeats per side (early stop), `classify` decides the outcome, then 5 fresh replays per side and `k_alt=3` alternate-control runs per side; all must reproduce each side's primary observation; a `Witness` is written with kinds, both observations, the replay set, env/policy ids and `locus="unlocalised"` (`runner.py:207-228`, `records.py:74-77`). Verified by `test_divergent_*`, `test_crash_reproduced_is_witness`, `test_replay_classes`, `verify` on a divergent pair, and probe `o_div`. Gaps: a witness is issued even if a replay/alt run was not sandbox-verified (NF-04, MB-05); alt runs are only `random.seed` and a shifted `time.time` (MB-07); no minimisation (optional), no Supersession (deferred), no build-mismatch `inconclusive` (deferred).

### 9.5 Provenance
Chain: `Verdict -> {Witness | SufficiencyRecord} + EvidencePackage -> Runs -> Observations/ProgramVersions`. `ProgramVersion.meta.src` stores source (cap 1 MiB), `EvidencePackage` stores config/H, harness digest, env, policy, inputs (cap 256 KiB each), rows, regions, stop reason, tamper flag. `python -m sbgv7 verify DIR` re-derives outcomes, regions and the verdict and checks ids and the chain (probe: `verified: true`; 6 forgery tests). Gaps: no digest of the V6 `changed_lines` code used for regions (MB-15); no event stream or replay recipe (deferred); chain is unkeyed (a writer who recomputes the whole chain can forge a consistent log; pin `log_head` out of band); over-cap items make verify exit 4.

### 9.6 Verdict taxonomy
Three values only (`records.py:7`), enforced by `assert` (stripped under `-O`: MB-04). Prohibited words are not representable as values. Strata that the FS says are reported separately (`api`, `resource_limit`, `r_empty`) are visible in `verdict.json` (`r_empty`) or in kinds/primary code; stratified reporting is evaluation-side.

### 9.7 Evidence sufficiency
See 9.1. The statement NDO asserts, as implemented: on the supplied deterministic inputs, under H, every changed executable unit ran at least once in a version containing it, with clean (non-lossy, non-degenerate) equality, and no observed-channel difference was found. Known holes that can make this false until fixed: NF-01 (big integers), NF-03 (fd-level output). Docstring/comment-only changes yield NDO with `r_empty=true` (vacuous) pending UD-2.

### 9.8 Output schemas
`verdict.json` keys as built (`runner.py:322-325`): verdict, level, primary, secondary, witness_id, verdict_id, sufficiency_id, pair_id, package_id, r_empty, policy_below_minimum, cpu_seconds_spent, log_head. `evidence.jsonl`: one JSON object per line `{seq, prev, rec, hash}`; record kinds ProgramVersion, Run, Observation, Witness, SufficiencyRecord, EvidencePackage, Verdict. No machine-readable schema file exists; SD-17 records the as-built schema in the spec decisions.

### 9.9 Failure handling
Verdict-level: harness/internal failure is `tool_error`, never blamed on the program; protocol violations are `unsafe_program`; limits never witness. CLI: `compare` exits 0 (verdict written), 2 (usage/config/inputs), 3 (ineligible); `verify` 0/1/2/4. Gaps: `--out` pointing at a file raises an uncaught traceback (probe); no code for internal errors (X2, MB-14); canonicalisation failures masquerade as program outcomes (MB-01).

### 9.10 Reproducibility
Same inputs and config give identical run, witness, pair and verdict ids across invocations (probe: ids equal; `test_repeated_runs_reproduce_ids_and_chain`; K1 spike reported 0 differences over 139 re-run pairs). Chain head hashes differ per invocation because timings sit in hashed `meta` (probe; X4, SD-14). Primary runs have no pinned hash seed/TZ/locale/threads, so programs depending on string-hash order quarantine as `nondeterministic` (probe `hashseed`; MB-07). Reproducibility on a second machine is untested (Phase 3).

