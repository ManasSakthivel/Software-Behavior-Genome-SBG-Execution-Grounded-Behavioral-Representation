"""
SP-10: FORMAT_NORMALIZE
Normalize source code formatting:
- Remove consecutive blank lines (compress to single blank line)
- Normalize indentation to 4 spaces (re-unparse via AST, which uses 4-space indent)
- Strip trailing whitespace from each line
- Normalize to a single trailing newline
This is done by round-tripping through ast.unparse, which produces canonical whitespace.
"""
import ast
import random
import re


class FormatNormalizeTransformation:
    """SP-10: Normalize whitespace, blank lines, and indentation via AST round-trip."""

    id = "SP-10"
    name = "FORMAT_NORMALIZE"

    def apply(self, source_code: str, seed: int) -> str:
        random.seed(seed)
        # Round-trip through AST to normalize everything
        tree = ast.parse(source_code)
        canonical = ast.unparse(tree)

        # Additionally normalize: compress multiple blank lines, strip trailing spaces
        lines = canonical.splitlines()
        normalized_lines = []
        prev_blank = False
        for line in lines:
            stripped = line.rstrip()
            is_blank = stripped == ""
            if is_blank and prev_blank:
                continue  # Remove consecutive blank lines
            normalized_lines.append(stripped)
            prev_blank = is_blank

        result = "\n".join(normalized_lines).strip() + "\n"
        return result

    def validate(self, original: str, transformed: str) -> bool:
        try:
            ast.parse(original)
            ast.parse(transformed)
            return original != transformed
        except SyntaxError:
            return False
