"""A4C shared helpers: paths, module resolution (verified / fixed copies), population assembly, method registry.  Pure stdlib.

Module resolution rule (PROTOCOL_ADDENDUM v1.1): baseline modules come from competitor_baselines/ (predecessor, frozen code) unless A4R's
VERIFIED_BASELINES.json says a module must be taken from recovery/fixed/.  Held-out data are only ever touched when every module that is imported
is covered by the verified list (guard: require_verified()).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
CB = HERE.parent                                  # competitor_baselines/
PKG = CB.parents[1]
REPO = PKG.parent / "SBG"
RAW = PKG / "results" / "raw"
PROC = PKG / "results" / "processed"
TAB = PKG / "results" / "tables"
REG = PKG / "logs" / "registry" / "A4C.jsonl"
VERIFIED = RAW / "EXP-A4R-001" / "VERIFIED_BASELINES.json"
FIXED = CB / "recovery" / "fixed"
NEW = CB / "competitors_new"
POPS = ("v9c_train", "v9c_dev", "v9c_val", "v10_test")
HELD = ("v9c_val", "v10_test")
SRC_MODULES = ["bl_common", "b02_static", "b03_execstats", "b04_valuespectra", "b05_pathspectra", "b05_traceseq", "b06_indep_inputs", "features", "models"]

# experiment ids (own protocol per id)
EXP_FEAT, EXP_FIT, EXP_PRED, EXP_EVAL, EXP_INC, EXP_RT = "EXP-A4C-001", "EXP-A4C-002", "EXP-A4C-003", "EXP-A4C-004", "EXP-A4C-005", "EXP-A4C-006"

sys.path.insert(0, str(PKG / "experiments" / "common"))
import eval_lib  # noqa: E402


def sha256_file(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def jdump(path, obj):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))


def jload(path):
    return json.loads(pathlib.Path(path).read_text())


def register(entry: dict):
    """Append one JSON line to the A4C registry (append-only)."""
    entry = {"agent": "A4C", "repo_commit": "3425693b432bb774b10db1cf3185eae1a7eef095", **entry}
    REG.parent.mkdir(parents=True, exist_ok=True)
    with open(REG, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


# ------------------------------------------------------------------ module resolution
def verified_state():
    """None if A4R has not published; otherwise the parsed JSON."""
    return jload(VERIFIED) if VERIFIED.exists() else None


def module_dir_for(name: str):
    """Directory that provides module `name`: recovery/fixed/ if A4R published a fixed copy and VERIFIED says to use it, else the predecessor dir."""
    if (FIXED / f"{name}.py").exists() and FIXED_ENABLED:
        return FIXED
    return CB


FIXED_ENABLED = False          # switched on by setup_modules() after reading VERIFIED_BASELINES.json


def setup_modules(use_fixed: bool):
    """Put the selected module directory first on sys.path (fork-pool workers inherit)."""
    global FIXED_ENABLED
    FIXED_ENABLED = use_fixed
    for d in (str(CB), str(FIXED)):
        while d in sys.path:
            sys.path.remove(d)
    sys.path.insert(0, str(CB))
    if use_fixed and FIXED.exists():
        sys.path.insert(0, str(FIXED))


def module_manifest():
    out = {}
    for m in SRC_MODULES:
        d = module_dir_for(m)
        p = d / f"{m}.py"
        out[m] = {"path": str(p.relative_to(PKG)), "sha256": sha256_file(p), "source": "recovery/fixed" if d == FIXED else "predecessor"}
    return out


def code_sha(extra=()):
    """Single sha256 over the sha of every module in use + this package's run/ code."""
    parts = [f"{k}:{v['sha256']}" for k, v in sorted(module_manifest().items())]
    for f in ("a4c_common.py", "run_all.py"):
        parts.append(f"{f}:{sha256_file(HERE / f)}")
    return sha256_str("|".join(parts))


def require_verified():
    """Guard for any stage that touches held-out populations: every module must be listed as verified by A4R."""
    v = verified_state()
    if v is None:
        raise SystemExit("BLOCKED: A4R VERIFIED_BASELINES.json not published; refusing to run baseline modules on held-out data")
    return v


# ------------------------------------------------------------------ population assembly
def pop_rows(pop):
    return eval_lib.load_population(pop)


def exclusions(pop):
    """base programs of the population whose trace-cache directory has no DONE marker (train: math_gray_code, empty dir)."""
    return sorted({r["base_id"] for r in pop_rows(pop) if not (RAW / "trace_cache" / pop / r["base_id"] / "DONE").exists()})


def feat_dir(pop):
    return RAW / EXP_FEAT / "features" / pop


def load_features(pop):
    out = {}
    d = feat_dir(pop)
    if d.exists():
        for f in sorted(d.glob("*.json")):
            out.update(jload(f))
    return out


def load_indep(pop):
    p = RAW / EXP_FEAT / "indep" / f"indep_{pop}.json"
    return jload(p) if p.exists() else {}


INDEP_KEYS = ("output_indep|frac40", "output_indep|any40", "output_indep|frac40_excmsg", "output_indep|frac11", "output_indep|any11")


def assemble(pop, drop_trace_missing=True):
    """Rows of the primary population with the score table S = frozen scores + edit + all label-free features (+ independent-input scores).
    Rows whose program has no trace cache (v9c_train math_gray_code) are dropped when drop_trace_missing (logged by the caller)."""
    rows = pop_rows(pop)
    feats = load_features(pop)
    ind = load_indep(pop)
    out, dropped = [], []
    for r in rows:
        f = feats.get(r["pair_id"])
        if f is None or not f.get("_trace_ok"):
            dropped.append(r["pair_id"])
            if drop_trace_missing:
                continue
        S = dict(r["scores"])
        S["edit"] = float(r["edit"])
        S["edit_rev"] = -S["edit"]
        S.update(f or {})
        i = ind.get(r["pair_id"])
        r["_indep_covered"] = bool(i)
        if i:
            S.update(i)
        for k in INDEP_KEYS:
            S.setdefault(k, 0.0)
        r["S"] = S
        out.append(r)
    return out, dropped


def col(rows, key):
    return [r["S"].get(key, 0.0) for r in rows]


def labels(rows):
    return [r["label"] for r in rows]


def clusters(rows):
    return [r["base_id"] for r in rows]
