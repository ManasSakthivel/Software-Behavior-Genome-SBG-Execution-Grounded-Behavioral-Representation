# 04 Formal problem definition

## 1. Program pair and declared scope
A pair is pi = (P0, P1, e, D, O, Env): base program P0, variant P1, declared entry point e (top-level function), input domain D (a set, or a distribution on it), observation boundary O (the channels that count: return value, exception, selected side effects, declared API calls), execution environment Env (interpreter, platform, resource limits, determinism controls). The declared comparison scope is S = (e, D, O, Env). Observation equality ~_O is defined on recorded observations (after canonicalisation, nondeterminism-aware).
Divergence within scope: Div(pi) holds iff there exists x in D such that O(P0,x,Env) is not ~_O-equal to O(P1,x,Env) under the pre-declared replication controls.
**Absence of an observed difference is not equivalence.** No result of this programme is a statement about equivalence over D, over time, over platforms, or over hash orders.

## 2. Independent outcome
Y(pi) in {1, 0, bottom}, produced by an adjudication protocol A with budget b that is independent of the system under evaluation (07):
- Y=1: A exhibits x in D and a confirmed (repeated, determinism-controlled) observable difference.
- Y=0: A exhausts budget b without finding such an x AND two reviewers judge that the change is not behaviour-altering within S (e.g. refactoring, dead-path fix).
- Y=bottom: unresolved or unlabelled; excluded from risk estimation and counted and reported.
Consequence stated up front: Y=0 is "no divergence found by A within budget b", so the estimated risk R_adj is a LOWER bound on the true risk R_true whenever A has less than full detection power. This is reported, not hidden.

## 3. Verdict policy and false assurance
A policy delta maps an evidence package E to {DIVERGENT_OBSERVABLE, INSUFFICIENT, NO_DIVERGENCE_OBSERVED}. Let A_i = 1 when delta(E_i) = NDO. A false assurance is F_i = 1 when A_i = 1 and Y_i = 1.
- Coverage: c(delta) = P(A=1).
- Joint risk: J(delta) = P(A=1, Y=1).
- **Conditional false-assurance risk: R(delta; Pi) = P(Y=1 | A=1) = J/c**, defined for a policy and a population Pi of version pairs drawn project by project. R is not the probability of equivalence, not a determinism probability, not general test-suite adequacy, not a statement about the unrestricted input space.
Pair-weighted R is primary; project-macro R is a pre-declared sensitivity.

## 4. Evidence representation
E = {(x_i, prov_i, obs_i^0, obs_i^1, runs_i, env_i)}_{i=1..n} plus the change description U (changed units from the AST diff). Feature vector phi(E) in R^k with k <= 8 (see 05). The risk model is s_theta(phi(E)) = estimated P(Y=1 | phi(E), eligible), where eligible = no witness and no hard blocker. Policy: issue NDO iff eligible and s_theta <= tau.
No single opaque confidence score and no ad hoc weights: s_theta is a transparent, monotone, penalised model whose coefficients and monotone directions are pre-declared.

## 5. Interventions on evidence
An intervention T is a map E -> E'. Operators are defined in 05; for each, whether execution is repeated is stated. The recomputed quantity is the decision procedure's output, delta(E') and s_theta(phi(E')). **This is "counterfactual" only with respect to the evidence package (what the procedure would have output given E'). It is not a counterfactual about the programs and supports no causal claim about program behaviour.** In formal text the operation is called evidence perturbation; CEC is retained as the working name.

## 6. Assumptions needed for each claim
| Claim | Assumptions |
|---|---|
| Calibration on held-out projects | held-out projects not used in fitting, threshold choice or feature design; labels independent of system |
| Population statement about R | projects are a (random) sample of a stated population; otherwise statements are about the benchmark only |
| Finite-sample guarantee on J via conformal risk control | projects exchangeable; loss monotone non-increasing in the threshold and bounded; score model fit on data disjoint from calibration; guarantee is in expectation over the calibration draw (Angelopoulos et al. 2024, Sec. 1.1, 2.4) |
| Guarantee on the ratio R=J/c | not given by CRC; needs a selective-risk method or a bound on c; not claimed |
| Intervention properties P1-P7 | stated per property in 05 |

## 7. Internal-consistency checks performed
J = c * R holds by definition; the policy is monotone in tau (smaller tau -> fewer NDO, so J non-increasing), which is the condition CRC needs; R is undefined when c=0 (reported as not estimable); exclusion of Y=bottom pairs changes both numerator and denominator and is reported with a worst-case (all unresolved = false assurance) sensitivity.
