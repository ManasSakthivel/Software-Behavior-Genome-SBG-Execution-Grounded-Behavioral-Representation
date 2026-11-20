# Adapter v1 compatibility report (Phase 4 preflight, corrected v2)

Scope: non-executing. Neither Adapter v1 nor frozen V8 was run on any of the 15 cases. Evidence: `ast` of the parent-revision sources, `git diff` of each fix, and the regression test lines added by each fix. Canonical matrix: `EXTERNAL_CASE_COMPATIBILITY_MATRIX.csv` (v2). The v1 version is preserved in `previous_v1/`.

## Adapter v1 rules (as implemented and gated)
Top-level functions; scalar parameters (`int`, `float`, `str`, `bool`); no defaulted parameters; no `*args`/`**kwargs`; changes confined to one file.

## Result: 0 of 15 compatible (each case individually blocked; see the audit)

Blockers are not unique to a case. Counts below are cases affected per category; a case appears in every category that blocks it.

| Category | Cases affected | Cases |
|---|---|---|
| CLASS | 7 | schedule:90bfdf355, schedule:f19998bcf, schedule:bcfa35789, funcy:2da8b5e04, more-itertools:2b8d5cddc, more-itertools:6b1907de2, boltons:d0a284fc7 |
| CONTAINER | 8 | funcy:848dd6dd2, funcy:e148cc9ab, funcy:e068b6400, funcy:54ed07a6a, more-itertools:2b8d5cddc, more-itertools:71e070b35, more-itertools:6b1907de2, boltons:d0a284fc7 |
| CALLABLE | 10 | schedule:90bfdf355, schedule:f19998bcf, schedule:bcfa35789, funcy:6cfcd4eec, funcy:980f0279a, funcy:e148cc9ab, funcy:6c111987f, funcy:54ed07a6a, more-itertools:2b8d5cddc, more-itertools:71e070b35 |
| DEFAULT | 12 | schedule:90bfdf355, schedule:f19998bcf, schedule:bcfa35789, funcy:6cfcd4eec, funcy:980f0279a, funcy:848dd6dd2, funcy:e148cc9ab, funcy:54ed07a6a, more-itertools:2b8d5cddc, more-itertools:71e070b35, more-itertools:6b1907de2, boltons:d0a284fc7 |
| NONSCALAR | 2 | funcy:980f0279a, funcy:6c111987f |
| VARKW | 4 | schedule:90bfdf355, schedule:f19998bcf, schedule:bcfa35789, funcy:e068b6400 |
| KWONLY | 2 | funcy:6cfcd4eec, funcy:e148cc9ab |

Time-dependence (not an adapter refusal; a validity risk, counted separately): 3 cases (schedule:f19998bcf, funcy:980f0279a, funcy:6c111987f).

**Unique cases with at least one adapter blocker: 15 of 15.**
**Cases with two or more blocker categories: 14 of 15.** One case (funcy 2da8b5e04) has a single category (CLASS).

## Observation boundary
Every case has a defect channel inside O = {outcome, exception, side_effect, api}; the boundary is not expanded. The more-itertools `bucket` defect is observed through the public key set (`set(D)`, an api channel).

## Changes from v1
See `PHASE4_PREFLIGHT_MATRIX_INTEGRITY_AUDIT.md` for the full list. In summary: entry points corrected for 5 cases (funcy 6cfcd4eec, 848dd6dd2, 54ed07a6a; boltons d0a284fc7; more-itertools 6b1907de2); blocker counts corrected for every category; VARKW, KWONLY and TIME categories added.
