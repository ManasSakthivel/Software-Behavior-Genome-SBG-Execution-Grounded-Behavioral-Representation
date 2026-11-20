# Pilot reproducibility report (Phase 4)

What is reproducible:
- Upstream defect reproduction for 15 shortlisted cases (parent fails on the regression test, fixed passes). Logs: `audit/phase2/repro/full/`. Summary: `audit/phase2/repro/SHORTLIST_PARENT_CHECK.json`.
- Frozen snapshot integrity: `phase3/verify_freeze.py` passes (23,692 files; blob hashes match commit `2edfe568`).

What is not reproducible here: any SBG score on any case, because none was produced.
Repeated-run consistency for SBG: not measured (0 runs).
