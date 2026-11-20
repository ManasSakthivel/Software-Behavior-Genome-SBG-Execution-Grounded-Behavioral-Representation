"""
SP-7: INLINE_FUNCTION
Find a small helper function (body <= 5 stmts, no recursion, single return) and
inline its body at every call site, replacing the call with the return expression.
"""
import ast
import random
import copy


def _is_inlineable(func_def: ast.FunctionDef) -> bool:
    """A function is inlineable if it has:
    - At most 5 statements
    - Exactly one return statement (last stmt)
    - No default args complexity
    - No *args/**kwargs
    - Not recursive
    """
    body = func_def.body
    if not body:
        return False
    if len(body) > 5:
        return False
    # Must end with return
    if not isinstance(body[-1], ast.Return):
        return False
    # No recursion (simple check: function name not in body)
    func_name = func_def.name
    for node in ast.walk(ast.Module(body=body, type_ignores=[])):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == func_name:
                return False
    # No *args/**kwargs in definition
    args = func_def.args
    if args.vararg or args.kwarg or args.kwonlyargs or args.posonlyargs:
        return False
    return True


def _inline_call(call_node: ast.Call, func_def: ast.FunctionDef) -> ast.expr:
    """Replace call with the return expression, substituting formal args with actual args."""
    param_names = [arg.arg for arg in func_def.args.args]
    actual_args = call_node.args

    if len(param_names) != len(actual_args):
        return call_node  # Mismatch; skip

    # Build substitution map
    sub_map = dict(zip(param_names, actual_args))

    # Clone the return expression
    ret_expr = copy.deepcopy(func_def.body[-1].value)

    # Substitute parameter names with actual arguments
    class _Substitutor(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id in sub_map:
                replacement = copy.deepcopy(sub_map[node.id])
                ast.copy_location(replacement, node)
                return replacement
            return node

    result = _Substitutor().visit(ret_expr)
    ast.fix_missing_locations(result)
    return result


class _InlinerTransformer(ast.NodeTransformer):
    def __init__(self, target_name: str, func_def: ast.FunctionDef):
        self.target_name = target_name
        self.func_def = func_def
        self.inlined = False

    def visit_Call(self, node: ast.Call):
        self.generic_visit(node)
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == self.target_name
            and not node.keywords
        ):
            result = _inline_call(node, self.func_def)
            if result is not node:
                self.inlined = True
                return result
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Remove the definition of the inlined function
        self.generic_visit(node)
        if node.name == self.target_name:
            return None  # Delete this node
        return node


class InlineFunctionTransformation:
    """SP-7: Inline a small helper function at all call sites and remove its definition."""

    id = "SP-7"
    name = "INLINE_FUNCTION"

    def apply(self, source_code: str, seed: int) -> str:
        random.seed(seed)
        rng = random.Random(seed)
        tree = ast.parse(source_code)

        # Find all top-level inlineable functions
        candidates = [
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and _is_inlineable(node)
        ]
        if not candidates:
            return source_code

        target = rng.choice(candidates)
        new_tree = copy.deepcopy(tree)

        inliner = _InlinerTransformer(target.name, target)
        new_tree = inliner.visit(new_tree)

        if not inliner.inlined:
            return source_code

        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    def validate(self, original: str, transformed: str) -> bool:
        try:
            ast.parse(original)
            ast.parse(transformed)
            return original != transformed
        except SyntaxError:
            return False
