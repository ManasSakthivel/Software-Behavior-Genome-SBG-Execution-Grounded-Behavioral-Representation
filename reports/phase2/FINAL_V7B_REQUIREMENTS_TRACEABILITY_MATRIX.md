# Final V7-B Requirements Traceability Matrix

Branch `research/v7b-final-validation`, HEAD `a6afa639` (updated in place; the earlier version described HEAD `cc56e029`). Phase 2, local only. This version recomputes the status of all 135 rules against the current code and tests. It does not claim equivalence of any pair, a detection rate, or that any threshold is correct. Statuses rest on code reading plus the existence of the cited test; the recorded run (276 passed, 1 skipped at `5efcef74`, code and tests unchanged since) was not repeated while writing this file. The reconciliation with the two earlier counts, and the status of UD-1..5, MB-01..16, D-01..23, A-01..18 and OI-01..22, are in `PHASE2_TRACEABILITY_RECONCILIATION.md`. The single risk register is `docs/architecture/V7B_RISK_REGISTER.md`.

## 0. Note: history of the earlier versions of this table

| Version | Basis | Counts recorded then |
|---|---|---|
| Audit table (`PHASE_2_SPEC_CONFORMANCE_AUDIT.md`, HEAD `1206312e`) | status of 135 rules | 63 Conforms / 45 Deviates / 23 Not implemented / 4 Unverifiable |
| Earlier version of this matrix (commit `f2aa9143`, HEAD `cc56e029`, marked unverified; recover with `git show f2aa9143:reports/phase2/FINAL_V7B_REQUIREMENTS_TRACEABILITY_MATRIX.md`) | final disposition of the same 135 rows, 169 tests, 168 passed + 1 skipped | 68 Conforms / 23 Mandatory implementation / 17 Specification correction / 15 Intentionally deferred / 7 Phase 3 dependency / 5 Optional functionality / 0 Invalid or obsolete |
| This version | current status of the same 135 rows at `a6afa639` | see section 2 |

The earlier version's sections 5-9 (disposition of the audit's groups, D-01..D-23, A-01..A-18, OI-01..OI-22, topic notes 9.1-9.10) described HEAD `cc56e029` before MB-01..MB-16 and are superseded by `PHASE2_TRACEABILITY_RECONCILIATION.md` sections 5-9. They remain in git history at `f2aa9143`. The two counts above were produced on different axes (status versus disposition) and neither was adopted here.

## 1. Method

- Rows are the 135 rules of the audit (IDs unchanged). Spec sources: `reports/final/V7B_FROZEN_SPEC.md` (FS) and `reports/v7_design/p0_reconciliation/*`.
- Code: `sbgv7/*.py` at HEAD; every `file:line` was checked against the current file. Tests: `tests/v7/*.py`; every test name was checked to exist as a `def` in the named file. Test paths are under `tests/v7/`.
- A row is Conforming only if the code line and an existing test are both named. A row with correct code and no test is Partially conforming and marked TEST GAP.
- Status values: Conforming, Partially conforming, Deviating, Not implemented, Unverifiable, Deferred to Phase 3 (definitions in the reconciliation, section 1).
- Evidence key: "recorded run" = 276 passed, 1 skipped at `5efcef74` (`MB_SECOND_STAGE_REVIEW.md` s9); "mutation item n" = a kill recorded for `scripts/mutation_check_mb.py` (16/16 killed, `MB_SECOND_STAGE_REVIEW.md` s4); `MB-nn` = `MANDATORY_IMPLEMENTATION_BACKLOG.md`; `SD-nn`/`UD-n` = `FINAL_SPECIFICATION_DECISIONS.md`.
- Ratified: UD-1 (as built), UD-3 option A, UD-4 option A, Decisions A and B. Open: UD-2, UD-5. SD-nn clarifications are implemented but not separately ratified; the FS text is not edited.

## 2. Counts by status

| Status | Rows |
|---|---|
| Conforming | 78 |
| Partially conforming | 30 |
| Deviating | 7 |
| Not implemented | 14 |
| Unverifiable | 2 |
| Deferred to Phase 3 | 4 |
| **Total** | **135** |

78 + 30 + 7 + 14 + 2 + 4 = 135. 56 rows differ from the audit's status and 42 differ from the earlier matrix's "Status now" column (see the reconciliation). Rows by status:

- Partially conforming (30): V3, V10, V11, B2d, B3a, B3b, B4b, B7b, O6, C12, P5, G1s, S1a, S1c, S1h, S1i, S2a, S2c, S3, E2, E5, E9, E11, M1, M3, I1, I2, I4, I5, X6.
- Deviating (7): O3, C7, C13, C15, F13, F14, X4.
- Not implemented (14): V8, B2c, C3, W3, P4, P6, G4s, G5s, E8, E10, F11, F16, F17, X5.
- Unverifiable (2): E7, I9.
- Deferred to Phase 3 (4): O5, I7, I10, X1.
- Conforming (78): all other rows.

## 3. Findings NF-01..NF-05 of the earlier review (status at HEAD)

| ID | Finding | Status | Evidence |
|---|---|---|---|
| NF-01 | big integers (above 4300 digits) reported as a program `ValueError`; two versions could both do so and be a clean SAME | Fixed (MB-01) | `harness.py:78,226-229`; `test_backlog_mb.py::test_mb01_huge_ints_differ`, `test_mb01_canon_failure_is_tool_error_not_outcome` |
| NF-02 | source path leaked into exception messages, giving a false witness | Fixed (MB-03) | `harness.py:18-20`; `test_backlog_mb.py::test_mb03_source_path_in_message_and_output_is_normalised` |
| NF-03 | `os.write(1, ...)` differences missed (false NDO S2) | Fixed for the known gap (MB-02); residual: program-created fd-1 streams | `runner.py:113-116`; `test_backlog_mb.py::test_mb02_os_write_differs`, `test_mb02_subprocess_output_differs` |
| NF-04 | protocol violation or unverified sandbox on a replay/alt run did not stop a witness | Fixed (MB-05) | `runner.py:195-202,246-247,256-257`; `test_backlog_mb.py::test_mb05_all_replays_tampered_gives_no_witness`, `test_mb05_alt_run_not_sandbox_ok_gives_sandbox_failure` |
| NF-05 | `python -O` stripped the invariants | Fixed (MB-04) | `records.py:27-32`; `test_backlog_mb.py::test_mb04_invariants_hold_under_python_O` |

## 4. Matrix (135 rows)

### 4.1 Verdicts and precedence

| ID | Spec | Requirement | Implementation (file:line, HEAD) | Test(s) in tests/v7 | Evidence | Status now | Disposition / owner |
|---|---|---|---|---|---|---|---|
| V1 | s2 | Exactly three verdict values | records.py:7,92-93; decide.py:77-87 | test_core.py::test_verdict_record_rejects_prohibited_values | closed tuple; decide() returns only the three strings | **Conforming** | Conforming |
| V2 | s2 | Prohibited outcomes (EQUIVALENT, SAME, PASS, VERIFIED, SAFE) unrepresentable | records.py:27-32,93 (explicit raise, not assert) | test_backlog_mb.py::test_mb04_invariants_hold_under_python_O; test_core.py::test_verdict_record_rejects_prohibited_values | MB-04: survives python -O (13 passed under -O, recorded in MB_SECOND_STAGE_REVIEW s9) | **Conforming** | Done (MB-04) |
| V3 | s2 row 0 | Identical src/deps/runtime: ineligible, excluded | runner.py:363-364,368-369; records.py:116; __main__.py:32,37-38 | test_backlog_mb.py::test_mb08_identical_pair_leaves_nothing_and_is_stable; test_core.py::test_identical_is_ineligible | identity checked before any file exists (MB-08); only source bytes compared, deps/runtime hashing is project-level (SD-20) | **Partially conforming** | Source-byte identity only; deps/runtime identity: Phase 3 |
| V4 | s2 row 1 | Non-voided CONFIRMED_DIFF gives DIVERGENT_OBSERVABLE before any blocker | decide.py:79-81 | test_core.py::test_divergent_return_with_trace; test_core.py::test_precedence_divergent_over_insufficient | - | **Conforming** | Conforming |
| V5 | s2 row 2 | Any B1..B9 gives INSUFFICIENT(primary=min rank; secondary) | decide.py:82-86; records.py:98 | test_core.py::test_decide_baseline_and_missing_evidence; test_core.py::test_property_incomplete_evidence_never_positive | secondary alphabetical (spec silent, A-07) | **Conforming** | Conforming |
| V6 | s2 row 3 | Else NO_DIVERGENCE_OBSERVED(highest level whose floors hold) | decide.py:65-74,87 | test_core.py::test_s1_and_s2 | S1/S2 reachable; S3 refused | **Conforming** | Conforming |
| V7 | s2 | Missing record counts as a blocker | decide.py:41-42 | test_core.py::test_decide_baseline_and_missing_evidence | - | **Conforming** | Conforming |
| V8 | s2 | DIVERGENT absorbing; voided only by Supersession (failed audit replay, drift) | none | none | no Supersession record, no audit replay | **Not implemented** | Programme-deferred (needs audit sampling) |
| V9 | s2 | Early stop at first witness allowed; sufficiency not scored for DIVERGENT | runner.py:382; decide.py:79-81 | test_core.py::test_divergent_return_with_trace | stop reason 'witness' in package (runner.py:388) | **Conforming** | Conforming |
| V10 | s2/s6 | NDO means every changed unit ran in each version containing it | runner.py:153-165,330; decide.py:59-61 | test_phase2_fixes.py::test_docstring_only_is_vacuous_not_a_difference; test_phase2_fixes.py::test_mixed_executable_and_docstring; test_phase2_fixes.py::test_non_executable_non_doc_change_is_unmodelled | docstring-only change gives NDO with r_empty (vacuous); UD-2 open, cap-at-S1 (CB-01) not implemented | **Partially conforming** | Open: UD-2 |
| V11 | s2 | internal_divergence absent when module E off | runner.py:396-400 (key never emitted) | none | no test asserts the absence (TEST GAP) | **Partially conforming** | Test gap: add a verdict.json key-set assertion |
| V12 | s2 | S0 only inside INSUFFICIENT | records.py:94; decide.py:73-74 | test_core.py::test_s0_never_with_no_divergence | - | **Conforming** | Conforming |
| V13 | s2/s7 | Unknown reason code downgrades to INSUFFICIENT | decide.py:62; records.py:95-96; verify.py:41-45 | test_backlog_mb.py::test_mb04_unknown_blocker_code_is_insufficient_tool_error; test_backlog_mb.py::test_mb04_verify_names_unknown_code | MB-04 | **Conforming** | Done (MB-04) |

### 4.2 Blocking conditions and reason codes

| ID | Spec | Requirement | Implementation (file:line, HEAD) | Test(s) in tests/v7 | Evidence | Status now | Disposition / owner |
|---|---|---|---|---|---|---|---|
| B0 | s7 | 18-code closed enum; retired codes absent | records.py:8-11; decide.py:8-11 | test_core.py::test_verdict_record_rejects_prohibited_values; test_backlog_mb.py::test_mb04_unknown_blocker_code_is_insufficient_tool_error | list equals FS s7 (18 codes, re-counted at this HEAD) | **Conforming** | Conforming |
| B0r | s7 | Ranks B1..B9; tie-break inside a rank | decide.py:7-11,85 | test_core.py::test_decide_baseline_and_missing_evidence | tie-break alphabetical is code-only (A-07; SD-12 pending) | **Conforming** | Spec text (SD-12) pending |
| B1 | s7 B1 | import_error | runner.py:200-201,301 | test_core.py::test_import_error_and_entry_missing_and_no_inputs | - | **Conforming** | Conforming |
| B2a | s7 B2 | alignment_failed | runner.py:312-313 | test_conformance_gaps.py::test_alignment_failed_via_static_phase | defensive; reached only when _regions raises; test monkeypatches _regions; mutation item 2 killed | **Conforming** | Defensive by design (SD-16) |
| B2b | s7 B2 | unsupported_signature (entry missing; incompatible signature with probe off) | runner.py:302,305-306 | test_core.py::test_import_error_and_entry_missing_and_no_inputs; test_core.py::test_signature_change | - | **Conforming** | Conforming |
| B2c | s7 B2 | ambiguous_entry | none (CLI takes one --entry: __main__.py:15) | none | never produced | **Not implemented** | Deferred with the explorer |
| B2d | s7 B2 | unmodelled_change (non-AST, dependency, config change) | runner.py:153-165,311 | test_phase2_fixes.py::test_non_executable_non_doc_change_is_unmodelled | single-file non-executable lines only; dependency/config changes are not detected | **Partially conforming** | Dependency/config scope: Phase 3 |
| B3a | s7 B3 | sandbox_failure when a property is violated or unverified | runner.py:70,95; isolation.py:279-280 | test_backlog_mb.py::test_mb06_required_property_unverified_is_sandbox_failure; test_backlog_mb.py::test_mb06_advisory_unavailable_keeps_verdicts_and_flags_policy | required set gates; rlimit_as/rlimit_nproc advisory (SD-07, not ratified); literal FS says any unverified property | **Partially conforming** | Open: ratify SD-07 |
| B3b | s7 B3 | unsafe_program (policy violation, tamper) | runner.py:117-121,198-199,299; decide.py:43-44 | test_result_protocol.py::test_forged_or_broken_result_is_unsafe_program; test_result_protocol.py::test_protocol_violations; test_backlog_mb.py::test_mb10_protocol_violation_is_unsafe_program_without_spurious_resource_limit | protocol violations covered; a sandbox denial surfaces as a program PermissionError (D-08); same-address-space adversary (I4) | **Partially conforming** | Phase 3 residual (I4/I10) |
| B4a | s7 B4 | flaky_witness | runner.py:248-251; decide.py:50 | test_core.py::test_replay_classes; test_backlog_mb.py::test_mb05_clean_replays_still_confirm | scripted runs; real-program flaky case untested | **Conforming** | Conforming |
| B4b | s7 B4 | env_sensitive (control-sensitive, fails k_alt) | runner.py:252-259; harness.py:179-186 | test_backlog_mb.py::test_mb07_real_env_sensitive_case; test_core.py::test_replay_classes | alt runs for every candidate (SD-09); datetime.now and hash seed not varied (Decisions A, B) | **Partially conforming** | Accepted limits (R1, R2) |
| B5 | s7 B5 | nondeterministic: quarantined input that hit or may have hit a changed unit | decide.py:50; runner.py:225-226 | test_core.py::test_nondeterministic_quarantined | 'may have hit' read as always (UD-4 option A, ratified) | **Conforming** | Spec text pending |
| B6 | s7 B6 | resource_limit: exactly one side ended in a harness limit | decide.py:50-51; runner.py:205-209,227-231 | test_core.py::test_timeout_asymmetric_and_both; test_backlog_mb.py::test_mb10_both_limit_still_resource_limit; test_backlog_mb.py::test_mb10_protocol_violation_is_unsafe_program_without_spurious_resource_limit | only both_limit/asymmetric limit map to resource_limit (MB-10); both-limit blocking by UD-4 A | **Conforming** | Done (MB-10) under UD-4 A |
| B7a | s7 B7 | capture_truncated | runner.py:96,108,115-116; decide.py:49 | test_conformance_gaps.py::test_capture_truncated_end_to_end | mutation item 1 killed | **Conforming** | Conforming |
| B7b | s7 B7 | blind_spot_dominant / blind spot in a changed unit | none (code never produced: decide.py:10 RANK only); fd-1 folding runner.py:113-116 | test_backlog_mb.py::test_mb02_os_write_differs; test_backlog_mb.py::test_mb02_subprocess_output_differs; test_second_stage.py::test_buffered_real_stdout_difference_is_observed | known stdout gap closed (MB-02, UD-3 A); no detector; os.fdopen(1) streams still lost | **Partially conforming** | Residual: detector deferred |
| B8a | s7 B8 | no_inputs | decide.py:53-55 | test_core.py::test_import_error_and_entry_missing_and_no_inputs | - | **Conforming** | Conforming |
| B8b | s7 B8 | unobservable_outcome (no non-degenerate channel) | decide.py:56-58; runner.py:232-234,239-240 | test_core.py::test_degenerate_unobservable; test_phase2_fixes.py::test_lossy_s1_is_insufficient; test_phase2_fixes.py::test_symmetric_binding_failure_is_not_a_same | UD-1 A-L1 ratified | **Conforming** | Conforming |
| B8c | s7 B8 | tool_error (internal failure, never blamed on the program) | decide.py:41-42,62; runner.py:201; harness.py:238-239 | test_backlog_mb.py::test_mb01_canon_failure_is_tool_error_not_outcome; test_backlog_mb.py::test_mb05_replay_harness_error_is_tool_error | - | **Conforming** | Conforming |
| B9 | s7 B9 | changed_region_not_activated / budget_exhausted_s0 | decide.py:59-61; runner.py:372-384; finalize 321,337 | test_core.py::test_budget_exhausted; test_backlog_mb.py::test_mb11_last_input_exhausting_budget_with_unhit_units_is_budget_exhausted | SD-19 granularity one run | **Conforming** | Conforming |

### 4.3 Per-input outcomes

| ID | Spec | Requirement | Implementation (file:line, HEAD) | Test(s) in tests/v7 | Evidence | Status now | Disposition / owner |
|---|---|---|---|---|---|---|---|
| O1 | s3 | Seven per-input outcomes | decide.py:6; runner.py:225-260 | test_core.py::test_replay_classes; test_core.py::test_no_run_input_blocks_no_divergence | - | **Conforming** | Conforming |
| O2 | s3 | returned/raised/exited/crashed/limit | harness.py:219-225; runner.py:104-121 | test_core.py::test_crash_reproduced_is_witness; test_core.py::test_timeout_asymmetric_and_both | - | **Conforming** | Conforming |
| O3 | s3/SPEC 2.4 | SystemExit is raised(type,msg); exited(code) is os._exit | harness.py:222-223; compare.py:62-63 | test_conformance_gaps.py::test_systemexit_code_is_compared | SystemExit recorded as exited(code); os._exit is unsafe_program (SD-11, pending) | **Deviating** | Spec text (SD-11) pending |
| O4 | s3 | Limits never a witness; both-limit is NO_RUN | runner.py:227-231 | test_core.py::test_timeout_asymmetric_and_both; test_backlog_mb.py::test_mb10_both_limit_still_resource_limit | - | **Conforming** | Conforming |
| O5 | s3 | Harness-limit MemoryError is limit(oom), not raised | harness.py:224-225; isolation.py:193-194 | test_isolation.py::test_memory_rlimit_as_hard (skipped on macOS) | RLIMIT_AS not enforceable on macOS; Linux only | **Deferred to Phase 3** | Phase 3 (Linux) |
| O6 | s3 | Unserialisable value is NO_RUN(unobservable_outcome), never equal | harness.py:226-229,238-239; _c cycles 86 | test_backlog_mb.py::test_mb01_canon_failure_is_tool_error_not_outcome; test_harness_canon.py::test_unobservable_is_lossy_never_s2 | canon failure is never an equal (MB-01) but surfaces as tool_error, not unobservable_outcome; huge ints now hex | **Partially conforming** | Spec wording vs tool_error: decide |
| O7 | s3 | Introduced non-termination gives INSUFFICIENT(resource_limit) | runner.py:229-231; decide.py:51 | test_core.py::test_timeout_asymmetric_and_both | - | **Conforming** | Conforming |

### 4.4 Observation boundary

| ID | Spec | Requirement | Implementation (file:line, HEAD) | Test(s) in tests/v7 | Evidence | Status now | Disposition / owner |
|---|---|---|---|---|---|---|---|
| C1 | s4 | C_obs default 6 channels | config.py:4,48; compare.py:51-73 | test_conformance_gaps.py::test_defaults_table_item6; test_core.py::test_divergent_exception_stdout_and_global | - | **Conforming** | Conforming |
| C2 | s4 | stderr/perf/lines/tracebacks/run ids excluded | runner.py:114 (only r.stdout folded); isolation.py:150-151 | test_conformance_gaps.py::test_stderr_only_difference_is_not_observed | mutation item 4 killed (first test version was vacuous, fixed) | **Conforming** | Conforming |
| C3 | s4 | Uninstrumentable channels drop to intersection; empty gives unobservable_outcome | none; decide.py:72 (constant) | none | - | **Not implemented** | Deferred (non-Python/module E) |
| C4 | s4 | Equality on canonical form; user __eq__/__repr__ never called | harness.py:23-34,69-126 | test_harness_canon.py::test_canonicalisation_runs_no_user_code | - | **Conforming** | Conforming |
| C5 | s4 | Type tag is identity | compare.py:14-15; harness.py:74-82 | test_core.py::test_comparator_types | - | **Conforming** | Conforming |
| C6 | s4 | Floats exact binary64, NaN equal | compare.py:17-23 | test_core.py::test_comparator_types | - | **Conforming** | Conforming |
| C7 | s4 | Declared tolerance: exact record + tolerance_masked, never pooled | compare.py:21-22 | test_core.py::test_comparator_options (equality only) | tolerance applied but no exact record, no flag; default 0 so no effect | **Deviating** | Optional (SD-24) |
| C8 | s4 | Mappings key-order-insensitive; ordered_mapping option | compare.py:33-38 | test_core.py::test_comparator_options | - | **Conforming** | Conforming |
| C9 | s4 | Sets unordered; sequences ordered | harness.py:100,108; compare.py:24-25 | test_core.py::test_comparator_types | - | **Conforming** | Conforming |
| C10 | s4 | Objects: class + __dict__/__slots__ digest to depth 3 | harness.py:13,94-126 | test_harness_canon.py::test_contents_difference_is_divergent; test_harness_canon.py::test_equal_contents_of_all_supported_types_reach_s2 | - | **Conforming** | Conforming |
| C11 | s4 | Exceptions: qualified type, normalised message, ignore option | compare.py:60-61; harness.py:224-225 | test_core.py::test_comparator_options | - | **Conforming** | Conforming |
| C12 | s4 | Normaliser N: addresses, ids, absolute paths, default reprs; declared and versioned | harness.py:18-20; runner.py:20-24; config.py:50 | test_backlog_mb.py::test_mb03_source_path_in_message_and_output_is_normalised; test_backlog_mb.py::test_mb03_real_message_change_still_differs | N1 strips addresses, workdir, source file and dir; other absolute paths and default reprs in returned strings are not normalised | **Partially conforming** | Residual normaliser scope |
| C13 | s4 | Message-only difference is kind=exception_message | compare.py:61 | test_core.py::test_comparator_options (equality only) | single kind 'exception' (SD-23 pending) | **Deviating** | Spec text (SD-23) pending |
| C14 | s4 | equal_lossy blocks S2 | harness.py:14,121,124; compare.py:73; decide.py:56-58,71 | test_phase2_fixes.py::test_decide_lossy_same_is_not_evidence; test_core.py::test_s1_not_s2_when_lossy | stricter (blocks S1 too); UD-1 ratified | **Conforming** | Conforming |
| C15 | s4 | stdout is bytes written by the call | harness.py:189-192 | test_second_stage.py::test_buffered_real_stdout_difference_is_observed (import case) | import-time output is part of stdout (UD-3 import sub-decision, as built) | **Deviating** | Spec text pending |

### 4.5 Witness, replay, signatures

| ID | Spec | Requirement | Implementation (file:line, HEAD) | Test(s) in tests/v7 | Evidence | Status now | Disposition / owner |
|---|---|---|---|---|---|---|---|
| W1 | s5 | Witness fields | records.py:82-85; runner.py:284-289 | test_core.py::test_divergent_return_with_trace | - | **Conforming** | Conforming |
| W2 | s5 | kinds priority outcome>exception>side_effect>api | compare.py:6,73 | test_core.py::test_divergent_exception_stdout_and_global | - | **Conforming** | Conforming |
| W3 | s5 | Witness immutable, voidable only by Supersession | none | none | append-only chain only; chain is forgeable by its writer (R6) | **Not implemented** | Programme-deferred |
| W4 | s5/s8 | Witness chain resolves to H, programs, input, environment, policy | runner.py:386-395; records.py:65 | test_phase2_fixes.py::test_package_holds_evidence_not_just_hashes; test_phase2_fixes.py::test_verify_recomputes_every_pair | EvidencePackage holds config/H, env, policy, inputs, rows, regions | **Conforming** | Conforming |
| W5 | s5 | Locus unlocalised valid | records.py:85 | test_conformance_gaps.py::test_witness_locus_unlocalised | mutation item 5 killed | **Conforming** | Conforming |
| P1 | s5 | r_det self-consistency, early stop, else QUARANTINED | runner.py:225-226,274-279 | test_core.py::test_nondeterministic_quarantined | - | **Conforming** | Conforming |
| P2 | s5 | r_replay=5 fresh replays, 5/5 reproduce | runner.py:242-251 | test_core.py::test_replay_classes; test_core.py::test_divergent_return_with_trace | all replays run before counting (cost only) | **Conforming** | Conforming |
| P3 | s5 | Agreement on C_obs, not trace | runner.py:135-139,248 | test_core.py::test_replay_classes | - | **Conforming** | Conforming |
| P4 | s5 | Build mismatch makes replay inconclusive | none | none | single interpreter per invocation | **Not implemented** | Deferred |
| P5 | s5 | k_alt alternate control settings | runner.py:252-259; harness.py:179-186 | test_backlog_mb.py::test_mb07_real_env_sensitive_case; test_backlog_mb.py::test_mb07_pure_random_difference_is_not_a_witness; test_backlog_mb.py::test_mb07_alt_virtualises_urandom_uuid_and_monotonic; test_second_stage.py::test_alt_virtualises_secrets_and_systemrandom; test_second_stage.py::test_datetime_now_is_NOT_virtualised_documented_limit | virtualised: time, monotonic, perf_counter, random seed, urandom/uuid4/secrets; not: datetime.now, hash seed (Decisions A, B) | **Partially conforming** | Accepted limits (R1, R2) |
| P6 | s5 | Optional minimisation | none | none | spec: optional | **Not implemented** | Optional |
| P7 | SPEC D7 | All replay processes charged to the CPU budget | runner.py:82-86,93,271-273 | test_backlog_mb.py::test_mb11_spent_includes_parent_cpu; test_backlog_mb.py::test_mb11_budget_stops_between_runs_inside_an_input | MB-11: parent CPU charged, check before every run; an in-flight run is not interrupted | **Conforming** | Done (MB-11) |
| P8 | s5 | crashed is a witness only if reproduced in every replay | runner.py:117-119,248-251 | test_core.py::test_crash_reproduced_is_witness | - | **Conforming** | Conforming |
| G1s | s5 | Compatible signatures proceed (arity/names, defaults added, declared rename) | runner.py:181-183,305 | test_core.py::test_signature_change | declared rename absent | **Partially conforming** | Optional extension |
| G2s | s5 | api_break_probe: bind failure gives kind=api witness | harness.py:213-218; compare.py:56-57 | test_phase2_fixes.py::test_asymmetric_binding_failure_is_api_witness; test_core.py::test_signature_change | - | **Conforming** | Conforming |
| G3s | s5 | Inputs valid for one side bound against the other | runner.py:232-234; decide.py:24 | test_phase2_fixes.py::test_symmetric_binding_failure_is_not_a_same; test_phase2_fixes.py::test_decide_invalid_input_never_positive | - | **Conforming** | Conforming |
| G4s | s5 | Entry missing in one version: lift to outermost common frame | none (fail-safe branch runner.py:302) | none | fails safe as unsupported_signature | **Not implemented** | Optional |
| G5s | s5 | Ungenerable inputs give unsupported_signature, never an invented default | config.py:84-98 (JSON inputs only) | test_core.py::test_bad_inputs (validation only) | no generator exists; rule never exercised | **Not implemented** | Deferred with the explorer |

### 4.6 Sufficiency

| ID | Spec | Requirement | Implementation (file:line, HEAD) | Test(s) in tests/v7 | Evidence | Status now | Disposition / owner |
|---|---|---|---|---|---|---|---|
| S1a | s6 | SufficiencyRecord: factors, stop reason, r_det, Merkle root, X_eff, quarantined, unhit, r_empty | runner.py:341-350; records.py:101-106 | test_backlog_mb.py::test_mb12_sufficiency_record_has_root_and_factors; test_backlog_mb.py::test_mb12_merkle_root_properties | Merkle root and F1..F4 added (MB-12); stop_reason values inputs_exhausted/budget_mid_input outside the SPEC enum; Merkle has no domain separation (R11) | **Partially conforming** | Open: SD-12 enum; R11 |
| S1b | s6 | Hit = deterministic-confirmed input executed unit; one-sided units | runner.py:324-330 | test_core.py::test_s1_and_s2; test_phase2_fixes.py::test_lossy_input_does_not_activate_changed_units | - | **Conforming** | Conforming |
| S1c | s6 | Uninstrumentable units unhit; R never shrunk | runner.py:153-165 | test_phase2_fixes.py::test_docstring_only_is_vacuous_not_a_difference; test_phase2_fixes.py::test_non_executable_non_doc_change_is_unmodelled | docstring lines vacuous (UD-2 open) | **Partially conforming** | Open: UD-2 |
| S1d | s6 | r_empty flagged and its own stratum | runner.py:344,398 | test_phase2_fixes.py::test_docstring_only_is_vacuous_not_a_difference | flag exposed in verdict.json; stratified reporting is evaluation-side | **Conforming** | Conforming |
| S1e | s6 | S1: >=1 SAME input valid on both, non-degenerate | decide.py:53-58; runner.py:232-234 | test_core.py::test_degenerate_unobservable; test_phase2_fixes.py::test_symmetric_binding_failure_is_not_a_same | - | **Conforming** | Conforming |
| S1f | s6 | S1: 100 percent of changed units hit | decide.py:59-61 | test_core.py::test_s1_and_s2 | - | **Conforming** | Conforming |
| S1g | s6 | S1: r_det per input; no quarantined input that may hit | decide.py:50; runner.py:225-226 | test_core.py::test_nondeterministic_quarantined | UD-4 A ratified | **Conforming** | Conforming (UD-4 A) |
| S1h | s6 | S1: tier >= L0/L1 with changed-region bitmap | runner.py:128-129; harness.py:149-152; config.py:51 | test_backlog_mb.py::test_mb13_constants_accepted_and_equal_to_defaults | L0 fixed; hit-line set stands for the bitmap (SD-08 pending); no tier field in records | **Partially conforming** | Spec text (SD-08) |
| S1i | s6 | S1: no truncation, no blind spot, tamper flag clear | decide.py:43-44,49 | test_conformance_gaps.py::test_capture_truncated_end_to_end; test_result_protocol.py::test_forged_or_broken_result_is_unsafe_program | truncation and tamper wired; blind-spot floor absent (B7b) | **Partially conforming** | Open: blind-spot detector |
| S2a | s6 | Direction coverage >= 0.80 of statically reachable directions | runner.py:13,168-178,331-335 | test_conformance_gaps.py::test_s2_coverage_two_branches; test_conformance_gaps.py::test_s2_coverage_loop_for_iter; test_conformance_gaps.py::test_deleted_and_inserted_line_units; test_core.py::test_s1_and_s2 | all directions counted reachable; vacuous coverage 1.0 (A-16, UD-2 open) | **Partially conforming** | Open: UD-2 / SD-22 |
| S2b | s6 | S2: every contributing input deterministic-confirmed | decide.py:50-52 | test_core.py::test_nondeterministic_quarantined | - | **Conforming** | Conforming |
| S2c | s6 | S2: all declared channels instrumented | decide.py:72 (constant True) | test_backlog_mb.py::test_mb02_os_write_differs | flag still a constant; the known fd-level gap is closed by MB-02 | **Partially conforming** | Open: flag truthful only for the known gap |
| S2d | s6 | S2: no equal_lossy on ret/side | decide.py:71 | test_core.py::test_s1_not_s2_when_lossy | - | **Conforming** | Conforming |
| S3 | s6/s11 | s3_enabled=false default; plateau/L2/corroboration | config.py:41-43,53; records.py:94 | test_core.py::test_bad_config (s3 true refused) | default and refusal implemented; S3 mechanism not built | **Partially conforming** | S3 deferred (SD-16) |
| S0 | s6 | S0 only inside INSUFFICIENT | decide.py:73-74 | test_core.py::test_s0_never_with_no_divergence | - | **Conforming** | Conforming |

### 4.7 Evidence model and modules

| ID | Spec | Requirement | Implementation (file:line, HEAD) | Test(s) in tests/v7 | Evidence | Status now | Disposition / owner |
|---|---|---|---|---|---|---|---|
| E1 | s8 | evidence_class on every record; status qualifier | records.py:12,35-48 | test_conformance_gaps.py::test_record_kinds_have_documented_evidence_class | mutation item 9 killed | **Conforming** | Conforming |
| E2 | s8 | Class per record kind; ChangedRegions, SourceMapping, ReplayCheck, Reproducibility, HarnessDeclaration, Input, ExplorationLog, Completeness records | records.py:54-67; runner.py:386-389 | test_phase2_fixes.py::test_package_holds_evidence_not_just_hashes | equivalents folded into EvidencePackage (SD-17 pending) | **Partially conforming** | Spec text (SD-17) |
| E3 | s8 | DIVERGENT chain: Verdict, Witness, runs, replays, H, programs, input, env, policy | runner.py:386-395 | test_phase2_fixes.py::test_verify_recomputes_every_pair | - | **Conforming** | Conforming |
| E4 | s8 | NDO chain: SufficiencyRecord, run-set root + rows, regions, H | runner.py:386-394,346 | test_phase2_fixes.py::test_verify_recomputes_every_pair | - | **Conforming** | Conforming |
| E5 | s8 | INSUFFICIENT chain: records that triggered each blocker | runner.py:341-350,393 | test_phase2_fixes.py::test_verify_recomputes_every_pair | blocker detail names input ids; refs include all runs, not only the triggering ones | **Partially conforming** | Spec text (SD-17) |
| E6 | s8 | T4: recompute verdict from the chain | verify.py:32-98 | test_phase2_fixes.py::test_verify_recomputes_every_pair; test_phase2_fixes.py::test_verify_detects_rehashed_forgeries; test_phase2_fixes.py::test_verify_divergent_forged_to_same | observations taken as recorded; nothing is re-executed | **Conforming** | Conforming |
| E7 | s9 | T6: no label-namespace record reachable | none | none | vacuous today | **Unverifiable** | Phase 3 audit tooling |
| E8 | s8 | Replay recipe + hashed event stream | runner.py:128-129 (hit lines only) | none | no event stream, no recipe | **Not implemented** | Deferred |
| E9 | s8 | Hash chain tamper detection | records.py:113-135; verify.py:35-57 | test_phase2_fixes.py::test_verify_detects_plain_edit_and_truncation; test_phase2_fixes.py::test_verify_detects_rehashed_forgeries; test_second_stage.py::test_v7b_docs_do_not_claim_tamper_proof | unkeyed plaintext chain; a writer who recomputes ids and hashes forges a consistent log (R6) | **Partially conforming** | Phase 3 trust anchor (R6) |
| E10 | s8 | Chain hash excludes run id/repeat index (EV-13) | none | none | no event-stream chain (SD-14) | **Not implemented** | Spec text (SD-14) |
| E11 | s8 | verify_chain, replay(recipe) | verify.py:32-98 | test_phase2_fixes.py::test_verify_cli_exit_codes | replay(recipe) absent | **Partially conforming** | Replay: Phase 3 |
| M1 | s9 | Core modules A,B,C,D,G,H,I,K,L | sbgv7/*.py | none | A, G absent; K, L evaluation-side | **Partially conforming** | Deferred / Phase 3 |
| M2 | s9 | Module I is the sole Verdict writer | runner.py:395; records.py:92-98 | test_core.py::test_verdict_record_rejects_prohibited_values | single call site (grep Verdict( in sbgv7) | **Conforming** | Conforming |
| M3 | s9 | Dependencies acyclic | sbgv7 import graph (verify imports runner; not vice versa) | none | no test asserts acyclicity; every test module imports the package (TEST GAP) | **Partially conforming** | Test gap |

### 4.8 Isolation

| ID | Spec | Requirement | Implementation (file:line, HEAD) | Test(s) in tests/v7 | Evidence | Status now | Disposition / owner |
|---|---|---|---|---|---|---|---|
| I1 | s10 | Fresh child, CPython 3.13, -I, scrubbed env, private cwd, pinned control env | isolation.py:118,125,269-276; runner.py:32-34 | test_second_stage.py::test_child_env_is_exactly_the_allowlist_and_path_is_clean; test_second_stage.py::test_hostile_parent_env_does_not_change_verdict_or_ids; test_backlog_mb.py::test_mb07_python_minor_version_flags_policy | -I replaced by -s -P -B + allowlist (cannot keep PYTHONHASHSEED); 3.13 is a flag, not a gate | **Partially conforming** | Open: interpreter gate |
| I2 | s10 | setrlimit CPU/FSIZE/NPROC/NOFILE/CORE + RSS watchdog | isolation.py:112-117,165-169,312 | test_isolation.py::test_cpu_rlimit; test_isolation.py::test_memory_limit_200mb_or_less; test_isolation.py::test_memory_rlimit_as_hard (skipped on macOS) | CPU, NOFILE, FSIZE, CORE and watchdog active; RLIMIT_AS and NPROC unavailable on macOS | **Partially conforming** | Linux enforcement: Phase 3 |
| I3 | s10 | Process-group kill | isolation.py:88-101,128 | test_isolation.py::test_child_process_survival; test_isolation.py::test_spin_wall_timeout | setsid escape not covered (documented, isolation.py:5-6) | **Conforming** | Conforming |
| I4 | s10 | Tracing outside user-code reach, tamper detection | harness.py:145-171 | test_result_protocol.py::test_forged_or_broken_result_is_unsafe_program; test_result_protocol.py::test_settrace_evasion_behaviour_unchanged | HMAC frame; tracer shares the address space with the program (R3) | **Partially conforming** | Phase 3 (R3) |
| I5 | s10 | Network denial (macOS sandbox-exec; Linux --network none) | sandbox_darwin.sb:2; isolation.py:109-110,321 | test_isolation.py::test_network_denied; test_conformance_gaps.py::test_loud_not_skipped_sandbox_must_be_active_on_darwin | macOS only, sandbox-exec deprecated, not a validated boundary; Linux path absent (R12) | **Partially conforming** | Linux/Docker: Phase 3 (R12) |
| I6 | s10 | Write confinement to private tmp | sandbox_darwin.sb:3-7; isolation.py:322 | test_isolation.py::test_write_outside_denied | reads unconfined | **Conforming** | Conforming |
| I7 | s10 | Exact failure classification | isolation.py:188-196 | test_isolation.py::test_cpu_rlimit; test_isolation.py::test_memory_limit_200mb_or_less | stderr substring and CPU-time heuristics; exact classes need Linux enforcement | **Deferred to Phase 3** | Phase 3 (Linux) |
| I8 | s10 | macOS runs flagged policy_below_minimum | runner.py:32-34,345,398 | test_conformance_gaps.py::test_policy_below_minimum_true_on_darwin; test_backlog_mb.py::test_mb07_python_minor_version_flags_policy | platform clause only weakly verified (R10) | **Conforming** | Conforming |
| I9 | s10 | Legacy runner/tracer is v6_compat | none | none | no legacy runner reachable from sbgv7 | **Unverifiable** | Deferred |
| I10 | s10 | Hostile fixtures: zero escapes, no stray processes | tr (forged frames); ti::test_no_stray_processes | none | no setsid, subprocess escape, monitoring-tamper or fork-bomb fixture; hard G1 gate needs Linux | **Deferred to Phase 3** | Phase 3 |

### 4.9 Config

| ID | Spec | Requirement | Implementation (file:line, HEAD) | Test(s) in tests/v7 | Evidence | Status now | Disposition / owner |
|---|---|---|---|---|---|---|---|
| F1 | s11 | harness.c_obs 6 channels | config.py:4,48 | test_conformance_gaps.py::test_defaults_table_item6 | - | **Conforming** | Conforming |
| F2 | s11 | harness.normaliser_id | config.py:50 | test_backlog_mb.py::test_mb13_constants_accepted_and_equal_to_defaults; test_backlog_mb.py::test_mb13_other_values_rejected_not_built | constant N1 only | **Conforming** | Done (MB-13) |
| F3 | s11 | float_tol rel=0,abs=0 | config.py:48 | test_conformance_gaps.py::test_defaults_table_item6 | - | **Conforming** | Conforming |
| F4 | s11 | ordered_mapping=false | config.py:49 | test_conformance_gaps.py::test_defaults_table_item6 | - | **Conforming** | Conforming |
| F5 | s11 | exc_message=exact_normalised | config.py:49 | test_conformance_gaps.py::test_defaults_table_item6 | - | **Conforming** | Conforming |
| F6 | s11 | stderr=excluded | config.py:50 | test_backlog_mb.py::test_mb13_constants_accepted_and_equal_to_defaults | constant only | **Conforming** | Done (MB-13) |
| F7 | s11 | capture_tier=L0(+bitmap) | config.py:51 | test_backlog_mb.py::test_mb13_constants_accepted_and_equal_to_defaults | constant L0 only | **Conforming** | Done (MB-13) |
| F8 | s11 | api_break_probe=true | config.py:50 | test_conformance_gaps.py::test_defaults_table_item6; test_phase2_fixes.py::test_asymmetric_binding_failure_is_api_witness | - | **Conforming** | Conforming |
| F9 | s11 | r_det=3, r_replay=5, k_alt=3 | config.py:52 | test_conformance_gaps.py::test_defaults_table_item6 | mutation item 6 killed | **Conforming** | Conforming |
| F10 | s11 | s2_branch_floor=0.80 | config.py:53 | test_conformance_gaps.py::test_defaults_table_item6; test_core.py::test_s1_and_s2 | - | **Conforming** | Conforming |
| F11 | s11 | s3_plateau_window, static_match_f1_trigger, witness_outside_R_diag | none | none | reserved (SD-18) | **Not implemented** | Deferred |
| F12 | s11 | s3_enabled=false | config.py:41-43,53 | test_core.py::test_bad_config (s3 true refused) | - | **Conforming** | Conforming |
| F13 | s11 | budget unit/grid=[10,60,300]/headline=60 | config.py:54 | test_conformance_gaps.py::test_defaults_table_item6 (headline only) | single cpu_seconds=60; grid is evaluation-side | **Deviating** | Spec text (SD-18) pending |
| F14 | s11 | per_run claims_cpu_s=10, fast_cpu_s=2 | config.py:55 | test_conformance_gaps.py::test_defaults_table_item6 (cpu_s only) | single cpu_s | **Deviating** | Spec text (SD-18) pending |
| F15 | s11 | per_run wall_s=20, rss_mib=2048 | config.py:55-56 | test_conformance_gaps.py::test_defaults_table_item6 | - | **Conforming** | Conforming |
| F16 | s11 | per_run max_events_L1=200000 | none | none | tier L1 absent | **Not implemented** | Deferred |
| F17 | s11 | seeds, stats, platform blocks | none | none | evaluation-side | **Not implemented** | Deferred |
| F18 | s11/SPEC 2.5 | Verdict identity includes all of H (repeat, floors, policy, profile, tier) | runner.py:75,80; verify.py:64-65 | test_backlog_mb.py::test_mb09_pair_id_covers_repeat_and_suff_not_budget; test_backlog_mb.py::test_mb09_pair_id_covers_policy | budget excluded by SD-20; pair id depends on the policy record (risk T-04) | **Conforming** | Done (MB-09) |

### 4.10 Gates, CLI, determinism

| ID | Spec | Requirement | Implementation (file:line, HEAD) | Test(s) in tests/v7 | Evidence | Status now | Disposition / owner |
|---|---|---|---|---|---|---|---|
| X1 | s12 | Gates G0-G8, K1-K5 | experiments/v7b/k1_spike.py; scripts/analyze_results.py (evaluation-side, not re-read) | tests/v7/test_analysis.py (analysis only) | K1 NOT MET on existing data; pre-MB numbers not comparable | **Deferred to Phase 3** | Phase 3 (UD-5 open) |
| X2 | CLI | CLI exit codes | __main__.py:10-44 | test_backlog_mb.py::test_mb14_out_is_a_file_exits_2_no_traceback; test_backlog_mb.py::test_mb14_unwritable_out_exits_2; test_backlog_mb.py::test_mb14_unexpected_exception_exits_1_one_line; test_backlog_mb.py::test_mb14_help_exits_0; test_phase2_fixes.py::test_verify_cli_exit_codes; test_core.py::test_cli | FS silent; contract per SD-13 | **Conforming** | Done (MB-14) |
| X3 | SPEC 2.5 | Same inputs/config give same ids | records.py:19-20,74; runner.py:80 | test_core.py::test_repeated_runs_reproduce_ids_and_chain | - | **Conforming** | Conforming |
| X4 | SPEC | Artefact determinism | records.py:35-43; runner.py:128-129,399 | none | timings in hashed meta, so log_head differs per invocation (SD-14); no test | **Deviating** | Spec text (SD-14) pending |
| X5 | s11 | Seeds: exploration_seed pre-declared | none | none | no explorer | **Not implemented** | Deferred |
| X6 | SPEC 5.1 | Determinism controls for primary runs | isolation.py:269-276; harness.py:179-186 | test_backlog_mb.py::test_mb07_hash_seed_pinned_set_order_is_deterministic; test_backlog_mb.py::test_mb07_alt_virtualises_urandom_uuid_and_monotonic; test_second_stage.py::test_alt_virtualises_secrets_and_systemrandom | hash seed, TZ, locale, UTF-8, threads pinned; datetime.now not virtualised, hash seed not varied (Decisions A, B) | **Partially conforming** | Accepted limits (R1, R2) |

## 5. Where the other registers now live

| Register | Location |
|---|---|
| Audit-to-current reconciliation table (rule, A, B, new, reason) | `reports/phase2/PHASE2_TRACEABILITY_RECONCILIATION.md` s4 |
| UD-1..UD-5 | same file, s5 |
| MB-01..MB-16 with tests | same file, s6 |
| D-01..D-23 | same file, s7 |
| A-01..A-18 | same file, s8 |
| OI-01..OI-22 | same file, s9 |
| Risks (R1..R22) | `docs/architecture/V7B_RISK_REGISTER.md` |
