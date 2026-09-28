"""
SP-3: DEAD_CODE_INSERT
Insert unreachable code blocks (if False: ...) at random statement-level positions.
The inserted blocks are syntactically valid but never executed.

SCOPE FIX
---------
``return None`` is only legal inside a function body. The original template
list offered it at every insertion point, including module and class scope,
where it produces a file that parses but does not compile:

    SyntaxError: 'return' outside function

103 of the 3 577 generated variants were corrupt this way (50 train, 16 dev,
17 val, 20 test), and every pair that used one was silently dropped from the
evaluation denominator. ``validate`` did not catch it because ``ast.parse``
accepts a module-level ``return`` -- the error is raised by the compiler, not
the parser -- so the check now uses ``compile``.

``_insert_dead_stmts`` now tracks whether it is inside a function body and
draws from ``_FUNCTION_ONLY_TEMPLATES`` only there.
"""
import ast
import random
import copy

# Legal at any statement position.
_DEAD_TEMPLATES = [
    "if False:\n    pass",
    "if False:\n    x_dead = 0",
    "if False:\n    raise RuntimeError('unreachable')",
    "if 1 == 0:\n    _ = 'dead'",
    "if not True:\n    print('dead')",
    "while False:\n    break",
]

# Legal only inside a function body.
_FUNCTION_ONLY_TEMPLATES = [
    "if False:\n    return None",
]


def _insert_dead_stmts(body: list, rng: random.Random, depth: int = 0,
                       in_function: bool = False) -> list:
    """Recursively insert dead-code statements into a statement list.

    ``in_function`` is True only for statement lists that sit inside a function
    body; templates containing ``return`` are drawn only there.
    """
    if depth > 2 or not body:
        return body
    templates = (_DEAD_TEMPLATES + _FUNCTION_ONLY_TEMPLATES if in_function
                 else _DEAD_TEMPLATES)
    new_body = []
    for stmt in body:
        # Possibly insert before this statement
        if rng.random() < 0.4:
            template = rng.choice(templates)
            dead_ast = ast.parse(template).body[0]
            new_body.append(dead_ast)
        new_body.append(stmt)
        # Recurse into compound statements, carrying the function-scope flag
        if isinstance(stmt, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            if hasattr(stmt, "body"):
                stmt.body = _insert_dead_stmts(stmt.body, rng, depth + 1, in_function)
            if hasattr(stmt, "orelse") and stmt.orelse:
                stmt.orelse = _insert_dead_stmts(stmt.orelse, rng, depth + 1, in_function)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stmt.body = _insert_dead_stmts(stmt.body, rng, depth + 1, in_function=True)
        elif isinstance(stmt, ast.ClassDef):
            # A class body is not a function body: ``return`` is illegal here.
            stmt.body = _insert_dead_stmts(stmt.body, rng, depth + 1, in_function=False)
    return new_body


class DeadCodeInsertTransformation:
    """SP-3: Insert unreachable code blocks at statement-level positions."""

    id = "SP-3"
    name = "DEAD_CODE_INSERT"

    def apply(self, source_code: str, seed: int) -> str:
        random.seed(seed)
        rng = random.Random(seed)
        tree = copy.deepcopy(ast.parse(source_code))

        tree.body = _insert_dead_stmts(tree.body, rng, depth=0, in_function=False)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def validate(self, original: str, transformed: str) -> bool:
        # compile(), not ast.parse(): a module-level ``return`` parses cleanly
        # and only the compiler rejects it, which is how the original corrupt
        # variants passed validation.
        try:
            compile(original, "<original>", "exec")
            compile(transformed, "<transformed>", "exec")
            return original != transformed
        except SyntaxError:
            return False
