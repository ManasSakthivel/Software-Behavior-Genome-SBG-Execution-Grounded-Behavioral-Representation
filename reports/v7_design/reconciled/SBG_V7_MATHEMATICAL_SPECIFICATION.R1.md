# SBG V7: Mathematical Specification (R1)

> Reconciled version R1 of SBG_V7_MATHEMATICAL_SPECIFICATION.md; original preserved at reports/v7_design/_original_archive/

Status: specification, no code. Companions: SBG_V7_DATA_AND_EVIDENCE_SCHEMA.R1.md (entities), SBG_V7_COMPETING_ARCHITECTURES.md, _DESIGN_SPINE.md.

Authority: P0_BINDING_DECISIONS.md (D1-D11) wins over this file. Sufficiency levels S0-S3, their floors and the reason-code semantics have exactly one definition, in P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md; this document cites that file and does not restate any threshold. All thresholds and weights that appear here are conventions, UNVALIDATED until a development split calibrates them (D3).

R1 summary of changes (details: CHANGELOG_math_schema.md): verdict set DIVERGENT_OBSERVABLE / INSUFFICIENT / NO_DIVERGENCE_OBSERVED(S1|S2|S3) with no equivalence verdict (section 8); internal-only divergence demoted to an advisory annotation (8.1b); seven evidence classes defined formally (Part 0); schema event vocabulary adopted; capture tiers, hash chain and replay recipe (sections 1.7, 1.8, 2.5-2.7); anchors exclude compared payload (5.2); canonical budget unit CPU-seconds (1.5); isolation per D10 (1.7, A10).

Every statement carries one of four claim labels (epistemic status), defined in 0.3, and every stored record carries one of the seven evidence classes of Part 0. A definition is a convention and belongs to the label of the thing it defines.

- OBSERVATION: something a harness recorded in a run, or a deterministic function of recorded data. True relative to the harness (assumptions A1-A11, section 9). Evidence classes: observation, derived.
- INFERENCE: a deterministic but heuristic derivation that goes beyond what was recorded (alignment, localisation, dependence reach). It can be wrong; it is reported with confidence or ambiguity. Evidence class: inferred.
- PROBABILISTIC ESTIMATE: a statement with a probability, valid only under stated sampling or exchangeability assumptions. Evidence class: inferred with status uncertain.
- FORMAL CLAIM: a theorem or checker result about the definitions, true by proof, with its premises and domain stated. Evidence class: proof.

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
| B | budget; canonical unit is CPU-seconds (cpu_s) summed over all processes and including all V7 overhead (tracing, ingest, hashing, alignment, replay); secondary caps: events, steps, wall time, memory, inputs |
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
| Verdict | one of DIVERGENT_OBSERVABLE, INSUFFICIENT(reason_code), NO_DIVERGENCE_OBSERVED(S), S in {S1, S2, S3} (section 8); no other value exists |
| C_obs | observed channels {ret, exc, side} (called C_out in 5.7) on which a verdict may be defined |
| internal_divergence | advisory annotation in {none, observed, unknown}; never a verdict (8.1b) |
| D_H | harness declaration record (3.5) |
| rho | run record, the replay recipe (1.8) |
| o(x) | per-input outcome (8.1) |

All sets are finite unless stated. "Iff" is used only for definitions and for theorems with proofs given.

---

# PART 0. EVIDENCE CLASSES AND EPISTEMIC STATUS

New in R1 (binding decision D4). The original had four epistemic classes and no definition of derived, missing, invalid or uncertain evidence. The seven classes are: observation, derived observation, inference, proof (primary classes) and missing, invalid, uncertain (statuses). Their mapping to schema entities is in SBG_V7_DATA_AND_EVIDENCE_SCHEMA.R1.md section 1.

## 0.1 Formal setting

A record is r = (id, content, class, status, producer, inputs). R_store is the finite set of records. inputs(r) is the finite set of records from which r was computed; the relation is acyclic; a record with inputs(r) empty is a root. run_H(V, x, E) = (tau, term) is as in 1.6. All definitions are relative to a harness H (1.5) and its declaration D_H (3.5).

0.1.1 Observation. r is an OBSERVATION iff it is a root and content(r) is a component of run_H(V, x, E) or of capture metadata produced by the harness in an isolated execution (1.7): events, outcomes, completeness, determinism reruns, replay reruns, isolation-check results. An observation is true relative to H only (A1-A11).

0.1.2 Derived observation. r is a DERIVED OBSERVATION iff there are records r_1..r_m (observations or derived observations), a total deterministic function f declared in the producer registry (name, version, code hash) and parameters theta with content(r) = f(content(r_1), ..., content(r_m); theta). Recompute check: any party holding the inputs, f and theta obtains identical canonical bytes. Examples: views P_v (4.5), alpha(sigma) (3.2), hit(b), act, cov, ob_c(e), N(ob_c(e)), the predicate e ~_C e', the outcome-difference predicate OD(x) (5.7 P2), hashes and chain roots (2.6).

0.1.3 Inference. r is an INFERENCE iff content(r) = g(content(r_1..r_m); theta, a) where a names a heuristic algorithm and version that selects one element from a set of admissible candidates, so that another admissible algorithm a' can give content(r') different from content(r) on the same inputs. g is deterministic for fixed (a, theta), so recomputation needs the same (a, theta). Every inference carries a and, where defined, an ambiguity or confidence value (5.3, 5.4). Examples: phi, A_v, the divergence index delta and locus, Fwd/Out/I_diff (5.9), the changed region R when produced by a diff algorithm, mined invariants (optional module E), the internal_divergence annotation.

0.1.4 Proof. r is a PROOF iff content(r) is a statement pi together with a premise set Pi (assumptions, declaration D_H, a finite domain D or an unrolling bound) and a derivation that is either a mathematical argument (8.2-8.5) or the output of a checker whose soundness is itself a stated premise. A proof licenses pi only under Pi; the record states method, domain, bound and premises. The dynamic tier can emit one proof record kind: the exhaustive-domain claim of Theorem 3. Solver-based claims (8.6) are a different method.

0.1.5 Missing evidence (status). For a claim c let Req(c) be the evidence the definition of c requires (for NO_DIVERGENCE_OBSERVED: runs of both versions for each explored input, completeness records, determinism reruns). An item m in Req(c) is MISSING iff no valid record of its kind exists in R_store for the stated scope. Missing differs from observed-absent: an event of kind k is OBSERVED-ABSENT in tau iff k is in the captured kinds of tau, tau is not truncated before the point of interest and the region of interest lies inside the instrumented coverage; otherwise its absence is MISSING and nothing may be concluded from it (a branch not taken is observed; a branch not instrumented is missing). Missing items are recorded explicitly with a cause (dropped kind, truncation, blind spot, build failure, no input, unmapped region, run not executed, tombstoned blob).

0.1.6 Invalid evidence (status). A record r is INVALID iff at least one validity predicate fails: (i) replay disagrees at the locus or outcome (5.8); (ii) r is superseded by an invalidation record; (iii) the run executed on the v6_compat path or below the declared minimum isolation profile (1.7); (iv) an assumption that r depends on is detected violated (A3, A5, A9, A10, A11); (v) the determinism class is unstable on a compared channel. Propagation: if r is in inputs(r') and r is invalid then r' is invalid, unless a recorded re-derivation of r' excludes r. A witness whose replay fails is void and no longer supports DIVERGENT_OBSERVABLE (8.2). Invalid records are retained, flagged, and never count as evidence for any verdict value.

0.1.7 Uncertain evidence (status). A record is UNCERTAIN iff it carries an uncertainty descriptor u = (scale, value, basis) with scale in {ordinal, heuristic_score, calibrated_probability, bound}. A heuristic_score (sigma, c, amb) is not a probability. A calibrated_probability is permitted only after calibration against independent labels (7.5) and is then a PROBABILISTIC ESTIMATE. Uncertainty must be propagated: a verdict that depends on an uncertain record carries separate uncertainty components, not one fused scalar. A sufficiency level is an ordinal scale (empirically calibrated at best, UNVALIDATED until calibrated).

## 0.2 Primary class and status are orthogonal

Primary class in {observation, derived, inferred, proof}; status is a subset of {missing, invalid, uncertain}. A record is thus a pair (class, status set). A verdict is a derived record over inferred and uncertain inputs; NO_DIVERGENCE_OBSERVED(S) is derived with status uncertain; INSUFFICIENT has status missing or invalid with a reason code.

## 0.3 Claim labels and their mapping to evidence classes

| claim label | evidence class and status |
|---|---|
| OBSERVATION | observation, or derived |
| INFERENCE | inferred |
| PROBABILISTIC ESTIMATE | inferred, status uncertain, scale calibrated_probability |
| FORMAL CLAIM | proof |

Absence of evidence is never a claim label of its own: it is the status missing and supports no verdict value other than INSUFFICIENT.

---

# PART I. OBSERVATION

## 1. Program version, scope, input, environment

1.1 [OBSERVATION-convention] A program version is V = (src, deps, rt): source tree, resolved dependency set (names and exact versions), and language runtime identity (implementation and version). Two versions are compared only with the same rt, or with rt explicitly recorded as differing and included in V.

1.2 A scope s = (module, symbol) designates an entry point with a signature sig(s) giving parameter names and, if available, types. A scope is comparable iff sig(s) exists in both V1 and V2 and is compatible (same arity and parameter names up to a declared renaming). Otherwise the scope is first lifted to the outermost frame whose symbol exists in both versions (the lifted scope is recorded in the verdict identity); if none exists, the pair ends INSUFFICIENT with reason unsupported_signature. Whether a call with the old signature failing in the new version is classified as an API difference is owned by P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md and is not decided here (see CHANGELOG, unresolved).

1.3 An input x in X_s is a serialisable bundle: argument values, plus the initial state of declared mutable resources (files, stdin, module globals) that the scope may read. Serialisation round-trips: decode(encode(x)) is observationally the same input for both versions (assumption A3).

1.4 An environment E = (E_c, E_u). E_c is the controlled part: random seed, hash seed, clock origin and rate, locale, environment variables, filesystem image, network stub, scheduling policy. E_u is the uncontrolled residue (true parallelism, real clock, OS entropy not intercepted). E is the same for both versions in a comparison (A6).

1.5 A harness H = (isolation profile I_H, tracer, alpha, N, C_inst, B). C_inst subset of Ch is the set of channels the harness can actually observe for this scope. B = (cpu_s, max_events, max_steps, max_wall, max_mem, max_inputs); cpu_s is the canonical budget, CPU-seconds (user plus system) summed over all processes of the pair evaluation including every V7 overhead; the other components are secondary safety caps. Budgets of different systems are compared only in cpu_s.

1.6 A run is the partial function run_H(V, x, E) = (tau, term) where tau is a trace and term in {RET, EXC, TIMEOUT, BUDGET, CRASH}. RET and EXC are normal terminations. Nothing else is assumed to be deterministic.

1.7 Isolation (binding decision D10). The isolation profile I_H requires: (a) each run executes in a fresh child process, never in a thread of the host; (b) resource limits by setrlimit (CPU, address space, open files, processes, file size); (c) the whole process group is killed on timeout or budget exhaustion; (d) tracing is set up outside the reach of user code and tracer evasion (for example sys.settrace(None)) is detected and recorded as a blind spot; (e) network access is denied; (f) filesystem writes are confined to a private directory. Mechanisms: sandbox-exec on macOS, container with network none on Linux. Epistemic status: a property counts as in force only when an experimental isolation check passes for that mechanism and is recorded (observation). In P0 only sandbox-exec network and write denial was observed to work; every other property is an UNVERIFIED design requirement until P1. The legacy runner (thread in host process, runaway thread keeps burning CPU, no rlimits, child processes survive, settrace(None) evades tracing, os._exit kills the host, network not denied: all verified defects) survives only as `v6_compat`; its runs are INVALID evidence (0.1.6 iii) for any V7 claim.

1.8 Run record and replay recipe. The default stored form of a run is rho(V, x, E, H) = (hash of V, hash of x, hash of E, hash of D_H, capture level, outcome, trace chain root (2.6), completeness summary, coverage bitmap of R). Events are not stored by default. They are stored in full only for witness runs, an audit sample and runs escalated to a higher capture level; otherwise they are regenerated by replaying rho in the same harness. Replay is expected to reproduce the chain root (A2, A11) and this is checked, not assumed. A run whose regenerated chain root differs from the stored root is invalid evidence (0.1.6 i).

## 2. Execution as an event sequence

2.1 An event is e = (id, kind, loc, payload, t) where
- id: natural number, unique in the trace, id(e_i) = i;
- kind in K, the schema event vocabulary {call, return, branch, line, exception, state_obs, data_def, data_use, side_effect, external_call, resource, truncation}. Short names used elsewhere in this document are aliases: ret = return, exc = exception, read = data_use, write = data_def, io = side_effect or external_call, alloc = resource (metric allocs); a state point is a state_obs event;
- loc in Loc(V): static location of the event;
- payload: abstracted data attached to the event (callee identity and argument abstraction for call; value abstraction for ret/read/write; exception type and normalised message for exc; target and byte abstraction for io; branch outcome for branch);
- t: logical timestamp, natural number, t(e_i) = i. Wall-clock time is never part of t and never compared.

2.2 A trace is tau = (e_1, ..., e_n) with n <= B.max_events. A trace carries truncated(tau) in {true, false}. Truncation makes every later claim about the trace a claim about its prefix only.

2.3 Read and write events carry an abstract location l in a finite-granularity location domain L (local variable of a frame, global, field of an abstract object identified by creation-site and allocation-order index, element-slot of a container as a single summary slot). The granularity is declared; coarser granularity conflates aliasing.

2.4 Run determinism evidence. For r >= 2 reruns under the same (V, x, E), define identical(tau, tau') iff same length and event-wise equal in (kind, loc, payload) after normalisation N. The determinism flag delta_det in {DET, CONTROLLED, UNCONTROLLED}: DET if all reruns are identical with no controls applied; CONTROLLED if they are identical only with E_c controls applied; UNCONTROLLED otherwise. Schema mapping: DET and CONTROLLED are class `deterministic` (CONTROLLED lists the controlled sources in masked_by_virtualisation); UNCONTROLLED is `outcome_stable_trace_unstable`, `unstable` or `unknown`. The flag is a property of (V, x, E), not of the pair. Determinism-confirmed on a channel set C means all reruns agree on the observations of C (outcome stability suffices for output-only comparison). The number of reruns is recorded; its minimum is set by policy, not here. This is an observation about r reruns only: it does not prove determinism on other inputs. Fixed-seed control makes runs repeatable but does not make them behaviour-preserving across versions (L14).

2.5 Capture tiers (completeness is explicit). L0: outcome only (termination class, return and exception abstraction, declared side effects, stdout and stderr hashes). L1: L0 plus call and return events plus a compact coverage bitmap of blocks and branches in the changed region R, so activation and branch-direction coverage exist from the first pass. L2: L1 plus branch, line and data events inside focus regions. L3: full line trace. Every run records the kinds captured, the kinds dropped, truncation and the level achieved (which may be lower than requested). A claim that needs an event kind the tier did not capture is a claim about missing evidence (0.1.5).

2.6 Trace hash chain. Let a trace be cut into chunks c_1, ..., c_m of at most a fixed number of events. Let beta(c_i) be the canonical bytes of the behaviour projection of c_i: for each event (seq, kind, function symbol, payload hash), with absolute line numbers, the run identifier and the repeat index excluded. Define h_0 = fixed constant, h_i = SHA-256(h_{i-1} || beta(c_i)), chain_root = h_m. Because the run identifier and repeat index are not hashed, two reruns of a deterministic run have equal chain roots, and replay agreement is well defined. The hash is computed incrementally inside the child process, so the chain exists even when no event chunk is stored.

2.7 Agreement notions. Replay agreement at the locus and outcome (5.8) is the criterion for witnesses. Whole-chain agreement (equal chain_root) is reported separately as a reproducibility statistic. A trace-unstable but outcome-stable run has unequal chain roots and may still yield a confirmed witness whose confidence is flagged nondet_adjusted.

## 3. Observed state and the abstraction function

3.1 A concrete state sigma at a state point is (frames, heap): the call stack with local variable bindings and the heap graph reachable from the current frame, the arguments, and the globals referenced by the scope.

3.2 State abstraction alpha_{d,p}(sigma) is defined by traversal from the roots in a canonical order (sorted variable names; sets and mappings sorted by abstracted key):
- depth d in N: nodes at distance > d from a root are replaced by the marker TOP_d;
- precision p: a declared value abstraction for base values: p = exact for ints, bools, None, and strings up to length L_s; floats compared with declared tolerance eps_f (or rounded to declared significant digits); otherwise (type, length, content hash);
- identity: no memory addresses, no object ids, no default repr strings (these are the repr-artefact class, cf. SP-11). Shared and cyclic structure is encoded by traversal-order back-references.
alpha is a deterministic function of sigma and (d, p). It is not injective.

3.3 [FORMAL-flavoured lemma inside OBSERVATION definitions] Refinement. If (d', p') refines (d, p) (d' >= d and p' at least as discriminating), then alpha_{d',p'}(sigma) = alpha_{d',p'}(sigma') implies alpha_{d,p}(sigma) = alpha_{d,p}(sigma'). Consequently any divergence visible under a coarser abstraction is visible under every finer one. (Proof: coarser is a function of finer by forgetting.)

3.4 State points. State snapshots are taken only at events of kinds in a declared set P (default: call, ret, exc, and branch events inside changed regions). The observed state at event e in P is a(e) = alpha_{d,p}(sigma_e). This bounds cost and makes state comparison a comparison at selected points only.

3.5 The declaration D_H = (d, p, L_s, eps_f, P, N, C, v, abstraction id, normaliser id, isolation profile, seed policy, capture-tier policy, reference to the floors and level definitions in P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md) is hashed, stored as one record and referenced by every witness and verdict. Changing it can change a verdict; verdicts are only comparable under the same declaration. Normaliser tier: floats are rounded to the declared significant digits before hashing (exact values stay in blobs), so a refactor that reorders float sums does not create a spurious difference; the tolerance is part of N.

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

5.2 Dynamic anchors. For an input x and runs tau1, tau2, a candidate anchor is a pair (e1, e2) with equal kind, loc(e1) and loc(e2) both outside the changed region R (section 6), equal callee identity, and equal call-stack context after applying m_s (which includes only unchanged callees). Anchors are defined by (kind, call-stack context, callee identity) only. The payload of an event whose channel is in C, or of any event under comparison, is never an anchoring criterion; payload equality of external events may be used only for channels not in C. Reason: matching on equal compared payloads biases alignment toward agreement and makes "no divergence" partly self-fulfilling (limitation L4).
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
N is the declared normaliser (canonical ordering, float tolerance, address and repr removal, timestamp masking). Observation equivalence for a channel set C subset of Ch: e ~_C e' iff for all c in C, N(ob_c(e)) = N(ob_c(e')). ~_C is an equivalence relation on events (equality of images). Channels not in C_inst cannot be in an honest C; claiming one yields INSUFFICIENT with reason unobservable_outcome (section 8).

5.6 First divergence. Let A_v = (step_1, ..., step_K) be an alignment path of tau1, tau2. A step is conforming under C iff
- it is M(i, j) with e_i ~_C e'_j, or
- it is D(i) (resp. I(j)) with ob_c absent for all c in C (the event is silent under C).
Define delta_{v,C}(tau1, tau2) = min { k : step_k is not conforming }, or infinity if every step conforms. Terminal comparison: if ret or exc is in C and term classes of the two runs differ in {RET, EXC, TIMEOUT, BUDGET, CRASH} or (both RET and the return observations differ) or (both EXC and the exception observations differ), the pair also diverges at step K+1 (if not earlier). The divergence locus is the pair (e_i or absent, e'_j or absent) at step delta.
A run pair is stably divergent if the locus is identical under all optimal alignments tied with A_v; otherwise the report states amb(A_v) > 0.

5.6b Alignment trust gate. Output-channel divergence (5.7 P2) needs no event alignment, so alignment failure never revokes DIVERGENT_OBSERVABLE; the locus is then reported as unlocalised. Alignment matters for the locus, for internal views and for function-level partitions. When the alignment trust at the locus is below the pre-registered threshold (set on a development corpus, not here), internal views are excluded and the annotation internal_divergence is `unknown`. If alignment is needed for the declared scope and fails, the pair is INSUFFICIENT with reason alignment_failed. amb(A_v) is a heuristic ambiguity score and is gated on, never read as a probability.

5.7 Properties (each follows directly from the definitions given a fixed alignment).
(P1) Channel monotonicity: C subset C' implies delta_{v,C'} <= delta_{v,C}. Observing more channels can only find a divergence no later.
(P2) Output predicate: OD(x) := terminal observations differ on C_out = {ret, exc, side}. OD does not depend on the alignment.
(P3) Abstraction refinement (from 3.3): divergence on channel state under a coarser alpha implies divergence under a finer alpha. The observed first divergence under alpha is an upper bound (later or equal) on the first true divergence: a real earlier divergence may exist that alpha or N erased.
(P4) Masked divergence: x is internally divergent but output-masked iff delta_{v,Ch}(tau1, tau2) < infinity and not OD(x). The set of such x is where state-aware comparison could add information beyond output comparison. It is not a set of defects: refactorings produce internal divergence by design (limitation L1). Under binding decision D2 a masked divergence is never a verdict; it can only feed the advisory annotation internal_divergence (8.1b) and only when the optional state-abstraction module E is enabled.

5.8 Witness. [OBSERVATION] A witness is the record w = (V1, V2, s, x, E, D_H, C, v, A_v, k, locus, reruns) with k = delta_{v,C} < infinity and C a subset of C_obs. It is replay-confirmed iff, in r >= r_min independent fresh-sandbox reruns of (V1, x, E) and (V2, x, E) (the value of r_min and the set of perturbed control settings are policy, see P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md), the same outcome and the same observations at the locus are reproduced, and the V1-vs-V1 reruns and V2-vs-V2 reruns are each identical at the locus (self-consistency; guards against a nondeterministic locus). Agreement is therefore at the locus and the outcome, not on the whole-chain hash (2.7); this keeps the nondet_adjusted path reachable. Replay executes under the same isolation profile (1.7); a replay on a weaker profile is invalid. The witness asserts: "under D_H and E, on input x, the two versions produced observations differing at this aligned locus." It does not assert that V2 is wrong, that the change was unintended, or that any specific line is the cause. It makes the claim independently checkable by anyone who can run H. A divergence on the state channel only is a diagnostic record, not a witness for a verdict.

5.9 Propagated impact. [INFERENCE, observed dependency, not causation] Given a witness with locus event e_j in tau2 (or e_i in tau1 if the event is absent in tau2), define
- Fwd(e_j) = set of events reachable from e_j along edges of G_dd(tau2);
- Out(w) = Fwd(e_j) intersect {e : some ob_c(e) is present for c in C_out};
- I_diff(w) = { e in Fwd(e_j) : e is matched by A_v to e' and e !~_C e' } union { e in Fwd(e_j) unmatched by A_v with some ob_c(e) present }.
Out(w) says: output events whose recorded value depends, via observed dataflow in this execution, on the divergent event. I_diff additionally requires a recorded difference at the downstream event. Claims licensed: "downstream of the divergence, in this execution, the following outputs are data-dependent on it, and these of them differ." Claims not licensed: that changing the divergent value would change them (no intervention was performed); that unreached events are unaffected (implicit flows, finer aliasing, and unexecuted paths are missing); that the divergent event is the root cause (an earlier divergence may be hidden by alpha, P3). A causal statement would require an interventional experiment (e.g. patching the value at e_j and observing the outputs) and is outside this specification.

---

# Part II-b. DERIVED OBSERVATION of evidence completeness

## 6. Evidence completeness and observation sufficiency

These quantities are deterministic functions of the recorded explorations. They describe how much was looked at. They are not probabilities of anything.

6.1 Changed region. R is a finite set of changed units (basic blocks, plus pseudo-units for changed dependencies and configuration) obtained from the static diff and phi, covering both V1-only and V2-only units. Each unit b has weight w(b) > 0 (default 1; or statement count, declared). R is an INFERENCE when it depends on a diff algorithm (record the algorithm and version). If R is empty and (src, deps, rt) are identical, the pair is UNCHANGED, an explicit terminal state with no verdict. If R is empty but something differs outside Python AST visibility (non-code files, configuration, native extension sources, dependency versions), the pair is not UNCHANGED: it ends INSUFFICIENT with reason unmodelled_change unless content hashes prove byte equality of all declared inputs. R is never shrunk to the instrumented subset: a changed unit that cannot be instrumented counts as unhit.

6.2 Activation fraction. hit(b) is true iff some input in X_n executed b in the version containing it. act = sum over b in R with hit(b) of w(b), divided by sum over b in R of w(b). act in [0, 1].

6.3 State-abstraction coverage. For each changed function u, a declared finite partition Pi_u of its entry abstract states into cells (product of per-variable classes from a fixed schema: None / bool / int in {negative, zero, one, small positive, large positive} / string or container in {empty, singleton, many} / type tag). Let cells_hit be the number of distinct cells of changed functions entered by some input in X_n, and cells_total the product-space size summed over changed functions (feasibility of cells unknown, so cells_total over-counts). cov = cells_hit / cells_total, in [0, 1]. cov is the coverage of a declared partition, not of the input space; it is a conservative (low) estimate of the coverage of feasible cells.

6.4 Saturation and budget. Let stop in {SATURATED, DOMAIN_EXHAUSTED, BUDGET, ERROR} be the exploration stopping reason. SATURATED: the last K_sat inputs added no new executed unit of R, no new cell, and no new aligned-trace shape. DOMAIN_EXHAUSTED: every x in a declared finite domain D (6.8) has been run. BUDGET: a limit in B was reached first; the budget is measured in cpu_s (1.5). sat = 1 for SATURATED and DOMAIN_EXHAUSTED; sat = k0 for BUDGET with declared constant k0 in (0, 1); sat = 0 for ERROR. Truncated traces (2.2) are counted in the reason set but do not alter sat. A plateau (SATURATED) is one reported factor only; it never confers a sufficiency level by itself (a plateau rewards weak explorers, binding decision D3).

6.5 Observability. Declared channel weights omega_c > 0 for c in C, summing to 1. obs = sum over c in C with c in C_inst and non-degenerate for this scope of omega_c. Non-degenerate means for ret: the scope returns a value with a non-trivial abstraction; for side: io/global mutation instrumentation is active; for state: alpha is supported for the types involved. A scope whose output is not serialisable has ret degenerate. obs in [0, 1]. This factor encodes the V5/V6 finding that an output-free channel is blind to return values.

6.6 Determinism gate. gamma = 1 if delta_det in {DET, CONTROLLED} on the compared channels, gamma = 0 if UNCONTROLLED. gamma is a factor of the sufficiency vector and equals the factor "determinism-confirmed" of the specification file; delta_det is per (V, x, E) (2.4), and any pair-level gamma is an aggregate that the specification defines.

6.7 Sufficiency score. With declared weights w1..w4 > 0, w1+w2+w3+w4 = 1 (default 1/4 each),
S = gamma * act^{w1} * cov^{w2} * sat^{w3} * obs^{w4}.
It is a weighted geometric mean gated by determinism. Alongside S the report always contains the factor vector (act, cov, sat, obs, delta_det, stop, truncation count) and the sufficiency level S1, S2 or S3 (or the INSUFFICIENT reason) assigned by P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md. Mapping of this document's factors to that specification's factors: gamma = determinism-confirmed; obs = instrumentation completeness; act = changed-region activation; cov, sat and the budget state = input diversity and budget. The level is a conjunction of floors on separately reported factors, never the scalar S alone; S is a descriptive index, UNVALIDATED, and the weights are conventions.

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

7.2 False-assurance rate. For verdict NO_DIVERGENCE_OBSERVED(S) and a sufficiency stratum s_j, FAR_j = P(y = div | verdict = NO_DIVERGENCE_OBSERVED, level in stratum j). A point estimate with an exact (Clopper-Pearson) interval from m_j labelled pairs with that verdict of which k_j were divergent is a PROBABILISTIC ESTIMATE valid for the labelled population; pairs are clustered (same program, duplicate groups), so intervals must come from a program-cluster bootstrap or cluster-aware method, not from treating pairs as independent. Claim "S is informative" iff FAR_j is monotone decreasing in S with intervals that separate (E6); until then S is descriptive only.

7.2b Equal definition for every system. False assurance is defined identically for V7 and for every baseline: a system that abstains (INSUFFICIENT, or its own abstention) makes no assurance claim and cannot be falsely assuring; "no difference found" must not be read as an implicit pass for any system, and baselines receive the same sufficiency-based abstention (binding decision D7).

7.3 Sampling bound. If inputs are drawn i.i.d. from a distribution Q on X_s, runs are deterministic and observable under C, and p = Q(x : divergence under C), then P(no divergence in n draws) = (1 - p)^n <= exp(-n * eps) whenever p >= eps. Hence if n >= ln(1/d0) / eps and no divergence is observed, then with confidence 1 - d0 we may assert p < eps (a statement about Q and C only). Premises that routinely fail: coverage-guided or targeted exploration is adaptive and not i.i.d.; Q may not resemble real usage; determinism may not hold. The bound is therefore reported only for the sub-run of i.i.d. sampled inputs, labelled with Q.

7.4 Conformal option. [Option, hypothesis until E6] Split conformal prediction on a calibration set with a nonconformity score s(z, y) (for example 1 minus the predicted probability of y from a model of z) and quantile q_hat = the ceil((n_cal + 1)(1 - a)) / n_cal empirical quantile of calibration scores. The prediction set Gamma(z) = { y : s(z, y) <= q_hat }. Under exchangeability of calibration and test pairs, P(y_test in Gamma(z_test)) >= 1 - a (marginal). If Gamma(z) = {div, nodiv} the system reports INSUFFICIENT; if it is a singleton it may annotate the verdict with that label. Limits: guarantee is marginal, not conditional on S or on program; exchangeability is violated by program clusters, duplicate groups and generator families (calibrate group-wise or leave-cluster-out; use Mondrian conformal by S-stratum if strata are large enough); under distribution shift (benchmark to real code, as BugsInPy shows) coverage can fail silently.

7.5 Ground-truth requirement. y must come from an oracle independent of the exploration that produced z and independent of the mutation generator that produced the pair (independent test suites, a separately specified reference implementation, exhaustive evaluation on small finite domains, or hand verification). A label that is a function of the generator makes every quantity in 7.1-7.4 an estimate of generator fingerprinting rather than of divergence detection. Labels from an oracle are themselves observations on a finite input set, so y has residual noise that must be reported. Exploration may use the label-free changed-region map but never labels, benchmark identity or outcomes of other pairs; any explorer tuning uses the development set only, with pre-declared seeds (binding decision D11).

7.6 A learned score (optional module J) falls here. It may order exploration; it never enters the verdict of section 8.

---

# PART IV. FORMAL CLAIM

## 8. Verdict semantics, annotation and theorems

8.0 Terminal states that are not verdicts. UNCHANGED (6.1) and OUT_OF_SCOPE (the scope is not comparable and cannot be lifted to a common outer frame, 1.2) are explicit terminal states. They are not elements of the verdict set.

8.1 Verdict set (binding decision D1). The canonical definition of sufficiency levels S0-S3, their floors, level assignment and the reason-code semantics is P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md; this section cites it and states no threshold. Per-input outcome o(x) for x in X_n: OBS_DIFF_CONFIRMED (a replay-confirmed difference on C_obs), OBS_DIFF_UNCONFIRMED (a difference on C_obs that replay did not confirm), NO_DIFF_OBSERVED, NO_RUN(reason). Let C_obs = {ret, exc, side}: return value, exception type and message class, declared side effects. For (V1, V2, s) with explored inputs X_n, environment E, declaration D_H, view v and budget B, apply the rules in order, first match wins:
1. DIVERGENT_OBSERVABLE iff some x in X_n has o(x) = OBS_DIFF_CONFIRMED: a replay-confirmed witness (5.8) in which an observed channel differs on deterministic-confirmed runs of both versions on the same input and environment. The witness set W is returned. The state channel never makes a verdict.
2. Otherwise INSUFFICIENT(reason_code) iff no confirmed witness exists and at least one of: (a) the sufficiency level is below S1; (b) alignment failed where alignment is required (5.6b); (c) unresolved nondeterminism on a compared channel; (d) capture is incomplete (truncation, dropped kinds, blind spot dominant, partial instrumentation); (e) budget, sandbox or isolation failure (including a run on v6_compat or below the minimum isolation profile, timeout, tool error); (f) signature or entry mismatch that is not handled, no valid input, import failure, or an unmodelled change; (g) some o(x) = OBS_DIFF_UNCONFIRMED (reason flaky_witness). The reason set is nonempty and drawn from the closed enum of SBG_V7_DATA_AND_EVIDENCE_SCHEMA.R1.md section 2.16 (primary reason plus secondary reasons).
3. Otherwise NO_DIVERGENCE_OBSERVED(S), S in {S1, S2, S3} the level assigned by the specification file: no confirmed witness, alignment valid, level at least S1. S0 exists only inside INSUFFICIENT.
Precedence 1 > 2 > 3.

Prohibited outcome names. There is no equivalence verdict anywhere. EQUIVALENT, SAME, PASS, VERIFIED, SAFE and "implicit pass" are not outcomes of any pair, system or baseline. Bounded equivalence exists only as the separately named FORMAL CLAIM BOUNDED_EQUIVALENCE_PROVEN (8.5, 8.6) with its stated domain; it is a record of class proof, never a value of Verdict.

Verdict identity. A verdict is a function of (pair, scope, D_H, seed policy), not of a particular run order. Rates (FAR, detection) are defined per seed and reported across the pre-declared seeds. A DIVERGENT_OBSERVABLE verdict carries no sufficiency score (it is a witnessed fact); sufficiency is scored only for NO_DIVERGENCE_OBSERVED.

8.1b Internal-divergence annotation (binding decision D2). Internal-only divergence is NOT a verdict. internal_divergence in {none, observed, unknown} is an advisory annotation attached only to pairs whose verdict is NO_DIVERGENCE_OBSERVED or INSUFFICIENT, and only if the optional state-abstraction module E is enabled; otherwise the field is absent. observed: some input has a masked divergence (5.7 P4) under alpha with alignment trust at or above the gate (5.6b). none: no state-channel divergence on inputs whose state coverage meets the declared floor. unknown: anything else (state not covered, alignment untrusted, alpha unsupported for the types). It is an INFERENCE with status uncertain. The truth class INTERNAL_ONLY cannot be defined independently of the SBG abstraction and alignment on real regressions (red-team Q3, Blocking); therefore no confirmatory hypothesis (H7, H8) depends on this annotation, and it is evaluated only in an exploratory pilot on authored-by-construction mutants with an independent reference state-dump tool. The validation row "internal change masked by outputs" is a pilot diagnostic, not a gate.

8.2 Proposition (absorption of DIVERGENT_OBSERVABLE). Fix everything except X_n. If the verdict is DIVERGENT_OBSERVABLE for X_n and X_n is a subset of X_n', the verdict for X_n' is DIVERGENT_OBSERVABLE, unless a witness is voided by a failed replay (an invalid-evidence event, 0.1.6) and no other confirmed witness remains. Proof: a replay-confirmed witness for x in X_n remains one in X_n'; rule 1 has the highest precedence. Corollary: DIVERGENT_OBSERVABLE is monotone in X_n up to witness invalidation, while NO_DIVERGENCE_OBSERVED(S) and INSUFFICIENT are not: further exploration may turn either into DIVERGENT_OBSERVABLE.

8.3 Theorem 1 (witness soundness, relative to the harness). Assume A1, A2, A10, A11 (section 9) and that the witness is replay-confirmed. Then V1 and V2 are not equivalent on input x under (~_C, N, E): there is an aligned step or terminal comparison at which recorded observations of an observed channel differ. If C equals the externally visible contract of s, then V1 and V2 violate behavioural equivalence with respect to that contract. Proof: by definition 5.6, delta < infinity means a non-conforming step exists; replay confirmation with A2 excludes nondeterminism as the explanation of the observed locus; A1 ensures recorded events are what executed. It does not follow that V2 is incorrect, that an intended change was not made, or that the locus is the cause.

8.4 Theorem 2 (NO_DIVERGENCE_OBSERVED does not imply equivalence, at every sufficiency level). There exist V1, V2, s, an input set X_n and a harness satisfying A1-A11 such that the verdict is NO_DIVERGENCE_OBSERVED at the highest level S3 with act = cov = sat = obs = gamma = 1 and S = 1, while V1 and V2 are not equivalent on X_s.
Proof by construction. Let s be a function of one integer argument. V1 returns x. V2 returns x + (1 if x == 123456789 else 0), written on the same single line. Changed region R = {that block}. Any X_n not containing 123456789 executes the block (act = 1); take the declared cell partition to be the sign/zero/size classes and let X_n hit all of them (cov = 1, and the cell partition cannot separate 123456789 from other large positives); exploration reaches a plateau (sat = 1); ret is observed (obs = 1); runs are deterministic (gamma = 1). Every run produces equal observations on all channels, so no divergence is recorded and every floor of the specification can be met, so the verdict is NO_DIVERGENCE_OBSERVED at the top level. But V1(123456789) != V2(123456789). QED. Consequence: no threshold on S, act, cov or any finite-sample statistic of the dynamic tier converts NO_DIVERGENCE_OBSERVED into an equivalence claim; the dynamic tier never emits the word "equivalent" as an outcome.

8.5 Theorem 3 (bounded guarantee, a FORMAL CLAIM). Let D be a finite subset of X_s and C a subset of C_obs. Suppose
(G1) D is a subset of X_n and every run (V1, x, E), (V2, x, E) for x in D terminates in RET or EXC within B with no truncation;
(G2) assumptions A1, A2, A3, A5, A6, A10 and A11 hold (faithful isolated harness, determinism, input round-trip, correct normaliser, identical environment);
(G3) every channel in C is observed (C subset of C_inst) and the terminal comparison of 5.6 is applied;
(G4) for every x in D no divergence on C is recorded, confirmed or unconfirmed.
Then for every x in D the terminal observations of V1 and V2 on C are N-equal: V1 and V2 are observationally equivalent on D under C, N and E. Proof: for each x in D, delta_{v,C} = infinity implies in particular that the terminal comparison of 5.6 conforms (it is part of the definition), and G1 ensures a terminal observation exists for each x. Equality is by definition of ~_C. QED.
The claim is emitted as BOUNDED_EQUIVALENCE_PROVEN(D, C, N, E), a record of class proof with method exhaustive_domain, domain D recorded and premises G1-G4 recorded. It is not a verdict value and does not change the verdict of the pair. What the theorem does not give: any claim for x outside D; any claim under a different E; any claim for channels outside C; any claim about internal state. The small-scope heuristic (bugs tend to have small counterexamples) is a hypothesis about program populations, not a consequence of Theorem 3 [HYP, test: fraction of known regressions in the benchmark that have a witness within the declared D; E1/E6].

8.6 Formal tier (optional, outside the dynamic pipeline). The formal tier has two methods: exhaustive_domain (8.5, no solver) and solver-based checking (bounded symbolic equivalence or regression verification on small units). The solver-based method yields BOUNDED_EQUIVALENCE_PROVEN(k, M, solver): under unrolling bound k, semantic model M of the language fragment, and a sound solver, V1 and V2 return equal results and raise equal exceptions on all inputs satisfying a stated precondition. It is of a different class from Theorems 1-3, depends on the fidelity of M and the solver, and is the only mechanism by which an unbounded-domain statement may be made. The word "equivalent" is licensed only for these proof records, always with the domain or bound.

8.7 Proposition (monotonicity in channels). By P1, if C is a subset of C' and both are subsets of C_obs and DIVERGENT_OBSERVABLE holds for C, it holds for C' on the same explored inputs. The converse fails by P4 only for channels outside C_obs (masked divergence), which never carry a verdict.

8.8 Proposition (the verdict rules are exclusive and exhaustive). On every pair not in a terminal state (8.0), exactly one of DIVERGENT_OBSERVABLE, INSUFFICIENT, NO_DIVERGENCE_OBSERVED holds. Proof: the rules are ordered; rule 1 tests the existence of a confirmed witness; rule 2 applies when rule 1 fails and any of its listed conditions holds; rule 3 is the final else and requires that none of them holds. QED. Two changed functions in one scope with a confirmed witness on one of them give DIVERGENT_OBSERVABLE by precedence, and the sufficiency of the other function is not scored.

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
- A10 Isolation: every run satisfies the isolation profile of 1.7 (fresh child process, rlimits, process-group kill, tracing outside user-code reach with evasion detection, network denied, write confinement) and each property has passed an experimental check. Status: UNVERIFIED except sandbox-exec network and write denial (P0). A detected violation makes the run invalid evidence.
- A11 Replay regeneration: replaying the recipe rho (1.8) in the same harness regenerates the same event stream and chain root (checked on witness runs and on an audit sample, not proved).

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
- L13 Verdicts depend on the declaration D_H and the seed policy (8.1); a different channel configuration, message-only exception handling, float tolerance or seed can change the outcome, which is why both are part of verdict identity.
- L14 Control is not behaviour preservation across versions. A refactor that changes the number or order of random draws, clock reads or set insertion order produces a deterministic, replayable difference under fixed seeds that replay confirmation cannot detect, because the controls remove the variability replay would expose. Mitigation (perturbation of control settings during witness replay, routing of RNG-, clock- or order-sensitive regions to INSUFFICIENT) is policy of the specification file; the residual false-divergence risk is UNQUANTIFIED.
- L15 A genuine distributional regression (a version that differs only in probability under uncontrolled randomness) is not representable by this verdict set; it ends INSUFFICIENT with reason nondeterministic.

## 11. Claim-status table

| statement | claim label | evidence class (status) | basis | what would falsify or weaken it |
|---|---|---|---|---|
| Replay-confirmed witness: versions differ on input x on an observed channel under D_H, E | OBSERVATION (+ Theorem 1) | derived on observation | recorded runs, replay at locus and outcome | harness bug (A1), isolation failure (A10), flaky locus (A2), wrong N (A5) |
| First divergence locus at aligned step k | INFERENCE | inferred (uncertain) | alignment A_v, ambiguity reported | alternative optimal alignment, amb > 0; E5 mismatch with hand alignment |
| Output reachable from divergence by dependence | INFERENCE (observed dependency) | inferred | G_dd of one execution | any need for causal wording; intervention experiment disagreeing |
| Sufficiency factor vector and level | OBSERVATION (descriptive) | derived (uncertain, ordinal) | recorded coverage and flags; level per the specification file | none for the vector; any probabilistic reading is unsupported |
| internal_divergence annotation | INFERENCE | inferred (uncertain) | module E, alpha, alignment trust | alpha masks the difference; alignment untrusted; no independent truth class (D2) |
| Missing item for a claim | OBSERVATION about the store | derived (missing) | absence of a valid record for Req(c) | a valid record is found |
| Invalidated record or witness | OBSERVATION | derived (invalid) | failed replay, supersession, isolation or assumption violation | the invalidation rule was applied wrongly |
| FAR by stratum, risk-coverage, conformal sets | PROBABILISTIC ESTIMATE | inferred (uncertain, calibrated) | independent labels, cluster-aware intervals | label contamination, exchangeability failure, shift |
| i.i.d. sampling bound p < eps at confidence 1 - d0 | PROBABILISTIC ESTIMATE | inferred (uncertain, bound) | premises of 7.3 | non-i.i.d. exploration, nondeterminism |
| NO_DIVERGENCE_OBSERVED does not imply equivalence | FORMAL CLAIM | proof | Theorem 2 | none (it is a counterexample proof) |
| Observational equivalence on finite D under C: BOUNDED_EQUIVALENCE_PROVEN | FORMAL CLAIM | proof (method exhaustive_domain) | Theorem 3, premises G1-G4 | violation of any premise, e.g. truncation or uncontrolled nondeterminism |
| DIVERGENT_OBSERVABLE absorbing under extension of X_n | FORMAL CLAIM | proof | Proposition 8.2 | witness not replayable (then it is void by definition) |
| Verdict rules exclusive and exhaustive | FORMAL CLAIM | proof | Proposition 8.8 | none |
| Unbounded equivalence BOUNDED_EQUIVALENCE_PROVEN(k, M, solver) | FORMAL CLAIM (formal tier only) | proof (method solver) | external solver, semantic model | model infidelity, unsoundness of solver |

## 12. Disagreements with the spine

1. Spine asks for "a precise monotone sufficiency score". Provided (6.7), but the verdict uses componentwise floors, not the scalar, because a scalar hides which factor failed and invites a confidence reading that is not supported (L7).
2. Spine says alignment is "static matching seeded by dynamic anchors". Provided with a restriction: anchors may use context and external events only, not the compared payload (5.2), to avoid circular agreement. Whether this suffices is E5.
3. Spine says equivalence "is only asserted by an optional formal tier". Amended: exhaustive evaluation over a finite declared domain gives a bounded observational equivalence (Theorem 3) without a solver, recorded as the formal claim BOUNDED_EQUIVALENCE_PROVEN; it is never a verdict value, and the dynamic tier never claims unbounded equivalence.
4. Spine's "first-divergence index" is not well defined without choosing an alignment; it is defined here as alignment-relative with an ambiguity report (5.4, 5.6), and as an upper bound on the true first divergence (P3).
5. Spine's "earlier detection of masked divergences" as the value proposition presupposes that internal divergence is informative. That is a hypothesis (L1, L12), and it needs labels independent of the mutation generator (7.5).

6. R1: the original's "DIVERGENT" over a possibly state-bearing channel set is split. Verdicts are defined on C_obs only; internal-only divergence is an advisory annotation (8.1b), because its truth class cannot be defined independently of the SBG abstraction and alignment on real regressions.
7. R1: the original scalar-or-floor sufficiency (6.7, 8.1 floors) is replaced for level assignment by the single definition in P0_VERDICT_AND_SUFFICIENCY_SPECIFICATION.md; the scalar S stays as a descriptive index.

## Appendix A. Name map from the original

| original name | R1 name |
|---|---|
| DIVERGENT | DIVERGENT_OBSERVABLE |
| DIVERGENT_INTERNAL_ONLY, internal_only_difference | annotation internal_divergence = observed (8.1b) |
| EQUIV_BOUNDED(k, M, solver) | BOUNDED_EQUIVALENCE_PROVEN(k, M, solver) |
| NO_INPUTS, UNSUPPORTED_SIGNATURE, IMPORT_FAILURE | no_inputs, unsupported_signature, import_error |
| NONDETERMINISTIC | nondeterministic |
| NOT_ACTIVATED | changed_region_not_activated |
| LOW_STATE_COVERAGE | low_state_coverage |
| BUDGET_EXHAUSTED | budget_exhausted |
| CHANNEL_BLIND | unobservable_outcome |
| SANDBOX_FAILURE | sandbox_failure |
| FLAKY_DIVERGENCE | flaky_witness |
| event kinds ret, exc, read, write, io, alloc | return, exception, data_use, data_def, side_effect or external_call, resource |
| budget B without CPU term | B with canonical cpu_s |