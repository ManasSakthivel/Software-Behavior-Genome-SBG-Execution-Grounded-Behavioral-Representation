# Reviewer D — Publication positioning / IEEE Access suitability (sceptical)

Scope: read-only review. Sources read: HANDOFF/{MASTER_HANDOFF_PROMPT,COMPLETED_WORK,BLOCKED_AND_FAILED_WORK}.md, `03_COMPETITOR_LANDSCAPE_AND_NOVELTY.md` (§0, §D, §E, §G.2, §H, §J), `07_EXPERIMENTAL_INTEGRITY_AUDIT.md` (§1–§3), `01_…FORENSIC_AUDIT.md` (grep only), `SBG/README.md`, `SBG/STATUS.md`, `SBG/artifacts/paper_evidence/{FINAL_SPRINT_REPORT,FINAL_IEEE_ACCESS_READINESS,CLAIM_TO_EVIDENCE_MATRIX,PRACTICAL_SIGNIFICANCE_ASSESSMENT,FINAL_MANUSCRIPT_BLUEPRINT}.md`, `SBG/docs/current/EVALUATION_PLAN_V9.md` (grep H1–H4). I did not re-run any experiment; every number below is relayed from those files. Tags: [VERIFIED-IN-FILE path] = I read it there; [INFERRED] = my reasoning; [UNVERIFIED] = not checked or general knowledge.

## 0. Bottom line

SBG is not a validated representation and not a bug detector. The only claims that survive the evidence are (a) an evaluation-methodology finding about edit-size confounds and label construction, (b) a conditional empirical result (SBG ≫ edit size on same-author synthetic Python pairs), and (c) honest nulls/negatives (no proven gain over execution statistics; no real-bug transfer). [INFERRED from the files below]. A "Negative Result"/methods-style framing is defensible for IEEE Access; a "new representation" framing is a likely reject. [INFERRED]

## 1. What SBG demonstrates vs. does not

**Demonstrates (within stated limits)**
- SBG V5 AUROC 0.897 [0.863, 0.922] vs forward edit-size 0.616 on V10 (638 pairs, 19 programs); H2 +0.254, H3 +0.281 (Holm-supported). [VERIFIED-IN-FILE SBG/artifacts/paper_evidence/FINAL_IEEE_ACCESS_READINESS.md §C; PKG/07_EXPERIMENTAL_INTEGRITY_AUDIT.md §2 — reproduced to |Δ|=0.0, 522 quantities]
- A transformation-family benchmark can be solved by edit size alone (V8-test: reversed edit 0.876 vs SBG 0.694; verdict "NOT DEMONSTRATED"). [VERIFIED-IN-FILE SBG/STATUS.md l.3; PKG/07 §2]
- Structural AST/token baselines are anti-informative on the corrected benchmark (0.105/0.169 vs SBG 0.601, ΔAUROC +0.50, Holm p=0.006) — but this is the V6-era 7-program arm. [VERIFIED-IN-FILE SBG/README.md "Corrected benchmark" table]
- A characterised blind spot (SC-6 value-only mutations: 17/23 score 0). [VERIFIED-IN-FILE CLAIM_TO_EVIDENCE_MATRIX.md A12]

**Does not demonstrate**
- Gain over edit + execution statistics (H4 +0.006 [−0.069, +0.068], Holm p=1.0; V9c-val +0.021 [−0.005, +0.048]); and the null is *not* evidence of equivalence (MDE ≈0.10 on V10; equivalence bound ≈±0.06). [VERIFIED-IN-FILE PKG/07 §1 item 5, T9]
- Real-bug transfer (BugsInPy 0.497, QuixBugs 0.444 after SP-2 exclusion; 0.410/0.388 before). [VERIFIED-IN-FILE PKG/07 §2; SBG/STATUS.md l.74]
- Independence of V10 (same author/generator; 16/19 programs >0.10 token-Jaccard to some dev program; "frozen before scoring" rests on self-reported timestamps in one commit c5bc130). [VERIFIED-IN-FILE PKG/07 T3, T7b]
- Superiority over any output-reading method (not run; label-tautology prevents a fair same-input comparison). [VERIFIED-IN-FILE PKG/03 §0 V5; PRACTICAL_SIGNIFICANCE_ASSESSMENT.md §2]
- That the representation is truly "output-free" in an information sense: tracer snapshots `repr()` of frame locals at return events; leakage untested. [VERIFIED-IN-FILE PKG/03 §0 V6 (code read by A1; experiment not run); A5E/A5F "not started" per HANDOFF/BLOCKED #7]
- Any cross-language capability (tracer is Python-only; COBOL corpus unusable). [VERIFIED-IN-FILE FINAL_SPRINT_REPORT.md "COBOL conclusion"]

## 2. Repo claims: supported / unsupported / contradicted

| Claim (location) | Status | Reason |
|---|---|---|
| "SBG V5 separates … far better than edit size … 0.875 with edit size exactly matched" (README.md Update block l.31-34) | **PARTLY SUPPORTED / needs qualification** | Number reproduces. But inside matched sets CHANGED has the larger edit in 292/319 sets and edit-size matched-set concordance (0.955) exceeds V5's (0.931); "size-matched" holds only for pooled stratified AUROC. [VERIFIED-IN-FILE PKG/07 T10] The doc itself concedes "not fully removed (92 % of V10 sets)". [VERIFIED-IN-FILE CLAIM_TO_EVIDENCE_MATRIX.md A7] |
| "composed design removes most of the confound" (matrix A7) | **PARTLY SUPPORTED** | Forward edit AUROC 0.616 is still well above 0.5; V9c-val edit concordance 0.924 vs V5 0.806 — edit size beats SBG there within sets. [VERIFIED-IN-FILE PKG/07 T10] |
| "V10 evaluation was a single run; all files were frozen before scoring" (FINAL_IEEE_ACCESS_READINESS.md §C) | **UNSUPPORTED as phrased** | Self-attested only; also FREEZE_V10 admits edit AUROC 0.616 was inspected pre-freeze. [VERIFIED-IN-FILE PKG/07 T3] |
| "H4 fails in both independent evaluations" (READINESS §F item 2) | **CONTRADICTED internally** | Same document says V10 is not independent. [VERIFIED-IN-FILE READINESS §D Blocker 2] |
| "Additional experiments needed: No — all H4 and real-bug questions are resolved" (READINESS summary table) | **CONTRADICTED** | Same file says H4 needs ~40–60 more programs; PKG/07 says H4 inconclusive; FINAL_SPRINT_REPORT lists blockers. [VERIFIED-IN-FILE] |
| "V9c-val … confirmatory validation" (READINESS §C) | **CONTRADICTED by data audit** | 16/216 EQUIVALENT change output; 67/216 CHANGED unobservable (31 %); repo's own `EQUIVALENT_LABEL_AUDIT.json` lists the 16 yet analysis keeps them. [VERIFIED-IN-FILE PKG/07 §1 item 4] README's "Known label defect" statement is absent from the README Update block. [VERIFIED-IN-FILE README.md l.24-42 — no mention] |
| "ready for manuscript drafting" / "GO within bounded scope" (FINAL_SPRINT_REPORT, READINESS §G) | **Over-optimistic vs PKG audit** | Handoff provisional gates: comparative benchmarking BLOCKED, robustness/external BLOCKED, novelty CONDITIONAL/weak. [VERIFIED-IN-FILE HANDOFF/COMPLETED_WORK.md l.19] |
| "SBG V5 beats ... structure" (README "Claim strength", 'supported') | **SUPPORTED but weak scope** | 7 programs, V6-era corpus, and AST/token baselines are structurally mismatched to transformation-induced rewrites (they rewrite source heavily by design). [VERIFIED-IN-FILE README.md l.51-55] A reviewer will call this a straw man. [INFERRED] |
| README body (l.46–365) still headlines the V6-era "0.601 [0.490, 0.706]", "13 programs" while the Update block cites V10 0.897 | **Stale / inconsistent** | Two different eras in one README; STATUS.md also says "SBG is NOT validated" and "Pending: stage 2a–4" from September. [VERIFIED-IN-FILE README.md, STATUS.md] Reviewers opening the repo will see conflicting headline numbers. [INFERRED] |
| "FINAL_NOVELTY_POSITION relies on K&A/DCI abstracts"; K&A-specific statements in RELATED_WORK_NOVELTY_AUDIT | **UNSUPPORTED** | K&A abstract-only. [VERIFIED-IN-FILE PKG/03 §0 V2, §E.1] |
| `docs/research/NOVELTY_ANALYSIS.md:286` "first sentence of any SBG abstract" | **CONTRADICTED** | ChangeGuard/Testora/PatchGuru exist. [VERIFIED-IN-FILE PKG/03 §E.1] |
| "Exact-zero scores … are the correct output" (READINESS §E item 8) | **Overstated** | 5.6 % of CHANGED V10 pairs score 0 and 63.6 % of EQUIVALENT do; ties drive AUROC half-credit. [VERIFIED-IN-FILE PKG/07 §2 note; PRACTICAL_SIGNIFICANCE §3] |
| Fitted claim "Executed statistics are a strong baseline: LOPO refit 0.885 vs SBG 0.897 (+0.012 n.s.)" | **SUPPORTED, important** | It means the headline "0.897 vs M_EX 0.791" is partly a combiner-transfer failure. [VERIFIED-IN-FILE matrix A9/A10; PKG/07 T9b] |

## 3. Candidate research questions / contributions, ranked by defensibility

1. **(Most defensible) Evaluation-methodology paper**: "How much of a trace-based change-detection signal survives edit-size control and a strong execution-statistics baseline?" Contributions: edit-size/label confound diagnosis (V8 reversed-edit 0.876), composed pairing, oracle-checked labels (V10 0/638 label errors), program-cluster statistics, honest H4 null with power analysis. Rated INCREMENTAL novelty at best; "first" unverifiable. [VERIFIED-IN-FILE PKG/03 §D rows 9,10,13; PKG/07 T5] Risk: confound is partly *self-inflicted* (a benchmark the authors built, then corrected) — reviewers may see it as fixing own artefact rather than a field-level finding. [INFERRED]
2. **Negative/null result**: "Trace-derived genome adds no demonstrated value over execution statistics, and does not transfer to real bugs." Requires a rigorous, meaningful question; H4 currently *underpowered* (≈410 programs for 80 % power at Δ=0.02 on V10), so the null is "inconclusive," not a clean negative. [VERIFIED-IN-FILE PKG/07 T9] Honest framing: "we could not show…; CI bounds ±0.07". Strengthened if combined with #1.
3. **Characterised empirical finding on triage** (exploratory): SBG ordering reaches 80 % recall with 44.7 % vs 72.5 % of list (edit). Post-hoc, 50 % prevalence by construction, no Holm family. [VERIFIED-IN-FILE PRACTICAL_SIGNIFICANCE_ASSESSMENT.md §3] Supporting only.
4. **"Validated behavioural representation"**: Not defensible. V10 not independent; V9c-val labels noisy; V6-era output-free arm 0.601 with execution stats indistinguishable; real-bug ≈ chance; state genome alone (0.917) beats full V5 (0.897) and V5's fixed weights have no ablation. [VERIFIED-IN-FILE matrix A15; README "distance formula loses to its own parts"]
5. **"Bug / regression detector"**: Contradicted (BugsInPy/QuixBugs ≤0.5; regression corpus 7/15; silent bugs 3/9). [VERIFIED-IN-FILE README "Where the representation was claimed to win"; these are from the earlier V6-era protocol — [INFERRED] still the latest]
6. **"Cross-language"**: Not testable now; SLACC (ICSE 2020) already claims cross-language dynamic clone detection. [VERIFIED-IN-FILE PKG/03 §D row 16]
7. **"Output-free genome beats output-reading differential testing"**: Untested; the label is defined by output differences on the same 11 inputs, so output-reading baselines are tautologically perfect on them. [VERIFIED-IN-FILE PKG/03 V5]

## 4. Titles / abstract claims to avoid

Avoid: "novel/first/unique"; "framework"; "genome" as an implied breakthrough (blueprint itself says so); "detects bugs/regressions"; "validated"; "outperforms/adds value beyond execution statistics"; "independent evaluation/programs"; "size-matched/size-controlled" unqualified; "output-free" unqualified (use "protocol-level: return values and prints are not read; frame-local snapshots are"); "semantic equivalence" (labels = *sample equivalence on 11 inputs*); "cross-language/language-agnostic"; "formal pseudometric" (implemented V5 is a fixed-weight L1/Jaccard sum); "practical/productivity"; "state of the art". [VERIFIED-IN-FILE FINAL_MANUSCRIPT_BLUEPRINT.md §1,§4; CLAIM_TO_EVIDENCE_MATRIX §B; PKG/03 §E.1] Additionally avoid the name collision risk "Software Behavior Genome" implying a biological/longitudinal "genome" — a longitudinal-genome claim is contradicted by Kessel FSE 2026. [VERIFIED-IN-FILE PKG/03 §D row 15] The blueprint's proposed title ("How Much Does a Trace-Derived Behavioural Representation Add? A Size-Aware, Oracle-Validated Evaluation …") is the safest one found; "Oracle-Validated" should be tempered because V9c-val labels are not clean (V10 only). [VERIFIED-IN-FILE blueprint l.8; PKG/07 §1.4]

## 5. IEEE Access suitability

**Retrieved from the web (accessed in this session)**
- https://ieeeaccess.ieee.org/about/ : "publishes articles that are of high interest to readers: original, technically correct, and clearly presented"; scope includes "Applied engineering articles … including negative results"; "binary decision process" (accept/reject); average acceptance rate shown as 20 %. [VERIFIED-IN-FILE (fetched page, not a repo file)]
- https://ieeeaccess.ieee.org/authors/submission-guidelines/ : manuscript types include **"Negative Result"** ("non-trivial theoretical or experimental negative or null result that does not support a hypothesis. Provided that the research question posed is meaningful and the study is rigorously conducted, this type of article has value"), **"Research Article"**, **"Methods"**, **"Applied Research"** ("Quantitative results for validation of the approach are expected"); AI-generated text must be disclosed in the acknowledgements; submissions with poor grammar or irrelevant/retracted references can be returned/rejected; >20 pages triggers editorial review; keywords 3–10. [fetched page]
- https://ieeeaccess.ieee.org/authors/reproducibility/ : post-publication "Code Available / Code Reviewed" badges; encourages sharing data and code in repositories. Not a pre-acceptance requirement on that page. [fetched page]
- "IEEE Access judges technical soundness, not novelty/impact" and any hard data-availability mandate were **not stated on the pages I retrieved**; treat as [UNVERIFIED general knowledge]. The "original, technically correct" wording above is the closest retrieved text; note it says *original*. [INFERRED]

**Fit assessment** [INFERRED unless noted]
- Scope: a software-engineering empirical/methods paper fits a multidisciplinary journal; "Negative Result" and "Methods" types exist. Fit is fine; **soundness is the risk**.
- Soundness weak points a reviewer will pin: (i) 19 same-author programs, program is the independence unit; (ii) H4 underpowered; (iii) V9c-val label noise (31 % CHANGED unobservable); (iv) edit-size confound residual within sets; (v) no head-to-head baseline (A4 comparative benchmark BLOCKED; no held-out predictions exist) [VERIFIED-IN-FILE HANDOFF/BLOCKED #6]; (vi) post-hoc exclusion of SP-2 negatives in external rescoring (7/40 BugsInPy SP-2 negatives invalid per repo audit; excluded after seeing results) [VERIFIED-IN-FILE SBG/STATUS.md l.95; PKG/07 §2]; (vii) results reproduce bit-identically only on CPython 3.13.x (3.9.6 flips 3,837/93,942 V10 orderings) [VERIFIED-IN-FILE HANDOFF/COMPLETED_WORK.md l.9]; (viii) PRNG/tracer details tied to sys.settrace.
- Literature context: ChangeGuard (FSE'25), Testora (ICSE'26) are direct Python same-task competitors; K&A full text unread; the repo has ≥8 wrong citations. An IEEE Access reviewer who knows ChangeGuard will ask why it is absent from the comparison. [VERIFIED-IN-FILE PKG/03 §0 V1,V7; §G.2 R1]
- Reproducibility: strong in tooling (807 tests pass, 10/10 consistency checks, hashes 533/536 match) but weak in artefact portability (single Python version; `FREEZE_V10.variants_tree_sha256` unreproducible; "35/35 trace check" is mostly a doc-string check). [VERIFIED-IN-FILE HANDOFF/COMPLETED_WORK.md l.9] Data availability: repo is public on GitHub per README; no archived DOI (Zenodo-type) is mentioned in what I read. [VERIFIED-IN-FILE README.md l.3, CITATION block; archive DOI — UNVERIFIED]
- Ethics/disclosure: corpus authorship ("authored/original") unnamed with an AI-agent workflow evident; 121 fresh programs added in one commit; GPL-3.0 ansible code inside an MIT repo. If an LLM wrote both the method and the corpus, generator bias and IEEE's AI-text/AI-content disclosure expectations apply. [VERIFIED-IN-FILE PKG/01 l.17, l.237-242; AI-text disclosure rule in fetched submission checklist]
- Risk: **desk reject: low–moderate** (format/grammar/ethics checks, disclosure issues, over-20-page length). **Reject after review: moderate–high if framed as a new representation or practical tool; moderate if framed as Negative Result/Methods with all caveats and an added independent-input baseline.** [INFERRED; I cannot predict outcomes]

**What a negative/null framing needs**
1. A meaningful question stated up front ("does a trace-derived representation add to execution statistics once edit size is controlled?"). 2. Pre-registered analysis with the actual freeze chronology disclosed as self-attested. 3. Power/MDE analysis in the paper (A3 numbers) and equivalence bounds ±0.06/±0.044 — not "no effect." 4. Fair baselines: in-distribution refit M_EX (0.885) as primary comparator, not the transferred 0.791. 5. Clean-subset sensitivity for V9c-val (V5 0.751→0.849 on 266 clean pairs; direction conservative). [VERIFIED-IN-FILE PKG/07 §1.4] 6. Full disclosure of SP-2 exclusion rationale and unfiltered external AUROCs. 7. Released code + frozen data with an archived DOI. [INFERRED]

## 6. Practical significance (practitioners)

- Demonstrated: only on synthetic, same-author transformation pairs, 50 % prevalence by construction, no precision interpretation; review-effort advantage vs edit size, not robustly vs execution stats (recall@25 % Δ vs M_EX n.s.). [VERIFIED-IN-FILE PRACTICAL_SIGNIFICANCE_ASSESSMENT.md §3, §5]
- Frozen threshold flags 65.4 % of pairs (sens 0.944, FPR 0.364); would inspect 417 pairs to find 301/319; blind to output-only edits; SP-8 extract-function false positives (median 0.42). [VERIFIED-IN-FILE same, §3]
- No tool, no human study, no real refactoring history, no CI integration. [VERIFIED-IN-FILE same §4]
- Practitioner takeaway honestly available: cheap trace statistics (call count, exceptions, coverage) from the same instrumented run are about as good as SBG; if you have inputs, comparing outputs is cheaper and dominates on value-only changes. [INFERRED from A9/A12; output-differential baseline itself not run]

## 7. Missing experiments that would change the positioning

| Experiment | Would change | Status |
|---|---|---|
| Output-reading baseline on an *independent* input battery (same inputs not used for labels) + ChangeGuard-comparator/Testora-style baseline | Moves from "SBG vs edit size" to a real comparative claim; either upgrades or kills any practical claim | A4 BLOCKED; no held-out predictions [VERIFIED-IN-FILE BLOCKED #6, #16] |
| Return-value/locals leakage ablation (strip `repr(locals)` at return events; SBG without state genome) | Decides whether "output-free" may appear in title/abstract | not started [VERIFIED-IN-FILE PKG/03 V6; BLOCKED #7] |
| Leave-one-component-out ablation + learned vs fixed weights | Decides whether "representation" or "weights" is the limit; state genome alone (0.917) > V5 | deliberately not run [VERIFIED-IN-FILE FINAL_SPRINT_REPORT §3] |
| Truly independent / human-authored programs (or real refactoring commits with all-input-validated labels) | Only route to a generalisation claim; V10 is same-author | not feasible per repo (3–6 weeks est.) [VERIFIED-IN-FILE READINESS Blocker 2] |
| ≥40–60 additional programs for H4 | Turns "inconclusive" into a meaningful null or a small positive | not done [VERIFIED-IN-FILE READINESS Blocker 1; PKG/07 T9: ≈410 programs for Δ=0.02] |
| Version-sensitivity effect on AUROC (3.9/3.11/3.14) | Reproducibility claim; currently "3.13.x only" | A5G not started [VERIFIED-IN-FILE BLOCKED #10] |
| Independent label re-audit of V8-test and V9c-train/dev | Whether early-stage conclusions (the confound story) rest on noisy labels | not done; V8 labels never audited [VERIFIED-IN-FILE PKG/07 §1 item 7] |
| Read K&A full text, Xie & Notkin, DCI evaluation sections | Related-work accuracy; could "reduce the Level-2 novelty argument" | blocked/open [VERIFIED-IN-FILE FINAL_SPRINT_REPORT "Essential" 1–2; PKG/03 §H] |

## 8. Recommended positioning (concise)

Primary: **Methods / Negative Result** — "A size-aware, oracle-checked evaluation of trace-derived behaviour-change scoring: strong over edit size, unresolved over execution statistics, no real-bug transfer." Secondary contribution: the SBG V5 representation as the *object under test*, not as the proposed solution. Do not claim novelty of the representation (rated ESTABLISHED/INCREMENTAL/UNRESOLVED-overlap). [INFERRED from PKG/03 §D]

Caveat on my own review: I relied on the PKG audit reports and the repo's own documents; I did not independently re-derive numbers, and A4-wave results were not available (nothing citable yet per HANDOFF/COMPLETED_WORK.md l.13), so any head-to-head conclusion remains open.
