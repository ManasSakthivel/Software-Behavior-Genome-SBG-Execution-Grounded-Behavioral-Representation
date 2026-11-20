# IEEE Access exploratory manuscript (V7-B, Phase 2 results)

Status: initial research manuscript, not peer reviewed, EXPLORATORY. Phase 2 only (local macOS). All evaluation data are non-pristine development data with no independent holdout; Linux/Docker isolation, tamper-proofing, complete determinism, comparison with published tools, K1/K5 and Phase 3 are NOT validated or deferred. No claim of IEEE Access readiness, superiority, equivalence checking or generalisation.

**Not compiled** (no LaTeX toolchain); see `COMPILE_OVERLEAF.md`.

Layout: `main.tex`; `sections/*.tex`; `tables/` (generated `P_*.tex` plus hand-written `baselines`, `capability`, `not_evaluated`); `references.bib` (only cited entries copied from `research/literature/VERIFIED_REFERENCES.bib`); `figures/*.dot` (old Graphviz sources, unused). Figures come from `results/v7b_phase2_summary/figures/` (see `FIGURE_TABLE_INVENTORY.md`).

Checks and generated files:
1. `.venv/bin/python scripts/p2_make_paper_figures.py` (repository root) regenerates figures and `tables/P_*.tex`, `tables/SOURCES.json` from `results/v7b_phase2_summary/`.
2. `python3 scripts/build_bib.py` rebuilds `references.bib`; `python3 scripts/check_manuscript.py` checks cites, refs, files and table numbers (run from this folder).
3. `python3 scripts/verify_numerical_claims.py` regenerates `NUMERICAL_CLAIM_VERIFICATION.md`; `python3 scripts/build_citation_verification.py` regenerates `CITATION_VERIFICATION.md`.
