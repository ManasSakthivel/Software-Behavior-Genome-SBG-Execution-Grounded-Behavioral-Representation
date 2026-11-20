# Novelty reconstruction report
Supersedes `NOVELTY_AND_PRIOR_WORK_ANALYSIS.md` (kept for history); linked from README.md.

**Problem.** A no-divergence verdict asserts only observation. Trusting it needs sufficiency, integrity, provenance and responsiveness; equivalence is unreachable by finite observation (Remark 1). A binary outcome carries none of these.

| Component | Status |
|---|---|
| False-assurance estimand R=P(F=1 given NDO) relative to (O,B,C) | Adapted (selective risk), new in scoping |
| Prop. 1 integrity must gate every verdict | New formal statement; elementary proof |
| Prop. 2 risk monotone in boundary/budget | New formal statement; elementary; assumes sound, monotone adjudication |
| Prop. 3 random abstention preserves expected risk | Known principle, restated |
| Prop. 4 conformance independent of accuracy | New formal statement; elementary |
| Change-conditioned profile / CEC | Adapted; predictive value not demonstrated |
| ERS eight properties, N/A and abstention accounting | New property set; builds on evidence deletion, metamorphic relations |
| Trusted acquisition | Engineering adaptation |
| Matched-coverage evaluation | Established practice applied |

**Closest work** (Table 2, 15 works): SemaDiff (dataset-level agreement accuracy), FEAgent (abstains, ledger, no risk estimand or integrity testing as described), selective classification, checked coverage, PIE, oracle assessment, in-toto. No "first" claims; "we did not find".
**Limit.** The contribution is an integration plus elementary formal consequences. Propositions are not deep theorems and are not presented as such.
