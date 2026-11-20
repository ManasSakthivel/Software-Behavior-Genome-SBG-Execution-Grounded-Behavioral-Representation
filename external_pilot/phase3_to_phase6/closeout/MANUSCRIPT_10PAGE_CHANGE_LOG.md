# SBG V8 IEEE Access manuscript: condensed 10-page version, change log (revision 2)

Status: first draft for researchers. Not submitted. The author-name line is retained; affiliation, e-mail and biography are removed and must be added before any journal submission.

## Files
- PDF: `closeout/SBG_V8_manuscript_10page.pdf` (10 pages by page-tree count).
- Source: `closeout/SBG_V8_manuscript_10page_source.zip`. The class file is the template class with the footer text removed.
- Working folder: `closeout/manuscript_10page/`. Unchanged: `closeout/manuscript_final/`.
- Public repository: https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation (public, read without credentials).

## Corrections made in revision 2
- Labeled-arm abstention: 127 of 266 (48%). Checked against the corpus table: 266 − 78 DIV − 61 NDO = 127. The earlier 125 (47%) was wrong.
- Frozen suite: 806 collected = 372 passed + 1 stalled (373rd test, run stopped) + 433 not run. No failures among the tests run.
- Probe identifiers renamed PR-04, PR-06, PR-08 (were P04, P06, P08). They no longer collide with ERS properties P6 and P8.
- Proofs: the four propositions now include short proofs in Section III, so the Table 1 entry "with proofs" points to text in the paper. No proof file exists in the public repository.
- Overclaim removed: "every number recomputed" replaced by an accurate statement; the cross-platform figure is marked as reported by the project and not re-run.
- Table 4 row referring to "settings A–G" reworded; those categories are not in the paper.
- Sentence about the label-blind generator rewritten (20 primary pairs: none; 10 supplementary: one, and the predictor passed that check).
- Internal notes removed: the 2edf568 sentence, all [VERIFY] tags, and the frozen-freeze sign-off status.
- Literature: SemaDiff figures now 75.95% accuracy and 58.89% recall on 183 labeled Java commits (from the public literature register, full-text read). DiffTestGen's percentage is not used because its abstract (78.2%) and body (79.7%) disagree in the register. PatchGuru title completed to the arXiv title (2602.05270). The FEAgent sentence was removed: the only source found was a NeurIPS 2026 abstract listing with no verifiable author list, and the claim could not be checked. Mutation citation narrowed to the 2018 correlation study.
- Strict-policy statement (v8.0s and v8.1 coincide on the 61 pairs) is supported by the stored ablation table; the [VERIFY] was removed.
- Front matter: `\history{}` and `\doi{}` are empty (the class needs them defined); date, DOI, footer volume text and biography placeholders removed. Affiliation line removed.
- Data availability rewritten to list only what is in the public repository (see below).
- Frozen thresholds: both values stated, discrepancy unresolved (unchanged).

## What the public repository contains (checked)
- Branch `research/v8-linux-validation` (head 07ecd5b7): commit 2edfe568 (frozen implementation), development records, held-out test pairs, both threshold files, the real-execution matrix and its manifests.
- Branch `research/v8-mac-hardening` (head 8e28f601): macOS results and profile-fix results.
- Not in the public repository: the security re-run output (`audit/security_rerun_darwin.json`) and its script; the statistics summary (`audit/stats_summary.json`) and recompute script; commits df612db0 and b9b8a86c; the per-run real-execution directories; the supplementary tables. The paper says these are available from the authors on request. To make that sentence public-checkable, push these files to the repository and change the sentence.

## Open items for the author (not resolvable from the repository)
1. Author affiliation, e-mail and biography (required by IEEE Access before submission).
2. Push the files listed above, or keep the "on request" wording.
3. The frozen-threshold discrepancy (0.072905 vs 0.040511) is unresolved; it is stated in the paper.
4. Confirm which figures and tables the brief requires in the main text. Current choice: two results figures and eight tables.
5. Visual layout check of the PDF (not done: no rasterizer). The build log shows overfull and underfull box warnings.
