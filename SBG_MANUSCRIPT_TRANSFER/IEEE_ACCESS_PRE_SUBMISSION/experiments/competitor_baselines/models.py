"""Stdlib models for the A4 combiners: CART tree / random forest (B03c) and an exact Newton (IRLS) solver for the same L2-logistic objective as
eval_lib.fit_logistic (used only for the exploratory leave-one-program-out refits, where 5000-step gradient descent is too slow)."""
from __future__ import annotations

import math
import random


# ------------------------------------------------------------------ CART / forest
class Tree:
    def __init__(self, max_depth, min_leaf=10, mtry=None, rng=None, nthr=24):
        self.max_depth, self.min_leaf, self.mtry, self.rng, self.nthr = max_depth, min_leaf, mtry, rng, nthr
        self.root = None

    @staticmethod
    def _gini(pos, n):
        if n == 0:
            return 0.0
        p = pos / n
        return 2 * p * (1 - p)

    def fit(self, X, y, idx=None):
        idx = list(range(len(X))) if idx is None else idx
        self.p = len(X[0])
        self.root = self._grow(X, y, idx, 0)
        return self

    def _leaf(self, y, idx):
        pos = sum(y[i] for i in idx)
        return ("leaf", (pos + 1.0) / (len(idx) + 2.0))

    def _grow(self, X, y, idx, depth):
        pos = sum(y[i] for i in idx)
        n = len(idx)
        if depth >= self.max_depth or n < 2 * self.min_leaf or pos == 0 or pos == n:
            return self._leaf(y, idx)
        feats = list(range(self.p))
        if self.mtry:
            feats = self.rng.sample(feats, min(self.mtry, self.p))
        best = (self._gini(pos, n) - 1e-12, None, None)
        base_imp = self._gini(pos, n)
        for f in feats:
            vals = sorted(set(X[i][f] for i in idx))
            if len(vals) < 2:
                continue
            cands = [(vals[k] + vals[k + 1]) / 2 for k in range(len(vals) - 1)]
            if len(cands) > self.nthr:
                step = len(cands) / self.nthr
                cands = [cands[int(j * step)] for j in range(self.nthr)]
            for t in cands:
                nl = pl = 0
                for i in idx:
                    if X[i][f] <= t:
                        nl += 1
                        pl += y[i]
                nr = n - nl
                if nl < self.min_leaf or nr < self.min_leaf:
                    continue
                imp = (nl * self._gini(pl, nl) + nr * self._gini(pos - pl, nr)) / n
                if imp < best[0]:
                    best = (imp, f, t)
        if best[1] is None or base_imp - best[0] < 1e-9:
            return self._leaf(y, idx)
        f, t = best[1], best[2]
        L = [i for i in idx if X[i][f] <= t]
        R = [i for i in idx if X[i][f] > t]
        return ("node", f, t, self._grow(X, y, L, depth + 1), self._grow(X, y, R, depth + 1))

    def predict(self, x):
        n = self.root
        while n[0] == "node":
            n = n[3] if x[n[1]] <= n[2] else n[4]
        return n[1]


class Forest:
    def __init__(self, n_trees=50, max_depth=4, seed=42, min_leaf=10):
        self.n_trees, self.max_depth, self.seed, self.min_leaf = n_trees, max_depth, seed, min_leaf

    def fit(self, X, y):
        rng = random.Random(self.seed)
        p = len(X[0])
        mtry = max(1, int(math.sqrt(p)))
        self.trees, self.inbag = [], []
        for _ in range(self.n_trees):
            idx = [rng.randrange(len(X)) for _ in range(len(X))]
            self.inbag.append(set(idx))
            self.trees.append(Tree(self.max_depth, self.min_leaf, mtry, rng).fit(X, y, idx))
        return self

    def oob_scores(self, X):
        """Out-of-bag probability per training row (used to choose thresholds without in-sample overfit)."""
        out = []
        for i, x in enumerate(X):
            ps = [t.predict(x) for t, ib in zip(self.trees, self.inbag) if i not in ib]
            out.append(sum(ps) / len(ps) if ps else self.predict(x))
        return out

    def predict(self, x):
        return sum(t.predict(x) for t in self.trees) / len(self.trees)


# ------------------------------------------------------------------ Newton solver for the eval_lib logistic objective
def _solve(A, b):
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[piv] = M[piv], M[c]
        d = M[c][c] or 1e-12
        for r in range(c + 1, n):
            f = M[r][c] / d
            for k in range(c, n + 1):
                M[r][k] -= f * M[c][k]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (M[r][n] - sum(M[r][k] * x[k] for k in range(r + 1, n))) / (M[r][r] or 1e-12)
    return x


def fit_logistic_irls(X, y, l2=1.0, iters=30):
    """Minimises mean log-loss + (l2/2n)||w||^2 on standardised features (bias unpenalised) = fixed point of eval_lib.fit_logistic's gradient descent."""
    n, d = len(X), len(X[0])
    mu = [sum(r[j] for r in X) / n for j in range(d)]
    sd = [math.sqrt(sum((r[j] - mu[j]) ** 2 for r in X) / n) or 1.0 for j in range(d)]
    Z = [[(r[j] - mu[j]) / sd[j] for j in range(d)] + [1.0] for r in X]
    w = [0.0] * (d + 1)
    for _ in range(iters):
        g = [0.0] * (d + 1)
        H = [[0.0] * (d + 1) for _ in range(d + 1)]
        for z, t in zip(Z, y):
            u = sum(a * b for a, b in zip(w, z))
            p = 1 / (1 + math.exp(-max(-30, min(30, u))))
            for j in range(d + 1):
                g[j] += (p - t) * z[j]
                pw = p * (1 - p) * z[j]
                for k in range(j, d + 1):
                    H[j][k] += pw * z[k]
        for j in range(d):
            g[j] += l2 * w[j]
            H[j][j] += l2
        for j in range(d + 1):
            for k in range(j):
                H[j][k] = H[k][j]
        H[d][d] += 1e-9
        step = _solve(H, g)
        w = [a - b for a, b in zip(w, step)]
        if max(abs(s) for s in step) < 1e-8:
            break
    return {"w": w[:d], "b": w[d], "mu": mu, "sd": sd}
