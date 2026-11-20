"""The nine pre-declared baselines + feature-set ablations behind one registry: REGISTRY[name](train_records, **kw) -> predictor
(.predict_risk(rec) in [0,1], .decide(rec) -> (verdict, risk)). Rule baselines ignore train_records. Risk for rule predictors is the
pseudo-risk 0.0 (NDO issued) / 1.0 (otherwise), so they only have one operating point and are compared at their own coverage.
Model baselines are calibrate.Model fits (tau chosen on inner project folds via calibrate.fit_select).
  b1 plain differential testing: NDO unless a witness           b2 B1+repetition: witness must be deterministic; any quarantined input -> INSUFFICIENT
  b3 V7-B fixed gate (rec.v7b_verdict)                          b4 coverage-only gate: full activation AND branch floor, nothing else
  b5 coverage-gated B1: B1 verdicts, but NDO only if activation floor (act_frac==1) holds   b6 matched abstention (random, 1,000 draws)
  b7 coverage-only calibration (act_frac, branch_cov_min)       b8 full CEC (full_profile + ERS features)   b9 CEC without ERS (full_profile)
"""
from __future__ import annotations
import numpy as np
from . import calibrate, schema
from .calibrate import has_witness, is_div, default_profile, v7b_verdict

DIV, INS, NDO = schema.VERDICTS
BRANCH_FLOOR = 0.80   # V7-B default s2_branch_floor


class Rule:
    def __init__(self, fn, name): self.fn = fn; self.name = name
    def decide(self, rec):
        v = self.fn(rec); return v, 0.0 if v == NDO else 1.0
    def predict_risk(self, rec): return self.decide(rec)[1]


def _floor(rec): return float(rec.config.get("s2_branch_floor", BRANCH_FLOOR))


def _b1(rec): return DIV if has_witness(rec) else NDO
def _b2(rec):
    if has_witness(rec): return DIV
    return INS if any(i.outcome == "QUARANTINED" or not i.deterministic for i in rec.inputs) else NDO
def _b3(rec): return rec.v7b_verdict or v7b_verdict(rec)   # historical recorded V7-B verdict
def _b4(rec, pf=default_profile):
    if has_witness(rec): return DIV
    f = pf(rec); return NDO if f["act_frac"] >= 1 - 1e-9 and f["branch_cov_min"] >= _floor(rec) else INS
def _b5(rec, pf=default_profile):
    v = _b1(rec)
    return v if v == DIV else (NDO if pf(rec)["act_frac"] >= 1 - 1e-9 else INS)


def _rule(fn, name, uses_profile=False):
    def factory(train_records=None, profile_fn=None, **kw):
        return Rule((lambda r: fn(r, profile_fn or default_profile)) if uses_profile else fn, name)
    return factory


def matched_abstention_risk(records, target_coverage, draws=1000, seed=0):
    """Baseline 6: among B1-issuable (non-witness) labelled pairs, abstain at random so that coverage (over all labelled pairs) equals
    target_coverage; mean selective risk over `draws` seeded draws. Random abstention cannot change risk beyond sampling noise."""
    lab = [r for r in records if r.y is not None]
    pool = np.array([r.y for r in lab if not has_witness(r)], float)
    k = int(round(target_coverage * len(lab)))
    if len(pool) < k or k == 0: return float("nan")
    rng = np.random.default_rng(seed)
    return float(np.mean([pool[rng.choice(len(pool), k, replace=False)].mean() for _ in range(draws)]))


class RandomAbstain:
    """Deterministic (seeded, per-pair hash) random abstainer for the registry; use matched_abstention_risk for the 1,000-draw estimate."""
    def __init__(self, target=0.3, seed=0, issue_rate=1.0): self.t = target / max(issue_rate, 1e-9); self.seed = seed
    def _u(self, rec):
        return np.random.default_rng([self.seed, int(rec.digest()[:8], 16)]).random()
    def decide(self, rec):
        if has_witness(rec): return DIV, 1.0
        return (NDO, 0.0) if self._u(rec) <= self.t else (INS, 1.0)
    def predict_risk(self, rec): return self.decide(rec)[1]


def _b6(train_records=None, target_coverage=0.3, seed=0, **kw):
    lab = [r for r in (train_records or []) if r.y is not None]
    rate = (sum(not has_witness(r) for r in lab) / len(lab)) if lab else 1.0
    return RandomAbstain(target_coverage, seed, rate)


def model_factory(names, with_ers=False, alphas=(0.10, 0.15)):
    def factory(train_records, profile_fn=None, extra_features_fn=None, extra_names=None, seed=0, B=1000, **kw):
        if with_ers and (extra_features_fn is None or not extra_names):
            raise ValueError("full CEC needs ERS response features (extra_features_fn + extra_names)")
        ek = dict(extra_features_fn=extra_features_fn, extra_names=extra_names) if with_ers else {}
        return calibrate.fit_select(train_records, names, alphas=alphas, seed=seed, B=B, profile_fn=profile_fn, **ek)
    return factory


MODEL_SPECS = {   # name -> (feature names, with_ers, description)
    "b7_cov_calibration": (schema.FEATURE_SETS["cov_only"], False),
    "b8_full_cec": (schema.FEATURE_SETS["full_profile"], True),
    "b9_cec_no_ers": (schema.FEATURE_SETS["full_profile"], False),
    "abl_mult_only": (["mu_min"], False),
    **{f"abl_{k}": (v, False) for k, v in schema.FEATURE_SETS.items() if k not in ("cov_only", "cov_act")},
}

REGISTRY = {
    "b1_plain_dt": _rule(lambda r, pf=None: _b1(r), "b1"),
    "b2_b1_repetition": _rule(lambda r, pf=None: _b2(r), "b2"),
    "b3_v7b_gate": _rule(lambda r, pf=None: _b3(r), "b3"),
    "b4_cov_gate": _rule(_b4, "b4", True),
    "b5_cov_gated_b1": _rule(_b5, "b5", True),
    "b6_matched_abstention": _b6,
    **{n: model_factory(f, e) for n, (f, e) in MODEL_SPECS.items()},
}
RULE_NAMES = ("b1_plain_dt", "b2_b1_repetition", "b3_v7b_gate", "b4_cov_gate", "b5_cov_gated_b1")


def make(name, train_records, **kw):
    if name not in REGISTRY: raise KeyError(f"unknown baseline {name!r}; have {sorted(REGISTRY)}")
    return REGISTRY[name](train_records, **kw)


def cli_register(sub):
    p = sub.add_parser("baselines", help="list baselines or score them on a records file (no model fitting)")
    p.add_argument("--records", default=None)
    p.set_defaults(func=_cli)


def _cli(a):
    import json
    from .evaluate import load_records
    if not a.records:
        print("\n".join(sorted(REGISTRY))); return 0
    recs = load_records(a.records); out = {}
    for n in RULE_NAMES:
        pr = make(n, None); vs = [pr.decide(r)[0] for r in recs]
        iss = [r for r, v in zip(recs, vs) if v == NDO and r.y is not None]
        out[n] = {"coverage": sum(v == NDO for v in vs) / max(len(vs), 1), "n_issued_labelled": len(iss),
                  "risk": (sum(r.y for r in iss) / len(iss)) if iss else None}
    print(json.dumps(out, indent=1)); return 0
