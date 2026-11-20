# Final reproducibility audit
Supersedes nothing (see `REPRODUCIBILITY.md`); linked from README.md.
1. **Analysis from saved records** (stats, post-hoc ERS matrix, five-dataset audit, figures): reproducible, no program executed; Linux = macOS to 1e-9.
2. **Re-executable collection** (macOS security suite, tests): re-run gives new observations.
3. **Not reproducible from repository:** per-run logs behind the 312 records; real-execution run directories (720-row matrix only; manifest lists uncommitted changes at 01fdaf09, seed 20261118); Linux security run (no host metadata, no commit); Linux stats run (`run_meta.json` has no commit).
Round 3 re-ran only figure generation (`make_figures.py`) and the LaTeX build. No public archive/DOI exists. Provenance table: paper Table 23.
