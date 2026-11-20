# SBG V6 — Feature Specification (per-pair vector)

| Name | Dim | Range | Regime | Undefined when |
|---|---|---|---|---|
| d_A invariant distance | 1 | [0,1] | R1 | no invariants either side |
| d_B transition JSD | 1 | [0,1] | R1 | no line events |
| d_C CFG WL-1 JSD | 1 | [0,1] | R1 | no edges |
| cfg_size (log N, log E, cyclomatic) Δ | 3 | [0,1) | R1 | no edges |
| g gated divergence | 1 | [0,1] | R1 | token seqs empty |
| α change-activation | 1 | [0,1] | R1 | no diff lines |
| c confidence | 1 | [0,1] | R1 | — |
| status one-hot | 3 | {0,1} | R1 | — |
| d_R return-state | 1 | [0,1] | R2 | no common usable input |
| δ_out exact differential | 1 | [0,1] | R2 (baseline) | same |
Missing → NaN in JSONL; models get an explicit missing-indicator and zero fill **inside** the pipeline fitted on training folds only.
Normalisation: all distances are bounded by construction; no global min–max (avoids test-set leakage).
Rename/format invariance requirements (tested): variable rename, function rename, comment/blank-line insertion, formatting leave d_A,d_B,d_C unchanged.
