# R6 — Associate Editor Assessment

Manuscript: "How Far Can a No-Divergence Verdict Be Trusted? False-Assurance Risk, Evidence Response Signatures, and a Pilot Study in Differential Regression Testing" (single author; IEEE Access template; compiled PDF 29 pages).

Method of assessment: read `main.tex`, `macros.tex`, all of `sections/` and `tables/` in include order, inspected the 12 figure PDFs (rasterised), page 1 of the compiled PDF, and `main.log`. Full-page PDF rendering was not available in my environment (no poppler), so I judged layout from page 1, the figure files, the table sources and the log, not from every typeset page.

---

## 1. Summary of the submission

The paper asks how often a differential-testing verdict of "no divergence observed" (NDO) is wrong. It recasts the NDO verdict as a selective prediction, defines a false-assurance risk R = P(F=1 | NDO) relative to an observation boundary O, an adjudication budget B and a population, and gives four short propositions: boundary/budget monotonicity, integrity must gate every verdict, random abstention keeps the expected risk the same, and ERS conformance is independent of accuracy. The prototype, SBG V8, adds:
- a 15-feature change-conditioned evidence profile;
- a sign-constrained logistic risk model with cluster-bootstrap thresholds (CEC);
- an integrity-first decision procedure;
- an "Evidence Response Signature" (ERS): eight properties checked by ten post-hoc evidence perturbations, i.e. metamorphic testing applied to the risk estimator;
- an HMAC-sealed evidence-collection pipeline with a threat model.

The empirical part is a pilot on 312 executed Python pairs (150 synthetic, 116 QuixBugs-derived, 46 BugsInPy units). 258 pairs have construction labels, and all are development data. The main findings:
- Plain differential testing has an observed risk of 0.169 [0.086, 0.354].
- The predecessor's gate abstains on two thirds of verdicts without lowering the rate (0.213).
- ERS found one profile defect.
- The predictive hypothesis (CEC+ERS beats coverage-only calibration by ≥5 pp) is not supported: +1.6 pp [−6.6, +16.3], with a minimum detectable effect of about 16 pp.
- No deployable threshold achieved risk control.
- An internal "five-dataset" artifact is reported as template-generated and excluded.

## 2. Fit and significance

**Fit.** In scope for IEEE Access: software testing and reliability with a formal and empirical component. The general readership will understand the question.

**Significance.** The question is good and under-studied. "What does an empty diff mean, and how often is it wrong?" matters in practice, especially now that LLM-based regression-test generators are evaluated only on the divergences they find. Two methodological points will transfer:
1. Compare abstaining procedures at matched coverage against random abstention (Prop. 3, B6).
2. Test a reliability estimator label-free, with perturbations that have known expected responses.

The candour about negative results is unusual and welcome.

The significance of what has actually been shown is limited:
- The single headline number (0.169) comes from construction labels on a corpus where all 13 gate-level false assurances are synthetic pairs (Sec. VII-C).
- The predictive contribution is null and underpowered by design (61 issued verdicts, effective n ≈ 41).
- The proposed method is numerically 4.4 pp worse than random abstention at c* (Table XVIII).
- The propositions are correct but nearly definitional; each proof is two or three lines.

In its current form this is a well-documented pilot plus a position on methodology, not a validated method.

## 3. Presentation assessment

### Title
At 25 words in three clauses it is too long, and the question form plus "Pilot Study" signals a preliminary result. Suggested: "False-Assurance Risk of No-Divergence Verdicts in Differential Regression Testing: Formulation, Evidence-Response Conformance, and a Pilot Study."

### Abstract
- Single paragraph, about 245–249 words. It meets the 150–250 limit, but only just.
- It is honest and specific, with interval and MDE reported. That is good.
- Problems:
  - "SBG V8" is introduced without expansion.
  - "the predecessor" is undefined for a reader who does not know V7-B (no citation exists for it).
  - "Three results follow" are the propositions, which are presented as findings.
  - The abstract spends about 40% of its words on negative or limiting statements, and does not say plainly what a practitioner gains.
  - It omits that the method did not beat random abstention.

### Keywords
Adequate. Consider adding "abstention" and "metamorphic testing", and dropping "software reliability" (too generic).

### Novelty within the first two pages
Partly clear. The Problem paragraph and the six-claim decomposition are effective. The "Approach" paragraph then lists four components, and the "Findings" list mixes results with project housekeeping (the five-dataset bullet). The reader reaches Table I, a page-wide contribution table with a "Status" column that is mostly qualified or negative, before seeing what is new. The novelty claim is also stated in different ways:
- "three formal results" (Sec. I and the abstract);
- "four propositions" (Table I, row C1);
- "the reformulation ... and the conformance discipline" (Sec. II-E).

### Structure
The order is logical: Intro, Related Work, Problem, Method, ERS, Trust, Design, Results by RQ, Discussion, Threats, Reproducibility, Conclusion. But Sections III–VI (formalism, method, ERS, trust) run to roughly 10 pages before any data appears. RQ5 ("scope of the evaluation evidence") is not a research question about the phenomenon: it is an audit of the author's own project artifacts.

### Length
29 pages in double-column IEEE Access format, with 23 tables, 12 figures, 6 algorithms and 76 references. IEEE Access sets no hard page limit, but this is roughly twice what the content supports. A reviewer will find the signal-to-apparatus ratio low. A target of 14–18 pages is realistic once the redundancy below is removed.

### Figures (12)
- **Fig. 1 (motivation).** Effective and the best figure in the paper. Its embedded title and footnote text duplicate the caption; remove them.
- **Fig. 2 (architecture), Fig. 3 (lifecycle), Fig. 4 (CEC).** Three full-width system diagrams. Fig. 2 has very small monospaced text that will be hard to read at print size, and it largely repeats Table V (components) and Algorithms 1–2. Fig. 3 is cited once and never discussed. Fig. 4 includes a schematic inset that is "not data". Merge these into one figure.
- **Fig. 5 (ERS framework).** A diagonal property-by-perturbation matrix: each perturbation tests exactly one property. It carries almost no information beyond a column of Table IX. Remove it.
- **Fig. 6 (threat model).** Overlaps Tables XI and XII. Keep at most one of the three.
- **Fig. 7 (evidence landscape).** Panel (c) gives a third of a full-width figure to an artifact the paper excludes as evidence. Panel (b) is a text box that repeats Table XIV. Panel (a) is useful but duplicates Table XV.
- **Fig. 8 (risk–coverage).** The two stacked panels make a tall single-column figure. Panel (b) is degenerate by construction: all models issue the same 61 pairs at c*. Drop (b), or move it to supplementary material.
- **Fig. 9 (forest).** Useful, and the one figure that summarises RQ4. The strict-policy markers are again degenerate.
- **Fig. 10 (calibration).** Five bins of about 17 pairs with Wilson intervals carry little information; it could go to supplementary material.
- **Fig. 11 (power/MDE).** Useful and should be kept. It is the key to interpreting the negative result.
- **Fig. 12 (traceability).** Shows internal filenames, commit hashes, branch names and a footnote about "Podman isolation" and "a 250-pair 'independent' validation" from internal reports. This is project process documentation, not scientific content. Remove it from the article and put it in the artifact README.

### Tables (23)
They are dense, mostly `\scriptsize`, with 7–10 columns of wrapped text. Many are prose set as tables. Major redundancy clusters:
- **ERS:** Table VIII (properties) + Table IX (perturbations) + Fig. 5 + Table X (property matrix). The "Existing evidence" column of Table VIII repeats Table X.
- **Results:** Table XVIII (statistical contrasts) + Table XXI (ablation) + Table XX (interpretation) + Fig. 9. Table XX restates Table XVIII with yes/no columns.
- **Security:** Table XI (threats) + Table XII (security outcomes) + Fig. 6.
- **Evaluation design:** Table XIII (design) + Table XIV (benchmarks) + Table XV (corpus) + Table XIX (cross-platform) + Fig. 7.
- **Related work:** Table III (positioning) + Table IV (synthesis). Table IV repeats the "Where it stops" paragraphs.
- **Threats:** Table XVI (design controls) + Table XXII (threats to validity).
- **Reproducibility:** Table XXIII (artifact provenance), lab-notebook detail better suited to the artifact.

Note: the roman numerals above are approximate. Labels are used in the text, so verify the numbering against the final PDF.

### Interpretation of figures and tables
Every figure and table is referenced at least once, which is good. Many are referenced exactly once and never interpreted, for example: Fig. 3 (lifecycle), Fig. 4 (CEC), Fig. 12, Table IV (synthesis), Table VII (cost), Table XIII (design), Table XVI (controls) and Table XXIII. Six algorithms are never referred to by number outside their own section, and Algorithm 3 (verdict generation) restates Eq. (V).

---

## 4. Major issues

### M1. The empirical evidence cannot support a journal contribution on the method's value (needs new experiments)
Evidence:
- All label-dependent results use construction labels on development data that was examined during design (Sec. III-G, Sec. VII-C, Table XVI).
- QuixBugs labels and evidence share inputs, so risk there is understated by construction.
- All 13 false assurances are synthetic.
- One cluster holds 43.8% of the labels.
- The primary contrast is null (+1.6 pp [−6.6, +16.3]) and changes sign across seeds.
- B8 is 4.4 pp worse than random abstention.
- No deployable threshold issues any verdict (Sec. VIII-D).

The paper is honest about all of this, but honesty does not convert a pilot into a validation. The author lists five unmet prerequisites for a confirmatory study (Sec. IX-D) and states that "none of these was attempted".

Fix: run at least a held-out, executed external corpus (e.g. BugsInPy/Defects4J checkouts) with independently adjudicated labels, using the already-implemented two-adjudicator protocol, at a size guided by Fig. 11. Alternatively, reposition the paper as a short methodology/position paper (estimand, matched-coverage-vs-random-abstention discipline, ERS) with the pilot as an illustration, and cut it by about half.
**New experiments: yes** for a validation paper; **no** for the repositioned short paper.

### M2. Length and redundancy: 29 pages, 23 tables, 12 figures, 6 algorithms (no new experiments)
See the redundancy clusters in Section 3. As written, the paper is very hard to referee and to read.

Concrete cuts:
- Remove Fig. 5, Fig. 12, Fig. 7(c), Table XX, Table IV and Algorithm 3.
- Merge Figs. 2–4 into one figure.
- Merge Tables XI and XII.
- Merge Tables XIII, XIV and XIX into one evaluation-settings table.
- Merge Table XVI into Table XXII.
- Move Tables VII, XXIII and the full Table VIII to supplementary material.

Target: at most 10 tables and 6 figures in the main text.

### M3. The paper reads as an internal project audit rather than a research article (no new experiments)
Evidence:
- Branch names (`research/v8-mac-hardening`), commit hashes, "dirty tree", "Linux-branch code" and "mac branch" appear throughout the results (Sec. VIII, Tables XIX, XXI and XXIII, Fig. 12).
- RQ5 and the five-dataset artifact appear in Sec. I (Findings), Sec. VII-B (category F), Sec. VIII-E, Fig. 7(c) and Table XIV.
- There are "report text only, not used" claims (608-test Linux run, container runtime).
- The footer of Table XXI is in all caps.

Readers and reviewers have no stake in an unpublished internal artifact that the author has already discarded. Bringing it into the article raises questions about what else in the project history was unreliable.

Fix:
- Delete RQ5 and every mention of the five-dataset artifact from the article; a sentence in the artifact README is enough.
- Report one code version (merge the profile fix, or report pre-fix only) and anchor it with a single archived DOI.
- Move provenance detail to the artifact.

### M4. Notation clash: property numbers versus perturbation IDs (no new experiments)
- Properties are numbered 1–8 (plus E). Perturbations are P1–P9 plus P1b. They do not align: Property 1 is tested by P2, Property 3 by P1/P1b, Property 7 by P8, Property 8 by P5.
- The text then mixes the two systems. Sec. III-B says integrity gating "is property P8"; Remark 1 refers to "P6" and "P8" as properties. Definition 5 indexes pass criteria by perturbation ID, while Table VIII indexes by property number.
- In Table VIII, row 1, "probe failed ... 227/227 after" means "passed 227/227".

Fix: give properties and perturbations one aligned scheme, e.g. properties ERS-1…ERS-9 tested by T1…T9 with matching indices, and use it everywhere.

### M5. The formal results are overstated (no new experiments)
- Prop. 1 (integrity) follows directly from an adversary who can write any content and a validator that is the only signal.
- Prop. 2 (monotonicity) follows from the two assumptions stated just before it (sound and monotone adjudication).
- Prop. 3 (random abstention) is a one-line expectation.
- Prop. 4 holds for any metric evaluated on a support set and any off-support input.

These are useful framing observations. Presenting them in the abstract as "three results" and in the contributions table as a formal contribution invites an expert reviewer to discount the paper. There is also an inconsistency: "three formal results" in the abstract and Sec. I versus "four propositions" in Table I.

Fix: present them as "observations" or "design consequences". Make the count consistent. Spend the saved abstract words on the transferable methodological message.

### M6. The novelty of ERS is modest and should be framed as such (no new experiments)
ERS is metamorphic testing (S4) applied to a risk estimator, with deletion-based validation borrowed from checked coverage (credited as the precursor of P1).
- The one substantive "defect detected" was in an unfitted all-feature probe, not in the fitted model. The fitted model retains essentially one feature (`mu_min`), and its passes on P4, P7 and P9 are vacuous by the author's own account (Sec. VIII-B).
- Three of the profile's 15 features are constant on the corpus.

The claim that ERS "exposed a profile defect invisible to aggregate metrics, confirmed under real execution" rests on 5 of 7 pairs in an exploratory run, from a dirty working tree, with no preserved run directories.

Fix: state plainly in the abstract and the contributions that the defect was found in a probe estimator. Add one ERS demonstration on an estimator that someone else would plausibly deploy, for example a model with several retained features, or a third-party estimator.
**New experiments: small** (post-hoc only, no new collection).

### M7. Reproducibility package is not citable, and an internal reference is broken (no new experiments)
- Sec. XI-A refers to "the project repository on branch research/v8-linux-validation", but gives no URL, DOI or archive.
- Sec. XI-B cites `FINAL_CLAIM_EVIDENCE_REGISTER.md`. The submission directory contains `CLAIM_EVIDENCE_REGISTER.md`; no file with the cited name exists.
- The per-run logs behind the 312 records are absent, so the earliest verifiable artifact is the derived records file (Sec. XI-A, level 3).
- The predecessor engine V7-B, which the method wraps and which serves as baseline B3, has no citation or public reference.

Fix:
- Deposit code, records and raw outputs in a public archive (e.g. Zenodo) and cite the DOI.
- Correct the filename.
- Cite or describe V7-B well enough that B3 can be reimplemented.

### M8. Submission metadata placeholders (publication blocker)
- The author affiliation and e-mail read "to be supplied by the author before submission".
- The biography is a placeholder.
- The template footer shows "VOLUME 11, 2023".

These must be completed before the manuscript can go to review.

---

## 5. Minor and editorial issues

1. The abstract is at the 250-word ceiling. Expand "SBG V8" and "predecessor", or drop them.
2. Sec. I, Findings: remove the five-dataset bullet (see M3).
3. Table I ("Contributions/Status"): a status column of "not demonstrated" or "partly supported" is unusual and self-undermining in a contributions table. Fold the status into the text or the threats section.
4. Table III (positioning): SBG V8 gets full marks (•) for "per-verdict probability" and "response to degraded evidence" while its predictive value is not demonstrated. The caveat is in the text; also add a footnote mark on the SBG V8 row.
5. Several labels on `\paragraph*` and sections are never referenced (`sec:res-robust`, `sec:cost`). Harmless, but check that `\label` inside `\paragraph*` resolves to the intended number.
6. Equation labels `eq:F`, `eq:R`, `eq:kappa`, `eq:rhat` and `eq:delta` are never referenced. Unnumber them, or refer to them.
7. Overfull hboxes: 9.3 pt (in a fragment at lines 58–58 of an input file; check the macros or the title block), 6.5 pt, and several of 1–2 pt. Fix these before production.
8. Table XXI footer: replace the all-caps sentence with normal case; "quixbugs" should be "QuixBugs"; "13-system evaluation" is unexplained.
9. Table VIII, row 1: "failed ... 227/227 after" should say "passed 227/227 after".
10. Fig. 1: remove the in-figure title and caption-like text.
11. Fig. 2: the font is too small at column width; increase it to at least 7 pt at print size.
12. Fig. 8(b) and the strict-policy markers in Fig. 9 show quantities that are equal by construction. Drop them, or grey them out with a clear label.
13. Repeated hedges such as "not demonstrated", "inconclusive" and "exploratory" occur dozens of times. Say each once, in a limitations paragraph, and then write directly.
14. Mixed British spelling ("operationalises", "behaviour") is acceptable, but be consistent with IEEE style throughout (IEEE accepts either).
15. Eight of 76 references are from 2026 and several are preprints (SemaDiff, FEAgent, EquiBench). Mark preprint status in the bibliography as well as in Table III, and check whether any have since been published.
16. Sec. VII-E ("Statistical methodology") says the hypotheses were "pre-registered", but no registry or timestamp is given, and Sec. XI-D says the prediction lock lacks an external timestamp. Use "pre-specified in the internal analysis plan" unless a public registration exists.
17. The "Non-claims" list in Sec. I is unusual but useful. Keep it, but shorten it.
18. Remove the code module names from definitions in Sec. III (e.g. `calibrate.Model.decide`); they belong in Table V or the artifact.

---

## 6. Scores (1–10)

| Criterion | Score | Justification |
|---|---|---|
| Novelty | 5 | The estimand framing and the matched-coverage-vs-random-abstention lens are useful; ERS is metamorphic testing applied to an estimator; each ingredient is acknowledged as prior work. |
| Technical contribution | 4 | A working, carefully engineered prototype, but its predictive core is not shown to work and the propositions are near-definitional. |
| Literature coverage | 8 | Broad and well organised (eight streams, 76 refs), with honest positioning; slightly padded by Table IV. |
| Experimental design | 4 | Matched coverage, a random-abstention reference, grouped CV and a cluster bootstrap are good choices, applied to development-only data with construction labels and n = 61. |
| Statistical validity | 6 | Analyses are correct and transparently reported (Holm, MDE, seeds, no equivalence claim); the sample is too small to answer the question. |
| Benchmark breadth | 3 | Python only; synthetic + QuixBugs labelled; BugsInPy unlabelled; no held-out benchmark. |
| Reproducibility | 5 | Exceptional internal traceability, but no public archive or DOI, missing per-run logs, a dirty-tree run, a wrong filename and an uncited predecessor. |
| Writing | 6 | Clear sentences and admirable candour, but the paper reads like a project audit and is repetitive and over-hedged. |
| Figures and tables | 3 | 23 tables and 12 figures with heavy redundancy, tiny fonts, degenerate panels and process figures. |
| Overall readiness | 3 | The core question is good, but the evidence is a pilot, the length is roughly double, and there are metadata placeholders. |

---

## 7. Editorial decision

**Reject and resubmit (major revision).** IEEE Access does not normally run multi-round major revisions; this is the appropriate route.

Rationale: the topic fits, the question matters, and the reporting is unusually honest. However:
- the central empirical claim about the method is null and underpowered on development-only, construction-labelled data;
- the length and table/figure redundancy are far beyond what the content supports;
- much of the text documents the author's own project history rather than the science;
- the submission contains author-metadata placeholders and lacks a citable artifact.

A resubmission should either:
- (a) add an independently adjudicated, held-out external evaluation (M1), or
- (b) reposition as a concise methodology paper of about 14–16 pages, centred on the estimand, the matched-coverage/random-abstention discipline and ERS, with the pilot as an illustration.

In either case, M2–M5, M7 and M8 must be addressed. I would not send the current version to external reviewers. Desk-returning it with this report will save reviewer effort and give the author a clear path.
