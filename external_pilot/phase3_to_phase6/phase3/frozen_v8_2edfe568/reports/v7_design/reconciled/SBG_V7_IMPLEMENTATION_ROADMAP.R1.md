Reconciled version R1 of SBG_V7_IMPLEMENTATION_ROADMAP.md; original preserved at reports/v7_design/_original_archive/

# SBG V7 Implementation Roadmap, R1

Status: documentation only. Authority: `reports/final/V7B_FROZEN_SPEC.md` (FS, especially s12 gates and s13 authorised scope) > `P0_BINDING_DECISIONS.md` (D1-D11) > this file. Gates are G0-G8 and checkpoints K1-K5 only (D9; CM G-01, K-01); the original G0-G9 numbering is retired. This roadmap **does not authorise anything**: every item marked "Phase 3, not started" needs explicit authorisation by the programme owner and is not implied to have been done.

## 1. Programme phases (R1 vocabulary)

Three vocabularies existed: the original design phases P0-P9, the frozen spec's "P0/P1", and the programme phases below. R1 fixes the programme phases and keeps the original P0-P9 only as workstream labels (section 3).

| Programme phase | Content | Status |
|---|---|---|
| **Phase 1** | Build and test the V7-B core (`sbgv7/`), development-only feasibility spike and baselines on existing non-pristine data, exploratory statistics, independent red-team review, readiness report, README/docs checks, closure | **Done** (`reports/final/PHASE_1_FINAL_CLOSURE_REPORT.md`: PASS_WITH_LIMITATIONS; readiness verdict B) |
| **Phase 2** | Reconciliation and audit: closing document debt O13 (this R1 set, changelog, index), spec-conformance audit (`reports/phase2/PHASE_2_SPEC_CONFORMANCE_AUDIT.md`, written separately). Documentation only: no change to `sbgv7/`, `tests/`, `results/`, V5/V6 files, `_original_archive/` or the original `SBG_V7_*.md` | **In progress** (this document set) |
| **Phase 3** | Gated infrastructure and benchmark work: Linux/container isolation passing I1-I7, feasibility spike on about 30 candidate projects, K1/K2 evaluation, then (only if gates pass) exploration, like-for-like and published-tool baselines, independent benchmark and adjudication, K5, sealed evaluation | **Phase 3, not started; not authorised** |

What Phase 1 did not achieve against FS s13 authorised scope: (1) Linux container isolation with I1-I7 passing (Docker daemon was down; macOS `sandbox-exec` verified only for network and write denial; `RLIMIT_AS` and `RLIMIT_NPROC` not enforced; reads unconfined; `setsid` escape untested); (2) the feasibility spike on about 30 real candidate projects (the dev spike used QuixBugs, BugsInPy extracted units on synthetic inputs, and synthetic pairs); (3) K1/K2 evaluation as defined (K1 NOT MET on development data; K2 indicative only). These carry into Phase 3 unchanged.

## 2. Phase 3 plan (gated; nothing here has been started)

Entry conditions (all required, none yet met): explicit written authorisation; Phase 2 conformance-audit findings triaged (each OI-nn closed, accepted or deferred with a reason); a Linux container host available (Docker or equivalent) and a security review owner (R11, R12); a frozen config snapshot and hashed candidate list. Steps in order; a later step does not start until the earlier gate result is recorded.

| Step | Work | Gate | Failure response (FS s12; no renegotiation) | Status |
|---|---|---|---|---|
| 3.1 | Build the isolation runner for Linux containers; pass I1-I7 as pass/fail checks; hostile-fixture suite, zero escapes, no stray processes (hard G1 gate, CM M-05) | I1-I7 + containment | Unverified property gives `sandbox_failure`; unresolved escape after one remediation cycle: halt external-code execution (RISK S4) | Phase 3, not started |
| 3.2 | Measure per-run limits and tracing overhead on the target platform (targets: <= 5x call/branch, <= 25x median line; limits provisional per FS s11); freeze them in `SandboxPolicy` | before K2 | n/a | Phase 3, not started |
| 3.3 | Feasibility spike on about 30 candidate projects (2-3 weeks per FS s13): build success, drivable fraction, input-representation coverage (object arguments, tuples/sets), determinism, replay activation | feeds K1/K2 | n/a | Phase 3, not started |
| 3.4 | **K1** real-pair feasibility: >= 100 runnable real pairs from >= 8 projects, project-level under D10 isolation | K1 | **STOP** | Phase 3, not started (dev-data count: 74 runnable real pairs, 1 true project plus 44 units on synthetic inputs, so K1 "NOT MET on development data"; not an evaluation of K1 as defined; OI-21) |
| 3.5 | **K2** on the K1 pairs under D10 isolation: determinism-confirmed >= 70% and replay+crude activation >= 35% | K2 | one redesign of B (<= 4 weeks); second failure **STOP** | Phase 3, not started (dev-data census indicative only) |
| 3.6 | **K3** exploration lift (explorer module A built only after K2 passes; no K3+ work before): activation >= 60% and >= +15 points over replay, lower 90% bound > 0 | K3 | **PIVOT** to replay + structure-aware exploration, no directed-exploration claim | Phase 3, not started |
| 3.7 | **K4** core thesis: FAR(V7) below both like-for-like comparators at matched decided coverage >= 0.60, lower 90% cluster-bootstrap bound > 0 and >= 10pp, at 60 CPU-s; comparators B1/B2 get the same diff-derived information or V7 is also run diff-blind (D7, D11) | K4 | **PIVOT** to V7-B' (sufficiency-aware differential testing, no explorer/impact/state, no novelty claim beyond the evaluation protocol); V7-B' no better than B1: **STOP** | Phase 3, not started |
| 3.8 | **K5** benchmark readiness: >= 60 projects, >= 250 independent divergent pairs, >= 20 mixed-class projects, kappa >= 0.7, clean leakage audit, hash-committed manifests, custodian | K5 | **DOWNGRADE**: no confirmatory evaluation, exploratory report only | Phase 3, not started |
| 3.9 | Optional, never a precondition: V7-A pilot (module E, <= 12 weeks, +10pp, authored suites, independent reference state-dump tool) only after V7-B shows headroom | G-pilot | n/a | Not authorised |

K thresholds are UNVALIDATED defaults carried from the original roadmap where D9 gave a response but no number (K2 70%/35%; O9). K3-K5 are consequences of FS s12 and are not run before K2 passes. Sealed-holdout unseal follows K5 and G5-G7 of `SBG_V7_VALIDATION_AND_ACCEPTANCE_GATES.R1.md`, one shot.

## 3. Original phases P0-P9 as workstreams: disposition

"As-built" is per `docs/architecture/V7B_IMPLEMENTATION.md` and the Phase 1 reports; not independently re-verified here.

| Orig. | Workstream | R1 disposition | Programme phase / status |
|---|---|---|---|
| P0 | Governance, freeze, schema, immutable store | Frozen spec and R1 set replace the "freeze in P0" target. Store = content-addressed records + hash-chained JSONL (no SQLite/CAS/Merkle). Seal timing: hash-commit of project list and pair ids at G0, labels sealed after adjudication (CM X-14) | Phase 1/2 (documents done; store partial, OI-03/OI-04) |
| P1 | Capture hardening: sandbox, determinism, completeness, replay | Isolation reduced to I1-I7 (FS s10); legacy runner `v6_compat` only | macOS part done (Phase 1); Linux/container **Phase 3, not started** |
| P2 | Static context and alignment | C minimal; G not built; `alignment_failed` only on parse failure | Minimal done; rest Phase 3, not started (and G never affects verdict value) |
| P3 | Divergence, sufficiency, three-valued verdict, controlled suites | Core implemented S1/S2; S3 refused (`s3_enabled=false`); independent synthetic suites with fingerprint audit not built | Core done (Phase 1); calibration and independent suites Phase 3, not started |
| P4 | Adaptive exploration (3 stages) | Module A not implemented; gated by K2 then K3; no K3+ work before K2 passes | Phase 3, not started |
| P5 | State/invariant + multi-view (conditional on K4) | Optional V7-A pilot only (module E); F removed | Not authorised |
| P6 | Impact analysis (conditional) | Optional/advisory; `ImpactSet` optional in chains | Not authorised |
| P7 | Independent benchmark and adjudication (P7a protocol/sourcing/seal, P7b adjudication/QA) | EP R1 and K5 govern; must add truth harness / H-M authoring / H-P (CM X-01, E-01) | Phase 3, not started |
| P8 | Sealed-holdout evaluation | One shot after K5 and G5-G7; holdout cost 292-875 CPU-h (up to about 1750 with diff-blind arms) budgeted explicitly (D7) | Phase 3, not started |
| P9 | Optional prediction layer (J) and formal tier | J off; formal tier optional, separate claim `BOUNDED_EQUIVALENCE_PROVEN`; J margin (+0.03 vs +0.05) unresolved (O12) | Not authorised |

## 4. Contracts, budgets, effort

- Cross-cutting contracts (original s2): superseded by `SBG_V7_DATA_AND_EVIDENCE_SCHEMA.R1.md`. The original verdict list of four values and the original S0-S3 description are retired.
- Budget unit: CPU-seconds summed over all processes including all V7 overhead; grid 10/60/300; headline 60 (FS s11). The original roadmap budget (60 s wall x 4 cores, up to 5000 executions) is retired (CM B-01, B-02). Capture alone at the old 1200-run scale consumes about the whole 60 CPU-s (estimate from the documents' own rates); the feasible input count must be set from Phase 3 measurement.
- Performance table (original s8): all rows are estimates, unmeasured; the per-pair storage bound (50 MB p99), 200 GB cap and 150 CPU-h holdout figure are known to be inconsistent with the original's own arithmetic at default scale (CM B-03, B-04) and are not restated.
- Effort: the original 51 engineer-weeks and 32 calendar weeks (22-48) were found to omit the truth harness, H-M authoring and H-P (CM E-01) and to contain a summing error (E-02: summed range about 32-87). **Effort is not re-estimated in R1 (unreconciled).** Only FS s13 durations are carried: spike 2-3 weeks; one redesign of B <= 4 weeks; V7-A pilot <= 12 weeks.
- Java/C: contract-compatible by design, no claim (original s9; R34). Python only; CPython 3.13.

## 5. Gate placement (G0-G8; from GATES R1 B)

K1 and K2 are exit conditions of G1; K3 of G2; K4 of G3 (first check) and G5 (final check); K5 of G5 before G6. G0 should be split (CM G-02): G0a protocol/store freeze, G0b data custody. **No gate G0-G8 is recorded as passed in the repository documents read for this reconciliation.** Containment (zero escapes) is a hard G1 sub-gate.

## 6. Governance rules (original s10) and risk linkage

Unchanged in intent: all thresholds frozen with hashes before dev results are looked at, changed only through dated amendments on the development split; the K-gate responses are not renegotiated. Risk IDs are `Rnn` in `SBG_V7_RISK_REGISTER.R1.md`; requirement IDs are `R-nn` in the failure-to-requirement matrix (CM G-03; no rename).

## 7. Not done / unreconciled here

Effort re-estimate; whether K1 NOT MET on development data already triggers the D9 STOP (OI-21); calendar for Phase 3; the original s7 "exact implementation order" (artefact checks per step) was not regenerated; parallelism map not redrawn.
