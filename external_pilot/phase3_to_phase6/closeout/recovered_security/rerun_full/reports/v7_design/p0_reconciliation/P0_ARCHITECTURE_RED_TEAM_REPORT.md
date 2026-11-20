# SBG V7 P0 Architecture Red-Team Report

Reviewer role: independent adversarial architecture review. Scope: all 13 `SBG_V7_*.md` documents, `_sources/_DESIGN_SPINE.md`, and `reports/v6_redesign/SBG_V6_FINAL_CLAIM_EVIDENCE_MATRIX.md`, read in full. Nothing was executed; all arithmetic below is back-of-envelope from numbers quoted in those documents, with assumptions stated. The master plan was not trusted: where it conflicts with the detail documents, the detail documents were read as primary. Literature remarks marked (recollection) are from my own knowledge, not verified, and carry the same caveat the research review applies to itself.

Severity scale: Blocking = P0 cannot be frozen / a headline claim cannot be made as specified. Major = changes a conclusion or a budget by a large factor; fix before G0. Moderate = fix before the relevant phase. Minor = hygiene.

## 0. Summary table

| Q | Topic | Severity | One-line verdict |
|---|---|---|---|
| 1 | Witness comparison vs differential testing | Major | For the observable verdict it is differential testing plus replay. Not a differentiator. |
| 2 | Minimum defensible contribution | Major | Change-adequacy-gated differential testing with a label-free adequacy criterion, plus an adjudicated benchmark. Everything else is optional. |
| 3 | Internal-only divergence independent of SBG | Blocking | Not definable independently: the truth class is a function of the tool's own abstraction and alignment. |
| 4 | Sufficiency model | Major (Blocking for the S0-S3 ordinal as written) | Activation is meaningful; the rest is arbitrary or perverse (plateau rewards weak explorers). Four incompatible S definitions. |
| 5 | Benchmark leakage via adaptive exploration | Blocking | Primary comparison is not like-for-like: V7 gets diff knowledge the baselines lack; verdict correlates with edit size; FAR comparator is inconsistent. |
| 6 | Static context | Moderate | Helps activation accounting; adds unsupported "change is textually local" assumption. |
| 7 | Evidence fabric overhead | Major | Storage and ingest arithmetic breaks the stated budgets by 10-50x on real code. Fixable by storing recipes, not events. |
| 8 | Verdicts MECE and operational | Blocking | Not MECE across documents; counter-examples below; verdict is a function of the run, not the pair. |
| 9 | Nondeterminism | Major | Fixed-seed control plus replay creates confirmed false divergences; real distributional regressions are unrepresentable. |
| 10 | Unalignable versions | Moderate | Output-channel verdict is alignment-free; internal views must be gated on alignment trust, which no document does. |
| 11 | Partial instrumentation | Moderate | Must restrict the channel set and compare on the intersection of observed vocabulary; asymmetric instrumentation creates false divergence. |
| 12 | Scalability to real projects | Major | Input representation, Python version, thread/AS limits and import cost are unresolved; expect eligibility near V6's 28.5% unless fixed. |
| 13 | Power for the internal-only claim | Blocking | H7 (+3pp) is under-powered by roughly 7x in effect and about 40x in sample; the success rule is jointly unachievable at about 13-39% power even for V7-B. |
| 14 | Can V7-B deliver most value cheaply | Major (recommendation) | Yes. About 30 engineer-weeks versus 51, about half the software and a much earlier answer. |

Blocking issues: Q3, Q5, Q8, Q13 (and the S0-S3 ordinal inside Q4).

---

## Q1. Is witness-based comparison genuinely different from conventional differential testing?

Severity: Major. (Blocking if "witness-based" is used as the novelty claim.)

Evidence.
- COMPETING_ARCHITECTURES section 7, alternative (f): "Can assert: OBSERVATION (witness with input and divergent outputs)." Section 4, alternative (c): "each cheaper alternative (output diff) [is] a strict subset (channels = {return, exception})".
- MATH_SPEC P2: "OD(x) := terminal observations differ on C_out = {ret, exc, side}. OD does not depend on the alignment."
- MASTER_PLAN decision 1: `DIVERGENT_OBSERVABLE` is "sound by replay relative to the harness". Theorem 1 premises are A1, A2, A5 (faithful harness, determinism, correct normaliser), the same premises any differential tester carries.
- FINAL_DECISION s2: pure same-budget differential testing "tied the selected design at 19/24 ... The composite is a bet".

Analysis. A witness is (input, two observations that differ). Every differential tester emits that. What V7 adds on the observable verdict: (a) replay in a fresh sandbox, which is routine flake filtering; (b) provenance hashing, which is engineering; (c) first-divergence locus, which is an alignment-dependent upper bound (MATH_SPEC P3, L3); (d) the state channel, which is unvalidated (L12) and, per the protocol, never verdict-bearing. The only parts that are not already differential testing are the sufficiency-gated NO_DIVERGENCE_OBSERVED/INSUFFICIENT semantics and the internal-state channel. The architecture itself concedes this by making (f) a strict subset of (c).

Resolution.
1. State the thesis as "differential testing plus change-adequacy gating (plus optional internal guidance)". Remove "witness-based" as a claimed differentiator.
2. Make B1 literally the V7 pipeline with C = {ret, exc, side}, same sandbox, same explorer, no sufficiency gate. Then every measured gain is attributable to a named component.
3. Add the baselines the research review itself omits: a changed-line (patch) coverage gate on top of B1 (this is routine industry practice for "was the change exercised"), a diff-directed output-only fuzzer, and a Python symbolic differ (CrossHair `diffbehavior`, recollection; verify), Pynguin and Hypothesis-based differencing (recollection).

---

## Q2. Minimum scientifically defensible contribution beyond existing tools

Severity: Major.

Evidence. RESEARCH_AND_NOVELTY_REVIEW bottom line: "the core primitives are old. SBG's defensible contribution is the discipline (never conflate 'no difference observed' with equivalence), the unified verdict taxonomy, and a rigorous evaluation." Risk R26 (H/H) says the same. The review's literature is metadata-verified at best and never read in full text.

Analysis. A verdict taxonomy that never says "equivalent" is a reporting convention, not a result. Theorem 2 (the `x == 123456789` construction) shows no sufficiency value converts NDO to equivalence, so the only scientific content of the NDO verdict is empirical: how often is "NDO under criterion Z" wrong on real regressions, and does Z beat the existing practice (differential testing plus patch coverage)?

Proposed minimum claim (one sentence, pre-registrable): On project-disjoint, independently adjudicated real Python regressions, at equal CPU, a differential tester that (i) is diff-directed and (ii) emits NO_DIVERGENCE_OBSERVED only when a label-free change-adequacy criterion is met, has a lower false-assurance rate at decided coverage >= 0.6 than (a) undirected differential testing with a patch-coverage gate and (b) diff-directed differential testing with a patch-coverage gate. Report as an estimate with a CI and a stated smallest effect of interest, not as a Holm superiority test (see Q13).

What would make it a contribution even if the effect is null: the released adjudicated benchmark, the truth-harness protocol, and a measured false-assurance rate for the field's implicit practice (patch coverage + no difference found = pass). I cannot confirm from this repo whether that rate has been published; mark as unverified.

Everything else (alignment, state abstraction, impact, invariants, J, formal tier) is non-minimal and must be admitted only by the retain-or-drop rule.

---

## Q3. Can internal-only divergence be established independently of the SBG algorithm?

Severity: Blocking (for the INTERNAL_ONLY truth class, H8, validation row 9(a), and V7-A).

Evidence.
- PROTOCOL s1: `INTERNAL_ONLY` = "internal state differs but no interface difference exists in the declared domain".
- MATH_SPEC 3.5: "The declaration (d, p, L_s, eps_f, P, N) is part of the harness ... Changing it can change a verdict." L11: "Divergences hidden by these choices are not detected, and those revealed by fine settings may be representation artefacts." P3: the observed first divergence is only an upper bound. L1: "Behaviour-preserving refactoring ... produce[s] divergence."
- RISK R04: "internals differ, behaviour does not, so DIVERGENT_INTERNAL_ONLY has a high false-alarm rate."

Analysis. "Internal state differs" has no meaning without (i) which state points (set P), (ii) which abstraction (alpha, d, p), (iii) which alignment phi. Those are exactly the SBG algorithm's own choices. An "independent truth harness" can reimplement them but cannot be independent of the definition: it inherits the same concept. Second, the class is nearly vacuous. For any non-identical code with different data flow, internal state at some chosen point differs, so INTERNAL_ONLY is approximately "Eq-B with different code". The Eq-B / INTERNAL_ONLY boundary is set by the tool's own sampling points. Third, the truth label is domain-relative: "no interface difference exists in the declared domain" is itself established by T1 (bounded exhaustive or >= 10^5 inputs, PROTOCOL 3.5), so INTERNAL_ONLY truth is only as strong as a heavy fuzzer's reach (see Q13, assumption 9).

What can be independent is the interface oracle. The measurable quantity of internal-state value is therefore not "internal divergences detected" but "interface witnesses exposed that a no-internal-view tool missed at equal budget" (this is H7, correctly framed). That measures internal state as search guidance, with truth from the independent interface oracle.

Resolution.
1. Delete INTERNAL_ONLY as a verdict value and as a truth class. Keep `internal_diff: {input, locus, view, alignment_trust}` as an attribute attached to any verdict, labelled diagnostic.
2. Delete H8 and validation row 9(a) as acceptance criteria (their pass condition depends on a label the tool helps define). Keep row 9(b) (masked on common inputs, exposed on a rare region, truth from independent oracle) as the only internal-state test.
3. Measure internal state only as guidance gain on interface truth (see V7-A conditions below).

---

## Q4. Is the sufficiency model meaningful or arbitrary coverage thresholds?

Severity: Major overall; Blocking for the S0-S3 ordinal as currently written.

Evidence: four mutually incompatible definitions.
- MATH_SPEC 6.7/8.1: continuous S = gamma * act^w1 * cov^w2 * sat^w3 * obs^w4 with weights 1/4 and "floors ... values are experiment parameters"; NDO iff all four floors met. `k0` for BUDGET is "a declared constant".
- PROTOCOL s1: "S1 = every changed region activated at least once on both versions; S2 = S1 and branch/state coverage >= 80% of the statically reachable branches ... S3 = S2 and the divergence-discovery curve has plateaued (no new coverage ... in the last 25% of the budget)."
- ROADMAP s2: "S1 = activated by at least one input; S2 = activated with distinct paths/state classes above a stated count; S3 = budget exhausted without new coverage".
- SCHEMA 2.15: "S1: reached, few inputs; S2: reached, both branch directions ...; S3: S2 + state saturation + formal tier agrees (if run)".
- NDO admission: MASTER_PLAN lists NDO "at sufficiency S0-S3"; PROTOCOL says S0 cannot be emitted as NDO; CONTRACTS I and SCHEMA T3 admit NDO at level >= S1. S1 is one input touching the change.

Analysis.
- Meaningful kernel: activation (the changed code ran). This is a necessary condition and equals what industry calls patch coverage. Report it as a count, not a level.
- Perverse: plateau/saturation. "No new coverage in the last 25% of budget" measures the explorer's reach, not the input space. A weaker explorer saturates earlier and earns S3; a stronger one keeps finding new coverage and never does. S3 therefore rewards weak exploration. Roadmap's "S3 = budget exhausted" is the opposite of assurance.
- Arbitrary: 80% branch coverage over "statically reachable branches" (over-approximated; dead and exception branches make 80% unattainable), the 25% window, the 0.35/0.20/0.10 caps, floors f_*, w_i, k0, and the partition Pi in 6.3 (declared after seeing benchmarks). Theorem 2 already shows S = 1 is compatible with divergence.
- Calibration is not estimable at the planned sample size (Q13): the S1/S2/S3 NDO strata would hold roughly 10-15 Div misses in total.

Resolution: replace the ordinal with a label-free, mechanism-grounded adequacy measure.
1. Report activation as raw counts: changed blocks and changed predicates hit, both branch directions, by both versions.
2. Define change adequacy A_chg = fraction of first-order mutants of the changed blocks of the new version (relational flip, constant +/-1, boundary shift, condition negation, statement deletion) that the explored input set kills under the same output channel. This answers the question the verdict asserts ("had the change differed here, would we have noticed?"). It turns Theorem 2's counter-example into low adequacy (mutant `x == 123456790` is not killed). Cap cost at 20% of budget with early exit per mutant. Equivalent mutants add noise; report the surviving mutant list as actionable evidence.
3. NDO requires pre-registered thresholds on activation and A_chg, set on a development split. No S ordinal, no "S3", no formal-tier clause.
4. Calibration without adjudicated labels: planted-fault recall. Because A_chg is computed from planted faults, its calibration (empirical kill rate of planted faults per adequacy stratum) can use thousands of planted faults per pair, removing the power problem. External validity is then checked once on the real set as a descriptive estimate.
5. Drop the saturation factor from any verdict condition. It may be logged.

---

## Q5. Can adaptive exploration introduce benchmark leakage?

Severity: Blocking (primary comparison is not like-for-like).

Evidence and findings.

(a) Information asymmetry in the primary comparison. MODULE_CONTRACTS A: exploration receives "SourceMapping x2 + changed-region set (from C)", directed scheduling uses AFLGo-style distance to changed blocks, and ROADMAP P4 seeds a "literal-pool from static context". PROTOCOL B1 is "same input generator family but undirected" and B2 is an "off-the-shelf coverage-guided Python fuzzer". Neither baseline sees the diff. A new-version literal in a changed guard (`if x == 123456789`) is exactly the witness input; reading the diff is how directed tools (and shadow symbolic execution) win. Gains on H2/H3/H4 would be attributed to V7 but come from diff awareness. Hence the "equal budget" comparison is equal-CPU, not equal-information.

(b) Verdict and sufficiency correlate with edit size, which correlates with label. Activation and coverage denominators are functions of changed-region size (C notes `region_size_fraction`). Fix commits are small and local; behaviour-preserving controls (renames, extract/inline, moves) are large. Large regions get lower act/cov and lower alignment trust, hence INSUFFICIENT. V7 then abstains on exactly the Eq-B-looking diffs, looking good on risk-coverage by selecting on diff shape. The protocol's shortcut probe (6.1) tests label versus edit size only. It does not test verdict or sufficiency versus label conditional on edit size.

(c) FAR comparator inconsistency (gameable). PROTOCOL H4 compares to "Plain DT's implicit 'no diff found = pass'". PROTOCOL s4 says B1/B2 emit the same three-valued output with the same S0-S3 gate "where possible". GATES C.1 item 3 uses the implicit-pass comparator. Any tool plus any abstention rule reduces FAR against an ungated pass; that is not V7's contribution. The fair test is V7 versus B1 plus the same gate at matched decided coverage (H5 does this; C.1 item 3 does not).

(d) Tuning parity is nominal. "Same number of tuning configurations" is not equal degrees of freedom. V7 exposes at least 20 knobs (d, p, L_s, eps_f, P, N, theta, gap penalty, w1..w4, k0, K_sat, f_act/f_cov/f_sat/f_obs, Pi, channel weights omega, 80%, 25%, window sizes); B2 has about 3-5.

(e) Authored-suite construction. H-M families "rarely-reached branch guards", "masked internal changes" are authored by people who know what the tool observes; row 9(b) on suite C is circular in the other direction (R05 acknowledges). Hard stratum = "truth=Div and seed-corpus outputs equal" is defined by the shared seed corpus, so replay-only detection is zero by construction on that stratum for both arms; H2/H7 there test generation, not state.

(f) What the leakage controls do and do not cover. Label-withheld byte-identical outputs (PROTOCOL 6.5, GATES D.1.6) detect illegitimate access. They cannot detect legitimate-but-label-correlated inputs (diff shape, new-version docstrings and literals, commit-type artefacts). New-version docstrings are in the "docstrings" the explorer may read (PROTOCOL 3.3.6) and a fix often rewrites them.

(g) Seeds and benchmark tuning. Five fixed seeds are fine. The design thresholds (K2 35%/60%, K3 +15pp) were set after reading V6 failure lists on BugsInPy/QuixBugs (R-26 residual contamination), and G1 uses those sets as "development targets" for exactly the quantity the design was shaped around.

Resolution.
1. Give B1 and B2 the same diff-derived information: add B1-directed (changed-region coverage reward, literal and boundary seeds from the diff, output-only comparison) and B2-directed (AFLGo-style). Then V7's marginal value over B1-directed is the true effect.
2. Add a diff-shape control: report verdict/sufficiency versus label within edit-size tertiles; train a diff-only classifier on sufficiency-vector components excluding witnesses and report its AUROC; require <= 0.65 or report the matched subset as primary.
3. Replace C.1 item 3 with FAR versus B1-directed plus identical gate at matched decided coverage.
4. Count and report tunable parameters; give baselines an equal random-search budget over their own knobs, not equal number of "configurations".
5. Strip docstrings and comments (new version) from the explorer's view, or run the explorer on old-version docs only; log all files opened (already planned).
6. Move design thresholds that were shaped by V6 failures into a stated "contaminated design prior" list, and require every primary claim to hold on H-R and H-X, which were not visible at design time.

---

## Q6. Does static context improve interpretation or add unsupported assumptions?

Severity: Moderate.

Evidence. CONTRACTS C ("deliberately minimal": AST/CFG, changed regions, signatures); MATH 6.1-6.2, 6.9 last bullet ("S says nothing about unchanged code whose behaviour changed through a changed dependency not represented in R"); CONTRACTS C failure modes (over-large regions, move/rename mis-detected as add+del).

Improves interpretation: yes, for INSUFFICIENT. A concrete list of unhit changed blocks is actionable, and distinguishes NOT_ACTIVATED from unsupported-signature cases.

Unsupported assumptions it adds.
1. Textual locality: behaviour change is located in the diff hunks. False for dependency or config changes, native-code changes (a Python AST diff sees nothing), changed class hierarchies, decorators, monkeypatches, and changed callees outside the diff.
2. Activation granularity: weights w(b) = 1 dilute a 30-line fix inside a 300-line rename; act becomes dominated by trivial blocks.
3. Matching correctness: GumTree-type matchers mis-handle moves; R then mixes "moved" and "changed". R determines the activation denominator, so matcher errors feed sufficiency directly.
4. Activation implies reaching a differing state (admitted in 6.9).

Resolution. Keep C to changed blocks/predicates plus signatures. Weight activation by changed predicates and statements rather than blocks. Add a label-free validity metric for R: the witness-outside-R rate (fraction of witnesses whose locus lies outside R or its static dependents). If above about 5% on development data, activation floors are untrustworthy and must be widened or the scope declared. Treat dependency/config/native diffs as explicit INSUFFICIENT(UNMODELLED_CHANGE) reasons, not silent "no change".

---

## Q7. Can the evidence fabric keep provenance without excessive storage/runtime overhead?

Severity: Major.

Inputs quoted from the documents (they disagree by 5x): SCHEMA s6 "~12 B compressed per event"; ROADMAP P1 "<= 40 B/event compressed", P0 "<= 60 B/event after zstd". Events per run: SCHEMA "L1 50-500", CONTRACTS cap 200,000 at L1, ROADMAP cap 1,000,000. Runs per pair: CONTRACTS "300 inputs x 2 versions x 2 repeats = 1200 runs"; PROTOCOL needs >= 3 repeats and 5/5 witness replays; ROADMAP default repeat k = 5 and "<= 5000 execs/pair". Ingest: CONTRACTS D "~1-5 MB/s per core in Python". Budget: PROTOCOL "60 CPU-s per pair including all V7 overhead"; ROADMAP "60 s wall-clock, 4 cores" (= 240 CPU-s); CONTRACTS A "60 s CPU". Three different budget definitions.

Arithmetic (assume 120 B raw canonical record per event, which is generous given site, payload and AbstractValue fields).

| Scenario | Events/run | Runs/pair | Events/pair | Stored (12 / 40 / 60 B) | Raw ingest at 5 / 1 MB/s |
|---|---|---|---|---|---|
| Small unit (design case) | 300 | 1,200 | 0.36 M | 4.3 / 14 / 22 MB | 9 s / 43 s |
| Real function, 20k events | 20,000 | 1,200 | 24 M | 0.29 / 0.96 / 1.4 GB | 580 s / 2,900 s |
| Same, repeats k=5, 5000 execs | 20,000 | 50,000 | 1,000 M | 12 / 40 / 60 GB | 24,000 s+ |

Consequences.
- Small units: ingest alone consumes 15-70% of a 60 CPU-s budget, breaking the "overhead <= 25% of per-pair budget" retain rule at the pessimistic end.
- Real code: ingest is 10-48x the whole 60 s budget, so either the "all overhead charged" equal-budget definition is not honoured or event volume must drop about 50x.
- Holdout: 300 pairs x 5 seeds = 1,500 pair-runs x 0.3-1.4 GB = 0.45-2.1 TB versus the roadmap's "peak storage <= 200 GB" (7-30x over) and "<= 50 MB p99 per pair".
- Dedup claim: chunks hash `{run, first_seq, prev_chunk_hash}` plus bytes that contain `site.line`, so repeats dedup (at most k-fold) but cross-version prefixes do not, because `payload_hash` excludes line while the chunk bytes include it.
- Tracer callback cost alone is about 1 microsecond or more per event in Python; 24 M events is 24+ CPU-s before any hashing.

Can provenance be kept cheaply? Yes, by changing what provenance is: store the replay recipe, not the events.
1. Default run record = {program hash, input hash, environment hash, outcome, chain_root computed by incremental `hashlib` inside the child, changed-region coverage bitmap, completeness summary}. About 300 B per run. 1,200 runs = 0.36 MB per pair.
2. Full event chunks only for (a) witness runs, (b) a 5% audit sample (CONTRACTS L already proposes 5%), (c) runs escalated to L2/L3. Regenerate on demand by deterministic replay (the design already claims replay).
3. Estimate: <= 20 witness runs x 20k events x 40 B = 16 MB per pair worst case; 1,500 pair-runs = 24 GB, well under 200 GB.
4. Hash in the child process with C-level hashing; do canonical JSON only for stored chunks.
5. Charge ingest and hashing to the CPU budget explicitly, and give baselines the same per-run process cost (fork per run is the dominant cost for small units; the instrumentation ratio is then irrelevant to equal-budget claims).
6. Reconcile the three budget definitions into one (recommend CPU-seconds summed over all processes, as in PROTOCOL s7), and delete the wall x cores variant.

---

## Q8. Are the verdicts mutually exclusive, collectively exhaustive, and operational?

Severity: Blocking.

Evidence of inconsistency across documents.
- Verdict set: MASTER_PLAN and ROADMAP s2 have four values (`DIVERGENT_OBSERVABLE`, `DIVERGENT_INTERNAL_ONLY`, `NO_DIVERGENCE_OBSERVED`, `INSUFFICIENT`). SCHEMA 2.16 and MATH 8.1 have three values; internal-only is a `reason_code` (`internal_only_difference`) under DIVERGENT and MATH's DIVERGENT is defined over C possibly = Ch (so internal-only is DIVERGENT). PROTOCOL treats INTERNAL_ONLY as a truth class and a DIVERGENT on it as a false alarm (H8). MASTER_PLAN s5 admits "must be propagated".
- Reason codes: three incompatible vocabularies (MATH 8.1: NONDETERMINISTIC, IMPORT_FAILURE, ...; PROTOCOL: NONDET, UNDRIVABLE, TIMEOUT, PARTIAL_INSTRUMENTATION, ...; SCHEMA: `alignment_failed`, `blind_spot_dominant`, `capture_truncated`, `unsafe_program`, ...). `alignment_failed` exists only in the schema.
- Sufficiency: four definitions (Q4). NDO admitted at S0 / S1 / S2 depending on the document.
- Missing terminal: UNCHANGED yields "no verdict" (MATH 6.1) but is not in any enum.
- Error definition in metrics: H4/H5 define error as NDO on Div, or DIVERGENT on Eq-B; the value `DIVERGENT_INTERNAL_ONLY` on a Div truth pair is neither correct nor wrong.

Counter-examples (constructed against MATH 8.1 and the master plan).

| # | Pair | What the rules produce | Defect |
|---|---|---|---|
| C1 | Scope has two changed functions. On function f1, input x1 yields a replay-confirmed output difference. On f2, the changed region is never activated and x7 is nondeterministic. | DIVERGENT by rule 2 (priority), carrying a SufficiencyRecord that may be S0 (schema requires sufficiency "for all three values"). | Not a defect of exclusivity (ordering resolves it) but the record is incoherent: a DIVERGENT verdict with S0 sufficiency. Metrics must define that sufficiency is not scored for DIVERGENT. Also `gamma` is per-pair in 6.6 yet delta_det is per-(V,x,E). |
| C2 | Internal-only difference on x1, observable difference on x2. | MATH: DIVERGENT (x2 witness). Master plan: INTERNAL_ONLY on x1 and OBSERVABLE on x2 with no aggregation rule. If exploration stops at the first divergence (TTFW is measured), the run returns INTERNAL_ONLY for a truth-Div pair. | Pair verdict is undefined or exploration-order dependent. Metric hole: neither false assurance nor correct. |
| C3 | V2 returns 1 with probability 0.9 under uncontrolled randomness; V1 always returns 0. | V2 fails self-consistency (V2 vs V2 differ at the locus), so MATH 5.8 refuses a witness; 8.1 rule 3 gives INSUFFICIENT(FLAKY_DIVERGENCE) forever. With the protocol's 5/5 replay rule P(DIVERGENT) = 0.9^5 = 0.59 (if self-consistency is waived), 0.5^5 = 0.03 for p = 0.5. | A genuine distributional regression is unrepresentable, and where representable the verdict is a coin flip over replay count. |
| C4 | Extract-function refactor, C includes the state channel. | Inserted `call`/`ret` state points have no counterpart: step I(j) with ob_state present is non-conforming (MATH 5.6), so DIVERGENT. | Failed alignment yields a false DIVERGENT. `amb(A_v) > 0` is "reported" but never gates the verdict. `alignment_failed` is not in the MATH reason-code set. |
| C5 | Fix commit adds a parameter or changes the signature. | UNSUPPORTED_SIGNATURE, hence INSUFFICIENT (MATH 1.2). | Truth is Div (calls with the old signature raise in the new version). Counted as a miss, and it is a selection effect: signature-changing fixes are excluded from the comparable set. |
| C6 | Divergence only in a `resource` kind (SCHEMA lists `kind: resource`) | PROTOCOL rubric says performance-only changes are not divergence; MATH C_out = {ret, exc, side}. | Enum and rubric disagree. |
| C7 | Message-only exception difference | Channel flag "default off" (PROTOCOL 1, row 7). | Verdict depends on configuration; acceptable only if the configuration is part of the verdict identity, which SCHEMA 2.16 does not include. |
| C8 | Same pair, two seeds | Seed 1 finds a witness, seed 2 does not (adaptive exploration). | Verdict is a function of the run, not the pair (MATH 8.2 corollary admits NDO and INSUFFICIENT are not monotone in X_n). "The verdict" for FAR is undefined without naming the seed policy. |

Resolution: one normative verdict spec.
1. Two-level structure. Per-input outcome o(x) in {OBS_DIFF_CONFIRMED, OBS_DIFF_UNCONFIRMED, INTERNAL_DIFF_ONLY, SAME, NO_RUN(reason)}. Pair verdict by fixed precedence:
   - DIVERGENT_OBSERVABLE iff some x has OBS_DIFF_CONFIRMED under perturbation-robust replay (Q9); kind in {outcome, exception, side_effect, api}.
   - else INSUFFICIENT iff any OBS_DIFF_UNCONFIRMED, any nondeterminism on a compared channel, any floor unmet, scope not comparable, or unmodelled change; reason codes from one closed list.
   - else NO_DIVERGENCE_OBSERVED with the adequacy vector (Q4).
   - UNCHANGED and OUT_OF_SCOPE are explicit terminal states, not verdicts.
   Exclusive and exhaustive by construction (ordered rules, final else).
2. `internal_diff` is an attribute on any verdict, never a value.
3. Signature-incompatible scope: classify `api` divergence (call with the old signature fails in the new version, excluding added parameters with defaults) as DIVERGENT_OBSERVABLE, not INSUFFICIENT.
4. Verdict identity = (pair, scope, channel config, harness declaration, seed policy). FAR and Det are defined per seed and reported across the five seeds.
5. Add a pre-registered distributional verdict path: `DIVERGENT_DISTRIBUTIONAL` using R >= 20 seeded reruns per version and a pre-declared two-sample test with effect-size floor, or explicitly document it as out of scope and counted INSUFFICIENT(NONDET) in the abstention report.
6. Metrics: DIVERGENT on truth Div is a TP regardless of attribute; define sufficiency scoring only for NDO.

---

## Q9. Nondeterminism without false divergence

Severity: Major.

Evidence. CONTRACTS B.3: `PYTHONHASHSEED=0`, `random.seed(random_seed)`, virtual clock advancing `tick_ns` per call, `os.urandom/uuid/secrets` patched to a seeded stream. PROTOCOL 9: >= 3 repeats; witness must reproduce 5/5. MATH 5.8: self-consistency of V1-V1 and V2-V2 at the locus. GATES row 11: injected nondeterminism flagged >= 95%.

Analysis.
1. Fixed-seed control is not behaviour-preserving across versions. Same seed does not mean same behaviour after a change in the number or order of RNG draws, clock reads (virtual clock advances per call, so an extra `time.time()` shifts every later timestamp), or the insertion order into sets of strings (hash seed fixed, iteration order still depends on construction). A pure refactor then produces a divergence that is deterministic, replays 5/5 and has V1-V1 and V2-V2 self-consistency. Replay confirmation cannot catch it because the controls removed the variability replay would expose. This is a confirmed false divergence, and it contradicts "sound by replay".
2. Real distributional regressions are unrepresentable (C3 in Q8).
3. Native sources: BLAS thread-order float summation, `id()`-dependent ordering, GC-timing `__del__` effects, C-level clocks. The documented thread ban patches `threading.Thread.start` but does not pin native BLAS/OpenMP threads.
4. Import-time state: a pre-imported fork template freezes import-time randomness per version template; two version templates can differ for reasons unrelated to the change.

Resolution.
1. Perturbation-robust witnesses. A DIVERGENT witness must replay under k >= 3 distinct control settings (random seed, hash seed, clock origin/tick) on both versions, with V1 outputs invariant across settings on x (else the input is control-sensitive). Cost multiplies only witness replays (cheap).
2. RNG/clock/set-order sensitivity flag: if the changed region or its callees consult RNG or clock, route to the distributional path or INSUFFICIENT(ENV_SENSITIVE) with the evidence of which source.
3. Pin native threads (OMP_NUM_THREADS=1 and equivalents) and add them to the determinism report; compare floats under declared tolerance and record it in the verdict identity.
4. Install virtualisation before import in both templates; verify template-vs-cold-start equivalence on a fixture suite.
5. Row 11 variant (b) ("nondeterminism controllable by seed/clock freeze: normal verdict after control") must be split: the test fixture set needs refactor-induced RNG-order changes expecting INSUFFICIENT or non-divergent, not a normal verdict.

---

## Q10. What happens when versions cannot be aligned?

Severity: Moderate.

Evidence. MATH 5.3-5.4 (phi partial, alignment ambiguity reported), 5.6 (steps D(i)/I(j)); SCHEMA reason code `alignment_failed`; ROADMAP R14 ("low confidence degrades to INSUFFICIENT"; fallback "Compare only at call/return boundaries"); CONTRACTS G ("unaligned_fraction rises ... I downgrades").

Analysis. The output-channel comparison needs no alignment (MATH P2), so DIVERGENT_OBSERVABLE is unaffected. Alignment matters for (i) internal views, (ii) first-divergence locus, (iii) function-level cov partitions Pi_u when functions are renamed, split or merged. Activation (hit(b) per version) does not need phi.

Gap: no document makes the verdict depend on alignment trust. MATH 5.6 only reports `amb`. SCHEMA has `alignment_trust` but no gate.

Resolution.
1. Degrade the channel set, not the verdict class. When alignment trust at the locus is below a pre-registered threshold (set on the refactor corpus; the R14 indicator is "node-level F1 < 0.90"), internal views are excluded from the verdict and the locus is reported as `unlocalised`.
2. Scope lifting: if entry symbol s no longer exists or changed incompatibly, retry at the outermost frame whose symbol exists in both versions; record the lifted scope in the verdict identity.
3. Internal-view DIVERGENT-like attributes require trust >= threshold; otherwise omit.
4. Report the unalignable fraction as a first-class abstention-reason statistic on refactor-heavy data.
5. Do not use `amb` as a probability; gate on it.

---

## Q11. How should partial instrumentation affect the verdict?

Severity: Moderate.

Evidence. GATES row 12: "NDO capped below S2 when the changed region is outside instrumentation; INSUFFICIENT(PARTIAL_INSTRUMENTATION) when completeness is below the declared floor". SCHEMA 2.9 `blind_spots` are known only when audit hooks detect them. CONTRACTS B.1: `sys.monitoring` restricted to code objects of the program under test.

Analysis.
1. Output-channel DIVERGENT stays sound under any instrumentation blind spot (outputs are observed at the harness boundary). Partial instrumentation only weakens absence claims and internal views.
2. Activation denominators must be pessimistic: uninstrumentable changed units count as unhit. In MATH 6.2 R comes from the static diff, so uninstrumented executed code yields hit = false (conservative). Do not shrink R to the instrumented subset (that inflates act).
3. Asymmetric instrumentation creates false internal divergences: old pure-Python loop versus new `sum()`/NumPy/C-extension call, or code moved into `exec`, a thread or a subprocess. Event streams differ for instrumentation reasons, not behavioural ones.
4. Changes outside Python AST visibility (C extension sources, data files, config, dependency versions) produce empty R and "no verdict" (MATH 6.1) even though behaviour may have changed.
5. "Changed region outside instrumentation" is knowable only for detected blind spots (audit hooks); undetected native time sources are found only by repeat disagreement (SCHEMA 9.3).

Resolution.
1. Verdict channel set = intersection of observed event kinds across both versions at the locus ("common support"). Internal views adjacent to a blind-spot boundary are discarded with `truncated_by: dependence_blind_spot`.
2. NDO requires completeness >= floor on the changed region for both versions; otherwise INSUFFICIENT(PARTIAL_INSTRUMENTATION) carrying which unit kinds were unobserved.
3. Treat non-Python or non-code changes as explicit INSUFFICIENT(UNMODELLED_CHANGE), never UNCHANGED, unless a content hash proves byte equality of all declared inputs.
4. Row 12's "miss rate under partial instrumentation <= full + 2pp" is not testable without ground truth on partially instrumented real pairs; plant faults inside blind-spot code on authored units to measure it.

---

## Q12. Scalability beyond small deterministic programs (BugsInPy/Defects4J-like)

Severity: Major.

Evidence. V6 BugsInPy coverage 28.5% (nondeterminism 60, unsupported signature 49, import 4 of 200). G1 target: "decided-pair coverage >= 70% of drivable and >= 50% of all". Risk R38: build success "< 60% of candidate projects at K1" is an early indicator. CONTRACTS A: input vocabulary is "int, float, bool, str, bytes, list, map, struct" with "no promise for pointer-rich C or reflective Java"; SCHEMA 2.4 rejects any input without a registered canonical codec (`unserialisable_input`).

Findings.
1. Input representation is the unresolved core. Real scopes take `self`, requests, DataFrames, file handles, callbacks and pytest fixtures. Canonical typed values cover primitives only. "Replay" of existing tests means executing test code that builds objects; that is code, not a canonical value, so it fits neither `Input` nor the "same input" requirement (T7). Pickling recorded arguments is not version-neutral (classes change between versions). No document designs this.
2. Python version. The tracer is `sys.monitoring` (PEP 669, Python >= 3.12). BugsInPy-style environments pin old interpreters (3.6-3.8, recollection; verify). On those, the fallback is `sys.settrace` at roughly 20-60x, against budgets written for the 3.12 path ("<= 5x", "<= 25x").
3. Process and resource limits. `threading.Thread.start` raises: any program that transitively spawns a thread (logging queue handlers, ThreadPoolExecutor, tqdm monitor, many HTTP clients) becomes `unsupported_concurrency`. `RLIMIT_AS = 512 MiB` is likely to break NumPy/pandas-class imports and anything mapping large arenas (likely; verify). Process-per-run with import cost: pandas-class import is about 0.5-1.5 s; at a 60 CPU-s budget a cold start per run permits under 100 runs, so a pre-imported fork template is mandatory, and forking after importing BLAS/OpenMP is unsafe.
4. Global state and I/O. Module singletons, `lru_cache`, logging config, environment and locale reads, files and network. The design handles these by isolation (fresh process) and denial, converting many units into INSUFFICIENT. That is honest but is exactly the V6 observation failure.
5. Funnel arithmetic (assumptions: build success 0.6 per R38, drivable-and-deterministic 0.3-0.5, V6 baseline 0.285). Candidates needed for 150 Div pairs: 150 / (0.6 x 0.4) = about 625 post-T0 fix commits across at least 40 projects (about 15 per project, cap 8 pairs). Feasible only if mining yields that; unknown until K1.
6. Roadmap K1 (>= 100 pairs, 8 projects), K5 (>= 200 pairs, >= 60 divergent, >= 15 projects) and PROTOCOL (>= 150 Div + 150 controls, >= 40 projects, >= 30 clusters for inference) disagree.

Resolution.
1. Before P1 hardening, run a 2-3 week feasibility spike on 30 candidate projects measuring: environment build, drivable-scope fraction, input-representation coverage, determinism, activation by replay + Hypothesis + diff literals. Kill if < 35% (K2 values), which the roadmap already specifies; make it earlier and include input representation.
2. Define `Input` for object arguments by recorded constructor-recipe or fixture-reference (call the test fixture and snapshot the argument with a version-neutral codec for the declared types), and state the supported type set explicitly with an eligibility report.
3. Make the PEP 669 requirement a profile; budget the settrace path separately.
4. Replace the thread ban and `RLIMIT_AS` hard defaults with per-project profiles validated on the hostile suite.
5. Reconcile K1/K5/PROTOCOL targets to one table.

---

## Q13. Is the benchmark powered for the internal-only claim? (back-of-envelope; a separate agent runs simulations)

Severity: Blocking.

Evidence. PROTOCOL s8 admits "+5pp is at the edge of detectability; H7's +3pp is NOT powered in H-R alone". PROTOCOL s2: SUPPORTED needs Holm p < 0.05 and positive on both H-R and H-M. Targets: about 150 Div, >= 40 projects, per-project cap about 8.

Arithmetic.

(a) Headline superiority (V7-B vs B1, +5pp paired detection). n_div = 150, 40 clusters (about 3.75 pairs per cluster; deff = 1 + (m-1) rho = 1.3-1.8 for rho 0.1-0.3, or 2 using the protocol's m = 8). n_eff about 75-115. Assume discordance pi_d = 0.10. SE of the paired difference = sqrt(pi_d / n_eff) = 0.0365 (n_eff 75) to 0.0295 (n_eff 115). True-effect z = 0.05 / SE = 1.37-1.69. Power at alpha 0.05 two-sided: 0.28-0.39. With Holm across the 8 test family (first-step alpha 0.00625, critical z 2.50): 0.13-0.21. Required n_eff for 80% power at alpha 0.00625: pi_d x (3.34 / 0.05)^2 = 446; at 0.05: 314 (agrees with the protocol's own formula, which gives about 311 for pi = 0.10). That is 630-890 raw Div pairs versus 150. Requiring significance on both H-R and H-M multiplies the probabilities.

(b) H7 (+3pp internal-state gain on the hard stratum). Hard stratum is 27% of V6 synthetic changed pairs; real prevalence unknown (R06 H likelihood, K1 target of only >= 30 real masked cases). h = 40 (27% of 150) or 15 (10%). The paired sign test needs b wins and zero losses: b = 6 gives p = 2 x 0.5^6 = 0.031; b = 9 gives p = 0.0039 (Holm 0.00625). Minimum detectable gain: 6/40 = 15pp (alpha 0.05) to 9/40 = 22.5pp (Holm); with h = 15, 40pp. The pre-declared +3pp needs n_eff = ((1.96 sqrt(0.2) + 0.84 sqrt(0.2 - 0.0009)) / 0.03)^2 = 1,740 hard-stratum pairs (pi = 0.2). Under the protocol's own +10pp margin: 155 effective, about 310 raw hard pairs, or about 1,150 real Div pairs at 27% hard share, 3,100 at 10%. Conclusion: the internal-state claim is unfalsifiable on real data at the planned size; V7-A as defined can only be confirmed if the true effect is >= 15-40pp.

(c) Calibration (S ordering, ECE <= 0.05, caps). Assume Det 0.75: 38 of 150 Div pairs are not DIVERGENT; about 15 INSUFFICIENT, about 23 NDO. Controls 150 with decided fraction 0.65 gives about 98 decided, most NDO. Total NDO about 113 split over S1-S3; S3 holds about 38 pairs. Standard error of a 10% rate at n = 38 is 0.049, so ECE <= 0.05 is unestimable (noise alone equals the tolerance). Adjacent-level difference 0.35 vs 0.20 at n = 30 each: SE 0.114, z = 1.3, not separable. Certifying "S3 miss rate <= 0.10" at one-sided 95%: 2 misses needs n >= 63, 0 misses n >= 30; the design yields about 38 total with an expected 4 misses (upper bound about 0.23). Also, "ECE of the claim miss rate <= cap" is ill-defined, since caps are upper bounds, not predicted probabilities.

(d) Label depth caps measurable advantage. Eq-B truth requires T1 (bounded exhaustive or property-based >= 10^5 inputs with all changed branches covered; PROTOCOL 3.5). That is a heavy differential fuzzer. Pairs it misses are labelled Eq-B, so a V7 that finds a deeper (replay-valid) witness gets a "false alarm". The truth harness ceiling bounds measurable V7 advantage and penalises exactly the gain claimed.

(e) Multiplicity creep. K4 passes on "any of" three metrics (ROADMAP: +10pp masked recall and +3pp real, or 20% relative FAR reduction, or 25% fewer detection executions) while only one has a CI condition; ROADMAP K4, PROTOCOL H7 and GATES row 9(b) use different thresholds.

(f) Adjudication effort. ROADMAP budgets about 70 adjudicator-hours (6 pairs/hour) for 200 pairs. PROTOCOL needs two-rater labels for 150 controls plus ambiguous items, a T1 harness run per Eq-B, and 1,000 authored pairs; ROADMAP's own R08 says complex pairs take hours. The 14 ew for P7 is optimistic by a factor of two or more.

Resolution.
1. Reframe H2-H5 as estimation: pre-declare a smallest effect of interest, report the FAR difference with a cluster CI, and use fixed-sequence (gatekeeping) testing instead of Holm over eight tests. State in advance that "inconclusive" is expected if the CI spans the SESOI.
2. Size the real set to the headline effect (about 630-890 raw Div pairs for +5pp at pi_d = 0.1) or lower ambition to +10pp (n_eff about 155 at pi_d = 0.2).
3. Test internal-state value only on authored suites with programmatic generation and independent oracle, sized to about 310 hard-stratum base programs at SESOI 10pp; real data descriptive only.
4. Calibrate sufficiency on planted-fault recall (thousands of faults per pair, Q4) and validate on real pairs as a single descriptive estimate.
5. Fix the Eq-B depth problem: give truth harness heavier budget than any tested arm, and treat "DIVERGENT on Eq-B with a replay-valid, oracle-confirmed witness" as a label correction, not a false alarm.
6. Replace the K4 any-of rule with one primary metric with a CI.

---

## Q14. Could V7-B deliver most of the practical value at much lower cost?

Severity: Major (the answer is yes; this is a scoping recommendation).

Evidence. FINAL_DECISION s4: V7-B is "narrower, still legitimate". FINAL_DECISION s5 and RISK "strongest arguments" 1, 2: the V6 failures were observation (28.5% coverage, 36 input-less pairs, 69 NOT_ACTIVATED, return-blind channel), not representation; RISK argument 2: "V7 spends most effort (P5, P6, views, invariants) on the part that the failure analysis did not implicate". Coverage by requirement (FAILURE_TO_REQUIREMENT_MATRIX R-01..R-31): V7-B satisfies R-01..R-11, R-16 (partly, via changed-region distance), R-17..R-19, R-22..R-31, about 25 of 31. Not covered: R-12, R-13, R-14, R-15 (state, per-input state comparison, multi-view graph, alignment) and R-20, R-21 (prediction), all of which concern the scorer/representation direction that V6's evidence did not support.

Cost. Roadmap core is 51 ew (P0 3, P1 8, P2 5, P3 8, P4 10, P7 14, P8 3). V7-B below is about 31 ew (software about 19 ew), roughly 40% less overall and about half the software, with the answer arriving about 12-16 weeks earlier because the K4 thesis decision no longer gates it. It also removes risks R01, R04, R14, R17, R21 and most of R24.

---

## Minimum viable V7-B

Definition: a differential tester with a diff-directed explorer, a label-free change-adequacy gate, perturbation-robust replay, and a three-valued verdict with reason codes. No event log, no alignment, no state abstraction, no impact analysis, no hash-chained store.

| Module | Content | Effort (ew) |
|---|---|---|
| M0 Governance-lite | Prereg, freeze, amendment log, JSONL + sha256 manifest, ported V6 statistics (cluster bootstrap, permutation, Holm), contamination registry | 1.5 |
| M1 Capture-lite | Subprocess per run (T1) plus hostile suite; Linux container for third-party; determinism controls plus perturbation replay (Q9); outcome capture (ret, exc, declared side effects) via canonical value digests; changed-line/branch coverage only (coverage events, not an event log); recipe-based run records (Q7) | 5 |
| M2 Static-lite | AST diff to changed blocks/predicates, signatures, scope lifting, UNMODELLED_CHANGE detection | 2 |
| M3 Explorer-lite | Replay harvest from parent-commit tests/docs; Hypothesis/type-hint generators; diff literal and boundary seeds; changed-predicate coverage feedback; ddmin witness minimisation; no concolic | 5 |
| M4 Verdict + adequacy | Single normative verdict spec (Q8); change-adequacy via mutants of the changed blocks (Q4); reason codes; replay confirmation | 3 |
| M5 Baselines and harness | B1 (undirected), B1-directed, B1+patch-coverage gate, B2 (coverage-guided fuzzer), CrossHair-style differ (recollection), conventional features; equal-CPU accounting | 3 |
| M6 Benchmark | H-R only (>= 40 projects target) plus small authored rare-guard suite; truth harness; adjudication; sealing and custodian | 10 |
| M7 Sealed evaluation and report | Single-shot run, claim ledger, from-raw reproduction | 2 |
| Total | | about 31.5 ew |

Calendar: about 16-20 weeks (range 12-28) with two engineers, one benchmark engineer, 0.5 statistician and adjudicators; benchmark (M6) is the critical path and should start in week 1. Estimates scale the roadmap's own point estimates (P0 3 to 1.5, P1 8 to 5, P2 5 to 2, P3+adequacy 8 to 3, P4 10 to 5, P7 14 to 10, P8 3 to 2); I have no independent basis beyond that.

Gate before M1: the 2-3 week feasibility spike from Q12 (build success, drivable fraction, input representation, determinism, activation). Stop if activation by replay + Hypothesis + diff literals is < 35%.

Deliverable: a CLI/library `compare(old, new, scope, budget)` returning JSON `{verdict, kind, witness input + replay script, adequacy vector or reason code, channel config, seed policy}`; a frozen adjudicated Python regression benchmark with truth-harness code; a pre-registered report giving FAR, detection, risk-coverage and abstention breakdown versus the diff-aware baselines with CIs and an explicit statement of power.

---

## Recommendation on V7-A

Do not commit to V7-A in the V7 programme. Treat it as a gated, pre-registered follow-on pilot, attempted only if every condition holds.

1. Headroom: V7-B on the sealed holdout shows false-assurance >= 10% at decided coverage >= 0.6 on H-R (otherwise there is nothing for internal guidance to recover).
2. Cheap-first mechanism: the internal signal is alignment-free and verdict-free: digests of call/return values at the scope boundary and of unchanged-callee arguments, plus a branch-trace hash, used as a reward in the explorer (divergence-guided fuzzing). No alignment module, no INTERNAL_ONLY verdict, no state abstraction family.
3. Independent truth: authored suites, programmatically generated, >= 300 hard-stratum base programs (n_eff about 155 at +10pp, pi = 0.2), oracle written without access to tool output, fingerprint audit AUROC <= 0.60 leave-family-out.
4. Pre-registered SESOI: +10pp interface-witness yield at equal CPU on the hard stratum, paired cluster CI lower bound > 0, one primary metric (no any-of rule).
5. Cost cap: <= 12 ew for the pilot; kill on failure; no real-data confirmatory claim (real data descriptive only unless >= 300 independent real hard-stratum Div pairs exist).
6. A fresh sealed holdout (H-X) for any real-data confirmation; V6 and H-R development contamination disclosed.
7. Prior (judgment, not measurement): probability of passing condition 4 is low to moderate (about 25% or less). The expected value of V7-A is therefore lower than that of finishing V7-B cleanly.

---

## Ten most dangerous unstated assumptions

1. Exploration is label-independent. In fact diff knowledge (changed regions, new-version literals, new docstrings) is correlated with the label and with the information baselines lack (Q5a, Q5f).
2. The comparable scope is stable and not selected on the outcome. Signature-changing fixes are excluded as UNSUPPORTED_SIGNATURE yet are truth Div (Q8 C5); exclusion biases the benchmark toward easy bugs.
3. Inputs are serialisable canonical values. Real scopes take objects and fixtures; the input/replay model does not cover them (Q12.1).
4. Seed/clock/hash-seed control preserves the behaviour being compared. It does not, across refactors that change RNG draws, clock reads or set construction, and replay cannot detect it (Q9.1).
5. The tracer and sandbox apply to the target environments: Python >= 3.12, no transitive threads, 512 MiB address space, cheap imports (Q12.2-3).
6. Alignment accuracy is high enough for internal views, and its uncertainty can be reported rather than gated (Q8 C4, Q10).
7. Output equality after normaliser N equals contract equality. N (repr, float tolerance, ordering, message channel) is a per-project oracle choice (MATH A5), unspecified for real projects.
8. The textually changed region contains all behaviour-relevant change. Dependency, config, native and hierarchy effects fall outside R (Q6.1).
9. The truth harness is independent and stronger than the systems under test. Eq-B (T1) is a heavy fuzzer's reach, so it caps measurable gains and mislabels deeper findings (Q13d).
10. Adaptive saturation indicates sufficiency, and about 150 Div pairs can calibrate it. Saturation measures the explorer, not the input space, and sample sizes cannot estimate the calibration (Q4, Q13c).

Honourable mentions: equal CPU budget is a fair equal-information comparison (Q5a, Q7); 30+ projects are 30+ independent clusters (forks, shared maintainers, shared dependency pins); "post-T0" commits are uncontaminated by pretraining of any LLM-assisted tooling.

---

## Appendix A: cross-document inconsistencies to close in P0

| Item | Document A | Document B | Needed |
|---|---|---|---|
| Verdict set | MASTER_PLAN/ROADMAP: four values incl. `DIVERGENT_INTERNAL_ONLY` | SCHEMA/MATH: three values; PROTOCOL: INTERNAL_ONLY is a truth class (DIVERGENT on it is a false alarm) | One spec (Q8) |
| NDO admission | MASTER_PLAN: S0-S3 | PROTOCOL: S0 not emitted; CONTRACTS I/SCHEMA T3: level >= S1; MATH: floors | One rule |
| S0-S3 | PROTOCOL (80% branches, plateau) | ROADMAP (S3 = budget exhausted), SCHEMA (S3 = formal tier agrees), MATH (continuous S) | Replace (Q4) |
| Reason codes | MATH | PROTOCOL, SCHEMA | One closed list |
| Budget unit | PROTOCOL: 60 CPU-s all overhead | ROADMAP: 60 s wall x 4 cores x <= 5000 execs; CONTRACTS: 60 s CPU, 300 inputs | One definition |
| Repeats | CONTRACTS: >= 2 | PROTOCOL: >= 3 (5/5 replay); ROADMAP: k = 5 | One value |
| Bytes per event | SCHEMA: 12 | ROADMAP: 40 and 60 | Measure |
| FAR comparator | PROTOCOL H4/GATES C.1.3: implicit pass | PROTOCOL s4: same gate | Same-gate (Q5c) |
| Real-set size | ROADMAP K1/K5: >= 100 pairs/8 projects; >= 200 pairs/>= 60 Div/15 projects | PROTOCOL: >= 150 Div + 150 controls, >= 40 projects, >= 30 clusters; per-project cap 5% vs <= 8 | One table |
| K4 | ROADMAP: any-of three metrics | PROTOCOL H7; GATES row 9(b) | One metric |
| F module | MASTER_PLAN: removed | PROTOCOL ablations and GATES G3 still treat F as a module | Align |
| `resource` divergence | SCHEMA kind list includes it | PROTOCOL rubric: performance-only is not divergence | Align |
| Tracer reuse | MASTER_PLAN: not acceptable for claims (code-read in CONTRACTS) | ROADMAP: grep-only, verify in P1; REPO_INVENTORY lists it as reusable | Read-only audit first |

## Appendix B: items checked and not found wrong

Immutability and canonical-serialisation rules (SCHEMA 3-4) are coherent and the layered RAW/DERIVED/DECISION separation is sound. The labels-excluded-from-A-I rule, the "no EQUIVALENT verdict" rule, Theorem 2's counter-example, and the retain-or-drop ablation rule are good and should survive. The statistics plan (cluster bootstrap, no optional stopping, one-shot seal) is appropriate; the problem is sample size and the choice of confirmatory tests, not method.
