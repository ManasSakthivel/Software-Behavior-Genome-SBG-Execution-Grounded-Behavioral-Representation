"""Run the V8 development evaluation. DEVELOPMENT DATA, EXPLORATORY, NOT INDEPENDENT VALIDATION.
usage: .venv/bin/python experiments/v8/run_dev_evaluation.py [--records datasets/v8/dev_records.jsonl] [--seeds 0 1 2] [--boot 10000]
Seed list: the FIRST seed is the primary analysis (full bootstrap); others only check sensitivity to the fold assignment (smaller --boot-extra).
Falls back to the synthetic generator (tests/v8/_synth.py) if the records file is absent (then output is labelled SYNTHETIC)."""
import argparse, datetime, json, os, shutil, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT)
from sbgv8 import evaluate  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--records", default=os.path.join(ROOT, "datasets/v8/dev_records.jsonl")); ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
ap.add_argument("--boot", type=int, default=10000); ap.add_argument("--boot-extra", type=int, default=2000); ap.add_argument("--tag", default=""); ap.add_argument("--strict", action="store_true", help="every V7-B blocker is hard (sensitivity)")
a = ap.parse_args()
if os.path.exists(a.records):
    recs = evaluate.load_records(a.records); src = a.records; note = None
else:
    sys.path.insert(0, os.path.join(ROOT, "tests/v8")); from _synth import make_records
    recs = make_records(n_proj=60, per_proj=6, mode="mult", seed=0); src = "SYNTHETIC"; note = "SYNTHETIC DATA (no dev_records.jsonl)"
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); out = os.path.join(ROOT, f"results/v8_dev_eval_{ts}{a.tag}"); os.makedirs(out)
meta = {"records": src, "seeds": a.seeds, "boot_primary": a.boot, "boot_extra": a.boot_extra, "n_records": len(recs), "timestamp": ts, "strict_blockers": a.strict}
for k, s in enumerate(a.seeds):
    res = evaluate.run(recs, os.path.join(out, f"seed{s}"), s, B=a.boot if k == 0 else a.boot_extra, extra_banner=note, strict_blockers=a.strict)
    print(f"seed {s}: labelled={res.get('n_labelled')} projects={res.get('n_projects')} primary={res.get('primary_system')} :: {res.get('ers_added_value')}")
json.dump(meta, open(os.path.join(out, "run_meta.json"), "w"), indent=1)
summ = os.path.join(ROOT, "results/v8_dev_summary" + ("_strict" if a.strict else "")); shutil.rmtree(summ, ignore_errors=True); os.makedirs(summ)
for k, s in enumerate(a.seeds):
    d = os.path.join(summ, f"seed{s}"); os.makedirs(d)
    for sub in ("tables", "plots"):
        if os.path.isdir(os.path.join(out, f"seed{s}", sub)): shutil.copytree(os.path.join(out, f"seed{s}", sub), os.path.join(d, sub))
    shutil.copy(os.path.join(out, f"seed{s}", "BANNER.txt"), d)
shutil.copy(os.path.join(out, "seed%d" % a.seeds[0], "results.json"), os.path.join(summ, "results_primary_seed.json")); shutil.copy(os.path.join(out, "run_meta.json"), summ)
print("wrote", out)
