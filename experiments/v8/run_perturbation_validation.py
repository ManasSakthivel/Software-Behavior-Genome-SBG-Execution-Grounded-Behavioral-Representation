"""Post-hoc ERS/perturbation validation on the DEVELOPMENT records (macOS, no engine runs). DEVELOPMENT / EXPLORATORY.
Predictors: stub (1-act_frac), model (calibrate.fit full_profile), model_dense (same, lambda=0.01: sensitivity, fewer zero coefficients),
b3 (V7-B fixed gate = RECORDED v7b_verdict; ignores the perturbed evidence by construction), b3_live (V7-B decide recomputed on the perturbed record).
tau for the two models is a declared DIAGNOSTIC (30th percentile of in-sample risk over eligible records) only so that NDO exists to be lost;
it is not a deployment threshold. N/A is never counted as pass: pass rate = pass / (pass+fail) over APPLICABLE cases.
Usage: .venv/bin/python experiments/v8/run_perturbation_validation.py [OUT_DIR=results/v8_mac_perturb]"""
import collections, hashlib, json, os, subprocess, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT)
from sbgv8 import baselines, calibrate, ers, perturb, schema
from sbgv8.profile import v7b_style_decision
from sbgv8.schema import EvidenceRecord, PERTURBATIONS

PIDS = list(PERTURBATIONS[:1]) + ["P1b"] + list(PERTURBATIONS[1:])
DATA = os.path.join(ROOT, "datasets/v8/dev_records.jsonl")


class B3Live:
    """V7-B gate recomputed from the (perturbed) record: NDO issued -> risk 0, otherwise 1 (same pseudo-risk convention as the baselines)."""
    def decide(self, r):
        v = v7b_style_decision(r)[0]; return v, 0.0 if v == "NO_DIVERGENCE_OBSERVED" else 1.0
    def predict_risk(self, r): return self.decide(r)[1]


def with_tau(m, recs, q=0.30):
    rs = [m.predict_risk(r) for r in recs if calibrate.is_eligible(r)]
    m.tau = float(np.quantile(rs, q)); return m


def probe_all_features(recs):
    """NOT fitted: calibrate.Model reading EVERY profile feature with its pre-declared sign (|std coef| = 0.4). Exists because the fitted models
    keep only mu_min, which makes invariance/monotonicity checks on the other features vacuous (delta exactly 0). Diagnostic, never a result."""
    names = list(schema.FEATURES); X = calibrate._design(recs, names, None, None)
    return calibrate.Model(names, [], [0.4 * (calibrate.RISK_SIGN[n] or 1) for n in names], 0.0, X.mean(0), np.where(X.std(0) < 1e-12, 1.0, X.std(0)), 0.0)


def predictors(recs):
    return {"stub": ers.ActivationStubPredictor(), "model": with_tau(calibrate.fit(recs, schema.FEATURE_SETS["full_profile"]), recs),
            "model_dense": with_tau(calibrate.fit(recs, schema.FEATURE_SETS["full_profile"], lam=0.01), recs),
            "probe_all_features": with_tau(probe_all_features(recs), recs),
            "b3": baselines.make("b3_v7b_gate", None), "b3_live": B3Live()}


def strict_pass(e):
    """Pass with NO credit for abstaining (INSUFFICIENT) where the declared rule gives credit: isolates passes that rest on risk behaviour."""
    if e.pid in ("P1", "P1b", "P4", "P5", "P7", "P9"): return e.delta >= -e.tolerance
    if e.pid == "P6": return e.pert_decision == "DIVERGENT_OBSERVABLE" or e.delta > 0
    return e.passed


def run(recs, preds, seed=0):
    rows, summ = [], {}
    for pn, P in preds.items():
        for pid in PIDS:
            c = collections.Counter(); reasons = collections.Counter(); dl = []
            for r in recs:
                e = ers.compute_ers(r, P, pid, seed=seed)
                st = "na" if e.passed is None else "pass" if e.passed else "fail"
                if st == "na": reasons["not_applicable: " + e.reason if not e.applicable else "assurance_undefined_orig_DIVERGENT"] += 1
                else:
                    c["responded"] += abs(e.delta) > e.tolerance if pid not in ("P8",) else 0
                    c["strict_pass"] += bool(strict_pass(e)); c["abstention_credit"] += bool(e.passed) and not strict_pass(e); dl.append(e.delta)
                c[st] += 1
                rows.append(dict(predictor=pn, pid=pid, pair_id=r.pair_id, arm=r.meta.get("arm"), status=st, applicable=e.applicable, expected=e.expected,
                                 observed=e.observed, orig_verdict=e.orig_decision, pert_verdict=e.pert_decision, orig_risk=round(e.orig_risk, 6),
                                 pert_risk=round(e.pert_risk, 6), delta=round(e.delta, 6), reason=e.reason, mode="post_hoc_recorded_evidence"))
            n = c["pass"] + c["fail"]
            summ[f"{pn}|{pid}"] = dict(predictor=pn, pid=pid, applicable=n, passed=c["pass"], failed=c["fail"], na=c["na"], total=len(recs),
                                       pass_rate=c["pass"] / n if n else None, strict_pass=c["strict_pass"], abstention_credited_passes=c["abstention_credit"],
                                       responded_beyond_tol=c["responded"], delta_min=min(dl) if dl else None, delta_max=max(dl) if dl else None,
                                       na_reasons=dict(reasons))
    return rows, summ


def md(summ, recs):
    L = [f"Records: {len(recs)}. pass rate = pass/(pass+fail) over APPLICABLE cases; N/A is excluded from numerator and denominator and listed separately.", ""]
    for pn in dict.fromkeys(s["predictor"] for s in summ.values()):
        L += [f"### Predictor `{pn}`", "", "| P | class | applicable (denominator) | pass | fail | N/A | pass rate | passes resting on abstention credit | responded beyond tol | delta min..max |", "|---|---|---|---|---|---|---|---|---|---|"]
        for pid in PIDS:
            s = summ[f"{pn}|{pid}"]; M = perturb.PERTURBATION_MATRIX.get(pid) or perturb.PERTURBATION_VARIANTS[pid]
            pr = "n/a" if s["pass_rate"] is None else f"{s['pass_rate']:.3f}"
            dm = "-" if s["delta_min"] is None else f"{s['delta_min']:+.3g}..{s['delta_max']:+.3g}"
            L.append(f"| {pid} | {M['evidence_class']['posthoc']} | {s['applicable']} | {s['passed']} | {s['failed']} | {s['na']} | {pr} | {s['abstention_credited_passes']} | {s['responded_beyond_tol']} | {dm} |")
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results/v8_mac_perturb"); os.makedirs(out, exist_ok=True)
    recs = [EvidenceRecord.from_json(l) for l in open(DATA) if l.strip()]
    preds = predictors(recs); rows, summ = run(recs, preds)
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    meta = dict(script="experiments/v8/run_perturbation_validation.py", command=" ".join(["python"] + sys.argv), seed=0, records=DATA, records_sha256=hashlib.sha256(open(DATA, "rb").read()).hexdigest(),
                git_head=git("rev-parse", "HEAD"), git_dirty=bool(git("status", "--porcelain", "--", "sbgv8", "experiments/v8")), n_records=len(recs),
                tau={k: getattr(p, "tau", None) for k, p in preds.items()}, model_nonzero_coef={k: [c["feature"] for c in p.coef_report()["coefficients"] if abs(c["std_coef"]) > 1e-9] for k, p in preds.items() if hasattr(p, "coef_report")})
    json.dump(dict(meta=meta, summary=summ), open(os.path.join(out, "posthoc_matrix.json"), "w"), indent=1, default=str)
    with open(os.path.join(out, "posthoc_per_record.jsonl"), "w") as f:
        for r in rows: f.write(json.dumps(r, default=str) + "\n")
    open(os.path.join(out, "posthoc_matrix.md"), "w").write(md(summ, recs))
    print(md(summ, recs)); print(json.dumps(meta["model_nonzero_coef"]), meta["tau"])
