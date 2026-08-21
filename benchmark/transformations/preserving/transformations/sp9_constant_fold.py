"""
SP-9: CONSTANT_FOLD
Pre-compute constant arithmetic/boolean/string expressions.
e.g., 2 * 3 -> 6, 10 // 2 -> 5, True and False -> False, "a" + "b" -> "ab"
"""
import ast
import random
import copy
import operator

_BINOP_EVAL = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.BitAnd: operator.and_,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
}

_UNARYOP_EVAL = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Invert: operator.invert,
    ast.Not: operator.not_,
}


def _safe_fold_binop(op_type, left_val, right_val):
    """Try to fold a binary op, returning (folded_value, True) or (None, False)."""
    fn = _BINOP_EVAL.get(op_type)
    if fn is None:
        return None, False
    try:
        # Guard against huge powers
        if op_type is ast.Pow and isinstance(right_val, int) and right_val > 64:
            return None, False
        # Guard against division by zero
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right_val == 0:
            return None, False
        result = fn(left_val, right_val)
        # Avoid huge results
        if isinstance(result, int) and abs(result) > 10 ** 15:
            return None, False
        return result, True
    except Exception:
        return None, False


class _ConstantFolder(ast.NodeTransformer):
    def visit_BinOp(self, node: ast.BinOp):
        self.generic_visit(node)
        if not (isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant)):
            return node
        left_val = node.left.value
        right_val = node.right.value
        # Only fold numeric and string types
        if not isinstance(left_val, (int, float, complex, str)) or not isinstance(right_val, (int, float, complex, str)):
            return node
        # Don't fold mixed string+numeric
        if type(left_val) != type(right_val) and not (isinstance(left_val, (int, float)) and isinstance(right_val, (int, float))):
            return node
        result, ok = _safe_fold_binop(type(node.op), left_val, right_val)
        if not ok:
            return node
        new_node = ast.Constant(value=result)
        ast.copy_location(new_node, node)
        return new_node

    def visit_UnaryOp(self, node: ast.UnaryOp):
        self.generic_visit(node)
        if not isinstance(node.operand, ast.Constant):
            return node
        op_type = type(node.op)
        fn = _UNARYOP_EVAL.get(op_type)
        if fn is None:
            return node
        try:
            result = fn(node.operand.value)
            new_node = ast.Constant(value=result)
            ast.copy_location(new_node, node)
            return new_node
        except Exception:
            return node

    def visit_BoolOp(self, node: ast.BoolOp):
        self.generic_visit(node)
        # Fold all-constant BoolOps
        if all(isinstance(v, ast.Constant) for v in node.values):
            try:
                if isinstance(node.op, ast.And):
                    result = all(v.value for v in node.values)
                    # Python's `and` returns the last truthy or first falsy value
                    val = node.values[0].value
                    for v in node.values:
                        val = val and v.value
                else:
                    val = node.values[0].value
                    for v in node.values:
                        val = val or v.value
                new_node = ast.Constant(value=val)
                ast.copy_location(new_node, node)
                return new_node
            except Exception:
                return node
        return node

    def visit_IfExp(self, node: ast.IfExp):
        self.generic_visit(node)
        if isinstance(node.test, ast.Constant):
            if node.test.value:
                return node.body
            else:
                return node.orelse
        return node


class ConstantFoldTransformation:
    """SP-9: Pre-compute constant arithmetic, boolean, and string expressions."""

    id = "SP-9"
    name = "CONSTANT_FOLD"

    def apply(self, source_code: str, seed: int) -> str:
        random.seed(seed)
        tree = copy.deepcopy(ast.parse(source_code))
        folder = _ConstantFolder()
        new_tree = folder.visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    def validate(self, original: str, transformed: str) -> bool:
        try:
            ast.parse(original)
            ast.parse(transformed)
            return original != transformed
        except SyntaxError:
            return False
