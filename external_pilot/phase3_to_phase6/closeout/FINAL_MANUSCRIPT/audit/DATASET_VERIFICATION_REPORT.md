# Five-Dataset Run: Dataset and Experimental Verification Report

Scope: the "five-dataset independent validation" in `results/v8/independent-validation/` (commit `ca7c2b2a`), checked at worktree HEAD `07ecd5b7`, branch `research/v8-linux-validation`. This audit was read-only. It changed no file in `results/`, `reports/`, `sbgv8/` or `datasets/`.

Reproduce every number below with:

```
cd /Users/manassakthivel/Desktop/SBG-V8-LINUX
/Users/manassakthivel/Desktop/SBG-V6/.venv/bin/python paper/IEEE_ACCESS_V8_FINAL/scripts/verify_five_dataset.py
# -> paper/IEEE_ACCESS_V8_FINAL/audit/five_dataset_summary.json
```

The JSON keys named in brackets below, such as `[provenance.*]`, point into `five_dataset_summary.json`.

---

## 0. Bottom line

**The five-dataset run executed no real benchmark code.** All 250 "change pairs" come from string templates written by hand in `sbgv8/independent_validation/datasets.py`. Only the project names and repo URLs are real. The commit SHAs, file paths, code, diffs and tests are fabricated. The verdicts are computed from evidence records whose outcomes the executor set directly from the benchmark label. A bug fix gets `CONFIRMED_DIFF` on its "trigger" tests, and a non-behavioural change gets `SAME` everywhere. As a result, the 200/50 verdict split matches the labels by construction. No program run, container, collector or sealing step produced it.

The numerical claims (250 pairs, 200/50, 0 INSUFFICIENT, hash) are internally consistent with the records. The descriptions of what those numbers measure are not supported. Several reported figures are also wrong; see §7.

---

## 1. What was actually executed (provenance)

Source: `sbgv8/independent_validation/{datasets,reproducibility,executor,blinded_export,analyze_and_report}.py` and `scripts/run_five_dataset_validation.py`.

| Question | Finding | Evidence |
|---|---|---|
| Were pairs taken from a benchmark checkout? | **No.** `pair_manifest.json` equals `datasets.load_all_candidate_pairs()` exactly. That function builds every pair from f-string templates. No file is read and no network or git access happens. | `[provenance.pair_manifest_equals_datasets_py_output] = true` |
| Are the commit SHAs real? | **No.** 250 of 250 `buggy_sha` values equal `sha1("<prefix>_<Project>_buggy_<i>")[:12]` (or the `_nb_b` variant), i.e. hashes of literal strings. | `[provenance.buggy_sha_equals_sha1_of_literal_string] = 250` |
| How much distinct code is there? | **12 code templates** for all 250 pairs, one per (dataset, change type, language). The naive normalisation counts 13 because the project name "Time" matches `getTimeout`. Within a project, bug_1 to bug_4 differ only by the integer in a comment. 244 distinct raw (base, variant) pairs; 6 are byte-identical duplicates (§3). | `[provenance.distinct_code_templates_by_dataset_and_change_type]`, `[provenance.distinct_raw_source_pairs] = 244` |
| What is the "patch diff"? | A 3-line stub showing the first 60 characters of base and variant. It is not a real diff. | `[provenance.patch_diff_is_truncated_60_char_stub] = 250` |
| What does the "bug fix" look like? | A single toy function per dataset. Defects4J: `if (a<0) return 0` changed to `return a*-1`. BugsInPy: `key.strip()` changed to `str(key).strip()`. Bears: `<` changed to `<=`. BugSwarm: `trim()`/`int()` coercion. Bugs.jar: leading-slash strip. | `datasets.py` |
| How are the non-behavioural candidates built? | By adding a comment or docstring (BugsInPy also turns a list comprehension into a generator) to a constant-returning function. They are behaviourally identical by construction. | `datasets.py` (`*_nb` blocks) |
| Was any Java compiled or run? | **No (0 of 180).** `reproducibility._execute_mock_or_real` returns `(None, True)` for any Java text that contains `"public class"`. | `reproducibility.py` L34-41 |
| Was any Python run? | Only inside the reproducibility gate, via in-process `exec`. Outputs are never compared base-vs-variant and never compared across repeats. The gate fails a pair only if the *base* raises on a `clean_same` test. | `reproducibility.py` L75-90 |
| Where do SBG's observations come from? | `executor.pair_to_evidence_record` sets `outcome="CONFIRMED_DIFF"` exactly when `change_type=="bug_fix" and purpose=="trigger_discriminating"`, and `"SAME"` otherwise. Hits, branches, channels, provenance, `integrity_ok=True` and `env_id="linux_podman_cgroups_v2"` are hard-coded constants. No collector, container or sandbox is invoked. | `[provenance.outcomes_equal_label_rule] = 250`; `[provenance.evidence_records_rederived_identically_without_execution] = 250` |
| Podman, Merkle sealing, HMAC anchors? | None of them appear in the execution code path. They appear only as literal text in the report generator (`analyze_and_report.py` L45, L154, L171, L219). | `grep -n -i "podman\|merkle\|hmac\|subprocess" sbgv8/independent_validation/*.py` |
| Which predictor produced the verdicts and ERS? | `sbgv8.ers.ActivationStubPredictor`. Its risk is `1 - act_frac` and its verdict comes from `v7b_style_decision`. Its own docstring says: *"For tests and CLI smoke only."* It is not the calibrated V8 model. | `executor.py` L106-110; `ers.py` |

**Sanity check (independent re-execution).** I re-ran the only executable artifacts, the 70 Python snippets, with base and variant on each listed test input. All 56 Python bug-fix snippets really do diverge: 40 BugsInPy (`AttributeError` vs value) and 16 BugSwarm (`"120"` vs `120`). All 14 Python non-behavioural snippets do not diverge `[python_snippet_reexecution]`. So the toy templates behave as their labels say. That says nothing about the real benchmark bugs they are named after.

---

## 2. Per-dataset verification

Sources: `pair_manifest.json`, `execution_results.jsonl` and `exclusions.jsonl`, via `[per_dataset.*]`.

| Dataset | Language (pairs) | Projects | Pairs | Bug fix | Non-behav. | Executed | DIV | NDO | INS | Excl. | Mean ms/pair (recorded) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Defects4J | Java 50 | 10 | 50 | 40 | 10 | 50 | 40 | 10 | 0 | 0 | 6.85 |
| BugsInPy | Python 50 | 10 | 50 | 40 | 10 | 50 | 40 | 10 | 0 | 0 | 6.82 |
| Bears | Java 50 | 10 | 50 | 40 | 10 | 50 | 40 | 10 | 0 | 0 | 6.66 |
| BugSwarm | Java 30 / Python 20 | 10 | 50 | 40 | 10 | 50 | 40 | 10 | 0 | 0 | 5.93 |
| Bugs.jar | Java 50 | 7 | 50 | 40 | 10 | 50 | 40 | 10 | 0 | 0 | 6.43 |
| **Total** | **Java 180 / Python 70** | **47** | **250** | **200** | **50** | **250** | **200** | **50** | **0** | **0** | **6.54** (sum 1.63 s) |

Project identities, from `[per_dataset.<ds>.projects]`:

- **Defects4J:** Cli, Codec, Compress, Csv, Gson, JacksonCore, Jsoup, Lang, Math, Time (4 bug + 1 NB each).
- **BugsInPy:** fastapi, flask, cookiecutter, tornado, sanic, rich, click, pysnooper, pytest, requests (4 + 1 each). To my knowledge, flask, rich, click, pytest and requests are not among the 17 projects in the published BugsInPy benchmark. Even the labels are therefore not BugsInPy provenance for those 5 projects; check this against the BugsInPy project list.
- **Bears:** Traccar, Dubbo, GraphQLJava, ElasticJob, Checkstyle, Spoon, OpenHtmlToPdf, Infinispan, SpringDataCommons, Fastjson (4 + 1 each).
- **BugSwarm:** Dropwizard, HubSpot, Orbit, RestAssured, SquareWire, ClosureTemplates (Java); ScikitLearn, FlaskAdmin, PyPDF, PyJWT (Python) (4 + 1 each).
- **Bugs.jar:** Camel, Flink, Wicket (6 + 2), JackrabbitOak, Log4j2 (6 + 1), Maven, Accumulo (5 + 1).

**Reproducibility.** No per-pair reproducibility record is persisted. The only machine-readable trace is the empty `exclusions.jsonl` (0 lines). "250/250 reproducible" therefore rests only on the gate code, which cannot fail a Java pair and does not test determinism (§1). `[totals.reproducibility_records_in_results] = 0`

**Runtime.** `duration_ms` measures in-process Python time to build the evidence record, build the profile and run 9 ERS perturbations with the stub. It is not program execution time.

---

## 3. Duplicates, overlap and development exposure

| Check | Result | Source |
|---|---|---|
| Duplicate `pair_id` | 0 | `[identifiers.duplicate_pair_ids]` |
| ID agreement across pair, execution and ERS files | 250 = 250 = 250, identical sets | `[identifiers.*]` |
| Byte-identical (base, variant) source pairs | 6 redundant pairs: 4 BugSwarm Python NB (scikitlearn, flaskadmin, pypdf, pyjwt) are one item; Bugs.jar camel/flink/wicket `non_behav_1` = `non_behav_2` | `[provenance.distinct_raw_source_pairs]` = 244 |
| Template-level duplication | All 40 bug fixes in a dataset share one template (per language) | `[provenance.distinct_code_templates_by_dataset_and_change_type]` |
| Cross-dataset project-name overlap | 0 | `[overlap.cross_dataset_project_names]` |
| Dev data | `datasets/v8/DEV_MANIFEST.jsonl` has 321 rows; `dev_records.jsonl` has 312 rows; 114 distinct projects; families: synthetic 150, quixbugs 116, bugsinpy 55 | `[overlap.*]` |
| Name overlap with dev projects | 0 | `[overlap.dev_project_name_overlap_total]` |

On exposure: name-disjointness holds, but it means little. The evaluation code was written by the same author, in the same commit as the code that scores it (`ca7c2b2a`). The real exposure is that the generator, the label, the observation and the verdict are all one piece of code. I could not reconcile the brief's "101 dev projects" with the repo; the manifests give 114.

---

## 4. Verdict-label alignment: tautological by construction

`[totals.verdict_x_label]` is `bug_fix -> DIV: 200` and `non_behavioural -> NDO: 50`, so agreement is 250/250. This holds in every dataset (40/10 each).

This is not evidence of detection ability:

1. The executor writes `CONFIRMED_DIFF` into a bug-fix record's inputs because the pair is labelled `bug_fix` (`executor.py` L39-44). `v7b_style_decision` then returns DIVERGENT for any record with a CONFIRMED_DIFF input. The label determines the verdict, and nothing is observed.
2. Non-behavioural records have only `SAME` inputs, and every input hits every changed unit (`hits=[1,2,3]`, `changed_units=[2,3]`). `act_frac` is therefore 1.0, the risk is 0, and the verdict is NDO. All 250 risk scores are exactly 0.0 `[per_dataset.*.risk_scores]`.
3. `EvidenceRecord.y` (the label) is also stored in each record. The stub does not read it, but the label already reached the evidence through the outcome assignment.

**Consequences:**

- False-assurance risk, coverage-risk curves and selective-risk numbers **cannot be estimated** from this run. There is no NDO case whose ground truth could be anything other than "no divergence". The non-behavioural candidates are comment or docstring edits of constant functions.
- Benchmark labels are **not** independent adjudication. Here they are not even benchmark labels, because the code is not benchmark code.
- **Human adjudication is pending.** `blinded_adjudication_template.csv` has 250 rows, and 0 rows have any value in `adjudicator_verdict`, `adjudicator_confidence`, `adjudicator_id` or `notes` `[adjudication.rows_with_any_decision] = 0`.
- **The blinded package leaks the label.** 130 of 250 `case_id`s contain `_bug_` or `non_behav`. 200 of 250 descriptions contain the word "fix". 56 patch stubs contain the `// Buggy` or `// Fixed` comment `[adjudication.label_leak_*]`. Adjudication of this package as-is would not be blind.

---

## 5. ERS recount and the unfixed-profile issue

### 5.1 Recount (`ers_results.jsonl`, `[ers.*]`)

Each pair has 9 perturbations (P1 to P9), so there are **250 × 9 = 2,250 trials, not 2,500**. The script asserts this. Across all trials: pass 1,010, fail 0, not applicable 1,240.

| P | Pass | Fail | N/A | Why N/A |
|---|---:|---:|---:|---|
| P1 | 10 | 0 | 240 | no sole-reacher input (240) |
| P2 | 250 | 0 | 0 | |
| P3 | 250 | 0 | 0 | |
| P4 | 50 | 0 | 200 | original already DIVERGENT |
| P5 | 50 | 0 | 200 | original already DIVERGENT |
| P6 | 50 | 0 | 200 | already DIVERGENT |
| P7 | 50 | 0 | 200 | original already DIVERGENT |
| P8 | 250 | 0 | 0 | |
| P9 | 50 | 0 | 200 | original already DIVERGENT |

Per dataset the split is identical up to scale (P1: 2 pass / 48 N/A; P2, P3, P8: 50 pass; P4 to P7 and P9: 10 pass / 40 N/A). The full table is in `[ers.per_dataset]`. Only 20 trials have a non-zero risk delta: P1 = +1.0 (10) and P5 = +1.0 (10). Every other trial has delta = 0 because the original risk is always 0.

### 5.2 Profile fix b9b8a86c

| Check | Result |
|---|---|
| `git merge-base --is-ancestor b9b8a86c research/v8-mac-hardening` | yes |
| `git merge-base --is-ancestor b9b8a86c HEAD` | **no** |
| `_relevant(` / `_classes(` in HEAD `sbgv8/profile.py` | **absent** (present on `research/v8-mac-hardening`) |
| Code path for `ers_results.jsonl` | `scripts/run_five_dataset_validation.py` → `executor.execute_sbg_v8_on_pair` → `sbgv8.ers.compute_ers` → **HEAD `sbgv8.profile.build_profile` (unfixed)** with `ActivationStubPredictor` |
| Replay with HEAD code vs recorded results | 2,250 / 2,250 identical (pass, delta, perturbed decision): the records were produced by the unfixed profile |
| Replay with the fixed profile (`git show research/v8-mac-hardening:sbgv8/profile.py`, monkey-patched into `sbgv8.ers`) | 0 / 2,250 change in pass, delta or decision |
| Perturbed-profile features under the unfixed profile | All 250 **P2** trials inflate `n_same`, `n_eff`, `n_eff_prov` and `n_rep` (e.g. flask NB: n_same 4→6, n_rep 12→18). P3 is unaffected because copies carry `duplicate_of`. Under the fixed profile no P2/P3 feature moves `[ers.profile_fix_check]`. |

**What this means:**

- The five-dataset ERS was produced with the defective profile.
- On P2, the defect is present in the data: irrelevant augmentation raises the quantity features.
- The reported 100% P2 pass is unaffected only because the stub predictor reads just `act_frac`, which is already 1.0 and cannot change.
- With the calibrated V8 model, which reads `n_eff`/`n_same`/`n_rep`, P2 outcomes could differ. That is the failure b9b8a86c was written to fix (found by P2 on 9 dev records).
- P2/P3 "invariance" here is therefore vacuous: risk is identically 0 and the predictor ignores the inflated features. It is not evidence of the invariance property.
- The ERS report's sentence "Zero risk perturbation on duplicate/irrelevant input additions" is literally true, but only for this reason.

---

## 6. Prediction-lock hash

```
shasum -a 256 results/v8/independent-validation/locked_predictions_manifest.json
# c1ee208e1da99643a59dcbc313c0f083bba61ec0bc5003aa4e53ea814e166298
jq -r .package_sha256 results/v8/independent-validation/prediction_lock_metadata.json
# c1ee208e1da99643a59dcbc313c0f083bba61ec0bc5003aa4e53ea814e166298
```

**Result:** the hashes match `[prediction_lock.match] = true`. Rebuilding the manifest from `execution_results.jsonl` with the `blinded_export.py` recipe reproduces the file byte-for-byte `[prediction_lock.manifest_rebuilt_from_execution_results_identical] = true`.

Limits of the lock:

- **Scope.** The hash covers only `locked_predictions_manifest.json`. It does not cover the pair manifest, the blinded cases, the CSV or the ERS/execution JSONL. Per-file SHA-256 values are listed in `[prediction_lock.file_sha256]`.
- **No independent anchor.** There is no external timestamp or signature. The lock, the code that produced it and the reports were committed together in `ca7c2b2a`. The hash proves the file has not changed since that commit. It does not prove the predictions came before any adjudication information.
- **The predictions are a deterministic function of the labels** (§4). Locking them adds no evidential value until real executions replace the templates.

---

## 7. Reported vs verified

| Claim (source) | Reported | Verified | Status |
|---|---|---|---|
| Datasets | 5 | 5 names | OK (names only) |
| Pairs per dataset / total | 50 / 250 | 50 / 250 | OK |
| Bug-fix / non-behavioural | 200 / 50 | 200 / 50 (labels assigned by template) | OK as counts |
| Distinct projects | 47 (10/10/10/10/7) | 47 (10/10/10/10/7) | OK |
| "Real-world change pairs", "immutable commit SHAs, patch diffs" (ACQUISITION, commit msg) | real | synthetic templates; SHAs = sha1 of literal strings; diffs are 60-char stubs | **FALSE** |
| Language split (PRELIMINARY_STATISTICAL) | Java 190 / Python 60 | **Java 180 / Python 70** | **WRONG** |
| Reproducibility (CHANGE_PAIR_REPRODUCIBILITY) | 250/250, 3 deterministic repeats | gate passes all by construction; Java never run; no repeat comparison; no records persisted | **UNSUPPORTED** |
| Verdicts | 200 DIV / 50 NDO / 0 INS | 200 / 50 / 0 | OK as counts; **tautological** |
| Verdict alignment 200/200, 50/50 (EXECUTION) | detection result | label → outcome → verdict by construction | **MISLEADING** |
| "Linux Podman runtime", "Merkle digests and HMAC anchors", "Podman 5.8.2: 0 crashes" | yes | not invoked; text hard-coded in report generator | **FALSE** |
| Mean execution time (EXECUTION) | 1.84 / 2.12 / 1.76 / 1.95 / 1.81, combined 1.90 ms | 6.85 / 6.82 / 6.66 / 5.93 / 6.43, combined 6.54 ms | **WRONG (hard-coded literals)** |
| ERS trials (ERS, SUMMARY) | 2,500; "2500 perturbation trials passed" | **2,250**; 1,010 pass, 0 fail, 1,240 N/A | **WRONG** |
| ERS per-P counts | table in ERS report | identical to recount | OK |
| ERS "8-property" / "10 perturbations" (driver) | 8 / 10 | 9 perturbation IDs evaluated (P1b not run) | inconsistent wording |
| ERS profile | (silent) | unfixed profile; P2 inflates quantity features; pass only because stub ignores them | **UNDISCLOSED DEFECT** |
| Predictor | "Frozen SBG V8 engine, policy v8.0" | `ActivationStubPredictor` ("tests and CLI smoke only") | **MISLEADING** |
| Exposure / overlap audit | 0 / 0 | 0 / 0 by project name | OK (but moot) |
| Non-behavioural "mined" (NON_BEHAVIOURAL) | mined | hand-written comment/docstring edits | **FALSE** |
| Exclusions | 0 | `exclusions.jsonl` empty | OK |
| Prediction lock hash | c1ee208e… | c1ee208e… recomputed | **MATCH** |
| Human adjudication | pending | 0/250 rows filled; package leaks labels | pending; **not blind as exported** |

---

## 8. Discrepancies (consolidated)

1. **Provenance.** No benchmark data is used. All 250 pairs are 12 templates with fabricated SHAs and paths. "Real-world", "acquired" and "mined" are inaccurate.
2. **No execution.** SBG observations are written from labels. No collector, container, Podman, Merkle or HMAC step runs. 180 Java pairs were never compiled.
3. **Tautological verdicts.** 250/250 label agreement is guaranteed by `executor.py` L39-44. Risk is 0.0 for every pair.
4. **Stub predictor** (`ActivationStubPredictor`) is used, not the calibrated V8 model.
5. **ERS trial count** is 2,250, not 2,500.
6. **ERS pass claim.** 1,240 of 2,250 trials are N/A, so "2,500 passed" is wrong twice.
7. **Unfixed ERS profile.** b9b8a86c is not in HEAD. P2 perturbed profiles show the defect. The pass rates are unaffected only because the stub cannot see the affected features.
8. **Language split** is Java 180 / Python 70, not 190 / 60.
9. **Runtimes in the execution report** are hard-coded literals that disagree with the recorded `duration_ms`.
10. **Reproducibility** is unverifiable: no records, and a gate that cannot fail a Java pair or detect nondeterminism.
11. **Duplicate items.** 6 byte-identical duplicate pairs (BugSwarm Python NB ×4; Bugs.jar NB_1 = NB_2 ×3 projects).
12. **BugsInPy project list.** It includes projects (flask, rich, click, pytest, requests) that, to my knowledge, are not in BugsInPy.
13. **Blinding broken.** Labels are visible in case IDs, descriptions and patch comments.
14. **Lock scope and timing.** The lock covers one file, has no external anchor, and was committed together with the code and reports.
15. `LINUX_FINAL_EXECUTION_REPORT.md` does not mention the five-dataset run, so it neither corroborates nor contradicts it. The commit also touched `sbgv7/decide.py` (it added `from __future__` above the module docstring, which demotes the docstring; harmless).

---

## 9. What the five-dataset run can and cannot support

**Can support:**

- A software-plumbing check: the V8 pipeline (record schema → profile → `v7b_style_decision` → ERS harness → lock/export) runs end to end on 250 hand-built records without crashing, in about 6.5 ms per record.
- Within the stub predictor, P8 (integrity tamper → INSUFFICIENT) fires on 250/250 records.
- The lock file is byte-stable since commit `ca7c2b2a`.

**Cannot support:**

- Any claim about real-world, external or independent validation on Defects4J, BugsInPy, Bears, BugSwarm or Bugs.jar.
- Any detection, sensitivity, specificity, false-assurance, coverage-risk or selective-risk figure.
- Cross-language or cross-project generalisation: 12 templates.
- Reproducibility or container-isolation claims.
- ERS invariance (P2/P3) or monotonicity (P1, P4, P5, P7, P9) claims for the V8 model. The stub is not the model, most monotone trials are N/A, and the profile defect is unfixed.
- Claims that blinded human adjudication is set up correctly, or that predictions were locked before label exposure in any meaningful sense.

**Recommendation for the manuscript.** Do not report the five-dataset run as validation. At most, describe it as a synthetic pipeline smoke test, and call it that. A real external validation needs:

- actual benchmark checkouts and the V8 collector on the real test suites;
- the calibrated model;
- the b9b8a86c profile fix merged;
- a de-labelled adjudication package;
- an externally timestamped lock.
