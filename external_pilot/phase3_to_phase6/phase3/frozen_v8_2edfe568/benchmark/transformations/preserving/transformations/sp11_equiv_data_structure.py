"""
SP-11: EQUIVALENT_DATA_STRUCTURE
Replace `list` with `collections.deque` where only append/pop semantics are used
(i.e., the list is used as a stack or queue: append, pop, extend, popleft).

Strategy:
- Find assignments of the form: name = [] or name = list()
- Check that the variable is only used with: append, pop, extend (no indexing, slicing, len is ok)
- Replace with: from collections import deque; name = deque()
- Replace append/pop calls accordingly (deque supports the same interface)

Because deque supports all list methods used in stack/queue patterns, this is semantically equivalent.
"""
import ast
import random
import copy


def _is_list_init(node: ast.expr) -> bool:
    """Check if node is [] or list()"""
    if isinstance(node, ast.List) and not node.elts:
        return True
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "list"
        and not node.args
        and not node.keywords
    ):
        return True
    return False


def _collect_list_vars(tree: ast.AST) -> set[str]:
    """Find variable names assigned to empty lists at the top level of a function."""
    result = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and _is_list_init(node.value):
                    result.add(target.id)
    return result


def _var_only_stack_ops(var_name: str, tree: ast.AST) -> bool:
    """
    Check that var_name is only used with: append, pop, extend, __len__ (len()),
    and not indexed, sliced, or passed to sorted/reversed/etc.
    """
    allowed_methods = {"append", "pop", "extend", "appendleft", "popleft", "clear"}
    for node in ast.walk(tree):
        # Check method calls: var.method(...)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == var_name
        ):
            if node.func.attr not in allowed_methods:
                return False
        # Check subscript access: var[i]
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == var_name
        ):
            return False
        # Check passing to functions like sorted(var), list(var), etc.
        if isinstance(node, ast.Call):
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id == var_name:
                    # Allow len() and bool()
                    if isinstance(node.func, ast.Name) and node.func.id in ("len", "bool", "not"):
                        continue
                    # Allow for loops: `for x in var`
                    # These are caught at For level, not Call level — ok
                    return False
        # Check for-loop iteration: `for x in var` is ok for deque
    return True


class _DequeReplacer(ast.NodeTransformer):
    def __init__(self, targets: set[str]):
        self.targets = targets

    def visit_Assign(self, node: ast.Assign):
        self.generic_visit(node)
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in self.targets:
                if _is_list_init(node.value):
                    # Replace with deque()
                    new_value = ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="collections", ctx=ast.Load()),
                            attr="deque",
                            ctx=ast.Load(),
                        ),
                        args=[],
                        keywords=[],
                    )
                    ast.copy_location(new_value, node.value)
                    node.value = new_value
        return node


class EquivalentDataStructureTransformation:
    """SP-11: Replace empty list with collections.deque where only stack/queue ops are used."""

    id = "SP-11"
    name = "EQUIVALENT_DATA_STRUCTURE"

    def apply(self, source_code: str, seed: int) -> str:
        random.seed(seed)
        rng = random.Random(seed)
        tree = ast.parse(source_code)

        list_vars = _collect_list_vars(tree)
        eligible = {v for v in list_vars if _var_only_stack_ops(v, tree)}

        if not eligible:
            return source_code

        # Pick a random subset
        chosen = set(rng.sample(sorted(eligible), k=rng.randint(1, len(eligible))))

        new_tree = _DequeReplacer(chosen).visit(copy.deepcopy(tree))

        # Add `import collections` if not already present
        has_import = any(
            (isinstance(n, ast.Import) and any(a.name == "collections" for a in n.names))
            or (isinstance(n, ast.ImportFrom) and n.module == "collections")
            for n in ast.walk(new_tree)
        )
        if not has_import:
            import_node = ast.Import(names=[ast.alias(name="collections")])
            ast.fix_missing_locations(import_node)
            new_tree.body.insert(0, import_node)

        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    def validate(self, original: str, transformed: str) -> bool:
        try:
            ast.parse(original)
            ast.parse(transformed)
            return original != transformed
        except SyntaxError:
            return False
