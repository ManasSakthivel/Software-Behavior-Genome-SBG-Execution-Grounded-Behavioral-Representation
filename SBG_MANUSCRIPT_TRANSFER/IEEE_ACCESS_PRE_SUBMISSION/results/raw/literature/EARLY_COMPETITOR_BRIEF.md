# EARLY COMPETITOR BRIEF (A1 → A4) — EXP-A1-001 — written 2026-11-14 (UTC fetch dates in `fetchlog.jsonl`)

Purpose: enough algorithmic detail to implement **ADAPTED** baselines on the shared trace cache (schema in PROTOCOL §3:
per-input `ret, ret_type, exc, stdout, cov, events=[c/r/e/l, function, lineno, locals]`, 11 inputs, run 0 only).
Everything below is labelled with the **access level** of my source, because I may only describe what I read.
Final A/B/C/D classification and full justification will be in `PKG/03_COMPETITOR_LANDSCAPE_AND_NOVELTY.md`.

## 0. Two facts A4 must know before implementing anything

1. **Label tautology.** SBG's CHANGED label = "return value / exception / stdout / argument-mutation differs on the protocol's 11 synthesised inputs"
   (PROTOCOL §2). Any baseline that compares *outputs on those same 11 inputs* (K&A behaviour sampling, ChangeGuard comparator, BERT/differential
   testing, DCI-style assertion check) **reproduces the label by construction → AUROC ≈ 1.0 is not a result, it is the definition.**
   Report it only as "output-reading (privileged) ceiling on label-defining inputs". The scientifically meaningful output-reading baseline
   uses **independent inputs** (fresh seed / different generator / fewer-than-11 stimuli = the K&A "how many tests" axis). That needs *new* executions,
   not the shared cache (cache = label-defining inputs only).
2. **No numpy/scipy/sklearn** → neural execution-trace models (TRACED, Wang-Singh-Su, blended embeddings, CodeExecutor, NExT) cannot be faithfully
   run. At most a clearly labelled *non-neural bag-of-trace-tokens + stdlib logistic/NB* proxy fitted on V9c-train (class **C/B-weak**, never presented as "TRACED").

## 1. Kessel & Atkinson 2019 — behaviour sampling for functional equivalence (SCAM 2019, 10.1109/SCAM.2019.00030)
* **Access:** paper = ABSTRACT-ONLY (closed IEEE; no OA copy anywhere; MADOC record 53324 has no PDF). Method model taken from the author's **open PhD thesis** (Kessel 2023, MADOC 64107; FULL-TEXT of the thesis extracted; sections actually read: §3.4.1, §9.1–9.2, §11.2.1–11.2.2, §16.1.1, §16.2 — the SCAM study itself is not a chapter) — i.e. *thesis-level description of the same framework*, **not** the SCAM experiment protocol.
* **Recorded:** per (system, stimulus) an *actuation* = serialised **response values** (return value / output) of the system for a stimulus; stored in a stimulus-response matrix (SRM).
* **Compared:** thesis §3.4.1: functional equivalence ⇔ A_g(x)=A_h(x) for all x in the sampled stimuli. §11.2.2: for graded similarity, concatenate each system's response strings and apply a normalised **string distance** (Levenshtein/Jaccard/q-gram…); distance matrix symmetric, d(i,i)=0.
* **Decision:** "non-equivalent as soon as one stimulus yields a different response". Abstract: ≥39 random tests needed to recognise non-equivalence 85 % of the time (vs 4 assumed originally); coverage-guided generated tests need far fewer.
* **Adapted baseline (B, output-reading):** `score = (#inputs with (ret,exc,stdout) differing)/n_inputs` (binary-any variant: 1 if any differs). Variants: (i) all 11 label-defining inputs → tautological ceiling; (ii) *k* random subsets of inputs (k=1,2,4,…,11) to reproduce the "tests needed" curve — still same inputs so still biased; (iii) **independent inputs** (new executions). Optional graded variant: normalised Levenshtein on `repr(ret)+exc+stdout` per input, averaged.
* **Code:** LASSO platform (Java; thesis + papers say publicly available; not verified here by me). No Python implementation of the SCAM study known.

## 2. ChangeGuard (Gröninger, Souza, Pradel; Proc. ACM SE 2(FSE) 2025, 10.1145/3715760; arXiv 2410.16092) — FULL-TEXT-READ
* **Task = SBG's task** (semantics-changing vs semantics-preserving change, **Python**, function level). The *closest contemporary task-level competitor*.
* **Recorded** (§2.4): for old/new function executed on the same inputs: (1) serialised **argument values (post-call) and return value** (generator/coroutine unwrapped); (2) captured **stdout/stderr**; (3) **log of calls to external functions** (name+args+order) — because learning-guided execution (LExecutor, neural model injects missing values) abstracts external calls; (4) **exceptions** (only "intentional" = raised via `raise`/AssertionError compared by type+args; unintended exceptions from injected values ⇒ ignore).
* **Decision:** any difference in (1)–(4) ⇒ *semantics-changing*; else after k=300 executions: *likely semantics-preserving*; if changed lines never reached / all runs died ⇒ *inconclusive*. Binary, no score.
* **Labels/eval:** 224 manually annotated commits (10 Python projects) + 3 automated-refactoring datasets; precision 77.1 %, recall 69.5 %; regression tests recall 7.6 %. No AUROC, no edit-size control.
* **Adapted baseline (B, output-reading):** run comparator (1)-(4) on the 11 protocol inputs from the cache: `score = fraction of inputs with any difference in {ret, exc type/args, stdout, args-mutation, ordered call-event list of *external* functions}`; handle "unintended exception" by ignoring inputs where both raised `TypeError/AttributeError/...` caused by synthesised args. **Same tautology as §0.1 for ret/exc/stdout; the extra signal is the external-call log** (compute from `events` type `c` whose function is not defined in the module).
* **Code:** https://github.com/sola-st/ChangeGuard (MIT, Python, pushed 2025-05-21; verified via GitHub API) built on https://github.com/michaelpradel/LExecutor (MIT). Needs HF transformers + a fine-tuned model → **not runnable under stdlib-only**; implement comparator only.

## 3. DCI — Danglot, Monperrus, Rudametkin, Baudry (EMSE 25(4) 2020, 10.1007/s10664-019-09794-7; arXiv 1902.08482) — FULL-TEXT-READ
* **Recorded/compared:** Java unit tests of the commit; **AAMPL** (assertion amplification: add assertions on all observable values of the object under test) and **SBAMPL** (hill-climbing input amplification); behavioural change = *an amplified test passes on pre-commit, fails on post-commit* (§2.3).
* **Decision:** binary per commit; detected 25/60 (SBAMPL) and 9/60 (AAMPL) of curated commits; applicable to 15.29 % of commits (needs an existing test executing the change). 
* **Adapted baseline:** only a *loose analogue* is possible (class **C**): "observe every value reachable from the entry function (return value, locals at return events) and assert equality across versions" == value-comparison on the same inputs (again tautological). Do **not** call it DCI.
* **Code:** https://github.com/STAMP-project/dspot (LGPL-3.0, Java), https://github.com/STAMP-project/dspot-experiments (benchmark). Java-only.

## 4. Value spectra / path spectra comparison — Xie & Notkin, IEEE TSE 31(10) 2005, 10.1109/TSE.2005.107 — ABSTRACT-ONLY (closed)
* From the abstract: *value spectra* characterise behaviour **inside the black box** (function-level entry/exit states: args, return values, state); compare old vs new spectra to detect **internal deviations even when program outputs are identical**; deviation-propagation call tree; path spectra (previous work) as approximation. 8 C programs.
* **This is the direct prior art for "output-free / internal-behaviour comparison"** (but value spectra *do* read return values; the path-spectrum variant does not).
* **Adapted baselines (B, ADAPTED from abstract-level description — say so):**
  * *path-spectrum* (output-free): per function, multiset of executed lines (from `l` events) or the set of covered lines (`cov`); `score = 1 − Jaccard` (set) and/or L1/total of per-line hit counts, averaged over inputs.
  * *value-spectrum* (output-reading): per function, set of (args-snapshot at `c`, return-snapshot at `r`) tuples from `locals` snapshots; `score = |symdiff|/|union|`.
  * *deviation-presence*: `score = 1[any function's spectrum differs]`.
* **Code:** none known for Python.

## 5. Differential testing / BERT — Evans & Savoia ESEC/FSE 2007 (10.1145/1295014.1295038), Jin–Orso–Xie ICST 2010 (10.1109/ICST.2010.64) — ABSTRACT-ONLY (closed); DCI §7.2 gives a secondary description (secondhand: BERT evaluated on a small artificial project [~60% of generated inputs revealed the seeded difference] and on Joda-Time, 54 version pairs → 36 behavioural differences of which only 1 was an actual regression fault; DCI text lines ~1415-1425 of text/danglot_dci.txt)
* BERT: (1) generate many test inputs focused on changed code, (2) run on old & new, identify differences in the tests' behaviour (abstract does not say whether this is outputs only or also internal state), (3) analyse/present. Evans & Savoia: create test suites for both versions and contrast both versions with both suites.
* **Adapted baseline = same as §1 (K&A) / §2 with test generation replaced by SBG's input battery.** Class **B** (output-reading, label-tautological on shared inputs).

## 6. Execution comparison / trace alignment — Sumner & Zhang, "Comparative causality", ICSE 2013, 10.1109/ICSE.2013.6606573 — ABSTRACT-ONLY (closed)
* Abstract: given **two executions and observed differences**, find causes by **state replacement** (replace part of the state at an earlier point to see whether the target difference is induced), uses a novel execution model, symmetric analysis of omission differences, slicing to limit scope. It is a **debugging/explanation** technique, not a version-pair scoring technique.
* **The "Sumner et al., Comparative analysis of software behavioral traces, ICST 2011" cited in the SBG repo (PRIOR_ART_MATRIX [42]) was NOT found** in Crossref (top-2 bibliographic hits: *Precise Calling Context Encoding*, TSE 2012; *Comparative causality*, ICSE 2013). Treat as non-existent/unverified; do not implement from the repo description.
* **Adapted "trace-alignment distance" baseline (B, ADAPTED; not Sumner & Zhang):** canonicalise function names by first-call order (as SBG does) and compute normalised edit distance / LCS between the `c`-event name sequences of old vs new per input, averaged over inputs; optional "first divergence position / trace length".

## 7. Dynamic software birthmarks — Myles & Collberg (K-gram birthmarks, SAC 2005, 10.1145/1066677.1066753; WPP birthmarks LNCS 2004, 10.1007/978-3-540-30144-8_34), Wang et al. (system-call birthmarks, ACSAC 2009, 10.1109/ACSAC.2009.24) — ABSTRACT-ONLY
* Birthmark = set of **k-grams of an execution sequence** (instruction opcodes / system calls / API calls); similarity = set containment / Jaccard / Dice; purpose: **plagiarism** (are these two the *same* program?), credibility + resilience to semantics-preserving transformations — i.e. **the same goal as SBG's SP-type invariance and the same ingredient as SBG's call-order bigrams / trigrams.**
* **Adapted baselines (A/B):** `d = 1 − Jaccard(set of k-grams of ordered call-name sequence)`, k∈{2,3,4}, averaged over inputs (name-canonicalised and raw). This is almost literally SBG-V3's bigram component → expect ≈ SBG-V3 behaviour.
* **Code:** none for Python (SandMark is Java).

## 8. Neural execution-trace models — Wang–Singh–Su (arXiv 1711.07163; code https://github.com/keowang/dynamic-program-embedding, last push 2018-06-30), Wang & Su blended embeddings (PLDI 2020, 10.1145/3385412.3385999; arXiv 1907.02136), TRACED (ICSE 2024, 10.1145/3597503.3608140; arXiv 2306.07487), CodeExecutor (arXiv 2305.05383), NExT (arXiv 2404.14662) — arXiv FULL-TEXT where listed
* **Recorded:** sequences of **live-variable value tuples** per executed step (W-S-S, blended), or source + inputs + traces for pre-training (TRACED). **Values are read** (not output-free). Trained on labels/self-supervision; evaluated on student-error classification, clone retrieval (POJ-104, MAP@R), vulnerability detection, execution prediction — **never on version-pair change judgement**.
* **Adapted baseline:** none faithful (needs GPU/torch). Class **D** for faithful; **C** (qualitative). A stdlib proxy would be a different method.

## 9. LLM-based change/equivalence judgement (2024-2026) — Testora (Pradel, ICSE 2026, 10.1145/3744916.3764527), Mokav (Etemadi et al., JSS 2025, 10.1016/j.jss.2025.112571), SemaDiff (Ayub et al., arXiv 2607.13111, 2026), ProbeGen (Allamanis & Yin, arXiv 2502.18473), EquiBench (Wei et al., arXiv 2502.12466) — FULL-TEXT-READ (arXiv) 
* All generate *tests/probes with an LLM* and compare **outputs** of old/new (Testora also uses PR text; SemaDiff = Java commits; Mokav = Python pairs from Codeforces + QuixBugs, goal = difference-exposing test). EquiBench = LLM judges equivalence **over all inputs** (labels from analysis/compilers; 2400 pairs; Python/C/CUDA/x86-64). **Class D/C for head-to-head** (LLM, network, different label regime). Testora code https://github.com/michaelpradel/Testora (MIT); EquiBench https://github.com/Anjiang-Wei/EquiBench (Apache-2.0).

## 10. Static baselines A4 may add cheaply (Class A, no new literature claim)
* *Normalised bytecode distance* (Python analogue of Trivial Compiler Equivalence, Papadakis et al. ICSE 2015, 10.1109/ICSE.2015.103): compile both files, compare `dis` instruction streams after name normalisation; binary/edit distance. TCE itself is binary-equality of optimised object code (for equivalent-mutant detection).
* Edit-size, AST/token distances already exist in the populations (`edit`, `static_ast`, `static_token`).
