Reconciled version R1 of SBG_V7_MODULE_CONTRACTS.md; original preserved at reports/v7_design/_original_archive/

# SBG V7 Module Contracts, R1 (pointer plus deltas)

**Authoritative content:** `reports/v7_design/p0_reconciliation/P0_RECONCILED_MODULE_CONTRACTS.md` ("PRMC"). It carries the full per-module contracts A-L, the capture tiers L0-L3, the I1-I7 isolation profile, replay-recipe storage, the dependency table, the end-to-end sequence, the 24-row "Changes from original" table (section 4) and its open items C-O1..C-O4 (section 5). This R1 file does not duplicate it. Read order: `reports/final/V7B_FROZEN_SPEC.md` (wins on any disagreement) > `P0_BINDING_DECISIONS.md` > PRMC > this file. The original `SBG_V7_MODULE_CONTRACTS.md` is superseded.

## 1. Summary (identical to PRMC s0 and FS s9)

Core: A Exploration, B Capture (only module that runs untrusted code), C Static, D Fabric, G Alignment, H Divergence/Witness, I Decision (sole writer of `Verdict`), K Validation, L Governance. Optional: E (state abstraction and invariant mining; V7-A pilot only; off), J (prediction; off; never touches a verdict). Removed: F (projections live inside G and H). Records flow through D; dependencies are acyclic.

## 2. Deltas on top of PRMC (this R1 only)

| # | Delta | Reason | ID |
|---|---|---|---|
| 1 | Every PRMC reference to "ORIG-C" now means the archived original, and every reference to `SBG_V7_DATA_AND_EVIDENCE_SCHEMA.md` ("SCHEMA") now means `SBG_V7_DATA_AND_EVIDENCE_SCHEMA.R1.md` | the schema R1 exists now (O13 closed) | O13 |
| 2 | PRMC "Open items" C-O1..C-O4 stay open. C-O1 (per-run limits, per-pair budget, event caps, storage/ingest bounds) is partly answered by FS s11 provisional values (claims 10 CPU-s, fast 2 CPU-s, wall 20 s, RSS 2 GiB, L1 events 200k, budget grid 10/60/300, headline 60) which are still "frozen from P1 measurement": P1 measurement was not made on the target platform (Phase 3, not started) | FS s11 | O5 |
| 3 | PRMC C-O2 (isolation properties I2-I4 unverified, container path untested) is unchanged by Phase 1: macOS child process plus `sandbox-exec` network/write denial verified; `RLIMIT_AS` and `RLIMIT_NPROC` not enforced on macOS (soft RSS watchdog only); reads unconfined; `setsid()` escape of group kill untested; Linux/Docker not tested. Claims stay restricted to non-adversarial benchmark corpora and `policy_below_minimum=true` | `research/security/EXECUTION_ISOLATION_AUDIT.md`; red team M-6 | OI-14 |
| 4 | PRMC C-O3 (object-argument inputs) is unchanged: as-built inputs are user-supplied JSON values only (no tuples, sets, objects) | V7B_IMPLEMENTATION "Not implemented" | OI-15, R54 |
| 5 | Module-to-code map (as-built, not independently re-verified): B `sbgv7/harness.py`, `isolation.py`, `_child.py`; D `records.py`; H `compare.py` and the replay protocol in `runner.py`; I `decide.py`; config `config.py`; CLI `__main__.py`; K `sbgv7/baselines/`. A, G, E, J absent; C minimal (imports `sbgv6.features.changed_lines` read-only); L documents only | `docs/architecture/V7B_IMPLEMENTATION.md` | n/a |
| 6 | Spec-vs-as-built differences discovered while reading are not resolved here; each is an open item for the conformance audit: stored data (hit lines + observation id vs recipe + hashed event stream, OI-03), run-set root (flat hash vs Merkle, OI-04), `Supersession` (OI-05), unproduced reason codes (OI-06), config subset (OI-07), dependency/runtime identity check (OI-08), `NO_RUN` mapping (OI-09), quarantine granularity (OI-10), `r_empty` stratum (OI-11), entropy virtualisation (OI-12), replay `inconclusive` on build mismatch (OI-13), tamper detection timing and stdout bypass (OI-20) | Index s4 | OI-03..OI-13, OI-20 |
| 7 | Contract K (validation) in PRMC lists baselines B1-B8 and the like-for-like rule; as-built has B1, B1+rep, B2 (QuixBugs only), B3 (minimal), B4 and a partial B5. B5 is a lookup of V6 scores on different inputs and is not input- or budget-matched; no published-tool baseline is implemented | `research/evaluation/BASELINE_IMPLEMENTATION_AND_FAIRNESS.md`; red team M-4 | R48, R50 |

## 3. Not changed

Nothing in PRMC is contradicted by this file. PRMC remains one source of truth for module contracts; if PRMC and the frozen spec ever disagree, the frozen spec wins and the case is logged in the Index.
