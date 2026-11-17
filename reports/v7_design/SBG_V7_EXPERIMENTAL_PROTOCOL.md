# SBG V7 Experimental Protocol (pre-implementation)

Status: DRAFT v0.1 for freeze at gate G0 (see SBG_V7_VALIDATION_AND_ACCEPTANCE_GATES.md). Nothing in this document has been run. No V7 code exists. All numbers that are not marked "V6 fact" are proposals with a stated justification and are subject to the amendment procedure in the gates document, section D.

Evidence base used (read-only): `_DESIGN_SPINE.md`; `reports/v6_redesign/SBG_V6_FINAL_ARCHITECTURE.md`, `SBG_V6_HOLDOUT_STATISTICAL_ANALYSIS.md`, `SBG_V6_FAILURE_ANALYSIS.md`; `artifacts/v6/audit/PROTOCOL_V2.json`.

V6 facts this protocol is built around:
- V6 holdout AUROC: v8 test 0.768, v10 0.851, QuixBugs 0.666 declared / 0.691 canonical, BugsInPy 0.505. The pre-declared claim "independent information beyond conventional features" was NOT SUPPORTED.
- Differential output comparison was strong wherever outputs were observable (v10 0.995, QB declared-evaluable 0.976) and useless where nothing activated (BugsInPy 0.502). The dominant real-world failure was observation (BugsInPy coverage 28.5%), not modelling.
- Of 1332 changed DEV pairs, 357 (27%) show no output difference: 61 unactivated, 180 masked internally, 116 unresolved. This "hard stratum" is where a V7 contribution beyond differential testing must live.
- Labels were a pure function of the mutation generator; SP-8 (47) and SP-11 (42) were label/instrument defects; 596 duplicate groups covered 1713 of 2392 pairs; generator fingerprinting gave GBM 0.972 falling to 0.742 leave-type-out.
- The selection rule was partly operationalised after data was seen ("not fully preregistered"). V7 must not repeat that.

---

## 1. Scope, units, and vocabulary

- Unit of analysis (a "pair"): (old, new, scope) where scope is a declared function/class/module entry-point set with a drivable signature.
- Verdict (system output): `DIVERGENT` (replayable witness input + first-divergence locus + evidence chain), `NO_DIVERGENCE_OBSERVED` with sufficiency level S in {S1, S2, S3} (never "equivalent"), `INSUFFICIENT` with reason code (NOT_ACTIVATED, NONDET, UNDRIVABLE, IMPORT, TIMEOUT, UNOBSERVED_CHANNEL, PARTIAL_INSTRUMENTATION, BUDGET).
- Sufficiency levels (pre-declared; thresholds are fixed here, not tuned on holdouts): S0 = changed region never activated (cannot be emitted as NO_DIVERGENCE_OBSERVED; maps to INSUFFICIENT/NOT_ACTIVATED); S1 = every changed region activated at least once on both versions; S2 = S1 and branch/state coverage of changed regions >= 80% of the statically reachable branches, and all declared observation channels instrumented; S3 = S2 and the divergence-discovery curve has plateaued (no new coverage or new state class in the last 25% of the budget).
- Truth (ground truth, section 3.5): `Div` (interface-level divergence exists), `Eq-B` (equivalent on the declared input domain, with evidence tier), `INTERNAL_ONLY` (internal state differs but no interface difference exists in the declared domain), `Undecided`.
- Interface level = return value (type-aware equality, with declared normalisation for repr artifacts such as deque vs list), raised exception type (message is a configurable channel, default off), declared side-effect channels (arguments mutated, globals written, files in a sandbox tmpdir, stdout/stderr). INTERNAL_ONLY is reported separately and never counted as Div. This answers the circularity risk of grading an internal-state system against labels that internal-state can create.

## 2. Research questions and pre-declared hypotheses

All directions are fixed now. "Plain DT" = plain differential testing with output equality at the same budget (baseline B1). Confirmatory tests are on the sealed holdouts (section 3.3) only. DEV/regression sets are used for development and for gate decisions, never for confirmatory claims.

RQ1 Is every DIVERGENT verdict a real, replayable, interface-level difference?
- H1 (validity, non-comparative): witness validity rate (replay-confirmed in a fresh sandbox, 5 replays, same difference and same locus) >= 0.99; the lower 95% cluster-bootstrap bound >= 0.97. Secondary: oracle-confirmed validity (the difference is an interface difference per truth, not an artifact) >= 0.95.

RQ2 At equal cost, does V7 find more divergences, and sooner, than plain DT and coverage-guided differential fuzzing?
- H2 (detection at equal budget): Det(B) = P(DIVERGENT | truth=Div) at CPU-budget B in {10 s, 60 s, 300 s} per pair. Direction: V7 >= Plain DT at every budget (non-inferiority margin -2 percentage points, lower paired CI bound > -2pp); V7 > Plain DT by >= +5pp at >= 2 of 3 budgets on the hard stratum (truth=Div and seed-corpus outputs equal), Holm-adjusted.
- H3 (time to first witness): TTFW measured in CPU-seconds including all V7 overhead, right-censored at budget. Direction: V7 lower than Plain DT; ratio of restricted-mean TTFW (RMST at 300 s) <= 0.80 on the pairs where truth=Div.

RQ3 Does V7 reduce false assurance, and is its abstention informative?
- H4 (false-assurance rate, FAR): FAR = P(verdict = NO_DIVERGENCE_OBSERVED | truth=Div), denominator = ALL truly divergent pairs (INSUFFICIENT counts as not-assured, but is penalised in H5/coverage). Direction: FAR(V7) < FAR(Plain DT's implicit "no diff found = pass") with relative reduction >= 25% or absolute >= 5pp at B = 60 s. Also stated per sufficiency level: P(NO_DIVERGENCE_OBSERVED at level >= S3 | Div) <= 0.10 on real regressions, monotone non-increasing in level S1 > S2 > S3.
- H5 (risk-coverage): risk = P(error | decided) where error = NO_DIVERGENCE_OBSERVED on Div, or DIVERGENT on Eq-B (false alarm). Coverage = decided fraction over ALL eligible pairs. Direction: V7's risk-coverage curve lies below Plain DT with activation-based abstention at coverage 0.6, 0.7, 0.8; AURC lower, Holm-adjusted. Minimum useful coverage on the real-regression holdout: >= 0.60 (V6 fact: BugsInPy coverage was 28.5%).
- H6 (calibration): (i) monotonic ordering of miss rates across S1/S2/S3 (cluster-bootstrap CI of adjacent differences excludes 0 in the right direction on pooled holdouts); (ii) ECE <= 0.05 for the claim "observed miss rate at level S is within the nominal cap for S" (caps: S1 <= 0.35, S2 <= 0.20, S3 <= 0.10; these are conservative claims, not predictions); (iii) INSUFFICIENT reasons are informative: the Div rate among INSUFFICIENT/NOT_ACTIVATED differs from the Div rate among decided by a pre-declared direction (V6 fact: abstained pairs were 43% CHANGED vs a 56% base rate; we expect abstention not to hide a higher-than-base Div rate by more than 10pp).

RQ4 Does internal-state/trace divergence add information beyond output-differential testing at equal budget? (the scientific question in the spine)
- H7: the full V7 (state/control-flow views + state-directed exploration) improves over V7-without-internal-state-views (output + coverage only) on the hard stratum: Delta Det(300 s) >= +3pp or RMST ratio <= 0.85, paired, Holm-adjusted, on the real-regression AND the authored-mutant holdouts. Pre-declared fallback: if H7 fails and H2-H6 hold, the permitted claim is "sufficiency-aware witness-based differential testing", not "internal-state divergence adds information". A null on H7 is an acceptable and publishable outcome.
- H8 (masked-internal): on `INTERNAL_ONLY` truth pairs, V7 reports DIVERGENT-by-interface in <= 1% (false alarm cap) and emits an INTERNAL_ONLY annotation in >= 70% of cases where the state view fires.

RQ5 Does it generalise?
- H9: performance on project-disjoint / family-disjoint holdouts relative to leave-project-out DEV: Det drop <= 10pp absolute, FAR increase <= 5pp absolute, calibration still monotone. Leave-mutation-family-out and unseen-family results are reported for every primary metric.

RQ6 (optional layer J, only if built): does a learned scorer beat conventional features?
- H10: AUROC is reported ONLY for the optional scoring layer, as paired delta vs conventional (edit size, token/AST distance, exec volume), vs V5, vs V6, vs DT-score (delta_out). Direction: scorer+conv > conv by >= +0.03 AUROC, paired, on >= 2 sealed holdouts, Holm-adjusted. Otherwise J is dropped. AUROC is never a headline for the verdict system.

Primary confirmatory family (Holm, alpha = 0.05): H1 (lower-bound check, not a test), H2 (three budgets x hard-stratum superiority), H3, H4, H5, H6(i), H7. Everything else is secondary and reported with unadjusted CIs labelled exploratory (Benjamini-Hochberg shown for reference).

## 3. Data

### 3.1 Benchmark inventory and status

| Set | Content | Status | Permitted use |
|---|---|---|---|
| V5/V6 DEV (v8 train+val, 57 programs, 2392 pairs) | synthetic SC-/SP- mutants | non-pristine, heavy duplication, generator-determined labels | development, unit/regression tests, validation-matrix seeds |
| v8 test (26 programs) | synthetic | NON-PRISTINE (observed with V5/V6) | labelled regression set only |
| v10 (19 programs, SC+SP composites) | synthetic | NON-PRISTINE | labelled regression set only |
| QuixBugs (declared/canonical) | small real bugs | NON-PRISTINE; 36 declared pairs have no inputs | labelled regression set; input-less cases test INSUFFICIENT honesty |
| BugsInPy | real bug fixes | NON-PRISTINE; V6 coverage 28.5% | labelled regression set; substrate-coverage target (G1); never confirmatory |

Rule: these five are never called pristine, never appear in a confirmatory table, and every table that includes them carries the tag "NON-PRISTINE (development/regression)". Any parameter chosen with them visible is a development parameter. This applies even if V7 code never trained on them: V5/V6 results on them were read.

### 3.2 New holdouts (to be constructed before implementation completes, sealed before G5)

H-R: fresh real-regression corpus (primary confirmatory).
- Source: Python projects NOT in BugsInPy, QuixBugs, V5/V6 base programs; project-disjoint verified by repository URL, package name, and source-hash overlap (as V6 did: 0 id overlap, 0 source-hash overlap).
- Time-awareness: only fix and refactor commits dated after a freeze date T0 declared at G0 and after the last day any V7 development data was collected; the project list is frozen by hash before commits are examined.
- Divergent pairs: (parent, fix) commits where a regression test added by the fix fails on parent and passes on fix (Defects4J-style). Scope = the function/class set the fix touches, with an extractable drivable signature.
- Non-divergent controls: (parent, child) commits classified as behaviour-preserving (formatting, rename, extract/inline, type-hint-only) AND whose full test suite passes unchanged on both; truth still needs adjudication (3.5). Controls are required, because FAR without matched Eq-B pairs rewards a system that always says DIVERGENT.
- Size targets: >= 40 projects; >= 150 Div pairs; >= 150 control pairs; per-project cap 5% of the corpus (<= 8 pairs per project) to avoid one project dominating; minimum 30 clusters (projects) with >= 1 pair after de-duplication, >= 20 projects containing both classes.
- Dataset-quality gate: shortcut probe (section 6.1) AUROC for edit-size-only on the corpus <= 0.65; if higher, report the edit-size-matched subset as co-primary.
- Excluded units (rule fixed before mining, ledger kept): needs network or external service, GPU/hardware, interactive input, undrivable signature (counted, reported, NOT silently dropped).

H-M: newly authored mutants with independent oracles (primary confirmatory for mechanism claims).
- Base programs: >= 40, drawn from sources disjoint from V5/V6 base programs (new repositories or newly written reference implementations with specifications).
- Authors: people who did not implement V7 and who have not seen V6 generators' output beyond the family descriptions; they follow a written authoring brief. Optionally an additional family authored by an LLM with the model identifier and prompt recorded; this family is tagged by author type and analysed separately (generator-fingerprint control). LLM-authored items are never adjudicated by an LLM.
- Families: >= 6 NEW families not equal to SC-1..SC-6 / SP-1..SP-11 (suggested: rarely-reached branch guards; boundary-only divergences; state-accumulation divergences exposed after k calls; masked internal changes (overwritten/cancelled intermediate); exception-type changes; side-effect-only changes; equivalence-preserving refactors verified by bounded exhaustive check). Each family contains both Div and Eq-B/INTERNAL_ONLY members, so a family is not label-predictive.
- Independent oracle: each item ships a specification-level reference (property test, spec reference implementation, or exhaustive enumeration over a bounded domain) written without access to V7 outputs. Truth for Eq-B requires exhaustive bounded checking or proof (tier T1/T2, section 3.5).
- Size: >= 1000 raw pairs, >= 400 de-duplication groups, per-base-program cap 5%.

H-P: prospective set (confirmatory, optional but recommended). Projects selected by H-R's rules, commits collected only after V7 is frozen (G6) over a fixed 8-week window; tests time-generalisation under a true temporal split.

H-X: reserve set. A second, disjoint H-R-like set, sealed and unopened. It is opened only (a) by an approved amendment after a confirmed contamination of H-R/H-M, or (b) for a pre-declared replication of a surprising result. Any opening burns it and is logged.

DEV-N: new development sets (not sealed): small hand-built validation-matrix suites (gates document, section A) and a dev split of real-regression mined under the same pipeline from a different time window and different projects than H-R. Used for threshold selection and G-gates.

### 3.3 Freezing, sealing, custody

1. Corpus manifest = per-item canonical record (old/new sources, scope, driver metadata, provenance URL/commit, collection date, inclusion-rule outcome). Items hashed with SHA-256 over a canonical serialisation; the manifest has a Merkle root.
2. Labels are stored in a separate artifact (labels.sealed) with its own hash, held by the custodian. The V7 pipeline cannot read it: the evaluation runner mounts only the inputs tree; the scorer mounts labels only after all system outputs are written and hashed.
3. Custodian: a person who is not a V7 implementer. Duties: build/hold the sealed archive offline (read-only medium plus an escrow copy), publish the hashes (manifest root, labels hash, analysis-plan hash, system-build hash) into the repository's append-only ledger and a third-party timestamp (e.g., RFC 3161 or a public commit).
4. Unseal: one-shot, requires (i) frozen system hash and config hash, (ii) frozen analysis plan hash, (iii) frozen budget and seed lists, (iv) a clean rehearsal on a burnt set (G6). The custodian logs who, when, hash verification, and the single run id. A second evaluation run on a holdout is forbidden except to resolve a crash (recorded as a deviation; identical code and seeds; the first result is retained and reported).
5. Burn rule: if any implementer, tuner, or analysis script reads a holdout item or label before unseal, that holdout is demoted to a labelled development set and H-X replaces it.
6. No label-guided input generation: exploration (module A) sees only the old code, the new code, signatures, docstrings, and tests present at the parent commit (never tests added by the fix commit, never any label, fix message, or issue text). Input seeds for H-M come only from the base program's public API and its own pre-existing examples. Enforced by environment (labels not mounted) and audited by a log of every file opened during exploration.

### 3.4 Time awareness and independence checks
- All H-R/H-P commits post-date T0; project list frozen before commit inspection.
- Independence report is a required deliverable: repository/package overlap, source-hash overlap, near-duplicate overlap (MinHash Jaccard >= 0.8 on normalised ASTs) against DEV, regression sets and each other; zero cross-split duplicate groups required.
- Time-aware development: tune on data from before T0 only; time-ordered validation (train earlier, evaluate later) on DEV-N.

### 3.5 Label adjudication protocol
Applies to H-R controls, all ambiguous H-R/H-M pairs, and a 100% audit of any pair where the original label and the independent bounded-check disagree.

1. Preserve: the original label (generator/commit-derived) is stored immutably as `label_original`. Adjudicated truth is `label_final`. Neither is overwritten. Every analysis reports both ("original" and "adjudicated"), with the adjudicated labels primary.
2. Independent evidence harness ("truth harness"): built by the custodian side, separate code path from V7. Produces evidence tiers: T0 none; T1 bounded exhaustive enumeration over a declared small domain, or property-based/fuzz run with >= 10^5 inputs and coverage of all changed branches (state the bound); T2 formal proof or bounded symbolic equivalence; T3 expert reading with a written argument. A witness found by the truth harness is conclusive evidence for Div. Eq-B needs T1 or better; T3 alone yields `Undecided` unless both adjudicators concur and write the argument.
3. Two independent adjudicators (A1, A2), blind to each other and to all V7/baseline outputs; both blind to which system found what. They get old/new code, scope, truth-harness evidence, and the rubric. Rubric (written, versioned, hashed): classes Div / Eq-B / INTERNAL_ONLY / Undecided; decision rules for repr artifacts (default: equal if values equal under declared normalisation), exception messages (off by default), non-contractual ordering (dict/set order treated as non-divergent only if documented as unordered), logging-only side effects, performance-only changes (not divergence), and non-termination changes (Div if reproducible 3/3 at 2x timeout).
4. Agreement: pilot on >= 60 items from DEV-N; collapsed 3-class Cohen's kappa target >= 0.80; if kappa < 0.70 or the CI lower bound < 0.60, revise the rubric and re-pilot on fresh items. On the real corpora, a >= 100-item double-rated sample (or all items if fewer) gives a kappa CI; target lower bound >= 0.70.
5. Disagreements: logged (item id, A1, A2, rationale); resolved by A3 (a third adjudicator, blind to who said what) with a written rationale; the pre-resolution votes are kept. Systematic disagreement categories feed rubric amendments (before unseal) only.
6. Undecided pairs: excluded from the primary denominator, always reported (count, share). Sensitivity bounds: recompute Det/FAR with all Undecided counted as Div (worst case for assurance) and all as Eq-B. If Undecided > 15% of any source, the source is flagged and the claim restricted. (V6 fact: 116 of 1332 changed pairs were unresolved, 8.7% of changed pairs; this is the realistic order of magnitude.)
7. Adjudicators never see which verdicts V7 produced; their labels are fixed before unseal where possible (H-M entirely; H-R labels frozen at sealing).

## 4. Baselines (all given the same pairs, same seed corpus, same sandbox, same budget)

| ID | Baseline | Role |
|---|---|---|
| B1 | Plain differential testing: same input generator family but undirected (random/property-based), output-equality only, same CPU budget | main comparator for H2-H5 |
| B2 | Coverage-guided differential fuzzing (off-the-shelf coverage-guided Python fuzzer driving both versions, comparing outputs and exceptions) | strong comparator; tuned with the same effort as V7 on DEV |
| B3 | Conventional features (edit size, token/AST distance, executed-line volume), LR and GBM | scoring layer comparator (H10) |
| B4 | V5 | historical scorer |
| B5 | V6 C0g (and C1) | historical scorer; scoring-layer comparison only |
| B6 | Metamorphic checks (declared relations, e.g. idempotence, permutation invariance, round-trip; check each relation on old and new; divergence if the relation holds on one version and fails on the other) | comparator for hard stratum |
| B7 | Replay of existing test suites at the parent commit (dev-time free oracle) | cost reference |
| B8 | Static-only: AST edit script + changed-region size, no execution | floor for INSUFFICIENT honesty |

Rules: B1/B2 emit the same three-valued outputs via a rule fixed beforehand (DIVERGENT on any output difference; NO_DIVERGENCE_OBSERVED with sufficiency computed by the SAME S0-S3 definitions applied to their traces where possible; INSUFFICIENT otherwise) so that risk-coverage comparisons are like-for-like; a second comparison reports each baseline in its native verdict form. V5/V6 are scorers, not verdict systems: they appear only in H10-type scoring comparisons and in the NON-PRISTINE regression table; they are not the primary bar (V6 sat at chance on real bugs, so beating it would be a weak result).

## 5. Ablations (paired, identical pairs and seeds; each arm a pre-declared contrast)

Per module (spine letters): A exploration, B capture, C static context, D evidence fabric, E state/invariant, F multi-view, G alignment, H divergence+impact, I evidence/uncertainty, J scorer (optional).
- A: replay-only; +random; +property-based; +structure-aware; +changed-region-directed (full A).
- B: determinism controls off/on; with/without completeness metadata.
- C: no static context vs AST/CFG vs +signatures.
- D/F: raw log only vs each derived view alone (control-flow; call; data-dependence; state-transition) vs all.
- E: no state abstraction vs state abstraction vs +invariants.
- G: no alignment (positional) vs static-only vs static + dynamic anchors.
- H: output-only vs +control-flow divergence vs +state divergence; impact propagation on/off (affects locus accuracy only, not Det).
- I: sufficiency levels off (binary) vs S1 only vs S1-S3; raw vs calibrated.
Per exploration strategy (scheduler arms, same budget): replay; random; property-based; structure-aware; changed-region-directed; state-divergence-guided; coverage-guided (B2 reused); optional concolic for hard branches.
Retain-or-drop rule (declared now): a module stays in the core iff, with Holm-adjusted paired contrast, it improves at least one primary metric (Det at some budget, TTFW RMST, FAR, risk-coverage AURC) with CI lower bound > 0, OR it is required by a correctness gate (validity, sufficiency honesty), AND its CPU overhead is <= 25% of the per-pair budget at median. Modules failing the rule are demoted to diagnostics, not removed from reports. This avoids V6's post-hoc rule operationalisation.

## 6. Leakage controls
1. Generator fingerprinting probe: train a classifier on label vs generator-fingerprint features (edit size, diff token n-grams, AST operator kinds, mutation-family id). Report AUROC for each holdout; shortcut AUROC > 0.65 triggers the edit-size/family-matched primary subset (V6 facts: edit size 0.771 DEV, 0.847 BugsInPy; GBM 0.972 -> 0.742 leave-type-out).
2. Edit size: stratify results by tertiles; report the reversed-edit-size score (a diagnostic V6 used) next to V7.
3. Duplicates: normalised-AST hash groups plus MinHash near-duplicates; analyses weight by group (effective sample) and report both raw and group-collapsed results; zero cross-split groups.
4. Leave-mutation-family-out on H-M and DEV; leave-project-out on H-R and DEV-N (>= 8 folds); report in every primary table.
5. Label-independence of inputs (3.3 point 6) and label-shuffle negative control: the full pipeline on permuted labels must give Det/FAR at chance-equivalent (Det unchanged because Det depends on truth only at scoring; the check is that scorer output across shuffles is invariant to anything the system saw: the system outputs must be byte-identical when labels are withheld; any difference is a leak).
6. Contamination by pretraining: any LLM-involved component (optional authored family, optional J) is disclosed with model identifier and training cutoff; H-R items are post-cutoff or marked otherwise; LLM-involved arms are reported separately.
7. Instrument leakage: results must hold with `repr` normalisation (V6 fact: SP-11 repr artifact).

## 7. Budget definitions (equal-cost comparison)
- Primary budget unit: CPU-seconds (user+sys) per pair, summed across ALL processes the method spawns, including tracing, alignment, static analysis, view construction and verdict computation. Measured with a cgroup/rusage counter; wall-clock reported secondarily. Grid: 10 s, 60 s, 300 s per pair (headline 60 s; 300 s for the hard stratum).
- Secondary budget units: number of input executions (pair-executions, grid 100 / 1000 / 10000) and distinct covered branches of changed regions at fixed time. Cross-check: conclusions must agree in direction under both units, otherwise reported as budget-definition-sensitive.
- Baselines receive the same seed corpus, same sandbox, same per-execution timeout, same machine class; pinning one core per run; single-tenant; tuning parity: baselines get the same number of tuning configurations on DEV as V7.
- Overhead honesty: V7 pays for tracing; baselines run un-instrumented but are charged for the coverage instrumentation they actually use (B2). No method gets free preprocessing.
- Anytime curves: every system logs (CPU-s, first witness, coverage) so that results at all budgets come from one run per seed (truncated), not separate runs.

## 8. Statistics
- Cluster: project for H-R; base program for H-M (secondary: two-way family x program bootstrap). Bootstrap B = 10000, seed 42, resample clusters with replacement; paired deltas on identical pairs; cluster sign-swap permutation test for paired contrasts (B = 10000).
- Effective sample: report raw pairs, de-duplication groups, clusters, Kish effective sample n_eff = (sum w)^2 / sum w^2 for any weighting, and design effect 1 + (m - 1) rho (m = mean cluster size, rho = intra-cluster correlation estimated from the data).
- Minimum cluster counts: confirmatory inference only if >= 30 clusters and >= 20 mixed-class clusters in the relevant holdout (V6 used 15/10, which let 19-51-cluster sets claim inference; raised here). Below this: descriptive only, labelled so.
- Multiplicity: Holm across the primary confirmatory family (section 2), alpha = 0.05 two-sided; stratum-level and secondary contrasts exploratory.
- Paired tests: McNemar-style at cluster level via sign-swap for binary detection; paired RMST/Wilcoxon on log-TTFW for time with right-censoring; risk-coverage compared by AURC and at fixed coverage points, with cluster bootstrap.
- Power sketch (paired detection, McNemar approximation): to detect a difference delta = 0.10 with discordant proportion pi = 0.20, alpha = 0.05 two-sided, power 0.80: n_eff = ((1.96 sqrt(pi) + 0.84 sqrt(pi - delta^2)) / delta)^2 ≈ 155 effective pairs. For delta = 0.05: ≈ 625. With m = 8 pairs/cluster and rho between 0.1 and 0.3, design effect is 1.7-3.1: delta = 0.10 needs roughly 265-480 raw pairs (about 33-60 clusters); delta = 0.05 needs roughly 1050-1950 raw pairs, which exceeds the H-R target, so +5pp superiority is only claimable on the pooled hard stratum of H-R+H-M (hard stratum is ~27% of changed pairs in V6-type data; H-M is sized to compensate by oversampling hard families). Therefore the +5pp margin in H2 is at the edge of detectability; H7's +3pp is NOT powered in H-R alone and is pooled or reported with its CI (a wide CI is reported as inconclusive, not as support). Targets are proposals; the power analysis is re-run with DEV-N variance estimates before G0 closes and the sample targets amended pre-seal if needed.
- Stopping rules: fixed sample size; no optional stopping or interim looks at holdout results. Corpus construction stops when targets are met or the mining window closes, decided without reference to system performance. Futility/kill rules apply only at DEV gates (gates document).
- Seeds: system randomness seeds {1001, 1002, 1003, 1004, 1005} for every stochastic arm; all five reported (mean and range); bootstrap seed 42; analysis scripts take no other seeds. PYTHONHASHSEED=0 in capture; hash-randomisation sensitivity tested separately.
- No tuning on holdouts: thresholds, S-level cutoffs, budgets, and decision rules are frozen at G6. Hyperparameters chosen on DEV-N with time-ordered or leave-project-out CV.

## 9. Execution environment: nondeterminism, timeouts, external services
- Sandbox: no network egress; fixed seeds for `random`, `numpy.random`, fixed clock (time freeze), fixed locale/TZ, PYTHONHASHSEED=0, deterministic temp dirs, filesystem confined to a per-run tmpdir; process isolation per pair (V6 lesson: group-mode harness hung on `math_gray_code`; per-pair mode only).
- Nondeterminism: each pair's old and new are each executed >= 3 times on the same input; if outputs on the same version disagree, the input is nondeterministic. Nondeterminism affecting a compared channel yields INSUFFICIENT(NONDET) unless controls make it deterministic; a divergence witness must reproduce in >= 5/5 fresh replays (flaky witnesses are not DIVERGENT; they count toward INSUFFICIENT with reason FLAKY_WITNESS). V6 fact: BugsInPy had 60 nondeterminism failures; coverage target addresses this.
- Timeouts: per-execution 10 s (CPU time basis), per-pair budget per section 7. Timeouts are never silently dropped: they stay in the denominator as INSUFFICIENT(TIMEOUT), or as DIVERGENT(non-termination) only if reproducible 3/3 at 2x limit in one version but not the other.
- External services: units needing them are excluded by the pre-declared inclusion rule (ledger entry with reason), or, if recorded/mocked fixtures exist at parent commit, run against the fixtures (fixtures identical for old/new). No live service calls during scoring. Exclusion decisions are made before system runs.
- Machine drift: pin machine class, record CPU model, Python version and lockfile hash; V6 left "different machine or Python version" unreproduced, V7 closes this at G8 with an independent rerun.
- Crashes: tool crashes are INSUFFICIENT(TOOL_ERROR) and counted against the system's coverage; crash rate > 2% blocks G6.

## 10. Reporting rules
- Report every pre-declared metric for every sealed holdout, positive or negative, in the same table layout, with the number of clusters, de-duplication groups and raw pairs.
- Headline numbers are always "all eligible pairs" (INSUFFICIENT counted as non-detection for Det and as non-coverage), never "activated-only". Activated-only is shown alongside, labelled.
- Abstention report (required per holdout): coverage, reason-code breakdown, label mix of abstained pairs, Div share among abstained vs decided, risk-coverage curve, and what plain DT would have said on abstained pairs.
- Negative results: a failed hypothesis is reported with its pre-declared consequence (section 2). Pre-declared claim ladder: SUPPORTED needs Holm p < 0.05 and positive on H-R AND H-M; PARTIAL needs one holdout; otherwise NOT SUPPORTED. No claim is made from regression sets.
- Failure catalogue: 15 worst false assurances and 15 worst false alarms per holdout with causes (as in V6 failure analysis), by family and by project.
- Deviations list and the amendment log are part of every report (gates document, section D).
- Mandatory language: "non-pristine" for the 5 legacy sets; "ground truth adjudicated by two raters, kappa = ..." with Undecided counts; "no-divergence observed at sufficiency S" never "equivalent".

## 11. Order of work (pre-implementation)
1. Freeze this protocol and the gates (G0); custodian appointed; T0 set.
2. Mine H-R/H-X/DEV-N project lists; build truth harness; author H-M (blinded); adjudicate; seal (hashes published) BEFORE any V7 module that executes code is integrated (G5 requires sealed hashes to exist).
3. Implementation proceeds against DEV/DEV-N and the validation matrix; holdouts untouched.
4. G6 freeze, G7 single-shot evaluation, G8 report.

## 12. Disagreements with the spine and open risks
1. The spine's "baselines V7 MUST beat or match" includes V5/V6; those are scorers and V6 was at chance on real bugs. They are retained only for the scoring layer and the regression table. The real bar is B1/B2.
2. The spine lists "internal change masked by outputs" as a feature. A masked internal change is, at the interface level, not a divergence unless some input exposes it. Without a separate truth class (INTERNAL_ONLY) the false-assurance metric becomes circular. This protocol adds INTERNAL_ONLY and counts a DIVERGENT verdict on it as a false alarm; the value of internal state is then measured as earlier/greater exposure of real interface witnesses (H7), not as an extra "divergence".
3. "Witness validity (replay-confirmed)" is near-tautological (a replayed witness reproduces). It is a correctness gate, not a performance metric; the discriminating metrics are Det at equal budget, FAR, and risk-coverage. Validity must additionally be oracle-confirmed to catch contract artifacts (H1 secondary).
4. FAR denominators: counting INSUFFICIENT as non-assurance means a system could lower FAR by abstaining everywhere. That is why H5 (coverage floor 0.60) and the abstention report are co-primary; a FAR win with coverage below the floor does not count.
5. The spine's equal-budget claim presumes a budget currency; this protocol fixes CPU-seconds including all V7 overhead, which is conservative for V7.
6. Real-regression ground truth remains scarce. At the proposed size (~150 Div pairs, ~40 projects), +5pp superiority is near the limit of what can be detected (section 8); the programme may legitimately end with "inconclusive on H7".
