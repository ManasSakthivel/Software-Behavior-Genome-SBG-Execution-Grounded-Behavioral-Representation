"""Sign-flip permutation (protocol test) vs cluster-robust t power at anchor designs. Seeded."""
import os, numpy as np
from scipy import stats
import power_sim as ps
OUT = os.path.join(ps.HERE, "out")
def perm_power(K, m, rho, p0, pi, delta, ns, rng, P=2000, alpha=0.05):
    q = ps.cells(p0, pi, delta); conc = 1 / rho - 1
    n = np.minimum(8, 1 + rng.poisson(max(m - 1, 0), size=(ns, K)))
    pk = rng.gamma(conc * np.clip(q, 1e-9, None), size=(ns, K, 4)); pk /= pk.sum(-1, keepdims=True)
    cnt = rng.multinomial(n, pk); D = (cnt[..., 2] - cnt[..., 1]).astype(float); sN = n.sum(1)
    est = D.sum(1) / sN
    s = rng.choice([-1.0, 1.0], size=(K, P))
    null = (D @ s) / sN[:, None]
    p = (np.abs(null) >= np.abs(est)[:, None] - 1e-12).mean(1)
    return ((p < alpha) & (est > 0)).mean()
rows = ["K,m,rho,p0,pi,delta,power_t,power_perm"]
rng = np.random.default_rng([ps.MASTER, 999])
for K, m, rho, pi, d in [(40,3.75,.15,.2,.05),(40,3.75,.15,.2,.10),(40,3.75,.15,.3,.10),(40,3.75,.05,.1,.10),(80,3.75,.15,.2,.05),(80,3.75,.15,.2,.10),(200,4,.15,.2,.05),(300,4,.15,.2,.05),(450,4,.15,.2,.05),(60,8,.15,.2,.10)]:
    pt = ps.sim_paired(K, m, rho, .6, pi, d, 3000, rng)["pow_0.05"]
    pp = perm_power(K, m, rho, .6, pi, d, 1000, rng)
    rows.append(f"{K},{m},{rho},0.6,{pi},{d},{pt:.3f},{pp:.3f}"); print(rows[-1])
open(os.path.join(OUT, "anchors_perm_vs_t.csv"), "w").write("\n".join(rows) + "\n")
