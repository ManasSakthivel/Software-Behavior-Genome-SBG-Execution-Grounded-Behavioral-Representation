"""B02b / B02c — own static baselines (class A, ADAPTED) and Trivial-Compiler-Equivalence analogue.

All computed from source text only (REPO read-only). Rename-invariant variants use alpha-renaming (first-appearance order).
"""
from __future__ import annotations

import ast
import builtins
import collections
import dis
import io
import keyword
import math
import tokenize

from bl_common import REPO, lev_norm, cosine_dist

BUILTINS = set(dir(builtins))
STATIC_CONFIGS = ["tok_lev_raw", "tok_lev_alpha", "astseq_lev_types", "astseq_lev_alpha", "tfidf2", "tfidf3", "bytecode_lev", "tce_ast", "tce_bytecode"]


def _strip_doc(body):
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        return body[1:] or [ast.Pass()]
    return body


class _Alpha(ast.NodeTransformer):
    def __init__(self):
        self.m = {}

    def _n(self, name):
        if name in BUILTINS and name not in self.m:
            return name
        return self.m.setdefault(name, f"v{len(self.m)}")

    def generic_visit(self, node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            node.body = _strip_doc(node.body)
        return super().generic_visit(node)

    def visit_FunctionDef(self, node):
        node.name = self._n(node.name)
        return self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        node.name = self._n(node.name)
        return self.generic_visit(node)

    def visit_arg(self, node):
        node.arg = self._n(node.arg)
        return self.generic_visit(node)

    def visit_Name(self, node):
        node.id = self._n(node.id)
        return node


def alpha_tree(src):
    return _Alpha().visit(ast.parse(src))


def ast_seq(tree, with_names):
    out = []
    stack = [tree]
    while stack:                                       # pre-order
        n = stack.pop()
        name = type(n).__name__
        if with_names:
            if isinstance(n, ast.Name):
                name += ":" + n.id
            elif isinstance(n, ast.arg):
                name += ":" + n.arg
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name += ":" + n.name
            elif isinstance(n, ast.Attribute):
                name += ":" + n.attr
            elif isinstance(n, ast.Constant):
                name += ":" + repr(n.value)
        out.append(name)
        stack.extend(reversed(list(ast.iter_child_nodes(n))))
    return out


def tok_seq(src, alpha):
    out, m = [], {}
    try:
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER):
                continue
            s = t.string
            if t.type == tokenize.STRING:
                s = "STR"
            elif alpha and t.type == tokenize.NAME and not keyword.iskeyword(s) and s not in BUILTINS:
                s = m.setdefault(s, f"v{len(m)}")
            out.append(s)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return []
    return out


_NAMEARG = {"LOAD_FAST", "STORE_FAST", "DELETE_FAST", "LOAD_GLOBAL", "STORE_GLOBAL", "LOAD_NAME", "STORE_NAME", "LOAD_ATTR", "STORE_ATTR", "LOAD_DEREF",
            "STORE_DEREF", "LOAD_FAST_LOAD_FAST", "STORE_FAST_STORE_FAST", "STORE_FAST_LOAD_FAST", "LOAD_FAST_CHECK", "LOAD_FAST_AND_CLEAR", "LOAD_CLOSURE",
            "LOAD_FROM_DICT_OR_GLOBALS", "LOAD_SUPER_ATTR", "IMPORT_NAME", "IMPORT_FROM", "MAKE_CELL", "COPY_FREE_VARS", "LOAD_LOCALS"}


def bytecode_seq(src):
    try:
        code = compile(src, "<a4>", "exec")
    except SyntaxError:
        return []
    out = []

    def rec(co):
        for ins in dis.get_instructions(co):
            op = ins.opname
            if op in _NAMEARG or "JUMP" in op or op.startswith("FOR_ITER") or op in ("SEND", "END_SEND"):
                out.append(op)
            elif op == "LOAD_CONST" or op == "RETURN_CONST":
                v = ins.argval
                out.append(op + ":" + ("<code>" if hasattr(v, "co_code") else repr(v)))
            else:
                out.append(op + (":" + str(ins.argrepr) if ins.argrepr and op in ("COMPARE_OP", "BINARY_OP", "CALL_INTRINSIC_1", "CONTAINS_OP", "IS_OP") else ""))
        for c in co.co_consts:
            if hasattr(c, "co_code"):
                rec(c)
    rec(code)
    return out


def _ngram_vec(seq, n, idf, N):
    tf = collections.Counter("\x1f".join(seq[i:i + n]) for i in range(max(0, len(seq) - n + 1)))
    default = math.log((N + 1) / 1.0) + 1.0
    return {g: c * idf.get(g, default) for g, c in tf.items()}


class StaticFeaturizer:
    """Caches per-file sequences; idf = {n: ({gram: idf}, N)} fitted on v9c_train sources only."""

    def __init__(self, idf=None):
        self.cache = {}
        self.idf = idf

    def file(self, rel):
        if rel in self.cache:
            return self.cache[rel]
        try:
            src = (REPO / rel).read_text()
        except OSError:
            self.cache[rel] = None
            return None
        d = {"tok_raw": tok_seq(src, False), "tok_alpha": tok_seq(src, True), "bc": bytecode_seq(src)}
        try:
            t = alpha_tree(src)
            d["ast_types"] = ast_seq(t, False)
            d["ast_alpha"] = ast_seq(t, True)
            d["ast_dump"] = ast.dump(t)
        except SyntaxError:
            d["ast_types"] = d["ast_alpha"] = []
            d["ast_dump"] = None
        self.cache[rel] = d
        return d

    def pair(self, base_rel, var_rel):
        a, b = self.file(base_rel), self.file(var_rel)
        if a is None or b is None:
            return {}
        out = {"tok_lev_raw": lev_norm(a["tok_raw"], b["tok_raw"]), "tok_lev_alpha": lev_norm(a["tok_alpha"], b["tok_alpha"]),
               "astseq_lev_types": lev_norm(a["ast_types"], b["ast_types"]), "astseq_lev_alpha": lev_norm(a["ast_alpha"], b["ast_alpha"]),
               "bytecode_lev": lev_norm(a["bc"], b["bc"]),
               "tce_ast": 0.0 if (a["ast_dump"] is not None and a["ast_dump"] == b["ast_dump"]) else 1.0,
               "tce_bytecode": 0.0 if (a["bc"] and a["bc"] == b["bc"]) else 1.0}
        if self.idf:
            for n in (2, 3):
                idf, N = self.idf[n]
                out[f"tfidf{n}"] = cosine_dist(_ngram_vec(a["ast_alpha"], n, idf, N), _ngram_vec(b["ast_alpha"], n, idf, N))
        return out


def fit_idf(featurizer, rel_paths):
    """Inverse document frequency of alpha-AST n-grams over unique train source files (unsupervised, train only)."""
    docs = sorted(set(rel_paths))
    out = {}
    for n in (2, 3):
        df = collections.Counter()
        N = 0
        for rel in docs:
            d = featurizer.file(rel)
            if not d:
                continue
            seq = d["ast_alpha"]
            N += 1
            df.update({"\x1f".join(seq[i:i + n]) for i in range(max(0, len(seq) - n + 1))})
        out[n] = ({g: math.log((N + 1) / (c + 1)) + 1.0 for g, c in df.items()}, N)
    return out
