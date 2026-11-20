# External-validation claim decision
New file; linked from `../README.md`. No manuscript text changed by this decision.

| Candidate | Decision | Why |
|---|---|---|
| Five-dataset Linux run | **Labelled pipeline demonstration.** Not external validation | Generated cases, label-derived outcomes, no container/Java execution evidence |
| QuixBugs (earlier workstream) | **Development / tuned.** Not external | 31/40 programs in V8 dev; harness repaired after results; synthetic negatives; V5 method |
| BugsInPy (earlier workstream) | **Development.** Not external | 43/51 bugs in V8 dev; V5 method; per-case results absent |
| Bugs.jar, Codeflaws | **Generated stand-ins.** Not external | Hand-written snippets, unresolvable commit, no checkouts |
| SeqCoBench | Synthetic-mutation study, out of scope | LLM-generated transformations |

**Claims allowed in the manuscript now:** the pipeline runs end to end; 0 externally validated cases; benchmark-breadth limit stands. This is what the current RQ5, Table 11 and conclusion already say. **Not allowed:** any statement that SBG was externally validated on QuixBugs, BugsInPy, Bugs.jar, Codeflaws or the five datasets.
