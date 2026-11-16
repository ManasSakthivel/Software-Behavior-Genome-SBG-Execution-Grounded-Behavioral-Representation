"""sanity_labels.py -- label-using sanity check of the A4B modules on v9c_train / v9c_dev ONLY (never v9c_val / v10_test: refused).

usage: python sanity_labels.py <module_name> [<pop> ...] [--limit N]  -> prints AUROC per multi-config; writes results/raw/EXP-A4B-001/sanity_<module>_<pop>.json
Scores are computed with the module's own score_pair_multi(); AUROC = eval_lib.auroc (tie-aware).  No bootstrap (sanity only).
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

sys.path.insert(0, str(L.PKG / "experiments" / "common"))
import eval_lib  # noqa: E402

ALLOWED = ("v9c_train", "v9c_dev")


def run(modname, pops, limit=None, outdir=None):
    mod = importlib.import_module(modname)
    ctx = L.Ctx()
    res = {}
    for pop in pops:
        if pop not in ALLOWED:
            raise SystemExit(f"REFUSED: labels may not be joined to scores on {pop}")
        rows = [r for r in ctx.population(pop) if r.get("in_primary_population")]
        if limit:
            import random
            rows = random.Random(42).sample(rows, min(limit, len(rows)))
        cols, ys, t0, nan = {}, [], time.time(), 0
        for r in rows:
            b, v = ctx.records(r, pop)
            try:
                m = mod.score_pair_multi(b, v, ctx)
            except Exception as e:  # noqa: BLE001
                m = {"__error__": float("nan")}
                print("ERR", r["pair_id"], type(e).__name__, e, file=sys.stderr)
            m = dict(m)
            m["__default__"] = mod.score_pair(b, v, ctx)
            for k, x in m.items():
                cols.setdefault(k, []).append(x)
            ys.append(r["label"])
        out = {"n_rows": len(rows), "seconds_per_pair": (time.time() - t0) / max(1, len(rows)), "auroc": {}, "n_nan": {}}
        for k, xs in cols.items():
            ok = [(x, y) for x, y in zip(xs, ys) if not (isinstance(x, float) and math.isnan(x))]
            out["n_nan"][k] = len(xs) - len(ok)
            out["auroc"][k] = round(eval_lib.auroc([a for a, _ in ok], [b for _, b in ok]), 4) if ok else None
        res[pop] = out
        print(modname, pop, json.dumps(out["auroc"], indent=0), "s/pair=%.3f" % out["seconds_per_pair"], "nan:", {k: v for k, v in out["n_nan"].items() if v})
        d = pathlib.Path(outdir or (L.PKG / "results" / "raw" / "EXP-A4B-001"))
        d.mkdir(parents=True, exist_ok=True)
        (d / f"sanity_{modname}_{pop}.json").write_text(json.dumps(out, indent=1, sort_keys=True))
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    lim = None
    if "--limit" in a:
        i = a.index("--limit")
        lim = int(a[i + 1])
        del a[i:i + 2]
    run(a[0], a[1:] or list(ALLOWED), lim)
