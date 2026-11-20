# P0: Ground-Truth Protocol for the INTERNAL_ONLY Truth Class

Status: DRAFT for freeze at G0 (amends SBG_V7_EXPERIMENTAL_PROTOCOL.md "EP" sections 1, 3.5 and H7/H8; nothing here has been run). Companion: P0_BENCHMARK_AND_POWER_ANALYSIS.md.
Evidence used (read-only): EP; SBG_V7_VALIDATION_AND_ACCEPTANCE_GATES.md (row 9); SBG_V7_MATHEMATICAL_SPECIFICATION.md sections 3, 5.5 to 5.9 (P4 "masked divergence"); SBG_V7_DATA_AND_EVIDENCE_SCHEMA.md; SBG_V7_FAILURE_TO_REQUIREMENT_MATRIX.md (F-04c, R-16); SBG_V6_FINAL_ARCHITECTURE.md; artifacts/v6/audit/LABEL_ADJUDICATION_SUMMARY.json.

Design rule of this document: the truth label INTERNAL_ONLY (IO) is defined and established WITHOUT any SBG output, SBG-selected input, SBG state abstraction (alpha_{d,p}), SBG normaliser, SBG alignment or SBG divergence locus. SBG's own "masked divergence" notion (math spec P4: delta_{v,Ch} < infinity and not OD(x)) is the thing being MEASURED against IO truth (H8), never the definition of it.

## 1. Formal definition

### 1.1 Declared objects (all fixed and hash-committed per pair BEFORE any SBG or baseline run on that pair)

- Pair: (V1, V2, s) with scope s (function/class/entry-point set with drivable signature).
- Input domain X: the set of call sequences (length <= k, default k = 1; k >= 2 required for pairs whose change is to persistent state) drawn from a declared domain. Two kinds: X_b (small, enumerable, bounded; at most 10^6 inputs) and X_ref (the truth team's larger spec-driven or generator-driven set, used for activation and for non-exhaustive evidence). X is declared by the truth team from the contract/docstring/spec; SBG never contributes to X.
- Observation boundary B = (C_out, N_out): C_out is the set of externally observable channels = {return value, uncaught exception type, declared side effects (arguments mutated in place, globals written, sandbox files, stdout/stderr)}; N_out is the declared output normaliser (type-aware equality; float tolerance; repr artifacts such as deque vs list equal if values equal; exception message OFF; non-documented-order containers compared as multisets only if documented unordered). B is a column in the pair record. The default is B_default (EP section 1). A wider boundary B_wide (adds exception message and logging) is used only for the boundary-sensitivity analysis in 1.5.
- Observed-output difference: OD_B(x) := N_out(out(V1,x)) != N_out(out(V2,x)) on C_out, where out also includes termination class (return / exception / timeout, timeout reproducible 3/3 at 2x).
- Internal observation-equivalence kappa (section 3): a function kappa mapping a concrete execution state to a canonical internal view. Two concrete states sigma, sigma' are internal-equivalent iff kappa(sigma) = kappa(sigma').
- Declared internal-predicate family Pi = {pi_1..pi_r}, written in a Predicate Declaration File (PDF) by the reference-harness (RH) team. Each pi is a pair (anchor, view): an anchor is a source location or contract-level state location that exists in both versions with the same semantic role (human-mapped, section 2.2); a view is kappa applied to a named value or to the post-call private state (fields, caches, memo tables, counters) of an object reachable from the arguments, self or module globals that is NOT in C_out. pi(sigma_V(x)) is the kappa-canonical value of that view at the anchor in version V on input x (first-hit, last-hit and multiset-of-hits variants are declared per pi).
- Internal difference at x: Phi(x) := exists pi in Pi with pi(V1, x) != pi(V2, x), on a run that is deterministic (V1-vs-V1 and V2-vs-V2 reruns identical at the anchor, r >= 5 fresh-sandbox reruns).
- Masked difference at x: M(x) := not OD_B(x) and Phi(x).

This gives the per-witness statement requested: "outputs are equal on the witness under the stated observation boundary, but a pre-declared internal-state predicate differs".

### 1.2 Pair-level truth classes (five; relative to X and B)

Let Act(x) = changed region executed on both versions at input x (RH coverage tool, section 2.2).

1. OBSERVABLE (Div): exists x in X with OD_B(x). (Any M(x') elsewhere is irrelevant: the pair is Div. Per-input M annotations are retained for H7 analysis.)
2. INTERNAL_ONLY (IO): for all x in X, not OD_B(x) (universal claim, evidence tier T1 or T2, section 2.3) AND exists x in X with Act(x) and Phi(x).
3. REPRESENTATION_ONLY (RO): for all x in X, not OD_B(x) (T1/T2) AND for all x in X, not Phi(x), although the concrete code, AST, trace, call graph or raw state differ. RO covers refactorings and re-representations (rename, reorder, temp variables, extract/inline, loop/comprehension, container type changes normalised by kappa) and statically dead changes.
4. UNACTIVATED: the changed region is reachable (not proven dead, T2) but no x in X_ref has Act(x). Neither Div, IO nor RO can be asserted. (V6 fact: 61 of 1332 changed pairs; "test inadequacy, NOT equivalence".)
5. INSUFFICIENT_OR_AMBIGUOUS: anything else, with a mandatory reason code: UNIVERSAL_CLAIM_NOT_ESTABLISHED (no T1/T2 for the "not OD on all of X" claim; fuzz-only evidence), PREDICATE_UNDECLARABLE, BOUNDARY_SENSITIVE, NONDET, ADJUDICATOR_DISAGREEMENT_UNRESOLVED, RH_TOOL_DISAGREEMENT.

EP's four-class scheme maps as: Div = 1; INTERNAL_ONLY = 2; Eq-B = 3 plus the provably-dead subset; Undecided = 4 and 5 (the split of Undecided is new and is reported). Counts of every class are reported for every source.

### 1.3 What the definition deliberately does not claim

- IO is relative to (X, B, Pi, kappa). It is a statement "no observable difference on the declared domain", not behavioural equivalence in general. A later system-found witness outside X does not refute IO (section 2.6) but is logged.
- IO is not "defect-free": IO pairs include masked bugs and intended changes. It is a measurement class for H8.
- Internal state that is never declared in Pi is not counted. Pi is intentionally conservative (section 3), so some real latent differences are not IO; they fall to RO or INSUFFICIENT (PREDICATE_UNDECLARABLE).

### 1.4 IO versus Div for persistent state (call sequences)

A private-state difference after call 1 that changes an output only in call k+1 is Div if the declared X includes sequences of length >= k+1, and IO if X is limited to shorter sequences and the difference is not exposed. Because this makes IO depend on k, every IO label records k, and pairs whose class changes between k = 1 and k = 3 are tagged BOUNDARY_SENSITIVE and excluded from the H8 primary analysis (reported separately).

### 1.5 Boundary sensitivity
Every IO/RO/Div label is recomputed under B_wide. Pairs whose class differs between B_default and B_wide are tagged BOUNDARY_SENSITIVE (e.g. logging-only or message-only changes; gates row 8 notes logging is "expected N/INTERNAL_ONLY by rubric"). They are excluded from H8 primary and reported with counts.

## 2. How ground truth is established independently of SBG

### 2.1 Team and tool separation (hard requirements)
- Custodian C (not a V7 implementer) owns the truth pipeline. RH team members have no commits to V7 modules A to I and no access to V7 outputs for the pair under evaluation.
- Repository boundary: the RH code lives in a separate package that must not import, vendor or copy V7 modules (CI check: import graph audit plus a token-similarity scan against V7 capture/normaliser code, threshold fixed in advance).
- Mechanism diversity: RH must use a different capture mechanism than V7 module B. If V7 B uses runtime tracing hooks, RH-A uses source-level AST probe insertion at the declared anchors (explicit dump calls) and RH-B uses a debugger-protocol or interpreter-level snapshot (a third mechanism). The canonicalisation kappa is re-implemented from section 3 of this document, not derived from V7's alpha.
- Two-tool rule: Phi must be established by both RH-A and RH-B for IO/RO decisions on mechanical pairs; disagreement produces INSUFFICIENT (RH_TOOL_DISAGREEMENT) pending adjudication.

### 2.2 Methods (each yields evidence with a tier; the pair record states which were used)
M1. Mutation-by-construction (H-M "masked internal change" and "refactoring" families). Authors who are not V7 implementers and have not seen V7 output apply a template from a closed, hash-frozen catalogue. IO templates: redundant intermediate transform that is later overwritten or cancelled; paired increment/decrement; different accumulation order of exact integers; extra or different private counter/cache/memo contents that never feed outputs within X; alternative intermediate representation normalised before return; early assignment that is overwritten. RO templates: rename of locals/functions, statement reordering of independent statements, temp introduction, extract/inline, loop to comprehension, if/else inversion, tuple swap vs temp. Each item ships a construction certificate: (a) intended class recorded BEFORE verification; (b) output equivalence over X_b by exhaustive enumeration (T1) or SMT/algebraic proof (T2); (c) for IO, an RH-demonstrated input x_Phi at which Phi holds; for RO, RH shows Phi false on all of X_b and on a metamorphic battery (2.4). Items whose verified class differs from the intended class are relabelled and the mismatch logged (a template-quality statistic).
M2. Independent reference instrumentation (RH-A, RH-B): produce, per (version, input, anchor), a canonical state-dump JSON; the diff is computed by a comparison script implementing kappa. Anchors come from the PDF.
M3. Human adjudication of the diff plus the RH state dump (section 4), for real-regression controls and any pair where M1 certificates do not apply.
M4. Bounded exhaustive verification: enumerate X_b (e.g. ints in [-8,8]; lists of length <= 5 over an alphabet of 3; strings of length <= 4 over 3 symbols; products of up to 3 arguments, capped at 10^6 inputs). This is the only route to the universal claim "not OD_B on all of X" besides proof. Where the true domain is larger than X_b, the label is IO-bounded with the bound stated; the claim is restricted to X_b.
M5. Spec-driven differential run on X_ref by the truth team's own generator (property-based, at least 10^5 inputs and 100% branch coverage of the changed region, RH coverage tool). This yields T1-f (fuzz) evidence: sufficient for Div (any witness is conclusive) and for Unactivated, NOT sufficient for IO/RO (those need T1-b exhaustive or T2); fuzz-only no-OD pairs become INSUFFICIENT (UNIVERSAL_CLAIM_NOT_ESTABLISHED), reported as IO-candidate sensitivity.

Predicate Declaration File and anchors. For each pair the RH team writes, from the old/new source and a change summary only: (i) B (channels, N_out); (ii) X_b and X_ref; (iii) Pi with anchors; (iv) the class they expect, optionally. The file is hashed and time-stamped in the ledger before any V7 or baseline process touches the pair. Amending a PDF after a system has run on the pair is forbidden; such a pair is marked PDF_AMENDED and excluded from confirmatory analysis.

### 2.3 Evidence tiers for truth
T1-b: exhaustive over X_b. T2: proof or bounded symbolic equivalence. T1-f: fuzz/spec-driven >= 10^5 inputs with changed-branch coverage. T3: expert reading with written argument. Class assignment: Div requires one RH-replayed witness (any tier). IO and RO require T1-b or T2 for the universal OD claim. T3 alone yields INSUFFICIENT unless both adjudicators concur in writing (then IO/RO with confidence "medium"). These tiers extend EP 3.5 item 2 and keep its numbering of T0 to T3.

### 2.4 Metamorphic predicate-sanity battery (guards against counting representation noise)
Before a PDF is accepted, Pi is run on V2 against V2' obtained by independent semantics-preserving rewriters (rename all locals, reorder independent statements, introduce temporaries, wrap in a helper function, swap list/tuple intermediates). Phi must be false for every rewrite on every x in a sample of >= 200 inputs. A predicate that fires on a rewriter is deleted from Pi. Programme-level gate: across all accepted PDFs, the RO-battery false-IO rate must be 0 on the pilot set; any positive rate triggers a kappa/Pi revision before sealing.

### 2.5 Ground truth for the masked-versus-exposed boundary
A masked difference exposed only on a rare region is Div (gates row 9b), established by the truth team's spec-driven generator or the oracle in M1, not by SBG. The universal claim for IO therefore carries the burden: for H-M the item author must provide T1-b/T2; for H-R controls IO is expected to be rare and mostly INSUFFICIENT.

### 2.6 Refutation channel (only direction allowed)
After system outputs are written and hashed, any replay-confirmed OD witness produced by ANY arm (V7, each baseline, ablations) on a pair labelled IO, RO or Eq-B is sent to RH for independent replay. If RH reproduces OD_B within X, the pair is re-adjudicated to Div (label_revised, with the witness id); if the witness lies outside X, the label stands and the item is logged OUTSIDE_DOMAIN_WITNESS. Revisions are applied identically to all arms, counted per arm and reported with and without revision (original adjudicated labels = primary for H8, revised as sensitivity; see circularity path C5).

## 3. Internal observation-equivalence classes (what counts as an internal difference)

kappa is a composition of the following reductions, applied in order to the named view before comparison. Rules R1 to R9 define when two internal states are "the same":

R1 Alpha-renaming: local variable and parameter names are replaced by role labels from the PDF anchor map (or by order of first definition inside the anchored scope). Renaming alone never counts.
R2 Dead/temporary values: a local that is not live at the anchor, or that has no counterpart in the anchor map, is dropped. Variables introduced only in one version are temporaries unless they persist beyond the call (field, global, closure cell, cache entry, returned-container internals) or the PDF maps them.
R3 Statement order of independent effects: the multiset (not sequence) of writes to distinct locations between two anchors is compared when the writes commute (declared by the PDF as independent). A sequence difference between independent writes never counts.
R4 Call-structure collapse: extract/inline/helper-wrapping is quotiented by comparing values at anchors in the scope's contract frames only; intermediate frames introduced by refactoring are collapsed into their caller.
R5 Container representation: list/tuple/deque/array and set/frozenset differences normalised by the same declared normaliser class as N_out (element sequence for ordered, multiset for documented-unordered); dict insertion order ignored unless documented ordered.
R6 Identity and address: no ids, addresses, default reprs, hash seeds (PYTHONHASHSEED=0 plus an explicit address scrub).
R7 Numeric precision: floats compared with the PDF tolerance (default 1e-9 relative); exact for ints/bools/strings.
R8 Evaluation strategy: lazily versus eagerly computed values (generator vs list) compared after forcing to the declared concrete sequence.
R9 Nondeterminism: values that differ between two reruns of the same version are excluded (the pair becomes INSUFFICIENT NONDET if the anchor itself is unstable).

A state difference COUNTS as Phi iff it (a) is at a PDF-declared anchor or contract-level private state, (b) survives R1 to R9, (c) is reproducible over r >= 5 fresh reruns, and (d) is detected by BOTH RH-A and RH-B (mechanical pairs). Control-flow differences count only when they change the value of a declared anchor view or the declared anchored decision (a branch/decision location mapped in the PDF); an unmapped extra branch is a temporary.

Worked classification (rubric appendix, pilot items drawn from V6 families, labels recorded as examples not rules): V6 "activated; internal trace differs but output identical (masked)" (180 pairs; SC-4 69, SC-13 30, SC-1 25) become IO only if the divergent trace element survives R1 to R9 at a PDF anchor; a divergent call graph alone (e.g. V6 SP-5, SP-8 style refactors) is RO. V6 "repr_only_container_type (deque vs list)" (42 pairs) is RO by R5/N_out. V6 "exception_type_differs" (47) is Div at B_default.

## 4. Adjudication procedure

Applies to all H-M IO/RO/Insufficient items, all H-R control pairs, every pair where RH and the original label disagree, every pair with RH-A/RH-B disagreement, and a random 20% of Div and Unactivated items (audit).

1. Preserve: `label_original` (generator or commit-derived intent) is immutable. Additional immutable fields: `label_rh` (mechanical class from the truth harness), `label_a1`, `label_a2`, `label_a3` (if used), `label_final`. Nothing is overwritten; both original and final are reported (final primary).
2. Evidence package for adjudicators (built only from RH, never from V7/baselines): V1/V2 source diff, PDF (B, X, Pi, anchors), RH dump diff at anchors, exhaustive/fuzz results and tier, coverage of the changed region, metamorphic-battery result. Adjudicators do not see: any V7 or baseline output or verdict, any SBG report, `label_original` (hidden until both votes are locked, to measure independent agreement), the other adjudicator's vote.
3. Two blind adjudicators A1, A2 (independent, not V7 implementers; at least one with no involvement in authoring the item) classify into the five classes with a reason code and a confidence (high/medium/low), following the versioned, hashed rubric R-IO v1. The rubric contains rules for: repr artifacts (R5), exception messages (off), non-contractual ordering, logging-only effects (boundary-sensitive), performance-only changes (not divergence), non-termination (Div if 3/3 at 2x), per-class decision tree (section 1.2), and the R1 to R9 table.
4. Agreement targets. Pilot on >= 60 DEV-N items stratified to contain >= 15 IO, >= 15 RO, >= 10 Div, >= 10 Unactivated, remainder Insufficient. Targets: five-class Cohen's kappa >= 0.80 (lower 95% CI bound >= 0.70); and the contested boundary IO versus RO as a binary kappa >= 0.75 (lower bound >= 0.65). Because IO prevalence is low (5% to 30%), kappa is depressed by the prevalence paradox, so also report PABAK, positive specific agreement on IO, and negative specific agreement. If either point target is missed or a lower bound falls below its floor, revise the rubric and re-pilot on fresh items (the failed pilot items are burned for rubric tuning). With 60 items the kappa standard error is about 0.08, so pilot results are screening, not proof; the production double-rated sample (all IO/RO/Insufficient items plus the 20% audit, at least 100 items) gives the reported interval.
5. Disagreements: logged (item id, A1, A2, rationale, rubric version). A3 resolves blind to who voted what, writes a rationale, pre-resolution votes kept. Unresolved after A3 (three-way split) becomes INSUFFICIENT (ADJUDICATOR_DISAGREEMENT_UNRESOLVED). Systematic disagreement categories drive rubric amendments before unseal only.
6. Logging: append-only JSON Lines ledger, each line SHA-256-chained to the previous; fields: item id, actor, role, timestamp, rubric hash, PDF hash, evidence-package hash, vote, reason code, confidence, tool versions. Intra-rater reliability: 10% of items re-rated by the same adjudicator after >= 4 weeks.
7. Freeze: labels are fixed and written to `labels.sealed` (EP 3.3) before unseal. Post-unseal changes are not applied to the primary analysis; they appear only in sensitivity analyses flagged POST_UNSEAL.
8. Undecided handling follows EP 3.5 item 6: excluded from primary denominators, always reported; sensitivity bounds with all Undecided as Div / as Eq-B; for H8 additionally all INSUFFICIENT counted as IO (and as Div). If Undecided exceeds 15% of any source, the source is flagged and the claim restricted. (V6 fact: 116/1332 = 8.7% unresolved; plus 61 not exercised = 4.6%.)

## 5. Explicit circularity analysis

Each row is a path by which SBG could classify a case using evidence that also determined, or leaked into, its label, with the control. "Audit" means a checked, logged control, not an assumption.

| # | Circular path | Control |
|---|---|---|
| C1 | IO defined through SBG's state abstraction alpha_{d,p}, divergence delta_{v,Ch} or the P4 predicate | Phi is defined by kappa and Pi (this document) and implemented in RH; alpha/d/p are not used; kappa vs alpha differences are reported as a descriptive table |
| C2 | RH shares code, normaliser N, or capture mechanism with V7 module B (same hooks yield same artifacts) | Separate package, import-graph and similarity audit, mechanism diversity, two RH tools that must agree, kappa re-implemented from section 3 |
| C3 | Authors of M1 templates tuned them to what SBG's state view detects | Authors never see V7 output; template catalogue hashed before any V7 run; family-level results reported; template-mismatch rate logged |
| C4 | SBG-selected or SBG-generated inputs establish truth (an OD found only because SBG found the input) | Truth inputs come only from X_b/X_ref built by the truth team; SBG inputs enter only through the refutation channel (C5) |
| C5 | Refutation channel lets system witnesses revise labels | Union over ALL arms, RH replay required, one direction only (toward Div), identical application to all arms, counts per arm, primary analysis on pre-revision adjudicated labels with revised labels as sensitivity |
| C6 | Adjudicators see SBG verdicts, evidence chain or reports | Evidence package built from RH only; blind; leak audit (grep for V7 artifact ids in adjudication packages and logs) |
| C7 | Adjudicators rubber-stamp the generator's intended label | `label_original` hidden until votes are locked; disagreement between final and original reported per family |
| C8 | Pair inclusion or exclusion depends on SBG behaviour (keep pairs where the state view fires; drop SBG-INSUFFICIENT pairs) | Inclusion rules fixed before mining and based only on syntactic/RH criteria; exclusion ledger; intention-to-treat analysis on all included pairs |
| C9 | Predicates Pi declared after seeing SBG's locus (post-hoc tailoring) | PDF hashed and ledger-stamped before any system runs on the item; PDF_AMENDED items excluded from confirmatory analysis |
| C10 | Tuning of the state abstraction, annotation rule or thresholds on the same items used for H8 | Sealed H-M/H-R; thresholds frozen at G6; H8 not computed on DEV items; V5/V6 sets stay NON-PRISTINE and are never confirmatory |
| C11 | SBG's normaliser N defines "equal output", so output-level truth inherits SBG's equivalence | N_out declared in the PDF by the truth team; discrepancy list between N_out and V7's N is reported; items on which they differ are flagged |
| C12 | SBG's annotation merely mirrors raw state diffs, and IO labels are also built from raw state diffs, so agreement is by construction | RO negative controls: pairs with large raw trace/state differences that vanish under kappa. An INTERNAL_ONLY annotation on RO counts as an error (proposed H8c below); kappa-based Pi and metamorphic battery |
| C13 | "Hard stratum" membership (seed-corpus outputs equal) defined by an SBG run | Hard stratum defined by the common seed corpus given to all arms (EP 7) and run by the truth harness, never by V7 output |
| C14 | "Unactivated" truth derived from V7's activation trace or S-levels | Activation measured by an independent coverage tool in RH on X_ref; V7 NOT_ACTIVATED vs truth Unactivated agreement reported as a result, not used for labelling |
| C15 | Same items choose the annotation threshold and then test it | Split by project/program: DEV-N for threshold choice; sealed holdouts for test; one unseal |
| C16 | Duplicated or lineage-related pairs appear in DEV and holdout (the system "recognises" the construction pattern) | Near-duplicate (MinHash >= 0.8) and lineage independence check, zero cross-split groups (EP 3.4); author-template ids recorded so template leakage across splits is auditable |
| C17 | Labels revised after seeing results (re-adjudication to fit) | Freeze at sealing; POST_UNSEAL revisions in sensitivity only; ledger hash chain |

Residual (uncontrolled) risks: (i) RH and V7 both run on CPython, so substrate artifacts can be shared even with different mechanisms; (ii) the universal claim is domain-bounded (X_b); (iii) authors' priors about "what masked changes look like" are shared with V7's designers (same literature); (iv) Pi is a human choice of what internal state is semantically meaningful, so IO measures agreement with that choice. These bound what H8 can claim: "V7's annotation agrees with an independently declared notion of masked internal difference on constructed and adjudicated pairs".

## 6. Hypotheses restated for this class (what the power analysis tests)

- H8a (annotation): among IO truth pairs on which V7's state view fires, the share with an INTERNAL_ONLY annotation is >= 70%. EP states the threshold as a rate; this protocol adds the decision rule: the one-sided 95% lower cluster-adjusted confidence bound must be >= 0.70 (a stricter, not looser, reading). The power analysis also shows the point-estimate-only reading, which has no error control and is NOT recommended.
- H8b (false alarm): on IO truth pairs, V7 reports DIVERGENT-by-interface in <= 1%; demonstrated only if the one-sided 95% upper bound is <= 1%.
- H8c (PROPOSED addition, needs amendment): on RO truth pairs, INTERNAL_ONLY annotation rate <= a cap to be fixed by DEV-N pilot before sealing. No cap is proposed here (it would be an invented threshold); the item is registered so C12 has a measured control.
- H7 (EP): Delta Det on the hard stratum (Div truth, seed outputs equal), full V7 vs V7 without internal-state views, >= +3pp, paired, on H-R AND H-M. Note: IO pairs do not enter Det (Det is defined on Div truth); IO prevalence enters only H8 and, through adjudication error (IO mislabelled as Div), as noise.
- Reporting: IO is always reported as its own column; never added to Div or to Eq-B; a DIVERGENT-by-interface verdict on IO or RO is a false alarm; an INTERNAL_ONLY annotation on Div is reported separately (not an error).

Realistic rates for planning (V6 facts, DEV, SBG-trace-defined so NOT independent truth): 180/1332 changed pairs (13.5%) were "masked"; of changed pairs without an output difference (357), 50% masked, 17% not exercised, 32% candidate equivalent. Taking "masked" as an upper bound on IO among internally divergent pairs: 180/(975 + 180) = 15.6% (975 = changed pairs with an output difference). Real-regression prevalence is unknown and likely lower because repository fixes are selected for failing tests (output-visible) by construction in H-R. The power analysis therefore spans 5% to 30%.
