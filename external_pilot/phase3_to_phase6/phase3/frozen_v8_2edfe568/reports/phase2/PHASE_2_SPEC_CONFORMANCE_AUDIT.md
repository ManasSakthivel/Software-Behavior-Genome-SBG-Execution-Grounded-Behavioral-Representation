# Phase 2: Repository and Specification-Conformance Audit of `sbgv7`

Branch `research/v7b-final-validation`, HEAD `1206312e`. Read-only audit; no code, test, result, V5/V6 file or spec was changed. This file is the only file written.

Method: read `reports/final/V7B_FROZEN_SPEC.md` (FS), `reports/final/P0_FINAL_RECONCILIATION_REPORT.md`, `P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md` (SPEC), `P0_RECONCILED_MODULE_CONTRACTS.md` (CONTRACTS), `docs/architecture/V7B_IMPLEMENTATION.md` (IMPL); read all of `sbgv7/*.py` (1,080 lines, excluding `baselines/`) and `tests/v7`; ran `.venv/bin/python -m pytest tests/v7 -q` once (**91 passed, 1 skipped, 21.9 s**; the skip is `test_memory_rlimit_as_hard`, because `rlimit_as` is UNAVAILABLE on this macOS host) and 12 small CLI probes in a scratchpad directory outside the repo (`.../scratchpad/exp2`, not committed). Where a finding rests on a probe it is marked **[probe]**; all others are from reading the cited lines.

Authority order (FS header): D1-D11 > SPEC > FS. Where FS and SPEC disagree and FS is not silent, I treat that as an inconsistency (section 2B), not as "SPEC governs".

Status legend: **C** Conforms, **D** Deviates, **N** Not implemented, **U** Unverifiable (cannot be decided from code or tests alone). Test column cites `test_core.py` unless prefixed `iso:` (`test_isolation.py`), `cli:` (`test_cli_help_safe.py`). "none" means no test asserts the behaviour.

---

## 1. Conformance matrix

### 1.1 Verdicts and precedence (FS s2, SPEC 3.3, 12.1)

| ID | Requirement | Implementation | St | Test |
|---|---|---|---|---|
| V1 | Exactly three verdict values | `records.py:7`, asserted `records.py:70` | C | 271, 310 |
| V2 | Prohibited outcomes (`EQUIVALENT`, `SAME`, `PASS`, `VERIFIED`, `SAFE`) unrepresentable | closed enum `records.py:7`; enforced with `assert` (`records.py:70-73`), so stripped under `python -O` (D-18) | C (weak) | 271; 310 checks only the substring "EQUIV" |
| V3 | Row 0: identical src/deps/runtime gives no verdict, excluded | `runner.py:188-189`; source bytes only (deps/runtime never hashed); evidence log already created at `runner.py:186-187` **[probe: a second run into the same dir exits 2]** | D | 148 (exception only); CLI exit 3 none |
| V4 | Row 1: any non-voided `CONFIRMED_DIFF` gives `DIVERGENT_OBSERVABLE` before any B-check | `decide.py:77-79` | C | 43, 302 |
| V5 | Row 2: any B1..B9 gives `INSUFFICIENT(primary=min rank; secondary)` | `decide.py:80-84`; secondary re-sorted alphabetically in `records.py:75` | C | 289, 310 |
| V6 | Row 3: else `NO_DIVERGENCE_OBSERVED(highest level whose floors hold)` | `decide.py:85`, `sufficiency` `decide.py:63-72` | C | 65-70 |
| V7 | Missing record counts as true | `decide.py:40,45-46` | C | 289, 310 |
| V8 | `DIVERGENT_OBSERVABLE` absorbing; voided only by `Supersession` (failed audit replay, drift) | no Supersession, no audit replay (IMPL:31) | N | none |
| V9 | Early stop at first witness is permitted; sufficiency not scored for DIVERGENT | `runner.py:225`, `runner.py:238` | C | 43 |
| V10 | NDO statement: every changed unit ran in each version containing it | unit set is changed lines intersected with executable lines (`runner.py:208-210`), so non-executable changed lines are dropped (D-05) | D | 82-88; docstring case none **[probe]** |
| V11 | `internal_divergence` absent when module E off | field never emitted (`runner.py:250-253`) | C | none |
| V12 | S0 only inside INSUFFICIENT, never with NDO | `records.py:71`, `runner.py:240` | C | 82-88, 271 |
| V13 | Unknown reason code downgrades to INSUFFICIENT | code raises `AssertionError` (`records.py:72-73`) or `KeyError` (`decide.py:83`) instead of downgrading | D | 271 (asserts the raise) |

### 1.2 Blocking conditions and reason codes (FS s2, s7; SPEC 3.3, 9)

| ID | Requirement | Implementation | St | Test |
|---|---|---|---|---|
| B0 | 18-code closed enum, retired codes absent | `records.py:8-11` equals the FS list exactly | C | 271 (one negative case) |
| B0r | Ranks B1..B9 | `decide.py:8-11` matches FS table; tie-break inside a rank unspecified in spec, code uses alphabetical `decide.py:83` | C / A-07 | 310 checks rank order only |
| B1 | `import_error` (build/import/entry resolution) | probe `runner.py:198`; call-run import error `runner.py:139-140` | C | 92-93 |
| B2a | `alignment_failed` | only if `changed_lines` raises (`runner.py:211-212`); unreachable in practice after a successful import probe | D | none |
| B2b | `unsupported_signature` (entry missing; incompatible sig with probe off) | `runner.py:199,203-204` | C (partial: no lifting) | 94-95, 106-107 |
| B2c | `ambiguous_entry` | never produced; `--entry` is a mandatory single identifier (`__main__.py:13,18`) | N | none |
| B2d | `unmodelled_change` (non-AST change, dependency/config change) | never produced (IMPL:28) | N | none |
| B3a | `sandbox_failure` when a property is violated **or unverified** | only: probe runs, `SANDBOX_UNAVAILABLE`, orphans, cleanup, rlimit-apply failure (`runner.py:60,196`). Unavailable `rlimit_as`/`rlimit_nproc`/etc. are silently skipped (`isolation.py:79-84`) and the run proceeds as sandbox_ok. **[probe: 3 GiB allocation under `rss_mib=2048` gave NDO S2]** | D | iso:106 (isolation layer only); verdict-level none |
| B3b | `unsafe_program` (policy violation, tamper) | never produced; `Evidence(tampered=False)` hard-coded at `runner.py:233`, per-run `tampered` (`runner.py:69,77`) never aggregated; IMPL:28 and `INDEPENDENT_RED_TEAM_REVIEW.md:61` say "except trace tamper", which is untrue | N | none (`decide.py:42` branch untested) |
| B4a | `flaky_witness` (replay disagreed) | `runner.py:168-170`, `decide.py:49` | C | 175-193 scripted only |
| B4b | `env_sensitive` (control-sensitive, fails `k_alt`) | `runner.py:172-175`; runs for every candidate, not only control-consulting ones (D-14) | D | 175-193 scripted only |
| B5 | `nondeterministic`: quarantined input that hit or may have hit a changed unit | every quarantined input blocks (`decide.py:49-51`, `runner.py:150-151`), hit or not | D (conservative) | 113 |
| B6 | `resource_limit`: exactly one side ended in a harness limit | `LIMIT_ASYMMETRIC` `runner.py:154`; plus `NO_RUN` of any cause (both-limit, sandbox, import error, harness error) also maps to `resource_limit` (`decide.py:50`) | D | 127-134, 343 |
| B7a | `capture_truncated` | `runner.py:68,137,165`, `decide.py:48` | C | none |
| B7b | `blind_spot_dominant` / blind spot in a changed unit | never produced | N | none |
| B8a | `no_inputs` (no deterministic-confirmed SAME input) | `decide.py:53-54` | C | 97 |
| B8b | `unobservable_outcome` (no non-degenerate channel) | `decide.py:55-56`, `runner.py:159-160`: degenerate = returned None with no stdout/files/globals/argmut change; a both-sides `bind_error` is counted non-degenerate (D-06) | D | 143 |
| B8c | `tool_error` (internal failure, never blamed on program) | missing-record `decide.py:40,46`; harness error `runner.py:140` | C | 289, 310 |
| B9 | `changed_region_not_activated` / `budget_exhausted_s0` | `decide.py:57-59`; budget flag only set if the loop `break`s before an input (`runner.py:217-219,233`) | C (partial, see D-13) | 82-88, 137 |

### 1.3 Per-input outcomes and terminal classes (FS s3, SPEC 2.4, 3.2)

| ID | Requirement | Implementation | St | Test |
|---|---|---|---|---|
| O1 | Seven outcomes `CONFIRMED_DIFF` .. `NO_RUN` | `decide.py:6`; produced `runner.py:147,151,154,157,170,175,180` | C | 175-193, 343 |
| O2 | `returned`, `raised(type,msg)`, `crashed(signal)`, `limit(kind)` | `harness.py:122,125-126`; `runner.py:63-65,72-74` | C | 55-62, 119-134 |
| O3 | `SystemExit` is `raised(type,msg)` (SPEC 2.4 table); `exited(code)` is `os._exit` | `harness.py:123-124` records `SystemExit` as `exited`, so `SystemExit(3)` equals `os._exit(3)` | D | none |
| O4 | Limits never a witness; both-limit is `NO_RUN` | `runner.py:152-154` | C | 127-134 |
| O5 | `MemoryError` caused by the harness limit is `limit(oom)`, not `raised` | `harness.py:125` catches all `BaseException` as program outcome (D-08) | D | none |
| O6 | Unserialisable value is `NO_RUN(unobservable_outcome)`, never "equal" | canon failure inside the call `try` (`harness.py:122`) is reported as `raised` **[probe: cyclic list in both versions gave NDO S2]** | D | none |
| O7 | Introduced non-termination gives `INSUFFICIENT(resource_limit)` | `runner.py:154`, `decide.py:50` | C | 127-134 |

### 1.4 Observation boundary and comparator (FS s4, SPEC 2)

| ID | Requirement | Implementation | St | Test |
|---|---|---|---|---|
| C1 | `C_obs` default list ret, exc, stdout, file, argmut, global | `config.py:4,42`, `compare.py:51-73` | C | 55-62 |
| C2 | stderr, performance, line numbers, tracebacks, run ids excluded | stderr drained, never compared (`isolation.py:91-103`) | C | none |
| C3 | Uninstrumentable channels drop to intersection; empty gives `unobservable_outcome` | all channels assumed instrumented; `s2_all_channels_instrumented` is constant `True` (`decide.py:70`) | N | none |
| C4 | Equality on canonical typed form; user `__eq__`/`__repr__` never called | `harness.py:17-42` calls `hasattr(v,"__dict__")` (can run user `__getattr__`) | D (minor) | none |
| C5 | Type tag is identity (`1`/`1.0`, `list`/`tuple`) | `compare.py:14-15`, `harness.py:19-32` | C | 205-209 |
| C6 | Floats exact binary64, NaNs equal, `-0.0 != 0.0` | `compare.py:17-23`, `harness.py:22` | C | 206-207 |
| C7 | Declared tolerance: exact result also recorded, `tolerance_masked`, never pooled | tolerance applied in `compare.py:21-22`; no exact record, no `tolerance_masked`, no pooling guard | D | 218 (equality only) |
| C8 | Mappings key-order-insensitive; `ordered_mapping` option | `compare.py:33-38`, `config.py:43` | C | 208, 215-217 |
| C9 | Sets unordered; sequences ordered | `harness.py:31`, `compare.py:24-25` | C | 207 |
| C10 | Objects: class + digest of `__dict__`/`__slots__` to depth 3 | `harness.py:38-42`: `vars(v)` only; `__slots__`-only objects opaque; contents of dict/list subclasses never read. **[probe: `OrderedDict(a=1)` vs `OrderedDict(a=2)` gave NDO S2 (non-lossy); namedtuple `P(1)` vs `P(2)` gave NDO S1]** | D | 222 (flag only) |
| C11 | Exceptions: same qualified type, no subclass coalescing; message after N; `exc_message=ignore` alternative | `compare.py:61`, `harness.py:126`, `config.py:43` | C | 219-221 |
| C12 | Normaliser N strips addresses, ids, absolute paths, default reprs; declared and versioned | N strips `0x...` and cwd only (`harness.py:13-14`), applied to stdout and exception text, not returned strings; no `normaliser_id` (identity only via the harness.py hash, `runner.py:46`) | D | none |
| C13 | Message-only difference is `kind=exception_message` | single kind `exception` (`compare.py:61`) | D (minor) | 221 |
| C14 | `equal_lossy` blocks S2 (ret/side) | `harness.py:9,29,36,40`, `runner.py:157`, `decide.py:69` | C | 76-80, 222 |
| C15 | stdout is "bytes written by the call" | import-time prints share the same capture (`harness.py:90-93,112`) | D (minor) | none |

### 1.5 Witness schema, replay protocol, signatures (FS s5, SPEC 4, 8.1)

| ID | Requirement | Implementation | St | Test |
|---|---|---|---|---|
| W1 | Witness fields pair, scope, input_hash, harness_decl_id, kinds[], obs_old/new, replay_set[{run_id,version,observation,status}], locus, env, sandbox_policy_id | `records.py:59-62`, `runner.py:176-178` | C | 43-52 |
| W2 | `kinds` priority outcome > exception > side_effect > api | `compare.py:6,73` | C | 51, 62, 103 |
| W3 | Immutable, voidable only by `Supersession` | immutable by chain; no Supersession | N | none |
| W4 | Witness chain resolves to H, programs, input, environment, sandbox policy | `h_id`, `env_id`, `policy_id` are hashes with no record in the log; input args never persisted (`records.py:47-49`, `runner.py:55,77-79`); sources stored only as sha256 (`records.py:44`) (D-09) | D | 43-52 (checks runs/observations only) |
| W5 | Locus `unlocalised` valid | `records.py:62` | C | none |
| P1 | Step 1: both versions self-consistent over `r_det=3`, early stop, else QUARANTINED | `runner.py:127-135,150-151` | C | 113 |
| P2 | Step 2: `r_replay=5` fresh replays per side, 5/5 reproduce, versions still differ | `runner.py:162-170` (all replays executed, then counted; spec says first disagreement ends the protocol) | C (cost deviation) | 175-193 scripted; 43 real |
| P3 | Agreement on `C_obs`, not trace or locus | `_same` uses `compare` (`runner.py:85-89`) | C | 183-185 |
| P4 | Step 3: interpreter/tracer build mismatch makes replay `inconclusive` | absent (IMPL:29) | N | none |
| P5 | Step 4: control-sensitive candidate reproduced under `k_alt=3` alternate settings, own observation invariant | runs for every candidate (`runner.py:172`); alternate setting only `random.seed` + `time.time/time_ns` (`harness.py:83-87`); no hash seed, no `datetime`, uuid, urandom | D | 186-188 scripted only; no real-program test |
| P6 | Step 5: optional minimisation | absent | N | none |
| P7 | All replay processes charged to CPU budget | child rusage charged (`runner.py:58`); parent overhead not charged (D-13) | D | none |
| P8 | `crashed` is a witness only if reproduced in every replay | via normal replay path | C | 119-124 |
| G1s | Compatible signatures proceed (same arity/names, defaults added, declared rename) | `runner.py:113-115`; declared rename absent; requires equal parameter kinds | D (partial) | 109 |
| G2s | `api_break_probe`: bind failure before body, confirmed by replay, `kind=api` | `harness.py:112-120`, `compare.py:57` | C | 100-107 |
| G3s | Inputs "valid for one side" are bound against the other | inputs are user-supplied; a `bind_error` on **both** sides compares equal, is non-degenerate and counts as a valid SAME **[probe: module-level change, input with wrong arity on both sides gave NDO S2]** | D | none |
| G4s | Entry missing in one version: lift to outermost common frame | absent (IMPL:28) | N | none |
| G5s | Ungenerable inputs give `unsupported_signature`, never an invented default | no generator exists; JSON-only inputs (`config.py:77-92`) | C (vacuous) | 236 |

### 1.6 Sufficiency S0-S3 (FS s6, SPEC 6)

| ID | Requirement | Implementation | St | Test |
|---|---|---|---|---|
| S1a | Record stores factor vector F1-F4, stop reason, `r_det`, run-set Merkle root, `X_eff`, quarantined count, unhit units, `r_empty` | `runner.py:240-245`: floors dict (not F1-F4), `stop_reason` in {inputs_exhausted,budget,witness} (outside the SPEC enum), flat sha256 of sorted run ids (not Merkle) | D | 70-73 |
| S1b | Hit: a deterministic-confirmed input executed the unit in a version containing it; one-sided units | `runner.py:221-226` (only SAME inputs), per-side sets | C | 65-69 |
| S1c | Uninstrumentable units count as unhit; R never shrunk | R shrunk to executable lines (`runner.py:208-210`) **[probe: docstring-only change gave NDO S2, `r_empty`]** | D | none |
| S1d | `r_empty` flagged and reported as its own stratum | stored `runner.py:244`; not in `verdict.json` (`runner.py:250-253`); defined as "no executable changed line", wider than SPEC "empty after normalisation" | D | none |
| S1e | S1 floor: >=1 SAME input, valid on both versions, non-degenerate | `decide.py:52-56`; "valid on both" fails for both-bind-error (G3s) | D | 97, 143 |
| S1f | S1 floor: 100% changed units hit | `decide.py:57-59` | C | 82-88 |
| S1g | S1 floor: `r_det` done per contributing input; no quarantined input that may hit | conservative (B5) | D (conservative) | 113 |
| S1h | S1 floor: tier >= L0 (FS) / >= L1 (SPEC) with changed-region coverage bitmap | line-hit lists in run `meta` only; no tier, no bitmap record | D | none |
| S1i | S1 floor: no truncation; no blind spot; tamper flag clear | truncation C (`decide.py:48`); blind spot N; tamper never evaluated (`runner.py:233`) | D | none |
| S2a | Direction coverage of changed regions >= 0.80 of statically reachable directions, per version | `runner.py:228-231`: branch opcodes on changed lines (`BRANCH_OPS`, `runner.py:14`), all directions counted reachable (IMPL:33); vacuous (no branches) = 1.0 | C (approximation) | 65-70 (single-branch toy only) |
| S2b | Every contributing input deterministic-confirmed | any non-SAME input blocks (`decide.py:45-51`) | C | 113 |
| S2c | All declared channels instrumented | constant `True` (`decide.py:70`) | N | none |
| S2d | No `equal_lossy` on ret/side | `decide.py:69` (any channel's lossy flag, wider than spec) | C | 76-80 |
| S3 | `s3_enabled=false` default; plateau, L2, corroborating explorer | true is refused (`config.py:35-37,46`); nothing else implemented | C (disabled) / N (levels) | 226, 252-254; `records.py:71` rejects S3 (276) |
| S0 | S0 label for failed S1 floor, only inside INSUFFICIENT | `decide.py:71`, `runner.py:240` | C | 82-88 |

### 1.7 Evidence model, hash chain, modules (FS s8, s9; CONTRACTS D)

| ID | Requirement | Implementation | St | Test |
|---|---|---|---|---|
| E1 | `evidence_class` on every record; `status` qualifier | `records.py:27-41`; `status` used only by SufficiencyRecord (`records.py:66`); `inferred`, `proof`, `missing`, `invalid` never used | C (minimal) | 72 |
| E2 | Class per record kind (observation: runs/replays; derived: ChangedRegions, SourceMapping, witness difference; inferred: alignment, locus, ImpactSet; SufficiencyRecord derived+uncertain) | Run/Observation observation, Witness/Verdict/ProgramVersion/SufficiencyRecord derived; **no ChangedRegions, SourceMapping, ReplayCheck, Reproducibility, HarnessDeclaration, Input, ExplorationLog, InstrumentationCompleteness records** | D | none |
| E3 | DIVERGENT chain: Verdict, Witness, primary runs, repeats, replays + ReplayCheck, H, programs, input, environment, sandbox policy | Verdict -> Witness -> runs/observations/ProgramVersion only (`runner.py:178`, `records.py:59-62`) | D | 43-52 |
| E4 | NDO chain: SufficiencyRecord -> run-set root + per-input rows, reproducibility, completeness, ChangedRegions, ExplorationLog, H | SufficiencyRecord -> runs + versions (`runner.py:246`); no per-input rows | D | 65-73 |
| E5 | INSUFFICIENT chain: records that triggered each blocker | blocker `(code, detail)` strings inside SufficiencyRecord body (`runner.py:245`); no triggering-record refs | D | none |
| E6 | T4: recomputing s2 from the chain reproduces value and primary code | no recompute function (`records.trace` only walks refs, `records.py:107-117`) | N | none |
| E7 | T6: no label-namespace record reachable | no label records exist | U | none |
| E8 | Stored by default: replay recipe + hashed event stream (~300 B/run); full events for witnesses, 5% audit, escalations | per-run slot id, status, summary, hit lines (`runner.py:76-80`); no recipe, no event stream, no input args | N | none |
| E9 | Hash chain over the store; tamper detection | linear JSONL chain `records.py:82-104`; verifies seq/prev/hash only; does not recheck `id == content_id`; tail truncation undetected; no external anchor | D | 258-268 (middle-record edit only) |
| E10 | Chain hash excludes run id and repeat index (CONTRACTS s4, EV-13) | refers to a per-run event-stream `chain_root`, which does not exist; the log chain includes ids and timings (`meta` is hashed into the chain: `records.py:89`) | N / A-10 | none |
| E11 | `verify_chain(verdict_id)`, `replay(recipe)` (module D) | `read_log` and `trace` only (`records.py:96-117`) | D | 258-268 |
| M1 | Core modules A, B, C, D, G, H, I, K, L | A, G, K, L absent; B = `harness.py`+`isolation.py`; C = imported V6 `changed_lines` (`runner.py:7`); H = `process_input`; I = `decide.py` | N (A,G,K,L) | none |
| M2 | Module I is the sole `Verdict` writer | `Verdict` built only in `runner.py:248` from `decide()` | C | 271 |
| M3 | Dependencies acyclic | import graph acyclic | C | none |

### 1.8 Isolation I1-I7 (FS s10, D10)

| ID | Requirement | Implementation | St | Test |
|---|---|---|---|---|
| I1 | Fresh child per run, CPython 3.13, `-I`, scrubbed env, private cwd | `isolation.py:86-89` (`-I -B`, env of 4 keys, tmp cwd); no 3.13 check (`sys.executable`); no `PYTHONHASHSEED`/`TZ`/`LC_ALL`/thread pinning that CONTRACTS B requires | D (partial) | iso:23 |
| I2 | `setrlimit` CPU/FSIZE/NPROC/NOFILE/CORE=0 + parent RSS watchdog | CPU, NOFILE, FSIZE, CORE applied (`isolation.py:79-84`); `rlimit_as` UNAVAILABLE and `rlimit_nproc` "not applied" (`isolation.py:243`, caps probe); watchdog polls every 0.1 s (`isolation.py:116-120`); unverified properties do not fail the run (B3a) | D | iso:37, 85, 96 (skipped here), 101 |
| I3 | Process-group kill | `start_new_session` + `killpg` + ESRCH verification (`isolation.py:88-89,123,56-69`); `setsid` escapes uncovered (documented) | C (limit documented) | iso:32, 42, 111 |
| I4 | Tracing outside user-code reach with tamper detection | `sys.monitoring` runs in the same process as untrusted code (`harness.py:54-82`); the result channel is a stdout line (`harness.py:74`, `runner.py:62`) that user code can forge by writing to fd 1 and `os._exit` **[probe: forged result accepted, NDO S2 for a variant that never returns]**; tamper flag computed (`harness.py:72`) but discarded (`runner.py:233`) | D | none |
| I5 | Network denial (macOS `sandbox-exec`; Linux `--network none`) | macOS profile `sandbox_darwin.sb:2`, capability probe `isolation.py:246-252`; Linux path absent (fails closed: every run `SANDBOX_UNAVAILABLE`, `isolation.py:77-78`) | C (macOS) / N (Linux) | iso:61, 106 |
| I6 | Write confinement to private tmp | `sandbox_darwin.sb:3-7`; profile is `(allow default)` so reads of the whole filesystem remain possible | C (writes) | iso:73 |
| I7 | Exact failure classification (`killed_wall`, `killed_mem`, `crashed`, `exited`, `base_exception`, `policy_violation`, `oom`, `truncated`...) | `isolation.py:136-151` uses heuristics including a stderr substring `"MemoryError" in se` (`isolation.py:144`) and a CPU-time guess for SIGKILL (`:142`); no `policy_violation`, no `base_exception`, no `oom`; sandbox denials surface as program `PermissionError` and can become witnesses | D | iso:37, 85, 101 |
| I8 | macOS runs flagged `policy_below_minimum` | `runner.py:244,252` (only SufficiencyRecord and `verdict.json`, not Run/Witness/Verdict records, contrary to README line 147-area wording "every record") | C (partial) | 72 (accepts True or False) |
| I9 | Legacy runner/tracer is `v6_compat`, its runs invalid evidence | no tagging mechanism | U | none |
| I10 | Hostile fixtures: zero escapes, no stray processes | no fixture for result forgery, `sys.monitoring` tamper, `setsid`, subprocess output; `iso:111` is environment-dependent | U | iso:42, 55, 111 |

### 1.9 Config fields and defaults (FS s11)

Strict validation (`config.py:53-66`) rejects every key not in `SCHEMA`; **[probe: a config containing `harness.normaliser_id`, `stderr`, `capture_tier` exits 2 with `unknown key(s)`]**.

| ID | Field (FS default) | Code (`config.py`) | St | Test |
|---|---|---|---|---|
| F1 | `harness.c_obs` (6 channels) | `:42` same default | C | 227 |
| F2 | `harness.normaliser_id` | absent | N | none |
| F3 | `float_tol={rel:0,abs:0}` | `:42` | C | 218 |
| F4 | `ordered_mapping=false` | `:43` | C | 217 |
| F5 | `exc_message=exact_normalised` | `:43` | C | 220, 227 |
| F6 | `stderr=excluded` | absent (behaviour implicit) | N | none |
| F7 | `capture_tier=L0(+bitmap)` | absent | N | none |
| F8 | `api_break_probe=true` | `:44` | C | 100-107 |
| F9 | `repeat.r_det=3, r_replay=5, k_alt=3` | `:45` (minimum bounds 1/1/0 allow weaker protocols) | C | 227 |
| F10 | `suff.s2_branch_floor=0.80` | `:46` | C | 228 |
| F11 | `suff.s3_plateau_window`, `static_match_f1_trigger`, `witness_outside_R_diag` | absent | N | none |
| F12 | `suff.s3_enabled=false` | `:46`, `true` refused `:35-37` | C | 227, 252-254 |
| F13 | `budget.unit=cpu_seconds`, `grid=[10,60,300]`, `headline=60` | single `budget.cpu_seconds=60` (`:47`); no grid | D | 228 |
| F14 | `per_run.claims_cpu_s=10`, `fast_cpu_s=2` | single `cpu_s=10` (`:48`); no fast tier | D | none |
| F15 | `per_run.wall_s=20`, `rss_mib=2048` | `:48-49` | C | none |
| F16 | `per_run.max_events_L1=200000` | absent | N | none |
| F17 | `seeds`, `stats`, `platform` blocks | absent | N | none |
| F18 | Verdict identity includes all of H (SPEC 2.5: repeat counts, floors, sandbox policy id, control profile, capture tier) | `h_id` hashes only `cfg["harness"]` + `harness.py` source (`runner.py:46`); `pair_id` omits `repeat`, `suff`, `budget` (`runner.py:51`) | D | 258-261 |

### 1.10 Gates, CLI, determinism

| ID | Requirement | Implementation | St | Test |
|---|---|---|---|---|
| X1 | Gates G0-G8, K1-K5 | evaluation-side (`experiments/v7b/k1_spike.py`, `scripts/analyze_results.py`), not in `sbgv7/`; K1 reported NOT MET in `research/evaluation/K1_K2_FEASIBILITY_REPORT.md:29` | U | analysis only (`test_analysis.py`) |
| X2 | CLI exit codes (FS silent; IMPL:5): 0 verdict, 2 usage/config/inputs, 3 identical | `__main__.py:23,25,27`; every verdict value, including INSUFFICIENT, exits 0; internal errors give an uncaught traceback (exit 1); `--out` being a file gives a traceback | D (spec gap A-11) | 242-254 (0, 2); exit 3 and `--help` of `sbgv7` itself none |
| X3 | Determinism: same inputs and config give the same ids | run, witness, pair, verdict ids stable | C | 258-261 |
| X4 | Determinism of artefacts | `evidence.jsonl` embeds timings in hashed `meta` (`records.py:35,89`, `runner.py:79`) and `verdict.json` includes `cpu_seconds_spent` (`runner.py:253`), so chain hashes and files differ per invocation | D (minor) | none |
| X5 | Seeds: `exploration_seed` pre-declared; `bootstrap_seed=42` | no explorer; none | N | none |
| X6 | Determinism controls for primary runs: hash seed, seeded RNG, virtual clock, single thread (SPEC 5.1) | none applied to primary runs; `-I` leaves string-hash randomisation on | N | none |

Status counts are in section 6.

---

## 2. Deviations and spec problems

### 2A. Deviations between code and spec

Severity: Blocking = invalidates a core claim or a hard gate; Major = a normative floor or invariant is unmet and can mislead a verdict; Moderate = deviation with limited or conservative effect; Minor = cosmetic or cost.

| ID | Severity | Deviation (evidence) | Change |
|---|---|---|---|
| D-01 | **Blocking** | Canonicalisation drops the contents of dict/list subclasses and `__slots__` objects (`harness.py:26-42`). `OrderedDict(a=1)` vs `OrderedDict(a=2)` return **NDO S2** (non-lossy) and namedtuple `P(1)` vs `P(2)` **NDO S1** **[probe]**. The `ret` channel is the central observation; the frozen claim "no observable difference was found" is false for these types. | CODE: canonicalise by exact-type container recursion (subclass of dict/list/tuple/set read by iteration), include slots, and set `lossy` whenever contents were not read. SPEC: add one sentence defining subclass/opaque-type canonicalisation (A-15). |
| D-02 | **Blocking** (for any third-party code and for the hard G1 isolation gate; Major for synthetic-only use) | Untrusted code shares a process with the tracer and result channel (`harness.py:54-82`, `runner.py:62`); a program can write a forged `SBGV7RESULT:` line to fd 1 and `os._exit(0)`. **[probe: variant whose real behaviour is "exit 0 without returning" yielded NDO S2.]** The tamper flag is computed (`harness.py:72`) but `Evidence(tampered=False)` (`runner.py:233`) discards it, so S1 floor "tamper flag clear" and `unsafe_program` are dead. IMPL:30 and the red-team review describe tamper as implemented. | CODE: pass `any(run.tampered)` into `Evidence`; move the result channel to a private fd/file or authenticate it with a per-run nonce; add hostile fixtures. SPEC: none. Fix IMPL:28,30 and `INDEPENDENT_RED_TEAM_REVIEW.md:61` (section 4). |
| D-03 | Major | Unverified isolation properties do not produce `sandbox_failure` (FS s10): absent `RLIMIT_AS`/`NPROC` are skipped (`isolation.py:79-84`; caps probe `:243`) and `runner.py:60` only checks network denial, cleanup, orphans, limit-apply failure. A 3 GiB allocation under `rss_mib=2048` ran to NDO S2 **[probe]**. | See A-01: SPEC must first say which properties are required versus flagged on macOS; then CODE maps a missing required property to `sandbox_failure`. |
| D-04 | Moderate | `NO_RUN` of any cause (sandbox, import error in call run, harness error, both-side limit) is mapped to `resource_limit` (`decide.py:50`); any quarantined input blocks even if it hit nothing (`decide.py:49`). SPEC 3.2 says NO_RUN "contributes no comparison evidence", the B table has no NO_RUN row, and B5 requires "hit or may have hit". `test_core.py:343` (red-team B-1) encodes the conservative reading. | SPEC: adopt the conservative rule explicitly (new row B6b "any `NO_RUN` input on which a changed unit may have been missed blocks"), and name the code by cause (sandbox, import, tool). CODE: report the true cause code instead of `resource_limit`. |
| D-05 | Major | Changed region R is shrunk to executable lines (`runner.py:208-210`); SPEC 6.2 "R is never shrunk". **[probe: changing a function docstring that is returned only on `x != 0`, input `x=0`, gave NDO S2 with `r_empty`.]** Non-executable semantic changes (docstrings, decorators evaluated elsewhere, `__doc__`/`inspect` readers, annotations, string constants split over lines) are invisible. | SPEC: define "changed unit" (A-03). CODE: any changed non-comment non-blank line with no executable instruction becomes `unmodelled_change`; keep `r_empty` only for comment/whitespace-only diffs. |
| D-06 | Major | `bind_error` on both sides compares equal (`compare.py:56-58` falls through), is non-degenerate (`runner.py:159-160`) and counts as the contributing SAME input. **[probe]** A module-level change plus an arity-wrong input reached NDO S2 without executing any function body. S1 requires an input "valid for both versions". | CODE: classify both-bind-error as `NO_RUN(invalid_input)` and exclude it from `X_eff`. |
| D-07 | Moderate | Canonicalisation errors inside `canon(fn(...))` are reported as `raised` (`harness.py:122,125`). **[probe: cyclic list in both versions gave NDO S2.]** | CODE: move `canon` outside the program `try`; on failure emit `NO_RUN(unobservable_outcome)`. |
| D-08 | Moderate | All `BaseException`, including `MemoryError` from the harness limit and `PermissionError` from sandbox denial, become program outcomes (`harness.py:125-126`); `unsafe_program` / `policy_violation` / `oom` classes are not produced (I7). Under an effective `RLIMIT_AS` (Linux) a limit-induced `MemoryError` could become a witness. | CODE: raise a distinct harness status for `MemoryError` under limit and for denied syscalls. SPEC: say how policy denials are detected (A-01). |
| D-09 | Major | Evidence log cannot reproduce or re-verify a verdict: no `HarnessDeclaration`, `Input`, `Environment`, `SandboxPolicy`, `ChangedRegions`, `ReplayCheck` records; input args and source bytes are not stored (only hashes) (`records.py:44,47-49`; `runner.py:55,77-79`). SPEC 2.5 "a verdict that does not reference a declaration is invalid evidence" is violated by construction. IMPL:24-31 admits part of this. | CODE: store those records (or store inputs and sources in the log) and reference them from Witness and SufficiencyRecord; add a recompute function (T4). |
| D-10 | Moderate | Verdict identity omits repeat counts, floors, budget, sandbox policy: `pair_id` hashes versions, entry, `cfg["harness"]` (`runner.py:46,51`). Two runs with `r_det=1` and `r_det=3` share a `pair_id`. SPEC 1.1/2.5 put these in H. | CODE: hash the whole validated config; or SPEC: restrict H to the harness section and add a separate "decision policy id". |
| D-11 | Moderate | Config schema differs from FS s11 in names and coverage (F2, F6, F7, F11, F13, F14, F16, F17) and unknown keys are fatal, so a spec-shaped config cannot be loaded **[probe]**. | CODE: accept FS field names (`claims_cpu_s`), reject only genuinely unsupported values (like `s3_enabled=true`); SPEC: mark which fields are "reserved, not built". |
| D-12 | Moderate | `compare_versions` creates the output dir and log before the identity check (`runner.py:186-189`); an identical pair exits 3 but leaves a 2-record `evidence.jsonl`, and the next run exits 2 "refusing to overwrite" **[probe]**. Identity check covers source only (deps/runtime never hashed). The API overwrites an existing log silently (`records.py:85`) while the CLI refuses (`__main__.py:19`). | CODE: check identity before creating files; one overwrite policy in the library. |
| D-13 | Moderate | Budget: parent time (hashing, `ps` polling, JSON) is not charged although SPEC D7 says "all processes incl. overhead" (`runner.py:58`); the check is per input (`runner.py:217`), so one input (up to ~22 child runs) can overshoot arbitrarily; `budget_exhausted_s0` is chosen only if the loop was cut short (`runner.py:233`), not if the last input exhausted it. | CODE: charge parent CPU; check the budget between runs; SPEC: define the stop granularity and when `budget_exhausted_s0` vs `changed_region_not_activated` applies (A-17). |
| D-14 | Moderate | Control profile: primary runs have no hash seed, TZ, LC_ALL or thread pinning (`isolation.py:87`); `-I` keeps string-hash randomisation, so legitimate set-of-str programs quarantine. Alternate settings cover only `random.seed` and `time.time*` (`harness.py:83-87`; `datetime.now`, `uuid`, `os.urandom`, `monotonic` unaffected), and alt runs execute for every candidate, not only control-consulting ones. | SPEC: add the determinism control profile to FS s11 (A-09). CODE: apply it. |
| D-15 | Minor | `SystemExit` is recorded as `exited` (`harness.py:123-124`), SPEC 2.4 classifies it `raised`. | SPEC: pick one (the FS only lists the classes). |
| D-16 | Moderate | S2 "all declared channels instrumented" is the constant `True` (`decide.py:70`); S1/S2 "blind spot" and "tier/bitmap" absent. S2 can be emitted while a channel is blind (for example a program writing via `os.write(1)` or a subprocess, IMPL:30). | CODE: detect fd-1 writes and subprocess/exec use via `sys.monitoring` events or audit hooks and set a blind-spot flag; until then cap at S1. |
| D-17 | Minor | Tolerance semantics (C7) missing; default tol 0 so no effect by default. | CODE. |
| D-18 | Minor | Invariants use `assert` (`records.py:36,70-73`) and vanish under `python -O`; unknown code raises instead of downgrading (V13). | CODE: explicit `raise`. |
| D-19 | Minor | Normaliser N narrower than SPEC 2.4 (absolute paths other than the workdir, object reprs in returned strings); exception messages that include the source path differ between base and variant files (`harness.py:13-14,95`). Import-time stdout is part of call stdout (C15). | CODE. |
| D-20 | Minor | Replays run to completion instead of stopping at the first disagreement (`runner.py:163`); secondary codes are listed alphabetically in the verdict (`records.py:75`) although `decide()` returns them by rank. | CODE (cost); SPEC (state ordering). |
| D-21 | Moderate | Chain verification is weak: tail truncation (dropping the Verdict and last records) passes `read_log`; `id` is not re-derived from content (`records.py:96-104`); unkeyed, no anchor. | CODE: store the head hash in `verdict.json` and verify ids. |
| D-22 | Minor | `stop_reason` value `inputs_exhausted` is outside the SPEC enum (`runner.py:242`); `r_empty` not exposed in `verdict.json`. | CODE or SPEC (add `inputs_exhausted`). |
| D-23 | Minor | Static layer is V6 code (`from sbgv6.features import changed_lines`, `runner.py:7`), whose normalisation rules are not part of the spec. | SPEC: cite the rule; CODE: vendor it into V7. |

### 2B. Spec ambiguities and internal inconsistencies

| ID | Severity | Problem | Resolution (change SPEC unless noted) |
|---|---|---|---|
| A-01 | Major | FS s10 says "an unverified property gives `sandbox_failure`" but also says macOS runs are allowed, flagged `policy_below_minimum`. On macOS `rlimit_as` and `rlimit_nproc` are structurally unverifiable, so the first rule would make every macOS run `INSUFFICIENT(sandbox_failure)`. | SPEC: enumerate required properties (network, write confinement, process-group kill, CPU/FSIZE/NOFILE limits) versus advisory ones (AS, NPROC) with their flag. |
| A-02 | Moderate | NO_RUN semantics (SPEC 3.2 vs 3.3): contributes no evidence, yet B table has no row for it; B6 names only `LIMIT_ASYMMETRIC`. | SPEC: add the explicit rule (D-04). |
| A-03 | Major | "Changed unit" granularity undefined (SPEC 6.2 says "basic blocks plus pseudo-units"; FS says "units"). "R is never shrunk" conflicts with comment/whitespace `r_empty` handling. | SPEC: define unit = executable line (or basic block) and treat non-executable semantic changes as `unmodelled_change`. |
| A-04 | Minor | "may have hit" (B5) has no operational definition for a quarantined input. | SPEC: define as union of hit lines over its repeats, or "always may have hit". |
| A-05 | Moderate | FS s6 S1 "tier >= L0 with bitmap" and s11 `capture_tier=L0(+bitmap)` vs SPEC 6.3 "Tier at least L1 including the changed-region coverage bitmap". | SPEC: pick L0+bitmap or L1 and fix the other document. |
| A-06 | Minor | Entry missing: FS B1 "entry resolution fails" gives `import_error`, FS s5 gives `unsupported_signature(detail=entry_missing)`. Code follows s5. | SPEC: state s5 wins. |
| A-07 | Minor | FS B8 omits `import_error` that SPEC B8 lists; no tie-break defined inside a rank (B2 has four codes, B4 two). Code: alphabetical. | SPEC: add tie-break order. |
| A-08 | Minor | `exited(code)` vs `raised(SystemExit)` boundary (D-15). | SPEC. |
| A-09 | Moderate | Control profile (hash seed, virtual clock, threads) is required by SPEC 5.1 and CONTRACTS B but absent from FS s11; SPEC 4.4 triggers `k_alt` only when a virtualised source was consulted, which cannot be known if primary runs are not virtualised. | SPEC: add profile fields; define trigger. |
| A-10 | Moderate | "Hash chain" names two objects: per-run event-stream `chain_root` (excludes run id and repeat index, EV-13) and the store-level chain. FS never defines the store chain that the code implements. | SPEC: define both. |
| A-11 | Moderate | FS defines no CLI contract; exit codes exist only in IMPL:5 and README. INSUFFICIENT and DIVERGENT both exit 0, so scripts cannot branch without parsing JSON. | SPEC: add a CLI section (suggest 0 verdict written, 2 usage/config, 3 ineligible, 4 tool_error). |
| A-12 | Minor | FS s2 row 3 lists `S3` and "highest level whose floors hold" while S3 is disabled and its corroboration clause is flagged INVENTED/UNVALIDATED only in SPEC. Whether an unimplemented `s3_enabled=true` must be refused is unspecified (code refuses). | SPEC: state refusal. |
| A-13 | Minor | `r_det=3` counts the primary run or not? Code: 3 runs per side in total. | SPEC. |
| A-14 | Moderate | Whether a sandbox violation on a replay or alt run voids an otherwise confirmed witness: "only invalid evidence voids" (FS s2) does not list it, B3 ranks below DIVERGENT. Code ignores replay-run sandbox status when emitting the witness (`runner.py:164-180`, `decide.py:77`). | SPEC: state that a witness requires sandbox-verified runs. |
| A-15 | Major | Container subclasses and opaque C types have no canonical rule (SPEC 2.2 lists `list` vs `deque` as different but not `OrderedDict`, `Counter`, `defaultdict`, namedtuple). Source of D-01. | SPEC. |
| A-16 | Moderate | Vacuous branch coverage (no branch in R) satisfies the 0.80 floor; code gives 1.0 (`runner.py:231`), so a one-line straight-line change reaches S2. SPEC silent. | SPEC: define vacuous coverage as S1-only. |
| A-17 | Minor | Budget stop granularity and `budget_exhausted_s0` selection (D-13). | SPEC. |
| A-18 | Minor | FS s3 says a "crashed" terminal requires reproduction "in every replay", while `QUARANTINED` is decided before replay; interaction for a crash that is intermittent in repeats is unstated. | SPEC. |

---

## 3. Untested normative behaviours

No test asserts any of the following (from the matrix, "none"):

1. CLI exit 3 for identical sources; `python -m sbgv7 --help`; exit paths for tool errors (X2). `test_cli_help_safe.py` covers only `k1_spike` and `baselines`.
2. Verdict-level `sandbox_failure` (B3a) and `unsafe_program`; tamper flag handling (`decide.py:42` branch never reached).
3. `capture_truncated` end to end (B7a); `alignment_failed` (B2a).
4. `env_sensitive`, `flaky_witness` and the control-alternation protocol with a real program (only scripted `Fake` runs, `test_core.py:154-193`).
5. Replay count semantics with real programs for defaults r_det=3, r_replay=5, k_alt=3: tests use `FAST` (2/2/1, `test_core.py:14`) except 113.
6. Float tolerance edge cases (`abs`-only, masked-vs-exact), tuple/frozenset/bytes/complex canonical forms, `-0.0` through the harness, subclass and slots objects (D-01), depth cut-off other than the one `lossy` example.
7. Lossy truncation at `MAXN=5000` and stdout cap 32768 (`harness.py:8`).
8. Config: defaults equal FS defaults (no test loads an empty config and asserts each value).
9. Hash chain: tail truncation, reordering, id/content mismatch; `trace` dangling-ref error.
10. `ineligible` for whitespace-only or comment-only change (the `r_empty` path), and the S0 degenerate record for run-less INSUFFICIENT.
11. S2 coverage arithmetic with more than one branch, loops (`FOR_ITER`), deleted/inserted one-sided units, per-version floors.
12. `policy_below_minimum` is asserted only as "True or False" (`test_core.py:72`).
13. Hostile programs: forged result line, `sys.monitoring` tamper, `os.write(1)`, `setsid`, subprocess, fork bombs, large allocation under an active RLIMIT_AS.
14. Budget accounting (parent overhead) and per-input overshoot.
15. Whole `test_core.py` is skipped when `network_denial != ACTIVE` (`test_core.py:13`), i.e. silently on any Linux CI.

---

## 4. Documents that contradict the frozen spec or the code

Searched `reports/`, `docs/`, `research/`, README and STATUS for `EQUIVALENT`, S3, internal-only, K1-K5, `GO_P1`, effort numbers. Legacy V5/V6/V4 documents use "equivalent" as a ground-truth label class (not a V7 verdict) and are excluded unless they bear on V7.

### 4.1 Contradict the frozen spec (superseded drafts without a banner)

The 13 files `reports/v7_design/SBG_V7_*.md` are byte-identical to `reports/v7_design/_original_archive/*` and carry no "superseded" banner (a banner count of 0 for 11 of 13; the other two only mention R1 in passing). They still state positions the FS retired:

| File:line | Contradiction |
|---|---|
| `SBG_V7_ARCHITECTURE_MASTER_PLAN.md:12` | four-valued verdict set including `DIVERGENT_INTERNAL_ONLY` (FS s2: exactly three) |
| `SBG_V7_IMPLEMENTATION_ROADMAP.md:43,174,186` | `DIVERGENT_INTERNAL_ONLY` as a class with a false-alarm criterion at G3 |
| `SBG_V7_IMPLEMENTATION_ROADMAP.md:9,64` | effort 51 engineer-weeks, 32 calendar weeks (22-48), 3 engineers; R1 (`reconciled/SBG_V7_IMPLEMENTATION_ROADMAP.R1.md:59`) says these omit work and contain a summing error (range 32-87) and re-estimates nothing |
| `SBG_V7_IMPLEMENTATION_ROADMAP.md:79` | K2 = activation census on a >=150-pair dev pool at "week ~6" (FS K2: determinism >=70% and replay+crude activation >=35% on K1 pairs under D10 isolation); `G0-G9` numbering (FS: G0-G8) |
| `SBG_V7_RISK_REGISTER.md:3,11,15,64-65` | `G0-G9`; K1 "< 60 runnable pairs" (FS: <100 over >=8 projects); K2 "< 50%"/"20-35%" thresholds; STOP conditions S1/S2 differ from FS s12 |
| `SBG_V7_FINAL_ARCHITECTURE_DECISION.md:19,33-34` | "~150 divergent real pairs"; "stop entirely if K1 or K5 fail" (FS K5: no confirmatory evaluation, not STOP); "Conditional GO for P0/P1" (FS: `GO_P1` scoped) |
| `SBG_V7_FAILURE_TO_REQUIREMENT_MATRIX.md:69,73` | R-19 demands an "EQUIVALENT-within-budget" class; R-23 labels preserving pairs EQUIVALENT (FS s2 prohibits) |
| `SBG_V7_MODULE_CONTRACTS.md:292` | `internal_only_difference` reason code (FS s7 retired) |
| `SBG_V7_DATA_AND_EVIDENCE_SCHEMA.md:300` | reason code list including `internal_only_d...` and observed-same codes (FS retired) |
| `SBG_V7_EXPERIMENTAL_PROTOCOL.md:21,42` | `INTERNAL_ONLY` truth class and H8 as confirmatory (D2: not confirmatory) |
| `SBG_V7_VALIDATION_AND_ACCEPTANCE_GATES.md:3,23,29` | DIVERGENT / NO_DIVERGENCE definitions pre-D1; row 3 "Equivalent refactoring"; row 9 internal-masked class |

Resolution: add a one-line banner to the 13 originals ("superseded by `reconciled/*.R1.md` and `reports/final/V7B_FROZEN_SPEC.md`") or delete the duplicates, keeping `_original_archive`.

### 4.2 Stale relative to the code or to the repository

| File:line | Claim | Reality |
|---|---|---|
| `reports/final/P0_FINAL_RECONCILIATION_REPORT.md:7` (and O13 at `:61`); `V7B_FROZEN_SPEC.md:137` | "no V7 code exists"; reconciled SCHEMA/ROADMAP/MASTER/FINAL R1 documents "do not exist" | code exists (HEAD `1206312e`); nine R1 files and `CHANGELOG_all_R1.md` now exist in `reports/v7_design/reconciled/` but are **untracked** (`git status`); only EP, MATH, GATES, RESEARCH R1 are tracked |
| `reconciled/SBG_V7_EXPERIMENTAL_PROTOCOL.R1.md:5`, `SBG_V7_MATHEMATICAL_SPECIFICATION.R1.md:5` | "No V7 code exists" / "no code" | stale |
| `docs/architecture/V7B_IMPLEMENTATION.md:28` | `unsafe_program` produced "except trace-tamper flag" | never produced (`runner.py:233`) |
| `docs/architecture/V7B_IMPLEMENTATION.md:30` | "Tamper detection is a post-run check of monitoring state" | computed, then discarded (`runner.py:233`) |
| `reports/final/INDEPENDENT_RED_TEAM_REVIEW.md:61` | same "except trace tamper" | same |
| `reports/final/FINAL_CLAIMS_AND_EVIDENCE_MATRIX.md:5` | "NO_DIVERGENCE_OBSERVED is blocked by incomplete evidence: Implemented and verified" | false for D-01, D-05, D-06, D-07 (section 2A) |
| `README.md:193-194` | `tests/v7` "76 collected; 4 files"; "85 passed" | 5 files (`test_cli_help_safe.py` added), 92 tests (91 passed, 1 skipped) |
| `README.md:27` | `sbgv7/` "about 1,100 lines" | 1,080 (core) + 306 (`baselines/`) = 1,386 |
| `README.md` (section 11) and IMPL:13 | "every record carried `policy_below_minimum`" | only the SufficiencyRecord and `verdict.json` (`runner.py:244,252`) |
| `research/evaluation/EXPLORATORY_RESULTS.md:47` | "at >= S3 (never emitted) coverage 0.291 risk 0" | S3 is never emitted, so a non-zero coverage at S3 is internally inconsistent |
| `docs/architecture/V7B_IMPLEMENTATION.md:7-10` | module list | omits `_child.py`, `sandbox_darwin.sb`, `baselines/` |

### 4.3 Terminology conflict (minor)

`research/evaluation/K1_K2_FEASIBILITY_REPORT.md:16,17,53,65-66` and `EXPLORATORY_RESULTS.md:15` use "EQUIVALENT" for generator labels (truth class). FS s2 forbids the word "as outcomes anywhere"; R1 restricts it to the truth class `Eq-B`. Rename to `Eq-B` or "generator label: preserving".

### 4.4 Consistent (checked, no contradiction found)

`FINAL_RESEARCH_READINESS_REPORT.md:15-17,30` (S3/explorer/E not implemented, K1 unmet, RLIMIT_AS/NPROC not enforced); `reports/final/V7B_FROZEN_SPEC.md:133` vs `P0_FINAL_RECONCILIATION_REPORT.md:82` (`GO_P1`, scoped); K1-K5 text in `reconciled/SBG_V7_IMPLEMENTATION_ROADMAP.R1.md:28-35`, GATES R1 rows 59-63 and `SBG_V7_FINAL_ARCHITECTURE_DECISION.R1.md:47,54` agree with FS s12. FS s13 "GO_P1" says P1 work is authorised; Phase 1 closure (`PHASE_1_FINAL_CLOSURE_REPORT.md`) is consistent with that scope.

---

## 5. Repository hygiene

| Item | Finding |
|---|---|
| Size | 23,032 tracked files; `results/` 182 MB on disk and 6,551 tracked files (`results/raw/k1_spike` 2,255, `baselines` 2,104, `k1_spike_postfix` 2,070); `benchmark/` 92 MB, `artifacts/` 56 MB, `paper/` 17 MB. Largest tracked blobs: `artifacts/v6/final/predictions_final.csv` 5.7 MB, `artifacts/v6/predictions_dev.csv` 4.7 MB, `SBG_PRE_V6_FILE_INVENTORY.csv` 2.9 MB, two `results/raw/baselines/.../B3/evidence.jsonl` 2.1 MB each. Pack size 48.6 MiB (`PHASE_1_FINAL_CLOSURE_REPORT.md`). No file over 6 MB in the tree; raw per-run evidence is committed rather than archived. |
| Stale or generated files in tree | `results/raw/{baselines,k1_spike,k1_spike_postfix}` are regenerable outputs from `experiments/v7b/k1_spike.py` and `sbgv7.baselines.run`; two result sets (`k1_spike` and `k1_spike_postfix`) coexist, and the Phase 1 incident overwrote 209 tracked files (`PHASE_1_FINAL_CLOSURE_REPORT.md` s4). `*.npz`, PDFs, PNGs tracked under `artifacts/` and `results/figures/`. |
| Files from earlier phases | root `phase5/`, `phase6/`, `phase7/` (228 KB), `FINAL_STANFORD_READINESS_REPORT.md`, `SBG_PRE_V6_*` inventory and manifest, `TEST_LOCK.json`, `STATUS.md` and `docs/CLAIMS_REGISTRY.yaml` (V5/V6 content; README says the old README is `docs/README_pre_v7b.md`), `docs/SBG_BOB_*` handoffs, `reports/{recovery_programme,remediation,sprint2,v6_*}`, 13 duplicated originals in `reports/v7_design/` (identical to `_original_archive`). 9 reconciled R1 files plus `CHANGELOG_all_R1.md` untracked. |
| `.gitignore` | ignores `__pycache__`, `.venv*`, `*.log`, `results/repro/`, `*.pkl`, `*.bin`; does **not** cover `results/raw/**` (large regenerable outputs), `*.npz`, `.DS_Store` is covered; no entry for scratch output dirs written by `--out`. `git ls-files` contains no `.pyc` or `.DS_Store`. |
| Flaky or environment-dependent tests | `iso:111 test_no_stray_processes` inspects the global process table (fails if any other V7 run is active; README admits it); wall/CPU-time tests with 1 s limits and `wall_s < 5/6` assertions (`test_core.py:127-134`, `iso:32,85`, `isolation.py:238`) are load-sensitive; `test_core.py:13` runs `capabilities()` (spawns a 1 s spin probe) at collection time and skips the entire module without `sandbox-exec`, so Linux CI passes with zero core tests. README records an earlier `killpg` `PermissionError` flake (guarded, "not a proof"). This run: no flake, 21.9 s. |
| Scripts without `--help` | By static check (no `argparse`/manual help): `scripts/build_dev_pairs_csv.py`, `scripts/check_docs_v7b.py`, `scripts/generate_figures.py`, `scripts/generate_v5_pairs.py`, `scripts/run_evaluation.sh`, and `python -m sbgv7.isolation` (any argument runs the capability probes). `k1_spike.py` and `sbgv7/baselines/run.py` have a manual `--help` (sys.argv scan, tested by `test_cli_help_safe.py`) but still default their output paths to the committed `results/` tree (closure report limitation 5). `scripts/analyze_results.py` and `power_actual.py` use argparse. Per the Phase 1 incident, any of the five unguarded scripts may run a full workload on `--help`; I did not execute them. |
| Test counts | `tests/v7`: 5 files, 92 tests (91 passed, 1 skipped); `test_analysis.py` and `test_baselines.py` do not test `sbgv7/*.py` engine behaviour. |

---

## 6. Counts

Matrix rows by status (135 rows in section 1, counted by script from the status column, first letter; the four split rows B0r, S3, E10, I5 are counted under their first status):

| Status | Rows |
|---|---|
| Conforms (C, including partial/conservative/macOS-only) | 63 |
| Deviates (D) | 45 |
| Not implemented (N) | 23 |
| Unverifiable (U) | 4 |

Deviation register: 23 code deviations (D-01..D-23: 2 Blocking, 4 Major, 10 Moderate, 7 Minor) and 18 spec problems (A-01..A-18: 3 Major, 7 Moderate, 8 Minor).

Not checked: Linux behaviour; any third-party repository; `experiments/` and `scripts/` beyond static `--help` detection; the 40-odd legacy V5/V6 documents beyond keyword search; whether `os.write(1)` subprocess bypass (IMPL:30) changes verdicts beyond what is shown; Counter/UserDict/deque canonicalisation (inferred from code, not probed).
