"""
generate_v5_pairs.py
Generate transformation variant pairs for the 25 V5 base programs.
Produces:
  - benchmark/v5/variants/<base_id>__<transform>_s0.py  (one variant per transform)
  - benchmark/v5/pairs_v5.jsonl
  - artifacts/v5/BENCHMARK_V5_PAIRS_MANIFEST.json
"""

import ast
import copy
import json
import os
import sys
import textwrap
import traceback
from pathlib import Path
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
BASE_DIR = ROOT / "benchmark" / "v5" / "corpus" / "base_programs"
VARIANT_DIR = ROOT / "benchmark" / "v5" / "variants"
JSONL_PATH = ROOT / "benchmark" / "v5" / "pairs_v5.jsonl"
MANIFEST_PATH = ROOT / "artifacts" / "v5" / "BENCHMARK_V5_PAIRS_MANIFEST.json"

VARIANT_DIR.mkdir(parents=True, exist_ok=True)
(ROOT / "artifacts" / "v5").mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# AST helpers
# ──────────────────────────────────────────────────────────────────────────────

def parse_source(src: str) -> Optional[ast.Module]:
    try:
        return ast.parse(src)
    except SyntaxError:
        return None


def unparse(tree: ast.AST) -> str:
    return ast.unparse(tree)


def is_valid_python(src: str) -> bool:
    try:
        ast.parse(src)
        return True
    except SyntaxError:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# SP-1 — Variable rename: add "_v" suffix to all local variable names
#         in function bodies (excludes params, globals, builtins).
# ──────────────────────────────────────────────────────────────────────────────

class SP1Renamer(ast.NodeTransformer):
    """Rename local variables by appending '_v' suffix inside function bodies."""

    BUILTINS = set(dir(__builtins__) if isinstance(__builtins__, dict) else dir(__builtins__))
    SKIP = {'self', 'cls', 'True', 'False', 'None', '__name__', '__main__'}

    def __init__(self):
        self._in_func = 0
        self._locals: set = set()

    def visit_FunctionDef(self, node):
        self._in_func += 1
        # collect local names first
        old_locals = self._locals
        self._locals = self._collect_locals(node)
        node = self.generic_visit(node)
        self._locals = old_locals
        self._in_func -= 1
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def _collect_locals(self, func_node) -> set:
        names = set()
        for n in ast.walk(func_node):
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        names.add(t.id)
            elif isinstance(n, (ast.AugAssign, ast.AnnAssign)):
                if isinstance(n.target, ast.Name):
                    names.add(n.target.id)
            elif isinstance(n, ast.For):
                if isinstance(n.target, ast.Name):
                    names.add(n.target.id)
            elif isinstance(n, ast.NamedExpr):
                if isinstance(n.target, ast.Name):
                    names.add(n.target.id)
            elif isinstance(n, (ast.comprehension,)):
                if isinstance(n.target, ast.Name):
                    names.add(n.target.id)
            elif isinstance(n, ast.withitem):
                if n.optional_vars and isinstance(n.optional_vars, ast.Name):
                    names.add(n.optional_vars.id)
        # exclude params
        if isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in func_node.args.args + func_node.args.posonlyargs + func_node.args.kwonlyargs:
                names.discard(arg.arg)
            if func_node.args.vararg:
                names.discard(func_node.args.vararg.arg)
            if func_node.args.kwarg:
                names.discard(func_node.args.kwarg.arg)
        names -= self.SKIP
        names -= self.BUILTINS
        return names

    def _rename(self, name: str) -> str:
        if self._in_func > 0 and name in self._locals and not name.endswith('_v'):
            return name + '_v'
        return name

    def visit_Name(self, node):
        node.id = self._rename(node.id)
        return node


def sp1_variable_rename(src: str) -> Optional[str]:
    tree = parse_source(src)
    if tree is None:
        return None
    try:
        new_tree = SP1Renamer().visit(copy.deepcopy(tree))
        ast.fix_missing_locations(new_tree)
        result = unparse(new_tree)
        if result == unparse(tree):
            # Nothing changed – fall back to simple comment header approach
            return None
        return result if is_valid_python(result) else None
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# SP-2 — Function rename: add "_fn" prefix to all non-dunder, non-main
#         function definitions and their call sites.
# ──────────────────────────────────────────────────────────────────────────────

class SP2FuncRenamer(ast.NodeTransformer):
    SKIP_PREFIXES = ('__', 'test_', '_')

    def __init__(self, names: set):
        self._names = names  # set of function names to rename

    def visit_FunctionDef(self, node):
        if node.name in self._names:
            node.name = 'fn_' + node.name
        self.generic_visit(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in self._names:
            node.func.id = 'fn_' + node.func.id
        elif isinstance(node.func, ast.Attribute) and node.func.attr in self._names:
            node.func.attr = 'fn_' + node.func.attr
        self.generic_visit(node)
        return node


def _collect_function_names(src: str) -> set:
    tree = parse_source(src)
    if tree is None:
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if (not name.startswith('__') and
                    not name.startswith('test_') and
                    not name.startswith('_') and
                    name != 'main'):
                names.add(name)
    return names


def sp2_function_rename(src: str) -> Optional[str]:
    tree = parse_source(src)
    if tree is None:
        return None
    names = _collect_function_names(src)
    if not names:
        return None
    try:
        new_tree = SP2FuncRenamer(names).visit(copy.deepcopy(tree))
        ast.fix_missing_locations(new_tree)
        result = unparse(new_tree)
        if result == unparse(tree):
            return None
        return result if is_valid_python(result) else None
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# SP-4 — Dead code: insert `if False: pass` at the start of each function body.
# ──────────────────────────────────────────────────────────────────────────────

class SP4DeadCodeInserter(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        dead = ast.parse("if False:\n    pass").body[0]
        node.body.insert(0, dead)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef


def sp4_dead_code(src: str) -> Optional[str]:
    tree = parse_source(src)
    if tree is None:
        return None
    try:
        new_tree = SP4DeadCodeInserter().visit(copy.deepcopy(tree))
        ast.fix_missing_locations(new_tree)
        result = unparse(new_tree)
        return result if is_valid_python(result) else None
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# SP-8 — Comment insertion: add `# no-op` comments between top-level statements
#         in every function body (implemented as pass-through since ast.unparse
#         strips comments – we do text-level insertion instead).
# ──────────────────────────────────────────────────────────────────────────────

def sp8_comment_insert(src: str) -> Optional[str]:
    """Insert a '# no-op' comment after the docstring of each function."""
    if not is_valid_python(src):
        return None
    lines = src.split('\n')
    new_lines = []
    in_func = False
    func_indent = 0
    for i, line in enumerate(lines):
        new_lines.append(line)
        stripped = line.lstrip()
        if stripped.startswith('def ') or stripped.startswith('async def '):
            in_func = True
            func_indent = len(line) - len(stripped)
        elif in_func and stripped.startswith('"""') and i > 0:
            # After opening docstring line, if it's a one-liner or closing """
            pass
        elif in_func and stripped and not stripped.startswith('#'):
            # Insert a no-op comment on the line after the first real statement
            indent = ' ' * (func_indent + 4)
            new_lines.insert(-1, f'{indent}# no-op')
            in_func = False
    result = '\n'.join(new_lines)
    return result if is_valid_python(result) else None


# ──────────────────────────────────────────────────────────────────────────────
# SC-1 — Off-by-one in range: find first range(n) and change to range(n+1)
# ──────────────────────────────────────────────────────────────────────────────

class SC1OffByOne(ast.NodeTransformer):
    def __init__(self):
        self._done = False

    def visit_Call(self, node):
        if not self._done:
            if (isinstance(node.func, ast.Name) and node.func.id == 'range' and
                    len(node.args) >= 1):
                # Change last arg (stop): add 1
                last = node.args[-1]
                node.args[-1] = ast.BinOp(
                    left=copy.deepcopy(last),
                    op=ast.Add(),
                    right=ast.Constant(value=1)
                )
                self._done = True
        self.generic_visit(node)
        return node


def sc1_off_by_one(src: str) -> Optional[str]:
    tree = parse_source(src)
    if tree is None:
        return None
    try:
        transformer = SC1OffByOne()
        new_tree = transformer.visit(copy.deepcopy(tree))
        if not transformer._done:
            return None
        ast.fix_missing_locations(new_tree)
        result = unparse(new_tree)
        orig = unparse(tree)
        if result == orig:
            return None
        return result if is_valid_python(result) else None
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# SC-3 — Operator swap: find first >= / <= / > / < and swap it
# ──────────────────────────────────────────────────────────────────────────────

_OP_SWAP = {
    ast.GtE: ast.Gt,
    ast.LtE: ast.Lt,
    ast.Gt:  ast.GtE,
    ast.Lt:  ast.LtE,
}


class SC3OperatorSwap(ast.NodeTransformer):
    def __init__(self):
        self._done = False

    def visit_Compare(self, node):
        if not self._done:
            for idx, op in enumerate(node.ops):
                op_type = type(op)
                if op_type in _OP_SWAP:
                    node.ops[idx] = _OP_SWAP[op_type]()
                    self._done = True
                    break
        self.generic_visit(node)
        return node


def sc3_operator_swap(src: str) -> Optional[str]:
    tree = parse_source(src)
    if tree is None:
        return None
    try:
        transformer = SC3OperatorSwap()
        new_tree = transformer.visit(copy.deepcopy(tree))
        if not transformer._done:
            return None
        ast.fix_missing_locations(new_tree)
        result = unparse(new_tree)
        orig = unparse(tree)
        if result == orig:
            return None
        return result if is_valid_python(result) else None
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# SC-5 — Wrong return: find first `return <numeric-expr>` in a non-test
#         function and change it to `return <expr> + 1`
# ──────────────────────────────────────────────────────────────────────────────

class SC5WrongReturn(ast.NodeTransformer):
    def __init__(self):
        self._done = False
        self._in_test = False

    def visit_FunctionDef(self, node):
        was_test = self._in_test
        if node.name.startswith('test_'):
            self._in_test = True
        self.generic_visit(node)
        self._in_test = was_test
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Return(self, node):
        if not self._done and not self._in_test and node.value is not None:
            val = node.value
            # Only mutate if the return value is not None/True/False/string
            is_numeric = (
                isinstance(val, ast.Constant) and isinstance(val.value, (int, float)) or
                isinstance(val, ast.Name) or
                isinstance(val, ast.BinOp) or
                isinstance(val, ast.UnaryOp) or
                isinstance(val, ast.Subscript) or
                isinstance(val, ast.Attribute) or
                isinstance(val, ast.Call)
            )
            # Avoid mutating string/bool constants
            if isinstance(val, ast.Constant) and isinstance(val.value, (str, bool)):
                is_numeric = False
            if is_numeric:
                node.value = ast.BinOp(
                    left=copy.deepcopy(val),
                    op=ast.Add(),
                    right=ast.Constant(value=1)
                )
                self._done = True
        return node


def sc5_wrong_return(src: str) -> Optional[str]:
    tree = parse_source(src)
    if tree is None:
        return None
    try:
        transformer = SC5WrongReturn()
        new_tree = transformer.visit(copy.deepcopy(tree))
        if not transformer._done:
            return None
        ast.fix_missing_locations(new_tree)
        result = unparse(new_tree)
        orig = unparse(tree)
        if result == orig:
            return None
        return result if is_valid_python(result) else None
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# SC-10 — Wrong variable: in assignments `a = b op c` inside function bodies,
#          swap b for a previously-defined local variable (not b).
# ──────────────────────────────────────────────────────────────────────────────

class SC10WrongVariable(ast.NodeTransformer):
    def __init__(self):
        self._done = False

    def visit_FunctionDef(self, node):
        if self._done:
            return node
        # collect assigned names in order
        assigned: list = []
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assign):
                for tgt in stmt.targets:
                    if isinstance(tgt, ast.Name):
                        if isinstance(stmt.value, ast.BinOp):
                            # Try to replace left of BinOp with a previous var
                            left = stmt.value.left
                            if isinstance(left, ast.Name) and assigned:
                                # pick a different variable
                                candidates = [v for v in assigned if v != left.id]
                                if candidates and not self._done:
                                    stmt.value.left = ast.Name(
                                        id=candidates[-1],
                                        ctx=ast.Load()
                                    )
                                    self._done = True
                        assigned.append(tgt.id)
        self.generic_visit(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef


def sc10_wrong_variable(src: str) -> Optional[str]:
    tree = parse_source(src)
    if tree is None:
        return None
    try:
        transformer = SC10WrongVariable()
        new_tree = transformer.visit(copy.deepcopy(tree))
        if not transformer._done:
            return None
        ast.fix_missing_locations(new_tree)
        result = unparse(new_tree)
        orig = unparse(tree)
        if result == orig:
            return None
        return result if is_valid_python(result) else None
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Fallback transformations for when primary ones produce no diff
# ──────────────────────────────────────────────────────────────────────────────

def sp1_fallback(src: str) -> str:
    """Add a header comment — always produces a syntactically valid variant."""
    return "# sp1-variant: variable-renamed (no renameable locals found)\n" + src


def sp2_fallback(src: str) -> str:
    return "# sp2-variant: function-renamed (all fns private/test)\n" + src


def sp4_fallback(src: str) -> str:
    # Insert a module-level dead block
    return "if False:\n    pass\n" + src


def sp8_fallback(src: str) -> str:
    return "# sp8-variant: comment inserted\n# no-op\n" + src


def sc1_fallback(src: str) -> Optional[str]:
    """
    Multiple strategies for SC-1 when no range() exists:
    1. Replace first `== 0` comparison with `== -1`.
    2. Change first `while x < y` to `while x <= y` (extends by one iteration).
    3. Change first `while x <= y` to `while x < y` (reduces by one).
    4. Change first literal 1 inside a loop boundary to 2.
    """
    tree = parse_source(src)
    if tree is None:
        return None

    # Strategy 1: == 0  →  == -1
    class _Eq0(ast.NodeTransformer):
        def __init__(self): self._done = False
        def visit_Compare(self, node):
            if not self._done:
                for idx, (op, comp) in enumerate(zip(node.ops, node.comparators)):
                    if isinstance(op, ast.Eq) and isinstance(comp, ast.Constant) and comp.value == 0:
                        node.comparators[idx] = ast.Constant(value=-1)
                        self._done = True
                        break
            self.generic_visit(node)
            return node

    t = _Eq0()
    new_tree = t.visit(copy.deepcopy(tree))
    if t._done:
        ast.fix_missing_locations(new_tree)
        r = unparse(new_tree)
        if is_valid_python(r) and r != unparse(tree):
            return r

    # Strategy 2: change first while-condition < to <=
    class _WhileBound(ast.NodeTransformer):
        def __init__(self): self._done = False
        def visit_While(self, node):
            if not self._done and isinstance(node.test, ast.Compare):
                test = node.test
                for idx, op in enumerate(test.ops):
                    if isinstance(op, ast.Lt):
                        test.ops[idx] = ast.LtE()
                        self._done = True
                        break
                    elif isinstance(op, ast.LtE):
                        test.ops[idx] = ast.Lt()
                        self._done = True
                        break
            self.generic_visit(node)
            return node

    t2 = _WhileBound()
    new_tree2 = t2.visit(copy.deepcopy(tree))
    if t2._done:
        ast.fix_missing_locations(new_tree2)
        r2 = unparse(new_tree2)
        if is_valid_python(r2) and r2 != unparse(tree):
            return r2

    # Strategy 3: change first enumerate(x, start=1) to start=2
    class _EnumStart(ast.NodeTransformer):
        def __init__(self): self._done = False
        def visit_Call(self, node):
            if not self._done:
                if isinstance(node.func, ast.Name) and node.func.id == 'enumerate':
                    for kw in node.keywords:
                        if kw.arg == 'start' and isinstance(kw.value, ast.Constant):
                            kw.value = ast.Constant(value=kw.value.value + 1)
                            self._done = True
                            break
            self.generic_visit(node)
            return node

    t3 = _EnumStart()
    new_tree3 = t3.visit(copy.deepcopy(tree))
    if t3._done:
        ast.fix_missing_locations(new_tree3)
        r3 = unparse(new_tree3)
        if is_valid_python(r3) and r3 != unparse(tree):
            return r3

    return None


def sc3_fallback(src: str) -> Optional[str]:
    """Swap first `==` to `!=` as a semantic change."""
    tree = parse_source(src)
    if tree is None:
        return None

    class _EqSwap(ast.NodeTransformer):
        def __init__(self): self._done = False
        def visit_Compare(self, node):
            if not self._done:
                for idx, op in enumerate(node.ops):
                    if isinstance(op, ast.Eq):
                        node.ops[idx] = ast.NotEq()
                        self._done = True
                        break
                    elif isinstance(op, ast.NotEq):
                        node.ops[idx] = ast.Eq()
                        self._done = True
                        break
            self.generic_visit(node)
            return node

    t = _EqSwap()
    new_tree = t.visit(copy.deepcopy(tree))
    if not t._done:
        return None
    ast.fix_missing_locations(new_tree)
    result = unparse(new_tree)
    return result if is_valid_python(result) else None


def sc5_fallback(src: str) -> Optional[str]:
    """Change first numeric constant 0 to -1 inside a function."""
    tree = parse_source(src)
    if tree is None:
        return None

    class _ConstMut(ast.NodeTransformer):
        def __init__(self): self._done = False; self._in_func = False
        def visit_FunctionDef(self, node):
            if node.name.startswith('test_'): return node
            self._in_func = True
            self.generic_visit(node)
            self._in_func = False
            return node
        visit_AsyncFunctionDef = visit_FunctionDef
        def visit_Constant(self, node):
            if not self._done and self._in_func and node.value == 0 and isinstance(node.value, int):
                node.value = -1
                self._done = True
            return node

    t = _ConstMut()
    new_tree = t.visit(copy.deepcopy(tree))
    if not t._done:
        return None
    ast.fix_missing_locations(new_tree)
    result = unparse(new_tree)
    return result if is_valid_python(result) else None


def sc10_fallback(src: str) -> Optional[str]:
    """
    Multiple attempts to produce a semantic change when SC-10 primary fails:
    1. Change first `+= 1` to `+= 2`.
    2. Change first positive integer constant in a non-test function body by +1.
    3. Remove a 'not' from the first UnaryOp inside a non-test function.
    """
    tree = parse_source(src)
    if tree is None:
        return None

    # Attempt 1: AugAssign += 1 → += 2
    class _AugMut(ast.NodeTransformer):
        def __init__(self): self._done = False
        def visit_AugAssign(self, node):
            if not self._done and isinstance(node.op, ast.Add):
                if isinstance(node.value, ast.Constant) and node.value.value == 1:
                    node.value = ast.Constant(value=2)
                    self._done = True
            self.generic_visit(node)
            return node

    t = _AugMut()
    new_tree = t.visit(copy.deepcopy(tree))
    if t._done:
        ast.fix_missing_locations(new_tree)
        result = unparse(new_tree)
        if is_valid_python(result) and result != unparse(tree):
            return result

    # Attempt 2: change first positive integer constant in a non-test function
    class _ConstAdd(ast.NodeTransformer):
        def __init__(self): self._done = False; self._in_func = False
        def visit_FunctionDef(self, node):
            if node.name.startswith('test_'):
                return node
            self._in_func = True
            self.generic_visit(node)
            self._in_func = False
            return node
        visit_AsyncFunctionDef = visit_FunctionDef
        def visit_Constant(self, node):
            if not self._done and self._in_func:
                if isinstance(node.value, int) and node.value > 0 and node.value < 1000:
                    node.value = node.value + 1
                    self._done = True
            return node

    t2 = _ConstAdd()
    new_tree2 = t2.visit(copy.deepcopy(tree))
    if t2._done:
        ast.fix_missing_locations(new_tree2)
        result2 = unparse(new_tree2)
        if is_valid_python(result2) and result2 != unparse(tree):
            return result2

    # Attempt 3: remove first 'not' inside a non-test function
    class _BoolNeg(ast.NodeTransformer):
        def __init__(self): self._done = False; self._in_func = False
        def visit_FunctionDef(self, node):
            if node.name.startswith('test_'):
                return node
            self._in_func = True
            self.generic_visit(node)
            self._in_func = False
            return node
        visit_AsyncFunctionDef = visit_FunctionDef
        def visit_UnaryOp(self, node):
            if not self._done and self._in_func and isinstance(node.op, ast.Not):
                self._done = True
                return node.operand
            self.generic_visit(node)
            return node

    t3 = _BoolNeg()
    new_tree3 = t3.visit(copy.deepcopy(tree))
    if t3._done:
        ast.fix_missing_locations(new_tree3)
        result3 = unparse(new_tree3)
        if is_valid_python(result3) and result3 != unparse(tree):
            return result3

    return None


# ──────────────────────────────────────────────────────────────────────────────
# Transformation registry
# ──────────────────────────────────────────────────────────────────────────────

TRANSFORMS = {
    # (transform_id, is_sp, primary_fn, fallback_fn)
    'sp-1': ('SP-1', True,  sp1_variable_rename, sp1_fallback),
    'sp-2': ('SP-2', True,  sp2_function_rename, sp2_fallback),
    'sp-4': ('SP-4', True,  sp4_dead_code,       sp4_fallback),
    'sp-8': ('SP-8', True,  sp8_comment_insert,  sp8_fallback),
    'sc-1': ('SC-1', False, sc1_off_by_one,      sc1_fallback),
    'sc-3': ('SC-3', False, sc3_operator_swap,   sc3_fallback),
    'sc-5': ('SC-5', False, sc5_wrong_return,    sc5_fallback),
    'sc-10':('SC-10',False, sc10_wrong_variable, sc10_fallback),
}


# ──────────────────────────────────────────────────────────────────────────────
# Main generation loop
# ──────────────────────────────────────────────────────────────────────────────

def extract_program_id(src: str, filename: str) -> str:
    for line in src.splitlines()[:5]:
        if line.startswith('# program_id:'):
            return line.split(':', 1)[1].strip()
    return filename.replace('.py', '')


def main():
    base_files = sorted(BASE_DIR.glob('*.py'))
    print(f"Found {len(base_files)} base programs.")

    all_pairs = []
    stats = {
        'total_programs': 0,
        'total_pairs': 0,
        'by_transform': {},
        'sp_pairs': 0,
        'sc_pairs': 0,
        'failed': [],
    }

    dev_split_idx = 0

    for base_file in base_files:
        stats['total_programs'] += 1
        src = base_file.read_text()
        base_id = extract_program_id(src, base_file.name)
        print(f"\nProcessing {base_id} ...")

        for transform_key, (transform_type, is_sp, primary_fn, fallback_fn) in TRANSFORMS.items():
            variant_id = f"{base_id}__{transform_key}_s0"
            variant_filename = f"{variant_id}.py"
            variant_path = VARIANT_DIR / variant_filename

            # Try primary transformer
            variant_src = None
            method_used = 'primary'
            try:
                variant_src = primary_fn(src)
            except Exception as exc:
                print(f"  {transform_type} primary failed: {exc}")

            # If primary failed or produced nothing different, try fallback
            if variant_src is None or variant_src == src:
                method_used = 'fallback'
                try:
                    if callable(fallback_fn):
                        if isinstance(fallback_fn(""), str):
                            variant_src = fallback_fn(src)
                        else:
                            variant_src = fallback_fn(src)
                except Exception as exc:
                    print(f"  {transform_type} fallback also failed: {exc}")

            # Final validity check
            if variant_src is None:
                print(f"  ✗ {transform_type} FAILED — skipping")
                stats['failed'].append({'base_id': base_id, 'transform': transform_type, 'reason': 'both primary and fallback returned None'})
                continue

            if not is_valid_python(variant_src):
                print(f"  ✗ {transform_type} invalid Python — skipping")
                stats['failed'].append({'base_id': base_id, 'transform': transform_type, 'reason': 'invalid Python syntax'})
                continue

            # Warn if identical to base (SP is fine; SC should differ)
            if variant_src == src and not is_sp:
                print(f"  ⚠ {transform_type} produced identical SC variant")

            # Write variant file
            variant_path.write_text(variant_src)

            # Assign split: 60% dev, 40% val
            split = 'dev' if dev_split_idx % 5 < 3 else 'val'
            dev_split_idx += 1

            label_int = 0 if is_sp else 1
            label_str = 'EQUIVALENT' if is_sp else 'CHANGED'

            pair = {
                'pair_id': f"v5__{base_id}__{transform_key}_s0",
                'base_id': base_id,
                'variant_id': variant_id,
                'base_path': f"benchmark/v5/corpus/base_programs/{base_file.name}",
                'variant_path': f"benchmark/v5/variants/{variant_filename}",
                'transformation_type': transform_type,
                'semantic_relation': label_str,
                'expected_label': label_str,
                'label': label_int,
                'split': split,
                'seed': 0,
                'gt_tier': 'GT-T3',
                'confidence': 0.95,
                'hard_negative': False,
                'method_used': method_used,
            }
            all_pairs.append(pair)

            stats['total_pairs'] += 1
            stats['by_transform'][transform_type] = stats['by_transform'].get(transform_type, 0) + 1
            if is_sp:
                stats['sp_pairs'] += 1
            else:
                stats['sc_pairs'] += 1

            print(f"  ✓ {transform_type} ({method_used}) → {variant_filename}")

    # Write JSONL
    with open(JSONL_PATH, 'w') as f:
        for pair in all_pairs:
            f.write(json.dumps(pair) + '\n')

    # Write manifest
    manifest = {
        'version': 'v5',
        'generated_by': 'scripts/generate_v5_pairs.py',
        'statistics': stats,
        'pairs': all_pairs,
    }
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Print summary
    print("\n" + "="*60)
    print("V5 BENCHMARK PAIRS GENERATION COMPLETE")
    print("="*60)
    print(f"  Programs processed : {stats['total_programs']}")
    print(f"  Total pairs        : {stats['total_pairs']}")
    print(f"  SP pairs           : {stats['sp_pairs']}")
    print(f"  SC pairs           : {stats['sc_pairs']}")
    print(f"  Failed             : {len(stats['failed'])}")
    print(f"\n  Pairs by transform type:")
    for k, v in sorted(stats['by_transform'].items()):
        print(f"    {k:8s} : {v}")
    print(f"\n  JSONL  → {JSONL_PATH}")
    print(f"  Manifest → {MANIFEST_PATH}")
    if stats['failed']:
        print(f"\n  Failed cases:")
        for f in stats['failed']:
            print(f"    {f['base_id']} / {f['transform']} : {f['reason']}")

    return stats


if __name__ == '__main__':
    main()
