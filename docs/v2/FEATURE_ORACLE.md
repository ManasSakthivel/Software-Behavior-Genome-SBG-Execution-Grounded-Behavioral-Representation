# SBG V2 — Feature Oracle Audit (SAFEGUARD-2)

**Pre-registration timestamp:** 2025-07-07  
**Purpose:** Classify every v2 dynamic feature as Output-free or Output-proximate BEFORE any experiments.

---

## Classification Rules

- **Output-free:** Feature captures execution STRUCTURE only (call frequency, branch coverage, allocation patterns, exception types). Cannot reveal output values. **ADMISSIBLE in SBG genome.**
- **Output-proximate:** Feature encodes or proxies return values, stdout, or output content. Equivalent to differential testing. **NEVER in SBG genome. Only in B09_differential_testing baseline.**

---

## Feature Classification Table

| ID | Feature | Classification | Rationale | SBG Admissible |
|----|---------|---------------|-----------|----------------|
| F01 | Branch coverage vector (line numbers reached) | OUTPUT-FREE | Which lines execute, not what values are computed | ✅ YES |
| F02 | Anonymized function call frequency histogram | OUTPUT-FREE | How often each structural position is called | ✅ YES |
| F03 | Hot path signature (SHA of top-5 anon function ranks) | OUTPUT-FREE | Execution order pattern, rename-invariant | ✅ YES |
| F04 | Instruction type histogram (call/return/exception/line counts) | OUTPUT-FREE | Event type distribution, no values | ✅ YES |
| F05 | Exception type set (class names only, no messages) | OUTPUT-FREE | Error behavior structure, not content | ✅ YES |
| F06 | Exception frequency per input | OUTPUT-FREE | How often errors occur | ✅ YES |
| F07 | Unique function count (integer, not names) | OUTPUT-FREE | Structural complexity measure | ✅ YES |
| F08 | Call depth distribution (histogram) | OUTPUT-FREE | Recursion depth pattern | ✅ YES |
| F09 | Trace length statistics (mean/std event count) | OUTPUT-FREE | Execution volume, no values | ✅ YES |
| F10 | Coverage consistency (Jaccard across inputs) | OUTPUT-FREE | Path stability across inputs | ✅ YES |
| F11 | Return value hash (SHA of repr(return_value)) | OUTPUT-PROXIMATE | Directly encodes output | ❌ NO |
| F12 | Stdout content hash | OUTPUT-PROXIMATE | Directly encodes output | ❌ NO |
| F13 | Return value type name (class name only) | OUTPUT-FREE | Type is structural; value not captured | ✅ YES |
| F14 | Stdout length (character count) | BORDERLINE — EXCLUDED | Proxies output length; excluded conservatively | ❌ NO |
| F15 | Exception message text | OUTPUT-PROXIMATE | Message may encode values | ❌ NO |
| F16 | Exception class name | OUTPUT-FREE | Same as F05, more granular | ✅ YES |
| F17 | L1 distance on call frequency histograms | OUTPUT-FREE | Structural aggregation | ✅ YES |
| F18 | Jaccard distance on coverage vectors | OUTPUT-FREE | Structural aggregation | ✅ YES |

---

## SBG V2 DynamicGenome Features (Output-free only)

F01, F02, F03, F04, F05, F06, F07, F08, F09, F10, F13, F16, F17, F18

## Differential Testing Baseline Features (B09)

F11, F12 — output comparison only; used in B09_differential_testing, labeled as such

## Excluded Features

F14 (borderline), F15 (output-proximate message text)

---

## Implementation Checklist

- [ ] DynamicFeatureNormalizer must NOT access `trace.return_value`
- [ ] DynamicFeatureNormalizer must NOT access `trace.stdout` content
- [ ] Exception handling must extract class name only (split on `:`, take first token)
- [ ] Code review: grep for `return_value` and `stdout` in sbg/v2/ — any occurrence requires justification
- [ ] Unit test: DynamicGenome.to_dict() must not contain keys "return_value" or "stdout"
