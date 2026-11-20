# Adapter extension feasibility (Phase 4 preflight; no implementation)

None of these extensions has been implemented. Each would change the adapter only, not frozen V8, provided the adapter continues to produce the `(base, variant, entry, inputs)` arguments that `compare()` already accepts.

| Extension | Cases unlocked | Required engineering | Changes frozen V8? | Extra fixtures needed | Input-generation bias risk | Validation needed |
|---|---|---|---|---|---|---|
| Class instance / method invocation | up to 7 | Build a harness that imports the class from the revision, constructs it from generated arguments, and calls the method. Must generate valid object states, not only constructor arguments. | No | Dev fixtures: a small class per pattern, with state | High: constructor and state generators decide what is reachable; the defect may only appear in certain states | Gates A–C as before, plus a state-coverage check per fixture |
| Container inputs (iterable, mapping, sequence) | up to 7 | Type-directed generation of small lists, tuples, dicts, with element types drawn from a fixed grammar | No | Dev fixtures with each container type | Medium: length and element distributions shape which branches fire | Determinism; coverage of element-type branches |
| Callable inputs | up to 5 | Generated callables from a fixed set (identity, constant, simple predicate); no user-supplied code | No | Dev fixtures with callable parameters | High: the set of callables determines reachable defect regions | Gate that the defect region is hit by at least one generated input on each development fixture |
| Defaulted parameters | up to 7 | Generate with and without the default, both recorded | No | Dev fixtures with defaults | Low–medium | Gate A variants |
| Non-scalar scalar-like inputs (timedelta, exception class) | 2 | Typed generators for datetime.timedelta and exception classes from a fixed list | No | Dev fixtures | Medium | Gate A variants |
| Multi-file modules | 0 in this shortlist | Not needed for these cases | No | — | — | — |

## Principal concern
Every extension moves the generator from "scalar inputs" to "generated objects, containers and callables". That is a research problem in its own right: the defect region depends on the generator. A pilot run after these extensions would measure as much the generator as SBG. This is the main reason the recommendation is not "extend and proceed".

## What would be needed for a defensible extension
1. A written input-generation specification, frozen before use.
2. Development fixtures separate from the 15 cases, with defect regions known only to the developer.
3. Demonstration that generation reaches a defect region on development fixtures, before any external case is run.
4. A new adapter version and checksum, recorded as a separate condition from v1.

No case-specific handwritten inputs were or will be introduced.
