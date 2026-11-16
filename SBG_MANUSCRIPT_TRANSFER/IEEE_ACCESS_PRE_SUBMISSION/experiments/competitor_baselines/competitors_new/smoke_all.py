"""smoke_all.py -- LABEL-FREE smoke run of a module on all four populations (crash / NaN-rate / timing check; labels are never read; no scores are stored).

usage: python smoke_all.py <module> [--limit-per-pop N]  -> results/raw/EXP-A4B-001/smoke_<module>.json
"""
from __future__ import annotations

import importlib
import json
import math
import sys
import time
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cn_lib as L  # noqa: E402


def run(modname, limit=None):
    mod = importlib.import_module(modname)
    ctx = L.Ctx()
    out = {"module": modname, "pops": {}}
    for pop in L.POPS:
        rows = [r for r in ctx.population(pop) if r.get("in_primary_population")]
        if limit:
            rows = rows[:limit]
        n_nan = n_err = 0
        vals = set()
        t0 = time.time()
        errs = []
        for r in rows:
            b, v = ctx.records(r, pop)
            try:
                x = mod.score_pair(b, v, ctx)
            except Exception as e:  # noqa: BLE001
                n_err += 1
                errs.append(f"{r['pair_id']}: {type(e).__name__}: {e}"[:200])
                continue
            if isinstance(x, float) and math.isnan(x):
                n_nan += 1
            else:
                vals.add(round(x, 9))
        dt = time.time() - t0
        out["pops"][pop] = {"n": len(rows), "n_nan": n_nan, "n_err": n_err, "distinct_values": len(vals), "seconds": round(dt, 2), "s_per_pair": round(dt / max(1, len(rows)), 5),
                            "first_errors": errs[:3]}
        print(modname, pop, out["pops"][pop], flush=True)
    d = L.PKG / "results" / "raw" / "EXP-A4B-001"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"smoke_{modname}.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    lim = None
    if "--limit-per-pop" in a:
        i = a.index("--limit-per-pop")
        lim = int(a[i + 1])
        del a[i:i + 2]
    run(a[0], lim)
