# SBG V7 Experimental Protocol, R1

Reconciled version R1 of SBG_V7_EXPERIMENTAL_PROTOCOL.md; original preserved at reports/v7_design/_original_archive/

Status: DRAFT R1 for freeze at gate G0 (see SBG_V7_VALIDATION_AND_ACCEPTANCE_GATES.R1.md, "GATES"). Nothing here has been run. No V7 code exists. Authority order when documents disagree: P0_BINDING_DECISIONS.md (D1-D11) first, then this document. Verdicts, reason codes and sufficiency levels S0-S3 are defined once, in P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md ("SPEC"); this document cites the SPEC and never restates a sufficiency threshold. All numbers not marked "V6 fact" are proposals with a stated justification; every change from the original is logged in CHANGELOG_protocol_gates.md with the contradiction-matrix IDs that motivated it.

Companion P0 documents used: P0_BINDING_DECISIONS.md, P0_CROSS_DOCUMENT_CONTRADICTION_MATRIX.md ("MATRIX"), P0_ARCHITECTURE_RED_TEAM_REPORT.md ("RT"), P0_BENCHMARK_AND_POWER_ANALYSIS.md ("POWER"), P0_INTERNAL_ONLY_GROUND_TRUTH_PROTOCOL.md ("GT"), P0_EXECUTION_ISOLATION_VERIFICATION.md.

V6 facts this protocol is built around (unchanged, re-checked against MATRIX N-01..N-04):
- V6 holdout AUROC: v8 test 0.768, v10 0.851, QuixBugs 0.666 declared / 0.691 canonical, BugsInPy 0.505. The pre-declared claim "independent information beyond conventional features" was NOT SUPPORTED.
- Differential output comparison was strong wherever outputs were observable (v10 0.995, QB declared-evaluable 0.976) and useless where nothing activated (BugsInPy 0.502). The dominant real-world failure was observation (BugsInPy activated 57/200 = 28.5%), not modelling. Abstention on BugsInPy was 143/200 = 71.5% (76.4% only among the 55 positives).
- Of 1332 changed DEV pairs, 357 (27%) show no output difference: 61 unactivated, 180 masked internally (SBG-trace-defined, therefore NOT independent truth), 116 unresolved.
- Labels were a pure function of the mutation generator; 596 duplicate groups covered 1713 of 2392 pairs; generator fingerprinting gave GBM 0.972 falling to 0.742 leave-type-out.
- The selection rule was partly operationalised after data was seen. V7 must not repeat that.

---

## 0. What this protocol can and cannot establish (read first)

1. The primary target is V7-B: sufficiency-aware, witness-based differential comparison with adaptive exploration (D6). Internal-state value (V7-A) is an optional, gated, exploratory pilot (section 2.6); no confirmatory hypothesis depends on it (D2).
2. Confirmatory superiority is claimed only at an effect of interest of +10 percentage points (pp). +5pp is exploratory. The -2pp non-inferiority claim is DROPPED: it needs about 8000 independent divergent pairs (POWER 6.5). Paired confidence intervals are reported instead; no claim of "not worse than" is made from them.
3. With about 40 projects and about 150 divergent pairs (the original H-R target) this design is underpowered: roughly 63% power at +10pp and 22% at +5pp with a t-test (POWER 6.2), 58% and 14% with the sign-flip permutation test this protocol uses; the smallest effect detectable at 80% power is about 12.5pp (14pp at the multiplicity-adjusted alpha). The H-R target is therefore raised (section 3.2) and, if it is not met, the confirmatory claim is withdrawn rather than the threshold relaxed (K5, GATES).
4. A non-significant result is reported as inconclusive with its interval. It is never reported as evidence of equality or of no effect.
5. All simulation-derived sizes are conditional on ASSUMED discordance (pi in [0.1, 0.3]) and ICC (rho in [0.05, 0.30]). They are re-run on development estimates and amended BEFORE sealing (section 8.6).

---

## 1. Scope, units, and vocabulary

- Unit of analysis (a "pair"): (old, new, scope), where scope is a declared function/class/module entry-point set with a drivable signature.
- Verdicts (D1; pair-level, per declared scope and input set; mutually exclusive by precedence 1 > 2 > 3; full definitions in the SPEC):
  1. `DIVERGENT_OBSERVABLE`: at least one replay-confirmed witness where an observed channel (return value, exception type/message class, declared side effects) differs on aligned, deterministic-confirmed runs. Absorbing: more exploration never revokes it unless replay fails (an invalid-evidence event that voids that witness).
  2. `INSUFFICIENT(reason_code)`: no confirmed witness and (sufficiency below S1, or alignment failed, or unresolved nondeterminism, or capture incomplete, or budget/sandbox failure, or unhandled signature/entry mismatch). Reason-code vocabulary: SPEC.
  3. `NO_DIVERGENCE_OBSERVED(S1|S2|S3)`: no confirmed witness, alignment valid, sufficiency at least S1. S0 is never a NO_DIVERGENCE_OBSERVED level; a pair at S0 is INSUFFICIENT.
- There is no equivalence verdict. `EQUIVALENT`, `SAME`, `PASS`, `VERIFIED` and "implicit pass" are prohibited as outcomes in tables, code and prose. Bounded equivalence exists only as the separately named formal claim `BOUNDED_EQUIVALENCE_PROVEN` from the optional formal tier, with its stated domain; it is not a verdict and enters no metric here.
- Sufficiency S0-S3: one definition, in the SPEC (conjunction of floors on separately reported factors; thresholds are UNVALIDATED defaults until a development split calibrates them; the plateau criterion cannot confer S3 on its own, D3). This protocol never restates those thresholds. Where a sentence below says "S2", it means "the level as defined in the SPEC".
- Advisory annotation `internal_divergence` (none | observed | unknown) may be attached to NO_DIVERGENCE_OBSERVED or INSUFFICIENT pairs, and only if the optional state-abstraction module E is enabled (D2, D5). It is not a verdict, never changes a verdict, and is not counted as divergence anywhere.
- Channel configuration (observed channels, normaliser, message channel on/off) is recorded in every verdict (MATRIX V-05). Default: return value, exception type, declared side effects; exception message OFF.
- Budget unit: CPU-seconds only (section 7).

### 1.1 Metric definitions (single definitions used everywhere)

- Eligible pair: passes the pre-declared inclusion rules (3.2); excluded units stay in the excluded-units ledger.
- Truth classes: five (section 3.5): observable divergence, internal-only (pilot only), representation-only, unactivated changed region, insufficient/ambiguous.
- Det(B) = P(verdict = DIVERGENT_OBSERVABLE | truth = observable divergence) at CPU budget B, denominator = ALL truly divergent eligible pairs (INSUFFICIENT counts as non-detection).
- False assurance (FA), the single definition for ALL systems: a pair whose adjudicated truth is observable divergence and whose emitted verdict is `NO_DIVERGENCE_OBSERVED(any S)`. FAR(B) = FA count / all truly divergent eligible pairs. An abstaining system (INSUFFICIENT) makes no assurance claim and is not a false assurance; it is penalised through decided coverage and Det, not through FAR. No system, baseline included, is credited with an "implicit pass".
- Decided coverage = share of ALL eligible pairs whose verdict is DIVERGENT_OBSERVABLE or NO_DIVERGENCE_OBSERVED. This is distinct from activation rate (changed region executed on both versions) and from determinism-confirmed rate; the three are always reported as three named quantities (MATRIX X-07). "Coverage" without a qualifier is not used.
- False alarm: a DIVERGENT_OBSERVABLE verdict on a pair whose final adjudicated truth is representation-only, internal-only or behaviour-equivalent on the declared domain. A replay-confirmed witness on such a pair is routed through the refutation channel (GT 2.6): if the truth harness reproduces the difference inside the declared domain the label is revised to observable divergence; otherwise it stands and is logged (outside-domain witness or contract artifact).
- Risk (H5) = P(error | decided), error = FA, or false alarm; decided as above.
- Hard stratum: truth = observable divergence AND the outputs of the common seed corpus (run by the truth harness, never by V7) are equal on both versions. Exploratory stratum only (section 2).

---

## 2. Research questions and hypotheses

All directions are fixed now. Confirmatory tests are run on the sealed holdouts only (3.3). DEV/DEV-N sets are for development and gate decisions, never for confirmatory claims.

Status key: CONF = confirmatory (in the Holm family); CHECK = correctness check with a pre-declared bound, not a significance test; EST = estimation with interval, no pass/fail beyond the stated consequence; EXPL = exploratory; PILOT = exploratory pilot (V7-A only).

| H | Question | Status | Where evaluated |
|---|---|---|---|
| H1 | witness validity | CHECK | H-R, H-M |
| H2a, H2b | detection at equal CPU budget vs like-for-like B1-directed / B2-directed | CONF (Holm family) | H-R (decision); H-M (directional replication, 2.7) |
| H3 | time to first witness | EST | H-R, H-M |
| H4 | false-assurance reduction | CONF (Holm family) | H-R (decision); H-M (directional replication) |
| H5 | risk-coverage | EST (coverage floor is a success condition, GATES C) | H-R, H-M |
| H6 | calibration of S levels | EST | pooled holdouts |
| H7 | internal-state views add information | PILOT / EST, never CONF | authored pilot suites (2.6) |
| H8a/b/c | internal-only annotation / false alarm / representation-only control | PILOT / EST, never CONF | H-M quota items (2.6) |
| H9 | generalisation | EST | leave-project/family-out, holdouts |
| H10 | learned scorer (only if J is built) | CONF in its own separate family | sealed holdouts (2.5) |

### 2.1 RQ1 validity
- H1 (CHECK): witness validity rate (DIVERGENT_OBSERVABLE witnesses replay-confirmed in a fresh sandbox, 5 replays, same difference and locus) >= 0.99 with a lower 95% cluster-bootstrap bound >= 0.97. Secondary: oracle-confirmed validity (the difference is an interface difference per truth, not a contract artifact) >= 0.95. Near-tautological for a replaying system (RT Q1), so it is a gate, not a performance claim.

### 2.2 RQ2 detection at equal cost (CONF)
Comparators are like-for-like (D7, section 4). Let V7 denote the diff-aware explorer when it uses the static changed-region map (permitted by D11); its primary comparators receive the same diff-derived information.
- H2a: Det(60 s) of V7 exceeds Det(60 s) of B1-directed by at least +10pp (effect of interest), one-sided superiority, paired on identical pairs, cluster sign-flip permutation test, Holm-adjusted.
- H2b: same against B2-directed.
- The 10 s and 300 s budgets, the diff-blind contrast (V7-diff-blind vs B1-blind and B2), the hard stratum, and any +5pp contrast are EXPL/EST: reported with paired cluster-bootstrap CIs and never used for a pass.
- No non-inferiority hypothesis exists. The paired CI of Det(V7) - Det(comparator) is reported at every budget and the report states that it does not establish "not worse".
- H3 (EST): TTFW in CPU-seconds including all V7 overhead, right-censored at budget; RMST ratio at 300 s on truth-divergent pairs, with CI. Pre-declared direction: ratio below 1. No numeric pass threshold (it is not powered; POWER does not simulate it).

### 2.3 RQ3 false assurance (CONF) and abstention (EST)
- H4: FAR(60 s) of V7 is lower than FAR(60 s) of B1-directed-with-the-same-sufficiency-gate by at least 10pp absolute (effect of interest), at matched decided coverage with decided coverage >= 0.60 for both arms, paired, cluster sign-flip, Holm-adjusted. FAR is computed under the single definition in 1.1; "no difference found = pass" is not a comparator. The original alternative branch ("relative reduction >= 25%") is retained as EXPL only: it equals +10pp only when FAR(B1) = 0.40 and falls to +5pp at FAR(B1) = 0.20 (POWER 6.1).
- Per sufficiency level: P(NO_DIVERGENCE_OBSERVED at S3 | truth divergent) <= 0.10 on real regressions is a calibration claim (H6), not a Holm test.
- H5 (EST): risk-coverage curves for V7 vs B1-directed+gate and B2-directed+gate at coverage 0.6, 0.7, 0.8, AURC with cluster-bootstrap CI. Minimum useful decided coverage on H-R >= 0.60 (V6 fact: BugsInPy 28.5%); this floor is a success condition (GATES C.1), not a hypothesis test. A FAR win with decided coverage below the floor does not count.
- H6 (EST): (i) ordering of miss rates S1 > S2 > S3 (cluster-bootstrap CI of adjacent differences); (ii) ECE against nominal miss-rate caps S1 <= 0.35, S2 <= 0.20, S3 <= 0.10 (UNVALIDATED defaults; they are claims about observed miss rate, not definitions of the levels, which live in the SPEC; they may be revised only by a class-B amendment before G6); (iii) abstention informativeness: Div share among INSUFFICIENT vs decided, with the pre-declared reading that abstention does not hide a Div rate higher than base by more than 10pp (V6 fact: abstained pairs were 43% changed against a 56% base rate).

### 2.4 RQ5 generalisation (EST)
- H9: project-disjoint / family-disjoint results relative to leave-project-out DEV-N: Det drop and FAR increase with CIs; ordering of S levels. Reference bounds (Det drop <= 10pp, FAR increase <= 5pp) are descriptive targets; they are not powered and are used as gate criteria only on DEV-N leave-out (GATES rows 13-14, G5).

### 2.5 RQ6 learned scorer (only if layer J is built; off by default, D5)
- H10: AUROC reported ONLY for the scoring layer, as paired delta vs conventional features (edit size, token/AST distance, exec volume), V5, V6, and the differential score. Direction: scorer+conv > conv by >= +0.03 AUROC, paired, on >= 2 sealed holdouts. Tested in a separate Holm family {H10 per holdout}, independent of the primary family. Sizing for H10 has not been simulated (unresolved, CHANGELOG U-8). AUROC is never a headline for the verdict system.

### 2.6 V7-A exploratory pilot (D2, D6; PILOT, not part of success criteria)
Attempted only after V7-B shows headroom on the sealed holdout (decided coverage >= 0.60 and FAR >= 10% on H-R, per RT "Recommendation on V7-A") and only by the conditions below. It is never a precondition for V7-B success.
- Scope: optional module E on authored-by-construction mutants (H-M pilot subset) with an independent reference state-dump tool (GT 2.1-2.2). No real-regression confirmatory use.
- Effect of interest +10pp interface-witness yield (Det) on the hard stratum at equal CPU, one primary metric, paired cluster-bootstrap lower bound > 0; time box <= 12 weeks; cost cap <= 12 engineer-weeks; kill on failure.
- H7 (PILOT/EST): Delta Det(300 s) on the hard stratum, full V7 (with state-guided exploration) vs V7 without internal-state views, paired. Power (POWER 6.7): about 41 hard pairs in H-R gives 6% at +3pp, 8% at +5pp, 26% at +10pp; no feasible size reaches +3pp. Therefore H7 is reported as an estimate with its interval and the label "inconclusive" unless the lower bound exceeds 0; a null on H7 is uninformative about the mechanism and is never reported as "internal state does not help". The original "+3pp or RMST <= 0.85 on both H-R and H-M" rule is withdrawn. Pre-declared fallback: V7-B stands on its own claim set; the report says internal-state views were not shown to add information.
- H8a (PILOT/EST): among truth internal-only pairs where the state view fires, the share carrying `internal_divergence = observed`; reported with a one-sided 95% lower design-effect-adjusted bound against 0.70. The point-estimate-only reading is not accepted (no error control). Requires >= 100 internal-only items in >= 40 base programs when the true rate is >= 0.85 (POWER 6.8).
- H8b (EST only): rate of DIVERGENT_OBSERVABLE verdicts on internal-only truth pairs, reported with its one-sided 95% upper bound (for example 0 of 38 gives about 7%). The "<= 1%" claim is dropped: it needs >= 600 internal-only items in >= 150 independent clusters and label contamination below 0.5% (POWER 6.8).
- H8c (EST, registered for circularity control C12): `internal_divergence = observed` rate on representation-only truth pairs; cap to be fixed on DEV-N before sealing.
- Labels for the pilot: the P0 ground-truth protocol (GT) applies to this pilot only. Internal-only is never counted as Div, never in the Det/FAR denominators, and a DIVERGENT_OBSERVABLE on it is a false alarm.

### 2.7 Multiplicity and claim ladder
- Primary confirmatory family (Holm, two-sided alpha = 0.05 familywise): {H2a, H2b, H4}, m = 3. H1 is a CHECK and sits outside the family. H10, if J is built, is its own family. Everything else is EST/EXPL/PILOT, reported with unadjusted CIs labelled "exploratory" (Benjamini-Hochberg shown for reference).
- Decision rule (replaces the original "positive on H-R AND H-M" ladder, which has joint power below 15% at the proposed sizes; POWER 6.7 logic): H-R carries the confirmatory decision. SUPPORTED = Holm-adjusted p < 0.05 on H-R for the test AND point estimate in the favourable direction on H-M with its CI reported. PARTIAL = significant on H-R only with H-M point estimate non-favourable, or the reverse. NOT SUPPORTED otherwise. INCONCLUSIVE = interval includes both 0 and the effect of interest and the sample met the K5 counts. No claim is made from regression sets. The H-M directional condition is a judgment recorded for PI sign-off (CHANGELOG U-3).

---

## 3. Data

### 3.1 Legacy benchmark inventory and status (unchanged)

| Set | Content | Status | Permitted use |
|---|---|---|---|
| V5/V6 DEV (v8 train+val, 57 programs, 2392 pairs) | synthetic SC-/SP- mutants | non-pristine, heavy duplication, generator-determined labels | development, unit/regression tests, validation-matrix seeds |
| v8 test (26 programs in the benchmark; 22 clusters evaluated, 967 pairs; MATRIX N-02) | synthetic | NON-PRISTINE | labelled regression set only |
| v10 (19 programs, SC+SP composites) | synthetic | NON-PRISTINE | labelled regression set only |
| QuixBugs (declared/canonical) | small real bugs | NON-PRISTINE; 36 declared pairs have no inputs | labelled regression set; input-less cases test INSUFFICIENT honesty |
| BugsInPy | real bug fixes | NON-PRISTINE; V6 activated 28.5% | labelled regression set; substrate-coverage target; never confirmatory |

Rule: these five are never called pristine, never appear in a confirmatory table, and every table including them carries "NON-PRISTINE (development/regression)". Any parameter chosen with them visible is a development parameter; thresholds shaped by V6 failure lists on them (K2 and K3 values) are listed as a "contaminated design prior" (RT Q5(g)).

### 3.2 Holdouts (constructed before implementation completes; sealed before G5 closes)

Counting units (applies to every set; POWER 2). Four counts are reported for every set and sample targets bind the LAST applicable one, not pairs:
- Pair: raw (old, new, scope) record after eligibility filtering.
- Independent project: distinct repository (URL, package name, source hash; forks collapse into upstream). H-M analogue: base program.
- Independent change lineage: pairs descended from one logical change (cherry-pick/backport/merge across branches or forks, revert-and-reapply, one mechanical refactor applied in many files, several mutants from one template on one base function). Operationally: shared commit patch-id or MinHash Jaccard >= 0.8 on the normalised AST diff. A lineage counts once.
- Independent cluster: unit of resampling and inference. Primary cluster = project (H-R) or base program (H-M); projects (programs) linked by a shared lineage merge into one cluster (union-find over lineage edges). The cluster count K is what every power figure and every minimum below refers to.
- Reporting rule: every table lists raw pairs, de-duplication groups, independent lineages, independent clusters, mean/max cluster size, estimated ICC, design effect 1 + (m - 1)rho, and Kish effective sample size. In simulation, 150 divergent pairs in 40 projects with about 2 pairs per lineage (75 lineages) drop +10pp power from 63% to 45% (POWER 2): a "pairs" target is a floor on lineages, not on pairs.

Duplicate handling (replaces the original single-line independence check):
- Near-duplicates are detected by normalised-AST hash groups plus MinHash (Jaccard >= 0.8) and shared patch-id.
- At most 3 pairs per lineage enter the primary denominators (the earliest 3 by pre-declared deterministic order); the rest go to a lineage-duplicates appendix and are excluded from primary analysis.
- At most 8 divergent-plus-control pairs per project (binding). The original "5% of the corpus per project" rule is dropped as redundant at these sizes (5% of 300 is 15, so 8 is the binding cap; MATRIX X-11); it is reported, not enforced.
- Zero duplicate groups across splits (DEV, DEV-N, H-R, H-M, H-P, H-X, legacy sets) are required; otherwise the item is removed from the later-sealed set.
- Analyses weight by group (effective sample) and report both raw and group-collapsed results.

H-R: fresh real-regression corpus (the only primary confirmatory set).
- Source: Python projects NOT in BugsInPy, QuixBugs or V5/V6 base programs; project-disjoint verified by repository URL, package name and source-hash overlap.
- Time-awareness: only commits dated after a freeze date T0 declared at G0 and after the last day any V7 development data was collected; the project list is frozen by hash before commits are examined.
- Observable-divergence pairs: (parent, fix) commits where a regression test added by the fix fails on parent and passes on fix. Scope = the function/class set the fix touches with an extractable drivable signature.
- Controls: (parent, child) commits classified as behaviour-preserving (formatting, rename, extract/inline, type-hint-only) AND full test suite passing unchanged on both; truth still requires adjudication (3.5). Most controls are expected to land in representation-only or insufficient/ambiguous (the universal "no output difference" claim needs T1-b or T2 evidence, GT 2.3); internal-only controls are expected to be rare in H-R and are reported descriptively only. Each project contributing divergent pairs should contribute at least one matched control where available.
- Size targets (replace the original ">= 40 projects, >= 150 Div pairs"): planning target >= 80 independent projects and >= 320 independent-lineage divergent pairs (about 4 per project), at least as many controls as the truth pipeline can establish; hard floor for any confirmatory claim (K5, D9): >= 60 independent projects and >= 250 independent divergent pairs, with >= 20 mixed-class projects. The 80/320 target is the multiplicity-adjusted requirement for 80% power at +10pp (central case pi = 0.2, rho = 0.15, POWER 6.4); 60/250 is the unadjusted requirement. Feasibility of mining 60-80 fresh post-T0 projects with regression tests is NOT demonstrated and is an open risk (CHANGELOG U-1).
- Dataset-quality gate: edit-size-only shortcut AUROC on the corpus <= 0.65; if higher, the edit-size-matched subset is co-primary. Additionally a diff-shape control (RT Q5(b)): report verdict and sufficiency against label within edit-size tertiles, and the AUROC of a diff-only classifier on the sufficiency-vector components excluding witnesses; require <= 0.65 or report the matched subset as primary.
- Excluded units (rule fixed before mining, ledger kept): needs network or external service, GPU/hardware, interactive input, undrivable signature (counted, reported, not silently dropped).

H-M: newly authored mutants with independent oracles (replication and mechanism set; confirmatory only if it meets the same K5 counts).
- Base programs: >= 60 (original >= 40), drawn from sources disjoint from V5/V6 base programs. Authors did not implement V7 and have not seen V6 generator output beyond family descriptions; they follow a written authoring brief. An optional LLM-authored family is tagged by author type with model identifier and prompt recorded and analysed separately; LLM-authored items are never adjudicated by an LLM.
- Families: >= 6 NEW families, each containing both observable-divergence and no-output-difference members so family is not label-predictive. Suggested: rarely-reached branch guards; boundary-only divergences; state-accumulation divergences exposed after k calls; masked internal changes; exception-type changes; side-effect-only changes; equivalence-preserving refactors verified by bounded exhaustive check.
- Independent oracle: each item ships a specification-level reference written without access to V7 outputs. The "no output difference" claim requires T1-b (bounded exhaustive) or T2 (proof).
- Size: >= 1000 raw pairs, >= 400 de-duplication groups, with lineage = same template on same base function counted once (<= 3 per lineage), <= 8 pairs per base program.
- Truth-class quotas (decided before labelling): observable-divergence families including a rare-region-exposure subtype; representation-only quota; internal-only quota >= 100 items in >= 40 base programs ONLY for the V7-A pilot (2.6), built by the GT M1 construction certificates. Items whose verified class differs from the intended class are relabelled and the mismatch logged.

H-P: prospective set (optional, exploratory/replication). Same rules as H-R, commits collected only after V7 is frozen (G6) over a fixed 8-week window; tests temporal generalisation.

H-X: reserve set, a second disjoint H-R-like set, sealed and unopened. Opened only (a) by an approved amendment after confirmed contamination of H-R/H-M, or (b) for a pre-declared replication of a surprising result. Any opening burns it and is logged.

DEV-N: unsealed development sets: hand-built validation-matrix suites (GATES section A) and a development split of real regressions mined under the same pipeline from a different time window and different projects than H-R. DEV-N must supply estimates of the discordant rate pi, ICC rho, base detection rate, hard-stratum share, internal-only/representation-only prevalence and label-noise rate under the GT pipeline (3.5; section 8.6).

### 3.3 Freezing, sealing, custody (unchanged in substance)
1. Corpus manifest = per-item canonical record (old/new sources, scope, driver metadata, provenance URL/commit, collection date, inclusion-rule outcome, lineage_id, cluster_id; field list in POWER 4), hashed with SHA-256 over a canonical serialisation; manifest has a Merkle root.
2. Labels live in a separate artifact (labels.sealed) with its own hash, held by the custodian. The evaluation runner mounts only the inputs tree; the scorer mounts labels only after all system outputs are written and hashed.
3. Custodian: a person who is not a V7 implementer. Duties: build/hold the sealed archive offline (read-only medium plus escrow copy), publish hashes (manifest root, labels hash, analysis-plan hash, system-build hash) into the append-only ledger and a third-party timestamp.
4. Unseal is one-shot and requires frozen system and config hash, frozen analysis-plan hash, frozen budget and seed lists, and a clean rehearsal on a burnt set (G6). A second evaluation run is forbidden except to resolve a crash (identical code and seeds; first result retained and reported).
5. Burn rule: any read of a holdout item or label by an implementer, tuner or analysis script before unseal demotes that holdout to a development set; H-X replaces it.
6. No label-guided input generation (D11): exploration sees old code, new code, signatures, the changed-region map (static, label-free), old-version docstrings/comments, and tests present at the parent commit. It never sees labels, benchmark identity, outcomes of other pairs, tests added by the fix commit, fix messages or issue text, or new-version docstrings/comments (RT Q5(e,f): the fix often rewrites them). Input seeds for H-M come only from the base program's public API and pre-existing examples. Enforced by environment (labels not mounted) and a log of every file opened during exploration. Explorer hyperparameters are tuned on development sets only; seeds are pre-declared.

### 3.4 Time awareness and independence checks
- All H-R/H-P commits post-date T0; project list frozen before commit inspection.
- Independence report (required deliverable): repository/package overlap, source-hash overlap, near-duplicate overlap (3.2 rule) against DEV, regression sets and each other; zero cross-split duplicate groups.
- Time-aware development: tune on pre-T0 data only; time-ordered validation on DEV-N.

### 3.5 Ground-truth classes and label adjudication
Truth is defined and established independently of any SBG output (D2; GT design rule). Five classes (GT 1.2, POWER 3), relative to a declared input domain X and observation boundary B:

| # | Truth class | Definition (short) | Evidence needed | In Det/FAR denominator | Role |
|---|---|---|---|---|---|
| 1 | Observable divergence (Div) | exists x in X with an output difference under B | one truth-harness-replayed witness (any tier) | yes | H2, H4, H5, H6 |
| 2 | Internal-only (IO) | no output difference over all of X, but a pre-declared canonical internal predicate differs | T1-b or T2 for the universal "no output difference" claim, plus a demonstrated differing predicate | no | V7-A pilot only (H7/H8); descriptive elsewhere |
| 3 | Representation-only (RO) | no output difference and no predicate difference; code/trace/representation differ | T1-b or T2 | no (false-alarm and annotation controls) | false-alarm rate; H8c |
| 4 | Unactivated changed region | changed region reachable but not executed by any truth-team input | coverage by independent tool | no, reported separately | abstention honesty vs INSUFFICIENT(not-activated) |
| 5 | Insufficient/ambiguous | evidence tier too weak, nondeterministic, boundary-sensitive, tool or adjudicator disagreement | reason code mandatory | excluded from primary denominators; always reported with sensitivity bounds | counts reported per source |

Mapping from the original EP classes: Div = 1; Eq-B = 3 plus the provably dead subset; INTERNAL_ONLY = 2; Undecided = 4 and 5 (split newly reported). Fuzz-only "no difference" evidence (T1-f) is NOT sufficient for classes 2 or 3; such pairs fall to class 5 (universal claim not established). This replaces the original EP T1 wording, which accepted a >= 10^5-input fuzz run as Eq-B evidence (MATRIX X-03).

Procedure (extends EP 3.5; details in GT 2-4):
1. Preserve: `label_original` is immutable; `label_final` is adjudicated truth; both reported, final primary. Additional immutable fields per GT 4.
2. Truth harness: built by the custodian side, separate code path, separate capture mechanism from V7 module B (two reference tools that must agree on mechanical pairs). Evidence tiers T0 none; T1-b bounded exhaustive over X_b (<= 10^6 inputs); T1-f fuzz/spec-driven >= 10^5 inputs with changed-branch coverage; T2 proof or bounded symbolic equivalence; T3 expert reading with written argument. Any harness-found witness is conclusive for Div.
3. Two independent adjudicators (A1, A2), blind to each other, to all V7 and baseline output, and (until votes lock) to `label_original`. Versioned, hashed rubric covering repr artifacts, exception messages (off), non-contractual ordering, logging-only effects, performance-only changes (not divergence), non-termination (Div if reproducible 3/3 at 2x timeout).
4. Agreement: pilot on >= 60 DEV-N items, stratified (GT 4): five-class Cohen's kappa >= 0.80 with lower CI bound >= 0.70, and binary internal-only-vs-representation-only kappa >= 0.75 (lower >= 0.65) for the pilot labels; for the collapsed three-class scheme used by the V7-B holdout (Div / no-output-difference / insufficient) kappa >= 0.80 and CI lower bound >= 0.70 on a >= 100-item double-rated sample (all items if fewer). Report PABAK and positive/negative specific agreement. The K5 gate requires kappa >= 0.7 (D9).
5. Disagreements: logged; third adjudicator A3 resolves blind with a written rationale; pre-resolution votes kept; three-way split becomes class 5.
6. Insufficient/ambiguous handling: excluded from primary denominators, always reported (count, share). Sensitivity bounds: recompute Det/FAR with all class-5 pairs counted as Div and as no-divergence. If class 5 exceeds 15% of any source, the source is flagged and the claim restricted (V6 fact: 8.7% unresolved).
7. Label-noise audit: contamination of no-output-difference labels by true Div must be audited and reported; it dilutes the paired effect by about (1 - e) (POWER 6.6) and, for the pilot, is fatal above about 2% (POWER 6.8).
8. Labels frozen at sealing (H-M entirely; H-R at sealing). Post-unseal changes appear only in sensitivity analyses flagged POST_UNSEAL. Refutation channel (GT 2.6): union over all arms, one direction only (toward Div), identical application to all arms; primary analysis uses pre-revision adjudicated labels, revised labels are sensitivity.

---

## 4. Baselines (D7: like-for-like; same pairs, seed corpus, sandbox, per-execution timeout, machine class)

| ID | Baseline | Role |
|---|---|---|
| B1-blind | plain differential testing: undirected random/property-based inputs, output equality, same CPU budget | secondary comparator; pairs with V7-diff-blind |
| B1-directed | B1 plus the same static changed-region information V7 uses (changed-region coverage reward, literal and boundary seeds from the diff), output-only comparison | PRIMARY comparator for H2a and H4 when V7 uses the changed-region map |
| B2 | off-the-shelf coverage-guided differential fuzzer, diff-blind | secondary comparator |
| B2-directed | B2 with directed scheduling toward changed blocks (AFLGo-style) | PRIMARY comparator for H2b |
| B3 | conventional features (edit size, token/AST distance, exec volume), LR and GBM | scorer comparator (H10, only if J) |
| B4, B5 | V5; V6 C0g (and C1) | historical scorers; regression table and H10 only; never the primary bar (V6 was at chance on real bugs) |
| B6 | metamorphic checks (declared relations) | hard-stratum comparator |
| B7 | replay of existing tests at the parent commit | cost reference |
| B8 | static-only: AST edit script plus changed-region size, no execution | floor for INSUFFICIENT honesty |

Rules:
1. Equal information: if V7's explorer reads the changed-region map, the primary comparators are B1-directed and B2-directed; V7 is ALSO run diff-blind (V7-diff-blind) against B1-blind and B2 as a secondary contrast, so V7's marginal value over diff awareness itself is visible (RT Q5(a)).
2. Same verdict function for all verdict systems: every B1/B2 variant emits the three-valued verdict by a rule fixed beforehand: DIVERGENT_OBSERVABLE on any replay-confirmed output difference; NO_DIVERGENCE_OBSERVED(S) with sufficiency computed by the SPEC on the baseline's own traces (a baseline run carries the coverage instrumentation needed for the SPEC factors and is charged for it); otherwise INSUFFICIENT. If a baseline cannot supply a factor the SPEC requires for S1, it emits INSUFFICIENT, never NO_DIVERGENCE_OBSERVED. Sufficiency-based abstention is therefore applied to baselines equally.
3. Native-form reporting: a baseline's raw "no difference found" is reported only in a descriptive table labelled "native output, not an assurance claim, unequal footing". It is not used by any hypothesis and carries no FAR.
4. Tuning parity: count and report the tunable parameters of every arm (V7 has at least 20 knobs; B2 about 3-5, RT Q5(d)); baselines receive an equal random-search budget over their own knobs on DEV-N, not merely an equal number of "configurations". A weaker-than-effort baseline voids the corresponding claim.
5. Only "same-budget" means the CPU-second budget of section 7.

---

## 5. Ablations (paired; identical pairs and seeds; each arm a pre-declared contrast on DEV-N, never on sealed data)

Module set per D5: core = A (exploration), B (capture), C (static context), D (evidence fabric: replay recipes plus hashed event streams), G (alignment), H (divergence plus impact), I (evidence/uncertainty/decision), K (validation harness), L (reproducibility). E (state abstraction and invariants) is OPTIONAL, V7-A pilot only. F is not a subsystem; control/call/dependence views are projections inside G and H. J is optional and off by default.

- A: replay-only; +random; +property-based; +structure-aware; +changed-region-directed (full A); diff-blind vs diff-aware (D7).
- B: determinism controls off/on; with/without completeness metadata; capture tiers L0-L3.
- C: no static context vs AST/CFG vs +signatures.
- D / projections in G,H: replay-recipe-only vs hashed event stream; each projection alone vs all.
- E (pilot): none vs state abstraction vs +invariants.
- G: no alignment (positional) vs static-only vs static + dynamic anchors.
- H: output-only vs +control-flow-event divergence; impact on/off (locus accuracy only).
- I: sufficiency off (binary) vs S1 only vs S1-S3; raw vs calibrated.
- Exploration strategies (scheduler arms, same budget): replay; random; property-based; structure-aware; changed-region-directed; coverage-guided (B2 reused); optional concolic.

Retain-or-drop rule (declared now): a module stays in the core iff, with a Holm-adjusted paired contrast on DEV-N, it improves at least one primary metric (Det at 60 s, TTFW RMST, FAR at matched coverage, AURC) with CI lower bound > 0, OR it is required by a correctness gate (validity, sufficiency honesty), AND its CPU overhead is <= 25% of the per-pair budget at median. Failing modules are demoted to diagnostics, not removed from reports.

---

## 6. Leakage controls
1. Generator fingerprinting probe: label vs generator-fingerprint features (edit size, diff token n-grams, AST operator kinds, mutation-family id). Report AUROC per holdout; > 0.65 triggers the edit-size/family-matched primary subset. This single 0.65 threshold is used everywhere in V7 documents (MATRIX X-09 records 0.55/0.60/0.65 elsewhere; the 0.60 in the roadmap is unresolved).
2. Edit size: stratify by tertiles; report the reversed-edit-size score; add the diff-shape control of 3.2.
3. Duplicates: section 3.2 rules.
4. Leave-mutation-family-out on H-M and DEV; leave-project-out on H-R and DEV-N (>= 8 folds); reported in every primary table.
5. Label-independence of inputs and label-shuffle negative control: system outputs must be byte-identical when labels are withheld; any difference is a leak.
6. Pretraining contamination: any LLM-involved component is disclosed with model identifier and training cutoff; H-R items are post-cutoff or marked; LLM-involved arms are reported separately.
7. Instrument leakage: results must hold under `repr` normalisation (V6 fact: SP-11 repr artifact).
8. Design-prior contamination: thresholds shaped by V6 failure lists are listed; every primary claim must be confirmed on the H-R sealed set, which was not visible at design time.

---

## 7. Budget definitions (single unit)
- The ONLY budget unit is CPU-seconds (user+sys) per pair, summed across ALL processes a method spawns, including tracing, alignment, static analysis, view construction, replay confirmation and verdict computation (D7). Measured with an rusage/cgroup counter. Wall-clock is reported as a diagnostic, never as a budget. Grid: 10 s, 60 s, 300 s per pair; headline and confirmatory budget 60 s.
- Number of input executions and distinct covered branches of changed regions are reported as diagnostic columns, not as budget units. A sensitivity table re-expresses detection against execution count; it is labelled sensitivity and no hypothesis depends on it.
- Baselines receive the same seed corpus, sandbox, per-execution timeout and machine class; single-tenant; one core pinned per run. Overhead honesty: V7 pays for tracing; baselines are charged for the coverage instrumentation they actually use. No method gets free preprocessing.
- Anytime curves: every system logs (CPU-s, first witness, coverage) so that all budgets come from one run per seed truncated at the budget (valid because DIVERGENT_OBSERVABLE is absorbing and witness-finding is monotone in time).
- Holdout cost budget (explicit; MATRIX B-03). Upper-bound cost of one sealed evaluation = pairs x arms x seeds x 300 s / 3600 CPU-hours, since a pair with no witness consumes the full 300 s. Reference arithmetic at 700 pairs and 5 seeds: one arm = 292 CPU-hours; three arms (V7, B1-directed, B2-directed) = 875 CPU-hours; with the three diff-blind and native arms the bound is about 1750 CPU-hours. Planned sizes (H-R about 640 pairs at 80 projects, plus H-M about 400 groups) exceed 700 pairs, so the figure is recomputed at G0 from frozen sizes and the approved budget is recorded in the ledger; G5 entry requires the approved holdout compute budget to be available. Mitigations that do not change the claim: deterministic arms run one seed; a pair stops at its first confirmed witness (witnesses are absorbing). The original 150 CPU-hour figure is withdrawn (low by 1.2-6x).
- Per-run limits and capture overhead budgets are set from measured cost in P1 (GATES G1), not from V6's 60 s default (MATRIX B-01, B-02).

---

## 8. Statistics

### 8.1 Primary analysis
- Cluster = independent cluster (3.2). Paired deltas on identical pairs. Primary test for H2a, H2b, H4: cluster sign-flip permutation test (B = 10000, seed 42) on per-cluster paired differences, one-sided in the favourable direction for the +10pp superiority contrast, Holm-adjusted over {H2a, H2b, H4}. The effect of interest (+10pp) is the planning alternative; the test rejects the null of no advantage, and the report additionally states whether the cluster-bootstrap CI excludes 0 and whether it includes +10pp.
- Intervals: cluster bootstrap B = 10000, seed 42, 95% two-sided for estimation; 90% where a gate says so.
- Minimum cluster counts: confirmatory inference only with >= 60 independent clusters and >= 20 mixed-class clusters in the holdout (K5; raised from the original 30/20, and from V6's 15/10). Below that, results are descriptive and labelled so.
- Effective sample: report raw pairs, groups, lineages, clusters, Kish n_eff = (sum w)^2 / sum w^2 and design effect.

### 8.2 Power (simulation under ASSUMED discordance and ICC; POWER 6)
Paired Det comparison, p0 = 0.6, mean divergent pairs per project m = 4, rho = 0.15, discordant rate pi = 0.2. "t" = cluster-robust t-test; "alpha.0167" = Holm-conservative proxy for three tests.

| Independent projects (pairs) | +5pp, t | +10pp, t | +10pp, alpha .0167, t |
|---|---|---|---|
| 40 (160) | 22% | 63% | 45% |
| 60 (240) | 28% | 82% | 66% |
| 80 (320) | 38% | 91% | 81% |

The sign-flip test used here has less power at small K (40 projects: 14% at +5pp, 58% at +10pp; the two agree within about 2pp at K >= 200). Smallest effect with 80% power at 40 projects: 12.5pp (14pp at alpha .0167). Required K at 80% power, pi = 0.2, rho = 0.15: +10pp about 60 projects (80 at alpha .0167); +5pp about 300 (450); +3pp about 700. ICC sensitivity at 40 projects: rho .05/.15/.30 gives +10pp power 75/63/50%.
Explicit statement: **with about 40 projects the design is underpowered for every confirmatory contrast, including +10pp.** Non-inferiority at -2pp has about 8-11% power at 40 projects and needs about 8000 independent divergent pairs (POWER 6.5); it is not a hypothesis of this protocol (R2). Both the H-R target of section 3.2 (planning 80 projects, floor 60) and the K5 gate derive from this table. The numbers are simulation outputs under assumed pi and rho; they are re-run on DEV-N estimates (8.6) and the sample targets amended pre-seal.

### 8.3 Other estimation rules
- Paired tests for time: paired RMST / Wilcoxon on log-TTFW with right-censoring (EST, no threshold).
- Risk-coverage compared by AURC and at fixed coverage with cluster bootstrap (EST).
- H8a/H8b use design-effect-scaled Clopper-Pearson bounds on the cluster count (pilot only).
- Label noise: sensitivity re-run with the contamination rates measured in the label audit (3.5 item 7).

### 8.4 Multiplicity
Holm familywise alpha = 0.05 over the primary family {H2a, H2b, H4}, stated in 2.7. Stratum-level contrasts (hard stratum, per-family, per-budget), secondary hypotheses and pilot hypotheses are exploratory; BH-adjusted values are shown for reference and labelled exploratory.

### 8.5 Stopping, seeds, tuning
- Fixed sample size; no optional stopping or interim looks at holdout results. Corpus construction stops when the pre-declared cluster/lineage targets are met or the mining window closes, decided without reference to system performance. Futility/kill rules apply only at development gates (GATES).
- Seeds: system seeds {1001..1005} for every stochastic arm, all five reported (mean and range); bootstrap seed 42; PYTHONHASHSEED=0 in capture with hash-randomisation sensitivity tested separately.
- No tuning on holdouts: thresholds, S-level cutoffs (as given by the SPEC and calibrated on development data), budgets and decision rules frozen at G6.

### 8.6 Pre-seal re-run of the power analysis (required, not optional)
Before G0 closes, estimate pi, rho, base detection rate, hard-stratum share, internal-only and representation-only prevalence and label-noise rates on DEV-N with the GT pipeline, then re-run power/power_sim.py with those parameters and amend sample targets as a class-B amendment BEFORE sealing. If the re-run shows the achievable K is below the K5 floor, the programme proceeds to an exploratory-only report (K5 failure response, D9), not to a relaxed threshold.

---

## 9. Execution environment: isolation, nondeterminism, timeouts, external services
- Isolation (D10). The existing runner is not acceptable for any V7 claim; it survives only as `v6_compat`. Verified findings: runner thread lives in the host process; a runaway thread keeps burning CPU; no rlimits; child processes survive; `sys.settrace(None)` evades tracing; `os._exit` kills the host; network not denied. V7 capture therefore uses a fresh child process per run, `setrlimit`, process-group kill, tracing set up outside user-code reach with `settrace` evasion detected, and network denial plus filesystem write confinement via sandbox-exec on macOS or container `--network none` on Linux. Each property must pass an experimental check in P1; in P0 only the sandbox-exec network/write denial was observed to work. Zero escapes on a hostile family is a hard G1 criterion (MATRIX M-05).
- Sandbox policy: no network egress; fixed seeds for `random`, `numpy.random`; time freeze; fixed locale/TZ; PYTHONHASHSEED=0; deterministic temp dirs; filesystem confined to a per-run tmpdir; per-pair process isolation (V6 lesson: group-mode hung on `math_gray_code`).
- Nondeterminism: each version is executed >= 3 times on the same input; disagreement on the same version marks the input nondeterministic. Nondeterminism affecting a compared channel yields INSUFFICIENT with the nondeterminism reason code unless controls make it deterministic. A witness must reproduce in 5/5 fresh replays; a flaky witness is not DIVERGENT_OBSERVABLE and counts toward INSUFFICIENT with the flaky-witness reason code. Fixed-seed control must not itself manufacture divergence (RT Q9); perturbation-robust replay is specified in the SPEC and module contracts. Replay-count values in other V7 documents (2, 3, 5) are reconciled there, not here (MATRIX M-06).
- Timeouts: per-execution 10 s CPU time; per-pair budget per section 7. Timeouts are never silently dropped: INSUFFICIENT with the timeout reason code, or DIVERGENT_OBSERVABLE(non-termination) only if reproducible 3/3 at 2x limit in one version and not the other.
- External services: units needing them are excluded by the pre-declared inclusion rule (ledger entry), or run against fixtures recorded at the parent commit (identical for old/new). No live service calls during scoring.
- Machine drift: pin machine class; record CPU model, Python version, lockfile hash; independent rerun on another machine at G8.
- Crashes: tool crashes are INSUFFICIENT with the tool-error reason code and counted against decided coverage; crash rate > 2% blocks G6.

---

## 10. Reporting rules
- Report every pre-declared metric for every sealed holdout, positive or negative, in one table layout, with clusters, groups, lineages and raw pairs.
- Headline numbers are always "all eligible pairs" (INSUFFICIENT counted as non-detection for Det and as non-coverage). Activated-only is shown alongside, labelled.
- Abstention report per holdout: decided coverage, activation rate, determinism-confirmed rate, reason-code breakdown, truth-class mix of abstained pairs, Div share abstained vs decided, risk-coverage curve, what B1-directed would have said on abstained pairs.
- Negative results: each failed hypothesis is reported with its pre-declared consequence. Claim ladder: section 2.7. Underpowered outcomes are labelled INCONCLUSIVE.
- Failure catalogue: 15 worst false assurances and 15 worst false alarms per holdout with causes, by family and project.
- Deviations list and amendment log are part of every report (GATES section D).
- Mandatory language: "non-pristine" for the five legacy sets; "ground truth adjudicated by two raters, kappa = ..." with class-5 counts; "no divergence observed at sufficiency S" and never "equivalent", "same", "pass" or "verified" as an outcome.
- Counts of truth classes 1-5 per source are always reported; internal-only is its own column and is never merged into divergent or equivalent.

---

## 11. Order of work (pre-implementation)
1. Freeze this protocol and GATES (G0); custodian appointed; T0 set; power analysis re-run on DEV-N estimates (8.6).
2. Mine H-R/H-X/DEV-N project lists; build truth harness; author H-M (blinded); adjudicate; seal (hashes published) BEFORE any V7 module that executes code is integrated (G5 requires sealed hashes to exist). The K1 feasibility pilot (GATES K table) may mine candidate pairs earlier but seals nothing.
3. Implementation proceeds against DEV/DEV-N and the validation matrix; holdouts untouched.
4. G6 freeze, G7 single-shot evaluation, G8 report. The V7-A pilot (2.6), if admitted, runs after G7 on authored suites and reports inside the G8 report as exploratory.

---

## 12. Disagreements with the spine, open risks, and what changed
1. The spine's "baselines V7 MUST beat or match" includes V5/V6; those are scorers, V6 was at chance on real bugs. They remain only for H10 and the regression table. The real bar is B1-directed and B2-directed (and, secondarily, the diff-blind pair).
2. "Internal change masked by outputs" is not a verdict (D2). A masked internal change is, at the interface level, not a divergence unless some input exposes it; the truth class internal-only measures the optional annotation in a pilot with an independent reference tool. The value of internal state would be shown only as earlier or greater exposure of real interface witnesses (H7), which at the proposed sizes is not obtainable as a confirmatory claim.
3. Witness validity (replay-confirmed) is near-tautological; it is a gate. The discriminating metrics are Det at equal cost, FAR with the single definition, and risk-coverage.
4. FAR denominators: abstention lowers FAR trivially; hence decided coverage >= 0.60 is a success condition and the abstention report is mandatory. FAR is compared against a baseline given the same sufficiency gate at matched decided coverage.
5. The budget currency is CPU-seconds including all V7 overhead.
6. Real-regression ground truth remains scarce. Mining 60-80 fresh independent post-T0 Python projects is unproven. The programme may legitimately end with "inconclusive" or with an exploratory-only report.
7. Residual risks (GT section 5): reference tools and V7 both run on CPython; the universal no-output-difference claim is domain-bounded; the predicate set Pi is a human choice.
