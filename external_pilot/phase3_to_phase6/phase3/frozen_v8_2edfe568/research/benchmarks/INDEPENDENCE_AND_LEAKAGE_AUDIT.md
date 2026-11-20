# Independence and leakage audit

Date 2026-11-17. Scope: which candidate sets can be called pristine for an SBG V7 holdout. "Independent" here means four things: (a) never used to build, tune, threshold or select SBG; (b) never scored with any SBG version whose result was observed; (c) no shared project, upstream lineage or near-duplicate code with a set that was; (d) construction and labelling free of SBG output (P0 GT protocol C1-C7).

## 1. Verdicts

| Set | (a) dev/tune | (b) scored+observed | (c) project/lineage overlap | Verdict |
|---|---|---|---|---|
| Base corpus, v5-v8 train/val/dev | yes | yes | self | DEV ONLY |
| v8 test, v10 independent | no | yes (V5 scored; V6 holdout H1/H2) | same transformer families and same style of base programs; v10 shares algorithm topics with QuixBugs-like programs | NON-PRISTINE |
| QuixBugs Python | no | yes (V5, V6 X1) | public since 2017 | NON-PRISTINE, burned |
| QuixBugs Java | no | no result artifact | same 40 algorithms as the Python set | NOT independent of X1 (task-level overlap); also unusable until Java SBG validated |
| BugsInPy | no | yes (V5, V6 X2, AUROC at chance) | 12 projects consumed | NON-PRISTINE, burned; the 5 unused projects (cookiecutter, fastapi, PySnooper, sanic, tornado) are NOT clean either: same dataset, same commit, same eligibility pass already enumerated them (manifest lists all 501 bugs with eligibility) |
| Tests4Py | n/a | indirect | derived from BugsInPy | REJECT |
| PyBugHive | no | no | black, cookiecutter, pandas, scrapy, spaCy also in BugsInPy; same upstream repos, different bugs | PARTIAL: 6 independent projects (discord.py, freqtrade, numpy, poetry, salt, jax); 5 overlapping projects merge into existing burned clusters, so exclude them from confirmatory clusters |
| SWE-bench / SWE-bench-Live | no | no | matplotlib overlaps BugsInPy; others distinct | Independent of SBG, usable as a project pool; issue-driven, mostly multi-file; contamination matters only for LLM baselines |
| BugSwarm, Defects4J, Bears, Bugs.jar, GitBug-Java | no | no | none with SBG sets | Independent of SBG, but Java; unusable until a validated Java SBG |
| ManyBugs, IntroClass | no | no | none | out of scope (C) |

Rule adopted: a project that appears in any burned set (BugsInPy 12 consumed projects plus the 5 enumerated ones, QuixBugs) is excluded from the confirmatory holdout, even when a new bug from it is fresh. Project overlap is the dominant leakage channel for real regressions because SBG's gains or failures can be project-idiom specific.

## 2. Leakage channels checked

1. Development leakage: V6 held out by-program splits; frozen manifests exist (artifacts/final/freeze_bugsinpy.json). Not re-audited here.
2. Observed-result leakage: the V6 holdout result (BugsInPy at chance; QuixBugs modest) is public inside the repo; any redesign motivated by those failures contaminates reuse of those sets (reports/v6_redesign/SBG_V6_FAILURE_ANALYSIS.md exists). V7 design documents read BugsInPy failures, so BugsInPy cannot be a V7 sealed holdout, only a development or smoke set.
3. Label leakage: BugsInPy negatives are SBG SP transforms; QuixBugs negatives too. They carry synthetic labels from the same transformer family SBG was developed against.
4. Time leakage: candidate fixes must post-date the freeze T0 of V7 and the training cutoff of any LLM baseline used. SWE-bench (2294 instances) and Defects4J are old; fresh evidence requires post-T0 mining (SWE-bench-Live style or own mining).
5. Construction leakage: ground truth from developer tests is independent of SBG; any witness input must come from repo tests at the parent or the truth team's generator (P0 provenance field input_source), never from SBG.
6. Selection leakage: the unit-eligibility rule (pure, stdlib-closed units) is a selection filter on projects; it is applied label-free and before any run (as for BugsInPy). Eligibility must be frozen before enumerating candidates and applied identically to all arms.
7. Duplicate leakage: lineage-level near duplicates (backports, forks) must collapse (P0 power doc section 2): MinHash Jaccard >= 0.8 or shared patch-id.
8. Public-knowledge leakage for baselines that are LLMs: Defects4J, QuixBugs, BugsInPy, SWE-bench are likely in pretraining; treat any LLM baseline result on them as unreliable.

## 3. Audit procedure before any holdout is sealed

- Compute SHA-256 of every candidate unit pair and test for equality or MinHash similarity >= 0.8 against all SBG-visible material (benchmark/, external/, artifacts/, paper/, reports/).
- Project/URL canonicalisation (forks collapse into upstream) and check against the burned-project list.
- Date filter: fix commit date strictly after T0 (the freeze date of V7 spec) for the H-P set.
- Leak audit log (hash-chained) recorded with the corpus manifest; fail if any overlap other than a declared exclusion.
- Edit-size shortcut probe (EP 6.1): edit-size-only AUROC <= 0.65, since reversed edit size already beats SBG V5 on every external set (STATUS.md).
