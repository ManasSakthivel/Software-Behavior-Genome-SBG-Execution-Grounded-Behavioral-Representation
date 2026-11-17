# V7-B Frozen Specification (P0 freeze)

Authority: `P0_BINDING_DECISIONS.md` (D1-D11) > `P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md` (SPEC) > this file. Where this file is silent, the SPEC governs. All numbers are UNVALIDATED defaults (D3), changeable only through the development split, never on sealed data. Nothing here claims equivalence or correctness of any pair; verdicts describe what was observed.

## 1. Scope

V7-B: sufficiency-aware, witness-based differential comparison of two Python versions of a declared scope (entry point), with adaptive exploration. Unit = pair + scope + harness declaration `H` + seed policy. V7-A (internal state) is an optional gated pilot outside this freeze.

## 2. Verdicts (exactly three; first match wins)

| # | Condition | Result |
|---|---|---|
| 0 | src, deps, runtime byte-identical | no verdict (`ineligible:identical`), excluded from metrics |
| 1 | some input has `o(x)=CONFIRMED_DIFF` (not voided) | `DIVERGENT_OBSERVABLE` |
| 2 | any blocking condition B1..B9 holds | `INSUFFICIENT(primary; secondary codes)` |
| 3 | none holds | `NO_DIVERGENCE_OBSERVED(S1|S2|S3)`, highest level whose floors hold |

- Prohibited as outcomes anywhere: `EQUIVALENT`, `SAME`, `PASS`, `VERIFIED`, `SAFE`, "implicit pass". `BOUNDED_EQUIVALENCE_PROVEN` is a formal claim with its domain, never a verdict, never required.
- `DIVERGENT_OBSERVABLE` is absorbing; only invalid evidence (failed audit replay, environment drift, supersession) voids a witness, then the verdict is recomputed. The other two values are not monotone in exploration. Sufficiency is scored only for `NO_DIVERGENCE_OBSERVED`.
- `NO_DIVERGENCE_OBSERVED` means: on the explored deterministic inputs, under `H`, every changed unit ran at least once in each version containing it and no observed-channel difference was found. Nothing about unexecuted inputs.
- `internal_divergence in {none, observed, unknown}` is an advisory annotation, present only if optional module E is enabled and only on `NO_DIVERGENCE_OBSERVED`/`INSUFFICIENT`; it never changes value, level, code or any metric.

### Blocking conditions (primary code = lowest rank; a missing record counts as true)

| Rank | Condition | Code(s) |
|---|---|---|
| B1 | build/import/entry resolution fails | `import_error` |
| B2 | scope or changed-region alignment failed/unhandled | `alignment_failed`, `unsupported_signature`, `ambiguous_entry`, `unmodelled_change` |
| B3 | sandbox property violated or unverified on a contributing run | `sandbox_failure`, `unsafe_program` |
| B4 | unconfirmed or environment-sensitive candidate | `flaky_witness`, `env_sensitive` |
| B5 | quarantined input that hit or may have hit a changed unit | `nondeterministic` |
| B6 | exactly one side ended in a harness limit | `resource_limit` |
| B7 | capture truncated, or blind spot in a changed unit | `capture_truncated`, `blind_spot_dominant` |
| B8 | no usable input / no non-degenerate channel / internal failure | `no_inputs`, `unobservable_outcome`, `tool_error` |
| B9 | an S1 floor fails | `changed_region_not_activated`, `budget_exhausted_s0` |

## 3. Per-input outcome `o(x)`

`CONFIRMED_DIFF` | `UNCONFIRMED_DIFF` (replay disagreed) | `ENV_SENSITIVE_DIFF` | `SAME` (equal on `C_obs`, both deterministic-confirmed) | `QUARANTINED` (a version not self-consistent) | `LIMIT_ASYMMETRIC` | `NO_RUN(reason)`.

Terminal classes: `returned(v)`, `raised(type,msg)`, `exited(code)`, `crashed(signal)` (witness only if reproduced in every replay), `limit(kind)` (never a witness; both sides limit gives `NO_RUN`). Introduced non-termination is `INSUFFICIENT(resource_limit)`, reported as its own stratum.

## 4. Observation boundary

`C_obs`: return value; exception (qualified type + normalised message); declared side effects (stdout, sandbox temp content, argument post-call digests, module globals written). Excluded: stderr, performance/resource, line numbers, tracebacks, run ids, internal state. Channels uninstrumentable in either version drop to the intersection; empty intersection gives `unobservable_outcome`.

Equality is on the canonical typed form after normaliser N (user `__eq__`/`__repr__` never called). Type tag is identity (`1` vs `1.0`, `list` vs `tuple` differ). Floats: exact binary64, NaNs equal; a declared tolerance is part of the identity and never pooled with exact verdicts. Mappings key-order-insensitive; sets unordered; sequences ordered; objects to depth 3. Exceptions: same qualified type (no subclass coalescing) and same normalised message (`exc_message=ignore` is a declared alternative identity). Lossy-equal observations are `equal_lossy` and block S2.

## 5. Witness schema and replay

`Witness{pair, scope, input_hash, harness_decl_id, kinds[outcome>exception>side_effect>api], obs_old, obs_new, replay_set[{run_id, version, observation, status}], locus? ("unlocalised" valid), env/build ids, sandbox_policy_id}`. Immutable; voidable only by `Supersession`.

Protocol (fresh child processes, all charged to the CPU budget):
1. Both versions self-consistent over `r_det=3` repeats (early stop at first disagreement), else `QUARANTINED`.
2. `r_replay=5` fresh replays per version; confirmed iff 5/5 reproduce each version's primary observation and the versions still differ. Agreement is on `C_obs`, not whole-trace hash or locus. First disagreement gives `UNCONFIRMED_DIFF`.
3. Interpreter/tracer build mismatch makes a replay `inconclusive`; repeat in a matching environment.
4. Control-sensitive candidate (virtualised RNG/clock/entropy/uuid consulted): also reproduce under `k_alt=3` alternate control settings, each version's own observation invariant; else `ENV_SENSITIVE_DIFF`.
5. Optional minimisation; the minimised input must itself pass 1-2.

A witness asserts only that the versions differ observably on this input.

Signatures: compatible (same arity/names, defaults added, declared rename) proceeds. Incompatible with `api_break_probe=true`: inputs valid for one side are bound against the other; a deterministic argument-binding failure before the body runs (`inspect.signature.bind`), confirmed by 1-2, is a `kind=api` witness, reported as its own stratum. Entry missing in one version: lift to outermost common frame, else `unsupported_signature(detail=entry_missing)`. Ungenerable input types: `unsupported_signature`, never an invented default. Several candidate entries: `ambiguous_entry`.

## 6. Sufficiency S0-S3

Conjunction of floors on separately reported factors F1 determinism, F2 instrumentation completeness, F3 changed-region activation, F4 input diversity/budget; levels nested; no scalar score decides a level. Each record stores the factor vector, stop reason, `r_det`, run-set Merkle root, `X_eff` size, quarantined count, unhit units, `r_empty`.

A changed unit is hit iff a deterministic-confirmed input executed it in a version containing it (deleted: V1; inserted: V2; modified: both). Uninstrumentable changed units count as unhit; R is never shrunk. `r_empty` (R empty after normalisation, bytes differ): activation vacuous, flagged, reported as its own stratum.

| Level | Floors |
|---|---|
| S0 | Label for "an S1 floor fails". Only inside `INSUFFICIENT`; never with `NO_DIVERGENCE_OBSERVED`. |
| S1 | >=1 `SAME` input valid on both versions, deterministic-confirmed, non-degenerate channel; 100% of changed units hit; `r_det` done for each contributing input; no quarantined input that may hit a changed unit; tier >= L0 with changed-region coverage bitmap; no truncation; no blind spot in a changed unit; tamper flag clear. |
| S2 | S1 and: branch/direction coverage of changed regions >= 0.80 of statically reachable directions, per version; every contributing input deterministic-confirmed (trace-unstable but outcome-stable allowed); all declared channels instrumented; no `equal_lossy` on `ret`/`side`. |
| S3 | S2 and: plateau (no new changed-region direction coverage in the last 25% of budget); all contributing inputs trace-stable, zero quarantined; L2 capture of changed regions and no blind spot reachable from R; a second, differently configured explorer within the same total budget finds no direction the first missed. **`s3_enabled=false` by default**; S3 may be emitted only after calibration shows it attainable and ordered. Otherwise the maximum level is S2. |

Permitted: "on n explored deterministic inputs, under `H`, changed code ran and no observable difference was found" (S2 adds the 80% direction statement). Prohibited at every level: equivalence, "no bug", "safe to merge", any probability or confidence of equivalence, statements about unexecuted inputs or internal state, reading S3 as closer to equivalence (a rare guard inside an already-hit block is invisible to every floor).

Calibration claims (claims to test, not definitions or gates): miss-rate caps S1 0.35, S2 0.20, S3 0.10, ECE 0.05.

## 7. Reason codes (closed enum, 18)

`import_error, unsupported_signature, ambiguous_entry, alignment_failed, unmodelled_change, sandbox_failure, unsafe_program, flaky_witness, env_sensitive, nondeterministic, resource_limit, capture_truncated, blind_spot_dominant, no_inputs, unobservable_outcome, changed_region_not_activated, budget_exhausted_s0, tool_error`. Retired: `LOW_STATE_COVERAGE`, `internal_only_difference`, `observed_same_at_Sx`. `tool_error` is never blamed on the program. Extension only by minor version; an unknown code downgrades dependent decisions to `INSUFFICIENT`.

## 8. Evidence model

Every record has `evidence_class` in {observation, derived, inferred, proof} and optional `status` in {missing, invalid, uncertain}. Runs, reproducibility, replay checks, completeness: observation. `ChangedRegions`, `SourceMapping`, the witness difference: derived. Alignment, locus, `ImpactSet`: inferred. `SufficiencyRecord`: derived, uncertain. `FormalResult`: proof. Chains: `DIVERGENT_OBSERVABLE` -> Witness -> primary runs, repeats, replays + `ReplayCheck`, `H`, programs, input, environment, sandbox policy. `NO_DIVERGENCE_OBSERVED` -> `SufficiencyRecord` -> run-set Merkle root + per-input rows, reproducibility, completeness, `ChangedRegions`, `ExplorationLog`, `H`. `INSUFFICIENT` -> the records that triggered each blocking condition (degenerate `level=S0` record allowed). No label-namespace record reachable (T6); recomputing section 2 from the chain reproduces value and primary code (T4). Stored by default: replay recipe + hashed event stream (about 300 B/run); full events only for witness runs, a 5% audit sample and escalations.

## 9. Modules (core A, B, C, D, G, H, I, K, L; E optional pilot; F removed; J optional, off)

| Mod | Reads | Writes |
|---|---|---|
| A Exploration | `ChangedRegions`, `SignatureSketch`, coverage bitmaps, `H`, budget, pre-declared seed | `Input`+provenance, `ExplorationLog` (stop reason in {budget, saturation, all_changed_branches_both_ways, domain_exhausted, unsupported_signature, no_generator}). No labels, benchmark identity or other pairs' outcomes (D11); also runs diff-blind. |
| B Capture | `ProgramVersion`, `Input`, env, `SandboxPolicy`, tier, focus regions, repeats, control profile | `RunBundle` (`ExecutionRun`, chunks, completeness, `Reproducibility`); status in {returned, raised, exited, crashed, killed_wall, killed_mem, timeout, oom, truncated, policy_violation, base_exception}; `trace_tampered`. Only module that runs untrusted code. |
| C Static | two `ProgramVersion` | `SourceMapping`, `ChangedRegions{kind, confidence, region_size_fraction, unmodelled}`, `SignatureSketch`, `parse_status` |
| D Fabric | all records | storage, `verify_chain`, `replay(recipe)` via B |
| G Alignment | `SourceMapping`, `ChangedRegions`, run projections | `SemanticCorrespondence`, per-locus trust; never affects verdict value |
| H Divergence | paired `RunBundle`, `H`, `Reproducibility`, replay via B | `o(x)`, `ReplayCheck`, `Witness`, optional locus/`ImpactSet` |
| I Decision | all pair evidence | `SufficiencyRecord`, `Verdict` (sole writer) |
| K Validation | all read-only + labels | manifests, adjudication, holdout commitments, scoring, gate reports |
| L Governance | manifests, store | freezes, audits (T1-T7, isolation compliance) |
| E (optional) | L2 chunks, alignment trust | `internal_divergence` annotation |

Dependencies are acyclic, by record exchange through D.

## 10. Isolation (D10; each a P1 pass/fail check; an unverified property gives `sandbox_failure`)

I1 fresh child process per run (CPython 3.13, `-I`, scrubbed env, private cwd); I2 `setrlimit` CPU/FSIZE/NPROC/NOFILE/CORE=0 plus parent RSS watchdog; I3 process-group kill; I4 tracing outside user-code reach (`sys.monitoring`) with tamper detection; I5 network denial (macOS `sandbox-exec`; Linux container `--network none`); I6 write confinement to private tmp; I7 exact failure classification. Legacy runner/tracer is `v6_compat` only; its runs are invalid evidence. Third-party repositories run only under Linux container isolation; macOS runs are synthetic/benchmark-only, flagged `policy_below_minimum`. Hostile fixtures: zero escapes, no stray processes.

## 11. Config fields (defaults, UNVALIDATED)

```
harness: c_obs=[ret,exc,side:stdout,side:file,side:argmut,side:global]; normaliser_id
         float_tol={rel:0,abs:0}; ordered_mapping=false; exc_message=exact_normalised
         stderr=excluded; capture_tier=L0(+bitmap); api_break_probe=true
repeat:  r_det=3; r_replay=5; k_alt=3
suff:    s2_branch_floor=0.80; s3_plateau_window=0.25; s3_enabled=false
         static_match_f1_trigger=0.90; witness_outside_R_diag=0.05
budget:  unit=cpu_seconds(all processes, incl. overhead); grid=[10,60,300]; headline=60
         per_run: claims_cpu_s=10, fast_cpu_s=2, wall_s=20, rss_mib=2048, max_events_L1=200000
         (provisional; frozen from P1 measurement)
         tracing_overhead_target: <=5x call/branch, <=25x median line
seeds:   exploration_seed in {1001..1005}; bootstrap_seed=42
stats:   effect_of_interest=+10pp; family={H2a,H2b,H4}; Holm alpha=0.05; no non-inferiority
         K5 floor: projects>=60, divergent_pairs>=250, mixed_class_projects>=20, kappa>=0.7
platform: python=3.13; policy per section 10
```

## 12. Gates

G0-G8 only. K1 real-pair feasibility (>=100 runnable pairs, >=8 projects): fail STOP. K2 determinism-confirmed >=70% and replay+crude activation >=35% on K1 pairs under D10 isolation: fail one redesign of B (<=4 weeks), second fail STOP. K3 activation >=60% and >=+15 points over replay: fail PIVOT to replay+structure-aware exploration with no directed-exploration claim. K4 FAR(V7) below both like-for-like comparators at matched decided coverage >=0.60, lower 90% bound >0 and >=10pp: fail PIVOT to V7-B' (sufficiency-aware differential testing, no explorer/impact/state); V7-B' no better than B1: STOP. K5 power-sized benchmark, kappa, clean leakage audit before any unseal: fail means no confirmatory evaluation (exploratory report only). Containment (zero escapes) is a hard G1 gate.

## 13. Final P0 decision: GO_P1 (scoped)

- All 10 blocking contradictions are closed by D1-D11 and the SPEC (one verdict set, one S0-S3, one K/G table, one budget unit, no equivalence verdict). The four reconciled drafts were checked and aligned (fixes logged in the reconciliation report).
- The remaining unknowns (isolation properties other than `sandbox-exec`, real-pair feasibility, determinism rate, object-argument inputs, per-run limits) cannot be settled on paper; they are what P1 measures and K1/K2 gate. STOP is not warranted: no gate has failed and V7-B needs no unproven mechanism.
- REVISE_P0 is not warranted: the missing reconciled documents (schema R1, roadmap R1, master/final-decision R1) are not inputs to the work below; they are debt to close before G0.

Authorised scope: (1) build the isolation runner and pass I1-I7 on a Linux container host (Docker was down in P0); (2) a 2-3 week feasibility spike on about 30 candidate projects (build success, drivable fraction, input-representation coverage, determinism, replay activation); (3) evaluate K1 and K2. No K3+ work until K2 passes; any gate failure follows section 12 without renegotiation.

Not claimed: any detection rate, that any threshold is correct, or equivalence of any pair.
