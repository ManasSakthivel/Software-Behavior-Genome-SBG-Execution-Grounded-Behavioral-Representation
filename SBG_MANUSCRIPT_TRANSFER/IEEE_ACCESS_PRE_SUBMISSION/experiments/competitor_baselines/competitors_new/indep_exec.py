"""indep_exec -- independent-input battery generator + sandboxed executor for the A4B differential-execution competitors (diffexec_indep, ka_behaviour_sampling).

Library part (imported by the modules) + CLI worker part (``python indep_exec.py battery|run ...``, each in its OWN clean subprocess with wall-clock timeouts).

Generator "A4B-gen-v1"  (how it differs from the protocol's 11 synthesised inputs, PROTOCOL section 3 / SBG ``experiments/final/protocol.py``)
  * protocol battery  : 11 fixed, program-independent constants per *type family* (annotation text collapsed to list/str/int/float/bool/dict; every ``list[...]``
                        gets the same 11 flat-int lists, every ``dict[...]`` the same 11 toy graphs), zipped across parameters, NOT validity-filtered, so for
                        e.g. ``list[list[int]]`` / ``list[str]`` / weighted-edge parameters many protocol inputs are structurally invalid.
  * A4B-gen-v1        : (i) parses the FULL annotation of every required parameter of the entry function (nested ``list[list[int]]``, ``list[str]``, ``tuple[..]``,
                        ``dict[K, list[K]]`` -> graph with referenced keys, module-level aliases like ``Matrix = list[list[int]]``, Optional/Union) and generates
                        structurally VALID random values; (ii) random sizes (geometric, incl. empty / singleton / up to 14), value ranges different from the
                        protocol constants, (iii) RNG seed = sha256("A4B-indep-v1|" + base_id) (disjoint from the predecessor's sha1(base_id) and from any constant),
                        (iv) candidates (<=500) are FILTERED USING THE ORIGINAL BASE PROGRAM ONLY (keep inputs on which the base returns normally within 0.5 s; target
                        40, need >= 12 else the program is BLOCKED_NO_VALID_INPUTS), (v) inputs whose repr equals a protocol input are dropped.
                        It never reads variants, labels or any SBG score.  Observed behaviour per input: (return repr, exception TYPE (+message kept separately),
                        stdout, repr of the arguments after the call [in-place mutation]).  Per-call SIGALRM 1.0 s, <=2 timeouts per file, subprocess wall limit,
                        RLIMIT_CPU 90 s, RLIMIT_AS 6 GiB (best effort on macOS).
"""
from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import io
import json
import os
import pathlib
import random
import re
import signal
import subprocess
import sys
import time
import types

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parents[2]
REPO = PKG.parent / "SBG"
OUT = PKG / "results" / "raw" / "EXP-A4B-002"
TARGET, MINVALID, MAXCAND = 40, 12, 500
CALL_LIMIT, BATTERY_LIMIT = 1.0, 0.5
GEN = "A4B-gen-v1"


class _TO(BaseException):
    pass


def _alarm(signum, frame):
    raise _TO()


_ADDR = re.compile(r"0x[0-9a-fA-F]+")


def _scrub(s):
    return _ADDR.sub("0x", s)


# ======================================================================== sandbox execution (used inside worker subprocesses)
def load_module(path):
    src = pathlib.Path(path).read_text()
    code = compile(src, str(path), "exec")
    mod = types.ModuleType("_a4b_prog")
    mod.__file__ = str(path)
    sys.modules["_a4b_prog"] = mod
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(code, mod.__dict__)
    return mod


def call_once(fn, args, limit):
    a = copy.deepcopy(args)
    buf = io.StringIO()
    ret = exc_t = exc_m = None
    signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, limit)
    try:
        with contextlib.redirect_stdout(buf):
            ret = _scrub(repr(fn(*a)))[:1000]
    except _TO:
        exc_t, exc_m = "TIMEOUT", ""
    except RecursionError:
        exc_t, exc_m = "RecursionError", ""
    except MemoryError:
        exc_t, exc_m = "MemoryError", ""
    except BaseException as e:  # noqa: BLE001
        exc_t, exc_m = type(e).__name__, _scrub(str(e))[:200]
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    try:
        post = _scrub(repr(a))[:1000]
    except BaseException:  # noqa: BLE001
        post = "<repr-error>"
    return {"ret": ret, "exc": exc_t, "msg": exc_m, "out": buf.getvalue()[:500], "post": post}


# ======================================================================== annotation-driven generator
def _alias_table(tree):
    t = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            t[n.targets[0].id] = n.value
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
            t[n.target.id] = n.value
    return t


def _geom(r, lo, hi, p=0.78):
    n = lo
    while n < hi and r.random() < p:
        n += 1
    return n


def _ann_name(ann):
    if isinstance(ann, ast.Subscript):
        return _ann_name(ann.value)
    if isinstance(ann, ast.Name):
        return ann.id
    if isinstance(ann, ast.Attribute):
        return ann.attr
    return ""


def _parse(s):
    return ast.parse(s, mode="eval").body


def gen_value(r, ann, aliases, hint=None, depth=0):
    """random structurally valid value for annotation AST `ann` (None -> unannotated => list of ints)."""
    if ann is None:
        return gen_value(r, _parse("list[int]"), aliases, hint, depth)
    if isinstance(ann, ast.Name) and ann.id in aliases and depth < 6:
        return gen_value(r, aliases[ann.id], aliases, hint, depth + 1)
    if isinstance(ann, ast.Constant) and isinstance(ann.value, str):
        try:
            return gen_value(r, _parse(ann.value), aliases, hint, depth + 1)
        except SyntaxError:
            return []
    name = _ann_name(ann)
    sl = ann.slice if isinstance(ann, ast.Subscript) else None
    args = list(sl.elts) if isinstance(sl, ast.Tuple) else ([sl] if sl is not None else [])
    low = name.lower()
    if low in ("int", "number"):
        if hint in ("k", "n", "m", "target", "capacity", "amount", "limit", "size", "count", "total", "num", "length", "width", "steps"):
            return r.choice([0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 15, 20, 25])
        return r.choice([r.randint(-12, 12), r.randint(0, 30), r.randint(-3, 3), r.randint(0, 6)])
    if low == "float":
        return round(r.uniform(-20, 20), r.choice([0, 1, 2]))
    if low == "bool":
        return r.random() < 0.5
    if low in ("str", "bytes"):
        alpha = r.choice(["ab", "abc", "abcdefgh", "xyz ", "aeiou", "()[]", "0123456789", "abcdefghijklmnopqrstuvwxyz"])
        s = "".join(r.choice(alpha) for _ in range(_geom(r, 0, 14)))
        return s.encode() if low == "bytes" else s
    if low in ("list", "sequence", "iterable", "mutablesequence", "deque", "collection"):
        inner = args[0] if args else _parse("int")
        return [gen_value(r, inner, aliases, hint, depth + 1) for _ in range(_geom(r, 0, 14))]
    if low in ("set", "frozenset"):
        inner = args[0] if args else _parse("int")
        v = {gen_value(r, inner, aliases, hint, depth + 1) for _ in range(_geom(r, 0, 10))}
        return v if low == "set" else frozenset(v)
    if low == "tuple":
        if len(args) == 2 and isinstance(args[1], ast.Constant) and args[1].value is Ellipsis:
            return tuple(gen_value(r, args[0], aliases, hint, depth + 1) for _ in range(_geom(r, 0, 8)))
        if not args:
            return tuple(r.randint(0, 9) for _ in range(r.randint(1, 4)))
        return tuple(gen_value(r, a, aliases, hint, depth + 1) for a in args)
    if low in ("dict", "mapping", "defaultdict", "counter", "ordereddict", "mutablemapping", "dataframe"):
        if low == "dataframe" or not args:
            kt, vt = _parse("str"), _parse("list[str]")
        elif len(args) == 1:
            kt, vt = args[0], _parse("int")
        else:
            kt, vt = args[0], args[1]
        n = _geom(r, 0, 7, 0.7)
        is_str = isinstance(kt, ast.Name) and kt.id == "str"
        pool = [chr(97 + i) for i in range(max(1, n))] if is_str else list(range(max(1, n)))
        d = {}
        graph_like = isinstance(vt, ast.Subscript) and "list" in ast.unparse(vt).lower()
        for k in pool[:n]:
            if graph_like:
                d[k] = [r.choice(pool) for _ in range(r.randint(0, min(3, len(pool))))]
                if r.random() < 0.7:
                    d[k] = [x for x in d[k] if x != k]
            else:
                d[k] = gen_value(r, vt, aliases, hint, depth + 1)
        return d
    if low == "optional":
        return None if r.random() < 0.15 else gen_value(r, args[0] if args else None, aliases, hint, depth + 1)
    if low == "union":
        return gen_value(r, r.choice(args) if args else None, aliases, hint, depth + 1)
    if low in ("any", "object"):
        return r.choice([r.randint(-5, 9), "ab", [r.randint(0, 5) for _ in range(r.randint(0, 5))]])
    return [r.randint(-9, 20) for _ in range(_geom(r, 0, 12))]


def entry_signature(src, entry):
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == entry)
    pos = list(fn.args.posonlyargs) + list(fn.args.args)
    req = pos[:max(0, len(pos) - len(fn.args.defaults))]
    return [(a.arg, a.annotation) for a in req], _alias_table(tree)


def protocol_reprs(src, entry):
    """repr of every input of the protocol's own battery for this signature (to drop duplicates); read-only import of the REPO protocol module."""
    try:
        sys.path.insert(0, str(REPO))
        from experiments.final.protocol import synthesise_inputs  # noqa: PLC0415
        sig, _ = entry_signature(src, entry)
        inp = synthesise_inputs([ast.unparse(a) if a is not None else None for _, a in sig])
        return {repr(x if isinstance(x, tuple) else ((x,) if sig else ())) for x in (inp or [])}
    except Exception:  # noqa: BLE001
        return set()


def make_battery(base_path, entry, base_id, out):
    t0 = time.time()
    src = pathlib.Path(base_path).read_text()
    sig, aliases = entry_signature(src, entry)
    drop = protocol_reprs(src, entry)
    rng = random.Random(int(hashlib.sha256(("A4B-indep-v1|" + base_id).encode()).hexdigest()[:16], 16))
    mod = load_module(base_path)
    fn = getattr(mod, entry)
    valid, seen, ncand = [], set(drop), 0
    while len(valid) < TARGET and ncand < MAXCAND:
        ncand += 1
        args = tuple(gen_value(rng, ann, aliases, nm) for nm, ann in sig)
        key = repr(args)
        if key in seen:
            continue
        seen.add(key)
        res = call_once(fn, args, BATTERY_LIMIT)
        if res["exc"] is None:
            valid.append(key)
    status = "ok" if len(valid) >= MINVALID else "BLOCKED_NO_VALID_INPUTS"
    pathlib.Path(out).write_text(json.dumps({"gen": GEN, "base_id": base_id, "entry": entry, "arity": len(sig), "n_candidates": ncand, "n_valid": len(valid),
                                             "n_dropped_protocol_dup": len(drop), "status": status, "inputs": valid, "seconds": round(time.time() - t0, 3)}))


def run_file(path, entry, battery, out):
    t0 = time.time()
    bat = json.loads(pathlib.Path(battery).read_text())
    res = {"path": str(path), "entry": entry, "n": len(bat["inputs"]), "status": "ok", "per_input": []}
    try:
        mod = load_module(path)
        fn = getattr(mod, entry)
    except BaseException as e:  # noqa: BLE001
        res["status"] = f"load_error:{type(e).__name__}"
        res["per_input"] = [{"ret": None, "exc": "LOAD_ERROR", "msg": "", "out": "", "post": ""} for _ in bat["inputs"]]
        pathlib.Path(out).write_text(json.dumps(res))
        return
    n_to = 0
    for key in bat["inputs"]:
        if n_to >= 2:
            res["per_input"].append({"ret": None, "exc": "TIMEOUT", "msg": "", "out": "", "post": ""})
            continue
        r = call_once(fn, ast.literal_eval(key), CALL_LIMIT)
        if r["exc"] == "TIMEOUT":
            n_to += 1
        res["per_input"].append(r)
    res["n_timeouts"] = n_to
    res["seconds"] = round(time.time() - t0, 3)
    pathlib.Path(out).write_text(json.dumps(res))


# ======================================================================== parent side (each execution in its own subprocess, wall-clock bounded)
def _limits():
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
        resource.setrlimit(resource.RLIMIT_AS, (6 << 30, 6 << 30))
    except Exception:  # noqa: BLE001
        pass


def _sub(args, wall):
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
    work = OUT / "work"
    work.mkdir(parents=True, exist_ok=True)
    try:
        p = subprocess.run([sys.executable, str(HERE / "indep_exec.py")] + [str(a) for a in args], cwd=str(work), env=env, capture_output=True, text=True,
                           timeout=wall, preexec_fn=_limits)
        return p.returncode, (p.stderr or "")[-300:]
    except subprocess.TimeoutExpired:
        return -999, "wall_timeout"


def battery_path(base_id):
    return OUT / "batteries" / f"{base_id}.json"


def run_path(path):
    return OUT / "runs" / (hashlib.sha1(path.encode()).hexdigest()[:16] + ".json")


def ensure_battery(base_rec, ctx, wall=240):
    """battery dict (status ok) or None (BLOCKED / failure).  Generated from the BASE file only; cached on disk."""
    base_id = base_rec["base_id"]
    bp = battery_path(base_id)
    if not bp.exists():
        ft = ctx.trace(base_rec)
        if not ft.ok or not ft.entry:
            return None
        bp.parent.mkdir(parents=True, exist_ok=True)
        rc, err = _sub(["battery", ctx.repo / base_rec["path"], ft.entry, base_id, bp], wall)
        if rc != 0 or not bp.exists():
            bp.write_text(json.dumps({"base_id": base_id, "status": f"GEN_FAILED rc={rc} {err}", "inputs": []}))
    b = json.loads(bp.read_text())
    return b if b.get("status") == "ok" else None


def ensure_run(rec, base_rec, ctx, wall=150):
    """per-file behaviour record on the base program's battery (cached on disk, keyed by file path); None if the file/base is not computable."""
    rp = run_path(rec["path"])
    if rp.exists():
        r = json.loads(rp.read_text())
        return r if r.get("per_input") else None
    ft = ctx.trace(rec)
    if not ft.ok or not ft.entry or ensure_battery(base_rec, ctx) is None:
        return None
    rp.parent.mkdir(parents=True, exist_ok=True)
    rc, err = _sub(["run", ctx.repo / rec["path"], ft.entry, battery_path(rec["base_id"]), rp], wall)
    if rc != 0 or not rp.exists():
        rp.write_text(json.dumps({"path": rec["path"], "status": f"RUN_FAILED rc={rc} {err}", "per_input": [], "n": 0}))
    r = json.loads(rp.read_text())
    return r if r.get("per_input") else None


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "battery":
        make_battery(*sys.argv[2:6])
    elif mode == "run":
        run_file(*sys.argv[2:6])
