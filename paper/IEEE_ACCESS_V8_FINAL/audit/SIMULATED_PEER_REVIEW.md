# Simulated Peer Review: IEEE Access submission

**Manuscript:** "When Is an Empty Difference Set Reassuring? Evidence-Conditioned False-Assurance Risk for No-Divergence Verdicts in Differential Regression Analysis" (SBG V8)
**Reviewer stance:** independent, skeptical, red-team. No manuscript file was edited.
**Date:** 2026-11-20

---

## 0. Summary of the submission

The paper defines a false-assurance risk R = P(F=1 | NDO) for no-divergence verdicts from differential testing. It proposes an evidence profile and a sign-constrained logistic calibrator (CEC), an "Evidence Response Signature" (ERS) of 8 properties tested by 9 post-hoc evidence perturbations, and a sealed evidence-collection pipeline with an adversarial evaluation.

On 312 development pairs (258 labelled) the predictive hypotheses are not supported: the H2 contrast is +1.6 pp with CI [-6.6, +16.3], and the sign is unstable across seeds. ERS works as a conformance test: it found one profile defect. The security evaluation is mixed: it distinguishes detection from prevention, and one attack channel (SENSE04b) remains open.

The paper reports its weaknesses unusually candidly. Its main problems are an empirical base too thin for a journal contribution and a few remaining text/code mismatches.

---

## 1. Numerical verification

### 1.1 Recomputed from `datasets/v8/dev_records.jsonl` (this review)

| Claim (location) | Recomputed | Status |
|---|---|---|
| 312 pairs, 1,976 inputs, all rc=0 (design.tex:37) | 312; 1,976; rc=0 for all 312 | OK |
| Outcome mix (audit) SAME 1863 / CONFIRMED_DIFF 84 / LIMIT_ASYM 22 / NO_RUN 6 / QUARANTINED 1 | identical | OK |
| 258 labelled; 106 Y=1; 152 Y=0; 54 unlabelled (tab_corpus) | 258 / 106 / 152 / 54 | OK |
| Synthetic 150 / 101 clusters / 77 / 68 / 5 | identical | OK |
| QuixBugs 31: 29 / 0 / 2; neg 85: 0 / 84 / 1; one shared cluster | identical (`project = quixbugs` for both arms) | OK |
| BugsInPy-derived 46, 12 clusters, unlabelled | 46, 12, all `y = None` | OK |
| 114 clusters total; 101 labelled projects (tab_ablation footnote) | 114; 101 (100 synthetic + 1 QuixBugs) | OK, but "101 projects" next to a corpus table showing 101 synthetic clusters is easy to misread (see 1.3) |
| QuixBugs = 43.8% of labelled (design.tex:39) | 113/258 = 0.438 | OK |
| V7-B DIV 84 (tab_corpus total) | 84 | OK |
| V7-B NDO 61 labelled, 13 misses, all synthetic (37 (13) + 24 (0)) | 61, 13; synthetic 37/13, quixbugs_neg 24/0 | OK |
| B3 NDO in 34 projects (power) | 34 | OK |
| B1: 183 NDO, coverage 0.709, 31 FA, R 0.169 | 183, 0.7093, 31, 0.1694 | OK |
| ERS P6 applicable 228; P8 recorded-replay fails 155; recomputed fails 84 | 228 records without a witness; 84 DIV + 71 NDO = 155 stored non-INS verdicts; 84 witnessed | OK |
| c* = 61/258 = 0.236; matched risks 0.213 = 13/61, 0.230 ≈ 14/61; difference 1/61 = 1.6 pp | consistent | OK |
| 0.213 − 0.169 = 4.4 pp vs random abstention | consistent | OK |
| "a third of the coverage" (abstract) | 0.236/0.709 = 0.333 | OK |
| ICC 0.61, DE 1.48, n_eff ≈ 41 | m̄ = 61/34 = 1.79; 1 + 0.79·0.61 = 1.48; 61/1.48 = 41.2 | OK |
| 460–1,160 verdicts = "roughly 8 to 19 times" | 7.5×–19.0× | OK ("roughly 8" acceptable) |
| Seeds +1.6, +1.6, +3.3, −4.1, −4.9, mean −0.5 | mean −0.50 | OK |
| H1a +0.003, H3 +0.030 | table: 0.649 − 0.645 = 0.004 (rounding of unrounded values), 0.645 − 0.615 = 0.030 | OK (audit 2c gives +0.003) |
| P2 probe 109/227 failures; Δ up to 0.32 | posthoc_matrix: 118 pass / 109 fail; Δ min −0.318 | OK |
| Fitted model responses 9/16, 68/93, 100/176 | posthoc_matrix `model` | OK |
| Security: 15 = 3+9+1+2; 19 = 3+14+1+1; 25 = 3+15+5+2; Linux 74 = 8+1+65 | arithmetic OK; the 25 matches SECURITY audit line 163 (27 minus 2 controls; no-effect 7 − 2 = 5) | OK |
| 247 passed / 8 skipped / 2 xfail (repro.tex:4) | ARCHITECTURE_AND_DEFINITIONS.md:5 | OK |
| Profile-fix effects (0.624 → 0.620; +3.3 → 0.0; ≤ 0.008) | STATISTICAL_AUDIT §3.5 (0.057 → 0.065 = 0.008) | OK (mac branch only) |
| Placebo 5/6, p 0.01–0.03, 0.21 | traceable only to mac-branch `ers_placebo_v8.{0,1}.json` via NUMERICAL_CLAIM_AUDIT.md:48; not in `stats_summary.json` | Traceable, off-branch |
| Frozen thresholds 0.24–0.50 | mac branch only (STAT audit §6) | Traceable, off-branch |

### 1.2 Wrong or inconsistent numbers

1. **BugsInPy count conflict.** `background.tex:93` (Table tab:benchmarks) says "55 extracted unit pairs (development)". The corpus has **46** BugsInPy-derived pairs (introduction.tex:18, tab_corpus, threats.tex:7, recomputed). The 55 comes from `DEV_MANIFEST.jsonl` (DATASET_VERIFICATION_REPORT.md:83). The manifest has 321 rows but only 312 records exist, so 9 pairs dropped out silently and the paper never explains this.
2. **Abstract length.** `sections/abstract.tex` is 256 words including LaTeX markup. The IEEE Access limit is 250 words.
3. **"54 unresolved"** (tab_ablation footnote) reuses the estimand term "unresolved" (problem.tex:38, adjudication outcome) for pairs that are simply *unlabelled*. Elsewhere the paper says "unlabelled".
4. **"258 with generator labels"** (tab_ablation footnote). QuixBugs labels are test-based, not generator labels (problem.tex:51).
5. **ERS P6 expected response is misstated.** `ers.tex` Table tab:perturb (line 47) and ers.tex:22/27 say P6 requires "verdict = DIV" and that Properties 5 and 7 "prescribe an exact outcome". The code, `sbgv8/ers.py` `_eval`, passes P6 when `v1 == DIV or d > 0 or v1 == INS`. As a result, 157 of 228 P6 "passes" for the V7-B recorded replay rest entirely on abstention credit (posthoc_matrix.md, `b3` row: "passes resting on abstention credit 157"). The table reports those 157 as passes, so P6 is weaker than the paper states.

### 1.3 Ambiguous or untraceable

- tab_corpus: the "NDO (miss)" column shows "--" for BugsInPy and 37 for Synthetic. V7-B actually issued NDO on 8 BugsInPy and 39 synthetic records (2 of them unlabelled), 71 in total. The caption says the column counts labelled pairs only, but the 71 matters because the P6/P8 failure counts (71, 155) are computed over all 312 records. Add the all-record NDO count.
- ers.tex:63: "Real-execution analogues exist for P2, P5 and P6 in a separate experiment (30 development pairs, few applicable)." STATISTICAL_AUDIT says the real-execution ERS claims are **report-only, with no raw files** on the Linux branch. Either cite the raw files or drop the sentence.
- reproducibility.tex:4: "A claim–evidence register maps every numerical statement". Name the file (`NUMERICAL_CLAIM_AUDIT.md`).
- threats.tex:13 / reproducibility.tex:11: "Every number in this paper was recomputed from raw records". The placebo, frozen-threshold and profile-fix numbers come from a different branch (`research/v8-mac-hardening`, b9b8a86c / 8e28f601), not from the declared replication branch (repro.tex:4). Say so.
- tab_ablation: the Runtime column is "--" in every row. Remove it.
- tab_ablation: rule baselines B1–B6 sit under the "Soft blockers (v8.0): 85 eligible" sub-header, but they do not depend on the policy. Move them to a separate "Rule baselines (all 258)" block.
- main.log: `Overfull \hbox (505.12pt too wide) has occurred while \output is active` (twice). Check the page where this occurs, probably a `table*` footnote parbox or the header.

---

## 2. Overclaims, ambiguous statements and citation misuse

### 2.1 Overclaims / unsupported statements (file:line)

| # | Location | Problem |
|---|---|---|
| O1 | introduction.tex:15 | "Evidence is captured **outside the program under test**, re-observed in a shadow run and sealed". The stdout tee is an in-process stub (trust.tex:19: "the tee shares the evaluated process's address space"). Shadow re-observation is optional and does not change the verdict (trust.tex:23). Only line/branch capture and frame checking are parent-side. |
| O2 | discussion.tex:4 | "What does transfer is the observation that the rate is neither negligible nor reduced …". This contradicts threats.tex:7 ("Nothing in this paper supports generalisation …") and the preceding sentence ("magnitude does not transfer"). It is a generalisation claim. |
| O3 | discussion.tex:6 and results.tex:20 | "full CEC at the same coverage was **worse than** random abstention" / "4.4 points worse". B6 is an expectation with no interval, and the B8-vs-B6 contrast is not significant. This exaggerates a negative result in the same way the paper rightly avoids exaggerating positives. |
| O4 | discussion.tex:6 | "We think this methodological point generalises beyond SBG". The opinion is acceptable, but it should be framed as a recommendation, not a finding. |
| O5 | conclusion.tex:5 and abstract | "prevents … post-hoc tampering by parties without the anchor key". Mechanically these attacks are detected and the verdict is forced to INS (fail-safe). A17 shows such forcing can deny a true divergence. "Prevents a false verdict (fail-safe abstention)" is accurate; "prevents tampering" is not. |
| O6 | abstract; conclusion.tex:5 | The security summary omits that **evidence substitution (A3/P06) is detection-only** (results.tex:74,78). Only in-process forgery is mentioned. |
| O7 | conclusion.tex:7 | "establishes the false-assurance estimand … as usable instruments". An estimand is defined, not established by data, and the estimand has never been measured (no adjudication). |
| O8 | introduction.tex:18 / results.tex:63 | "separates the SBG trust gate from its predecessor". The P8 pass for SBG is tautological: P8 sets `integrity_ok = 0`, and the trust gate is the one-line rule `if not integrity_ok: INS`, added *after* the matrix revealed the failure (results.tex:63). The "recorded" V7-B column replays a stored verdict and cannot respond by construction, which makes it a strawman. This is disclosed, but it is still presented as evidence the protocol "discriminates between decision rules" (C3). |
| O9 | problem.tex:37 | "the measured R is a lower bound on the rate …". This holds only if adjudication has no false-positive divergences and only for the same issued set. State the assumption. |
| O10 | discussion.tex:16 | "Multiplicity … was the one feature that fitted models **consistently** retained". The only evidence is seed-0 and the ERS fitted model (results.tex:61, tab_ers footnote). No coefficient table across seeds or folds is reported. |
| O11 | design.tex:84 / results.tex:20 | "None of the eight contrasts reaches unadjusted significance at 0.05". The p-values are **one-sided** bootstrap p (`stats.boot_p_one_sided`), but the paper never says so, and the power analysis uses two-sided α = 0.05. State the sidedness. |
| O12 | results.tex:76, tab_security, threats.tex:11 | "Container probes". The paper itself states that no container runtime is invoked (trust.tex:15), so the label invites a Podman/container-isolation reading. Rename them "isolation probes". |

**Checked and found acceptable:**
- **Equivalence:** repeatedly disclaimed (problem.tex:15, 37; abstract).
- **Adjudication:** consistently marked "implemented, not executed" (tab:stages, intro:30, repro).
- **Causal language about perturbations:** ers.tex:62–63 and threats.tex:3 explicitly disclaim it. No causal verbs found in results.
- **ERS predictive advantage:** correctly not claimed. The placebo is framed as weak and unadjusted.
- **Generalisation:** correctly disclaimed in intro:30 and threats.tex:7, except O2.
- **Podman:** the only mention is the disclosure at repro.tex:11.

### 2.2 Citation checks against LITERATURE_COMPARISON_REGISTER.md

| Location | Citation | Issue |
|---|---|---|
| introduction.tex:3 | `mckeeman1998differential` cited for "running an old and a new version … to check a change" | Register: must NOT be cited for version-pair regression analysis (its setting is multiple implementations). Keep only `evans2007differential` there, or reword to "comparing implementations or versions". |
| background.tex:39 (tab:capability) | `just2014mutants` "Y" for "Evaluates empty difference sets" | The study concerns mutant/real-fault coupling, not empty difference sets. Downgrade to P and cite `jia2011analysis`. |
| background.tex:39 | `inozemtseva2014coverage` P for "Evaluates empty difference sets" | Stretch: it evaluates coverage–effectiveness correlation. |
| background.tex:40–41 | `papadakis2019mutation` for "Explicit false-assurance estimand (P)" and "Evidence diversity (P)" | Register: the survey's specific findings were not read. Do not attribute specific capabilities. |
| background.tex:45 | `inozemtseva2014coverage`, `papadakis2018mutation`, `schuler2011assessing` P for "Matched-coverage risk comparison" | None compares selective risk at matched coverage. Inozemtseva controls for suite size, and Papadakis 2018 is about mutant subsumption inflating scores. Use "--" or N. |
| background.tex:46 | `palikareva2016shadow` P and `torresarias2019intoto` P for "Abstention-aware verdicts" | Register: palikareva must not be cited for calibrating no-divergence verdicts. In-toto does not abstain; it fails verification. Use N. |
| background.tex:63 (tab:method) | `kuchta2018shadow` with "CoREBench patches (C)" | Register: details not read, do not attribute specific results. Attribute the evaluation to `palikareva2016shadow` only. |
| background.tex:23, tab | `slsa2023spec` | Register: v1.0 is retired (v1.2 current). Update or note the version. |
| background, intro | Six 2026 preprints (`hu2026difftestgen`, `lecong2026patchguru`, `fu2026orion`, `paul2026beyond`, `ayub2026semadiff`, plus `durieux2019critical`) | Acceptable as preprints. SemaDiff is the closest work and is correctly labelled a preprint in tab:method; label it so in the text (intro:7, background:8) too. |

**Correct uses:**
- `schuler2011assessing` is credited as the precursor of P1, as the register requires.
- `angelopoulos2024conformal` / `bates2021distribution` carry the exchangeability caveat.
- `evans2007differential` is used for the ambiguity premise.
- `durieux2019critical` is paired with `tomassi2019note`.

---

## 3. Denominators, matched coverage and statistical methodology

**Denominators.**
- Coverage and risk use 258 labelled pairs throughout, consistently.
- The eligible pools are 85 under soft (24 Y=1, 54 projects) and 61 under strict.
- The fractional tie-breaking in `stats.matched_risk` matches the description (design.tex:81). Ranking within the outer fold matches `evaluate.py:68`.

**Matched coverage.**
- The logic is sound and transductive, and the paper says so.
- Under strict policy the ceiling equals c*, so the comparison is degenerate. The paper correctly reports point estimates only, and the 50.2% valid-resample artifact is disclosed.
- **Weakness:** c* was chosen as V7-B's coverage. A single operating point on an 85-pair pool is fragile. Report risk at 2–3 additional coverages, or the area under the risk–coverage curve with a cluster CI. `stats_summary.json` likely already contains the curves.

**Methodology vs code (`sbgv8/calibrate.py`, `stats.py`, `evaluate.py`).**
- λ grid {0.3, 1, 3, 10} by inner 3-fold log loss: matches `LAMBDA_GRID`, `fit_select`.
- Sign constraints as L-BFGS-B box bounds (all −1 except `lossy_frac` +1); ERS features free: matches `RISK_SIGN`.
- Outer 5-fold project-grouped CV: matches `outer_k=5`, `project_folds`.
- Threshold rule (one-sided 95% project-cluster bootstrap upper bound): matches `select_threshold`. The bootstrap size inside threshold selection is 500 (`fit_B=500`) or 1,000 (default), not 10,000; the paper does not state it.
- The pre-registered primary Holm family {vs B7, vs B3, vs B6} matches `evaluate.py:192-194`. The paper does not report this family's own Holm p-values; it reports the wider 8-contrast family instead (smallest 0.68 soft). STAT audit §2d gives primary-family Holm p ≥ 0.46 in all soft seeds and min 0.058 under strict seed 2, the latter a boundary artifact. Report the pre-registered family's result explicitly, since it is the pre-registered analysis.
- P-values are one-sided (`boot_p_one_sided`). See O11.
- Bootstrap: B = 10,000 percentile with the audit's own RNG stream. OK.
- Power: crude McNemar normal approximation with a cluster-inflated design effect. The paper states the assumptions adequately; call it approximate.

**Negative results.**
- Stated accurately and prominently: H2, H1a and H3 are not supported, no risk control, B3 is not better than B1, deployable thresholds issue zero NDO.
- One omission: STAT audit §2d records that under strict policy seed 2 the ERS log-loss CI excludes 0. The paper reports only "all five soft-policy seeds" (results.tex:45). Add the strict count (1/5) for completeness.
- Worst-case risks counting unlabelled NDO as FA (B1 0.333, B3 0.324, B4 0.225, B5 0.227) are available but unreported. problem.tex:38 promises worst-case reporting for unresolved cases. These pairs are unlabelled rather than adjudication-unresolved, but reporting them would be consistent with the stated philosophy.

---

## 4. Scores (1–10)

| Criterion | Score | Rationale |
|---|---|---|
| Novelty | 6 | Combining selective risk, evidence perturbation and integrity for NDO verdicts is new. The ingredients are not new, and the paper says so. |
| Technical contribution | 5 | Clean estimand and protocol. The calibrator effectively uses one feature. The predictive component did not work, and three profile features are constant. |
| Literature coverage | 7 | Broad and current, with careful positioning. Some capability-table cells over-attribute (Section 2.2). |
| Experimental design | 4 | Pre-registration and matched coverage are good. However: design-exposed data, construction labels, shared inputs between label and evidence in QuixBugs, one cluster holding 43.8%, real-project pairs unlabelled, a single c*, and post-hoc fixes made on the same data. |
| Statistical validity | 6 | Honest and conservative: cluster bootstrap, Holm, power analysis. Weaknesses: sidedness unstated, primary-family result not reported, single operating point, n = 61. |
| Benchmark breadth | 2 | Small synthetic Python functions plus QuixBugs; no labelled real-project data; no external corpus. |
| Reproducibility | 6 | Scripts, raw records and a claim register exist. Several numbers live on another branch, raw run directories are absent from the worktree, and Linux security metadata is missing. |
| Writing quality | 8 | Clear, precise and self-critical. Abstract slightly over length. |
| Figure/table quality | 6 | Informative. Empty Runtime column, rule baselines under the wrong sub-header, a P6 criterion mismatch in tab:perturb, and an overfull box in the log. Figures were not inspected visually in this review. |
| Overall publication readiness | 4 | Methodologically sound pilot. The contribution rests on a conformance protocol that found one defect, a "separation" partly built by construction, and a negative predictive result on design-exposed data. |

---

## 5. Three strongest contributions

1. **Matched-coverage evaluation with a random-abstention baseline.** It shows convincingly that a sufficiency gate (V7-B) abstained on three quarters of verdicts without lowering risk (0.213 vs 0.169). This is a transferable methodological lesson for any abstaining verifier.
2. **ERS as a label-free conformance test.** P2 caught a real profile defect (109/227) that aggregate metrics could not reveal, because the fitted model happened to ignore the affected features.
3. **A careful estimand definition and honest reporting.** The paper separates the selective-risk estimand from equivalence, handles unresolved adjudications explicitly, distinguishes detection from prevention in the security evaluation, and discloses an invalid internal artifact (the five-dataset cohort) and fabricated report figures.

## 6. Five most likely reviewer objections

1. **No validated empirical result.** All risks use construction labels on design-exposed data. The only labelled "real" arm (QuixBugs) has shared label/evidence inputs and no misses. The 46 real-project pairs are unlabelled. A journal reviewer will ask what is publishable beyond a protocol plus a null.
2. **The ERS evidence is thin and partly circular.** P8 is passed by a one-line rule added after the failure was observed. The "recorded" V7-B column cannot respond by construction. P6 accepts abstention, contrary to its stated criterion. P1 applies to only 16 records. Every perturbation is post-hoc and synthetic.
3. **The calibrator is degenerate.** It effectively uses one feature (`mu_min`), three gate features are constant, and the coverage-only model has an inverted slope (−1.83). So "CEC vs coverage-only" does not test the evidence-profile idea.
4. **Underpowered by design.** n = 61 NDO in 34 clusters, MDE ≈ 16 pp versus a 5 pp hypothesis. The study could not have answered its primary question. Why was it run and reported as such rather than scaled first?
5. **Security evaluation is narrow and platform-split.** Probes are author-written. Linux results lack metadata, 65/74 Linux probes never reached a decision, and no post-remediation Linux run exists. An open sensing channel (SENSE04b) remains, and substitution is detection-only.

## 7. Missing comparisons

- Risk at matched coverage for **B4/B5 rule gates vs CEC**. B4 reaches risk 0.121 at coverage 0.547, lower than every calibrated model at c*. Is a two-line coverage rule as good as or better than CEC? Report B4/B5 risk subsampled to c* (rank by activation/branch coverage) or CEC at c = 0.547 (not attainable under strict; possible under soft only up to 85/258 = 0.33, which should also be stated).
- **Mutation-based adequacy** (kill-rate of mutants of the changed region by the declared inputs) as a baseline estimator of NDO risk. It is the most obvious prior-art competitor and is discussed at length in Related Work but never run.
- **Checked coverage / dynamic dependence** in place of the reachability proxy (acknowledged as future work).
- **Test-generation augmentation** (e.g., Hypothesis or an LLM generator) to see whether more diverse inputs change B1 risk. This is the practical alternative to abstention.
- **AURC (area under the risk–coverage curve)** with cluster CIs across all coverages, instead of a single c*.

## 8. Statistical weaknesses (summary)

- One-sided bootstrap p-values used without saying so; the power analysis is two-sided.
- The pre-registered Holm family's results are not reported directly.
- Single matched operating point (c* = 0.236). AURC or multiple c* values are missing.
- Calibration slopes are reported with CIs spanning about 1.6 units: uninformative, as admitted.
- The B6 comparison is stated without uncertainty (O3).
- Seeds are fold replicates. This is correctly not pooled, but the seed range is used rhetorically ("sign unstable"). Fine as presented.
- The placebo test (100 permutations, min p ≈ 0.01) is unadjusted and on another branch.
- Design-exposed data plus two post-result method changes (integrity override, profile fix) mean every analysis is effectively exploratory. The paper says so, but the pre-registration framing (design.tex:86) can mislead readers into treating results as confirmatory.

## 9. Citation weaknesses (summary)

See Section 2.2: the McKeeman version-pair use, five over-attributed cells in tab:capability, Kuchta attribution, the retired SLSA version, and heavy reliance on 2026 preprints for the closest prior work.

---

## 10. Required revisions

### (a) Fixable now with existing evidence (exact text edits)

**E1. Benchmarks table count.** `sections/background.tex:93`
- Old: `BugsInPy~\cite{widyasari2020bugsinpy} & Python & 493 bugs, 17 projects & 55 extracted unit pairs (development) \\`
- New: `BugsInPy~\cite{widyasari2020bugsinpy} & Python & 493 bugs, 17 projects & 46 executed unit pairs, unlabelled (development) \\`
- Also add to `design.tex:37`, after "…function-level extractions from BugsInPy bugs~\cite{widyasari2020bugsinpy};": ` of the 55 extracted, 46 produced evidence records (the development manifest lists 321 candidate pairs, of which 312 were executed);` Verify the reason for the 9 dropped pairs before inserting.

**E2. P6 criterion matches code.** `sections/ers.tex:47` (tab:perturb)
- Old: `P6 & Append a confirmed-difference witness that hits all changed units & P & verdict $=\DIV{}$ \\`
- New: `P6 & Append a confirmed-difference witness that hits all changed units & P & verdict $=\DIV{}$ (\INS{} or $\Delta>0$ accepted) \\`

`sections/ers.tex:22`
- Old: `\item \emph{Divergence responsiveness.} Adding an independent discriminating input must change the verdict to \DIV{}.`
- New: `\item \emph{Divergence responsiveness.} Adding an independent discriminating input must withdraw a reassuring verdict; the intended outcome is \DIV{}, and the implementation also accepts \INS{} or a risk increase.`

`sections/ers.tex:27`
- Old: `Properties 5 and 7 prescribe an exact outcome.`
- New: `Property 7 prescribes an exact outcome; Property 5 prescribes withdrawal of \NDO{}.`

`sections/results.tex:63`, after "…on 71 records": add ` (its 157 passes rest entirely on stored \INS{} verdicts, i.e.\ abstention credit)`.

**E3. Evidence capture overclaim.** `sections/introduction.tex:15`
- Old: `Evidence is captured outside the program under test, re-observed in a shadow run and sealed,`
- New: `Coverage and run records are captured by a controller outside the program under test, standard output is teed by an in-process stub, an optional shadow run re-observes return values, and the evidence is sealed,`

**E4. Generalisation in Discussion.** `sections/discussion.tex:4`
- Old: `What does transfer is the observation that the rate is neither negligible nor reduced in any demonstrable way by stricter abstention.`
- New: `On these data the rate was neither negligible nor demonstrably reduced by stricter abstention; whether this holds elsewhere is untested.`

**E5. Random-abstention comparison.** `sections/results.tex:20`
- Old: `and is 4.4 points \emph{worse} than random abstention among B1-issuable pairs, whose expected risk is 0.169.`
- New: `and its observed risk is 4.4 points above the expected risk of random abstention among B1-issuable pairs (0.169); this contrast is not significant.`

`sections/discussion.tex:6`
- Old: `and full \cec{} at the same coverage was worse than random abstention.`
- New: `and full \cec{} at the same coverage did not beat random abstention (observed risk 4.4 points higher, not significant).`

**E6. Sidedness and the pre-registered family.** `sections/design.tex:84`, after "…and is Holm-adjusted.": add ` All bootstrap $p$-values are one-sided (H1: B8 has lower risk or log loss).`

`sections/results.tex:20`
- Old: `None of the eight recomputed contrasts reaches unadjusted significance at 0.05 in either policy, and after Holm adjustment the smallest $p$ is 0.68 (soft) and 1.0 (strict).`
- New: `In the pre-registered three-test family the Holm-adjusted $p$ is at least 0.46 in every soft-policy seed. None of the eight recomputed contrasts reaches unadjusted one-sided significance at 0.05 in either policy, and after Holm adjustment the smallest $p$ is 0.68 (soft) and 1.0 (strict).`

**E7. Security wording.** `sections/abstract.tex`
- Old: `Adversarial testing confirmed prevention of result-channel and keyless post-hoc tampering, detection-only coverage of in-process forgery, and one open sensing channel.`
- New: `Adversarial testing showed fail-safe abstention under result-channel and keyless post-hoc tampering, detection-only coverage of in-process forgery and evidence substitution, and one open sensing channel.`

`sections/conclusion.tex:5`
- Old: `The evidence collector prevents result-channel and post-hoc tampering by parties without the anchor key, detects but does not prevent in-process harness forgery,`
- New: `Result-channel and post-hoc tampering by parties without the anchor key force abstention rather than a false verdict; in-process harness forgery and evidence substitution are detected but not prevented;`

**E8. "Container" probes.** In `sections/results.tex:76`, `tables/tab_security.tex:17,21`, `sections/threats.tex:11` and the `fig_security_outcomes` caption/labels, replace `container probes` / `Container probes` with `isolation probes` / `Isolation probes`. At first use (results.tex:76) add ` (named ``container'' in the result file; no container runtime is invoked)`.

**E9. Conclusion "establishes".** `sections/conclusion.tex:7`
- Old: `The present evaluation therefore establishes the false-assurance estimand, the evidence-response framework and its perturbation protocol as usable instruments,`
- New: `The present evaluation therefore shows that the false-assurance estimand can be operationalised and that the evidence-response protocol can detect estimator defects,`

**E10. ERS separation claim is partly by construction.** `sections/introduction.tex:18`
- Old: `and the property matrix separates the \sbg{} trust gate from its predecessor, which violates integrity sensitivity on 155 of 312 records.`
- New: `and the property matrix exposed that the predecessor's verdicts ignore integrity failures (155 of 312 records when replayed, 84 when recomputed), which motivated the \sbg{} trust gate that now passes by construction.`

**E11. McKeeman citation.** `sections/introduction.tex:3`
- Old: `one of the oldest and most widely used ways of checking a change~\cite{mckeeman1998differential,evans2007differential}.`
- New: `one of the oldest and most widely used ways of checking a change~\cite{evans2007differential}, an application of differential testing~\cite{mckeeman1998differential}.`

**E12. Capability-table over-attribution.** `sections/background.tex:39–46`
- Row "Evaluates empty difference sets": `Y~\cite{just2014mutants}` → `P~\cite{jia2011analysis}`; `P~\cite{inozemtseva2014coverage}` → `N`.
- Row "Explicit false-assurance estimand": `P~\cite{papadakis2019mutation}` → `N`.
- Row "Matched-coverage risk comparison": the coverage, mutation and checked-coverage cells → `N`.
- Row "Abstention-aware verdicts": `P~\cite{palikareva2016shadow}` → `N`; `P~\cite{torresarias2019intoto}` → `N`.
- `background.tex:63`: `Shadow symbolic execution~\cite{palikareva2016shadow,kuchta2018shadow}` → `Shadow symbolic execution~\cite{palikareva2016shadow}`.

**E13. Table hygiene.** `tables/tab_ablation.tex`
- Delete the `Runtime` column; the footnote already states the per-seed runtime.
- Insert `\multicolumn{8}{l}{\emph{Rule baselines (all 258 labelled pairs)}} \\` before the B1 row, and move the "Soft blockers" header to just above the B7 row.
- Footnote: `54 unresolved and excluded` → `54 unlabelled and excluded`; `258 with generator labels` → `258 with construction labels`; `101 projects` → `101 labelled projects (114 overall)`.

**E14. Untraceable real-execution sentence.** `sections/ers.tex:63`
- Old: `Real-execution analogues exist for P2, P5 and P6 in a separate experiment (30 development pairs, few applicable); they are not part of the results reported here.`
- New: `A separate real-execution script for P2, P5 and P6 exists, but no raw output from it is in the replication package, and no result from it is used.`

**E15. Branch provenance.** `sections/reproducibility.tex:4`, after "…on branch \code{research/v8-linux-validation}.": add ` The placebo, frozen-threshold and profile-fix results come from branch \code{research/v8-mac-hardening} (commits \code{8e28f601}, \code{b9b8a86c}).`
- Replace `A claim--evidence register maps every numerical statement in this paper to its source file.` with `A claim--evidence register (\code{NUMERICAL\_CLAIM\_AUDIT.md}) maps every numerical statement in this paper to its source file.`

**E16. Missing strict-seed result.** `sections/results.tex:45`
- Old: `its interval includes zero in all five soft-policy seeds.`
- New: `its interval includes zero in all five soft-policy seeds and in four of five strict-policy seeds.`

**E17. Lower-bound assumption.** `sections/problem.tex:37`
- Old: `Because adjudication is itself bounded, the measured $\R$ is a lower bound`
- New: `Because adjudication is itself bounded, and assuming adjudicators do not report spurious divergences, the measured $\R$ is a lower bound`

**E18. Worst-case risks.** `sections/results.tex:6`, after the B1 sentence, add: ` Counting the unlabelled pairs that received \NDO{} as false assurances gives worst-case risks of 0.333 (B1), 0.324 (B3), 0.225 (B4) and 0.227 (B5).` Source: STAT audit §2a.

**E19. Abstract to 250 words or fewer.** For example, delete "(activation, coverage, multiplicity and diversity of observations, reproducibility, observation loss, channels, provenance, integrity, environment)" and replace it with "(activation, coverage, multiplicity, reproducibility, provenance and integrity)".

**E20.** Resolve the 505 pt overfull `\output` box reported in `main.log`.

### (b) Requiring new experiments or data

1. Run the implemented two-adjudicator protocol on an external corpus of real benchmark checkouts (BugsInPy and Defects4J execution), with a prediction lock that has an external timestamp. Target ≥ 460 issued NDO verdicts.
2. Label the 46 BugsInPy-derived pairs (at minimum, adjudicate the 8 V7-B NDO pairs) so that one real-project arm enters the risk estimates.
3. Populate provenance and environment from actual runs, and replace `obs_react` with dynamic dependence or checked coverage. Then re-run the profile ablations.
4. Re-run the ERS matrix with the profile fix integrated on the evaluated branch. Execute real (non-post-hoc) P2/P5/P6 interventions and include their raw output.
5. Add a mutation-adequacy baseline and AURC / multi-c* comparisons, including B4/B5 vs CEC at a common coverage.
6. Re-run the Linux security suite after remediation with host, sandbox configuration and timestamp recorded. Diagnose the 65 undecided probes. Implement anonymised file names for SENSE04b and re-test. An independent red team is desirable.

---

## 11. Recommendation: **Major revision**

**Reasons.**
- The manuscript is honest, well written and methodologically careful. Its estimand and matched-coverage lesson are useful.
- Its empirical support does not yet reach journal level. All risk numbers rest on construction labels from design-exposed, mostly synthetic data with one dominant cluster. The predictive contribution is null and underpowered by the authors' own analysis.
- The headline positive result (ERS as a conformance test) rests on one defect found on one probe estimator and a trust-gate pass that holds by construction. The P6 pass criterion is mis-described.
- The Section 10(a) edits fix every textual problem found and should be made regardless.
- Acceptance would require at least items (b)1–2: some independently adjudicated or real-project labelled data, even a modest set, so that the paper reports something beyond a pilot on its own development corpus.
- If the authors want to publish without new data, the paper should be repositioned explicitly as a methodology / negative-results paper. A short-paper or registered-report track may fit better than an IEEE Access full article.

*Reviewer's scope note:* the figures were not inspected visually beyond their captions and the PDF text (20 pages, no unresolved "??" references). The raw run directories (`results/repro/v8_dev_20261118_195446`) are not present in the worktree, so the hash-chained logs were not re-verified.
