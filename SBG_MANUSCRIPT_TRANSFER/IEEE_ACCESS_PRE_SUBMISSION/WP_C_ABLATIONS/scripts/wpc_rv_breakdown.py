#!/usr/bin/env python3
"""EXP-WPC-006b: why do some SC-6 pairs STILL tie with their SP-only partner under the exploratory return-value variants?
Descriptive only (no AUROC): joins EXP-WPC-004 per-pair forensics (permitted splits v9c_dev, v9c_train) with the EXP-WPC-002 pair table
(rv_* distances).  Never reads v10_test / v9c_val.  Exploratory; never original-SBG evidence.
"""
from __future__ import annotations

import collections
import csv
import json
import pathlib
import sys

WPC = pathlib.Path(__file__).resolve().parents[1]
OUT = WPC / "raw" / "EXP-WPC-006" / "rv_sc6_breakdown.json"


def main():
    if OUT.exists():
        sys.exit("refusing to overwrite " + str(OUT))
    res = {}
    allrows = []
    for split in ("v9c_dev", "v9c_train"):
        pairs = {r["pair_id"]: r for r in csv.DictReader(open(WPC / "raw/EXP-WPC-002" / f"{split}_pairs.csv"))}
        for f in csv.DictReader(open(WPC / "raw/EXP-WPC-004" / f"sc6_pairs_{split}.csv")):
            p = pairs.get(f["pair_id"])
            q = pairs.get(f["partner_id"])
            if p is None or q is None:
                continue
            desc = f["sc6_edit_desc_auto"]
            form = "not" if " -> `return not " in desc or "return not" in desc.split("->")[-1] else "+1" if "+ 1" in desc else "other"
            allrows.append({"split": split, "pair_id": f["pair_id"], "form": form, "v5_zero": float(p["r_v5"]) == 0.0,
                            "rv_pair": float(p["rv_abs100"]), "rv_partner": float(q["rv_abs100"]),
                            "rv_type_pair": float(p["rv_type_abs"]), "rv_type_partner": float(q["rv_type_abs"]),
                            "pv_rettype_diff": int(float(f["pv_rettype_diff"])) if f["pv_rettype_diff"] not in ("", "None") else None,
                            "pv_ret_diff": int(float(f["pv_ret_diff"])) if f["pv_ret_diff"] not in ("", "None") else None,
                            "pv_exc_diff": f["pv_exc_diff"]})
    for key in ("form",):
        g = collections.defaultdict(list)
        for r in allrows:
            g[r[key]].append(r)
        res["by_" + key] = {k: {"n": len(v), "rv_abs100_strictly_above_partner": sum(1 for r in v if r["rv_pair"] > r["rv_partner"]),
                                 "rv_abs100_tied": sum(1 for r in v if r["rv_pair"] == r["rv_partner"]),
                                 "rv_abs100_below": sum(1 for r in v if r["rv_pair"] < r["rv_partner"]),
                                 "return_type_changed_on_some_input": sum(1 for r in v if (r["pv_rettype_diff"] or 0) > 0),
                                 "return_type_unchanged_on_all_inputs": sum(1 for r in v if r["pv_rettype_diff"] == 0)}
                             for k, v in g.items()}
    res["tied_rows_detail"] = collections.Counter(
        (r["form"], "type_changed" if (r["pv_rettype_diff"] or 0) > 0 else "type_same") for r in allrows if r["rv_pair"] == r["rv_partner"])
    res["tied_rows_detail"] = {"|".join(k): v for k, v in res["tied_rows_detail"].items()}
    res["n_rows"] = len(allrows)
    res["rows"] = allrows
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))


if __name__ == "__main__":
    main()
