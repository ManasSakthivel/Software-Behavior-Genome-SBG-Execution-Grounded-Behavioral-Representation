# SBG V7: Mathematical Specification

Status: specification, no code. Companion: SBG_V7_COMPETING_ARCHITECTURES.md. Shared brief: _DESIGN_SPINE.md.

Every statement carries one of four epistemic classes. A definition is a convention and belongs to the class of the thing it defines.

- OBSERVATION: something a harness recorded in a run, or a deterministic function of recorded data. True relative to the harness (assumptions A1-A9, section 9).
- INFERENCE: a deterministic but heuristic derivation that goes beyond what was recorded (alignment, localisation, dependence reach). It can be wrong; it is reported with confidence or ambiguity.
- PROBABILISTIC ESTIMATE: a statement with a probability, valid only under stated sampling or exchangeability assumptions.
- FORMAL CLAIM: a theorem about the definitions, true by proof, with its premises stated.

---

## 0. Notation and symbol table

| symbol | meaning |
|---|---|
| V1, V2 | old and new program version (section 1) |
| s | scope: an entry point (module path, qualified symbol) with signature sig(s) |
| X_s | input domain of s (set of serialisable argument bundles incl. initial resource state) |
| x | an input, x in X_s |
| X_n | the finite set of inputs actually explored, X_n subset of X_s, |X_n| = n_in |
| E | environment (section 1) |
| H | harness: sandbox, tracer, abstraction alpha, normaliser N, instrumented channel set, budget B |
| B | budget (max events, steps, wall time, memory, inputs) |
| tau | a trace: finite sequence of events |
| e = (id, kind, loc, payload, t) | an event (section 2) |
| K | set of event kinds |
| Loc(V) | static locations (function, basic block, line) of version V |
| alpha_{d,p} | state abstraction with depth d and value-precision p |
| Ch | channel set {ret, exc, side, state} |
| C | a chosen subset of Ch (the observed channels) |
| ~_C | observation equivalence on events under C |
| v | a view in {ctl, call, dd} |
| phi | correspondence: partial injective map Loc(V1) -> Loc(V2) with confidence c |
| A | alignment of two traces (section 4) |
| delta | first-divergence step index (section 5) |
| w | a witness (section 5) |
| R | changed region: set of changed code units (section 6) |
| act, cov, sat, obs, gamma | sufficiency factors (section 6) |
| S | sufficiency score (section 6) |
| Verdict | one of DIVERGENT, NO_DIVERGENCE_OBSERVED, INSUFFICIENT (section 8) |

All sets are finite unless stated. "Iff" is used only for definitions and for theorems with proofs given.

---

# PART I. OBSERVATION

## 1. Program version, scope, input, environment

1.1 [OBSERVATION-convention] A program version is V = (src, deps, rt): source tree, resolved dependency set (names and exact versions), and language runtime identity (implementation and version). Two versions are compared only with the same rt, or with rt explicitly recorded as differing and included in V.

1.2 A scope s = (module, symbol) designates an entry point with a signature sig(s) giving parameter names and, if available, types. A scope is comparable iff sig(s) exists in both V1 and V2 and is compatible (same arity and parameter names up to a declared renaming). Otherwise the scope is UNSUPPORTED_SIGNATURE (reason code, section 8).

1.3 An input x in X_s is a serialisable bundle: argument values, plus the initial state of declared mutable resources (files, stdin, module globals) that the scope may read. Serialisation round-trips: decode(encode(x)) is observationally the same input for both versions (assumption A3).

1.4 An environment E = (E_c, E_u). E_c is the controlled part: random seed, hash seed, clock origin and rate, locale, environment variables, filesystem image, network stub, scheduling policy. E_u is the uncontrolled residue (true parallelism, real clock, OS entropy not intercepted). E is the same for both versions in a comparison (A6).

1.5 A harness H = (sandbox, tracer, alpha, N, C_inst, B). C_inst subset of Ch is the set of channels the harness can actually observe for this scope. B = (max_events, max_steps, max_wall, max_mem, max_inputs).

1.6 A run is the partial function run_H(V, x, E) = (tau, term) where tau is a trace and term in {RET, EXC, TIMEOUT, BUDGET, CRASH}. RET and EXC are normal terminations. Nothing else is assumed to be deterministic.

## 2. Execution as an event sequence

2.1 An event is e = (id, kind, loc, payload, t) where
- id: natural number, unique in the trace, id(e_i) = i;
- kind in K, with K containing at least {call, ret, exc, branch, line, read, write, io, alloc};
- loc in Loc(V): static location of the event;
- payload: abstracted data attached to the event (callee identity and argument abstraction for call; value abstraction for ret/read/write; exception type and normalised message for exc; target and byte abstraction for io; branch outcome for branch);
- t: logical timestamp, natural number, t(e_i) = i. Wall-clock time is never part of t and never compared.

2.2 A trace is tau = (e_1, ..., e_n) with n <= B.max_events. A trace carries truncated(tau) in {true, false}. Truncation makes every later claim about the trace a claim about its prefix only.

2.3 Read and write events carry an abstract location l in a finite-granularity location domain L (local variable of a frame, global, field of an abstract object identified by creation-site and allocation-order index, element-slot of a container as a single summary slot). The granularity is declared; coarser granularity conflates aliasing.

2.4 Run determinism evidence. For r >= 2 reruns under the same (V, x, E), define identical(tau, tau') iff same length and event-wise equal in (kind, loc, payload) after normalisation N. The determinism flag delta_det in {DET, CONTROLLED, UNCONTROLLED}: DET if all reruns are identical with no controls applied; CONTROLLED if they are identical only with E_c controls applied; UNCONTROLLED otherwise. This is an observation about r reruns only: it does not prove determinism on other inputs.

## 3. Observed state and the abstraction function

3.1 A concrete state sigma at a state point is (frames, heap): the call stack with local variable bindings and the heap graph reachable from the current frame, the arguments, and the globals referenced by the scope.

3.2 State abstraction alpha_{d,p}(sigma) is defined by traversal from the roots in a canonical order (sorted variable names; sets and mappings sorted by abstracted key):
- depth d in N: nodes at distance > d from a root are replaced by the marker TOP_d;
- precision p: a declared value abstraction for base values: p = exact for ints, bools, None, and strings up to length L_s; floats compared with declared tolerance eps_f (or rounded to declared significant digits); otherwise (type, length, content hash);
- identity: no memory addresses, no object ids, no default repr strings (these are the repr-artefact class, cf. SP-11). Shared and cyclic structure is encoded by traversal-order back-references.
alpha is a deterministic function of sigma and (d, p). It is not injective.

3.3 [FORMAL-flavoured lemma inside OBSERVATION definitions] Refinement. If (d', p') refines (d, p) (d' >= d and p' at least as discriminating), then alpha_{d',p'}(sigma) = alpha_{d',p'}(sigma') implies alpha_{d,p}(sigma) = alpha_{d,p}(sigma'). Consequently any divergence visible under a coarser abstraction is visible under every finer one. (Proof: coarser is a function of finer by forgetting.)

3.4 State points. State snapshots are taken only at events of kinds in a declared set P (default: call, ret, exc, and branch events inside changed regions). The observed state at event e in P is a(e) = alpha_{d,p}(sigma_e). This bounds cost and makes state comparison a comparison at selected points only.

3.5 The declaration (d, p, L_s, eps_f, P, N) is part of the harness and is recorded in every witness. Changing it can change a verdict; verdicts are only comparable under the same declaration.

## 4. Behavioural transitions, the induced LTS, and views

4.1 Label of an event: lambda(e) = (kind(e), loc(e)) (location may be coarsened to function or block).

4.2 Observed transition. For consecutive state points e_i, e_j in P (no state point between) in one trace, the observed transition is (a(e_i), lambda(e_j), a(e_j)).

4.3 Induced labelled transition system. For a version V and explored inputs X_n, with the set of traces T(V, X_n), define M(V, X_n) = (Q, Lambda, ->, Q0) where Q is the set of abstract states a(e) occurring in T, Lambda the set of labels, -> the set of observed transitions of 4.2 over all traces, Q0 the abstract states at entry of s. Same (q, lambda) may have several successors; nondeterminism is represented, not resolved.

4.4 [FORMAL, by construction] Monotone under-approximation. If X_n subset X_n', then ->(V, X_n) subset ->(V, X_n'). Each observed transition is realised by an actual run under the harness (given A1). Therefore the absence of a transition from M(V1, X_n) that is present in M(V2, X_n) (after renaming by phi) is NOT evidence that it is infeasible in V1. LTS difference reports "observed in one, not observed in the other".

4.5 Views. A view v in {ctl, call, dd} is a deterministic projection P_v(tau). It is forgetful: P_v(tau) = P_v(tau') does not imply tau = tau'. Views are derived data; they are recomputable from the log (the log is ground truth).
- P_ctl(tau): the sequence of (loc, outcome) for events of kind branch and line.
- P_call(tau): the call tree: nodes are call events with callee identity, children are calls made before the matching ret/exc, determined by stack discipline. A call without matching return (non-local exit) is closed by the exc event or by truncation.
- P_dd(tau): the dynamic data-dependence graph G_dd = (events in tau, D) with an edge (e_j -> e_i) in D iff e_i reads abstract location l, e_j is the last write to l before e_i in tau (reaching definition), or e_i consumes a value produced by e_j through argument binding or return binding. Control-dependence edges (branch -> events in its dynamic region) are an optional extension requiring static post-dominators.
G_dd is an observed dependency graph for one execution. It misses implicit flows through unobserved control and aliasing finer than granularity L; it records dependence, not influence.

---

# PART II. INFERENCE

## 5. Semantic correspondence (alignment)

5.1 Static matching. m_s : Loc(V1) -> Loc(V2) (partial) is produced by a deterministic AST/CFG matcher at the granularity of functions and basic blocks. Each pair (l1, l2) in m_s has score sigma_s(l1, l2) in [0, 1]. Pairs absent from m_s are unmatched (deleted in V1 or inserted in V2).

5.2 Dynamic anchors. For an input x and runs tau1, tau2, a candidate anchor is a pair (e1, e2) with equal kind, loc(e1) and loc(e2) both outside the changed region R (section 6), equal call-stack context after applying m_s (which includes only unchanged callees), and equal payload on external events (io, calls into unchanged libraries). Anchors are restricted to context and external events; they must not use the payload of events under comparison. Reason: matching on equal compared payloads biases alignment toward agreement and makes "no divergence" partly self-fulfilling (limitation L4).
For a location pair (l1, l2), let n_a(l1, l2) be the number of anchors, over X_n, whose locations are l1 and l2, and n(l) the number of runs that reach l. Dynamic score: sigma_d(l1, l2) = n_a(l1, l2) / max(n(l1), n(l2)) if the max is positive, else 0.

5.3 Correspondence. phi is the partial injective map obtained from a maximum-weight injective matching (e.g. assignment on the bipartite candidate graph, respecting a declared nesting constraint between functions and their blocks) over confidences c(l1, l2) = g(sigma_s, sigma_d), subject to c >= theta (declared threshold). g : [0,1]^2 -> [0,1] is nondecreasing in both arguments with g(0,0) = 0; the default noisy-or g = 1 - (1 - sigma_s)(1 - sigma_d) assumes the two sources are independent, which is not justified; this default is a [HYP-E5] to be replaced by a fitted or conservative (e.g. max) rule. phi is injective by construction and partial: unmatched locations are first-class (they represent inserted/deleted code).
phi is INFERENCE. Its confidence c is a heuristic score, not a probability, until calibrated (E5).

5.4 Event alignment. For a view v and traces tau1, tau2 of the same x, an alignment A_v is a set of index pairs M subset {1..n1} x {1..n2} that is
- partial and injective (each index at most once);
- order preserving: (i, j), (i', j') in M and i < i' imply j < j';
- admissible: (i, j) in M implies kind(e_i) = kind(e_j) and (loc(e_i), loc(e_j)) in phi, or both locs are unchanged and identical under the identity map of unchanged code.
A_v maximises sum over M of c(loc(e_i), loc(e_j)) minus a declared gap penalty per unmatched event, computed by dynamic programming, ties broken by a fixed deterministic rule (earliest index). A_v is equivalently a sequence of steps, each of the form M(i, j) (matched pair), D(i) (event only in tau1), or I(j) (event only in tau2), in trace order.
Alignment is not unique in general. Define ambiguity amb(A_v) in [0, 1] as 1 minus the fraction of top-k optimal alignments that agree with A_v on the divergence locus (section 5.6). It is part of the report.

## 5b. Observation equivalence and divergence (subsections 5.5 to 5.9)

(Section numbering note: 5.5 onward is OBSERVATION relative to a given alignment; the alignment itself is the INFERENCE. A divergence report is therefore "OBSERVATION of a difference between two recorded events, located by an INFERRED alignment".)

5.5 Channel observation functions. For c in Ch and event e, ob_c(e) is defined as
- ob_ret(e): the normalised value abstraction if e is the outermost return of s, else absent (bottom);
- ob_exc(e): (exception type, normalised message) if e is the outermost uncaught exception of s, else absent;
- ob_side(e): (target, byte abstraction) for io events and writes to state outside s's frames that outlive the call (globals, arguments mutated in place), else absent;
- ob_state(e): a(e) if e in P, else absent.
N is the declared normaliser (canonical ordering, float tolerance, address and repr removal, timestamp masking). Observation equivalence for a channel set C subset of Ch: e ~_C e' iff for all c in C, N(ob_c(e)) = N(ob_c(e')). ~_C is an equivalence relation on events (equality of images). Channels not in C_inst cannot be in an honest C; claiming one is CHANNEL_BLIND (section 8).

5.6 First divergence. Let A_v = (step_1, ..., step_K) be an alignment path of tau1, tau2. A step is conforming under C iff
- it is M(i, j) with e_i ~_C e'_j, or
- it is D(i) (resp. I(j)) with ob_c absent for all c in C (the event is silent under C).
Define delta_{v,C}(tau1, tau2) = min { k : step_k is not conforming }, or infinity if every step conforms. Terminal comparison: if ret or exc is in C and term classes of the two runs differ in {RET, EXC, TIMEOUT, BUDGET, CRASH} or (both RET and the return observations differ) or (both EXC and the exception observations differ), the pair also diverges at step K+1 (if not earlier). The divergence locus is the pair (e_i or absent, e'_j or absent) at step delta.
A run pair is stably divergent if the locus is identical under all optimal alignments tied with A_v; otherwise the report states amb(A_v) > 0.

5.7 Properties (each follows directly from the definitions given a fixed alignment).
(P1) Channel monotonicity: C subset C' implies delta_{v,C'} <= delta_{v,C}. Observing more channels can only find a divergence no later.
(P2) Output predicate: OD(x) := terminal observations differ on C_out = {ret, exc, side}. OD does not depend on the alignment.
(P3) Abstraction refinement (from 3.3): divergence on channel state under a coarser alpha implies divergence under a finer alpha. The observed first divergence under alpha is an upper bound (later or equal) on the first true divergence: a real earlier divergence may exist that alpha or N erased.
(P4) Masked divergence: x is internally divergent but output-masked iff delta_{v,Ch}(tau1, tau2) < infinity and not OD(x). The set of such x is where state-aware comparison could add information beyond output comparison. It is not a set of defects: refactorings produce internal divergence by design (limitation L1).

5.8 Witness. [OBSERVATION] A witness is the record w = (V1, V2, s, x, E, H, C, v, A_v, k, locus, reruns) with k = delta_{v,C} < infinity. It is replay-confirmed iff in r >= r_min independent fresh-sandbox reruns of (V1, x, E) and (V2, x, E) the same k, locus, and the same observations at the locus are reproduced, and in addition the V1-vs-V1 reruns and V2-vs-V2 reruns are each identical at the locus (self-consistency; guards against nondeterministic locus). The witness asserts: "under H and E, on input x, the two versions produced observations differing at this aligned locus." It does not assert that V2 is wrong, that the change was unintended, or that any specific line is the cause. It makes the claim independently checkable by anyone who can run H.

5.9 Propagated impact. [INFERENCE, observed dependency, not causation] Given a witness with locus event e_j in tau2 (or e_i in tau1 if the event is absent in tau2), define
- Fwd(e_j) = set of events reachable from e_j along edges of G_dd(tau2);
- Out(w) = Fwd(e_j) intersect {e : some ob_c(e) is present for c in C_out};
- I_diff(w) = { e in Fwd(e_j) : e is matched by A_v to e' and e !~_C e' } union { e in Fwd(e_j) unmatched by A_v with some ob_c(e) present }.
Out(w) says: output events whose recorded value depends, via observed dataflow in this execution, on the divergent event. I_diff additionally requires a recorded difference at the downstream event. Claims licensed: "downstream of the divergence, in this execution, the following outputs are data-dependent on it, and these of them differ." Claims not licensed: that changing the divergent value would change them (no intervention was performed); that unreached events are unaffected (implicit flows, finer aliasing, and unexecuted paths are missing); that the divergent event is the root cause (an earlier divergence may be hidden by alpha, P3). A causal statement would require an interventional experiment (e.g. patching the value at e_j and observing the outputs) and is outside this specification.

---

# Part II-b. OBSERVATION of evidence completeness

## 6. Evidence completeness and observation sufficiency

These quantities are deterministic functions of the recorded explorations. They describe how much was looked at. They are not probabilities of anything.

6.1 Changed region. R is a finite set of changed units (basic blocks, plus pseudo-units for changed dependencies and configuration) obtained from the static diff and phi, covering both V1-only and V2-only units. Each unit b has weight w(b) > 0 (default 1; or statement count, declared). If R is empty and (src, deps, rt) are identical, the pair is UNCHANGED and out of scope (no verdict is issued).

6.2 Activation fraction. hit(b) is true iff some input in X_n executed b in the version containing it. act = sum over b in R with hit(b) of w(b), divided by sum over b in R of w(b). act in [0, 1].

6.3 State-abstraction coverage. For each changed function u, a declared finite partition Pi_u of its entry abstract states into cells (product of per-variable classes from a fixed schema: None / bool / int in {negative, zero, one, small positive, large positive} / string or container in {empty, singleton, many} / type tag). Let cells_hit be the number of distinct cells of changed functions entered by some input in X_n, and cells_total the product-space size summed over changed functions (feasibility of cells unknown, so cells_total over-counts). cov = cells_hit / cells_total, in [0, 1]. cov is the coverage of a declared partition, not of the input space; it is a conservative (low) estimate of the coverage of feasible cells.

6.4 Saturation and budget. Let stop in {SATURATED, DOMAIN_EXHAUSTED, BUDGET, ERROR} be the exploration stopping reason. SATURATED: the last K_sat inputs added no new executed unit of R, no new cell, and no new aligned-trace shape. DOMAIN_EXHAUSTED: every x in a declared finite domain D (6.8) has been run. BUDGET: a limit in B was reached first. sat = 1 for SATURATED and DOMAIN_EXHAUSTED; sat = k0 for BUDGET with declared constant k0 in (0, 1); sat = 0 for ERROR. Truncated traces (2.2) are counted in the reason set but do not alter sat.

6.5 Observability. Declared channel weights omega_c > 0 for c in C, summing to 1. obs = sum over c in C with c in C_inst and non-degenerate for this scope of omega_c. Non-degenerate means for ret: the scope returns a value with a non-trivial abstraction; for side: io/global mutation instrumentation is active; for state: alpha is supported for the types involved. A scope whose output is not serialisable has ret degenerate. obs in [0, 1]. This factor encodes the V5/V6 finding that an output-free channel is blind to return values.

6.6 Determinism gate. gamma = 1 if delta_det in {DET, CONTROLLED}, gamma = 0 if UNCONTROLLED.

6.7 Sufficiency score. With declared weights w1..w4 > 0, w1+w2+w3+w4 = 1 (default 1/4 each),
S = gamma * act^{w1} * cov^{w2} * sat^{w3} * obs^{w4}.
It is a weighted geometric mean gated by determinism. Alongside S the report always contains the vector (act, cov, sat, obs, delta_det, stop, truncation count) and, for NO_DIVERGENCE_OBSERVED, the componentwise floors (section 8) that were met.

Properties [FORMAL, each by inspection of the formula]:
(S1) S in [0, 1]; S = 0 iff gamma = 0 or some factor is 0.
(S2) S is nondecreasing in each of act, cov, sat, obs.
(S3) With obs, gamma and stop held fixed, adding inputs to X_n never decreases act or cov, hence never decreases S.
(S4) The geometric mean forbids compensation: a zero in any factor forces S = 0. Weights are conventions, not estimates; sensitivity of verdicts to (w_i, k0) must be reported.

6.8 Finite-domain exhaustiveness. A declared finite domain D subset of X_s (for example, all integer lists of length <= k with entries in [-m, m]) is exhaustively covered if X_n contains D and every run on D terminates in RET or EXC within B with no truncation. This is a different object from act/cov and enables Theorem 3.

6.9 What S does NOT imply. [OBSERVATION about the metric]
- It is not the probability that the versions are equivalent, nor that no divergence exists, nor one minus a false-assurance rate. Any such interpretation requires calibration against independent labels (E6) and would then be a PROBABILISTIC ESTIMATE per stratum.
- S = 1 is compatible with divergent versions (Theorem 2 gives a concrete instance with act = 1, cov = 1, sat = 1, obs = 1).
- act measures execution of changed code, not that execution reached a state where old and new code differ; cov depends on the declared partition, not the true input space.
- S values are comparable across scopes only if the partitions, weights, channels and budgets are identical.
- High S under a coarse alpha or an over-permissive normaliser N is high confidence in a weak observation.
- S says nothing about unchanged code whose behaviour changed through a changed dependency not represented in R.

---

# PART III. PROBABILISTIC ESTIMATE

## 7. Uncertainty

7.1 Setting. Let z denote the evidence summary for a pair (the vector of section 6, plus divergence features if any), and y in {div, nodiv} a ground-truth label obtained from an independent oracle (section 7.5). A selective predictor is a pair (h, g): a score h(z) in [0, 1] and an accept rule g(z) in {0, 1}. Coverage Phi(g) = P(g = 1). Selective risk R(g) = P(error | g = 1). The risk-coverage curve is {(Phi(g_tau), R(g_tau))} over thresholds tau; the area under it (AURC) summarises it. Probabilities are over the distribution that generates (z, y), which must be stated (a benchmark is a sample from one, not from "programs in general").

7.2 False-assurance rate. For verdict NO_DIVERGENCE_OBSERVED and a sufficiency stratum s_j, FAR_j = P(y = div | verdict = NDO, S in stratum j). A point estimate with an exact (Clopper-Pearson) interval from m_j labelled NDO pairs of which k_j were divergent is a PROBABILISTIC ESTIMATE valid for the labelled population; pairs are clustered (same program, duplicate groups), so intervals must come from a program-cluster bootstrap or cluster-aware method, not from treating pairs as independent. Claim "S is informative" iff FAR_j is monotone decreasing in S with intervals that separate (E6); until then S is descriptive only.

7.3 Sampling bound. If inputs are drawn i.i.d. from a distribution Q on X_s, runs are deterministic and observable under C, and p = Q(x : divergence under C), then P(no divergence in n draws) = (1 - p)^n <= exp(-n * eps) whenever p >= eps. Hence if n >= ln(1/d0) / eps and no divergence is observed, then with confidence 1 - d0 we may assert p < eps (a statement about Q and C only). Premises that routinely fail: coverage-guided or targeted exploration is adaptive and not i.i.d.; Q may not resemble real usage; determinism may not hold. The bound is therefore reported only for the sub-run of i.i.d. sampled inputs, labelled with Q.

7.4 Conformal option. [Option, hypothesis until E6] Split conformal prediction on a calibration set with a nonconformity score s(z, y) (for example 1 minus the predicted probability of y from a model of z) and quantile q_hat = the ceil((n_cal + 1)(1 - a)) / n_cal empirical quantile of calibration scores. The prediction set Gamma(z) = { y : s(z, y) <= q_hat }. Under exchangeability of calibration and test pairs, P(y_test in Gamma(z_test)) >= 1 - a (marginal). If Gamma(z) = {div, nodiv} the system reports INSUFFICIENT; if it is a singleton it may annotate the verdict with that label. Limits: guarantee is marginal, not conditional on S or on program; exchangeability is violated by program clusters, duplicate groups and generator families (calibrate group-wise or leave-cluster-out; use Mondrian conformal by S-stratum if strata are large enough); under distribution shift (benchmark to real code, as BugsInPy shows) coverage can fail silently.

7.5 Ground-truth requirement. y must come from an oracle independent of the exploration that produced z and independent of the mutation generator that produced the pair (independent test suites, a separately specified reference implementation, exhaustive evaluation on small finite domains, or hand verification). A label that is a function of the generator makes every quantity in 7.1-7.4 an estimate of generator fingerprinting rather than of divergence detection. Labels from an oracle are themselves observations on a finite input set, so y has residual noise that must be reported.

7.6 A learned score (optional module J) falls here. It may order exploration; it never enters the verdict of section 8.

---

# PART IV. FORMAL CLAIM

## 8. Three-valued verdict semantics and theorems

8.1 Verdict function. For (V1, V2, s) with explored inputs X_n, environment E, harness H, channels C, view v, budget B, floors f = (f_act, f_cov, f_sat, f_obs) declared in advance:
1. If the pair is UNCHANGED (6.1) no verdict.
2. DIVERGENT iff there exists x in X_n with a replay-confirmed witness (5.8). The witness set W is returned.
3. Otherwise NO_DIVERGENCE_OBSERVED iff gamma = 1 and act >= f_act and cov >= f_cov and sat >= f_sat and obs >= f_obs and no x in X_n produced a divergence at all (including unconfirmed ones; an unconfirmed divergence yields INSUFFICIENT with reason FLAKY_DIVERGENCE). The vector and S are returned.
4. Otherwise INSUFFICIENT with a nonempty set of reason codes from {NO_INPUTS, UNSUPPORTED_SIGNATURE, IMPORT_FAILURE, NONDETERMINISTIC, NOT_ACTIVATED (act < f_act), LOW_STATE_COVERAGE (cov < f_cov), BUDGET_EXHAUSTED (sat < f_sat), CHANNEL_BLIND (obs < f_obs), SANDBOX_FAILURE, FLAKY_DIVERGENCE}. These map to V5/V6 failure categories (nondeterminism 60, unsupported signature 49, import 4, QuixBugs declared without inputs 36, NOT_ACTIVATED 69).
Floors are conventions; their values are experiment parameters (E6), not derived constants.

8.2 Proposition (stability of DIVERGENT). Fix everything except X_n. If the verdict is DIVERGENT for X_n and X_n subset X_n', the verdict for X_n' is DIVERGENT. Proof: the witness for x in X_n remains a replay-confirmed witness for x in X_n'. Corollary: DIVERGENT is monotone in X_n, while NO_DIVERGENCE_OBSERVED and INSUFFICIENT are not: further exploration may turn either into DIVERGENT.

8.3 Theorem 1 (witness soundness, relative to the harness). Assume A1, A2 (section 9) and that the witness is replay-confirmed. Then V1 and V2 are not equivalent on input x under (~_C, N, alpha, E): there is an aligned step at which recorded observations differ. If C is a subset of C_out and equals the externally visible contract of s, then V1 and V2 violate behavioural equivalence with respect to that contract. Proof: by definition 5.6, delta < infinity means a non-conforming step exists; replay-confirmation with A2 excludes nondeterminism as the explanation for the observed locus; A1 ensures recorded events are what executed. It does not follow that V2 is incorrect, that an intended change was not made, or that the locus is the cause. For C containing the state channel, the claim is only "differs under alpha_{d,p}" and the refinement lemma 3.3 gives the direction of robustness.

8.4 Theorem 2 (NO_DIVERGENCE_OBSERVED does not imply equivalence, even at maximal sufficiency). There exist V1, V2, s, an input set X_n and a harness satisfying A1-A9 such that the verdict is NO_DIVERGENCE_OBSERVED with act = cov = sat = obs = gamma = 1 and S = 1, while V1 and V2 are not equivalent on X_s.
Proof by construction. Let s be a function of one integer argument. V1 returns x. V2 returns x + (1 if x == 123456789 else 0), written on the same single line. Changed region R = {that block}. Any X_n not containing 123456789 executes the block (act = 1); take the declared cell partition to be the sign/zero/size classes and let X_n hit all of them (cov = 1, and the cell partition cannot separate 123456789 from other large positives); exploration stops by saturation (sat = 1); ret is observed (obs = 1); runs are deterministic (gamma = 1). Every run produces equal observations on all channels, so no divergence is recorded and the verdict is NO_DIVERGENCE_OBSERVED with S = 1. But V1(123456789) != V2(123456789). QED. Consequence: no threshold on S, act, cov or any finite-sample statistic of the dynamic tier converts NO_DIVERGENCE_OBSERVED into an equivalence claim; the word "equivalent" is never emitted by the dynamic tier.

8.5 Theorem 3 (bounded guarantee). Let D be a finite subset of X_s and C subset-or-equal C_out. Suppose
(G1) D subset X_n and every run (V1, x, E), (V2, x, E) for x in D terminates in RET or EXC within B with no truncation;
(G2) assumptions A1, A2, A3, A5 and A6 hold (faithful harness, determinism, input round-trip, correct normaliser, identical environment);
(G3) every channel in C is observed (C subset of C_inst) and the terminal comparison of 5.6 is applied;
(G4) the verdict is NO_DIVERGENCE_OBSERVED.
Then for every x in D, the terminal observations of V1 and V2 on C are N-equal. That is, V1 and V2 are observationally equivalent on D under C, N, and E. Proof: for each x in D, delta_{v,C} = infinity implies in particular that the terminal comparison of 5.6 conforms (it is included in the definition), and G1 ensures a terminal observation exists for each x. Equality is by definition of ~_C. QED.
What the theorem does not give: any claim for x outside D; any claim under a different E; any claim for channels outside C; any claim about internal state if the state channel is not in C. The small-scope heuristic (bugs tend to have small counterexamples) is a hypothesis about program populations, not a consequence of Theorem 3 [HYP, test: fraction of known regressions in the benchmark that have a witness within the declared D; E1/E6].

8.6 Formal tier (optional, outside the dynamic pipeline). Bounded symbolic equivalence checking or regression verification on small units can produce the claim EQUIV_BOUNDED(k, M, solver) meaning: under unrolling bound k, semantic model M of the language fragment, and a sound solver, V1 and V2 return equal results and raise equal exceptions on all inputs satisfying a stated precondition. This claim is of a different class from Theorems 1-3, depends on the fidelity of M and the solver, and is the only mechanism by which an unbounded-domain equivalence statement may be made. Exhaustive evaluation over a finite D (Theorem 3) is the dynamic analogue and requires no solver.

8.7 Proposition (monotonicity in channels). By P1, if C subset C' and DIVERGENT holds for (C), it holds for (C') on the same explored inputs and alignment. The converse fails by P4 (masked divergence).

---

## 9. Assumptions

- A1 Harness faithfulness: tracing, sandboxing and abstraction do not alter the observed behaviour of the program beyond the declared budget and recorded perturbations; the sandbox captures all declared side effects.
- A2 Determinism for replay: for a witness, rerunning under the same (V, x, E_c) reproduces the observation at the locus (checked by reruns, not proved).
- A3 Input round-trip: serialised inputs decode to behaviourally identical values in both versions.
- A4 Input validity: x is a valid input for both versions (signature compatibility, 1.2).
- A5 Correct normaliser: N removes only representation artefacts and no real behavioural information; N is part of the declaration.
- A6 Identical environment for both versions of a comparison.
- A7 Same runtime identity unless explicitly part of V.
- A8 Budget does not truncate observations that matter, or truncation is reported and weakens claims to prefixes.
- A9 alpha is deterministic and canonical (same concrete state always yields the same abstract state).

## 10. Known limitations

- L1 Divergence is not defect. Behaviour-preserving refactoring and intended behaviour changes both produce divergence. Without a specification or an independent oracle, the system reports difference, not error.
- L2 The system observes executed behaviour only. Unactivated code, unexplored input classes and rare conditions are invisible (Theorem 2).
- L3 Observed first divergence is an upper bound on the true first divergence (P3). Localisation inherits alignment error (INFERENCE) and abstraction coarseness.
- L4 Alignment can bias results: anchors restricted to context reduce circularity but cannot remove it; refactorings that reorder or restructure code can produce spurious or missing divergences. Accuracy is untested (E5).
- L5 Impact is observed dependence in one execution; implicit flows, aliasing finer than granularity L, and unexecuted paths are missing; no causal or counterfactual claim is made.
- L6 Uncontrolled nondeterminism defeats replay; such pairs end INSUFFICIENT, not "equal". Control coverage is measured (E8), not assumed.
- L7 The sufficiency score has conventional weights and floors; it is not calibrated, not a probability, and not comparable across declarations. Whether it predicts false assurance is a hypothesis (E6).
- L8 Labels. The V5/V6 label is a function of the mutation generator; label noise exists (SP-8, SP-11); duplicates inflate apparent performance; no pristine holdout exists. Section 7 quantities are meaningful only with independent labels.
- L9 Conformal and sampling bounds require exchangeability / i.i.d. inputs that adaptive exploration and clustered benchmarks violate.
- L10 All concrete tooling evidence is Python; the definitions are language-neutral but their instantiation (alpha, location domain L, normaliser N, event schema) is per language.
- L11 The state channel depends on (d, p, P, N). Divergences hidden by these choices are not detected, and those revealed by fine settings may be representation artefacts.
- L12 Internal divergence adds value beyond output comparison only if E1 shows it; that is not established.

## 11. Claim-status table

| statement | class | basis | what would falsify or weaken it |
|---|---|---|---|
| Replay-confirmed witness: versions differ on input x under C, N, alpha, E | OBSERVATION (+ Theorem 1) | recorded events, reruns | harness bug (A1), flaky locus (A2), wrong N (A5) |
| First divergence locus at aligned step k | INFERENCE | alignment A_v, ambiguity reported | alternative optimal alignment, amb > 0; E5 mismatch with hand alignment |
| Output reachable from divergence by dependence | INFERENCE (observed dependency) | G_dd of one execution | any need for causal wording; intervention experiment disagreeing |
| Sufficiency vector and S | OBSERVATION (descriptive index) | recorded coverage and flags | none; but any probabilistic reading is unsupported |
| FAR by stratum, risk-coverage, conformal sets | PROBABILISTIC ESTIMATE | independent labels, cluster-aware intervals | label contamination, exchangeability failure, shift |
| i.i.d. sampling bound p < eps at confidence 1 - d0 | PROBABILISTIC ESTIMATE | premises of 7.3 | non-i.i.d. exploration, nondeterminism |
| NO_DIVERGENCE_OBSERVED does not imply equivalence | FORMAL CLAIM | Theorem 2 | none (it is a counterexample proof) |
| Observational equivalence on finite D under C | FORMAL CLAIM | Theorem 3, premises G1-G4 | violation of any premise, e.g. truncation or uncontrolled nondeterminism |
| DIVERGENT stable under extension of X_n | FORMAL CLAIM | Proposition 8.2 | witness not replayable |
| Unbounded equivalence EQUIV_BOUNDED(k, M, solver) | FORMAL CLAIM (formal tier only) | external solver, semantic model | model infidelity, unsoundness of solver |

## 12. Disagreements with the spine

1. Spine asks for "a precise monotone sufficiency score". Provided (6.7), but the verdict uses componentwise floors, not the scalar, because a scalar hides which factor failed and invites a confidence reading that is not supported (L7).
2. Spine says alignment is "static matching seeded by dynamic anchors". Provided with a restriction: anchors may use context and external events only, not the compared payload (5.2), to avoid circular agreement. Whether this suffices is E5.
3. Spine says equivalence "is only asserted by an optional formal tier". Amended: exhaustive evaluation over a finite declared domain gives a bounded observational equivalence (Theorem 3) without a solver; the dynamic tier still never claims unbounded equivalence.
4. Spine's "first-divergence index" is not well defined without choosing an alignment; it is defined here as alignment-relative with an ambiguity report (5.4, 5.6), and as an upper bound on the true first divergence (P3).
5. Spine's "earlier detection of masked divergences" as the value proposition presupposes that internal divergence is informative. That is a hypothesis (L1, L12), and it needs labels independent of the mutation generator (7.5).
