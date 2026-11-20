# SBG Final Sprint — Completion Status

**Written:** 5 Nov 2026 (consolidation pass). **Repo:** `SBG`, branch `remediation/sbg-v4`.

## 1. Integrity result (re-checked at the end of this pass)

| Check | Result |
|---|---|
| Branch | `remediation/sbg-v4` (unchanged) |
| HEAD | `93ef3f38b840fc1e2a16a478b27bc9a2fb2b2146` (unchanged) |
| Tracked diff / staged diff | 0 lines / 0 lines |
| `git status` | The same four untracked `artifacts/final/*v8dev*` and `*dev_output_free_v8*` files as in the baseline, plus `paper/`. No new untracked files outside `paper/`. |
| Protected-file SHA-256 | 14,955 files hashed against `_baseline/sha256_before.txt`: **0 differences, 0 read errors**. The baseline equals the previous sprint's baseline byte for byte. |
| Files outside `paper/` newer than the baseline marker | None |
| Previous sprint directory (`paper/empirical_sprint_2026-11-04/`) | Not modified in this sprint (latest mtime 4 Nov 21:40) |
| Commits made | None |

**Limits of this check.** The baseline file list covers 14,955 files outside `paper/`. It excludes `paper/` itself and gitignored `__pycache__` directories. Nothing inside the previous sprint's directory was hash-baselined, so "not modified" there rests on timestamps only.

## 2. Completed

- **Agent 1** (`agent_1/agent_1_program_robustness_final.md`): independent recomputation, 79 checks, 0 mismatches. Corrected in the audit pass: pooled V5−M_EX delta is exploratory (not "frozen"); Holm family is H1–H6.
- **Agent 2** (`agent_2/agent_2_real_bug_failure_taxonomy.md`): written; **audited, with substantial defects.** An audit notice has been inserted. Its primary AUROCs and exact-zero reconciliation hold; its taxonomy and mechanism claims are not usable (see audit §3).
- **Agent 3** (`agent_3/agent_3_external_validation_decision.md`): candidate selection and protocol. The statement approving manuscript preparation was removed; a status banner was added. No SeqCoBench evaluation was run.
- **Agent 4** (`agent_4/agent_4_independent_evidence_audit.md`): written in this pass using the existing `agent_4/tables` and my own direct recomputations from frozen artifacts.
- **Agent 5** (`agent_5/agent_5_java_readiness.md`): written, not edited. It was already correctly scoped.
- **Agent 6** (`agent_6/FINAL_EMPIRICAL_READINESS_REPORT.md`): written in this pass.

## 3. Verified in this pass (independent code or direct artifact reads)

- V10 headline (19 / 638 / 319; V5 0.896768; edit 0.616046; M_EX 0.790789; M_EX+V5 0.797088), Holm family H1–H6, H4 not established.
- V9c (11 / 432 / 216; V5 0.7514) and V8 (V5 0.6937 vs reversed edit 0.8759) from frozen JSONs.
- All seven ablation AUROCs on V10.
- Per-program AUROCs, 19/0 and 14/5 win/loss, LOPO ranges, within/between concordance, matched-set concordance (edit size 0.9545 beats V5 0.931).
- BugsInPy 0.4099 and QuixBugs 0.3877 with CIs; the 21 / 24 / 26 exact-zero reconciliation.
- Seven invalid SP-2 negatives; unevaluated-pair counts for BugsInPy (14 positives, 39 negatives).
- Python-sensitivity stored counts (120/30, 75/4, max 0.4085).

## 4. Remains unaudited or only reviewed

- **Agent 4's `scripts/` and `tables/`:** their producer is unattested (spawn cancelled, files appeared). I relied on them only where my own computations agreed.
- **SeqCoBench:** counts are consistent across files but come from one pipeline; provenance, AST-overlap result, HumanEval/MBPP yield percentages, and power numbers were not independently checked. No network access was used.
- **Java:** 12-test pass, overhead figures, trace-gap findings and effort estimates were not rerun. The smoke JSONs were inspected only.
- **COBOL:** report reviewed, nothing rerun.
- **Component ablation on V9c:** deltas not recomputed.
- **Python sensitivity:** Spearman 0.968 and decision-flip count not recomputed; 3.13.5 vs 3.13.15 provenance unresolved.
- **Leave-two-out, effective-n, Spearman correlations, SC/SP-family tables** (previous-sprint outputs).
- **Agent 2's QuixBugs crash sets and quoted source snippets:** no source artifact found; treated as not established.
- **`STANFORD_GATE.json`:** dated 30 Oct, not regenerated.

## 5. Integrity concerns

1. **Agent 4 provenance.** The Agent 4 spawn call was cancelled, yet its scripts and tables exist. I cannot say who created them or whether they ran to completion. They agreed with independent checks.
2. **Agent 2 report defects.** Substantive errors (see audit §3). The report was kept for traceability with a notice, rather than deleted.
3. **Hard-coded inputs in `build_taxonomy.py`** are not traceable to an artifact.
4. **Interpreter version discrepancy** in the repository (3.13.15 vs 3.13.5).
5. **Scratch footprint:** `agent_5/_ws/` (about 6 MB) and `_baseline/` hash lists (about 5 MB) are inside the sprint directory. Harmless but deletable.
6. **Edited source reports.** Three reports in this sprint directory (Agents 1, 2, 3) were edited in the audit pass. None of the edits touch frozen evidence.

## 6. Execution record

No benchmark, V8/V9c/V10 evaluation, scorer, tracer or external-data job was run in this pass. Python was used for reading frozen JSON/JSONL, computing AUROCs from them in memory, and hashing. Nothing was downloaded. No agents were launched in this pass.

## 7. Verdict carried to the consolidated report

**READY AFTER SPECIFIED REMEDIATION** (wording and framing fixes, not new experiments). See `agent_6/FINAL_EMPIRICAL_READINESS_REPORT.md` §14–§16. This does not imply readiness for submission.
