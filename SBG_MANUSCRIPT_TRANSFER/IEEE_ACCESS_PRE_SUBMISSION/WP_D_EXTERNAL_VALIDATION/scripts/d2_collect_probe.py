#!/usr/bin/env python3
"""WP-D / D2 Task D: collect '@@UNIT' lines from logs/D1_cold_*.log into compare/D_cold_start_results.json (+ .csv)."""
import csv, glob, json, os
D2 = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw", "WPD-D2_repro"))
rows = []
for f in sorted(glob.glob(os.path.join(D2, "logs", "D1_cold_*.log"))):
    tag = os.path.basename(f)[:-4]
    got = False
    for l in open(f):
        if l.startswith("@@UNIT "):
            d = json.loads(l[7:]); d["tag"] = tag; rows.append(d); got = True
    if not got:
        rows.append({"tag": tag, "unit": None, "note": "no result (timeout / failure) - see command_log.jsonl"})
os.makedirs(os.path.join(D2, "compare"), exist_ok=True)
json.dump(rows, open(os.path.join(D2, "compare", "D_cold_start_results.json"), "w"), indent=1)
with open(os.path.join(D2, "compare", "D_cold_start_results.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["tag", "python", "hashseed", "unit", "n_events", "sbg_v5_consecutive"])
    for r in rows:
        w.writerow([r["tag"], r.get("python"), r.get("hashseed"), (r.get("unit") or "").split("/")[-2:] and "/".join((r.get("unit") or "").split("/")[-2:]),
                    r.get("n_events"), r.get("sbg_v5_consecutive")])
for r in rows:
    print(r["tag"], r.get("n_events"), r.get("sbg_v5_consecutive"))
