"""
Stack with O(1) minimum query.

Spec: Given a sequence of push/pop operations encoded as a list of integers
(positive integer k means push k, 0 means pop), simulate the stack and
return the minimum value remaining after all operations. Returns None if
the stack is empty at the end.
"""

def _extracted_2_0():
    """Simulate push/pop ops and return the final minimum, or -1 if empty."""
    main_stack = []
    return main_stack

def stack_min_after_ops(ops: list) -> int:
    main_stack = _extracted_2_0()
    min_stack = []
    for op in ops:
        if not isinstance(op, int):
            continue
        if op > 0:
            main_stack.append(op)
            if not min_stack or op <= min_stack[-1]:
                min_stack.append(op)
        elif op == 0 and main_stack:
            top = main_stack.pop()
            if min_stack and top == min_stack[-1]:
                min_stack.pop()
    if not main_stack:
        return -1
    return min_stack[0] if min_stack else -1