"""K1/K2 feasibility spike for sbgv7 on EXISTING (non-pristine) data. DEVELOPMENT/EXPLORATORY only.
Usage: python experiments/v7b/k1_spike.py run [--arms quixbugs,quixbugs_neg,synthetic,bugsinpy_units] [--rerun N]
       python experiments/v7b/k1_spike.py summarize
Engine is invoked only via `python -m sbgv7 compare` (sandboxed child per run). OMP_NUM_THREADS=1, <=4 processes.
Per-run limits are the spec's fast_cpu_s=2 / wall 5 s (config default 10/20 made infinite loops cost 60 s a pair);
this is a spike setting, not a tuned threshold."""
import collections, glob, json, os, random, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
RAW = os.path.join(ROOT, os.environ.get("K1_RAW", "results/raw/k1_spike"))
PROC = os.path.join(ROOT, os.environ.get("K1_PROC", "results/processed"))
CFG = {"budget": {"cpu_seconds": 60, "per_run": {"cpu_s": 2, "wall_s": 5}}}
MAXIN, SYN_MAX, WORKERS = 12, 150, 4
ENV = dict(os.environ, OMP_NUM_THREADS="1", PYTHONHASHSEED="0")
PY = os.path.join(ROOT, ".venv/bin/python")


def J(p): return json.load(open(os.path.join(ROOT, p)))


def jsonable(x):
    return json.loads(json.dumps(x))  # tuples -> lists


def synth_inputs(path):
    from experiments.final.entry_policy import select_entry_structural
    d = select_entry_structural(open(os.path.join(ROOT, path)).read())
    ins = d.inputs[:MAXIN]
    if ins == [None]: args = [[]]
    elif isinstance(ins[0], tuple): args = [list(i) for i in ins]
    else: args = [[i] for i in ins]
    return d.name, [{"id": f"i{k}", "args": jsonable(a)} for k, a in enumerate(args)]


def tasks_quixbugs():
    out = []
    for p in J("external/quixbugs/manifest.json")["programs"]:
        if not p["eligible"]["declared"]: continue
        cases = [json.loads(l) for l in open(os.path.join(ROOT, p["declared_inputs"]["file"])) if l.strip()]
        ins = [{"id": f"i{k}", "args": c[0]} for k, c in enumerate(cases[:MAXIN])]
        out.append(dict(arm="quixbugs", pair=p["id"], base=p["buggy_path"], var=p["fixed_path"], entry=p["id"], inputs=ins,
                        label="BUGGY_VS_FIXED", project="quixbugs"))
        for n in p["negatives"]:
            out.append(dict(arm="quixbugs_neg", pair=n["variant_id"], base=p["fixed_path"], var=n["path"], entry=p["id"], inputs=ins,
                            label="SYN_EQUIVALENT", project="quixbugs", sp=n["transformation_type"]))
    return out


def tasks_synthetic():
    rng = random.Random(20261117)
    byprog = collections.defaultdict(lambda: collections.defaultdict(list))
    for f in sorted(glob.glob(os.path.join(ROOT, "benchmark/datasets/v8/pairs_*.jsonl")) + glob.glob(os.path.join(ROOT, "benchmark/datasets/v10_independent/pairs_*.jsonl"))):
        for l in open(f):
            d = json.loads(l); d["ds"] = f.split("datasets/")[1].split("/")[0]
            byprog[(d["benchmark_version"], d["base_id"])][d["expected_label"]].append(d)
    pick = []
    for k in sorted(byprog):  # stratified by program: <=1 EQUIVALENT + 1 CHANGED each, then trim round-robin to SYN_MAX
        for lab in ("EQUIVALENT", "CHANGED"):
            if byprog[k][lab]: pick.append(rng.choice(byprog[k][lab]))
    rng.shuffle(pick); pick = pick[:SYN_MAX]
    out = []
    for d in pick:
        try: entry, ins = synth_inputs(d["base_path"])
        except Exception as e: out.append(dict(arm="synthetic", pair=d["pair_id"], skip=f"entry_policy: {type(e).__name__}", label=d["expected_label"], project=d["base_id"])); continue
        out.append(dict(arm="synthetic", pair=d["pair_id"], base=d["base_path"], var=d["variant_path"], entry=entry, inputs=ins,
                        label=d["expected_label"], project=d["base_id"], sp=d["transformation_type"]))
    return out


def tasks_bugsinpy():
    out = []
    for b in J("external/bugsinpy/manifest.json")["bugs"]:
        for u in b["units"]:
            if not u["eligible"]: continue
            pid = u["unit_dir"].split("/")[-1]
            if u["kind"] != "function":
                out.append(dict(arm="bugsinpy_units", pair=pid, skip="class unit (engine supports top-level functions only)", project=b["project"], label="REAL_BUGFIX")); continue
            try: entry, ins = synth_inputs(u["buggy_path"])
            except Exception as e: out.append(dict(arm="bugsinpy_units", pair=pid, skip=f"entry_policy: {type(e).__name__}", project=b["project"], label="REAL_BUGFIX")); continue
            out.append(dict(arm="bugsinpy_units", pair=pid, base=u["buggy_path"], var=u["fixed_path"], entry=entry, inputs=ins,
                            label="REAL_BUGFIX", project=b["project"]))
    return out


def run_one(t, tag):
    d = os.path.join(RAW, t["arm"], tag, t["pair"]); os.makedirs(d, exist_ok=True)
    if os.path.exists(os.path.join(d, "evidence.jsonl")): os.remove(os.path.join(d, "evidence.jsonl"))
    json.dump(t["inputs"], open(os.path.join(d, "inputs.json"), "w")); json.dump(CFG, open(os.path.join(d, "cfg.json"), "w"))
    t0 = time.time()
    r = subprocess.run([PY, "-m", "sbgv7", "compare", os.path.join(ROOT, t["base"]), os.path.join(ROOT, t["var"]), "--entry", t["entry"],
                        "--inputs", d + "/inputs.json", "--config", d + "/cfg.json", "--out", d], cwd=ROOT, env=ENV, capture_output=True, text=True)
    wall = time.time() - t0
    open(os.path.join(d, "stderr.txt"), "w").write(r.stderr[-4000:])
    rec = {k: t.get(k) for k in ("arm", "pair", "label", "project", "sp", "entry")}
    rec.update(tag=tag, rc=r.returncode, wall_s=round(wall, 2), n_inputs=len(t["inputs"]))
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


def cmd_run(arms, rerun):
    allt = {"quixbugs": tasks_quixbugs, "synthetic": tasks_synthetic, "bugsinpy_units": tasks_bugsinpy}
    tasks = []
    q = tasks_quixbugs()
    for a in arms:
        tasks += [t for t in (q if a.startswith("quixbugs") else allt[a]()) if t["arm"] == a]
    os.makedirs(PROC, exist_ok=True)
    skipped = [t for t in tasks if "skip" in t]; runnable = [t for t in tasks if "skip" not in t]
    print(f"{len(runnable)} to run, {len(skipped)} skipped pre-run", flush=True)
    res = []
    with ThreadPoolExecutor(WORKERS) as ex:
        for i, r in enumerate(ex.map(lambda t: run_one(t, "run1"), runnable)):
            res.append(r); print(i, r["arm"], r["pair"], r["verdict"], r.get("primary"), r["wall_s"], flush=True)
    for t in skipped: res.append(dict(arm=t["arm"], pair=t["pair"], label=t["label"], project=t["project"], verdict="NOT_DRIVEN", primary=t["skip"], tag="run1"))
    # determinism: rerun a stratified subset (all real-pair arms, first `rerun` of others)
    rr = [t for t in runnable if t["arm"] in ("quixbugs", "bugsinpy_units")] + \
         [t for t in runnable if t["arm"] in ("quixbugs_neg", "synthetic")][:rerun]
    with ThreadPoolExecutor(WORKERS) as ex:
        for r in ex.map(lambda t: run_one(t, "run2"), rr): res.append(r)
    with open(os.path.join(PROC, "k1_spike_per_pair.jsonl"), "a") as f:
        for r in res: f.write(json.dumps(r) + "\n")


def cmd_summarize():
    rows = [json.loads(l) for l in open(os.path.join(PROC, "k1_spike_per_pair.jsonl"))]
    r1 = {(r["arm"], r["pair"]): r for r in rows if r["tag"] == "run1"}
    r2 = {(r["arm"], r["pair"]): r for r in rows if r["tag"] == "run2"}
    S = {"note": "DEVELOPMENT/EXPLORATORY feasibility; all data non-pristine; no thresholds tuned"}
    key = lambda r: (r.get("verdict"), r.get("level"), r.get("primary"), tuple(r.get("secondary") or ()), r.get("witness_id"))
    for arm in sorted({a for a, _ in r1}):
        rs = [r for (a, _), r in r1.items() if a == arm]
        ran = [r for r in rs if r["verdict"] not in ("NOT_DRIVEN",)]
        c = collections.Counter(r["verdict"] for r in rs)
        prim = collections.Counter(r.get("primary") for r in rs if r["verdict"] in ("INSUFFICIENT", "NOT_DRIVEN"))
        non_div = [r for r in ran if r["verdict"] != "DIVERGENT_OBSERVABLE"]
        act = [r for r in ran if r["verdict"] == "DIVERGENT_OBSERVABLE" or (r.get("units_total") and r["units_hit"] == r["units_total"])]
        det_ok = [r for r in ran if r["verdict"] == "DIVERGENT_OBSERVABLE" or (r.get("quarantined") == 0 and "nondeterministic" not in [r.get("primary")] + (r.get("secondary") or []))]
        # "runnable": engine reached the body of both versions on >=1 input (not import_error/unsupported_signature/no_inputs/tool_error/sandbox_failure)
        bad = {"import_error", "unsupported_signature", "alignment_failed", "tool_error", "sandbox_failure", "no_inputs"}
        runnable = [r for r in ran if r["verdict"] == "DIVERGENT_OBSERVABLE" or not ({r.get("primary")} | set(r.get("secondary") or ())) & bad]
        both = [(r1[(arm, p)], r2[(arm, p)]) for (a, p) in r2 if a == arm and (a, p) in r1]
        wt = sorted(r["wall_s"] for r in ran)
        S[arm] = dict(n_pairs=len(rs), n_not_driven=c.get("NOT_DRIVEN", 0), n_projects=len({r["project"] for r in rs}),
                      n_runnable=len(runnable), runnable_projects=len({r["project"] for r in runnable}),
                      verdicts=dict(c), insufficient_reasons=dict(prim), frac_insufficient=round(c.get("INSUFFICIENT", 0) / max(1, len(rs)), 3),
                      det_confirmed_frac=round(len(det_ok) / max(1, len(ran)), 3), activation_frac=round(len(act) / max(1, len(ran)), 3),
                      levels=dict(collections.Counter(r.get("level") for r in ran if r["verdict"] == "NO_DIVERGENCE_OBSERVED")),
                      determinism=dict(n_rerun=len(both), identical=sum(key(a) == key(b) for a, b in both),
                                       diffs=[(a["pair"], key(a)[:3], key(b)[:3]) for a, b in both if key(a) != key(b)]),
                      wall_s=dict(median=wt[len(wt) // 2] if wt else None, p90=wt[int(.9 * len(wt))] if wt else None, total=round(sum(wt), 1)),
                      engine_crashes=[(r["pair"], r.get("crash")) for r in rs if r["verdict"] == "ENGINE_NO_VERDICT"],
                      confusion={lab: dict(collections.Counter(r["verdict"] + ("/" + r["level"] if r.get("level") else "") for r in rs if r["label"] == lab)) for lab in sorted({r["label"] for r in rs})})
    json.dump(S, open(os.path.join(PROC, "k1_spike_summary.json"), "w"), indent=1)
    print(json.dumps(S, indent=1))


def _usage_exit():
    """-h/--help prints usage and exits 0 BEFORE any work or file write; unknown/missing commands exit 2 (they used to fall through to summarize)."""
    a = sys.argv[1:]
    if any(x in ("-h", "--help") for x in a):
        print("usage:\n" + __doc__); sys.exit(0)
    if not a or a[0] not in ("run", "summarize"):
        print("usage: k1_spike.py {run [--arms A,B] [--rerun N] | summarize} (see --help)", file=sys.stderr); sys.exit(2)


if __name__ == "__main__":
    _usage_exit()
    if sys.argv[1] == "run":
        arms = (sys.argv[sys.argv.index("--arms") + 1] if "--arms" in sys.argv else "quixbugs,quixbugs_neg,synthetic,bugsinpy_units").split(",")
        cmd_run(arms, int(sys.argv[sys.argv.index("--rerun") + 1]) if "--rerun" in sys.argv else 25)
    else: cmd_summarize()
