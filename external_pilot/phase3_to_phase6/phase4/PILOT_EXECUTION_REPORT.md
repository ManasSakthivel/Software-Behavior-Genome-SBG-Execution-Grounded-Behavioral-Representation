# Pilot execution report (Phase 4)

Status: **NOT EXECUTED.** Blocker: the frozen SBG V8 package has no input generator for external modules (`phase3/SBG_V8_EVALUATION_PROTOCOL.md` §4). Per-case inputs written by hand are forbidden by the brief, so no case can be run through the frozen package. The executed cohort is 0.

- Candidate cohort: 15 cases (`audit/phase2/PILOT_CASE_SHORTLIST.md`).
- Eligible for execution: 0 (no generator for external inputs).
- Executed: 0. Cases excluded: 15 (reason: execution infrastructure absent).
- No SBG score, verdict, runtime or memory figure exists for any case.
- Infrastructure checked: CPython 3.13.15 venv created from the declared lock; the frozen project tests were run (see `phase3/pytest_frozen_2edfe568.log`).
- Prior five-dataset run (`ca7c2b2a`): its executor does not run programs; its "verdicts" come from test labels and a stub predictor. Not used here.
