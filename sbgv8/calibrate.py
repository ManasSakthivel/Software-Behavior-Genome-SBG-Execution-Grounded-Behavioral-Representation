"""Transparent monotone-sign L2-penalised logistic regression of false-assurance risk, P(Y=1 | phi(E), eligible).
- features come from sbgv8.profile.build_profile (or an injected profile_fn); optional extra_features_fn adds ERS response features
- sign constraints are pre-declared (RISK_SIGN) and enforced as box bounds in L-BFGS-B; ERS features have free sign (no pre-declared direction)
- fit on ELIGIBLE pairs only (no witness, no hard blocker, V7-B verdict not DIVERGENT_OBSERVABLE); y=None pairs skipped and counted
- y is read ONLY inside fit()/recalibrate()/threshold_for_risk(); never in predict_risk/decide.
"""
from __future__ import annotations
import math
import numpy as np
from scipy import optimize
from . import stats

# pre-declared directions: -1 => more of the feature lowers risk, +1 => raises it, 0 => free (ERS response features)
RISK_SIGN = {"act_frac": -1, "branch_cov_min": -1, "mu_min": -1, "mu_mean": -1, "n_same": -1, "n_rep": -1, "obs_react": -1,
             "n_eff": -1, "n_eff_prov": -1, "repro_frac": -1, "lossy_frac": +1, "chan_complete": -1, "prov_ok": -1,
             "integrity_ok": -1, "env_ok": -1}
LOG1P = {"mu_min", "mu_mean", "n_same", "n_rep", "n_eff", "n_eff_prov"}   # count features enter as log1p
LAMBDA_GRID = (0.3, 1.0, 3.0, 10.0)
DEFAULT_LAMBDA = 1.0


def default_profile(rec):
    from . import profile  # lazy: agent B's module
    return profile.build_profile(rec)


def v7b_verdict(rec):
    try:
        from . import profile
        return profile.v7b_style_decision(rec)[0]
    except (ImportError, AttributeError):
        return rec.v7b_verdict


def has_witness(rec):
    return any(i.outcome == "CONFIRMED_DIFF" for i in rec.inputs)


def is_div(rec):
    return has_witness(rec) or v7b_verdict(rec) == "DIVERGENT_OBSERVABLE"


# V7-B blocker codes that merely restate graded coverage evidence (act_frac / branch coverage are features). Treating them as HARD would
# make coverage constant among eligible pairs and the coverage-only baseline vacuous. STRICT_BLOCKERS=True (sensitivity run) makes every blocker hard.
SOFT_BLOCKERS = {"changed_region_not_activated", "budget_exhausted_s0"}
STRICT_BLOCKERS = False


def _code(b): return b[0] if isinstance(b, (list, tuple)) else str(b)


def is_eligible(rec):
    return not is_div(rec) and all(_code(b) in SOFT_BLOCKERS and not STRICT_BLOCKERS for b in rec.blockers)


def _vec(feats, names, mean=None, std=None):
    x = np.array([float(feats[n]) for n in names])
    x = np.array([math.log1p(max(v, 0.0)) if n in LOG1P else v for n, v in zip(names, x)])
    return x if mean is None else (x - mean) / std


class Model:
    def __init__(self, names, extra_names, coef, intercept, mean, std, lam, tau=-math.inf, profile_fn=None, extra_fn=None, info=None):
        self.names = list(names); self.extra_names = list(extra_names); self.all_names = self.names + self.extra_names
        self.coef = np.asarray(coef, float); self.intercept = float(intercept); self.mean = np.asarray(mean); self.std = np.asarray(std)
        self.lam = lam; self.tau = tau; self.profile_fn = profile_fn; self.extra_fn = extra_fn; self.info = info or {}
        self.recal = None   # ("platt", a, b) | ("iso", xs, ys)

    # --- features / prediction (never touches rec.y) ---
    def features(self, rec):
        f = dict((self.profile_fn or default_profile)(rec))
        if self.extra_fn: f.update(self.extra_fn(rec))
        return f

    def raw_logit(self, rec):
        return float(self.intercept + self.coef @ _vec(self.features(rec), self.all_names, self.mean, self.std))

    def _apply_recal(self, z):
        p = 1 / (1 + math.exp(-z))
        if self.recal is None: return p
        if self.recal[0] == "platt": return 1 / (1 + math.exp(-(self.recal[1] + self.recal[2] * z)))
        return float(np.interp(p, self.recal[1], self.recal[2]))

    def predict_risk(self, rec):
        return min(1.0, max(0.0, self._apply_recal(self.raw_logit(rec))))

    def decide(self, rec):
        """DIV precedence kept; NDO iff eligible and risk <= tau; else INSUFFICIENT."""
        r = self.predict_risk(rec)
        # V8 trust gate (resolution of ERS P8 finding, see reports/v8/V8_ERS_SPECIFICATION.md): evidence that failed integrity
        # verification is not accepted for ANY verdict, including a witnessed divergence. V7-B itself is unchanged.
        if not rec.integrity_ok: return "INSUFFICIENT", 1.0
        if is_div(rec): return "DIVERGENT_OBSERVABLE", r
        return ("NO_DIVERGENCE_OBSERVED" if is_eligible(rec) and r <= self.tau else "INSUFFICIENT"), r

    def coef_report(self):
        rows = [{"feature": n, "declared_sign": RISK_SIGN.get(n, 0), "std_coef": float(c), "transform": "log1p" if n in LOG1P else "raw",
                 "mean": float(m), "std": float(s), "at_bound": bool(RISK_SIGN.get(n, 0) and abs(c) < 1e-9)}
                for n, c, m, s in zip(self.all_names, self.coef, self.mean, self.std)]
        return {"intercept": self.intercept, "lambda": self.lam, "tau": self.tau, "recalibration": self.recal[0] if self.recal else None,
                "coefficients": rows, **self.info}

    # --- recalibration on a SEPARATE fold ---
    def recalibrate(self, cal_records, method="platt"):
        d = [(self.raw_logit(r), r.y) for r in cal_records if r.y is not None and is_eligible(r)]
        if len(d) < 10 or len({y for _, y in d}) < 2: return self
        z = np.array([a for a, _ in d]); y = np.array([b for _, b in d], float)
        if method == "platt":
            f = lambda b: np.sum(np.logaddexp(0, b[0] + b[1] * z) - y * (b[0] + b[1] * z)) + 1e-6 * b[1] ** 2
            b = optimize.minimize(f, [0.0, 1.0], bounds=[(None, None), (1e-3, None)], method="L-BFGS-B").x
            self.recal = ("platt", float(b[0]), float(b[1]))
        else:
            p = 1 / (1 + np.exp(-z)); o = np.argsort(p, kind="stable"); xs, ys = p[o], y[o]
            vals, cnts = [], []   # pool adjacent violators
            for v in ys:
                vals.append(v); cnts.append(1)
                while len(vals) > 1 and vals[-2] > vals[-1]:
                    t = cnts[-2] + cnts[-1]; vals[-2:] = [(vals[-2] * cnts[-2] + vals[-1] * cnts[-1]) / t]; cnts[-2:] = [t]
            fit = np.repeat(vals, cnts)
            self.recal = ("iso", xs, fit)
        return self


def _design(records, names, extra_fn, profile_fn):
    pf = profile_fn or default_profile
    rows = []
    for r in records:
        f = dict(pf(r))
        if extra_fn: f.update(extra_fn(r))
        rows.append(_vec(f, names))
    return np.array(rows).reshape(len(records), len(names))


def _solve(Z, y, lo, hi, lam):
    k = Z.shape[1]
    def f(b):
        eta = b[0] + Z @ b[1:]
        nll = np.sum(np.logaddexp(0, eta) - y * eta) + 0.5 * lam * np.sum(b[1:] ** 2)
        g = 1 / (1 + np.exp(-eta)) - y
        return nll, np.r_[g.sum(), Z.T @ g + lam * b[1:]]
    r = optimize.minimize(f, np.zeros(k + 1), jac=True, method="L-BFGS-B", bounds=[(None, None)] + list(zip(lo, hi)))
    return r.x


def fit(train_records, feature_names, extra_features_fn=None, lam=DEFAULT_LAMBDA, profile_fn=None, extra_names=None, tau=-math.inf):
    """Fit on eligible, labelled pairs. `extra_names` = names produced by extra_features_fn (free sign). Returns Model."""
    names = list(dict.fromkeys(feature_names))     # dedupe (cov_act repeats act_frac)
    extra = list(extra_names or [])
    allnames = names + [e for e in extra if e not in names]
    skipped_y = sum(r.y is None for r in train_records)
    el = [r for r in train_records if r.y is not None and is_eligible(r)]
    X = _design(el, allnames, extra_features_fn, profile_fn); y = np.array([r.y for r in el], float)
    mean = X.mean(0) if len(el) else np.zeros(len(allnames)); std = X.std(0) if len(el) else np.ones(len(allnames))
    dead = std < 1e-12; std = np.where(dead, 1.0, std)
    Z = (X - mean) / std
    sg = np.array([RISK_SIGN.get(n, 0) for n in allnames])
    lo = np.where(sg > 0, 0.0, np.where(sg < 0, -np.inf, -np.inf)); hi = np.where(sg > 0, np.inf, np.where(sg < 0, 0.0, np.inf))
    lo = np.where(dead, 0.0, lo); hi = np.where(dead, 0.0, hi)
    if len(el) and y.min() != y.max():
        b = _solve(Z, y, lo, hi, lam)
    else:   # degenerate labels: constant prior risk
        pr = (y.mean() if len(el) else 0.5); pr = min(max(pr, 1e-3), 1 - 1e-3)
        b = np.r_[math.log(pr / (1 - pr)), np.zeros(len(allnames))]
    info = {"n_train_total": len(train_records), "n_train_eligible_labelled": len(el), "n_skipped_y_none": skipped_y,
            "n_ineligible_excluded": sum(not is_eligible(r) for r in train_records), "train_base_rate": float(y.mean()) if len(el) else None}
    return Model(names, [e for e in extra if e not in names], b[1:], b[0], mean, std, lam, tau, profile_fn, extra_features_fn, info)


def scores(model, records):
    """Risk and eligibility arrays for records (no y access)."""
    return (np.array([model.predict_risk(r) for r in records]), np.array([is_eligible(r) for r in records]))


def threshold_for_risk(cal_records, alpha, model, B=1000, seed=0):
    """Largest-coverage tau whose upper (95% one-sided) project-cluster-bootstrap bound on selective risk <= alpha, on cal_records
    (y=None pairs dropped). Returns (tau, info); tau=-inf issues nothing."""
    cr = [r for r in cal_records if r.y is not None]
    s, e = scores(model, cr)
    return stats.select_threshold(s, e, [r.y for r in cr], [r.project for r in cr], alpha, B, seed)


def crc_threshold(cal_records, model, alpha, by_project=True):
    """EXPLORATORY. Conformal risk control (Angelopoulos et al.) for the JOINT risk J(tau)=E[1(NDO issued and Y=1)].
    Loss L(tau)=1[eligible, risk<=tau, y=1] is bounded in [0,1] and non-decreasing in tau; choose the largest tau with
    n/(n+1)*mean L(tau) + 1/(n+1) <= alpha. Assumptions: units are exchangeable (project units when by_project=True: per-project mean
    loss; otherwise pairs, which is NOT valid when pairs cluster by project); the model was fit on data disjoint from cal_records;
    guarantee is in EXPECTATION over the calibration draw, for the joint risk J (=c*R), NOT for conditional R, and not per pair/project.
    Returns tau (-inf if even the empty rule violates the bound, i.e. n too small)."""
    cr = [r for r in cal_records if r.y is not None]
    s, e = scores(model, cr)
    y = np.array([r.y for r in cr], float); pr = np.array([r.project for r in cr])
    cands = sorted(set(s[e & (y >= 0)].tolist()))
    best = -math.inf
    units = sorted(set(pr))
    n = len(units) if by_project else len(cr)
    for t in cands:
        L = ((s <= t) & e & (y == 1)).astype(float)
        mean = np.mean([L[pr == u].mean() for u in units]) if by_project else L.mean()
        if n / (n + 1) * mean + 1 / (n + 1) <= alpha: best = t
        else: break   # monotone in tau
    return best


def oof_risks(records, names, k=3, seed=0, lam=DEFAULT_LAMBDA, **kw):
    """Project-grouped out-of-fold risk for each record (inner CV). Eligibility-only fitting inside each fold."""
    fold = stats.project_folds([r.project for r in records], k, seed)
    out = np.full(len(records), 0.5)
    for f in sorted(set(fold)):
        tr = [r for r, g in zip(records, fold) if g != f]; te = [i for i, g in enumerate(fold) if g == f]
        m = fit(tr, names, lam=lam, **kw)
        for i in te: out[i] = m.predict_risk(records[i])
    return out


def fit_select(records, names, alphas=(0.15,), inner_k=3, seed=0, B=1000, lam_grid=LAMBDA_GRID, **kw):
    """Model selection on inner project folds only: lambda by OOF log loss, thresholds tau_alpha from OOF risks (never from the final
    fit's in-sample risks, never from any outer test fold). Returns Model refit on all `records` with .tau (first alpha) and .taus."""
    lab = [r for r in records if r.y is not None]
    el = np.array([is_eligible(r) for r in lab]); y = np.array([r.y for r in lab], float); proj = [r.project for r in lab]
    best = (math.inf, DEFAULT_LAMBDA, None)
    for lam in lam_grid:
        p = oof_risks(lab, names, inner_k, seed, lam, **kw)
        ll = stats.logloss(p[el], y[el]) if el.sum() else math.inf
        if ll < best[0] - 1e-12: best = (ll, lam, p)
    lam, p = best[1], best[2]
    taus = {}
    for a in alphas:
        taus[a] = stats.select_threshold(p, el, y, proj, a, B, seed)[0] if p is not None else -math.inf
    m = fit(records, names, lam=lam, tau=taus[alphas[0]], **kw)
    m.taus = taus; m.info["chosen_lambda"] = lam; m.info["inner_oof_logloss"] = best[0] if best[0] < math.inf else None
    return m


def cli_register(sub):
    p = sub.add_parser("calibrate", help="fit the monotone-sign logistic model on a records jsonl; print coef_report (development data)")
    p.add_argument("--records", required=True); p.add_argument("--features", default="full_profile"); p.add_argument("--lam", type=float, default=DEFAULT_LAMBDA)
    p.set_defaults(func=_cli)


def _cli(a):
    import json
    from . import schema
    from .evaluate import load_records
    m = fit(load_records(a.records), schema.FEATURE_SETS[a.features], lam=a.lam)
    print(json.dumps(m.coef_report(), indent=1)); return 0
