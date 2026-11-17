"""Task 6: label adjudication EVIDENCE (no relabelling, no deletion). DEV only.
 -> artifacts/v6/audit/LABEL_ADJUDICATION.csv, LABEL_ADJUDICATION_SUMMARY.json"""
import json, sys, pathlib, re, csv, difflib, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from experiments.v6.evaluate import *   # noqa
from sbgv6.observe import PythonAdapter
from sbgv6 import features as F
OUT = REPO / "artifacts/v6/audit"
meta = {}
for f in ("train", "val"):
    for l in open(REPO / f"benchmark/datasets/v8/pairs_{f}.jsonl"):
        r = json.loads(l); meta[r["pair_id"]] = r
df = load(["v8train", "v8val"]); y = df.label.values.astype(int)
ad, cache = PythonAdapter(), {}
def obs(p):
    if p not in cache: cache[p] = ad.observe(str(REPO / p))
    return cache[p]
DEQ = re.compile(r"deque\((\[[^()]*\])(?:, maxlen=None)?\)")
norm = lambda s: DEQ.sub(r"\1", s)
rows = []
def diff_head(pid):
    m = meta[pid]; a = (REPO / m["base_path"]).read_text().splitlines(); b = (REPO / m["variant_path"]).read_text().splitlines()
    return " | ".join(l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---"))[:400]
for _, r in df.iterrows():
    eq = r.label == 0; has = (r.delta_out or 0) > 0
    if not ((eq and has) or ((not eq) and (r.delta_out == 0))): continue
    d = {"pair_id": r.pair_id, "base_id": r.base_id, "transformation_type": r.transformation_type, "original_label": int(r.label),
         "delta_out": r.delta_out, "d_R": r.d_R, "status": r.status, "alpha": r.alpha, "d_A": r.d_A, "d_B": r.d_B, "d_C": r.d_C}
    if eq and has:                       # equivalent-labelled but outputs differ: look at the actual values
        a, b = obs(meta[r.pair_id]["base_path"]), obs(meta[r.pair_id]["variant_path"]); cls, det = "no_diff_found_on_rerun", ""
        if a.ok and b.ok:
            for i, (x, z) in enumerate(zip(a.runs[0], b.runs[0])):
                if x.truncated or z.truncated: continue
                (_, ex), (_, ez) = F._rv(x), F._rv(z)
                if ex != ez:
                    if ex[0] != ez[0]: cls = "exception_type_differs"
                    elif norm(ex[1]) == norm(ez[1]): cls = "repr_only_container_type (deque vs list); value equal"
                    else: cls = "value_differs"
                    det = f"input#{i}: base={ex[1][:70]!r} var={ez[1][:70]!r}"; break
        d.update(evidence_class="EQ_LABEL_OUTPUT_DIFF:" + cls, detail=det)
    else:                                # changed-labelled but no output difference
        trace_diff = any((r[c] or 0) > 0 for c in ("d_A", "d_B", "d_C"))
        if r.status in ("UNKNOWN",): cls = "unknown_evidence"
        elif r.status == "NOT_ACTIVATED": cls = "changed_code_not_exercised_by_declared_inputs (test inadequacy, NOT equivalence)"
        elif trace_diff: cls = "activated; internal trace differs but output identical (masked)"
        else: cls = "activated; trace and output identical (candidate equivalent mutant OR insufficient discrimination)"
        d.update(evidence_class="CHANGED_LABEL_NO_OUTPUT_DIFF:" + cls, detail=diff_head(r.pair_id))
    d["adjudication_status"] = "automated evidence only; ORIGINAL LABEL PRESERVED; no human adjudication yet"
    rows.append(d)
with open(OUT / "LABEL_ADJUDICATION.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
S = {"n_rows": len(rows), "by_class": collections.Counter(r["evidence_class"] for r in rows),
     "by_type_and_class": collections.Counter((r["transformation_type"], r["evidence_class"].split(":")[1][:60]) for r in rows)}
S = json.loads(json.dumps(S, default=str)) if False else {"n_rows": S["n_rows"], "by_class": dict(S["by_class"]), "by_type_and_class": {f"{a}|{b}": n for (a, b), n in S["by_type_and_class"].items()}}
# impact on the headline numbers if the evidence classes were (hypothetically) excluded -- sensitivity only, labels untouched
s = neutral(df, "delta_out").values; ids = {r["pair_id"]: r["evidence_class"] for r in rows}
def sens(pred):
    m = ~df.pair_id.map(lambda p: pred(ids.get(p, ""))).values; return {"n_kept": int(m.sum()), "delta_out_auroc": auroc(y[m], s[m])}
S["sensitivity_delta_out_auroc"] = {"all_pairs": auroc(y, s), "drop_repr_only_deque": sens(lambda c: "repr_only" in c), "drop_all_89_eq_output_diff": sens(lambda c: c.startswith("EQ_")),
    "drop_not_exercised": sens(lambda c: "not_exercised" in c), "drop_unexplained_candidate_equivalent": sens(lambda c: "candidate equivalent" in c)}
json.dump(S, open(OUT / "LABEL_ADJUDICATION_SUMMARY.json", "w"), indent=1); print(json.dumps(S, indent=1))
