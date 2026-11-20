# Closure of the Adapter v1 pilot attempt

Date: 2026-11-20

## Conclusion
The 15 shortlisted external cases are scientifically eligible with qualifications, but they cannot be executed using the current External Input Adapter v1 interface. **No external pilot was performed.**

This is not a negative SBG result. SBG V8 has not been run on any external case, so no conclusion about its behaviour on external cases can be drawn.

## Basis
- Phase 2: 15 cases with verified buggy and fixed revisions and reproduced parent/fixed behaviour (`audit/phase2/`).
- Phase 4 preflight: 0 of 15 compatible with Adapter v1; 15 of 15 have at least one blocker; 14 of 15 have two or more; 6 are exception-only evidence (`phase3_to_phase6/phase4_preflight/`, integrity audit completed).

## Preserved, unchanged
- Frozen SBG V8 at commit `2edfe568` (`phase3_to_phase6/phase3/`).
- External Input Adapter v1 and commits `b778654`, `9873eb8` (`external_input_adapter_v1/`).
- The 15 shortlisted cases (`audit/phase2/PILOT_CASE_SHORTLIST*`).
- All corrected Phase 4 preflight documents, with prior versions in `previous_v1/`.

## Not done
- No adapter extension was developed in this closeout.
- No case was executed through SBG V8 or Adapter v1.
