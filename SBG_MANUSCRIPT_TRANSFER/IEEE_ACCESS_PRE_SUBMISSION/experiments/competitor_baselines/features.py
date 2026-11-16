"""EXP-A4-002 feature computation: every label-free baseline score for every primary pair of a population (one pass per program)."""
from __future__ import annotations

import collections
import pickle
import time

import b02_static
import b03_execstats
import b04_valuespectra
import b05_pathspectra
import b05_traceseq
from bl_common import FileTrace, eval_lib

_IDF = {}


def init_worker(idf_path):
    with open(idf_path, "rb") as f:
        _IDF.update(pickle.load(f))


def unique_paths(rows):
    s = []
    seen = set()
    for r in rows:
        for k in ("base_path", "variant_path"):
            if r[k] not in seen:
                seen.add(r[k])
                s.append((r["base_id"], r[k]))
    return s


def fit_idfs(pop_rows, pop="v9c_train"):
    """Unsupervised document-frequency tables from the TRAIN split only."""
    feat = b02_static.StaticFeaturizer()
    paths = [r["base_path"] for r in pop_rows] + [r["variant_path"] for r in pop_rows]
    static_idf = b02_static.fit_idf(feat, paths)
    fts = [FileTrace(pop, b, p) for b, p in unique_paths(pop_rows)]
    return {"static": static_idf, "trace": b05_traceseq.fit_idf(fts)}


def compute_program(job):
    pop, rows = job
    t0 = time.time()
    feat = b02_static.StaticFeaturizer(_IDF["static"])
    ft = {}

    def get(base_id, path):
        if path not in ft:
            ft[path] = FileTrace(pop, base_id, path)
        return ft[path]
    out = {}
    for r in rows:
        a, b = get(r["base_id"], r["base_path"]), get(r["base_id"], r["variant_path"])
        f = dict(feat.pair(r["base_path"], r["variant_path"]))
        f = {f"static|{k}": v for k, v in f.items()}
        if a.ok and b.ok:
            f.update(b03_execstats.exec_features(a, b))
            f.update(b05_traceseq.pair_features(a, b, _IDF["trace"]))
            f.update(b05_pathspectra.pair_features(a, b))
            f.update(b04_valuespectra.pair_features(a, b))
            f.update(b03_execstats.oracle_features(a, b))
            f["_trace_ok"] = 1.0
        else:
            f["_trace_ok"] = 0.0
        out[r["pair_id"]] = f
    return {"base_id": rows[0]["base_id"], "features": out, "seconds": time.time() - t0, "extract_seconds": {p: x.extract_seconds for p, x in ft.items()}}
