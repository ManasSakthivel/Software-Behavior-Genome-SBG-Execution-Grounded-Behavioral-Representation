# Claims and evidence matrix
| Claim | Evidence | Source file/result | Verification status | Permitted wording |
|---|---|---|---|---|
| The verdict set has no equivalence outcome | closed enum, decide.py reviewed by red team | sbgv7/records.py, decide.py, INDEPENDENT_RED_TEAM_REVIEW.md | Implemented and verified | "The system never reports equivalence." |
| NO_DIVERGENCE_OBSERVED is blocked by incomplete evidence | tests incl. property test and B-1 regression | tests/v7/test_core.py | Implemented and verified (after fix 700532b8) | "Incomplete evidence yields INSUFFICIENT." |
| Isolation: process, timeout, network and write denial | probes | research/security/EXECUTION_ISOLATION_AUDIT.md, tests/v7/test_isolation.py | Verified on macOS only; Linux not tested | "Verified on macOS sandbox-exec." |
| Memory/process-count limits | RLIMIT_AS rejected on macOS; NPROC not applied | same | Not enforced (soft RSS watchdog) | "Soft memory cap only." |
| V7-B detects divergences | 0.708 vs B1 0.774 on 321 dev pairs | results/postfix/, EXPLORATORY_RESULTS.md | Evaluated, exploratory, non-pristine, V7-B shaped on this data | "On development data V7-B detected 71%, below plain differential testing (77%)." |
| V7-B lowers false assurance | 0.123 vs 0.226 | same | Exploratory; mostly outcomes moved to INSUFFICIENT; CI lower bound +4.3pp < +10pp | "Fewer false assurances, largely through abstention; not confirmed." |
| Sufficiency adds value | no label separation; B1+rep ~ B1 | red-team review | Unsupported | Do not claim. |
| Generalisation across projects | none | - | Not evaluated | Do not claim. |
| Superiority over published tools | none compared | BASELINE_IMPLEMENTATION_AND_FAIRNESS.md | Not evaluated | Do not claim. |
| Independent benchmark | all data exposed | research/benchmarks/INDEPENDENCE_AND_LEAKAGE_AUDIT.md | Unsupported | "No pristine holdout exists." |
| Runtime overhead | child-process CPU only | EXPLORATORY_RESULTS.md | Lower bound only | "Overhead not fully measured." |
| Manuscript compiles | no LaTeX available | paper/.../README.md | Not verified; reference/table checker passes | "Draft, not compiled." |
