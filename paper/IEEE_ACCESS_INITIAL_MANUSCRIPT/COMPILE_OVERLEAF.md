# Compiling the manuscript (NOT yet done: no LaTeX toolchain on the authoring machine)

Status as of 2026-11-17: `pdflatex`, `latexmk`, `tectonic` and Graphviz `dot` are all absent here. The manuscript has **never been compiled**. `scripts/check_manuscript.py` verifies cite keys, labels/refs, included files and table numbers, which is not a compile.

## Overleaf (recommended)
1. Render the diagrams first (any machine with Graphviz): `for f in figures/*.dot; do dot -Tpdf "$f" -o "${f%.dot}.pdf"; done`. Until then `\dotfig` prints a placeholder box (by design).
2. The data-figure includes in `sections/results.tex` point to `../../results/postfix/figures/*.pdf`, outside this folder, so a zip of only this directory will not find them. Either upload the whole repository, or copy those PDFs into `figures/` and change the three `\includegraphics` paths accordingly (a path edit only; do not regenerate or alter the figures).
3. Zip this directory (`main.tex`, `references.bib`, `sections/`, `tables/`, `figures/`) and upload via Overleaf "New project -> Upload project". Set the main document to `main.tex`, compiler pdfLaTeX, and let BibTeX/Biber run (the draft uses `cite` + BibTeX).
4. `IEEEtran` is built in to Overleaf. For the journal template, replace `\documentclass[journal]{IEEEtran}` with `\documentclass{ieeeaccess}` (use the official IEEE Access template project) and adapt the title block; section files are class-independent.
5. Expected checks after compiling: no undefined citations/references in the log; the figure placeholders gone; table widths fit two columns (tables were never typeset and may need `\resizebox`/`table*`).

## Local
`brew install --cask mactex-no-gui graphviz` (large), then `latexmk -pdf main.tex`. Do not report a successful compile until the log is read.
