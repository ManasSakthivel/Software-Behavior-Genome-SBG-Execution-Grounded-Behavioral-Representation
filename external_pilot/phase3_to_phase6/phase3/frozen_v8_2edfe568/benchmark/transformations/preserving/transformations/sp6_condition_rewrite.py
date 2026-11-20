"""
SP-6: CONDITION_REWRITE
Rewrite boolean conditions using De Morgan's law and comparison negation:
  - a > b  ->  not (a <= b)
  - a < b  ->  not (a >= b)
  - a >= b ->  not (a < b)
  - a <= b ->  not (a > b)
  - a == b ->  not (a != b)
  - a != b ->  not (a == b)
  - not x  ->  (x is False or not bool(x)) -> simplest: remove double negation
Also: `if x and y` -> `if not (not x or not y)` (De Morgan)
"""
import ast
import random
import copy


_FLIP_OPS = {
    ast.Gt: ast.LtE,
    ast.Lt: ast.GtE,
    ast.GtE: ast.Lt,
    ast.LtE: ast.Gt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
}


class _ConditionRewriter(ast.NodeTransformer):
    def __init__(self, rng: random.Random):
        self.rng = rng
        self._changed = False

    def visit_Compare(self, node: ast.Compare):
        self.generic_visit(node)
        # Only rewrite simple single-op comparisons
        if len(node.ops) != 1:
            return node
        op_type = type(node.ops[0])
        if op_type not in _FLIP_OPS:
            return node
        if self.rng.random() < 0.6:
            flipped_op = _FLIP_OPS[op_type]()
            inner = ast.Compare(
                left=node.left,
                ops=[flipped_op],
                comparators=node.comparators,
            )
            result = ast.UnaryOp(op=ast.Not(), operand=inner)
            ast.copy_location(result, node)
            ast.fix_missing_locations(result)
            self._changed = True
            return result
        return node

    def visit_BoolOp(self, node: ast.BoolOp):
        self.generic_visit(node)
        # De Morgan: (a and b) -> not (not a or not b)
        #            (a or b)  -> not (not a and not b)
        if self.rng.random() < 0.4:
            if isinstance(node.op, ast.And):
                new_op = ast.Or()
            else:
                new_op = ast.And()
            negated_values = [
                ast.UnaryOp(op=ast.Not(), operand=v) for v in node.values
            ]
            inner = ast.BoolOp(op=new_op, values=negated_values)
            result = ast.UnaryOp(op=ast.Not(), operand=inner)
            ast.copy_location(result, node)
            ast.fix_missing_locations(result)
            self._changed = True
            return result
        return node


class ConditionRewriteTransformation:
    """SP-6: Rewrite comparisons and boolean expressions to logically equivalent forms."""

    id = "SP-6"
    name = "CONDITION_REWRITE"

    def apply(self, source_code: str, seed: int) -> str:
        random.seed(seed)
        rng = random.Random(seed)
        tree = copy.deepcopy(ast.parse(source_code))
        rewriter = _ConditionRewriter(rng)
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
