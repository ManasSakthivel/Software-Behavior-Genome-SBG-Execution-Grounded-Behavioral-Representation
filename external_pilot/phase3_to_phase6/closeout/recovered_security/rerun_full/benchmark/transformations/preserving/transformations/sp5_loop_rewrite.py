"""
SP-5: LOOP_REWRITE
Convert for-range loops to while loops, and list comprehensions to explicit for loops.
"""
import ast
import random
import copy


class _LoopRewriter(ast.NodeTransformer):
    """
    Two rewrites:
      1. for <var> in range(...) -> while <var> < ...:  (for-range -> while)
      2. [expr for var in iter] -> explicit for-loop appending to a list  (list comp -> for)
    """

    def __init__(self, rng: random.Random, mode: str):
        self.rng = rng
        self.mode = mode  # "for_to_while" | "listcomp_to_for" | "both"
        self._counter = 0

    def _fresh(self, base: str) -> str:
        self._counter += 1
        return f"_sbg_{base}_{self._counter}"

    def visit_For(self, node: ast.For):
        self.generic_visit(node)
        if self.mode not in ("for_to_while", "both"):
            return node
        # Only rewrite for var in range(...) with a simple Name target
        if not isinstance(node.target, ast.Name):
            return node
        if not (
            isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "range"
        ):
            return node

        args = node.iter.args
        var = node.target.id

        # Build start/stop/step from range args
        if len(args) == 1:
            start = ast.Constant(value=0)
            stop = args[0]
            step = ast.Constant(value=1)
        elif len(args) == 2:
            start = args[0]
            stop = args[1]
            step = ast.Constant(value=1)
        elif len(args) == 3:
            start = args[0]
            stop = args[1]
            step = args[2]
        else:
            return node

        # Detect negative step: ast.Constant(-1) OR ast.UnaryOp(USub, Constant(N))
        def _is_negative_step(s: ast.expr) -> bool:
            if isinstance(s, ast.Constant) and isinstance(s.value, int) and s.value < 0:
                return True
            if (
                isinstance(s, ast.UnaryOp)
                and isinstance(s.op, ast.USub)
                and isinstance(s.operand, ast.Constant)
                and isinstance(s.operand.value, int)
                and s.operand.value > 0
            ):
                return True
            return False

        if _is_negative_step(step):
            # while var > stop: body; var += step
            cond = ast.Compare(
                left=ast.Name(id=var, ctx=ast.Load()),
                ops=[ast.Gt()],
                comparators=[stop],
            )
        else:
            # while var < stop: body; var += step
            cond = ast.Compare(
                left=ast.Name(id=var, ctx=ast.Load()),
                ops=[ast.Lt()],
                comparators=[stop],
            )

        # var = start
        init = ast.Assign(
            targets=[ast.Name(id=var, ctx=ast.Store())],
            value=start,
        )
        # var += step
        increment = ast.AugAssign(
            target=ast.Name(id=var, ctx=ast.Store()),
            op=ast.Add(),
            value=step,
        )
        new_body = list(node.body) + [increment]

        while_node = ast.While(test=cond, body=new_body, orelse=node.orelse)
        result = [init, while_node]
        for n in result:
            ast.fix_missing_locations(n)
        return result  # returning a list replaces the node

    def visit_ListComp(self, node: ast.ListComp):
        self.generic_visit(node)
        if self.mode not in ("listcomp_to_for", "both"):
            return node
        # Only handle single-generator list comps without ifs for safety
        if len(node.generators) != 1:
            return node
        gen = node.generators[0]
        if gen.ifs:
            # Still rewrite but preserve the if condition
            pass
        if not isinstance(gen.target, ast.Name):
            return node

        # We need to be inside an assignment; return a Call to a helper inline expression.
        # Since we can't easily inject statements from an expression visitor, we
        # wrap in a call to a lambda that builds the list — this is still equivalent.
        # Actually, ast.NodeTransformer can't inject statements for expressions.
        # Instead we transform to: list(expr for var in iter if cond)
        # which IS a genexpr — semantically identical.
        inner_gen = ast.GeneratorExp(elt=node.elt, generators=node.generators)
        call = ast.Call(
            func=ast.Name(id="list", ctx=ast.Load()),
            args=[inner_gen],
            keywords=[],
        )
        ast.copy_location(call, node)
        ast.fix_missing_locations(call)
        return call


def _pick_mode(source: str, rng: random.Random) -> str:
    tree = ast.parse(source)
    has_for_range = any(
        isinstance(n, ast.For)
        and isinstance(n.iter, ast.Call)
        and isinstance(n.iter.func, ast.Name)
        and n.iter.func.id == "range"
        for n in ast.walk(tree)
    )
    has_listcomp = any(isinstance(n, ast.ListComp) for n in ast.walk(tree))

    modes = []
    if has_for_range:
        modes.append("for_to_while")
    if has_listcomp:
        modes.append("listcomp_to_for")
    if has_for_range and has_listcomp:
        modes.append("both")
    return rng.choice(modes) if modes else "for_to_while"


class LoopRewriteTransformation:
    """SP-5: Convert for-range to while; convert list comprehension to genexpr wrapped in list()."""

    id = "SP-5"
    name = "LOOP_REWRITE"

    def apply(self, source_code: str, seed: int) -> str:
        random.seed(seed)
        rng = random.Random(seed)
        tree = copy.deepcopy(ast.parse(source_code))
        mode = _pick_mode(source_code, rng)
        rewriter = _LoopRewriter(rng, mode)
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
