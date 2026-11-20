"""Prospective power simulation for SBG V7 P0 (paired, clustered).

Run:  .venv/bin/python reports/v7_design/p0_reconciliation/power/power_sim.py
Outputs: power/out/*.csv and power/out/RESULTS.txt.  Master seed fixed (MASTER).

Model (headline, H2/H4): per divergent pair the two arms (A = same-budget differential
testing, B = V7) give a binary success (detect / not falsely assured).  Cell probabilities
q11,q10,q01,q00 are set from base rate p0, discordant rate pi, effect delta:
    q10=(pi-delta)/2, q01=(pi+delta)/2, q11=p0-q10, q00=rest.
Cluster (project) effect: each cluster draws its own cell probabilities from
Dirichlet(alpha*q), alpha=1/rho-1, so ICC of the paired difference d=b-a equals rho exactly.
Cluster size = min(8, 1+Poisson(m-1)) (protocol cap of 8 pairs/project).
Test: cluster-robust ratio estimator, t_{K-1}, two-sided; success = p<alpha and est>0.
Type-I check and a sign-flip permutation cross-check are in selfcheck().
"""
import os, itertools
import numpy as np
from scipy import stats

MASTER = 20261117
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
_ctr = [0]


def rng_next():
    _ctr[0] += 1
    return np.random.default_rng([MASTER, _ctr[0]])


def cells(p0, pi, delta):
    q10 = (pi - delta) / 2
    q01 = (pi + delta) / 2
    q11 = p0 - q10
    q00 = 1 - q11 - q10 - q01
    q = np.array([q11, q10, q01, q00])
    return q if (q >= -1e-12).all() else None


def sim_paired(K, m, rho, p0, pi, delta, nsims, rng, alphas=(0.05,), noise=0.0,
               contam_rate=0.03, g=1, zero_ok=False, ni_margin=None, min_est=None):
    """Power per alpha. g = pairs per lineage (n counts lineages, each gives g identical pairs)."""
    q = cells(p0, pi, delta)
    if q is None:
        return None
    q = np.clip(q, 1e-9, None)
    q /= q.sum()
    conc = 1.0 / rho - 1.0
    if zero_ok:
        n = np.minimum(8, rng.poisson(m, size=(nsims, K)))
    else:
        n = np.minimum(8, 1 + rng.poisson(max(m - 1, 0), size=(nsims, K)))
    cont = rng.binomial(n, noise) if noise > 0 else np.zeros_like(n)
    ntrue = n - cont
    gam = rng.gamma(conc * q, size=(nsims, K, 4))
    pk = gam / gam.sum(-1, keepdims=True)
    cnt = rng.multinomial(ntrue, pk)
    D = (cnt[..., 2] - cnt[..., 1]).astype(float)
    if noise > 0:  # contaminated (truly non-divergent) pairs: both arms ~ Bern(contam_rate)
        D += rng.binomial(cont, contam_rate) - rng.binomial(cont, contam_rate)
    D *= g
    N = (n * g).astype(float)
    Kn = (N > 0).sum(1)
    sN = np.maximum(N.sum(1), 1)
    est = D.sum(1) / sN
    res = D - est[:, None] * N
    var = (Kn / np.maximum(Kn - 1, 1)) * (res ** 2).sum(1) / sN ** 2
    se = np.sqrt(np.maximum(var, 1e-18))
    df = np.maximum(Kn - 1, 1)
    out = {"est": est.mean(), "se": se.mean(), "n_pairs": N.sum(1).mean()}
    pval = 2 * stats.t.sf(np.abs(est / se), df)
    for a in alphas:
        ok = (pval < a) & (est > 0)
        if min_est is not None:
            ok &= est >= min_est
        out[f"pow_{a:g}"] = ok.mean()
    if ni_margin is not None:
        lb = est - stats.t.ppf(0.975, df) * se
        out["pow_ni"] = (lb > -ni_margin).mean()
    return out


def selfcheck(log):
    r = sim_paired(40, 3.75, 0.15, 0.6, 0.2, 0.0, 20000, rng_next())
    log(f"selfcheck type-I (K=40,m=3.75,rho=.15,delta=0; upper tail of two-sided .05 test, expect ~0.025): {r['pow_0.05']:.4f}")
    r = sim_paired(20, 2, 0.30, 0.6, 0.3, 0.0, 20000, rng_next())
    log(f"selfcheck type-I (K=20,m=2,rho=.30,delta=0; expect ~0.025): {r['pow_0.05']:.4f}")
    rng = rng_next()
    K, m, rho, p0, pi, delta, ns = 40, 3.75, 0.15, 0.6, 0.2, 0.05, 400
    q = cells(p0, pi, delta); conc = 1 / rho - 1
    rej_t = rej_p = 0
    for _ in range(ns):
        n = np.minimum(8, 1 + rng.poisson(m - 1, size=K))
        pk = rng.dirichlet(conc * q, size=K)
        cnt = np.array([rng.multinomial(n[j], pk[j]) for j in range(K)])
        D = (cnt[:, 2] - cnt[:, 1]).astype(float)
        est = D.sum() / n.sum()
        res = D - est * n
        se = np.sqrt(K / (K - 1) * (res ** 2).sum()) / n.sum()
        rej_t += (2 * stats.t.sf(abs(est / se), K - 1) < 0.05) and est > 0
        s = rng.choice([-1, 1], size=(2000, K))
        null = (s * D).sum(1) / n.sum()
        rej_p += (np.mean(np.abs(null) >= abs(est)) < 0.05) and est > 0
    log(f"selfcheck t-test vs sign-flip permutation power (K=40,m=3.75,rho=.15,p0=.6,pi=.2,delta=.05, {ns} sims): t={rej_t/ns:.3f} perm={rej_p/ns:.3f}")
    # empirical ICC of d (one-way ANOVA estimator) with equal cluster size
    rng = rng_next(); K, m = 4000, 4
    q = cells(0.6, 0.2, 0.05); conc = 1 / 0.15 - 1
    pk = rng.dirichlet(conc * q, size=K)
    cnt = np.array([rng.multinomial(m, p) for p in pk])
    vals = np.concatenate([np.repeat([0, -1, 1, 0], c) for c in [None]]) if False else None
    # build d per pair: cells order 11,10,01,00 -> d = 0,-1,+1,0
    d = np.zeros((K, m))
    for j in range(K):
        d[j] = rng.permutation(np.repeat([0, -1, 1, 0], cnt[j]))
    msb = m * d.mean(1).var(ddof=1); msw = d.var(1, ddof=1).mean()
    log(f"selfcheck empirical ICC of d (nominal 0.15): {(msb-msw)/(msb+(m-1)*msw):.3f}")


def sim_h8a(K, nio, rho, a_true, phi, nsims, rng):
    """Single-arm test. Returns (power point>=.7, power one-sided 95% CP lcb>=.7 (deff-scaled), mean n_fire)."""
    n = rng.poisson(max(nio / K, 1e-9), size=(nsims, K))
    fire = rng.binomial(n, phi)
    conc = 1 / rho - 1
    pj = rng.beta(a_true * conc, (1 - a_true) * conc, size=(nsims, K))
    x = rng.binomial(fire, pj)
    nf = fire.sum(1); xs = x.sum(1)
    mbar = nf / np.maximum((fire > 0).sum(1), 1)
    deff = 1 + (mbar - 1) * rho
    ne = nf / deff; xe = xs / deff
    pt = (nf > 0) & (xs / np.maximum(nf, 1) >= 0.70)
    lcb = np.where((ne > 0) & (xe > 0), stats.beta.ppf(0.05, np.maximum(xe, 1e-9), np.maximum(ne - xe, 0) + 1), 0.0)
    return pt.mean(), (lcb >= 0.70).mean(), nf.mean()


def sim_h8b(nio, f, c, rho, K, nsims, rng, det_contam=0.5):
    """False-alarm <=1% on IO-labelled pairs (one-sided 95% CP UCB, deff-scaled).
    c = share of IO-labelled pairs that are truly Div (adjudication error); V7 flags those DIVERGENT w.p. det_contam."""
    n = rng.poisson(nio / K, size=(nsims, K))
    conc = 1 / rho - 1
    cont = rng.binomial(n, c)
    clean = n - cont
    pj = rng.beta(f * conc, (1 - f) * conc, size=(nsims, K)) if f > 0 else np.zeros((nsims, K))
    x = rng.binomial(clean, pj) + rng.binomial(cont, det_contam)
    N = n.sum(1); X = x.sum(1)
    mbar = N / np.maximum((n > 0).sum(1), 1)
    deff = 1 + (mbar - 1) * rho
    ne = N / deff; xe = X / deff
    ucb = np.where(ne > 0, stats.beta.ppf(0.95, xe + 1, np.maximum(ne - xe, 1e-9)), 1.0)
    return (ucb <= 0.01).mean()


def save(name, header, rows):
    p = os.path.join(OUT, name)
    with open(p, "w") as fh:
        fh.write(header + "\n")
        for r in rows:
            fh.write(",".join("" if v is None else (f"{v:.4f}" if isinstance(v, (float, np.floating)) else str(v)) for v in r) + "\n")
    print("wrote", p, len(rows), "rows")


def main():
    lines = []
    def log(s):
        print(s); lines.append(s)
    log(f"master seed {MASTER}; numpy {np.__version__}")
    selfcheck(log)
    NS = 1500
    A05, AH = 0.05, 0.05 / 3    # unadjusted; alpha/3 (three budgets) as Holm-conservative proxy
    kA, kH = f"pow_{A05:g}", f"pow_{AH:g}"

    rows = []
    for K, m, rho, p0, pi, d in itertools.product([20, 30, 40, 50, 60, 80], [2, 4, 8], [0.05, 0.15, 0.30],
                                                  [0.4, 0.6, 0.8], [0.10, 0.20, 0.30], [0.03, 0.05, 0.10]):
        r = sim_paired(K, m, rho, p0, pi, d, NS, rng_next(), alphas=(A05, AH))
        if r is None:
            continue
        rows.append((K, m, rho, p0, pi, d, round(r["n_pairs"]), r[kA], r[kH], r["se"]))
    save("headline_power_grid.csv", "K,m,rho,p0,pi,delta,mean_pairs,power_a05,power_a0167,mean_se", rows)

    bigK = [20, 30, 40, 50, 60, 80, 100, 150, 200, 300, 450, 700, 1000, 1500, 2500]
    req = []
    for m, rho, pi, d in itertools.product([4, 8], [0.05, 0.15, 0.30], [0.10, 0.20, 0.30], [0.03, 0.05, 0.10]):
        if cells(0.6, pi, d) is None:
            continue
        need = {}
        for a in (A05, AH):
            need[a] = None
            for K in bigK:
                r = sim_paired(K, m, rho, 0.6, pi, d, 800, rng_next(), alphas=(a,))
                if r[f"pow_{a:g}"] >= 0.8:
                    need[a] = K; break
        req.append((m, rho, pi, d, 0.6, need[A05], need[A05] and need[A05] * m, need[AH], need[AH] and need[AH] * m))
    save("headline_required_projects.csv", "m,rho,pi,delta,p0,K_a05,pairs_a05,K_a0167,pairs_a0167", req)

    mde = []
    dgrid = np.round(np.arange(0.01, 0.2501, 0.005), 3)
    for K, m, rho, pi in itertools.product([20, 30, 40, 60, 80, 120], [2, 4, 8], [0.05, 0.15, 0.30], [0.10, 0.20, 0.30]):
        res = {}
        for a in (A05, AH):
            res[a] = None
            for d in dgrid:
                if d > pi:
                    break
                r = sim_paired(K, m, rho, 0.6, pi, d, 500, rng_next(), alphas=(a,))
                if r and r[f"pow_{a:g}"] >= 0.8:
                    res[a] = d; break
        mde.append((K, m, rho, pi, 0.6, K * m, res[A05], res[AH]))
    save("headline_mde.csv", "K,m,rho,pi,p0,approx_pairs,MDE_a05,MDE_a0167", mde)

    ni = []
    for K, rho, pi, d in itertools.product([40, 80, 200, 500, 1000, 2000], [0.05, 0.15, 0.30], [0.10, 0.20], [0.0, 0.02]):
        r = sim_paired(K, 4, rho, 0.6, pi, d, 800, rng_next(), ni_margin=0.02)
        ni.append((K, 4, rho, pi, d, K * 4, r["pow_ni"]))
    save("noninferiority_power.csv", "K,m,rho,pi,true_delta,approx_pairs,power_ni_2pp", ni)

    nz = []
    for K, e, d in itertools.product([40, 80, 200], [0.0, 0.05, 0.10, 0.15, 0.25], [0.05, 0.10]):
        r = sim_paired(K, 3.75, 0.15, 0.6, 0.2, d, NS, rng_next(), alphas=(A05,), noise=e)
        nz.append((K, e, d, r["est"], r[kA]))
    save("label_noise_power.csv", "K,contamination,true_delta,mean_observed_delta,power_a05", nz)

    ln = []
    for g, d in itertools.product([1, 2, 3, 5], [0.05, 0.10]):
        r = sim_paired(40, max(3.75 / g, 1.0), 0.15, 0.6, 0.2, d, NS, rng_next(), alphas=(A05,), g=g)
        ln.append((g, d, round(r["n_pairs"], 1), round(r["n_pairs"] / g, 1), r[kA]))
    save("lineage_duplicates_power.csv", "pairs_per_lineage,true_delta,raw_pairs,independent_lineages,power_a05", ln)

    h7 = []
    designs = {"H-R alone (K=40; 150 Div; hard 27%)": (40, 150 / 40 * 0.27),
               "H-M alone (K=40; 200 Div; hard 50%)": (40, 200 / 40 * 0.50),
               "H-R expanded (K=80; 300 Div)": (80, 300 / 80 * 0.27),
               "H-R expanded (K=150; 600 Div)": (150, 600 / 150 * 0.27),
               "H-R expanded (K=300; 1200 Div)": (300, 1200 / 300 * 0.27),
               "H-M expanded (K=80; 400 Div; hard 50%)": (80, 400 / 80 * 0.5)}
    for name, (K, mh) in designs.items():
        for p0, pi, d, rho in itertools.product([0.3, 0.5], [0.10, 0.20, 0.30], [0.03, 0.05, 0.10], [0.05, 0.15, 0.30]):
            r = sim_paired(K, mh, rho, p0, pi, d, NS, rng_next(), alphas=(A05, AH), zero_ok=True, min_est=0.03)
            if r is None:
                continue
            h7.append((name, p0, pi, d, rho, round(r["n_pairs"], 1), r[kA], r[kH]))
    save("h7_hard_stratum_power.csv", "design,p0_hard,pi,delta,rho,hard_pairs,power_a05_est_ge_3pp,power_a0167_est_ge_3pp", h7)

    io = []
    for pio, K, a_true, rho in itertools.product([0.05, 0.10, 0.20, 0.30], [40, 80], [0.75, 0.85, 0.95], [0.15, 0.30]):
        nio = 150 * pio / (1 - pio)
        r = sim_h8a(K, nio, rho, a_true, 0.8, 2000, rng_next())
        io.append((pio, K, round(nio, 1), a_true, rho, r[0], r[1], r[2]))
    save("h8a_annotation_power.csv", "prevalence_io,K,n_io,true_annot_given_fire,rho,power_point_ge_70,power_lcb95_ge_70,mean_n_fire", io)

    fa = []
    for n_io, Kmode, f, c in itertools.product([38, 150, 300, 600, 1000, 1500, 3000, 6000], ["K40", "m4"], [0.0, 0.002, 0.005], [0.0, 0.02, 0.05]):
        K = 40 if Kmode == "K40" else max(40, n_io // 4)
        fa.append((n_io, K, f, c, 0.15, sim_h8b(n_io, f, c, 0.15, K, 4000, rng_next())))
    save("h8b_false_alarm_power.csv", "n_io,K,true_false_alarm,label_contamination,rho,power_ucb95_le_1pct", fa)

    rq = []
    for a_true, rho in itertools.product([0.80, 0.85, 0.90, 0.95], [0.15, 0.30]):
        need = None
        for nio in [10, 15, 20, 30, 40, 50, 60, 80, 100, 130, 160, 200, 300, 400]:
            if sim_h8a(40, nio, rho, a_true, 0.8, 1500, rng_next())[1] >= 0.8:
                need = nio; break
        rq.append((a_true, rho, need))
    save("h8a_required_n_io.csv", "true_annot_given_fire,rho,n_io_for_power_80_lcb", rq)

    open(os.path.join(OUT, "RESULTS.txt"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
