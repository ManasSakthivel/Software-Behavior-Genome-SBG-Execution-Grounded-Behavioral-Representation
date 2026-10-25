# Citation verification (remediation audit, section G)

Checked on 2026-10-25 against **Crossref** (`api.crossref.org`, bibliographic
queries) and **arXiv** (`export.arxiv.org` API). DBLP was queried but returned
HTTP 429 (rate limit), so it contributed nothing. Only titles, authors, venues,
years and DOIs from those records were compared; **no full text was read**, and
abstracts were used only where stated. Absence from Crossref is not proof that a
paper does not exist, so "not found" below means "not found by this check".

The source documents (`docs/research/PRIOR_ART_MATRIX.md`,
`artifacts/research/prior_art_summary.json`, `docs/research/NOVELTY_ANALYSIS.md`)
were written by an earlier workflow and are left byte-for-byte unchanged in the
JSON artifact. The Markdown matrix carries a correction notice and inline flags
pointing here.

## Results

| # | Citation as written in the repo | Result | What the primary record shows |
|---|---|---|---|
| 33 | Buch & Trivedi, "Learning Program Semantics with Code Representations: An Empirical Study", SANER 2019 | **Incorrect as cited** | That exact title is Siow, Liu, Xie, Meng, *SANER 2022*, DOI `10.1109/saner53432.2022.00073`. No Buch & Trivedi paper with this title was found. The nearest SANER 2019 Buch paper is Buch & Andrzejak, "Learning-Based Recursive Aggregation of Abstract Syntax Trees for Code Clone Detection", DOI `10.1109/saner.2019.8668039` (clone detection; not shown to be cross-language). The matrix's description ("AST paths, CFG, PDG embeddings; cross-language comparison") is therefore **unverified**. `NOVELTY_ANALYSIS.md` line 138 uses the same attribution. |
| 17 | Churchill, Sharma, Bastien, Aiken, "Sound Loop Summarization and Regression Verification", PLDI 2019 | **Not found; probable conflation** | No work with this title was found. The same four authors wrote "Sound Loop Superoptimization for Google Native Client", ASPLOS 2017, DOI `10.1145/3037697.3037754`. A PLDI 2019 paper by Churchill, Padon, Sharma, Aiken is "Semantic program alignment for equivalence checking", DOI `10.1145/3314221.3314596`. Which one (if either) was intended is not established; the matrix's "LibPNG case studies" and "abstract interpretation" description is unverified. |
| 39 | DeFreez, Thakur, Rubio-González, "Path-Based Function Embeddings", FSE 2018 | **Title and venue conflated; description partly contradicted** | Two records exist: (a) "Path-based function embeddings", ICSE 2018 *Companion* (40th ICSE), DOI `10.1145/3183440.3195042`; (b) "Path-based function embedding and its application to error-handling specification mining", ESEC/FSE 2018, DOI `10.1145/3236024.3236059` (arXiv `1802.07779`). The arXiv abstract describes random walks over a labeled pushdown system, function synonyms in the Linux kernel and error-handling specification mining, not "CFG paths ... API misuse detection" as the matrix says. |
| 36 | Ding, Fung, Charland, "Asm2Vec: ...", IEEE S&P 2019 | **Verified** (heading mislabelled) | Crossref: DOI `10.1109/sp.2019.00003`, 2019 IEEE Symposium on Security and Privacy, authors Ding, Fung, Charland. The entry heading reads "Meng et al. — BinaryDiff via Asm2Vec" but the citation is Ding et al.; heading should be corrected. |
| new | Person, Dwyer, Elbaum, Păsăreanu, "Differential symbolic execution" | **Verified; missing from the matrix** | Crossref: ESEC/FSE 2008 (16th ACM SIGSOFT Intl. Symposium on Foundations of Software Engineering), DOI `10.1145/1453101.1453131`. Directly relevant: it compares two program versions by symbolic summaries. |
| new | Wang, Singh, Su, "Dynamic Neural Program Embedding for Program Repair" | **Verified on arXiv; venue not confirmed here; missing from the matrix** | arXiv `1711.07163` (v4 2018-06-30). The abstract states embeddings learned from execution traces (sequences of live-variable values), which makes it the closest learned execution-trace baseline family. Publication venue was not checked and is not asserted. A second work by Wang & Su, "Blended, precise semantic program embeddings", PLDI 2020, DOI `10.1145/3385412.3385999`, was found in Crossref. |

## Consequence

* Three of the four suspect entries (33, 17, 39) cannot be cited as written.
  Replace them only after the authors consult the primary records above.
* Person et al. and Wang et al. should be added to the related-work discussion
  and the second one used to motivate the learned execution-trace baseline in
  `docs/current/EVALUATION_PLAN_V8.md`.
* Nothing in the manuscript should state that any of these papers was read in
  full on the basis of this check.
* No `.bib` file exists in the repository; there is nothing to regenerate.
