#!/usr/bin/env python3
"""WP-E Diagnostic Probe for math_gray_code trace failure.
Tests extraction and tracing on each variant with time and memory instrumentation.
"""
import sys
import os
import pathlib
import time
import json
import resource
import traceback

REPO = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/SBG")
sys.path.insert(0, str(REPO))
os.chdir(REPO)

from experiments.final import extraction as ex

def get_max_rss_mb():
    # On macOS, ru_maxrss is in bytes; on Linux in KB
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return rss / (1024 * 1024)
    return rss / 1024

def jl(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

def main():
    v9_pairs = [p for p in jl(REPO / "benchmark/datasets/v9_composed/pairs_train.jsonl") if p["base_id"] == "math_gray_code"]
    v8_pairs = {p["pair_id"]: p for p in jl(REPO / "benchmark/datasets/v8/pairs_train.jsonl")}
    all_pairs = list(v9_pairs)
    for p in v9_pairs:
        m_id = p["matched_equivalent_pair_id"]
        if m_id in v8_pairs:
            all_pairs.append(v8_pairs[m_id])
    
    paths = sorted(set([p["base_path"] for p in all_pairs] + [p["variant_path"] for p in all_pairs]))
    print(f"Total files to probe: {len(paths)}")
    
    results = []
    
    for i, path in enumerate(paths, 1):
        full_path = str(REPO / path)
        cache = {}
        t0 = time.time()
        rss0 = get_max_rss_mb()
        try:
            print(f"[{i}/{len(paths)}] Probing {path} ...", flush=True)
            res = ex.extract_program(full_path, cache, "output_free_v8")
            dt = time.time() - t0
            rss1 = get_max_rss_mb()
            stats = res.stats if res else {}
            events = stats.get("n_events", 0) if stats else 0
            res_info = {
                "path": path,
                "ok": res.ok if res else False,
                "failure_kind": res.failure_kind if res else "NONE",
                "failure_detail": str(res.failure_detail) if res else "NONE",
                "elapsed_sec": round(dt, 4),
                "rss_mb": round(rss1, 2),
                "rss_delta_mb": round(rss1 - rss0, 2),
                "stats": stats
            }
            print(f"  -> ok={res_info['ok']}, time={dt:.2f}s, RSS={rss1:.1f}MB, stats={stats}", flush=True)
            results.append(res_info)
        except Exception as e:
            dt = time.time() - t0
            rss1 = get_max_rss_mb()
            err_msg = traceback.format_exc()
            print(f"  -> CRASHED: {e} ({dt:.2f}s, RSS={rss1:.1f}MB)", flush=True)
            results.append({
                "path": path,
                "ok": False,
                "error": str(e),
                "traceback": err_msg,
                "elapsed_sec": round(dt, 4),
                "rss_mb": round(rss1, 2)
            })

    out_file = pathlib.Path("/Users/manassakthivel/Desktop/SBG-FINALREVIEW/IEEE_ACCESS_PRE_SUBMISSION/WP_E_MATH_GRAY_CODE/diagnostic_probe_results.json")
    out_file.write_text(json.dumps(results, indent=2))
    print(f"Diagnostic probe finished. Wrote {len(results)} results to {out_file}")

if __name__ == "__main__":
    main()
