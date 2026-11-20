"""Phase 2 E4/E5 config-variant driver. DEVELOPMENT/EXPLORATORY; pre-registered in reports/phase2/E3_E7_PROTOCOLS.md.
Usage:
  python experiments/v7b/p2_variants.py run --variant V0|V1|V2|V3|V4|V5|S2F06|S2F08|S2F09 --out DIR [--arms a,b] [--workers 4] [--limit N]
  python experiments/v7b/p2_variants.py csv --e3 E3_DIR --runs V0=DIR V1=DIR ... --out FILE.csv [--baselines B1,B1+rep]
  python experiments/v7b/p2_variants.py list
`run` applies the variant's config to the SAME task list as experiments/v7b/k1_spike.py (its builders are imported, not edited), calls
`python -m sbgv7 compare` once per pair (V5: through a `python -c` wrapper that sets sbgv7.runner.FOLD_FD1=False), and writes
DIR/proc/k1_spike_per_pair.jsonl (k1_spike schema, tag run1, plus a `variant` key) and DIR/raw/<arm>/run1/<pair>/ evidence.
Refuses an existing non-empty DIR. `csv` builds a dev_pairs_per_system-style CSV (system = variant name) for scripts/analyze_results.py;
truth/dataset/flag are copied from the E3 V7-B rows, B1/B1+rep rows (if asked) from E3. -h exits 0 before any work; bad usage exits 2."""
import argparse, copy, csv, importlib.util, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARMS = "quixbugs,quixbugs_neg,synthetic,bugsinpy_units"
VARIANTS = {  # config deltas over k1_spike.CFG (which leaves every other key at the sbgv7 default)
    "V0": {}, "V1": {"repeat": {"r_det": 1}}, "V2": {"repeat": {"r_replay": 1}}, "V3": {"repeat": {"k_alt": 0}},
    "V4": {"repeat": {"r_det": 1, "r_replay": 1, "k_alt": 0}}, "V5": {},  # V5 = FOLD_FD1=False (UD-3 reversal), same config as V0
    "S2F06": {"suff": {"s2_branch_floor": 0.6}}, "S2F08": {"suff": {"s2_branch_floor": 0.8}}, "S2F09": {"suff": {"s2_branch_floor": 0.9}},
}
WRAP = ("import sys, sbgv7.runner as r; r.FOLD_FD1 = False; from sbgv7.__main__ import main; sys.exit(main(sys.argv[1:]))")


def k1():
    s = importlib.util.spec_from_file_location("k1_spike", os.path.join(ROOT, "experiments/v7b/k1_spike.py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def build_cfg(variant, base):
    cfg = copy.deepcopy(base)
    for sec, d in VARIANTS[variant].items(): cfg.setdefault(sec, {}).update(d)
    return cfg


def run_one(K, variant, cfg, t, raw):
    d = os.path.join(raw, t["arm"], "run1", t["pair"]); os.makedirs(d)  # fresh dir: evidence is never overwritten
    json.dump(t["inputs"], open(os.path.join(d, "inputs.json"), "w")); json.dump(cfg, open(os.path.join(d, "cfg.json"), "w"))
    head = [K.PY, "-c", WRAP] if variant == "V5" else [K.PY, "-m", "sbgv7"]
    t0 = time.time()
    r = subprocess.run(head + ["compare", os.path.join(ROOT, t["base"]), os.path.join(ROOT, t["var"]), "--entry", t["entry"],
                       "--inputs", d + "/inputs.json", "--config", d + "/cfg.json", "--out", d], cwd=ROOT, env=K.ENV, capture_output=True, text=True)
    wall = time.time() - t0
    open(os.path.join(d, "stderr.txt"), "w").write(r.stderr[-4000:])
    rec = {k: t.get(k) for k in ("arm", "pair", "label", "project", "sp", "entry")}
    rec.update(tag="run1", rc=r.returncode, wall_s=round(wall, 2), n_inputs=len(t["inputs"]), variant=variant)
    vp = os.path.join(d, "verdict.json")
    if os.path.exists(vp):
        v = json.load(open(vp))
        rec.update(verdict=v["verdict"], level=v["level"], primary=v["primary"], secondary=v["secondary"], witness_id=v["witness_id"], cpu_s=v["cpu_seconds_spent"])
        for l in open(os.path.join(d, "evidence.jsonl")):
            r_ = json.loads(l)["rec"]
            if r_["kind"] == "SufficiencyRecord":
                b = r_["body"]; rec.update(units_total=b["units_total"], units_hit=b["units_hit"], inputs_same=b["inputs_same"],
                                           quarantined=b["quarantined"], stop_reason=b["stop_reason"], branch_cov=b["branch_cov"], r_empty=b["r_empty"])
    else:
        rec.update(verdict="ENGINE_NO_VERDICT", crash=r.stderr[-800:])
    return rec


def cmd_run(a):
    out = os.path.abspath(a.out)
    if os.path.exists(out) and os.listdir(out): sys.exit(f"error: refusing to write into non-empty {out}")
    K = k1(); allt = {"quixbugs": K.tasks_quixbugs, "synthetic": K.tasks_synthetic, "bugsinpy_units": K.tasks_bugsinpy}
    arms = a.arms.split(","); bad = set(arms) - {"quixbugs", "quixbugs_neg", "synthetic", "bugsinpy_units"}
    if bad: sys.exit(f"error: unknown arm(s) {sorted(bad)}")
    q, tasks = K.tasks_quixbugs(), []
    for arm in arms: tasks += [t for t in (q if arm.startswith("quixbugs") else allt[arm]()) if t["arm"] == arm]
    runnable = [t for t in tasks if "skip" not in t][: a.limit or None]
    skipped = [t for t in tasks if "skip" in t] if not a.limit else []
    raw, proc = os.path.join(out, "raw"), os.path.join(out, "proc"); os.makedirs(raw); os.makedirs(proc)
    cfg = build_cfg(a.variant, K.CFG); json.dump(dict(variant=a.variant, cfg=cfg, fold_fd1=a.variant != "V5", workers=a.workers, arms=arms), open(os.path.join(out, "variant.json"), "w"), indent=1)
    print(f"{a.variant}: {len(runnable)} to run, {len(skipped)} skipped pre-run", flush=True)
    with ThreadPoolExecutor(a.workers) as ex, open(os.path.join(proc, "k1_spike_per_pair.jsonl"), "w") as f:
        for i, r in enumerate(ex.map(lambda t: run_one(K, a.variant, cfg, t, raw), runnable)):
            f.write(json.dumps(r) + "\n"); f.flush(); print(i, r["arm"], r["pair"], r["verdict"], r.get("primary"), r["wall_s"], flush=True)
        for t in skipped:
            f.write(json.dumps(dict(arm=t["arm"], pair=t["pair"], label=t["label"], project=t["project"], verdict="NOT_DRIVEN", primary=t["skip"], tag="run1", variant=a.variant)) + "\n")


MAP = {"DIVERGE": "DIVERGENT_OBSERVABLE", "NO_DIFF": "NO_DIVERGENCE_OBSERVED"}
BLKEY = {"B1": "B1", "B1+rep": "B1rep"}


def cmd_csv(a):
    if os.path.exists(a.out): sys.exit(f"error: {a.out} exists")
    e3 = os.path.abspath(a.e3)
    proc = os.path.join(e3, "processed")
    base = {r["pair_id"]: r for r in csv.DictReader(open(os.path.join(proc, "dev_pairs_per_system.csv"))) if r["system"] == "V7-B"}
    rows = []
    for spec in a.runs:
        name, d = spec.split("=", 1)
        for l in open(os.path.join(d, "proc", "k1_spike_per_pair.jsonl")):
            r = json.loads(l); pid = f"{r['arm']}:{r['pair']}"; b = base[pid]
            rows.append(dict(project=b["project"], pair_id=pid, system=name, verdict=r["verdict"], sufficiency=r.get("level") or "", truth=b["truth"],
                             cpu_s=r.get("cpu_s", ""), mem_mb="", dataset=b["dataset"], flag=b["flag"]))
    for name in [x for x in a.baselines.split(",") if x]:
        if name not in BLKEY: sys.exit(f"error: baseline {name} not supported")
        bl = {(r["arm"], r["pair"]): r for r in map(json.loads, open(os.path.join(proc, "baselines_per_pair.jsonl")))}
        for pid, b in base.items():
            arm, pair = pid.split(":", 1); x = bl.get((arm, pair), {}).get(BLKEY[name])
            rows.append(dict(project=b["project"], pair_id=pid, system=name, verdict=MAP.get(x["verdict"], "") if x else "", sufficiency="", truth=b["truth"],
                             cpu_s=x["cpu_s"] if x else "", mem_mb="", dataset=b["dataset"], flag=b["flag"]))
    rows.sort(key=lambda r: (r["system"], r["pair_id"]))
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["project", "pair_id", "system", "verdict", "sufficiency", "truth", "cpu_s", "mem_mb", "dataset", "flag"])
        w.writeheader(); w.writerows(rows)
    print(len(rows), "rows ->", a.out)


def parser():
    ap = argparse.ArgumentParser(prog="p2_variants.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run"); r.add_argument("--variant", required=True, choices=sorted(VARIANTS)); r.add_argument("--out", required=True)
    r.add_argument("--arms", default=ARMS); r.add_argument("--workers", type=int, default=4); r.add_argument("--limit", type=int, default=0)
    c = sp.add_parser("csv"); c.add_argument("--e3", required=True); c.add_argument("--runs", nargs="+", required=True); c.add_argument("--out", required=True)
    c.add_argument("--baselines", default="")
    sp.add_parser("list")
    return ap


if __name__ == "__main__":
    a = parser().parse_args()
    if a.cmd == "list": print(json.dumps(VARIANTS, indent=1))
    elif a.cmd == "run": cmd_run(a)
    else: cmd_csv(a)
