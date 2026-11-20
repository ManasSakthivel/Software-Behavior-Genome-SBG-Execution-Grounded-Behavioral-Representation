# Adapter v1 compatibility report (Phase 4 preflight)

Scope: non-executing. Adapter v1 and frozen SBG V8 were not run on any of the 15 cases. Inspection used `git show`, `git diff` and Python `ast` on the parent revision sources only.

## Adapter v1 supports
Top-level functions whose parameters are scalars (`int`, `float`, `str`, `bool`), with no defaults, no `*args`/`**kwargs`, and changes confined to one file.

## Result: 0 of 15 compatible

| Blocking feature | Cases blocked | Cases |
|---|---|---|
| Class instance or method needed | 7 | schedule 90bfdf355, f19998bcf, bcfa35789 (Job, Scheduler); funcy 2da8b5e04 (descriptor on a generated class); more-itertools 2b8d5cddc (bucket), 6b1907de2 (seekable); boltons d0a284fc7 (IndexedSet) |
| Container input (iterable, mapping, sequence, or stateful container) | 7 | funcy 848dd6dd2, 54ed07a6a, e068b6400; more-itertools 2b8d5cddc, 71e070b35, 6b1907de2; boltons d0a284fc7 |
| Callable input | 5 | funcy 6cfcd4eec, e148cc9ab, 54ed07a6a; more-itertools 2b8d5cddc (key, validator), 71e070b35 (key) |
| Defaulted parameters | 7 | funcy 980f0279a, 54ed07a6a, e148cc9ab; schedule bcfa35789; more-itertools 2b8d5cddc (validator), 71e070b35, 6b1907de2 |
| Non-scalar scalar-like input (timedelta, exception class) | 2 | funcy 6c111987f, 980f0279a |
| Multi-file change | 0 | — (all 15 change exactly one source file) |

A case is listed under every feature that blocks it, so counts overlap.

## Observation boundary
Every case has a defect channel inside O = {outcome, exception, side_effect, api}. Examples: schedule run_all (side_effect), memoize (TypeError, exception), more-itertools bucket (public key set, api). No case is observationally unsuitable under the frozen boundary. The boundary is not expanded.

## Time dependence (not a compatibility failure, but a validity risk)
- schedule f19998bcf: uses a mocked date.
- funcy 980f0279a and 6c111987f: involve time or timeout arithmetic; reproducibility of the parent failure needs repeat runs.
