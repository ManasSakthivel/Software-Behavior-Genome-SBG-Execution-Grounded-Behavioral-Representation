# Limitations

Stated as limits on what the evidence supports, not as caveats on a conclusion
that is otherwise assumed.

## Sample size

The test split holds 13 programs, of which 7 are in scope for the output-free
protocol. The unit of independence is the program, not the pair, so a
confidence interval computed correctly is wide: the clustered bootstrap
interval on the statistically valid set spans roughly ±0.07 AUROC with 13
clusters, and more with 7. Nothing here supports a claim about behaviour on
programs unlike these.

Pair counts in the thousands do not change this. 744 test pairs come from 13
programs, and resampling pairs rather than programs is what made the published
interval narrower than it should have been.

## Corpus realism

Every program is a self-contained, single-file, synthetic exercise with its own
self-test, written for this benchmark. None comes from a real project, none has
dependencies, none exceeds a few hundred lines. Results here say nothing about
production code, and the corpus's uniform structure — a `test_*` driver in 62 of
64 files — is exactly what produced the protocol defect described in
`docs/current/EVALUATION_PROTOCOL.md`.

## Protocol coverage

The output-free protocol requires an entry function whose parameters can be
supplied from a fixed type battery. 41 of 64 corpus programs qualify. The 23
that do not are mostly class-based (`ds_hash_table`, `api_rate_limiter`,
`fsm_vending_machine`, …), and they are not a random sample: they are the
programs with state, which is precisely where a *state*-transition genome
should have the most to say. The corrected evaluation therefore runs on the
easier half of the corpus, and that biases it in SBG's favour in a way the
numbers do not show.

Extending the protocol to class-based programs needs a way to drive an object
through a sequence of method calls without hand-writing a driver per program.
That is unsolved here.

## The distance function

`distance_v5 = 0.50·d_v3 + 0.25·d_temporal + 0.25·d_state` has fixed weights
that were never fitted. On the statistically valid test set the combination
scores below two of its own components, so the weighting is losing information
rather than combining it. A learned combination fitted on dev and evaluated on
the frozen test set would settle whether the representation or the distance
formula is the limit — it has not been run, and until it is, "the
representation is weak" is not separable from "these weights are wrong".

## Threshold

τ\* = 0.08 is the median SBG distance of semantics-preserving dev pairs, fixed
before the hard negatives and the regression corpus were scored. It was chosen
under the published protocol and has not been re-derived for the output-free
protocol, whose distance distribution differs. The hard-negative and regression
numbers should be read as "at this threshold", not as the best achievable
operating point — and re-deriving the threshold on test data would be exactly
the leak the fixed value exists to prevent.

## Statistical power

With 13 clusters, a clustered bootstrap has limited resolution and the paired
comparisons detect only large differences. The one comparison that survives
Holm correction (SBG V5 versus the V3 exception component) is a difference of
about 0.05 AUROC. Smaller real differences would not be detected here, so a
non-significant comparison is not evidence of equivalence.

## External validation

The QuixBugs, BugsInPy and Java cross-language results in `results/external/`
were **not** re-run or verified in this release. They use the same
entry-discovery code as the main benchmark, so they are subject to the same
protocol defect, and their status is unresolved rather than confirmed. They are
excluded from every claim in the README.

## Benchmark construction

The corrected benchmark's observability filter is a static over-approximation:
name-based call resolution marks a definition reachable whenever a matching
name appears anywhere in a reachable body. It can only mark *more* pairs
observable, so it is conservative for the purpose of removing false CHANGED
labels — but some pairs it admits may still be unobservable in practice.

The remaining EQUIVALENT pairs include 33 in the corrected test split whose
transformation touches only scaffolding. They are correctly labelled and they
are trivially easy.

## What a positive result here would and would not mean

The strongest supportable statement is about ranking pairs within a small set
of synthetic single-file Python programs, under a protocol that executes one
function per program over a fixed input battery. It is not a statement about
detecting regressions in real software, about languages other than Python, or
about programs whose behaviour depends on state, concurrency or I/O.
