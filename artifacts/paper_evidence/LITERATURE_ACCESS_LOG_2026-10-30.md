# Literature access log — 2026-10-30

Status: **partial; manuscript-preparation phases were NOT completed.** This file only records what was actually
attempted and read after the final sprint (commit `65c040d`). It supersedes nothing; the earlier
`RELATED_WORK_COMPARISON.md` depth tags remain the authoritative source-depth record except where this log
upgrades a source explicitly.

## 1. Kessel & Atkinson, SCAM 2019 (DOI 10.1109/SCAM.2019.00030) — full text NOT obtained

Title verified: "On the Efficacy of Dynamic Behavior Comparison for Judging Functional Equivalence"
(Marcus Kessel, Colin Atkinson, University of Mannheim; IEEE Xplore document 8930875).

| Attempt | Result |
|---|---|
| Unpaywall API (`/v2/10.1109/SCAM.2019.00030`) | `oa_status: closed`, no OA locations, `has_repository_copy: false` |
| Semantic Scholar Graph API | `openAccessPdf.status: CLOSED` |
| OpenAlex | `is_oa: false`; `any_repository_has_fulltext: false`; locations only `doi.org` and IEEE Xplore |
| `doi.org` and IEEE Xplore (curl) | HTTP 202 bot-challenge page, no paper content |
| ResearchGate (curl) | HTTP 403 |
| DBLP (curl) | bot-challenge page |
| Mannheim repository MADOC (curl) | proof-of-work (Anubis) challenge page; a browser session passed it. An exact-title search returned zero results, but a later author search ("Kessel behavior") found the record: <https://madoc.bib.uni-mannheim.de/53324/> (SCAM 2019, pp. 193–203, ISBN 978-1-7281-4938-7). **The record is metadata and abstract only; no PDF is attached** (contrast record 72759, which links a PDF). The full abstract was read there; it matches the abstract-level description already in the repository. |
| arXiv API, "behavior sampling" + equivalence | 0 results |

Conclusion: no legitimate full-text copy was found. **Nothing in the repository may claim the paper was read in
full.** Only the abstract-level description recorded earlier stands. Remains a pre-submission limitation.

Later Kessel & Atkinson papers with open copies were located (arXiv:2409.14071 "N-Version Assessment and
Enhancement of Generative AI", IEEE Software 2024; arXiv:2406.04710) and the extracted text of 2409.14071 was
searched for references to the SCAM paper (terms: SCAM, efficacy, behavior sampling, equivalence): none found.
This does not substitute for reading the SCAM paper.

## 2. Other sources

| Source | Identifier | Access outcome | Depth now supportable |
|---|---|---|---|
| Danglot, Monperrus, Rudametkin, Baudry, "An Approach and Benchmark to Detect Behavioral Changes of Commits in Continuous Integration" | arXiv:1902.08482v3 (16 Dec 2019); EMSE 25(4), 2020 | Open PDF downloaded, text extracted (35 pp.) | Sections read: abstract, introduction, §2.3–2.5, RQ answers, §6, §7 related work |
| Wei et al., "EquiBench: Benchmarking Large Language Models' Reasoning about Program Semantics via Equivalence Checking" | arXiv:2502.12466v3 (19 Sep 2025) | Open PDF downloaded, text extracted (14 pp.) | Sections read: abstract, introduction, related work, discussion, limitations. **Venue is not stated in the PDF**; cite as arXiv preprint unless a venue is verified |
| Evans & Savoia 2007 (10.1145/1295014.1295038) | | Unpaywall closed; ACM/CMU URLs returned HTML, not PDF | metadata only (its method as summarised by Danglot et al. §7.2 is a secondary description) |
| Jin, Orso, Xie, ICST 2010 (10.1109/ICST.2010.64) | | Unpaywall closed; Georgia Tech URL 404; Wayback no snapshot; CiteSeerX unreachable | metadata only (secondary description in Danglot et al. §7.2) |
| Person et al., FSE 2008 (10.1145/1453101.1453131) | | Unpaywall closed; UNL dissertation page is a landing page only. An NTRS URL tried returned an **unrelated** NASA Spinoff document (discarded) | metadata only (secondary description in Danglot et al. §7.1) |
| Podgurski & Pierce 1992; Jiang & Su 2009; Just et al. 2014 | | Unpaywall closed | metadata only |
| Ojdanić et al., TOSEM 2023 (10.1145/3530786) | arXiv:2112.14566 | Open copy exists; **not read** | metadata only |

## 3. Facts taken from the sources actually read (published statements, not our interpretation)

- Danglot et al.: behavioural change = a modification that triggers a new state for some inputs, observable as a
  test passing on one version and failing on the other (§2.3). DCI uses test amplification; evaluated on 60
  commits from 6 Java projects; DCI(SBAMPL) detected changes in 25/60 commits, DCI(AAMPL) in 9/60; applicable
  to 15.29% of commits. Their §7.2 summarises Evans & Savoia (differential testing, 38 changes in one SIR
  subject) and Jin et al. (BERT, Joda-Time, 54 version pairs, 36 differences, one confirmed regression fault).
- EquiBench: 2400 pairs, Python/C/CUDA/x86-64, six categories, 19 LLMs; equivalence defined over *all possible
  inputs*; labels from program analysis, compiler scheduling and superoptimization; states random testing
  (Jiang & Su 2009) lacks formal label guarantees. SBG's labels are protocol-input equivalence only, so the two
  are not comparable label regimes.

## 4. Consequence for claim boundaries

- No new claim is made by this log. SBG must still not be called "first", must not cite Kessel & Atkinson
  beyond its abstract, and must not describe Evans & Savoia, Jin et al. or Person et al. from first-hand reading.
- Work not done in this phase: LOPO fairness audit write-up, frozen-contribution update, IEEE Access template
  check, manuscript draft, critical review. The final-sprint verdict (`FINAL_SPRINT_REPORT.md`: ready for
  drafting with specific pre-submission blockers) is unchanged.
