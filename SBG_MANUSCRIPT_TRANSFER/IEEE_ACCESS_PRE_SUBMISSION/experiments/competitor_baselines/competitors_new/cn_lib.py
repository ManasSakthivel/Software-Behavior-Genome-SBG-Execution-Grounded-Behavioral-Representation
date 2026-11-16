"""Shared library of the A4B competitor modules (pure stdlib; REPO and the trace cache are only ever READ).

Written independently of the predecessor modules in ``experiments/competitor_baselines/*.py`` (which are under audit by A4R and are NOT imported).

Uniform interface of every module in this package
-------------------------------------------------
    score_pair(base_record, variant_record, ctx) -> float        larger = more likely CHANGED (distance orientation)
    score_pair_multi(base_record, variant_record, ctx) -> dict   optional: all declared configurations of the module (name -> float)

``record``  = dict ``{"pop": "v9c_dev", "base_id": "ds_deque_ops", "path": "benchmark/.../x.py", ["pair_id": ...]}``  (``path`` is the population field
              ``base_path`` / ``variant_path``).  For unit tests a record may carry ``"source"`` (str) and/or ``"trace"`` (dict in the trace-cache schema,
              see PROTOCOL section 3) which then override the file system.
``ctx``     = :class:`Ctx` (below): cached-trace loader (``ctx.trace(rec)``), source reader (``ctx.source(rec)``), population rows
              (``ctx.population(name)``, ``ctx.records(row, pop)``) and the unsupervised train-only statistics (``ctx.idf_tokens()``, from v9c_train *sources*).
Return value NaN (float('nan')) = "not computable for this pair" (missing/failed trace, syntax error, ...); A4C must log and handle NaN explicitly.
"""
from __future__ import annotations

import ast
import builtins
import collections
import gzip
import hashlib
import io
import json
import keyword
import math
import pathlib
import re
import sys
import tokenize

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parents[2]
REPO = PKG.parent / "SBG"
CACHE = PKG / "results" / "raw" / "trace_cache"
POPDIR = PKG / "configs" / "populations"
POPS = ("v9c_train", "v9c_dev", "v9c_val", "v10_test")
NAN = float("nan")
BUILTINS = set(dir(builtins))


# ====================================================================== trace cache
def cache_file(pop: str, base_id: str, path: str) -> pathlib.Path:
    return CACHE / pop / base_id / (hashlib.sha1(path.encode()).hexdigest()[:12] + "__" + pathlib.Path(path).stem + ".json.gz")


_ADDR = re.compile(r"0x[0-9a-fA-F]+")
_FUNC = re.compile(r"<function [^>]*>")


def scrub(s):
    """Object addresses / function reprs are run-dependent -> neutralised."""
    return _ADDR.sub("0x", _FUNC.sub("<function>", s)) if isinstance(s, str) else s


class FileTrace:
    """One program file from the trace cache.

    ``.ok``      False if the cache entry is missing / the extraction failed / no traces
    ``.entry``   entry function name recorded by the frozen extraction
    ``.inputs``  list (one per protocol input) of dict(events=[(type, fn, lineno, snap_or_None)], ret, ret_type, exc, stdout, cov, trunc, input)
                 with the driver wrapper frames (``<lambda>`` at the wrapper line) removed and snapshots scrubbed.
    """

    def __init__(self, rec_json, path=""):
        self.path = path
        self.ok = False
        self.entry = None
        self.inputs = []
        self.failure = "cache_missing"
        self.extract_seconds = None
        if rec_json is None:
            return
        self.entry = rec_json.get("entry_function")
        self.extract_seconds = rec_json.get("extract_seconds")
        self.failure = rec_json.get("failure_kind")
        sb = rec_json.get("sandbox")
        if not rec_json.get("ok") or not sb or not sb.get("traces"):
            return
        self.ok = True
        self.inputs = [self._clean(t) for t in sb["traces"]]

    @staticmethod
    def _clean(t):
        ev = t["events"]
        wl = None
        if ev and ev[0][0] == "c" and ev[0][1] == "<lambda>" and isinstance(ev[0][3], dict) and ("entry_fn" in ev[0][3] or "args" in ev[0][3]):
            wl = ev[0][2]
        out = []
        for e in ev:
            if wl is not None and e[1] == "<lambda>" and e[2] == wl:
                continue
            snap = e[3]
            if isinstance(snap, dict):
                snap = {k: scrub(v) for k, v in snap.items()}
            out.append((e[0], e[1], e[2], snap))
        return {"events": out, "ret": t.get("ret"), "ret_type": t.get("ret_type"), "exc": t.get("exc"), "stdout": t.get("stdout"),
                "cov": t.get("cov"), "trunc": t.get("trunc"), "input": t.get("input")}


class Ctx:
    """Context passed to every ``score_pair``.  Cheap to construct; everything is lazy and memoised."""

    def __init__(self, repo=REPO, cache=CACHE, indep_runs_dir=None):
        self.repo = pathlib.Path(repo)
        self.cache = pathlib.Path(cache)
        self._traces = {}
        self._src = {}
        self._pops = {}
        self._idf = None
        self.indep_runs_dir = pathlib.Path(indep_runs_dir) if indep_runs_dir else None  # set by diffexec_indep (precomputed independent-input runs)

    # ---- traces / sources
    def trace(self, rec) -> FileTrace:
        key = rec.get("path"), rec.get("pop"), id(rec.get("trace")) if rec.get("trace") is not None else None
        if key in self._traces:
            return self._traces[key]
        if rec.get("trace") is not None:
            ft = FileTrace(rec["trace"], rec.get("path", ""))
        else:
            fn = cache_file(rec["pop"], rec["base_id"], rec["path"])
            if fn.exists():
                with gzip.open(fn, "rt") as f:
                    ft = FileTrace(json.load(f), rec["path"])
            else:
                ft = FileTrace(None, rec["path"])
        self._traces[key] = ft
        return ft

    def source(self, rec):
        if rec.get("source") is not None:
            return rec["source"]
        p = rec["path"]
        if p not in self._src:
            try:
                self._src[p] = (self.repo / p).read_text()
            except OSError:
                self._src[p] = None
        return self._src[p]

    # ---- populations
    def population(self, name):
        if name not in self._pops:
            self._pops[name] = json.loads((POPDIR / f"{name}.json").read_text())["rows"]
        return self._pops[name]

    @staticmethod
    def records(row, pop):
        b = {"pop": pop, "base_id": row["base_id"], "path": row["base_path"], "pair_id": row["pair_id"]}
        v = {"pop": pop, "base_id": row["base_id"], "path": row["variant_path"], "pair_id": row["pair_id"]}
        return b, v

    # ---- train-only statistics
    def idf_tokens(self):
        """IDF tables of identifier-normalised token n-grams (n=1,2,3), document = unique v9c_train source file (base or variant). Train sources only."""
        if self._idf is None:
            docs = sorted({r[k] for r in self.population("v9c_train") if r.get("in_primary_population") for k in ("base_path", "variant_path")})
            self._idf = fit_idf_tokens([self.source({"path": d}) for d in docs])
        return self._idf


# ====================================================================== sequence / set distances
def lev(a, b):
    """Levenshtein distance of two sequences of hashables (Myers/Hyyro bit-parallel; exact)."""
    a, b = list(a), list(b)
    p = 0
    n = min(len(a), len(b))
    while p < n and a[p] == b[p]:
        p += 1
    a, b = a[p:], b[p:]
    s = 0
    n = min(len(a), len(b))
    while s < n and a[-1 - s] == b[-1 - s]:
        s += 1
    if s:
        a, b = a[:len(a) - s], b[:len(b) - s]
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) > len(b):
        a, b = b, a
    m = len(a)
    full = (1 << m) - 1
    peq = {}
    for i, x in enumerate(a):
        peq[x] = peq.get(x, 0) | (1 << i)
    pv, mv, score, top = full, 0, m, 1 << (m - 1)
    for y in b:
        eq = peq.get(y, 0)
        xv = eq | mv
        xh = ((((eq & pv) + pv) ^ pv) | eq) & full
        ph = (mv | ~(xh | pv)) & full
        mh = pv & xh
        if ph & top:
            score += 1
        elif mh & top:
            score -= 1
        ph = ((ph << 1) | 1) & full
        mh = (mh << 1) & full
        pv = (mh | ~(xv | ph)) & full
        mv = ph & xv
    return score


def lev_norm(a, b):
    n = max(len(a), len(b))
    return lev(a, b) / n if n else 0.0


def lcs_len(a, b):
    """LCS length, bit-parallel (Hyyro 2004 / Crochemore et al. 2001)."""
    a, b = list(a), list(b)
    if not a or not b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    peq = {}
    for i, x in enumerate(a):
        peq[x] = peq.get(x, 0) | (1 << i)
    full = (1 << len(a)) - 1
    v = full
    for y in b:
        m = peq.get(y)
        if m:
            u = v & m
            v = ((v + u) | (v - u)) & full
    return len(a) - bin(v).count("1")


def unmatched_fraction(a, b):
    """Needleman-Wunsch global alignment with match 0 / mismatch 2 / gap 1 (== indel alignment): fraction of events of both sequences that stay
    unmatched = 1 - 2 LCS / (|a| + |b|)."""
    if not a and not b:
        return 0.0
    return 1.0 - 2.0 * lcs_len(a, b) / (len(a) + len(b))


def jaccard_dist(sa, sb):
    if not sa and not sb:
        return 0.0
    return 1.0 - len(sa & sb) / len(sa | sb)


def containment_dist(sa, sb):
    """1 - |A cap B| / max(|A|, |B|)  (symmetric two-way containment: 0 iff each birthmark is contained in the other)."""
    if not sa and not sb:
        return 0.0
    return 1.0 - len(sa & sb) / max(len(sa), len(sb))


def wjaccard_dist(ca, cb):
    """1 - sum(min)/sum(max) over multisets (Counter)."""
    if not ca and not cb:
        return 0.0
    inter = union = 0
    for k in ca.keys() | cb.keys():
        x, y = ca.get(k, 0), cb.get(k, 0)
        inter += x if x < y else y
        union += x if x > y else y
    return 1.0 - inter / union if union else 0.0


def cosine_dist(va, vb):
    if not va and not vb:
        return 0.0
    if not va or not vb:
        return 1.0
    num = sum(v * vb.get(k, 0.0) for k, v in va.items())
    na = math.sqrt(sum(v * v for v in va.values()))
    nb = math.sqrt(sum(v * v for v in vb.values()))
    return min(1.0, max(0.0, 1.0 - num / (na * nb))) if na and nb else 1.0


def kgrams(seq, k):
    if not seq:
        return set()
    if len(seq) < k:
        return {tuple(seq)}
    return {tuple(seq[i:i + k]) for i in range(len(seq) - k + 1)}


def mean(v):
    v = list(v)
    return sum(v) / len(v) if v else 0.0


# ====================================================================== source normalisation
def strip_docstrings(tree):
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = n.body
            if b and isinstance(b[0], ast.Expr) and isinstance(getattr(b[0], "value", None), ast.Constant) and isinstance(b[0].value.value, str):
                n.body = b[1:] or [ast.Pass()]
    return tree


def defined_names(tree):
    """Names *bound by the program itself* (functions, classes, parameters, assignment/loop/with/except/comprehension targets, global decls) minus
    names bound by imports (those refer to external code and keep their identity) -- only these are alpha-renamed."""
    d, imported = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            d.add(n.name)
        elif isinstance(n, ast.arg):
            d.add(n.arg)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            d.add(n.id)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            d.add(n.name)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            d.update(n.names)
        elif isinstance(n, ast.Import):
            imported.update((a.asname or a.name).split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            imported.update(a.asname or a.name for a in n.names)
    return d - imported


class _Alpha(ast.NodeTransformer):
    """alpha-renaming by order of first appearance in a pre-order walk (v0, v1, ...); builtins / imports / attributes / keyword names untouched."""

    def __init__(self, names):
        self.names = names
        self.m = {}

    def _n(self, s):
        if s in self.names:
            return self.m.setdefault(s, f"v{len(self.m)}")
        return s

    def visit_FunctionDef(self, node):
        node.name = self._n(node.name)
        return self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef

    def visit_arg(self, node):
        node.arg = self._n(node.arg)
        return self.generic_visit(node)

    def visit_Name(self, node):
        node.id = self._n(node.id)
        return node

    def visit_ExceptHandler(self, node):
        if node.name:
            node.name = self._n(node.name)
        return self.generic_visit(node)

    def visit_Global(self, node):
        node.names = [self._n(x) for x in node.names]
        return node

    visit_Nonlocal = visit_Global


def parse_normalised(src, rename=True):
    """AST with docstrings removed and (optionally) program-defined identifiers alpha-renamed.  Raises SyntaxError."""
    tree = strip_docstrings(ast.parse(src))
    if rename:
        tree = _Alpha(defined_names(tree)).visit(tree)
        ast.fix_missing_locations(tree)
    return tree


_SKIP_FIELDS = {"ctx", "type_comment", "kind"}


def ast_label(n):
    """Node label used by tree-edit distance / n-grams: type name + semantic payload (names after alpha, constants, operators)."""
    t = type(n).__name__
    if isinstance(n, ast.Name):
        return "Name:" + n.id
    if isinstance(n, ast.arg):
        return "arg:" + n.arg
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return t + ":" + n.name
    if isinstance(n, ast.Attribute):
        return "Attribute:" + n.attr
    if isinstance(n, ast.Constant):
        return "Constant:" + type(n.value).__name__ + ":" + repr(n.value)[:40]
    if isinstance(n, ast.keyword):
        return "keyword:" + str(n.arg)
    if isinstance(n, ast.alias):
        return "alias:" + n.name
    return t


def ast_tree(n, labels=True):
    """Nested ``(label, [children])`` tuples (context / operator-context singleton nodes dropped)."""
    kids = []
    for c in ast.iter_child_nodes(n):
        if isinstance(c, (ast.expr_context,)):
            continue
        kids.append(ast_tree(c, labels))
    return (ast_label(n) if labels else type(n).__name__, kids)


def tree_size(t):
    return 1 + sum(tree_size(c) for c in t[1])


def line_shape(line):
    """Whitespace-normalised source line with identifiers erased (keywords/operators/numbers kept, strings -> STR)."""
    out = []
    try:
        for t in tokenize.generate_tokens(io.StringIO(line.strip() + "\n").readline):
            if t.type in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER, tokenize.COMMENT):
                continue
            s = t.string
            if t.type == tokenize.NAME and not keyword.iskeyword(s) and s not in BUILTINS:
                s = "ID"
            elif t.type == tokenize.STRING:
                s = "STR"
            out.append(s)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return re.sub(r"\s+", " ", line.strip())
    return " ".join(out)


def token_seq(src, mode):
    """Token sequence for n-gram models. mode: 'alpha' (identifier -> v<k> by first appearance), 'id' (identifier -> ID), 'raw'."""
    out, m = [], {}
    try:
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER):
                continue
            s = t.string
            if t.type == tokenize.STRING:
                s = "STR"
            elif t.type == tokenize.NAME and not keyword.iskeyword(s) and s not in BUILTINS:
                if mode == "alpha":
                    s = m.setdefault(s, f"v{len(m)}")
                elif mode == "id":
                    s = "ID"
            out.append(s)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return []
    return out


def ngram_counter(seq, ns):
    c = collections.Counter()
    for n in ns:
        for i in range(max(0, len(seq) - n + 1)):
            c["\x1f".join(seq[i:i + n])] += 1
    return c


def fit_idf_tokens(sources, ns=(1, 2, 3), mode="alpha"):
    """IDF = log((N+1)/(df+1)) + 1 over token-n-gram sets of the given (train) sources; returns (idf dict, N)."""
    df = collections.Counter()
    N = 0
    for s in sources:
        if s is None:
            continue
        seq = token_seq(s, mode)
        if not seq:
            continue
        N += 1
        df.update(ngram_counter(seq, ns).keys())
    return ({g: math.log((N + 1) / (c + 1)) + 1.0 for g, c in df.items()}, N)


# ====================================================================== trace helpers
def anon_map(seq_of_names):
    """function-name -> f<k> by order of first appearance (SBG-style anonymisation)."""
    m = {}
    for x in seq_of_names:
        if x not in m:
            m[x] = f"f{len(m)}"
    return m


def paired_inputs(fa, fb):
    n = min(len(fa.inputs), len(fb.inputs))
    return [(fa.inputs[i], fb.inputs[i]) for i in range(n)]


def defined_functions(src):
    try:
        return {n.name for n in ast.walk(ast.parse(src)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    except SyntaxError:
        return set()


def lev_str_norm(a, b):
    """normalised Levenshtein distance of two strings (None treated as '')."""
    a, b = a or "", b or ""
    if a == b:
        return 0.0
    return lev_norm(a, b)


def append_registry(entry, agent="A4B"):
    p = PKG / "logs" / "registry" / f"{agent}.jsonl"
    with open(p, "a") as f:
        f.write(json.dumps(entry) + "\n")


def jdump(p, obj):
    pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(p).write_text(json.dumps(obj, indent=1, sort_keys=True))
