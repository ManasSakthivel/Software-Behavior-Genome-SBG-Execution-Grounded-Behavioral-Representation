Reconciled version R1 of SBG_V7_RISK_REGISTER.md; original preserved at reports/v7_design/_original_archive/

# SBG V7 Risk Register, R1

Authority: `reports/final/V7B_FROZEN_SPEC.md` (gates s12) > `P0_BINDING_DECISIONS.md`. **IDs R01-R38 are kept unchanged**; new risks R39-R54 are appended. Risk IDs are `Rnn`; requirement IDs in the failure-to-requirement matrix are `R-nn` (CM G-03: the proposed `RK-nn` rename was not applied, to keep IDs stable). L = likelihood, I = impact (L/M/H), as in the original; Phase 1 does not change any L/I value except where stated, and no L/I was re-estimated from data. Roles are roles, not persons: PI, STAT, ENG-CAP, ENG-AN, ENG-BM, SEC, ADJ, CUST.

Gate references: the original used ROADMAP G0-G9. R1 uses G0-G8 only (CM G-01); G9 (optional prediction/formal tier) becomes "G-J" (the optional-layer gate in GATES R1). The "Monitored by" mapping in section 1 is a proposed re-mapping by topic against the GATES R1 headings (G1 substrate, G2 exploration, G3 alignment/divergence, G4 evidence/decision, G5 integrated dev, G6 freeze, G7 sealed eval, G8 reporting); it was not reviewed by an owner.

## 1. Original risks R01-R38: R1 status

Status vocabulary: Open (unchanged), Re-scoped (changed by a binding decision), Elevated (Phase 1 evidence), Partly mitigated, Out of core. "Evidence" cites reports, not new measurements.

| ID | Category | Risk (short; full text in archive) | L | I | R1 status and update | Monitored by (R1) |
|---|---|---|---|---|---|---|
| R01 | Scientific | Core thesis collapses: V7 reduces to differential testing plus coverage | H | H | **Elevated.** Red team: B1+rep differs from B1 on 2 of 311 pairs and tracks V7-B on detection; K4 not evaluated. Fallback now defined: V7-B' then STOP if no better than B1 (D9). "Internal-state" part of the thesis is out of scope (D2) | K4, G3, G5 |
| R02 | Technical/Scientific | Exploration cannot raise real-world activation | H | H | Open. No explorer exists; dev census is indicative only (K2 not evaluated as defined) | K2, K3, G2 |
| R03 | Scientific | S-levels uncalibrated; high S gives false assurance | M | H | **Elevated.** S1/S2 thresholds UNVALIDATED; S3 disabled; sufficiency did not separate synthetic labels (25% vs 32% changed); see R39-R41 | G4, G8 |
| R04 | Scientific | Internal-only divergence dominated by benign refactors | H | M | **Re-scoped.** Not a verdict (D2); annotation only if E is on; pilot-only | pilot |
| R05 | Data/Label | Synthetic suites circular | M | H | Open; development synthetic labels are unadjudicated (2 mislabelled cases found) | G3, K5 |
| R06 | Data/Label | Too few real masked-divergence cases | H | H | Open; masked stratum is a pilot diagnostic now (D2); real-pair count: see R47 | K1, K5 |
| R07 | Data/Label | Label noise; "behaviour" ambiguity | H | H | Open; no adjudication exists | G7, K5, G8 |
| R08 | Team/Time | Adjudication cost overruns | H | M | Open; effort not re-estimated (CM E-01) | K5 |
| R09 | Technical | Nondeterminism uncontrolled | H | M | Open; distributional regressions out of scope and reported as abstentions (P0 reconciliation report resolution row 27); entropy virtualisation partial (R46) | K2, G1 |
| R10 | Technical | Tracer overhead / PEP 669 edge cases | M | M | Partly mitigated: as-built capture is `sys.monitoring`-based; differential check against a `settrace` oracle and overhead on target platform not verified | G1 |
| R11 | Safety | Sandbox escape / host compromise | M | H | **Elevated.** macOS-only, reads unconfined, `setsid` escape untested, `RLIMIT_AS`/`NPROC` not enforced; see R43-R45 | G1 (hard gate) |
| R12 | Safety/Infra | Developers run untrusted code natively | M | H | Open; policy: third-party repositories run only under Linux container isolation (FS s10); macOS records carry `policy_below_minimum=true` | G1 |
| R13 | Safety/Infra | Supply chain in environment builds | M | H | Open; no external repository built (Phase 3, not started) | G0b/G1, K1 |
| R14 | Technical | Alignment fails on heavy refactors | M | M | Open; G not built; alignment never gates the verdict value | G3 |
| R15 | Technical | Python dynamism defeats static context | M | M | Open; unsupported-construct counters not implemented | G2 |
| R16 | Scientific | Unrealistic generated inputs | M | H | Open; no generator exists (inputs user-supplied JSON) | G4, G8 |
| R17 | Scientific | State abstraction tuned to flatter thesis | M | M | Out of core (E optional) | pilot |
| R18 | Sci./Team | Holdout disappointment, retuning | M | H | Open; no holdout exists | G8 |
| R19 | Scientific | Optional prediction layer repeats V6 | H | L | Out of core (J off) | G-J |
| R20 | Reproducibility | Environment drift dev vs holdout | M | M | Open; single machine, cross-machine reproduction not verified | G1, G8 |
| R21 | Scientific | Formal tier too narrow | H | L | Out of core; separate formal claim only | G-J |
| R22 | Scope creep | Over-engineered schema/store | M | M | Partly mitigated (JSONL + hash chain used); schema R1 adds entities not built | G0 |
| R23 | Reproducibility | Schema churn invalidates evidence | M | M | Open; add-only/MINOR rules in schema R1 | G1, G3 |
| R24 | Scope creep | Expansion to P5/P6/P9/Java/C before thesis | H | H | Partly mitigated: E, J, explorer, impact not built | K4, G8 |
| R25 | Sci./Comm. | Over-claiming | M | H | Partly mitigated: `scripts/check_docs_v7b.py` lints README claims; claims matrix exists; reviewer-style list of claims not to make in the red-team review; README still carries V5/V6-era claims on the same page (R49) | G6, G8 |
| R26 | Novelty | Substantial overlap with existing work | H | H | **Materialised in part.** Novelty assessment: C1-C4 partially novel, C5 unsupported; closest 2024-26 tools not run as baselines (R48) | G0, K4, G8 |
| R27 | Leakage | Public-bug leakage | M | H | Open; all existing data burned or developer-owned | K5, G7 |
| R28 | Leakage | Dev/holdout contamination via design reuse | M | H | Open; V7-B was shaped on development data (readiness report) | G7, K5 |
| R29 | Team/Time | Key-person dependency | M | H | Open | every gate |
| R30 | Scientific | Forking paths, p-hacking | H | M | Open; exploratory analyses labelled; Holm over {H2a,H2b,H4} for confirmatory | G0, G5, G8 |
| R31 | Scientific | Insufficient power | M | H | **Elevated.** P0 power: 63% at +10pp for 40 projects, 22% at +5pp; K5 floor 60 projects / 250 divergent pairs not approached | K5 |
| R32 | Reproducibility | Non-hermetic exploration | M | M | Open; no explorer; seed policy specified, not implemented (OI-07) | G4, G8 |
| R33 | Infrastructure | Storage/compute blow-up | M | M | Open; ESA shows bounds fail at default scale; raw dev results ~150 MB uncompressed in tree (pack 48.61 MiB); see R53 | G1, G8 |
| R34 | Scope/Claims | Java/C claims leak in | M | M | Open | G8 |
| R35 | Scientific | Strawman baselines | M | H | **Materialised in part**; see R50 | G3, G8 |
| R36 | Data/Label | Selection bias of runnable/deterministic filter | H | M | Open; funnel reporting required; dev 9 class units not driven | K1, K2, G8 |
| R37 | Scientific | Metric gaming through abstention | M | M | **Elevated.** INSUFFICIENT dominated by engine gaps (renames 49, generators, class units 8); not honest-abstention evidence (R42) | G3, G8 |
| R38 | Infrastructure | Real-project environment builds fail at scale | H | M | Open; Phase 3 | K1 |

Role/owner, early indicator, mitigation and fallback columns of the original are unchanged except where the Phase 1 or D1-D11 changes above alter them; the full text is in the archive. Changed fallbacks: R01 fallback is V7-B' (D9); R04 fallback is the annotation-only status; R03 fallback "collapse to a binary activated flag" remains available.

## 2. New risks R39-R54 (from the red team, isolation audit, power analysis and Phase 1)

| ID | Category | Risk | L | I | Early indicator | Mitigation | Fallback | Owner | Monitored by | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| R39 | Scientific | Sufficiency adds no measurable value over repeated plain differential testing (B1+rep) | H | H | K4 paired FAR difference lower bound <= 0; S-levels do not separate labels | Pre-declared K4 test on independent data; B1+rep as the null model | V7-B' then STOP if no better than B1 (D9) | STAT | K4 | red team B-2, M-1 |
| R40 | Scientific | S1/S2 floors are weak: S2 reachable from 2 inputs (no F4 floor); `s2_all_channels_instrumented` hard-coded True; branch denominator treats all directions reachable | H | M | S2 verdicts with very few inputs; conformance audit finds the hard-coded flag | Conformance audit (OI-01, OI-02, OI-17); any floor change only via the development split | Report S-level with factor vector and `n` inputs; never present S2 as a quality grade | ENG-AN | G4 | red team M-2, Mi-3 |
| R41 | Scientific | `NO_DIVERGENCE_OBSERVED` issued on pairs that are real fixes (16 of 46 driven BugsInPy units; 15 at S2, on synthetic battery inputs) | H | H | Real-fix pairs receiving NDO; FAR on independent pairs | Wording rule: states only explored inputs and `H`; adjudicated FAR evaluation | Treat NDO as non-assurance in all reports | PI | K4, G8 | red team M-3 |
| R42 | Scientific | INSUFFICIENT rate driven by unimplemented engine features (renames, generators, class units) read as "honest abstention"; spec reason codes never produced (`ambiguous_entry`, `unmodelled_change`, `unsafe_program` except tamper, `blind_spot_dominant`) | H | M | Share of INSUFFICIENT explained by engine gaps | Report abstention by cause; implement or declare unsupported; audit OI-06, OI-15 | Do not use INSUFFICIENT rate as evidence of calibration | ENG-AN | G4, G8 | red team M-5, s5 |
| R43 | Safety | Isolation below spec minimum: macOS `sandbox-exec` only (deprecated by Apple), `RLIMIT_AS`/`NPROC` not enforced (soft RSS watchdog), reads unconfined, `setsid` escape untested | H | H | Any hostile fixture succeeds; every record `policy_below_minimum=true` | Linux container isolation with I1-I7 checks (Phase 3, not started); macOS runs only synthetic/benchmark | Halt external-code execution (S4) | SEC | G1 (hard gate) | isolation audit; red team M-6 |
| R44 | Infrastructure | Docker/Linux container path untested (daemon down in P0 and Phase 1) so K2 and K1 cannot be evaluated as defined | H | H | No I1-I7 pass record on Linux | Obtain a Linux container host; run I1-I7 first (FS s13) | Stay at synthetic/benchmark-only claims | ENG-CAP | G1, K2 | FS s13; EXECUTION_LOG |
| R45 | Technical | Capture bypass: `os.write(1)` and subprocess output evade stdout capture; tamper detection is a post-run check of monitoring state | M | M | Programs writing via fd or subprocess give differing observed output between runs | Container-level capture; tamper flag blocks S1 | Declare channel uninstrumentable (drop to intersection) | ENG-CAP | G1 | red team Mo-6; V7B_IMPLEMENTATION |
| R46 | Technical | Control alternation (`k_alt`) virtualises only `random.seed` and `time`; uuid, `os.urandom`, env not virtualised, so `ENV_SENSITIVE` detection is partial and flaky differences may be called confirmed | M | M | Witnesses that fail under un-virtualised entropy | Extend virtualisation before any real-project run; audit OI-12 | Report as known limit | ENG-CAP | G1 | red team Mo-4 |
| R47 | Data/Label | No independent benchmark: all data burned or developer-owned; K1 not met on dev data; K5 far; independence audit declares nothing pristine | H | H | Phase 3 mining campaign not started | Mining with Linux isolation, project-disjoint, custodian, kappa-checked truth team | Exploratory report only (K5 DOWNGRADE) | ENG-BM | K1, K5 | red team B-3, s7; readiness |
| R48 | Novelty/Overlap | Published and 2024-26 LLM differential-testing tools (Testora, DiffTestGen, Mokav, Cleverest, DiffSpec, DiffKemp, Shadow SE) not compared; reviewers can reject competitive claims | H | H | Reviewer asks "how is this not X" with no data | Run at least one external baseline or drop competitive claims | Position as design/feasibility with evidence contract | PI | G8 | red team s2, M-4; novelty assessment |
| R49 | Scientific/Comm. | Legacy V5/V6 claims (README AUROC 0.897, "Supported" rows) and stale numbers (isolation audit "11 passed" vs later counts; B3 CPU 1407 vs 1424 s; tests 74 vs 75 passed across reports) conflated with V7-B | M | M | Docs check finds mixed claims | Keep `docs/README_pre_v7b.md` separation; extend `check_docs_v7b.py`; number audit | Dated errata | STAT | G6, G8 | red team Mi-1, Mi-2 |
| R50 | Scientific | Baseline fairness: B3 is a minimal mutation loop, B2 covers QuixBugs only, B5 is a lookup of V6 scores on different inputs, B4/B5 thresholds fitted on development material, diff-information parity audit absent, V7 parent-CPU overhead unmeasured | M | H | Baseline activation well below V7 on the same pairs | Like-for-like rule (D7, D11); freeze baselines before V7 numbers on independent data | Report both strengthened and original | STAT | G3, G8 | red team M-4, Mo-5 |
| R51 | Process | Reconciled-document debt and spec/doc drift: the R1 set (closing O13) may still disagree with the frozen spec or the as-built code; three phase vocabularies; EP s3.2, 4, 5, 6 and the 14-row matrix were not checked line by line | M | M | Index "unreconciled" list non-empty; audit finds new disagreements | Index and conformance audit; frozen spec wins on any conflict | Amend by dated changelog | PI | G0 | P0 report s4, O13 |
| R52 | Safety/Process | Accidental execution of full workloads through scripts without safe `--help` (incident in Phase 1: probing `--help` overwrote 209 tracked result files; restored) | M | M | Any script lacking arg parsing run for help | Fixed for `experiments/v7b/k1_spike.py` and `sbgv7.baselines.run` in commit 1206312e with regression tests; audit other scripts for default output into committed paths | Restore from committed version; do not commit unverified output | ENG-BM | G1 | PHASE_1_FINAL_CLOSURE_REPORT s4 |
| R53 | Infrastructure | Repository bloat: raw result files committed (about 160 MB uncompressed; pack 48.61 MiB); history untouched by decision | M | L | Pack growth; per-file size > 5 MB | LFS or external archive with sha256 manifest; per-file size guard (recommended, not applied) | Leave history untouched | ENG-CAP | G8 | PHASE_1_FINAL_CLOSURE_REPORT s2 |
| R54 | Technical | Input representation limits: JSON-only inputs (no tuples, sets, objects), entry must be a top-level function, no declared renames, generators run no body, 8 class units not driven; replay+crude activation may stay below the K2 35% floor | H | H | K2 activation below 35% on real projects | Published supported-type set; spike measurement (O7) | K2 fail triggers one redesign of B, then STOP | ENG-AN | K2 | O7; red team Q12 recap, s9 |

## 3. Strongest arguments against (original; kept, with updates)

Original arguments 1-7 stand as written (differential testing in new clothes; observation not representation is the binding constraint; scarce noisy ground truth; thin novelty; cost vs benefit; three-valued verdicts shifting the burden to many INSUFFICIENT outputs; cost of untrusted execution). Updates: arguments 1 and 4 are now supported by the Phase 1 red-team data (B1+rep, R39); argument 6 is partly realised (INSUFFICIENT about 36-44% on development arms, mostly from engine gaps, R42). Responses that would change the assessment: K4 shows a measured FAR gain at equal budget on independent data; K3 shows an activation uplift; K1/K5 show an adequate real stratum.

## 4. Stop and cut-back conditions (reconciled to D9 and FS s12)

STOP (publish the negative result and the observation-layer artefacts): K1 fails; K2 fails twice (one redesign of B allowed); V7-B' no better than B1 at K4; S4 any unresolved sandbox escape after one remediation cycle or inability to run untrusted code under policy; S5 two consecutive gate slips of more than 4 weeks each with no PI-accepted scope reduction, or loss of benchmark/adjudication capacity before K5; S6 unrepairable leakage in the sealed holdout (do not unseal; rebuild). PIVOT: K3 fail (replay plus structure-aware exploration, no directed-exploration claim); K4 fail (V7-B'). K5 fail: no confirmatory evaluation (DOWNGRADE). Superseded from the original: S1's "K1 < 60 AND no distinct controlled-suite claim" conjunction and the 60-99 "exploratory" band (D9 fixes the K1 response at STOP); S2's "K2 and K3 both fail" (K2 twice); S3's "K4 fails twice and R03 uninformative" (K4 then V7-B'). Cut back (drop P5/P6/P9 workstreams) if K4 passes only marginally or the budget or calendar exceeds the 90th-percentile estimate; the 48-week figure is unreconciled (effort not re-estimated). Whether the existing "K1 NOT MET on development data" statement already triggers STOP is an open programme decision (OI-21).

## 5. Early-warning dashboard

As the original, plus: containment escapes (must be 0), share of INSUFFICIENT by cause, number of real-fix pairs with NDO, `policy_below_minimum` share of records, and open conformance items.
