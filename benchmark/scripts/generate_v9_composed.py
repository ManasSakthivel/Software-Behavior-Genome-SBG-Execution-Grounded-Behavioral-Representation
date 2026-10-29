#!/usr/bin/env python3
"""
benchmark/scripts/generate_v9_composed.py
=========================================
Size-decoupled CHANGED variants for the edit-size controlled evaluation (docs/current/EVALUATION_PLAN_V9.md).

Problem (LABEL_GENERATION_AUDIT.json): in v8 the label is bound to the transformation family, and the families differ in
edit size (SC-* edit one site, 2 lines; SP-3/4/8/11 rewrite many sites, 8-16 lines), so edit size alone gives AUROC ~0.87.

Design: every v8 EQUIVALENT pair (program p, SP family t, seed s) -- left UNCHANGED, same variant file, same pair id -- gets ONE
composed CHANGED partner  SP_t,s( SC_k(p) ):  a semantics-changing mutation SC_k applied to the program FIRST, then the SAME
semantics-preserving rewrite SP_t,s applied on top.  The partner is compared with the ORIGINAL base program p, exactly like the
EQUIVALENT variant.  Hence

  * the only difference between the two classes' construction is the presence of the mutation (behaviour change);
  * both are rewritten by the same SP family with the same seed -> edit sizes match up to the mutation's own ~2 lines;
  * labels are NOT altered by the composition: SP preserves the semantics of its input, so SP(SC(p)) behaves like SC(p).

SC_k is chosen by a score-free deterministic rotation: SC types in numeric order starting at index (j mod |SC|), j = 0-based
position of the EQUIVALENT pair within its program in the v8 pair file; the first SC type whose candidate is accepted by
the SAME gate used in v8 (compiles, not a no-op, statically observable from the entry) is used.  If none is accepted the
EQUIVALENT pair simply has no partner (logged in the manifest as `unmatched`).  No score, label statistic, or edit-size
statistic is used to choose anything.

Splits: train, dev, val.  The test split is NOT generated (it has been examined; see FREEZE_V8*.json).
Programs with stale v8 variants are excluded (DIAGNOSTIC_V8_STALE_VARIANTS.json).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from benchmark.scripts.generate_v8_dataset import SC_TYPES, check_candidate   # noqa: E402
from benchmark.transformations.mutations.mutator import apply_mutation       # noqa: E402
from benchmark.transformations.preserving.transformer import apply_transformation   # noqa: E402

V8 = REPO / "benchmark/datasets/v8"
OUT = REPO / "benchmark/datasets/v9_composed"
STALE = {s["program"] for s in json.loads((REPO / "artifacts/paper_evidence/DIAGNOSTIC_V8_STALE_VARIANTS.json").read_text())["stale_programs"]}
SPLITS = ("train", "dev", "val")


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compose(base_path: pathlib.Path, sc: str, sp: str, seed: int, tmp: pathlib.Path):
    mutated, _ = apply_mutation(str(base_path), sc, seed=seed, site=0)
    if mutated == base_path.read_text():
        return None
    mp = tmp / base_path.name
    mp.write_text(mutated)
    kw = {"max_names": 1} if sp in ("SP-1", "SP-2") else {}
    out, _ = apply_transformation(str(mp), sp, seed=seed, **kw)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    manifest = {"benchmark_version": "v9_composed", "generator": "benchmark/scripts/generate_v9_composed.py",
                "derived_from": "benchmark/datasets/v8 (EQUIVALENT pairs reused verbatim)", "sc_types": SC_TYPES,
                "stale_programs_excluded": sorted(STALE), "test_split_generated": False, "splits": {}}
    for split in SPLITS:
        v8 = [json.loads(l) for l in (V8 / f"pairs_{split}.jsonl").read_text().splitlines() if l.strip()]
        v8 = [r for r in v8 if r["base_id"] not in STALE]
        equiv = [r for r in v8 if r["semantic_relation"] == "EQUIVALENT"]
        vdir = out / "variants" / split
        vdir.mkdir(parents=True, exist_ok=True)
        pairs, unmatched = [], []
        per_prog = {}
        with tempfile.TemporaryDirectory() as td:
            tmp = pathlib.Path(td)
            for r in equiv:
                j = per_prog.get(r["base_id"], 0)
                per_prog[r["base_id"]] = j + 1
                base_path = REPO / r["base_path"]
                base_src = base_path.read_text()
                sp = r["transformation_type"]
                chosen = None
                for k in range(len(SC_TYPES)):
                    sc = SC_TYPES[(j + k) % len(SC_TYPES)]
                    try:
                        src = compose(base_path, sc, sp, r["seed"], tmp)
                    except Exception:   # noqa: BLE001  (generator failure -> try next SC type; logged via `tried`)
                        continue
                    if src is None:
                        continue
                    ok, _why = check_candidate(base_src, src, "CHANGED")
                    if ok:
                        chosen = (sc, src)
                        break
                if chosen is None:
                    unmatched.append(r["pair_id"])
                    continue
                sc, src = chosen
                vid = f"{r['base_id']}__{sc.lower().replace('-', '')}+{sp.lower().replace('-', '')}_s{r['seed']}_j{j}"
                vp = vdir / f"{vid}.py"
                vp.write_text(src)
                pairs.append({"pair_id": f"{split}__{vid}", "base_id": r["base_id"], "variant_id": vid,
                              "base_path": r["base_path"], "variant_path": str(vp.relative_to(REPO)),
                              "transformation_type": f"{sc}+{sp}", "sc_type": sc, "sp_type": sp,
                              "matched_equivalent_pair_id": r["pair_id"], "semantic_relation": "CHANGED",
                              "expected_label": "CHANGED", "split": split, "seed": r["seed"], "gt_tier": "GT-T3",
                              "confidence": 0.90, "hard_negative": False, "benchmark_version": "v9_composed"})
        (out / f"pairs_{split}.jsonl").write_text("".join(json.dumps(p) + "\n" for p in pairs))
        manifest["splits"][split] = {"n_programs": len({r["base_id"] for r in equiv}), "n_equivalent_v8_reused": len(equiv),
                                     "n_composed_changed": len(pairs), "n_unmatched_equivalent": len(unmatched),
                                     "unmatched_pair_ids": unmatched, "pair_file_sha256": sha(out / f"pairs_{split}.jsonl")}
        print(split, manifest["splits"][split]["n_programs"], "programs;", len(equiv), "equiv;", len(pairs), "composed changed;", len(unmatched), "unmatched")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
