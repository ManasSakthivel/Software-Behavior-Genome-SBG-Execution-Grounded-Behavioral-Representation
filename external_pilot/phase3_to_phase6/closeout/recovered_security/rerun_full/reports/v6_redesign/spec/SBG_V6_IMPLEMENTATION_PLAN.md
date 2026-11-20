# SBG V6 — Implementation Plan
1. `sbgv6/config.py` constants. 2. `observe.py` Python adapter + trace recorder. 3. `features.py` blocks. 4. `evidence.py`. 5. `distance.py`. 6. `fusion.py`. 7. `tests/v6/` (invariance, determinism, evidence status, undefined handling, golden toy pairs). 8. `experiments/v6/{extract_pairs,evaluate,robustness}.py`. 9. DEV run -> decisions -> freeze -> H1/H2/X -> reports.
Milestone commits: specs, code+tests (807 V5 tests re-run), DEV results, freeze, post-freeze runs, final reports.
Non-goals: neural models; Java/C implementation; PDG slicing; symbolic execution.
