"""Design-time sample-size arithmetic for the V8 calibration study (no experimental data; assumptions are inputs).
Stdlib only. Run: python3 sample_size_calc.py
Quantities: issued NDO verdicts needed for a given CI half-width on the false-assurance risk, inflated by a cluster design effect
DEFF = 1 + (m-1)*rho (m = mean issued-NDO per project, rho = intra-project correlation of the error indicator), and the
total pairs implied by an NDO-issuance rate."""
import math

def wilson_hw(p, n, z=1.96):
    d = 1 + z * z / n
    return z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d

def n_for_hw(p, hw):
    n = 10
    while wilson_hw(p, n) > hw: n += 1
    return n

print("risk p | half-width | issued NDO needed (iid) | with DEFF (m=3,rho=0.15) | with DEFF (m=5,rho=0.3)")
for p in (0.05, 0.10, 0.20):
    for hw in (0.03, 0.05, 0.07):
        n = n_for_hw(p, hw)
        print(f"{p:.2f} | {hw:.2f} | {n} | {math.ceil(n*(1+2*0.15))} | {math.ceil(n*(1+4*0.3))}")

print("\nCoverage (NDO issuance rate c) -> total adjudicated pairs needed for N issued NDO verdicts")
for c in (0.2, 0.25, 0.4):
    for N in (150, 250, 400):
        print(f"c={c:.2f}  N_issued={N}: total pairs ~ {math.ceil(N/c)}")

print("\nPaired difference in selective risk at matched coverage (two systems issue NDO on the same K pairs; discordant error share d):")
print("approximate K needed to detect risk difference delta with 80% power, alpha 0.05 (McNemar normal approx, discordant proportion q of K)")
for delta in (0.05, 0.08, 0.10):
    for q in (0.10, 0.20):
        # H1: p10-p01 = delta, discordant total q: n = ((1.96*sqrt(q)+0.84*sqrt(q-delta^2))/delta)^2
        n = ((1.96 * math.sqrt(q) + 0.8416 * math.sqrt(q - delta * delta)) / delta) ** 2
        print(f"delta={delta:.2f} q={q:.2f}: K ~ {math.ceil(n)} matched issued pairs (x DEFF 1.45 for clustering ~ {math.ceil(n*1.45)})")

print("\nExact one-sided upper bound when 0 false assurances observed in N issued (rule of three, iid): 3/N")
for N in (60, 100, 150, 250): print(f"N={N}: ~{3/N:.3f}")
print("\nPhase 2 dev observed (not a design input): V7-B 13/61 wrong among issued NDO; B1 24/130.")
