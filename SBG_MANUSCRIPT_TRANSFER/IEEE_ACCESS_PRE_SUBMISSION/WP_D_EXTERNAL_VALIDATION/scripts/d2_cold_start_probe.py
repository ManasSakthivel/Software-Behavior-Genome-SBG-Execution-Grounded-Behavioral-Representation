#!/usr/bin/env python3
"""WP-D / D2 Task D: cold-start / self-distance probe, re-implemented from the description in
artifacts/paper_evidence/raw/cold_start_probe.json (the original /tmp/sd_probe.py is not in the repo).

Within ONE process: N consecutive extract_program() calls on the same unit (protocol
output_free_v8), re.purge() before each; records n_events of each and the sbg_v5 distance
between every pair of consecutive extractions (extraction 1 vs 2 = the 'self distance' that
rescore_external_v8 reports as base_self_distance_v5).

    d2_cold_start_probe.py COPY_ROOT N_CALLS REL_UNIT [REL_UNIT ...]   (prints one JSON line)
Run under different PYTHONHASHSEED values / interpreters by d2_run.py.
"""
import json
import os
import re
import sys

root, n_calls = sys.argv[1], int(sys.argv[2])
units = sys.argv[3:]
sys.path.insert(0, root)
from experiments.final import extraction as ex  # noqa: E402

out = {"python": sys.version.split()[0], "hashseed": os.environ.get("PYTHONHASHSEED"), "units": {}}
for u in units:
    exts = []
    print("@@START " + u, flush=True)
    for _ in range(n_calls):
        re.purge()
        exts.append(ex.extract_program(os.path.join(root, u), {}, "output_free_v8"))
    n_events = [e.stats.get("n_events") if e.ok else None for e in exts]
    dists = []
    for a, b in zip(exts, exts[1:]):
        s = ex.score_pair(a, b) if a.ok and b.ok else None
        dists.append(None if s is None else s["sbg_v5"])
    out["units"][u] = {"n_events": n_events, "ok": [e.ok for e in exts], "sbg_v5_consecutive": dists,
                       "entry": exts[0].entry_discovery}
    print("@@UNIT " + json.dumps({"python": out["python"], "hashseed": out["hashseed"], "unit": u, **out["units"][u]}),
          flush=True)
print("@@" + json.dumps(out))
