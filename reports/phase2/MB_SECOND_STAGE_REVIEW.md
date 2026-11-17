# MB-01..MB-16 second-stage review (Phase 2, local only)

Scope: uncommitted working tree on `research/v7b-final-validation` (HEAD f2aa9143). Local macOS, no Docker/Linux/third-party code, no experiments, `results/` and `artifacts/` untouched (`git status` shows no change there), nothing committed, V5/V6 code untouched, nothing about Phase 3. Everything below that says "isolation" means LOCAL ENVIRONMENT CONTROL; it is NOT validated operating-system isolation.

## 1. Line-by-line diff review (HEAD vs working tree), per file and hunk
Legend: OK = correct as written; NOTE = correct, residual risk; CHANGED = changed in this stage.

### sbgv7/isolation.py
| Hunk | Purpose | Correctness | Risk / suggested change |
|---|---|---|---|
| `Result.workdir` | give the parent the private cwd for normalising fd-1 bytes (MB-02/03) | OK; populated on every return path of `_run`; the finally-rmtree only removes it afterwards | none |
| `-I -B` to `-s -P -B` (both `cmd` constructions) | `-I` ignores `PYTHONHASHSEED` (SD-09) | OK given a from-scratch env (section 3) | CHANGED: the duplicated command is still built twice (once before, once inside `if channel`); harmless, not refactored |
| env dict | pin SD-09 profile | was OK but incomplete: no PYTHONUTF8/IOENCODING/NOUSERSITE/SAFEPATH pin | CHANGED: `child_env(workdir)` allowlist function, `DET_ENV` extended; env is the only source of PYTHON* variables |
| `DET_ENV`, `REQUIRED`, `ADVISORY` | profile and SD-07 table | OK; `DET_ENV` is a module global read at call time (tests monkeypatch it), so the policy id follows it | NOTE: `DET_ENV` is recorded in the policy record, so any edit changes every `policy_id`/`pair_id` (intended, MB-09) |

### sbgv7/harness.py
| Hunk | Purpose | Correctness | Risk |
|---|---|---|---|
| module docstring | scope statement | OK | none |
| `norm`: `<SRC>`, `<SRCDIR>`, workdir, then addresses | MB-03 | OK: longest first; `os.getcwd()` is realpath form, `norm_parent` handles both forms | NOTE: a message containing a different path that merely shares a prefix with SRCDIR is rewritten too; accepted |
| `_BASES` int as `hex(int.__add__(v,0))`, `_c` int as `hex(v)` | MB-01: `str(int)` raises past 4300 digits, `hex` does not | OK; type tag kept, negatives `-0x..` | NOTE: `sys.set_int_max_str_digits` no longer matters for canon; the user program's own `str(big)` still raises as program behaviour |
| ctl block: monotonic/perf_counter shift, seeded `os.urandom` | MB-07 | OK | CHANGED: also `random._urandom = os.urandom` so `secrets`/`SystemRandom` are seeded in alt runs; primary runs keep real entropy |
| `finish` | frame writer | WAS A DEFECT: `os._exit(0)` discards buffered `sys.__stdout__` writes, so a program that writes to the real stdout stream (not `print`, which is captured) had an unobserved channel | CHANGED: `sys.__stdout__.flush()` guarded by `except BaseException` before the frame; flushed bytes reach fd 1 and the parent folds them into `side:stdout` |
| canon moved outside the program `try` | MB-01: canon failure is `harness_error`, not an outcome | OK; falls to the outer `except BaseException` that builds `harness_error` | none |

### sbgv7/runner.py
| Hunk | Purpose | Correctness | Risk / suggestion |
|---|---|---|---|
| `FOLD_FD1`, `norm_parent` | MB-02/03 | OK; the same replacement order as the harness, plus realpath of workdir | NOTE: only attached when `phase == ok and mode == call`; probe and import_error runs never carry fd1 (not needed: they do not enter comparison) |
| `v6_digest` | MB-15 | OK for the module that defines `changed_lines` | NOTE: hashes only that file, not its imports; weak provenance. Suggest hashing the whole `sbgv6/features` closure later |
| `below_minimum` | SD-07/SD-09 flag | OK; always True on macOS and with `rlimit_nproc` hard-coded UNAVAILABLE | NOTE: the platform clause is never the deciding one in practice (see MB-16 item 7 weakness) |
| `BudgetStop`, `t0`, `cpu_total`, `over_budget` | MB-11 | OK: `time.process_time` charges parent CPU | NOTE: process-wide CPU, includes pump threads; fine, conservative |
| `required_ok`, `sandbox_ok` gate | MB-06 | OK | none |
| `policy`/`h_id`/`pair_id` | MB-07, MB-09 | OK; verify recomputes the same formulas | pair ids change for all old evidence (documented) |
| fd1 attach in `Ctx.run` | MB-02 | OK; capped 32 KiB sets `truncated` | NOTE: parent stdout pump cap is 4 MiB, so the effective bound is the 32 KiB slice |
| `_run_blockers`, `_no_run`, `classify` additions | MB-05, MB-10 | OK: replay and alt runs now checked for sandbox/tamper/phase; reason carried | none |
| `process_input` local `run` + `BudgetStop` | MB-11 | OK; `getattr(ctx,"over_budget", lambda: False)` keeps scripted `Fake` contexts working | NOTE: a run in progress is not interrupted (granularity is one run) |
| `finalize` (`budget_mid_input`, `policy_below_minimum`, `merkle_root`, `factors`) | MB-11/12 | OK | none |
| `compare_versions` | MB-08 identity before side effects; budget loop `for/else` | OK | none |

### sbgv7/records.py, verify.py, decide.py, config.py, compare.py, __main__.py, baselines.py
| File / hunk | Purpose | Correctness | Risk / suggestion |
|---|---|---|---|
| records `InvariantError`, `_inv` | MB-04 explicit raises (ValueError and AssertionError subclass) | OK, survives `-O` (tested) | none |
| records `merkle_root` | MB-12 | OK: sorted, de-duplicated, odd node promoted | NOTE: no leaf/node domain separation (`sha(i)` vs `sha(a+b)`); ids are 27-char strings so no practical collision; suggest a `0x00`/`0x01` prefix before this root is ever used for inclusion proofs |
| records `open(path, "x")` | MB-08 | OK | none |
| verify unknown reason code loop | MB-04 | OK (operator precedence of `A + B if cond else []` gives the intended result) | none |
| verify `h_id`/`pair_id` recompute, `v6_digest` check | MB-09/15 | OK; a package without the digest field is accepted (documented) | NOTE: leniency for old evidence |
| verify `finalize(..., pkg.get("policy_below_minimum"))` | MB-06 | OK | none |
| decide `NO_RUN` mapping, unknown code to `tool_error` | MB-10, MB-04 | OK; unknown legacy `None` reason stays conservative | none |
| config `_const` + 3 constant fields | MB-13 | OK; refuses other values rather than ignoring them | none |
| compare `(stdout, fd1)` tuple | MB-02 | OK; `a.get("fd1","")` keeps old observations comparable | none |
| `__main__` OSError to 2, Exception to 1 | MB-14 | OK; message only, no traceback | NOTE: `except Exception` hides internal tracebacks by design; consider `SBGV7_DEBUG` later |
| baselines `int(n[1], 0)` | MB-01 consequence | OK for `0x`, `-0x` | none |
| tests: `test_core` skip reason, `test_phase2_fixes` hex forged values | conscious expectation change | OK; no assertion weakened | none |

### Tests and docs
`tests/v7/test_backlog_mb.py`, `test_conformance_gaps.py`, `test_second_stage.py` (new), `docs/architecture/V7B_BACKLOG_STATUS.md`, `V7B_IMPLEMENTATION.md`, `scripts/mutation_check_mb.py` reviewed; changes of this stage are listed in section 6.

## 2. MB-01..MB-16 verification matrix (spec rule, implementation, tests, weak verification)
| MB | Spec rule | Implementation | Regression tests | Weak verification / residual |
|---|---|---|---|---|
| 01 | O6, B8c, D-07, NF-01, SD-15 | harness `_c`/`_BASES`/`main`; baselines `plain` | test_mb01_* (23) | none new; mutation (revert hex) killed 10 tests in stage 1 |
| 02 | B7b, S2c, S1i, D-16, UD-3 A | runner `Ctx.run`/`norm_parent`; compare; harness `finish` flush | test_mb02_*, test_second_stage buffered/closed/`os._exit` | fd-1 output buffered in a program-created stream (`os.fdopen(1)`) is still lost; user `os._exit` is `unsafe_program` (by SD-11) |
| 03 | C12, D-19, SD-23 | `norm`, `norm_parent` | test_mb03_* | none |
| 04 | V2, V13, D-18 | records `_inv`; decide; verify | test_mb04_* (also under `-O`: 13 passed) | none |
| 05 | A-14, SD-10 | runner `_run_blockers`, `classify` | test_mb05_* (scripted `Fake` runs) | tests use fakes for replay/alt; the live path is covered only by the generic end-to-end tests |
| 06 | B3a, D-03, SD-07 | isolation `REQUIRED`; runner `required_ok` | test_mb06_* | interpreter 3.13 is a flag, not a gate |
| 07 | I1, X6, SD-09 | isolation `DET_ENV`/`child_env`; harness ctl block | test_mb07_*, test_second_stage env/hostile/shadow/secrets/datetime | K2 rates not re-measured; `datetime.now` not virtualised; hash seed not varied in alt runs |
| 08 | V3, D-12 | runner identity check; records `open("x")` | test_mb08_* | none |
| 09 | F18, D-10 | `h_id`, `pair_id`, verify | test_mb09_* | none |
| 10 | B6, D-04, UD-4 A | `_no_run`, decide | test_mb10_* | UD-4 policy unchanged |
| 11 | P7, B9, D-13 | `Ctx.over_budget`, `BudgetStop` | test_mb11_* | in-flight run not interrupted |
| 12 | S1a, OI-04 | `merkle_root`, `factors` | test_mb12_* | no domain separation in the Merkle hash (above) |
| 13 | F2, F6, F7, D-11 | config `_const` | test_mb13_* | none |
| 14 | X2, A-11 | `__main__` | test_mb14_* | none |
| 15 | D-23 | `v6_digest` | test_mb15_* | hashes one file only; old packages without the field accepted |
| 16 | B2a, B7a, B6, O3, W5, S2a, C2, I8, F1/F9, E1 | tests only | test_conformance_gaps.py (13 tests, 12 sub-items) | see section 4 |

## 3. MB-07: `-I` versus `-s -P -B`, controlled child environment
**Experiment** (scratchpad probe script, `.venv` Python 3.13.15, parent env cleared with `env -i` and then loaded with hostile variables):
| Item | `-I -B` | `-s -P -B` + env passed through | `-E -s -P -B` | what we ship: `-s -P -B` + allowlist env |
|---|---|---|---|---|
| PYTHONPATH / PYTHONHOME / PYTHONSTARTUP / PYTHONUSERBASE / PYTHONWARNINGS / PYTHONMALLOC / PYTHONDEVMODE / PYTHONSAFEPATH / PYTHONIOENCODING / PYTHONUTF8 / PYTHONINSPECT | all ignored (`ignore_environment=1`) | all honoured; with PYTHONHOME=/nonexistent the interpreter dies (`No module named 'encodings'`); PYTHONPATH puts the attacker's dir on `sys.path` | ignored | not present in the child at all (never inherited) |
| PYTHONHASHSEED | IGNORED: `hash('a')` differs on every start even with `PYTHONHASHSEED=0` | honoured: constant `4644417185603328019` for seed 0 | ignored | `0`, constant |
| user site / `usercustomize` | off (`no_user_site=1`) | off with `-s` | off | off (`-s` plus `PYTHONNOUSERSITE=1`) |
| `sys.path[0]` / cwd / script dir | not added (`-P` implied) | not added with `-P` | not added | not added (`-P` plus `PYTHONSAFEPATH=1`); private cwd |
| `sys.flags.isolated`, `ignore_environment` | 1, 1 | 0, 0 | 0, 1 | 0, 0 (program-visible, not a compared channel) |
| PYTHONDONTWRITEBYTECODE | ignored by `-I` but `-B` given | env or `-B` | same | `-B` and env |
| TZ / LC_ALL / locale / UTF-8 mode | ignored LC_*; UTF-8 mode from C locale | honoured | LC_* still honoured by libc | pinned `TZ=UTC`, `LC_ALL=C.UTF-8`, `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8:strict` |
| `sitecustomize` | imported from `sys.path` | same | same | imported only from the interpreter's own site-packages (none exists in this venv); no PYTHONPATH can add one |
| LD_PRELOAD / DYLD_INSERT_LIBRARIES | not interpreter flags: honoured by the dynamic loader if present in the env | same | same | not present in the child env |

**Can inherited env affect the child?** At HEAD already no: `Popen(env=...)` was a literal dict (the parent environment was never forwarded), so `-I` was redundant for env protection and only had the side effect of killing `PYTHONHASHSEED`. After this stage the allowlist is a named function (`isolation.child_env`), and `-I` cannot be restored without breaking SD-09 because the hash seed is read once at interpreter start. Choice justified by the experiment: `-s -P -B` plus an allowlist built from scratch (not inherit-then-strip) is the strongest configuration that preserves `PYTHONHASHSEED`; the only extra surface compared with `-I` is a program-visible flag difference.
**Hostile-environment tests** (`tests/v7/test_second_stage.py`): parent env with `PYTHONPATH` to a directory holding malicious `sitecustomize`, `usercustomize`, `json`, `os`; `PYTHONHOME`, `PYTHONSTARTUP`, `PYTHONINSPECT`, `PYTHONBREAKPOINT`, `LD_PRELOAD`, `DYLD_INSERT_LIBRARIES`, `DYLD_LIBRARY_PATH`, `PYTHONUSERBASE`, `PYTHONWARNINGS=error`, `PYTHONHASHSEED=random`, `PYTHONMALLOC`, `PYTHONDEVMODE`, `PYTHONOPTIMIZE`, locale/TZ and others (27 variables). Asserted for hostile and clean: child env equals the allowlist exactly (plus macOS `__CF_USER_TEXT_ENCODING`, CPython `LC_CTYPE`), `sys.path` has no attacker dir/cwd/empty entry, flags (`no_user_site`, `safe_path`, `dont_write_bytecode`, `utf8_mode`, not dev mode/inspect), hash equals the `PYTHONHASHSEED=0` reference, `tzname`, encodings, no warnoptions/xoptions, default `breakpointhook`, `json`/`os` from the stdlib, `orig_argv` contains `-s -P -B` and not `-I`; end to end the hostile run yields identical verdict, pair id, verdict id and observation ids as the clean run, and `verify` passes. Mutation checks: inheriting `os.environ` and dropping the hash seed are both caught.
**Trusted controller cannot be shadowed**: the harness inserts the PROGRAM directory at `sys.path[0]` (sibling imports must work), so safety depends on every trusted import being done before. `test_program_directory_cannot_shadow_trusted_modules` writes a killing shadow file for every public stdlib module name into the program directory and runs primary and alt runs with a rich return value: no shadow is hit, outcome `SAME`, parent `sys.modules`/`sys.path` unchanged. The parent never adds the program directory to its own path.
**What this is not**: local environment control, not validated OS isolation. sandbox-exec is deprecated and macOS-only; Linux/Docker confinement does not exist; process-group escape via `setsid` is not covered.
**Scientific validity of K2 and what must be rerun.** Before MB-07 the children hashed strings with a random seed even though `experiments/v7b/k1_spike.py` set `PYTHONHASHSEED=0` in its own env (never forwarded). Programs whose output depends on set/dict-of-str order were therefore `nondeterministic` before; now they are deterministic, so the determinism rate (K2) can only increase, the activation census changes, and hash-order-dependent differences can no longer be detected as env-sensitive (the alt runs keep seed 0). Together with MB-01 (hex ints), MB-02 (fd-1 folded into stdout), MB-09 (pair id includes repeat/suff/policy) and MB-12 every evidence id changes. Must be re-measured in Phase 3 (not run here): `results/raw/k1_spike*` and `results/raw/k1_spike_postfix*` (outputs of `experiments/v7b/k1_spike.py`), and the reports that quote them: `research/evaluation/K1_K2_FEASIBILITY_REPORT.md`, `EXPLORATORY_RESULTS.md`, `POSTFIX_RERUN_NOTE.md`. Old logs are not re-verifiable for pair id. V5/V6 results do not use `sbgv7` and are unaffected.

## 4. MB-16 mutation-sensitivity evidence
`scripts/mutation_check_mb.py` copies `sbgv6`, `sbgv7`, `tests/v7` into a fresh temp dir per mutation, checks the copy is the one imported, applies ONE text substitution to the copy, runs the one named test in the copy (baseline must pass, mutant must fail), and exits non-zero if any mutant survives. The working tree is never written. Result: **16/16 mutants killed** (11 MB-16 items, 5 second-stage checks).
| MB-16 item | Test | Mutation applied to the copy | Result |
|---|---|---|---|
| 1 capture_truncated | test_capture_truncated_end_to_end | decide: disable the truncated blocker | killed |
| 2 alignment_failed | test_alignment_failed_via_static_phase | runner: report `unsupported_signature` instead | killed |
| 3 SystemExit code | test_systemexit_code_is_compared | compare: ignore exit code | killed |
| 4 stderr excluded | test_stderr_only_difference_is_not_observed | runner: fold stderr into fd1 | **first run: SURVIVED**. Cause: the test wrote `'a'` without newline; stderr is line-buffered and the harness ends with `os._exit`, so stderr was empty and the test passed vacuously. Fixed (newline added); now killed |
| 5 locus | test_witness_locus_unlocalised | records: `locus="line:1"` | killed |
| 6 defaults | test_defaults_table_item6 | config: `r_det` 3 to 2 | killed |
| 7 policy_below_minimum | test_policy_below_minimum_true_on_darwin | runner: `below_minimum` returns False | killed. WEAK: on macOS the flag is true anyway through the hard-coded `rlimit_nproc` UNAVAILABLE, so the `sys.platform == "darwin"` clause is not independently verified; alternative verification: the unit test `test_mb07_python_minor_version_flags_policy` monkeypatches platform and Python version and checks `below_minimum` directly |
| 8 FOR_ITER | test_s2_coverage_loop_for_iter | runner: drop `FOR_ITER` from `BRANCH_OPS` | killed |
| 9 evidence class | test_record_kinds_have_documented_evidence_class | records: default class `derived` | killed |
| 10 dangling ref | test_trace_raises_chain_error_on_dangling_ref | records: skip dangling refs | killed |
| 11 CLI | not a separate test | covered by test_mb08_* and test_mb14_help_exits_0 | not mutated here (CLI exit paths mutated in stage 1 evidence) |
| 12 loud, not skipped | test_loud_not_skipped_sandbox_must_be_active_on_darwin | isolation: force `network_denial` UNAVAILABLE | killed |
Second-stage mutants (all killed): child env inherits `os.environ`; hash seed dropped; stdout flush removed; `random._urandom` not rebound; alt time shift removed (proves the rebuilt `test_mb07_real_env_sensitive_case` really depends on the shift).

## 5. Flaky `test_mb07_real_env_sensitive_case`, output capture, determinism, evidence integrity
**Flaky test.** Old construction `(int(time.time()) // 1000) % 2` fails whenever a 1000 s epoch boundary falls inside the primary, repeat, replay or alt runs. New construction is boundary-free: the program creates a file in its private cwd and returns `1 + (abs(mtime - time.time()) > 500)`; the filesystem clock is not virtualised but `time.time` is shifted +1000 s x ctl in alt runs only, so the value is 1 in primary/replay and 2 in alt at any wall-clock moment. 50 consecutive pytest invocations: **50/50 passed**.
**Output capture at `os._exit`.** Frozen spec s4 (`reports/final/V7B_FROZEN_SPEC.md:45`): "`C_obs`: return value; exception ...; declared side effects (stdout, sandbox temp content, argument post-call digests, module globals written). Excluded: stderr ...". Defect confirmed: output written through the real stream `sys.__stdout__` is buffered and the harness ends with `os._exit(0)`, so it vanished and two versions differing only there were reported SAME (a false-assurance path in a declared channel). Fix (safe, harness-controlled exit path): flush `sys.__stdout__` in `finish`, guarded by `except BaseException`; bytes then reach fd 1 and MB-02 folds them into `side:stdout`. Tests: write / print(file=sys.__stdout__) / import-time, differing is DIVERGENT, identical is not, closed stdout does not break the harness. Precise remaining limits: a program-created stream around fd 1 (`os.fdopen(1)`, `open(1,'w')`) with unflushed data; any output after the program itself calls `os._exit`/`os.abort` (no result frame, so `unsafe_program` by SD-11, tested with print then `os._exit`); stderr (excluded by contract; a user's unterminated stderr write is also lost, which has no effect on the verdict).
**Determinism table.** Maintained in `docs/architecture/V7B_IMPLEMENTATION.md` ("Child environment and determinism"): virtualised in alt runs: `time.time/_ns`, `monotonic`, `perf_counter`, global `random` seed, `os.urandom`, `uuid4`, and now `secrets`/`SystemRandom`; env only: hash seed, locale, TZ, UTF-8, threads env, `os.environ`, cwd; not controlled: `datetime.now/utcnow/today`, `id()`/addresses (only `0x....` text is normalised), pid, thread scheduling, `process_time`, filesystem state outside the private dir, direct `/dev/urandom`. Decision: `datetime.now`/`today` are NOT virtualised: the only way is replacing `datetime.datetime`, which changes type identity in canonical forms (`datetime.datetime` name), `isinstance`/pickling behaviour and is not cheap or safe; SD-09 keeps its documented "not virtualised" semantics, characterised by `test_datetime_now_is_NOT_virtualised_documented_limit`. `secrets`/`SystemRandom` rebinding is a one-line extension of SD-09's `os.urandom` item (same entropy source); it only affects alt runs and is tested in both directions (primary keeps real entropy).
**Evidence integrity.** The log is an unkeyed plaintext SHA-256 chain plus content ids. A writer of `DIR` can recompute every id and hash and rewrite `verdict.json` (same directory, so its `log_head` check proves nothing against that writer); `verify` accepts it. It is therefore not tamper-evident against a deliberate writer and not tamper-proof. Trust anchor required: pinned `log_head`/verdict id outside `DIR`, signature over `log_head` with a key the producer cannot use afterwards, append-only store without rewrite rights, trusted timestamp. Wording: V7-B docs now say this explicitly (`V7B_IMPLEMENTATION.md`; the `verify` exit-1 text changed from "tamper" to "inconsistency detected"), guarded by `test_v7b_docs_do_not_claim_tamper_proof` (affirmative "tamper-proof"/"immutable" claims in `docs/architecture` and `sbgv7/` fail).
Search results for `tamper-proof|tamper proof|immutable|tamper-evident` (grep of `docs/ README* reports/ paper/`):
- V7-B documents corrected or already clean: `docs/architecture/*` (clean after edit; no affirmative claims), `sbgv7/*.py` (clean).
- V7-B documents containing the claim, NOT edited (outside owned scope or frozen): `reports/final/V7B_FROZEN_SPEC.md:51` (Witness "Immutable; voidable only by Supersession", frozen), `reports/phase2/PHASE_2_SPEC_CONFORMANCE_AUDIT.md:95` and `FINAL_V7B_REQUIREMENTS_TRACEABILITY_MATRIX.md:120` (state "immutable by chain; no Supersession", accurate as a gap statement), `paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/sections/definitions.tex:10` and `figures/evidence_witness_model.dot:5` ("immutable" witness: should read "append-only, hash-chained; not tamper-evident without an external anchor"), `reports/v7_design/**` (design history: `SBG_V7_ARCHITECTURE_MASTER_PLAN.md:33`, `COMPETING_ARCHITECTURES.md:54,178`, `FINAL_ARCHITECTURE_DECISION.md:4,25`, `IMPLEMENTATION_ROADMAP.md:51,92,350`, `DATA_AND_EVIDENCE_SCHEMA.md:356`, `MODULE_CONTRACTS.md:441`, `reconciled/*`, `p0_reconciliation/*` including `P0_RECONCILED_MODULE_CONTRACTS.md:56,475` "tamper-proof tracing" listed as unverified, plus the `_original_archive` copies).
- V5/V6 historical files (not edited): `docs/archive/superseded/pre_strengthening_baseline.md`, `external_validation_baseline.md`, `pre_repair_baseline.md`, `docs/archive/v4/V4_HOSTILE_REVIEW.md`, `V4_STATISTICAL_INTEGRITY.md`, `docs/archive/v3/SP2_FORENSIC_REPORT.md`, `reports/remediation/agent_a_sp2_repair.md`, `paper/empirical_sprint_*`, `paper/final_empirical_readiness_*` (the "immutable" there refers to frozen V1-V3 artifacts or unrelated Java/Python code).
- Zero hits for the literal strings "tamper-proof", "tamper proof", "tamper-evident" in any V7-B document before this stage; "immutable" was the only claim.

## 6. Updated risk register
| ID | Risk | Status after this stage | Next step |
|---|---|---|---|
| R1 | Hash order not detectable as env-sensitive (seed fixed in alt runs) | NEW, accepted | optional: vary seed in alt runs in a later decision (changes SD-09) |
| R2 | `datetime.now/today` unvirtualised, false witness possible | documented limit | decide in a later SD whether to virtualise via subclass |
| R3 | Harness shares the process with the program (D-02 is protocol correctness) | open, documented | Phase 3 |
| R4 | `-I` dropped: flags visible, no kernel/loader hardening | accepted, env allowlist + tests | none |
| R5 | K2/K1 numbers measured before MB-07/MB-01/MB-02 not comparable | open, listed in section 3 | Phase 3 re-measure |
| R6 | Plaintext forgeable hash chain | open, documented, test guards wording | add anchor (signature/pinned head) in Phase 3 |
| R7 | MB-16 item 4 vacuous test | FIXED | none |
| R8 | Flaky env-sensitive test | FIXED (50/50) | none |
| R9 | Buffered `sys.__stdout__` loss | FIXED for the harness-controlled path; residual limits listed | none |
| R10 | Item 7 platform clause only weakly tested | open (low) | if `rlimit_nproc` ever becomes ACTIVE, add a direct platform test |
| R11 | Merkle root without domain separation; `v6_digest` single file | open (low) | prefix leaf/node; hash the import closure |
| R12 | macOS-only sandbox, deprecated, not a validated boundary; Linux/Docker absent | open | Phase 3 |
| R13 | `-X` options/`sys.orig_argv` and `__CF_USER_TEXT_ENCODING` visible to program | accepted | none |

## 7. Security and determinism assessment
Security: result-channel correctness (HMAC frame, one frame, per-run key) is a correctness property against accidental or naive output forgery; a hostile program in the same address space can still read harness closures. Environment control is now an explicit allowlist with hostile-parent tests; import-path hijack of the trusted code is covered by the all-stdlib shadow test. None of it is validated OS isolation.
Determinism: the profile (hash seed, TZ, locale, UTF-8, single-thread env) plus alt-run virtualisation of time, random, urandom/uuid4/secrets gives repeatable runs for the common nondeterminism sources; the unvirtualised sources are listed in the table and are the reason `k_alt` alt runs run for every candidate witness.

## 8. Exact remaining changes (none blocks the Phase 2 backlog)
1. (Phase 3) re-measure K1/K2 on the new engine; do not cite pre-change numbers.
2. (decision) vary `PYTHONHASHSEED` in alt runs if hash-order sensitivity should surface as `env_sensitive`.
3. (decision) subclass-based `datetime` virtualisation, or keep the documented limit.
4. (low) Merkle leaf/node prefix; hash the V6 import closure in `v6_digest`; direct platform test for `below_minimum` once `rlimit_nproc` is verifiable.
5. (docs, outside owned scope) reword "immutable" in `paper/IEEE_ACCESS_INITIAL_MANUSCRIPT/sections/definitions.tex:10` and `figures/evidence_witness_model.dot:5`; frozen spec W3 stays as written.
6. (Phase 3) evidence trust anchor: pinned `log_head` and signature.
Files changed in this stage: `sbgv7/isolation.py` (`child_env`, `DET_ENV`), `sbgv7/harness.py` (stdout flush, `random._urandom` rebind), `tests/v7/test_second_stage.py` (new, 15 tests), `tests/v7/test_backlog_mb.py` (rebuilt flaky test), `tests/v7/test_conformance_gaps.py` (item 4 newline), `scripts/mutation_check_mb.py` (new), `docs/architecture/V7B_IMPLEMENTATION.md`, `docs/architecture/V7B_BACKLOG_STATUS.md`, this report.

## 9. Test evidence (commands and results, all run from the repo root)
- Baseline before changes: `.venv/bin/python -m pytest tests/v7 -q` = 261 passed, 1 skipped.
- Failing-test-first: new `test_second_stage.py` initially failed on the allowlist pins (3 env vars), the three buffered-stdout tests, the secrets test and the docs wording test; hostile-env, shadow and flaky-replacement tests passed immediately (the from-scratch env already protected HEAD; they are guards, confirmed by the inherit-env mutant).
- Final: `.venv/bin/python -m pytest tests/v7 -q` = **276 passed, 1 skipped** (the one skip is the pre-existing one).
- `-O` subset: `.venv/bin/python -O -m pytest tests/v7 -q -k "mb04 or invariants or rejects_prohibited"` = 13 passed.
- Flaky loop: 50 runs of `tests/v7/test_backlog_mb.py::test_mb07_real_env_sensitive_case` = 50 passed.
- Mutations: `.venv/bin/python scripts/mutation_check_mb.py` = 16/16 mutants killed (`--only "item 4"` re-run after the fix: killed).
- Probe files lived only in the scratchpad; `git status` shows no change under `results/` or `artifacts/`.
