#!/usr/bin/env python3
"""ab01 -- read-only provenance / integrity check of the existing A4 evidence (EXP-A4B-001, EXP-A4C-001..005, EXP-A4D-002..005).

Writes only into WP_A_B_COMPARATIVE_BENCHMARK/raw/EXP-A4R-002/.  Reads everything else; modifies nothing.
Checks: (1) frozen_config sha256, (2) module sha256 recorded in frozen config / A4C-001 manifest vs. current files,
(3) code_sha256 recomputed with the frozen recipe vs. recorded, (4) prediction-file inventory per population and meta consistency,
(5) mtimes of code vs. freeze, (6) held-out predictions presence, (7) population sha256 vs. configs.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import pathlib
import time

HERE = pathlib.Path(__file__).resolve().parent
WP = HERE.parent
PKG = WP.parent
RAW = PKG / "results" / "raw"
CB = PKG / "experiments" / "competitor_baselines"
OUT = WP / "raw" / "EXP-A4R-002"
OUT.mkdir(parents=True, exist_ok=True)


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def sha_s(s):
    return hashlib.sha256(s.encode()).hexdigest()


rep = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "checks": {}}
fcp = RAW / "EXP-A4C-002" / "frozen_config.json"
fc = json.loads(fcp.read_text())
EXPECT = "f52bfaee96f501fc19198de2a585dcfc500e0ae21e13f2dec0d3d670251e7bdb"
rep["checks"]["frozen_config_sha256"] = {"expected": EXPECT, "actual": sha(fcp), "match": sha(fcp) == EXPECT,
                                         "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(fcp.stat().st_mtime))}

# module hashes
mods = {}
for m, v in fc["module_manifest"].items():
    cur = sha(PKG / v["path"])
    mods[m] = {"frozen": v["sha256"], "current": cur, "match": cur == v["sha256"],
               "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((PKG / v["path"]).stat().st_mtime))}
rep["checks"]["module_hashes_vs_frozen_config"] = mods

# recompute code sha with the frozen recipe (module shas sorted + a4c_common.py + run_all.py)
parts = [f"{k}:{v['sha256']}" for k, v in sorted(fc["module_manifest"].items())]
for f in ("a4c_common.py", "run_all.py"):
    parts.append(f"{f}:{sha(CB / 'run' / f)}")
cur_code = sha_s("|".join(parts))
rep["checks"]["code_sha256"] = {"frozen": fc["code_sha256"], "recomputed_from_current_files": cur_code, "match": cur_code == fc["code_sha256"],
                                "a4c_common_sha": sha(CB / "run" / "a4c_common.py"), "run_all_sha": sha(CB / "run" / "run_all.py"),
                                "a4c_001_manifest_code_sha": json.loads((RAW / "EXP-A4C-001" / "module_manifest.json").read_text())["code_sha256"],
                                "note": "if mismatch: run_all.py / a4c_common.py changed after the freeze; the 9 predecessor module files are what scores depend on"}
rep["checks"]["run_all_mtime_vs_freeze"] = {"run_all.py": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((CB / 'run' / 'run_all.py').stat().st_mtime)),
                                            "a4c_common.py": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((CB / 'run' / 'a4c_common.py').stat().st_mtime)),
                                            "stages_eval.py(not in SRC_MODULES)": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((CB / 'stages_eval.py').stat().st_mtime)),
                                            "frozen_config": rep["checks"]["frozen_config_sha256"]["mtime"]}

# prediction inventory
pdir = RAW / "EXP-A4C-003" / "predictions"
inv = {}
for p in sorted(os.listdir(pdir)):
    d = pdir / p
    if d.is_dir():
        inv[p] = len(list(d.glob("*.json")))
rep["checks"]["A4C-003_prediction_files_per_population"] = inv
meta = json.loads((pdir / "meta.json").read_text())
mm = meta["methods"]
rep["checks"]["A4C-003_meta"] = {"n_methods": len(mm), "keys": [k for k in meta if k != "methods"],
                                 "frozen_sha_values": sorted({m.get("frozen_config_sha256") for m in mm.values()}),
                                 "code_sha_values": sorted({m.get("code_sha256") for m in mm.values()})}
# consistency: every meta method has a file in each existing pop and vice-versa
cons = {}
for pop in inv:
    files = {f.stem for f in (pdir / pop).glob("*.json")}
    cons[pop] = {"files": len(files), "in_meta_not_files": len(set(mm) - files), "files_not_in_meta": len(files - set(mm))}
rep["checks"]["A4C-003_meta_vs_files"] = cons
rep["checks"]["heldout_predictions_present"] = {"v9c_val": inv.get("v9c_val", 0), "v10_test": inv.get("v10_test", 0),
                                                "registry_A4C_jsonl_exists": (PKG / "logs" / "registry" / "A4C.jsonl").exists(),
                                                "VERIFIED_BASELINES_exists": (RAW / "EXP-A4R-001" / "VERIFIED_BASELINES.json").exists(),
                                                "READY_files": sorted(os.path.basename(x) for x in glob.glob(str(CB / "competitors_new" / "*.READY")))}

# populations
popd = PKG / "configs" / "populations"
rep["checks"]["population_sha256"] = {f.stem: sha(f) for f in sorted(popd.glob("*.json"))}
rep["checks"]["population_sha256_in_frozen_config"] = fc["population_sha256"]

# inventory of experiment dirs
exps = {}
for d in sorted(RAW.glob("EXP-A4*")):
    files = [f for f in d.rglob("*") if f.is_file()]
    exps[d.name] = {"n_files": len(files), "bytes": sum(f.stat().st_size for f in files),
                    "latest_mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(max((f.stat().st_mtime for f in files), default=0)))}
rep["checks"]["experiment_dirs"] = exps
(OUT / "provenance_check.json").write_text(json.dumps(rep, indent=1, sort_keys=True))
print(json.dumps({k: v for k, v in rep["checks"].items() if k not in ("module_hashes_vs_frozen_config", "experiment_dirs")}, indent=1)[:3500])
print({m: v["match"] for m, v in mods.items()})
