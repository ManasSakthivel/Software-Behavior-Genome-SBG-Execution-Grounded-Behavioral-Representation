# Literature Review Protocol

Date: 2026-11-17. Type: targeted (known-item plus gap-driven) scoping review with adversarial novelty assessment. **This is not a PRISMA systematic review and makes no PRISMA claim.** It was done by one reviewer (an AI agent), without dual screening, pre-registration, or a formal risk-of-bias tool.

## 1. Review question
Which published work supports, partially covers, or pre-empts five claimed contributions of SBG (V7): (C1) a witness representation for cross-version behaviour, (C2) an explicit sufficiency record, (C3) an evidence-grounded "insufficient" outcome, (C4) reproducibility-aware (nondeterminism-aware) comparison, (C5) empirical evidence for the above.

Topic areas (14): differential testing; regression testing; behaviour comparison; dynamic analysis; test adequacy; trace analysis; observability; equivalence/non-equivalence; metamorphic testing; test selection/generation; nondeterminism/flaky tests; evidence-based analysis; abstention/selective prediction; reproducibility of SE experiments.

## 2. Inclusion criteria (declared before screening)
- I1 Peer-reviewed paper, tool paper, survey, or arXiv preprint with a stable identifier (DOI, arXiv ID) that I could resolve to bibliographic metadata.
- I2 Directly about one of the 14 topic areas AND bears on at least one of C1-C5 (e.g. compares two program versions, defines a verdict/outcome taxonomy, reports on sufficiency/adequacy of observation, flakiness/nondeterminism, abstention, or reproducibility methodology).
- I3 Foundational or canonical work for a topic (surveys, original technique papers) is admitted as background even if it does not touch C1-C5.
- I4 English. Years 1970-2026 (abstention theory needs Chow 1970; otherwise mostly 1997-2026).
- I5 Prior verified entries from `reports/v7_design/p0_reconciliation/P0_LITERATURE_VERIFICATION.md` are carried forward unchanged, with their original access levels and corrections.

## 3. Exclusion criteria
- E1 No resolvable metadata (cannot verify title, authors, venue, year) -> excluded and logged NOT VERIFIED.
- E2 Resolved record does not match the intended paper (title similarity below 0.9 or first author mismatch) -> not included.
- E3 Blog posts, vendor documentation, tool README (may be noted in text, never in the evidence matrix as a paper).
- E4 Topic off-scope (medical/other "patch testing", unrelated "metamorphic" uses).
- E5 Duplicate record of an included work (reprints, replication packages) -> merged, DOI of the paper kept.
- E6 Claims I could not tie to an accessed text are not recorded as findings (marked NOT VERIFIED).

## 4. Source types and access levels
Source types: peer-reviewed paper; tool paper; survey; preprint; book/tech report (metadata only).
Access levels used in the evidence matrix (strict):
- FULL TEXT: I read the paper body (only carried-forward prior entries qualify; this review read no new paper in full).
- ABSTRACT: I read an abstract returned by Crossref, arXiv API, or a search snippet.
- METADATA: only bibliographic record verified (Crossref/arXiv API).
Findings, method, evaluation and limitations are filled only to the extent the access level supports; otherwise NOT VERIFIED.

## 5. Process actually performed
1. Fetched the litreview skill (`borghei/Claude-Skills`, `research/litreview/SKILL.md`). The fetch tool summarised it, so I did not see verbatim text. It describes: PICO-framed question, criteria declared before screening, search strategy script, source-quality scoring, thematic synthesis, anti-patterns (criteria after results, citing without reading, unscored sources, no gap discussion).
2. Downloaded the three referenced scripts. **Used:** `search_strategy_builder.py` (run with `python3 -I`, input `question.json`): it produced one monolithic AND/OR Boolean string identical for each database and a PRISMA log template; I judged that string too coarse and used it only as a scaffold (per-topic strings are in `SEARCH_STRATEGY.md`). **Not used:** `source_quality_scorer.py` and `thematic_synthesis_builder.py` (downloaded, not run); the scorer needs per-source sample/citation data I did not have, and its scores are heuristics. Quality was instead recorded as access level plus peer-review status.
3. Reused the P0 verification file (not re-verified here).
4. Candidate generation: topic-by-topic candidate list from reviewer knowledge (known-item search) plus 5 web searches for gap-driven items (verification witnesses; patch-coverage studies; LLM differential/regression test generation; LLM equivalence benchmarks).
5. Verification: each candidate resolved via Crossref `query.bibliographic` (top-3, best title similarity), Crossref DOI lookup, or the arXiv API; abstracts were additionally pulled from the Semantic Scholar batch API where available; accepted only with title similarity >= 0.9 and first-author check. Unresolved candidates are in the exclusion log, not in the bib.
6. Screening: single reviewer, title/metadata against I1-I3/E1-E6, decisions logged in `SCREENING_AND_EXCLUSION_LOG.csv`.
7. Synthesis: narrative/thematic by topic, then adversarial classification of C1-C5.

## 6. Limitations (declared)
Single reviewer; no systematic database queries with result counts (Crossref/arXiv are lookups, not exhaustive searches); no ACM DL/IEEE Xplore/Scopus access; rate limiting (HTTP 429) cost coverage; most new entries are metadata/abstract level; absence claims ("we found none") are weak. Candidate lists are biased toward what the reviewer already knew.
