"""Evidence Response Signature (ERS): response of ANY predictor to pre-declared evidence perturbations.
Delta_j = risk(E'_j) - risk(E). Predictor protocol: .predict_risk(rec) -> [0,1], .decide(rec) -> (verdict, risk).
ERS is evidence-perturbation response only: no causal claim about programs. Never reads rec.y / rec.meta."""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from sbgv8 import perturb
from sbgv8.profile import build_profile, v7b_style_decision
from sbgv8.schema import PERTURBATIONS, EvidenceRecord

NDO, DIV, INS = "NO_DIVERGENCE_OBSERVED", "DIVERGENT_OBSERVABLE", "INSUFFICIENT"
EPS = 1e-6
TOL = {"P1": EPS, "P1b": EPS, "P2": 0.02, "P3": 0.02, "P4": EPS, "P5": EPS, "P6": 0.0, "P7": EPS, "P8": 0.0, "P9": EPS}
_MONO = ("P1", "P1b", "P4", "P5", "P7", "P9")


@dataclass
class ERS:
    pid: str
    params: dict
    applicable: bool
    orig_profile: dict
    pert_profile: dict
    orig_risk: float
    pert_risk: float
    orig_decision: str
    pert_decision: str
    coverage_before: dict
    coverage_after: dict
    provenance_status: dict       # prov_ok before/after
    integrity_status: dict        # integrity_ok before/after
    expected: str
    observed: str
    passed: object                # True / False / None (not applicable)
    tolerance: float
    delta: float
    reason: str = ""
    perturbation: dict = field(default_factory=dict)


def _eval(pid, d, v0, v1, p0, p1, tol):
    if pid in _MONO:
        if v0 == DIV: return None, "original already divergent; assurance risk not defined"
        ok = d >= -tol or v1 == INS
        return ok, f"delta={d:+.4g} verdict {v0}->{v1}"
    if pid in ("P2", "P3"):
        return abs(d) <= tol and v0 == v1, f"|delta|={abs(d):.4g} verdict {v0}->{v1}"
    if pid == "P6":
        return v1 == DIV or d > 0 or v1 == INS, f"delta={d:+.4g} verdict {v0}->{v1}"
    return (p1["integrity_ok"] == 0.0 and v1 == INS), f"integrity_ok={p1['integrity_ok']} verdict {v0}->{v1}"  # P8


def compute_ers(rec, predictor, pid, seed=0, **params):
    r2, pr = perturb.apply(rec, pid, seed=seed, **params)
    p0, p1 = build_profile(rec), build_profile(r2)
    r0, r1 = predictor.predict_risk(rec), predictor.predict_risk(r2)
    v0, v1 = predictor.decide(rec)[0], predictor.decide(r2)[0]
    tol, d = TOL[pid], r1 - r0
    ok, why = (None, pr.reason) if not pr.applicable else _eval(pid, d, v0, v1, p0, p1, tol)
    if pid == "P8" and pr.applicable is False: ok = None
    cov = lambda p: {k: p[k] for k in ("act_frac", "branch_cov_min", "chan_complete")}
    return ERS(pid, pr.params, pr.applicable, p0, p1, r0, r1, v0, v1, cov(p0), cov(p1), {"before": p0["prov_ok"], "after": p1["prov_ok"]},
               {"before": p0["integrity_ok"], "after": p1["integrity_ok"]}, (perturb.PERTURBATION_MATRIX.get(pid) or perturb.PERTURBATION_VARIANTS[pid])["expected"], why, ok, tol,
               d if pr.applicable else 0.0, "" if ok is not None else why, pr.to_dict())


def ers_vector(rec, predictor, pids=PERTURBATIONS, seed=0):
    """{ers_<pid>_delta: risk delta}; 0.0 where the perturbation is not applicable (documented convention)."""
    return {f"ers_{p}_delta": compute_ers(rec, predictor, p, seed=seed).delta for p in pids}


def run_matrix(records, predictor, pids=PERTURBATIONS, seed=0):
    counts, fails = {p: {"pass": 0, "fail": 0, "na": 0} for p in pids}, []
    for rec in records:
        for p in pids:
            e = compute_ers(rec, predictor, p, seed=seed)
            k = "na" if e.passed is None else "pass" if e.passed else "fail"
            counts[p][k] += 1
            if k == "fail": fails.append((rec.pair_id, p))
    md = ["| Perturbation | Name | Mode | Pass | Fail | N/A |", "|---|---|---|---|---|---|"]
    for p in pids:
        M, c = perturb.PERTURBATION_MATRIX.get(p) or perturb.PERTURBATION_VARIANTS[p], counts[p]
        mode = "post-hoc (synthetic recorded input; real execution needs collector)" if p in ("P2", "P6", "P5") else "post-hoc"
        md.append(f"| {p} | {M['name']} | {mode} | {c['pass']} | {c['fail']} | {c['na']} |")
    return {"counts": counts, "failures": fails, "n_records": len(records), "markdown": "\n".join(md)}


class ActivationStubPredictor:
    """Simple deterministic stub: risk = 1 - act_frac; decision from the V7-B-style rules. For tests and CLI smoke only."""
    def predict_risk(self, rec): return 1.0 - build_profile(rec)["act_frac"]
    def decide(self, rec):
        # V8 trust gate (same rule as calibrate.Model.decide): unverified evidence is never authoritative, witnessed DIVERGENT included.
        # v7b_style_decision itself stays a faithful replica of V7-B (witness precedence over the tamper flag).
        if not rec.integrity_ok: return "INSUFFICIENT", 1.0
        return v7b_style_decision(rec)[0], self.predict_risk(rec)


def _load(path):
    return [EvidenceRecord.from_json(l) for l in open(path) if l.strip()]


def cli_register(sub):
    e = sub.add_parser("ers", help="run the ERS perturbation matrix (stub predictor; development data only)")
    e.add_argument("records"); e.add_argument("--seed", type=int, default=0)
    e.set_defaults(func=lambda a: print(run_matrix(_load(a.records), ActivationStubPredictor(), seed=a.seed)["markdown"]))
    p = sub.add_parser("perturb", help="apply one perturbation to one record, print the PerturbationRecord")
    p.add_argument("records"); p.add_argument("pid", choices=PERTURBATIONS); p.add_argument("--index", type=int, default=0)
    p.add_argument("--seed", type=int, default=0)
    p.set_defaults(func=lambda a: print(json.dumps(perturb.apply(_load(a.records)[a.index], a.pid, seed=a.seed)[1].to_dict(), indent=1)))
