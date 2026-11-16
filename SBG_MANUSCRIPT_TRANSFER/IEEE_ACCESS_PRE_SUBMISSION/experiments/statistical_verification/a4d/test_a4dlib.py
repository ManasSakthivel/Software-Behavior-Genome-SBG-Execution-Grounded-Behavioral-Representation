"""Unit tests for a4dlib (run: python test_a4dlib.py   or   pytest test_a4dlib.py)."""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a4dlib as L  # noqa: E402


def _rand(n=120, K=6, seed=1, ties=True):
    rng = random.Random(seed)
    y = [rng.randint(0, 1) for _ in range(n)]
    c = [f"p{rng.randrange(K)}" for _ in range(n)]
    s = [(round(rng.gauss(0.8 * yy, 1), 1) if ties else rng.gauss(0.8 * yy, 1)) for yy in y]
    s2 = [(round(rng.gauss(0.4 * yy, 1), 1) if ties else rng.gauss(0.4 * yy, 1)) for yy in y]
    return y, c, s, s2


def test_auroc_vs_bruteforce_and_cliff():
    for seed in range(5):
        y, c, s, _ = _rand(seed=seed)
        assert abs(L.auroc(s, y) - L.auroc_bruteforce(s, y)) < 1e-12
        assert abs(L.cliffs_delta(s, y) - (2 * L.auroc(s, y) - 1)) < 1e-12
    assert L.auroc([1, 1, 1, 1], [0, 1, 0, 1]) == 0.5
    assert L.auroc([0, 1, 2, 3], [0, 0, 1, 1]) == 1.0


def test_pair_matrices_bootstrap_equals_direct_resample():
    y, c, s, s2 = _rand()
    d = L.Data(y, c)
    U, D = L.pair_matrices(d, s)
    assert abs(L.auroc_from_matrices(U, D) - L.auroc(s, y)) < 1e-12
    res = L.Resamples(d.K, B=25, seed=7)
    for m in res.counts:
        idx = [i for k in range(d.K) for _ in range(m[k]) for i in d.members[k]]
        yy = [y[i] for i in idx]
        want = L.auroc_bruteforce([s[i] for i in idx], yy) if 0 < sum(yy) < len(yy) else None
        got = L.auroc_from_matrices(U, D, m)
        assert (want is None and got is None) or abs(want - got) < 1e-12


def test_strata_matrices():
    y, c, s, _ = _rand()
    d = L.Data(y, c)
    st = [i % 3 for i in range(d.n)]
    U, D = L.pair_matrices(d, s, st)
    num = den = 0.0
    for a in range(d.n):
        for b in range(d.n):
            if y[a] == 1 and y[b] == 0 and st[a] == st[b]:
                num += 1.0 if s[a] > s[b] else 0.5 if s[a] == s[b] else 0.0
                den += 1
    assert abs(L.auroc_from_matrices(U, D) - num / den) < 1e-12


def test_auprc_known():
    # perfect ranking -> 1; all tied -> prevalence
    assert abs(L.auprc([3, 2, 1, 0], [1, 1, 0, 0]) - 1.0) < 1e-12
    assert abs(L.auprc([1, 1, 1, 1], [1, 0, 1, 0]) - 0.5) < 1e-12
    # hand example: scores 4,3,2,1 labels 1,0,1,0 -> AP = (1/2)(1) + (1/2)(2/3)
    assert abs(L.auprc([4, 3, 2, 1], [1, 0, 1, 0]) - (0.5 * 1 + 0.5 * 2 / 3)) < 1e-12


def test_youden_prf():
    s = [0.1, 0.2, 0.2, 0.7, 0.8, 0.9]
    y = [0, 0, 1, 1, 1, 0]
    thr, j = L.youden(s, y)
    best = max((sum(1 for a, b in zip(s, y) if a >= t and b == 1) / 3 - sum(1 for a, b in zip(s, y) if a >= t and b == 0) / 3, -t) for t in set(s))
    assert abs(j - best[0]) < 1e-12 and thr == -best[1]
    r = L.prf(s, y, 0.7)
    assert (r["tp"], r["fp"], r["fn"], r["tn"]) == (2, 1, 1, 2)


def test_distributions():
    assert abs(L.t_ppf(0.975, 18) - 2.100922) < 1e-5
    assert abs(L.t_ppf(0.975, 10) - 2.228139) < 1e-5
    assert abs(L.t_ppf(0.8, 18) - 0.862049) < 1e-4
    assert abs(L.t_two_sided_p(2.100922, 18) - 0.05) < 1e-5


def test_holm_bh():
    p = {"a": 0.01, "b": 0.04, "c": 0.03}
    h = L.holm(p)
    assert abs(h["a"] - 0.03) < 1e-12 and abs(h["c"] - 0.06) < 1e-12 and abs(h["b"] - 0.06) < 1e-12
    bh = L.benjamini_hochberg(p)
    assert abs(bh["a"] - 0.03) < 1e-12 and abs(bh["c"] - 0.04) < 1e-12 and abs(bh["b"] - 0.04) < 1e-12
    assert abs(L.holm({"a": 0.01}, m=19)["a"] - 0.19) < 1e-12


def test_wilcoxon_sign():
    p, w = L.wilcoxon_exact_p([1, 2, 3, 4, 5])
    assert abs(p - 2 / 32) < 1e-12 and w == 15
    p, _ = L.wilcoxon_exact_p([1, -2, 3, -4, 5, 6])  # W+=1+3+5+6=15, n=6 -> exact two-sided 0.4375? compute by brute force
    brute = 0
    for mask in range(64):
        t = sum((r if (mask >> (r - 1)) & 1 else 0) for r in range(1, 7))
        if t >= 15 or t <= 21 - 15:
            brute += 1
    assert abs(p - brute / 64) < 1e-12
    ps, a, b = L.sign_test_p([1, 1, 1, 1, -1, 0])
    assert (a, b) == (4, 1) and abs(ps - 2 * (1 + 5) / 32) < 1e-12


def test_delong_matches_known_properties():
    y, c, s, s2 = _rand(n=200, K=5, seed=3, ties=False)
    r = L.delong_test(s, s2, y)
    assert abs(r["auc_a"] - L.auroc(s, y)) < 1e-12 and abs(r["auc_b"] - L.auroc(s2, y)) < 1e-12
    r0 = L.delong_test(s, s, y)
    assert r0["p"] == 1.0
    # DeLong single-AUC variance vs Hanley-McNeil order of magnitude
    assert 0.01 < r["se_a"] < 0.06
    # invariance to swapping roles
    r2 = L.delong_test(s2, s, y)
    assert abs(r["z"] + r2["z"]) < 1e-9
    # tie-aware components average to AUROC on both sides
    v10, v01 = L.delong_components(s, y)
    assert abs(sum(v10) / len(v10) - sum(v01) / len(v01)) < 1e-12


def test_logistic_newton_vs_gd():
    rng = random.Random(0)
    X = [[rng.gauss(0, 1), rng.gauss(5, 3)] for _ in range(150)]
    y = [1 if (x[0] + 0.1 * x[1] + rng.gauss(0, 1)) > 0.5 else 0 for x in X]
    a = L.fit_logistic_newton(X, y)
    b = L.fit_logistic_gd(X, y, iters=3000)
    assert max(abs(p - q) for p, q in zip(a["w"], b["w"])) < 1e-3 and abs(a["b"] - b["b"]) < 1e-3


def test_icc():
    # perfectly clustered -> ICC ~1 ; pure noise -> ~0 (can be slightly negative)
    vals = [1, 1, 1, 5, 5, 5, 9, 9, 9]
    cl = ["a"] * 3 + ["b"] * 3 + ["c"] * 3
    assert L.icc1(vals, cl)[0] > 0.99
    rng = random.Random(0)
    v = [rng.random() for _ in range(2000)]
    c = [i % 20 for i in range(2000)]
    assert abs(L.icc1(v, c)[0]) < 0.05


def test_signflip_and_power():
    assert abs(L.signflip_weighted_p([1, 1, 1, 1, 1], [1] * 5) - 2 / 32) < 1e-12
    m = L.mde(0.02, 18)
    assert 0.05 < m["mde_t"] < 0.065 and m["mde_normal"] < m["mde_t"]
    assert abs(L.power_at(0.0, 0.02, 18) - 0.05) < 1e-6


def test_zsum_rankavg():
    rng = random.Random(1)
    X = [[rng.gauss(yy, 1), rng.gauss(-yy, 1)] for yy in (rng.randint(0, 1) for _ in range(300))]
    y = [1 if r[0] > 0.5 else 0 for r in X]
    m = L.fit_zsum(X, y)
    assert m["sign"][0] == 1.0
    q = L.fit_rankavg(X, y)
    sc = [L.rankavg_apply(q, r) for r in X]
    assert 0.0 <= min(sc) and max(sc) <= 1.0 and L.auroc(sc, y) > 0.7


if __name__ == "__main__":
    fs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for f in fs:
        f()
        print("ok", f.__name__)
    print(f"{len(fs)} tests passed")
