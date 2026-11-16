#!/usr/bin/env python3
"""A4C driver (EXP-A4C-001..003).  Stages (each is resumable; checkpoints per program / model / method):

  modules                      write module manifest (sha256, predecessor|fixed)
  idf                          fit unsupervised IDF tables on v9c_train (programs that HAVE a trace cache only)   -> EXP-A4C-001/idf.pkl
  features  --pop P            label-free baseline features of every primary pair (per program checkpoint)           -> EXP-A4C-001/features/<pop>/<base>.json
  indep     --pop P            independent-input batteries + execution + pair scores (B06b)                           -> EXP-A4C-001/indep/
  fit                          fit on v9c_train, select on v9c_dev, FREEZE                                            -> EXP-A4C-002/{frozen_config.json,selection.json,models.pkl}
  predict   --pop P            write predictions/<pop>/<method>.json for every method (held-out only after the freeze is registered) -> EXP-A4C-003/predictions
  marker                       create A4C_PREDICTIONS_READY once both held-out populations are complete

Run: PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 <py313> run_all.py --stage <stage> [--pop P] [--allow-provisional]
`--allow-provisional` permits running UNVERIFIED predecessor modules on v9c_train/v9c_dev ONLY (never on held-out data).
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import gzip
import hashlib
import json
import multiprocessing
import pathlib
import pickle
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a4c_common as C  # noqa: E402
from a4c_common import RAW, PKG, EXP_FEAT, EXP_FIT, EXP_PRED, eval_lib, jdump, jload  # noqa: E402

PY = sys.executable
WORKERS = 3
_G = {}


# ------------------------------------------------------------------ setup / guards
def setup(pops, allow_provisional):
    """Choose module dirs; refuse to touch held-out populations with unverified code."""
    v = C.verified_state()
    held = [p for p in pops if p in C.HELD]
    if v is None:
        if held:
            raise SystemExit(f"BLOCKED: held-out population(s) {held} requested but A4R VERIFIED_BASELINES.json is not published")
        if not allow_provisional:
            raise SystemExit("A4R verification not published; pass --allow-provisional to run predecessor modules on v9c_train/v9c_dev only")
        C.setup_modules(False)
        return {"provisional": True}
    use_fixed = bool(v.get("use_fixed_modules", True)) if isinstance(v, dict) else True
    C.setup_modules(use_fixed)
    return {"provisional": False, "verified_file_sha256": C.sha256_file(C.VERIFIED)}


def import_modules():
    global F, B6, bl
    import features as F  # noqa: F811
    import b06_indep_inputs as B6  # noqa: F811
    import bl_common as bl  # noqa: F811


# ------------------------------------------------------------------ stage: modules
def stage_modules():
    man = C.module_manifest()
    out = RAW / EXP_FEAT / "module_manifest.json"
    jdump(out, {"modules": man, "code_sha256": C.code_sha(), "python": sys.version, "verified_file": str(C.VERIFIED) if C.VERIFIED.exists() else None})
    print(json.dumps(man, indent=1))


# ------------------------------------------------------------------ stage: idf
def train_rows_with_cache():
    rows = C.pop_rows("v9c_train")
    excl = C.exclusions("v9c_train")
    return [r for r in rows if r["base_id"] not in excl], excl


def stage_idf():
    rows, excl = train_rows_with_cache()
    t = time.time()
    idf = F.fit_idfs(rows)
    out = RAW / EXP_FEAT / "idf.pkl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump(idf, f)
    print(f"idf fitted on {len(rows)} train rows (excluded programs without trace cache: {excl}) in {time.time() - t:.1f}s -> {out}")
    jdump(RAW / EXP_FEAT / "idf_meta.json", {"n_rows": len(rows), "excluded_programs": excl, "sha256": C.sha256_file(out)})


# ------------------------------------------------------------------ stage: features
def _feat_job(job):
    pop, base, rows = job
    out = C.feat_dir(pop) / f"{base}.json"
    if out.exists():
        return base, 0.0, True
    r = F.compute_program((pop, rows))
    jdump(out, r["features"])
    jdump(C.feat_dir(pop) / f"_extract_{base}.json.meta", r["extract_seconds"])
    return base, r["seconds"], False


def stage_features(pop):
    rows = C.pop_rows(pop)
    excl = set(C.exclusions(pop))
    by = collections.defaultdict(list)
    for r in rows:
        if r["base_id"] not in excl:
            by[r["base_id"]].append(r)
    jobs = [(pop, b, by[b]) for b in sorted(by)]
    t = time.time()
    with multiprocessing.get_context("fork").Pool(WORKERS, initializer=F.init_worker, initargs=(str(RAW / EXP_FEAT / "idf.pkl"),)) as pool:
        for base, sec, skipped in pool.imap_unordered(_feat_job, jobs):
            print(f"  {pop} {base:34s} {'(checkpoint)' if skipped else f'{sec:.1f}s'}", flush=True)
    feats = C.load_features(pop)
    n_bad = sum(1 for v in feats.values() if not v.get("_trace_ok"))
    jdump(RAW / EXP_FEAT / f"features_{pop}_summary.json", {"pop": pop, "n_pairs_with_features": len(feats), "n_primary": len(rows), "excluded_programs": sorted(excl),
                                                         "n_excluded_pairs": sum(1 for r in rows if r["base_id"] in excl), "n_trace_not_ok": n_bad, "seconds": time.time() - t})
    print(f"{pop}: {len(feats)} pairs featurised, excluded programs {sorted(excl)}, trace-not-ok {n_bad}, {time.time() - t:.0f}s")


# ------------------------------------------------------------------ stage: indep (B06b)
def _sub(cmd, timeout):
    t = time.time()
    try:
        o = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env={"PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"},
                           cwd=str(C.module_dir_for("b06_indep_inputs")))
        return o.returncode, o.stderr[-300:], time.time() - t
    except subprocess.TimeoutExpired:
        return -9, "TIMEOUT", time.time() - t


def _entry_of(pop, base_id, path):
    with gzip.open(bl.cache_file(pop, base_id, path), "rt") as f:
        return json.load(f).get("entry_function")


def _runfile(root, pop, base_id, path):
    return root / "runs" / pop / base_id / (hashlib.sha1(path.encode()).hexdigest()[:12] + "__" + pathlib.Path(path).stem + ".json")


def stage_indep(pop):
    root = RAW / EXP_FEAT / "indep"
    (root / "batteries").mkdir(parents=True, exist_ok=True)
    b6 = str(C.module_dir_for("b06_indep_inputs") / "b06_indep_inputs.py")
    rows = C.pop_rows(pop)
    excl = set(C.exclusions(pop))
    bases = {}
    for r in rows:
        if r["base_id"] not in excl:
            bases.setdefault(r["base_id"], r["base_path"])
    log = []
    jobs = []
    for b, p in sorted(bases.items()):
        out = root / "batteries" / f"{pop}__{b}.json"
        if not out.exists():
            jobs.append((b, [PY, b6, "battery", p, _entry_of(pop, b, p), b, str(out)]))
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as ex:
        for (b, _), (rc, err, dt) in zip(jobs, ex.map(lambda j: _sub(j[1], 300), jobs)):
            log.append({"pop": pop, "base": b, "stage": "battery", "rc": rc, "err": err, "s": round(dt, 2)})
    files = {}
    for r in rows:
        if r["base_id"] in bases:
            for k in ("base_path", "variant_path"):
                files[(r["base_id"], r[k])] = None
    rjobs = []
    for (b, p) in sorted(files):
        bat = root / "batteries" / f"{pop}__{b}.json"
        if not bat.exists() or json.loads(bat.read_text())["status"] != "ok":
            continue
        out = _runfile(root, pop, b, p)
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.exists():
            rjobs.append((out, [PY, b6, "run", p, _entry_of(pop, b, p) or "", str(bat), str(out)]))
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as ex:
        for (out, _), (rc, err, dt) in zip(rjobs, ex.map(lambda j: _sub(j[1], 120), rjobs)):
            if rc or not out.exists():
                out.write_text(json.dumps({"status": f"worker_fail:{rc}:{err}", "per_input": [], "n": 0, "wall_parent_s": dt}))
                log.append({"pop": pop, "file": out.name, "rc": rc, "err": err})
            else:
                d = json.loads(out.read_text())
                d["wall_parent_s"] = dt
                out.write_text(json.dumps(d))
    print(f"{pop}: executed {len(rjobs)} files in {time.time() - t0:.0f}s")
    scores, n_blocked = {}, 0
    for r in rows:
        bat = root / "batteries" / f"{pop}__{r['base_id']}.json"
        if r["base_id"] not in bases or not bat.exists() or json.loads(bat.read_text())["status"] != "ok":
            n_blocked += 1
            continue
        ra = json.loads(_runfile(root, pop, r["base_id"], r["base_path"]).read_text())
        rb = json.loads(_runfile(root, pop, r["base_id"], r["variant_path"]).read_text())
        s = B6.pair_scores(ra, rb)
        if s:
            scores[r["pair_id"]] = s
    jdump(root / f"indep_{pop}.json", scores)
    jdump(root / f"indep_log_{pop}.json", log)
    print(f"{pop}: indep-covered {len(scores)}/{len(rows)} (not covered: {len(rows) - len(scores)}), failures logged {len(log)}")


# ------------------------------------------------------------------ stage: fit  (train fit, dev selection, freeze)
def fast_youden(s, y):
    """Identical semantics to eval_lib.youden_threshold (scan ascending thresholds, replace only on strict improvement) in O(n log n)."""
    P, N = sum(y), len(y) - sum(y)
    order = sorted(range(len(s)), key=lambda i: s[i])
    vals = sorted(set(s))
    # suffix counts via a sweep over unique values ascending
    pos_below = neg_below = 0
    idx = 0
    best, thr = -2.0, None
    n = len(order)
    for v in vals:
        tp, fp = P - pos_below, N - neg_below
        j = (tpr := tp / P) - (fpr := fp / N)
        if j > best + 1e-12:
            best, thr = j, v
        while idx < n and s[order[idx]] == v:
            if y[order[idx]] == 1:
                pos_below += 1
            else:
                neg_below += 1
            idx += 1
    return thr


def _fit_job(spec):
    import a4c_methods as M
    import models
    rows = _G["train"]
    kind, payload = spec
    if kind == "lr":
        X = [[r["S"].get(f, 0.0) for f in payload] for r in rows]
        return spec, eval_lib.fit_logistic(X, C.labels(rows))
    _, kd, fs = payload.split("|")
    k, d = kd.split("_d")
    X = [[r["S"].get(f, 0.0) for f in M.FEATS[fs]] for r in rows]
    y = C.labels(rows)
    m = models.Tree(int(d), 10).fit(X, y) if k == "DT" else models.Forest(50, int(d), 42).fit(X, y)
    return spec, {"kind": k, "model": m, "feats": M.FEATS[fs]}


def fit_models(specs, ckpt):
    """Fit missing specs in a fork pool (<=WORKERS), checkpointing every model."""
    todo = [s for s in specs if not (ckpt / (C.sha256_str(repr(s))[:16] + ".pkl")).exists()]
    ckpt.mkdir(parents=True, exist_ok=True)
    if todo:
        with multiprocessing.get_context("fork").Pool(WORKERS) as pool:
            for spec, m in pool.imap_unordered(_fit_job, todo):
                with open(ckpt / (C.sha256_str(repr(spec))[:16] + ".pkl"), "wb") as f:
                    pickle.dump(m, f)
                print("   fitted", spec[0], spec[1] if isinstance(spec[1], str) else "+".join(spec[1]), flush=True)
    out = {}
    for s in specs:
        with open(ckpt / (C.sha256_str(repr(s))[:16] + ".pkl"), "rb") as f:
            out[s] = pickle.load(f)
    return out


def attach_models(rows, Mdl, train=False, inc=None):
    import a4c_methods as M
    for name, fs in M.MODEL_NAMES.items():
        m = Mdl[("lr", tuple(M.FEATS[fs]))]
        for r in rows:
            r["S"][name] = eval_lib.logit_score(m, [r["S"].get(f, 0.0) for f in M.FEATS[fs]])
    for spec in M.FOREST_SPECS:
        tm = Mdl[("tree", spec)]
        X = [[r["S"].get(f, 0.0) for f in tm["feats"]] for r in rows]
        sc = tm["model"].oob_scores(X) if (train and tm["kind"] == "RF") else [tm["model"].predict(x) for x in X]
        for r, v in zip(rows, sc):
            r["S"][spec] = v
    for name, feats in (inc or {}).items():
        m = Mdl[("lr", tuple(feats))]
        for r in rows:
            r["S"][name] = eval_lib.logit_score(m, [r["S"].get(f, 0.0) for f in feats])


def stage_fit():
    import a4c_methods as M
    t0 = time.time()
    tr, drop_tr = C.assemble("v9c_train")
    dv, drop_dv = C.assemble("v9c_dev")
    print("train", len(tr), "dev", len(dv), "dropped", len(drop_tr), len(drop_dv))
    _G["train"] = tr
    ck = RAW / EXP_FIT / "models_ckpt"
    base_specs = [("lr", tuple(M.FEATS[fs])) for fs in M.MODEL_NAMES.values()] + [("tree", s) for s in M.FOREST_SPECS]
    Mdl = fit_models(base_specs, ck)
    attach_models(tr, Mdl, train=True)
    attach_models(dv, Mdl, train=False)
    ytr, ydv = C.labels(tr), C.labels(dv)
    keys = [k for k in M.all_config_keys() if k in tr[0]["S"] and k in dv[0]["S"]]
    table = {k: {"train_auroc": eval_lib.auroc(C.col(tr, k), ytr), "dev_auroc": eval_lib.auroc(C.col(dv, k), ydv)} for k in keys}
    fams = M.families()
    sel = {}
    for fam, cs in fams.items():
        cs = [c for c in cs if c in table]
        best = max(cs, key=lambda c: (round(table[c]["dev_auroc"], 12), -cs.index(c)))
        sel[fam] = {"representative": best, "dev_auroc": table[best]["dev_auroc"], "candidates": {c: table[c]["dev_auroc"] for c in cs}}
    xkey = lambda x: sel[x]["representative"] if x.endswith("*") else x  # noqa: E731
    inc_names = {}
    for bname in ("EX", "EXx"):
        for x in M.INC_X:
            inc_names[f"INC|{bname}+{xkey(x)}"] = M.FEATS[bname] + [xkey(x)]
    Mdl.update(fit_models(list(dict.fromkeys(("lr", tuple(f)) for f in inc_names.values())), ck))
    attach_models(tr, Mdl, train=True, inc=inc_names)
    attach_models(dv, Mdl, train=False, inc=inc_names)
    all_keys = list(dict.fromkeys(keys + list(inc_names)))
    thr = {k: fast_youden(C.col(tr, k), ytr) for k in all_keys}
    # fast_youden must agree with eval_lib.youden_threshold (spot check)
    for k in ("sbg_v5", "edit", "LR_EX"):
        assert thr[k] == eval_lib.youden_threshold(C.col(tr, k), ytr), k
    for k in inc_names:
        table[k] = {"train_auroc": eval_lib.auroc(C.col(tr, k), ytr), "dev_auroc": eval_lib.auroc(C.col(dv, k), ydv)}
    summ = jload(PKG / "configs" / "populations" / "SUMMARY.json")
    frozen = {"representatives": {f: sel[f]["representative"] for f in sel}, "thresholds_train_youden": thr, "inc_names": inc_names,
              "population_sha256": {p: summ[p]["sha256"] for p in summ}, "train_n": len(tr), "train_excluded_programs": C.exclusions("v9c_train"),
              "dev_n": len(dv), "module_manifest": C.module_manifest(), "code_sha256": C.code_sha(),
              "policy": "representative = highest v9c_dev AUROC within family (ties -> declared order); thresholds = Youden on v9c_train(reduced) scores of the same predictor (RF: OOB scores)"}
    out = RAW / EXP_FIT
    jdump(out / "selection.json", sel)
    jdump(out / "config_train_dev_auroc.json", table)
    jdump(out / "frozen_config.json", frozen)
    with open(out / "models.pkl", "wb") as f:
        pickle.dump(Mdl, f)
    sha = C.sha256_file(out / "frozen_config.json")
    print("fit+selection done in", round(time.time() - t0), "s;  frozen_config sha256", sha, " models.pkl sha256", C.sha256_file(out / "models.pkl"))
    for f, v in sel.items():
        print(f"  {f:26s} rep={v['representative']:50s} dev AUROC {v['dev_auroc']:.4f}")


# ------------------------------------------------------------------ stage: predict
def frozen_registered(sha):
    return C.REG.exists() and sha in C.REG.read_text()


def stage_predict(pop):
    import a4c_methods as M
    out = RAW / EXP_FIT
    fc_path = out / "frozen_config.json"
    if pop in C.HELD:
        if not fc_path.exists() or not frozen_registered(C.sha256_file(fc_path)):
            raise SystemExit("BLOCKED: frozen_config.json missing or its sha256 is not in the A4C registry; freeze before scoring held-out data")
    frozen = jload(fc_path)
    with open(out / "models.pkl", "rb") as f:
        Mdl = pickle.load(f)
    rows, dropped = C.assemble(pop, drop_trace_missing=(pop in ("v9c_train", "v9c_dev")))
    attach_models(rows, Mdl, train=(pop == "v9c_train"), inc=frozen["inc_names"])
    keys = [k for k in M.all_config_keys() + list(frozen["inc_names"]) if k in rows[0]["S"]]
    if pop != "v10_test":
        keys = [k for k in keys if k not in ("sbg_v6", "sbg_state_v6")]
    pdir = RAW / EXP_PRED / "predictions" / pop
    pdir.mkdir(parents=True, exist_ok=True)
    n_new = 0
    for k in keys:
        fp = pdir / f"{M.safe(k)}.json"
        if fp.exists():
            continue
        rowsout = [{"pair_id": r["pair_id"], "base_id": r["base_id"], "label": r["label"], "group": r["group"], "score": r["S"].get(k, 0.0)} for r in rows]
        fp.write_text(json.dumps({"method": k, "population": pop, "orientation": "higher=CHANGED", "rows": rowsout}))
        n_new += 1
    jdump(pdir / "_population_info.json", {"pop": pop, "n_rows": len(rows), "n_dropped_missing_trace": len(dropped), "dropped": dropped[:50],
                                           "indep_covered": sum(1 for r in rows if r.get("_indep_covered")), "n_methods": len(keys)})
    print(f"{pop}: {n_new} new prediction files ({len(keys)} methods, {len(rows)} rows, dropped {len(dropped)})")


def stage_meta():
    """predictions/meta.json: per-method metadata (code sha256, config, orientation, train threshold, family/role/label)."""
    import a4c_methods as M
    out = RAW / EXP_FIT
    frozen = jload(out / "frozen_config.json")
    fam_of = M.family_of()
    reps = set(frozen["representatives"].values())
    cs = jload(out / "config_train_dev_auroc.json")
    meta = {}
    for k in sorted(cs):
        fam = fam_of.get(k, "incremental" if k.startswith("INC|") else "other")
        role = "reference" if k in M.SBG_REFS else "representative" if k in reps else "diagnostic" if fam.startswith("diag:") else "incremental" if k.startswith("INC|") else "exploratory"
        meta[M.safe(k)] = {"method": k, "family": fam, "role": role, "class": M.FAMILY_CLASS.get(fam), "label": M.label_of(k), "privileged_output_reading": M.privileged(k),
                           "orientation": "higher=CHANGED", "train_threshold_youden": frozen["thresholds_train_youden"].get(k),
                           "train_auroc": cs[k]["train_auroc"], "dev_auroc": cs[k]["dev_auroc"], "config": k if not k.startswith("INC|") else {"features": frozen["inc_names"][k]},
                           "representative_of": sorted(f for f, rk in frozen["representatives"].items() if rk == k),
                           "code_sha256": frozen["code_sha256"], "frozen_config_sha256": C.sha256_file(out / "frozen_config.json")}
    jdump(RAW / EXP_PRED / "predictions" / "meta.json", {"experiment": EXP_PRED, "frozen_config": str((out / "frozen_config.json").relative_to(PKG)),
                                                         "train_excluded_programs": frozen["train_excluded_programs"], "methods": meta})
    print("meta.json:", len(meta), "methods")


def stage_marker():
    base = RAW / EXP_PRED
    need = {p: len(list((base / "predictions" / p).glob("*.json"))) for p in C.HELD}
    if any(n < 100 for n in need.values()):
        raise SystemExit(f"not complete: {need}")
    stage_meta()
    (base / "A4C_PREDICTIONS_READY").write_text(json.dumps({"wave": 1, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "files": need,
                                                           "meta": "predictions/meta.json", "frozen_config_sha256": C.sha256_file(RAW / EXP_FIT / "frozen_config.json")}, indent=1))
    print("marker written", need)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--pop", default=None)
    ap.add_argument("--allow-provisional", action="store_true")
    a = ap.parse_args()
    pops = [a.pop] if a.pop else list(C.POPS)
    needs_held = a.stage in ("features", "indep", "predict") and any(p in C.HELD for p in pops)
    if a.stage in ("idf", "fit"):
        pops = ["v9c_train", "v9c_dev"]
    info = setup(pops if a.stage in ("features", "indep", "idf", "fit", "predict") else [], a.allow_provisional)
    if a.stage in ("idf", "features", "indep"):
        import_modules()
    if a.stage == "modules":
        stage_modules()
    elif a.stage == "idf":
        stage_idf()
    elif a.stage == "features":
        for p in pops:
            stage_features(p)
    elif a.stage == "indep":
        for p in pops:
            stage_indep(p)
    elif a.stage == "fit":
        stage_fit()
    elif a.stage == "predict":
        for p in pops:
            stage_predict(p)
    elif a.stage == "meta":
        stage_meta()
    elif a.stage == "marker":
        stage_marker()
    else:
        raise SystemExit("unknown stage")
