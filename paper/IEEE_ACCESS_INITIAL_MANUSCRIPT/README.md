# IEEE Access initial manuscript (V7-B)

Status: initial research manuscript, not peer reviewed, EXPLORATORY. All evaluation data are non-pristine development data; no confirmatory result exists.

**Not compiled.** No LaTeX toolchain (`kpsewhich`, `pdflatex`) is installed on this machine, so `main.tex` was never compiled and may contain LaTeX errors. It uses `IEEEtran` (journal option); if `ieeeaccess.cls` is available, switch the `\documentclass` line. Diagrams in `figures/*.dot` are unrendered (no Graphviz); `\dotfig` prints a placeholder until `dot -Tpdf X.dot -o figures/X.pdf` is run.

Layout: `main.tex`, `sections/*.tex`, `tables/*.tex` (T1-T10 generated, `capability`, `not_evaluated`, `baselines` hand-written), `references.bib` (only cited entries copied from `research/literature/VERIFIED_REFERENCES.bib`), `figures/` (diagram sources), `FIGURE_AND_TABLE_REGISTER.md`.
Data figures are included from `../../results/postfix/figures/` (post-fix); `results/figures/` holds superseded pre-fix versions.

Scripts (run from this directory, Python 3 stdlib only):
1. `python3 scripts/make_tables.py` regenerates `tables/T*.tex`, `tables/derived_crosstab.csv`, `tables/SOURCES.json` from `results/postfix/`.
2. `python3 scripts/build_bib.py` rebuilds `references.bib`.
3. `python3 scripts/check_manuscript.py` checks cite keys, refs/labels, included files, cited paths, and that every number in generated tables appears in its source file.
