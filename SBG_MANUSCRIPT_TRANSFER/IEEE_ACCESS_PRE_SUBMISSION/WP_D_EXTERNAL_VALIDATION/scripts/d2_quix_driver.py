#!/usr/bin/env python3
"""WP-D / D2 Task C helper: score QuixBugs programs for ONE regime under a chosen interpreter,
by calling the repository's own per-program worker exactly as external_quixbugs.score() does:

    <python> experiments/final/external_quixbugs.py worker --program ID --regime canonical --protocol output_free_v7

(cwd = repository root of the COPY, WORKER_TIMEOUT_S = 900 per program as in the repo).
The repo's own `score` stage always runs both regimes; this driver runs only the requested
regime. Row sorting / freeze_sha256 stamping replicate external_quixbugs.score() for that
regime. For the canonical regime all 40 programs are eligible, so no 'ineligible' rows exist;
for other regimes ineligible programs are only listed in the .meta.json side file (no rows
are fabricated).

    d2_quix_driver.py COPY_ROOT PYTHON REGIME OUT_JSONL [WORKERS=3]

Run under `d2_run.py`; stdlib only; the driver itself runs under any python >= 3.8.
"""
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import time

root, py, regime, out = sys.argv[1:5]
workers = int(sys.argv[5]) if len(sys.argv) > 5 else 3
protocol = "output_free_v7"
WORKER_TIMEOUT_S = 900
manifest = json.load(open(os.path.join(root, "external/quixbugs/manifest.json")))
freeze_sha = hashlib.sha256(open(os.path.join(root, "artifacts/final/freeze_quixbugs.json"), "rb").read()).hexdigest()

jobs, ineligible = [], []
for entry in manifest["programs"]:
    (jobs if entry["eligible"][regime] else ineligible).append(entry["id"])
print(f"[d2_quix] python={py} regime={regime} eligible_programs={len(jobs)} ineligible={len(ineligible)}", flush=True)


def run(pid):
    cmd = [py, os.path.join(root, "experiments/final/external_quixbugs.py"), "worker", "--program", pid,
           "--regime", regime, "--protocol", protocol]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=root, timeout=WORKER_TIMEOUT_S,
                              env=dict(os.environ))
    except subprocess.TimeoutExpired:
        return pid, [], f"harness_timeout: worker exceeded {WORKER_TIMEOUT_S}s", time.time() - t0
    marker = "@@ROWS@@"
    if proc.returncode != 0 or marker not in proc.stdout:
        return pid, [], f"worker_failed (rc={proc.returncode}): {proc.stderr.strip()[-400:]}", time.time() - t0
    return pid, json.loads(proc.stdout.split(marker, 1)[1]), None, time.time() - t0


rows, errors = [], {}
with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
    for pid, r, err, secs in pool.map(run, jobs):
        if err:
            errors[pid] = err
        rows.extend(r)
        print(f"  [{regime}] {pid:28s} {sum(1 for x in r if x['evaluated'])}/{len(r)} evaluated {secs:.1f}s"
              + (f"  ({err[:100]})" if err else ""), flush=True)
for r in rows:
    r["freeze_sha256"] = freeze_sha
rows.sort(key=lambda r: r["pair_id"])
with open(out, "w") as fh:
    fh.write("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
json.dump({"ineligible_programs": ineligible, "worker_errors": errors, "n_rows": len(rows),
           "python": py}, open(out + ".meta.json", "w"), indent=1)
print(f"[d2_quix] wrote {out}: {len(rows)} rows; worker_errors={len(errors)}", flush=True)
sys.exit(1 if errors else 0)
