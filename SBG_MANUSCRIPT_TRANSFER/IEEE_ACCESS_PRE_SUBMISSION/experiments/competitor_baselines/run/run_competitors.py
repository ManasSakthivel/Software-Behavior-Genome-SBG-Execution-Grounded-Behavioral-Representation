#!/usr/bin/env python3
"""A4C wave-2: execute every A4B competitor that has a `<name>.READY` file (EXP-A4C-007).

Stages (all resumable; checkpoints per module x population x program):
  scores  --pop P [--only name]   label-free scores of every declared configuration of every READY module        -> EXP-A4C-007/scores/<pop>/<module>/<program>.json
  freeze                          dev selection (highest v9c_dev AUROC per module; ties -> sorted order) + train-Youden thresholds
                                  -> EXP-A4C-007/frozen_config.json  (sha256 must be put in the registry BEFORE `predict` on held-out)
  predict --pop P                 predictions/<pop>/<method>.json for every module x configuration (+ meta)       -> EXP-A4C-007/predictions
  marker                          A4C_PREDICTIONS_READY (wave 2)
NaN policy (A4B returns NaN for "not computable"): NaN -> 0.0 (= no evidence of change) and the number of NaNs is logged per module/population in the meta.
"""
from __future__ import annotations

import argparse
import collections
import importlib
import json
import math
import multiprocessing
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a4c_common as C  # noqa: E402
from a4c_common import RAW, PKG, eval_lib, jdump, jload  # noqa: E402

EXP = "EXP-A4C-007"
NEW = C.NEW


def ready_modules():
    out = {}
    for f in sorted(NEW.glob("*.READY")):
        try:
            info = json.loads(f.read_text())
        except Exception:  # noqa: BLE001
            info = {"raw": f.read_text()[:300]}
        out[f.stem] = info
    return out


def _mod(name):
    if str(NEW) not in sys.path:
        sys.path.insert(0, str(NEW))
    return importlib.import_module(name)


def _score_program(job):
    name, pop, base, rows = job
    out = RAW / EXP / "scores" / pop / name / f"{base}.json"
    if out.exists():
        return name, pop, base, 0.0, True
    t0 = time.time()
    mod = _mod(name)
    import cn_lib
    ctx = cn_lib.Ctx()
    res = {}
    for r in rows:
        b, v = ctx.records(r, pop)
        if hasattr(mod, "score_pair_multi"):
            d = mod.score_pair_multi(b, v, ctx)
        else:
            d = {"default": mod.score_pair(b, v, ctx)}
        res[r["pair_id"]] = {k: (None if (x is None or (isinstance(x, float) and math.isnan(x))) else float(x)) for k, x in d.items()}
    jdump(out, res)
    return name, pop, base, time.time() - t0, False


def stage_scores(pop, only):
    mods = ready_modules()
    if only:
        mods = {k: v for k, v in mods.items() if k in only}
    if not mods:
        print("no READY modules")
        return
    if pop in C.HELD and C.verified_state() is None:
        raise SystemExit("BLOCKED: A4R verification missing; not touching held-out data")
    rows = C.pop_rows(pop)
    excl = set(C.exclusions(pop))
    by = collections.defaultdict(list)
    for r in rows:
        if r["base_id"] not in excl:
            by[r["base_id"]].append(r)
    jobs = [(n, pop, b, by[b]) for n in mods for b in sorted(by)]
    t = time.time()
    with multiprocessing.get_context("fork").Pool(3) as pool:
        for name, p, base, sec, skipped in pool.imap_unordered(_score_program, jobs):
            print(f"  {name:28s} {p} {base:32s} {'(ckpt)' if skipped else f'{sec:.1f}s'}", flush=True)
    print(f"{pop}: {len(jobs)} module-programs in {time.time() - t:.0f}s")


def load_scores(pop, name):
    d = RAW / EXP / "scores" / pop / name
    out = {}
    for f in sorted(d.glob("*.json")):
        out.update(jload(f))
    return out


def assemble(pop, name):
    """rows (primary, program has trace cache) + {config: [scores]}; NaN -> 0.0 and counted"""
    excl = set(C.exclusions(pop))
    sc = load_scores(pop, name)
    rows = [r for r in C.pop_rows(pop) if r["base_id"] not in excl and r["pair_id"] in sc]
    cfgs = sorted({k for r in rows for k in sc[r["pair_id"]]})
    cols, nn = {}, {}
    for k in cfgs:
        raw = [sc[r["pair_id"]].get(k) for r in rows]
        nn[k] = sum(1 for x in raw if x is None)
        cols[k] = [0.0 if x is None else x for x in raw]
    return rows, cols, nn


def stage_freeze():
    mods = ready_modules()
    frozen = {"modules": {}, "ready_info": mods, "policy": "per module: representative = highest v9c_dev AUROC config (ties -> sorted order); Youden threshold on v9c_train(reduced) scores of the same config"}
    for name in mods:
        rt, ct, nt = assemble("v9c_train", name)
        rd, cd, nd = assemble("v9c_dev", name)
        if not rt or not rd:
            frozen["modules"][name] = {"status": "NO_SCORES"}
            continue
        yt, yd = C.labels(rt), C.labels(rd)
        tab = {k: {"train_auroc": eval_lib.auroc(ct[k], yt), "dev_auroc": eval_lib.auroc(cd[k], yd), "thr": eval_lib.youden_threshold(ct[k], yt), "n_nan_train": nt[k], "n_nan_dev": nd[k]}
               for k in sorted(ct)}
        rep = max(sorted(tab), key=lambda k: round(tab[k]["dev_auroc"], 12))
        frozen["modules"][name] = {"configs": tab, "representative": rep}
    jdump(RAW / EXP / "frozen_config.json", frozen)
    jdump(RAW / EXP / "frozen_config_modules_sha.json", {n: C.sha256_file(NEW / f"{n}.py") for n in mods} | {"cn_lib": C.sha256_file(NEW / "cn_lib.py")})
    print("frozen sha256", C.sha256_file(RAW / EXP / "frozen_config.json"))
    for n, v in frozen["modules"].items():
        if "representative" in v:
            print(f"  {n:28s} rep={v['representative']:40s} dev {v['configs'][v['representative']]['dev_auroc']:.4f} ({len(v['configs'])} configs)")


def stage_predict(pop):
    fc = RAW / EXP / "frozen_config.json"
    if pop in C.HELD and (not fc.exists() or C.sha256_file(fc) not in C.REG.read_text()):
        raise SystemExit("BLOCKED: wave-2 frozen_config.json sha256 not registered")
    frozen = jload(fc)
    pdir = RAW / EXP / "predictions" / pop
    pdir.mkdir(parents=True, exist_ok=True)
    meta_path = RAW / EXP / "predictions" / "meta.json"
    meta = jload(meta_path)["methods"] if meta_path.exists() else {}
    for name, fm in frozen["modules"].items():
        if "configs" not in fm:
            continue
        rows, cols, nn = assemble(pop, name)
        for k, s in cols.items():
            safe = f"{name}__{k}".replace("|", "__").replace("*", "").replace("/", "_").replace(" ", "")
            fp = pdir / f"{safe}.json"
            if not fp.exists():
                fp.write_text(json.dumps({"method": f"{name}|{k}", "population": pop, "orientation": "higher=CHANGED",
                                          "rows": [{"pair_id": r["pair_id"], "base_id": r["base_id"], "label": r["label"], "group": r["group"], "score": x} for r, x in zip(rows, s)]}))
            info = frozen["ready_info"].get(name, {})
            m = meta.setdefault(safe, {"method": f"{name}|{k}", "family": f"A4B:{name}", "role": "competitor_representative" if k == fm["representative"] else "competitor",
                                       "class": info.get("class") if isinstance(info, dict) else None,
                                       "label": "ADAPTED", "privileged_output_reading": "outreading" in name or "diffexec" in name or "oracle" in name,
                                       "orientation": "higher=CHANGED", "train_threshold_youden": fm["configs"][k]["thr"], "train_auroc": fm["configs"][k]["train_auroc"],
                                       "dev_auroc": fm["configs"][k]["dev_auroc"], "config": k, "code_sha256": C.sha256_file(NEW / f"{name}.py"),
                                       "frozen_config_sha256": C.sha256_file(fc), "ready": info})
            m.setdefault("n_nan", {})[pop] = nn[k]
        print(pop, name, "ok")
    jdump(meta_path, {"experiment": EXP, "frozen_config": str(fc.relative_to(PKG)), "methods": meta})


def stage_marker():
    base = RAW / EXP
    need = {p: len(list((base / "predictions" / p).glob("*.json"))) for p in C.HELD}
    if any(n < 1 for n in need.values()):
        raise SystemExit(f"not complete: {need}")
    (base / "A4C_PREDICTIONS_READY").write_text(json.dumps({"wave": 2, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "files": need,
                                                           "frozen_config_sha256": C.sha256_file(base / "frozen_config.json")}, indent=1))
    print("marker", need)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--pop")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    if a.stage == "scores":
        stage_scores(a.pop, [x for x in a.only.split(",") if x])
    elif a.stage == "freeze":
        stage_freeze()
    elif a.stage == "predict":
        stage_predict(a.pop)
    elif a.stage == "marker":
        stage_marker()
