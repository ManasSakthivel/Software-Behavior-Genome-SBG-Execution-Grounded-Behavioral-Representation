# Ground-truth validity audit
New file; linked from `../README.md`.

## What the labels are
| Label | Origin | What it establishes |
|---|---|---|
| 200 `bug_fix` (y=1) | Assigned by the generator for every case in the four "buggy/fixed" sets | By the name, a fix changes behaviour on the bug-triggering input. In the generated cases this holds only because each template embeds a discriminating input (`trigger_discriminating`, 400 inputs) |
| 50 `non_behavioural` (y=0) | Authored by the generator ("formatting and documentation cleanup") | Not a benchmark label: none of the five benchmarks provides behaviour-preserving pairs. Preservation holds by template construction |

What genuine benchmark labels would establish, for reference: Defects4J/BugsInPy/Bears/Bugs.jar bug-fix pairs mean the developer test fails on the buggy version and passes on the fixed one, i.e. an observable behavioural difference *on that test*, not general correctness. BugSwarm labels CI fail/pass, a weaker notion. None of these would be an adjudication within (O, B).

## Were predictions scored against the label that built the case?
Yes. In `executor.pair_to_evidence_record`, `y` and the per-input outcomes are both derived from `change_type`; the V8 verdict is then computed from those outcomes. The verdict is `DIVERGENT_OBSERVABLE` for 200/200 bug fixes and `NO_DIVERGENCE_OBSERVED` for 50/50 non-behavioural. This is circular: any accuracy computed is a check of the mapping.

## What needs independent adjudication
All 250 would, if the cases were real. As they stand, adjudication of the generated snippets would test only whether the generator's labels agree with a human reading of 6-line functions. It would not validate SBG on real software. The protocol in `INDEPENDENT_ADJUDICATION_PROTOCOL.md` is therefore designed to apply to real checkouts (or to these 250 cases as a snippet-level sanity check, clearly labelled).

## Preservation
Original results are untouched. Their scope: pipeline demonstration and label-consistency; no claim of detection or risk.
