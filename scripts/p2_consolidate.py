#!/usr/bin/env python
"""Phase 2 consolidation (pre-registered in reports/phase2/E3_E7_PROTOCOLS.md). READ-ONLY on every input; writes only into a NEW --out DIR.
  p2_consolidate.py build --out DIR [--e1 DIR] [--e3 DIR] [--e4 DIR] [--e5 DIR] [--e6 DIR] [--e7 DIR] [--postfix results/postfix]
  p2_consolidate.py consistency --a FILE.jsonl --b FILE.jsonl [--strict]     (k1_spike_per_pair.jsonl files, tag run1; prints JSON)
Layouts: E1 DIR/proc/k1_spike_per_pair.jsonl; E3 DIR/processed/{k1_spike_per_pair.jsonl,baselines_per_pair*.jsonl,dev_pairs_per_system.csv},
DIR/statistics/*.json; E4/E5 DIR/<VARIANT>/proc/k1_spike_per_pair.jsonl and DIR/statistics*/ (analyze_results outputs, any depth); E6 DIR/*.json;
E7 DIR/{verify_table,corruption_results}.json. Emits DIR/consolidated.json and DIR/tables.md. Missing inputs are listed, never invented.
Derived (NOT executed) sufficiency-gate counterfactual: INSUFFICIENT verdicts are re-labelled NO_DIVERGENCE_OBSERVED (G_A: all reasons;
G_B: only reasons attributable to the sufficiency gate, GATE_REASONS). -h exits 0 before any work; bad usage exits 2."""
import argparse, collections, csv, glob, json, os, random, sys

POS = "DIV"
GATE_REASONS = {"changed_region_not_activated", "budget_exhausted_s0", "blind_spot_dominant", "unobservable_outcome"}  # fixed in the protocol
STRICT = ("verdict", "level", "primary", "secondary", "witness_id")
LOOSE = ("verdict", "level", "primary")
BOOT, SEED = 10000, 42


def jl(p): return [json.loads(l) for l in open(p)]
def run1(p): return {(r["arm"], r["pair"]): r for r in jl(p) if r["tag"] == "run1"}
def js(p): return json.load(open(p))
def kf(r, fields): return tuple(json.dumps(r.get(f), sort_keys=True) for f in fields)


def consistency(A, B, strict):
    f = STRICT if strict else LOOSE
    common = sorted(set(A) & set(B)); diffs = [(k, [A[k].get(x) for x in LOOSE], [B[k].get(x) for x in LOOSE]) for k in common if kf(A[k], f) != kf(B[k], f)]
    return dict(fields=f, n_a=len(A), n_b=len(B), n_common=len(common), identical=len(common) - len(diffs), n_diff=len(diffs),
                verdict_only_diff=sum(A[k]["verdict"] != B[k]["verdict"] for k in common),
                verdict_matrix={f"{a}|{b}": n for (a, b), n in sorted(collections.Counter((A[k]["verdict"], B[k]["verdict"]) for k in common).items())},
                diffs=[dict(pair=list(k), a=x, b=y) for k, x, y in diffs[:200]], only_a=[list(k) for k in sorted(set(A) - set(B))][:50], only_b=[list(k) for k in sorted(set(B) - set(A))][:50])


def mcnemar_exact(b, c):
    from scipy import stats
    return 1.0 if b + c == 0 else float(stats.binomtest(min(b, c), b + c, 0.5).pvalue)


def quarantined(r): return int(bool(r.get("quarantined")) or "nondeterministic" in [r.get("primary")] + list(r.get("secondary") or []))


def e1(d, postfix):
    rows = jl(os.path.join(d, "proc", "k1_spike_per_pair.jsonl")); r1 = {(r["arm"], r["pair"]): r for r in rows if r["tag"] == "run1"}
    r2 = {(r["arm"], r["pair"]): r for r in rows if r["tag"] == "run2"}
    out = dict(verdicts_by_arm={a: dict(collections.Counter(r["verdict"] for k, r in r1.items() if k[0] == a)) for a in sorted({k[0] for k in r1})},
               run1_vs_run2=consistency({k: r1[k] for k in r2 if k in r1}, r2, True))
    out["quarantined_rate_new"] = round(sum(map(quarantined, r1.values())) / max(1, len(r1)), 4)
    if postfix and os.path.exists(os.path.join(postfix, "processed/k1_spike_per_pair.jsonl")):
        old = run1(os.path.join(postfix, "processed/k1_spike_per_pair.jsonl")); com = sorted(set(old) & set(r1))
        b = sum(quarantined(r1[k]) and not quarantined(old[k]) for k in com); c = sum(quarantined(old[k]) and not quarantined(r1[k]) for k in com)
        out["old_vs_new"] = dict(n_common=len(com), quarantined_old=sum(quarantined(old[k]) for k in com), quarantined_new=sum(quarantined(r1[k]) for k in com),
                                 new_only=b, old_only=c, p_mcnemar_exact=mcnemar_exact(b, c), consistency_loose=consistency(old, r1, False))
    return out


def truth_map(e3):
    return {r["pair_id"]: r for r in csv.DictReader(open(os.path.join(e3, "processed/dev_pairs_per_system.csv"))) if r["system"] == "V7-B"}


def boot_share(items, proj):
    """items: list of (project, num, den). Percentile CI of sum(num)/sum(den), project-cluster resampling."""
    g = collections.defaultdict(lambda: [0, 0])
    for p, n, d in items: g[p][0] += n; g[p][1] += d
    ps = sorted(g); rng = random.Random(SEED); r = []
    for _ in range(BOOT):
        s = [g[rng.choice(ps)] for _ in ps]; den = sum(x[1] for x in s)
        if den: r.append(sum(x[0] for x in s) / den)
    r.sort(); tot = sum(x[1] for x in g.values())
    return dict(est=sum(x[0] for x in g.values()) / tot if tot else None, lo=r[int(.025 * len(r))] if r else None, hi=r[int(.975 * len(r))] if r else None, n=tot, K=len(ps))


def gate_counterfactual(k1rows, tr, label):
    """Derived from recorded V7-B verdicts; no engine run. Primary-eligible pairs only (truth DIV / NO_OBS_DIFF)."""
    el = [(k, r, tr[f"{k[0]}:{k[1]}"]["truth"]) for k, r in k1rows.items() if f"{k[0]}:{k[1]}" in tr and tr[f"{k[0]}:{k[1]}"]["truth"] in ("DIV", "NO_OBS_DIFF")]
    out = {"label": label, "DERIVED_NOT_EXECUTED": True, "n_eligible": len(el)}
    for name, conv in (("actual", set()), ("G_A_all_insufficient_to_NDO", None), ("G_B_gate_reasons_only_to_NDO", GATE_REASONS)):
        def v(r):
            if r["verdict"] != "INSUFFICIENT" or name == "actual": return r["verdict"]
            return "NO_DIVERGENCE_OBSERVED" if conv is None or r.get("primary") in conv else "INSUFFICIENT"
        dv = [(k, r, v(r)) for k, r, t in el if t == "DIV"]; no = [(k, r, v(r)) for k, r, t in el if t == "NO_OBS_DIFF"]
        allv = [x for _, _, x in dv + no]; dec = [x for x in allv if x in ("DIVERGENT_OBSERVABLE", "NO_DIVERGENCE_OBSERVED")]
        fa = sum(x == "NO_DIVERGENCE_OBSERVED" for _, _, x in dv)
        out[name] = dict(detection=sum(x == "DIVERGENT_OBSERVABLE" for _, _, x in dv), false_assurance=fa, n_div=len(dv), false_alarm=sum(x == "DIVERGENT_OBSERVABLE" for _, _, x in no),
                         n_nodiff=len(no), abstention=sum(x not in ("DIVERGENT_OBSERVABLE", "NO_DIVERGENCE_OBSERVED") for x in allv), n_decided=len(dec),
                         false_assurance_rate=round(fa / len(dv), 4) if dv else None, ndo_error_among_NDO_verdicts=round(fa / max(1, sum(x == "NO_DIVERGENCE_OBSERVED" for x in allv)), 4))
    return out


def attribution(k1rows, tr, e3):
    """Among DIV pairs where baseline B1 / B1+rep says NO_DIFF (a false assurance), what does V7-B say?  abstention share = INSUFFICIENT / (INSUFFICIENT + DIVERGENT)."""
    bl = {(r["arm"], r["pair"]): r for r in jl(os.path.join(e3, "processed/baselines_per_pair.jsonl"))}; res = {}
    for b in ("B1", "B1rep"):
        items, dist = [], collections.Counter()
        for k, r in k1rows.items():
            t = tr.get(f"{k[0]}:{k[1]}")
            x = bl.get(k, {}).get(b)
            if not t or t["truth"] != "DIV" or not isinstance(x, dict) or x.get("verdict") != "NO_DIFF": continue
            dist[r["verdict"]] += 1
            if r["verdict"] in ("INSUFFICIENT", "DIVERGENT_OBSERVABLE"): items.append((r["project"], int(r["verdict"] == "INSUFFICIENT"), 1))
        res[b] = dict(n_baseline_false_assurance=sum(dist.values()), v7b_verdicts=dict(dist), abstention_share_of_reduction=boot_share(items, None) if items else None)
    return res


def variant_summary(d):
    out = {}
    for p in sorted(glob.glob(os.path.join(d, "*", "proc", "k1_spike_per_pair.jsonl"))):
        name = p.split(os.sep)[-3]; r = run1(p)
        out[name] = dict(n=len(r), verdicts=dict(collections.Counter(x["verdict"] for x in r.values())),
                         levels=dict(collections.Counter(x.get("level") for x in r.values() if x["verdict"] == "NO_DIVERGENCE_OBSERVED")),
                         insufficient_reasons=dict(collections.Counter(x.get("primary") for x in r.values() if x["verdict"] == "INSUFFICIENT")),
                         cpu_s_sum=round(sum(x.get("cpu_s", 0) for x in r.values()), 1), _rows=r)
    return out


def flips(V, ref):
    out = {}
    for n, v in V.items():
        if n == ref: continue
        a, b = V[ref]["_rows"], v["_rows"]; cat = lambda r: (r["verdict"], r.get("level"))
        com = sorted(set(a) & set(b)); fl = [k for k in com if cat(a[k]) != cat(b[k])]
        out[n] = dict(vs=ref, n_common=len(com), flips_category=len(fl), flips_verdict=sum(a[k]["verdict"] != b[k]["verdict"] for k in com),
                      matrix=dict(collections.Counter(f"{cat(a[k])}->{cat(b[k])}" for k in fl)))
    return out


def md_table(rows, cols):
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows])


def cmd_build(a):
    out = os.path.abspath(a.out)
    if os.path.exists(out): sys.exit(f"error: {out} exists")
    C, missing, md = {}, [], ["# Phase 2 consolidated tables (generated; exploratory, non-pristine data)\n"]
    def need(name, d):
        if d and os.path.isdir(d): return True
        missing.append(name); return False
    if need("E1", a.e1): C["E1"] = e1(a.e1, a.postfix); md.append(f"## E1\nrun1 vs run2 identical: {C['E1']['run1_vs_run2']['identical']}/{C['E1']['run1_vs_run2']['n_common']}\n")
    k3 = None
    if need("E3", a.e3):
        e3 = a.e3; k3 = run1(os.path.join(e3, "processed/k1_spike_per_pair.jsonl")); tr = truth_map(e3)
        C["E3"] = dict(system_metrics=js(os.path.join(e3, "statistics/system_metrics.json")), paired=js(os.path.join(e3, "statistics/paired_comparisons.json")),
                       summary=js(os.path.join(e3, "statistics/summary.json")), consistency_vs_postfix_loose=None, consistency_vs_e1_strict=None)
        if a.postfix and os.path.exists(os.path.join(a.postfix, "processed/k1_spike_per_pair.jsonl")):
            C["E3"]["consistency_vs_postfix_loose"] = consistency(run1(os.path.join(a.postfix, "processed/k1_spike_per_pair.jsonl")), k3, False)
        if a.e1 and os.path.isdir(a.e1): C["E3"]["consistency_vs_e1_strict"] = consistency(run1(os.path.join(a.e1, "proc/k1_spike_per_pair.jsonl")), k3, True)
        C["gate_counterfactual_E3"] = gate_counterfactual(k3, tr, "E3 V7-B verdicts"); C["abstention_attribution_E3"] = attribution(k3, tr, e3)
        md.append("## E3 system metrics\n" + md_table([dict(system=r["system"], outcome=r["outcome"], est=r["est"], lo=r["lo"], hi=r["hi"], n=r["n"], K=r["K"]) for r in C["E3"]["system_metrics"]], ["system", "outcome", "est", "lo", "hi", "n", "K"]) + "\n")
        md.append("## Derived gate counterfactual (NOT executed)\n" + md_table([dict(variant=k, **v) for k, v in C["gate_counterfactual_E3"].items() if isinstance(v, dict)], ["variant", "detection", "false_assurance", "n_div", "false_alarm", "abstention", "false_assurance_rate"]) + "\n")
    for name, d, ref in (("E4", a.e4, "V0"), ("E5", a.e5, "S2F08")):
        if need(name, d):
            V = variant_summary(d); stats = {os.path.relpath(p, d): js(p) for p in glob.glob(os.path.join(d, "statistics*", "**", "paired_comparisons.json"), recursive=True)}
            C[name] = dict(variants={n: {k: x for k, x in v.items() if k != "_rows"} for n, v in V.items()}, flips=flips(V, ref) if ref in V else "reference variant missing", statistics=stats)
            if name == "E4" and a.e3 and ref in V and k3 is not None: C["gate_counterfactual_E4_V0"] = gate_counterfactual(V[ref]["_rows"], truth_map(a.e3), "E4 V0 verdicts")
            md.append(f"## {name} variants\n" + md_table([dict(variant=n, **{k: v[k] for k in ("n", "verdicts", "levels")}) for n, v in C[name]["variants"].items()], ["variant", "n", "verdicts", "levels"]) + "\n")
    if need("E6", a.e6): C["E6"] = {os.path.basename(p): js(p) for p in glob.glob(os.path.join(a.e6, "**", "*.json"), recursive=True) if "/tasks/" not in p and "/work/" not in p and "timing_raw" not in p}
    if need("E7", a.e7):
        C["E7"] = {n: js(os.path.join(a.e7, n + ".json")) for n in ("verify_table", "corruption_results") if os.path.exists(os.path.join(a.e7, n + ".json"))}
        cr = C["E7"].get("corruption_results", []); md.append(f"## E7 corruption suite\n{sum(r['as_expected'] for r in cr)}/{len(cr)} as expected\n" + md_table([r for r in cr if not r["as_expected"]], ["source_class", "case", "expected", "observed"]) + "\n")
    C["missing_inputs"] = missing
    os.makedirs(out); json.dump(C, open(os.path.join(out, "consolidated.json"), "w"), indent=1, default=str); open(os.path.join(out, "tables.md"), "w").write("\n".join(md))
    print("wrote", out, "missing:", missing)


def parser():
    ap = argparse.ArgumentParser(prog="p2_consolidate.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build"); b.add_argument("--out", required=True); b.add_argument("--postfix", default="results/postfix")
    for e in ("e1", "e3", "e4", "e5", "e6", "e7"): b.add_argument("--" + e, default=None)
    c = sp.add_parser("consistency"); c.add_argument("--a", required=True); c.add_argument("--b", required=True); c.add_argument("--strict", action="store_true")
    return ap


if __name__ == "__main__":
    a = parser().parse_args()
    if a.cmd == "build": cmd_build(a)
    else: print(json.dumps(consistency(run1(a.a), run1(a.b), a.strict), indent=1))
