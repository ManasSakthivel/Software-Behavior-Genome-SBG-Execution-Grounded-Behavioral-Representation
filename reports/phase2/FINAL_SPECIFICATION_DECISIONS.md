# Final Specification Decisions (V7-B)

Branch `research/v7b-final-validation`, HEAD `cc56e029`. Documentation only: the frozen spec (`reports/final/V7B_FROZEN_SPEC.md`, "FS") is **not edited here**; this file lists what should change in it, why, and what each choice costs. All numbers remain UNVALIDATED defaults. Nothing here claims equivalence of any pair or a detection rate.

Authority order stays: D1-D11 > SPEC > FS. A decision marked **USER DECISION** would change what a verdict asserts about observed behaviour (the scientific meaning of SBG); I recommend an option but do not treat it as chosen. All other decisions are engineering or documentation clarifications: I recommend and the owner may proceed without a separate sign-off, but they are listed so nothing changes silently.

## 0. Summary

| ID | Topic | Class | Recommendation |
|---|---|---|---|
| UD-1 (SD-01) | A-L1: a lossy or degenerate `SAME` is not evidence | USER DECISION (already applied in code) | Ratify as built (option A) |
| UD-2 (SD-02) | A-U1 + A-16: empty/vacuous changed region, unmodelled lines | USER DECISION (already applied in code) | Ratify A-U1; cap `r_empty` verdicts at S1 (option B) |
| UD-3 (SD-03) | Observation boundary: import-time output and fd-level output | USER DECISION | Include fd-level bytes; keep import-time output, documented |
| UD-4 (SD-04) | Conservative blocking by quarantined / `NO_RUN` inputs | USER DECISION | Keep conservative until calibration data exists |
| UD-5 (SD-05) | K1 on existing development data | USER DECISION (programme) | Do not declare K1 triggered or cleared now (see K1 file) |
| SD-06 | A-B1: both-side binding failure is `NO_RUN(invalid_input)` | engineering | Ratify |
| SD-07 | A-01: required versus advisory isolation properties | clarification | Adopt table in section 2 |
| SD-08 | Definition of "changed unit", tier, bitmap, `r_empty` | clarification | Adopt |
| SD-09 | Determinism control profile and `k_alt` trigger | clarification (SPEC 5.1 already requires) | Adopt |
| SD-10 | A-14: a witness requires sandbox-verified runs | clarification | Adopt |
| SD-11 | `SystemExit` class | clarification | Adopt as built |
| SD-12 | Orderings, enums, counting rules | clarification | Adopt |
| SD-13 | CLI contract and exit codes | clarification | Adopt |
| SD-14 | Two hash chains; definition of reproducibility | clarification | Adopt |
| SD-15 | Canonicalisation of subclasses and opaque values | clarification | Adopt as built |
| SD-16 | S3 refusal, F4 reported-only, defensive `alignment_failed` | clarification | Adopt |
| SD-17 | Output schemas and record-kind mapping | clarification | Adopt |
| SD-18 | Config reserved fields and mapping | clarification | Adopt |
| SD-19 | Budget granularity and `budget_exhausted_s0` selection | clarification | Adopt |
| SD-20 | Pair identity and H definition; single-file scope | clarification | Adopt |
| SD-21 | `NO_RUN` semantics | see UD-4 | - |
| SD-22 | Direction-coverage approximation | clarification | Adopt |
| SD-23 | Normaliser N and exception kinds | clarification | Adopt |
| SD-24 | Tolerance | deferral | Keep default 0 |

User decisions needed: **5** (UD-1..UD-5).

---

## 1. USER DECISIONS

### UD-1 (SD-01) Amendment A-L1: an equality established on a lossy or degenerate canonical form is not evidence of no divergence

**State.** Applied in code at `decide.py:56-58`, `runner.py:263`, `harness.py` (LOSSY flag), commit `cc56e029`; tests `test_phase2_fixes.py::test_decide_lossy_same_is_not_evidence`, `test_lossy_s1_is_insufficient[*]`, `test_lossy_input_does_not_activate_changed_units`; probes `lossy` and `gen` give `INSUFFICIENT(unobservable_outcome)`. The FS says only "Lossy-equal observations are `equal_lossy` and block S2" (s4) and "non-degenerate channel" (s6 S1), so the FS literally allows `NO_DIVERGENCE_OBSERVED(S1)` on lossy equality. The code is stricter than the frozen text and no one ratified that.

| Option | Effect |
|---|---|
| A. Ratify as built: a lossy/degenerate `SAME` does not count as the S1 `SAME` input and does not activate units; with no clean `SAME`, `INSUFFICIENT(unobservable_outcome)`; a clean `SAME` next to a lossy one gives S1 at most | stricter than the FS; no new reason code |
| B. Revert to the FS text: a lossy `SAME` counts for S1, only S2 is blocked | `NO_DIVERGENCE_OBSERVED(S1)` could be issued when the returned values were never read (for example a function returning a lambda or an iterator: only the type name is compared) |
| C. Lossy counts toward S1 but the verdict carries a `lossy` annotation and activation is not credited | still a positive verdict whose statement is false for the unread part |

**Consequences.** A raises the INSUFFICIENT share for programs returning opaque objects (generators, iterators, lambdas, very large containers); K1/K2 numbers measured before the fix (`results/raw/k1_spike*`) are not comparable and must be re-measured before any gate use. B or C keep those counts but let the verdict assert something the engine did not observe.

**Recommendation.** A. **Rationale.** NO_DIVERGENCE_OBSERVED is defined (FS s2) as "no observed-channel difference was found"; a value that was not read was not observed, so equality of its type name is not an observation. A only tightens; it cannot create a false NDO. If ratified, edit FS s6 S1 to read "non-degenerate and non-lossy".

### UD-2 (SD-02) Amendment A-U1 and ambiguity A-16: what NDO says when no changed unit exists

**State.** Applied at `runner.py:114-126,281` (commit `cc56e029`). Changed lines inside bare string statements are `doc_only_lines` (vacuous, never a unit, never a witness unless a declared channel observes the docstring); other changed non-executable lines (not `else:`/`try:`/`finally:`) give `INSUFFICIENT(unmodelled_change)`; comment/whitespace changes vanish; `r_empty` = no changed unit and nothing unmodelled. Probes `doc` and `nolines`: `NO_DIVERGENCE_OBSERVED S2`, `r_empty=true`. Tests `test_phase2_fixes.py::test_docstring_only_is_vacuous_not_a_difference`, `test_comment_or_whitespace_only`, `test_docstring_observed_through_doc_is_a_real_witness`, `test_mixed_executable_and_docstring`, `test_non_executable_non_doc_change_is_unmodelled`.

| Option | Effect |
|---|---|
| A. Ratify as built | NDO at up to S2 with the `r_empty` flag; S2's "80 % direction coverage" is vacuous (coverage defined as 1.0 when R has no branches) |
| B. A, and an `r_empty` verdict (or any vacuous coverage) is capped at S1 | the flag stays; level no longer implies measured direction coverage |
| C. Treat `r_empty` as `INSUFFICIENT(changed_region_not_activated)` | contradicts FS s6 ("flagged, reported as its own stratum"); changes the verdict table |
| D. Treat docstring changes as `unmodelled_change` | unnecessary: docstrings are observable only through a declared channel and that case already yields a witness |

**Consequences.** B needs a small code change (conditional item CB-01 in the backlog: pass `r_empty` into `Evidence`, cap in `sufficiency`). C would change how the FS defines a verdict and would make comment-only commits unscoreable. The unmodelled-line rule (part of A) can make pairs with a lone closing bracket or a decorator move `INSUFFICIENT`; it never creates a positive verdict.

**Recommendation.** Ratify the A-U1 rules and adopt B. **Rationale.** The S2 text promises a statement about changed-region directions that cannot hold when there is no changed region; S1 is the honest ceiling for a vacuous activation, and the stratum flag remains available for analysis.

### UD-3 (SD-03) Observation boundary: import-time output and fd-level output

**State.** (a) The harness redirects `sys.stdout` only, around import and call (`harness.py:181-185,204`), so print statements executed at import time are part of the compared stdout (probe `importprint`: differing import-time prints gave DIVERGENT). (b) Bytes written with `os.write(1, ...)` or by a subprocess go to the real fd 1; the parent receives them in `Result.stdout` but `runner.run` ignores them (probe `subproc`: `os.write(1,b"A")` vs `b"B"` gave NDO S2). FS s4 lists "declared side effects (stdout, ...)" and `stderr` as excluded without saying how stdout is delimited.

| Option (fd-level) | Effect |
|---|---|
| A. Fold the parent-observed fd-1 bytes into the `side:stdout` channel | closes a probe-confirmed false-assurance path; `sbgv7` does not otherwise change meaning |
| B. Treat any fd-level output as a blind spot: `INSUFFICIENT(blind_spot_dominant)` | no new observation; many programs that legitimately shell out become INSUFFICIENT |
| C. Status quo | rejected: NDO is issued while an observable difference exists |

| Option (import-time) | Effect |
|---|---|
| A. As built: stdout is everything written during import and call under H | simple; a module that prints on import differently is a divergence of the scope under H |
| B. Exclude import-time output | needs a separate capture phase; a real behavioural change at import becomes invisible |
| C. Separate declared channel `side:import_stdout` | more faithful, more configuration |

**Recommendation.** fd-level: A (backlog MB-02). Import-time: A, documented ("stdout = bytes written during import and the call"). **Rationale.** Both choices follow the FS aim that every declared channel is actually observed; excluding an effect the program really has would be the silent choice. Consequence of A: K1/K2 dev results involving subprocess or `os.write` output may change.

### UD-4 (SD-04) Conservative blocking by quarantined and `NO_RUN` inputs

**State.** FS B5: a quarantined input "that hit or may have hit a changed unit" blocks; B6: exactly one side limited. As built, **any** quarantined input blocks NDO and S2 (`decide.py:50`), regardless of hits, and every `NO_RUN` input (both-sides limit, sandbox failure, protocol violation, harness error) adds a blocker (`decide.py:51`; `test_no_run_input_blocks_no_divergence`, the red-team B-1 case). SPEC 3.2 says `NO_RUN` contributes no comparison evidence and no B row names it.

| Option | Effect |
|---|---|
| A. Conservative as built: "may have hit" = always; any `NO_RUN` blocks | fewest positive verdicts; lowest risk of a false NDO; hit sets of nondeterministic runs are unreliable anyway |
| B. Precise: a quarantined input blocks only if the union of hit lines over its repeats meets a changed unit (or is unknown); both-limit `NO_RUN` is ignored when clean `SAME` inputs already activate every unit | more NDO; relies on hit lines from runs known to be inconsistent |
| C. Hybrid: A for quarantined, B for both-limit `NO_RUN` | middle |

**Consequences.** A inflates INSUFFICIENT on pairs with one flaky or timing-out input among many (such inputs are common in generated batteries); B can issue NDO on a suite that contains an input the engine could not judge. No calibration data exists to size the loss.

**Recommendation.** A until development data (K2 population, Phase 3) measures the cost; write the rule into FS B5/B6 and name the real cause code per `NO_RUN` (backlog MB-10, which is independent of the choice). **Rationale.** The decision changes how much unobserved behaviour an NDO may coexist with; the engine's own reproducibility evidence cannot support the "did not hit" claim for an input it could not reproduce.

### UD-5 (SD-05) K1 on existing development data

See `K1_K5_READINESS_AND_DECISION.md`. Options: (A) do not evaluate K1 in Phase 2 and leave it neither triggered nor cleared pending the authorised Phase 3 spike (recommended); (B) declare K1 failed on the existing inventory and STOP; (C) amend K1 so that existing data passes (not recommended: FS s13 forbids renegotiation after a gate failure and the thresholds may change only through the development split, not to avoid a stop). This is the programme owner's decision.

---

## 2. Other decisions (recommendation; no separate user sign-off needed)

**SD-06 Amendment A-B1: an input that fails to bind on both versions is `NO_RUN(invalid_input)`.** State: `runner.py:180-182`, `decide.py:51`; tests `test_symmetric_binding_failure_is_not_a_same`, `test_decide_invalid_input_never_positive`. Alternatives: leave as an equal `bind_error` `SAME` (the audit's D-06: NDO S2 without executing any body), or make it a blocker (would punish a bad input rather than ignore it). Consequence: excluded from `X_eff`; with no other clean `SAME` the result is `INSUFFICIENT(no_inputs)`. `invalid_input` is a sub-reason, not a 19th code. Recommendation: ratify. Rationale: S1 requires an input valid on both versions.

**SD-07 A-01 Required versus advisory isolation properties.** FS s10 says "an unverified property gives `sandbox_failure`" and also allows macOS runs flagged `policy_below_minimum`; on macOS `RLIMIT_AS` and `RLIMIT_NPROC` are structurally unverifiable. Alternatives: (a) strict: every I2 property must verify, so every macOS run is `INSUFFICIENT(sandbox_failure)`; (b) required/advisory split; (c) status quo (nothing but network denial gates). Recommendation (b): required = network denial, write confinement, process-group kill, `RLIMIT_CPU`, `RLIMIT_FSIZE`, `RLIMIT_NOFILE`, interpreter 3.13; advisory (flagged in the policy record, run still valid but `policy_below_minimum`) = `RLIMIT_AS`, `RLIMIT_NPROC`, read confinement; on Linux (Phase 3) all become required. Consequence: macOS stays usable for synthetic/benchmark work; a missing required control now fails visibly (MB-06). Rationale: honours both FS sentences.

**SD-08 Changed unit, tier, bitmap, `r_empty`.** Unit = an executable source line (a line with at least one bytecode instruction per `co_lines`) in a version containing it, taken from the V6 `changed_lines` diff; docstring-only lines are vacuous; other non-executable changed lines are `unmodelled_change` (UD-2). Capture tier is L0, and the "changed-region coverage bitmap" is the stored per-run hit-line set (`Run.meta.hits`); FS s6 (L0) wins over SPEC 6.3 (L1) for now (A-05). `r_empty` = no changed unit and nothing unmodelled. Alternatives: basic blocks (more precise, more code), L1 tier (needs event counts and the `max_events_L1` cap). Recommendation: as stated. Rationale: matches the implementation and every conformance row.

**SD-09 Determinism control profile and `k_alt` trigger.** SPEC 5.1 already requires a control profile for primary runs (hash seed, RNG, clock, threads); FS s11 omits it (A-09). Adopt in FS: primary runs pin `PYTHONHASHSEED=0`, `TZ=UTC`, `LC_ALL=C.UTF-8`, single-thread env; alternate settings (`k_alt`) shift RNG seed, `time.time/_ns/monotonic`, `os.urandom` (and so `uuid4`); `datetime.now` is documented as not virtualised. Because "was a virtualised source consulted" cannot be known without instrumentation, the alt runs execute for every candidate witness (as built). Alternatives: leave the hash seed random (programs iterating a set of strings quarantine as `nondeterministic`, probe `hashseed`), or instrument consultation. Consequence: more programs become deterministic and comparable; K2's determinism rate is measured under the pinned profile and must be re-measured. The profile is part of H (SD-20). Recommendation: adopt (MB-07). Rationale: it is already normative in SPEC 5.1; it makes the `nondeterministic` code mean a genuine instability.

**SD-10 A-14 A witness requires sandbox-verified, untampered runs.** FS s2 lists only invalid evidence as voiding a witness but also ranks B3 below DIVERGENT. Adopt: a `CONFIRMED_DIFF` requires every primary, repeat, replay and alt run to be sandbox-verified and tamper-free; otherwise the input is `NO_RUN` with the real blocker (`sandbox_failure`/`unsafe_program`). Alternative: keep witness precedence over B3 (a forged replay could then back a witness; NF-04). Recommendation: adopt (MB-05). Rationale: a witness certifies reproduction; reproduction on an unverified run is not evidence.

**SD-11 `SystemExit`.** Adopt as built: `SystemExit` is `exited(code)` (compared by canonical code); `os._exit` and exit without a result frame are protocol violations (`unsafe_program`). Alternative: `raised(SystemExit, msg)` per SPEC 2.4 table. Difference only for `SystemExit(3)` versus `SystemExit("3")` (code compare differs, message compare equal). Recommendation: as built. Rationale: the code carries meaning that a message string loses.

**SD-12 Orderings, enums, counting.** (a) `secondary` codes are listed alphabetically after the primary; the primary is the lowest rank, ties broken alphabetically (A-07); (b) FS B1 (entry resolution) is read through s5: a missing entry is `unsupported_signature(detail=entry_missing)` (A-06); (c) `r_det=3` means three runs per side in total, including the primary (A-13); (d) `QUARANTINED` is decided before replay, so an intermittent crash is quarantined, not a witness (A-18); (e) add `inputs_exhausted` to the stop-reason enum (D-22); (f) B8 lists `import_error` as in SPEC. Alternatives: rank-ordered secondaries, `r_det` excluding primary. Recommendation: as built. Rationale: these are all deterministic and already implemented.

**SD-13 CLI contract (A-11).** `compare`: 0 verdict written (any verdict value, so scripts must read `verdict.json`), 2 usage/config/inputs/output path error, 3 `ineligible:identical`, 1 internal error (message, no traceback); `verify`: 0 verified, 1 mismatch/tamper, 2 unreadable/missing, 4 evidence omitted by size cap. Alternative: encode the verdict in the exit code (rejected: three verdicts do not map to a process success/failure meaning and would invite treating NDO as "pass"). Recommendation: adopt (MB-14).

**SD-14 Two hash chains and reproducibility (A-10, X4).** Define (i) the store chain (`evidence.jsonl`: seq/prev/hash; includes `meta`, therefore timings) and (ii) the per-run event-stream chain (EV-13, excludes run id and repeat index), which does not exist yet and is retired until event streams are stored. Reproducibility is defined on **ids and decisions** (run, witness, pair, verdict ids; value, level, codes; per-input rows), not on chain head bytes or `cpu_seconds_spent`. Alternative: strip timings from the chain (loses their tamper evidence). Recommendation: adopt. Rationale: probe shows ids equal and heads different; this states what is promised.

**SD-15 Canonicalisation (A-15).** Adopt the as-built rule in FS s4: containers (dict, list, tuple, set, frozenset, deque, and any subclass) are read by the builtin base type's own methods and tagged `["obj", type, ...]` when not the exact builtin type; instance state is `__dict__` plus every `__slots__` descriptor in the MRO; int/float/str/bytes subclasses keep `<value>`; no user code runs; cycles are structural; opaque objects, depth > 3, > 5000 items, > 50000 nodes, nesting > 40 and unreadable slots set `lossy`. Recommendation: adopt. Evidence: 24 tests in `test_harness_canon.py`. Open code defect inside this rule: big integers (NF-01, MB-01).

**SD-16 S3, F4, defensive code.** (a) `s3_enabled=true` is refused until calibration shows S3 attainable and ordered; the FS row-3 wording "highest level whose floors hold" is read as S1 or S2 only (A-12); (b) F4 (input diversity/budget) is reported in the record but has no floor until the development split calibrates one (OI-02); (c) `alignment_failed` is a defensive code produced only when region computation raises. Recommendation: adopt. Rationale: states what the code does and prevents a reader inferring a diversity guarantee.

**SD-17 Output schemas and record-kind mapping.** Record kinds as built: `ProgramVersion` (derived), `Run` and `Observation` (observation), `Witness`, `SufficiencyRecord` (status `uncertain`), `EvidencePackage`, `Verdict` (derived). The FS names ChangedRegions, SourceMapping, ReplayCheck, Reproducibility, HarnessDeclaration, Input, ExplorationLog and completeness records; as built they are fields of `EvidencePackage.body` (regions, config/H, inputs, rows) or derivable (ReplayCheck, Reproducibility from the Run records). `verdict.json` keys: verdict, level, primary, secondary, witness_id, verdict_id, sufficiency_id, pair_id, package_id, r_empty, policy_below_minimum, cpu_seconds_spent, log_head. Alternative: split into separate kinds (more records, no gain while `verify` recomputes from the package). Recommendation: record this mapping in the FS and defer a JSON Schema file.

**SD-18 Config reserved fields.** FS s11 fields not built are marked "reserved": `s3_plateau_window`, `static_match_f1_trigger`, `witness_outside_R_diag`, `max_events_L1`, `seeds`, `stats`, `platform`, budget grid (evaluation protocol), `claims_cpu_s` (= default `cpu_s` 10) and `fast_cpu_s` (= explicit `cpu_s` override, 2). Constant-valued fields `normaliser_id`, `stderr=excluded`, `capture_tier=L0` are accepted only with their single built value (MB-13); any other value is rejected as "not built". Alternative: accept and ignore (rejected: nothing degrades silently).

**SD-19 Budget granularity (A-17).** CPU budget = child `ru_utime+ru_stime` plus the parent's own process time; the check runs between runs, not between inputs; `budget_exhausted_s0` is chosen when the budget stop cut the input list short or the budget was exhausted when the last input finished with units still unhit; otherwise `changed_region_not_activated`. Recommendation: adopt (MB-11).

**SD-20 Identity.** `pair_id` hashes both source digests, the entry, and H, where H = harness section, repeat section, suff section, harness digest and sandbox policy id (not the budget, which is a run policy stored in the package). Single-file scope: "identical" means identical source bytes of the two files (and identical interpreter, since one is used); dependency/runtime byte-identity is a project-level check deferred to Phase 3. Alternative: hash the whole config. Recommendation: as stated (MB-09, MB-08).

**SD-21** `NO_RUN` semantics: see UD-4.

**SD-22 Direction coverage.** Denominator = 2 x number of branch instructions (`POP_JUMP_IF_*`, `FOR_ITER`, `SEND`) on changed lines per version; every direction is counted reachable (conservative); no branch in R gives vacuous coverage 1.0 (see UD-2). Recommendation: document; additional tests (MB-16).

**SD-23 Normaliser N and kinds.** N (version `N1`, declared in H): `0x...` addresses to `0xADDR`, the private workdir to `<WORKDIR>`, and (new) the source file path and its directory to `<SRC>`/`<SRCDIR>` in exception messages and stdout (MB-03). Witness `kinds` are the FS enum outcome/exception/side_effect/api; a message-only exception difference is `exception`. Recommendation: adopt.

**SD-24 Tolerance.** `float_tol` stays 0 by default; a nonzero tolerance would require recording the exact result, a `tolerance_masked` flag and a never-pool rule (C7). Deferred: no code until a declared tolerance is actually needed.

---

## 3. What this file does not decide
S3 enablement, any K gate, any change to numbers (floors, repeat counts, budgets), explorer or state-module scope, and the Linux isolation design. These need development-split evidence or Phase 3.
