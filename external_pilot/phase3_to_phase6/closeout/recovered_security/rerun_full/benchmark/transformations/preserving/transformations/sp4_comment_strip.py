"""
SP-4: COMMENT_STRIP
Remove all docstrings and inline comments from Python source.
Uses tokenize to strip comments; uses AST to strip docstring expression statements.
"""
import ast
import copy
import io
import random
import tokenize


def _strip_comments_via_tokenize(source: str) -> str:
    """Remove all COMMENT tokens, preserving all other tokens and structure."""
    tokens = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                continue
            tokens.append(tok)
    except tokenize.TokenError:
        return source
    try:
        return tokenize.untokenize(tokens)
    except Exception:
        return source


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    """Remove docstring expression statements from all function/class/module bodies."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                node.body = node.body[1:]
                # If body is now empty, add a pass
                if not node.body:
                    node.body = [ast.Pass()]
    return tree


class CommentStripTransformation:
    """SP-4: Remove all docstrings and comments."""

    id = "SP-4"
    name = "COMMENT_STRIP"

    def apply(self, source_code: str, seed: int) -> str:
        random.seed(seed)
        # Step 1: strip inline comments
        stripped = _strip_comments_via_tokenize(source_code)
        # Step 2: strip docstrings via AST
        try:
            tree = ast.parse(stripped)
        except SyntaxError:
            tree = ast.parse(source_code)
        tree = _strip_docstrings(copy.deepcopy(tree))
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)

    def validate(self, original: str, transformed: str) -> bool:
        try:
            ast.parse(original)
            ast.parse(transformed)
            return original != transformed
        except SyntaxError:
            return False
