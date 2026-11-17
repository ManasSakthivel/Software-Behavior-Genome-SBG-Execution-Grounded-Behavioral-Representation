"""Driver: python -m sbgv7.baselines.run run [--arms a,b] [--only B1,B3] [--limit N] | summarize.
Pairs/paths/inputs/labels come from experiments/v7b/k1_spike.py task builders + results/raw/k1_spike/<arm>/run1/<pair>/inputs.json
(the exact inputs V7-B saw). DEVELOPMENT/EXPLORATORY only; nothing tuned except B4's threshold (development rows only)."""
import collections, importlib.util, json, os, sys
from concurrent.futures import ThreadPoolExecutor
from . import baselines as B
from ..config import load_inputs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, os.environ.get("BL_RAW", "results/raw/baselines"))  # env overrides let reproduction runs avoid overwriting committed results
PROC = os.path.join(ROOT, os.environ.get("K1_PROC", "results/processed"))
CAP, SEED = 60, 1001  # CPU-s per pair (= V7-B headline budget); first exploration_seed of the spec
CFG = {"budget": {"cpu_seconds": CAP, "per_run": {"cpu_s": 2, "wall_s": 5}}}  # identical to the K1 spike
os.environ["OMP_NUM_THREADS"] = "1"; os.environ["PYTHONHASHSEED"] = "0"
POS = {"BUGGY_VS_FIXED", "REAL_BUGFIX", "CHANGED"}


def spike():
    s = importlib.util.spec_from_file_location("k1_spike", os.path.join(ROOT, "experiments/v7b/k1_spike.py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def tasks(arms):
    k = spike(); allt = {"quixbugs": k.tasks_quixbugs, "synthetic": k.tasks_synthetic, "bugsinpy_units": k.tasks_bugsinpy}
    q, out = k.tasks_quixbugs(), []
    for a in arms: out += [t for t in (q if a.startswith("quixbugs") else allt[a]()) if t["arm"] == a]
    man = k.J("external/quixbugs/manifest.json")["programs"]
    exp = {p["id"]: [json.loads(l)[1] for l in open(os.path.join(ROOT, p["declared_inputs"]["file"])) if l.strip()] for p in man if p["eligible"]["declared"]}
    for t in out:
        if "skip" in t: continue
        t["inputs"] = load_inputs(os.path.join(k.RAW, t["arm"], "run1", t["pair"], "inputs.json"))  # the exact V7-B inputs
        t["expected"] = exp.get(t["entry"], [])[: len(t["inputs"])] if t["arm"].startswith("quixbugs") else None
    return out


def run_pair(t, only):
    row = {k: t.get(k) for k in ("arm", "pair", "label", "project", "sp")}
    if "skip" in t:
        return {**row, "NOT_DRIVEN": t["skip"]}
    ab = lambda p: os.path.join(ROOT, p)
    d = os.path.join(RAW, t["arm"], t["pair"])
    row["edit_size"] = B.edit_size(ab(t["base"]), ab(t["var"]))
    for name, fn in (("B1", lambda c, x: B.b1(c, t["inputs"], CAP)), ("B1rep", lambda c, x: B.b1_rep(c, t["inputs"], CAP)),
                     ("B2", lambda c, x: B.b2(c, t["inputs"], t["expected"], CAP)), ("B3", lambda c, x: B.b3(c, t["inputs"], CAP, SEED))):
        if only and name not in only: continue
        if name == "B2" and not t["expected"]:
            row[name] = {"verdict": "NOT_RUN", "reason": "no declared expected outputs (no test oracle) for this arm"}; continue
        try:
            c, _ = B.make_ctx(ab(t["base"]), ab(t["var"]), t["entry"], CFG, os.path.join(d, name))
            row[name] = fn(c, None)
        except Exception as e:  # recorded, never swallowed silently
            row[name] = {"verdict": "ERROR", "detail": f"{type(e).__name__}: {e}"}
    return row


def cmd_run(arms, only, limit):
    ts = tasks(arms)[: limit or None]
    os.makedirs(PROC, exist_ok=True)
    with ThreadPoolExecutor(4) as ex, open(os.path.join(PROC, "baselines_per_pair.jsonl"), "a") as f:
        for r in ex.map(lambda t: run_pair(t, only), ts):
            f.write(json.dumps(r) + "\n"); f.flush(); print(r["arm"], r["pair"], {k: v["verdict"] for k, v in r.items() if isinstance(v, dict)}, flush=True)


def cmd_summarize():
    rows = [json.loads(l) for l in open(os.path.join(PROC, "baselines_per_pair.jsonl"))]
    rows = list({(r["arm"], r["pair"]): r for r in rows}.values())  # last write wins
    v7 = {(r["arm"], r["pair"]): r for r in map(json.loads, open(os.path.join(PROC, "k1_spike_per_pair.jsonl"))) if r["tag"] == "run1"}
    run = [r for r in rows if "NOT_DRIVEN" not in r]
    # B4: threshold on a DEVELOPMENT half (project-hash parity), reported on both halves; deployed threshold uses the tune half only.
    half = lambda r: sum(map(ord, r["project"])) % 2
    tune = [r for r in run if half(r) == 0]
    t, ba = B.tune_threshold([r["edit_size"] for r in tune], [r["label"] in POS for r in tune])
    for r in run: r["B4"] = {"verdict": B.b4(r["edit_size"], t), "cpu_s": 0.0, "edit_size": r["edit_size"]}
    c0 = B.load_c0g(ROOT)
    tr = [(s, l) for s, st, l, src in c0.values() if src == "train_oof" and st == "ACTIVATED"]
    t5, ba5 = B.tune_threshold([s for s, _ in tr], [bool(l) for _, l in tr])  # threshold from TRAIN OOF only
    for r in run:
        pid = r["pair"] if r["arm"] == "synthetic" else (f"quixbugs__{r['pair']}__bug__declared" if r["arm"] == "quixbugs" else f"quixbugs__{r['pair']}__declared")
        if r["arm"] == "bugsinpy_units": r["B5"] = {"verdict": "NOT_RUN", "reason": "V6 BugsInPy pair ids are function-level real_fix/SP rows from other extraction; no join to K1 units"}
        elif pid not in c0: r["B5"] = {"verdict": "NOT_RUN", "reason": "pair absent from V6 artifacts"}
        else:
            s, st, _, src = c0[pid]
            r["B5"] = {"verdict": (DIV if s >= t5 else NOD) if st == "ACTIVATED" else "ABSTAIN_V6", "score": s, "src": src}
    S = {"note": "DEVELOPMENT/EXPLORATORY; non-pristine; descriptive only", "cap_cpu_s": CAP, "seed": SEED,
         "B4": {"threshold": t, "tune_balanced_acc": round(ba, 3), "tune_n": len(tune), "tune_rule": "projects with even sum(ord) hash"},
         "B5": {"threshold": t5, "train_oof_balanced_acc": round(ba5, 3), "n_train_oof_activated": len(tr)}}
    for arm in sorted({r["arm"] for r in run}):
        rs = [r for r in run if r["arm"] == arm]; S[arm] = {"n": len(rs)}
        for b in ("B1", "B1rep", "B2", "B3", "B4", "B5"):
            vs = [r.get(b) for r in rs if r.get(b)]
            if not vs: continue
            c = collections.Counter(v["verdict"] for v in vs)
            ct = {lab: dict(collections.Counter(r[b]["verdict"] for r in rs if r.get(b) and r["label"] == lab)) for lab in sorted({r["label"] for r in rs})}
            cpu = sorted(v.get("cpu_s", 0) for v in vs if "cpu_s" in v)
            agree = collections.Counter((r[b]["verdict"], v7[(arm, r["pair"])]["verdict"]) for r in rs if r.get(b) and (arm, r["pair"]) in v7)
            S[arm][b] = dict(verdicts=dict(c), by_label=ct, cpu_s=dict(median=cpu[len(cpu) // 2] if cpu else None, max=cpu[-1] if cpu else None, total=round(sum(cpu), 1)),
                             vs_v7={f"{a}|{b_}": n for (a, b_), n in agree.items()})
    json.dump(S, open(os.path.join(PROC, "baselines_summary.json"), "w"), indent=1)
    with open(os.path.join(PROC, "baselines_per_pair_final.jsonl"), "w") as f:
        for r in run: f.write(json.dumps(r) + "\n")
    print(json.dumps(S, indent=1))


DIV, NOD = B.DIVERGE, B.NO_DIFF
if __name__ == "__main__":
    a = sys.argv
    if a[1] == "run":
        g = lambda k, d=None: a[a.index(k) + 1] if k in a else d
        cmd_run(g("--arms", "quixbugs,quixbugs_neg,synthetic,bugsinpy_units").split(","), set(g("--only", "").split(",")) - {""}, int(g("--limit", 0)))
    else: cmd_summarize()
