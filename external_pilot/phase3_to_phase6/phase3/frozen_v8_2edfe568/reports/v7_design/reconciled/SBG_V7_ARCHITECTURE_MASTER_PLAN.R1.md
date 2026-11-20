Reconciled version R1 of SBG_V7_ARCHITECTURE_MASTER_PLAN.md; original preserved at reports/v7_design/_original_archive/

# SBG V7 Architecture Master Plan, R1

Status: documentation only (Phase 2). Authority order: `reports/final/V7B_FROZEN_SPEC.md` (frozen spec, "FS") > `p0_reconciliation/P0_BINDING_DECISIONS.md` (D1-D11) > this file. Where this file and the frozen spec disagree, the frozen spec wins. Where the frozen spec and the as-built code (`sbgv7/`, described in `docs/architecture/V7B_IMPLEMENTATION.md`) disagree, the disagreement is recorded as an open item (OI-nn, listed in `reports/phase2/PHASE_2_RECONCILIATION_INDEX.md`) for `reports/phase2/PHASE_2_SPEC_CONFORMANCE_AUDIT.md`; this file does not pick a side. Nothing here claims equivalence or correctness of any pair, a detection rate, or that any threshold is right. All numbers are UNVALIDATED defaults.

## 1. What V7 is (restated for V7-B)

V7-B is a sufficiency-aware, witness-based differential comparison of two Python versions of a declared scope (entry point), under a declared harness `H` and a pre-declared seed policy (FS s1). Per pair it emits exactly one of three verdicts: `DIVERGENT_OBSERVABLE`, `INSUFFICIENT(primary; secondary codes)`, `NO_DIVERGENCE_OBSERVED(S1|S2)` (S3 is defined but `s3_enabled=false` and refused by the as-built config). `ineligible:identical` is a no-verdict exclusion. There is no equivalence verdict; `EQUIVALENT`, `SAME`, `PASS`, `VERIFIED`, `SAFE`, "implicit pass" are prohibited as outcomes (D1; FS s2). `NO_DIVERGENCE_OBSERVED` states only that, on the explored deterministic inputs under `H`, every changed unit ran at least once in each version containing it and no observed-channel difference was found.

Why (unchanged from the original, still the motivating evidence): the V6 dominant failure was observation (28.5% BugsInPy coverage, unactivated changes, return-blind channel), not modelling; V7 therefore invests in controlled execution, explicit sufficiency, replayable witnesses and an evidence contract, not in a learned scorer. V7-A (internal-state value) is an optional gated pilot, never a precondition (D6).

## 2. Reconciled decisions: disposition of the original eleven

| # | Original decision (MASTER s2) | R1 disposition | Basis |
|---|---|---|---|
| 1 | Four verdict values incl. `DIVERGENT_INTERNAL_ONLY`; `NO_DIVERGENCE_OBSERVED` at S0-S3 | **Replaced.** Three values; `internal_divergence in {none, observed, unknown}` is an advisory annotation present only if optional module E is enabled, never a verdict, never changes value, level, code or metric. S0 exists only inside `INSUFFICIENT` | D1, D2, D3; CM V-01, V-02, V-03, S-01, S-02 |
| 2 | F is not a subsystem; three projections inside G and H | **Kept.** Gates/protocol ablate the projection library, not a module | D5; CM M-01 |
| 3 | E split: state abstraction core, invariant mining optional | **Replaced.** E is wholly optional (V7-A pilot only, off by default). The canonical value layer (`AbstractValue`, normaliser N) lives in B/D, not E | D5, D2; CM M-02 |
| 4 | Existing runner/tracer unacceptable; isolation rebuilt | **Kept and made concrete** as I1-I7 (FS s10). Legacy runner survives only as `v6_compat`; its runs are invalid evidence | D10; CM M-04, M-05, M-08 |
| 5 | Capture tiers L0-L3 with explicit completeness | **Kept.** L0 carries a changed-region coverage bitmap; default tier L0(+bitmap) | CM EV-07; FS s11 |
| 6 | Alignment anchors never use the compared payload | **Kept.** G never affects verdict value; locus is optional and inferred; `unlocalised` is valid | CM EV-06; FS s9 |
| 7 | Labels structurally excluded from A-I | **Kept**, strengthened by D11 (also no benchmark identity, no other pairs' outcomes; diff-blind exploration run) | D11 |
| 8 | Synthetic P3 suites need independent generator + fingerprint audit | **Kept** as a K/G requirement; synthetic results are unit/development evidence only | R05; GATES R1 |
| 9 | Witness validity is a correctness gate; FAR paired with coverage floor 0.60 | **Kept**; K4 uses matched decided coverage >= 0.60 | D9 |
| 10 | Budget unit CPU-seconds incl. all V7 overhead | **Kept**; grid 10/60/300, headline 60; per-run limits provisional | D7; CM B-01 |
| 11 | J optional, off by default, own sealed holdout | **Kept**; J never touches a verdict | D5 |

New reconciled decisions added by R1 (from FS and the P0/Phase 1 record): (12) replay protocol `r_det=3`, `r_replay=5`, `k_alt=3`, agreement on `C_obs` (not trace hash or locus); (13) evidence classes observation/derived/inferred/proof + status missing/invalid/uncertain on every record; (14) replay recipe plus hashed event stream by default (full events only for witnesses, a 5% audit sample, escalations); (15) API-break probe (`api_break_probe=true`) yields a `kind=api` witness stratum; (16) K1-K5 and G0-G8 are the only checkpoint/gate names, with the fixed STOP/PIVOT/DOWNGRADE responses of FS s12.

## 3. Architecture

Text form (diagrams in this file were not rendered; the original's mermaid source is unchanged in the archive and would need E drawn as optional and F absent):

```
untrusted programs (old, new)
   |  fresh child process per run (I1-I7), tier L0(+bitmap) by default
   v
B Capture  --RunBundle-->  D Evidence fabric (content-addressed, hash-chained; replay recipe + hashed stream)
C Static (ChangedRegions, SourceMapping, SignatureSketch) --> A Exploration (inputs; label-free; diff-blind run also)
A --Input--> B ;  D --paired RunBundle--> H Divergence/Witness (o(x), ReplayCheck, Witness) ; G Alignment (optional locus/trust)
H, B, C, G --records--> I Decision (SufficiencyRecord, Verdict: sole writer)
K Validation (read-only + labels, scoring) ; L Governance (freezes, audits T1-T7, isolation compliance)
E (optional pilot): internal_divergence annotation only.   J (optional, off): never touches a verdict.
```

Core modules (FS s9): A, B, C, D, G, H, I, K, L. Optional: E (pilot), J (off), concolic extension of A (off), formal tier (`BOUNDED_EQUIVALENCE_PROVEN` is a separate formal claim with its domain, never a verdict). F removed. Dependencies are acyclic and go by record exchange through D. Per-module contracts: `p0_reconciliation/P0_RECONCILED_MODULE_CONTRACTS.md` (authoritative) via `SBG_V7_MODULE_CONTRACTS.R1.md`.

### 3.1 As-built mapping (from `docs/architecture/V7B_IMPLEMENTATION.md`; not independently re-verified by this document)

| Module (FS) | As-built location | State per V7B_IMPLEMENTATION.md |
|---|---|---|
| B Capture | `sbgv7/harness.py` (child-side), `sbgv7/isolation.py`, `sbgv7/sandbox_darwin.sb`, `sbgv7/_child.py` | Implemented; macOS `sandbox-exec` only, `policy_below_minimum=true` on every record |
| D Fabric | `sbgv7/records.py` | Implemented as content-addressed records + hash-chained JSONL; flat hash of run ids, not Merkle; no recipe/event-stream storage (OI-03, OI-04) |
| H Divergence | `sbgv7/compare.py`, `sbgv7/runner.py` (replay protocol) | Implemented for the boundary channels and API break |
| I Decision | `sbgv7/decide.py` | Implemented, S1/S2 only |
| C Static | `sbgv6.features.changed_lines` imported read-only; `runner.py` activation | Minimal; no `ChangedRegions` record with `kind/confidence/unmodelled` |
| A Exploration | none | Not implemented (inputs are user-supplied JSON) |
| G Alignment | none | Not implemented (only `alignment_failed` on parse failure) |
| E, J | none | Not implemented (E/J optional anyway) |
| K Validation | `sbgv7/baselines/`, `experiments/v7b/`, `research/evaluation/` | Development baselines B1, B1+rep, B2 (QuixBugs only), B3 (minimal), B4; B5 partial and not fair; no K gate machinery |
| L Governance | documents only | Not implemented as code |

## 4. Document map (R1 set)

Authoritative order and supersession are in `reports/phase2/PHASE_2_RECONCILIATION_INDEX.md`. In short: frozen spec; D1-D11; `P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md` (SPEC) where the frozen spec is silent; then the R1 set in `reports/v7_design/reconciled/` (this file, schema, roadmap, risk register, final decision, competing architectures, failure-to-requirement matrix, module contracts pointer, experimental protocol, mathematical specification, validation gates, research errata). The original `SBG_V7_*.md` files are historical and superseded; copies are in `_original_archive/`.

## 5. Inconsistencies from the original s5: status

| Original item | Status in R1 |
|---|---|
| Math spec/schema may say single `DIVERGENT` | Closed (math R1 F4/F5 and schema R1) |
| Thresholds untuned | Open by design: all are UNVALIDATED defaults (D3), changeable only on the development split |
| References metadata-verified only | Open; use `P0_LITERATURE_VERIFICATION.md` and `research/literature/`; absence claims rest mostly on abstracts |
| No cross-reading | Partly closed: P0 reconciliation cross-read; residual: EP s3.2, 4, 5, 6 and the 14-row validation matrix not line-by-line checked (P0 reconciliation report s4) |
| Mermaid never rendered | Open |

## 6. Not claimed

No detection rate, no false-assurance reduction, no calibration of S1/S2, no generalisation beyond Python top-level functions with JSON-representable arguments on one macOS machine, no isolation claim stronger than "verified on macOS `sandbox-exec`" (FINAL_CLAIMS_AND_EVIDENCE_MATRIX). Phase 3 items (Linux/Docker isolation, project-level runs of external repositories, independent benchmark collection, exploration, published-tool baselines) are **Phase 3, not started**.
