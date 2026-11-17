"""Extract V6 features (and recompute V5) for every pair of a scored set.

  PYTHONHASHSEED=0 python experiments/v6/extract_pairs.py <set>      set in {v8train,v8val,v8test,v10}
Writes artifacts/v6/features_<set>.jsonl (one row per pair; V5 stored scores merged; nothing dropped).
"""
import os, json, pathlib, sys, time, multiprocessing as mp
REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
ART = REPO / "artifacts" / "final"
SETS = {  # set -> (scored file with stored V5 scores, dataset pair file with paths)
    "v8train": ("pairs_v8train_output_free_v8.jsonl", "benchmark/datasets/v8/pairs_train.jsonl"),
    "v8val": ("pairs_v8val_output_free_v8.jsonl", "benchmark/datasets/v8/pairs_val.jsonl"),
    "v8test": ("pairs_v8test_output_free_v8.jsonl", "benchmark/datasets/v8/pairs_test.jsonl"),
    "v10": ("pairs_v10_test_v6exp.jsonl", "benchmark/datasets/v10_independent/pairs_test.jsonl"),
}
STALE = set(json.load(open(REPO / "artifacts/paper_evidence/LABEL_GENERATION_AUDIT.json"))["stale_programs_excluded_from_all_numbers"])


def load(name):
    scored_f, ds_f = SETS[name]
    paths = {r["pair_id"]: r for r in map(json.loads, open(REPO / ds_f))}
    rows = []
    for r in map(json.loads, open(ART / scored_f)):
        if r["base_id"] in STALE or r["pair_id"] not in paths:
            continue
        r["_paths"] = paths[r["pair_id"]]
        if "label" not in r:          # v10 scored file carries no labels: take them from the dataset file, unchanged
            r["label"] = 0 if r["_paths"]["expected_label"] == "EQUIVALENT" else 1
            r["transformation_type"] = r["_paths"]["transformation_type"]
        rows.append(r)
    return rows


def work(group):
    from sbgv6.observe import PythonAdapter
    from sbgv6.distance import pair_record
    from sbgv6 import features as F
    from experiments.final import extraction as X
    ad, out, base = PythonAdapter(), [], None
    for r in group:
        t0 = time.time()
        try:
            base = base or ad.observe(str(REPO / r["_paths"]["base_path"]))
            var = ad.observe(str(REPO / r["_paths"]["variant_path"]))
            rec = pair_record(base, var)
            la, lb = F.changed_lines(base.source, var.source)
            v5 = X.score_pair(base.record, var.record)
            rec["edit_lines"] = len(la) + len(lb)
            rec["v5_recomputed"] = None if v5 is None else v5["sbg_v5"]
        except BaseException as e:  # noqa: BLE001  -> explicit UNKNOWN, never dropped
            rec = {"status": "UNKNOWN", "reasons": ["harness_exception:" + type(e).__name__]}
        stored = r.get("scores") or {}
        out.append({"pair_id": r["pair_id"], "base_id": r["base_id"], "label": r["label"],
                    "transformation_type": r["transformation_type"], "split": r["split"],
                    "v5_stored": stored, "v5_evaluated": r["evaluated"], "secs": round(time.time() - t0, 3), **rec})
    return out


def lost(group, why):
    return [{"pair_id": r["pair_id"], "base_id": r["base_id"], "label": r["label"],
             "transformation_type": r["transformation_type"], "split": r["split"], "v5_stored": r.get("scores") or {},
             "v5_evaluated": r["evaluated"], "secs": None, "status": "UNKNOWN", "reasons": ["worker_lost:" + why]}
            for r in group]


if __name__ == "__main__":
    name = sys.argv[1]
    rows = load(name)
    outf = pathlib.Path(os.environ.get("SBG_V6_OUT", REPO / "artifacts" / "v6")) / f"features_{name}.jsonl"
    done = {json.loads(l)["pair_id"] for l in open(outf)} if outf.exists() else set()
    groups = {}
    for r in rows:
        if r["pair_id"] not in done:
            groups.setdefault(r["base_id"], []).append(r)
    t0, n = time.time(), len(done)
    with mp.Pool(12, maxtasksperchild=4) as pool, open(outf, "a") as f:
        tasks = [[r] for g in groups.values() for r in g] if os.environ.get("SBG_SPLIT") else list(groups.values())
        pend = [(g, pool.apply_async(work, (g,))) for g in tasks]
        for g, ar in pend:
            try:
                res = ar.get(timeout=int(__import__("os").environ.get("SBG_GROUP_TIMEOUT","240")))
            except mp.TimeoutError:
                res = lost(g, "timeout_240s")
            except BaseException as e:  # noqa: BLE001
                res = lost(g, type(e).__name__)
            for o in res:
                f.write(json.dumps(o, default=str) + "\n")
            f.flush(); n += len(res)
            print(f"{name}: {n}/{len(rows)} {time.time()-t0:.0f}s", flush=True)
    print("done", name, n)
