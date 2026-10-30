"""EXPLORATORY correction to ZERO_SCORE_ROOT_CAUSE_V1 classes (ii)/(iv): how many 'raw values differ' zero-scored CHANGED pairs differ ONLY by
memory addresses / SP-2 renamed qualnames in object reprs (i.e. not a value difference at all)?  Writes raw/zero_score_address_correction_v1.json.
    PYTHONHASHSEED=0 python experiments/final/zero_score_address_correction.py"""
import collections, json, pathlib, re, sys
REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "experiments" / "final"))
import diagnose_zero_scores as dz                                                    # noqa: E402

ADDR = re.compile(r"0x[0-9a-fA-F]+")
QUAL = re.compile(r"<function ([\w.<>]+) at 0x[0-9a-fA-F]+>")


def norm(v):
    v = QUAL.sub("<function>", v)
    return ADDR.sub("0xADDR", v)


def main():
    d = json.loads((REPO / "artifacts/paper_evidence/raw/zero_score_diagnostic_v1.json").read_text())["pairs"]
    v6 = {}
    for s in ("train", "dev"):
        for l in (REPO / f"artifacts/final/pairs_v9c_{s}_v6exp.jsonl").read_text().splitlines():
            r = json.loads(l); v6[r["pair_id"]] = r
    meta = {}
    for s in ("train", "dev"):
        for l in (REPO / f"benchmark/datasets/v9_composed/pairs_{s}.jsonl").read_text().splitlines():
            m = json.loads(l); meta[m["pair_id"]] = m
    tgt = [r for r in d if r["label"] == 1 and r["scores"]["sbg_v5"] == 0 and not r["raw_values_equal"]]
    out, cache = [], {}
    for r in tgt:
        m = meta[r["pair_id"]]
        if m["base_path"] not in cache:
            cache[m["base_path"]] = dz._run(m["base_path"])
        A, B = cache[m["base_path"]], dz._run(m["variant_path"])
        real = False
        for ta, tb in zip(A["traces"], B["traces"]):
            for x, y in zip(ta.events, tb.events):
                if sorted(norm(v) for v in x.local_vars_snapshot.values()) != sorted(norm(v) for v in y.local_vars_snapshot.values()):
                    real = True
        out.append({"pair_id": r["pair_id"], "differs_after_address_normalisation": real, "output_differs": r["n_inputs_output_differs"] > 0,
                    "v6_zero": v6[r["pair_id"]].get("sbg_v6") == 0, "abstract_values_equal_v5": r["abstract_values_equal"]})
    c = collections.Counter((o["differs_after_address_normalisation"], o["v6_zero"]) for o in out)
    summ = {"n_zero_changed_raw_values_differ": len(out), "address_or_qualname_only": sum(1 for o in out if not o["differs_after_address_normalisation"]),
            "real_value_difference": sum(1 for o in out if o["differs_after_address_normalisation"]),
            "real_value_diff__v6_rescued": c[(True, False)], "real_value_diff__v6_still_zero": c[(True, True)],
            "address_only__v6_rescued": c[(False, False)]}
    p = REPO / "artifacts/paper_evidence/raw/zero_score_address_correction_v1.json"
    p.write_text(json.dumps({"artifact": "zero_score_address_correction_v1", "status": "EXPLORATORY diagnostic", "summary": summ, "pairs": out}, indent=1) + "\n")
    print(summ)


if __name__ == "__main__":
    main()
