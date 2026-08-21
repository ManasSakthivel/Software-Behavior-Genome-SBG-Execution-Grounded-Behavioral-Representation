"""
SP-8: EXTRACT_FUNCTION
Extract a contiguous sequence of pure statements from a function body into a new helper,
replacing the block with a call to that helper.

Strategy:
- Find a function body with >= 4 statements
- Extract a contiguous slice of 2–3 statements that are purely computational
  (no return/break/continue/raise inside the slice)
- Identify names defined before the slice and used inside (parameters of new func)
- Identify names defined inside the slice and used after (return values of new func)
- Create a new function and replace the slice with a call
"""
import ast
import random
import copy
from typing import Optional


def _names_assigned(stmts: list) -> set[str]:
    result = set()
    for stmt in stmts:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    for n in ast.walk(t):
                        if isinstance(n, ast.Name):
                            result.add(n.id)
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                t = node.target
                if isinstance(t, ast.Name):
                    result.add(t.id)
            elif isinstance(node, ast.For):
                for n in ast.walk(node.target):
                    if isinstance(n, ast.Name):
                        result.add(n.id)
    return result


def _names_used(stmts: list) -> set[str]:
    result = set()
    for stmt in stmts:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                result.add(node.id)
    return result


def _has_control_flow(stmts: list) -> bool:
    for stmt in stmts:
        for node in ast.walk(stmt):
            if isinstance(node, (ast.Return, ast.Break, ast.Continue, ast.Raise, ast.Yield, ast.YieldFrom)):
                return True
    return False


def _try_extract(
    body: list,
    rng: random.Random,
    func_counter: list,
    available_before: set[str],
) -> Optional[tuple]:
    """Try to find a slice to extract. Returns (slice_start, slice_end, params, returns) or None."""
    n = len(body)
    if n < 4:
        return None

    # Try a few random slices
    for _ in range(10):
        start = rng.randint(0, n - 2)
        length = rng.randint(2, min(3, n - start))
        end = start + length
        slice_stmts = body[start:end]

        if _has_control_flow(slice_stmts):
            continue

        used_in_slice = _names_used(slice_stmts)
        assigned_in_slice = _names_assigned(slice_stmts)

        # Parameters: names used in slice that were available before slice
        params = sorted(used_in_slice & available_before - assigned_in_slice)

        # Return values: names assigned in slice that are used after
        after_stmts = body[end:]
        used_after = _names_used(after_stmts)
        returns = sorted(assigned_in_slice & used_after)

        # Keep it simple: at most 1 return variable
        if len(returns) > 1:
            continue

        return (start, end, params, returns)
    return None


def _build_extracted_func(
    name: str,
    slice_stmts: list,
    params: list[str],
    returns: list[str],
) -> ast.FunctionDef:
    body = copy.deepcopy(slice_stmts)
    if returns:
        ret_val = (
            ast.Name(id=returns[0], ctx=ast.Load())
            if len(returns) == 1
            else ast.Tuple(
                elts=[ast.Name(id=r, ctx=ast.Load()) for r in returns],
                ctx=ast.Load(),
            )
        )
        body.append(ast.Return(value=ret_val))
    else:
        body.append(ast.Return(value=ast.Constant(value=None)))

    args = ast.arguments(
        posonlyargs=[],
        args=[ast.arg(arg=p) for p in params],
        vararg=None,
        kwonlyargs=[],
        kw_defaults=[],
        kwarg=None,
        defaults=[],
    )
    func_def = ast.FunctionDef(
        name=name,
        args=args,
        body=body,
        decorator_list=[],
        returns=None,
    )
    ast.fix_missing_locations(func_def)
    return func_def


def _build_call_stmt(
    func_name: str,
    params: list[str],
    returns: list[str],
) -> ast.stmt:
    call = ast.Call(
        func=ast.Name(id=func_name, ctx=ast.Load()),
        args=[ast.Name(id=p, ctx=ast.Load()) for p in params],
        keywords=[],
    )
    if not returns:
        stmt = ast.Expr(value=call)
    elif len(returns) == 1:
        stmt = ast.Assign(
            targets=[ast.Name(id=returns[0], ctx=ast.Store())],
            value=call,
        )
    else:
        stmt = ast.Assign(
            targets=[
                ast.Tuple(
                    elts=[ast.Name(id=r, ctx=ast.Store()) for r in returns],
                    ctx=ast.Store(),
                )
            ],
            value=call,
        )
    ast.fix_missing_locations(stmt)
    return stmt


class ExtractFunctionTransformation:
    """SP-8: Extract a block of statements into a new helper function."""

    id = "SP-8"
    name = "EXTRACT_FUNCTION"

    def apply(self, source_code: str, seed: int) -> str:
        random.seed(seed)
        rng = random.Random(seed)
        tree = ast.parse(source_code)

        # Find eligible function bodies
        func_defs = [
            n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        if not func_defs:
            # Try module body
            target_body_owner = tree
            body = tree.body
        else:
            target_body_owner = rng.choice(func_defs)
            body = target_body_owner.body

        # Collect names defined before any slice (args + module-level)
        if isinstance(target_body_owner, (ast.FunctionDef, ast.AsyncFunctionDef)):
            available_before = {arg.arg for arg in target_body_owner.args.args}
        else:
            available_before = set()
        available_before |= _names_assigned(body)

        func_counter = [0]
        result = _try_extract(body, rng, func_counter, available_before)
        if result is None:
            return source_code

        start, end, params, returns = result
        slice_stmts = body[start:end]

        # Generate unique function name
        new_func_name = f"_extracted_{seed}_{start}"

        new_func = _build_extracted_func(new_func_name, slice_stmts, params, returns)
        call_stmt = _build_call_stmt(new_func_name, params, returns)

        new_tree = copy.deepcopy(tree)

        # Replace the body slice with the call stmt
        if isinstance(target_body_owner, ast.Module):
            new_tree.body = (
                body[:start] + [call_stmt] + body[end:]
            )
            # Insert new function definition before the host function (or at start)
            new_tree.body.insert(0, new_func)
        else:
            # Re-find the function in the deep copy
            for node in ast.walk(new_tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == target_body_owner.name
                ):
                    node.body = (
                        node.body[:start] + [call_stmt] + node.body[end:]
                    )
                    break
            # Insert helper before the host function in the module body
            for i, stmt in enumerate(new_tree.body):
                if (
                    isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and stmt.name == target_body_owner.name
                ):
                    new_tree.body.insert(i, new_func)
                    break

        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    def validate(self, original: str, transformed: str) -> bool:
        try:
            ast.parse(original)
            ast.parse(transformed)
            return original != transformed
        except SyntaxError:
            return False
