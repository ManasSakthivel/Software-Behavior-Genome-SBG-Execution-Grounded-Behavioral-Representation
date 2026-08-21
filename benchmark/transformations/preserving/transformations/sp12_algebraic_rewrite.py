"""
SP-12: ALGEBRAIC_REWRITE
Apply algebraic identity rewrites:
  x * 2  ->  x + x
  x - 0  ->  x
  x + 0  ->  x
  x * 1  ->  x
  x * 0  ->  0
  x / 1  ->  x
  x ** 1 ->  x
  x ** 0 ->  1
  0 + x  ->  x
  1 * x  ->  x
  x // 1 ->  x
  x - x  ->  0  (only for simple Name nodes to avoid side-effect duplication)
  x & x  ->  x  (same)
  x | x  ->  x  (same)
"""
import ast
import random
import copy


def _is_const(node: ast.expr, val) -> bool:
    return isinstance(node, ast.Constant) and node.value == val


def _same_name(a: ast.expr, b: ast.expr) -> bool:
    return (
        isinstance(a, ast.Name)
        and isinstance(b, ast.Name)
        and a.id == b.id
    )


class _AlgebraicRewriter(ast.NodeTransformer):
    def __init__(self, rng: random.Random):
        self.rng = rng

    def visit_BinOp(self, node: ast.BinOp):
        self.generic_visit(node)
        left, op, right = node.left, node.op, node.right

        # x * 2  ->  x + x  (only if left is a simple name, to avoid double eval)
        if isinstance(op, ast.Mult) and _is_const(right, 2) and isinstance(left, ast.Name):
            if self.rng.random() < 0.7:
                result = ast.BinOp(
                    left=copy.deepcopy(left),
                    op=ast.Add(),
                    right=copy.deepcopy(left),
                )
                ast.copy_location(result, node)
                ast.fix_missing_locations(result)
                return result

        # x - 0  ->  x
        if isinstance(op, ast.Sub) and _is_const(right, 0):
            return left

        # x + 0 or 0 + x  ->  x
        if isinstance(op, ast.Add):
            if _is_const(right, 0):
                return left
            if _is_const(left, 0):
                return right

        # x * 1 or 1 * x  ->  x
        if isinstance(op, ast.Mult):
            if _is_const(right, 1):
                return left
            if _is_const(left, 1):
                return right

        # x * 0 or 0 * x  ->  0  (only safe for numeric; skip if could be string/list)
        # Skip this rewrite: x * 0 is 0 for ints but [] for lists — not safe.

        # x / 1 or x // 1  ->  x
        if isinstance(op, (ast.Div, ast.FloorDiv)) and _is_const(right, 1):
            return left

        # x ** 1  ->  x
        if isinstance(op, ast.Pow) and _is_const(right, 1):
            return left

        # x ** 0  ->  1  (safe for numeric types)
        if isinstance(op, ast.Pow) and _is_const(right, 0) and isinstance(left, ast.Name):
            result = ast.Constant(value=1)
            ast.copy_location(result, node)
            return result

        # x - x  ->  0  (only simple Names)
        if isinstance(op, ast.Sub) and _same_name(left, right):
            result = ast.Constant(value=0)
            ast.copy_location(result, node)
            return result

        # x & x  ->  x, x | x  ->  x  (only simple Names)
        if isinstance(op, (ast.BitAnd, ast.BitOr)) and _same_name(left, right):
            return left

        return node


class AlgebraicRewriteTransformation:
    """SP-12: Apply algebraic identity rewrites (x*2->x+x, x-0->x, x+0->x, etc.)."""

    id = "SP-12"
    name = "ALGEBRAIC_REWRITE"

    def apply(self, source_code: str, seed: int) -> str:
        random.seed(seed)
        rng = random.Random(seed)
        tree = copy.deepcopy(ast.parse(source_code))
        rewriter = _AlgebraicRewriter(rng)
        new_tree = rewriter.visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    def validate(self, original: str, transformed: str) -> bool:
        try:
            ast.parse(original)
            ast.parse(transformed)
            return original != transformed
        except SyntaxError:
            return False
