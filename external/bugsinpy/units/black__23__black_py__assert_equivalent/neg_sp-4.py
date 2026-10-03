from typing import Iterator
import sys

def assert_equivalent(src: str, dst: str) -> None:
    import ast
    import traceback

    def _v(node: ast.AST, depth: int=0) -> Iterator[str]:
        yield f"{'  ' * depth}{node.__class__.__name__}("
        for field in sorted(node._fields):
            try:
                value = getattr(node, field)
            except AttributeError:
                continue
            yield f"{'  ' * (depth + 1)}{field}="
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        yield from _v(item, depth + 2)
            elif isinstance(value, ast.AST):
                yield from _v(value, depth + 2)
            else:
                yield f"{'  ' * (depth + 2)}{value!r},  # {value.__class__.__name__}"
        yield f"{'  ' * depth})  # /{node.__class__.__name__}"
    try:
        src_ast = ast.parse(src)
    except Exception as exc:
        major, minor = sys.version_info[:2]
        raise AssertionError(f"cannot use --safe with this file; failed to parse source file with Python {major}.{minor}'s builtin AST. Re-run with --fast or stop using deprecated Python 2 syntax. AST error message: {exc}")
    try:
        dst_ast = ast.parse(dst)
    except Exception as exc:
        log = dump_to_file(''.join(traceback.format_tb(exc.__traceback__)), dst)
        raise AssertionError(f'INTERNAL ERROR: Black produced invalid code: {exc}. Please report a bug on https://github.com/ambv/black/issues.  This invalid output might be helpful: {log}') from None
    src_ast_str = '\n'.join(_v(src_ast))
    dst_ast_str = '\n'.join(_v(dst_ast))
    if src_ast_str != dst_ast_str:
        log = dump_to_file(diff(src_ast_str, dst_ast_str, 'src', 'dst'))
        raise AssertionError(f'INTERNAL ERROR: Black produced code that is not equivalent to the source.  Please report a bug on https://github.com/ambv/black/issues.  This diff might be helpful: {log}') from None

def dump_to_file(*output: str) -> str:
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', prefix='blk_', suffix='.log', delete=False) as f:
        for lines in output:
            f.write(lines)
            f.write('\n')
    return f.name

def diff(a: str, b: str, a_name: str, b_name: str) -> str:
    import difflib
    a_lines = [line + '\n' for line in a.split('\n')]
    b_lines = [line + '\n' for line in b.split('\n')]
    return ''.join(difflib.unified_diff(a_lines, b_lines, fromfile=a_name, tofile=b_name, n=5))