# SBG V6 — Architecture

Layers (each independently testable; `sbgv6/`):
1. **Adapter** (`observe.py`): language adapter interface `observe(source, entry, inputs) -> Observation`. Implemented: **Python** (reuses the V5 sandbox tracer so V5 and V6 see identical traces). **Java and C: interface only — not implemented** (no behaviour-measuring adapter exists in the repo; prior Java/C results measured static text, see `02_PRIOR_CLAIM_AUDIT.md`).
2. **Evidence** (`evidence.py`): per-side completion/truncation/timeout/exception/instrumentation, nondeterminism check, change-activation.
3. **Blocks** (`features.py`): A invariants, B transitions, C dynamic-CFG, R return-state, E change-activation.
4. **Distance** (`distance.py`): block distances, status ∈ {ACTIVATED, NOT_ACTIVATED, UNKNOWN}, confidence, raw V6 score. No labels used.
5. **Fusion** (`fusion.py`): optional supervised models; trained only inside training folds. The representation layer 1–4 has no trainable parameters.
6. **Reporting**: JSONL per pair with all block distances, evidence, status, raw score, stored V5 scores.

Data flow: source pair → entry/inputs (V5 protocol, unchanged) → traces (run 0 for features, run 1 for nondeterminism check) → per-side Observation → blocks → pair record → (optional) fusion → score + status + confidence.

Failure conditions: import failure, no entry, non-termination, empty trace, nondeterminism → status UNKNOWN with reason code. Nothing is imputed as "no change".

Regimes: R1 (oracle-free: blocks A,B,C,E-evidence only; return values/exception *types* unused) and R2 (adds R and differential baseline). Reported separately.

Reproducibility: PYTHONHASHSEED=0, seed 42, CPython 3.13.15, config frozen in `sbgv6/config.py` and hashed in the freeze record before any held-out run.
