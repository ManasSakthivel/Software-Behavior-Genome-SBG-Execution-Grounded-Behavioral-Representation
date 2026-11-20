# SBG V7 P0: Audit Findings Summary

Scope: 13 `SBG_V7_*.md` design documents plus `_sources/_DESIGN_SPINE.md` (current files are byte-identical to `_original_archive/`). Details: `P0_CROSS_DOCUMENT_CONTRADICTION_MATRIX.md` (row IDs below) and `P0_EVIDENCE_TAXONOMY_AND_SCHEMA_AUDIT.md`.

## Counts by severity (matrix rows)

| Severity | Count |
|---|---|
| Blocking | 10 |
| Major | 31 |
| Moderate | 17 |
| Minor | 7 |
| Total | 65 |

(One further row, N-04, records a check with no contradiction and is not counted.)

By theme: verdict/equivalence 7, sufficiency 5, evidence/schema 13, modules/isolation 9, budgets 4, experimental design 14, checkpoints/gates 7, effort 2, requirements/numbers 4.

Spot-checks: 23 numeric claims compared with repo files; 18 match, 5 have a discrepancy or need a qualifier (CONV GBM 0.972 vs 0.9705; "V6 alone ~0.52" vs 0.5824; BugsInPy UNKNOWN causes sum to 113 vs 117; "76% abstention" is 42/55 real fixes, 71.5% overall; v8 26 programs vs 22 clusters, explained).

## Top 10 blockers

1. **V-01/V-02/V-03 Verdict set.** MASTER and ROADMAP use four values (`DIVERGENT_OBSERVABLE`, `DIVERGENT_INTERNAL_ONLY`, ...); SCHEMA, MATH, CONTRACTS, EP and GATES use three. The same masked-internal case is a fourth verdict, an annotation, or a false alarm, with tolerated rates of 30% (ROADMAP G3), 0 promotions (GATES row 3) and 1% (EP H8). Requirements R-03, R-19 and R-23 still demand an "EQUIVALENT-within-budget" class that MASTER forbids.
2. **S-01 Four incompatible S0-S3 definitions** (SCHEMA, ROADMAP, EP, plus MATH's scalar with floors), and four definitions of "saturation"; the calibration caps (S1 0.35, S2 0.20, S3 0.10) exist only against EP's version.
3. **K-01 K1-K5 outcomes disagree.** FINAL: "stop entirely if K1 or K5 fail"; ROADMAP: de-scope or pivot; RISK: stop only on conjunctions. K4's pass condition is an any-of weaker than H7 and V7-A.
4. **G-01 Gate numbering.** G0-G8 (MASTER, FINAL, GATES) vs G0-G9 (ROADMAP, RISK) with different meanings from G1 on; "G1 hard gate", "freeze at G6" and every "monitored by G-n" are ambiguous.
5. **X-01 Confirmatory holdout not planned.** EP/GATES require positive results on H-R and H-M plus truth harness, H-P and H-X; ROADMAP P7 builds none of H-M/H-P/H-X and excludes mutation pairs.
6. **X-02 K5 size gate too small.** K5 passes at 200 pairs, 60 divergent, 15 projects; EP and FINAL require about 150 divergent, 150 controls, 40 projects, 30 clusters (otherwise "descriptive only").
7. **X-03 Truth circularity.** INTERNAL_ONLY truth presupposes an internal-state notion the truth harness does not define; Eq-B by fuzz-negative is "no tool found a difference", which ROADMAP itself forbids.
8. **B-01 Budget unit.** EP/MASTER: CPU-seconds (grid 10/60/300); ROADMAP K3/K4/P4: 60 s wall on 4 cores (up to 240 CPU-s), 5000 executions; CONTRACTS/SCHEMA: 300 inputs, 60 s. K4 calibrated on one budget does not predict the confirmatory claim on another. Companion arithmetic (B-02, B-03): capture alone uses the 60 CPU-s at k=2; holdout cost about 292-875 CPU-h vs the stated 150.
9. **S-01 follow-on / EV-06 (Major, escalate in P0).** Anchors defined on "equal payload_hash" (CONTRACTS G, SCHEMA) reintroduce the circularity MASTER decision 6 closes; and M-05: GATES G1 has no sandbox-escape hard gate although RISK calls it the only hard gate. Both are Major in the matrix and should be fixed before P1.
10. **G-02 G0 not passable at week 3.** GATES G0 needs frozen project lists, independence report, kappa pilot and truth-harness smoke test; ROADMAP schedules that data work for weeks 1-12 (K1 at week 4, adjudication weeks 8-29). Also E-01: the 51 engineer-week / 32-week estimate excludes truth harness, H-M authoring and H-P (about 230 adjudicator-hours at EP scope **[est]**).

Note on counting: items 1 spans three Blocking rows; items 9 and 10 each combine one Blocking or Major row with its closest sibling, so the numbered list is 10 items but the Blocking count is exactly the 10 rows V-01, V-02, V-03, S-01, B-01, X-01, X-02, X-03, K-01, G-01. G-02 and EV-06/M-05 are Major, listed because they gate P1 progress.

## Other findings worth knowing

- R-01..R-31 are cited by ID only in INVENTORY, MASTER and FINAL; R-13 and R-30 are not found in any V7 design document; R-14 is orphaned by the removal of F (R-A, M-01).
- Evidence classes: none of the seven requested classes is defined anywhere; canonical proposal and 12 provenance gaps in the audit file (EV-01..EV-13, tables 2 and 3.2).
- Storage and ingest bounds hold only at CONTRACTS scale (about 1,200 runs per pair), not at the ROADMAP default (up to about 50,000 runs per pair at k=5) (**[est]**).
- Existing runner and tracer are confirmed unsuitable for claims (no subprocess/rlimit; daemon thread plus `sys.settrace`), consistent with MASTER decision 4.

## Not checked or unverified

Mermaid diagrams not rendered; literature references and DOIs not verified; R-xx coverage judged by ID grep plus topic search; CAS deduplication behaviour unspecified; schema examples read, not executed; all overhead figures are estimates from the documents' own rates.
