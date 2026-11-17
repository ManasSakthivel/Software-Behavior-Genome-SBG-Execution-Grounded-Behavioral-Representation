"""Compare re-extracted features (artifacts/v6/repro) with the frozen saved features, field by field."""
import json, math, pathlib, collections, sys
REPO = pathlib.Path(__file__).resolve().parents[2]
NUM = ["d_A", "d_B", "d_C", "d_R", "delta_out", "g", "alpha", "conf", "d_v6", "edit_lines", "v5_recomputed"]
def rd(p): return {r["pair_id"]: r for r in map(json.loads, open(p))}
out = {"files": {}, "mismatch": collections.Counter(), "max_abs_diff": collections.defaultdict(float), "mismatch_examples": []}
n = 0
for s in ("v8train", "v8val"):
    a, b = rd(REPO / f"artifacts/v6/features_{s}.jsonl"), rd(REPO / f"artifacts/v6/repro/features_{s}.jsonl")
    out["files"][s] = {"saved": len(a), "repro": len(b), "ids_equal": set(a) == set(b)}
    for k in a:
        if k not in b: continue
        n += 1; x, y = a[k], b[k]
        if x["status"] != y["status"]: out["mismatch"]["status"] += 1; out["mismatch_examples"].append((k, x["status"], y["status"], x.get("reasons"), y.get("reasons")))
        if x["label"] != y["label"]: out["mismatch"]["label"] += 1
        for c in NUM:
            u, v = x.get(c), y.get(c)
            if u is None and v is None: continue
            if (u is None) != (v is None): out["mismatch"][c] += 1; continue
            d = abs(u - v); out["max_abs_diff"][c] = max(out["max_abs_diff"][c], d)
            if d > 1e-9: out["mismatch"][c] += 1
        if x.get("cfg_size") != y.get("cfg_size"):
            if any(abs(p - q) > 1e-9 for p, q in zip(x.get("cfg_size") or [], y.get("cfg_size") or [])) or (x.get("cfg_size") is None) != (y.get("cfg_size") is None): out["mismatch"]["cfg_size"] += 1
out["pairs_compared"] = n; out["mismatch"] = dict(out["mismatch"]); out["max_abs_diff"] = dict(out["max_abs_diff"]); out["mismatch_examples"] = out["mismatch_examples"][:10]
out["bitwise_identical_features"] = not out["mismatch"]
json.dump(out, open(REPO / "artifacts/v6/repro/REPRO_COMPARE.json", "w"), indent=1); print(json.dumps(out, indent=1))
