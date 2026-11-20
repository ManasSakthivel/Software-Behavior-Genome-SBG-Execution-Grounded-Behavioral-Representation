# Third-round initial research audit
Supersedes nothing; linked from README.md. Written per the third-round brief. Static inspection only; no experiment, benchmark, probe, perturbation or statistics pipeline was run. Round-2 self-scores were treated as claims to test.

## Findings
| # | Finding | Evidence | Consequence |
|---|---|---|---|
| I1 | Round 2 understated executed evaluation: the 312-pair corpus has 31 QuixBugs, 85 QuixBugs-negative and 46 BugsInPy units (43 bugs, 12 projects), all executed (rc 0, 932 s total) | `datasets/v8/dev_records.jsonl` (`meta.run_meta`) | "No external benchmark executed" corrected to "executed as development data; none held out" |
| I2 | Closest recent work missing: FEAgent (arXiv 2610.04371, abstaining equivalence assessor), EquiBench (2502.12466) | arXiv API | Added and positioned |
| I3 | Observability stream missing: PIE, failed error propagation, coincidental correctness, oracle assessment | Crossref | 4 references added |
| I4 | Theory thin (one elementary proposition) | `problem.tex` | Three propositions with proofs added |
| I5 | No formal ERS conformance definition | `ers.tex`, `sbgv8/ers.py:_eval` | Definition added |
| I6 | Tables 2-3 in `\tiny` | `background.tex` | Redesigned |
| I7 | Redundant figures (xplat, security, taxonomy) | results/ers | Removed |
| I8 | No cost analysis | `stats.py`, `calibrate.py`, `run_meta` | Cost table added |
| I9 | Provenance uneven (no commit in Linux stats run; real-exec run on dirty tree) | run manifests | Provenance table rebuilt |
| I10-11 | Null result and design controls not tabulated | discussion/design | Tables added |

## Per criterion: why not 9, and can existing evidence fix it?
| Criterion | R2 | Blocker | Fixable without new experiments? |
|---|---|---|---|
| Novelty | 7 | Integration contribution | Partly (done) |
| Technical | 7 | Effectiveness unproven | Formal part (done) |
| Literature | 8 | Gaps I2, I3 | Yes (done) |
| Exp. design | 5 | Dev data, construction labels, no holdout | Presentation only |
| Statistics | 7 | n=61 issued verdicts, MDE ~16 pp | Presentation only |
| Benchmark breadth | 2 | Python only, no holdout | Only accurate characterisation |
| Reproducibility | 7 | Missing run dirs/logs | Presentation only |
| Writing | 8 | Length, internal-audit tone | Partly |
| Figures/tables | 8 | Dense tables, redundancy | Yes (done) |
| Readiness | 5 | Central question open | No |

Minimum new evidence for 9+: held-out multi-language benchmark execution; independently adjudicated corpus (460-1,160 NDO verdicts for a 5-pt effect); merged profile fix; Linux security re-run with metadata.
