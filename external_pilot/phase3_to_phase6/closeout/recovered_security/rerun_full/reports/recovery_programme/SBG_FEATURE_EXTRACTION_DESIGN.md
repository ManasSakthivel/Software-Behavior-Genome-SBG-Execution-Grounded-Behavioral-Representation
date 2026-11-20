# SBG BEHAVIOURAL FEATURE EXTRACTION PIPELINE DESIGN

**Date:** 2026-11-16  
**Auditor/Author:** Principal Software Engineering Scientist  
**Focus:** Zero-Leakage, Deterministic Dynamic Trace & Genome Extraction

---

## 1. Architectural Philosophy & Zero-Leakage Principle

The feature extraction architecture enforces strict methodological and scientific invariants:
1. **Prediction-Time Feature Separation:**
   Only information available at prediction time is extracted. When evaluating a candidate change/patch $(P, P')$, feature extraction is executed strictly on the base and variant programs under test inputs. Output oracle values and ground-truth fix labels are strictly isolated.
2. **Single Shared Execution Pass:**
   To prevent confounding feature definitions with execution protocols, both base and variant are traced in an identical execution pass with identical input batteries, timeouts ($1.0\text{ s}$ per trace), and event budgets ($5,000$ events per trace).
3. **Rename-Invariant Structural Entry Selection:**
   Protocol `output_free_v8` inspects AST topology to select the corresponding structural entry point between $P$ and $P'$ even when function names are altered by refactoring transformations, preventing test driver leakage or entry-point mismatch.
4. **Deterministic Sandboxing:**
   Executions occur in worker threads with `sys.settrace`, capturing:
   - Line execution counts and coverage sets.
   - Function call/return event sequences.
   - Local variable snapshots (string representations truncated at 100 characters).
   - Unhandled exception types and tracebacks.

---

## 2. Feature Extraction Stages

```
Source File P (.py)
   │
   ▼
[Stage 1: Static AST Analysis & Entry Policy]
   │  ├── Parse AST, identify callable functions
   │  └── Structural matching under renaming (experiments/final/entry_policy.py)
   │
   ▼
[Stage 2: Dynamic Sandbox Tracing]
   │  ├── Input Battery: 11 type-matched synthesized inputs
   │  ├── sys.settrace instrumentation (5 runs / input, max 5,000 events)
   │  └── Record TraceEvent objects (event_type, lineno, func_name, locals_repr)
   │
   ▼
[Stage 3: Multi-Dimensional Genome Construction]
   │  ├── Call Topology Genome (V3): Function call frequencies & Jaccard line coverage
   │  ├── Temporal Sequence Genome (V5 temporal): Instruction type dynamic time warping
   │  └── State Transition Genome (V5 state): Shannon entropy & variable value transitions
   │
   ▼
[Stage 4: Pairwise Dissimilarity Computation]
   │  └── Composite Metric: d_V5 = 0.50 * d_V3 + 0.25 * d_temporal + 0.25 * d_state
   │
   ▼
[Stage 5: Serialization & Provenance Stamping]
   │  └── Store vector + metadata + SHA-256 hash in JSONL / Parquet format
```

---

## 3. Failure Handling & Explicit Exclusions

Rather than silently dropping unexecutable mutants or failing pairs:
- Failures are captured in a structured failure ledger.
- Program timeouts, syntax errors, or unresolved imports are logged with exact failure classifications.
- Unevaluable pairs are explicitly tracked in denominator audits.
