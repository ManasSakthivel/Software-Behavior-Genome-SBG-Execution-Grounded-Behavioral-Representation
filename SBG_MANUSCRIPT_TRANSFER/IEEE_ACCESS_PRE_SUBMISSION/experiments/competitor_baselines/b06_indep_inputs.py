"""B06b — INDEPENDENT-INPUT output differencing (class B, ADAPTED; Kessel&Atkinson-style behaviour sampling / ChangeGuard-comparator non-LLM core).

Worker modes (each runs in its own clean subprocess; REPO is only read):
  battery <base_rel_path> <entry_fn> <base_id> <out.json>   : generate a NEW input battery for a base program (own type-driven generator, filtered by the
                                                              ORIGINAL base program only: keep inputs on which the base returns without exception)
  run     <rel_path> <entry_fn> <battery.json> <out.json>   : execute one program file on the battery; record per input (ret repr, exception type/msg,
                                                              stdout, post-call argument repr); SIGALRM 1.5 s per input; <=2 timeouts then remaining inputs = TIMEOUT
The generator never reads variant files, labels or SBG scores.  Inputs equal to any protocol-battery input (same signature) are dropped (independence).
"""
from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import pathlib
import random
import signal
import sys
import time
import types

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parents[1]
REPO = PKG.parent / "SBG"
TARGET, MINVALID, MAXCAND = 40, 12, 600


class _TO(BaseException):
    pass


def _handler(signum, frame):
    raise _TO()


def load_module(rel):
    src = (REPO / rel).read_text()
    code = compile(src, str(REPO / rel), "exec")
    mod = types.ModuleType("_a4_prog")
    mod.__file__ = str(REPO / rel)
    sys.modules["_a4_prog"] = mod
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(code, mod.__dict__)
    return mod


def call_once(fn, args, limit):
    """returns dict(ret, exc_type, exc_msg, stdout, args) ; timeouts -> exc_type 'TIMEOUT'."""
    a = copy.deepcopy(args)
    buf = io.StringIO()
    ret = exc_t = exc_m = None
    signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, limit)
    try:
        with contextlib.redirect_stdout(buf):
            ret = repr(fn(*a))[:500]
    except _TO:
        exc_t, exc_m = "TIMEOUT", ""
    except RecursionError as e:
        exc_t, exc_m = "RecursionError", ""
    except BaseException as e:  # noqa: BLE001
        exc_t, exc_m = type(e).__name__, str(e)[:200]
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    try:
        post = repr(a)[:500]
    except BaseException:  # noqa: BLE001
        post = "<repr-error>"
    return {"ret": ret, "exc_type": exc_t, "exc_msg": exc_m, "stdout": buf.getvalue()[:500], "args": post}


# ------------------------------------------------------------------ generator
def _ints(r, lo, hi, n):
    return [r.randint(lo, hi) for _ in range(n)]


def _graph(r, directed, letters):
    n = r.randint(1, 5)
    keys = [chr(97 + i) for i in range(n)] if letters else list(range(n))
    g = {k: [] for k in keys}
    for _ in range(r.randint(0, 2 * n)):
        u, v = r.choice(keys), r.choice(keys)
        if u == v and r.random() < 0.7:
            continue
        if v not in g[u]:
            g[u].append(v)
        if not directed and u not in g[v]:
            g[v].append(u)
    return g


def _word(r, alpha, lo, hi):
    return "".join(r.choice(alpha) for _ in range(r.randint(lo, hi)))


LIST_T = [
    lambda r: _ints(r, -20, 40, r.randint(0, 12)),
    lambda r: _ints(r, 0, 9, r.randint(1, 10)),
    lambda r: _ints(r, 1, 12, r.randint(1, 8)),
    lambda r: [_ints(r, 0, 5, 2) for _ in range(r.randint(0, 8))],
    lambda r: [[r.randint(0, 5), r.randint(0, 5), r.randint(1, 9)] for _ in range(r.randint(0, 8))],
    lambda r: [_ints(r, 0, 1, c) for c in [r.randint(1, 4)] for _ in range(r.randint(1, 4))],
    lambda r: [_ints(r, -5, 9, c) for c in [r.randint(1, 4)] for _ in range(r.randint(1, 4))],
    lambda r: [_word(r, "abcd", 1, 5) for _ in range(r.randint(0, 7))],
    lambda r: (lambda n, m: [[1 if i == j else m[min(i, j)][max(i, j)] for j in range(n)] for i in range(n)])(
        (n := r.randint(1, 5)), [[r.randint(0, 1) for _ in range(5)] for _ in range(5)]),
    lambda r: [sorted([r.randint(0, 12), r.randint(0, 12)]) for _ in range(r.randint(0, 6))],
    lambda r: [r.choice(["push %d" % r.randint(0, 9), "pop", "min", "top"]) for _ in range(r.randint(0, 9))],
    lambda r: [r.choice([("push", r.randint(0, 9)), ("pop", None), ("min", None)]) for _ in range(r.randint(0, 9))],
    lambda r: [[r.randint(1, 9) for _ in range(c)] for c in [r.randint(1, 4)] for _ in range(c)],
]
STR_T = [
    lambda r: _word(r, "abc", 0, 10),
    lambda r: _word(r, "abcdefghijklmnopqrstuvwxyz", 0, 12),
    lambda r: " ".join(_word(r, "abcde", 1, 5) for _ in range(r.randint(0, 5))),
    lambda r: _word(r, "()[]{}", 0, 10),
    lambda r: r.choice([" ", "", "+", "-"]) + _word(r, "0123456789", 0, 7) + r.choice(["", " ", ".5", "e2", "x"]),
    lambda r: _word(r, "23456789", 1, 6),
    lambda r: _word(r, "aeioubcd", 0, 12),
]
INT_T = [lambda r: r.randint(0, 8), lambda r: r.randint(0, 15), lambda r: r.randint(-5, 20), lambda r: r.randint(1, 30), lambda r: r.randint(1, 5)]
DICT_T = [lambda r: _graph(r, True, False), lambda r: _graph(r, False, False), lambda r: _graph(r, True, True), lambda r: _graph(r, False, True)]
FLOAT_T = [lambda r: round(r.uniform(-10, 10), 2)]
BOOL_T = [lambda r: r.random() < 0.5]
POOLS = {"list": LIST_T, "str": STR_T, "int": INT_T, "dict": DICT_T, "float": FLOAT_T, "bool": BOOL_T}


def entry_signature(rel, entry):
    tree = ast.parse((REPO / rel).read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == entry)
    pos = list(fn.args.posonlyargs) + list(fn.args.args)
    req = pos[:max(0, len(pos) - len(fn.args.defaults))]
    return [ast.unparse(a.annotation) if a.annotation else None for a in req]


def protocol_inputs(annotations):
    sys.path.insert(0, str(REPO))
    from experiments.final.protocol import synthesise_inputs  # read-only import
    inp = synthesise_inputs(annotations)
    out = set()
    for x in inp or []:
        out.add(repr(x if isinstance(x, tuple) else ((x,) if annotations else ())))
    return out


def make_battery(base_rel, entry, base_id, out):
    t0 = time.time()
    sig = entry_signature(base_rel, entry)
    try:
        from_proto = protocol_inputs(sig)
    except Exception:  # noqa: BLE001
        from_proto = set()
    fams = []
    for a in sig:
        t = (a or "list").strip()
        fams.append(t.split("[")[0].lower() if t.split("[")[0].lower() in POOLS else "list")
    rng = random.Random(int(hashlib.sha1(base_id.encode()).hexdigest()[:8], 16))
    mod = load_module(base_rel)
    fn = getattr(mod, entry)
    valid, seen, n_cand = [], set(from_proto), 0
    while len(valid) < TARGET and n_cand < MAXCAND:
        n_cand += 1
        args = tuple(rng.choice(POOLS[f])(rng) for f in fams)
        key = repr(args)
        if key in seen:
            continue
        seen.add(key)
        res = call_once(fn, args, 0.5)
        if res["exc_type"] is None:
            valid.append(key)
    status = "ok" if len(valid) >= MINVALID else "BLOCKED_NO_VALID_INPUTS"
    pathlib.Path(out).write_text(json.dumps({"base_id": base_id, "entry": entry, "families": fams, "n_candidates": n_cand, "n_valid": len(valid), "status": status,
                                              "inputs": valid, "seconds": time.time() - t0}))


def run_file(rel, entry, battery, out):
    t0 = time.time()
    bat = json.loads(pathlib.Path(battery).read_text())
    res = {"path": rel, "entry": entry, "n": len(bat["inputs"]), "per_input": [], "status": "ok"}
    try:
        mod = load_module(rel)
        fn = getattr(mod, entry)
    except BaseException as e:  # noqa: BLE001
        res["status"] = f"load_error:{type(e).__name__}"
        res["per_input"] = [{"ret": None, "exc_type": "LOAD_ERROR", "exc_msg": "", "stdout": "", "args": ""} for _ in bat["inputs"]]
        pathlib.Path(out).write_text(json.dumps(res))
        return
    n_to = 0
    for key in bat["inputs"]:
        if n_to >= 2:
            res["per_input"].append({"ret": None, "exc_type": "TIMEOUT", "exc_msg": "", "stdout": "", "args": ""})
            continue
        r = call_once(fn, ast.literal_eval(key), 1.5)
        if r["exc_type"] == "TIMEOUT":
            n_to += 1
        res["per_input"].append(r)
    res["n_timeouts"] = n_to
    res["seconds"] = time.time() - t0
    pathlib.Path(out).write_text(json.dumps(res))


def pair_scores(ra, rb):
    """From two run files -> score dict (fraction/any over all inputs; first-11 budget; k-curve; exc-msg variant)."""
    n = min(len(ra["per_input"]), len(rb["per_input"]))
    core, msg = [], []
    for i in range(n):
        a, b = ra["per_input"][i], rb["per_input"][i]
        c = (a["ret"] != b["ret"]) or (a["exc_type"] != b["exc_type"]) or (a["stdout"] != b["stdout"]) or (a["args"] != b["args"])
        core.append(c)
        msg.append(c or a["exc_msg"] != b["exc_msg"])
    if not n:
        return {}
    f = lambda v: sum(v) / len(v)  # noqa: E731
    out = {"output_indep|frac40": f(core), "output_indep|any40": float(any(core)), "output_indep|frac40_excmsg": f(msg), "output_indep|frac11": f(core[:11]),
           "output_indep|any11": float(any(core[:11])), "output_indep|n_inputs": float(n)}
    for k in (1, 2, 4, 8, 16, 32):
        if n >= k:
            out[f"output_indep|any_k{k}"] = float(any(core[:k]))
            out[f"output_indep|frac_k{k}"] = f(core[:k])
    return out


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "battery":
        make_battery(*sys.argv[2:6])
    elif mode == "run":
        run_file(*sys.argv[2:6])
