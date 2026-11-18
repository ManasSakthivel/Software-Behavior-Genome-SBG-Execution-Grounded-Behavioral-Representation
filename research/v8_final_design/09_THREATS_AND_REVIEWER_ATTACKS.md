# 09 Threats and reviewer attacks

| # | Strongest attack | Answer in the design | Residual risk |
|---|---|---|---|
| 1 | "Evidence ablation is Schuler & Zeller 2011; influence is checked coverage; selective prediction and conformal control are textbook." | Agreed and attributed (02, 01). The contribution is claimed only as adaptation plus a tested hypothesis (RQ3) and an adjudicated estimand; not as a new intervention or calibrator. | A reviewer may find the contribution thin; the fallback paper is a negative/methodology result (10). |
| 2 | "Calibration on 60 projects with a few dozen false-assurance events is noise." | 07 sample-size analysis; at most 5 predictors; pilot downgrade rules; no generalisation claim. | High: realised intervals may be wide. |
| 3 | "Labels are circular: your adjudication inputs resemble your evidence." | Separate generators and seeds, blind adjudicators, kappa gate, Y=0 stated as budget-relative lower bound on risk. | Medium: independence is partial. |
| 4 | "The improvement is only abstention again." | Primary metric is risk at matched coverage with a matched-abstention baseline; coverage at fixed risk reported; Phase 2 showed this exact failure so the test is built in. | Low if executed as designed. |
| 5 | "A calibrated probability on dev projects will not transfer." | Project-held-out CV and one-shot holdout; transfer beyond the benchmark not claimed. | Medium. |
| 6 | "Response features are redundant with coverage multiplicity." | Baselines 9 and the multiplicity-only baseline; H3 can fail and is reported. | Real possibility. |
| 7 | "Counterfactual is misused; no causal identification." | Terminology restricted to evidence recomputation; formal text says evidence perturbation; no causal claims. | Low. |
| 8 | "The program can forge its own evidence." | V8-A parent-side collection and anchored log; until validated, all claims are conditional on non-adversarial programs. Phase 3 forgery suite. | High until Phase 3. |
| 9 | "Selection-induced bias: R is conditional on A=1." | Reported with c; eligibility set defined; pair- and project-weighted variants. | Low. |
| 10 | "Conformal guarantee misapplied." | CRC stated as secondary, with exchangeability, monotone loss, marginal-expectation caveats; ratio not claimed. | Low. |
| 11 | "Influence (D2) is not measurable in Python at useful precision." | M4 go/no-go; fall back to activation and multiplicity only. | Medium: reduces novelty further. |
| 12 | "Benchmark contamination by LLM training or public projects." | Record exposure; select projects with post-cutoff commits where possible; report contamination sensitivity. | Medium. |
| 13 | "Phase 2 numbers used to design V8 and then reused." | Dev data barred from confirmation; registration frozen before holdout scoring. | Low. |
| 14 | "macOS results do not transfer." | Linux/Docker validation in Phase 3 (V8-A); not claimed otherwise. | Medium. |
