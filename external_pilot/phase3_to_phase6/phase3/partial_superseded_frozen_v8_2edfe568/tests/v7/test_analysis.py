"""Known-answer, coverage and calibration tests for scripts/analyze_results.py and power_actual.py (synthetic data only)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import analyze_results as ar
import power_actual as pa


def test_holm_known():
    assert np.allclose(ar.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])


def test_mcnemar_exact_known():
    assert ar.mcnemar_exact(10, 2) == pytest.approx(158 / 4096)
    assert ar.mcnemar_exact(0, 0) == 1.0


def test_signflip_exact_known():
    # d=[1,1,1]: |sum|=3 reached by 2 of 8 sign patterns
    assert ar.sign_flip_p([1, 1, 1]) == pytest.approx(0.25)


def test_ratio_ci_point_estimate_and_seed():
    a = ar.ratio_ci([1, 2, 3], [4, 4, 4], 500, 7, "x")
    assert a["est"] == pytest.approx(0.5) and a["lo"] <= 0.5 <= a["hi"]
    assert a == ar.ratio_ci([1, 2, 3], [4, 4, 4], 500, 7, "x")  # reproducible with seed


def test_bootstrap_coverage_clustered():
    # true marginal rate p=.4, ICC=.15, 40 projects x 4 pairs; percentile CI should cover ~95%
    rng, p, rho, K, m, hit, reps = np.random.default_rng(1), 0.4, 0.15, 40, 4, 0, 300
    a = 1 / rho - 1
    for r in range(reps):
        pj = rng.beta(p * a, (1 - p) * a, K)
        num = rng.binomial(m, pj)
        ci = ar.ratio_ci(num, np.full(K, m), 1000, 100 + r, f"c{r}")
        hit += ci["lo"] <= p <= ci["hi"]
    assert 0.90 <= hit / reps <= 0.99, hit / reps


def _null_paired(rng, K=20, m=4):
    pj = rng.beta(1, 1, K)  # project-heterogeneous success prob, identical for both systems => null
    y1, y2 = rng.random((K, m)) < pj[:, None], rng.random((K, m)) < pj[:, None]
    return (y2.astype(int) - y1).sum(1), int((y2 & ~y1).sum()), int((y1 & ~y2).sum())


def test_null_calibration_signflip_and_mcnemar():
    rng, reps, rej_sf, rej_mc = np.random.default_rng(2), 400, 0, 0
    for _ in range(reps):
        d, b, c = _null_paired(rng)
        rej_sf += ar.sign_flip_p(d, 999, int(rng.integers(1e9))) < 0.05
    assert 0.02 <= rej_sf / reps <= 0.08, rej_sf / reps
    for _ in range(reps):  # independent pairs (no clustering): exact McNemar must not exceed alpha
        y1, y2 = rng.random(80) < 0.5, rng.random(80) < 0.5
        rej_mc += ar.mcnemar_exact(int((y2 & ~y1).sum()), int((y1 & ~y2).sum())) < 0.05
    assert rej_mc / reps <= 0.07


def test_signflip_detects_true_effect():
    d = np.array([2, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1], float)
    assert ar.sign_flip_p(d, 5000) < 0.001


def _fixture(tmp):
    rows = []
    # 2 projects, 10 DIV + 4 NO_OBS_DIFF + 2 UNACTIVATED(excluded). sysA detects all DIV; sysB detects 6, 3 FA, 1 abstain.
    for i in range(10):
        proj = "p1" if i < 5 else "p2"
        pid = f"d{i}"
        rows.append([proj, pid, "A", ar.DIV, "", "DIV", 1, 10])
        v = ar.DIV if i < 6 else (ar.NDO if i < 9 else "TIMEOUT")
        rows.append([proj, pid, "B", v, "S2" if v == ar.NDO else "", "DIV", 2, 20])
    for i in range(4):
        for s in "AB":
            rows.append(["p1" if i < 2 else "p2", f"n{i}", s, ar.NDO, "S1", "NO_OBS_DIFF", 1, 10])
    for i in range(2):
        for s in "AB":
            rows.append(["p1", f"u{i}", s, ar.INS, "", "UNACTIVATED", 1, 10])
    f = Path(tmp) / "pairs.csv"
    pd.DataFrame(rows, columns=ar.COLS).to_csv(f, index=False)
    return f


def test_end_to_end_known_counts(tmp_path):
    out = tmp_path / "stats"
    s = ar.run(_fixture(tmp_path), out, ref="B", seed=42, boot=500, n_perm=2000)
    assert s["excluded_from_primary_denominators"] == {"UNACTIVATED": 2}
    assert s["failed_or_missing_runs"] == 1
    sm = pd.read_csv(out / "system_metrics.csv").set_index(["system", "outcome"])
    assert sm.loc[("A", "detection"), "est"] == 1.0
    assert sm.loc[("B", "detection"), "est"] == 0.6 and sm.loc[("B", "false_assurance"), "est"] == 0.3
    assert sm.loc[("B", "abstention"), "est"] == pytest.approx(1 / 14)
    pc = pd.read_csv(out / "paired_comparisons.csv").set_index(["test", "outcome"])
    r = pc.loc[("A", "detection")]
    assert (r.b_test_only, r.c_ref_only, r["diff"]) == (4, 0, pytest.approx(0.4))
    assert r.p_mcnemar_exact_pairlevel == pytest.approx(2 * 0.5 ** 4)
    assert pc.loc[("A", "false_assurance"), "improvement"] == pytest.approx(0.3)
    rc = pd.read_csv(out / "risk_coverage.csv")
    b0 = rc[(rc.system == "B") & (rc.min_sufficiency_for_NDO == "none")].iloc[0]
    assert b0.decided == 13 and b0.risk == pytest.approx(3 / 13)       # 3 FA of 13 decided
    b3 = rc[(rc.system == "B") & (rc.min_sufficiency_for_NDO == "S3")].iloc[0]
    assert b3.decided == 6                                              # all NDO abstained at S3
    assert (out / "class_counts.csv").exists() and (out / "summary.json").exists()
    assert json.loads((out / "summary.json").read_text())["seed"] == 42


def test_missing_rows_are_failures(tmp_path):
    f = _fixture(tmp_path)
    df = pd.read_csv(f, dtype=str, keep_default_na=False)
    pd.concat([df, df.iloc[:0]])[~((df.system == "B") & (df.pair_id == "d0"))].to_csv(f, index=False)
    o = ar.outcome_frame(ar.load(f))
    r = o[(o.system == "B") & (o.pair_id == "d0")].iloc[0]
    assert r.verdict_n == "FAILED" and r.detection == 0 and r.abstention == 1


def test_icc_recovers_known():
    rng, K, m, rho = np.random.default_rng(3), 400, 5, 0.3
    u = rng.normal(0, np.sqrt(rho), K)
    y = (u[:, None] + rng.normal(0, np.sqrt(1 - rho), (K, m))).ravel()
    assert abs(ar.icc_anova(y, np.repeat(np.arange(K), m)) - rho) < 0.05


def test_power_script_null_and_monotone():
    sizes = np.full(40, 4)
    null = pa.simulate_power(sizes, 0.6, 0.2, 0.15, 0.0, 0.05, sims=800, flips=299)
    assert null <= 0.04                       # one-sided (positive-direction) type I, nominal .025
    p5, p10 = (pa.simulate_power(sizes, 0.6, 0.2, 0.15, d, 0.05, sims=500, flips=299) for d in (0.05, 0.10))
    assert p10 > p5 and 0.4 <= p10 <= 0.8     # P0 table: ~58-63% at K=40, m=4
    assert pa.simulate_power(sizes, 0.6, 0.1, 0.15, 0.2, 0.05) is None   # delta > pi infeasible
