"""
SP-3: DEAD_CODE_INSERT
Insert unreachable code blocks (if False: ...) at random statement-level positions.
The inserted blocks are syntactically valid but never executed.
"""
import ast
import random
import copy

_DEAD_TEMPLATES = [
    "if False:\n    pass",
    "if False:\n    x_dead = 0",
    "if False:\n    raise RuntimeError('unreachable')",
    "if False:\n    return None",
    "if 1 == 0:\n    _ = 'dead'",
    "if not True:\n    print('dead')",
    "while False:\n    break",
]


def _insert_dead_stmts(body: list, rng: random.Random, depth: int = 0) -> list:
    """Recursively insert dead-code statements into a statement list."""
    if depth > 2 or not body:
        return body
    new_body = []
    for stmt in body:
        # Possibly insert before this statement
        if rng.random() < 0.4:
            template = rng.choice(_DEAD_TEMPLATES)
            dead_ast = ast.parse(template).body[0]
            new_body.append(dead_ast)
        new_body.append(stmt)
        # Recurse into compound statements
        if isinstance(stmt, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            if hasattr(stmt, "body"):
                stmt.body = _insert_dead_stmts(stmt.body, rng, depth + 1)
            if hasattr(stmt, "orelse") and stmt.orelse:
                stmt.orelse = _insert_dead_stmts(stmt.orelse, rng, depth + 1)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            stmt.body = _insert_dead_stmts(stmt.body, rng, depth + 1)
    return new_body


class DeadCodeInsertTransformation:
    """SP-3: Insert unreachable code blocks at statement-level positions."""

    id = "SP-3"
    name = "DEAD_CODE_INSERT"

    def apply(self, source_code: str, seed: int) -> str:
        random.seed(seed)
        rng = random.Random(seed)
        tree = copy.deepcopy(ast.parse(source_code))

        tree.body = _insert_dead_stmts(tree.body, rng, depth=0)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def validate(self, original: str, transformed: str) -> bool:
        try:
            ast.parse(original)
            ast.parse(transformed)
            return original != transformed
        except SyntaxError:
            return False
