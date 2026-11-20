# SBG V6 — Mathematical Formulation

## Objects
* Version pair (P, P′); entry function f; input list X = (x₁…x_K) fixed by the protocol (same X for both versions; never read from labels).
* Execution τ(P,x) = (E, r, ε, κ) : event list E (call/line/return/exception with repr-capped locals), return value r, exception type ε∈𝔼∪{⊥}, completion κ∈{COMPLETE, EXC, TRUNC, TIMEOUT, FAIL}. `TRUNC` = event cap hit; `TIMEOUT` = per-trace budget; `FAIL` = harness/instrumentation error.
* Usable trace: κ ∈ {COMPLETE, EXC}. U(P) = {x : τ(P,x) usable}.

## Blocks (each returns d ∈ [0,1] or ⊥ = undefined)
**A — invariants.** Program point π=(g,k): g = function ordinal (first-call order over X), k ∈ {entry, exit, loop_j} (j = first-execution rank of loop headers). Slot s = variable rank by first appearance in g's frame snapshots. Observation set O(π,s) = abstract values a(v) over all usable traces.
Predicate library Θ: `type=T`, `nonnull`, `sign∈{neg,zero,pos}`, `const=c` (numeric, |c|≤10⁶), `len∈{0,1,2–3,4+}` (sized values). Pair predicates over numeric slots (s,t) at the same π: `s<t`, `s≤t`, `s=t`, `s≠t`; and `len(s)=t`. A predicate θ is **asserted** at (π,s) iff it holds on all |O| ≥ n_min=3 observations. Invariant set I(P) = {(π,s,θ)} with support n = |O|.
Weight w(n) = min(1, log₂(1+n)/log₂(1+K_w)), K_w=8.
d_A(P,P′) = 1 − Σ_{ι∈I∩I′} min(w,w′) / Σ_{ι∈I∪I′} max(w,w′). ⊥ if I∪I′ = ∅.

**B — transitions.** Statement kind κ(ℓ) from the AST (If, For, While, Return, Assign, AugAssign, Expr, Raise, Try, With, Other). For consecutive line events (ℓ,ℓ′) in the same frame: token t=(κ(ℓ),κ(ℓ′),back) with back=[ℓ′≤ℓ]; if ℓ is an If/While/For header, add taken=[ℓ < ℓ′ ≤ end(ℓ)]. Empirical token distribution p over all usable traces. d_B = JSD₂(p,p′) = ½KL(p‖m)+½KL(p′‖m), m=(p+p′)/2, base-2 so d_B∈[0,1]. ⊥ if either side has no tokens.

**C — dynamic CFG.** Directed graph G with node = statement kind, edge multiplicities from consecutive line events. WL-1 label of a node u = (κ(u), sorted multiset of (κ(v), ⌈log₂(1+count)⌉) over successors). q = visit-weighted distribution of WL-1 labels; d_C = JSD₂(q,q′). Also size features c = (log|N|, log|E|, E−N+2) compared as |Δ|/(1+|Δ|).

**R — return state (R2 regime only).** σ(x) = (ε, type(r), sign(r), lenbucket(r)). d_R = |{x∈U∩U′ : σ(x)≠σ′(x)}| / |U∩U′|. Differential-testing baseline δ_out = fraction of x with (ε, repr(r)) ≠ (ε′, repr(r′)).

**E — change activation.** Λ, Λ′ = changed lines of P, P′ from `difflib.SequenceMatcher` over comment/blank-stripped, whitespace-normalised source lines. act(P,x)=[coverage(τ(P,x)) ∩ Λ ≠ ∅]. α = ½(mean_x act(P,x) + mean_x act(P′,x)). First divergence: with token sequences T(x),T′(x), j*(x) = first index where they differ (∞ if none); gated divergence g = mean_x (1 − j*(x)/max(|T|,|T′|)) with g=0 when j*=∞.

## Evidence and status
Per side: usable fraction u=|U|/K, truncated fraction, exception fraction, nondeterminism flag ν (feature signature of run 0 ≠ run 1).
status(P,P′) = UNKNOWN if instrumentation FAIL ∨ u<u_min=0.5 ∨ u′<u_min ∨ ν;
NOT_ACTIVATED if usable ∧ α = 0 (change lines never executed on either side);
ACTIVATED otherwise.
Confidence c = u·u′·(0.5+0.5·min(1,α/α₀)), α₀=0.5.
**Rule:** a block distance computed under UNKNOWN is never reported as 0; the pair is marked abstained.

## Raw (unsupervised) V6 distance
d_V6 = mean of defined values among {d_A, d_B, d_C} (R1) and {d_A,d_B,d_C,d_R} (R2). Undefined for UNKNOWN. NOT_ACTIVATED pairs get d_V6 as computed (it is empirically ≈0 when nothing changed) and are flagged.

## Supervised fusion (separate from the representation)
z(P,P′) = [d_A,d_B,d_C,(d_R),g,α,c,status one-hots,missing indicators]. Fusion models f_θ: LR (L2, C∈{0.1,1,10}), HistGradientBoosting (depth ≤3, ≤100 iters), Reliability-aware LR (features d_·×c plus z). Hyperparameters chosen by inner grouped CV; Platt calibration fit on inner out-of-fold scores.

## Complexity
Tracing O(K·E_max) (E_max=5000). A: O(Σ|O|·s²) with s ≤ 6 numeric slots/point. B,C: O(E). Memory O(E) per trace.
