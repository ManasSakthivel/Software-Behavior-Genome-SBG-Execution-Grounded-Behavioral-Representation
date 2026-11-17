#!/usr/bin/env python
"""Power / MDE recomputed from the ACTUAL design (projects, pairs per project, discordance, ICC).

Every number is SIMULATION-BASED under the labelled assumptions below; it is not a prediction of
system performance. Re-run with DEV-N / VAL parameters BEFORE sealing, and again with the realised
holdout design (power is a design property; do NOT report post-hoc power at the observed effect).

ASSUMPTIONS (printed in the output JSON):
 A1 outcome per pair is binary success for the 'improvement' outcome (detection) on truth=DIV pairs.
 A2 cells (neither, ref-only, test-only, both) per project ~ Dirichlet(alpha*q), alpha=1/rho-1
    (so the ICC of the paired difference ~ rho); q from p0 (ref success), pi (discordance), delta.
 A3 cluster sizes = observed sizes, or min(8,1+Poisson(m-1)) when overridden.
 A4 test = the plan's primary test: project-level sign-flip permutation (two-sided), alpha and alpha/family.
Inputs: either --processed CSV (+ --test/--reference systems) to read K, sizes, p0, pi, rho from data,
or explicit --projects/--mean-pairs/--p0/--pi/--rho.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_results as ar


def simulate_power(sizes, p0, pi, rho, delta, alpha, sims=600, flips=499, seed=20261117):
    q10, q01 = (pi - delta) / 2, (pi + delta) / 2
    q11, q00 = p0 - q10, 1 - p0 - q01
    if min(q10, q01, q11, q00) < -1e-12:
        return None  # infeasible cell probabilities (delta > pi, or p0 out of range)
    q = np.clip([q00, q10, q01, q11], 1e-9, None)
    q /= q.sum()
    rng = np.random.default_rng(seed)
    K, N = len(sizes), int(np.sum(sizes))
    proj = np.repeat(np.arange(K), sizes)
    onehot = np.zeros((N, K))
    onehot[np.arange(N), proj] = 1
    alpha_d = 1 / max(rho, 0.01) - 1
    g = rng.gamma(alpha_d * q, size=(sims, K, 4)) + 1e-300
    cum = np.cumsum(g / g.sum(-1, keepdims=True), -1)[:, proj, :3]
    cell = (rng.random((sims, N))[..., None] > cum).sum(-1)
    d = ((cell == 2).astype(float) - (cell == 1)) @ onehot            # per-project b - c
    signs = rng.choice([-1.0, 1.0], size=(flips, K))
    obs = np.abs(d.sum(1))
    perm = np.abs(d @ signs.T)
    p = (1 + (perm >= obs[:, None] - 1e-9).sum(1)) / (1 + flips)
    return float(np.mean((p < alpha) & (d.sum(1) > 0)))


def mde(sizes, p0, pi, rho, alpha, target=0.8, step=0.01, **kw):
    for delta in np.arange(step, pi + 1e-9, step):
        pw = simulate_power(sizes, p0, pi, rho, delta, alpha, **kw)
        if pw is not None and pw >= target:
            return round(float(delta), 4)
    return None  # not reached below the discordance ceiling


def from_data(path, test, ref):
    df = ar.load(path)
    o = ar.outcome_frame(df)
    a = o[(o.system == test) & (o.truth == "DIV")].set_index("pair_id")
    b = o[(o.system == ref) & (o.truth == "DIV")].set_index("pair_id")
    dd = a.detection - b.detection.reindex(a.index)
    ds = ar.design_stats(a.project.to_numpy(), dd.to_numpy())
    sizes = a.groupby("project").size().to_numpy()
    return dict(sizes=sizes, p0=float(b.detection.mean()), pi=float((dd != 0).mean()), rho=ds["icc"],
                observed_delta_for_information_only=float(dd.mean()), design=ds)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--processed"); ap.add_argument("--test"); ap.add_argument("--reference")
    ap.add_argument("--projects", type=int); ap.add_argument("--mean-pairs", type=float, default=4.0)
    ap.add_argument("--p0", type=float); ap.add_argument("--pi", type=float); ap.add_argument("--rho", type=float)
    ap.add_argument("--family", type=int, default=3, help="Holm family size for the conservative alpha/family")
    ap.add_argument("--sims", type=int, default=600); ap.add_argument("--out")
    a = ap.parse_args(argv)
    base = from_data(a.processed, a.test, a.reference) if a.processed else {}
    pick = lambda arg, k: arg if arg is not None else base.get(k)
    p0, pi, rho = pick(a.p0, "p0"), pick(a.pi, "pi"), pick(a.rho, "rho")
    if None in (p0, pi, rho):
        sys.exit("need --processed or all of --p0 --pi --rho")
    if a.projects:
        rng = np.random.default_rng(1)
        sizes = np.minimum(8, 1 + rng.poisson(a.mean_pairs - 1, a.projects))
    else:
        sizes = base["sizes"]
    rows = []
    for rho_s in sorted({round(rho, 3), 0.05, 0.15, 0.30}):
        for pi_s in sorted({round(pi, 3), round(pi * 0.5, 3), round(min(pi * 1.5, 0.9), 3)}):
            for al in (0.05, 0.05 / a.family):
                r = dict(rho=rho_s, pi=pi_s, alpha=round(al, 4), K=len(sizes), pairs=int(np.sum(sizes)))
                for dl in (0.05, 0.10):
                    r[f"power_{int(dl*100)}pp"] = simulate_power(sizes, p0, pi_s, rho_s, dl, al, a.sims)
                r["mde_80"] = mde(sizes, p0, pi_s, rho_s, al, sims=max(200, a.sims // 3))
                rows.append(r)
    res = dict(assumptions=__doc__, inputs=dict(p0=p0, pi=pi, rho=rho, K=len(sizes), pairs=int(np.sum(sizes)),
               from_data={k: v for k, v in base.items() if k != "sizes"}), grid=rows,
               note="power at +10pp (P0 D8) is the confirmatory yardstick; +5pp exploratory; mde_80=None means not reachable below pi.")
    txt = json.dumps(res, indent=1, default=float)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(txt)
    print(txt)
    return res


if __name__ == "__main__":
    main()
