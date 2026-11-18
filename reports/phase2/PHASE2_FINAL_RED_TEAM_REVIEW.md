# Phase 2 final red-team review (independent, adversarial)

Reviewer scope: branch `research/v7b-final-validation`, HEAD `55585e07`. Read-only except this file. Phase 3 activities were not done. Prior reviews were read as claims, not conclusions. Scratch work: `/private/tmp/claude-502/-Users-manassakthivel-Desktop/94829057-e242-408f-a00f-a48d5554f758/scratchpad/{rt,probes}`.

## Verdict: READY WITH DOCUMENTED LIMITATIONS

0 BLOCKING, 5 MAJOR, 9 MINOR. The engine and the evidence pipeline behave as specified, the headline E3 numbers recompute exactly, and the novelty and integrity wording is conservative. The MAJOR findings are about what the data can support (they are interpretation and analysis gaps, not code defects) and should be fixed or stated in the manuscript before independent validation starts. Nothing found invalidates the "exploratory, non-pristine" framing; several findings weaken the one positive claim (lower false assurance).

## Verified (positive evidence)

- Unit suite: `.venv/bin/python -m pytest tests/v7 tests/v6 -q` gave `286 passed, 1 skipped in 100.60s`. `scripts/check_docs_v7b.py`: ALL PASSED. `python3 paper/.../scripts/check_manuscript.py`: ALL CHECKS PASSED (cites=38, labels=48).
- Raw archives: `shasum -a 256 *.tar.gz` equals both `RAW_ARCHIVE_SHA256SUMS.txt` and the archive-side `SHA256SUMS.txt` (7 of 7 match). I extracted only E4 (`ex4/`).
- `scripts/analyze_results.py ... --reference B1 --seed 42 --boot 10000` on `p2_e3_.../processed/dev_pairs_per_system.csv` reproduced `paired_comparisons.csv` byte-identically (diff of the first 25 columns: IDENTICAL).
- Independent recomputation (`rt/stats.py`, own code): B1 FA 24/106, detection 82/106; V7-B FA 13/106, detection 75/106, abstention 122/258 (18 divergent + 104 no-difference); exact McNemar FA b=0, c=11, p=0.000977; detection b=0, c=7, p=0.015625; project sign-flip p about 0.00075 (FA) and 0.031 (detection); own percentile bootstrap CI of the FA difference [-0.205, -0.043] and detection [-0.115, -0.026], equal to the reported intervals. Holm 0.0059 = 0.000977 x 6 is arithmetically consistent with a family of 8 (4 comparisons x 2 outcomes). 78 clusters among divergent pairs; the 11 discordant FA pairs sit in 11 different projects, so clustering does not change the FA test.
- Pre-registration order: `reports/phase2/E3_E7_PROTOCOLS.md` has exactly one commit (`aea4202c`, 2026-11-18 08:07:09 +0530), together with the p2 drivers; the reported E3 run directory is `...092700` (09:27), E4 and later are later still; the file was never edited afterwards (`git log -- file` shows one commit). `git diff 5efcef74 HEAD --stat -- sbgv7 tests sbgv6` is empty, so the engine was not changed between implementation and experiments. E1 started at 07:49, before the protocol commit, but its rule was already fixed in the rerun matrix (`a6afa639`, 00:24) and the protocol says so.
- E4 variants really applied: run-kind counts from the raw evidence (`ex4`, Run records): V0 13,764 (repeat 7,840, replay 840, alt 504); V1 5,930 (no repeats); V2 13,082 (replay 168); V3 13,250 (no alt); V4 4,746; V5 13,754. `variant.json` of V1 holds `repeat.r_det=1`. So "no verdict change" is not caused by a silent no-op.
- Numerical claim file: I recomputed 10 claims (rows 33, 41, 42, 45, 48, 50, 51, 77/78 via `verify_table.json`/`corruption_results.json`, 55, 52): all agreed. Caveat in M-5 below.
- Novelty wording: `related_work.tex:14`, `rqs_contributions.tex:13`, `README.md:80` respect items 1-3, 7, 8 of the "must NOT say" list in `research/literature/NOVELTY_REASSESSMENT_PHASE2.md` section 5. My grep for "first", "novel", "outperform", "state of the art", "immutable", "tamper-proof" found only negated or "not" uses in the manuscript and README. No finding on novelty overstatement (one reservation in m-3).

## Findings

### MAJOR

**M-1. The sufficiency gate does not make "no divergence" answers more trustworthy; the false-assurance gain is pure coverage loss, and the risk-coverage presentation is flattering.**
Evidence (`rt/stats.py`, E3 CSV, 258 eligible pairs): wrong share among NO_DIVERGENCE_OBSERVED verdicts is V7-B 13/61 = 0.213 versus B1 24/130 = 0.185. By level: S1 5/16 wrong (0.31), S2 8/45 (0.18). `results.tex:27` and Table riskcov report "risk 0.096", which is 13/136 where the 136 "decided" pairs include 75 detections; the "S3" row (risk 0, 75 decided) contains only witnessed divergences although S3 is never issued. Discussion text at `discussion.tex:6` ("only the gate lowers false assurance") is true only in the coverage sense.
Balancing positive finding that the manuscript does not report: abstention is selective. 11 of the 24 B1 false assurances became INSUFFICIENT versus 7 of the 82 B1-detected pairs (46% vs 8.5%, one-sided Fisher p about 1.1e-4, `rt/more.py`). This is a better argument for the gate than the current text.
Fix: report precision of NO_DIVERGENCE verdicts (13/61 vs 24/130) and the 46% vs 8.5% selectivity statistic; drop or relabel the S3 row and the "risk" column so it is not a mixture of detections and no-difference calls. Severity MAJOR because the central RQ2 answer is read from the flattering metric.

**M-2. "Lower false alarm (0/152 vs 46/152)" is listed as Supported, but it is a harness artefact plus abstention, and the pre-declared sensitivity analysis was not run.**
Evidence: all 46 B1 false alarms are `renamed_entry_SP-2` pairs (B1 treats a missing entry as a difference; `baselines.tex:2`); 48 of the 152 negatives carry that flag and V7-B returns INSUFFICIENT on all 48 (`rt` Counter). On the other 104 negatives B1 has 0 false alarms, and V7-B abstains on 56 of them. The protocol (E3_E7_PROTOCOLS.md, E3 "Sensitivity (pre-declared)") required `statistics/sensitivity_excluding_SP2_renamed/`; no such directory exists in `results/v7b_phase2_summary/p2_e3_*/statistics/` and no report mentions it. The claim appears at `stats_status.tex:11` and `PHASE2_CONSOLIDATED_EXPERIMENTAL_ANALYSIS.md` section 8; the old README's note that excluding these pairs makes B1 detection exceed V7-B was not carried into the manuscript.
Fix: run the pre-declared sensitivity (or disclose it was skipped as a protocol deviation in section 9 of the consolidated analysis), remove the false-alarm line from "Supported".

**M-3. Label validity and baseline structure limit what the headline can mean.**
(a) All 24 B1 false assurances are synthetic "changed" pairs (generator labels, `datasets.tex` itself says divergence may lie outside the sampled inputs): B1 detects 29/29 QuixBugs pairs, whose label oracle (declared tests) is also the input source, so detection there is nearly circular. Hence "false assurance" is partly "generator said changed, sampled inputs showed nothing", not a verified miss. 77 of 106 divergent pairs drive the whole contrast.
(b) B1 and B1+rep never abstain by construction, so FA(B1) vs FA(V7-B) mainly measures "has an abstention option"; a trivial coverage-gated B1 (abstain if changed lines unhit) and a matched-abstention null were not run. B1+rep is a null for repetition, not for abstention.
(c) The pre-registered hypothesis was "does not have lower detection". Detection is lower by 6.6pp with unadjusted McNemar p=0.0156 and a cluster CI [-11.5, -2.6] that excludes zero; the text says "not significant after Holm" (Holm 0.156). That Holm multiplier is inflated by two degenerate comparisons in the family (B1+rep with p=1, and B4 with trivially tiny p). Calling this "possible loss" understates an observed 7-pair loss.
Fix: state (a) and (b) in Threats, add the coverage-gated baseline in Phase 3 design, and word detection as "lower, CI excludes zero, not Holm-significant under a family of 8".

**M-4. Evidence can be forged by the evaluated program itself, and `verify` cannot see it (documented, but demonstrated here to be easy).**
Probe `probes/f1_v.py`: the variant (x+2) versus base (x+1) does `m = sys.modules['__main__']; m.canon = lambda v: orig(v-1) ...`. Result: `NO_DIVERGENCE_OBSERVED S1`, and `python -m sbgv7 verify` returned `{"verified": true ...}` (rc 0). So a malicious or merely adversarial change yields a false positive-assurance verdict with a verifying log. This is the "result channel shares an address space" limitation in `threats.tex:12` and README, so honesty is intact, but the manuscript's phrase "replayable witnesses" and "verify" invite more trust than this allows; any future use on untrusted code is unsafe. Plain unrechained edits are detected (`probes/forge/b`: "VERIFY FAILED: chain broken at seq 4"); E7 shows re-chained edits are not (3 documented cases).
Fix: keep the limitation in the abstract-level scope statement; Phase 3 should move canonicalisation to the parent or a separate process.

**M-5. The numerical-claim verification is partly self-referential and the E4 headline relies on report-only numbers.**
`NUMERICAL_CLAIM_VERIFICATION.md` recomputes from the same processed CSV/JSON files that produced the paper tables (my independent recomputation agreed, so no number is wrong). 8 of 83 groups are REPORT-ONLY (13,764 / 5,930 / 13,250 / 4,746 run counts, 320/321, 84 witness-id changes, 286/1). I verified the run counts from the raw archive (above); the others I did not re-derive (witness-id 84 and the 320/321 strict key).
Fix: label the file "internal consistency check" and add my archive-derived run counts as an independent source. Severity MAJOR only because the file is presented as the honesty backstop.

### MINOR

- **m-1. Docstring-only change yields NO_DIVERGENCE_OBSERVED/S2.** Probe p5 (docstring edit only): verdict S2, `verdict.json` has `"r_empty": true`. Spec-conformant (S1d) but the headline level is vacuous and the flag is visible only in `verdict.json`. Fix: surface `r_empty` in the CLI output or cap the level.
- **m-2. E5 is a tautology.** The floor only splits S1/S2 inside NDO (the protocol itself predicts identical verdicts); E5 cannot fail. State it as a code-reading check in the manuscript (already partly stated in `discussion.tex:6`).
- **m-3. Novelty reservation.** "At most weakly novel in combination" is acceptable, but the DiffKemp DOI/title duplicate flagged in `NOVELTY_REASSESSMENT_PHASE2.md` (malik2026diffkemp equals malik2021's title) is not resolved; I could not check it (no network use).
- **m-4. README is internally inconsistent.** Line 22/36 says V7-B has lower false assurance than B1; lines 76 and 208 (sections 4.3 and 14) still say the evidence does not support that and that the README does not claim V7-B reduces false assurance; line 129/254 call `results/postfix` "current". `STATUS.md` is a 2026-10-29 V5-era document with no Phase 2 status. Fix: one pass over README sections 4.3, 11, 14.
- **m-6. `scripts/e1_analyze.py --help` is not safe**: traceback `ValueError: not enough values to unpack`, rc 1 (no side effects; git status clean). Other p2 scripts and `p2_variants.py` return rc 0 on `--help`.
- **m-7. Traceability spot-check (15 Conforming rows: V4, V9, B4a, B7a, C2, C4, C10, W4, P8, G3s, S1f, E6, I3, I6, F15).** All cited tests exist as `def` (16 of 16 names checked) and the tests I read (`test_stderr_only_difference_is_not_observed`, `test_capture_truncated_end_to_end`, `test_child_process_survival`, `test_write_outside_denied`) actually exercise the rule. One citation is loose: C2 cites `isolation.py:150-151`, which is the stdout/stderr pump threads, not the stderr exclusion (that lives in `runner.py`). Failure rate: 0 of 15 wrong rule or missing test; 1 of 15 imprecise line. Line numbers elsewhere matched current files. (I did not run each cited test individually; the whole suite passed.)
- **m-8. E6 conclusions are as good as the machine state allows**: battery power, load flags in both runs (4.81, 2.24), ratio CIs are tight (1.584-1.742) because each pair is re-timed 5 times, not because 40 pairs were many; disclosed in the analysis, one-line caveat in the paper would suffice. No E6 re-measurement was made by me.
- **m-9. Adversarial probe outcomes (all via `python -m sbgv7 compare` then `verify`, results in `probes/`)**:
  | probe | observed | correct per spec |
  |---|---|---|
  | p1 forged `{"result":..}` line on stdout (variant also x+2) | DIVERGENT_OBSERVABLE; verify ok | yes |
  | p2 `os._exit(0)` in variant | INSUFFICIENT primary `unsafe_program`; verify ok | yes |
  | p3 10**5000 vs +1 | DIVERGENT_OBSERVABLE | yes |
  | p4 dict subclass differing value | DIVERGENT_OBSERVABLE | yes |
  | p5 docstring-only | NDO/S2, `r_empty: true` | spec-conformant, see m-1 |
  | p6 symmetric binding failure (f(x,y) called with 1 arg) | INSUFFICIENT `no_inputs` | yes |
  | p7 output via `os.write(1,...)` differing | DIVERGENT_OBSERVABLE (fd-1 fold) | yes |
  | p8/p10 wall-clock and `datetime.now` (variant differs by trailing comment) | INSUFFICIENT `nondeterministic` / `flaky_witness` | yes |
  | p9 / q9 set order | p9 (list(set) vs sorted): DIVERGENT; q9 (same list(set) both): NDO/S2 | yes, but hash seed is pinned to 0 so hash-order dependence is untested (disclosed) |
  | p11/q15 hostile env (PYTHONPATH, LD_PRELOAD, PYTHONSTARTUP, SBG_X set in parent) | NDO/S2 (no divergence) | yes, I did not independently prove the variable was stripped inside the child |
  | p13 monkeypatching `json.dumps` in the variant | INSUFFICIENT `unsafe_program` | yes |
  | p14 pure refactor | NDO/S2 | yes (bounded by inputs) |
  | f1 `sys.modules['__main__'].canon` patch | NDO/S1, verify ok | engine wrong, see M-4 |
  Not tested: p12 (write-confinement) was an invalid probe (both versions returned differing constants), so I make no claim about it. First attempts p8 and p10 used identical sources and correctly got "no verdict is issued" (probe error, not engine error).
  `verify` catches: byte edits without rechain (chain broken), missing/truncated logs, verdict.json mismatch, unknown reason codes, content-id mismatch (see `verify.py`). It does not catch: re-chained edits of unverified fields, deleted `verdict.json`, in-process forged observations (f1), anything requiring re-execution.

## Methodology notes (no separate finding)

- Denominators: 258 = 106 + 152 recomputed; 57 UNLABELLED (55 BugsInPy units + 2 QuixBugs) and 6 SUSPECT_LABEL are excluded in all analysis; the 9 NOT_DRIVEN are counted as abstention as pre-registered (`verdict` empty for B1 on 9 rows, none inside the 258 denominators). Exclusions are as pre-registered.
- Cluster dominance (one QuixBugs project holds 113 of 258 eligible pairs) is stated; the FA test is unaffected, the abstention CI [0.353, 0.524] is cluster-dependent.
- Protocol deviations (killed legacy pytest, test-guard abort, E6 repeat, suspend artefact) are disclosed in section 9 of the consolidated analysis and `setup.tex`.
- E1: the weak "SUPPORTED" is stated with 1 vs 2 pairs and confounding; no overstatement found.
- Reproducibility: README/guide commands I ran (`check_docs_v7b.py`, `make -n verify-docs-v7b`, `--help` on 6 scripts, `analyze_results.py` into scratch, `sbgv7 compare/verify`) work as written except m-6. I did not re-run E1, E3-E7 (hours, load sensitive, out of scope).
- Manuscript is explicitly "not compiled"; I could not verify compilation (no LaTeX toolchain checked); `check_manuscript.py` only checks cites/labels/numbers.

## Remaining blockers before independent validation

None blocking. Required before validation: fix M-1 to M-3 wording and the missing SP-2 sensitivity (or disclose its omission); reconcile README (m-4). Recommended design change for the validator: add a coverage-gated B1 and a matched-abstention null, and hold out labels that are not generator-derived.

## Could not verify

E1/E3 re-execution; LaTeX compilation; external literature (DiffKemp DOI, 2026 preprint contents); 84 witness-id-change pairs and 320/321 strict key; per-run RSS; whether hostile env vars were stripped inside the child (only that results were identical).
