# V8 API reference (generated from source signatures and docstrings; see `sbgv8/schema.py` for shared data types)

CLI: `python -m sbgv8 --help` (subcommands: compare, verify, forge-test, ers, perturb, calibrate, baselines, evaluate, manifest-dev).


## sbgv8.schema
Shared V8 schemas. SINGLE SOURCE OF TRUTH for interfaces between collection, profile, perturbation, calibration, evaluation.

- `EvidenceRecord(pair_id: 'str', project: 'str', family: 'str' = 'unknown', split: 'str' = 'development', y: 'Optional[int]' = None, v7b_verdict: 'str' = '', v7b_level: 'Optional[str]' = None, inputs: 'list' = <factory>, changed_units: 'dict' = <factory>, static_branches: 'dict' = <factory>, declared_channels: 'list' = <factory>, env_id: 'str' = '', env_consistent: 'bool' = True, integrity_ok: 'bool' = True, blockers: 'list' = <factory>, config: 'dict' = <factory>, meta: 'dict' = <factory>) -> None`: EvidenceRecord(pair_id: 'str', project: 'str', family: 'str' = 'unknown', split: 'str' = 'development', y: 'Optional[int]' = None, v7b_verdict: 'str' = '', v7b_level: 'Optional[str]' = None, inputs: 'list' = <factory>, changed_units: 'dict' = <factory>, static_branches: 'dict' = <factory>, declared_channels: 'list' = <factory>, env_id: 'str' = '', env_consistent: 'bool' = True, integrity_ok: 'bool' = True, blockers: 'list' = <factory>, config: 'dict' = <factory>, meta: 'dict' = <factory>)
- `InputEvidence(input_id: 'str', outcome: 'str', lossy: 'bool' = False, degenerate: 'bool' = False, deterministic: 'bool' = True, n_repeat_runs: 'int' = 0, provenance: 'str' = 'declared', provenance_ok: 'bool' = True, obs_fingerprint: 'str' = '', channels_present: 'list' = <factory>, hits: 'dict' = <factory>, branches: 'dict' = <factory>, duplicate_of: 'Optional[str]' = None) -> None`: InputEvidence(input_id: 'str', outcome: 'str', lossy: 'bool' = False, degenerate: 'bool' = False, deterministic: 'bool' = True, n_repeat_runs: 'int' = 0, provenance: 'str' = 'declared', provenance_ok: 'bool' = True, obs_fingerprint: 'str' = '', channels_present: 'list' = <factory>, hits: 'dict' = <factory>, branches: 'dict' = <factory>, duplicate_of: 'Optional[str]' = None)

## sbgv8.collect
V8 collection: run the V7-B engine UNMODIFIED (sbgv7.runner.compare_versions) and capture, from the PARENT process only, the

- `compare(base, variant, entry, inputs, cfg, out_dir, label=None, project=None, family=None)`: Public API: run + sidecar, return the EvidenceRecord. `cfg` may be partial (filled from sbgv7 defaults).
- `run_capture(base, variant, entry, inputs, cfg, out_dir)`: compare_versions(...) + sidecar. Returns the engine's verdict dict (unchanged).

## sbgv8.adapter
Evidence directory (V7-B evidence.jsonl [+ v8_parts.json sidecar]) -> schema.EvidenceRecord. Pure read; never executes anything.

- `channels(obs, summary)`
- `fingerprint(obs)`
- `load_log(d)`
- `load_record(evidence_dir, label=None, project=None, family=None)`
- `load_sidecar(d)`
- `recorded_parts(recs, byid)`: Per-input hit/branch sets recomputed from the Run records themselves (what the sidecar must agree with): {input_id: {hits, branches}}.

## sbgv8.trust
Trust report for one evidence directory + forgery suite. This module DOES NOT claim security: it separates five questions that a hash chain

- `TrustReport(integrity: dict, provenance: dict, authenticity: dict, isolation: dict, issues: list, inference: dict = <factory>) -> None`: TrustReport(integrity: dict, provenance: dict, authenticity: dict, isolation: dict, issues: list, inference: dict = <factory>)
- `check(evidence_dir, shadow=False, expected_sources=None, pinned_head=None)`: expected_sources={'base': path, 'variant': path} and pinned_head (log head hash recorded out of band) are OPTIONAL external anchors;
- `check_sidecar(d)`: {'status': ok|missing|inconsistent, 'detail'}. ok = bound to this log (sha256 + head) and equal to what the Run records themselves say.
- `forgery_suite(cfg_over=None, only=None)`: Run every attack; returns {'meta':..., 'results':[row...]}. Each row: verdict observed, which checks fired, outcome. Unresolved attacks stay listed as SUCCEEDS (open).
- `shadow_check(d, timeout_s=10)`: Re-observe both sides on every recorded input and compare the return-value fingerprint with the recorded variant/base primary observation.
- `shadow_run(src_path, entry, args, kwargs, timeout_s=10)`: One independent minimal observation: a fresh sandboxed child (sbgv7.isolation transport, but NOT harness.py: own canonicaliser, own exec, own result fd).

## sbgv8.profile
Evidence profile phi(E) and a V7-B-style decision on an EvidenceRecord. Reads only evidence fields: NEVER rec.y or rec.meta.

- `build_profile(rec)`
- `v7b_style_decision(rec)`: Replicates sbgv7.decide.decide on a record -> (verdict, level). Approximations (data not in record): truncated/sandbox_ok are assumed

## sbgv8.perturb
Evidence perturbations P1..P9 (post-hoc on recorded evidence; real-execution variants need the collector and are flagged).

- `PerturbationRecord(pid: 'str', params: 'dict', seed: 'int', input_digest: 'str', output_digest: 'str', mode: 'str', execution_required: 'bool', applicable: 'bool' = True, reason: 'str' = '') -> None`: PerturbationRecord(pid: 'str', params: 'dict', seed: 'int', input_digest: 'str', output_digest: 'str', mode: 'str', execution_required: 'bool', applicable: 'bool' = True, reason: 'str' = '')
- `apply(rec, pid, seed=0, **params)`: -> (new_record, PerturbationRecord). Not applicable -> unchanged copy with applicable=False and a reason.

## sbgv8.ers
Evidence Response Signature (ERS): response of ANY predictor to pre-declared evidence perturbations.

- `ActivationStubPredictor()`: Simple deterministic stub: risk = 1 - act_frac; decision from the V7-B-style rules. For tests and CLI smoke only.
- `ERS(pid: 'str', params: 'dict', applicable: 'bool', orig_profile: 'dict', pert_profile: 'dict', orig_risk: 'float', pert_risk: 'float', orig_decision: 'str', pert_decision: 'str', coverage_before: 'dict', coverage_after: 'dict', provenance_status: 'dict', integrity_status: 'dict', expected: 'str', observed: 'str', passed: 'object', tolerance: 'float', delta: 'float', reason: 'str' = '', perturbation: 'dict' = <factory>) -> None`: ERS(pid: 'str', params: 'dict', applicable: 'bool', orig_profile: 'dict', pert_profile: 'dict', orig_risk: 'float', pert_risk: 'float', orig_decision: 'str', pert_decision: 'str', coverage_before: 'dict', coverage_after: 'dict', provenance_status: 'dict', integrity_status: 'dict', expected: 'str', observed: 'str', passed: 'object', tolerance: 'float', delta: 'float', reason: 'str' = '', perturbation: 'dict' = <factory>)
- `cli_register(sub)`
- `compute_ers(rec, predictor, pid, seed=0, **params)`
- `ers_vector(rec, predictor, pids=('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9'), seed=0)`: {ers_<pid>_delta: risk delta}; 0.0 where the perturbation is not applicable (documented convention).
- `run_matrix(records, predictor, pids=('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9'), seed=0)`

## sbgv8.calibrate
Transparent monotone-sign L2-penalised logistic regression of false-assurance risk, P(Y=1 | phi(E), eligible).

- `Model(names, extra_names, coef, intercept, mean, std, lam, tau=-inf, profile_fn=None, extra_fn=None, info=None)`
- `cli_register(sub)`
- `crc_threshold(cal_records, model, alpha, by_project=True)`: EXPLORATORY. Conformal risk control (Angelopoulos et al.) for the JOINT risk J(tau)=E[1(NDO issued and Y=1)].
- `default_profile(rec)`
- `fit(train_records, feature_names, extra_features_fn=None, lam=1.0, profile_fn=None, extra_names=None, tau=-inf)`: Fit on eligible, labelled pairs. `extra_names` = names produced by extra_features_fn (free sign). Returns Model.
- `fit_select(records, names, alphas=(0.15,), inner_k=3, seed=0, B=1000, lam_grid=(0.3, 1.0, 3.0, 10.0), **kw)`: Model selection on inner project folds only: lambda by OOF log loss, thresholds tau_alpha from OOF risks (never from the final
- `has_witness(rec)`
- `is_div(rec)`
- `is_eligible(rec)`
- `oof_risks(records, names, k=3, seed=0, lam=1.0, **kw)`: Project-grouped out-of-fold risk for each record (inner CV). Eligibility-only fitting inside each fold.
- `scores(model, records)`: Risk and eligibility arrays for records (no y access).
- `threshold_for_risk(cal_records, alpha, model, B=1000, seed=0)`: Largest-coverage tau whose upper (95% one-sided) project-cluster-bootstrap bound on selective risk <= alpha, on cal_records
- `v7b_verdict(rec)`

## sbgv8.baselines
The nine pre-declared baselines + feature-set ablations behind one registry: REGISTRY[name](train_records, **kw) -> predictor

- `RandomAbstain(target=0.3, seed=0, issue_rate=1.0)`: Deterministic (seeded, per-pair hash) random abstainer for the registry; use matched_abstention_risk for the 1,000-draw estimate.
- `Rule(fn, name)`
- `cli_register(sub)`
- `make(name, train_records, **kw)`
- `matched_abstention_risk(records, target_coverage, draws=1000, seed=0)`: Baseline 6: among B1-issuable (non-witness) labelled pairs, abstain at random so that coverage (over all labelled pairs) equals
- `model_factory(names, with_ers=False, alphas=(0.1, 0.15))`

## sbgv8.stats
V8 statistics: project-clustered bootstrap, selective risk, matched coverage, calibration metrics, Holm, power report.

- `bca_ci(theta, reps, jack, level=0.95)`: BCa interval; `jack` = leave-one-project-out estimates.
- `boot_metric(fn, y, p, proj, B=2000, seed=0)`: Percentile CI of a metric fn(y, p) under project-cluster resampling (rows replicated by multiplicity).
- `boot_p_one_sided(diff_reps)`: H1: diff > 0 (baseline risk minus system risk). p = (1+#{diff<=0})/(B+1) over valid replicates.
- `brier(p, y)`
- `calibration_slope_intercept(p, y)`: slope: logistic regression of y on logit(p); intercept: calibration-in-the-large with slope fixed to 1 (offset-only fit).
- `cluster_counts(proj, B=10000, seed=0)`: B x N matrix of resample weights: project drawn with replacement, every pair of a drawn project gets its multiplicity.
- `coverage(ndo, w=None)`
- `coverage_at_risk(curve, alpha)`: Largest coverage with empirical risk <= alpha (optimistic: threshold picked on the same data).
- `ece(p, y, nbins=10, quantile=False)`
- `ece_sensitivity(p, y)`: ECE under several binnings; must be reported as a range and never alone (it is binning-dependent).
- `holm(pvals)`
- `logloss(p, y)`
- `logloss_each(p, y, eps=1e-06)`
- `matched_risk(score, elig, y, cstar, w=None)`: Selective risk when the lowest-score eligible pairs are issued until coverage == cstar (fractional at ties). w: B x N weights or None.
- `paired_matched(score_a, elig_a, score_b, elig_b, y, proj, cstar, B=10000, seed=0, jackknife=True)`: Risk(B) - Risk(A) at the same coverage cstar (positive = A safer), paired project-cluster bootstrap. Returns dict.
- `pct_ci(reps, level=0.95)`
- `power_report(proj, y, ndo, target_delta=0.05)`: Precision from the ACTUAL cluster structure of issued-NDO pairs. Status downgrades to pilot/exploratory when
- `project_folds(proj, k, seed=0)`: Deterministic project-grouped fold id per pair; a project is in exactly one fold. Greedy size balancing after seeded shuffle.
- `redundancy_table(X, names, thresh=0.8)`: Spearman correlation matrix, VIF per feature, and the list of |rho|>=thresh pairs.
- `reliability_bins(p, y, nbins=10, quantile=False)`
- `risk_coverage_curve(score, elig, y)`: Points (coverage, risk, n_ndo) as the threshold sweeps up over distinct eligible scores.
- `rng_for(seed, label='')`
- `select_threshold(score, elig, y, proj, alpha, B=1000, seed=0, level=0.95)`: Largest-coverage threshold whose one-sided upper project-cluster-bootstrap bound on selective risk <= alpha.
- `selective_risk(y, ndo, w=None)`: R = P(Y=1 | NDO) ; nan if no NDO. `ndo` may be fractional (0..1).

## sbgv8.evaluate
Evaluation driver: nested project-grouped CV of all baselines/ablations, primary matched-coverage comparison, tables, plots.

- `cli_register(sub)`
- `default_ers_factory(pids=None)`: model -> (extra_features_fn, extra_names) using sbgv8.ers (None if ers/perturb unavailable).
- `load_records(path)`
- `rank_scores(score, elig, fold)`: Within-fold average-rank of the risk among eligible pairs, scaled to (0,1]. Pooled outer-fold models have different intercepts, so raw
- `run(records, out_dir, seed=0, B=10000, outer_k=5, profile_fn=None, ers_factory='default', fit_B=500, plots=True, extra_banner=None, strict_blockers=False)`

## sbgv8.manifest
V8 dataset manifest: data model, validation, JSONL/CSV IO, deterministic hashing, development-manifest builder.

- `ManifestRow(project: 'str', family: 'str', family_rule: 'str', pair_id: 'str', split: 'str' = 'development', version_info: 'dict' = <factory>, change_meta: 'dict' = <factory>, observation_boundary: 'dict' = <factory>, adjudication_budget: 'dict' = <factory>, outcome_class: 'str' = 'not_adjudicated', y: 'Optional[int]' = None, label_source: 'str' = '', provenance: 'dict' = <factory>, include: 'bool' = True, reasons: 'list' = <factory>, status: 'str' = '') -> None`: ManifestRow(project: 'str', family: 'str', family_rule: 'str', pair_id: 'str', split: 'str' = 'development', version_info: 'dict' = <factory>, change_meta: 'dict' = <factory>, observation_boundary: 'dict' = <factory>, adjudication_budget: 'dict' = <factory>, outcome_class: 'str' = 'not_adjudicated', y: 'Optional[int]' = None, label_source: 'str' = '', provenance: 'dict' = <factory>, include: 'bool' = True, reasons: 'list' = <factory>, status: 'str' = '')
- `build_dev_manifest(records_path='datasets/v8/dev_records.jsonl', csv_path='results/v7b_phase2_summary/p2_e3_20261118_092700/processed/dev_pairs_per_system.csv')`: Prefer dev_records.jsonl (EvidenceRecord JSON, one per line); else the Phase 2 per-system CSV (one row per pair, system B1).
- `cli_register(sp)`
- `derive_family_dev(pair_id)`: Label-independent family rule arm_prefix_v1 (see FAMILY_RULE_DEV_DOC).
- `manifest_hash(rows)`: Order-independent sha256 over row digests (sorted by pair_id).
- `read_csv(path)`
- `read_jsonl(path)`
- `validate(rows, raise_on_error=False)`: Return list of issue strings (empty = valid).
- `write_csv(rows, path)`
- `write_jsonl(rows, path)`

## sbgv8.splits
Project-aware splitting, leakage checks, nested grouped folds, family-shift split, and the holdout label guard.

- `HoldoutGuard(token_path=None, log_path=None)`: Reading labels of holdout rows raises unless `token_path` is given AND the file exists. The module never writes a token;
- `HoldoutLocked(...)`: Not enough permissions.
- `assert_heldout_families(a)`
- `assert_no_leakage(assignment, families=False)`: Raise AssertionError when a project (and, if families=True, a family) appears in more than one split.
- `family_shift_feasibility(items, min_families=3, min_projects_per_family=5, min_labelled_pairs_per_family=20, max_family_share=0.6)`: Report whether the data supports a project-family shift experiment, and why not. Counts only labelled (y in 0/1) pairs.
- `family_shift_split(items, seed, held_out_families=None, n_held_out=1, calib_fraction=0.3)`: Train/calibrate on some families, evaluate on held-out families. Within train families projects are split (project-aware) into
- `nested_group_folds(items, seed, outer_k=5, inner_k=3, group='project')`: Yield dicts {outer, train_groups, test_groups, inner:[{train_groups,val_groups}]}; every fold is group-disjoint.
- `project_split(items, seed, fractions=None, group='project', strata=None)`: items: manifest rows, EvidenceRecords or dicts (need pair_id, project, family). group: 'project'|'family'.
- `strip_holdout_labels(items)`: Return dict copies of items with y/outcome removed for holdout rows (safe default view).

## sbgv8.adjudication
Blinded adjudication workflow model (Phase 3 tooling; no adjudicator or decision is ever fabricated here).

- `AdjudicationCase(pair_id: 'str', observation_boundary: 'dict', budget: 'dict', evidence_reviewed: 'tuple' = ()) -> None`: AdjudicationCase(pair_id: 'str', observation_boundary: 'dict', budget: 'dict', evidence_reviewed: 'tuple' = ())
- `BlindingViolation(...)`: Inappropriate argument value (of correct type).
- `BudgetFrozen(...)`: Unspecified run-time error.
- `Workflow(log_path, clock=<function _now at 0x109f44680>)`: State is rebuilt by replaying the JSONL hash chain at `log_path`. roles: 'primary' (exactly two distinct adjudicators) and
- `agreement_report(wf, kappa_min=0.7, min_double_fraction=0.3)`
- `check_blind(obj, path='case')`
- `cohen_kappa(a, b, labels=('confirmed_divergence', 'no_divergence_found_within_budget', 'unresolved'))`: Returns dict(kappa, po, pe, n, note). Degenerate marginals (pe == 1, i.e. both raters use one identical category): kappa is
- `confusion_matrix(a, b, labels=('confirmed_divergence', 'no_divergence_found_within_budget', 'unresolved'))`
- `estimand_variants(outcomes, issued=None)`: outcomes: {pair_id: outcome}. Returns {variant: {'y': {pair: y}, 'n_unresolved', ['risk','n_issued']}}.
- `verify_chain(path)`
- `y_from_adjudication(outcome, unresolved='drop')`: confirmed -> 1, none_found -> 0. unresolved: 'drop' -> None (excluded, counted); 'worst_case_divergence' -> 1; 'non_divergence' -> 0.
