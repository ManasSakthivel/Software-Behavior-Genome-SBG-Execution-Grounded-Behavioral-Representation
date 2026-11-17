# Search Strategy

Search date: 2026-11-17 (all searches that day). This was **known-item and gap-driven lookup, not an exhaustive database search**; no result counts per database exist, and no PRISMA flow is claimed.

## Sources used
| Source | Access | How used | Limits |
|---|---|---|---|
| Crossref REST API (`api.crossref.org/works`) | open | `query.bibliographic=<title> <first author>`, top 3, best title similarity; DOI lookup for corrections | HTTP 429 (1 req/s public pool) cost one full pass; abstracts present for only 14 of 107 title queries |
| arXiv API (`export.arxiv.org`) | open | ID lookup for preprints (11 included) | none observed |
| Semantic Scholar Graph API (batch, DOI ids) | open, unauthenticated | abstracts for 103 resolved DOIs (48 had one); required one retry after 429 | abstract coverage partial; abstracts may be truncated |
| Web search (5 queries) | open | gap-driven discovery (see below) | snippets only; no page read in full |
| P0 verification file | local | prior verified entries carried forward | see that file's access levels |
Not accessible / not used: ACM DL (HTTP 403 per P0), IEEE Xplore, Scopus, Web of Science, DBLP, Google Scholar, publisher PDFs (no new full texts were read).

## Per-topic search strings (applied as known-item title+author lookups; strings below describe intent and were also used as web-search seeds)
| Topic | Intent string |
|---|---|
| differential testing | ("differential testing" OR "behavioral regression testing") AND (versions OR patch OR implementations) |
| regression testing / test selection | ("regression test selection" OR "test prioritization" OR "change impact") AND (safe OR dynamic OR predictive) |
| behaviour comparison | (spectra OR "program profiling" OR "failure-inducing") AND (versions OR regression) |
| dynamic analysis | ("dynamic analysis" OR "dynamic binary instrumentation" OR "specification mining") |
| test adequacy | ("test adequacy" OR "coverage" OR "mutation score") AND ("real faults" OR effectiveness) |
| trace analysis | (trace OR "whole program paths" OR "log" OR "invariant-constrained models") AND (inference OR anomaly) |
| observability | (tracing OR observability OR "distributed tracing") AND (production OR microservice) |
| equivalence / non-equivalence | ("equivalence checking" OR "regression verification" OR "translation validation") AND (programs OR versions OR LLM) |
| metamorphic testing | ("metamorphic testing" OR "metamorphic relations") AND (inference OR survey) |
| test selection / generation | ("test generation" OR fuzzing OR concolic OR "search-based") AND (LLM OR patch OR directed) |
| nondeterminism / flaky | (flaky OR nondeterminism OR "record and replay" OR "order-dependent") AND tests |
| evidence-based analysis | ("evidence-based software engineering" OR "systematic review" OR "thematic synthesis") |
| abstention / selective prediction | ("reject option" OR "selective classification" OR calibration OR "uncertainty") AND (code OR LLM) |
| reproducibility of SE experiments | (reproducibility OR replication OR "artifact sharing" OR leakage) AND ("software engineering" OR "machine learning") |

## Web-search queries run (5)
1. verification witnesses exchangeable validated Beyer Dangl Dietsch Heizmann Stahlbauer TOSEM
2. patch testing "change not covered" inconclusive no behavioral difference observed test suite does not exercise the change regression (returned mostly medical patch testing; excluded under E4)
3. Does the test suite cover the patch? Coverage of code changes patch coverage empirical study Marinescu Hosek Cadar "Covrig"
4. LLM generate tests that expose behavioral differences between two program versions regression differential unit tests arXiv
5. EquiBench benchmarking large language models program semantics equivalence checking arXiv

## Skill script note
`search_strategy_builder.py` (litreview skill) was run on `question.json` (PICO: population = versions/changes/patches; intervention = differential testing, RTS, dynamic impact analysis, trace comparison; comparator = equivalence checking, regression verification, metamorphic testing, test generation; outcome = difference, equivalence, adequacy, flakiness, abstention, reproducibility; 1997-2026; English). It output one identical AND of four OR-groups for every database, which is too broad to execute; it was not used as the actual search.

## Known coverage gaps
Observability has only 2 included papers (tracing systems literature mostly lacks DOIs or was not reached: Dapper, X-Trace not verified). Static regression-test-selection tools, program-repair patch assessment beyond one paper, and LLM-for-testing 2024-26 work are sampled, not exhaustive. Searches were biased toward the reviewer's prior knowledge.

## Pass 2 additions (2026-11-17)
Additional web searches (about 14): LLM regression/differential test generation 2024-26; Cleverest; Shadow follow-ups; DiffKemp journal extension; PatchGuru; equivalent-mutant LLM study; PIE and checked coverage; LLM flakiness; behaviour-preservation checks; execution-trace representations; abstention for code models. Full texts were fetched from arXiv HTML pages, the Imperial/VUT author copies and an Internet Archive copy of Evans & Savoia. ACM DL remained inaccessible (HTTP 403). Searches remain biased to the reviewer's prior knowledge and the search engine's index; no counts per database exist. Not found: Shadow follow-ups after 2018, DiffKemp papers beyond ICST 2021 and TOSEM 2026 (other than theses).
