# Mandatory Implementation Backlog (Phase 2, local only)

Branch `research/v7b-final-validation`, HEAD `cc56e029`. Source: `FINAL_V7B_REQUIREMENTS_TRACEABILITY_MATRIX.md` (rows with final disposition "Mandatory implementation"), `FINAL_SPECIFICATION_DECISIONS.md` (SD-/UD- references). Items are ordered by risk to the validity of a verdict (false assurance first). Every item is runnable on this macOS host with `.venv/bin/python -m pytest tests/v7`; none needs Docker, Linux or third-party code. Excluded because they are Phase 3 dependencies or deferred: Linux isolation (I2, I4, I5-Linux, I7, I10, O5, D-08), explorer, input generation, module E, S3, Supersession, event streams, replay(recipe), build-mismatch handling, K gates.

Sizes: XS < 30 changed lines, S 30-100, M 100-300 (code + tests). Owner of each file is the implementation agent for the next phase; this task did not edit any of them.

Standing acceptance for every item: the full `tests/v7` suite stays green (currently 168 passed, 1 skipped), `python -m sbgv7 verify` still exits 0 on freshly produced evidence for each new scenario, and no new reason code or verdict value is introduced (the 18-code enum and the three verdicts are unchanged).

| # | ID | Item | Priority | Size |
|---|---|---|---|---|
| 1 | MB-01 | Canonicalisation failure must not become a program outcome (big integers) | Blocking | S |
| 2 | MB-02 | Capture fd-level output (`os.write(1)`, subprocess) in the stdout channel | Blocking | S |
| 3 | MB-03 | Normalise the source path in exception messages and stdout | Major | XS |
| 4 | MB-04 | Invariants as explicit raises; unknown reason code handling | Major | XS |
| 5 | MB-05 | A witness requires sandbox-verified, untampered replay and alt runs | Major | S |
| 6 | MB-06 | `sandbox_failure` for unverified required isolation properties | Major | S |
| 7 | MB-07 | Determinism control profile and wider alternate-control virtualisation | Major | M |
| 8 | MB-08 | Identity check before any side effect; one overwrite policy | Moderate | XS |
| 9 | MB-09 | Pair identity covers repeat, suff and policy (H definition) | Moderate | S |
| 10 | MB-10 | Name the real cause of a `NO_RUN` input | Moderate | S |
| 11 | MB-11 | Budget: charge parent CPU, check between runs | Moderate | S |
| 12 | MB-12 | Merkle run-set root and factor vector in the SufficiencyRecord | Moderate | S |
| 13 | MB-13 | Accept FS constant config fields (`normaliser_id`, `stderr`, `capture_tier`) | Minor | XS |
| 14 | MB-14 | CLI failure handling and exit codes | Minor | XS |
| 15 | MB-15 | Record a digest of the V6 `changed_lines` code in the package | Minor | XS |
| 16 | MB-16 | Test-gap closure (tests only) | Moderate | M |

Total: 16 items. Rough effort: 2 M, 8 S, 6 XS, about 2 to 3 engineer-days including tests.

---

### MB-01 Canonicalisation failure must not become a program outcome
- Matrix: O6, B8c, D-07, NF-01. Finding: probe `bigint`: `return 10**5000` vs `return 10**5001` gave NO_DIVERGENCE_OBSERVED S2, because `harness.py:76` (`str(v)` on an int) raises `ValueError` (4300-digit limit) inside the program `try` (`harness.py:213-218`), so both versions "raised ValueError" and compare equal.
- Files: `sbgv7/harness.py` (`_c` int branch, `_BASES` int conv, the call `try` at 213-218), possibly `sbgv7/runner.py:172` (phase handling).
- Change: encode ints without decimal conversion (for example `hex(int.__add__(v, 0))`; the comparator only needs equality); call `canon()` outside the program `try` so an exception raised by the harness itself becomes `phase="harness_error"` (already mapped to `tool_error`) and never an outcome.
- Acceptance (add to `test_harness_canon.py`): `10**5000` vs `10**5001` => `DIVERGENT_OBSERVABLE`; equal huge ints => not divergent and clean (non-lossy); a return value whose canonicalisation is forced to raise (monkeypatched `_c` in a harness unit run, or a descriptor that raises a `BaseException` subclass) gives `INSUFFICIENT(tool_error)`, never NDO; `verify` exits 0 on each.
- Size S. Blocks: none. Priority: first (false assurance on the `ret` channel).

### MB-02 Capture fd-level output in the stdout channel
- Matrix: B7b, S2c, S1i, D-16, OI-01, OI-20, NF-03; decision UD-3 option A (recommended). Finding: probe `subproc`: `os.write(1,b"A")` vs `b"B"` gave NDO S2; the parent already receives these bytes (`Result.stdout`, `isolation.py` stdout pump) but `runner.run` ignores them.
- Files: `sbgv7/runner.py` (`Ctx.run`, where `d`/`out.obs` is built, lines 54-93), `sbgv7/compare.py:66-67` (stdout comparison), `sbgv7/harness.py` only if the observation shape needs a field, `sbgv7/decide.py:72` (leave the flag, now truthful for stdout).
- Change: when the child reaches the call, attach the parent-observed fd-1 bytes (normalised like stdout, capped) to the observation as part of the `side:stdout` channel (for example `obs["fd1"]`, included in the Observation record so `verify` recomputes it); `compare` treats it under `side:stdout`; truncation of the fd-1 pump sets `capture_truncated`.
- Acceptance (new tests in `test_core.py` or `test_phase2_fixes.py`): `os.write(1,b"A")` vs `b"B"` => `DIVERGENT_OBSERVABLE` (kind `side_effect`); identical `os.write` output => NDO as before; `subprocess.run(["/bin/echo","x"])` vs `"y"` under the sandbox => DIVERGENT; a program that writes nothing to fd 1 produces unchanged ids for existing tests except where the observation shape changed (update expected values consciously); `verify` exits 0.
- If UD-3 chooses option B instead: replace the change with "any fd-1 bytes set a blind-spot flag => `INSUFFICIENT(blind_spot_dominant)`" (same files).
- Size S. Depends: UD-3 (default A).

### MB-03 Normalise the source path in exception messages and stdout
- Matrix: C12, D-19, NF-02. Finding: probe `filepath`: `raise ValueError(__file__)` in base and variant files gave DIVERGENT.
- Files: `sbgv7/harness.py:17-18` (`norm`).
- Change: replace `SRC` and `os.path.dirname(SRC)` by `<SRC>` and `<SRCDIR>` (longest first) before the existing substitutions; apply to exception messages, stdout and fd-1 (MB-02).
- Acceptance: a pair whose only difference is a trailing comment and whose function raises `ValueError(__file__)` in both => not DIVERGENT (NDO with `r_empty`); a pair where the message text itself changes still => DIVERGENT.
- Size XS. Decision: SD-23.

### MB-04 Invariants as explicit raises; unknown reason code handling
- Matrix: V2, V13, D-18, NF-05. Finding: probe: `python -O` accepted `Verdict("EQUIVALENT", ...)` and `primary="bogus_code"`.
- Files: `sbgv7/records.py:38,85-88` (asserts), `sbgv7/decide.py:85` (`RANK[c]` KeyError), `sbgv7/verify.py` (reading a log with an unknown code).
- Change: `raise ValueError` for each invariant; `verify`/readers map an unknown code to INSUFFICIENT semantics (a `VerifyError` that names it) instead of an unhandled KeyError.
- Acceptance: a subprocess `python -O -c` constructing `Verdict("EQUIVALENT",...)` raises; same for an unknown primary code; `decide` with an injected unknown blocker code returns INSUFFICIENT (primary `tool_error`) rather than raising; existing `test_verdict_record_rejects_prohibited_values` still passes.
- Size XS.

### MB-05 A witness requires sandbox-verified, untampered replay and alt runs
- Matrix: A-14, NF-04, SD-10. Finding (code reading, not probed): `classify` checks tamper/sandbox only on primary and repeat runs (`runner.py:166-173`); replay/alt results update `ev.sandbox_ok` (`:193`) but the outcome stays `CONFIRMED_DIFF`, and `decide.py:79-81` returns the witness before any blocker.
- Files: `sbgv7/runner.py` (`classify`, lines 190-204), `sbgv7/decide.py` (no change expected).
- Change: after fetching replay and alt runs, if any run is not `sandbox_ok` or is `tampered` (or has `phase in import_error/harness_error`), set the outcome to `NO_RUN` and emit the real blocker (`sandbox_failure`, `unsafe_program`, `tool_error`) instead of `CONFIRMED_DIFF`.
- Acceptance (scripted-run test in `test_core.py` using the existing `Fake` runs of `test_replay_classes`): all 5 replays tampered => no witness, verdict `INSUFFICIENT(unsafe_program)`; one alt run not sandbox_ok => `INSUFFICIENT(sandbox_failure)`; a clean replay set still gives `CONFIRMED_DIFF`; `verify` agrees (classify is shared).
- Size S.

### MB-06 `sandbox_failure` for unverified required isolation properties
- Matrix: B3a, D-03, A-01, SD-07. Finding: unavailable limits are skipped silently (`isolation.py:111-114`); `runner.py:61` gates only on `SANDBOX_UNAVAILABLE`, cleanup and orphans.
- Files: `sbgv7/runner.py:36-52,61` (`Ctx.__init__` capability summary, `out.sandbox_ok`), `sbgv7/isolation.py` (expose a REQUIRED/ADVISORY split in `capabilities()` output or a helper).
- Change: required set (SD-07) = network_denial, write_confinement, process_group_kill, rlimit_cpu, rlimit_fsize, rlimit_nofile; if any is not ACTIVE every run is `sandbox_ok=False` (so probe => `INSUFFICIENT(sandbox_failure)`); advisory (`rlimit_as`, `rlimit_nproc`) recorded in the policy record and in `policy_below_minimum`.
- Acceptance: monkeypatched capabilities with `rlimit_cpu` UNAVAILABLE => `INSUFFICIENT(sandbox_failure)` at verdict level; with only `rlimit_as` UNAVAILABLE (this host) => verdicts unchanged and `policy_below_minimum` true; policy id differs between the two capability sets.
- Size S. Depends: SD-07.

### MB-07 Determinism control profile and wider alternate-control virtualisation
- Matrix: I1, X6, B4b, P5, D-14, OI-12, A-09, SD-09.
- Files: `sbgv7/isolation.py:118` (child env), `sbgv7/harness.py:175-179` (alternate settings), `sbgv7/runner.py:44-46` (env/policy record), config (H) if the profile becomes declared.
- Change: primary and replay runs get `PYTHONHASHSEED=0`, `TZ=UTC`, `LC_ALL=C.UTF-8`, `OMP_NUM_THREADS=MKL_NUM_THREADS=1`; record the Python minor version and flag `policy_below_minimum` if it is not 3.13; alternate settings additionally shift `time.monotonic`/`perf_counter`, replace `os.urandom` (and thus `uuid4`) by a seeded generator, keep `random.seed`; document that `datetime.now` is not virtualised.
- Acceptance: a program returning `list({"a","b","c","d","e"})` in both versions with one changed line => deterministic (no `nondeterministic`); a program whose difference comes only from `random`/`os.urandom` is not `CONFIRMED_DIFF` (quarantined or `ENV_SENSITIVE_DIFF`); a real (not scripted) `env_sensitive` case: difference that disappears under the alternate seed => `INSUFFICIENT(env_sensitive)`; pair/policy ids change when the profile changes.
- Size M. Note: K2-style determinism rates must be re-measured after this item.

### MB-08 Identity check before any side effect; one overwrite policy
- Matrix: V3, D-12.
- Files: `sbgv7/runner.py:295-300` (`compare_versions`), `sbgv7/records.py:97-101` (`EvidenceLog.__init__` truncates silently), `sbgv7/__main__.py:30`.
- Change: read both sources and raise `Ineligible` before `os.makedirs` and before the log is opened; `EvidenceLog` refuses to overwrite an existing file unless explicitly told to.
- Acceptance: identical pair leaves no `evidence.jsonl` and a second identical invocation also exits 3 (not 2); calling `compare_versions` twice into the same non-identical output directory raises instead of truncating.
- Size XS.

### MB-09 Pair identity covers repeat, suff and policy (H)
- Matrix: F18, D-10, SD-20.
- Files: `sbgv7/runner.py:47,52`, `sbgv7/verify.py:59-60`, `test_core.py::test_repeated_runs_reproduce_ids_and_chain`.
- Change: `h_id = content_id("H", [cfg["harness"], cfg["repeat"], cfg["suff"], harness_sha])`; `pair_id` additionally includes `policy_id`; budget stays out (stored in the package); verify recomputes the same.
- Acceptance: two runs differing only in `r_det` have different `pair_id`; differing only in `budget.cpu_seconds` have the same `pair_id`; `verify` exits 0; ids stay stable across invocations.
- Size S.

### MB-10 Name the real cause of a `NO_RUN` input
- Matrix: B6, D-04, OI-09. Finding: `decide.py:51` adds `resource_limit` for every `NO_RUN` except `invalid_input`; probe `sysexit` shows `unsafe_program` with a spurious secondary `resource_limit`.
- Files: `sbgv7/runner.py:169-182` (set `ev.reason` to one of `both_limit`, `sandbox`, `tamper`, `import`, `tool`, `invalid_input`), `sbgv7/decide.py:51`.
- Change: only `both_limit` maps to `resource_limit`; other causes already carry their own blocker via `stat` and map to None here. The conservative blocking policy itself is unchanged (UD-4).
- Acceptance: protocol-violation input => primary `unsafe_program`, secondary has no `resource_limit`; both-sides-limit input still => `resource_limit`; `test_no_run_input_blocks_no_divergence` and `test_property_incomplete_evidence_never_positive` pass; `verify` exits 0.
- Size S. Depends: none (UD-4 only changes later whether both-limit blocks).

### MB-11 Budget: charge parent CPU, check between runs
- Matrix: P7, B9, D-13, A-17, SD-19.
- Files: `sbgv7/runner.py:59,305-310`.
- Change: add the parent's `time.process_time()` delta to `spent`; check the budget inside `process_input` before each child run (stop at run granularity, remaining runs of that input are not started and the input is dropped or marked incomplete, which blocks as `budget_exhausted_s0`).
- Acceptance: a tiny budget stops mid-input with `budget_exhausted_s0`; `cpu_seconds_spent` >= child CPU sum; the last input exhausting the budget with unhit units => `budget_exhausted_s0` rather than `changed_region_not_activated` (SD-19); `test_budget_exhausted` updated and green.
- Size S.

### MB-12 Merkle run-set root and factor vector in the SufficiencyRecord
- Matrix: S1a, OI-04.
- Files: `sbgv7/runner.py:278-283`, `sbgv7/records.py` (small Merkle helper), `verify.py` (recomputes the body through `finalize`, so no change expected).
- Change: `run_set_root` = binary Merkle root over sorted run ids; add `factors` = {F1: quarantined count and r_det, F2: truncation/tamper/lossy flags, F3: units_hit/units_total, F4: inputs_same and stop_reason}; keep existing keys.
- Acceptance: root changes if any run id is added or removed; root is order-independent; `verify` exits 0; record keys present.
- Size S.

### MB-13 Accept FS constant config fields
- Matrix: F2, F6, F7, D-11, OI-07, SD-18.
- Files: `sbgv7/config.py:41-50` (SCHEMA), `sbgv7/runner.py:47` (H includes them).
- Change: `harness.normaliser_id` (only `"N1"`), `harness.stderr` (only `"excluded"`), `harness.capture_tier` (only `"L0"`) accepted and defaulted; any other value raises `ConfigError("not built")`; no other field is added.
- Acceptance: a config with those three keys at their constants loads and gives the same verdict as `{}`; a different value exits 2 with the message; `test_bad_config` extended.
- Size XS.

### MB-14 CLI failure handling and exit codes
- Matrix: X2, A-11, SD-13.
- Files: `sbgv7/__main__.py:26-38`.
- Change: catch `OSError` around the output-directory/log creation and map to exit 2 with a one-line message; catch any other `Exception` from `compare_versions` and exit 1 with a one-line message (no traceback); document codes in the module docstring.
- Acceptance: `--out` pointing at an existing file => exit 2, no traceback; an unwritable `--out` => exit 2; `python -m sbgv7 --help` exits 0; identical pair exits 3 (also covered by MB-08).
- Size XS.

### MB-15 Record a digest of the V6 `changed_lines` code in the package
- Matrix: D-23.
- Files: `sbgv7/runner.py:7,312-315`, `sbgv7/verify.py:65-66`.
- Change: store `sha256` of `sbgv6/features.py` (the module providing `changed_lines`) in `EvidencePackage`; verify fails with a clear message if the live digest differs (regions would not be reproducible).
- Acceptance: package contains the digest; a tampered recorded digest => `VerifyError`; unchanged tree => verify 0.
- Size XS. (Vendoring the function into `sbgv7/` is the alternative and also acceptable; do not edit `sbgv6/`.)

### MB-16 Test-gap closure (tests only)
- Matrix: B2a, B7a, B6, O3, W5, S2a, C2, I8, F1/F9 defaults, E1; audit section 3 items 1-12.
- Files: `tests/v7/` (new `test_conformance_gaps.py`, or additions to `test_core.py`/`test_phase2_fixes.py`).
- Tests to add: (1) `capture_truncated` end to end (print 40000 chars => `INSUFFICIENT(capture_truncated)`, probe-confirmed); (2) `alignment_failed` via `static_phase` with a stubbed `_regions` that raises; (3) `SystemExit(3)` vs `SystemExit(4)` => DIVERGENT and equal `SystemExit(3)` => equal (exited class); (4) stderr-only difference => NDO (excluded channel); (5) witness `locus == "unlocalised"`; (6) `load_config({})` equals the FS defaults table (c_obs, float_tol, ordered_mapping, exc_message, api_break_probe, r_det/r_replay/k_alt, s2_branch_floor, s3_enabled, budget 60, per_run 10/20/2048); (7) `policy_below_minimum` is `True` on darwin (strengthen `test_core.py:72`); (8) S2 coverage with two branches, a loop (`FOR_ITER`), a deleted line (base-only unit) and an inserted line (variant-only unit); (9) every record kind has the documented `evidence_class`; (10) `trace()` raises `ChainError` on a dangling ref; (11) CLI: exit 3 for identical, `--help` of `python -m sbgv7`; (12) make the module-level skip in `test_core.py:13` loud (a visible skip reason plus one always-run test that fails if `network_denial` is not ACTIVE on darwin).
- Acceptance: all new tests pass here; each fails when the corresponding behaviour is reverted (spot-check at least items 1, 3, 6, 8).
- Size M.

---

## Conditional items (not executable until the user decision is made)
- **CB-01 (UD-2 option B).** Cap `NO_DIVERGENCE_OBSERVED` at S1 when `r_empty` is true or branch coverage is vacuous: pass `r_empty` into `Evidence` (`runner.py:273-274`, `decide.py:27-36,65-74`); acceptance: probes `doc`/`nolines` give S1 with `r_empty`, a pair with real changed branches still reaches S2. Size XS.
- **CB-02 (UD-3 option B).** Replace MB-02 with a blind-spot flag (see MB-02). Size XS.
- **CB-03 (UD-4 option B or C).** Precise "may have hit" for quarantined inputs (union of repeat hit lines) and non-blocking both-limit `NO_RUN`: `runner.classify`, `decide._blockers`; acceptance defined at decision time. Size S.
- **CB-04 (UD-1 option B or C).** Only if UD-1 reverts A-L1; revert `decide.py:56-58` and `runner.py:263`.

## Not in this backlog (with reason)
Specification corrections (17 matrix rows, 18 ambiguities): documents, see `FINAL_SPECIFICATION_DECISIONS.md`. Optional functionality (early replay stop, declared rename, entry lifting, minimisation, tolerance exactness): additive, no verdict risk. Deferred/Phase 3: see the first paragraph. Documentation drift outside the owned files (README test counts, readiness report, `IMPLEMENTATION.md` statements): their owners; current facts are 169 tests, 168 passed + 1 skipped, about 40 s.
