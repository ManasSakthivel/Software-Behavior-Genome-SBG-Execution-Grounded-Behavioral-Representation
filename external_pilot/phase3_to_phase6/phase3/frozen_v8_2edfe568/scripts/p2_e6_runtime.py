#!/usr/bin/env python
"""Phase 2 E6 runtime/resource study (pre-registered in reports/phase2/E3_E7_PROTOCOLS.md).
  p2_e6_runtime.py records --src LABEL=DIR [LABEL=DIR ...] --out FILE.json
      Derive cost from existing run dirs (E3 / E4 variants): reads evidence.jsonl + verdict.json (+ k1_spike_per_pair.jsonl wall_s). Read-only on inputs.
      Only collected quantities are reported: Run-record meta cpu_s/wall_s, run counts by kind, verdict.json cpu_seconds_spent.
      Per-run peak RSS is NOT stored in evidence (isolation measures it but runner.py does not log it): it is not reported from E3/E4.
  p2_e6_runtime.py select --out FILE.json            print/write the fixed 40-pair subset (no engine run)
  p2_e6_runtime.py timing --out DIR [--reps 5]       sequential study, one process at a time: V0 vs B1 vs B1+rep on the subset; wait4 rusage gives
      tree CPU and peak RSS (max over the waited process tree, not additive). Refuses an existing non-empty DIR.
  Subset rule: runnable (non-skipped) k1_spike tasks sorted by (arm,pair); random.Random(20261118).sample per arm with quotas
  quixbugs 8, quixbugs_neg 8, synthetic 16, bugsinpy_units 8 (fewer if the arm has fewer runnable).
-h exits 0 before any work; bad usage exits 2."""
import argparse, collections, glob, importlib.util, json, os, platform, random, statistics, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUOTA = {"quixbugs": 8, "quixbugs_neg": 8, "synthetic": 16, "bugsinpy_units": 8}
SEED, BOOT = 20261118, 10000
SYSTEMS = ("V0", "B1", "B1rep")


def k1():
    s = importlib.util.spec_from_file_location("k1_spike", os.path.join(ROOT, "experiments/v7b/k1_spike.py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def q3(x):
    x = sorted(x)
    if len(x) < 2: return [x[0]] * 3 if x else [None] * 3
    return [round(v, 3) for v in statistics.quantiles(x, n=4, method="inclusive")]


def summ(x): q = q3(x); return dict(n=len(x), median=q[1], q1=q[0], q3=q[2], max=round(max(x), 3) if x else None, sum=round(sum(x), 3))


# ---------------------------------------------------------------- records (E3/E4 derived)
def cmd_records(a):
    if os.path.exists(a.out): sys.exit(f"error: {a.out} exists")
    res = {"note": "derived from evidence logs; concurrency 4 in E3/E4 so wall_s is load-inflated; peak RSS not collected in evidence"}
    for spec in a.src:
        label, d = spec.split("=", 1); rows = []
        walls = {}
        for jf in glob.glob(os.path.join(d, "**", "k1_spike_per_pair.jsonl"), recursive=True):
            for l in open(jf):
                r = json.loads(l)
                if r["tag"] == "run1": walls[(r["arm"], r["pair"])] = r.get("wall_s")
        for ev in sorted(glob.glob(os.path.join(d, "**", "evidence.jsonl"), recursive=True)):
            dd = os.path.dirname(ev)
            if "/baselines/" in dd or not os.path.exists(os.path.join(dd, "verdict.json")) or "/run1/" not in dd + "/": continue
            v = json.load(open(os.path.join(dd, "verdict.json"))); kinds = collections.Counter(); cpu = collections.Counter(); wall = collections.Counter()
            for l in open(ev):
                r = json.loads(l)["rec"]
                if r["kind"] == "Run":
                    k = r["body"]["run_kind"]; kinds[k] += 1; cpu[k] += r["meta"]["cpu_s"]; wall[k] += r["meta"]["wall_s"]
            arm, pair = dd.split("/run1/")[0].rsplit("/", 1)[1], os.path.basename(dd)
            rows.append(dict(arm=arm, pair=pair, verdict=v["verdict"], level=v["level"], primary=v["primary"], engine_cpu_s=v["cpu_seconds_spent"],
                             child_cpu_s=round(sum(cpu.values()), 3), child_wall_s=round(sum(wall.values()), 3), n_runs=sum(kinds.values()),
                             runs=dict(kinds), child_cpu_by_kind={k: round(x, 3) for k, x in cpu.items()}, process_wall_s=walls.get((arm, pair))))
        tot = collections.Counter()
        for r in rows:
            for k, x in r["child_cpu_by_kind"].items(): tot[k] += x
        s = sum(tot.values()) or 1
        res[label] = dict(n_pairs=len(rows), engine_cpu_s=summ([r["engine_cpu_s"] for r in rows]), child_cpu_s=summ([r["child_cpu_s"] for r in rows]),
                          n_runs=summ([r["n_runs"] for r in rows]), process_wall_s=summ([r["process_wall_s"] for r in rows if r["process_wall_s"] is not None]),
                          child_cpu_share_by_run_kind={k: round(x / s, 4) for k, x in sorted(tot.items())},
                          by_arm={arm: dict(n=len(g), engine_cpu_s=summ([r["engine_cpu_s"] for r in g])) for arm in sorted({r["arm"] for r in rows}) for g in [[r for r in rows if r["arm"] == arm]]},
                          by_verdict={v: dict(n=len(g), n_runs=summ([r["n_runs"] for r in g]), engine_cpu_s=summ([r["engine_cpu_s"] for r in g]))
                                      for v in sorted({r["verdict"] for r in rows}) for g in [[r for r in rows if r["verdict"] == v]]},
                          per_pair=rows)
        bf = glob.glob(os.path.join(d, "processed", "baselines_per_pair_final.jsonl"))
        if bf:
            bl = [json.loads(l) for l in open(bf[0])]
            res[label]["baseline_cpu_s"] = {b: summ([r[b]["cpu_s"] for r in bl if isinstance(r.get(b), dict) and "cpu_s" in r[b]]) for b in ("B1", "B1rep", "B2", "B3")}
    json.dump(res, open(a.out, "w"), indent=1); print("wrote", a.out)


# ---------------------------------------------------------------- subset + timing
def subset(K):
    q, allt = K.tasks_quixbugs(), {"quixbugs": K.tasks_quixbugs, "synthetic": K.tasks_synthetic, "bugsinpy_units": K.tasks_bugsinpy}
    rng, out = random.Random(SEED), []
    for arm, n in QUOTA.items():
        ts = sorted([t for t in (q if arm.startswith("quixbugs") else allt[arm]()) if t["arm"] == arm and "skip" not in t], key=lambda t: (t["arm"], t["pair"]))
        out += rng.sample(ts, min(n, len(ts)))
    return out


def cmd_select(a):
    t = subset(k1()); o = [{k: x[k] for k in ("arm", "pair", "project", "label")} for x in t]
    if a.out:
        if os.path.exists(a.out): sys.exit(f"error: {a.out} exists")
        json.dump(o, open(a.out, "w"), indent=1)
    print(json.dumps(o))


def hardware():
    sc = lambda c: subprocess.run(c, capture_output=True, text=True).stdout.strip()
    return dict(cpu=sc(["sysctl", "-n", "machdep.cpu.brand_string"]), ncpu=sc(["sysctl", "-n", "hw.ncpu"]), mem_bytes=sc(["sysctl", "-n", "hw.memsize"]),
                os=sc(["sw_vers", "-productVersion"]), machine=platform.machine(), python=sys.version.split()[0], loadavg=os.getloadavg(),
                power=sc(["pmset", "-g", "batt"]).splitlines()[:1])


def timed(cmd, env, log):
    t0 = time.perf_counter()
    with open(log, "w") as f: p = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT)
    _, st, ru = os.wait4(p.pid, 0)
    wall = time.perf_counter() - t0
    rss = ru.ru_maxrss / (1 if sys.platform == "darwin" else 1024) / 2 ** 20
    return dict(wall_s=wall, cpu_s=ru.ru_utime + ru.ru_stime, peak_rss_mib=rss, rc=os.waitstatus_to_exitcode(st))


def one_child(a):  # internal: run one baseline in-process; prints the baseline's result dict
    from sbgv7.baselines import baselines as B
    from sbgv7.config import load_inputs
    t = json.load(open(a.task)); inputs = load_inputs(t["inputs"])
    c, _ = B.make_ctx(t["base"], t["var"], t["entry"], t["cfg"], a.workdir)
    print(json.dumps((B.b1 if a.system == "B1" else B.b1_rep)(c, inputs, 60)))


def cmd_timing(a):
    out = os.path.abspath(a.out)
    if os.path.exists(out) and os.listdir(out): sys.exit(f"error: refusing to write into non-empty {out}")
    K = k1(); tasks = subset(K); os.makedirs(out)
    hw = hardware(); env = K.ENV; me = os.path.abspath(__file__)
    for t in tasks:  # one task file per pair (read by the B1 child so it does not pay task-building cost)
        d = os.path.join(out, "tasks", t["arm"], t["pair"]); os.makedirs(d)
        json.dump(t["inputs"], open(d + "/inputs.json", "w")); json.dump(K.CFG, open(d + "/cfg.json", "w"))
        json.dump(dict(base=os.path.join(ROOT, t["base"]), var=os.path.join(ROOT, t["var"]), entry=t["entry"], inputs=d + "/inputs.json", cfg=K.CFG), open(d + "/task.json", "w"))
    jobs = [(r, t, s) for r in range(a.reps) for t in tasks for s in SYSTEMS]
    random.Random(SEED + 1).shuffle(jobs)  # fixed-seed interleaving: drift (thermal/background) is spread over systems
    rows = []
    for i, (rep, t, s) in enumerate(jobs):
        td = os.path.join(out, "tasks", t["arm"], t["pair"]); wd = os.path.join(out, "work", s, f"rep{rep}", t["arm"], t["pair"]); os.makedirs(wd)
        if s == "V0":
            cmd = [K.PY, "-m", "sbgv7", "compare", os.path.join(ROOT, t["base"]), os.path.join(ROOT, t["var"]), "--entry", t["entry"],
                   "--inputs", td + "/inputs.json", "--config", td + "/cfg.json", "--out", wd]
        else:
            cmd = [K.PY, me, "_one", "--system", s, "--task", td + "/task.json", "--workdir", wd]
        m = timed(cmd, env, wd + "/stdout.txt")
        m.update(system=s, rep=rep, arm=t["arm"], pair=t["pair"], project=t["project"], order=i)
        if s == "V0" and os.path.exists(wd + "/verdict.json"): m["engine_cpu_s"] = json.load(open(wd + "/verdict.json"))["cpu_seconds_spent"]
        rows.append(m); print(i, len(jobs), s, t["pair"], round(m["wall_s"], 2), flush=True)
    startup = {n: [timed([K.PY, "-c", f"import {n}"], env, os.devnull)["wall_s"] for _ in range(5)] for n in ("sbgv7.runner", "sbgv7.baselines.baselines")}
    hw["loadavg_end"] = os.getloadavg()
    json.dump(dict(hardware=hw, subset=[{k: x[k] for k in ("arm", "pair", "project")} for x in tasks], rows=rows, startup_import_wall_s=startup, reps=a.reps),
              open(os.path.join(out, "timing_raw.json"), "w"), indent=1)
    json.dump(analyse(rows, hw, a.reps), open(os.path.join(out, "timing_summary.json"), "w"), indent=1); print("done", out)


def analyse(rows, hw, reps):
    g = collections.defaultdict(list)
    for r in rows: g[(r["pair"], r["system"])].append(r)
    pairs = sorted({k[0] for k in g}); proj = {r["pair"]: r["project"] for r in rows}
    med = lambda p, s, m: statistics.median(x[m] for x in g[(p, s)])
    out = dict(hardware=hw, reps=reps, n_pairs=len(pairs), failed_runs=sum(r["rc"] != 0 for r in rows), systems={}, relative_overhead={})
    for s in SYSTEMS:
        d = {}
        for m in ("wall_s", "cpu_s", "peak_rss_mib"):
            pm = [med(p, s, m) for p in pairs]
            cv = [statistics.pstdev(x[m] for x in g[(p, s)]) / statistics.mean(x[m] for x in g[(p, s)]) for p in pairs if statistics.mean(x[m] for x in g[(p, s)]) > 0]
            d[m] = dict(per_pair_median=summ(pm), cv_across_reps=dict(median=round(statistics.median(cv), 4), max=round(max(cv), 4)) if cv else None)
        out["systems"][s] = d
    rng = random.Random(SEED); projs = sorted(set(proj.values())); byproj = {p: [q for q in pairs if proj[q] == p] for p in projs}
    for s in ("B1", "B1rep"):
        for m in ("wall_s", "cpu_s"):
            ratio = {p: med(p, "V0", m) / med(p, s, m) for p in pairs if med(p, s, m) > 0}
            pr = list(ratio.values()); bs = []
            for _ in range(BOOT):  # project-cluster bootstrap of the median per-pair ratio
                pick = [q for p in (rng.choice(projs) for _ in projs) for q in byproj[p] if q in ratio]
                if pick: bs.append(statistics.median(ratio[q] for q in pick))
            bs.sort()
            out["relative_overhead"][f"V0_over_{s}_{m}"] = dict(per_pair_ratio=summ(pr), ratio_of_sums=round(sum(med(p, "V0", m) for p in pairs) / sum(med(p, s, m) for p in pairs), 3),
                                                              median_ratio_ci95=[round(bs[int(.025 * len(bs))], 3), round(bs[int(.975 * len(bs))], 3)] if bs else None)
    return out


def parser():
    ap = argparse.ArgumentParser(prog="p2_e6_runtime.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("records"); r.add_argument("--src", nargs="+", required=True); r.add_argument("--out", required=True)
    s = sp.add_parser("select"); s.add_argument("--out", default="")
    t = sp.add_parser("timing"); t.add_argument("--out", required=True); t.add_argument("--reps", type=int, default=5)
    o = sp.add_parser("_one"); o.add_argument("--system", required=True, choices=["B1", "B1rep"]); o.add_argument("--task", required=True); o.add_argument("--workdir", required=True)
    return ap


if __name__ == "__main__":
    sys.path.insert(0, ROOT)
    a = parser().parse_args()
    {"records": cmd_records, "select": cmd_select, "timing": cmd_timing, "_one": one_child}[a.cmd](a)
