# Reviewer A (NOVELTY) — adversarial memo on "Software Behavior Genome (SBG)"

Scope: read-only review of repo evidence. No experiments run, nothing under `SBG/` or existing PKG files touched. PKG = `IEEE_ACCESS_PRE_SUBMISSION`.
Sources read: `HANDOFF/MASTER_HANDOFF_PROMPT.md`; `03_COMPETITOR_LANDSCAPE_AND_NOVELTY.md` (full, cited "03 §x / Lnnn"); `results/raw/literature/EARLY_COMPETITOR_BRIEF.md` ("Brief §x"); `results/raw/literature/bibliography_verified.json`, `fetchlog.jsonl`, `text/` listing, `build_bib.py` (grep); `SBG/artifacts/paper_evidence/{FINAL_NOVELTY_POSITION,RELATED_WORK_COMPARISON,RELATED_WORK_NOVELTY_AUDIT,NOVELTY_CLAIM_TO_EVIDENCE}.md` (partial); `SBG/README.md` (grep). `01_...FORENSIC_AUDIT.md` contains no novelty/prior-art statements (grep of "novel|first|Kessel|ChangeGuard" returned only unrelated hits).

**Tag legend.** [FULL-TEXT] = the repo's own record says the full paper was read (usually the arXiv version, not the published one). [ABSTRACT-ONLY] = only an abstract was read. [METADATA-ONLY] = only a bibliographic record. [DIRECT-EXPERIMENT] = used only for (a) SBG-side numbers the repo reports from its own runs, which I did not re-run, and (b) my own recount of `bibliography_verified.json`. [QUALITATIVE-COMPARISON] = a reasoned comparison with no experiment. [UNVERIFIED] = cannot be supported from repo files. I read no external papers, so every claim about prior work inherits the repo's access level.

---

## 1. Kessel & Atkinson (SCAM 2019): exact evidence level

| Fact | Tag | Source |
|---|---|---|
| Access to the SCAM 2019 paper (10.1109/SCAM.2019.00030) is **abstract only**. IEEE is paywalled, Unpaywall says `is_oa=false`, `oa_locations=[]`, MADOC record 53324 has no PDF, CORE returned 403, and there is no arXiv copy. | [ABSTRACT-ONLY] | 03 L85, §H L369-381; `openalex/unpaywall_kessel_atkinson.json`; `fetchlog.jsonl` (last entries) |
| What the abstract supports: a behaviour-sampling study of functional-equivalence judgement. An earlier experiment suggested about 4 random tests give about 85% recognition of non-equivalence. The larger study needs ≥39 random tests, and far fewer with coverage-based generation. | [ABSTRACT-ONLY] | 03 L381; Brief §1 |
| The 36-item reference list was resolved via OpenAlex. A1 "did not see Xie & Notkin/BERT among them". This is a negative on an OpenAlex-resolved list, so it is not a statement about the paper's text. | [METADATA-ONLY] | 03 L381 |
| Representation, labels, metrics, baselines and input generation of the SCAM study are **not known**. | [UNVERIFIED] | 03 L381 |
| The "framework" description (response-value stimulus-response matrix; output-string distances; "non-equivalent as soon as one stimulus differs") comes from Kessel's **2023 PhD thesis**. Only §3.4.1, §9.1-9.2, §11.2, §16.1-16.2 were read, plus two JSS-2024 papers read partially. The thesis is not the SCAM study. | [FULL-TEXT] (thesis, partial) | 03 L170-172, L206; Brief §1 |
| The FSE-2026 Kessel vision paper (versioned run-time behaviour, behavioural fingerprints incl. call sequences) was read in full. It is a vision paper with no evaluation. | [FULL-TEXT] | 03 L173, L222 |

**What can be concluded.**
- K&A establish prior art for "compare dynamic behaviour of two implementations to judge equivalence". The title and abstract prove this. [ABSTRACT-ONLY]
- They are an output/response-sampling family member. This is inferred from the later thesis plus the abstract's "behaviour sampling" wording. [QUALITATIVE-COMPARISON]

**What cannot be concluded.**
- Any sentence of the form "K&A do not report AUROC / use manual labels / lack a size baseline / compare against formal verification". [UNVERIFIED]
- The repo's own `FINAL_NOVELTY_POSITION.md` §2 is honest on this: "Until read, any sentence of the form 'unlike K&A, SBG…' beyond … is unsupported". [ABSTRACT-ONLY]
- The repo is **internally inconsistent**. `RELATED_WORK_NOVELTY_AUDIT.md:52` and `NOVELTY_CLAIM_TO_EVIDENCE.md:52-56` still carry the wrong DOI `10.1109/SCAM.2019.00019` (Harrand et al., B93). Per 03 L291 they also assert K&A dataset/metric/baseline properties. I confirmed the wrong DOI in both files and "Verified from: IEEE Xplore title/abstract (server returned 502 on full text)" in the latter. [ABSTRACT-ONLY]
- The thesis cannot substitute for the paper. In 03 §B (L206) K&A's SCAM protocol is marked UNVERIFIED while thesis details are mixed into the same row, which invites misreading. [QUALITATIVE-COMPARISON]
- The "edit-size confound is not discussed in K&A / DCI" statement (`FINAL_NOVELTY_POSITION.md` §2; `RELATED_WORK_COMPARISON.md:47`) rests on abstract (+intro for DCI) only. 03 later read DCI in full but did not record whether DCI addresses such confounds. [ABSTRACT-ONLY]

**Verdict A1.** Any novelty claim phrased as a delta against K&A is not currently defensible. It can only be defended as "K&A (abstract-level) address test-count sufficiency for output-based equivalence judgement; SBG does not read outputs".

---

## 2. Feature-by-feature: novel, or a combination of known execution-derived features?

SBG-side facts come from 03 §B L205 / §D (A1 read the code) and from the repo's reported numbers. I did not re-run them. [DIRECT-EXPERIMENT, not re-run]

| SBG feature | Closest prior art (repo-verified IDs) | Evidence level of the comparison | 03's rating | My rating |
|---|---|---|---|---|
| Call topology (anonymised call-frequency histogram, coverage size, depth/length stats) | Path/branch/profile spectra: Reps 1997 (B10), Harrold 1998/2000 (B11/B12), Xie & Notkin 2005 (B04); WPP/API-call birthmarks (B48-B51) | **Abstract-only** for all (B12, B48 metadata-only). 03 §D L257 | Established | **Established.** The abstracts name the technique, so refuting novelty is safe. [ABSTRACT-ONLY] |
| Call-order bigrams/trigrams | K-gram birthmarks (Myles & Collberg 2005, B49), system-call birthmarks (B50), API-call birthmarks (B51), DyCLINK (B44) | Abstract-only. Brief §7 says the baseline is "almost literally SBG-V3's bigram component". | Established | **Established.** Plausible leakage of SBG's own edge to a plain k-gram Jaccard. [ABSTRACT-ONLY] |
| Exception structure (type set, rate, (fn,exc,depth) hash, transitions) | Exceptions as observable behaviour in ChangeGuard (B24, "intentional exceptions", compared by type+args) | ChangeGuard [FULL-TEXT]; BERT/K&A [ABSTRACT-ONLY]. 03 L259 admits structural (non-output) use was "not exhaustively searched". | Established | **Established or at best a minor variant.** The hash is a small variant; "not exhaustively searched" means "no prior art found" is weak here. [QUALITATIVE-COMPARISON] |
| Temporal bundle (phase entropy, loop run-lengths, causal pairs) | Generic sequence n-gram/entropy features | No specific prior art read. Absence of prior art is a bounded search (03 §F). | Incremental | **Weak.** Per the repo's own H4 null, the bundle shows no demonstrated incremental utility over execution statistics (FINAL_NOVELTY_POSITION §4 row 1: LOPO +0.010 n.s.; V10 +0.006 CI [-0.069,+0.068]). [DIRECT-EXPERIMENT, not re-run] A novel bundle with no demonstrated utility is not a contribution. |
| Abstract state-transition genome (func_idx, pre, event, post tuples over bucketed values) | Value spectra (Xie & Notkin, B04); ADABU (B14); Daikon (B13); Collector-Sahab (B18); Revealing Regressions (B19); NumericalDiff (B32); Wang-Singh-Su variable-value traces (B37) | B04, B13, B14, B18, B19, B32 **abstract-only**. B37 [FULL-TEXT]. 03 L261: "cannot close without reading Xie & Notkin and ADABU full text". | Unresolved overlap | **Unresolved overlap, and it is the main novelty risk.** The repo itself calls the state component "the strongest piece" (FINAL_NOVELTY_POSITION §4), yet it is the least cleared against prior art. Brief §4 calls value spectra "the direct prior art for output-free / internal-behaviour comparison". [ABSTRACT-ONLY] |
| "Output-free" design | Path spectra/birthmarks/DyCLINK ignore outputs by design. Xie & Notkin: deviations exposed "even when outputs are the same". | [ABSTRACT-ONLY] (B04). The strictness claim is contradicted by 03 V6: `tracer.py` L366-372 snapshots `repr(locals)` (≤100 chars) at return events. Leakage is untested. | Established idea; strictness unresolved | **Established idea, and the strict "output-free" wording is unverified.** [QUALITATIVE-COMPARISON] [UNVERIFIED] |
| Rename invariance via first-call-order anonymisation | Birthmarks (B49/B51), NumericalDiff (B32, variable-name independent), DyCLINK (B44) | Abstract-only | Established | **Established** (implementation detail). [ABSTRACT-ONLY] |
| Fixed-weight sum 0.50/0.25/0.25 of L1/Jaccard terms | Generic weighted distances | — | Established | **Established, and a risk.** Hand-set weights invite a "tuned?" challenge. 03 L264 defers this to other agents. [UNVERIFIED] |
| Pairwise CHANGED/EQUIVALENT ranking task | ChangeGuard (B24), Testora (B25), SemaDiff (B28), PatchGuru (B29), K&A (B01), DCI (B17) | Mixed: B24/B25/B17 [FULL-TEXT], B28 [FULL-TEXT] partial, B29/B01 [ABSTRACT-ONLY] | Unresolved overlap | **Not novel as a task.** Only the output-free, unsupervised score output is a differentiator, and that differentiator is also established per the rows above. |

**Net.** Every representation component is either established or has abstract-only-cleared overlap. This agrees with 03 V3 and with the repo's own "weak-to-modest" Level-1 rating (`FINAL_NOVELTY_POSITION.md` §4). I would go further than 03 on the state genome. A1 called it "unresolved", but a reviewer holding Xie & Notkin 2005 would call it a re-abstraction of value spectra unless proven otherwise. [QUALITATIVE-COMPARISON]

---

## 3. Which novelty claims are defensible, weak, or indefensible

**Indefensible (do not write):**
- Any "first/novel/unique" claim: "first formal behavioural distance", "no prior work…", "first systematic benchmark" (`docs/research/NOVELTY_ANALYSIS.md:286`, `NOVELTY_AUDIT_V5.md:204`, etc., 03 §E.1 L282-289). These are CONTRADICTED by ChangeGuard [FULL-TEXT], DCI [FULL-TEXT], and the older families [ABSTRACT-ONLY].
- "Cross-language" or "longitudinal versioned behavioural genome". Contradicted by SLACC [ABSTRACT-ONLY] and Kessel FSE 2026 [FULL-TEXT]. 03 notes they are not in current paper claims.
- Anything of the form "unlike K&A …" beyond the abstract-level distinction in §1. [UNVERIFIED]
- "All citations are to real published works" (PRIOR_ART_MATRIX footer), which is FALSE per 03 §E.2. This includes a non-existent "Sumner ICST 2011". [METADATA-ONLY]
- "Output-free" without qualification, given `repr(locals)` snapshots at return events. [UNVERIFIED]

**Weak:**
- The representation as an algorithmic contribution (Level 1). Established components, H4 null.
- The temporal bundle (no demonstrated utility).
- Task framing "unsupervised score for CHANGED vs EQUIVALENT". It overlaps ChangeGuard, whose published P/R (77.1%/69.5% on 224 annotated commits) is not comparable to SBG's AUROC on 19 programs. [QUALITATIVE-COMPARISON]

**Defensible only in bounded form (all INCREMENTAL, not STRONG):**
- **Edit-size/label confound diagnosis and composed size-matched benchmark.** Wording must stay "in the literature found". The in-repo support is edit-AUROC 0.876 reversed (V8) and 0.616 after the composed design (V10), plus 0.875 exact-edit-stratified. [DIRECT-EXPERIMENT, not re-run] Adjacent precedents are all abstract-only or partial: Yu 2022, Krinke 2025, Allamanis 2019, Chakraborty 2022 and Geirhos 2020 [ABSTRACT-ONLY / METADATA-ONLY]; Fu & Menzies 2017 [FULL-TEXT partial] is explicitly "not an edit-size-confound study". JIT-defect change-size baselines (Kamei B78, Nagappan B79) were **not verified** (03 L162-163: "size is a strong predictor is NOT verified"). So "no precedent" is [UNVERIFIED] outside the clone/ML-benchmark neighbourhood.
- **Oracle-validated labels.** Equals the mutation-kill criterion (B69-B71 [ABSTRACT-ONLY]). It is a rigour feature, not novelty. The "EQUIVALENT" label is sample-equivalence over 11 inputs only. [QUALITATIVE-COMPARISON]
- **Honest null result** (no gain over execution statistics; BugsInPy 0.497, QuixBugs 0.444 per `FINAL_NOVELTY_POSITION.md` §6 and the handoff). This is the most defensible empirical contribution, but it is a negative result on a same-author benchmark. [DIRECT-EXPERIMENT, not re-run]
- **Label tautology (V5) as a head-to-head design constraint.** Any output-reading baseline on the same 11 inputs reproduces the label by construction. This is sound reasoning from the protocol (03 L17; Brief §0), not novelty. [QUALITATIVE-COMPARISON]

**Honest top-line.** The defensible position is a methodology-plus-null-result paper (as MASTER_HANDOFF §10 provisional gate says: "novelty CONDITIONAL/weak"). A "new representation" paper is not defensible on this evidence.

---

## 4. Literature depth

### 4a. Recount of the 96 works

I recounted `results/raw/literature/bibliography_verified.json`: ABSTRACT-ONLY 66, METADATA-ONLY 12, FULL-TEXT-READ 8, FULL-TEXT-READ (partial) 10. That matches 03 L79 (8/10/66/12). [DIRECT-EXPERIMENT]

| Depth | N | Share | Works |
|---|---|---|---|
| FULL-TEXT | 8 | 8.3% | B17 DCI, B24 ChangeGuard, B25 Testora, B26 Mokav, B27 ProbeGen, B37 Wang-Singh-Su, B62 EquiBench, B89 Kessel FSE-26 |
| FULL-TEXT (partial) | 10 | 10.4% | B28 SemaDiff, B34 TRACED, B35 CodeExecutor, B36 NExT, B38 Wang-Su blended, B68 Ojdanić, B72 Fu & Menzies, B86 Kessel thesis, B87/B88 Kessel JSS-24 |
| ABSTRACT-ONLY | 66 | 68.8% | incl. B01 K&A, B04 Xie & Notkin, B05 BERT, B06 Evans & Savoia, B29 PatchGuru, all birthmark/spectra/clone/symbolic papers |
| METADATA-ONLY | 12 | 12.5% | incl. B08 Sumner 2011, B12 Harrold 1998, B15 McKeeman, B48 Myles 2004, B53 SymDiff, B76 Geirhos, B79 Nagappan |

Overall **81% of the corpus is abstract- or metadata-only**. [DIRECT-EXPERIMENT]

**Inversion finding.** By bibliography group, Group A (B01-B16: behaviour sampling, spectra, differential testing, execution comparison, Daikon, ADABU) has **0 full-text** (13 abstract-only, 3 metadata-only). The full-text reads concentrate in the recent LLM/neural/benchmark papers (groups B, C, F, I). So the works closest to SBG's *representation* (value/path spectra, birthmarks, DyCLINK, ADABU) are the least read, while the works closest to its *task* were read thoroughly. The novelty verdict on the representation is therefore the least well-supported part of the analysis. [DIRECT-EXPERIMENT] [QUALITATIVE-COMPARISON]

### 4b. Depth on the closest competitors

| Competitor | Depth recorded in 03 | Caveats |
|---|---|---|
| ChangeGuard (FSE 2025) | [FULL-TEXT] (arXiv 2410.16092v2) + repo metadata (B24) | Arxiv v2, not the camera-ready. Results (P 77.1%, R 69.5%) are as published. No head-to-head was possible: faithful reproduction is class D (needs LExecutor neural injection). Absent from the SBG repo docs entirely, which I confirmed by grep of `SBG/` returning no hit. |
| Testora (ICSE 2026) | [FULL-TEXT] (arXiv 2503.18597v3) (B25) | Published ICSE-26 version not read. Uses PR natural language SBG never sees (class D). |
| SemaDiff | 03 table B28: [FULL-TEXT] partial ("abstract/intro/eval"). Brief §9 lists it under FULL-TEXT-READ. | **Inconsistent between 03 and the brief.** Unreviewed 2026 preprint. 03 L219 also marks Java as UNVERIFIED. |
| PatchGuru | 03 B29: [ABSTRACT-ONLY] ("PDF downloaded, not read in full"). Brief §9 lists the whole group FULL-TEXT-READ. `text/patchguru.txt` (~71 KB) exists. | Another inconsistency between brief and 03. Per 03 it is the weakest-read of the four recent competitors. |
| Kessel & Atkinson | [ABSTRACT-ONLY] (§1). Thesis and FSE-26 context only. | Highest-risk gap. |
| DCI | [FULL-TEXT]. Repo docs (`FINAL_NOVELTY_POSITION.md` §1) still say "abstract and introduction read". | 03 flags a 25/60 vs 28/60 inconsistency inside DCI itself (L210). |
| Xie & Notkin 2005 | [ABSTRACT-ONLY] | Closest prior art for the state/output-free claim. |

Note that "full text" for arXiv-based items means the preprint, not the published version. For arXiv-only/unreviewed 2026 items (SemaDiff, PatchGuru, NumericalDiff, FEAgent, Impact-is-not-invalidation), 03 R10 flags them as unreviewed preprints. I did not independently verify the arXiv IDs or dates, so those remain [UNVERIFIED] by me beyond 03's Crossref/arXiv-API record.

---

## 5. Literature-coverage gaps and biases

1. **Depth inversion (§4a).** The prior art for SBG's actual features was not read in full. [DIRECT-EXPERIMENT]
2. **Recency bias.** 21 of 96 works are 2025-26, and 12 are 2026 (my recount of `year`). Many are preprints or abstract-only. [DIRECT-EXPERIMENT] Core 1992-2012 prior art is mostly closed-access, and 03 L428 lists 14 paywalled works whose full text was not obtained.
3. **Downloaded but absent from the verified bibliography/03.** `text/` contains `invariant_diffs.txt` (arXiv 1911.07988, "Invariant Diffs", Joshy & Le), `envtrace.txt` (execution-trace alignment for LLM code evaluation) and `output_equiv_oracles_miss.txt` (equivalence-invisible bug fixes in quantum transpilers). These appear in `fetchlog.jsonl`/OpenAlex search files but in no 03 table or `build_bib.py` entry (my grep). "Invariant Diffs" is directly on point for version-to-version behavioural comparison. Whether it was read is [UNVERIFIED]. That the only grep hits for these names are the fetch log, OpenAlex search results and an unrelated archive file is [METADATA-ONLY].
4. **Search was bounded and tool-limited.** OpenAlex keyword search (11 queries), forward citations, Crossref/arXiv/DBLP. DBLP was rate-limited after about 14 queries, Semantic Scholar had 429s, and Google Scholar/Scopus/WoS were not queried (03 §K L431). A "no prior work" finding is therefore weak by construction. [QUALITATIVE-COMPARISON]
5. **Adjacent areas not surveyed:** JIT defect prediction (size/churn baselines), mutant-size/subsumption, program-repair patch size, metamorphic testing, regression test selection/change-impact analysis, SE-specific statistical methodology (03 §F items 7, 9). The repo's own `FINAL_NOVELTY_POSITION.md` §3 says this wider literature "was not surveyed systematically". The edit-size-confound novelty claim is exposed exactly here. [UNVERIFIED]
6. **Python/Java/C bias, learning-heavy bias.** The 2023-26 coverage is dominated by LLM/neural execution papers, which are class D for the head-to-head and not SBG's real neighbours. Classical dynamic-analysis literature (spectra, birthmarks, relative-debugging, trace comparison) is under-read.
7. **Bibliographic hygiene.** At least 8 wrong or unfindable citations in the older repo docs (03 §E.2), including a non-existent Sumner ICST-2011 paper and the wrong K&A DOI still present in two paper-evidence files. 03 itself states "nothing from the in-repo literature files was trusted without re-verification" (L5). Residual risk is whether the manuscript reuses un-reverified entries. [METADATA-ONLY]
8. **Unverified citers.** SABER, Treefix, Condor, RippleGUItester, AgentExecutor and "False Proximity" (embedding similarity vs behavioural divergence of mutants) appear only in OpenAlex citer lists (03 L189-190). "False Proximity" is flagged as potentially relevant and remains unread. [UNVERIFIED]
9. **Name collision.** "Software behavior genome" not found in 3 OpenAlex phrasings. A negative result under a bounded search (03 V9). [METADATA-ONLY]
10. **Self-consistency of evidence.** The repo's `RELATED_WORK_COMPARISON.md` marks Podgurski, Evans & Savoia, BERT etc. as META, while 03 upgrades several to ABSTRACT-ONLY (OpenAlex abstracts). Fine, but the manuscript must cite 03's levels, not the older ones. [METADATA-ONLY]

---

## Overall judgement (novelty only)

- **Novelty gate: CONDITIONAL / weak.** The method is a recombination of established execution-derived features. The only unresolved overlap that could be fatal is value spectra (Xie & Notkin 2005) vs the state genome, and it has not been read in full. [ABSTRACT-ONLY]
- **Closest competitor, same task and language:** ChangeGuard (FSE 2025), which the SBG repo does not cite. [FULL-TEXT]
- **K&A:** treat as abstract-only; strike all "K&A do not…" sentences. [ABSTRACT-ONLY] [UNVERIFIED]
- **Recommended claims:** an evaluation-methodology contribution with a size-confound diagnosis ("in the literature found", no "first"), plus an honest strong-baseline null result. Do not claim a novel representation. Read in full, before submission: Xie & Notkin 2005, K&A 2019, Invariant Diffs, ADABU, Kamei/Nagappan, and one JIT-defect size-baseline paper.
