# Adjudicator instructions (TEMPLATE; Phase 3, requires explicit authorisation before use)

You judge ONE version pair at a time, alone, without discussing it. You will not be shown any tool verdict, score, risk, or
baseline output, and you must not seek them. If you have seen them, say so and stop; the case is reassigned.

## What you receive (frozen, hashed)
- pair id, the code diff (no commit message or issue text unless the protocol lists it), the declared entry point,
- the observation boundary O (channels that count: return value, exception, selected side effects, declared API calls),
- the budget b (e.g. number of independent adjudication generators, seeds, time cap). You may not exceed or extend it.
- adjudication-only inputs. These are never the inputs the evaluated system used.

## Decide exactly one outcome
1. `confirmed_divergence`: you exhibit an input x in the declared domain where base and variant differ in an observable
   channel in O, and the difference reproduces on repeated runs under the determinism controls. Attach x, both observations,
   and run ids.
2. `no_divergence_found_within_budget`: you used the whole budget without such an input AND you judge, from the diff, that the
   change is not behaviour-altering within scope (refactor, dead path, out of scope). This is NOT a claim of equivalence.
3. `unresolved`: budget exhausted but you cannot judge the change, or runs were non-reproducible, or the scope is unclear.
   Do not guess; unresolved cases are counted and reported.

## Record
Outcome, free-text rationale (required), evidence artefact ids, your adjudicator id, and the time. Decisions are
append-only; you cannot edit one. Disagreements go to a third adjudicator who sees both rationales but no tool outputs.
The audit log is tamper-evident only (hash chain), not tamper-proof.
