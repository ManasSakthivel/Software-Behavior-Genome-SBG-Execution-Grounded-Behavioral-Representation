"""Print compact markdown tables from out/*.csv (used to fill the report)."""
import csv, os
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
def rd(f): return list(csv.DictReader(open(os.path.join(O, f))))
def fl(x): return float(x)
def pick(rows, **kw): return [r for r in rows if all(abs(fl(r[k]) - v) < 1e-6 if k not in ("design",) else r[k] == v for k, v in kw.items())]
def pct(x): return "" if x == "" else f"{100*fl(x):.0f}"
g = rd("headline_power_grid.csv")
print("## A power(%), p0=.6 rho=.15 m=4; cols delta 3/5/10 ; a=.05 | a=.0167")
for pi in (.1, .2, .3):
    for K in (20, 30, 40, 50, 60, 80):
        r = {fl(x["delta"]): x for x in pick(g, K=K, m=4, rho=.15, p0=.6, pi=pi)}
        print(f"pi={pi} K={K} pairs~{K*4}: " + " ".join(f"d{int(d*100)}:{pct(r[d]['power_a05'])}|{pct(r[d]['power_a0167'])}" for d in (.03, .05, .1) if d in r))
print("## B p0 sensitivity K=40 m=4 rho=.15 pi=.2")
for p0 in (.4, .6, .8):
    r = {fl(x["delta"]): x for x in pick(g, K=40, m=4, rho=.15, p0=p0, pi=.2)}
    print(p0, {d: pct(r[d]['power_a05']) for d in r})
print("## C rho sensitivity K=40 m=4 p0=.6 pi=.2")
for rho in (.05, .15, .3):
    r = {fl(x["delta"]): x for x in pick(g, K=40, m=4, rho=rho, p0=.6, pi=.2)}
    print(rho, {d: pct(r[d]['power_a05']) for d in r})
print("## D MDE (pp) a=.05 | a=.0167 ; p0=.6 ; m=4")
M = rd("headline_mde.csv")
for pi in (.1, .2, .3):
    for rho in (.05, .15, .3):
        print(f"pi={pi} rho={rho}: " + " ".join(f"K{K}:{(fl(r['MDE_a05'])*100 if r['MDE_a05'] else float('nan')):.1f}|{(fl(r['MDE_a0167'])*100 if r['MDE_a0167'] else float('nan')):.1f}" for K in (20,30,40,60,80,120) for r in pick(M, K=K, m=4, rho=rho, pi=pi)))
print("## D2 MDE m=2 and m=8 at pi=.2 rho=.15")
for m in (2, 8):
    print(m, " ".join(f"K{K}:{(fl(r['MDE_a05'])*100 if r['MDE_a05'] else float('nan')):.1f}" for K in (20,30,40,60,80,120) for r in pick(M, K=K, m=m, rho=.15, pi=.2)))
print("## NI"); 
for r in rd("noninferiority_power.csv"):
    if r["rho"] == "0.1500": print(r["K"], r["pi"], r["true_delta"], r["approx_pairs"], pct(r["power_ni_2pp"]))
print("## noise")
for r in rd("label_noise_power.csv"): print(r)
print("## lineage")
for r in rd("lineage_duplicates_power.csv"): print(r)
print("## H7")
H = rd("h7_hard_stratum_power.csv")
for des in dict.fromkeys(r["design"] for r in H):
    for p0 in (.3,):
        for pi in (.2, .3):
            for rho in (.15,):
                r = {fl(x["delta"]): x for x in H if x["design"] == des and fl(x["p0_hard"]) == p0 and abs(fl(x["pi"]) - pi) < 1e-6 and abs(fl(x["rho"]) - rho) < 1e-6}
                print(des, f"p0={p0} pi={pi} rho={rho} hard_pairs~{r[.03]['hard_pairs']}:", {d: pct(r[d]['power_a05_est_ge_3pp']) for d in r})
print("## H8a")
for r in rd("h8a_annotation_power.csv"):
    if r["K"] == "40" and r["rho"] == "0.1500": print(r["prevalence_io"], r["n_io"], r["true_annot_given_fire"], "point", pct(r["power_point_ge_70"]), "lcb", pct(r["power_lcb95_ge_70"]), "nfire", r["mean_n_fire"])
print("## H8a required"); print(open(os.path.join(O, "h8a_required_n_io.csv")).read())
print("## H8b")
for r in rd("h8b_false_alarm_power.csv"): print(r["n_io"], r["K"], r["true_false_alarm"], r["label_contamination"], pct(r["power_ucb95_le_1pct"]))
