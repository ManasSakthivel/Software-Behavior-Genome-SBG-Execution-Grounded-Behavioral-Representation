# Scientific eligibility reassessment (Phase 4 preflight)

Phase 2 classifications are preserved unchanged. Technical adapter compatibility is not treated as scientific eligibility; the two are assessed separately.

## Per-criterion status (all 15 cases)

| Criterion | Status | Basis |
|---|---|---|
| Authentic upstream provenance | Met for local evidence; upstream identity verified only against local `origin` URLs, not online | Phase 2 overlap audit |
| Buggy and fixed revision identity | Met | commits and parents recorded in `PILOT_CASE_SHORTLIST_DATA.json` |
| Parent/fixed reproduction | Met for all 15 (parent fails, fixed passes) | `audit/phase2/repro/full/` |
| Valid input domain | Met for behaviour; not met for adapter v1 (see compatibility report) | this preflight |
| Independence from development data | Met at repository and case level | Phase 2 overlap audit |
| Behavioural evidence category | 8 assertion, 1 raises, 6 exception-removed | strict check |
| Exception-only evidence | 6 cases (see below) | strict check |
| Suitable for primary evaluation | Qualified; see below | this document |

## Exception-only cases (6)
schedule 90bfdf355; funcy 2da8b5e04, 980f0279a, e148cc9ab, 6c111987f, e068b6400.

For these, the parent failure is an exception the fix removes, not an assertion on the defective value. The exception may be a symptom. Each is retained as a candidate, but cannot be the sole basis of any primary claim. Recommended: report them separately as a secondary stratum.

## Adjusted classifications
- All 15: SCIENTIFICALLY_ELIGIBLE_BUT_ADAPTER_UNSUPPORTED. Scientific eligibility holds with qualifications; adapter compatibility fails.
- None was reclassified as SCIENTIFICALLY_INELIGIBLE, PROVENANCE_UNRESOLVED or OBSERVATIONALLY_UNSUITABLE. The provenance caveat (local-remote-only identity) applies to all 15 and is disclosed, not used to exclude.

## Counts
- Scientifically eligible (with qualifications): 15
- Scientifically ineligible: 0
- Unresolved provenance: 0 (caveat applies to all 15)
- Exception-only evidence: 6
