# Class-Driver Policy Decision
## Software Behavior Genome (SBG) — B07 Resolution

**Date:** 2026-10-26  
**Branch:** `remediation/sbg-v2`  
**Status:** DECISION MADE — Option 1 as primary; Option 2 as pre-declared secondary if validated on dev  
**Source analysis:** `reports/remediation/agent_c_v8_coverage.md` (full coverage analysis)

---

## 1. Decision

**Primary v8 policy: Option 1 — function-only execution; class programs → `not_evaluable`.**

**Pre-declared secondary stratum: Option 2 — rename-invariant class driver** (only if implemented, tested, and dev-validated before the protocol freeze; reported separately; never mixed into the primary number).

**Option 3 (alphabetical class driver) is rejected** — it is not rename-invariant under the repaired SP-2.

---

## 2. Options compared

| Criterion | Option 1: function-only | Option 2: structural class driver | Option 3: alphabetical |
|---|---|---|---|
| Rename-invariant | ✅ Yes | ✅ Yes (with interface key) | ❌ No — 25/48 pairs differ under repaired SP-2 |
| Programs evaluable | 18/47 (38%) | 34/47 (72%) | 34/47 (72%) |
| New code needed | None | ~30–50 lines + tests + new protocol id | None (already exists) |
| New pre-registration entry needed | No | Yes | No |
| Contamination risk | Low | Low if implemented correctly | High — see §4 |
| Fresh programs needed (≥20 evaluable) | ≥50 total (38% attrition) | ≥28 total (72% attrition) | Not recommended |

---

## 3. Justification for Option 1 as primary

**Correctness:** Option 1 is the only option whose every trace is selected by a rule shown to be rename-invariant under all SP transformations including the repaired SP-2. The 37-test `test_entry_policy.py` suite passes on all function-only programs.

**No contamination:** The class driver's alphabetical ordering changes the driven method sequence in 25/48 pairs even after the SP-2 repair. This is because alphabetical ordering depends on method names, and the repaired SP-2 can still add `fn_` prefix to method names. Using it in the primary result would reintroduce the instability that `output_free_v8` was designed to remove.

**Simplicity:** Option 1 needs no new code, no new protocol id, and no new pre-registration amendment. The existing `entry_policy.py` and its 37 tests already cover it completely.

**Coverage cost is honest:** 18/47 programs (38%) is a real limitation that must be reported. Under Option 1, the evaluation is restricted to stateless functional programs (sorting, string matching, graph algorithms, parsing). Stateful class-based programs (data structures, FSMs, API wrappers) are excluded. This must be stated in the claim boundary and the paper's scope.

---

## 4. Why Option 3 is rejected

From `agent_c_v8_coverage.md`:

> The class driver is not rename-invariant, and the problem is bigger than "alphabetical ordering": the *eligibility* filter is also name-based (`_` prefix, `Test` prefix). SP-2 adds the prefix `fn_` to many names, so `_swap` → `fn__swap` becomes public and enters the driven set; `len(methods)` changes, which changes the modulus and therefore every step.
> 
> On the committed v6 variants: 25/293 class-program EQUIVALENT pairs have different driven sequences. Under the repaired SP-2: **25/48 non-no-op variants** differ.

This means Option 3 would produce non-equivalent traces for base and variant programs that should be labelled EQUIVALENT. Scoring them as EQUIVALENT pairs when they executed differently is a label-integrity defect.

---

## 5. Option 2 implementation specification (if pursued for secondary stratum)

Option 2 requires a rename-invariant class driver. Based on the agent_c analysis, the correct approach is:

**Method ordering key:** `(is_static: bool, required_param_annotation_texts: tuple, return_annotation_text: str)` with declaration-order tie-break within equal keys.

**Rationale for this key:**
- `is_static` and annotation texts are not changed by any rename transformation (SP-1/SP-2) or by the body-editing SP-3/5/6/8/11 transformations.
- Declaration order provides a deterministic tie-break that is invariant under all current SP transformations (SP-1 through SP-12 do not reorder method declarations).
- The body fingerprint approach (`sha256(normalised AST)`) was tested and **rejected**: it changes in 106/293 pairs for body-editing transformations (SP-3, SP-5, SP-6, SP-8, SP-11).

**Eligibility filter:** Replace name-based filters (`_` prefix, `Test` prefix) with structural filters:
- A method is a helper if it is referenced as `self.<m>()` by another non-driver method (mirror of the function-tier rule).
- Dunder methods remain excluded (their names are protocol, not user-chosen; SP-2 skips them).
- Exception-class detection remains via base-class name pattern (no current SP renames base class names).

**New protocol id:** Must use a distinct protocol id (e.g., `output_free_v8_class`) and a new pre-registration entry.

**Validation before freeze:** Must be validated on the dev split of the fresh benchmark. The measured driven-sequence stability (base vs variant for EQUIVALENT pairs) must be documented. If stability is < 95% of EQUIVALENT pairs, do not use in the primary result.

**If implemented:** Report Option 2 results as a separately labelled secondary stratum in the paper. Never combine them into the primary AUROC.

---

## 6. Coverage consequence for fresh program count

Under **Option 1 (primary)**:
- Observed attrition rate: 18/47 = 38% of programs are evaluable.
- To achieve ≥20 evaluable programs: write **≥50 total programs** (50 × 38% ≈ 19; write ≥54 to be safe).
- Important: design fresh programs to maximize the proportion with a single unambiguous root function (avoid multi-API library modules, avoid pure class programs).

Under **Option 2 (secondary, if implemented)**:
- Observed survival rate: 34/47 = 72%.
- To achieve ≥20 evaluable: write ≥28 programs.
- But Option 2 requires additional implementation and validation work before it can be used.

**This session's decision: write ≥50 programs targeting Option 1 eligibility. Design programs as single-function modules where possible. Record the reasons for any NoEntryPoint or AmbiguousEntryPoint outcomes.**

---

## 7. AmbiguousEntryPoint programs — separate issue

11 programs raise `AmbiguousEntryPoint` (not `NoEntryPoint`): these are multi-API function modules (e.g., `graph_bellman_ford` has `bellman_ford` and `reconstruct_path` both as parallel public APIs). The class driver cannot recover these; they would require a multi-root driver.

**Handling for fresh programs:** When writing fresh programs, avoid programs with multiple parallel public APIs of equal structural rank. Each fresh program should have one clearly identifiable entry function (the "main thing this module computes"). If a program has multiple parallel APIs, document it as a candidate for exclusion before generating any data.

---

## 8. What this decision does not change

- The function-tier entry policy (`output_free_v8`) is already implemented and tested.
- The existing 37 tests in `tests/test_entry_policy.py` cover the function-only policy.
- No code changes are required for Option 1 to take effect in `generate_v7_dataset.py`.
- The class-driver code in `class_driver.py` is preserved for potential Option 2 secondary analysis.

---

## 9. Recording this decision

This decision must be recorded in `FREEZE_V8.json` at the time of the protocol freeze:
```json
{
  "entry_policy_id": "v8:structural",
  "entry_policy_class_driver": "Option 1: function-only; class programs not_evaluable",
  "option_2_secondary_stratum": "not implemented (deferred)"
}
```

If Option 2 is implemented and validated before the freeze, change:
```json
{
  "entry_policy_class_driver": "Option 1 primary + Option 2 secondary (interface key, declaration-order tie-break)",
  "option_2_secondary_protocol_id": "output_free_v8_class",
  "option_2_secondary_dev_stability": "<measured fraction>"
}
```
