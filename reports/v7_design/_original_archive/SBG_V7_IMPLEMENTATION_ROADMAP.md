# SBG V7 Implementation Roadmap

Status: design document, no implementation. Companion: `SBG_V7_RISK_REGISTER.md`. Shared brief: `_DESIGN_SPINE.md`.
Scope: Python first. Java/C are contract-compatible by design and carry NO claim until tested (section 9).

## 0. How to read this document

- All numeric budgets and thresholds below are PROPOSED pre-registered values. They are to be frozen in P0 (`governance/prereg_v7.json`) before any dev-set result is looked at. Changing one afterwards requires a dated amendment, as in the V6 freeze/amendment discipline (`experiments/final/make_freeze_amendment*.py`).
- Effort is in engineer-weeks (ew): point estimate (P10-P90). Staffing assumption: 3 engineers (E1 capture/infra, E2 analysis/verdict, E3 benchmark/eval), 0.5 statistician/PI, and a pool of 2 adjudicators at roughly 0.3 FTE each (adjudication effort is counted in P7). Estimates are not additive in the ranges; see section 3.
- Gates: G0-G9 (one per phase, a phase is "done" only when its gate passes). Kill/pivot checkpoints: K1-K5 (section 4). Risk IDs R01-R34 refer to the risk register.

## 1. What exists and what it implies for the plan (grounded in the repo)

- `experiments/final/extraction.py` (563 lines): single shared execution pass over `sbg.v2.execution.runner.SandboxRunner`, N_RUNS=5, MAX_EVENTS=5000, seed 42, records failure reasons. Reusable as the P1 reference baseline and a regression oracle (2392/2392 from-raw reproduction already demonstrated).
- `sbgv6/observe.py`: `Adapter` Protocol with only `observe(path) -> Observation`; Java/C "interface only". This is a too-thin contract (no scope, no budget, no completeness metadata, no replay); V7 replaces it with the contracts in section 2 and keeps the V6 `Observation` as a legacy shim.
- A grep of `sbg/v2/execution/runner.py` found no `subprocess`, `resource` or rlimit use. Treat the current "sandbox" as in-process isolation, NOT a security boundary, until verified in P1 step 1. If confirmed, P1 safety work is new construction, not hardening.
- `benchmark/` has `splits/leakage_audit_report.json`, `ground_truth/validator.py`, `external/{bugsinpy,quixbugs,quixbugs_java}`. These are dev-grade assets and must be labelled contaminated (spine: no pristine V5/V6 holdout). They are usable as a DEV pool and for the K2 activation census, never for the sealed holdout.
- Known observation failure budget to beat (BugsInPy coverage 28.5%; nondeterminism 60, unsupported signature 49, import 4; QuixBugs declared 36 pairs without inputs; v8test 69 NOT_ACTIVATED).

## 2. Cross-cutting contracts (defined in P0, versioned, language-neutral)

All contracts are JSON-Schema (draft 2020-12) documents with a `schema_version`, canonical JSON serialisation (sorted keys, no floats without explicit precision, UTF-8) and a content hash `sha256(canonical_json)`. No Python object leaks into a contract (no pickles, no repr strings as keys; V6 SP-11 repr artifact is the cautionary case).

| Contract | Key fields (illustrative, not exhaustive) |
|---|---|
| `ProgramVersion` | content hash, language, source-tree hash, dependency lock hash, interpreter/toolchain id, entry scope (function/class/module), provenance (repo, commit) |
| `Scope` | list of target symbols; unit boundary; declared I/O surface (args, globals read, files, env) |
| `ExecutionPlan` | seed(s), time/exec/event/memory budgets, determinism controls requested, sandbox profile id |
| `Event` | `trace_id, seq, kind` in {call, return, line, branch, exception, state_write, io, alloc_summary}, `loc` (file hash, line, symbol id), `payload` (canonical value digest + bounded canonical value), logical clock. No wall-clock in hashed fields. |
| `TraceBundle` | version id, input id, ordered events (content-addressed chunks), outcome (return digest / exception type+message digest / timeout / crash / oom / killed), determinism report |
| `CaptureManifest` (completeness metadata) | per trace: events dropped, cap hit, uninstrumented callee set, C-extension boundary crossings, unobserved I/O, value-digest truncations, determinism-control status (each control: applied / not applicable / failed), N repeat agreement |
| `WitnessInput` | canonical encoded input, generator provenance (replay / structure-aware / property / directed + seed), minimisation status |
| `AlignmentMap` | static node mapping (AST/CFG), dynamic anchors used, confidence per mapping, unmapped regions (explicit) |
| `DivergenceRecord` | witness id, first-divergence locus (old loc, new loc, event index), divergence class (see below), per-view diffs, replay confirmations (k of n) |
| `SufficiencyReport` | changed-region activation (bool + hit counts per changed region), state-coverage level, budget consumed, distinct-path count, unobserved-boundary list |
| `Verdict` | one of three values, reason code, evidence hashes, sufficiency level, tool + schema versions |
| `BenchmarkPair`, `AdjudicationRecord` | label provenance, adjudicators, protocol, disagreement log, leakage-audit hashes |

Evidence store (P0): append-only, content-addressed (hash = key), write-once; a run manifest lists the hashes it used. A `verify` command recomputes every hash. This extends the V6 manifest/hash discipline.

Verdict set (refinement of the spine, see Disagreements in my final reply):
1. `DIVERGENT_OBSERVABLE`: output/exception/declared side-effect differs for a replayable witness. Sound for deterministic scopes by construction (replay confirms).
2. `DIVERGENT_INTERNAL_ONLY`: outputs equal on the witness but internal state/trace differs after alignment. Advisory class. It is NOT a behavioural-difference claim because refactorings legitimately change internals. It becomes evidence only if validated against adjudicated "masked divergence" ground truth (P3/P7).
3. `NO_DIVERGENCE_OBSERVED` with a sufficiency level S0-S3 (S0 = changed region never activated, i.e. effectively INSUFFICIENT; S1 = activated by at least one input; S2 = activated with distinct paths/state classes above a stated count; S3 = budget exhausted without new coverage). Never "equivalent".
4. `INSUFFICIENT` with reason code (non-deterministic, no-valid-input, import failure, unsupported signature, sandbox kill, budget). (Spine's INSUFFICIENT/UNKNOWN; counted as the abstention class.)

## 3. Phase schedule, effort and critical path (summary)

| Phase | Name | ew point (P10-P90) | Hard deps | Can run in parallel with | Conditional? |
|---|---|---|---|---|---|
| P0 | Governance, freeze, evidence schema, immutable store, baseline harness skeleton | 3 (2-5) | none | P7a starts | no |
| P1 | Capture hardening: sandbox, determinism, completeness, replay, robustness suite | 8 (5-14) | P0 | P2, P7a | no |
| P2 | Static context + alignment | 5 (3-8) | P0 (schema) | P1, P7a | no |
| P3 | Divergence/localisation, sufficiency, three-valued verdict; synthetic suites; baselines | 8 (5-13) | P1, P2 | P7a/b, P4 stage 1 design | no |
| P4 | Adaptive exploration (3 stages) | 10 (6-18) | P1, P2, P3 verdict core | P7b | no (but killable) |
| P5 | State/invariant + multi-view projections | 8 (4-14) | P3, K4 pass | P6, P7b | YES (ablation-gated) |
| P6 | Impact analysis | 5 (3-8) | P3 (needs P5 only if state views used) | P5, P7b | YES |
| P7 | Independent benchmark construction + adjudication (P7a protocol/sourcing/seal; P7b adjudication/QA) | 14 (9-24), mostly parallel | P0 for 7a; P3 stable for 7b labels vs tool outputs not needed (labels are tool-independent) | everything | no |
| P8 | Sealed-holdout evaluation | 3 (2-5) | P3+P4 frozen, P5/P6 decision made, P7 complete, K5 pass | none | no |
| P9 | Optional prediction layer (P9a) and formal tier (P9b) | 6 (3-12) | P8 for P9a; P3 for P9b spike | P9b can start earlier | YES |

Totals: core (P0-P4, P7, P8) 51 ew (P10-P90 about 36-82 if summed; realistic aggregate 40-70 with partial independence). With P5+P6: 64 ew. With P9: 70 ew.

Critical path (calendar, 3 engineers): P0 (3) -> P1 (8) -> P3 (8) -> P4 (10) -> [K4 thesis decision] -> P8 (3) = 32 weeks (about 22-48). P2 (5) hides inside P1's 8 weeks. P7 (14 ew) must finish by the end of P4 (week ~29) or it becomes the critical path; start it in week 1 with E3 full time and adjudicators from week 8. If K4 passes and P5+P6 are funded, they add up to 8 calendar weeks (P5 8 ew in parallel with P6 5 ew on two engineers) before P8: path 40 weeks.

Principal ordering changes versus the suggested order (and why):
1. P7 is split. P7a (protocol, source selection, sealing the holdout by hash commitment, dev pool) starts in week 1 in parallel with P0/P1. Reason: benchmark construction is the longest-lead item and the scientific question cannot be answered without it; late construction invites tuning on what will become the holdout.
2. Baseline harness (plain differential, coverage-guided differential, conventional features, V5, V6 re-run) is built in P0/P1 and frozen before P3. Reason: "beats baselines at equal budget" is the only success criterion; baselines built after the system are weaker (V6 lesson).
3. An activation census (K2) is moved to mid-P1, before the full hardening, because observation failure, not modelling, dominated V6.
4. The thesis go/no-go (K4) sits at the end of P3/P4, BEFORE P5/P6 are funded. P5/P6 are explicitly conditional.
5. P9b (formal tier) can be a 2-ew spike after P3, independent of the rest; P9a (learned prediction) is only after P8 and never feeds the primary claim.
6. Synthetic suites in P3 are generated from a spec independent of the detectors, with a generator-fingerprint audit (V6 GBM fingerprint 0.972 to 0.742 leave-type-out), because the V6 circularity (label = f(mutation generator)) would otherwise recur.

## 4. Early kill / pivot checkpoints (pre-stated)

| ID | When | Test | Proceed | Pivot / stop |
|---|---|---|---|---|
| K1 | end week 4 (P7a pilot) | Data feasibility: runnable real-defect pairs assembled with a working env, unit-level entry, independent of V5/V6 benchmark generators | >= 100 runnable pairs from >= 8 projects | 60-99: shrink claims to "exploratory". < 60: drop real-bug claims, keep controlled-suite + QuixBugs-style study only; re-scope programme as methods paper |
| K2 | mid-P1 (week ~6) | Activation census on the DEV pool (BugsInPy-style, >= 150 pairs) with replay-only and a crude random-argument generator: fraction of pairs where changed region is entered in both versions by >= 1 input, and capture deterministic | Replay+crude gives >= 35% activation and capture-determinism >= 70% of runnable pairs | Capture-determinism < 50% after determinism control: restrict scope to pure/deterministic units and state that limit in all claims. Activation < 20% even with crude generation: investigate harness bug before anything else (one retry, 2 weeks) |
| K3 | P4 stage 2 end (structure-aware/property-based) | Activation uplift over replay at default budget (60 s, 4 cores, <= 5000 execs/pair), same pairs as K2 | Activation >= 60% AND uplift >= +15 pp absolute over replay (paired bootstrap, program-cluster, lower 90% CI > 0) AND >= +5 pp over coverage-guided differential fuzz baseline | Activation < 50% or uplift < +10 pp: STOP stage 3 and concolic; ship V7 as "sufficiency reporting" (honest INSUFFICIENT rates) on top of replay; revisit scope claims |
| K4 | end P3 and again after P4 | THE thesis test on the dev benchmark at equal execution + wall-clock budget: does state/trace divergence add anything over output differential? Metrics: (a) recall of adjudicated-masked divergences (see P3 suites, and a real-bug subset), (b) false-assurance rate (true divergent pairs given NO_DIVERGENCE_OBSERVED at S>=2), (c) time/exec-to-first-detection | Any of: (a) +10 pp recall on masked controlled suite AND >= +3 pp on real dev; or (b) relative reduction >= 20% with CI excluding 0; or (c) median detection executions reduced >= 25% | If none: thesis falsified at dev. Do NOT build P5/P6/P9. Pivot to "sufficiency-aware differential testing" (output verdict + calibrated INSUFFICIENT), proceed straight to P8 with that smaller claim |
| K5 | before P8 | Benchmark validity: adjudication Cohen kappa; leakage audit; statistical power | kappa >= 0.70 on a double-adjudicated 25% sample; >= 200 adjudicated pairs with >= 60 truly divergent real defects across >= 15 projects; leakage audit clean (no shared program clusters, no generator fingerprint predictive at AUROC > 0.60 leave-project-out) | Underpowered: do not run P8 for a confirmatory claim; report as exploratory with CIs. Leakage found: rebuild affected strata, do not unseal |

Overall stop condition: see risk register section "Conditions under which V7 should be stopped".

## 5. Phase specifications

Package layout (new, additive; no edits to existing files): `sbgv7/{governance,evidence,sandbox,capture,static,align,diverge,sufficiency,verdict,explore,state,views,impact,bench,eval,formal,adapters}`; tests under `tests_v7/`; frozen artifacts under `results/v7/`.

---

### P0. Governance, freeze, evidence schema, immutable store

**Objectives.** Make V7 unable to repeat V6's process failures: a pre-registered analysis plan with the kill thresholds in section 4, a branch/freeze discipline, versioned language-neutral contracts, and a tamper-evident evidence store. Declare the V5/V6 benchmarks as contaminated DEV assets. Skeleton of the baseline/validation harness (K).

**Dependencies.** None.

**Modules.** `governance` (prereg file, freeze, amendment log, hash manifest, claim-evidence matrix template), `evidence` (schemas, canonicaliser, content-addressed store, `verify`, provenance DAG), `eval` skeleton (cluster bootstrap, permutation tests, paired comparison, ported from V6 stats).

**Data contracts.** Section 2 contracts (all), `prereg_v7.json` (hypotheses, primary metric, equal-budget definition = (max execs, max wall-clock, max events) all matched, baselines list, kill thresholds, dev/holdout policy, multiple-comparison correction), `CLAIM_LEDGER.md` structure (claim -> evidence hash -> status).

**Unit tests.** Canonical JSON is byte-stable across platforms/python versions (golden vectors); hash collision/mutation test (flip 1 byte -> `verify` fails); write-once enforcement; schema round-trip for every contract with hypothesis-style generated documents; no-float-nondeterminism test.

**Integration tests.** Ingest a synthetic run end-to-end; re-derive manifest from raw; "from-raw reproduction" template reproduces V6's 2392/2392 as a smoke check of the discipline (reuse existing script, read-only).

**Performance tests / budgets.** Store write >= 50k events/s single thread for 200-byte events; verify 1M events <= 10 s; storage <= 60 B/event after zstd on typical traces; manifest build for 10k bundles <= 60 s.

**Scientific validation.** Prereg review by someone outside the build team (statistician): checks equal-budget definition, that K-thresholds are falsifiable, and that the primary metric is not a function of any label generator. Prereg committed (hash published into the store) before P3 begins.

**Completion criteria (G0).** All contracts versioned and frozen v1.0; store passes tamper test; prereg + kill thresholds signed and hashed; V5/V6 data labelled `contaminated_dev` in a registry; branch `v7/main` created with protected rules (V6 tag untouched); baseline harness skeleton runs a null baseline through the store.

**Risks and fallback.** Over-engineering the schema (R22): time-box 3 weeks; fallback = JSONL + sha256 manifest (already proven in V6) with the schema as documentation, upgrade later. Schema churn after P1 (R23): add-only evolution rule, `schema_version` negotiation.

---

### P1. Capture hardening (sandbox, determinism control, completeness metadata, replay) + robustness suite

**Objectives.** Convert "execute and hope" into a trustworthy observation layer: (1) real isolation for untrusted code, (2) determinism control with an explicit report of what was controlled, (3) every trace carries completeness metadata, (4) any witness replays from the store to an identical canonical trace digest. Target the real-world observation failure (V6 28.5% BugsInPy coverage).

**Dependencies.** P0. Reuses `extraction.py`/`SandboxRunner` behaviour as regression oracle.

**Modules.** `sandbox` (process-per-execution workers; Linux container/nsjail/gVisor profile; macOS dev fallback = Docker; rlimits CPU/AS/NPROC/FSIZE; no network namespace; read-only FS plus tmpfs scratch; seccomp deny-list for exec/socket; wall-clock kill with process-group termination; env scrubbing; secrets never mounted), `capture` (tracer on `sys.monitoring` (PEP 669, Python >= 3.12) with `sys.settrace` fallback; event kinds from section 2; bounded canonical value digester; capped events with explicit truncation flag), determinism control (PYTHONHASHSEED, `random`/`numpy` seeding, frozen clock via injectable time source, fixed locale/TZ, deterministic iteration of sets in value digests, ordering of dict/set repr canonicalised, thread-count pin, stdout/stderr capture, filesystem virtualised, PID/cwd normalised; each control reports applied/failed), nondeterminism detector (k-repeat agreement test with k from prereg, default 5, minimal-diff localisation of the nondeterministic event), `replay` (re-execute witness from store; compare digest), signature handling (typed argument adapters: positional/keyword/default, bound methods, class entry via driver, fixtures for module-level state; reason codes for the 49 "unsupported signature" and 4 "import" classes).

**Data contracts.** `ExecutionPlan`, `Event`, `TraceBundle`, `CaptureManifest`, `WitnessInput`, plus `SandboxProfile` (profile id, mounts, limits, syscall policy hash). Failure reason code enum (frozen, never imputed).

**Unit tests.** Each determinism control individually flips a known-nondeterministic fixture to deterministic and reports status; each sandbox limit kills a hostile fixture (fork bomb, memory bomb, infinite loop, file-fill, network connect attempt, `os.system`, reading `~/.ssh`, writing outside scratch, ptrace/proc probing, signal handler tricks, `sys.settrace` removal by the target, monkeypatching `time`); tracer does not leak events from the harness itself; event digester is stable under dict/set permutation; cap/truncation flags correct; replay equals original for 100 deterministic fixtures.

**Integration tests.** Re-run the V6 extraction protocol through the new capture on 200 sampled V5/V6 programs and compare outcome digests (regression: new capture may differ only with an explained reason code); robustness suite (below) end to end; kill -9 of worker mid-trace yields INSUFFICIENT with reason, not a partial trace presented as complete.

**Robustness suite (named deliverable).** >= 120 fixtures in 8 families: (a) time-dependent, (b) RNG without seed, (c) hash-order, (d) threads/async races, (e) filesystem/env/network reads, (f) C-extension/numpy boundaries, (g) global/module state across calls, (h) hostile/adversarial (above list). Each fixture has an expected capture status. Gate requires correct classification of >= 95% of fixtures and zero sandbox escapes.

**Performance tests / budgets.** Tracing overhead vs native: call/return/branch-level <= 5x median, line-level <= 25x median (PEP 669), <= 60x p95; sandbox cold start (container) <= 2.0 s, warm worker <= 300 ms; per-input capture median <= 2 s, p95 <= 10 s on the dev pool; throughput >= 200 captured executions/s on tiny units with 4 workers; memory <= 2 GB per sandbox, event cap 1,000,000 per trace (cap reached must be flagged); trace storage compressed <= 40 B/event; determinism check (k=5) cost <= 5x single capture, with adaptive early-stop at first disagreement.

**Scientific validation.** K2 activation census (week ~6): measure on the contaminated DEV pool (>= 150 BugsInPy-style pairs) replay-only and crude-random activation and determinism. Measurement-validity study: repeat each capture on a second machine/OS image; digest agreement >= 99% for pairs labelled deterministic (cross-environment reproducibility). Report the new coverage vs V6's 28.5% with reason-code breakdown.

**Completion criteria (G1).** Robustness suite passes; zero escapes in the hostile family; replay identical for 100% of deterministic fixtures across 20 repeats; coverage on the DEV real pool >= 70% of runnable pairs with deterministic capture (target; < 50% triggers K2 pivot); per-trace CaptureManifest present for 100% of bundles; performance budgets met or each exception recorded with rationale.

**Risks and fallback.** PEP 669 availability/behaviour differences (R10): fallback `settrace`, accept higher overhead budget (x2). Seccomp/gVisor unavailable on dev macOS (R12): all untrusted execution runs in Linux containers only; macOS native execution of untrusted code is forbidden by policy. Determinism control cannot cover C-extensions/threads (R09): classify as INSUFFICIENT with reason code rather than control it; narrow scope statement. Overhead blowout: drop to call-level capture plus selective line capture inside changed regions only (valid because the research question is about changed-region behaviour).

---

### P2. Static context + alignment

**Objectives.** Provide the minimal static layer: AST/CFG per function, signature extraction, changed-region computation between old/new, and a statement-level alignment seeded by anchors (signatures, call sites, return statements) with explicit unmapped regions. Static context also feeds exploration (P4) with branch conditions and constants.

**Dependencies.** P0 schema. Parallel to P1; dynamic anchors arrive in P3.

**Modules.** `static` (ast normaliser, CFG builder, call graph intra-module, constant/literal pool, branch-condition extractor, signature/type-hint reader), `align` (tree-diff, e.g. GumTree-style top-down/bottom-up matching implemented minimally or wrapping a vetted library; CFG-node mapping; rename/move/extract-function handling with confidence; behaviour-preserving transformation catalogue to test false divergences: rename, reorder independent statements, extract/inline function, loop rewrite).

**Data contracts.** `ChangedRegion` list, `AlignmentMap` (node map, confidence, unmapped), `StaticContext` (CFG hash, branch conditions, literals).

**Unit tests.** AST/CFG golden outputs for 60 syntactic-form fixtures (comprehensions, try/finally, with, match, decorators, async, lambdas, generators); alignment unit tests: identity maps 100%; rename-only alignment 100% and zero changed regions after normalisation; known edits produce the expected region; property test: align(a,b) then align(b,a) consistent within 2%.

**Integration tests.** Alignment on 300 DEV pairs from V5 variants and real BugsInPy diffs; compare changed-region sets with the VCS diff hunk set (agreement metric); refactoring corpus (>= 100 behaviour-preserving transformations, independent of the V5 generator) yields correct mapping >= 90% of nodes.

**Performance tests / budgets.** AST+CFG for a 5k-LOC module <= 2 s; alignment <= 1 s per function pair at 500 AST nodes, <= 10 s at 5k nodes; peak memory <= 500 MB.

**Scientific validation.** Alignment quality against a hand-aligned gold set (60 pairs, 2 annotators): node-level F1 >= 0.90, unmapped-region precision reported. Ablation recorded: seeded-by-anchors vs static-only (decides whether dynamic anchors are worth it in P3).

**Completion criteria (G2).** Fixtures pass; F1 >= 0.90 on gold; budgets met; deterministic outputs (hash-stable).

**Risks and fallback.** Alignment fails on heavy refactors (R14): flag low-confidence regions and let the verdict degrade to INSUFFICIENT (reason `alignment_low_confidence`) rather than compare misaligned traces. Fallback to function-level alignment (compare only at call/return boundaries). Python-specific dynamism (decorators, metaprogramming) (R15): declare unsupported-constructs list, count them in coverage report.

---

### P3. Divergence/localisation, sufficiency, three-valued verdict on synthetic controlled suites

**Objectives.** Implement the verdict engine and test it where ground truth is controllable. Validate soundness of DIVERGENT_OBSERVABLE, validate localisation, define and measure sufficiency levels, and run the first honest version of K4 against baselines.

**Dependencies.** P1 (traces, replay), P2 (alignment). Baseline harness from P0/P1.

**Modules.** `diverge` (output/exception/side-effect comparator with declared observation points; first-divergence along aligned event sequences; per-view comparator interface limited to control-flow + call + returned-value digests in P3; localisation = first-divergence locus mapped back to changed region), `sufficiency` (activation, distinct-path counting, budget accounting, S0-S3 assignment, calibration table: for each S, empirical miss rate on known-divergent pairs), `verdict` (decision rules, reason codes, evidence chain assembly, witness minimisation by delta-debugging on inputs within budget), `eval` (baseline runners: plain output differential at same budget, coverage-guided differential fuzzing with off-the-shelf engine such as Atheris/Hypothesis-coverage wrapper, conventional features, V5, V6).

**Synthetic controlled suites (independent construction).** Suite A: behaviour-preserving transformations (negatives; >= 400 pairs, 10+ transformation families, none shared with the V5 mutator code). Suite B: output-visible divergences (positives; >= 400). Suite C: masked divergences (state differs, output equal on default inputs, an explicit revealing input exists by construction; >= 300), including internal-only differences which are intentionally NOT behaviour changes (>= 100, "benign internal change" negatives) to measure the DIVERGENT_INTERNAL_ONLY false-alarm rate. Suite D: nondeterminism-injected negatives (>= 150). Suite E: unobservable-by-default (changed region needs a rare input; >= 150) to calibrate sufficiency. Generation spec stored and hashed; generator fingerprint audit: a GBM on syntactic features must score <= 0.60 AUROC leave-family-out, else regenerate (V6 lesson).

**Data contracts.** `DivergenceRecord`, `SufficiencyReport`, `Verdict`, synthetic-suite manifest with the construction ground truth (which input reveals the divergence, why masked).

**Unit tests.** Comparator on hand-built traces (equal, first-diverge, length mismatch, exception parity, truncated trace -> INSUFFICIENT not DIVERGENT); decision table exhaustively tested (every combination of {activation, determinism, alignment confidence, outputs equal/different, truncation}); minimiser preserves divergence; localisation exact on Suite B/C.

**Integration tests.** Full pipeline on each suite; replay-confirmation: every DIVERGENT_OBSERVABLE re-executed in a fresh sandbox, k=3; invariance tests (pair order swap yields symmetric verdict, with locus mirrored).

**Performance tests / budgets.** Compare two traces of 100k events <= 5 s; first-divergence early exit (diverging at event i costs O(i)); full pair verdict (given cached traces) <= 10 s median; end-to-end pair at default budget (60 s exploration excluded) <= 30 s; evidence bundle per pair <= 50 MB p99.

**Scientific validation.** (1) Soundness: false DIVERGENT_OBSERVABLE on Suites A and D <= 1.0% (upper 95% CI <= 2%); witness replay confirmation >= 99.5%. (2) Localisation: first-divergence locus within the changed region on >= 95% of Suite B/C. (3) Sufficiency calibration: monotone decreasing miss rate across S1 -> S3 on Suite E with the calibration table. (4) K4 first read: state/trace divergence vs output differential on Suite C and dev real subset at equal budget with program-cluster bootstrap, paired; baselines' numbers frozen first. (5) Shortcut controls: edit-size-only, token distance, generator-fingerprint features evaluated on the same suites, reported next to V7 (V6's edit-size reversed 0.771/0.847).

**Completion criteria (G3).** All soundness thresholds met; DIVERGENT_INTERNAL_ONLY false-alarm rate on benign-internal negatives reported (expected high; if > 30% at S>=2 the class is demoted to diagnostic-only, not a verdict); K4 interim recorded in the claim ledger (pass or not).

**Risks and fallback.** Synthetic suites circular (R05): independent generator code, audit above, and treat synthetic results as unit evidence only (no headline). Internal divergence is dominated by benign refactoring (R04): then DIVERGENT_INTERNAL_ONLY is dropped; V7 reduces to output-differential plus sufficiency. First-divergence noise from legitimate refactors: alignment-aware comparison and equivalence-class abstraction of values (P5 may refine).

---

### P4. Adaptive exploration (replay -> structure-aware/property-based -> changed-region-directed)

**Objectives.** Raise activation (the dominant real-world failure) without labels. Three stages, each independently gated, each reusing the verdict engine unchanged.

**Dependencies.** P1, P2 (changed regions, branch conditions, literals), P3 (verdict core to measure detection and sufficiency).

**Modules.** `explore` with a scheduler and three generators behind one interface `propose(budget_state, static_ctx, coverage_state) -> WitnessInput`:
- Stage 1 Replay: harvest inputs from existing tests/docstrings/doctests/examples/callers within the repo; normalise signatures (P1 adapters). Deterministic, no labels.
- Stage 2 Structure-aware/property-based: type-hint and signature-driven generators (Hypothesis-style strategies), literal-pool seeding from static context, boundary values, mutation of replay inputs, grammar for container shapes.
- Stage 3 Changed-region-directed: coverage-feedback (branch coverage inside changed regions of both versions), distance-to-changed-region heuristics from CFG, selective scheduling toward uncovered changed branches; optional concolic/symbolic assist limited to hard branch conditions (feature-flagged, off by default; invoked only if K3 passed and budget remains).
Budget accountant shared with baselines (same execs, wall-clock, events).

**Data contracts.** `WitnessInput` provenance by stage, `ExplorationLog` (per-input new coverage, time), `BudgetState`. Seeds recorded; whole run reproducible from `(seed, plan)` (scheduler must be deterministic given seed; parallel workers merge in a canonical order).

**Unit tests.** Each generator respects type hints/signatures (>= 95% type-valid inputs where hints exist); scheduler deterministic under seed; budget never exceeded by > 5%; stage ordering (earlier stage inputs always retained); directedness test on a synthetic CFG with a guarded changed branch (directed stage reaches it with <= 20% of the execs the undirected stage needs on average over 50 seeds).

**Integration tests.** Per-stage end-to-end on Suite E, dev real pool, and a hostile-input run (generators must not produce inputs that escape the sandbox policy; inputs capped in size).

**Performance tests / budgets.** Default budget per pair: 60 s wall-clock, 4 cores, <= 5000 executions (K3 numbers measured at this budget); also a low budget (10 s) and high (300 s) for curve reporting; scheduler overhead <= 10% of wall-clock; >= 200 exec/s on tiny units; coverage-feedback overhead <= 30%.

**Scientific validation.** Activation-vs-budget curves per stage (the main figure), with replay, crude-random, and coverage-guided-differential-fuzz baselines on identical budgets; effect on verdict distribution (INSUFFICIENT share) and on detection recall; ablation per stage; stage 3's marginal contribution over stage 2 (decide whether concolic is ever turned on). K3 check after stage 2; K4 re-read after stage 3.

**Completion criteria (G4).** K3 passed (or pivot executed); each retained stage shows a paired CI lower bound > 0 for marginal activation gain, else removed; reproducibility (same seed same trace digests, 3 repeats, 2 machines); no sandbox policy violation from generated inputs.

**Risks and fallback.** Exploration cannot raise real-world activation (R02, the central technical risk): stop at K3, ship replay + crude generation + honest INSUFFICIENT. Property-based inputs unrealistic so divergences are spurious (R16): require witness realism filter (inputs must satisfy documented preconditions where known; flag otherwise `unrealistic_input_risk`, report separately). Nondeterminism amplified by weird inputs: reuse P1 detector, classify not guess.

---

### P5. State/invariant + multi-view projections (CONDITIONAL on K4)

**Objectives.** Only if K4 shows state/trace divergence beats output differential: add state abstraction, simple relational invariants (e.g. x <= y, len preserved, monotonic, return-in-range, via Daikon-style templates mined per version, diffed across versions), and derived views (CFG path, call graph, data-dependence, state-transition system) as deterministic projections of the event log.

**Dependencies.** P3, P4, K4 pass. Ablation design must be pre-registered before building (which view, which expected gain).

**Modules.** `state` (value abstraction: type-class, sign, size bucket, set-of-seen-types; invariant template miner with minimum-support rules; invariant diff), `views` (projection functions event log -> view; each view hashed from the log hash so views are never stored truth; view comparators plugged into `diverge`).

**Data contracts.** `ViewSpec` (version, projection id, parameters), `InvariantSet`, `ViewDiff`. Views are regenerable; store only their hash and spec.

**Unit tests.** Projection determinism and idempotence; invariant miner recovers planted invariants on synthetic programs (precision/recall >= 0.9 at stated support); invariants with insufficient support are dropped not guessed; abstraction soundness test (abstract equal implies concrete equal within the abstraction).

**Integration tests.** Views regenerate bit-identically from the store; end-to-end verdicts with and without each view on suites.

**Performance tests / budgets.** Projection of 100k events <= 3 s per view; invariant mining on 10k states <= 30 s; total P5 overhead per pair <= 25% of P3 pair cost; memory <= 1 GB.

**Scientific validation.** Ablation lattice: {output only, +control-flow, +call, +value digests, +state abstraction, +invariants, +all views} at equal budget; each addition retained only if paired CI for recall or false-assurance reduction excludes 0 with minimum effect +2 pp (pre-registered); complexity penalty (kept only if cost <= 25%). Overfitting control: choose view set on DEV, freeze, evaluate once on holdout.

**Completion criteria (G5).** Retained view set justified by ablation; unjustified views deleted, not just disabled; documentation of which hypotheses failed.

**Risks and fallback.** Ablation shows no view adds value (R04): delete P5; V7 = P3+P4 (this is an acceptable and publishable negative result). State abstraction too coarse/fine (R17): parametric sweep on DEV with the choice frozen pre-holdout.

---

### P6. Impact analysis (CONDITIONAL)

**Objectives.** From the first divergence, propagate observed dependencies forward (dynamic dependence along the trace) to list affected outputs/state/callers, labelled "observed dependency, not causal proof". Provide a narrow, useful product feature, not a research claim.

**Dependencies.** P3 (first-divergence), P2 (CFG/call), optionally P5 views.

**Modules.** `impact` (dynamic data/control dependence tracking on the event log, slice computation, affected-callers list from static call graph intersected with traces, severity bucket: output-visible / state-only / unobserved).

**Data contracts.** `ImpactRecord` (seed divergence, dependence edges with evidence event ids, reached outputs, truncation flags).

**Unit tests.** Slice correctness on hand-built programs with known dependence (data, control, aliasing via containers); slice over-approximation bound stated; truncation flagged.

**Integration tests.** On Suite B/C: impact set contains the true affected outputs (recall >= 0.9) and the seed locus; precision measured against hand-labelled impact on 60 pairs (target >= 0.6, otherwise labelled low-confidence).

**Performance tests / budgets.** Slice over 100k events <= 10 s; memory <= 1.5 GB; disabled by default in K4 evaluations so it cannot inflate the main metric.

**Scientific validation.** Hand-labelled impact gold set (2 annotators, kappa >= 0.6); comparison against a plain static call-graph reachability baseline for impact (does dynamic observation add precision?).

**Completion criteria (G6).** Precision/recall reported with CIs; documented as advisory; excluded from headline claims unless it beats the static baseline by >= 15 pp precision at equal recall.

**Risks and fallback.** Scope creep and over-claiming "causal" (R24, R25): wording is enforced by schema (`kind: observed_dependency`). Fallback: ship only affected-outputs list.

---

### P7. Independent benchmark construction + adjudication

**Objectives.** Produce an evaluation set that does not share generators, labels, or program clusters with V5/V6, with a sealed holdout. This is the programme's largest non-code effort. P7a (weeks 1-8): protocol, sourcing, pilot, hash-commit the holdout. P7b (weeks 8-29): adjudication and QA.

**Dependencies.** P0 for 7a. No dependence on tool outputs (labels must be tool-independent).

**Modules.** `bench` (source miners, environment builders per project with locked dependencies, unit-level entry harness, adjudication UI/CLI, label-provenance registry, leakage auditor (cluster dedup via normalised AST hash plus near-duplicate detection, project-level split, generator-fingerprint probe, output-oracle leak audit ported from `output_oracle_leak_audit.py`), power calculator).

**Sources (stratified, each stratum reported separately).**
1. Real defects: BugsInPy-style bug-fix pairs from >= 15 projects NOT in the V6 external set where possible (new projects), Defects4J-style for later Java, plus real regressions mined from project histories (pre/post commit pairs with an accompanying regression test as independent evidence).
2. Real behaviour-preserving changes: refactoring commits validated by full test-suite pass and by adjudication.
3. Real masked-divergence cases: commits where the change is not visible to existing tests but is later fixed/reverted (the interesting stratum; expected scarce, target >= 30).
4. Competition/benchmark variants (QuixBugs-style) kept as a separate, labelled "toy" stratum.
Mutation-generated pairs are excluded from the confirmatory holdout (V6 label = f(generator) problem); permitted only in the P3 synthetic suites.

**Label protocol.** Label units: (old, new, scope) with label in {behaviour-preserving, behaviour-changing, unclear}. Evidence for behaviour-changing: failing/passing test pair, adjudicator-written revealing input, or documented spec change. Evidence for behaviour-preserving: refactoring commit plus passing suite plus adjudicator review, never "no tool found a difference" (circularity). "Unclear" pairs are kept and scored as a separate class, not dropped silently. Two adjudicators independently on 25% (kappa >= 0.70), disagreements resolved by a third; adjudicators blind to all tool outputs; adjudication instructions versioned.

**Data contracts.** `BenchmarkPair`, `AdjudicationRecord`, `LeakageAuditReport`, `HoldoutCommitment` (hash of pair ids + labels published in P0 store; labels sealed in an offline encrypted archive held by a non-developer custodian).

**Unit tests.** Env builder reproducibility (rebuild twice equal hash); dedup (planted near-duplicates found >= 98%); split invariants (no project crosses dev/holdout); label schema validation.

**Integration tests.** Dry run: a pilot of 50 pairs adjudicated end to end including kappa computation; leakage auditor run on the contaminated V6 data to confirm it catches the known 596 duplicate groups (calibration of the auditor).

**Performance tests / budgets.** Environment build <= 20 min per project (cached afterwards); full benchmark replay <= 24 h on the reference 16-core node; adjudication throughput target >= 6 pairs per adjudicator-hour (budget 200+ pairs = about 70 adjudicator-hours with double-labelling).

**Scientific validation.** Power analysis frozen before sealing: with 200 pairs (>= 60 divergent) detect a +10 pp paired recall difference at alpha 0.05 with power >= 0.8 only if discordant pairs >= ~40; if not achievable, record it and downgrade P8 claims to exploratory. Label-noise estimate via re-adjudication sample; noise sensitivity analysis (flip 5%/10% labels) reported with the headline.

**Completion criteria (G7 and K5).** Holdout sealed; leakage audit clean; kappa >= 0.70; sample sizes met; dev set separately frozen; everything hash-committed before P3 tuning begins (only the commitment is early, adjudication may finish later).

**Risks and fallback.** Not enough real masked cases (R06, R07): K1 pivot; smaller real set plus honest negative-power statement. Adjudication cost overruns (R08): cut sample to the minimum power set, drop strata (toy first). Label disputes about "behaviour": always adjudicate relative to a stated scope and spec; ambiguous -> unclear class.

---

### P8. Sealed-holdout evaluation

**Objectives.** One confirmatory run of the frozen system against all frozen baselines on the sealed holdout, with pre-declared claims reported exactly as pre-registered, including negative outcomes.

**Dependencies.** P3/P4 frozen (and P5/P6 if retained), P7 complete, K5 pass, prereg hash unchanged.

**Modules.** `eval` (single-run orchestrator, unseal procedure with custodian, claim-evidence matrix generator, paired cluster bootstrap by project/program cluster, permutation tests, multiple-comparison correction (Holm) across the pre-declared claim set, calibration (ECE/reliability of sufficiency levels), abstention coverage-vs-error curves, failure analysis template).

**Data contracts.** `HoldoutRunManifest` (system hash, baseline hashes, environment image digests, prereg hash, unseal log), `ClaimLedger` final.

**Unit tests.** Orchestrator refuses to run if any frozen hash mismatches, if holdout was accessed earlier (access log), or if a second unseal is requested; dry run on a decoy holdout of the same format.

**Integration tests.** Full rehearsal on a rehearsal split built from dev data with the identical pipeline (never the holdout); from-raw reproduction of the final tables (as in V6: bit-identical).

**Performance tests / budgets.** Whole holdout (>= 200 pairs, default exploration budget) <= 12 h wall on 16 cores; per pair <= 120 s median, <= 300 s p95; peak storage <= 200 GB.

**Scientific validation.** Primary metric as pre-registered (recommendation: detection recall at matched false-DIVERGENT rate <= 1%, plus false-assurance rate at S>=2, with abstention coverage reported); secondary: time-to-detection, INSUFFICIENT share, calibration; strata reported separately (real defect, refactor, masked, toy). Baselines: plain differential at equal budget, coverage-guided differential fuzz, conventional features, V5, V6. Negative or null results are reported equally.

**Completion criteria (G8).** Holdout run once; claims classified SUPPORTED / NOT SUPPORTED / INCONCLUSIVE per pre-declared rule; any deviation documented; artefacts hashed.

**Risks and fallback.** Holdout result disappoints (R18): publish as is; no re-tuning; a failed holdout may motivate a new, separately sealed holdout for a V8, never reuse. Environment drift between dev and holdout (R20): container digests pinned.

---

### P9. Optional: prediction layer (P9a) and formal tier (P9b)

**P9a Prediction layer (J).** Objective: a calibrated selective predictor on top of V7 evidence for the cases where evidence is insufficient (not replacing the verdict). Dependencies: P8 complete; trained only on DEV and an additional dev-grade pool; must be evaluated on a SECOND sealed holdout (the P8 one is spent). Modules: small linear/GBM models only, features = V7 evidence summaries; no GNN/LLM dependency. Tests: leave-project-out and leave-generator-family-out; shortcut controls (edit size, fingerprint). Budget: <= 50 ms inference. Validation: must beat the shortcut features by a pre-stated margin (AUROC +0.05, CI > 0) on leave-project-out, else not shipped. Completion: shipped as advisory with calibration, or dropped. Risk R19: repeats V6 (conventional-feature parity); fallback: drop.

**P9b Formal tier.** Objective: a bounded symbolic / regression-verification check for small pure units, the only place the word "equivalent" may appear ("equivalent up to bound B for scope S"). Spike (2 ew) after P3, full (3-6 ew) after K4. Modules: `formal` (translate a restricted Python subset to SMT, bounded loop unrolling, CrossHair/Z3 wrappers; timeouts; result in {EQUIV_BOUNDED, COUNTEREXAMPLE, UNKNOWN}). Tests: planted equivalent/inequivalent pairs (>= 200 small units); counterexamples must replay in the P1 sandbox (cross-check of the two tiers). Budgets: <= 30 s per unit, supported subset coverage reported (expected small, <= 25% of real pairs; stated, not hidden). Completion: soundness (zero EQUIV_BOUNDED on known-inequivalent in the planted set) and coverage documented. Risk R21: coverage too small to matter; fallback: keep as an oracle for building benchmark labels only.

---

## 6. Parallelism map

```
week:   1      4      8        16        24        29     32   40
E1      P0 ---- P1 capture ---------- K2(w6) ---> P4 stage1..3 (w17-29) -> P8
E2      (P0)    P2 static/align ---- P3 verdict+suites (w9-16) -> K4 -> P5 (w30-37, if K4) 
E3      P7a ----- K1(w4) ---- P7b adjudication (w8-29) ------- K5 ---------- P6 (if funded)
Stat    prereg(w3) ........ baseline freeze (w8) ........ power analysis ........ P8 analysis
```

Parallel sets: {P1, P2, P7a}; {P3, P7b}; {P4, P7b, P9b spike}; {P5, P6}. Serial: P0 -> P1 -> P3 -> P4 -> K4 -> P8.

## 7. Exact implementation order (numbered, each step ends with an artefact check)

1. P0.1 Create `v7/main` branch, protect V6 tag, copy contamination registry (V5/V6 marked `contaminated_dev`).
2. P0.2 Write and hash `prereg_v7.json` draft (equal-budget definition, baselines, K1-K5 thresholds, primary metric, claim list). Stats review.
3. P0.3 Contract schemas v1.0 and canonical serialiser with golden vectors.
4. P0.4 Content-addressed immutable store and `verify`; reproduction smoke test on V6 data.
5. P0.5 Evaluation stats port (cluster bootstrap, permutation, Holm) and null-baseline run through the store. G0.
6. P7a.1 (parallel from week 1) Benchmark protocol, adjudication instructions, source list, pilot of 50-100 pairs, env builder. K1 at week 4.
7. P1.1 Verify actual isolation of `SandboxRunner` (read-only audit); if unsafe, mark untrusted-code execution forbidden outside the new sandbox.
8. P1.2 Sandbox worker + hostile fixtures (R-safety first; no further capture work until hostile suite passes).
9. P1.3 Tracer on PEP 669 with event schema and caps; overhead measurement.
10. P1.4 Determinism controls + nondeterminism detector + completeness manifest.
11. P1.5 Signature adapters and reason codes (the 49 + 4 classes), replay.
12. P1.6 K2 activation census on DEV pool (replay + crude random). Decision.
13. P1.7 Robustness suite complete; cross-machine reproducibility check. G1.
14. P2.1 (parallel with P1.3 onward) AST/CFG + signature + changed regions; P2.2 alignment; refactor corpus and gold set; G2.
15. P3.0 Freeze baselines (plain differential, coverage-guided differential fuzz, conventional features, V5, V6) with a baseline-freeze hash. Prereg hash must predate any V7 number.
16. P3.1 Synthetic suites A-E generated from independent spec; fingerprint audit.
17. P3.2 Comparator, first-divergence, localisation.
18. P3.3 Sufficiency (activation, S-levels) and verdict decision table.
19. P3.4 Witness minimisation and replay confirmation.
20. P3.5 First K4 read; calibration table. G3.
21. P4.1 Stage 1 replay harvest; P4.2 Stage 2 structure-aware/property-based; K3 decision.
22. P4.3 Stage 3 directed (if K3 passed); concolic only if justified by stage 3 marginal gain.
23. P4.4 K4 second read with full explorer. G4. DECISION: go to P5/P6 or go straight to P8 with the smaller claim.
24. P7b.1 Adjudication complete; leakage audit; power analysis; K5. G7.
25. P5.1 (only if K4 pass) ablation pre-registration, then state abstraction, invariants, views; G5. P6 in parallel if funded; G6.
26. P9b spike may run any time after step 20.
27. P8.1 Freeze everything (system hash, baselines, env digests), rehearsal on a dev-derived split, from-raw reproduction check.
28. P8.2 Unseal once, run, analyse exactly per prereg, publish ledger. G8.
29. P9a only after step 28, with a second sealed holdout. P9b full if justified.
30. Java/C adapter work (section 9) only after step 28, as a separate programme with its own gates.

## 8. Performance budget summary (single table)

| Item | Budget |
|---|---|
| Trace overhead (call/branch level; line level) | <= 5x; <= 25x median (<= 60x p95) |
| Sandbox start (container cold; warm worker) | <= 2.0 s; <= 300 ms |
| Capture per input (median; p95) | <= 2 s; <= 10 s |
| Capture throughput small units, 4 workers | >= 200 exec/s |
| Per-trace event cap; memory per sandbox | 1M events; 2 GB |
| Store write; storage | >= 50k events/s; <= 40 B/event compressed |
| AST+CFG 5k LOC; alignment 500 nodes | <= 2 s; <= 1 s |
| Compare 100k-event traces; pair verdict from cache | <= 5 s; <= 10 s |
| Exploration default budget | 60 s, 4 cores, <= 5000 execs; scheduler overhead <= 10% |
| End-to-end pair (default budget) | median <= 120 s, p95 <= 300 s |
| P5 added cost; impact slice 100k events | <= 25%; <= 10 s |
| Holdout full run | <= 12 h on 16 cores |

## 9. Java/C adapter policy (design-for, claim-nothing)

- The `Event`/`TraceBundle`/`CaptureManifest`/`Scope` contracts carry no Python concepts (symbol ids are language-qualified strings; value digests are over a language-neutral canonical value model: null, bool, int, decimal string, string, bytes, sequence, map, record, opaque-with-type-name).
- Adapter interface (replaces `sbgv6.observe.Adapter`): `capabilities() -> {events, value_depth, determinism_controls, sandbox_profile}`, `prepare(version, scope)`, `execute(plan, input) -> TraceBundle`, `replay(bundle) -> digest`. Capabilities are declared per adapter and surface in `CaptureManifest`; analysis modules must degrade (INSUFFICIENT) when a needed capability is absent.
- Conformance suite (P1 deliverable): golden trace corpora and a language-neutral `trace_conformance` test that any adapter must pass (schema validity, ordering, determinism report, truncation flags).
- Rule: no document, table or abstract may state a result for Java or C until (a) the adapter passes conformance, (b) the robustness suite is ported, (c) a language-specific benchmark of >= 100 adjudicated pairs exists, and (d) results meet the same prereg procedure. Until then, outputs are labelled "Python only; Java/C: contract only". The existing `benchmark/cross_language` (10 programs) and `external/quixbugs_java` are smoke fixtures, not evidence.

## 10. Reproducibility and governance rules applied in every phase

- Every number in a report is regenerated from the store by a script whose hash is in the manifest (from-raw reproduction check at each gate).
- Seeds, interpreter version, OS image digest, dependency lock hash are in every `ExecutionPlan`.
- Hypotheses, metrics, K thresholds only change through dated amendments with justification; holdout access is logged.
- Dev results are never described as confirmatory; V5/V6 data are described as contaminated dev.
- Every phase ends with a written gate review listing: criteria met/unmet, deviations, risk register updates.
