# P0: Benchmark Construction Protocol and Prospective Power Analysis

Status: DRAFT for freeze at G0. Amends SBG_V7_EXPERIMENTAL_PROTOCOL.md ("EP") sections 3 and 8 (EP's own power sketch is cross-checked in 6.9). Companion: P0_INTERNAL_ONLY_GROUND_TRUTH_PROTOCOL.md ("GT"). Nothing here uses V7 output; no V7 code exists. All simulation numbers are model-based with the assumptions stated in 6.1; they are not predictions of V7 performance.
Code: reports/v7_design/p0_reconciliation/power/ (power_sim.py, anchors_perm.py, summarize.py); raw outputs in power/out/*.csv, RESULTS.txt, TABLES.txt. Interpreter: /Users/manassakthivel/Desktop/SBG-V6/.venv/bin/python (numpy 2.5.5, scipy 1.18.1). Master seed 20261117 (every configuration draws from default_rng([20261117, counter]), counter order fixed by the script). Re-running reproduces the CSVs.

## 1. Verdict (read this first)

The proposed sample (about 150 divergent pairs, 40+ projects, about 4 divergent pairs per project) is NOT sufficient for the protocol's confirmatory claims as written. Thresholds are not relaxed here; the consequences are stated as recommendations (section 7).

| Claim | Powered at ~150 Div pairs / 40 projects? | Smallest effect detectable with 80% power (40 projects, m=4, rho=.15, discordant rate .20) | What the data can support |
|---|---|---|---|
| H2/H4 superiority +5pp over same-budget DT | No: 22% power (t-test), 14% (the protocol's sign-flip test) | 12.5pp (alpha .05), 14pp (alpha .0167) | Only large effects (>= ~12pp) |
| +10pp | Marginal: 63% (t), 58% (sign-flip) | | |
| H2 non-inferiority at -2pp | No: 8% to 11% at true delta 0 | needs about 8000 divergent pairs for ~90% power | A CI, not a confirmatory NI claim |
| H7 hard-stratum +3pp, on H-R AND H-M | No: about 6% (H-R, ~40 hard pairs) and 8% (H-M, ~100 hard pairs) | not reached at any size up to 1200 Div pairs (20%) | Estimation only; null is uninformative |
| H8a annotation >= 70% (lower bound rule) | No at realistic H-R prevalence (10% to 20% gives 17 to 38 IO pairs): 20% to 50% power even at a true rate of 85% | needs about 100 IO pairs at a true rate 85%; 40 to 50 at 90% | Constructed IO items in H-M (quota), not H-R |
| H8b false alarm <= 1% | No: 0% power at 150 Div; needs >= ~300 effective IO pairs | needs >= 600 IO pairs in >= 150 independent clusters even at true rate 0 | Estimation with upper bound only |

## 2. Units of analysis: pairs, projects, lineages, clusters

Four different counts are reported for every set, and sample-size targets apply to the LAST applicable one, not to pairs.

- Pairs: raw (old, new, scope) records after eligibility filtering.
- Independent projects: distinct repositories (by URL, package name and source-hash; forks collapse into the upstream). For H-M, the analogue is base programs.
- Independent change lineages: a lineage is a set of pairs descended from one logical change (the same fix cherry-picked or merged across branches/forks/backports, a revert-and-reapply, a mechanical refactor applied in many files by one commit, or several mutants made from the same template on the same base function). Pairs in a lineage are near duplicates (MinHash Jaccard >= 0.8 on normalised AST diff, or shared commit patch-id). A lineage counts once.
- Independent clusters: the unit of resampling in the inference (EP 8). Primary cluster = project (H-R) or base program (H-M). Where a lineage spans projects, projects connected by a shared lineage merge into one cluster (union-find over lineage edges). The cluster count K used in all inference and in the power tables below is this number.

Why they differ materially: in simulation (power/out/lineage_duplicates_power.csv), 150 raw divergent pairs in 40 projects with ~2 pairs per lineage (75 independent lineages) drop power at +10pp from 63% to 45%; with 3 per lineage (50 lineages) to 34%; at +5pp the figures fall from 20% to 13% and 11%. A target of "150 divergent pairs" is therefore a floor on independent lineages, not on pairs.

Reporting rule: every table lists raw pairs, de-duplication groups, independent lineages, independent clusters, mean/max cluster size, estimated ICC, design effect 1 + (m-1)rho, and Kish effective sample size. Design caps: <= 8 pairs per project (EP), <= 5% of a set per project, <= 3 pairs per lineage kept (extras go to a lineage-duplicates appendix and are excluded from the primary denominators).

## 3. Truth classes (five) and their roles in metrics

Definitions and the evidence needed are in GT section 1.2 and 2. Summary of use:

| Class | Short definition | In Det / FAR denominator (H2-H6) | In H7 | In H8 | Notes |
|---|---|---|---|---|---|
| 1 Observable divergence (Div) | exists input in declared domain with output difference under boundary B | yes (all) | hard stratum if seed-corpus outputs equal | no | replayed witness is sufficient evidence |
| 2 Internal-only (IO) | no output difference on whole declared domain (T1/T2), but a pre-declared kappa-canonical internal predicate differs | no | no | denominator for H8a, H8b | verdict DIVERGENT-by-interface is a false alarm |
| 3 Representation-only (RO) | no output difference and no kappa-difference; code/trace/representation differ | no (Eq-B) | no | negative control for annotation (proposed H8c) | refactors, renames, temps, normalised repr |
| 4 Unactivated changed region | changed region reachable but not executed by any truth-team input | no, reported separately | no | no | maps to INSUFFICIENT/NOT_ACTIVATED; measures abstention honesty |
| 5 Insufficient/ambiguous | evidence tier too weak, nondeterministic, boundary-sensitive, tool or adjudicator disagreement | excluded from primary denominators, always reported with sensitivity bounds | excluded | excluded (sensitivity: counted as IO / as Div) | >15% of a source flags the source |

## 4. Per-pair record

One record per pair, stored in `corpus_manifest` (hashed, Merkle root per EP 3.3); labels in the separate sealed artifact. Fields (required unless marked optional):

| Group | Field | Content |
|---|---|---|
| Project identity | project_id, repo_url, package, license, language/runtime version | canonical identity used for independence checks |
| Versions | base_ref, modified_ref, base_hash, modified_hash, scope (entry points, signature), diff_summary | commit SHAs or content hashes; scope declared before labelling |
| Change lineage | lineage_id, lineage_parent (optional), patch_id, template_id (H-M), near_dup_group, cluster_id | for independence and clustering |
| Input provenance | input_source in {truth_generator, spec_example, repo_test_at_parent, author_authored}; X_b/X_ref descriptors and hashes; seed corpus id; `sbg_inputs_used_for_truth` (must be false) | no SBG or baseline input enters truth except via the refutation channel (GT 2.6) |
| Environment | OS, interpreter, dependency lock hash, PYTHONHASHSEED=0, sandbox spec, time/memory limits, virtualised sources | needed for replay |
| Expected behaviour | contract/spec reference, boundary B (channels, N_out), expected class by the authoring team (H-M) | stored as `label_original` |
| Ground-truth rationale | class, reason code, evidence tier, witness id or exhaustive-run id, PDF hash, predicate list Pi, k (sequence length) | `label_rh`, `label_final` |
| Independent adjudication | adjudicator ids (pseudonymised), votes, rubric hash, agreement flag, A3 rationale, ledger hash | blind per GT 4 |
| Reproducibility | replay count r, V1-vs-V1 and V2-vs-V2 identical flag, RH-A/RH-B agreement, runtime, deterministic flag | |
| Label confidence | high / medium / low plus a numeric tier T1-b, T1-f, T2, T3 | high = T1-b/T2 and adjudicator agreement; medium = T3 with written concurrence or RH disagreement resolved; low = single-method; low-confidence items are in sensitivity strata, not dropped |
| Strata tags | hard_stratum (seed-corpus outputs equal), boundary_sensitive, source_set, time_bucket | |

## 5. Benchmark construction protocol

1. Sets and roles are as in EP 3.2 (H-R real regressions, H-M authored mutants with independent oracles, H-P prospective, H-X reserve). V5/V6/QuixBugs/BugsInPy remain NON-PRISTINE (EP 3.1).
2. Cluster-first planning: the target is stated in independent clusters and independent lineages first, pairs second. Enrolment stops when the pre-declared cluster/lineage targets are met or the mining window closes, decided without reference to any system output.
3. Per-source quotas by truth class (decided before labelling, filled by the truth pipeline): H-R: Div >= (see 7), controls (RO/IO/Eq) matched per project, Unactivated and Insufficient reported as they fall. H-M: IO quota set by design (see 7), RO quota, Div families with exposed-on-rare-region subtype, equal-sized families so a family is not label-predictive (EP).
4. Matched controls: every project contributing Div pairs should contribute at least one behaviour-preserving control (RO/IO candidate) where available; >= 20 mixed-class projects (EP).
5. Truth pipeline as in GT: PDF written and hashed first; RH-A/RH-B evidence; two blind adjudicators; labels sealed before any system run on the holdout; the evaluation runner mounts inputs only.
6. Shortcut probe (EP 6.1): edit-size-only AUROC <= 0.65; otherwise edit-size-matched subset is co-primary.
7. Pilot before freezing targets: DEV-N must provide estimates of the discordant rate pi, the ICC rho, the base detection rate, the hard-stratum share and the IO/RO prevalence, using the same truth pipeline on a different time window and different projects. The power analysis in section 6 is then re-run (power_sim.py parameters) and the sample targets amended BEFORE sealing. This is required by EP 8 and is not optional here.

## 6. Prospective power analysis

### 6.1 Model
- Unit of analysis: divergent pair (truth = Div). Two arms paired on the same pairs: A = same-budget differential testing, B = V7. Outcome per arm is binary (detected, or for FAR "not falsely assured"). FAR has the same paired structure with delta = absolute FAR reduction; EP's alternative "relative reduction >= 25%" equals delta = 0.25 x FAR(A) (for FAR(A) = 0.40, 10pp; for 0.20, 5pp; so the absolute 5pp branch is binding only when FAR(A) <= 0.20).
- Cell probabilities (both, A only, B only, neither): q10 = (pi - delta)/2, q01 = (pi + delta)/2, q11 = p0 - q10, q00 = remainder, with p0 = arm A success rate, pi = discordant rate P(A != B), delta = q01 - q10.
- Cluster (project) heterogeneity: each project draws its own cell probabilities from Dirichlet(alpha q), alpha = 1/rho - 1; this makes the ICC of the paired difference exactly rho (verified empirically: nominal 0.15, measured 0.153, RESULTS.txt). Cluster size m_j = min(8, 1 + Poisson(m - 1)), the EP cap of 8. m = mean divergent pairs per project (150 pairs / 40 projects = 3.75, labelled "m=4").
- Test: cluster-robust ratio estimator with t on K-1 df, two-sided, success = p < alpha and estimate > 0. alpha = 0.05 and alpha = 0.05/3 = 0.0167 (a Holm-conservative proxy for the three budgets in H2). Type-I check under delta = 0: 0.0262 and 0.0279 per tail against a nominal 0.025 (RESULTS.txt).
- Cross-check with the protocol's own test (cluster sign-flip permutation, 2000 flips, 1000 sims, anchors_perm_vs_t.csv): the t-test is optimistic at small K. At 40 projects the permutation test has 14% power at +5pp (t: 20%), 58% at +10pp (t: 63%), 39% for pi = .3 at +10pp (t: 46%); the two agree within about 2pp at K >= 200.
- Replicates: 1500 per grid cell (800 for required-K searches, 500 for MDE scans; Monte-Carlo SE about 1 to 2.5 pp).
- Limitations: binary outcomes; one budget; Dirichlet heterogeneity is one plausible form; independence between the 3 budgets and the multiple hypotheses is not modelled; pi and rho are unknown and are the parameters most needing DEV-N estimates.

### 6.2 Headline paired comparison: power
Power in percent, p0 = .6, rho = .15, m = 4 (so pairs about 4K). "a05 | a0167" = alpha .05 | alpha .0167. Base detection rate has almost no effect (p0 = .4 / .6 / .8 at K=40, pi=.2: +5pp 22/22/21%; +10pp 65/63/63%) because the paired test depends on discordance, not the marginal rate.

| K projects (pairs) | pi=.10 +3pp | +5pp | +10pp | pi=.20 +3pp | +5pp | +10pp | pi=.30 +3pp | +5pp | +10pp |
|---|---|---|---|---|---|---|---|---|---|
| 20 (80) | 8 / 2 | 18 / 5 | 74 / 38 | 6 / 2 | 12 / 5 | 38 / 20 | 6 / 2 | 10 / 4 | 26 / 13 |
| 30 (120) | 12 / 5 | 30 / 13 | 95 / 77 | 10 / 4 | 17 / 7 | 53 / 32 | 7 / 3 | 12 / 6 | 35 / 20 |
| **40 (160)** | 16 / 6 | 36 / 18 | 100 / 96 | 9 / 4 | **22 / 11** | **63 / 45** | 9 / 3 | 13 / 6 | 45 / 29 |
| 50 (200) | 20 / 9 | 45 / 27 | 100 / 99 | 13 / 6 | 26 / 13 | 74 / 57 | 10 / 5 | 18 / 9 | 53 / 35 |
| 60 (240) | 24 / 12 | 51 / 33 | 100 / 100 | 15 / 7 | 28 / 16 | 82 / 66 | 11 / 4 | 21 / 11 | 64 / 46 |
| 80 (320) | 29 / 16 | 66 / 48 | 100 / 100 | 17 / 7 | 38 / 23 | 91 / 81 | 13 / 6 | 27 / 16 | 75 / 60 |

ICC sensitivity at K=40, m=4, pi=.2 (alpha .05): rho .05 / .15 / .30 gives +5pp 26 / 22 / 18% and +10pp 75 / 63 / 50%. Full grid: power/out/headline_power_grid.csv (1458 cells: K 20 to 80, m 2/4/8, rho .05/.15/.30, p0 .4/.6/.8, pi .1/.2/.3, delta 3/5/10pp).

### 6.3 Minimum detectable effect (80% power, p0 = .6, m = 4)
Entries are MDE in pp, alpha .05 | alpha .0167 ("n/a" = not reached below the discordance ceiling pi).

| pi | rho | K=20 | K=30 | K=40 | K=60 | K=80 | K=120 |
|---|---|---|---|---|---|---|---|
| .10 | .05 | 9.5 / n/a | 8.5 / 9.5 | 7.0 / 8.5 | 6.5 / 7.0 | 5.5 / 6.5 | 4.5 / 5.0 |
| .10 | .15 | n/a | 9.0 / n/a | 8.0 / 9.0 | 7.0 / 8.0 | 6.0 / 7.0 | 5.0 / 6.0 |
| .20 | .05 | 15.0 / 17.0 | 12.5 / 14.5 | 11.0 / 12.5 | 8.5 / 10.0 | 8.0 / 9.0 | 6.0 / 7.5 |
| **.20** | **.15** | 15.5 / 18.5 | 13.5 / 16.0 | **12.5 / 14.0** | 10.0 / 11.5 | 9.0 / 10.0 | 7.5 / 8.5 |
| .20 | .30 | 18.5 / 20.0 | 15.5 / 17.5 | 13.5 / 16.0 | 11.5 / 13.0 | 10.0 / 11.5 | 8.5 / 9.5 |
| .30 | .15 | 21.0 / 24.0 | 17.5 / 19.5 | 15.0 / 17.5 | 12.5 / 14.5 | 11.0 / 12.5 | 9.0 / 10.0 |
| .30 | .30 | 23.0 / n/a | 19.0 / 22.5 | 17.5 / 19.0 | 14.0 / 16.0 | 12.0 / 14.5 | 10.5 / 12.0 |

Pairs per project (pi=.2, rho=.15, alpha .05, K=40): m=2 (80 pairs) 15.0pp; m=4 (160) 12.5pp; m=8 (320) 10.5pp. Projects matter more than pairs per project. Full table: power/out/headline_mde.csv.

So at the proposed size the protocol can only detect an advantage of about 8pp (if V7 and DT disagree on only 10% of pairs) to about 15pp (30% discordance). The +5pp superiority margin is detectable only if discordance is about 10% or less AND K is about 100 or more.

### 6.4 Required numbers (80% power, p0 = .6, m = 4)
Smallest K from the grid {20, 30, 40, 50, 60, 80, 100, 150, 200, 300, 450, 700, 1000, 1500, 2500} reaching 80% power. Entry = projects at alpha .05 | alpha .0167; pairs = about 4 x projects (m = 4); for m = 8, K is roughly halved at the same pair count only when rho is small. (power/out/headline_required_projects.csv has m = 4 and 8.) Values are one grid step coarse.

| rho | pi | +3pp | +5pp | +10pp |
|---|---|---|---|---|
| .05 | .10 | 300 / 450 | 100 / 150 | 20 / 30 |
| .05 | .20 | 700 / 700 | 200 / 300 | 50 / 80 |
| .05 | .30 | 1000 / 1500 | 300 / 450 | 80 / 100 |
| .15 | .10 | 450 / 700 | 150 / 150 | 30 / 40 |
| **.15** | **.20** | 700 / 1000 | **300 / 450** | **60 / 80** |
| .15 | .30 | 1500 / 1500 | 450 / 700 | 100 / 150 |
| .30 | .10 | 450 / 700 | 150 / 300 | 30 / 50 |
| .30 | .20 | 1000 / 1500 | 450 / 450 | 80 / 150 |
| .30 | .30 | 1500 / 2500 | 700 / 700 | 150 / 200 |

Central case (pi .2, rho .15): +10pp needs about 60 projects (240 divergent pairs; 80 projects at the multiplicity-adjusted alpha); +5pp needs about 300 projects (about 1200 pairs; 450 projects at the adjusted alpha); +3pp needs about 700 projects (about 2800 pairs). These agree with EP's own sketch (265 to 480 raw pairs for +10pp, 1050 to 1950 for +5pp): the simulation confirms the sketch rather than contradicting it. The problem is that the proposed H-R target (150 Div pairs, 40 projects) sits below the sketch's own requirement for either margin. The requirement is on independent lineages/clusters (section 2); duplicates inflate raw pairs without helping.

### 6.5 H2 non-inferiority (margin -2pp, lower paired CI bound > -2pp)
Power by sample size, rho = .15, m = 4 (non_inferiority power in power/out/noninferiority_power.csv):

| K (pairs) | pi=.10, true delta 0 | pi=.10, true +2pp | pi=.20, true delta 0 | pi=.20, true +2pp |
|---|---|---|---|---|
| 40 (160) | 11% | 28% | 8% | 15% |
| 200 (800) | 29% | 84% | 18% | 54% |
| 500 (2000) | 63% | 100% | 36% | 89% |
| 1000 (4000) | 90% | 100% | 61% | 99% |
| 2000 (8000) | 99% | 100% | 91% | 100% |

A -2pp non-inferiority margin needs several thousand divergent pairs (about 8000 at pi=.2 if V7 and DT truly tie). It is infeasible for H-R and for H-M. This is an arithmetic property of a 2pp margin, not of V7. Options: (a) do not make a confirmatory non-inferiority claim and report the CI; (b) expand about 50 fold (rejected as infeasible); (c) change the margin only by a justified, pre-registered amendment under EP/Gates D and not on power grounds. This document does not alter the margin.

### 6.6 Adjudication label noise
Model: a fraction e of the pairs labelled Div are truly non-divergent (IO/RO/Eq mislabelled as Div); on these both arms fire with probability .03, independent (label_noise_power.csv). Effects (p0 = .6, pi = .2, rho = .15, m = 3.75):

| K | e | observed delta when true +5pp | power at +5pp | observed delta when true +10pp | power at +10pp |
|---|---|---|---|---|---|
| 40 | 0 | 5.1 | 22% | 10.0 | 64% |
| 40 | .10 | 4.6 | 19% | 9.1 | 58% |
| 40 | .25 | 3.7 | 17% | 7.2 | 48% |
| 80 | 0 | 5.0 | 35% | 10.0 | 90% |
| 80 | .10 | 4.6 | 33% | 9.1 | 87% |
| 80 | .25 | 3.7 | 28% | 7.5 | 81% |
| 200 | 0 | 5.0 | 70% | 10.0 | 99.9% |
| 200 | .15 | 4.3 | 65% | 8.6 | 99.9% |

Random mislabelling dilutes delta by roughly (1 - e) and costs 2 to 5 points of power at these sizes; the bigger damage is to H8 (6.8). Noise that correlates with a system's output (e.g. IO mislabelled Div whose divergence one arm flags) is NOT modelled and is the reason for blind adjudication and the refutation-channel controls (GT C5 to C7). Realistic noise: V6 had 8.7% unresolved changed pairs; a kappa of 0.80 implies about 5% to 10% disagreement on the contested boundary.

### 6.7 H7: internal-state gain on the hard stratum
Success defined as: Holm-style two-sided p < alpha, estimate >= +3pp, hard stratum = truth Div and seed-corpus outputs equal (EP: about 27% of changed pairs in V6-type data; H-M oversamples hard families, assumed 50%). Hard-stratum arm-A detection p0 = .3 (power insensitive to p0), pi = .2, rho = .15. (h7_hard_stratum_power.csv has pi .1/.2/.3, delta 3/5/10pp, rho .05/.15/.30, p0 .3/.5.)

| Design | Hard pairs | Power at +3pp | +5pp | +10pp |
|---|---|---|---|---|
| H-R as proposed (40 projects, 150 Div) | about 41 | 6% | 8% | 26% |
| H-M as proposed (40 programs, 200 Div, 50% hard) | about 100 | 8% | 16% | 49% |
| H-R expanded (80 projects, 300 Div) | about 81 | 8% | 13% | 47% |
| H-R expanded (150 projects, 600 Div) | about 162 | 12% | 27% | 78% |
| H-R expanded (300 projects, 1200 Div) | about 324 | 20% | 46% | 97% |
| H-M expanded (80 programs, 400 Div) | about 200 | 15% | 28% | 78% |

H7 as written requires positive results on BOTH H-R and H-M, so joint power is the product of the two independent-set powers (assuming independence): as proposed, +5pp about 8% x 16% = 1.3%; +10pp about 26% x 49% = 13%. Even doubling H-M and expanding H-R to 300 Div pairs gives about 13% x 28% = 3.6% at +5pp. A +3pp effect is not detectable at any feasible size (best case 20% at 1200 Div pairs). IO prevalence does not enter H7 power (IO is not in the Det denominator); it enters only through IO-to-Div mislabelling (6.6).

Consequence: with the sample as proposed, "H7 fails" is the overwhelmingly likely outcome whether or not internal-state views help. A null on H7 is therefore uninformative about the mechanism and must be reported as inconclusive (its CI), not as evidence that internal state does not help; the V7-B fallback claim stays legitimate, but a V7-A claim ("internal-state divergence adds information") is not obtainable at this sample size unless the effect is >= 10pp on a hard stratum of >= 160 pairs per holdout.

### 6.8 Internal-only experiment (H8)
IO count in H-R = 150 x p/(1 - p) with p = IO / (IO + Div) among internally divergent pairs; p = 5%, 10%, 20%, 30% gives 7.9, 16.7, 37.5, 64.3 IO pairs (reading p as the share among 150 total gives 7.5, 15, 30, 45; same conclusions). Realistic p: V6 "masked" share 15.6% of internally divergent pairs (SBG-defined, upper bound; GT section 6).

H8a (annotation >= 70% among IO pairs where the state view fires). State view fires on 80% of IO pairs (assumed). K = 40, rho = .15. Power by rule (percent), point-estimate rule / one-sided 95% lower-bound rule (design-effect scaled Clopper-Pearson):

| prevalence (IO pairs) | true rate .75 | .85 | .95 |
|---|---|---|---|
| 5% (7.9) | 65 / 1 | 84 / 4 | 96 / 12 |
| 10% (16.7) | 67 / 5 | 93 / 20 | 100 / 61 |
| 20% (37.5) | 73 / 10 | 98 / 50 | 100 / 96 |
| 30% (64.3) | 79 / 15 | 99 / 72 | 100 / 100 |

(each cell "point / lower-bound"). The point-estimate rule passes easily but has no error control (a system at a true rate of exactly 70% passes about half the time; not simulated) and is NOT acceptable evidence. The lower-bound rule needs IO counts that H-R will not supply. Required IO pairs for 80% power on the lower-bound rule (h8a_required_n_io.csv): true rate .80 gives about 300 (rho .15; not reached below 400 at rho .30); .85 gives about 100; .90 gives 40 to 50; .95 gives about 30.

H8b (false alarm <= 1%; one-sided 95% upper bound, design-effect scaled). With a 1% claim the zero-event requirement is about 299 effective IO pairs (1 - 0.05^(1/n) <= 0.01); clustering divides n by the design effect 1 + (m - 1)rho. Power from h8b_false_alarm_power.csv (rho = .15):

| IO pairs | clusters | true FA 0, labels perfect | true FA .2% | true FA .5% | any true FA, 2% of IO labels actually Div |
|---|---|---|---|---|---|
| 8 to 64 (H-R) | 40 | 0% | 0% | 0% | 0% |
| 300 | 40 | 0% | 0% | 0% | 0% |
| 600 | 40 | 0% | 0% | 0% | 0% |
| 600 | 150 | 100% | 44% | 13% | 0.7% |
| 1000 | 250 | 100% | 83% | 33% | 0.9% |
| 1500 | 375 | 100% | 95% | 49% | 1.2% |
| 3000 | 750 | 100% | 99.95% | 79% | 1.5% |

Two findings. (i) The 1% cap is demonstrable only with several hundred IO pairs spread over >= 150 independent clusters, and even then only if the true false-alarm rate is below about 0.3%. (ii) Adjudication contamination is fatal: if 2% of IO-labelled pairs are truly Div and V7 correctly flags half of them DIVERGENT, the measured false-alarm floor is 1.0% before any real false alarm, so the claim fails at every n. This makes IO labels the single most consequential labelling task: they need T1-b/T2 evidence of "no output difference on the declared domain" (GT 2.3), and the contamination rate must be audited to well below 2%.

### 6.9 Is the proposed sample sufficient? (explicit statement)

No. With about 150 divergent pairs in about 40 projects:
- The paired headline comparison can detect only about 12.5pp (range 7pp to 17.5pp over discordance .10 to .30 and ICC .05 to .30) at 80% power. The protocol's +5pp superiority margin has 22% power (14% with the sign-flip test); +10pp has about 60%.
- Non-inferiority at -2pp is not testable (about 10% power).
- H7 at +3pp on both holdouts is not testable (joint power under 2%); a null result carries almost no information.
- H8a and H8b cannot be confirmed on H-R (8 to 64 IO pairs); H8b needs hundreds of IO pairs in >= 150 clusters.
The protocol itself already concedes part of this (EP 8 and risk 6: "+5pp is at the edge of detectability", "may legitimately end with inconclusive on H7"). The simulation agrees with EP's sketch (265 to 480 raw pairs for +10pp, 1050 to 1950 for +5pp) and shows that the proposed target (150 Div pairs) is below the sketch's own requirement for both margins, not merely near an edge. Independent clusters, not pairs, are the binding resource.

## 7. Recommendations (expand OR narrow; thresholds unchanged)

R1 Expand the primary H-R divergent sample to the size that supports the claim, or narrow the claim:
- To keep the +5pp superiority claim at pi about .2: about 300 independent projects (about 1200 independent-lineage divergent pairs). At pi about .1 (V7 and DT disagree on only one pair in ten): about 150 projects. Neither is realistic for fresh post-T0 Python regressions with per-project caps.
- To narrow: state the confirmatory superiority claim at +10pp, which at pi .2 and rho .15 needs about 60 projects (about 240 independent divergent pairs; 80 projects at the adjusted alpha) and at pi .3 about 100 to 150 projects. Raise the H-R target from "40+ projects / 150 Div" to at least 60 to 80 projects / about 250 to 320 independent divergent pairs. Keep +5pp as an estimation target with its CI, labelled exploratory, unless the DEV-N pilot shows pi <= .10.
- Pool H-R and H-M only by pre-declared amendment (they differ in construction and cluster type; EP 8 already allows pooling the hard stratum); the power in 6.2 applies to the pooled K if the pooled cluster count is used and heterogeneity is modelled.

R2 Non-inferiority at -2pp: do not carry it as a confirmatory claim (needs thousands of pairs). Report the paired CI. Do not widen the margin to manufacture power; any margin change needs an independent justification and the amendment procedure.

R3 H7: either (a) designate H7 as an estimation objective with a pre-stated interval and an "inconclusive" outcome (recommended), or (b) expand each holdout's hard stratum to >= 160 pairs (about 600 Div pairs in about 150 projects for H-R, about 320 in 80 programs for H-M), which still gives only 27% to 28% power at +5pp per holdout and fails to reach +3pp. The +3pp margin is not powered at any feasible size and should not be cited as a pass/fail criterion.

R4 H8: move confirmatory H8 to H-M, where IO items can be built to a quota: >= 100 IO items in >= 40 base programs (>= 60 programs if ICC is .3) supports H8a with the lower-bound rule when the true annotation rate is >= .85; for H8b at 1%, build >= 600 IO items in >= 150 independent base-program/template clusters and audit label contamination to < 0.5%. Otherwise report H8b as an estimate with its upper bound (for example 0 of 38 gives an upper bound near 7%) and drop the "<= 1%" claim. In H-R, report IO counts descriptively.

R5 Cluster accounting: apply targets to independent clusters and lineages (section 2); keep <= 3 pairs per lineage in primary analysis.

R6 Re-run: before G0 closes, estimate pi, rho, hard-stratum share, IO/RO prevalence and label-noise rates on DEV-N with the GT pipeline, then rerun `power_sim.py` with those parameters and amend targets pre-seal. The numbers in this document are conditional on assumed pi in [.1, .3] and rho in [.05, .30].

## 8. Reproduction
- `.venv/bin/python reports/v7_design/p0_reconciliation/power/power_sim.py` writes power/out/*.csv, RESULTS.txt (self-checks) and takes about 2 minutes. `anchors_perm.py` writes anchors_perm_vs_t.csv; `summarize.py` prints the pivots used above (TABLES.txt).
- Seeds: master 20261117 with an incrementing counter; no other randomness.
- Known coarseness: required-K values are one grid step coarse; MDE steps are 0.5pp; "n/a" means the threshold was not reached within the discordance ceiling pi (delta cannot exceed pi).
