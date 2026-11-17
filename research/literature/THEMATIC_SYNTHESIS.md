# Thematic Synthesis

Basis: `EVIDENCE_MATRIX.csv` (158 rows: 7 FULL TEXT, 89 ABSTRACT, 62 METADATA; one METADATA row, Covrig, has unverified DOI). Statements below carry the access level of the cited source; "inference" marks reviewer reasoning. Cite keys are in `VERIFIED_REFERENCES.bib` (shown as author-year).

## T1. Comparing versions by execution is old; the field now generates the comparing tests with LLMs
Differential testing predates SBG's setting (McKeeman 1998, secondary; Evans & Savoia ESEC/FSE 2007, abstract: 21%/34%/21% more behaviour changes than regression testing alone on 3 subjects). Cross-version behaviour comparison appears in Shadow symbolic execution (Palikareva 2016, full text), behavioral regression testing (Jin, Orso, Xie ICST 2010, metadata), DiffGen (Taneja & Xie ASE 2008, metadata), and differential regression testing for REST APIs (Godefroid et al. ISSTA 2020, abstract). Recent LLM work (all arXiv abstracts): Mokav (difference-exposing tests; 81.7% of 1,535 Codeforces pairs), Testora (ICSE 2026 per arXiv comment; compares PR intent to behavioural differences; 19 regressions found), Cleverest/Liu et al. (FSE 2025 per arXiv comment; reaches changed code), DiffSpec, and DiffTestGen (463 PRs; 78.2% with differences exposed). Theme: finding a difference is well served; reporting what is known when none is found is not the focus of these abstracts (absence in abstracts only).

## T2. "Did the tests touch the change?" is studied as coverage, not as a verdict condition
Impact analysis papers state results hold only for observed executions (Law & Rothermel ICSE 2003, Orso et al. ICSE 2004: full text per P0). Hilton et al. ASE 2018 (abstract) and Covrig (ISSTA 2014, snippet only, unverified DOI) examine whether patches are covered. Santelices et al. (ASE 2008, metadata) and KATCH (FSE 2013, metadata) target test augmentation/high-coverage patch testing. DiffTestGen (abstract) introduces a "union coverage" metric over modified code in old and new versions as generation feedback. Theme: change coverage is measured and used to drive generation; none of the abstracts read makes coverage of the change a precondition for the output verdict (inference from abstracts; weak).

## T3. Sound equivalence work and its "unknown" outcomes
Proof-oriented tools (Godlin & Strichman, Felsing et al. full text, SymDiff, ARDiff, client-specific equivalence checking, Ramos & Engler) treat equivalence as the target and are limited by language subset or scalability (Felsing: integer-only programs of 16-53 LOC). DiffKemp (full text) already reports "not proven equal" and a separate undetermined outcome tied to missing definitions. Theme: a three-way outcome exists in static tools; its reason (missing definition, unsupported construct) is about analysability, not about whether observation sufficed.

## T4. Witnesses are mature in verification, not in cross-version behavioural testing
Verification Witnesses (Beyer et al. TOSEM 2022; FSE 2015, 2016 predecessors; abstracts) define exchangeable, independently validated artefacts for proofs and alarms. In the testing literature surveyed, witnesses are concrete difference-exposing inputs (Mokav "DET", Shadow divergent inputs replayed natively). No source read defines a standard replayable witness format for cross-version behaviour evidence (absence claim; limited search).

## T5. Flakiness and nondeterminism threaten re-execution, and are mostly studied per test, not per verdict
Empirical analysis of flaky tests (Luo FSE 2014, metadata), surveys (Parry TOSEM 2021), detectors (iDFlakies, DeFlaker, iFixFlakies, NonDex, state-polluting tests), prediction (Pinto vocabulary; FlakeFlagger; Flakify; Haben replication), industrial studies (Google, Apple, Lam ISSTA 2019 root causing), Python (Gruber ICST 2021). LLM output nondeterminism is itself a reproducibility threat (Ouyang TOSEM, abstract). Record-and-replay was not verified (rr paper not resolved). Theme: flakiness is characterised as a test-outcome property; handling flakiness inside a cross-version behavioural comparison verdict is not a topic in the abstracts read (inference). DiffTestGen's use of re-runs to filter flaky differences appeared only in a search snippet and is NOT VERIFIED.

## T6. Adequacy research warns that coverage is a weak proxy for evidence strength
Zhu et al. 1997 (adequacy survey), Inozemtseva & Holmes 2014 (title: coverage not strongly correlated with effectiveness; metadata only), Kochhar 2015, Papadakis ICSE 2018, Andrews TSE 2006, Just FSE 2014 (357 faults; 73% coupled, 17% not coupled; abstract-level in P0), Petrovic ICSE 2021. Theme: any sufficiency record based on coverage alone is contestable; mutation/real-fault coupling is partial.

## T7. Abstention is well developed in ML, thin in SE-specific verdicts
Chow 1970 (reject option), Geifman & El-Yaniv 2017, SelectiveNet, Guo calibration, conformal tutorials, Hendrickx reject-option survey (Machine Learning 2024), Kamath selective QA, Kadavath, Kuhn, and Spiess ICSE 2025 (calibration for code LMs). All abstain on model confidence/uncertainty. None of these abstain on lack of observational evidence about a program change (inference from abstracts). Risk-coverage reporting is the established evaluation vocabulary.

## T8. Evaluation reproducibility and leakage
Gonzalez-Barahona & Robles (2012, 2023), Shepperd 2014 and 2018, Tantithamthavorn TSE 2017 (metadata), Timperley EMSE 2021, Collberg & Proebsting 2016, Kapoor & Narayanan 2023, Gundersen & Kjensmo AAAI 2018, Allamanis 2019 (duplication, P0), Herzig 2013 (label noise, P0), Arcuri & Briand STVR (statistical tests for randomised algorithms), Klees et al. CCS 2018 (fuzzing evaluation), Lamb & Zacchiroli (reproducible builds). Theme: pitfalls (duplication, label noise, leakage, randomisation, artefact sharing) are well documented; they motivate, but do not substitute for, SBG's own controls.

## T9. Methodology for this review
Kitchenham et al. (ICSE 2004), Dyba et al. (IEEE Software 2005), Runeson & Host 2009, Petersen 2008, Cruzes & Dyba 2011 inform the evidence-based approach used here; this review follows them only loosely (single reviewer, no dual screening).

## Cross-cutting gaps in the evidence base (this review)
1. Observability and trace-capture systems are thinly covered (2 rows).
2. 62 of 158 rows are metadata only; their relevance statements are reviewer inference.
3. No new paper was read in full; all "not addressed" statements are absence-in-abstract and weak.
