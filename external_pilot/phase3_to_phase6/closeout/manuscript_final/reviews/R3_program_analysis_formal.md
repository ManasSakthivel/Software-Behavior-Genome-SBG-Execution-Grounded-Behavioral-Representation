# Review R3: Program Analysis and Formal Methods

**Manuscript:** "How Far Can a No-Divergence Verdict Be Trusted? False-Assurance Risk, Evidence Response Signatures, and a Pilot Study in Differential Regression Testing" (IEEE Access, V8 final)

**Reviewer expertise:** program analysis, formal methods

**Scope of this review:** I read main.tex and every section and table in include order. I checked Propositions 1–4, Remarks 1–2, Definition 9 (ERS conformance) and Algorithms 1–5 against `sbgv8/{calibrate,ers,stats,evidence_schema,collect,profile,adapter,procsep}.py`, plus the modules they depend on (`policy.py`, `baselines.py`, `perturb.py`, `trust.py`, `sbgv7/isolation.py`, `sbgv7/sandbox_darwin.sb`, `sbgv7/verify.py`) and the stored corpus `datasets/v8/dev_records.jsonl`. I ran nothing except read-only inspection. One step was a short read-only Python count of record metadata fields.

---

## Summary

The paper treats a differential-testing "no divergence observed" (NDO) verdict as a selective prediction. It defines a false-assurance risk R = P(F=1 | NDO) relative to an observation boundary O, an adjudication budget B and a population. It states four propositions:
- Prop. 1: integrity must gate every verdict.
- Prop. 2: risk is monotone in (O, B).
- Prop. 3: random abstention preserves expected risk.
- Prop. 4: ERS conformance and accuracy are independent.

It implements an integrity-first decision procedure (SBG V8) and an Evidence Response Signature (ERS), which is a metamorphic-style conformance test of the risk estimator under ten evidence perturbations. The pilot covers 312 development pairs. Its empirical results are honestly reported as mostly negative or inconclusive.

From a formal-methods standpoint the framing is careful and much more candid than usual. However, the formal layer is weaker than the paper presents it:
- (a) Two of the four propositions are near-tautologies whose hypotheses carry the whole argument.
- (b) Prop. 4(ii) is false as stated for the estimator class the paper actually uses (g∘φ).
- (c) The adversary premise of Prop. 1 is not satisfied by the implementation. The validator accepts a "legacy" directory with all V8 artefacts stripped, and ι is stored as a writable record field.
- (d) Most ERS "passes" of the proposed procedure hold by construction. The paper does not identify these as tautological, which overstates RQ2.

None of these issues needs new experiments to state correctly. Concern 2 needs either a code fix plus a security re-run, or a narrower claim.

---

## Strengths

1. **Clean separation of the estimand from equivalence.** Remark 1 (problem.tex:83–85) and the explicit (O, B, 𝒞)-relativity of R (problem.tex:111) are correct and useful. The complete-case, worst-case and optimistic reporting for unresolved cases (problem.tex:113) is good practice.
2. **Correct matched-coverage methodology.** Prop. 3 is elementary but is the right reference point. B6 (`baselines.py:48–56`) implements exactly the fixed-k, uniform-without-replacement process the proposition assumes. Fractional tie handling in `stats.matched_risk` (stats.py:77–94) matches Algorithm 5 and the matched-risk definition, including "undefined if eligible share < c*".
3. **Trust-gate ordering matches the code.** Eq. (V) and Algorithm 4 match `calibrate.Model.decide` (calibrate.py:88–95) on the ordering ι → witness → eligibility/threshold. The rationale "a forged witness is also content" is sound.
4. **Faithful transcription of the ERS conformance definition.** Definition 9 (ers.tex:14–23) and Algorithm 6 match `ers._eval` (ers.py:41–50) exactly, including the tolerances ε=1e-6 and δ=0.02, the N/A rule for monotone trials when v₀=DIV, and the P6/P8 conditions. Remark 2 (vacuous V⊥ passes everything) is correct against this code.
5. **Unusually honest scoping.** The paper discloses construction labels, development exposure, the excluded template artefact, uncommitted-tree runs, the unmerged profile fix and the open sensing channel.
6. **Consistent ERS counts.** P2 failures 109/227 = 227−118 in tab_ers.tex:16. V7-B recomputed P8 failures 84 = 312−228.

---

## Major concerns

### M1. Prop. 4(ii) is false for the estimator class actually used; the independence claim is overstated.

**Evidence.**
- The estimator is R̂(E) = g(φ(E)) (problem.tex:138–142; calibrate.py:71–86, where `predict_risk` depends on the record only through `features(rec)` = φ, plus optional ERS extras).
- Prop. 4(ii) (problem.tex:162–164) constructs g′ that agrees with g on supp(𝒟) but differs at T_j(E), and assumes only T_j(E) ∉ supp(𝒟).
- If g′ must also factor through φ, it can differ at T_j(E) only if **φ(T_j(E)) ∉ φ(supp 𝒟)**.
- This fails in exactly the cases the paper reports:
  - P3: duplicates are dropped before φ is computed (profile.py:46), so φ(T₃(E)) = φ(E).
  - P2 after the profile fix: the paper itself reports "Δ exactly zero" (results.tex:41), so φ(T₂(E)) = φ(E).
  - In both cases **no** g′ can fail the invariance, contrary to "for every estimator g there is g′ that … fails property j".
- The proposition also ignores the positive controls:
  - P6 cannot be failed by changing g at all. Appending a CONFIRMED_DIFF input makes `has_witness` true (calibrate.py:35–40), so V returns DIV whenever ι=1.
  - P8 is decided by the trust gate, not by g.
  - The statement quantifies over "property j" without restricting j to the invariance and monotone classes.
- Part (i) is about coverage, not accuracy. V⊥ has coverage 0, so its selective risk R is undefined (0/0), not "bad". (i) therefore shows "conformance does not imply usefulness", not "conformance does not imply accuracy".

**Fix.**
- Restate (ii) for j ∈ invariance ∪ monotone, with the hypothesis φ(T_j(E)) ∉ φ(supp 𝒟), and state it for estimators of the form g∘φ.
- Add the complementary (and more informative) lemma: *if φ(T_j(E)) = φ(E), every φ-based estimator passes invariance j; if T_j moves every signed feature in its risk-increasing direction and g is sign-monotone, every such g passes monotone j.* This shows which ERS properties test φ, which test g and which test V (see M3).
- Rename "logically independent" to "neither implies the other". The current statement is a standard off-support non-identifiability fact and should be presented as such, not as a headline formal result (abstract; introduction.tex:32).

**New experiments:** none.

### M2. The adversary premise of Prop. 1 does not hold in the implementation (downgrade to "legacy", and ι as a stored field). The RQ1 claim "fail-safe for keyless writers" is not supported as stated.

**Evidence.**
- Prop. 1 assumes the evidence adversary "cannot produce [a record] that passes validation (ι=1) without the key K" (problem.tex:87).
- **Downgrade path:**
  - `validate_dir` calls `check_anchor` only if a capture record exists, an anchor file exists, or `require_anchor` is set (evidence_schema.py:204). A configured key is **not** part of that condition.
  - If a keyless writer (A2) deletes `v8_parts.json`, `v8_capture.json` and `v8_anchor.json`, then `check_capture` returns `not_collected` (evidence_schema.py:146–149), `trusted` becomes `None` (line 207), and `adapter.load_record` sets `integrity_ok = True` (adapter.py:97). The V7-B chain check (`sbgv7/verify.py`) is keyless, and the paper grants that A2 can recompute it (trust.tex:9).
  - `require_anchor=True` is never passed on any production path (collect.py:42, adapter.py:60; the only use is a test, tests/v8/test_security_schema.py:171).
  - Algorithm 2 (approach.tex:94) says a missing anchor "adds a reason" whenever K is given. That does not match the code. Tab. threats (trust.tex:57) lists "strip or alter the anchor: Blocked" with the legacy exemption only as residual risk. It is not recognised as a full bypass of Prop. 1's premise.
  - Effect on verdicts: a forged witness in a re-chained, downgraded log then yields DIV. The DIV branch of Prop. 1 is realised by a keyless writer. A forged NDO yields NDO under B1/V7-B effective verdicts (`procsep.decide`, procsep.py:146–149). For CEC, the missing sidecar empties the hits, which probably but not provably drives the risk above τ.
- **ι is content:**
  - Definition 2 puts ι(E) inside the record's metadata (problem.tex:50). The pipeline for RQ2–RQ4 reads `integrity_ok` as a stored boolean from `dev_records.jsonl`; `Model.decide` reads `rec.integrity_ok` (calibrate.py:93) and never re-validates.
  - P8 is implemented as "set the flag" (ers.tex Tab. perturbations, P8). In the model of Prop. 1, an adversary who writes "a record with any content" can therefore write ι=1, and the proof's step "the record fails validation, as E* does" is not well-defined.
  - ι must be a function of the sealed directory evaluated by the trusted decision-maker, not a field of E.
- **Corpus integrity was not the integrity defined in the paper:**
  - All 312 development records have `meta.capture` and `meta.anchor` absent and `sidecar='ok'`. I counted this read-only: `Counter({(None, None, 'ok', True): 312})`.
  - So ι on the corpus used for RQ2–RQ4 means hash chain plus sidecar binding only. No capture record and no anchor were applied, contrary to the Definition of Integrity (problem.tex:54).
- **A3 is not covered either:**
  - Validation does not bind the record to the change c. The anchor covers file digests and the session (evidence_schema.py:104–109), not program identity.
  - A3 can therefore present a genuine ι=1 record for another change, and Prop. 1's adversary model ("a record for c") is not well-defined. The paper concedes A3 is "detection only" (trust.tex:58), but Prop. 1 is stated without this exception.
- **Possible A1 → key-holder escalation (unverified, should be argued):**
  - A1 runs "with the analysis's user identity" (trust.tex:8). The key may come from the controller's environment `SBGV8_ANCHOR_KEY` (evidence_schema.py:88).
  - On Linux, `bwrap` is invoked with `--proc /proc` but without `--unshare-pid` (sbgv7/isolation.py:75), so a same-uid child can plausibly read `/proc/<controller>/environ`.
  - On macOS the profile is `(allow default)` with only network and write denials (sandbox_darwin.sb:2–8).
  - The exclusion "any process running as the controller user that can read [K]" (trust.tex:12) may therefore include A1 itself. If so, the A1/A2 separation collapses.

**Fix.**
1. Make ι a function V can only obtain from the validator, e.g. ι = Validate(d, K) evaluated inside `decide`. Remove it from the record content in Definition 2.
2. Treat "no capture record" as untrusted whenever a key is configured (or always for V8-collected pairs). Make `require_anchor` the default and fix Algorithm 2 to match.
3. Restate Prop. 1's hypothesis as an explicit property of the validator ("no keyless party can produce a directory d with Validate(d,K)=true that was not sealed by the controller for change c"), and bind the anchor to program digests so that A3 is covered.
4. State that RQ2–RQ4 records were validated without capture or anchor.
5. Either remove the key from the controller environment and add `--unshare-pid` with a private /proc, or move this to the residual-risk table.

**New experiments:** a targeted downgrade attack and a /proc-environ probe in the security suite are cheap and should be added. They are not needed for the formal correction itself.

### M3. Most ERS conformance results for the proposed procedure hold by construction, so RQ2 is overstated for SBG V8.

**Evidence.** Row by row for the fitted model (tab_ers.tex:14–23):

| Row | Why it passes by construction |
|---|---|
| P3 | Flagged copies are removed before φ (profile.py:46) and before the V7-B replica (profile.py:85). Every φ-based predictor passes, so "all predictors 262/262" carries no information. |
| P2 (post-fix) | φ is unchanged ("Δ exactly zero", results.tex:41). |
| P6 | An appended CONFIRMED_DIFF input forces DIV through `is_div` whenever ι=1 (calibrate.py:39–40, 94). The paper notes "by construction" for P8 (ers.tex:51; results.tex:45) but not for P6. |
| P8 | The trust gate (acknowledged in the paper). |
| P4, P7, P9 | Resp. 0, acknowledged as vacuous. |
| P5, P1, P1b | The model is sign-constrained (calibrate.py:14–16, 157–159), and Platt recalibration keeps the slope ≥ 1e-3 (calibrate.py:111). P5 reduces the clean set without touching the share denominators, so every signed feature moves in the risk-increasing direction and Δ ≥ 0 is guaranteed up to optimiser tolerance. For P1/P1b the only feature that can move the wrong way is `chan_complete` (a mean over U, profile.py:56,69), which carries no weight (P4 Resp. 0). |

The only non-tautological findings are therefore the unfitted probe's P2 failure, which is a defect of φ rather than of an estimator, and the V7-B "recorded" failures, which hold by construction because a stored verdict cannot react. The claim "the matrix detected a profile defect" stands. "Does the SBG procedure satisfy the properties" (RQ2) is largely answered by design, not by experiment.

**Fix.** Add a column to Tab. ers or Tab. ersprops classifying each pass as *entailed by φ*, *entailed by sign constraints*, *entailed by V's case order*, or *empirical*. Fold this into the lemma proposed in M1. Reword RQ2's answer and the "most transferable result" paragraph (discussion.tex:8) accordingly.

**New experiments:** none.

### M4. Prop. 2 is close to circular, is stated for a different risk estimator than the one reported, and is never instantiated.

**Evidence.**
- The "monotone adjudication" assumption (problem.tex:115) already says, per input, that what is found under (O,B) and separates under O′ is found under (O′,B′). Given that, the proof is one line. The soundness assumption is never used in the proof.
- Adjudication is modelled as a deterministic function A(c;O,B), but the planned adjudicators are humans. The statement needs either an a.s. coupling or a statement in expectation.
- The proposition is about the **optimistic** estimator |{div}|/|S| (denominator |S|, problem.tex:118). The paper's headline estimator is the **complete-case** n_d/(n_d+n_n) (problem.tex:113), and that estimator is **not** monotone. Counterexample: under (O,B), 1 div, 0 nodiv and 9 unresolved gives 1.0. Under (O′,B′), the 9 resolve to nodiv, giving 0.1.
- R is defined as a population probability (eq. R), while Prop. 2 is about a finite share over a fixed S. The notation R_{O,B}(S) is introduced only inside the statement.
- The abstract and introduction phrase the result as "a risk measured under one boundary is a lower bound for any wider one". That is true only for the share of S, under the circular assumption, and only for the adjudication boundary (S fixed), not the verdict boundary.
- The empirical study never varies O or B and uses construction labels Y instead of A (problem.tex:169; design.tex:138–139). The proposition therefore supports no reported number.

**Fix.**
- State the result for the optimistic estimator and add a remark that complete-case risk is not monotone.
- Remove the unused soundness assumption, or show where it is needed (e.g. to exclude spurious div under O′).
- Phrase it as a definitional consequence rather than a theorem, and fix the abstract wording.

**New experiments:** none.

### M5. The proof of Prop. 1 needs unstated assumptions, and the conclusion is stronger than the proof supports.

**Evidence.** The proof (problem.tex:92) relies on several implicit assumptions:
- (i) V is a deterministic function of record content alone, with no side input such as the change c, the source digests or a pinned head. Under (i), "indistinguishable" is just functional determinism.
- (ii) Records are transferable across changes. This contradicts the claim that evidence is "change-conditioned", since U_c is inside E (problem.tex:50).
- (iii) The adversary chooses the population ("risk … on changes chosen by the adversary is 1"), whereas R is defined over a fixed 𝒞 (problem.tex:107–108).
- (iv) Changes that diverge within O exist and are available to the adversary.

In addition, "bounded risk therefore *requires* V=INS whenever ι=0" (problem.tex:94) is a necessity claim. The proposition only shows that any untrusted record mapped to a non-INS verdict yields an attack. The DIV case is not about false-assurance risk at all; it bounds spurious DIV, a different metric that is never defined.

**Fix.** State (i)–(iv) explicitly, define the metric for spurious DIV, and restrict the "requires" claim to deterministic, content-only V. Note that the proposition is a one-step consequence of determinism. Its value is in motivating the case order, which is fine, but it should not be counted as one of "three formal results" of comparable weight.

**New experiments:** none.

### M6. Algorithm/code mismatches in the decision procedure and eligibility.

**Evidence.**
1. **DIV condition.** Eq. (V) case 2 and Def. 4 say DIV iff "a witness exists". Algorithm 4 line 3 says "a confirmed, reproducible witness". The code uses `is_div = has_witness(rec) or v7b_verdict(rec) == DIV` (calibrate.py:39–40). `has_witness` checks only the outcome label `CONFIRMED_DIFF` (line 36) and performs no reproducibility check. The V7-B disjunct is not mentioned in the paper.
2. **Eligibility.** Definition 3 (problem.tex:58) says "no witness and β ⊆ Θ". The code additionally excludes records whose re-derived V7-B verdict is DIV (calibrate.py:52–54). Policy v8.1 (policy.py:25–28) requires an empty blocker list **and** a V7-B NDO, i.e. it is stricter than "additionally requires that the fixed gate would issue NDO" on top of v8.0.
3. **Algorithm 4 line 1** computes r before the trust gate, then returns the sentinel risk 1.0 on ι=0 (calibrate.py:90–93). ERS uses `predict_risk`, not the returned risk (ers.py:56), so for P8 the response Δ reflects g and not the gate. This is harmless but undocumented. Δ₈ in B8's feature vector is therefore not "the response of the procedure".
4. **Profile definition.** `branch_cov_min` is documented in the code as an approximation that counts every recorded branch key, capped at 2×static, "instead of only the static ones" (profile.py:30–31). Tab. profile (approach.tex:135) presents the exact definition.
5. **Empty changed-unit set.** When U_c = ∅, Eq. (act) is 0/0. The code sets act_frac = 1 and obs_react = 1 but mu_min = mu_mean = 0 (profile.py:58–64). These conventions are inconsistent with each other and undocumented.
6. **Code tree is pre-fix.** profile.py:62–66 still counts all clean inputs (n_same, n_rep, n_eff). The fixed profile described in approach.tex:154 is not in the reviewed code; it lives on another branch (reproducibility.tex table, "Fix not merged").

**Fix.** Align Eq. (V), Definition 3 and Algorithm 4 with the code, or the code with them. Document the approximation and the empty-U_c conventions. Merge the profile fix or state clearly which φ each result uses.

**New experiments:** none, unless the code is changed. If `is_div` changes, re-run the analysis (minutes, per reproducibility.tex).

### M7. The threshold rule's "upper bound" is anti-conservative as implemented, and the complexity/cost table has gaps.

**Evidence.**
- `select_threshold` imputes risk **0** for bootstrap replicates in which a prefix is empty: `np.where(cn > 0, cf/cn, 0.0)` (stats.py:121). For short prefixes drawn from a few projects, this biases the 95th percentile downward.
- The bound is pointwise per prefix, but the selection takes the largest prefix whose bound is ≤ α, with no simultaneity correction across prefixes.
- τ is selected on inner-OOF scores from models fitted on about two thirds of the training data, then applied to the refit model's scores (calibrate.py:226–230). The score scales need not agree.
- The paper says only "no finite-sample guarantee" (approach.tex:159). All three issues should be stated. They have no effect on the reported numbers only because no model issued any NDO.
- **Cost table** (approach.tex:213–234):
  - The 21 MB figure for B×N weights corresponds to N = 258 (10,000×258×8 B ≈ 20.6 MB), not to the N = 312 defined in the same paragraph (≈ 25 MB).
  - Algorithm 3 uses B = 1,000 (calibrate.py:175, 216) while the text discusses 10,000. Both values should be stated per stage.
  - B8's features are ERS responses of a base model. If they are computed through `ers_vector` (ers.py:67–69), one B8 risk evaluation costs O(J(unh+d)). Fitting B8 then costs O(N·J·(unh+d)) per fold beyond what the table lists, and an ERS matrix *of* B8 would be O(N·J²·(unh+d)).
  - Profile cost O(unh) is correct up to set construction (profile.py:49).

**Fix.** Use NaN-dropping (as `matched_risk` already does) or a conservative imputation of 1. Mention the selection effect and the refit-scale mismatch. Correct the memory figure and add the B8 cost row.

**New experiments:** none required.

---

## Minor concerns

**Notation**
1. Properties and perturbations share overlapping numerals with different meanings: "Property 7" is tested by P8 and "Property 8" by P5 (ers.tex:45–53). The text then says "property P8" (problem.tex:94) and "P6 accept INS" (problem.tex:156) as if P-ids were property ids. Use distinct labels (e.g. π₁…π₈ for properties).
2. "Eight properties" plus an extra "E" row gives nine rows and ten perturbations. Say "eight properties and one environment check" consistently (abstract, ers.tex:6, Fig. ersframework).
3. Symbol overloading:
   - c is a change, c* a coverage level, and 𝒞 the population, while C is the clean set (approach.tex:108).
   - 𝓑 is the budget and B the bootstrap resample count.
   - k is the kept-subset size (Prop. 3), the number of inner folds, and both the index and the target inside one line of Algorithm 5 (design.tex:184: "k ← c*·Σ_k w_k").
   - h means executed lines h_s(i), changed units executed h(i), and lines hit per input in the cost table.
4. U_c is described as "changed lines on either side" (Tab. notation), but the implementation uses (side, line) pairs (profile.py:5,13–14), so a line changed on both sides counts twice. State this.
5. o_O(P,x;e) is used without defining the canonicalisation, and Def. 1 requires the inequality to be "reproduced on re-execution", which has no counterpart in `has_witness`.
6. F is defined only for issued NDO, but R is written with the same symbol for the population probability (eq. R) and for the finite share in Prop. 2.
7. The integrity definition (problem.tex:54) omits the V7-B hash-chain verification and the legacy `trusted=None` exemption, both of which appear in Algorithm 2 (approach.tex:98,102).

**Statements and proofs**
8. Prop. 3 is correct but elementary (linearity of expectation with a fixed denominator). Label it a lemma. Note that it does not license "almost all of that reduction is explained by issuing fewer verdicts" for the deterministic B3 (discussion.tex:6) without a B3-vs-B6 interval at B3's own coverage.
9. In ERS Definition 9, the P8 condition "ι(T₈(E))=0" is always true by construction of T₈, so the property reduces to v₁ = INS. Say so.
10. Monotone trials on records with v₀ = INS pass whenever v₁ = INS (ers.py:44), including when risk falls. The "abstention credit" definition (ers.tex:22) handles this, but the count of applicable trials with v₀ = INS should be reported per row.
11. Remark 2 states the vacuity result "as implemented". Note that V⊥ has undefined selective risk, so it is not "inaccurate" (cf. M1).
12. The 0.02 invariance tolerance and the 1e-6 monotone tolerance are unmotivated. The invariance tolerance is on a probability scale, so it is very lenient at low risks and strict near 0.5. Consider a logit-scale tolerance.
13. Calling ERS "metamorphic testing of the estimator" is apt. However, the relations as stated are mostly invariance/monotonicity relations of φ (M3), which are closer to feature-map specifications than to metamorphic relations of g.

**Implementation and presentation**
14. `ers.ers_vector` sets Δ = 0 for non-applicable perturbations (ers.py:67–69). This conflates "no response" with "not applicable" in B8's features. Add an applicability indicator.
15. Algorithm 1 returns INS when `val.trusted = false`, but `trusted = none` (legacy) returns the engine verdict (collect.py:42–43; procsep.py:148). Make this explicit in the algorithm.
16. "Independent capture" is not independent of the evaluated address space (trust.tex:26), which the paper admits. Rename it (e.g. "parent-side tee").
17. Tab. ersprops row 5 and Tab. ers report the "recomputed V7-B" and SBG P6 results together without flagging the SBG result as entailed (M3).

---

## Scores (1–10)

| Criterion | Score | Justification |
|---|---|---|
| Novelty | 5 | Applying the selective-risk framing and metamorphic-style estimator checks to NDO verdicts is a fresh combination, but each ingredient is standard. |
| Technical contribution | 4 | The propositions are near-tautological (P1, P2, P3), one is incorrect for the estimator used (P4(ii)), and the integrity premise is not met by the code. |
| Literature coverage | 7 | Broad and well organised. Regression verification, checked coverage and selective prediction are cited appropriately. |
| Experimental design | 5 | Matched coverage and a random-abstention reference are well chosen. The corpus is development-exposed, and RQ2 passes are largely by construction. |
| Statistical validity | 6 | Cluster bootstrap, Holm and MDE are done carefully and negatives are reported honestly. The threshold bound is anti-conservative as implemented. |
| Benchmark breadth | 3 | Python only, small synthetic programs plus QuixBugs, unlabelled BugsInPy, and no held-out data. |
| Reproducibility | 6 | Analysis is reproducible from records. Collection logs are missing, the profile fix is unmerged, and the corpus lacks the capture/anchor integrity. |
| Writing | 7 | Clear, candid and well structured. Property/perturbation numbering and symbol overloading hurt the formal sections. |
| Figures and tables | 6 | Informative traceability and threat tables. The ERS tables should mark entailed passes, and the cost table has small errors. |
| Overall readiness | 4 | The formal claims need restatement and the integrity premise needs a code fix or a narrowed claim before acceptance. |

## Recommendation

**Major revision.** The empirical honesty is commendable and the negative result is worth publishing. The formal layer must be corrected before the "three formal results" can be claimed:
- restate Prop. 4(ii) for g∘φ;
- recast Prop. 2 for the estimator it actually covers;
- make Prop. 1's premise true in code (no legacy downgrade, ι not a record field, change-bound anchor) or narrow the claim;
- separate ERS passes entailed by construction from empirical ones;
- align Eq. (V), Definition 3 and Algorithms 2–4 with the implementation.

Apart from cheap targeted security probes for M2, no new experiments are required.
