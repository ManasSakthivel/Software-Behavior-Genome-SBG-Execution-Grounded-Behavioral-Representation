"""
SP-1: VARIABLE_RENAME
Rename local variables systematically using a deterministic seed-controlled mapping.
"""
import ast
import random
import copy


# Candidate rename pools: original_suffix -> replacement
RENAME_POOL = [
    ("i", "idx"),
    ("j", "jdx"),
    ("k", "kdx"),
    ("n", "num"),
    ("m", "cnt"),
    ("x", "val"),
    ("y", "yval"),
    ("z", "zval"),
    ("result", "output"),
    ("res", "out"),
    ("temp", "tmp"),
    ("count", "total"),
    ("flag", "found"),
    ("data", "payload"),
    ("lst", "items"),
    ("arr", "array_"),
    ("node", "vertex"),
    ("cur", "current"),
    ("prev", "previous"),
    ("nxt", "nxt_"),
    ("ans", "answer"),
    ("buf", "buffer_"),
    ("acc", "accumulator"),
    ("val", "value"),
    ("elem", "element"),
]


class _ScopeCollector(ast.NodeVisitor):
    """Collect all names that are assigned (local variables) within function scopes."""

    def __init__(self):
        self.local_names: set[str] = set()

    def visit_FunctionDef(self, node):
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for t in child.targets:
                    for n in ast.walk(t):
                        if isinstance(n, ast.Name):
                            self.local_names.add(n.id)
            elif isinstance(child, (ast.For, ast.comprehension)):
                target = getattr(child, "target", None)
                if target:
                    for n in ast.walk(target):
                        if isinstance(n, ast.Name):
                            self.local_names.add(n.id)
            elif isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name):
                    self.local_names.add(child.target.id)
            elif isinstance(child, ast.AugAssign):
                if isinstance(child.target, ast.Name):
                    self.local_names.add(child.target.id)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for arg in child.args.args:
                    self.local_names.add(arg.arg)
        self.generic_visit(node)


class _Renamer(ast.NodeTransformer):
    def __init__(self, rename_map: dict[str, str]):
        self.rename_map = rename_map

    def visit_Name(self, node):
        if node.id in self.rename_map:
            return ast.copy_location(
                ast.Name(id=self.rename_map[node.id], ctx=node.ctx), node
            )
        return node

    def visit_arg(self, node):
        if node.arg in self.rename_map:
            new_node = copy.copy(node)
            new_node.arg = self.rename_map[node.arg]
            return new_node
        return node


class VariableRenameTransformation:
    """SP-1: Rename local variables using a deterministic pool-based mapping.

    ``max_names`` controls the maximum number of variables renamed per call.
    The default ``None`` preserves the original behaviour (rename up to all
    pool-matching variables). ``max_names=1`` renames exactly one variable
    (all its occurrences), which limits the edit size to roughly
    2 × (number of occurrences) lines and creates meaningful overlap with
    the SC mutation edit-size range. This is the setting used when generating
    the v7/v8 benchmark to mitigate the edit-size confound.

    See ``docs/current/EDIT_SIZE_REDESIGN.md`` for the full rationale.
    """

    id = "SP-1"
    name = "VARIABLE_RENAME"

    def apply(self, source_code: str, seed: int,
              max_names: "int | None" = None) -> str:
        random.seed(seed)
        tree = ast.parse(source_code)

        collector = _ScopeCollector()
        collector.visit(tree)
        local_names = collector.local_names

        # Build a rename mapping from the pool, filtered to names that exist
        candidates = [(old, new) for old, new in RENAME_POOL if old in local_names]
        if not candidates:
            return source_code

        # Randomly pick a subset of candidates to rename (at least 1).
        # max_names caps the count to limit edit size (see class docstring).
        k = random.randint(1, max(1, len(candidates)))
        if max_names is not None:
            k = min(k, max(1, max_names))
        chosen = random.sample(candidates, k)

        # Ensure no collision: new name must not be an existing name
        existing = set(local_names)
        rename_map = {}
        for old, new in chosen:
            if new not in existing and old not in rename_map:
                rename_map[old] = new
                existing.add(new)
                existing.discard(old)

        if not rename_map:
            return source_code

        new_tree = _Renamer(rename_map).visit(copy.deepcopy(tree))
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    def validate(self, original: str, transformed: str) -> bool:
        try:
            ast.parse(original)
            ast.parse(transformed)
            return original != transformed
        except SyntaxError:
            return False
