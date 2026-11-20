# SBG — Prioritised Completion Plan for 2026-11-04

**Companion to:** `SBG_CURRENT_STATE_FORENSIC_AUDIT_2026-11-04.md`
**Basis:** frozen V9c-val and V10 evidence at `remediation/sbg-v4` (`93ef3f3`). **No new experiments.**
**Goal:** the shortest scientifically safe path to a complete, defensible IEEE Access manuscript.

## Ground rules

1. **Do not touch frozen artifacts.** Never run `make reproduce-*`, `v7-*`, `quixbugs`, `bugsinpy` or `java`. Do not run `evaluate_v8/9/10.py`. Write all new files in a **new directory** such as `paper/` or a separate folder, and commit nothing until the draft is done.
2. **Every number in the paper comes from a frozen JSON file**, copied through a script that only reads (see P0-5).
3. **Wording rules.** V10 is "withheld, same author and generator". Null results are "no statistically established gain", never "equivalent". Real-bug results are "exploratory, at or below chance".
4. **Banned words** (checklist item 19 of the blueprint): first, novel, unique, validated, detects bugs, generalises, beyond execution statistics, V6 better, COBOL.

## Decisions that fix the shape of the paper

| Decision | Choice |
|---|---|
| Paper type | Evaluation-methodology paper with an empirical (partly negative) finding |
| Primary method | SBG V5, fixed weights 0.50/0.25/0.25 |
| Headline split | V10 (19 programs, 638 pairs, 319 matched sets) |
| Replication | V9c-val (11 programs, 432 pairs) |
| Motivating negative | V8 test: V5 0.694 vs reversed edit size 0.876 |
| Where the H4 null goes | Abstract, Results (own subsection), Discussion, Conclusion |

---

# P0 — Mandatory before submission

## P0-1 Create the manuscript skeleton in the IEEE Access template
- **File:** new `paper/main.tex`, `paper/refs.bib`, `paper/figures/`, `paper/tables/`.
- **Change:** download the current IEEE Access LaTeX template (`ieeeaccess.cls`) from IEEE's author centre. Set up the ten sections from `FINAL_MANUSCRIPT_BLUEPRINT.md` §5.
- **Why:** nothing exists. All other tasks hang off this.
- **Depends on:** nothing.
- **Effort:** 0.5 h.
- **Verify:** the empty skeleton compiles with `pdflatex`. UNVERIFIED whether a LaTeX toolchain is installed locally; fall back to Overleaf.
- **Deliverable:** compiling skeleton.

## P0-2 Build the bibliography from verified records only
- **File:** `paper/refs.bib`.
- **Change:**
  - Include only works with verified metadata: Kessel & Atkinson `10.1109/SCAM.2019.00030`, Danglot et al. `10.1007/s10664-019-09794-7`, EquiBench arXiv:2502.12466 (cite as arXiv; **no venue**), TRACED `10.1145/3597503.3608140`, Krinke & Ragkhitwetsagul arXiv:2505.04311, Yu et al. `10.1145/3502852`, Ojdanić et al. `10.1145/3530786`, Just et al. `10.1145/2635868.2635929`, Jiang & Su `10.1145/1572272.1572283`, Evans & Savoia `10.1145/1295014.1295038`, Jin et al. `10.1109/ICST.2010.64`, Person et al. `10.1145/1453101.1453131`, Podgurski & Pierce `10.1145/143062.143152`, BugsInPy (ESEC/FSE '20), QuixBugs (Lin, Koppel, Chen, Solar-Lezama, SPLASH Companion 2017, `10.1145/3135932.3135941`).
  - Add the gap candidates from audit §I.4 **only after** you open each DOI and confirm title and authors: Xie & Notkin (`10.1109/tse.2005.107`), Myles & Collberg (two papers), Papadakis et al. TCE (`10.1109/icse.2015.103`), Chen et al. metamorphic testing survey (`10.1145/3143561`), Sumner & Zhang (`10.1109/icse.2013.6606573`).
  - Drop Sumner (ICST 2011), the Piech characterisation, and `PRIOR_ART_MATRIX.md` entries [17], [21], [24], [25], [33], [36], [39].
- **Why:** several repo citations are wrong or unverifiable; reviewers check DOIs.
- **Depends on:** nothing.
- **Effort:** 1.5 h.
- **Verify:** each BibTeX entry has a resolvable DOI or arXiv ID. No entry copied from `PRIOR_ART_MATRIX.md`.
- **Deliverable:** `refs.bib`.

## P0-3 Obtain the related-work evidence you can obtain, and label the rest
- **File:** `paper/sections/related_work.tex`.
- **Change:**
  - Try to obtain Kessel & Atkinson full text (institutional access, author request, ResearchGate). Read at least the study design, representation and result sections.
  - Read Xie & Notkin, Jin et al., and Person et al. at method level if available.
  - **If any of these cannot be read**, write the comparison at abstract level and state this in the text ("we compare against the published abstract"). Do **not** write "unlike K&A, which..." beyond what the abstract supports.
- **Why:** the nearest-neighbour paper is the reviewer's first objection (audit §P, objection 3).
- **Depends on:** P0-2.
- **Effort:** 2 h (access-dependent).
- **Verify:** every contrast sentence is traceable to a passage you have read. Fix blueprint item 16 ("full text read") to reflect reality.
- **Deliverable:** related-work section with explicit read-depth.

## P0-4 Write the Evaluation and Results sections from frozen JSON
- **File:** `paper/sections/{representation,design,results}.tex`.
- **Change:**
  - Representation: V5 formula exactly as in `sbg/v5/distance_v5.py:32-34`; component weights as in audit §D.1; say the weights are fixed and were never fitted; say it is a pseudometric.
  - Design: SP/SC families, dynamic-oracle labels ("equivalent on 11 synthesised inputs"), composed pairing, program-level splits, cluster bootstrap B = 2000 seed 42, one-sided cluster permutation, Holm over H1–H6, frozen-model protocol.
  - Results: V8 negative, edit-size diagnosis, V9c-val H1–H4, V10 H1–H6, exact-size stratified AUROC (note 17–23% retention).
- **Why:** this is the paper's core and it is already fully measured.
- **Depends on:** P0-5 (tables).
- **Effort:** 2.5 h.
- **Verify:** audit Appendix 1 matrix: each sentence maps to a row.
- **Deliverable:** three LaTeX sections.

## P0-5 Generate tables from frozen JSON (read-only script)
- **File:** new `paper/build_tables.py` (outside `experiments/final/`; reads only).
- **Change:** emit Blueprint Tables 1, 2, 3, 4 (stratified), 5 (family concordance), 7 (components) and 8 (real-bug transfer) as LaTeX from `V10_INDEPENDENT_EVALUATION.json`, `V9_VAL_EVALUATION.json`, `INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json`, `EXTERNAL_RESCORE_V8.json`, `DATASET_SUMMARY_V3.json`.
- **Why:** removes transcription error; the audit recomputed these values with zero discrepancy, so the JSON is trustworthy.
- **Depends on:** P0-1.
- **Effort:** 1.5 h.
- **Verify:** compare 10 randomly chosen cells against the audit's §F.2 table.
- **Deliverable:** `paper/tables/*.tex`.
- **Safety:** open files in read mode only. Write output only under `paper/`.

## P0-6 Produce the headline figures (read-only)
- **File:** `paper/build_figures.py`; outputs `paper/figures/*.pdf`.
- **Change:** Fig. 1 forest plot of paired deltas (H2, H3, H4, H5, H6); Fig. 2 edit-size confound (V8 reversed 0.876 → V10 forward 0.616, and the edit distribution by label).
- **Why:** the existing four SVGs show obsolete V6 numbers and must not be used.
- **Depends on:** P0-5.
- **Effort:** 1.5 h.
- **Verify:** values in the plot equal the table values. Use vector PDF; check legibility at single-column width (3.5 in).
- **Deliverable:** two figures. Figs 3–4 (case study, review curve) are P1.

## P0-7 Write abstract, introduction, discussion, threats, limitations, conclusion
- **File:** `paper/sections/*.tex`.
- **Change:**
  - Abstract (IEEE Access limit is about 250 words; confirm in the template): use the exact claim in audit §P.7, and include the null (H4) and the limitation (SC-6; real-bug transfer at or below chance).
  - Threats and limitations: take the list from audit §M and Blueprint §8–9.
  - Add a disclosure paragraph: V10 was designed after the V8 and V9 results; the freeze and scored files were committed in the same commit (`c5bc130`); design-level statistics (edit-size distribution) were inspected before the freeze.
  - State the null correctly: "no statistically established gain; increments up to about 0.07 cannot be excluded".
- **Why:** abstract, introduction and conclusion are all missing.
- **Depends on:** P0-4.
- **Effort:** 2 h.
- **Verify:** run the banned-word grep (see below).
- **Deliverable:** complete text.

## P0-8 Reproducibility, data and code availability statement
- **File:** `paper/sections/availability.tex`.
- **Change:**
  - Cite the commit `93ef3f3` / GitHub `main` (`9be24b3`), Python 3.13.5, macOS arm64, `PYTHONHASHSEED=0`, and the hash manifests (`FREEZE_V10.json`, 25/25 verified).
  - **Do not claim** that CI reproduces the artifacts byte for byte (GitHub CI is currently red).
  - Report 807 tests passing locally, with the environment stated.
  - Mention that the 3.9 vs 3.13 distance shift can reach 0.41, so only 3.13 reproduces.
  - Add a licence statement (the repo has MIT `LICENSE`; confirm the BugsInPy and QuixBugs licences yourself: UNVERIFIED).
- **Why:** IEEE Access expects a data and code availability statement.
- **Depends on:** nothing.
- **Effort:** 0.5 h.
- **Verify:** every cited hash and count is quoted from the files.
- **Deliverable:** statement.

## P0-9 Author, funding, conflict and ethics declarations
- **File:** `paper/main.tex` front matter.
- **Change:** fill in author names, affiliations, funding, conflict-of-interest and acknowledgements **yourself**. The repo contains no verified affiliations. Do not invent any.
- **Effort:** 0.25 h.
- **Deliverable:** front matter.

## P0-10 Final consistency pass before submission
- **Change:**
  - Run a banned-word grep over `paper/`: `first|novel|unique|validated|detects? bugs|generali[sz]|beyond execution|V6 (is )?better|COBOL|independent(ly)?`. Review each hit.
  - Confirm "V10" always appears with "withheld" or "same author".
  - Confirm no number in the text is absent from the JSON.
- **Effort:** 0.5 h.
- **Deliverable:** clean grep.

**P0 subtotal:** about 12.5 hours of work with full serial effort. See the schedule for how to compress this.

---

# P1 — High-value improvements

| # | Task | File | Effort | Why | Verify |
|---|---|---|---|---|---|
| P1-1 | Fig. 3 (state-transition diff for Case 1 and Case 2) and a short case-study paragraph, including a failure case (Case 3 / 4a) | `paper/figures/`, data in `REPRESENTATION_CASES_traces.json` | 1 h | Shows what the representation encodes. | Matches `REPRESENTATION_CASE_STUDIES.md` |
| P1-2 | Fig. 4 review-fraction vs recall, **labelled exploratory, prevalence 50%** | `PRACTICAL_SIGNIFICANCE_ANALYSIS.json` | 0.75 h | Practical meaning. | Matches the JSON |
| P1-3 | LOPO refit paragraph (M_EX 0.885 → SBG 0.897) to explain why the frozen-M_EX comparison is not a fair "SBG beats execution statistics" | text only | 0.5 h | Pre-empts an overclaim and a reviewer attack. | Matches `INCREMENTAL_CONTRIBUTION_ANALYSIS_lopo.json` |
| P1-4 | Add a systematic-search paragraph for the §I.4 gaps (what was searched, where, when) | `paper/sections/related_work.tex` | 1 h | The repo's own position says no systematic search was done. | State queries and databases honestly |
| P1-5 | Update `FINAL_MANUSCRIPT_BLUEPRINT.md` checklist items 16–18 and rename "INDEPENDENT" in the readiness file title | repo docs | 0.5 h | The blueprint currently contradicts the evidence. Do this **after** the draft, as a separate commit. | grep |
| P1-6 | Correct stale top-level repo docs: `README.md` body, `docs/VERSION_MAP.md`, `STATUS.md`, `docs/CLAIMS_REGISTRY.yaml` | repo | 2 h | Reviewers will click the GitHub link. | `consistency_check.py` remains 10/10 (run on a copy) |
| P1-7 | Fix CI: drop the py3.9 legs or pin an OS image that has 3.9; decide whether `check_reproduction.py --strict` is byte-exact on Linux | `.github/workflows/ci.yml` | 1 h | Red CI undermines the reproducibility statement. | Green run on GitHub |
| P1-8 | `git fetch` and fast-forward local `main` to `9be24b3`; commit or discard the 4 untracked `*v8*` files; back up the `SBG FINAL` working tree | git (owner action) | 0.5 h | Removes confusion about what is on GitHub. | `git status` clean |
| P1-9 | Request a Zenodo DOI for the release | external | 0.5 h | Archival code and data citation. | DOI resolves |

**Priority inside P1:** P1-3, P1-1, P1-4, P1-5, P1-8, then the rest.

---

# P2 — Optional polish

- Fig. 2 variant with per-program AUROC strip.
- Supplementary PDF: complete H1–H6 tables, V9c-val tables, per-family concordance, post-hoc supplement (labelled).
- Notation table for the genome components.
- Short Python-version sensitivity paragraph in the threats section.
- A one-paragraph replay of the V6 correction history for the appendix.
- Regenerate the four README SVGs from the new numbers.
- Update `make help` to reflect V8–V10 flow.

---

# DO NOT DO

| Item | Why it is unsafe |
|---|---|
| Re-run, re-score or "refresh" V8, V9c or V10 | Violates the single-run freeze. Overwrites frozen data. |
| Fit new V5 weights, promote `sbg_state`, or declare a V7 | Post-hoc optimisation on a test split. `sbg_state` 0.917 was not pre-declared. |
| Tune thresholds or change the Youden τ | Frozen. |
| Promote V6 | H5 not supported. |
| Change the BugsInPy/QuixBugs input protocol, or add bug-triggering inputs | Post-hoc tuning of the failing result. |
| Drop SP-2 from the real-bug headline | The 0.497/0.444 figures are sensitivity analyses. Report all-pairs numbers as primary and SP-2-excluded as a labelled diagnostic. |
| Construct a new independent program set | Needs 2–4 weeks per the repo's own estimate. |
| Run SBG on COBOL or Java | No executable corpus exists. |
| Add new baselines to V10 | Changes the post-freeze analysis family. Any new baseline must be labelled post-hoc. |
| Merge the "SBG FINAL" clone's v7-TEST numbers | Different benchmark version. Not compatible with V10. |
| Say "SBG outperforms execution statistics" using the frozen M_EX | It is a combiner-transfer artifact. |
| Cite K&A in detail without having read it | Fabrication risk. |
| Call 19 programs "independent" or treat 638 pairs as 638 units | Wrong clustering unit. |
| Run `make check` / `verify-artifacts` in the real repo | Rewrites manifests, tables, figures and the README. |
| Switch branches in the real repo while drafting | Use a copy. |

---

# Hour-by-hour plan (single writer, 12 working hours, "today")

The first five hours can run in **parallel** across two people or two agents if available. The serial total of P0 is about 12.5 h, so the schedule below assumes some parallelism. If you are working alone, **plan on submitting the draft tomorrow** rather than compressing the literature work.

| Clock | Task | Output |
|---|---|---|
| 08:00–08:30 | P0-1 skeleton, template | compiling `main.tex` |
| 08:30–10:00 | P0-2 bibliography (verify every DOI) | `refs.bib` |
| 10:00–12:00 | P0-3 literature access and reading (K&A, Xie & Notkin, Jin, Person). **Parallel:** P0-5 tables script | related-work notes; tables |
| 12:00–12:30 | Lunch | – |
| 12:30–14:30 | P0-4 representation, design and results text | 3 sections |
| 14:30–16:00 | P0-6 figures | Fig. 1–2 |
| 16:00–18:00 | P0-7 abstract, intro, discussion, threats, limitations, conclusion | full draft |
| 18:00–18:30 | P0-8 availability statement, P0-9 declarations | front and back matter |
| 18:30–19:00 | P0-10 banned-word grep and number check | clean |
| 19:00–20:00 | P1-3, P1-1 if time | extra analysis paragraphs |
| 20:00–21:00 | Compile, read the PDF end to end once, fix overfull boxes | `main.pdf` |
| 21:00–22:00 | Independent review: give the PDF and the audit report to a second reviewer (human or a different AI) and fix only factual errors | review notes |

**Cut line.** If the literature access in 10:00–12:00 fails, keep the section with explicit abstract-level wording and still finish on schedule. If P0-4 or P0-7 slip, drop P1 entirely.

**Realistic outcome.** By the end of the day you can have a complete, scoped, accurate draft. You should **submit only after** (a) the literature wording has been checked against what you actually read, (b) the declarations are yours, and (c) a second review has found no factual errors. If any of the three is not done tonight, submit tomorrow rather than weaken the claims.

---

# Verification checklist for the final PDF

- [ ] Abstract contains the H4 null (+0.006, 95% CI [−0.069, +0.068]) and the limitations (SC-6, real-bug transfer).
- [ ] V10 is described as "withheld, same author and generator"; 19 programs are called the clusters.
- [ ] Equivalence is defined as "on protocol inputs".
- [ ] H5 is described as "not supported (Holm p = 0.090)".
- [ ] Every table cell matches a frozen JSON field.
- [ ] No "first / novel / validated / detects bugs / generalises / beyond execution statistics".
- [ ] Every BibTeX entry has a DOI or arXiv ID that was opened.
- [ ] K&A and the differential-testing papers are described at the depth actually read.
- [ ] Reproducibility statement does not claim green CI.
- [ ] Author, funding and conflict declarations filled in by the authors.
