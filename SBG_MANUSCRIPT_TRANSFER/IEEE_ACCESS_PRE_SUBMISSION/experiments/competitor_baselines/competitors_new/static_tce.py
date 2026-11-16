"""static_tce -- Trivial-Compiler-Equivalence (TCE) analogue for Python + rename-robust normalised-bytecode / normalised-AST-hash baselines
(class A for the algorithm, ADAPTED to Python and to version-pair change scoring, source-only, output-free).

Papadakis et al. (ICSE 2015) declare a mutant *equivalent* iff the optimised object code of original and mutant is byte-identical.
Python analogue implemented here (``score_pair``):
  1. ``compile(src, ..., optimize=2)``  (asserts and docstrings dropped, constant folding / peephole optimisations of CPython 3.13),
  2. ``dis`` instruction stream of the module and, recursively, all nested code objects (in ``co_consts`` order),
  3. normalisation: local/cell/free variable operands -> index of first use in that code object; names of module-level program-defined functions/globals
     -> index of first appearance; attribute / external-global names kept; jump targets -> instruction index; line numbers/positions ignored; code
     objects replaced by their own recursively normalised stream; exception tables included.
  score = 0.0 if the two normalised streams are identical (=> predicted EQUIVALENT), else 1.0   (binary, like TCE).
``score_pair_multi`` additionally returns the soft versions needed to break ties:  ``bytecode_lev`` (normalised Levenshtein of the instruction streams),
``ast_hash`` (binary, alpha-normalised ``ast.dump`` equal -> 0), ``bytecode_O0`` (binary without optimisation).
"""
from __future__ import annotations

import dis
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cn_lib as L  # noqa: E402

_LOCAL_OPS = set(dis.haslocal) | set(dis.hasfree)
_NAME_OPS = set(dis.hasname)
_JUMP_OPS = set(dis.hasjump)


def _module_defs(code):
    """module-level bound names (functions / classes / globals assigned at module level)."""
    d = set()
    for ins in dis.get_instructions(code):
        if ins.opname in ("STORE_NAME",):
            d.add(ins.argval)
    return d


def _stream(code, mod_defs, gmap, out):
    insts = list(dis.get_instructions(code))
    idx = {ins.offset: i for i, ins in enumerate(insts)}
    lmap = {}

    def loc(nm):
        return lmap.setdefault(nm, f"L{len(lmap)}")

    def glob(nm):
        if nm in mod_defs:
            return gmap.setdefault(nm, f"G{len(gmap)}")
        return nm

    nested = []
    out.append(("CODE", code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount, code.co_flags & 0x7F))
    for ins in insts:
        op, v = ins.opcode, ins.argval
        name = ins.opname
        if op in _JUMP_OPS:
            out.append((name, idx.get(v, -1)))
        elif op in _LOCAL_OPS:
            out.append((name, tuple(loc(x) for x in v) if isinstance(v, tuple) else loc(v)))
        elif op in _NAME_OPS:
            if name in ("LOAD_ATTR", "STORE_ATTR", "DELETE_ATTR", "IMPORT_FROM", "LOAD_METHOD", "LOAD_SUPER_ATTR"):
                out.append((name, v))
            elif name in ("LOAD_GLOBAL", "STORE_GLOBAL", "LOAD_NAME", "STORE_NAME", "DELETE_NAME", "DELETE_GLOBAL"):
                out.append((name, glob(v)))
            else:
                out.append((name, v))
        elif name == "LOAD_CONST" or name == "RETURN_CONST":
            if hasattr(v, "co_code"):
                out.append((name, "<code>"))
                nested.append(v)
            else:
                out.append((name, repr(v)))
        else:
            out.append((name, ins.arg if not isinstance(v, str) else v))
    parse = getattr(dis, "_parse_exception_table", None)
    if parse is not None:
        for e in parse(code):
            out.append(("EXC", idx.get(e.start, -1), idx.get(e.end, -1), idx.get(e.target, -1), e.depth, e.lasti))
    for c in nested:
        _stream(c, mod_defs, gmap, out)
    return out


def normalised_bytecode(src, optimize=2):
    code = compile(src, "<a4b>", "exec", optimize=optimize, dont_inherit=True)
    return _stream(code, _module_defs(code), {}, [])


def _bc(rec, ctx, optimize):
    src = ctx.source(rec)
    if src is None:
        return None
    try:
        return normalised_bytecode(src, optimize)
    except (SyntaxError, ValueError, RecursionError):
        return None


def score_pair(base_record, variant_record, ctx):
    a, b = _bc(base_record, ctx, 2), _bc(variant_record, ctx, 2)
    if a is None or b is None:
        return L.NAN
    return 0.0 if a == b else 1.0


def score_pair_multi(base_record, variant_record, ctx):
    a2, b2 = _bc(base_record, ctx, 2), _bc(variant_record, ctx, 2)
    a0, b0 = _bc(base_record, ctx, 0), _bc(variant_record, ctx, 0)
    out = {}
    if a2 is not None and b2 is not None:
        out["tce_bytecode_O2"] = 0.0 if a2 == b2 else 1.0
        out["bytecode_lev_O2"] = L.lev_norm([repr(x) for x in a2], [repr(x) for x in b2])
    else:
        out["tce_bytecode_O2"] = out["bytecode_lev_O2"] = L.NAN
    out["tce_bytecode_O0"] = (0.0 if a0 == b0 else 1.0) if (a0 is not None and b0 is not None) else L.NAN
    try:
        ta = L.parse_normalised(ctx.source(base_record))
        tb = L.parse_normalised(ctx.source(variant_record))
        import ast
        out["tce_ast_alpha"] = 0.0 if ast.dump(ta) == ast.dump(tb) else 1.0
    except (SyntaxError, TypeError):
        out["tce_ast_alpha"] = L.NAN
    return out
