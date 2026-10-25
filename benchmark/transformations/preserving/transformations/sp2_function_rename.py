"""
SP-2: FUNCTION_RENAME
Rename helper (non-main, non-dunder) function definitions and all their call sites.
"""
import ast
import random
import copy


_RENAME_SUFFIXES = [
    ("compute", "calculate"),
    ("calculate", "compute"),
    ("process", "handle"),
    ("handle", "process"),
    ("run", "execute"),
    ("execute", "run"),
    ("find", "locate"),
    ("locate", "find"),
    ("check", "verify"),
    ("verify", "check"),
    ("get", "fetch"),
    ("fetch", "get"),
    ("make", "build"),
    ("build", "create"),
    ("helper", "util"),
    ("util", "helper"),
    ("parse", "decode"),
    ("decode", "parse"),
    ("init", "setup"),
    ("setup", "init"),
]

# Prefixes used to generate new names when no suffix rule matches
_NEW_PREFIX = "fn_"


def _collect_function_names(tree: ast.AST) -> list[str]:
    """Return names of top-level and nested user-defined functions (skip dunders and 'main')."""
    names = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if not (name.startswith("__") and name.endswith("__")) and name != "main":
                names.append(name)
    return names


class _FunctionRenamer(ast.NodeTransformer):
    def __init__(self, rename_map: dict[str, str]):
        self.rename_map = rename_map

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        if node.name in self.rename_map:
            new_node = copy.copy(node)
            new_node.name = self.rename_map[node.name]
            return new_node
        return node

    def visit_AsyncFunctionDef(self, node):
        return self.visit_FunctionDef(node)

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id in self.rename_map:
            new_func = ast.Name(
                id=self.rename_map[node.func.id], ctx=node.func.ctx
            )
            ast.copy_location(new_func, node.func)
            new_node = copy.copy(node)
            new_node.func = new_func
            return new_node
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        if node.attr in self.rename_map:
            new_node = copy.copy(node)
            new_node.attr = self.rename_map[node.attr]
            return new_node
        return node


class FunctionRenameTransformation:
    """SP-2: Rename helper function names deterministically."""

    id = "SP-2"
    name = "FUNCTION_RENAME"

    def __init__(self):
        self.last_rename_map: dict[str, str] = {}

    def apply(self, source_code: str, seed: int) -> str:
        random.seed(seed)
        tree = ast.parse(source_code)
        func_names = list(dict.fromkeys(_collect_function_names(tree)))  # dedup, preserve order

        if not func_names:
            self.last_rename_map = {}
            return source_code

        # Build rename map: try suffix table first, fall back to prefix
        suffix_map = {old: new for old, new in _RENAME_SUFFIXES}
        existing = set(func_names)
        rename_map: dict[str, str] = {}

        candidates = random.sample(func_names, k=random.randint(1, max(1, len(func_names))))
        for name in candidates:
            new_name = None
            # Try suffix substitution
            for old_s, new_s in _RENAME_SUFFIXES:
                if name == old_s:
                    new_name = new_s
                    break
                if name.startswith(old_s + "_") or name.startswith(old_s.capitalize()):
                    new_name = name.replace(old_s, new_s, 1)
                    break
            if new_name is None:
                new_name = _NEW_PREFIX + name
            if new_name not in existing:
                rename_map[name] = new_name
                existing.add(new_name)
                existing.discard(name)

        if not rename_map:
            self.last_rename_map = {}
            return source_code

        self.last_rename_map = rename_map
        new_tree = _FunctionRenamer(rename_map).visit(copy.deepcopy(tree))
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    def validate(self, original: str, transformed: str) -> bool:
        try:
            orig_tree = ast.parse(original)
            trans_tree = ast.parse(transformed)
        except SyntaxError:
            return False

        if original == transformed:
            return False

        orig_funcs = set(_collect_function_names(orig_tree))
        trans_funcs = set(_collect_function_names(trans_tree))

        rename_map = getattr(self, "last_rename_map", None)
        if rename_map:
            for old_name, new_name in rename_map.items():
                if old_name in trans_funcs:
                    return False
                if new_name not in trans_funcs:
                    return False
        else:
            renamed_away = orig_funcs - trans_funcs
            new_introduced = trans_funcs - orig_funcs
            if not renamed_away or not new_introduced:
                return False

        return True
