# Adapter extension feasibility (Phase 4 preflight, corrected v2; no implementation)

None of these extensions has been implemented. Each would change the adapter only, not frozen V8, provided the adapter still produces the `(base, variant, entry, inputs)` arguments that `compare()` accepts.

| Extension | Cases affected (overlapping) | Required engineering | Changes frozen V8? | Extra fixtures | Input-generation bias risk | Validation |
|---|---|---|---|---|---|---|
| Class instance / method invocation | 7 | Build objects from the revision, construct them from generated arguments, and call the method. The state must be generated, not just constructor arguments. | No | a small class per pattern, with state | High: constructor and state generation decide which defect states are reachable | Gates A–C plus a state-coverage check per fixture |
| Container inputs | 8 | Type-directed generation of lists, tuples, dicts and ranges from a fixed grammar | No | one fixture per container type | Medium: length and element distributions shape which branches fire | determinism; branch coverage over element types |
| Callable inputs | 10 | Generated callables from a fixed set (identity, constant, predicate); no user-supplied code | No | fixtures with callable parameters | High: the callable set determines reachable defect regions | a defect-region hit check on each development fixture |
| Defaulted parameters | 12 | Generate with and without the default and record both | No | fixtures with defaults | Low–medium | Gate A variants |
| Variadic or **kwargs | 4 | Generate positional and keyword forms explicitly | No | fixtures with varargs and kwargs | Medium | Gate A variants |
| Keyword-only parameters | 2 | As for defaults, with keyword-only binding | No | fixtures | Low–medium | Gate A variants |
| Non-scalar scalar-like inputs (timedelta, exception class) | 2 | Typed generators for timedelta and exception classes from a fixed list | No | fixtures | Medium | Gate A variants |
| Multi-file modules | 0 | Not needed by these cases | No | — | — | — |

Time-dependent cases (3) need controlled clocks in the harness. That is a harness question, not an adapter-refusal question.

## Principal concern
Each extension moves input generation from scalar values to objects, containers, callables and keyword forms. The defect region then depends on the generator. A pilot after these extensions would measure the generator as much as SBG. This is the main reason the recommendation is not "extend and proceed".

## What a defensible extension needs
1. A written, frozen input-generation specification.
2. Development fixtures separate from the 15 cases, with defect regions known only to the developer.
3. Evidence that generation reaches a defect region on the development fixtures, before any external case is run.
4. A new adapter version and checksum, recorded as a separate condition from v1.

No case-specific handwritten inputs were or will be introduced.
