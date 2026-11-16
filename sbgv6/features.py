"""Feature blocks A (invariants), B (transitions), C (dynamic CFG), R (return state), E (activation)."""
from __future__ import annotations
import ast, difflib, math
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
from sbgv6 import config as C

_KIND = {ast.If: "If", ast.For: "For", ast.While: "While", ast.Return: "Return", ast.Assign: "Assign",
         ast.AugAssign: "AugAssign", ast.AnnAssign: "Assign", ast.Expr: "Expr", ast.Raise: "Raise",
         ast.Try: "Try", ast.With: "With", ast.FunctionDef: "Def", ast.Break: "Break", ast.Continue: "Continue"}
_LOOPS = (ast.For, ast.While)


def stmt_maps(source: str):
    """lineno -> kind, lineno -> end_lineno, set(loop header linenos). Outer statements win a shared line."""
    kinds, ends, heads = {}, {}, set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return kinds, ends, heads
    for n in ast.walk(tree):
        if isinstance(n, ast.stmt) and n.lineno not in kinds:
            kinds[n.lineno] = _KIND.get(type(n), "Other")
            ends[n.lineno] = getattr(n, "end_lineno", n.lineno)
            if isinstance(n, _LOOPS):
                heads.add(n.lineno)
    return kinds, ends, heads


def _walk_frames(trace):
    """Yield (event, frame_id) with a call/return stack (events carry no frame id)."""
    stack, nxt = [], 0
    for ev in trace.events:
        if ev.event_type == "call":
            stack.append(nxt); nxt += 1
            yield ev, stack[-1]
        elif ev.event_type == "return":
            yield ev, (stack.pop() if stack else -1)
        else:
            yield ev, (stack[-1] if stack else -1)


def absval(r: str):
    """repr -> (type, numeric value|None, len|None). Truncated/unparseable reprs keep only a coarse type."""
    try:
        v = ast.literal_eval(r)
    except Exception:
        t = {"[": "list", "(": "tuple", "{": "dict", "'": "str", '"': "str"}.get(r[:1], "obj")
        return (t, None, None)
    if v is None:
        return ("NoneType", None, None)
    if isinstance(v, bool):
        return ("bool", int(v), None)
    if isinstance(v, (int, float)):
        return (type(v).__name__, v, None)
    if isinstance(v, (str, list, tuple, dict, set, frozenset)):
        return (type(v).__name__, None, len(v))
    return ("obj", None, None)


def _lb(n):
    return "0" if n == 0 else "1" if n == 1 else "2-3" if n <= 3 else "4+"


def _sign(x):
    return "neg" if x < 0 else "zero" if x == 0 else "pos"


# ---------------------------------------------------------------- A
def invariants(runs0, source) -> Dict[tuple, int]:
    """Asserted invariants {(point, slot|slotpair, predicate): support} over usable traces of run 0."""
    _, _, heads = stmt_maps(source)
    fn_ord: Dict[str, int] = {}
    slot_ord: Dict[int, Dict[str, int]] = defaultdict(dict)
    loop_ord: Dict[Tuple[int, int], int] = {}
    obs: Dict[tuple, List[dict]] = defaultdict(list)
    for tr in runs0:
        if tr.exception is not None and not tr.events:
            continue
        for ev, _fid in _walk_frames(tr):
            g = fn_ord.setdefault(ev.function_name, len(fn_ord))
            if ev.event_type == "call":
                pt = (g, "entry")
            elif ev.event_type == "return":
                pt = (g, "exit")
            elif ev.event_type == "line" and ev.lineno in heads:
                pt = (g, "loop%d" % loop_ord.setdefault((g, ev.lineno), sum(1 for k in loop_ord if k[0] == g)))
            else:
                continue
            so = slot_ord[g]
            vals = {}
            for name, r in ev.local_vars_snapshot.items():
                vals[so.setdefault(name, len(so))] = absval(r)
            obs[pt].append(vals)
    inv: Dict[tuple, int] = {}
    for pt, olist in obs.items():
        slots = sorted({s for o in olist for s in o})
        for s in slots:
            vs = [o[s] for o in olist if s in o]
            n = len(vs)
            if n < C.N_MIN:
                continue
            ts = {v[0] for v in vs}
            if len(ts) == 1:
                inv[(pt, s, "type=" + next(iter(ts)))] = n
            if "NoneType" not in ts:
                inv[(pt, s, "nonnull")] = n
            nums = [v[1] for v in vs]
            if all(x is not None for x in nums):
                sg = {_sign(x) for x in nums}
                if len(sg) == 1:
                    inv[(pt, s, "sign=" + next(iter(sg)))] = n
                if len(set(nums)) == 1 and abs(nums[0]) <= C.NUM_CAP:
                    inv[(pt, s, "const=%r" % (nums[0],))] = n
            lens = [v[2] for v in vs]
            if all(x is not None for x in lens):
                bs = {_lb(x) for x in lens}
                if len(bs) == 1:
                    inv[(pt, s, "len=" + next(iter(bs)))] = n
        numeric = [s for s in slots if all(o[s][1] is not None for o in olist if s in o)][: C.MAX_NUM_SLOTS]
        sized = [s for s in slots if all(o[s][2] is not None for o in olist if s in o)][: C.MAX_NUM_SLOTS]
        for i, s in enumerate(numeric):
            for t in numeric[i + 1:]:
                ps = [(o[s][1], o[t][1]) for o in olist if s in o and t in o]
                if len(ps) < C.N_MIN:
                    continue
                for name, f in (("eq", lambda a, b: a == b), ("lt", lambda a, b: a < b), ("gt", lambda a, b: a > b),
                                ("le", lambda a, b: a <= b), ("ge", lambda a, b: a >= b), ("ne", lambda a, b: a != b)):
                    if all(f(a, b) for a, b in ps):
                        inv[(pt, (s, t), name)] = len(ps); break
        for s in sized:
            for t in numeric:
                ps = [(o[s][2], o[t][1]) for o in olist if s in o and t in o]
                if len(ps) >= C.N_MIN and all(a == b for a, b in ps):
                    inv[(pt, (s, t), "len=")] = len(ps)
    return inv


def _w(n):
    return min(1.0, math.log2(1 + n) / math.log2(1 + C.K_W))


def d_invariant(i1, i2):
    keys = set(i1) | set(i2)
    if not keys:
        return None
    num = sum(min(_w(i1[k]), _w(i2[k])) for k in keys if k in i1 and k in i2)
    den = sum(max(_w(i1.get(k, 0)), _w(i2.get(k, 0))) for k in keys)
    return 1.0 - num / den if den else None


# ---------------------------------------------------------------- B / C
def token_seqs(runs0, source) -> List[list]:
    kinds, ends, _ = stmt_maps(source)
    out = []
    for tr in runs0:
        prev, seq = {}, []
        for ev, fid in _walk_frames(tr):
            if ev.event_type != "line":
                if ev.event_type == "return":
                    prev.pop(fid, None)
                continue
            p = prev.get(fid)
            if p is not None:
                kp, kc = kinds.get(p, "Other"), kinds.get(ev.lineno, "Other")
                tok = (kp, kc, ev.lineno <= p)
                if kp in ("If", "While", "For"):
                    tok += (p < ev.lineno <= ends.get(p, p),)
                seq.append(tok)
            prev[fid] = ev.lineno
        out.append(seq)
    return out


def jsd(p: Counter, q: Counter):
    sp, sq = sum(p.values()), sum(q.values())
    if not sp or not sq:
        return None
    d = 0.0
    for k in set(p) | set(q):
        a, b = p.get(k, 0) / sp, q.get(k, 0) / sq
        m = (a + b) / 2
        if a:
            d += 0.5 * a * math.log2(a / m)
        if b:
            d += 0.5 * b * math.log2(b / m)
    return min(1.0, max(0.0, d))


def cfg_summary(runs0, source):
    """Dynamic CFG on statement ids: WL-1 label histogram + size triple."""
    kinds, _, _ = stmt_maps(source)
    edges, visits = Counter(), Counter()
    for tr in runs0:
        prev = {}
        for ev, fid in _walk_frames(tr):
            if ev.event_type == "return":
                prev.pop(fid, None); continue
            if ev.event_type != "line":
                continue
            visits[ev.lineno] += 1
            if fid in prev:
                edges[(prev[fid], ev.lineno)] += 1
            prev[fid] = ev.lineno
    succ, pred = defaultdict(list), defaultdict(list)
    for (a, b), c in edges.items():
        succ[a].append((kinds.get(b, "Other"), math.ceil(math.log2(1 + c))))
        pred[b].append((kinds.get(a, "Other"), math.ceil(math.log2(1 + c))))
    wl = Counter()
    for n, v in visits.items():
        wl[(kinds.get(n, "Other"), tuple(sorted(succ[n])), tuple(sorted(pred[n])))] += v
    N, E = len(visits), len(edges)
    return wl, (math.log1p(N), math.log1p(E), float(E - N + 2) if N else 0.0)


def ratio(a, b):
    d = abs(a - b)
    return d / (1 + d)


# ---------------------------------------------------------------- R
def _exc_type(e):
    return None if e is None else str(e).split(":")[0].strip()


def _rv(tr):
    try:
        r = repr(tr.return_value)
    except Exception:
        r = "<unrepr>"
    t, num, ln = absval(r[:100])
    return (_exc_type(tr.exception), t, None if num is None else _sign(num), None if ln is None else _lb(ln)), \
           (_exc_type(tr.exception), r)


def return_state(t1, t2):
    """(d_R abstract, delta_out exact) over inputs usable on both sides, run 0."""
    n = a = e = 0
    for x, y in zip(t1, t2):
        if x.truncated or y.truncated:
            continue
        (sx, ex), (sy, ey) = _rv(x), _rv(y)
        n += 1; a += sx != sy; e += ex != ey
    return (a / n, e / n) if n else (None, None)


# ---------------------------------------------------------------- E
def _norm_lines(src):
    out = []
    for i, l in enumerate(src.splitlines(), 1):
        t = " ".join(l.split("#")[0].split())
        if t:
            out.append((i, t))
    return out


def changed_lines(src1, src2):
    a, b = _norm_lines(src1), _norm_lines(src2)
    sm = difflib.SequenceMatcher(a=[t for _, t in a], b=[t for _, t in b], autojunk=False)
    la, lb = set(), set()
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            la |= {a[k][0] for k in range(i1, i2)}
            lb |= {b[k][0] for k in range(j1, j2)}
    return la, lb


def activation(runs1, runs2, lam1, lam2):
    def frac(tr, lam):
        if not lam or not tr:
            return 0.0
        return sum(bool(set(t.coverage) & lam) for t in tr) / len(tr)
    return 0.5 * (frac(runs1, lam1) + frac(runs2, lam2)) if (lam1 or lam2) else None


def gated_divergence(s1, s2):
    vals = []
    for a, b in zip(s1, s2):
        L = max(len(a), len(b))
        if not L:
            continue
        j = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), None)
        if j is None:
            j = min(len(a), len(b)) if len(a) != len(b) else None
        vals.append(0.0 if j is None else 1 - j / L)
    return sum(vals) / len(vals) if vals else None
