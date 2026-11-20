# Claim–evidence register

This register covers the manuscript in `paper/IEEE_ACCESS_V8_FINAL/` (branch `research/v8-linux-validation`).

Paths are relative to the repository root unless they start with `audit/`, `scripts/` or `tables/`, which live in this directory.

Confidence classes:
- **D**: directly demonstrated
- **S**: supported but limited
- **E**: exploratory
- **N**: not established (stated as such in the paper)
- **F**: future work

## Scientific claims

| # | Claim (as worded in the paper) | Evidence source | Experimental support | Conf. | Location |
|---|---|---|---|---|---|
| 1 | The false-assurance risk R = P(F=1 \| NDO) is defined relative to O, B and the change population; it is a selective risk, not an equivalence claim | Definition; El-Yaniv & Wiener 2010; Geifman & El-Yaniv 2017 | Formal definition (no experiment needed) | D | §III-C, Eqs. 1–3 |
| 2 | Unresolved adjudications enter R through complete-case, worst-case and optimistic variants | `sbgv8/adjudication.py`; `reports/v8/V8_ADJUDICATION_PROTOCOL.md` | Implemented and tested on synthetic fixtures | D (design) | §III-C |
| 3 | The profile has 15 change-conditioned features with the stated definitions | `sbgv8/profile.py:44-75`; `audit/ARCHITECTURE_AND_DEFINITIONS.md` §1.2 | Code inspection | D | §IV-B, Table 4 |
| 4 | The observable-influence feature is only a reachability proxy | `profile.py:51-53` | Code inspection | D | §IV-B, §II-C |
| 5 | Provenance, integrity and environment features were constant on the dev corpus | `datasets/v8/dev_records.jsonl` (312 of 312 have `integrity_ok` and `env_consistent` true); adapter never sets provenance | Recount | D | §IV-B, Table 4 |
| 6 | Verdict logic is: trust gate → witness → eligible and risk ≤ τ | `procsep.py:146-149`; `calibrate.py:88-95` | Code inspection | D | §IV-C |
| 7 | CEC is a sign-constrained L2 logistic regression; λ is chosen by inner grouped CV; τ comes from a cluster-bootstrap upper bound | `calibrate.py`; `stats.py:112-126` | Code inspection | D | §IV-D |
| 8 | ERS: 8 properties plus an environment check; 9 perturbations (plus the P1b variant); stated pass criteria and tolerances | `sbgv8/ers.py:13, 41-50`; `sbgv8/perturb.py` | Code inspection | D | §V, Table 5, Fig. 3 |
| 9 | The perturbations are post-hoc edits of recorded evidence, not interventions | `perturb.py` (deep copy; class "a") | Code inspection | D | §V-D |
| 10 | The ERS matrix detected a profile defect: the all-feature probe failed P2 on 109 of 227 records before the fix and passed 227 of 227 after it | `results/v8/linux/perturb/posthoc_matrix.md`; `b9b8a86c:results/v8_mac_perturb_profilefix2/posthoc_matrix.md` | Executed post-hoc matrix, both branches | D | §VIII-D, Table 9, abstract |
| 11 | The V7-B recorded verdict fails P6 (71) and P8 (155); recomputed V7-B fails P8 (84); the V8 trust gate passes P8 312 of 312 | `posthoc_matrix.md` (predictors `b3`, `b3_live`, `model`) | Executed post-hoc matrix | D | §VIII-D, Table 9 |
| 12 | Plain DT risk is 0.169 [0.086, 0.354] at coverage 0.709; the V7-B gate is 0.213 [0.090, 0.457] at 0.236 | `audit/stats_summary.json` → `seed0_recomputed.soft_v8.0.rules` | Recomputed from records; cluster bootstrap B = 10,000 | E (construction labels) | §VIII-A, Table 8, abstract |
| 13 | The V7-B gate's abstention did not lower risk among issued verdicts | Same as #12 | Point estimates; CIs overlap | E | §VIII-A, §IX-A |
| 14 | At c*, CEC+ERS is 0.213 vs B7 0.230: a difference of +1.6 pp [−6.6, +16.3]; H2 is not supported | `audit/STATISTICAL_AUDIT_REPORT.md` §2c | Recomputed | E | §VIII-B, abstract, conclusion |
| 15 | CEC+ERS is 4.4 pp worse than random abstention at c* | `tables/tab_ablation.tex` (B6 0.169 vs B8 0.213) | Recomputed | E | §VIII-B |
| 16 | No contrast survives Holm; the smallest Holm p is 0.68 (soft) and 1.0 (strict) | STATISTICAL_AUDIT_REPORT §2c | Recomputed | E | §VIII-B |
| 17 | The ERS log-loss gain is 0.030 [−0.014, 0.085]; H3 is not supported | STATISTICAL_AUDIT_REPORT §2c | Recomputed | E | §VIII-B |
| 18 | The placebo test puts the observed gain above the 95th percentile in 5 of 6 runs (p 0.01–0.03; 0.21 in the sixth) | `b9b8a86c:results/v8_mac_reanalysis_20261118_222059_profilefix2/ers_placebo_v8.{0,1}.json` | Mac branch, post-fix, 100 permutations, unadjusted | E | §VIII-B |
| 19 | Calibration slopes are unstable: CEC 0.30 [−0.46, 1.13]; B7 −1.83 | STATISTICAL_AUDIT_REPORT §2b, §2d | Recomputed | E | §VIII-B, Fig. 6 |
| 20 | Nested-CV thresholds at α ∈ {0.10, 0.15} issue no NDO (multiplicity-only issues 1) | `tables/tab_ablation.tex` footnote; STATISTICAL_AUDIT_REPORT §6 | Linux runs | E | §VIII-B |
| 21 | In the frozen-threshold study, the conservative rule issues nothing and the optimistic rule gives held-out R of 0.24–0.50 | STATISTICAL_AUDIT_REPORT §6 (mac branch `v8_mac_reanalysis_20261118_210512`) | Mac branch | E | §VIII-B |
| 22 | The sign of the primary contrast is unstable across 5 seeds (+1.6, +1.6, +3.3, −4.1, −4.9) | STATISTICAL_AUDIT_REPORT §2d | Saved Linux results | E | §VIII-C |
| 23 | The profile fix changes no conclusion | STATISTICAL_AUDIT_REPORT §3.5 | Mac post-fix rerun | S | §VIII-C |
| 24 | MDE is about 16.5 pp at n = 61; 460–1,160 NDO are needed for 5 pp | STATISTICAL_AUDIT_REPORT §5; `figures/fig_power_mde.pdf` | Computed (ICC 0.61, design effect 1.48) | S | §VIII-C, Fig. 7 |
| 25 | Original suite before hardening: 15 attacks (3 blocked, 9 detected, 1 no effect, 2 succeeded) | SBG-V6 `results/v8_mac_security/attack_suite_before.json`; `audit/security_outcomes.json` | Executed (macOS) | D | §VIII-E, Table 10 |
| 26 | Re-run at the final commit: 25 attacks/probes (3 blocked, 15 detected of which 5 detection-only, 5 no effect, 2 succeeded: P08, SENSE04b) | `audit/security_rerun_darwin.json` (`scripts/audit_security_rerun.py`) | Executed (macOS) | D | §VIII-E, Table 10, Fig. 8 |
| 27 | The SENSE04 fix is partial (SENSE04b succeeds) | `audit/security_rerun_darwin.json` | Executed (macOS) | D | §VIII-E |
| 28 | Linux: 51 tamper probes detected (24 distinct operations); of 74 container probes, 65 INS with unrecorded cause, 8 no effect, 1 succeeded | `results/v8/linux/expanded_security_suite_results.json`; SECURITY_THREAT_MODEL_AUDIT §2 | Executed, but without host metadata | S | §VIII-E, Table 10 |
| 29 | Linux isolation is bwrap/unshare network-only; there is no Podman, PID namespace or seccomp | `sbgv7/isolation.py:71-78, 118-125, 320` | Code inspection | D | §VI-B |
| 30 | Security position: fail-safe integrity against keyless writers; detection (not prevention) of in-process forgery and substitution; one open sensing channel | Items #25–#29 | As above | S | §VIII-E, conclusion |
| 31 | The five-dataset artifact is label-derived and excluded | `audit/DATASET_VERIFICATION_REPORT.md`; `sbgv8/independent_validation/executor.py:38-43` | Code plus replay (250 of 250) | D | §XI-B |
| 32 | No prior method combines the estimand, a change-conditioned profile with integrity signals, and a perturbation-response protocol | `audit/literature_tables.md` (gap statement) | Literature review of 70 verified sources; "in the sources we reviewed" | S | §II-G |
| 33 | ERS features improve prediction | — | CIs include 0; sign unstable | N | §VIII-B, §IX-B (stated as not established) |
| 34 | CEC reduces false-assurance risk | — | H2 not supported | N | §VIII-B |
| 35 | Results generalise beyond the dev corpus | — | — | N | §X |
| 36 | Independently adjudicated external evaluation | Protocol implemented (`sbgv8/adjudication.py`) | Not executed | F | §XI-C, §IX-D |
| 37 | Integrating the profile fix into the evaluated branch | `b9b8a86c` (other branch) | — | F | §XI-B |

## Explicitly prohibited claims, and where the paper disclaims them

| Prohibited claim | Disclaimer location |
|---|---|
| Program equivalence | §I (last paragraph), §III-B, §III-C item 1 |
| Complete detection of divergence | §I |
| Distribution-free robustness or conformal guarantee | §II-E, §IV-D |
| Causal effects from post-hoc perturbations | §V-D, §X |
| ERS superiority | §VIII-B, §IX-B, conclusion |
| Completed human adjudication | §I, §III-E, Table 6, §XI-C |
| Benchmark labels presented as independent ground truth | §III-E, §VII-C |
| Complete adversarial security, or container isolation | §VI-A, §VIII-E, Table 10 |
| Generalisation to other languages or systems | §X (external validity) |
