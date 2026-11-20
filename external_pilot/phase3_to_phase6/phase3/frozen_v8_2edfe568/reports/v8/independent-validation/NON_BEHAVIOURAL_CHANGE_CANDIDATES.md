# Non-Behavioural Change Candidates Report (Phase 2)

## 1. Objective & Cohort Description

To evaluate SBG V8's capability to correctly observe `NO_DIVERGENCE_OBSERVED` without producing spurious alarms, 50 candidate non-behavioural changes (10 per dataset) were mined and evaluated.

| Dataset | Candidate Refactoring / Docs Pairs | Target Files | Verified Clean SAME Tests |
|---|---:|---|---:|
| **Defects4J** | 10 | Config, Constants, Formatting | 10 / 10 |
| **BugsInPy** | 10 | Utility Formatters, Docstrings | 10 / 10 |
| **Bears** | 10 | Protocol Constants, Javadoc | 10 / 10 |
| **BugSwarm** | 10 | Version Helpers, Type Annotations | 10 / 10 |
| **Bugs.jar** | 10 | Module Descriptors, Routing Metadata | 10 / 10 |
| **Total** | **50** | **Formatting, Docs, Refactoring** | **50 / 50** |

## 2. Adjudication Note
These pairs represent candidate non-behavioural changes. They will be submitted alongside bug-fix pairs to blinded human adjudicators to establish whether any subtle behavioral divergence exists.
