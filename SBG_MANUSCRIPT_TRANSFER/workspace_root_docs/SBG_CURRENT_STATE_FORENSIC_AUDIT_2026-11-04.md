# SBG — Current-State Forensic Audit and IEEE Access Readiness Assessment

**Audit date:** 2026-11-04 · **Auditor mode:** read-only · **Subject:** Software Behavior Genome (SBG)
**Working tree audited:** `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG`, branch `remediation/sbg-v4`, HEAD `93ef3f38b840fc1e2a16a478b27bc9a2fb2b2146` (2026-11-02 20:18 +0530)

## How to read this report

**Evidence labels**

| Label | Meaning |
|---|---|
| **[V-me]** | I checked this directly (git, file, code) in this audit. |
| **[V-sub]** | A subagent recomputed or checked this from raw artifacts. I reviewed the summary but did not repeat every step. |
| **[DOC]** | Taken from a repo document. The underlying evidence was not re-checked. |
| **UNVERIFIED** | No evidence either way. |

**Safety.** No repo file was edited, created or deleted. No `make` target, experiment script, `git checkout/switch/reset/clean/stash/commit/merge` or `fetch` (other than `fetch --dry-run`) was run. Scratch work is in `/Users/manassakthivel/Desktop/SBG_AUDIT_WORK/`. The test suite and the consistency check were run only on a `git archive HEAD` copy there. After the audit, `git status` in the repo still shows only the same 4 untracked files [V-me].

**Subagent reliability.** Six subagents ran. One (implementation audit) failed and was re-run as two narrower tasks. Where subagent output was internally inconsistent I say so (see §D.6 and §H.2).

---

# Section A — Executive summary

1. **No manuscript exists.** There is no `.tex`, `.bib`, `.docx`, IEEE template, abstract text or built figure or table for the V8–V10 work. The only paper-related artifact is an outline: `artifacts/paper_evidence/FINAL_MANUSCRIPT_BLUEPRINT.md`, which calls itself "not a draft paper". [V-me, V-sub]
2. **The science is in better shape than the paper.** The latest frozen evidence is internally consistent and reproducible:
   - Every V10 headline number was recomputed from the raw scored pairs with zero discrepancy (AUROC, bootstrap CIs, permutation p, Holm). [V-sub]
   - 807 tests pass and the 10-check consistency gate passes, on a clean copy of HEAD. [V-sub]
   - Freeze hashes match: 25/25 for `FREEZE_V10`, 18/18 for the V4 manifest. [V-sub]
3. **What the evidence supports** (V10, 19 programs, 638 pairs, 319 matched sets):

   | Claim | Result | Decision |
   |---|---|---|
   | H1: SBG V5 above chance | AUROC 0.897 [0.863, 0.922] | supported |
   | H2: SBG adds to edit size | +0.254 | supported |
   | H3: SBG beats forward edit size | +0.281 (edit size 0.616) | supported |
   | **H4: SBG adds to edit size + execution statistics** | **+0.006 [−0.069, +0.068], Holm p = 1.0** | **not supported** |
   | H5: V6 beats V5 | +0.003, Holm p = 0.090 | not supported |
   | H6: V6 adds to M_EX | +0.008, Holm p = 1.0 | not supported |

   H4 is also null on the earlier V9c validation split (+0.021, Holm p = 0.117).
4. **What it does not support:**
   - Incremental value beyond cheap execution statistics.
   - Real-bug detection. BugsInPy 0.497 and QuixBugs 0.444 after exclusions; 0.410 and 0.388 in the original v7 runs. All are at or below chance.
   - Independence. V10 is a withheld set from the same author and generator.
   - Cross-language generality.
   - V6 > V5.
5. **Defensible contribution.** The strongest supported contribution is an **evaluation-methodology and empirical finding**, with a modest method component:
   - An edit-size confound was diagnosed: a trivial predictor reaches AUROC 0.876 (reversed) on a transformation-family benchmark.
   - A size-aware, oracle-validated, preregistered evaluation was built.
   - A trace-derived representation was shown to carry signal beyond edit size.
   - That representation was shown to be **statistically indistinguishable from simple execution statistics** on 19 programs.

   This is an honest "negative-plus-methodology" paper. It is not a "new state-of-the-art representation" paper.
6. **Repository risks** (details in §B, §K):
   - GitHub `main` is `9be24b3`, the merge of PR #2. Its tree equals local HEAD, but the local `origin/main` ref is stale. [V-me for the ref mismatch, V-sub for the tree equality]
   - CI on GitHub is red: py3.9 legs never run, and the `fast-experiments` job fails byte-exact reproduction. [V-sub]
   - README, `VERSION_MAP.md`, `STATUS.md`, `CLAIMS_REGISTRY.yaml` and `FINAL_STANFORD_READINESS_REPORT.md` are stale or contradict current evidence.
   - A separate local clone, `/Users/manassakthivel/Desktop/SBG FINAL`, holds uncommitted, unpushed work on a different lineage.
7. **Literature is the weakest remaining pillar.** Nearest prior work (Kessel & Atkinson) is abstract-only. Differential-testing and value-spectra papers (Jin et al., Xie & Notkin, Person et al.) are metadata-only. No `.bib` exists. Several entries in `PRIOR_ART_MATRIX.md` are wrong. [V-sub]
8. **Verdict (§O): NOT READY FOR SUBMISSION.** The reason is the missing manuscript and bibliography, not the science. A complete draft is feasible today. A submission-quality version depends on literature access (§N).

---

# Section B — Repository state

## B.1 Git facts [V-me unless marked]

| Item | Finding |
|---|---|
| Audit root | `/Users/manassakthivel/Desktop/SBG-FINALREVIEW` is **not** a git repo. It contains `SBG/` (the repo), `venvs/py313`, `venvs/py39`, and empty `0_h/`, `1_h/`. |
| Repo | `/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG` |
| Current branch | `remediation/sbg-v4` |
| HEAD | `93ef3f38b840fc1e2a16a478b27bc9a2fb2b2146` — "Add FINAL_PROJECT_HANDOFF… (no new results)", 2026-11-02 20:18:51 +0530 |
| Remote | `origin` = `https://github.com/ManasSakthivel/Software-Behavior-Genome-SBG-Execution-Grounded-Behavioral-Representation` |
| Local `main` vs `origin/main` (local ref) | both `dc09fe4`. **The remote-tracking ref is stale.** |
| `git ls-remote origin` | `main` = **`9be24b3`**; `remediation/sbg-v4` = `93ef3f3`; `refs/pull/1/head` = `9a9104f`; `refs/pull/2/head` = `93ef3f3`; also `remediation/sbg-v2` (`d4d3cbd`), `remediation/sbg-v3` (`8386eb5`), `research/v6-evaluation-correction` (`9a9104f`) |
| What is `9be24b3`? | The GitHub merge commit of PR #2 "Remediation/sbg v4". Parents are `dc09fe4` and `93ef3f3`. Its tree equals `93ef3f3`'s tree. [V-sub, via GitHub web and API fetch] |
| Staged changes | none |
| Modified tracked files | none |
| Untracked files | 4, all in `artifacts/final/` (see B.3) |
| Stashes | none |
| Open PRs | 0. PR #1 (v6 correction) and PR #2 (sbg-v4) are both merged. [V-sub] |
| Commits ahead of local `main` | 27 (`git rev-list main..HEAD`) |
| Unpushed commits on the current branch | **0**. `HEAD` equals `origin/remediation/sbg-v4`. |
| Local-only branches | `independent-audit/ieee-access-2026-10` (`5d3dae9`, 1 commit ahead of `e3038e0`), `remediation/ieee-access-audit` (`e3038e0`), local `main`. These are not on GitHub. |

**Conclusion.** The repo contains no unpushed development *beyond* the 4 untracked files and two local-only audit branches. Anything described as "recent work not on GitHub" is more likely in the other clones (B.4).

## B.2 Last 30 commits (newest first) [V-me]

```
93ef3f3 Add FINAL_PROJECT_HANDOFF (no new results)
e8a0815 Literature access log: Kessel & Atkinson full text not obtainable; Danglot, EquiBench full-text reads; manuscript phases not completed
65c040d Final sprint report
0c08641 Final sprint deliverables (incremental contribution, novelty, case studies, practical significance, COBOL, blueprint); correct K&A DOI
7039568 Final sprint: exploratory analysis scripts
9bed2f0 Pre-manuscript release check
401d16e IEEE Access audit package (statistical, incremental-value, independence, real-bug, novelty, claims, reproducibility, readiness)
c5bc130 SBG V4 remediation: zero-score root cause, EQUIVALENT label defects (SP-8/SP-11), experimental V6-graded, v10 set + single frozen evaluation
8386eb5 Evidence package v3 (remediation/sbg-v3)
1b41e20 Phase 4: corrected external harness rescore
8d3d4f0 v9 VAL evaluation (single frozen run)
6dd5a0f v9 controlled evaluation: composed dataset, frozen models, FREEZE_V9 (committed BEFORE val scores opened)
d4d3cbd EOD evidence package (remediation/sbg-v2)
7958a04 v8 TEST evaluation (single frozen run)
c0f6c6d freeze amendment 2: chunked harness
465be1b freeze amendment 1
ebb8c44 freeze: FREEZE_V8.json before any v8 test scoring
496fb4f pre-test diagnostics, tau_v8 from dev only
b54ea99 evidence: paper-evidence package, v7 train + weight fit, v8 dev re-score
f15cb9a design: max_names redesign
e479519 remediation: 23-blocker register
0d0889c agent reports, handoff
625ca3f v7 generator (SP-2 fixed), edit-size analysis
410b3ae correct false preregistration chronology
5cf5211 fix(sp2)
e3038e0 remediation/ieee-access-audit
d9d6380 remediation: gate recursion, entry-point/input-aliasing fixes, tests, protocol v8 plan
dc09fe4 (old main) final SBG→BOB handoff
ad7b655 finalize SBG handoff validation
```

## B.3 The 4 untracked files [V-me, V-sub]

| File | Rows | Nature |
|---|---|---|
| `artifacts/final/pairs_v8dev_output_free_v8.jsonl` | 598 | v8 dev scored pairs (27 Oct). Includes one pair from the stale program `math_happy_number`. |
| `artifacts/final/pairs_dev_output_free_v8.jsonl` | 597 | v8 dev scored pairs (28 Oct, later copy). |
| `artifacts/final/programs_v8dev_output_free_v8.json` / `programs_dev_output_free_v8.json` | – | Matching program-level files. |

- `pairs_v8dev_output_free_v8.jsonl` is referenced by `EXPERIMENT_MANIFEST.json`, `zero_score_population.py` and `build_paper_evidence_meta.py`.
- `pairs_dev_output_free_v8.jsonl` is referenced by `DATA_VALIDATION.md`, `RESEARCH_STATUS.md` and others.
- **Effect on reproducibility:** the zero-score population row (207/593, 34.9%) is **not regenerable from a clean checkout**. No frozen headline result depends on these files. The authoritative v8 dev result is `MAIN_EVALUATION_v8devrescore_output_free_v8.json`, which is tracked. Whether the stale pair affects the zero-score analysis is UNVERIFIED.

## B.4 Branch comparison table

| Branch / clone | Tip | Relation to `remediation/sbg-v4` | On GitHub? | Content / importance |
|---|---|---|---|---|
| **`remediation/sbg-v4`** (current) | `93ef3f3` | – | Yes (and merged into `main` via PR #2) | **Most recent and authoritative.** V8 test, V9 composed, V10 withheld, evidence package V4, final-sprint analyses, literature access log. |
| `main` (local) | `dc09fe4` | 27 behind | Remote `main` = `9be24b3` (merge) | Stale. Needs a fast-forward after `git fetch`. |
| `remediation/sbg-v3` | `8386eb5` | 8 behind | Yes | Evidence package v3, V9 val. Subsumed by v4. |
| `remediation/sbg-v2` | `d4d3cbd` | 12 behind | Yes | V8 test result (NOT DEMONSTRATED). Subsumed. |
| `remediation/ieee-access-audit` | `e3038e0` | 25 behind | **No** | Early audit remediation. Subsumed. |
| `independent-audit/ieee-access-2026-10` | `5d3dae9` | 1 ahead / 25 behind | **No** | One audit report commit on an older base. A diff against v4 shows only older state. Low value. |
| `research/v6-evaluation-correction` | `9a9104f` | – | Yes (PR #1, merged) | V6 correction. Historical. |
| **Separate clone `/Users/manassakthivel/Desktop/SBG FINAL`**, branch `final-audit-remediation` | `2b8e2eb` | **Different lineage** (forked from `dc09fe4`; shares no commits with v4) | No | 14 modified and 23 untracked files. Holds a "NO-GO FOR MANUSCRIPT DRAFTING" audit set, a **v7 TEST evaluation** on the V6 benchmark (M2 0.7297 vs `exception_fraction` 0.5861, +0.1437), a QuixBugs canonical/declared analysis, a protocol-leak matched comparison (+0.1252 on 472 pairs), and new pipeline-guard tooling. [V-sub] |
| `/Users/manassakthivel/Desktop/SF Projects/SBG` | `e1b1849` | Earlier "A+ closure" era | UNVERIFIED | `paper_data/` and `HOSTILE_REVIEW_POST_CLOSURE.md`. V1–V6 era. Not diffed. |

**Which branch has the latest SBG work:** `remediation/sbg-v4`, which is also what GitHub `main` now contains.

**Effect of the "SBG FINAL" clone on the paper:**

| Area | Effect |
|---|---|
| Methodology and evaluation protocol | The V6-era v7-TEST run predates the V8–V10 redesign. The edit-size confound probably applies to it, but I did not check. |
| Results | It would be unsafe to mix those numbers with V10. They are incompatible versions. |
| Manuscript | Its "NO-GO" verdict predates V8–V10. |
| Reproducibility | It is uncommitted state that is easy to lose. Back it up, but do not merge it into the paper. |

---

# Section C — Research version map

| Version | Introduced | Problems found | Status |
|---|---|---|---|
| **V1/V2** | Initial genome, coverage and call frequencies. | 60% volume-weighted (coverage 0.30, call frequency 0.30). [DOC] | Superseded. |
| **V3** | Adds call-transition bigrams, input sensitivity, call-depth variance, path stability and exception-causality hash. 8 fixed weights summing to 1.0 (`sbg/v3/genome.py:480-482`). [V-me] | Still volume-heavy. | Embedded inside V5 at weight 0.50. |
| **V4** | Intermediate. | – | Superseded. |
| **V5** | `0.50·d_V3 + 0.25·d_temporal + 0.25·d_state` (`sbg/v5/distance_v5.py:32-34,47-80`). Temporal and state-transition genomes. | Evaluated on the original benchmark with protocol defects (below). | **Primary method in the V9/V10 evaluations. Weights are fixed and were not fitted on any split.** |
| **"Published" protocol (original test)** | Original benchmark (3,577 pairs, 60 programs assigned) with output-reading drivers. | Output-oracle leak, self-test drivers, input aliasing, SP-2 defects, wrong denominators, pair-level bootstrap. `README.md:87` still lists withdrawn "3,777 pairs / 99 programs". | **Withdrawn and superseded.** |
| **V6 corrected evaluation** (`output_free_v6`, PR #1) | Output-free entry-point selection, program-level splits (28/10/9/13). | Preregistration backdated (committed Oct 3 vs claimed Sep 28; see `docs/current/TEST_SET_CHRONOLOGY.md`). **All V6 results are exploratory.** | Historical. Stale README "headline" (SBG 0.601 vs AST 0.105). |
| **V7** (`output_free_v7`) | Class-driver tier, τ* = 0.072905 (dev only), weight fitting (M0/M1/M2). | Test split "observed, not held out". | Superseded. |
| **V8** | Structural entry policy; `max_names=1`; 100 programs (49/14/11/26). One frozen TEST run: **SBG V5 0.694 [0.659, 0.727] vs reversed edit size 0.876 → "NOT DEMONSTRATED".** | Edit-size confound (benchmark design artifact). 8 stale programs. SP-8 and SP-11 EQUIVALENT label defects. | **Result stands as a negative.** Dataset superseded. |
| **V9 / V9c** | Composed (size-decoupled) matched design: 70 programs (46/13/11), no test split. Frozen before val was opened (`6dd5a0f` → `8d3d4f0`). | – | **Confirmatory (val): H1–H3 supported, H4 not (+0.021, Holm p = 0.117).** |
| **V10** | 19 withheld programs, 644 pairs (638 evaluated). Dynamic-oracle labels. Single frozen run. | Same author and generator as development. Freeze and results committed together (§F.4). | **Headline split.** Confirmatory-by-freeze. Not independent. |
| **V6-experimental** (graded state abstraction) | Replaces the sign-based state abstraction with exact small integers, digit counts and sizes. Distance code is identical to V5. | Dev: ΔAUROC +0.0001, no gain. | **Experimental arm only.** H5 is not supported. V5 remains the primary method. |

**The word "V6" has three meanings and must not be mixed:**
1. the V6 *evaluation* correction (output-free protocol),
2. the V6 *benchmark* (2,340 pairs, 60 programs),
3. the V6 *representation* (graded state abstraction; `sbg/v6/state_transition_genome_v6.py`).

**Authoritative statement for the paper.** Representation = **V5, fixed weights**. Headline evaluation = **V10 (withheld, same author)**, with **V9c-val** as the earlier confirmatory replication. V8 test is reported as the motivating negative. V6-experimental is an exploratory arm.

**Frozen vs exploratory**

| Class | Items |
|---|---|
| Confirmatory-by-freeze | V9c-val H1–H4, V10 H1–H6, V8 test criterion (NOT DEMONSTRATED). |
| Exploratory | Everything on V6/V7 splits, post-hoc V10 supplement, LOPO refit, family concordance, case studies, practical-significance curves, real-bug rescoring. |
| Withdrawn | Original published protocol numbers, the "0.075 protocol leak" size (contested in the "SBG FINAL" clone), the 3,777-pair benchmark. |

---

# Section D — Scientific methodology

## D.1 Representation and distance (read from code) [V-me / V-sub]

- **V5 distance:** `sbg/v5/distance_v5.py:32-34` sets `V3_WEIGHT = 0.50`, `TEMPORAL_WEIGHT = 0.25`, `STATE_WEIGHT = 0.25`. Lines 47-80 do the combination. Result clamped to [0, 1].
  - On a V3 extraction failure it returns a neutral 0.5.
  - If V5 layers are unavailable it returns `d_V3` only.
  - If a temporal or state exception occurs, the component falls back to `d_V3` (line ~70).
  - These fallbacks are **silent**. Their frequency in the evaluations is UNVERIFIED.
- **V3 distance** (`sbg/v3/genome.py:441-539`), 8 fixed-weight components, each in [0, 1]:

  | Component | Weight |
  |---|---:|
  | Coverage size | 0.20 |
  | Call-transition bigrams | 0.25 |
  | Call frequency | 0.20 |
  | Exception (type Jaccard + rate) | 0.10 |
  | Call depth | 0.10 |
  | Coverage consistency | 0.05 |
  | Input sensitivity | 0.05 |
  | Exception-causality hash match | 0.05 |

- **Temporal** (`sbg/v5/temporal_genome_v5.py:475-594`): trigram L1 (0.20), entropy (0.10), exception transitions (0.10), exception recovery (0.15), causal precedence (0.15), phase (0.10), loop run-length (0.20).
- **State-transition** (`sbg/v5/state_transition_genome.py:443-486`): frequency-weighted Jaccard over abstract state transitions, `1 − Σmin/Σmax`. Values are abstracted to ZERO/POSITIVE/NEGATIVE and EMPTY/SINGLETON/MULTI.
- **Properties:** all components are symmetric and bounded, with d(g, g) = 0. It is a **pseudometric** at best. Identity of indiscernibles and the triangle inequality are not enforced or tested.
- **The README formula is correct** for V5.
- **Redundancy:**
  - V3 coverage and call frequency overlap, and bigrams partly overlap trigrams.
  - The V3 call-structure features also overlap the temporal trigrams.
  - Exact-zero scores are common when a mutation does not change the trace abstraction.
  - **Not formally ablated** on the frozen splits. The V3/temporal/state component AUROCs are descriptive only.
- **Weights:** V5's 0.50/0.25/0.25 are fixed a priori and were never tuned. The M1/M2 weight fits (`WEIGHT_FITTING.json`: fit on v7 train, chosen on dev, never on test) belong to the V6-era benchmark and are **not** part of the V5 headline.
- **Fixed weights as a limiting factor [V-sub, descriptive]:**
  - `sbg_state` alone beats V5 on V8 dev (0.799 vs 0.739), V8 test (0.751 vs 0.694), and V10 (0.917 vs 0.897).
  - So the fixed composite is not optimal on these benchmarks.
  - Per instructions I did not fit new weights. Do not present state-only as a result: it was not pre-declared.

## D.2 Protocol audit: is each fix implemented? [V-sub, code-level]

| Issue | Status | Evidence |
|---|---|---|
| Entry-point selection (output-free) | **VERIFIED in code** | `experiments/final/entry_policy.py:232-293` (V8 structural policy, rename-invariant); `tests/test_entry_policy.py:99-146`. |
| Self-test drivers and assertions in traced regions | **Verified for V8+.** V6/V7 shipped with 28 historical SP-2 driver traces, whitelisted in `consistency_check.py:274-311`. | Whitelisted pairs remain in frozen V6/V7 artifacts. |
| Output-oracle leakage (SAFEGUARD-2) | **Static audit only** (`output_oracle_leak_audit.py`, gate C6). | No runtime guard inside the tracer. UNVERIFIED beyond static scan. |
| Canonical-input aliasing | **Partly verified.** The deepcopy fix is in `protocol.py` and `extraction.py`. | **No isolated unit test.** |
| Mutation-site selection and reachability | **Reachability validated by static observability audit and oracle labels. Mutation-site choice itself is a generator-side property, not fixed.** | CHANGED labels are checked for observability. Whether sites are representative of real faults is a construct-validity limit. |
| Invalid programs (SP-2 renamed methods, SP-8/SP-11) | **SP-2 fixed** (tests exist). **SP-8 and SP-11 defects remain in V8/V9c data** (§E.5). V10 avoids them with the oracle. | `test_sp2_repair.py`, `EQUIVALENT_LABEL_AUDIT.json`. |
| Denominators | **VERIFIED** (consistency gate C3: VALID ⊆ EVALUABLE ⊆ ALL; failure ledgers). | – |
| Pair-level → program-level bootstrap | **VERIFIED.** `sbg/statistics.py:89-135`: cluster = base program, B = 2000, seed 42. | – |
| Tracer isolation, timeouts, hash seed | **VERIFIED in code and tests** (`MAX_TIMEOUTS=2`, `re.purge()` per extraction in the external rescore). | `PYTHONHASHSEED=0` for confirmatory runs. 3.9 vs 3.13 shifts the distance by up to 0.41. |
| Threshold provenance (τ from dev only) | **VERIFIED** (`tests/test_threshold_provenance.py`). | – |
| Program eligibility ("41 of 64") | **DOCUMENTED**, not asserted by a test. | `docs/current/LIMITATIONS.md:31`, `EVALUATION_PROTOCOL.md:77`. |

**The "41 of 64" figure** is a V6-era number (function-tier entry only). The V7 class-driver tier and the V8 structural policy widen eligibility, and V8 uses 100 programs. A subagent read `DRIVER_SYNTHESIS_VALIDATION.json` as 41 function-tier plus 20 class-tier programs, 61 of 64 (UNVERIFIED by me). **Use V8-era counts in the paper, not "41/64".**

**Implication.** Under output-free eligibility the evaluated population is restricted to programs whose entry function takes synthesizable argument types. The excluded programs (class-heavy, IO, unsupported signatures) are systematically different. Results must be stated as applying to **algorithmic, pure-function-style Python programs with synthesisable inputs**.

## D.3 What SBG contributes (ranked by defensibility)

| Candidate contribution | Defensible? |
|---|---|
| Evaluation methodology: edit-size confound diagnosis, composed matched pairing, oracle-validated labels, preregistered cluster-level tests | **Yes — strongest.** |
| Empirical study: trace-derived distance vs edit size vs execution statistics | **Yes — a clear positive result against edit size and a clear null against execution statistics.** |
| Benchmark construction methodology | Partly. The generator still has known label defects. V10 is small (19 programs). |
| A new representation | **Weak.** The genome combines known ideas. Novelty is bounded by the unread literature (§I). |
| A new distance function | **Weak.** Fixed-weight sum of standard L1/Jaccard terms; a pseudometric. |

## D.4 Original and corrected protocols, in short

- **Original ("published"):** trace the benchmark's own drivers on canonical inputs, output-reading, mutation families keyed to edit size, pair-level bootstrap.
- **Corrected ("output-free"):** structurally chosen entry function, synthesised inputs from a fixed type battery, no return-value reading by the scorer, static observability audit, program-level splits, cluster bootstrap and permutation.
- **V9c:** each CHANGED pair is an SC mutation composed onto an SP-transformed variant, matched to an EQUIVALENT pair of similar edit size.
- **V10:** 19 programs excluded from V8 by token-Jaccard 0.10–0.15, labels from a dynamic oracle, frozen models fit on V9c-train only.

## D.5 Self-inflicted researcher degrees of freedom (must be disclosed)

1. **V10 was designed after seeing negative V8-test and V9c-val results.** The composed design is a response to the edit-size finding. This is legitimate, but "confirmatory" means "confirmatory of a hypothesis chosen after exploratory failure".
2. `FREEZE_V10.json` states that *design-level statistics* were inspected before freezing: pair counts, per-program counts, and the edit-size distribution (forward AUROC 0.616, mean edit 8.34 vs 10.27). No SBG scores or execution statistics were seen. [V-me]
3. **The freeze, the scored file and the evaluation were committed together** in `c5bc130` (§F.4). "Before scoring" rests on a self-declared timestamp and hashes, not on git ordering. By contrast, V9 was committed in two steps (`6dd5a0f` → `8d3d4f0`). [V-me, V-sub]
4. V6's inclusion as an arm followed a rule that was met "technically" (point estimates only, CIs include 0).
5. Earlier incident: the preregistration was backdated. Documented in `TEST_SET_CHRONOLOGY.md`. The V6 results are labelled exploratory, correctly.

## D.6 Subagent inconsistency noted

Subagent D reported "21/41" exact-zero BugsInPy scores from the v7 pairs file against "26/41" in `EXTERNAL_RESCORE_V8.json`, and left the difference unexplained. I treat the harness-version explanation as plausible but **UNVERIFIED**. Both numbers are reported with their source.

---

# Section E — Dataset and benchmark

## E.1 Authoritative counts [V-sub from manifests and JSON; UNVERIFIED where noted]

| Version | Split | Programs | Pairs | CHANGED | EQUIVALENT | Notes |
|---|---|---:|---:|---:|---:|---|
| Published (original) | test | 13 | 744 | 366 | 378 | Evaluable 378; 337 `base:unsupported_signature`. |
| Published (original), whole benchmark | all | 60 assigned of 64 on disk | 3,577 | – | – | Manifest total 3,592 includes 15 cross-language pairs. README still shows withdrawn 3,777/99. |
| V6 regenerated | train / dev / val / test | 28 / 10 / 9 / 13 | 1,129 / 372 / 351 / 488 (= 2,340) | 570 / 159 / 169 / 246 | 559 / 213 / 182 / 223 | – |
| V8 | train / dev / val / test | 49 / 14 / 11 / 26 | 2,057 / 597 / 461 / 1,130 (= 4,245) | 2,406 total | 1,839 total | 8 stale programs excluded from evaluations. Non-stale test: 22 programs, 967 pairs, 956 evaluable. |
| V9c composed | train / dev / val | 46 / 13 / 11 | 1,684 / 466 / 436 (= 2,586) | 1,293 | 1,293 | Matched-complete: 1,650 / 464 / 432. No test split. |
| **V10 withheld** | test | **19** | **644 scored (641 evaluated; 638 in 319 matched sets)** | **319** | **319** | 3 non-terminating. Rejections at generation: 316 no-op equivalents, 32 oracle-differing equivalents, 14 no CHANGED match. |

- **Transformation families:** 12 SP (semantic-preserving) × 14 SC (semantic-changing) in the original; the V10 manifest logs rejection counts per family.
- **Program-level split integrity:** `benchmark/splits/leakage_audit_report.json` reports zero base-program leakage, zero near-duplicates (normalized source hash), `audit_passed: true`. The independent re-run of the near-duplicate check is **UNVERIFIED**. V10 programs share no program with any V8 or V9 split. [V-sub]
- **Obsolete datasets:** 8 programs have stale V8 variants. They were excluded by name from V8 test and all V9c splits. Whether any exploratory script consumed them is **UNVERIFIED** (see B.3).

## E.2 Label validity

| Family | Finding |
|---|---|
| SP-2 (rename) | Fixed from V7. 7 of 40 BugsInPy SP-2 negatives are still provably broken (`NameError` on `fix_kv` in `js_to_json`). QuixBugs SP-2: 0 of 40 broken. |
| **SP-8 (extract method)** | **Active defect in V8/V9c data.** 37 of 83 EQUIVALENT pairs (44.6%) in train differ in output (dev 7/23, val 10/23). `EQUIVALENT_LABEL_AUDIT.json`. |
| **SP-11 (list → deque)** | **Active defect.** 36 of 42 train EQUIVALENTs (85.7%) differ in type (dev 6/6, val 6/12). |
| Combined | About 8.7% of V8 train EQUIVALENT variants change output. |
| **V8 test** | **Not audited** (deliberately kept unread). SP-8/SP-11 label quality on V8 test is UNVERIFIED. |
| V10 | Dynamic-oracle validated (return, exception, argument mutation, stdout on protocol inputs). It contains none of the SP-8/SP-11 defects: 17 SP-8 and 15 SP-11 candidates were rejected. |

"Equivalent" here always means **equivalent on the 11 synthesised protocol inputs**, not semantically equivalent. This must be in the text.

## E.3 Edit-size confound across versions (AUROC of edit size as a predictor)

| Dataset | Direction | AUROC |
|---|---|---|
| V6/V7 train, dev | reversed (larger edit → EQUIVALENT) | 0.954 / 0.957 |
| V8 train / dev / val / **test** | reversed | 0.849 / 0.877 / 0.885 / **0.876** |
| V9c matched train | forward | 0.610 |
| **V10** | forward | **0.616** (mean edit CHANGED 10.27–10.29 vs EQUIVALENT 8.34–8.36) |

- The composed design **reverses the sign** of the confound and shrinks its magnitude from 0.88 to 0.62. It does **not** eliminate it.
- In V10, 92% of matched sets (the checklist says 91%) have the larger edit on the CHANGED side.
- Exact-size stratified AUROC for V5 is 0.875 (edit size itself 0.500). `EVALUATION_PLAN_V9.md:18` notes that equal-size strata retain only 17–23% of cross-label pairs, so stratified estimates use a non-random subset.
- **Matched-set bias:**
  - The design forces a 1:1 class balance, so the prior is removed.
  - CHANGED pairs require static observability, which restricts them to programs with observable mutations.
  - CHANGED variants are "SC on top of SP", so they are systematically larger.
- **Statement for the paper:** exact edit-size matching *reduces* confounding. It does not establish generalisation.

## E.4 Implications of 19 programs

- The program is the clustering unit. 638 pairs ≈ **19 independent units**.
- CIs reported are cluster-bootstrap CIs. H4's CI [−0.069, +0.068] leaves increments up to about ±0.07 open.
- A null here is **inconclusive, not evidence of equivalence**. The test is underpowered for increments below roughly 0.05–0.07.
- V10 programs are "algorithmic siblings" of development programs, with token-Jaccard 0.10–0.15 to a development sibling (`FREEZE_V10.json`). Same author, same generator, same SP/SC families, same input protocol.

## E.5 Untracked or alternate datasets

See B.3. No tracked headline result uses the stale variants.

---

# Section F — Statistical audit

## F.1 Implementation [V-sub; `sbg/statistics.py`]

| Method | Lines | Detail |
|---|---|---|
| AUROC | 51-83 | Tie-aware Mann-Whitney with mid-ranks. A degenerate case returns 0.5. |
| Cluster bootstrap CI | 89-135 | Resamples base programs, B = 2000, seed 42, percentile CI. Single-class resamples are discarded rather than pinned to 0.5. |
| Cluster permutation | 141-172 | One-sided, labels permuted **within** program, p = (k + 1)/(B + 1). |
| Paired Δ | 178-235 | Both predictors rescored on the same resampled clusters. Two-sided bootstrap p. |
| Holm | 283-303 | Monotone step-down. |
| Wilson | 309-324 | Detection-rate intervals. |
| Logistic models | `fit_weights.py:83-119` | Full-batch gradient descent, 5000 iterations, lr 0.5, L2 = 1.0, standardised features, **fit on V9c-train only** for V10. |
| Threshold | `evaluate_v4_dev.py:76-91` | Youden J on V9c-train, applied unchanged. |
| Exact-size stratification | `evaluate_v9.py:134-144` | Mann-Whitney concordance restricted to equal-edit-size cross-label pairs. |

## F.2 V10 recomputation [V-sub, in memory, frozen models, no refit]

Population: 644 scored → 641 evaluated → 638 matched-complete (319 sets, 319 CHANGED / 319 EQUIVALENT, 19 programs). All 21 predictors are scored on the **same** 638 pairs.

| Quantity | Reported | Recomputed | Δ |
|---|---:|---:|---:|
| SBG V5 AUROC | 0.896768 [0.862918, 0.921553] | same | 0 |
| Forward edit size | 0.616046 [0.606281, 0.627539] | same | 0 |
| M_EX (edit + execution statistics) | 0.790789 [0.717595, 0.850563] | same | 0 |
| M_EX+V5 | 0.797088 [0.668922, 0.898150] | same | 0 |
| M_E+V5 | 0.870545 [0.836119, 0.898227] | same | 0 |
| SBG V6 (experimental) | 0.899657 [0.867456, 0.923487] | same | 0 |
| sbg_state (component) | 0.917100 [0.893309, 0.937922] | same | 0 |
| coverage_size / exception_fraction / call_count | 0.779 / 0.701 / 0.692 | same | 0 |
| static AST / token | 0.591 / 0.582 | same | 0 |

**All four values you asked me to verify are verified.**

## F.3 Hypothesis decisions

| ID | Test | V10 result | Holm p | Decision | Status |
|---|---|---|---:|---|---|
| H1 | V5 AUROC > 0.5 (cluster permutation) | 0.897; raw p 0.0005 | 0.003 | **Supported** | pre-declared |
| H2 | M_E+V5 − M_E | **+0.254** [+0.218, +0.285] | 0.005 | **Supported** | pre-declared |
| H3 | V5 − forward edit | **+0.281** [+0.244, +0.308] | 0.005 | **Supported** | pre-declared |
| **H4** | **M_EX+V5 − M_EX** | **+0.0063** [−0.0690, +0.0680] | **1.000** | **Not supported** | pre-declared |
| H5 | V6 − V5 (experimental) | +0.0029 [+0.0003, +0.0060], raw p 0.030 | 0.090 | **Not supported** | pre-declared |
| H6 | M_EX+V6 − M_EX (experimental) | +0.0085 [−0.067, +0.069] | 1.000 | **Not supported** | pre-declared |

**V9c-val (n = 432 pairs, 11 programs):** V5 AUROC 0.751 [0.706, 0.794]. H1 supported (Holm 0.002), H2 +0.112 (0.003), H3 +0.140 (0.003), **H4 +0.021 [−0.005, +0.048], Holm p = 0.117, not supported.**

**Reading of H5:** the raw CI excludes zero but the pre-declared Holm family does not reject. The correct statement is "V6 is not shown to be better than V5". Do **not** say "V6 is significantly better", and do not say "no difference".

**Reading of H4:** this is a non-rejection with a wide interval. It is **not proof of equivalence**. The right wording is "no statistically established gain; increments of about 0.07 or smaller cannot be excluded".

## F.4 Pre-registration chronology [V-me]

- `FREEZE_V10.json`: `written_at 2026-10-30T12:15:42Z`, `git_head 8386eb5`, status "FROZEN BEFORE ANY v10 PAIR WAS SCORED".
- It was committed **together with** the scored pairs, `FREEZE_V10_SCORED.json` and `V10_INDEPENDENT_EVALUATION.json` in commit `c5bc130` (2026-10-30 18:02:32 +0530). That commit also contains the generator, the evaluator, and the dataset.
- `evaluate_v10.py` refuses to run unless hashes match (`:73-90`) and refuses to overwrite its output (`:43`, `:94`). That is real integrity enforcement, but it is **self-attested**.
- V9: `6dd5a0f` (freeze, 12:18:00) → `8d3d4f0` (val scores, 12:18:37). Better ordering in git, though only 37 seconds apart.
- **For the paper:** describe V10 as "frozen by hash manifest prior to scoring; freeze and results were committed in the same commit." Do not claim an independent timestamped preregistration.

## F.5 Post-hoc results (exploratory only) [V10_POSTHOC_SUPPLEMENT.json]

| Comparison | Δ | Note |
|---|---:|---|
| V5 − coverage_size | +0.118 [+0.062, +0.175] | post-hoc |
| V5 − M_X | +0.104 [+0.031, +0.183] | post-hoc |
| V5 − M_EX | +0.106 [+0.033, +0.186] | post-hoc |
| V5 − M_EX+V5 | +0.100 [−0.009, +0.235] | post-hoc |
| Edit − V5 matched concordance | +0.0235 [−0.0105, +0.0621] | post-hoc |
| LOPO refit: M_EX / M_EX+V5 / V5 | 0.885 / 0.895 / 0.897 | exploratory |

**Critical interpretation:** the frozen M_EX (0.791) was fit on V9c-train and applied to V10. It **does not transfer well**. When refit leave-one-program-out, M_EX reaches 0.885, essentially level with SBG (0.897). The post-hoc "V5 beats M_EX by 0.106" therefore reflects combiner transfer failure and must **not** be promoted to "SBG beats execution statistics". That is a trap in the manuscript.

## F.6 Other checks

- Exclusions: 3 non-terminating V10 pairs and their 3 matched partners are dropped; the denominator is 638. [V-sub]
- Missing or neutral scores: the 0.5 neutral value for failed extraction. Frequency UNVERIFIED.
- Detection-rate intervals: Wilson (regression suite, 7/15 = 0.467 [0.248, 0.699]).
- Non-terminating executions: bounded by a timeout counter (max 2).

---

# Section G — Baseline comparison

| Predictor (V10, 638 pairs, same population) | AUROC | Verdict |
|---|---:|---|
| Static AST | 0.591 | far below SBG |
| Static token | 0.582 | far below SBG |
| Forward edit size | 0.616 | far below SBG (H3) |
| Call count | 0.692 | below SBG |
| Exception fraction | 0.701 | below SBG |
| Coverage size | 0.779 | below SBG (post-hoc Δ +0.118) |
| M_X / M_EX (frozen logistic) | 0.793 / 0.791 | below SBG alone, **but combiner transfer is weak** |
| SBG V5 | **0.897** | – |
| SBG V6 (experimental) | 0.900 | not significantly better (H5) |
| sbg_state alone | 0.917 | descriptive, **not pre-declared** |
| M_E+V5 | 0.871 | – |
| M_EX+V5 | 0.797 | no gain over M_EX (H4) |
| LOPO-refit M_EX / M_EX+V5 | 0.885 / 0.895 | exploratory |

**Same-population verification.** All 21 predictors were scored on the same 638 pairs. [V-sub]

**Why SBG V5 adds no established value over execution statistics (hypothesis, not a finding):**
1. The execution statistics (coverage, exception fraction, call count) are summaries of the same trace and plausibly capture most of the separable signal. This is not established causally.
2. With 19 clusters, the CI of the increment is about ±0.07.
3. The frozen M_EX combiner is fit on one design and does not transfer, which lowers M_EX unevenly.
4. Per-program, M_EX beat V5 on 5 of 19 programs (e.g. `str_group_anagrams` −0.158, `sort_radix_sort_lsd` −0.133). [V-sub]

**How should the representation be presented?** As an **empirical measurement method and a complementary signal** whose standalone performance strongly beats size-based baselines, but which has **no demonstrated incremental value** over simple execution statistics on this benchmark. **Not** as a replacement predictor.

---

# Section H — Failure analysis

## H.1 Real-bug results [V-sub: recomputed from raw pairs]

| Corpus | Protocol | Population | AUROC | 95% CI | n (pos/neg) |
|---|---|---|---:|---|---|
| BugsInPy | v6 | VALID | 0.4057 | [0.322, 0.490] | 140 (39/101) |
| BugsInPy | **v7 (committed headline)** | VALID | **0.4099** | [0.326, 0.494] | 147 (41/106) |
| BugsInPy | v8 rescore (re.purge, structural entry) | all | 0.4159 | [0.322, 0.514] | 147 |
| BugsInPy | v8, SP-2 excluded | | **0.497** | [0.402, 0.596] | 107 (41/66) |
| QuixBugs canonical | v7 | all | **0.3877** | [0.285, 0.503]* | 152 (40/112) |
| QuixBugs canonical | v8 rescore | all | 0.3842 | [0.285, 0.490] | 151 |
| QuixBugs canonical | v8, SP-2 excluded | | **0.444** | [0.355, 0.539] | 111 (39/72) |
| QuixBugs declared inputs (24 evaluable of 40) | v7 | evaluable | 0.702 | [0.584, 0.817] | 99 (24/75) |

*The QuixBugs headline JSON itself has no CI. The CI comes from `DIAGNOSTIC_EXTERNAL.json` (exploratory status).

- The "corrected" 0.497 and 0.444 are *sensitivity analyses* on the v8-rescored, SP-2-excluded subsets. They are **not** frozen headline results. All were obtained with no freeze, and the harness was changed after seeing the original results. They are **exploratory**. The primary committed results are 0.410 and 0.388.
- **Invalid labels:** 7 of 40 BugsInPy SP-2 negatives are broken (all `youtube_dl/utils.py::js_to_json`), scoring 0.79–0.80. A benchmark defect, not a scorer defect.
- **Self-distance contamination:** 3 of 41 BugsInPy bases have nonzero self-distance (max 0.673) from process-global `re` cache. `re.purge()` moves AUROC 0.410 → 0.429. A harness artifact. QuixBugs: 1 of 40, max 0.026.
- **Exact zeros:** BugsInPy 21/41 (v7 pairs, my subagent) or 26/41 (v8 rescore file). QuixBugs 32/40. Cause: the 11 synthesised inputs frequently do not reach the faulty path, and output-free scoring cannot see return values.
- **Do the inputs trigger the bugs?** For QuixBugs, evidence says the input protocol is the main driver: with the bug's own declared inputs, AUROC is 0.702 on the 24 evaluable positives, versus 0.439 for synthesised inputs on the same programs. Selection bias from evaluability is only partly excluded.
- **Return-value blindness:** with output reading, only 4 of 41 BugsInPy positives would be detected on these inputs (15 of 101 negatives also differ). Hard-negative set: SBG 1 TP, 1 FP, 4 TN, 6 FN (n = 12). Regression set: 7/15 detected (0.467 [0.248, 0.699]); all missed bugs are value-only or below threshold.

**Classification of the real-bug result**

| Cause | Class |
|---|---|
| Broken SP-2 labels | benchmark defect |
| `re` cache self-distance | harness artifact |
| Inputs not exercising the bug | protocol limitation (Python-level input synthesis) |
| Return values not visible | **design limitation of the output-free representation** |

There is **no evidence of an implementation defect** in the scorer. The conclusion is a genuine **method/protocol limitation**: SBG as specified is not a real-bug detector.

**Do not change inputs now.** Changing the input protocol after seeing results would be post-hoc. Report the negative.

## H.2 Component-level failure classes [V-sub]

| Failure class | Affected | Root cause | By design? | Bug? | Affects headline? | Fixable today without changing the question? |
|---|---|---|---|---|---|---|
| **SC-6 value-only mutations** | V10: 73.9% (17/23) of SC-6 CHANGED score exactly 0; concordance SBG 0.50 vs M_EX 1.00 | Return value not recorded (SAFEGUARD-2) | Yes | No | Limits claims. Must appear in the abstract. | No (would require relaxing SAFEGUARD-2) |
| **SP-2** | V10 SP-2 concordance 0.830; BugsInPy 7 broken labels | Rename of the entry function; benchmark label defect in external data | Partly | Data defect | Minor | Report only |
| **SP-8** | 37/83 train equivalents wrong (44.6%) | Generator emits undefined helper | No | **Generator defect** | V8/V9c training and val quality | Cannot be corrected in frozen data; V10 filters by oracle |
| **SP-11** | 36/42 train equivalents wrong | `deque` returned | No | **Generator defect** | Same | Same |
| Exact-zero scores on CHANGED | Main benchmark: (i) unexercised 65 train + 14 dev; (ii) state abstraction collapses 40; (iii) output-only 23 + 4; (iv) other 8 | Mixed | Mostly | No scorer defect found (`ZERO_SCORE_ROOT_CAUSE_V1.md`) | Moderate | No |
| State outperforms V5 | V8 dev, test; V10 | Composite weights fixed | N/A | No | Component finding | Do not tune |
| SBG below simple statistics | 5 of 19 V10 programs | Exec statistics already track the label | – | No | Supports the H4 null | No |
| Programs excluded from the output-free population | Many (V6: 337 of 744 published-test pairs) | Unsynthesisable signatures | Yes | No | **Population restriction** | No |

**One internal inconsistency in the earlier analysis:** a subagent attributed "about 0.03–0.05 AUROC depression" to SC-6 on V8 test. I found no artifact supporting that number, so I do not cite it. UNVERIFIED.

**Zero-score rate.** A frequently quoted 37% of pairs have SBG exactly 0; much of that is correct (EQUIVALENT pairs). It is not a defect.

## H.3 COBOL and Java

- COBOL: 0 executable programs. All 85 `.cbl` files are Db2 precompiler snippets. No AUROC exists. **Must not be cited as evidence of generality.**
- Java: `external_java.py` exists but no committed result artifact was found. No Java AUROC can be cited. (Cross-language claims: none.)

---

# Section I — Literature and novelty

## I.1 Verified facts [V-sub, Crossref/arXiv]

- **Kessel & Atkinson**, "On the Efficacy of Dynamic Behavior Comparison for Judging Functional Equivalence", SCAM 2019, pp. 193–203, DOI `10.1109/SCAM.2019.00030`. The repo's DOI correction is **correct** (the old `…00019` DOI is Harrand et al., a decompiler paper). **Full text was not obtained** (`LITERATURE_ACCESS_LOG_2026-10-30.md`). Only the abstract was read. The stale wrong DOI still appears in the bodies of `RELATED_WORK_NOVELTY_AUDIT.md:52` and `NOVELTY_CLAIM_TO_EVIDENCE.md:54`.
- **Danglot et al.**, EMSE 25(4), 2020, DOI `10.1007/s10664-019-09794-7`, arXiv:1902.08482. Metadata verified (arXiv). Sections read in the extracted PDF per the access log. The "ABS+INTRO" tag in the comparison table is stale.
- **EquiBench** (Wei et al.), arXiv:2502.12466, title "Reasoning about Program Semantics via Equivalence Checking". 11 authors. **The repo's earlier claims of a "NeurIPS 2025 Workshop" venue and 5 authors are wrong.** Partial full text.
- **TRACED** (Ding et al.), ICSE 2024, DOI `10.1145/3597503.3608140`. Metadata and ACM abstract only.
- **Krinke & Ragkhitwetsagul**, arXiv:2505.04311; **Yu et al.** TOSEM 2022, `10.1145/3502852`. Abstract/metadata only.
- Evans & Savoia (ESEC/FSE 2007 companion), Jin–Orso–Xie (ICST 2010), Person et al. (FSE 2008), Jiang & Su (ISSTA 2009), Just et al. (FSE 2014), Ojdanić et al. (TOSEM 2023): metadata verified, **not read**.
- **QuixBugs authors/venue in the repo are wrong**: Crossref `10.1145/3135932.3135941` is Lin, Koppel, Chen, Solar-Lezama (SPLASH Companion 2017).
- **Not found:** the "Sumner et al., Comparative analysis of software behavioral traces, ICST 2011" entry. The repo's description of it as "the most direct prior art" rests on an unverified paper.
- **Piech et al. (ICML 2015):** the repo describes it as an LSTM over variable traces; the arXiv abstract describes a linear precondition→postcondition mapping. The repo's characterisation contradicts the abstract.
- `PRIOR_ART_MATRIX.md`: its footer still says "All citations are to real published works". Entries [17], [33], [39] are known unciteable, [36] is mislabelled, [21], [24], [25] have garbled headings. **It must not be used as a bibliography.**
- **There is no `.bib`, `.tex` or reference list.** `CITATION.cff` is a software citation only.

## I.2 Related work vs SBG

| Work | Problem and technique | SBG difference | Meaningful? | Defensible? |
|---|---|---|---|---|
| Kessel & Atkinson | Does behaviour sampling judge functional equivalence? Large empirical study. | Structured trace distance vs response comparison. | **Unknown** (full text unread). | Only abstract-level. |
| Danglot (DCI) | Behavioural change detection in CI via test amplification, with a 60-commit Java benchmark. | No test generation, Python, synthetic labels, continuous score. | Yes for mechanism. | Yes as complementary. DCI's own "first curated dataset" claim means SBG cannot claim benchmark novelty. |
| Differential testing / regression (Evans, Jin, Person, Xie & Notkin) | Compare two versions on inputs. | Trace-derived distance vs output/state difference. | **Unverified. The central unfilled gap.** | Not yet. Jin et al. and Xie & Notkin compare internal behaviour. |
| Jiang & Su; Podgurski & Pierce | Equivalence mining by random testing. | Fixed 11-input battery. | Unknown | No method-level claim. |
| TRACED; Wang/Singh/Su; Piech | Learned execution-aware or trace embeddings. | Non-learned, interpretable, pairwise. | Different paradigm | Yes as background; Piech must be rewritten. |
| EquiBench | LLM equivalence benchmark, 2,400 pairs, analysis-derived labels. | SBG labels are equivalence on protocol inputs only. | Yes | Yes. |
| Krinke; Yu et al. | Benchmark label-validity in clone detection. | Shared motivation (shortcut baselines). | Analogous | Cite Yu et al.'s linear baseline as the closest methodological precedent. |
| Just et al.; Ojdanić | Mutants vs real faults; mutant relevance. | SBG's null on real bugs. | Explains the limitation | Cite as threats to validity. Not read. |

## I.3 Claims that must not be made

- "First execution-based equivalence method / first behavioural distance" — Podgurski & Pierce 1992, Kessel & Atkinson, Xie & Notkin, Jin et al. and others predate it. This language survives in `NOVELTY_ANALYSIS.md:132,270,286` and `literature_novelty_audit.md`.
- "First to name the edit-size confound" — supported only against the roughly 12 sources the repo touched. No systematic search was done.
- "Rename-invariance is novel" — dynamic birthmark literature is unread.
- Any claim built on Sumner or Piech as described in the repo.

## I.4 Related-work gaps (all CANDIDATE — verify before citing; Crossref confirms metadata only) [V-sub]

| Gap | Candidate |
|---|---|
| Value-spectra regression testing | Xie & Notkin, IEEE TSE 2005, `10.1109/tse.2005.107` |
| Execution/trace comparison | Sumner & Zhang, "Comparative causality", ICSE 2013, `10.1109/icse.2013.6606573` |
| Dynamic birthmarks | Myles & Collberg (LNCS 2004, `10.1007/978-3-540-30144-8_34`; SAC 2005, `10.1145/1066677.1066753`); Wang et al., ACSAC 2009, `10.1109/acsac.2009.24` |
| Equivalent mutants | Papadakis et al., "Trivial Compiler Equivalence", ICSE 2015, `10.1109/icse.2015.103` |
| Metamorphic testing | Chen et al., ACM Computing Surveys 2018, `10.1145/3143561` |
| Regression test selection | Rothermel & Harrold, IEEE TSE 1996, `10.1109/32.536955` |
| Functionally similar code | Suzuki et al., SCAM 2017, `10.1109/scam.2017.21` |
| Compiler/semantic equivalence checking | Churchill et al., PLDI 2019 (lookup failed in this audit; UNVERIFIED) |
| Benchmark validity for behaviour-change/equivalence | None found. Needs a targeted search. |
| Python-specific dynamic analysis | None found. Needs a targeted search. |

**Defensible novelty statement.** *"We contribute a size-aware, oracle-validated, preregistered evaluation design for execution-based behaviour-change detection, together with an empirical finding: a rename-invariant, output-free trace representation carries signal beyond edit size but no statistically established signal beyond simple execution statistics on a small withheld set."* The words "first", "novel framework" and "genome" (as an implied breakthrough) should stay out of the title and abstract.

---

# Section J — Manuscript assessment

**A complete manuscript does not exist.** The most authoritative file is `artifacts/paper_evidence/FINAL_MANUSCRIPT_BLUEPRINT.md`. Searches of the repo, the other three SBG-related clones and the Desktop found no `.tex`, `.bib`, `.docx` or IEEE template for SBG. The `paper_data/` folder in `SF Projects/SBG` is V1–V6-era evidence.

| Section | Status | Basis |
|---|---|---|
| Title | PARTIALLY COMPLETE | Blueprint proposes "How Much Does a Trace-Derived Behavioural Representation Add? A Size-Aware, Oracle-Validated Evaluation…" plus an alternative. Not frozen. |
| Abstract | **MISSING** | Only a list of permitted claims. |
| Introduction | **MISSING** | Outline only. |
| Motivation | PARTIALLY COMPLETE | Edit-size story is documented, not written. |
| Research questions | REQUIRES REWRITING | `RESEARCH_QUESTION.md` predates V9/V10. Blueprint refers to RQ1–RQ4. |
| Related work | PARTIALLY COMPLETE | Comparison table has "not verified" cells. No `.bib`. |
| Methodology | PARTIALLY COMPLETE | `FORMAL_MODEL.md` predates V8–V10; `EVALUATION_PLAN_V9.md` is current. |
| Representation | PARTIALLY COMPLETE | V5 code and README correct. |
| Experimental design | PARTIALLY COMPLETE | Freezes and plans exist. |
| Results | PARTIALLY COMPLETE | Frozen JSON exists. No built tables or figures. |
| Statistical analysis | PARTIALLY COMPLETE | `FINAL_STATISTICAL_AUDIT.md` and the implementation exist. |
| Discussion | PARTIALLY COMPLETE | Claim boundaries and case studies exist. |
| Threats to validity | PARTIALLY COMPLETE | Blueprint §8 is current. `THREATS_TO_VALIDITY.md` is **stale**. |
| Limitations | PARTIALLY COMPLETE | Blueprint §9 is current. `docs/current/LIMITATIONS.md` is stale. |
| Conclusion | **MISSING** | – |
| References | **MISSING** | No `.bib`; several citations unsafe. |

**Scientifically inaccurate if reused:** the README "Short version" and "Claim strength" blocks, `FINAL_STANFORD_READINESS_REPORT.md`, `PRIOR_ART_MATRIX.md` and the novelty-claim sections of `NOVELTY_ANALYSIS.md`.

**Figures.** `docs/figures/` holds four SVGs built by `make_figures.py`. They are vector (no resolution problem), but all show **V6-era numbers** (published, output-free and corrected AUROC, 0.105 vs 0.601). None shows V10, V9c or edit-size content. They are consistent with the generated README block but misleading as headline figures. **None of the planned Fig. 1–4 or Tables 1–8 exists.**

**Blueprint caveat.** `FINAL_IEEE_ACCESS_READINESS.md` calls the state "READY TO DRAFT" and uses "V10_INDEPENDENT_EVALUATION" as the filename. The "independent" label conflicts with the same repo's `INDEPENDENT_EVALUATION_LIMITATIONS.md`. The blueprint's checklist item 16 says "Kessel & Atkinson … full text read", which is **false**.

---

# Section K — Reproducibility and software quality

| Check | Result |
|---|---|
| Tests (copy of HEAD, py3.13.5) | **807 passed, 3 warnings, 0 failures, 366.8 s.** [V-sub] The README says "516 tests"; `CLAIMS_REGISTRY` says 653; `REPRODUCTION.md` says 657. All stale. |
| Consistency gate | **10/10 pass** (`consistency_check.py`; non-mutating; run on the copy only). [V-sub] |
| Hash verification | `FREEZE_V10` 25/25 ✓; `EXPERIMENT_MANIFEST_V4` 18/18 ✓; `FREEZE_V10_SCORED` ✓ (644 rows, 641 evaluated); `FREEZE_V9` code 12/12 ✓; `FREEZE_V8` 10/11 (the `evaluate_v8.py` difference is disclosed in amendments 1 and 2). [V-sub] |
| Dataset-block hashes in FREEZE_V8/V9; `freeze_*.json` | Not checked here (gate C9 covers the Phase-2 freezes). |
| GitHub CI | `ci.yml` runs on push to `main`, PRs and manual dispatch. **Last runs red** (#8 on `9be24b3`, #7 on `93ef3f3`): py3.9 jobs fail at setup (no 3.9 on Ubuntu 26.04), and `fast-experiments` py3.13 fails `check_reproduction.py --strict` (byte-exact artifacts not reproduced on the Linux runner). Tests py3.13 and the scientific-integrity job pass. [V-sub] |
| Environment match | Experiments: macOS arm64, CPython 3.13.5. `requirements-lock.txt` mentions 3.13.15. `PYTHON_VERSION_SENSITIVITY.json`: up to 0.41 distance shift between 3.9.6 and 3.13.15. A 3.9 CI leg can only check code, never reproduce artifacts. |
| `requirements-lock.txt` | Pins pytest and dependencies only. `TEST_LOCK.json` is a stale 2026-08-30 artifact. |
| Makefile | **Overwrite risk:** `reproduce-fast`, `reproduce-v5`, `reproduce-output-free`, `benchmark-v6`, `v7-train`, `v7-fit`, `v7-test`, `quixbugs`, `bugsinpy`, `java` have **no code-level overwrite guard**. `check`/`verify-artifacts` rewrite audit JSONs, manifests, tables, figures and the README (deterministic, but not read-only). No V8/V9/V10 targets exist. `make help` still describes the Phase-2 flow. |
| Overwrite guards | `evaluate_v10.py` (`:43`, `:94`), `evaluate_v9.py` (`:256`, `:286`) refuse to overwrite. `evaluate_v8.py` refuses unless `--allow_overwrite_never_use` is passed. Committed frozen thresholds and V6/V7 pairs rely on convention. |
| Reproduction hazards | `FINAL_SPRINT_REPORT` steps need `venvs/py313` and a **local-only** COBOL path (`/Users/manassakthivel/Desktop/COBOLSRC`). The zero-score row needs an untracked file. |
| Headline numbers traceable to committed artifacts? | **Yes for V9c-val, V10, V8 test, real-bug rescoring.** The README's V6 headline is traceable but obsolete. |
| Stale / misleading historical reports | `FINAL_STANFORD_READINESS_REPORT.md` (repo root, V6 era), `STATUS.md` (three stacked eras, no V10), `docs/VERSION_MAP.md` (table ends at V6), `docs/CLAIMS_REGISTRY.yaml` (no V9/V10 claims; C021 correctly says INSUFFICIENT_EVIDENCE), `README.md` L46-56, L316-319, L350-352, L492-502, L504, L4, L87. |
| Does the consistency gate catch stale claims? | Partly. It checks internal consistency of the Phase-2 artifacts and claims but does not flag the V6-era README body. |

I did **not** run: `verify_trace_v4.py`, the 3.9 interpreter, or any `reproduce-*` target.

---

# Section L — Existing work (what is already done)

| Task | Existing status | Evidence | Remaining work |
|---|---|---|---|
| Research audit | **Done, repeatedly** | `FINAL_PROJECT_HANDOFF.md`, `FINAL_STATISTICAL_AUDIT.md`, `INCREMENTAL_VALUE_AUDIT.md`, `REAL_BUG_GENERALISATION_AUDIT.md`, this report | Do not redo. Update `FINAL_PROJECT_HANDOFF.md` §A (PR #2 is merged). |
| Literature review | **Partial** | `RELATED_WORK_COMPARISON.md`, `LITERATURE_ACCESS_LOG_2026-10-30.md` | Kessel & Atkinson full text; Jin / Xie & Notkin / Person at method level; systematic searches (§I.4); build `.bib`. |
| Novelty analysis | **Done at a defensible level** | `FINAL_NOVELTY_POSITION.md` | Remove "first" language from the older docs; do not quote them. |
| Statistical verification | **Done and independently re-verified here** | `FINAL_STATISTICAL_AUDIT.md`, §F | Optionally a LOPO fairness write-up (exploratory). |
| Manuscript outline | **Done** | `FINAL_MANUSCRIPT_BLUEPRINT.md` | Fix blueprint item 16 and the "independent" naming. |
| Full manuscript | **Not started** | No `.tex` / draft anywhere | Everything. |
| Figures | **Planned only; the 4 existing SVGs are V6-era** | Blueprint §6 | Build Fig. 1–4 and Tables 1–8 from frozen JSON. |
| IEEE formatting | **Not started** | No template | Obtain the IEEE Access template and set up LaTeX. |
| Reproducibility | **Strong core, rough edges** | §K | CI, stale docs, untracked files. |
| Final independent AI review | **Not done for a manuscript** | – | After a draft exists. |
| Local work not on GitHub | `SBG FINAL` working tree; `independent-audit/…` branch; 4 untracked files | §B.4 | Back up; do not merge into the paper. |

**WRP-related outputs:** none found in any SBG-related location. UNVERIFIED for locations I did not search.

---

# Section M — Critical blockers

## Blockers to submission

| # | Blocker | Type |
|---|---|---|
| 1 | **No manuscript, abstract, figures, tables or IEEE-formatted file** | Completeness |
| 2 | **No bibliography.** Nearest-neighbour prior work (Kessel & Atkinson) and the differential-testing / value-spectra family are unread; several repo citations are wrong | Completeness / accuracy |
| 3 | **README, VERSION_MAP, STATUS, CLAIMS_REGISTRY, FINAL_STANFORD_READINESS_REPORT contradict current evidence** (V6-era headline claims, "516 tests", "13 programs", external "not re-run") | Accuracy of the public record |
| 4 | **V10 "independent" naming** in several files and in the blueprint's own checklist | Accuracy |
| 5 | **CI is red** and the claim "CI runs 3.9 and 3.13" is false | Reproducibility statement |

## Scientific limits that must be disclosed (not blockers if scoped)

- H4 null; underpowered (19 clusters).
- V10 same author and generator; post-failure design of the composed benchmark.
- Equivalence = on 11 synthesised inputs.
- Real-bug null.
- Output-free blind spot (SC-6 73.9%).
- Python-only, algorithmic programs, one corpus.
- Edit-size confound reduced, not removed.
- Freeze/results committed together.

---

# Section N — Final recommendations

**Fix**
- Write the manuscript from frozen V9c-val and V10 JSON only.
- Replace the stale README body, `VERSION_MAP.md`, `STATUS.md` and the claims registry (after submission is drafted; edits to the repo are outside this audit).
- Rename "independent" to "withheld, same author".

**Disclose**
- Everything in Section M's second table.
- The V8 negative result as motivation, not as something to hide.
- That freeze and scoring were in one commit.
- That Kessel & Atkinson was read at abstract level only (if full text cannot be obtained).

**Leave as future work**
- Independently authored or real-project programs.
- Output-based differential-testing baseline.
- Relaxing SAFEGUARD-2.
- Another language.
- Weight fitting for V5 / state-only variants.
- Real-bug input protocol redesign.

---

# Section O — Submission readiness verdict

## **NOT READY FOR SUBMISSION.**

**Explanation.** The verdict follows from the state of the paper, not the state of the experiments.

- There is no manuscript, no bibliography and no built figures (Blockers 1 and 2). That alone makes submission impossible today.
- The statistical evidence is sound, reproducible and honestly negative on the questions that matter most (H4, real bugs). It supports a **scoped** paper. It does **not** support a "novel validated representation" paper.
- If the work is scoped as in §D.3 and §I.4, the remaining work is writing, bibliography verification and documentation cleanup. **It is not additional science.** That is why I did not choose "conditionally ready — scientific blockers remain". The remaining scientific limits are disclosure items.
- Technical readiness is a separate matter from editorial acceptance. A paper whose main novel-method result is a null against a simple baseline is a legitimate negative-result paper, but acceptance prospects at IEEE Access are uncertain and are not predicted here.

---

# Section P — Answers to the final research questions (§21)

1. **Strongest defensible contribution:** an edit-size-aware, oracle-validated, preregistered evaluation methodology, plus an empirical finding that a trace-derived representation beats size-based baselines but has no established gain over simple execution statistics.
2. **Primary method:** **SBG V5 with fixed weights 0.50/0.25/0.25.** V6 is an experimental arm only.
3. **Headline split:** **V10** (19 withheld programs, 638 pairs), described as "withheld, same author and generator", with **V9c-val** as the earlier replication and **V8 test** as the motivating negative.
4. **Main paper:**
   - V8 negative (0.694 vs 0.876 reversed edit).
   - Edit-size diagnosis (Table/Fig).
   - V9c-val and V10 H1–H6 with Holm.
   - Exact-size stratified AUROC.
   - The H4 null, prominently.
   - SC-6 blind spot.
   - Real-bug null, one table.
5. **Supplementary:** LOPO refit, family-level concordance, case studies, review-effort curves, component AUROCs, post-hoc V10 supplement (all labelled exploratory), hard-negative and regression sets.
6. **Exclude entirely:** original published-protocol numbers; the V6-era headline (SBG 0.601 vs AST 0.105); "0.075 leak"; COBOL and Java; the 3,777-pair benchmark; any "first / novel / validated / detects bugs / beyond execution statistics / V6 better" statement; the SBG FINAL v7 numbers.
7. **Strongest abstract-level claim:** *"On 19 withheld, oracle-validated programs, a trace-derived behavioural distance reaches AUROC 0.897 [0.863, 0.922] against 0.616 for forward edit size, but adds no statistically established gain over edit size plus simple execution statistics (+0.006, 95% CI [−0.069, +0.068]), and does not transfer to real-bug corpora."*
8. **Three most serious reviewer objections:**
   1. *"The comparison against the strongest baseline is a null, on 19 programs of one author; why is this a contribution?"* (underpowered, same-author).
   2. *"Labels are equivalence on 11 synthetic inputs, mutations are synthetic, and the real-bug transfer is at chance."*
   3. *"Prior work (Kessel & Atkinson, Jin et al., Xie & Notkin, birthmarks) already compares executions or internal behaviour of program versions; where is the novelty?"*
9. **Can the manuscript honestly be completed today?** A **complete, scoped draft** with tables and figures from frozen JSON: yes, if no new experiments are run and about 8–10 focused hours are available. A **verified, submission-quality** version: marginal; it depends on literature access for Kessel & Atkinson and on method-level reading of three differential-testing papers. If those cannot be obtained, disclose them as abstract-only and do not submit with unverified citations.
10. **Must be done before submission:** see `SBG_TODAY_COMPLETION_PLAN_2026-11-04.md`, P0.
11. **Abandon for this submission:** real-bug generalisation improvements, new baselines, weight fitting, V6 promotion, COBOL/Java, independent-program construction, any change to inputs or thresholds.
12. **SBG vs RELIC (RIFT FINAL) as an IEEE Access candidate:** **On evidence alone, SBG's chain is stronger; RELIC has a draft and SBG does not.** [V-sub; RELIC not independently audited]
    - RELIC's own readiness document claims 9 of 9 gates and 626 passing tests, but also reports the learned variant at **0.0% P@1** on dev, val and held-out, H1 and H3 **not supported**, and a README that says live evaluation is "pending" — which contradicts the readiness document.
    - SBG has preregistered, hash-frozen, reproduced positive results (H1–H3) and a clear null (H4) with 807 verified passing tests.
    - RELIC's `docs/IEEE_PAPER_DRAFT.md` is roughly 1,600 words of Markdown.
    - They are different problems and neither was compared on a common standard. I would **not name a winner** from this. The fair statement is that SBG has the stronger *evidence chain*, RELIC has the stronger *manuscript progress*, and neither has a strong positive headline.

---

# Appendix 1 — Claim-to-evidence matrix

| # | Claim | Artifact | Result | Test / CI | Population | Version | Class |
|---|---|---|---|---|---|---|---|
| 1 | SBG V5 above chance | `V10_INDEPENDENT_EVALUATION.json` | 0.897 | cluster permutation; Holm 0.003; CI [0.863, 0.922] | 19 programs / 638 pairs | V5, V10 | Confirmatory (frozen) |
| 2 | SBG adds to edit size | same | +0.254 | Holm 0.005; [0.218, 0.285] | same | V10 | Confirmatory |
| 3 | SBG beats forward edit size | same | 0.897 vs 0.616 (+0.281) | Holm 0.005; [0.244, 0.308] | same | V10 | Confirmatory |
| 4 | **No established gain beyond edit size + execution statistics** | same | +0.006 | Holm 1.0; [−0.069, +0.068] | same | V10 | Confirmatory (null) |
| 5 | Same on a second split | `V9_VAL_EVALUATION.json` | +0.021 | Holm 0.117; [−0.005, +0.048] | 11 programs / 432 pairs | V9c-val | Confirmatory (null) |
| 6 | V6 not shown better than V5 | V10 | +0.0029 | Holm 0.090 | same | V6-exp | Confirmatory (null) |
| 7 | Edit size alone solves the V8 benchmark | `V8_TEST_EVALUATION.json`, `LABEL_GENERATION_AUDIT.json` | reversed edit 0.876 vs SBG 0.694 | pre-declared NOT DEMONSTRATED | 22 programs / 956 pairs | V8 | Confirmatory (negative) |
| 8 | Composed design reduces confound | `DATASET_SUMMARY_V3.json`, V10 | forward edit 0.616 | descriptive | V9c, V10 | – | Descriptive |
| 9 | Stratified AUROC | V10 | 0.875 | exploratory | equal-size strata only | V10 | Exploratory |
| 10 | SC-6 invisible | `INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json` | 73.9% (17/23) zero | descriptive | SC-6 CHANGED | V10 | Exploratory |
| 11 | Real bugs at/below chance | `BUGSINPY_output_free_v7.json`, `QUIXBUGS_output_free_v7.json`, `EXTERNAL_RESCORE_V8.json` | 0.410 / 0.388 (0.497 / 0.444 excl. SP-2) | CIs span 0.5 only after exclusion | 41 and 40 positives | v7 and v8-rescore | Exploratory |
| 12 | State alone 0.917 | V10 | descriptive | – | V10 | – | Descriptive only |
| 13 | LOPO refit | `INCREMENTAL_CONTRIBUTION_ANALYSIS_lopo.json` | 0.885 / 0.895 / 0.897 | – | V10 | – | Exploratory |

## Claims that must NOT appear in the manuscript

| Claim | Why not |
|---|---|
| SBG is validated for real-world bug detection | BugsInPy 0.410 / QuixBugs 0.388 (≤ 0.5 after SP-2 exclusion). Exploratory only. |
| SBG provides incremental value beyond execution statistics | H4 +0.006, CI includes 0, on two splits. |
| SBG is the first execution-based equivalence method | Prior art (Podgurski & Pierce; K&A; Xie & Notkin; Jin et al.). |
| SBG generalises across programming languages | Python only; no COBOL or Java result exists. |
| V10 represents independently authored software | Same author and generator. |
| SBG V6 is superior to V5 | H5 Holm 0.090. |
| Exact edit-size matching establishes generalisation | It reduces a confound. 17–23% retention, and 92% of V10 sets still have the larger edit on the CHANGED side. |
| SBG beats execution statistics (using M_EX 0.791) | Combiner transfer failure; LOPO M_EX 0.885. |
| Equivalent = semantically equivalent | Only equivalent on protocol inputs. |

## Appendix 2 — Evidence not independently checked by me

- Near-duplicate re-run on splits; SP-8/SP-11 label rates on V8 test; zero-score analysis effect of the stale pair.
- BugsInPy zero count 21 vs 26.
- Crossref entries: all beyond the Kessel, Danglot and EquiBench verifications.
- RELIC's test count and results.
- `verify_trace_v4.py`, the py3.9 interpreter, and the dataset-block hashes in FREEZE_V8/V9.
