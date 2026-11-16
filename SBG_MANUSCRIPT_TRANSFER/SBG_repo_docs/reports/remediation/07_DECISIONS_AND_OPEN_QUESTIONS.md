# 07. Decisions and open questions

Branch: `remediation/sbg-v2`. Status: decisions required from the experiment
owner before any further experiment can be run.

---

## D1. Edit-size benchmark redesign (BLOCKING)

**Question:** Implement Agent B's `max_sites` redesign before generating the
fresh test set?

**Evidence:** Reversed edit-size AUROC on v6 test = 0.967. Bins ≥6 changed
lines contain 0 CHANGED pairs. The confound is structural and cannot be
analysed away. On the dev split, reversed edit-size AUROC = 0.957 and SBG V5
AUROC within the smallest bin (0–2 lines) = 0.492 (chance).

**Options:**

| Option | Description | Impact on timeline |
|---|---|---|
| D1-A | Implement `max_sites=2` cap for SP transformations; add multi-site SC variants | 2–3 weeks |
| D1-B | Use the current generators; report edit-size stratified results and call out the confound explicitly | Now |
| D1-C | Hybrid: implement `max_sites` for SP-1 and SP-2 only (highest confounders) | 1 week |

**Recommendation:** D1-A. The confound is so complete (0.967) that any
positive AUROC result is scientifically uninformative without addressing it.
If D1-B is chosen, the paper title and abstract must not claim that SBG
detects semantic change — it would only show that the edit-size shortcut does.

**Dependency:** `benchmark/scripts/generate_v7_dataset.py` already uses the
repaired SP-2. The `max_sites` parameter needs to be added there and to all SP
transformation generators (SP-1 through SP-12).

---

## D2. Class-based program policy for v8 (BLOCKING)

**Question:** Which class-driver policy to use for v8?

**Evidence from Agent C:**
- 16 of 47 non-test programs raise `NoEntryPoint` (all class-only)
- 11 raise `AmbiguousEntryPoint` (function modules with multiple APIs)
- Under Option 1 (function-only): 18/47 programs evaluable
- Under Option 2 (function + rename-invariant class driver): 34/47 evaluable

**Options:**

| Option | Description | Rename-invariant | Programs evaluable |
|---|---|---|---|
| 1 | Function entries only; class → `not_evaluable` | Yes | 18/47 |
| 2 | Function + class driver with coarse structural ordering | Yes | 34/47 |
| 3 | Function + alphabetical class tier, flag `rename_invariant=False` | No | 34/47 |

Agent C recommends Option 1 as primary with Option 2 as a dev-validated
secondary stratum. Option 3 is rejected (known-unstable in the primary result).

**Impact of Option 1:** the plan says "write ≥30 so ≥20 survive". Under
Option 1 only ~38% of programs are evaluable, so ≥50 programs must be written
to get ≥20 evaluable. Agent E's analysis agrees: write ≥36 programs.

**Dependency:** affects fresh-program count and the freeze checklist.

---

## D3. Fresh test set source (BLOCKING)

**Question:** Write programs from scratch, or adapt from public permissively-
licensed sources?

**Evidence:** Agent E identified 7 source families covering ~77 candidate
programs. The existing 64 programs, 25 in `benchmark/v5/corpus`, 50 QuixBugs,
55 regression programs, and 10 cross-language programs are all excluded.

**Options:**

| Option | Description | Risk |
|---|---|---|
| D3-A | Write from scratch | Slowest; safest for independence |
| D3-B | Adapt from CC0/MIT-licensed public sources with provenance record | Faster; requires deduplication check |
| D3-C | Hybrid | Recommended |

**Recommendation:** D3-C. Allow adaptation with a documented provenance record
and a Jaccard token-overlap screen (threshold 0.10) against all known programs.
Any program above 0.10 must be rewritten or dropped.

**Required minimum:** 36 programs that pass v8 selection (after SP-2 fix and
D2 policy choice). Agent E's template in `docs/current/FRESH_PROGRAM_SOURCES.md`.

---

## D4. Learned execution-trace baseline (NON-BLOCKING)

**Question:** Approve a GRU/embedding learned baseline?

**Evidence:** Agent D found this requires a non-stdlib dependency. A
bag-of-events cosine similarity could approximate it without dependencies.
BugsInPy and QuixBugs show below-chance results, so the learned baseline
may not help.

**Recommendation:** Defer until after the fresh-split evaluation establishes
whether SBG has signal to improve. Required minimum baseline suite (Agent D):
`edit_size (reversed)`, `exception_fraction`, `call_count`, `static_ast`,
`SBG V5`.

---

## D5. Handling of adverse external results (NON-BLOCKING for code, BLOCKING for paper)

**Evidence:**
- BugsInPy (v7, output_free): AUROC 0.410, CI [0.326, 0.494] — below chance
  on 39 bugs across 11 projects
- QuixBugs canonical (v7): AUROC 0.388 on 40 bugs
- Agent D: 29/40 QuixBugs programs (72.5%) below chance individually; BugsInPy
  result is systematic across 6/11 projects

**Required for submission:** These results must appear in the primary results
section, not a limitations appendix. A plausible explanation (not post-hoc
tuning) must be presented. Current hypothesis: the benchmark's synthetic
programs have a different edit-size distribution from real bug fixes, and SBG
captures edit-size signal that inverts on real bugs. This hypothesis must be
tested on dev data only.

---

## D6. Gate `real_program_validity` logic (MEDIUM PRIORITY)

**Issue:** The gate passes `real_program_validity` because 39 programs were
evaluated, but AUROC = 0.410 (below chance). The gate conflates coverage with
success.

**Recommended fix:** Change the `real_program_validity` check in
`experiments/final/stanford_gate.py` to also require AUROC ≥ 0.5 for the
external evaluation. After the fix, this category would be BLOCKED.

**Constraint:** This would change the gate from 8/20 to 7/20 PASS. Documents
quoting "8/20" would need to be updated. The orchestrator should implement this
as a separate commit after owner approval.

---

## D7. Power analysis requirement before fresh test

**Agent E finding:** `benchmark/scripts/power_analysis.py` reports ADEQUATE at
800 pairs but treats pairs as independent. Program-level SD from v6 = 0.145
(range 0.364–0.803).

**Required before freezing:** Run `power_analysis.py` on dev data per-program
results, not per-pair. If SD of per-program AUROC differences > 0.15, write ≥30
evaluable programs (≥50 total with D2-Option 1 attrition).

**This is a pre-freeze gate, not a submission blocker per se.** The evaluation
plan already requires it (§3 step 2). Run `benchmark/scripts/power_analysis.py`
on dev-only data before the FREEZE_V8.json is written.

---

## Order of operations (frozen)

All seven steps must be completed in order. No step may proceed before its
predecessor is verified:

1. **D1**: Choose and implement edit-size redesign (`max_sites` or equivalent)
2. **D2**: Choose class-driver policy for v8
3. **D3**: Choose fresh-program source policy; write ≥36 programs
4. **Fix SP-2** (done in this branch) → apply to v7 generator → regenerate full dataset
5. **Run `data_integrity.py --strict`** on the new dataset → must exit 0
6. **Freeze**: commit `FREEZE_V8.json` with all SHAs before any extraction
7. **Run**: `make v7-train v7-fit v7-test` in order → one run, no re-run
