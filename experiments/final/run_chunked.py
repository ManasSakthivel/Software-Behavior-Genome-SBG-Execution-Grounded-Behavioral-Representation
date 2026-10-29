"""Harness only: score a split with ONE SUBPROCESS PER BASE PROGRAM, then merge in dataset order.

Why: a single process that traces a few hundred mutants accumulates leaked, non-terminating tracer worker threads
(documented in extraction.py) and eventually stalls (observed at ~525 pairs on v8 test, twice, at different programs;
every pair completes when run alone).  Per-program processes bound that state.  Scores are a function of
(program file, protocol) only -- v8 dev was verified identical across PYTHONHASHSEED 0/1/7 and across re-scores --
and `--verify-against` checks chunked == single-process output on dev.

    python run_chunked.py --split dev  --pairs-dir benchmark/datasets/v8 --tag v8dev_chunked --verify-against artifacts/final/pairs_v8devrescore_output_free_v8.jsonl
    python run_chunked.py --split test --pairs-dir artifacts/final/v8_test_nonstale --tag v8test
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
STATIC = ("static_ast", "static_token")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["train", "dev", "val", "test"])
    ap.add_argument("--pairs-dir", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--protocol", default="output_free_v8")
    ap.add_argument("--out-dir", default=str(REPO / "artifacts" / "final"))
    ap.add_argument("--dataset-label", default="benchmark/datasets/v8")
    ap.add_argument("--verify-against")
    ap.add_argument("--per-program-timeout", type=int, default=420)
    ap.add_argument("--per-pair-timeout", type=int, default=90)
    ap.add_argument("--max-rss-gb", type=float, default=4.0, help="watchdog: kill a scoring subprocess above this RSS")
    a = ap.parse_args()
    pairs_dir = (REPO / a.pairs_dir).resolve()
    pairs = [json.loads(l) for l in (pairs_dir / f"pairs_{a.split}.jsonl").read_text().splitlines() if l.strip()]
    order, by = [], {}
    for p in pairs:
        if p["base_id"] not in by:
            order.append(p["base_id"])
        by.setdefault(p["base_id"], []).append(p)
    work = REPO / "tmp" / f"chunks_{a.tag}"
    if work.exists():
        shutil.rmtree(work)
    rows = {}
    timeouts = []
    env = dict(os.environ, PYTHONHASHSEED="0")
    for i, prog in enumerate(order, 1):
        cd = work / prog
        cd.mkdir(parents=True)
        (cd / f"pairs_{a.split}.jsonl").write_text("".join(json.dumps(p) + "\n" for p in by[prog]))
        out = work / f"out_{prog}"
        def run_chunk(plist, tag, timeout):
            cdir = work / f"{prog}__{tag}"
            cdir.mkdir(parents=True)
            (cdir / f"pairs_{a.split}.jsonl").write_text("".join(json.dumps(p) + "\n" for p in plist))
            outd = work / f"out_{prog}__{tag}"
            cmd = [sys.executable, str(REPO / "experiments/final/run_main_evaluation.py"), "--split", a.split,
                   "--protocol", a.protocol, "--dataset-dir", str(cdir), "--tag", "chunk", "--out-dir", str(outd),
                   "--checkpoint-every", "1000"]
            proc = subprocess.Popen(cmd, cwd=REPO, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            t0 = time.time()
            while proc.poll() is None:
                time.sleep(1.0)
                rss = subprocess.run(["ps", "-o", "rss=", "-p", str(proc.pid)], capture_output=True, text=True).stdout.strip()
                if (rss and int(rss) / 1e6 > a.max_rss_gb) or time.time() - t0 > timeout:
                    proc.kill(); proc.wait()
                    raise subprocess.TimeoutExpired(cmd, timeout)
            if proc.returncode:
                raise SystemExit(f"chunk {prog} failed: {proc.stderr.read()[-400:]}")
            return [json.loads(l) for l in (outd / f"pairs_chunk_{a.protocol}.jsonl").read_text().splitlines()]

        try:
            got = run_chunk(by[prog], "all", a.per_program_timeout)
        except subprocess.TimeoutExpired:
            # Fallback (mechanical, score-independent): one subprocess per pair; a pair that exceeds the hard timeout is recorded
            # unevaluated with failure_kind=harness_timeout.  Logged so the exclusion is visible.
            print(f"  {prog}: program chunk exceeded {a.per_program_timeout}s -> per-pair fallback", flush=True)
            got = []
            for p in by[prog]:
                try:
                    got += run_chunk([p], p["pair_id"].replace("/", "_"), a.per_pair_timeout)
                except subprocess.TimeoutExpired:
                    print(f"  HARNESS_TIMEOUT {p['pair_id']}", flush=True)
                    timeouts.append(p["pair_id"])
                    got.append({"pair_id": p["pair_id"], "base_id": p["base_id"], "split": p["split"], "protocol": a.protocol,
                                "transformation_type": p["transformation_type"], "semantic_relation": p["semantic_relation"],
                                "label": 1 if p["semantic_relation"] == "CHANGED" else 0, "evaluated": False, "failure_side": "variant",
                                "failure_kind": "harness_timeout", "failure_detail": f"exceeded {a.per_pair_timeout}s wall clock or {a.max_rss_gb} GB RSS"})
        for row in got:
            row["dataset"] = a.dataset_label
            rows[row["pair_id"]] = row
        print(f"[{i}/{len(order)}] {prog}: {len(by[prog])} pairs", flush=True)
    merged = [rows[p["pair_id"]] for p in pairs]
    dest = pathlib.Path(a.out_dir) / f"pairs_{a.tag}_{a.protocol}.jsonl"
    dest.write_text("".join(json.dumps(r) + "\n" for r in merged))
    print("wrote", dest, len(merged), "evaluated", sum(r["evaluated"] for r in merged), "harness_timeouts", timeouts)
    shutil.rmtree(work)
    if a.verify_against:
        ref = {json.loads(l)["pair_id"]: json.loads(l) for l in pathlib.Path(a.verify_against).read_text().splitlines() if l.strip()}
        bad = 0
        for r in merged:
            q = ref[r["pair_id"]]
            if r["evaluated"] != q["evaluated"] or (r["evaluated"] and
                    {k: v for k, v in r["scores"].items() if k not in STATIC} != {k: v for k, v in q["scores"].items() if k not in STATIC}):
                bad += 1
        print(f"VERIFY vs {a.verify_against}: {len(merged)} pairs, {bad} differ")
        if bad:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
