"""Label-validity audit of v8 EQUIVALENT variants (EXPLORATORY; no SBG score is read).

Two independent checks, per split:
  (1) STATIC: the variant references a name bound nowhere in the module that the base does not reference
      (a provable NameError on the path that reaches it) -- same rule as audit_external_negatives.undefined_names.
  (2) DYNAMIC ORACLE: on the protocol's own synthesised inputs, base and variant return value / exception /
      in-place argument mutation differ (outputs are read ONLY here, as ground truth for the label; never as a score).

Writes artifacts/paper_evidence/EQUIVALENT_LABEL_AUDIT.json.   PYTHONHASHSEED=0 python experiments/final/audit_equivalent_label_validity.py
"""
import collections, copy, importlib.util, json, pathlib, re, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "experiments" / "final"))
from audit_external_negatives import undefined_names                       # noqa: E402
from experiments.final.entry_policy import select_entry_structural          # noqa: E402

STALE = {s["program"] for s in json.loads((REPO / "artifacts/paper_evidence/DIAGNOSTIC_V8_STALE_VARIANTS.json").read_text())["stale_programs"]}


def jl(p):
    return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]


def load(path):
    re.purge()
    s = importlib.util.spec_from_file_location("_m", str(REPO / path)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def call(f, i):
    a = copy.deepcopy(i)
    try:
        r = f() if i is None else (f(*a) if isinstance(a, tuple) else f(a))
        return ("ok", repr(r)[:300], repr(a)[:300])
    except BaseException as e:                                              # noqa: BLE001
        return ("exc", type(e).__name__, repr(a)[:300])


def main():
    out = {"artifact": "EQUIVALENT_LABEL_AUDIT", "status": "EXPLORATORY audit; outputs used only as label ground truth; the burned v8 TEST split is deliberately NOT audited", "splits": {}}
    for split in ("train", "dev", "val"):
        meta = [m for m in jl(REPO / f"benchmark/datasets/v8/pairs_{split}.jsonl") if m["semantic_relation"] == "EQUIVALENT" and m["base_id"] not in STALE]
        by = collections.defaultdict(lambda: {"n": 0, "static_undefined": 0, "output_differs": 0, "exception_in_variant_only": 0, "type_change_only": 0, "checked": 0})
        ex_rows = []
        cache = {}
        for m in meta:
            t = m["transformation_type"]; d = by[t]; d["n"] += 1
            bsrc = (REPO / m["base_path"]).read_text(); vsrc = (REPO / m["variant_path"]).read_text()
            try:
                if set(undefined_names(vsrc)) - set(undefined_names(bsrc)):
                    d["static_undefined"] += 1
            except SyntaxError:
                d["static_undefined"] += 1
            try:
                if m["base_path"] not in cache:
                    dec = select_entry_structural(bsrc); cache[m["base_path"]] = (dec, getattr(load(m["base_path"]), dec.name))
                dec, fb = cache[m["base_path"]]
                fv = getattr(load(m["variant_path"]), select_entry_structural(vsrc).name)
            except Exception:                                               # noqa: BLE001
                continue
            d["checked"] += 1
            diffs = [(i, call(fb, i), call(fv, i)) for i in dec.inputs]
            bad = [x for x in diffs if x[1] != x[2]]
            if bad:
                d["output_differs"] += 1
                if any(x[1][0] == "ok" and x[2][0] == "exc" for x in bad):
                    d["exception_in_variant_only"] += 1
                if all(x[1][0] == "ok" and x[2][0] == "ok" and x[1][1].replace("deque(", "").replace(")", "") == x[2][1].replace("deque(", "").replace(")", "") for x in bad):
                    d["type_change_only"] += 1
                if len(ex_rows) < 400:
                    ex_rows.append({"pair_id": m["pair_id"], "transformation_type": t, "n_inputs_differ": len(bad), "first": [repr(bad[0][0])[:60], bad[0][1][:2], bad[0][2][:2]]})
        tot = sum(v["n"] for v in by.values()); od = sum(v["output_differs"] for v in by.values())
        out["splits"][split] = {"n_equivalent_nonstale": tot, "n_output_differs": od, "by_transformation": dict(by), "output_differs_pairs": ex_rows}
        print(split, tot, od, {k: (v["output_differs"], v["n"]) for k, v in by.items() if v["output_differs"]}, flush=True)
    (REPO / "artifacts/paper_evidence/EQUIVALENT_LABEL_AUDIT.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
