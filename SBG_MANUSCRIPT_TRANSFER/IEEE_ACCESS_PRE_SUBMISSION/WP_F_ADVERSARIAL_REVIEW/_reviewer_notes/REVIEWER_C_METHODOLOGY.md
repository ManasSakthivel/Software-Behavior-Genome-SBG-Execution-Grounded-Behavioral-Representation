# Reviewer C — Methodological validity (internal / external / construct / reproducibility)

Scope: SBG at `SBG/` HEAD `3425693`. Read-only. Paths are relative to `SBG/` unless prefixed `PKG/`.
Tags: **[VERIFIED-IN-FILE]** I opened the file; **[MY-COMPUTATION]** I recomputed from frozen population / trace-cache files (read-only, Python 3, no repo code run; V10 is already burned, so these are audit diagnostics, not new evidence for SBG); **[INFERRED]**; **[UNVERIFIED]**.
Severity: FATAL (invalidates a headline claim as worded) / MAJOR / MINOR.
I did not read `results/raw/EXP-A4C-*`.

---

## 0. Bottom line

The arithmetic is sound (A3 reproduced 522 quantities, 0 discrepancy; A2 reproduced the scored files bit-exactly on 3.13.5). The problem is what the numbers measure.

1. The headline (V10 AUROC 0.897) answers a narrow question: "on synthetic, mutation-and-rewrite pairs from one generator family, does a coarse trace difference on 11 fixed inputs predict that a pre-selected output difference on the same 11 inputs exists?" It does not support "behavioural equivalence/change detection", real-bug detection, other languages, or any practical triage claim.
2. Three issues could each become FATAL for the wording "output-free, independent, held-out":
   - (C-1) the label is the output oracle on SBG's own inputs;
   - (C-2) the "output-free" guarantee is untested against the locals-snapshot channel;
   - (C-3) V10 is held-out by program identity only. Its programs were rejected by the project's own novelty rule, and it shares generator, transformation families, oracle and author with development.
3. The paper survives only with the claim scoped to the narrow question above, a clearly labelled null/negative result (H4, real bugs, SC-6), and the version-specific caveat.

---

## 1. INTERNAL VALIDITY

### C-1 Label tautology / selected-for-observability — **MAJOR** (FATAL for any head-to-head against output-reading methods on the same inputs)
- CHANGED = return/exception/mutation/stdout differs on the protocol's 11 synthesised inputs. [VERIFIED-IN-FILE `PKG/configs/PROTOCOL.md:36`; `benchmark/scripts/generate_v10_independent.py:13-19,71-98`]
- The V10 generator accepts a CHANGED variant only if `oracle(mutant) != oracle(base)` on at least one input, and accepts an EQUIVALENT variant only if its oracle equals the base's on every input. [VERIFIED-IN-FILE `generate_v10_independent.py:136-137,154`] A3 re-confirmed 319/319 and 322/322. [VERIFIED-IN-FILE `PKG/07 §4.5`]
- Consequences:
  - (a) Any output-reading method on the same inputs scores AUROC 1.0 by definition (`PKG/03` V5, R3).
  - (b) The CHANGED class excludes by construction every mutation that is not output-visible on those inputs. The benchmark therefore cannot measure false negatives against real behavioural change, only against "output-visible-on-11-inputs" change.
  - (c) The EQUIVALENT class is "sample-equivalent" only. The oracle already removed the rewrites that broke behaviour: 32 `eq_oracle` rejections, plus SP-8 17 and SP-11 15 candidates. [VERIFIED-IN-FILE `PKG/07` T5b]
- A fair competitor needs independent inputs (labels from battery A, competitors on battery B). I saw no such design in the frozen protocol. [INFERRED]

### C-2 "Output-free" and the locals channel — **MAJOR, untested; potentially FATAL for the word "output-free"**
- The tracer records `repr(frame.f_locals)` (cap 100 chars) at every call/line/return event, including the `return` event. [VERIFIED-IN-FILE `sbg/extraction/dynamic/tracer.py:364-384`; the `arg` return value of `settrace` is ignored (`:336`)]
- The state genome consumes those snapshots as abstract values (ZERO/POSITIVE/EMPTY/…). "SAFEGUARD-2" forbids reading return values, but not locals. [VERIFIED-IN-FILE `sbg/v5/state_transition_genome.py:29-30,93-140`]
- When the result is held in a local and returned by name, the output is in the trace. In the corpus, 62 of 121 `fresh_programs` have a 4-space-indented `return <bare_name>` (crude regex). They include 10 of the 19 V10 programs: `sort_pancake`, `sort_gnome_sort`, `sort_stooge_sort`, `sort_tree_sort`, `sort_gravity_bead`, `sort_radix_sort_lsd`, `sort_bitonic_sort`, `graph_topological_kahn`, `ds_min_heap_array`, `str_group_anagrams`. [MY-COMPUTATION via grep]
- Consistent with this hypothesis, though not a test of it:
  - The state component alone beats the composite on V10 (0.917 vs 0.897, ΔCI [+0.007,+0.039], p .002). [VERIFIED-IN-FILE `PKG/07 §4.2`]
  - The state genome is the part that ingests values.
- Mitigating: SC-6 (return-expression mutation) is invisible (§6), so the leak is not total. It covers any mutation that perturbs an intermediate that is still in scope at return. The V10 selection rule (output must differ) favours exactly those mutations. [INFERRED]
- Prior precedent: the earlier "published" protocol traced the self-test driver and its `AssertionError`s, which the project itself called an output comparison that "invalidates the output-free claim". [VERIFIED-IN-FILE `experiments/final/protocol.py:17-25`] A second leakage channel should therefore be expected, not assumed absent.
- The required test (A5E) has not been run. I would not accept "output-free" in a title or abstract until it has been, for example by scrubbing locals at `return` events or replacing local values by shape-only tokens.

### C-3 V10 "independent" held-out — **MAJOR**
- All 19 programs were excluded from V8 by the repo's own novelty rule (token-Jaccard 0.101–0.146 > 0.10 vs a corpus sibling) and then repackaged as the held-out set. [VERIFIED-IN-FILE `generate_v10_independent.py:5-9`, `FREEZE_V10.json:44`]
- A3 found 16/19 above 0.10 against a V8/V9c program, max 0.225 (`math_coin_change` vs V9c-val `math_ways_to_change`). [VERIFIED-IN-FILE `PKG/07` T7b] Nearest-neighbour AST-3-gram similarity reaches 0.61 (V9c-internal max 0.69). So V10 programs are about as close to development programs as development programs are to each other at the tail. [VERIFIED-IN-FILE]
- V10 reuses `SC_TYPES`/`SP_TYPES` (SC-1..14, SP-1..12) from `generate_v8_dataset`, `compose` from `generate_v9_composed`, the same mutator and transformer, and the same oracle. [VERIFIED-IN-FILE `generate_v10_independent.py:41-44`] Only the base program differs. Transformer/mutator pairs therefore have identical inductive biases across train, dev and test. SBG's thresholds and weights were fixed on the same transformation families.
- Authorship: the corpus header says `provenance: authored / license: original` with no author or tool. [VERIFIED-IN-FILE `benchmark/corpus/fresh_programs/sort_gnome_sort.py:1-5`] All programs were added in commit `b54ea99`, whose message reads "NOT research-ready; no held-out confirmatory evaluation exists". [VERIFIED-IN-FILE `git log b54ea99`] Three commits carry Claude co-author trailers (`PKG/01 §1`), and the repo's own plan lists "disclose any LLM assistance" as a risk control (`reports/remediation/agent_e_fresh_dataset.md:441`). Who or what wrote the 121 programs is **[UNVERIFIED]**. If an LLM that also designed SBG wrote them, that is a shared-generator bias that must be disclosed.
- The README concedes "same author and generation procedure … not independently authored software" (`README.md:33-34`) [VERIFIED-IN-FILE]. The manuscript should say "held-out programs" and never "independent".

### C-4 Benchmark iteration after negative results — **MAJOR (researcher degrees of freedom)**
- On 2026-10-28 the repo's own commit says "reversed edit size still beats SBG V5 on every run; external transfer below chance". [VERIFIED-IN-FILE `git log b54ea99`] The V8 test result is SBG 0.694 vs reversed-edit 0.876 (`PKG/09 §3` #19-20).
- A composed, size-decoupled design (V9) followed on 10-29 12:18. V10 followed 38 minutes later (`8386eb5`, 12:56), frozen on 10-30. [VERIFIED-IN-FILE `git log`] Whether V9c-val scores had been opened before the V10 generator was written is **[UNVERIFIED]**. FREEZE_V9 states they had not been at freeze time.
- The V10 freeze itself discloses that forward edit AUROC 0.616 and the mean edit sizes (8.34 vs 10.27) were inspected pre-freeze. [VERIFIED-IN-FILE `FREEZE_V10.json:43`]
- The redesign is defensible (the V8 confound was real). But the reported sequence V8→V9→V10 is a forking path in which only the benchmark that favours SBG is the headline. All three must be reported, with V8-test as a negative result.

### C-5 "Frozen before scoring" is self-attested — **MINOR for scores, MAJOR for the word "pre-registered"**
- FREEZE_V10, scored pairs, evaluation and dataset share commit `c5bc130`; `written_at` is a self-reported timestamp. [VERIFIED-IN-FILE `PKG/09 §2`; `PKG/07 §4.8`]
- Leakage risk to the scores is low, because:
  - thresholds and models refit identically from V9c-train only (A3-006), and
  - weights date from 2026-08-21, before any fresh program existed.
- But the weights were introduced alongside an older corpus where AUROC was 0.551 (`PKG/07 §4.8`), so "no tuning" is not provable for that corpus. [VERIFIED-IN-FILE]

### C-6 V9c-val label defects — **MAJOR**
- 16/216 EQUIVALENT pairs differ in output (SP-8 ×10, SP-11 ×6). 67/216 CHANGED (31%) show no difference in return, exception, stdout or argument mutation on the protocol inputs. [VERIFIED-IN-FILE `PKG/07 §4.5`]
- The repo's V9c validity audit reports 0 unobservable CHANGED pairs, but is static and "executes nothing". [VERIFIED-IN-FILE `PKG/07 §7.1`] This is a statement that contradicts the dynamic evidence. A reader trusting `BENCHMARK_VALIDITY_AUDIT_V9C.json` is misled.
- The same defects sit in V9c-train (SP-8 37/83, SP-11 36/42 differ), the only place where thresholds and combiners were fitted. So the frozen thresholds and the combiner coefficients were fitted on noisy labels. [VERIFIED-IN-FILE `ZERO_SCORE_ROOT_CAUSE_V1.md:53-60`]
- The effect on AUROC is conservative (0.751→0.849 on a 266-pair clean subset), but that subset selects on outputs and is an upper bound. [VERIFIED-IN-FILE]
- V9c-val is the only second confirmatory set. With 31% unobservable positives, it is a weak confirmation.
- The frozen V5 Youden threshold is 7.955e-05, the smallest non-zero step. [VERIFIED-IN-FILE `PKG/07 §4.4`] The operating point is effectively "any trace difference at all". Precision/recall/F1 at that point are therefore a restatement of the zero-score rate.

### C-7 Pseudo-replication, clustering, power — **MINOR / MAJOR for wording**
- V10: 84 AST-identical variant groups cover 212 rows. After de-duplication AUROC is 0.884 (inside the CI). [VERIFIED-IN-FILE `PKG/07` T4]
- Program-level clustering is correct, with 19 clusters. Percentile-bootstrap bounds shift ±0.002–0.004 across seeds; the H5 raw p ranges 0.029–0.052 (seed 42 is the lowest). [VERIFIED-IN-FILE `PKG/07` T8b]
- H4 MDE ≈ 0.10 on V10. "No gain over execution statistics" is absence of evidence. [VERIFIED-IN-FILE]
- Matched-set concordance: edit 0.955 vs V5 0.931 (V10); edit 0.924 vs V5 0.806 (V9c-val). Inside a matched set the CHANGED member has the larger edit in 292/319 sets. [VERIFIED-IN-FILE `PKG/07` T10] The "size-matched" claim holds for pooled AUROC only. SBG's advantage over edit size is a between-pair effect, not a within-pair discrimination.

### C-8 AUROC depends on benchmark composition — **MAJOR (interpretation)** [MY-COMPUTATION from `PKG/configs/populations/v10_test.json`, primary rows]
- 63.6% of EQUIVALENT V10 pairs score exactly 0 (203/319). They sit in the rename/format families: SP-1 45/48, SP-2 52/53, SP-4 52/55, SP-6 49/52. SP-3 has 0/55 zeros. A pooled AUROC therefore mixes a trivial half ("renames leave the trace unchanged") with a hard half.
- Within-SP-family AUROC (CHANGED vs EQUIVALENT sharing the same rewrite), V5 / edit:

| SP family | n per class | V5 | edit |
|---|---|---|---|
| SP-1, SP-4, SP-6 | 48 / 55 / 52 | 0.980 / 0.998 / 0.998 | 0.650 / 0.962 / 0.684 |
| SP-3 | 55 | 0.964 | 0.615 |
| SP-2 | 53 | **0.836** | **0.875** |
| SP-5 | 34 | 0.774 | 0.727 |
| **SP-8 (extract-method)** | 18 | **0.611** | 0.606 |
| SP-11 | 3 | 1.000 | 1.000 |
| easy {1,2,4,6} / hard {3,5,8,11,12} | 208 / 111 | 0.952 / **0.836** | – / 0.582 |

- The most practically relevant behaviour-preserving edits (extract-method, container swap, restructuring) are where SBG is at 0.61–0.77 and indistinguishable from edit size on SP-8. The 0.897 is carried by rename/format-invariance, a property any normalised trace comparison has.
- This is exploratory and post hoc. I recommend the authors report a stratified table pre-emptively. Many cells are small (SP-8 n=18, SP-11 n=3).

---

## 2. EXTERNAL VALIDITY

### E-1 Synthetic vs real — **MAJOR**
- The corpus is "single-file exercises written for this benchmark … no real-world code" (`README.md:495-496`) [VERIFIED-IN-FILE]. 23 programs the protocol cannot handle are mostly class-based (`README.md:497-499`): scope selection removes the stateful programs. [VERIFIED-IN-FILE]
- The mutations are 14 mechanical operators (e.g. SC-6 `return x`→`return not x`, `mutator.py:355-377`) [VERIFIED-IN-FILE]. They are not natural bugs, and the oracle selects the observable subset.
- Evidence level per the repo's own assessment: "Demonstrated on synthetic, same-author benchmarks". [VERIFIED-IN-FILE `PRACTICAL_SIGNIFICANCE_ASSESSMENT.md:104`]

### E-2 Real bugs — **MAJOR (claim-level)**
- BugsInPy 0.497 [0.402, 0.596] requires excluding SP-2 negatives post hoc. All-pairs values: 0.410–0.416. QuixBugs 0.444 after exclusion, 0.384–0.388 on all pairs. 26/41 BugsInPy and about 32/39 QuixBugs real-bug pairs score exactly 0. [VERIFIED-IN-FILE `REAL_BUG_GENERALISATION_AUDIT.md:12-20,75`]
- Internal inconsistency: the audit gives "31/40 QuixBugs" (line 44) and "32/39" (line 75). [VERIFIED-IN-FILE] **MINOR**.
- The negatives are synthetic SP rewrites of the fixed program, not independent real version pairs, so "real" applies to the positives only.
- The audit's root cause ("fixed protocol inputs do not expose the bug") is incomplete. A "declared inputs" regime (bug-exposing test inputs) was run and committed (`artifacts/final/pairs_quixbugs_declared_output_free_v7.jsonl`) but the audit treats the input mismatch as the cause and does not report the declared-regime result. [MY-COMPUTATION]
  - Declared regime: 152 rows, 99 evaluated, 24 real-bug pairs evaluated of 40.
  - Excluded real-bug pairs: 9 ineligible, 5 non-terminating, 2 harness error. Non-termination is itself an observable difference, so these exclusions are not neutral and must be reported with the AUROC.
  - All 24 evaluated bug pairs have output differences, yet **8/24 score exactly 0** (e.g. `get_factors` 10/11 inputs differ, `flatten` 6/7 differ).
  - Pooled (not cluster-bootstrapped) AUROC 0.70 on those 24 positives vs 75 negatives.
  - Conclusion: even with bug-exposing inputs a third of the bugs are trace-invisible. That is the SC-6 architecture limit, not an input problem.
- The audit recommends no new real-bug experiment, citing protocol-change risk. That is acceptable for the pre-registered run, but the declared-regime numbers should be disclosed, not left in a jsonl.

### E-3 Languages — **MAJOR if any generality is claimed**
- The tracer is `sys.settrace` Python-only (`README.md:503`). The Java and COBOL attempts are unusable or unverified (`README.md:39-40,500-502`). [VERIFIED-IN-FILE]
- `docs/research/NOVELTY_ANALYSIS.md` "language-agnostic" is unsupported (`PKG/03 §E.1`). Remove it.

---

## 3. GENERALISATION (summary)
- Across programs: some support, 19 programs, same family. Leave-one-program-out V5 range 0.892–0.906 [VERIFIED-IN-FILE `PKG/07 §4.2`]. Per-program AUROC is lower for some programs, e.g. 0.745 for `sort_radix_sort_lsd` (`V10_INDEPENDENT_EVALUATION.json:622-626`). [VERIFIED-IN-FILE]
- Across transformation families: none. The test uses the development families (C-3).
- Across authors / code styles: none. The V10 set is a single-author synthetic corpus.
- Across interpreters: negative (§5).
- Across input batteries: none. A single fixed battery per type annotation. The 23 programs the protocol cannot parameterise are out of scope.
- Across tasks: real bugs at chance (E-2).

---

## 4. PRACTICAL SIGNIFICANCE — **MAJOR**
- No real-version pairs, no developer evaluation. 50% prevalence by construction. The repo's own text refuses precision claims and cost claims. [VERIFIED-IN-FILE `PRACTICAL_SIGNIFICANCE_ASSESSMENT.md:44-48,100-110`]
- The decisive baseline is missing: **output differential testing on the same inputs** was "not run as a baseline" (`:33-35`). That is the cheapest and most obvious practitioner tool. It catches SC-6, which SBG misses. By C-1 it would score 1.0 on this benchmark. The honest statement is that on a benchmark whose labels are defined by output differences, SBG without outputs cannot beat the obvious baseline, and its only value would be on inputs where output comparison is unavailable (e.g. no oracle, non-deterministic output). That scenario is not evaluated.
- Triage numbers: at the frozen threshold the reviewer inspects 417 pairs to find 301/319 changes (FP rate 0.364). Review fraction for 80% recall 0.447 vs 0.555 for the M_EX baseline. [VERIFIED-IN-FILE `PRACTICAL_SIGNIFICANCE_ASSESSMENT.md:57,85-87`] On V10 the M_EX gap is dataset-dependent (CI includes 0 for H4).
- Input synthesis: a fixed battery keyed on parameter type annotations (`protocol.py:54-94`). It requires typed signatures, the supported families (list/str/int/float/bool/dict), and a structurally chosen single entry function. Real code with unannotated or domain-typed parameters is out of scope. [VERIFIED-IN-FILE]
- Cost: the V10 recompute took 89 s with 2 workers for 660 tiny programs (`PKG/logs/registry/A2_repo.jsonl`, EXP-A2-007) [VERIFIED-IN-FILE], so toy programs are cheap. One V9c-val program takes 74 s. The 5 repeated runs are redundant for deterministic code (event digests identical in 663/663 files, `PKG/09 §4.2`), so cost is 5× what the information needs. The runner has per-trace 1 s and program 60 s budgets, no memory cap. No cost study on real-size code exists. [VERIFIED-IN-FILE / INFERRED]
- Practitioner workflow supported by evidence: none beyond "rank synthetic refactoring variants". The repo's own proposed workflow (`:112-121`) says "run a cheap output comparison in parallel", which concedes the value question.

---

## 5. REPRODUCIBILITY

| # | Finding | Sev. | Evidence |
|---|---|---|---|
| R-1 | Bit-identical only on CPython 3.13.x. On 3.9.6: V10 299/613 evaluated pairs differ, 3,837/93,942 cross-label orderings flip (4.1%), pooled AUROC 0.8947→0.9226. V9c-val 0.7530→0.7815. 3.11/3.14 differ on a 4-program subset. | **MAJOR** | [VERIFIED-IN-FILE `PKG/09 §6`] |
| R-2 | The version swing (≈ +0.03 AUROC) is larger than the H5 effect (+0.0029) and about half the H4 CI half-width. Results are a property of an interpreter implementation detail, not only of the representation. Cause not isolated. | **MAJOR** | [INFERRED] from R-1; [UNVERIFIED] mechanism (likely line-event / repr / frame details) |
| R-3 | The headline path is undocumented: README, `REPRODUCTION.md` and Makefile never mention `evaluate_v10`/`score_v6_experimental`/`FREEZE_V10`. | MAJOR | [VERIFIED-IN-FILE `PKG/09 §9.1`] |
| R-4 | `FREEZE_V10.variants_tree_sha256` cannot be reproduced; 25 per-file pins and byte-identical regeneration cover the same files. | MINOR | [VERIFIED-IN-FILE `PKG/09 §1.2`] |
| R-5 | "7 vs 10 checks": `consistency_check.py` has 10 (C1–C10), all pass. Fixed in `9bed2f0`. One stale file (`FINAL_PREMANUSCRIPT_RELEASE_CHECK.md`) contradicts itself. Do not cite "7". | MINOR | [VERIFIED-IN-FILE `PKG/01 §7`] |
| R-6 | "35/35 trace checks" is mostly string/hard-coded checks. Citing it as trace verification is misleading. The real verification is A2's 644/644 + 436/436 recompute. | MINOR (MAJOR if cited as evidence) | [VERIFIED-IN-FILE `PKG/09 §8.2`] |
| R-7 | 10 reporting scripts and `sbg/v2/execution/runner.py` (headline path) are not hash-pinned; `external_bugsinpy.py` and `external_quixbugs.py` are among them. | MINOR | [VERIFIED-IN-FILE `PKG/09 §3`] |
| R-8 | GPL-3.0 (ansible, 18 units) copied verbatim into an MIT repo (`external/bugsinpy/manifest.json:120,313…1061`). | MINOR (licence) | [VERIFIED-IN-FILE] |
| R-9 | ≥8 wrong/unfindable/mismatched citations in the repo's literature material: Sumner ICST 2011 non-existent, K&A DOI wrong in two bodies, Piech mischaracterised, [17], [33], [39], [24], [25], PIT venue, QuixBugs/EquiBench metadata. Not a validity threat, but a credibility threat if carried into the manuscript. | MAJOR (manuscript) | [VERIFIED-IN-FILE `PKG/03 §E.2`] |
| R-10 | `math_gray_code` (V9c-train) trace dump died rc=-9 after 1057 s; uninvestigated. The frozen scoring did handle it (it appears among truncated-trace programs, `ZERO_SCORE_ROOT_CAUSE_V1.md:37`). | MINOR | [VERIFIED-IN-FILE `HANDOFF/BLOCKED_AND_FAILED_WORK.md:5`] |
| R-11 | Plausible mechanism for R-10: a variant that removes the `n > 14` guard (`math_gray_code.py:18`) with `INT_BATTERY` value 100 (`protocol.py:65`) tries to build 2^100 items. After the 1 s deadline the tracer's daemon thread keeps running with no memory cap (`PKG/01` D6), so the process is OOM-killed. | MINOR | [INFERRED] only; check with a bounded subprocess |
| R-12 | Absolute paths in 27 tracked files; 4 untracked v8-dev files needed by `zero_score_population.py`; no guard on overwrite-capable Makefile targets. | MINOR/MAJOR | [VERIFIED-IN-FILE `PKG/01` D3, D4, D12] |
| R-13 | CI and tests are green at HEAD (807 passed, py3.13). | – | [VERIFIED-IN-FILE `PKG/01`] |

The statement "reproducible" should read: "scored files reproduce bit-exactly on CPython 3.13.5; other versions give different scores."

---

## 6. SC-6 "17/23 changed pairs invisible"

**Location of the evidence**
- `artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json:699-703`: `changed_zero_rate_by_sc_family["SC-6"] = {n: 23, sbg_v5: 0.7391, sbg_v6: 0.7391}`. 0.7391 = 17/23. [VERIFIED-IN-FILE]
- `PRACTICAL_SIGNIFICANCE_ASSESSMENT.md:85,88-89`: "18 CHANGED pairs (5.6%) score 0 (17 of them SC-6 …; SC-2: 1)". [VERIFIED-IN-FILE]
- `REPRESENTATION_CASE_STUDIES.md:154-171` (case study + the claim that all three execution statistics are also zero in 73.9% of SC-6 pairs). [VERIFIED-IN-FILE]
- `ZERO_SCORE_ROOT_CAUSE_V1.md:44` (train/dev: 23 of 27 "output differs, trace byte-identical" are SC-6). [VERIFIED-IN-FILE]

**What "invisible" means.** `sbg_v5 == 0.0` exactly, with V3, temporal and state components all exactly 0, while the oracle-verified output differs. It is not "small score" and not "tracer failed".

**Independent check on V10** [MY-COMPUTATION, `PKG/configs/populations/v10_test.json` + `PKG/results/raw/trace_cache/v10_test`, run 0 of each trace, 17 zero-scored SC-6 pairs compared with their matched EQUIVALENT partner so the SP rewrite cancels]:
- The V10 composition is as stated: SC-6 = 23 CHANGED pairs over 18 programs; 17 are zero (and 1 SC-2 pair is the only other CHANGED zero: 17+1 = 18/319).
- The `(event type, function, line)` event stream is identical for 17/17 on all inputs compared.
- Events plus locals snapshots are fully identical for 7/17. For the other 10 the raw locals differ between CHANGED variant and EQUIVALENT partner but the abstraction collapses them to zero. (Part may be address noise in reprs: `PKG/09 §4.2`.)
- The returned value differs on 3–11 of 11 inputs in every one of the 17 pairs.
- 6 of 23 SC-6 pairs are non-zero (0.02–0.46). The repo's explanation "presumably downstream control flow" is unverified pair by pair (`CASE_STUDIES:167-168`). [VERIFIED-IN-FILE]

**Is it architectural?** Yes, by protocol design, not by tracer limitation.
- The mutation changes only `return expr`→`return not expr` (`mutator.py:360-377`). The value leaves the function and is unobserved unless consumed by a traced caller. The protocol traces one entry function.
- Python's `settrace` hands the return value to the trace function (`arg` at `tracer.py:336`), and `ExecutionTrace.return_value` is even stored (`:316`). Reading it is trivial. Omission is the SAFEGUARD-2 policy choice.
- The policy is what keeps SBG non-tautological on this benchmark. If returns were read, SBG would become the label oracle (C-1). So the limitation cannot be "fixed" without removing the property that makes the benchmark non-circular. This is the central methodological tension of the paper.
- The class is not just SC-6. Anything that changes a result without changing path or abstract local state is invisible. This explains real-bug zeros (E-2: 8/24 with declared inputs).
- Severity: **MAJOR**. The README and case studies disclose it ("invisible by design"). The abstract must carry the limitation too.

---

## 7. What would make this defensible (ranked)

1. Run the locals-leakage test (C-2) and report it either way.
2. Re-title/scope the claim: "trace-level difference on fixed inputs as a proxy for output-visible change in synthetic Python transformations". No "equivalence", no "independent", no "output-free" without the test.
3. Report V8-test (negative), V9c-val (noisy labels) and V10 together with the iteration history (C-4).
4. Add a stratified-by-SP table (C-8) and the within-matched-set edit comparison (C-7).
5. Add an independent-input output-differential baseline with labels from a separate battery; state it as a ceiling.
6. State "CPython 3.13.5 only" in the abstract-level claims; report the 3.9 shift. Isolate the cause if feasible.
7. Disclose corpus/generator authorship (human/LLM) and replace "authored/original" with a provenance statement.
8. Report the declared-input QuixBugs regime next to the canonical one, with all exclusions.
9. Fix the ≥8 citations before any text is reused; drop "language-agnostic".
10. Do not cite 35/35 as verification. Cite the bit-exact recompute instead.

## 8. Not verified by me
- Who/what authored the 121 programs (no tooling or text says).
- Whether V9c-val scores were opened before V10 generation.
- The cause of the 3.9/3.11/3.14 score shifts.
- Pair-by-pair mechanism for the 6 non-zero SC-6 pairs.
- Any V8-test label audit (never done by repo or A3).
- My own computations were run on frozen population/trace-cache copies and use run 0 only. They are pooled, not cluster-bootstrapped.
