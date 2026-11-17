"""Observation boundary comparator. Operates on the canonical typed forms produced by harness.py;
user __eq__/__repr__ are never called (they never leave the child). Type tag is identity."""
import json, math
from dataclasses import dataclass, field

KIND_ORDER = ("outcome", "exception", "side_effect", "api")


def _key(n):
    return json.dumps(n, sort_keys=True)


def node_eq(a, b, tol, ordered):
    if a[0] != b[0]:
        return False  # 1 vs 1.0, list vs tuple differ
    t = a[0]
    if t == "float":
        x, y = float(a[1]), float(b[1])
        if math.isnan(x) or math.isnan(y):
            return math.isnan(x) and math.isnan(y)
        if tol["rel"] or tol["abs"]:
            return math.isclose(x, y, rel_tol=tol["rel"], abs_tol=tol["abs"])
        return a[1] == b[1]  # exact binary64 (repr round-trips; -0.0 != 0.0)
    if t in ("list", "tuple", "set", "frozenset"):
        return len(a[1]) == len(b[1]) and all(node_eq(x, y, tol, ordered) for x, y in zip(a[1], b[1]))
    if t == "dict":
        return _pairs_eq(a[1], b[1], tol, ordered)
    if t == "obj":
        return a[1] == b[1] and _pairs_eq(a[2], b[2], tol, ordered)
    return a == b


def _pairs_eq(p, q, tol, ordered):
    if len(p) != len(q):
        return False
    if not ordered:
        p, q = sorted(p, key=lambda kv: _key(kv[0])), sorted(q, key=lambda kv: _key(kv[0]))
    return all(_key(k1) == _key(k2) and node_eq(v1, v2, tol, ordered) for (k1, v1), (k2, v2) in zip(p, q))


@dataclass
class Comparison:
    kinds: list = field(default_factory=list)
    lossy: bool = False  # equal on a channel that was lossy-canonicalised (blocks S2)

    @property
    def equal(self):
        return not self.kinds


def compare(a, b, h):
    """a, b: observations (dicts from the harness / runner). h: harness declaration."""
    tol, ordered, ch = h["float_tol"], h["ordered_mapping"], set(h["c_obs"])
    ks = set()
    ta, tb = a["t"], b["t"]
    if ta != tb:
        ks.add("api" if "bind_error" in (ta, tb) else "outcome")
    elif ta == "returned":
        if "ret" in ch and not node_eq(a["ret"], b["ret"], tol, ordered): ks.add("outcome")
    elif ta == "raised":
        if "exc" in ch and (a["type"] != b["type"] or (h["exc_message"] != "ignore" and a["msg"] != b["msg"])): ks.add("exception")
    elif ta == "exited":
        if a["code"] != b["code"]: ks.add("outcome")
    elif ta == "crashed":
        if a["signal"] != b["signal"]: ks.add("outcome")
    if "stdout" in a and "stdout" in b:  # both reached the call
        if "side:stdout" in ch and a["stdout"] != b["stdout"]: ks.add("side_effect")
        if "side:file" in ch and a["files"] != b["files"]: ks.add("side_effect")
        if "side:argmut" in ch and not node_eq(a["argmut"], b["argmut"], tol, ordered): ks.add("side_effect")
        if "side:global" in ch and not _pairs_eq([[["str", k], v] for k, v in a["globals"].items()],
                                                  [[["str", k], v] for k, v in b["globals"].items()], tol, ordered):
            ks.add("side_effect")
    return Comparison([k for k in KIND_ORDER if k in ks], bool(a.get("lossy") or b.get("lossy")))
