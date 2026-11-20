# SBG V8: architecture and formal definitions as implemented (audit)

Audited tree: `research/v8-linux-validation` @ `07ecd5b7`. File:line references point into that tree. The comparison branch is `research/v8-mac-hardening` @ `b9b8a86c`; the two branches split at `8e28f601`. Read-only audit: no repo file was modified.

Test suite (macOS 26.7 arm64, Python 3.13, `PYTHONPATH=. .venv/bin/python -m pytest tests/v8 -q -p no:cacheprovider`): **247 passed, 8 skipped, 2 xfailed** (85 s). Podman was not needed. The 8 skips are `test_ers_validation.py:116` ("no recorded evidence directory"). The 2 xfails are the profile defects that the mac branch fixes (see §1.2.1).

---

## 1. Formal definitions

### 1.1 Evidence record (`sbgv8/schema.py`)

A pair's evidence is an `EvidenceRecord` E (`schema.py:29-60`) with these parts:
- **Identity:** `pair_id`, `project`, `family`, `split`.
- **Label:** `y ∈ {1,0,None}`. Only fitting and evaluation read it. The digest at `schema.py:58-60` excludes `y` and `meta`.
- **Historical V7-B result:** `v7b_verdict`, `v7b_level`.
- **Inputs:** `inputs: list[InputEvidence]`.
- **Changed units:** `changed_units = {base:[line], variant:[line]}`.
- **Static branch counts:** `static_branches = {base:int, variant:int}`. These count branch instructions on changed lines.
- **Channels:** `declared_channels ⊆ CHANNELS = (outcome, exception, side_effect, api)` (`schema.py:11`).
- **Environment:** `env_id`, `env_consistent`.
- **Integrity:** `integrity_ok`.
- **Blockers:** `blockers`, the V7-B reason codes.
- **Config:** `config = {r_det, r_replay, k_alt, s2_branch_floor}`.
- **Meta:** `meta`, never used as a feature.

Each input is an `InputEvidence` i (`schema.py:13-27`) with these fields:
- `outcome ∈ {SAME, CONFIRMED_DIFF, QUARANTINED, NO_RUN, …}`.
- Flags `lossy`, `degenerate` and `deterministic`.
- `n_repeat_runs`: the count of repeat, replay and alt runs.
- `provenance`, a class label, and `provenance_ok`.
- `obs_fingerprint`: the first 32 hex characters of sha256 over the canonical variant primary observation (`adapter.py:27-28`).
- `channels_present` (`adapter.py:31-38`).
- `hits[side]`: executed lines.
- `branches[side][key] = directions`.
- `duplicate_of`: set only by perturbation P3.

**How the record is built from a real run.** `adapter.load_record` (`adapter.py:60-97`) reads `evidence.jsonl` (the V7-B hash chain) and the `v8_parts.json` sidecar. Hits and branches come only from a sidecar that is bound to the log and validated (`adapter.py:73`). The integrity flag is computed as:

`integrity_ok = verify() ∧ sidecar≠inconsistent ∧ validate_dir.trusted≠False` (`adapter.py:97`)

The adapter never sets `env_consistent`, `provenance` or `duplicate_of`, so on collected data:
- `env_ok ≡ 1`;
- `prov_ok ≡ 1`;
- unflagged duplicates are counted.

The tests pin the last point as an xfail.

**On-disk artefacts** (`evidence_schema.py:1-8, 19-21, 60-74`). Each evidence directory holds:
- `evidence.jsonl`: the V7-B SHA-256 hash chain, `h_k = sha(h_{k-1} ‖ canon(rec_k))`.
- `verdict.json`.
- `v8_parts.json`: schema `v8.parts.1`. Holds per-input outcome, hits and branches, plus `log_head` and `evidence_sha256`.
- `v8_capture.json`: schema `v8.capture.1`. Holds one parent-side record per spawned run: seq, 128-bit nonce, side, input_hash, status, timings, fd1/fd2 sha256, tee statistics, harness stdout sha256 and a verdict of `match`, `no_frame`, `mismatch` or `incomplete`.
- `v8_anchor.json`: schema `v8.anchor.1`, `HMAC-SHA256(K, "sbgv8.anchor.1\n" ‖ canon{schema,key_id,session,files})`, where `files` maps each of the four files above to its sha256 (`evidence_schema.py:101-109`).

Validation is exact and fails on any deviation (`evidence_schema.py:38-57`):
- missing or extra keys;
- wrong types (a bool is not accepted as an int);
- out-of-bounds sizes;
- unknown schema versions.

### 1.2 Profile φ(E) (`sbgv8/profile.py:44-75`, Linux HEAD)

Notation:
- U_c = {(side, line)} is the set of changed units (`profile.py:13-14`).
- 𝓘 = {i ∈ inputs : duplicate_of(i) = ∅} is the set of non-duplicate inputs (`profile.py:46`).
- C = {i ∈ 𝓘 : outcome = SAME ∧ deterministic ∧ ¬lossy} is the set of clean inputs (`profile.py:17-18, 47`).
- h(i) = hits(i) ∩ U_c.
- fp(i) = obs_fingerprint(i), or else `"id:"+input_id`. An input without a fingerprint is never treated as equal to another input (`profile.py:25-26`).

| Feature | Dimension (05 spec) | Computation as implemented | Line |
|---|---|---|---|
| `act_frac` (activation) | D1 | \|∪_{i∈C} h(i)\| / \|U_c\| (1.0 if U_c = ∅) | 48, 58 |
| `branch_cov_min` (branch coverage) | D1 | min_side min(1, Σ_k min(2, \|∪_{i∈C} dirs_k\|) / (2·static_side)). Equals 1 if static = 0. **Approximation:** all recorded branch keys are counted, not only the static ones | 29-41, 59 |
| `mu_min`, `mu_mean` (multiplicity) | D1 | μ_u = \|{fp(i) : i∈C, u∈h(i)}\|. These are the min and mean over u∈U_c (0 if U_c = ∅) | 49-50, 60-61 |
| `n_same` | D1/D5 | \|C\| | 62 |
| `n_rep` (repetition) | D4 | Σ_{i∈C} n_repeat_runs(i) | 63 |
| `obs_react` (observable-influence **proxy**) | D2 | \|∪{h(i) : i∈C, ¬degenerate(i), channels_present(i)≠∅}\| / \|U_c\|. This is **not** the dynamic dependence or slicing that 05 specifies | 51-53, 64 |
| `n_eff` (effective diversity) | D5 | \|{fp(i) : i∈C}\| | 65 |
| `n_eff_prov` | D5/D6 | \|{(fp(i), provenance(i)) : i∈C, provenance≠label_derived, provenance_ok}\| | 53, 66 |
| `repro_frac` (reproducibility) | D4 | \|{i∈𝓘 : deterministic}\| / \|𝓘\| | 67 |
| `lossy_frac` (observation loss) | D3 | \|{i∈𝓘 : lossy ∨ degenerate}\| / \|𝓘\| | 68 |
| `chan_complete` (channel completeness) | D3 | mean_{i∈𝓘} \|declared ∩ channels_present(i)\| / \|declared\| | 55-56, 69 |
| `prov_ok` (provenance) | D6 | 1 iff ∀ i∈**inputs** (duplicates included): provenance_ok ∧ provenance≠label_derived | 70 |
| `integrity_ok` | D8 | 1[rec.integrity_ok] | 71 |
| `env_ok` (environment consistency) | D7 | 1[rec.env_consistent] | 72 |

Count features (`mu_*`, `n_same`, `n_rep`, `n_eff`, `n_eff_prov`) enter the model as log1p (`calibrate.py:17, 57-60`).

#### 1.2.1 Branch difference in `profile.py`: the mac fix is missing from the Linux branch

`b9b8a86c:sbgv8/profile.py` replaces 𝓘 with `_classes(_relevant(rec, units), units)`. That expression keeps only inputs that hit at least one changed unit, and it collapses unflagged copies with identical (fp, hit set, outcome, flags, provenance, channels) into one class whose n_repeat_runs is the maximum over the copies.

The Linux HEAD lacks this fix. As a result, irrelevant inputs (P2) and unflagged duplicates raise `n_same`, `n_eff`, `n_eff_prov` and `n_rep`. Two tests in the Linux branch are xfail for this reason (`test_ers_validation.py::test_unflagged_duplicates_do_not_raise_confidence` and `::test_all_feature_model_irrelevant_evidence_cannot_improve_risk`). In `results/v8/linux/perturb/posthoc_per_record.jsonl`, `probe_all_features` fails P2 on 109 of 227 records. The Linux `PERTURBATION_VALIDATION_REPORT.md` omits that predictor's column.

Other mac-vs-Linux code differences:
- The mac branch has no `A07c` attack.
- The mac branch has no bwrap/unshare path in `sbgv7/isolation.py`.
- The mac branch has no `2edfe568` argv/`__file__` sanitisation.
- The mac branch has less defensive parsing in `trust.check`, `check_capture` and `check_sidecar`.
- The mac branch's `trust.check` fails safe on a truncated log with no EvidencePackage or Verdict. The Linux branch keeps the older try/except form.

### 1.3 Verdict decision logic

There are three decision layers, applied in this order.

1. **V7-B engine** (`sbgv7/decide.py:78-88`, and the faithful replica `profile.v7b_style_decision`, `profile.py:78-97`):
   - **DIV** if any input is CONFIRMED_DIFF with a witness.
   - Else **INSUFFICIENT** if any blocker exists (`decide.py:40-63`). Blockers include:
     - recorded `rec.blockers`;
     - the tamper flag, giving `unsafe_program`;
     - QUARANTINED, which gives `nondeterministic`;
     - no clean SAME input, which gives `no_inputs`;
     - all SAME inputs degenerate or lossy, which gives `unobservable_outcome`;
     - U_c ⊄ hit, which gives `changed_region_not_activated` or `budget_exhausted_s0`;
     - env-inconsistent, which gives `env_sensitive` (V8 replica only).
   - Else **NDO**, at level S2 if branch_cov ≥ `s2_floor` (0.80) on both sides and no SAME input is lossy, otherwise at S1.
2. **V8 trust gate** (`procsep.decide`, `procsep.py:146-149`, applied in `collect.py:42-43` and `trust.py:194`): if `validate_dir.trusted is False`, the verdict becomes INSUFFICIENT. Untrusted evidence can never yield NDO or DIV.
3. **CEC policy** (`calibrate.Model.decide`, `calibrate.py:88-95`):
   - `integrity_ok=False` → INSUFFICIENT with risk 1.0. This also overrides a witnessed DIV; it was added after the P8 finding.
   - Else `is_div` (witness or V7-B DIV) → **DIV**.
   - Else **NDO** iff `is_eligible(rec) ∧ risk(rec) ≤ τ`.
   - Otherwise **INSUFFICIENT**.

`is_eligible = ¬is_div ∧ policy.blockers_ok(rec)` (`calibrate.py:52-54`). The named policies, in `policy.py:13, 22-35`, are:
- `v8.0`, the default and **soft** policy: every recorded blocker must be in {`changed_region_not_activated`, `budget_exhausted_s0`}. Coverage stays a graded feature.
- `v8.0s`, the **strict** policy (the legacy flag `STRICT_BLOCKERS=True`): no blocker of any kind.
- `v8.1`: no recorded blocker **and** the V7-B-style recomputation gives NDO. Under v8.1, CEC can only abstain further from V7-B's NDO set.

A gap: `evaluate.py:62` computes issued NDOs as `elig ∧ ¬is_div ∧ score ≤ τ` **without** the `integrity_ok` gate of `Model.decide`. Under v8.0, `is_eligible` reads only `rec.blockers` and not `integrity_ok`. Evaluation tables could therefore count an NDO on an integrity-failed record that `decide()` would refuse.

### 1.4 CEC calibration model (`sbgv8/calibrate.py`, `sbgv8/stats.py`)

**Model family.** L2-penalised logistic regression of P(Y=1 | φ(E), eligible):
- Features are z-scored, with count features log1p-transformed.
- Sign constraints are declared in advance (`RISK_SIGN`, `calibrate.py:14-16`): every feature has sign −1 except `lossy_frac`, which has +1. ERS features have free sign. The constraints are enforced as L-BFGS-B box bounds (`calibrate.py:135-143, 157-159`).
- Features with zero variance are pinned to 0 (`calibrate.py:155, 159`).
- The objective is `Σ log(1+e^η) − yη + ½λ‖β‖²` (`calibrate.py:139`).
- If the labels are degenerate, the model falls back to a constant prior (`calibrate.py:160-164`).

**Feature sets** (`schema.py:80-88`): `cov_only`, `cov_rep`, `cov_mult`, `cov_infl`, `cov_prov`, and `full_profile` (all 15). `full_cec` = full_profile + the 9 `ers_Pj_delta` features (`schema.py:91`).

**Training.**
- Fitting uses only eligible, labelled pairs (`calibrate.py:152`).
- λ ∈ {0.3, 1, 3, 10} is chosen by inner project-grouped 3-fold OOF log loss (`calibrate.py:216-226, 205-213`).
- The model is then refit on all training records.
- Platt or isotonic recalibration exists (`calibrate.py:105-122`) but is **not called** by `evaluate.py`.

**Threshold selection.** `stats.select_threshold` (`stats.py:112-126`) works on inner-OOF risks:
- Eligible pairs are sorted by risk. Ties form one group (`stats.py:68-74`).
- For each prefix, it computes the 95% one-sided project-cluster-bootstrap upper bound on selective risk, using B multinomial project resamples (`stats.py:25-31`).
- τ_α is the score of the largest-coverage prefix whose upper bound is ≤ α. Otherwise τ = −∞, which issues nothing.

`frozen_thresholds` (`calibrate.py:239-256`) adds two rules:
- (`pt`, α): the empirical OOF risk is ≤ α with at least 5 pairs issued.
- (`cov`): the τ whose calibration coverage is closest to `target_cov`. In `evaluate.freeze`, `target_cov` is the V7-B gate coverage of the training projects (`evaluate.py:325-329`).

Frozen α values are {0.10, 0.15, 0.20} (`evaluate.py:299-300`). `crc_threshold` (conformal risk control on the joint risk J; `calibrate.py:183-202`) is labelled EXPLORATORY.

**Important default.** `fit()` has `tau=−inf` (`calibrate.py:146`), so a model built with plain `fit()` never issues NDO. The ERS matrix in `results/v8/linux/ers/ers_matrix.json` comes from `experiments/v8/run_ers_matrix.py:9`, which calls plain `fit()`. Its every "monotone" pass is therefore satisfiable by abstention.

### 1.5 ERS and the perturbations

**Response.** Δ_j = risk_f(T_j(E)) − risk_f(E) (`ers.py:53-64`). The pass predicate is `_eval` (`ers.py:41-50`) with tolerances `TOL` (`ers.py:13`):
- **Monotone** (P1, P1b, P4, P5, P7, P9): N/A if the original verdict is DIV. Otherwise pass iff Δ ≥ −tol (tol = 1e-6) **or** the perturbed verdict is INSUFFICIENT.
- **Invariance** (P2, P3): pass iff \|Δ\| ≤ 0.02 **and** the verdict is unchanged.
- **P6**: pass iff the verdict is DIV, or Δ > 0, or the verdict is INSUFFICIENT.
- **P8**: pass iff perturbed `integrity_ok == 0` **and** the verdict is INSUFFICIENT.
- An inapplicable perturbation gives `passed=None`. N/A is never a pass.

**Perturbations** (`perturb.py`). All are post-hoc edits of a deep copy of the record. They are deterministic, with an RNG seeded by (pid, seed, digest(E)) (`perturb.py:105, 209-218`). The control type is this audit's classification, derived from `_eval`.

| P | Exact operation (code) | Lines | Property tested | Expected direction | Control type |
|---|---|---|---|---|---|
| P1 | Delete every clean non-duplicate input that is the *sole* reacher of a changed unit, or sole capturer of a channel. One target is chosen at random. N/A if no target exists | 111-124 | relevant-evidence sensitivity | risk ↑ or abstain | robustness / monotone |
| P1b | Delete all clean inputs that cover the least-multiplicity covered unit, provided this does not delete all clean inputs (named variant) | 127-134 | relevant-evidence sensitivity | risk ↑ or abstain | robustness / monotone |
| P2 | Append k=2 synthetic SAME inputs. Their hits are on unchanged lines, with fresh fingerprints, `n_repeat_runs = max` over existing inputs, and all channels. N/A if no clean input exists | 137-146 | irrelevant-evidence invariance | Δ≈0, same verdict | **negative control** (invariance) |
| P3 | Append k=2 deep copies of random inputs with `duplicate_of` set | 149-155 | duplicate-evidence invariance | Δ≈0, same verdict | **negative control** (invariance) |
| P4 | Remove one random captured channel from every input. Inputs left with no channel become degenerate with fp="masked-empty", and a CONFIRMED_DIFF input left with no channel becomes SAME | 158-168 | observation-loss sensitivity | risk ↑ or abstain | robustness / monotone |
| P5 | Mark round(0.5·\|deterministic SAME\|) inputs non-deterministic and halve every `n_repeat_runs` | 171-176 | reproducibility sensitivity | risk ↑ or abstain | robustness / monotone |
| P6 | Append a synthetic CONFIRMED_DIFF witness that hits all changed units (provenance `generator:p6_independent`). N/A if the pair is already divergent | 179-183 | divergence responsiveness | verdict → DIV | **positive control** (exact outcome) |
| P7 | Set provenance=`label_derived` (default) or provenance_ok=False on 100% of inputs (frac=1.0) | 186-191 | provenance sensitivity | risk ↑ or abstain | robustness / monotone |
| P8 | Set integrity_ok=False. Variant `corrupt` also drops every second hit | 194-199 | integrity rejection | verdict → INS, integrity_ok=0 | **positive control** (exact outcome) |
| P9 | Set env_consistent=False and append "\|inconsistent" to env_id | 202-204 | environment sensitivity | risk ↑ or abstain | robustness / monotone |

Evidence class (`perturb.py:73-80`): every row above is class (a), a recorded-evidence transformation. Real-execution analogues exist only for P2 and P5 (class b) and P6 (class c), in `experiments/v8/run_real_exec_perturbations.py`. They are not part of `perturb.apply`.

**"8 ERS properties" vs 9 perturbations.** Three numberings of the properties exist:

| Source | Property numbering |
|---|---|
| Design `05 §3` | P1 irrelevant invariance, P2 duplicate invariance, P3 relevant sensitivity, P4 observation loss, P5 divergence responsiveness, P6 provenance, P7 *calibration validity* (empirical; not a perturbation) |
| Code (`ers.py`, `V8_ERS_SPECIFICATION.md`) | nine properties keyed by perturbation id P1–P9 |
| Linux `ERS_VALIDATION_REPORT.md` | 8 properties: Prop1=P2, Prop2=P3, Prop3=P1/P1b, Prop4=P4, Prop5=P6, Prop6=P7, Prop7=P8, Prop8=P5 |

The Linux 8-property list does not map **P9 (environment)**. The paper must fix one mapping. `figures/fig_perturbation_taxonomy.pdf` uses the Linux 8-property numbering and shows P9 as an extra code-level property.

### 1.6 Spec-vs-code disagreements (summary)

| # | Spec / report says | Code does | Source |
|---|---|---|---|
| 1 | φ has k ≤ 8 dimensions; the tier-1 model has ≤ 5 predictors (04 §4, 05 §4) | 15 features; `full_profile` uses all 15. The fitted dev model keeps only `mu_min` (per the mac ERS addendum) | `schema.py:63-79` |
| 2 | D2: observable influence via dynamic dependence or backward slice (05 §1) | Reachability proxy (`obs_react`) | `profile.py:51-53` |
| 3 | T_irr, T_bud, T_aug are real execution interventions (05 §2) | Post-hoc synthetic records; real execution only in a separate experiment script (30 dev pairs) | `perturb.py:137-183` |
| 4 | Recalibration: isotonic or Platt on a separate fold (05 §4) | Implemented but not called in `evaluate.py` | `calibrate.py:105-122` |
| 5 | Branch coverage is over static branch keys | All recorded keys, capped at 2·static | `profile.py:30-31` |
| 6 | Linux ERS report: P7 "corrupt harness/config provenance", P8 "break hash chain", P5 "r_det 1→5 narrows uncertainty intervals" | P7 sets provenance labels/flags; P8 sets a boolean flag; P5 flips determinism flags and halves counts | `perturb.py:186-199, 171-176` |
| 7 | Linux ERS report: "8 properties verified at 100%" | The ERS matrix model has τ=−∞, so it always abstains; monotone passes hold by abstention. Per the per-record file, `model`'s P2/P3/P4/P6/P7/P8/P9 deltas are exactly 0. The `probe_all_features` predictor fails P2 109/227 | `run_ers_matrix.py:9`, `calibrate.py:146`, `posthoc_per_record.jsonl` |
| 8 | Linux remediation report: harness sanitises `sys.argv = [a["src"]]` | Post-fix code sets `sys.argv = ["target_program.py"]` and `mod.__file__="target_program.py"`. Before the fix, the harness had `sys.argv=[SRC]` | `sbgv7/harness.py:12, 192` |
| 9 | Linux reports: PID namespace (`--unshare-pid`), nproc limit, seccomp, Podman `--read-only`, `--network=none`, pids_limit=64 | bwrap: `--unshare-net --ro-bind / / --bind WORKDIR --dev /dev --proc /proc` only. No `--unshare-pid` and no seccomp. `rlimit_nproc` is reported UNAVAILABLE. **No code invokes podman** | `sbgv7/isolation.py:71-78, 118-125, 320` |
| 10 | `trust._isolation` reports "macOS sandbox-exec", `validated_on_linux: False` even on Linux | Stale strings | `trust.py:199-203`, `procsep.py:1` |
| 11 | Five-dataset "Podman execution" (independent-validation reports) | `executor.py` builds records from labels and dataset metadata. Outcomes are derived from `change_type` (label leak), hits are hard-coded to [1,2,3], and `env_id` is the literal string "linux_podman_cgroups_v2". No execution happens | `sbgv8/independent_validation/executor.py:20-101` |

---

## 2. Architecture

### 2.1 Pipeline (evidence → verdict)

| # | Stage | Component (code) | Input → output |
|---|---|---|---|
| 1 | Pair ingestion | `collect.compare` (`collect.py:47-54`) | (base.py, variant.py, entry, inputs, cfg). `cfg` is filled from sbgv7 defaults |
| 2 | Controller | `collect.run_capture` (`collect.py:17-44`) | Runs the **unmodified** V7-B `runner.compare_versions`. Wraps `runner.finalize` in the parent only, via `spy`, to capture parts (`collect.py:24-31`) |
| 3 | Sandboxed execution | `sbgv7.isolation.run_script/_run` (`isolation.py:111-216`) | One fresh child per run, with: <br>• own session/process group, with killpg plus ESRCH-verified cleanup; <br>• rlimits CPU, NOFILE, FSIZE, AS if active, and CORE=0 (`:118-123`); <br>• RSS watchdog and wall timeout; <br>• allow-list env with no anchor key (`:281-283`); <br>• macOS `sandbox-exec` (network denied, writes confined to the workdir) or Linux `bwrap --unshare-net --ro-bind / /`, else `unshare --net` (`:71-78`) |
| 4 | Result channel | `_child.py` → `harness.py`. Result frame `SBGV7F1 <len> <hmac>` (`isolation.py:42-68`) | Per-run 32-byte key, passed over a pipe that is closed before user code runs. A dedicated result fd carries the frame; stdout is never treated as protocol |
| 5 | Trusted evidence capture (tee) | `procsep.Supervisor._spawn` (`procsep.py:106-134`) + `_tee_child.py` | Replaces the harness spawn with a stub that tees every `sys.stdout` write to the real fd 2 as framed records `@@SBGV8T@@<nonce> seq O/W/X/C hex@@`, *before* the harness `Cap` sees it. The parent parses (`:31-59`) and compares with the harness-reported stdout (`judge`, `:65-83`). Unsupervised spawns are flagged |
| 6 | Sealing | `collect.py:38-41` | Writes `v8_parts.json` (bound to log head and sha256), `v8_capture.json` and `v8_anchor.json` (HMAC, only if a key is given) |
| 7 | Integrity checks (validator) | `evidence_schema.validate_dir` (`:197-208`). Optional isolated validator `procsep.validate_isolated` in a fresh interpreter, with an HMAC-authenticated reply (`procsep.py:156-182`) | Checks: sidecar vs Run records; capture vs log (binding, seq contiguity, nonce uniqueness, count, per-run status/side/input hash/timings/stdout digest); anchor MAC → `trusted ∈ {True, False, None}` |
| 8 | Trust report (optional) | `trust.check` (`trust.py:136-196`) | Adds `sbgv7 verify` recomputation, verdict.json, harness digest, `pinned_head`, `expected_sources` (source sha256 binding) and **shadow re-observation** (`trust.py:91-129`). The shadow is an independent minimal runner with its own canonicaliser, re-executed in the sandbox, that compares return values only |
| 9 | Record | `adapter.load_record` (`adapter.py:60-97`) | `EvidenceRecord` with `integrity_ok` |
| 10 | Profile | `profile.build_profile` | φ(E), 15 features |
| 11 | Calibration | `calibrate.fit_select` / `frozen_thresholds` | risk ∈ [0,1], τ_α |
| 12 | Verdict | `procsep.decide` → `Model.decide` | DIV / NDO / INSUFFICIENT |
| 13 | ERS | `perturb.apply` + `ers.compute_ers/run_matrix` | Δ_j, pass/fail/N/A per perturbation |

Steps 7–8 are not equally binding. Only `validate_dir` (capture, anchor and sidecar) feeds `integrity_ok` and the verdict. Shadow, `expected_sources` and `pinned_head` raise issues in `TrustReport`, but they **do not** change `effective_verdict` (`trust.py:194` uses `procsep.decide(raw_v, val)`). This audit's rerun confirms it: A01, A02, A07 and P06 are "DETECTED" while `effective_verdict` remains NO_DIVERGENCE_OBSERVED.

### 2.2 Process roles (`procsep.py:1-15`)

1. **Controller** (`collect.run_capture`): holds the anchor key and session nonce, and writes the artefacts. It never executes evaluated code.
2. **Evaluated process**: the V7-B child runs `_tee_child.py` → `harness.py` → program. It receives the harness JSON and a per-run nonce (in argv). It has no key.
3. **Evidence collector** (`Supervisor`): runs in the parent and owns fd 1/2 pipes.
4. **Evidence validator**: `validate_dir` in-process, or `validate_isolated` in a fresh interpreter with a nonce- and HMAC-authenticated reply.
5. **Decision engine** (`procsep.decide`): pure, and fails safe.

The documented limit: the tee and the harness share the evaluated program's address space. A program that replaces `sys.stdout` or `os.write`, or `dup2`s fd 2, can suppress records, which leads to `incomplete` and then untrusted. If it also reads the nonce from argv, it can forge matching records, and that is undetected.

### 2.3 Container / sandbox configuration

**As implemented** (`sbgv7/isolation.py`):

| Platform | Configuration |
|---|---|
| macOS | `sandbox-exec` profile `sbgv7/sandbox_darwin.sb`: `(deny network*)`, file writes denied outside WORKDIR |
| Linux | `/usr/bin/bwrap --unshare-net --ro-bind / / --bind WORKDIR WORKDIR --dev /dev --proc /proc`, or `unshare --net` |

On both platforms:
- rlimits: CPU = per-run cpu_s (2 s in the suites), AS = mem_mb only when the probe shows it enforced (UNAVAILABLE on this Mac), NOFILE 256, FSIZE 16 MiB, CORE 0;
- NPROC is **not applied** (`isolation.py:320`);
- RSS watchdog polls every 100 ms;
- output cap of 4 MiB per run in the runner;
- `REQUIRED` controls must all be ACTIVE for `sandbox_ok` (`isolation.py:287`).

The code has **no** PID, user or IPC namespace, no seccomp filter, no cgroup limits and no Podman invocation.

**As reported only** (`PODMAN_ISOLATION_REPORT.md`, `LINUX_ENVIRONMENT_REPORT.md`): rootless Podman 5.8.2 / crun 1.27 with:
- `netns="none"`;
- `userns="auto"`;
- `pids_limit=64`;
- ulimits cpu 5:10, as 1 GiB, nproc 32, nofile 1024;
- `--read-only`;
- a noexec tmpfs.

No containers.conf, run script, podman command line or probe output exists in the repo. Treat these claims as unverified.

### 2.4 What is hashed or MACed, and where keys live

| Object | Mechanism | Key / where |
|---|---|---|
| `evidence.jsonl` | SHA-256 hash chain plus content ids, recomputed by `sbgv7.verify` | keyless |
| result frame (child → parent) | HMAC-SHA256 per run | random 32 B per run, made in the parent and passed over a pipe that is closed before user code runs (`isolation.py:127-131`) |
| `v8_parts.json`, `v8_capture.json` | bound by `log_head` + `evidence_sha256`; capture also binds config sha256, harness sha256, stub sha256 and per-run stdout sha256 | keyless |
| tee records | 128-bit per-run nonce (in child argv) | not secret against the child |
| `v8_anchor.json` | HMAC-SHA256 over the sha256 digests of the four files + session | `SBGV8_ANCHOR_KEY` (hex, ≥ 16 B) or an argument, held by the controller and never put in the evidence dir or the child env (`evidence_schema.py:86-94`). `key_id` = HMAC(K, "sbgv8-key-id")[:16] |
| validator reply | HMAC-SHA256 (channel key, nonce, result) | random per call |
| source binding | sha256 of `expected_sources` vs the recorded ProgramVersion | supplied by the reviewer |

### 2.5 Component list for diagrams

- **Untrusted domain:**
  - base program B and variant program V;
  - `harness.py` (V7-B harness, Cap stdout capture, canonicaliser);
  - `_tee_child.py` (in-process tee stub).
- **Sandbox boundary:** per-run fresh process, process group, rlimits, network denial, write confinement (sandbox-exec or bwrap).
- **Trusted parent (controller process):**
  - V7-B runner (`compare_versions`, `finalize` spy);
  - `procsep.Supervisor` (collector: fd1/fd2 pipes, tee parser, judge);
  - result-frame HMAC check;
  - anchor key K.
- **Artefacts:** evidence.jsonl, verdict.json, v8_parts.json, v8_capture.json, v8_anchor.json.
- **Validator:** `validate_dir`, optionally `validate_isolated`.
- **Optional reviewer checks:** `trust.check`, consisting of the shadow re-observation sandbox, expected_sources and pinned_head.
- **Decision:** adapter → profile φ → calibrated logistic risk → τ_α → verdict, with the trust gate and integrity gate.
- **Audit loop:** ERS (P1–P9) around profile and decision.

The figures are `figures/fig_architecture.pdf` and `figures/fig_pipeline.pdf`, generated by `scripts/make_diagrams.py`.
