"""V8 DEVELOPMENT collection (exploratory). Same pairs/inputs/limits as experiments/v7b/k1_spike.py (E3), but each pair is run through
`python -m sbgv8 compare` (V7-B engine unmodified + v8_parts.json sidecar). Usage:
  dev_collect.py run [--out results/repro/v8_dev_<ts>]   (<=4 workers, resumable)    dev_collect.py build --out DIR   (-> datasets/v8/dev_records.jsonl + compare with E3)
Labels: truth column of the E3 dev_pairs_per_system.csv: DIV->1, NO_OBS_DIFF->0, UNLABELLED/SUSPECT_LABEL->None. family = project (placeholder)."""
import collections, csv, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from experiments.v7b.k1_spike import CFG, ENV, PY, WORKERS, tasks_bugsinpy, tasks_quixbugs, tasks_synthetic  # read-only reuse of the E3 pair/input builders

E3 = os.path.join(ROOT, "results/v7b_phase2_summary/p2_e3_20261118_092700/processed/dev_pairs_per_system.csv")
OUT_JSONL = os.path.join(ROOT, "datasets/v8/dev_records.jsonl")
LABEL = {"DIV": 1, "NO_OBS_DIFF": 0}  # anything else (UNLABELLED, SUSPECT_LABEL) -> None


def tasks():
    return [t for f in (tasks_quixbugs, tasks_synthetic, tasks_bugsinpy) for t in f() if "skip" not in t]


def run_one(t, out):
    d = os.path.join(out, t["arm"], t["pair"]); os.makedirs(d, exist_ok=True)
    if os.path.exists(os.path.join(d, "v8_parts.json")): return "resumed"
    for p in ("evidence.jsonl", "verdict.json"):
        if os.path.exists(os.path.join(d, p)): os.remove(os.path.join(d, p))
    json.dump(t["inputs"], open(d + "/inputs.json", "w")); json.dump(CFG, open(d + "/cfg.json", "w"))
    t0 = time.time()
    r = subprocess.run([PY, "-m", "sbgv8", "compare", os.path.join(ROOT, t["base"]), os.path.join(ROOT, t["var"]), "--entry", t["entry"],
                        "--inputs", d + "/inputs.json", "--config", d + "/cfg.json", "--out", d], cwd=ROOT, env=ENV, capture_output=True, text=True)
    open(d + "/stderr.txt", "w").write(r.stderr[-4000:])
    json.dump({"rc": r.returncode, "wall_s": round(time.time() - t0, 2), "load1": os.getloadavg()[0], **{k: t.get(k) for k in ("arm", "pair", "project", "label")}}, open(d + "/run_meta.json", "w"))
    return r.returncode


def cmd_run(out):
    ts = tasks(); os.makedirs(out, exist_ok=True)
    print(f"{len(ts)} pairs, out={out}, workers={WORKERS}", flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        for i, (t, rc) in enumerate(zip(ts, ex.map(lambda t: run_one(t, out), ts))): print(i, t["arm"], t["pair"], rc, flush=True)
    print("COLLECT DONE", flush=True)


def cmd_build(out):
    from sbgv8.adapter import load_record
    e3 = {r["pair_id"]: r for r in csv.DictReader(open(E3)) if r["system"] == "V7-B"}
    recs, cmp = [], collections.Counter(); diffs = []
    for t in tasks():
        d = os.path.join(out, t["arm"], t["pair"]); key = f"{t['arm']}:{t['pair']}"; row = e3.get(key)
        if not os.path.exists(os.path.join(d, "v8_parts.json")): diffs.append((key, "NO_RECORD")); continue
        rec = load_record(d, label=LABEL.get(row["truth"]) if row else None, project=t["project"], family=t["project"])
        rec.pair_id = key; rec.split = "development"
        rec.meta.update(label_source="phase2_dev_generator_label", truth_raw=row["truth"] if row else None, arm=t["arm"], dataset=row["dataset"] if row else None,
                        run_meta=json.load(open(d + "/run_meta.json")) if os.path.exists(d + "/run_meta.json") else None, src_dir=os.path.relpath(d, ROOT))
        recs.append(rec)
        if row:
            same = (rec.v7b_verdict, rec.v7b_level or "") == (row["verdict"], row["sufficiency"] or "")
            cmp["agree" if same else "differ"] += 1
            if not same: diffs.append((key, (rec.v7b_verdict, rec.v7b_level), (row["verdict"], row["sufficiency"]), rec.blockers[:2]))
    os.makedirs(os.path.dirname(OUT_JSONL), exist_ok=True)
    with open(OUT_JSONL, "w") as f:
        for r in sorted(recs, key=lambda r: r.pair_id): f.write(r.to_json() + "\n")
    print(json.dumps({"records": len(recs), "y": dict(collections.Counter(r.y for r in recs)), "e3": dict(cmp), "diffs": diffs}, indent=1, default=str))


if __name__ == "__main__":
    a = sys.argv[1:]
    out = os.path.join(ROOT, a[a.index("--out") + 1]) if "--out" in a else os.path.join(ROOT, "results/repro", "v8_dev_" + time.strftime("%Y%m%d_%H%M%S"))
    if a and a[0] == "run": cmd_run(out)
    elif a and a[0] == "build": cmd_build(out)
    else: print(__doc__); sys.exit(2)
