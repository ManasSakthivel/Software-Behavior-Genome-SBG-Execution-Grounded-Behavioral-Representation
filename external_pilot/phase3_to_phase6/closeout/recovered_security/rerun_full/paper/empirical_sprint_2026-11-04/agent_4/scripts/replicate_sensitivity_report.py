"""Re-derive the PYTHON_VERSION_SENSITIVITY report from the two rerun outputs (py313 vs py39),
using the repo's own _walk/classification logic (imported from the COPY; main() is NOT called)."""
import sys, json, pathlib
here = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(here / "copy" / "experiments" / "final"))
import python_version_sensitivity as pvs
names = ("HARD_NEGATIVE_V5_RESULTS.json", "REGRESSION_V5_RESULTS.json")
A = {n: json.load(open(here/"outputs"/"py313"/n)) for n in names}
B = {n: json.load(open(here/"outputs"/"py39"/n)) for n in names}
rep = {}
for n in names:
    diffs = []; pvs._walk(A[n], B[n], [], diffs)
    dist = [d for d in diffs if ".distances." in f".{d[1]}." or "distances" in d[1]]
    moved = [d for d in dist if d[0] > 0]
    reported = [p for dl, p in diffs if dl > 0 and "distances" not in p and "n_events" not in p]
    nev = [(p, dl) for dl, p in diffs if dl > 0 and "n_events" in p]
    top = sorted(moved, reverse=True)[:5]
    rep[n] = {"distance_values": len(dist), "distance_values_changed": len(moved),
              "max_abs_distance_change": round(max(d[0] for d in dist), 6),
              "reported_values_changed": reported, "n_events_fields_changed": nev,
              "top5_moved": [(round(a, 6), p) for a, p in top]}
print(json.dumps(rep, indent=1))
stored = json.load(open(here/"outputs"/"committed"/"PYTHON_VERSION_SENSITIVITY.json"))["experiments"]
for n in names:
    s = stored[n]; r = rep[n]
    print(n, "MATCH_STORED" if all(s[k] == r[k] for k in ("distance_values","distance_values_changed","max_abs_distance_change","reported_values_changed")) else "MISMATCH")
