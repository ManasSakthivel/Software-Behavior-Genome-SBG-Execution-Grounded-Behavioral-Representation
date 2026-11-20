"""REAL-EXECUTION perturbations P2/P5/P6 on a PRE-DECLARED subset of development pairs (macOS; engine only via `python -m sbgv8 compare`).
DEVELOPMENT / EXPLORATORY. No holdout, no Linux, no external repos. Limits as experiments/v8/dev_collect.py (per-run cpu 2 s / wall 5 s, budget 60 s), 2 workers.
Commands:  select_supplement / run_supplement -> SUPPLEMENTARY P6 cohort, declared AFTER the primary run showed P6 applicable on 0/20 (see below)
           select   -> writes results/v8_mac_perturb/realexec_selection.json (rule + seed + sha256 of inputs) BEFORE any engine run
           run      -> refuses to start without the selection file; probes candidates, runs P2/P5/P6 variants, writes records + manifest
           analyze  -> (re)builds results/v8_mac_perturb/realexec_matrix.{json,md} from the stored records (no engine)
SELECTION RULE (declared before running; uses no label y, no verdict-by-label, no predictor output):
  pool = dev records whose src evidence dir exists, v7b_verdict != DIVERGENT_OBSERVABLE, >=1 clean SAME input, >=1 changed unit,
         recorded wall_s <= 10 (bounds run time), and a task entry in dev_collect.tasks().
  sample with random.Random(20261118) over pool sorted by pair_id, quota per arm: quixbugs 10, synthetic 10, bugsinpy_units 5, quixbugs_neg 5 (<=30).
VARIANTS per selected pair (all with the same per-run limits; E0 = the recorded dev evidence of that pair):
  candidates: <=24 seeded, output-blind mutations of the pair's own recorded args (int +-1/0/neg, str/list reverse/drop/dup/sort, dict key drop, bool flip).
  probe: engine on candidates only. P2 inputs = first 4 candidates with outcome SAME, deterministic, non-lossy, non-empty hits and NO changed unit hit
         (checked from the recorded hit sets, again on the final augmented record). P6 input = first candidate with outcome CONFIRMED_DIFF (deterministic,
         non-lossy), i.e. a discriminating input found by a generator that never saw outputs or labels; selection is conditioned on the probe outcome.
  p2: original inputs + P2 inputs.   p6: original inputs + the P6 input.
  p5_low (r_det,r_replay,k_alt)=(1,1,0), p5_mid=(2,3,1), p5_high=(5,8,5): original inputs, other limits unchanged (default recorded is (3,5,3)).
  P5 expected: risk(low/mid) >= risk(E0) or INSUFFICIENT. P5_high is reported as information only (no declared expectation).
SUPPLEMENT (declared after seeing the primary result, hence labelled as such): pool = as above but y == 1 (dev label: a divergence is known to exist for the pair) and recorded
  verdict not divergent, not in the primary selection; sample 10 with random.Random(SEED+1). The label is used ONLY to pick pairs where a discriminating input can exist; the
  generator that proposes inputs is still output- and label-blind. Results are reported as a separate cohort.
Evidence classes: P2 = (b) re-execution with added inputs; P5 = (b) re-execution with changed config (repetition of an identical deterministic run is NOT an
independent sample: n_rep vs n_eff are reported side by side); P6 = (c) independently generated input (label/output-blind generator), outcome-conditioned."""
import collections, hashlib, json, os, random, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT)
from experiments.v8.dev_collect import CFG, ENV, PY, tasks
from experiments.v8.run_perturbation_validation import predictors
from sbgv8 import ers
from sbgv8.profile import build_profile
from sbgv8.schema import EvidenceRecord

OUT = os.path.join(ROOT, "results/v8_mac_perturb"); SEL = os.path.join(OUT, "realexec_selection.json"); RUN = os.path.join(OUT, "realexec_20261118")
DATA = os.path.join(ROOT, "datasets/v8/dev_records.jsonl"); SEED = 20261118; QUOTA = {"quixbugs": 10, "synthetic": 10, "bugsinpy_units": 5, "quixbugs_neg": 5}
WORKERS, K_P2, MAX_CAND = 2, 4, 24
P5_CFG = {"low": (1, 1, 0), "mid": (2, 3, 1), "high": (5, 8, 5)}
DIV = "DIVERGENT_OBSERVABLE"
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def clean(i): return i.outcome == "SAME" and i.deterministic and not i.lossy
def uset(r): return {(s, l) for s in ("base", "variant") for l in r.changed_units.get(s, [])}
def hset(i): return {(s, l) for s in ("base", "variant") for l in i.hits.get(s, [])}


def select():
    recs = {r.pair_id: r for r in map(EvidenceRecord.from_json, open(DATA)) if r.pair_id}
    tk = {f"{t['arm']}:{t['pair']}": t for t in tasks()}; pool = collections.defaultdict(list)
    for pid, r in sorted(recs.items()):
        m = r.meta.get("run_meta") or {}
        if (pid in tk and os.path.isdir(os.path.join(ROOT, r.meta.get("src_dir", "/nonexistent"))) and r.v7b_verdict != DIV and any(clean(i) for i in r.inputs)
                and uset(r) and (m.get("wall_s") or 99) <= 10): pool[r.meta["arm"]].append(pid)
    rng, chosen = random.Random(SEED), []
    for arm, q in QUOTA.items(): chosen += rng.sample(pool[arm], min(q, len(pool[arm])))
    os.makedirs(OUT, exist_ok=True)
    json.dump({"declared_before_running": True, "seed": SEED, "quota": QUOTA, "pool_sizes": {a: len(v) for a, v in pool.items()}, "selected": chosen,
               "records_sha256": sha(DATA), "rule": __doc__.split("SELECTION RULE")[1].split("VARIANTS")[0].strip(), "written": time.strftime("%Y-%m-%dT%H:%M:%S")},
              open(SEL, "w"), indent=1)
    print(len(chosen), "selected", {a: len(v) for a, v in pool.items()})


def select_supplement():
    sel = json.load(open(SEL)); tk = {f"{t['arm']}:{t['pair']}" for t in tasks()}; pool = []
    for r in sorted(map(EvidenceRecord.from_json, open(DATA)), key=lambda r: r.pair_id):
        m = r.meta.get("run_meta") or {}
        if (r.y == 1 and r.v7b_verdict != DIV and any(clean(i) for i in r.inputs) and uset(r) and (m.get("wall_s") or 99) <= 10 and r.pair_id in tk and r.pair_id not in sel["selected"]
                and os.path.isdir(os.path.join(ROOT, r.meta.get("src_dir", "/nonexistent")))): pool.append(r.pair_id)
    sel["supplement"] = {"declared_after_primary_run": True, "seed": SEED + 1, "pool_size": len(pool), "selected": random.Random(SEED + 1).sample(pool, min(10, len(pool))), "written": time.strftime("%Y-%m-%dT%H:%M:%S")}
    json.dump(sel, open(SEL, "w"), indent=1); print(sel["supplement"])


def variants(v):
    if isinstance(v, bool): return [not v]
    if isinstance(v, int): return [v + 1, v - 1, 0 if v else 1, -v if v else 2]
    if isinstance(v, float): return [v + 1.0, -v, 0.0]
    if isinstance(v, str): return [v[::-1], v[1:], v[:-1], v + v[:1], v.upper()] if v else ["a"]
    if isinstance(v, list):
        out = [v[::-1], v[1:], v[:-1], v + v[:1]]
        try: out.append(sorted(v))
        except TypeError: pass
        for k in range(min(len(v), 2)): out += [v[:k] + [x] + v[k + 1:] for x in variants(v[k])[:2]]
        return out
    if isinstance(v, dict): return [{k: x for k, x in v.items() if k != d} for d in list(v)[:2]]
    return []


def candidates(orig, pair):
    seen, out = {json.dumps(i["args"]) for i in orig}, []
    for i in orig:
        for j, a in enumerate(i["args"]):
            for x in variants(a):
                args = i["args"][:j] + [x] + i["args"][j + 1:]; k = json.dumps(args)
                if k not in seen: seen.add(k); out.append(args)
    random.Random(f"{SEED}|{pair}").shuffle(out)
    return [{"id": f"c{n}", "args": a} for n, a in enumerate(out[:MAX_CAND])]


def engine(t, inputs, d, repeat=None):
    from sbgv8.adapter import load_record
    os.makedirs(d, exist_ok=True); cfg = json.loads(json.dumps(CFG))
    if repeat: cfg["repeat"] = dict(zip(("r_det", "r_replay", "k_alt"), repeat))
    json.dump(inputs, open(d + "/inputs.json", "w")); json.dump(cfg, open(d + "/cfg.json", "w"))
    cmd = [PY, "-m", "sbgv8", "compare", os.path.join(ROOT, t["base"]), os.path.join(ROOT, t["var"]), "--entry", t["entry"], "--inputs", d + "/inputs.json", "--config", d + "/cfg.json", "--out", d]
    for attempt in (0, 1):   # tolerate a transient failure while another agent edits the collector
        if os.path.exists(d + "/evidence.jsonl"): os.remove(d + "/evidence.jsonl")
        t0 = time.time(); r = subprocess.run(cmd, cwd=ROOT, env=ENV, capture_output=True, text=True)
        meta = {"cmd": " ".join(cmd[1:]), "rc": r.returncode, "wall_s": round(time.time() - t0, 2), "attempt": attempt, "stderr_tail": r.stderr[-300:]}
        if os.path.exists(d + "/v8_parts.json"): break
    try:
        rec = load_record(d, project=t["project"], family=t["project"]); rec.pair_id = f"{t['arm']}:{t['pair']}"
        try:
            from sbgv8 import trust
            meta["trust_issues"] = trust.check(d).issues
        except Exception as e: meta["trust_issues"] = f"trust.check failed: {type(e).__name__}: {e}"
        return rec, meta
    except Exception as e:
        meta["error"] = f"{type(e).__name__}: {e}"; return None, meta


def per_pair(t, recs):
    pid, E0 = f"{t['arm']}:{t['pair']}", recs[f"{t['arm']}:{t['pair']}"]; base = os.path.join(RUN, t["arm"], t["pair"]); out = {"pair": pid, "runs": {}, "records": {}}
    def go(name, extra, repeat=None):
        rec, meta = engine(t, t["inputs"] + extra, os.path.join(base, name), repeat) if extra != "probe" else (None, None)
        out["runs"][name] = meta; out["records"][name] = rec.to_json() if rec else None; return rec
    cands = candidates(t["inputs"], pid); out["n_candidates"] = len(cands)
    rec, meta = engine(t, cands, os.path.join(base, "probe")) if cands else (None, {"error": "no candidates derivable"}); out["runs"]["probe"] = meta
    p2, p6 = [], []
    if rec:
        U = uset(rec)
        for i in sorted(rec.inputs, key=lambda i: int(i.input_id[1:])):
            if clean(i) and not i.degenerate and hset(i) and not (hset(i) & U) and len(p2) < K_P2: p2.append(i.input_id)
            if i.outcome == "CONFIRMED_DIFF" and i.deterministic and not i.lossy and not p6: p6.append(i.input_id)
    out["p2_inputs"], out["p6_inputs"] = p2, p6; cmap = {c["id"]: c for c in cands}
    if p2: go("p2", [cmap[i] for i in p2])
    if p6: go("p6", [cmap[i] for i in p6])
    for n, rp in P5_CFG.items(): go("p5_" + n, [], rp)
    return out


def cmd_run(supp=False):
    if not os.path.exists(SEL): sys.exit("selection file missing: run `select` first (selection must be declared before any engine run)")
    sel = json.load(open(SEL)); assert sel["records_sha256"] == sha(DATA), "dev_records changed since selection"
    chosen = sel["supplement"]["selected"] if supp else sel["selected"]
    recs = {r.pair_id: r for r in map(EvidenceRecord.from_json, open(DATA))}; tk = {f"{t['arm']}:{t['pair']}": t for t in tasks()}
    os.makedirs(RUN, exist_ok=True); res = []
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    with ThreadPoolExecutor(WORKERS) as ex:
        for k, o in enumerate(ex.map(lambda p: per_pair(tk[p], recs), chosen)): res.append(o); print(k, o["pair"], {n: (m or {}).get("rc") for n, m in o["runs"].items()}, flush=True)
    json.dump({"git_head": git("rev-parse", "HEAD"), "git_dirty_paths": git("status", "--porcelain", "--", "sbgv8", "experiments/v8").splitlines(), "seed": SEED, "workers": WORKERS,
               "command": "python experiments/v8/run_real_exec_perturbations.py " + ("run_supplement" if supp else "run"), "selection_sha256": sha(SEL), "cfg": CFG, "p5_configs": P5_CFG, "finished": time.strftime("%Y-%m-%dT%H:%M:%S"), "pairs": res},
              open(os.path.join(RUN, "manifest_supplement.json" if supp else "manifest.json"), "w"), indent=1)


def judge(pid, r0, r1, P, tol_note=""):
    d, v0, v1 = P.predict_risk(r1) - P.predict_risk(r0), P.decide(r0)[0], P.decide(r1)[0]
    mono = pid.startswith("P5")
    if mono and v0 == DIV: return None, "orig already divergent", d, v0, v1
    key = "P5" if mono else pid
    ok, why = ers._eval(key, d, v0, v1, build_profile(r0), build_profile(r1), ers.TOL[key]); return ok, why, d, v0, v1


def cmd_analyze():
    man = json.load(open(os.path.join(RUN, "manifest.json"))); sp = os.path.join(RUN, "manifest_supplement.json")
    for o in man["pairs"]: o["cohort"] = "primary"
    if os.path.exists(sp):
        ms = json.load(open(sp)); man["pairs"] += [dict(o, cohort="supplement") for o in ms["pairs"]]; man["supplement_git_head"] = ms["git_head"]
    E = {r.pair_id: r for r in map(EvidenceRecord.from_json, open(DATA))}
    preds = predictors(list(E.values())); info = []; L = lambda s: EvidenceRecord.from_json(s) if s else None; rows, notes = [], []
    for o in man["pairs"]:
        r0, R = E[o["pair"]], {k: L(v) for k, v in o["records"].items()}
        def add(pid, name, r1, why_na=None):
            for pn, P in preds.items():
                if r1 is None: rows.append(dict(pair=o["pair"], cohort=o["cohort"], pid=pid, predictor=pn, status="na", reason=why_na)); continue
                ok, why, d, v0, v1 = judge(pid, r0, r1, P)
                rows.append(dict(pair=o["pair"], cohort=o["cohort"], pid=pid, predictor=pn, status="na" if ok is None else "pass" if ok else "fail", observed=why, delta=d, v0=v0, v1=v1,
                                 reason=why if ok is None else "", class_="b" if pid != "P6" else "c(label/output-blind generator, outcome-conditioned)"))
        U = uset(r0)
        if R.get("p2"):   # integrity of the claim: added inputs touch no changed unit; original inputs reproduce the recorded evidence
            new = [i for i in R["p2"].inputs if i.input_id in o["p2_inputs"]]; assert all(not (hset(i) & uset(R["p2"])) for i in new)
            same = all(next((j.obs_fingerprint, hset(j)) for j in R["p2"].inputs if j.input_id == i.input_id) == (i.obs_fingerprint, hset(i)) for i in r0.inputs if any(j.input_id == i.input_id for j in R["p2"].inputs))
            notes.append(dict(pair=o["pair"], pid="P2", added=len(new), added_hit_changed_unit=0, original_evidence_reproduced=same, verdict_v7b_after=R["p2"].v7b_verdict))
        add("P2", "p2", R.get("p2"), f"no candidate input exercising only unchanged code among {o['n_candidates']} probed" if not o["p2_inputs"] else "p2 run failed")
        add("P6", "p6", R.get("p6"), f"no independently generated discriminating input among {o['n_candidates']} probed candidates" if not o["p6_inputs"] else "p6 run failed")
        for n in ("low", "mid"): add("P5_" + n, "p5_" + n, R.get("p5_" + n), "p5 run failed")
        pr = {n: R.get("p5_" + n) for n in ("low", "mid", "high")}; pr["default"] = r0
        for pn, P in preds.items():   # P5_high = information only (no declared expectation): does MORE identical repetition lower risk (= credited as independent evidence)?
            if pr["high"] is not None: info.append(dict(pair=o["pair"], predictor=pn, delta_high_vs_default=P.predict_risk(pr["high"]) - P.predict_risk(r0), v_default=P.decide(r0)[0], v_high=P.decide(pr["high"])[0]))
        notes.append(dict(pair=o["pair"], pid="P5", per_config={n: (None if r is None else dict(n_rep=build_profile(r)["n_rep"], n_eff=build_profile(r)["n_eff"], repro_frac=build_profile(r)["repro_frac"],
                          verdict=r.v7b_verdict, outcomes=[i.outcome for i in r.inputs], r_cfg=r.config)) for n, r in pr.items()}))
    summ = collections.defaultdict(collections.Counter); reasons = collections.defaultdict(collections.Counter)
    for r in rows:
        k = f"{r['predictor']}|{r['pid']}|{r['cohort']}"; summ[k][r["status"]] += 1
        if r["status"] == "na": reasons[k][(r["reason"] or "")[:90]] += 1
    out = {"rows": rows, "notes": notes, "p5_high_info": info, "p5_high_summary": {pn: dict(n=len(v), risk_decreased=sum(x["delta_high_vs_default"] < -1e-6 for x in v), min=min(x["delta_high_vs_default"] for x in v)) for pn in preds for v in [[x for x in info if x["predictor"] == pn]]}, "summary": {k: dict(**{c: v[c] for c in ("pass", "fail", "na")}, applicable=v["pass"] + v["fail"], total=sum(v.values()), na_reasons=dict(reasons[k])) for k, v in summ.items()}, "n_pairs": len(man["pairs"]), "n_primary": sum(o["cohort"] == "primary" for o in man["pairs"]),
           "git_head": man["git_head"], "seed": man["seed"], "failed_runs": [(o["pair"], n, (m or {}).get("error") or (m or {}).get("rc")) for o in man["pairs"] for n, m in o["runs"].items() if m and (m.get("error") or m.get("rc"))]}
    json.dump(out, open(os.path.join(OUT, "realexec_matrix.json"), "w"), indent=1, default=str)
    md = ["| predictor | P | applicable | pass | fail | N/A | total |", "|---|---|---|---|---|---|---|"]
    for k, v in sorted(out["summary"].items()): p, q, c = k.split("|"); md.append(f"| {p} | {q} ({c}) | {v['applicable']} | {v['pass']} | {v['fail']} | {v['na']} | {v['total']} |")
    open(os.path.join(OUT, "realexec_matrix.md"), "w").write("\n".join(md)); print("\n".join(md)); print("failed runs:", out["failed_runs"])


if __name__ == "__main__":
    {"select": select, "run": cmd_run, "analyze": cmd_analyze, "select_supplement": select_supplement, "run_supplement": lambda: cmd_run(True)}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
